# Mock Services - Jira, TestRail & Slack

A comprehensive suite of lightweight local mock services for **Jira**, **TestRail**, and **Slack** APIs, designed for teaching and demonstrating agentic AI integrations without requiring real API credentials.

## 🎯 Overview

This repository provides three fully functional mock services that simulate popular development and collaboration tools:

- **🎫 Jira Mock** (Port 4001) - Issue tracking and project management
- **🧪 TestRail Mock** (Port 4002) - Test case management and execution tracking  
- **💬 Slack Mock** (Port 4003) - Team communication and messaging

Each service includes:
- ✅ **REST API** endpoints matching real service APIs
- 🌐 **Web UI** for interactive testing and demonstration
- 📊 **API Documentation** via Swagger/OpenAPI
- 🐳 **Docker support** for easy deployment
- 📋 **Postman collections** for API testing
- 🧪 **Test suites** for validation

## 🚀 Quick Start - Multiple Ways to Run

### 📋 All Available Startup Methods

| Method | Platform | Command | Use Case |
|--------|----------|---------|----------|
| **🐳 Docker Compose** | All OS | `docker compose up -d --build` | **Recommended** - Production-ready |
| **🚀 All Services Script** | Mac/Linux | `./start-all.sh` | **Easy** - One command for all services |
| **🪟 All Services Batch** | Windows | `start-all.bat` | **Easy** - Windows one-command startup |
| **🔧 Individual Scripts** | Mac/Linux | `cd service && ./start.sh` | Local development, service-by-service |
| **🪟 Individual Batch** | Windows | `cd service && start.bat` | Windows service-by-service |
| **🐍 Python Direct** | All OS | `python app.py` | Direct execution, custom environments |

📚 **Detailed Guide**: See [STARTUP_GUIDE.md](STARTUP_GUIDE.md) for comprehensive instructions

### 🎯 Method 1: Docker Compose (Production-Ready)

**Start all three services with one command:**

```bash
# Clone and navigate
git clone <repository-url>
cd Jira_Testrail_Slack_Demo_Service

# Start everything
docker compose up -d --build

# View logs (optional)
docker compose logs -f

# Stop everything
docker compose down
```

**✅ Result**: All services running on ports 4001, 4002, 4003 with health checks and auto-restart

### 🚀 Method 2: All Services Scripts (Easiest for Development)

**Mac/Linux - One command for all services:**

```bash
# Start all services locally
./start-all.sh

# Stop all services
./stop-all.sh

# Use Docker instead
./start-all.sh --docker
```

**Windows - One command for all services:**

```cmd
# Start all services locally
start-all.bat

# Stop all services  
stop-all.bat

# Use Docker instead
start-all.bat docker
```

**✅ Result**: All services with dependency checking, health monitoring, and log management

### 🔧 Method 3: Individual Shell Scripts (Mac/Linux)

**Start each service in separate terminals:**

```bash
# Terminal 1 - Jira Mock
cd mock-services/jira-mock
./start.sh                    # Starts on port 4001

# Terminal 2 - TestRail Mock  
cd mock-services/testrail-mock
./start.sh                    # Starts on port 4002

# Terminal 3 - Slack Mock
cd mock-services/slack-mock
./start.sh                    # Starts on port 4003
```

### 🪟 Method 4: Windows Batch Files

**Start each service in separate command prompts:**

```cmd
# Command Prompt 1 - Jira Mock
cd mock-services\jira-mock
start.bat

# Command Prompt 2 - TestRail Mock  
cd mock-services\testrail-mock
start.bat

# Command Prompt 3 - Slack Mock
cd mock-services\slack-mock
start.bat
```

### 🐍 Method 5: Direct Python Execution

**Run Python files directly (after installing dependencies):**

```bash
# Jira Mock
cd mock-services/jira-mock
pip install -r requirements.txt
python app.py                 # or python start_simple.py

# TestRail Mock
cd mock-services/testrail-mock  
pip install -r requirements.txt
python app.py

# Slack Mock
cd mock-services/slack-mock
pip install -r requirements.txt
python app_simple.py          # or python start_simple.py
```

### ⚡ Method 6: Manual Uvicorn (Advanced)

**Full manual control:**

```bash
# Install dependencies for each service first
cd mock-services/jira-mock && pip install -r requirements.txt
cd ../testrail-mock && pip install -r requirements.txt  
cd ../slack-mock && pip install -r requirements.txt

# Start each service manually
uvicorn mock-services.jira-mock.app:app --host 0.0.0.0 --port 4001 &
uvicorn mock-services.testrail-mock.app:app --host 0.0.0.0 --port 4002 &
uvicorn mock-services.slack-mock.app_simple:app --host 0.0.0.0 --port 4003 &
```

### 🎯 Quick Decision Guide

