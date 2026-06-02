"""Spec 48/49/50 — build-transparency catalogs + public `/build/*` endpoints.

These tests pin the surface as a faithful mirror of the build:
- the roadmap covers all 14 phases with well-formed spec + gap refs,
- the feature map uses only valid classifications and stays internally consistent,
- the api-contract route count equals an *independent* recount of the live route
  table (it cannot over- or under-report what's deployed),
- the public endpoints return the full contract shapes.
"""

from __future__ import annotations

import re

import pytest
from httpx import AsyncClient

from unipaith.main import app
from unipaith.transparency.api_contract import build_api_contract
from unipaith.transparency.features import ALL_FEATURES, build_features
from unipaith.transparency.roadmap import PHASES, build_roadmap

_API_PREFIX = "/api/v1"
_SKIP = {"HEAD", "OPTIONS"}
_SPEC_RE = re.compile(r"^\d{2}")  # every spec ref starts with a two-digit doc id


# ── Roadmap (spec 48) ───────────────────────────────────────────────────────


def test_roadmap_covers_fourteen_phases():
    rm = build_roadmap()
    assert rm["summary"]["phase_count"] == 14
    assert [p["number"] for p in rm["phases"]] == list(range(1, 15))


def test_roadmap_statuses_and_counts():
    rm = build_roadmap()
    for p in rm["phases"]:
        assert p["status"] in ("shipped", "deferred")
        assert p["status_label"]
        assert p["goal"] and p["evidence"] and p["done_when"]
    assert rm["summary"]["shipped"] == 13
    assert rm["summary"]["deferred"] == 1
    # Phases 1–13 are the MVP; all must be shipped.
    assert rm["summary"]["mvp_complete"] is True


def test_roadmap_spec_and_gap_refs_well_formed():
    for p in PHASES:
        for spec in p.specs:
            assert _SPEC_RE.match(spec), f"phase {p.number} spec ref {spec!r} malformed"
        for gap in p.gap_items:
            assert gap.startswith("G-"), f"phase {p.number} gap id {gap!r} malformed"


# ── Features (spec 49) ──────────────────────────────────────────────────────


def test_features_classifications_valid():
    for f in ALL_FEATURES:
        assert f.side in ("student", "institution")
        assert f.status in ("covered", "written", "net_new")
        assert f.klass in ("core", "extend", "defer")
        assert _SPEC_RE.match(f.spec) or f.spec.startswith(("cross", "infra")), (
            f"feature {f.name!r} spec ref {f.spec!r} malformed"
        )


def test_features_summary_internally_consistent():
    ft = build_features()
    s = ft["summary"]
    assert s["feature_count"] == len(ft["features"]) == len(ALL_FEATURES)
    assert s["student_count"] + s["institution_count"] == s["feature_count"]
    assert sum(s["klass_counts"].values()) == s["feature_count"]
    assert s["delivered"] == sum(1 for f in ALL_FEATURES if f.delivered)
    # Every core/extend feature is delivered → the MVP cut is complete.
    assert s["mvp_complete"] is True
    # ahead_of_plan == deferred features the build shipped anyway.
    assert s["ahead_of_plan"] == sum(1 for f in ALL_FEATURES if f.klass == "defer" and f.delivered)
    assert s["ahead_of_plan"] >= 4  # international, fees, recruitment, graduate


# ── API contract (spec 50) — the live, can't-drift map ──────────────────────


def _live_route_count() -> int:
    """Independent recount of the live route table under /api/v1."""
    total = 0
    for r in app.routes:
        path = getattr(r, "path", "")
        methods = getattr(r, "methods", None)
        if path.startswith(_API_PREFIX) and methods:
            total += len([m for m in methods if m not in _SKIP])
    return total


def test_api_contract_route_count_matches_live_table():
    """The reported route count must equal an independent recount — the map is
    generated from the running app, so it can never drift from what's deployed."""
    contract = build_api_contract(app.routes)
    assert contract["summary"]["route_count"] == _live_route_count()


def test_api_contract_groups_sum_to_total():
    contract = build_api_contract(app.routes)
    assert sum(g["route_count"] for g in contract["groups"]) == contract["summary"]["route_count"]
    assert contract["summary"]["router_count"] == len(contract["groups"])


def test_api_contract_surfaces_itself_and_marks_public():
    contract = build_api_contract(app.routes)
    tags = {g["tag"] for g in contract["groups"]}
    assert "build-transparency" in tags  # the surface lists its own routes
    # Health and the build surface are public.
    build_group = next(g for g in contract["groups"] if g["tag"] == "build-transparency")
    assert build_group["access"] == "public"
    assert contract["summary"]["public_route_count"] >= 4


def test_api_contract_ai_endpoints_are_the_spec_set():
    contract = build_api_contract(app.routes)
    ai = contract["ai_endpoints"]
    assert ai, "expected the §6 AI endpoints to be detected"
    # Every detected AI endpoint is a genuine assistive surface (no over-capture).
    for path in ai:
        assert any(
            tok in path
            for tok in (
                "/messages",
                "/explain",
                "/rationale",
                "/strategy/generate",
                "/workshops/",
                "/identity/regenerate-summary",
            )
        ), f"{path} is not an expected AI endpoint"


# ── Public endpoints ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_overview_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/build/overview")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("roadmap", "features", "api", "agents", "surfaces"):
        assert key in body
    assert len(body["surfaces"]) == 4
    assert {s["key"] for s in body["surfaces"]} == {"claude-api", "roadmap", "features", "api"}


@pytest.mark.asyncio
async def test_roadmap_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/build/roadmap")
    assert resp.status_code == 200
    assert len(resp.json()["phases"]) == 14


@pytest.mark.asyncio
async def test_features_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/build/features")
    assert resp.status_code == 200
    assert resp.json()["summary"]["mvp_complete"] is True


@pytest.mark.asyncio
async def test_api_contract_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/build/api-contract")
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"]["route_count"] > 0
    assert body["conventions"] and body["status_taxonomy"] and body["groups"]
