from ..base_state import BaseState


class ScanState(BaseState):
    def enter(self, context):
        print("Entering Scan State")
        context.camera.start()
        return None

    def execute(self, context):
        print("Executing Scan State")
        if context.camera.detect_aruco() != []:
            from .moving_state import MovingState

            return MovingState()
        return None

    def exit(self, context):
        print("Exiting Scan State")
        context.camera.stop()
        return None
