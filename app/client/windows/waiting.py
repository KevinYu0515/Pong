from .base import WindowState
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
        self.control_bars = []
    
    def handle(self):
        for widget in self.app.window.winfo_children():
            widget.destroy()

        print("Displaying waiting screen...")
        self.create_ui()
        asyncio.run_coroutine_threadsafe(self.get_players(), self.app.loop)

    def create_ui(self):
        self.preview_frame = ttk.Frame(self.app.window, padding=10, borderwidth=20, height=200, relief=RAISED, style='default.TFrame')
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
        
        self.log_frame = ttk.Frame(self.app.window, padding=10, borderwidth=20, relief=RAISED, style='default.TFrame')
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

        # 玩家準備樣式
        ready_style = ttk.Style()
        ready_style.configure("Ready.TLabel", background="#5cb85c")

        # 布局的玩家樣式
        control_bar_style = ttk.Style()
        control_bar_style.configure('DafultBar.TFrame', background="#4CAF50")

        # 布局預覽 UI 
        self.control_bars.clear()
        for player in self.left_group:
            control_bar = ttk.Frame(self.preview_frame, width=10, height=100, style='DafultBar.TFrame')
            if player.get('name') == self.app.username:
                control_bar.configure(borderwidth=10, relief=RAISED)
            control_bar.pack(side='left', anchor='w', padx=10, pady=5)
            self.control_bars.append(control_bar)
        
        for player in self.right_group:
            control_bar = ttk.Frame(self.preview_frame, width=10, height=100, style='DafultBar.TFrame')
            if player.get('name') == self.app.username:
                control_bar.configure(borderwidth=10, relief=RAISED)
            control_bar.pack(side='right', anchor='e', padx=10, pady=5)
            self.control_bars.append(control_bar)

        # 玩家資訊 UI
        self.player_frames = []
        def switch_player(idx, side):
            print(f"Switching player to {idx}")
            group = self.left_group if side == 'left' else self.right_group

            async def handle_switch_player():
                try:
                    await self.app.websocket_client.send(json.dumps({
                        "type": "switch_position",
                        "data": {
                            "room_id": self.app.room_id,
                            "name1": self.app.username,
                            "name2": group[idx].get('name'),
                            "position1": group[idx].get('position'),
                            "position2": self.position,
                        }
                    }))

                    async with self.app.condition:
                        await self.app.condition.wait()
                        self.handle()

                except Exception as e:
                    print(e)

            asyncio.run_coroutine_threadsafe(handle_switch_player(), self.app.loop)

        if any(player['name'] == self.app.username for player in self.left_group):
            for idx, player in enumerate(self.left_group):
                player_frame = ttk.Frame(self.info_frame, padding=5)
                player_frame.pack(fill='x', padx=10, pady=5)
                ttk.Label(player_frame, text=f"{player.get('name')}", font=("Arial", 14), anchor=('w')).pack(side='left')
                if player.get('ready'):
                    player_frame.config(style='success.TFrame')
                    player_frame.children['!label'].config(style='Ready.TLabel')

                if player.get('name') == self.app.username:
                    self.position = int(player.get('position'))
                    self.side = player.get('side')
                    self.is_ready = player.get('ready')
                elif not player.get('ready'):
                    ttk.Button(player_frame, text="更換", command=lambda idx=idx: switch_player(idx, 'left')).pack(side='right')

                self.player_frames.append(player_frame)
        
        elif any(player['name'] == self.app.username for player in self.right_group):
            for idx, player in enumerate(self.right_group):
                player_frame = ttk.Frame(self.info_frame, padding=5)
                player_frame.pack(fill='x', padx=10, pady=5)
                ttk.Label(player_frame, text=f"{player.get('name')}", font=("Arial", 14), anchor=('e')).pack(side='right')
            
                if player.get('name') == self.app.username:
                    self.position = int(player.get('position'))
                    self.side = player.get('side')
                    self.is_ready = player.get('ready')
                elif not player.get('ready'):
                    ttk.Button(player_frame, text="更換", command=lambda idx=idx: switch_player(idx, 'right')).pack(side='left')

                self.player_frames.append(player_frame)

        if self.is_ready:
            self.ready_button.config(text="取消準備", style='warning.TButton')
            self.player_frames[self.position - 1].config(style='success.TFrame')
            self.player_frames[self.position - 1].children['!label'].config(style='Ready.TLabel')

        else:
            self.ready_button.config(text="準備", style='success.TButton')
            self.player_frames[self.position - 1].config(style='default.TFrame')
            self.player_frames[self.position - 1].children['!label'].config(style='default.TLabel')

    def change_group(self):
        
        group = self.left_group if self.side == 'right' else self.right_group
        if len(group) >= self.limit:
            Messagebox.show_info(message="該陣營已達到人數上限")
            return
        
        print(f"Player {self.app.username} changed group")
        
        async def handle_change_group():
            try:
                await self.app.websocket_client.send(json.dumps({
                    "type": "group_action",
                    "action": "change_group",
                    "data": {
                        "room_id": self.app.room_id,
                        "side": 'right' if self.side == 'left' else 'left',
                        "username": self.app.username,
                        'position': len(self.left_group) + 1 if self.side == 'right' else len(self.right_group) + 1
                    }
                }))
                
                async with self.app.condition:
                    await self.app.condition.wait()
                    print("Changed group")
                    self.handle()

            except Exception as e:
                print(e)
        
        asyncio.run_coroutine_threadsafe(handle_change_group(), self.app.loop)
    
    def toggle_ready(self):

        def check_last_ready():
            if len(self.left_group) == 0 or len(self.right_group) == 0:
                return False
            all_players = self.left_group + self.right_group
            return sum(1 for player in all_players if not player.get('ready')) == 1

        async def handle_toggle_ready():
            try:
                await self.app.websocket_client.send(json.dumps({
                    "type": "toggle_ready",
                    "data": {
                        "room_id": self.app.room_id,
                        "name": self.app.username,
                        "status": self.is_ready,
                    }
                }))

                async with self.app.condition:
                    await self.app.condition.wait()
                    print(f"Player {self.app.username} is {'ready' if self.is_ready else 'unready'}")

            except Exception as e:
                print(e)

        async def start_game():
            try:
                await self.app.websocket_client.send(json.dumps({
                    "type": "start_game",
                    "data": {
                        "room_id": self.app.room_id
                    }
                }))

                async with self.app.condition:
                    await self.app.condition.wait()
                    print("Game started")
                    self.app.change_state('Game')
            except Exception as e:
                print(e)

        if not self.is_ready and check_last_ready():
            result = Messagebox.yesno(message="你是最後一位準備玩家，按下確認將開始遊戲")
            self.app.set_start_game(result == 'Yes')
        else:
            if not self.is_ready and (len(self.left_group) == 0 or len(self.right_group) == 0):
                Messagebox.show_info(message="等待對面陣營加入")
            if not self.is_ready:
                self.ready_button.config(text="取消準備", style='warning.TButton')
                self.player_frames[self.position - 1].config(style='success.TFrame')
                self.player_frames[self.position - 1].children['!label'].config(style='Ready.TLabel')
                self.is_ready = True
            else:
                self.ready_button.config(text="準備", style='success.TButton')
                self.player_frames[self.position - 1].config(style='default.TFrame')
                self.player_frames[self.position - 1].children['!label'].config(style='default.TLabel')
                self.is_ready = False
            asyncio.run_coroutine_threadsafe(handle_toggle_ready(), self.app.loop)
        
        if self.app.is_start:
            self.ready_button.config(text="取消準備", style='warning.TButton')
            self.player_frames[self.position - 1].config(style='success.TFrame')
            self.player_frames[self.position - 1].children['!label'].config(style='Ready.TLabel')
            self.is_ready = True
            asyncio.run_coroutine_threadsafe(handle_toggle_ready(), self.app.loop)
            asyncio.run_coroutine_threadsafe(start_game(), self.app.loop)

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
        async def handle_return_to_lobby():
            try:
                await self.app.websocket_client.send(json.dumps({
                    "type": "group_action",
                    "action": "leave_room",
                    "data": {
                        "room_id": self.app.room_id,
                        "side": self.side,
                        "username": self.app.username,
                        "position": self.position
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