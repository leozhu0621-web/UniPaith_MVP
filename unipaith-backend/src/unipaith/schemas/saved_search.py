"""Spec 56 §6 — Saved-search request/response schemas.

The stored ``query`` is a ``SavedQuery`` — the durable half of a ``SearchRequest``
(`schemas/search.py`): the NL text, the constraint chips, the panel filters and
the sort. Page/page-size are runtime-only, so they're not persisted; restoring a
saved search reopens Explore at page 1 with these constraints applied.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from unipaith.schemas.institution import ProgramSummaryResponse
from unipaith.schemas.search import ConstraintChip, FilterState, SortOption

EntityType = Literal["program", "scholarship", "school"]


class SavedQuery(BaseModel):
    """The persisted, replayable shape of a search — mirrors SearchRequest minus
    pagination."""

    query: str | None = None
    chips: list[ConstraintChip] = Field(default_factory=list)
    filters: FilterState | None = None
    sort: SortOption = SortOption.relevance


class SavedSearchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    entity_type: EntityType = "program"
    query: SavedQuery = Field(default_factory=SavedQuery)
    alert_enabled: bool = False


class SavedSearchUpdate(BaseModel):
    """Partial update — rename, toggle the alert, or replace the stored query."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    query: SavedQuery | None = None
    alert_enabled: bool | None = None


class SavedSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    entity_type: str
    query: SavedQuery
    alert_enabled: bool
    last_run_at: datetime | None = None
    last_match_count: int | None = None
    last_alerted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class SavedSearchRunResponse(BaseModel):
    """Live result of replaying a saved search now — the count plus a small
    sample for a preview."""

    count: int
    results: list[ProgramSummaryResponse]
