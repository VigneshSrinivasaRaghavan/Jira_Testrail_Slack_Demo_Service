"""Tests for Slack mock API endpoints."""

import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import app and dependencies
from app import app
from storage import get_db
from models import Base


@pytest.fixture
def test_db():
    """Create a test database."""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    database_url = f"sqlite:///{db_path}"
    
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestingSessionLocal
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Authentication headers for tests."""
    return {"Authorization": "Bearer test-token"}


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "slack-mock"


class TestChatAPI:
    """Test chat API endpoints."""
    
    def test_post_message_success(self, client, auth_headers):
        """Test successful message posting."""
        # First, we need to seed some data
        from storage import SessionLocal
        from models import Channel
        
        db = SessionLocal()
        channel = Channel(id="C1234567890", name="test-channel")
        db.add(channel)
        db.commit()
        db.close()
        
        payload = {
            "channel": "test-channel",
            "text": "Hello, world!",
            "username": "TestUser"
        }
        
        response = client.post("/api/chat.postMessage", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["ok"] is True
        assert data["channel"] == "C1234567890"
        assert "ts" in data
        assert data["message"]["text"] == "Hello, world!"
        assert data["message"]["user"] == "TestUser"
    
    def test_post_message_missing_auth(self, client):
        """Test message posting without authentication."""
        payload = {
            "channel": "test-channel",
            "text": "Hello, world!"
        }
        
        response = client.post("/api/chat.postMessage", json=payload)
        assert response.status_code == 401
    
    def test_post_message_channel_not_found(self, client, auth_headers):
        """Test message posting to non-existent channel."""
        payload = {
            "channel": "non-existent",
            "text": "Hello, world!"
        }
        
        response = client.post("/api/chat.postMessage", json=payload, headers=auth_headers)
        assert response.status_code == 404
    
    def test_post_message_validation_error(self, client, auth_headers):
        """Test message posting with invalid data."""
        payload = {
            "channel": "test-channel"
            # Missing required 'text' field
        }
        
        response = client.post("/api/chat.postMessage", json=payload, headers=auth_headers)
        assert response.status_code == 422


class TestConversationsAPI:
    """Test conversations API endpoints."""
    
    def test_get_conversation_history_success(self, client, auth_headers):
        """Test successful conversation history retrieval."""
        # Seed data
        from storage import SessionLocal
        from models import Channel, Message
        
        db = SessionLocal()
        channel = Channel(id="C1234567890", name="test-channel")
        db.add(channel)
        db.commit()
        
        message = Message(
            ts="1234567890.123456",
            channel_id="C1234567890",
            user="TestUser",
            text="Test message"
        )
        db.add(message)
        db.commit()
        db.close()
        
        response = client.get(
            "/api/conversations.history?channel=test-channel",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["ok"] is True
        assert len(data["messages"]) == 1
        assert data["messages"][0]["text"] == "Test message"
        assert data["messages"][0]["user"] == "TestUser"
    
    def test_get_conversation_history_missing_auth(self, client):
        """Test conversation history without authentication."""
        response = client.get("/api/conversations.history?channel=test-channel")
        assert response.status_code == 401
    
    def test_get_conversation_history_channel_not_found(self, client, auth_headers):
        """Test conversation history for non-existent channel."""
        response = client.get(
            "/api/conversations.history?channel=non-existent",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    def test_get_conversation_history_with_limit(self, client, auth_headers):
        """Test conversation history with limit parameter."""
        # Seed data
        from storage import SessionLocal
        from models import Channel, Message
        
        db = SessionLocal()
        channel = Channel(id="C1234567890", name="test-channel")
        db.add(channel)
        db.commit()
        
        # Add multiple messages
        for i in range(5):
            message = Message(
                ts=f"123456789{i}.123456",
                channel_id="C1234567890",
                user="TestUser",
                text=f"Test message {i}"
            )
            db.add(message)
        
        db.commit()
        db.close()
        
        response = client.get(
            "/api/conversations.history?channel=test-channel&limit=3",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["ok"] is True
        assert len(data["messages"]) == 3


class TestFilesAPI:
    """Test files API endpoints."""
    
    def test_upload_file_success(self, client, auth_headers):
        """Test successful file upload."""
        # Seed channel data
        from storage import SessionLocal
        from models import Channel
        
        db = SessionLocal()
        channel = Channel(id="C1234567890", name="test-channel")
        db.add(channel)
        db.commit()
        db.close()
        
        # Create test file
        test_file_content = b"Test file content"
        
        response = client.post(
            "/api/files.upload",
            headers=auth_headers,
            data={
                "channels": "test-channel",
                "title": "Test File",
                "initial_comment": "Uploading test file"
            },
            files={"file": ("test.txt", test_file_content, "text/plain")}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["ok"] is True
        assert data["file"]["name"] == "test.txt"
        assert data["file"]["title"] == "Test File"
        assert data["file"]["mimetype"] == "text/plain"
        assert data["file"]["size"] == len(test_file_content)
    
    def test_upload_file_missing_auth(self, client):
        """Test file upload without authentication."""
        test_file_content = b"Test file content"
        
        response = client.post(
            "/api/files.upload",
            data={"channels": "test-channel"},
            files={"file": ("test.txt", test_file_content, "text/plain")}
        )
        
        assert response.status_code == 401


class TestUI:
    """Test UI endpoints."""
    
    def test_ui_home(self, client):
        """Test UI home page."""
        response = client.get("/ui/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_ui_channel_view_success(self, client):
        """Test UI channel view."""
        # Seed data
        from storage import SessionLocal
        from models import Channel
        
        db = SessionLocal()
        channel = Channel(id="C1234567890", name="test-channel")
        db.add(channel)
        db.commit()
        db.close()
        
        response = client.get("/ui/channel/test-channel")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_ui_channel_view_not_found(self, client):
        """Test UI channel view for non-existent channel."""
        response = client.get("/ui/channel/non-existent")
        assert response.status_code == 404
    
    def test_root_redirect(self, client):
        """Test root URL redirects to UI."""
        response = client.get("/", allow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/ui"


if __name__ == "__main__":
    pytest.main([__file__])
