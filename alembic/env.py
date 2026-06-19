"""Alembic environment for the centralized APGuru migrations repo.

Standalone and decoupled from any application: the database URL comes from
the environment (``DATABASE_URL``, or composed from ``DB_*`` vars), and there
is no ``target_metadata`` because every migration is hand-written raw SQL —
``alembic revision --autogenerate`` is intentionally not supported here.
"""

import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

load_dotenv()

# Alembic Config object — provides access to values in alembic.ini.
config = context.config

# Configure Python logging from the .ini file.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Hand-written raw-SQL migrations only: no model metadata, no autogenerate.
target_metadata = None


def _database_url() -> str:
    """Resolve the sync SQLAlchemy URL from the environment.

    Prefers a full ``DATABASE_URL``; otherwise composes one from the
    individual ``DB_*`` variables (so teammates can reuse an app ``.env``).
    """
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    host = os.environ.get("DB_HOST")
    name = os.environ.get("DB_NAME")
    user = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASSWORD")
    port = os.environ.get("DB_PORT", "3306")
    if not all([host, name, user, password]):
        raise RuntimeError(
            "No database configuration found. Set DATABASE_URL, or all of "
            "DB_HOST / DB_NAME / DB_USER / DB_PASSWORD (DB_PORT optional, "
            "defaults to 3306). See .env.example."
        )
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"


config.set_main_option("sqlalchemy.url", _database_url())


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL, no live connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (against a live connection)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
