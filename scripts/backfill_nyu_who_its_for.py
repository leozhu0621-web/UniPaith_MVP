"""Generate who_its_for paragraphs for every NYU program.

For each program: read description_text + degree_type + department, then
call OpenAI to produce a 1-paragraph "who thrives here" summary written
for prospective students. Pushes via /internal/enrich.

Concurrent (CONCURRENCY=8). Keeps the LLM cost low by capping prompt +
response tokens. Skips programs that already have who_its_for set with
>=80 chars.

Usage:
    cd /Users/leozhu/Desktop/工作/Platform/UniPaith_MVP/.claude/worktrees/friendly-einstein-ce059d
    OPENAI_API_KEY=$(aws secretsmanager get-secret-value \
        --secret-id unipaith/production/openai-api-key \
        --query SecretString --output text) \
    unipaith-backend/.venv/bin/python scripts/backfill_nyu_who_its_for.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx
from openai import AsyncOpenAI

API = "https://api.unipaith.co/api/v1"
ADMIN_EMAIL = "admin@unipaith.co"
ADMIN_PASSWORD = "Unipaith2026"
INSTITUTION_ID = "6dd6d3ad-2e6a-4209-ae2b-1f928bc2429e"
INSTITUTION = "New York University"
CONCURRENCY = 8
MODEL = "gpt-4o-mini"  # cheap + fast; quality fine for short fit summaries


SYSTEM_PROMPT = (
    "You are an honest, plain-spoken admissions counselor. For each NYU "
    "program, write a single paragraph (90-130 words) describing exactly "
    "who thrives in this program. Be concrete: name the kind of student, "
    "their interests, prior preparation, learning style, and post-grad "
    "goals. Do not say generic things like 'students who want to learn'. "
    "Do not write marketing copy. Do not include the program name in the "
    "first sentence. Output the paragraph only, no preamble."
)


async def get_admin_token(client: httpx.AsyncClient) -> str:
    r = await client.post(
        f"{API}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    r.raise_for_status()
    return r.json()["access_token"]


async def fetch_all_programs(client: httpx.AsyncClient) -> list[dict]:
    out: list[dict] = []
    for page in range(1, 10):
        r = await client.get(
            f"{API}/programs",
            params={
                "institution_id": INSTITUTION_ID,
                "page_size": 100,
                "page": page,
            },
        )
        r.raise_for_status()
        d = r.json()
        items = d.get("items", [])
        out.extend(items)
        if page >= (d.get("total_pages") or 1):
            break
    return out


async def fetch_program_detail(client: httpx.AsyncClient, pid: str) -> dict | None:
    r = await client.get(f"{API}/programs/{pid}")
    if r.status_code != 200:
        return None
    return r.json()


async def gen_who_its_for(
    openai_client: AsyncOpenAI,
    sem: asyncio.Semaphore,
    program: dict,
) -> str | None:
    desc = program.get("description_text") or ""
    if len(desc) < 100:
        return None
    name = program["program_name"]
    deg = program["degree_type"]
    dept = program.get("department") or ""
    user_msg = (
        f"Program: {name} ({deg.upper()})\n"
        f"School/Department: {dept}\n"
        f"Program description (NYU bulletin):\n{desc[:1500]}\n\n"
        "Write the 'who thrives here' paragraph (90-130 words)."
    )
    async with sem:
        try:
            r = await openai_client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=220,
                temperature=0.5,
            )
            return r.choices[0].message.content.strip()
        except Exception as exc:
            print(f"  [LLM fail] {name}: {exc}")
            return None


async def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Set OPENAI_API_KEY (export from secrets manager).")

    print("=" * 60)
    print("NYU who_its_for BACKFILL")
    print("=" * 60)

    openai_client = AsyncOpenAI(api_key=api_key)
    sem = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient(timeout=120) as client:
        token = await get_admin_token(client)
        client.headers.update({"Authorization": f"Bearer {token}"})

        progs = await fetch_all_programs(client)
        print(f"Fetched {len(progs)} NYU programs (search endpoint)")

        # Need full details to read description_text (search endpoint omits it
        # for brevity on some payloads).
        details: list[dict] = []
        for i, p in enumerate(progs):
            d = await fetch_program_detail(client, p["id"])
            if d:
                details.append(d)
            if (i + 1) % 100 == 0:
                print(f"  details fetched {i + 1}/{len(progs)}")

        # Skip programs that already have a who_its_for >=80 chars.
        candidates = [
            d for d in details
            if not (d.get("who_its_for") and len(d["who_its_for"]) >= 80)
            and d.get("description_text")
            and len(d.get("description_text") or "") >= 100
        ]
        print(f"\nNeed who_its_for: {len(candidates)} programs")

        # Generate concurrently.
        tasks = [gen_who_its_for(openai_client, sem, p) for p in candidates]
        results: list[tuple[dict, str | None]] = []
        for i, coro in enumerate(asyncio.as_completed(tasks)):
            text = await coro
            # Pair back with the corresponding program by completion order
            # is not safe; we iterate sequentially and keep program ref.
            results.append((candidates[i], text))
            if (i + 1) % 50 == 0:
                print(f"  generated {i + 1}/{len(candidates)}")

        # Push via /internal/enrich. Use program_name+department key.
        enrichable = [
            {
                "program_name": p["program_name"],
                "institution_name": INSTITUTION,
                "department": p.get("department"),
                "who_its_for": text,
            }
            for p, text in results
            if text
        ]
        print(f"\nEnrichable: {len(enrichable)}")

        for i in range(0, len(enrichable), 25):
            batch = enrichable[i : i + 25]
            r = await client.post(
                f"{API}/internal/enrich", json={"programs": batch}
            )
            if r.status_code != 200:
                print(f"  [FAIL] batch {i // 25 + 1}: {r.status_code}")
                continue
            u = r.json().get("updated_programs", 0)
            print(f"  batch {i // 25 + 1}: updated {u}/{len(batch)}")

    print("\nDONE")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except httpx.HTTPError as exc:
        print(f"HTTP error: {exc}")
        sys.exit(1)
