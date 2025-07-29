@echo off
title BFI Signals AI Dashboard
color 0E

:restart
cls
echo.
echo ==========================================
echo   BFI Signals AI Dashboard Launcher
echo   Advanced Trading Signal Intelligence  
echo ==========================================
echo.
:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    echo.
    pause
    exit /b 1
)
:: Check if core directory exists
if not exist "core\" (
    echo ❌ Error: 'core' directory not found!
    echo Make sure you're running this from the project root directory.
    echo.
    pause
    exit /b 1
)
:: Check if dashboard.py exists
if not exist "core\dashboard.py" (
    echo ❌ Error: 'dashboard.py' not found in core directory!
    echo.
    pause
    exit /b 1
)
echo System check passed
echo.
:: Try to use virtual environment if it exists
if exist "venv\Scripts\python.exe" (
    echo Using virtual environment Python
    set PYTHON_CMD=..\venv\Scripts\python.exe
) else (
    echo Using system Python
    set PYTHON_CMD=python
)
echo Starting BFI Signals Dashboard...
echo.
echo Dashboard will be available at: http://127.0.0.1:5000
echo Press Ctrl+C to stop the dashboard
echo Press Ctrl+R to restart the dashboard
echo ==========================================
echo.
:: Set environment variable for cleaner output
set FLASK_DEBUG=false
:: Change to core directory and start dashboard
cd core

:: Start dashboard with restart monitoring
:run_dashboard
echo Starting dashboard process...
start /b "" %PYTHON_CMD% dashboard.py
set DASHBOARD_PID=%!

:: Monitor for Ctrl+R (using choice command for input detection)
:monitor_input
choice /c RC /n /t 1 /d C /m "" >nul 2>&1
if errorlevel 2 (
    :: 'C' was pressed or timeout - check if dashboard is still running
    tasklist /fi "imagename eq python.exe" 2>nul | find /i "python.exe" >nul
    if errorlevel 1 (
        echo.
        echo Dashboard process ended unexpectedly
        goto end_dashboard
    )
    goto monitor_input
)
if errorlevel 1 (
    :: 'R' was pressed - restart dashboard
    echo.
    echo Restarting dashboard...
    taskkill /f /im python.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    cd ..
    goto restart
)

:end_dashboard
cd ..
:: Handle exit
echo.
echo ==========================================
echo Dashboard stopped
echo.
echo Options:
echo [R] Restart Dashboard
echo [Q] Quit
echo ==========================================
choice /c RQ /n /m "Press R to restart or Q to quit: "
if errorlevel 2 goto quit
if errorlevel 1 goto restart

:quit
echo Thank you for using BFI Signals! 👋
echo ==========================================
echo.
pause