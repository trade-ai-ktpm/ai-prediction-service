from sqlalchemy import Column, Integer, TIMESTAMP, DECIMAL, ForeignKey, UniqueConstraint, func
from src.storage.database import Base


class CandleData(Base):
    __tablename__ = "candle_data_1m"
    
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, primary_key=True)
    open = Column(DECIMAL(20, 8), nullable=False)
    high = Column(DECIMAL(20, 8), nullable=False)
    low = Column(DECIMAL(20, 8), nullable=False)
    close = Column(DECIMAL(20, 8), nullable=False)
    volume = Column(DECIMAL(30, 8), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('coin_id', 'timestamp', name='uq_candle_data_1m'),
    )

