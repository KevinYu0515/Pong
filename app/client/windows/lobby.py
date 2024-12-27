from .base import WindowState
from ttkbootstrap.constants import *
from ..constants import mode_list, disconnection_list
import ttkbootstrap as ttk
import json, asyncio
    
class LobbyState(WindowState):
    def __init__(self, app):
        super().__init__(app)
        self.room_frames = []

    def handle(self):
        print("Displaying lobby screen...")
        self.create_ui()
        asyncio.run_coroutine_threadsafe(self.get_all_rooms(), self.app.loop)

    def create_ui(self):
        self.label_welcome = ttk.Label(
            self.app.window,
            text=f"Welcome, {self.app.username}!",
            style="success.TLabel",
            font=("Arial", 24),
        )
        self.label_welcome.pack(pady=20)
        self.create_room_button = ttk.Button(
            self.app.window, text="Create Room", command=self.create_room
        )
        self.create_room_button.pack(pady=20)

        logout_button = ttk.Button(self.app.window, text="Logout", command=self.on_logout)
        logout_button.pack(pady=20)

    async def get_all_rooms(self):
        print("Getting all rooms...")
        try:
            await self.app.websocket_client.send(json.dumps({"type": "get_all_rooms"}))
            
            async with self.app.condition:
                await self.app.condition.wait()
                print(self.app.event_response.get('data'))
                self.build_room(self.app.event_response.get('data'))

        except Exception as e:
            print(e)

    def build_room(self, rooms=[]):
        print("Building room...")
        self.canvas = ttk.Canvas(self.app.window, highlightthickness=0)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollbar = ttk.Scrollbar(self.app.window, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        def update_scroll_region(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        self.scrollable_frame.bind("<Configure>", update_scroll_region)

        self.room_frames = []
        for idx, room in enumerate(rooms):
            room_frame = ttk.Labelframe(self.scrollable_frame, text=f"房間 ID: {room.get('id')}", bootstyle=PRIMARY, height=100, padding=20)
            room_frame.pack(pady=10, fill="x", padx=(20, 0), expand=True)
            label_text1 = [f"[{mode_list[room.get('mode')]}]",
                           *([f"[陣營上限 {room.get('player_limit')} 位]"] if room.get('mode') != 0 else ""),
                           f"[每局 {room.get('duration')} s]",
                           f"[最快獲得 {room.get('winning_points')} 分獲勝]"]
            room_ui = {
                "rule": ttk.Label(room_frame, text=' '.join(label_text1), style="primary.TLabel", font=("Arial", 10)),
            }
            
            for label in room_ui.values():
                label.pack(pady=5, fill="x")
            
            self.create_join_buttons(room_frame, room.get('id'), room.get('left_count'), room.get('right_count'), room.get('player_limit'))
            self.room_frames.append(room_frame)

    def create_room(self):
        self.app.change_state('Create_Room')
    
    def create_join_buttons(self, room_frame, id, left_count, right_count, player_limit):
        button_frame = ttk.Frame(room_frame)
        button_frame.pack(pady=10, fill="x")

        if left_count >= player_limit:
            limit_left_label = ttk.Label(button_frame, text=f"已達人數限制", style="danger.TLabel", font=("Arial", 20))
            limit_left_label.pack(pady=10, padx=10, side=ttk.LEFT)
        else:
            left_button = ttk.Button(button_frame, text="加入左邊陣營", bootstyle="primary", command=lambda: join_group(id, "left"))
            left_button.pack(pady=10, padx=10, side=ttk.LEFT)

        count = ttk.Label(button_frame, text=f"{left_count} VS. {right_count}", style="info.TLabel", font=("Arial", 20))
        count.pack(pady=10, padx=30, side=ttk.LEFT, expand=True)
        
        if right_count >= player_limit:
            limit_right_label = ttk.Label(button_frame, text=f"已達人數限制", style="danger.TLabel", font=("Arial", 20))
            limit_right_label.pack(pady=10, padx=10, side=ttk.RIGHT)
        else:
            left_button = ttk.Button(button_frame, text="加入右邊陣營", bootstyle="warning", command=lambda: join_group(id, "right"))
            left_button.pack(pady=10, padx=10, side=ttk.RIGHT)
    
        def join_group(room_id, side):
            print(f"Joining {side} group...")

            async def handle_join_group():
                try:
                    await self.app.websocket_client.send(json.dumps({
                        "type": "group_action",
                        "action": "join_group",
                        "data": {
                            "room_id": room_id,
                            "side": side,
                            "username": self.app.username,
                            "position": right_count + 1 if side == 'right' else left_count + 1
                        }
                    }))

                    async with self.app.condition:
                        await self.app.condition.wait()
                        print("Joined group")
                        self.app.set_room_id(room_id)
                        self.app.change_state('Waiting')
    
                except Exception as e:
                    print(e)
            asyncio.run_coroutine_threadsafe(handle_join_group(), self.app.loop)

    def on_logout(self):
        print("Logging out...")

        async def handle_logout():
            try:
                await self.app.websocket_client.send(json.dumps({
                    "type": "logout",
                    "data": {
                        "name": self.app.username
                    }
                }))

                async with self.app.condition:
                    await self.app.condition.wait()
                    print("Logged out")
                    self.app.set_username(None)
                    self.app.change_state('Login')

            except Exception as e:
                print(e)
        
        asyncio.run_coroutine_threadsafe(handle_logout(), self.app.loop)