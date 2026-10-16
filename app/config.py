"""Centralize settings so the app doesn't hard-code environment-specific values.

Pydantic Settings reads matching environment variables first, then .env, then
these defaults. For example, DATABASE_URL overrides database_url below.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FastAPI Async Task Platform"

    # Used to sign JWTs. Set a long, random value in your local .env file.
    # The default is only for local learning and must not be used in production.
    secret_key: str = "change-this-secret-before-deployment"
    access_token_expire_minutes: int = 30

    # Docker Compose uses the service names "db" and "redis". These localhost
    # defaults are useful when running the API directly on your own computer.
    database_url: str = "postgresql+psycopg://app:app_password@localhost:5432/async_tasks"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # extra="ignore" lets unrelated environment variables exist without errors.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Import settings from this single instance throughout the application.
settings = Settings()
