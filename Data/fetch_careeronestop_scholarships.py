#!/usr/bin/env python3
"""Acquire the CareerOneStop Scholarship Finder dataset into Data/sources/scholarships/.

CareerOneStop (U.S. Dept of Labor) publishes ~9,500 real scholarships through its
public Scholarship Finder tool. There is NO Web API for it (verified: the v1 API
has no scholarship endpoint) and no bulk download — but the finder renders its
results SERVER-SIDE into the page HTML, paginated, so we read the public pages
directly (no key, no JS, public gov-funded data):

    https://www.careeronestop.org/Toolkit/Training/find-scholarships.aspx
        ?curPage={n}&keyword=&pagesize=500

Each result row carries: scholarship name (+ a numeric scholarshipId + detail URL),
organization, purpose, level of study, award amount, and deadline. We page through
all results at 500/page (~19 pages) and write:
  - Data/sources/scholarships/careeronestop_scholarships.json (normalized records)

Run:  python3 Data/fetch_careeronestop_scholarships.py
"""
from __future__ import annotations

import json
import re
import time
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup  # type: ignore

OUT_DIR = Path(__file__).resolve().parent / "sources" / "scholarships"
BASE = "https://www.careeronestop.org/Toolkit/Training/find-scholarships.aspx"
DETAIL = "https://www.careeronestop.org/Toolkit/Training/find-scholarships-detail.aspx"
PAGE_SIZE = 500
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", "ignore")


def _clean(s: str | None) -> str | None:
    if s is None:
        return None
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


def _after(cell, label: str) -> str | None:
    """The Name cell stacks 'Organization:' and 'Purposes:' as inline labels;
    pull the text that follows a given label within the cell."""
    txt = cell.get_text(" ", strip=True)
    m = re.search(re.escape(label) + r"\s*:?\s*(.*?)(?:Organization:|Purposes?:|$)", txt)
    return _clean(m.group(1)) if m else None


def _cell_by_header(row, header_id: str) -> str | None:
    """Map a row cell by its `headers` attribute (robust to column re-order).
    Columns: thAN=name, thLOS=level, thAT=award type, thAA=amount, thD=deadline."""
    td = row.find("td", attrs={"headers": [header_id]}) or row.find(
        "td", attrs={"headers": header_id}
    )
    return _clean(td.get_text(" ", strip=True)) if td else None


def _parse_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[dict] = []
    for a in soup.select("a[href*='find-scholarships-detail.aspx']"):
        href = a.get("href", "")
        m = re.search(r"scholarshipId=(\d+)", href)
        if not m:
            continue
        sid = m.group(1)
        row = a.find_parent("tr")
        if row is None:
            continue
        name_cell = row.find("td", attrs={"headers": ["thAN"]}) or row.find_all("td")[0]
        out.append(
            {
                "id": sid,
                "name": _clean(a.get_text()),
                "organization": _after(name_cell, "Organization"),
                "purpose": _after(name_cell, "Purposes") or _after(name_cell, "Purpose"),
                "level_of_study": _cell_by_header(row, "thLOS"),
                "award_type": _cell_by_header(row, "thAT"),
                "award_amount": _cell_by_header(row, "thAA"),
                "deadline": _cell_by_header(row, "thD"),
                "url": f"{DETAIL}?scholarshipId={sid}",
                "source": "careeronestop_scholarship_finder",
            }
        )
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    first = _get(f"{BASE}?curPage=1&keyword=&pagesize={PAGE_SIZE}&newsearch=true")
    total_m = re.search(r"([0-9,]+)\s+scholarships", first)
    total = int(total_m.group(1).replace(",", "")) if total_m else 0
    pages = max(1, -(-total // PAGE_SIZE)) if total else 1
    print(f"total scholarships: {total} → {pages} page(s) at {PAGE_SIZE}/page")

    by_id: dict[str, dict] = {}
    for r in _parse_page(first):
        by_id[r["id"]] = r
    for p in range(2, pages + 1):
        html = _get(f"{BASE}?curPage={p}&keyword=&pagesize={PAGE_SIZE}&newsearch=true")
        recs = _parse_page(html)
        for r in recs:
            by_id[r["id"]] = r
        print(f"  page {p}/{pages}: +{len(recs)} (total {len(by_id)})")
        time.sleep(0.5)  # be polite

    records = sorted(by_id.values(), key=lambda r: r["name"] or "")
    out = OUT_DIR / "careeronestop_scholarships.json"
    out.write_text(json.dumps(records, indent=2, ensure_ascii=False))
    print(f"Wrote {len(records)} scholarships → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
