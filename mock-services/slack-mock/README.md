# Slack Mock Service

A FastAPI-based mock service that simulates Slack's chat.postMessage, conversations.history, and files.upload APIs for testing and development purposes.

## Features

- 🚀 **Chat API**: Post messages to channels with threading support
- 📜 **History API**: Retrieve conversation history with pagination
- 📎 **File Upload**: Upload files to channels (simulated)
- 🌐 **Web UI**: Simple interface to view channels and messages
- 🔐 **Authentication**: Bearer token validation (configurable)
- 📊 **API Documentation**: Built-in Swagger/OpenAPI docs
- 🐳 **Docker Ready**: Containerized with health checks

## Quick Start

### Using Docker Compose (Recommended)

```bash
# From project root
docker compose up -d slack-mock

# View logs
docker compose logs -f slack-mock
```

### Local Development

```bash
cd mock-services/slack-mock

# Install dependencies
pip install -r requirements.txt

# Run the service
python app.py
```

## API Endpoints

### Core Slack APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat.postMessage` | Send messages to channels |
| `GET` | `/api/conversations.history` | Get channel message history |
| `POST` | `/api/files.upload` | Upload files to channels |

### Web Interface

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/ui` | Channel overview page |
| `GET` | `/ui/channel/{name}` | Individual channel view |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger API documentation |
| `GET` | `/redoc` | ReDoc API documentation |

## Usage Examples

### Post Message

```bash
curl -X POST "http://localhost:4003/api/chat.postMessage" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "qa-reports",
    "text": "Hello from API!",
    "username": "APIBot"
  }'
```

### Get Conversation History

```bash
curl -X GET "http://localhost:4003/api/conversations.history?channel=qa-reports&limit=50" \
  -H "Authorization: Bearer your-token"
```

### Upload File

```bash
curl -X POST "http://localhost:4003/api/files.upload" \
  -H "Authorization: Bearer your-token" \
  -F "channels=qa-reports" \
  -F "title=Test Document" \
  -F "initial_comment=Uploading test file" \
  -F "file=@/path/to/your/file.txt"
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `4003` | Server port |
| `HOST` | `0.0.0.0` | Server host |
| `MOCK_AUTH_REQUIRED` | `true` | Enable/disable auth |
| `DEFAULT_SLACK_CHANNEL` | `qa-reports` | Default channel name |
| `DATABASE_URL` | `sqlite:///./slack_mock.db` | Database connection |

## Default Channels

The service comes with two pre-configured channels:

1. **#qa-reports** (`C1234567890`) - Quality Assurance Reports and Updates
2. **#general** (`C0987654321`) - General Discussion

## API Mapping to Real Slack

| Mock Endpoint | Real Slack Endpoint | Notes |
|---------------|-------------------|-------|
| `POST /api/chat.postMessage` | `POST https://slack.com/api/chat.postMessage` | Simplified response format |
| `GET /api/conversations.history` | `GET https://slack.com/api/conversations.history` | Basic pagination support |
| `POST /api/files.upload` | `POST https://slack.com/api/files.upload` | File storage is simulated |

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

- **Collection**: `Slack_Mock_API.postman_collection.json`
- **Environment**: `Slack_Mock_Environment.postman_environment.json`

## Web Interface

Visit the web interface at:

- **Channel Overview**: http://localhost:4003/ui
- **Specific Channel**: http://localhost:4003/ui/channel/qa-reports

The web interface allows you to:
- View all channels and their message counts
- Browse message history for each channel
- Post new messages via a simple form
- See API usage examples

## Development

### Project Structure

```
slack-mock/
├── app.py              # FastAPI application
├── models.py           # SQLAlchemy models
├── routes.py           # API route handlers
├── storage.py          # Database operations
├── templates/          # Jinja2 templates
│   ├── index.html      # Channel overview
│   └── channel_view.html # Channel detail view
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

## Troubleshooting

### Common Issues

1. **Port Already in Use**: Change the `PORT` environment variable
2. **Database Locked**: Stop all instances and delete `slack_mock.db`
3. **Auth Errors**: Set `MOCK_AUTH_REQUIRED=false` to disable auth

### Logs

View service logs:

```bash
# Docker Compose
docker compose logs slack-mock

# Local development
# Logs are printed to stdout
```

## License

This is a mock service for development and testing purposes only.
