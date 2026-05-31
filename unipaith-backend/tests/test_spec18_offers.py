"""Spec 18 · Decisions & Offers — offer capture, decision states, comparison,
post-acceptance workflow, and the OutcomeBrief fallback invariant."""

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User
from unipaith.models.workflow import Notification


async def _setup(
    db: AsyncSession, student_user: User, inst_user: User, n_programs: int = 2
) -> tuple[StudentProfile, list[Program]]:
    db.add(student_user)
    db.add(inst_user)
    await db.flush()
    profile = StudentProfile(user_id=student_user.id)
    db.add(profile)
    inst = Institution(
        admin_user_id=inst_user.id,
        name="Foo U",
        type="university",
        country="US",
        city="Boston",
    )
    db.add(inst)
    await db.flush()
    specs = [("MS Computer Science", 48000), ("MS Data Science", 40000)]
    progs: list[Program] = []
    for name, tuition in specs[:n_programs]:
        p = Program(
            institution_id=inst.id,
            program_name=name,
            degree_type="masters",
            description_text="A program.",
            tuition=tuition,
            is_published=True,
        )
        db.add(p)
        progs.append(p)
    await db.commit()
    return profile, progs


async def _create_app(client: AsyncClient, program_id) -> str:
    r = await client.post("/api/v1/applications", json={"program_id": str(program_id)})
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _submit_external(client: AsyncClient, app_id: str) -> None:
    """Move an app out of `draft` so it counts as pending/withdrawable."""
    await client.patch(f"/api/v1/applications/me/{app_id}", json={"submission_mode": "external"})
    r = await client.post(f"/api/v1/applications/me/{app_id}/submit")
    assert r.status_code == 200, r.text


async def _record_offer(client: AsyncClient, app_id: str, **overrides) -> dict:
    body = {
        "offer_type": "full_admission",
        "scholarship_amount": 20000,
        "scholarship_currency": "USD",
        "tuition_estimate": 48000,
        "total_cost_estimate": 96000,
        "response_deadline": "2027-04-15",
        "start_term": {"season": "Fall", "year": 2027},
    }
    body.update(overrides)
    r = await client.post(f"/api/v1/applications/me/{app_id}/offers", json=body)
    assert r.status_code == 201, r.text
    return r.json()


@pytest.mark.asyncio
async def test_record_external_offer_flips_state_and_notifies(
    student_client, db_session, mock_student_user, mock_institution_user
):
    _, progs = await _setup(db_session, mock_student_user, mock_institution_user)
    app_id = await _create_app(student_client, progs[0].id)

    offer = await _record_offer(student_client, app_id)
    assert offer["received_externally"] is True
    assert offer["scholarship_amount"] == 20000
    assert offer["plain_language_brief"] is not None
    assert offer["plain_language_brief"]["summary"]
    # key_terms surface scholarship + start term (spec 18 §4)
    labels = {t["label"] for t in offer["plain_language_brief"]["key_terms"]}
    assert "Scholarship" in labels

    # the application now reads as a decision (offer received → accepted, §2)
    a = await student_client.get(f"/api/v1/applications/me/{app_id}")
    assert a.json()["decision_state"] == "accepted"

    # offer-received notification fired (§8)
    notifs = (
        (
            await db_session.execute(
                select(Notification).where(Notification.user_id == mock_student_user.id)
            )
        )
        .scalars()
        .all()
    )
    assert any(n.notification_type == "decision_made" for n in notifs)


@pytest.mark.asyncio
async def test_pending_state_without_offer(
    student_client, db_session, mock_student_user, mock_institution_user
):
    _, progs = await _setup(db_session, mock_student_user, mock_institution_user, n_programs=1)
    app_id = await _create_app(student_client, progs[0].id)
    a = await student_client.get(f"/api/v1/applications/me/{app_id}")
    assert a.json()["decision_state"] == "pending"


