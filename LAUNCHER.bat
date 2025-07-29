@echo off
title BFI Signals - Main Launcher
color 0A

echo.
echo ==========================================
echo   🚀 BFI Signals Trading System
echo   Advanced AI-Powered Market Analysis
echo ==========================================
echo.
echo 1. Start Dashboard          (Web Interface)
echo 2. Generate Trading Signals (Manual Run) 
echo 3. Quick Setup             (First Time)
echo 4. View Documentation
echo 5. Exit
echo.
echo ==========================================
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo Starting Dashboard...
    call start_dashboard.bat
) else if "%choice%"=="2" (
    echo Generating Trading Signals...
    call venv\Scripts\activate && python run_bfi_signals.py
) else if "%choice%"=="3" (
    echo Running Setup...
    cd scripts && call easy_install.bat
) else if "%choice%"=="4" (
    echo Opening Documentation...
    start README.md
) else if "%choice%"=="5" (
    echo Thanks for using BFI Signals! 👋
    exit
) else (
    echo Invalid choice. Please try again.
    pause
    goto :EOF
)

pause 