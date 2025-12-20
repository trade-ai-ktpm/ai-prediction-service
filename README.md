# AI Prediction Service

Service dự đoán giá cryptocurrency sử dụng AI models (LLM) với kiến trúc linh hoạt, cho phép thay đổi model dễ dàng.

## Tính năng

- ✅ Dự đoán giá coin dựa trên dữ liệu nến lịch sử và tin tức
- ✅ Hỗ trợ nhiều AI providers: OpenAI, Anthropic, Gemini, Local Models
- ✅ Caching predictions để tối ưu performance
- ✅ RESTful API với FastAPI
- ✅ PostgreSQL database với SQLAlchemy ORM
- ✅ Redis cache (optional)
- ✅ Design patterns: Strategy, Factory, Repository

## Kiến trúc

```
┌─────────────┐
│   FastAPI   │
│   Routes    │
└──────┬──────┘
       │
┌──────▼──────────┐
│   Prediction    │
│    Pipeline     │
└──────┬──────────┘
       │
       ├─────────────┐
       │             │
┌──────▼──────┐  ┌──▼────────┐
│   Model     │  │   Data    │
│  Strategy   │  │   Repos   │
└─────────────┘  └───────────┘
```

## Cài đặt

### 1. Clone và setup environment

```bash
cd ai-prediction-service
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Cấu hình environment

```bash
cp .env.example .env
```

Chỉnh sửa `.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_prediction
REDIS_URL=redis://localhost:6379/0

OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here

DEFAULT_MODEL_PROVIDER=openai
```

### 3. Setup database

```bash
# Tạo database
createdb ai_prediction

# Chạy schema
psql -d ai_prediction -f database/schema.sql
```

### 4. Chạy service

```bash
cd src
python main.py
```

Service sẽ chạy tại `http://localhost:8000`

## API Documentation

Sau khi chạy service, truy cập:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoints

#### POST /api/v1/predictions/

Tạo prediction mới

Request:

```json
{
  "coin_symbol": "BTC",
  "timeframe": "1h",
  "prediction_type": "price",
  "model_name": "openai"
}
```

Response:

```json
{
  "id": 1,
  "coin_id": 1,
  "coin_symbol": "BTC",
  "model_name": "gpt-4-turbo-preview",
  "predicted_value": {
    "price_direction": "up",
    "estimated_price_range": {
      "low": 45000,
      "high": 47000
    }
  },
  "confidence_score": 0.75,
  "reasoning": "...",
  "created_at": "2024-01-01T00:00:00"
}
```

#### GET /api/v1/predictions/models

Liệt kê các AI models có sẵn

## Thay đổi AI Model

### Cách 1: Thay đổi default provider

Trong `.env`:

```env
DEFAULT_MODEL_PROVIDER=anthropic  # hoặc openai, gemini
```

### Cách 2: Chỉ định model khi gọi API

```json
{
  "coin_symbol": "BTC",
  "timeframe": "1h",
  "model_name": "gemini"
}
```

### Cách 3: Thêm custom adapter

```python
# src/models/adapters/custom_adapter.py
from src.models.base import BaseAIModel

class CustomAdapter(BaseAIModel):
    async def predict(self, input_data):
        # Implementation
        pass

# Đăng ký adapter
from src.models.factory import ModelFactory
ModelFactory.register_adapter("custom", CustomAdapter)
```

## Cấu trúc thư mục

```
src/
├── api/                    # API layer
│   ├── routes/            # API endpoints
│   └── dependencies.py    # FastAPI dependencies
├── core/                  # Core business logic
│   ├── interfaces/        # Abstract interfaces
│   ├── pipeline/          # Prediction pipeline
│   └── exceptions.py      # Custom exceptions
├── models/                # AI Model implementations
│   ├── adapters/         # Model adapters (Strategy)
│   ├── prompts/          # Prompt templates
│   ├── base.py           # Base model class
│   └── factory.py        # Model factory
├── data/                  # Data layer
│   ├── models/           # SQLAlchemy models
│   └── repositories/     # Repository pattern
├── schemas/               # Pydantic schemas
├── storage/               # Storage layer
│   ├── database.py       # Database connection
│   └── cache.py          # Redis cache
├── config/                # Configuration
├── utils/                 # Utilities
└── main.py               # Application entry
```

## Design Patterns

### 1. Strategy Pattern

Cho phép thay đổi AI model provider mà không cần sửa code:

- `AIModelInterface`: Interface chung
- `OpenAIAdapter`, `AnthropicAdapter`, `GeminiAdapter`: Implementations

### 2. Factory Pattern

Tạo model instances dựa trên configuration:

- `ModelFactory.create_model(provider, config)`

### 3. Repository Pattern

Tách biệt data access logic:

- `CoinRepository`, `CandleRepository`, `NewsRepository`, `PredictionRepository`

### 4. Dependency Injection

Quản lý dependencies thông qua FastAPI's Depends

## Testing

```bash
# Unit tests
pytest tests/unit -v

# Integration tests
pytest tests/integration -v
```

## Docker

```bash
docker-compose up -d
```

## License

MIT
# ai-prediction-service
