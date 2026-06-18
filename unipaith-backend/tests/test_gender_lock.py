"""Gender 3-month (90-day) change-lock — Spec 2026-06-18 basic-info demographics.

Covers StudentService.update_profile enforcement via the PUT profile endpoint:
  (a) first set stamps gender_identity_updated_at and succeeds;
  (b) changing gender when the last change was < 90 days ago → 422;
  (c) changing gender when the last change was >= 90 days ago → succeeds + re-stamps;
  (d) editing a non-gender field while gender is unchanged → allowed, timestamp untouched.
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.student import StudentProfile
from unipaith.models.user import User

PROFILE_URL = "/api/v1/students/me/profile"


async def _ensure_profile(db: AsyncSession, user: User) -> None:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()


async def _get_profile(db: AsyncSession, user: User) -> StudentProfile:
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user.id))
    return result.scalar_one()


async def _set_gender_stamp(db: AsyncSession, user: User, stamp: datetime | None) -> None:
    """Backdate (or clear) the stored gender_identity_updated_at directly, so the
    lock window can be exercised without sleeping. Expire so the next request,
    sharing this session, re-reads the committed value."""
    profile = await _get_profile(db, user)
    profile.gender_identity_updated_at = stamp
    await db.commit()
    db.expire_all()


@pytest.mark.asyncio
async def test_first_set_stamps_and_succeeds(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    before = datetime.now(UTC)

    resp = await student_client.put(PROFILE_URL, json={"gender_identity": "Woman"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["gender_identity"] == "Woman"
    # First set stamps the timestamp (was null).
    assert body["gender_identity_updated_at"] is not None
    stamped = datetime.fromisoformat(body["gender_identity_updated_at"])
    assert stamped >= before


@pytest.mark.asyncio
async def test_change_within_90_days_is_rejected(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    # First set: allowed, stamps "now".
    first = await student_client.put(PROFILE_URL, json={"gender_identity": "Woman"})
    assert first.status_code == 200

    # Backdate the stamp to 30 days ago — still inside the 90-day lock.
    await _set_gender_stamp(db_session, mock_student_user, datetime.now(UTC) - timedelta(days=30))

    resp = await student_client.put(PROFILE_URL, json={"gender_identity": "Man"})

    assert resp.status_code == 422
    assert "once every 3 months" in resp.json()["detail"]
    # Value did not change.
    profile = await _get_profile(db_session, mock_student_user)
    assert profile.gender_identity == "Woman"


@pytest.mark.asyncio
async def test_change_after_90_days_succeeds_and_restamps(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    first = await student_client.put(PROFILE_URL, json={"gender_identity": "Woman"})
    assert first.status_code == 200

    # Backdate the stamp to 100 days ago — outside the 90-day lock.
    old_stamp = datetime.now(UTC) - timedelta(days=100)
    await _set_gender_stamp(db_session, mock_student_user, old_stamp)

    resp = await student_client.put(PROFILE_URL, json={"gender_identity": "Non-binary"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["gender_identity"] == "Non-binary"
    # Re-stamped to ~now, strictly newer than the backdated stamp.
    new_stamp = datetime.fromisoformat(body["gender_identity_updated_at"])
    assert new_stamp > old_stamp


@pytest.mark.asyncio
async def test_other_field_edit_does_not_touch_gender_stamp(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    first = await student_client.put(PROFILE_URL, json={"gender_identity": "Woman"})
    assert first.status_code == 200
    locked_stamp = first.json()["gender_identity_updated_at"]
    assert locked_stamp is not None

    # Backdate well inside the lock window — proves a non-gender edit is NOT
    # blocked by the lock and does NOT re-stamp.
    await _set_gender_stamp(db_session, mock_student_user, datetime.now(UTC) - timedelta(days=1))
    stamp_before = (await _get_profile(db_session, mock_student_user)).gender_identity_updated_at

    resp = await student_client.put(PROFILE_URL, json={"first_name": "Alice"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["first_name"] == "Alice"
    assert body["gender_identity"] == "Woman"
    # Timestamp untouched by the non-gender edit.
    assert (
        await _get_profile(db_session, mock_student_user)
    ).gender_identity_updated_at == stamp_before


@pytest.mark.asyncio
async def test_resending_same_gender_does_not_block_or_restamp(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """Re-sending the unchanged gender value inside the lock window is a no-op:
    never blocks, never re-stamps."""
    await _ensure_profile(db_session, mock_student_user)
    first = await student_client.put(PROFILE_URL, json={"gender_identity": "Woman"})
    assert first.status_code == 200

    await _set_gender_stamp(db_session, mock_student_user, datetime.now(UTC) - timedelta(days=10))
    stamp_before = (await _get_profile(db_session, mock_student_user)).gender_identity_updated_at

    resp = await student_client.put(PROFILE_URL, json={"gender_identity": "Woman"})

    assert resp.status_code == 200
    assert (
        await _get_profile(db_session, mock_student_user)
    ).gender_identity_updated_at == stamp_before
