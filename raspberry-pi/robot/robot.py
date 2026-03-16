from robot.camera import Camera
from robot.motors import Motors
from vision.aruco_detect import ArucoDetector
from utils.debug import get_logger

logger = get_logger("robot")


class Robot:
    FRAME_WIDTH = 320
    FRAME_HEIGHT = 240

    def __init__(self):
        self.camera = Camera(resolution=(self.FRAME_WIDTH, self.FRAME_HEIGHT))
        self.motors = Motors()
        self.aruco_detector = ArucoDetector()

    def stop(self):
        logger.info("Stopping robot hardware")
        self.motors.stop_motors()
        self.camera.stop()
        logger.info("Robot hardware stopped")
