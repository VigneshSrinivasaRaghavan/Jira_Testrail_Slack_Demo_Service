@echo off
REM Simple Mock Services Launcher for Windows
REM Starts all three services without complex variable expansion

echo ===============================================================
echo                   Mock Services Launcher                     
echo                                                               
echo  Jira Mock     - Issue Management      (Port 4001)          
echo  TestRail Mock - Test Case Management  (Port 4002)          
echo  Slack Mock    - Team Communication    (Port 4003)          
echo ===============================================================
echo.

REM Check if Docker mode requested
if "%1"=="docker" goto docker_mode
if "%1"=="help" goto show_help

REM Local mode (default)
echo Starting services locally...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is required but not installed
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)

REM Create logs directory
if not exist "logs" mkdir "logs"

REM Start Jira Mock
echo Starting Jira Mock on port 4001...
cd mock-services\jira-mock
start /b "Jira Mock" cmd /c "start.bat > ..\..\logs\jira-mock.log 2>&1"
cd ..\..
timeout /t 3 /nobreak >nul

REM Start TestRail Mock
echo Starting TestRail Mock on port 4002...
cd mock-services\testrail-mock
start /b "TestRail Mock" cmd /c "start.bat > ..\..\logs\testrail-mock.log 2>&1"
cd ..\..
timeout /t 3 /nobreak >nul

REM Start Slack Mock
echo Starting Slack Mock on port 4003...
cd mock-services\slack-mock
start /b "Slack Mock" cmd /c "start.bat > ..\..\logs\slack-mock.log 2>&1"
cd ..\..
timeout /t 3 /nobreak >nul

echo.
echo All services started!
echo.
echo Service Access URLs:
echo   Jira Mock:     http://localhost:4001/ui
echo   TestRail Mock: http://localhost:4002/ui
echo   Slack Mock:    http://localhost:4003/ui
echo   API Docs:      http://localhost:400[1-3]/docs
echo   Health Check:  http://localhost:400[1-3]/health
echo.
echo Service Management:
echo   stop-all.bat                     # Stop all services
echo   type logs\*.log                  # View logs
echo.
echo Press any key to exit...
pause >nul
goto end

:docker_mode
echo Starting services with Docker Compose...

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is required but not installed
    echo Please install Docker Desktop from https://docker.com
    pause
    exit /b 1
)

REM Start services
docker compose up -d --build
if errorlevel 1 (
    echo Failed to start Docker services
    pause
    exit /b 1
)

echo Docker services started successfully!
echo.
echo Service Access URLs:
echo   Jira Mock:     http://localhost:4001/ui
echo   TestRail Mock: http://localhost:4002/ui
echo   Slack Mock:    http://localhost:4003/ui
echo.
echo Useful Docker commands:
echo   docker compose logs -f           # View logs
echo   docker compose ps               # Check status
echo   docker compose down             # Stop services
echo.
echo Press any key to exit...
pause >nul
goto end

:show_help
echo Usage:
echo   start-all-simple.bat             Start all services locally
echo   start-all-simple.bat docker     Use Docker Compose
echo   start-all-simple.bat help       Show this help
echo.
echo Examples:
echo   start-all-simple.bat             # Local development mode
echo   start-all-simple.bat docker     # Container mode
echo.
pause >nul

:end
