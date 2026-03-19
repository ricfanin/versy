#!/usr/bin/env python3
"""
Benchmark confronto SegFormer vs YOLOv8n-seg su Raspberry Pi 4.
Misura latenza, FPS, uso memoria e IoU tra i due modelli.

Uso:
    python3 benchmark_rpi.py                               # Benchmark con camera
    python3 benchmark_rpi.py --source video.mp4            # Benchmark da video
    python3 benchmark_rpi.py --source usb                  # Benchmark da webcam
    python3 benchmark_rpi.py --frames 200                  # Numero di frame
    python3 benchmark_rpi.py --size 128                    # Risoluzione 128

Dipendenze:
    pip install opencv-python onnxruntime numpy picamera2
"""

import argparse
import os
import time
from threading import Thread

import cv2
import numpy as np
import onnxruntime as ort


# ---- Camera streams (riuso dalle inference) ----

class PiCameraStream:
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
    def __init__(self, path):
        self.cap = cv2.VideoCapture(path)

    def read(self):
        return self.cap.read()

    def stop(self):
        self.cap.release()

    def isOpened(self):
        return self.cap.isOpened()


# ---- SegFormer inference ----

def segformer_preprocess(frame, size):
    img = cv2.resize(frame, (size, size))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = (img - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    img = np.transpose(img, (2, 0, 1))
    return np.expand_dims(img, 0).astype(np.float32)


def segformer_postprocess(output, frame_h, frame_w):
    mask = np.argmax(output[0][0], axis=0)
    mask = cv2.resize(mask.astype(np.uint8), (frame_w, frame_h),
                      interpolation=cv2.INTER_NEAREST)
    return (mask == 1).astype(np.uint8) * 255


# ---- YOLOv8-seg inference ----

def yolo_preprocess(frame, size):
    img = cv2.resize(frame, (size, size))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    return np.expand_dims(img, 0)


def yolo_postprocess(outputs, frame_h, frame_w, img_size, conf_threshold=0.5):
    det_output = outputs[0]
    proto = outputs[1]

    predictions = det_output[0].T
    num_mask_coeffs = 32
    num_classes = predictions.shape[1] - 4 - num_mask_coeffs

    boxes = predictions[:, :4]
    class_scores = predictions[:, 4:4 + num_classes]
    mask_coeffs = predictions[:, 4 + num_classes:]

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

    x1 = boxes[:, 0] - boxes[:, 2] / 2
    y1 = boxes[:, 1] - boxes[:, 3] / 2
    x2 = boxes[:, 0] + boxes[:, 2] / 2
    y2 = boxes[:, 1] + boxes[:, 3] / 2
    boxes_xyxy = np.stack([x1, y1, x2, y2], axis=1)

    indices = cv2.dnn.NMSBoxes(
        boxes_xyxy.tolist(), confidences.tolist(),
        conf_threshold, 0.5
    )

    if len(indices) == 0:
        return np.zeros((frame_h, frame_w), dtype=np.uint8)

    indices = np.array(indices).flatten()

    proto_masks = proto[0]
    mask_h, mask_w = proto_masks.shape[1], proto_masks.shape[2]

    final_mask = np.zeros((frame_h, frame_w), dtype=np.uint8)

    for idx in indices:
        coeffs = mask_coeffs[idx]
        raw_mask = np.tensordot(coeffs, proto_masks, axes=([0], [0]))
        raw_mask = 1.0 / (1.0 + np.exp(-raw_mask))

        box = boxes_xyxy[idx]
        scale_x = mask_w / img_size
        scale_y = mask_h / img_size
        bx1 = max(0, int(box[0] * scale_x))
        by1 = max(0, int(box[1] * scale_y))
        bx2 = min(mask_w, int(box[2] * scale_x))
        by2 = min(mask_h, int(box[3] * scale_y))

        cropped = np.zeros_like(raw_mask)
        cropped[by1:by2, bx1:bx2] = raw_mask[by1:by2, bx1:bx2]

        resized = cv2.resize(cropped, (frame_w, frame_h), interpolation=cv2.INTER_LINEAR)
        final_mask[resized > 0.5] = 255

    return final_mask


def compute_iou(mask_a, mask_b):
    """Calcola IoU tra due maschere binarie."""
    a = mask_a > 0
    b = mask_b > 0
    intersection = np.sum(a & b)
    union = np.sum(a | b)
    if union == 0:
        return 1.0
    return intersection / union


def load_session(model_path):
    """Carica sessione ONNX."""
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 4
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    session = ort.InferenceSession(model_path, opts, providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    return session, input_name


def get_model_size_mb(path):
    """Dimensione file in MB."""
    if os.path.exists(path):
        return os.path.getsize(path) / 1e6
    return 0.0


def main():
    parser = argparse.ArgumentParser(description="Benchmark SegFormer vs YOLOv8n-seg su RPi4")
    parser.add_argument("--size", type=int, default=256, help="Risoluzione input")
    parser.add_argument("--frames", type=int, default=100, help="Numero frame da testare")
    parser.add_argument("--warmup", type=int, default=10, help="Frame di warmup (esclusi)")
    parser.add_argument("--conf", type=float, default=0.5, help="YOLO confidence threshold")
    parser.add_argument("--source", default="picamera",
                        help="picamera | usb | /path/to/video.mp4")
    parser.add_argument("--camera-id", type=int, default=0)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    args = parser.parse_args()

    size = args.size
    segformer_path = f"models/trained/segformer_table_{size}.onnx"
    yolo_path = f"models/trained/yolov8n_seg_table_{size}.onnx"

    # Controlla quali modelli sono disponibili
    has_segformer = os.path.exists(segformer_path)
    has_yolo = os.path.exists(yolo_path)

    if not has_segformer and not has_yolo:
        print(f"Nessun modello trovato per size={size}!")
        print(f"  Cercato: {segformer_path}")
        print(f"  Cercato: {yolo_path}")
        return

    print("=" * 60)
    print(f"BENCHMARK: SegFormer vs YOLOv8n-seg @ {size}px")
    print(f"Frame: {args.frames} (+ {args.warmup} warmup)")
    print("=" * 60)

    # Modello sizes
    if has_segformer:
        print(f"\nSegFormer: {segformer_path} ({get_model_size_mb(segformer_path):.1f} MB)")
    else:
        print(f"\nSegFormer: NON TROVATO ({segformer_path})")

    if has_yolo:
        print(f"YOLOv8:    {yolo_path} ({get_model_size_mb(yolo_path):.1f} MB)")
    else:
        print(f"YOLOv8:    NON TROVATO ({yolo_path})")

    # Carica modelli
    sf_session, sf_input = None, None
    yolo_session, yolo_input = None, None

    if has_segformer:
        print("\nCaricamento SegFormer...")
        sf_session, sf_input = load_session(segformer_path)

    if has_yolo:
        print("Caricamento YOLOv8...")
        yolo_session, yolo_input = load_session(yolo_path)

    # Apri sorgente video
    if args.source == "picamera":
        cam = PiCameraStream(args.width, args.height)
    elif args.source == "usb":
        cam = USBCameraStream(args.camera_id, args.width, args.height)
    else:
        cam = VideoFileStream(args.source)

    if not cam.isOpened():
        print("Errore: impossibile aprire la sorgente video")
        return

    # Raccogli frame
    total_frames = args.frames + args.warmup
    print(f"\nRaccolta {total_frames} frame...")

    sf_times = []
    yolo_times = []
    ious = []

    for i in range(total_frames):
        ret, frame = cam.read()
        if not ret:
            print(f"Fine video al frame {i}")
            break

        frame_h, frame_w = frame.shape[:2]
        is_warmup = i < args.warmup

        # SegFormer inference
        sf_mask = None
        if has_segformer:
            t0 = time.perf_counter()
            sf_data = segformer_preprocess(frame, size)
            sf_out = sf_session.run(None, {sf_input: sf_data})
            sf_mask = segformer_postprocess(sf_out, frame_h, frame_w)
            sf_elapsed = time.perf_counter() - t0
            if not is_warmup:
                sf_times.append(sf_elapsed)

        # YOLOv8 inference
        yolo_mask = None
        if has_yolo:
            t0 = time.perf_counter()
            yolo_data = yolo_preprocess(frame, size)
            yolo_out = yolo_session.run(None, {yolo_input: yolo_data})
            yolo_mask = yolo_postprocess(yolo_out, frame_h, frame_w, size, args.conf)
            yolo_elapsed = time.perf_counter() - t0
            if not is_warmup:
                yolo_times.append(yolo_elapsed)

        # IoU tra i due modelli
        if sf_mask is not None and yolo_mask is not None and not is_warmup:
            ious.append(compute_iou(sf_mask, yolo_mask))

        if not is_warmup and (i - args.warmup + 1) % 20 == 0:
            print(f"  Frame {i - args.warmup + 1}/{args.frames}")

    cam.stop()

    # Risultati
    print("\n" + "=" * 60)
    print("RISULTATI")
    print("=" * 60)

    def print_stats(name, times):
        times_ms = np.array(times) * 1000
        fps_vals = 1.0 / np.array(times)
        print(f"\n  {name}:")
        print(f"    Latenza media:  {np.mean(times_ms):7.1f} ms")
        print(f"    Latenza mediana:{np.median(times_ms):7.1f} ms")
        print(f"    Latenza min:    {np.min(times_ms):7.1f} ms")
        print(f"    Latenza max:    {np.max(times_ms):7.1f} ms")
        print(f"    Latenza p95:    {np.percentile(times_ms, 95):7.1f} ms")
        print(f"    FPS medio:      {np.mean(fps_vals):7.1f}")
        print(f"    FPS mediano:    {np.median(fps_vals):7.1f}")

    if sf_times:
        print_stats("SegFormer-B0", sf_times)

    if yolo_times:
        print_stats("YOLOv8n-seg", yolo_times)

    # Confronto diretto
    if sf_times and yolo_times:
        sf_avg = np.mean(sf_times) * 1000
        yolo_avg = np.mean(yolo_times) * 1000
        speedup = sf_avg / yolo_avg

        print(f"\n  CONFRONTO:")
        print(f"    Speedup YOLOv8: {speedup:.2f}x {'piu veloce' if speedup > 1 else 'piu lento'}")
        print(f"    Diff latenza:   {sf_avg - yolo_avg:+.1f} ms")

        if ious:
            print(f"\n  CONCORDANZA MASCHERE (IoU):")
            print(f"    IoU medio:      {np.mean(ious):.3f}")
            print(f"    IoU mediano:    {np.median(ious):.3f}")
            print(f"    IoU min:        {np.min(ious):.3f}")

    # Tabella riepilogativa
    print(f"\n{'=' * 60}")
    print(f"{'Metrica':<25} {'SegFormer':>15} {'YOLOv8n-seg':>15}")
    print(f"{'-' * 60}")

    if has_segformer:
        sf_fps = f"{1.0 / np.mean(sf_times):.1f}"
        sf_lat = f"{np.mean(sf_times) * 1000:.0f} ms"
        sf_size = f"{get_model_size_mb(segformer_path):.1f} MB"
    else:
        sf_fps = sf_lat = sf_size = "N/A"

    if has_yolo:
        yolo_fps = f"{1.0 / np.mean(yolo_times):.1f}"
        yolo_lat = f"{np.mean(yolo_times) * 1000:.0f} ms"
        yolo_size = f"{get_model_size_mb(yolo_path):.1f} MB"
    else:
        yolo_fps = yolo_lat = yolo_size = "N/A"

    print(f"{'Modello ONNX':<25} {sf_size:>15} {yolo_size:>15}")
    print(f"{'Latenza media':<25} {sf_lat:>15} {yolo_lat:>15}")
    print(f"{'FPS medio':<25} {sf_fps:>15} {yolo_fps:>15}")

    if ious:
        print(f"{'IoU tra modelli':<25} {np.mean(ious):>15.3f} {'':>15}")

    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
