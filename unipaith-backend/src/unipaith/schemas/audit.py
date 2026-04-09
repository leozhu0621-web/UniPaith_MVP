from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    application_id: UUID | None
    actor_user_id: UUID | None
    action: str
    entity_type: str
    entity_id: str
    description: str | None
    old_value: dict | None
    new_value: dict | None
    metadata_json: dict | None
    created_at: datetime
    actor_email: str | None = None


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
