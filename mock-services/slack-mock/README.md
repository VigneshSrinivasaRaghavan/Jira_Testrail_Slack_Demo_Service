# Slack Mock Service

A FastAPI-based mock service that replicates the Slack Web API for training, testing, and local development. All responses follow the exact Slack API format (`{"ok": true, ...}`).

---

## Features

- **15 API endpoints** matching real Slack's Web API surface
- **Slack-style Bearer token auth** (`xoxb-*` / `xoxp-*` tokens)
- **Real-time UI** — Slack-like 3-column layout with auto-polling (4s)
- **Channel management** — list, create, view history, members, threads
- **Reactions** — add and retrieve emoji reactions on messages
- **File upload** simulation
- **Swagger docs** at `/docs` with pre-filled auth token
- **SQLite** persistence with seed data

---

## Quick Start

### Local (Python)

```bash
cd mock-services/slack-mock
pip install -r requirements.txt
python app.py
```

### Docker Compose

```bash
# From project root
docker compose up -d slack-mock
docker compose logs -f slack-mock
```

Service runs on **http://localhost:4003**

---

## 🔑 Authentication

Every API call requires a Bearer token in the `Authorization` header.

```
Authorization: Bearer xoxb-mock-bot-token
```

Accepted token formats:

| Format | Example |
|--------|---------|
| Bot token (`xoxb-*`) | `xoxb-mock-bot-token` ← **use this** |
| User token (`xoxp-*`) | `xoxp-any-value` |
| Dev shortcuts | `demo-token`, `test-token` |

**Auth error responses** (HTTP 200, matching real Slack):
```json
{ "ok": false, "error": "not_authed" }    // missing token
{ "ok": false, "error": "invalid_auth" }  // unrecognised format
```

---

## API Endpoints

### System

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/health` | No | Service health check |
| `GET` | `/api/api.test` | No | API connectivity test |
| `GET/POST` | `/api/auth.test` | Yes | Validate token, return workspace info |

### Chat

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/chat.postMessage` | Yes | **Send a message to a channel** |
| `POST` | `/api/chat.update` | Yes | Edit an existing message |
| `POST` | `/api/chat.delete` | Yes | Delete a message |

### Conversations

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/conversations.list` | Yes | List all channels |
| `GET` | `/api/conversations.info` | Yes | Get channel details |
| `POST` | `/api/conversations.create` | Yes | Create a new channel |
| `GET` | `/api/conversations.history` | Yes | Get channel message history |
| `GET` | `/api/conversations.members` | Yes | List channel members |
| `GET` | `/api/conversations.replies` | Yes | Get thread replies |

### Users

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/users.list` | Yes | List all users |
| `GET` | `/api/users.info` | Yes | Get a specific user |

### Reactions & Files

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/reactions.add` | Yes | Add emoji reaction to a message |
| `GET` | `/api/reactions.get` | Yes | Get reactions on a message |
| `POST` | `/api/files.upload` | Yes | Upload a file to a channel |

### Web UI & Docs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/ui` | Slack-like channel list |
| `GET` | `/ui/channel/{name}` | Channel view with messages |
| `GET` | `/docs` | Swagger UI (with pre-filled auth) |
| `GET` | `/redoc` | ReDoc API documentation |

---

## Usage Examples

### Send a Message

```bash
curl -X POST "http://localhost:4003/api/chat.postMessage" \
  -H "Authorization: Bearer xoxb-mock-bot-token" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "qa-reports",
    "text": "This is test message from API",
    "username": "MockBot"
  }'
```

Response:
```json
{
  "ok": true,
  "channel": "C1234567890",
  "ts": "1774296066.063248",
  "message": {
    "type": "message",
    "text": "This is test message from API",
    "user": "MockBot",
    "ts": "1774296066.063248",
    "team": "T0MOCKTEAM1"
  }
}
```

### List Channels

