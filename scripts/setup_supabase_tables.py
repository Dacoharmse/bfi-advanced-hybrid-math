#!/usr/bin/env python3
"""
Setup Supabase Tables for BFI Signals
Creates all necessary tables in Supabase database
"""

import sys
import os

# Add the core directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from storage.supabase_client import supabase_client

def create_tables():
    """Create all required tables in Supabase"""
    
    if not supabase_client.available:
        print("❌ Supabase client not available")
        return False
    
    print("Creating Supabase tables...")
    
    try:
        # Create users table
        print("📝 Creating users table...")
        users_sql = '''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            is_active BOOLEAN DEFAULT FALSE,
            is_approved BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            email_verified BOOLEAN DEFAULT FALSE,
            verification_token TEXT,
            approved_by INTEGER,
            approved_at TIMESTAMP,
            profile_picture TEXT,
            full_name TEXT,
            timezone TEXT DEFAULT 'UTC'
        )
        '''
        
        # Create signal_performance table
        print("📝 Creating signal_performance table...")
        signals_sql = '''
        CREATE TABLE IF NOT EXISTS signal_performance (
            id SERIAL PRIMARY KEY,
            symbol TEXT NOT NULL,
            signal_type TEXT,
            predicted_probability INTEGER,
            risk_level TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            actual_outcome INTEGER,
            profit_loss REAL,
            risky_play_outcome INTEGER,
            user_id INTEGER,
            signal_data JSONB,
            bias TEXT,
            current_value REAL,
            take_profit REAL,
            entry1 REAL,
            entry2 REAL,
            sl_tight REAL,
            sl_wide REAL,
            probability_percentage INTEGER,
            cv_position REAL,
            posted_to_discord BOOLEAN DEFAULT FALSE,
            entry_price REAL,
            stop_loss REAL,
            net_change REAL
        )
        '''
        
        # Create user_sessions table
        print("📝 Creating user_sessions table...")
        sessions_sql = '''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            session_token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT
        )
        '''
        
        # Create user_notifications table
        print("📝 Creating user_notifications table...")
        notifications_sql = '''
        CREATE TABLE IF NOT EXISTS user_notifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            notification_type TEXT DEFAULT 'signal',
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            signal_id INTEGER
        )
        '''
        
        # Create password_reset_tokens table
        print("📝 Creating password_reset_tokens table...")
        reset_tokens_sql = '''
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            used BOOLEAN DEFAULT FALSE
        )
        '''
        
        # Create journal_entries table
        print("📝 Creating journal_entries table...")
        journal_sql = '''
        CREATE TABLE IF NOT EXISTS journal_entries (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            symbol TEXT NOT NULL,
            entry_type TEXT,
            entry_date DATE,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
        
        # Execute SQL commands (Note: This would typically be done via Supabase SQL Editor)
        print("\n⚠️  IMPORTANT: Execute the following SQL commands in your Supabase SQL Editor:")
        print("\n" + "="*60)
        print(users_sql)
        print("\n" + "="*60)
        print(signals_sql)
        print("\n" + "="*60)
        print(sessions_sql)
        print("\n" + "="*60)
        print(notifications_sql)
        print("\n" + "="*60)
        print(reset_tokens_sql)
        print("\n" + "="*60)
        print(journal_sql)
        print("\n" + "="*60)
        
        print("\n✅ Table creation SQL generated successfully!")
        print("📋 Copy and paste each SQL block into your Supabase SQL Editor to create the tables.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up tables: {e}")
        return False

if __name__ == "__main__":
    create_tables()