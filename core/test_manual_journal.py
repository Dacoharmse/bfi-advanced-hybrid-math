#!/usr/bin/env python3
"""
Test script for manual journal functionality
"""

import os
import sys
from datetime import datetime
from manual_journal import journal_manager

def test_manual_journal():
    """Test manual journal operations"""
    print("🧪 Testing Manual Journal Operations")
    print("=" * 50)
    
    # Test 1: Get existing entries
    print("1. Testing get_journal_entries()...")
    entries, message = journal_manager.get_journal_entries()
    print(f"   ✅ {message}")
    print(f"   📊 Found {len(entries)} entries")
    
    if entries:
        latest_entry = entries[0]
        print(f"   📝 Latest: {latest_entry['symbol']} {latest_entry['trade_type']} on {latest_entry['trade_date']}")
    
    # Test 2: Get statistics
    print("\n2. Testing get_journal_statistics()...")
    stats, message = journal_manager.get_journal_statistics()
    print(f"   ✅ {message}")
    
    if stats and stats['overall']:
        overall = stats['overall']
        print(f"   📊 Total trades: {overall[0]}")
        print(f"   📈 Wins: {overall[1]}")
        print(f"   📉 Losses: {overall[2]}")
        print(f"   ⚖️  Breakevens: {overall[3]}")
        print(f"   ⏳ Pending: {overall[4]}")
        print(f"   💰 Total P&L: ${overall[5]:.2f}")
        
        # Calculate win rate
        completed = overall[1] + overall[2] + overall[3]
        win_rate = (overall[1] / completed * 100) if completed > 0 else 0
        print(f"   🎯 Win Rate: {win_rate:.1f}%")
    
    # Test 3: Test single entry retrieval
    if entries:
        print(f"\n3. Testing get_journal_entry() for ID {entries[0]['id']}...")
        entry, message = journal_manager.get_journal_entry(entries[0]['id'])
        print(f"   ✅ {message}")
        if entry:
            print(f"   📝 Entry: {entry['symbol']} {entry['trade_type']}")
            print(f"   💰 P&L: ${entry['profit_loss']:.2f}")
    
    # Test 4: Test creating a new entry
    print("\n4. Testing create_journal_entry()...")
    test_entry = {
        'symbol': 'TEST',
        'trade_type': 'CALL',
        'entry_price': 1000.00,
        'exit_price': 1050.00,
        'quantity': 1,
        'outcome': 'WIN',
        'profit_loss': 50.00,
        'trade_date': datetime.now().strftime('%Y-%m-%d'),
        'entry_time': '10:30',
        'exit_time': '11:15',
        'notes': 'Test entry for validation',
        'chart_image_path': None
    }
    
    entry_id, message = journal_manager.create_journal_entry(test_entry)
    if entry_id:
        print(f"   ✅ {message} (ID: {entry_id})")
        
        # Test 5: Update the test entry
        print(f"\n5. Testing update_journal_entry() for ID {entry_id}...")
        test_entry['notes'] = 'Updated test entry'
        test_entry['profit_loss'] = 55.00
        
        success, message = journal_manager.update_journal_entry(entry_id, test_entry)
        print(f"   ✅ {message}" if success else f"   ❌ {message}")
        
        # Test 6: Delete the test entry
        print(f"\n6. Testing delete_journal_entry() for ID {entry_id}...")
        success, message = journal_manager.delete_journal_entry(entry_id)
        print(f"   ✅ {message}" if success else f"   ❌ {message}")
    else:
        print(f"   ❌ {message}")
    
    # Test 7: Test file validation (without actual file)
    print("\n7. Testing file validation...")
    test_data = b"fake image data"
    is_valid, message = journal_manager.validate_image(test_data)
    print(f"   Expected failure: {message}")
    
    print("\n🎉 Manual Journal Testing Complete!")
    print("=" * 50)

if __name__ == "__main__":
    # Change to the correct directory
    os.chdir('/home/chronic/Projects/bfi-signals/core')
    test_manual_journal()