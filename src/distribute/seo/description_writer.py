"""LLM listing description generator."""

from src.shared.llm import generate
from src.shared.logger import get_logger

logger = get_logger("description_writer")

DESCRIPTION_PROMPT = """Write a compelling product listing description for a digital template.

Product: {product_name}
Format: {format}
Price: ${price}
Key features: {features}
Target audience: {audience}
Platform: {platform}

Guidelines:
- Lead with the main benefit, not features
- Use scannable formatting (bullet points, short paragraphs)
- Include a clear call to action
- Mention what's included in the download
- Address common objections (ease of use, customization)
- Keep tone professional but approachable
- Do NOT use excessive emojis or hype language
- For Etsy: include relevant keywords naturally in the text

Write the description in markdown format."""


def write_description(
    product_name: str,
    format: str,
    price: float,
    features: list[str],
    audience: str,
    platform: str,
) -> str:
    """Generate a listing description optimized for the target platform.

    Args:
        product_name: The product name.
        format: Template format (notion, sheets, etc.).
        price: Product price.
        features: Key product features.
        audience: Target audience.
        platform: Target marketplace platform.

    Returns:
        Formatted description string.
    """
    logger.info("writing_description", product=product_name, platform=platform)

    prompt = DESCRIPTION_PROMPT.format(
        product_name=product_name,
        format=format,
        price=price,
        features=", ".join(features) if features else "comprehensive template",
        audience=audience or "general",
        platform=platform,
    )

    description = generate(prompt)

    logger.info("description_written", product=product_name, length=len(description))
    return description
