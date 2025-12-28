from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession
from src.celery_app import celery_app
from src.storage import get_db_session
from src.core.pipeline import PredictionPipeline
from src.data.repositories import PredictionRepository
from src.config import get_logger
import asyncio

logger = get_logger(__name__)


@celery_app.task(bind=True, name="src.tasks.prediction_task.create_prediction")
def create_prediction_task(
    self: Task,
    prediction_id: int,
    coin_symbol: str,
    timeframe: str,
    prediction_type: str = "price",
    model_name: str = None
):
    try:
        self.update_state(
            state='PROCESSING',
            meta={'progress': 20, 'message': f'Loading {coin_symbol} data...'}
        )
        
        result = asyncio.run(_execute_prediction(
            self,
            prediction_id,
            coin_symbol,
            timeframe,
            prediction_type,
            model_name
        ))
        
        return {
            "status": "COMPLETED",
            "prediction_id": prediction_id,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Prediction task failed: {str(e)}")
        asyncio.run(_mark_prediction_failed(prediction_id, str(e)))
        raise


async def _execute_prediction(
    task: Task,
    prediction_id: int,
    coin_symbol: str,
    timeframe: str,
    prediction_type: str,
    model_name: str
):
    async with get_db_session() as db:
        pipeline = PredictionPipeline(db)
        pred_repo = PredictionRepository(db)
        
        await pred_repo.update_status(prediction_id, "PROCESSING")
        
        task.update_state(
            state='PROCESSING',
            meta={'progress': 40, 'message': 'Fetching candle data...'}
        )
        
        task.update_state(
            state='AI_THINKING',
            meta={'progress': 60, 'message': 'AI analyzing patterns...'}
        )
        
        result = await pipeline.execute_prediction(
            coin_symbol=coin_symbol,
            timeframe=timeframe,
            prediction_type=prediction_type,
            model_name=model_name
        )
        
        task.update_state(
            state='FINALIZING',
            meta={'progress': 90, 'message': 'Saving results...'}
        )
        
        await pred_repo.update_prediction_result(
            prediction_id=prediction_id,
            predicted_value=result.predicted_value,
            confidence_score=result.confidence_score,
            model_name=result.model_name,
            model_version=result.model_version,
            metadata=result.metadata,
            status="COMPLETED"
        )
        
        return result


async def _mark_prediction_failed(prediction_id: int, error_message: str):
    async with get_db_session() as db:
        pred_repo = PredictionRepository(db)
        await pred_repo.update_status(
            prediction_id,
            "FAILED",
            error_message=error_message
        )
