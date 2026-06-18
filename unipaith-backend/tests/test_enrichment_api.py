"""Slice C.2 — enrichment API integration (Spec 1)."""

import pytest

from tests._uni_helpers import ensure_profile

BASE = "/api/v1/students/me/enrichment"


@pytest.mark.asyncio
async def test_next_returns_plan_and_essentials_flag(student_client, db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.get(f"{BASE}/next")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "items" in body and "essentials_present" in body
    assert isinstance(body["items"], list)
    # a fresh student has no essentials yet → planner asks essentials first
    assert body["essentials_present"] is False
    assert body["items"], "planner should surface at least one signal to enrich"
    assert body["items"][0]["tier"] == "essential"


@pytest.mark.asyncio
async def test_set_value_round_trips(student_client, db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    first = (await student_client.get(f"{BASE}/next")).json()["items"][0]
    field = first["field"]
    s = await student_client.post(f"{BASE}/{field}/value", json={"value": "female"})
    assert s.status_code == 200, s.text
    # after setting it, the same field is no longer the top "ask" (it now has a value)
    after = (await student_client.get(f"{BASE}/next?limit=20")).json()
    asked_now = [i for i in after["items"] if i["field"] == field and i["action"] == "ask"]
    assert not asked_now, "a field with a stored value must not still be an ASK"


@pytest.mark.asyncio
async def test_unknown_field_rejected(student_client, db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.post(f"{BASE}/not_a_real_field/value", json={"value": "x"})
    assert r.status_code == 400, r.text
