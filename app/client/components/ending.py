from components.base import WindowState

class EndingState(WindowState):
    def __init__(self, app):
        super().__init__(app)

    def handle(self):
        print("Displaying ending screen...")
        self.create_ui()

    def create_ui(self):
        pass