"""Spec 58 — the real hardening this spec ships, asserted.

These are the spec's own "audit scripts" (§2, §4) turned into tests plus unit
coverage for the net-new safe code (the boot guard, the PII registry/mask, the
consent gate, the asymmetric-redaction contract):

- the boot guard refuses to start with the dev auth bypass on in prod/staging;
- PII masks redact by tier (health/policy-gated fully, others partially);
- a denied consent lever short-circuits an AI agent;
- the student rationale projection leaks no institution-only signal key;
- every ``*/me/*`` route carries the ``get_current_user`` auth dependency.
"""

from __future__ import annotations

from fastapi.routing import APIRoute

from unipaith.ai.consent import is_call_permitted
from unipaith.ai.rationale_redaction import (
    flatten_keys,
    project_for_institution,
    project_for_student,
)
from unipaith.core import security
from unipaith.core.pii import PIIClass, classify, mask, registry_summary
from unipaith.dependencies import get_current_user
from unipaith.main import app
from unipaith.transparency.live_routes import expand_routes

# asyncio_mode = "auto" (pyproject) — the sync tests below run as plain functions.


# ── §2 · Boot guard ─────────────────────────────────────────────────────────
def test_boot_guard_raises_on_prod_bypass(monkeypatch):
    monkeypatch.setattr(security.settings, "environment", "production")
    monkeypatch.setattr(security.settings, "cognito_bypass", True)
    assert security.auth_bypass_safe() is False
    try:
        security.assert_secure_auth_config()
        raise AssertionError("guard did not fail boot with prod + bypass")
    except RuntimeError as e:
        assert "cognito_bypass" in str(e)


def test_boot_guard_guards_staging_too(monkeypatch):
    monkeypatch.setattr(security.settings, "environment", "staging")
    monkeypatch.setattr(security.settings, "cognito_bypass", True)
    assert security.auth_bypass_safe() is False


def test_boot_guard_allows_prod_without_bypass(monkeypatch):
    monkeypatch.setattr(security.settings, "environment", "production")
    monkeypatch.setattr(security.settings, "cognito_bypass", False)
    assert security.auth_bypass_safe() is True
    security.assert_secure_auth_config()  # must not raise


def test_boot_guard_allows_dev_bypass(monkeypatch):
    # The default test environment — bypass on, environment=development.
    monkeypatch.setattr(security.settings, "environment", "development")
    monkeypatch.setattr(security.settings, "cognito_bypass", True)
    assert security.auth_bypass_safe() is True
    security.assert_secure_auth_config()  # must not raise


# ── §3 · PII registry + mask ────────────────────────────────────────────────
def test_pii_mask_fully_redacts_sensitive_tiers():
    assert mask("dyslexia", PIIClass.HEALTH) == "[redacted]"
    assert mask("US123456", PIIClass.POLICY_GATED) == "[redacted]"


def test_pii_mask_partials_ordinary_pii():
    masked = mask("jane.doe@gmail.com", PIIClass.PII)
    assert masked.startswith("j")
    assert "jane" not in masked and "gmail" not in masked
    assert "•" in masked
    # A generic value keeps only first + last char.
    g = mask("Beijing", PIIClass.PII)
    assert g[0] == "B" and g[-1] == "g" and "•" in g


def test_pii_mask_none_and_empty():
    assert mask(None) == ""
    assert mask("") == ""


def test_pii_registry_is_classified_and_encryption_targets_counted():
    rs = registry_summary()
    assert rs["field_count"] == len(rs["models"]) or rs["field_count"] >= rs["model_count"]
    # Each registered field resolves to a tier.
    assert classify("AcademicRecord", "gpa") == PIIClass.PII_SENSITIVE
    assert classify("StudentAccommodation", "category") == PIIClass.HEALTH
    assert classify("Nope", "nope") is None
    # The encryption targets are exactly the policy-gated + health tiers.
    counts = rs["counts_by_class"]
    assert rs["encryption_target_count"] == (
        counts[PIIClass.POLICY_GATED.value] + counts[PIIClass.HEALTH.value]
    )
    assert rs["encryption_target_count"] > 0


