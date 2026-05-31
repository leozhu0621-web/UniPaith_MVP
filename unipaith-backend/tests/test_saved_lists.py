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


@pytest.mark.asyncio
async def test_compare_programs_returns_spec10_dimensions(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Spec 10 §8 — compare returns the fields backing the five dimensions."""
    _, institution, program1 = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    program2 = Program(
        institution_id=institution.id,
        program_name="Data Science PhD",
        degree_type="phd",
        is_published=True,
        tuition=60000,
        campus_setting="urban",
        delivery_format="on_campus",
        acceptance_rate=0.2,
        outcomes_data={"median_salary": 88000, "employment_rate": 0.9, "payback_months": 20},
    )
    db_session.add(program2)
    await db_session.commit()

    resp = await student_client.post(
        "/api/v1/students/me/saved/compare",
        json={"program_ids": [str(program1.id), str(program2.id)]},
    )
    assert resp.status_code == 200
    progs = resp.json()["programs"]
    assert len(progs) == 2
    keys = set(progs[0].keys())
    for k in (
        "campus_setting",
        "median_salary",
        "employment_rate",
        "payback_months",
        "fitness_score",
        "confidence_score",
        "tuition",
        "delivery_format",
        "acceptance_rate",
    ):
        assert k in keys, f"compare row missing {k}"

    ds = next(p for p in progs if p["program_name"] == "Data Science PhD")
    assert ds["median_salary"] == 88000
    assert ds["employment_rate"] == 0.9
    assert ds["campus_setting"] == "urban"


@pytest.mark.asyncio
async def test_patch_priority_persists(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})
    resp = await student_client.patch(
        f"/api/v1/students/me/saved/{program.id}",
        json={"priority": "planning_to_apply"},
    )
    assert resp.status_code == 200
    assert resp.json()["priority"] == "planning_to_apply"

    listed = await student_client.get("/api/v1/students/me/saved")
    assert listed.json()[0]["priority"] == "planning_to_apply"


@pytest.mark.asyncio
async def test_start_application_from_saved(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})
    resp = await student_client.post(
        f"/api/v1/students/me/saved/{program.id}/start-application",
    )
    assert resp.status_code == 201
    app_id = resp.json()["app_id"]

    listed = await student_client.get("/api/v1/students/me/saved")
    assert listed.json()[0]["status"] == "application_started"

    apps = await student_client.get("/api/v1/applications/me")
    assert any(a["id"] == app_id for a in apps.json())


@pytest.mark.asyncio
async def test_compare_rejects_more_than_four(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, institution, program1 = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    ids = [program1.id]
    for i in range(4):
        p = Program(
            institution_id=institution.id,
            program_name=f"Prog {i}",
            degree_type="masters",
            is_published=True,
        )
        db_session.add(p)
        ids.append(p.id)
    await db_session.commit()

    resp = await student_client.post(
        "/api/v1/students/me/saved/compare",
        json={"program_ids": [str(x) for x in ids[:5]]},
    )
    assert resp.status_code == 422
