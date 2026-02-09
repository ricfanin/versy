from .base_state import BaseState
from .states.init_state import InitState


class StateMachine:
    def __init__(self, motors):
        self.current_state: BaseState = InitState()
        self.running = False
        self.motors = motors

    def start(self):
        """Avvia la macchina a stati"""
        self.running = True
        self.current_state.enter(self)

    def update(self):
        """Chiamata dal main loop per aggiornare lo stato"""
        if not self.running:
            return

        try:
            next_state = self.current_state.execute(self)

            if next_state and next_state != self.current_state:
                self._transition_to(next_state)

        except Exception as e:
            print(f"❌ Errore nello stato {type(self.current_state).__name__}: {e}")

    def _transition_to(self, new_state: BaseState):
        """Gestisce la transizione tra stati"""
        print(f"🔄 {type(self.current_state).__name__} → {type(new_state).__name__}")
        self.current_state.exit(self)
        self.previous_state = self.current_state
        self.current_state = new_state
        self.current_state.enter(self)
