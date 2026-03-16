"""Pydantic models for the Discover module."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class Keyword(BaseModel):
    """A keyword used to drive demand research."""

    id: int | None = None
    term: str
    category: str | None = None
    subcategory: str | None = None
    is_seed: bool = False
    discovered_from: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class EtsyListingData(BaseModel):
    """Data extracted from a single Etsy listing."""

    listing_id: str
    title: str
    price: float
    currency: str = "USD"
    review_count: int = 0
    star_rating: float = 0.0
    shop_name: str = ""
    num_favorers: int = 0
    tags: list[str] = Field(default_factory=list)
    thumbnail_url: str = ""


class DemandSignal(BaseModel):
    """Demand signal captured for a keyword on a specific platform."""

    keyword_id: int
    platform: str
    captured_at: date

    # Etsy-specific
    etsy_search_volume: int | None = None
    etsy_competition: int | None = None
    etsy_avg_price: float | None = None
    etsy_avg_reviews: float | None = None
    etsy_top_seller_ids: list[str] = Field(default_factory=list)

    # Pinterest-specific
    pinterest_trend: str | None = None
    pinterest_volume: int | None = None
    pinterest_save_rate: float | None = None

    # TikTok-specific
    tiktok_posts_7d: int | None = None
    tiktok_views_7d: int | None = None
    tiktok_keyword_tier: str | None = None

    # Google Trends
    google_interest: int | None = None
    google_momentum: float | None = None
    google_related: list[str] = Field(default_factory=list)

    raw_data: dict | None = None


class DemandSignalAggregate(BaseModel):
    """Aggregated demand signals across all platforms for scoring."""

    keyword_id: int
    keyword_term: str

    etsy_search_volume: int = 0
    etsy_competition: int = 0
    etsy_avg_price: float = 0.0
    etsy_avg_reviews: float = 0.0

    pinterest_trend: str = "stable"
    pinterest_volume: int = 0

    tiktok_posts_7d: int = 0
    tiktok_views_7d: int = 0

    google_interest: int = 0
    google_momentum: float = 1.0


class OpportunityScore(BaseModel):
    """Composite opportunity score with component breakdown."""

    total: float
    revenue_potential: float
    competition_difficulty: float
    trend_momentum: float
    social_validation: float


class Opportunity(BaseModel):
    """A scored opportunity ready for human review."""

    id: int | None = None
    keyword_id: int
    niche_label: str
    opportunity_score: float = 0.0

    revenue_potential: float = 0.0
    competition_score: float = 0.0
    trend_momentum: float = 0.0
    social_validation: float = 0.0
    competitor_gap: float = 0.0

    recommended_price: float | None = None
    recommended_format: str | None = None
    recommended_platforms: list[str] = Field(default_factory=list)
    seasonal_peak: str | None = None

    status: str = "new"
    notes: str | None = None
    gap_analysis: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None
    reviewed_at: datetime | None = None


class CompetitorShop(BaseModel):
    """A competitor shop being tracked."""

    id: int | None = None
    platform: str
    shop_name: str = ""
    shop_url: str = ""
    platform_shop_id: str = ""
    niche_focus: str = ""
    tier: str = "mid"


class CompetitorProduct(BaseModel):
    """A snapshot of a competitor's product."""

    id: int | None = None
    competitor_id: int
    platform_listing_id: str = ""
    title: str = ""
    price: float = 0.0
    review_count: int = 0
    avg_rating: float = 0.0
    estimated_sales: int | None = None
    tags: list[str] = Field(default_factory=list)
    captured_at: date | None = None
    raw_data: dict | None = None


class ReviewInsight(BaseModel):
    """Structured insights extracted from competitor reviews."""

    competitor_product_id: int
    sentiment: str = "neutral"
    themes: list[str] = Field(default_factory=list)
    feature_requests: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    analyzed_at: datetime | None = None
