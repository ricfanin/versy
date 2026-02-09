from .machine.state_machine import StateMachine
from .motors.motors import Motors
from .vision.camera import Camera


class Robot:
    def __init__(self):
        self.motors = Motors()
        self.camera = Camera()
        self.state_machine = StateMachine()
