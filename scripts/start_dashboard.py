#!/usr/bin/env python3
"""
BFI Signals Dashboard Launcher
Professional trading signal intelligence dashboard startup script
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_requirements():
    """Check if all required files and dependencies exist"""
    print("🔍 Checking system requirements...")
    
    # Check if core directory exists
    core_dir = Path("core")
    if not core_dir.exists():
        print("❌ Error: 'core' directory not found!")
        print("   Make sure you're running this from the project root directory.")
        return False
    
    # Check if dashboard.py exists
    dashboard_file = core_dir / "dashboard.py"
    if not dashboard_file.exists():
        print("❌ Error: 'dashboard.py' not found in core directory!")
        return False
    
    # Check virtual environment
    venv_dir = Path("venv")
    if venv_dir.exists():
        print("✅ Virtual environment found")
    else:
        print("⚠️  Virtual environment not found - using system Python")
    
    return True

def get_python_executable():
    """Get the appropriate Python executable"""
    venv_dir = Path("venv")
    
    if venv_dir.exists():
        # Check for Windows
        if os.name == 'nt':
            python_exe = venv_dir / "Scripts" / "python.exe"
            if python_exe.exists():
                return str(python_exe)
        else:
            # Unix/Linux/Mac
            python_exe = venv_dir / "bin" / "python"
            if python_exe.exists():
                return str(python_exe)
    
    # Fallback to system Python
    return sys.executable

def start_dashboard():
    """Start the BFI Signals Dashboard"""
    print("\n🚀 Starting BFI Signals AI Dashboard...")
    print("=" * 50)
    
    # Change to core directory
    core_dir = Path("core")
    
    # Get Python executable
    python_exe = get_python_executable()
    print(f"📍 Using Python: {python_exe}")
    print(f"📂 Working directory: {core_dir.absolute()}")
    
    try:
        # Start the dashboard
        os.chdir(core_dir)
        
        print("\n🌟 Dashboard starting...")
        print("📱 Access your dashboard at: http://127.0.0.1:5000")
        print("🛑 Press Ctrl+C to stop the dashboard")
        print("=" * 50)
        
        # Run the dashboard
        subprocess.run([python_exe, "dashboard.py"], check=True)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Dashboard stopped by user")
        print("Thank you for using BFI Signals! 👋")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting dashboard: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   1. Make sure all dependencies are installed: pip install -r setup/requirements.txt")
        print("   2. Check if port 5000 is already in use")
        print("   3. Verify your Python environment is set up correctly")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check the installation and try again.")

def main():
    """Main function"""
    print("🎯 BFI Signals AI Dashboard Launcher")
    print("Advanced AI-Powered Trading Signal Intelligence")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ System check failed!")
        input("Press Enter to exit...")
        return 1
    
    print("✅ All requirements satisfied")
    
    # Start the dashboard
    start_dashboard()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        input("Press Enter to exit...")
        sys.exit(1) 