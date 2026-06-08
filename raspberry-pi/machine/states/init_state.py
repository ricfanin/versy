from utils.debug import get_logger
from machine.base_state import BaseState

logger = get_logger("states.init")


class InitState(BaseState):
    """Idle: dequeue del prossimo job e transizione a ScanState"""

    def __init__(self, state_machine):
        self.sm = state_machine

    def enter(self):
        logger.info("Entering initialization state")
        self.sm.robot.camera.start()
        self.sm.current_job = None
        return None

    def execute(self):
        job = self.sm.dequeue()
        if job is None:
            return None

        self.sm.current_job = job
        from .scan_state import ScanState

        logger.info(f"Job dequeued: marker_id={job.marker_id} username={job.username}")
        return ScanState(self.sm)

    def exit(self):
        logger.info("Exiting initialization state")
        return None
