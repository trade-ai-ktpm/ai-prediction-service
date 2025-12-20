from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class PredictionRequest(BaseModel):
    coin_symbol: str = Field(..., max_length=20)
    timeframe: str = Field(..., max_length=10)
    prediction_type: str = Field(default="price", max_length=50)
    model_name: Optional[str] = None


class PredictionResponse(BaseModel):
    id: int
    coin_id: int
    coin_symbol: str
    model_name: str
    model_version: Optional[str]
    prediction_type: str
    timeframe: str
    predicted_value: Dict[str, Any]
    confidence_score: Optional[Decimal]
    reasoning: str
    created_at: datetime
    valid_until: Optional[datetime]
    metadata: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class PredictionCreate(BaseModel):
    coin_id: int
    model_name: str
    model_version: Optional[str] = None
    prediction_type: str
    timeframe: str
    predicted_value: Dict[str, Any]
    confidence_score: Optional[Decimal] = None
    input_data_hash: Optional[str] = None
    valid_until: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
