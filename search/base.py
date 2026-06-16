"""
Base class for all marketplace searchers.
"""

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Optional


@dataclass
class SearchResult:
    """Represents a single product search result from a marketplace."""
    marketplace: str
    title: str
    price: str
    currency: str
    url: str
    image_url: Optional[str] = None
    in_stock: Optional[bool] = None
    rating: Optional[float] = None
    is_local: bool = False  # True = Azerbaijan market

    def format(self) -> str:
        stock_icon = "✅" if self.in_stock is True else ("❌" if self.in_stock is False else "⚪")
        rating_str = f"⭐ {self.rating}/5" if self.rating else ""
        flag = "🇦🇿" if self.is_local else "🌍"
        lines = [
            f"{flag} <b>{self.marketplace}</b>",
            f"📦 {self.title[:120]}",
            f"💰 <b>{self.price} {self.currency}</b>",
            f"{stock_icon} {'Stokdadır' if self.in_stock else ('Stokda yoxdur' if self.in_stock is False else 'Stok məlumatı yoxdur')} {rating_str}",
            f"🔗 <a href=\"{self.url}\">Məhsula bax</a>",
        ]
        return "\n".join(lines)


class BaseSearcher(ABC):
    """Abstract base class for marketplace search implementations."""

    marketplace_name: str = ""
    marketplace_emoji: str = "🏪"
    is_local: bool = False

    @abstractmethod
    async def search(self, query: str, barcode: Optional[str] = None) -> list[SearchResult]:
        """Search for a product by query string or barcode."""
        pass

    async def search_by_barcode(self, barcode: str) -> list[SearchResult]:
        """Search by barcode — defaults to using barcode as query."""
        return await self.search(barcode)

    async def search_by_url(self, url: str) -> list[SearchResult]:
        """Search by product URL — extract name and search."""
        # Default: use URL as query (subclasses can override)
        return await self.search(url)

    def _make_result(self, **kwargs) -> SearchResult:
        """Helper to create SearchResult with marketplace defaults."""
        defaults = {
            "marketplace": self.marketplace_name,
            "is_local": self.is_local,
        }
        defaults.update(kwargs)
        return SearchResult(**defaults)

    def __repr__(self):
        return f"<{self.__class__.__name__} ({self.marketplace_name})>"
