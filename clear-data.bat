@echo off
REM Clear Local Data Script for Mock Services (Windows)
REM This script clears all local data from Jira, Slack, and TestRail mock services

echo 🧹 Clearing local data from all mock services...

REM Remove database files
echo 📂 Removing database files...
if exist "mock-services\jira-mock\jira.db" del /f "mock-services\jira-mock\jira.db"
if exist "mock-services\slack-mock\slack_mock.db" del /f "mock-services\slack-mock\slack_mock.db"
if exist "mock-services\testrail-mock\testrail.db" del /f "mock-services\testrail-mock\testrail.db"

REM Remove Python cache directories
echo 🐍 Removing Python cache directories...
if exist "mock-services\jira-mock\__pycache__" rmdir /s /q "mock-services\jira-mock\__pycache__"
if exist "mock-services\slack-mock\__pycache__" rmdir /s /q "mock-services\slack-mock\__pycache__"
if exist "mock-services\testrail-mock\__pycache__" rmdir /s /q "mock-services\testrail-mock\__pycache__"

REM Clear data directory (if it has files)
echo 📁 Clearing Slack data directory...
if exist "mock-services\slack-mock\data\*" del /f /q "mock-services\slack-mock\data\*"

REM Remove log files and PID files
echo 📝 Removing log files...
if exist "logs\*.log" del /f /q "logs\*.log"
if exist "logs\*.pid" del /f /q "logs\*.pid"
if exist "logs\archive\*.log" del /f /q "logs\archive\*.log"

echo ✅ All local data cleared successfully!
echo.
echo Note: When you restart the services, they will:
echo - Recreate empty databases
echo - Load fresh seed/sample data
echo - Start with clean logs
echo.
echo To restart all services, run:
echo   start-all.bat
echo.
pause