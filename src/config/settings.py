from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    DATABASE_URL: str
    
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 3600
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    
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
    MAX_NEWS: int = 50
    
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
