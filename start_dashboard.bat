@echo off
title BFI Signals AI Dashboard
color 0E

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

echo ✅ System check passed
echo.

:: Try to use virtual environment if it exists
if exist "venv\Scripts\python.exe" (
    echo 📍 Using virtual environment Python
    set PYTHON_CMD=..\venv\Scripts\python.exe
) else (
    echo 📍 Using system Python
    set PYTHON_CMD=python
)

echo 🚀 Starting BFI Signals Dashboard...
echo.
echo 📱 Dashboard will be available at: http://127.0.0.1:5000
echo 🛑 Press Ctrl+C to stop the dashboard
echo ==========================================
echo.

:: Set environment variable for cleaner output
set FLASK_DEBUG=false

:: Change to core directory and start dashboard
cd core
%PYTHON_CMD% dashboard.py

:: Handle exit
echo.
echo ==========================================
echo 🛑 Dashboard stopped
echo Thank you for using BFI Signals! 👋
echo ==========================================
echo.
pause 