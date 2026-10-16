from fastapi import FastAPI
from sqlalchemy import text
from app.api import router
from app.config import settings
from app.database import engine
from app.tasks import celery_app
app=FastAPI(title=settings.app_name,description="JWT-authenticated async task processing with Celery, Redis, PostgreSQL.",version="1.0.0")
app.include_router(router)
@app.get("/",tags=["meta"])
def root():return {"name":settings.app_name,"docs":"/docs","health":"/health/live"}
@app.get("/health/live",tags=["health"])
def live():return {"status":"ok"}
@app.get("/health/ready",tags=["health"])
def ready():
    deps={}
    try:
        with engine.connect() as c:c.execute(text("SELECT 1"))
        deps["database"]="ok"
    except Exception:deps["database"]="unavailable"
    try:
        with celery_app.connection_for_read() as c:c.ensure_connection(max_retries=0)
        deps["redis"]="ok"
    except Exception:deps["redis"]="unavailable"
    ok=all(x=="ok" for x in deps.values())
    return {"status":"ok" if ok else "degraded","dependencies":deps}