| If you want... | Use this method |
|----------------|-----------------|
| **Easiest setup (beginners)** | 🚀 All Services Scripts (`./start-all.sh` or `start-all.bat`) |
| **Production-like environment** | 🐳 Docker Compose |
| **Individual service control** | 🔧 Individual scripts |
| **Custom Python environment** | 🐍 Direct Python execution |
| **Full control** | ⚡ Manual Uvicorn |

**Service URLs (all methods):**
- 🎫 **Jira Mock**: http://localhost:4001/ui
- 🧪 **TestRail Mock**: http://localhost:4002/ui  
- 💬 **Slack Mock**: http://localhost:4003/ui

## 📋 Service Details

### 🎫 Jira Mock Service (Port 4001)

**Purpose**: Simulates Atlassian Jira Cloud REST API v3 for issue management.

**Key Features**:
- Create, read, update, delete issues
- File attachments support
- JQL search functionality
- Issue types: Bug, Task, Story, Epic
- Priority and status management

**Quick Test**:
```bash
# Health check
curl http://localhost:4001/health

# Get sample issue
curl -H "Authorization: Bearer token" http://localhost:4001/rest/api/3/issue/QA-1
```

**Documentation**: [Jira Mock README](mock-services/jira-mock/README.md)

### 🧪 TestRail Mock Service (Port 4002)

**Purpose**: Simulates TestRail's REST API for test case management and execution tracking.

**Key Features**:
- Test case creation and management
- Test execution and result tracking
- Test runs and test plans
- Test sections organization
- Status tracking (Passed, Failed, Blocked, etc.)

**Quick Test**:
```bash
# Health check
curl http://localhost:4002/health

# Get sample test case
curl -H "Authorization: Bearer token" http://localhost:4002/index.php?/api/v2/get_case/1
```

**Documentation**: [TestRail Mock README](mock-services/testrail-mock/README.md)

### 💬 Slack Mock Service (Port 4003)

**Purpose**: Simulates Slack's Web API for team communication and messaging.

**Key Features**:
- Post messages to channels
- Retrieve conversation history
- File upload simulation
- Channel management
- Threading support
- Two demo channels: #qa-reports and #general

**Quick Test**:
```bash
# Health check
curl http://localhost:4003/health

# Get channel history
curl -H "Authorization: Bearer token" "http://localhost:4003/api/conversations.history?channel=qa-reports"
```

**Documentation**: [Slack Mock README](mock-services/slack-mock/README.md)

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root or `mock-services/` directory:

```env
# Authentication
MOCK_AUTH_REQUIRED=true

# Service-specific settings
JIRA_PROJECT_KEY=QA
TESTRAIL_PROJECT_ID=1
DEFAULT_SLACK_CHANNEL=qa-reports

# Optional features
ENABLE_RATE_LIMIT=false
```

### Port Configuration

| Service | Default Port | Environment Variable |
|---------|--------------|---------------------|
| Jira Mock | 4001 | `JIRA_PORT` |
| TestRail Mock | 4002 | `TESTRAIL_PORT` |
| Slack Mock | 4003 | `SLACK_PORT` |

## 🧪 Testing All Services

### Health Check Script

```bash
#!/bin/bash
echo "🔍 Checking all mock services..."

services=("Jira:4001" "TestRail:4002" "Slack:4003")

for service in "${services[@]}"; do
    name=${service%%:*}
    port=${service##*:}
    
    if curl -s -f "http://localhost:$port/health" > /dev/null; then
        echo "✅ $name Mock (port $port) - Healthy"
    else
        echo "❌ $name Mock (port $port) - Not responding"
    fi
done
```

### Integration Test Example

```bash
# Test complete workflow across all services
echo "🚀 Testing integration workflow..."

# 1. Create Jira issue
ISSUE_RESPONSE=$(curl -s -X POST "http://localhost:4001/rest/api/3/issue" \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{"fields":{"summary":"Integration test issue","issuetype":{"name":"Bug"}}}')

ISSUE_KEY=$(echo $ISSUE_RESPONSE | jq -r '.key')
echo "📝 Created Jira issue: $ISSUE_KEY"

# 2. Create TestRail test case
TEST_RESPONSE=$(curl -s -X POST "http://localhost:4002/index.php?/api/v2/add_case/1" \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test for '$ISSUE_KEY'","template_id":1}')

TEST_ID=$(echo $TEST_RESPONSE | jq -r '.id')
echo "🧪 Created TestRail case: $TEST_ID"

# 3. Post to Slack
curl -s -X POST "http://localhost:4003/api/chat.postMessage" \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{"channel":"qa-reports","text":"Created '$ISSUE_KEY' and test case '$TEST_ID'","username":"IntegrationBot"}'

echo "💬 Posted to Slack channel"
echo "✅ Integration test completed!"
```

## 📚 API Documentation

Each service provides interactive API documentation:

- **Jira Mock**: http://localhost:4001/docs
- **TestRail Mock**: http://localhost:4002/docs  
- **Slack Mock**: http://localhost:4003/docs

## 📦 Postman Collections

