from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.interfaces import AIModelInterface, PredictionInput
from src.data.repositories import CoinRepository, CandleRepository, NewsRepository, PredictionRepository
from src.models.factory import ModelFactory
from src.schemas.prediction import PredictionCreate, PredictionResponse
from src.utils import generate_hash
from src.config import settings, get_logger
from src.core.exceptions import ModelNotFoundError, InvalidInputError

logger = get_logger(__name__)


class PredictionPipeline:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.coin_repo = CoinRepository(db)
        self.candle_repo = CandleRepository(db)
        self.news_repo = NewsRepository(db)
        self.prediction_repo = PredictionRepository(db)
    
    async def predict(
        self,
        coin_symbol: str,
        timeframe: str,
        prediction_type: str = "price",
        model_name: Optional[str] = None
    ) -> PredictionResponse:
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
                "timestamp": str(c.timestamp),
                "open": float(c.open),
                "high": float(c.high),
                "low": float(c.low),
                "close": float(c.close),
                "volume": float(c.volume)
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
        
        input_hash = generate_hash({
            "coin_id": coin.id,
            "timeframe": timeframe,
            "prediction_type": prediction_type,
            "candles": candle_data[-20:],
            "news": news_data[-10:]
        })
        
        cached = await self.prediction_repo.get_cached_prediction(
            input_hash,
            datetime.utcnow() - timedelta(hours=1)
        )
        
        if cached:
            logger.info(f"Using cached prediction for {coin_symbol}")
            return PredictionResponse(
                id=cached.id,
                coin_id=cached.coin_id,
                coin_symbol=coin_symbol,
                model_name=cached.model_name,
                model_version=cached.model_version,
                prediction_type=cached.prediction_type,
                timeframe=cached.timeframe,
                predicted_value=cached.predicted_value,
                confidence_score=cached.confidence_score,
                reasoning=cached.metadata.get("reasoning", ""),
                created_at=cached.created_at,
                valid_until=cached.valid_until,
                metadata=cached.metadata
            )
        
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
        
        prediction_create = PredictionCreate(
            coin_id=coin.id,
            model_name=model_info["model"],
            model_version=model_info["version"],
            prediction_type=prediction_type,
            timeframe=timeframe,
            predicted_value=result.predicted_value,
            confidence_score=result.confidence_score,
            input_data_hash=input_hash,
            valid_until=datetime.utcnow() + timedelta(hours=24),
            metadata={
                **result.metadata,
                "reasoning": result.reasoning
            }
        )
        
        saved_prediction = await self.prediction_repo.create(prediction_create)
        
        return PredictionResponse(
            id=saved_prediction.id,
            coin_id=saved_prediction.coin_id,
            coin_symbol=coin_symbol,
            model_name=saved_prediction.model_name,
            model_version=saved_prediction.model_version,
            prediction_type=saved_prediction.prediction_type,
            timeframe=saved_prediction.timeframe,
            predicted_value=saved_prediction.predicted_value,
            confidence_score=saved_prediction.confidence_score,
            reasoning=result.reasoning,
            created_at=saved_prediction.created_at,
            valid_until=saved_prediction.valid_until,
            metadata=saved_prediction.metadata
        )
    
    async def _get_model_config(self, provider: str) -> dict:
        config = {
            "provider": provider,
            "model_identifier": "",
            "api_key": ""
        }
        
        if provider == "openai":
            config["model_identifier"] = "gpt-4-turbo-preview"
            config["api_key"] = settings.OPENAI_API_KEY
        elif provider == "anthropic":
            config["model_identifier"] = "claude-3-sonnet-20240229"
            config["api_key"] = settings.ANTHROPIC_API_KEY
        elif provider == "gemini":
            config["model_identifier"] = "gemini-pro"
            config["api_key"] = settings.GOOGLE_API_KEY
        else:
            raise ModelNotFoundError(f"Unknown provider: {provider}")
        
        return config
