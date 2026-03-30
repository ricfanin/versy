"""Mock delle librerie Raspberry Pi per sviluppo su PC"""
import random


class MockI2CDevice:
    def __init__(self, i2c_bus, address):
        self.address=address
        print(f"[MOCK] I2CDEVICE inizializzato all'indirizzo {hex(address)}")

    def write(self, data):
        non_voglio_stampa=True
        #print(f"[MOCK] I2C write: {list(data)}")

class MockI2C:
    def __init__(self, scl=None, sda=None):
        # Simula l'inizializzazione del bus I2C con i pin SCL e SDA
        print(f"[MOCK] I2C inizializzato con SCL={scl}, SDA={sda}")


#Mock per board
class MockPin:
    pass
SCL = MockPin() #finto pin SCL
SDA = MockPin() #finto pin SDA

#Mock per I2C device:
class i2c_device:
    I2CDevice = MockI2CDevice


# Mock per ToF sensors (VL53L0X)
class MockDigitalInOut:
    def __init__(self, pin):
        self.pin = pin
        self.value = False

    def switch_to_output(self, value=False):
        self.value = value


class MockVL53L0X:
    def __init__(self, i2c, address=0x29):
        self._address = address
        print(f"[MOCK] VL53L0X inizializzato all'indirizzo {hex(address)}")

    @property
    def range(self):
        return random.randint(50, 500)

    def set_address(self, new_address):
        self._address = new_address


class MockBoard:
    D16 = MockPin()
    D20 = MockPin()
    D21 = MockPin()

    @staticmethod
    def I2C():
        return MockI2C()