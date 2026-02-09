import time

from robot.robot import Robot


def main():
    """Entry point per testare il robot"""
    try:
        print("🤖 Inizializzazione robot...")
        robot = Robot()

        print("🚀 Avvio robot...")
        robot.start()

        # Main loop
        print("🔄 Avvio main loop...")
        while True:
            robot.state_machine.update()
            time.sleep(0.1)  # 10Hz update rate

    except KeyboardInterrupt:
        print("\n🛑 Arresto richiesto dall'utente")
    except Exception as e:
        print(f"❌ Errore: {e}")
    finally:
        print("🔧 Cleanup completato")


if __name__ == "__main__":
    main()
