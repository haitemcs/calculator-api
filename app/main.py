"""Create the FastAPI application and expose basic health checks.

This module is intentionally small: request handling lives in api.py, while
database models, authentication, and background work each have their own module.
"""
from fastapi import FastAPI
from sqlalchemy import text

from app.api import router
from app.config import settings
from app.database import engine
from app.tasks import celery_app

app = FastAPI(
    title=settings.app_name,
    description="JWT-authenticated task processing with Celery, Redis, and PostgreSQL.",
    version="1.0.0",
)

# Keep the API routes in one place instead of defining every endpoint here.
app.include_router(router)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    """Give a small welcome response and point people to the useful URLs."""
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "health": "/health/live",
    }


@app.get("/health/live", tags=["health"])
def live() -> dict[str, str]:
    """Check that the web process can respond; this does not check dependencies."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
def ready() -> dict[str, object]:
    """Check whether the API can currently reach PostgreSQL and Redis."""
    dependencies: dict[str, str] = {}

    # SELECT 1 is a lightweight way to confirm that a database connection works.
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        dependencies["database"] = "ok"
    except Exception:
        # Keep internal exception details out of a public health endpoint.
        dependencies["database"] = "unavailable"

    # Celery uses Redis as its message broker, so the API checks broker access too.
    try:
        with celery_app.connection_for_read() as connection:
            connection.ensure_connection(max_retries=0)
        dependencies["redis"] = "ok"
    except Exception:
        dependencies["redis"] = "unavailable"

    is_ready = all(value == "ok" for value in dependencies.values())
    return {
        "status": "ok" if is_ready else "degraded",
        "dependencies": dependencies,
    }
