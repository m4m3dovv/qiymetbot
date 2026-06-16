"""
Walmart.com searcher
"""

import aiohttp
from bs4 import BeautifulSoup
from typing import Optional
from .base import BaseSearcher, SearchResult
import urllib.parse


class WalmartSearcher(BaseSearcher):
    marketplace_name = "Walmart"
    marketplace_emoji = "🏪"
    is_local = False

    async def search(self, query: str, barcode: Optional[str] = None) -> list[SearchResult]:
        results = []
        search_query = barcode if barcode else query
        try:
            encoded = urllib.parse.quote_plus(search_query)
            search_url = f"https://www.walmart.com/search?q={encoded}"
            results.append(self._make_result(
                title=f"\"{search_query}\" — Walmart",
                price="—", currency="USD", url=search_url,
            ))
        except Exception as e:
            print(f"[Walmart] Error: {e}")
        return results

    async def search_by_barcode(self, barcode: str) -> list[SearchResult]:
        return await self.search(barcode)
