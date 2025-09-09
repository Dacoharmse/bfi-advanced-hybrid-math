-- BFI Signals Database Tables Setup
-- Execute these commands in Supabase SQL Editor

-- 1. Users table
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
);

-- 2. Signal Performance table
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
);

-- 3. User Sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT
);

-- 4. User Notifications table
CREATE TABLE IF NOT EXISTS user_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    notification_type TEXT DEFAULT 'signal',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    signal_id INTEGER
);

-- 5. Password Reset Tokens table
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used BOOLEAN DEFAULT FALSE
);

-- 6. Journal Entries table
CREATE TABLE IF NOT EXISTS journal_entries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    symbol TEXT NOT NULL,
    entry_type TEXT,
    entry_date DATE,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);