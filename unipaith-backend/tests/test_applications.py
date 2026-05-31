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
async def test_create_application_populates_spec15_fields(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Spec 15 §14 — create from saved → expected fields populated."""
    _, prog = await _setup_student_and_program(db_session, mock_student_user, mock_institution_user)
    resp = await student_client.post("/api/v1/applications", json={"program_id": str(prog.id)})
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "draft"
    assert body["submission_mode"] == "internal"
    assert body["readiness_pct"] == 0
    assert body["intent_picker"] is None


@pytest.mark.asyncio
async def test_submit_blocked_when_not_ready(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Spec 15 §14 — internal submit blocked when readiness < 100%."""
    _, prog = await _setup_student_and_program(db_session, mock_student_user, mock_institution_user)
    create_resp = await student_client.post(
        "/api/v1/applications", json={"program_id": str(prog.id)}
    )
    app_id = create_resp.json()["id"]
    resp = await student_client.post(f"/api/v1/applications/me/{app_id}/submit")
    assert resp.status_code == 400
    assert "not ready" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_submit_external_marks_platform_side(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Spec 15 §7/§14 — external submission marks the platform side without
    invoking institution-receive (no submission package row)."""
    from sqlalchemy import func, select

    from unipaith.models.application import ApplicationSubmission

    _, prog = await _setup_student_and_program(db_session, mock_student_user, mock_institution_user)
    create_resp = await student_client.post(
        "/api/v1/applications", json={"program_id": str(prog.id)}
    )
    app_id = create_resp.json()["id"]

    patch_resp = await student_client.patch(
        f"/api/v1/applications/me/{app_id}", json={"submission_mode": "external"}
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["submission_mode"] == "external"

    resp = await student_client.post(f"/api/v1/applications/me/{app_id}/submit")
    assert resp.status_code == 200
    assert resp.json()["status"] == "submitted"
    assert resp.json()["submitted_at"] is not None

    # External must NOT create an institution-side submission package.
    count = await db_session.scalar(select(func.count()).select_from(ApplicationSubmission))
    assert count == 0


@pytest.mark.asyncio
async def test_submit_allowed_when_ready_internal(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Spec 15 §14 — internal submit allowed when all required items complete."""
    _, prog = await _setup_student_and_program(db_session, mock_student_user, mock_institution_user)
    create_resp = await student_client.post(
        "/api/v1/applications", json={"program_id": str(prog.id)}
    )
    app_id = create_resp.json()["id"]

    # Generate the checklist, then mark every required item complete (§7 manual).
    cl = (await student_client.get(f"/api/v1/students/me/applications/{app_id}/checklist")).json()
    for item in cl["items"]:
        if item.get("required"):
            r = await student_client.patch(
                f"/api/v1/applications/me/{app_id}/checklist",
                json={"item_key": item["key"], "completed": True},
            )
            assert r.status_code == 200
    ready = (await student_client.post(f"/api/v1/applications/me/{app_id}/check-readiness")).json()
    assert ready["is_ready"] is True
    assert ready["completion_percentage"] == 100

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
