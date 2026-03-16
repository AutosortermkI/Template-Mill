"""Classify trend stage using lightweight signal analysis."""

from dataclasses import dataclass

from src.shared.logger import get_logger

logger = get_logger("trend_classifier")


@dataclass
class TrendClassification:
    """Result of trend stage classification."""

    stage: str  # 'emerging', 'growing', 'peak', 'declining', 'fading'
    confidence: float  # 0.0 to 1.0
    signals: dict  # evidence supporting the classification


def classify_trend_stage(
    google_momentum: float,
    pinterest_trend: str,
    tiktok_growth_rate: float | None = None,
    historical_interest: list[float] | None = None,
) -> TrendClassification:
    """Classify a keyword's trend stage based on multi-platform signals.

    Args:
        google_momentum: Google Trends momentum ratio (recent / historical average).
        pinterest_trend: Pinterest trend classification string.
        tiktok_growth_rate: Optional TikTok post growth rate (7d over 7d).
        historical_interest: Optional list of historical Google interest values.

    Returns:
        TrendClassification with stage, confidence, and supporting signals.
    """
    signals: dict = {
        "google_momentum": google_momentum,
        "pinterest_trend": pinterest_trend,
    }

    score = 0.0

    # Google momentum scoring
    if google_momentum >= 2.5:
        score += 2.0
    elif google_momentum >= 1.5:
        score += 1.5
    elif google_momentum >= 1.0:
        score += 0.8
    elif google_momentum >= 0.5:
        score += 0.0
    else:
        score -= 1.0

    # Pinterest trend scoring
    pinterest_scores = {
        "breakout": 2.0,
        "rising": 1.5,
        "stable": 0.0,
        "declining": -1.0,
    }
    score += pinterest_scores.get(pinterest_trend, 0.0)

    # TikTok growth rate
    if tiktok_growth_rate is not None:
        signals["tiktok_growth_rate"] = tiktok_growth_rate
        if tiktok_growth_rate >= 2.0:
            score += 1.0
        elif tiktok_growth_rate >= 1.2:
            score += 0.5

    # Classify based on composite score
    if score >= 3.5:
        stage = "emerging"
        confidence = min(score / 5.0, 1.0)
    elif score >= 2.0:
        stage = "growing"
        confidence = 0.7
    elif score >= 0.5:
        stage = "peak"
        confidence = 0.6
    elif score >= -0.5:
        stage = "declining"
        confidence = 0.6
    else:
        stage = "fading"
        confidence = min(abs(score) / 3.0, 1.0)

    result = TrendClassification(stage=stage, confidence=round(confidence, 2), signals=signals)

    logger.info("trend_classified", stage=result.stage, confidence=result.confidence)
    return result
