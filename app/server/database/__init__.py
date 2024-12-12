from .room_db import create_db

def init_app():
    create_db()
