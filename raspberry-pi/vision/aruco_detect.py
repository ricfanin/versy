from pathlib import Path

import cv2
import cv2.aruco as aruco
import numpy as np

from utils.debug import get_logger

# Initialize module logger
logger = get_logger("aruco_detect")


class ArucoDetector:
    def __init__(self, calibration_path=None, marker_size=0.025):
        if calibration_path is None:
            # Percorso relativo al file corrente
            calibration_path = (
                Path(__file__).parent.parent / "config" / "camera_calibration.npz"
            )
        self.aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
        self.aruco_parameters = aruco.DetectorParameters()
        self.detector = aruco.ArucoDetector(self.aruco_dict, self.aruco_parameters)
        data = np.load(calibration_path)
        self.camera_matrix = data["camera_matrix"]
        self.dist_coeffs = data["dist_coeffs"]
        self.marker_size = marker_size

        # Buffer per smoothing del pitch (debug)
        self.pitch_history = []
        self.PITCH_BUFFER_SIZE = 10

    def detect(self, frame, show=True):
        """restituisce array di markers rilevati fonendo:
        id, rvc, tvec, distance, roll, pitch, yaw, center"""
        h = frame.shape[0]
        pframe = self.__preprocess(frame)
        corners, ids, _ = self.detector.detectMarkers(pframe)
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
                marker_data = self.__process_marker_data(
                    i,
                    marker_id[0],
                    corners_display[i],
                    rvecs[i],
                    tvecs[i],
                    h,
                )
                results.append(marker_data)

                if show:
                    self.__draw_debug(frame, marker_data, corners_display[i])
        if show:
            cv2.imshow("frame", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            cv2.waitKey(1)  # Necessario per aggiornare la finestra OpenCV
        if results != []:
            logger.info(f"Rilevati {len(results)} marker(s)")
        return results

    def __preprocess(self, frame):
        """Converte in grigio e applica blur"""
        frame_flipped = cv2.flip(frame, 0)
        gray = cv2.cvtColor(frame_flipped, cv2.COLOR_RGB2GRAY)
        gaus = cv2.GaussianBlur(gray, (3, 3), 0)

        cv2.imshow("g", gray)
        cv2.imshow("gaus", gaus)
        return gray

    def __process_marker_data(self, index, m_id, corners, rvec, tvec, frame_height):
        """Calcola distanze, angoli e organizza il dizionario."""
        center = np.mean(corners[0], axis=0)
        roll, pitch, yaw = self.__rotation_vector_to_euler_angles(rvec)
        distance = np.linalg.norm(tvec)
        return {
            "id": int(m_id),
            "rvec": rvec,
            "tvec": tvec,
            "distance": float(distance) * 100,
            "angles": (roll, pitch, yaw),
            "center": (int(center[0]), frame_height - int(center[1])),
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
            f"ID:{m_id}  Dist:{dist:.1f}cm",
            f"Roll:{r:.1f}  Pitch:{p:.1f}  Yaw:{y:.1f}",
            f"Pitch avg({self.PITCH_BUFFER_SIZE}):{pitch_avg:.1f}  std:{pitch_std:.1f}",
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
        yaw = (np.degrees(z) + 180) % 360 - 180
        return roll, pitch, yaw
