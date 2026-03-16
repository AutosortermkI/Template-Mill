"""TikTok Creative Center scraper for trending hashtags and keyword insights."""

from src.shared.logger import get_logger
from src.shared.scraper_base import ScraperBase

logger = get_logger("tiktok_creative")


class TikTokCreativeScraper(ScraperBase):
    """Scrape TikTok Creative Center for trend data in template/productivity categories."""

    BASE_URL = "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en"
    KEYWORD_URL = "https://ads.tiktok.com/business/creativecenter/inspiration/popular/keyword/pc/en"

    RELEVANT_INDUSTRIES = ["Education", "Apps & Software", "Business Services"]

    async def scrape_trending_hashtags(self, time_range: str = "7") -> list[dict]:
        """Scrape trending hashtags from TikTok Creative Center.

        Args:
            time_range: '7' for 7-day or '30' for 30-day trends.

        Returns:
            List of dicts with hashtag name, post count, trend direction, growth rate.
        """
        page = await self.new_page()
        hashtags: list[dict] = []

        try:
            logger.info("scraping_tiktok_hashtags", time_range=time_range)
            await page.goto(self.BASE_URL, wait_until="networkidle")
            await self.random_delay(min_sec=3.0, max_sec=6.0)
            await self.check_captcha(page)

            # TikTok CC is a fully JS-rendered SPA
            # Use text-based locators for resilience against class name changes
            rows = page.locator("table tbody tr")
            count = await rows.count()

            for i in range(min(count, 50)):
                row = rows.nth(i)
                cells = row.locator("td")
                cell_count = await cells.count()

                if cell_count >= 3:
                    name = (await cells.nth(1).text_content() or "").strip()
                    posts = (await cells.nth(2).text_content() or "").strip()

                    if name:
                        hashtags.append({
                            "name": name,
                            "post_count": posts,
                            "time_range": time_range,
                        })

                await self.random_delay(min_sec=0.2, max_sec=0.5)

            logger.info("tiktok_hashtags_scraped", count=len(hashtags))
        finally:
            await page.close()

        return hashtags

    async def scrape_keyword_insights(self) -> list[dict]:
        """Scrape keyword insights from TikTok Creative Center.

        Returns:
            List of dicts with keyword, volume tier, and related terms.
        """
        page = await self.new_page()
        keywords: list[dict] = []

        try:
            logger.info("scraping_tiktok_keywords")
            await page.goto(self.KEYWORD_URL, wait_until="networkidle")
            await self.random_delay(min_sec=3.0, max_sec=6.0)
            await self.check_captcha(page)

            rows = page.locator("table tbody tr")
            count = await rows.count()

            for i in range(min(count, 50)):
                row = rows.nth(i)
                cells = row.locator("td")
                cell_count = await cells.count()

                if cell_count >= 2:
                    keyword = (await cells.nth(1).text_content() or "").strip()
                    if keyword:
                        keywords.append({
                            "keyword": keyword,
                            "volume_tier": "unknown",
                        })

            logger.info("tiktok_keywords_scraped", count=len(keywords))
        finally:
            await page.close()

        return keywords
