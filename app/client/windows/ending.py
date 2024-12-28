from .base import WindowState
import ttkbootstrap as ttk

class EndingState(WindowState):
    def __init__(self, app):
        super().__init__(app)

    def handle(self):
        print("Displaying ending screen...")
        self.create_ui()

    def create_ui(self):
        center_frame = ttk.Frame(self.app.window)
        center_frame.pack(expand=True)
        self.label = ttk.Label(
            center_frame,
            text="Game Over",
            style="danger.TLabel",
            font=("Arial", 24),
        )
        self.label.pack(pady=10) 
        return_button = ttk.Button(center_frame, text="Return To Lobby", command=self.return_to_lobby)
        return_button.pack(pady=20)

    def return_to_lobby(self):
        self.app.room_id = None
        self.app.change_state('Lobby')