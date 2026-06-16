"""
Search manager that orchestrates searches across all marketplaces.
Runs all searches concurrently for maximum speed.
"""

import asyncio
from typing import Optional
from .base import BaseSearcher, SearchResult

# Import all searchers
from .araz import ArazSearcher
from .bravo import BravoSearcher
from .bazarstore import BazarStoreSearcher
from .sait import SaitSearcher
from .bolmart import BolMartSearcher
from .amazon import AmazonSearcher
from .ebay import EbaySearcher
from .aliexpress import AliExpressSearcher
from .temu import TemuSearcher
from .walmart import WalmartSearcher


LOCAL_SEARCHERS = [
    ArazSearcher,
    BravoSearcher,
    BazarStoreSearcher,
    SaitSearcher,
    BolMartSearcher,
]

GLOBAL_SEARCHERS = [
    AmazonSearcher,
    EbaySearcher,
    AliExpressSearcher,
    TemuSearcher,
    WalmartSearcher,
]


class SearchManager:
    """Manages all marketplace searchers and runs searches concurrently."""

    def __init__(self):
        self.local_searchers: list[BaseSearcher] = [cls() for cls in LOCAL_SEARCHERS]
        self.global_searchers: list[BaseSearcher] = [cls() for cls in GLOBAL_SEARCHERS]
        self.all_searchers: list[BaseSearcher] = self.local_searchers + self.global_searchers

    async def search_all(
        self,
        query: str,
        barcode: Optional[str] = None,
        include_local: bool = True,
        include_global: bool = True,
    ) -> list[SearchResult]:
        """Search all enabled marketplaces concurrently."""

        searchers = []
        if include_local:
            searchers.extend(self.local_searchers)
        if include_global:
            searchers.extend(self.global_searchers)

        if not searchers:
            return []

        tasks = [self._safe_search(searcher, query, barcode) for searcher in searchers]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        all_results = []
        for result in results_list:
            if isinstance(result, Exception):
                print(f"[Search Error] {result}")
                continue
            if isinstance(result, list):
                all_results.extend(result)

        # Sort: local results first, then by price (if parseable)
        all_results.sort(key=lambda r: (0 if r.is_local else 1, r.marketplace))
        return all_results

    async def search_local(self, query: str, barcode: Optional[str] = None) -> list[SearchResult]:
        """Search only local (Azerbaijan) marketplaces."""
        return await self.search_all(query, barcode, include_local=True, include_global=False)

    async def search_global(self, query: str, barcode: Optional[str] = None) -> list[SearchResult]:
        """Search only global marketplaces."""
        return await self.search_all(query, barcode, include_local=False, include_global=True)

    async def _safe_search(
        self, searcher: BaseSearcher, query: str, barcode: Optional[str]
    ) -> list[SearchResult]:
        """Wrapper that catches exceptions in individual searchers."""
        try:
            if barcode:
                return await searcher.search_by_barcode(barcode)
            else:
                return await searcher.search(query)
        except Exception as e:
            print(f"[{searcher.marketplace_name}] Search error: {e}")
            return []
