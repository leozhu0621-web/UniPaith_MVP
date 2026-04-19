"""Bulk-add every NYU program parsed from the bulletin sitemap to prod.

Reads data/nyu/bulletin_programs_full.json (produced by
parse_nyu_bulletin_programs.py) and POSTs to /internal/bulk-add-programs.
Idempotent: existing (program_name, department) rows are skipped.

After this runs, backfill_nyu_descriptions.py should be run to populate
description_text + tracks from each bulletin page.

Usage:
    cd /Users/leozhu/Desktop/工作/Platform/UniPaith_MVP
    unipaith-backend/.venv/bin/python scripts/bulk_add_nyu_programs.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx

API = "https://api.unipaith.co/api/v1"
ADMIN_EMAIL = "admin@unipaith.co"
ADMIN_PASSWORD = "Unipaith2026"
INSTITUTION = "New York University"
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "nyu" / "bulletin_programs_full.json"


async def get_admin_token(client: httpx.AsyncClient) -> str:
    r = await client.post(
        f"{API}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    r.raise_for_status()
    return r.json()["access_token"]


async def main() -> None:
    if not DATA_PATH.exists():
        raise SystemExit(
            f"{DATA_PATH} missing - run parse_nyu_bulletin_programs.py first."
        )

    records = json.loads(DATA_PATH.read_text())
    print(f"Loaded {len(records)} bulletin program records")

    # Payload per-batch. Batch by school to keep requests small.
    from collections import defaultdict
    by_dept: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_dept[r["department"]].append(
            {
                "program_name": r["program_name"],
                "degree_type": r["degree_type"],
                "department": r["department"],
                # Seed minimal; description / tracks / outcomes / media come
                # from the backfill pass that fetches each bulletin URL.
                # The bulletin URL itself is stashed in the seed script's
                # source-of-truth JSON; we don't persist it on the DB row
                # because Program doesn't have that column. The backfill
                # script reads the JSON directly.
                "is_published": True,
            }
        )

    async with httpx.AsyncClient(timeout=60) as client:
        token = await get_admin_token(client)
        client.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )

        total_inserted = 0
        total_skipped = 0
        for dept, progs in sorted(by_dept.items(), key=lambda kv: -len(kv[1])):
            payload = {"institution_name": INSTITUTION, "programs": progs}
            r = await client.post(f"{API}/internal/bulk-add-programs", json=payload)
            if r.status_code != 200:
                print(f"  [FAIL] {dept}: {r.status_code} {r.text[:200]}")
                continue
            d = r.json()
            ins = d.get("inserted", 0)
            skp = d.get("skipped_existing", 0)
            total_inserted += ins
            total_skipped += skp
            print(
                f"  {dept:40s}  inserted={ins:3d}  skipped_existing={skp:3d}  total={len(progs)}"
            )

        print(
            f"\nDONE  total inserted={total_inserted}  already_existed={total_skipped}"
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except httpx.HTTPError as exc:
        print(f"HTTP error: {exc}")
        sys.exit(1)
