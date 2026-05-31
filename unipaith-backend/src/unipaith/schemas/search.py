"""Spec 10 — Discovery type-first program search schemas.

Request/response models for the authed search surface:
  POST /me/search/interpret   — NL query → structured constraint chips
  POST /me/search/programs    — chips + filters + sort → programs
  GET/POST/DELETE /me/compare — server-persisted compare set

`ConstraintChip` mirrors spec 10 §9 and the `submit_constraints` tool schema
(`ai/tools/query_interpreter_schema.py`) — keep the category enum in sync.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from unipaith.schemas.institution import ProgramSummaryResponse


class ConstraintCategory(StrEnum):
    degree_level = "degree_level"
    major = "major"
    location = "location"
    budget = "budget"
    format = "format"
    start_term = "start_term"
    duration = "duration"
    selectivity = "selectivity"
    other = "other"


class ConstraintChip(BaseModel):
    """One editable/removable constraint (spec 10 §4). `value` is the canonical
    machine value; `display` is the human label. `id` is deterministic
    (`category:value`) so the client can de-dupe and key on it."""

    id: str | None = None
    category: ConstraintCategory
    value: str
    display: str
    confidence: int = Field(default=100, ge=0, le=100)
    user_confirmed: bool = False

    def with_id(self) -> ConstraintChip:
        if not self.id:
            self.id = f"{self.category.value}:{self.value}".lower()
        return self


class SortOption(StrEnum):
    relevance = "relevance"
    fitness = "fitness"
    confidence = "confidence"
    tuition_asc = "tuition_asc"
    tuition_desc = "tuition_desc"
    acceptance_asc = "acceptance_asc"
    acceptance_desc = "acceptance_desc"
    deadline = "deadline"
    recently_added = "recently_added"


class FilterState(BaseModel):
    """Panel-level facets that augment chips (spec 10 §5). All optional; chips
    remain the primary constraint source. Merged with chip-derived kwargs in
    `SearchService.search` (explicit filters win on conflict)."""

    campus_setting: str | None = None
    program_name: str | None = None
    country: str | None = None
    region: str | None = None
    city: str | None = None
    degree_types: list[str] | None = None
    delivery_formats: list[str] | None = None
    min_tuition: int | None = None
    max_tuition: int | None = None
    min_duration_months: int | None = None
    max_duration_months: int | None = None
    min_acceptance_rate: float | None = None
    max_acceptance_rate: float | None = None
    start_year: int | None = None
    # Spec 10 §5 — featured / outcome filters (data-gated; null-valued programs
    # are excluded when the corresponding filter is set).
    min_median_salary: int | None = None
    min_employment_rate: float | None = None
    max_payback_months: int | None = None


class InterpretRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)


class InterpretResponse(BaseModel):
    chips: list[ConstraintChip]
    interpretation: str
    # True when the rule-based parser served the result (LLM off/failed) — the
    # UI shows a "Limited search active" note (spec 10 §11).
    degraded: bool = False


class SearchRequest(BaseModel):
    query: str | None = None
    chips: list[ConstraintChip] = Field(default_factory=list)
    filters: FilterState | None = None
    sort: SortOption = SortOption.relevance
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=24, ge=1, le=60)


class SearchResponse(BaseModel):
    results: list[ProgramSummaryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CompareItem(BaseModel):
    program_id: UUID
    program_name: str
    institution_name: str
    degree_type: str | None = None


class CompareListResponse(BaseModel):
    items: list[CompareItem]
    max: int = 4


class CompareAddRequest(BaseModel):
    program_id: UUID
