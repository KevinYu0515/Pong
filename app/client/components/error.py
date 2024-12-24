from ttkbootstrap.dialogs import Messagebox

class ErrorState:
    def __init__(self, title, message):
        self.title = title
        self.message = message

    def alert(self, parent):
        parent.after(0, lambda: Messagebox.show_error(self.title, self.message, parent=parent))