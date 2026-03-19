#!/usr/bin/env python3
"""
Instance segmentation tavolo con YOLOv8n-seg su Raspberry Pi 4.
Supporta PiCamera (libcamera) e webcam USB.

Uso:
    python3 inference_yolo_rpi.py                          # PiCamera, modello 256
    python3 inference_yolo_rpi.py --size 128               # PiCamera, modello 128 (più veloce)
    python3 inference_yolo_rpi.py --source usb             # Webcam USB
    python3 inference_yolo_rpi.py --source video.mp4       # Da file video
    python3 inference_yolo_rpi.py --headless               # Senza GUI, salva output

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
        time.sleep(1)
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
    """Carica il modello ONNX YOLOv8n-seg."""
    model_path = f"models/trained/yolov8n_seg_table_{size}.onnx"

    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 4
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

    session = ort.InferenceSession(model_path, opts, providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    input_shape = session.get_inputs()[0].shape

    print(f"Modello caricato: {model_path}")
    print(f"Input: {input_name} {input_shape}")
    return session, input_name


def preprocess(frame, size):
    """Preprocessa il frame per YOLOv8: resize, normalize 0-1, CHW."""
    img = cv2.resize(frame, (size, size))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    return np.expand_dims(img, 0)


def postprocess(outputs, frame_h, frame_w, img_size, conf_threshold=0.5):
    """Post-processing YOLOv8-seg: NMS + mask decoding.

    YOLOv8-seg ONNX outputs:
        output0: (1, 116, N) - detections [x,y,w,h, conf, 32 mask coefficients]
        output1: (1, 32, mask_h, mask_w) - prototype masks
    """
    det_output = outputs[0]  # (1, 116, N)
    proto = outputs[1]       # (1, 32, mask_h, mask_w)

    # Transpose: (1, 116, N) -> (N, 116)
    predictions = det_output[0].T

    # Colonne: x_center, y_center, w, h, class_scores..., mask_coeffs (32)
    # Per 1 classe: cols 0-3 = box, col 4 = conf, cols 5-36 = mask coefficients (ma 4+nc+32=37 per nc=1)
    # YOLOv8 con 1 classe: 4 + 1 + 32 = 37... ma output ha 37 cols
    num_mask_coeffs = 32
    num_classes = predictions.shape[1] - 4 - num_mask_coeffs

    boxes = predictions[:, :4]
    class_scores = predictions[:, 4:4 + num_classes]
    mask_coeffs = predictions[:, 4 + num_classes:]

    # Confidence filtering
    if num_classes == 1:
        confidences = class_scores[:, 0]
    else:
        confidences = np.max(class_scores, axis=1)

    mask = confidences > conf_threshold
    if not np.any(mask):
        return np.zeros((frame_h, frame_w), dtype=np.uint8)

    boxes = boxes[mask]
    confidences = confidences[mask]
    mask_coeffs = mask_coeffs[mask]

    # Converti xywh -> xyxy
    x1 = boxes[:, 0] - boxes[:, 2] / 2
    y1 = boxes[:, 1] - boxes[:, 3] / 2
    x2 = boxes[:, 0] + boxes[:, 2] / 2
    y2 = boxes[:, 1] + boxes[:, 3] / 2
    boxes_xyxy = np.stack([x1, y1, x2, y2], axis=1)

    # NMS
    indices = cv2.dnn.NMSBoxes(
        boxes_xyxy.tolist(), confidences.tolist(),
        conf_threshold, 0.5
    )

    if len(indices) == 0:
        return np.zeros((frame_h, frame_w), dtype=np.uint8)

    indices = np.array(indices).flatten()

    # Decode masks
    proto_masks = proto[0]  # (32, mask_h, mask_w)
    mask_h, mask_w = proto_masks.shape[1], proto_masks.shape[2]

    final_mask = np.zeros((frame_h, frame_w), dtype=np.uint8)

    for idx in indices:
        coeffs = mask_coeffs[idx]  # (32,)
        # Maschera = sigmoid(coeffs @ proto_masks)
        raw_mask = np.tensordot(coeffs, proto_masks, axes=([0], [0]))  # (mask_h, mask_w)
        raw_mask = 1.0 / (1.0 + np.exp(-raw_mask))  # sigmoid

        # Crop mask al bounding box (migliora qualita')
        box = boxes_xyxy[idx]
        scale_x = mask_w / img_size
        scale_y = mask_h / img_size
        bx1 = max(0, int(box[0] * scale_x))
        by1 = max(0, int(box[1] * scale_y))
        bx2 = min(mask_w, int(box[2] * scale_x))
        by2 = min(mask_h, int(box[3] * scale_y))

        cropped = np.zeros_like(raw_mask)
        cropped[by1:by2, bx1:bx2] = raw_mask[by1:by2, bx1:bx2]

        # Resize alla dimensione del frame
        resized = cv2.resize(cropped, (frame_w, frame_h), interpolation=cv2.INTER_LINEAR)
        final_mask[resized > 0.5] = 255

    return final_mask


def main():
    parser = argparse.ArgumentParser(description="YOLOv8n-seg table segmentation su RPi4")
    parser.add_argument("--size", type=int, default=256,
                        help="Risoluzione input modello")
    parser.add_argument("--conf", type=float, default=0.5,
                        help="Soglia confidence (default 0.5)")
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
        os.makedirs("output_yolo", exist_ok=True)

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
            outputs = session.run(None, {input_name: input_data})
            table_mask = postprocess(
                outputs, frame.shape[0], frame.shape[1],
                args.size, args.conf
            )

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
                    cv2.imwrite(f"output_yolo/frame_{frame_count:05d}.png", result)
                    print(f"Frame {frame_count} | FPS: {avg_fps:.1f} | Table: {table_pct:.1f}%")
            else:
                overlay = frame.copy()
                overlay[table_mask > 0] = [0, 255, 0]
                result = cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)

                cv2.putText(result,
                            f"YOLO FPS: {avg_fps:.1f} | Table: {table_pct:.1f}% | {args.size}px",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                cv2.imshow("YOLOv8 Table Segmentation", result)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord("s"):
                    cv2.imwrite("frame.png", frame)
                    cv2.imwrite("mask_yolo.png", table_mask)
                    cv2.imwrite("result_yolo.png", result)
                    print("Salvato: frame.png, mask_yolo.png, result_yolo.png")

    finally:
        cam.stop()
        if not args.headless:
            cv2.destroyAllWindows()
        print(f"\nMedia FPS: {np.mean(fps_list):.1f}")


if __name__ == "__main__":
    main()
