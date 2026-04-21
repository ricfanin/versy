from utils.debug import get_logger
from machine.base_state import BaseState

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
        if not self.sm.robot.camera.test_camera():
            logger.error("Camera test failed, retrying")
            return None
        if not self.sm.robot.motors.test_motors():
            logger.error("Motors test failed, retrying")
            return None
        if not self.sm.robot.tofs.test_tofs():
            logger.error("ToF test failed, retrying")
            return None
        logger.info("Initialization complete - camera, motors and ToF OK")
        return None

    def exit(self):
        logger.info("Exiting initialization state")
        self.sm.robot.camera.start()
        return None
