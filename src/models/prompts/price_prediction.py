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
        prompt += "\n\nTin tức gần đây:\n"
        for item in news:
            prompt += f"\n- [{item.get('published_at')}] {item.get('title')} (Sentiment: {item.get('sentiment_score', 'N/A')})"
    
    prompt += f"""

Dựa trên dữ liệu trên, hãy dự đoán giá cho timeframe {input_data.timeframe} tiếp theo.

Trả về kết quả dưới dạng JSON với format:
{{
    "prediction": {{
        "price_direction": "up/down/sideways",
        "estimated_price_range": {{
            "low": <số>,
            "high": <số>
        }},
        "key_levels": {{
            "support": [<số>],
            "resistance": [<số>]
        }}
    }},
    "confidence": <0.0-1.0>,
    "reasoning": "<lý do chi tiết>"
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
    "reasoning": "<phân tích chi tiết>"
}
"""
    
    return prompt
