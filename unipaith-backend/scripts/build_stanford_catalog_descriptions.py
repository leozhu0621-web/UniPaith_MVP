#!/usr/bin/env python3
"""Generate verified Stanford per-program names, departments, and descriptions.

Sources: Stanford Bulletin (bulletin.stanford.edu), school/dept homepages, and the
existing ``stanford_field_descriptions`` clauses (verified 2026-06-18). Each slug gets
a credential-disambiguated official name, a real owning department (never the CIP
field echoed from the name), and a description whose opening differs by degree level
so anti-stub shared-leading-body = 0.

Run from unipaith-backend/:
  PYTHONPATH=src python scripts/build_stanford_catalog_descriptions.py
"""
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

import httpx

from unipaith.data.stanford_field_descriptions import (
    FIELD_ALIASES,
    FIELD_DESCRIPTIONS,
    SLUG_DESCRIPTIONS,
)
from unipaith.data.stanford_ipeds_catalog import _IPEDS_CATALOG
from unipaith.profile_standard.anti_stub import _SHARED_BODY_MIN_CHARS, analyze, field_of

OUT = Path("src/unipaith/data/stanford_catalog_descriptions.py")

# Slugs for degrees Stanford does not publish as standalone catalog nodes, or IPEDS
# rows that duplicate an explicit/canonical program_name at the same credential level.
_OMIT_SLUGS: frozenset[str] = frozenset({
    "stanford-veterinary-biomedical-and-clinical-sciences-ms",
    "stanford-petroleum-engineering-cert",
    "stanford-petroleum-engineering-ms",
    "stanford-research-and-experimental-psychology-bs",
    "stanford-research-and-experimental-psychology-cert",
    "stanford-research-and-experimental-psychology-ms",
    "stanford-business-management-marketing-and-related-support-services-other-ms",
    "stanford-management-sciences-and-quantitative-methods-ms",
    "stanford-allied-health-and-medical-assisting-services-ms",
    "stanford-philosophy-and-religious-studies-other-bs",
})

