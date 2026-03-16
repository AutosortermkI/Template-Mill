"""Automated weekly performance report generation."""

from datetime import date, datetime, timedelta

from src.analyze.models import WeeklyDigest
from src.shared.logger import get_logger

logger = get_logger("weekly_digest")


def generate_weekly_digest(
    current_stats: dict,
    previous_stats: dict,
    new_opportunities: list[dict] | None = None,
    competitor_movements: list[dict] | None = None,
) -> WeeklyDigest:
    """Generate a weekly performance summary.

    Args:
        current_stats: This week's aggregated stats.
        previous_stats: Last week's aggregated stats for comparison.
        new_opportunities: New high-scoring opportunities from discover module.
        competitor_movements: Notable competitor changes.

    Returns:
        WeeklyDigest with full summary.
    """
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    logger.info("generating_weekly_digest", week_start=str(week_start))

    current_revenue = current_stats.get("total_revenue", 0.0)
    previous_revenue = previous_stats.get("total_revenue", 0.0)
    current_sales = current_stats.get("total_sales", 0)
    previous_sales = previous_stats.get("total_sales", 0)

    revenue_change = (
        ((current_revenue - previous_revenue) / previous_revenue * 100)
        if previous_revenue > 0
        else 0.0
    )
    sales_change = (
        ((current_sales - previous_sales) / previous_sales * 100)
        if previous_sales > 0
        else 0.0
    )

    # Generate action items
    action_items: list[str] = []
    if revenue_change < -10:
        action_items.append("Revenue dropped >10% — review listing performance and pricing")
    if new_opportunities:
        action_items.append(f"{len(new_opportunities)} new opportunities flagged for review")
    if competitor_movements:
        action_items.append(f"{len(competitor_movements)} competitor movements detected")

    digest = WeeklyDigest(
        week_start=week_start,
        week_end=week_end,
        generated_at=datetime.now(),
        total_revenue=current_revenue,
        total_sales=current_sales,
        revenue_change_pct=round(revenue_change, 1),
        sales_change_pct=round(sales_change, 1),
        top_products=current_stats.get("top_products", []),
        underperformers=current_stats.get("underperformers", []),
        new_opportunities=new_opportunities or [],
        competitor_movements=competitor_movements or [],
        action_items=action_items,
    )

    logger.info(
        "weekly_digest_generated",
        revenue=digest.total_revenue,
        sales=digest.total_sales,
        action_items=len(digest.action_items),
    )

    return digest


def format_digest_html(digest: WeeklyDigest) -> str:
    """Format the weekly digest as an HTML email.

    Args:
        digest: The generated weekly digest.

    Returns:
        HTML string for email delivery.
    """
    top_products_html = ""
    for p in digest.top_products[:5]:
        top_products_html += f"<li>{p.get('name', 'Unknown')} — ${p.get('revenue', 0):.2f}</li>"

    action_items_html = ""
    for item in digest.action_items:
        action_items_html += f"<li>{item}</li>"

    return f"""
    <html>
    <body style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto;">
        <h1>TemplateMill Weekly Digest</h1>
        <p>{digest.week_start} — {digest.week_end}</p>

        <h2>Revenue: ${digest.total_revenue:.2f} ({digest.revenue_change_pct:+.1f}%)</h2>
        <p>Sales: {digest.total_sales} ({digest.sales_change_pct:+.1f}%)</p>

        <h3>Top Products</h3>
        <ul>{top_products_html or '<li>No sales data yet</li>'}</ul>

        <h3>Action Items</h3>
        <ul>{action_items_html or '<li>No actions needed</li>'}</ul>
    </body>
    </html>
    """
