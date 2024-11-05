import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Get the directory containing the migrations folder
migrations_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Get the parent directory of the app folder
root_dir = os.path.dirname(migrations_dir)
# Add the root directory to Python path
sys.path.insert(0, root_dir)

# Import the models and config
from app.db.base_class import Base
from app.core.config import settings

# Import all models to ensure they are known to SQLAlchemy
from app.models.entities.user import User, group_members
from app.models.entities.group import Group
from app.models.entities.password import Password

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set sqlalchemy.url in alembic.ini
config.set_main_option("sqlalchemy.url", str(settings.SQLALCHEMY_DATABASE_URI))

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = str(settings.SQLALCHEMY_DATABASE_URI)
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()