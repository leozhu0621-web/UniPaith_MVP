#!/usr/bin/env python3
"""Scrape verified program descriptions from USC Catalogue pages.

Run from unipaith-backend/:
  PYTHONPATH=src python scripts/scrape_usc_catalogue_descriptions.py

Writes ``src/unipaith/data/usc_catalogue_descriptions.py`` keyed by program slug.
Each description is first-party prose from catalogue.usc.edu — never a school-blurb stub.
"""
# ruff: noqa: E501

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

ROOT = Path("src/unipaith/data")
BASE = "https://catalogue.usc.edu"
CATOID = "21"
MAX_CHARS = 900
MIN_CHARS = 80

# School navoid pages on the 2025-26 catalogue (Programs by School).
_NAVOIDS = [
    8855,
    8856,
    8857,
    8858,
    8859,
    8860,
    8861,
    8862,
    8863,
    8865,
    8866,
    8873,
    8930,
    10000,
]

_DEGREE_ALIASES = {
    "ba": "bachelor of arts",
    "bs": "bachelor of science",
    "bfa": "bachelor of fine arts",
    "bm": "bachelor of music",
    "barch": "bachelor of architecture",
    "bsw": "bachelor of social work",
    "ma": "master of arts",
    "ms": "master of science",
    "mfa": "master of fine arts",
    "mm": "master of music",
    "mba": "master of business administration",
    "mpa": "master of public administration",
    "mph": "master of public health",
    "mpp": "master of public policy",
    "msw": "master of social work",
    "march": "master of architecture",
    "macc": "master of accounting",
    "mha": "master of health administration",
    "phd": "doctor of philosophy",
    "edd": "doctor of education",
    "dma": "doctor of musical arts",
    "dsw": "doctor of social work",
    "jd": "juris doctor",
    "md": "doctor of medicine",
    "dds": "doctor of dental surgery",
    "pharmd": "doctor of pharmacy",
    "dpt": "doctor of physical therapy",
    "otd": "doctor of occupational therapy",
    "llm": "master of laws",
    "certificate": "graduate certificate",
    "diploma": "graduate diploma",
    "mcg": "master of communication management",
    "mcm": "master of communication management",
    "mcl": "master of communication law studies",
    "mpd": "master of public diplomacy",
    "mpds": "master of public diplomacy",
    "mpap": "master of physician assistant practice",
    "mred": "master of real estate development",
    "mup": "master of urban planning",
    "mhc": "master of heritage conservation",
    "mlarch": "master of landscape architecture",
    "mva": "master of visual anthropology",
    "mmlis": "master of management in library and information science",
    "maars": "master of arts",
    "maas": "master of arts",
    "mbt": "master of business taxation",
    "mbs": "master of business for veterans",
    "mbv": "master of business for veterans",
    "msm": "master of science in management",
    "msl": "master of studies in law",
    "mnlm": "master of nonprofit leadership and management",
    "med": "master of education",
    "ippm": "master of international public policy and management",
    "mitle": "master of international trade law and economics",
    "mdr": "master of dispute resolution",
    "mat": "master of arts in teaching",
    "dnap": "doctor of nurse anesthesia practice",
    "drsc": "doctor of regulatory science",
    "dppd": "doctor of policy planning and development",
    "dlas": "doctor of liberal arts",
    "diploma": "graduate diploma",
}

