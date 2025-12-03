from src.utils.messages import BaseMessage, ArucoFindMessage, MoveMessage, StopMessage
from src.handlers.aruco_find import aruco_handler
from src.handlers.move import move_handler

def handle_message(message: BaseMessage):
    match message:
        case ArucoFindMessage():
            aruco_handler()
        case MoveMessage():
            move_handler()
        case StopMessage():
            move_handler()

