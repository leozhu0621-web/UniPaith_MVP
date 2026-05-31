"""Spec 19 — Discovery stage gap-closing behaviors.

Covers the end-to-end fixes that make the 3-track conversation actually
progress and hand off:

  - completion map reflects ACTIVE session progress (not only completed)
  - profile layer auto-advance: layer-complete → current session completed +
    next-layer session spawned; identity completes terminally
  - deterministic DiscoveryJudge handoff at the >=50% threshold
  - personality-signals endpoint reconstructs facets from extractions
  - rule-based fallback prompt on orchestrator failure (2xx, never 5xx)

These run with AI_MOCK_MODE=true; the LLM-path test monkeypatches the agent
import so no real API calls happen (mirrors test_plan2_integration.py).
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.discovery import DiscoveryMessage, DiscoverySession
from unipaith.models.student import StudentProfile
from unipaith.models.user import User
from unipaith.services.discovery_service import (
    PROFILE_LAYER_ORDER,
    DiscoveryService,
    _normalize_confidence,
)

BASE = "/api/v1/students/me/discovery"


async def _ensure_profile(db: AsyncSession, user: User) -> StudentProfile:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile


# ── completion map reflects active progress ─────────────────────────────────


@pytest.mark.asyncio
async def test_completion_map_reflects_active_session_progress(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """An ACTIVE goals session with completion_pct set must show up in the
    completion map — the gate/progress UI reads live progress, not only
    completed sessions."""
    await _ensure_profile(db_session, mock_student_user)
    sid = (await student_client.post(f"{BASE}/sessions", json={"track": "goals"})).json()["id"]

    sess = (
        await db_session.execute(select(DiscoverySession).where(DiscoverySession.id == sid))
    ).scalar_one()
    sess.completion_pct = Decimal("0.5")
    await db_session.commit()

    resp = await student_client.get(f"{BASE}/completion")
    assert resp.status_code == 200
    assert Decimal(resp.json()["goals"]) == Decimal("0.500")


# ── profile layer auto-advance ──────────────────────────────────────────────


class _FakeVerdict:
    """Minimal stand-in for LayerVerdict for the advance hook."""

    def __init__(self, *, layer_complete: bool):
        self.layer_complete = layer_complete
        self.completion_pct = Decimal("0.8")
        self.next_probe_hint = None


@pytest.mark.asyncio
async def test_profile_layer_auto_advances_and_spawns_next(
    db_session: AsyncSession, mock_student_user: User
):
    profile = await _ensure_profile(db_session, mock_student_user)
    svc = DiscoveryService(db_session)
    basic = DiscoverySession(
        student_id=profile.id,
        track="profile",
        layer="basic",
        status="active",
        completion_pct=Decimal("0.8"),
    )
    db_session.add(basic)
    await db_session.flush()

    await svc._maybe_advance_profile_layer(session=basic, verdict=_FakeVerdict(layer_complete=True))
    await db_session.commit()

    await db_session.refresh(basic)
    assert basic.status == "completed"
    assert basic.completion_pct == Decimal("0.8")

    rows = (
        (
            await db_session.execute(
                select(DiscoverySession).where(
                    DiscoverySession.student_id == profile.id,
                    DiscoverySession.layer == "personality",
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].status == "active"
    assert rows[0].completion_pct == Decimal("0")


@pytest.mark.asyncio
async def test_identity_layer_completes_terminally(
    db_session: AsyncSession, mock_student_user: User
):
    """Identity is the deepest layer — completing it must NOT spawn a successor."""
    profile = await _ensure_profile(db_session, mock_student_user)
    svc = DiscoveryService(db_session)
    identity = DiscoverySession(
        student_id=profile.id,
        track="profile",
        layer="identity",
        status="active",
        completion_pct=Decimal("0.9"),
    )
    db_session.add(identity)
    await db_session.flush()

    await svc._maybe_advance_profile_layer(
        session=identity, verdict=_FakeVerdict(layer_complete=True)
    )
    await db_session.commit()

    await db_session.refresh(identity)
    assert identity.status == "completed"
    all_sessions = (
        (
            await db_session.execute(
                select(DiscoverySession).where(DiscoverySession.student_id == profile.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(all_sessions) == 1
    assert PROFILE_LAYER_ORDER[-1] == "identity"


@pytest.mark.asyncio
async def test_incomplete_layer_does_not_advance(db_session: AsyncSession, mock_student_user: User):
    profile = await _ensure_profile(db_session, mock_student_user)
    svc = DiscoveryService(db_session)
    basic = DiscoverySession(
        student_id=profile.id,
        track="profile",
        layer="basic",
        status="active",
        completion_pct=Decimal("0.4"),
    )
    db_session.add(basic)
    await db_session.flush()

    await svc._maybe_advance_profile_layer(
        session=basic, verdict=_FakeVerdict(layer_complete=False)
    )
    await db_session.commit()

    await db_session.refresh(basic)
    assert basic.status == "active"


# ── deterministic handoff judge ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handoff_judge_true_at_threshold(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    for track in ("goals", "needs"):
        sid = (await student_client.post(f"{BASE}/sessions", json={"track": track})).json()["id"]
        await student_client.patch(
            f"{BASE}/sessions/{sid}", json={"status": "completed", "completion_pct": "0.6"}
        )
    pid = (
        await student_client.post(f"{BASE}/sessions", json={"track": "profile", "layer": "basic"})
    ).json()["id"]
    await student_client.patch(
        f"{BASE}/sessions/{pid}", json={"status": "completed", "completion_pct": "0.7"}
    )

    resp = await student_client.get(f"{BASE}/handoff")
    assert resp.status_code == 200
    data = resp.json()
    assert data["should_handoff"] is True
    assert data["handoff_target"] == "recommendation"


@pytest.mark.asyncio
async def test_handoff_judge_false_when_behind(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    sid = (await student_client.post(f"{BASE}/sessions", json={"track": "goals"})).json()["id"]
    await student_client.patch(
        f"{BASE}/sessions/{sid}", json={"status": "completed", "completion_pct": "0.9"}
    )

    resp = await student_client.get(f"{BASE}/handoff")
    assert resp.status_code == 200
    data = resp.json()
    assert data["should_handoff"] is False
    assert data["handoff_target"] is None


# ── personality-signals endpoint ────────────────────────────────────────────


def test_normalize_confidence_handles_both_scales():
    assert _normalize_confidence(0.82) == 82
    assert _normalize_confidence(82) == 82
    assert _normalize_confidence(1) == 100
    assert _normalize_confidence(None) is None
    assert _normalize_confidence("nope") is None


@pytest.mark.asyncio
async def test_personality_signals_reconstructed_from_extractions(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    profile = await _ensure_profile(db_session, mock_student_user)
    sess = DiscoverySession(
        student_id=profile.id,
        track="profile",
        layer="personality",
        status="active",
        completion_pct=Decimal("0.3"),
    )
    db_session.add(sess)
    await db_session.flush()
    db_session.add(
        DiscoveryMessage(
            session_id=sess.id,
            role="student",
            content="I'm always the one who plans the group trips.",
            extracted_signals={
                "personality": [
                    {
                        "facet": "peer_style",
                        "value": "the organizer",
                        "evidence": "I'm always the one who plans the group trips.",
                        "confidence": 0.82,
                    }
                ]
            },
        )
    )
    await db_session.commit()

    resp = await student_client.get(f"{BASE}/personality-signals")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["facet"] == "peer_style"
    assert data[0]["value"] == "the organizer"
    assert data[0]["confidence"] == 82


@pytest.mark.asyncio
async def test_personality_signals_empty_for_new_student(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.get(f"{BASE}/personality-signals")
    assert resp.status_code == 200
    assert resp.json() == []


# ── rule-based fallback on orchestrator failure (never 5xx) ──────────────────


@pytest.mark.asyncio
async def test_orchestrator_failure_serves_rule_based_prompt(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    monkeypatch,
):
    """Spec 19 §9 — when the v2 pipeline raises, the turn still returns 201
    with a rule-based assistant prompt (marked _mode=rule_based), never a 5xx."""
    await _ensure_profile(db_session, mock_student_user)
    monkeypatch.setattr(settings, "ai_discovery_v2_enabled", True)

    import unipaith.ai.extractor as extractor_mod

    def _boom():
        raise RuntimeError("simulated agent outage")

    monkeypatch.setattr(extractor_mod, "get_extractor", _boom)

    sid = (
        await student_client.post(f"{BASE}/sessions", json={"track": "profile", "layer": "basic"})
    ).json()["id"]
    resp = await student_client.post(
        f"{BASE}/sessions/{sid}/messages",
        json={"role": "student", "content": "Hi, I'm a senior."},
    )
    assert resp.status_code == 201, resp.text
    assistant = resp.json()["assistant_message"]
    assert assistant is not None
    assert assistant["extracted_signals"]["_mode"] == "rule_based"
    assert "course" in assistant["content"].lower()
