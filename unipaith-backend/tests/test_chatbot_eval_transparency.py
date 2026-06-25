"""Spec 61 — the /build/chatbot-eval transparency surface.

Asserts the payload shape, that the constitution dimensions + version are read
live from the rubric files, that the eval-suite case counts equal what the
runner's loaders read off disk (so the page can't inflate the battery), that the
suites are present in the live runner, that the agent tiers resolve from the
registry, and that the public endpoint serves it unauthenticated and shows up in
the overview hub.
"""

from __future__ import annotations

from httpx import AsyncClient

from unipaith.ai.evals import runner
from unipaith.ai.evals.constitution import load_constitution
from unipaith.main import app
from unipaith.transparency.chatbot_eval import build_chatbot_eval

# asyncio_mode = "auto" (pyproject) runs the async tests without an explicit mark.


def test_payload_shape_is_consistent():
    payload = build_chatbot_eval(app.routes)
    for key in (
        "the_bar",
        "summary",
        "constitutions",
        "agents",
        "loop_stages",
        "eval_suites",
        "safety",
        "deterministic_checks",
        "build_tasks",
        "acceptance",
        "config_knobs",
        "routes",
        "open_questions",
    ):
        assert key in payload, f"missing {key}"

    s = payload["summary"]
    assert s["suite_count"] == len(payload["eval_suites"])
    assert s["loop_stage_count"] == len(payload["loop_stages"])
    assert s["build_task_count"] == len(payload["build_tasks"])
    assert s["acceptance_count"] == len(payload["acceptance"])
    # The honest live/partial/planned split sums to the total.
    assert s["tasks_live"] + s["tasks_partial"] + s["tasks_planned"] == s["build_task_count"]
    for t in payload["build_tasks"]:
        assert t["status"] in {"live", "partial", "planned"}


def test_constitution_dimensions_read_live_from_the_rubric():
    payload = build_chatbot_eval(app.routes)
    s = payload["summary"]
    student = load_constitution("student")
    assert s["constitution_version"] == student.version
    assert s["dimension_count"] == len(student.dimensions)
    assert s["hard_floor_count"] == len(student.hard_floor_keys)
    assert s["constitutions_present"] is True
    # Both agents are surfaced, each with its 7-dimension rubric.
    present = [c for c in payload["constitutions"] if c.get("present")]
    assert len(present) == 2
    for c in present:
        assert c["dimension_count"] == 7
        assert c["hard_floor_keys"] == ["safety"]


def test_eval_suite_case_counts_equal_what_the_runner_reads_off_disk():
    payload = build_chatbot_eval(app.routes)
    by_key = {x["key"]: x for x in payload["eval_suites"]}
    # The page reports exactly what the runner's loaders read — not a claim.
    assert by_key["redteam"]["case_count"] == len(runner.load_redteam())
    assert by_key["safety_crisis"]["case_count"] == len(runner.load_crisis())
    assert by_key["constitution_adherence"]["case_count"] == len(runner.load_constitution_cases())
    # Every suite the page lists is actually registered in the runner.
    for suite in payload["eval_suites"]:
        assert suite["in_runner"] is True, suite["key"]
        assert suite["status"] in {"live", "partial", "planned"}
    # The two safety suites are hard-floored.
    floors = {x["key"] for x in payload["eval_suites"] if x["hard_floor"]}
    assert {"safety_crisis", "redteam"} <= floors


def test_agents_run_on_qwen_with_tiers_from_the_registry():
    payload = build_chatbot_eval(app.routes)
    from unipaith.ai.agent_registry import tier_for

    assert payload["summary"]["agent_count"] == 2
    keys = {a["key"] for a in payload["agents"]}
    assert keys == {"student_advisor", "faculty_assistant"}
    for a in payload["agents"]:
        assert a["tier"] == tier_for(a["agent_name"])
    # 2026-06-25: Uni's conversation moved to Qwen via Together, so the agents are
    # no longer pinned to Claude — `all_agents_claude` is now False.
    assert payload["summary"]["all_agents_claude"] is False


def test_safety_floor_coverage_is_live():
    payload = build_chatbot_eval(app.routes)
    safety = payload["safety"]
    assert safety["always_on"] is True
    assert safety["crisis_pattern_count"] == 3
    assert safety["harmful_pattern_count"] == 4
    # The five deterministic checks are surfaced.
    names = {c["name"] for c in payload["deterministic_checks"]}
    assert {"no_generation", "no_pii_leak", "no_admit_deny", "refusal_correct"} <= names


def test_routes_resolved_live_from_route_table():
    payload = build_chatbot_eval(app.routes)
    routes = payload["routes"]
    # The student advisor's discovery surface is actually served.
    assert any("/discovery" in p for p in routes["discovery"])
    # The faculty assistant bucket is institution-side only (not the student inbox).
    assert all("/institutions/" in p for p in routes["institution_reply"])


async def test_endpoint_is_public(client: AsyncClient):
    r = await client.get("/api/v1/build/chatbot-eval")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["summary"]["dimension_count"] == 7
    assert body["summary"]["agent_count"] == 2


async def test_overview_includes_chatbot_eval_surface(client: AsyncClient):
    r = await client.get("/api/v1/build/overview")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "chatbot_eval" in body
    keys = {s["key"] for s in body["surfaces"]}
    assert "chatbot-eval" in keys
    surface = next(s for s in body["surfaces"] if s["key"] == "chatbot-eval")
    assert surface["spec"] == "61"
    assert surface["path"] == "/goal/chatbot-eval"
