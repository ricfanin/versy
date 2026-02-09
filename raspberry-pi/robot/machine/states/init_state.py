from ..base_state import BaseState


class InitState(BaseState):
    """Stato di inizializzazione del robot"""

    def enter(self, state_machine):
        print("Entering InitState")
        return None

    def execute(self, state_machine):
        print("Executing InitState: Testing...")
        if not state_machine.camera.test_camera():
            print("Camera test failed, retrying...")
            return None
        if not state_machine.motors.test_motors():
            print("Motors test failed, retrying...")
            return None
        print("Initialization complete - camera and motors OK")
        from .scan_state import ScanState

        return ScanState()

    def exit(self, state_machine):
        print("Exiting InitState")
        return None
