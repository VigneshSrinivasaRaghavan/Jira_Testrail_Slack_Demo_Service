# Mock Services - Jira, TestRail & Slack

A lightweight suite of local mock services for **Jira**, **TestRail**, and **Slack** APIs, designed for teaching and demonstrating agentic AI integrations without requiring real API credentials.

## 🎯 What You Get

Three fully functional mock services that simulate popular development tools:

- **🎫 Jira Mock** (Port 4001) - Issue tracking and project management
- **🧪 TestRail Mock** (Port 4002) - Test case management and execution tracking  
- **💬 Slack Mock** (Port 4003) - Team communication and messaging

Each service includes REST APIs, web UI, Swagger docs, and Postman collections.

## 🚀 Quick Start

### Mac/Linux - One Command

```bash
# Clone and start everything
git clone <repository-url>
cd Jira_Testrail_Slack_Demo_Service

# Start all services
./start-all.sh

# Stop all services
./stop-all.sh
```

### Windows - One Command

```cmd
# Clone and start everything
git clone <repository-url>
cd Jira_Testrail_Slack_Demo_Service

# Start all services
start-all.bat

# Stop all services
stop-all.bat
```

**✅ Result**: All three services running with health checks and log management

**Service URLs:**
- 🎫 **Jira Mock**: http://localhost:4001/ui
- 🧪 **TestRail Mock**: http://localhost:4002/ui  
- 💬 **Slack Mock**: http://localhost:4003/ui

## 📋 Service Details

### 🎫 Jira Mock Service (Port 4001)
- **Purpose**: Issue tracking and project management
- **Features**: CRUD operations, JQL search, attachments, issue types (Bug, Task, Story, Epic)
- **Documentation**: [Jira Mock README](mock-services/jira-mock/README.md)

### 🧪 TestRail Mock Service (Port 4002)
- **Purpose**: Test case management and execution tracking
- **Features**: Test cases, test runs, results tracking, delete operations (single & bulk)
- **Documentation**: [TestRail Mock README](mock-services/testrail-mock/README.md)

### 💬 Slack Mock Service (Port 4003)
- **Purpose**: Team communication and messaging
- **Features**: Post messages, conversation history, file uploads, channels (#qa-reports, #general)
- **Documentation**: [Slack Mock README](mock-services/slack-mock/README.md)

## 🧪 Testing & Documentation

**Health Check All Services:**
```bash
curl http://localhost:4001/health && curl http://localhost:4002/health && curl http://localhost:4003/health
```

**API Documentation:**
- **Jira Mock**: http://localhost:4001/docs
- **TestRail Mock**: http://localhost:4002/docs  
- **Slack Mock**: http://localhost:4003/docs

**Postman Collections:** Each service includes ready-to-import Postman collections in their respective directories.

## 🎓 Perfect For

- **AI Agent Development Training** - Multi-API integrations without real credentials
- **API Integration Workshops** - Realistic data and responses
- **DevOps Testing** - CI/CD pipelines without external dependencies
- **Educational Demos** - Complete development workflow simulation

## 🚨 Troubleshooting

**Services not starting?**
```bash
# Check ports and restart
lsof -i :4001 -i :4002 -i :4003
./stop-all.sh && ./start-all.sh
```

**Need more help?** Check individual service README files for detailed configuration and troubleshooting.

---

**Ready to start?** Run `./start-all.sh` (Mac/Linux) or `start-all.bat` (Windows) and visit the web interfaces! 🚀