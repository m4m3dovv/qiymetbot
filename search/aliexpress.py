"""
AliExpress searcher
"""

import aiohttp
from bs4 import BeautifulSoup
import json
from typing import Optional
from .base import BaseSearcher, SearchResult
import urllib.parse


class AliExpressSearcher(BaseSearcher):
    marketplace_name = "AliExpress"
    marketplace_emoji = "🚢"
    is_local = False

    async def search(self, query: str, barcode: Optional[str] = None) -> list[SearchResult]:
        results = []
        search_query = barcode if barcode else query
        try:
            async with aiohttp.ClientSession() as session:
                encoded = urllib.parse.quote_plus(search_query)
                search_url = f"https://www.aliexpress.com/w/wholesale-{encoded}.html"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                async with session.get(search_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        results.append(self._make_result(
                            title=f"\"{search_query}\" — AliExpress",
                            price="—", currency="USD", url=search_url,
                        ))
                        return results
                    html = await resp.text()

                soup = BeautifulSoup(html, "lxml")
                scripts = soup.find_all("script", {"type": "application/ld+json"})
                for script in scripts[:5]:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and data.get("@type") == "Product":
                            offers = data.get("offers", {})
                            price = offers.get("price", "—")
                            results.append(self._make_result(
                                title=data.get("name", "AliExpress Məhsul"),
                                price=str(price), currency="USD",
                                url=offers.get("url", search_url),
                            ))
                    except (json.JSONDecodeError, AttributeError):
                        continue

                if not results:
                    results.append(self._make_result(
                        title=f"\"{search_query}\" — AliExpress",
                        price="—", currency="USD", url=search_url,
                    ))
        except Exception as e:
            print(f"[AliExpress] Error: {e}")
        return results

    async def search_by_barcode(self, barcode: str) -> list[SearchResult]:
        return await self.search(barcode)
