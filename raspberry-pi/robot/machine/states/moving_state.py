import time

from ..base_state import BaseState


class MovingState(BaseState):
    """Stato di movimento del robot"""

    def __init__(self, state_machine, aruco_data):
        self.marker = aruco_data[0]
        # Target: centro del frame
        self.target_x = state_machine.camera.FRAME_WIDTH // 2
        self.target_y = state_machine.camera.FRAME_HEIGHT // 2 + 65
        self.target_yaw = 0  # Vogliamo che il marker sia frontale (yaw = 0)

    def update_data(self, state_machine):
        res = state_machine.camera.detect_aruco()
        if res != []:
            self.marker = res[0]
            return True
        else:
            state_machine.motors.setDirectionAndSpeed(0, 0, 0)
            return False

    def enter(self, state_machine) -> None:
        print("Entering MovingState")
        return None

    def execute(self, state_machine):

        if self.update_data(state_machine):
            print(
                "marker: ",
                self.marker,
                " target: ",
                self.target_x,
                self.target_y,
                self.target_yaw,
            )
            # Extract center coordinates from tuple
            center_x, center_y = self.marker["center"]  # center: x, y
            # Calcola errori (quanto siamo lontani dal target)
            error_x = self.target_x - center_x  # Positivo = marker a sinistra
            error_y = center_y - self.target_y  # Positivo = marker in alto
            error_yaw = (
                self.target_yaw - self.marker["angles"][2]  # angles: roll, pith, yaw
            )  # Positivo = dobbiamo ruotare a sinistra

            # Calcola velocità con PID
            vx = error_x
            vy = -error_y * 1.2
            vyaw = 0
            if error_yaw > 1:
                vyaw = 7
            elif error_yaw < -1:
                vyaw = -7

            print(f"Errors: X={error_x:.1f} Y={error_y:.1f} Yaw={error_yaw:.1f}")
            print(f"Speeds: vx={vx:.1f} vy={vy:.1f} vyaw={vyaw:.1f}")

            state_machine.motors.setDirectionAndSpeed(vx, vy, vyaw)

            if abs(error_x) < 20 and abs(error_y) < 20 and abs(error_yaw) < 5:
                from .scan_state import ScanState

                return ScanState()
        return None

    def exit(self, state_machine) -> None:
        print("Exiting MovingState")
        state_machine.motors.setDirectionAndSpeed(0, 0, 0)
        return None
