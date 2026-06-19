"""Spec 1 enrichment write-typing — weight scaling + taxonomy validation.

Backend-alignment fix (2026-06-19 audit, gap #1/#2): the enrichment value path
must (a) scale a 0-5 weight to 0-10 and project it onto StudentPreference (the
column the matcher reads), and (b) reject categorical/multi values that are not
in the field's CATALOG taxonomy.
"""

import pytest
from sqlalchemy import select

from tests._uni_helpers import ensure_profile
from unipaith.models.student import StudentPreference
from unipaith.services.intake.intake_engine_service import IntakeEngineService

BASE = "/api/v1/students/me/enrichment"


async def _preference(db, user):
    pid = await IntakeEngineService(db).profile_id_for_user(user.id)
    db.expire_all()
    return (
        await db.execute(select(StudentPreference).where(StudentPreference.student_id == pid))
    ).scalar_one_or_none()


@pytest.mark.asyncio
async def test_weight_scales_0_5_to_0_10_on_preference(
    student_client, db_session, mock_student_user
):
    """A 0-5 importance weight is stored 0-10 on StudentPreference (matcher reads this)."""
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.post(f"{BASE}/weight_cost/value", json={"value": 4})
    assert r.status_code == 200, r.text
    pref = await _preference(db_session, mock_student_user)
    assert pref is not None, "a weight write must create/find the StudentPreference row"
    assert pref.weight_cost == 8, "weight 4 (0-5) must project as 8 (0-10) onto StudentPreference"


@pytest.mark.asyncio
async def test_weight_out_of_range_rejected(student_client, db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.post(f"{BASE}/weight_location/value", json={"value": 9})
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_weight_non_numeric_rejected(student_client, db_session, mock_student_user):
    """The old scale widget submitted a phrase ('essential') — that must now be rejected."""
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.post(f"{BASE}/weight_support/value", json={"value": "essential"})
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_categorical_out_of_taxonomy_rejected(student_client, db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.post(f"{BASE}/gender/value", json={"value": "female"})
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_categorical_in_taxonomy_accepted(student_client, db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.post(f"{BASE}/gender/value", json={"value": "Woman"})
    assert r.status_code == 200, r.text


@pytest.mark.asyncio
async def test_multi_out_of_taxonomy_rejected(student_client, db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.post(f"{BASE}/needs/value", json={"value": ["not_a_real_need"]})
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_free_text_categorical_not_taxonomy_checked(
    student_client, db_session, mock_student_user
):
    """nationality/country are categorical with NO options (free text) — must still accept."""
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.post(f"{BASE}/nationality/value", json={"value": "Canada"})
    assert r.status_code == 200, r.text
