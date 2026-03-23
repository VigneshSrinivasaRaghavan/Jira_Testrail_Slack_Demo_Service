"""API routes for Slack mock service."""

import os
import logging
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from storage import (
    get_db,
    get_channel_by_name, get_channel_by_id, create_channel,
    get_channel_members,
    create_message, get_messages, get_message_by_ts, get_thread_replies,
    create_file,
    get_all_users, get_user_by_id,
    add_reaction, get_reactions_for_message,
)
from models import Channel, Message, User

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")


class SlackAuthError(Exception):
    """Raised when Slack auth fails; caught by app-level handler to return {"ok":false}."""
    def __init__(self, error_code: str):
        self.error_code = error_code
        super().__init__(error_code)

api_router = APIRouter(prefix="/api")
ui_router = APIRouter(prefix="/ui")

# ─────────────────────────── constants ───────────────────────────

WORKSPACE_ID = "T0MOCKTEAM1"
WORKSPACE_NAME = "Mock Workspace"
BOT_USER_ID = "USLACKBOT"
DEMO_TOKENS = {"demo-token", "test-token", "demo-token-12345"}

# ─────────────────────────── auth helpers ────────────────────────


def _extract_token(request: Request) -> Optional[str]:
    """
    Extract Bearer token from:
      1. Authorization: Bearer <token>  header
      2. token= query param
    (POST body token handled separately where needed)
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    token_param = request.query_params.get("token")
    if token_param:
        return token_param
    return None


def _validate_token(token: Optional[str]) -> bool:
    """Accept xoxb-/xoxp-/xoxa- prefixed tokens and known demo tokens."""
    if not token:
        return False
    if token in DEMO_TOKENS:
        return True
    return token.startswith(("xoxb-", "xoxp-", "xoxa-", "xoxs-"))


async def require_auth(request: Request) -> str:
    """
    Dependency that extracts + validates the Slack-style token.
    Returns the raw token string on success.
    Raises SlackAuthError (caught by app-level handler) on failure.
    """
    auth_required = os.getenv("MOCK_AUTH_REQUIRED", "true").lower() == "true"
    if not auth_required:
        return "bypass"

    token = _extract_token(request)
    if not token:
        raise SlackAuthError("not_authed")
    if not _validate_token(token):
        raise SlackAuthError("invalid_auth")
    return token


# Override default HTTPException handler so Slack-format errors flow through
def slack_error(error_code: str, status_code: int = 200):
    """Return a Slack-style error response."""
    return JSONResponse(status_code=status_code,
                        content={"ok": False, "error": error_code})


# ─────────────────────────── pydantic models ─────────────────────

class PostMessageRequest(BaseModel):
    channel: str
    text: str = ""
    username: Optional[str] = Field("SlackBot")
    thread_ts: Optional[str] = None
    attachments: Optional[List[Any]] = None
    blocks: Optional[List[Any]] = None


class UpdateMessageRequest(BaseModel):
    channel: str
    ts: str
    text: str


class DeleteMessageRequest(BaseModel):
    channel: str
    ts: str


class CreateConversationRequest(BaseModel):
    name: str
    is_private: bool = False


class ReactionAddRequest(BaseModel):
    channel: str
    timestamp: str
    name: str


# ─────────────────────────── api.test ────────────────────────────

@api_router.get("/api.test")
@api_router.post("/api.test")
async def api_test(error: Optional[str] = None, foo: Optional[str] = None):
    """Checks API calling code."""
    if error:
        return {"ok": False, "error": error}
    result: dict = {"ok": True}
    if foo:
        result["foo"] = foo
    return result


# ─────────────────────────── auth.test ───────────────────────────

@api_router.get("/auth.test")
@api_router.post("/auth.test")
async def auth_test(token: str = Depends(require_auth)):
    """Checks authentication & identity."""
    return {
        "ok": True,
        "url": "https://mockslack.slack.com/",
        "team": WORKSPACE_NAME,
        "user": "mock_bot",
        "team_id": WORKSPACE_ID,
        "user_id": BOT_USER_ID,
        "bot_id": "B0MOCKBOT01",
        "is_enterprise_install": False,
    }


# ─────────────────────────── chat.* ──────────────────────────────

@api_router.post("/chat.postMessage")
async def post_message(
    request: PostMessageRequest,
    db: Session = Depends(get_db),
    token: str = Depends(require_auth),
):
    """Sends a message to a channel."""
    if not request.text and not request.attachments and not request.blocks:
        return {"ok": False, "error": "no_text"}

    channel = (get_channel_by_name(db, request.channel)
               or get_channel_by_id(db, request.channel))
    if not channel:
        return {"ok": False, "error": "channel_not_found"}

    message = create_message(
        db=db,
        channel_id=channel.id,
        user=request.username or BOT_USER_ID,
        text=request.text,
        thread_ts=request.thread_ts,
    )

    return {
        "ok": True,
        "channel": channel.id,
        "ts": message.ts,
        "message": {
            "type": "message",
            "bot_id": "B0MOCKBOT01",
            "text": message.text,
            "user": message.user,
            "ts": message.ts,
            "team": WORKSPACE_ID,
            "thread_ts": message.thread_ts,
            "attachments": request.attachments or [],
            "blocks": request.blocks or [],
        },
    }


@api_router.post("/chat.update")
async def update_message(
    req: UpdateMessageRequest,
    db: Session = Depends(get_db),
    token: str = Depends(require_auth),
):
    """Updates a message."""
    channel = get_channel_by_name(db, req.channel) or get_channel_by_id(db, req.channel)
    if not channel:
        return {"ok": False, "error": "channel_not_found"}

    msg = get_message_by_ts(db, req.ts)
    if not msg or msg.channel_id != channel.id:
        return {"ok": False, "error": "message_not_found"}

    msg.text = req.text
    db.commit()
    db.refresh(msg)

    return {
        "ok": True,
        "channel": channel.id,
        "ts": msg.ts,
        "text": msg.text,
    }


@api_router.post("/chat.delete")
async def delete_message(
    req: DeleteMessageRequest,
    db: Session = Depends(get_db),
    token: str = Depends(require_auth),
):
    """Deletes a message."""
    channel = get_channel_by_name(db, req.channel) or get_channel_by_id(db, req.channel)
    if not channel:
        return {"ok": False, "error": "channel_not_found"}

    msg = get_message_by_ts(db, req.ts)
    if not msg or msg.channel_id != channel.id:
        return {"ok": False, "error": "message_not_found"}

    db.delete(msg)
    db.commit()

    return {"ok": True, "channel": channel.id, "ts": req.ts}


# ─────────────────────────── conversations.* ─────────────────────

@api_router.get("/conversations.list")
async def conversations_list(
    limit: int = 100,
    cursor: Optional[str] = None,
    exclude_archived: bool = False,
    types: str = "public_channel",
    db: Session = Depends(get_db),
    token: str = Depends(require_auth),
):
    """Lists all channels in a Slack team."""
    channels = db.query(Channel).limit(limit).all()
    return {
        "ok": True,
        "channels": [_channel_obj(c) for c in channels],
        "response_metadata": {"next_cursor": ""},
    }


@api_router.get("/conversations.info")
async def conversations_info(
    channel: str,
    db: Session = Depends(get_db),
    token: str = Depends(require_auth),
):
    """Retrieve information about a conversation."""
    ch = get_channel_by_name(db, channel) or get_channel_by_id(db, channel)
    if not ch:
        return {"ok": False, "error": "channel_not_found"}
    return {"ok": True, "channel": _channel_obj(ch)}


@api_router.post("/conversations.create")
async def conversations_create(
    req: CreateConversationRequest,
    db: Session = Depends(get_db),
    token: str = Depends(require_auth),
):
    """Initiates a public or private channel-based conversation."""
    existing = get_channel_by_name(db, req.name)
    if existing:
        return {"ok": False, "error": "name_taken"}

    channel = create_channel(db, name=req.name, is_private=req.is_private)
    return {"ok": True, "channel": _channel_obj(channel)}


@api_router.get("/conversations.history")
async def get_conversation_history(
    channel: str,
    limit: int = 100,
    oldest: Optional[str] = None,
    latest: Optional[str] = None,
    inclusive: bool = False,
    cursor: Optional[str] = None,
    db: Session = Depends(get_db),
    token: str = Depends(require_auth),
):
    """Fetches a conversation's history of messages and events."""
    channel_obj = get_channel_by_name(db, channel) or get_channel_by_id(db, channel)
    if not channel_obj:
        return {"ok": False, "error": "channel_not_found"}

    messages = get_messages(db, channel_obj.id, limit, oldest, latest)
    formatted = [_message_obj(m, db) for m in reversed(messages)]

    return {
        "ok": True,
        "messages": formatted,
        "has_more": len(messages) == limit,
        "pin_count": 0,
        "channel_actions_ts": None,
        "channel_actions_count": 0,
        "response_metadata": {
            "next_cursor": messages[-1].ts if messages and len(messages) == limit else ""
        },
    }


