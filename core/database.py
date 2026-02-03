"""Database engine and session management."""

import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, inspect as sa_inspect, text, String, Date
from sqlalchemy.orm import sessionmaker, Session

from core.config import config
from core.models import Base

logger = logging.getLogger(__name__)

# Handle sqlite:/// path — ensure directory exists
_url = config.database_url
if _url.startswith("sqlite:///"):
    import os
    db_path = _url.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

engine = create_engine(
    _url,
    echo=False,
    pool_pre_ping=True,
    # SQLite needs check_same_thread=False for multi-threaded use
    connect_args={"check_same_thread": False} if _url.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")
    _migrate_missing_columns()


def _migrate_missing_columns() -> None:
    """Add missing columns to existing tables (simple ALTER TABLE migration).

    Uses SQLAlchemy inspect to compare model columns vs actual DB columns
    and adds any that are missing. This keeps existing databases from breaking
    when we add new columns to the models.
    """
    inspector = sa_inspect(engine)
    for table_name, table in Base.metadata.tables.items():
        if not inspector.has_table(table_name):
            continue
        existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
        for col in table.columns:
            if col.name not in existing_cols:
                # Build ALTER TABLE statement
                col_type = col.type.compile(engine.dialect)
                default = ""
                if col.default is not None:
                    default_val = col.default.arg
                    if callable(default_val):
                        default_val = default_val(None)
                    if isinstance(default_val, str):
                        default = f" DEFAULT '{default_val}'"
                    elif default_val is not None:
                        default = f" DEFAULT {default_val}"
                nullable = "" if col.nullable else " NOT NULL"
                # SQLite doesn't support NOT NULL without default on ALTER TABLE
                if _url.startswith("sqlite") and not col.nullable and not default:
                    if isinstance(col.type, String):
                        default = " DEFAULT ''"
                    else:
                        default = " DEFAULT NULL"
                    nullable = ""
                stmt = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}{default}{nullable}"
                try:
                    with engine.begin() as conn:
                        conn.execute(text(stmt))
                    logger.info("Migrated: added column %s.%s", table_name, col.name)
                except Exception:
                    logger.debug("Column %s.%s may already exist, skipping", table_name, col.name)


@contextmanager
def get_session() -> Session:
    """Provide a transactional database session scope."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_or_create_user(telegram_id: int, username: str | None = None, language: str = "en") -> "User":
    """Get existing user or create a new one."""
    from core.models import User

    with get_session() as session:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if user is None:
            user = User(telegram_id=telegram_id, username=username, language=language)
            session.add(user)
            session.flush()
        else:
            if username and user.username != username:
                user.username = username
        # Detach and return a usable copy
        session.expunge(user)
        return user
