"""Tests for the Scorecard -> ref_institutions ingestion slice (spec 2026-06-20)."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from unipaith.models import RefInstitution
from unipaith.services.reference_ingest import (
    SEED_PROVENANCE,
    clean_value,
    csv_row_to_record,
    decode_control,
    upsert_institutions,
)


def test_clean_value_decodes_sentinels():
    for sentinel in ["NULL", "PrivacySuppressed", "NA", "PS", ""]:
        assert clean_value(sentinel) is None
    assert clean_value("  0.1234 ") == "0.1234"


def test_decode_control():
    assert decode_control(1) == "public"
    assert decode_control(2) == "private nonprofit"
    assert decode_control(3) == "private for-profit"
    assert decode_control(None) is None
    assert decode_control(9) is None


def test_csv_row_to_record_maps_and_folds_program_pct():
    row = {
        "UNITID": "166027",
        "OPEID": "00216500",
        "OPEID6": "002165",
        "INSTNM": "Harvard University",
        "CITY": "Cambridge",
        "STABBR": "MA",
        "CONTROL": "2",
        "ADM_RATE": "0.0468",
        "UGDS": "7973",
        "MD_EARN_WNE_P10": "95114",
        "SAT_AVG": "1520",
        "PCIP11": "0.12",
        "PCIP14": "PrivacySuppressed",
        "PCIP52": "0",
    }
    rec = csv_row_to_record(row)
    assert rec["unitid"] == 166027
    assert rec["name"] == "Harvard University"
    assert rec["control_code"] == 2
    assert rec["control"] == "private nonprofit"
    assert rec["admit_rate"] == 0.0468
    assert rec["size"] == 7973
    assert rec["earnings_10yr_median"] == 95114
    assert rec["program_pct"]["PCIP11"] == 0.12
    assert "PCIP14" not in rec["program_pct"]  # sentinel dropped
    assert "PCIP52" not in rec["program_pct"]  # zero dropped
    # the helper must NOT set a `source` that violates KNOWLEDGE_SOURCE_CHECK
    assert "source" not in rec


@pytest.mark.asyncio
async def test_upsert_is_idempotent_and_carries_seed_provenance(db_session):
    recs = [
        {"unitid": 1, "name": "Alpha U", "state": "CA", "control_code": 1, "control": "public"},
        {
            "unitid": 2,
            "name": "Beta College",
            "state": "NY",
            "control_code": 2,
            "control": "private nonprofit",
        },
    ]
    await upsert_institutions(db_session, recs)
    await upsert_institutions(db_session, recs)  # second time must not duplicate
    count = await db_session.scalar(select(func.count()).select_from(RefInstitution))
    assert count == 2

    row = (await db_session.scalars(select(RefInstitution).where(RefInstitution.unitid == 1))).one()
    assert row.source == SEED_PROVENANCE["source"] == "seed"
    assert row.status == "live"
    assert row.fetched_at is not None

    # update path — Core upsert writes to the DB; expire the identity map so we read fresh
    recs[0]["name"] = "Alpha University"
    await upsert_institutions(db_session, recs)
    db_session.expire_all()
    row = (await db_session.scalars(select(RefInstitution).where(RefInstitution.unitid == 1))).one()
    assert row.name == "Alpha University"
    # still no duplicate after the update
    assert await db_session.scalar(select(func.count()).select_from(RefInstitution)) == 2


async def _seed_three(db_session):
    await upsert_institutions(
        db_session,
        [
            {
                "unitid": 166027,
                "name": "Harvard University",
                "state": "MA",
                "control_code": 2,
                "control": "private nonprofit",
                "size": 7973,
                "admit_rate": 0.0468,
                "earnings_10yr_median": 95114,
            },
            {
                "unitid": 110635,
                "name": "University of California-Berkeley",
                "state": "CA",
                "control_code": 1,
                "control": "public",
                "size": 30980,
                "admit_rate": 0.1124,
            },
            {
                "unitid": 243744,
                "name": "Stanford University",
                "state": "CA",
                "control_code": 2,
                "control": "private nonprofit",
                "size": 7645,
                "admit_rate": 0.0434,
            },
        ],
    )


@pytest.mark.asyncio
async def test_api_search_and_filter(client, db_session):
    await _seed_three(db_session)
    r = await client.get("/api/v1/reference/institutions", params={"q": "stanford"})
    assert r.status_code == 200
    assert any(i["name"] == "Stanford University" for i in r.json()["items"])

    r = await client.get(
        "/api/v1/reference/institutions", params={"state": "CA", "control": "public"}
    )
    assert [i["name"] for i in r.json()["items"]] == ["University of California-Berkeley"]


@pytest.mark.asyncio
async def test_api_detail_and_404(client, db_session):
    await _seed_three(db_session)
    r = await client.get("/api/v1/reference/institutions/166027")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Harvard University"
    assert body["earnings_10yr_median"] == 95114

    r = await client.get("/api/v1/reference/institutions/999999")
    assert r.status_code == 404
