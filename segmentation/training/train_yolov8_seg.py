"""
Script per il training di YOLOv8n-seg su dataset di table segmentation
ed export del modello in formato ONNX.

Uso:
    python train_yolov8_seg.py --data ../yolo_dataset/data.yaml --epochs 100
    python train_yolov8_seg.py --export best.pt --size 256
"""

import argparse
import os


def train(args):
    """Esegue il training del modello YOLOv8n-seg."""
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
        # early stopping
        patience=20,
        # learning rate
        lr0=0.01,
        lrf=0.01,
        warmup_epochs=5,
        # augmentation
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
        # salvataggio e validazione
        save=True,
        save_period=10,
        val=True,
        plots=True,
    )

    best = str(model.trainer.best)
    print(f"\nTraining completato. Best model: {best}")
    return best


def export_onnx(model_path, img_size, output_dir):
    """Esporta il modello .pt in formato ONNX."""
    from ultralytics import YOLO
    import shutil

    model = YOLO(model_path)
    os.makedirs(output_dir, exist_ok=True)

    model.export(format="onnx", imgsz=img_size, simplify=True, opset=17, half=False)

    src = model_path.replace(".pt", ".onnx")
    dst = os.path.join(output_dir, f"yolov8n_seg_table_{img_size}.onnx")

    if not os.path.exists(src):
        print(f"Errore: file ONNX non trovato in {src}")
        return None

    shutil.copy2(src, dst)
    size_mb = os.path.getsize(dst) / 1e6
    print(f"ONNX esportato: {dst} ({size_mb:.1f} MB)")
    return dst


def validate(model_path, data_yaml):
    """Valida il modello e stampa le metriche mAP."""
    from ultralytics import YOLO

    model = YOLO(model_path)
    metrics = model.val(data=data_yaml)

    print(f"\nBox  mAP50: {metrics.box.map50:.4f}  mAP50-95: {metrics.box.map:.4f}")
    print(f"Mask mAP50: {metrics.seg.map50:.4f}  mAP50-95: {metrics.seg.map:.4f}")
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Training e export YOLOv8n-seg")
    parser.add_argument("--data", default="../yolo_dataset/data.yaml", help="Path al data.yaml")
    parser.add_argument("--output", default="../models/trained", help="Cartella output modelli")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--size", type=int, default=256, help="Dimensione immagine")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--device", default="", help="Device per il training (es. 'cpu', '0')")
    parser.add_argument("--export", type=str, default=None, help="Path .pt da esportare (skip training)")
    parser.add_argument("--validate-only", type=str, default=None, help="Path .pt da validare")
    args = parser.parse_args()

    if args.validate_only:
        validate(args.validate_only, args.data)
    elif args.export:
        export_onnx(args.export, args.size, args.output)
    else:
        best = train(args)
        validate(best, args.data)
        os.makedirs(args.output, exist_ok=True)
        export_onnx(best, args.size, args.output)


if __name__ == "__main__":
    main()
