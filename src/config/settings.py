from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str
    
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 3600
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    DEFAULT_MODEL_PROVIDER: str = "openai"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    MAX_CANDLES: int = 100
    MAX_NEWS: int = 50
    
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
