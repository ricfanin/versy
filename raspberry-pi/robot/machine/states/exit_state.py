from ...utils.debug import get_logger
from ..base_state import BaseState

# Initialize module logger
logger = get_logger("states.init")


class ExitState(BaseState):
    """Stato di uscita dalla state machine"""

    def __init__(self, state_machine):
        self.sm = state_machine

    def enter(self):
        logger.info("Entering exit state")
        return None

    def execute(self):
        logger.info("Executing exit: stopping everything")
        self.sm.stop()
        logger.info("Exit complete")

        return None

    def exit(self):
        logger.info("Exiting exit state")
        return None
