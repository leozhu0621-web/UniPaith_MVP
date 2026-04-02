import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User


async def _setup_student_and_program(
    db: AsyncSession,
    student_user: User,
    inst_user: User,
) -> tuple[StudentProfile, Program]:
    db.add(student_user)
    db.add(inst_user)
    await db.flush()

    profile = StudentProfile(user_id=student_user.id)
    db.add(profile)

    inst = Institution(
        admin_user_id=inst_user.id,
        name="Test U",
        type="university",
        country="US",
    )
    db.add(inst)
    await db.flush()

    prog = Program(
        institution_id=inst.id,
        program_name="MS Test",
        degree_type="masters",
        description_text="A program.",
        tuition=30000,
        is_published=True,
    )
    db.add(prog)
    await db.commit()
    return profile, prog


@pytest.mark.asyncio
async def test_create_application(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, prog = await _setup_student_and_program(db_session, mock_student_user, mock_institution_user)
    resp = await student_client.post(
        "/api/v1/applications",
        json={
            "program_id": str(prog.id),
        },
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "draft"


@pytest.mark.asyncio
async def test_duplicate_application(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, prog = await _setup_student_and_program(db_session, mock_student_user, mock_institution_user)
    await student_client.post(
        "/api/v1/applications",
        json={
            "program_id": str(prog.id),
        },
    )
    resp = await student_client.post(
        "/api/v1/applications",
        json={
            "program_id": str(prog.id),
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_my_applications(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, prog = await _setup_student_and_program(db_session, mock_student_user, mock_institution_user)
    await student_client.post(
        "/api/v1/applications",
        json={
            "program_id": str(prog.id),
        },
    )
    resp = await student_client.get("/api/v1/applications/me")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_submit_application(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, prog = await _setup_student_and_program(db_session, mock_student_user, mock_institution_user)
    create_resp = await student_client.post(
        "/api/v1/applications",
        json={
            "program_id": str(prog.id),
        },
    )
    app_id = create_resp.json()["id"]
    resp = await student_client.post(f"/api/v1/applications/me/{app_id}/submit")
    assert resp.status_code == 200
    assert resp.json()["status"] == "submitted"
    assert resp.json()["submitted_at"] is not None


@pytest.mark.asyncio
async def test_withdraw_draft(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, prog = await _setup_student_and_program(db_session, mock_student_user, mock_institution_user)
    create_resp = await student_client.post(
        "/api/v1/applications",
        json={
            "program_id": str(prog.id),
        },
    )
    app_id = create_resp.json()["id"]
    resp = await student_client.delete(f"/api/v1/applications/me/{app_id}")
    assert resp.status_code == 204
