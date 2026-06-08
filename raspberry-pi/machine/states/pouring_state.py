import time

from machine.state_machine import StateMachine
from utils.debug import get_logger
from machine.base_state import BaseState

logger = get_logger("states.pouring")

POUR_DISTANCE_MM = 90
FORWARD_SPEED = 29
# Portata della pompa misurata: ~1.5–1.8 L/min → ~25–30 ml/s. Da ricalibrare.
PUMP_ML_PER_SECOND = 30
PUMP_POWER = 255


class PouringState(BaseState):
    """Avanza dritto piano e versa quando il ToF frontale rileva il bicchiere"""

    def __init__(self, state_machine: "StateMachine"):
        self.sm = state_machine

    def enter(self) -> None:
        logger.info("Entering pouring state")
        return None

    def execute(self):
        tof = self.sm.robot.get_tof_front()
        print(tof)

        if tof is not None and tof < POUR_DISTANCE_MM:
            ml_target = self.sm.current_job.ml
            pump_seconds = ml_target / PUMP_ML_PER_SECOND
            logger.info(
                f"Bicchiere rilevato a {tof}mm, verso {ml_target}ml (~{pump_seconds:.2f}s)"
            )
            self.sm.robot.motors.stop_motors()

            self.sm.robot.motors.set_pompa_power(PUMP_POWER)
            time.sleep(pump_seconds)
            self.sm.robot.motors.set_pompa_power(0)

            from .retreat_state import RetreatState
            from websocket.utils.messages import PourCompleteMessage

            self.sm.publish(PourCompleteMessage(ml_poured=ml_target))
            return RetreatState(self.sm)

        self.sm.robot.motors.setDirectionAndSpeed(0, FORWARD_SPEED, 0)
        return None

    def exit(self) -> None:
        logger.info("Exiting pouring state")
        self.sm.robot.motors.stop_motors()
        return None
