"""
Product lookup service using barcode databases.
Falls back to Open Food Facts and UPCitemdb APIs.
"""

import aiohttp
import json
from typing import Optional


async def lookup_barcode(barcode: str) -> Optional[dict]:
    """
    Look up product information by barcode (EAN/UPC).
    Tries multiple barcode databases.
    Returns dict with 'name', 'description', 'image', 'category' or None.
    """
    # Try Open Food Facts first
    result = await _lookup_openfoodfacts(barcode)
    if result and result.get("name"):
        return result

    # Try UPCitemdb
    result = await _lookup_upcitemdb(barcode)
    if result and result.get("name"):
        return result

    # Try Barcodelookup
    result = await _lookup_barcodelookup(barcode)
    if result and result.get("name"):
        return result

    return None


async def _lookup_openfoodfacts(barcode: str) -> Optional[dict]:
    """Lookup via Open Food Facts API."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
            headers = {"User-Agent": "PriceCheckerBot/1.0"}
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

            if data.get("status") == 1:
                product = data.get("product", {})
                name = product.get("product_name") or product.get("product_name_en") or ""
                if not name:
                    return None
                return {
                    "name": name,
                    "description": product.get("generic_name", ""),
                    "image": product.get("image_url") or product.get("image_front_url"),
                    "category": product.get("categories", ""),
                    "brand": product.get("brands", ""),
                    "countries": product.get("countries", ""),
                }
    except Exception as e:
        print(f"[OpenFoodFacts] Error: {e}")
    return None


async def _lookup_upcitemdb(barcode: str) -> Optional[dict]:
    """Lookup via UPCitemdb API."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.upcitemdb.com/prod/trial/lookup?upc={barcode}"
            headers = {"User-Agent": "PriceCheckerBot/1.0"}
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

            items = data.get("items", [])
            if items:
                item = items[0]
                return {
                    "name": item.get("title", ""),
                    "description": item.get("description", ""),
                    "image": item.get("images", [None])[0] if item.get("images") else None,
                    "category": item.get("category", ""),
                    "brand": item.get("brand", ""),
                }
    except Exception as e:
        print(f"[UPCitemdb] Error: {e}")
    return None


async def _lookup_barcodelookup(barcode: str) -> Optional[dict]:
    """Lookup via barcodelookup.com (limited free API)."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.barcodelookup.com/v3/products?barcode={barcode}&formatted=y&key=demo"
            headers = {"User-Agent": "PriceCheckerBot/1.0"}
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

            products = data.get("products", [])
            if products:
                item = products[0]
                return {
                    "name": item.get("title", ""),
                    "description": item.get("description", ""),
                    "image": item.get("images", [None])[0] if item.get("images") else None,
                    "category": item.get("category", ""),
                    "brand": item.get("brand", ""),
                }
    except Exception as e:
        print(f"[Barcodelookup] Error: {e}")
    return None
