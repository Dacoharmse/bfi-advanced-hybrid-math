#!/bin/bash

# BFI Signals Project Setup Script
# This script automates the setup process for Unix/macOS systems

set -e  # Exit on any error

echo "🚀 BFI Signals Project Setup Starting..."
echo "=========================================="

# Create and cd into bfi-signals directory
echo "📁 Creating project directory..."
if [ ! -d "bfi-signals" ]; then
    mkdir bfi-signals
    echo "✅ Created bfi-signals directory"
else
    echo "ℹ️  bfi-signals directory already exists"
fi

cd bfi-signals

# Check if Python is installed
echo "🔍 Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "✅ Python3 found: $(python3 --version)"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo "✅ Python found: $(python --version)"
else
    echo "❌ Python not found! Please install Python from https://python.org"
    exit 1
fi

# Initialize git repository
echo "📦 Initializing git repository..."
if [ ! -d ".git" ]; then
    git init
    echo "✅ Git repository initialized"
else
    echo "ℹ️  Git repository already exists"
fi

# Create virtual environment
echo "🐍 Creating virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi

# Activate virtual environment and install packages
echo "📦 Installing Python packages..."
source venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Install required packages
pip install -r requirements.txt

echo "✅ All packages installed successfully!"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Environment Variables for BFI Signals Project
# This file stores sensitive configuration data
# Never commit this file to version control!

# Discord Integration (REQUIRED)
# Get your webhook URL from Discord: Server Settings > Integrations > Webhooks
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL_HERE

# Trading Configuration
# Comma-separated list of symbols to analyze (default: ^NDX for NASDAQ-100)
TRADING_SYMBOLS=^NDX

# Discord Formatting
# Use enhanced Discord formatting with embeds (true/false)
USE_ENHANCED_DISCORD=true

# Add your API keys and configuration here
# Example:
# API_KEY=your_api_key_here
# DATABASE_URL=your_database_url_here
# DEBUG=True
EOF
    echo "✅ .env file created"
else
    echo "ℹ️  .env file already exists"
fi

echo ""
echo "🎉 Setup Complete!"
echo "==================="
echo ""
echo "⚠️  IMPORTANT: Configure your Discord webhook!"
echo "1. Edit the .env file and add your Discord webhook URL"
echo "2. See DISCORD_SETUP.md for detailed instructions"
echo ""
echo "To test your setup:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Test Discord connection:"
echo "   python main.py --test-connection"
echo ""
echo "3. Generate signals:"
echo "   python main.py"
echo ""
echo "4. When done, deactivate:"
echo "   deactivate"
echo ""
echo "📊 Run 'python main.py' each morning to generate signals"
echo "🔗 Signals will be posted to your Discord channel"
echo ""
echo "Happy trading! 🚀" 