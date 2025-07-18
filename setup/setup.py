#!/usr/bin/env python3
"""
BFI Signals Setup Script
Automated setup for BFI Signals project on any computer
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def print_header():
    """Print setup header"""
    print("=" * 60)
    print("BFI Signals - Automated Setup")
    print("   Bonang Finance Hybrid Math Strategy")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8+ is required!")
        print(f"   Current version: {sys.version}")
        print("   Please upgrade Python and try again.")
        return False
    
    print(f"SUCCESS: Python {sys.version.split()[0]} detected")
    return True

def check_pip():
    """Check if pip is available"""
    print("Checking pip availability...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        print("SUCCESS: pip is available")
        return True
    except subprocess.CalledProcessError:
        print("ERROR: pip is not available!")
        print("   Please install pip and try again.")
        return False

def create_virtual_environment():
    """Create virtual environment in parent directory"""
    print("Creating virtual environment...")
    
    # Change to parent directory where venv should be created
    parent_dir = Path("..").resolve()
    os.chdir(parent_dir)
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("WARNING: Virtual environment already exists")
        response = input("   Delete and recreate? (y/n): ").lower().strip()
        if response == 'y':
            print("Removing existing virtual environment...")
            shutil.rmtree(venv_path)
        else:
            print("SUCCESS: Using existing virtual environment")
            return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("SUCCESS: Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to create virtual environment: {e}")
        return False

def get_venv_python():
    """Get path to virtual environment Python"""
    system = platform.system().lower()
    
    if system == "windows":
        return Path("venv") / "Scripts" / "python.exe"
    else:
        return Path("venv") / "bin" / "python"

def install_dependencies():
    """Install project dependencies"""
    print("Installing dependencies...")
    
    venv_python = get_venv_python()
    
    if not venv_python.exists():
        print("ERROR: Virtual environment Python not found!")
        return False
    
    # Use requirements.txt from setup folder
    requirements_file = Path("setup") / "requirements.txt"
    if not requirements_file.exists():
        print("ERROR: requirements.txt not found in setup folder!")
        return False
    
    try:
        # Upgrade pip first
        print("   Upgrading pip...")
        subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # Install requirements
        print("   Installing project dependencies...")
        subprocess.run([str(venv_python), "-m", "pip", "install", "-r", str(requirements_file)], 
                      check=True)
        
        print("SUCCESS: Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        return False

def create_env_file():
    """Create .env file template in parent directory"""
    print("Creating .env file template...")
    
    env_path = Path(".env")
    
    if env_path.exists():
        print("WARNING: .env file already exists")
        response = input("   Overwrite with template? (y/n): ").lower().strip()
        if response != 'y':
            print("SUCCESS: Keeping existing .env file")
            return True
    
    env_template = """# BFI Signals Configuration
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
"""
    
    try:
        with open(env_path, 'w') as f:
            f.write(env_template)
        print("SUCCESS: .env file created successfully")
        return True
    except Exception as e:
        print(f"ERROR: Failed to create .env file: {e}")
        return False

def test_installation():
    """Test the installation"""
    print("Testing installation...")
    
    venv_python = get_venv_python()
    
    try:
        # Test imports - add core to Python path
        test_script = """
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
    
    print("SUCCESS: All imports successful")
    
except ImportError as e:
    print(f"ERROR: Import error: {e}")
    sys.exit(1)
"""
        
        result = subprocess.run([str(venv_python), "-c", test_script], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("SUCCESS: Installation test passed!")
            return True
        else:
            print(f"ERROR: Installation test failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"ERROR: Test failed: {e}")
        return False

def create_launcher_scripts():
    """Create launcher scripts for different platforms"""
    print("Creating launcher scripts...")
    
    # The main launcher should already exist, just verify it's there
    main_launcher = Path("RUN_BFI_SIGNALS.bat")
    if main_launcher.exists():
        print("SUCCESS: Main launcher already exists")
        return True
    else:
        print("WARNING: Main launcher not found - this is expected for first-time setup")
        return True

def print_completion_message():
    """Print completion message with instructions"""
    print("\n" + "=" * 60)
    print("BFI Signals Setup Complete!")
    print("=" * 60)
    print()
    print("NEXT STEPS:")
    print("1. Configure Discord webhook:")
    print("   - Edit .env file in the main folder")
    print("   - Add your Discord webhook URL")
    print("   - See setup/DISCORD_SETUP.md for instructions")
    print()
    print("2. Test the installation:")
    print("   - Run: RUN_BFI_SIGNALS.bat")
    print("   - Or activate venv and run: python core/main.py")
    print()
    print("3. Configure symbols (optional):")
    print("   - Edit TRADING_SYMBOLS in .env file")
    print("   - Default: ^NDX,US30 (NASDAQ-100 and US30)")
    print()
    print("You're ready to generate trading signals!")
    print("WARNING: Remember: Always use proper risk management!")
    print()

def main():
    """Main setup function"""
    print_header()
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    if not check_pip():
        return False
    
    # Setup steps
    if not create_virtual_environment():
        return False
    
    if not install_dependencies():
        return False
    
    if not create_env_file():
        return False
    
    if not create_launcher_scripts():
        return False
    
    if not test_installation():
        return False
    
    print_completion_message()
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nERROR: Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: Setup failed: {e}")
        sys.exit(1) 