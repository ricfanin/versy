from robot.camera import Camera
from robot.motors import Motors
from robot.tofs import Tofs
from vision.aruco_detect import ArucoDetector
from vision.table_segmentation import TableSegmentor
from utils.debug import get_logger

logger = get_logger("robot")


class Robot:
    FRAME_WIDTH = 320
    FRAME_HEIGHT = 240

    def __init__(self):
        self.camera = Camera(resolution=(self.FRAME_WIDTH, self.FRAME_HEIGHT))
        self.motors = Motors()
        self.tofs = Tofs()
        self.aruco_detector = ArucoDetector()
        self.table_segmentor = TableSegmentor()

    def get_tof_measures(self):
        try:
            return self.tofs.detect_range()
        except Exception as e:
            logger.error(f"Errore lettura ToF: {e}")
            return [None, None, None]

    def get_tof_sx(self):
        return self.tofs.get_sx()

    def get_tof_dx(self):
        return self.tofs.get_dx()

    def get_tof_front(self):
        return self.tofs.get_front()

    def stop(self):
        logger.info("Stopping robot hardware")
        self.motors.stop_motors()
        self.tofs.stop()
        self.camera.stop()
        logger.info("Robot hardware stopped")
