"""Seed the external scholarships catalog (Spec 2026-06-14).

Reads ``seed_data/scholarships.json`` (the 9,500-row CareerOneStop export) and
upserts each row by ``external_id`` — idempotent, safe to re-run locally or in
prod via the ``aws ecs run-task`` one-off pattern. The json ``id`` field is the
CareerOneStop detail id and maps to ``external_id``.

Usage:
    PYTHONPATH=src python -m scripts.seed_scholarships
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import async_session
from unipaith.models.scholarship import Scholarship

# Resolve the seed file relative to the backend repo root robustly: this file is
# at ``<repo>/scripts/seed_scholarships.py``; the data lives at
# ``<repo>/seed_data/scholarships.json``.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SEED_FILE = _REPO_ROOT / "seed_data" / "scholarships.json"

# Per-statement chunk size for the upsert (keeps each round-trip bounded).
_CHUNK = 500


def _load_rows() -> list[dict]:
    with _SEED_FILE.open(encoding="utf-8") as fh:
        data = json.load(fh)
    rows: list[dict] = []
    for item in data:
        external_id = str(item.get("id") or "").strip()
        name = (item.get("name") or "").strip()
        if not external_id or not name:
            # External id + name are required; skip malformed rows rather than
            # writing a NOT-NULL violation.
            continue
        rows.append(
            {
                "external_id": external_id,
                "name": name[:500],
                "organization": _clip(item.get("organization"), 500),
                "purpose": item.get("purpose") or None,
                "level_of_study": _clip(item.get("level_of_study"), 300),
                "award_type": _clip(item.get("award_type"), 120),
                "award_amount": _clip(item.get("award_amount"), 200),
                "deadline": _clip(item.get("deadline"), 120),
                "url": item.get("url") or None,
                "source": _clip(item.get("source"), 60) or "careeronestop",
            }
        )
    return rows


def _clip(value: object, length: int) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text[:length] if text else None


async def upsert_rows(db: AsyncSession, rows: list[dict]) -> int:
    """Idempotent upsert of normalized scholarship dicts keyed on
    ``external_id``. Re-running refreshes the mutable fields without inserting
    duplicates. Does not commit — the caller owns the transaction. Importable so
    tests can exercise the same upsert path."""
    if not rows:
        return 0
    for start in range(0, len(rows), _CHUNK):
        chunk = rows[start : start + _CHUNK]
        stmt = pg_insert(Scholarship).values(chunk)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Scholarship.external_id],
            set_={
                "name": stmt.excluded.name,
                "organization": stmt.excluded.organization,
                "purpose": stmt.excluded.purpose,
                "level_of_study": stmt.excluded.level_of_study,
                "award_type": stmt.excluded.award_type,
                "award_amount": stmt.excluded.award_amount,
                "deadline": stmt.excluded.deadline,
                "url": stmt.excluded.url,
                "source": stmt.excluded.source,
            },
        )
        await db.execute(stmt)
    return len(rows)


async def seed() -> int:
    rows = _load_rows()
    if not rows:
        print("No scholarship rows found in seed_data/scholarships.json")
        return 0

    async with async_session() as db:
        count = await upsert_rows(db, rows)
        await db.commit()

    print(f"Seeded {count} scholarships (upsert by external_id) from {_SEED_FILE.name}")
    return count


async def main() -> None:
    await seed()


if __name__ == "__main__":
    asyncio.run(main())
