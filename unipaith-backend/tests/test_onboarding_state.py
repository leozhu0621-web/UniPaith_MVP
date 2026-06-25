"""Ship C — student_profiles.onboarding_state persistence.

Covers the fixed API contract for the Imprint-style onboarding wizard:
PATCH /students/me/onboarding/state merges answers key-wise, stamps
completed_at/dismissed_at exactly once (idempotent), is student-only, and
the student profile response exposes onboarding_state. On first completion
the answers fan into StudentPreference (fill-only-if-empty) and one manual
student_goals row.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.goals import StudentGoal
from unipaith.models.student import StudentPreference, StudentProfile
from unipaith.models.user import User

STATE_URL = "/api/v1/students/me/onboarding/state"
PROFILE_URL = "/api/v1/students/me/profile"


async def _ensure_profile(db: AsyncSession, user: User) -> StudentProfile:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile


# --- PATCH merge semantics ---


@pytest.mark.asyncio
async def test_patch_merges_answers_key_wise(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)

    resp = await student_client.patch(
        STATE_URL,
        json={"answers": {"stage": "exploring", "interests": ["cs"]}, "last_step": 1},
    )
    assert resp.status_code == 200
    state = resp.json()
    assert state["answers"] == {"stage": "exploring", "interests": ["cs"]}
    assert state["last_step"] == 1
    assert state["completed_at"] is None
    assert state["dismissed_at"] is None

    # A later step adds keys without clobbering earlier answers.
    resp = await student_client.patch(
        STATE_URL,
        json={"answers": {"degree_level": "masters"}, "last_step": 2},
    )
    assert resp.status_code == 200
    state = resp.json()
    assert state["answers"]["stage"] == "exploring"
    assert state["answers"]["interests"] == ["cs"]
    assert state["answers"]["degree_level"] == "masters"
    assert state["last_step"] == 2

    # Re-answering an existing key overwrites just that key.
    resp = await student_client.patch(STATE_URL, json={"answers": {"stage": "building_list"}})
    state = resp.json()
    assert state["answers"]["stage"] == "building_list"
    assert state["answers"]["degree_level"] == "masters"
    # last_step untouched when not sent.
    assert state["last_step"] == 2


@pytest.mark.asyncio
async def test_patch_rejects_invalid_enum_values(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.patch(STATE_URL, json={"answers": {"stage": "vibing"}})
    assert resp.status_code == 422
    resp = await student_client.patch(STATE_URL, json={"answers": {"budget_band": "1_dollar"}})
    assert resp.status_code == 422


# --- completion / dismissal stamps ---


@pytest.mark.asyncio
async def test_completed_stamp_is_idempotent(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)

    resp = await student_client.patch(STATE_URL, json={"completed": True})
    assert resp.status_code == 200
    first_stamp = resp.json()["completed_at"]
    assert first_stamp is not None

    # Replaying completed=True never overwrites the original stamp.
    resp = await student_client.patch(STATE_URL, json={"completed": True})
    assert resp.status_code == 200
    assert resp.json()["completed_at"] == first_stamp

    # And a fan-in side effect does not replay either: still at most one goal.
    goals = (
        (await db_session.execute(select(StudentGoal).where(StudentGoal.source == "manual")))
        .scalars()
        .all()
    )
    assert len(goals) <= 1


@pytest.mark.asyncio
async def test_dismissed_stamp_is_idempotent(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)

    resp = await student_client.patch(STATE_URL, json={"dismissed": True})
    assert resp.status_code == 200
    first_stamp = resp.json()["dismissed_at"]
    assert first_stamp is not None
    assert resp.json()["completed_at"] is None

    resp = await student_client.patch(STATE_URL, json={"dismissed": True})
    assert resp.json()["dismissed_at"] == first_stamp


@pytest.mark.asyncio
async def test_completed_false_does_not_stamp(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.patch(STATE_URL, json={"completed": False, "dismissed": False})
    assert resp.status_code == 200
    assert resp.json()["completed_at"] is None
    assert resp.json()["dismissed_at"] is None


# --- role guard ---


@pytest.mark.asyncio
async def test_patch_403_for_institution_admin(institution_client: AsyncClient):
    resp = await institution_client.patch(STATE_URL, json={"completed": True})
    assert resp.status_code == 403


# --- profile response exposes the field ---


@pytest.mark.asyncio
async def test_profile_response_exposes_onboarding_state(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)

    resp = await student_client.get(PROFILE_URL)
    assert resp.status_code == 200
    assert "onboarding_state" in resp.json()
    assert resp.json()["onboarding_state"] is None

    await student_client.patch(STATE_URL, json={"answers": {"degree_level": "phd"}, "last_step": 3})
    resp = await student_client.get(PROFILE_URL)
    state = resp.json()["onboarding_state"]
    assert state["answers"]["degree_level"] == "phd"
    assert state["last_step"] == 3
    assert state.get("completed_at") is None


# --- fan-in on completion ---


@pytest.mark.asyncio
async def test_completion_fans_into_preferences_and_goals(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)

    await student_client.patch(
        STATE_URL,
        json={
            "answers": {
                "degree_level": "masters",
                "intake_term": "Fall 2027",
                "budget_band": "20k_40k",
                "geos": ["United States", "Canada"],
            }
        },
    )
    resp = await student_client.patch(STATE_URL, json={"completed": True})
    assert resp.status_code == 200
    assert resp.json()["completed_at"] is not None

    pref = (await db_session.execute(select(StudentPreference))).scalar_one()
    assert pref.target_degree_level == "masters"
    assert pref.target_start_term == "Fall 2027"
    assert pref.preferred_regions == ["United States", "Canada"]
    assert pref.budget_min == 20_000
    assert pref.budget_max == 40_000

    goal = (await db_session.execute(select(StudentGoal))).scalar_one()
    assert goal.source == "manual"
    assert goal.source_session_id is None
    assert goal.category == "academic"
    assert "master's" in goal.specific
    assert "Fall 2027" in goal.specific


@pytest.mark.asyncio
async def test_fan_in_never_overwrites_existing_preferences(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    profile = await _ensure_profile(db_session, mock_student_user)
    db_session.add(
        StudentPreference(
            student_id=profile.id,
            target_degree_level="phd",
            budget_min=50_000,
            budget_max=80_000,
        )
    )
    await db_session.commit()

    await student_client.patch(
        STATE_URL,
        json={"answers": {"degree_level": "masters", "budget_band": "lt_20k"}, "completed": True},
    )

    pref = (await db_session.execute(select(StudentPreference))).scalar_one()
    assert pref.target_degree_level == "phd"  # student's own value wins
    assert pref.budget_min == 50_000
    assert pref.budget_max == 80_000


@pytest.mark.asyncio
async def test_budget_fans_in_without_completion(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """A budget chosen in setup persists to StudentPreference immediately — not
    only on the final completion stamp — so Costs & Aid + the program net-price
    estimator read it instead of telling the student to "add a budget" she set.
    A later band change updates the band-derived budget."""
    await _ensure_profile(db_session, mock_student_user)

    resp = await student_client.patch(STATE_URL, json={"answers": {"budget_band": "40k_60k"}})
    assert resp.status_code == 200
    assert resp.json()["completed_at"] is None  # NOT completed — the durability fix

    # Column-level select → plain tuple, fresh from the DB (no ORM identity cache).
    budget = (
        await db_session.execute(select(StudentPreference.budget_min, StudentPreference.budget_max))
    ).one()
    assert budget == (40_000, 60_000)

    # Changing the band updates the band-derived budget (not a hand-set one).
    await student_client.patch(STATE_URL, json={"answers": {"budget_band": "60k_plus"}})
    budget = (
        await db_session.execute(select(StudentPreference.budget_min, StudentPreference.budget_max))
    ).one()
    assert budget == (60_000, None)


@pytest.mark.asyncio
async def test_completion_with_no_mappable_answers_skips_fan_in(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.patch(
        STATE_URL, json={"answers": {"stage": "exploring"}, "completed": True}
    )
    assert resp.status_code == 200
    assert resp.json()["completed_at"] is not None

    assert (await db_session.execute(select(StudentPreference))).scalar_one_or_none() is None
    assert (await db_session.execute(select(StudentGoal))).scalar_one_or_none() is None
