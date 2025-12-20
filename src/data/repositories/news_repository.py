from typing import List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from src.data.models import NewsData
from src.config import get_logger

logger = get_logger(__name__)


class NewsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_recent_news(
        self,
        coin_symbol: str = None,
        limit: int = 50,
        days: int = 7
    ) -> List[NewsData]:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(NewsData).where(
            NewsData.published_at >= cutoff_date
        )
        
        if coin_symbol:
            query = query.where(
                NewsData.coins.contains([coin_symbol])
            )
        
        query = query.order_by(NewsData.published_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
