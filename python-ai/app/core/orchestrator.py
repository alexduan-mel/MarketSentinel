import asyncio
import logging
from typing import Dict, List
from datetime import datetime
from .registry import ProviderRegistry
from .config_loader import load_adapters_config, load_watchlist_config


class NewsOrchestrator:
    def __init__(self, config_path: str = "config/adapters.yaml", watchlist_path: str = "config/watchlist.yaml"):
        self.config = load_adapters_config(config_path)
        self.watchlist_path = watchlist_path
        self.watchlist_config = load_watchlist_config(watchlist_path)
        self.registry = ProviderRegistry()
        self.provider_intervals: Dict[str, int] = {}
        self._running = False
        self.logger = logging.getLogger(self.__class__.__name__)
        self._initialize_providers()
        self._log_startup_info()
    
    def _initialize_providers(self):
        """Initialize providers based on adapters.yaml configuration."""
        from app.providers import YahooRSSAdapter, FinnhubAdapter
        
        adapters_config = self.config.get("adapters", {})
        
        # Initialize YahooRSSAdapter
        yahoo_config = adapters_config.get("yahoo_rss", {})
        if yahoo_config.get("enabled", False):
            yahoo_adapter = YahooRSSAdapter(watchlist_path=self.watchlist_path)
            self.registry.register(yahoo_adapter)
            self.provider_intervals["yahoo_rss"] = yahoo_config.get("interval_seconds", 300)
            self.logger.info(f"Initialized YahooRSSAdapter (interval: {self.provider_intervals['yahoo_rss']}s)")
        
        # Initialize FinnhubAdapter
        finnhub_config = adapters_config.get("finnhub", {})
        if finnhub_config.get("enabled", False):
            api_key_env = finnhub_config.get("api_key_env", "FINNHUB_KEY")
            finnhub_adapter = FinnhubAdapter(api_key=None)  # Will use env var
            self.registry.register(finnhub_adapter)
            self.provider_intervals["finnhub"] = finnhub_config.get("interval_seconds", 15)
            self.logger.info(f"Initialized FinnhubAdapter (interval: {self.provider_intervals['finnhub']}s)")
    
    def _log_startup_info(self):
        """Log startup information about watched symbols and enabled adapters."""
        # Get enabled symbols from watchlist
        symbols = []
        for asset in self.watchlist_config.get("assets", []):
            if asset.get("enabled", True):
                symbols.append(asset.get("symbol", "UNKNOWN"))
        
        # Get enabled adapters
        enabled_adapters = list(self.provider_intervals.keys())
        
        symbols_str = ", ".join(symbols) if symbols else "None"
        adapters_str = ", ".join(enabled_adapters) if enabled_adapters else "None"
        
        self.logger.info(f"Sentinel-Python: Watching [{symbols_str}] with [{adapters_str}]")
    
    async def fetch_all(self) -> int:
        providers = self.registry.get_all()
        if not providers:
            self.logger.warning("[Orchestrator] No providers registered")
            return 0
        
        tasks = [provider.fetch() for provider in providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_pushed = 0
        for provider, result in zip(providers, results):
            if isinstance(result, Exception):
                self.logger.error(f"[Orchestrator] Error from {provider.name}: {result}")
            else:
                total_pushed += result
                self.logger.info(f"[Orchestrator] {provider.name} pushed {result} articles to queue")
        
        return total_pushed
    
    async def start(self):
        self._running = True
        self.logger.info(f"[Orchestrator] Started with {self.registry.count()} providers")
        
        # Track last fetch time for each provider
        last_fetch = {name: 0 for name in self.provider_intervals.keys()}
        
        while self._running:
            try:
                current_time = asyncio.get_event_loop().time()
                
                # Check which providers need to fetch based on their intervals
                providers_to_fetch = []
                for provider in self.registry.get_all():
                    interval = self.provider_intervals.get(provider.name, 300)
                    if current_time - last_fetch.get(provider.name, 0) >= interval:
                        providers_to_fetch.append(provider)
                        last_fetch[provider.name] = current_time
                
                if providers_to_fetch:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.logger.info(f"\n[Orchestrator] Fetch cycle started at {timestamp}")
                    
                    tasks = [provider.fetch() for provider in providers_to_fetch]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    total_pushed = 0
                    for provider, result in zip(providers_to_fetch, results):
                        if isinstance(result, Exception):
                            self.logger.error(f"[Orchestrator] Error from {provider.name}: {result}")
                        else:
                            total_pushed += result
                            self.logger.info(f"[Orchestrator] {provider.name} pushed {result} articles to queue")
                    
                    self.logger.info(f"[Orchestrator] Total articles pushed to queue: {total_pushed}")
                
                # Sleep for a short time before checking again
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"[Orchestrator] Unexpected error: {e}")
                await asyncio.sleep(60)
    
    def stop(self):
        self._running = False
        self.logger.info("[Orchestrator] Stopped")
