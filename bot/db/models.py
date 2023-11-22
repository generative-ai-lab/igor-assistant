from sqlalchemy import Column, Integer, BigInteger, Text, Time

from bot.db.base import Base


class ChatMessage(Base):
    __tablename__ = "chatmessage"
    
    uniq_id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    user_id = Column(BigInteger)
    role = Column(Text)
    content = Column(Text)
    date_time = Column(Time)