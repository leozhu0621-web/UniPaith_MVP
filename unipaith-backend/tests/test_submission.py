"""Tests for application submission flow."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application
from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User


async def _seed_student_and_program(db: AsyncSession, student_user: User, institution_user: User):
    """Create a student profile, institution, and published program."""
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
    await db.commit()
    return profile, institution, program


async def _create_application_with_checklist(
    client: AsyncClient,
    db: AsyncSession,
    profile_id,
    program_id,
) -> Application:
    """Create a draft application and generate its checklist."""
    app = Application(
        student_id=profile_id,
        program_id=program_id,
        status="draft",
    )
    db.add(app)
    await db.commit()

    # Generate checklist via API
    await client.post(f"/api/v1/students/me/applications/{app.id}/checklist")
    return app


@pytest.mark.asyncio
async def test_submit_application(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    app = await _create_application_with_checklist(
        student_client, db_session, profile.id, program.id
    )

    # Submit the application: POST /api/v1/applications/me/{application_id}/submit
    resp = await student_client.post(
        f"/api/v1/applications/me/{app.id}/submit"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "submitted"


@pytest.mark.asyncio
async def test_submit_blocks_incomplete(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Submitting without required items or a non-existent application should fail."""
    profile, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    # Create application without checklist — no documents prepared
    app = Application(
        student_id=profile.id,
        program_id=program.id,
        status="draft",
    )
    db_session.add(app)
    await db_session.commit()

    resp = await student_client.post(
        f"/api/v1/applications/me/{app.id}/submit"
    )
    # Should fail — either 400 (validation) or 422 (business rule)
    assert resp.status_code in (400, 422)
