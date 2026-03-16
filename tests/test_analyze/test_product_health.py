"""Tests for product health assessment."""

from src.analyze.reports.product_health import assess_product_health


def test_high_performer_gets_high_score() -> None:
    """A product with strong metrics should score well."""
    health = assess_product_health(
        product_id=1,
        product_name="Best Seller",
        stats={
            "total_revenue": 600.0,
            "total_sales": 40,
            "avg_daily_views": 60.0,
            "conversion_rate": 0.06,
            "revenue_trend": [100, 120, 150, 180],
        },
    )
    assert health.health_score >= 80
    assert health.trend_direction == "improving"


def test_low_performer_gets_recommendations() -> None:
    """A product with low traffic should get SEO recommendations."""
    health = assess_product_health(
        product_id=2,
        product_name="Underperformer",
        stats={
            "total_revenue": 5.0,
            "total_sales": 1,
            "avg_daily_views": 3.0,
            "conversion_rate": 0.005,
        },
    )
    assert health.health_score < 30
    assert any("traffic" in r.lower() for r in health.recommendations)


def test_zero_stats_returns_valid_health() -> None:
    """Zero stats should not crash the assessor."""
    health = assess_product_health(
        product_id=3,
        product_name="New Product",
        stats={},
    )
    assert health.health_score >= 0
    assert health.trend_direction == "stable"
