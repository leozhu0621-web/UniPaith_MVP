"""Demo mode — reset_student_demo_data wipes generated memory, keeps the account."""

import uuid

from sqlalchemy import select

from unipaith.models.goals import StudentGoal
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.demo_service import reset_student_demo_data


async def test_reset_wipes_memory_keeps_account(db_session):
    user = User(
        id=uuid.uuid4(),
        email=f"demo-{uuid.uuid4().hex[:6]}@example.com",
        cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
        role=UserRole.student,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    profile = StudentProfile(user_id=user.id, discovery_completion={"profile": "done"})
    db_session.add(profile)
    await db_session.flush()
    db_session.add(
        StudentGoal(student_id=profile.id, category="academic", specific="Top CS program")
    )
    await db_session.flush()

    await reset_student_demo_data(db_session, user.id)

    # Student-generated memory is gone.
    remaining = (
        (
            await db_session.execute(
                select(StudentGoal.id).where(StudentGoal.student_id == profile.id)
            )
        )
        .scalars()
        .all()
    )
    assert remaining == []

    # Account + profile survive; journey fields reset in place.
    assert (
        await db_session.execute(select(User.id).where(User.id == user.id))
    ).scalar_one_or_none() is not None
    completion = (
        await db_session.execute(
            select(StudentProfile.discovery_completion).where(StudentProfile.id == profile.id)
        )
    ).scalar_one_or_none()
    assert completion == {}


async def test_reset_without_profile_is_noop(db_session):
    # A user_id with no profile must not raise.
    await reset_student_demo_data(db_session, uuid.uuid4())
