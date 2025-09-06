"""SQLAlchemy models for Slack mock service."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Channel(Base):
    """Slack channel model."""
    
    __tablename__ = "channels"
    
    id = Column(String, primary_key=True)  # e.g., "C1234567890"
    name = Column(String(80), unique=True, nullable=False)  # e.g., "qa-reports"
    topic = Column(String(250), default="")
    purpose = Column(String(250), default="")
    is_private = Column(Boolean, default=False)
    created_on = Column(DateTime, default=datetime.utcnow)
    updated_on = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("Message", back_populates="channel", cascade="all, delete-orphan")


class Message(Base):
    """Slack message model."""
    
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(String, unique=True, nullable=False)  # Slack timestamp format
    channel_id = Column(String, ForeignKey("channels.id"), nullable=False)
    user = Column(String(50), nullable=False)  # e.g., "U1234567890" or username
    text = Column(Text, nullable=False)
    thread_ts = Column(String, nullable=True)  # For threaded messages
    created_on = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    channel = relationship("Channel", back_populates="messages")
    files = relationship("File", back_populates="message", cascade="all, delete-orphan")


class File(Base):
    """Slack file attachment model."""
    
    __tablename__ = "files"
    
    id = Column(String, primary_key=True)  # e.g., "F1234567890"
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    name = Column(String(255), nullable=False)
    title = Column(String(255), nullable=True)
    mimetype = Column(String(100), nullable=False)
    filetype = Column(String(50), nullable=False)
    size = Column(Integer, nullable=False)
    url_private = Column(String(500), nullable=False)
    permalink = Column(String(500), nullable=False)
    created_on = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("Message", back_populates="files")
