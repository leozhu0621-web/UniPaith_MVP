"""Fetch each NYU bulletin URL + extract description_text + tracks.

Reads data/nyu/bulletin_programs_full.json, fetches each bulletin page
concurrently (polite rate limit), extracts:
- description_text: the first main paragraph (source-annotated)
- tracks: {concentrations, note} dict when the page lists named
  concentrations/specializations/tracks

Then hits the existing /internal/enrich endpoint per program to write
the data. Idempotent: fields that are already populated with >=200 chars
are left alone (change via SOURCE_OVERWRITE=true env var).

Usage:
    cd /Users/leozhu/Desktop/工作/Platform/UniPaith_MVP
    unipaith-backend/.venv/bin/python scripts/backfill_nyu_descriptions.py
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

API = "https://api.unipaith.co/api/v1"
ADMIN_EMAIL = "admin@unipaith.co"
ADMIN_PASSWORD = "Unipaith2026"
INSTITUTION = "New York University"
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "nyu" / "bulletin_programs_full.json"
CONCURRENCY = 6  # polite toward bulletins.nyu.edu
USER_AGENT = (
    "UniPaithResearchBot/1.0 "
    "(educational research; attributes source URLs; "
    "contact: admin@unipaith.co)"
)


def extract_from_html(html: str, url: str) -> tuple[str | None, dict | None]:
    """Return (description_text, tracks_dict_or_none)."""
    soup = BeautifulSoup(html, "html.parser")

    # Description: first <p> inside the main content body. Bulletins
    # typically put the program summary as the first paragraph of
    # .main_content or #textcontainer. Try a few selectors.
    desc = None
    for selector in [
        "#textcontainer p",
        ".main_content p",
        "main p",
        "article p",
        "body p",
    ]:
        for p in soup.select(selector):
            text = p.get_text(" ", strip=True)
            if len(text) >= 150 and not text.lower().startswith(("for questions", "contact us")):
                desc = text
                break
        if desc:
            break

    if desc:
        # Normalize whitespace, strip.
        desc = re.sub(r"\s+", " ", desc).strip()
        if len(desc) > 800:
            # Trim to two sentences max to keep cards readable.
            parts = re.split(r"(?<=[.!?])\s+", desc)
            desc = " ".join(parts[:3]).strip()
        desc = f"{desc}\n\n[Source: {url}]"

    # Tracks: look for headings named "Concentrations" / "Tracks" /
    # "Specializations" and pull their sibling list items.
    concentrations: list[str] = []
    note: str | None = None
    for heading in soup.find_all(["h2", "h3", "h4"]):
        heading_text = heading.get_text(" ", strip=True).lower()
        if not any(
            k in heading_text
            for k in ("concentration", "track", "specialization", "pathway", "focus area")
        ):
            continue
        # Collect list items until next heading.
        cursor = heading.next_sibling
        while cursor is not None:
            name = getattr(cursor, "name", None)
            if name in ("h2", "h3", "h4"):
                break
            if name in ("ul", "ol"):
                for li in cursor.find_all("li", recursive=False):
                    t = li.get_text(" ", strip=True)
                    t = re.sub(r"\s+", " ", t)
                    if 2 <= len(t) <= 120:
                        concentrations.append(t)
            cursor = cursor.next_sibling
        if concentrations:
            note = f"Source: {url}"
            break

    tracks = None
    if concentrations:
        # Dedup + preserve order
        seen: set[str] = set()
        uniq = []
        for c in concentrations:
            if c not in seen:
                seen.add(c)
                uniq.append(c)
        tracks = {"concentrations": uniq, "note": note or f"Source: {url}"}

    return desc, tracks


async def fetch_and_extract(
    client: httpx.AsyncClient, rec: dict, sem: asyncio.Semaphore
) -> dict | None:
    url = rec["bulletin_url"]
    async with sem:
        try:
            r = await client.get(url)
            if r.status_code != 200:
                return {"__fetch_failed__": True, "url": url, "code": r.status_code, **rec}
        except Exception as exc:
            return {"__fetch_failed__": True, "url": url, "error": str(exc), **rec}
    desc, tracks = extract_from_html(r.text, url)
    return {
        "program_name": rec["program_name"],
        "institution_name": INSTITUTION,
        "department": rec["department"],
        "description_text": desc,
        "tracks": tracks,
        "__source_url__": url,
    }


async def get_admin_token(client: httpx.AsyncClient) -> str:
    r = await client.post(
        f"{API}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    r.raise_for_status()
    return r.json()["access_token"]


async def main() -> None:
    if not DATA_PATH.exists():
        raise SystemExit(f"Missing {DATA_PATH}")

    records = json.loads(DATA_PATH.read_text())
    print(f"Backfilling descriptions for {len(records)} NYU programs...")

    # Step 1: concurrent fetch + extract from bulletin.
    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
        timeout=30,
    ) as client:
        tasks = [fetch_and_extract(client, r, sem) for r in records]
        results = []
        for i, coro in enumerate(asyncio.as_completed(tasks)):
            res = await coro
            results.append(res)
            if (i + 1) % 50 == 0:
                print(f"  fetched {i + 1}/{len(records)}")

    fetched = [r for r in results if r and not r.get("__fetch_failed__")]
    failed = [r for r in results if r and r.get("__fetch_failed__")]
    have_desc = sum(1 for r in fetched if r.get("description_text"))
    have_tracks = sum(1 for r in fetched if r.get("tracks"))
    print(
        f"\nFetched OK: {len(fetched)}  failed: {len(failed)}  "
        f"have description: {have_desc}  have tracks: {have_tracks}"
    )

    # Cache raw results for re-use.
    cache_path = DATA_PATH.parent / "bulletin_backfill_cache.json"
    cache_path.write_text(json.dumps(fetched, indent=2))
    print(f"Cached extracted payloads: {cache_path}")

    # Step 2: push to /internal/enrich in batches.
    enrichable = [
        {
            "program_name": r["program_name"],
            "institution_name": r["institution_name"],
            "department": r["department"],
            **({"description_text": r["description_text"]} if r.get("description_text") else {}),
            **({"tracks": r["tracks"]} if r.get("tracks") else {}),
        }
        for r in fetched
        if (r.get("description_text") or r.get("tracks"))
    ]
    print(f"Enrichable programs: {len(enrichable)}")

    async with httpx.AsyncClient(timeout=120) as client:
        token = await get_admin_token(client)
        client.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )

        batch_size = 20
        total_updated = 0
        for i in range(0, len(enrichable), batch_size):
            batch = enrichable[i : i + batch_size]
            r = await client.post(
                f"{API}/internal/enrich",
                json={"programs": batch},
            )
            if r.status_code != 200:
                print(f"  [FAIL] batch {i // batch_size + 1}: {r.status_code} {r.text[:200]}")
                continue
            d = r.json()
            u = d.get("updated_programs", 0)
            total_updated += u
            print(
                f"  batch {i // batch_size + 1}/{(len(enrichable) - 1) // batch_size + 1}: "
                f"updated {u}/{len(batch)}"
            )

        print(f"\nDONE updated_programs={total_updated}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except httpx.HTTPError as exc:
        print(f"HTTP error: {exc}")
        sys.exit(1)
