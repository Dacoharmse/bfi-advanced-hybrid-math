#!/usr/bin/env python3
"""
BFI Signals Easy Install Script
Automated setup for the BFI Signals AI Dashboard
"""

import os
import sys
import subprocess
import platform
import venv
from pathlib import Path
import shutil
import time

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header():
    """Print installation header"""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("=" * 60)
    print("    BFI Signals AI Dashboard - Easy Install")
    print("    Advanced Trading Signal Intelligence Setup")
    print("=" * 60)
    print(f"{Colors.END}")

def print_step(step_num, description):
    """Print installation step"""
    print(f"\n{Colors.BLUE}📍 Step {step_num}: {description}{Colors.END}")
    print("-" * 40)

def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def check_python_version():
    """Check if Python version is compatible"""
    print_step(1, "Checking Python version")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python {version.major}.{version.minor} is not supported")
        print("Please install Python 3.8 or higher from https://python.org")
        return False
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_system_requirements():
    """Check system requirements"""
    print_step(2, "Checking system requirements")
    
    # Check OS
    os_name = platform.system()
    print(f"Operating System: {os_name}")
    
    # Check if git is available (optional)
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        print_success("Git is available")
    except:
        print_warning("Git not found (optional for updates)")
    
    # Check if pip is available
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, check=True)
        print_success("pip is available")
        return True
    except:
        print_error("pip is not available")
        return False

def create_virtual_environment():
    """Create virtual environment"""
    print_step(3, "Creating virtual environment")
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print_warning("Virtual environment already exists")
        user_input = input("Do you want to recreate it? (y/N): ").lower().strip()
        if user_input == 'y':
            print("Removing existing virtual environment...")
            shutil.rmtree(venv_path)
        else:
            print_success("Using existing virtual environment")
            return True
    
    try:
        print("Creating virtual environment...")
        venv.create(venv_path, with_pip=True)
        print_success("Virtual environment created successfully")
        return True
    except Exception as e:
        print_error(f"Failed to create virtual environment: {e}")
        return False

def get_venv_python():
    """Get virtual environment Python executable"""
    venv_path = Path("venv")
    
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

def install_dependencies():
    """Install required dependencies"""
    print_step(4, "Installing dependencies")
    
    requirements_file = Path("setup") / "requirements.txt"
    
    if not requirements_file.exists():
        print_error("requirements.txt not found in setup directory")
        return False
    
    python_exe = get_venv_python()
    
    try:
        print("Installing required packages...")
        result = subprocess.run([
            str(python_exe), "-m", "pip", "install", "-r", str(requirements_file)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print_success("All dependencies installed successfully")
            return True
        else:
            print_error("Failed to install dependencies")
            print(result.stderr)
            return False
            
    except Exception as e:
        print_error(f"Error installing dependencies: {e}")
        return False

def setup_environment_file():
    """Setup environment configuration"""
    print_step(5, "Setting up environment configuration")
    
    env_file = Path(".env")
    
    if env_file.exists():
        print_warning(".env file already exists")
        return True
    
    # Create basic .env file
    env_content = """# BFI Signals Configuration
# Discord Integration
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here

# API Keys (if needed)
# GEMINI_API_KEY=your_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///ai_learning.db

# Application Settings
FLASK_ENV=production
DEBUG=False
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print_success("Environment file created")
        print_warning("Remember to configure your Discord webhook URL in .env")
        return True
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        return False

def verify_installation():
    """Verify installation"""
    print_step(6, "Verifying installation")
    
    # Check core files
    core_files = [
        "core/dashboard.py",
        "core/ai_engine.py",
        "core/strategy.py",
        "core/data_fetch.py"
    ]
    
    for file_path in core_files:
        if Path(file_path).exists():
            print_success(f"{file_path} found")
        else:
            print_error(f"{file_path} missing")
            return False
    
    # Test Python import
    python_exe = get_venv_python()
    try:
        result = subprocess.run([
            str(python_exe), "-c", "import flask, sqlite3, pandas; print('All imports successful')"
        ], capture_output=True, text=True, cwd="core")
        
        if result.returncode == 0:
            print_success("All required modules can be imported")
            return True
        else:
            print_error("Import test failed")
            print(result.stderr)
            return False
            
    except Exception as e:
        print_error(f"Failed to test imports: {e}")
        return False

def create_database():
    """Initialize database if needed"""
    print_step(7, "Setting up database")
    
    db_file = Path("core") / "ai_learning.db"
    
    if db_file.exists():
        print_success("Database already exists")
        return True
    
    try:
        # Copy database from root if it exists
        root_db = Path("ai_learning.db")
        if root_db.exists():
            shutil.copy2(root_db, db_file)
            print_success("Database copied to core directory")
        else:
            print_warning("Database will be created on first run")
        
        return True
    except Exception as e:
        print_error(f"Database setup failed: {e}")
        return False

def print_completion_message():
    """Print installation completion message"""
    print(f"\n{Colors.GREEN}{Colors.BOLD}")
    print("=" * 60)
    print("    🎉 INSTALLATION COMPLETED SUCCESSFULLY! 🎉")
    print("=" * 60)
    print(f"{Colors.END}")
    
    print(f"\n{Colors.CYAN}🚀 How to start the dashboard:{Colors.END}")
    print(f"   {Colors.WHITE}• Windows: Double-click 'start_dashboard.bat'{Colors.END}")
    print(f"   {Colors.WHITE}• Linux/Mac: Run 'python3 start_dashboard.py'{Colors.END}")
    
    print(f"\n{Colors.CYAN}📱 Dashboard URL:{Colors.END}")
    print(f"   {Colors.WHITE}http://127.0.0.1:5000{Colors.END}")
    
    print(f"\n{Colors.CYAN}⚙️  Configuration:{Colors.END}")
    print(f"   {Colors.WHITE}• Edit '.env' file to configure Discord webhook{Colors.END}")
    print(f"   {Colors.WHITE}• Check 'setup/DISCORD_SETUP.md' for Discord setup{Colors.END}")
    
    print(f"\n{Colors.YELLOW}💡 Need help?{Colors.END}")
    print(f"   {Colors.WHITE}• Check README.md for documentation{Colors.END}")
    print(f"   {Colors.WHITE}• Review setup/INSTALL.md for troubleshooting{Colors.END}")

def main():
    """Main installation function"""
    print_header()
    
    # Check if already in project directory
    if not Path("core").exists():
        print_error("Please run this script from the BFI Signals project root directory")
        return 1
    
    # Installation steps
    steps = [
        check_python_version,
        check_system_requirements,
        create_virtual_environment,
        install_dependencies,
        setup_environment_file,
        verify_installation,
        create_database
    ]
    
    for step in steps:
        if not step():
            print_error("Installation failed!")
            print("Please check the error messages above and try again.")
            return 1
        time.sleep(0.5)  # Small delay for better UX
    
    print_completion_message()
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        input(f"\n{Colors.WHITE}Press Enter to exit...{Colors.END}")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Installation cancelled by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.END}")
        input("Press Enter to exit...")
        sys.exit(1) 