"""Tests for distribute module models."""

from src.distribute.models import Listing, SEOData


def test_listing_defaults() -> None:
    """Listing should default to draft status."""
    listing = Listing(product_id=1, platform="etsy")
    assert listing.status == "draft"
    assert listing.views == 0
    assert listing.sales == 0


def test_seo_data_creation() -> None:
    """SEOData should hold all optimization fields."""
    seo = SEOData(
        title="Student Planner | Notion Template",
        tags=["planner", "notion", "student"],
        description="A comprehensive student planner.",
        platform="etsy",
    )
    assert len(seo.tags) == 3
    assert seo.platform == "etsy"
