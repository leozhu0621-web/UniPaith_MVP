"""Phase A — Identity API tests.

Single-row-per-student. The critical regression is that partial upserts must
PRESERVE existing list values — naive upsert (set every field) would clobber
core_values on a request that only changed worldview.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.student import StudentProfile
from unipaith.models.user import User
from unipaith.services.identity_service import STUB_IDENTITY_SUMMARY

IDENT = "/api/v1/students/me/identity"


async def _ensure_profile(db: AsyncSession, user: User) -> StudentProfile:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile


@pytest.mark.asyncio
async def test_get_identity_auto_creates_empty_row(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """First read of a student's identity should not 404; it returns a fresh
    empty row so the client doesn't have to special-case the bootstrap."""
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.get(IDENT)
    assert resp.status_code == 200
    data = resp.json()
    assert data["core_values"] == []
    assert data["worldview"] == []
    assert data["self_awareness"] == []
    assert data["identity_summary"] is None


@pytest.mark.asyncio
async def test_upsert_writes_all_three_lists(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    body = {
        "core_values": [
            {
                "value": "Curiosity",
                "evidence": "Switched majors twice based on interest.",
                "confidence": "0.9",
                "source_quote": "I switched because I wanted to learn more.",
            }
        ],
        "worldview": [
            {
                "belief": "Growth requires discomfort.",
                "context": "Brought up mid-conversation about hard classes.",
                "confidence": "0.7",
            }
        ],
        "self_awareness": [
            {
                "insight": "I underestimate prep time.",
                "trigger_event": "Missed two deadlines last semester.",
                "confidence": "0.8",
            }
        ],
    }
    resp = await student_client.put(IDENT, json=body)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["core_values"]) == 1
    assert data["core_values"][0]["value"] == "Curiosity"
    assert len(data["worldview"]) == 1
    assert len(data["self_awareness"]) == 1


@pytest.mark.asyncio
async def test_upsert_partial_preserves_other_fields(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """Regression — a request that only sets `worldview` must NOT clobber
    core_values or self_awareness."""
    await _ensure_profile(db_session, mock_student_user)
    # First write: full payload
    await student_client.put(
        IDENT,
        json={
            "core_values": [
                {
                    "value": "Curiosity",
                    "evidence": "x",
                }
            ],
            "self_awareness": [{"insight": "y", "trigger_event": "z"}],
        },
    )
    # Second write: only worldview
    resp = await student_client.put(
        IDENT,
        json={"worldview": [{"belief": "Effort compounds.", "context": "x"}]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["core_values"]) == 1
    assert data["core_values"][0]["value"] == "Curiosity"
    assert len(data["self_awareness"]) == 1
    assert data["self_awareness"][0]["insight"] == "y"
    assert len(data["worldview"]) == 1


@pytest.mark.asyncio
async def test_explicit_empty_list_clears_field(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """Passing `[]` explicitly is intentional clearing, distinct from omitting
    the key (which preserves)."""
    await _ensure_profile(db_session, mock_student_user)
    await student_client.put(
        IDENT,
        json={"core_values": [{"value": "v", "evidence": "e"}]},
    )
    resp = await student_client.put(IDENT, json={"core_values": []})
    assert resp.status_code == 200
    assert resp.json()["core_values"] == []


@pytest.mark.asyncio
async def test_invalid_confidence_in_list_item_rejected(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.put(
        IDENT,
        json={"core_values": [{"value": "v", "evidence": "e", "confidence": "1.5"}]},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_regenerate_summary_returns_stub(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    # Seed with some structured fields so the regenerate is operating on
    # something real.
    await student_client.put(
        IDENT,
        json={"core_values": [{"value": "v", "evidence": "e"}]},
    )
    resp = await student_client.post(f"{IDENT}/regenerate-summary")
    assert resp.status_code == 200
    assert resp.json()["identity_summary"] == STUB_IDENTITY_SUMMARY


@pytest.mark.asyncio
async def test_identity_blocked_for_non_students(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    db_session.add(mock_institution_user)
    await db_session.commit()
    resp = await institution_client.get(IDENT)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_returns_same_row_after_upsert(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """Identity is single-row — a second GET must return the same student_id
    and reflect the latest upsert."""
    await _ensure_profile(db_session, mock_student_user)
    first = (await student_client.get(IDENT)).json()
    await student_client.put(
        IDENT,
        json={"identity_summary": "manual override"},
    )
    second = (await student_client.get(IDENT)).json()
    assert first["student_id"] == second["student_id"]
    assert second["identity_summary"] == "manual override"
