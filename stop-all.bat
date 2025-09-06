@echo off
REM =============================================================================
REM Mock Services - Stop All Services Script (Windows)
REM =============================================================================
REM 
REM This script stops all running mock services (Jira, TestRail, Slack) that
REM were started locally using start-all.bat
REM
REM Usage:
REM   stop-all.bat                     Stop local services
REM   stop-all.bat docker             Stop Docker services
REM   stop-all.bat force              Force kill all services
REM   stop-all.bat help               Show help
REM
REM =============================================================================

setlocal enabledelayedexpansion

REM Configuration
set "LOG_DIR=logs"

REM Parse command line arguments
set "MODE=%1"
if "%MODE%"=="" set "MODE=local"

goto :main

:print_banner
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    🛑 Mock Services Stopper                  ║
echo ║                                                              ║
echo ║  Stopping all running mock services...                      ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
goto :eof

:show_help
call :print_banner
echo Usage:
echo   stop-all.bat                     Stop local services gracefully
echo   stop-all.bat docker             Stop Docker Compose services
echo   stop-all.bat force              Force kill all services
echo   stop-all.bat help               Show this help
echo.
echo Examples:
echo   stop-all.bat                     # Normal shutdown
echo   stop-all.bat docker             # Stop Docker containers
echo   stop-all.bat force              # Emergency shutdown
goto :eof

:stop_docker_services
echo 🐳 Stopping Docker Compose services...

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed
    pause
    exit /b 1
)

REM Stop and remove containers
docker compose down
if errorlevel 1 (
    echo ❌ Failed to stop Docker services
    pause
    exit /b 1
)

echo ✅ Docker services stopped successfully!
goto :eof

:stop_local_services
echo 🛑 Stopping local services...

set /a stopped_count=0

REM Kill processes by port
for %%p in (4001 4002 4003) do (
    echo 🛑 Checking port %%p...
    
    REM Find processes using the port
    for /f "tokens=5" %%a in ('netstat -ano ^| find ":%%p "') do (
        set "pid=%%a"
        if defined pid (
            echo 🛑 Killing process !pid! on port %%p...
            taskkill /PID !pid! /F >nul 2>&1
            if not errorlevel 1 (
                set /a stopped_count+=1
                echo ✅ Process !pid! stopped
            )
        )
    )
)

REM Also kill by process name (backup method)
echo 🔍 Checking for any remaining processes...

REM Kill Python processes that might be our services
tasklist /FI "IMAGENAME eq python.exe" /FO CSV | find "python.exe" >nul 2>&1
if not errorlevel 1 (
    echo 🛑 Stopping Python processes...
    taskkill /IM python.exe /F >nul 2>&1
)

tasklist /FI "IMAGENAME eq pythonw.exe" /FO CSV | find "pythonw.exe" >nul 2>&1
if not errorlevel 1 (
    echo 🛑 Stopping Python background processes...
    taskkill /IM pythonw.exe /F >nul 2>&1
)

echo.
if %stopped_count% gtr 0 (
    echo 🎉 Services stopped successfully!
    echo    Stopped %stopped_count% processes
) else (
    echo ⚠️  No running services found
)
goto :eof

:force_stop_services
echo 💥 Force stopping all services...

REM Kill all processes on our ports
for %%p in (4001 4002 4003) do (
    echo 💥 Force killing processes on port %%p...
    
    for /f "tokens=5" %%a in ('netstat -ano ^| find ":%%p "') do (
        taskkill /PID %%a /F >nul 2>&1
    )
)

REM Kill any Python processes that might be our services
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM pythonw.exe /F >nul 2>&1

REM Clean up log files
if exist "%LOG_DIR%" (
    del /Q "%LOG_DIR%\*.pid" >nul 2>&1
)

echo ✅ Force stop completed
goto :eof

:check_status
echo 🔍 Checking service status...

set /a running_services=0

for %%p in (4001 4002 4003) do (
    curl -s -f "http://localhost:%%p/health" >nul 2>&1
    if not errorlevel 1 (
        if %%p==4001 set "service_name=Jira Mock"
        if %%p==4002 set "service_name=TestRail Mock"
        if %%p==4003 set "service_name=Slack Mock"
        echo ⚠️  !service_name! is still running on port %%p
        set /a running_services+=1
    )
)

if %running_services%==0 (
    echo ✅ All services are stopped
) else (
    echo ⚠️  %running_services% services are still running
    echo 💡 Try: stop-all.bat force
)
goto :eof

:cleanup_logs
echo 🧹 Cleaning up log files...

if exist "%LOG_DIR%" (
    REM Archive old logs with timestamp
    for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
    set "timestamp=!dt:~0,8!_!dt:~8,6!"
    
    if not exist "%LOG_DIR%\archive" mkdir "%LOG_DIR%\archive"
    
    for %%f in ("%LOG_DIR%\*.log") do (
        if exist "%%f" (
            move "%%f" "%LOG_DIR%\archive\%%~nf_!timestamp!.log" >nul 2>&1
        )
    )
    
    echo ✅ Log files archived
    
    REM Remove any remaining files
    del /Q "%LOG_DIR%\*.pid" >nul 2>&1
)
goto :eof

:main
call :print_banner

if "%MODE%"=="docker" (
    call :stop_docker_services
) else if "%MODE%"=="force" (
    call :force_stop_services
    call :check_status
) else if "%MODE%"=="help" (
    call :show_help
) else if "%MODE%"=="local" (
    call :stop_local_services
    call :check_status
    call :cleanup_logs
) else (
    echo ❌ Unknown option: %MODE%
    echo Use "help" for usage information
    pause
    exit /b 1
)

echo.
echo Press any key to exit...
pause >nul
