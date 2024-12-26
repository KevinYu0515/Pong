from .base import WindowState
import ttkbootstrap as ttk
import json, asyncio, threading
from .error import ErrorState

class LoginState(WindowState):
    def __init__(self, app):
        super().__init__(app)

    def handle(self):
        print("Displaying login screen...")
        self.create_ui()

    def create_ui(self):
        self.frame = ttk.Frame(self.app.window, padding=10)
        self.frame.place(relx=0.5, rely=0.5, anchor="center")

        self.title = ttk.Label(self.frame, text="Neon Pong", style="primary.TLabel", font=("Arial", 20))
        self.title.pack(pady=5)

        self.label_username = ttk.Label(self.frame, text="Username")
        self.label_username.pack(pady=5)

        self.username_entry = ttk.Entry(self.frame)
        self.username_entry.pack(pady=10)

        login_button = ttk.Button(self.frame, text="Login", command=lambda: self.on_login())
        login_button.pack(pady=20)

    def on_login(self):
        username = self.username_entry.get()
        if not username:
            return
        
        async def handle_login():
            try:
                await self.app.websocket_client.send(json.dumps({
                    "type": "login",
                    "data": {
                        "name": username
                    }
                }))
                
                async with self.app.condition:
                    await self.app.condition.wait()
                    response = self.app.event_response
                    if response.get('status') == 'error':
                        ErrorState(response.get('message'), "Login Error").alert(self.app.window)
                        self.username_entry.delete(0, 'end')
                    else:
                        print(f"Logged in as {username}")
                        self.app.set_username(username)
                        self.app.change_state('Lobby')
                    

            except Exception as e:
                print(e)

        asyncio.run_coroutine_threadsafe(handle_login(), self.app.loop)