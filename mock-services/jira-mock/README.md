# Jira Mock Service

A FastAPI-based mock service that simulates Atlassian Jira Cloud REST API v3 for testing and development purposes.

## Features

- 🎯 **Issue Management**: Create, read, update, and delete issues
- 📎 **File Attachments**: Upload and manage file attachments
- 🌐 **Web UI**: Simple interface for issue management
- 🔐 **Authentication**: Bearer token validation (configurable)
- 📊 **API Documentation**: Built-in Swagger/OpenAPI docs
- 🐳 **Docker Ready**: Containerized with health checks

## Quick Start

### Using Docker Compose (Recommended)

```bash
# From project root
docker compose up -d jira-mock

# View logs
docker compose logs -f jira-mock
```

### Local Development

```bash
cd mock-services/jira-mock

# Option 1: Use startup script
./start.sh

# Option 2: Manual setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 4001 --reload
```

### Windows Users

```cmd
cd mock-services\jira-mock

# Use batch script
start.bat

# Or PowerShell
.\start-jira.ps1
```

## API Endpoints

### Core Jira APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/rest/api/3/issue` | Create new issue |
| `GET` | `/rest/api/3/issue/{issueIdOrKey}` | Get issue details |
| `PUT` | `/rest/api/3/issue/{issueIdOrKey}` | Update issue |
| `DELETE` | `/rest/api/3/issue/{issueIdOrKey}` | Delete issue |
| `GET` | `/rest/api/3/search` | Search issues with JQL |
| `POST` | `/rest/api/3/issue/{issueIdOrKey}/attachments` | Upload attachments |

### Web Interface

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/ui` | Issue list and quick-create form |
| `GET` | `/ui/issue/{key}` | Issue detail view |
| `POST` | `/ui/create` | Create issue via web form |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger API documentation |
| `POST` | `/admin/reset` | Reset database with seed data |

## Usage Examples

### Create Issue

```bash
curl -X POST "http://localhost:4001/rest/api/3/issue" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "fields": {
      "summary": "Test issue from API",
      "description": "This is a test issue created via API",
      "issuetype": {"name": "Bug"},
      "priority": {"name": "High"}
    }
  }'
```

### Get Issue

```bash
curl -X GET "http://localhost:4001/rest/api/3/issue/QA-1" \
  -H "Authorization: Bearer your-token"
```

### Search Issues

```bash
curl -X GET "http://localhost:4001/rest/api/3/search?jql=project=QA&startAt=0&maxResults=50" \
  -H "Authorization: Bearer your-token"
```

### Upload Attachment

```bash
curl -X POST "http://localhost:4001/rest/api/3/issue/QA-1/attachments" \
  -H "Authorization: Bearer your-token" \
  -F "file=@/path/to/your/file.txt"
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `4001` | Server port |
| `HOST` | `0.0.0.0` | Server host |
| `MOCK_AUTH_REQUIRED` | `true` | Enable/disable auth |
| `JIRA_PROJECT_KEY` | `QA` | Default project key |
| `DATABASE_URL` | `sqlite:///./jira.db` | Database connection |

## Default Data

The service comes with pre-seeded sample issues:

- **QA-1**: Sample Bug - "Login page not loading"
- **QA-2**: Sample Task - "Update user documentation"
- **QA-3**: Sample Story - "Implement dark mode"

## API Mapping to Real Jira

| Mock Endpoint | Real Jira Endpoint | Notes |
|---------------|-------------------|-------|
| `POST /rest/api/3/issue` | `POST https://your-domain.atlassian.net/rest/api/3/issue` | Simplified field validation |
| `GET /rest/api/3/issue/{key}` | `GET https://your-domain.atlassian.net/rest/api/3/issue/{key}` | Core fields supported |
| `GET /rest/api/3/search` | `GET https://your-domain.atlassian.net/rest/api/3/search` | Basic JQL support |
| `POST /rest/api/3/issue/{key}/attachments` | `POST https://your-domain.atlassian.net/rest/api/3/issue/{key}/attachments` | File upload simulation |

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

- **Collection**: `Jira_Mock_API.postman_collection.json`
- **Environment**: `Jira_Mock_Environment.postman_environment.json`

## Web Interface

Visit the web interface at:

- **Issue List**: http://localhost:4001/ui
- **Specific Issue**: http://localhost:4001/ui/issue/QA-1

The web interface allows you to:
- View all issues in a table format
- Create new issues via a simple form
- View detailed issue information
- See API usage examples

## Database Management

### Reset Database

```bash
# Option 1: API reset (requires auth)
curl -X POST -H "Authorization: Bearer token" http://localhost:4001/admin/reset

# Option 2: Delete database file (service restart required)
rm jira.db

# Option 3: Docker volume reset
docker compose down
docker volume rm jira_db
docker compose up -d jira-mock
```

### Inspect Database

```bash
# View tables
sqlite3 jira.db ".tables"

# View issues
sqlite3 jira.db "SELECT * FROM issues;"
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**: Change the `PORT` environment variable
2. **Database Locked**: Stop all instances and delete `jira.db`
3. **Auth Errors**: Set `MOCK_AUTH_REQUIRED=false` to disable auth

### Logs

View service logs:

```bash
# Docker Compose
docker compose logs jira-mock

# Local development
# Logs are printed to stdout
```

### Health Check

```bash
# Quick health check
curl http://localhost:4001/health

# Or use the provided script
./check_jira.sh
```

## Development

### Project Structure

```
jira-mock/
├── app.py              # FastAPI application
├── templates/          # Jinja2 templates
│   ├── index.html      # Issue list view
│   └── issue_detail.html # Issue detail view
├── static/             # Static assets
├── Dockerfile          # Container definition
├── requirements.txt    # Python dependencies
├── start.sh           # Startup script (Unix)
├── start.bat          # Startup script (Windows)
└── README.md          # This file
```

### Adding New Features

1. **New API Endpoint**: Add route to `app.py`
2. **Database Changes**: Update SQLAlchemy models
3. **UI Changes**: Modify templates in `templates/`
4. **Tests**: Add tests following existing patterns

## License

This is a mock service for development and testing purposes only.
