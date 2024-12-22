from components.base import WindowState
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
import json, asyncio

class WaitingState(WindowState):
    def __init__(self, app):
        super().__init__(app)
        self.is_ready = False
        self.position = 0
        self.limit = 0
        self.side = 'left'
        self.left_group = []
        self.right_group = []
        self.player_frames = []
        self.chat = []
    
    def handle(self):
        print("Displaying waiting screen...")
        self.create_ui()
        asyncio.run_coroutine_threadsafe(self.get_players(), self.app.loop)

    def create_ui(self):
        self.preview_frame = ttk.Frame(self.app.window, padding=10, borderwidth=20, height=200, relief=RAISED, style='White.TFrame')
        self.preview_frame.pack(fill='x', anchor='n', padx=20, pady=(10, 5))

        self.info_frame = ttk.Frame(self.app.window, padding=10, height=200)
        self.info_frame.pack(fill='x', anchor='n', padx=20, pady=5)
        
        self.button_frame = ttk.Frame(self.app.window, padding=10, height=200)
        self.button_frame.pack(fill='x', anchor='s', padx=20, pady=(5, 10))
        
        self.ready_button = ttk.Button(self.button_frame, text="準備", command=lambda: self.toggle_ready(), style='success.TButton')
        self.ready_button.pack(pady=10, padx=10, side='left')
        return_button = ttk.Button(self.button_frame, text="切換陣營", command=lambda: self.change_group(), style='warning.TButton')
        return_button.pack(pady=20, padx=10, side='left')
        return_button = ttk.Button(self.button_frame, text="返回大廳", command=lambda: self.return_to_lobby())
        return_button.pack(pady=20, padx=10, side='right')
        
        self.log_frame = ttk.Frame(self.app.window, padding=10, borderwidth=20, relief=RAISED, style='White.TFrame')
        self.log_frame.pack(fill='x', pady=10, padx=20)
        for text in self.chat:
            log_text = ttk.Label(self.log_frame, text=text, font=("Arial", 12))
            log_text.pack(fill='x', pady=5)

        self.chat_frame = ttk.Frame(self.app.window, padding=10, height=200, relief=RAISED, style='default.TFrame')
        self.chat_frame.pack(fill='x', anchor='s', padx=20, pady=(5, 10))
        self.chat_input = ttk.Entry(self.chat_frame)
        self.chat_input.pack(pady=10, fill='x', expand=True, anchor='w', side='left')
        self.submit_button = ttk.Button(self.chat_frame, text="送出", command=lambda: self.submit_chat(self.chat_input.get()))
        self.submit_button.pack(pady=10, fill='x', expand=True, anchor='e', side='right')

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
                self.limit = data.get('player_limit')
                self.update_players()

        except Exception as e:
            print(e)

    def update_players(self):
        self.player_frames = []
        for widget in self.info_frame.winfo_children():
            widget.destroy()

        def switch_player(idx, side):
            print(f"Switching player to {idx}")
            group = self.left_group if side == 'left' else self.right_group

            async def handle_switch_player():
                try:
                    await self.app.websocket_client.send(json.dumps({
                        "type": "switch_position",
                        "data": {
                            "name1": self.app.username,
                            "name2": group[idx].get('name'),
                            "position1": group[idx].get('position'),
                            "position2": idx,
                        }
                    }))

                    async with self.app.condition:
                        await self.app.condition.wait()
                        print("Switched player")
                        self.update_players()
                except Exception as e:
                    print(e)

            asyncio.run_coroutine_threadsafe(handle_switch_player(), self.app.loop)

        
        if  any(player['name'] == self.app.username for player in self.left_group):
            for idx, player in enumerate(self.left_group):
                if player.get('name') == self.app.username:
                    self.position = idx
                    self.side = 'left'

                player_frame = ttk.Frame(self.info_frame, padding=5)
                player_frame.pack(fill='x', padx=10, pady=5)
                ttk.Label(player_frame, text=f"{player.get('name')}", font=("Arial", 14), anchor=('w')).pack(side='left')

                if player.get('name') != self.app.username:
                    ttk.Button(player_frame, text="更換", command=lambda: switch_player(idx, 'left')).pack(side='right')
                
                self.player_frames.append(player_frame)
        
        elif any(player['name'] == self.app.username for player in self.right_group):
            for idx, player in enumerate(self.right_group):
                if player.get('name') == self.app.username:
                    self.position = idx
                    self.side = 'right'

                player_frame = ttk.Frame(self.info_frame, padding=5)
                player_frame.pack(fill='x', padx=10, pady=5)
                ttk.Label(player_frame, text=f"{player.get('name')}", font=("Arial", 14), anchor=('e')).pack(side='right')
                    
                if player.get('name') != self.app.username:
                    ttk.Button(player_frame, text="更換", command=lambda: switch_player(idx, 'right')).pack(side='left')

                self.player_frames.append(player_frame)
        
        self.ready_button.config(text="準備", style='success.TButton')
        self.player_frames[self.position].config(style='default.TFrame')
        self.player_frames[self.position].children['!label'].config(style='default.TLabel')
        self.is_ready = False

        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        
        self.control_bars = []
        for player in self.left_group:
            control_bar_style = ttk.Style()
            custom_color = "#4CAF50"
            control_bar_style.configure('White.TFrame', background=custom_color)
            control_bar = ttk.Frame(self.preview_frame, width=10, height=100, style='White.TFrame')
            control_bar.pack(side='left', anchor='w', padx=10, pady=5)
            self.control_bars.append(control_bar)

    def change_group(self):
        def up_to_limit(group):
            if len(group) >= self.limit:
                Messagebox.show_info(message="該陣營已達到人數上限")
                return True
            return False
        
        if  self.side == 'left':
            if up_to_limit(self.right_group):
                return
            the_chosen_player = next((player for player in self.left_group if player['name'] == self.app.username), None)
            if the_chosen_player:
                self.left_group.remove(the_chosen_player)
                self.right_group.append(the_chosen_player)
        elif self.side == 'right':
            if up_to_limit(self.left_group):
                return
            the_chosen_player = next((player for player in self.right_group if player['name'] == self.app.username), None)
            if the_chosen_player:
                self.right_group.remove(the_chosen_player)
                self.left_group.append(the_chosen_player)
        
        print(f"Player {self.app.username} changed group")
        
        async def handle_change_group():
            try:
                await self.app.websocket_client.send(json.dumps({
                    "type": "group_action",
                    "action": "change_group",
                    "data": {
                        "room_id": self.app.room_id,
                        "side": 'right' if self.side == 'left' else 'left',
                        "username": self.app.username
                    }
                }))
                
                async with self.app.condition:
                    await self.app.condition.wait()
                    print("Changed group")
                    self.update_players()
            except Exception as e:
                print(e)
        
        asyncio.run_coroutine_threadsafe(handle_change_group(), self.app.loop)
    
    def toggle_ready(self):
        ready_style = ttk.Style()
        ready_style.configure("Ready.TLabel", background="#5cb85c")

        def check_last_ready():
            all_players = self.left_group + self.right_group
            return sum(1 for player in all_players if not player.get('ready')) == 1

        if check_last_ready():
            Messagebox.show_info(message="你是最後一位準備玩家，按下確認將開始遊戲")

        async def handle_toggle_ready():
            try:
                await self.app.websocket_client.send(json.dumps({
                    "type": "toggle_ready",
                    "data": {
                        "name": self.app.username,
                        "status": self.is_ready
                    }
                }))

                async with self.app.condition:
                    await self.app.condition.wait()
                    print(f"Player {self.app.username} is {'ready' if self.is_ready else 'unready'}")

            except Exception as e:
                print(e)

        if not self.is_ready:
            self.ready_button.config(text="取消準備", style='warning.TButton')
            self.player_frames[self.position].config(style='success.TFrame')
            self.player_frames[self.position].children['!label'].config(style='Ready.TLabel')
            self.is_ready = True
        else:
            self.ready_button.config(text="準備", style='success.TButton')
            self.player_frames[self.position].config(style='default.TFrame')
            self.player_frames[self.position].children['!label'].config(style='default.TLabel')
            self.is_ready = False
        
        asyncio.run_coroutine_threadsafe(handle_toggle_ready(), self.app.loop)

    def submit_chat(self, chat_text: str):

        print(f"Message from {self.app.username}: {chat_text}")
        async def handle_chat():
            try:
                await self.app.websocket_client.send(json.dumps({
                    "type": "chat",
                    "data": {
                        "room_id": self.app.room_id,
                        "side": self.side,
                        "message": f"{self.app.username}: {chat_text}", 
                    }
                })) 

            except Exception as e:
                print(e)

        self.chat_input.delete(0, 'end')
        asyncio.run_coroutine_threadsafe(handle_chat(), self.app.loop)

    def return_to_lobby(self):
        if self.side == 'left':
            the_chosen_player = next((player for player in self.left_group if player['name'] == self.app.username), None)
            if the_chosen_player:
                self.left_group.remove(the_chosen_player)
        elif self.side == 'right':
            the_chosen_player = next((player for player in self.right_group if player['name'] == self.app.username), None)
            if the_chosen_player:
                self.right_group.remove(the_chosen_player)

        async def handle_return_to_lobby():
            try:
                await self.app.websocket_client.send(json.dumps({
                    "type": "group_action",
                    "action": "leave_room",
                    "data": {
                        "room_id": self.app.room_id,
                        "side": self.side,
                        "username": self.app.username
                    }
                }))

                async with self.app.condition:
                    await self.app.condition.wait()
                    print("Leave room")
                    self.app.room_id = None
                    self.app.change_state('Lobby')

            except Exception as e:
                print(e)

        asyncio.run_coroutine_threadsafe(handle_return_to_lobby(), self.app.loop)