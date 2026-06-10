"""Spec 20 §2 — Connect following model.

Covers: auto-follow on save (source=saved) and on start-application
(source=application); unfollow blocked while an application is active; mute;
the Manage-Following detail (can_unfollow).
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User
from unipaith.services.application_service import ApplicationService


async def _seed(db: AsyncSession, student_user: User, institution_user: User):
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
async def test_saving_program_auto_follows_institution(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, institution, program = await _seed(db_session, mock_student_user, mock_institution_user)

    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})

    resp = await student_client.get("/api/v1/connect/follows")
    assert resp.status_code == 200
    follows = resp.json()
    assert len(follows) == 1
    assert follows[0]["institution_id"] == str(institution.id)
    assert follows[0]["source"] == "saved"
    assert follows[0]["muted"] is False
    assert follows[0]["can_unfollow"] is True


@pytest.mark.asyncio
async def test_starting_application_auto_follows_and_allows_unfollow(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution, program = await _seed(
        db_session, mock_student_user, mock_institution_user
    )

    await ApplicationService(db_session).create_application(profile.id, program.id)
    await db_session.commit()

    resp = await student_client.get("/api/v1/connect/follows")
    follows = resp.json()
    assert len(follows) == 1
    assert follows[0]["source"] == "application"
    # Following is a user-controlled choice → always reversible (pin removed).
    assert follows[0]["can_unfollow"] is True

    # Unfollow succeeds even while the application is active — saving/following
    # must always be reversible (fixes "I can't unsave the school").
    ok = await student_client.delete(f"/api/v1/connect/follows/{institution.id}")
    assert ok.status_code == 204
    assert (await student_client.get("/api/v1/connect/follows")).json() == []


@pytest.mark.asyncio
async def test_mute_keeps_follow(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, institution, program = await _seed(db_session, mock_student_user, mock_institution_user)
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})

    muted = await student_client.patch(
        f"/api/v1/connect/follows/{institution.id}", json={"muted": True}
    )
    assert muted.status_code == 200
    assert muted.json()["muted"] is True

    follows = (await student_client.get("/api/v1/connect/follows")).json()
    assert len(follows) == 1  # still following
    assert follows[0]["muted"] is True


@pytest.mark.asyncio
async def test_explicit_follow_then_unfollow(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, institution, _ = await _seed(db_session, mock_student_user, mock_institution_user)

    f = await student_client.post(f"/api/v1/connect/follows/{institution.id}")
    assert f.status_code == 201
    follows = (await student_client.get("/api/v1/connect/follows")).json()
    assert len(follows) == 1
    assert follows[0]["source"] == "explicit"
    assert follows[0]["can_unfollow"] is True

    u = await student_client.delete(f"/api/v1/connect/follows/{institution.id}")
    assert u.status_code == 204


@pytest.mark.asyncio
async def test_auto_follow_disabled_on_save(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Spec 20 §2 — Settings toggle disables auto-follow on save."""
    _, institution, program = await _seed(db_session, mock_student_user, mock_institution_user)

    disabled = await student_client.put(
        "/api/v1/students/me/preferences", json={"auto_follow_on_save": False}
    )
    assert disabled.status_code == 200

    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})

    follows = (await student_client.get("/api/v1/connect/follows")).json()
    assert follows == []

    feed = (await student_client.get("/api/v1/connect/feed")).json()
    assert feed["followed_count"] == 0

    # Explicit follow still works when auto-follow is off.
    await student_client.post(f"/api/v1/connect/follows/{institution.id}")
    assert len((await student_client.get("/api/v1/connect/follows")).json()) == 1
