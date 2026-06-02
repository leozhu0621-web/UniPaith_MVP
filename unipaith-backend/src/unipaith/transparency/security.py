"""Spec 58 — security, trust & compliance, as queryable data.

Spec 58 is explicit that the backend is "mostly hardening + filling gaps, not
greenfield": the auth / consent / safety controls already exist (``core/security``,
``dependencies``, ``ai/consent``, ``ai/rationale_redaction``, ``core/middleware``,
``services/audit_service``) and the spec maps concrete controls + named gaps onto
them. This module turns that spec into the payload behind ``GET /build/security``
and the ``/goal/security`` page, the same way ``transparency.production`` turns
spec 55 into ``GET /build/production``.

The self-verifying hooks (read live from the running system, never asserted):

- the **auth posture** — ``settings.cognito_bypass`` / ``settings.environment`` and
  the boot-guard invariant ``auth_bypass_safe()`` — is read off the live config +
  ``core.security``, so the page can't claim a guard the deployed app doesn't run;
- the **consent posture** — the four levers, the agent count and the per-lever
  gated-agent counts — is read straight from ``ai.consent.AGENT_REQUIRES`` /
  ``DEFAULT_MASK``, so it equals what the LLM call site enforces;
- the **redaction-map size** is ``len(INSTITUTION_ONLY_KEY_SUBSTRINGS)`` from the
  live ``ai.rationale_redaction`` map;
- the **PII registry counts** are ``core.pii.registry_summary()`` — the same
  registry ``mask()`` uses;
- the **security headers** are the live ``core.middleware.SECURITY_HEADERS`` the
  app emits on every response.

The narrative (controls, their live/partial/planned split, the §10 checklist, the
§11 acceptance, the §12 open questions, the FERPA/GDPR map) is authored from spec
58; the numbers are introspected. Each control + build task is honestly classified
``live`` / ``partial`` / ``planned`` — the infra-dependent halves (column
encryption, AV scan, WAF, moderation service, incident runbook) are marked
``planned`` with the control that already anticipates them as evidence, exactly
like ``production.py`` does for ElastiCache / arq / metrics. DB-free and
unauthenticated.
"""

from __future__ import annotations

from dataclasses import dataclass

from unipaith.ai.consent import AGENT_REQUIRES, DEFAULT_MASK
from unipaith.ai.rationale_redaction import INSTITUTION_ONLY_KEY_SUBSTRINGS
from unipaith.config import settings
from unipaith.core.middleware import SECURITY_HEADERS
from unipaith.core.pii import CLASS_DESCRIPTIONS, CLASS_LABELS, PIIClass, registry_summary
from unipaith.core.security import auth_bypass_safe

Status = str  # "live" | "partial" | "planned"

# The four consent levers, in display order (ai/consent.py mask shape).
CONSENT_LEVERS: tuple[str, ...] = ("matching", "outreach", "analytics", "training")


# ── §1 · The bar ────────────────────────────────────────────────────────────
THE_BAR: dict = {
    "statement": (
        "Security is a property of the running system, not a policy doc: every "
        "request is authenticated and owner-checked, every AI/ML call passes a "
        "consent gate before it runs, sensitive data is classified and masked, "
        "and the controls that aren't fully built yet are named — not implied."
    ),
    "principle": "Assistive, consent-gated, least-privilege — with the gaps surfaced, not hidden.",
}


# ── §1–§9 · Controls ────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Control:
    key: str
    title: str
    section: str  # spec 58 section, e.g. "§2"
    status: Status
    module: str  # the real file the control lives in (or "—" for planned)
    blurb: str
    built: tuple[str, ...]  # what is live today
    planned: tuple[str, ...]  # the gap, honestly named


