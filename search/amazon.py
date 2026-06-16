"""
Amazon.com searcher
"""

import aiohttp
from bs4 import BeautifulSoup
from typing import Optional
from .base import BaseSearcher, SearchResult
import urllib.parse


class AmazonSearcher(BaseSearcher):
    marketplace_name = "Amazon"
    marketplace_emoji = "📦"
    is_local = False

    async def search(self, query: str, barcode: Optional[str] = None) -> list[SearchResult]:
        results = []
        search_query = barcode if barcode else query
        try:
            async with aiohttp.ClientSession() as session:
                encoded = urllib.parse.quote_plus(search_query)
                search_url = f"https://www.amazon.com/s?k={encoded}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                async with session.get(search_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        results.append(self._make_result(
                            title=f"\"{search_query}\" — Amazon",
                            price="—",
                            currency="USD",
                            url=search_url,
                        ))
                        return results
                    html = await resp.text()

                soup = BeautifulSoup(html, "lxml")
                products = soup.select("[data-component-type='s-search-result']")
                for prod in products[:8]:
                    try:
                        title_el = prod.select_one("h2 a span, .a-text-normal")
                        price_el = prod.select_one(".a-price .a-offscreen, .a-price-whole")
                        link_el = prod.select_one("h2 a, .a-link-normal")
                        img_el = prod.select_one(".s-image")
                        rating_el = prod.select_one(".a-icon-star-small span, [aria-label*='out of']")

                        title = title_el.get_text(strip=True) if title_el else None
                        if not title:
                            continue
                        price = price_el.get_text(strip=True) if price_el else "—"
                        link = link_el["href"] if link_el and link_el.get("href") else ""
                        if link and not link.startswith("http"):
                            link = f"https://www.amazon.com{link}"
                        img = img_el["src"] if img_el and img_el.get("src") else None
                        rating = None
                        if rating_el:
                            try:
                                r = rating_el.get("aria-label", rating_el.get_text())
                                rating = float(''.join(c for c in r if c.isdigit() or c == '.')[:3])
                            except (ValueError, IndexError):
                                pass

                        results.append(self._make_result(
                            title=title, price=price, currency="USD",
                            url=link or search_url, image_url=img,
                            in_stock=True, rating=rating,
                        ))
                    except Exception:
                        continue

                if not results:
                    results.append(self._make_result(
                        title=f"\"{search_query}\" — Amazon",
                        price="—", currency="USD", url=search_url,
                    ))
        except Exception as e:
            print(f"[Amazon] Error: {e}")
        return results

    async def search_by_barcode(self, barcode: str) -> list[SearchResult]:
        return await self.search(barcode)
