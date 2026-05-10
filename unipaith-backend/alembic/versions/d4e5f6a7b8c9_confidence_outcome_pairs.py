"""Phase D2 — confidence_outcome_pairs (calibrator training data).

See `unipaith.models.confidence_outcome` for the design rationale.

Revision ID: d4e5f6a7b8c9
Revises: c2d3e4f5a6b7
Create Date: 2026-05-10 21:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "d4e5f6a7b8c9"  # pragma: allowlist secret
down_revision = "c2d3e4f5a6b7"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "confidence_outcome_pairs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("programs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("predicted_confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("outcome", sa.SmallInteger(), nullable=False),
        sa.Column("outcome_kind", sa.String(20), nullable=False),
        sa.Column("matched_at", sa.DateTime(timezone=True)),
        sa.Column(
            "event_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("outcome IN (0, 1)", name="ck_cop_outcome_binary"),
        sa.CheckConstraint(
            "outcome_kind IN ('applied', 'accepted', 'enrolled', 'aged_out')",
            name="ck_cop_outcome_kind",
        ),
    )
    op.create_index(
        "ix_cop_kind_created",
        "confidence_outcome_pairs",
        ["outcome_kind", "created_at"],
    )
    op.create_index(
        "ix_cop_student",
        "confidence_outcome_pairs",
        ["student_id"],
    )
    op.create_index(
        "ix_cop_program",
        "confidence_outcome_pairs",
        ["program_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_cop_program", table_name="confidence_outcome_pairs")
    op.drop_index("ix_cop_student", table_name="confidence_outcome_pairs")
    op.drop_index("ix_cop_kind_created", table_name="confidence_outcome_pairs")
    op.drop_table("confidence_outcome_pairs")
