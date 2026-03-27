from machine.state_machine import StateMachine
from utils.debug import get_logger
from machine.base_state import BaseState
import math
import time

logger = get_logger("states.moving")


class MovingState(BaseState):
    """Stato di movimento del robot"""

    def __init__(self, state_machine: "StateMachine", marker: dict):
        self.updated = False
        self.sm = state_machine
        self.initial_marker = marker

        self.target_x = self.sm.robot.FRAME_WIDTH // 2
        self.target_y = (self.sm.robot.FRAME_HEIGHT // 2) - 60

        self.marker = marker
        self.distance = self.marker["distance"]
        self.roll = self.marker["angles"][0]
        self.pitch = self.marker["angles"][1]
        self.yaw = self.marker["angles"][2]
        self.center_x = self.marker["center"][0]
        self.center_y = self.marker["center"][1]
        self.retries = 0
        self.is_centered = False

    def enter(self) -> None:
        logger.info("Entering moving state")
        self.updated = True
        return None

    def update_data(self):
        frame = self.sm.robot.camera.get_frame()
        res = self.sm.robot.aruco_detector.detect(frame) if frame is not None else []
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
            self.retries += 1
    
    def set_is_centered_flag(self):
        error_x = self.target_x - self.center_x
        if abs(error_x) >= 50: # pixel di deadzone per considerare l'aruco centrato
            logger.warning(f"Marker not centered: error_x={error_x}")
            self.is_centered = False

    def is_aruco_centered(self, deadzone: int):
        error_x = self.target_x - self.center_x
        logger.debug(f"error_x: {error_x}")
        # con error_X positivo, il marker è a sinistra del centro, con error_X negativo, il marker è a destra del centro
        if abs(error_x) > deadzone:
            if error_x > 0:
                # rotazione anti oraria
                self.sm.robot.motors.setDirectionAndSpeed(0, 0, -1)
            else:
                # rotazione oraria
                self.sm.robot.motors.setDirectionAndSpeed(0, 0, 1)
            self.updated = False
            return False
        self.is_centered = True
        return True

    def is_close_to_aruco(self, target_dist: int):
        if self.distance > target_dist:
            self.sm.robot.motors.setDirectionAndSpeed(0, 10, 0)
            self.updated = False
            return False
        return True

    def is_parallel_to_aruco(self, target_pitch: int):

        # pitch maggiore = aruco rivolto a sinistra
        # pitch minore = aruco rivolto a destra

        if abs(self.pitch) > target_pitch:
            if self.pitch > 0:
                self.sm.robot.motors.setDirectionAndSpeed(-7, 0, 0)
            else:
                self.sm.robot.motors.setDirectionAndSpeed(7, 0, 0)
            self.updated = False
            return False
        return True

    def execute(self):
        logger.debug(f"Marker: {self.marker}")
        # marker:  {'id': 0, 'rvec': array([ x, y, z]), 'tvec': array([x ,  y,  z]), 'distance': 14.322984264396954, 'angles': (np.float64(x), np.float64(y), np.float64(z)), 'center': (x, y)}
        if not self.updated:
            self.update_data()

            print("retries", self.retries)
            if self.retries > 3:
                self.sm.robot.motors.stop_motors()
            if self.retries > 100:  # numero di frame senza un aruco
                from .scan_state import ScanState

                logger.error("ARUCO LOST")
                return ScanState(self.sm)
            return None
        
        # self.set_is_centered_flag()

        # # per cambiare priorità delle azioni basta spostarle (es: voglio che prima sia parallelo e poi si avvicina, inverto is_close con is_parallel)
        # if not self.is_centered:
        #     if not self.is_aruco_centered(15): #pixel di deadzone per considerare l'aruco centrato
        #         return None

        # if not self.is_close_to_aruco(30): # distanza in cm per considerare l'aruco abbastanza vicino
        #     return None

        # if not self.is_parallel_to_aruco(19): # angolo di pitch in gradi per considerare l'aruco abbastanza parallelo
        #     return None

        # if not self.is_close_to_aruco(19):
        #     return None
        error_x = -(self.center_x - self.target_x) # il meno è dovuto al vflip
        error_y = self.center_y - self.target_y
        vx = math.copysign(math.sqrt(abs(error_x)), error_x) * 4
        vy = math.copysign(math.sqrt(abs(error_y)), error_y) * 2
        
        print("vx",vx,"vy",vy,"pitch", self.pitch, "error x ", error_x, "error y ", error_y, )

        # if abs(self.pitch) < 5 or error_x > 50 or error_y > 50 or True:
        #     self.sm.robot.motors.setDirectionAndSpeed(vx, vy, 0)
        # elif self.pitch > 0:
        #     self.sm.robot.motors.setDirectionAndSpeed(vx + 7, vy, 10)
        # else:
        #     self.sm.robot.motors.setDirectionAndSpeed(vx -7 , vy , -10)

        self.updated = False
        return None
        logger.error("ARRIVATO AL BICCHIERE")
        self.sm.robot.motors.stop_motors()
        self.sm.robot.motors.set_pompa_power(255)
        time.sleep(0.5)
        self.sm.robot.motors.set_pompa_power(0)
        # self.sm.robot.motors.setDirectionAndSpeed(0, 50, 0)
        # time.sleep(0.8)
        self.sm.robot.motors.stop_motors()
        logger.error("STO VERSANDO LO SDROGO ....")
        time.sleep(3)

        from .retreat_state import RetreatState

        return RetreatState(self.sm, self.initial_marker)

    def exit(self) -> None:
        logger.info("Exiting moving state")
        self.sm.robot.motors.stop_motors()
        return None
