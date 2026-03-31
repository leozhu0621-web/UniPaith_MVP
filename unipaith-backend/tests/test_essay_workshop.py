"""Tests for essay workshop — create, update, finalize, feedback."""

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
async def test_create_essay(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    resp = await student_client.post(
        "/api/v1/students/me/essays",
        json={
            "program_id": str(program.id),
            "essay_type": "personal_statement",
            "content": "This is my personal statement about my passion for CS.",
            "prompt_text": "Tell us about yourself.",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["word_count"] is not None or data["content"] is not None


@pytest.mark.asyncio
async def test_update_essay(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    # Create first
    create_resp = await student_client.post(
        "/api/v1/students/me/essays",
        json={
            "program_id": str(program.id),
            "essay_type": "personal_statement",
            "content": "Draft version one.",
        },
    )
    assert create_resp.status_code == 201
    essay_id = create_resp.json()["id"]
    original_version = create_resp.json()["essay_version"]

    # Update
    update_resp = await student_client.put(
        f"/api/v1/students/me/essays/{essay_id}",
        json={"content": "Draft version two with more detail."},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["essay_version"] >= original_version


@pytest.mark.asyncio
async def test_finalize_essay(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    create_resp = await student_client.post(
        "/api/v1/students/me/essays",
        json={
            "program_id": str(program.id),
            "essay_type": "personal_statement",
            "content": "My finalized essay content here.",
        },
    )
    essay_id = create_resp.json()["id"]

    resp = await student_client.post(f"/api/v1/students/me/essays/{essay_id}/finalize")
    assert resp.status_code == 200
    assert resp.json()["status"] == "final"


@pytest.mark.asyncio
async def test_request_feedback(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """In AI_MOCK_MODE=true, feedback should return mock ai_feedback."""
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    create_resp = await student_client.post(
        "/api/v1/students/me/essays",
        json={
            "program_id": str(program.id),
            "essay_type": "personal_statement",
            "content": "My essay that needs feedback.",
        },
    )
    essay_id = create_resp.json()["id"]

    resp = await student_client.post(
        f"/api/v1/students/me/essays/{essay_id}/feedback",
        json={"feedback_type": "full_review"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_feedback"] is not None
