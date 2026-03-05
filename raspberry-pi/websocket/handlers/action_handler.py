from src.utils.messages import PourMessage, MoveMessage, StopMessage, BaseMessage, ErrorMessage, PourCompleteMessage

def move_handler(msg: MoveMessage):
    try:
        # interfaccia per movimento
        response = BaseMessage(type="move_complete")
    except Exception as e:
        response = ErrorMessage(
            code="MOVE_ERROR",
            message=str(e)
        )
    return response


def stop_handler(msg: StopMessage):
    try:
        # interfaccia per stop
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
