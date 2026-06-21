"""NCES CIP 2020 <-> SOC 2018 crosswalk -> link ref_majors <-> ref_occupations (careers 2c).

The major->career join. Reads the NCES CIP-SOC crosswalk pairs and denormalizes them onto the
existing rows: ``ref_majors.related_occupations`` = [{soc_code,title}], and
``ref_occupations.related_majors`` = [{cip_code,title}]. No migration, no new table — only
JSONB list columns on rows that already exist (unmatched cip/soc are skipped).
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession


def _clean(s) -> str:
    return str(s or "").strip().rstrip(".").strip()


def pair_from_row(row: dict) -> dict | None:
    """One crosswalk row -> {cip_code, cip_title, soc_code, soc_title}. None if incomplete."""
    cip = _clean(row.get("CIP2020Code"))
    soc = _clean(row.get("SOC2018Code"))
    if not cip or not soc:
        return None
    return {
        "cip_code": cip,
        "cip_title": _clean(row.get("CIP2020Title")),
        "soc_code": soc,
        "soc_title": _clean(row.get("SOC2018Title")),
    }


def build_link_maps(pairs: list[dict]) -> tuple[dict, dict]:
    """Group pairs into cip -> [occupations] and soc -> [majors], deduped by code."""
    cip_to_occs: dict[str, list] = defaultdict(list)
    soc_to_majors: dict[str, list] = defaultdict(list)
    seen_co: set = set()
    seen_sm: set = set()
    for p in pairs:
        cip, soc = p["cip_code"], p["soc_code"]
        if (cip, soc) not in seen_co:
            seen_co.add((cip, soc))
            cip_to_occs[cip].append({"soc_code": soc, "title": p["soc_title"]})
        if (soc, cip) not in seen_sm:
            seen_sm.add((soc, cip))
            soc_to_majors[soc].append({"cip_code": cip, "title": p["cip_title"]})
    return dict(cip_to_occs), dict(soc_to_majors)


async def link_crosswalk(db: AsyncSession, pairs: list[dict]) -> dict:
    """Write related_occupations onto ref_majors and related_majors onto ref_occupations.

    Returns {majors_linked, occupations_linked} = rows actually updated (existing rows only).
    """
    from unipaith.models import RefMajor, RefOccupation

    cip_to_occs, soc_to_majors = build_link_maps(pairs)
    majors_linked = 0
    for cip, occs in cip_to_occs.items():
        res = await db.execute(
            update(RefMajor).where(RefMajor.cip_code == cip).values(related_occupations=occs)
        )
        majors_linked += res.rowcount or 0
    occupations_linked = 0
    for soc, majors in soc_to_majors.items():
        res = await db.execute(
            update(RefOccupation).where(RefOccupation.soc_code == soc).values(related_majors=majors)
        )
        occupations_linked += res.rowcount or 0
    await db.commit()
    return {"majors_linked": majors_linked, "occupations_linked": occupations_linked}
