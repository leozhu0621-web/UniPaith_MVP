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
from unipaith.models.base import Base
from unipaith.transparency.acceptance import BLOCKERS, JOURNEYS, build_acceptance
from unipaith.transparency.api_contract import build_api_contract
from unipaith.transparency.data_model import PLANNED, build_data_model
from unipaith.transparency.features import ALL_FEATURES, build_features
from unipaith.transparency.production import BUILD_TASKS, PILLARS, SLOS, build_production
from unipaith.transparency.roadmap import PHASES, build_roadmap
from unipaith.transparency.ux_benchmark import (
    ACCEPTANCE,
    INTERACTION_STANDARDS,
    SURFACES,
    build_ux_benchmark,
)

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


def _live_table_count() -> int:
    """Independent recount of the live SQLAlchemy metadata tables."""
    return len(Base.metadata.tables)


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


# ── Data model (spec 51) — the live, can't-drift table map ──────────────────


def test_data_model_table_count_matches_live_metadata():
    """The reported table count must equal an independent recount of the live
    SQLAlchemy metadata — the map is introspected from the running models, so it
    can never drift from the deployed schema."""
    dm = build_data_model()
    assert dm["summary"]["table_count"] == _live_table_count()


def test_data_model_domains_partition_every_table():
    dm = build_data_model()
    # Every live table lands in exactly one domain.
    assert sum(d["table_count"] for d in dm["domains"]) == dm["summary"]["table_count"]
    for d in dm["domains"]:
        for row in d["tables"]:
            assert row["table"] and row["module"]
            assert row["column_count"] > 0


def test_data_model_surfaces_doc_drift():
    dm = build_data_model()
    s = dm["summary"]
    # Spec 51 was drafted at 107 tables; the live schema has more.
    assert s["doc_claimed_tables"] == 107
    assert s["table_count"] > s["doc_claimed_tables"]
    assert s["jsonb_column_count"] > 0 and s["fk_count"] > 0


def test_data_model_planned_presence_is_computed_live():
    dm = build_data_model()
    s = dm["summary"]
    assert s["planned_total"] == len(PLANNED)
    # Some §8 'not built' items shipped since the doc (payments, story-bank).
    assert s["planned_now_live"] >= 2
    by_table = {p["table"]: p for p in dm["planned"]}
    assert by_table["payments"]["live"] is True
    assert by_table["student_follows"]["live"] is False
    assert by_table["student_follows"]["covered_by_live"] is True  # institution_follows


def test_data_model_already_built_items_are_live():
    dm = build_data_model()
    for b in dm["already_built"]:
        assert b["live"] is True, f"{b['table']} should be live"


# ── Acceptance & runbook (spec 52) — readiness read from the running system ──


def test_acceptance_readiness_reads_the_live_system():
    acc = build_acceptance(app.routes)
    s = acc["summary"]
    assert s["route_count"] == _live_route_count()
    assert s["table_count"] == _live_table_count()
    assert s["agent_count"] > 0
    assert s["boots"] is True
    assert s["launch_blockers_total"] == len(BLOCKERS)


def test_acceptance_has_two_journeys_with_steps():
    acc = build_acceptance(app.routes)
    assert len(acc["journeys"]) == len(JOURNEYS) == 2
    assert {j["key"] for j in acc["journeys"]} == {"student", "institution"}
    for j in acc["journeys"]:
        assert j["steps"] and all(st["title"] and st["detail"] for st in j["steps"])


def test_acceptance_blockers_well_formed_and_gate_launch_ready():
    acc = build_acceptance(app.routes)
    for b in acc["launch_blockers"]:
        assert b["status"] in ("cleared", "deferred")
        assert b["title"] and b["evidence"]
    s = acc["summary"]
    assert s["launch_ready"] == (
        s["boots"]
        and s["launch_blockers_cleared"] == s["launch_blockers_total"]
        and s["mvp_features_complete"]
    )


# ── UX benchmark (spec 53) — narrative authored, backing resolved live ──────


