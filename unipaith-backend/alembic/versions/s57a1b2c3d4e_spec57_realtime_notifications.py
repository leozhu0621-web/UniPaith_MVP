"""Spec 57 §3/§4/§6 — realtime notification columns.

Extends ``notifications`` with the three columns the fan-out + digest path needs:

- ``event_id``        — idempotency key; a repeated hook writes one row. A partial
                        unique index enforces it (NULLs, the legacy rows, don't collide).
- ``urgency``         — ``urgent`` (immediate) | ``digest`` (batched, §6). Defaults
                        urgent so every existing row keeps firing right away.
- ``delivery_status`` — per-channel outcomes ({channel: sent|failed|...}) the
                        delivery wrapper writes for observability + the DLQ.

Plus the index the digest sweep scans by. All adds are guarded (column / index
existence) so the migration is a safe no-op against a dev/test DB built from the
models via ``create_all`` (conftest path), and re-runnable in prod.

Revision ID: s57a1b2c3d4e
Revises: s56a1b2c3d4e
Create Date: 2026-06-02

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "s57a1b2c3d4e"  # pragma: allowlist secret
# s56a1b2c3d4e (Spec 56 saved-searches) is the single head at branch time; chain
# off it to keep the graph single-headed (test_alembic_has_single_head).
down_revision = "s56a1b2c3d4e"  # pragma: allowlist secret
branch_labels = None
depends_on = None

_TABLE = "notifications"


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return any(c["name"] == column for c in insp.get_columns(table))


def _has_index(table: str, name: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return any(ix["name"] == name for ix in insp.get_indexes(table))


def upgrade() -> None:
    if not _has_column(_TABLE, "event_id"):
        op.add_column(_TABLE, sa.Column("event_id", sa.String(length=200), nullable=True))
    if not _has_column(_TABLE, "urgency"):
        op.add_column(
            _TABLE,
            sa.Column(
                "urgency",
                sa.String(length=20),
                nullable=False,
                server_default="urgent",
            ),
        )
    if not _has_column(_TABLE, "delivery_status"):
        op.add_column(
            _TABLE,
            sa.Column(
                "delivery_status",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
        )

    if not _has_index(_TABLE, "uq_notifications_event_id"):
        # Partial unique — only non-NULL event_ids must be unique (idempotency).
        op.create_index(
            "uq_notifications_event_id",
            _TABLE,
            ["event_id"],
            unique=True,
            postgresql_where=sa.text("event_id IS NOT NULL"),
        )
    if not _has_index(_TABLE, "ix_notifications_user_urgency_emailed"):
        op.create_index(
            "ix_notifications_user_urgency_emailed",
            _TABLE,
            ["user_id", "urgency", "is_emailed"],
        )


def downgrade() -> None:
    if _has_index(_TABLE, "ix_notifications_user_urgency_emailed"):
        op.drop_index("ix_notifications_user_urgency_emailed", table_name=_TABLE)
    if _has_index(_TABLE, "uq_notifications_event_id"):
        op.drop_index("uq_notifications_event_id", table_name=_TABLE)
    for col in ("delivery_status", "urgency", "event_id"):
        if _has_column(_TABLE, col):
            op.drop_column(_TABLE, col)
