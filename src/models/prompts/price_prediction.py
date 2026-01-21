from typing import Dict, Any
from src.core.interfaces import AIModelInterface, PredictionInput


def build_price_prediction_prompt(input_data: PredictionInput) -> str:
    candles = input_data.candle_data[-10:]  # Reduce to 10 candles
    news = input_data.news_data[-5:]  # Reduce to 5 news items
    
    prompt = f"""You are a cryptocurrency price prediction expert.

Recent candle data (timeframe: {input_data.timeframe}):
"""
    
    for candle in candles:
        prompt += f"\n- Time: {candle.get('timestamp')}, Open: {candle.get('open')}, High: {candle.get('high')}, Low: {candle.get('low')}, Close: {candle.get('close')}, Volume: {candle.get('volume')}"
    
    if news:
        prompt += "\n\n**Recent news:**\n"
        for idx, item in enumerate(news, 1):
            title = item.get('title', 'N/A')
            source = item.get('source', 'N/A')
            published = item.get('published_at', 'N/A')
            prompt += f"\n{idx}. [{published}] {title} (Source: {source})"
    
    prompt += f"""

Dựa trên dữ liệu nến và tin tức trên, hãy dự đoán giá cho 6 phút tiếp theo (khung thời gian {input_data.timeframe}).

Cung cấp:
- price_direction: "up" (tăng), "down" (giảm), hoặc "sideways" (đi ngang)
- estimated_price_range: dự đoán giá thấp nhất và cao nhất
- trajectory: 10 điểm giá tại các mốc thời gian 36s, 72s, 108s, 144s, 180s, 216s, 252s, 288s, 324s, 360s
- key_levels: các mức hỗ trợ (support) và kháng cự (resistance)
- confidence: điểm tin cậy từ 0.0 đến 1.0
- reasoning: PHÂN TÍCH CHI TIẾT BẰNG TIẾNG VIỆT (200-300 từ), bao gồm:
  + Phân tích xu hướng giá từ dữ liệu nến
  + Đánh giá khối lượng giao dịch
  + Tác động của tin tức (nếu có)
  + Các chỉ báo kỹ thuật quan trọng
  + Lý do cho dự đoán hướng giá
  + Các yếu tố rủi ro cần lưu ý
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
