"""
Araz Supermarket (araz.az) searcher
Azerbaijan's largest supermarket chain
"""

import aiohttp
from bs4 import BeautifulSoup
from typing import Optional
from .base import BaseSearcher, SearchResult


class ArazSearcher(BaseSearcher):
    marketplace_name = "Araz Supermarket"
    marketplace_emoji = "🛒"
    is_local = True

    async def search(self, query: str, barcode: Optional[str] = None) -> list[SearchResult]:
        results = []
        try:
            async with aiohttp.ClientSession() as session:
                search_url = f"https://araz.az/az/search?q={query}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept-Language": "az-AZ,az;q=0.9,en;q=0.8",
                }
                async with session.get(search_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        return results
                    html = await resp.text()

                soup = BeautifulSoup(html, "lxml")
                products = soup.select(".product-item, .product-card, .item, [class*='product']")

                for prod in products[:10]:
                    try:
                        title_el = prod.select_one("a[title], .product-name, .name, h3, h2, .title")
                        price_el = prod.select_one(".price, .product-price, [class*='price']")
                        link_el = prod.select_one("a[href]")
                        img_el = prod.select_one("img")

                        if not title_el:
                            continue

                        title = title_el.get_text(strip=True)
                        price = price_el.get_text(strip=True) if price_el else "Qiymət tapılmadı"
                        link = link_el["href"] if link_el and link_el.get("href") else ""
                        if link and not link.startswith("http"):
                            link = f"https://araz.az{link}"
                        img = img_el["src"] if img_el and img_el.get("src") else None

                        if title:
                            results.append(self._make_result(
                                title=title,
                                price=price,
                                currency="AZN",
                                url=link or search_url,
                                image_url=img,
                                in_stock=True,
                            ))
                    except Exception:
                        continue

        except Exception as e:
            print(f"[Araz] Error: {e}")

        return results

    async def search_by_barcode(self, barcode: str) -> list[SearchResult]:
        return await self.search(barcode)
