from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MatchResultResponse(BaseModel):
    """Phase A: dual scores (fitness + confidence). The legacy `match_score`
    and `score_breakdown` fields stay in the response for one release so the
    frontend can update without coordination — they get dropped in Phase E.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    program_id: UUID

    # Phase A — dual scores (preferred).
    fitness_score: Decimal
    confidence_score: Decimal
    fitness_breakdown: dict | None = None
    confidence_breakdown: dict | None = None
    rationale_text: str | None = None
    rationale_generated_at: datetime | None = None
    strategy_version_id: UUID | None = None

    # DEPRECATED — drop in Phase E. Now nullable so post-Phase-A writes that
    # only set the dual scores still validate.
    match_score: Decimal | None = None
    score_breakdown: dict | None = None

    match_tier: int | None = None
    reasoning_text: str | None = None
    model_version: str | None = None
    computed_at: datetime
    is_stale: bool

    program_name: str | None = None
    institution_id: UUID | None = None
    institution_name: str | None = None
    degree_type: str | None = None
    tuition: int | None = None
    acceptance_rate: float | None = None

    # Spec 09 §6 — reach / target / safer banding (derived from program
    # selectivity vs the student's stated tolerance; fitness-only fallback).
    band_label: str | None = None

    # Spec 09 §4A — probability bands (admit / scholarship / waitlist + drivers).
    # null when the program lacks historical admit signal OR the student isn't
    # match-ready, so the UI shows "Not enough data yet" instead of false precision.
    probability_bands: dict | None = None


class StudentMatchResponse(BaseModel):
    """Spec AI-Structure-3 §14 / §6 — the STUDENT projection of a match.

    BACKEND-ONLY CONTRACT: the student never sees a raw matching number. This
    schema deliberately OMITS ``fitness_score`` / ``confidence_score`` /
    ``match_score`` / ``score_breakdown`` — the raw CPEF posterior and its
    weights are internal. The student gets only the human-readable readouts:
    the reach/target/safer ``band_label`` (Spec 09 §6), the probability bands
    (Spec 09 §4A), the redacted score breakdowns (the rationale popover's
    qualitative drivers, already passed through the §5.5 redaction map), and the
    rationale text. The full numeric schema (``MatchResultResponse``) is served
    only to institution/admin surfaces.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    program_id: UUID

    # Qualitative, student-safe readouts only — NO raw score field.
    fitness_breakdown: dict | None = None
    confidence_breakdown: dict | None = None
    rationale_text: str | None = None
    rationale_generated_at: datetime | None = None
    strategy_version_id: UUID | None = None

    match_tier: int | None = None
    reasoning_text: str | None = None
    model_version: str | None = None
    computed_at: datetime
    is_stale: bool

    program_name: str | None = None
    institution_id: UUID | None = None
    institution_name: str | None = None
    degree_type: str | None = None
    tuition: int | None = None
    acceptance_rate: float | None = None

    # Spec 09 §6 — reach / target / safer banding (the student's fit readout).
    band_label: str | None = None

    # Simple, range-based student-safe "Fit" readout (NOT the raw number): "Fit"
    # when the computed fitness clears the threshold, else None. Lets the strategy
    # surfaces show a Fit signal without exposing the omitted fitness_score.
    fit_label: str | None = None

    # Spec 09 §4A — probability bands (admit / scholarship / waitlist + drivers).
    probability_bands: dict | None = None


class ExplainMatchResponse(BaseModel):
    """Returned by POST /me/matches/{program_id}/explain. The rationale_text
    is generated on demand — Phase A synthesizes a deterministic 3-line
    explanation from the breakdown columns; Plan 2 will replace with an LLM
    call. Cached on the row, so subsequent reads via /me/matches return it
    inline.

    Spec 06 §3 / §5.5 — this is the STUDENT (redacted) projection of the
    rationale. The breakdowns and citations carried here are already passed
    through `ai.rationale_redaction.project_for_student`, so institution-only
    comparative signals never reach this surface. `redacted=True` tells the
    UI it is showing the safe view."""

    model_config = ConfigDict(from_attributes=True)

    program_id: UUID
    rationale_text: str
    rationale_generated_at: datetime
    is_stub: bool = True
    decision_brief: dict | None = None
    # Redacted (student-safe) signal views — single source the popover renders.
    fitness_breakdown: dict | None = None
    confidence_breakdown: dict | None = None
    cited_student_fields: list[str] = []
    cited_program_fields: list[str] = []
    redacted: bool = True


class InstitutionMatchRationaleResponse(BaseModel):
    """Spec 06 §3 / §5.5 + spec 32 §6 — the INSTITUTION (full, evidence-linked)
    projection of the same match rationale a student sees redacted.

    Served only to `institution_admin` for applications to that institution's
    programs. Nothing is withheld: every citation and every comparative /
    internal matching signal is present so a reviewer has the full audit
    trail. `redacted` is always False here."""

    application_id: UUID
    student_id: UUID
    program_id: UUID
    available: bool = True
    rationale_text: str = ""
    cited_student_fields: list[str] = []
    cited_program_fields: list[str] = []
    fitness_breakdown: dict = {}
    confidence_breakdown: dict = {}
    fitness_score: float | None = None
    confidence_score: float | None = None
    grounded: bool = True
    redacted: bool = False
    is_stub: bool = False


class MatchListResponse(BaseModel):
    matches: list[MatchResultResponse]
    total: int
    tier_counts: dict
    computed_at: datetime | None
    is_fresh: bool


class EngagementSignalRequest(BaseModel):
    program_id: UUID
    signal_type: str
    signal_value: int = 1


class EngagementSignalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    program_id: UUID
    signal_type: str
    signal_value: int
    created_at: datetime
