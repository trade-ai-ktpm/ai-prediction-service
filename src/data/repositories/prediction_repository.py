from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from src.data.models import Prediction
from src.schemas.prediction import PredictionCreate
from src.config import get_logger
from decimal import Decimal

logger = get_logger(__name__)


class PredictionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, prediction_data: PredictionCreate) -> Prediction:
        prediction = Prediction(**prediction_data.model_dump())
        self.db.add(prediction)
        await self.db.commit()
        await self.db.refresh(prediction)
        logger.info(f"Created prediction for coin_id: {prediction.coin_id}")
        return prediction
    
    async def get_by_id(self, prediction_id: int) -> Optional[Prediction]:
        result = await self.db.execute(
            select(Prediction).where(Prediction.id == prediction_id)
        )
        return result.scalar_one_or_none()
    
    async def get_cached_prediction(
        self,
        input_hash: str,
        valid_after: datetime
    ) -> Optional[Prediction]:
        result = await self.db.execute(
            select(Prediction)
            .where(
                and_(
                    Prediction.input_data_hash == input_hash,
                    Prediction.created_at >= valid_after,
                    Prediction.status == 'COMPLETED'
                )
            )
            .order_by(Prediction.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_latest_by_coin(
        self,
        coin_id: int,
        timeframe: str,
        prediction_type: str = "price",
        max_age_hours: int = 1
    ) -> Optional[Prediction]:
        valid_after = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        result = await self.db.execute(
            select(Prediction)
            .where(
                and_(
                    Prediction.coin_id == coin_id,
                    Prediction.timeframe == timeframe,
                    Prediction.prediction_type == prediction_type,
                    Prediction.status == 'COMPLETED',
                    Prediction.created_at >= valid_after
                )
            )
            .order_by(desc(Prediction.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def update_status(
        self,
        prediction_id: int,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        result = await self.db.execute(
            select(Prediction).where(Prediction.id == prediction_id)
        )
        prediction = result.scalar_one_or_none()
        
        if prediction:
            prediction.status = status
            if error_message:
                prediction.error_message = error_message
            await self.db.commit()
            logger.info(f"Updated prediction {prediction_id} status to {status}")
    
    async def update_prediction_result(
        self,
        prediction_id: int,
        predicted_value: Dict[str, Any],
        confidence_score: Optional[Decimal],
        model_name: str,
        model_version: Optional[str],
        metadata: Optional[Dict[str, Any]],
        status: str = "COMPLETED"
    ) -> None:
        result = await self.db.execute(
            select(Prediction).where(Prediction.id == prediction_id)
        )
        prediction = result.scalar_one_or_none()
        
        if prediction:
            prediction.predicted_value = predicted_value
            prediction.confidence_score = confidence_score
            prediction.model_name = model_name
            prediction.model_version = model_version
            prediction.meta_data = metadata
            prediction.status = status
            prediction.valid_until = datetime.utcnow() + timedelta(hours=24)
            await self.db.commit()
            logger.info(f"Updated prediction {prediction_id} with results")

