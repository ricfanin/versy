#!/usr/bin/env python3
"""
Semantic segmentation in tempo reale da webcam USB.
Uso: python3 inference_rpi.py [--model deeplabv3|segformer] [--camera 0] [--res 128]
"""
import argparse
import time
from threading import Thread

import cv2
import numpy as np

try:
    from ai_edge_litert.interpreter import Interpreter
except ImportError:
    try:
        from tflite_runtime.interpreter import Interpreter
    except ImportError:
        from tensorflow.lite import Interpreter

MODELS = {
    "deeplabv3": {
        "path": "models/deeplabv3_pascal.tflite",
        "table_class": 11,
        "normalize": False,
        "runtime": "tflite",
    },
    "segformer256": {
        "path": "models/segformer_256.onnx",
        "table_class": [15, 33],
        "floor_class": 3,
        "normalize": True,
        "runtime": "onnx",
        "fixed_size": (256, 256),
    },
    "segformer128": {
        "path": "models/segformer_128.onnx",
        "table_class": [15, 33],
        "floor_class": 3,
        "normalize": True,
        "runtime": "onnx",
        "fixed_size": (128, 128),
    },
}


class CameraThread:
    """Cattura frame in un thread separato per non bloccare l'inferenza."""

    def __init__(self, src, width, height):
        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.ret, self.frame = self.cap.read()
        self.running = True
        Thread(target=self._update, daemon=True).start()

    def _update(self):
        while self.running:
            self.ret, self.frame = self.cap.read()

    def read(self):
        return self.ret, self.frame

    def stop(self):
        self.running = False
        self.cap.release()

    def isOpened(self):
        return self.cap.isOpened()


def load_model(name, res):
    cfg = MODELS[name].copy()
    if "fixed_size" in cfg:
        cfg["size"] = cfg["fixed_size"]
    else:
        cfg["size"] = (res, res)

    if cfg["runtime"] == "onnx":
        import onnxruntime as ort
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 4
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        session = ort.InferenceSession(cfg["path"], opts, providers=["CPUExecutionProvider"])
        cfg["input_name"] = session.get_inputs()[0].name
        cfg["input_dtype"] = np.float32
        return session, cfg

    interpreter = Interpreter(model_path=cfg["path"], num_threads=4)
    interpreter.allocate_tensors()
    inp = interpreter.get_input_details()[0]
    out = interpreter.get_output_details()[0]
    cfg["input_dtype"] = inp["dtype"]
    cfg["input_index"] = inp["index"]
    cfg["output_index"] = out["index"]
    return interpreter, cfg


def preprocess(frame, cfg):
    img = cv2.resize(frame, cfg["size"])
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    if cfg["normalize"]:
        img = img.astype(np.float32) / 255.0
        img = (img - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
        img = np.transpose(img, (2, 0, 1))
    else:
        img = img.astype(np.float32) / 127.5 - 1.0

    return np.expand_dims(img, 0).astype(cfg["input_dtype"])


def inference(model, cfg, input_data):
    if cfg["runtime"] == "onnx":
        return model.run(None, {cfg["input_name"]: input_data})[0]

    model.set_tensor(cfg["input_index"], input_data)
    model.invoke()
    return model.get_tensor(cfg["output_index"])


def get_table_mask(output, size, model_name, cfg):
    if cfg["runtime"] == "onnx":
        data = output[0] if output.ndim == 4 else output
        mask = np.argmax(data, axis=1)[0]
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
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=240)
    parser.add_argument("--res", type=int, default=128, help="Risoluzione input modello (default 128)")
    args = parser.parse_args()

    print(f"Carico {args.model} (input {args.res}x{args.res})...")
    model, cfg = load_model(args.model, args.res)

    print(f"Apro camera {args.camera} ({args.width}x{args.height})...")
    cam = CameraThread(args.camera, args.width, args.height)

    if not cam.isOpened():
        print("Errore: impossibile aprire la camera")
        return

    print("Premi 'q' per uscire, 's' per salvare frame")

    fps_avg = []
    last_mask = None

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        t0 = time.perf_counter()

        input_data = preprocess(frame, cfg)
        output = inference(model, cfg, input_data)
        table_mask = get_table_mask(output, (frame.shape[1], frame.shape[0]), args.model, cfg)
        last_mask = table_mask

        elapsed = time.perf_counter() - t0
        fps = 1.0 / elapsed
        fps_avg.append(fps)
        if len(fps_avg) > 30:
            fps_avg.pop(0)

        # Overlay verde sul tavolo
        overlay = frame.copy()
        overlay[table_mask > 0] = [0, 255, 0]
        result = cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)

        table_pct = np.sum(table_mask > 0) / table_mask.size * 100
        cv2.putText(result, f"FPS: {np.mean(fps_avg):.1f} | Tavolo: {table_pct:.1f}%", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Segmentation", result)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("s"):
            cv2.imwrite("frame.png", frame)
            cv2.imwrite("mask.png", table_mask)
            print("Salvato: frame.png, mask.png")

    cam.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