@pytest.mark.asyncio
async def test_accept_offer_sets_decision_and_returns_withdrawable(
    student_client, db_session, mock_student_user, mock_institution_user
):
    _, progs = await _setup(db_session, mock_student_user, mock_institution_user)
    app0 = await _create_app(student_client, progs[0].id)
    app1 = await _create_app(student_client, progs[1].id)
    await _submit_external(student_client, app1)  # app1 is now pending

    offer = await _record_offer(student_client, app0)
    r = await student_client.patch(
        f"/api/v1/applications/me/{app0}/offers/{offer['id']}",
        json={"response": "accepted"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["offer"]["status"] == "accepted"
    withdrawable_ids = {w["id"] for w in data["withdrawable_apps"]}
    assert app1 in withdrawable_ids

    a = await student_client.get(f"/api/v1/applications/me/{app0}")
    assert a.json()["decision_state"] == "accepted_by_student"
    assert a.json()["student_decision"] == "accepted_by_student"


@pytest.mark.asyncio
async def test_decline_offer(student_client, db_session, mock_student_user, mock_institution_user):
    _, progs = await _setup(db_session, mock_student_user, mock_institution_user, n_programs=1)
    app_id = await _create_app(student_client, progs[0].id)
    offer = await _record_offer(student_client, app_id)
    r = await student_client.patch(
        f"/api/v1/applications/me/{app_id}/offers/{offer['id']}",
        json={"response": "declined", "decline_reason": "Chose another school"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["offer"]["status"] == "declined"
    a = await student_client.get(f"/api/v1/applications/me/{app_id}")
    assert a.json()["decision_state"] == "declined_by_student"


@pytest.mark.asyncio
async def test_offers_comparison_renders_dimensions_and_indicators(
    student_client, db_session, mock_student_user, mock_institution_user
):
    _, progs = await _setup(db_session, mock_student_user, mock_institution_user)
    app0 = await _create_app(student_client, progs[0].id)
    app1 = await _create_app(student_client, progs[1].id)
    # app0 is cheaper net (96k − 20k = 76k) than app1 (80k − 0 = 80k)
    await _record_offer(student_client, app0, scholarship_amount=20000, total_cost_estimate=96000)
    await _record_offer(student_client, app1, scholarship_amount=0, total_cost_estimate=80000)

    r = await student_client.get("/api/v1/applications/me/offers/comparison")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["count"] == 2
    for item in data["offers"]:
        assert "cost" in item and "net_cost" in item["cost"]
        assert "fit" in item and "outcomes" in item
        assert item["location"] == "Boston, US"
    # most-affordable indicator points at the cheaper net cost (§5)
    assert data["indicators"]["most_affordable"] == app0
    # rule-based advisor copy when 2+ offers (§9)
    assert data.get("advisor_summary")
    assert "net cost" in data["advisor_summary"].lower() or "fit" in data["advisor_summary"].lower()


@pytest.mark.asyncio
async def test_withdraw_is_status_preserving(
    student_client, db_session, mock_student_user, mock_institution_user
):
    _, progs = await _setup(db_session, mock_student_user, mock_institution_user, n_programs=1)
    app_id = await _create_app(student_client, progs[0].id)
    await _submit_external(student_client, app_id)

    r = await student_client.post(f"/api/v1/applications/me/{app_id}/withdraw")
    assert r.status_code == 200, r.text
    assert r.json()["decision_state"] == "withdrawn"
    # row preserved (not hard-deleted) — still fetchable
    a = await student_client.get(f"/api/v1/applications/me/{app_id}")
    assert a.status_code == 200
    assert a.json()["student_decision"] == "withdrawn"


@pytest.mark.asyncio
async def test_bulk_withdraw(student_client, db_session, mock_student_user, mock_institution_user):
    _, progs = await _setup(db_session, mock_student_user, mock_institution_user)
    app0 = await _create_app(student_client, progs[0].id)
    app1 = await _create_app(student_client, progs[1].id)
    await _submit_external(student_client, app0)
    await _submit_external(student_client, app1)

    r = await student_client.post(
        "/api/v1/applications/me/withdraw-bulk",
        json={"application_ids": [app0, app1]},
    )
    assert r.status_code == 200, r.text
    assert r.json()["withdrawn_count"] == 2


@pytest.mark.asyncio
async def test_outcome_brief_agent_failure_falls_back_no_5xx(
    monkeypatch, student_client, db_session, mock_student_user, mock_institution_user
):
    """Plan 2 invariant — with the flag on, an agent that raises must still
    yield a 200 with the rule-based brief, never a 5xx."""
    from unipaith.config import settings

    monkeypatch.setattr(settings, "ai_outcome_brief_v2_enabled", True)
    import unipaith.ai.outcome_brief as ob

    class _Boom:
        async def generate(self, **_kw):
            raise RuntimeError("simulated agent failure")

    monkeypatch.setattr(ob, "get_outcome_brief_agent", lambda: _Boom())

    _, progs = await _setup(db_session, mock_student_user, mock_institution_user, n_programs=1)
    app_id = await _create_app(student_client, progs[0].id)
    offer = await _record_offer(student_client, app_id, scholarship_amount=5000)
    assert offer["plain_language_brief"]["source"] == "rule_based"


@pytest.mark.asyncio
async def test_institution_offer_created_as_sent(
    institution_client,
    db_session,
    mock_student_user,
    mock_institution_user,
):
    """Institution-created offers must land as ``sent`` with a brief (§3/§11)."""
    profile, progs = await _setup(
        db_session, mock_student_user, mock_institution_user, n_programs=1
    )
    from unipaith.models.application import Application

    app = Application(
        student_id=profile.id,
        program_id=progs[0].id,
        status="submitted",
        submission_mode="external",
        submitted_at=datetime.now(UTC),
    )
    db_session.add(app)
    await db_session.commit()
    await db_session.refresh(app)
    app_id = str(app.id)

    dec = await institution_client.post(
        f"/api/v1/applications/review/{app_id}/decision",
        json={"decision": "admitted"},
    )
    assert dec.status_code == 200, dec.text

    offer_r = await institution_client.post(
        f"/api/v1/applications/review/{app_id}/offer",
        json={
            "offer_type": "full_admission",
            "scholarship_amount": 5000,
            "response_deadline": "2027-04-15",
        },
    )
    assert offer_r.status_code == 201, offer_r.text
    offer_body = offer_r.json()
    assert offer_body["status"] == "sent"
    assert offer_body["plain_language_brief"] is not None
    assert offer_body["plain_language_brief"]["summary"]
