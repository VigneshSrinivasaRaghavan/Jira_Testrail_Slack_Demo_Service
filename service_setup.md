**Goal:**

Create **three local mock services** that simulate **Jira**, **TestRail**, and **Slack** APIs + a super simple web UI for each, so I can demo Agentic AI integrations *without* real credentials. I should be able to run all three with **Docker Compose**, and switch between “mock” and “real” in my agent via config.

**Tech choices (use these defaults):**

* Backend: **FastAPI (Python 3.11)**
* Storage: **SQLite** (via SQLAlchemy)
* Templates: **Jinja2** for ultra-simple UIs
* Docs: Built-in **OpenAPI/Swagger** from FastAPI
* Containerization: **Docker** + **docker-compose**
* Ports: Jira mock `4001`, TestRail mock `4002`, Slack mock `4003`
* Lint/format: ruff + black
* Tests: pytest (basic happy-path tests for core endpoints)

**Repo structure:**

```
mock-services/
  docker-compose.yml
  .env.example
  README.md
  shared/
    seed/
      sample_issues.json
      sample_testcases.json
      sample_messages.json
    schemas/
      jira.py
      testrail.py
      slack.py
  jira-mock/
    app.py
    models.py
    routes.py
    storage.py
    templates/
      index.html
      issue_detail.html
    static/
    Dockerfile
    requirements.txt
    tests/
  testrail-mock/
    app.py
    models.py
    routes.py
    storage.py
    templates/
      index.html
      testcase_detail.html
    static/
    Dockerfile
    requirements.txt
    tests/
  slack-mock/
    app.py
    models.py
    routes.py
    storage.py
    templates/
      index.html
      channel_view.html
    static/
    Dockerfile
    requirements.txt
    tests/
  postman/
    Mock-Jira.postman_collection.json
    Mock-TestRail.postman_collection.json
    Mock-Slack.postman_collection.json
```

---

### 1) Jira Mock (localhost:4001)

**Purpose:** Mimic a subset of Atlassian Jira Cloud REST v3 to support: create issue, attach file, list issues, get issue.

**Endpoints:**

* `POST /rest/api/3/issue`
* `GET /rest/api/3/issue/{issueIdOrKey}`
* `POST /rest/api/3/issue/{issueIdOrKey}/attachments`
* `GET /ui` → issue list
* `GET /ui/issue/{key}` → issue details

**Auth:** Any `Authorization: Bearer <token>` header required.

**Data:** SQLite tables: `issues`, `attachments`. Keys like `QA-1`, `QA-2`.

---

### 2) TestRail Mock (localhost:4002)

**Purpose:** Mimic core TestRail APIs for creating test cases and adding results.

**Endpoints (simplified from real TestRail):**

* `POST /index.php?/api/v2/add_case/{section_id}`

  * Req: `{ "title": "Login should succeed with valid credentials", "template_id": 1, "type_id": 1, "priority_id": 2 }`
  * Res: `{ "id": 101, "title": "...", "section_id": 1, "created_on": "..." }`
* `POST /index.php?/api/v2/add_result/{case_id}`

  * Req: `{ "status_id": 1, "comment": "Executed via agent" }`
  * Res: `{ "id": 201, "case_id": 101, "status_id": 1, "comment": "..." }`
* `GET /index.php?/api/v2/get_case/{case_id}`
* `GET /ui`

  * Show list of test cases (ID, Title, Status, Updated).
* `GET /ui/case/{id}`

  * Show details + execution history.

**Auth:** Same Bearer header presence rule.

**Data:** SQLite tables:

* `cases` (id, section\_id, title, template\_id, type\_id, priority\_id, created\_on, updated\_on).
* `results` (id, case\_id, status\_id, comment, created\_on).

---

### 3) Slack Mock (localhost:4003)

**Purpose:** Mimic `chat.postMessage` and channel history.

**Endpoints:**

* `POST /api/chat.postMessage`
* `GET /api/conversations.history?channel=qa-reports`
* `GET /ui` → channel view

(Nice-to-have) `POST /api/files.upload`

**Auth:** Same Bearer rule.

**Data:** SQLite tables: `channels`, `messages`, `files`.

---

### 4) Cross-cutting features

* Swagger docs at `/docs` & `/redoc`
* CORS enabled
* Seed data from `shared/seed/*.json`
* Log every request
* Pydantic validation
* Pagination (`?startAt=0&maxResults=50` for Jira, `?limit=50` for Slack/TestRail)
* Optional rate-limit simulation
* `.env` example:

```
MOCK_AUTH_REQUIRED=true
ENABLE_RATE_LIMIT=false
JIRA_PROJECT_KEY=QA
TESTRAIL_PROJECT_ID=1
DEFAULT_SLACK_CHANNEL=qa-reports
```

---

### 5) Docker & local run

* `docker compose up -d --build` runs all three
* Healthchecks per service
* Persistent volumes for SQLite

**Make targets:** up, down, logs, test

---

### 6) Postman collections

Generate collections for Jira, TestRail, Slack with sample requests.

---

### 7) Tests

pytest per service:

* happy path create/read/update
* missing auth → 401
* validation error → 400
* unknown → 404

---

### 8) Acceptance criteria

* `docker compose up -d --build` runs all 3 services
* Visit:

  * Jira UI → `http://localhost:4001/ui`
  * TestRail UI → `http://localhost:4002/ui`
  * Slack UI → `http://localhost:4003/ui`
* Swagger docs at `/docs`
* POSTs reflect in UI
* Code clean, formatted, short docstrings

---

### 9) Bonus

* Quick-create forms in UI pages
* `/health` endpoint
* Inline docs mapping mock → real API fields

---

**Deliverables:**

* Full code per structure, ready to run
* README.md with usage + mapping
* Postman collections
* Basic pytest tests

---

**If anything is unclear, assume simplest working version and proceed.**

---