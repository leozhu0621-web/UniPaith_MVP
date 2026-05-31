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
    # Accepts the canonical matrix {type: {email,sms,in_app,push}} or a list of
    # {type, channels}; legacy {type: bool} is tolerated (normalised server-side).
    preferences: dict | list | None = None
    email_frequency: str | None = None


class NotificationPreferenceResponse(BaseModel):
    id: UUID
    user_id: UUID
    email_enabled: bool
    preferences: dict | None
    email_frequency: str
    # Full canonical per-type × per-channel matrix with defaults filled in.
    matrix: list[dict]
    updated_at: datetime
