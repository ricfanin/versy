import time

from robot.state_machine import StateMachine


def main():
    """Entry point per testare il robot"""
    try:
        print("🤖 Inizializzazione state machine...")
        state_machine = StateMachine()

        print("🚀 Avvio state machine...")
        state_machine.start()

        # Main loop
        print("🔄 Avvio main loop...")
        while True:
            state_machine.update()
            time.sleep(0.1)  # 10Hz update rate

    except KeyboardInterrupt:
        print("\n🛑 Arresto richiesto dall'utente")
    except Exception as e:
        print(f"❌ Errore: {e}")
    finally:
        state_machine.stop()
        print("🔧 Cleanup completato")


if __name__ == "__main__":
    main()
