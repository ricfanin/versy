"""Mock delle librerie Raspberry Pi per sviluppo su PC"""
class MockI2CDevice:
    def __init__(self, i2c_bus, address):
        self.address=address
        print(f"[MOCK] I2CDEVICE inizializzato all'indirizzo {hex(address)}")
    
    def write(self, data):
        print(f"[MOCK] I2C write: {list(data)}")
    
class MockI2C:
    def __init__(self, scl, sda):
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