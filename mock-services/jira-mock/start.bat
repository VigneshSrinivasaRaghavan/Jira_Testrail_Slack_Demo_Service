@echo off
REM Quick start script for Jira Mock Service (Windows - local development)

echo 🚀 Starting Jira Mock Service...

REM Check if we're in the right directory
if not exist "app.py" (
    echo ❌ Error: Please run this script from the jira-mock directory
    echo    cd mock-services\jira-mock
    echo    start.bat
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip and install dependencies
echo 📥 Installing dependencies...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

REM Start the server
echo ✅ Starting Jira Mock on http://localhost:4001
echo    - UI: http://localhost:4001/ui
echo    - API Docs: http://localhost:4001/docs
echo    - Health: http://localhost:4001/health
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn app:app --host 0.0.0.0 --port 4001 --reload
