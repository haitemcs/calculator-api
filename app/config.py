"""Centralize settings that differ between local development and deployment.

Pydantic Settings reads environment variables first, then values in .env, then
the defaults below. For example, DATABASE_URL overrides database_url.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FastAPI Async Task Platform"

    # JWTs are signed with this key. Use a long, random value in your own .env.
    # The fallback is for local learning only, not a production secret.
    secret_key: str = "change-this-secret-before-deployment"
    access_token_expire_minutes: int = 30

    # Docker Compose resolves the hostnames "db" and "redis" inside its network.
    # These localhost defaults are for running the app directly on your computer.
    database_url: str = "postgresql+psycopg://app:app_password@localhost:5432/async_tasks"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Ignore unrelated environment variables instead of failing during startup.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Other modules import this shared settings object rather than parsing config again.
settings = Settings()
