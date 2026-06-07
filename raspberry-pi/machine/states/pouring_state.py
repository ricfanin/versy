from machine.state_machine import StateMachine
from utils.debug import get_logger
from machine.base_state import BaseState
import time

logger = get_logger("states.pouring")

POUR_DISTANCE_MM = 90
FORWARD_SPEED = 26


class PouringState(BaseState):
    """Avanza dritto piano e versa quando il ToF frontale rileva il bicchiere"""

    def __init__(self, state_machine: "StateMachine", initial_marker: dict):
        self.sm = state_machine
        self.initial_marker = initial_marker

    def enter(self) -> None:
        logger.info("Entering pouring state")
        return None

    def execute(self):
        tof = self.sm.robot.get_tof_front()
        print(tof)

        if tof is not None and tof < POUR_DISTANCE_MM:
            logger.info(f"Bicchiere rilevato a {tof}mm, verso!")
            self.sm.robot.motors.stop_motors()

            # self.sm.robot.motors.set_pompa_power(255)
            # time.sleep(3)
            # self.sm.robot.motors.set_pompa_power(0)

            from .retreat_state import RetreatState
            from websocket.utils.messages import PourCompleteMessage

            self.sm.publish(PourCompleteMessage(ml_poured=30))
            return RetreatState(self.sm, self.initial_marker)

        self.sm.robot.motors.setDirectionAndSpeed(0, FORWARD_SPEED, 0)
        return None

    def exit(self) -> None:
        logger.info("Exiting pouring state")
        self.sm.robot.motors.stop_motors()
        return None
