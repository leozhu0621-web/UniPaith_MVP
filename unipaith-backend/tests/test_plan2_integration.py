"""Plan 2 integration — flag on/off paths through Plan 1's surface.

These tests verify the wiring, not the LLM quality. We monkeypatch the
agent objects so we don't need real API keys; the point is:

  - Default (flag OFF) → existing rule-based stub path runs (is_stub=True)
  - Flag ON + agent succeeds → LLM path returns is_stub=False with the
    canonical four output fields populated
  - Flag ON + agent fails → graceful fallback to stub (is_stub=True)
    so the caller never sees a 500
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole

WORKSHOPS = "/api/v1/students/me/workshops"
MATCHES = "/api/v1/students/me/matches"


async def _ensure_profile(db: AsyncSession, user: User) -> StudentProfile:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile


# ── Workshop essay coach — flag ON + success ─────────────────────────────


@dataclass
class _FakeFeedback:
    rubric_scores: dict = field(
        default_factory=lambda: {
            "specificity": 5,
            "voice": 4,
            "structure": 5,
            "prompt_alignment": 4,
            "evidence": 5,
        }
    )
    structural_issues: list = field(
        default_factory=lambda: [
            {"issue": "Intro buries the lede.", "severity": "moderate", "location_ref": "para 1"}
        ]
    )
    missing_elements: list = field(default_factory=lambda: ["A reflection moment."])
    questions_for_student: list = field(
        default_factory=lambda: ["What's the moment that made you choose this path?"]
    )
    prompt_alignment_notes: str = "Tracks the prompt's themes well."
    schema_version: int = 1
    cost_usd: float = 0.0
    latency_ms: int = 0
    raw: dict | None = None

    def is_well_formed(self) -> bool:
        return True


@dataclass
class _FakeVerdict:
    score: int = 0
    passed: bool = True
    evidence: str = ""
    category: str | None = None


@dataclass
class _FakeResult:
    feedback: _FakeFeedback
    verdict: _FakeVerdict

    @property
    def passed(self) -> bool:
        return self.feedback.is_well_formed() and self.verdict.passed


class _FakeCoach:
    """Stand-in for WorkshopCoach. Configured with a return value or to
    raise — covers the flag-ON success and flag-ON failure paths."""

    def __init__(self, *, raise_with: Exception | None = None, passed: bool = True):
        self._raise = raise_with
        self._passed = passed

    async def coach_essay(
        self, *, draft: Any, student_id: Any = None, db: Any = None
    ) -> _FakeResult:
        if self._raise:
            raise self._raise
        return _FakeResult(
            feedback=_FakeFeedback(),
            verdict=_FakeVerdict(passed=self._passed),
        )


@pytest.mark.asyncio
async def test_essay_v2_flag_off_returns_stub(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """Default config: stub path. Belt-and-suspenders against accidentally
    flipping the flag default."""
    assert settings.ai_workshops_v2_enabled is False
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        f"{WORKSHOPS}/essay/feedback",
        json={"essay_text": "I want to be a doctor. " * 5},
    )
    assert resp.status_code == 201
    assert resp.json()["is_stub"] is True


@pytest.mark.asyncio
async def test_essay_v2_flag_on_uses_coach(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    monkeypatch: pytest.MonkeyPatch,
):
    await _ensure_profile(db_session, mock_student_user)
    monkeypatch.setattr(settings, "ai_workshops_v2_enabled", True)
    monkeypatch.setattr(
        "unipaith.ai.coach.get_workshop_coach",
        lambda: _FakeCoach(passed=True),
    )

    resp = await student_client.post(
        f"{WORKSHOPS}/essay/feedback",
        json={"essay_text": "I learned that effort compounds. " * 10},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["is_stub"] is False
    assert data["domain"] == "essay"
    # Coach output flowed through into all four canonical fields.
    assert data["rubric_scores"]["specificity"] == 5.0
    assert any("Intro" in i["issue"] for i in data["structural_issues"])
    assert any("reflection" in m["element"].lower() for m in data["missing_elements"])
    assert len(data["suggested_questions"]) == 1


@pytest.mark.asyncio
async def test_essay_v2_flag_on_judge_fail_falls_back(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    monkeypatch: pytest.MonkeyPatch,
):
    """Guardrail trip → fall back to stub, not 500."""
    await _ensure_profile(db_session, mock_student_user)
    monkeypatch.setattr(settings, "ai_workshops_v2_enabled", True)
    monkeypatch.setattr(
        "unipaith.ai.coach.get_workshop_coach",
        lambda: _FakeCoach(passed=False),
    )
    resp = await student_client.post(
        f"{WORKSHOPS}/essay/feedback",
        json={"essay_text": "I want to be a doctor. " * 5},
    )
    assert resp.status_code == 201
    assert resp.json()["is_stub"] is True


@pytest.mark.asyncio
async def test_essay_v2_flag_on_coach_raises_falls_back(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    monkeypatch: pytest.MonkeyPatch,
):
    """API-level exception (timeout, parse error) → fall back to stub."""
    await _ensure_profile(db_session, mock_student_user)
    monkeypatch.setattr(settings, "ai_workshops_v2_enabled", True)
    monkeypatch.setattr(
        "unipaith.ai.coach.get_workshop_coach",
        lambda: _FakeCoach(raise_with=RuntimeError("LLM timeout")),
    )
    resp = await student_client.post(
        f"{WORKSHOPS}/essay/feedback",
        json={"essay_text": "I want to be a doctor. " * 5},
    )
    assert resp.status_code == 201
    assert resp.json()["is_stub"] is True


# ── Match rationale flag ─────────────────────────────────────────────────


async def _seed_match_with_program(
    db: AsyncSession, mock_student_user: User
) -> tuple[StudentProfile, Program]:
    profile = await _ensure_profile(db, mock_student_user)
    admin = User(
        id=uuid4(),
        email=f"inst-admin-{uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-sub-{uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(admin)
    await db.flush()
    inst = Institution(admin_user_id=admin.id, name="Test U", type="university", country="US")
    db.add(inst)
    await db.flush()
    program = Program(institution_id=inst.id, program_name="Test", degree_type="masters")
    db.add(program)
    await db.flush()
    match = MatchResult(
        student_id=profile.id,
        program_id=program.id,
        fitness_score=Decimal("0.8"),
        confidence_score=Decimal("0.6"),
        fitness_breakdown={"gpa": 0.9},
        confidence_breakdown={"reason": "test"},
    )
    db.add(match)
    await db.commit()
    await db.refresh(program)
    return profile, program


@pytest.mark.asyncio
async def test_explain_v2_flag_off_returns_stub(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    assert settings.ai_match_rationale_v2_enabled is False
    _, program = await _seed_match_with_program(db_session, mock_student_user)
    resp = await student_client.post(f"{MATCHES}/{program.id}/explain")
    assert resp.status_code == 200
    assert resp.json()["is_stub"] is True
    text = resp.json()["rationale_text"]
    assert text, "stub must still return a rationale string"
    # AI-Structure-3 §14: the stub rationale is qualitative — never a raw number.
    assert not any(ch.isdigit() for ch in text), f"stub leaked a number: {text!r}"


@pytest.mark.asyncio
async def test_explain_v2_flag_on_falls_back_when_no_feature_vector(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    monkeypatch: pytest.MonkeyPatch,
):
    """Flag on but the student has no feature vector yet (Discovery hasn't
    completed) → MatchService returns None → endpoint falls through to the
    stub. The caller still gets a 200 with a usable rationale."""
    monkeypatch.setattr(settings, "ai_match_rationale_v2_enabled", True)
    _, program = await _seed_match_with_program(db_session, mock_student_user)
    resp = await student_client.post(f"{MATCHES}/{program.id}/explain")
    assert resp.status_code == 200
    # Without a feature vector, MatchService returns None and we fall back.
    # The response is still well-formed and usable.
    assert resp.json()["rationale_text"]
