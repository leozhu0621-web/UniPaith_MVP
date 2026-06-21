"""Tests for the BLS -> ref_occupations ingestion (careers slice 2b)."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from unipaith.models import RefOccupation
from unipaith.services.reference_occupations_ingest import (
    OCC_SEED_PROVENANCE,
    bls_row_to_occupation,
    clean_num,
    upsert_occupations,
)


def test_clean_num():
    assert clean_num("206420") == 206420.0
    assert clean_num("1,234") == 1234.0
    assert clean_num(">=239200") == 239200.0
    assert clean_num("4.3") == 4.3
    for blank in ["—", "*", "", "N/A", None]:
        assert clean_num(blank) is None


def test_bls_row_to_occupation_line_item():
    row = {
        "soc_code": "11-1011",
        "title": "  Chief executives",
        "occ_type": "Line item",
        "employment_k": "309.4",
        "growth_pct": "4.3",
        "wage": "206420",
        "education": "Bachelor's degree",
    }
    rec = bls_row_to_occupation(row)
    assert rec == {
        "soc_code": "11-1011",
        "title": "Chief executives",
        "median_salary": 206420,
        "employment": 309400,
        "projected_growth_pct": 4.3,
        "education_typical": "Bachelor's degree",
    }


def test_bls_row_skips_summary_and_invalid():
    # Summary aggregate rows are skipped
    assert (
        bls_row_to_occupation({"soc_code": "11-0000", "title": "Management", "occ_type": "Summary"})
        is None
    )
    # invalid SOC
    assert (
        bls_row_to_occupation({"soc_code": "Total", "title": "x", "occ_type": "Line item"}) is None
    )


def test_bls_row_handles_suppressed_wage():
    row = {
        "soc_code": "11-1031",
        "title": "Legislators",
        "occ_type": "Line item",
        "employment_k": "27.7",
        "growth_pct": "3.4",
        "wage": "—",
        "education": "Bachelor's degree",
    }
    rec = bls_row_to_occupation(row)
    assert rec["median_salary"] is None
    assert rec["employment"] == 27700


@pytest.mark.asyncio
async def test_upsert_occupations_idempotent_and_provenance(db_session):
    recs = [
        {
            "soc_code": "15-1252",
            "title": "Software Developers",
            "median_salary": 130160,
            "employment": 1692100,
            "projected_growth_pct": 17.9,
            "education_typical": "Bachelor's degree",
        },
        {
            "soc_code": "29-1141",
            "title": "Registered Nurses",
            "median_salary": 86070,
            "employment": 3300100,
            "projected_growth_pct": 6.0,
            "education_typical": "Bachelor's degree",
        },
    ]
    await upsert_occupations(db_session, recs)
    await upsert_occupations(db_session, recs)
    assert await db_session.scalar(select(func.count()).select_from(RefOccupation)) == 2
    row = (
        await db_session.scalars(select(RefOccupation).where(RefOccupation.soc_code == "15-1252"))
    ).one()
    assert row.source == OCC_SEED_PROVENANCE["source"] == "seed"
    assert float(row.median_salary) == 130160
    assert row.related_majors == []


async def _seed_two(db_session):
    await upsert_occupations(
        db_session,
        [
            {
                "soc_code": "15-1252",
                "title": "Software Developers",
                "median_salary": 130160,
                "employment": 1692100,
                "projected_growth_pct": 17.9,
            },
            {
                "soc_code": "29-1141",
                "title": "Registered Nurses",
                "median_salary": 86070,
                "employment": 3300100,
                "projected_growth_pct": 6.0,
            },
        ],
    )


@pytest.mark.asyncio
async def test_api_occupations_search_and_detail(client, db_session):
    await _seed_two(db_session)
    r = await client.get("/api/v1/reference/occupations", params={"q": "software"})
    assert r.status_code == 200
    assert [o["soc_code"] for o in r.json()["items"]] == ["15-1252"]

    r = await client.get("/api/v1/reference/occupations/29-1141")
    assert r.status_code == 200
    assert r.json()["title"] == "Registered Nurses"
    assert r.json()["median_salary"] == 86070

    r = await client.get("/api/v1/reference/occupations/99-9999")
    assert r.status_code == 404
