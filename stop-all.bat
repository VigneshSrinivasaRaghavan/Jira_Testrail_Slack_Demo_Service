@echo off
REM Simple Mock Services Stopper for Windows
REM Stops all running mock services without complex variable expansion

echo ===============================================================
echo                   Mock Services Stopper                     
echo                                                               
echo  Stopping all running mock services...                      
echo ===============================================================
echo.

REM Check if Docker mode requested
if "%1"=="docker" goto docker_mode
if "%1"=="help" goto show_help
if "%1"=="force" goto force_mode

REM Local mode (default)
echo Stopping local services...
echo.

REM Kill processes by port using simple approach
echo Stopping Jira Mock on port 4001...
for /f "tokens=5" %%a in ('netstat -ano ^| find ":4001 "') do (
    taskkill /PID %%a /F >nul 2>&1
    if not errorlevel 1 echo   Process %%a stopped
)

echo Stopping TestRail Mock on port 4002...
for /f "tokens=5" %%a in ('netstat -ano ^| find ":4002 "') do (
    taskkill /PID %%a /F >nul 2>&1
    if not errorlevel 1 echo   Process %%a stopped
)

echo Stopping Slack Mock on port 4003...
for /f "tokens=5" %%a in ('netstat -ano ^| find ":4003 "') do (
    taskkill /PID %%a /F >nul 2>&1
    if not errorlevel 1 echo   Process %%a stopped
)

REM Also kill Python processes that might be our services
echo Checking for any remaining Python processes...
tasklist /FI "IMAGENAME eq python.exe" /FO CSV | find "python.exe" >nul 2>&1
if not errorlevel 1 (
    echo Stopping Python processes...
    taskkill /IM python.exe /F >nul 2>&1
)

tasklist /FI "IMAGENAME eq pythonw.exe" /FO CSV | find "pythonw.exe" >nul 2>&1
if not errorlevel 1 (
    echo Stopping Python background processes...
    taskkill /IM pythonw.exe /F >nul 2>&1
)

echo.
echo Services stopped successfully!
goto end

:docker_mode
echo Stopping Docker Compose services...

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not installed
    pause
    exit /b 1
)

REM Stop and remove containers
docker compose down
if errorlevel 1 (
    echo Failed to stop Docker services
    pause
    exit /b 1
)

echo Docker services stopped successfully!
goto end

:force_mode
echo Force stopping all services...

REM Force kill all processes on our ports
for /f "tokens=5" %%a in ('netstat -ano ^| find ":4001 "') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| find ":4002 "') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| find ":4003 "') do taskkill /PID %%a /F >nul 2>&1

REM Kill any Python processes
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM pythonw.exe /F >nul 2>&1

echo Force stop completed
goto end

:show_help
echo Usage:
echo   stop-all-simple.bat             Stop all services locally
echo   stop-all-simple.bat docker     Stop Docker Compose services
echo   stop-all-simple.bat force      Force kill all services
echo   stop-all-simple.bat help       Show this help
echo.
echo Examples:
echo   stop-all-simple.bat             # Normal shutdown
echo   stop-all-simple.bat docker     # Stop Docker containers
echo   stop-all-simple.bat force      # Emergency shutdown
echo.
pause >nul

:end
