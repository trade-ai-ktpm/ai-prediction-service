from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.data.models import Coin
from src.config import get_logger

logger = get_logger(__name__)


class CoinRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, coin_id: int) -> Optional[Coin]:
        result = await self.db.execute(
            select(Coin).where(Coin.id == coin_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_symbol(self, symbol: str) -> Optional[Coin]:
        # Query directly with full symbol (e.g., BTCUSDT)
        result = await self.db.execute(
            select(Coin).where(Coin.symbol == symbol)
        )
        return result.scalar_one_or_none()
    
    async def create(self, symbol: str, name: str) -> Coin:
        coin = Coin(symbol=symbol, name=name)
        self.db.add(coin)
        await self.db.commit()
        await self.db.refresh(coin)
        logger.info(f"Created coin: {symbol}")
        return coin
    
    async def get_or_create(self, symbol: str, name: str = None) -> Coin:
        coin = await self.get_by_symbol(symbol)
        if not coin:
            coin = await self.create(symbol, name or symbol)
        return coin
