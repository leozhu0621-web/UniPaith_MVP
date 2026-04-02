"""Tests for saved lists (save/unsave/list programs)."""

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
async def test_save_program(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    resp = await student_client.post(
        "/api/v1/students/me/saved",
        json={"program_id": str(program.id)},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["program_id"] == str(program.id)


@pytest.mark.asyncio
async def test_unsave_program(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    # Save first
    save_resp = await student_client.post(
        "/api/v1/students/me/saved",
        json={"program_id": str(program.id)},
    )
    assert save_resp.status_code == 201

    # Unsave
    resp = await student_client.delete(f"/api/v1/students/me/saved/{program.id}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_list_saved(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution, program1 = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )

    program2 = Program(
        institution_id=institution.id,
        program_name="Data Science PhD",
        degree_type="phd",
        is_published=True,
        tuition=60000,
    )
    db_session.add(program2)
    await db_session.commit()

    # Save both programs
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program1.id)})
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program2.id)})

    resp = await student_client.get("/api/v1/students/me/saved")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_save_duplicate(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    # Save once
    resp1 = await student_client.post(
        "/api/v1/students/me/saved", json={"program_id": str(program.id)}
    )
    assert resp1.status_code == 201

    # Save again — expect conflict
    resp2 = await student_client.post(
        "/api/v1/students/me/saved", json={"program_id": str(program.id)}
    )
    assert resp2.status_code == 409
