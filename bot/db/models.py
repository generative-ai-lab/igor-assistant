from sqlalchemy import Column, Integer, BigInteger, Text, Time, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from bot.db.base import Base


class User(Base):
    __tablename__ = "user"

    user_id = Column(BigInteger, primary_key=True, unique=True)
    first_name = Column(Text)
    last_name = Column(Text)
    username = Column(Text)
    context_window = Column(Integer, default=1)


class ChatMessage(Base):
    __tablename__ = "chatmessage"

    uniq_id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('user.user_id'))
    role = Column(Text)
    content = Column(Text)
    is_text = Column(Boolean)
    date_time = Column(Time)
    user = relationship("User")
