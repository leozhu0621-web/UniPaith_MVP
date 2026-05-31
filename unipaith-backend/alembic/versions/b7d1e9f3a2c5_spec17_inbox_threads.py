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
Inbox "Mark complete" reuses mechanisms already on main rather than adding
parallel columns:
- checklist completion → the Spec 15 per-item ``manual_complete`` flag
  (durable across ``generate_checklist`` via ``_load_manual_keys``).
- the linked calendar deadline → the Spec 16 ``student_calendar.status``
  column (set to ``completed``); linkage via the existing ``reference_id``
  (= thread id).

Chains off ``b7c1d9e2f3a4`` (Spec 16 calendar), the single head after the
Spec 13/15/16 merge.

Revision ID: b7d1e9f3a2c5
Revises: b7c1d9e2f3a4
Create Date: 2026-05-31

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "b7d1e9f3a2c5"
down_revision = "b7c1d9e2f3a4"
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

    # Mark-complete propagation reuses mechanisms already on main:
    #   - checklist item completion → Spec 15 ``manual_complete`` (JSONB flag)
    #   - linked calendar deadline → Spec 16 ``student_calendar.status``
    # so no new checklist/calendar columns are added here.

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
