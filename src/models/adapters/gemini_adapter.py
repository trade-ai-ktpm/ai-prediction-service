import json
from typing import Dict, Any
import google.generativeai as genai
from src.models.base import BaseAIModel
from src.core.interfaces import PredictionInput, PredictionOutput
from src.models.prompts import build_price_prediction_prompt, build_trend_analysis_prompt
from src.config import get_logger

logger = get_logger(__name__)


class GeminiAdapter(BaseAIModel):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        api_key = config.get("api_key")
        if not api_key:
            raise ValueError("Google API key is required")
        
        genai.configure(api_key=api_key)
        
        from src.config import settings
        self.model_name = config.get("model_identifier", settings.DEFAULT_GEMINI_MODEL)
        self.model = genai.GenerativeModel(self.model_name)
        self.temperature = config.get("temperature", 0.7)
    
    async def predict(self, input_data: PredictionInput) -> PredictionOutput:
        if input_data.prediction_type == "price":
            prompt = build_price_prediction_prompt(input_data)
        elif input_data.prediction_type == "trend":
            prompt = build_trend_analysis_prompt(input_data)
        else:
            prompt = build_price_prediction_prompt(input_data)
        
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                )
            )
            
            content = response.text
            print(f"DEBUG - Raw response length: {len(content)}")
            print(f"DEBUG - Raw response (first 300 chars): {content[:300]}")
            
            if not content or not content.strip():
                raise ValueError(f"Empty response from Gemini. Response object: {response}")
            
            logger.info(f"Gemini raw response: {content[:500]}")
            
            # Extract JSON from markdown code block if present
            if "```json" in content or "```" in content:
                # Find the JSON block
                import re
                # Match ```json ... ``` or ``` ... ```
                json_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1).strip()
                    print(f"DEBUG - Extracted JSON from markdown block")
                else:
                    # Fallback: remove first and last ``` lines
                    lines = content.strip().split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].strip() == "```":
                        lines = lines[:-1]
                    content = "\n".join(lines)
            
            print(f"DEBUG - Cleaned content (first 300 chars): {content[:300]}")
            logger.info(f"Gemini cleaned content: {content[:500]}")
            
            if not content.strip():
                raise ValueError("Content is empty after cleaning markdown")
            
            result = json.loads(content)
            
            return PredictionOutput(
                predicted_value=result.get("prediction", {}),
                confidence_score=result.get("confidence", 0.5),
                reasoning=result.get("reasoning", ""),
                metadata={
                    "model": self.model_name,
                    "provider": "gemini"
                }
            )
        except Exception as e:
            logger.error(f"Gemini prediction error: {str(e)}")
            raise
    
    async def validate_config(self) -> bool:
        try:
            await self.model.generate_content_async("test")
            return True
        except Exception as e:
            logger.error(f"Gemini config validation failed: {str(e)}")
            return False
