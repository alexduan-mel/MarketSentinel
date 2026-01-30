-- Enable extensions for Time-Series and AI
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Assets Table (The tickers we track)
CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    symbol TEXT UNIQUE NOT NULL,
    name TEXT,
    asset_type TEXT DEFAULT 'stock'
);

-- 2. News Events Table (The Hypertable)
CREATE TABLE IF NOT EXISTS news_events (
    time TIMESTAMPTZ NOT NULL,
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol TEXT NOT NULL,
    source TEXT NOT NULL,
    headline TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    summary TEXT,
    sentiment_score NUMERIC,
    metadata JSONB
);

-- Convert to Hypertable for performance
SELECT create_hypertable('news_events', 'time', if_not_exists => TRUE);

-- Insert a test asset
INSERT INTO assets (symbol, name) VALUES ('MARKET', 'General Market News') ON CONFLICT DO NOTHING;