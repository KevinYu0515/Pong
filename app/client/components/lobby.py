from components.base import WindowState
from server.database.room_db import get_all_room_settings, update_room_groups
from ttkbootstrap.constants import *
from constants import mode_list, disconnection_list
import ttkbootstrap as ttk
import json
    
class LobbyState(WindowState):
    def __init__(self, app):
        super().__init__(app)
        self.room_frames = []

    def handle(self):
        print("Displaying lobby screen...")
        self.create_ui()

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
        self.build_room()

    def build_room(self):
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

        rooms = get_all_room_settings()
        for idx, room in enumerate(rooms):
            room_frame = ttk.Labelframe(self.scrollable_frame, text=f"房間 ID: {room.id}", bootstyle=PRIMARY, height=100, padding=20)
            room_frame.pack(pady=10, fill="x", padx=(20, 0), expand=True)
            label_text1 = [f"[{mode_list[room.mode]}]",
                           *([f"[陣營上限 {room.player_limit} 位]"] if room.mode != 0 else ""),
                           f"[每局 {room.duration} s]",
                           f"[最快獲得 {room.winning_points} 分獲勝]"]
            label_text2 = f"缺額機制: {disconnection_list[room.disconnection]}"
            room_ui = {
                "rule": ttk.Label(room_frame, text=' '.join(label_text1), style="primary.TLabel", font=("Arial", 10)),
                "disconnection": ttk.Label(room_frame, text=label_text2, style="primary.TLabel", font=("Arial", 10))
            }
            
            for label in room_ui.values():
                label.pack(pady=5, fill="x")
            
            self.create_join_buttons(room_frame, room.id, json.loads(room.left_group), json.loads(room.right_group), room.player_limit)
            self.room_frames.append(room_frame)

    def create_room(self):
        self.app.change_state('Create_Room')
    
    def create_join_buttons(self, room_frame, id, left_group, right_group, player_limit):
        button_frame = ttk.Frame(room_frame)
        button_frame.pack(pady=10, fill="x")

        if len(left_group) >= player_limit:
            limit_left_label = ttk.Label(button_frame, text=f"已達人數限制", style="danger.TLabel", font=("Arial", 20))
            limit_left_label.pack(pady=10, padx=10, side=ttk.LEFT)
        else:
            left_button = ttk.Button(button_frame, text="加入左邊陣營", bootstyle="primary", command=lambda: self.join_group(id, "left", left_group, right_group))
            left_button.pack(pady=10, padx=10, side=ttk.LEFT)

        count = ttk.Label(button_frame, text=f"{len(left_group)} VS. {len(right_group)}", style="info.TLabel", font=("Arial", 20))
        count.pack(pady=10, padx=30, side=ttk.LEFT, expand=True)
        
        if len(right_group) >= player_limit:
            limit_right_label = ttk.Label(button_frame, text=f"已達人數限制", style="danger.TLabel", font=("Arial", 20))
            limit_right_label.pack(pady=10, padx=10, side=ttk.RIGHT)
        else:
            left_button = ttk.Button(button_frame, text="加入右邊陣營", bootstyle="warning", command=lambda: self.join_group(id, "right", left_group, right_group))
            left_button.pack(pady=10, padx=10, side=ttk.RIGHT)
    
    def join_group(self, room_id, group, left_group: list, right_group: list):
        if group == 'left':
            left_group.append(self.app.username)
        elif group == 'right':
            right_group.append(self.app.username)
        
        print(f"Joining {group} group...")
        update_room_groups(room_id, left_group=json.dumps(left_group), right_group=json.dumps(right_group))
        self.app.set_room_id(room_id)
        self.app.change_state('Waiting')

    def on_logout(self):
        print("Logging out...")
        self.app.change_state('Login')