import time

from ..base_state import BaseState


class MovingState(BaseState):
    """Stato di movimento del robot"""

    def enter(self, context) -> None:
        print("Entering MovingState")
        context.motors.setDirectionAndSpeed(0, 80, 0)
        return None

    def execute(self, context):
        print("Executing MovingState")
        from .scan_state import ScanState

        time.sleep(2)
        return ScanState()

    def exit(self, context) -> None:
        print("Exiting MovingState")
        context.motors.setDirectionAndSpeed(0, 0, 0)
        return None
