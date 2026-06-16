"""
OBA Market searcher
OBA is #4 shopping app in Azerbaijan - major supermarket chain
"""

import aiohttp
from bs4 import BeautifulSoup
from typing import Optional
from .base import BaseSearcher, SearchResult
import urllib.parse


class OBASearcher(BaseSearcher):
    marketplace_name = "OBA Market"
    marketplace_emoji = "🛒"
    is_local = True

    async def search(self, query: str, barcode: Optional[str] = None) -> list[SearchResult]:
        results = []
        search_query = barcode if barcode else query

        try:
            async with aiohttp.ClientSession() as session:
                encoded = urllib.parse.quote_plus(search_query)
                # OBA Market website
                search_url = f"https://obamarket.az/az/search?q={encoded}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept-Language": "az-AZ,az;q=0.9,en;q=0.8",
                }

                async with session.get(search_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, "lxml")

                        # Try various CSS selectors
                        products = soup.select(".product-item, .product-card, [class*='product'], .item-card")
                        for prod in products[:10]:
                            try:
                                title_el = prod.select_one("[class*='title'], [class*='name'], h3, h2, a[title]")
                                price_el = prod.select_one("[class*='price'], .price")
                                link_el = prod.select_one("a[href]")
                                img_el = prod.select_one("img")

                                title = title_el.get_text(strip=True) if title_el else None
                                if not title:
                                    continue

                                price = price_el.get_text(strip=True) if price_el else "—"
                                link = link_el["href"] if link_el and link_el.get("href") else ""
                                if link and not link.startswith("http"):
                                    link = f"https://obamarket.az{link}"
                                img = img_el["src"] if img_el and img_el.get("src") else None

                                results.append(self._make_result(
                                    title=title,
                                    price=price,
                                    currency="AZN",
                                    url=link or search_url,
                                    image_url=img,
                                ))
                            except Exception:
                                continue

                # Fallback link
                if not results:
                    results.append(self._make_result(
                        title=f"\"{search_query}\" üçün OBA Market-də axtarış",
                        price="—",
                        currency="AZN",
                        url=f"https://obamarket.az/az/search?q={encoded}",
                    ))

        except Exception as e:
            print(f"[OBA] Error: {e}")

        return results

    async def search_by_barcode(self, barcode: str) -> list[SearchResult]:
        return await self.search(barcode)
