"""Pydantic models for the Distribute module."""

from datetime import datetime

from pydantic import BaseModel, Field


class Listing(BaseModel):
    """A product listing on a specific platform."""

    id: int | None = None
    product_id: int
    platform: str  # 'etsy', 'gumroad', 'shopify', 'payhip'
    platform_listing_id: str = ""
    listing_url: str = ""

    # SEO
    title: str = ""
    tags: list[str] = Field(default_factory=list)
    description: str = ""

    # Performance
    views: int = 0
    favorites: int = 0
    sales: int = 0
    revenue: float = 0.0
    conversion_rate: float = 0.0
    avg_rating: float = 0.0
    review_count: int = 0

    # A/B testing
    variant_group: str = ""
    variant_label: str = ""

    status: str = "draft"  # draft, active, paused, retired

    created_at: datetime | None = None
    updated_at: datetime | None = None


class SEOData(BaseModel):
    """SEO-optimized content for a listing."""

    title: str
    tags: list[str] = Field(default_factory=list)
    description: str = ""
    platform: str = ""


class PlatformConstraints(BaseModel):
    """Platform-specific listing constraints."""

    max_title_length: int
    max_tags: int = 0
    max_tag_length: int = 0
    max_description_length: int = 0
    strategy: str = ""
