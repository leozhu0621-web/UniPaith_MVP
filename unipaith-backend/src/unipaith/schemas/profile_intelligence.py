from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

PROFILE_INTELLIGENCE_STANDARD_VERSION = 1

FRESHNESS_STATUS = Literal["current", "aging", "stale", "unknown"]
SOURCE_TYPE = Literal[
    "official",
    "government",
    "institution_report",
    "student_narrative",
    "employer_feedback",
    "verified_secondary",
    "derived",
]
CONCLUSION_TYPE = Literal["fact", "inferred", "institution_confirmed"]

TARGET_PROFILE_LAYERS = (
    "background_academic",
    "goals_behaviors_learning_working_style",
    "values_motivations_community",
)

PROTECTED_TRAIT_TERMS = {
    "race",
    "racial",
    "ethnicity",
    "ethnic",
    "sex",
    "gender",
    "gender_identity",
    "sexual_orientation",
    "age",
    "disability",
    "disabled",
    "religion",
    "religious",
    "national_origin",
    "citizenship",
    "marital",
    "pregnancy",
    "veteran",
    "genetic",
}
_PROTECTED_RE = re.compile(
    r"\b("
    + "|".join(re.escape(t).replace("_", r"[_\s-]?") for t in PROTECTED_TRAIT_TERMS)
    + r")\b",
    re.IGNORECASE,
)


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def assert_no_protected_traits(value: Any) -> None:
    """Reject protected-trait targeting/scoring payloads.

    The public profile can discuss community resources. This guard is for target
    profiles, preference weights, and private decision reasoning, where using
    protected traits would be scoring or personalization.
    """
    if value is None:
        return
    if isinstance(value, str):
        if _PROTECTED_RE.search(value):
            raise ValueError("protected traits cannot be used for matching or decision reasoning")
        return
    if isinstance(value, dict):
        for k, v in value.items():
            assert_no_protected_traits(str(k))
            assert_no_protected_traits(v)
        return
    if isinstance(value, (list, tuple, set)):
        for item in value:
            assert_no_protected_traits(item)


class Freshness(BaseModel):
    status: FRESHNESS_STATUS = "unknown"
    as_of: str | None = None
    checked_at: str | None = None
    max_age_days: int | None = Field(default=None, ge=0)


class EvidenceReference(BaseModel):
    label: str = Field(min_length=1, max_length=240)
    url: HttpUrl
    source_type: SOURCE_TYPE = "official"
    field_path: str | None = None
    freshness: Freshness = Field(default_factory=Freshness)
    quoted_or_paraphrased: Literal["paraphrased", "quoted_short", "data_point"] = "paraphrased"


class IntelligenceFinding(BaseModel):
    statement: str = Field(min_length=1, max_length=900)
    source_type: CONCLUSION_TYPE = "inferred"
    confidence: float = Field(ge=0, le=1)
    freshness: Freshness = Field(default_factory=Freshness)
    time_sensitive: bool = False
    evidence: list[EvidenceReference] = Field(default_factory=list)

    @model_validator(mode="after")
    def _has_evidence_and_current_dynamic_fact(self) -> IntelligenceFinding:
        if not self.evidence:
            raise ValueError("every populated conclusion must cite evidence")
        if self.time_sensitive and self.freshness.status == "stale":
            raise ValueError("stale time-sensitive conclusions must be omitted")
        return self


class IntelligenceSection(BaseModel):
    summary: str | None = None
    findings: list[IntelligenceFinding] = Field(default_factory=list)


class ProfileIntelligence(BaseModel):
    standard_version: int = PROFILE_INTELLIGENCE_STANDARD_VERSION
    profile_version: int = 1
    generated_at: str = Field(default_factory=utc_now_iso)
    sections: dict[str, IntelligenceSection] = Field(default_factory=dict)
    omissions: list[dict[str, str]] = Field(default_factory=list)

    @model_validator(mode="after")
    def _versioned(self) -> ProfileIntelligence:
        if self.standard_version != PROFILE_INTELLIGENCE_STANDARD_VERSION:
            raise ValueError("unsupported profile intelligence standard")
        return self


