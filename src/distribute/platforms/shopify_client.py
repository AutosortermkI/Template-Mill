"""Shopify Admin API product management client."""

import httpx

from src.distribute.models import Listing, SEOData
from src.shared.config import settings
from src.shared.exceptions import ShopifyAPIError, ShopifyAuthError
from src.shared.logger import get_logger

logger = get_logger("shopify_client")


class ShopifyClient:
    """Manage Shopify products via Admin REST API."""

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

    async def _request(self, method: str, path: str, **kwargs: object) -> dict:
        """Make an authenticated API request."""
        response = await self._client.request(method, f"{self._base_url}{path}", **kwargs)

        if response.status_code == 401:
            raise ShopifyAuthError("Shopify authentication failed")
        if response.status_code >= 400:
            raise ShopifyAPIError(f"Shopify API error {response.status_code}: {response.text}")

        return response.json() if response.content else {}

    async def create_product(self, seo_data: SEOData, price: float) -> Listing:
        """Create a new product on Shopify.

        Args:
            seo_data: SEO-optimized title and description.
            price: Product price.

        Returns:
            Listing object with the platform product ID.
        """
        logger.info("creating_shopify_product", title=seo_data.title)

        data = {
            "product": {
                "title": seo_data.title,
                "body_html": seo_data.description,
                "product_type": "Digital Template",
                "status": "draft",
                "variants": [{"price": str(price)}],
                "tags": ", ".join(seo_data.tags),
            }
        }

        result = await self._request("POST", "/products.json", json=data)
        product = result.get("product", {})

        listing = Listing(
            product_id=0,
            platform="shopify",
            platform_listing_id=str(product.get("id", "")),
            title=seo_data.title,
            tags=seo_data.tags,
            description=seo_data.description,
            status="draft",
        )

        logger.info("shopify_product_created", product_id=listing.platform_listing_id)
        return listing

    async def update_product(self, product_id: str, updates: dict) -> dict:
        """Update a Shopify product."""
        logger.info("updating_shopify_product", product_id=product_id)
        return await self._request("PUT", f"/products/{product_id}.json", json={"product": updates})

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
