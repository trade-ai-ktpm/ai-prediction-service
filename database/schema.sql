-- AI Prediction Service Database Schema
-- TimescaleDB (PostgreSQL 16 + TimescaleDB extension)

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Bảng lưu thông tin coins
CREATE TABLE IF NOT EXISTS coins (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng lưu dữ liệu nến 1 phút (candlestick 1-minute base data)
-- TimescaleDB hypertable for optimal time-series performance
CREATE TABLE IF NOT EXISTS candle_data_1m (
    coin_id INTEGER REFERENCES coins(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    open DECIMAL(20, 8) NOT NULL,
    high DECIMAL(20, 8) NOT NULL,
    low DECIMAL(20, 8) NOT NULL,
    close DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(30, 8) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(coin_id, timestamp)
);

-- Convert to hypertable (partitioned by timestamp with 1-day chunks)
SELECT create_hypertable('candle_data_1m', 'timestamp', 
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Enable compression for data older than 7 days
ALTER TABLE candle_data_1m SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'coin_id'
);

SELECT add_compression_policy('candle_data_1m', INTERVAL '7 days');

-- Optional: Retention policy to auto-delete data older than 90 days
-- SELECT add_retention_policy('candle_data_1m', INTERVAL '90 days');

-- Continuous Aggregate: 5-minute candles
CREATE MATERIALIZED VIEW candle_data_5m
WITH (timescaledb.continuous) AS
SELECT 
    coin_id,
    time_bucket('5 minutes', timestamp) AS timestamp,
    first(open, timestamp) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, timestamp) AS close,
    sum(volume) AS volume
FROM candle_data_1m
GROUP BY coin_id, time_bucket('5 minutes', timestamp);

-- Continuous Aggregate: 15-minute candles
CREATE MATERIALIZED VIEW candle_data_15m
WITH (timescaledb.continuous) AS
SELECT 
    coin_id,
    time_bucket('15 minutes', timestamp) AS timestamp,
    first(open, timestamp) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, timestamp) AS close,
    sum(volume) AS volume
FROM candle_data_1m
GROUP BY coin_id, time_bucket('15 minutes', timestamp);

-- Continuous Aggregate: 1-hour candles
CREATE MATERIALIZED VIEW candle_data_1h
WITH (timescaledb.continuous) AS
SELECT 
    coin_id,
    time_bucket('1 hour', timestamp) AS timestamp,
    first(open, timestamp) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, timestamp) AS close,
    sum(volume) AS volume
FROM candle_data_1m
GROUP BY coin_id, time_bucket('1 hour', timestamp);

-- Continuous Aggregate: 4-hour candles
CREATE MATERIALIZED VIEW candle_data_4h
WITH (timescaledb.continuous) AS
SELECT 
    coin_id,
    time_bucket('4 hours', timestamp) AS timestamp,
    first(open, timestamp) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, timestamp) AS close,
    sum(volume) AS volume
FROM candle_data_1m
GROUP BY coin_id, time_bucket('4 hours', timestamp);

-- Continuous Aggregate: 1-day candles
CREATE MATERIALIZED VIEW candle_data_1d
WITH (timescaledb.continuous) AS
SELECT 
    coin_id,
    time_bucket('1 day', timestamp) AS timestamp,
    first(open, timestamp) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, timestamp) AS close,
    sum(volume) AS volume
FROM candle_data_1m
GROUP BY coin_id, time_bucket('1 day', timestamp);

-- Refresh policies for continuous aggregates (auto-refresh every 5 minutes)
SELECT add_continuous_aggregate_policy('candle_data_5m',
    start_offset => INTERVAL '10 minutes',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '5 minutes');

SELECT add_continuous_aggregate_policy('candle_data_15m',
    start_offset => INTERVAL '30 minutes',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '5 minutes');

SELECT add_continuous_aggregate_policy('candle_data_1h',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '15 minutes');

SELECT add_continuous_aggregate_policy('candle_data_4h',
    start_offset => INTERVAL '8 hours',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 hour');

SELECT add_continuous_aggregate_policy('candle_data_1d',
    start_offset => INTERVAL '2 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- Bảng lưu tin tức crypto
CREATE TABLE IF NOT EXISTS news_data (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    source VARCHAR(200),
    url TEXT,
    published_at TIMESTAMP NOT NULL,
    sentiment_score DECIMAL(3, 2),
    coins TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng lưu predictions
CREATE TABLE IF NOT EXISTS predictions (\n    id SERIAL PRIMARY KEY,
    coin_id INTEGER REFERENCES coins(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50),
    prediction_type VARCHAR(50) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    predicted_value JSONB NOT NULL,
    confidence_score DECIMAL(3, 2),
    input_data_hash VARCHAR(64),
    status VARCHAR(20) DEFAULT 'PENDING',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,
    metadata JSONB
);


-- Bảng lưu model configurations
CREATE TABLE IF NOT EXISTS model_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    provider VARCHAR(50) NOT NULL,
    model_identifier VARCHAR(200) NOT NULL,
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
-- TimescaleDB automatically creates index on timestamp (time column)
-- Only need additional index for coin_id queries
CREATE INDEX IF NOT EXISTS idx_candle_1m_coin ON candle_data_1m(coin_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_news_data_published ON news_data(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_data_coins ON news_data USING GIN(coins);
CREATE INDEX IF NOT EXISTS idx_predictions_coin_created ON predictions(coin_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_hash ON predictions(input_data_hash);
CREATE INDEX IF NOT EXISTS idx_predictions_status ON predictions(status) WHERE status IN ('PENDING', 'PROCESSING');
CREATE INDEX IF NOT EXISTS idx_model_configs_active ON model_configs(is_active) WHERE is_active = true;


-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_coins_updated_at BEFORE UPDATE ON coins
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_model_configs_updated_at BEFORE UPDATE ON model_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
