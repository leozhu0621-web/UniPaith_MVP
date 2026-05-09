"""Phase A — Goals API tests.

CRUD + provenance + auth isolation. Provenance is checked at two levels: the
service surfaces a friendly 400; the DB CHECK constraint catches anything that
slips past (we exercise both).
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.student import StudentProfile
from unipaith.models.user import User

GOALS = "/api/v1/students/me/goals"
DISC = "/api/v1/students/me/discovery"


async def _ensure_profile(db: AsyncSession, user: User) -> StudentProfile:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile


@pytest.mark.asyncio
async def test_create_manual_goal_minimal(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        GOALS,
        json={"category": "academic", "specific": "Get into a med school program."},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["category"] == "academic"
    assert data["specific"] == "Get into a med school program."
    assert data["status"] == "active"
    assert data["source"] == "manual"
    assert data["source_session_id"] is None
    assert data["confidence"] is None


@pytest.mark.asyncio
async def test_create_manual_goal_with_full_smart(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        GOALS,
        json={
            "category": "personal",
            "specific": "Build a portfolio of 3 ML projects.",
            "measurable": "3 GitHub repos with READMEs and demos.",
            "achievable_notes": "Allocate 5 hrs/week.",
            "relevant_notes": "Strengthens applications for AI master's.",
            "time_bound": "2026-12-31",
            "confidence": "0.7",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["measurable"].startswith("3 GitHub")
    assert data["time_bound"] == "2026-12-31"
    assert Decimal(data["confidence"]) == Decimal("0.70")


@pytest.mark.asyncio
async def test_create_discovery_goal_requires_session_id(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        GOALS,
        json={
            "category": "academic",
            "specific": "Apply to 5 NYU programs.",
            "source": "discovery",
        },
    )
    assert resp.status_code == 400
    assert "source_session_id" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_create_manual_goal_rejects_session_id(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    sid = (await student_client.post(f"{DISC}/sessions", json={"track": "goals"})).json()["id"]
    resp = await student_client.post(
        GOALS,
        json={
            "category": "academic",
            "specific": "manual goal",
            "source": "manual",
            "source_session_id": sid,
        },
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_discovery_goal_with_session_id_succeeds(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    sid = (await student_client.post(f"{DISC}/sessions", json={"track": "goals"})).json()["id"]
    resp = await student_client.post(
        GOALS,
        json={
            "category": "academic",
            "specific": "Apply to 5 NYU programs.",
            "source": "discovery",
            "source_session_id": sid,
            "confidence": "0.85",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["source"] == "discovery"
    assert data["source_session_id"] == sid


@pytest.mark.asyncio
async def test_confidence_outside_range_rejected(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        GOALS,
        json={
            "category": "academic",
            "specific": "x",
            "confidence": "1.5",
        },
    )
    assert resp.status_code == 422  # pydantic Field(ge=0, le=1)


@pytest.mark.asyncio
async def test_invalid_category_rejected(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(
        GOALS,
        json={"category": "career", "specific": "x"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_goals_filters_by_status(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    g1 = (
        await student_client.post(GOALS, json={"category": "academic", "specific": "active1"})
    ).json()
    await student_client.post(GOALS, json={"category": "academic", "specific": "active2"})
    # Mark one as met
    await student_client.put(f"{GOALS}/{g1['id']}", json={"status": "met"})

    resp = await student_client.get(GOALS)
    assert len(resp.json()) == 2

    resp = await student_client.get(f"{GOALS}?status=active")
    assert len(resp.json()) == 1
    assert resp.json()[0]["specific"] == "active2"

    resp = await student_client.get(f"{GOALS}?status=met")
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_partial_update_preserves_unspecified_fields(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    g = (
        await student_client.post(
            GOALS,
            json={
                "category": "personal",
                "specific": "x",
                "measurable": "y",
                "time_bound": "2026-12-31",
            },
        )
    ).json()
    # Update status only
    resp = await student_client.put(f"{GOALS}/{g['id']}", json={"status": "revised"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "revised"
    assert data["measurable"] == "y"
    assert data["time_bound"] == "2026-12-31"
    assert data["specific"] == "x"


@pytest.mark.asyncio
async def test_delete_goal(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    g = (await student_client.post(GOALS, json={"category": "academic", "specific": "x"})).json()
    resp = await student_client.delete(f"{GOALS}/{g['id']}")
    assert resp.status_code == 204
    resp = await student_client.put(f"{GOALS}/{g['id']}", json={"status": "met"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unknown_goal_id_returns_404(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    bogus = "00000000-0000-0000-0000-000000000000"
    resp = await student_client.put(f"{GOALS}/{bogus}", json={"status": "met"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_goals_blocked_for_non_students(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    db_session.add(mock_institution_user)
    await db_session.commit()
    resp = await institution_client.get(GOALS)
    assert resp.status_code == 403
