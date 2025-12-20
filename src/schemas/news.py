from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class NewsDataBase(BaseModel):
    title: str
    content: Optional[str] = None
    source: Optional[str] = Field(None, max_length=200)
    url: Optional[str] = None
    published_at: datetime
    sentiment_score: Optional[Decimal] = Field(None, ge=-1.0, le=1.0)
    coins: Optional[List[str]] = None


class NewsDataCreate(NewsDataBase):
    pass


class NewsDataResponse(NewsDataBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
