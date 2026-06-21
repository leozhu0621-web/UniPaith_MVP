#!/usr/bin/env python3
"""Fetch IPEDS admissions (Urban Education Data Portal) into a committed JSONL seed.

Pulls the admissions FUNNEL totals (sex=99) for one year and distills per-institution
{applied, admitted, enrolled, admit_rate, yield_rate}. The API is the source of record
(catalog: urban-education-data-portal-ipeds); the committed seed ships in the backend image.

    python3 Data/tools/build_reference_ipeds_seed.py            # default year 2022
    python3 Data/tools/build_reference_ipeds_seed.py --year 2022
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "unipaith-backend", "src"))

from unipaith.services.reference_ipeds_ingest import ipeds_admissions_record  # noqa: E402

DEFAULT_OUT = os.path.join(REPO, "unipaith-backend/data/reference/ref_ipeds_admissions.jsonl")
BASE = "https://educationdata.urban.org/api/v1/college-university/ipeds/admissions-enrollment"


def fetch_all(year: int) -> list[dict]:
    """Fetch every page of the sex=99 (total) admissions rows for a year."""
    url = f"{BASE}/{year}/?sex=99"
    out: list[dict] = []
    while url:
        req = urllib.request.Request(url, headers={"User-Agent": "unipaith-reference/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 - trusted gov data host
            payload = json.load(resp)
        out.extend(payload.get("results", []))
        url = payload.get("next")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2022)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    rows = fetch_all(args.year)
    n = 0
    with open(args.out, "w", encoding="utf-8") as fh:
        for row in rows:
            rec = ipeds_admissions_record(row)
            if rec is None:
                continue
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    print(f"wrote {n} IPEDS admissions records (year {args.year}) -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
