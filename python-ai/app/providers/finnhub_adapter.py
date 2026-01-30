import os
import json
import logging
from datetime import datetime
import httpx
import redis
from .base_provider import BaseNewsProvider
from app.core.models import NewsArticle


class FinnhubAdapter(BaseNewsProvider):
    def __init__(self, api_key: str = None, redis_client: redis.Redis = None):
        super().__init__("finnhub")
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")
        self.base_url = "https://finnhub.io/api/v1"
        self.redis_client = redis_client or redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            decode_responses=True
        )
        self.queue_name = "news_ingest_queue"
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def fetch(self) -> int:
        if not self.api_key:
            self.logger.warning(f"[{self.name}] API key not configured")
            return 0
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/news",
                    params={"category": "general", "token": self.api_key}
                )
                response.raise_for_status()
                data = response.json()
            
            pushed_count = 0
            for item in data:
                article = NewsArticle(
                    provider=self.name,
                    title=item.get("headline", ""),
                    url=item.get("url", ""),
                    published_at=datetime.fromtimestamp(item.get("datetime", 0)),
                    summary=item.get("summary"),
                    symbols=item.get("related", "").split(",") if item.get("related") else [],
                    source=item.get("source")
                )
                
                article_json = article.model_dump_json()
                self.redis_client.rpush(self.queue_name, article_json)
                pushed_count += 1
            
            self.logger.info(f"[{self.name}] Pushed {pushed_count} articles to Redis queue")
            return pushed_count
        
        except httpx.HTTPStatusError as e:
            self.logger.error(f"[{self.name}] HTTP error: {e.response.status_code}")
            return 0
        except Exception as e:
            self.logger.error(f"[{self.name}] Error: {e}")
            return 0
