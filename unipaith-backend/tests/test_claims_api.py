"""Slice D.1 — claim hinge (Spec 2)."""

import uuid

import pytest

from unipaith.models.institution import Institution, Program

CLAIMS = "/api/v1/institutions/me/claims"


async def _make_institution(db_session, user) -> Institution:
    inst = Institution(
        admin_user_id=user.id, name="Test University", type="university", country="USA"
    )
    db_session.add(inst)
    await db_session.flush()
    return inst


@pytest.mark.asyncio
async def test_claim_marks_owned_program(institution_client, db_session, mock_institution_user):
    inst = await _make_institution(db_session, mock_institution_user)
    prog = Program(
        institution_id=inst.id, program_name="Bachelor of Science in CS", degree_type="bachelors"
    )
    db_session.add(prog)
    await db_session.flush()

    r = await institution_client.post(CLAIMS, json={"program_ids": [str(prog.id)]})
    assert r.status_code == 200, r.text
    assert r.json()["claimed"]["programs"] == 1

    await db_session.refresh(prog)
    assert prog.is_claimed is True
    assert str(prog.claimed_by_user_id) == str(mock_institution_user.id)
    assert prog.claimed_at is not None


@pytest.mark.asyncio
async def test_claim_nonexistent_program_is_noop(
    institution_client, db_session, mock_institution_user
):
    await _make_institution(db_session, mock_institution_user)
    r = await institution_client.post(CLAIMS, json={"program_ids": [str(uuid.uuid4())]})
    assert r.status_code == 200, r.text
    assert r.json()["claimed"]["programs"] == 0
