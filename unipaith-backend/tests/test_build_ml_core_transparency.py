"""Spec 63 — the /build/ml-core transparency surface.

Asserts the payload shape, that the capability / acceptance statuses sum
consistently, that the boundary + pin + audit-gate + L3 weights are resolved live
from the running modules (so the page can't claim a boundary the code doesn't
enforce), and that the public endpoint serves it unauthenticated + the overview
lists the surface.
"""

from __future__ import annotations

from httpx import AsyncClient

from unipaith.ai import boundary
from unipaith.main import app
from unipaith.services.matching import DEFAULT_WEIGHTS
from unipaith.transparency.ml_core import build_ml_core

# asyncio_mode = "auto" (pyproject) runs the async tests without an explicit mark.


def test_build_ml_core_payload_shape_is_consistent():
    payload = build_ml_core(app.routes)
    for key in (
        "the_rule",
        "summary",
        "boundary_columns",
        "boundary",
        "model_roster",
        "provider_routing",
        "pipeline",
        "embeddings",
        "l3_scoring",
        "capabilities",
        "phases",
        "acceptance",
        "slos",
        "config_knobs",
        "routes",
        "open_questions",
    ):
        assert key in payload, f"missing {key}"

    s = payload["summary"]
    caps = payload["capabilities"]
    assert s["capability_count"] == len(caps)
    # The honest live/partial/planned split sums to the total.
    assert (
        s["capabilities_live"] + s["capabilities_partial"] + s["capabilities_planned"]
        == (s["capability_count"])
    )
    acc = payload["acceptance"]
    assert s["acceptance_count"] == len(acc)
    assert (
        s["acceptance_live"] + s["acceptance_partial"] + s["acceptance_planned"]
        == (s["acceptance_count"])
    )
    assert s["pipeline_stage_count"] == len(payload["pipeline"])
    assert s["phase_count"] == len(payload["phases"])
    assert s["slo_count"] == len(payload["slos"])
    assert s["config_knob_count"] == len(payload["config_knobs"])
    assert s["open_question_count"] == len(payload["open_questions"])
    # Every capability carries a valid status + the built/planned envelope.
    for c in caps:
        assert c["status"] in {"live", "partial", "planned"}
        assert isinstance(c["built"], list)
        assert isinstance(c["planned"], list)
    for a in acc:
        assert a["status"] in {"live", "partial", "planned"}


def test_boundary_counts_read_live_from_boundary_module():
    payload = build_ml_core(app.routes)
    s = payload["summary"]
    # The counts are the live boundary sets, not hardcoded numbers.
    assert s["human_facing_count"] == len(boundary.HUMAN_FACING)
    assert s["qwen_eligible_count"] == len(boundary.QWEN_ELIGIBLE)
    assert s["qwen_first_batch_count"] == len(boundary.QWEN_FIRST_BATCH)
    # The headline safety number — the Qwen ML backend serves zero human-facing
    # agents — is recomputed live, not asserted.
    assert s["human_facing_served_by_qwen"] == 0
    assert s["human_facing_pinned"] == len(boundary.HUMAN_FACING)
    assert s["qwen_eligible_routable"] == len(boundary.QWEN_ELIGIBLE)
    assert s["boundary_intact"] is True
    assert payload["boundary"]["leaked_agents"] == []
    # The classification lists round-trip the live sets.
    assert set(payload["boundary"]["human_facing"]) == set(boundary.HUMAN_FACING)
    assert set(payload["boundary"]["qwen_eligible"]) == set(boundary.QWEN_ELIGIBLE)


def test_audit_gate_and_routing_read_live():
    payload = build_ml_core(app.routes)
    s = payload["summary"]
    # The ai_turns.provider CHECK accepting 'qwen' is introspected from the live
    # model constraint.
    assert s["ai_turns_accepts_qwen"] is True
    # Qwen is registered as a transport; inert by default (qwen_enabled off).
    assert s["qwen_registered"] is True
    assert s["qwen_enabled"] is False
    assert s["qwen_available"] is False
    assert s["default_provider"] == "anthropic"
    routing = payload["provider_routing"]
    assert routing["qwen_models"]["workhorse"]
    assert routing["qwen_models"]["embedding"]


def test_model_roster_respects_the_boundary():
    payload = build_ml_core(app.routes)
    roster = payload["model_roster"]
    assert payload["summary"]["roster_boundary_ok"] is True
    # No human-facing roster row is served by Qwen; every Qwen row is non-human.
    for row in roster:
        if row["faces_human"]:
            assert row["provider"] == "anthropic"
        if row["provider"] == "qwen":
            assert row["faces_human"] is False
    assert payload["summary"]["roster_qwen_rows"] > 0
    assert payload["summary"]["roster_claude_rows"] > 0


def test_l3_weights_and_embeddings_read_live():
    payload = build_ml_core(app.routes)
    l3 = payload["l3_scoring"]
    assert l3["weights"] == dict(DEFAULT_WEIGHTS)
    assert l3["weight_sum"] == round(sum(DEFAULT_WEIGHTS.values()), 4) == 1.0
    emb = payload["embeddings"]
    # Live store stays Voyage 1024-d by default; Qwen target documented.
    assert emb["provider"] == "voyage"
    assert emb["live_dimension"] == 1024
    assert emb["matryoshka_target"] == 1536


async def test_build_ml_core_endpoint_is_public(client: AsyncClient):
    r = await client.get("/api/v1/build/ml-core")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["summary"]["human_facing_served_by_qwen"] == 0
    assert body["summary"]["human_facing_count"] == len(boundary.HUMAN_FACING)
    assert body["the_rule"]["headline"] == "Qwen processes. Claude communicates."


async def test_overview_includes_ml_core_surface(client: AsyncClient):
    r = await client.get("/api/v1/build/overview")
    assert r.status_code == 200, r.text
    body = r.json()
    keys = {s["key"] for s in body["surfaces"]}
    assert "ml-core" in keys
    surface = next(s for s in body["surfaces"] if s["key"] == "ml-core")
    assert surface["spec"] == "63"
    assert surface["path"] == "/goal/ml-core"
    assert surface["stat_label"] == "agents pinned to Claude"
    # The overview also carries the ml_core summary block.
    assert "ml_core" in body
    assert body["ml_core"]["human_facing_served_by_qwen"] == 0
