import os
import sys
import subprocess
import time

def check_environment():
    """Check if the environment is properly set up"""
    print("BFI SIGNALS - BONANG FINANCE HYBRID MATH STRATEGY")
    print("=" * 50)
    print()
    
    # Check virtual environment
    venv_python = "venv\\Scripts\\python.exe"
    if not os.path.exists(venv_python):
        print("ERROR: Virtual environment not found!")
        print("Please run setup first: go to 'setup' folder and run setup.bat")
        input("Press Enter to exit...")
        return False
    print("✓ Virtual environment: OK")
    
    # Check .env file
    if not os.path.exists(".env"):
        print("ERROR: Configuration file missing!")
        print("Please create .env file with your Discord webhook URL")
        input("Press Enter to exit...")
        return False
    print("✓ Configuration file: OK")
    
    # Check main application
    if not os.path.exists("core\\main.py"):
        print("ERROR: Main application not found!")
        print("Please ensure all files are properly installed")
        input("Press Enter to exit...")
        return False
    print("✓ Main application: OK")
    
    return True

def run_bfi_signals():
    """Run the BFI Signals application"""
    if not check_environment():
        return
    
    print()
    print("⚠️ RISK WARNING: These signals are for educational purposes.")
    print("Use proper risk management and only trade what you can afford to lose.")
    print()
    
    # Test Discord connection
    print("Testing Discord connection...")
    result = subprocess.run([
        "venv\\Scripts\\python.exe", 
        "core\\main.py", 
        "--test-connection"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("ERROR: Discord connection failed!")
        print("Please check your webhook URL in .env file")
        print("Error details:", result.stderr)
        input("Press Enter to exit...")
        return
    print("✓ Discord connection: OK")
    
    print()
    print("Generating trading signals...")
    print("This may take a moment while we analyze the markets...")
    print()
    
    # Run the main application
    result = subprocess.run([
        "venv\\Scripts\\python.exe", 
        "core\\main.py"
    ])
    
    if result.returncode == 0:
        print()
        print("SUCCESS: BFI Signals completed!")
        print("Check your Discord channel for the trading signals.")
    else:
        print()
        print("ERROR: BFI Signals encountered an error")
        print("Please check the error messages above")
    
    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    try:
        run_bfi_signals()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
        input("Press Enter to exit...") 