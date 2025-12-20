from abc import ABC, abstractmethod
from typing import List, Dict, Any


class DataProcessorInterface(ABC):
    @abstractmethod
    async def process(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def validate(self, data: List[Dict[str, Any]]) -> bool:
        pass
