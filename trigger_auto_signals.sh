#!/bin/bash
# Manual Auto Signal Generation Trigger for Linux/Mac
# This script manually triggers the auto signal generation system

echo "==============================================="
echo "BFI SIGNALS - Manual Auto Signal Trigger"
echo "==============================================="
echo

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    echo "Using Python 3..."
    python3 trigger_auto_signals.py
elif command -v python &> /dev/null; then
    echo "Using Python..."
    python trigger_auto_signals.py
else
    echo "❌ Python not found! Please install Python 3.x"
    exit 1
fi

echo
echo "Script completed. Check Discord for signals!"