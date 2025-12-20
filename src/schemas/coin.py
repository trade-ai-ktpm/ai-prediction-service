from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CoinBase(BaseModel):
    symbol: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)


class CoinCreate(CoinBase):
    pass


class CoinResponse(CoinBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
