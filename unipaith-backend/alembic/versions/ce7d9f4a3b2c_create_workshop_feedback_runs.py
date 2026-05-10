"""Phase A — create workshop_feedback_runs.

Spec is explicit: workshops "do not generate context" — they coach. This
table backs the new feedback-only endpoints under /me/workshops. The schema
deliberately has no `revised_text` / `improved_text` / `generated_essay`
field; a CI test (test_workshop_no_generation_contract.py) will fail if any
such field ever sprouts on the response model.

Output shape per row:
  rubric_scores       — {dimension: 0..5}
  structural_issues   — [{issue, severity, location_ref}]
  missing_elements    — [{element, importance}]
  suggested_questions — [{question, why}]   (interview practice / test
                                              guidance contexts)

Domain values: 'essay' | 'interview' | 'test'. Different domains populate
different subsets of the JSONB columns.

Revision ID: ce7d9f4a3b2c
Revises: bd5c6e3f2a1b
Create Date: 2026-05-09 18:30:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "ce7d9f4a3b2c"  # pragma: allowlist secret
down_revision = "bd5c6e3f2a1b"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workshop_feedback_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Allowed values: 'essay' | 'interview' | 'test'
        sa.Column("domain", sa.String(20), nullable=False),
        # Free-form pointer back to whatever the feedback is about. For
        # essays this is a student_documents row id; for interviews it's a
        # target program id (or null for generic practice); for test
        # guidance it's a test type label.
        sa.Column("input_artifact_id", sa.String(120), nullable=True),
        # Original prompt / context the student was working against.
        sa.Column("prompt_text", sa.Text, nullable=True),
        sa.Column(
            "rubric_scores",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "structural_issues",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "missing_elements",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "suggested_questions",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        # Phase A flag: TRUE while the rule-based stub is in use. Plan 2's
        # workshop coach flips it to FALSE.
        sa.Column(
            "is_stub",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "domain IN ('essay','interview','test')",
            name="ck_workshop_feedback_runs_domain",
        ),
    )
    op.create_index(
        "ix_workshop_feedback_runs_student_domain",
        "workshop_feedback_runs",
        ["student_id", "domain", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_workshop_feedback_runs_student_domain",
        table_name="workshop_feedback_runs",
    )
    op.drop_table("workshop_feedback_runs")
