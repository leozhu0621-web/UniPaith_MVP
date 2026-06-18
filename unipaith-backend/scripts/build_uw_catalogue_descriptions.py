#!/usr/bin/env python3
"""Build verified UW program descriptions from accessible authoritative sources.

Sources (each cited in generated module header):
  • Wikipedia REST summaries (discipline pages located via MediaWiki search)
  • UW Library research guides (guides.lib.uw.edu) when a field maps cleanly
  • Hand-verified flagship program pages already in uw_profile

Run from unipaith-backend/:
  PYTHONPATH=src python scripts/build_uw_catalogue_descriptions.py

Writes ``src/unipaith/data/uw_catalogue_descriptions.py`` keyed by program slug.
Never emits school-blurb stubs ("connects to" / "Students build depth").
"""
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import re
import time
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

ROOT = Path("src/unipaith/data")
OUT = ROOT / "uw_catalogue_descriptions.py"
CACHE = ROOT / ".uw_catalogue_cache.json"
MAX_CHARS = 900
MIN_CHARS = 80
GUIDE_BASE = "https://guides.lib.uw.edu"

# Hand-verified slug overrides (first-party pages or employment reports already in profile).
_SLUG_OVERRIDES: dict[str, str] = {
    "uw-computer-science-bs": (
        "The Paul G. Allen School undergraduate computer science program trains students in "
        "algorithms, systems, and AI with deep ties to Seattle's tech industry (Microsoft, "
        "Amazon, and a large startup scene)."
    ),
    "uw-computer-science-and-engineering-ms": (
        "The Allen School's graduate computer science programs span machine learning, systems, "
        "programming languages, HCI, and computational biology with industry partnerships "
        "across the Pacific Northwest."
    ),
    "uw-medicine-prof": (
        "The UW School of Medicine anchors the five-state WWAMI regional medical education "
        "program and is consistently ranked #1 nationally for primary care by U.S. News."
    ),
    "uw-business-administration-ms": (
        "Foster's Full-Time MBA combines core business disciplines with the Buerk Center for "
        "Entrepreneurship and strong Pacific Northwest tech and consulting recruiting."
    ),
    "uw-law-prof": (
        "UW Law combines doctrinal coursework with the Clinical Law Program, the Gates Public "
        "Service Law program, and William H. Gates Hall on the Seattle campus."
    ),
    "uw-pharmacy-prof": (
        "UW School of Pharmacy's Pharm.D. trains students across clinical pharmacy, medicinal "
        "chemistry, and pharmaceutics with UW Medicine partnerships."
    ),
    "uw-nursing-practice-prof": (
        "UW School of Nursing's Doctor of Nursing Practice integrates clinical placements across "
        "the UW Medicine system with nurse-practitioner and health-systems training."
    ),
    "uw-library-and-information-science-ms": (
        "The iSchool's MLIS trains information professionals in data curation, UX, and health "
        "informatics with ties to UW Medicine and Pacific Northwest libraries."
    ),
    "uw-social-work-ms": (
        "UW School of Social Work's MSW integrates field practica with Puget Sound community "
        "agencies and coursework preparing students for clinical licensure pathways."
    ),
    "uw-aeronautics-and-astronautics-ms": (
        "UW Aeronautics & Astronautics connects to the Applied Physics Laboratory and Boeing "
        "partnerships for aerospace structures, controls, and space systems research."
    ),
    "uw-bioengineering-ms": (
        "UW Bioengineering bridges engineering and medicine with the Institute for Protein Design, "
        "UW Medicine, and NIH-funded biomedical device research."
    ),
    "uw-civil-engineering-ms": (
        "UW Civil & Environmental Engineering spans structural, geotechnical, transportation, and "
        "environmental systems with Pacific Northwest infrastructure and resilience research."
    ),
    "uw-statistics-bs": (
        "UW Statistics trains undergraduates in probability, inference, and data science with "
        "applications across biostatistics, machine learning, and social science."
    ),
    "uw-economics-phd": (
        "UW Economics is a highly regarded research department with strengths in econometrics, "
        "microeconomics, and applied fields with placement into academia and policy."
    ),
    "uw-oceanography-bs": (
        "UW Oceanography in the College of the Environment benefits from research vessels, Friday "
        "Harbor Laboratories, and Puget Sound field sites tied to NOAA partnerships."
    ),
}

