from .room_db import create_db as create_room_db
from .user_db import create_db as create_user_db

DATABASE_URL = {
    'room': 'sqlite:///room_settings.db',
    'user': 'sqlite:///user.db'
}

def init_db():
    create_room_db()
    create_user_db()
