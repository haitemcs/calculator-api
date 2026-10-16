"""Create the FastAPI application and expose basic health checks.

HTTP endpoints live in api.py. Keeping startup and health checks here makes
the entry point easier to find when you first open the project.
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

# Register the endpoints defined in api.py under this application.
app.include_router(router)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    """Return a small welcome response with links to useful URLs."""
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "health": "/health/live",
    }


@app.get("/health/live", tags=["health"])
def live() -> dict[str, str]:
    """Check that the web process responds, without checking its dependencies."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
def ready() -> dict[str, object]:
    """Check whether the API can reach PostgreSQL and the Redis broker."""
    dependencies: dict[str, str] = {}

    # SELECT 1 is a cheap query used only to confirm a database connection works.
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        dependencies["database"] = "ok"
    except Exception:
        # Health checks return a simple status rather than internal error details.
        dependencies["database"] = "unavailable"

    # Celery uses Redis to pass jobs from the API to the separate worker process.
    try:
        with celery_app.connection_for_read() as connection:
            connection.ensure_connection(max_retries=0)
        dependencies["redis"] = "ok"
    except Exception:
        dependencies["redis"] = "unavailable"

    # The API is ready only when both dependencies respond.
    is_ready = all(value == "ok" for value in dependencies.values())
    return {
        "status": "ok" if is_ready else "degraded",
        "dependencies": dependencies,
    }
