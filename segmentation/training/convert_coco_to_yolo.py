"""
Script per convertire un dataset COCO Segmentation (da Roboflow) in formato YOLOv8.

Uso:
    python convert_coco_to_yolo.py --zip "dataset.zip" --output ../yolo_dataset
"""

import argparse
import json
import os
import zipfile

import cv2
import numpy as np
from pycocotools import mask as mask_util


def rle_to_polygons(rle, h, w, min_area=100):
    """Converte una maschera RLE in lista di poligoni normalizzati."""
    binary = mask_util.decode(rle).astype(np.uint8)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    polygons = []
    for cnt in contours:
        if cv2.contourArea(cnt) < min_area:
            continue
        eps = 0.005 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, eps, True)
        if len(approx) < 3:
            continue

        pts = approx.reshape(-1, 2)
        norm = []
        for x, y in pts:
            norm.append(f"{x / w:.6f}")
            norm.append(f"{y / h:.6f}")
        polygons.append(norm)

    return polygons


def convert_split(zf, split, out_dir, min_area=100):
    """Converte uno split (train/valid/test) da COCO a YOLO."""
    try:
        data = json.loads(zf.read(f"{split}/_annotations.coco.json"))
    except KeyError:
        print(f"  {split}: annotations non trovate, skip")
        return 0

    img_dir = os.path.join(out_dir, "images", split)
    lbl_dir = os.path.join(out_dir, "labels", split)
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(lbl_dir, exist_ok=True)

    images = {img["id"]: img for img in data["images"]}

    # mappa tutte le categorie (tranne supercategory "objects") a classe 0 = table
    cat_map = {}
    for cat in data["categories"]:
        if cat["name"] != "objects":
            cat_map[cat["id"]] = 0

    # raggruppa annotazioni per immagine
    anns_by_img = {}
    for ann in data["annotations"]:
        anns_by_img.setdefault(ann["image_id"], []).append(ann)

    count = 0
    for img_id, info in images.items():
        fname = info["file_name"]
        h, w = info["height"], info["width"]

        # estrai immagine dallo zip
        try:
            img_bytes = zf.read(f"{split}/{fname}")
            with open(os.path.join(img_dir, fname), "wb") as f:
                f.write(img_bytes)
        except KeyError:
            continue

        # converti annotazioni in formato YOLO
        lines = []
        for ann in anns_by_img.get(img_id, []):
            if ann["category_id"] not in cat_map:
                continue
            cls = cat_map[ann["category_id"]]
            seg = ann["segmentation"]

            if isinstance(seg, dict):
                # formato RLE
                polys = rle_to_polygons(seg, h, w, min_area)
            elif isinstance(seg, list):
                # formato polygon
                polys = []
                for poly in seg:
                    if len(poly) < 6:
                        continue
                    norm = []
                    for i in range(0, len(poly), 2):
                        norm.append(f"{poly[i] / w:.6f}")
                        norm.append(f"{poly[i + 1] / h:.6f}")
                    polys.append(norm)
            else:
                continue

            for p in polys:
                lines.append(f"{cls} " + " ".join(p))

        lbl_name = os.path.splitext(fname)[0] + ".txt"
        with open(os.path.join(lbl_dir, lbl_name), "w") as f:
            f.write("\n".join(lines))
        count += 1

    print(f"  {split}: {count} immagini convertite")
    return count


def main():
    parser = argparse.ArgumentParser(description="Converte COCO Segmentation -> YOLOv8")
    parser.add_argument("--zip", required=True, help="Path al .zip del dataset COCO")
    parser.add_argument("--output", default="../yolo_dataset", help="Cartella output")
    parser.add_argument("--min-area", type=int, default=100, help="Area minima contorno in pixel")
    args = parser.parse_args()

    print(f"Conversione: {args.zip} -> {args.output}")
    os.makedirs(args.output, exist_ok=True)

    total = 0
    with zipfile.ZipFile(args.zip, "r") as zf:
        for split in ["train", "valid", "test"]:
            total += convert_split(zf, split, args.output, args.min_area)

    # genera data.yaml per YOLOv8
    abs_path = os.path.abspath(args.output).replace("\\", "/")
    yaml_path = os.path.join(args.output, "data.yaml")
    with open(yaml_path, "w") as f:
        f.write(f"path: {abs_path}\n")
        f.write("train: images/train\n")
        f.write("val: images/valid\n")
        f.write("test: images/test\n\n")
        f.write("names:\n")
        f.write("  0: table\n")

    print(f"\nTotale: {total} immagini convertite")
    print(f"data.yaml salvato in: {yaml_path}")


if __name__ == "__main__":
    main()
