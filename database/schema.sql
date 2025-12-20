-- AI Prediction Service Database Schema
-- PostgreSQL 14+

-- Bảng lưu thông tin coins
CREATE TABLE IF NOT EXISTS coins (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng lưu dữ liệu nến (candlestick)
CREATE TABLE IF NOT EXISTS candle_data (
    id SERIAL PRIMARY KEY,
    coin_id INTEGER REFERENCES coins(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(20, 8) NOT NULL,
    high DECIMAL(20, 8) NOT NULL,
    low DECIMAL(20, 8) NOT NULL,
    close DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(30, 8) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(coin_id, timestamp, timeframe)
);

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
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    coin_id INTEGER REFERENCES coins(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50),
    prediction_type VARCHAR(50) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    predicted_value JSONB NOT NULL,
    confidence_score DECIMAL(3, 2),
    input_data_hash VARCHAR(64),
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
CREATE INDEX IF NOT EXISTS idx_candle_data_coin_time ON candle_data(coin_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_candle_data_timeframe ON candle_data(timeframe);
CREATE INDEX IF NOT EXISTS idx_news_data_published ON news_data(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_data_coins ON news_data USING GIN(coins);
CREATE INDEX IF NOT EXISTS idx_predictions_coin_created ON predictions(coin_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_hash ON predictions(input_data_hash);
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
