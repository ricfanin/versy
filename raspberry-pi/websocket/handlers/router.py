from websocket.utils.messages import BaseMessage, ArucoFindMessage, MoveMessage, StopMessage, PourMessage, PourStartMessage, PourStopMessage
from websocket.handlers.aruco_handler import aruco_handler
from websocket.handlers.action_handler import move_handler, stop_handler, pour_handler, pour_start_handler, pour_stop_handler
from machine.state_machine import StateMachine

def handle_message(message: BaseMessage, sm: StateMachine, username: str):
    match message:
        case ArucoFindMessage():
            return aruco_handler(message, sm, username)
        case MoveMessage():
            return move_handler(message)
        case StopMessage():
            return stop_handler(message, sm)
        case PourMessage():
            return pour_handler(message)
        case PourStartMessage():
            return pour_start_handler(message)
        case PourStopMessage():
            return pour_stop_handler(message)
