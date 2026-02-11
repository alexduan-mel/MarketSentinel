-- ============================================================
-- SentinelStream - M1 Schema (PostgreSQL / TimescaleDB)
-- Includes: tables + indexes + comments
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ----------------------------
-- 1) Tickers (dimension table)
-- ----------------------------
CREATE TABLE IF NOT EXISTS tickers (
  ticker_id      SERIAL PRIMARY KEY,
  symbol         TEXT NOT NULL UNIQUE,   -- e.g., 'AAPL'
  name           TEXT,                   -- e.g., 'Apple Inc.'
  exchange       TEXT,                   -- e.g., 'NASDAQ'
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE tickers IS 'Ticker dimension table (basic entity registry)';
COMMENT ON COLUMN tickers.symbol IS 'Ticker symbol, e.g., AAPL';
COMMENT ON COLUMN tickers.name IS 'Company name (optional)';
COMMENT ON COLUMN tickers.exchange IS 'Exchange (optional)';

-- ------------------------------------------------------
-- 2) News events (append-only event table, normalized)
-- ------------------------------------------------------
CREATE TABLE IF NOT EXISTS news_events (
  news_id         TEXT PRIMARY KEY,
  trace_id        UUID NOT NULL,          -- correlation ID per pipeline run
  source          TEXT NOT NULL,          -- e.g., finnhub / polygon / rss
  source_event_id TEXT,                  -- provider-specific ID if available

  published_at    TIMESTAMPTZ NOT NULL,   -- from provider (point-in-time context)
  ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- system ingestion time

  title           TEXT NOT NULL,
  url             TEXT NOT NULL,
  content         TEXT,                   -- optional full text if available

  tickers         TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],  -- MVP linkage

  raw_payload     JSONB,                  -- raw provider payload for debugging/replay

  CONSTRAINT uq_news_source_url UNIQUE (source, url)
);

COMMENT ON TABLE news_events IS 'Normalized news events ingested from external sources';
COMMENT ON COLUMN news_events.news_id IS 'Deterministic unique ID (recommended: sha256(source|url))';
COMMENT ON COLUMN news_events.trace_id IS 'Correlation ID for a single pipeline run';
COMMENT ON COLUMN news_events.source IS 'News provider name';
COMMENT ON COLUMN news_events.source_event_id IS 'Provider-specific event ID if available';
COMMENT ON COLUMN news_events.published_at IS 'Published time from provider (UTC)';
COMMENT ON COLUMN news_events.ingested_at IS 'Ingestion time in SentinelStream (UTC)';
COMMENT ON COLUMN news_events.tickers IS 'Tickers associated with this news event (MVP as TEXT[])';
COMMENT ON COLUMN news_events.raw_payload IS 'Raw provider payload stored for debugging/replay';

-- Indexes for dashboard queries
CREATE INDEX IF NOT EXISTS idx_news_published_at ON news_events (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_source ON news_events (source);
CREATE INDEX IF NOT EXISTS idx_news_tickers_gin ON news_events USING GIN (tickers);

-- ------------------------------------------------------
-- 3) LLM analyses (structured output + raw output)
-- ------------------------------------------------------
CREATE TABLE IF NOT EXISTS llm_analyses (
  analysis_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  news_id         TEXT NOT NULL REFERENCES news_events(news_id) ON DELETE CASCADE,
  trace_id        UUID NOT NULL,          -- same trace_id used in this processing run

  provider        TEXT NOT NULL,          -- openai / gemini
  model           TEXT NOT NULL,          -- exact model name
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  sentiment       TEXT NOT NULL CHECK (sentiment IN ('positive', 'negative', 'neutral')),
  confidence      DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  impact_score    DOUBLE PRECISION CHECK (impact_score IS NULL OR (impact_score >= 0 AND impact_score <= 1)),

  entities        JSONB NOT NULL DEFAULT '[]'::JSONB,  -- [{symbol,name?,confidence?},...]
  summary         TEXT NOT NULL,                       -- short summary
  rationale       TEXT,                                -- optional short reasoning

  raw_output      JSONB,                               -- raw model output

  CONSTRAINT uq_analysis_run UNIQUE (news_id, trace_id, provider, model)
);

COMMENT ON TABLE llm_analyses IS 'LLM analysis results (raw output + parsed fields)';
COMMENT ON COLUMN llm_analyses.news_id IS 'FK to news_events.news_id';
COMMENT ON COLUMN llm_analyses.trace_id IS 'Correlation ID for the processing run';
COMMENT ON COLUMN llm_analyses.provider IS 'LLM provider name';
COMMENT ON COLUMN llm_analyses.model IS 'Exact model identifier';
COMMENT ON COLUMN llm_analyses.sentiment IS 'positive | negative | neutral';
COMMENT ON COLUMN llm_analyses.confidence IS 'Overall confidence in [0,1]';
COMMENT ON COLUMN llm_analyses.impact_score IS 'Optional impact score in [0,1]';
COMMENT ON COLUMN llm_analyses.entities IS 'Extracted entities/tickers as JSON array';
COMMENT ON COLUMN llm_analyses.raw_output IS 'Raw model output for debugging/replay';

CREATE INDEX IF NOT EXISTS idx_analysis_news_id ON llm_analyses (news_id);
CREATE INDEX IF NOT EXISTS idx_analysis_created_at ON llm_analyses (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_sentiment ON llm_analyses (sentiment);
CREATE INDEX IF NOT EXISTS idx_analysis_entities_gin ON llm_analyses USING GIN (entities);
