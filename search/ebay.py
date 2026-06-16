"""
eBay.com searcher
"""

import aiohttp
from bs4 import BeautifulSoup
from typing import Optional
from .base import BaseSearcher, SearchResult
import urllib.parse


class EbaySearcher(BaseSearcher):
    marketplace_name = "eBay"
    marketplace_emoji = "🏷️"
    is_local = False

    async def search(self, query: str, barcode: Optional[str] = None) -> list[SearchResult]:
        results = []
        search_query = barcode if barcode else query
        try:
            async with aiohttp.ClientSession() as session:
                encoded = urllib.parse.quote_plus(search_query)
                search_url = f"https://www.ebay.com/sch/i.html?_nkw={encoded}&_sacat=0"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                async with session.get(search_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        results.append(self._make_result(
                            title=f"\"{search_query}\" — eBay",
                            price="—", currency="USD", url=search_url,
                        ))
                        return results
                    html = await resp.text()

                soup = BeautifulSoup(html, "lxml")
                products = soup.select(".s-item")
                for prod in products[:8]:
                    try:
                        title_el = prod.select_one(".s-item__title")
                        price_el = prod.select_one(".s-item__price")
                        link_el = prod.select_one(".s-item__link")
                        img_el = prod.select_one(".s-item__image-img")

                        title = title_el.get_text(strip=True) if title_el else None
                        if not title or "Shop on eBay" in title:
                            continue
                        price = price_el.get_text(strip=True) if price_el else "—"
                        link = link_el["href"] if link_el and link_el.get("href") else ""
                        img = img_el["src"] if img_el and img_el.get("src") else None

                        results.append(self._make_result(
                            title=title, price=price, currency="USD",
                            url=link or search_url, image_url=img, in_stock=True,
                        ))
                    except Exception:
                        continue

                if not results:
                    results.append(self._make_result(
                        title=f"\"{search_query}\" — eBay",
                        price="—", currency="USD", url=search_url,
                    ))
        except Exception as e:
            print(f"[eBay] Error: {e}")
        return results

    async def search_by_barcode(self, barcode: str) -> list[SearchResult]:
        return await self.search(barcode)
