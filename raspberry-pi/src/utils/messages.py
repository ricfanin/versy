# Messages models

from pydantic import BaseModel, Field
from typing import Literal, Annotated, Union

class BaseMessage(BaseModel):
    type:str

# incoming message

class MoveMessage(BaseMessage):
    type: Literal["move"]
    x: float
    y: float

class StopMessage(BaseMessage):
    type: Literal["stop"]

class ArudoFindMessage(BaseMessage):
    type: Literal["find_aruco"]
    marker_id: int

class PourMessage(BaseMessage):
    type: Literal["pour"]
    ml: int

# outgoing message

class StatusMessage(BaseMessage):
    type: Literal["status"]
    state: str
    battery: int | None = None
    message: str | None = None

class ArucoFoundMessage(BaseMessage):
    type: Literal["aruco_found"]
    marker_id: int
    distance_cm: float
    angle_deg: float

class PourCompleteMessage(BaseMessage):
    type: Literal["pour_complete"]
    ml_poured: float

class ErrorMessage(BaseMessage):
    type: Literal["error"] = "error"
    code: str
    message: str


IncomingMessages = Annotated[
    Union[MoveMessage, StopMessage, ArudoFindMessage, PourMessage],
    Field(discriminator="type")
]

OutgoingMessages = Annotated[
    Union[StatusMessage, ArucoFoundMessage, PourCompleteMessage, ErrorMessage],
    Field(discriminator="type")
]