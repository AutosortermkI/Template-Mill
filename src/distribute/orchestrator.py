"""Distribute module orchestrator — coordinates multi-platform listing creation."""

from src.distribute.models import Listing, SEOData
from src.distribute.seo.description_writer import write_description
from src.distribute.seo.tag_generator import generate_tags
from src.distribute.seo.title_optimizer import generate_titles
from src.shared.logger import get_logger

logger = get_logger("distribute_orchestrator")


class DistributeOrchestrator:
    """Coordinates SEO optimization and multi-platform listing creation."""

    def generate_seo_package(
        self,
        product_name: str,
        primary_keyword: str,
        secondary_keywords: list[str],
        format: str,
        price: float,
        features: list[str],
        audience: str,
        platforms: list[str],
    ) -> dict[str, SEOData]:
        """Generate complete SEO-optimized listing data for each platform.

        Args:
            product_name: Product name.
            primary_keyword: Main target keyword.
            secondary_keywords: Additional keywords.
            format: Template format.
            price: Product price.
            features: Key features list.
            audience: Target audience.
            platforms: List of target platforms.

        Returns:
            Dict mapping platform name to SEOData.
        """
        logger.info("generating_seo_package", product=product_name, platforms=platforms)

        results: dict[str, SEOData] = {}

        for platform in platforms:
            titles = generate_titles(product_name, primary_keyword, secondary_keywords, platform)
            tags = generate_tags(product_name, primary_keyword, platform)
            description = write_description(product_name, format, price, features, audience, platform)

            results[platform] = SEOData(
                title=titles[0] if titles else product_name,
                tags=tags,
                description=description,
                platform=platform,
            )

        logger.info("seo_package_complete", platforms=list(results.keys()))
        return results
