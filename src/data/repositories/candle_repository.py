from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.data.models import CandleData
from src.config import get_logger

logger = get_logger(__name__)


class CandleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_recent_candles(
        self,
        coin_id: int,
        timeframe: str,
        limit: int = 100
    ) -> List[CandleData]:
        result = await self.db.execute(
            select(CandleData)
            .where(
                and_(
                    CandleData.coin_id == coin_id,
                    CandleData.timeframe == timeframe
                )
            )
            .order_by(CandleData.timestamp.desc())
            .limit(limit)
        )
        candles = result.scalars().all()
        return list(reversed(candles))
    
    async def get_candles_in_range(
        self,
        coin_id: int,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[CandleData]:
        result = await self.db.execute(
            select(CandleData)
            .where(
                and_(
                    CandleData.coin_id == coin_id,
                    CandleData.timeframe == timeframe,
                    CandleData.timestamp >= start_time,
                    CandleData.timestamp <= end_time
                )
            )
            .order_by(CandleData.timestamp.asc())
        )
        return result.scalars().all()
