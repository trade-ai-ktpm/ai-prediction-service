from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class CandleDataBase(BaseModel):
    timestamp: datetime
    open: Decimal = Field(..., decimal_places=8)
    high: Decimal = Field(..., decimal_places=8)
    low: Decimal = Field(..., decimal_places=8)
    close: Decimal = Field(..., decimal_places=8)
    volume: Decimal = Field(..., decimal_places=8)
    timeframe: str = Field(..., max_length=10)


class CandleDataCreate(CandleDataBase):
    coin_id: int


class CandleDataResponse(CandleDataBase):
    id: int
    coin_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
