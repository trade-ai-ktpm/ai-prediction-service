# Sơ đồ luồng xử lý AI Prediction Service

## 1. Luồng xử lý tổng quan

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT REQUEST                          │
│  POST /api/v1/predictions/                                      │
│  { "coin_symbol": "BTC", "timeframe": "1h" }                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    1. FASTAPI ENTRY POINT                       │
│                      (src/main.py)                              │
│  - Nhận HTTP request                                            │
│  - Route đến prediction_router                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    2. API ROUTE HANDLER                         │
│              (src/api/routes/prediction.py)                     │
│  - Validate input với PredictionRequest schema                  │
│  - Inject database session (Dependency Injection)               │
│  - Tạo PredictionPipeline instance                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   3. PREDICTION PIPELINE                        │
│              (src/core/pipeline/predictor.py)                   │
│                                                                 │
│  Step 3.1: Lấy coin từ database                                │
│  ┌──────────────────────────────────────┐                      │
│  │ coin_repo.get_by_symbol("BTC")       │                      │
│  │ → CoinRepository                      │                      │
│  └──────────────────────────────────────┘                      │
│                     │                                           │
│  Step 3.2: Lấy dữ liệu nến                                     │
│  ┌──────────────────────────────────────┐                      │
│  │ candle_repo.get_recent_candles()     │                      │
│  │ → CandleRepository                    │                      │
│  │ → Lấy 100 nến gần nhất                │                      │
│  └──────────────────────────────────────┘                      │
│                     │                                           │
│  Step 3.3: Lấy tin tức                                         │
│  ┌──────────────────────────────────────┐                      │
│  │ news_repo.get_recent_news()          │                      │
│  │ → NewsRepository                      │                      │
│  │ → Lấy 50 tin tức gần nhất             │                      │
│  └──────────────────────────────────────┘                      │
│                     │                                           │
│  Step 3.4: Generate hash & check cache                         │
│  ┌──────────────────────────────────────┐                      │
│  │ hash = generate_hash(input_data)     │                      │
│  │ cached = get_cached_prediction(hash) │                      │
│  └──────────────────────────────────────┘                      │
│                     │                                           │
│                     ├─── Có cache? ───┐                        │
│                     │                  │                        │
│                    YES                NO                        │
│                     │                  │                        │
│                     │   Step 3.5: Tạo AI model                 │
│                     │   ┌──────────────────────────────┐       │
│                     │   │ ModelFactory.create_model()  │       │
│                     │   │ → Chọn provider (openai)     │       │
│                     │   │ → Return OpenAIAdapter       │       │
│                     │   └──────────────────────────────┘       │
│                     │                  │                        │
│                     │   Step 3.6: Gọi AI predict               │
│                     │   ┌──────────────────────────────┐       │
│                     │   │ model.predict(input_data)    │       │
│                     │   │ → OpenAIAdapter.predict()    │       │
│                     │   └──────────────────────────────┘       │
│                     │                  │                        │
│                     │   Step 3.7: Lưu vào database             │
│                     │   ┌──────────────────────────────┐       │
│                     │   │ prediction_repo.create()     │       │
│                     │   └──────────────────────────────┘       │
│                     │                  │                        │
│                     └──────────────────┘                        │
│                                                                 │
│  Step 3.8: Return PredictionResponse                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    4. RESPONSE TO CLIENT                        │
│  {                                                              │
│    "id": 1,                                                     │
│    "coin_symbol": "BTC",                                        │
│    "predicted_value": {...},                                    │
│    "confidence_score": 0.75,                                    │
│    "reasoning": "..."                                           │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Chi tiết: Model Factory (Strategy Pattern)

```
┌─────────────────────────────────────────────────────────────────┐
│                      MODEL FACTORY                              │
│                  (src/models/factory.py)                        │
│                                                                 │
│  Input: provider = "openai", config = {...}                    │
│                                                                 │
│  _adapters = {                                                  │
│    "openai": OpenAIAdapter,      ◄─── Mapping                  │
│    "anthropic": AnthropicAdapter,                               │
│    "gemini": GeminiAdapter,                                     │
│    "local": LocalAdapter                                        │
│  }                                                              │
│                                                                 │
│  create_model(provider, config):                               │
│    1. adapter_class = _adapters.get("openai")                  │
│       → adapter_class = OpenAIAdapter                           │
│                                                                 │
│    2. return adapter_class(config)                             │
│       → return OpenAIAdapter(config)                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     OPENAI ADAPTER                              │
│           (src/models/adapters/openai_adapter.py)               │
│                                                                 │
│  __init__(config):                                              │
│    self.client = AsyncOpenAI(api_key=config["api_key"])        │
│    self.model = "gpt-4-turbo-preview"                          │
│                                                                 │
│  predict(input_data):                                           │
│    1. prompt = build_price_prediction_prompt(input_data)       │
│       → "Bạn là chuyên gia crypto..."                          │
│                                                                 │
│    2. response = await self.client.chat.completions.create()   │
│       → Gọi OpenAI API                                          │
│                                                                 │
│    3. result = json.loads(response.content)                    │
│       → Parse JSON response                                     │
│                                                                 │
│    4. return PredictionOutput(                                 │
│         predicted_value=result["prediction"],                  │
│         confidence_score=result["confidence"],                 │
│         reasoning=result["reasoning"]                          │
│       )                                                         │
└─────────────────────────────────────────────────────────────────┘
```

## 3. Chi tiết: Repository Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    COIN REPOSITORY                              │
│           (src/data/repositories/coin_repository.py)            │
│                                                                 │
│  __init__(db: AsyncSession):                                    │
│    self.db = db  ◄─── Database session được inject             │
│                                                                 │
│  get_by_symbol(symbol: str):                                    │
│    ┌─────────────────────────────────────┐                     │
│    │ 1. Build SQL query                  │                     │
│    │    select(Coin)                     │                     │
│    │    .where(Coin.symbol == "BTC")     │                     │
│    │                                     │                     │
│    │ 2. Execute query                    │                     │
│    │    result = await db.execute(query) │                     │
│    │                                     │                     │
│    │ 3. Return result                    │                     │
│    │    return result.scalar_one_or_none()│                    │
│    └─────────────────────────────────────┘                     │
│                                                                 │
│  create(symbol: str, name: str):                               │
│    ┌─────────────────────────────────────┐                     │
│    │ 1. Create model instance            │                     │
│    │    coin = Coin(symbol="BTC", ...)   │                     │
│    │                                     │                     │
│    │ 2. Add to session                   │                     │
│    │    db.add(coin)                     │                     │
│    │                                     │                     │
│    │ 3. Commit transaction               │                     │
│    │    await db.commit()                │                     │
│    │                                     │                     │
│    │ 4. Refresh & return                 │                     │
│    │    await db.refresh(coin)           │                     │
│    │    return coin                      │                     │
│    └─────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

## 4. Dependency Injection Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI REQUEST                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  @router.post("/")                                              │
│  async def create_prediction(                                   │
│      request: PredictionRequest,  ◄─── Auto validate            │
│      db: AsyncSession = Depends(get_db)  ◄─── Auto inject       │
│  ):                                                             │
│                                                                 │
│  FastAPI tự động:                                               │
│  1. Gọi get_db() để lấy database session                        │
│  2. Inject vào parameter db                                     │
│  3. Sau khi xử lý xong, tự động close session                   │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      get_db()                                   │
│              (src/storage/database.py)                          │
│                                                                 │
│  async def get_db():                                            │
│      async with AsyncSessionLocal() as session:                 │
│          try:                                                   │
│              yield session  ◄─── Trả session cho route          │
│          finally:                                               │
│              await session.close()  ◄─── Auto cleanup           │
└─────────────────────────────────────────────────────────────────┘
```

## 5. Caching Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT DATA                                   │
│  coin_id: 1                                                     │
│  timeframe: "1h"                                                │
│  candles: [...]  (20 nến gần nhất)                             │
│  news: [...]     (10 tin tức gần nhất)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   GENERATE HASH                                 │
│              (src/utils/hash.py)                                │
│                                                                 │
│  hash = SHA256(JSON.stringify(input_data))                     │
│  → "a3f5e8d9c2b1..."                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CHECK DATABASE CACHE                           │
│                                                                 │
│  SELECT * FROM predictions                                      │
│  WHERE input_data_hash = "a3f5e8d9c2b1..."                     │
│    AND created_at > NOW() - INTERVAL '1 hour'                  │
│                                                                 │
│  ┌─────────────┐                    ┌──────────────┐           │
│  │ Found?      │─── YES ───────────►│ Return cache │           │
│  └─────────────┘                    └──────────────┘           │
│         │                                                       │
│        NO                                                       │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────┐                   │
│  │ Call AI model                           │                   │
│  │ Save prediction with hash to database   │                   │
│  └─────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

## 6. Tóm tắt các Pattern

### Strategy Pattern

```
Interface: AIModelInterface
         │
         ├─── OpenAIAdapter
         ├─── AnthropicAdapter
         ├─── GeminiAdapter
         └─── LocalAdapter

Sử dụng: model.predict(data)  # Gọi giống nhau cho mọi provider
```

### Factory Pattern

```
Input: provider="openai", config={...}
       │
       ▼
ModelFactory.create_model()
       │
       ▼
Output: OpenAIAdapter instance
```

### Repository Pattern

```
Business Logic  ──────►  Repository  ──────►  Database
(Pipeline)              (CoinRepo)           (PostgreSQL)

Tách biệt: Business logic không biết SQL
```

### Dependency Injection

```
FastAPI ──────► get_db() ──────► AsyncSession
                                      │
                                      ▼
                              Route Handler
                                      │
                                      ▼
                              PredictionPipeline
```