def test_ux_benchmark_shape_and_classifications():
    p = build_ux_benchmark(app.routes)
    s = p["summary"]
    assert s["surface_count"] == len(SURFACES) == len(p["surfaces"])
    assert s["standard_count"] == len(INTERACTION_STANDARDS) == len(p["standards"])
    assert s["acceptance_count"] == len(ACCEPTANCE) == len(p["acceptance"])
    assert p["the_bar"]["statement"]
    assert set(p["the_bar"]["benchmarks"]) == {"LinkedIn", "Handshake"}

    valid_benchmarks = {"linkedin", "handshake", "chatgpt", "ats"}
    for surface in p["surfaces"]:
        assert surface["name"] and surface["benchmark"] and surface["files"]
        assert surface["build_contract"], f"{surface['key']} has no build contract"
        assert surface["benchmark_key"] in valid_benchmarks
        for spec in surface["specs"]:
            assert _SPEC_RE.match(spec), f"surface {surface['key']} spec {spec!r} malformed"
    for standard in p["standards"]:
        assert standard["title"] and standard["body"] and standard["mechanism"]
    assert p["empty_state"]["rule"]
    assert len(p["empty_state"]["first_run"]) == 2


def test_ux_benchmark_backing_resolves_live():
    """Every surface's backing count is an independent recount of the live route
    table — so the page can't claim a surface the deployed app doesn't serve."""
    rows = [
        (getattr(r, "path", ""), m)
        for r in app.routes
        for m in (getattr(r, "methods", None) or set())
        if getattr(r, "path", "").startswith(_API_PREFIX) and m not in _SKIP
    ]
    live_paths = {p for (p, _) in rows}
    payload = build_ux_benchmark(app.routes)
    by_key = {s["key"]: s for s in payload["surfaces"]}

    union: set[tuple[str, str]] = set()
    for surface in SURFACES:
        matched = [(p, m) for (p, m) in rows if any(mk in p for mk in surface.route_markers)]
        union.update(matched)
        # Every benchmarked surface is actually wired to live endpoints.
        assert matched, f"surface {surface.key} backs zero live routes"
        assert by_key[surface.key]["backed_route_count"] == len(matched)
        # The sample paths shown on the page are real, live routes.
        for sample in by_key[surface.key]["sample_paths"]:
            assert sample in live_paths

    assert payload["summary"]["backed_route_total"] == len(union)
    assert payload["summary"]["surfaces_backed"] == len(SURFACES)
    assert payload["summary"]["backed_route_total"] <= len(rows)


# ── Production readiness (spec 55) — narrative authored, posture read live ───


def test_production_shape_and_classifications():
    p = build_production(app)
    s = p["summary"]
    valid = {"live", "partial", "planned"}

    assert s["pillar_count"] == len(PILLARS) == len(p["pillars"])
    assert s["build_task_count"] == len(BUILD_TASKS) == len(p["build_tasks"])
    assert s["slo_count"] == len(SLOS) == len(p["slos"])
    assert p["the_bar"]["statement"] and p["the_bar"]["slo_headline"]

    # Counts partition cleanly across the three classifications.
    assert s["pillars_live"] + s["pillars_partial"] + s["pillars_planned"] == s["pillar_count"]
    assert s["tasks_live"] + s["tasks_partial"] + s["tasks_planned"] == s["build_task_count"]

    for pl in p["pillars"]:
        assert pl["status"] in valid
        assert pl["title"] and pl["blurb"] and pl["section"].startswith("§")
        assert pl["built"], f"pillar {pl['key']} claims no shipped substance"
    for t in p["build_tasks"]:
        assert t["status"] in valid
        assert t["text"] and t["evidence"] and t["section"].startswith("§")


