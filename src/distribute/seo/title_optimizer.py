"""A/B title generation and optimization per platform constraints."""

from src.distribute.models import SEOData
from src.shared.llm import generate_json
from src.shared.logger import get_logger

logger = get_logger("title_optimizer")

PLATFORM_CONSTRAINTS = {
    "etsy": {
        "max_length": 140,
        "strategy": "front-load primary keyword, include 2-3 secondary keywords",
        "separator": " | ",
    },
    "gumroad": {
        "max_length": 200,
        "strategy": "benefit-driven, can be longer and more descriptive",
        "separator": " — ",
    },
    "shopify": {
        "max_length": 255,
        "strategy": "SEO-optimized for Google, include primary keyword early",
        "separator": " — ",
    },
    "pinterest": {
        "max_length": 100,
        "strategy": "action-oriented, visual language",
        "separator": " ",
    },
}

TITLE_GENERATION_PROMPT = """Generate optimized listing titles for a digital template product.

Product: {product_name}
Primary keyword: {primary_keyword}
Secondary keywords: {secondary_keywords}
Platform: {platform}
Max length: {max_length} characters
Strategy: {strategy}

Generate 3 title variants for A/B testing. Each must be under {max_length} characters.

Respond in JSON:
{{
  "titles": [
    {{"title": "...", "primary_keyword_position": 0, "character_count": 0}},
    {{"title": "...", "primary_keyword_position": 0, "character_count": 0}},
    {{"title": "...", "primary_keyword_position": 0, "character_count": 0}}
  ]
}}"""


def generate_titles(
    product_name: str,
    primary_keyword: str,
    secondary_keywords: list[str],
    platform: str,
) -> list[str]:
    """Generate optimized listing titles for a specific platform.

    Args:
        product_name: The product name.
        primary_keyword: Main search keyword to target.
        secondary_keywords: Additional keywords to include.
        platform: Target platform for constraint matching.

    Returns:
        List of 3 title variants for A/B testing.
    """
    constraints = PLATFORM_CONSTRAINTS.get(platform, PLATFORM_CONSTRAINTS["etsy"])
    logger.info("generating_titles", product=product_name, platform=platform)

    prompt = TITLE_GENERATION_PROMPT.format(
        product_name=product_name,
        primary_keyword=primary_keyword,
        secondary_keywords=", ".join(secondary_keywords),
        platform=platform,
        max_length=constraints["max_length"],
        strategy=constraints["strategy"],
    )

    result = generate_json(prompt)
    titles = [t["title"][:constraints["max_length"]] for t in result.get("titles", [])]

    logger.info("titles_generated", platform=platform, count=len(titles))
    return titles
