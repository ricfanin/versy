from ...utils.debug import get_logger
from ..base_state import BaseState

# Initialize module logger
logger = get_logger("states.init")


class InitState(BaseState):
    """Stato di inizializzazione del robot"""

    def enter(self, state_machine):
        logger.info("Entering initialization state")
        return None

    def execute(self, state_machine):
        logger.info("Executing initialization: testing components")
        if not state_machine.camera.test_camera():
            logger.error("Camera test failed, retrying")
            return None
        if not state_machine.motors.test_motors():
            logger.error("Motors test failed, retrying")
            return None
        logger.info("Initialization complete - camera and motors OK")
        from .scan_state import ScanState

        return ScanState()

    def exit(self, state_machine):
        logger.info("Exiting initialization state")
        state_machine.camera.start()
        return None