CONTROLS: tuple[Control, ...] = (
    Control(
        "authn",
        "Authentication",
        "§2",
        "live",
        "core/security.py",
        "Cognito JWT verified against JWKS; the dev token only works under bypass.",
        (
            "Cognito JWT validated against JWKS (RS256, issuer + audience checked)",
            "Dev token (dev:<uuid>:<role>) accepted only when cognito_bypass=true",
            "Boot guard refuses to start with the bypass on in production/staging",
            "Short-lived access + refresh; tokens scrubbed from logs",
        ),
        ("MFA-state surfaced on sensitive institution actions",),
    ),
    Control(
        "authz",
        "Authorization",
        "§2",
        "live",
        "dependencies.py",
        "Role guards plus owner-checks on every user-scoped resource.",
        (
            "require_student / require_institution_admin on every router",
            "Owner-checks: a student reads only their own data; an institution "
            "only its own applicants",
            "Route-guard audit test asserts every me-scoped route is guarded",
            "Three roles: student · institution_admin · admin",
        ),
        ("Centralized policy/ABAC engine (guards are per-route today)",),
    ),
    Control(
        "consent",
        "Consent enforcement",
        "§4",
        "live",
        "ai/consent.py",
        "Every AI/ML call resolves the student's consent mask before it runs.",
        (
            "Four-lever mask: matching · outreach · analytics · training",
            "is_call_permitted gates the call; a denied lever short-circuits to "
            "the rule-based fallback (never a 5xx)",
            "training=false governs any future tuning corpus (opt-in column)",
            "Consent change invalidates that student's cached AI artifacts",
        ),
        ("A single decorator on every agent entrypoint (most gate in-service today)",),
    ),
    Control(
        "redaction",
        "Asymmetric rationale",
        "§4",
        "live",
        "ai/rationale_redaction.py",
        "One artifact, projected differently: students never see institution-only signals.",
        (
            "Redaction map of institution-only signal substrings (cohort, "
            "selectivity, calibration, fairness internals)",
            "project_for_student strips them from prose, citations + breakdowns",
            "Contract test asserts the student payload leaks no institution-only key",
        ),
        (),
    ),
    Control(
        "pii",
        "PII protection",
        "§3",
        "partial",
        "core/pii.py",
        "Sensitive fields are classified and masked; column-encryption is the next step.",
        (
            "core/pii.py classification registry (pii · FERPA · policy-gated · health)",
            "mask() redacts PII in logs + AI context; health/policy-gated fully redacted",
            "RDS encryption at rest (KMS) on by default; TLS on every internal hop",
        ),
        (
            "Column-level KMS-envelope encryption on the policy-gated + health tiers",
            "PII-minimization: bulk PII processed in-VPC so less reaches the API layer",
        ),
    ),
    Control(
        "input_safety",
        "Input safety (OWASP)",
        "§5",
        "partial",
        "core/s3.py · api/*",
        "Parameterized queries, validated bodies, and upload caps; AV scan is next.",
        (
            "Pydantic v2 validates every request body (422 on bad input)",
            "SQLAlchemy parameterized only — no string-built SQL",
            "Upload content-type allowlist + size cap on documents/media",
            "React escapes by default; CORS allowlist; bearer-token (no classic CSRF)",
        ),
        (
            "S3 → ClamAV scan → quarantine before a document is parse_status=ready",
            "Crawler SSRF guard (source allowlist + private-IP block) + injection test",
        ),
    ),
    Control(
        "moderation",
        "Trust & safety / moderation",
        "§6",
        "planned",
        "—",
        "Abuse rate-limits exist; the UGC moderation pass is the named gap.",
        (
            "Abuse rate-limits on connect-requests + message spam",
            "Minors ↔ adults peer-matching block (spec 20 §6.4)",
        ),
        (
            "UGC moderation pass (rules + a cheap LLM classifier) → report → queue → action",
            "Crisis-signal detection → empathetic response + human/crisis escalation (hard-floor)",
        ),
    ),
    Control(
        "audit",
        "Audit trail",
        "§7",
        "live",
        "services/audit_service.py",
        "Everything sensitive is written to an append-only ledger.",
        (
            "Append-only audit log (DB trigger blocks update/delete)",
            "Logged: consent change · data export/deletion · AI-generated content · "
            "decision release · fairness override · integrity action",
            "Students can read their own access log (incl. institution access)",
        ),
        (),
    ),
    Control(
        "rate_limit",
        "Rate limiting",
        "§5",
        "live",
        "core/rate_limit.py",
        "Per-IP limiting with a structured 429; abuse buckets next.",
        (
            "slowapi per-IP limiter with a 429 + error-code handler",
            "rate_limit_enabled / rate_limit_per_minute config knobs",
        ),
        ("Per-user + stricter AI/bulk buckets (Retry-After); idempotency keys"),
    ),
    Control(
        "headers",
        "Security headers & transport",
        "§8",
        "live",
        "core/middleware.py",
        "Defence-in-depth headers on every response; TLS everywhere.",
        (
            "X-Content-Type-Options · X-Frame-Options · Referrer-Policy on every response",
            "Content-Security-Policy default-src 'none' (the API serves JSON)",
            "HSTS in production; CORS origin allowlist",
        ),
        ("CSP report-only telemetry endpoint",),
    ),
    Control(
        "secrets",
        "Secrets & supply chain",
        "§8",
        "partial",
        "infra/ · AWS Secrets Manager",
        "Secrets live only in Secrets Manager; the CI scanners are the gap.",
        (
            "DB password + keys injected from AWS Secrets Manager at boot — never in the bundle",
            "# pragma: allowlist secret convention in the repo",
            "RDS in a private subnet + security groups; no public S3",
        ),
        (
            "detect-secrets / gitleaks in pre-commit + CI",
            "pip-audit + npm audit (pinned lockfiles); WAF on CloudFront / ALB",
        ),
    ),
    Control(
        "compliance",
        "FERPA / GDPR ops",
        "§7",
        "partial",
        "core/data_safety.py",
        "Consent, access-logging and safe-delete are wired; the export bundle is next.",
        (
            "Education-record access logged; institution sees only its own applicants",
            "GDPR/CCPA consent levers (ai/consent.py); directory-info release honored",
            "ensure_can_delete_user guard + 30-day deactivate grace",
        ),
        (
            "data_export_service producing the portable bundle (spec 21)",
            "Full purge across tables after the grace window (extends data_safety)",
        ),
    ),
    Control(
        "incident",
        "Incident response",
        "§9",
        "planned",
        "—",
        "The forensic substrate exists; the runbook + on-call are the gap.",
        (
            "Structured logs + request-id make every request greppable for forensics",
            "Append-only audit log scopes the blast radius of any breach",
        ),
        (
            "infra/runbooks/incident.md — sev classification + on-call + notify timelines",
            "Breach → contain → assess → notify → blameless postmortem flow",
        ),
    ),
)