@api_router.get("/conversations.members")
async def conversations_members(
    channel: str,
    limit: int = 100,
    cursor: Optional[str] = None,
    db: Session = Depends(get_db),
    token: str = Depends(require_auth),
):
    """Retrieve members of a conversation."""
    ch = get_channel_by_name(db, channel) or get_channel_by_id(db, channel)
    if not ch:
        return {"ok": False, "error": "channel_not_found"}

    members = get_channel_members(db, ch.id)
    return {
        "ok": True,
        "members": [m.user_id for m in members],
        "response_metadata": {"next_cursor": ""},
    }


@api_router.get("/conversations.replies")
async def conversations_replies(
    channel: str,
    ts: str,
    limit: int = 100,
    oldest: Optional[str] = None,
    latest: Optional[str] = None,
    cursor: Optional[str] = None,
    db: Session = Depends(get_db),
    token: str = Depends(require_auth),
):
    """Retrieve a thread of messages posted to a conversation."""
    ch = get_channel_by_name(db, channel) or get_channel_by_id(db, channel)
    if not ch:
        return {"ok": False, "error": "channel_not_found"}

    parent = get_message_by_ts(db, ts)
    if not parent:
        return {"ok": False, "error": "thread_not_found"}

    replies = get_thread_replies(db, ch.id, ts, limit)
    all_msgs = [_message_obj(parent, db)] + [_message_obj(r, db) for r in replies]

    return {
        "ok": True,
        "messages": all_msgs,
        "has_more": False,
        "response_metadata": {"next_cursor": ""},
    }


