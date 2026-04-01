"""add admin_audit_events table

Revision ID: 9f2b1d3c4a10
Revises: 0002, 376b5ff064cd
Create Date: 2026-04-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "9f2b1d3c4a10"
down_revision: Union[str, Sequence[str], None] = ("0002", "376b5ff064cd")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_audit_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("actor_user_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=128), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_admin_audit_events_actor_user_id"),
        "admin_audit_events",
        ["actor_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_admin_audit_events_action"),
        "admin_audit_events",
        ["action"],
        unique=False,
    )
    op.create_index(
        op.f("ix_admin_audit_events_entity_type"),
        "admin_audit_events",
        ["entity_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_admin_audit_events_entity_id"),
        "admin_audit_events",
        ["entity_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_admin_audit_events_entity_id"), table_name="admin_audit_events")
    op.drop_index(op.f("ix_admin_audit_events_entity_type"), table_name="admin_audit_events")
    op.drop_index(op.f("ix_admin_audit_events_action"), table_name="admin_audit_events")
    op.drop_index(
        op.f("ix_admin_audit_events_actor_user_id"),
        table_name="admin_audit_events",
    )
    op.drop_table("admin_audit_events")
