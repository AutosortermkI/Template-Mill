"""Tests for the opportunity scoring model."""

from src.discover.analyzers.opportunity_scorer import score_opportunity
from src.discover.models import DemandSignalAggregate


def test_score_returns_valid_range(sample_demand_signals: DemandSignalAggregate) -> None:
    """Score should be between 0 and 100."""
    score = score_opportunity(sample_demand_signals)
    assert 0 <= score.total <= 100
    assert 0 <= score.revenue_potential <= 100
    assert 0 <= score.competition_difficulty <= 100
    assert 0 <= score.trend_momentum <= 100
    assert 0 <= score.social_validation <= 100


def test_high_opportunity_scores_above_threshold(high_opportunity_signals: DemandSignalAggregate) -> None:
    """A strong opportunity should score above the alert threshold."""
    score = score_opportunity(high_opportunity_signals)
    assert score.total >= 60  # Should be well above review threshold


def test_low_opportunity_scores_below_threshold(low_opportunity_signals: DemandSignalAggregate) -> None:
    """A saturated market should score low."""
    score = score_opportunity(low_opportunity_signals)
    assert score.total < 50


def test_high_scores_higher_than_low(
    high_opportunity_signals: DemandSignalAggregate,
    low_opportunity_signals: DemandSignalAggregate,
) -> None:
    """High opportunity should score significantly higher than low opportunity."""
    high_score = score_opportunity(high_opportunity_signals)
    low_score = score_opportunity(low_opportunity_signals)
    assert high_score.total > low_score.total


def test_zero_signals_returns_valid_score() -> None:
    """Zero values should not crash the scorer."""
    signals = DemandSignalAggregate(
        keyword_id=0,
        keyword_term="empty",
        etsy_search_volume=0,
        etsy_competition=0,
        etsy_avg_price=0.0,
        etsy_avg_reviews=0.0,
    )
    score = score_opportunity(signals)
    assert score.total >= 0


def test_breakout_trend_boosts_score() -> None:
    """A breakout Pinterest trend should significantly boost the trend component."""
    base = DemandSignalAggregate(
        keyword_id=1,
        keyword_term="test",
        etsy_search_volume=1000,
        etsy_competition=100,
        etsy_avg_price=20.0,
        etsy_avg_reviews=30.0,
        pinterest_trend="stable",
        google_momentum=1.0,
    )
    breakout = base.model_copy(update={"pinterest_trend": "breakout"})

    base_score = score_opportunity(base)
    breakout_score = score_opportunity(breakout)

    assert breakout_score.trend_momentum > base_score.trend_momentum


# ── Trends-only mode tests ─────────────────────────────────────────────────


def test_trends_only_differentiates_by_interest() -> None:
    """Without Etsy data, keywords with different interest levels should score differently."""
    high_interest = DemandSignalAggregate(
        keyword_id=0,
        keyword_term="popular keyword",
        google_interest=80,
        google_momentum=1.2,
    )
    low_interest = DemandSignalAggregate(
        keyword_id=0,
        keyword_term="obscure keyword",
        google_interest=10,
        google_momentum=0.5,
    )

    high_score = score_opportunity(high_interest)
    low_score = score_opportunity(low_interest)

    assert high_score.total > low_score.total
    assert high_score.total != low_score.total  # Must be different


def test_trends_only_differentiates_by_momentum() -> None:
    """Without Etsy data, rising keywords should score higher than declining ones."""
    rising = DemandSignalAggregate(
        keyword_id=0,
        keyword_term="rising keyword",
        google_interest=50,
        google_momentum=1.8,
    )
    declining = DemandSignalAggregate(
        keyword_id=0,
        keyword_term="declining keyword",
        google_interest=50,
        google_momentum=0.4,
    )

    rising_score = score_opportunity(rising)
    declining_score = score_opportunity(declining)

    assert rising_score.total > declining_score.total


def test_trends_only_zero_data_scores_low() -> None:
    """With no data at all, score should be low but valid."""
    signals = DemandSignalAggregate(
        keyword_id=0,
        keyword_term="no data",
        google_interest=0,
        google_momentum=0.0,
    )
    score = score_opportunity(signals)
    assert 0 <= score.total <= 100
    assert score.total < 20  # Should be low without any data


def test_trends_only_uses_different_weights_than_full() -> None:
    """Trends-only mode should use different scoring weights."""
    # Same keyword with Etsy data vs without
    with_etsy = DemandSignalAggregate(
        keyword_id=0,
        keyword_term="test",
        etsy_search_volume=1000,
        etsy_competition=100,
        etsy_avg_price=20.0,
        google_interest=50,
        google_momentum=1.0,
    )
    without_etsy = DemandSignalAggregate(
        keyword_id=0,
        keyword_term="test",
        google_interest=50,
        google_momentum=1.0,
    )

    full_score = score_opportunity(with_etsy)
    trends_score = score_opportunity(without_etsy)

    # Scores should differ because different weights are used
    assert full_score.total != trends_score.total
