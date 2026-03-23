# Jira Mock API – Postman Collection

## Files

The Postman collection has moved to the shared `postman-collections/` folder at the project root:

```
postman-collections/
├── Jira_Mock_v2.postman_collection.json      ← Import this
└── Jira_Mock_v2.postman_environment.json     ← Import this too
```

---

## Quick Start

### 1. Import into Postman

1. Open Postman
2. Click **Import**
3. Import both files from `postman-collections/`:
   - `Jira_Mock_v2.postman_collection.json`
   - `Jira_Mock_v2.postman_environment.json`

### 2. Select the Environment

Top-right dropdown → select **"Jira Mock – Local"**

### 3. Start the Service

```bash
# From project root
./start-all.sh

# Or just Jira mock
cd mock-services/jira-mock
source .venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 4001
```

### 4. Run Health Check

Hit **System → Health Check** first to confirm the service is up.

---

## Authentication

Every API request requires this exact Bearer token:

```
Authorization: Bearer mock-jira-token-2025
```

The environment file already has this configured in the `api_token` variable — no manual setup needed.
Any other token returns `401 Unauthorized`.

> Get the token from: **http://localhost:4001/docs** — it's shown at the top of the page.

---

## Collection Structure (25 requests)

| Folder | Requests |
|--------|----------|
| **System** | Health Check |
| **Story** | Create, Read, Edit (PUT), Edit (PATCH), Get Transitions, → In Progress, → Done, Delete |
| **Bug** | Create, Read, Edit (PUT), Edit (PATCH), → In Progress, → Done, Delete |
| **Search (JQL)** | All Issues, Stories Only, Bugs Only, In Progress, Done |
| **Error Cases** | 401 No Token, 401 Wrong Token, 404 Not Found |
| **Admin** | Reset Database |

---

## Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `base_url` | `http://localhost:4001` | Jira Mock base URL |
| `api_token` | `mock-jira-token-2025` | Fixed Bearer token |
| `issue_key` | `QA-1` | Used in Read / Edit / Delete / Transition — auto-updated by Create |
| `created_story_key` | *(auto-set)* | Key of the last created Story |
| `created_bug_key` | *(auto-set)* | Key of the last created Bug |
| `transition_id` | *(auto-set)* | First available transition ID from Get Transitions |

---

## Workflow Tips

**Create then operate:** Run **Create Story** or **Create Bug** first — the test script auto-saves the new key into `{{issue_key}}`. Read, Edit, Transition, and Delete will then use it automatically.

**Reset between sessions:** Run **Admin → Reset Database** to wipe all test data and restore the 7 seed issues (QA-1 through QA-7).

**Run as a suite:** Use Postman's **Collection Runner** (▶ Run) to execute all 25 requests in sequence and see pass/fail counts per test assertion.
