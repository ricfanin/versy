from ...utils.debug import get_logger
from ..base_state import BaseState

# Initialize module logger
logger = get_logger("states.retreat")


class RetreatState(BaseState):
    """Stato di ritorno alla posizione iniziale"""

    # marker:  {'id': 0, 'rvec': array([ x, y, z]), 'tvec': array([x ,  y,  z]), 'distance': 14.322984264396954, 'angles': (np.float64(x), np.float64(y), np.float64(z)), 'center': (x, y)}

    def __init__(self, state_machine, initial_marker: dict):
        self.sm = state_machine
        self.target_pos = initial_marker

    def enter(self):
        logger.info("Entering retreat state")
        return None

    def execute(self):
        logger.info("RETREAT COMPLETED: robot is back to initial position and orientation")
        # Passa allo stato ExitState
        from .exit_state import ExitState
        return ExitState(self.sm)

    def exit(self):
        logger.info("Exiting retreat state")
        return None
