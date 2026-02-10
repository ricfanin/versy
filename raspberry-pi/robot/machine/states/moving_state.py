import time

from ...utils.debug import get_logger
from ..base_state import BaseState

# Initialize module logger
logger = get_logger("states.moving")


class MovingState(BaseState):
    """Stato di movimento del robot"""

    def __init__(self, state_machine, aruco_data):
        self.marker = aruco_data[0]
        # Target: centro del frame
        frame = state_machine.camera.get_frame()
        self.target_x = frame.shape[1] // 2
        self.target_y = frame.shape[0] // 2
        self.target_yaw = 0  # Vogliamo che il marker sia frontale (yaw = 0)

    def update_data(self, state_machine):
        res = state_machine.camera.detect_aruco()
        if res != []:
            self.marker = res[0]
            return True
        else:
            state_machine.motors.setDirectionAndSpeed(0, 0, 0)
            return False

    def enter(self, state_machine) -> None:
        logger.info("Entering moving state")
        return None

    def execute(self, state_machine):

        if self.update_data(state_machine):
            logger.debug(
                f"Marker: {self.marker}, Target: ({self.target_x}, {self.target_y}, {self.target_yaw})"
            )
            # Extract center coordinates from tuple
            center_x, center_y = self.marker["center"]  # center: x, y
            # Calcola errori (quanto siamo lontani dal target)
            error_x = self.target_x - center_x  # Positivo = marker a sinistra
            error_y = center_y - self.target_y  # Positivo = marker in alto
            error_yaw = (
                self.target_yaw - self.marker["angles"][2]  # angles: roll, pith, yaw
            )  # Positivo = dobbiamo ruotare a sinistra

            # Calcola velocità con PID
            vx = error_x
            vy = -error_y * 1.2
            vyaw = 0
            if error_yaw > 1:
                vyaw = 7
            elif error_yaw < -1:
                vyaw = -7

            logger.verbose(
                f"Control errors - X: {error_x:.1f}, Y: {error_y:.1f}, Yaw: {error_yaw:.1f}"
            )
            logger.verbose(
                f"Motor speeds - vx: {vx:.1f}, vy: {vy:.1f}, vyaw: {vyaw:.1f}"
            )

            state_machine.motors.setDirectionAndSpeed(vx, vy, vyaw)
            return None
        else:
            from .scan_state import ScanState

            return ScanState()

    def exit(self, state_machine) -> None:
        logger.info("Exiting moving state")
        state_machine.motors.setDirectionAndSpeed(0, 0, 0)
        return None