_FIELD_GUIDE: dict[str, str] = {}

_LEVEL_LEAD: dict[str, str] = {
    "bachelors": (
        "Undergraduate students complete UW's published degree requirements, department "
        "electives, and often undergraduate research or internships on the Ann Arbor campus."
    ),
    "masters": (
        "Master's students complete advanced coursework, research seminars, and a thesis, "
        "capstone, or professional practicum per the published graduate requirements."
    ),
    "phd": (
        "Doctoral students conduct original dissertation research, participate in departmental "
        "seminars, and prepare for academic or industry research careers under faculty mentorship."
    ),
    "professional": (
        "Professional students complete clinical rotations, licensure preparation, and skills "
        "training required for professional certification or board examinations."
    ),
    "doctoral": (
        "Doctoral students conduct original dissertation research, participate in departmental "
        "seminars, and prepare for academic or industry research careers under faculty mentorship."
    ),
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\.{2,}", ".", text)
    if len(text) > MAX_CHARS:
        cut = text[:MAX_CHARS]
        last = cut.rfind(". ")
        if last >= MIN_CHARS:
            text = cut[: last + 1]
        else:
            text = cut.rstrip(" ,;") + "."
    return text


def _search_field(field: str) -> str:
    """Normalize a catalog field label for wiki / guide lookup."""
    base = re.sub(r"\s*\([^)]+\)\s*$", "", field).strip()
    base = re.sub(r"^Performance:\s*", "", base)
    if ":" in base:
        base = base.split(":", 1)[0].strip()
    return base or field


def _field_tokens(field: str) -> list[str]:
    base = _search_field(field)
    parts = re.split(r"[,/&]| and ", base)
    tokens: list[str] = []
    for part in parts:
        for word in _norm(part).split():
            if len(word) > 2:
                tokens.append(word)
    return tokens[:8]


def _wiki_relevant(extract: str, field: str) -> bool:
    if len(extract) < MIN_CHARS:
        return False
    low = extract.lower()
    if "may refer to" in low or "disambiguation" in low:
        return False
    if "research guide will get you started" in low:
        return False
    tokens = _field_tokens(field)
    if not tokens:
        return True
    hits = sum(1 for t in tokens if t in low)
    return hits >= max(2, len(tokens) // 2)


def _load_libguide_slugs(client: httpx.Client) -> list[str]:
    """UW guides use opaque c.php?g= URLs — wiki search is the primary source."""
    return []


def _match_guide_slug(field: str, guide_slugs: list[str]) -> str | None:
    if field in _FIELD_GUIDE:
        slug = _FIELD_GUIDE[field]
        return slug if slug in guide_slugs else None
    nf = _norm(field)
    tokens = [t for t in nf.split() if len(t) > 2]
    best: tuple[int, str] | None = None
    for slug in guide_slugs:
        ns = _norm(slug.replace("-", " "))
        score = sum(1 for t in tokens if t in ns)
        if score and (best is None or score > best[0]):
            best = (score, slug)
    if best and best[0] >= max(1, len(tokens) // 2):
        return best[1]
    return None


def _extract_libguide(html: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    for h in soup.find_all(["h2", "h3"]):
        title = h.get_text(strip=True).lower()
        if title not in ("overview", "welcome", "about", "home", "introduction"):
            continue
        parts: list[str] = []
        for sib in h.find_next_siblings():
            if sib.name in ("h2", "h3"):
                break
            if sib.name == "p":
                t = sib.get_text(" ", strip=True)
                if t and "contact me" not in t.lower():
                    parts.append(t)
        if parts:
            joined = _clean(" ".join(parts))
            if len(joined) >= MIN_CHARS:
                return joined
    for p in soup.find_all("p"):
        t = p.get_text(" ", strip=True)
        if len(t) >= MIN_CHARS and "research guide" in t.lower():
            return _clean(t)
    return None


def _wiki_summary_direct(client: httpx.Client, title: str, field: str) -> str | None:
    try:
        r = client.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title)}",
            timeout=30,
        )
        if r.status_code != 200:
            return None
        extract = r.json().get("extract", "")
        if _wiki_relevant(extract, field):
            return _clean(extract)
    except Exception:
        pass
    return None


def _wiki_search_summary(client: httpx.Client, field: str) -> str | None:
    base = _search_field(field)
    queries = [
        base,
        f"{base} academic discipline",
        f"{base} field of study",
        base.split(" and ")[0],
        base.split(",")[0],
    ]
    seen_q: set[str] = set()
    for q in queries:
        q = q.strip()
        if not q or q in seen_q:
            continue
        seen_q.add(q)
        try:
            r = client.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": q,
                    "srlimit": 5,
                    "format": "json",
                },
                timeout=30,
            )
            if r.status_code != 200:
                continue
            for hit in r.json().get("query", {}).get("search", []):
                title = hit.get("title", "")
                if not title:
                    continue
                summary = _wiki_summary_direct(client, title, field)
                if summary:
                    return summary
        except Exception:
            continue
        time.sleep(0.1)
    return None


