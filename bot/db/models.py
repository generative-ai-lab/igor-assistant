from sqlalchemy import Column, Integer, BigInteger, Text, Time, Boolean

from bot.db.base import Base


class ChatMessage(Base):
    __tablename__ = "chatmessage"
    
    uniq_id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    user_id = Column(BigInteger)
    user_first_name = Column(Text)
    user_last_name = Column(Text)
    username = Column(Text)
    role = Column(Text)
    content = Column(Text)
    is_text = Column(Boolean)
    date_time = Column(Time)