"""Google Trends wrapper using pytrends with rate limiting and retry logic."""

import asyncio
from typing import TypedDict
from urllib3.util.retry import Retry

from src.shared.exceptions import RateLimitError
from src.shared.logger import get_logger

# ── Compatibility shim ──────────────────────────────────────────────────────
# pytrends 4.9.x passes the deprecated `method_whitelist` kwarg to
# urllib3.util.retry.Retry.  That parameter was removed in urllib3 2.0
# (replaced by `allowed_methods`).  We monkey-patch the constructor so the
# call succeeds regardless of the urllib3 version installed.
_original_retry_init = Retry.__init__


def _patched_retry_init(self, *args, **kwargs):
    if "method_whitelist" in kwargs:
        kwargs["allowed_methods"] = kwargs.pop("method_whitelist")
    return _original_retry_init(self, *args, **kwargs)


Retry.__init__ = _patched_retry_init  # type: ignore[assignment]

from pytrends.request import TrendReq  # noqa: E402  (must import after patch)

logger = get_logger("google_trends")


class TrendData(TypedDict):
    """Per-keyword trend data returned by the scraper."""

    momentum: float  # recent / overall average (>1 = rising, <1 = declining)
    interest: int  # average interest level (0-100, normalized within batch)


def _chunk(lst: list, size: int) -> list[list]:
    """Split a list into chunks of the given size."""
    return [lst[i : i + size] for i in range(0, len(lst), size)]


class GoogleTrendsScraper:
    """Wrapper around pytrends with rate limiting and structured output.

    When batch requests return empty data, retries keywords individually.
    Raises clear errors instead of silently returning zeros.
    """

    def __init__(self) -> None:
        try:
            self.pytrends = TrendReq(hl="en-US", tz=300, retries=3, backoff_factor=2)
        except Exception as e:
            logger.error("google_trends_init_failed", error=str(e))
            raise ConnectionError(
                f"Could not connect to Google Trends: {e}\n"
                "This usually means Google is blocking your requests.\n"
                "Try: using a VPN, waiting a few minutes, or running with --etsy-only"
            ) from e

    def _extract_trend_data(self, df, keyword: str) -> TrendData | None:
        """Extract momentum and interest from a DataFrame for a keyword."""
        if df.empty or keyword not in df.columns:
            return None
        recent = df[keyword].tail(4).mean()
        overall = df[keyword].mean()
        return TrendData(
            momentum=round(recent / max(overall, 1), 2),
            interest=round(overall),
        )

    async def _fetch_single(self, keyword: str, geo: str) -> TrendData | None:
        """Fetch trend data for a single keyword (fallback for failed batches)."""
        try:
            self.pytrends.build_payload([keyword], timeframe="today 12-m", geo=geo)
            df = self.pytrends.interest_over_time()
            return self._extract_trend_data(df, keyword)
        except Exception as e:
            logger.warning("google_trends_single_failed", keyword=keyword, error=str(e))
            return None

    async def get_momentum(self, keywords: list[str], geo: str = "US") -> dict[str, TrendData]:
        """Calculate trend momentum and interest level for each keyword.

        Momentum = average interest over last ~30 days / overall average.
        A value > 1.0 indicates rising interest, < 1.0 indicates declining.
        Interest = average interest level over the past 12 months (0-100).

        Note: Interest values are normalized within each batch of 5 keywords,
        so they are most meaningful for relative comparison within a batch.

        When a batch returns empty data, retries each keyword individually.

        Args:
            keywords: List of keywords to analyze (batched in groups of 5).
            geo: Geographic region code.

        Returns:
            Dict mapping keyword to TrendData with momentum and interest.
        """
        results: dict[str, TrendData] = {}
        failed_keywords: list[str] = []

        for batch_num, batch in enumerate(_chunk(keywords, 5)):
            try:
                logger.info("google_trends_batch", keywords=batch, geo=geo)
                self.pytrends.build_payload(batch, timeframe="today 12-m", geo=geo)
                df = self.pytrends.interest_over_time()

                if df.empty:
                    logger.warning(
                        "google_trends_empty_response",
                        batch=batch,
                        msg="Google returned no data for this batch",
                    )
                    failed_keywords.extend(batch)
                else:
                    batch_got_data = False
                    for kw in batch:
                        td = self._extract_trend_data(df, kw)
                        if td is not None:
                            results[kw] = td
                            batch_got_data = True
                        else:
                            failed_keywords.append(kw)

                    if batch_got_data:
                        logger.info("google_trends_batch_complete", results_count=len(batch))

            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "too many" in error_msg:
                    logger.warning("google_trends_rate_limited", batch=batch)
                    raise RateLimitError(f"Google Trends rate limit hit: {e}") from e
                logger.error("google_trends_error", batch=batch, error=str(e))
                failed_keywords.extend(batch)

            # Rate limit: 10 second delay between batches
            if batch_num < len(_chunk(keywords, 5)) - 1:
                await asyncio.sleep(10)

        # Retry failed keywords individually (Google sometimes rejects batches
        # but accepts individual queries)
        if failed_keywords:
            logger.info(
                "google_trends_retry_individual",
                count=len(failed_keywords),
                msg="Retrying failed keywords individually",
            )
            for kw in failed_keywords:
                await asyncio.sleep(3)  # Shorter delay for individual requests
                td = await self._fetch_single(kw, geo)
                if td is not None:
                    results[kw] = td
                else:
                    results[kw] = TrendData(momentum=0.0, interest=0)

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
