"""Uni managed agent — discovery_sessions.agent_session_id.

Binds a student's discovery journey to its Anthropic managed-agent session id
(``sesn_...``). Guarded so it is a safe no-op against the conftest
``create_all`` test DB and idempotent on re-run.

Revision ID: uni_agent_sess_a1b2c3
Revises: cornellprof3
Create Date: 2026-06-12
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "uni_agent_sess_a1b2c3"  # pragma: allowlist secret
down_revision = "cornellprof3"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _cols() -> set[str]:
    insp = sa.inspect(op.get_bind())
    if "discovery_sessions" not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns("discovery_sessions")}


def upgrade() -> None:
    cols = _cols()
    if not cols:
        return
    if "agent_session_id" not in cols:
        op.add_column(
            "discovery_sessions",
            sa.Column("agent_session_id", sa.String(length=64), nullable=True),
        )
        op.create_index(
            "ix_discovery_sessions_agent_session_id",
            "discovery_sessions",
            ["agent_session_id"],
        )


def downgrade() -> None:
    if "agent_session_id" in _cols():
        op.drop_index(
            "ix_discovery_sessions_agent_session_id",
            table_name="discovery_sessions",
        )
        op.drop_column("discovery_sessions", "agent_session_id")
