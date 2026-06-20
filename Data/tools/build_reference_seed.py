#!/usr/bin/env python3
"""Distill the local College Scorecard institution CSV into a committed JSONL seed.

Run locally (needs the raw CSV under Data/sources/, which is git-ignored). Idempotent.
The output JSONL (~3-4 MB, public-domain) is committed and ships in the backend Docker
image; the loader (scripts/seed_reference_institutions.py) reads it in any environment.

    python3 Data/tools/build_reference_seed.py
    python3 Data/tools/build_reference_seed.py --csv /path/to/Institution.csv --out /path/out.jsonl

Decoding logic is shared with the loader via unipaith.services.reference_ingest.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))  # Data/tools
REPO = os.path.dirname(os.path.dirname(HERE))  # repo root
sys.path.insert(0, os.path.join(REPO, "unipaith-backend", "src"))

from unipaith.services.reference_ingest import csv_row_to_record  # noqa: E402

DEFAULT_CSV = os.path.join(
    REPO, "Data/sources/college-scorecard/institution/Most-Recent-Cohorts-Institution.csv"
)
DEFAULT_DICT = os.path.join(REPO, "Data/dictionaries/college-scorecard.fields.json")
DEFAULT_OUT = os.path.join(
    REPO, "unipaith-backend/data/reference/reference_institutions.jsonl"
)


def read_vintage(dict_path: str) -> str | None:
    try:
        with open(dict_path, encoding="utf-8") as fh:
            return json.load(fh)["_meta"].get("version")
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=DEFAULT_CSV)
    ap.add_argument("--dict", dest="dict_path", default=DEFAULT_DICT)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    if not os.path.exists(args.csv):
        print(f"ERROR: raw CSV not found: {args.csv}", file=sys.stderr)
        return 1

    csv.field_size_limit(10_000_000)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    vintage = read_vintage(args.dict_path)
    n = 0
    with open(args.csv, newline="", encoding="utf-8", errors="replace") as fh, open(
        args.out, "w", encoding="utf-8"
    ) as out:
        for row in csv.DictReader(fh):
            rec = csv_row_to_record(row)
            if rec.get("unitid") is None or not rec.get("name"):
                continue
            rec["source_vintage"] = vintage
            # drop null keys to keep the committed seed small; the loader uses
            # dict.get(col) so missing keys load as NULL.
            rec = {k: v for k, v in rec.items() if v is not None}
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    print(f"wrote {n} institutions -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
