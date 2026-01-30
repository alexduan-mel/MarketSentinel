import os
import json
import logging
from typing import List, Dict
from datetime import datetime
import httpx
import feedparser
import redis
import yaml
from .base_provider import BaseNewsProvider
from app.core.models import NewsArticle


class YahooRSSAdapter(BaseNewsProvider):
    def __init__(self, redis_client: redis.Redis = None, watchlist_path: str = None):
        super().__init__("yahoo_rss")
        self.feed_url = "https://finance.yahoo.com/news/rss"
        self.redis_client = redis_client or redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            decode_responses=True
        )
        self.queue_name = "news_ingest_queue"
        self.logger = logging.getLogger(self.__class__.__name__)
        self.watchlist = self._load_watchlist(watchlist_path or "config/watchlist.yaml")
    
    def _load_watchlist(self, path: str) -> Dict:
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"Could not load watchlist from {path}: {e}")
            return {"assets": []}
    
    def _clean_yahoo_url(self, url: str) -> str:
        if "*" in url:
            parts = url.split("*")
            return parts[-1] if len(parts) > 1 else url
        return url
    
    def _match_keywords(self, text: str, keywords: List[str]) -> bool:
        if not text or not keywords:
            return False
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    def _find_matching_symbols(self, title: str, summary: str) -> List[str]:
        matched_symbols = []
        for asset in self.watchlist.get("assets", []):
            if not asset.get("enabled", True):
                continue
            
            keywords = asset.get("keywords", [])
            if self._match_keywords(title, keywords) or self._match_keywords(summary, keywords):
                matched_symbols.append(asset["symbol"])
        
        return matched_symbols
    
    async def fetch(self) -> int:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.feed_url)
                response.raise_for_status()
                feed_content = response.text
            
            feed = feedparser.parse(feed_content)
            
            pushed_count = 0
            filtered_count = 0
            
            for entry in feed.entries:
                published_at = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                
                raw_url = entry.get("link", "")
                cleaned_url = self._clean_yahoo_url(raw_url)
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                
                # Find matching symbols based on keywords
                matched_symbols = self._find_matching_symbols(title, summary)
                
                # Only push articles that match at least one watchlist asset
                if matched_symbols:
                    article = NewsArticle(
                        provider=self.name,
                        title=title,
                        url=cleaned_url,
                        published_at=published_at,
                        summary=summary,
                        symbols=matched_symbols,
                        source="Yahoo Finance"
                    )
                    
                    article_json = article.model_dump_json()
                    self.redis_client.rpush(self.queue_name, article_json)
                    pushed_count += 1
                else:
                    filtered_count += 1
            
            self.logger.info(f"[{self.name}] Pushed {pushed_count} articles, filtered {filtered_count} irrelevant articles")
            return pushed_count
        
        except httpx.HTTPStatusError as e:
            self.logger.error(f"[{self.name}] HTTP error: {e.response.status_code}")
            return 0
        except Exception as e:
            self.logger.error(f"[{self.name}] Error: {e}")
            return 0
