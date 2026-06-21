"""IPEDS admissions (via the Urban Education Data Portal) -> ref_institutions enrichment.

Adds the detailed admissions FUNNEL (applied / admitted / enrolled + computed admit & yield
rates) onto each institution — more granular than Scorecard's single admission rate. Keyed by
unitid, merged into the existing ``ref_institutions.extra`` JSONB under ``ipeds_admissions``.
No migration, no new table. Unmatched unitids are skipped.

Source: educationdata.urban.org IPEDS admissions-enrollment (sex=99 = total).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


def _int(v) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _rate(numer, denom) -> float | None:
    if numer is None or not denom:
        return None
    return round(numer / denom, 4)


def ipeds_admissions_record(row: dict) -> dict | None:
    """One Urban IPEDS admissions row (sex=99) -> {unitid, ipeds_admissions}. None if unusable."""
    unitid = _int(row.get("unitid"))
    applied = _int(row.get("number_applied"))
    admitted = _int(row.get("number_admitted"))
    enrolled = _int(row.get("number_enrolled_total"))
    if unitid is None or applied is None or applied <= 0:
        return None
    return {
        "unitid": unitid,
        "ipeds_admissions": {
            "year": _int(row.get("year")),
            "applied": applied,
            "admitted": admitted,
            "enrolled": enrolled,
            "admit_rate": _rate(admitted, applied),
            "yield_rate": _rate(enrolled, admitted),
        },
    }


async def upsert_ipeds_admissions(
    db: AsyncSession, records: list[dict], batch_size: int = 500
) -> int:
    """Merge ipeds_admissions into ref_institutions.extra for each existing unitid. Idempotent.

    Python-side merge (load row -> mutate extra dict): preserves sibling extra keys (e.g. carnegie)
    and matches on the unitid unique column (the PK is a UUID).
    """
    from sqlalchemy import select

    from unipaith.models import RefInstitution

    by_unitid = {
        r["unitid"]: r["ipeds_admissions"]
        for r in records
        if r.get("unitid") is not None and r.get("ipeds_admissions")
    }
    unitids = list(by_unitid)
    linked = 0
    for start in range(0, len(unitids), batch_size):
        chunk = unitids[start : start + batch_size]
        rows = (
            await db.scalars(select(RefInstitution).where(RefInstitution.unitid.in_(chunk)))
        ).all()
        for row in rows:
            extra = dict(row.extra or {})
            extra["ipeds_admissions"] = by_unitid[row.unitid]
            row.extra = extra
            linked += 1
        await db.commit()
    return linked
