from typing import Optional
import redis.asyncio as redis
from src.config import settings, get_logger
import json

logger = get_logger(__name__)


class CacheManager:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.enabled = settings.REDIS_URL is not None
    
    async def connect(self):
        if not self.enabled:
            logger.warning("Redis cache is disabled (no REDIS_URL configured)")
            return
        
        try:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self.enabled = False
    
    async def disconnect(self):
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis cache disconnected")
    
    async def get(self, key: str) -> Optional[dict]:
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    async def set(self, key: str, value: dict, ttl: int = None):
        if not self.enabled or not self.redis_client:
            return
        
        try:
            ttl = ttl or settings.CACHE_TTL
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(value)
            )
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
    
    async def delete(self, key: str):
        if not self.enabled or not self.redis_client:
            return
        
        try:
            await self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
    
    async def clear_pattern(self, pattern: str):
        if not self.enabled or not self.redis_client:
            return
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache clear pattern error: {str(e)}")


cache_manager = CacheManager()
