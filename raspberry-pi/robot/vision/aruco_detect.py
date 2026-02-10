from pathlib import Path

import cv2
import cv2.aruco as aruco
import numpy as np

from ..utils.debug import get_logger

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

    def detect(self, frame, show=True):
        """restituisce array di markers rilevati fonendo:
        id, rvc, tvec, distance, roll, pitch, yaw, center"""
        pframe = self.__preprocess(frame)
        corners, ids, _ = self.detector.detectMarkers(pframe)
        results = []
        if ids is not None:
            rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(
                corners, self.marker_size, self.camera_matrix, self.dist_coeffs
            )
            for i, marker_id in enumerate(ids):
                marker_data = self.__process_marker_data(
                    i,
                    marker_id[0],
                    corners[i],
                    rvecs[i][0],
                    tvecs[i][0],
                    frame.shape[0],
                )
                results.append(marker_data)

                if show:
                    self.__draw_debug(frame, marker_data, corners[i])
        if show:
            cv2.imshow("frame", frame)
            cv2.waitKey(1)  # Necessario per aggiornare la finestra OpenCV
        if results != []:
            logger.info(f"Rilevati {len(results)} marker(s)")
        return results

    def __preprocess(self, frame):
        """Converte in grigio e applica blur"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gaus = cv2.GaussianBlur(gray, (3, 3), 0)
        return gaus

    def __process_marker_data(self, index, m_id, corners, rvec, tvec, frame_height):
        """Calcola distanze, angoli e organizza il dizionario."""
        center = np.mean(corners[0], axis=0)
        roll, pitch, yaw = self.__rotation_vector_to_euler_angles(rvec)
        distance = np.linalg.norm(tvec)
        return {
            "id": int(m_id),
            "rvec": rvec,
            "tvec": tvec,
            "distance": float(distance),
            "angles": (roll, pitch, yaw),
            "center": (int(center[0]), frame_height - int(center[1])),
        }

    def __draw_debug(self, frame, data, corners):
        """Gestisce tutta la parte grafica sul frame."""
        m_id = data["id"]
        dist = data["distance"]
        r, p, y = data["angles"]

        # Assi
        cv2.drawFrameAxes(
            frame,
            self.camera_matrix,
            self.dist_coeffs,
            data["rvec"],
            data["tvec"],
            self.marker_size * 0.5,
        )

        # Info Testuali
        top_left = tuple(corners[0][0].astype(int))
        bottom_left = tuple(corners[0][3].astype(int) + 20)

        cv2.putText(
            frame,
            f"ID:{m_id} Dist:{dist * 100:.1f}cm",
            top_left,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )
        cv2.putText(
            frame,
            f"R:{r:.1f} P:{p:.1f} Y:{y:.1f}",
            bottom_left,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )
        width = frame.shape[1]
        height = frame.shape[0]
        target_x = width // 2
        target_y = height // 2
        cv2.circle(frame, (target_x, target_y), radius=2, color=(255,0,0), thickness=-1)

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
        yaw = (np.degrees(z) + 180) % 360 - 180
        return roll, pitch, yaw
