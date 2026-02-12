import time

from ...utils.debug import get_logger
from ..base_state import BaseState

# Initialize module logger
logger = get_logger("states.scan")


class ScanState(BaseState):
    def enter(self, state_machine):
        logger.info("Entering scan state")
        # state_machine.motors.setDirectionAndSpeed(0, 0, 15) DA RIMETTERE
        return None

    def execute(self, state_machine):
        res = state_machine.camera.detect_aruco()
        if res != []:
            logger.debug(f"ArUco markers detected: {len(res)} markers found")
            from .moving_state import MovingState

            return MovingState(state_machine, res[0])
        logger.verbose("No ArUco markers detected, continuing scan")
        return None

    def exit(self, state_machine):
        logger.info("Exiting scan state")
        state_machine.motors.stop_motors()
        return None
