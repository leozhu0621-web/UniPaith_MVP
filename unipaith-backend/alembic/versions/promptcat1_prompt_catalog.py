"""prompt_catalog — the data-driven Prompt Library (widget spec §6)

Hand-written; autogenerate is unreliable (env.py runs create_all). Creates the
table only; rows are seeded idempotently from the in-code CATALOG snapshot by
CatalogService.ensure_seeded (insert-if-absent), so a later Airtable sync owns
updates without re-seed clobbering.

Revision ID: promptcat1
Revises: nwdefab1
Create Date: 2026-06-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "promptcat1"  # pragma: allowlist secret
down_revision: str | None = "nwdefab1"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has(table: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if _has("prompt_catalog"):
        return
    op.create_table(
        "prompt_catalog",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("key", sa.String(length=60), nullable=False),
        sa.Column("section", sa.String(length=40), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("ask_kind", sa.String(length=20), nullable=False),
        sa.Column("value_type", sa.String(length=20), nullable=False),
        sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tier", sa.String(length=20), nullable=False),
        sa.Column("required", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "display_logic",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("saves_to", sa.String(length=60), nullable=False),
        sa.Column("reference_source", sa.String(length=40), nullable=True),
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
        sa.UniqueConstraint("key", name="uq_prompt_catalog_key"),
    )
    op.create_index("ix_prompt_catalog_active_sort", "prompt_catalog", ["active", "sort_order"])


def downgrade() -> None:
    op.drop_table("prompt_catalog")
