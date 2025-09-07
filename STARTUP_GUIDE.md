# 🚀 Mock Services - Complete Startup Guide

This guide covers all the different ways to start and manage the Mock Services suite (Jira, TestRail, and Slack).

## 📋 Quick Reference Table

| Method | Platform | Files | Command | Use Case |
|--------|----------|-------|---------|----------|
| **🐳 Docker Compose** | All OS | `docker-compose.yml` | `docker compose up -d --build` | **Recommended** - Production-like |
| **🔧 All Services Script** | Mac/Linux | `start-all.sh` / `stop-all.sh` | `./start-all.sh` | One command for all services |
| **🪟 All Services Batch** | Windows | `start-all.bat` / `stop-all.bat` | `start-all.bat` | Windows one-command startup (simple version) |
| **⚙️ Individual Scripts** | Mac/Linux | `mock-services/*/start.sh` | `cd service && ./start.sh` | Service-by-service control |
| **🔧 Individual Batch** | Windows | `mock-services/*/start.bat` | `cd service && start.bat` | Windows service-by-service |
| **🐍 Direct Python** | All OS | `app.py` / `start_simple.py` | `python app.py` | Direct execution |

## 🎯 Method 1: Docker Compose (Recommended)

### ✅ Advantages
- **One command** starts everything
- **Isolated environments** with proper networking
- **Automatic health checks** and restart policies
- **Production-ready** configuration
- **Easy cleanup** with volumes

### 🚀 Usage

```bash
# Start all services
docker compose up -d --build

# View logs
docker compose logs -f

# Check status
docker compose ps

# Stop all services
docker compose down

# Complete cleanup (removes volumes)
docker compose down -v
```

### 🔧 Advanced Docker Commands

```bash
# Start specific service
docker compose up -d jira-mock

# Rebuild specific service
docker compose up -d --build slack-mock

# View logs for specific service
docker compose logs -f testrail-mock

# Execute command in running container
docker compose exec jira-mock bash

# Scale services (if needed)
docker compose up -d --scale jira-mock=2
```

## 🔧 Method 2: All Services Scripts (Mac/Linux)

### ✅ Advantages
- **Local development** friendly
- **Easy debugging** with direct log access
- **No Docker required**
- **Fast startup** for development

### 📁 Files
- `start-all.sh` - Start all services locally
- `stop-all.sh` - Stop all services gracefully

### 🚀 Usage

```bash
# Make scripts executable (one time)
chmod +x start-all.sh stop-all.sh

# Start all services locally
./start-all.sh

# Start with Docker instead
./start-all.sh --docker

# Stop all services
./stop-all.sh

# Force stop (emergency)
./stop-all.sh --force

# Get help
./start-all.sh --help
```

### 🔍 Features
- **Dependency checking** (Python, pip)
- **Port availability** checking
- **Health monitoring** with curl tests
- **Log management** in `logs/` directory
- **PID tracking** for clean shutdown
- **Colorized output** for better UX

## 🪟 Method 3: All Services Batch (Windows)

### ✅ Advantages
- **Windows native** batch files
- **No WSL required**
- **Command prompt** friendly
- **Simplified design** - no complex variable expansion
- **Cross-platform compatibility** tested

### 📁 Files
- `start-all.bat` - Start all services on Windows
- `stop-all.bat` - Stop all services on Windows

### 🚀 Usage

```cmd
# Start all services locally
start-all.bat

# Start with Docker instead
start-all.bat docker

# Stop all services
stop-all.bat

# Force stop (emergency)
stop-all.bat force

# Get help
start-all.bat help
```

### 🔍 Features
- **Dependency checking** (Python, Docker)
- **Simple service startup** - no complex loops
- **Process management** with taskkill
- **Log file management** in `logs/` directory
- **Error handling** and user prompts
- **Docker support** for containerized deployment

## ⚙️ Method 4: Individual Service Scripts

### 🚀 Mac/Linux Individual Scripts

```bash
# Jira Mock
cd mock-services/jira-mock
./start.sh                    # Port 4001

# TestRail Mock  
cd mock-services/testrail-mock
./start.sh                    # Port 4002

# Slack Mock
cd mock-services/slack-mock
./start.sh                    # Port 4003
```

### 🪟 Windows Individual Scripts

```cmd
# Jira Mock
cd mock-services\jira-mock
start.bat

# TestRail Mock
cd mock-services\testrail-mock
start.bat

# Slack Mock
cd mock-services\slack-mock
start.bat
```

