"""Activate built-but-orphaned primitives.

- Spec 70 §3: GET /me/scholarships/match surfaces scholarships to students from
  the seeded external catalog (ScholarshipService.matches_for_student).
- Spec 67 §2: the application submit path records a labeled confidence outcome
  (the learning loop's training data), consent-gated.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.scholarship import Scholarship
from unipaith.models.student import StudentDataConsent, StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.learning_loop import LearningLoopService


async def _profile(db: AsyncSession, user: User) -> StudentProfile:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile


async def _program(db: AsyncSession) -> Program:
    admin = User(
        id=uuid4(),
        email=f"a{uuid4().hex[:6]}@e.co",
        cognito_sub=f"s{uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(admin)
    await db.flush()
    inst = Institution(admin_user_id=admin.id, name="U", type="university", country="US")
    db.add(inst)
    await db.flush()
    program = Program(
        institution_id=inst.id, program_name="MS CS", degree_type="masters", is_published=True
    )
    db.add(program)
    await db.commit()
    await db.refresh(program)
    return program


# ── Spec 70 — scholarship match endpoint ───────────────────────────────────


@pytest.mark.asyncio
async def test_scholarship_match_endpoint_returns_eligible(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _profile(db_session, mock_student_user)
    # The endpoint now draws from the seeded external-scholarship catalog (the
    # structured `scholarships` reference table has no prod writer), so seed there.
    db_session.add(
        Scholarship(
            external_id=f"open-{uuid4().hex[:6]}",
            name="Open Award",
            organization="Open Fund",
            level_of_study="Graduate",
            award_type="external",
            award_amount="$3,000",  # verbatim text → parsed to a 3000 estimate
            source="careeronestop",
        )
    )
    await db_session.commit()

    resp = await student_client.get("/api/v1/students/me/scholarships/match")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert any(item["name"] == "Open Award" for item in data)
    assert data[0]["award_estimate"] == 3000


# ── Spec 67 — learning-loop outcome recording ──────────────────────────────


async def _seed_match_and_consent(
    db: AsyncSession, *, training: bool
) -> tuple[StudentProfile, Program]:
    user = User(
        id=uuid4(),
        email=f"st{uuid4().hex[:6]}@e.co",
        cognito_sub=f"ss{uuid4().hex[:8]}",
        role=UserRole.student,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    profile = StudentProfile(user_id=user.id)
    db.add(profile)
    await db.flush()
    program = await _program(db)
    db.add(
        MatchResult(
            student_id=profile.id,
            program_id=program.id,
            fitness_score=Decimal("0.7"),
            confidence_score=Decimal("0.6"),
        )
    )
    db.add(
        StudentDataConsent(
            student_id=profile.id,
            consent_matching=True,
            consent_outreach=False,
            consent_research=False,
            consent_training=training,
            consent_peer_connect=False,
        )
    )
    await db.commit()
    return profile, program


@pytest.mark.asyncio
async def test_learning_loop_records_with_training_consent(db_session: AsyncSession):
    profile, program = await _seed_match_and_consent(db_session, training=True)
    svc = LearningLoopService(db_session)
    pair = await svc.record_outcome_for(
        student_id=profile.id, program_id=program.id, outcome_kind="applied"
    )
    assert pair is not None
    assert pair.outcome == 1
    assert pair.outcome_kind == "applied"
    assert float(pair.predicted_confidence) == 0.6
    assert await svc.confidence_pair_count() == 1


@pytest.mark.asyncio
async def test_learning_loop_skips_without_training_consent(db_session: AsyncSession):
    profile, program = await _seed_match_and_consent(db_session, training=False)
    svc = LearningLoopService(db_session)
    pair = await svc.record_outcome_for(
        student_id=profile.id, program_id=program.id, outcome_kind="applied"
    )
    assert pair is None
    assert await svc.confidence_pair_count() == 0


@pytest.mark.asyncio
async def test_learning_loop_skips_without_prior_prediction(db_session: AsyncSession):
    """No MatchResult for the pair → nothing to label → no-op."""
    profile, program = await _seed_match_and_consent(db_session, training=True)
    other_program = await _program(db_session)
    svc = LearningLoopService(db_session)
    pair = await svc.record_outcome_for(
        student_id=profile.id, program_id=other_program.id, outcome_kind="applied"
    )
    assert pair is None
