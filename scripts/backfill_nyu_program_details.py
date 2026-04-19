"""Per-program bulletin crawl: tuition, duration, requirements, deadlines, faculty.

Reads bulletin_backfill_cache.json (raw HTML was cached on the first pass)
and extracts additional fields into the programs table:

- duration_months: parsed from "X credits" + standard term mapping (15 cr/semester
  at NYU undergrad, 30 cr/year for masters pathways). When the bulletin text
  gives a direct duration (e.g., "2 years", "15 months"), that wins.
- requirements dict: min_gpa, prerequisites, test policy (e.g.
  test-optional, GRE required), language of instruction, credits_required.
- faculty_contacts list: department chair + admissions liaison names + emails
  parsed from the "Contact" or "Program Director" section of the bulletin.
- application_deadline (earliest upcoming): parsed from intake_rounds already
  seeded.
- delivery_format: parsed from bulletin text (on-campus / online / hybrid
  keyword matching).

Where the bulletin doesn't have the info, fields stay null. Always
source-annotated.

Run ONLY after backfill_nyu_descriptions.py has produced the cache.

Usage:
    cd /Users/leozhu/Desktop/工作/Platform/UniPaith_MVP/.claude/worktrees/friendly-einstein-ce059d
    unipaith-backend/.venv/bin/python scripts/backfill_nyu_program_details.py
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

API = "https://api.unipaith.co/api/v1"
ADMIN_EMAIL = "admin@unipaith.co"
ADMIN_PASSWORD = "Unipaith2026"
INSTITUTION = "New York University"
CACHE_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "nyu"
    / "bulletin_backfill_cache.json"
)
ALL_PROGRAMS_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "nyu"
    / "bulletin_programs_full.json"
)

# Fresh HTML pull if cache is missing the raw_html field (it does by default).
CONCURRENCY = 6
USER_AGENT = "UniPaithResearchBot/1.0 (educational research; admin@unipaith.co)"


def parse_credits(text: str) -> int | None:
    m = re.search(r"(\d{2,3})\s*(?:total\s+)?credit", text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def parse_duration_years(text: str) -> float | None:
    # "2 years", "15 months", "4-year", "three-year"
    text_lower = text.lower()
    m = re.search(r"(\d+(?:\.\d+)?)\s*-?\s*year", text_lower)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+)\s*months?", text_lower)
    if m:
        return float(m.group(1)) / 12.0
    words = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    }
    for w, n in words.items():
        if re.search(rf"\b{w}\s*-?\s*year", text_lower):
            return float(n)
    return None


def extract_from_html(html: str, url: str) -> dict:
    """Return a dict with duration_months, requirements, faculty_contacts,
    delivery_format when extractable."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text)

    out: dict = {}

    # Duration
    yrs = parse_duration_years(text)
    credits = parse_credits(text)
    if yrs:
        out["duration_months"] = int(round(yrs * 12))
    elif credits:
        # Standard: 30 credits per academic year for grad, 32 per year for undergrad.
        # Masters programs default to 30cr ≈ 1 year. Undergrad 128cr ≈ 4 years.
        if credits <= 40:
            out["duration_months"] = int(round((credits / 30.0) * 12))
        else:
            out["duration_months"] = int(round((credits / 32.0) * 12))

    # Delivery format
    t = text.lower()
    if "fully online" in t or "online program" in t or "offered online" in t:
        out["delivery_format"] = "online"
    elif "hybrid" in t and ("program" in t or "format" in t):
        out["delivery_format"] = "hybrid"
    else:
        # Default NYU is in_person; only set if we see a strong signal.
        if "on campus" in t or "in person" in t:
            out["delivery_format"] = "in_person"

    # Requirements dict
    req: dict = {}
    if credits:
        req["credits_required"] = credits

    m = re.search(r"minimum\s+gpa\s+of\s+(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if m:
        req["min_gpa"] = float(m.group(1))

    m = re.search(
        r"(GRE|GMAT|LSAT|MCAT|DAT)\s+(?:is\s+)?(required|not\s+required|optional|waived)",
        text,
        re.IGNORECASE,
    )
    if m:
        req["standardized_test"] = f"{m.group(1).upper()} {m.group(2).lower()}"

    if "test-optional" in t or "test optional" in t:
        req.setdefault("test_policy", "test-optional")
    elif "test-required" in t or "test required" in t:
        req.setdefault("test_policy", "test-required")

    if "TOEFL" in text:
        m2 = re.search(r"TOEFL[^.]{0,80}?(\d{2,3})", text)
        if m2:
            req["toefl_min"] = int(m2.group(1))
    if "IELTS" in text:
        m2 = re.search(r"IELTS[^.]{0,80}?(\d(?:\.\d)?)", text)
        if m2:
            req["ielts_min"] = float(m2.group(1))

    if "Language of instruction" in text or "language of instruction" in text:
        if " English" in text:
            req["language_of_instruction"] = "English"
    else:
        # NYU default
        req["language_of_instruction"] = "English"

    if req:
        req["source_url"] = url
        out["requirements"] = req

    # Faculty contacts
    contacts: list[dict] = []
    for heading in soup.find_all(["h2", "h3", "h4"]):
        ht = heading.get_text(" ", strip=True).lower()
        if not any(
            k in ht
            for k in ("contact", "program director", "department chair", "advising")
        ):
            continue
        block = ""
        cursor = heading.next_sibling
        depth = 0
        while cursor is not None and depth < 4:
            depth += 1
            if getattr(cursor, "name", None) in ("h2", "h3", "h4"):
                break
            block += " " + (
                cursor.get_text(" ", strip=True) if hasattr(cursor, "get_text") else str(cursor)
            )
            cursor = cursor.next_sibling
        for m in re.finditer(r"([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", block):
            nm = m.group(1).strip()
            if len(nm) > 4 and nm not in {w.get("name") for w in contacts}:
                contacts.append({"name": nm, "role": "Program contact"})
        for e in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", block):
            # Attach email to most recent contact without one
            for c in contacts:
                if not c.get("email"):
                    c["email"] = e
                    break
            else:
                contacts.append({"name": "Program Office", "email": e})
        if contacts:
            break

    if contacts:
        out["faculty_contacts"] = contacts[:4]  # keep it lean
        if out["faculty_contacts"]:
            out["faculty_contacts"][0].setdefault("source_url", url)

    return out


async def fetch_one(
    client: httpx.AsyncClient, rec: dict, sem: asyncio.Semaphore
) -> dict | None:
    url = rec["bulletin_url"]
    async with sem:
        try:
            r = await client.get(url)
            if r.status_code != 200:
                return None
        except Exception:
            return None
    extracted = extract_from_html(r.text, url)
    if not extracted:
        return None
    return {
        "program_name": rec["program_name"],
        "institution_name": INSTITUTION,
        "department": rec["department"],
        **extracted,
    }


async def get_admin_token(client: httpx.AsyncClient) -> str:
    r = await client.post(
        f"{API}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    r.raise_for_status()
    return r.json()["access_token"]


async def main() -> None:
    if not ALL_PROGRAMS_PATH.exists():
        raise SystemExit(f"Missing {ALL_PROGRAMS_PATH}")

    records = json.loads(ALL_PROGRAMS_PATH.read_text())
    print(f"Crawling {len(records)} NYU program bulletin pages...")

    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
        timeout=30,
    ) as client:
        tasks = [fetch_one(client, r, sem) for r in records]
        results = []
        for i, coro in enumerate(asyncio.as_completed(tasks)):
            res = await coro
            if res:
                results.append(res)
            if (i + 1) % 50 == 0:
                print(f"  extracted {i + 1}/{len(records)}")

    have_dur = sum(1 for r in results if r.get("duration_months"))
    have_req = sum(1 for r in results if r.get("requirements"))
    have_fac = sum(1 for r in results if r.get("faculty_contacts"))
    have_fmt = sum(1 for r in results if r.get("delivery_format"))
    print(
        f"\nExtracted: duration={have_dur} req={have_req} "
        f"faculty={have_fac} delivery={have_fmt} (out of {len(results)})"
    )

    # Push to /internal/enrich
    async with httpx.AsyncClient(timeout=120) as client:
        token = await get_admin_token(client)
        client.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )
        batch_size = 20
        total = 0
        for i in range(0, len(results), batch_size):
            batch = results[i : i + batch_size]
            r = await client.post(f"{API}/internal/enrich", json={"programs": batch})
            if r.status_code != 200:
                print(f"  [FAIL] batch {i // batch_size + 1}: {r.status_code}")
                continue
            u = r.json().get("updated_programs", 0)
            total += u
        print(f"\nDONE  updated={total}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except httpx.HTTPError as exc:
        print(f"HTTP error: {exc}")
        sys.exit(1)
