"""add institution_follows table and institutions.founded_year (+ merge heads)

Spec 12 (School Detail page): explicit institution Follow that drives the
Connect feed independent of saved programs, plus a founded_year column so the
header can render "Founded 1831" per spec §2.

This revision also MERGES the two divergent Alembic heads that exist on main
(``d4e6f8a0b2c4`` add_student_compare_items — itself a child of
``c8e4a2b1f9d3`` add_consent_training_lever — and ``df8e1c5b4a3d``
extend_student_profile_summaries) so ``alembic upgrade head`` is unambiguous.
After this revision the lineage has a single head again.

Revision ID: a1f7c93d2e64
Revises: d4e6f8a0b2c4, df8e1c5b4a3d
Create Date: 2026-05-31

"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1f7c93d2e64"
# Tuple down_revision → this is also a merge of the two prior heads.
down_revision = ("d4e6f8a0b2c4", "df8e1c5b4a3d")
branch_labels = None
depends_on = None


def _has_column(bind, table: str, column: str) -> bool:
    insp = sa.inspect(bind)
    try:
        return any(c["name"] == column for c in insp.get_columns(table))
    except Exception:
        return False


def _has_table(bind, table: str) -> bool:
    insp = sa.inspect(bind)
    return insp.has_table(table)


def upgrade() -> None:
    bind = op.get_bind()

    # founded_year — institution founding year (nullable; header shows it when set).
    # Guarded so it is a no-op if a dev DB built via create_all already has it.
    if not _has_column(bind, "institutions", "founded_year"):
        op.add_column(
            "institutions",
            sa.Column("founded_year", sa.Integer(), nullable=True),
        )

    # institution_follows — explicit student → institution follow.
    if not _has_table(bind, "institution_follows"):
        op.create_table(
            "institution_follows",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["student_id"], ["student_profiles.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["institution_id"], ["institutions.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "student_id", "institution_id", name="uq_institution_follow"
            ),
        )
        op.create_index(
            "ix_institution_follows_student", "institution_follows", ["student_id"]
        )
        op.create_index(
            "ix_institution_follows_institution",
            "institution_follows",
            ["institution_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_table(bind, "institution_follows"):
        op.drop_index(
            "ix_institution_follows_institution", table_name="institution_follows"
        )
        op.drop_index("ix_institution_follows_student", table_name="institution_follows")
        op.drop_table("institution_follows")
    if _has_column(bind, "institutions", "founded_year"):
        op.drop_column("institutions", "founded_year")
