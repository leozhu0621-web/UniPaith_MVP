"""session_templates — guided work-orders for the Uni advisor chat (spec §5/§6).

Hand-written; autogenerate is unreliable (env.py runs create_all). Creates
both tables only; rows are seeded idempotently from the in-code TEMPLATE_LIBRARY
constant by TemplateService.ensure_seeded (insert-if-absent), so a later
Airtable sync owns updates without re-seed clobbering.

Revision ID: sesstmpl1
Revises: scoredweights1
Create Date: 2026-06-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "sesstmpl1"  # pragma: allowlist secret
down_revision: str | None = "scoredweights1"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has(table: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _has("session_templates"):
        op.create_table(
            "session_templates",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                server_default=sa.text("gen_random_uuid()"),
                nullable=False,
            ),
            sa.Column("key", sa.String(length=40), nullable=False),
            sa.Column("title", sa.String(length=120), nullable=False),
            sa.Column("topic", sa.String(length=30), nullable=False),
            sa.Column("stage", sa.String(length=20), nullable=False),
            sa.Column("outcome", sa.String(length=160), nullable=False),
            sa.Column("icon", sa.String(length=30), nullable=False),
            sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
            sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
            sa.Column("airtable_record_id", sa.String(length=64), nullable=True),
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
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("key", name="uq_session_templates_key"),
        )
        op.create_index(
            "ix_session_templates_active_sort", "session_templates", ["active", "sort_order"]
        )

    if not _has("session_template_steps"):
        op.create_table(
            "session_template_steps",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                server_default=sa.text("gen_random_uuid()"),
                nullable=False,
            ),
            sa.Column(
                "template_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
            ),
            sa.Column("step_order", sa.Integer(), nullable=False),
            sa.Column("step_type", sa.String(length=10), nullable=False),
            sa.Column("prompt_key", sa.String(length=60), nullable=True),
            sa.Column("action_key", sa.String(length=40), nullable=True),
            sa.Column("label", sa.String(length=60), nullable=False),
            sa.Column("airtable_record_id", sa.String(length=64), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["template_id"],
                ["session_templates.id"],
                ondelete="CASCADE",
            ),
            sa.CheckConstraint(
                "step_type IN ('prompt','action')",
                name="ck_session_template_steps_type",
            ),
            sa.CheckConstraint(
                "(prompt_key IS NULL) <> (action_key IS NULL)",
                name="ck_session_template_steps_exactly_one_key",
            ),
        )
        op.create_index(
            "ix_session_template_steps_template_order",
            "session_template_steps",
            ["template_id", "step_order"],
        )


def downgrade() -> None:
    op.drop_table("session_template_steps")
    op.drop_table("session_templates")
