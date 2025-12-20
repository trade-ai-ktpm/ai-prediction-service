import json
from typing import Dict, Any
from openai import AsyncOpenAI
from src.models.base import BaseAIModel
from src.core.interfaces import PredictionInput, PredictionOutput
from src.models.prompts import build_price_prediction_prompt, build_trend_analysis_prompt
from src.config import get_logger

logger = get_logger(__name__)


class OpenAIAdapter(BaseAIModel):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        api_key = config.get("api_key")
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = config.get("model_identifier", "gpt-4-turbo-preview")
        self.temperature = config.get("temperature", 0.7)
    
    async def predict(self, input_data: PredictionInput) -> PredictionOutput:
        if input_data.prediction_type == "price":
            prompt = build_price_prediction_prompt(input_data)
        elif input_data.prediction_type == "trend":
            prompt = build_trend_analysis_prompt(input_data)
        else:
            prompt = build_price_prediction_prompt(input_data)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a crypto price prediction expert. Always respond in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=self.temperature
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return PredictionOutput(
                predicted_value=result.get("prediction", {}),
                confidence_score=result.get("confidence", 0.5),
                reasoning=result.get("reasoning", ""),
                metadata={
                    "model": self.model,
                    "tokens": response.usage.total_tokens,
                    "provider": "openai"
                }
            )
        except Exception as e:
            logger.error(f"OpenAI prediction error: {str(e)}")
            raise
    
    async def validate_config(self) -> bool:
        try:
            await self.client.models.retrieve(self.model)
            return True
        except Exception as e:
            logger.error(f"OpenAI config validation failed: {str(e)}")
            return False
