"""Spec 30 — Institution setup wizard contract tests."""

from __future__ import annotations

from sqlalchemy import select

from unipaith.models.institution import Institution
from unipaith.models.settings import InstitutionTeamInvite

API = "/api/v1"


async def _create_institution(client, name: str = "Test University") -> dict:
    r = await client.post(
        f"{API}/institutions/me",
        json={
            "name": name,
            "type": "university",
            "country": "United States",
            "city": "Boston",
            "website_url": "https://testu.edu",
            "description_text": "A test institution.",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _create_program(client, name: str = "MBA") -> dict:
    r = await client.post(
        f"{API}/institutions/me/programs",
        json={
            "program_name": name,
            "degree_type": "masters",
            "delivery_format": "hybrid",
            "application_deadline": "2026-12-01",
            "tuition": 45000,
            "description_text": "First program.",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


async def test_fresh_invite_setup_state(institution_client):
    r = await institution_client.get(f"{API}/institutions/me/setup")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["institution_id"] is None
    assert body["step"] == 1
    assert body["setup_complete"] is False
    assert body["steps_complete"]["profile"] is False


async def test_profile_step_persists_and_resumes(
    institution_client, db_session, mock_institution_user
):
    await _create_institution(institution_client)

    r = await institution_client.get(f"{API}/institutions/me/setup")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["steps_complete"]["profile"] is True
    assert body["step"] == 2

    inst = (
        await db_session.execute(
            select(Institution).where(Institution.admin_user_id == mock_institution_user.id)
        )
    ).scalar_one()
    assert inst.setup_steps_complete["profile"] is True
    assert inst.setup_step == 2


async def test_program_step_then_skip_optional_and_complete(institution_client):
    await _create_institution(institution_client)
    prog = await _create_program(institution_client)

    r = await institution_client.get(f"{API}/institutions/me/setup")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["steps_complete"]["program"] is True
    assert body["first_program_id"] == prog["id"]
    assert body["setup_complete"] is False

    complete = await institution_client.post(f"{API}/institutions/me/setup/complete")
    assert complete.status_code == 200, complete.text
    done = complete.json()
    assert done["setup_complete"] is True
    assert done["steps_complete"]["data"] is False
    assert done["steps_complete"]["team"] is False


async def test_cannot_complete_without_program(institution_client):
    await _create_institution(institution_client)
    r = await institution_client.post(f"{API}/institutions/me/setup/complete")
    assert r.status_code == 400


async def test_patch_setup_step_advances(institution_client):
    await _create_institution(institution_client)
    await _create_program(institution_client)

    r = await institution_client.patch(
        f"{API}/institutions/me/setup/step",
        json={"step": 4},
    )
    assert r.status_code == 200, r.text
    assert r.json()["step"] == 4


async def test_team_invite_marks_team_step(institution_client, db_session, mock_institution_user):
    await _create_institution(institution_client)
    await _create_program(institution_client)

    invite = await institution_client.post(
        f"{API}/institutions/settings/team/invite",
        json={"email": "colleague@testu.edu", "role": "admissions"},
    )
    assert invite.status_code == 200, invite.text

    setup = await institution_client.get(f"{API}/institutions/me/setup")
    assert setup.json()["steps_complete"]["team"] is True

    inst = (
        await db_session.execute(
            select(Institution).where(Institution.admin_user_id == mock_institution_user.id)
        )
    ).scalar_one()
    invites = (
        (
            await db_session.execute(
                select(InstitutionTeamInvite).where(InstitutionTeamInvite.institution_id == inst.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(invites) == 1


async def test_institution_response_includes_setup_fields(institution_client):
    await _create_institution(institution_client)
    r = await institution_client.get(f"{API}/institutions/me")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "setup_complete" in body
    assert body["setup_complete"] is False
    assert body["setup_step"] == 2
