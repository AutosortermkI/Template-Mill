"""Backfill historical trend data for existing keywords."""

import asyncio

from src.discover.scrapers.google_trends import GoogleTrendsScraper
from src.shared.logger import get_logger, setup_logging


async def main() -> None:
    """Backfill Google Trends data for all seed keywords."""
    setup_logging()
    logger = get_logger("backfill_trends")
    logger.info("backfill_trends_start")

    scraper = GoogleTrendsScraper()

    # TODO: Load keywords from database
    keywords: list[str] = []

    if not keywords:
        logger.info("no_keywords_to_backfill")
        return

    momentum = await scraper.get_momentum(keywords)
    logger.info("backfill_complete", keyword_count=len(momentum))

    # TODO: Store results in demand_signals table


if __name__ == "__main__":
    asyncio.run(main())
