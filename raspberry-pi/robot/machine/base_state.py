from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from state_machine import StateMachine


class BaseState(ABC):
    """Classe astratta per tutti gli stati del robot"""

    @abstractmethod
    def enter(self, context: "StateMachine") -> None:
        """Chiamata quando si entra nello stato"""
        pass

    @abstractmethod
    def execute(self, context: "StateMachine") -> Optional["BaseState"]:
        """Eseguita ogni ciclo. Ritorna nuovo stato o None"""
        pass

    @abstractmethod
    def exit(self, context: "StateMachine") -> None:
        """Chiamata quando si esce dallo stato"""
        pass