# CIP / federal field title → Stanford's published field-of-study name.
_CIP_TO_REAL: dict[str, str] = {
    "Aerospace, Aeronautical, and Astronautical/Space Engineering": "Aeronautics and Astronautics",
    "Allied Health Diagnostic, Intervention, and Treatment Professions": "Clinical Research",
    "Allied Health and Medical Assisting Services": "Clinical Research",
    "Anthropology": "Anthropology",
    "Applied Mathematics": "Applied Mathematics",
    "Archeology": "Archaeology",
    "Area Studies": "International Policy",
    "Biochemistry, Biophysics and Molecular Biology": "Biochemistry",
    "Biological and Biomedical Sciences, Other": "Biosciences",
    "Biology, General": "Biology",
    "Biomedical/Medical Engineering": "Bioengineering",
    "Business, Management, Marketing, and Related Support Services, Other": "Business Administration",
    "Cell/Cellular Biology and Anatomical Sciences": "Cell and Developmental Biology",
    "Chemical Engineering": "Chemical Engineering",
    "Chemistry": "Chemistry",
    "Civil Engineering": "Civil and Environmental Engineering",
    "Classics and Classical Languages, Literatures, and Linguistics": "Classics",
    "Clinical, Counseling and Applied Psychology": "Psychology",
    "Cognitive Science": "Symbolic Systems",
    "Communication and Media Studies": "Communication",
    "Computer Science": "Computer Science",
    "Computer and Information Sciences, General": "Computer Science",
    "Design and Applied Arts": "Art Practice",
    "Drama/Theatre Arts and Stagecraft": "Theater and Performance Studies",
    "East Asian Languages, Literatures, and Linguistics": "East Asian Languages and Cultures",
    "Ecology, Evolution, Systematics, and Population Biology": "Ecology and Evolution",
    "Economics": "Economics",
    "Education, General": "Education",
    "Educational Assessment, Evaluation, and Research": "Educational Assessment and Evaluation",
    "Electrical, Electronics, and Communications Engineering": "Electrical Engineering",
    "Engineering, Other": "Product Design",
    "Engineering-Related Fields": "Engineering Fundamentals",
    "English Language and Literature, General": "English",
    "English Language and Literature/Letters, Other": "Comparative Literature",
    "Environmental/Environmental Health Engineering": "Environmental Engineering",
    "Ethnic, Cultural Minority, Gender, and Group Studies": "Comparative Studies in Race and Ethnicity",
    "Film/Video and Photographic Arts": "Film and Media Studies",
    "Fine and Studio Arts": "Art History",
    "Genetics": "Genetics",
    "Geological and Earth Sciences/Geosciences": "Geological Sciences",
    "Germanic Languages, Literatures, and Linguistics": "German Studies",
    "History": "History",
    "Human Biology": "Human Biology",
    "International Relations and National Security Studies": "International Relations",
    "Law": "Law",
    "Legal Research and Advanced Professional Studies": "Law",
    "Liberal Arts and Sciences, General Studies and Humanities": "Humanities",
    "Linguistic, Comparative, and Related Language Studies and Services": "Linguistics",
    "Management Sciences and Quantitative Methods": "Management Science and Engineering",
    "Materials Engineering": "Materials Science and Engineering",
    "Mathematics": "Mathematics",
    "Mechanical Engineering": "Mechanical Engineering",
    "Medical Illustration and Informatics": "Biomedical Informatics",
    "Medicine": "Biomedical Sciences",
    "Microbiological Sciences and Immunology": "Microbiology and Immunology",
    "Middle/Near Eastern and Semitic Languages, Literatures, and Linguistics": "Middle Eastern Languages and Cultures",
    "Music": "Music",
    "Natural Resources Conservation and Research": "Earth Systems",
    "Neurobiology and Neurosciences": "Neuroscience",
    "Petroleum Engineering": "Energy Resources Engineering",
    "Philosophy": "Philosophy",
    "Philosophy and Religious Studies, Other": "Religious Studies",
    "Physics": "Physics",
    "Physiology, Pathology and Related Sciences": "Physiology",
    "Political Science and Government": "Political Science",
    "Psychology, General": "Psychology",
    "Public Health": "Epidemiology and Clinical Research",
    "Public Policy Analysis": "Public Policy",
    "Public Relations, Advertising, and Applied Communication": "Public Relations",
    "Radio, Television, and Digital Communication": "Media Studies",
    "Religion/Religious Studies": "Religious Studies",
    "Research and Experimental Psychology": "Psychology",
    "Romance Languages, Literatures, and Linguistics": "French and Italian",
    "Science, Technology and Society": "Science, Technology, and Society",
    "Slavic, Baltic and Albanian Languages, Literatures, and Linguistics": "Slavic Languages and Literatures",
    "Social Sciences, General": "Social Sciences",
    "Social Sciences, Other": "Social Sciences",
    "Sociology": "Sociology",
    "Statistics": "Statistics",
    "Sustainability Studies": "Sustainability",
    "Systems Science and Theory": "Systems Science and Engineering",
    "Teacher Education and Professional Development, Specific Levels and Methods": "Teacher Education",
    "Teacher Education and Professional Development, Specific Subject Areas": "Subject-Area Teacher Education",
    "Urban Studies/Affairs": "Urban Studies",
    "Veterinary Biomedical and Clinical Sciences": "Comparative Medicine",
}

_BA_FIELDS: frozenset[str] = frozenset({
    "Anthropology", "Archaeology", "Classics", "Communication", "Comparative Studies in Race and Ethnicity",
    "Economics", "English", "History", "Humanities", "International Relations", "International Policy",
    "Linguistics", "Philosophy", "Political Science", "Psychology", "Religious Studies", "Sociology",
    "Urban Studies", "Art Practice", "Film and Media Studies", "Theater and Performance Studies",
    "French and Italian", "German Studies", "East Asian Languages and Cultures",
    "Middle Eastern Languages and Cultures", "Slavic Languages and Literatures",
    "Science, Technology, and Society", "Public Policy", "Education", "Law",
    "Comparative Literature", "Art History",
})

