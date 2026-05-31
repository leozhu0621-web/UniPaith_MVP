"""Spec 15 §6.5 / §8 / §14 — guardrails, intent capture, offer response."""

from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import OfferLetter
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentProfile
from unipaith.models.user import User


async def _setup(
    db: AsyncSession, student_user: User, inst_user: User
) -> tuple[StudentProfile, Program]:
    db.add(student_user)
    db.add(inst_user)
    await db.flush()
    profile = StudentProfile(user_id=student_user.id)
    db.add(profile)
    inst = Institution(admin_user_id=inst_user.id, name="Test U", type="university", country="US")
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


async def _create_app(client: AsyncClient, program_id) -> str:
    resp = await client.post("/api/v1/applications", json={"program_id": str(program_id)})
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_guardrail_scan_low_fit_band(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, prog = await _setup(db_session, mock_student_user, mock_institution_user)
    app_id = await _create_app(student_client, prog.id)

    # Low fitness (15%) → low band + blocker (spec 15 §6.5, fitness ≤ 30).
    db_session.add(
        MatchResult(
            student_id=profile.id,
            program_id=prog.id,
            fitness_score=Decimal("0.15"),
            confidence_score=Decimal("0.80"),
        )
    )
    await db_session.commit()

    resp = await student_client.post(f"/api/v1/applications/me/{app_id}/guardrail-scan")
    assert resp.status_code == 200
    body = resp.json()
    assert body["fit_band"] == "low"
    assert body["recommended_action"] == "reconsider"
    assert body["fitness_score"] == 15.0
    assert any("low" in b.lower() for b in body["blockers"])
    assert body["is_rule_based"] is True

    # Persisted onto the application.
    detail = (await student_client.get(f"/api/v1/applications/me/{app_id}")).json()
    assert detail["fit_band"] == "low"
    assert detail["guardrail_blockers"]


@pytest.mark.asyncio
async def test_guardrail_scan_medium_when_unscored(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, prog = await _setup(db_session, mock_student_user, mock_institution_user)
    app_id = await _create_app(student_client, prog.id)
    resp = await student_client.post(f"/api/v1/applications/me/{app_id}/guardrail-scan")
    assert resp.status_code == 200
    assert resp.json()["fit_band"] == "medium"


@pytest.mark.asyncio
async def test_intent_back_up_requires_rationale(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, prog = await _setup(db_session, mock_student_user, mock_institution_user)
    app_id = await _create_app(student_client, prog.id)

    # back_up without a rationale → rejected (spec 15 §6.5, ≥ 80 chars).
    resp = await student_client.patch(
        f"/api/v1/applications/me/{app_id}", json={"intent_picker": "back_up"}
    )
    assert resp.status_code == 400

    # Too-short rationale → still rejected.
    resp = await student_client.patch(
        f"/api/v1/applications/me/{app_id}",
        json={"intent_picker": "back_up", "intent_rationale": "too short"},
    )
    assert resp.status_code == 400

    # ≥ 80 chars → accepted and persisted.
    long_rationale = (
        "This is my backup school because it has a strong program and I want options "
        "if my reach schools do not work out for me this cycle."
    )
    assert len(long_rationale) >= 80
    resp = await student_client.patch(
        f"/api/v1/applications/me/{app_id}",
        json={"intent_picker": "back_up", "intent_rationale": long_rationale},
    )
    assert resp.status_code == 200
    assert resp.json()["intent_picker"] == "back_up"
    assert resp.json()["intent_rationale"] == long_rationale


@pytest.mark.asyncio
async def test_intent_dream_needs_no_rationale(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, prog = await _setup(db_session, mock_student_user, mock_institution_user)
    app_id = await _create_app(student_client, prog.id)
    resp = await student_client.patch(
        f"/api/v1/applications/me/{app_id}", json={"intent_picker": "dream"}
    )
    assert resp.status_code == 200
    assert resp.json()["intent_picker"] == "dream"


@pytest.mark.asyncio
async def test_invalid_intent_rejected(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, prog = await _setup(db_session, mock_student_user, mock_institution_user)
    app_id = await _create_app(student_client, prog.id)
    resp = await student_client.patch(
        f"/api/v1/applications/me/{app_id}", json={"intent_picker": "totally_made_up"}
    )
    # Pydantic Literal validation rejects with 422.
    assert resp.status_code in (400, 422)


@pytest.mark.asyncio
async def test_offer_accept_updates_state(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, prog = await _setup(db_session, mock_student_user, mock_institution_user)
    app_id = await _create_app(student_client, prog.id)

    db_session.add(
        OfferLetter(
            application_id=app_id,
            offer_type="full_admission",
            scholarship_amount=10000,
            status="sent",
        )
    )
    await db_session.commit()

    resp = await student_client.post(
        f"/api/v1/applications/me/{app_id}/offer/respond", json={"response": "accepted"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"
    assert resp.json()["student_response"] == "accepted"

    # The brief is surfaced on the embedded offer (spec 15 §6.6).
    detail = (await student_client.get(f"/api/v1/applications/me/{app_id}")).json()
    assert detail["offer"] is not None
    assert detail["offer"]["brief"]
