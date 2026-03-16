"""Discover module orchestrator — coordinates scrapers and analyzers into workflows."""

from datetime import date

from src.discover.analyzers.opportunity_scorer import score_opportunity
from src.discover.models import DemandSignal, DemandSignalAggregate, Opportunity
from src.discover.scrapers.etsy_autocomplete import EtsyAutocompleteScraper
from src.discover.scrapers.etsy_listings import EtsyListingScraper
from src.discover.scrapers.google_trends import GoogleTrendsScraper
from src.shared.config import settings
from src.shared.logger import get_logger

logger = get_logger("discover_orchestrator")


class DiscoverOrchestrator:
    """Coordinates all discover scrapers and scoring into scheduled workflows."""

    def __init__(self) -> None:
        self.etsy_listings = EtsyListingScraper()
        self.google_trends = GoogleTrendsScraper()

    async def run_daily(self, keywords: list[dict]) -> list[Opportunity]:
        """Execute the daily demand scan workflow.

        1. Run Etsy listing scraper for top keywords.
        2. Run Google Trends momentum check.
        3. Re-score all active opportunities.

        Args:
            keywords: List of keyword dicts with 'id' and 'term' keys.

        Returns:
            List of scored Opportunity objects.
        """
        logger.info("daily_workflow_start", keyword_count=len(keywords))
        today = date.today()
        opportunities: list[Opportunity] = []

        # Step 1: Gather Etsy competition data
        etsy_signals: dict[int, dict] = {}
        for kw in keywords:
            try:
                stats = await self.etsy_listings.get_competition_stats(kw["term"])
                etsy_signals[kw["id"]] = stats
            except Exception as e:
                logger.error("etsy_scrape_failed", keyword=kw["term"], error=str(e))

        # Step 2: Gather Google Trends momentum
        terms = [kw["term"] for kw in keywords]
        try:
            momentum = await self.google_trends.get_momentum(terms)
        except Exception as e:
            logger.error("google_trends_failed", error=str(e))
            momentum = {}

        # Step 3: Score opportunities
        for kw in keywords:
            etsy = etsy_signals.get(kw["id"], {})
            google_mom = momentum.get(kw["term"], 1.0)

            aggregate = DemandSignalAggregate(
                keyword_id=kw["id"],
                keyword_term=kw["term"],
                etsy_search_volume=etsy.get("listing_count", 0) * 10,  # rough estimate
                etsy_competition=etsy.get("listing_count", 0),
                etsy_avg_price=etsy.get("avg_price", 0.0),
                etsy_avg_reviews=etsy.get("avg_reviews", 0.0),
                google_momentum=google_mom,
            )

            score = score_opportunity(aggregate)

            opportunity = Opportunity(
                keyword_id=kw["id"],
                niche_label=kw["term"],
                opportunity_score=score.total,
                revenue_potential=score.revenue_potential,
                competition_score=score.competition_difficulty,
                trend_momentum=score.trend_momentum,
                social_validation=score.social_validation,
            )

            # Auto-flag based on threshold
            if score.total >= settings.OPPORTUNITY_ALERT_THRESHOLD:
                opportunity.status = "flagged"
                logger.info("high_score_opportunity", keyword=kw["term"], score=score.total)

            opportunities.append(opportunity)

        logger.info("daily_workflow_complete", opportunities=len(opportunities))
        return opportunities

    async def run_weekly_expansion(self, seed_keywords: list[str]) -> list[str]:
        """Execute the weekly keyword expansion workflow.

        1. Run Etsy autocomplete expansion from seed keywords.
        2. Deduplicate discovered terms.

        Args:
            seed_keywords: List of seed keyword strings.

        Returns:
            List of newly discovered keyword strings.
        """
        logger.info("weekly_expansion_start", seed_count=len(seed_keywords))

        all_discovered: list[str] = []

        async with EtsyAutocompleteScraper() as scraper:
            results = await scraper.expand_all(seed_keywords)
            for seed, suggestions in results.items():
                all_discovered.extend(suggestions)
                logger.info("seed_expanded", seed=seed, new_terms=len(suggestions))

        deduplicated = list(set(all_discovered))
        logger.info("weekly_expansion_complete", total_discovered=len(deduplicated))
        return deduplicated

    async def close(self) -> None:
        """Clean up resources."""
        await self.etsy_listings.close()
