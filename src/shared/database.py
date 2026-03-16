"""PostgreSQL connection and query helpers using SQLAlchemy."""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.shared.config import settings
from src.shared.logger import get_logger

logger = get_logger("database")

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Get or create the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
        logger.info("database_engine_created")
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Get or create the session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine())
    return _session_factory


def get_session() -> Session:
    """Create a new database session."""
    return get_session_factory()()


def execute_query(query: str, params: dict | None = None) -> list[dict]:
    """Execute a raw SQL query and return results as dicts."""
    with get_engine().connect() as conn:
        result = conn.execute(text(query), params or {})
        if result.returns_rows:
            columns = list(result.keys())
            return [dict(zip(columns, row)) for row in result.fetchall()]
        conn.commit()
        return []


def check_connection() -> bool:
    """Verify database connectivity."""
    try:
        execute_query("SELECT 1")
        logger.info("database_connection_ok")
        return True
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))
        return False
