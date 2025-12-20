from typing import Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ModelConfigBase(BaseModel):
    name: str = Field(..., max_length=100)
    provider: str = Field(..., max_length=50)
    model_identifier: str = Field(..., max_length=200)
    config: Dict[str, Any]
    is_active: bool = True


class ModelConfigCreate(ModelConfigBase):
    pass


class ModelConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    provider: Optional[str] = Field(None, max_length=50)
    model_identifier: Optional[str] = Field(None, max_length=200)
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ModelConfigResponse(ModelConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
