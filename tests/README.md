# 🧪 Hướng dẫn chạy test AI Module

## ✅ Containers đã sẵn sàng!

Tất cả Docker containers đang chạy:

- ✅ PostgreSQL (port 5401)
- ✅ Redis (port 6380)
- ✅ API Service (port 8001)

---

## 🚀 Cách chạy test

### Chạy test trong Docker container:

```bash
docker exec -it ai-prediction-api python tests/test_ai_module.py
```

**Lưu ý:** Bạn cần có `GEMINI_API_KEY` trong file `.env` để test Gemini adapter!

---

## 📝 Kiểm tra .env file

Đảm bảo file `.env` có:

```bash
GEMINI_API_KEY=your_actual_google_api_key_here
```

Nếu chưa có, thêm API key vào `.env` rồi restart container:

```bash
docker compose -f docker/docker-compose.yml restart api
```

---

## 🎯 Kết quả mong đợi

Nếu test chạy thành công, bạn sẽ thấy:

```
🚀 AI Module Test - Using Mock Data
============================================================

🧪 Testing Gemini Adapter (gemini-2.0-flash-exp)
============================================================
✅ Model created: {'provider': 'gemini', 'model': 'gemini-2.0-flash-exp', 'version': '1.0'}

📊 Input data:
  - Candles: 50 candles
  - News: 3 articles
  - Timeframe: 1h
  - Type: price

⏳ Calling Gemini API...

✅ Prediction Result:
  📈 Predicted Value: {...}
  🎯 Confidence Score: 0.85
  💭 Reasoning: ...
```

---

## 🔧 Troubleshooting

### Lỗi: "GEMINI_API_KEY không được set"

```bash
# Kiểm tra .env
cat .env | grep GEMINI_API_KEY

# Nếu chưa có, thêm vào .env
echo "GEMINI_API_KEY=your_key_here" >> .env

# Restart API container
docker compose -f docker/docker-compose.yml restart api
```

### Lỗi: "Module not found"

Container đã mount đúng thư mục tests, nếu vẫn lỗi thử rebuild:

```bash
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml up -d
```

---

## 📚 Test file location

- **Local:** `/home/ngocphat/learn/kien-truc-phan-mem/crypto/ai-prediction-service/tests/test_ai_module.py`
- **Container:** `/app/tests/test_ai_module.py`

---

## 🎉 Bây giờ hãy chạy test!

```bash
docker exec -it ai-prediction-api python tests/test_ai_module.py
```
