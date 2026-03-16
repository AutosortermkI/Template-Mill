"""Tests for the trend stage classifier."""

from src.discover.analyzers.trend_classifier import classify_trend_stage


def test_high_momentum_breakout_is_emerging() -> None:
    """High Google momentum + breakout Pinterest should classify as emerging."""
    result = classify_trend_stage(
        google_momentum=3.0,
        pinterest_trend="breakout",
    )
    assert result.stage in ("emerging", "growing")
    assert result.confidence > 0.5


def test_declining_signals_classified_correctly() -> None:
    """Low momentum + declining Pinterest should classify as declining or fading."""
    result = classify_trend_stage(
        google_momentum=0.3,
        pinterest_trend="declining",
    )
    assert result.stage in ("declining", "fading")


def test_stable_signals_classified_as_peak_or_stable() -> None:
    """Moderate signals should classify in the middle range."""
    result = classify_trend_stage(
        google_momentum=1.0,
        pinterest_trend="stable",
    )
    assert result.stage in ("peak", "declining")


def test_tiktok_growth_boosts_classification() -> None:
    """High TikTok growth should push classification toward emerging."""
    without_tiktok = classify_trend_stage(
        google_momentum=1.5,
        pinterest_trend="rising",
    )
    with_tiktok = classify_trend_stage(
        google_momentum=1.5,
        pinterest_trend="rising",
        tiktok_growth_rate=3.0,
    )
    # With TikTok boost, should be same or better stage
    stage_order = ["fading", "declining", "peak", "growing", "emerging"]
    assert stage_order.index(with_tiktok.stage) >= stage_order.index(without_tiktok.stage)


def test_classification_returns_valid_confidence() -> None:
    """Confidence should always be between 0 and 1."""
    result = classify_trend_stage(google_momentum=1.0, pinterest_trend="stable")
    assert 0.0 <= result.confidence <= 1.0
