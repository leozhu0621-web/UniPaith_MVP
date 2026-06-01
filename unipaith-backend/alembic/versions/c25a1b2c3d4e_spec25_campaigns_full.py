"""Spec 25 (Campaigns — institution outbound): full campaign shape

Brings the legacy v0 campaign tables up to the Spec 25 contract:

* ``campaigns`` gains objective / owner / destination / cta_type / channels /
  associate_program_ids / associate_intake_round_id / audience_* / sent_count
  and the §7 approval columns. Legacy columns (program_id, segment_id,
  campaign_type, message_*) are retained and dual-written for back-compat.
* ``campaign_recipients`` becomes channel-aware and can hold uploaded-list
  contacts (student_id nullable) plus per-recipient unsubscribe/bounce/fail
  state so the §8 metrics shape can be computed.
* ``target_segments`` gains description / uploaded_list_ids / frequency cap.
* ``institutions`` gains require_campaign_approval (§7 toggle).
* New tables: ``uploaded_lists``, ``uploaded_contacts``,
  ``campaign_suppressions`` (§4 external opt-out / suppression).
* ``ck_ai_turns_agent`` CHECK extended with 'campaign_copy' (Spec 45 §16).

Every step is guarded with has_column / has_table / has_index so the migration
is a safe no-op against a dev/test DB built from the models via ``create_all``.

Revision ID: c25a1b2c3d4e
Revises: a8263041209b
Create Date: 2026-05-31

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "c25a1b2c3d4e"  # pragma: allowlist secret
down_revision = "a8263041209b"  # pragma: allowlist secret
branch_labels = None
depends_on = None


# ── idempotency helpers ────────────────────────────────────────────────────
def _insp(bind):
    return sa.inspect(bind)


def _has_table(bind, table: str) -> bool:
    try:
        return _insp(bind).has_table(table)
    except Exception:
        return False


def _has_column(bind, table: str, column: str) -> bool:
    try:
        return any(c["name"] == column for c in _insp(bind).get_columns(table))
    except Exception:
        return False


def _has_index(bind, table: str, index: str) -> bool:
    try:
        return any(i["name"] == index for i in _insp(bind).get_indexes(table))
    except Exception:
        return False


_CAMPAIGN_COLS: list[tuple[str, sa.types.TypeEngine, dict]] = [
    ("objective", sa.String(40), {}),
    ("owner_id", postgresql.UUID(as_uuid=True), {}),
    ("destination_type", sa.String(40), {}),
    ("destination_id", postgresql.UUID(as_uuid=True), {}),
    ("destination_url", sa.String(1000), {}),
    ("cta_type", sa.String(30), {}),
    ("channels", postgresql.JSONB(), {}),
    ("associate_program_ids", postgresql.JSONB(), {}),
    ("associate_intake_round_id", postgresql.UUID(as_uuid=True), {}),
    ("audience_segment_ids", postgresql.JSONB(), {}),
    ("audience_uploaded_list_ids", postgresql.JSONB(), {}),
    ("audience_deduped_count", sa.Integer(), {}),
    ("sent_count", sa.Integer(), {}),
    ("submitted_for_approval_at", sa.DateTime(timezone=True), {}),
    ("approved_by", postgresql.UUID(as_uuid=True), {}),
    ("approved_at", sa.DateTime(timezone=True), {}),
    ("rejection_comment", sa.Text(), {}),
]

_RECIPIENT_COLS: list[tuple[str, sa.types.TypeEngine]] = [
    ("uploaded_contact_id", postgresql.UUID(as_uuid=True)),
    ("email", sa.String(320)),
    ("first_name", sa.String(255)),
    ("last_name", sa.String(255)),
    ("channel", sa.String(20)),
    ("unsubscribed_at", sa.DateTime(timezone=True)),
    ("bounced_at", sa.DateTime(timezone=True)),
    ("failed_at", sa.DateTime(timezone=True)),
    ("failure_reason", sa.String(255)),
]

_AGENT_NAMES = [
    "orchestrator",
    "extractor",
    "validator",
    "feature_emitter",
    "rationale",
    "workshop_coach",
    "workshop_judge",
    "embedding",
    "review_summarizer",
    "authenticity_risk",
    "matcher",
    "query_interpreter",
    "inbox_reply_drafter",
    "connect_ranker",
    "event_recommender",
]


def _agent_check_sql(names: list[str]) -> str:
    quoted = ",".join(f"'{n}'" for n in names)
    return f"agent IN ({quoted})"


def upgrade() -> None:
    bind = op.get_bind()

    # ── uploaded_lists ─────────────────────────────────────────────────────
    if not _has_table(bind, "uploaded_lists"):
        op.create_table(
            "uploaded_lists",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "institution_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("institutions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text()),
            sa.Column("source", sa.String(30), nullable=False, server_default="csv_upload"),
            sa.Column(
                "source_consent_confirmed",
                sa.Boolean(),
                nullable=False,
                server_default="false",
            ),
            sa.Column(
                "dataset_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("institution_datasets.id", ondelete="SET NULL"),
            ),
            sa.Column("contact_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "created_by",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )

    # ── uploaded_contacts ──────────────────────────────────────────────────
    if not _has_table(bind, "uploaded_contacts"):
        op.create_table(
            "uploaded_contacts",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "list_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("uploaded_lists.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "institution_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("institutions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("email", sa.String(320), nullable=False),
            sa.Column("first_name", sa.String(255)),
            sa.Column("last_name", sa.String(255)),
            sa.Column("extra", postgresql.JSONB()),
            sa.Column("opted_out", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("opted_out_at", sa.DateTime(timezone=True)),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
    if not _has_index(bind, "uploaded_contacts", "ix_uploaded_contacts_list"):
        op.create_index("ix_uploaded_contacts_list", "uploaded_contacts", ["list_id"])
    if not _has_index(bind, "uploaded_contacts", "ix_uploaded_contacts_inst_email"):
        op.create_index(
            "ix_uploaded_contacts_inst_email", "uploaded_contacts", ["institution_id", "email"]
        )

    # ── campaign_suppressions ──────────────────────────────────────────────
    if not _has_table(bind, "campaign_suppressions"):
        op.create_table(
            "campaign_suppressions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "institution_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("institutions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("email", sa.String(320), nullable=False),
            sa.Column("reason", sa.String(30)),
            sa.Column(
                "source_campaign_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("campaigns.id", ondelete="SET NULL"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.UniqueConstraint(
                "institution_id", "email", name="uq_campaign_suppression_inst_email"
            ),
        )
    if not _has_index(bind, "campaign_suppressions", "ix_campaign_suppressions_inst"):
        op.create_index(
            "ix_campaign_suppressions_inst", "campaign_suppressions", ["institution_id"]
        )

    # ── institutions.require_campaign_approval ─────────────────────────────
    if not _has_column(bind, "institutions", "require_campaign_approval"):
        op.add_column(
            "institutions",
            sa.Column(
                "require_campaign_approval",
                sa.Boolean(),
                nullable=False,
                server_default="false",
            ),
        )

    # ── target_segments extensions ─────────────────────────────────────────
    if not _has_column(bind, "target_segments", "description"):
        op.add_column("target_segments", sa.Column("description", sa.Text()))
    if not _has_column(bind, "target_segments", "uploaded_list_ids"):
        op.add_column("target_segments", sa.Column("uploaded_list_ids", postgresql.JSONB()))
    if not _has_column(bind, "target_segments", "frequency_cap_per_week"):
        op.add_column("target_segments", sa.Column("frequency_cap_per_week", sa.Integer()))

    # ── campaigns extensions ───────────────────────────────────────────────
    for name, col_type, _ in _CAMPAIGN_COLS:
        if not _has_column(bind, "campaigns", name):
            op.add_column("campaigns", sa.Column(name, col_type))
    # FKs for the new campaign columns (best-effort; skipped if already present).
    _add_fk_safe(
        bind, "fk_campaigns_owner_id_users", "campaigns", "users", ["owner_id"], ["id"], "SET NULL"
    )
    _add_fk_safe(
        bind,
        "fk_campaigns_approved_by_users",
        "campaigns",
        "users",
        ["approved_by"],
        ["id"],
        "SET NULL",
    )
    _add_fk_safe(
        bind,
        "fk_campaigns_intake_round",
        "campaigns",
        "intake_rounds",
        ["associate_intake_round_id"],
        ["id"],
        "SET NULL",
    )

    # ── campaign_recipients extensions ─────────────────────────────────────
    # student_id becomes nullable (uploaded-list contacts have no student).
    if _has_column(bind, "campaign_recipients", "student_id"):
        try:
            op.alter_column("campaign_recipients", "student_id", nullable=True)
        except Exception:
            pass
    for name, col_type in _RECIPIENT_COLS:
        if not _has_column(bind, "campaign_recipients", name):
            op.add_column("campaign_recipients", sa.Column(name, col_type))
    _add_fk_safe(
        bind,
        "fk_campaign_recipients_uploaded_contact",
        "campaign_recipients",
        "uploaded_contacts",
        ["uploaded_contact_id"],
        ["id"],
        "SET NULL",
    )
    if not _has_index(bind, "campaign_recipients", "ix_campaign_recipients_campaign_email"):
        op.create_index(
            "ix_campaign_recipients_campaign_email",
            "campaign_recipients",
            ["campaign_id", "email"],
        )

    # ── ck_ai_turns_agent CHECK → allow 'campaign_copy' (Spec 45 §16) ──────
    if _has_table(bind, "ai_turns"):
        op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_agent")
        check = _agent_check_sql([*_AGENT_NAMES, "campaign_copy"])
        op.execute(f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_agent CHECK ({check})")


def _add_fk_safe(bind, name, table, ref_table, local_cols, remote_cols, ondelete):
    """Create a named FK only if a constraint with that name doesn't exist."""
    try:
        existing = {fk.get("name") for fk in _insp(bind).get_foreign_keys(table)}
        if name in existing:
            return
        op.create_foreign_key(name, table, ref_table, local_cols, remote_cols, ondelete=ondelete)
    except Exception:
        # create_all-built DBs already have unnamed/auto FKs; ignore conflicts.
        pass


def downgrade() -> None:
    bind = op.get_bind()

    if _has_table(bind, "ai_turns"):
        op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_agent")
        check = _agent_check_sql(_AGENT_NAMES)
        op.execute(f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_agent CHECK ({check})")

    if _has_index(bind, "campaign_recipients", "ix_campaign_recipients_campaign_email"):
        op.drop_index("ix_campaign_recipients_campaign_email", table_name="campaign_recipients")
    for name, _ in _RECIPIENT_COLS:
        if _has_column(bind, "campaign_recipients", name):
            op.drop_column("campaign_recipients", name)

    for name, _, _ in _CAMPAIGN_COLS:
        if _has_column(bind, "campaigns", name):
            op.drop_column("campaigns", name)

    for col in ("description", "uploaded_list_ids", "frequency_cap_per_week"):
        if _has_column(bind, "target_segments", col):
            op.drop_column("target_segments", col)

    if _has_column(bind, "institutions", "require_campaign_approval"):
        op.drop_column("institutions", "require_campaign_approval")

    for tbl in ("campaign_suppressions", "uploaded_contacts", "uploaded_lists"):
        if _has_table(bind, tbl):
            op.drop_table(tbl)
