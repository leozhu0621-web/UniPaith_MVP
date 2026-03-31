"""Tests for event hooks — on_application_submitted, on_decision_made."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application
from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User
from unipaith.models.workflow import Notification, Touchpoint
from unipaith.services.event_hooks import on_application_submitted, on_decision_made


async def _seed_context(db: AsyncSession, student_user: User, institution_user: User):
    """Create all entities needed for hook tests, including an application."""
    db.add(student_user)
    db.add(institution_user)

    profile = StudentProfile(user_id=student_user.id, first_name="Test", last_name="Student")
    db.add(profile)

    institution = Institution(
        admin_user_id=institution_user.id,
        name="Test University",
        type="university",
        country="United States",
    )
    db.add(institution)
    await db.flush()

    program = Program(
        institution_id=institution.id,
        program_name="CS Masters",
        degree_type="masters",
        is_published=True,
        tuition=50000,
    )
    db.add(program)
    await db.flush()

    application = Application(
        student_id=profile.id,
        program_id=program.id,
        status="submitted",
    )
    db.add(application)
    await db.commit()
    return profile, institution, program, application


@pytest.mark.asyncio
async def test_on_application_submitted(
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution, program, application = await _seed_context(
        db_session, mock_student_user, mock_institution_user
    )

    await on_application_submitted(
        db=db_session,
        student_id=profile.id,
        student_user_id=mock_student_user.id,
        application_id=application.id,
        program_id=program.id,
        institution_id=institution.id,
        admin_user_id=mock_institution_user.id,
        confirmation_number="CONF-001",
    )
    await db_session.commit()

    # Verify notification was created for the institution admin
    result = await db_session.execute(
        select(Notification).where(
            Notification.user_id == mock_institution_user.id,
            Notification.notification_type == "application_submitted",
        )
    )
    notification = result.scalar_one_or_none()
    assert notification is not None
    assert "CONF-001" in notification.body

    # Verify touchpoint was created
    result = await db_session.execute(
        select(Touchpoint).where(
            Touchpoint.student_id == profile.id,
            Touchpoint.touchpoint_type == "application_submitted",
        )
    )
    touchpoint = result.scalar_one_or_none()
    assert touchpoint is not None
    assert touchpoint.institution_id == institution.id


@pytest.mark.asyncio
async def test_on_decision_made(
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution, program, application = await _seed_context(
        db_session, mock_student_user, mock_institution_user
    )

    await on_decision_made(
        db=db_session,
        student_user_id=mock_student_user.id,
        application_id=application.id,
        decision="accepted",
    )
    await db_session.commit()

    # Verify notification was created for the student
    result = await db_session.execute(
        select(Notification).where(
            Notification.user_id == mock_student_user.id,
            Notification.notification_type == "decision_made",
        )
    )
    notification = result.scalar_one_or_none()
    assert notification is not None
    assert "accepted" in notification.body.lower() or "Accepted" in notification.title


@pytest.mark.asyncio
async def test_on_decision_made_rejected(
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Verify that rejection notifications use appropriate messaging."""
    profile, institution, program, application = await _seed_context(
        db_session, mock_student_user, mock_institution_user
    )

    await on_decision_made(
        db=db_session,
        student_user_id=mock_student_user.id,
        application_id=application.id,
        decision="rejected",
    )
    await db_session.commit()

    result = await db_session.execute(
        select(Notification).where(
            Notification.user_id == mock_student_user.id,
            Notification.notification_type == "decision_made",
        )
    )
    notification = result.scalar_one_or_none()
    assert notification is not None
    assert notification.title == "Application Decision Update"
