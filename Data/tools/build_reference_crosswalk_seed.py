#!/usr/bin/env python3
"""Distill the NCES CIP 2020 <-> SOC 2018 crosswalk (CIP-SOC sheet) into a committed JSONL seed.

Run locally (needs Data/sources/ipeds/CIP2020_SOC2018_Crosswalk.xlsx + openpyxl). Idempotent.

    python3 Data/tools/build_reference_crosswalk_seed.py
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

from unipaith.services.reference_crosswalk_ingest import pair_from_row  # noqa: E402

DEFAULT_XLSX = os.path.join(REPO, "Data/sources/ipeds/CIP2020_SOC2018_Crosswalk.xlsx")
DEFAULT_OUT = os.path.join(REPO, "unipaith-backend/data/reference/ref_cip_soc.jsonl")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", default=DEFAULT_XLSX)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()
    if not os.path.exists(args.xlsx):
        print(f"ERROR: crosswalk xlsx not found: {args.xlsx}", file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    wb = openpyxl.load_workbook(args.xlsx, read_only=True, data_only=True)
    ws = wb["CIP-SOC"]
    header = None
    n = 0
    with open(args.out, "w", encoding="utf-8") as out:
        for row in ws.iter_rows(values_only=True):
            if header is None:
                header = [str(c).strip() if c is not None else "" for c in row]
                continue
            rec = dict(zip(header, row, strict=False))
            pair = pair_from_row(rec)
            if pair is None:
                continue
            out.write(json.dumps(pair, ensure_ascii=False) + "\n")
            n += 1
    wb.close()
    print(f"wrote {n} crosswalk pairs -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
