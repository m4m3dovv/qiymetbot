"""
Temu.com searcher
"""

import aiohttp
from typing import Optional
from .base import BaseSearcher, SearchResult
import urllib.parse


class TemuSearcher(BaseSearcher):
    marketplace_name = "Temu"
    marketplace_emoji = "🔥"
    is_local = False

    async def search(self, query: str, barcode: Optional[str] = None) -> list[SearchResult]:
        results = []
        search_query = barcode if barcode else query
        try:
            encoded = urllib.parse.quote_plus(search_query)
            search_url = f"https://www.temu.com/search_result.html?search_key={encoded}"
            # Temu is heavily JS-rendered, just provide search link
            results.append(self._make_result(
                title=f"\"{search_query}\" — Temu",
                price="—", currency="USD", url=search_url,
            ))
        except Exception as e:
            print(f"[Temu] Error: {e}")
        return results

    async def search_by_barcode(self, barcode: str) -> list[SearchResult]:
        return await self.search(barcode)
