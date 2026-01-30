from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.providers.base_provider import BaseNewsProvider


class ProviderRegistry:
    def __init__(self):
        self._providers: List["BaseNewsProvider"] = []
    
    def register(self, provider: "BaseNewsProvider") -> None:
        if provider not in self._providers:
            self._providers.append(provider)
            print(f"[Registry] Registered: {provider.name}")
    
    def unregister(self, provider: "BaseNewsProvider") -> None:
        if provider in self._providers:
            self._providers.remove(provider)
            print(f"[Registry] Unregistered: {provider.name}")
    
    def get_all(self) -> List["BaseNewsProvider"]:
        return self._providers.copy()
    
    def count(self) -> int:
        return len(self._providers)
    
    def __repr__(self) -> str:
        return f"<ProviderRegistry(providers={len(self._providers)})>"
