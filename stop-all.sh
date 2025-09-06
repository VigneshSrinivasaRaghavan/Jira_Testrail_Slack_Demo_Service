#!/bin/bash

# =============================================================================
# Mock Services - Stop All Services Script (Mac/Linux)
# =============================================================================
# 
# This script stops all running mock services (Jira, TestRail, Slack) that
# were started locally using start-all.sh
#
# Usage:
#   ./stop-all.sh                     # Stop local services
#   ./stop-all.sh --docker           # Stop Docker services
#   ./stop-all.sh --force            # Force kill all services
#   ./stop-all.sh --help             # Show help
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
SERVICES=("jira-mock" "testrail-mock" "slack-mock")
LOG_DIR="logs"

print_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🛑 Mock Services Stopper                  ║"
    echo "║                                                              ║"
    echo "║  Stopping all running mock services...                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

show_help() {
    print_banner
    echo -e "${CYAN}Usage:${NC}"
    echo "  ./stop-all.sh                     Stop local services gracefully"
    echo "  ./stop-all.sh --docker           Stop Docker Compose services"
    echo "  ./stop-all.sh --force            Force kill all services"
    echo "  ./stop-all.sh --help             Show this help"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo "  ./stop-all.sh                     # Normal shutdown"
    echo "  ./stop-all.sh --docker           # Stop Docker containers"
    echo "  ./stop-all.sh --force            # Emergency shutdown"
}

stop_docker_services() {
    echo -e "${BLUE}🐳 Stopping Docker Compose services...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi
    
    # Stop and remove containers
    docker compose down
    
    echo -e "${GREEN}✅ Docker services stopped successfully!${NC}"
}

stop_local_services() {
    echo -e "${BLUE}🛑 Stopping local services...${NC}"
    
    local stopped_count=0
    
    # Stop services using PID files
    for service in "${SERVICES[@]}"; do
        pid_file="$LOG_DIR/$service.pid"
        
        if [[ -f "$pid_file" ]]; then
            pid=$(cat "$pid_file")
            
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${YELLOW}🛑 Stopping $service (PID: $pid)...${NC}"
                kill "$pid"
                
                # Wait for graceful shutdown
                local count=0
                while kill -0 "$pid" 2>/dev/null && [[ $count -lt 10 ]]; do
                    sleep 1
                    ((count++))
                done
                
                if kill -0 "$pid" 2>/dev/null; then
                    echo -e "${YELLOW}⚠️  Force killing $service...${NC}"
                    kill -9 "$pid" 2>/dev/null || true
                fi
                
                echo -e "${GREEN}✅ $service stopped${NC}"
                ((stopped_count++))
            else
                echo -e "${YELLOW}⚠️  $service was not running (stale PID file)${NC}"
            fi
            
            # Remove PID file
            rm -f "$pid_file"
        else
            echo -e "${YELLOW}⚠️  No PID file found for $service${NC}"
        fi
    done
    
    # Also try to kill by process name (backup method)
    echo -e "${BLUE}🔍 Checking for any remaining processes...${NC}"
    
    local processes_killed=0
    
    # Kill uvicorn processes on our ports
    for port in 4001 4002 4003; do
        local pids=$(lsof -ti:$port 2>/dev/null || true)
        if [[ -n "$pids" ]]; then
            echo -e "${YELLOW}🛑 Killing processes on port $port...${NC}"
            echo "$pids" | xargs kill -TERM 2>/dev/null || true
            sleep 2
            echo "$pids" | xargs kill -9 2>/dev/null || true
            ((processes_killed++))
        fi
    done
    
    # Kill any remaining uvicorn processes related to our services
    pkill -f "uvicorn.*app:app" 2>/dev/null || true
    pkill -f "python.*app.py" 2>/dev/null || true
    pkill -f "start_simple.py" 2>/dev/null || true
    
    echo ""
    if [[ $stopped_count -gt 0 ]] || [[ $processes_killed -gt 0 ]]; then
        echo -e "${GREEN}🎉 Services stopped successfully!${NC}"
        echo -e "${GREEN}   Stopped $stopped_count services via PID files${NC}"
        if [[ $processes_killed -gt 0 ]]; then
            echo -e "${GREEN}   Killed $processes_killed additional processes${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  No running services found${NC}"
    fi
}

force_stop_services() {
    echo -e "${RED}💥 Force stopping all services...${NC}"
    
    # Kill all processes on our ports
    for port in 4001 4002 4003; do
        local pids=$(lsof -ti:$port 2>/dev/null || true)
        if [[ -n "$pids" ]]; then
            echo -e "${RED}💥 Force killing processes on port $port...${NC}"
            echo "$pids" | xargs kill -9 2>/dev/null || true
        fi
    done
    
    # Kill any Python processes that might be our services
    pkill -9 -f "uvicorn.*app:app" 2>/dev/null || true
    pkill -9 -f "python.*app.py" 2>/dev/null || true
    pkill -9 -f "start_simple.py" 2>/dev/null || true
    
    # Clean up PID files
    rm -f "$LOG_DIR"/*.pid 2>/dev/null || true
    
    echo -e "${GREEN}✅ Force stop completed${NC}"
}

check_status() {
    echo -e "${BLUE}🔍 Checking service status...${NC}"
    
    local running_services=0
    
    for port in 4001 4002 4003; do
        if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
            case $port in
                4001) service_name="Jira Mock" ;;
                4002) service_name="TestRail Mock" ;;
                4003) service_name="Slack Mock" ;;
            esac
            echo -e "${YELLOW}⚠️  $service_name is still running on port $port${NC}"
            ((running_services++))
        fi
    done
    
    if [[ $running_services -eq 0 ]]; then
        echo -e "${GREEN}✅ All services are stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  $running_services services are still running${NC}"
        echo -e "${CYAN}💡 Try: ./stop-all.sh --force${NC}"
    fi
}

cleanup_logs() {
    echo -e "${BLUE}🧹 Cleaning up log files...${NC}"
    
    if [[ -d "$LOG_DIR" ]]; then
        # Archive old logs
        local timestamp=$(date +%Y%m%d_%H%M%S)
        if ls "$LOG_DIR"/*.log 1> /dev/null 2>&1; then
            mkdir -p "$LOG_DIR/archive"
            for log_file in "$LOG_DIR"/*.log; do
                if [[ -f "$log_file" ]]; then
                    mv "$log_file" "$LOG_DIR/archive/$(basename "$log_file" .log)_$timestamp.log"
                fi
            done
            echo -e "${GREEN}✅ Log files archived${NC}"
        fi
        
        # Remove PID files
        rm -f "$LOG_DIR"/*.pid 2>/dev/null || true
    fi
}

# Main execution
case "${1:-}" in
    --docker)
        print_banner
        stop_docker_services
        ;;
    --force)
        print_banner
        force_stop_services
        check_status
        ;;
    --help|-h)
        show_help
        ;;
    "")
        print_banner
        stop_local_services
        check_status
        cleanup_logs
        ;;
    *)
        echo -e "${RED}❌ Unknown option: $1${NC}"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
