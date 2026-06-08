from robot.motors import Motors

_motors = Motors()

PUMP_POWER = 255


def move(vx: float, vy: float, omega: float) -> None:
    _motors.setDirectionAndSpeed(vx=vx * 100, vy=vy * 100, vang=omega * 100)


def stop() -> None:
    _motors.stop_motors()


def pump_on() -> None:
    _motors.set_pompa_power(PUMP_POWER)


def pump_off() -> None:
    _motors.set_pompa_power(0)
