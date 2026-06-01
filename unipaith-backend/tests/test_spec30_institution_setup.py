"""Spec 30 — Institution Setup (first-run wizard): backend contract tests.

Covers the acceptance checks in Spec 30 §10:
- new account is forced into setup until profile + program exist;
- each step persists independently and resume returns the last step;
- skipping optional steps (data/team) still allows finishing;
- `setup_complete` flips once the minimum is met;
- team invites are audit-logged;
- the endpoints never 5xx on bad input (validation / 4xx fallback).
"""

from __future__ import annotations

from sqlalchemy import select

from unipaith.models.audit import AdmissionsAuditLog
from unipaith.models.institution import Institution

API = "/api/v1"


async def _make_institution(db_session, user, *, description: str | None = None) -> Institution:
    inst = Institution(
        admin_user_id=user.id,
        name="Test University",
        type="university",
        country="US",
        website_url="https://www.testu.edu",
        description_text=description,
    )
    db_session.add(inst)
    await db_session.flush()
    return inst


async def _add_program(institution_client) -> str:
    r = await institution_client.post(
        f"{API}/institutions/me/programs",
        json={"program_name": "BSc Computer Science", "degree_type": "bachelors"},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


# ── State + resume ───────────────────────────────────────────────────────────


async def test_setup_state_before_institution_exists(institution_client):
    """A freshly-invited admin with no institution row gets a clean Step-1 state
    (no 5xx) so the wizard can render and Step 1 can create the institution."""
    r = await institution_client.get(f"{API}/institutions/me/setup")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["institution_id"] is None
    assert body["step"] == 1
    assert body["setup_complete"] is False
    assert body["steps_complete"] == {
        "profile": False,
        "program": False,
        "data": False,
        "team": False,
    }


async def test_steps_complete_derive_from_real_data(
    institution_client, db_session, mock_institution_user
):
    # Institution with name/type/country but NO description → profile incomplete.
    await _make_institution(db_session, mock_institution_user)
    body = (await institution_client.get(f"{API}/institutions/me/setup")).json()
    assert body["steps_complete"]["profile"] is False
    assert body["institution_id"] is not None

    # Filling the description (via the profile editor) satisfies the profile step.
    r = await institution_client.put(
        f"{API}/institutions/me", json={"description_text": "A great place to learn."}
    )
    assert r.status_code == 200, r.text
    body = (await institution_client.get(f"{API}/institutions/me/setup")).json()
    assert body["steps_complete"]["profile"] is True
    assert body["steps_complete"]["program"] is False

    # Adding a program satisfies the program step + records first_program_id.
    program_id = await _add_program(institution_client)
    body = (await institution_client.get(f"{API}/institutions/me/setup")).json()
    assert body["steps_complete"]["program"] is True
    assert body["first_program_id"] == program_id


async def test_step_persists_independently_and_resumes(
    institution_client, db_session, mock_institution_user
):
    await _make_institution(db_session, mock_institution_user)
    # Navigate to step 2 and skip the optional data step.
    r = await institution_client.patch(
        f"{API}/institutions/me/setup/step", json={"step": 2, "skip_data": True}
    )
    assert r.status_code == 200, r.text
    # Re-fetching resumes at the last navigated step with prior input intact.
    body = (await institution_client.get(f"{API}/institutions/me/setup")).json()
    assert body["step"] == 2
    assert body["skipped"]["data"] is True
    assert body["skipped"]["team"] is False


# ── Completion gating ────────────────────────────────────────────────────────


async def test_complete_blocked_until_profile_and_program(
    institution_client, db_session, mock_institution_user
):
    await _make_institution(db_session, mock_institution_user)  # no description, no program

    # No profile description, no program → cannot finish.
    r = await institution_client.post(f"{API}/institutions/me/setup/complete")
    assert r.status_code == 400, r.text

    # Add profile but still no program → still blocked.
    await institution_client.put(
        f"{API}/institutions/me", json={"description_text": "We teach things."}
    )
    r = await institution_client.post(f"{API}/institutions/me/setup/complete")
    assert r.status_code == 400, r.text

    # Add a program → minimum met → finish succeeds and flips the flag.
    await _add_program(institution_client)
    r = await institution_client.post(f"{API}/institutions/me/setup/complete")
    assert r.status_code == 200, r.text
    assert r.json()["setup_complete"] is True
    assert r.json()["step"] == "done"

    # Persisted: a fresh GET shows setup_complete + done.
    body = (await institution_client.get(f"{API}/institutions/me/setup")).json()
    assert body["setup_complete"] is True
    assert body["step"] == "done"


async def test_skip_optional_steps_then_finish(
    institution_client, db_session, mock_institution_user
):
    await _make_institution(db_session, mock_institution_user, description="Learn here.")
    await _add_program(institution_client)

    # Skip data + team — both optional — and finish.
    await institution_client.patch(
        f"{API}/institutions/me/setup/step", json={"skip_data": True, "skip_team": True}
    )
    r = await institution_client.post(f"{API}/institutions/me/setup/complete")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["setup_complete"] is True
    # Optional steps register as complete via the skip flags.
    assert body["steps_complete"]["data"] is True
    assert body["steps_complete"]["team"] is True


# ── Team invite audit (Spec 30 §10 / Spec 36) ────────────────────────────────


async def test_team_invite_is_audit_logged(institution_client, db_session, mock_institution_user):
    inst = await _make_institution(db_session, mock_institution_user)

    inv = await institution_client.post(
        f"{API}/institutions/settings/team/invite",
        json={"email": "recruiter@testu.edu", "role": "recruiter"},
    )
    assert inv.status_code == 200, inv.text

    rows = (
        (
            await db_session.execute(
                select(AdmissionsAuditLog).where(
                    AdmissionsAuditLog.institution_id == inst.id,
                    AdmissionsAuditLog.action == "team.invite",
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].entity_type == "team_invite"
    assert rows[0].actor_user_id == mock_institution_user.id


# ── No-5xx invariant ─────────────────────────────────────────────────────────


async def test_invalid_step_is_422_not_5xx(institution_client, db_session, mock_institution_user):
    await _make_institution(db_session, mock_institution_user)
    r = await institution_client.patch(f"{API}/institutions/me/setup/step", json={"step": 9})
    assert r.status_code == 422, r.text


async def test_complete_without_institution_is_4xx_not_5xx(institution_client):
    r = await institution_client.post(f"{API}/institutions/me/setup/complete")
    assert r.status_code < 500, r.text
    assert r.status_code in (400, 404)