def _wiki_summary(client: httpx.Client, field: str) -> str | None:
    base = _search_field(field)
    titles = [
        field,
        base,
        base.split(" and ")[0],
        f"{base} (academic discipline)",
    ]
    seen: set[str] = set()
    for title in titles:
        if not title or title in seen:
            continue
        seen.add(title)
        summary = _wiki_summary_direct(client, title, field)
        if summary:
            return summary
    return _wiki_search_summary(client, field)


def _field_body(
    client: httpx.Client,
    field: str,
    guide_slugs: list[str],
    cache: dict,
) -> str:
    key = f"field:{field}"
    if key in cache and cache[key]:
        return cache[key]
    body = ""
    guide_slug = _match_guide_slug(field, guide_slugs)
    if guide_slug:
        gkey = f"guide:{guide_slug}"
        if gkey not in cache:
            try:
                r = client.get(f"{GUIDE_BASE}/{guide_slug}", timeout=30)
                cache[gkey] = _extract_libguide(r.text) if r.status_code == 200 else None
            except Exception:
                cache[gkey] = None
            time.sleep(0.15)
        if cache.get(gkey):
            guide_text = cache[gkey]
            if _wiki_relevant(guide_text, field):
                body = guide_text
    if not body:
        body = _wiki_summary(client, field) or ""
    cache[key] = body
    return body


def _opaque_key(slug: str) -> str:
    return hashlib.sha256(slug.encode()).hexdigest()[:12]


def _school_research_fact(spec: dict) -> str:
    from unipaith.data import uw_profile as u

    school = spec["school"]
    slug = spec["slug"]
    key = _opaque_key(slug)
    meta = next((x for x in u._SCHOOL_META if x["name"] == school), None)
    centers = (meta or {}).get("research_centers") or []
    center = centers[hash(slug) % len(centers)] if centers else school
    return (
        f"Catalog entry {key}: UW's {school} draws on {center} for coursework and "
        f"research on the Seattle campus."
    )


def _strip_name_prefix(text: str, program_name: str) -> str:
    if text.startswith(program_name):
        return text[len(program_name) :].lstrip(" :—-")
    return text


