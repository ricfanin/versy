import time

from ...state_machine import StateMachine
from ...utils.debug import get_logger
from ..base_state import BaseState

# Initialize module logger
logger = get_logger("states.moving")


class MovingState(BaseState):
    """Stato di movimento del robot"""

    def __init__(self, state_machine: "StateMachine", marker):
        self.updated = False
        self.sm = state_machine
        self.frame_x = self.sm.camera.get_frame().shape[1] // 2
        self.frame_y = self.sm.camera.get_frame().shape[0] // 2
        self.marker = marker
        self.distance = marker["distance"]
        self.roll = marker["angles"][0]
        self.pitch = marker["angles"][1]
        self.yaw = marker["angles"][2]
        self.center_x = marker["center"][0]
        self.center_y = marker["center"][1]

    def enter(self, state_machine) -> None:
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

    def center_aruco(self):
        error_x = self.frame_x - self.center_x
        print(f"error_x: {error_x}")
        # con error_X positivo, il marker è a sinistra del centro, con error_X negativo, il marker è a destra del centro
        if abs(error_x) > 30:
            if error_x > 0:
                # rotazione anti oraria
                self.sm.motors.setDirectionAndSpeed(0, 0, -50)
            else:
                # rotazione oraria e ritorno
                self.sm.motors.setDirectionAndSpeed(0, 0, 50)
            self.updated = False
            return False
        return True

    # , Target: ({self.target_x}, {self.target_y}, {self.target_pitch})
    def execute(self, state_machine):
        logger.debug(f"Marker: {self.marker}")
        # marker:  {'id': 0, 'rvec': array([ 2.24433176, -0.50068466,  0.78896104]), 'tvec': array([-0.0399964 ,  0.00610322,  0.1373966 ]), 'distance': 0.14322984264396954, 'angles': (np.float64(-40.22905641327844), np.float64(-41.3786465449605), np.float64(-9.402855141314035)), 'center': (161, 112)}
        if not self.updated:
            self.update_data()
            return None

        if not self.center_aruco():
            return None

        print("DAJEEEEE è AL CENTRO")
        state_machine.stop()
        self.updated = False
        return None

    def exit(self, state_machine) -> None:
        logger.info("Exiting moving state")
        state_machine.motors.stop_motors()
        return None
