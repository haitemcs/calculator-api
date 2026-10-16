"""Set up SQLAlchemy and provide a database session when code needs one."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# The engine manages connections and reuses them through a connection pool.
# pool_pre_ping checks that a pooled connection is still alive before using it.
engine = create_engine(settings.database_url, pool_pre_ping=True)

# SessionLocal is a factory: calling it creates a new session for one unit of work.
# Endpoints commit successful changes and close their session when they're done.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Base class inherited by models such as User and Task.

    SQLAlchemy collects those models' table definitions in Base.metadata.
    Alembic uses that metadata when creating and tracking schema migrations.
    """


def get_db() -> Generator[Session, None, None]:
    """Provide one session to an endpoint and close it afterward.

    FastAPI's Depends(get_db) manages this generator. The finally block also runs
    when the endpoint raises an exception, helping avoid leaked connections.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
