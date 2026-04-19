"""Parse NYU Bulletin sitemap into structured program records.

Output: data/nyu/bulletin_programs_full.json - ready for seeding into the
platform via /internal/seed-institutions or a direct bulk-insert path.

Each record has:
    program_name   - derived from URL slug, title-cased
    degree_type    - bachelors / masters / phd / certificate / diploma
    degree_label   - BA / BS / BFA / MA / MS / MFA / MBA / PhD / MAT / etc.
    department     - NYU school name (mapped from bulletin school slug)
    bulletin_url   - source URL for later description fetch
    bulletin_level - undergraduate / graduate

Run:
    unipaith-backend/.venv/bin/python scripts/parse_nyu_bulletin_programs.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SITEMAP_PATH = Path("/tmp/nyu_sitemap.xml")
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "nyu" / "bulletin_programs_full.json"

# School slug -> NYU canonical department name (used in institution.programs.department)
SCHOOL_MAP = {
    "abu-dhabi": "NYU Abu Dhabi",
    "arts": "Tisch School of the Arts",
    "arts-science": "College of Arts & Science",
    "business": "Stern School of Business",
    "culture-education-human-development": "Steinhardt School",
    "dentistry": "College of Dentistry",
    "engineering": "Tandon School of Engineering",
    "global-public-health": "School of Global Public Health",
    "individualized-study": "Gallatin School",
    "law": "School of Law",
    "liberal-studies": "Liberal Studies",
    "medicine-grossman": "Grossman School of Medicine",
    "medicine-long-island": "Grossman Long Island School of Medicine",
    "nursing": "Rory Meyers College of Nursing",
    "professional-studies": "School of Professional Studies",
    "public-service": "Wagner Graduate School of Public Service",
    "shanghai": "NYU Shanghai",
    "social-work": "Silver School of Social Work",
}

# Order matters: longer / more specific suffixes first so we pick the right
# degree-type for dual-degree slugs like "computer-science-engineering-bs-bs".
DEGREE_SUFFIXES: list[tuple[str, str, str]] = [
    # (slug_suffix, degree_type, degree_label)
    ("-ba-bs", "bachelors", "BA/BS"),
    ("-bs-bs", "bachelors", "BS/BS"),
    ("-ba-ba", "bachelors", "BA/BA"),
    ("-ba-mba", "bachelors", "BA/MBA"),
    ("-bs-ms", "bachelors", "BS/MS"),
    ("-bs-msc", "bachelors", "BS/MS"),
    ("-advanced-certificate", "certificate", "Advanced Certificate"),
    ("-graduate-certificate", "certificate", "Graduate Certificate"),
    ("-certificate", "certificate", "Certificate"),
    ("-diploma", "diploma", "Diploma"),
    ("-doctorate", "phd", "Doctorate"),
    ("-edd", "phd", "EdD"),
    ("-jd", "phd", "JD"),
    ("-lld", "phd", "LLD"),
    ("-llm", "masters", "LLM"),
    ("-md-phd", "phd", "MD/PhD"),
    ("-md", "phd", "MD"),
    ("-mfa", "masters", "MFA"),
    ("-mba", "masters", "MBA"),
    ("-mph", "masters", "MPH"),
    ("-mpa", "masters", "MPA"),
    ("-msw", "masters", "MSW"),
    ("-mat", "masters", "MAT"),
    ("-mph-mba", "masters", "MPH/MBA"),
    ("-ms-phd", "phd", "MS/PhD"),
    ("-ma-phd", "phd", "MA/PhD"),
    ("-phd", "phd", "PhD"),
    ("-dds", "phd", "DDS"),
    ("-dnp", "phd", "DNP"),
    ("-bfa", "bachelors", "BFA"),
    ("-bs", "bachelors", "BS"),
    ("-ba", "bachelors", "BA"),
    ("-bm", "bachelors", "BM"),
    ("-bmus", "bachelors", "BMus"),
    ("-ms", "masters", "MS"),
    ("-ma", "masters", "MA"),
    ("-mm", "masters", "MM"),
    ("-mmus", "masters", "MMus"),
    ("-mps", "masters", "MPS"),
    ("-minor", None, "Minor"),  # skipped
]


def parse_slug(slug: str) -> tuple[str, str, str] | None:
    """Return (program_name, degree_type, degree_label) or None to skip."""
    slug = slug.rstrip("/").lower()
    for suffix, dtype, label in DEGREE_SUFFIXES:
        if slug.endswith(suffix):
            name_part = slug[: -len(suffix)]
            if dtype is None:
                return None  # skip minors
            # Title-case, keep acronyms like "nyu" upper-cased
            words = []
            for w in name_part.split("-"):
                if w in {"nyu", "mba", "phd", "ii", "iii", "ai", "ml", "ux", "ui"}:
                    words.append(w.upper())
                elif w in {"and", "of", "in", "the", "for", "with", "at"}:
                    words.append(w)
                else:
                    words.append(w.capitalize())
            name = " ".join(words)
            return name, dtype, label
    return None


def main() -> None:
    if not SITEMAP_PATH.exists():
        raise SystemExit(f"Missing sitemap at {SITEMAP_PATH}. Fetch it first with curl.")
    xml = SITEMAP_PATH.read_text()
    urls = re.findall(r"<loc>([^<]+)</loc>", xml)
    prog_urls = [
        u
        for u in urls
        if "/programs/" in u and not u.endswith("/programs/")
    ]

    records: list[dict] = []
    skipped_minors = 0
    skipped_unknown = 0
    for url in prog_urls:
        m = re.match(
            r"https://bulletins\.nyu\.edu/(undergraduate|graduate)/([^/]+)/programs/(.+?)/?$",
            url,
        )
        if not m:
            skipped_unknown += 1
            continue
        level, school_slug, prog_slug = m.groups()
        dept = SCHOOL_MAP.get(school_slug)
        if not dept:
            skipped_unknown += 1
            continue
        parsed = parse_slug(prog_slug)
        if parsed is None:
            skipped_minors += 1
            continue
        name, dtype, label = parsed
        records.append(
            {
                "program_name": name,
                "degree_type": dtype,
                "degree_label": label,
                "department": dept,
                "bulletin_url": url,
                "bulletin_level": level,
            }
        )

    # Dedupe on (program_name, department, degree_label)
    seen: set[tuple[str, str, str]] = set()
    unique: list[dict] = []
    for r in records:
        key = (r["program_name"], r["department"], r["degree_label"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(unique, indent=2))
    print(f"URLs scanned:      {len(prog_urls)}")
    print(f"Parsed programs:   {len(records)}")
    print(f"Unique programs:   {len(unique)}")
    print(f"Skipped minors:    {skipped_minors}")
    print(f"Skipped (no slug): {skipped_unknown}")
    print(f"Written to:        {OUTPUT_PATH}")

    from collections import Counter
    by_dept = Counter(r["department"] for r in unique)
    by_deg = Counter(r["degree_type"] for r in unique)
    print("\nby department:")
    for d, n in by_dept.most_common():
        print(f"  {n:4d}  {d}")
    print("\nby degree_type:")
    for d, n in by_deg.most_common():
        print(f"  {n:4d}  {d}")


if __name__ == "__main__":
    main()
