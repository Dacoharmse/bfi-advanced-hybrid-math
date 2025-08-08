#!/usr/bin/env python3
"""
Test script to verify journal route logic works correctly
"""
import sqlite3
import os

def test_journal_data():
    """Test the exact logic from the journal route"""
    print("🧪 Testing journal data retrieval...")
    
    # Check working directory and database
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"📄 Database exists: {os.path.exists('ai_learning.db')}")
    
    try:
        conn = sqlite3.connect("ai_learning.db")
        cursor = conn.cursor()
        
        # Test the overall stats query (same as journal route)
        print("\n=== Testing Overall Stats Query ===")
        cursor.execute('''
            SELECT 
                COUNT(*) as total_signals,
                SUM(CASE WHEN actual_outcome = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN actual_outcome = 0 THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN actual_outcome = 2 THEN 1 ELSE 0 END) as breakevens,
                SUM(CASE WHEN actual_outcome IS NULL THEN 1 ELSE 0 END) as pending,
                AVG(CASE WHEN actual_outcome IS NOT NULL THEN predicted_probability * 100 ELSE NULL END) as avg_probability,
                AVG(CASE WHEN actual_outcome = 1 THEN predicted_probability * 100 ELSE NULL END) as avg_win_probability,
                AVG(CASE WHEN actual_outcome = 0 THEN predicted_probability * 100 ELSE NULL END) as avg_loss_probability
            FROM signal_performance
        ''')
        overall_stats = cursor.fetchone()
        print(f"✅ Overall stats: {overall_stats}")
        
        # Test recent signals query
        print("\n=== Testing Recent Signals Query ===")
        cursor.execute('''
            SELECT 
                id, symbol, signal_type, predicted_probability, risk_level, 
                timestamp, actual_outcome, profit_loss
            FROM signal_performance 
            ORDER BY timestamp DESC 
            LIMIT 20
        ''')
        recent_signals = cursor.fetchall()
        print(f"✅ Recent signals count: {len(recent_signals)}")
        
        # Calculate stats like the journal route does
        print("\n=== Testing Stats Calculation ===")
        total_completed = overall_stats[1] + overall_stats[2] + overall_stats[3]  # wins + losses + breakevens
        overall_win_rate = (overall_stats[1] / total_completed * 100) if total_completed > 0 else 0
        
        # Extract individual stats for template
        total_signals = overall_stats[0]
        wins = overall_stats[1]
        losses = overall_stats[2]
        breakevens = overall_stats[3]
        pending = overall_stats[4]
        
        print(f"📊 Total signals: {total_signals}")
        print(f"📊 Win rate: {overall_win_rate:.1f}%")
        print(f"📊 Wins: {wins}, Losses: {losses}, Breakevens: {breakevens}, Pending: {pending}")
        
        # Test template variables
        print("\n=== Template Variables ===")
        template_vars = {
            'total_signals': total_signals,
            'win_rate': overall_win_rate,
            'wins': wins,
            'losses': losses,
            'breakevens': breakevens,
            'pending': pending,
            'signals': recent_signals,
            'signals_length': len(recent_signals)
        }
        
        for key, value in template_vars.items():
            print(f"  {key}: {value}")
        
        # Test template condition
        signals_condition = recent_signals and len(recent_signals) > 0
        print(f"\n🔍 Template condition 'signals and signals|length > 0': {signals_condition}")
        
        if signals_condition:
            print("✅ Should show signals table")
        else:
            print("❌ Will show 'No Trading Signals Yet'")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_journal_data()