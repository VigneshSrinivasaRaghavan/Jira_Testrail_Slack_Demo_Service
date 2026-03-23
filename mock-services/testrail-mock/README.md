# TestRail Mock Service

A FastAPI-based mock that implements the real **TestRail API v2** endpoint patterns for integration testing and student training.

---

## Features

- Full TestRail API v2 URL pattern: `GET /index.php?/api/v2/get_case/{id}`
- Fixed single-credential auth matching real TestRail Basic Auth
- CRUD for Projects, Sections, Test Cases, Test Runs, Test Results
- Paginated list responses (`offset`, `limit`, `_links`)
- Web UI at `/ui` mimicking the TestRail interface
- Interactive API docs at `/docs` (Swagger UI with Authorize button)
- SQLite persistence — data survives restarts

---

## Quick Start

### Local

```bash
cd mock-services/testrail-mock
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 4002 --reload
```

### Docker Compose

```bash
# From project root
docker compose up -d testrail-mock
docker compose logs -f testrail-mock
```

---

## Authentication

This mock uses the **exact same auth as real TestRail**: HTTP Basic Auth with your email as the username and your API key as the password.

| Field | Value |
|-------|-------|
| **Email** | `admin@testrail.mock` |
| **API Key** | `MockAPI@123` |
| **Header** | `Authorization: Basic YWRtaW5AdGVzdHJhaWwubW9jazpNb2NrQVBJQDEyMw==` |

> Only these exact credentials are accepted. See `/docs` for the interactive Authorize button.

Bearer token shortcut also works: `Authorization: Bearer MockAPI@123`

Override credentials via environment variables:
```
TESTRAIL_MOCK_EMAIL=admin@testrail.mock
TESTRAIL_MOCK_API_KEY=MockAPI@123
```

---

## API Endpoints

All endpoints support both the real TestRail URL pattern (`index.php?/api/v2/`) and the clean REST path (`/api/v2/`).

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/index.php?/api/v2/get_projects` | List all projects |
| `GET` | `/index.php?/api/v2/get_project/{project_id}` | Get project |
| `POST` | `/index.php?/api/v2/add_project` | Create project |
| `POST` | `/index.php?/api/v2/update_project/{project_id}` | Update project |
| `POST` | `/index.php?/api/v2/delete_project/{project_id}` | Delete project |

### Sections

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/index.php?/api/v2/get_sections/{project_id}` | List sections |
| `GET` | `/index.php?/api/v2/get_section/{section_id}` | Get section |
| `POST` | `/index.php?/api/v2/add_section/{project_id}` | Create section |
| `POST` | `/index.php?/api/v2/update_section/{section_id}` | Update section |
| `POST` | `/index.php?/api/v2/delete_section/{section_id}` | Delete section |

### Test Cases

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/index.php?/api/v2/get_cases/{project_id}` | List cases (paginated) |
| `GET` | `/index.php?/api/v2/get_case/{case_id}` | Get case |
| `POST` | `/index.php?/api/v2/add_case/{section_id}` | Create case |
| `POST` | `/index.php?/api/v2/update_case/{case_id}` | Update case |
| `POST` | `/index.php?/api/v2/delete_case/{case_id}` | Delete case |
| `POST` | `/index.php?/api/v2/delete_cases/{project_id}` | Bulk delete cases |
| `POST` | `/index.php?/api/v2/copy_cases_to_section/{section_id}` | Copy cases |
| `POST` | `/index.php?/api/v2/move_cases_to_section/{section_id}` | Move cases |

### Test Runs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/index.php?/api/v2/get_runs/{project_id}` | List runs |
| `GET` | `/index.php?/api/v2/get_run/{run_id}` | Get run |
| `POST` | `/index.php?/api/v2/add_run/{project_id}` | Create run |
| `POST` | `/index.php?/api/v2/update_run/{run_id}` | Update run |
| `POST` | `/index.php?/api/v2/close_run/{run_id}` | Close run |
| `POST` | `/index.php?/api/v2/delete_run/{run_id}` | Delete run |

