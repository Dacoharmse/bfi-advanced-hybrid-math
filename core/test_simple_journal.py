#!/usr/bin/env python3
"""
Simple test to isolate the journal formatting error
"""
import sqlite3
import os

def test_simple_journal():
    """Test a simplified version of the journal logic"""
    try:
        print("🧪 Testing simple journal logic...")
        
        # Test database connection
        conn = sqlite3.connect("ai_learning.db")
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute('SELECT COUNT(*) FROM signal_performance')
        count = cursor.fetchone()[0]
        print(f"✅ Database connection: {count} signals found")
        
        # Test the exact query from journal route
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
        print(f"✅ Query result: {overall_stats}")
        print(f"✅ Result types: {[type(x) for x in overall_stats]}")
        
        # Test calculations exactly like in journal route
        total_completed = (overall_stats[1] or 0) + (overall_stats[2] or 0) + (overall_stats[3] or 0)
        overall_win_rate = float((overall_stats[1] or 0) / total_completed * 100) if total_completed > 0 else 0.0
        
        # Test variable assignments
        total_signals = int(overall_stats[0] or 0)
        wins = int(overall_stats[1] or 0)
        win_rate = float(overall_win_rate)
        avg_rr = float(1.5)
        total_pnl = float(0.0)
        
        print(f"✅ Calculations successful:")
        print(f"   total_signals: {total_signals} ({type(total_signals)})")
        print(f"   win_rate: {win_rate} ({type(win_rate)})")
        print(f"   avg_rr: {avg_rr} ({type(avg_rr)})")
        print(f"   total_pnl: {total_pnl} ({type(total_pnl)})")
        
        # Test formatting like in template
        print("🧪 Testing template-style formatting...")
        test_format1 = f"{win_rate:.1f}%"
        test_format2 = f"{avg_rr:.1f}"
        test_format3 = f"${total_pnl:.2f}"
        
        print(f"✅ Format tests passed:")
        print(f"   win_rate format: {test_format1}")
        print(f"   avg_rr format: {test_format2}")
        print(f"   total_pnl format: {test_format3}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error in simple journal test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_simple_journal()