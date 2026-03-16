"""Google Trends wrapper using pytrends with rate limiting and retry logic."""

import asyncio

from pytrends.request import TrendReq

from src.shared.exceptions import RateLimitError
from src.shared.logger import get_logger

logger = get_logger("google_trends")


def _chunk(lst: list, size: int) -> list[list]:
    """Split a list into chunks of the given size."""
    return [lst[i : i + size] for i in range(0, len(lst), size)]


class GoogleTrendsScraper:
    """Wrapper around pytrends with rate limiting and structured output."""

    def __init__(self) -> None:
        self.pytrends = TrendReq(hl="en-US", tz=300, retries=3, backoff_factor=2)

    async def get_momentum(self, keywords: list[str], geo: str = "US") -> dict[str, float]:
        """Calculate trend momentum for each keyword.

        Momentum = average interest over last ~30 days / overall average.
        A value > 1.0 indicates rising interest, < 1.0 indicates declining.

        Args:
            keywords: List of keywords to analyze (batched in groups of 5).
            geo: Geographic region code.

        Returns:
            Dict mapping keyword to momentum ratio.
        """
        results: dict[str, float] = {}

        for batch in _chunk(keywords, 5):
            try:
                logger.info("google_trends_batch", keywords=batch, geo=geo)
                self.pytrends.build_payload(batch, timeframe="today 12-m", geo=geo)
                df = self.pytrends.interest_over_time()

                for kw in batch:
                    if kw in df.columns:
                        recent = df[kw].tail(4).mean()
                        overall = df[kw].mean()
                        results[kw] = round(recent / max(overall, 1), 2)
                    else:
                        results[kw] = 0.0

                logger.info("google_trends_batch_complete", results_count=len(batch))

            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "too many" in error_msg:
                    logger.warning("google_trends_rate_limited", batch=batch)
                    raise RateLimitError(f"Google Trends rate limit hit: {e}") from e
                logger.error("google_trends_error", batch=batch, error=str(e))
                for kw in batch:
                    results[kw] = 0.0

            # Rate limit: 10 second delay between batches
            await asyncio.sleep(10)

        return results

    async def get_related_queries(self, keyword: str, geo: str = "US") -> dict[str, list[str]]:
        """Get related rising and top queries for a keyword.

        Args:
            keyword: The keyword to find related queries for.
            geo: Geographic region code.

        Returns:
            Dict with 'rising' and 'top' lists of related query strings.
        """
        logger.info("google_trends_related", keyword=keyword, geo=geo)

        try:
            self.pytrends.build_payload([keyword], timeframe="today 12-m", geo=geo)
            related = self.pytrends.related_queries()

            result: dict[str, list[str]] = {"rising": [], "top": []}

            kw_data = related.get(keyword, {})
            if kw_data.get("rising") is not None:
                result["rising"] = kw_data["rising"]["query"].tolist()[:20]
            if kw_data.get("top") is not None:
                result["top"] = kw_data["top"]["query"].tolist()[:20]

            return result

        except Exception as e:
            logger.error("google_trends_related_error", keyword=keyword, error=str(e))
            return {"rising": [], "top": []}