class TargetProfileSignal(BaseModel):
    attribute: str = Field(min_length=1, max_length=120)
    preferred_values: list[str] = Field(default_factory=list)
    statement: str | None = Field(default=None, max_length=600)
    weight: float = Field(default=0.0, ge=0, le=1)
    confidence: float = Field(default=0.0, ge=0, le=1)
    evidence: list[EvidenceReference] = Field(default_factory=list)

    @model_validator(mode="after")
    def _safe_and_grounded(self) -> TargetProfileSignal:
        if not self.evidence:
            raise ValueError("target profile signals must cite public evidence")
        assert_no_protected_traits(
            {
                "attribute": self.attribute,
                "preferred_values": self.preferred_values,
                "statement": self.statement,
            }
        )
        return self


class TargetProfile(BaseModel):
    standard_version: int = PROFILE_INTELLIGENCE_STANDARD_VERSION
    derived_at: str = Field(default_factory=utc_now_iso)
    layers: dict[str, list[TargetProfileSignal]]

    @field_validator("layers")
    @classmethod
    def _all_layers_present(cls, value: dict[str, list[TargetProfileSignal]]):
        missing = [layer for layer in TARGET_PROFILE_LAYERS if layer not in value]
        if missing:
            raise ValueError(f"missing target profile layers: {missing}")
        return value

    @model_validator(mode="after")
    def _safe(self) -> TargetProfile:
        # Signal-level validators guard the actual matching attributes,
        # preferred values, and reasoning statements. Evidence metadata may
        # legitimately cite a program page whose URL/title contains a protected
        # studies field, and citations are not scoring inputs.
        assert_no_protected_traits(list(self.layers.keys()))
        return self


class DecisionEvidence(BaseModel):
    side: Literal["student", "program", "institution", "system"] = "program"
    path: str = Field(min_length=1, max_length=240)
    label: str = Field(min_length=1, max_length=240)
    url: HttpUrl | None = None


class DecisionBriefItem(BaseModel):
    statement: str = Field(min_length=1, max_length=800)
    confidence: float = Field(default=0.5, ge=0, le=1)
    uncertainty: str | None = Field(default=None, max_length=600)
    evidence: list[DecisionEvidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def _grounded_and_safe(self) -> DecisionBriefItem:
        if not self.evidence:
            raise ValueError("decision brief items must cite evidence")
        assert_no_protected_traits({"statement": self.statement, "uncertainty": self.uncertainty})
        return self


class DecisionBrief(BaseModel):
    standard_version: int = PROFILE_INTELLIGENCE_STANDARD_VERSION
    student_profile_version: int = 1
    program_profile_version: int = 1
    generated_at: str = Field(default_factory=utc_now_iso)
    sections: dict[str, list[DecisionBriefItem]] = Field(default_factory=dict)
    omissions: list[dict[str, str]] = Field(default_factory=list)

    @model_validator(mode="after")
    def _safe(self) -> DecisionBrief:
        # DecisionBriefItem validates the private reasoning text. Evidence URLs
        # and labels can point to legitimate public program pages and should not
        # be treated as personalization/scoring signals.
        assert_no_protected_traits(list(self.sections.keys()))
        return self


def validate_profile_intelligence(payload: dict[str, Any]) -> dict[str, Any]:
    return ProfileIntelligence.model_validate(payload).model_dump(mode="json")


def validate_target_profile(payload: dict[str, Any]) -> dict[str, Any]:
    return TargetProfile.model_validate(payload).model_dump(mode="json")


def validate_decision_brief(payload: dict[str, Any]) -> dict[str, Any]:
    return DecisionBrief.model_validate(payload).model_dump(mode="json")
