from typing import Dict, Type, Any
from src.core.interfaces import AIModelInterface
from src.models.adapters import OpenAIAdapter, AnthropicAdapter, GeminiAdapter, LocalAdapter
from src.core.exceptions import ModelNotFoundError
from src.config import get_logger

logger = get_logger(__name__)


class ModelFactory:
    _adapters: Dict[str, Type[AIModelInterface]] = {
        "openai": OpenAIAdapter,
        "anthropic": AnthropicAdapter,
        "gemini": GeminiAdapter,
        "local": LocalAdapter,
    }
    
    @classmethod
    def create_model(cls, provider: str, config: Dict[str, Any]) -> AIModelInterface:
        adapter_class = cls._adapters.get(provider.lower())
        if not adapter_class:
            raise ModelNotFoundError(f"Unknown provider: {provider}")
        
        logger.info(f"Creating model instance for provider: {provider}")
        return adapter_class(config)
    
    @classmethod
    def register_adapter(cls, provider: str, adapter_class: Type[AIModelInterface]):
        logger.info(f"Registering custom adapter for provider: {provider}")
        cls._adapters[provider.lower()] = adapter_class
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        return list(cls._adapters.keys())
