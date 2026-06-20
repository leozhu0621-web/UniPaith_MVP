"""deep profile intelligence and decision brief contracts

Revision ID: deepintel1
Revises: harvardpercred1
Create Date: 2026-06-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "deepintel1"
down_revision: str | Sequence[str] | None = "harvardpercred1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    jsonb = postgresql.JSONB(astext_type=sa.Text())

    op.add_column("institutions", sa.Column("profile_intelligence", jsonb, nullable=True))
    op.add_column(
        "institutions",
        sa.Column(
            "profile_intelligence_version",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "institutions",
        sa.Column("profile_intelligence_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "institutions",
        sa.Column("is_claimed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "institutions", sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "institutions",
        sa.Column("claimed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_institutions_claimed_by_user_id_users",
        "institutions",
        "users",
        ["claimed_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    for table in ("schools", "programs"):
        op.add_column(table, sa.Column("profile_intelligence", jsonb, nullable=True))
        op.add_column(
            table,
            sa.Column(
                "profile_intelligence_version",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
        )
        op.add_column(
            table,
            sa.Column("profile_intelligence_updated_at", sa.DateTime(timezone=True), nullable=True),
        )

    op.add_column("program_preferences", sa.Column("target_profile", jsonb, nullable=True))
    op.add_column("program_preferences", sa.Column("preference_weights", jsonb, nullable=True))
    op.add_column("program_preferences", sa.Column("provenance", jsonb, nullable=True))
    op.add_column(
        "program_preferences",
        sa.Column("standard_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "program_preferences", sa.Column("derived_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("match_rationales", sa.Column("decision_brief", jsonb, nullable=True))

    session = Session(bind=op.get_bind())
    try:
        from unipaith.services.profile_enrichment.intelligence import (
            backfill_profile_intelligence_sync,
        )

        backfill_profile_intelligence_sync(session)
        from unipaith.services.match.derive_preferences import backfill_program_preferences

        backfill_program_preferences(session)
    finally:
        session.close()


def downgrade() -> None:
    op.drop_column("match_rationales", "decision_brief")
    op.drop_column("program_preferences", "derived_at")
    op.drop_column("program_preferences", "standard_version")
    op.drop_column("program_preferences", "provenance")
    op.drop_column("program_preferences", "preference_weights")
    op.drop_column("program_preferences", "target_profile")

    for table in ("programs", "schools"):
        op.drop_column(table, "profile_intelligence_updated_at")
        op.drop_column(table, "profile_intelligence_version")
        op.drop_column(table, "profile_intelligence")

    op.drop_constraint(
        "fk_institutions_claimed_by_user_id_users", "institutions", type_="foreignkey"
    )
    op.drop_column("institutions", "claimed_by_user_id")
    op.drop_column("institutions", "claimed_at")
    op.drop_column("institutions", "is_claimed")
    op.drop_column("institutions", "profile_intelligence_updated_at")
    op.drop_column("institutions", "profile_intelligence_version")
    op.drop_column("institutions", "profile_intelligence")
