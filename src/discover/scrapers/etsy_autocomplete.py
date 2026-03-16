"""Etsy search autocomplete scraper for keyword expansion."""

from src.shared.logger import get_logger
from src.shared.scraper_base import ScraperBase

logger = get_logger("etsy_autocomplete")


class EtsyAutocompleteScraper(ScraperBase):
    """Expand seed keywords using Etsy's autocomplete suggestions."""

    ETSY_URL = "https://www.etsy.com"

    async def expand_keyword(self, seed: str) -> list[str]:
        """Type seed into Etsy search and capture autocomplete suggestions.

        Args:
            seed: The seed keyword to expand.

        Returns:
            Deduplicated list of autocomplete suggestions.
        """
        suggestions: list[str] = []
        page = await self.new_page()

        try:
            logger.info("expanding_keyword", seed=seed)
            await page.goto(self.ETSY_URL, wait_until="domcontentloaded")
            await self.random_delay()
            await self.check_captcha(page)

            search_box = page.locator('input[name="search_query"]')

            # First pass: type the seed keyword
            await search_box.type(seed, delay=100)
            await page.wait_for_timeout(1500)

            items = await page.locator('[role="option"]').all_text_contents()
            suggestions.extend(items)
            logger.info("base_suggestions", seed=seed, count=len(items))

            # Second pass: seed + each letter a-z for deeper expansion
            for letter in "abcdefghijklmnopqrstuvwxyz":
                await search_box.fill(f"{seed} {letter}")
                await page.wait_for_timeout(1000)

                items = await page.locator('[role="option"]').all_text_contents()
                suggestions.extend(items)
                await self.random_delay(min_sec=0.5, max_sec=1.5)

            logger.info("expansion_complete", seed=seed, total_raw=len(suggestions))
        finally:
            await page.close()

        deduplicated = list(set(suggestions))
        logger.info("expansion_deduplicated", seed=seed, unique_count=len(deduplicated))
        return deduplicated

    async def expand_all(self, seeds: list[str]) -> dict[str, list[str]]:
        """Expand multiple seed keywords.

        Args:
            seeds: List of seed keywords to expand.

        Returns:
            Dict mapping each seed to its expanded suggestions.
        """
        results: dict[str, list[str]] = {}
        for seed in seeds:
            results[seed] = await self.expand_keyword(seed)
            await self.random_delay(min_sec=3.0, max_sec=6.0)
        return results
