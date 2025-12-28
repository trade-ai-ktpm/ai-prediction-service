from src.celery_app import celery_app
from src.storage import get_db_session, cache_manager
from src.core.pipeline import PredictionPipeline
from src.config import get_logger, settings
import asyncio

logger = get_logger(__name__)

TOP_COINS = ['BTC', 'ETH', 'SOL', 'BNB', 'ADA', 'XRP', 'DOT', 'DOGE', 'MATIC', 'AVAX']
TIMEFRAMES = ['1h', '4h', '1d']


@celery_app.task(name="src.tasks.precompute_task.precompute_top_coins")
def precompute_top_coins():
    logger.info("Starting pre-computation for top coins...")
    
    results = asyncio.run(_precompute_all())
    
    logger.info(f"Pre-computation completed: {results['success']}/{results['total']} predictions")
    return results


async def _precompute_all():
    total = 0
    success = 0
    
    async with get_db_session() as db:
        pipeline = PredictionPipeline(db)
        
        for coin in TOP_COINS:
            for timeframe in TIMEFRAMES:
                total += 1
                try:
                    result = await pipeline.execute_prediction(
                        coin_symbol=coin,
                        timeframe=timeframe,
                        prediction_type="price",
                        model_name=settings.DEFAULT_MODEL_PROVIDER
                    )
                    
                    cache_key = f"pred:latest:{coin}:{timeframe}"
                    await cache_manager.set(
                        cache_key,
                        result.dict(),
                        ttl=1200
                    )
                    
                    success += 1
                    logger.info(f"Pre-computed {coin} {timeframe}")
                    
                except Exception as e:
                    logger.error(f"Failed to pre-compute {coin} {timeframe}: {str(e)}")
    
    return {"total": total, "success": success, "failed": total - success}
