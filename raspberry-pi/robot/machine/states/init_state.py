from ..base_state import BaseState
from .scan_state import ScanState


class InitState(BaseState):
    """Stato di inizializzazione del robot"""

    def enter(self, context) -> None:
        print("Entering InitState")
        return None

    def execute(self, context):
        print("Executing InitState")
        return ScanState()

    def exit(self, context) -> None:
        print("Exiting InitState")
        return None
