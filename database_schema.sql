-- BFI Signals Database Schema for Supabase
-- Execute this in your Supabase SQL Editor

-- Market closing data (captured at 23:05 GMT+2)
CREATE TABLE IF NOT EXISTS market_close_data (
    id SERIAL PRIMARY KEY,
    capture_date DATE NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    price DECIMAL(12,2) NOT NULL,
    change_amount DECIMAL(12,2) NOT NULL,
    change_percent DECIMAL(8,4) NOT NULL,
    previous_close DECIMAL(12,2) NOT NULL,
    daily_high DECIMAL(12,2) NOT NULL,
    daily_low DECIMAL(12,2) NOT NULL,
    raw_change DECIMAL(12,8) NOT NULL,
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source VARCHAR(50) DEFAULT 'live_feed',
    UNIQUE(capture_date, symbol)
);

-- Generated signals 
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    signal_date DATE NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    signal_type VARCHAR(20) NOT NULL, -- 'auto', 'manual', 'semi_auto'
    bias VARCHAR(10) NOT NULL, -- 'LONG', 'SHORT'
    current_value DECIMAL(12,2) NOT NULL,
    take_profit DECIMAL(12,2) NOT NULL,
    entry1 DECIMAL(12,2) NOT NULL,
    entry2 DECIMAL(12,2) NOT NULL,
    sl_tight DECIMAL(12,2) NOT NULL,
    sl_wide DECIMAL(12,2) NOT NULL,
    probability_percentage INTEGER NOT NULL,
    cv_position DECIMAL(5,4) NOT NULL,
    signal_data JSONB NOT NULL, -- Full signal object
    posted_to_discord BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Data capture log (for monitoring)
CREATE TABLE IF NOT EXISTS data_capture_log (
    id SERIAL PRIMARY KEY,
    capture_date DATE NOT NULL,
    symbols_captured INTEGER NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_market_data_date_symbol ON market_close_data(capture_date, symbol);
CREATE INDEX IF NOT EXISTS idx_signals_date_symbol ON signals(signal_date, symbol);
CREATE INDEX IF NOT EXISTS idx_capture_log_date ON data_capture_log(capture_date);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE market_close_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_capture_log ENABLE ROW LEVEL SECURITY;

-- Create policies to allow public access (adjust as needed)
CREATE POLICY "Allow public read access" ON market_close_data FOR SELECT USING (true);
CREATE POLICY "Allow public insert access" ON market_close_data FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update access" ON market_close_data FOR UPDATE USING (true);

CREATE POLICY "Allow public read access" ON signals FOR SELECT USING (true);
CREATE POLICY "Allow public insert access" ON signals FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update access" ON signals FOR UPDATE USING (true);

CREATE POLICY "Allow public read access" ON data_capture_log FOR SELECT USING (true);
CREATE POLICY "Allow public insert access" ON data_capture_log FOR INSERT WITH CHECK (true);

-- Sample data insertion (for testing)
INSERT INTO market_close_data (
    capture_date, symbol, price, change_amount, change_percent, 
    previous_close, daily_high, daily_low, raw_change, source
) VALUES (
    '2025-07-29', 'NASDAQ', 23336.25, -20.02, -0.09, 
    23356.27, 23510.92, 23298.91, -20.018046875, 'sample_data'
) ON CONFLICT (capture_date, symbol) DO NOTHING;

INSERT INTO market_close_data (
    capture_date, symbol, price, change_amount, change_percent, 
    previous_close, daily_high, daily_low, raw_change, source
) VALUES (
    '2025-07-29', 'DOW', 44603.18, -234.38, -0.52, 
    44837.56, 44883.66, 44584.22, -234.38031249999767, 'sample_data'
) ON CONFLICT (capture_date, symbol) DO NOTHING;