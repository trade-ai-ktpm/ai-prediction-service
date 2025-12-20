# Hướng dẫn Đọc hiểu AI Prediction Service (Cho người mới Python)

## 📚 Mục lục

1. [Bắt đầu từ đâu?](#bắt-đầu-từ-đâu)
2. [Kiến thức Python cần biết](#kiến-thức-python-cần-biết)
3. [Luồng đọc code từng bước](#luồng-đọc-code-từng-bước)
4. [Giải thích các khái niệm quan trọng](#giải-thích-các-khái-niệm-quan-trọng)
5. [Ví dụ thực tế](#ví-dụ-thực-tế)

---

## 🎯 Bắt đầu từ đâu?

### Bước 1: Đọc README.md trước

Mở file [README.md](file:///home/ngocphat/learn/kien-truc-phan-mem/crypto/ai-prediction-service/README.md) để hiểu:

- Dự án làm gì?
- Có những tính năng gì?
- Cách cài đặt và chạy

### Bước 2: Xem Database Schema

Mở [database/schema.sql](file:///home/ngocphat/learn/kien-truc-phan-mem/crypto/ai-prediction-service/database/schema.sql) để hiểu:

- Dữ liệu được lưu như thế nào?
- Có những bảng gì?
- Mối quan hệ giữa các bảng

### Bước 3: Theo luồng đọc code (xem phần dưới)

---

## 📖 Kiến thức Python cần biết

### 1. Class và Object

```python
# Class là bản thiết kế, Object là thực thể
class Car:
    def __init__(self, brand):  # Constructor - hàm khởi tạo
        self.brand = brand      # self = this trong Java/C#

    def drive(self):            # Method - hàm của class
        print(f"{self.brand} is driving")

# Tạo object
my_car = Car("Toyota")
my_car.drive()  # Output: Toyota is driving
```

### 2. Async/Await

```python
# async = hàm bất đồng bộ (không chờ đợi)
async def fetch_data():
    # await = đợi kết quả trước khi tiếp tục
    result = await database.query()
    return result

# Gọi hàm async
data = await fetch_data()
```

**Tại sao dùng async?**

- Không block khi chờ database, API
- Xử lý nhiều requests cùng lúc
- Performance tốt hơn

### 3. Type Hints

```python
# Khai báo kiểu dữ liệu (giống TypeScript)
def add(a: int, b: int) -> int:
    return a + b

# Optional = có thể None
from typing import Optional
def get_user(id: int) -> Optional[User]:
    return user or None
```

### 4. Decorators

```python
# @ là decorator - thêm chức năng cho hàm
@app.get("/users")  # Biến hàm thành API endpoint
async def get_users():
    return users

# Tương đương với:
# app.get("/users")(get_users)
```

### 5. Abstract Base Class (ABC)

```python
from abc import ABC, abstractmethod

# Class trừu tượng - không thể tạo instance trực tiếp
class Animal(ABC):
    @abstractmethod  # Bắt buộc class con phải implement
    def make_sound(self):
        pass

class Dog(Animal):
    def make_sound(self):  # Phải implement
        return "Woof!"
```

---

## 🔍 Luồng đọc code từng bước

### BƯỚC 1️⃣: Entry Point - main.py

**Đọc file:** [src/main.py](file:///home/ngocphat/learn/kien-truc-phan-mem/crypto/ai-prediction-service/src/main.py)

```python
# 1. Import FastAPI framework
from fastapi import FastAPI

# 2. Tạo ứng dụng
app = FastAPI(title="AI Prediction Service")

# 3. Đăng ký routes (API endpoints)
app.include_router(health_router)      # /health
app.include_router(prediction_router)  # /api/v1/predictions

# 4. Chạy server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Hiểu gì?**

- `main.py` là điểm bắt đầu của ứng dụng
- FastAPI tự động tạo API documentation tại `/docs`
- `lifespan` function chạy khi start/stop app (setup database, cache)

**Đọc tiếp:** Routes để xem API endpoints

---

### BƯỚC 2️⃣: API Routes - Nơi nhận requests

**Đọc file:** [src/api/routes/prediction.py](file:///home/ngocphat/learn/kien-truc-phan-mem/crypto/ai-prediction-service/src/api/routes/prediction.py)

```python
@router.post("/", response_model=PredictionResponse)
async def create_prediction(
    request: PredictionRequest,           # Request body
    db: AsyncSession = Depends(get_db)    # Dependency Injection
):
    # 1. Tạo pipeline instance
    pipeline = PredictionPipeline(db)

    # 2. Gọi hàm predict
    result = await pipeline.predict(
        coin_symbol=request.coin_symbol,
        timeframe=request.timeframe,
        prediction_type=request.prediction_type,
        model_name=request.model_name
    )

    # 3. Trả về kết quả
    return result
```

**Hiểu gì?**

- `@router.post("/")` = API endpoint POST
- `Depends(get_db)` = FastAPI tự động inject database session
- `PredictionRequest` = Pydantic model validate input
- `PredictionResponse` = Format output

**Đọc tiếp:** PredictionPipeline để xem logic xử lý

---

### BƯỚC 3️⃣: Prediction Pipeline - Core Logic

**Đọc file:** [src/core/pipeline/predictor.py](file:///home/ngocphat/learn/kien-truc-phan-mem/crypto/ai-prediction-service/src/core/pipeline/predictor.py)

```python
class PredictionPipeline:
    def __init__(self, db: AsyncSession):
        # Khởi tạo repositories
        self.coin_repo = CoinRepository(db)
        self.candle_repo = CandleRepository(db)
        self.news_repo = NewsRepository(db)
        self.prediction_repo = PredictionRepository(db)

    async def predict(self, coin_symbol: str, ...):
        # BƯỚC 1: Lấy thông tin coin
        coin = await self.coin_repo.get_by_symbol(coin_symbol)

        # BƯỚC 2: Lấy dữ liệu nến
        candles = await self.candle_repo.get_recent_candles(
            coin.id, timeframe, limit=100
        )

        # BƯỚC 3: Lấy tin tức
        news = await self.news_repo.get_recent_news(
            coin_symbol=coin_symbol, limit=50
        )

        # BƯỚC 4: Tạo hash để cache
        input_hash = generate_hash({...})

        # BƯỚC 5: Check cache
        cached = await self.prediction_repo.get_cached_prediction(...)
        if cached:
            return cached  # Trả về luôn nếu có cache

        # BƯỚC 6: Tạo AI model từ Factory
        model = ModelFactory.create_model(provider, config)

        # BƯỚC 7: Gọi AI để predict
        result = await model.predict(prediction_input)

        # BƯỚC 8: Lưu vào database
        saved = await self.prediction_repo.create(...)

        # BƯỚC 9: Trả về kết quả
        return PredictionResponse(...)
```

**Hiểu gì?**

- Pipeline = chuỗi các bước xử lý
- Repositories = lớp truy cập database
- Factory = tạo AI model instance
- Caching = tránh gọi AI nhiều lần cho cùng input

**Đọc tiếp:** ModelFactory để hiểu Strategy Pattern

---

### BƯỚC 4️⃣: Model Factory - Strategy Pattern

**Đọc file:** [src/models/factory.py](file:///home/ngocphat/learn/kien-truc-phan-mem/crypto/ai-prediction-service/src/models/factory.py)

```python
class ModelFactory:
    # Dictionary lưu mapping provider -> Adapter class
    _adapters = {
        "openai": OpenAIAdapter,
        "anthropic": AnthropicAdapter,
        "gemini": GeminiAdapter,
        "local": LocalAdapter,
    }

    @classmethod
    def create_model(cls, provider: str, config: dict):
        # Lấy class tương ứng với provider
        adapter_class = cls._adapters.get(provider)

        # Tạo instance và trả về
        return adapter_class(config)
```

**Tại sao dùng Factory?**

```python
# ❌ Không dùng Factory - phải sửa code mỗi khi thêm provider
if provider == "openai":
    model = OpenAIAdapter(config)
elif provider == "anthropic":
    model = AnthropicAdapter(config)
# ... phải thêm elif mỗi lần có provider mới

# ✅ Dùng Factory - chỉ cần register
model = ModelFactory.create_model(provider, config)

# Thêm provider mới không cần sửa code
ModelFactory.register_adapter("new_provider", NewAdapter)
```

**Đọc tiếp:** Một adapter cụ thể (OpenAI)

---

### BƯỚC 5️⃣: AI Model Adapter - Strategy Pattern

**Đọc file:** [src/models/adapters/openai_adapter.py](file:///home/ngocphat/learn/kien-truc-phan-mem/crypto/ai-prediction-service/src/models/adapters/openai_adapter.py)

```python
# Kế thừa từ BaseAIModel, implement AIModelInterface
class OpenAIAdapter(BaseAIModel):
    def __init__(self, config: dict):
        super().__init__(config)  # Gọi constructor của class cha
        self.client = AsyncOpenAI(api_key=config["api_key"])
        self.model = config["model_identifier"]

    async def predict(self, input_data: PredictionInput):
        # 1. Build prompt từ template
        prompt = build_price_prediction_prompt(input_data)

        # 2. Gọi OpenAI API
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert..."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        # 3. Parse kết quả
        result = json.loads(response.choices[0].message.content)

        # 4. Trả về PredictionOutput
        return PredictionOutput(
            predicted_value=result["prediction"],
            confidence_score=result["confidence"],
            reasoning=result["reasoning"],
            metadata={...}
        )
```

**Tại sao dùng Strategy Pattern?**

```python
# Tất cả adapters đều implement cùng interface
class AIModelInterface(ABC):
    async def predict(self, input_data):
        pass

# Pipeline không cần biết đang dùng provider nào
model = ModelFactory.create_model(provider, config)
result = await model.predict(input_data)  # Gọi giống nhau cho mọi provider
```

**Đọc tiếp:** Repository Pattern

---

### BƯỚC 6️⃣: Repository - Data Access Layer

**Đọc file:** [src/data/repositories/coin_repository.py](file:///home/ngocphat/learn/kien-truc-phan-mem/crypto/ai-prediction-service/src/data/repositories/coin_repository.py)

```python
class CoinRepository:
    def __init__(self, db: AsyncSession):
        self.db = db  # Database session

    async def get_by_symbol(self, symbol: str):
        # SQLAlchemy query
        result = await self.db.execute(
            select(Coin).where(Coin.symbol == symbol)
        )
        return result.scalar_one_or_none()

    async def create(self, symbol: str, name: str):
        coin = Coin(symbol=symbol, name=name)
        self.db.add(coin)
        await self.db.commit()
        await self.db.refresh(coin)
        return coin

    async def get_or_create(self, symbol: str, name: str):
        coin = await self.get_by_symbol(symbol)
        if not coin:
            coin = await self.create(symbol, name)
        return coin
```

**Tại sao dùng Repository?**

- Tách biệt logic database khỏi business logic
- Dễ test (có thể mock repository)
- Thay đổi database không ảnh hưởng business logic

**Đọc tiếp:** Pydantic Schemas

---

### BƯỚC 7️⃣: Pydantic Schemas - Validation

**Đọc file:** [src/schemas/prediction.py](file:///home/ngocphat/learn/kien-truc-phan-mem/crypto/ai-prediction-service/src/schemas/prediction.py)

```python
from pydantic import BaseModel, Field

# Schema cho request (input validation)
class PredictionRequest(BaseModel):
    coin_symbol: str = Field(..., max_length=20)  # Required, max 20 chars
    timeframe: str = Field(..., max_length=10)
    prediction_type: str = Field(default="price")  # Optional, default "price"
    model_name: Optional[str] = None  # Optional

# Schema cho response (output format)
class PredictionResponse(BaseModel):
    id: int
    coin_symbol: str
    predicted_value: Dict[str, Any]
    confidence_score: Optional[Decimal]
    reasoning: str
    created_at: datetime

    class Config:
        from_attributes = True  # Cho phép convert từ SQLAlchemy model
```

**Pydantic làm gì?**

```python
# ✅ Valid request
request = PredictionRequest(
    coin_symbol="BTC",
    timeframe="1h"
)

# ❌ Invalid request - Pydantic tự động raise error
request = PredictionRequest(
    coin_symbol="BITCOIN_SYMBOL_TOO_LONG",  # > 20 chars
    timeframe="1h"
)
# ValidationError: coin_symbol max_length is 20
```

---

## 🎓 Giải thích các khái niệm quan trọng

### 1. Dependency Injection (DI)

**Không dùng DI:**

```python
class PredictionPipeline:
    def __init__(self):
        # Hard-coded dependencies
        self.db = create_database_connection()
        self.cache = create_redis_connection()
```

**Dùng DI:**

```python
class PredictionPipeline:
    def __init__(self, db: AsyncSession):
        # Dependencies được inject từ bên ngoài
        self.db = db

# FastAPI tự động inject
@router.post("/")
async def create_prediction(db: AsyncSession = Depends(get_db)):
    pipeline = PredictionPipeline(db)
```

**Lợi ích:**

- Dễ test (inject mock dependencies)
- Loose coupling
- Dễ thay đổi implementation

### 2. Strategy Pattern

**Vấn đề:** Cần hỗ trợ nhiều AI providers, dễ thêm mới

**Giải pháp:**

```python
# 1. Define interface
class AIModelInterface(ABC):
    @abstractmethod
    async def predict(self, input_data):
        pass

# 2. Implement strategies
class OpenAIAdapter(AIModelInterface):
    async def predict(self, input_data):
        # OpenAI specific logic
        pass

class AnthropicAdapter(AIModelInterface):
    async def predict(self, input_data):
        # Anthropic specific logic
        pass

# 3. Use polymorphism
model: AIModelInterface = factory.create_model(provider)
result = await model.predict(input_data)  # Gọi giống nhau
```

### 3. Repository Pattern

**Vấn đề:** Business logic bị lẫn với database queries

**Giải pháp:**

```python
# ❌ Không dùng Repository
async def predict(coin_symbol: str):
    # Business logic lẫn với SQL
    result = await db.execute(
        select(Coin).where(Coin.symbol == coin_symbol)
    )
    coin = result.scalar_one_or_none()
    # ... more SQL queries ...

# ✅ Dùng Repository
async def predict(coin_symbol: str):
    # Business logic sạch
    coin = await coin_repo.get_by_symbol(coin_symbol)
    candles = await candle_repo.get_recent_candles(coin.id)
    # ... no SQL here ...
```

### 4. Factory Pattern

**Vấn đề:** Tạo objects phức tạp, nhiều điều kiện

**Giải pháp:**

```python
# ❌ Không dùng Factory
if provider == "openai":
    model = OpenAIAdapter(openai_config)
elif provider == "anthropic":
    model = AnthropicAdapter(anthropic_config)
# ... nhiều if-elif ...

# ✅ Dùng Factory
model = ModelFactory.create_model(provider, config)
```

---

## 💡 Ví dụ thực tế: Luồng xử lý 1 request

### Request: Dự đoán giá BTC

```bash
POST /api/v1/predictions/
{
  "coin_symbol": "BTC",
  "timeframe": "1h",
  "prediction_type": "price",
  "model_name": "openai"
}
```

### Luồng xử lý:

```
1. main.py
   ↓ FastAPI nhận request

2. api/routes/prediction.py
   ↓ Validate input với PredictionRequest schema
   ↓ Inject database session
   ↓ Tạo PredictionPipeline instance

3. core/pipeline/predictor.py
   ↓ get_by_symbol("BTC") → CoinRepository
   ↓ get_recent_candles() → CandleRepository
   ↓ get_recent_news() → NewsRepository
   ↓ generate_hash() → check cache
   ↓ create_model("openai") → ModelFactory

4. models/factory.py
   ↓ Lookup "openai" → OpenAIAdapter class
   ↓ Return OpenAIAdapter instance

5. models/adapters/openai_adapter.py
   ↓ build_price_prediction_prompt()
   ↓ Call OpenAI API
   ↓ Parse JSON response
   ↓ Return PredictionOutput

6. core/pipeline/predictor.py
   ↓ Save to database → PredictionRepository
   ↓ Return PredictionResponse

7. api/routes/prediction.py
   ↓ FastAPI serialize to JSON
   ↓ Return HTTP 200 với response body
```

---

## 📝 Checklist đọc hiểu

### Level 1: Cơ bản

- [ ] Hiểu dự án làm gì (đọc README)
- [ ] Biết database có những bảng gì (đọc schema.sql)
- [ ] Biết API có những endpoints gì (đọc routes/)
- [ ] Hiểu luồng xử lý cơ bản (main.py → routes → pipeline)

### Level 2: Trung bình

- [ ] Hiểu Strategy Pattern (Factory + Adapters)
- [ ] Hiểu Repository Pattern
- [ ] Hiểu Dependency Injection
- [ ] Biết cách thêm AI provider mới

### Level 3: Nâng cao

- [ ] Hiểu async/await hoạt động như thế nào
- [ ] Hiểu caching strategy
- [ ] Hiểu SQLAlchemy ORM
- [ ] Có thể extend thêm features mới

---

## 🎯 Bài tập thực hành

### Bài 1: Thêm endpoint mới

Tạo endpoint GET `/api/v1/predictions/{id}` để lấy prediction theo ID

### Bài 2: Thêm AI provider mới

Tạo `HuggingFaceAdapter` để support Hugging Face models

### Bài 3: Thêm prediction type mới

Thêm `volatility` prediction type với prompt template riêng

---

## 🔗 Tài liệu tham khảo

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Python Async/Await](https://docs.python.org/3/library/asyncio.html)

---

## ❓ Câu hỏi thường gặp

### Q: Tại sao dùng async/await?

**A:** Để xử lý nhiều requests đồng thời mà không bị block. Khi chờ database/API, Python có thể xử lý request khác.

### Q: Pydantic khác gì với dataclass?

**A:** Pydantic có validation tự động, serialization/deserialization, và integration tốt với FastAPI.

### Q: Tại sao cần nhiều layers (API, Core, Data)?

**A:** Separation of concerns - mỗi layer có trách nhiệm riêng, dễ maintain và test.

### Q: Factory Pattern khác gì với Strategy Pattern?

**A:**

- **Factory**: Tạo objects (how to create)
- **Strategy**: Định nghĩa behaviors (how to behave)

### Q: Khi nào dùng Repository Pattern?

**A:** Khi muốn tách biệt business logic khỏi data access logic, đặc biệt trong ứng dụng lớn.
