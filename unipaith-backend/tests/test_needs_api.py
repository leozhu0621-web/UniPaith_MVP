"""Phase A — Needs API tests.

CRUD + Maslow-level enum + provenance (incl. the 'inferred' source which
allows session_id either way) + auth isolation.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unipaith.models.student import StudentProfile
from unipaith.models.user import User

NEEDS = "/api/v1/students/me/needs"
DISC = "/api/v1/students/me/discovery"


async def _ensure_profile(db: AsyncSession, user: User) -> StudentProfile:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile


@pytest.mark.asyncio
async def test_create_manual_need(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        NEEDS,
        json={
            "maslow_level": "physiological",
            "need_type": "housing",
            "signal": "Needs on-campus housing or affordable rent.",
            "severity": "must_have",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["maslow_level"] == "physiological"
    assert data["severity"] == "must_have"
    assert data["source"] == "manual"


@pytest.mark.asyncio
async def test_all_maslow_levels_accepted(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    for level in (
        "physiological",
        "safety",
        "social",
        "self_esteem",
        "self_actualization",
    ):
        resp = await student_client.post(
            NEEDS,
            json={
                "maslow_level": level,
                "need_type": f"type-{level}",
                "signal": "x",
                "severity": "nice_to_have",
            },
        )
        assert resp.status_code == 201, (level, resp.text)


@pytest.mark.asyncio
async def test_invalid_maslow_level_rejected(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        NEEDS,
        json={
            "maslow_level": "self_transcendence",  # not in the enum
            "need_type": "x",
            "signal": "x",
            "severity": "must_have",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_invalid_severity_rejected(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        NEEDS,
        json={
            "maslow_level": "safety",
            "need_type": "x",
            "signal": "x",
            "severity": "blocker",  # not in the enum
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_discovery_need_requires_session_id(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        NEEDS,
        json={
            "maslow_level": "social",
            "need_type": "community",
            "signal": "x",
            "severity": "must_have",
            "source": "discovery",
        },
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_manual_need_rejects_session_id(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    sid = (await student_client.post(f"{DISC}/sessions", json={"track": "needs"})).json()["id"]
    resp = await student_client.post(
        NEEDS,
        json={
            "maslow_level": "social",
            "need_type": "community",
            "signal": "x",
            "severity": "must_have",
            "source": "manual",
            "source_session_id": sid,
        },
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_inferred_need_accepts_session_id_either_way(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """'inferred' source covers cross-session inference. The DB CHECK and
    service both allow it with or without a session id."""
    await _ensure_profile(db_session, mock_student_user)
    # Without session_id
    r1 = await student_client.post(
        NEEDS,
        json={
            "maslow_level": "self_actualization",
            "need_type": "research_culture",
            "signal": "Repeatedly mentioned wanting to publish.",
            "severity": "strong_preference",
            "source": "inferred",
        },
    )
    assert r1.status_code == 201, r1.text

    # With session_id
    sid = (await student_client.post(f"{DISC}/sessions", json={"track": "needs"})).json()["id"]
    r2 = await student_client.post(
        NEEDS,
        json={
            "maslow_level": "self_esteem",
            "need_type": "scholarship",
            "signal": "x",
            "severity": "must_have",
            "source": "inferred",
            "source_session_id": sid,
        },
    )
    assert r2.status_code == 201, r2.text


@pytest.mark.asyncio
async def test_list_filters_by_maslow_level(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    await student_client.post(
        NEEDS,
        json={
            "maslow_level": "physiological",
            "need_type": "housing",
            "signal": "x",
            "severity": "must_have",
        },
    )
    await student_client.post(
        NEEDS,
        json={
            "maslow_level": "social",
            "need_type": "community",
            "signal": "x",
            "severity": "must_have",
        },
    )
    resp = await student_client.get(f"{NEEDS}?maslow_level=physiological")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["need_type"] == "housing"


@pytest.mark.asyncio
async def test_partial_update_preserves_fields(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    n = (
        await student_client.post(
            NEEDS,
            json={
                "maslow_level": "social",
                "need_type": "community",
                "signal": "Wants international student community.",
                "severity": "strong_preference",
            },
        )
    ).json()
    resp = await student_client.put(f"{NEEDS}/{n['id']}", json={"severity": "must_have"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["severity"] == "must_have"
    assert data["maslow_level"] == "social"
    assert data["need_type"] == "community"
    assert data["signal"].startswith("Wants international")


@pytest.mark.asyncio
async def test_delete_need(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    n = (
        await student_client.post(
            NEEDS,
            json={
                "maslow_level": "safety",
                "need_type": "healthcare",
                "signal": "x",
                "severity": "must_have",
            },
        )
    ).json()
    resp = await student_client.delete(f"{NEEDS}/{n['id']}")
    assert resp.status_code == 204
    resp = await student_client.put(f"{NEEDS}/{n['id']}", json={"severity": "nice_to_have"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_needs_blocked_for_non_students(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    db_session.add(mock_institution_user)
    await db_session.commit()
    resp = await institution_client.get(NEEDS)
    assert resp.status_code == 403
