"""Carnegie Classification 2025 -> ref_institutions "distinction" enrichment.

Adds the Carnegie research / institutional / access-&-earnings classification onto each
institution (keyed by unitid). No migration, no new table: the labels are merged into the
existing ``ref_institutions.extra`` JSONB under the ``carnegie`` key, so the institution
detail can surface "R1: ..." style distinction. Unmatched unitids are skipped.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


def _clean(v) -> str | None:
    if v is None:
        return None
    s = str(v).strip().rstrip(".").strip()
    return s or None


def carnegie_from_row(row: dict) -> dict | None:
    """One Carnegie 'data' sheet row -> {unitid, carnegie:{...}}. None if no unitid or no labels."""
    raw_unitid = row.get("unitid")
    try:
        unitid = int(float(raw_unitid))
    except (TypeError, ValueError):
        return None
    carnegie = {
        "research": _clean(row.get("research2025name")),
        "classification": _clean(row.get("ic2025name")),
        "access_earnings": _clean(row.get("saec2025name")),
    }
    carnegie = {k: v for k, v in carnegie.items() if v is not None}
    if not carnegie:
        return None
    return {"unitid": unitid, "carnegie": carnegie}


async def upsert_carnegie(db: AsyncSession, records: list[dict], batch_size: int = 500) -> int:
    """Merge the carnegie object into ref_institutions.extra for each existing unitid. Idempotent.

    Python-side merge (load row -> mutate extra dict -> flush): preserves sibling extra keys and
    sidesteps JSONB-operator type inference. Unitid is a unique column (the PK is a UUID), so we
    match on unitid, not the primary key.
    """
    from sqlalchemy import select

    from unipaith.models import RefInstitution

    by_unitid = {
        r["unitid"]: r["carnegie"]
        for r in records
        if r.get("unitid") is not None and r.get("carnegie")
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
            extra["carnegie"] = by_unitid[row.unitid]
            row.extra = extra
            linked += 1
        await db.commit()
    return linked
