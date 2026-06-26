"""Budget preference now reaches the matcher: _overlay_student_attrs populates
budget_max_usd_per_year (the affordability veto + graded fit) and needs_aid (so
the hard veto skips aid-seeking students, never wrongly excluding them)."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.student import StudentPreference, StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.match_service import MatchService


async def _student(db: AsyncSession, *, budget_max, funding_requirement) -> StudentProfile:
    user = User(
        id=uuid4(),
        email=f"s{uuid4().hex[:6]}@e.co",
        cognito_sub=f"x{uuid4().hex[:8]}",
        role=UserRole.student,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    profile = StudentProfile(user_id=user.id)
    db.add(profile)
    await db.flush()
    db.add(
        StudentPreference(
            student_id=profile.id,
            budget_max=budget_max,
            funding_requirement=funding_requirement,
        )
    )
    await db.flush()
    return profile


async def test_overlay_populates_budget_and_aid_seeking(db_session: AsyncSession):
    profile = await _student(db_session, budget_max=20_000, funding_requirement="full_scholarship")
    sparse: dict = {}
    await MatchService(db_session)._overlay_student_attrs(profile.id, sparse)
    assert sparse["budget_max_usd_per_year"] == 20_000
    # full_scholarship → aid-seeking → the budget veto SKIPS this student.
    assert sparse["needs_aid"] is True


async def test_overlay_self_funded_is_not_aid(db_session: AsyncSession):
    profile = await _student(db_session, budget_max=40_000, funding_requirement="self_funded")
    sparse: dict = {}
    await MatchService(db_session)._overlay_student_attrs(profile.id, sparse)
    assert sparse["budget_max_usd_per_year"] == 40_000
    assert sparse["needs_aid"] is False