# ── §10 · Build-task checklist ──────────────────────────────────────────────
@dataclass(frozen=True)
class BuildTask:
    section: str
    status: Status
    text: str
    evidence: str


BUILD_TASKS: tuple[BuildTask, ...] = (
    BuildTask(
        "§2",
        "live",
        "Startup assert: cognito_bypass=false in production (fail boot)",
        "assert_secure_auth_config() runs at the top of the lifespan, outside any try.",
    ),
    BuildTask(
        "§2",
        "live",
        "Route audit: every me-scoped route has a role guard + owner check",
        "Asserted by tests/test_security_route_guards.py over the live route table.",
    ),
    BuildTask(
        "§3",
        "partial",
        "core/pii.py (classification + mask()); column encryption on policy-gated/health",
        "Registry + mask() are live; the column-level KMS envelope is planned.",
    ),
    BuildTask(
        "§4",
        "partial",
        "Consent gate on all AI/ML entrypoints; training-set filter + redaction contract test",
        "is_call_permitted + the redaction contract test are live; a single decorator is planned.",
    ),
    BuildTask(
        "§5",
        "partial",
        "Upload AV scan (S3→scan→quarantine) before parse_status=ready; type/size allowlist",
        "Content-type + size caps are live; the ClamAV scan step is planned.",
    ),
    BuildTask(
        "§5",
        "planned",
        "Crawler SSRF guard (allowlist + private-IP block); prompt-injection structural test",
        "Deferred with the crawler (spec 60), which is not yet in the repo.",
    ),
    BuildTask(
        "§6",
        "partial",
        "Moderation pass for UGC + minors↔adults block; crisis escalation hard-floor",
        "The minors↔adults block + abuse caps are live; the moderation pass is planned.",
    ),
    BuildTask(
        "§7",
        "partial",
        "data_export_service + full-purge-after-grace extension of data_safety.py",
        "ensure_can_delete_user + audit are live; the export bundle + full purge are planned.",
    ),
    BuildTask(
        "§8",
        "partial",
        "Secret scanner + pip-audit/npm audit in CI; WAF + security headers in infra",
        "Security headers are live; the CI scanners + WAF are planned.",
    ),
    BuildTask(
        "§9",
        "planned",
        "infra/runbooks/incident.md",
        "Deferred to the incident-response control; the forensic substrate is live.",
    ),
)


# ── §11 · Acceptance ────────────────────────────────────────────────────────
@dataclass(frozen=True)
class AcceptanceItem:
    status: Status
    text: str