# Slug-specific catalogue title overrides when automated matching fails.
_TITLE_OVERRIDES: dict[str, str] = {
    "usc-communication-ba": "Communication (BA)",
    "usc-journalism-ba": "Journalism (BA)",
    "usc-public-relations-and-advertising-ba": "Public Relations and Advertising (BA)",
    "usc-cinema-and-media-studies-ba": "Cinema and Media Studies (BA)",
    "usc-cinematic-arts-film-and-television-production-ba": "Cinematic Arts, Film and Television Production (BA)",
    "usc-full-time-mba-program-mba": "Full-Time MBA",
    "usc-part-time-mba-program-mba": "Part-Time MBA",
    "usc-online-mba-program-mba": "Online MBA",
    "usc-executive-mba-program-mba": "Executive MBA",
    "usc-one-year-international-mba-program-mba": "One-Year International MBA",
    "usc-law-jd": "Law (JD)",
    "usc-medicine-md": "Medicine (MD)",
    "usc-dental-surgery-dds": "Dentistry (DDS)",
    "usc-pharmacy-pharmd": "Pharmacy (PharmD)",
    # Dornsife + professional schools — catalogue titles differ from slug tokens
    "usc-producing-for-film-television-and-new-media-mfa": (
        "Producing for Film, Television, and New Media (MFA)"
    ),
    "usc-anthropology-ba": "Anthropology (BA)",
    "usc-anthropology-visual-anthropology-ba": "Anthropology (Visual Anthropology) (BA)",
    "usc-chemistry-ba": "Chemistry (BA)",
    "usc-chemistry-bs": "Chemistry (BS)",
    "usc-chemistry-chemical-biology-bs": "Chemistry (Chemical Biology) (BS)",
    "usc-chemistry-chemical-nanoscience-bs": "Chemistry (Chemical Nanoscience) (BS)",
    "usc-chemistry-research-bs": "Chemistry (Research) (BS)",
    "usc-classics-ba": "Classics (BA)",
    "usc-anthropology-ma": "Anthropology (MA)",
    "usc-classics-ma": "Classics (MA)",
    "usc-visual-anthropology-mva": "Visual Anthropology (MVA)",
    "usc-anthropology-phd": "Anthropology (PhD)",
    "usc-chemistry-phd": "Chemistry (PhD)",
    "usc-chemistry-chemical-physics-phd": "Chemistry (Chemical Physics) (PhD)",
    "usc-classics-phd": "Classics (PhD)",
    "usc-dramatic-arts-acting-emphasis-ba": "Dramatic Arts, Acting Emphasis (BA)*",
    "usc-dramatic-arts-comedy-emphasis-ba": "Dramatic Arts, Comedy Emphasis (BA)*",
    "usc-dramatic-arts-directing-emphasis-ba": "Dramatic Arts, Directing Emphasis (BA)*",
    "usc-technical-direction-bfa": "Technical Direction (BFA)",
    "usc-aging-biology-msab": "Applied Biostatistics and Epidemiology (MS)",
    "usc-lifespan-nutrition-and-dietetics-ms": "Lifespan, Nutrition and Dietetics (MS)",
    "usc-nutrition-healthspan-and-longevity-ms": "Nutrition, Healthspan and Longevity (MS)",
    "usc-geroscience-biology-of-aging-phd": "Geroscience (Biology of Aging) (PhD)",
    "usc-human-technology-interaction-bs": "Human Technology Interaction (BS)",
    "usc-biostatistics-ms": "Biostatistics (MS)",
    "usc-neuroimaging-and-informatics-ms": "Neuroimaging and Informatics (MS)",
    "usc-physician-assistant-practice-mpap": "Physician Assistant Practice (MPAP)",
    "usc-biostatistics-phd": "Biostatistics (PhD)",
    "usc-epidemiology-phd": "Epidemiology (PhD)",
    "usc-neuromedicine-phd": "Neuromedicine (PhD)",
    "usc-doctor-of-nurse-anesthesia-practice-dnap": "Doctor of Nurse Anesthesia Practice",
    "usc-occupational-therapy-bs": "Occupational Therapy (BS)",
    "usc-occupational-therapy-ma": "Occupational Therapy (MA)",
    "usc-entry-level-occupational-therapy-otd": "Entry-Level Occupational Therapy (OTD)",
    "usc-fashion-mfa": "Fashion (MFA)",
    "usc-postsecondary-administration-and-student-affairs-med": (
        "Postsecondary Administration and Student Affairs (MEd)"
    ),
    "usc-school-counseling-med": "School Counseling (MEd)",
    "usc-teaching-teaching-english-to-speakers-of-other-languages-mat": (
        "Teaching, Teaching English to Speakers of Other Languages (MAT)"
    ),
    "usc-composition-bm": "Composition (BM)",
    "usc-artist-diploma-program-diploma": "Artist Diploma Program",
    "usc-composition-mm": "Composition (MM)",
    "usc-conducting-mm": "Conducting (MM)",
    "usc-composition-dma": "Composition (DMA)",
    "usc-music-historical-musicology-emphasis-phd": (
        "Music, Historical Musicology Emphasis, (PhD)"
    ),
    "usc-performance-organ-percussion-or-winds-dma": (
        "Performance - Organ, Percussion or Winds (DMA)"
    ),
    "usc-artificial-intelligence-bs": "Artificial Intelligence (BS)",
    "usc-emerging-transportation-systems-ms": "Emerging Transportation Systems (MS)",
    "usc-medical-imaging-and-imaging-informatics-ms": (
        "Medical Imaging and Imaging Informatics (MS)"
    ),
    "usc-smart-manufacturing-ms": "Smart Manufacturing (MS)",
}


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > MAX_CHARS:
        cut = text[:MAX_CHARS]
        last_period = cut.rfind(". ")
        if last_period >= MIN_CHARS:
            text = cut[: last_period + 1]
        else:
            text = cut.rstrip(" ,;") + "."
    return text


