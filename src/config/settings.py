from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    DATABASE_URL: str
    
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 3600
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8002
    
    DEFAULT_MODEL_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini")
    
    # Model identifiers
    DEFAULT_GEMINI_MODEL: str = "gemini-2.5-flash"
    DEFAULT_OPENAI_MODEL: str = "gpt-4-turbo-preview"
    DEFAULT_ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    
    MAX_CANDLES: int = 100
    MAX_NEWS: int = int(os.getenv("MAX_NEWS", "20"))
    NEWS_DAYS: int = int(os.getenv("NEWS_DAYS", "3"))
    NEWS_CONTENT_MAX_LENGTH: int = int(os.getenv("NEWS_CONTENT_MAX_LENGTH", "500"))
    
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
