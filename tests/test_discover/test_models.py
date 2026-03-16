"""Tests for discover module Pydantic models."""

from src.discover.models import (
    DemandSignal,
    DemandSignalAggregate,
    EtsyListingData,
    Keyword,
    Opportunity,
)


def test_keyword_defaults() -> None:
    """Keyword should have sensible defaults."""
    kw = Keyword(term="test keyword")
    assert kw.is_seed is False
    assert kw.category is None
    assert kw.id is None


def test_etsy_listing_data_creation() -> None:
    """EtsyListingData should parse correctly."""
    listing = EtsyListingData(
        listing_id="123456",
        title="Student Planner | Notion Template",
        price=19.99,
    )
    assert listing.listing_id == "123456"
    assert listing.price == 19.99
    assert listing.review_count == 0


def test_demand_signal_aggregate_defaults() -> None:
    """Aggregate should have safe defaults for scoring."""
    agg = DemandSignalAggregate(keyword_id=1, keyword_term="test")
    assert agg.etsy_search_volume == 0
    assert agg.google_momentum == 1.0
    assert agg.pinterest_trend == "stable"


def test_opportunity_defaults() -> None:
    """Opportunity should default to 'new' status."""
    opp = Opportunity(keyword_id=1, niche_label="test niche")
    assert opp.status == "new"
    assert opp.opportunity_score == 0.0
