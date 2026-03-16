"""Pinterest pin scheduling and management."""

import httpx

from src.shared.config import settings
from src.shared.exceptions import PinterestAPIError
from src.shared.logger import get_logger

logger = get_logger("pinterest_pins")


class PinterestPinClient:
    """Schedule and manage Pinterest pins linking to product listings."""

    API_BASE = "https://api.pinterest.com/v5"

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {settings.PINTEREST_ACCESS_TOKEN}"},
            timeout=30.0,
        )

    async def create_pin(
        self,
        board_id: str,
        title: str,
        description: str,
        image_url: str,
        destination_url: str,
    ) -> dict:
        """Create a pin on a Pinterest board.

        Args:
            board_id: The board to pin to.
            title: Pin title (first 50 chars most important).
            description: Pin description with keywords.
            image_url: URL of the pin image (2:3 ratio, 1000x1500px ideal).
            destination_url: Product URL with UTM tracking.

        Returns:
            Dict with pin ID and URL.
        """
        logger.info("creating_pinterest_pin", board_id=board_id, title=title)

        data = {
            "board_id": board_id,
            "title": title[:100],
            "description": description[:500],
            "media_source": {"source_type": "image_url", "url": image_url},
            "link": destination_url,
        }

        try:
            response = await self._client.post(f"{self.API_BASE}/pins", json=data)
            if response.status_code >= 400:
                raise PinterestAPIError(f"Pinterest API error: {response.status_code}")

            result = response.json()
            logger.info("pinterest_pin_created", pin_id=result.get("id"))
            return result

        except PinterestAPIError:
            raise
        except Exception as e:
            logger.error("pinterest_pin_error", error=str(e))
            raise PinterestAPIError(f"Failed to create pin: {e}") from e

    async def get_pin_analytics(self, pin_id: str) -> dict:
        """Get analytics for a specific pin."""
        response = await self._client.get(f"{self.API_BASE}/pins/{pin_id}/analytics")
        if response.status_code >= 400:
            raise PinterestAPIError(f"Pinterest analytics error: {response.status_code}")
        return response.json()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
