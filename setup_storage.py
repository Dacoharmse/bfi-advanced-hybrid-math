#!/usr/bin/env python3
"""
Setup Script for BFI Signals Storage System
Installs dependencies and configures the storage system
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"   Error output: {e.stderr}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 BFI SIGNALS - STORAGE SYSTEM SETUP")
    print("=" * 60)
    print()
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} detected")
    print()
    
    # Install dependencies
    print("📦 Installing Storage System Dependencies:")
    
    dependencies = [
        ("pip install supabase>=2.0.0", "Installing Supabase client"),
        ("pip install schedule>=1.2.0", "Installing scheduler"),
        ("pip install pytz>=2023.3", "Installing timezone support"),
        ("pip install python-dateutil>=2.8.0", "Installing date utilities"),
    ]
    
    failed_installs = 0
    for command, description in dependencies:
        if not run_command(command, description):
            failed_installs += 1
    
    if failed_installs > 0:
        print(f"⚠️ {failed_installs} dependencies failed to install")
        print("   You may need to install them manually")
    else:
        print("✅ All dependencies installed successfully")
    
    print()
    
    # Create directories
    print("📁 Creating Storage Directories:")
    directories = [
        'data/backups',
        'data/daily', 
        'data/current',
        'logs'
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created: {directory}")
        except Exception as e:
            print(f"❌ Failed to create {directory}: {e}")
    
    print()
    
    # Test storage system
    print("🧪 Testing Storage System:")
    try:
        # Add current directory to Python path
        sys.path.append('core')
        
        # Test imports
        try:
            from storage.data_manager import data_manager
            print("✅ Storage modules imported successfully")
        except ImportError as e:
            print(f"❌ Import failed: {e}")
            return False
        
        # Test connections
        try:
            connections = data_manager.test_connections()
            print(f"✅ Connection test completed:")
            print(f"   📡 Supabase: {'✅ Connected' if connections.get('supabase') else '❌ Not Connected'}")
            print(f"   💾 Local Storage: {'✅ Available' if connections.get('local') else '❌ Not Available'}")
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
        
    except Exception as e:
        print(f"❌ Storage system test failed: {e}")
    
    print()
    
    # Create sample data
    print("📊 Creating Sample Data:")
    try:
        from datetime import date
        from storage.data_manager import save_market_data
        
        sample_date = date(2025, 7, 29)
        sample_data = {
            'nasdaq': {
                'price': '23,336.25',
                'change': '-20.02',
                'changePercent': '-0.09%',
                'rawChange': -20.018046875,
                'previousClose': '23,356.27',
                'high': '23,510.92',
                'low': '23,298.91',
                'timestamp': '2025-07-29T20:58:03.326711'
            }
        }
        
        results = save_market_data(sample_date, sample_data)
        print(f"✅ Sample data created for {sample_date}")
        print(f"   📡 Supabase: {'✅' if results.get('supabase') else '❌'}")
        print(f"   💾 Local: {'✅' if results.get('local') else '❌'}")
        
    except Exception as e:
        print(f"❌ Sample data creation failed: {e}")
    
    print()
    
    # Database schema instructions
    print("🗄️ Database Schema Setup:")
    print("   1. Go to your Supabase project dashboard")
    print("   2. Navigate to SQL Editor")
    print("   3. Execute the SQL script in 'database_schema.sql'")
    print("   4. Verify tables are created: market_close_data, signals, data_capture_log")
    print()
    
    # Usage instructions
    print("📋 USAGE INSTRUCTIONS:")
    print()
    print("1. Test the complete system:")
    print("   python test_storage_system.py")
    print()
    print("2. Start the data capture scheduler:")
    print("   python core/storage/scheduler.py --run")
    print()
    print("3. Manual data capture:")
    print("   python core/storage/scheduler.py --manual 2025-07-29")
    print()
    print("4. Test capture process:")
    print("   python core/storage/scheduler.py --test")
    print()
    
    # Configuration info
    print("⚙️ CONFIGURATION:")
    print("   📡 Supabase URL: https://kiiugsmjybncvtrdshdk.supabase.co")
    print("   🕐 Capture Time: 23:05 GMT+2 daily")
    print("   📊 Symbols: NASDAQ, DOW, GOLD")
    print("   💾 Local Storage: data/ directory")
    print("   🔄 Backup: Automatic daily backups")
    print()
    
    print("=" * 60)
    print("🎉 STORAGE SYSTEM SETUP COMPLETE!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        import traceback
        print("📋 Full Error Details:")
        print(traceback.format_exc())
        sys.exit(1)