"""Tests for the discover repository module using an in-memory SQLite database."""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from src.discover.models import Opportunity
from src.discover.repository import (
    insert_demand_signal,
    insert_keywords,
    load_keywords,
    load_seed_terms,
    save_opportunities,
    upsert_opportunity,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT NOT NULL UNIQUE,
    category TEXT,
    subcategory TEXT,
    is_seed INTEGER NOT NULL DEFAULT 0,
    discovered_from TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_id INTEGER NOT NULL UNIQUE REFERENCES keywords(id),
    niche_label TEXT NOT NULL,
    opportunity_score REAL NOT NULL DEFAULT 0,
    revenue_potential REAL DEFAULT 0,
    competition_score REAL DEFAULT 0,
    trend_momentum REAL DEFAULT 0,
    social_validation REAL DEFAULT 0,
    competitor_gap REAL DEFAULT 0,
    recommended_price REAL,
    recommended_format TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    notes TEXT,
    gap_analysis TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    reviewed_at TEXT
);

CREATE TABLE demand_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_id INTEGER NOT NULL REFERENCES keywords(id),
    platform TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    etsy_search_volume INTEGER,
    etsy_competition INTEGER,
    etsy_avg_price REAL,
    etsy_avg_reviews REAL,
    google_interest INTEGER,
    google_momentum REAL
);
"""


@pytest.fixture
def db_session() -> Session:
    """Create an in-memory SQLite database with the core schema."""
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        for stmt in _SCHEMA.split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))
        conn.commit()
    factory = sessionmaker(bind=engine)
    session = factory()
    yield session
    session.close()


@pytest.fixture
def seeded_session(db_session: Session) -> Session:
    """Session pre-loaded with a few keywords."""
    db_session.execute(
        text("INSERT INTO keywords (term, category, is_seed, discovered_from) VALUES ('planner', 'planner', 1, 'manual')")
    )
    db_session.execute(
        text("INSERT INTO keywords (term, category, is_seed, discovered_from) VALUES ('tracker', 'tracker', 1, 'manual')")
    )
    db_session.execute(
        text("INSERT INTO keywords (term, category, is_seed, discovered_from) VALUES ('notion dark mode', 'template', 0, 'etsy_autocomplete')")
    )
    db_session.commit()
    return db_session


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_load_keywords_returns_all(seeded_session: Session) -> None:
    """load_keywords should return all keywords."""
    keywords = load_keywords(session=seeded_session)
    assert len(keywords) == 3
    assert keywords[0]["term"] == "planner"


def test_load_keywords_seed_only(seeded_session: Session) -> None:
    """load_keywords with seed_only=True should filter to seeds."""
    keywords = load_keywords(session=seeded_session, seed_only=True)
    assert len(keywords) == 2
    assert all(kw["is_seed"] for kw in keywords)


def test_load_seed_terms(seeded_session: Session) -> None:
    """load_seed_terms should return just term strings."""
    terms = load_seed_terms(session=seeded_session)
    assert terms == ["planner", "tracker"]


def test_insert_keywords_deduplicates(seeded_session: Session) -> None:
    """Inserting existing terms should skip them via ON CONFLICT."""
    inserted = insert_keywords(
        ["planner", "brand new keyword", "tracker"],
        discovered_from="test",
        session=seeded_session,
    )
    assert inserted == 1  # only "brand new keyword" is new
    all_kw = load_keywords(session=seeded_session)
    assert len(all_kw) == 4


def test_upsert_opportunity_insert(seeded_session: Session) -> None:
    """First upsert should insert a new opportunity."""
    opp = Opportunity(
        keyword_id=1,
        niche_label="planner",
        opportunity_score=72.5,
        revenue_potential=80.0,
        competition_score=60.0,
        trend_momentum=70.0,
        social_validation=50.0,
    )
    opp_id = upsert_opportunity(opp, session=seeded_session)
    assert opp_id >= 1


def test_upsert_opportunity_update(seeded_session: Session) -> None:
    """Second upsert for same keyword_id should update, not duplicate."""
    opp = Opportunity(keyword_id=1, niche_label="planner", opportunity_score=50.0)
    upsert_opportunity(opp, session=seeded_session)

    opp_updated = Opportunity(keyword_id=1, niche_label="planner", opportunity_score=85.0)
    upsert_opportunity(opp_updated, session=seeded_session)

    rows = seeded_session.execute(text("SELECT * FROM opportunities WHERE keyword_id = 1")).fetchall()
    assert len(rows) == 1
    assert float(rows[0][3]) == 85.0  # opportunity_score column


def test_save_opportunities_batch(seeded_session: Session) -> None:
    """save_opportunities should persist all opportunities."""
    opps = [
        Opportunity(keyword_id=1, niche_label="planner", opportunity_score=70.0),
        Opportunity(keyword_id=2, niche_label="tracker", opportunity_score=55.0),
    ]
    count = save_opportunities(opps, session=seeded_session)
    assert count == 2


def test_insert_demand_signal(seeded_session: Session) -> None:
    """insert_demand_signal should create a new signal row."""
    signal_id = insert_demand_signal(
        keyword_id=1,
        platform="etsy+google",
        captured_at=date(2026, 3, 16),
        data={
            "etsy_search_volume": 5000,
            "etsy_competition": 200,
            "etsy_avg_price": 15.0,
            "etsy_avg_reviews": 50.0,
            "google_momentum": 1.5,
        },
        session=seeded_session,
    )
    assert signal_id >= 1
    rows = seeded_session.execute(text("SELECT * FROM demand_signals")).fetchall()
    assert len(rows) == 1
