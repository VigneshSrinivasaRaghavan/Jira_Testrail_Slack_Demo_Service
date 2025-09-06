"""Database storage and initialization for Slack mock service."""

import os
import time
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, Channel, Message, File

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./slack_mock.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database and create tables."""
    Base.metadata.create_all(bind=engine)
    
    # Add seed data
    db = SessionLocal()
    try:
        # Check if channels already exist
        if db.query(Channel).count() == 0:
            seed_data(db)
    finally:
        db.close()


def seed_data(db: Session):
    """Add initial seed data for demo purposes."""
    
    # Create channels
    channels = [
        Channel(
            id="C1234567890",
            name="qa-reports",
            topic="Quality Assurance Reports and Updates",
            purpose="Channel for sharing QA test results and automation reports"
        ),
        Channel(
            id="C0987654321", 
            name="general",
            topic="General Discussion",
            purpose="Company-wide announcements and general discussion"
        )
    ]
    
    for channel in channels:
        db.add(channel)
    
    db.commit()
    
    # Create sample messages
    base_ts = int(time.time())
    messages = [
        Message(
            ts=f"{base_ts - 3600}.000100",
            channel_id="C1234567890",
            user="U1111111111",
            text="🚀 Test automation run completed successfully! All 47 tests passed."
        ),
        Message(
            ts=f"{base_ts - 3000}.000200", 
            channel_id="C1234567890",
            user="U2222222222",
            text="Found a critical bug in the login flow. Creating JIRA ticket now."
        ),
        Message(
            ts=f"{base_ts - 1800}.000300",
            channel_id="C1234567890", 
            user="U1111111111",
            text="Bug has been logged as QA-123. TestRail case updated with failure details."
        ),
        Message(
            ts=f"{base_ts - 900}.000400",
            channel_id="C0987654321",
            user="U3333333333", 
            text="Good morning team! Don't forget about the sprint retrospective at 2 PM."
        ),
        Message(
            ts=f"{base_ts - 300}.000500",
            channel_id="C0987654321",
            user="U2222222222",
            text="Thanks for the reminder! I'll be there."
        )
    ]
    
    for message in messages:
        db.add(message)
    
    db.commit()


def generate_timestamp() -> str:
    """Generate Slack-style timestamp."""
    return f"{time.time():.6f}"


def get_channel_by_name(db: Session, channel_name: str) -> Channel:
    """Get channel by name."""
    return db.query(Channel).filter(Channel.name == channel_name).first()


def get_channel_by_id(db: Session, channel_id: str) -> Channel:
    """Get channel by ID."""
    return db.query(Channel).filter(Channel.id == channel_id).first()


def create_message(db: Session, channel_id: str, user: str, text: str, thread_ts: str = None) -> Message:
    """Create a new message."""
    message = Message(
        ts=generate_timestamp(),
        channel_id=channel_id,
        user=user,
        text=text,
        thread_ts=thread_ts
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_messages(db: Session, channel_id: str, limit: int = 50, oldest: str = None, latest: str = None) -> list[Message]:
    """Get messages for a channel with pagination."""
    query = db.query(Message).filter(Message.channel_id == channel_id)
    
    if oldest:
        query = query.filter(Message.ts >= oldest)
    if latest:
        query = query.filter(Message.ts <= latest)
    
    return query.order_by(Message.ts.desc()).limit(limit).all()


def create_file(db: Session, name: str, title: str, mimetype: str, filetype: str, size: int, message_id: int = None) -> File:
    """Create a new file record."""
    file_id = f"F{int(time.time())}{os.urandom(4).hex()}"
    
    file_obj = File(
        id=file_id,
        message_id=message_id,
        name=name,
        title=title or name,
        mimetype=mimetype,
        filetype=filetype,
        size=size,
        url_private=f"https://files.slack.com/files-pri/{file_id}/{name}",
        permalink=f"https://mockslack.slack.com/files/{file_id}"
    )
    
    db.add(file_obj)
    db.commit()
    db.refresh(file_obj)
    return file_obj
