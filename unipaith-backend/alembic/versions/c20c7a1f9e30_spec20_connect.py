"""Spec 20 (Connect): follow graph + events + peers schema

Schema for the Connect surface (Stage 3a):
- ``institution_follows`` gains ``program_id`` / ``source`` / ``muted``
  (Spec 20 §2 following model — auto-follow on save/apply, mute).
- ``events`` gains ``meeting_link`` (Spec 20 §5 — revealed to RSVP'd students).
- ``student_data_consent`` gains ``consent_peer_connect`` (Spec 20 §6.1 /
  §11 — a NEW consent dimension, default false, revocable).
- ``conversations`` gains ``thread_type`` + ``peer_student_id`` (Spec 20 §6.3
  — a NEW ``peer`` Inbox thread type).
- NEW ``peer_profiles`` / ``peer_connections`` / ``peer_reports`` tables for the
  opt-in, privacy-gated Peers tab (Spec 20 §6).

Guarded with has_column/has_table so it is a safe no-op against a dev/test DB
that was built from the models via ``create_all``.

Revision ID: c20c7a1f9e30
Revises: b7c1d9e2f3a4
Create Date: 2026-05-31

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "c20c7a1f9e30"  # pragma: allowlist secret
down_revision = "b7c1d9e2f3a4"  # pragma: allowlist secret
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


# Spec 20 §8 — widen ai_turns.agent CHECK for the two new Connect agents.
_NEW_AGENT_CHECK = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'connect_ranker','event_recommender')"
)
_OLD_AGENT_CHECK = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter')"
)


def upgrade() -> None:
    bind = op.get_bind()

    # ── ai_turns.agent CHECK: allow connect_ranker + event_recommender (§8) ──
    op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_agent")
    op.execute(f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_agent CHECK ({_NEW_AGENT_CHECK})")

    # ── institution_follows: Spec 20 §2 following model ──
    if not _has_column(bind, "institution_follows", "program_id"):
        op.add_column(
            "institution_follows",
            sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
    if not _has_fk(bind, "institution_follows", "fk_institution_follows_program"):
        op.create_foreign_key(
            "fk_institution_follows_program",
            "institution_follows",
            "programs",
            ["program_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if not _has_column(bind, "institution_follows", "source"):
        op.add_column(
            "institution_follows",
            sa.Column(
                "source",
                sa.String(length=20),
                server_default=sa.text("'explicit'"),
                nullable=False,
            ),
        )
    if not _has_column(bind, "institution_follows", "muted"):
        op.add_column(
            "institution_follows",
            sa.Column(
                "muted",
                sa.Boolean(),
                server_default=sa.text("false"),
                nullable=False,
            ),
        )

    # ── events: Spec 20 §5 meeting link ──
    if not _has_column(bind, "events", "meeting_link"):
        op.add_column("events", sa.Column("meeting_link", sa.String(length=1000), nullable=True))

    # ── student_data_consent: Spec 20 §6.1 peer-connect consent dimension ──
    if not _has_column(bind, "student_data_consent", "consent_peer_connect"):
        op.add_column(
            "student_data_consent",
            sa.Column(
                "consent_peer_connect",
                sa.Boolean(),
                server_default=sa.text("false"),
                nullable=False,
            ),
        )

    # ── conversations: Spec 20 §6.3 peer thread type ──
    if not _has_column(bind, "conversations", "thread_type"):
        op.add_column(
            "conversations",
            sa.Column(
                "thread_type",
                sa.String(length=20),
                server_default=sa.text("'human'"),
                nullable=True,
            ),
        )
    if not _has_column(bind, "conversations", "peer_student_id"):
        op.add_column(
            "conversations",
            sa.Column("peer_student_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
    if not _has_fk(bind, "conversations", "fk_conversations_peer_student"):
        op.create_foreign_key(
            "fk_conversations_peer_student",
            "conversations",
            "student_profiles",
            ["peer_student_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # ── peer_profiles: Spec 20 §6.2 peer-visibility sub-profile ──
    if not _has_table(bind, "peer_profiles"):
        op.create_table(
            "peer_profiles",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("display_name", sa.String(length=120), nullable=True),
            sa.Column("use_alias", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("intended_major", sa.String(length=150), nullable=True),
            sa.Column("region", sa.String(length=120), nullable=True),
            sa.Column("bio", sa.Text(), nullable=True),
            sa.Column(
                "share_targets", sa.Boolean(), server_default=sa.text("true"), nullable=False
            ),
            sa.Column("visible", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
            sa.UniqueConstraint("student_id", name="uq_peer_profile_student"),
        )

    # ── peer_connections: Spec 20 §6.3 connect requests ──
    if not _has_table(bind, "peer_connections"):
        op.create_table(
            "peer_connections",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("requester_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("addressee_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "status",
                sa.String(length=20),
                server_default=sa.text("'requested'"),
                nullable=False,
            ),
            sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
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
            sa.ForeignKeyConstraint(["requester_id"], ["student_profiles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["addressee_id"], ["student_profiles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("requester_id", "addressee_id", name="uq_peer_connection_pair"),
        )
        op.create_index("ix_peer_connections_addressee", "peer_connections", ["addressee_id"])
        op.create_index("ix_peer_connections_requester", "peer_connections", ["requester_id"])

    # ── peer_reports: Spec 20 §6.3 moderation queue ──
    if not _has_table(bind, "peer_reports"):
        op.create_table(
            "peer_reports",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("reporter_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("reported_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("reason", sa.String(length=50), nullable=True),
            sa.Column("detail", sa.Text(), nullable=True),
            sa.Column(
                "status", sa.String(length=20), server_default=sa.text("'open'"), nullable=False
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["reporter_id"], ["student_profiles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["reported_id"], ["student_profiles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_peer_reports_status", "peer_reports", ["status"])


def downgrade() -> None:
    bind = op.get_bind()
    op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_agent")
    op.execute(f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_agent CHECK ({_OLD_AGENT_CHECK})")
    if _has_table(bind, "peer_reports"):
        op.drop_table("peer_reports")
    if _has_table(bind, "peer_connections"):
        op.drop_table("peer_connections")
    if _has_table(bind, "peer_profiles"):
        op.drop_table("peer_profiles")
    if _has_fk(bind, "conversations", "fk_conversations_peer_student"):
        op.drop_constraint("fk_conversations_peer_student", "conversations", type_="foreignkey")
    for col in ("peer_student_id", "thread_type"):
        if _has_column(bind, "conversations", col):
            op.drop_column("conversations", col)
    if _has_column(bind, "student_data_consent", "consent_peer_connect"):
        op.drop_column("student_data_consent", "consent_peer_connect")
    if _has_column(bind, "events", "meeting_link"):
        op.drop_column("events", "meeting_link")
    if _has_fk(bind, "institution_follows", "fk_institution_follows_program"):
        op.drop_constraint(
            "fk_institution_follows_program", "institution_follows", type_="foreignkey"
        )
    for col in ("muted", "source", "program_id"):
        if _has_column(bind, "institution_follows", col):
            op.drop_column("institution_follows", col)
