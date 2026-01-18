from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime
from decimal import Decimal


class NewsSource(BaseModel):
    title: str
    source: str
    url: str
    published_at: str


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
    confidence_score: Optional[float]
    
    @field_serializer('confidence_score')
    def serialize_confidence(self, value: Optional[Decimal]) -> Optional[float]:
        return float(value) if value is not None else None
    reasoning: Optional[str] = None
    status: str = "COMPLETED"
    error_message: Optional[str] = None
    created_at: datetime
    valid_until: Optional[datetime]
    metadata: Optional[Dict[str, Any]]
    sources: Optional[List[NewsSource]] = None
    
    class Config:
        from_attributes = True


class PredictionCreate(BaseModel):
    coin_id: int
    model_name: str = "pending"
    model_version: Optional[str] = None
    prediction_type: str
    timeframe: str
    predicted_value: Dict[str, Any] = {}
    confidence_score: Optional[Decimal] = None
    input_data_hash: Optional[str] = None
    status: str = "PENDING"
    error_message: Optional[str] = None
    valid_until: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
