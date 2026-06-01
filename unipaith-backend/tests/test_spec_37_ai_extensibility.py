"""Spec 37 — AI Extensibility contract tests.

Covers the four §8 requirements plus the net-new pieces:
- §3 human<->AI edit-diff captured + audit-logged (ai_generated / human_edit /
  decision_action) for the institution surfaces.
- §1.3 AI failure → rule-based fallback, never a 5xx (verified under AI_MOCK_MODE,
  where every agent deterministically falls back to its rule-based path).
- §5 per-surface on/off toggles + confidence thresholds + no-training tier.
- §4 assistant chat is grounded (citations) and never invents.
- §7 G-AI4 authenticity scan auto-triggers on submit + respects the toggle.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application, IntegritySignal, Rubric
from unipaith.models.engagement import StudentEssay
from unipaith.models.institution import Institution, Program, Reviewer
from unipaith.models.student import StudentProfile
from unipaith.models.user import User

API = "/api/v1"

# Essay engineered to trip the conservative rule-based authenticity heuristic:
# a generic AI opener + 3 cliché tells + 6 em-dashes → 3 signals → band=medium.
FLAGGING_ESSAY = (
    "In today's world, my journey is a rich tapestry of multifaceted experiences "
    "that delve into who I am — a learner — a builder — a dreamer — "
    "a leader — and a friend — woven together over many years of growth."
)


async def _seed(
    db: AsyncSession, student_user: User, institution_user: User, *, essay: bool = False
):
    db.add(student_user)
    db.add(institution_user)
    profile = StudentProfile(user_id=student_user.id, first_name="Ada", last_name="Lovelace")
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
    await db.flush()
    application = Application(student_id=profile.id, program_id=program.id, status="submitted")
    db.add(application)
    db.add(Reviewer(institution_id=institution.id, user_id=institution_user.id, name="Dr. Rev"))
    if essay:
        db.add(StudentEssay(student_id=profile.id, program_id=program.id, content=FLAGGING_ESSAY))
    await db.commit()
    return profile, institution, program, application


async def _make_rubric(db: AsyncSession, institution_id) -> Rubric:
    rubric = Rubric(
        institution_id=institution_id,
        rubric_name="Holistic",
        criteria=[
            {"name": "Academic", "weight": 0.5, "max_score": 5},
            {"name": "Fit", "weight": 0.5, "max_score": 5},
        ],
        is_active=True,
    )
    db.add(rubric)
    await db.commit()
    return rubric


# ── §5 configuration ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ai_config_defaults_and_update(
    institution_client: AsyncClient, db_session, mock_student_user, mock_institution_user
):
    await _seed(db_session, mock_student_user, mock_institution_user)

    r = await institution_client.get(f"{API}/institutions/settings")
    assert r.status_code == 200
    cfg = r.json()["ai_config"]
    assert cfg["no_training"] is False
    # All 8 surfaces present; rubric_prefill ships with the spec's 70 floor.
    assert "packet_summary" in cfg["surfaces"]
    assert cfg["surfaces"]["rubric_prefill"]["min_confidence"] == 70
    assert cfg["surfaces"]["packet_summary"]["enabled"] is True

    r = await institution_client.patch(
        f"{API}/institutions/settings",
        json={
            "ai_config": {
                "surfaces": {
                    "packet_summary": {"enabled": False},
                    "rubric_prefill": {"min_confidence": 150},  # clamped to 100
                },
                "no_training": True,
            }
        },
    )
    assert r.status_code == 200
    cfg = r.json()["ai_config"]
    assert cfg["surfaces"]["packet_summary"]["enabled"] is False
    assert cfg["surfaces"]["rubric_prefill"]["min_confidence"] == 100
    assert cfg["no_training"] is True


# ── §3 capture + §5 toggle: packet summary ──────────────────────────────────


@pytest.mark.asyncio
async def test_packet_summary_capture_and_toggle(
    institution_client: AsyncClient, db_session, mock_student_user, mock_institution_user
):
    _, _, _, app = await _seed(db_session, mock_student_user, mock_institution_user)

    r = await institution_client.post(f"{API}/reviews/applications/{app.id}/ai-packet/regenerate")
    assert r.status_code == 200
    assert "draft_token" in r.json()

    ev = await institution_client.get(
        f"{API}/institutions/me/ai-surface/events", params={"surface": "packet_summary"}
    )
    assert ev.status_code == 200
    actions = [e["action"] for e in ev.json()]
    assert "ai_generated:packet_summary" in actions

    # Toggle off → endpoint returns disabled, no agent call.
    await institution_client.patch(
        f"{API}/institutions/settings",
        json={"ai_config": {"surfaces": {"packet_summary": {"enabled": False}}}},
    )
    r = await institution_client.post(f"{API}/reviews/applications/{app.id}/ai-packet/regenerate")
    assert r.status_code == 200
    assert r.json().get("disabled") is True


# ── §3 full triplet + §5 threshold: rubric prefill → score ──────────────────


@pytest.mark.asyncio
async def test_rubric_prefill_threshold_and_triplet(
    institution_client: AsyncClient, db_session, mock_student_user, mock_institution_user
):
    _, institution, _, app = await _seed(db_session, mock_student_user, mock_institution_user)
    rubric = await _make_rubric(db_session, institution.id)

    # Default floor is 70; a minimal profile yields a low-confidence packet, so
    # the pre-fill is withheld.
    r = await institution_client.post(
        f"{API}/reviews/applications/{app.id}/ai-prefill", params={"rubric_id": str(rubric.id)}
    )
    assert r.status_code == 200
    assert r.json()["withheld_low_confidence"] is True
    assert r.json()["prefill"] == {}

    # Drop the floor to 0 → pre-fill is shown + a draft token returned.
    await institution_client.patch(
        f"{API}/institutions/settings",
        json={"ai_config": {"surfaces": {"rubric_prefill": {"min_confidence": 0}}}},
    )
    r = await institution_client.post(
        f"{API}/reviews/applications/{app.id}/ai-prefill", params={"rubric_id": str(rubric.id)}
    )
    body = r.json()
    assert body["withheld_low_confidence"] is False
    assert body["prefill"]
    token = body["draft_token"]

    # Score (human edits the AI pre-fill) → human_edit + decision_action.
    r = await institution_client.post(
        f"{API}/reviews/applications/{app.id}/score",
        json={
            "rubric_id": str(rubric.id),
            "criterion_scores": {"Academic": 4, "Fit": 3},
            "reviewer_notes": "Edited by a human reviewer.",
            "ai_draft_token": token,
        },
    )
    assert r.status_code == 200

    ev = await institution_client.get(
        f"{API}/institutions/me/ai-surface/events", params={"surface": "rubric_prefill"}
    )
    actions = [e["action"] for e in ev.json()]
    assert "ai_generated:rubric_prefill" in actions
    assert "human_edit:rubric_prefill" in actions
    assert "decision_action:rubric_prefill" in actions


# ── §4 assistant chat: grounded + toggle ────────────────────────────────────


@pytest.mark.asyncio
async def test_assistant_chat_grounded_and_toggle(
    institution_client: AsyncClient, db_session, mock_student_user, mock_institution_user
):
    _, _, _, app = await _seed(db_session, mock_student_user, mock_institution_user)

    r = await institution_client.post(
        f"{API}/reviews/applications/{app.id}/assistant-chat",
        json={"question": "What is their strongest signal?"},
    )
    assert r.status_code == 200
    body = r.json()
    # Grounded answer carries citations and never invents (rule-based fallback
    # cites the packet fields it used).
    assert "citations" in body
    assert body.get("grounded") is True

    ev = await institution_client.get(
        f"{API}/institutions/me/ai-surface/events", params={"surface": "assistant_chat"}
    )
    assert "ai_generated:assistant_chat" in [e["action"] for e in ev.json()]

    await institution_client.patch(
        f"{API}/institutions/settings",
        json={"ai_config": {"surfaces": {"assistant_chat": {"enabled": False}}}},
    )
    r = await institution_client.post(
        f"{API}/reviews/applications/{app.id}/assistant-chat",
        json={"question": "Anything?"},
    )
    assert r.status_code == 200
    assert r.json().get("disabled") is True


# ── §3 capture + §1.3 graceful + §5 toggle: message draft ───────────────────


@pytest.mark.asyncio
async def test_message_draft_graceful_commit_and_toggle(
    institution_client: AsyncClient, db_session, mock_student_user, mock_institution_user
):
    _, _, _, app = await _seed(db_session, mock_student_user, mock_institution_user)

    r = await institution_client.post(
        f"{API}/institutions/me/templates/ai-draft",
        params={"application_id": str(app.id), "message_type": "missing_items"},
    )
    assert r.status_code == 200
    body = r.json()
    # Mock mode → AI drafter unavailable → graceful rule-based draft (never 5xx).
    assert body["source"] == "rule_based"
    assert body["subject"] and body["body"]
    token = body["draft_token"]

    # Human edits + sends → commit records the diff.
    r = await institution_client.post(
        f"{API}/institutions/me/ai-surface/commit",
        json={
            "surface": "message_draft",
            "draft_token": token,
            "final_content": {"subject": body["subject"], "body": body["body"] + " Edited."},
            "action": "message_sent",
        },
    )
    assert r.status_code == 200
    assert r.json()["was_edited"] is True

    ev = await institution_client.get(
        f"{API}/institutions/me/ai-surface/events", params={"surface": "message_draft"}
    )
    actions = [e["action"] for e in ev.json()]
    assert "ai_generated:message_draft" in actions
    assert "human_edit:message_draft" in actions
    assert "decision_action:message_draft" in actions

    # Toggle off → disabled.
    await institution_client.patch(
        f"{API}/institutions/settings",
        json={"ai_config": {"surfaces": {"message_draft": {"enabled": False}}}},
    )
    r = await institution_client.post(
        f"{API}/institutions/me/templates/ai-draft",
        params={"application_id": str(app.id), "message_type": "decision"},
    )
    assert r.status_code == 200
    assert r.json().get("disabled") is True


# ── §5 no-training tier flows into capture metadata ─────────────────────────


@pytest.mark.asyncio
async def test_no_training_tier_marks_events(
    institution_client: AsyncClient, db_session, mock_student_user, mock_institution_user
):
    _, _, _, app = await _seed(db_session, mock_student_user, mock_institution_user)
    await institution_client.patch(
        f"{API}/institutions/settings", json={"ai_config": {"no_training": True}}
    )
    await institution_client.post(
        f"{API}/institutions/me/templates/ai-draft",
        params={"application_id": str(app.id), "message_type": "clarification"},
    )
    ev = await institution_client.get(
        f"{API}/institutions/me/ai-surface/events", params={"surface": "message_draft"}
    )
    gen = [e for e in ev.json() if e["action"] == "ai_generated:message_draft"]
    assert gen and gen[0]["training_eligible"] is False


# ── §7 G-AI4 authenticity: toggle + auto-trigger on submit ──────────────────


@pytest.mark.asyncio
async def test_authenticity_toggle_respected(
    institution_client: AsyncClient, db_session, mock_student_user, mock_institution_user
):
    _, institution, _, app = await _seed(
        db_session, mock_student_user, mock_institution_user, essay=True
    )
    from unipaith.services.review_pipeline_service import ReviewPipelineService

    # Enabled (default) → the flagging essay produces an authenticity signal.
    await ReviewPipelineService(db_session).scan_integrity(institution.id, app.id)
    await db_session.commit()
    sigs = (
        (
            await db_session.execute(
                select(IntegritySignal).where(
                    IntegritySignal.application_id == app.id,
                    IntegritySignal.signal_type == "essay_authenticity",
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(sigs) == 1

    # Idempotent rescan → no duplicate.
    await ReviewPipelineService(db_session).scan_integrity(institution.id, app.id)
    await db_session.commit()
    sigs = (
        (
            await db_session.execute(
                select(IntegritySignal).where(
                    IntegritySignal.application_id == app.id,
                    IntegritySignal.signal_type == "essay_authenticity",
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(sigs) == 1


@pytest.mark.asyncio
async def test_authenticity_disabled_creates_no_signal(
    db_session, mock_student_user, mock_institution_user
):
    profile, institution, program, app = await _seed(
        db_session, mock_student_user, mock_institution_user, essay=True
    )
    # Disable the authenticity surface.
    institution.ai_config = {"surfaces": {"authenticity_risk": {"enabled": False}}}
    await db_session.commit()

    from unipaith.services.review_pipeline_service import ReviewPipelineService

    await ReviewPipelineService(db_session).scan_integrity(institution.id, app.id)
    await db_session.commit()
    sigs = (
        (
            await db_session.execute(
                select(IntegritySignal).where(
                    IntegritySignal.application_id == app.id,
                    IntegritySignal.signal_type == "essay_authenticity",
                )
            )
        )
        .scalars()
        .all()
    )
    assert sigs == []


@pytest.mark.asyncio
async def test_submit_auto_triggers_integrity_scan(
    db_session, mock_student_user, mock_institution_user
):
    profile, institution, program, app = await _seed(
        db_session, mock_student_user, mock_institution_user, essay=True
    )
    # Reset the seeded application to a draft external submission (one app per
    # student/program) with the flagging essay already on file.
    app.status = "draft"
    app.submission_mode = "external"
    await db_session.commit()

    from unipaith.services.application_service import ApplicationService

    result = await ApplicationService(db_session).submit_application(profile.id, app.id)
    assert result.status == "submitted"
    await db_session.commit()

    sigs = (
        (
            await db_session.execute(
                select(IntegritySignal).where(
                    IntegritySignal.application_id == app.id,
                    IntegritySignal.signal_type == "essay_authenticity",
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(sigs) == 1


# ── §1.3 no surface 5xxes when the agent path is unavailable ────────────────


@pytest.mark.asyncio
async def test_ai_surfaces_never_5xx_in_fallback(
    institution_client: AsyncClient, db_session, mock_student_user, mock_institution_user
):
    _, institution, _, app = await _seed(db_session, mock_student_user, mock_institution_user)
    rubric = await _make_rubric(db_session, institution.id)

    calls = [
        institution_client.post(f"{API}/reviews/applications/{app.id}/ai-packet/regenerate"),
        institution_client.post(
            f"{API}/reviews/applications/{app.id}/assistant-chat",
            json={"question": "Summarize."},
        ),
        institution_client.post(
            f"{API}/institutions/me/templates/ai-draft",
            params={"application_id": str(app.id), "message_type": "interview_invite"},
        ),
        institution_client.post(
            f"{API}/reviews/applications/{app.id}/ai-prefill",
            params={"rubric_id": str(rubric.id)},
        ),
    ]
    for coro in calls:
        resp = await coro
        assert resp.status_code == 200, resp.text
