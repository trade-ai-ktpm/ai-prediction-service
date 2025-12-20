from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel


class PredictionInput(BaseModel):
    candle_data: List[Dict[str, Any]]
    news_data: List[Dict[str, Any]]
    timeframe: str
    prediction_type: str


class PredictionOutput(BaseModel):
    predicted_value: Dict[str, Any]
    confidence_score: float
    reasoning: str
    metadata: Dict[str, Any]


class AIModelInterface(ABC):
    @abstractmethod
    async def predict(self, input_data: PredictionInput) -> PredictionOutput:
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        pass
    
    @abstractmethod
    async def validate_config(self) -> bool:
        pass
