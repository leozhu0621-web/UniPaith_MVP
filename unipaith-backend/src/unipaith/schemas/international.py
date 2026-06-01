"""Spec 38 — International Admissions request schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CountryRequirementItem(BaseModel):
    item: str
    status: Literal["pending", "received", "verified", "waived"] = "pending"


class PatchInternationalRequest(BaseModel):
    """Partial update of the editable international-processing fields (§4).

    Immigration-document and SEVIS fields are intentionally excluded — they move
    only through the generate endpoint."""

    credential_provider: Literal["WES", "ECE", "SpanTran", "other"] | None = None
    credential_status: (
        Literal["none", "requested", "in_progress", "received", "verified"] | None
    ) = None
    credential_report_ref: str | None = None
    credential_normalized_gpa: float | None = Field(None, ge=0, le=4.0)
    credential_source_scale: str | None = None
    credential_notes: str | None = None
    english_test: Literal["TOEFL", "IELTS", "DET", "PTE"] | None = None
    english_score: float | None = Field(None, ge=0)
    english_meets_minimum: bool | None = None
    english_waiver_eligible: bool | None = None
    english_waiver_basis: str | None = None
    country_requirements: list[CountryRequirementItem] | None = None
    visa_appointment_at: str | None = None
    visa_consulate: str | None = None
    visa_outcome: Literal["pending", "approved", "denied"] | None = None


class NormalizeGpaRequest(BaseModel):
    raw_gpa: float | None = Field(None, ge=0)
    scale_hint: str | None = None
    country: str | None = None


class GenerateImmigrationDocRequest(BaseModel):
    doc_type: Literal["I-20", "DS-2019"] = "I-20"


class EnglishPolicyTest(BaseModel):
    test: Literal["TOEFL", "IELTS", "DET", "PTE"]
    min_score: float = Field(ge=0)


class EnglishPolicyRequest(BaseModel):
    """Spec 38 §2.2 — accepted English tests + minimum scores + waiver rules."""

    accepted_tests: list[EnglishPolicyTest] = Field(default_factory=list)
    waiver_native_english_countries: list[str] = Field(default_factory=list)
    waiver_prior_degree_in_english: bool = True
    expected_version: int | None = None
