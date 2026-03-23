# Jira Mock Service

A FastAPI-based mock of Atlassian Jira Cloud REST API v3 for AI agent training and integration testing.

---

## Quick Start

### Local (Recommended for development)

```bash
cd mock-services/jira-mock
source .venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 4001 --reload
```

Or use the startup script from the project root:

```bash
./start-all.sh
```

### Docker

```bash
docker compose up -d jira-mock
docker compose logs -f jira-mock
```

### Windows

```cmd
cd mock-services\jira-mock
start.bat
# or
.\start-jira.ps1
```

Service runs at: **http://localhost:4001**

---

## Authentication

All REST API endpoints require a fixed Bearer token:

```
Authorization: Bearer mock-jira-token-2025
```

- Any other token → `401 Unauthorized`
- UI routes (`/ui/*`) do not require auth
- The token is shown prominently in the API docs at `/docs`
- Configurable via env var `JIRA_API_TOKEN`

---

## API Endpoints

### Issues

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/rest/api/3/issue` | Create issue (Story or Bug) |
| `GET` | `/rest/api/3/issue/{key}` | Read issue |
| `PUT` | `/rest/api/3/issue/{key}` | Edit issue (real Jira method) — returns 204 |
| `PATCH` | `/rest/api/3/issue/{key}` | Edit issue (partial) — returns 204 |
| `DELETE` | `/rest/api/3/issue/{key}` | Delete issue — returns 204 |
| `GET` | `/rest/api/3/issue/{key}/transitions` | List available status transitions |
| `POST` | `/rest/api/3/issue/{key}/transitions` | Transition status |
| `GET` | `/rest/api/3/search` | Search / list issues (supports JQL) |

### System & Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check — no auth required |
| `GET` | `/docs` | Swagger UI — interactive API docs |
| `POST` | `/admin/reset` | Wipe DB and restore seed data |

### Web UI

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/ui` | Backlog / issue list |
| `GET` | `/ui/issue/{key}` | Issue detail view |
| `POST` | `/ui/create` | Create issue via form |
| `POST` | `/ui/issue/{key}/edit` | Edit issue via form |
| `POST` | `/ui/issue/{key}/transition` | Status transition via form |
| `POST` | `/ui/issue/{key}/delete` | Delete issue via form |

---

## Story Fields

| API Field | Description |
|-----------|-------------|
| `customfield_10016` | Story Points (integer) |
| `customfield_10020` | Sprint (string or sprint object) |
| `customfield_10014` | Epic Link (parent issue key) |

## Bug Fields

| API Field | Description |
|-----------|-------------|
| `environment` | Environment where bug occurs (plain text or ADF doc) |
| `fixVersions` | Array of `{"name": "..."}` version objects |
| `duedate` | ISO date string `YYYY-MM-DD` |

---

## Create Issue – Examples

### Story

```bash
curl -X POST http://localhost:4001/rest/api/3/issue \
  -H "Authorization: Bearer mock-jira-token-2025" \
  -H "Content-Type: application/json" \
  -d '{
    "fields": {
      "project": {"key": "QA"},
      "summary": "User can log in with valid credentials",
      "description": "As a user I want to log in.\n\nACCEPTANCE CRITERIA\nAC1 - Valid login redirects to dashboard.",
      "issuetype": {"name": "Story"},
      "priority": {"name": "High"},
      "assignee": "jane.smith",
      "customfield_10016": 5,
      "customfield_10020": "Sprint 1"
    }
  }'
```

### Bug

```bash
curl -X POST http://localhost:4001/rest/api/3/issue \
  -H "Authorization: Bearer mock-jira-token-2025" \
  -H "Content-Type: application/json" \
  -d '{
    "fields": {
      "project": {"key": "QA"},
      "summary": "Login button unresponsive in Safari",
      "description": "First tap on Login does nothing in Safari 17.",
      "issuetype": {"name": "Bug"},
      "priority": {"name": "Critical"},
      "environment": "Production – Safari 17, iOS 17.4",
      "fixVersions": [{"name": "v1.3.1"}],
      "duedate": "2025-10-31"
    }
  }'
```

### Read Issue

```bash
curl http://localhost:4001/rest/api/3/issue/QA-1 \
  -H "Authorization: Bearer mock-jira-token-2025"
```

### Edit Issue (PUT)

```bash
curl -X PUT http://localhost:4001/rest/api/3/issue/QA-1 \
  -H "Authorization: Bearer mock-jira-token-2025" \
  -H "Content-Type: application/json" \
  -d '{"fields": {"priority": {"name": "Critical"}, "customfield_10016": 8}}'
```

### Transition Status

