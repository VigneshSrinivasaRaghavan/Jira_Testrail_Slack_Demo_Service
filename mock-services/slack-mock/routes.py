"""API routes for Slack mock service."""

import os
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from storage import get_db, get_channel_by_name, get_channel_by_id, create_message, get_messages, create_file
from models import Channel, Message

# Setup logging
logger = logging.getLogger(__name__)

# Templates
templates = Jinja2Templates(directory="templates")

# Routers
api_router = APIRouter(prefix="/api")
ui_router = APIRouter(prefix="/ui")


# Pydantic models for API requests/responses
class PostMessageRequest(BaseModel):
    channel: str = Field(..., description="Channel name or ID")
    text: str = Field(..., description="Message text")
    username: Optional[str] = Field("SlackBot", description="Username posting the message")
    thread_ts: Optional[str] = Field(None, description="Thread timestamp for replies")


class PostMessageResponse(BaseModel):
    ok: bool
    channel: str
    ts: str
    message: dict


class ConversationHistoryResponse(BaseModel):
    ok: bool
    messages: List[dict]
    has_more: bool
    pin_count: int = 0
    response_metadata: dict


class FileUploadResponse(BaseModel):
    ok: bool
    file: dict


async def require_auth(request: Request):
    """Simple auth check - just require any Bearer token."""
    auth_required = os.getenv("MOCK_AUTH_REQUIRED", "true").lower() == "true"
    
    if not auth_required:
        return True
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    return True


# API Routes
@api_router.post("/chat.postMessage", response_model=PostMessageResponse)
async def post_message(
    request: PostMessageRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """Post a message to a Slack channel."""
    try:
        logger.info("Posting message to channel: %s", request.channel)
        
        # Find channel by name or ID
        channel = get_channel_by_name(db, request.channel) or get_channel_by_id(db, request.channel)
        
        if not channel:
            raise HTTPException(status_code=404, detail=f"Channel not found: {request.channel}")
        
        # Create message
        message = create_message(
            db=db,
            channel_id=channel.id,
            user=request.username,
            text=request.text,
            thread_ts=request.thread_ts
        )
        
        return PostMessageResponse(
            ok=True,
            channel=channel.id,
            ts=message.ts,
            message={
                "type": "message",
                "user": message.user,
                "text": message.text,
                "ts": message.ts,
                "thread_ts": message.thread_ts
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in post_message: %s", e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@api_router.get("/conversations.history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    channel: str,
    limit: int = 50,
    oldest: Optional[str] = None,
    latest: Optional[str] = None,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """Get conversation history for a channel."""
    try:
        logger.info("Getting history for channel: %s", channel)
        
        # Find channel by name or ID
        channel_obj = get_channel_by_name(db, channel) or get_channel_by_id(db, channel)
        
        if not channel_obj:
            raise HTTPException(status_code=404, detail=f"Channel not found: {channel}")
        
        # Get messages
        messages = get_messages(db, channel_obj.id, limit, oldest, latest)
        
        # Format messages for Slack API response
        formatted_messages = []
        for msg in reversed(messages):  # Slack returns oldest first
            formatted_messages.append({
                "type": "message",
                "user": msg.user,
                "text": msg.text,
                "ts": msg.ts,
                "thread_ts": msg.thread_ts
            })
        
        return ConversationHistoryResponse(
            ok=True,
            messages=formatted_messages,
            has_more=len(messages) == limit,
            response_metadata={
                "next_cursor": messages[-1].ts if messages and len(messages) == limit else ""
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in get_conversation_history: %s", e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@api_router.post("/files.upload", response_model=FileUploadResponse)
async def upload_file(
    channels: str = Form(...),
    title: Optional[str] = Form(None),
    initial_comment: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """Upload a file to Slack."""
    logger.info("Uploading file: %s to channels: %s", file.filename, channels)
    
    # Read file content to get size
    content = await file.read()
    file_size = len(content)
    
    # Create file record
    file_obj = create_file(
        db=db,
        name=file.filename,
        title=title,
        mimetype=file.content_type or "application/octet-stream",
        filetype=file.filename.split('.')[-1] if '.' in file.filename else "unknown",
        size=file_size
    )
    
    # If there's an initial comment, post it as a message
    if initial_comment:
        channel_names = [c.strip() for c in channels.split(',')]
        for channel_name in channel_names:
            channel = get_channel_by_name(db, channel_name)
            if channel:
                create_message(
                    db=db,
                    channel_id=channel.id,
                    user="FileUploader",
                    text=f"{initial_comment}\n📎 Uploaded: {file.filename}"
                )
    
    return FileUploadResponse(
        ok=True,
        file={
            "id": file_obj.id,
            "name": file_obj.name,
            "title": file_obj.title,
            "mimetype": file_obj.mimetype,
            "filetype": file_obj.filetype,
            "size": file_obj.size,
            "url_private": file_obj.url_private,
            "permalink": file_obj.permalink,
            "timestamp": int(file_obj.created_on.timestamp())
        }
    )


# UI Routes
@ui_router.get("/", response_class=HTMLResponse)
async def ui_home(request: Request, db: Session = Depends(get_db)):
    """Main UI page showing channels."""
    try:
        channels = db.query(Channel).all()
        
        # Get recent messages for each channel
        channel_data = []
        for channel in channels:
            recent_messages = get_messages(db, channel.id, limit=5)
            message_count = db.query(Message).filter(Message.channel_id == channel.id).count()
            channel_data.append({
                "channel": channel,
                "message_count": message_count,
                "recent_messages": recent_messages
            })
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "channels": channel_data,
            "title": "Slack Mock - Channels"
        })
    except Exception as e:
        logger.error("Error in ui_home: %s", e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@ui_router.get("/channel/{channel_name}", response_class=HTMLResponse)
async def ui_channel_view(request: Request, channel_name: str, db: Session = Depends(get_db)):
    """Channel view showing messages."""
    try:
        channel = get_channel_by_name(db, channel_name)
        
        if not channel:
            raise HTTPException(status_code=404, detail=f"Channel not found: {channel_name}")
        
        messages = get_messages(db, channel.id, limit=100)
        messages.reverse()  # Show oldest first in UI
        
        return templates.TemplateResponse("channel_view.html", {
            "request": request,
            "channel": channel,
            "messages": messages,
            "title": f"#{channel.name} - Slack Mock"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in ui_channel_view: %s", e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


# Health check
@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "slack-mock"}
