from typing import List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.dialects.postgresql import ARRAY
from src.data.models import NewsData
from src.config import get_logger

logger = get_logger(__name__)

# Symbol mapping
SYMBOL_MAPPING = {
    'BTCUSDT': 'BTC',
    'ETHUSDT': 'ETH',
    'BNBUSDT': 'BNB',
    'SOLUSDT': 'SOL',
    'ADAUSDT': 'ADA',
    'XRPUSDT': 'XRP',
    'DOGEUSDT': 'DOGE',
    'DOTUSDT': 'DOT',
    'MATICUSDT': 'MATIC',
    'AVAXUSDT': 'AVAX',
}


class NewsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def normalize_symbol(self, symbol: str) -> str:
        """Convert frontend symbol to database symbol"""
        return SYMBOL_MAPPING.get(symbol, symbol)
    
    async def get_by_id(self, news_id: int) -> NewsData | None:
        """Get news by ID"""
        query_str = "SELECT * FROM news_data WHERE id = :news_id"
        result = await self.db.execute(text(query_str), {"news_id": news_id})
        row = result.fetchone()
        
        if not row:
            return None
        
        return NewsData(
            id=row[0],
            title=row[1],
            content=row[2],
            url=row[3],
            source=row[4],
            published_at=row[5],
            coins=row[6]
        )
    
    async def get_recent_news(
        self,
        coin_symbol: str = None,
        limit: int = 20,
        days: int = 3
    ) -> List[NewsData]:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Base query
        query_str = """
            SELECT * FROM news_data
            WHERE published_at >= :cutoff_date
            AND content IS NOT NULL
            AND LENGTH(content) > 100
        """
        
        params = {"cutoff_date": cutoff_date, "limit": limit}
        
        if coin_symbol:
            # Normalize symbol and search in coins array
            normalized = self.normalize_symbol(coin_symbol)
            query_str += " AND :coin_symbol = ANY(coins)"
            params["coin_symbol"] = normalized
        
        query_str += " ORDER BY published_at DESC LIMIT :limit"
        
        result = await self.db.execute(text(query_str), params)
        rows = result.fetchall()
        
        # Convert rows to NewsData objects
        news_list = []
        for row in rows:
            news = NewsData(
                id=row[0],
                title=row[1],
                content=row[2],
                url=row[3],
                source=row[4],
                published_at=row[5],
                coins=row[6]
            )
            news_list.append(news)
        
        return news_list