### Test Results

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/index.php?/api/v2/get_results/{test_id}` | Get results for a test |
| `GET` | `/index.php?/api/v2/get_results_for_case/{run_id}/{case_id}` | Results for case in run |
| `GET` | `/index.php?/api/v2/get_results_for_run/{run_id}` | All results for a run |
| `POST` | `/index.php?/api/v2/add_result/{test_id}` | Add single result |
| `POST` | `/index.php?/api/v2/add_result_for_case/{run_id}/{case_id}` | Add result for case in run |
| `POST` | `/index.php?/api/v2/add_results/{run_id}` | Bulk add by test_id |
| `POST` | `/index.php?/api/v2/add_results_for_cases/{run_id}` | Bulk add by case_id ⭐ |

### Utilities

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/index.php?/api/v2/get_statuses` | All result statuses |
| `GET` | `/index.php?/api/v2/get_case_types` | All case types |
| `GET` | `/index.php?/api/v2/get_priorities` | All priorities |
| `GET` | `/index.php?/api/v2/get_templates/{project_id}` | All templates |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (no auth) |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/ui` | Web interface |

---

## Usage Examples

```bash
# Get all cases for project 1
curl -u "admin@testrail.mock:MockAPI@123" \
  "http://localhost:4002/index.php?/api/v2/get_cases/1"

# Create a test case
curl -X POST -u "admin@testrail.mock:MockAPI@123" \
  -H "Content-Type: application/json" \
  "http://localhost:4002/index.php?/api/v2/add_case/1" \
  -d '{
    "title": "Login with valid credentials",
    "type_id": 1,
    "priority_id": 3,
    "custom_preconds": "User account exists",
    "custom_steps_separated": [
      {"content": "Open login page", "expected": "Page loads"},
      {"content": "Enter credentials", "expected": "Fields accepted"},
      {"content": "Click Login", "expected": "Dashboard shown"}
    ]
  }'

# Add a result for a case in a run (most common automation use case)
curl -X POST -u "admin@testrail.mock:MockAPI@123" \
  -H "Content-Type: application/json" \
  "http://localhost:4002/index.php?/api/v2/add_result_for_case/1/1" \
  -d '{"status_id": 1, "comment": "Passed", "elapsed": "45s"}'

# Bulk add results by case_id
curl -X POST -u "admin@testrail.mock:MockAPI@123" \
  -H "Content-Type: application/json" \
  "http://localhost:4002/index.php?/api/v2/add_results_for_cases/1" \
  -d '{
    "results": [
      {"case_id": 1, "status_id": 1, "comment": "Pass", "elapsed": "12s"},
      {"case_id": 2, "status_id": 5, "comment": "Fail – button not found"}
    ]
  }'
```

---

## Status / Type / Priority Reference

### Status IDs
| ID | Name |
|----|------|
| 1 | Passed |
| 2 | Blocked |
| 3 | Untested |
| 4 | Retest |
| 5 | Failed |

### Type IDs
| ID | Name |
|----|------|
| 1 | Other |
| 2 | Automated |
| 3 | Functionality |
| 4 | Regression |
| 5 | Smoke |
| 6 | UI |
| 7 | Performance |

### Priority IDs
| ID | Name |
|----|------|
| 1 | Low |
| 2 | Medium |
| 3 | High |
| 4 | Critical |

---

## Postman Collection

Import from the `postman-collections/` folder at the project root:

| File | Description |
|------|-------------|
| `TestRail_Mock.postman_collection.json` | 41 requests, 8 folders, auto-capture test scripts |
| `TestRail_Mock.postman_environment.json` | Environment with credentials and dynamic ID variables |

See `POSTMAN_COLLECTION_README.md` for detailed usage instructions.

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TESTRAIL_MOCK_EMAIL` | `admin@testrail.mock` | Auth email |
| `TESTRAIL_MOCK_API_KEY` | `MockAPI@123` | Auth API key |
| `DATABASE_URL` | `sqlite:///./testrail.db` | Database path |

---

## Project Structure

```
testrail-mock/
├── app.py                    # FastAPI app, middleware, UI routes
├── models.py                 # SQLAlchemy models + Pydantic schemas
├── routes.py                 # API route handlers + auth
├── storage.py                # DB init, migration, seeding
├── templates/                # Jinja2 UI templates
├── tests/
│   └── test_api.py           # pytest test suite
├── requirements.txt
├── Dockerfile
├── README.md
└── POSTMAN_COLLECTION_README.md
```

---

## Running Tests

```bash
cd mock-services/testrail-mock
source .venv/bin/activate
pytest tests/ -v
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `401 Unauthorized` | Use `admin@testrail.mock` / `MockAPI@123` |
| `400 Bad Request` | Entity with that ID doesn't exist |
| `422 Validation Error` | Missing required field or wrong type |
| Port in use | Another process is on 4002 — kill it or change port |
| Data gone after restart | Check `testrail.db` wasn't deleted |
