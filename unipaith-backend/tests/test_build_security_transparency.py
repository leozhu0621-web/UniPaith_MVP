"""Spec 58 — the /build/security transparency surface.

Asserts the payload shape, that the control statuses sum consistently, that the
consent posture / PII counts / security-header set are resolved live from the
running modules (so the page can't claim a control the app doesn't run), and that
the public endpoint serves it unauthenticated + the overview lists the surface.
"""

from __future__ import annotations

from httpx import AsyncClient

from unipaith.ai.consent import AGENT_REQUIRES
from unipaith.ai.rationale_redaction import INSTITUTION_ONLY_KEY_SUBSTRINGS
from unipaith.core.middleware import SECURITY_HEADERS
from unipaith.core.pii import PII_REGISTRY
from unipaith.main import app
from unipaith.transparency.security import build_security

# asyncio_mode = "auto" (pyproject) runs the async tests without an explicit mark.


def test_build_security_payload_shape_is_consistent():
    payload = build_security(app)
    for key in (
        "the_bar",
        "summary",
        "controls",
        "consent",
        "pii",
        "headers",
        "auth",
        "config_knobs",
        "compliance",
        "build_tasks",
        "acceptance",
        "open_questions",
    ):
        assert key in payload, f"missing {key}"

    s = payload["summary"]
    controls = payload["controls"]
    assert s["control_count"] == len(controls)
    # The honest live/partial/planned split sums to the total.
    assert s["controls_live"] + s["controls_partial"] + s["controls_planned"] == s["control_count"]
    assert s["build_task_count"] == len(payload["build_tasks"])
    assert s["acceptance_count"] == len(payload["acceptance"])
    assert s["compliance_count"] == len(payload["compliance"])
    # Every control carries a valid status + the built/planned envelope + module.
    for c in controls:
        assert c["status"] in {"live", "partial", "planned"}
        assert isinstance(c["built"], list)
        assert isinstance(c["planned"], list)
        assert c["module"]


def test_consent_posture_reads_live_from_agent_requires():
    payload = build_security(app)
    s = payload["summary"]
    consent = payload["consent"]
    # The agent count is the live AGENT_REQUIRES size, not a hardcoded number.
    assert s["consent_agent_count"] == len(AGENT_REQUIRES)
    assert consent["agent_count"] == len(AGENT_REQUIRES)
    assert s["consent_lever_count"] == 4
    assert consent["levers"] == ["matching", "outreach", "analytics", "training"]
    # The per-lever gated-agent counts sum to ≤ the agent total (ungated agents
    # declare None) and each lever count matches a recount off AGENT_REQUIRES.
    by_lever = {lc["lever"]: lc["agent_count"] for lc in consent["lever_counts"]}
    for lever, count in by_lever.items():
        assert count == sum(1 for v in AGENT_REQUIRES.values() if v == lever)
    assert sum(by_lever.values()) <= len(AGENT_REQUIRES)
    # The redaction-map size is the live map length.
    assert s["redaction_map_size"] == len(INSTITUTION_ONLY_KEY_SUBSTRINGS)


def test_pii_and_header_counts_read_live():
    payload = build_security(app)
    s = payload["summary"]
    # PII field count equals the live registry size; classes carry counts.
    assert s["pii_field_count"] == len(PII_REGISTRY)
    assert payload["pii"]["field_count"] == len(PII_REGISTRY)
    assert s["pii_encryption_target_count"] > 0
    assert sum(c["count"] for c in payload["pii"]["classes"]) == len(PII_REGISTRY)
    # The header set is exactly what the middleware emits.
    assert s["security_header_count"] == len(SECURITY_HEADERS)
    assert payload["headers"]["names"] == list(SECURITY_HEADERS.keys())
    assert "Content-Security-Policy" in payload["headers"]["names"]


def test_auth_posture_and_guard_invariant():
    payload = build_security(app)
    s = payload["summary"]
    # In the test environment (development) the bypass is safe and guarded.
    assert s["prod_bypass_guarded"] is True
    assert s["auth_bypass_safe"] is True
    assert payload["auth"]["bypass_safe"] is True
    assert s["live_is_source_of_truth"] is True


async def test_build_security_endpoint_is_public(client: AsyncClient):
    r = await client.get("/api/v1/build/security")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["summary"]["control_count"] >= 10
    assert body["summary"]["consent_agent_count"] == len(AGENT_REQUIRES)


async def test_overview_includes_security_surface(client: AsyncClient):
    r = await client.get("/api/v1/build/overview")
    assert r.status_code == 200, r.text
    body = r.json()
    keys = {s["key"] for s in body["surfaces"]}
    assert "security" in keys
    surface = next(s for s in body["surfaces"] if s["key"] == "security")
    assert surface["spec"] == "58"
    assert surface["path"] == "/goal/security"
    assert surface["stat_label"] == "controls live"
    # The overview also carries the security summary block.
    assert "security" in body
    assert body["security"]["control_count"] >= 10


async def test_security_response_carries_hardened_headers(client: AsyncClient):
    """The middleware change ships: the strict CSP + the existing headers are set."""
    r = await client.get("/api/v1/build/security")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert "default-src 'none'" in r.headers.get("Content-Security-Policy", "")
