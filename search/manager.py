"""
Search manager that orchestrates searches across all marketplaces.
Runs all searches concurrently for maximum speed.
"""

import asyncio
from typing import Optional
from .base import BaseSearcher, SearchResult

from .wolt import WoltSearcher
from .umico import UmicoSearcher
from .trendyol import TrendyolSearcher
from .oba import OBASearcher
from .google_shopping import GoogleShoppingSearcher
from .amazon import AmazonSearcher
from .ebay import EbaySearcher
from .aliexpress import AliExpressSearcher
from .temu import TemuSearcher
from .walmart import WalmartSearcher


LOCAL_SEARCHERS = [
    WoltSearcher,       # Araz, Bravo, SPAR, Neptun + 115 supermarkets via Wolt API
    UmicoSearcher,      # #2 shopping app in AZ (500K+ products)
    TrendyolSearcher,   # #3 shopping app in AZ
    OBASearcher,        # #4 shopping app in AZ
    GoogleShoppingSearcher,  # Universal - finds prices across ALL AZ sites
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

        # Sort: local results with prices first, then without prices, then global
        def sort_key(r: SearchResult):
            has_price = 0 if r.price and r.price != "—" and r.price != "N/A" else 1
            is_local = 0 if r.is_local else 1
            return (is_local, has_price, r.marketplace)

        all_results.sort(key=sort_key)
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
