#!/usr/bin/env python3
"""
Simple Auto Signal Generation Trigger
Direct trigger without API dependency
"""

import sys
import os
from datetime import datetime

# Add the core directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

def main():
    """Simple main function to trigger auto signal generation"""
    print("🤖 BFI SIGNALS - Simple Auto Signal Trigger")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    try:
        # Import and run the auto generation function
        from dashboard import generate_auto_signal_for_next_day
        
        print("🚀 Starting auto signal generation...")
        signals = generate_auto_signal_for_next_day()
        
        if signals:
            print(f"\n✅ Successfully generated {len(signals)} signals!")
            print("📢 Signals should now appear in Discord")
            
            # Show summary
            for i, signal in enumerate(signals, 1):
                symbol = signal.get('display_name', signal.get('symbol', 'Unknown'))
                direction = signal.get('direction', 'Unknown')
                entry = signal.get('entry_price', 0)
                confidence = signal.get('confidence', 0)
                print(f"   {i}. {symbol} {direction} @ {entry:.2f} (Confidence: {confidence}%)")
        else:
            print("❌ No signals were generated")
            print("💡 Check that market data is available and auto generation is enabled")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Run from project root directory")
        print("   2. Make sure core/dashboard.py exists")
        print("   3. Check that dependencies are installed")

if __name__ == "__main__":
    main()