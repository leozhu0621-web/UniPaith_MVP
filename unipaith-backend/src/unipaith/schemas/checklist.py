from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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


# --- Program-level checklist configuration ---


class CreateProgramChecklistItemRequest(BaseModel):
    item_name: str = Field(min_length=1, max_length=255)
    category: str = Field(
        "document",
        pattern=(
            r"^(essay|test_score|recommendation|"
            r"interview|portfolio|document|financial|other)$"
        ),
    )
    requirement_level: str = Field(
        "required",
        pattern=r"^(required|optional|conditional|not_applicable)$",
    )
    description: str | None = None
    instructions: str | None = None
    sort_order: int = 0


class UpdateProgramChecklistItemRequest(BaseModel):
    item_name: str | None = Field(None, min_length=1, max_length=255)
    category: str | None = None
    requirement_level: str | None = None
    description: str | None = None
    instructions: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class ProgramChecklistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    program_id: UUID
    item_name: str
    category: str
    requirement_level: str
    description: str | None
    instructions: str | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class BulkChecklistRequest(BaseModel):
    items: list[CreateProgramChecklistItemRequest] = Field(min_length=1)
