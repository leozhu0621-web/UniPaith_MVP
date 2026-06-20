#!/usr/bin/env python3
"""Generate uf_ipeds_catalog.py with University of Florida school mapping."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.generate_ipeds_catalog import fetch_programs, slugify  # noqa: E402

CALS = "College of Agricultural and Life Sciences"
ARTS = "College of the Arts"
BUSINESS = "Warrington College of Business"
DENTISTRY = "College of Dentistry"
DCP = "College of Design, Construction and Planning"
EDUCATION = "College of Education"
ENGINEERING = "Herbert Wertheim College of Engineering"
HHP = "College of Health and Human Performance"
JOURNALISM = "College of Journalism and Communications"
LAW = "Levin College of Law"
CLAS = "College of Liberal Arts and Sciences"
MEDICINE = "College of Medicine"
NURSING = "College of Nursing"
PHARMACY = "College of Pharmacy"
PHHP = "College of Public Health and Health Professions"
VET = "College of Veterinary Medicine"


def cip_to_school(cip: str, title: str) -> str:
    t = title.lower()
    prefix = cip[:2]

    if prefix == "22" or "law" in t:
        return LAW
    if cip.startswith("51.06") or "dentistry" in t or "dental" in t:
        return DENTISTRY
    if cip.startswith("51.12") or cip.startswith("51.14") or (
        "medicine" in t and "veterinary" not in t and "dental" not in t
    ):
        return MEDICINE
    if "public health" in t or cip.startswith("51.22"):
        return PHHP
    if cip.startswith("51.20") or "pharmacy" in t:
        return PHARMACY
    if cip.startswith("51.24") or cip.startswith("01.80") or cip.startswith("01.81") or "veterinary" in t:
        return VET
    if cip.startswith("51.38") or "nursing" in t:
        return NURSING

    if prefix == "01" or ("agricultural" in t and "engineering" not in t and "business" not in t) or "animal science" in t or "food science" in t:
        return CALS

    if prefix == "52" or ("business" in t and "agricultural" not in t) or "accounting" in t or "finance" in t or "marketing" in t:
        return BUSINESS

    if prefix == "13" or "education" in t or "teaching" in t:
        return EDUCATION

    if prefix == "04" or "architecture" in t or "interior design" in t or "landscape" in t:
        return DCP
    if prefix == "15" and "construction" in t:
        return DCP
    if prefix == "03" and "environmental" not in t:
        return CALS

    if prefix in ("14", "15") or ("engineering" in t and "biomedical" not in t):
        return ENGINEERING
    if cip.startswith("14.09") or "computer" in t or "information science" in t:
        return ENGINEERING

    if prefix == "45" or "geography" in t or "cartography" in t or "political science" in t:
        return CLAS

    if prefix == "50" or "music" in t or "dance" in t or "theatre" in t or "theater" in t or (
        " art" in f" {t}" or t.startswith("art ")
    ):
        if "communication" in t or "journalism" in t or "media" in t:
            return JOURNALISM
        return ARTS

    if cip.startswith("09.") or "journalism" in t or "telecommunication" in t:
        return JOURNALISM

    if prefix == "31" or "kinesiology" in t or "sport" in t or "exercise" in t or "recreation" in t:
        return HHP

    if cip.startswith("51.") and prefix != "51":
        return PHHP

    return CLAS


def main() -> None:
    programs = fetch_programs(134130)
    lines = [
        '"""College Scorecard / IPEDS Field-of-Study catalog for University of Florida (UNITID 134130).',
        "",
        "Generated from College Scorecard Field-of-Study data (2024); each row is one",
        "awarded 4-digit CIP + credential level mapped to its owning UF college.",
        "Explicit flagship entries in ``uf_profile.PROGRAMS`` take precedence —",
        "this module supplies the breadth-first catalog nodes only.",
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        "_IPEDS_CATALOG: list[tuple] = [",
    ]
    for row in programs:
        school = cip_to_school(row["cip"], row["title"])
        slug = f"uf-{slugify(row['title'])}-{row['dtype'][:2]}"
        if row["dtype"] == "professional":
            slug = f"uf-{slugify(row['title'])}-prof"
        elif row["dtype"] == "certificate":
            slug = f"uf-{slugify(row['title'])}-cert"
        elif row["dtype"] == "bachelors":
            slug = f"uf-{slugify(row['title'])}-bs"
        elif row["dtype"] == "masters":
            slug = f"uf-{slugify(row['title'])}-ms"
        elif row["dtype"] == "phd":
            slug = f"uf-{slugify(row['title'])}-phd"
        desc = (
            f"{row['title']} — a University of Florida {row['dtype']} program "
            f"offered through the {school}."
        )
        lines.append(
            f"    ({slug!r}, {school!r}, {row['title']!r}, {row['dtype']!r}, "
            f"{row['cip']!r}, {row['dur']}, 'on_campus', {desc!r}),"
        )
    lines.append("]")
    lines.append("")
    out = Path(__file__).resolve().parents[1] / "src/unipaith/data/uf_ipeds_catalog.py"
    out.write_text("\n".join(lines) + "\n")
    print(f"Wrote {len(programs)} rows to {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
