import asyncio
import logging
from logging.config import fileConfig

from sqlalchemy import inspect, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context, op
from unipaith.config import settings
from unipaith.models import Base  # noqa: F401 — side-effect: registers all models

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

_log = logging.getLogger("alembic.runtime.migration")


def _install_idempotency_guards() -> None:
    """Make schema-creation ops tolerate objects that already exist.

    This chain carries corrective "best-effort" migrations (b1c2d3e4f5a6,
    c2e3f4a5b6c7, d3f4a5b6c7d8, e4a5b6c7d8e9) that repair a production database
    whose earlier migrations were stamped-without-running. d3f4a5b6c7d8 in
    particular runs ``metadata.create_all`` for the *current* model set, so on a
    fresh database (``make dev-backend``, a new environment, disaster recovery)
    every table/column/index/constraint already exists by the time the later
    migrations that "own" them replay their plain ``CREATE``/``ADD`` — which
    would otherwise raise DuplicateTable/DuplicateColumn and abort the upgrade.

    Guarding the create-ops to skip pre-existing objects makes ``upgrade head``
    replay cleanly from scratch while leaving normal incremental upgrades (where
    the object does not yet exist) completely unchanged — production deploys add
    only genuinely-new objects, so these guards never fire there.
    """

    def _insp():
        return inspect(op.get_bind())

    _orig_create_table = op.create_table
    _orig_add_column = op.add_column
    _orig_create_index = op.create_index
    _orig_create_unique = op.create_unique_constraint
    _orig_create_fk = op.create_foreign_key
    _orig_create_check = op.create_check_constraint

    def create_table(table_name, *cols, **kw):  # noqa: ANN001, ANN202
        if _insp().has_table(table_name):
            _log.info("idempotent: skip create_table %s (already exists)", table_name)
            return None
        return _orig_create_table(table_name, *cols, **kw)

    def add_column(table_name, column, **kw):  # noqa: ANN001, ANN202
        insp = _insp()
        if insp.has_table(table_name) and column.name in {
            c["name"] for c in insp.get_columns(table_name)
        }:
            _log.info(
                "idempotent: skip add_column %s.%s (already exists)",
                table_name,
                column.name,
            )
            return None
        return _orig_add_column(table_name, column, **kw)

    def create_index(index_name, table_name, *args, **kw):  # noqa: ANN001, ANN202
        insp = _insp()
        if (
            index_name
            and insp.has_table(table_name)
            and index_name in {ix["name"] for ix in insp.get_indexes(table_name)}
        ):
            _log.info("idempotent: skip create_index %s (already exists)", index_name)
            return None
        return _orig_create_index(index_name, table_name, *args, **kw)

    def create_unique_constraint(name, table_name, *args, **kw):  # noqa: ANN001, ANN202
        insp = _insp()
        if (
            name
            and insp.has_table(table_name)
            and name in {uc["name"] for uc in insp.get_unique_constraints(table_name)}
        ):
            _log.info("idempotent: skip unique_constraint %s (already exists)", name)
            return None
        return _orig_create_unique(name, table_name, *args, **kw)

    def create_foreign_key(name, source_table, *args, **kw):  # noqa: ANN001, ANN202
        insp = _insp()
        if (
            name
            and insp.has_table(source_table)
            and name in {fk["name"] for fk in insp.get_foreign_keys(source_table)}
        ):
            _log.info("idempotent: skip foreign_key %s (already exists)", name)
            return None
        return _orig_create_fk(name, source_table, *args, **kw)

    def create_check_constraint(name, table_name, *args, **kw):  # noqa: ANN001, ANN202
        insp = _insp()
        if (
            name
            and insp.has_table(table_name)
            and name in {ck["name"] for ck in insp.get_check_constraints(table_name)}
        ):
            _log.info("idempotent: skip check_constraint %s (already exists)", name)
            return None
        return _orig_create_check(name, table_name, *args, **kw)

    op.create_table = create_table
    op.add_column = add_column
    op.create_index = create_index
    op.create_unique_constraint = create_unique_constraint
    op.create_foreign_key = create_foreign_key
    op.create_check_constraint = create_check_constraint


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


def do_run_migrations(connection):  # noqa: ANN001
    context.configure(connection=connection, target_metadata=target_metadata)
    _install_idempotency_guards()
    # Bound how long ANY migration waits for a lock. The enrichment routine ships
    # heavy data migrations (e.g. the per-school `<school>_profile.apply()` repairs)
    # that run at container boot; when they contend for a row/table lock held by the
    # already-running task's scheduler they block the boot FOREVER → ECS health-check
    # timeout → deploy rollback → no backend code can ship (this exact hang froze
    # prod on `berkeleycip1`). lock_timeout affects only lock WAITS — a running
    # statement is untouched — so it never kills a legitimately slow migration; a
    # migration that hits it should catch the error and skip its idempotent data
    # work so the chain still advances (see `berkeleycip1`).
    connection.exec_driver_sql("SET lock_timeout = '30s'")
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
