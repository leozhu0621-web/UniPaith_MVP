"""Tests for resume workshop — auto-generate, finalize, feedback."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

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


@pytest.mark.asyncio
async def test_auto_generate(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    resp = await student_client.post(
        "/api/v1/students/me/resume/generate",
        json={
            "format_type": "standard",
            "target_program_id": str(program.id),
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] is not None


@pytest.mark.asyncio
async def test_finalize_resume(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    create_resp = await student_client.post(
        "/api/v1/students/me/resume/generate",
        json={"format_type": "standard", "target_program_id": str(program.id)},
    )
    resume_id = create_resp.json()["id"]

    resp = await student_client.post(f"/api/v1/students/me/resume/{resume_id}/finalize")
    assert resp.status_code == 200
    assert resp.json()["status"] == "final"


@pytest.mark.asyncio
async def test_request_feedback(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """In AI_MOCK_MODE=true, feedback should return mock ai_suggestions."""
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    create_resp = await student_client.post(
        "/api/v1/students/me/resume/generate",
        json={"format_type": "standard", "target_program_id": str(program.id)},
    )
    resume_id = create_resp.json()["id"]

    resp = await student_client.post(
        f"/api/v1/students/me/resume/{resume_id}/feedback",
        json={"feedback_type": "full_review"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_suggestions"] is not None
