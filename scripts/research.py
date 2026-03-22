"""Standalone demand research script — no database required.

Pulls Google Trends momentum + Etsy competition stats for seed keywords,
scores each opportunity, and outputs a ranked table + CSV.

Usage:
    python scripts/research.py              # full run (Etsy + Google Trends)
    python scripts/research.py --trends-only  # skip Etsy (no API key needed)
"""

import argparse
import asyncio
import csv
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.discover.analyzers.opportunity_scorer import score_opportunity
from src.discover.models import DemandSignalAggregate
from src.discover.scrapers.google_trends import GoogleTrendsScraper, TrendData
from src.shared.config import settings

# ── Seed keywords ────────────────────────────────────────────────────────────
SEED_KEYWORDS = [
    {"term": "planner", "category": "planner"},
    {"term": "tracker", "category": "tracker"},
    {"term": "dashboard", "category": "dashboard"},
    {"term": "template", "category": "template"},
    {"term": "budget", "category": "tracker"},
    {"term": "habit tracker", "category": "tracker"},
    {"term": "meal planner", "category": "planner"},
    {"term": "study planner", "category": "planner"},
    {"term": "notion template", "category": "template"},
    {"term": "notion dashboard", "category": "dashboard"},
    {"term": "notion planner", "category": "planner"},
    {"term": "notion budget", "category": "tracker"},
    {"term": "notion student", "category": "template"},
    {"term": "notion aesthetic", "category": "template"},
    {"term": "student planner", "category": "planner"},
    {"term": "freelancer template", "category": "template"},
    {"term": "wedding planner", "category": "planner"},
    {"term": "adhd planner", "category": "planner"},
    {"term": "small business template", "category": "template"},
    {"term": "content creator planner", "category": "planner"},
    {"term": "digital planner", "category": "planner"},
    {"term": "spreadsheet template", "category": "template"},
    {"term": "goodnotes planner", "category": "planner"},
    {"term": "budget spreadsheet", "category": "tracker"},
    {"term": "project tracker", "category": "tracker"},
    {"term": "self care planner", "category": "planner"},
    {"term": "reading tracker", "category": "tracker"},
    {"term": "fitness planner", "category": "planner"},
    {"term": "travel planner", "category": "planner"},
    {"term": "social media planner", "category": "planner"},
]

_EMPTY_TREND = TrendData(momentum=0.0, interest=0)


async def fetch_etsy_stats(keywords: list[dict]) -> dict[str, dict]:
    """Fetch Etsy competition stats for each keyword."""
    from src.discover.scrapers.etsy_listings import EtsyListingScraper

    scraper = EtsyListingScraper()
    results = {}

    for i, kw in enumerate(keywords, 1):
        term = kw["term"]
        print(f"  [{i}/{len(keywords)}] Etsy: {term}", end="", flush=True)
        try:
            stats = await scraper.get_competition_stats(term)
            results[term] = stats
            print(f"  — {stats['listing_count']} listings, ${stats['avg_price']:.2f} avg")
        except Exception as e:
            print(f"  — ERROR: {e}")
            results[term] = {"listing_count": 0, "avg_price": 0.0, "avg_reviews": 0.0}

    await scraper.close()
    return results


async def fetch_trends(keywords: list[dict]) -> dict[str, TrendData]:
    """Fetch Google Trends momentum and interest for each keyword."""
    terms = [kw["term"] for kw in keywords]
    print(f"  Fetching Google Trends for {len(terms)} keywords (batches of 5, ~10s between)...")
    try:
        scraper = GoogleTrendsScraper()
    except ConnectionError as e:
        print(f"\n  ERROR: {e}\n")
        return {kw["term"]: _EMPTY_TREND for kw in keywords}

    try:
        trend_data = await scraper.get_momentum(terms)

        # Report what we got
        got_data = sum(1 for td in trend_data.values() if td["interest"] > 0)
        got_momentum = sum(1 for td in trend_data.values() if td["momentum"] > 0)
        print(f"  Got interest data for {got_data}/{len(terms)} keywords, "
              f"momentum for {got_momentum}/{len(terms)}")

        if got_data == 0:
            print("\n  WARNING: Google Trends returned no usable data for any keyword.")
            print("  This usually means Google is rate-limiting or blocking pytrends.")
            print("  Try: waiting a few minutes, using a VPN, or adding ETSY_API_KEY to .env\n")

        return trend_data
    except Exception as e:
        print(f"\n  WARNING: Google Trends failed ({type(e).__name__}: {e})")
        print("  Continuing without trend data...\n")
        return {kw["term"]: _EMPTY_TREND for kw in keywords}


