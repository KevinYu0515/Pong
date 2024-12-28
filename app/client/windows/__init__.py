import ttkbootstrap as ttk
from .login import LoginState
from .lobby import LobbyState
from .base import AppInterface
from .creating import Create_RoomState
from .waiting import WaitingState
from .ending import EndingState
import asyncio, threading, websockets, json
from ...game import Game_Client
from ...utils import *

SERVER_URL = "ws://127.0.0.1:10001"

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
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.is_start = False
        self.username = None
        self.room_id = None
        self.states = {
            'Login': LoginState,
            'Lobby': LobbyState,
            'Create_Room': Create_RoomState,
            'Waiting': WaitingState,
            'Ending': EndingState
        }

        self.state = self.states['Login'](self)
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
                asyncio.create_task(self.handle_event(response))

        except websockets.exceptions.ConnectionClosedOK:
            print("Connection closed cleanly by the server.")
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Connection closed with error: {e}")
        except Exception as e:
            print(f"Error receiving message: {e}")

    async def handle_event(self, response):
        if response.get('status') == 'start_game':

            try:
                game_client_address = get_local_address_from_websockets(self.websocket_client)
                game_server_address = (response.get('data').get('server_address')[0], response.get('data').get('server_address')[1])
                left_players = response.get('data').get('left_players')
                right_players = response.get('data').get('right_players')
                
                game = Game_Client(game_client_address, game_server_address, left_players, right_players, {"side": self.state.side, "idx": self.state.position - 1})
                self.window.withdraw()
                print("Starting game...")
                game.run()
                print("Ending game...")
                self.change_state('Ending')
                self.window.deiconify()

            except Exception as e:
                print(e)

        elif response.get('status') == 'refresh':
            print("Updating state...")
            self.clear_window()
            if 'data' in response and 'chat' in response.get('data'):
                self.state.chat.append(response.get('data').get('chat'))
            self.state.handle()

        elif response.get('status') == 'error':
            async with self.condition:
                self.event_response = response
                self.condition.notify()

        elif response.get('status') == 'success':
            async with self.condition:
                self.event_response = response
                self.condition.notify()

    async def close_connection(self):
        print(self.websocket_client)
        if self.websocket_client:
            try:
                await self.websocket_client.close()
                print("Connection closed")
            except Exception as e:
                print(f"Error closing connection: {e}")

    def on_close(self):
        print("Closing application...")
        self.window.destroy()

        async def handle_logout():
            try:
                if self.username is not None:
                    await self.websocket_client.send(json.dumps({
                        "type": "logout",
                        "data": {
                            "name": self.username
                        }
                    }))
                
                await self.close_connection()

            except Exception as e:
                print(e)
        asyncio.run_coroutine_threadsafe(handle_logout(), self.loop)

    def clear_window(self):
        for widget in self.window.winfo_children():
            widget.destroy()

    def change_state(self, state_name):
        self.clear_window()
        if state_name in self.states:
            self.state = self.states[state_name](self)
            self.state.handle()

    def set_username(self, username):
        self.username = username
        print(f"Username set to: {self.username}")
    
    def set_room_id(self, room_id):
        self.room_id = room_id
        print(f"Room ID set to: {self.room_id}")
    
    def set_start_game(self, is_start):
        self.is_start = is_start
        print(f"Game start: {self.is_start}")

    def run(self):
        self.window.mainloop()