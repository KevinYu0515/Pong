import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Enum, create_engine, ForeignKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from . import Base, Session

class UserDB(Base):
    __tablename__ = 'users'
    
    uuid = Column(
        String, 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    name = Column(String, nullable=False)
    status = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime, nullable=False)
    room_id = Column(Integer, ForeignKey('group.room_id'), nullable=True)
    side = Column(Enum('left', 'right', name='side_enum'), nullable=True)
    position = Column(String(20), nullable=True)
    color = Column(String(20), nullable=True)
    ready = Column(Boolean, default=False)
    group = relationship("GroupDB", back_populates="players")

def add_user(name):
    session = Session()
    user = UserDB(name=name, status=True, last_login=datetime.now())
    session.add(user)
    session.commit()
    session.close()

def user_exists(name):
    session = Session()
    exists = session.query(UserDB).filter_by(name=name).first() is not None
    session.close()
    return exists

def user_online(name):
    session = Session()
    user = session.query(UserDB).filter_by(name=name).first()
    session.close()
    return user.status is True

def user_login(name):
    session = Session()
    user = session.query(UserDB).filter_by(name=name).first()
    user.status = True
    user.last_login = datetime.now()
    session.commit()
    session.close()

def user_logout(name):
    session = Session()
    user = session.query(UserDB).filter_by(name=name).first()
    user.status = False
    user.room_id = None
    user.side = None
    user.position = None
    user.ready = False
    session.commit()
    session.close()

def set_user_ready_status(name, status):
    session = Session()
    user = session.query(UserDB).filter_by(name=name).first()
    user.ready = status
    session.commit()

def set_user_color(name, color):
    session = Session()
    user = session.query(UserDB).filter_by(name=name).first()
    user.color = color
    session.commit()

def set_user_group(name, room_id, side, position):
    session = Session()
    user = session.query(UserDB).filter_by(name=name).first()
    user.room_id = room_id
    user.side = side
    user.position = position
    session.commit()

def set_user_position(name, position):
    session = Session()
    user = session.query(UserDB).filter_by(name=name).first()
    user.position = position
    session.commit()
