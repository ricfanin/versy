from src.utils.messages import BaseMessage, ArucoFindMessage, MoveMessage, StopMessage, PourMessage
from src.handlers.aruco_handler import aruco_handler
from src.handlers.action_handler import move_handler, stop_handler, pour_handler

def handle_message(message: BaseMessage):
    match message:
        case ArucoFindMessage():
            return aruco_handler(message)
        case MoveMessage():
            return move_handler(message)
        case StopMessage():
            return stop_handler(message)
        case PourMessage():
            return pour_handler(message)

