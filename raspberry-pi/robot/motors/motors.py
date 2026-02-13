import time

import numpy as np

from ..utils.debug import get_logger

logger = get_logger("motors")

# Import condizionali
try:
    import busio  # pyright: ignore[reportAssignmentType]
    from adafruit_bus_device import i2c_device
    from board import SCL, SDA

    MOCK_MODE = False
except ImportError:
    logger.warning("Raspberry Pi libraries not found - using MOCK MODE")
    from ..software_testing.mock_raspberry import SCL, SDA, i2c_device
    from ..software_testing.mock_raspberry import MockI2C as busio_I2C

    MOCK_MODE = True

    class busio:
        I2C = busio_I2C


class Motors:
    __M_1 = 0
    __M_2 = 2
    __M_3 = 1
    __K_ROT = 1
    __ANGOLO_OFFSET_CAMERA_GRADI = 0  # altrimenti drifta in basso a destra

    def __init__(self):
        i2c_bus = busio.I2C(SCL, SDA)
        self.mspi2c = i2c_device.I2CDevice(i2c_bus, 0x10)
        self.kiwi_matrix = self.__compute_kiwi_matrix()

        if MOCK_MODE:
            logger.info("Motors initialized in MOCK MODE - no real hardware")

    def __send_motor_power(self, motor, power):

        if power < 0:
            power = 256 - abs(power)

        data = [motor, power]

        try:
            self.mspi2c.write(bytes(data))
            if MOCK_MODE:
                motor_names = {0: "M1", 2: "M2", 1: "M3"}
                actual_power = power if power < 128 else -(256 - power)
                logger.verbose(
                    f"Motor {motor_names.get(motor, motor)}: power {actual_power}"
                )
        except Exception as e:
            logger.error(f"I2C communication error: {e}")
            time.sleep(0.01)
            self.mspi2c.write(bytes(data))

    def __set_powers(self, m1_power, m2_power, m3_power):
        if MOCK_MODE:
            logger.debug(
                f"Setting motor powers - M1: {m1_power}, M2: {m2_power}, M3: {m3_power}"
            )
        self.__send_motor_power(self.__M_1, m1_power)
        self.__send_motor_power(self.__M_2, m2_power)
        self.__send_motor_power(self.__M_3, m3_power)

    def __compute_kiwi_matrix(self):
        """
        Restituisce la matrice T'' = [ T*R | k ] per un kiwi drive.
        Include: vx, vy, vang.
        """

        phi = np.radians(self.__ANGOLO_OFFSET_CAMERA_GRADI)

        # Matrice T ideale 3x2
        T = np.array([[-1, 0], [1 / 2, -np.sqrt(3) / 2], [1 / 2, np.sqrt(3) / 2]])

        # Matrice di rotazione 2x2
        R = np.array([[np.cos(phi), -np.sin(phi)], [np.sin(phi), np.cos(phi)]])

        T_prime = T @ R  # = matrice traslazione

        # Aggiungo la colonna per la rotazione
        col_rot = np.array([[self.__K_ROT], [self.__K_ROT], [self.__K_ROT]])

        T_full = np.hstack((T_prime, col_rot))

        return T_full

    def __computeKiwiDrivePowers(self, vx, vy, vang=0):
        v = np.array([vx, vy, vang])

        potenze = self.kiwi_matrix @ v
        logger.debug(f"before {potenze}")
        max_power = max(abs(potenze))
        min_power = min(abs(potenze))
        signs = np.sign(potenze)
        zeros = potenze != 0
        potenze = abs(potenze)

        if max_power > 100:
            mult = 75 / max_power
            potenze = signs * (25 + potenze * mult) * zeros
        elif min_power < 25:
            potenze = signs * (25 + potenze * 0.75) * zeros

        logger.debug(f"after {potenze}")
        return potenze

    def setDirectionAndSpeed(self, vx, vy, vang=0):
        """Imposta la direzione e la velocità dei motori."""

        # avanti -> vy
        # rotazione oraria -> vang
        # destra -> vx

        p1, p2, p3 = self.__computeKiwiDrivePowers(vx, -vy, -vang)
        self.__set_powers(-int(p1), -int(p2), -int(p3))

    def test_motors(self) -> bool:
        """Test method for InitState to verify motors functionality"""
        try:
            self.stop_motors()
            logger.info("Motors test passed")
            return True
        except Exception as e:
            logger.error(f"Motors test failed: {e}")
            return False

    def stop_motors(self):
        self.__set_powers(0, 0, 0)


if __name__ == "__main__":
    motors = Motors()
    # motors.test_motors()
    time.sleep(5)
    motors.setDirectionAndSpeed(0, 0, -10)
    time.sleep(2)

    motors.stop_motors()
    # motors.set_powers(80, 0, 0)
    # time.sleep(2)
    # motors.set_powers(0, 80, 0)
    # time.sleep(2)
    # motors.set_powers(0, 0, 80)
    # time.sleep(2)
    # motors.set_powers(0, 0, 0)

# m1 -> 60
# m2 -> 40
# m3 -> 60