ACCEPTANCE: tuple[AcceptanceItem, ...] = (
    AcceptanceItem(
        "live",
        "Prod refuses to boot with auth bypass on; every me-route role+owner guarded.",
    ),
    AcceptanceItem(
        "partial",
        "Policy-gated/health PII masked in logs + AI context; encrypted at rest (RDS KMS) — "
        "column-level encryption is the named next step.",
    ),
    AcceptanceItem(
        "live",
        "No AI/ML call runs without a passing consent mask; training=false governs the tuning set.",
    ),
    AcceptanceItem(
        "partial",
        "Uploads type/size-capped; AV scan, crawler SSRF guard + injection red-team are planned.",
    ),
    AcceptanceItem(
        "partial",
        "Deletion purges + audits; UGC moderation + crisis hard-floor are planned.",
    ),
    AcceptanceItem(
        "partial",
        "Secrets only in Secrets Manager; headers live — scanner + dep-audit + WAF planned.",
    ),
)


# ── §12 · Open questions ────────────────────────────────────────────────────
OPEN_QUESTIONS: tuple[dict, ...] = (
    {
        "q": "Column-encryption approach",
        "a": "A KMS envelope on the few highest-sensitivity fields (policy-gated + "
        "health) over sqlalchemy-utils EncryptedType — fewer moving parts, keys in KMS.",
    },
    {
        "q": "Antivirus engine",
        "a": "Start with ClamAV-on-Lambda (cost) on the S3 upload event; revisit a "
        "managed scan API if volume warrants.",
    },
    {
        "q": "Moderation model",
        "a": "Rules + a cheap classifier for the MVP; a full moderation model is a "
        "fast-follow once volume justifies it.",
    },
)


# ── FERPA / GDPR compliance map ─────────────────────────────────────────────
@dataclass(frozen=True)
class ComplianceItem:
    regime: str  # "FERPA" | "GDPR/CCPA" | "Retention"
    control: str
    status: Status
    module: str


COMPLIANCE: tuple[ComplianceItem, ...] = (
    ComplianceItem(
        "FERPA", "Education-record access is logged", "live", "services/audit_service.py"
    ),
    ComplianceItem(
        "FERPA", "Directory-info release preference honored", "live", "models/student.py"
    ),
    ComplianceItem(
        "FERPA", "An institution sees only its own applicants", "live", "dependencies.py"
    ),
    ComplianceItem(
        "GDPR/CCPA", "Four-lever consent, enforced at the call site", "live", "ai/consent.py"
    ),
    ComplianceItem(
        "GDPR/CCPA",
        "Right to erasure: safe-delete guard + 30-day grace",
        "partial",
        "core/data_safety.py",
    ),
    ComplianceItem(
        "GDPR/CCPA",
        "Right to portability: data-export bundle",
        "planned",
        "services/data_export_service.py",
    ),
    ComplianceItem(
        "Retention",
        "Audit + financial rows never hard-deleted",
        "live",
        "services/audit_service.py",
    ),
    ComplianceItem(
        "Retention",
        "Per-class TTL; PII soft-delete then purge after grace",
        "partial",
        "core/data_safety.py",
    ),
)


def _consent_lever_counts() -> list[dict]:
    """Per-lever count of agents gated behind it — read off AGENT_REQUIRES."""
    out: list[dict] = []
    for lever in CONSENT_LEVERS:
        count = sum(1 for needed in AGENT_REQUIRES.values() if needed == lever)
        out.append({"lever": lever, "agent_count": count})
    return out


def _config_knobs() -> list[dict]:
    """Live security-relevant config, read straight off ``settings``."""
    return [
        {"name": "environment", "value": settings.environment, "section": "§2"},
        {"name": "cognito_bypass", "value": settings.cognito_bypass, "section": "§2"},
        {"name": "debug", "value": settings.debug, "section": "§8"},
        {"name": "rate_limit_enabled", "value": settings.rate_limit_enabled, "section": "§5"},
        {"name": "rate_limit_per_minute", "value": settings.rate_limit_per_minute, "section": "§5"},
        {"name": "cors_allowlist_size", "value": len(settings.cors_origins), "section": "§8"},
        {
            "name": "cognito_pool_configured",
            "value": bool(settings.cognito_user_pool_id),
            "section": "§2",
        },
    ]


