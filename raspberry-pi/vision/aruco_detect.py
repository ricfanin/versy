from pathlib import Path

import cv2
import cv2.aruco as aruco
import numpy as np

from utils.debug import get_logger

# Initialize module logger
logger = get_logger("aruco_detect")


class ArucoDetector:
    def __init__(self, calibration_path=None, marker_size=0.046):
        if calibration_path is None:
            # Percorso relativo al file corrente
            calibration_path = (
                Path(__file__).parent.parent / "config" / "camera_calibration.npz"
            )
        self.aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_100)
        self.aruco_parameters = aruco.DetectorParameters()

        # Piu' finestre di soglia adattiva (6 invece di 3)
        self.aruco_parameters.adaptiveThreshWinSizeMin = 3
        self.aruco_parameters.adaptiveThreshWinSizeMax = 23
        self.aruco_parameters.adaptiveThreshWinSizeStep = 4
        # Corner refinement tramite contorno (stabile per marker piccoli)
        self.aruco_parameters.cornerRefinementMethod = aruco.CORNER_REFINE_CONTOUR
        # Error correction completa (1 bit su DICT_4X4_50)
        self.aruco_parameters.errorCorrectionRate = 1.0
        # Forma piu' tollerante per quadrilateri distorti
        self.aruco_parameters.polygonalApproxAccuracyRate = 0.05
        # Corner distance rilassata per marker piccoli
        self.aruco_parameters.minCornerDistanceRate = 0.02
        # Piu' pixel per cella nella rettifica prospettica
        self.aruco_parameters.perspectiveRemovePixelPerCell = 6

        self.detector = aruco.ArucoDetector(self.aruco_dict, self.aruco_parameters)
        data = np.load(calibration_path)
        self.camera_matrix = data["camera_matrix"]
        self.dist_coeffs = data["dist_coeffs"]
        self.marker_size = marker_size

        self.CANDIDATE_MAX_DISTANCE_PX = 60
        self.CANDIDATE_SIZE_TOLERANCE = 0.5  # perimetro candidato deve essere entro +/-50% dell'ultimo noto

        self.pitch_history = []
        self.PITCH_BUFFER_SIZE = 10

    def detect(self, frame, show=True, expected_ids=None, expected_perimeter=None, perimeter_tolerance=None, last_known_center=None, last_known_id=None, last_known_perimeter=None):
        """restituisce array di markers rilevati fonendo:
        id, rvc, tvec, distance, roll, pitch, yaw, center, confidence.
        Se expected_ids e' fornito (iterable di int), filtra sia i risultati
        sia il disegno di debug ai soli marker con quegli ID.
        Se expected_perimeter e perimeter_tolerance sono forniti, scarta i
        marker il cui perimetro si discosta oltre la tolleranza relativa."""
        h = frame.shape[0]
        pframe = self.__preprocess(frame)
        try:
            corners, ids, rejected = self.detector.detectMarkers(pframe)
        except cv2.error:
            logger.warning("ArUco detectMarkers failed (contour interpolation), skipping frame")
            return []
        expected_set = set(expected_ids) if expected_ids is not None else None
        results = []
        if ids is not None:
            # Punti 3D del marker (ordine: TL, TR, BR, BL)
            half = self.marker_size / 2
            obj_points = np.array([
                [-half, half, 0],
                [half, half, 0],
                [half, -half, 0],
                [-half, -half, 0],
            ], dtype=np.float32)

            # Stima posa sui corners originali (calibrazione corretta)
            # poi sceglie la soluzione IPPE con Z verso la camera
            rvecs = []
            tvecs = []
            for c in corners:
                _, rvec_solutions, tvec_solutions, _ = cv2.solvePnPGeneric(
                    obj_points, c[0], self.camera_matrix, self.dist_coeffs,
                    flags=cv2.SOLVEPNP_IPPE_SQUARE,
                )
                best = 0
                best_score = float('inf')
                for j in range(len(rvec_solutions)):
                    R, _ = cv2.Rodrigues(rvec_solutions[j])
                    t = tvec_solutions[j].flatten()
                    score = np.dot(R[:, 2], t / np.linalg.norm(t))
                    if score < best_score:
                        best_score = score
                        best = j
                rvecs.append(rvec_solutions[best].flatten())
                tvecs.append(tvec_solutions[best].flatten())

            # Corners flippate per il disegno sul frame display
            corners_display = []
            for c in corners:
                cd = c.copy()
                cd[0, :, 1] = h - 1 - cd[0, :, 1]
                corners_display.append(cd)

            for i, marker_id in enumerate(ids):
                if expected_set is not None and int(marker_id[0]) not in expected_set:
                    continue
                marker_data = self.__process_marker_data(
                    i,
                    marker_id[0],
                    corners_display[i],
                    rvecs[i],
                    tvecs[i],
                    h,
                )
                if expected_perimeter is not None and perimeter_tolerance is not None:
                    p = marker_data["perimeter"]
                    if abs(p - expected_perimeter) / expected_perimeter > perimeter_tolerance:
                        logger.info(f"Aruco id={marker_data['id']} scartato per perimetro: {p}")
                        continue
                marker_data["confidence"] = "full"
                results.append(marker_data)

                if show:
                    self.__draw_debug(frame, marker_data, corners_display[i])

        elif last_known_center is not None and rejected is not None and len(rejected) > 0:
            best_candidate = None
            best_dist_sq = float('inf')

            for candidate_corners in rejected:
                # Check dimensioni: il perimetro deve essere simile all'ultimo noto
                if last_known_perimeter is not None:
                    cand_perimeter = self.__compute_perimeter(candidate_corners[0])
                    ratio = cand_perimeter / last_known_perimeter
                    if abs(ratio - 1.0) > self.CANDIDATE_SIZE_TOLERANCE:
                        continue

                center = np.mean(candidate_corners[0], axis=0)
                center_display = (int(center[0]), h - int(center[1]))

                dx = center_display[0] - last_known_center[0]
                dy = center_display[1] - last_known_center[1]
                dist_sq = dx * dx + dy * dy

                if dist_sq < best_dist_sq:
                    best_dist_sq = dist_sq
                    best_candidate = center_display

            if best_candidate is not None and best_dist_sq < self.CANDIDATE_MAX_DISTANCE_PX ** 2:
                results.append({
                    "id": last_known_id if last_known_id is not None else -1,
                    "rvec": None,
                    "tvec": None,
                    "distance": None,
                    "angles": None,
                    "center": best_candidate,
                    "confidence": "low",
                    "perimeter": None,
                })
                logger.info(f"Fallback: rejected candidate at {best_candidate}, dist={best_dist_sq**0.5:.1f}px")

        if show:
            cv2.imshow("frame", frame)
            cv2.waitKey(1)  # Necessario per aggiornare la finestra OpenCV
        if results != []:
            logger.info(f"Rilevati {len(results)} marker(s)")
        return results

    def __preprocess(self, frame):
        """Converte in grigio e applica blur"""
        frame_flipped = cv2.flip(frame, 0)
        gray = cv2.cvtColor(frame_flipped, cv2.COLOR_BGR2GRAY)
        return gray

    @staticmethod
    def __compute_perimeter(corners_pts):
        """Calcola il perimetro di un quadrilatero dai suoi 4 corner points."""
        pts = corners_pts
        perimeter = 0.0
        for i in range(4):
            perimeter += np.linalg.norm(pts[i] - pts[(i + 1) % 4])
        return perimeter

    def __process_marker_data(self, index, m_id, corners, rvec, tvec, frame_height):
        """Calcola distanze, angoli e organizza il dizionario."""
        center = np.mean(corners[0], axis=0)
        roll, pitch, yaw = self.__rotation_vector_to_euler_angles(rvec)
        distance = np.linalg.norm(tvec)
        perimeter = self.__compute_perimeter(corners[0])
        return {
            "id": int(m_id),
            "rvec": rvec,
            "tvec": tvec,
            "distance": float(distance) * 100,
            "angles": (roll, pitch, yaw),
            "center": (int(center[0]), frame_height - int(center[1])),
            "perimeter": float(perimeter),
        }

    def __draw_debug(self, frame, data, corners):
        """Gestisce tutta la parte grafica sul frame."""
        h = frame.shape[0]
        m_id = data["id"]
        dist = data["distance"]
        r, p, y = data["angles"]

        # Contorno ArUco spesso e colorato
        pts = corners[0].reshape((-1, 1, 2)).astype(int)
        cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 0), thickness=3)
        # Cerchi sui corner (rosso=TL, verde=TR, blu=BR, giallo=BL)
        corner_colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255)]
        for i, color in enumerate(corner_colors):
            pt = tuple(corners[0][i].astype(int))
            cv2.circle(frame, pt, 5, color, -1)

        # Assi 3D - proietta nel frame originale (flippato) e poi flippa y per il display
        axis_length = self.marker_size * 0.5
        axis_pts_3d = np.float32([
            [0, 0, 0], [axis_length, 0, 0], [0, axis_length, 0], [0, 0, axis_length]
        ])
        img_pts, _ = cv2.projectPoints(
            axis_pts_3d, data["rvec"], data["tvec"],
            self.camera_matrix, self.dist_coeffs
        )
        img_pts = img_pts.reshape(-1, 2)
        img_pts[:, 1] = h - 1 - img_pts[:, 1]  # flip y per il display
        origin = tuple(img_pts[0].astype(int))
        cv2.line(frame, origin, tuple(img_pts[1].astype(int)), (0, 0, 255), 2)  # X rosso
        cv2.line(frame, origin, tuple(img_pts[2].astype(int)), (0, 255, 0), 2)  # Y verde
        cv2.line(frame, origin, tuple(img_pts[3].astype(int)), (255, 0, 0), 2)  # Z blu

        # Smoothing pitch per debug
        self.pitch_history.append(p)
        if len(self.pitch_history) > self.PITCH_BUFFER_SIZE:
            self.pitch_history.pop(0)
        pitch_avg = np.mean(self.pitch_history)
        pitch_std = np.std(self.pitch_history) if len(self.pitch_history) > 1 else 0

        # Testo in alto a destra
        width = frame.shape[1]
        height = frame.shape[0]
        x_text = width - 320
        line_h = 22
        lines = [
            f"ID:{m_id}  Dist:{dist:.1f}cm  Yaw:{y:.1f}",
        ]
        for i, line in enumerate(lines):
            cv2.putText(
                frame,
                line,
                (x_text, 25 + i * line_h),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                2,
            )

        # Reticolo centro frame
        target_x = width // 2
        target_y = height // 2
        cv2.circle(
            frame, (target_x, target_y), radius=2, color=(255, 0, 0), thickness=-1
        )

    def __rotation_vector_to_euler_angles(self, rvec):
        """Converte il vettore di rotazione in angoli espressi in gradi"""
        R, _ = cv2.Rodrigues(rvec)
        sy = np.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)
        singular = sy < 1e-6
        if not singular:
            x = np.arctan2(R[2, 1], R[2, 2])
            y = np.arctan2(-R[2, 0], sy)
            z = np.arctan2(R[1, 0], R[0, 0])
        else:
            x = np.arctan2(-R[1, 2], R[1, 1])
            y = np.arctan2(-R[2, 0], sy)
            z = 0

        roll = (np.degrees(x)) % 360 - 180
        pitch = (np.degrees(y) + 180) % 360 - 180
        # Yaw=0 quando il marker è dritto (non ruotato di 180° nel suo piano).
        yaw = np.degrees(z) % 360 - 180
        return roll, pitch, yaw
