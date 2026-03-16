"""NLP analysis of competitor reviews using Claude LLM."""

from src.discover.models import ReviewInsight
from src.shared.llm import generate_json
from src.shared.logger import get_logger

logger = get_logger("review_analyzer")

REVIEW_ANALYSIS_PROMPT = """Analyze these product reviews for a {product_type} template.
Extract structured insights:

Reviews:
{reviews_text}

Respond in JSON:
{{
  "pain_points": ["specific complaints about the product"],
  "feature_requests": ["things reviewers wish the product had"],
  "praise_themes": ["what reviewers loved"],
  "quality_gaps": ["opportunities to build something better"],
  "suggested_improvements": ["concrete product features that would address the complaints"]
}}"""


def analyze_reviews(
    reviews: list[str],
    product_type: str,
    competitor_product_id: int,
) -> ReviewInsight:
    """Analyze competitor reviews to extract actionable insights.

    Args:
        reviews: List of review text strings (typically 1-3 star reviews).
        product_type: Type of template product (e.g., "daily planner", "budget tracker").
        competitor_product_id: ID of the competitor product these reviews belong to.

    Returns:
        ReviewInsight with extracted themes, pain points, and feature requests.
    """
    logger.info(
        "analyzing_reviews",
        product_type=product_type,
        review_count=len(reviews),
        competitor_product_id=competitor_product_id,
    )

    reviews_text = "\n---\n".join(reviews)
    prompt = REVIEW_ANALYSIS_PROMPT.format(
        product_type=product_type,
        reviews_text=reviews_text,
    )

    result = generate_json(prompt)

    insight = ReviewInsight(
        competitor_product_id=competitor_product_id,
        sentiment="negative",  # analyzing low-star reviews
        themes=result.get("praise_themes", []),
        feature_requests=result.get("feature_requests", []),
        pain_points=result.get("pain_points", []),
    )

    logger.info(
        "reviews_analyzed",
        pain_points=len(insight.pain_points),
        feature_requests=len(insight.feature_requests),
    )

    return insight
