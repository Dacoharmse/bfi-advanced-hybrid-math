#!/usr/bin/env python3
"""
Database Migration Script for Manual Trade Journal
Creates the manual_journal_entries table for manual trade tracking
"""

import sqlite3
import os
from datetime import datetime

def create_manual_journal_table():
    """Create the manual journal entries table"""
    db_path = "ai_learning.db"
    
    print(f"🔧 Creating manual journal table in {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create manual_journal_entries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS manual_journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                trade_type TEXT NOT NULL CHECK (trade_type IN ('CALL', 'PUT', 'LONG', 'SHORT')),
                entry_price REAL NOT NULL,
                exit_price REAL,
                quantity INTEGER NOT NULL DEFAULT 1,
                outcome TEXT CHECK (outcome IN ('WIN', 'LOSS', 'BREAKEVEN', 'PENDING')),
                profit_loss REAL DEFAULT 0.0,
                trade_date DATE NOT NULL,
                entry_time TEXT,
                exit_time TEXT,
                notes TEXT,
                chart_image_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_manual_journal_symbol 
            ON manual_journal_entries(symbol)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_manual_journal_date 
            ON manual_journal_entries(trade_date)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_manual_journal_outcome 
            ON manual_journal_entries(outcome)
        ''')
        
        # Create trigger to update updated_at timestamp
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_manual_journal_timestamp 
            AFTER UPDATE ON manual_journal_entries
            FOR EACH ROW
            BEGIN
                UPDATE manual_journal_entries 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END
        ''')
        
        conn.commit()
        print("✅ Manual journal entries table created successfully!")
        
        # Verify table creation
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='manual_journal_entries'")
        result = cursor.fetchone()
        if result:
            print("✅ Table verification successful")
            
            # Show table schema
            cursor.execute("PRAGMA table_info(manual_journal_entries)")
            columns = cursor.fetchall()
            print("📋 Table Schema:")
            for col in columns:
                print(f"   {col[1]} ({col[2]})")
        else:
            print("❌ Table verification failed")
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
    finally:
        if conn:
            conn.close()
            
    return True

def create_sample_data():
    """Create some sample journal entries for testing"""
    db_path = "ai_learning.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Insert sample data
        sample_entries = [
            {
                'symbol': 'NASDAQ',
                'trade_type': 'CALL',
                'entry_price': 15250.00,
                'exit_price': 15300.00,
                'quantity': 1,
                'outcome': 'WIN',
                'profit_loss': 50.00,
                'trade_date': '2025-08-01',
                'entry_time': '09:30',
                'exit_time': '10:15',
                'notes': 'Strong bullish momentum at market open',
                'chart_image_path': None
            },
            {
                'symbol': 'US30',
                'trade_type': 'PUT',
                'entry_price': 39800.00,
                'exit_price': 39750.00,
                'quantity': 1,
                'outcome': 'WIN',
                'profit_loss': 50.00,
                'trade_date': '2025-08-01',
                'entry_time': '14:30',
                'exit_time': '15:00',
                'notes': 'Bearish reversal pattern confirmed',
                'chart_image_path': None
            },
            {
                'symbol': 'GOLD',
                'trade_type': 'LONG',
                'entry_price': 2045.50,
                'exit_price': None,
                'quantity': 2,
                'outcome': 'PENDING',
                'profit_loss': 0.0,
                'trade_date': '2025-08-02',
                'entry_time': '08:00',
                'exit_time': None,
                'notes': 'Safe haven trade during market uncertainty',
                'chart_image_path': None
            }
        ]
        
        for entry in sample_entries:
            cursor.execute('''
                INSERT INTO manual_journal_entries 
                (symbol, trade_type, entry_price, exit_price, quantity, outcome, 
                 profit_loss, trade_date, entry_time, exit_time, notes, chart_image_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry['symbol'], entry['trade_type'], entry['entry_price'], 
                entry['exit_price'], entry['quantity'], entry['outcome'],
                entry['profit_loss'], entry['trade_date'], entry['entry_time'],
                entry['exit_time'], entry['notes'], entry['chart_image_path']
            ))
        
        conn.commit()
        print("✅ Sample data created successfully!")
        
        # Show inserted data
        cursor.execute("SELECT COUNT(*) FROM manual_journal_entries")
        count = cursor.fetchone()[0]
        print(f"📊 Total entries in manual journal: {count}")
        
    except sqlite3.Error as e:
        print(f"❌ Database error creating sample data: {e}")
        
    finally:
        if conn:
            conn.close()

def main():
    """Main migration function"""
    print("🚀 Starting manual journal database migration...")
    print(f"📅 Migration started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if database exists
    if not os.path.exists("ai_learning.db"):
        print("❌ Database file ai_learning.db not found!")
        return False
    
    # Create the table
    if create_manual_journal_table():
        print("✅ Manual journal table migration completed successfully!")
        
        # Create sample data automatically for testing
        create_sample_data()
        
        return True
    else:
        print("❌ Migration failed!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)