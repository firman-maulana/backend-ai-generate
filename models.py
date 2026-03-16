from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON, Date
from sqlalchemy.orm import relationship
from database import Base
from datetime import date

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=True)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=True)  # null kalau login google
    
    messages = relationship("Message", back_populates="user")
    video_template = relationship("VideoTemplate", back_populates="user")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String)
    content = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, default=date.today)  # Tanggal pesan (tanpa waktu)
    meta_data = Column(JSON, nullable=True)  # Renamed from 'metadata' (reserved word)

    user = relationship("User", back_populates="messages")


class VideoTemplate(Base):
    __tablename__ = "video_templates"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text, nullable=True)
    video_url = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    likes = Column(Integer, default=0)
    duration = Column(String, default="00:00")
    date = Column(Date, default=date.today)

    user = relationship("User", back_populates="video_template")