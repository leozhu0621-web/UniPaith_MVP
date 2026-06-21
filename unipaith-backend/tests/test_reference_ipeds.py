"""Tests for the IPEDS admissions -> ref_institutions enrichment."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from unipaith.models import RefInstitution
from unipaith.services.reference_ingest import upsert_institutions
from unipaith.services.reference_ipeds_ingest import (
    ipeds_admissions_record,
    upsert_ipeds_admissions,
)


def test_ipeds_admissions_record_computes_rates():
    rec = ipeds_admissions_record(
        {
            "unitid": 166027,
            "year": 2022,
            "number_applied": 61221,
            "number_admitted": 1984,
            "number_enrolled_total": 1646,
            "sex": 99,
        }
    )
    a = rec["ipeds_admissions"]
    assert rec["unitid"] == 166027
    assert a["applied"] == 61221
    assert a["admit_rate"] == round(1984 / 61221, 4)
    assert a["yield_rate"] == round(1646 / 1984, 4)
    # zero / missing applications -> unusable
    assert ipeds_admissions_record({"unitid": 1, "number_applied": 0}) is None
    assert ipeds_admissions_record({"number_applied": 10}) is None


@pytest.mark.asyncio
async def test_upsert_ipeds_merges_into_extra_preserving_siblings(db_session):
    await upsert_institutions(db_session, [{"unitid": 166027, "name": "Harvard University"}])
    # carnegie already present -> must survive
    row = (
        await db_session.scalars(select(RefInstitution).where(RefInstitution.unitid == 166027))
    ).one()
    row.extra = {"carnegie": {"research": "Research 1"}}
    await db_session.commit()

    linked = await upsert_ipeds_admissions(
        db_session,
        [
            {"unitid": 166027, "ipeds_admissions": {"applied": 61221, "admit_rate": 0.0324}},
            {"unitid": 999999, "ipeds_admissions": {"applied": 1}},  # absent -> skipped
        ],
    )
    assert linked == 1

    db_session.expire_all()
    row = (
        await db_session.scalars(select(RefInstitution).where(RefInstitution.unitid == 166027))
    ).one()
    assert row.extra["ipeds_admissions"]["applied"] == 61221
    assert row.extra["carnegie"]["research"] == "Research 1"  # sibling preserved


@pytest.mark.asyncio
async def test_api_detail_includes_ipeds(client, db_session):
    await upsert_institutions(db_session, [{"unitid": 166027, "name": "Harvard University"}])
    await upsert_ipeds_admissions(
        db_session,
        [
            {"unitid": 166027, "ipeds_admissions": {"applied": 61221, "admit_rate": 0.0324}},
        ],
    )
    r = await client.get("/api/v1/reference/institutions/166027")
    assert r.status_code == 200
    assert r.json()["ipeds_admissions"]["applied"] == 61221
