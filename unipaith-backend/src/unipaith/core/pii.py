"""Spec 58 §3 — PII classification registry + masking.

The single source of truth for which persisted fields carry personal data, and at
what sensitivity. Two jobs:

- ``mask()`` produces a redacted form of a value so logs and AI context send
  task-scoped, masked PII (spec 58 §3 / 63 §12) — Claude never receives a raw
  government-ID or disability detail just because it sits on the same row.
- ``registry_summary()`` lets the ``/goal/security`` transparency surface report
  the live field-by-class counts, so the page's PII numbers are read from this
  registry rather than asserted in prose.

Classification follows the spec 42 §3.2 / spec 46 sensitivity tiers:

- ``pii``            — ordinary personal data (email, phone, DOB, names).
- ``pii_sensitive``  — FERPA education records (GPA, transcripts, test scores).
- ``policy_gated``   — identity / eligibility data released only under an explicit
                       policy gate (government-ID, passport, citizenship,
                       financial-proof band).
- ``health_pii``     — health / disability data (accommodations, insurance).

This is a *registry + helper*, not a schema change — no column is altered. Spec 58
§3's column-level encryption for the ``policy_gated`` / ``health_pii`` tiers is the
named next step (KMS envelope, spec §12), surfaced as ``planned`` on /goal/security;
``encryption_target_count`` reports how many fields that work would cover.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

_BULLET = "•"  # • — the mask fill char


class PIIClass(StrEnum):
    """Sensitivity tiers, ordered least → most sensitive."""

    PII = "pii"
    PII_SENSITIVE = "pii_sensitive"  # FERPA education records
    POLICY_GATED = "policy_gated"  # government-ID / financial / eligibility
    HEALTH = "health_pii"  # health / disability


CLASS_LABELS: dict[PIIClass, str] = {
    PIIClass.PII: "Personal",
    PIIClass.PII_SENSITIVE: "FERPA education record",
    PIIClass.POLICY_GATED: "Policy-gated identity",
    PIIClass.HEALTH: "Health / disability",
}

CLASS_DESCRIPTIONS: dict[PIIClass, str] = {
    PIIClass.PII: "Ordinary personal data — masked in logs and AI context.",
    PIIClass.PII_SENSITIVE: "Education records under FERPA — access-logged.",
    PIIClass.POLICY_GATED: "Released only under an explicit policy gate; column-encryption target.",
    PIIClass.HEALTH: "Health / disability data; never sent to AI context; "
    "column-encryption target.",
}

# The two tiers spec 58 §3 marks for column-level encryption (KMS envelope).
ENCRYPTION_TARGET_CLASSES: frozenset[PIIClass] = frozenset({PIIClass.POLICY_GATED, PIIClass.HEALTH})


@dataclass(frozen=True)
class PIIField:
    """One classified field: a real ``(model, field)`` and its sensitivity tier."""

    model: str
    field: str
    cls: PIIClass
    note: str = ""


# Authored from the real SQLAlchemy models (models/user.py, models/student.py).
# Every entry names a column that exists today; the tier drives masking + the
# encryption-target count. Not exhaustive of every personal field — it captures
# the sensitive set the spec calls out, the way the rationale redaction map
# captures the institution-only signal set.
PII_REGISTRY: tuple[PIIField, ...] = (
    # ── Ordinary personal data ──────────────────────────────────────────────
    PIIField("User", "email", PIIClass.PII, "Login + contact email"),
    PIIField("StudentProfile", "date_of_birth", PIIClass.PII, "Date of birth"),
    PIIField("StudentProfile", "secondary_phone", PIIClass.PII, "Contact phone"),
    PIIField("StudentProfile", "emergency_contact", PIIClass.PII, "JSONB contact block"),
    PIIField("StudentProfile", "gender_identity", PIIClass.PII, "Self-described gender"),
    PIIField(
        "RecommendationRequest",
        "recommender_email",
        PIIClass.PII,
        "Third-party recommender email",
    ),
    PIIField("Institution", "contact_phone", PIIClass.PII, "Institution contact phone"),
    # ── FERPA education records ──────────────────────────────────────────────
    PIIField("AcademicRecord", "gpa", PIIClass.PII_SENSITIVE, "FERPA: reported GPA"),
    PIIField(
        "AcademicRecord",
        "normalized_gpa",
        PIIClass.PII_SENSITIVE,
        "FERPA: normalized GPA",
    ),
    # ── Policy-gated identity / eligibility (column-encryption target) ───────
    PIIField("StudentProfile", "nationality", PIIClass.POLICY_GATED, "Nationality"),
    PIIField(
        "StudentProfile",
        "passport_issuing_country",
        PIIClass.POLICY_GATED,
        "Passport issuing country",
    ),
    PIIField(
        "StudentVisaInfo",
        "passport_expiration_date",
        PIIClass.POLICY_GATED,
        "Passport expiry",
    ),
    PIIField(
        "StudentVisaInfo",
        "country_of_citizenship",
        PIIClass.POLICY_GATED,
        "Citizenship",
    ),
    PIIField(
        "StudentVisaInfo",
        "financial_proof_amount_band",
        PIIClass.POLICY_GATED,
        "Financial-proof eligibility band",
    ),
    # ── Health / disability (column-encryption target) ──────────────────────
    PIIField(
        "StudentAccommodation",
        "category",
        PIIClass.HEALTH,
        "Disability / accommodation category",
    ),
    PIIField(
        "StudentAccommodation",
        "details_text",
        PIIClass.HEALTH,
        "Free-text disability detail",
    ),
    PIIField(
        "StudentAccommodation",
        "documentation_status",
        PIIClass.HEALTH,
        "Accommodation documentation status",
    ),
    PIIField(
        "StudentVisaInfo",
        "health_insurance_waiver_intent",
        PIIClass.HEALTH,
        "Health-insurance waiver intent",
    ),
)


def classify(model: str, field: str) -> PIIClass | None:
    """Return the sensitivity tier for a ``(model, field)``, or None if untagged."""
    for f in PII_REGISTRY:
        if f.model == model and f.field == field:
            return f.cls
    return None


def mask(value: Any, cls: PIIClass | None = None) -> str:
    """Return a redacted form of ``value`` safe for logs + AI context.

    Policy gating by tier:
    - ``policy_gated`` / ``health_pii`` → fully redacted (``[redacted]``); these
      never reveal a single character.
    - everything else → a partial mask that reveals only the first (and, for
      longer strings, the last) character, so a value stays greppable/diffable
      without exposing the data. Emails reveal only the first local char + TLD.

    ``None`` / empty → ``""``. Always over-masks rather than under-masks.
    """
    if value is None:
        return ""
    s = str(value)
    if not s:
        return ""
    if cls in ENCRYPTION_TARGET_CLASSES:
        return "[redacted]"
    if "@" in s:
        local, _, domain = s.partition("@")
        head = local[:1] if local else ""
        tld = domain.rsplit(".", 1)[-1] if "." in domain else ""
        suffix = f"@{_BULLET * 3}.{tld}" if tld else f"@{_BULLET * 3}"
        return f"{head}{_BULLET * 3}{suffix}"
    if len(s) <= 2:
        return _BULLET * len(s)
    if len(s) <= 4:
        return f"{s[0]}{_BULLET * (len(s) - 1)}"
    return f"{s[0]}{_BULLET * (len(s) - 2)}{s[-1]}"


def mask_field(model: str, field: str, value: Any) -> str:
    """Mask ``value`` using the tier registered for ``(model, field)``."""
    return mask(value, classify(model, field))


def registry_summary() -> dict[str, Any]:
    """Live counts for the /goal/security PII section — read from the registry."""
    counts: dict[str, int] = {c.value: 0 for c in PIIClass}
    for f in PII_REGISTRY:
        counts[f.cls.value] += 1
    models = sorted({f.model for f in PII_REGISTRY})
    return {
        "field_count": len(PII_REGISTRY),
        "class_count": len(PIIClass),
        "counts_by_class": counts,
        "models": models,
        "model_count": len(models),
        "encryption_target_count": sum(
            1 for f in PII_REGISTRY if f.cls in ENCRYPTION_TARGET_CLASSES
        ),
    }