# ── §4 · Consent gate ───────────────────────────────────────────────────────
def test_consent_gate_denies_when_lever_off():
    # The extractor sits behind the analytics lever (ai/consent.py).
    denied = {"matching": True, "outreach": True, "analytics": False, "training": True}
    granted = {"matching": True, "outreach": True, "analytics": True, "training": True}
    assert is_call_permitted("extractor", denied) is False
    assert is_call_permitted("extractor", granted) is True
    # A matching-gated agent is blocked when matching is off.
    assert is_call_permitted("rationale", {**granted, "matching": False}) is False


def test_consent_gate_allows_ungated_agents():
    # Workshop coaches declare no lever (the act of opening the workshop is consent).
    empty = {"matching": False, "outreach": False, "analytics": False, "training": False}
    assert is_call_permitted("workshop_coach", empty) is True


# ── §4 · Asymmetric rationale redaction contract ────────────────────────────
def test_student_projection_leaks_no_institution_only_key():
    fitness = {
        "academic_fit": 0.8,
        "cohort_percentile_band": "top-10",  # institution-only
        "selectivity_delta": -0.2,  # institution-only
    }
    student = project_for_student(
        rationale_text="A strong academic match.",
        cited_student_fields=["sparse.research_experience"],
        cited_program_fields=["program.outcomes", "program.selectivity_delta"],
        fitness_breakdown=fitness,
        confidence_breakdown={},
    )
    keys = flatten_keys(student.fitness_breakdown)
    assert "cohort_percentile_band" not in keys
    assert "selectivity_delta" not in keys
    assert "academic_fit" in keys  # the student's own signal survives
    # The institution-only program citation is dropped; the public one stays.
    assert "program.selectivity_delta" not in student.cited_program_fields
    assert "program.outcomes" in student.cited_program_fields
    assert student.redacted is True


def test_institution_projection_is_lossless():
    fitness = {"academic_fit": 0.8, "cohort_percentile_band": "top-10"}
    inst = project_for_institution(
        rationale_text="A strong academic match.",
        cited_student_fields=["sparse.research_experience"],
        cited_program_fields=["program.selectivity_delta"],
        fitness_breakdown=fitness,
        confidence_breakdown={},
    )
    assert "cohort_percentile_band" in flatten_keys(inst.fitness_breakdown)
    assert inst.redacted is False


# ── §2 · Route-guard audit (the spec's audit script) ────────────────────────
def _dependency_calls(dependant) -> set:
    calls: set = set()
    stack = [dependant]
    while stack:
        node = stack.pop()
        call = getattr(node, "call", None)
        if call is not None:
            calls.add(call)
        stack.extend(getattr(node, "dependencies", []) or [])
    return calls


def test_me_scoped_routes_carry_an_auth_guard():
    """Every ``/students/me/*`` and ``/institutions/me/*`` route must depend on
    ``get_current_user`` (require_student / require_institution_admin /
    require_faculty_* all depend on it). No me-scoped route relies on obscurity."""
    unguarded: list[str] = []
    checked = 0
    for route in expand_routes(app):
        inner = getattr(route, "_route", route)
        if not isinstance(inner, APIRoute):
            continue
        path = route.path
        if "/students/me/" not in path and "/institutions/me/" not in path:
            # Also catch the exact ``/me`` tail without a trailing segment.
            if not (path.endswith("/students/me") or path.endswith("/institutions/me")):
                continue
        checked += 1
        if get_current_user not in _dependency_calls(inner.dependant):
            unguarded.append(f"{sorted(route.methods)} {path}")
    assert checked > 0, "expected to find me-scoped routes to audit"
    assert not unguarded, "me-scoped routes missing an auth guard:\n" + "\n".join(unguarded)
