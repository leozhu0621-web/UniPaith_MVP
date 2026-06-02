"""Spec 42 §3.19–§3.20 / §4.17 — Prompt Library + Story Bank tests.

Covers: catalog seed + filtering, response upsert (version++ / STAR auto-detect /
§5 provenance), story CRUD + linking, summary counts, and the flag-ON inference
overlay (PromptCoach). The flag-ON path is exercised explicitly — the
MissingGreenlet class of bug only appears with the AI surface enabled.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai import prompt_coach
from unipaith.config import settings
from unipaith.models.student import StudentProfile
from unipaith.models.user import User
from unipaith.services.prompt_library_seed import SEED_COUNT

BASE = "/api/v1/students/me/prompt-library"

_STAR_ANSWER = (
    "During my junior year our robotics team was failing and morale was low. "
    "My goal was to rebuild the team before regionals. So I organized weekly "
    "stand-ups and I rewrote the build plan from scratch. As a result we placed "
    "2nd regionally, up from 11th — a 78% jump in score. Looking back, I learned "
    "that small consistent wins rebuild trust faster than big speeches."
)


async def _ensure_profile(db: AsyncSession, user: User) -> StudentProfile:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile


# ── Catalog ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_catalog_seeds_on_first_read(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    r = await student_client.get(f"{BASE}/prompts")
    assert r.status_code == 200
    prompts = r.json()
    assert len(prompts) == SEED_COUNT
    keys = {p["prompt_key"] for p in prompts}
    # The eight readiness-anchor keys must exist (prompt_coach.CORE_INTERVIEW_KEYS).
    for k in prompt_coach.CORE_INTERVIEW_KEYS:
        assert k in keys
    # Ordered by sort_order.
    orders = [p["sort_order"] for p in prompts]
    assert orders == sorted(orders)


@pytest.mark.asyncio
async def test_catalog_filters(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    r = await student_client.get(f"{BASE}/prompts", params={"channel": "interview"})
    assert r.status_code == 200
    assert all(p["target_channel"] == "interview" for p in r.json())
    r2 = await student_client.get(f"{BASE}/prompts", params={"intent": "failure"})
    assert all(p["intent_tag"] == "failure" for p in r2.json())
    assert len(r2.json()) >= 1


# ── Responses (§3.19) ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_response_detects_star_and_versions(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    r = await student_client.put(
        f"{BASE}/responses/proudest_accomplishment",
        json={"response_text": _STAR_ANSWER, "draft_status": "draft", "confidence_self_rating": 4},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # STAR auto-detected on save (system-derived).
    assert body["star_situation_present"] is True
    assert body["star_task_present"] is True
    assert body["star_action_present"] is True
    assert body["star_result_present"] is True
    assert body["star_reflection_present"] is True
    assert body["impact_metric_present"] is True
    assert body["version_count"] == 1
    # §5 record metadata.
    assert body["source"] == "student-typed"
    assert body["confidence"] == 70
    assert body["record_version"] == 1

    # Second save → versions increment (idempotent upsert on student+prompt_key).
    r2 = await student_client.put(
        f"{BASE}/responses/proudest_accomplishment",
        json={"response_text": _STAR_ANSWER + " More.", "draft_status": "final"},
    )
    assert r2.status_code == 200
    assert r2.json()["version_count"] == 2
    assert r2.json()["record_version"] == 2
    assert r2.json()["draft_status"] == "final"

    # Exactly one row per (student, prompt).
    lst = await student_client.get(f"{BASE}/responses")
    rows = [x for x in lst.json() if x["prompt_key"] == "proudest_accomplishment"]
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_unknown_prompt_key_404_not_500(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    r = await student_client.put(f"{BASE}/responses/not_a_real_prompt", json={"response_text": "x"})
    assert r.status_code == 404


# ── Story bank (§3.20) ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_story_crud_and_link(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    # Create.
    c = await student_client.post(
        f"{BASE}/stories",
        json={
            "title": "Robotics turnaround",
            "summary": "Rebuilt a failing team.",
            "primary_competency": "leadership",
            "competency_tags": ["resilience", "impact", "not_a_real_tag"],
            "context_tags": ["school"],
            "difficulty_tier": 4,
            "scale_tier": 3,
        },
    )
    assert c.status_code == 201, c.text
    story = c.json()
    sid = story["id"]
    assert story["primary_competency"] == "leadership"
    # Out-of-vocab tag dropped (DB CHECK safety).
    assert "not_a_real_tag" not in story["competency_tags"]
    assert story["source"] == "student-typed"

    # Update.
    u = await student_client.put(
        f"{BASE}/stories/{sid}", json={"title": "Robotics turnaround (v2)", "difficulty_tier": 5}
    )
    assert u.status_code == 200
    assert u.json()["title"] == "Robotics turnaround (v2)"
    assert u.json()["record_version"] == 2

    # Link to a response.
    lr = await student_client.put(
        f"{BASE}/responses/biggest_failure",
        json={"response_text": _STAR_ANSWER, "linked_story_id": sid},
    )
    assert lr.status_code == 200
    assert lr.json()["linked_story_id"] == sid

    # Delete.
    d = await student_client.delete(f"{BASE}/stories/{sid}")
    assert d.status_code == 204
    lst = await student_client.get(f"{BASE}/stories")
    assert all(s["id"] != sid for s in lst.json())


@pytest.mark.asyncio
async def test_link_foreign_story_rejected(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    import uuid

    r = await student_client.put(
        f"{BASE}/responses/why_now",
        json={"response_text": "x", "linked_story_id": str(uuid.uuid4())},
    )
    assert r.status_code == 400


# ── Summary (§4.17) ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_summary_flag_off_raw_counts(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User, monkeypatch
):
    monkeypatch.setattr(settings, "ai_prompt_library_v2_enabled", False)
    await _ensure_profile(db_session, mock_student_user)
    await student_client.put(
        f"{BASE}/responses/proudest_accomplishment",
        json={"response_text": _STAR_ANSWER, "draft_status": "final"},
    )
    s = await student_client.get(f"{BASE}/summary")
    assert s.status_code == 200
    body = s.json()
    assert body["inference_enabled"] is False
    assert body["total_prompts"] == SEED_COUNT
    assert body["answered_count"] == 1
    assert body["final_count"] == 1
    # No inference overlay when the flag is off.
    assert body["interview_readiness_band"] is None
    assert body["suggested_practice_plan"] is None


@pytest.mark.asyncio
async def test_summary_flag_on_attaches_inference_overlay(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User, monkeypatch
):
    # TEST THE AI SURFACE FLAG-ON (the MissingGreenlet class only shows here).
    monkeypatch.setattr(settings, "ai_prompt_library_v2_enabled", True)
    await _ensure_profile(db_session, mock_student_user)

    # Answer two core prompts strongly + add a story so the overlay has signal.
    await student_client.post(
        f"{BASE}/stories",
        json={
            "title": "Teamwork story",
            "primary_competency": "teamwork",
            "competency_tags": ["communication"],
        },
    )
    await student_client.put(
        f"{BASE}/responses/proudest_accomplishment",
        json={"response_text": _STAR_ANSWER, "draft_status": "final", "confidence_self_rating": 5},
    )

    s = await student_client.get(f"{BASE}/summary")
    assert s.status_code == 200
    body = s.json()
    assert body["inference_enabled"] is True
    assert body["interview_readiness_band"] in ("low", "medium", "high")
    assert isinstance(body["interview_readiness_score"], int)
    assert isinstance(body["competency_coverage_gaps"], list)
    assert isinstance(body["story_prompt_matching_table"], list)
    assert isinstance(body["revision_priority_list"], list)
    assert body["suggested_practice_plan"]


@pytest.mark.asyncio
async def test_summary_empty_profile_never_5xx(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User, monkeypatch
):
    monkeypatch.setattr(settings, "ai_prompt_library_v2_enabled", True)
    await _ensure_profile(db_session, mock_student_user)
    s = await student_client.get(f"{BASE}/summary")
    assert s.status_code == 200
    assert s.json()["interview_readiness_band"] == "low"


# ── Engine unit checks (pure, no DB) ───────────────────────────────────────────


def test_engine_star_and_impact_pure():
    a = prompt_coach.analyze_response(_STAR_ANSWER, word_limit=180)
    assert a["star_count"] == 5
    assert a["impact_metric_present"] is True
    assert a["authenticity_confidence_flag"] is True


def test_engine_empty_is_safe():
    a = prompt_coach.analyze_response("", word_limit=180)
    assert a["star_count"] == 0
    assert a["impact_metric_present"] is False
    summary = prompt_coach.coach_summary([], [], [])
    assert summary["interview_readiness_band"] == "low"
    assert summary["interview_readiness_score"] == 0
