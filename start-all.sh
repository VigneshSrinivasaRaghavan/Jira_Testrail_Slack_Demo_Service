#!/bin/bash

# =============================================================================
# Mock Services - Start All Services Script (Mac/Linux)
# =============================================================================
# 
# This script starts all three mock services (Jira, TestRail, Slack) locally
# for development and testing purposes.
#
# Usage:
#   ./start-all.sh                    # Start all services
#   ./start-all.sh --docker          # Use Docker Compose instead
#   ./start-all.sh --help            # Show help
#
# Services:
#   - Jira Mock:     http://localhost:4001/ui
#   - TestRail Mock: http://localhost:4002/ui  
#   - Slack Mock:    http://localhost:4003/ui
#
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SERVICES=("jira-mock:4001" "testrail-mock:4002" "slack-mock:4003")
BASE_DIR="mock-services"
LOG_DIR="logs"

# Create logs directory
mkdir -p "$LOG_DIR"

print_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🚀 Mock Services Launcher                 ║"
    echo "║                                                              ║"
    echo "║  🎫 Jira Mock     - Issue Management      (Port 4001)       ║"
    echo "║  🧪 TestRail Mock - Test Case Management  (Port 4002)       ║"
    echo "║  💬 Slack Mock    - Team Communication    (Port 4003)       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

show_help() {
    print_banner
    echo -e "${CYAN}Usage:${NC}"
    echo "  ./start-all.sh                    Start all services locally"
    echo "  ./start-all.sh --docker          Use Docker Compose"
    echo "  ./start-all.sh --help            Show this help"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo "  ./start-all.sh                    # Local development mode"
    echo "  ./start-all.sh --docker          # Container mode"
    echo ""
    echo -e "${CYAN}Access URLs:${NC}"
    echo "  Jira Mock:     http://localhost:4001/ui"
    echo "  TestRail Mock: http://localhost:4002/ui"
    echo "  Slack Mock:    http://localhost:4003/ui"
    echo ""
    echo -e "${CYAN}Stop Services:${NC}"
    echo "  ./stop-all.sh                     # Stop local services"
    echo "  docker compose down               # Stop Docker services"
}

check_dependencies() {
    echo -e "${BLUE}🔍 Checking dependencies...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is required but not installed${NC}"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        echo -e "${RED}❌ pip is required but not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Dependencies check passed${NC}"
}

check_ports() {
    echo -e "${BLUE}🔍 Checking port availability...${NC}"
    
    for service in "${SERVICES[@]}"; do
        port=${service##*:}
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  Port $port is already in use${NC}"
            echo -e "${YELLOW}   You may need to stop existing services first${NC}"
        fi
    done
}

start_docker_services() {
    echo -e "${BLUE}🐳 Starting services with Docker Compose...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is required but not installed${NC}"
        exit 1
    fi
    
    # Start services
    docker compose up -d --build
    
    echo -e "${GREEN}✅ Docker services started successfully!${NC}"
    echo ""
    show_access_urls
    echo ""
    echo -e "${CYAN}📋 Useful Docker commands:${NC}"
    echo "  docker compose logs -f           # View logs"
    echo "  docker compose ps               # Check status"
    echo "  docker compose down             # Stop services"
}

start_local_services() {
    echo -e "${BLUE}🔧 Starting services locally...${NC}"
    
    check_dependencies
    check_ports
    
    # Start each service
    for service in "${SERVICES[@]}"; do
        service_name=${service%%:*}
        port=${service##*:}
        
        echo -e "${YELLOW}🚀 Starting $service_name on port $port...${NC}"
        
        cd "$BASE_DIR/$service_name"
        
        # Make start script executable
        chmod +x start.sh
        
        # Start service in background and redirect output to log
        nohup ./start.sh > "../../$LOG_DIR/$service_name.log" 2>&1 &
        
        # Store PID for later cleanup
        echo $! > "../../$LOG_DIR/$service_name.pid"
        
        cd - > /dev/null
        
        # Wait a moment for service to start
        sleep 2
        
        # Check if service is responding
        if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name started successfully${NC}"
        else
            echo -e "${YELLOW}⚠️  $service_name may still be starting...${NC}"
        fi
    done
    
    echo ""
    echo -e "${GREEN}🎉 All services started!${NC}"
    echo ""
    show_access_urls
    echo ""
    show_management_info
}

show_access_urls() {
    echo -e "${CYAN}🌐 Service Access URLs:${NC}"
    echo "┌─────────────────┬─────────────────────────────────────────┐"
    echo "│ Service         │ URL                                     │"
    echo "├─────────────────┼─────────────────────────────────────────┤"
    echo "│ 🎫 Jira Mock    │ http://localhost:4001/ui                │"
    echo "│ 🧪 TestRail Mock│ http://localhost:4002/ui                │"
    echo "│ 💬 Slack Mock   │ http://localhost:4003/ui                │"
    echo "│ 📚 API Docs     │ http://localhost:400[1-3]/docs          │"
    echo "│ 🏥 Health Check │ http://localhost:400[1-3]/health        │"
    echo "└─────────────────┴─────────────────────────────────────────┘"
}

show_management_info() {
    echo -e "${CYAN}📋 Service Management:${NC}"
    echo "  ./stop-all.sh                    # Stop all services"
    echo "  tail -f logs/*.log               # View logs"
    echo "  ./start-all.sh --docker         # Use Docker instead"
    echo ""
    echo -e "${CYAN}📁 Log Files:${NC}"
    echo "  logs/jira-mock.log               # Jira service logs"
    echo "  logs/testrail-mock.log           # TestRail service logs"  
    echo "  logs/slack-mock.log              # Slack service logs"
}

# Main execution
case "${1:-}" in
    --docker)
        print_banner
        start_docker_services
        ;;
    --help|-h)
        show_help
        ;;
    "")
        print_banner
        start_local_services
        ;;
    *)
        echo -e "${RED}❌ Unknown option: $1${NC}"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
