"""SQLAlchemy session factory and dependency injection helper for OmniPharma.

Creates the main engine and session factory from ``Settings.database_url``
and exposes a ``get_db()`` generator for FastAPI dependency injection.
Separate engine/session factories are provided for the PPB catalogue DB.

Imports/dependencies: sqlalchemy, app.core.config, app.db.models.

Public outputs: ``engine``, ``SessionLocal``, ``get_db()``,
``create_all_tables()``.
"""

from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.models import Base


def _make_engine(url: str):
    """Create a SQLAlchemy engine, enabling WAL mode for SQLite.

    Args:
        url: SQLAlchemy connection string.

    Returns:
        A configured :class:`sqlalchemy.engine.Engine` instance.
    """
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    eng = create_engine(url, connect_args=connect_args, echo=False)

    # Enable WAL journal mode for SQLite to support concurrent readers.
    if url.startswith("sqlite"):

        @event.listens_for(eng, "connect")
        def set_sqlite_pragma(dbapi_conn, _connection_record):  # noqa: ANN001
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return eng


_settings = get_settings()

engine = _make_engine(_settings.database_url)
"""Primary database engine bound to ``Settings.database_url``."""

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)
"""Session factory for the primary patient/rules database."""


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for use as a FastAPI dependency.

    Opens a new :class:`sqlalchemy.orm.Session` for the duration of the
    HTTP request and closes it (rolling back on any unhandled exception)
    when the request handler returns.

    Yields:
        An active :class:`sqlalchemy.orm.Session` bound to the primary
        database engine.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables() -> None:
    """Create all ORM-mapped tables that do not yet exist.

    Idempotent — safe to call at every application startup. Uses
    ``Base.metadata.create_all`` so only missing tables are created;
    existing tables and their data are not modified.

    Returns:
        None
    """
    Base.metadata.create_all(bind=engine)
