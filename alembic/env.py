"""Alembic migration environment — wired to the application models and settings."""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure the project root is on sys.path so 'app' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import Base FIRST so all ORM models are registered
from app.db.base import Base  # noqa: E402

# Import all models so Alembic knows about every table.
import app.models  # noqa: F401

from app.core.config import settings  # noqa: E402

# --------------------------------------------------------------------------- #
# Alembic Config object                                                       #
# --------------------------------------------------------------------------- #
config = context.config

# Inject the database URL from application settings so alembic.ini does not
# need to contain any credentials.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# --------------------------------------------------------------------------- #
# Run migrations offline                                                      #
# --------------------------------------------------------------------------- #
def run_migrations_offline() -> None:
    """Run without a live DB connection; outputs SQL to stdout."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# --------------------------------------------------------------------------- #
# Run migrations online                                                       #
# --------------------------------------------------------------------------- #
def run_migrations_online() -> None:
    """Run with a live DB connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