Import the provided Postman collections for interactive API testing:

### Jira Mock
- Collection: `mock-services/jira-mock/Jira_Mock_API.postman_collection.json`
- Environment: `mock-services/jira-mock/Jira_Mock_Environment.postman_environment.json`

### TestRail Mock  
- Collection: `mock-services/testrail-mock/TestRail_Mock_API.postman_collection.json`
- Environment: `mock-services/testrail-mock/TestRail_Mock_Environment.postman_environment.json`

### Slack Mock
- Collection: `mock-services/slack-mock/Slack_Mock_API.postman_collection.json`
- Environment: `mock-services/slack-mock/Slack_Mock_Environment.postman_environment.json`

## 🎓 Educational Use Cases

This mock service suite is perfect for:

### 1. **AI Agent Development Training**
- Teach students to build AI agents that interact with multiple APIs
- Demonstrate cross-service workflows and integrations
- Practice error handling and API authentication

### 2. **API Integration Workshops**
- Show real-world API patterns and best practices
- Demonstrate REST API design principles
- Practice with realistic data and responses

### 3. **DevOps and Testing**
- CI/CD pipeline testing without external dependencies
- Load testing and performance benchmarking
- Integration testing scenarios

### 4. **Agile Workflow Simulation**
- Demonstrate complete development workflows
- Show tool integration in modern development practices
- Practice with realistic project management scenarios

## 🛠️ Development

### Project Structure

```
Jira_Testrail_Slack_Demo_Service/
├── docker-compose.yml          # Multi-service orchestration
├── readme.md                   # This file
├── service_setup.md           # Technical specifications
└── mock-services/
    ├── jira-mock/             # Jira mock service
    │   ├── app.py             # FastAPI application
    │   ├── templates/         # Web UI templates
    │   ├── Dockerfile         # Container definition
    │   └── README.md          # Service documentation
    ├── testrail-mock/         # TestRail mock service
    │   ├── app.py             # FastAPI application
    │   ├── models.py          # Database models
    │   ├── routes.py          # API routes
    │   └── README.md          # Service documentation
    └── slack-mock/            # Slack mock service
        ├── app.py             # FastAPI application
        ├── models.py          # Database models
        ├── routes.py          # API routes
        └── README.md          # Service documentation
```

### Adding New Services

1. Create new directory under `mock-services/`
2. Follow the established FastAPI + SQLAlchemy pattern
3. Add service to `docker-compose.yml`
4. Create comprehensive README.md
5. Add Postman collection and tests

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## 🚨 Troubleshooting

### Common Issues

**Port Conflicts**:
```bash
# Check what's using the ports
lsof -i :4001 -i :4002 -i :4003

# Kill processes if needed
pkill -f uvicorn
```

**Docker Issues**:
```bash
# Reset everything
docker compose down -v
docker system prune -f
docker compose up -d --build
```

**Database Issues**:
```bash
# Reset all databases
rm -f mock-services/*/*.db
docker compose restart
```

### Getting Help

1. Check individual service README files
2. Review API documentation at `/docs` endpoints
3. Check service logs: `docker compose logs [service-name]`
4. Verify health endpoints: `curl http://localhost:400[1-3]/health`

## 📄 License

This project is designed for educational and development purposes. Each mock service simulates real APIs for learning and testing without requiring actual service credentials.

## 📋 Quick Reference Card

### 🚀 Fastest Way to Start (Copy & Paste)

```bash
# Option 1: All services with one script (Mac/Linux) - EASIEST!
./start-all.sh

# Option 2: All services with Docker (Production-ready)
docker compose up -d --build

# Option 3: All services (Windows) - EASIEST!
start-all.bat

# Option 4: Individual services (Mac/Linux)
cd mock-services/jira-mock && ./start.sh &
cd ../testrail-mock && ./start.sh &  
cd ../slack-mock && ./start.sh &
```

### 🌐 Service Access URLs

| Service | Web UI | API Docs | Health Check |
|---------|--------|----------|--------------|
| **Jira Mock** | http://localhost:4001/ui | http://localhost:4001/docs | http://localhost:4001/health |
| **TestRail Mock** | http://localhost:4002/ui | http://localhost:4002/docs | http://localhost:4002/health |
| **Slack Mock** | http://localhost:4003/ui | http://localhost:4003/docs | http://localhost:4003/health |

### 🔧 Quick Commands

```bash
# Stop all services
./stop-all.sh                # Mac/Linux
stop-all.bat                 # Windows
docker compose down          # Docker

# Check all services are running
curl http://localhost:4001/health && curl http://localhost:4002/health && curl http://localhost:4003/health

# View logs
tail -f logs/*.log           # Local services
docker compose logs -f      # Docker services

# Reset everything
./stop-all.sh && ./start-all.sh                    # Local
docker compose down -v && docker compose up -d --build  # Docker
```

---

**Ready to start?** Choose your preferred method above and visit the web interfaces to explore the mock services! 🚀