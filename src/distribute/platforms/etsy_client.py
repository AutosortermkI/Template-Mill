"""Etsy API listing management client."""

import httpx

from src.distribute.models import Listing, SEOData
from src.shared.config import settings
from src.shared.exceptions import EtsyAPIError, EtsyAuthError, EtsyRateLimitError
from src.shared.logger import get_logger
from src.shared.rate_limiter import RateLimiter

logger = get_logger("etsy_client")

_rate_limiter = RateLimiter(rate=0.05, max_tokens=5.0)


class EtsyClient:
    """Manage Etsy listings via API v3."""

    API_BASE = "https://openapi.etsy.com/v3"

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            headers={
                "x-api-key": settings.ETSY_API_KEY,
                "Authorization": f"Bearer {settings.ETSY_ACCESS_TOKEN}",
            },
            timeout=30.0,
        )

    async def _request(self, method: str, path: str, **kwargs: object) -> dict:
        """Make an authenticated API request with rate limiting."""
        await _rate_limiter.acquire()
        response = await self._client.request(method, f"{self.API_BASE}{path}", **kwargs)

        if response.status_code == 401:
            raise EtsyAuthError("Etsy authentication failed")
        if response.status_code == 429:
            raise EtsyRateLimitError("Etsy rate limit exceeded")
        if response.status_code >= 400:
            raise EtsyAPIError(f"Etsy API error {response.status_code}: {response.text}")

        return response.json() if response.content else {}

    async def create_listing(
        self,
        shop_id: str,
        seo_data: SEOData,
        price: float,
        is_digital: bool = True,
    ) -> Listing:
        """Create a new draft listing on Etsy.

        Args:
            shop_id: The Etsy shop ID.
            seo_data: SEO-optimized title, tags, and description.
            price: Product price in USD.
            is_digital: Whether this is a digital download.

        Returns:
            Listing object with the platform listing ID.
        """
        logger.info("creating_etsy_listing", title=seo_data.title)

        data = {
            "title": seo_data.title[:140],
            "description": seo_data.description,
            "price": price,
            "who_made": "i_did",
            "when_made": "made_to_order",
            "taxonomy_id": 69,  # Digital templates
            "tags": seo_data.tags[:13],
            "is_digital": is_digital,
            "type": "download" if is_digital else "physical",
            "state": "draft",
        }

        result = await self._request(
            "POST",
            f"/application/shops/{shop_id}/listings",
            json=data,
        )

        listing = Listing(
            product_id=0,
            platform="etsy",
            platform_listing_id=str(result.get("listing_id", "")),
            title=seo_data.title,
            tags=seo_data.tags,
            description=seo_data.description,
            status="draft",
        )

        logger.info("etsy_listing_created", listing_id=listing.platform_listing_id)
        return listing

    async def update_listing(self, listing_id: str, updates: dict) -> dict:
        """Update an existing Etsy listing."""
        logger.info("updating_etsy_listing", listing_id=listing_id)
        return await self._request("PUT", f"/application/listings/{listing_id}", json=updates)

    async def upload_image(self, shop_id: str, listing_id: str, image_path: str) -> dict:
        """Upload an image to an Etsy listing."""
        logger.info("uploading_etsy_image", listing_id=listing_id)
        with open(image_path, "rb") as f:
            return await self._request(
                "POST",
                f"/application/shops/{shop_id}/listings/{listing_id}/images",
                files={"image": f},
            )

    async def get_listing_stats(self, listing_id: str) -> dict:
        """Get performance stats for a listing."""
        return await self._request("GET", f"/application/listings/{listing_id}")

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
