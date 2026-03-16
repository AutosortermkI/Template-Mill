"""Competitor shop monitoring — detect new products, price changes, review velocity."""

from datetime import date

import httpx

from src.discover.models import CompetitorProduct, CompetitorShop
from src.shared.config import settings
from src.shared.exceptions import EtsyAPIError
from src.shared.logger import get_logger
from src.shared.rate_limiter import RateLimiter

logger = get_logger("competitor_monitor")

_rate_limiter = RateLimiter(rate=0.05, max_tokens=5.0)


class CompetitorMonitor:
    """Track competitor shops and detect changes in their product catalog."""

    API_BASE = "https://openapi.etsy.com/v3"

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            headers={"x-api-key": settings.ETSY_API_KEY},
            timeout=30.0,
        )

    async def fetch_shop_listings(self, shop: CompetitorShop) -> list[CompetitorProduct]:
        """Fetch all active listings from a competitor's Etsy shop.

        Args:
            shop: The competitor shop to scrape.

        Returns:
            List of CompetitorProduct snapshots.
        """
        await _rate_limiter.acquire()
        logger.info("fetching_competitor_listings", shop=shop.shop_name)

        try:
            response = await self._client.get(
                f"{self.API_BASE}/application/shops/{shop.platform_shop_id}/listings/active",
                params={"limit": 100},
            )

            if response.status_code != 200:
                raise EtsyAPIError(f"Failed to fetch shop listings: {response.status_code}")

            data = response.json()
            products: list[CompetitorProduct] = []

            for item in data.get("results", []):
                product = CompetitorProduct(
                    competitor_id=shop.id or 0,
                    platform_listing_id=str(item["listing_id"]),
                    title=item.get("title", ""),
                    price=item.get("price", {}).get("amount", 0) / item.get("price", {}).get("divisor", 100),
                    review_count=item.get("num_favorers", 0),
                    tags=item.get("tags", []),
                    captured_at=date.today(),
                    raw_data=item,
                )
                products.append(product)

            logger.info("competitor_listings_fetched", shop=shop.shop_name, count=len(products))
            return products

        except EtsyAPIError:
            raise
        except Exception as e:
            logger.error("competitor_fetch_error", shop=shop.shop_name, error=str(e))
            raise EtsyAPIError(f"Failed to monitor competitor: {e}") from e

    def diff_snapshots(
        self,
        previous: list[CompetitorProduct],
        current: list[CompetitorProduct],
    ) -> dict:
        """Compare two snapshots to detect changes.

        Returns:
            Dict with keys: new_listings, removed_listings, price_changes, review_changes.
        """
        prev_by_id = {p.platform_listing_id: p for p in previous}
        curr_by_id = {p.platform_listing_id: p for p in current}

        prev_ids = set(prev_by_id.keys())
        curr_ids = set(curr_by_id.keys())

        new_ids = curr_ids - prev_ids
        removed_ids = prev_ids - curr_ids
        common_ids = prev_ids & curr_ids

        price_changes = []
        review_changes = []

        for lid in common_ids:
            prev = prev_by_id[lid]
            curr = curr_by_id[lid]

            if prev.price != curr.price:
                price_changes.append({
                    "listing_id": lid,
                    "title": curr.title,
                    "old_price": prev.price,
                    "new_price": curr.price,
                })

            review_delta = curr.review_count - prev.review_count
            if review_delta != 0:
                review_changes.append({
                    "listing_id": lid,
                    "title": curr.title,
                    "review_delta": review_delta,
                })

        return {
            "new_listings": [curr_by_id[lid] for lid in new_ids],
            "removed_listings": list(removed_ids),
            "price_changes": price_changes,
            "review_changes": review_changes,
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
