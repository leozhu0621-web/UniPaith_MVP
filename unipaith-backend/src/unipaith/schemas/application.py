from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateApplicationRequest(BaseModel):
    program_id: UUID


class UpdateApplicationRequest(BaseModel):
    status: Literal["draft", "submitted", "under_review", "interview", "decision_made"] | None = (
        None
    )
    completeness_status: Literal["complete", "incomplete", "pending_verification"] | None = None
    missing_items: list[str] | None = None


class PatchApplicationRequest(BaseModel):
    """Student partial update (spec 15 §9) — submission mode + guardrail intent."""

    submission_mode: Literal["internal", "external"] | None = None
    intent_picker: (
        Literal["career_fit", "back_up", "dream", "cultural_fit", "family_input", "other"] | None
    ) = None
    intent_rationale: str | None = None


class SubmitApplicationRequest(BaseModel):
    pass


class DecisionRequest(BaseModel):
    decision: Literal["admitted", "rejected", "waitlisted", "deferred"]
    decision_notes: str | None = None


class ChecklistToggleRequest(BaseModel):
    """Manually mark a checklist item complete/incomplete (spec 15 §7)."""

    item_key: str
    completed: bool


class GuardrailScanResponse(BaseModel):
    fit_band: Literal["low", "medium", "high"]
    fitness_score: float | None = None
    recommended_action: Literal["proceed", "review", "reconsider"]
    blockers: list[str]
    is_rule_based: bool = True


class ProgramBrief(BaseModel):
    """Minimal program info embedded in application responses."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    program_name: str
    degree_type: str
    institution_name: str | None = None
    tuition: int | None = None
    duration_months: int | None = None
    application_deadline: date | None = None


class OfferLetterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    application_id: UUID
    offer_type: str | None
    tuition_amount: int | None
    scholarship_amount: int
    financial_package_total: int | None
    conditions: dict | None
    response_deadline: date | None
    status: str | None
    student_response: str | None
    response_at: datetime | None
    brief: str | None = None
    # --- Spec 18 · Decisions & Offers ---
    received_externally: bool = False
    decision_date: date | None = None
    scholarship_currency: str | None = None
    tuition_estimate: int | None = None
    total_cost_estimate: int | None = None
    start_term_season: str | None = None
    start_term_year: int | None = None
    next_step_actions: list | None = None
    plain_language_brief: dict | None = None
    generated_letter_url: str | None = None
    created_at: datetime
    updated_at: datetime


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    # Spec 32 — institution-facing lists attach the applicant's display name so
    # reviewers never see a raw UUID. None on student-side paths.
    student_name: str | None = None
    program_id: UUID
    status: str | None
    match_score: Decimal | None
    match_reasoning_text: str | None
    submitted_at: datetime | None
    decision: str | None
    decision_at: datetime | None
    # Spec 18 §2 — student-side decision + the unified derived decision state.
    student_decision: str | None = None
    decision_state: str | None = None
    completeness_status: str | None
    missing_items: dict | None
    # --- Spec 15 workspace fields ---
    submission_mode: str = "internal"
    readiness_pct: int | None = None
    intent_picker: str | None = None
    intent_rationale: str | None = None
    fit_band: str | None = None
    guardrail_blockers: list | None = None
    offer: OfferLetterResponse | None = None
    created_at: datetime
    updated_at: datetime
    program: ProgramBrief | None = None


class ApplicationDetailResponse(ApplicationResponse):
    decision_notes: str | None = None
    decision_by: UUID | None = None


class CreateOfferRequest(BaseModel):
    offer_type: Literal["full_admission", "conditional", "waitlist_offer"]
    tuition_amount: int | None = None
    scholarship_amount: int = 0
    assistantship_details: dict | None = None
    financial_package_total: int | None = None
    conditions: dict | None = None
    response_deadline: date | None = None


class OfferRespondRequest(BaseModel):
    response: Literal["accepted", "declined"]
    decline_reason: str | None = None


# --- Spec 18 · Decisions & Offers ---


class StartTerm(BaseModel):
    season: str | None = None
    year: int | None = None


class RecordOfferRequest(BaseModel):
    """Student records an offer received off-platform (spec 18 §3/§14)."""

    offer_type: Literal[
        "full_admission",
        "conditional",
        "waitlist_to_admit",
        "partial",
        "transfer_credit_offer",
    ] = "full_admission"
    decision_date: date | None = None
    response_deadline: date | None = None
    scholarship_amount: int | None = None
    scholarship_currency: str | None = "USD"
    tuition_amount: int | None = None
    tuition_estimate: int | None = None
    total_cost_estimate: int | None = None
    financial_package_total: int | None = None
    conditions: dict | None = None
    start_term: StartTerm | None = None
    next_step_actions: list[dict] | None = None


class OfferDecisionResponse(BaseModel):
    """Accept/decline result + the other pending apps now withdrawable (§6)."""

    offer: OfferLetterResponse
    withdrawable_apps: list[dict] = []


class BulkWithdrawRequest(BaseModel):
    application_ids: list[UUID]


class WithdrawResult(BaseModel):
    withdrawn_count: int


class OfferComparisonItem(BaseModel):
    application_id: str
    offer_id: str
    program_name: str | None = None
    institution_name: str | None = None
    degree_type: str | None = None
    decision_state: str | None = None
    cost: dict
    fit: dict
    outcomes: dict
    location: str | None = None
    response_deadline: str | None = None
    conditions: dict | None = None


class OffersComparisonResponse(BaseModel):
    offers: list[OfferComparisonItem]
    indicators: dict
    must_have_constraints: list[dict]
    count: int
    advisor_summary: str | None = None
