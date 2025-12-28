from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.interfaces import AIModelInterface, PredictionInput, PredictionResult
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
        """Entry point for async predictions - checks cache and enqueues task if needed"""
        coin = await self.coin_repo.get_by_symbol(coin_symbol)
        if not coin:
            raise InvalidInputError(f"Coin {coin_symbol} not found")
        
        # Tier 1: Check Redis cache (pre-computed)
        cache_key = f"pred:latest:{coin_symbol}:{timeframe}"
        cached_data = await cache_manager.get(cache_key)
        if cached_data:
            logger.info(f"Cache HIT (tier 1) for {coin_symbol} {timeframe}")
            return PredictionResponse(**cached_data)
        
        # Tier 2: Check DB cache (recent predictions)
        db_cached = await self.prediction_repo.get_latest_by_coin(
            coin.id,
            timeframe,
            prediction_type,
            max_age_hours=1
        )
        if db_cached:
            logger.info(f"Cache HIT (tier 2) for {coin_symbol} {timeframe}")
            response = PredictionResponse(
                id=db_cached.id,
                coin_id=db_cached.coin_id,
                coin_symbol=coin_symbol,
                model_name=db_cached.model_name,
                model_version=db_cached.model_version,
                prediction_type=db_cached.prediction_type,
                timeframe=db_cached.timeframe,
                predicted_value=db_cached.predicted_value,
                confidence_score=db_cached.confidence_score,
                reasoning=db_cached.meta_data.get("reasoning") if db_cached.meta_data else None,
                status=db_cached.status,
                created_at=db_cached.created_at,
                valid_until=db_cached.valid_until,
                metadata=db_cached.meta_data
            )
            # Warm Redis cache
            await cache_manager.set(cache_key, response.dict(), ttl=1200)
            return response
        
        # Tier 3: Create PENDING prediction and enqueue task
        logger.info(f"Cache MISS for {coin_symbol} {timeframe} - creating async task")
        
        prediction_create = PredictionCreate(
            coin_id=coin.id,
            prediction_type=prediction_type,
            timeframe=timeframe,
            status="PENDING"
        )
        
        pending_prediction = await self.prediction_repo.create(prediction_create)
        
        # Enqueue Celery task
        from src.tasks.prediction_task import create_prediction_task
        task = create_prediction_task.delay(
            pending_prediction.id,
            coin_symbol,
            timeframe,
            prediction_type,
            model_name
        )
        
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
    ) -> PredictionResult:
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
                "published_at": str(n.published_at),
                "sentiment_score": float(n.sentiment_score) if n.sentiment_score else None
            }
            for n in news
        ]
        
        provider = model_name or settings.DEFAULT_MODEL_PROVIDER
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
        
        return result
    
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
