#!/usr/bin/env python3
"""
Converte dataset COCO Segmentation (RLE) da Roboflow in formato YOLOv8 Segmentation.

Uso:
    pip install pycocotools opencv-python
    python convert_coco_to_yolo.py --zip "../My First Project.v2i.coco-segmentation.zip" --output ../yolo_dataset
"""

import argparse
import json
import os
import zipfile

import cv2
import numpy as np
from pycocotools import mask as mask_util


def rle_to_polygons(rle_seg, img_h, img_w, min_area=100):
    """Converte RLE segmentation in poligoni normalizzati YOLO."""
    # Decodifica RLE in maschera binaria
    binary_mask = mask_util.decode(rle_seg).astype(np.uint8)

    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    polygons = []
    for contour in contours:
        if cv2.contourArea(contour) < min_area:
            continue

        # Semplifica contorno
        epsilon = 0.005 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        if len(approx) < 3:
            continue

        # Normalizza coordinate 0-1
        points = approx.reshape(-1, 2)
        normalized = []
        for px, py in points:
            normalized.append(f"{px / img_w:.6f}")
            normalized.append(f"{py / img_h:.6f}")

        polygons.append(normalized)

    return polygons


def convert_split(zip_ref, split, output_dir, min_area=100):
    """Converte un split COCO in formato YOLO seg."""
    ann_path = f"{split}/_annotations.coco.json"
    try:
        ann_data = json.loads(zip_ref.read(ann_path))
    except KeyError:
        print(f"  {split}: _annotations.coco.json non trovato, skip")
        return 0

    img_out = os.path.join(output_dir, "images", split)
    lbl_out = os.path.join(output_dir, "labels", split)
    os.makedirs(img_out, exist_ok=True)
    os.makedirs(lbl_out, exist_ok=True)

    # Mappa image_id -> info
    images = {img["id"]: img for img in ann_data["images"]}

    # Mappa category: trova l'id di "table"
    cat_map = {}
    for cat in ann_data["categories"]:
        if cat["name"] != "objects":  # Skip la supercategory
            cat_map[cat["id"]] = 0  # Mappa tutto a classe 0 per YOLO

    # Raggruppa annotazioni per immagine
    ann_by_img = {}
    for ann in ann_data["annotations"]:
        img_id = ann["image_id"]
        if img_id not in ann_by_img:
            ann_by_img[img_id] = []
        ann_by_img[img_id].append(ann)

    converted = 0
    for img_id, img_info in images.items():
        file_name = img_info["file_name"]
        img_h = img_info["height"]
        img_w = img_info["width"]

        # Estrai immagine dallo zip
        img_zip_path = f"{split}/{file_name}"
        try:
            img_data = zip_ref.read(img_zip_path)
            with open(os.path.join(img_out, file_name), "wb") as f:
                f.write(img_data)
        except KeyError:
            continue

        # Converti annotazioni
        lines = []
        annotations = ann_by_img.get(img_id, [])
        for ann in annotations:
            cat_id = ann["category_id"]
            if cat_id not in cat_map:
                continue

            yolo_class = cat_map[cat_id]
            seg = ann["segmentation"]

            # Gestisci sia RLE che polygon format
            if isinstance(seg, dict):
                # RLE format
                polygons = rle_to_polygons(seg, img_h, img_w, min_area)
            elif isinstance(seg, list):
                # Polygon format diretto
                polygons = []
                for poly in seg:
                    if len(poly) < 6:
                        continue
                    normalized = []
                    for i in range(0, len(poly), 2):
                        normalized.append(f"{poly[i] / img_w:.6f}")
                        normalized.append(f"{poly[i + 1] / img_h:.6f}")
                    polygons.append(normalized)
            else:
                continue

            for poly in polygons:
                line = f"{yolo_class} " + " ".join(poly)
                lines.append(line)

        # Scrivi label file
        label_name = os.path.splitext(file_name)[0] + ".txt"
        with open(os.path.join(lbl_out, label_name), "w") as f:
            f.write("\n".join(lines))

        converted += 1

    print(f"  {split}: {converted} immagini, {len(ann_data['annotations'])} annotazioni")
    return converted


def main():
    parser = argparse.ArgumentParser(description="COCO Segmentation -> YOLO Segmentation")
    parser.add_argument("--zip", required=True, help="Path al file .zip COCO Segmentation")
    parser.add_argument("--output", default="../yolo_dataset", help="Directory output")
    parser.add_argument("--min-area", type=int, default=100, help="Area minima contorno (px)")
    args = parser.parse_args()

    print(f"Conversione: {args.zip} -> {args.output}")
    os.makedirs(args.output, exist_ok=True)

    with zipfile.ZipFile(args.zip, "r") as z:
        total = 0
        for split in ["train", "valid", "test"]:
            total += convert_split(z, split, args.output, args.min_area)

    # Crea data.yaml
    abs_path = os.path.abspath(args.output).replace("\\", "/")
    yaml_path = os.path.join(args.output, "data.yaml")
    with open(yaml_path, "w") as f:
        f.write(f"path: {abs_path}\n")
        f.write("train: images/train\n")
        f.write("val: images/valid\n")
        f.write("test: images/test\n")
        f.write("\n")
        f.write("names:\n")
        f.write("  0: table\n")

    print(f"\nTotale: {total} immagini convertite")
    print(f"data.yaml: {yaml_path}")
    print(f"\nProssimo step: python train_yolov8_seg.py --data {yaml_path}")


if __name__ == "__main__":
    main()
