"""Discover module orchestrator — coordinates scrapers and analyzers into workflows."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from src.discover.analyzers.opportunity_scorer import score_opportunity
from src.discover.models import DemandSignalAggregate, Opportunity
from src.discover.repository import (
    insert_demand_signal,
    insert_keywords,
    load_keywords,
    load_seed_terms,
    save_opportunities,
)
from src.discover.scrapers.etsy_autocomplete import EtsyAutocompleteScraper
from src.discover.scrapers.etsy_listings import EtsyListingScraper
from src.discover.scrapers.google_trends import GoogleTrendsScraper
from src.shared.config import settings
from src.shared.logger import get_logger

logger = get_logger("discover_orchestrator")


class DiscoverOrchestrator:
    """Coordinates all discover scrapers and scoring into scheduled workflows."""

    def __init__(self, session: Session | None = None) -> None:
        self.etsy_listings = EtsyListingScraper()
        self.google_trends = GoogleTrendsScraper()
        self._session = session

    async def run_daily(self, keywords: list[dict] | None = None) -> list[Opportunity]:
        """Execute the daily demand scan workflow.

        1. Load keywords from DB (or use provided list).
        2. Run Etsy listing scraper for each keyword.
        3. Run Google Trends momentum check.
        4. Score opportunities and persist to DB.

        Args:
            keywords: Optional list of keyword dicts with 'id' and 'term'.
                      If None, loads all keywords from the database.

        Returns:
            List of scored Opportunity objects.
        """
        if keywords is None:
            keywords = load_keywords(session=self._session)

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

        # Step 3: Score opportunities and persist signals
        for kw in keywords:
            etsy = etsy_signals.get(kw["id"], {})
            google_mom = momentum.get(kw["term"], 1.0)

            search_volume = etsy.get("listing_count", 0) * 10
            competition = etsy.get("listing_count", 0)
            avg_price = etsy.get("avg_price", 0.0)
            avg_reviews = etsy.get("avg_reviews", 0.0)

            aggregate = DemandSignalAggregate(
                keyword_id=kw["id"],
                keyword_term=kw["term"],
                etsy_search_volume=search_volume,
                etsy_competition=competition,
                etsy_avg_price=avg_price,
                etsy_avg_reviews=avg_reviews,
                google_momentum=google_mom,
            )

            # Persist the raw demand signal
            try:
                insert_demand_signal(
                    keyword_id=kw["id"],
                    platform="etsy+google",
                    captured_at=today,
                    data={
                        "etsy_search_volume": search_volume,
                        "etsy_competition": competition,
                        "etsy_avg_price": avg_price,
                        "etsy_avg_reviews": avg_reviews,
                        "google_momentum": google_mom,
                    },
                    session=self._session,
                )
            except Exception as e:
                logger.error("signal_persist_failed", keyword=kw["term"], error=str(e))

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

        # Step 4: Persist all opportunities
        try:
            save_opportunities(opportunities, session=self._session)
        except Exception as e:
            logger.error("opportunities_persist_failed", error=str(e))

        logger.info("daily_workflow_complete", opportunities=len(opportunities))
        return opportunities

    async def run_weekly_expansion(self, seed_keywords: list[str] | None = None) -> list[str]:
        """Execute the weekly keyword expansion workflow.

        1. Load seed keywords from DB (or use provided list).
        2. Run Etsy autocomplete expansion.
        3. Deduplicate and persist new keywords to DB.

        Args:
            seed_keywords: Optional list of seed keyword strings.
                           If None, loads seed keywords from the database.

        Returns:
            List of newly discovered keyword strings.
        """
        if seed_keywords is None:
            seed_keywords = load_seed_terms(session=self._session)

        logger.info("weekly_expansion_start", seed_count=len(seed_keywords))

        all_discovered: list[str] = []

        async with EtsyAutocompleteScraper() as scraper:
            results = await scraper.expand_all(seed_keywords)
            for seed, suggestions in results.items():
                all_discovered.extend(suggestions)
                logger.info("seed_expanded", seed=seed, new_terms=len(suggestions))

        deduplicated = list(set(all_discovered))

        # Persist newly discovered keywords
        try:
            inserted = insert_keywords(
                deduplicated,
                discovered_from="etsy_autocomplete",
                session=self._session,
            )
            logger.info("new_keywords_persisted", inserted=inserted, total_discovered=len(deduplicated))
        except Exception as e:
            logger.error("keyword_persist_failed", error=str(e))

        logger.info("weekly_expansion_complete", total_discovered=len(deduplicated))
        return deduplicated

    async def close(self) -> None:
        """Clean up resources."""
        await self.etsy_listings.close()
