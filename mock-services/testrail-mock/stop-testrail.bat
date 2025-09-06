@echo off
REM Stop script for TestRail Mock Service (Windows)

echo 🛑 Stopping TestRail Mock Service...

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
    goto :stop_service
)

where podman >nul 2>&1
if %errorlevel% == 0 (
    set CONTAINER_CMD=podman
    goto :stop_service
)

echo ❌ Error: Neither docker nor podman found.
exit /b 1

:stop_service
REM Stop the service
%CONTAINER_CMD% compose down

echo ✅ TestRail Mock Service stopped successfully!