def build_results(
    keywords: list[dict],
    trends: dict[str, TrendData],
    etsy: dict[str, dict] | None,
) -> list[dict]:
    """Score each keyword and return sorted results."""
    rows = []

    for kw in keywords:
        term = kw["term"]
        trend_data = trends.get(term, _EMPTY_TREND)
        momentum = trend_data["momentum"]
        interest = trend_data["interest"]

        etsy_data = (etsy or {}).get(term, {})
        listing_count = etsy_data.get("listing_count", 0)
        avg_price = etsy_data.get("avg_price", 0.0)
        avg_reviews = etsy_data.get("avg_reviews", 0.0)

        # Use listing_count as a proxy for search volume (Etsy API doesn't expose true search volume)
        search_volume_proxy = listing_count * 50  # rough estimate

        aggregate = DemandSignalAggregate(
            keyword_id=0,
            keyword_term=term,
            etsy_search_volume=search_volume_proxy,
            etsy_competition=listing_count,
            etsy_avg_price=avg_price,
            etsy_avg_reviews=avg_reviews,
            google_momentum=momentum,
            google_interest=interest,
        )

        score = score_opportunity(aggregate)

        rows.append({
            "keyword": term,
            "category": kw["category"],
            "score": score.total,
            "interest": interest,
            "momentum": momentum,
            "trend": score.trend_momentum,
            "listings": listing_count,
            "avg_price": avg_price,
            "avg_reviews": avg_reviews,
        })

    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows


def print_table(rows: list[dict], has_etsy: bool) -> None:
    """Print a formatted results table."""
    print("\n" + "=" * 100)
    print("DEMAND RESEARCH RESULTS")
    print("=" * 100)

    if has_etsy:
        header = (
            f"{'Rank':<5} {'Keyword':<28} {'Score':>6} {'Interest':>8} "
            f"{'Mom.':>5} {'Trend':>6} {'Listings':>8} {'AvgPrice':>9}"
        )
        print(header)
        print("-" * 100)
        for i, r in enumerate(rows, 1):
            flag = " **" if r["score"] >= 50 else ""
            print(
                f"{i:<5} {r['keyword']:<28} {r['score']:>6.1f} {r['interest']:>8} "
                f"{r['momentum']:>5.2f} {r['trend']:>6.1f} {r['listings']:>8} "
                f"{r['avg_price']:>8.2f}{flag}"
            )
    else:
        header = f"{'Rank':<5} {'Keyword':<28} {'Score':>6} {'Interest':>8} {'Momentum':>9} {'Direction':>10}"
        print(header)
        print("-" * 72)
        for i, r in enumerate(rows, 1):
            if r["momentum"] >= 1.2:
                direction = "RISING **"
            elif r["momentum"] >= 0.8:
                direction = "stable"
            elif r["momentum"] > 0:
                direction = "declining"
            else:
                direction = "—"
            print(
                f"{i:<5} {r['keyword']:<28} {r['score']:>6.1f} {r['interest']:>8} "
                f"{r['momentum']:>9.2f} {direction:>10}"
            )

    print()
    if has_etsy:
        print("** = high opportunity (score >= 50)")
    else:
        print("** = rising momentum (>1.2)")
        print("Interest = avg Google search interest (0-100, relative within batches of 5)")
    print()


def export_csv(rows: list[dict]) -> str:
    """Export results to a timestamped CSV file."""
    filename = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return filename


async def main() -> None:
    parser = argparse.ArgumentParser(description="TemplateMill demand research")
    parser.add_argument("--trends-only", action="store_true", help="Skip Etsy API calls (Google Trends only)")
    parser.add_argument("--etsy-only", action="store_true", help="Skip Google Trends (Etsy API only)")
    parser.add_argument("--no-csv", action="store_true", help="Don't export CSV")
    args = parser.parse_args()

    has_etsy = not args.trends_only and bool(settings.ETSY_API_KEY)
    has_trends = not args.etsy_only

    if not args.trends_only and not settings.ETSY_API_KEY:
        print("WARNING: No ETSY_API_KEY found in .env — running with Google Trends only.")
        print("         Add your key to .env or use --trends-only to suppress this warning.\n")

    keywords = SEED_KEYWORDS

    # Fetch data
    print(f"\nResearching {len(keywords)} keywords...\n")

    trends: dict[str, TrendData] = {}
    if has_trends:
        trends = await fetch_trends(keywords)
    else:
        trends = {kw["term"]: _EMPTY_TREND for kw in keywords}

    etsy = None
    if has_etsy:
        print()
        etsy = await fetch_etsy_stats(keywords)

    # Score and rank
    rows = build_results(keywords, trends, etsy)

    # Check if results are meaningful
    scores = [r["score"] for r in rows]
    if len(set(scores)) <= 1:
        print("\n" + "=" * 72)
        print("  NO ACTIONABLE DATA — all keywords scored identically.")
        print("  Neither Google Trends nor Etsy returned usable data.")
        print()
        print("  To fix, try ONE of:")
        print("    1. Add ETSY_API_KEY to .env  (most reliable data source)")
        print("    2. Wait a few minutes and retry  (Google may be rate-limiting)")
        print("    3. Use a VPN  (Google blocks some IPs from Trends data)")
        print("=" * 72 + "\n")
        if not args.no_csv:
            csv_file = export_csv(rows)
            print(f"(Empty results exported to: {csv_file})")
        return

    # Output
    print_table(rows, has_etsy)

    if not args.no_csv:
        csv_file = export_csv(rows)
        print(f"Results exported to: {csv_file}")


if __name__ == "__main__":
    asyncio.run(main())
