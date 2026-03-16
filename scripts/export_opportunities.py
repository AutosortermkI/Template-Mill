"""Export opportunities to CSV for review."""

import csv
import sys
from datetime import datetime

from src.shared.database import execute_query
from src.shared.logger import get_logger, setup_logging


def main() -> None:
    """Export all opportunities to a CSV file."""
    setup_logging()
    logger = get_logger("export_opportunities")

    output_file = f"opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    try:
        rows = execute_query(
            """
            SELECT o.id, k.term, o.niche_label, o.opportunity_score,
                   o.revenue_potential, o.competition_score, o.trend_momentum,
                   o.status, o.recommended_price, o.recommended_format,
                   o.created_at
            FROM opportunities o
            JOIN keywords k ON o.keyword_id = k.id
            ORDER BY o.opportunity_score DESC
            """
        )

        if not rows:
            print("No opportunities found.")
            return

        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        print(f"Exported {len(rows)} opportunities to {output_file}")
        logger.info("export_complete", count=len(rows), file=output_file)

    except Exception as e:
        logger.error("export_failed", error=str(e))
        print(f"Export failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
