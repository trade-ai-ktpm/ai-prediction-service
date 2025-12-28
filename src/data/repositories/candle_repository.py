from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text
from src.data.models import CandleData
from src.config import get_logger

logger = get_logger(__name__)


class CandleRepository:
    TIMEFRAME_TABLE_MAP = {
        '1m': 'candle_data_1m',
        '5m': 'candle_data_5m',
        '15m': 'candle_data_15m',
        '1h': 'candle_data_1h',
        '4h': 'candle_data_4h',
        '1d': 'candle_data_1d'
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _get_table_name(self, timeframe: str) -> str:
        table_name = self.TIMEFRAME_TABLE_MAP.get(timeframe, 'candle_data_1m')
        if timeframe not in self.TIMEFRAME_TABLE_MAP:
            logger.warning(f"Unknown timeframe '{timeframe}', defaulting to 1m")
        return table_name
    
    async def get_recent_candles(
        self,
        coin_id: int,
        timeframe: str,
        limit: int = 100
    ) -> List[dict]:
        table_name = self._get_table_name(timeframe)
        
        query = text(f"""
            SELECT coin_id, timestamp, open, high, low, close, volume
            FROM {table_name}
            WHERE coin_id = :coin_id
            ORDER BY timestamp DESC
            LIMIT :limit
        """)
        
        result = await self.db.execute(
            query,
            {"coin_id": coin_id, "limit": limit}
        )
        
        candles = result.fetchall()
        return [
            {
                "coin_id": row[0],
                "timestamp": row[1],
                "open": row[2],
                "high": row[3],
                "low": row[4],
                "close": row[5],
                "volume": row[6]
            }
            for row in reversed(candles)
        ]
    
    async def get_candles_in_range(
        self,
        coin_id: int,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[dict]:
        table_name = self._get_table_name(timeframe)
        
        query = text(f"""
            SELECT coin_id, timestamp, open, high, low, close, volume
            FROM {table_name}
            WHERE coin_id = :coin_id
              AND timestamp >= :start_time
              AND timestamp <= :end_time
            ORDER BY timestamp ASC
        """)
        
        result = await self.db.execute(
            query,
            {
                "coin_id": coin_id,
                "start_time": start_time,
                "end_time": end_time
            }
        )
        
        candles = result.fetchall()
        return [
            {
                "coin_id": row[0],
                "timestamp": row[1],
                "open": row[2],
                "high": row[3],
                "low": row[4],
                "close": row[5],
                "volume": row[6]
            }
            for row in candles
        ]
    
    async def insert_candle_1m(
        self,
        coin_id: int,
        timestamp: datetime,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float
    ) -> None:
        candle = CandleData(
            coin_id=coin_id,
            timestamp=timestamp,
            open=open,
            high=high,
            low=low,
            close=close,
            volume=volume
        )
        self.db.add(candle)
        await self.db.commit()
        logger.info(f"Inserted 1m candle for coin_id={coin_id} at {timestamp}")