def test_production_config_knobs_read_live():
    """The config knobs are read straight off the running ``settings`` — the page
    shows the deployed values, not a doc snapshot."""
    from unipaith.config import settings

    p = build_production(app)
    s = p["summary"]
    assert s["config_group_count"] == len(p["config_groups"])
    assert s["config_knob_count"] == sum(len(g["knobs"]) for g in p["config_groups"]) > 0
    knobs = {k["name"]: k["value"] for g in p["config_groups"] for k in g["knobs"]}
    assert knobs["db_pool_size"] == settings.db_pool_size
    assert knobs["rate_limit_per_minute"] == settings.rate_limit_per_minute
    assert knobs["ai_request_timeout_s"] == settings.ai_request_timeout_seconds


def test_production_health_probes_and_middleware_resolve_live():
    """Health probes are resolved from the live route table and the middleware
    count is the real stack — so the page can't claim probes the app doesn't serve."""
    found = {
        getattr(r, "path", "")
        for r in app.routes
        if getattr(r, "path", "").startswith(_API_PREFIX)
        and getattr(r, "path", "").endswith(("/health", "/ready"))
        and any(m not in _SKIP for m in (getattr(r, "methods", None) or set()))
    }
    p = build_production(app)
    assert set(p["health_probes"]["paths"]) == found
    assert found == {f"{_API_PREFIX}/health", f"{_API_PREFIX}/ready"}
    assert p["summary"]["health_route_count"] == p["health_probes"]["count"] == 2
    # Middleware count equals the real stack; cache reports its live counters.
    assert p["middleware"]["count"] == p["summary"]["middleware_count"] >= 3
    assert p["middleware"]["classes"]
    assert "hit_rate" in p["cache"] and p["cache"]["backend"] == "memory"


# ── Public endpoints ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_production_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/build/production")
    assert resp.status_code == 200
    body = resp.json()
    for key in (
        "the_bar",
        "summary",
        "pillars",
        "config_groups",
        "middleware",
        "scheduler",
        "health_probes",
        "cache",
        "build_tasks",
        "slos",
        "open_questions",
    ):
        assert key in body
    assert body["summary"]["pillar_count"] == len(PILLARS)
    assert body["health_probes"]["count"] == 2


@pytest.mark.asyncio
async def test_overview_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/build/overview")
    assert resp.status_code == 200
    body = resp.json()
    for key in (
        "roadmap",
        "features",
        "api",
        "agents",
        "data_model",
        "acceptance",
        "production",
        "search",
        "surfaces",
    ):
        assert key in body
    assert len(body["surfaces"]) == 9
    assert {s["key"] for s in body["surfaces"]} == {
        "claude-api",
        "roadmap",
        "features",
        "api",
        "data-model",
        "acceptance",
        "experience",
        "backend",
        "search",
    }
    # Spec 55 — the backend surface carries the pillar count read from the run.
    backend = next(s for s in body["surfaces"] if s["key"] == "backend")
    assert backend["spec"] == "55"
    assert backend["path"] == "/goal/backend"
    assert backend["stat"] == body["production"]["pillar_count"]
    # Spec 56 — the search surface carries the live-capability count read from the run.
    search = next(s for s in body["surfaces"] if s["key"] == "search")
    assert search["spec"] == "56"
    assert search["path"] == "/goal/search"
    assert search["stat"] == (
        f"{body['search']['capabilities_live']}/{body['search']['capability_count']}"
    )


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


@pytest.mark.asyncio
async def test_data_model_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/build/data-model")
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"]["table_count"] > 0
    assert body["domains"] and body["conventions"]
    assert body["already_built"] and body["planned"]


@pytest.mark.asyncio
async def test_acceptance_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/build/acceptance")
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"]["launch_blockers_total"] == len(BLOCKERS)
    assert len(body["journeys"]) == 2
    assert body["dod"] and body["integration_gates"] and body["signoff"]


@pytest.mark.asyncio
async def test_ux_benchmark_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/build/ux-benchmark")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("the_bar", "summary", "surfaces", "standards", "empty_state", "acceptance"):
        assert key in body
    # Every benchmarked surface is wired to live endpoints (the self-verifying claim).
    assert body["summary"]["surfaces_backed"] == body["summary"]["surface_count"]
    assert all(s["backed_route_count"] > 0 for s in body["surfaces"])
