from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class CandleDataBase(BaseModel):
    timestamp: datetime
    open: Decimal = Field(...)
    high: Decimal = Field(...)
    low: Decimal = Field(...)
    close: Decimal = Field(...)
    volume: Decimal = Field(...)
    timeframe: str = Field(..., max_length=10)


class CandleDataCreate(CandleDataBase):
    coin_id: int


class CandleDataResponse(CandleDataBase):
    id: int
    coin_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
