from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChecklistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    category: str
    required: bool
    completed: bool
    description: str | None = None


class ApplicationChecklistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    program_id: UUID
    items: list[dict] | None
    completion_percentage: int
    auto_generated_at: datetime | None


class ReadinessCheckResponse(BaseModel):
    is_ready: bool
    completion_percentage: int
    missing_items: list[str]
    warnings: list[str]
