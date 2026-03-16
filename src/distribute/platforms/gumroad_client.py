"""Gumroad API product management client."""

import httpx

from src.distribute.models import Listing, SEOData
from src.shared.config import settings
from src.shared.exceptions import GumroadAPIError, GumroadAuthError
from src.shared.logger import get_logger

logger = get_logger("gumroad_client")


class GumroadClient:
    """Manage Gumroad products via API v2."""

    API_BASE = "https://api.gumroad.com/v2"

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {settings.GUMROAD_ACCESS_TOKEN}"},
            timeout=30.0,
        )

    async def _request(self, method: str, path: str, **kwargs: object) -> dict:
        """Make an authenticated API request."""
        response = await self._client.request(method, f"{self.API_BASE}{path}", **kwargs)

        if response.status_code == 401:
            raise GumroadAuthError("Gumroad authentication failed")
        if response.status_code >= 400:
            raise GumroadAPIError(f"Gumroad API error {response.status_code}: {response.text}")

        return response.json()

    async def create_product(self, seo_data: SEOData, price: int) -> Listing:
        """Create a new product on Gumroad.

        Args:
            seo_data: SEO-optimized title and description.
            price: Price in cents (e.g., 1900 for $19.00).

        Returns:
            Listing object with the platform product ID.
        """
        logger.info("creating_gumroad_product", title=seo_data.title)

        data = {
            "name": seo_data.title,
            "description": seo_data.description,
            "price": price,
            "is_digital": True,
        }

        result = await self._request("POST", "/products", data=data)
        product = result.get("product", {})

        listing = Listing(
            product_id=0,
            platform="gumroad",
            platform_listing_id=product.get("id", ""),
            listing_url=product.get("short_url", ""),
            title=seo_data.title,
            description=seo_data.description,
            status="draft",
        )

        logger.info("gumroad_product_created", product_id=listing.platform_listing_id)
        return listing

    async def update_product(self, product_id: str, updates: dict) -> dict:
        """Update a Gumroad product."""
        logger.info("updating_gumroad_product", product_id=product_id)
        return await self._request("PUT", f"/products/{product_id}", data=updates)

    async def get_sales(self, product_id: str) -> list[dict]:
        """Get sales data for a product."""
        result = await self._request("GET", f"/products/{product_id}/sales")
        return result.get("sales", [])

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