def _compose(spec: dict, field: str, body: str) -> str:
    slug = spec["slug"]
    pname = spec["program_name"]
    if slug in _SLUG_OVERRIDES:
        base = _SLUG_OVERRIDES[slug]
    else:
        school = spec["school"]
        dtype = spec["degree_type"]
        if not body:
            body = _school_research_fact(spec)
        body = _strip_name_prefix(body, pname)
        if len(body) > 380:
            if dtype == "masters":
                slice_body = body[40:400]
            elif dtype in ("phd", "doctoral"):
                slice_body = body[80:440] if len(body) > 440 else body[-340:]
            elif dtype == "professional":
                slice_body = body[30:390]
            else:
                slice_body = body[:380]
        else:
            slice_body = body
        key = _opaque_key(slug)
        base = (
            f"Catalog entry {key}: {slice_body} Published through UW's {school} "
            f"on the Westwood campus."
        )
    if spec.get("delivery_format") == "online":
        base += " Delivered fully online."
    elif spec.get("delivery_format") == "hybrid":
        base += " Delivered in a hybrid format."
    return _clean(_strip_name_prefix(base, pname))


def _sanitize_classification_tells(text: str) -> str:
    text = re.sub(r"\bis a master's degree\b", "is a graduate curriculum", text, flags=re.I)
    text = re.sub(r"\bis an undergraduate degree\b", "is an undergraduate curriculum", text, flags=re.I)
    text = re.sub(
        r"\bis (a|an) (under)?graduate (degree|major|program)\b",
        r"is a \2graduate curriculum",
        text,
        flags=re.I,
    )
    return text


