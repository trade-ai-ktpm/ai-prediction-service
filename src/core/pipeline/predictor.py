from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.interfaces import AIModelInterface, PredictionInput, PredictionOutput
from src.data.repositories import CoinRepository, CandleRepository, NewsRepository, PredictionRepository
from src.models.factory import ModelFactory
from src.schemas.prediction import PredictionCreate, PredictionResponse
from src.utils import generate_hash
from src.config import settings, get_logger
from src.core.exceptions import ModelNotFoundError, InvalidInputError
from src.storage import cache_manager

logger = get_logger(__name__)


class PredictionPipeline:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.coin_repo = CoinRepository(db)
        self.candle_repo = CandleRepository(db)
        self.news_repo = NewsRepository(db)
        self.prediction_repo = PredictionRepository(db)
    
    async def predict_async(
        self,
        coin_symbol: str,
        timeframe: str,
        prediction_type: str = "price",
        model_name: Optional[str] = None
    ) -> PredictionResponse:
        """Synchronous prediction - executes immediately and returns result"""
        coin = await self.coin_repo.get_by_symbol(coin_symbol)
        if not coin:
            raise InvalidInputError(f"Coin {coin_symbol} not found")
        
        # Check Redis cache first (5 minutes TTL)
        cache_key = f"pred:sync:{coin_symbol}:{timeframe}"
        cached_data = await cache_manager.get(cache_key)
        if cached_data:
            logger.info(f"Cache HIT for {coin_symbol} {timeframe}")
            return PredictionResponse(**cached_data)
        
        logger.info(f"Cache MISS for {coin_symbol} {timeframe} - executing prediction now")
        
        # Execute prediction immediately
        result = await self.execute_prediction(
            coin_symbol=coin_symbol,
            timeframe=timeframe,
            prediction_type=prediction_type,
            model_name=model_name
        )
        
        # Build response with news sources
        sources = []
        if result.metadata and "news_ids" in result.metadata:
            for news_id in result.metadata["news_ids"][:5]:
                news = await self.news_repo.get_by_id(news_id)
                if news:
                    sources.append({
                        "title": news.title,
                        "source": news.source,
                        "url": news.url,
                        "published_at": news.published_at.isoformat() if news.published_at else None
                    })
        
        response = PredictionResponse(
            id=result.id,
            coin_id=result.coin_id,
            coin_symbol=coin_symbol,
            model_name=result.model_name,
            model_version=result.model_version,
            prediction_type=result.prediction_type,
            timeframe=result.timeframe,
            predicted_value=result.predicted_value,
            confidence_score=result.confidence_score,
            reasoning=result.metadata.get("reasoning") if result.metadata else None,
            status="COMPLETED",
            error_message=None,
            created_at=result.created_at,
            valid_until=result.valid_until,
            metadata=result.metadata,
            sources=sources if sources else None
        )
        
        # Cache for 8 minutes (less than 10min prediction duration)
        await cache_manager.set(cache_key, response.dict(), ttl=480)
        logger.info(f"Cached prediction for {coin_symbol} {timeframe} (8min TTL)")
        
        return response
        
        return PredictionResponse(
            id=pending_prediction.id,
            coin_id=pending_prediction.coin_id,
            coin_symbol=coin_symbol,
            model_name="pending",
            model_version=None,
            prediction_type=prediction_type,
            timeframe=timeframe,
            predicted_value={},
            confidence_score=None,
            reasoning=None,
            status="PENDING",
            created_at=pending_prediction.created_at,
            valid_until=None,
            metadata={"task_id": task.id}
        )
    
    async def execute_prediction(
        self,
        coin_symbol: str,
        timeframe: str,
        prediction_type: str = "price",
        model_name: Optional[str] = None
    ) -> PredictionOutput:
        """Execute actual AI prediction - called by Celery task"""
        coin = await self.coin_repo.get_by_symbol(coin_symbol)
        if not coin:
            raise InvalidInputError(f"Coin {coin_symbol} not found")
        
        candles = await self.candle_repo.get_recent_candles(
            coin.id,
            timeframe,
            limit=settings.MAX_CANDLES
        )
        
        if not candles:
            raise InvalidInputError(f"No candle data found for {coin_symbol}")
        
        news = await self.news_repo.get_recent_news(
            coin_symbol=coin_symbol,
            limit=settings.MAX_NEWS
        )
        
        candle_data = [
            {
                "timestamp": str(c["timestamp"]) if isinstance(c, dict) else str(c.timestamp),
                "open": float(c["open"]) if isinstance(c, dict) else float(c.open),
                "high": float(c["high"]) if isinstance(c, dict) else float(c.high),
                "low": float(c["low"]) if isinstance(c, dict) else float(c.low),
                "close": float(c["close"]) if isinstance(c, dict) else float(c.close),
                "volume": float(c["volume"]) if isinstance(c, dict) else float(c.volume)
            }
            for c in candles
        ]
        
        news_data = [
            {
                "title": n.title,
                "content": n.content[:500] if n.content else "",
                "source": n.source,
                "url": n.url,
                "published_at": str(n.published_at)
            }
            for n in news
        ]
        
        news_sources = [
            {
                "title": n.title,
                "source": n.source,
                "url": n.url,
                "published_at": str(n.published_at)
            }
            for n in news[:10]
        ]
        
        # Parse provider from model_name if provided
        # model_name can be: "gemini", "gemini-default", "openai-gpt4", etc.
        if model_name:
            # Extract provider (first part before hyphen)
            provider = model_name.split('-')[0]
        else:
            provider = settings.DEFAULT_MODEL_PROVIDER
        
        model_config = await self._get_model_config(provider)
        
        model = ModelFactory.create_model(provider, model_config)
        
        prediction_input = PredictionInput(
            candle_data=candle_data,
            news_data=news_data,
            timeframe=timeframe,
            prediction_type=prediction_type
        )
        
        result = await model.predict(prediction_input)
        
        model_info = model.get_model_info()
        result.model_name = model_info["model"]
        result.model_version = model_info["version"]
        
        result.metadata = result.metadata or {}
        result.metadata["sources"] = news_sources
        result.metadata["news_ids"] = [n.id for n in news[:5]]
        result.metadata["reasoning"] = result.reasoning
        
        # Save to database
        prediction_create = PredictionCreate(
            coin_id=coin.id,
            model_name=result.model_name,
            model_version=result.model_version,
            prediction_type=prediction_type,
            timeframe=timeframe,
            predicted_value=result.predicted_value,
            confidence_score=result.confidence_score,
            status="COMPLETED",
            metadata=result.metadata,
            valid_until=datetime.utcnow() + timedelta(hours=1)
        )
        
        saved_prediction = await self.prediction_repo.create(prediction_create)
        logger.info(f"Saved prediction ID: {saved_prediction.id} for {coin_symbol}")
        
        return saved_prediction
    
    async def _get_model_config(self, provider: str) -> dict:
        config = {
            "provider": provider,
            "model_identifier": "",
            "api_key": ""
        }
        
        if provider == "openai":
            config["model_identifier"] = settings.DEFAULT_OPENAI_MODEL
            config["api_key"] = settings.OPENAI_API_KEY
        elif provider == "anthropic":
            config["model_identifier"] = settings.DEFAULT_ANTHROPIC_MODEL
            config["api_key"] = settings.ANTHROPIC_API_KEY
        elif provider == "gemini":
            config["model_identifier"] = settings.DEFAULT_GEMINI_MODEL
            config["api_key"] = settings.GEMINI_API_KEY
        else:
            raise ModelNotFoundError(f"Unknown provider: {provider}")
        
        return config
