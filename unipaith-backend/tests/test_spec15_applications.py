"""Spec 15 — applications guardrails and submit gate."""

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application, OfferLetter
from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User


async def _setup(db, student_user, inst_user):
    db.add(student_user)
    db.add(inst_user)
    await db.flush()
    profile = StudentProfile(
        user_id=student_user.id,
        first_name="Test",
        last_name="Student",
        nationality="US",
        country_of_residence="US",
    )
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
        description_text="x",
        tuition=1,
        is_published=True,
    )
    db.add(prog)
    await db.commit()
    return profile, prog


@pytest.mark.asyncio
async def test_submit_blocks_when_not_ready(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, prog = await _setup(db_session, mock_student_user, mock_institution_user)
    create = await student_client.post("/api/v1/applications", json={"program_id": str(prog.id)})
    app_id = create.json()["id"]
    resp = await student_client.post(f"/api/v1/applications/me/{app_id}/submit")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_guardrail_scan_low_fit(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, prog = await _setup(db_session, mock_student_user, mock_institution_user)
    create = await student_client.post("/api/v1/applications", json={"program_id": str(prog.id)})
    app_id = create.json()["id"]
    app = await db_session.get(Application, UUID(app_id))
    app.match_score = 0.15
    await db_session.commit()
    resp = await student_client.post(f"/api/v1/applications/me/{app_id}/guardrail-scan")
    assert resp.status_code == 200
    assert resp.json()["fit_band"] == "low"


@pytest.mark.asyncio
async def test_offer_accept(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, prog = await _setup(db_session, mock_student_user, mock_institution_user)
    app = Application(
        student_id=profile.id,
        program_id=prog.id,
        status="decision_made",
        decision="admitted",
    )
    db_session.add(app)
    await db_session.flush()
    db_session.add(OfferLetter(application_id=app.id, offer_type="full_admission", status="sent"))
    await db_session.commit()
    resp = await student_client.post(
        f"/api/v1/applications/me/{app.id}/offer/respond",
        json={"response": "accepted"},
    )
    assert resp.status_code == 200
    assert resp.json()["student_response"] == "accepted"
