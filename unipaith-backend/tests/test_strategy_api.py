"""Phase A — Strategy API tests.

Covers:
- Generation guards (no goals → 400)
- Generation produces non-empty rule-based content + is_stub=True
- Career → degree mapping (parametrized)
- Versioning monotonic per student
- One-active-strategy invariant under activate/re-activate flows
- Edit creates new draft + archives original (clone-and-modify)
- Auth isolation
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unipaith.models.student import StudentProfile
from unipaith.models.user import User

STRAT = "/api/v1/students/me/strategy"
GOALS = "/api/v1/students/me/goals"
NEEDS = "/api/v1/students/me/needs"


async def _ensure_profile(db: AsyncSession, user: User) -> StudentProfile:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile


async def _seed_active_academic_goal(
    client: AsyncClient, specific: str = "Become a family medicine physician."
) -> dict:
    resp = await client.post(GOALS, json={"category": "academic", "specific": specific})
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── generation guards ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_with_no_goals_returns_400(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post(f"{STRAT}/generate")
    assert resp.status_code == 400
    assert "academic goal" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_generate_succeeds_with_one_academic_goal(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    await _seed_active_academic_goal(student_client)
    resp = await student_client.post(f"{STRAT}/generate")
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "draft"
    assert data["version"] == 1
    assert data["is_stub"] is True
    assert data["career_target"]
    assert data["target_degree"]
    assert len(data["academic_path"]) >= 1
    assert len(data["financial_path"]) >= 1
    assert len(data["geographic_path"]) >= 1
    assert data["narrative"]


# ── career → degree mapping ───────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "specific,expected_degree",
    [
        ("Become a family medicine physician", "MD"),
        ("Practice law as an immigration attorney", "JD"),
        ("Get an MBA and consult", "MBA"),
        ("Pursue a PhD in physics academia", "PhD"),
        ("Work as a data scientist building ML systems", "Master's in CS / Data Science"),
        ("Become a software engineer", "BS / MS in Computer Science"),
        ("Start a public health career", "MPH"),
        ("Knit sweaters professionally", "TBD"),
    ],
)
async def test_career_target_to_degree_mapping(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    specific: str,
    expected_degree: str,
):
    await _ensure_profile(db_session, mock_student_user)
    await _seed_active_academic_goal(student_client, specific=specific)
    resp = await student_client.post(f"{STRAT}/generate")
    assert resp.status_code == 201, resp.text
    assert resp.json()["target_degree"] == expected_degree


# ── versioning + active invariant ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_versions_monotonic_per_student(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    await _seed_active_academic_goal(student_client)
    v1 = (await student_client.post(f"{STRAT}/generate")).json()
    v2 = (await student_client.post(f"{STRAT}/generate")).json()
    v3 = (await student_client.post(f"{STRAT}/generate")).json()
    assert (v1["version"], v2["version"], v3["version"]) == (1, 2, 3)


@pytest.mark.asyncio
async def test_versions_list_ordered_desc(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    await _seed_active_academic_goal(student_client)
    for _ in range(3):
        await student_client.post(f"{STRAT}/generate")
    resp = await student_client.get(f"{STRAT}/versions")
    assert resp.status_code == 200
    versions = [s["version"] for s in resp.json()]
    assert versions == sorted(versions, reverse=True)


@pytest.mark.asyncio
async def test_active_returns_null_initially(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.get(f"{STRAT}/active")
    assert resp.status_code == 200
    assert resp.json() is None


@pytest.mark.asyncio
async def test_activate_promotes_draft_to_active(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    await _seed_active_academic_goal(student_client)
    s = (await student_client.post(f"{STRAT}/generate")).json()

    resp = await student_client.post(f"{STRAT}/{s['id']}/activate")
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"

    active = (await student_client.get(f"{STRAT}/active")).json()
    assert active["id"] == s["id"]


@pytest.mark.asyncio
async def test_activating_new_archives_previous_active(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """The partial unique index forbids two active rows. Service must archive
    the previous active before promoting the new one — no IntegrityError."""
    await _ensure_profile(db_session, mock_student_user)
    await _seed_active_academic_goal(student_client)
    a = (await student_client.post(f"{STRAT}/generate")).json()
    b = (await student_client.post(f"{STRAT}/generate")).json()

    await student_client.post(f"{STRAT}/{a['id']}/activate")
    resp = await student_client.post(f"{STRAT}/{b['id']}/activate")
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "active"

    # a should now be archived
    a_after = (await student_client.get(f"{STRAT}/{a['id']}")).json()
    assert a_after["status"] == "archived"

    # active endpoint returns b
    active = (await student_client.get(f"{STRAT}/active")).json()
    assert active["id"] == b["id"]


@pytest.mark.asyncio
async def test_reactivating_active_is_idempotent(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    await _seed_active_academic_goal(student_client)
    s = (await student_client.post(f"{STRAT}/generate")).json()
    await student_client.post(f"{STRAT}/{s['id']}/activate")
    resp = await student_client.post(f"{STRAT}/{s['id']}/activate")
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


@pytest.mark.asyncio
async def test_cannot_activate_archived_strategy(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    await _seed_active_academic_goal(student_client)
    a = (await student_client.post(f"{STRAT}/generate")).json()
    b = (await student_client.post(f"{STRAT}/generate")).json()
    await student_client.post(f"{STRAT}/{a['id']}/activate")
    await student_client.post(f"{STRAT}/{b['id']}/activate")
    # a is now archived; trying to activate it must fail.
    resp = await student_client.post(f"{STRAT}/{a['id']}/activate")
    assert resp.status_code == 400


# ── update creates new draft ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_archives_original_creates_new_draft(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    await _seed_active_academic_goal(student_client)
    orig = (await student_client.post(f"{STRAT}/generate")).json()

    resp = await student_client.patch(
        f"{STRAT}/{orig['id']}",
        json={"target_degree": "MD-PhD"},
    )
    assert resp.status_code == 200, resp.text
    new = resp.json()
    assert new["id"] != orig["id"]
    assert new["status"] == "draft"
    assert new["version"] == orig["version"] + 1
    assert new["target_degree"] == "MD-PhD"
    # Inherited from original
    assert new["career_target"] == orig["career_target"]
    assert len(new["academic_path"]) == len(orig["academic_path"])

    # Original is now archived
    orig_after = (await student_client.get(f"{STRAT}/{orig['id']}")).json()
    assert orig_after["status"] == "archived"


@pytest.mark.asyncio
async def test_update_active_archives_it_and_no_active_remains(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """Editing an active strategy archives it. The new draft is NOT
    auto-activated — there's a brief no-active window until the user calls
    activate explicitly."""
    await _ensure_profile(db_session, mock_student_user)
    await _seed_active_academic_goal(student_client)
    s = (await student_client.post(f"{STRAT}/generate")).json()
    await student_client.post(f"{STRAT}/{s['id']}/activate")

    new = (await student_client.patch(f"{STRAT}/{s['id']}", json={"narrative": "rewritten"})).json()
    assert new["status"] == "draft"
    assert new["narrative"] == "rewritten"

    # No active strategy anymore
    active = (await student_client.get(f"{STRAT}/active")).json()
    assert active is None


@pytest.mark.asyncio
async def test_cannot_update_archived_strategy(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    await _seed_active_academic_goal(student_client)
    s = (await student_client.post(f"{STRAT}/generate")).json()
    # First edit: archives original
    await student_client.patch(f"{STRAT}/{s['id']}", json={"narrative": "v1 narrative"})
    # Second edit on the now-archived original: rejected
    resp = await student_client.patch(f"{STRAT}/{s['id']}", json={"narrative": "v2 narrative"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_with_explicit_empty_list_clears_field(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    await _seed_active_academic_goal(student_client)
    s = (await student_client.post(f"{STRAT}/generate")).json()
    new = (await student_client.patch(f"{STRAT}/{s['id']}", json={"academic_path": []})).json()
    assert new["academic_path"] == []


# ── auth ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_strategy_blocked_for_non_students(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    db_session.add(mock_institution_user)
    await db_session.commit()
    resp = await institution_client.get(f"{STRAT}/active")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unknown_strategy_returns_404(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    bogus = "00000000-0000-0000-0000-000000000000"
    resp = await student_client.get(f"{STRAT}/{bogus}")
    assert resp.status_code == 404


# ── provenance + needs → geographic_path ──────────────────────────────────


@pytest.mark.asyncio
async def test_geographic_path_pulls_from_social_needs(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    await _seed_active_academic_goal(student_client)
    # Two social needs — geographic_path should mention both regions.
    await student_client.post(
        NEEDS,
        json={
            "maslow_level": "social",
            "need_type": "Northeast US",
            "signal": "Wants to be near family in NYC.",
            "severity": "must_have",
        },
    )
    await student_client.post(
        NEEDS,
        json={
            "maslow_level": "social",
            "need_type": "International student community",
            "signal": "Prefers diverse cohort.",
            "severity": "strong_preference",
        },
    )

    resp = await student_client.post(f"{STRAT}/generate")
    geo = resp.json()["geographic_path"]
    regions = {item["region"] for item in geo}
    assert "Northeast US" in regions
    assert "International student community" in regions
