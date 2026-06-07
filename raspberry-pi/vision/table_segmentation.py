from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

from utils.debug import get_logger

# Initialize module logger
logger = get_logger("table_segmentation")


class TableSegmentor:
    def __init__(
        self,
        model_path=None,
        input_size=256,
        conf_threshold=0.4,
        nms_threshold=0.04,
        mask_threshold=0.4,
        erode_px=1,
        num_threads=4,
    ):
        if model_path is None:
            # Percorso relativo al file corrente (stesso pattern di ArucoDetector)
            model_path = Path(__file__).parent / "models" / "table_seg.onnx"

        opts = ort.SessionOptions()
        opts.intra_op_num_threads = num_threads
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        self.session = ort.InferenceSession(
            str(model_path), opts, providers=["CPUExecutionProvider"]
        )
        self.input_name = self.session.get_inputs()[0].name
        self.input_size = input_size
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        self.mask_threshold = mask_threshold
        self.erode_px = erode_px

        self.last_stats = {}

        logger.info(f"TableSegmentor caricato: {model_path}")

    def detect(self, frame, show=False):
        """Esegue la segmentazione del tavolo sul frame.

        Args:
            frame: numpy array (H, W, 3). Il frame da robot.camera e' RGB888.
            show: se True mostra l'overlay verde della maschera in una finestra.

        Returns:
            mask: numpy array (H, W) uint8 con valori 0 (background) o 255 (tavolo).
        """
        h, w = frame.shape[:2]
        input_data = self.__preprocess(frame)
        outputs = self.session.run(None, {self.input_name: input_data})
        mask = self.__postprocess(outputs, h, w)

        # Riallinea la maschera al frame display (stesso pattern di ArucoDetector):
        # in __preprocess unflippiamo il frame per dare al modello l'orientazione di
        # training; qui flippiamo la mask per riportarla nello spazio del frame display.
        mask = cv2.flip(mask, 0)

        if show:
            self.__draw_debug(frame, mask)

        return mask

    def __preprocess(self, frame):
        """Unflip + resize + BGR->RGB + normalizzazione [0,1] + tensor (1, 3, S, S).

        NB1: la camera (robot/camera.py) ha vflip=True, quindi il frame arriva
        gia' flippato verticalmente. Il modello e' stato addestrato senza vflip
        nelle augmentation: lo unflippiamo qui per dargli l'orientazione "diritta".
        Stesso pattern di ArucoDetector.__preprocess.

        NB2: picamera2 con format="RGB888" emette in realta' un buffer BGR
        (quirk di libcamera, il nome e' little-endian rispetto al byte order).
        Il modello vuole RGB, quindi convertiamo. Stessa conversione di
        segmentation/inference.py:40.
        """
        frame_unflipped = cv2.flip(frame, 0)
        img = cv2.resize(frame_unflipped, (self.input_size, self.input_size))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))
        return np.expand_dims(img, 0)

    def __postprocess(self, outputs, frame_h, frame_w):
        """Restituisce maschera binaria (0/255) dalle output YOLOv8-seg."""
        detections = outputs[0][0].T  # (N candidati, 37 valori)
        prototypes = outputs[1][0]  # (32, mask_h, mask_w)

        # ogni candidato: [x, y, w, h, score, 32 coefficienti maschera]
        boxes = detections[:, :4]
        scores = detections[:, 4]
        mask_coeffs = detections[:, 5:]

        n_candidates = len(scores)
        top5_raw = np.sort(scores)[-5:][::-1]

        empty_mask = np.zeros((frame_h, frame_w), dtype=np.uint8)
        keep = scores > self.conf_threshold
        if not np.any(keep):
            self.last_stats = {
                "n_candidates": n_candidates,
                "top5_raw_scores": top5_raw.tolist(),
                "n_above_conf": 0,
                "n_after_nms": 0,
                "kept_scores": [],
                "table_pct": 0.0,
            }
            return empty_mask
        boxes = boxes[keep]
        scores = scores[keep]
        mask_coeffs = mask_coeffs[keep]

        n_above_conf = len(scores)

        # xywh -> xyxy
        half_w = boxes[:, 2] / 2
        half_h = boxes[:, 3] / 2
        x1 = boxes[:, 0] - half_w
        y1 = boxes[:, 1] - half_h
        x2 = boxes[:, 0] + half_w
        y2 = boxes[:, 1] + half_h
        boxes_xyxy = np.stack([x1, y1, x2, y2], axis=1)

        # NMS: rimuovi box duplicati
        indices = cv2.dnn.NMSBoxes(
            boxes_xyxy.tolist(),
            scores.tolist(),
            self.conf_threshold,
            self.nms_threshold,
        )
        if len(indices) == 0:
            self.last_stats = {
                "n_candidates": n_candidates,
                "top5_raw_scores": top5_raw.tolist(),
                "n_above_conf": n_above_conf,
                "n_after_nms": 0,
                "kept_scores": [],
                "table_pct": 0.0,
            }
            return empty_mask
        indices = np.array(indices).flatten()

        kept_scores = scores[indices]

        # ricostruisci maschera combinando i 32 prototipi con i coefficienti
        mask_h, mask_w = prototypes.shape[1], prototypes.shape[2]
        final_mask = np.zeros((frame_h, frame_w), dtype=np.uint8)

        for i in indices:
            raw = np.tensordot(mask_coeffs[i], prototypes, axes=([0], [0]))
            raw = 1.0 / (1.0 + np.exp(-raw))  # sigmoid

            # crop al bounding box (in coordinate prototype)
            box = boxes_xyxy[i]
            sx, sy = mask_w / self.input_size, mask_h / self.input_size
            bx1 = max(0, int(box[0] * sx))
            by1 = max(0, int(box[1] * sy))
            bx2 = min(mask_w, int(box[2] * sx))
            by2 = min(mask_h, int(box[3] * sy))
            cropped = np.zeros_like(raw)
            cropped[by1:by2, bx1:bx2] = raw[by1:by2, bx1:bx2]

            resized = cv2.resize(cropped, (frame_w, frame_h))
            final_mask[resized > self.mask_threshold] = 255

        if self.erode_px > 0:
            k = 2 * self.erode_px + 1
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
            final_mask = cv2.erode(final_mask, kernel, iterations=1)

        table_pct = (final_mask > 0).mean() * 100
        self.last_stats = {
            "n_candidates": n_candidates,
            "top5_raw_scores": top5_raw.tolist(),
            "n_above_conf": n_above_conf,
            "n_after_nms": len(indices),
            "kept_scores": kept_scores.tolist(),
            "table_pct": table_pct,
        }

        return final_mask

    def __draw_debug(self, frame, mask):
        """Overlay verde della maschera sul frame e visualizzazione."""
        overlay = frame.copy()
        overlay[mask > 0] = [0, 255, 0]
        result = cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)

        table_pct = (mask > 0).mean() * 100
        cv2.putText(
            result,
            f"Table: {table_pct:.1f}% | {self.input_size}px",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )
        cv2.imshow("table_segmentation", result)
        cv2.waitKey(1)
