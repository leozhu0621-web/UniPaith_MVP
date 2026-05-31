"""Profile Overview endpoint + portable export (spec 10 §4, §16, §18)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.student import StudentProfile
from unipaith.models.user import User

OVERVIEW = "/api/v1/students/me/profile/overview"
EXPORT = "/api/v1/students/me/profile/export"

# spec 10 §18 CompletionCategory enum
CATEGORIES = {
    "identity",
    "academics",
    "experience",
    "goals",
    "needs",
    "strategy",
    "preparation",
    "preferences",
    "financial",
    "data",
}


async def _ensure_profile(db: AsyncSession, user: User) -> StudentProfile:
    profile = StudentProfile(
        user_id=user.id, first_name="Sienna", last_name="Chen", nationality="United States"
    )
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile


@pytest.mark.asyncio
async def test_overview_shape(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.get(OVERVIEW)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["personal"]["first_name"] == "Sienna"
    assert data["personal"]["primary_email"] == mock_student_user.email
    comp = data["completion"]
    assert 0 <= comp["overall_pct"] <= 100
    cats = {c["category"] for c in comp["per_category"]}
    assert CATEGORIES.issubset(cats)
    for c in comp["per_category"]:
        assert 0 <= c["pct"] <= 100
    assert isinstance(data["next_actions"], list)
    assert len(data["next_actions"]) <= 4


@pytest.mark.asyncio
async def test_overview_next_actions_for_empty_profile(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    actions = (await student_client.get(OVERVIEW)).json()["next_actions"]
    assert len(actions) >= 1
    assert all(a["deep_link"].startswith("/s/profile?tab=") for a in actions)
    assert all(a["action"] and a["reason"] for a in actions)


@pytest.mark.asyncio
async def test_export_json(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.get(EXPORT, params={"format": "json"})
    assert resp.status_code == 200
    assert "application/json" in resp.headers["content-type"]
    assert resp.json()["first_name"] == "Sienna"


@pytest.mark.asyncio
async def test_export_pdf(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.get(EXPORT, params={"format": "pdf"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:5] == b"%PDF-"


@pytest.mark.asyncio
async def test_export_commonapp_mapping(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.get(EXPORT, params={"format": "commonapp"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["format"] == "commonapp"
    assert body["fields"]["personal.legal_name.first"] == "Sienna"
    assert isinstance(body["unmapped"], list)


@pytest.mark.asyncio
async def test_overview_blocked_for_non_students(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    db_session.add(mock_institution_user)
    await db_session.commit()
    resp = await institution_client.get(OVERVIEW)
    assert resp.status_code == 403
