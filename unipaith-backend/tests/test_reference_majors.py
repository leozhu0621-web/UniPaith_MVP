"""Tests for the CIP -> ref_majors ingestion (careers slice, 2026-06-20)."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from unipaith.models import RefMajor
from unipaith.services.reference_majors_ingest import (
    MAJOR_SEED_PROVENANCE,
    cip_row_to_major,
    clean_title,
    strip_cip,
    upsert_majors,
)


def test_strip_cip_unwraps_excel_text():
    assert strip_cip('="01.0101"') == "01.0101"
    assert strip_cip('="01"') == "01"
    assert strip_cip("11.0701") == "11.0701"
    assert strip_cip(None) is None


def test_clean_title_strips_trailing_period():
    assert clean_title("Computer Science.") == "Computer Science"
    assert clean_title("  Agriculture, General.  ") == "Agriculture, General"
    assert clean_title(None) is None


def test_cip_row_to_major():
    row = {
        "CIPCode": '="11.0701"',
        "CIPTitle": "Computer Science.",
        "CIPDefinition": "A program that focuses on computers.",
    }
    rec = cip_row_to_major(row)
    assert rec == {
        "cip_code": "11.0701",
        "title": "Computer Science",
        "description": "A program that focuses on computers.",
    }
    # unusable rows -> None
    assert cip_row_to_major({"CIPCode": "", "CIPTitle": "x"}) is None


@pytest.mark.asyncio
async def test_upsert_majors_idempotent_and_provenance(db_session):
    recs = [
        {"cip_code": "11.0701", "title": "Computer Science", "description": "CS"},
        {"cip_code": "14.0901", "title": "Computer Engineering", "description": "CE"},
    ]
    await upsert_majors(db_session, recs)
    await upsert_majors(db_session, recs)
    assert await db_session.scalar(select(func.count()).select_from(RefMajor)) == 2

    row = (await db_session.scalars(select(RefMajor).where(RefMajor.cip_code == "11.0701"))).one()
    assert row.source == MAJOR_SEED_PROVENANCE["source"] == "seed"
    assert row.status == "live"
    assert row.related_occupations == []  # list default applied on insert

    recs[0]["title"] = "Computer Science, General"
    await upsert_majors(db_session, recs)
    db_session.expire_all()
    row = (await db_session.scalars(select(RefMajor).where(RefMajor.cip_code == "11.0701"))).one()
    assert row.title == "Computer Science, General"
    assert await db_session.scalar(select(func.count()).select_from(RefMajor)) == 2


async def _seed_two(db_session):
    await upsert_majors(
        db_session,
        [
            {"cip_code": "11.0701", "title": "Computer Science", "description": "CS"},
            {
                "cip_code": "26.0101",
                "title": "Biology/Biological Sciences, General",
                "description": "Bio",
            },
        ],
    )


@pytest.mark.asyncio
async def test_api_majors_search_and_detail(client, db_session):
    await _seed_two(db_session)
    r = await client.get("/api/v1/reference/majors", params={"q": "computer"})
    assert r.status_code == 200
    assert [m["cip_code"] for m in r.json()["items"]] == ["11.0701"]

    r = await client.get("/api/v1/reference/majors/26.0101")
    assert r.status_code == 200
    assert r.json()["title"] == "Biology/Biological Sciences, General"

    r = await client.get("/api/v1/reference/majors/99.9999")
    assert r.status_code == 404
