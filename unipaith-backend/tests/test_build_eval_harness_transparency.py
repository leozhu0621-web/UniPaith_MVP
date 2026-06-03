"""Spec 62 — the /build/eval-harness transparency surface.

Asserts the payload shape, that the consumers are resolved live from the
``harness.CONSUMERS`` registry, that the golden-case counts equal what the
``case_store`` reads off disk (so the page can't inflate the set), that the two
added tables are present in the running SQLAlchemy metadata, that the CI suites
are registered in the live runner, and that the public endpoint serves it
unauthenticated and shows up in the overview hub as the 15th surface.
"""

from __future__ import annotations

from httpx import AsyncClient

from unipaith.ai.evals import case_store, harness, runner
from unipaith.main import app
from unipaith.models.base import Base
from unipaith.transparency.eval_harness import build_eval_harness

# asyncio_mode = "auto" (pyproject) runs the async tests without an explicit mark.


def test_payload_shape_is_consistent():
    payload = build_eval_harness(app.routes)
    for key in (
        "the_bar",
        "summary",
        "consumers",
        "adapter_hooks",
        "eval_modes",
        "suites",
        "data_model",
        "synthetic_redteam",
        "slos",
        "cost_controls",
        "phases",
        "acceptance",
        "open_questions",
        "config_knobs",
        "routes",
        "tiers",
    ):
        assert key in payload, f"missing {key}"

    s = payload["summary"]
    assert s["consumer_count"] == len(payload["consumers"])
    assert s["eval_mode_count"] == len(payload["eval_modes"])
    assert s["acceptance_count"] == len(payload["acceptance"])
    assert s["phase_count"] == len(payload["phases"])
    for a in payload["acceptance"]:
        assert a["status"] in {"live", "partial", "planned"}
    for m in payload["eval_modes"]:
        assert m["status"] in {"live", "partial", "planned"}


def test_consumers_resolved_live_from_the_registry():
    payload = build_eval_harness(app.routes)
    live = [c for c in payload["consumers"] if c["status"] == "live"]
    # The live consumers are exactly the harness registry — read, not asserted.
    assert {c["key"] for c in live} == set(harness.CONSUMERS)
    assert payload["summary"]["consumers_live"] == len(harness.CONSUMERS)
    # The chatbot + extraction consumers are both live; match_rationale is planned.
    keys = {c["key"] for c in payload["consumers"]}
    assert {"chatbot", "extraction"} <= keys
    assert any(c["status"] == "planned" for c in payload["consumers"])


def test_golden_counts_equal_what_case_store_reads_off_disk():
    payload = build_eval_harness(app.routes)
    by_key = {c["key"]: c for c in payload["consumers"]}
    for consumer in harness.CONSUMERS:
        assert by_key[consumer]["golden_case_count"] == case_store.golden_count(consumer)
    # The headline total is the sum across the live consumers.
    assert payload["summary"]["golden_case_total"] == sum(
        case_store.golden_count(c) for c in harness.CONSUMERS
    )


def test_extraction_consumer_has_the_hard_floor_dimension():
    payload = build_eval_harness(app.routes)
    extraction = next(c for c in payload["consumers"] if c["key"] == "extraction")
    floors = {d["key"] for d in extraction["dimensions"] if d["hard_floor"]}
    assert "no_fabrication" in floors
    # Its judge is independent of the system under test (62 §4).
    assert extraction["judge"]["independent"] is True
    # Every extraction dimension is deterministic (gates with no key).
    assert all(d["kind"] == "deterministic" for d in extraction["dimensions"])


def test_added_tables_present_in_live_metadata():
    payload = build_eval_harness(app.routes)
    new_tables = {t["name"]: t for t in payload["data_model"]["new_tables"]}
    assert set(new_tables) == {"eval_cases", "eval_results"}
    for t in new_tables.values():
        assert t["present"] is True, t["name"]
        assert t["present"] == (t["name"] in Base.metadata.tables)
        assert t["column_count"] > 0
    assert payload["summary"]["new_tables_present"] == 2
    # The reused ml_loop tables are confirmed present too.
    for t in payload["data_model"]["reused_tables"]:
        assert t["present"] is True, t["name"]


def test_ci_suites_registered_in_the_live_runner():
    payload = build_eval_harness(app.routes)
    for suite in payload["suites"]:
        assert suite["in_runner"] is True, suite["key"]
        assert suite["key"] in runner.SUITES
    # The eval modes name a backing ml_loop table that actually exists.
    for m in payload["eval_modes"]:
        assert m["backing_table_present"] == (m["backing_table"] in Base.metadata.tables)


async def test_endpoint_is_public(client: AsyncClient):
    r = await client.get("/api/v1/build/eval-harness")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["summary"]["consumers_live"] == len(harness.CONSUMERS)
    assert body["summary"]["new_tables_present"] == 2


async def test_overview_includes_eval_harness_surface(client: AsyncClient):
    r = await client.get("/api/v1/build/overview")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "eval_harness" in body
    keys = {s["key"] for s in body["surfaces"]}
    assert "eval-harness" in keys
    surface = next(s for s in body["surfaces"] if s["key"] == "eval-harness")
    assert surface["spec"] == "62"
    assert surface["path"] == "/goal/eval-harness"
    assert surface["stat"] == body["eval_harness"]["consumers_live"]
