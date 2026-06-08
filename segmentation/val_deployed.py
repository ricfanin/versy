"""Validazione del modello ONNX effettivamente usato dal robot (256px)."""
import os
from pathlib import Path

os.environ["YOLO_OFFLINE"] = "True"
os.environ["MPLBACKEND"] = "Agg"

from ultralytics import YOLO


def main():
    model_path = (
        Path(__file__).parent.parent
        / "raspberry-pi" / "vision" / "models" / "table_seg.onnx"
    )
    data_path = Path(__file__).parent / "yolo_dataset_v4" / "data.yaml"

    model = YOLO(str(model_path), task="segment")
    metrics = model.val(
        data=str(data_path),
        imgsz=256,
        batch=1,
        split="val",
        conf=0.001,
        iou=0.6,
        workers=0,            # niente multiprocessing (deadlock su Windows)
        project="runs/segment",
        name="val_deployed_256",
        plots=True,
        verbose=True,
    )

    print("\n========= RISULTATI MODELLO ROBOT (table_seg.onnx, 256px) =========")
    print(f"Box   -> P={metrics.box.mp:.4f}  R={metrics.box.mr:.4f}  "
          f"mAP50={metrics.box.map50:.4f}  mAP50-95={metrics.box.map:.4f}")
    print(f"Mask  -> P={metrics.seg.mp:.4f}  R={metrics.seg.mr:.4f}  "
          f"mAP50={metrics.seg.map50:.4f}  mAP50-95={metrics.seg.map:.4f}")
    print(f"Inferenza: {metrics.speed['inference']:.1f} ms/img")
    print("===================================================================")


if __name__ == "__main__":
    main()
