from  .base import WindowState
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json, asyncio

class Create_RoomState(WindowState):
    def __init__(self, app):
        super().__init__(app)
    
    def handle(self):
        print("Displaying create_room screen...")
        self.create_ui()

    def create_ui(self):
        self.frame = ttk.Frame(self.app.window, padding=20, width=400, height=400)
        self.frame.pack(fill=BOTH, expand=True)
        self.frame.place(relx=0.5, rely=0.5, anchor="center")

        # 遊戲選項
        self.lf_mode = ttk.Labelframe(self.frame, text="遊戲模式", bootstyle=PRIMARY, width=300, height=100, padding=20)
        self.lf_mode.pack(pady=10, padx=20)
        mode = ttk.IntVar(value=0)
        ttk.Radiobutton(self.lf_mode, text='雙人對打模式', variable=mode, value=0, command=lambda: self.change_settings(mode.get())).pack(side=ttk.LEFT, padx=10)
        ttk.Radiobutton(self.lf_mode, text='多人模式', variable=mode, value=1, command=lambda: self.change_settings(mode.get())).pack(side=ttk.LEFT, padx=10)
        ttk.Radiobutton(self.lf_mode, text='混亂模式', variable=mode, value=2, command=lambda: self.change_settings(mode.get())).pack(side=ttk.LEFT, padx=10)

        # 人數限制
        self.lf_player_limit = ttk.Labelframe(self.frame, text="陣營人數（上限為 3 )",bootstyle=PRIMARY, width=300, height=100, padding=20)
        self.lf_player_limit.pack(pady=10, padx=20)
        player_limit = ttk.Spinbox(self.lf_player_limit, from_=1, to=3, increment=1)
        player_limit.set(1)
        player_limit.pack(fill=X, pady=5)

        # 時間長度
        self.lf_duration = ttk.Labelframe(self.frame, text="每局時間長度（秒）",bootstyle=PRIMARY, width=300, height=100, padding=20)
        self.lf_duration.pack(pady=10, padx=20)
        duration_input = ttk.Spinbox(self.lf_duration, from_=1, to=120, increment=1)
        duration_input.set(10)
        duration_input.pack(fill=X, pady=5)

        # 獲勝條件
        lf = ttk.Labelframe(self.frame, text="最終獲勝分數（上限為 20 )", bootstyle=PRIMARY, width=300, height=100, padding=20)
        lf.pack(pady=10, padx=20)
        winning_points = ttk.Spinbox(lf, from_=1, to=20, increment=1)
        winning_points.set(3)
        winning_points.pack(fill=X, pady=5)

        # 提交按鈕
        ttk.Button(self.frame, text="創建房間", command=lambda: self.submit(
            mode=mode.get(),
            player_limit= 1 if mode.get() == 0 else player_limit.get(),
            duration=duration_input.get(),
            winning_points=winning_points.get(),
        )).pack(pady=10)

        ttk.Button(self.frame, text="返回大廳", command=lambda: self.app.change_state('Lobby')).pack(pady=10)

        self.lf_player_limit.pack_forget()
    
    def submit(self, **result):
        print("Creating Room...", result)

        async def handle_create_room():
            try:
                await self.app.websocket_client.send(json.dumps({
                    "type": "create_room",
                    "data": result
                }))

                async with self.app.condition:
                    await self.app.condition.wait()
                    print(f"Room created successfully")
                    self.app.change_state('Lobby')

            except Exception as e:
                print(e)
       
        asyncio.run_coroutine_threadsafe(handle_create_room(), self.app.loop)

    def change_settings(self, selected_mode):
        self.toggle_player_limit(selected_mode)
        self.toggle_duration(selected_mode)

    def toggle_player_limit(self, selected_mode):
        if selected_mode == 0:
            self.lf_player_limit.pack_forget()
        else:
            self.lf_player_limit.pack(pady=10, padx=20, after=self.lf_mode)
    
    def toggle_duration(self, selected_mode):
        if selected_mode == 2:
            self.lf_duration.pack_forget()
        else:
            self.lf_duration.pack(pady=10, padx=20, after=self.lf_mode)