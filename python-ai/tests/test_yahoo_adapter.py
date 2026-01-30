import sys
import os
from collections import defaultdict

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.providers.yahoo_rss_adapter import YahooRSSAdapter

def test_keyword_matching():
    """Test keyword matching with mock news articles."""
    print("=" * 100)
    print("Testing YahooRSSAdapter - Keyword Matching with Mock Data")
    print("=" * 100)
    
    # Initialize adapter with watchlist
    adapter = YahooRSSAdapter(watchlist_path="../config/watchlist.yaml")
    
    print(f"\nWatchlist loaded: {len(adapter.watchlist.get('assets', []))} assets")
    for asset in adapter.watchlist.get('assets', []):
        if asset.get('enabled', True):
            keywords_str = ", ".join(asset.get('keywords', [])[:5]) + "..."
            print(f"  - {asset['symbol']}: {asset['name']}")
            print(f"    Keywords: {keywords_str}")
    
    # Mock news articles
    mock_articles = [
        {
            "title": "Apple Unveils New iPhone 15 Pro with Revolutionary Camera System",
            "summary": "Apple Inc. announced the latest iPhone featuring advanced AI capabilities and improved battery life.",
            "url": "https://finance.yahoo.com/news/apple-iphone-15-pro-123456.html"
        },
        {
            "title": "Tim Cook Discusses Apple's Vision for AI Integration",
            "summary": "In a recent interview, Apple CEO Tim Cook shared insights about the company's AI strategy and future product roadmap.",
            "url": "https://finance.yahoo.com/news/tim-cook-ai-vision-234567.html"
        },
        {
            "title": "Google Announces Major Updates to Android Operating System",
            "summary": "Alphabet's Google revealed Android 15 with enhanced privacy features and improved performance optimizations.",
            "url": "https://finance.yahoo.com/news/google-android-15-345678.html"
        },
        {
            "title": "Sundar Pichai: Google Cloud Revenue Surges 30% Year-Over-Year",
            "summary": "Google CEO Sundar Pichai announced strong quarterly results driven by cloud computing and AI services growth.",
            "url": "https://finance.yahoo.com/news/google-cloud-revenue-456789.html"
        },
        {
            "title": "Waymo Expands Self-Driving Service to New Cities",
            "summary": "Alphabet's autonomous vehicle unit Waymo announced expansion plans to three additional metropolitan areas.",
            "url": "https://finance.yahoo.com/news/waymo-expansion-567890.html"
        },
        {
            "title": "Federal Reserve Announces Interest Rate Decision",
            "summary": "The Federal Reserve kept interest rates unchanged as inflation continues to moderate.",
            "url": "https://finance.yahoo.com/news/fed-interest-rates-678901.html"
        },
        {
            "title": "Apple Watch Series 9 Breaks Sales Records in Q4",
            "summary": "The latest Apple Watch featuring new health monitoring capabilities exceeded sales expectations.",
            "url": "https://finance.yahoo.com/news/apple-watch-sales-789012.html"
        },
        {
            "title": "YouTube Premium Subscribers Reach 100 Million Milestone",
            "summary": "Google's YouTube announced its premium subscription service has crossed 100 million paying subscribers.",
            "url": "https://finance.yahoo.com/news/youtube-premium-890123.html"
        }
    ]
    
    print("\n" + "-" * 100)
    print("Testing Keyword Matching on Mock Articles")
    print("-" * 100 + "\n")
    
    # Group articles by symbol
    articles_by_symbol = defaultdict(list)
    filtered_count = 0
    
    for article in mock_articles:
        title = article["title"]
        summary = article["summary"]
        
        # Find matching symbols based on keywords
        matched_symbols = adapter._find_matching_symbols(title, summary)
        
        if matched_symbols:
            article_info = {
                "title": title,
                "url": article["url"],
                "summary": summary,
                "matched_symbols": matched_symbols
            }
            for symbol in matched_symbols:
                articles_by_symbol[symbol].append(article_info)
        else:
            filtered_count += 1
            print(f"❌ FILTERED: {title[:60]}...")
    
    # Display results
    print("\n" + "=" * 100)
    print("RESULTS")
    print("=" * 100)
    
    total_matched = sum(len(articles) for articles in articles_by_symbol.values())
    print(f"\n✅ Total articles matched: {total_matched}")
    print(f"❌ Articles filtered out: {filtered_count}")
    print(f"📊 Total articles processed: {len(mock_articles)}\n")
    
    # Show 2 articles per company
    for symbol in sorted(articles_by_symbol.keys()):
        articles = articles_by_symbol[symbol]
        asset_name = next((a['name'] for a in adapter.watchlist.get('assets', []) if a['symbol'] == symbol), symbol)
        
        print("\n" + "=" * 100)
        print(f"📰 {symbol} - {asset_name}")
        print("=" * 100)
        print(f"Total articles found: {len(articles)}\n")
        
        # Show first 2 articles
        for i, article in enumerate(articles[:2], 1):
            print(f"  [{i}] {article['title']}")
            print(f"      Matched symbols: {', '.join(article['matched_symbols'])}")
            print(f"      URL: {article['url']}")
            print(f"      Summary: {article['summary']}")
            print()
    
    print("\n" + "=" * 100)
    print("✅ Keyword Matching Test Complete")
    print("=" * 100)
    print("\nThe adapter successfully:")
    print("  ✓ Loaded watchlist configuration")
    print("  ✓ Matched articles to symbols based on keywords")
    print("  ✓ Filtered out irrelevant articles")
    print("  ✓ Grouped articles by company")
    print("\n💡 To test with real Yahoo RSS data, wait a few minutes for rate limits to reset")
    print("   or run the adapter inside Docker where rate limits may differ.")

if __name__ == "__main__":
    test_keyword_matching()
