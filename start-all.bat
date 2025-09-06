@echo off
REM =============================================================================
REM Mock Services - Start All Services Script (Windows)
REM =============================================================================
REM 
REM This script starts all three mock services (Jira, TestRail, Slack) locally
REM for development and testing purposes.
REM
REM Usage:
REM   start-all.bat                    Start all services
REM   start-all.bat docker            Use Docker Compose instead
REM   start-all.bat help              Show help
REM
REM Services:
REM   - Jira Mock:     http://localhost:4001/ui
REM   - TestRail Mock: http://localhost:4002/ui  
REM   - Slack Mock:    http://localhost:4003/ui
REM
REM =============================================================================

setlocal enabledelayedexpansion

REM Configuration
set "BASE_DIR=mock-services"
set "LOG_DIR=logs"

REM Create logs directory
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Parse command line arguments
set "MODE=%1"
if "%MODE%"=="" set "MODE=local"

goto :main

:print_banner
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    🚀 Mock Services Launcher                 ║
echo ║                                                              ║
echo ║  🎫 Jira Mock     - Issue Management      (Port 4001)       ║
echo ║  🧪 TestRail Mock - Test Case Management  (Port 4002)       ║
echo ║  💬 Slack Mock    - Team Communication    (Port 4003)       ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
goto :eof

:show_help
call :print_banner
echo Usage:
echo   start-all.bat                    Start all services locally
echo   start-all.bat docker            Use Docker Compose
echo   start-all.bat help              Show this help
echo.
echo Examples:
echo   start-all.bat                    # Local development mode
echo   start-all.bat docker            # Container mode
echo.
echo Access URLs:
echo   Jira Mock:     http://localhost:4001/ui
echo   TestRail Mock: http://localhost:4002/ui
echo   Slack Mock:    http://localhost:4003/ui
echo.
echo Stop Services:
echo   stop-all.bat                     # Stop local services
echo   docker compose down              # Stop Docker services
goto :eof

:check_dependencies
echo 🔍 Checking dependencies...

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not installed
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)

REM Check pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip is required but not installed
    pause
    exit /b 1
)

echo ✅ Dependencies check passed
goto :eof

:check_ports
echo 🔍 Checking port availability...

REM Check if ports are in use (Windows netstat)
for %%p in (4001 4002 4003) do (
    netstat -an | find "LISTENING" | find ":%%p " >nul 2>&1
    if not errorlevel 1 (
        echo ⚠️  Port %%p is already in use
        echo    You may need to stop existing services first
    )
)
goto :eof

:start_docker_services
echo 🐳 Starting services with Docker Compose...

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is required but not installed
    echo Please install Docker Desktop from https://docker.com
    pause
    exit /b 1
)

REM Start services
docker compose up -d --build
if errorlevel 1 (
    echo ❌ Failed to start Docker services
    pause
    exit /b 1
)

echo ✅ Docker services started successfully!
echo.
call :show_access_urls
echo.
echo 📋 Useful Docker commands:
echo   docker compose logs -f           # View logs
echo   docker compose ps               # Check status
echo   docker compose down             # Stop services
goto :eof

:start_local_services
echo 🔧 Starting services locally...

call :check_dependencies
call :check_ports

REM Services to start
set "services=jira-mock testrail-mock slack-mock"
set "ports=4001 4002 4003"

REM Start each service
set /a index=0
for %%s in (%services%) do (
    set /a index+=1
    for /f "tokens=!index!" %%p in ("%ports%") do (
        echo 🚀 Starting %%s on port %%p...
        
        REM Navigate to service directory
        cd "%BASE_DIR%\%%s"
        
        REM Start service in background
        start /b "%%s" cmd /c "start.bat > ..\..\%LOG_DIR%\%%s.log 2>&1"
        
        REM Return to root directory
        cd ..\..
        
        REM Wait for service to start
        timeout /t 3 /nobreak >nul
        
        REM Check if service is responding
        curl -s -f "http://localhost:%%p/health" >nul 2>&1
        if not errorlevel 1 (
            echo ✅ %%s started successfully
        ) else (
            echo ⚠️  %%s may still be starting...
        )
    )
)

echo.
echo 🎉 All services started!
echo.
call :show_access_urls
echo.
call :show_management_info
goto :eof

:show_access_urls
echo 🌐 Service Access URLs:
echo ┌─────────────────┬─────────────────────────────────────────┐
echo │ Service         │ URL                                     │
echo ├─────────────────┼─────────────────────────────────────────┤
echo │ 🎫 Jira Mock    │ http://localhost:4001/ui                │
echo │ 🧪 TestRail Mock│ http://localhost:4002/ui                │
echo │ 💬 Slack Mock   │ http://localhost:4003/ui                │
echo │ 📚 API Docs     │ http://localhost:400[1-3]/docs          │
echo │ 🏥 Health Check │ http://localhost:400[1-3]/health        │
echo └─────────────────┴─────────────────────────────────────────┘
goto :eof

:show_management_info
echo 📋 Service Management:
echo   stop-all.bat                     # Stop all services
echo   type logs\*.log                  # View logs
echo   start-all.bat docker            # Use Docker instead
echo.
echo 📁 Log Files:
echo   logs\jira-mock.log               # Jira service logs
echo   logs\testrail-mock.log           # TestRail service logs  
echo   logs\slack-mock.log              # Slack service logs
goto :eof

:main
call :print_banner

if "%MODE%"=="docker" (
    call :start_docker_services
) else if "%MODE%"=="help" (
    call :show_help
) else if "%MODE%"=="local" (
    call :start_local_services
) else (
    echo ❌ Unknown option: %MODE%
    echo Use "help" for usage information
    pause
    exit /b 1
)

echo.
echo Press any key to exit...
pause >nul
