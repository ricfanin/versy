import time

from ...utils.debug import get_logger
from ..base_state import BaseState

# Initialize module logger
logger = get_logger("states.scan")


class ScanState(BaseState):
    def enter(self, state_machine):
        logger.info("Entering scan state")
        return None

    def execute(self, state_machine):
        res = state_machine.camera.detect_aruco()
        if res != []:
            logger.debug(f"ArUco markers detected: {len(res)} markers found")
            from .moving_state import MovingState

            return MovingState(state_machine, res)
        logger.verbose("No ArUco markers detected, continuing scan")
        return None

    def exit(self, state_machine):
        logger.info("Exiting scan state")
        # state_machine.camera.stop() non va bene, non devo distruggere la camera perchè la uso dopo e ci mette troppo tempo a fermare il thread, distruggere la finestra e poi ricrearla, quindi lascio la camera accesa e basta
        # potrei portare tutto in init state e rompere la cam solo quando si spegne il versy
        return None
