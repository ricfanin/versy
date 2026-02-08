from .motors.motors import Motors

# from .vision.test_camera import Camera
# testing commit


class Robot:
    def __init__(self):
        self.motors = Motors()
