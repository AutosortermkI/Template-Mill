"""Gumroad sales data collector."""

from datetime import date

from src.analyze.models import DailyStats
from src.shared.config import settings
from src.shared.exceptions import GumroadAPIError
from src.shared.logger import get_logger

logger = get_logger("gumroad_stats")

import httpx


class GumroadStatsCollector:
    """Collect sales data from Gumroad."""

    API_BASE = "https://api.gumroad.com/v2"

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {settings.GUMROAD_ACCESS_TOKEN}"},
            timeout=30.0,
        )

    async def collect_product_stats(self, product_id: str) -> DailyStats:
        """Collect sales data for a Gumroad product.

        Args:
            product_id: The Gumroad product ID.

        Returns:
            DailyStats for today.
        """
        logger.info("collecting_gumroad_stats", product_id=product_id)

        try:
            response = await self._client.get(f"{self.API_BASE}/products/{product_id}")

            if response.status_code >= 400:
                raise GumroadAPIError(f"Failed to get product stats: {response.status_code}")

            data = response.json().get("product", {})

            return DailyStats(
                listing_id=0,
                platform="gumroad",
                date=date.today(),
                sales=data.get("sales_count", 0),
                revenue=float(data.get("sales_usd_cents", 0)) / 100.0,
            )

        except GumroadAPIError:
            raise
        except Exception as e:
            logger.error("gumroad_stats_error", product_id=product_id, error=str(e))
            raise GumroadAPIError(f"Failed to collect Gumroad stats: {e}") from e

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
