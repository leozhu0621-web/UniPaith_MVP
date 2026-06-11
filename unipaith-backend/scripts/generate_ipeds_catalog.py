#!/usr/bin/env python3
"""Generate ``<univ>_ipeds_catalog.py`` from College Scorecard Field-of-Study data."""

from __future__ import annotations

import argparse
import json
import re
import urllib.request


CREDENTIAL_MAP = {
    1: ("certificate", 12),
    2: ("certificate", 12),
    3: ("bachelors", 48),
    5: ("masters", 24),
    6: ("certificate", 12),
    7: ("phd", 60),
    8: ("certificate", 12),
    17: ("certificate", 12),
    18: ("certificate", 12),
    19: ("professional", 36),
}


def slugify(text: str) -> str:
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:80]


def cip_to_school_princeton(cip: str, title: str) -> str:
    """Map a 4-digit CIP to Princeton's five academic units."""
    prefix = cip[:2]
    if prefix in ("14", "15", "11") and "public" not in title.lower():
        if cip.startswith("44.") or "public administration" in title.lower():
            return "Princeton School of Public and International Affairs"
        return "School of Engineering and Applied Science"
    if prefix in ("44",) or "public" in title.lower() or "policy" in title.lower():
        return "Princeton School of Public and International Affairs"
    if prefix in ("26", "27", "40", "41", "30"):
        return "The Natural Sciences"
    if prefix in ("45", "42", "52", "51", "09"):
        return "The Social Sciences"
    return "The Humanities"


def fetch_programs(unitid: int) -> list[dict]:
    fields = (
        "latest.programs.cip_4_digit.code,"
        "latest.programs.cip_4_digit.title,"
        "latest.programs.cip_4_digit.credential.level,"
        "latest.programs.cip_4_digit.credential.title"
    )
    url = (
        f"https://api.data.gov/ed/collegescorecard/v1/schools"
        f"?id={unitid}&fields={fields}&per_page=1"
    )
    req = urllib.request.Request(url, headers={"X-Api-Key": "DEMO_KEY"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    rows = data["results"][0]["latest.programs.cip_4_digit"]
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        code = row["code"]
        cip = f"{code[:2]}.{code[2:]}"
        level = row["credential"]["level"]
        dtype, dur = CREDENTIAL_MAP.get(level, ("masters", 24))
        key = (cip, dtype)
        if key in seen:
            continue
        seen.add(key)
        title = row["title"].rstrip(".")
        out.append({"cip": cip, "title": title, "dtype": dtype, "dur": dur})
    out.sort(key=lambda r: (r["cip"], r["dtype"]))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unitid", type=int, required=True)
    parser.add_argument("--prefix", required=True, help="slug prefix, e.g. princeton")
    parser.add_argument("--name", required=True, help="display name, e.g. Princeton")
    parser.add_argument("--school-fn", default="cip_to_school_princeton")
    args = parser.parse_args()

    programs = fetch_programs(args.unitid)
    lines = [
        f'"""College Scorecard / IPEDS Field-of-Study catalog for {args.name} (UNITID {args.unitid}).',
        "",
        "Generated from College Scorecard Field-of-Study data (2024); each row is one",
        f"awarded 4-digit CIP + credential level mapped to its owning {args.name} school.",
        f'Explicit flagship entries in ``{args.prefix}_profile.PROGRAMS`` take precedence —',
        "this module supplies the breadth-first catalog nodes only.",
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        "_IPEDS_CATALOG: list[tuple] = [",
    ]
    for row in programs:
        school = cip_to_school_princeton(row["cip"], row["title"])
        slug = f"{args.prefix}-{slugify(row['title'])}-{row['dtype'][:2]}"
        if row["dtype"] == "professional":
            slug = f"{args.prefix}-{slugify(row['title'])}-prof"
        elif row["dtype"] == "certificate":
            slug = f"{args.prefix}-{slugify(row['title'])}-cert"
        elif row["dtype"] == "bachelors":
            slug = f"{args.prefix}-{slugify(row['title'])}-bs"
        elif row["dtype"] == "masters":
            slug = f"{args.prefix}-{slugify(row['title'])}-ms"
        elif row["dtype"] == "phd":
            slug = f"{args.prefix}-{slugify(row['title'])}-phd"
        desc = (
            f"{row['title']} — a {args.name} {row['dtype']} program offered through "
            f"the {school}."
        )
        lines.append(
            f"    ({slug!r}, {school!r}, {row['title']!r}, {row['dtype']!r}, "
            f"{row['cip']!r}, {row['dur']}, 'in_person', {desc!r}),"
        )
    lines.append("]")
    lines.append("")
    print("\n".join(lines))
    print(f"# total rows: {len(programs)}", file=__import__("sys").stderr)


if __name__ == "__main__":
    main()
