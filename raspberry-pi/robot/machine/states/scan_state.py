import time

from ..base_state import BaseState


class ScanState(BaseState):
    def enter(self, context):
        print("Entering Scan State")
        context.camera.start()
        return None

    def execute(self, context):
        print("Executing Scan State")
        if len(context.camera.detect_aruco()) != 0:
            context.motors.setDirectionAndSpeed(0, 80, 0)
        else:
            context.motors.setDirectionAndSpeed(0, 0, 0)
        return None

    def exit(self, context):
        print("Exiting Scan State")
        context.camera.stop()
        return None
