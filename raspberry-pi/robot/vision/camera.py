from threading import Thread
from typing import Optional

import cv2

from ..utils.debug import get_logger
from .aruco_detect import ArucoDetector

# Initialize module logger
logger = get_logger("vision.camera")


class Camera:
    FRAME_WIDTH = 320
    FRAME_HEIGHT = 240
    FPS = 30

    def __init__(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)
        self.aruco_detector = ArucoDetector()
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, self.FPS)
        self.__stopped = False
        self.__frame = None
        self.__thread: Optional[Thread] = None

    def start(self):
        self.__thread = Thread(target=self.update, daemon=True)
        logger.info("Starting camera thread")
        self.__thread.start()
        return self

    def update(self):
        while not self.__stopped:
            ret, frame = self.cap.read()
            self.__frame = frame

    def get_frame(self):
        return self.__frame

    def detect_aruco(self):
        frame = self.get_frame()
        res = []
        if frame is not None:
            res = self.aruco_detector.detect(frame)
        return res

    def test_camera(self) -> bool:
        """Test method for InitState to verify camera functionality"""
        try:
            # Try to capture a frame
            ret, frame = self.cap.read()
            if ret and frame is not None:
                logger.info("Camera test passed")
                return True
            else:
                logger.error("Camera test failed - no frame captured")
                return False

        except Exception as e:
            logger.error(f"Camera test failed: {e}")
            return False

    def stop(self):
        logger.info("Stopping camera")
        self.__stopped = True
        if self.__thread and self.__thread.is_alive():
            self.__thread.join(timeout=1.0)
        self.cap.release()
        cv2.destroyAllWindows()
        logger.info("Camera stopped successfully")
