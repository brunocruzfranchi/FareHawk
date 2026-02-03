"""Database engine and session management."""

import logging
from contextlib import contextmanager
from sqlalchemy import create_engine
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
