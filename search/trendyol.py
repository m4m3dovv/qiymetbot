"""
Trendyol Azerbaijan searcher
Trendyol is #3 shopping app in Azerbaijan
Uses their public web search which returns product data
"""

import aiohttp
from bs4 import BeautifulSoup
import json
from typing import Optional
from .base import BaseSearcher, SearchResult
import urllib.parse


class TrendyolSearcher(BaseSearcher):
    marketplace_name = "Trendyol AZ"
    marketplace_emoji = "🧥"
    is_local = True

    async def search(self, query: str, barcode: Optional[str] = None) -> list[SearchResult]:
        results = []
        search_query = barcode if barcode else query

        try:
            async with aiohttp.ClientSession() as session:
                encoded = urllib.parse.quote_plus(search_query)
                search_url = f"https://www.trendyol.com/az/sr?q={encoded}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "az-AZ,az;q=0.9,en;q=0.8",
                }

                async with session.get(search_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        # Fallback: just link to search page
                        results.append(self._make_result(
                            title=f"\"{search_query}\" üçün Trendyol-da axtarış",
                            price="—",
                            currency="AZN",
                            url=search_url,
                        ))
                        return results
                    html = await resp.text()

                # Try to find product data in script tags (Trendyol uses __NEXT_DATA__)
                soup = BeautifulSoup(html, "lxml")

                next_data = soup.find("script", {"id": "__NEXT_DATA__"})
                if next_data:
                    try:
                        data = json.loads(next_data.string)
                        products = (
                            data.get("props", {})
                            .get("pageProps", {})
                            .get("products", [])
                        )
                        for prod in products[:10]:
                            try:
                                title = prod.get("name", "")
                                sale_price = prod.get("salePrice", prod.get("price", {}))
                                if isinstance(sale_price, dict):
                                    sale_price = sale_price.get("value", "N/A")
                                original_price = prod.get("originalPrice", prod.get("marketPrice", {}))
                                if isinstance(original_price, dict):
                                    original_price = original_price.get("value")

                                discount = None
                                if original_price and sale_price and isinstance(original_price, (int, float)) and isinstance(sale_price, (int, float)) and original_price > 0:
                                    disc_pct = int((1 - float(sale_price) / float(original_price)) * 100)
                                    if disc_pct > 0:
                                        discount = f"{disc_pct}%"

                                price_str = f"{float(sale_price):.2f}" if isinstance(sale_price, (int, float)) else str(sale_price)
                                url = prod.get("url", f"/az/product/-p-{prod.get('id', '')}")
                                if not url.startswith("http"):
                                    url = f"https://www.trendyol.com{url}"
                                img = prod.get("images", [None])
                                if isinstance(img, list) and img:
                                    img = img[0]
                                    if isinstance(img, dict):
                                        img = img.get("url", img.get("src"))

                                rating = prod.get("ratingScore", {}).get("averageRating") if isinstance(prod.get("ratingScore"), dict) else None

                                if title:
                                    results.append(self._make_result(
                                        title=title,
                                        price=price_str,
                                        currency="AZN",
                                        url=url,
                                        image_url=img,
                                        in_stock=prod.get("inStock", True),
                                        rating=float(rating) if rating else None,
                                        discount=discount,
                                    ))
                            except Exception:
                                continue
                    except (json.JSONDecodeError, AttributeError) as e:
                        print(f"[Trendyol] JSON parse error: {e}")

                # Fallback: direct link
                if not results:
                    results.append(self._make_result(
                        title=f"\"{search_query}\" üçün Trendyol-da axtarış",
                        price="—",
                        currency="AZN",
                        url=search_url,
                    ))

        except Exception as e:
            print(f"[Trendyol] Error: {e}")

        return results

    async def search_by_barcode(self, barcode: str) -> list[SearchResult]:
        return await self.search(barcode)
