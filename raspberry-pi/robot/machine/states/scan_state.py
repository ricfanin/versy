from ...utils.debug import get_logger
from ..base_state import BaseState

logger = get_logger("states.scan")


class ScanState(BaseState):
    def __init__(self, state_machine):
        self.sm = state_machine

    def enter(self):
        logger.info("Entering scan state")
        # state_machine.motors.setDirectionAndSpeed(0, 0, 5) DA RIMETTERE
        return None

    def execute(self):
        res = self.sm.camera.detect_aruco()
        if res != []:
            self.sm.motors.stop_motors()
            logger.debug(f"ArUco markers detected: {len(res)} markers found")
            from .moving_state import MovingState

            return MovingState(self.sm, res[0])
        logger.verbose("No ArUco markers detected, continuing scan")
        return None

    def exit(self):
        logger.info("Exiting scan state")
        self.sm.motors.stop_motors()
        return None
