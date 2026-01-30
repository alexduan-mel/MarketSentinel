from abc import ABC, abstractmethod
from typing import List
from app.core.models import NewsArticle


class BaseNewsProvider(ABC):
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def fetch(self) -> List[NewsArticle]:
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
