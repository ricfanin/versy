import time

from ...utils.debug import get_logger
from ..base_state import BaseState

# Initialize module logger
logger = get_logger("states.moving")


class MovingState(BaseState):
    """Stato di movimento del robot"""

    def __init__(self, state_machine, aruco_data):
        self.marker = aruco_data[0]
        # Target: centro del frame
        frame = state_machine.camera.get_frame()
        self.target_x = frame.shape[1] // 2
        self.target_y = frame.shape[0] // 2
        self.target_pitch = 0  # Vogliamo che il marker sia frontale
        
        # Parametri di controllo
        self.MIN_SPEED = 20  # Velocità minima efficace
        self.MAX_SPEED = 100  # Velocità massima
        self.WORKING_SPEED_RANGE = self.MAX_SPEED - self.MIN_SPEED  # 80
        
        # Soglie di errore per considerare il target raggiunto
        self.THRESHOLD_X = 30  # pixel
        self.THRESHOLD_Y = 30  # pixel
        self.THRESHOLD_PITCH = 10  # gradi
        self.THRESHOLD_DISTANCE = 0.1  # metri (distanza target)
        
        # Guadagni proporzionali (da calibrare)
        self.KP_X = 0.15  # Guadagno per errore X (laterale)
        self.KP_Y = 0.15  # Guadagno per errore Y (verticale)
        self.KP_PITCH = 1.5  # Guadagno per errore angolare
        self.KP_DISTANCE = 40  # Guadagno per distanza (scala velocità con distanza)

    def update_data(self, state_machine):
        res = state_machine.camera.detect_aruco()
        if res != []:
            self.marker = res[0]
            return True
        else:
            state_machine.motors.setDirectionAndSpeed(0, 0, 0)
            return False

    def enter(self, state_machine) -> None:
        logger.info("Entering moving state")
        return None
    
    def normalize_speed(self, speed):
        """
        Normalizza la velocità nell'intervallo [MIN_SPEED, MAX_SPEED]
        mantenendo il segno. Se |speed| < soglia, torna 0
        """
        if abs(speed) < 5:  # Soglia sotto cui consideriamo velocità nulla
            return 0
        
        # Normalizza nell'intervallo [MIN_SPEED, MAX_SPEED]
        sign = 1 if speed > 0 else -1
        normalized = min(abs(speed), self.MAX_SPEED)
        
        # Scala nell'intervallo working range e aggiungi MIN_SPEED
        if normalized > 0:
            # Map da [0, MAX_SPEED] a [MIN_SPEED, MAX_SPEED]
            scaled = (normalized / self.MAX_SPEED) * self.WORKING_SPEED_RANGE + self.MIN_SPEED
            return sign * scaled
        
        return 0
    
    def is_target_reached(self, error_x, error_y, error_pitch, distance):
        """Verifica se il target è stato raggiunto entro le soglie"""
        x_ok = abs(error_x) < self.THRESHOLD_X
        y_ok = abs(error_y) < self.THRESHOLD_Y
        pitch_ok = abs(error_pitch) < self.THRESHOLD_PITCH
        distance_ok = distance < self.THRESHOLD_DISTANCE
        
        return x_ok and y_ok and pitch_ok and distance_ok

    def execute(self, state_machine):
        if self.update_data(state_machine):
            # Extract center coordinates from tuple
            center_x, center_y = self.marker["center"]
            
            # Calcola errori (quanto siamo lontani dal target)
            error_x = self.target_x - center_x  # Positivo = marker a sinistra
            error_y = center_y - self.target_y  # Positivo = marker in alto
            error_pitch = self.target_pitch - self.marker["angles"][2]  # Positivo = ruotiamo a sinistra
            distance = self.marker["distance"]
            
            logger.debug(
                f"Marker center: ({center_x}, {center_y}), "
                f"Distance: {distance:.2f}m, Pitch: {self.marker['angles'][2]:.1f}°"
            )
            
            # Verifica se abbiamo raggiunto il target
            if self.is_target_reached(error_x, error_y, error_pitch, distance):
                logger.info("Target reached! Stopping motors.")
                state_machine.motors.setDirectionAndSpeed(0, 0, 0)
                # Qui potresti tornare uno stato diverso, es: TargetReachedState()
                return None
            
            # Calcola velocità proporzionali agli errori
            # La velocità aumenta con la distanza e con l'errore
            distance_factor = min(distance / self.THRESHOLD_DISTANCE, 2.5)  # Cap a 2.5x
            
            vx_raw = self.KP_X * error_x * distance_factor
            vy_raw = self.KP_Y * error_y * distance_factor  # Negativo perché Y è invertito
            vpitch_raw = self.KP_PITCH * error_pitch
            
            # Normalizza le velocità nell'intervallo [MIN_SPEED, MAX_SPEED]
            vx = self.normalize_speed(vx_raw)
            vy = self.normalize_speed(vy_raw)
            vpitch = self.normalize_speed(vpitch_raw)
            
            logger.info(
                f"Errors - X: {error_x:>6.1f}px, Y: {error_y:>6.1f}px, "
                f"Pitch: {error_pitch:>6.1f}°, Dist: {distance:.2f}m"
            )
            logger.info(
                f"Speeds - vx: {vx:>6.1f}, vy: {vy:>6.1f}, vpitch: {vpitch:>6.1f}"
            )
            
            state_machine.motors.setDirectionAndSpeed(vx, vy, vpitch)
            return None
        else:
            from .scan_state import ScanState
            # return ScanState()
            return None

    def exit(self, state_machine) -> None:
        logger.info("Exiting moving state")
        state_machine.motors.setDirectionAndSpeed(0, 0, 0)
        return None