from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..state_machine import RobotStateMachine

class BaseState(ABC):
    """Classe base per tutti gli stati del robot"""
    
    @abstractmethod
    def enter(self, context: 'RobotStateMachine') -> None:
        """Chiamata quando si entra nello stato"""
        pass
    
    @abstractmethod  
    def execute(self, context: 'RobotStateMachine') -> Optional['BaseState']:
        """Eseguita ogni ciclo. Ritorna nuovo stato o None"""
        pass
    
    @abstractmethod
    def exit(self, context: 'RobotStateMachine') -> None:
        """Chiamata quando si esce dallo stato"""
        pass
