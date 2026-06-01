"""Spec 30 — Institution setup wizard orchestration fields.

Adds setup_complete, setup_step, setup_steps_complete, and first_program_id
to institutions. Backfills setup_complete for existing rows that already have
programs.

Revision ID: d30e4f5a6b7c  # pragma: allowlist secret
Revises: c29a1b2d3e4f  # pragma: allowlist secret
Create Date: 2026-06-01

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "d30e4f5a6b7c"  # pragma: allowlist secret
down_revision = "c29a1b2d3e4f"  # pragma: allowlist secret
branch_labels = None
depends_on = None

_DEFAULT_STEPS = '{"profile": false, "program": false, "data": false, "team": false}'


def upgrade() -> None:
    op.add_column(
        "institutions",
        sa.Column(
            "setup_complete",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "institutions",
        sa.Column(
            "setup_step",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )
    op.add_column(
        "institutions",
        sa.Column(
            "setup_steps_complete",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text(f"'{_DEFAULT_STEPS}'::jsonb"),
        ),
    )
    op.add_column(
        "institutions",
        sa.Column("first_program_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Existing institutions with programs are treated as setup-complete.
    op.execute(
        sa.text(
            """
            UPDATE institutions i
            SET setup_complete = true,
                setup_step = 4,
                setup_steps_complete = (
                    '{"profile": true, "program": true, "data": false, "team": false}'::jsonb
                ),
                first_program_id = (
                    SELECT p.id FROM programs p
                    WHERE p.institution_id = i.id
                    ORDER BY p.created_at ASC
                    LIMIT 1
                )
            WHERE EXISTS (
                SELECT 1 FROM programs p WHERE p.institution_id = i.id
            )
            """
        )
    )

    # Institutions without programs but with a profile still need the wizard.
    op.execute(
        sa.text(
            """
            UPDATE institutions i
            SET setup_steps_complete = jsonb_set(
                COALESCE(setup_steps_complete, '{}'::jsonb),
                '{profile}',
                'true'::jsonb
            )
            WHERE NOT setup_complete
            """
        )
    )


def downgrade() -> None:
    op.drop_column("institutions", "first_program_id")
    op.drop_column("institutions", "setup_steps_complete")
    op.drop_column("institutions", "setup_step")
    op.drop_column("institutions", "setup_complete")
