"""Tests for the CIP<->SOC crosswalk linker (careers slice 2c)."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from unipaith.models import RefMajor, RefOccupation
from unipaith.services.reference_crosswalk_ingest import (
    build_link_maps,
    link_crosswalk,
    pair_from_row,
)
from unipaith.services.reference_majors_ingest import upsert_majors
from unipaith.services.reference_occupations_ingest import upsert_occupations

PAIRS = [
    {
        "cip_code": "11.0701",
        "cip_title": "Computer Science",
        "soc_code": "15-1252",
        "soc_title": "Software Developers",
    },
    {
        "cip_code": "11.0701",
        "cip_title": "Computer Science",
        "soc_code": "15-1211",
        "soc_title": "Computer Systems Analysts",
    },
    {
        "cip_code": "14.0901",
        "cip_title": "Computer Engineering",
        "soc_code": "15-1252",
        "soc_title": "Software Developers",
    },
]


def test_pair_from_row_strips_and_validates():
    p = pair_from_row(
        {
            "CIP2020Code": "01.0000",
            "CIP2020Title": "Agriculture, General.",
            "SOC2018Code": "19-1011",
            "SOC2018Title": "Animal Scientists",
        }
    )
    assert p == {
        "cip_code": "01.0000",
        "cip_title": "Agriculture, General",
        "soc_code": "19-1011",
        "soc_title": "Animal Scientists",
    }
    assert pair_from_row({"CIP2020Code": "", "SOC2018Code": "19-1011"}) is None


def test_build_link_maps_groups_and_dedups():
    cip_to_occs, soc_to_majors = build_link_maps(PAIRS)
    assert {o["soc_code"] for o in cip_to_occs["11.0701"]} == {"15-1252", "15-1211"}
    assert {m["cip_code"] for m in soc_to_majors["15-1252"]} == {"11.0701", "14.0901"}


@pytest.mark.asyncio
async def test_link_crosswalk_writes_both_directions(db_session):
    await upsert_majors(
        db_session,
        [
            {"cip_code": "11.0701", "title": "Computer Science", "description": "CS"},
            {"cip_code": "14.0901", "title": "Computer Engineering", "description": "CE"},
        ],
    )
    await upsert_occupations(
        db_session,
        [
            {"soc_code": "15-1252", "title": "Software Developers", "median_salary": 130160},
            {"soc_code": "15-1211", "title": "Computer Systems Analysts", "median_salary": 103800},
        ],
    )
    result = await link_crosswalk(db_session, PAIRS)
    assert result["majors_linked"] == 2
    assert result["occupations_linked"] == 2

    db_session.expire_all()
    cs = (await db_session.scalars(select(RefMajor).where(RefMajor.cip_code == "11.0701"))).one()
    assert {o["soc_code"] for o in cs.related_occupations} == {"15-1252", "15-1211"}
    dev = (
        await db_session.scalars(select(RefOccupation).where(RefOccupation.soc_code == "15-1252"))
    ).one()
    assert {m["cip_code"] for m in dev.related_majors} == {"11.0701", "14.0901"}


@pytest.mark.asyncio
async def test_link_crosswalk_skips_absent_rows(db_session):
    # only one major exists; a pair referencing a missing major/occupation is a no-op there
    await upsert_majors(db_session, [{"cip_code": "11.0701", "title": "Computer Science"}])
    result = await link_crosswalk(db_session, PAIRS)
    assert result["majors_linked"] == 1  # only 11.0701 existed (14.0901 absent)
    assert result["occupations_linked"] == 0  # no occupations seeded
