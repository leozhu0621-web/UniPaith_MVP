from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from unipaith.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AdmissionsAuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Append-only audit trail (Spec 36).

    Every consequential action records who/what/when. Rows are never updated
    and never deleted — a Postgres ``BEFORE UPDATE OR DELETE`` trigger
    (installed by the Spec 36 migration) enforces this at the DB layer.

    ``institution_id`` is nullable so student-scoped events (consent changes,
    data exports, deletion requests) can be recorded without an institution
    (Spec 36 §3 — ``institution_id: string | null``).
    """

    __tablename__ = "admissions_audit_log"
    __table_args__ = (
        Index("ix_audit_app_id", "application_id"),
        Index("ix_audit_institution_created", "institution_id", "created_at"),
        # Spec 36 — category-scoped listing + actor filter.
        Index("ix_audit_inst_category_created", "institution_id", "category", "created_at"),
        Index("ix_audit_actor", "actor_user_id"),
    )

    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=True,
    )
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Spec 36 §2 — the 13-category taxonomy this event belongs to. Nullable so
    # legacy rows survive; backfilled by the migration and inferred from
    # ``action`` on write when not supplied.
    category: Mapped[str | None] = mapped_column(String(40))
    # Spec 36 §3 — student | institution_admin | system | ai_agent.
    actor_role: Mapped[str | None] = mapped_column(String(20))
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # Spec 36 §3 — free-text rationale; required for overrides (enforced at the
    # service layer, not the column, so legacy rows stay valid).
    reason: Mapped[str | None] = mapped_column(Text)
    old_value: Mapped[dict | None] = mapped_column(JSONB)
    new_value: Mapped[dict | None] = mapped_column(JSONB)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)
    # Spec 36 §3 — request provenance, captured at the API layer when available.
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)

    actor_user = relationship("User", lazy="joined")  # type: ignore[name-defined]

    # Spec 36 §3 names the timestamp ``occurred_at``; the column is the
    # mixin's ``created_at``. Expose an alias so response schemas map cleanly.
    @property
    def occurred_at(self):
        return self.created_at

    @property
    def actor_email(self) -> str | None:
        # ``actor_user`` is eager-joined, so this does not trigger lazy IO.
        return getattr(self.actor_user, "email", None) if self.actor_user else None


# ── Append-only enforcement (Spec 36 §11) ───────────────────────────────────
# Shared DDL so the migration and the append-only test install the *same*
# guard. PostgreSQL only. Each tuple element is a SINGLE statement — asyncpg
# (the async alembic / app driver) rejects multi-statement strings — so callers
# execute them one at a time (see the Spec 36 migration + test_spec36).

_AUDIT_BLOCK_FN = """
CREATE OR REPLACE FUNCTION audit_block_mutation() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION
        'admissions_audit_log is append-only (Spec 36): % is not permitted', TG_OP;
END;
$$ LANGUAGE plpgsql
"""

# Install order: function, drop any stale trigger, then (re)create the trigger.
AUDIT_APPEND_ONLY_INSTALL_SQL: tuple[str, ...] = (
    _AUDIT_BLOCK_FN,
    "DROP TRIGGER IF EXISTS trg_audit_append_only ON admissions_audit_log",
    (
        "CREATE TRIGGER trg_audit_append_only "
        "BEFORE UPDATE OR DELETE ON admissions_audit_log "
        "FOR EACH ROW EXECUTE FUNCTION audit_block_mutation()"
    ),
)

AUDIT_APPEND_ONLY_DROP_SQL: tuple[str, ...] = (
    "DROP TRIGGER IF EXISTS trg_audit_append_only ON admissions_audit_log",
    "DROP FUNCTION IF EXISTS audit_block_mutation()",
)
