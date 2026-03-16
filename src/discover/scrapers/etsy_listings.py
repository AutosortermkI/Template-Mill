"""Etsy listing data extractor for competition analysis."""

import httpx

from src.discover.models import EtsyListingData
from src.shared.config import settings
from src.shared.exceptions import EtsyAPIError, EtsyRateLimitError
from src.shared.logger import get_logger
from src.shared.rate_limiter import RateLimiter

logger = get_logger("etsy_listings")

# Etsy API allows 5,000 calls/day — roughly 3.5/min sustained
_rate_limiter = RateLimiter(rate=0.05, max_tokens=5.0)


class EtsyListingScraper:
    """Extract listing data from Etsy via API or scraping fallback."""

    API_BASE = "https://openapi.etsy.com/v3"

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            headers={"x-api-key": settings.ETSY_API_KEY},
            timeout=30.0,
        )

    async def search_listings(
        self,
        keyword: str,
        limit: int = 48,
        sort_on: str = "score",
    ) -> list[EtsyListingData]:
        """Search Etsy listings for a keyword.

        Args:
            keyword: Search term.
            limit: Max results to return (max 100 per Etsy API).
            sort_on: Sort order — 'score' (relevance) or 'num_favorers'.

        Returns:
            List of parsed listing data.
        """
        await _rate_limiter.acquire()
        logger.info("searching_etsy", keyword=keyword, limit=limit, sort=sort_on)

        try:
            response = await self._client.get(
                f"{self.API_BASE}/application/listings/active",
                params={
                    "keywords": keyword,
                    "limit": min(limit, 100),
                    "sort_on": sort_on,
                    "includes": "Images",
                },
            )

            if response.status_code == 429:
                raise EtsyRateLimitError("Etsy API rate limit exceeded")
            if response.status_code != 200:
                raise EtsyAPIError(f"Etsy API error: {response.status_code} — {response.text}")

            data = response.json()
            listings = []
            for item in data.get("results", []):
                listing = EtsyListingData(
                    listing_id=str(item["listing_id"]),
                    title=item.get("title", ""),
                    price=item.get("price", {}).get("amount", 0) / item.get("price", {}).get("divisor", 100),
                    currency=item.get("price", {}).get("currency_code", "USD"),
                    review_count=item.get("num_favorers", 0),
                    star_rating=0.0,
                    shop_name="",
                    num_favorers=item.get("num_favorers", 0),
                    tags=item.get("tags", []),
                )
                listings.append(listing)

            logger.info("etsy_search_complete", keyword=keyword, results=len(listings))
            return listings

        except (EtsyRateLimitError, EtsyAPIError):
            raise
        except Exception as e:
            logger.error("etsy_search_error", keyword=keyword, error=str(e))
            raise EtsyAPIError(f"Failed to search Etsy: {e}") from e

    async def get_competition_stats(self, keyword: str) -> dict:
        """Get competition statistics for a keyword.

        Returns dict with keys: listing_count, avg_price, avg_reviews, top_seller_ids.
        """
        listings = await self.search_listings(keyword, limit=48)

        if not listings:
            return {
                "listing_count": 0,
                "avg_price": 0.0,
                "avg_reviews": 0.0,
                "top_seller_ids": [],
            }

        prices = [l.price for l in listings if l.price > 0]
        reviews = [l.review_count for l in listings]

        return {
            "listing_count": len(listings),
            "avg_price": sum(prices) / len(prices) if prices else 0.0,
            "avg_reviews": sum(reviews) / len(reviews) if reviews else 0.0,
            "top_seller_ids": [l.listing_id for l in listings[:10]],
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
