"""Etsy shop stats collector for daily performance data."""

from datetime import date

from src.analyze.models import DailyStats
from src.shared.config import settings
from src.shared.exceptions import EtsyAPIError
from src.shared.logger import get_logger
from src.shared.rate_limiter import RateLimiter

logger = get_logger("etsy_stats")

import httpx

_rate_limiter = RateLimiter(rate=0.05, max_tokens=5.0)


class EtsyStatsCollector:
    """Collect daily performance data from Etsy listings."""

    API_BASE = "https://openapi.etsy.com/v3"

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            headers={
                "x-api-key": settings.ETSY_API_KEY,
                "Authorization": f"Bearer {settings.ETSY_ACCESS_TOKEN}",
            },
            timeout=30.0,
        )

    async def collect_listing_stats(self, listing_id: str) -> DailyStats:
        """Collect performance stats for a single Etsy listing.

        Args:
            listing_id: The Etsy listing ID.

        Returns:
            DailyStats for today.
        """
        await _rate_limiter.acquire()
        logger.info("collecting_etsy_stats", listing_id=listing_id)

        try:
            response = await self._client.get(
                f"{self.API_BASE}/application/listings/{listing_id}",
            )

            if response.status_code >= 400:
                raise EtsyAPIError(f"Failed to get listing stats: {response.status_code}")

            data = response.json()

            return DailyStats(
                listing_id=int(listing_id),
                platform="etsy",
                date=date.today(),
                views=data.get("views", 0),
                favorites=data.get("num_favorers", 0),
            )

        except EtsyAPIError:
            raise
        except Exception as e:
            logger.error("etsy_stats_error", listing_id=listing_id, error=str(e))
            raise EtsyAPIError(f"Failed to collect Etsy stats: {e}") from e

    async def collect_shop_stats(self, shop_id: str) -> dict:
        """Collect overall shop performance stats."""
        await _rate_limiter.acquire()
        response = await self._client.get(f"{self.API_BASE}/application/shops/{shop_id}")

        if response.status_code >= 400:
            raise EtsyAPIError(f"Failed to get shop stats: {response.status_code}")

        return response.json()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