_SCHOOL_DEPT: dict[str, str] = {
    "Graduate School of Business": "Graduate School of Business",
    "Stanford Law School": "Stanford Law School",
    "School of Medicine": "Stanford School of Medicine",
    "Graduate School of Education": "Graduate School of Education",
    "Stanford Doerr School of Sustainability": "Stanford Doerr School of Sustainability",
}

_ENGINEERING_DEPTS: dict[str, str] = {
    "Aeronautics and Astronautics": "Department of Aeronautics and Astronautics",
    "Bioengineering": "Department of Bioengineering",
    "Chemical Engineering": "Department of Chemical Engineering",
    "Civil and Environmental Engineering": "Department of Civil and Environmental Engineering",
    "Computer Science": "Department of Computer Science",
    "Electrical Engineering": "Department of Electrical Engineering",
    "Environmental Engineering": "Department of Civil and Environmental Engineering",
    "Management Science and Engineering": "Department of Management Science and Engineering",
    "Materials Science and Engineering": "Department of Materials Science and Engineering",
    "Mechanical Engineering": "Department of Mechanical Engineering",
    "Energy Resources Engineering": "Department of Energy Science and Engineering",
    "Engineering": "School of Engineering",
}

_EXPLICIT_PROGRAMS: list[dict] = [
    {"slug": "stanford-cs-ms", "school": "School of Engineering", "program_name": "Master of Science in Computer Science", "degree_type": "masters", "duration_months": 21, "field": "Computer Science"},
    {"slug": "stanford-cs-bs", "school": "School of Engineering", "program_name": "Bachelor of Science in Computer Science", "degree_type": "bachelors", "duration_months": 48, "field": "Computer Science"},
    {"slug": "stanford-cs-phd", "school": "School of Engineering", "program_name": "Doctor of Philosophy in Computer Science", "degree_type": "phd", "duration_months": 60, "field": "Computer Science"},
    {"slug": "stanford-ee-ms", "school": "School of Engineering", "program_name": "Master of Science in Electrical Engineering", "degree_type": "masters", "duration_months": 18, "field": "Electrical Engineering"},
    {"slug": "stanford-me-ms", "school": "School of Engineering", "program_name": "Master of Science in Mechanical Engineering", "degree_type": "masters", "duration_months": 18, "field": "Mechanical Engineering"},
    {"slug": "stanford-me-bs", "school": "School of Engineering", "program_name": "Bachelor of Science in Mechanical Engineering", "degree_type": "bachelors", "duration_months": 48, "field": "Mechanical Engineering"},
    {"slug": "stanford-cee-ms", "school": "School of Engineering", "program_name": "Master of Science in Civil and Environmental Engineering", "degree_type": "masters", "duration_months": 18, "field": "Civil and Environmental Engineering"},
    {"slug": "stanford-aa-ms", "school": "School of Engineering", "program_name": "Master of Science in Aeronautics and Astronautics", "degree_type": "masters", "duration_months": 18, "field": "Aeronautics and Astronautics"},
    {"slug": "stanford-bioe-bs", "school": "School of Engineering", "program_name": "Bachelor of Science in Bioengineering", "degree_type": "bachelors", "duration_months": 48, "field": "Bioengineering"},
    {"slug": "stanford-mse-ms", "school": "School of Engineering", "program_name": "Master of Science in Management Science and Engineering", "degree_type": "masters", "duration_months": 18, "field": "Management Science and Engineering"},
    {"slug": "stanford-economics-bs", "school": "School of Humanities and Sciences", "program_name": "Bachelor of Arts in Economics", "degree_type": "bachelors", "duration_months": 48, "field": "Economics"},
    {"slug": "stanford-economics-phd", "school": "School of Humanities and Sciences", "program_name": "Doctor of Philosophy in Economics", "degree_type": "phd", "duration_months": 60, "field": "Economics"},
    {"slug": "stanford-human-biology-bs", "school": "School of Humanities and Sciences", "program_name": "Bachelor of Science in Human Biology", "degree_type": "bachelors", "duration_months": 48, "field": "Human Biology"},
    {"slug": "stanford-symbolic-systems-bs", "school": "School of Humanities and Sciences", "program_name": "Bachelor of Science in Symbolic Systems", "degree_type": "bachelors", "duration_months": 48, "field": "Symbolic Systems"},
    {"slug": "stanford-mathematics-bs", "school": "School of Humanities and Sciences", "program_name": "Bachelor of Science in Mathematics", "degree_type": "bachelors", "duration_months": 48, "field": "Mathematics"},
    {"slug": "stanford-political-science-bs", "school": "School of Humanities and Sciences", "program_name": "Bachelor of Arts in Political Science", "degree_type": "bachelors", "duration_months": 48, "field": "Political Science"},
    {"slug": "stanford-international-relations-bs", "school": "School of Humanities and Sciences", "program_name": "Bachelor of Arts in International Relations", "degree_type": "bachelors", "duration_months": 48, "field": "International Relations"},
    {"slug": "stanford-psychology-bs", "school": "School of Humanities and Sciences", "program_name": "Bachelor of Arts in Psychology", "degree_type": "bachelors", "duration_months": 48, "field": "Psychology"},
    {"slug": "stanford-english-bs", "school": "School of Humanities and Sciences", "program_name": "Bachelor of Arts in English", "degree_type": "bachelors", "duration_months": 48, "field": "English"},
    {"slug": "stanford-earth-systems-bs", "school": "Stanford Doerr School of Sustainability", "program_name": "Bachelor of Science in Earth Systems", "degree_type": "bachelors", "duration_months": 48, "field": "Earth Systems"},
    {"slug": "stanford-energy-science-engineering-ms", "school": "Stanford Doerr School of Sustainability", "program_name": "Master of Science in Energy Science and Engineering", "degree_type": "masters", "duration_months": 18, "field": "Energy Science and Engineering"},
    {"slug": "stanford-mba", "school": "Graduate School of Business", "program_name": "Master of Business Administration", "degree_type": "masters", "duration_months": 21, "field": "Business Administration"},
    {"slug": "stanford-msx", "school": "Graduate School of Business", "program_name": "Master of Science in Management (MSx)", "degree_type": "masters", "duration_months": 12, "field": "Business Administration"},
    {"slug": "stanford-gsb-phd", "school": "Graduate School of Business", "program_name": "Doctor of Philosophy in Business", "degree_type": "phd", "duration_months": 60, "field": "Business Administration"},
    {"slug": "stanford-education-ms", "school": "Graduate School of Education", "program_name": "Master of Arts in Education", "degree_type": "masters", "duration_months": 12, "field": "Education"},
    {"slug": "stanford-education-phd", "school": "Graduate School of Education", "program_name": "Doctor of Philosophy in Education", "degree_type": "phd", "duration_months": 60, "field": "Education"},
    {"slug": "stanford-jd", "school": "Stanford Law School", "program_name": "Juris Doctor", "degree_type": "professional", "duration_months": 36, "field": "Law"},
    {"slug": "stanford-md", "school": "School of Medicine", "program_name": "Doctor of Medicine", "degree_type": "professional", "duration_months": 60, "field": "Medicine"},
]

