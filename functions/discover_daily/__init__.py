"""Azure Function: Daily demand scan — runs Etsy + Google Trends for top keywords."""

import json
import logging

import azure.functions as func

logger = logging.getLogger("discover_daily")


async def main(timer: func.TimerRequest) -> None:
    """Run daily demand intelligence scan.

    Triggered by timer (configured in function.json).
    """
    logger.info("discover_daily triggered")

    try:
        from src.discover.orchestrator import DiscoverOrchestrator

        orchestrator = DiscoverOrchestrator()

        # TODO: Load top keywords from database
        keywords: list[dict] = []

        opportunities = await orchestrator.run_daily(keywords)

        # TODO: Store results in database

        logger.info(f"discover_daily complete: {len(opportunities)} opportunities scored")

    except Exception as e:
        logger.error(f"discover_daily failed: {e}")
        raise
