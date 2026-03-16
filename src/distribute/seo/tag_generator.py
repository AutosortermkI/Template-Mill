"""Platform-specific tag optimization."""

from src.shared.llm import generate_json
from src.shared.logger import get_logger

logger = get_logger("tag_generator")

TAG_GENERATION_PROMPT = """Generate optimized tags for a digital template listing.

Product: {product_name}
Primary keyword: {primary_keyword}
Platform: {platform}
Max tags: {max_tags}
Max tag length: {max_tag_length} characters

Tag strategy:
- 1-2 exact match keyword tags
- 3-4 long-tail variations
- 2-3 audience-specific tags
- 2-3 style/aesthetic tags
- 1-2 seasonal or trending tags (if applicable)

Respond in JSON:
{{
  "tags": ["tag1", "tag2", ...]
}}

Each tag must be {max_tag_length} characters or fewer. Generate exactly {max_tags} tags."""

PLATFORM_TAG_LIMITS = {
    "etsy": {"max_tags": 13, "max_tag_length": 20},
    "shopify": {"max_tags": 20, "max_tag_length": 50},
    "gumroad": {"max_tags": 10, "max_tag_length": 30},
}


def generate_tags(
    product_name: str,
    primary_keyword: str,
    platform: str,
) -> list[str]:
    """Generate platform-optimized tags for a product listing.

    Args:
        product_name: The product name.
        primary_keyword: Main search keyword.
        platform: Target platform.

    Returns:
        List of tags within platform constraints.
    """
    limits = PLATFORM_TAG_LIMITS.get(platform, PLATFORM_TAG_LIMITS["etsy"])
    logger.info("generating_tags", product=product_name, platform=platform)

    prompt = TAG_GENERATION_PROMPT.format(
        product_name=product_name,
        primary_keyword=primary_keyword,
        platform=platform,
        max_tags=limits["max_tags"],
        max_tag_length=limits["max_tag_length"],
    )

    result = generate_json(prompt)
    tags = [tag[:limits["max_tag_length"]] for tag in result.get("tags", [])]
    tags = tags[: limits["max_tags"]]

    logger.info("tags_generated", platform=platform, count=len(tags))
    return tags
