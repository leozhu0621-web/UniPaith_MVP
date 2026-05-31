"""Spec 16 (Calendar): extend student_calendar + add calendar_item_states

Spec 16 §6 gives a richer CalendarItem shape than the original
``student_calendar`` table carried, so this revision adds the missing fields
(status / category / location / meeting_link / application_id /
reminder_settings) to the student-created entries table, and creates
``calendar_item_states`` — a per-student overlay that records mark-complete /
notes / attached-confirmation on *derived* items (deadlines, interviews,
offers, events) without mutating their source domain tables.

Guarded with has_column/has_table so it is a safe no-op against a dev DB that
was built from the models via ``create_all``.

Revision ID: b7c1d9e2f3a4
Revises: a1f7c93d2e64
Create Date: 2026-05-31

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "b7c1d9e2f3a4"  # pragma: allowlist secret
down_revision = "a1f7c93d2e64"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _has_column(bind, table: str, column: str) -> bool:
    insp = sa.inspect(bind)
    try:
        return any(c["name"] == column for c in insp.get_columns(table))
    except Exception:
        return False


def _has_table(bind, table: str) -> bool:
    insp = sa.inspect(bind)
    return insp.has_table(table)


def _has_fk(bind, table: str, name: str) -> bool:
    insp = sa.inspect(bind)
    try:
        return any(fk.get("name") == name for fk in insp.get_foreign_keys(table))
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()

    # ── student_calendar: Spec 16 §6 CalendarItem fields ──
    if not _has_column(bind, "student_calendar", "status"):
        op.add_column(
            "student_calendar",
            sa.Column(
                "status",
                sa.String(length=20),
                server_default=sa.text("'scheduled'"),
                nullable=False,
            ),
        )
    if not _has_column(bind, "student_calendar", "category"):
        op.add_column(
            "student_calendar", sa.Column("category", sa.String(length=30), nullable=True)
        )
    if not _has_column(bind, "student_calendar", "location"):
        op.add_column(
            "student_calendar", sa.Column("location", sa.String(length=500), nullable=True)
        )
    if not _has_column(bind, "student_calendar", "meeting_link"):
        op.add_column(
            "student_calendar", sa.Column("meeting_link", sa.String(length=1000), nullable=True)
        )
    if not _has_column(bind, "student_calendar", "reminder_settings"):
        op.add_column(
            "student_calendar",
            sa.Column("reminder_settings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )
    if not _has_column(bind, "student_calendar", "application_id"):
        op.add_column(
            "student_calendar",
            sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
    if not _has_fk(bind, "student_calendar", "fk_student_calendar_application"):
        op.create_foreign_key(
            "fk_student_calendar_application",
            "student_calendar",
            "applications",
            ["application_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # ── calendar_item_states: per-student overlay on derived items ──
    if not _has_table(bind, "calendar_item_states"):
        op.create_table(
            "calendar_item_states",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("item_key", sa.String(length=120), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("confirmation_url", sa.String(length=1000), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
            sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("student_id", "item_key", name="uq_calendar_state_item"),
        )
        op.create_index("ix_calendar_item_states_student", "calendar_item_states", ["student_id"])


def downgrade() -> None:
    bind = op.get_bind()
    if _has_table(bind, "calendar_item_states"):
        op.drop_index("ix_calendar_item_states_student", table_name="calendar_item_states")
        op.drop_table("calendar_item_states")
    if _has_fk(bind, "student_calendar", "fk_student_calendar_application"):
        op.drop_constraint(
            "fk_student_calendar_application", "student_calendar", type_="foreignkey"
        )
    cols = (
        "application_id",
        "reminder_settings",
        "meeting_link",
        "location",
        "category",
        "status",
    )
    for col in cols:
        if _has_column(bind, "student_calendar", col):
            op.drop_column("student_calendar", col)
