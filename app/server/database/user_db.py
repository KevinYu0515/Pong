import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = 'sqlite:///user.db'

Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class User(Base):
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

def create_db():
    Base.metadata.create_all(engine)

def add_user(name):
    session = Session()
    user = User(name=name, status=True, last_login=datetime.now())
    session.add(user)
    session.commit()
    print(f"使用者已新增: {user.uuid}, {user.name}")
    session.close()

def user_exists(name):
    session = Session()
    exists = session.query(User).filter_by(name=name).first() is not None
    session.close()
    return exists

def user_online(name):
    session = Session()
    user = session.query(User).filter_by(name=name).first()
    session.close()
    return user.status is True

def user_login(name):
    session = Session()
    user = session.query(User).filter_by(name=name).first()
    user.status = True
    user.last_login = datetime.now()
    session.commit()
    session.close()

def user_logout(name):
    session = Session()
    user = session.query(User).filter_by(name=name).first()
    user.status = False
    session.commit()
    session.close()
