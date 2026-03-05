#!/usr/bin/env python3
"""
Esporta modelli TFLite per semantic segmentation su Raspberry Pi.
- DeepLabV3 (PASCAL VOC): download diretto, 21 classi
- SegFormer (ADE20K): conversione da PyTorch, 150 classi
"""
import os
import shutil
import subprocess
import urllib.request

MODELS_DIR = "models"


def download_deeplabv3():
    """Scarica DeepLabV3 già convertito in TFLite."""
    output = os.path.join(MODELS_DIR, "deeplabv3_pascal.tflite")
    if os.path.exists(output):
        print(f"DeepLabV3 già presente: {output}")
        return output

    url = "https://tfhub.dev/tensorflow/lite-model/deeplabv3/1/metadata/2?lite-format=tflite"
    print("Scarico DeepLabV3...")

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        with open(output, "wb") as f:
            f.write(resp.read())

    print(f"Salvato: {output} ({os.path.getsize(output) / 1e6:.1f} MB)")
    return output


def convert_segformer():
    """Converte SegFormer da PyTorch a TFLite via ONNX."""
    output = os.path.join(MODELS_DIR, "segformer_ade20k.tflite")
    if os.path.exists(output):
        print(f"SegFormer già presente: {output}")
        return output

    try:
        import torch
        from transformers import SegformerForSemanticSegmentation
    except ImportError:
        print("Installa: pip install torch transformers")
        return None

    # Carica modello
    print("Carico SegFormer B0 da HuggingFace...")
    model = SegformerForSemanticSegmentation.from_pretrained(
        "nvidia/segformer-b0-finetuned-ade-512-512"
    )
    model.eval()

    # Export ONNX
    onnx_path = os.path.join(MODELS_DIR, "segformer.onnx")
    print("Converto in ONNX...")
    torch.onnx.export(
        model,
        torch.randn(1, 3, 512, 512),
        onnx_path,
        input_names=["pixel_values"],
        output_names=["logits"],
        opset_version=17,
        do_constant_folding=True,
    )

    # ONNX -> TFLite
    tf_dir = os.path.join(MODELS_DIR, "segformer_tf")
    print("Converto in TFLite...")
    result = subprocess.run(
        ["onnx2tf", "-i", onnx_path, "-o", tf_dir, "-oiqt"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Conversione fallita: {result.stderr[:200]}")
        return None

    # Copia il modello float16 (buon compromesso size/precisione)
    for f in os.listdir(tf_dir):
        if "float16" in f and f.endswith(".tflite"):
            shutil.copy(os.path.join(tf_dir, f), output)
            break

    # Pulizia
    os.remove(onnx_path)
    if os.path.exists(onnx_path + ".data"):
        os.remove(onnx_path + ".data")
    shutil.rmtree(tf_dir)

    print(f"Salvato: {output} ({os.path.getsize(output) / 1e6:.1f} MB)")
    return output


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)

    print("=" * 50)
    print("DEEPLABV3 (PASCAL VOC)")
    print("=" * 50)
    download_deeplabv3()

    print()
    print("=" * 50)
    print("SEGFORMER (ADE20K)")
    print("=" * 50)
    convert_segformer()

    print()
    print("=" * 50)
    print("CLASSI UTILI")
    print("=" * 50)
    print("""
DeepLabV3 (PASCAL VOC, 21 classi):
  0 = background
  9 = chair
  11 = diningtable
  15 = person

SegFormer (ADE20K, 150 classi):
  0 = wall
  3 = floor
  15 = table
  33 = dining_table
  23 = sofa
""")


if __name__ == "__main__":
    main()