def build_security(app=None) -> dict:  # noqa: ANN001 — app kept for signature parity
    """Assemble the ``GET /build/security`` payload.

    Narrative is authored from spec 58; the auth posture, consent counts,
    redaction-map size, PII registry counts and security-header set are
    introspected from ``settings`` / ``ai.consent`` / ``ai.rationale_redaction`` /
    ``core.pii`` / ``core.middleware`` so the page mirrors the deployed controls.
    The ``app`` arg is accepted for parity with the other ``build_*`` functions.
    """
    pii = registry_summary()
    lever_counts = _consent_lever_counts()
    config_knobs = _config_knobs()
    header_names = list(SECURITY_HEADERS.keys())

    def _count(status: Status) -> int:
        return sum(1 for c in CONTROLS if c.status == status)

    def _task_count(status: Status) -> int:
        return sum(1 for t in BUILD_TASKS if t.status == status)

    controls_out = [
        {
            "key": c.key,
            "title": c.title,
            "section": c.section,
            "status": c.status,
            "module": c.module,
            "blurb": c.blurb,
            "built": list(c.built),
            "planned": list(c.planned),
        }
        for c in CONTROLS
    ]

    pii_classes = [
        {
            "key": cls.value,
            "label": CLASS_LABELS[cls],
            "description": CLASS_DESCRIPTIONS[cls],
            "count": pii["counts_by_class"][cls.value],
            "encryption_target": cls in {PIIClass.POLICY_GATED, PIIClass.HEALTH},
        }
        for cls in PIIClass
    ]

    return {
        "the_bar": dict(THE_BAR),
        "summary": {
            "control_count": len(CONTROLS),
            "controls_live": _count("live"),
            "controls_partial": _count("partial"),
            "controls_planned": _count("planned"),
            "build_task_count": len(BUILD_TASKS),
            "tasks_live": _task_count("live"),
            "tasks_partial": _task_count("partial"),
            "tasks_planned": _task_count("planned"),
            "acceptance_count": len(ACCEPTANCE),
            "acceptance_live": sum(1 for a in ACCEPTANCE if a.status == "live"),
            "consent_agent_count": len(AGENT_REQUIRES),
            "consent_lever_count": len(CONSENT_LEVERS),
            "consent_default_permissive": all(DEFAULT_MASK.values()),
            "redaction_map_size": len(INSTITUTION_ONLY_KEY_SUBSTRINGS),
            "pii_field_count": pii["field_count"],
            "pii_class_count": pii["class_count"],
            "pii_encryption_target_count": pii["encryption_target_count"],
            "security_header_count": len(header_names),
            "cors_allowlist_size": len(settings.cors_origins),
            "environment": settings.environment,
            "cognito_bypass": settings.cognito_bypass,
            "auth_bypass_safe": auth_bypass_safe(),
            "prod_bypass_guarded": True,
            "compliance_count": len(COMPLIANCE),
            "open_question_count": len(OPEN_QUESTIONS),
            "live_is_source_of_truth": True,
        },
        "controls": controls_out,
        "consent": {
            "levers": list(CONSENT_LEVERS),
            "lever_counts": lever_counts,
            "agent_count": len(AGENT_REQUIRES),
            "default_permissive": all(DEFAULT_MASK.values()),
            "redaction_map_size": len(INSTITUTION_ONLY_KEY_SUBSTRINGS),
            "note": "Each agent declares the lever it sits behind; a denied lever "
            "short-circuits to the rule-based fallback, never a 5xx.",
        },
        "pii": {
            "field_count": pii["field_count"],
            "class_count": pii["class_count"],
            "encryption_target_count": pii["encryption_target_count"],
            "model_count": pii["model_count"],
            "classes": pii_classes,
        },
        "headers": {
            "count": len(header_names),
            "names": header_names,
            "hsts_in_production": True,
            "note": "Set on every response by core/middleware.py; HSTS is added in "
            "production; CSP is skipped only for the debug-only docs routes.",
        },
        "auth": {
            "environment": settings.environment,
            "cognito_bypass": settings.cognito_bypass,
            "bypass_safe": auth_bypass_safe(),
            "pool_configured": bool(settings.cognito_user_pool_id),
            "note": "The dev token is accepted only when cognito_bypass=true, and the "
            "boot guard refuses to start with it on in production/staging.",
        },
        "config_knobs": config_knobs,
        "compliance": [
            {"regime": c.regime, "control": c.control, "status": c.status, "module": c.module}
            for c in COMPLIANCE
        ],
        "build_tasks": [
            {"section": t.section, "status": t.status, "text": t.text, "evidence": t.evidence}
            for t in BUILD_TASKS
        ],
        "acceptance": [{"status": a.status, "text": a.text} for a in ACCEPTANCE],
        "open_questions": [dict(q) for q in OPEN_QUESTIONS],
    }