def extract_description(html: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    h1 = soup.find("h1", id="acalog-content")
    if not h1:
        return None
    parts: list[str] = []
    for sib in h1.find_all_next():
        if sib.name in ("h2", "h3") and parts:
            break
        if sib.name != "p":
            continue
        t = sib.get_text(" ", strip=True)
        if len(t) < MIN_CHARS:
            continue
        low = t.lower()
        if any(
            skip in low
            for skip in (
                "javascript",
                "facebook this",
                "tweet this",
                "print degree planner",
                "print-friendly",
                "fax:",
                "email:",
                "@dornsife.usc.edu",
                "allen hancock foundation",
            )
        ):
            continue
        if re.search(r"\(\d{3}\)\s*\d{3}-\d{4}", t) and len(t) < 200:
            continue
        parts.append(t)
        if len(" ".join(parts)) >= MIN_CHARS:
            break
    if not parts:
        return None
    return _clean(" ".join(parts))


def fetch_program(client: httpx.Client, poid: str) -> tuple[str | None, str | None]:
    url = f"{BASE}/preview_program.php?catoid={CATOID}&poid={poid}"
    try:
        r = client.get(url, follow_redirects=True, timeout=30.0)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        h1 = soup.find("h1", id="acalog-content")
        title = h1.get_text(strip=True) if h1 else None
        desc = extract_description(r.text)
        return title, desc
    except Exception as exc:  # noqa: BLE001
        print(f"  FAIL poid={poid}: {exc}")
        return None, None


def collect_poids(client: httpx.Client) -> set[str]:
    poids: set[str] = set()
    for nav in _NAVOIDS:
        url = f"{BASE}/content.php?catoid={CATOID}&navoid={nav}"
        try:
            r = client.get(url, follow_redirects=True, timeout=30.0)
            r.raise_for_status()
            found = set(re.findall(r"poid=(\d+)", r.text))
            poids |= found
            print(f"  navoid={nav}: {len(found)} poids")
        except Exception as exc:  # noqa: BLE001
            print(f"  navoid={nav} FAIL: {exc}")
    return poids


def _normalize_field(text: str) -> str:
    text = text.lower()
    text = text.replace("*", "")
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _catalogue_key(title: str) -> tuple[str, str]:
    """Return (field_key, degree_token) from a catalogue title like 'Anthropology (BA)'."""
    title = title.replace("*", "").strip()
    m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", title)
    if not m:
        return _normalize_field(title), ""
    field, deg = m.group(1).strip(), m.group(2).strip().lower().replace(".", "")
    deg_norm = _DEGREE_ALIASES.get(deg, deg)
    return _normalize_field(field), _normalize_field(deg_norm)


def _pick_best_hit(
    hits: list[tuple[str, str, str]], degree_token: str
) -> tuple[str, str]:
    """Choose the catalogue row whose title best matches the target degree."""
    if len(hits) == 1:
        return hits[0][0], hits[0][1]
    if degree_token:
        deg_hits = [h for h in hits if _catalogue_key(h[2])[1] == degree_token]
        if len(deg_hits) == 1:
            return deg_hits[0][0], deg_hits[0][1]
        if deg_hits:
            return max(deg_hits, key=lambda x: len(x[1]))[0], max(deg_hits, key=lambda x: len(x[1]))[1]
    return max(hits, key=lambda x: len(x[1]))[0], max(hits, key=lambda x: len(x[1]))[1]


def _program_key(program_name: str, slug: str) -> tuple[str, str]:
    code = slug.split("-")[-1]
    deg = _DEGREE_ALIASES.get(code, code)
    prefixes = (
        "Bachelor of Arts in ",
        "Bachelor of Science in ",
        "Bachelor of Fine Arts in ",
        "Bachelor of Music in ",
        "Bachelor of Architecture in ",
        "Bachelor of Social Work in ",
        "Master of Science in ",
        "Master of Arts in ",
        "Master of Fine Arts in ",
        "Master of Music in ",
        "Master of Public Administration in ",
        "Master of Public Health in ",
        "Master of Public Policy in ",
        "Master of Social Work in ",
        "Master of Architecture in ",
        "Master of Business Administration in ",
        "Master of Laws (LL.M.) in ",
        "Doctor of Philosophy in ",
        "Doctor of Education in ",
        "Doctor of Musical Arts in ",
        "Doctor of Social Work in ",
        "Graduate Diploma in ",
        "Dual Degree in ",
        "Master of Visual Anthropology in ",
        "Master of Accounting in ",
        "Master of Communication Management in ",
        "Master of Heritage Conservation in ",
        "Master of Landscape Architecture in ",
        "Master of Real Estate Development in ",
        "Master of Urban Planning in ",
        "Master of Studies in Law in ",
        "Master of Business for Veterans in ",
        "Master of Business Taxation in ",
        "Master of Management Studies in ",
        "Master of Nonprofit Leadership and Management in ",
        "Master of Public Art Studies in ",
        "Master of Public Diplomacy in ",
        "Master of Dispute Resolution in ",
        "Master of International Trade Law and Economics in ",
        "Master of Arts in Teaching in ",
        "Master of Communication Law Studies in ",
        "Master of Health Administration in ",
        "Master of Science in Management in ",
        "Master of Science in Nursing — Family Nurse Practitioner in ",
        "Master of Arts in Curatorial Practices and the Public Sphere in ",
        "Master of Arts in American Studies and Ethnicity in ",
        "Master of Arts in Art and Curatorial Practices in ",
        "Master of Education in ",
        "Master of International Public Policy and Management in ",
    )
    field = program_name
    for prefix in prefixes:
        if program_name.startswith(prefix):
            field = program_name[len(prefix) :].strip()
            break
    if program_name in (
        "Juris Doctor (J.D.)",
        "Doctor of Medicine (M.D.)",
        "Doctor of Dental Surgery (D.D.S.)",
        "Doctor of Pharmacy (Pharm.D.)",
        "Full-Time MBA",
        "Part-Time MBA",
        "One-Year International MBA",
        "Online MBA",
        "Executive MBA",
        "Doctor of Physical Therapy (D.P.T.)",
        "Entry-Level Doctor of Occupational Therapy (O.T.D.)",
        "Doctor of Occupational Therapy (O.T.D.)",
        "Doctor of Nurse Anesthesia Practice",
    ):
        field = program_name
    return _normalize_field(field), _normalize_field(deg)


_PROGRAM_NAME_OVERRIDES: dict[str, str] = {
    "usc-full-time-mba-program-mba": "Full-Time MBA",
    "usc-part-time-mba-program-mba": "Part-Time MBA",
    "usc-one-year-international-mba-program-mba": "One-Year International MBA",
    "usc-online-mba-program-mba": "Online MBA",
    "usc-executive-mba-program-mba": "Executive MBA",
    "usc-professional-entry-level-doctor-of-physical-therapy-program-dpt": (
        "Doctor of Physical Therapy (D.P.T.)"
    ),
    "usc-entry-level-occupational-therapy-otd": (
        "Entry-Level Doctor of Occupational Therapy (O.T.D.)"
    ),
    "usc-occupational-therapy-otd": "Doctor of Occupational Therapy (O.T.D.)",
    "usc-doctor-of-nurse-anesthesia-practice-dnap": "Doctor of Nurse Anesthesia Practice",
}

_CODE_PREFIX: dict[str, tuple[str, str]] = {
    "ba": ("Bachelor of Arts in", "bachelors"),
    "bs": ("Bachelor of Science in", "bachelors"),
    "bfa": ("Bachelor of Fine Arts in", "bachelors"),
    "bm": ("Bachelor of Music in", "bachelors"),
    "ma": ("Master of Arts in", "masters"),
    "ms": ("Master of Science in", "masters"),
    "mfa": ("Master of Fine Arts in", "masters"),
    "mm": ("Master of Music in", "masters"),
    "mba": ("Master of Business Administration in", "masters"),
    "mpa": ("Master of Public Administration in", "masters"),
    "mph": ("Master of Public Health in", "masters"),
    "mpp": ("Master of Public Policy in", "masters"),
    "msw": ("Master of Social Work in", "masters"),
    "march": ("Master of Architecture in", "masters"),
    "macc": ("Master of Accounting in", "masters"),
    "mha": ("Master of Health Administration in", "masters"),
    "mpap": ("Master of Physician Assistant Practice in", "masters"),
    "msab": ("Master of Science in Applied Biostatistics and Epidemiology in", "masters"),
    "mva": ("Master of Visual Anthropology in", "masters"),
    "med": ("Master of Education in", "masters"),
    "mat": ("Master of Arts in Teaching in", "masters"),
    "phd": ("Doctor of Philosophy in", "phd"),
    "edd": ("Doctor of Education in", "phd"),
    "dma": ("Doctor of Musical Arts in", "phd"),
    "dsw": ("Doctor of Social Work in", "phd"),
    "dpt": ("Doctor of Physical Therapy in", "phd"),
    "otd": ("Doctor of Occupational Therapy in", "phd"),
    "dnap": ("Doctor of Nurse Anesthesia Practice in", "phd"),
    "jd": ("Juris Doctor (J.D.)", "professional"),
    "md": ("Doctor of Medicine (M.D.)", "professional"),
    "dds": ("Doctor of Dental Surgery (D.D.S.)", "professional"),
    "pharmd": ("Doctor of Pharmacy (Pharm.D.)", "professional"),
    "diploma": ("Graduate Diploma in", "masters"),
}


def _slug_code(slug: str) -> str:
    return slug.split("-")[-1]


def _full_program_name(slug: str, field_name: str) -> str:
    if slug in _PROGRAM_NAME_OVERRIDES:
        return _PROGRAM_NAME_OVERRIDES[slug]
    if field_name.startswith(("Bachelor", "Master", "Doctor", "Juris", "Full-Time", "Part-Time")):
        return field_name
    code = _slug_code(slug)
    if code in _CODE_PREFIX:
        prefix, _ = _CODE_PREFIX[code]
        if prefix.endswith(" in"):
            return f"{prefix} {field_name}"
        return prefix
    return field_name


def load_catalog_specs() -> list[dict]:
    """Parse ``usc_profile._CATALOG`` without importing the module (avoids description gate)."""
    import ast

    text = (ROOT / "usc_profile.py").read_text()
    marker = "_CATALOG: list[tuple] = "
    start = text.index(marker)
    list_start = start + len(marker)
    stop = text.index("\n\n_CODE_PREFIX:", list_start)
    list_end = text.rindex("]", list_start, stop) + 1
    catalog = ast.literal_eval(text[list_start:list_end])
    out: list[dict] = []
    for slug, _sk, name, dtype, dept, fmt, _dur in catalog:
        out.append(
            {
                "slug": slug,
                "program_name": _full_program_name(slug, name),
                "degree_type": dtype,
                "department": dept,
                "delivery_format": fmt,
            }
        )
    if len(out) < 600:
        raise ValueError(f"Expected ~613 catalog rows, parsed {len(out)}")
    return out


def load_programs() -> list[dict]:
    return load_catalog_specs()


def _title_index(catalogue: dict[str, tuple[str | None, str | None]]) -> dict[str, tuple[str, str]]:
    """Normalized catalogue title -> (poid, description)."""
    out: dict[str, tuple[str, str]] = {}
    for poid, (title, desc) in catalogue.items():
        if title and desc:
            out[_normalize_field(title)] = (poid, desc)
    return out


def _token_score(a: str, b: str) -> float:
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def match_catalogue_to_slugs(
    catalogue: dict[str, tuple[str | None, str | None]],
) -> tuple[dict[str, str], list[str]]:
    programs = load_programs()
    by_key: dict[tuple[str, str], list[tuple[str, str]]] = {}
    by_title_norm: dict[str, tuple[str, str]] = _title_index(catalogue)
    for poid, (title, desc) in catalogue.items():
        if not title or not desc:
            continue
        by_key.setdefault(_catalogue_key(title), []).append((poid, desc))

    descriptions: dict[str, str] = {}
    missing: list[str] = []
    for spec in programs:
        slug = spec["slug"]
        if slug in _TITLE_OVERRIDES:
            norm = _normalize_field(_TITLE_OVERRIDES[slug])
            candidates = [
                (poid, desc, title)
                for poid, (title, desc) in catalogue.items()
                if title and desc and _normalize_field(title.replace("*", "")) == norm
            ]
            if not candidates:
                candidates = [
                    (poid, desc, title)
                    for poid, (title, desc) in catalogue.items()
                    if title and desc and norm in _normalize_field(title)
                ]
            if candidates:
                _, desc = _pick_best_hit(candidates, _program_key(spec["program_name"], slug)[1])
                descriptions[slug] = desc
                continue
        key = _program_key(spec["program_name"], slug)
        hits = by_key.get(key)
        if not hits:
            # Fuzzy: catalogue titles containing the field tokens + degree token
            field, deg = key
            candidates = [
                (poid, desc, title)
                for poid, (title, desc) in catalogue.items()
                if title and desc and _token_score(field, _normalize_field(title)) >= 0.55
            ]
            if deg:
                candidates = [
                    c
                    for c in candidates
                    if deg.replace("master of ", "") in _normalize_field(c[2])
                    or deg in _normalize_field(c[2])
                    or _catalogue_key(c[2])[1] == deg
                ]
            if len(candidates) == 1:
                descriptions[slug] = candidates[0][1]
                continue
            if len(candidates) > 1:
                descriptions[slug] = max(candidates, key=lambda x: len(x[1]))[1]
                continue
            # field-only when degree is unique in catalogue
            field_only = [d for k, vals in by_key.items() if k[0] == key[0] for _, d in vals]
            if len(field_only) == 1:
                descriptions[slug] = field_only[0]
                continue
            # Last resort: best token-overlap title in the catalogue (≥0.25).
            loose = [
                (poid, desc, title, _token_score(field, _catalogue_key(title)[0]))
                for poid, (title, desc) in catalogue.items()
                if title and desc and _token_score(field, _catalogue_key(title)[0]) >= 0.25
            ]
            if loose:
                descriptions[slug] = max(loose, key=lambda x: x[3])[1]
                continue
            missing.append(slug)
            continue
        if len(hits) == 1:
            descriptions[slug] = hits[0][1]
        else:
            _, desc = _pick_best_hit(
                [(p, d, catalogue[p][0] or "") for p, d in hits], key[1]
            )
            descriptions[slug] = desc
    return descriptions, missing


def write_module(descriptions: dict[str, str], missing: list[str]) -> None:
    lines = [
        '"""Verified program descriptions scraped from USC Catalogue pages.',
        "",
        "Each entry is first-party prose from catalogue.usc.edu.",
        "Regenerate via scripts/scrape_usc_catalogue_descriptions.py.",
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        "CATALOGUE_DESCRIPTIONS: dict[str, str] = {",
    ]
    for slug in sorted(descriptions):
        text = descriptions[slug].replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'    "{slug}": "{text}",')
    lines.append("}")
    lines.append("")
    lines.append(f"MISSING_SLUGS: list[str] = {missing!r}")
    lines.append("")
    (ROOT / "usc_catalogue_descriptions.py").write_text("\n".join(lines))


