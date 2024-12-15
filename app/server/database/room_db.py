from sqlalchemy import Column, Integer, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///room_settings.db"

Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class RoomSettings(Base):
    __tablename__ = 'room_settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    mode = Column(Integer, nullable=False)
    player_limit = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    winning_points = Column(Integer, nullable=False)
    disconnection = Column(Integer, nullable=False)
    left_group = Column(Text, nullable=False, default="[]")
    right_group = Column(Text, nullable=False, default="[]")

    def __repr__(self):
        return f"<RoomSettings(mode={self.mode}, player_limit={self.player_limit}, " \
               f"duration={self.duration}, winning_points={self.winning_points}, disconnection={self.disconnection})>"
    
def create_db():
    Base.metadata.create_all(engine)

def add_room_setting(mode, player_limit, duration, winning_points, disconnection):
    session = Session()
    room_setting = RoomSettings(
        mode=mode,
        player_limit=player_limit,
        duration=duration,
        winning_points=winning_points,
        disconnection=disconnection
    )
    session.add(room_setting)
    session.commit()
    session.close()

def update_room_setting(id, mode=None, player_limit=None, duration=None, winning_points=None, disconnection=None):
    session = Session()
    room_setting = session.query(RoomSettings).filter_by(id=id).first()
    if room_setting:
        if mode is not None:
            room_setting.mode = mode
        if player_limit is not None:
            room_setting.player_limit = player_limit
        if duration is not None:
            room_setting.duration = duration
        if winning_points is not None:
            room_setting.winning_points = winning_points
        if disconnection is not None:
            room_setting.disconnection = disconnection
        session.commit()
    session.close()

def update_room_groups(id, left_group=None, right_group=None):
    session = Session()
    room_setting = session.query(RoomSettings).filter_by(id=id).first()
    if room_setting:
        if left_group is not None:
            room_setting.left_group = left_group
        if right_group is not None:
            room_setting.right_group = right_group
        session.commit()
    session.close()

def delete_room_setting(id):
    session = Session()
    room_setting = session.query(RoomSettings).filter_by(id=id).first()
    if room_setting:
        session.delete(room_setting)
        session.commit()
    session.close()

def get_room_setting(id):
    session = Session()
    room_setting = session.query(RoomSettings).filter_by(id=id).first()
    session.close()
    return room_setting


def get_all_room_settings():
    session = Session()
    room_settings = session.query(RoomSettings).all()
    room_settings = [{
        "id": room.id,
        "mode": room.mode,
        "player_limit": room.player_limit,
        "duration": room.duration,
        "winning_points": room.winning_points,
        "disconnection": room.disconnection,
        "left_group": room.left_group,
        "right_group": room.right_group
    } for room in room_settings]
    session.close()
    return room_settings
