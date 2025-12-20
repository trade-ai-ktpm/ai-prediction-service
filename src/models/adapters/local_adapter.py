from typing import Dict, Any
from src.models.base import BaseAIModel
from src.core.interfaces import PredictionInput, PredictionOutput
from src.config import get_logger

logger = get_logger(__name__)


class LocalAdapter(BaseAIModel):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model_path = config.get("model_path", "")
        logger.info(f"Local model adapter initialized with path: {self.model_path}")
    
    async def predict(self, input_data: PredictionInput) -> PredictionOutput:
        logger.warning("Local model prediction not implemented yet")
        
        return PredictionOutput(
            predicted_value={
                "price_direction": "sideways",
                "estimated_price_range": {"low": 0, "high": 0}
            },
            confidence_score=0.0,
            reasoning="Local model not implemented",
            metadata={
                "model": "local",
                "provider": "local"
            }
        )
    
    async def validate_config(self) -> bool:
        return True
