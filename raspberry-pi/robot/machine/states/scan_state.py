import time

from ..base_state import BaseState


class ScanState(BaseState):
    def enter(self, context):
        print("Entering Scan State")
        return None

    def execute(self, context):
        print("Executing Scan State")
        # Import dinamico per evitare import circolare
        from .init_state import InitState

        return InitState()

    def exit(self, context):
        print("Exiting Scan State")
        return None
