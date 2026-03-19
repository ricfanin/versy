#!/usr/bin/env python3
"""
Train YOLOv8n-seg per table segmentation ed esporta ONNX per RPi4.

Uso:
    pip install ultralytics

    # Training
    python train_yolov8_seg.py --data ../yolo_dataset/data.yaml --epochs 100

    # Solo export ONNX
    python train_yolov8_seg.py --export runs/segment/table_seg/weights/best.pt --size 256

    # Training + export a piu' risoluzioni
    python train_yolov8_seg.py --data ../yolo_dataset/data.yaml --epochs 100 --size 256
"""

import argparse
import os


def train(args):
    from ultralytics import YOLO

    model = YOLO("yolov8n-seg.pt")  # Pre-trained su COCO-seg

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
        # Ottimizzazioni per dataset piccolo
        patience=20,
        lr0=0.01,
        lrf=0.01,
        warmup_epochs=5,
        # Augmentation
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
        # Salvataggio
        save=True,
        save_period=10,
        val=True,
        plots=True,
    )

    best_path = os.path.join("runs", "segment", "table_seg", "weights", "best.pt")
    print(f"\nTraining completato! Best model: {best_path}")
    return best_path


def export_onnx(model_path, img_size, output_dir):
    """Esporta YOLOv8-seg in ONNX per RPi4."""
    from ultralytics import YOLO

    model = YOLO(model_path)
    os.makedirs(output_dir, exist_ok=True)

    model.export(
        format="onnx",
        imgsz=img_size,
        simplify=True,
        opset=17,
        half=False,  # RPi4 non supporta FP16
    )

    src_onnx = model_path.replace(".pt", ".onnx")
    dst_onnx = os.path.join(output_dir, f"yolov8n_seg_table_{img_size}.onnx")

    if os.path.exists(src_onnx):
        import shutil
        shutil.copy2(src_onnx, dst_onnx)
        size_mb = os.path.getsize(dst_onnx) / 1e6
        print(f"ONNX esportato: {dst_onnx} ({size_mb:.1f} MB)")
    else:
        print(f"Errore: ONNX non trovato in {src_onnx}")
        return None

    # Verifica con onnxruntime
    try:
        import numpy as np
        import onnxruntime as ort
        session = ort.InferenceSession(dst_onnx)
        input_info = session.get_inputs()[0]
        dummy = np.random.randn(1, 3, img_size, img_size).astype(np.float32)
        outputs = session.run(None, {input_info.name: dummy})
        print(f"Verifica OK: {len(outputs)} output(s)")
        for i, out in enumerate(outputs):
            print(f"  output[{i}]: shape={out.shape}, dtype={out.dtype}")
    except ImportError:
        print("Installa onnxruntime per verificare: pip install onnxruntime")

    return dst_onnx


def validate(model_path, data_yaml):
    """Valida il modello sul validation set."""
    from ultralytics import YOLO

    model = YOLO(model_path)
    metrics = model.val(data=data_yaml)

    print(f"\n--- Validation Results ---")
    print(f"Box mAP50: {metrics.box.map50:.4f}")
    print(f"Box mAP50-95: {metrics.box.map:.4f}")
    print(f"Mask mAP50: {metrics.seg.map50:.4f}")
    print(f"Mask mAP50-95: {metrics.seg.map:.4f}")
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Train YOLOv8n-seg per table segmentation")
    parser.add_argument("--data", default="../yolo_dataset/data.yaml", help="Path a data.yaml")
    parser.add_argument("--output", default="../models/trained", help="Directory output modelli")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--size", type=int, default=256, help="Risoluzione input")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--device", default="", help="cuda device o cpu")
    parser.add_argument("--export", type=str, default=None,
                        help="Path modello .pt da esportare (skip training)")
    parser.add_argument("--validate-only", type=str, default=None,
                        help="Path modello .pt da validare (skip training)")

    args = parser.parse_args()

    if args.validate_only:
        validate(args.validate_only, args.data)
    elif args.export:
        export_onnx(args.export, args.size, args.output)
    else:
        best_path = train(args)

        print("\n--- Validazione finale ---")
        validate(best_path, args.data)

        print("\n--- Export ONNX ---")
        os.makedirs(args.output, exist_ok=True)
        export_onnx(best_path, args.size, args.output)


if __name__ == "__main__":
    main()
