"""SQLAlchemy models for Slack mock service."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """Slack user model."""

    __tablename__ = "users"

    id = Column(String, primary_key=True)           # e.g. "U1234567890"
    name = Column(String(80), unique=True, nullable=False)
    real_name = Column(String(255), default="")
    display_name = Column(String(255), default="")
    email = Column(String(255), default="")
    is_bot = Column(Boolean, default=False)
    avatar_color = Column(String(7), default="#4a154b")  # hex for avatar circle
    created_on = Column(DateTime, default=datetime.utcnow)


class Reaction(Base):
    """Emoji reaction on a message."""

    __tablename__ = "reactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_ts = Column(String, ForeignKey("messages.ts"), nullable=False)
    name = Column(String(50), nullable=False)        # emoji name without colons
    user_id = Column(String, nullable=False)
    created_on = Column(DateTime, default=datetime.utcnow)

    message = relationship("Message", back_populates="reactions")


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
    members = relationship("ChannelMember", back_populates="channel", cascade="all, delete-orphan")


class ChannelMember(Base):
    """Membership mapping between users and channels."""

    __tablename__ = "channel_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String, ForeignKey("channels.id"), nullable=False)
    user_id = Column(String, nullable=False)
    joined_on = Column(DateTime, default=datetime.utcnow)

    channel = relationship("Channel", back_populates="members")


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
    reactions = relationship("Reaction", back_populates="message", cascade="all, delete-orphan")


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
