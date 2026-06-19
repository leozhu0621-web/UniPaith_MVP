"""Add the external scholarships catalog table (Spec 2026-06-14).

Creates ``external_scholarships`` — the 9,500-row CareerOneStop scholarship
catalog that backs Resources › Financial. Columns are written by hand to match
``models/scholarship.py::Scholarship`` exactly (a unique index on
``external_id`` drives the idempotent re-seed; ``level_of_study`` is indexed for
the "for your level" matches query).

The table is ``external_scholarships`` (not ``scholarships``) because Spec 60
already owns ``scholarships`` (institution/program-linked reference awards).

Revision ID: schol1a2b3c4d
Revises: uclaprof5
Create Date: 2026-06-14
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "schol1a2b3c4d"
# Re-pointed to chain after each concurrent head as it landed on main
# (uclaprof5 → stanfordprof11 → progprefbf1). The table is purely additive, so
# chaining after the latest head is always safe.
down_revision = "progprefbf1"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return sa.inspect(bind).has_table(name)


def upgrade() -> None:
    if _has_table("external_scholarships"):
        return
    op.create_table(
        "external_scholarships",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("external_id", sa.String(32), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("organization", sa.String(500), nullable=True),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("level_of_study", sa.String(300), nullable=True),
        sa.Column("award_type", sa.String(120), nullable=True),
        sa.Column("award_amount", sa.String(200), nullable=True),
        sa.Column("deadline", sa.String(120), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("source", sa.String(60), nullable=False, server_default="careeronestop"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_external_scholarships_external_id",
        "external_scholarships",
        ["external_id"],
        unique=True,
    )
    op.create_index(
        "ix_external_scholarships_level_of_study",
        "external_scholarships",
        ["level_of_study"],
    )


def downgrade() -> None:
    op.drop_index("ix_external_scholarships_level_of_study", table_name="external_scholarships")
    op.drop_index("ix_external_scholarships_external_id", table_name="external_scholarships")
    op.drop_table("external_scholarships")