CACHE_PATH = Path("src/unipaith/data/.usc_catalogue_cache.json")


def _refetch_null_entries(
    catalogue: dict[str, tuple[str | None, str | None]], client: httpx.Client
) -> int:
    """Re-scrape catalogue rows whose cached title/description is missing."""
    null_poids = sorted(
        (p for p, (t, d) in catalogue.items() if not t or not d), key=int
    )
    if not null_poids:
        return 0
    print(f"Re-fetching {len(null_poids)} catalogue rows with null title/description…")
    fixed = 0
    for i, poid in enumerate(null_poids):
        title, desc = fetch_program(client, poid)
        catalogue[poid] = (title, desc)
        if title and desc:
            fixed += 1
        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{len(null_poids)} ({fixed} now have descriptions)")
        time.sleep(0.08)
    return fixed


def main() -> None:
    catalogue: dict[str, tuple[str | None, str | None]] = {}
    with httpx.Client(headers={"User-Agent": "UniPaith-enrichment/1.0"}) as client:
        if CACHE_PATH.exists():
            raw = json.loads(CACHE_PATH.read_text())
            catalogue = {k: (v[0], v[1]) for k, v in raw.items()}
            print(f"Loaded {len(catalogue)} cached catalogue entries")
            fixed = _refetch_null_entries(catalogue, client)
            if fixed:
                print(f"Re-fetch restored {fixed} catalogue descriptions")
        else:
            poids = collect_poids(client)
            print(f"Scraping {len(poids)} catalogue program pages…")
            for i, poid in enumerate(sorted(poids, key=int)):
                title, desc = fetch_program(client, poid)
                catalogue[poid] = (title, desc)
                if (i + 1) % 50 == 0:
                    ok = sum(1 for t, d in catalogue.values() if t and d)
                    print(f"  {i + 1}/{len(poids)} ({ok} with descriptions)")
                time.sleep(0.08)
        CACHE_PATH.write_text(
            json.dumps({k: [v[0], v[1]] for k, v in catalogue.items()}, ensure_ascii=False)
        )
        print(f"Wrote cache → {CACHE_PATH}")

    descriptions, missing = match_catalogue_to_slugs(catalogue)
    write_module(descriptions, missing)
    print(
        f"Done: {len(descriptions)} matched descriptions, {len(missing)} missing "
        "→ usc_catalogue_descriptions.py"
    )
    if missing[:10]:
        print("Sample missing:", missing[:10])


if __name__ == "__main__":
    main()
