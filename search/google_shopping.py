"""
Google Shopping searcher
Finds product prices across all Azerbaijani and global e-commerce sites
This is the most universal fallback that works for any product.
"""

import aiohttp
from bs4 import BeautifulSoup
from typing import Optional
from .base import BaseSearcher, SearchResult
import urllib.parse


class GoogleShoppingSearcher(BaseSearcher):
    marketplace_name = "Google Shopping"
    marketplace_emoji = "🔍"
    is_local = False

    async def search(self, query: str, barcode: Optional[str] = None) -> list[SearchResult]:
        results = []
        search_query = barcode if barcode else query

        try:
            async with aiohttp.ClientSession() as session:
                # Search Google Shopping for Azerbaijan
                encoded = urllib.parse.quote_plus(search_query)
                search_url = f"https://www.google.com/search?q={encoded}&tbm=shop&tbs=mr:1,local_avail:1&hl=az"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "az-AZ,az;q=0.9,en;q=0.8",
                }

                async with session.get(search_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        results.append(self._make_result(
                            title=f"\"{search_query}\" üçün Google Shopping-də axtarış",
                            price="—",
                            currency="AZN",
                            url=f"https://www.google.com/search?q={encoded}&tbm=shop",
                        ))
                        return results
                    html = await resp.text()

                soup = BeautifulSoup(html, "lxml")

                # Google Shopping product cards
                products = soup.select(".sh-dgr__content, .sh-dgr__grid-result, [class*='sh-dgr'], .P8xhZc")
                for prod in products[:10]:
                    try:
                        title_el = prod.select_one(".sh-nk__er-sh-nk__eq, [class*='title'], h3, .tAxDex")
                        price_el = prod.select_one(".sh-nk__price, [class*='price'], .a8Pemb")
                        link_el = prod.select_one("a[href]")
                        rating_el = prod.select_one("[class*='rating'], .Rsc7Yb")

                        title = title_el.get_text(strip=True) if title_el else None
                        if not title:
                            continue

                        price = price_el.get_text(strip=True) if price_el else "—"
                        link = link_el["href"] if link_el and link_el.get("href") else ""
                        if link and not link.startswith("http"):
                            link = f"https://www.google.com{link}"

                        rating = None
                        if rating_el:
                            try:
                                rating = float(''.join(c for c in rating_el.get_text() if c.isdigit() or c == '.')[:3])
                            except (ValueError, IndexError):
                                pass

                        results.append(self._make_result(
                            title=title,
                            price=price,
                            currency="AZN",
                            url=link or search_url,
                            rating=rating,
                        ))
                    except Exception:
                        continue

                # Fallback
                if not results:
                    results.append(self._make_result(
                        title=f"\"{search_query}\" üçün Google Shopping-də axtarış",
                        price="—",
                        currency="AZN",
                        url=f"https://www.google.com/search?q={encoded}&tbm=shop",
                    ))

        except Exception as e:
            print(f"[Google Shopping] Error: {e}")

        return results

    async def search_by_barcode(self, barcode: str) -> list[SearchResult]:
        return await self.search(barcode)
