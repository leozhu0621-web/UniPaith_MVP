"""Idempotent deepintel1 schema repair + UCLA re-apply when migrations were stamped not run.

When the container entrypoint's stamp-recovery path marks heads applied without executing
DDL, production can ship code that SELECTs ``profile_intelligence`` (and related columns)
before those columns exist — every institution/program browse endpoint 500s. This revision
guards every ``deepintel1`` column add with ``_has_column`` and re-applies
``ucla_profile.apply()`` so the UCLA per-credential repair (#975) lands even if
``uclapercrd1`` was stamped without running.

Revision ID: deepintelfix1
Revises: jhupercrd1
Create Date: 2026-06-21
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import inspect, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucla_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "deepintelfix1"
down_revision = "jhupercrd1"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    try:
        return column in {c["name"] for c in inspect(bind).get_columns(table)}
    except Exception:
        return False


def _add(table: str, column: sa.Column) -> None:
    if not _has_column(table, column.name):
        op.add_column(table, column)


def _has_fk(table: str, fk_name: str) -> bool:
    bind = op.get_bind()
    try:
        return fk_name in {fk["name"] for fk in inspect(bind).get_foreign_keys(table)}
    except Exception:
        return False


def upgrade() -> None:
    jsonb = postgresql.JSONB(astext_type=sa.Text())

    _add("institutions", sa.Column("profile_intelligence", jsonb, nullable=True))
    _add(
        "institutions",
        sa.Column(
            "profile_intelligence_version",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    _add(
        "institutions",
        sa.Column("profile_intelligence_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    _add(
        "institutions",
        sa.Column("is_claimed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    _add(
        "institutions",
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
    )
    _add(
        "institutions",
        sa.Column("claimed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    if not _has_fk("institutions", "fk_institutions_claimed_by_user_id_users"):
        op.create_foreign_key(
            "fk_institutions_claimed_by_user_id_users",
            "institutions",
            "users",
            ["claimed_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )

    for table in ("schools", "programs"):
        _add(table, sa.Column("profile_intelligence", jsonb, nullable=True))
        _add(
            table,
            sa.Column(
                "profile_intelligence_version",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
        )
        _add(
            table,
            sa.Column("profile_intelligence_updated_at", sa.DateTime(timezone=True), nullable=True),
        )

    _add("program_preferences", sa.Column("target_profile", jsonb, nullable=True))
    _add("program_preferences", sa.Column("preference_weights", jsonb, nullable=True))
    _add("program_preferences", sa.Column("provenance", jsonb, nullable=True))
    _add(
        "program_preferences",
        sa.Column("standard_version", sa.Integer(), nullable=False, server_default="1"),
    )
    _add(
        "program_preferences",
        sa.Column("derived_at", sa.DateTime(timezone=True), nullable=True),
    )
    _add("match_rationales", sa.Column("decision_brief", jsonb, nullable=True))

    session = Session(bind=op.get_bind())
    try:
        ucla_profile.apply(session)
        inst = session.scalar(
            select(Institution).where(Institution.name == ucla_profile.INSTITUTION_NAME)
        )
        if inst is not None:
            backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    finally:
        session.close()


def downgrade() -> None:
    pass
