from sqlalchemy import Column, Integer, String, TIMESTAMP, DECIMAL, ForeignKey, UniqueConstraint, func
from src.storage.database import Base


class CandleData(Base):
    __tablename__ = "candle_data"
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False)
    open = Column(DECIMAL(20, 8), nullable=False)
    high = Column(DECIMAL(20, 8), nullable=False)
    low = Column(DECIMAL(20, 8), nullable=False)
    close = Column(DECIMAL(20, 8), nullable=False)
    volume = Column(DECIMAL(30, 8), nullable=False)
    timeframe = Column(String(10), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('coin_id', 'timestamp', 'timeframe', name='uq_candle_data'),
    )
