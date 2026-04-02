"""Tests for CRM service — touchpoint logging and timeline."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Institution
from unipaith.models.student import StudentProfile
from unipaith.models.user import User
from unipaith.services.crm_service import CRMService


async def _seed_student_and_institution(
    db: AsyncSession, student_user: User, institution_user: User
):
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
    await db.commit()
    return profile, institution


@pytest.mark.asyncio
async def test_log_touchpoint(
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution = await _seed_student_and_institution(
        db_session, mock_student_user, mock_institution_user
    )
    crm = CRMService(db_session)
    tp = await crm.log_touchpoint(
        student_id=profile.id,
        touchpoint_type="program_saved",
        institution_id=institution.id,
        description="Student saved CS Masters program",
    )
    await db_session.commit()

    assert tp.id is not None
    assert tp.touchpoint_type == "program_saved"
    assert tp.student_id == profile.id
    assert tp.institution_id == institution.id


@pytest.mark.asyncio
async def test_get_timeline(
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution = await _seed_student_and_institution(
        db_session, mock_student_user, mock_institution_user
    )
    crm = CRMService(db_session)

    # Log multiple touchpoints
    await crm.log_touchpoint(
        student_id=profile.id,
        touchpoint_type="program_saved",
        institution_id=institution.id,
        description="Saved program",
    )
    await crm.log_touchpoint(
        student_id=profile.id,
        touchpoint_type="application_started",
        institution_id=institution.id,
        description="Started application",
    )
    await crm.log_touchpoint(
        student_id=profile.id,
        touchpoint_type="message_sent",
        institution_id=institution.id,
        description="Sent a message",
    )
    await db_session.commit()

    timeline = await crm.get_student_timeline(student_id=profile.id, institution_id=institution.id)
    assert len(timeline) == 3
    # All three touchpoint types should be present
    types = {t.touchpoint_type for t in timeline}
    assert types == {"program_saved", "application_started", "message_sent"}
