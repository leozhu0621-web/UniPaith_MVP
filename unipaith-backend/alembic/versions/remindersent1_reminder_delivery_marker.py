"""add student_calendar.reminder_sent_at + suppress pre-deploy backlog

``reminder_at`` rows were persisted but never delivered (no scheduler job read
them). The new reminder-delivery loop stamps ``reminder_sent_at`` once a
reminder is delivered so it never re-sends. Backfill: stamp every
already-overdue reminder as sent so enabling the loop doesn't blast the
historical backlog — only reminders that come due AFTER this deploy fire.

Revision ID: remindersent1
Revises: purduewhotuition1
Create Date: 2026-06-26
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "remindersent1"
down_revision = "purduewhotuition1"
branch_labels = None
depends_on = None

_TABLE = "student_calendar"
_COL = "reminder_sent_at"
_IX = "ix_student_calendar_pending_reminders"


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return any(c["name"] == column for c in insp.get_columns(table))


def _has_index(table: str, name: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return any(ix["name"] == name for ix in insp.get_indexes(table))


def upgrade() -> None:
    if not _has_column(_TABLE, _COL):
        op.add_column(_TABLE, sa.Column(_COL, sa.DateTime(timezone=True), nullable=True))
    # Suppress the pre-deploy backlog: stamp every reminder already due so the
    # newly-enabled delivery loop only fires reminders that come due after this
    # deploy (no flood of historical reminders).
    op.execute(
        "UPDATE student_calendar SET reminder_sent_at = now() "
        "WHERE reminder_at IS NOT NULL AND reminder_at <= now() "
        "AND reminder_sent_at IS NULL"
    )
    if not _has_index(_TABLE, _IX):
        # Partial index — the delivery loop scans only pending (un-sent) reminders.
        op.create_index(
            _IX,
            _TABLE,
            ["reminder_at"],
            unique=False,
            postgresql_where=sa.text("reminder_sent_at IS NULL"),
        )


def downgrade() -> None:
    if _has_index(_TABLE, _IX):
        op.drop_index(_IX, table_name=_TABLE)
    if _has_column(_TABLE, _COL):
        op.drop_column(_TABLE, _COL)
