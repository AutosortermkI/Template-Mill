"""Azure Function: Daily competitor tracking."""

import logging

import azure.functions as func

logger = logging.getLogger("competitor_monitor")


async def main(timer: func.TimerRequest) -> None:
    """Run daily competitor monitoring scan."""
    logger.info("competitor_monitor triggered")

    try:
        from src.discover.scrapers.competitor_monitor import CompetitorMonitor

        monitor = CompetitorMonitor()

        # TODO: Load tracked competitors from database
        # TODO: Fetch and diff snapshots
        # TODO: Store results and send alerts

        logger.info("competitor_monitor complete")
        await monitor.close()

    except Exception as e:
        logger.error(f"competitor_monitor failed: {e}")
        raise
