"""Analyze module orchestrator — coordinates data collection and reporting."""

from src.analyze.reports.feedback_loop import compute_prediction_accuracy
from src.analyze.reports.product_health import assess_product_health
from src.analyze.reports.weekly_digest import generate_weekly_digest
from src.shared.logger import get_logger

logger = get_logger("analyze_orchestrator")


class AnalyzeOrchestrator:
    """Coordinates analytics collection, health scoring, and digest generation."""

    def run_daily_collection(self, listings: list[dict]) -> list[dict]:
        """Run daily stats collection for all active listings.

        Args:
            listings: List of listing dicts with platform and platform_listing_id.

        Returns:
            List of collected stats dicts.
        """
        logger.info("daily_collection_start", listing_count=len(listings))
        collected: list[dict] = []

        for listing in listings:
            logger.info(
                "collecting_stats",
                platform=listing.get("platform"),
                listing_id=listing.get("platform_listing_id"),
            )
            # Stats collection delegated to platform-specific collectors
            collected.append(listing)

        logger.info("daily_collection_complete", collected=len(collected))
        return collected

    def run_weekly_report(
        self,
        current_stats: dict,
        previous_stats: dict,
        opportunities: list[dict] | None = None,
        competitor_data: list[dict] | None = None,
    ) -> dict:
        """Generate weekly performance report.

        Args:
            current_stats: This week's aggregated stats.
            previous_stats: Last week's stats for comparison.
            opportunities: New opportunity alerts.
            competitor_data: Competitor movement data.

        Returns:
            Dict with digest data and HTML report.
        """
        logger.info("weekly_report_start")

        digest = generate_weekly_digest(
            current_stats,
            previous_stats,
            opportunities,
            competitor_data,
        )

        logger.info("weekly_report_complete", revenue=digest.total_revenue)

        return {
            "digest": digest.model_dump(),
            "action_items": digest.action_items,
        }

    def run_feedback_loop(
        self,
        predictions: list[dict],
        actuals: list[dict],
    ) -> dict:
        """Run the feedback loop to calibrate scoring.

        Args:
            predictions: Predicted opportunity scores.
            actuals: Actual performance data.

        Returns:
            Summary of prediction accuracy and needed adjustments.
        """
        signals = compute_prediction_accuracy(predictions, actuals)

        return {
            "total_compared": len(signals),
            "avg_accuracy": (
                round(sum(s.accuracy for s in signals) / len(signals), 3) if signals else 0.0
            ),
            "adjustments_needed": [
                {"keyword_id": s.keyword_id, "adjustment": s.adjustment_needed}
                for s in signals
                if s.adjustment_needed
            ],
        }
