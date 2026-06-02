"""Spec 60 — public reference API, system-guarded ops, and the /build/knowledge
transparency surface.

Covers acceptance #1 (only allowlisted sources; the registry is system-guarded)
and the public, provenance-carrying reference reads, plus the /goal/knowledge
payload shape and its presence in the /goal hub overview.
"""

from __future__ import annotations

from httpx import AsyncClient

from unipaith.config import settings
from unipaith.main import app
from unipaith.services.crawler.seed import seed_all
from unipaith.transparency.knowledge import build_knowledge

PREFIX = "/api/v1"


def test_build_knowledge_payload_shape_is_consistent():
    payload = build_knowledge(app.routes)
    for key in (
        "the_bar",
        "summary",
        "benchmark",
        "reference_graph",
        "pipeline",
        "change_event_types",
        "authority_ladder",
        "capabilities",
        "phases",
        "acceptance",
        "config_knobs",
        "routes",
        "open_questions",
    ):
        assert key in payload, f"missing {key}"
    s = payload["summary"]
    caps = payload["capabilities"]
    assert s["capability_count"] == len(caps)
    assert s["capabilities_live"] + s["capabilities_partial"] + s["capabilities_planned"] == len(
        caps
    )
    # The reference tables + engine tables are read live from the metadata.
    assert s["reference_tables_present"] == 9
    assert s["engine_tables_present"] == 4
    assert s["registered_source_count"] == 16
    # Every reference-graph table actually exists in the running schema.
    assert all(d["table_present"] for d in payload["reference_graph"])
    # The benchmark asset (§1A) is present.
    assert len(payload["benchmark"]) >= 5


async def test_build_knowledge_endpoint_public(client: AsyncClient):
    resp = await client.get(f"{PREFIX}/build/knowledge")
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"]["live_is_source_of_truth"] is True
    assert body["summary"]["reference_domain_count"] == 8


async def test_overview_includes_knowledge_surface(client: AsyncClient):
    resp = await client.get(f"{PREFIX}/build/overview")
    assert resp.status_code == 200
    body = resp.json()
    assert "knowledge" in body
    keys = {s["key"] for s in body["surfaces"]}
    assert "knowledge" in keys
    surface = next(s for s in body["surfaces"] if s["key"] == "knowledge")
    assert surface["path"] == "/goal/knowledge"
    assert surface["spec"] == "60"


async def test_reference_reads_are_public_and_carry_provenance(client: AsyncClient, db_session):
    await seed_all(db_session)

    resp = await client.get(f"{PREFIX}/reference/occupations")
    assert resp.status_code == 200
    rows = resp.json()
    assert rows, "expected seeded occupations"
    first = rows[0]
    prov = first["provenance"]
    assert prov["source"] == "seed"
    assert prov["source_url"]
    assert prov["confidence"] is not None
    assert prov["status"] in ("live", "provisional")

    # Other domains are served too.
    for path in (
        "tests",
        "visas",
        "geo-cost",
        "majors",
        "rankings",
        "accreditation",
        "scholarships",
    ):
        r = await client.get(f"{PREFIX}/reference/{path}")
        assert r.status_code == 200, path

    summary = (await client.get(f"{PREFIX}/reference/summary")).json()
    assert summary["total"] > 0
    assert summary["occupations"] >= 1


async def test_ops_api_is_system_guarded(client: AsyncClient, monkeypatch):
    # No token configured → locked (403).
    monkeypatch.setattr(settings, "crawler_ops_token", "")
    denied = await client.get(f"{PREFIX}/crawler/sources")
    assert denied.status_code == 403

    # With a configured token + matching header → 200.
    monkeypatch.setattr(settings, "crawler_ops_token", "secret-ops")
    ok = await client.get(f"{PREFIX}/crawler/sources", headers={"X-Ops-Token": "secret-ops"})
    assert ok.status_code == 200
    # Wrong token → 403.
    wrong = await client.get(f"{PREFIX}/crawler/sources", headers={"X-Ops-Token": "nope"})
    assert wrong.status_code == 403
