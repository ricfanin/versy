from ..base_state import BaseState


class InitState(BaseState):
    """Stato di inizializzazione del robot"""

    def enter(self, context):
        print("Entering InitState")
        return None

    def execute(self, context):
        print("Executing InitState: Testing...")
        if not context.camera.test_camera():
            print("Camera test failed, retrying...")
            return None
        if not context.motors.test_motors():
            print("Motors test failed, retrying...")
            return None
        print("Initialization complete - camera and motors OK")
        from .scan_state import ScanState

        return ScanState()

    def exit(self, context):
        print("Exiting InitState")
        return None
