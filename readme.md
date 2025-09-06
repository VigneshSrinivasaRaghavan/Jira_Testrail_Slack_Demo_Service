### Mock Services - Jira / TestRail / Slack

Lightweight local mocks for Jira, TestRail and Slack used for teaching/demoing agentic integrations.

- Repo root: run compose / podman from here.
- All services live under `mock-services/`:
  - `mock-services/jira-mock/`
  - `mock-services/testrail-mock/` (TODO)
  - `mock-services/slack-mock/` (TODO)

## Requirements

- Python 3.11+ (for local run)
- `podman` / `podman compose` (recommended if you don't have Docker Desktop)
- `sqlite3` (optional, for local DB inspection)

## 🚀 Quick Start (One-Click Launch)

### 🍎 Mac/Linux Users

**Option 1: Local Development (Recommended)**
```bash
cd mock-services/jira-mock
./start.sh
```

**Option 2: Container (Docker/Podman)**
```bash
cd mock-services/jira-mock
./start-jira.sh
```

**Stop Service:**
```bash
cd mock-services/jira-mock
./stop-jira.sh
```

### 🪟 Windows Users

**Option 1: Local Development (Recommended)**
```cmd
cd mock-services\jira-mock
start.bat
```

**Option 2: Container (Docker Desktop)**
```cmd
cd mock-services\jira-mock
start-jira.bat
```

**Option 3: PowerShell (Alternative)**
```powershell
cd mock-services\jira-mock
.\start-jira.ps1
```

**Stop Service:**
```cmd
cd mock-services\jira-mock
stop-jira.bat
```

## 📋 Manual Setup (If Scripts Don't Work)

### Mac/Linux - Local Development
```bash
cd mock-services/jira-mock
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 4001 --reload
```

### Windows - Local Development
```cmd
cd mock-services\jira-mock
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 4001 --reload
```

### Container (Any OS with Docker/Podman)
```bash
# From repo root
docker compose up -d --build jira-mock
docker compose logs -f jira-mock
docker compose down
```

## Environment

Place optional env at `mock-services/.env` (or repo root) — example values:

```
MOCK_AUTH_REQUIRED=true
ENABLE_RATE_LIMIT=false
JIRA_PROJECT_KEY=QA
TESTRAIL_PROJECT_ID=1
DEFAULT_SLACK_CHANNEL=qa-reports
```

## Jira mock (running on port 4001)

- UI: `GET /ui` — simple index + quick-create form
- Issue detail UI: `GET /ui/issue/{key}`
- Health: `GET /health`

REST API (requires presence of `Authorization: Bearer <token>` header; any token accepted):

- `POST /rest/api/3/issue` — create issue (Jira-style JSON payload under `fields`). Returns 201 with `key`.
- `GET  /rest/api/3/issue/{issue_key}` — get issue
- `GET  /rest/api/3/search?startAt=0&maxResults=50` — list issues
- `POST /ui/create` — quick-create from UI (form)

Admin / maintenance endpoints (auth required):

- `DELETE /rest/api/3/issue/{issue_key}` — delete single issue (204)
- `POST /admin/reset` — remove DB and reseed from `mock-services/shared/seed/sample_issues.json` (returns `{ "status": "reset" }`)

DB and seed

- DB file (local): `mock-services/jira-mock/jira.db`
- Seed JSON: `mock-services/shared/seed/sample_issues.json` — automatically loaded on first startup or after `POST /admin/reset`.

Reset options

- Full reset (fast): stop server, delete DB, restart (reseeds automatically)
  ```bash
  pkill -f uvicorn || true
  rm -f mock-services/jira-mock/jira.db
  # restart server
  source mock-services/jira-mock/.venv/bin/activate
  python -m uvicorn app:app --host 0.0.0.0 --port 4001 --reload
  ```

- From container (Podman) remove volume and restart
  ```bash
  podman compose down
  podman volume rm jira_db
  podman compose up -d --build jira-mock
  ```

- HTTP reset (requires Authorization header):
  ```bash
  curl -X POST -H 'Authorization: Bearer x' http://localhost:4001/admin/reset
  ```

Quick curl examples

```bash
# Health
curl -s http://localhost:4001/health

# Get seeded issue (QA-1)
curl -s -H 'Authorization: Bearer x' http://localhost:4001/rest/api/3/issue/QA-1

# Create via API (JSON)
curl -s -X POST http://localhost:4001/rest/api/3/issue \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer x' \
  -d '{"fields":{"summary":"Test create","description":"from curl","issuetype":{"name":"Bug"}}}'
```

## Where things live

- Jira code: `mock-services/jira-mock/` (`app.py`, `templates/`, `Dockerfile`, `requirements.txt`)
- Shared seeds: `mock-services/shared/seed/`
- Top-level compose: `docker-compose.yml`

## Next steps / TODO

- Implement TestRail mock (`mock-services/testrail-mock/`) on port 4002
- Implement Slack mock (`mock-services/slack-mock/`) on port 4003
- Add Postman collections (optional)

---
Add further details here as we expand the repository; treat this file as the canonical runbook for demos.

