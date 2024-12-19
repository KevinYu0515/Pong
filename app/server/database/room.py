from sqlalchemy import Column, Integer, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from .group import GroupDB
from .user import UserDB
from . import Base, Session

class RoomSettings(Base):
    __tablename__ = 'room_settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    mode = Column(Integer, nullable=False)
    player_limit = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    winning_points = Column(Integer, nullable=False)
    disconnection = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<RoomSettings(mode={self.mode}, player_limit={self.player_limit}, " \
               f"duration={self.duration}, winning_points={self.winning_points}, disconnection={self.disconnection})>"

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
    room_id = room_setting.id
    session.close()
    return room_id

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
    room = session.query(RoomSettings).filter_by(id=id).first()

    left_group_players = session.query(UserDB).filter(UserDB.room_id == id, UserDB.side == 'left').all()
    right_group_players = session.query(UserDB).filter(UserDB.room_id == id, UserDB.side == 'right').all()
    
    left_group_players = [{
                            "name": player.name,
                            "ready": player.ready,
                            "color": player.color,
                            "position": player.position,
                        } for player in left_group_players]
    right_group_players = [{
                            "name": player.name,
                            "ready": player.ready,
                            "color": player.color,
                            "position": player.position,
                        } for player in right_group_players]

    print(left_group_players)
    print(right_group_players)
    room_setting = {
        "id": room.id,
        "mode": room.mode,
        "player_limit": room.player_limit,
        "duration": room.duration,
        "winning_points": room.winning_points,
        "disconnection": room.disconnection,
        'left_group': left_group_players,
        'right_group': right_group_players
    }
    session.close()
    return room_setting

def get_all_room_settings():
    session = Session()
    room_settings = session.query(RoomSettings).all()

    group_counts = (
        session.query(
            GroupDB.room_id,
            GroupDB.side,
            func.count(UserDB.uuid).label('player_count')
        )
        .join(UserDB, (UserDB.room_id == GroupDB.room_id) & 
                     (UserDB.side == GroupDB.side))
        .group_by(GroupDB.room_id, GroupDB.side)
        .all()
    )
    
    counts_dict = {}
    for room_id, side, count in group_counts:
        if room_id not in counts_dict:
            counts_dict[room_id] = {"left_count": 0, "right_count": 0}
        counts_dict[room_id][f"{side}_count"] = count

    room_settings = [{
        "id": room.id,
        "mode": room.mode,
        "player_limit": room.player_limit,
        "duration": room.duration,
        "winning_points": room.winning_points,
        "disconnection": room.disconnection,
        'left_count': counts_dict.get(room.id, {}).get("left_count", 0),
        'right_count': counts_dict.get(room.id, {}).get("right_count", 0)
    } for room in room_settings]
    session.close()
    return room_settings

def delete_room(room_id):
    session = Session()
    room = session.query(RoomSettings).filter_by(id=room_id).first()
    session.delete(room)
    session.commit()
    session.close()