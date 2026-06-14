#!/usr/bin/env python3
"""Generate uw_madison_ipeds_catalog.py with UW-Madison school mapping."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.generate_ipeds_catalog import CREDENTIAL_MAP, fetch_programs, slugify  # noqa: E402

CALS = "College of Agricultural and Life Sciences"
BUSINESS = "Wisconsin School of Business"
EDUCATION = "School of Education"
ENGINEERING = "College of Engineering"
HUMAN_ECOLOGY = "School of Human Ecology"
LAW = "Law School"
LETTERS = "College of Letters and Science"
CDIS = "School of Computer, Data and Information Sciences"
JOURNALISM = "School of Journalism and Mass Communication"
SOCIAL_WORK = "School of Social Work"
MEDICINE = "School of Medicine and Public Health"
NURSING = "School of Nursing"
NELSON = "Nelson Institute for Environmental Studies"
PHARMACY = "School of Pharmacy"
VET = "School of Veterinary Medicine"


def cip_to_school(cip: str, title: str) -> str:
    t = title.lower()
    prefix = cip[:2]

    if prefix == "22" or "law" in t:
        return LAW
    if cip.startswith("51.12") or cip.startswith("51.14") or cip.startswith("51.22"):
        return MEDICINE
    if "public health" in t or cip.startswith("51.22"):
        return MEDICINE
    if cip.startswith("51.20") or "pharmacy" in t:
        return PHARMACY
    if cip.startswith("51.24") or cip.startswith("01.80") or cip.startswith("01.81") or "veterinary" in t:
        return VET
    if cip.startswith("51.38") or "nursing" in t:
        return NURSING

    if prefix == "52" or "business" in t or "accounting" in t or "finance" in t or "marketing" in t:
        return BUSINESS

    if prefix == "13" or "education" in t or "teaching" in t:
        return EDUCATION

    if prefix == "19" or "human ecology" in t or "consumer" in t or "family" in t:
        return HUMAN_ECOLOGY

    if prefix == "01" or ("agricultural" in t and "engineering" not in t) or "animal science" in t or "food science" in t:
        return CALS

    if prefix == "03" or "environmental" in t or "forestry" in t or "natural resources" in t:
        return NELSON

    if prefix in ("14", "15") or ("engineering" in t and "biomedical" not in t):
        return ENGINEERING

    if prefix == "11" or "computer" in t or "data science" in t or "information science" in t:
        return CDIS

    if cip.startswith("09.") or "journalism" in t or "communication" in t or "media" in t:
        return JOURNALISM

    if cip.startswith("44.07") or "social work" in t:
        return SOCIAL_WORK

    if cip.startswith("44.") or "public administration" in t or "public policy" in t or "public affairs" in t:
        return LETTERS

    return LETTERS


def main() -> None:
    programs = fetch_programs(240444)
    lines = [
        '"""College Scorecard / IPEDS Field-of-Study catalog for University of Wisconsin-Madison (UNITID 240444).',
        "",
        "Generated from College Scorecard Field-of-Study data (2024); each row is one",
        "awarded 4-digit CIP + credential level mapped to its owning UW-Madison school.",
        "Explicit flagship entries in ``uw_madison_profile.PROGRAMS`` take precedence —",
        "this module supplies the breadth-first catalog nodes only.",
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        "_IPEDS_CATALOG: list[tuple] = [",
    ]
    for row in programs:
        school = cip_to_school(row["cip"], row["title"])
        slug = f"uw-madison-{slugify(row['title'])}-{row['dtype'][:2]}"
        if row["dtype"] == "professional":
            slug = f"uw-madison-{slugify(row['title'])}-prof"
        elif row["dtype"] == "certificate":
            slug = f"uw-madison-{slugify(row['title'])}-cert"
        elif row["dtype"] == "bachelors":
            slug = f"uw-madison-{slugify(row['title'])}-bs"
        elif row["dtype"] == "masters":
            slug = f"uw-madison-{slugify(row['title'])}-ms"
        elif row["dtype"] == "phd":
            slug = f"uw-madison-{slugify(row['title'])}-phd"
        desc = (
            f"{row['title']} — a University of Wisconsin-Madison {row['dtype']} program "
            f"offered through the {school}."
        )
        lines.append(
            f"    ({slug!r}, {school!r}, {row['title']!r}, {row['dtype']!r}, "
            f"{row['cip']!r}, {row['dur']}, 'on_campus', {desc!r}),"
        )
    lines.append("]")
    lines.append("")
    out = Path(__file__).resolve().parents[1] / "src/unipaith/data/uw_madison_ipeds_catalog.py"
    out.write_text("\n".join(lines) + "\n")
    print(f"Wrote {len(programs)} rows to {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
