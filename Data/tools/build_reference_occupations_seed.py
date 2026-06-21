#!/usr/bin/env python3
"""Distill BLS Employment Projections (Table 1.2) into a committed JSONL seed for ref_occupations.

Run locally (needs Data/sources/bls-onet/EmploymentProjections_occupation_2024-34.xlsx + openpyxl).
Idempotent. The output JSONL is committed and ships in the backend image.

    python3 Data/tools/build_reference_occupations_seed.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))  # Data/tools
REPO = os.path.dirname(os.path.dirname(HERE))  # repo root
sys.path.insert(0, os.path.join(REPO, "unipaith-backend", "src"))

from unipaith.services.reference_occupations_ingest import bls_row_to_occupation  # noqa: E402

DEFAULT_XLSX = os.path.join(
    REPO, "Data/sources/bls-onet/EmploymentProjections_occupation_2024-34.xlsx"
)
DEFAULT_OUT = os.path.join(REPO, "unipaith-backend/data/reference/ref_occupations.jsonl")

# Table 1.2 column indices (verified against the 2024-34 workbook).
COLS = {"title": 0, "soc_code": 1, "occ_type": 2, "employment_k": 3, "growth_pct": 8,
        "wage": 11, "education": 12}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", default=DEFAULT_XLSX)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()
    if not os.path.exists(args.xlsx):
        print(f"ERROR: BLS xlsx not found: {args.xlsx}", file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    wb = openpyxl.load_workbook(args.xlsx, read_only=True, data_only=True)
    ws = wb["Table 1.2"]
    n = 0
    with open(args.out, "w", encoding="utf-8") as out:
        for row in ws.iter_rows(values_only=True):
            if not row or len(row) <= COLS["education"]:
                continue
            clean = {k: row[i] for k, i in COLS.items()}
            rec = bls_row_to_occupation(clean)
            if rec is None:
                continue
            rec = {k: v for k, v in rec.items() if v is not None}
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    wb.close()
    print(f"wrote {n} occupations -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
