"""Database repository for the Discover module — keyword, signal, and opportunity CRUD."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.discover.models import DemandSignalAggregate, Opportunity
from src.shared.database import get_session
from src.shared.logger import get_logger

logger = get_logger("discover_repository")


def load_keywords(session: Session | None = None, seed_only: bool = False) -> list[dict]:
    """Return keyword rows as dicts with 'id' and 'term' keys.

    Args:
        session: Optional SQLAlchemy session (created if not provided).
        seed_only: If True, only return seed keywords.
    """
    s = session or get_session()
    try:
        query = "SELECT id, term, category, subcategory, is_seed FROM keywords"
        if seed_only:
            query += " WHERE is_seed = TRUE"
        query += " ORDER BY id"
        rows = s.execute(text(query)).mappings().all()
        return [dict(r) for r in rows]
    finally:
        if session is None:
            s.close()


def load_seed_terms(session: Session | None = None) -> list[str]:
    """Return just the term strings for seed keywords."""
    keywords = load_keywords(session=session, seed_only=True)
    return [kw["term"] for kw in keywords]


def insert_keywords(terms: list[str], discovered_from: str, session: Session | None = None) -> int:
    """Insert new keywords, skipping duplicates. Returns count of inserted rows."""
    s = session or get_session()
    inserted = 0
    try:
        for term in terms:
            result = s.execute(
                text(
                    """
                    INSERT INTO keywords (term, discovered_from)
                    VALUES (:term, :discovered_from)
                    ON CONFLICT (term) DO NOTHING
                    """
                ),
                {"term": term, "discovered_from": discovered_from},
            )
            inserted += result.rowcount
        s.commit()
        logger.info("keywords_inserted", count=inserted, source=discovered_from)
        return inserted
    except Exception:
        s.rollback()
        raise
    finally:
        if session is None:
            s.close()


def upsert_opportunity(opportunity: Opportunity, session: Session | None = None) -> int:
    """Insert or update an opportunity by keyword_id. Returns the opportunity id."""
    s = session or get_session()
    try:
        row = s.execute(
            text(
                """
                INSERT INTO opportunities (
                    keyword_id, niche_label, opportunity_score,
                    revenue_potential, competition_score, trend_momentum,
                    social_validation, competitor_gap,
                    recommended_price, recommended_format, status
                ) VALUES (
                    :keyword_id, :niche_label, :opportunity_score,
                    :revenue_potential, :competition_score, :trend_momentum,
                    :social_validation, :competitor_gap,
                    :recommended_price, :recommended_format, :status
                )
                ON CONFLICT (keyword_id) DO UPDATE SET
                    niche_label = EXCLUDED.niche_label,
                    opportunity_score = EXCLUDED.opportunity_score,
                    revenue_potential = EXCLUDED.revenue_potential,
                    competition_score = EXCLUDED.competition_score,
                    trend_momentum = EXCLUDED.trend_momentum,
                    social_validation = EXCLUDED.social_validation,
                    competitor_gap = EXCLUDED.competitor_gap,
                    recommended_price = EXCLUDED.recommended_price,
                    recommended_format = EXCLUDED.recommended_format,
                    status = EXCLUDED.status,
                    updated_at = :updated_at
                RETURNING id
                """
            ),
            {
                "keyword_id": opportunity.keyword_id,
                "niche_label": opportunity.niche_label,
                "opportunity_score": opportunity.opportunity_score,
                "revenue_potential": opportunity.revenue_potential,
                "competition_score": opportunity.competition_score,
                "trend_momentum": opportunity.trend_momentum,
                "social_validation": opportunity.social_validation,
                "competitor_gap": opportunity.competitor_gap,
                "recommended_price": opportunity.recommended_price,
                "recommended_format": opportunity.recommended_format,
                "status": opportunity.status,
                "updated_at": datetime.utcnow(),
            },
        )
        result = row.fetchone()
        s.commit()
        return result[0] if result else 0
    except Exception:
        s.rollback()
        raise
    finally:
        if session is None:
            s.close()


def save_opportunities(opportunities: list[Opportunity], session: Session | None = None) -> int:
    """Batch-upsert a list of opportunities. Returns count saved."""
    s = session or get_session()
    count = 0
    try:
        for opp in opportunities:
            upsert_opportunity(opp, session=s)
            count += 1
        logger.info("opportunities_saved", count=count)
        return count
    finally:
        if session is None:
            s.close()


def insert_demand_signal(
    keyword_id: int,
    platform: str,
    captured_at: date,
    data: dict,
    session: Session | None = None,
) -> int:
    """Insert a demand signal row. Returns the new row id."""
    s = session or get_session()
    try:
        row = s.execute(
            text(
                """
                INSERT INTO demand_signals (
                    keyword_id, platform, captured_at,
                    etsy_search_volume, etsy_competition, etsy_avg_price, etsy_avg_reviews,
                    google_interest, google_momentum
                ) VALUES (
                    :keyword_id, :platform, :captured_at,
                    :etsy_search_volume, :etsy_competition, :etsy_avg_price, :etsy_avg_reviews,
                    :google_interest, :google_momentum
                )
                RETURNING id
                """
            ),
            {
                "keyword_id": keyword_id,
                "platform": platform,
                "captured_at": captured_at,
                "etsy_search_volume": data.get("etsy_search_volume"),
                "etsy_competition": data.get("etsy_competition"),
                "etsy_avg_price": data.get("etsy_avg_price"),
                "etsy_avg_reviews": data.get("etsy_avg_reviews"),
                "google_interest": data.get("google_interest"),
                "google_momentum": data.get("google_momentum"),
            },
        )
        result = row.fetchone()
        s.commit()
        return result[0] if result else 0
    except Exception:
        s.rollback()
        raise
    finally:
        if session is None:
            s.close()
