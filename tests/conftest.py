"""Shared test fixtures for TemplateMill."""

import pytest

from src.discover.models import DemandSignalAggregate


@pytest.fixture
def sample_demand_signals() -> DemandSignalAggregate:
    """Sample demand signals for testing the opportunity scorer."""
    return DemandSignalAggregate(
        keyword_id=1,
        keyword_term="student planner",
        etsy_search_volume=5000,
        etsy_competition=200,
        etsy_avg_price=15.0,
        etsy_avg_reviews=50.0,
        pinterest_trend="rising",
        pinterest_volume=8000,
        tiktok_posts_7d=1500,
        tiktok_views_7d=500000,
        google_interest=75,
        google_momentum=1.5,
    )


@pytest.fixture
def high_opportunity_signals() -> DemandSignalAggregate:
    """High-scoring opportunity signals."""
    return DemandSignalAggregate(
        keyword_id=2,
        keyword_term="adhd daily planner",
        etsy_search_volume=8000,
        etsy_competition=50,
        etsy_avg_price=25.0,
        etsy_avg_reviews=10.0,
        pinterest_trend="breakout",
        pinterest_volume=15000,
        tiktok_posts_7d=3000,
        tiktok_views_7d=2000000,
        google_interest=90,
        google_momentum=2.5,
    )


@pytest.fixture
def low_opportunity_signals() -> DemandSignalAggregate:
    """Low-scoring opportunity signals (saturated market)."""
    return DemandSignalAggregate(
        keyword_id=3,
        keyword_term="basic to-do list",
        etsy_search_volume=500,
        etsy_competition=450,
        etsy_avg_price=5.0,
        etsy_avg_reviews=200.0,
        pinterest_trend="declining",
        pinterest_volume=200,
        tiktok_posts_7d=50,
        tiktok_views_7d=10000,
        google_interest=20,
        google_momentum=0.5,
    )
