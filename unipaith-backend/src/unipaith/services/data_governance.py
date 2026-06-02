"""Spec 46 §1/§5/§9/§10 — institution data-governance reference data + config.

A pure-data module (like ``major_track_catalog``): the single source of truth for
the sub-processor list (§10), the verbatim brand commitments (§1), the retention
schedule (§5), and the per-institution governance settings (§9) helpers. No DB
models of its own — the only persisted state is the ``institutions.data_governance``
JSONB blob, merged over ``DEFAULT_DATA_GOVERNANCE`` here.
"""

from __future__ import annotations

from unipaith.core.exceptions import BadRequestException
from unipaith.models.fairness import PROTECTED_ATTRIBUTES

# §1 — the four brand commitments (verbatim). Contractual; shown on the
# institution data tab and compressed in student tooltips.
BRAND_COMMITMENTS: list[dict[str, str]] = [
    {
        "title": "Fit, not fame.",
        "body": (
            "We match students to programs where they'll thrive — not where the "
            "brand ranks highest."
        ),
    },
    {
        "title": "Explain everything.",
        "body": "Every match, every score, every recommendation comes with reasoning.",
    },
    {
        "title": "Partnership, not extraction.",
        "body": "We exchange value for data — we don't sell it.",
    },
    {
        "title": "Bias-avoidance is a practice.",
        "body": (
            "It's not a checkbox. Every cohort is audited; flags escalate to humans; "
            "decisions are never fully automated."
        ),
    },
]

# §10 — the sub-processor list. What we use, and what each one touches.
SUBPROCESSORS: list[dict[str, str]] = [
    {
        "name": "AWS (ECS, RDS, S3, CloudFront)",
        "touches": "All production data",
        "classification": "All classes including PII",
        "region": "us-east-1 (default)",
    },
    {
        "name": "Anthropic API",
        "touches": "Inference inputs (student data, application packets) at call time",
        "classification": "PII (during inference; not retained per Anthropic policy)",
        "region": "US",
    },
    {
        "name": "OpenAI API (parallel fallback)",
        "touches": "Same as Anthropic",
        "classification": "Same",
        "region": "US",
    },
    {
        "name": "AWS Cognito",
        "touches": "Auth credentials",
        "classification": "PII",
        "region": "us-east-1",
    },
    {
        "name": "AWS SES",
        "touches": "Outbound email",
        "classification": "PII (recipient address)",
        "region": "us-east-1",
    },
    {
        "name": "Stripe (planned)",
        "touches": "Payment card on file",
        "classification": "Financial PII",
        "region": "US",
    },
    {
        "name": "ACH B2B processor (planned)",
        "touches": "Institution payments",
        "classification": "Institution billing data",
        "region": "US",
    },
    {
        "name": "Sentry (or equivalent)",
        "touches": "Error telemetry",
        "classification": "Should NOT capture PII (sanitization required)",
        "region": "US",
    },
]

# Each sub-processor agreement: SOC 2 Type II (or audited equivalent); DPA;
# uptime SLA; data-residency commitment where available. A "no model training on
# UniPaith data" clause is required for every LLM provider.
SUBPROCESSOR_NOTE = (
    "Every sub-processor is bound by a DPA and SOC 2 Type II (or audited "
    "equivalent). A “no model training on UniPaith data” clause is "
    "required for every LLM provider. No raw student PII is ever sold, licensed, "
    "or rented — there is no data-broker line of business."
)

# §5 — data retention schedule (the rows students/institutions care about).
RETENTION_POLICY: list[dict[str, str]] = [
    {
        "data_type": "Account (auth)",
        "retention": "Indefinite while active; full purge 30 days after deletion request.",
    },
    {
        "data_type": "Profile signals",
        "retention": "Indefinite while account active; purge after the 30-day grace on deletion.",
    },
    {
        "data_type": "Application packets",
        "retention": "7 years after last cycle activity (FERPA + audit norms).",
    },
    {
        "data_type": "Discovery transcripts",
        "retention": "1 year after last activity; archive then auto-purge.",
    },
    {"data_type": "Engagement telemetry", "retention": "18 months rolling; raw events purged."},
    {"data_type": "AI audit ledger", "retention": "7 years (compliance + fairness audits)."},
    {
        "data_type": "Consent change history",
        "retention": "Indefinite — required for regulatory defense.",
    },
    {
        "data_type": "Documents (transcripts, portfolios)",
        "retention": "Same as application packets (7 years).",
    },
    {"data_type": "Search queries (raw text)", "retention": "90 days. Opt-in only."},
    {
        "data_type": "Disability / health data",
        "retention": "Same as profile; on deletion redact, don't archive.",
    },
]

# §9 — per-institution governance config defaults.
DEFAULT_DATA_GOVERNANCE: dict = {
    "override_expiry_weeks_default": 1,
    "protected_attributes_tracked": list(PROTECTED_ATTRIBUTES),
    "no_training_tier": False,
    # Phase 14 deferred — US only for now.
    "data_residency": "us",
}

_RESIDENCY_OPTIONS = {"us", "canada", "eu"}


def resolve_governance(stored: dict | None) -> dict:
    """Merge a stored ``institutions.data_governance`` blob over the defaults."""
    merged = dict(DEFAULT_DATA_GOVERNANCE)
    if stored:
        for key in DEFAULT_DATA_GOVERNANCE:
            if key in stored and stored[key] is not None:
                merged[key] = stored[key]
    return merged


def validate_governance_patch(patch: dict) -> dict:
    """Validate a partial governance update; returns the cleaned subset."""
    cleaned: dict = {}
    if "override_expiry_weeks_default" in patch:
        weeks = patch["override_expiry_weeks_default"]
        if not isinstance(weeks, int) or not (1 <= weeks <= 4):
            raise BadRequestException("override_expiry_weeks_default must be an integer 1–4.")
        cleaned["override_expiry_weeks_default"] = weeks
    if "protected_attributes_tracked" in patch:
        attrs = patch["protected_attributes_tracked"]
        if not isinstance(attrs, list) or any(a not in PROTECTED_ATTRIBUTES for a in attrs):
            raise BadRequestException(
                "protected_attributes_tracked must be a subset of the tracked attributes."
            )
        cleaned["protected_attributes_tracked"] = list(dict.fromkeys(attrs))
    if "no_training_tier" in patch:
        cleaned["no_training_tier"] = bool(patch["no_training_tier"])
    if "data_residency" in patch:
        residency = patch["data_residency"]
        if residency not in _RESIDENCY_OPTIONS:
            raise BadRequestException("data_residency must be one of: us, canada, eu.")
        cleaned["data_residency"] = residency
    return cleaned
