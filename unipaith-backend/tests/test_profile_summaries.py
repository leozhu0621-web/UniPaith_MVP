"""Phase A — Profile summary auto-update tests.

Two service hooks keep `student_profiles.discovery_completion` and
`student_profiles.strategy_active_id` in sync with downstream tables.
This file validates both hooks fire correctly and that the GET /me/profile
response surfaces the resulting values.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unipaith.models.student import StudentProfile
from unipaith.models.user import User

PROFILE = "/api/v1/students/me/profile"
DISC = "/api/v1/students/me/discovery"
GOALS = "/api/v1/students/me/goals"
STRAT = "/api/v1/students/me/strategy"


async def _ensure_profile(db: AsyncSession, user: User) -> StudentProfile:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile


# ── discovery_completion auto-update ──────────────────────────────────────


@pytest.mark.asyncio
async def test_profile_starts_with_empty_completion(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """A fresh profile has no completed sessions; the summary should be the
    default empty dict (or all zeros — either is acceptable post-Phase-A2)."""
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.get(PROFILE)
    assert resp.status_code == 200
    data = resp.json()
    completion = data["discovery_completion"]
    # Either {} (fresh row) or {profile:0, goals:0, needs:0, identity:0}
    # is correct. Phase A2 may have already touched the row.
    if completion:
        assert all(v == 0 for v in completion.values())


@pytest.mark.asyncio
async def test_completion_summary_updates_on_session_complete(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """When DiscoveryService.update_session sets a session to 'completed',
    the profile's discovery_completion field reflects the new max-per-track
    value. Phase B's home page reads this without joining."""
    await _ensure_profile(db_session, mock_student_user)

    # Start + complete a goals session at 0.7
    g = (await student_client.post(f"{DISC}/sessions", json={"track": "goals"})).json()
    await student_client.patch(
        f"{DISC}/sessions/{g['id']}",
        json={"status": "completed", "completion_pct": "0.7"},
    )

    profile = (await student_client.get(PROFILE)).json()
    completion = profile["discovery_completion"]
    assert completion["goals"] == pytest.approx(0.7, abs=0.01)
    assert completion["needs"] == 0
    assert completion["profile"] == 0
    assert completion["identity"] == 0


@pytest.mark.asyncio
async def test_identity_layer_lifts_identity_dimension(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """Completing a profile/identity session should bump the 'identity'
    dimension (separate from the 'profile' track total)."""
    await _ensure_profile(db_session, mock_student_user)
    s = (
        await student_client.post(
            f"{DISC}/sessions", json={"track": "profile", "layer": "identity"}
        )
    ).json()
    await student_client.patch(
        f"{DISC}/sessions/{s['id']}",
        json={"status": "completed", "completion_pct": "1"},
    )
    profile = (await student_client.get(PROFILE)).json()
    completion = profile["discovery_completion"]
    assert completion["profile"] == pytest.approx(1.0, abs=0.01)
    assert completion["identity"] == pytest.approx(1.0, abs=0.01)


@pytest.mark.asyncio
async def test_completion_does_not_update_for_status_changes_other_than_completed(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """A draft → abandoned transition should NOT update the summary; we
    only care about completed sessions in the dimension max."""
    await _ensure_profile(db_session, mock_student_user)
    s = (await student_client.post(f"{DISC}/sessions", json={"track": "goals"})).json()
    await student_client.patch(
        f"{DISC}/sessions/{s['id']}",
        json={"status": "abandoned", "completion_pct": "0.5"},
    )
    profile = (await student_client.get(PROFILE)).json()
    completion = profile["discovery_completion"]
    # No completed sessions → goals dimension is still 0 (or absent).
    assert completion.get("goals", 0) == 0


# ── strategy_active_id auto-update ────────────────────────────────────────


@pytest.mark.asyncio
async def test_strategy_active_id_starts_null(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    profile = (await student_client.get(PROFILE)).json()
    assert profile["strategy_active_id"] is None


@pytest.mark.asyncio
async def test_strategy_active_id_set_on_activate(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    # Need an active academic goal to generate a strategy.
    await student_client.post(
        GOALS, json={"category": "academic", "specific": "Become a physician."}
    )
    s = (await student_client.post(f"{STRAT}/generate")).json()
    await student_client.post(f"{STRAT}/{s['id']}/activate")

    profile = (await student_client.get(PROFILE)).json()
    assert profile["strategy_active_id"] == s["id"]


@pytest.mark.asyncio
async def test_strategy_active_id_clears_when_active_archived_via_edit(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """Editing an active strategy archives it (clone-and-modify) and
    creates a NEW draft — the new draft is NOT auto-activated, so the
    profile's strategy_active_id should clear."""
    await _ensure_profile(db_session, mock_student_user)
    await student_client.post(
        GOALS, json={"category": "academic", "specific": "Become a physician."}
    )
    s = (await student_client.post(f"{STRAT}/generate")).json()
    await student_client.post(f"{STRAT}/{s['id']}/activate")
    # Confirm pre-state
    assert (await student_client.get(PROFILE)).json()["strategy_active_id"] == s["id"]

    # Edit the active row → archives it, creates new draft. No active.
    await student_client.patch(f"{STRAT}/{s['id']}", json={"narrative": "manual override"})
    profile = (await student_client.get(PROFILE)).json()
    assert profile["strategy_active_id"] is None


@pytest.mark.asyncio
async def test_strategy_active_id_repoints_when_swapping_active(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """Activating a NEW strategy should archive the previous active AND
    re-point the profile pointer."""
    await _ensure_profile(db_session, mock_student_user)
    await student_client.post(
        GOALS, json={"category": "academic", "specific": "Become a physician."}
    )
    a = (await student_client.post(f"{STRAT}/generate")).json()
    b = (await student_client.post(f"{STRAT}/generate")).json()

    await student_client.post(f"{STRAT}/{a['id']}/activate")
    assert (await student_client.get(PROFILE)).json()["strategy_active_id"] == a["id"]

    await student_client.post(f"{STRAT}/{b['id']}/activate")
    assert (await student_client.get(PROFILE)).json()["strategy_active_id"] == b["id"]
