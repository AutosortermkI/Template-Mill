"""APScheduler-based job scheduler replacing Azure Functions.

Runs all scheduled pipeline jobs (daily scans, weekly analysis, competitor
monitoring, analytics collection, weekly digest) as cron-triggered tasks
in a single long-running process.

Usage:
    python -m src.scheduler          # run the scheduler
    python -m src.scheduler --once   # run all jobs once immediately, then exit
"""

import argparse
import asyncio
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.shared.logger import get_logger, setup_logging

logger = get_logger("scheduler")


async def job_discover_daily() -> None:
    """Daily demand scan — Etsy listings + Google Trends for top keywords."""
    logger.info("job_start", job="discover_daily")
    try:
        from src.discover.orchestrator import DiscoverOrchestrator

        orchestrator = DiscoverOrchestrator()
        opportunities = await orchestrator.run_daily()
        await orchestrator.close()
        logger.info("job_complete", job="discover_daily", opportunities=len(opportunities))
    except Exception as e:
        logger.error("job_failed", job="discover_daily", error=str(e))


async def job_discover_weekly() -> None:
    """Weekly deep analysis — full keyword expansion and scoring."""
    logger.info("job_start", job="discover_weekly")
    try:
        from src.discover.orchestrator import DiscoverOrchestrator

        orchestrator = DiscoverOrchestrator()
        new_keywords = await orchestrator.run_weekly_expansion()
        # Run a full scoring pass on all keywords after expansion
        opportunities = await orchestrator.run_daily()
        await orchestrator.close()
        logger.info(
            "job_complete",
            job="discover_weekly",
            new_keywords=len(new_keywords),
            opportunities=len(opportunities),
        )
    except Exception as e:
        logger.error("job_failed", job="discover_weekly", error=str(e))


async def job_competitor_monitor() -> None:
    """Daily competitor tracking."""
    logger.info("job_start", job="competitor_monitor")
    try:
        from src.discover.scrapers.competitor_monitor import CompetitorMonitor

        monitor = CompetitorMonitor()
        # TODO: Load tracked competitors from database
        # TODO: Fetch and diff snapshots, store results, send alerts
        await monitor.close()
        logger.info("job_complete", job="competitor_monitor")
    except Exception as e:
        logger.error("job_failed", job="competitor_monitor", error=str(e))


async def job_analytics_collect() -> None:
    """Daily sales data collection across all platforms."""
    logger.info("job_start", job="analytics_collect")
    try:
        from src.analyze.orchestrator import AnalyzeOrchestrator

        orchestrator = AnalyzeOrchestrator()
        # TODO: Load active listings from database
        listings: list[dict] = []
        collected = orchestrator.run_daily_collection(listings)
        # TODO: Store collected stats
        logger.info("job_complete", job="analytics_collect", collected=len(collected))
    except Exception as e:
        logger.error("job_failed", job="analytics_collect", error=str(e))


async def job_weekly_digest() -> None:
    """Weekly performance report generation."""
    logger.info("job_start", job="weekly_digest")
    try:
        from src.analyze.orchestrator import AnalyzeOrchestrator

        orchestrator = AnalyzeOrchestrator()
        # TODO: Aggregate stats from database
        current_stats: dict = {}
        previous_stats: dict = {}
        report = orchestrator.run_weekly_report(current_stats, previous_stats)
        # TODO: Send email digest
        logger.info(
            "job_complete",
            job="weekly_digest",
            action_items=len(report.get("action_items", [])),
        )
    except Exception as e:
        logger.error("job_failed", job="weekly_digest", error=str(e))


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the APScheduler instance with all pipeline jobs."""
    scheduler = AsyncIOScheduler()

    # Daily at 06:00 UTC — demand scan
    scheduler.add_job(job_discover_daily, "cron", hour=6, minute=0, id="discover_daily")

    # Daily at 07:00 UTC — competitor monitoring
    scheduler.add_job(job_competitor_monitor, "cron", hour=7, minute=0, id="competitor_monitor")

    # Daily at 08:00 UTC — analytics collection
    scheduler.add_job(job_analytics_collect, "cron", hour=8, minute=0, id="analytics_collect")

    # Sunday at 02:00 UTC — weekly deep analysis
    scheduler.add_job(job_discover_weekly, "cron", day_of_week="sun", hour=2, minute=0, id="discover_weekly")

    # Monday at 09:00 UTC — weekly digest
    scheduler.add_job(job_weekly_digest, "cron", day_of_week="mon", hour=9, minute=0, id="weekly_digest")

    return scheduler


async def run_all_once() -> None:
    """Run every job once immediately (useful for testing or manual runs)."""
    logger.info("running_all_jobs_once")
    await job_discover_daily()
    await job_discover_weekly()
    await job_competitor_monitor()
    await job_analytics_collect()
    await job_weekly_digest()
    logger.info("all_jobs_complete")


def main() -> None:
    """Entry point for the scheduler."""
    setup_logging()

    parser = argparse.ArgumentParser(description="TemplateMill pipeline scheduler")
    parser.add_argument("--once", action="store_true", help="Run all jobs once and exit")
    args = parser.parse_args()

    if args.once:
        asyncio.run(run_all_once())
        return

    scheduler = create_scheduler()
    scheduler.start()
    logger.info("scheduler_started", jobs=len(scheduler.get_jobs()))

    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("scheduler_stopped")


if __name__ == "__main__":
    main()
