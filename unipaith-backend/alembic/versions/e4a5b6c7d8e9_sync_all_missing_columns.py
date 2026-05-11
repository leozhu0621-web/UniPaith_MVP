"""sync all missing columns onto existing tables

The prior corrective migrations (b1c2d3e4f5a6, c2e3f4a5b6c7,
d3f4a5b6c7d8) backfilled missing tables and the column set that
3b8d4e2f7a1c was supposed to add, but other historic migrations
were also stamped-without-running. Programs.school_id surfaced
the next time a student tried to browse programs.

Rather than play whack-a-mole, sweep every declarative model and
compare its column list against the live schema. For each column
present on the model but missing on the DB, emit
ALTER TABLE ... ADD COLUMN IF NOT EXISTS with the type SQLAlchemy
infers from the mapped_column. Existing columns are left alone.

This is "best-effort, idempotent, no constraints" — server defaults
are preserved, NULL/NOT NULL is intentionally relaxed to NULLABLE on
adds (since existing rows have no value), and foreign-key constraints
on the new columns are NOT added (a separate ALTER TABLE ADD
CONSTRAINT would be brittle here; the FK can be added in a future
schema-cleanup pass once the data layer is settled).

Revision ID: e4a5b6c7d8e9
Revises: d3f4a5b6c7d8
Create Date: 2026-05-10 21:00:00.000000

"""

from __future__ import annotations

import logging

from sqlalchemy import inspect

from alembic import op

# revision identifiers
revision = "e4a5b6c7d8e9"
down_revision = "d3f4a5b6c7d8"
branch_labels = None
depends_on = None

log = logging.getLogger("alembic.runtime.migration")


def upgrade() -> None:
    from unipaith import models  # noqa: F401 — register all model modules
    from unipaith.models.base import Base

    bind = op.get_bind()
    insp = inspect(bind)

    added = 0
    skipped_no_table = 0
    for table in Base.metadata.sorted_tables:
        if not insp.has_table(table.name):
            skipped_no_table += 1
            continue
        existing = {c["name"] for c in insp.get_columns(table.name)}
        for col in table.columns:
            if col.name in existing:
                continue
            # Render the column's DDL via SQLAlchemy's compiler. We don't
            # use op.add_column directly because we want IF NOT EXISTS
            # semantics for safety in case of partial reruns.
            type_sql = col.type.compile(dialect=bind.dialect)
            default_clause = ""
            if col.server_default is not None:
                # arg can be a TextClause; render via str() through the dialect
                arg = col.server_default.arg
                default_str = arg.text if hasattr(arg, "text") else str(arg)
                # Quote string defaults; leave bools/numerics as-is
                if (
                    default_str.lower() in ("true", "false")
                    or default_str.replace(".", "").replace("-", "").isdigit()
                ):
                    default_clause = f" DEFAULT {default_str}"
                else:
                    escaped = default_str.replace("'", "''")
                    default_clause = f" DEFAULT '{escaped}'"
            stmt = (
                f"ALTER TABLE {table.name} "
                f'ADD COLUMN IF NOT EXISTS "{col.name}" '
                f"{type_sql}{default_clause}"
            )
            log.info("sync: %s", stmt)
            op.execute(stmt)
            added += 1

    log.info(
        "schema sync complete: added=%d skipped_no_table=%d",
        added,
        skipped_no_table,
    )


def downgrade() -> None:
    # No-op: schema sync is forward-only.
    pass
