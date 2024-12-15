import ttkbootstrap as ttk
from .login import LoginState
from .lobby import LobbyState
from .base import AppInterface
from .creating import Create_RoomState
from .waiting import WaitingState
from .ending import EndingState
import asyncio, threading, websockets, json

SERVER_URL = "ws://localhost:10001"

class App(AppInterface):
    def __init__(self, themename='superhero', title='Neon Pong', geometry='400x400'):
        threading.Thread(target=self.start_websocket_client, daemon=True).start()
        self.loop = asyncio.get_event_loop()
        self.condition = asyncio.Condition()
        self.event_response = None
        self.websocket_client = None
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


    def start_websocket_client(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.connect_to_server())

    async def connect_to_server(self):
        try:
            async with websockets.connect(SERVER_URL) as self.websocket_client:
                print("Connected to server")
                self.loop = asyncio.get_event_loop()
                await asyncio.gather(
                    self.listen_for_messages()
                )

        except Exception as e:
            print(f"Failed to connect to server: {e}")

    async def listen_for_messages(self):
        try:
            while True:
                response = json.loads(await self.websocket_client.recv())
                print(f"Received message: {response}")
                if response.get('status') == 'refresh':
                    print("Updating state...")
                    for widget in self.window.winfo_children():
                        widget.destroy()
                    self.state.handle()
                elif response.get('status') == 'error':
                    print(f"Error: {response.get('message')}")
                elif response.get('status') == 'success':
                    async with self.condition:
                        self.event_response = response
                        self.condition.notify()

        except Exception as e:
            print(f"Error receiving message: {e}")

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