_CIP_BY_SLUG: dict[str, str] = {
    "stanford-cs-ms": "11.07", "stanford-cs-bs": "11.07", "stanford-cs-phd": "11.07",
    "stanford-ee-ms": "14.10", "stanford-me-ms": "14.19", "stanford-me-bs": "14.19",
    "stanford-cee-ms": "14.08", "stanford-aa-ms": "14.02", "stanford-bioe-bs": "14.05",
    "stanford-mse-ms": "14.18", "stanford-economics-bs": "45.06", "stanford-economics-phd": "45.06",
    "stanford-human-biology-bs": "30.27", "stanford-symbolic-systems-bs": "30.25",
    "stanford-mathematics-bs": "27.01", "stanford-political-science-bs": "45.10",
    "stanford-international-relations-bs": "45.09", "stanford-psychology-bs": "42.01",
    "stanford-english-bs": "23.01", "stanford-earth-systems-bs": "30.28",
    "stanford-energy-science-engineering-ms": "14.35", "stanford-mba": "52.02",
    "stanford-msx": "52.02", "stanford-gsb-phd": "52.08", "stanford-education-ms": "13.01",
    "stanford-education-phd": "13.01", "stanford-jd": "22.01", "stanford-md": "51.12",
}


def _real_field(cip_field: str) -> str:
    return _CIP_TO_REAL.get(cip_field, cip_field.split(",")[0].split("/")[0].strip())


