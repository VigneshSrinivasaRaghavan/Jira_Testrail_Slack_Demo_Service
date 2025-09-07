# TestRail Mock Service

A FastAPI-based mock service that simulates TestRail's REST API for test case management and execution tracking.

## Features

- 🧪 **Test Case Management**: Create, read, update test cases
- 📊 **Test Execution**: Add test results and track execution history
- 🏃 **Test Runs**: Create and manage test runs
- 📁 **Test Sections**: Organize test cases in sections
- 🌐 **Web UI**: Simple interface for test management
- 🔐 **Authentication**: Bearer token validation (configurable)
- 📊 **API Documentation**: Built-in Swagger/OpenAPI docs
- 🐳 **Docker Ready**: Containerized with health checks

## Quick Start

### Using Docker Compose (Recommended)

```bash
# From project root
docker compose up -d testrail-mock

# View logs
docker compose logs -f testrail-mock
```

### Local Development

```bash
cd mock-services/testrail-mock

# Option 1: Use startup script
./start.sh

# Option 2: Manual setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 4002 --reload
```

### Windows Users

```cmd
cd mock-services\testrail-mock

# Use batch script
start.bat

# Or PowerShell
.\start-testrail.ps1
```

## API Endpoints

### Core TestRail APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/index.php?/api/v2/add_case/{section_id}` | Create test case |
| `GET` | `/index.php?/api/v2/get_case/{case_id}` | Get test case |
| `POST` | `/index.php?/api/v2/update_case/{case_id}` | Update test case |
| `DELETE` | `/index.php?/api/v2/delete_case/{case_id}` | Delete test case |
| `GET` | `/index.php?/api/v2/get_cases/{project_id}` | Get all test cases |
| `DELETE` | `/index.php?/api/v2/cases/bulk` | Bulk delete test cases |
| `POST` | `/index.php?/api/v2/add_result/{case_id}` | Add test result |
| `GET` | `/index.php?/api/v2/get_results/{case_id}` | Get test results |
| `POST` | `/index.php?/api/v2/add_run/{project_id}` | Create test run |
| `GET` | `/index.php?/api/v2/get_run/{run_id}` | Get test run |

### Web Interface

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/ui` | Test case overview |
| `GET` | `/ui/case/{case_id}` | Test case detail view |
| `GET` | `/ui/run/{run_id}` | Test run detail view |
| `POST` | `/ui/case/create` | Create test case via web form |
| `POST` | `/ui/run/create` | Create test run via web form |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger API documentation |
| `POST` | `/admin/reset` | Reset database with seed data |

## Usage Examples

### Create Test Case

```bash
curl -X POST "http://localhost:4002/index.php?/api/v2/add_case/1" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Login should succeed with valid credentials",
    "template_id": 1,
    "type_id": 1,
    "priority_id": 2,
    "estimate": "5m",
    "custom_steps": "1. Navigate to login page\n2. Enter valid credentials\n3. Click login"
  }'
```

### Get Test Case

```bash
curl -X GET "http://localhost:4002/index.php?/api/v2/get_case/1" \
  -H "Authorization: Bearer your-token"
```

### Delete Test Case

```bash
curl -X DELETE "http://localhost:4002/api/v2/case/1" \
  -H "Authorization: Bearer your-token"
```

### Bulk Delete Test Cases

```bash
curl -X DELETE "http://localhost:4002/api/v2/cases/bulk" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "case_ids": [1, 2, 3, 4, 5]
  }'
```

### Add Test Result

```bash
curl -X POST "http://localhost:4002/index.php?/api/v2/add_result/1" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "status_id": 1,
    "comment": "Test passed successfully",
    "elapsed": "3m",
    "defects": "BUG-123"
  }'
```

### Create Test Run

```bash
curl -X POST "http://localhost:4002/index.php?/api/v2/add_run/1" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Smoke Test Run",
    "description": "Basic smoke testing",
    "case_ids": [1, 2, 3]
  }'
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `4002` | Server port |
| `HOST` | `0.0.0.0` | Server host |
| `MOCK_AUTH_REQUIRED` | `true` | Enable/disable auth |
| `TESTRAIL_PROJECT_ID` | `1` | Default project ID |
| `DATABASE_URL` | `sqlite:///./testrail.db` | Database connection |

