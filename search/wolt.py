"""
Wolt Searcher - searches Araz, Bravo, and other AZ supermarkets via Wolt API
This is the most reliable way to search Azerbaijani supermarkets because
Wolt has a public consumer API that returns product data with prices.
"""

import aiohttp
from typing import Optional
from .base import BaseSearcher, SearchResult

# Baku coordinates
BAKU_LAT = "40.4093"
BAKU_LON = "49.8671"

WOLT_SEARCH_URL = "https://restaurant-api.wolt.com/v1/pages/search"


class WoltSearcher(BaseSearcher):
    """
    Search all supermarkets on Wolt (Araz, Bravo, SPAR, Neptun, etc.)
    Returns results grouped by venue/store name.
    """
    marketplace_name = "Wolt Marketlər"
    marketplace_emoji = "🛒"
    is_local = True

    # Known supermarket venue slugs for direct menu access
    SUPERMARKET_SLUGS = {
        "araz": [
            "araz-supermarket-6-parallel",
            "araz-supermarket-28-may",
            "araz-supermarket-azadlig-3",
            "araz-supermarket-nasimi",
            "araz-supermarket-neftchiler",
        ],
        "bravo": [
            "bravo-supermarket-azure",
            "bravo-supermarket-bulbul-ave",
            "bravo-supermarket-tahir-97",
        ],
    }

    async def search(self, query: str, barcode: Optional[str] = None) -> list[SearchResult]:
        results = []
        search_query = barcode if barcode else query

        try:
            async with aiohttp.ClientSession() as session:
                # Search items across all venues in Baku
                payload = {
                    "q": search_query,
                    "target": "items",
                    "lat": BAKU_LAT,
                    "lon": BAKU_LON,
                }
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Origin": "https://wolt.com",
                    "Referer": "https://wolt.com/",
                }

                async with session.post(
                    WOLT_SEARCH_URL,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status != 200:
                        print(f"[Wolt] Search returned status {resp.status}")
                        return results
                    data = await resp.json()

                # Parse results from sections
                sections = data.get("sections", [])
                for section in sections:
                    items = section.get("items", [])
                    for item in items:
                        try:
                            venue_info = item.get("venue", {})
                            venue_name = venue_info.get("name", "Wolt Market")
                            item_name = item.get("name", "")
                            price_data = item.get("price", {})
                            image_data = item.get("image", {})

                            if not item_name:
                                continue

                            # Price is in cents, convert to AZN
                            price_amount = price_data.get("amount", 0) / 100
                            currency = price_data.get("currency", "AZN")
                            if currency == "AZN":
                                price_str = f"{price_amount:.2f}"
                            else:
                                price_str = f"{price_amount:.2f}"

                            # Build product URL
                            venue_slug = venue_info.get("slug", "")
                            product_url = f"https://wolt.com/en/aze/baku/venue/{venue_slug}" if venue_slug else "https://wolt.com/en/aze/baku/category/supermarkets"

                            image_url = image_data.get("url", "") if image_data else None

                            # Determine which store
                            store_label = venue_name

                            results.append(self._make_result(
                                marketplace=store_label,
                                title=item_name,
                                price=price_str,
                                currency=currency,
                                url=product_url,
                                image_url=image_url,
                                in_stock=True,
                            ))

                            # Limit to 15 results
                            if len(results) >= 15:
                                break
                        except Exception as e:
                            print(f"[Wolt] Item parse error: {e}")
                            continue

                    if len(results) >= 15:
                        break

        except Exception as e:
            print(f"[Wolt] Error: {e}")

        return results

    async def search_by_barcode(self, barcode: str) -> list[SearchResult]:
        return await self.search(barcode)
