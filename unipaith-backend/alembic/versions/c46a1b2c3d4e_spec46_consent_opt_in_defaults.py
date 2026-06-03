"""Spec 46 §2 — outreach + analytics consent default to opt-in (false).

The `outreach` and `analytics`(=`consent_research`) levers were created with the
ORM applying `default=True`, contradicting Spec 46 §2 which mandates both default
to **false** (the student opts in explicitly; only `matching` defaults true).

This migration:
  1. Sets a DB-level `server_default false` on both columns (matches the new ORM
     default and protects raw inserts).
  2. Pre-launch privacy correction: resets every existing row to opt-out. No
     student has given an explicit opt-in yet (demo/seed accounts only, and demo
     accounts are regenerated on login), so there are no real consents to
     preserve — leaving them `true` would keep students wrongly opted into
     institution outreach.

Guarded so it is a safe no-op against the conftest `create_all` test DB.

Revision ID: c46a1b2c3d4e
Revises: cs69inst1a2b3
Create Date: 2026-06-03

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "c46a1b2c3d4e"  # pragma: allowlist secret
down_revision = "cs69inst1a2b3"  # pragma: allowlist secret
branch_labels = None
depends_on = None

_COLS = ("consent_outreach", "consent_research")


def _existing_cols() -> set[str]:
    insp = sa.inspect(op.get_bind())
    if "student_data_consent" not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns("student_data_consent")}


def upgrade() -> None:
    cols = _existing_cols()
    for col in _COLS:
        if col not in cols:
            continue
        op.alter_column(
            "student_data_consent",
            col,
            server_default=sa.text("false"),
            existing_type=sa.Boolean(),
            existing_nullable=False,
        )
        # Pre-launch opt-in correction — reset every existing row to opt-out.
        op.execute(f"UPDATE student_data_consent SET {col} = false")


def downgrade() -> None:
    cols = _existing_cols()
    for col in _COLS:
        if col not in cols:
            continue
        op.alter_column(
            "student_data_consent",
            col,
            server_default=sa.text("true"),
            existing_type=sa.Boolean(),
            existing_nullable=False,
        )
