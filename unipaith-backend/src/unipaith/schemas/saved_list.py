from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SaveProgramRequest(BaseModel):
    program_id: UUID
    notes: str | None = None


class UpdateSavedNotesRequest(BaseModel):
    notes: str


class CompareProgramsRequest(BaseModel):
    program_ids: list[UUID] = Field(min_length=2, max_length=5)


class SavedProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    list_id: UUID
    program_id: UUID
    notes: str | None = None
    added_at: datetime | None = None
    program_name: str | None = None
    institution_name: str | None = None


class ComparisonProgramSummary(BaseModel):
    id: str
    program_name: str | None = None
    institution_name: str | None = None
    institution_country: str | None = None
    degree_type: str | None = None
    duration_months: int | None = None
    tuition: float | None = None
    acceptance_rate: float | None = None
    application_deadline: str | None = None
    match_score: float | None = None
    match_tier: int | None = None


class ComparisonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    programs: list[ComparisonProgramSummary]
    comparison: dict
