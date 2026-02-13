from ...utils.debug import get_logger
from ..base_state import BaseState

logger = get_logger("states.init")


class InitState(BaseState):
    """Stato di inizializzazione del robot"""

    def __init__(self, state_machine):
        self.sm = state_machine

    def enter(self):
        logger.info("Entering initialization state")
        return None

    def execute(self):
        logger.info("Executing initialization: testing components")
        if not self.sm.camera.test_camera():
            logger.error("Camera test failed, retrying")
            return None
        if not self.sm.motors.test_motors():
            logger.error("Motors test failed, retrying")
            return None
        logger.info("Initialization complete - camera and motors OK")
        from .scan_state import ScanState

        return ScanState(self.sm)

    def exit(self):
        logger.info("Exiting initialization state")
        self.sm.camera.start()
        return None
