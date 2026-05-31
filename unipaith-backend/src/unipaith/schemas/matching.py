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
    institution_name: str | None = None
    degree_type: str | None = None
    tuition: int | None = None


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
