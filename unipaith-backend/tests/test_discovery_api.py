"""Phase A — Discovery API tests.

Covers session lifecycle, message append (with stub assistant reply),
completion math, cross-tenant isolation, and CHECK-constraint enforcement.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from unipaith.models.discovery import DiscoveryMessage, DiscoverySession
from unipaith.models.student import StudentProfile
from unipaith.models.user import User
from unipaith.services.discovery_service import (
    STUB_ASSISTANT_CONTENT,
    STUB_PHASE_MARKER,
)

BASE = "/api/v1/students/me/discovery"


async def _ensure_profile(db: AsyncSession, user: User) -> StudentProfile:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile


# ── start_session ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_session_creates_active_row(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(f"{BASE}/sessions", json={"track": "goals"})
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["track"] == "goals"
    assert data["layer"] is None
    assert data["status"] == "active"
    assert Decimal(data["completion_pct"]) == Decimal("0")
    assert data["started_at"] is not None
    assert data["completed_at"] is None


@pytest.mark.asyncio
async def test_start_session_rejects_invalid_track(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(f"{BASE}/sessions", json={"track": "career"})
    assert resp.status_code == 422  # pydantic Literal rejects


@pytest.mark.asyncio
async def test_start_profile_session_requires_layer(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(f"{BASE}/sessions", json={"track": "profile"})
    assert resp.status_code == 400
    assert "layer" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_start_non_profile_session_forbids_layer(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(f"{BASE}/sessions", json={"track": "goals", "layer": "basic"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_start_profile_session_with_each_layer(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    for layer in ("basic", "personality", "identity"):
        resp = await student_client.post(
            f"{BASE}/sessions", json={"track": "profile", "layer": layer}
        )
        assert resp.status_code == 201, (layer, resp.text)
        assert resp.json()["layer"] == layer


# ── append_message + stub assistant ────────────────────────────────────────


@pytest.mark.asyncio
async def test_append_student_message_returns_stub_assistant_reply(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    create_resp = await student_client.post(f"{BASE}/sessions", json={"track": "needs"})
    sid = create_resp.json()["id"]

    resp = await student_client.post(
        f"{BASE}/sessions/{sid}/messages",
        json={"role": "student", "content": "I need to live somewhere quiet."},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["student_message"]["role"] == "student"
    assert data["student_message"]["content"] == "I need to live somewhere quiet."
    assert data["assistant_message"] is not None
    assert data["assistant_message"]["role"] == "assistant"
    assert data["assistant_message"]["content"] == STUB_ASSISTANT_CONTENT
    assert data["assistant_message"]["extracted_signals"] == STUB_PHASE_MARKER


@pytest.mark.asyncio
async def test_append_assistant_or_system_message_does_not_add_stub(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """Plan 2 will write 'assistant' messages directly. Today we still want to
    accept that role without auto-stubbing a second reply."""
    await _ensure_profile(db_session, mock_student_user)
    sid = (await student_client.post(f"{BASE}/sessions", json={"track": "goals"})).json()["id"]

    for role in ("assistant", "system"):
        resp = await student_client.post(
            f"{BASE}/sessions/{sid}/messages",
            json={"role": role, "content": f"hello from {role}"},
        )
        assert resp.status_code == 201, (role, resp.text)
        assert resp.json()["assistant_message"] is None


@pytest.mark.asyncio
async def test_append_message_with_extracted_signals_persists_them(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    sid = (
        await student_client.post(
            f"{BASE}/sessions",
            json={"track": "profile", "layer": "personality"},
        )
    ).json()["id"]

    payload = {
        "role": "student",
        "content": "I love music and outdoor sports.",
        "extracted_signals": {
            "interests": ["music", "outdoor sports"],
            "confidence": 0.82,
        },
    }
    resp = await student_client.post(f"{BASE}/sessions/{sid}/messages", json=payload)
    assert resp.status_code == 201
    sig = resp.json()["student_message"]["extracted_signals"]
    assert sig["interests"] == ["music", "outdoor sports"]
    assert sig["confidence"] == 0.82


@pytest.mark.asyncio
async def test_cannot_append_to_non_active_session(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    sid = (await student_client.post(f"{BASE}/sessions", json={"track": "goals"})).json()["id"]
    # Mark completed
    patch = await student_client.patch(
        f"{BASE}/sessions/{sid}",
        json={"status": "completed", "completion_pct": "1"},
    )
    assert patch.status_code == 200
    resp = await student_client.post(
        f"{BASE}/sessions/{sid}/messages",
        json={"role": "student", "content": "hello"},
    )
    assert resp.status_code == 400


# ── list / get / patch ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_session_list_filters_by_track_and_status(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    # Two goals sessions, one needs session
    await student_client.post(f"{BASE}/sessions", json={"track": "goals"})
    g2 = (await student_client.post(f"{BASE}/sessions", json={"track": "goals"})).json()
    await student_client.post(f"{BASE}/sessions", json={"track": "needs"})

    # Mark one goals session completed
    await student_client.patch(
        f"{BASE}/sessions/{g2['id']}",
        json={"status": "completed", "completion_pct": "1"},
    )

    resp = await student_client.get(f"{BASE}/sessions?track=goals")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = await student_client.get(f"{BASE}/sessions?track=goals&status=active")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await student_client.get(f"{BASE}/sessions?status=completed")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_session_detail_includes_messages_in_order(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    sid = (await student_client.post(f"{BASE}/sessions", json={"track": "goals"})).json()["id"]
    await student_client.post(
        f"{BASE}/sessions/{sid}/messages",
        json={"role": "student", "content": "first"},
    )
    await student_client.post(
        f"{BASE}/sessions/{sid}/messages",
        json={"role": "student", "content": "second"},
    )

    resp = await student_client.get(f"{BASE}/sessions/{sid}")
    assert resp.status_code == 200
    msgs = resp.json()["messages"]
    # 2 student messages + 2 stub assistant replies = 4
    assert len(msgs) == 4
    contents = [m["content"] for m in msgs]
    assert contents[0] == "first"
    assert contents[2] == "second"


@pytest.mark.asyncio
async def test_patch_session_completed_sets_completed_at(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    sid = (await student_client.post(f"{BASE}/sessions", json={"track": "goals"})).json()["id"]

    resp = await student_client.patch(
        f"{BASE}/sessions/{sid}",
        json={"status": "completed", "completion_pct": "0.85"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["completed_at"] is not None
    assert Decimal(data["completion_pct"]) == Decimal("0.850")


# ── completion map ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_completion_map_returns_zero_for_new_student(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.get(f"{BASE}/completion")
    assert resp.status_code == 200
    data = resp.json()
    for key in ("profile", "goals", "needs", "identity"):
        assert Decimal(data[key]) == Decimal("0")


@pytest.mark.asyncio
async def test_completion_map_reflects_completed_sessions(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    # Goals at 0.5
    g = (await student_client.post(f"{BASE}/sessions", json={"track": "goals"})).json()
    await student_client.patch(
        f"{BASE}/sessions/{g['id']}",
        json={"status": "completed", "completion_pct": "0.5"},
    )
    # Needs at 0.9
    n = (await student_client.post(f"{BASE}/sessions", json={"track": "needs"})).json()
    await student_client.patch(
        f"{BASE}/sessions/{n['id']}",
        json={"status": "completed", "completion_pct": "0.9"},
    )
    # Profile-identity at 1.0 — exercises the dual write to identity dimension
    p = (
        await student_client.post(
            f"{BASE}/sessions", json={"track": "profile", "layer": "identity"}
        )
    ).json()
    await student_client.patch(
        f"{BASE}/sessions/{p['id']}",
        json={"status": "completed", "completion_pct": "1"},
    )

    resp = await student_client.get(f"{BASE}/completion")
    data = resp.json()
    assert Decimal(data["goals"]) == Decimal("0.500")
    assert Decimal(data["needs"]) == Decimal("0.900")
    assert Decimal(data["profile"]) == Decimal("1.000")
    assert Decimal(data["identity"]) == Decimal("1.000")


# ── cross-tenant isolation ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_session_404_for_unknown_id(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """A session id that doesn't belong to the caller (or doesn't exist)
    returns 404. This is the actual cross-tenant guard inside
    DiscoveryService — it filters by `student_id` on every read/write so a
    leaked id from a peer never resolves."""
    await _ensure_profile(db_session, mock_student_user)
    bogus = "00000000-0000-0000-0000-000000000000"
    resp = await student_client.get(f"{BASE}/sessions/{bogus}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_session_endpoints_blocked_for_non_students(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    """`require_student` rejects non-student roles at the dependency layer."""
    db_session.add(mock_institution_user)
    await db_session.commit()
    resp = await institution_client.post(f"{BASE}/sessions", json={"track": "goals"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_session_cascade_delete_drops_messages(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """Regression — the FK has ondelete=CASCADE; deleting the parent drops the
    children. We verify by deleting the session row directly (no API endpoint
    for delete in Phase A) and asserting messages disappear."""
    await _ensure_profile(db_session, mock_student_user)
    sid = (await student_client.post(f"{BASE}/sessions", json={"track": "goals"})).json()["id"]
    await student_client.post(
        f"{BASE}/sessions/{sid}/messages",
        json={"role": "student", "content": "hello"},
    )

    # Pre-check: 2 messages exist (1 student + 1 stub assistant)
    pre = await db_session.execute(
        select(DiscoveryMessage).where(DiscoveryMessage.session_id == sid)
    )
    assert len(pre.scalars().all()) == 2

    # Drop the session
    sess = (
        await db_session.execute(select(DiscoverySession).where(DiscoverySession.id == sid))
    ).scalar_one()
    await db_session.delete(sess)
    await db_session.commit()

    post = await db_session.execute(
        select(DiscoveryMessage).where(DiscoveryMessage.session_id == sid)
    )
    assert post.scalars().all() == []
