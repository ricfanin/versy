#!/usr/bin/env python3
"""
Fine-tune SegFormer-B0 per semantic segmentation su dataset Roboflow.
Classi: 0=background, 1=table

Uso:
    pip install torch torchvision transformers pillow albumentations evaluate
    python train_segformer.py --data ../roboflow_dataset --epochs 50 --batch 8

Export ONNX per RPi4:
    python train_segformer.py --export best_model --size 128
"""

import argparse
import os

import albumentations as A
import evaluate
import numpy as np
import torch
from albumentations.pytorch import ToTensorV2
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from transformers import SegformerForSemanticSegmentation


# ---------- Dataset ----------

class RoboflowSegDataset(Dataset):
    """Dataset Roboflow con immagini .jpg e maschere _mask.png."""

    def __init__(self, root_dir, transform=None, img_size=512):
        self.root_dir = root_dir
        self.transform = transform
        self.img_size = img_size

        self.images = sorted(
            f for f in os.listdir(root_dir)
            if f.endswith(".jpg") and not f.endswith("_mask.png")
        )
        # Verifica che ogni immagine abbia la maschera corrispondente
        self.pairs = []
        for img_name in self.images:
            mask_name = img_name.replace(".jpg", "_mask.png")
            if os.path.exists(os.path.join(root_dir, mask_name)):
                self.pairs.append((img_name, mask_name))

        print(f"  {root_dir}: {len(self.pairs)} coppie immagine/maschera")

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        img_name, mask_name = self.pairs[idx]

        image = np.array(Image.open(
            os.path.join(self.root_dir, img_name)
        ).convert("RGB"))

        mask = np.array(Image.open(
            os.path.join(self.root_dir, mask_name)
        ).convert("L"))

        # Binarizza la maschera (0=background, 1=table)
        mask = (mask > 0).astype(np.int64)

        if self.transform:
            transformed = self.transform(image=image, mask=mask)
            image = transformed["image"]
            mask = transformed["mask"]

        return {"pixel_values": image.float(), "labels": mask.long()}


def get_transforms(img_size, is_train=True):
    """Augmentation per training, solo resize per validation."""
    if is_train:
        return A.Compose([
            A.Resize(img_size, img_size),
            A.HorizontalFlip(p=0.5),
            A.RandomBrightnessContrast(p=0.3),
            A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.15, rotate_limit=15, p=0.4),
            A.GaussNoise(p=0.2),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ToTensorV2(),
        ])
    return A.Compose([
        A.Resize(img_size, img_size),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2(),
    ])


# ---------- Training ----------