# ─────────────────────────── users.* ─────────────────────────────

@api_router.get("/users.list")
async def users_list(
    limit: int = 100,
    cursor: Optional[str] = None,
    db: Session = Depends(get_db),
    token: str = Depends(require_auth),
):
    """Lists all users in a Slack team."""
    users = get_all_users(db)
    return {
        "ok": True,
        "members": [_user_obj(u) for u in users],
        "cache_ts": 0,
        "response_metadata": {"next_cursor": ""},
    }


@api_router.get("/users.info")
async def users_info(
    user: str,
    db: Session = Depends(get_db),
    token: str = Depends(require_auth),
):
    """Gets information about a user."""
    u = get_user_by_id(db, user)
    if not u:
        return {"ok": False, "error": "user_not_found"}
    return {"ok": True, "user": _user_obj(u)}


# ─────────────────────────── reactions.* ─────────────────────────

@api_router.post("/reactions.add")
async def reactions_add(
    req: ReactionAddRequest,
    db: Session = Depends(get_db),
    token: str = Depends(require_auth),
):
    """Adds a reaction to an item."""
    ch = get_channel_by_name(db, req.channel) or get_channel_by_id(db, req.channel)
    if not ch:
        return {"ok": False, "error": "channel_not_found"}

    msg = get_message_by_ts(db, req.timestamp)
    if not msg:
        return {"ok": False, "error": "message_not_found"}

    add_reaction(db, req.timestamp, req.name, BOT_USER_ID)
    return {"ok": True}


@api_router.get("/reactions.get")
async def reactions_get(
    channel: str,
    timestamp: str,
    db: Session = Depends(get_db),
    token: str = Depends(require_auth),
):
    """Gets reactions for an item."""
    ch = get_channel_by_name(db, channel) or get_channel_by_id(db, channel)
    if not ch:
        return {"ok": False, "error": "channel_not_found"}

    msg = get_message_by_ts(db, timestamp)
    if not msg:
        return {"ok": False, "error": "message_not_found"}

    reactions = get_reactions_for_message(db, timestamp)
    grouped: dict = {}
    for r in reactions:
        if r.name not in grouped:
            grouped[r.name] = []
        grouped[r.name].append(r.user_id)

    return {
        "ok": True,
        "type": "message",
        "channel": ch.id,
        "message": {
            **_message_obj(msg, db),
            "reactions": [
                {"name": name, "count": len(users), "users": users}
                for name, users in grouped.items()
            ],
        },
    }


# ─────────────────────────── files.* ─────────────────────────────

