from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Spec 13 §4.2 — persisted priority enum.
PriorityLiteral = Literal["considering", "planning_to_apply", "applied", "dropped"]


class SaveProgramRequest(BaseModel):
    program_id: UUID
    notes: str | None = None


class UpdateSavedNotesRequest(BaseModel):
    """Legacy PUT /{program_id}/notes body — kept for back-compat."""

    notes: str


class UpdateSavedRequest(BaseModel):
    """PATCH /students/me/saved/{program_id} — partial curation update.

    Spec 13 §4.2 (priority, closes gap G-S5) + §4.3 (tags & notes). Any field
    left unset is untouched.
    """

    priority: PriorityLiteral | None = None
    notes: str | None = None
    tags: list[str] | None = None

    @field_validator("tags")
    @classmethod
    def _clean_tags(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        seen: set[str] = set()
        out: list[str] = []
        for raw in v:
            s = str(raw).strip()
            if s and s.lower() not in seen:
                seen.add(s.lower())
                out.append(s)
        return out[:20]


class CompareProgramsRequest(BaseModel):
    # Spec 13 §5 — max 4 programs in one compare.
    program_ids: list[UUID] = Field(min_length=2, max_length=4)


class SavedProgramResponse(BaseModel):
    """A saved program enriched with curation + the derived match/status data
    the Saved List (Spec 13 §7) renders per row.

    `status` / `band_label` are derived (from application existence and the
    match row) — output is lenient `str` so an unexpected upstream value can
    never 500 the list.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    list_id: UUID
    program_id: UUID
    notes: str | None = None
    added_at: datetime | None = None

    # Spec 13 §4.2 / §4.3 — persisted curation.
    priority: str = "considering"
    tags: list[str] = Field(default_factory=list)

    # Spec 13 §4.4 — derived from application existence.
    status: str = "considering"

    # Spec 13 §7 — reach / target / safer + dual scores (derived from the match row).
    band_label: str | None = None
    fitness_score: float | None = None
    confidence_score: float | None = None

    # Program / institution detail — flattened for the row, plus a nested
    # `program` object for back-compat with consumers that read `sp.program?.*`.
    program_name: str | None = None
    institution_id: UUID | None = None
    institution_name: str | None = None
    institution_country: str | None = None
    institution_city: str | None = None
    degree_type: str | None = None
    tuition: float | None = None
    application_deadline: str | None = None
    acceptance_rate: float | None = None
    duration_months: int | None = None
    program: dict | None = None


class StartApplicationResponse(BaseModel):
    """Spec 13 §6 — one-click conversion of a saved program to an application."""

    app_id: UUID
    program_id: UUID
    status: str
    created: bool


class ComparisonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    programs: list[dict]
    ai_analysis: str | None = None
