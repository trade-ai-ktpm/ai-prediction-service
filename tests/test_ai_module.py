import asyncio
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from typing import Dict, Any
from src.models.factory import ModelFactory
from src.core.interfaces import PredictionInput


def create_mock_candle_data():
    """Tạo dữ liệu nến giả cho BTC"""
    base_price = 45000
    candles = []
    
    for i in range(5):
        timestamp = datetime.now() - timedelta(hours=5-i)
        open_price = base_price + (i * 100)
        high_price = open_price + 200
        low_price = open_price - 150
        close_price = open_price + 50
        
        candles.append({
            "timestamp": timestamp.isoformat(),
            "open": float(open_price),
            "high": float(high_price),
            "low": float(low_price),
            "close": float(close_price),
            "volume": 1000000.0 + (i * 10000),
            "timeframe": "1h"
        })
    
    return candles


def create_mock_news_data():
    """Tạo dữ liệu tin tức giả"""
    return [
        {
            "title": "Bitcoin reaches new all-time high",
            "content": "Bitcoin has surged to unprecedented levels...",
            "sentiment_score": 0.85,
            "published_at": (datetime.now() - timedelta(hours=2)).isoformat()
        },
        {
            "title": "Major institutional investors enter crypto market",
            "content": "Several large institutions announced crypto investments...",
            "sentiment_score": 0.75,
            "published_at": (datetime.now() - timedelta(hours=5)).isoformat()
        },
        {
            "title": "Regulatory concerns impact crypto prices",
            "content": "New regulations may affect cryptocurrency trading...",
            "sentiment_score": -0.3,
            "published_at": (datetime.now() - timedelta(hours=8)).isoformat()
        }
    ]


async def test_gemini_adapter():
    """Test Gemini adapter với mock data"""
    print("\n" + "="*60)
    print("🧪 Testing Gemini Adapter (gemini-2.5-flash)")
    print("="*60)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY không được set trong .env")
        return
    
    config = {
        "provider": "gemini",
        "model_identifier": "gemini-2.5-flash",
        "api_key": api_key,
        "temperature": 0.7
    }
    
    try:
        model = ModelFactory.create_model("gemini", config)
        print(f"✅ Model created: {model.get_model_info()}")
        
        input_data = PredictionInput(
            candle_data=create_mock_candle_data(),
            news_data=create_mock_news_data(),
            timeframe="1h",
            prediction_type="price"
        )
        
        print("\n📊 Input data:")
        print(f"  - Candles: {len(input_data.candle_data)} candles")
        print(f"  - News: {len(input_data.news_data)} articles")
        print(f"  - Timeframe: {input_data.timeframe}")
        print(f"  - Type: {input_data.prediction_type}")
        
        print("\n⏳ Calling Gemini API...")
        result = await model.predict(input_data)
        
        print("\n✅ Prediction Result:")
        print(f"  📈 Predicted Value: {result.predicted_value}")
        print(f"  🎯 Confidence Score: {result.confidence_score}")
        print(f"  💭 Reasoning: {result.reasoning[:200]}...")
        print(f"  📋 Metadata: {result.metadata}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_openai_adapter():
    """Test OpenAI adapter (optional)"""
    print("\n" + "="*60)
    print("🧪 Testing OpenAI Adapter")
    print("="*60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY không được set - bỏ qua test này")
        return
    
    config = {
        "provider": "openai",
        "model_identifier": "gpt-4-turbo-preview",
        "api_key": api_key,
        "temperature": 0.7
    }
    
    try:
        model = ModelFactory.create_model("openai", config)
        print(f"✅ Model created: {model.get_model_info()}")
        
        input_data = PredictionInput(
            candle_data=create_mock_candle_data(),
            news_data=create_mock_news_data(),
            timeframe="1h",
            prediction_type="price"
        )
        
        print("\n⏳ Calling OpenAI API...")
        result = await model.predict(input_data)
        
        print("\n✅ Prediction Result:")
        print(f"  📈 Predicted Value: {result.predicted_value}")
        print(f"  🎯 Confidence Score: {result.confidence_score}")
        print(f"  💭 Reasoning: {result.reasoning[:200]}...")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


async def main():
    """Main test function"""
    print("\n🚀 AI Module Test - Using Mock Data")
    print("="*60)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    await test_gemini_adapter()
    
    # await test_openai_adapter()
    
    print("\n" + "="*60)
    print("✅ Test completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
