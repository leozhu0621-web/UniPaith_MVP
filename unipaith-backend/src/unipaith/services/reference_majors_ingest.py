"""NCES CIP 2020 -> ref_majors ingestion (spec 2026-06-20, careers slice).

Populates the existing (Spec 60) ``ref_majors`` table from the NCES Classification of
Instructional Programs dictionary — the canonical major taxonomy. No migration: the table
already exists. Pure helpers shared by the seed builder + loader.

CIP cells arrive Excel-text-wrapped (``="01.0101"``); ``strip_cip`` unwraps them.
``source="seed"`` / ``status="live"`` are the only ``KNOWLEDGE_*_CHECK``-allowed values.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

MAJOR_SEED_PROVENANCE = {
    "source": "seed",
    "source_domain": "nces.ed.gov",
    "source_url": "https://nces.ed.gov/ipeds/cipcode/",
    "confidence": 0.95,
    "status": "live",
}

_CIP_WRAP = re.compile(r'^="?|"$')


def strip_cip(value) -> str | None:
    """Unwrap an Excel-text CIP cell: ``="01.0101"`` -> ``01.0101``."""
    if value is None:
        return None
    s = re.sub(_CIP_WRAP, "", str(value).strip()).strip().strip('"')
    return s or None


def clean_title(value) -> str | None:
    if value is None:
        return None
    s = str(value).strip().rstrip(".").strip()
    return s or None


def cip_row_to_major(row: dict) -> dict | None:
    """Map one CIPCode2020.csv row to a ref_majors record (no provenance). None if unusable."""
    cip = strip_cip(row.get("CIPCode"))
    title = clean_title(row.get("CIPTitle"))
    if not cip or not title:
        return None
    desc = (row.get("CIPDefinition") or "").strip() or None
    return {"cip_code": cip, "title": title, "description": desc}


_MAJOR_DOMAIN_COLUMNS = ["cip_code", "title", "description"]
_PROVENANCE_COLUMNS = [
    "source",
    "source_domain",
    "source_url",
    "confidence",
    "status",
    "fetched_at",
]


async def upsert_majors(db: AsyncSession, records: list[dict], batch_size: int = 500) -> int:
    """Upsert ref_majors by cip_code with seed provenance. Idempotent."""
    from unipaith.models import RefMajor

    now = datetime.now(UTC)
    written = 0
    for start in range(0, len(records), batch_size):
        chunk = records[start : start + batch_size]
        rows = []
        for r in chunk:
            if not r.get("cip_code"):
                continue
            row = {col: r.get(col) for col in _MAJOR_DOMAIN_COLUMNS}
            row.update(MAJOR_SEED_PROVENANCE)
            row["fetched_at"] = now
            rows.append(row)
        if not rows:
            continue
        update_cols = [c for c in (_MAJOR_DOMAIN_COLUMNS + _PROVENANCE_COLUMNS) if c != "cip_code"]
        stmt = pg_insert(RefMajor).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["cip_code"],
            set_={c: getattr(stmt.excluded, c) for c in update_cols},
        )
        await db.execute(stmt)
        written += len(rows)
    await db.commit()
    return written
