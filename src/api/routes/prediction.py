from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.prediction import PredictionRequest, PredictionResponse
from src.core.pipeline import PredictionPipeline
from src.storage import get_db, cache_manager
from src.core.exceptions import InvalidInputError, ModelNotFoundError
from src.config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["ai-predictions"])


@router.post("/", response_model=PredictionResponse)
async def create_prediction(
    request: PredictionRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        pipeline = PredictionPipeline(db)
        result = await pipeline.predict_async(
            coin_symbol=request.coin_symbol,
            timeframe=request.timeframe,
            prediction_type=request.prediction_type,
            model_name=request.model_name
        )
        return result
    except InvalidInputError as e:
        logger.error(f"Invalid input: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ModelNotFoundError as e:
        logger.error(f"Model not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{prediction_id}", response_model=PredictionResponse)
async def get_prediction(
    prediction_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get prediction by ID"""
    try:
        pipeline = PredictionPipeline(db)
        prediction = await pipeline.prediction_repo.get_by_id(prediction_id)
        
        if not prediction:
            raise HTTPException(status_code=404, detail="Prediction not found")
        
        # Get coin info
        coin = await pipeline.coin_repo.get_by_id(prediction.coin_id)
        
        # Get news sources if available
        sources = []
        if prediction.meta_data and "news_ids" in prediction.meta_data:
            news_ids = prediction.meta_data["news_ids"]
            for news_id in news_ids[:5]:  # Limit to 5 sources
                news = await pipeline.news_repo.get_by_id(news_id)
                if news:
                    sources.append({
                        "title": news.title,
                        "source": news.source,
                        "url": news.url,
                        "published_at": news.published_at.isoformat() if news.published_at else None
                    })
        
        return PredictionResponse(
            id=prediction.id,
            coin_id=prediction.coin_id,
            coin_symbol=coin.symbol if coin else "UNKNOWN",
            model_name=prediction.model_name,
            model_version=prediction.model_version,
            prediction_type=prediction.prediction_type,
            timeframe=prediction.timeframe,
            predicted_value=prediction.predicted_value,
            confidence_score=prediction.confidence_score,
            reasoning=prediction.meta_data.get("reasoning") if prediction.meta_data else None,
            status=prediction.status,
            error_message=prediction.error_message,
            created_at=prediction.created_at,
            valid_until=prediction.valid_until,
            metadata=prediction.meta_data,
            sources=sources if sources else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching prediction: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/latest/{coin_symbol}", response_model=PredictionResponse)
async def get_latest_prediction(
    coin_symbol: str,
    timeframe: str = "1h",
    db: AsyncSession = Depends(get_db)
):
    """
    Get latest pre-computed prediction for a coin.
    This endpoint returns cached predictions that are updated every 5 minutes.
    No LLM call is made - instant response.
    """
    try:
        # Try to get from cache first
        cache_key = f"pred:latest:{coin_symbol}:{timeframe}"
        cached = await cache_manager.get(cache_key)
        
        if cached:
            logger.info(f"Latest prediction cache HIT for {coin_symbol} {timeframe}")
            return PredictionResponse(**cached)
        
        # If not in cache, compute on-demand (fallback)
        logger.warning(f"Latest prediction cache MISS for {coin_symbol} {timeframe} - computing on-demand")
        pipeline = PredictionPipeline(db)
        result = await pipeline.predict_async(
            coin_symbol=coin_symbol,
            timeframe=timeframe,
            prediction_type="price",
            model_name=None
        )
        return result
        
    except Exception as e:
        logger.error(f"Error fetching latest prediction: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/models")
async def list_available_models():
    from src.models.factory import ModelFactory
    
    return {
        "available_providers": ModelFactory.get_available_providers(),
        "default_provider": "openai"
    }
