"""Recovery — idempotently ensure the recent ORM-mapped columns exist on
``institutions`` / ``schools`` / ``programs`` / ``program_preferences`` /
``match_rationales`` (``aiclaim01`` + ``deepintel1`` + ``aivisamig01``).

WHY: those migrations add columns with plain ``op.add_column`` (no
``IF NOT EXISTS``); ``deepintel1`` also ends with an ORM backfill. If one partially
applies and then fails, the container entrypoint's last-ditch recovery purges
``alembic_version`` and ``alembic stamp heads`` — marking it *applied without
running it*. The ORM (``models/institution.py`` / ``models/ai_artifacts.py``)
maps every one of those columns, so each ``SELECT`` against those tables 500s the
entire public browse + detail surface.

A normal ``alembic upgrade heads`` cannot self-heal (the migration is stamped, so
it is skipped), and the intervening per-credential data migrations
(``uclapercrd1`` / ``jhupercrd1`` / …) ``select(Institution)`` + run
``backfill_program_preferences`` — so they would fail on the missing columns
before this tail recovery could run. ``docker-entrypoint.sh`` therefore also runs
``recovery_ddl.RECOVERY_STATEMENTS`` *before* ``alembic upgrade``. This migration
keeps the alembic history honest and covers the canonical fresh-DB path; the
shared statements are pure ``ADD COLUMN IF NOT EXISTS`` + guarded FKs (no-op when
present, restore when missing — no backfill / service call that could re-fail).

Revision ID: deepintelfix1
Revises: jhupercrd1
Create Date: 2026-06-21

"""

from __future__ import annotations

from alembic import op

from unipaith.recovery_ddl import RECOVERY_STATEMENTS

# revision identifiers, used by Alembic.
revision = "deepintelfix1"  # pragma: allowlist secret
down_revision = "jhupercrd1"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    for statement in RECOVERY_STATEMENTS:
        op.execute(statement)


def downgrade() -> None:
    # Recovery-only: never drop columns the real migrations own (dropping them
    # would re-break the read paths). Intentionally a no-op.
    pass
