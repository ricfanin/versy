import time

from machine.state_machine import StateMachine
from utils.debug import get_logger
from machine.base_state import BaseState

logger = get_logger("states.retreat")


class RetreatState(BaseState):
    """Indietreggia 1s e poi ruota a sinistra 1s"""

    BACKWARD_VY = -30
    BACKWARD_DURATION = 1.0

    ROTATE_VANG = -25
    ROTATION_DURATION = 1.0

    def __init__(self, state_machine: "StateMachine", initial_marker: dict):
        self.sm = state_machine
        self.phase = "retreating"
        self.phase_start_time = None

    def enter(self):
        logger.info("Entering retreat state")
        self.phase_start_time = time.time()

    def execute(self):
        elapsed = time.time() - self.phase_start_time

        if self.phase == "retreating":
            if elapsed >= self.BACKWARD_DURATION:
                logger.info("Retreat indietro completato, inizio rotazione 1s a sinistra")
                self.sm.robot.motors.stop_motors()
                self.phase = "rotating"
                self.phase_start_time = time.time()
                return None
            self.sm.robot.motors.setDirectionAndSpeed(0, self.BACKWARD_VY, 0)
            return None

        if elapsed >= self.ROTATION_DURATION:
            self.sm.robot.motors.stop_motors()
            from .init_state import InitState

            logger.info("Rotazione completata, torno a InitState")
            return InitState(self.sm)

        self.sm.robot.motors.setDirectionAndSpeed(0, 0, self.ROTATE_VANG)
        return None

    def exit(self):
        logger.info("Exiting retreat state")
        self.sm.robot.motors.stop_motors()
