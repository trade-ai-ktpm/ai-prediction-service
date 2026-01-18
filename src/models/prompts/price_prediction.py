from typing import Dict, Any
from src.core.interfaces import AIModelInterface, PredictionInput


def build_price_prediction_prompt(input_data: PredictionInput) -> str:
    candles = input_data.candle_data[-20:]
    news = input_data.news_data[-10:]
    
    prompt = f"""Bạn là chuyên gia phân tích và dự đoán giá cryptocurrency.

Dữ liệu nến gần nhất (timeframe: {input_data.timeframe}):
"""
    
    for candle in candles:
        prompt += f"\n- Thời gian: {candle.get('timestamp')}, Open: {candle.get('open')}, High: {candle.get('high')}, Low: {candle.get('low')}, Close: {candle.get('close')}, Volume: {candle.get('volume')}"
    
    if news:
        prompt += "\n\n**Tin tức gần đây được sử dụng để dự đoán:**\n"
        for idx, item in enumerate(news, 1):
            title = item.get('title', 'N/A')
            source = item.get('source', 'N/A')
            published = item.get('published_at', 'N/A')
            sentiment = item.get('sentiment_score', 'N/A')
            prompt += f"\n{idx}. [{published}] **{title}**"
            prompt += f"\n   - Nguồn: {source}"
            prompt += f"\n   - Sentiment: {sentiment}"
    
    prompt += f"""

Dựa trên dữ liệu biểu đồ nến và các tin tức trên, hãy dự đoán giá cho 10 phút tiếp theo (timeframe {input_data.timeframe}).

**Yêu cầu đặc biệt:**
1. Dự đoán trajectory gồm 5 mốc thời gian: +2 phút, +4 phút, +6 phút, +8 phút, +10 phút
2. Mỗi mốc dự đoán giá sẽ đạt ở thời điểm đó
3. Trajectory phải hợp lý và phản ánh xu hướng dự đoán

**Quan trọng:** Trong phần "reasoning", hãy giải thích cách bạn sử dụng từng tin tức trên để đưa ra dự đoán. Nêu rõ tin tức nào ảnh hưởng tích cực, tin tức nào ảnh hưởng tiêu cực, và tại sao.

Trả về kết quả dưới dạng JSON với format:
{{
    "prediction": {{
        "price_direction": "up/down/sideways",
        "estimated_price_range": {{
            "low": <số>,
            "high": <số>
        }},
        "trajectory": [
            {{"time_offset_seconds": 120, "price": <giá dự đoán sau 2 phút>}},
            {{"time_offset_seconds": 240, "price": <giá dự đoán sau 4 phút>}},
            {{"time_offset_seconds": 360, "price": <giá dự đoán sau 6 phút>}},
            {{"time_offset_seconds": 480, "price": <giá dự đoán sau 8 phút>}},
            {{"time_offset_seconds": 600, "price": <giá dự đoán sau 10 phút>}}
        ],
        "key_levels": {{
            "support": [<số>],
            "resistance": [<số>]
        }}
    }},
    "confidence": <0.0-1.0>,
    "reasoning": "<lý do ngắn gọn (TỐI ĐA 500 từ), tóm tắt các yếu tố chính ảnh hưởng đến dự đoán>"
}}
"""
    
    return prompt


def build_trend_analysis_prompt(input_data: PredictionInput) -> str:
    candles = input_data.candle_data[-50:]
    
    prompt = f"""Phân tích xu hướng thị trường cryptocurrency.

Dữ liệu {len(candles)} nến gần nhất (timeframe: {input_data.timeframe}):
"""
    
    for candle in candles:
        prompt += f"\n- {candle.get('timestamp')}: Close={candle.get('close')}, Volume={candle.get('volume')}"
    
    prompt += """

Phân tích xu hướng và trả về JSON:
{
    "prediction": {
        "trend": "bullish/bearish/neutral",
        "strength": "weak/moderate/strong",
        "duration_estimate": "<thời gian dự kiến>"
    },
    "confidence": <0.0-1.0>,
    "reasoning": "<phân tích ngắn gọn (TỐI ĐA 300 từ)>"
}
"""
    
    return prompt
