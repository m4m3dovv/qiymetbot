"""
Temu.com searcher
Uses web scraping to find product prices on Temu
"""

import aiohttp
from bs4 import BeautifulSoup
import json
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
            async with aiohttp.ClientSession() as session:
                encoded = urllib.parse.quote_plus(search_query)
                search_url = f"https://www.temu.com/search_result.html?search_key={encoded}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                async with session.get(search_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        return results
                    html = await resp.text()

                soup = BeautifulSoup(html, "lxml")

                # Try JSON-LD first
                scripts = soup.find_all("script", {"type": "application/ld+json"})
                for script in scripts[:5]:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and data.get("@type") == "Product":
                            offers = data.get("offers", {})
                            price = offers.get("price", "N/A")
                            results.append(self._make_result(
                                title=data.get("name", "Temu Məhsul"),
                                price=str(price),
                                currency="USD",
                                url=offers.get("url", search_url),
                            ))
                    except (json.JSONDecodeError, AttributeError):
                        continue

                # Fallback HTML parsing
                if not results:
                    products = soup.select("[class*='product'], [class*='goods'], [class*='item']")
                    for prod in products[:8]:
                        try:
                            title_el = prod.select_one("[class*='title'], [class*='name'], h3")
                            price_el = prod.select_one("[class*='price']")
                            link_el = prod.select_one("a[href]")

                            title = title_el.get_text(strip=True) if title_el else None
                            if not title:
                                continue

                            price = price_el.get_text(strip=True) if price_el else "N/A"
                            link = link_el["href"] if link_el and link_el.get("href") else ""

                            results.append(self._make_result(
                                title=title,
                                price=price,
                                currency="USD",
                                url=link or search_url,
                            ))
                        except Exception:
                            continue

        except Exception as e:
            print(f"[Temu] Error: {e}")

        return results

    async def search_by_barcode(self, barcode: str) -> list[SearchResult]:
        return await self.search(barcode)
