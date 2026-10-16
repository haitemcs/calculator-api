from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    app_name: str = "FastAPI Async Task Platform"
    secret_key: str = "change-this-secret-before-deployment"
    access_token_expire_minutes: int = 30
    database_url: str = "postgresql+psycopg://app:app_password@localhost:5432/async_tasks"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
settings = Settings()
