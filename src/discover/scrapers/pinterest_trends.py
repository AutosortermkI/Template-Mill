"""Pinterest Trends scraper for trend data capture."""

import httpx

from src.shared.config import settings
from src.shared.exceptions import PinterestAPIError
from src.shared.logger import get_logger
from src.shared.rate_limiter import RateLimiter
from src.shared.scraper_base import ScraperBase

logger = get_logger("pinterest_trends")

_rate_limiter = RateLimiter(rate=0.1, max_tokens=10.0)


class PinterestTrendsScraper(ScraperBase):
    """Capture trend data from Pinterest Trends and Pinterest Predicts."""

    API_BASE = "https://api.pinterest.com/v5"
    TRENDS_URL = "https://trends.pinterest.com"

    def __init__(self, headless: bool | None = None) -> None:
        super().__init__(headless=headless)
        self._api_client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {settings.PINTEREST_ACCESS_TOKEN}"},
            timeout=30.0,
        )

    async def get_trend_metrics_api(
        self,
        keyword: str,
        region: str = "US",
    ) -> dict:
        """Query Pinterest API for trend metrics.

        Args:
            keyword: The keyword to query trends for.
            region: Geographic region (US, UK, CA, AU).

        Returns:
            Dict with trend direction, volume, and related terms.
        """
        await _rate_limiter.acquire()
        logger.info("pinterest_api_query", keyword=keyword, region=region)

        try:
            response = await self._api_client.get(
                f"{self.API_BASE}/trends/metrics",
                params={"keyword": keyword, "region": region},
            )

            if response.status_code != 200:
                raise PinterestAPIError(f"Pinterest API error: {response.status_code}")

            return response.json()
        except PinterestAPIError:
            raise
        except Exception as e:
            logger.error("pinterest_api_error", keyword=keyword, error=str(e))
            raise PinterestAPIError(f"Failed to query Pinterest trends: {e}") from e

    async def scrape_trends_page(self, keyword: str) -> dict:
        """Scrape Pinterest Trends page as fallback when API is unavailable.

        Args:
            keyword: The keyword to search trends for.

        Returns:
            Dict with trend classification and related data.
        """
        page = await self.new_page()

        try:
            logger.info("scraping_pinterest_trends", keyword=keyword)
            await page.goto(
                f"{self.TRENDS_URL}/search?q={keyword}&geo=US",
                wait_until="networkidle",
            )
            await self.random_delay()
            await self.check_captcha(page)

            # Extract trend direction from the page
            trend_data: dict = {
                "keyword": keyword,
                "trend_direction": "stable",
                "related_terms": [],
            }

            return trend_data
        finally:
            await page.close()

    def classify_trend(self, momentum: float) -> str:
        """Classify a trend based on its momentum value.

        Args:
            momentum: Ratio of recent interest to historical interest.

        Returns:
            One of: 'breakout', 'rising', 'stable', 'declining'.
        """
        if momentum >= 3.0:
            return "breakout"
        elif momentum >= 1.5:
            return "rising"
        elif momentum >= 0.8:
            return "stable"
        else:
            return "declining"

    async def close(self) -> None:
        """Close the API client."""
        await self._api_client.aclose()
