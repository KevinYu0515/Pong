import ttkbootstrap as ttk
from .login import LoginState
from .lobby import LobbyState
from .base import AppInterface
from .creating import Create_RoomState
from .waiting import WaitingState
from .ending import EndingState

class App(AppInterface):
    def __init__(self, themename='superhero', title='Neon Pong', geometry='400x400'):
        self.window = ttk.Window(themename=themename)
        self.window.title(title)
        self.window.geometry(geometry)
        self.username = None
        self.room_id = None
        self.states = {
            'Login': LoginState(self),
            'Lobby': LobbyState(self),
            'Create_Room': Create_RoomState(self),
            'Waiting': WaitingState(self),
            'Ending': EndingState(self)
        }

        self.state = self.states['Login']
        self.state.handle()

    def clear_window(self):
        # ttk.Style.instance = None
        for widget in self.window.winfo_children():
            widget.destroy()
       

    def change_state(self, state_name):
        self.clear_window()
        if state_name in self.states:
            self.state = self.states[state_name]
            self.state.handle()

    def set_username(self, username):
        self.username = username
        print(f"Username set to: {self.username}")
    
    def set_room_id(self, room_id):
        self.room_id = room_id
        print(f"Room ID set to: {self.room_id}")

    def run(self):
        self.window.mainloop()