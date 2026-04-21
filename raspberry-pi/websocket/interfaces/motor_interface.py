from robot.motors import Motors

_motors = Motors()


def move(vx: float, vy: float, omega: float) -> None:
    _motors.setDirectionAndSpeed(vx=vx * 100, vy=vy * 100, vang=omega * 100)


def stop() -> None:
    _motors.stop_motors()
