import asyncio
from app.core import ProviderRegistry, NewsOrchestrator
from app.providers import FinnhubAdapter, YahooRSSAdapter


async def main():
    registry = ProviderRegistry()
    
    finnhub = FinnhubAdapter(api_key="your_finnhub_api_key_here")
    yahoo_rss = YahooRSSAdapter()
    
    registry.register(finnhub)
    registry.register(yahoo_rss)
    
    orchestrator = NewsOrchestrator(registry, interval_minutes=5)
    
    articles = await orchestrator.fetch_all()
    
    print(f"\n=== Fetched {len(articles)} articles ===")
    for article in articles[:3]:
        print(f"\n[{article.provider}] {article.title}")
        print(f"URL: {article.url}")
        print(f"Published: {article.published_at}")


if __name__ == "__main__":
    asyncio.run(main())
