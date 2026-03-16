"""Pydantic models for the Analyze module."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class DailyStats(BaseModel):
    """Daily performance stats for a listing."""

    listing_id: int
    platform: str
    date: date
    views: int = 0
    favorites: int = 0
    orders: int = 0
    revenue: float = 0.0
    conversion_rate: float = 0.0


class ProductHealth(BaseModel):
    """Performance health score for a product."""

    product_id: int
    product_name: str
    health_score: float = 0.0  # 0-100
    total_revenue: float = 0.0
    total_sales: int = 0
    avg_daily_views: float = 0.0
    conversion_rate: float = 0.0
    trend_direction: str = "stable"  # improving, stable, declining
    recommendations: list[str] = Field(default_factory=list)


class WeeklyDigest(BaseModel):
    """Weekly performance summary report."""

    week_start: date
    week_end: date
    generated_at: datetime | None = None

    total_revenue: float = 0.0
    total_sales: int = 0
    revenue_change_pct: float = 0.0
    sales_change_pct: float = 0.0

    top_products: list[dict] = Field(default_factory=list)
    underperformers: list[dict] = Field(default_factory=list)
    new_opportunities: list[dict] = Field(default_factory=list)
    competitor_movements: list[dict] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)


class FeedbackSignal(BaseModel):
    """Signal from performance data fed back to the discover module."""

    keyword_id: int
    predicted_score: float
    actual_performance: float  # normalized sales metric
    accuracy: float  # how close prediction was
    adjustment_needed: str = ""  # which scoring component to adjust
