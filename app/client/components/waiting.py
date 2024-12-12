from components.base import WindowState
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from server.database.room_db import get_room_setting, update_room_groups
import json

class WaitingState(WindowState):
    def __init__(self, app):
        super().__init__(app)
    
    def handle(self):
        print("Displaying waiting screen...")
        self.create_ui()

    def create_ui(self):
        self.preview_frame = ttk.Frame(self.app.window, padding=10, borderwidth=20, height=200, relief=RAISED, style='White.TFrame')
        self.preview_frame.pack(fill='x', anchor='n', padx=20, pady=(10, 5))
        
        self.info_frame = ttk.Frame(self.app.window, padding=10, height=200)
        self.info_frame.pack(fill='x', anchor='n', padx=20, pady=5)
        
        room = get_room_setting(self.app.room_id)
        
        left_group = json.loads(room.left_group)
        right_group = json.loads(room.right_group)
        for idx in range(max(len(left_group), len(right_group))):
            player_frame = ttk.Frame(self.info_frame, padding=5)
            player_frame.pack(fill='x', padx=10, pady=5)

            if idx  < len(left_group):
                ttk.Label(player_frame, text=f"{left_group[idx]}", font=("Arial", 14), anchor='w').pack(side='left')
            if idx < len(right_group):
                ttk.Label(player_frame, text=f"{right_group[idx]}", font=("Arial", 14), anchor='e').pack(side='right')
        
        button_frame = ttk.Frame(self.app.window, padding=10, height=200)
        button_frame.pack(fill='x', anchor='s', padx=20, pady=(5, 10))
        ready_button = ttk.Button(button_frame, text="準備", command=lambda: self.ready())
        ready_button.pack(pady=10, padx=10, side='left')
        return_button = ttk.Button(button_frame, text="切換陣營", command=lambda: self.change_group(left_group, right_group))
        return_button.pack(pady=20, padx=10, side='left')
        return_button = ttk.Button(button_frame, text="返回大廳", command=lambda: self.return_to_lobby(left_group, right_group))
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
    
    def change_group(self, left_group: list, right_group: list):
        if self.app.username in left_group:
            left_group.remove(self.app.username)
            right_group.append(self.app.username)
        elif self.app.username in right_group:
            right_group.remove(self.app.username)
            left_group.append(self.app.username)
        
        update_room_groups(self.app.room_id, left_group=json.dumps(left_group), right_group=json.dumps(right_group))
    
    def ready(self):
        print(f"Player {self.app.username} ready")

    def submit_chat(self, chat_text: str):
        print(f"Message from {self.app.username}: {chat_text}")
    
    def return_to_lobby(self, left_group: list, right_group: list):
        if self.app.username in left_group:
            left_group.remove(self.app.username)
        if self.app.username in right_group:
            right_group.remove(self.app.username)

        update_room_groups(self.app.room_id, left_group=json.dumps(left_group), right_group=json.dumps(right_group))
        self.app.change_state('Lobby')