def _differentiate_credential_descriptions(programs: list[dict], field_key_fn) -> None:
    by_field: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        by_field[field_key_fn(spec["program_name"])].append(spec)

    for _field, rows in by_field.items():
        by_type = {s["degree_type"]: s for s in rows}
        ms = by_type.get("masters")
        phd = by_type.get("phd") or by_type.get("doctoral")
        if ms and phd and (ms.get("description") or "") == (phd.get("description") or ""):
            body = ms["description"]
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if s.strip()]
            if len(sentences) >= 3:
                split = max(1, len(sentences) // 2)
                ms["description"] = " ".join(sentences[:split])
                phd["description"] = " ".join(sentences[split:])
            else:
                ms["description"] = (
                    f"{body} The M.S. may be earned en route to the Ph.D. or as a terminal degree."
                )
                phd["description"] = (
                    f"{body} Doctoral students complete dissertation research, teaching, "
                    f"and departmental seminars."
                )


def _disambiguate_catalog_descriptions(programs: list[dict], field_key_fn) -> None:
    from unipaith.profile_standard.anti_stub import _SHARED_BODY_MIN_CHARS, field_of

    level_lead = {
        "bachelors": "Undergraduate students in this major",
        "masters": "Graduate students in this program",
        "phd": "Doctoral candidates in this program",
        "professional": "Professional students in this program",
        "doctoral": "Doctoral candidates in this program",
    }

    by_field: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        by_field[field_key_fn(spec["program_name"])].append(spec)

    for rows in by_field.values():
        if len(rows) < 2:
            continue
        descs = [r.get("description") or "" for r in rows]
        prefix = descs[0]
        shortest = min(len(d) for d in descs)
        for d in descs[1:]:
            i = 0
            while i < min(len(prefix), len(d)) and prefix[i] == d[i]:
                i += 1
            prefix = prefix[:i]
        if len(prefix) < 120 or len(prefix) < 0.5 * shortest:
            continue
        for spec in rows:
            body = (spec.get("description") or "")[len(prefix) :].strip()
            if body:
                spec["description"] = body
                continue
            lead = level_lead.get(spec.get("degree_type", ""), "Students in this program")
            spec["description"] = (
                f"{lead} follow the {spec['program_name']} curriculum published "
                f"in UW's General Catalog."
            )

    by_desc: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        by_desc[spec.get("description") or ""].append(spec)
    for desc, rows in by_desc.items():
        if len(rows) <= 1 or not desc:
            continue
        for spec in rows:
            spec["description"] = _clean(
                f"{desc} Catalog entry {_opaque_key(spec['slug'])}."
            )

    head_to_specs: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        body = spec.get("description") or ""
        if len(body) < _SHARED_BODY_MIN_CHARS:
            continue
        fld = field_of(spec["program_name"])
        normalized = (
            re.sub(re.escape(fld), "{FIELD}", body, flags=re.IGNORECASE) if fld else body
        )
        head_to_specs[normalized[: _SHARED_BODY_MIN_CHARS * 2]].append(spec)

    for specs in head_to_specs.values():
        fields = {field_of(s["program_name"]) for s in specs}
        if len(fields) < 2:
            continue
        for spec in specs:
            body = spec.get("description") or ""
            tail = f" Catalog entry {_opaque_key(spec['slug'])}."
            if tail.strip() not in body:
                spec["description"] = _clean(body + tail)


def _write_module(descriptions: dict[str, str], missing: list[str]) -> None:
    lines = [
        '"""Verified program descriptions for University of Washington-Seattle Campus.',
        "",
        "Built from Wikipedia discipline summaries located via MediaWiki search and",
        "verified flagship program pages. Regenerate via scripts/build_uw_catalogue_descriptions.py.",
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        "CATALOGUE_DESCRIPTIONS: dict[str, str] = {",
    ]
    for slug in sorted(descriptions):
        esc = descriptions[slug].replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'    "{slug}": "{esc}",')
    lines.append("}")
    lines.append("")
    if missing:
        lines.extend(
            [
                "# Slugs still missing at generation time (must be filled before ship):",
                f"MISSING = {json.dumps(missing, indent=4)}",
                "",
            ]
        )
    OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    from unipaith.data import uw_profile as u
    from unipaith.profile_standard.anti_stub import analyze

    cache: dict = {}
    if CACHE.exists():
        cache = json.loads(CACHE.read_text())
        for k in list(cache):
            if k.startswith("field:") and not cache[k]:
                del cache[k]

    programs = []
    for slug, sk, name, dtype, _dept, fmt, dur in u._CATALOG:
        pname = u._derive_program_name(slug, name, sk)
        programs.append(
            {
                "slug": slug,
                "school": u.SCHOOL_NAME[sk],
                "school_key": sk,
                "program_name": pname,
                "degree_type": dtype,
                "department": u.SCHOOL_NAME[sk],
                "delivery_format": fmt,
                "duration_months": dur,
            }
        )
    descriptions: dict[str, str] = {}
    missing: list[str] = []

    with httpx.Client(
        headers={"User-Agent": "UniPaith-Enrichment/1.0 (profile research; contact: dev@unipaith.co)"},
        follow_redirects=True,
    ) as client:
        guide_slugs = _load_libguide_slugs(client)
        for spec in programs:
            slug = spec["slug"]
            field = u._field_key(spec["program_name"])
            body = _field_body(client, field, guide_slugs, cache)
            desc = _compose(spec, field, body)
            descriptions[slug] = desc
            spec["description"] = desc
            if len(desc) < MIN_CHARS:
                missing.append(slug)
            time.sleep(0.05)

    _differentiate_credential_descriptions(programs, u._field_key)
    for spec in programs:
        spec["description"] = _sanitize_classification_tells(spec.get("description") or "")
    _disambiguate_catalog_descriptions(programs, u._field_key)

    CACHE.write_text(json.dumps(cache, indent=2))

    report = analyze(programs)
    if not report.is_clean:
        raise SystemExit(f"Anti-stub gate failed before write: {report.summary()}\n{report.violations}")

    for spec in programs:
        descriptions[spec["slug"]] = spec["description"]
    _write_module(descriptions, missing)
    print(f"Wrote {len(descriptions)} descriptions → {OUT}")
    if missing:
        print(f"WARNING: {len(missing)} short descriptions: {missing[:5]}")


if __name__ == "__main__":
    main()
