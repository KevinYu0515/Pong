from abc import ABC, abstractmethod
from ttkbootstrap import Window
from typing import Dict
from asyncio import AbstractEventLoop, Condition

class AppInterface(ABC):
    def __init__(self):
        self.loop: None | AbstractEventLoop = None
        self.websocket_client = None
        self.window: None | Window = None
        self.username: None | str = None
        self.room_id: None | int = None
        self.states: Dict[str, WindowState] 
        self.event_response: None | str = None
        self.condition: None | Condition = None
        self.is_start: bool = False

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
    def set_start_game(self, is_start: bool):
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
