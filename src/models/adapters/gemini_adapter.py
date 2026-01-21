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
        
        # Define JSON schema to enforce strict JSON output
        response_schema = {
            "type": "object",
            "properties": {
                "prediction": {
                    "type": "object",
                    "properties": {
                        "price_direction": {"type": "string"},
                        "estimated_price_range": {
                            "type": "object",
                            "properties": {
                                "low": {"type": "number"},
                                "high": {"type": "number"}
                            },
                            "required": ["low", "high"]
                        },
                        "trajectory": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "time_offset_seconds": {"type": "integer"},
                                    "price": {"type": "number"}
                                },
                                "required": ["time_offset_seconds", "price"]
                            }
                        },
                        "key_levels": {
                            "type": "object",
                            "properties": {
                                "support": {
                                    "type": "array",
                                    "items": {"type": "number"}
                                },
                                "resistance": {
                                    "type": "array",
                                    "items": {"type": "number"}
                                }
                            },
                            "required": ["support", "resistance"]
                        }
                    },
                    "required": ["price_direction", "estimated_price_range", "trajectory", "key_levels"]
                },
                "confidence": {"type": "number"},
                "reasoning": {"type": "string"}
            },
            "required": ["prediction", "confidence", "reasoning"]
        }
        
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=8192,
                    candidate_count=1,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                )
            )
            
            # Debug: Check finish_reason and safety_ratings
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                logger.info(f"Gemini finish_reason: {candidate.finish_reason}")
                if hasattr(candidate, 'safety_ratings'):
                    logger.info(f"Gemini safety_ratings: {candidate.safety_ratings}")
            
            content = response.text
            logger.info(f"Gemini raw response length: {len(content)}")
            
            if not content or not content.strip():
                raise ValueError(f"Empty response from Gemini. Response object: {response}")
            
            logger.info(f"Gemini raw response: {content[:500]}")
            
            # With response_schema, Gemini should return pure JSON
            # No need for complex extraction logic
            try:
                result = json.loads(content)
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON parsing failed: {str(json_err)}")
                logger.error(f"Response content: {content}")
                raise ValueError(f"Invalid JSON from Gemini: {str(json_err)}")
            
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
