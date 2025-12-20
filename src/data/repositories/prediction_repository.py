from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.data.models import Prediction
from src.schemas.prediction import PredictionCreate
from src.config import get_logger

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
                    Prediction.created_at >= valid_after
                )
            )
            .order_by(Prediction.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
