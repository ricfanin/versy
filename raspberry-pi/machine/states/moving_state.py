from machine.state_machine import StateMachine
from utils.debug import get_logger
from machine.base_state import BaseState

logger = get_logger("states.moving")


class MovingState(BaseState):
    """Stato di movimento del robot"""

    EXPECTED_PERIMETER = 170
    PERIMETER_TOLERANCE = 0.7

    MAX_RETRIES = 100
    MAX_LOW_CONFIDENCE = 5
    TARGET_Y_OFFSET = 60
    YAW_OFFSET = 10
    ON_TARGET_COUNT_REQUIRED = 5

    def __init__(self, state_machine: "StateMachine", marker: dict):
        self.sm = state_machine
        self.initial_marker = marker

        self.target_x = self.sm.robot.FRAME_WIDTH // 2
        self.target_y = (self.sm.robot.FRAME_HEIGHT // 2) - self.TARGET_Y_OFFSET

        self._unpack_marker(marker)

        self.updated = False
        self.retries = 0
        self.low_confidence_count = 0
        self.on_target_count = 0

    def _unpack_marker(self, marker: dict) -> None:
        self.marker = marker
        self.center_x = marker["center"][0]
        self.center_y = marker["center"][1]
        self.distance = marker["distance"]
        self.roll = marker["angles"][0]
        self.pitch = marker["angles"][1]
        self.yaw = marker["angles"][2]

    def _filter_by_perimeter(self, markers: list) -> list:
        filtered = []
        for m in markers:
            p = m.get("perimeter")
            if p is not None and abs(p - self.EXPECTED_PERIMETER) / self.EXPECTED_PERIMETER <= self.PERIMETER_TOLERANCE:
                filtered.append(m)
            else:
                logger.info(f"Aruco id={m['id']} scartato per perimetro: {p}")
        return filtered

    def _compute_velocities(self, error_x: float, error_y: float) -> tuple:
        # laterale: bang-bang con deadband
        if abs(error_x) < 25:
            vx = 0
        elif error_x > 0:
            vx = 35
        else:
            vx = -35

        # avanti/indietro: proporzionale, clampato
        vy = max(-50, min(error_y * 0.5, 40))

        # yaw: correggi solo quando circa centrato
        vr = 0
        if abs(error_x) < 30 and abs(error_y) < 50:
            yaw_error = self.yaw + self.YAW_OFFSET
            if yaw_error > 5:
                vr = 15
            elif yaw_error < -5:
                vr = -15

        return vx, vy, vr

    def _check_on_target(self, error_x: float, error_y: float):
        yaw_error = self.yaw + self.YAW_OFFSET
        if abs(error_x) < 30 and abs(error_y) < 40 and abs(yaw_error) < 5:
            self.on_target_count += 1
            logger.info(f"On target {self.on_target_count}/{self.ON_TARGET_COUNT_REQUIRED}")
            if self.on_target_count >= self.ON_TARGET_COUNT_REQUIRED:
                from .pouring_state import PouringState

                logger.info("Aruco centrato, passo a PouringState")
                return PouringState(self.sm, self.initial_marker)
        else:
            self.on_target_count = 0
        return None

    def enter(self) -> None:
        logger.info("Entering moving state")
        self.updated = True
        return None

    def update_data(self):
        frame = self.sm.robot.camera.get_frame()
        detections = self.sm.robot.aruco_detector.detect(frame)

        if detections:
            detections = self._filter_by_perimeter(detections)

        if not detections:
            self.sm.robot.motors.stop_motors()
            self.retries += 1
            return

        marker = detections[0]
        self.center_x = marker["center"][0]
        self.center_y = marker["center"][1]

        if marker["confidence"] == "full":
            self._unpack_marker(marker)
            self.low_confidence_count = 0
        else:
            self.low_confidence_count += 1
            if self.low_confidence_count > self.MAX_LOW_CONFIDENCE:
                self.retries += 1
                return

        self.updated = True
        self.retries = 0

    def execute(self):
        logger.debug(f"Marker: {self.marker}")

        if not self.updated:
            self.update_data()
            if self.retries > self.MAX_RETRIES:
                from .scan_state import ScanState

                logger.error("ARUCO LOST")
                return ScanState(self.sm)
            return None

        error_x = -(self.center_x - self.target_x)
        error_y = self.center_y - self.target_y

        vx, vy, vr = self._compute_velocities(error_x, error_y)
        logger.debug(f"error_x={error_x} error_y={error_y} yaw_error={self.yaw + self.YAW_OFFSET}")
        self.sm.robot.motors.setDirectionAndSpeed(vx, vy, vr)

        transition = self._check_on_target(error_x, error_y)
        if transition:
            return transition

        self.updated = False
        return None

    def exit(self) -> None:
        logger.info("Exiting moving state")
        self.sm.robot.motors.stop_motors()
        return None
