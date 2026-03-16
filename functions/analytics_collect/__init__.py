"""Azure Function: Daily sales data collection across all platforms."""

import logging

import azure.functions as func

logger = logging.getLogger("analytics_collect")


async def main(timer: func.TimerRequest) -> None:
    """Collect daily performance data from all platforms."""
    logger.info("analytics_collect triggered")

    try:
        from src.analyze.orchestrator import AnalyzeOrchestrator

        orchestrator = AnalyzeOrchestrator()

        # TODO: Load active listings from database
        listings: list[dict] = []

        collected = orchestrator.run_daily_collection(listings)

        # TODO: Store collected stats

        logger.info(f"analytics_collect complete: {len(collected)} listings processed")

    except Exception as e:
        logger.error(f"analytics_collect failed: {e}")
        raise