## 🐍 Method 5: Direct Python Execution

### 🚀 Usage

```bash
# Install dependencies for each service
cd mock-services/jira-mock && pip install -r requirements.txt
cd ../testrail-mock && pip install -r requirements.txt
cd ../slack-mock && pip install -r requirements.txt

# Start services directly
cd mock-services/jira-mock && python app.py &
cd ../testrail-mock && python app.py &
cd ../slack-mock && python app_simple.py &
```

## 📊 Service Status Monitoring

### 🔍 Health Check Commands

```bash
# Check all services
curl http://localhost:4001/health  # Jira
curl http://localhost:4002/health  # TestRail  
curl http://localhost:4003/health  # Slack

# One-liner health check
curl -s http://localhost:4001/health && curl -s http://localhost:4002/health && curl -s http://localhost:4003/health && echo "All services healthy!"
```

### 📱 Access URLs

| Service | Web UI | API Docs | Health Check |
|---------|--------|----------|--------------|
| **Jira Mock** | http://localhost:4001/ui | http://localhost:4001/docs | http://localhost:4001/health |
| **TestRail Mock** | http://localhost:4002/ui | http://localhost:4002/docs | http://localhost:4002/health |
| **Slack Mock** | http://localhost:4003/ui | http://localhost:4003/docs | http://localhost:4003/health |

## 🛠️ Troubleshooting

### 🔧 Common Issues

#### Port Already in Use
```bash
# Check what's using the ports
lsof -i :4001 -i :4002 -i :4003

# Kill processes on specific port
sudo kill -9 $(lsof -ti:4001)

# Or use the stop scripts
./stop-all.sh --force
```

#### Docker Issues
```bash
# Reset Docker environment
docker compose down -v
docker system prune -f
docker compose up -d --build

# Check Docker logs
docker compose logs --tail=50 -f
```

#### Python/Dependencies Issues
```bash
# Reinstall dependencies
cd mock-services/jira-mock
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Windows Batch File Issues
```cmd
# If you get "was unexpected at this time" errors:
# Make sure you're using the correct batch files:
start-all.bat          # ✅ Working (simplified version)
stop-all.bat           # ✅ Working (simplified version)

# NOT these (they were removed due to delayed expansion issues):
# start-all-fixed.bat  # ❌ Removed
# start-all-simple.bat # ❌ Renamed to start-all.bat
```

### 📋 Debug Information

#### View Logs
```bash
# Docker logs
docker compose logs -f [service-name]

# Local logs (when using scripts)
tail -f logs/*.log

# Individual service logs
tail -f logs/jira-mock.log
tail -f logs/testrail-mock.log
tail -f logs/slack-mock.log
```

#### Check Process Status
```bash
# Linux/Mac
ps aux | grep -E "(uvicorn|python.*app)"

# Windows
tasklist | findstr python
```

## 🎯 Recommended Workflows

### 👨‍🎓 For Students/Learning
```bash
# Easy one-command startup
./start-all.sh

# Access web interfaces to explore
open http://localhost:4001/ui  # Jira
open http://localhost:4002/ui  # TestRail
open http://localhost:4003/ui  # Slack

# Stop when done
./stop-all.sh
```

### 👨‍💻 For Development
```bash
# Individual services for debugging
cd mock-services/jira-mock && ./start.sh
# Make changes, test, restart as needed

# Or use Docker for consistency
docker compose up -d --build
docker compose logs -f jira-mock
```

### 🏢 For Production/Demo
```bash
# Use Docker Compose for reliability
docker compose up -d --build

# Monitor health
watch -n 5 'curl -s http://localhost:4001/health && curl -s http://localhost:4002/health && curl -s http://localhost:4003/health'

# Graceful shutdown
docker compose down
```

## 📚 Additional Resources

- **Main README**: [readme.md](readme.md) - Complete project overview
- **Individual Service Docs**:
  - [Jira Mock README](mock-services/jira-mock/README.md)
  - [TestRail Mock README](mock-services/testrail-mock/README.md)
  - [Slack Mock README](mock-services/slack-mock/README.md)
- **Docker Compose**: [docker-compose.yml](docker-compose.yml) - Container orchestration
- **Postman Collections**: Each service includes API testing collections

---

**Choose the method that best fits your needs and environment!** 🚀
