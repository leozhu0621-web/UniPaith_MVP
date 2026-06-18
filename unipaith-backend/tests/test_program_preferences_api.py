"""Slice D.3 — institution ProgramPreference editor API (Spec 2/3)."""

import uuid

import pytest

from unipaith.models.institution import Institution, Program


async def _make_program(db_session, user) -> Program:
    inst = Institution(
        admin_user_id=user.id, name="Test University", type="university", country="USA"
    )
    db_session.add(inst)
    await db_session.flush()
    prog = Program(institution_id=inst.id, program_name="MS in Data Science", degree_type="masters")
    db_session.add(prog)
    await db_session.flush()
    return prog


def _url(pid) -> str:
    return f"/api/v1/institutions/me/programs/{pid}/preferences"


@pytest.mark.asyncio
async def test_put_then_get_preferences(institution_client, db_session, mock_institution_user):
    prog = await _make_program(db_session, mock_institution_user)
    payload = {
        "pref_min_gpa": 3.6,
        "pref_fields": ["data_science", "statistics"],
        "pref_levels": ["bachelors"],
        "weight_academic": 8,
    }
    r = await institution_client.put(_url(prog.id), json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["source"] == "claimed"  # first-party
    assert body["pref_min_gpa"] == 3.6
    assert body["pref_fields"] == ["data_science", "statistics"]
    assert body["weight_academic"] == 8

    g = await institution_client.get(_url(prog.id))
    assert g.status_code == 200, g.text
    assert g.json()["pref_min_gpa"] == 3.6


@pytest.mark.asyncio
async def test_get_preferences_empty_when_unset(
    institution_client, db_session, mock_institution_user
):
    prog = await _make_program(db_session, mock_institution_user)
    g = await institution_client.get(_url(prog.id))
    assert g.status_code == 200, g.text
    assert g.json() is None  # no preferences yet


@pytest.mark.asyncio
async def test_cannot_edit_unowned_program(institution_client, db_session, mock_institution_user):
    # the caller has an institution + program, but PUTs to a foreign program id
    await _make_program(db_session, mock_institution_user)
    r = await institution_client.put(_url(uuid.uuid4()), json={"pref_min_gpa": 3.0})
    assert r.status_code == 404, r.text
