@echo off
echo 🚀 BFI Signals - Quick Setup
echo ============================
echo.

echo 🔍 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo ✅ Python found!
echo.

echo 🔧 Running automated setup...
python setup.py

if errorlevel 1 (
    echo.
    echo ❌ Setup failed! Please check error messages above.
    pause
    exit /b 1
)

echo.
echo ✅ Setup completed successfully!
echo.
echo 📋 NEXT STEPS:
echo 1. Configure Discord webhook in .env file
echo 2. Run run_bfi_signals_auto.bat to generate signals
echo.
pause 