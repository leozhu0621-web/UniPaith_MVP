"""Phase A — Workshop feedback API functional tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unipaith.models.student import StudentProfile
from unipaith.models.user import User

WORKSHOPS = "/api/v1/students/me/workshops"


async def _ensure_profile(db: AsyncSession, user: User) -> StudentProfile:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile


# ── Essay ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_essay_feedback_returns_rubric_and_issues(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    short_essay = "I want to be a doctor. " * 5  # short, simple
    resp = await student_client.post(
        f"{WORKSHOPS}/essay/feedback",
        json={"essay_text": short_essay, "prompt_text": "Why this program?"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["domain"] == "essay"
    assert data["is_stub"] is True
    assert data["rubric_scores"]
    # Short essay should flag the length issue.
    issue_strings = [i["issue"] for i in data["structural_issues"]]
    assert any("shorter" in s.lower() for s in issue_strings)


@pytest.mark.asyncio
async def test_essay_feedback_too_short_rejected_at_pydantic(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """Schema enforces min_length=20 on essay_text — protects the stub
    heuristic from divide-by-zero / nonsense outputs."""
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        f"{WORKSHOPS}/essay/feedback",
        json={"essay_text": "too short"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_essay_feedback_long_essay_passes_length_check(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """A 500-word essay with 4 paragraphs should pass length and structure
    rubrics. Confirms the heuristic isn't always-pessimistic."""
    await _ensure_profile(db_session, mock_student_user)
    paragraph = (
        "I learned that effort compounds in ways I didn't initially expect. "
        "First, I tried to brute-force my coursework. However, the most "
        "valuable signals came from people who pushed me to revise. I "
        "discovered that asking better questions was the actual leverage. "
    ) * 5
    essay = "\n\n".join([paragraph] * 4)
    resp = await student_client.post(
        f"{WORKSHOPS}/essay/feedback",
        json={"essay_text": essay},
    )
    data = resp.json()
    rubric = data["rubric_scores"]
    assert rubric["length_appropriateness"] >= 3.5
    assert rubric["paragraph_structure"] >= 3.5


# ── Interview ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_interview_practice_returns_5_questions_no_answers(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        f"{WORKSHOPS}/interview/practice",
        json={"interview_type": "behavioral"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["domain"] == "interview"
    assert len(data["suggested_questions"]) >= 5
    # CRITICAL: no field carries a model answer. Every question item has
    # exactly {question, why}; there is no `answer` / `model_answer`.
    for q in data["suggested_questions"]:
        assert set(q.keys()) == {"question", "why"}


@pytest.mark.asyncio
@pytest.mark.parametrize("itype", ["behavioral", "technical", "general"])
async def test_interview_practice_each_type(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    itype: str,
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        f"{WORKSHOPS}/interview/practice",
        json={"interview_type": itype},
    )
    assert resp.status_code == 201
    assert len(resp.json()["suggested_questions"]) >= 5


# ── Test guidance ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_test_guidance_with_score_gap(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        f"{WORKSHOPS}/test/guidance",
        json={"test_type": "GRE", "current_score": 305, "target_score": 320},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["domain"] == "test"
    assert data["rubric_scores"]["gap"] == 15.0
    assert data["missing_elements"]


@pytest.mark.asyncio
async def test_test_guidance_already_at_target(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        f"{WORKSHOPS}/test/guidance",
        json={"test_type": "GRE", "current_score": 325, "target_score": 320},
    )
    data = resp.json()
    assert data["rubric_scores"]["gap"] == -5.0
    assert any(
        "above target" in e["element"].lower() or "consistency" in e["element"].lower()
        for e in data["missing_elements"]
    )


@pytest.mark.asyncio
async def test_test_guidance_invalid_test_type_rejected(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        f"{WORKSHOPS}/test/guidance",
        json={"test_type": "FAKE_TEST"},
    )
    assert resp.status_code == 422


# ── List runs ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_runs_filters_by_domain(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    # Seed one of each domain.
    await student_client.post(
        f"{WORKSHOPS}/essay/feedback",
        json={"essay_text": "short essay text I want feedback on. " * 5},
    )
    await student_client.post(f"{WORKSHOPS}/interview/practice", json={"interview_type": "general"})
    await student_client.post(
        f"{WORKSHOPS}/test/guidance",
        json={"test_type": "TOEFL", "current_score": 95, "target_score": 105},
    )

    all_runs = (await student_client.get(f"{WORKSHOPS}/runs")).json()
    assert len(all_runs) == 3

    essays = (await student_client.get(f"{WORKSHOPS}/runs?domain=essay")).json()
    assert len(essays) == 1 and essays[0]["domain"] == "essay"


# ── Auth ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_workshops_blocked_for_non_students(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    db_session.add(mock_institution_user)
    await db_session.commit()
    resp = await institution_client.get(f"{WORKSHOPS}/runs")
    assert resp.status_code == 403