```bash
curl "http://localhost:4003/api/conversations.list" \
  -H "Authorization: Bearer xoxb-mock-bot-token"
```

### Get Channel History

```bash
curl "http://localhost:4003/api/conversations.history?channel=qa-reports&limit=50" \
  -H "Authorization: Bearer xoxb-mock-bot-token"
```

### Auth Test

```bash
curl "http://localhost:4003/api/auth.test" \
  -H "Authorization: Bearer xoxb-mock-bot-token"
```

---

## Postman Collection

Import the collection from the shared `postman-collections/` folder at the project root:

```
postman-collections/
├── Slack_Mock.postman_collection.json       ← 17 requests, 6 folders
└── Slack_Mock.postman_environment.json      ← pre-filled token + variables
```

See [`POSTMAN_COLLECTION_README.md`](./POSTMAN_COLLECTION_README.md) for setup and run order.

---

## Seed Data

| Type | Name | ID |
|------|------|----|
| Channel | `#qa-reports` | `C1234567890` |
| Channel | `#general` | `C0987654321` |
| Channel | `#dev-alerts` | `C1122334455` |
| User | `alice` | `U1111111111` |
| User | `bob` | `U2222222222` |
| User | `charlie` | `U3333333333` |

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `4003` | Server port |
| `HOST` | `0.0.0.0` | Server host |
| `MOCK_AUTH_REQUIRED` | `true` | Set to `false` to bypass auth |
| `DATABASE_URL` | `sqlite:///./slack_mock.db` | Database connection |

---

## Project Structure

```
slack-mock/
├── app.py                    # FastAPI app, middleware, OpenAPI schema
├── routes.py                 # All API + UI route handlers
├── models.py                 # SQLAlchemy models (Channel, Message, User, Reaction, ...)
├── storage.py                # Database CRUD operations + seed data
├── templates/
│   ├── index.html            # Slack-like SPA (sidebar + chat + polling)
│   └── channel_view.html     # Channel deep-link redirect
├── tests/
│   ├── test_api.py           # Unit tests
│   └── test_comprehensive.py # End-to-end smoke tests
├── requirements.txt
├── Dockerfile
├── README.md                 # This file
└── POSTMAN_COLLECTION_README.md
```

---

## Running Tests

```bash
cd mock-services/slack-mock

# Quick smoke test (requires service running on :4003)
python test_comprehensive.py

# Unit tests
pytest tests/ -v
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Port already in use | Change `PORT` env var or kill existing process: `lsof -ti :4003 \| xargs kill` |
| Database locked | Stop all instances, delete `slack_mock.db`, restart |
| `{"ok": false, "error": "invalid_auth"}` | Use `xoxb-mock-bot-token` or any `xoxb-*` / `xoxp-*` token |
| Channel not found | Use seed channel names: `qa-reports`, `general`, `dev-alerts` |

---

## API Mapping to Real Slack

| Mock Endpoint | Real Slack API | Notes |
|---------------|----------------|-------|
| `POST /api/chat.postMessage` | `chat.postMessage` | Full request/response parity |
| `GET /api/conversations.list` | `conversations.list` | Pagination cursor supported |
| `GET /api/conversations.history` | `conversations.history` | oldest/latest filters work |
| `GET /api/conversations.members` | `conversations.members` | Returns user ID array |
| `GET /api/conversations.replies` | `conversations.replies` | Thread support |
| `POST /api/conversations.create` | `conversations.create` | Public + private |
| `GET /api/auth.test` | `auth.test` | Returns workspace/user info |
| `GET /api/users.list` | `users.list` | Returns members array |
| `GET /api/users.info` | `users.info` | Full profile object |
| `POST /api/reactions.add` | `reactions.add` | Emoji reactions on messages |
| `GET /api/reactions.get` | `reactions.get` | Grouped by emoji name |
| `POST /api/files.upload` | `files.upload` | File storage simulated |
