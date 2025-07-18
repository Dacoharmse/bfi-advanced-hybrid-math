# BFI Signals Manual Installation Script
# Run this script in PowerShell as Administrator

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "BFI Signals - Manual Installation" -ForegroundColor Cyan
Write-Host "Bonang Finance Hybrid Math Strategy" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "WARNING: This script should be run as Administrator for best results" -ForegroundColor Yellow
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host ""
}

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Green
try {
    $pythonVersion = python --version 2>&1
    Write-Host "SUCCESS: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found! Please install Python 3.8+ first." -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check pip
Write-Host "Checking pip..." -ForegroundColor Green
try {
    $pipVersion = pip --version 2>&1
    Write-Host "SUCCESS: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: pip not found! Please install pip." -ForegroundColor Red
    exit 1
}

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Green
pip install --upgrade pip

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Green
if (Test-Path "venv") {
    Write-Host "WARNING: Virtual environment already exists" -ForegroundColor Yellow
    $response = Read-Host "Delete and recreate? (y/n)"
    if ($response -eq "y") {
        Remove-Item -Recurse -Force "venv"
        Write-Host "Removed existing virtual environment" -ForegroundColor Green
    } else {
        Write-Host "Using existing virtual environment" -ForegroundColor Green
    }
}

if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "SUCCESS: Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Green
Write-Host "Installing yfinance..." -ForegroundColor Yellow
pip install "yfinance>=0.2.18"

Write-Host "Installing requests..." -ForegroundColor Yellow
pip install "requests>=2.31.0"

Write-Host "Installing python-dotenv..." -ForegroundColor Yellow
pip install "python-dotenv>=1.0.0"

Write-Host "Installing beautifulsoup4..." -ForegroundColor Yellow
pip install "beautifulsoup4>=4.12.0"

Write-Host "Installing pandas..." -ForegroundColor Yellow
pip install "pandas>=2.0.0"

Write-Host "Installing feedparser..." -ForegroundColor Yellow
pip install "feedparser>=6.0.0"

Write-Host "Installing google-genai..." -ForegroundColor Yellow
pip install "google-genai>=0.8.0"

Write-Host "Installing flask..." -ForegroundColor Yellow
pip install "flask>=3.0.0"

Write-Host "SUCCESS: All dependencies installed!" -ForegroundColor Green

# Create .env file if it doesn't exist
Write-Host "Creating .env file..." -ForegroundColor Green
if (-not (Test-Path ".env")) {
    $envContent = @"
# BFI Signals Configuration
# This file stores sensitive configuration data
# Never commit this file to version control!

# Discord Integration (REQUIRED)
# Get your webhook URL from Discord: Server Settings > Integrations > Webhooks
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL_HERE

# Trading Configuration
# Comma-separated list of symbols to analyze (default: ^NDX for NASDAQ-100)
TRADING_SYMBOLS=^NDX,US30

# Optional Settings
# Use simple Discord formatting (true/false)
USE_SIMPLE_DISCORD=false

# Include news sentiment analysis (true/false)
INCLUDE_NEWS_ANALYSIS=true

# Add your API keys and configuration here
# Example:
# API_KEY=your_api_key_here
# DATABASE_URL=your_database_url_here
# DEBUG=True
"@
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "SUCCESS: .env file created" -ForegroundColor Green
} else {
    Write-Host "WARNING: .env file already exists - keeping existing file" -ForegroundColor Yellow
}

# Test installation
Write-Host "Testing installation..." -ForegroundColor Green
try {
    python -c "
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'core'))

try:
    import pandas as pd
    import requests
    import yfinance as yf
    from bs4 import BeautifulSoup
    from dotenv import load_dotenv
    import feedparser
    
    # Test our core modules
    from strategy import calculate_signal
    from data_fetch import fetch_last_two_1h_bars
    from discord_post import post_signal
    from news_sentiment import analyze_symbol_news
    
    print('SUCCESS: All imports successful')
    
except ImportError as e:
    print(f'ERROR: Import error: {e}')
    sys.exit(1)
"
    Write-Host "SUCCESS: Installation test passed!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Installation test failed!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "BFI Signals Setup Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Configure Discord webhook:" -ForegroundColor White
Write-Host "   - Edit .env file in the main folder" -ForegroundColor White
Write-Host "   - Add your Discord webhook URL" -ForegroundColor White
Write-Host "   - See setup/DISCORD_SETUP.md for instructions" -ForegroundColor White
Write-Host ""
Write-Host "2. Test the installation:" -ForegroundColor White
Write-Host "   - Run: RUN_BFI_SIGNALS.bat" -ForegroundColor White
Write-Host "   - Or activate venv and run: python core/main.py" -ForegroundColor White
Write-Host ""
Write-Host "3. Configure symbols (optional):" -ForegroundColor White
Write-Host "   - Edit TRADING_SYMBOLS in .env file" -ForegroundColor White
Write-Host "   - Default: ^NDX,US30 (NASDAQ-100 and US30)" -ForegroundColor White
Write-Host ""
Write-Host "You're ready to generate trading signals!" -ForegroundColor Green
Write-Host "WARNING: Remember: Always use proper risk management!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 