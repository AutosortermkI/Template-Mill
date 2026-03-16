"""Payhip manual assist client (no official API available)."""

from src.shared.logger import get_logger

logger = get_logger("payhip_client")


class PayhipClient:
    """Payhip product management — manual assist only.

    Payhip does not provide a public API. This client generates
    the listing data in a structured format for manual upload.
    """

    def prepare_listing_data(
        self,
        title: str,
        description: str,
        price: float,
        tags: list[str],
    ) -> dict:
        """Prepare listing data for manual Payhip upload.

        Args:
            title: Product title.
            description: Product description.
            price: Product price.
            tags: Product tags/categories.

        Returns:
            Dict with all data needed for manual Payhip listing creation.
        """
        logger.info("preparing_payhip_listing", title=title)

        return {
            "platform": "payhip",
            "title": title,
            "description": description,
            "price": price,
            "tags": tags,
            "requires_manual_upload": True,
            "instructions": (
                "1. Log in to Payhip dashboard\n"
                "2. Click 'Add Product'\n"
                "3. Select 'Digital Download'\n"
                "4. Fill in the details from this data\n"
                "5. Upload the template file and preview images\n"
                "6. Set the price and publish"
            ),
        }