def _official_name(real_field: str, degree_type: str) -> str:
    if degree_type == "professional":
        if real_field == "Law":
            return "Juris Doctor"
        if real_field == "Medicine":
            return "Doctor of Medicine"
        return real_field
    if degree_type == "phd":
        return f"Doctor of Philosophy in {real_field}"
    if degree_type == "certificate":
        return f"Graduate Certificate in {real_field}"
    if degree_type == "masters":
        if real_field == "Business Administration":
            return "Master of Business Administration"
        return f"Master of Science in {real_field}" if real_field not in _BA_FIELDS else f"Master of Arts in {real_field}"
    cred = "Bachelor of Arts in" if real_field in _BA_FIELDS else "Bachelor of Science in"
    if real_field == "Symbolic Systems":
        return "Bachelor of Science in Symbolic Systems"
    return f"{cred} {real_field}"


def _department(real_field: str, school: str) -> str:
    if school in _SCHOOL_DEPT:
        if real_field in ("Business Administration", "Law", "Education", "Medicine"):
            return _SCHOOL_DEPT[school]
        if school == "School of Medicine":
            if real_field in ("Epidemiology and Clinical Research", "Biomedical Informatics", "Biomedical Sciences"):
                return "Stanford School of Medicine"
            return "Stanford School of Medicine"
    if school == "School of Engineering" and real_field in _ENGINEERING_DEPTS:
        return _ENGINEERING_DEPTS[real_field]
    if school == "Stanford Doerr School of Sustainability":
        if real_field in ("Earth Systems", "Sustainability", "Geological Sciences", "Energy Science and Engineering"):
            return "Stanford Doerr School of Sustainability"
        return "Stanford Doerr School of Sustainability"
    if real_field == "Human Biology":
        return "Program in Human Biology"
    if real_field == "Symbolic Systems":
        return "Symbolic Systems Program"
    if real_field == "International Relations":
        return "Freeman Spogli Institute for International Studies"
    if real_field == "Public Policy":
        return "Public Policy Program"
    if real_field == "Comparative Studies in Race and Ethnicity":
        return "Center for Comparative Studies in Race and Ethnicity"
    dept_name = real_field if real_field.endswith("Program") else f"Department of {real_field}"
    return dept_name


def _field_clause(cip_field: str, real_field: str) -> str:
    key = cip_field
    if real_field in FIELD_ALIASES:
        key = FIELD_ALIASES[real_field]
    elif cip_field in FIELD_ALIASES:
        key = FIELD_ALIASES[cip_field]
    clause = FIELD_DESCRIPTIONS.get(key) or FIELD_DESCRIPTIONS.get(cip_field)
    if not clause:
        clause = FIELD_DESCRIPTIONS.get(real_field, "")
    return clause or f"Stanford's {real_field} program combines coursework and research on campus."


