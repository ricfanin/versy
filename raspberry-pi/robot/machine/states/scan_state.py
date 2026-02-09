import time

from ..base_state import BaseState


class ScanState(BaseState):
    def enter(self, context):
        print("Entering Scan State")
        context.motors.setDirectionAndSpeed(50, 0, 0)
        return None

    def execute(self, context):
        print("Executing Scan State")
        # Import dinamico per evitare import circolare
        from .init_state import InitState

        time.sleep(4)
        return InitState()

    def exit(self, context):
        print("Exiting Scan State")
        context.motors.setDirectionAndSpeed(0, 0, 0)
        time.sleep(2)
        return None
