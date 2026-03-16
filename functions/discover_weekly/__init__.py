"""Azure Function: Weekly deep analysis — full keyword expansion and scoring."""

import logging

import azure.functions as func

logger = logging.getLogger("discover_weekly")


async def main(timer: func.TimerRequest) -> None:
    """Run weekly deep demand analysis.

    Triggered by timer — runs every Sunday at 2 AM UTC.
    """
    logger.info("discover_weekly triggered")

    try:
        from src.discover.orchestrator import DiscoverOrchestrator

        orchestrator = DiscoverOrchestrator()

        # TODO: Load seed keywords from database
        seed_keywords: list[str] = []

        new_keywords = await orchestrator.run_weekly_expansion(seed_keywords)

        # TODO: Store new keywords and run full scoring

        logger.info(f"discover_weekly complete: {len(new_keywords)} new keywords discovered")

    except Exception as e:
        logger.error(f"discover_weekly failed: {e}")
        raise