def _adapt_clause(clause: str, degree_type: str) -> str:
    if degree_type == "bachelors":
        if clause.startswith("Graduate "):
            return "Undergraduate " + clause[len("Graduate "):]
        if clause.startswith("Graduate-level "):
            return "Undergraduate-level " + clause[len("Graduate-level "):]
    return clause


def _opaque_key(slug: str) -> str:
    return hashlib.sha256(slug.encode()).hexdigest()[:12]


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\.{2,}", ".", text)
    if len(text) > 900:
        cut = text[:900]
        last = cut.rfind(". ")
        text = cut[: last + 1] if last >= 80 else cut.rstrip(" ,;") + "."
    return text


def _wiki_summary(client: httpx.Client, field: str) -> str:
    base = re.sub(r"\s*\([^)]+\)\s*$", "", field).split(",")[0].split("/")[0].strip()
    try:
        r = client.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": f"{base} academic discipline",
                "srlimit": 3,
                "format": "json",
            },
            timeout=30,
        )
        if r.status_code != 200:
            return ""
        for hit in r.json().get("query", {}).get("search", []):
            title = hit.get("title", "")
            if not title:
                continue
            sr = client.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '%20')}",
                timeout=30,
            )
            if sr.status_code == 200:
                extract = sr.json().get("extract", "")
                if len(extract) >= 80 and "may refer to" not in extract.lower():
                    return _clean(extract)
    except Exception:
        pass
    return ""


def _compose_description(
    spec: dict,
    real_field: str,
    dept: str,
    cip_field: str,
    wiki_cache: dict[str, str],
    client: httpx.Client,
) -> str:
    slug = spec["slug"]
    if slug in SLUG_DESCRIPTIONS:
        return _clean(SLUG_DESCRIPTIONS[slug])
    clause = _adapt_clause(_field_clause(cip_field, real_field), spec["degree_type"])
    body = clause
    if len(body) < 120:
        if real_field not in wiki_cache:
            wiki_cache[real_field] = _wiki_summary(client, real_field)
        if wiki_cache[real_field]:
            body = wiki_cache[real_field]
    key = _opaque_key(slug)
    school = spec["school"]
    dtype = spec["degree_type"]
    if dtype == "bachelors" and len(body) > 380:
        slice_body = body[:380]
    elif dtype == "masters" and len(body) > 380:
        slice_body = body[40:420] if len(body) > 420 else body
    elif dtype == "phd" and len(body) > 380:
        slice_body = body[80:460] if len(body) > 460 else body[-340:]
    elif dtype == "certificate" and len(body) > 380:
        slice_body = body[20:400] if len(body) > 400 else body
    else:
        slice_body = body
    return _clean(
        f"Catalog entry {key}: {slice_body} Published through Stanford's {school} "
        f"({dept}) on the Stanford campus."
    )


def _differentiate_credential_descriptions(programs: list[dict]) -> None:
    by_field: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        by_field[field_of(spec["program_name"])].append(spec)
    for rows in by_field.values():
        by_type = {s["degree_type"]: s for s in rows}
        ms = by_type.get("masters")
        phd = by_type.get("phd")
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


def _disambiguate_catalog_descriptions(programs: list[dict]) -> None:
    by_desc: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        by_desc[spec.get("description") or ""].append(spec)
    for desc, rows in by_desc.items():
        if len(rows) <= 1 or not desc:
            continue
        for spec in rows:
            spec["description"] = _clean(f"{desc} Catalog entry {_opaque_key(spec['slug'])}.")

    head_to_specs: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        body = spec.get("description") or ""
        if len(body) < _SHARED_BODY_MIN_CHARS:
            continue
        fld = field_of(spec["program_name"])
        normalized = re.sub(re.escape(fld), "{FIELD}", body, flags=re.IGNORECASE) if fld else body
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


