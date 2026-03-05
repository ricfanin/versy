#!/usr/bin/env python3
"""
Semantic segmentation in tempo reale da webcam USB.
Uso: python3 inference_rpi.py [--model deeplabv3|segformer] [--camera 0]
"""
import argparse
import time

import cv2
import numpy as np

try:
    from tflite_runtime.interpreter import Interpreter
except ImportError:
    from tensorflow.lite import Interpreter

MODELS = {
    "deeplabv3": {
        "path": "models/deeplabv3_pascal.tflite",
        "size": (257, 257),
        "table_class": 11,
        "normalize": False,
    },
    "segformer": {
        "path": "models/segformer_ade20k.tflite",
        "size": (512, 512),
        "table_class": [15, 33],
        "floor_class": 3,
        "normalize": True,
    },
}


def load_model(name):
    cfg = MODELS[name]
    interpreter = Interpreter(model_path=cfg["path"])
    interpreter.allocate_tensors()
    return interpreter, cfg


def preprocess(frame, cfg):
    img = cv2.resize(frame, cfg["size"])
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    if cfg["normalize"]:
        img = img.astype(np.float32) / 255.0
        img = (img - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
        img = np.transpose(img, (2, 0, 1))
        return np.expand_dims(img, 0).astype(np.float32)

    return np.expand_dims(img, 0).astype(np.uint8)


def inference(interpreter, input_data):
    inp = interpreter.get_input_details()[0]
    out = interpreter.get_output_details()[0]

    interpreter.set_tensor(inp["index"], input_data)
    interpreter.invoke()
    return interpreter.get_tensor(out["index"])


def get_table_mask(output, size, model_name, cfg):
    if model_name == "segformer":
        mask = np.argmax(output[0], axis=0)
    else:
        mask = np.argmax(output[0], axis=-1)

    mask = cv2.resize(mask.astype(np.uint8), size, interpolation=cv2.INTER_NEAREST)

    classes = cfg["table_class"]
    if isinstance(classes, int):
        classes = [classes]

    table = np.zeros_like(mask, dtype=np.uint8)
    for c in classes:
        table |= (mask == c).astype(np.uint8)

    return table * 255


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=MODELS.keys(), default="deeplabv3")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    args = parser.parse_args()

    print(f"Carico {args.model}...")
    interpreter, cfg = load_model(args.model)

    print(f"Apro camera {args.camera}...")
    cap = cv2.VideoCapture(args.camera)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    if not cap.isOpened():
        print("Errore: impossibile aprire la camera")
        return

    print("Premi 'q' per uscire, 's' per salvare frame")

    fps_avg = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        t0 = time.perf_counter()

        input_data = preprocess(frame, cfg)
        output = inference(interpreter, input_data)
        table_mask = get_table_mask(output, (frame.shape[1], frame.shape[0]), args.model, cfg)

        elapsed = time.perf_counter() - t0
        fps = 1.0 / elapsed
        fps_avg.append(fps)
        if len(fps_avg) > 30:
            fps_avg.pop(0)

        # Overlay verde sul tavolo
        overlay = frame.copy()
        overlay[table_mask > 0] = [0, 255, 0]
        result = cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)

        # Info
        cv2.putText(result, f"FPS: {np.mean(fps_avg):.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(result, f"Model: {args.model}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Segmentation", result)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("s"):
            cv2.imwrite("frame.png", frame)
            cv2.imwrite("mask.png", table_mask)
            print("Salvato: frame.png, mask.png")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
