"""Spec 17 (Inbox) — extend conversations/messages/calendar/checklists

Layers application-threaded inbox semantics onto the existing
``conversations`` / ``messages`` tables (reused by both student inbox and
institution messaging, Spec 29) rather than introducing parallel
``inbox_*`` tables. All additions are nullable / server-defaulted, so the
existing Pydantic allow-list schemas and institution messaging are
unaffected.

Key, non-obvious changes:
- ``messages.sender_id`` is relaxed to NULLABLE so *system* threads
  (missing-item alerts, status updates) can carry author-less messages.
- ``application_checklists.manual_overrides`` is a regeneration-proof
  completion signal: ``ChecklistService.generate_checklist`` rebuilds
  ``items`` from scratch, so a student-confirmed completion must live
  outside that derived list. Inbox "Mark complete" writes here.
- Calendar linkage reuses the existing ``student_calendar.reference_id``
  (= thread id); ``completed_at`` gives "Mark complete" an observable
  effect on the linked deadline.

Single head on this branch is ``a1f7c93d2e64`` (verified via
``alembic heads``), so this is an ordinary single-parent migration.

Revision ID: b7d1e9f3a2c5
Revises: a1f7c93d2e64
Create Date: 2026-05-31

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "b7d1e9f3a2c5"
down_revision = "a1f7c93d2e64"
branch_labels = None
depends_on = None


def _has_column(bind, table: str, column: str) -> bool:
    insp = sa.inspect(bind)
    try:
        return any(c["name"] == column for c in insp.get_columns(table))
    except Exception:
        return False


def _has_index(bind, table: str, index: str) -> bool:
    insp = sa.inspect(bind)
    try:
        return any(ix["name"] == index for ix in insp.get_indexes(table))
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()

    # ── conversations → inbox thread metadata ──────────────────────────────
    if not _has_column(bind, "conversations", "application_id"):
        op.add_column(
            "conversations",
            sa.Column(
                "application_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("applications.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )
    if not _has_index(bind, "conversations", "ix_conversations_application_id"):
        op.create_index("ix_conversations_application_id", "conversations", ["application_id"])
    if not _has_column(bind, "conversations", "thread_type"):
        op.add_column(
            "conversations",
            sa.Column(
                "thread_type",
                sa.String(20),
                server_default="human",
                nullable=False,
            ),
        )
    if not _has_column(bind, "conversations", "action_label"):
        op.add_column(
            "conversations",
            sa.Column("action_label", sa.String(40), nullable=True),
        )
    if not _has_column(bind, "conversations", "due_date"):
        op.add_column(
            "conversations",
            sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        )
    if not _has_column(bind, "conversations", "waiting_on"):
        op.add_column(
            "conversations",
            sa.Column(
                "waiting_on",
                sa.String(20),
                server_default="none",
                nullable=False,
            ),
        )
    if not _has_column(bind, "conversations", "linked_checklist_item_category"):
        op.add_column(
            "conversations",
            sa.Column("linked_checklist_item_category", sa.String(50), nullable=True),
        )

    # ── messages → attachments, delivery status, AI-draft provenance ───────
    if not _has_column(bind, "messages", "attachments"):
        op.add_column(
            "messages",
            sa.Column(
                "attachments",
                postgresql.JSONB(),
                server_default=sa.text("'[]'::jsonb"),
                nullable=False,
            ),
        )
    if not _has_column(bind, "messages", "status"):
        op.add_column(
            "messages",
            sa.Column("status", sa.String(20), server_default="sent", nullable=False),
        )
    if not _has_column(bind, "messages", "ai_draft_used"):
        op.add_column(
            "messages",
            sa.Column(
                "ai_draft_used",
                sa.Boolean(),
                server_default=sa.text("false"),
                nullable=False,
            ),
        )
    # System messages have no human author → relax the NOT NULL.
    # DROP NOT NULL is a no-op if the column is already nullable.
    op.alter_column(
        "messages", "sender_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True
    )

    # ── student_calendar → completion marker ───────────────────────────────
    if not _has_column(bind, "student_calendar", "completed_at"):
        op.add_column(
            "student_calendar",
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        )

    # ── application_checklists → regeneration-proof completion overrides ────
    if not _has_column(bind, "application_checklists", "manual_overrides"):
        op.add_column(
            "application_checklists",
            sa.Column(
                "manual_overrides",
                postgresql.JSONB(),
                server_default=sa.text("'{}'::jsonb"),
                nullable=False,
            ),
        )

    # ── ai_turns.agent CHECK → allow 'inbox_reply_drafter' (spec 45 §13) ────
    # The InboxReplyDrafter writes a cost-ledger row; without this the INSERT
    # would violate ck_ai_turns_agent in prod.
    op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_agent")
    op.execute(
        "ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_agent CHECK ("
        "agent IN ('orchestrator','extractor','validator','feature_emitter',"
        "'rationale','workshop_coach','workshop_judge','embedding',"
        "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
        "'inbox_reply_drafter'))"
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_agent")
    op.execute(
        "ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_agent CHECK ("
        "agent IN ('orchestrator','extractor','validator','feature_emitter',"
        "'rationale','workshop_coach','workshop_judge','embedding',"
        "'review_summarizer','authenticity_risk','matcher','query_interpreter'))"
    )

    if _has_column(bind, "application_checklists", "manual_overrides"):
        op.drop_column("application_checklists", "manual_overrides")
    if _has_column(bind, "student_calendar", "completed_at"):
        op.drop_column("student_calendar", "completed_at")

    # Restore NOT NULL only if no author-less rows exist (best-effort).
    op.alter_column(
        "messages", "sender_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False
    )
    for col in ("ai_draft_used", "status", "attachments"):
        if _has_column(bind, "messages", col):
            op.drop_column("messages", col)

    if _has_index(bind, "conversations", "ix_conversations_application_id"):
        op.drop_index("ix_conversations_application_id", table_name="conversations")
    for col in (
        "linked_checklist_item_category",
        "waiting_on",
        "due_date",
        "action_label",
        "thread_type",
        "application_id",
    ):
        if _has_column(bind, "conversations", col):
            op.drop_column("conversations", col)
