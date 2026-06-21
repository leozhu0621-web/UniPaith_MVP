"""Tests for the Carnegie classification -> ref_institutions enrichment."""

from __future__ import annotations

import pytest
from sqlalchemy import select, update

from unipaith.models import RefInstitution
from unipaith.services.reference_carnegie_ingest import carnegie_from_row, upsert_carnegie
from unipaith.services.reference_ingest import upsert_institutions


async def _by_unitid(db, unitid):
    return (await db.scalars(select(RefInstitution).where(RefInstitution.unitid == unitid))).one()


def test_carnegie_from_row():
    rec = carnegie_from_row(
        {
            "unitid": "166027",
            "research2025name": "Research 1: Very High Spending and Doctorate Production",
            "ic2025name": "Research University",
            "saec2025name": "Higher Access, Higher Earnings",
        }
    )
    assert rec["unitid"] == 166027
    assert rec["carnegie"]["research"].startswith("Research 1")
    assert rec["carnegie"]["access_earnings"] == "Higher Access, Higher Earnings"
    # no unitid -> None; no labels -> None
    assert carnegie_from_row({"unitid": "x"}) is None
    assert carnegie_from_row({"unitid": "1"}) is None


@pytest.mark.asyncio
async def test_upsert_carnegie_merges_into_extra(db_session):
    await upsert_institutions(
        db_session,
        [
            {"unitid": 166027, "name": "Harvard University", "state": "MA"},
        ],
    )
    # a pre-existing sibling key in extra must survive the merge
    await db_session.execute(
        update(RefInstitution).where(RefInstitution.unitid == 166027).values(extra={"keep": 1})
    )
    await db_session.commit()

    linked = await upsert_carnegie(
        db_session,
        [
            {
                "unitid": 166027,
                "carnegie": {"research": "Research 1", "classification": "Research University"},
            },
            {"unitid": 999999, "carnegie": {"research": "x"}},  # absent -> skipped
        ],
    )
    assert linked == 1

    db_session.expire_all()
    row = await _by_unitid(db_session, 166027)
    assert row.extra["carnegie"]["research"] == "Research 1"
    assert row.extra["keep"] == 1  # sibling preserved


@pytest.mark.asyncio
async def test_api_detail_includes_carnegie(client, db_session):
    await upsert_institutions(db_session, [{"unitid": 166027, "name": "Harvard University"}])
    await upsert_carnegie(
        db_session,
        [
            {
                "unitid": 166027,
                "carnegie": {"research": "Research 1", "access_earnings": "Higher/Higher"},
            },
        ],
    )
    r = await client.get("/api/v1/reference/institutions/166027")
    assert r.status_code == 200
    assert r.json()["carnegie"]["research"] == "Research 1"
