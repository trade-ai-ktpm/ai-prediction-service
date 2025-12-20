from sqlalchemy.ext.asyncio import AsyncSession
from src.storage import get_db
from src.core.pipeline import PredictionPipeline


async def get_prediction_pipeline(
    db: AsyncSession = get_db()
) -> PredictionPipeline:
    return PredictionPipeline(db)
