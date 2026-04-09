"""add institution_posts table

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "b2c3d4e5f6g7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "institution_posts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("institution_id", UUID(as_uuid=True),
                  sa.ForeignKey("institutions.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("author_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("media_urls", JSONB()),
        sa.Column("pinned", sa.Boolean(), server_default="false"),
        sa.Column("tagged_program_ids", JSONB()),
        sa.Column("tagged_intake", sa.String(50)),
        sa.Column("status", sa.String(20), server_default="draft"),
        sa.Column("scheduled_for", sa.DateTime(timezone=True)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("is_template", sa.Boolean(), server_default="false"),
        sa.Column("template_name", sa.String(255)),
        sa.Column("view_count", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_institution_posts_inst_status",
        "institution_posts",
        ["institution_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_institution_posts_inst_status", table_name="institution_posts")
    op.drop_table("institution_posts")
