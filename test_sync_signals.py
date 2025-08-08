#!/usr/bin/env python3
"""
Standalone script to test signal synchronization
"""

import sqlite3
import json
import os
from datetime import datetime

def sync_json_signals_to_db():
    """Load signals from JSON files and sync them to SQLite database"""
    try:
        # Use absolute path to database
        db_path = os.path.join('/home/chronic/Projects/bfi-signals/core', 'ai_learning.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add missing columns to existing table if needed
        columns_to_add = [
            ('entry_price', 'REAL'),
            ('take_profit', 'REAL'),
            ('stop_loss', 'REAL'),
            ('bias', 'TEXT'),
            ('net_change', 'REAL')
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                cursor.execute(f'ALTER TABLE signal_performance ADD COLUMN {column_name} {column_type}')
                print(f"Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    # Column already exists
                    pass
                else:
                    raise
        
        # Get existing signal timestamps to avoid duplicates
        cursor.execute('SELECT timestamp FROM signal_performance')
        existing_timestamps = set(row[0] for row in cursor.fetchall())
        print(f"Found {len(existing_timestamps)} existing signals in database")
        
        # Load signals from daily JSON files
        data_dir = '/home/chronic/Projects/bfi-signals/data/daily'
        signals_added = 0
        
        if os.path.exists(data_dir):
            print(f"Scanning directory: {data_dir}")
            for filename in os.listdir(data_dir):
                if filename.endswith('.json') and 'signals_' in filename:
                    filepath = os.path.join(data_dir, filename)
                    print(f"Processing file: {filename}")
                    
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                            
                        if 'signals' in data:
                            for signal_entry in data['signals']:
                                signal = signal_entry.get('signal', {})
                                created_at = signal_entry.get('created_at', signal.get('generated_at', ''))
                                
                                # Skip if already exists
                                if created_at in existing_timestamps:
                                    continue
                                
                                # Extract signal data
                                symbol = signal.get('symbol', 'UNKNOWN')
                                probability = signal.get('probability_percentage', 75) / 100.0
                                entry_price = signal.get('entry1', signal.get('current_value', 0))
                                take_profit = signal.get('take_profit', 0)
                                stop_loss = signal.get('sl_tight', 0)
                                bias = signal.get('bias', 'UNKNOWN')
                                net_change = signal.get('net_change', 0)
                                
                                # Insert into database
                                cursor.execute('''
                                    INSERT INTO signal_performance 
                                    (symbol, signal_type, predicted_probability, risk_level, timestamp, 
                                     entry_price, take_profit, stop_loss, bias, net_change)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (
                                    symbol, 'Hybrid Math', probability, 'Medium', created_at,
                                    entry_price, take_profit, stop_loss, bias, net_change
                                ))
                                
                                signals_added += 1
                                print(f"  Added signal: {symbol} {bias} @ {created_at}")
                                
                    except Exception as e:
                        print(f"Error processing {filename}: {e}")
        else:
            print(f"Data directory not found: {data_dir}")
        
        conn.commit()
        conn.close()
        print(f"✅ Signal sync completed successfully. Added {signals_added} new signals.")
        return True
        
    except Exception as e:
        print(f"❌ Error syncing signals: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🔄 Starting signal synchronization...")
    result = sync_json_signals_to_db()
    print(f"Sync result: {result}")