@api_router.post("/files.upload")
async def upload_file(
    channels: str = Form(...),
    title: Optional[str] = Form(None),
    initial_comment: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _token: str = Depends(require_auth),
):
    """Uploads or creates a file."""
    logger.info("Uploading file: %s to channels: %s", file.filename, channels)

    content = await file.read()
    file_size = len(content)

    file_obj = create_file(
        db=db,
        name=file.filename,
        title=title,
        mimetype=file.content_type or "application/octet-stream",
        filetype=file.filename.split(".")[-1] if "." in file.filename else "unknown",
        size=file_size,
    )

    if initial_comment:
        for channel_name in [c.strip() for c in channels.split(",")]:
            ch = get_channel_by_name(db, channel_name)
            if ch:
                create_message(db=db, channel_id=ch.id, user="FileUploader",
                               text=f"{initial_comment}\n📎 Uploaded: {file.filename}")

    return {
        "ok": True,
        "file": {
            "id": file_obj.id,
            "name": file_obj.name,
            "title": file_obj.title,
            "mimetype": file_obj.mimetype,
            "filetype": file_obj.filetype,
            "size": file_obj.size,
            "url_private": file_obj.url_private,
            "permalink": file_obj.permalink,
            "timestamp": int(file_obj.created_on.timestamp()),
        },
    }


# ─────────────────────────── health ──────────────────────────────

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "slack-mock"}


# ─────────────────────────── UI routes ───────────────────────────

@ui_router.get("/", response_class=HTMLResponse)
async def ui_home(request: Request, db: Session = Depends(get_db)):
    """Main Slack-like UI."""
    try:
        channels = db.query(Channel).all()
        users = get_all_users(db)

        channel_data = []
        for ch in channels:
            recent = get_messages(db, ch.id, limit=5)
            msg_count = db.query(Message).filter(Message.channel_id == ch.id).count()
            channel_data.append({
                "channel": ch,
                "message_count": msg_count,
                "recent_messages": recent,
            })

        return templates.TemplateResponse("index.html", {
            "request": request,
            "channels": channel_data,
            "users": users,
            "title": "Slack Mock",
            "workspace_name": WORKSPACE_NAME,
        })
    except Exception as e:
        logger.error("Error in ui_home: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@ui_router.get("/channel/{channel_name}", response_class=HTMLResponse)
async def ui_channel_view(request: Request, channel_name: str,
                          db: Session = Depends(get_db)):
    """Channel view — kept for direct deep-links."""
    channel = get_channel_by_name(db, channel_name)
    if not channel:
        raise HTTPException(status_code=404, detail=f"Channel not found: {channel_name}")

    messages = get_messages(db, channel.id, limit=100)
    messages.reverse()

    users = get_all_users(db)
    channels = db.query(Channel).all()
    channel_data = []
    for ch in channels:
        recent = get_messages(db, ch.id, limit=5)
        msg_count = db.query(Message).filter(Message.channel_id == ch.id).count()
        channel_data.append({
            "channel": ch,
            "message_count": msg_count,
            "recent_messages": recent,
        })

    return templates.TemplateResponse("index.html", {
        "request": request,
        "channels": channel_data,
        "active_channel": channel,
        "messages": messages,
        "users": users,
        "title": f"#{channel.name} - Slack Mock",
        "workspace_name": WORKSPACE_NAME,
    })


# ─────────────────────────── helpers ─────────────────────────────

def _channel_obj(c: Channel) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "is_channel": True,
        "is_group": False,
        "is_im": False,
        "is_mpim": False,
        "is_private": c.is_private,
        "created": int(c.created_on.timestamp()),
        "is_archived": False,
        "is_general": c.name == "general",
        "topic": {"value": c.topic or "", "creator": "", "last_set": 0},
        "purpose": {"value": c.purpose or "", "creator": "", "last_set": 0},
        "num_members": 0,
    }


def _message_obj(m: Message, db: Session) -> dict:
    reactions = get_reactions_for_message(db, m.ts)
    grouped: dict = {}
    for r in reactions:
        if r.name not in grouped:
            grouped[r.name] = []
        grouped[r.name].append(r.user_id)

    return {
        "type": "message",
        "user": m.user,
        "text": m.text,
        "ts": m.ts,
        "thread_ts": m.thread_ts,
        "reply_count": 0,
        "team": WORKSPACE_ID,
        "reactions": [
            {"name": name, "count": len(users), "users": users}
            for name, users in grouped.items()
        ],
    }


def _user_obj(u: User) -> dict:
    return {
        "id": u.id,
        "name": u.name,
        "deleted": False,
        "is_bot": u.is_bot,
        "profile": {
            "real_name": u.real_name,
            "display_name": u.display_name,
            "email": u.email,
            "avatar_hash": "",
            "status_text": "",
            "status_emoji": "",
        },
        "team_id": WORKSPACE_ID,
    }
