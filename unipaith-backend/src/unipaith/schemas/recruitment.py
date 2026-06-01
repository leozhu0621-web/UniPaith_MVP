"""Spec 40 — Recruitment CRM (Pre-Applicant) request/response schemas.

Shared by ``RecruitmentService`` (which builds them) and ``api/recruitment.py``
(which serves them). Mirrors the §4 data shapes; the frontend types in
``frontend/src/types/index.ts`` are the wire mirror of these.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from unipaith.models.recruitment import (
    FAIR_KINDS,
    FAIR_STATUSES,
    PROSPECT_SOURCES,
    PROSPECT_STAGES,
    TRIP_STATUSES,
    VISIT_KINDS,
    VISIT_STATUSES,
)

# ── Prospects ────────────────────────────────────────────────────────────────


class ProspectBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str | None = None
    phone: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    interests: list[str] = Field(default_factory=list)
    source: str = "web"
    source_detail: str | None = None
    stage: str = "prospect"
    territory_id: UUID | None = None
    owner_user_id: UUID | None = None
    owner_name: str | None = None
    consent_outreach: bool = False
    notes: str | None = None


class CreateProspectRequest(ProspectBase):
    pass


class UpdateProspectRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = None
    phone: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    interests: list[str] | None = None
    source: str | None = None
    source_detail: str | None = None
    stage: str | None = None
    territory_id: UUID | None = None
    owner_user_id: UUID | None = None
    owner_name: str | None = None
    consent_outreach: bool | None = None
    notes: str | None = None


class ProspectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str | None = None
    phone: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    interests: list[str] | None = None
    source: str
    source_detail: str | None = None
    stage: str
    territory_id: UUID | None = None
    owner_user_id: UUID | None = None
    owner_name: str | None = None
    converted_application_id: UUID | None = None
    consent_outreach: bool
    apply_likelihood: float | None = None
    priority_reason: str | None = None
    # Derived (set by the service when ProspectPrioritizer ran): hot|warm|cold.
    priority_band: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ProspectListResponse(BaseModel):
    items: list[ProspectResponse]
    total: int
    # True when ProspectPrioritizer ran (apply_likelihood populated). The FE
    # shows an AI badge + a FallbackNote when this is False but AI is on.
    prioritized: bool = False
    stage_counts: dict[str, int] = Field(default_factory=dict)


class ProspectImportRow(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str | None = None
    phone: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    interests: list[str] = Field(default_factory=list)
    # Per-row explicit opt-in (e.g. a captured inquiry where the prospect agreed
    # to be contacted). Defaults False → outreach stays opt-in only (§7 / 46).
    consent_outreach: bool = False


class ProspectImportRequest(BaseModel):
    source: str = "list"
    source_detail: str | None = None
    territory_id: UUID | None = None
    rows: list[ProspectImportRow] = Field(default_factory=list)


class ProspectImportResult(BaseModel):
    imported: int
    deduped: int
    suppressed: int
    total_rows: int


class ConvertProspectRequest(BaseModel):
    # Optional — link to a specific application the prospect started. When
    # omitted the prospect is simply advanced to the ``applicant`` stage.
    application_id: UUID | None = None


class ProspectToSegmentRequest(BaseModel):
    prospect_ids: list[UUID] = Field(default_factory=list, min_length=1)
    list_name: str = Field(min_length=1, max_length=255)


class ProspectToSegmentResult(BaseModel):
    list_id: UUID
    list_name: str
    added: int
    skipped_no_consent: int
    skipped_no_email: int


# ── Travel calendar (trips + visits) ─────────────────────────────────────────


class TripVisitBase(BaseModel):
    kind: str = "school"
    name: str = Field(min_length=1, max_length=255)
    fair_id: UUID | None = None
    visit_date: date | None = None
    status: str = "planned"
    notes: str | None = None


class CreateTripVisitRequest(TripVisitBase):
    pass


class UpdateTripVisitRequest(BaseModel):
    kind: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    fair_id: UUID | None = None
    visit_date: date | None = None
    prospects_met: int | None = Field(default=None, ge=0)
    status: str | None = None
    notes: str | None = None


class TripVisitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trip_id: UUID
    kind: str
    name: str
    fair_id: UUID | None = None
    visit_date: date | None = None
    prospects_met: int
    status: str
    notes: str | None = None


class CreateTripRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    region: str | None = None
    start_date: date
    end_date: date
    recruiter_user_id: UUID | None = None
    recruiter_name: str | None = None
    budget: Decimal | None = None
    spend: Decimal | None = None
    status: str = "planned"
    notes: str | None = None
    visits: list[CreateTripVisitRequest] = Field(default_factory=list)


class UpdateTripRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    region: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    recruiter_user_id: UUID | None = None
    recruiter_name: str | None = None
    budget: Decimal | None = None
    spend: Decimal | None = None
    status: str | None = None
    notes: str | None = None


class TripResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    region: str | None = None
    start_date: date
    end_date: date
    recruiter_user_id: UUID | None = None
    recruiter_name: str | None = None
    budget: Decimal | None = None
    spend: Decimal
    status: str
    notes: str | None = None
    visits: list[TripVisitResponse] = Field(default_factory=list)
    # Derived (§6): spend > budget, and same-recruiter date overlap with another trip.
    over_budget: bool = False
    conflict: bool = False
    created_at: datetime
    updated_at: datetime


# ── Fairs / high-school directory ────────────────────────────────────────────


class FairBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    kind: str = "fair"
    city: str | None = None
    region: str | None = None
    country: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    prior_year_yield: int | None = Field(default=None, ge=0)
    event_date: date | None = None
    status: str = "prospective"
    notes: str | None = None


class CreateFairRequest(FairBase):
    pass


class UpdateFairRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    kind: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    prior_year_yield: int | None = Field(default=None, ge=0)
    event_date: date | None = None
    status: str | None = None
    notes: str | None = None


class FairResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    kind: str
    city: str | None = None
    region: str | None = None
    country: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    prior_year_yield: int | None = None
    event_date: date | None = None
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class CapturedLead(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str | None = None
    phone: str | None = None
    interests: list[str] = Field(default_factory=list)
    consent_outreach: bool = False


class FairCaptureRequest(BaseModel):
    leads: list[CapturedLead] = Field(default_factory=list, min_length=1)
    territory_id: UUID | None = None
    # Optionally attribute the capture to a specific trip visit (bumps its
    # prospects_met counter).
    trip_visit_id: UUID | None = None


class FairCaptureResult(BaseModel):
    captured: int
    deduped: int
    suppressed: int
    fair_id: UUID


# ── Territories ──────────────────────────────────────────────────────────────


class TerritoryGeo(BaseModel):
    regions: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)


class CreateTerritoryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    geo: TerritoryGeo | None = None
    owner_user_id: UUID | None = None
    owner_name: str | None = None
    notes: str | None = None


class UpdateTerritoryRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    geo: TerritoryGeo | None = None
    owner_user_id: UUID | None = None
    owner_name: str | None = None
    notes: str | None = None


class TerritoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    geo: dict | None = None
    owner_user_id: UUID | None = None
    owner_name: str | None = None
    notes: str | None = None
    # Aggregate-on-read metrics (§2.4).
    prospect_count: int = 0
    applicant_count: int = 0
    conversion_rate: float = 0.0
    # True when neither owner field is set (§6 unassigned nudge).
    unassigned: bool = True
    created_at: datetime
    updated_at: datetime


class TerritorySuggestion(BaseModel):
    kind: str
    label: str
    rationale: str
    candidate_name: str | None = None


class TerritoryOptimizeResponse(BaseModel):
    territory_id: UUID
    suggestions: list[TerritorySuggestion] = Field(default_factory=list)
    # True when TerritoryOptimizer (LLM) produced these; False = rule-based fallback.
    ai_generated: bool = False


class TerritoryDashboardResponse(BaseModel):
    territories: list[TerritoryResponse] = Field(default_factory=list)
    # Roll-up across all territories.
    total_prospects: int = 0
    total_applicants: int = 0
    overall_conversion_rate: float = 0.0
    unassigned_count: int = 0


# ── Summary (empty-state + headline metrics) ─────────────────────────────────


class RecruitmentSummaryResponse(BaseModel):
    prospect_count: int = 0
    applicant_count: int = 0
    trip_count: int = 0
    fair_count: int = 0
    territory_count: int = 0
    unassigned_territory_count: int = 0
    over_budget_trip_count: int = 0
    stage_counts: dict[str, int] = Field(default_factory=dict)
    source_counts: dict[str, int] = Field(default_factory=dict)
    # True when the institution has no prospects AND no captured leads → the
    # empty state ("Import a prospect list or capture leads at a fair to start.").
    is_empty: bool = True


# Allowed-value tuples re-exported for the API layer's validation messages.
__all__ = [
    "PROSPECT_SOURCES",
    "PROSPECT_STAGES",
    "TRIP_STATUSES",
    "VISIT_KINDS",
    "VISIT_STATUSES",
    "FAIR_KINDS",
    "FAIR_STATUSES",
    "CreateProspectRequest",
    "UpdateProspectRequest",
    "ProspectResponse",
    "ProspectListResponse",
    "ProspectImportRequest",
    "ProspectImportResult",
    "ConvertProspectRequest",
    "ProspectToSegmentRequest",
    "ProspectToSegmentResult",
    "CreateTripRequest",
    "UpdateTripRequest",
    "TripResponse",
    "CreateTripVisitRequest",
    "UpdateTripVisitRequest",
    "TripVisitResponse",
    "CreateFairRequest",
    "UpdateFairRequest",
    "FairResponse",
    "FairCaptureRequest",
    "FairCaptureResult",
    "CreateTerritoryRequest",
    "UpdateTerritoryRequest",
    "TerritoryResponse",
    "TerritoryDashboardResponse",
    "TerritoryOptimizeResponse",
    "TerritorySuggestion",
    "RecruitmentSummaryResponse",
]
