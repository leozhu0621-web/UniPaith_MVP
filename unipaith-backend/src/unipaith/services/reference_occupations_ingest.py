"""BLS Employment Projections -> ref_occupations ingestion (careers slice 2b).

Populates the existing (Spec 60) ``ref_occupations`` table from the BLS Occupational
Projections matrix (Table 1.2) — real wages, employment, projected growth, and typical
entry education per SOC occupation. No migration: the table already exists.

Only "Line item" rows (detailed SOC occupations) are loaded; "Summary" aggregates are
skipped. ``source="seed"`` / ``status="live"`` are the only KNOWLEDGE_*_CHECK-allowed values.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

OCC_SEED_PROVENANCE = {
    "source": "seed",
    "source_domain": "bls.gov",
    "source_url": "https://www.bls.gov/emp/data/occupational-data.htm",
    "confidence": 0.95,
    "status": "live",
}

_SOC_RE = re.compile(r"^\d{2}-\d{4}$")
_NUM_CLEAN = re.compile(r"[,$>=<≥*\s]")


def clean_num(value) -> float | None:
    """Parse a BLS numeric cell. '—'/'*'/'' -> None; '>=239200'/'1,234' -> number."""
    if value is None:
        return None
    s = str(value).strip()
    if s in {"", "—", "-", "*", "N/A", "NA"}:
        return None
    s = _NUM_CLEAN.sub("", s)
    try:
        return float(s)
    except ValueError:
        return None


def bls_row_to_occupation(row: dict) -> dict | None:
    """Map one clean BLS Table 1.2 row to a ref_occupations record (no provenance).

    Expects keys: soc_code, title, occ_type, employment_k, growth_pct, wage, education.
    Returns None for non-detailed rows (Summary) or invalid SOC codes.
    """
    if (row.get("occ_type") or "").strip() != "Line item":
        return None
    soc = (row.get("soc_code") or "").strip()
    if not _SOC_RE.match(soc):
        return None
    title = (row.get("title") or "").strip()
    if not title:
        return None
    emp_k = clean_num(row.get("employment_k"))
    wage = clean_num(row.get("wage"))
    growth = clean_num(row.get("growth_pct"))
    edu = (row.get("education") or "").strip() or None
    return {
        "soc_code": soc,
        "title": title,
        "median_salary": int(wage) if wage is not None else None,
        "employment": int(emp_k * 1000) if emp_k is not None else None,
        "projected_growth_pct": growth,
        "education_typical": edu,
    }


_OCC_DOMAIN_COLUMNS = [
    "soc_code",
    "title",
    "median_salary",
    "employment",
    "projected_growth_pct",
    "education_typical",
]
_PROVENANCE_COLUMNS = [
    "source",
    "source_domain",
    "source_url",
    "confidence",
    "status",
    "fetched_at",
]


async def upsert_occupations(db: AsyncSession, records: list[dict], batch_size: int = 500) -> int:
    """Upsert ref_occupations by soc_code with seed provenance. Idempotent."""
    from unipaith.models import RefOccupation

    now = datetime.now(UTC)
    written = 0
    for start in range(0, len(records), batch_size):
        chunk = records[start : start + batch_size]
        rows = []
        for r in chunk:
            if not r.get("soc_code"):
                continue
            row = {col: r.get(col) for col in _OCC_DOMAIN_COLUMNS}
            row.update(OCC_SEED_PROVENANCE)
            row["fetched_at"] = now
            rows.append(row)
        if not rows:
            continue
        update_cols = [c for c in (_OCC_DOMAIN_COLUMNS + _PROVENANCE_COLUMNS) if c != "soc_code"]
        stmt = pg_insert(RefOccupation).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["soc_code"],
            set_={c: getattr(stmt.excluded, c) for c in update_cols},
        )
        await db.execute(stmt)
        written += len(rows)
    await db.commit()
    return written
