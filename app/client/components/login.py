from components.base import WindowState
import ttkbootstrap as ttk

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

        login_button = ttk.Button(self.frame, text="Login", command=self.on_login)
        login_button.pack(pady=20)

    def on_login(self):
        username = self.username_entry.get()
        if username:
            print(f"Logged in as {username}")
            self.app.set_username(username)
            self.app.change_state('Lobby')