"""
Umico / Birmarket searcher
Umico is the #2 shopping app in Azerbaijan with 500K+ products
Uses their internal search API
"""

import aiohttp
import json
from typing import Optional
from .base import BaseSearcher, SearchResult
import urllib.parse


class UmicoSearcher(BaseSearcher):
    marketplace_name = "Umico (Birmarket)"
    marketplace_emoji = "🛍️"
    is_local = True

    async def search(self, query: str, barcode: Optional[str] = None) -> list[SearchResult]:
        results = []
        search_query = barcode if barcode else query

        try:
            async with aiohttp.ClientSession() as session:
                # Try Umico/Birmarket search API
                # Their frontend likely calls an internal API
                encoded = urllib.parse.quote_plus(search_query)

                # Try the API endpoint that the website uses
                api_url = f"https://api.umico.az/api/v1/products/search?q={encoded}&page=1&limit=10"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json",
                    "Origin": "https://birmarket.az",
                    "Referer": "https://birmarket.az/",
                }

                try:
                    async with session.get(api_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            products = data.get("products", data.get("data", data.get("items", [])))
                            if isinstance(products, list):
                                for prod in products[:10]:
                                    try:
                                        title = prod.get("name", prod.get("title", ""))
                                        price = prod.get("price", prod.get("sale_price", "N/A"))
                                        if isinstance(price, (int, float)):
                                            price = f"{price:.2f}"
                                        original_price = prod.get("original_price", prod.get("list_price"))
                                        discount = None
                                        if original_price and price and isinstance(original_price, (int, float)):
                                            disc_pct = int((1 - float(price) / float(original_price)) * 100)
                                            if disc_pct > 0:
                                                discount = f"{disc_pct}%"
                                        link = prod.get("url", prod.get("slug", ""))
                                        if link and not link.startswith("http"):
                                            link = f"https://birmarket.az/product/{link}"
                                        img = prod.get("image", prod.get("image_url", prod.get("images", [None])[0] if prod.get("images") else None))

                                        if title:
                                            results.append(self._make_result(
                                                title=title,
                                                price=str(price),
                                                currency="AZN",
                                                url=link or f"https://birmarket.az/search?q={encoded}",
                                                image_url=img,
                                                in_stock=prod.get("in_stock", prod.get("available", True)),
                                                discount=discount,
                                            ))
                                    except Exception:
                                        continue
                except Exception:
                    pass

                # Fallback: try alternate API patterns
                if not results:
                    alt_urls = [
                        f"https://birmarket.az/api/search?q={encoded}",
                        f"https://api.birmarket.az/v1/products?q={encoded}",
                    ]
                    for alt_url in alt_urls:
                        try:
                            async with session.get(alt_url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    products = data.get("products", data.get("data", data.get("items", [])))
                                    if isinstance(products, list):
                                        for prod in products[:10]:
                                            try:
                                                title = prod.get("name", prod.get("title", ""))
                                                price = prod.get("price", "N/A")
                                                if isinstance(price, (int, float)):
                                                    price = f"{price:.2f}"
                                                link = prod.get("url", prod.get("slug", ""))
                                                if link and not link.startswith("http"):
                                                    link = f"https://birmarket.az/product/{link}"
                                                img = prod.get("image", prod.get("image_url"))

                                                if title:
                                                    results.append(self._make_result(
                                                        title=title,
                                                        price=str(price),
                                                        currency="AZN",
                                                        url=link or f"https://birmarket.az/search?q={encoded}",
                                                        image_url=img,
                                                    ))
                                            except Exception:
                                                continue
                        except Exception:
                            continue

                # Final fallback: direct link to search page
                if not results:
                    results.append(self._make_result(
                        title=f"\"{search_query}\" üçün Umico-da axtarış",
                        price="—",
                        currency="AZN",
                        url=f"https://birmarket.az/search?q={encoded}",
                        in_stock=None,
                    ))

        except Exception as e:
            print(f"[Umico] Error: {e}")

        return results

    async def search_by_barcode(self, barcode: str) -> list[SearchResult]:
        return await self.search(barcode)
