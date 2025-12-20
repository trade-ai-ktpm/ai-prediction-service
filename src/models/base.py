from typing import Dict, Any
from abc import ABC
from src.core.interfaces import AIModelInterface


class BaseAIModel(AIModelInterface):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = config.get("provider", "unknown")
        self.model_identifier = config.get("model_identifier", "unknown")
        self.model_version = config.get("model_version", "1.0")
    
    def get_model_info(self) -> Dict[str, str]:
        return {
            "provider": self.provider,
            "model": self.model_identifier,
            "version": self.model_version
        }
