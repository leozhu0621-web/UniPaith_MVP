from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

SavedPriority = Literal["considering", "planning_to_apply", "applied", "dropped"]
SavedStatus = Literal[
    "considering",
    "application_started",
    "submitted",
    "accepted",
    "rejected",
    "waitlisted",
    "dropped",
]
MatchBand = Literal["reach", "target", "safer"]


class SaveProgramRequest(BaseModel):
    program_id: UUID
    notes: str | None = None


class UpdateSavedNotesRequest(BaseModel):
    notes: str


class PatchSavedProgramRequest(BaseModel):
    priority: SavedPriority | None = None
    notes: str | None = None
    tags: list[str] | None = None


class CompareProgramsRequest(BaseModel):
    program_ids: list[UUID] = Field(min_length=2, max_length=4)


class SavedProgramCard(BaseModel):
    """Program summary embedded in saved-list rows (Spec 13 §7)."""

    id: UUID
    institution_id: UUID
    program_name: str
    degree_type: str
    department: str | None = None
    tuition: int | None = None
    duration_months: int | None = None
    delivery_format: str | None = None
    acceptance_rate: float | None = None
    application_deadline: date | None = None
    institution_name: str | None = None
    institution_country: str | None = None
    institution_city: str | None = None
    median_salary: int | None = None
    employment_rate: float | None = None
    description_text: str | None = None


class SavedProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    list_id: UUID
    program_id: UUID
    notes: str | None = None
    added_at: datetime | None = None
    priority: SavedPriority = "considering"
    status: SavedStatus = "considering"
    tags: list[str] = Field(default_factory=list)
    program_name: str | None = None
    institution_name: str | None = None
    program: SavedProgramCard | None = None
    fitness_score: float | None = None
    confidence_score: float | None = None
    band_label: MatchBand | None = None


class StartApplicationResponse(BaseModel):
    app_id: UUID


class ComparisonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    programs: list[dict]
    ai_analysis: str | None
