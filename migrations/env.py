"""Alembic setup: connect migrations to the application's models and settings."""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app import models  # noqa: F401 -- registers the models with Base.metadata.
from app.config import settings
from app.database import Base

config = context.config
# Use the same database URL as the application.
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name:
    fileConfig(config.config_file_name)

# Alembic compares this metadata with the database schema.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Prepare SQL without opening a database connection."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to the database and apply migrations."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


# Alembic selects the online or offline path based on the command being run.
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
