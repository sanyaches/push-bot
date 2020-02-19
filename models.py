from sqlalchemy import create_engine, Column,Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


engine = create_engine('sqlite:///some.db',connect_args={'check_same_thread': False})
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


class User(Base):
    __tablename__ = 'users'

    chat_id = Column(Integer, primary_key=True)
    vk_token = Column(String)

    def __init__(self, chat_id, vk_token):
        self.chat_id = chat_id
        self.vk_token = vk_token