```bash
# Get available transitions
curl http://localhost:4001/rest/api/3/issue/QA-1/transitions \
  -H "Authorization: Bearer mock-jira-token-2025"

# Move to In Progress (id=2) / Done (id=3) / To Do (id=1)
curl -X POST http://localhost:4001/rest/api/3/issue/QA-1/transitions \
  -H "Authorization: Bearer mock-jira-token-2025" \
  -H "Content-Type: application/json" \
  -d '{"transition": {"id": "2"}}'
```

### Search with JQL

```bash
# All issues
curl "http://localhost:4001/rest/api/3/search" \
  -H "Authorization: Bearer mock-jira-token-2025"

# Stories only
curl "http://localhost:4001/rest/api/3/search?jql=issuetype=Story" \
  -H "Authorization: Bearer mock-jira-token-2025"

# Bugs in progress
curl "http://localhost:4001/rest/api/3/search?jql=issuetype=Bug" \
  -H "Authorization: Bearer mock-jira-token-2025"
```

---

## Description Format (ADF)

Real Jira Cloud uses **Atlassian Document Format (ADF)** for `description` and `environment`.

The mock accepts both plain strings and ADF objects as input. Responses always return ADF format:

```json
{
  "type": "doc",
  "version": 1,
  "content": [
    {
      "type": "paragraph",
      "content": [{"type": "text", "text": "Your description text here"}]
    }
  ]
}
```

---

## Status Transitions

| Transition ID | Target Status | From |
|---------------|---------------|------|
| `1` | To Do | In Progress, Done |
| `2` | In Progress | To Do, Done |
| `3` | Done | In Progress |

---

## JQL Search Support

| JQL Expression | Example |
|----------------|---------|
| `issuetype = Story` | `?jql=issuetype=Story` |
| `issuetype = Bug` | `?jql=issuetype=Bug` |
| `status = "In Progress"` | `?jql=status="In Progress"` |
| `status = Done` | `?jql=status=Done` |

---

## Seed Data

On first start (or after `POST /admin/reset`), the DB loads 7 sample issues:

| Key | Type | Summary | Status |
|-----|------|---------|--------|
| QA-1 | Story | Login Page Workflow for OrangeHRM | To Do |
| QA-2 | Story | Logout Workflow for OrangeHRM | In Progress |
| QA-3 | Story | Dashboard Navigation | To Do |
| QA-4 | Bug | Login fails with valid credentials on first attempt | To Do |
| QA-5 | Bug | Forgot Password link does not send reset email | In Progress |
| QA-6 | Bug | Search Employee returns no results for partial matches | Done |
| QA-7 | Story | Add New Employee – Full workflow validation | Done |

---

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `JIRA_API_TOKEN` | `mock-jira-token-2025` | The only accepted Bearer token |
| `JIRA_PROJECT_KEY` | `QA` | Project key prefix for issue keys |
| `JIRA_PROJECT_NAME` | `QA Project` | Project display name |

---

## Postman Collection

Located in the project root `postman-collections/` folder:

```
postman-collections/
├── Jira_Mock_v2.postman_collection.json      ← 25 requests, 6 folders
└── Jira_Mock_v2.postman_environment.json     ← Pre-configured with token
```

See `POSTMAN_COLLECTION_README.md` for import and usage instructions.

---

## Project Structure

```
jira-mock/
├── app.py                        # FastAPI app — all routes, DB schema, auth
├── templates/
│   ├── base.html                 # Shared layout (nav, sidebar, create modal)
│   ├── index.html                # Backlog / issue list view
│   └── issue_detail.html         # Issue detail with edit/transition/delete
├── static/
│   ├── style.css                 # Jira-like design system
│   └── main.js                   # Modal, type toggling, keyboard shortcuts
├── seed/
│   └── sample_issues.json        # 7 seed issues (Stories + Bugs)
├── Dockerfile
├── requirements.txt
├── start.sh / start.bat
├── README.md                     # This file
└── POSTMAN_COLLECTION_README.md  # Postman import guide
```

---

## Database Management

```bash
# Reset via API
curl -X POST http://localhost:4001/admin/reset \
  -H "Authorization: Bearer mock-jira-token-2025"

# Inspect SQLite directly
sqlite3 mock-services/jira-mock/jira.db "SELECT key, issue_type, status, summary FROM issues;"

# Delete DB file (service will recreate + reseed on next start)
rm mock-services/jira-mock/jira.db
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `401 Unauthorized` | Use `Authorization: Bearer mock-jira-token-2025` exactly |
| `404 Not Found` | Check the issue key exists — run `GET /rest/api/3/search` to list all |
| Port 4001 in use | `kill $(lsof -ti :4001)` then restart |
| DB schema errors | Delete `jira.db` — it recreates on startup |
| Template errors | Check `logs/jira-mock.log` for the Jinja2 traceback |

```bash
# View live logs
tail -f logs/jira-mock.log
```
