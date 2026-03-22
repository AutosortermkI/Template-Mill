"""Composite demand scoring model for opportunity evaluation."""

from src.discover.models import DemandSignalAggregate, OpportunityScore
from src.shared.logger import get_logger

logger = get_logger("opportunity_scorer")

TREND_STAGE_MAP = {
    "breakout": 1.0,
    "rising": 0.75,
    "stable": 0.4,
    "declining": 0.1,
}

# Scoring weights — full data (Etsy + social available)
WEIGHT_REVENUE = 0.40
WEIGHT_COMPETITION = 0.30
WEIGHT_TREND = 0.20
WEIGHT_SOCIAL = 0.10

# Scoring weights — trends-only mode (no Etsy/social data)
WEIGHT_TREND_ONLY_INTEREST = 0.45
WEIGHT_TREND_ONLY_MOMENTUM = 0.35
WEIGHT_TREND_ONLY_PINTEREST = 0.20


def _has_etsy_data(signals: DemandSignalAggregate) -> bool:
    """Check if Etsy data is present (non-default values)."""
    return signals.etsy_search_volume > 0 or signals.etsy_competition > 0


def score_opportunity(signals: DemandSignalAggregate) -> OpportunityScore:
    """Compute composite opportunity score from aggregated demand signals.

    When Etsy data is available, uses the full scoring model:
    - Revenue potential (40%): search volume x average price, normalized.
    - Competition difficulty (30%): inversely proportional to listing count x review moat.
    - Trend momentum (20%): cross-platform Pinterest + Google signal.
    - Social validation (10%): TikTok activity level.

    When only Google Trends data is available, shifts to trends-focused scoring:
    - Interest level (45%): how popular the keyword is (Google Trends average).
    - Momentum (35%): whether interest is rising or falling.
    - Pinterest signal (20%): cross-platform trend stage.

    Args:
        signals: Aggregated demand signals across all platforms.

    Returns:
        OpportunityScore with total and component breakdown (0-100 scale).
    """
    if _has_etsy_data(signals):
        return _score_full(signals)
    return _score_trends_only(signals)


def _score_full(signals: DemandSignalAggregate) -> OpportunityScore:
    """Full scoring model with Etsy + social data."""
    # Revenue potential: search volume × average price, normalized to 0-1
    revenue = min((signals.etsy_search_volume * signals.etsy_avg_price) / 50000, 1.0)

    # Competition: inversely proportional to listing count × review moat
    comp_raw = (signals.etsy_competition / 500) * (signals.etsy_avg_reviews / 100)
    competition = 1.0 - min(comp_raw, 1.0)

    # Trend momentum: cross-platform signal
    pinterest_signal = TREND_STAGE_MAP.get(signals.pinterest_trend, 0.3)
    google_signal = min(signals.google_momentum / 2.0, 1.0)
    trend = (pinterest_signal * 0.6) + (google_signal * 0.4)

    # Social validation: TikTok activity
    social = min(signals.tiktok_posts_7d / 3000, 1.0)

    total = (
        (revenue * WEIGHT_REVENUE)
        + (competition * WEIGHT_COMPETITION)
        + (trend * WEIGHT_TREND)
        + (social * WEIGHT_SOCIAL)
    )

    score = OpportunityScore(
        total=round(total * 100, 2),
        revenue_potential=round(revenue * 100, 2),
        competition_difficulty=round(competition * 100, 2),
        trend_momentum=round(trend * 100, 2),
        social_validation=round(social * 100, 2),
    )

    logger.info(
        "opportunity_scored",
        keyword=signals.keyword_term,
        total=score.total,
        revenue=score.revenue_potential,
        competition=score.competition_difficulty,
        trend=score.trend_momentum,
        social=score.social_validation,
    )

    return score


def _score_trends_only(signals: DemandSignalAggregate) -> OpportunityScore:
    """Trends-focused scoring when only Google Trends data is available.

    Uses interest level and momentum as the primary differentiators.
    """
    # Interest level: google_interest is 0-100
    interest = min(signals.google_interest / 100.0, 1.0)

    # Momentum: >1 = rising, <1 = declining, 0 = no data
    # Scale so 1.0 (flat) = 0.5, 2.0+ (strong growth) = 1.0, 0 (no data) = 0
    momentum = min(signals.google_momentum / 2.0, 1.0)

    # Pinterest cross-platform signal
    pinterest_signal = TREND_STAGE_MAP.get(signals.pinterest_trend, 0.3)

    total = (
        (interest * WEIGHT_TREND_ONLY_INTEREST)
        + (momentum * WEIGHT_TREND_ONLY_MOMENTUM)
        + (pinterest_signal * WEIGHT_TREND_ONLY_PINTEREST)
    )

    score = OpportunityScore(
        total=round(total * 100, 2),
        revenue_potential=round(interest * 100, 2),
        competition_difficulty=0.0,  # Unknown without Etsy
        trend_momentum=round(momentum * 100, 2),
        social_validation=round(pinterest_signal * 100, 2),
    )

    logger.info(
        "opportunity_scored",
        keyword=signals.keyword_term,
        mode="trends_only",
        total=score.total,
        interest=score.revenue_potential,
        momentum=score.trend_momentum,
        pinterest=score.social_validation,
    )

    return score
