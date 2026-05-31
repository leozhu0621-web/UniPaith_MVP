"""Spec 15 — application workspace fields.

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-05-31 18:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

revision = "c4d5e6f7a8b9"  # pragma: allowlist secret
down_revision = "b3c4d5e6f7a8"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _add_column_if_missing(table: str, column: str, ddl: str) -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if column not in {c["name"] for c in insp.get_columns(table)}:
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {ddl}")


def upgrade() -> None:
    _add_column_if_missing(
        "applications",
        "submission_mode",
        "submission_mode VARCHAR(20) NOT NULL DEFAULT 'internal'",
    )
    _add_column_if_missing(
        "applications", "readiness_pct", "readiness_pct INTEGER NOT NULL DEFAULT 0"
    )
    _add_column_if_missing(
        "applications",
        "ready_to_submit",
        "ready_to_submit BOOLEAN NOT NULL DEFAULT false",
    )
    _add_column_if_missing("applications", "next_action", "next_action VARCHAR(255)")
    _add_column_if_missing("applications", "intent_picker", "intent_picker VARCHAR(30)")
    _add_column_if_missing("applications", "intent_rationale", "intent_rationale TEXT")
    _add_column_if_missing("applications", "fit_band", "fit_band VARCHAR(10)")
    _add_column_if_missing("applications", "guardrail_blockers", "guardrail_blockers JSONB")


def downgrade() -> None:
    for col in (
        "submission_mode",
        "readiness_pct",
        "ready_to_submit",
        "next_action",
        "intent_picker",
        "intent_rationale",
        "fit_band",
        "guardrail_blockers",
    ):
        op.drop_column("applications", col)
