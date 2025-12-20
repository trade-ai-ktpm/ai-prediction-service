from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.prediction import PredictionRequest, PredictionResponse
from src.core.pipeline import PredictionPipeline
from src.storage import get_db
from src.core.exceptions import InvalidInputError, ModelNotFoundError
from src.config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/predictions", tags=["predictions"])


@router.post("/", response_model=PredictionResponse)
async def create_prediction(
    request: PredictionRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        pipeline = PredictionPipeline(db)
        result = await pipeline.predict(
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


@router.get("/models")
async def list_available_models():
    from src.models.factory import ModelFactory
    
    return {
        "available_providers": ModelFactory.get_available_providers(),
        "default_provider": "openai"
    }
