#!/usr/bin/env python3
"""
Training YOLOv8n-seg per table segmentation + export ONNX per RPi4.

Uso:
    python train_yolov8_seg.py --data ../yolo_dataset/data.yaml --epochs 100
    python train_yolov8_seg.py --export runs/segment/table_seg/weights/best.pt --size 256
    python train_yolov8_seg.py --export best.pt --size 256 --int8 --data ../yolo_dataset/data.yaml
"""

import argparse
import glob
import os


def train(args):
    from ultralytics import YOLO

    model = YOLO("yolov8n-seg.pt")

    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.size,
        batch=args.batch,
        workers=args.workers,
        device=args.device,
        project="runs/segment",
        name="table_seg",
        exist_ok=True,
        patience=20,
        lr0=0.01,
        lrf=0.01,
        warmup_epochs=5,
        hsv_h=0.015,
        hsv_s=0.5,
        hsv_v=0.3,
        degrees=10.0,
        translate=0.1,
        scale=0.3,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        copy_paste=0.1,
        save=True,
        save_period=10,
        val=True,
        plots=True,
    )

    best_path = str(model.trainer.best)
    print(f"\nTraining completato. Best model: {best_path}")
    return best_path


def export_onnx(model_path, img_size, output_dir):
    from ultralytics import YOLO
    import shutil

    model = YOLO(model_path)
    os.makedirs(output_dir, exist_ok=True)

    model.export(format="onnx", imgsz=img_size, simplify=True, opset=17, half=False)

    src_onnx = model_path.replace(".pt", ".onnx")
    dst_onnx = os.path.join(output_dir, f"yolov8n_seg_table_{img_size}.onnx")

    if not os.path.exists(src_onnx):
        print(f"Errore: ONNX non trovato in {src_onnx}")
        return None

    shutil.copy2(src_onnx, dst_onnx)
    size_mb = os.path.getsize(dst_onnx) / 1e6
    print(f"ONNX FP32 esportato: {dst_onnx} ({size_mb:.1f} MB)")
    return dst_onnx


def quantize_int8(onnx_path, output_dir, img_size, data_dir=None):
    """Quantizzazione post-export con onnxruntime.quantization."""
    from onnxruntime.quantization import quantize_dynamic, QuantType

    dst = os.path.join(output_dir, f"yolov8n_seg_table_{img_size}_int8.onnx")

    quantize_dynamic(
        onnx_path,
        dst,
        weight_type=QuantType.QInt8,
    )

    size_mb = os.path.getsize(dst) / 1e6
    print(f"ONNX INT8 esportato: {dst} ({size_mb:.1f} MB)")

    # Verifica
    import numpy as np
    import onnxruntime as ort
    session = ort.InferenceSession(dst)
    dummy = np.random.randn(1, 3, img_size, img_size).astype(np.float32)
    outputs = session.run(None, {session.get_inputs()[0].name: dummy})
    print(f"Verifica OK: {len(outputs)} output(s)")
    for i, out in enumerate(outputs):
        print(f"  output[{i}]: shape={out.shape}")

    return dst


def validate(model_path, data_yaml):
    from ultralytics import YOLO

    model = YOLO(model_path)
    metrics = model.val(data=data_yaml)

    print(f"\nBox  mAP50: {metrics.box.map50:.4f}  mAP50-95: {metrics.box.map:.4f}")
    print(f"Mask mAP50: {metrics.seg.map50:.4f}  mAP50-95: {metrics.seg.map:.4f}")
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="../yolo_dataset/data.yaml")
    parser.add_argument("--output", default="../models/trained")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--size", type=int, default=256)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--device", default="")
    parser.add_argument("--export", type=str, default=None, help="Path .pt da esportare (skip training)")
    parser.add_argument("--int8", action="store_true", help="Quantizzazione INT8 post-export")
    parser.add_argument("--validate-only", type=str, default=None, help="Path .pt da validare")
    args = parser.parse_args()

    if args.validate_only:
        validate(args.validate_only, args.data)
    elif args.export:
        fp32_path = export_onnx(args.export, args.size, args.output)
        if args.int8 and fp32_path:
            quantize_int8(fp32_path, args.output, args.size)
    else:
        best_path = train(args)
        validate(best_path, args.data)
        os.makedirs(args.output, exist_ok=True)
        fp32_path = export_onnx(best_path, args.size, args.output)
        if args.int8 and fp32_path:
            quantize_int8(fp32_path, args.output, args.size)


if __name__ == "__main__":
    main()
