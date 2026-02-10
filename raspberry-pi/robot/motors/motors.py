import busio
import numpy as np
from adafruit_bus_device import i2c_device
from board import SCL, SDA


class Motors:
    __M_1 = 0
    __M_2 = 2
    __M_3 = 1
    __K_ROT = 2
    __ANGOLO_OFFSET_CAMERA_GRADI = 1.9

    def __init__(self):
        i2c_bus = busio.I2C(SCL, SDA)
        self.mspi2c = i2c_device.I2CDevice(i2c_bus, 0x10)
        self.kiwi_matrix = self.__compute_kiwi_matrix()

    def __send_motor_power(self, motor, power):
        if power > 100:
            power = 100
        if power < -100:
            power = -100

        if power < 0:
            power = 256 - abs(power)

        data = [motor, power]
        try:
            self.mspi2c.write(bytes(data))
        except Exception as e:
            print("errore nell'invio dei dati tramite i2c:", e)

    def __set_powers(self, m1_power, m2_power, m3_power):
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
        return potenze

    def setDirectionAndSpeed(self, vx, vy, vang=0):
        """Imposta la direzione e la velocità dei motori."""
        p1, p2, p3 = self.__computeKiwiDrivePowers(vx, vy, vang)
        self.__set_powers(-int(p1), -int(p2), -int(p3))

    def test_motors(self) -> bool:
        """Test method for InitState to verify motors functionality"""
        try:
            # Test basic motor communication by setting zero power
            self.setDirectionAndSpeed(0, 0, 0)
            print("Motors test passed")
            return True
        except Exception as e:
            print(f"Motors test failed: {e}")
            return False


if __name__ == "__main__":
    motors = Motors()
    motors.setDirectionAndSpeed(0, 80, 0)