def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    num_classes = 2  # background + table
    img_size = args.size

    # Modello pre-trained su ADE20K, fine-tune per 2 classi
    model = SegformerForSemanticSegmentation.from_pretrained(
        "nvidia/segformer-b0-finetuned-ade-512-512",
        num_labels=num_classes,
        ignore_mismatched_sizes=True,
    ).to(device)

    # Dataset
    train_ds = RoboflowSegDataset(
        os.path.join(args.data, "train"),
        transform=get_transforms(img_size, is_train=True),
        img_size=img_size,
    )
    val_ds = RoboflowSegDataset(
        os.path.join(args.data, "valid"),
        transform=get_transforms(img_size, is_train=False),
        img_size=img_size,
    )

    train_loader = DataLoader(
        train_ds, batch_size=args.batch, shuffle=True,
        num_workers=args.workers, pin_memory=True,
    )
    val_loader = DataLoader(
        val_ds, batch_size=args.batch, shuffle=False,
        num_workers=args.workers, pin_memory=True,
    )

    # Optimizer e scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    # Metrica IoU
    iou_metric = evaluate.load("mean_iou")

    best_miou = 0.0
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)

    print(f"\nTraining: {args.epochs} epochs, img_size={img_size}, batch={args.batch}, lr={args.lr}")
    print(f"Train: {len(train_ds)} | Val: {len(val_ds)}\n")

    for epoch in range(args.epochs):
        # --- Train ---
        model.train()
        train_loss = 0.0

        for batch in train_loader:
            pixel_values = batch["pixel_values"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(pixel_values=pixel_values, labels=labels)
            loss = outputs.loss

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            train_loss += loss.item()

        scheduler.step()
        avg_train_loss = train_loss / len(train_loader)

        # --- Validation ---
        model.eval()
        val_loss = 0.0

        with torch.no_grad():
            for batch in val_loader:
                pixel_values = batch["pixel_values"].to(device)
                labels = batch["labels"].to(device)

                outputs = model(pixel_values=pixel_values, labels=labels)
                val_loss += outputs.loss.item()

                # Upsample logits alla dimensione della maschera
                logits = outputs.logits
                upsampled = torch.nn.functional.interpolate(
                    logits, size=(img_size, img_size),
                    mode="bilinear", align_corners=False,
                )
                preds = upsampled.argmax(dim=1).cpu().numpy()
                refs = labels.cpu().numpy()

                iou_metric.add_batch(
                    predictions=preds,
                    references=refs,
                )

        avg_val_loss = val_loss / len(val_loader)
        metrics = iou_metric.compute(
            num_labels=num_classes,
            ignore_index=255,
        )
        miou = metrics["mean_iou"]

        print(
            f"Epoch {epoch+1:3d}/{args.epochs} | "
            f"Train Loss: {avg_train_loss:.4f} | "
            f"Val Loss: {avg_val_loss:.4f} | "
            f"mIoU: {miou:.4f} | "
            f"LR: {scheduler.get_last_lr()[0]:.6f}"
        )

        # Salva il modello migliore
        if miou > best_miou:
            best_miou = miou
            save_path = os.path.join(output_dir, "best_model")
            model.save_pretrained(save_path)
            print(f"  -> Nuovo best mIoU: {miou:.4f}, salvato in {save_path}")

    # Salva anche l'ultimo modello
    model.save_pretrained(os.path.join(output_dir, "last_model"))
    print(f"\nTraining completato! Best mIoU: {best_miou:.4f}")
    print(f"Modelli salvati in: {output_dir}/")

    return os.path.join(output_dir, "best_model")


# ---------- Export ONNX ----------

def export_onnx(model_path, img_size, output_dir):
    """Esporta il modello in ONNX per inference su RPi4."""
    device = torch.device("cpu")

    model = SegformerForSemanticSegmentation.from_pretrained(model_path)
    model.eval().to(device)

    dummy = torch.randn(1, 3, img_size, img_size)
    onnx_path = os.path.join(output_dir, f"segformer_table_{img_size}.onnx")

    torch.onnx.export(
        model,
        dummy,
        onnx_path,
        input_names=["pixel_values"],
        output_names=["logits"],
        opset_version=17,
        do_constant_folding=True,
        dynamic_axes={
            "pixel_values": {0: "batch"},
            "logits": {0: "batch"},
        },
    )

    size_mb = os.path.getsize(onnx_path) / 1e6
    print(f"ONNX esportato: {onnx_path} ({size_mb:.1f} MB)")

    # Verifica con onnxruntime
    try:
        import onnxruntime as ort
        session = ort.InferenceSession(onnx_path)
        out = session.run(None, {"pixel_values": dummy.numpy()})
        print(f"Verifica OK: output shape = {out[0].shape}")
    except ImportError:
        print("Installa onnxruntime per verificare: pip install onnxruntime")

    return onnx_path


# ---------- Main ----------

def main():
    parser = argparse.ArgumentParser(description="Fine-tune SegFormer-B0 per table segmentation")
    parser.add_argument("--data", default="../roboflow_dataset", help="Path al dataset Roboflow")
    parser.add_argument("--output", default="../models/trained", help="Directory output modelli")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--lr", type=float, default=6e-5)
    parser.add_argument("--size", type=int, default=256, help="Risoluzione input (default 256)")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--export", type=str, default=None,
                        help="Path modello da esportare in ONNX (skip training)")

    args = parser.parse_args()

    if args.export:
        # Solo export ONNX
        export_onnx(args.export, args.size, args.output)
    else:
        # Training + export
        best_path = train(args)
        print("\n--- Export ONNX ---")
        os.makedirs(args.output, exist_ok=True)
        # Export a 128 e 256 per RPi4
        for size in [128, 256]:
            export_onnx(best_path, size, args.output)


if __name__ == "__main__":
    main()
