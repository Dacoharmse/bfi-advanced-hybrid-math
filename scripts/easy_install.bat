@echo off
title BFI Signals Easy Install
color 0A

echo.
echo ==========================================
echo   BFI Signals AI Dashboard - Easy Install
echo   Advanced Trading Signal Intelligence  
echo ==========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

:: Check if we're in the right directory
if not exist "core\" (
    echo ❌ Error: 'core' directory not found!
    echo Make sure you're running this from the BFI Signals project directory.
    echo.
    pause
    exit /b 1
)

echo ✅ Starting automated installation...
echo.

:: Run the Python installation script
python easy_install.py

:: Check if installation was successful
if errorlevel 1 (
    echo.
    echo ❌ Installation failed!
    echo Please check the error messages above.
    echo.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo 🎉 Installation completed successfully!
echo ==========================================
echo.
echo You can now start the dashboard by:
echo • Double-clicking 'start_dashboard.bat'
echo • Or running 'python start_dashboard.py'
echo.
pause 