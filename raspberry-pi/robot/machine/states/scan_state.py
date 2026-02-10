import time

from ..base_state import BaseState


class ScanState(BaseState):

    def enter(self, state_machine):
        print("Entering Scan State")
        return None

    def execute(self, state_machine):
        res = state_machine.camera.detect_aruco()
        if res != []:
            from .moving_state import MovingState

            return MovingState(state_machine, res)
        return None

    def exit(self, state_machine):
        print("Exiting Scan State")
        # state_machine.camera.stop() non va bene, non devo distruggere la camera perchè la uso dopo e ci mette troppo tempo a fermare il thread, distruggere la finestra e poi ricrearla, quindi lascio la camera accesa e basta
        # potrei portare tutto in init state e rompere la cam solo quando si spegne il versy
        return None
