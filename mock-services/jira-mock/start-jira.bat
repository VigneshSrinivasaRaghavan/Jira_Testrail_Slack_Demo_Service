@echo off
REM Quick start script for Jira Mock Service (Windows - from repo root)

echo 🚀 Starting Jira Mock Service with Docker/Podman...

REM Navigate to repo root (two levels up from jira-mock folder)
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
echo 🔧 Building and starting Jira Mock...
%CONTAINER_CMD% compose up -d --build jira-mock

REM Wait a moment for startup
timeout /t 3 /nobreak >nul

REM Check if service is running (simplified check for Windows)
%CONTAINER_CMD% compose ps jira-mock >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Jira Mock Service started successfully!
    echo.
    echo 🌐 Access URLs:
    echo    - UI: http://localhost:4001/ui
    echo    - API Docs: http://localhost:4001/docs
    echo    - Health: http://localhost:4001/health
    echo.
    echo 📋 Useful commands:
    echo    - View logs: %CONTAINER_CMD% compose logs -f jira-mock
    echo    - Stop service: %CONTAINER_CMD% compose down
    echo    - Restart: %CONTAINER_CMD% compose restart jira-mock
    echo.
) else (
    echo ❌ Failed to start Jira Mock Service
    echo 📋 Check logs: %CONTAINER_CMD% compose logs jira-mock
    exit /b 1
)
