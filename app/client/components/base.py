from abc import ABC, abstractmethod
from ttkbootstrap import Window
from typing import Dict

class AppInterface(ABC):
    def __init__(self):
        self.window: None | Window = None
        self.username: None | str = None
        self.room_id: None | int = None
        self.states: Dict[str, WindowState] 

    @abstractmethod
    def clear_window(self):
        pass

    @abstractmethod
    def change_state(self, state_name: str):
        pass
    
    @abstractmethod
    def set_username(self, username: str):
        pass

    @abstractmethod
    def set_room_id(self, room_id: str):
        pass
    
    @abstractmethod
    def run(self):
        pass

class WindowState(ABC):
    def __init__(self, app: AppInterface):
        self.app = app

    @abstractmethod
    def handle(self):
        pass

    @abstractmethod
    def create_ui(self):
        pass



