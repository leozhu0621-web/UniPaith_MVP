from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    notification_type: str
    title: str
    body: str
    action_url: str | None
    metadata_: dict | None
    is_read: bool
    is_emailed: bool
    created_at: datetime
    read_at: datetime | None


class UpdateNotificationPrefsRequest(BaseModel):
    email_enabled: bool | None = None
    preferences: dict | None = None


class NotificationPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    email_enabled: bool
    preferences: dict | None
    updated_at: datetime
