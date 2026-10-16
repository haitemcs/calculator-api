"""Set up SQLAlchemy and provide one database session per request or task."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# The engine manages the pool of database connections for the application.
# pool_pre_ping checks a pooled connection before using it, helping with stale
# connections after a database restart.
engine = create_engine(settings.database_url, pool_pre_ping=True)

# A session is a unit of work: it tracks ORM changes until commit or rollback.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Base class that SQLAlchemy models inherit from."""


def get_db() -> Generator[Session, None, None]:
    """Yield a session to a FastAPI endpoint and always close it afterward.

    FastAPI's Depends(get_db) handles the generator lifecycle. The finally block
    runs even if an endpoint raises an exception, so connections aren't left open.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
