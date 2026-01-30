import os
import json
import logging
import time
from datetime import datetime
import redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert
from app.db import get_session, NewsEvent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("StorageWorker")


class StorageWorker:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            decode_responses=True
        )
        self.queue_name = "news_ingest_queue"
        self.running = True
        logger.info("StorageWorker initialized")
    
    def _upsert_news_event(self, article_data: dict):
        session = get_session()
        try:
            news_event = NewsEvent(
                time=datetime.fromisoformat(article_data["published_at"].replace("Z", "+00:00")),
                symbol=article_data.get("symbols", ["MARKET"])[0] if article_data.get("symbols") else "MARKET",
                source=article_data.get("provider", "unknown"),
                headline=article_data.get("title", ""),
                url=article_data.get("url", ""),
                summary=article_data.get("summary"),
                sentiment_score=None,
                extra_data={
                    "provider": article_data.get("provider"),
                    "source": article_data.get("source"),
                    "symbols": article_data.get("symbols", [])
                }
            )
            
            stmt = insert(NewsEvent).values(
                time=news_event.time,
                symbol=news_event.symbol,
                source=news_event.source,
                headline=news_event.headline,
                url=news_event.url,
                summary=news_event.summary,
                sentiment_score=news_event.sentiment_score,
                extra_data=news_event.extra_data
            )
            
            stmt = stmt.on_conflict_do_nothing(index_elements=['url'])
            
            result = session.execute(stmt)
            session.commit()
            
            if result.rowcount > 0:
                logger.info(f"Inserted news event: {article_data.get('title', '')[:50]}...")
            else:
                logger.debug(f"Duplicate URL skipped: {article_data.get('url', '')[:50]}...")
            
        except IntegrityError as e:
            session.rollback()
            logger.warning(f"Integrity error (duplicate): {e}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting news event: {e}")
        finally:
            session.close()
    
    def run(self):
        logger.info(f"StorageWorker started, listening on queue: {self.queue_name}")
        
        while self.running:
            try:
                result = self.redis_client.blpop(self.queue_name, timeout=5)
                
                if result:
                    queue_name, article_json = result
                    article_data = json.loads(article_json)
                    
                    self._upsert_news_event(article_data)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from queue: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in worker loop: {e}")
                time.sleep(1)
    
    def stop(self):
        self.running = False
        logger.info("StorageWorker stopped")


if __name__ == "__main__":
    worker = StorageWorker()
    try:
        worker.run()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        worker.stop()
