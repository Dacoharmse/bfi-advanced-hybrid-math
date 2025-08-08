#!/usr/bin/env python3
"""
Test Script for BFI Signals Storage System
Verifies Supabase and local storage integration
"""

import sys
import os
from datetime import date, datetime

# Add core directory to path
sys.path.append('core')

def test_storage_system():
    """Test the complete storage system"""
    print("=" * 60)
    print("🧪 BFI SIGNALS - STORAGE SYSTEM TEST")
    print("=" * 60)
    print()
    
    try:
        # Import storage components
        from storage.data_manager import data_manager, test_storage_connections
        from storage.local_storage import local_storage
        from storage.supabase_client import supabase_client
        
        print("✅ Storage modules imported successfully")
        print()
        
        # Test connections
        print("🔌 Testing Storage Connections:")
        connections = test_storage_connections()
        print(f"   📡 Supabase: {'✅ Connected' if connections.get('supabase') else '❌ Not Connected'}")
        print(f"   💾 Local Storage: {'✅ Available' if connections.get('local') else '❌ Not Available'}")
        print()
        
        # Test data operations
        print("📊 Testing Data Operations:")
        
        # Sample market data (yesterday's closing data)
        test_date = date(2025, 7, 29)
        test_data = {
            'nasdaq': {
                'price': '23,336.25',
                'change': '-20.02',
                'changePercent': '-0.09%',
                'rawChange': -20.018046875,
                'previousClose': '23,356.27',
                'high': '23,510.92',
                'low': '23,298.91',
                'timestamp': '2025-07-29T20:58:03.326711'
            },
            'dow': {
                'price': '44,603.18',
                'change': '-234.38',
                'changePercent': '-0.52%',
                'rawChange': -234.38031249999767,
                'previousClose': '44,837.56',
                'high': '44,883.66',
                'low': '44,584.22',
                'timestamp': '2025-07-29T20:58:10.966437'
            }
        }
        
        print(f"   📝 Saving test data for {test_date}...")
        save_results = data_manager.save_market_close_data(test_date, test_data)
        print(f"   📡 Supabase Save: {'✅' if save_results.get('supabase') else '❌'}")
        print(f"   💾 Local Save: {'✅' if save_results.get('local') else '❌'}")
        print(f"   📊 Total Symbols: {save_results.get('total_symbols', 0)}")
        print()
        
        # Test data retrieval
        print(f"   📖 Retrieving test data for {test_date}...")
        retrieved_data = data_manager.get_market_close_data(test_date)
        
        if retrieved_data:
            print(f"   ✅ Retrieved {len(retrieved_data)} symbols:")
            for symbol, data in retrieved_data.items():
                price = data.get('price', 'N/A')
                change = data.get('change', 'N/A')
                print(f"      {symbol.upper()}: {price} ({change})")
        else:
            print("   ❌ No data retrieved")
        print()
        
        # Test latest data retrieval
        print("   📖 Testing latest data retrieval...")
        latest_data = data_manager.get_latest_market_close_data()
        
        if latest_data:
            print(f"   ✅ Retrieved latest data ({len(latest_data)} symbols):")
            for symbol, data in latest_data.items():
                price = data.get('price', 'N/A')
                date_info = data.get('date', 'N/A')
                print(f"      {symbol.upper()}: {price} (Date: {date_info})")
        else:
            print("   ❌ No latest data retrieved")
        print()
        
        # Test signal saving
        print("   📊 Testing signal saving...")
        test_signal = {
            'symbol': 'NASDAQ',
            'display_name': 'NAS100',
            'bias': 'SHORT',
            'current_value': 23336.25,
            'net_change': -20.02,
            'take_profit': 23356.27,
            'entry1': 23298.91,
            'entry2': 23336.25,
            'sl_tight': 23436.25,
            'sl_wide': 23536.25,
            'probability_percentage': 75,
            'cv_position': 0.16,
            'generated_at': datetime.now().isoformat()
        }
        
        signal_results = data_manager.save_signal(test_signal)
        print(f"   📡 Supabase Signal Save: {'✅' if signal_results.get('supabase') else '❌'}")
        print(f"   💾 Local Signal Save: {'✅' if signal_results.get('local') else '❌'}")
        print()
        
        # Summary
        print("📋 TEST SUMMARY:")
        total_tests = 6
        passed_tests = 0
        
        if connections.get('local'): passed_tests += 1
        if save_results.get('local'): passed_tests += 1
        if retrieved_data: passed_tests += 1
        if latest_data: passed_tests += 1
        if signal_results.get('local'): passed_tests += 1
        
        # Supabase tests (bonus)
        supabase_tests = 0
        if connections.get('supabase'): supabase_tests += 1
        if save_results.get('supabase'): supabase_tests += 1
        if signal_results.get('supabase'): supabase_tests += 1
        
        print(f"   ✅ Core Tests Passed: {passed_tests}/{total_tests}")
        print(f"   📡 Supabase Tests Passed: {supabase_tests}/3")
        print()
        
        if passed_tests >= 4:  # At least local storage working
            print("🎉 STORAGE SYSTEM TEST: PASSED")
            print("   💾 Local storage is working correctly")
            if supabase_tests >= 2:
                print("   📡 Supabase integration is working correctly")
            else:
                print("   ⚠️ Supabase integration needs attention")
        else:
            print("❌ STORAGE SYSTEM TEST: FAILED")
            print("   🔧 Please check the error messages above")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Try installing dependencies: pip install -r storage_requirements.txt")
    except Exception as e:
        print(f"❌ Test Error: {e}")
        import traceback
        print("📋 Full Error Details:")
        print(traceback.format_exc())
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    test_storage_system()