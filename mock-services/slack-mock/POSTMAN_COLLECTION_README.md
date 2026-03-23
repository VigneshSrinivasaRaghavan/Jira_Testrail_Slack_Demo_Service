# Slack Mock API – Postman Collection Guide

The Postman collection and environment for this service live in the shared `postman-collections/` folder at the project root:

```
postman-collections/
├── Slack_Mock.postman_collection.json       ← import this
└── Slack_Mock.postman_environment.json      ← import this
```

---

## Quick Setup

1. Open Postman
2. Click **Import** → select both files above
3. Select **Slack Mock – Local** from the environment dropdown (top-right)
4. Make sure the service is running on `http://localhost:4003`
5. Run **Health Check** to confirm it's up, then start testing

---

## 🔑 Authentication

Every API request requires this header:

```
Authorization: Bearer xoxb-mock-bot-token
```

This is pre-configured in the environment (`api_token` variable). The collection's auth is set to **Bearer Token → `{{api_token}}`** so all requests inherit it automatically — no manual setup needed per request.

**Accepted token formats** (same rules as real Slack):

| Format | Example |
|--------|---------|
| Bot token | `xoxb-mock-bot-token` ← **use this** |
| Any `xoxb-*` | `xoxb-anything-works` |
| Any `xoxp-*` | `xoxp-user-token` |
| Dev shortcuts | `demo-token`, `test-token` |

**Error responses when auth fails:**

```json
{ "ok": false, "error": "not_authed" }    // no token sent
{ "ok": false, "error": "invalid_auth" }  // unrecognised token format
```

---

## Environment Variables

| Variable | Default Value | Auto-Updated By |
|----------|---------------|-----------------|
| `base_url` | `http://localhost:4003` | — |
| `api_token` | `xoxb-mock-bot-token` | — |
| `channel_name` | `qa-reports` | Create Channel |
| `channel_id` | `C1234567890` | List Channels, Create Channel |
| `message_ts` | _(empty)_ | Send Message, Get Channel History |
| `user_id` | `U1111111111` | List Users |

---

## Collection Structure (17 requests)

### System
| Request | Method | Endpoint |
|---------|--------|----------|
| Health Check | GET | `/health` |
| Auth Test | GET | `/api/auth.test` |

### Conversations
| Request | Method | Endpoint |
|---------|--------|----------|
| List Channels | GET | `/api/conversations.list` |
| Get Channel Info | GET | `/api/conversations.info` |
| Create Channel | POST | `/api/conversations.create` |
| Get Channel History | GET | `/api/conversations.history` |
| Get Channel Members | GET | `/api/conversations.members` |
| Get Thread Replies | GET | `/api/conversations.replies` |

### Chat
| Request | Method | Endpoint |
|---------|--------|----------|
| Send Message | POST | `/api/chat.postMessage` |
| Update Message | POST | `/api/chat.update` |
| Delete Message | POST | `/api/chat.delete` |
| Send Message – Reply (thread) | POST | `/api/chat.postMessage` |

### Users
| Request | Method | Endpoint |
|---------|--------|----------|
| List Users | GET | `/api/users.list` |
| Get User Info | GET | `/api/users.info` |

### Reactions
| Request | Method | Endpoint |
|---------|--------|----------|
| Add Reaction | POST | `/api/reactions.add` |
| Get Reactions | GET | `/api/reactions.get` |

### Files
| Request | Method | Endpoint |
|---------|--------|----------|
| Upload File | POST | `/api/files.upload` |

---

## Recommended Run Order

Run the requests in this order to ensure variables are populated before they are needed:

1. **Health Check** — confirm service is up
2. **Auth Test** — confirm token is accepted
3. **List Channels** → saves `{{channel_id}}`
4. **Send Message** → saves `{{message_ts}}`
5. **Get Channel History** → confirms message is there
6. **Update Message** → edits the sent message
7. **Add Reaction** → adds 👍 to the message
8. **Get Reactions** → confirms reaction is recorded
9. **Send Message – Reply** → replies in the thread
10. **Get Thread Replies** → retrieves the thread
11. **List Users** → saves `{{user_id}}`
12. **Get User Info** → retrieves user details
13. **Delete Message** → cleans up (clears `{{message_ts}}`)
14. **Create Channel** → creates a new channel

---

## Send a Message – Quick Example

**Request:**
```
POST http://localhost:4003/api/chat.postMessage
Authorization: Bearer xoxb-mock-bot-token
Content-Type: application/json
```
```json
{
  "channel": "qa-reports",
  "text": "This is test message from API",
  "username": "MockBot"
}
```

**Response:**
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

## Running with Newman (CLI)

```bash
newman run ../../postman-collections/Slack_Mock.postman_collection.json \
  -e ../../postman-collections/Slack_Mock.postman_environment.json \
  --reporters cli,json \
  --reporter-json-export results.json
```
