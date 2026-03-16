"""Seed the keywords table with initial seed keywords for demand research."""

SEED_KEYWORDS = [
    # Core template categories
    {"term": "planner", "category": "planner", "subcategory": None},
    {"term": "tracker", "category": "tracker", "subcategory": None},
    {"term": "dashboard", "category": "dashboard", "subcategory": None},
    {"term": "template", "category": "template", "subcategory": None},
    {"term": "budget", "category": "tracker", "subcategory": "finance"},
    {"term": "habit tracker", "category": "tracker", "subcategory": "productivity"},
    {"term": "meal planner", "category": "planner", "subcategory": "health"},
    {"term": "study planner", "category": "planner", "subcategory": "student"},
    # Notion-specific
    {"term": "notion template", "category": "template", "subcategory": "notion"},
    {"term": "notion dashboard", "category": "dashboard", "subcategory": "notion"},
    {"term": "notion planner", "category": "planner", "subcategory": "notion"},
    {"term": "notion budget", "category": "tracker", "subcategory": "notion"},
    {"term": "notion student", "category": "template", "subcategory": "student"},
    {"term": "notion aesthetic", "category": "template", "subcategory": "aesthetic"},
    # Audience segments
    {"term": "student planner", "category": "planner", "subcategory": "student"},
    {"term": "freelancer template", "category": "template", "subcategory": "freelancer"},
    {"term": "wedding planner", "category": "planner", "subcategory": "wedding"},
    {"term": "adhd planner", "category": "planner", "subcategory": "adhd"},
    {"term": "small business template", "category": "template", "subcategory": "business"},
    {"term": "content creator planner", "category": "planner", "subcategory": "creator"},
    # Product types
    {"term": "digital planner", "category": "planner", "subcategory": "digital"},
    {"term": "spreadsheet template", "category": "template", "subcategory": "sheets"},
    {"term": "goodnotes planner", "category": "planner", "subcategory": "goodnotes"},
    {"term": "budget spreadsheet", "category": "tracker", "subcategory": "finance"},
    {"term": "project tracker", "category": "tracker", "subcategory": "project"},
    # Trending niches
    {"term": "self care planner", "category": "planner", "subcategory": "wellness"},
    {"term": "reading tracker", "category": "tracker", "subcategory": "reading"},
    {"term": "fitness planner", "category": "planner", "subcategory": "fitness"},
    {"term": "travel planner", "category": "planner", "subcategory": "travel"},
    {"term": "social media planner", "category": "planner", "subcategory": "marketing"},
]


def main() -> None:
    """Insert seed keywords into the database."""
    from src.shared.database import get_session
    from src.shared.logger import get_logger, setup_logging

    setup_logging()
    logger = get_logger("seed_keywords")

    session = get_session()

    try:
        for kw in SEED_KEYWORDS:
            session.execute(
                """
                INSERT INTO keywords (term, category, subcategory, is_seed, discovered_from)
                VALUES (:term, :category, :subcategory, TRUE, 'manual')
                ON CONFLICT (term) DO NOTHING
                """,
                kw,
            )

        session.commit()
        logger.info("seed_keywords_complete", count=len(SEED_KEYWORDS))
        print(f"Seeded {len(SEED_KEYWORDS)} keywords.")

    except Exception as e:
        session.rollback()
        logger.error("seed_keywords_failed", error=str(e))
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
