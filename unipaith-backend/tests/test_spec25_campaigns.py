"""Spec 25 — Campaigns (institution outbound). Integration coverage for the
§13 test matrix: audience dedup, internal send per consent, external send
respecting opt-out / suppression, click→attribution, plus lifecycle + approval.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application
from unipaith.models.engagement import Conversation, Message
from unipaith.models.institution import (
    CampaignRecipient,
    Institution,
    Program,
)
from unipaith.models.student import StudentDataConsent, StudentProfile
from unipaith.models.user import User, UserRole

API = "/api/v1/institutions"


async def _mk_institution(
    db: AsyncSession, user: User, *, require_approval: bool = False
) -> Institution:
    inst = Institution(
        admin_user_id=user.id,
        name="Test University",
        type="university",
        country="United States",
        require_campaign_approval=require_approval,
    )
    db.add(inst)
    await db.commit()
    return inst


async def _mk_program(db: AsyncSession, inst_id) -> Program:
    prog = Program(institution_id=inst_id, program_name="CS MS", degree_type="masters")
    db.add(prog)
    await db.commit()
    return prog


async def _mk_applied_student(
    db: AsyncSession, program_id, *, first: str, consent_outreach: bool
) -> StudentProfile:
    user = User(
        id=uuid.uuid4(),
        email=f"{first.lower()}-{uuid.uuid4().hex[:6]}@students.edu",
        cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
        role=UserRole("student"),
        is_active=True,
    )
    db.add(user)
    await db.flush()
    profile = StudentProfile(user_id=user.id, first_name=first, last_name="Applicant")
    db.add(profile)
    await db.flush()
    db.add(Application(student_id=profile.id, program_id=program_id, status="submitted"))
    db.add(StudentDataConsent(student_id=profile.id, consent_outreach=consent_outreach))
    await db.commit()
    return profile


# ── empty state + objective validation ──────────────────────────────────────
@pytest.mark.asyncio
async def test_empty_state_and_validation(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    await _mk_institution(db_session, mock_institution_user)
    resp = await institution_client.get(f"{API}/me/campaigns")
    assert resp.status_code == 200
    assert resp.json() == []

    bad = await institution_client.post(
        f"{API}/me/campaigns", json={"name": "X", "objective": "not_a_real_objective"}
    )
    assert bad.status_code == 422


# ── external: dedupe + suppression + send + metrics ──────────────────────────
@pytest.mark.asyncio
async def test_external_dedupe_suppression_send_metrics(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    await _mk_institution(db_session, mock_institution_user)

    # Uploaded list with a duplicate (case-insensitive) and a to-be-suppressed email.
    list_resp = await institution_client.post(
        f"{API}/me/uploaded-lists",
        json={
            "name": "Prospects",
            "source": "csv_upload",
            "source_consent_confirmed": True,
            "contacts": [
                {"email": "ana@x.com", "first_name": "Ana"},
                {"email": "ANA@x.com", "first_name": "Ana Dup"},  # dup of ana@x.com
                {"email": "ben@x.com", "first_name": "Ben"},  # will be suppressed
                {"email": "cara@x.com", "first_name": "Cara"},
            ],
        },
    )
    assert list_resp.status_code == 201
    list_id = list_resp.json()["id"]
    assert list_resp.json()["contact_count"] == 3  # case-insensitive dedupe on import

    # Suppress ben@x.com institution-wide.
    sup = await institution_client.post(f"{API}/me/suppressions", json={"email": "ben@x.com"})
    assert sup.status_code == 201

    create = await institution_client.post(
        f"{API}/me/campaigns",
        json={
            "name": "Open House",
            "objective": "event_promotion",
            "cta_type": "rsvp_event",
            "channels": ["external_email"],
            "audience_uploaded_list_ids": [list_id],
            "subject": "Join us, {{first_name}}",
            "body": "RSVP now.",
        },
    )
    assert create.status_code == 201
    cid = create.json()["id"]
    assert create.json()["channels"] == ["external_email"]

    # Preview: ana (dedup of ANA) + cara = 2; ben suppressed.
    prev = await institution_client.post(f"{API}/me/campaigns/{cid}/preview-audience")
    assert prev.status_code == 200
    body = prev.json()
    assert body["deduped_count"] == 2, body
    assert body["suppressed_count"] == 1, body
    assert len(body["sample"]) == 2

    # Send.
    send = await institution_client.post(f"{API}/me/campaigns/{cid}/send")
    assert send.status_code == 200, send.text
    assert send.json()["status"] == "active"
    assert send.json()["sent_count"] == 2

    # Recipients: ben suppressed, ana + cara present.
    recips = (
        await db_session.execute(
            select(CampaignRecipient.email).where(CampaignRecipient.campaign_id == uuid.UUID(cid))
        )
    ).all()
    emails = {r[0].lower() for r in recips}
    assert emails == {"ana@x.com", "cara@x.com"}, emails
    assert "ben@x.com" not in emails

    # Metrics shape (Spec 25 §8).
    metrics = await institution_client.get(f"{API}/me/campaigns/{cid}/metrics")
    m = metrics.json()
    assert m["sent"] == 2 and m["delivered"] == 2
    assert "conversions" in m and "unsubscribes" in m and "bounces" in m

    # Cannot delete a sent campaign.
    dele = await institution_client.delete(f"{API}/me/campaigns/{cid}")
    assert dele.status_code == 400


# ── internal: drops into inbox per consent.outreach ──────────────────────────
@pytest.mark.asyncio
async def test_internal_send_respects_consent(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    inst = await _mk_institution(db_session, mock_institution_user)
    prog = await _mk_program(db_session, inst.id)
    yes = await _mk_applied_student(db_session, prog.id, first="Yes", consent_outreach=True)
    await _mk_applied_student(db_session, prog.id, first="No", consent_outreach=False)

    seg = await institution_client.post(
        f"{API}/me/segments",
        json={"segment_name": "Applicants", "criteria": {"statuses": ["submitted"]}},
    )
    assert seg.status_code == 201
    seg_id = seg.json()["id"]

    create = await institution_client.post(
        f"{API}/me/campaigns",
        json={
            "name": "Welcome",
            "objective": "nurture",
            "channels": ["internal_messaging"],
            "audience_segment_ids": [seg_id],
            "subject": "Welcome to CS MS",
            "body": "We saw your application.",
        },
    )
    cid = create.json()["id"]

    prev = (await institution_client.post(f"{API}/me/campaigns/{cid}/preview-audience")).json()
    assert prev["deduped_count"] == 1, prev  # only the consenting student
    assert prev["consent_excluded_count"] == 1, prev

    send = await institution_client.post(f"{API}/me/campaigns/{cid}/send")
    assert send.status_code == 200
    assert send.json()["sent_count"] == 1

    # The consenting student got a system inbox thread + message; the other did not.
    convos = (
        (
            await db_session.execute(
                select(Conversation).where(
                    Conversation.student_id == yes.id, Conversation.thread_type == "system"
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(convos) == 1
    msgs = (
        (await db_session.execute(select(Message).where(Message.conversation_id == convos[0].id)))
        .scalars()
        .all()
    )
    assert len(msgs) == 1 and "application" in msgs[0].message_body

    recips = (
        (
            await db_session.execute(
                select(CampaignRecipient).where(CampaignRecipient.campaign_id == uuid.UUID(cid))
            )
        )
        .scalars()
        .all()
    )
    assert len(recips) == 1 and recips[0].student_id == yes.id


# ── lifecycle transitions ────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_lifecycle_transitions(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    await _mk_institution(db_session, mock_institution_user)
    list_resp = await institution_client.post(
        f"{API}/me/uploaded-lists",
        json={"name": "L", "contacts": [{"email": "d@x.com"}]},
    )
    lid = list_resp.json()["id"]
    cid = (
        await institution_client.post(
            f"{API}/me/campaigns",
            json={
                "name": "Drip",
                "channels": ["external_email"],
                "audience_uploaded_list_ids": [lid],
                "subject": "Hi",
                "body": "Body",
            },
        )
    ).json()["id"]

    assert (await institution_client.post(f"{API}/me/campaigns/{cid}/send")).json()[
        "status"
    ] == "active"
    assert (await institution_client.post(f"{API}/me/campaigns/{cid}/pause")).json()[
        "status"
    ] == "paused"
    assert (await institution_client.post(f"{API}/me/campaigns/{cid}/resume")).json()[
        "status"
    ] == "active"
    assert (await institution_client.post(f"{API}/me/campaigns/{cid}/complete")).json()[
        "status"
    ] == "completed"
    # Re-sending a completed campaign is rejected.
    assert (await institution_client.post(f"{API}/me/campaigns/{cid}/send")).status_code == 400


# ── approval workflow (Spec 25 §7) ───────────────────────────────────────────
@pytest.mark.asyncio
async def test_approval_workflow(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    await _mk_institution(db_session, mock_institution_user, require_approval=True)
    list_resp = await institution_client.post(
        f"{API}/me/uploaded-lists", json={"name": "L", "contacts": [{"email": "e@x.com"}]}
    )
    lid = list_resp.json()["id"]
    cid = (
        await institution_client.post(
            f"{API}/me/campaigns",
            json={
                "name": "Needs sign-off",
                "channels": ["external_email"],
                "audience_uploaded_list_ids": [lid],
                "subject": "Hi",
                "body": "Body",
            },
        )
    ).json()["id"]

    # Cannot send a draft while approval is required.
    assert (await institution_client.post(f"{API}/me/campaigns/{cid}/send")).status_code == 400

    submit = await institution_client.post(f"{API}/me/campaigns/{cid}/submit-approval")
    assert submit.json()["status"] == "pending_approval"

    # Reject → back to draft with comment.
    rej = await institution_client.post(
        f"{API}/me/campaigns/{cid}/reject", json={"comment": "Tighten the subject line"}
    )
    assert rej.json()["status"] == "draft"
    assert rej.json()["rejection_comment"] == "Tighten the subject line"

    # Resubmit + approve → then sendable.
    await institution_client.post(f"{API}/me/campaigns/{cid}/submit-approval")
    appr = await institution_client.post(f"{API}/me/campaigns/{cid}/approve")
    assert appr.json()["approved_at"] is not None
    sent = await institution_client.post(f"{API}/me/campaigns/{cid}/send")
    assert sent.status_code == 200 and sent.json()["status"] == "active"


# ── click → attribution → conversion in metrics ──────────────────────────────
@pytest.mark.asyncio
async def test_click_attribution_conversion(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    inst = await _mk_institution(db_session, mock_institution_user)
    prog = await _mk_program(db_session, inst.id)
    student = await _mk_applied_student(db_session, prog.id, first="Click", consent_outreach=True)
    seg = await institution_client.post(
        f"{API}/me/segments",
        json={"segment_name": "All", "criteria": {"statuses": ["submitted"]}},
    )
    seg_id = seg.json()["id"]
    cid = (
        await institution_client.post(
            f"{API}/me/campaigns",
            json={
                "name": "Track me",
                "channels": ["internal_messaging"],
                "audience_segment_ids": [seg_id],
                "subject": "S",
                "body": "B",
            },
        )
    ).json()["id"]
    await institution_client.post(f"{API}/me/campaigns/{cid}/send")

    # Record a downstream apply_started action via the service (student-facing path).
    from unipaith.services.institution_service import InstitutionService

    await InstitutionService(db_session).record_campaign_action(
        uuid.UUID(cid), student.id, "apply_started"
    )
    await db_session.commit()

    metrics = (await institution_client.get(f"{API}/me/campaigns/{cid}/metrics")).json()
    assert metrics["conversions"]["apply_started"] == 1, metrics


# ── "Draft with AI" — fallback path (AI_MOCK_MODE → template stub) ────────────
@pytest.mark.asyncio
async def test_draft_with_ai_fallback(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    await _mk_institution(db_session, mock_institution_user)
    resp = await institution_client.post(
        f"{API}/me/campaigns/draft-copy",
        json={"objective": "event_promotion", "cta_type": "rsvp_event"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    # In tests (mock mode / flag off) the deterministic template stub serves.
    assert data["source"] == "fallback"
    assert data["subject"] and data["body"]
    # Personalization tokens must survive verbatim (double-brace).
    assert "{{first_name}}" in data["body"]
    assert "{{event_link}}" in data["body"]
