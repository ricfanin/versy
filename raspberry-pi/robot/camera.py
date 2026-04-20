import sys

sys.path.append("/usr/lib/python3/dist-packages")
from threading import Thread
from typing import Optional, Tuple

import cv2
from picamera2 import Picamera2

from utils.debug import get_logger

# Initialize module logger
logger = get_logger("vision.camera")


class Camera:
    FRAME_WIDTH = 320
    FRAME_HEIGHT = 240
    FPS = 30

    def __init__(
        self,
        resolution: Tuple[int, int] = (320, 240),
        brightness: Optional[float] = 0.2,
        hflip: bool = False,
        vflip: bool = True,
    ):
        self.cam = Picamera2()
        self.__stopped = False
        self.__frame = None
        self.__thread: Optional[Thread] = None

        full_fov_mode = None
        for mode in self.cam.sensor_modes:
            # Controlla se il crop_limits inizia da (0,0) - indica full FOV
            if mode["crop_limits"][0] == 0 and mode["crop_limits"][1] == 0:
                full_fov_mode = mode
                break

        config = self.cam.create_video_configuration(
            main={"size": resolution, "format": "RGB888"},
            sensor={
                "output_size": full_fov_mode[
                    "size"
                ],  # Forza il sensor mode con full FOV
                "bit_depth": full_fov_mode["bit_depth"],
            },
        )

        if hflip or vflip:
            from libcamera import Transform

            config["transform"] = Transform(hflip=int(hflip), vflip=int(vflip))

        self.cam.configure(config)

        if brightness is not None:
            self.cam.set_controls({"Brightness": float(brightness)})

        self.cam.start()

    def start(self):
        self.__thread = Thread(target=self.update, daemon=True)
        logger.info("Starting camera thread")
        self.__thread.start()
        return self

    def update(self):
        while not self.__stopped:
            frame = self.cam.capture_array()
            self.__frame = frame

    def get_frame(self):
        return self.__frame

    def test_camera(self) -> bool:
        """Test method for InitState to verify camera functionality"""
        try:
            # Try to capture a frame
            frame = self.cam.capture_array()
            if frame is not None:
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
        self.cam.stop()
        cv2.destroyAllWindows()
        logger.info("Camera stopped successfully")
