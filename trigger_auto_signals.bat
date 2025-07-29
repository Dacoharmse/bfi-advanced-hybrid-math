@echo off
REM Manual Auto Signal Generation Trigger for Windows
REM This script manually triggers the auto signal generation system

echo ===============================================
echo BFI SIGNALS - Manual Auto Signal Trigger
echo ===============================================
echo.

REM Try Python 3 first, then fallback to python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Using Python...
    python trigger_auto_signals.py
) else (
    py --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo Using py launcher...
        py trigger_auto_signals.py
    ) else (
        echo Python not found! Please install Python 3.x
        pause
        exit /b 1
    )
)

echo.
echo Press any key to close...
pause >nul