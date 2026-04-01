from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from unipaith.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AdminAuditEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "admin_audit_events"

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    payload_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    actor_user = relationship("User", lazy="joined")  # type: ignore[name-defined]
