from machine.state_machine import StateMachine
from machine.states.init_state import InitState
from websocket.utils.messages import (
    PourMessage,
    PourStartMessage,
    PourStopMessage,
    MoveMessage,
    StopMessage,
    BaseMessage,
    ErrorMessage,
    PourCompleteMessage,
)
from websocket.interfaces.motor_interface import move as motor_move
from websocket.interfaces.motor_interface import pump_on, pump_off

def move_handler(msg: MoveMessage):
    try:
        motor_move(msg.vx, msg.vy, msg.omega)
        response = BaseMessage(type="move_complete")
    except Exception as e:
        response = ErrorMessage(
            code="MOVE_ERROR",
            message=str(e)
        )
    return response


def stop_handler(msg: StopMessage, sm: StateMachine):
    try:
        sm.robot.motors.stop_motors()
        sm.clear_queue()
        sm.current_job = None
        sm.transition_to(InitState(sm))
        response = BaseMessage(type="stop_complete")
    except Exception as e:
        response = ErrorMessage(
            code="STOP_ERROR",
            message=str(e)
        )
    return response

def pour_handler(msg: PourMessage):
    try:
        # interfaccia per pouring
        response = PourCompleteMessage(ml_poured=30)
    except Exception as e:
        response = ErrorMessage(
            code="POUR_ERROR",
            message=str(e)
        )
    return response


def pour_start_handler(msg: PourStartMessage):
    """Guida manuale: tiene la pompa attiva.

    L'app invia tanti pour_start finché il bottone è premuto; l'handler è
    idempotente, ogni evento riconferma semplicemente la pompa accesa.
    """
    try:
        pump_on()
        response = BaseMessage(type="pour_started")
    except Exception as e:
        response = ErrorMessage(
            code="POUR_ERROR",
            message=str(e)
        )
    return response


def pour_stop_handler(msg: PourStopMessage):
    """Guida manuale: ferma la pompa al rilascio del bottone."""
    try:
        pump_off()
        response = BaseMessage(type="pour_stopped")
    except Exception as e:
        response = ErrorMessage(
            code="POUR_ERROR",
            message=str(e)
        )
    return response
