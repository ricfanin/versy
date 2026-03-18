#!/usr/bin/env python3
"""
Semantic segmentation tavolo in tempo reale su Raspberry Pi 4.
Supporta PiCamera (libcamera) e webcam USB.

Uso:
    python3 inference_rpi.py                        # PiCamera, modello 256
    python3 inference_rpi.py --size 128             # PiCamera, modello 128 (più veloce)
    python3 inference_rpi.py --source usb           # Webcam USB
    python3 inference_rpi.py --source video.mp4     # Da file video
    python3 inference_rpi.py --headless              # Senza GUI, salva output

Dipendenze:
    pip install opencv-python onnxruntime numpy picamera2
"""

import argparse
import time
from threading import Thread

import cv2
import numpy as np
import onnxruntime as ort


class PiCameraStream:
    """Stream dalla PiCamera via libcamera/picamera2."""

    def __init__(self, width, height):
        from picamera2 import Picamera2

        self.picam = Picamera2()
        config = self.picam.create_preview_configuration(
            main={"size": (width, height), "format": "RGB888"}
        )
        self.picam.configure(config)
        self.picam.start()
        time.sleep(1)  # Warm-up
        self.frame = self.picam.capture_array()
        self.running = True
        Thread(target=self._update, daemon=True).start()

    def _update(self):
        while self.running:
            self.frame = self.picam.capture_array()

    def read(self):
        return self.frame is not None, self.frame

    def stop(self):
        self.running = False
        self.picam.stop()

    def isOpened(self):
        return self.running


class USBCameraStream:
    """Stream da webcam USB con thread separato."""

    def __init__(self, src, width, height):
        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.ret, self.frame = self.cap.read()
        self.running = True
        Thread(target=self._update, daemon=True).start()

    def _update(self):
        while self.running:
            self.ret, self.frame = self.cap.read()

    def read(self):
        return self.ret, self.frame

    def stop(self):
        self.running = False
        self.cap.release()

    def isOpened(self):
        return self.cap.isOpened()


class VideoFileStream:
    """Stream da file video."""

    def __init__(self, path):
        self.cap = cv2.VideoCapture(path)

    def read(self):
        return self.cap.read()

    def stop(self):
        self.cap.release()

    def isOpened(self):
        return self.cap.isOpened()


def load_model(size):
    """Carica il modello ONNX custom per table segmentation."""
    model_path = f"models/trained/segformer_table_{size}.onnx"

    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 4
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

    session = ort.InferenceSession(model_path, opts, providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name

    print(f"Modello caricato: {model_path}")
    return session, input_name


def preprocess(frame, size):
    """Preprocessa il frame per SegFormer."""
    img = cv2.resize(frame, (size, size))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = (img - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    img = np.transpose(img, (2, 0, 1))
    return np.expand_dims(img, 0).astype(np.float32)


def segment(session, input_name, input_data, frame_size):
    """Esegue inference e ritorna la maschera binaria del tavolo."""
    output = session.run(None, {input_name: input_data})[0]
    mask = np.argmax(output[0], axis=0)
    mask = cv2.resize(mask.astype(np.uint8), frame_size, interpolation=cv2.INTER_NEAREST)
    return (mask == 1).astype(np.uint8) * 255


def main():
    parser = argparse.ArgumentParser(description="Table segmentation su RPi4")
    parser.add_argument("--size", type=int, choices=[128, 256], default=256,
                        help="Risoluzione input modello (128=veloce, 256=preciso)")
    parser.add_argument("--source", default="picamera",
                        help="picamera | usb | /path/to/video.mp4")
    parser.add_argument("--camera-id", type=int, default=0,
                        help="ID camera USB (default 0)")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--headless", action="store_true",
                        help="Senza GUI, salva frame in output/")
    parser.add_argument("--save-interval", type=int, default=30,
                        help="In modalità headless, salva ogni N frame")
    args = parser.parse_args()

    # Carica modello
    session, input_name = load_model(args.size)

    # Apri sorgente video
    if args.source == "picamera":
        print(f"Apro PiCamera ({args.width}x{args.height})...")
        cam = PiCameraStream(args.width, args.height)
    elif args.source == "usb":
        print(f"Apro webcam USB {args.camera_id} ({args.width}x{args.height})...")
        cam = USBCameraStream(args.camera_id, args.width, args.height)
    else:
        print(f"Apro video: {args.source}")
        cam = VideoFileStream(args.source)

    if not cam.isOpened():
        print("Errore: impossibile aprire la sorgente video")
        return

    if args.headless:
        import os
        os.makedirs("output", exist_ok=True)

    print("Premi 'q' per uscire, 's' per salvare frame")

    fps_list = []
    frame_count = 0

    try:
        while True:
            ret, frame = cam.read()
            if not ret:
                break

            t0 = time.perf_counter()

            input_data = preprocess(frame, args.size)
            table_mask = segment(session, input_name, input_data,
                                 (frame.shape[1], frame.shape[0]))

            elapsed = time.perf_counter() - t0
            fps = 1.0 / elapsed
            fps_list.append(fps)
            if len(fps_list) > 30:
                fps_list.pop(0)

            avg_fps = np.mean(fps_list)
            table_pct = np.sum(table_mask > 0) / table_mask.size * 100
            frame_count += 1

            if args.headless:
                if frame_count % args.save_interval == 0:
                    overlay = frame.copy()
                    overlay[table_mask > 0] = [0, 255, 0]
                    result = cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)
                    cv2.imwrite(f"output/frame_{frame_count:05d}.png", result)
                    print(f"Frame {frame_count} | FPS: {avg_fps:.1f} | Table: {table_pct:.1f}%")
            else:
                overlay = frame.copy()
                overlay[table_mask > 0] = [0, 255, 0]
                result = cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)

                cv2.putText(result,
                            f"FPS: {avg_fps:.1f} | Table: {table_pct:.1f}% | {args.size}px",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                cv2.imshow("Table Segmentation", result)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord("s"):
                    cv2.imwrite("frame.png", frame)
                    cv2.imwrite("mask.png", table_mask)
                    cv2.imwrite("result.png", result)
                    print("Salvato: frame.png, mask.png, result.png")

    finally:
        cam.stop()
        if not args.headless:
            cv2.destroyAllWindows()
        print(f"\nMedia FPS: {np.mean(fps_list):.1f}")


if __name__ == "__main__":
    main()
