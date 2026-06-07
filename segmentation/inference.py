#!/usr/bin/env python3
"""
Inferenza YOLOv8n-seg per table detection su Raspberry Pi 4.

Uso:
    python3 inference.py                        # PiCamera, 256px
    python3 inference.py --size 128             # PiCamera, 128px
    python3 inference.py --source usb           # Webcam USB
    python3 inference.py --source video.mp4     # Da file video
    python3 inference.py --headless             # Senza GUI
    python3 inference.py --int8                 # Modello quantizzato INT8
"""

import argparse
import time

import cv2
import numpy as np
import onnxruntime as ort

from camera import open_camera


def load_model(size, int8=False):
    suffix = "_int8" if int8 else ""
    model_path = f"models/trained/yolov8n_seg_table_{size}{suffix}.onnx"

    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 4
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

    session = ort.InferenceSession(model_path, opts, providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    print(f"Modello: {model_path}")
    return session, input_name


def preprocess(frame, size):
    img = cv2.resize(frame, (size, size))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    return np.expand_dims(img, 0)


def postprocess(outputs, frame_h, frame_w, img_size, conf_threshold=0.5):
    """Restituisce una maschera binaria (0/255) dalla output del modello."""
    detections = outputs[0][0].T  # (N candidati, 37 valori)
    prototypes = outputs[1][0]    # (32, mask_h, mask_w)

    # ogni candidato ha: [x,y,w,h, score, 32 coefficienti maschera]
    boxes = detections[:, :4]
    scores = detections[:, 4]
    mask_coeffs = detections[:, 5:]

    # filtra candidati con score troppo basso
    mask_vuota = np.zeros((frame_h, frame_w), dtype=np.uint8)
    keep = scores > conf_threshold
    if not np.any(keep):
        return mask_vuota
    boxes = boxes[keep]
    scores = scores[keep]
    mask_coeffs = mask_coeffs[keep]

    # xywh -> xyxy
    half_w = boxes[:, 2] / 2
    half_h = boxes[:, 3] / 2
    x1 = boxes[:, 0] - half_w
    y1 = boxes[:, 1] - half_h
    x2 = boxes[:, 0] + half_w
    y2 = boxes[:, 1] + half_h
    boxes_xyxy = np.stack([x1, y1, x2, y2], axis=1)

    # NMS: rimuovi box duplicati
    indices = cv2.dnn.NMSBoxes(
        boxes_xyxy.tolist(), scores.tolist(), conf_threshold, 0.5
    )
    if len(indices) == 0:
        return mask_vuota
    indices = np.array(indices).flatten()

    # ricostruisci maschera combinando i 32 prototipi con i coefficienti
    mask_h, mask_w = prototypes.shape[1], prototypes.shape[2]
    final_mask = np.zeros((frame_h, frame_w), dtype=np.uint8)

    for i in indices:
        raw = np.tensordot(mask_coeffs[i], prototypes, axes=([0], [0]))
        raw = 1.0 / (1.0 + np.exp(-raw))  # sigmoid

        # crop al bounding box
        box = boxes_xyxy[i]
        sx, sy = mask_w / img_size, mask_h / img_size
        bx1 = max(0, int(box[0] * sx))
        by1 = max(0, int(box[1] * sy))
        bx2 = min(mask_w, int(box[2] * sx))
        by2 = min(mask_h, int(box[3] * sy))
        cropped = np.zeros_like(raw)
        cropped[by1:by2, bx1:bx2] = raw[by1:by2, bx1:bx2]

        resized = cv2.resize(cropped, (frame_w, frame_h))
        final_mask[resized > 0.5] = 255

    return final_mask


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=256)
    parser.add_argument("--conf", type=float, default=0.5)
    parser.add_argument("--source", default="picamera", help="picamera | usb | path/to/video")
    parser.add_argument("--camera-id", type=int, default=0)
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=240)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--int8", action="store_true", help="Usa modello quantizzato INT8")
    parser.add_argument("--save-interval", type=int, default=30)
    args = parser.parse_args()

    session, input_name = load_model(args.size, args.int8)
    cam = open_camera(args.source, args.camera_id, args.width, args.height)

    if not cam.isOpened():
        print("Errore: impossibile aprire la sorgente video")
        return

    if args.headless:
        import os
        os.makedirs("output", exist_ok=True)

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
            table_mask = postprocess(outputs, frame.shape[0], frame.shape[1], args.size, args.conf)
            elapsed = time.perf_counter() - t0

            frame = cv2.flip(frame, 0)
            table_mask = cv2.flip(table_mask, 0)

            fps = 1.0 / elapsed
            fps_list.append(fps)
            if len(fps_list) > 30:
                fps_list.pop(0)

            avg_fps = np.mean(fps_list)
            table_pct = np.sum(table_mask > 0) / table_mask.size * 100
            frame_count += 1

            overlay = frame.copy()
            overlay[table_mask > 0] = [0, 255, 0]
            result = cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)

            if args.headless:
                if frame_count % args.save_interval == 0:
                    cv2.imwrite(f"output/frame_{frame_count:05d}.png", result)
                    print(f"Frame {frame_count} | FPS: {avg_fps:.1f} | Table: {table_pct:.1f}%")
            else:
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
