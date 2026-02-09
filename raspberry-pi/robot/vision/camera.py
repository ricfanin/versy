from threading import Thread
from typing import Optional, Tuple

import cv2

from .aruco_detect import ArucoDetector


class Camera:
    def __init__(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)
        self.aruco_detector = ArucoDetector()
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.__stopped = False
        self.__frame = None
        self.__thread: Optional[Thread] = None

    def start(self):
        self.__thread = Thread(target=self.update, daemon=True)
        print("Starting camera thread...")
        self.__thread.start()
        return self

    def update(self):
        while not self.__stopped:
            ret, frame = self.cap.read()
            self.__frame = frame

    def get_frame(self):
        return self.__frame

    def detect_aruco(self):
        print("Detecting ArUco markers...")
        frame = self.get_frame()
        res = []
        if frame is not None:
            res = self.aruco_detector.detect(frame)
        return res

    def stop(self):
        self.__stopped = True
        if self.__thread and self.__thread.is_alive():
            self.__thread.join(timeout=1.0)
        self.cap.release()
        cv2.destroyAllWindows()
