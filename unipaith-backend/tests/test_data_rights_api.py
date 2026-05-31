"""Data Rights tab — consent levers (incl. the training lever), the per-lever
change log, and the access log (spec 10 §16 / 43 §2, §8)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.student import StudentProfile
from unipaith.models.user import User

RIGHTS = "/api/v1/students/me/data-rights"
ACCESS = "/api/v1/students/me/access-log"


async def _ensure_profile(db: AsyncSession, user: User) -> StudentProfile:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile


@pytest.mark.asyncio
async def test_data_rights_get_none_before_set(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.get(RIGHTS)
    assert resp.status_code == 200
    assert resp.json() is None


@pytest.mark.asyncio
async def test_consent_training_lever_persists(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """The 4th consent lever (spec §22.7) round-trips through PUT and GET."""
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.put(RIGHTS, json={"consent_training": True})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["consent_training"] is True
    for lever in ("consent_matching", "consent_outreach", "consent_research"):
        assert lever in data
    again = (await student_client.get(RIGHTS)).json()
    assert again["consent_training"] is True


@pytest.mark.asyncio
async def test_consent_default_training_false(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """Training is opt-in — defaults False even when other levers are set."""
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.put(RIGHTS, json={"consent_matching": True})
    assert resp.json()["consent_training"] is False


@pytest.mark.asyncio
async def test_consent_change_log_records_toggles(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """Each real lever change is appended to consent_change_log (spec §16
    'Last changed' + history)."""
    await _ensure_profile(db_session, mock_student_user)
    await student_client.put(RIGHTS, json={"consent_training": True})
    resp = await student_client.put(RIGHTS, json={"consent_outreach": False})
    log = resp.json()["consent_change_log"] or []
    levers_logged = {entry["lever"] for entry in log}
    assert "consent_training" in levers_logged
    assert "consent_outreach" in levers_logged
    assert all("value" in e and "at" in e for e in log)


@pytest.mark.asyncio
async def test_deletion_request_sets_grace_timestamp(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """Requesting deletion stamps the timestamp that anchors the 30-day grace."""
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.put(RIGHTS, json={"deletion_requested": True})
    data = resp.json()
    assert data["deletion_requested"] is True
    assert data["deletion_requested_at"] is not None
    # Reversible: clearing it drops the timestamp.
    cleared = (await student_client.put(RIGHTS, json={"deletion_requested": False})).json()
    assert cleared["deletion_requested"] is False
    assert cleared["deletion_requested_at"] is None


@pytest.mark.asyncio
async def test_access_log_empty_for_new_student(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.get(ACCESS)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_data_rights_blocked_for_non_students(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    db_session.add(mock_institution_user)
    await db_session.commit()
    resp = await institution_client.get(RIGHTS)
    assert resp.status_code == 403
