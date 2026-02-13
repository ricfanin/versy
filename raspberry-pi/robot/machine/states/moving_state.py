from ...state_machine import StateMachine
from ...utils.debug import get_logger
from ..base_state import BaseState

logger = get_logger("states.moving")


class MovingState(BaseState):
    """Stato di movimento del robot"""

    def __init__(self, state_machine: "StateMachine", marker):
        self.updated = False
        self.sm = state_machine

        frame = self.sm.camera.get_frame()
        if frame is not None:
            self.frame_x = frame.shape[1] // 2
            self.frame_y = frame.shape[0] // 2
        else:
            # dovrebbe essere la stessa cosa
            self.frame_x = self.sm.camera.FRAME_WIDTH // 2
            self.frame_y = self.sm.camera.FRAME_HEIGHT // 2

        self.marker = marker
        self.distance = self.marker["distance"]
        self.roll = self.marker["angles"][0]
        self.pitch = self.marker["angles"][1]
        self.yaw = self.marker["angles"][2]
        self.center_x = self.marker["center"][0]
        self.center_y = self.marker["center"][1]
        self.retries = 0

    def enter(self) -> None:
        logger.info("Entering moving state")
        self.updated = True
        return None

    def update_data(self):
        res = self.sm.camera.detect_aruco()
        if res != []:
            self.marker = res[0]
            self.distance = self.marker["distance"]
            self.roll = self.marker["angles"][0]
            self.pitch = self.marker["angles"][1]
            self.yaw = self.marker["angles"][2]
            self.center_x = self.marker["center"][0]
            self.center_y = self.marker["center"][1]
            self.updated = True
            self.retries = 0
        else:
            self.sm.motors.stop_motors()
            self.retries += 1

    def is_aruco_centered(self):
        error_x = self.frame_x - self.center_x
        logger.debug(f"error_x: {error_x}")
        # con error_X positivo, il marker è a sinistra del centro, con error_X negativo, il marker è a destra del centro
        if abs(error_x) > 20:
            if error_x > 0:
                # rotazione anti oraria
                self.sm.motors.setDirectionAndSpeed(0, 0, -1)
            else:
                # rotazione oraria e ritorno
                self.sm.motors.setDirectionAndSpeed(0, 0, 1)
            self.updated = False
            return False
        return True

    def is_close_to_aruco(self):
        if self.distance > 10:
            self.sm.motors.setDirectionAndSpeed(0, 40, 0)
            self.updated = False
            return False
        return True

    def is_parallel_to_aruco(self):

        # pitch maggiore = aruco rivolto a sinistra
        # pitch minore = aruco rivolto a destra

        if abs(self.pitch) > 10:
            if self.pitch > 0:
                self.sm.motors.setDirectionAndSpeed(-15, 0, 0)
            else:
                self.sm.motors.setDirectionAndSpeed(15, 0, 0)
            self.updated = False
            return False
        return True

    def execute(self):
        logger.debug(f"Marker: {self.marker}")
        # marker:  {'id': 0, 'rvec': array([ x, y, z]), 'tvec': array([x ,  y,  z]), 'distance': 14.322984264396954, 'angles': (np.float64(x), np.float64(y), np.float64(z)), 'center': (x, y)}
        if not self.updated:
            self.update_data()
            if self.retries > 100:  # numero di frame senza un aruco
                from .scan_state import ScanState

                logger.error("ARUCO LOST")
                return ScanState(self.sm)
            return None

        # per cambiare priorità delle azioni basta spostarle (es: voglio che prima sia parallelo e poi si avvicina, inverto is_close con is_parallel)
        if not self.is_aruco_centered():
            return None

        if not self.is_close_to_aruco():
            return None

        if not self.is_parallel_to_aruco():
            return None

        self.sm.motors.stop_motors()
        logger.error("DAJEEEEE è AL CENTRO e VICINO")

        from .exit_state import ExitState

        return ExitState(self.sm)

    def exit(self) -> None:
        logger.info("Exiting moving state")
        self.sm.motors.stop_motors()
        return None
