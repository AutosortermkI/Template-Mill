"""UTM and referral tracking aggregator."""

from src.shared.logger import get_logger

logger = get_logger("traffic_sources")


class TrafficSourceAggregator:
    """Aggregate traffic source data from UTM parameters and referral tracking."""

    def build_utm_url(
        self,
        base_url: str,
        source: str,
        medium: str,
        campaign: str,
        content: str = "",
    ) -> str:
        """Build a URL with UTM tracking parameters.

        Args:
            base_url: The destination URL.
            source: Traffic source (e.g., 'pinterest', 'etsy').
            medium: Marketing medium (e.g., 'social', 'marketplace').
            campaign: Campaign name (e.g., 'spring-planners-2026').
            content: Optional content identifier for A/B testing.

        Returns:
            URL with UTM parameters appended.
        """
        separator = "&" if "?" in base_url else "?"
        params = f"utm_source={source}&utm_medium={medium}&utm_campaign={campaign}"
        if content:
            params += f"&utm_content={content}"

        return f"{base_url}{separator}{params}"

    def aggregate_sources(self, raw_data: list[dict]) -> dict:
        """Aggregate traffic source data into a summary.

        Args:
            raw_data: List of raw traffic event dicts with 'source', 'medium', 'campaign'.

        Returns:
            Summary dict with source breakdown and top campaigns.
        """
        by_source: dict[str, int] = {}
        by_campaign: dict[str, int] = {}

        for event in raw_data:
            source = event.get("source", "direct")
            campaign = event.get("campaign", "none")

            by_source[source] = by_source.get(source, 0) + 1
            by_campaign[campaign] = by_campaign.get(campaign, 0) + 1

        return {
            "by_source": dict(sorted(by_source.items(), key=lambda x: x[1], reverse=True)),
            "by_campaign": dict(sorted(by_campaign.items(), key=lambda x: x[1], reverse=True)),
            "total_events": len(raw_data),
        }
