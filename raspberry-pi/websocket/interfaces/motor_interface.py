from robot.motors import Motors

_motors = Motors()


def move(x: float, y: float) -> None:
    _motors.setDirectionAndSpeed(vx=x * 100, vy=y * 100)


def stop() -> None:
    _motors.stop_motors()
