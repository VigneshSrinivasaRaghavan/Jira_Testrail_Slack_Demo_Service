"""Database storage and initialization for Slack mock service."""

import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, Channel, ChannelMember, Message, File, User, Reaction

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

    db = SessionLocal()
    try:
        if db.query(Channel).count() == 0:
            seed_data(db)
    finally:
        db.close()


def seed_data(db: Session):
    """Add initial seed data for demo purposes."""

    # Create users
    users = [
        User(id="U1111111111", name="alice", real_name="Alice Johnson",
             display_name="Alice", email="alice@example.com", avatar_color="#E01E5A"),
        User(id="U2222222222", name="bob", real_name="Bob Smith",
             display_name="Bob", email="bob@example.com", avatar_color="#2EB67D"),
        User(id="U3333333333", name="charlie", real_name="Charlie Davis",
             display_name="Charlie", email="charlie@example.com", avatar_color="#ECB22E"),
        User(id="USLACKBOT", name="slackbot", real_name="Slackbot",
             display_name="Slackbot", email="", is_bot=True, avatar_color="#4a154b"),
    ]
    for user in users:
        db.add(user)

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
        ),
        Channel(
            id="C1122334455",
            name="dev-alerts",
            topic="Development Alerts",
            purpose="Automated alerts from CI/CD pipelines and monitoring"
        ),
    ]
    for channel in channels:
        db.add(channel)

    db.commit()

    # Seed channel memberships
    memberships = [
        ("C1234567890", "U1111111111"),
        ("C1234567890", "U2222222222"),
        ("C0987654321", "U1111111111"),
        ("C0987654321", "U2222222222"),
        ("C0987654321", "U3333333333"),
        ("C1122334455", "U1111111111"),
        ("C1122334455", "U3333333333"),
    ]
    for channel_id, user_id in memberships:
        db.add(ChannelMember(channel_id=channel_id, user_id=user_id))

    db.commit()

    # Create sample messages
    base_ts = time.time()
    messages = [
        Message(ts=f"{base_ts - 3600:.6f}", channel_id="C1234567890",
                user="U1111111111",
                text="🚀 Test automation run completed successfully! All 47 tests passed."),
        Message(ts=f"{base_ts - 3000:.6f}", channel_id="C1234567890",
                user="U2222222222",
                text="Found a critical bug in the login flow. Creating JIRA ticket now."),
        Message(ts=f"{base_ts - 1800:.6f}", channel_id="C1234567890",
                user="U1111111111",
                text="Bug has been logged as QA-123. TestRail case updated with failure details."),
        Message(ts=f"{base_ts - 900:.6f}", channel_id="C0987654321",
                user="U3333333333",
                text="Good morning team! Don't forget about the sprint retrospective at 2 PM."),
        Message(ts=f"{base_ts - 300:.6f}", channel_id="C0987654321",
                user="U2222222222",
                text="Thanks for the reminder! I'll be there."),
        Message(ts=f"{base_ts - 120:.6f}", channel_id="C1122334455",
                user="USLACKBOT",
                text="✅ Build #142 passed — all tests green."),
    ]
    for msg in messages:
        db.add(msg)

    db.commit()


# ──────────────────────────── timestamp ────────────────────────────

def generate_timestamp() -> str:
    """Generate Slack-style timestamp."""
    return f"{time.time():.6f}"


# ──────────────────────────── channels ─────────────────────────────

def get_channel_by_name(db: Session, channel_name: str) -> Channel:
    return db.query(Channel).filter(Channel.name == channel_name).first()


def get_channel_by_id(db: Session, channel_id: str) -> Channel:
    return db.query(Channel).filter(Channel.id == channel_id).first()


def create_channel(db: Session, name: str, is_private: bool = False,
                   topic: str = "", purpose: str = "") -> Channel:
    channel_id = f"C{int(time.time())}{os.urandom(3).hex().upper()}"
    channel = Channel(id=channel_id, name=name, is_private=is_private,
                      topic=topic, purpose=purpose)
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


def get_channel_members(db: Session, channel_id: str) -> list:
    return db.query(ChannelMember).filter(ChannelMember.channel_id == channel_id).all()


# ──────────────────────────── messages ─────────────────────────────

def create_message(db: Session, channel_id: str, user: str, text: str,
                   thread_ts: str = None) -> Message:
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


def get_messages(db: Session, channel_id: str, limit: int = 50,
                 oldest: str = None, latest: str = None) -> list:
    query = db.query(Message).filter(Message.channel_id == channel_id)
    if oldest:
        query = query.filter(Message.ts >= oldest)
    if latest:
        query = query.filter(Message.ts <= latest)
    return query.order_by(Message.ts.desc()).limit(limit).all()


def get_message_by_ts(db: Session, ts: str) -> Message:
    return db.query(Message).filter(Message.ts == ts).first()


def get_thread_replies(db: Session, channel_id: str, thread_ts: str,
                       limit: int = 50) -> list:
    return (db.query(Message)
            .filter(Message.channel_id == channel_id,
                    Message.thread_ts == thread_ts)
            .order_by(Message.ts.asc())
            .limit(limit)
            .all())


# ──────────────────────────── files ────────────────────────────────

def create_file(db: Session, name: str, title: str, mimetype: str,
                filetype: str, size: int, message_id: int = None) -> File:
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


# ──────────────────────────── users ────────────────────────────────

def get_all_users(db: Session) -> list:
    return db.query(User).all()


def get_user_by_id(db: Session, user_id: str) -> User:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_name(db: Session, name: str) -> User:
    return db.query(User).filter(User.name == name).first()


# ──────────────────────────── reactions ────────────────────────────

def add_reaction(db: Session, message_ts: str, name: str, user_id: str) -> Reaction:
    existing = (db.query(Reaction)
                .filter(Reaction.message_ts == message_ts,
                        Reaction.name == name,
                        Reaction.user_id == user_id)
                .first())
    if existing:
        return existing
    reaction = Reaction(message_ts=message_ts, name=name, user_id=user_id)
    db.add(reaction)
    db.commit()
    db.refresh(reaction)
    return reaction


def get_reactions_for_message(db: Session, message_ts: str) -> list:
    return db.query(Reaction).filter(Reaction.message_ts == message_ts).all()
