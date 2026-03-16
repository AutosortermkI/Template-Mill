"""Per-product performance scoring and health assessment."""

from src.analyze.models import ProductHealth
from src.shared.logger import get_logger

logger = get_logger("product_health")


def assess_product_health(
    product_id: int,
    product_name: str,
    stats: dict,
) -> ProductHealth:
    """Assess the health of a product based on its performance metrics.

    Args:
        product_id: Product ID.
        product_name: Product name.
        stats: Dict with keys: total_revenue, total_sales, avg_daily_views,
               conversion_rate, revenue_trend (list of last 4 weeks).

    Returns:
        ProductHealth with score and recommendations.
    """
    logger.info("assessing_product_health", product_id=product_id)

    total_revenue = stats.get("total_revenue", 0.0)
    total_sales = stats.get("total_sales", 0)
    avg_views = stats.get("avg_daily_views", 0.0)
    conversion = stats.get("conversion_rate", 0.0)
    revenue_trend = stats.get("revenue_trend", [])

    # Calculate health score (0-100)
    score = 0.0

    # Revenue component (40 points max)
    if total_revenue >= 500:
        score += 40
    elif total_revenue >= 100:
        score += 25
    elif total_revenue >= 20:
        score += 10

    # Conversion component (30 points max)
    if conversion >= 0.05:
        score += 30
    elif conversion >= 0.02:
        score += 20
    elif conversion >= 0.01:
        score += 10

    # Traffic component (20 points max)
    if avg_views >= 50:
        score += 20
    elif avg_views >= 20:
        score += 12
    elif avg_views >= 5:
        score += 5

    # Trend component (10 points max)
    trend_direction = "stable"
    if len(revenue_trend) >= 2:
        recent = sum(revenue_trend[-2:]) / 2
        earlier = sum(revenue_trend[:2]) / max(len(revenue_trend[:2]), 1)
        if earlier > 0:
            trend_ratio = recent / earlier
            if trend_ratio >= 1.2:
                trend_direction = "improving"
                score += 10
            elif trend_ratio <= 0.8:
                trend_direction = "declining"
            else:
                score += 5

    # Generate recommendations
    recommendations: list[str] = []
    if avg_views < 10:
        recommendations.append("Low traffic — consider Pinterest promotion or SEO title update")
    if conversion < 0.01 and avg_views >= 10:
        recommendations.append("Low conversion — review listing images and description")
    if trend_direction == "declining":
        recommendations.append("Revenue declining — consider price adjustment or seasonal refresh")
    if total_sales > 10 and conversion >= 0.03:
        recommendations.append("Strong performer — consider creating variations or bundles")

    health = ProductHealth(
        product_id=product_id,
        product_name=product_name,
        health_score=round(score, 1),
        total_revenue=total_revenue,
        total_sales=total_sales,
        avg_daily_views=avg_views,
        conversion_rate=conversion,
        trend_direction=trend_direction,
        recommendations=recommendations,
    )

    logger.info("product_health_assessed", product_id=product_id, score=health.health_score)
    return health
