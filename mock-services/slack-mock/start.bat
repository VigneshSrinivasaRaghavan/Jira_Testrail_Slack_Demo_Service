@echo off
REM Quick start script for Slack Mock Service (Windows - local development)

echo 🚀 Starting Slack Mock Service...

REM Check if we're in the right directory
if not exist "app.py" (
    echo ❌ Error: Please run this script from the slack-mock directory
    echo    cd mock-services\slack-mock
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
echo ✅ Starting Slack Mock on http://localhost:4003
echo    - UI: http://localhost:4003/ui
echo    - API Docs: http://localhost:4003/docs
echo    - Health: http://localhost:4003/health
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn app:app --host 0.0.0.0 --port 4003 --reload
