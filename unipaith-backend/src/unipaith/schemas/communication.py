from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateTemplateRequest(BaseModel):
    template_type: str = Field(
        ...,
        pattern=r"^(missing_items|interview_invite|clarification|decision_admit|decision_reject|decision_waitlist|offer_notice|custom)$",
    )
    name: str = Field(min_length=1, max_length=255)
    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1)
    program_id: UUID | None = None
    variables: list[str] | None = None
    is_default: bool = False


class UpdateTemplateRequest(BaseModel):
    template_type: str | None = None
    name: str | None = Field(None, min_length=1, max_length=255)
    subject: str | None = Field(None, min_length=1, max_length=500)
    body: str | None = None
    program_id: UUID | None = None
    variables: list[str] | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    program_id: UUID | None
    template_type: str
    name: str
    subject: str
    body: str
    variables: list[str] | dict | None
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    program_name: str | None = None


class SendFromTemplateRequest(BaseModel):
    application_ids: list[UUID] = Field(min_length=1)
    variable_overrides: dict[str, str] | None = None


class SendResult(BaseModel):
    success_count: int
    failed_ids: list[UUID]


class TemplatePreviewResponse(BaseModel):
    rendered_subject: str
    rendered_body: str
    variables_used: list[str]
