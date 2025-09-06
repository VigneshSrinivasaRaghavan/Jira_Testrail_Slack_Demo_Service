@echo off
REM Quick start script for TestRail Mock Service (Windows - from repo root)

echo 🚀 Starting TestRail Mock Service with Docker/Podman...

REM Navigate to repo root (two levels up from testrail-mock folder)
cd /d "%~dp0"
cd ..\..

REM Check if we're in the repo root
if not exist "docker-compose.yml" (
    echo ❌ Error: Could not find docker-compose.yml in repo root
    echo    Current directory: %CD%
    exit /b 1
)

REM Check if docker or podman is available
where docker >nul 2>&1
if %errorlevel% == 0 (
    set CONTAINER_CMD=docker
    goto :start_service
)

where podman >nul 2>&1
if %errorlevel% == 0 (
    set CONTAINER_CMD=podman
    goto :start_service
)

echo ❌ Error: Neither docker nor podman found. Please install Docker Desktop.
exit /b 1

:start_service
echo 📦 Using %CONTAINER_CMD% to start services...

REM Start the service
echo 🔧 Building and starting TestRail Mock...
%CONTAINER_CMD% compose up -d --build testrail-mock

REM Wait a moment for startup
timeout /t 3 /nobreak >nul

REM Check if service is running (simplified check for Windows)
%CONTAINER_CMD% compose ps testrail-mock >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ TestRail Mock Service started successfully!
    echo.
    echo 🌐 Access URLs:
    echo    - UI Dashboard: http://localhost:4002/ui
    echo    - Test Cases: http://localhost:4002/ui/cases
    echo    - API Docs: http://localhost:4002/docs
    echo    - Health: http://localhost:4002/health
    echo.
    echo 📋 Useful commands:
    echo    - View logs: %CONTAINER_CMD% compose logs -f testrail-mock
    echo    - Stop service: %CONTAINER_CMD% compose down
    echo    - Restart: %CONTAINER_CMD% compose restart testrail-mock
    echo.
    echo 🧪 Sample API calls:
    echo    - Get test cases: curl -H "Authorization: Bearer test-token" http://localhost:4002/api/v2/cases/1
    echo    - Add test result: curl -X POST -H "Authorization: Bearer test-token" -H "Content-Type: application/json" -d "{\"status_id\":1,\"comment\":\"Test passed\"}" http://localhost:4002/api/v2/results/1
    echo.
) else (
    echo ❌ Failed to start TestRail Mock Service
    echo 📋 Check logs: %CONTAINER_CMD% compose logs testrail-mock
    exit /b 1
)
