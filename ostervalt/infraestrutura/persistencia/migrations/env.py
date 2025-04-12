from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
import sys
import os

# Add the absolute path to the project root to sys.path
sys.path.insert(0, "/home/micelio/ostervalt/ostervalt")

from infraestrutura.persistencia.models import Base
from infraestrutura.persistencia.base import Database

config = context.config
config.config_file_name = "/home/micelio/ostervalt/ostervalt/infraestrutura/persistencia/migrations/alembic.ini"
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
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
    database = Database()
    connectable = database.engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
