#!/usr/bin/env python3
"""Distill the NCES CIP 2020 dictionary into a committed JSONL seed for ref_majors.

Run locally (needs Data/sources/ipeds/CIPCode2020.csv). Idempotent. The output JSONL is
committed and ships in the backend image; the loader seeds any environment from it.

    python3 Data/tools/build_reference_majors_seed.py
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

from unipaith.services.reference_majors_ingest import cip_row_to_major  # noqa: E402

DEFAULT_CSV = os.path.join(REPO, "Data/sources/ipeds/CIPCode2020.csv")
DEFAULT_OUT = os.path.join(REPO, "unipaith-backend/data/reference/ref_majors.jsonl")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=DEFAULT_CSV)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()
    if not os.path.exists(args.csv):
        print(f"ERROR: CIP CSV not found: {args.csv}", file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    n = 0
    with open(args.csv, newline="", encoding="utf-8-sig") as fh, open(
        args.out, "w", encoding="utf-8"
    ) as out:
        for row in csv.DictReader(fh):
            rec = cip_row_to_major(row)
            if rec is None:
                continue
            rec = {k: v for k, v in rec.items() if v is not None}
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    print(f"wrote {n} majors -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
