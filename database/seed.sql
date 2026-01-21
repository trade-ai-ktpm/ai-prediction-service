-- Seed initial coins data
INSERT INTO coins (symbol, name) VALUES
    ('BTCUSDT', 'Bitcoin'),
    ('ETHUSDT', 'Ethereum'),
    ('BNBUSDT', 'Binance Coin'),
    ('SOLUSDT', 'Solana'),
    ('ADAUSDT', 'Cardano'),
    ('XRPUSDT', 'Ripple'),
    ('DOGEUSDT', 'Dogecoin'),
    ('DOTUSDT', 'Polkadot'),
    ('MATICUSDT', 'Polygon'),
    ('LINKUSDT', 'Chainlink')
ON CONFLICT (symbol) DO NOTHING;

-- Seed default model configuration (Gemini)
INSERT INTO model_configs (name, provider, model_identifier, config, is_active) VALUES
    (
        'gemini-default',
        'gemini',
        'gemini-1.5-flash',
        '{"temperature": 0.7, "max_tokens": 2000, "top_p": 0.9}'::jsonb,
        true
    )
ON CONFLICT (name) DO UPDATE SET
    provider = EXCLUDED.provider,
    model_identifier = EXCLUDED.model_identifier,
    config = EXCLUDED.config,
    is_active = EXCLUDED.is_active,
    updated_at = CURRENT_TIMESTAMP;
