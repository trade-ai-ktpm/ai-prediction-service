from sqlalchemy import Column, Integer, String, TIMESTAMP, DECIMAL, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from src.storage.database import Base


class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50))
    prediction_type = Column(String(50), nullable=False)
    timeframe = Column(String(10), nullable=False)
    predicted_value = Column(JSONB, nullable=False)
    confidence_score = Column(DECIMAL(3, 2))
    input_data_hash = Column(String(64), index=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    valid_until = Column(TIMESTAMP)
    meta_data = Column("metadata", JSONB)
