#!/usr/bin/env python3
"""
Manual Auto Signal Generation Trigger
Manually trigger the auto signal generation system for testing
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add the core directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

def trigger_via_api():
    """Trigger auto signal generation via API endpoint"""
    try:
        print("🚀 Triggering auto signal generation via API...")
        
        # Make API call to trigger auto generation
        response = requests.post('http://localhost:5000/api/generate_auto_signal', 
                               headers={'Content-Type': 'application/json'},
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ API Success: {data.get('message')}")
                print(f"🎯 Signals generated: {data.get('signals_generated', 0)}")
                
                # Show generated signals
                signals = data.get('signals', [])
                for signal in signals:
                    symbol = signal.get('display_name', signal.get('symbol', 'Unknown'))
                    direction = signal.get('direction', 'Unknown')
                    entry = signal.get('entry_price', 0)
                    print(f"   • {symbol} {direction} @ {entry:.2f}")
                
                return True
            else:
                print(f"❌ API Error: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure the dashboard is running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ API trigger failed: {e}")
        return False

def trigger_direct():
    """Trigger auto signal generation directly by importing the function"""
    try:
        print("🚀 Triggering auto signal generation directly...")
        
        # Import the dashboard module
        from dashboard import generate_auto_signal_for_next_day
        
        # Call the function directly
        signals = generate_auto_signal_for_next_day()
        
        if signals:
            print(f"✅ Direct Success: Generated {len(signals)} signals")
            for signal in signals:
                symbol = signal.get('display_name', signal.get('symbol', 'Unknown'))
                direction = signal.get('direction', 'Unknown')
                entry = signal.get('entry_price', 0)
                print(f"   • {symbol} {direction} @ {entry:.2f}")
            return True
        else:
            print("❌ No signals were generated")
            return False
            
    except Exception as e:
        print(f"❌ Direct trigger failed: {e}")
        return False

def main():
    """Main function to trigger auto signal generation"""
    print("=" * 60)
    print("🤖 BFI SIGNALS - Manual Auto Signal Generation Trigger")
    print("=" * 60)
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Try API method first
    print("Method 1: API Trigger")
    api_success = trigger_via_api()
    
    if not api_success:
        print("\nMethod 2: Direct Import Trigger")
        direct_success = trigger_direct()
        
        if not direct_success:
            print("\n❌ Both methods failed!")
            print("💡 Troubleshooting:")
            print("   1. Make sure the dashboard is running: python core/dashboard.py")
            print("   2. Check that market data is available")
            print("   3. Verify Discord webhook is configured")
            sys.exit(1)
    
    print("\n✅ Auto signal generation completed successfully!")
    print("📢 Check your Discord channel for the posted signals")
    print("=" * 60)

if __name__ == "__main__":
    main()