"""Tests for application checklist generation and readiness checks."""

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


async def _create_draft_application(db: AsyncSession, student_id, program_id) -> Application:
    app = Application(
        student_id=student_id,
        program_id=program_id,
        status="draft",
    )
    db.add(app)
    await db.commit()
    return app


@pytest.mark.asyncio
async def test_generate_checklist(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    app = await _create_draft_application(db_session, profile.id, program.id)

    resp = await student_client.post(f"/api/v1/students/me/applications/{app.id}/checklist")
    assert resp.status_code == 201
    data = resp.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_readiness_check(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    app = await _create_draft_application(db_session, profile.id, program.id)

    # Generate checklist first
    await student_client.post(f"/api/v1/students/me/applications/{app.id}/checklist")

    resp = await student_client.get(f"/api/v1/students/me/applications/{app.id}/readiness")
    assert resp.status_code == 200
    data = resp.json()
    # Profile is incomplete so readiness should be false
    assert data["is_ready"] is False
