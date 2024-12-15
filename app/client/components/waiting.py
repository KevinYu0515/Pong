from components.base import WindowState
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json, asyncio

class WaitingState(WindowState):
    def __init__(self, app):
        super().__init__(app)
        self.left_group = []
        self.right_group = []
    
    def handle(self):
        print("Displaying waiting screen...")
        self.create_ui()
        asyncio.run_coroutine_threadsafe(self.get_players(), self.app.loop)

    def create_ui(self):
        self.preview_frame = ttk.Frame(self.app.window, padding=10, borderwidth=20, height=200, relief=RAISED, style='White.TFrame')
        self.preview_frame.pack(fill='x', anchor='n', padx=20, pady=(10, 5))
        
        self.info_frame = ttk.Frame(self.app.window, padding=10, height=200)
        self.info_frame.pack(fill='x', anchor='n', padx=20, pady=5)
        
        button_frame = ttk.Frame(self.app.window, padding=10, height=200)
        button_frame.pack(fill='x', anchor='s', padx=20, pady=(5, 10))
        ready_button = ttk.Button(button_frame, text="準備", command=lambda: self.ready())
        ready_button.pack(pady=10, padx=10, side='left')
        return_button = ttk.Button(button_frame, text="切換陣營", command=lambda: self.change_group())
        return_button.pack(pady=20, padx=10, side='left')
        return_button = ttk.Button(button_frame, text="返回大廳", command=lambda: self.return_to_lobby())
        return_button.pack(pady=20, padx=10, side='right')
        
        log_frame = ttk.Frame(self.app.window, padding=10, borderwidth=20, relief=RAISED, style='White.TFrame')
        log_frame.pack(fill='x', pady=10, padx=20)
        log_text = ttk.Label(log_frame, text="測試用訊息...", font=("Arial", 12))
        log_text.pack(fill='x', pady=5)

        chat_frame = ttk.Frame(self.app.window, padding=10, height=200, relief=RAISED, style='default.TFrame')
        chat_frame.pack(fill='x', anchor='s', padx=20, pady=(5, 10))
        chat_input = ttk.Entry(chat_frame)
        chat_input.pack(pady=10, fill='x', expand=True, anchor='w', side='left')
        submit_button = ttk.Button(chat_frame, text="送出", command=lambda: self.submit_chat(chat_input.get()))
        submit_button.pack(pady=10, fill='x', expand=True, anchor='e', side='right')

    async def get_players(self):
        try:
            await self.app.websocket_client.send(json.dumps({
                "type": "get_players",
                "data": {
                    "room_id": self.app.room_id
                }
            }))
            
            async with self.app.condition:
                await self.app.condition.wait()
                data = self.app.event_response.get('data')
                self.left_group = data.get('left_group')
                self.right_group = data.get('right_group')
                self.update_players()

        except Exception as e:  
            print(e)

    def update_players(self):
        for widget in self.info_frame.winfo_children():
            widget.destroy()
        for idx in range(max(len(self.left_group), len(self.right_group))):
            player_frame = ttk.Frame(self.info_frame, padding=5)
            player_frame.pack(fill='x', padx=10, pady=5)

            if idx  < len(self.left_group):
                ttk.Label(player_frame, text=f"{self.left_group[idx]}", font=("Arial", 14), anchor='w').pack(side='left')
            if idx < len(self.right_group):
                ttk.Label(player_frame, text=f"{self.right_group[idx]}", font=("Arial", 14), anchor='e').pack(side='right')
    
    def change_group(self):
        if self.app.username in self.left_group:
            self.left_group.remove(self.app.username)
            self.right_group.append(self.app.username)
        elif self.app.username in self.right_group:
            self.right_group.remove(self.app.username)
            self.left_group.append(self.app.username)
        
        print(f"Player {self.app.username} changed group")
        
        async def handle_change_group():
            try:
                await self.app.websocket_client.send(json.dumps({
                    "type": "group_action",
                    "action": "change_group",
                    "data": {
                        "room_id": self.app.room_id,
                        "left_group": self.left_group,
                        "right_group": self.right_group
                    }
                }))
                
                async with self.app.condition:
                    await self.app.condition.wait()
                    print("Changed group")
                    self.update_players()

            except Exception as e:
                print(e)
        
        asyncio.run_coroutine_threadsafe(handle_change_group(), self.app.loop)
    
    def ready(self):
        print(f"Player {self.app.username} ready")

    def submit_chat(self, chat_text: str):
        print(f"Message from {self.app.username}: {chat_text}")
    
    def return_to_lobby(self):
        if self.app.username in self.left_group:
            self.left_group.remove(self.app.username)
        if self.app.username in self.right_group:
            self.right_group.remove(self.app.username)

        async def handle_return_to_lobby():
            try:
                await self.app.websocket_client.send(json.dumps({
                    "type": "group_action",
                    "action": "leave_room",
                    "data": {
                        "room_id": self.app.room_id,
                        "left_group": self.left_group,
                        "right_group": self.right_group
                    }
                }))

                async with self.app.condition:
                    await self.app.condition.wait()
                    print("Leave room")
                    self.app.change_state('Lobby')

            except Exception as e:
                print(e)

        asyncio.run_coroutine_threadsafe(handle_return_to_lobby(), self.app.loop)