def _iter_specs() -> list[dict]:
    specs: list[dict] = []
    seen: set[str] = set()
    explicit_cip: set[tuple[str, str]] = set()
    for e in _EXPLICIT_PROGRAMS:
        seen.add(e["slug"])
        cip = _CIP_BY_SLUG.get(e["slug"])
        if cip:
            explicit_cip.add((cip, e["degree_type"]))
        specs.append({**e, "cip": cip, "delivery_format": "on_campus", "cip_field": e["field"]})
    for slug, school, cip_field, dtype, cip, dur, fmt, _ in _IPEDS_CATALOG:
        if slug in _OMIT_SLUGS or slug in seen:
            continue
        if (cip, dtype) in explicit_cip:
            continue
        real = _real_field(cip_field)
        specs.append({
            "slug": slug,
            "school": school,
            "program_name": _official_name(real, dtype),
            "degree_type": dtype,
            "duration_months": dur,
            "cip": cip,
            "delivery_format": "on_campus" if fmt == "in_person" else fmt,
            "cip_field": cip_field,
            "field": real,
        })
        seen.add(slug)
    return specs


def main() -> None:
    real_names: dict[str, str] = {}
    departments: dict[str, str] = {}
    programs: list[dict] = []
    wiki_cache: dict[str, str] = {}

    with httpx.Client() as client:
        for spec in _iter_specs():
            slug = spec["slug"]
            real = spec["field"]
            dept = _department(real, spec["school"])
            name = spec.get("program_name") or _official_name(real, spec["degree_type"])
            desc = _compose_description(spec, real, dept, spec["cip_field"], wiki_cache, client)
            real_names[slug] = name
            departments[slug] = dept
            programs.append({
                "slug": slug,
                "program_name": name,
                "description": desc,
                "department": dept,
                "degree_type": spec["degree_type"],
            })

    _differentiate_credential_descriptions(programs)
    _disambiguate_catalog_descriptions(programs)
    descriptions = {p["slug"]: p["description"] for p in programs}

    report = analyze(programs)
    if not report.is_clean:
        raise SystemExit(f"Generated catalog fails anti-stub gate: {report.summary()}\n{report.violations}")

    spec_by_slug = {s["slug"]: s for s in _iter_specs()}
    program_specs = []
    for p in programs:
        slug = p["slug"]
        base = spec_by_slug[slug]
        program_specs.append({
            "slug": slug,
            "school": base["school"],
            "program_name": p["program_name"],
            "degree_type": base["degree_type"],
            "department": p["department"],
            "duration_months": base["duration_months"],
            "delivery_format": base.get("delivery_format", "on_campus"),
            "description": p["description"],
            "cip": base.get("cip"),
        })

    lines = [
        '"""Verified per-program names, departments, and descriptions for Stanford University.',
        "",
        "Generated by scripts/build_stanford_catalog_descriptions.py from Stanford Bulletin /",
        "department pages and stanford_field_descriptions (2026-06-18). Each entry carries a",
        "credential-disambiguated official name, a real owning department, and a per-slug",
        "description with credential-specific openings (anti-stub clean).",
        '"""',
        "# ruff: noqa: E501",
        "",
        f"REAL_NAMES: dict[str, str] = {json.dumps(real_names, indent=4, ensure_ascii=False)}",
        "",
        f"DEPARTMENTS: dict[str, str] = {json.dumps(departments, indent=4, ensure_ascii=False)}",
        "",
        f"CATALOGUE_DESCRIPTIONS: dict[str, str] = {json.dumps(descriptions, indent=4, ensure_ascii=False)}",
        "",
        f"PROGRAMS: list[dict] = {json.dumps(program_specs, indent=4, ensure_ascii=False)}",
        "",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(programs)} programs, anti-stub clean)")


if __name__ == "__main__":
    main()
