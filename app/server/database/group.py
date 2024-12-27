from sqlalchemy import Column, Integer, ForeignKey, Enum, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from . import Base, Session

class GroupDB(Base):
    __tablename__ = 'group'
    
    side = Column(Enum('left', 'right', name='side_enum'), nullable=False)
    room_id = Column(Integer, ForeignKey('room_settings.id'), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('side', 'room_id'),
    )
    players = relationship("UserDB", back_populates="group")
    room = relationship("RoomSettings", backref="groups")
    
    @property
    def get_left_group(self):
        return [player for player in self.players if player.side == 'left']

    @property
    def get_right_group(self):
        return [player for player in self.players if player.side == 'right']

def add_new_groups(room_id):
    session = Session()
    left_group = GroupDB(side='left', room_id=room_id)
    right_group = GroupDB(side='right', room_id=room_id)
    session.add(left_group)
    session.add(right_group)
    session.commit()
    session.close()

def get_side_group(room_id, side):
    session = Session()
    group = session.query(GroupDB).filter_by(room_id=room_id, side=side).first()
    session.close()
    return group

def cout_ready_players(room_id):
    session = Session()
    group = session.query(GroupDB).filter_by(room_id=room_id).first()
    ready_players = [player for player in group.players if player.ready]
    session.close()
    return len(ready_players)