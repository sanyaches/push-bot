# All for database #
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String

engine = create_engine('sqlite:///some.db', connect_args={'check_same_thread': False})
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


class User(Base):
    __tablename__ = 'users'

    chat_id = Column(Integer, primary_key=True)
    vk_token = Column(String)
    gm_credentials = Column(String)

    def __init__(self, chat_id, vk_token, gm_credentials ):
        self.chat_id = chat_id
        self.vk_token = vk_token
        self.gm_credentials = gm_credentials
