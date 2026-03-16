"""Initial schema — all core tables for the TemplateMill pipeline.

Revision ID: 001
Revises:
Create Date: 2026-03-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Discover module ──────────────────────────────────────────────

    op.create_table(
        "keywords",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("term", sa.String(255), nullable=False, unique=True),
        sa.Column("category", sa.String(100)),
        sa.Column("subcategory", sa.String(100)),
        sa.Column("is_seed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("discovered_from", sa.String(100)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_keywords_category", "keywords", ["category"])

    op.create_table(
        "demand_signals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "keyword_id",
            sa.Integer,
            sa.ForeignKey("keywords.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("captured_at", sa.Date, nullable=False),
        # Etsy
        sa.Column("etsy_search_volume", sa.Integer),
        sa.Column("etsy_competition", sa.Integer),
        sa.Column("etsy_avg_price", sa.Numeric(10, 2)),
        sa.Column("etsy_avg_reviews", sa.Numeric(10, 2)),
        sa.Column("etsy_top_seller_ids", postgresql.JSONB, server_default="[]"),
        # Pinterest
        sa.Column("pinterest_trend", sa.String(50)),
        sa.Column("pinterest_volume", sa.Integer),
        sa.Column("pinterest_save_rate", sa.Numeric(5, 4)),
        # TikTok
        sa.Column("tiktok_posts_7d", sa.Integer),
        sa.Column("tiktok_views_7d", sa.BigInteger),
        sa.Column("tiktok_keyword_tier", sa.String(50)),
        # Google
        sa.Column("google_interest", sa.Integer),
        sa.Column("google_momentum", sa.Numeric(6, 3)),
        sa.Column("google_related", postgresql.JSONB, server_default="[]"),
        # Raw payload
        sa.Column("raw_data", postgresql.JSONB),
    )
    op.create_index(
        "ix_demand_signals_keyword_date",
        "demand_signals",
        ["keyword_id", "captured_at"],
    )

    op.create_table(
        "opportunities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "keyword_id",
            sa.Integer,
            sa.ForeignKey("keywords.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("niche_label", sa.String(255), nullable=False),
        sa.Column(
            "opportunity_score", sa.Numeric(6, 2), nullable=False, server_default="0"
        ),
        sa.Column("revenue_potential", sa.Numeric(6, 2), server_default="0"),
        sa.Column("competition_score", sa.Numeric(6, 2), server_default="0"),
        sa.Column("trend_momentum", sa.Numeric(6, 2), server_default="0"),
        sa.Column("social_validation", sa.Numeric(6, 2), server_default="0"),
        sa.Column("competitor_gap", sa.Numeric(6, 2), server_default="0"),
        sa.Column("recommended_price", sa.Numeric(10, 2)),
        sa.Column("recommended_format", sa.String(50)),
        sa.Column(
            "recommended_platforms", postgresql.JSONB, server_default="[]"
        ),
        sa.Column("seasonal_peak", sa.String(50)),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="new",
        ),
        sa.Column("notes", sa.Text),
        sa.Column("gap_analysis", sa.Text),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_opportunities_score", "opportunities", ["opportunity_score"])
    op.create_index("ix_opportunities_status", "opportunities", ["status"])

    op.create_table(
        "competitor_shops",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("shop_name", sa.String(255), nullable=False),
        sa.Column("shop_url", sa.String(500)),
        sa.Column("platform_shop_id", sa.String(100)),
        sa.Column("niche_focus", sa.String(255)),
        sa.Column("tier", sa.String(50), server_default="mid"),
    )
    op.create_index(
        "ix_competitor_shops_platform_id",
        "competitor_shops",
        ["platform", "platform_shop_id"],
        unique=True,
    )

    op.create_table(
        "competitor_products",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "competitor_id",
            sa.Integer,
            sa.ForeignKey("competitor_shops.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform_listing_id", sa.String(100)),
        sa.Column("title", sa.String(500)),
        sa.Column("price", sa.Numeric(10, 2)),
        sa.Column("review_count", sa.Integer, server_default="0"),
        sa.Column("avg_rating", sa.Numeric(3, 2)),
        sa.Column("estimated_sales", sa.Integer),
        sa.Column("tags", postgresql.JSONB, server_default="[]"),
        sa.Column("captured_at", sa.Date),
        sa.Column("raw_data", postgresql.JSONB),
    )

    op.create_table(
        "review_insights",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "competitor_product_id",
            sa.Integer,
            sa.ForeignKey("competitor_products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sentiment", sa.String(50), server_default="neutral"),
        sa.Column("themes", postgresql.JSONB, server_default="[]"),
        sa.Column("feature_requests", postgresql.JSONB, server_default="[]"),
        sa.Column("pain_points", postgresql.JSONB, server_default="[]"),
        sa.Column(
            "analyzed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    # ── Build module ─────────────────────────────────────────────────

    op.create_table(
        "products",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "opportunity_id",
            sa.Integer,
            sa.ForeignKey("opportunities.id", ondelete="SET NULL"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, server_default=""),
        sa.Column("format", sa.String(50), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), server_default="0"),
        sa.Column("template_url", sa.String(500)),
        sa.Column("asset_blob_path", sa.String(500)),
        sa.Column("mockup_blob_paths", postgresql.JSONB, server_default="[]"),
        sa.Column("thumbnail_blob_path", sa.String(500)),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("quality_score", sa.Numeric(5, 2), server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_products_status", "products", ["status"])

    # ── Distribute module ────────────────────────────────────────────

    op.create_table(
        "listings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "product_id",
            sa.Integer,
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("platform_listing_id", sa.String(100)),
        sa.Column("listing_url", sa.String(500)),
        # SEO
        sa.Column("title", sa.String(500)),
        sa.Column("tags", postgresql.JSONB, server_default="[]"),
        sa.Column("description", sa.Text),
        # Performance
        sa.Column("views", sa.Integer, server_default="0"),
        sa.Column("favorites", sa.Integer, server_default="0"),
        sa.Column("sales", sa.Integer, server_default="0"),
        sa.Column("revenue", sa.Numeric(10, 2), server_default="0"),
        sa.Column("conversion_rate", sa.Numeric(7, 4), server_default="0"),
        sa.Column("avg_rating", sa.Numeric(3, 2), server_default="0"),
        sa.Column("review_count", sa.Integer, server_default="0"),
        # A/B testing
        sa.Column("variant_group", sa.String(100)),
        sa.Column("variant_label", sa.String(100)),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_listings_product_platform",
        "listings",
        ["product_id", "platform"],
    )
    op.create_index(
        "ix_listings_platform_id",
        "listings",
        ["platform", "platform_listing_id"],
        unique=True,
    )

    # ── Analyze module ───────────────────────────────────────────────

    op.create_table(
        "daily_stats",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "listing_id",
            sa.Integer,
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("views", sa.Integer, server_default="0"),
        sa.Column("favorites", sa.Integer, server_default="0"),
        sa.Column("orders", sa.Integer, server_default="0"),
        sa.Column("revenue", sa.Numeric(10, 2), server_default="0"),
        sa.Column("conversion_rate", sa.Numeric(7, 4), server_default="0"),
    )
    op.create_index(
        "ix_daily_stats_listing_date",
        "daily_stats",
        ["listing_id", "date"],
        unique=True,
    )

    op.create_table(
        "feedback_signals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "keyword_id",
            sa.Integer,
            sa.ForeignKey("keywords.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("predicted_score", sa.Numeric(6, 2), nullable=False),
        sa.Column("actual_performance", sa.Numeric(6, 2), nullable=False),
        sa.Column("accuracy", sa.Numeric(5, 3), nullable=False),
        sa.Column("adjustment_needed", sa.String(100), server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("feedback_signals")
    op.drop_table("daily_stats")
    op.drop_table("listings")
    op.drop_table("products")
    op.drop_table("review_insights")
    op.drop_table("competitor_products")
    op.drop_table("competitor_shops")
    op.drop_table("opportunities")
    op.drop_table("demand_signals")
    op.drop_table("keywords")