## Test Status IDs

The service uses standard TestRail status IDs:

| Status ID | Status Name | Description |
|-----------|-------------|-------------|
| `1` | Passed | Test passed successfully |
| `2` | Blocked | Test is blocked |
| `3` | Untested | Test not yet executed |
| `4` | Retest | Test needs to be retested |
| `5` | Failed | Test failed |

## Default Data

The service comes with pre-seeded sample test cases:

- **Case 1**: "User Login - Valid Credentials"
- **Case 2**: "User Login - Invalid Credentials"  
- **Case 3**: "Password Reset Functionality"
- **Case 4**: "User Registration Process"

## API Mapping to Real TestRail

| Mock Endpoint | Real TestRail Endpoint | Notes |
|---------------|----------------------|-------|
| `POST /index.php?/api/v2/add_case/{section_id}` | `POST https://your-domain.testrail.io/index.php?/api/v2/add_case/{section_id}` | Core fields supported |
| `GET /index.php?/api/v2/get_case/{case_id}` | `GET https://your-domain.testrail.io/index.php?/api/v2/get_case/{case_id}` | Standard response format |
| `POST /index.php?/api/v2/add_result/{case_id}` | `POST https://your-domain.testrail.io/index.php?/api/v2/add_result/{case_id}` | Result tracking |
| `POST /index.php?/api/v2/add_run/{project_id}` | `POST https://your-domain.testrail.io/index.php?/api/v2/add_run/{project_id}` | Test run management |

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/ -v
```

## Postman Collection

Import the provided Postman collection for interactive testing:

- **Collection**: `TestRail_Mock_API.postman_collection.json`
- **Environment**: `TestRail_Mock_Environment.postman_environment.json`

## Web Interface

Visit the web interface at:

- **Test Cases Overview**: http://localhost:4002/ui
- **Specific Test Case**: http://localhost:4002/ui/case/1
- **Test Run Details**: http://localhost:4002/ui/run/1

The web interface allows you to:
- View all test cases in organized sections
- Create new test cases via forms
- Execute test cases and add results
- Manage test runs and track progress
- View execution history and statistics

## Database Management

### Reset Database

```bash
# Option 1: API reset (requires auth)
curl -X POST -H "Authorization: Bearer token" http://localhost:4002/admin/reset

# Option 2: Delete database file (service restart required)
rm testrail.db

# Option 3: Docker volume reset
docker compose down
docker volume rm testrail_db
docker compose up -d testrail-mock
```

### Inspect Database

```bash
# View tables
sqlite3 testrail.db ".tables"

# View test cases
sqlite3 testrail.db "SELECT * FROM cases;"

# View test results
sqlite3 testrail.db "SELECT * FROM results;"
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**: Change the `PORT` environment variable
2. **Database Locked**: Stop all instances and delete `testrail.db`
3. **Auth Errors**: Set `MOCK_AUTH_REQUIRED=false` to disable auth

### Logs

View service logs:

```bash
# Docker Compose
docker compose logs testrail-mock

# Local development
# Logs are printed to stdout
```

### Health Check

```bash
# Quick health check
curl http://localhost:4002/health
```

## Development

### Project Structure

```
testrail-mock/
├── app.py              # FastAPI application
├── models.py           # SQLAlchemy models
├── routes.py           # API route handlers
├── storage.py          # Database operations
├── templates/          # Jinja2 templates
│   ├── index.html      # Test case overview
│   ├── case_detail.html # Test case detail
│   └── run_detail.html # Test run detail
├── shared/             # Shared resources
│   └── seed/           # Seed data
├── tests/              # Test suite
├── Dockerfile          # Container definition
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

### Adding New Features

1. **New API Endpoint**: Add route to `routes.py`
2. **Database Changes**: Update models in `models.py`
3. **UI Changes**: Modify templates in `templates/`
4. **Tests**: Add tests to `tests/test_api.py`

## License

This is a mock service for development and testing purposes only.