@echo off
REM Quick start script for TestRail Mock Service (Windows - local development)

echo 🚀 Starting TestRail Mock Service...

REM Check if we're in the right directory
if not exist "app.py" (
    echo ❌ Error: Please run this script from the testrail-mock directory
    echo    cd mock-services\testrail-mock
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
echo    Installing FastAPI and dependencies (this may take a moment)...
pip install -r requirements.txt

REM Start the server
echo ✅ Starting TestRail Mock on http://localhost:4002
echo    - UI Dashboard: http://localhost:4002/ui
echo    - Test Cases: http://localhost:4002/ui/cases
echo    - API Docs: http://localhost:4002/docs
echo    - Health: http://localhost:4002/health
echo.
echo 🧪 Sample test data loaded:
echo    - 5 test sections (Authentication, User Management, API Tests, UI Tests, Integration)
echo    - 18 sample test cases with steps and results
echo    - 1 test run with execution history
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn app:app --host 0.0.0.0 --port 4002 --reload
