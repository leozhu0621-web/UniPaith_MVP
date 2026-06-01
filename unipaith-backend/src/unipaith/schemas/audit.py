from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    """List-row view (Spec 36 §4 table). Lightweight — the heavy before/after
    diff + provenance live on :class:`AuditEventDetailResponse`."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID | None = None
    application_id: UUID | None = None
    actor_user_id: UUID | None = None
    actor_role: str | None = None
    category: str | None = None
    action: str
    entity_type: str
    entity_id: str
    description: str | None = None
    reason: str | None = None
    created_at: datetime
    occurred_at: datetime | None = None
    actor_email: str | None = None


class AuditEventDetailResponse(AuditLogResponse):
    """Single-event view (Spec 36 §5 `GET /audit-log/:id`) with full diff."""

    old_value: dict | None = None
    new_value: dict | None = None
    metadata_json: dict | None = None
    ip_address: str | None = None
    user_agent: str | None = None


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
