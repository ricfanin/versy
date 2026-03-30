import time
from utils.debug import get_logger

logger = get_logger("tofs")

import board
from digitalio import DigitalInOut
from adafruit_vl53l0x import VL53L0X

# try:
#     import board
#     from digitalio import DigitalInOut
#     from adafruit_vl53l0x import VL53L0X

#     MOCK_MODE = False
# except ImportError:
#     from software_testing.mock_raspberry import (
#         MockDigitalInOut as DigitalInOut,
#         MockVL53L0X as VL53L0X,
#         MockBoard as board,
#     )

#     MOCK_MODE = True


NOMI_SENSORI = ["sinistra (D16)", "destra (D20)", "frontale (D21)"]

SX = 0
DX = 1
FRONT = 2


class Tofs:
    def __init__(self):
        self.distanze = []

        self.i2c = board.I2C()
        self.xshut = [
            DigitalInOut(board.D16),
            DigitalInOut(board.D20),
            DigitalInOut(board.D21),
        ]

        for power_pin in self.xshut:
            power_pin.switch_to_output(value=False)

        # self.vl53[i] = sensore oppure None se non collegato
        self.vl53 = [None] * len(self.xshut)

        for i, power_pin in enumerate(self.xshut):
            power_pin.value = True
            time.sleep(0.02)
            try:
                self.vl53[i] = VL53L0X(self.i2c)
                time.sleep(0.02)
                if i < len(self.xshut) - 1:
                    self.vl53[i].set_address(i + 0x30)
                logger.info(f"ToF {i} ({NOMI_SENSORI[i]}) OK")
            except Exception as e:
                logger.warning(f"ToF {i} ({NOMI_SENSORI[i]}) non trovato: {e}")
                power_pin.value = False
                self.vl53[i] = None

        attivi = sum(1 for s in self.vl53 if s is not None)
        logger.info(f"ToF sensors initialized ({attivi}/{len(self.xshut)} sensori attivi)")

    def detect_range(self):
        distanza_tmp = []
        for index, sensor in enumerate(self.vl53):
            if sensor is None:
                distanza_tmp.append(None)
                continue
            try:
                dis = sensor.range
            except Exception as e:
                logger.error(f"Errore lettura ToF {index}: {e}")
                distanza_tmp.append(None)
                continue
            distanza_tmp.append(dis)
        return distanza_tmp

    def _read_single(self, index):
        sensor = self.vl53[index]
        if sensor is None:
            return None
        try:
            return sensor.range
        except Exception as e:
            logger.error(f"Errore lettura ToF {index}: {e}")
            return None

    def get_sx(self):
        return self._read_single(SX)

    def get_dx(self):
        return self._read_single(DX)

    def get_front(self):
        return self._read_single(FRONT)

    def test_tofs(self) -> bool:
        try:
            result = self.detect_range()
            if len(result) > 0:
                logger.info(f"ToF test passed: {result}")
                return True
            logger.error("ToF test failed: nessuna lettura")
            return False
        except Exception as e:
            logger.error(f"ToF test failed: {e}")
            return False

    def stop(self):
        for pin in self.xshut:
            pin.value = False
        logger.info("ToF sensors stopped")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, sys.path[0] + "/..")

    tofs = Tofs()

    # Uso: python -m robot.tofs        → testa tutti quelli collegati
    #      python -m robot.tofs 0      → testa solo sensore 0 (sinistra)
    #      python -m robot.tofs 2      → testa solo sensore 2 (frontale)
    if len(sys.argv) > 1:
        idx = int(sys.argv[1])
        if idx < 0 or idx >= len(tofs.vl53):
            print(f"Indice non valido. Usa 0-{len(tofs.vl53) - 1}")
            sys.exit(1)
        if tofs.vl53[idx] is None:
            print(f"ToF {idx} ({NOMI_SENSORI[idx]}) non collegato")
            sys.exit(1)
        indici = [idx]
    else:
        indici = [i for i, s in enumerate(tofs.vl53) if s is not None]

    if not indici:
        print("Nessun sensore ToF trovato!")
        sys.exit(1)

    print(f"\nTest continuo su {len(indici)} sensore/i - premi Ctrl+C per uscire\n")
    try:
        while True:
            for i in indici:
                try:
                    dis = tofs.vl53[i].range
                    print(f"  ToF {i} ({NOMI_SENSORI[i]}): {dis} mm")
                except Exception as e:
                    print(f"  ToF {i} ({NOMI_SENSORI[i]}): ERRORE - {e}")
            print("---")
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nFine test")
    finally:
        tofs.stop()
