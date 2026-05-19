from machine.state_machine import StateMachine
from machine.states.init_state import InitState
from websocket.utils.messages import PourMessage, MoveMessage, StopMessage, BaseMessage, ErrorMessage, PourCompleteMessage
from websocket.interfaces.motor_interface import move as motor_move

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
