"""Shopify analytics collector."""

from datetime import date

from src.analyze.models import DailyStats
from src.shared.config import settings
from src.shared.exceptions import ShopifyAPIError
from src.shared.logger import get_logger

logger = get_logger("shopify_stats")

import httpx


class ShopifyStatsCollector:
    """Collect analytics from Shopify Admin API."""

    API_VERSION = "2024-01"

    def __init__(self) -> None:
        self._base_url = f"https://{settings.SHOPIFY_STORE_URL}/admin/api/{self.API_VERSION}"
        self._client = httpx.AsyncClient(
            headers={
                "X-Shopify-Access-Token": settings.SHOPIFY_ACCESS_TOKEN,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def collect_product_stats(self, product_id: str) -> DailyStats:
        """Collect stats for a Shopify product.

        Args:
            product_id: The Shopify product ID.

        Returns:
            DailyStats for today.
        """
        logger.info("collecting_shopify_stats", product_id=product_id)

        try:
            response = await self._client.get(f"{self._base_url}/products/{product_id}.json")

            if response.status_code >= 400:
                raise ShopifyAPIError(f"Failed to get product stats: {response.status_code}")

            return DailyStats(
                listing_id=int(product_id),
                platform="shopify",
                date=date.today(),
            )

        except ShopifyAPIError:
            raise
        except Exception as e:
            logger.error("shopify_stats_error", product_id=product_id, error=str(e))
            raise ShopifyAPIError(f"Failed to collect Shopify stats: {e}") from e

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
