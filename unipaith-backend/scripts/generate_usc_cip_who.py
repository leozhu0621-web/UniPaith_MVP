#!/usr/bin/env python3
"""Generate usc_cip_who.py — run from unipaith-backend with PYTHONPATH=src."""
# ruff: noqa: E501
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from unipaith.data import bu_cip_who as bu
from unipaith.data import cornell_cip_who as cornell
from unipaith.data import usc_profile as usc

majors_by_title: dict[str, str] = {}
majors_4digit: dict[str, str] = {}
ref_path = Path(__file__).resolve().parents[1] / "data/reference/ref_majors.jsonl"
with ref_path.open() as f:
    for line in f:
        m = json.loads(line)
        code, title = m["cip_code"], m["title"].strip()
        tl = title.lower()
        majors_by_title[tl] = code
        if re.match(r"^\d{2}\.\d{2}$", code):
            majors_4digit[tl] = code
        if ", General" in title:
            majors_by_title[title.replace(", General", "").strip().lower()] = code


def lookup_cip(field: str) -> str | None:
    if field in bu.CIP_BY_FIELD:
        return bu.CIP_BY_FIELD[field]
    if field in USC_CIP_OVERRIDES:
        return USC_CIP_OVERRIDES[field]
    fl = field.lower()
    for key in (fl, fl + ", general"):
        if key in majors_4digit:
            return majors_4digit[key]
        if key in majors_by_title:
            c = majors_by_title[key]
            if re.match(r"^\d{2}\.\d{2}", c):
                return c[:5] if len(c) >= 5 else c
    best = None
    for title, code in majors_4digit.items():
        if fl in title or title in fl:
            if best is None or len(title) < len(best[0]):
                best = (title, code)
    if best:
        return best[1]
    words = set(re.findall(r"[a-z]+", fl))
    best_score, best_code = 0, None
    for title, code in majors_4digit.items():
        score = len(words & set(re.findall(r"[a-z]+", title)))
        if score > best_score and score >= max(2, len(words) // 2):
            best_score, best_code = score, code
    return best_code


# Verified NCES CIP-2020 families for USC catalogue fields not resolved by bu/ref_majors lookup.
USC_CIP_OVERRIDES: dict[str, str] = {
    "Acting, Stage and Screen": "50.0506",
    "Addiction Science": "51.1501",
    "Aging Biology": "26.1101",
    "American Popular Culture": "05.0102",
    "Applied Analytics": "30.7101",
    "Artificial Intelligence for Business": "52.0201",
    "Artist Diploma Program": "50.0901",
    "Arts Leadership": "50.1001",
    "Arts, Technology and the Business of Innovation": "50.9999",
    "Biokinesiology": "51.2308",
    "Biopharmaceutical Sciences": "26.1201",
    "Business Research": "52.0201",
    "Business of Cinematic Arts": "50.0601",
    "Business of Innovation": "52.0701",
    "Central European Studies": "05.0108",
    "Cinematic Arts": "50.0601",
    "Clinical Trial Management": "51.2706",
    "Communication Management": "09.0101",
    "Community Oral Health": "51.0501",
    "Computational Linguistics": "16.0102",
    "Computational Neuroscience": "26.1502",
    "Contemporary Latino and Latin American Studies": "05.0107",
    "Contemporary Teaching Practice": "13.1205",
    "Craniofacial Biology": "51.0501",
    "Curatorial Practices and the Public Sphere": "50.0701",
    "Cyber Security Engineering": "14.0901",
    "Digital Social Media": "09.0901",
    "Dramatic Arts": "50.0501",
    "Educational Counseling": "13.1101",
    "Educational Leadership": "13.0401",
    "Emergency Management": "43.0302",
    "Emerging Transportation Systems": "14.0801",
    "Engineering Management": "14.3501",
    "Entrepreneurship and Innovation": "52.0701",
    "Environmental Risk Analysis": "03.0104",
    "Fashion": "50.0407",
    "Fashion Innovation": "50.0407",
    "Financial Engineering": "14.3501",
    "Food Industry Management Program": "19.0501",
    "Game Art": "50.0411",
    "Geodesign": "04.0301",
    "Geroscience": "26.1101",
    "Global Executive": "52.0201",
    "Global Geodesign": "04.0301",
    "Global Health Studies": "51.2201",
    "Global Health and Human Rights Leadership": "51.2201",
    "Global Studies": "30.2001",
    "Global Supply Chain Management for Executives": "52.0203",
    "Health Behavior Research": "51.2201",
    "Health Promotion and Disease Prevention Studies": "51.2207",
    "Healthcare Decision Analysis": "51.2203",
    "Hospitality and Tourism": "52.0901",
    "Interactive Media": "11.0801",
    "International MBA Program": "52.0201",
    "Italian": "16.0904",
    "Jazz Studies": "50.0904",
    "Jewish Studies": "05.0210",
    "Language Sciences": "16.0101",
    "Latin American and Iberian Cultures, Media and Politics": "05.0107",
    "Lifespan Health": "51.2201",
    "Long Term Care Administration": "51.0701",
    "MBA Program for Professionals and Managers": "52.0201",
    "Management in Sustainability Management": "03.0103",
    "Management of Drug Development": "51.2706",
    "Medical Product Quality": "51.2706",
    "Middle East Studies": "05.0108",
    "Narrative Studies": "23.1302",
    "Non-Governmental Organizations and Social Change": "44.0401",
    "Nutritional Science": "30.1901",
    "Occupational Science": "51.2306",
    "Occupational Therapy": "51.2304",
    "Ocean Sciences": "30.0501",
    "Perfusion Sciences": "51.0909",
    "Physical Biology": "26.1308",
    "Producing for Film, Television, and New Media": "50.0602",
    "Product Development Engineering": "14.3501",
    "Project Management in Global Health and Development": "51.2201",
    "Quantitative Biology": "26.1101",
    "Regulatory Management": "51.2211",
    "Regulatory Science": "26.1201",
    "School Counseling": "13.1101",
    "Screen Scoring": "50.0902",
    "Senior Living Hospitality": "52.0901",
    "Smart Manufacturing": "14.0701",
    "Spanish": "16.0905",
    "Speech-Language Pathology": "51.0203",
    "Sports Leadership": "31.0505",
    "Sustainable Engineering": "14.1401",
    "Teaching in Multiple Subject": "13.1201",
    "Teaching in Single Subject": "13.1205",
    "Technical Direction": "50.0502",
    "Theatrical Design": "50.0504",
    "Themed Entertainment": "50.0102",
    "Translational Biomedical Informatics": "51.2706",
    "Policy, Planning, and Development": "44.0401",
    "Regulatory Science": "26.1201",
    "Longevity Arts and Sciences": "30.9999",
    "Business Taxation": "52.0301",
    "Business Taxation for Working Professionals": "52.0301",
    "Building Science": "14.0801",
    "Business for Veterans": "52.0201",
    "Comparative Law": "22.0201",
    "Dispute Resolution": "22.0201",
    "Health Administration": "51.0701",
    "International Public Policy and Management": "44.0401",
    "International Trade Law and Economics": "52.1301",
    "Landscape Architecture": "04.0601",
    "Management Studies": "52.0201",
    "Library and Information Science": "25.0101",
    "Nonprofit Leadership and Management": "44.0401",
    "Physician Assistant Practice": "51.0912",
    "Planning and Development Studies": "04.0301",
    "Public Diplomacy": "09.0901",
    "Dollinger Master of Real Estate Development": "04.0901",
    "Urban Planning": "04.0301",
    "Urban Planning (Executive MUP Online)": "04.0301",
    "Visual Anthropology": "45.0201",
}


def who_lead(field: str) -> str:
    if field in bu.WHO_BY_FIELD:
        return bu.WHO_BY_FIELD[field]
    if field in cornell.WHO_BY_FIELD:
        return cornell.WHO_BY_FIELD[field]
    fl = field.lower()
    if "nurse practitioner" in fl or "adult-gerontology" in fl:
        return f"Registered nurses advancing to advanced practice as {field.lower()} specialists"
    if fl.startswith("teaching") or "teachers of" in fl or "teacher of" in fl:
        return f"Students preparing to teach in {field.lower()}"
    if " and " in field:
        return f"Students drawn to the intersection of {field.lower()}"
    if "engineering" in fl:
        return f"Students focused on {field.lower()} who want to design and build systems"
    if "education" in fl or "teaching" in fl:
        return f"Students preparing for careers in {field.lower()}"
    if any(x in fl for x in ("business", "finance", "marketing", "management", "accounting", "mba")):
        return f"Students focused on {field.lower()} in organizations and markets"
    if "nursing" in fl:
        return f"Nurses and health professionals focused on {field.lower()}"
    if any(x in fl for x in ("music", "theatre", "theater", "dance", "performance", "acting", "cinematic", "film")):
        return f"Students committed to {field.lower()} as performers, creators, or scholars"
    if any(x in fl for x in ("art", "design", "media", "cinema")):
        return f"Students drawn to {field.lower()} as makers and critical thinkers"
    if any(x in fl for x in ("science", "biology", "chemistry", "physics", "math")):
        return f"Students fascinated by {field.lower()} and how it explains the natural world"
    if any(x in fl for x in ("health", "medical", "clinical", "therapy", "dental", "pharmacy")):
        return f"Students committed to improving health through {field.lower()}"
    if any(x in fl for x in ("data", "computer", "cyber", "informatics", "computing", "analytics")):
        return f"Students who want to work with {field.lower()} using rigorous technical methods"
    if any(x in fl for x in ("policy", "public", "urban", "planning", "affairs", "diplomacy")):
        return f"Students focused on {field.lower()} to address public challenges"
    if any(x in fl for x in ("language", "linguistics", "literature", "writing", "journalism", "communication")):
        return f"Students drawn to {field.lower()} through language, texts, and culture"
    if fl.endswith(" studies"):
        return f"Students drawn to {field.lower()}"
    return f"Students drawn to {field.lower()}"


_DESIG = re.compile(
    r"^(?:Bachelor of Arts|Bachelor of Science|Bachelor of Fine Arts|Bachelor of Music|"
    r"Bachelor of Architecture|Bachelor of Social Work|"
    r"Master of Arts|Master of Science|Master of Fine Arts|Master of Music|"
    r"Master of Engineering|Master of Architecture|Master of Business Administration|"
    r"Master of Public Administration|Master of Public Health|Master of Public Policy|"
    r"Master of Social Work|Master of Education|Master of Accounting|"
    r"Master of Arts in Teaching|Master of Communication Management|"
    r"Master of Laws \(LL\.M\.\)|Master of Studies in Law|"
    r"Master of Business Taxation|Master of Business for Veterans|"
    r"Master of Communication Law Studies|Master of Dispute Resolution|"
    r"Master of Health Administration|Master of International Public Policy and Management|"
    r"Master of International Trade Law and Economics|Master of Landscape Architecture|"
    r"Master of Management Studies|Master of Management in Library and Information Science|"
    r"Master of Nonprofit Leadership and Management|Master of Public Art Studies|"
    r"Master of Public Diplomacy|Master of Real Estate Development|Master of Urban Planning|"
    r"Master of Visual Anthropology|"
    r"Doctor of Philosophy|Doctor of Musical Arts|Doctor of Education|"
    r"Doctor of Social Work|Doctor of Policy, Planning, and Development|"
    r"Doctor of Regulatory Science|Doctor of Liberal Arts|"
    r"Graduate Diploma|Dual Degree) in (.+)$"
)


def base_field(name: str) -> str | None:
    m = _DESIG.match(name)
    if not m:
        return None
    field = re.sub(r"\s*\(.*?\)", "", m.group(1))
    return re.split(r" / | to ", field)[0].strip()


SPECIAL: dict[str, tuple[str, str]] = {
    "Juris Doctor": (
        "22.0101",
        "Students committed to becoming lawyers through USC Gould School of Law's full J.D. curriculum.",
    ),
    "Doctor of Medicine": (
        "51.1201",
        "Students committed to becoming physicians through the Keck School of Medicine of USC's M.D. program.",
    ),
    "Doctor of Dental Surgery": (
        "51.0401",
        "Students committed to becoming dentists through USC's Herman Ostrow School of Dentistry D.D.S. program.",
    ),
    "Doctor of Pharmacy": (
        "51.2001",
        "Students committed to becoming pharmacists through USC Mann School of Pharmacy's Pharm.D. program.",
    ),
    "Doctor of Physical Therapy": (
        "51.2308",
        "Students committed to becoming physical therapists through USC's entry-level D.P.T. program.",
    ),
    "Doctor of Physical Therapy (D.P.T.)": (
        "51.2308",
        "Students committed to becoming physical therapists through USC's entry-level D.P.T. program.",
    ),
    "Doctor of Occupational Therapy": (
        "51.2304",
        "Students committed to becoming occupational therapists through USC's O.T.D. program.",
    ),
    "Doctor of Occupational Therapy (O.T.D.)": (
        "51.2304",
        "Students committed to becoming occupational therapists through USC's O.T.D. program.",
    ),
    "Entry-Level Doctor of Occupational Therapy": (
        "51.2304",
        "Students committed to becoming occupational therapists through USC's entry-level O.T.D. program.",
    ),
    "Entry-Level Doctor of Occupational Therapy (O.T.D.)": (
        "51.2304",
        "Students committed to becoming occupational therapists through USC's entry-level O.T.D. program.",
    ),
    "Doctor of Nurse Anesthesia Practice": (
        "51.3801",
        "Advanced-practice nurses pursuing the terminal clinical doctorate in nurse anesthesia at USC.",
    ),
    "Full-Time MBA": (
        "52.0201",
        "Professionals who want USC Marshall's full-time M.B.A. with Los Angeles industry access.",
    ),
    "Part-Time MBA": (
        "52.0201",
        "Working professionals who want USC Marshall's part-time M.B.A. while staying in their careers.",
    ),
    "One-Year International MBA": (
        "52.0201",
        "Experienced professionals who want USC Marshall's one-year international M.B.A.",
    ),
    "Online MBA": (
        "52.0201",
        "Working professionals who want USC Marshall's online M.B.A. with the same Marshall credential.",
    ),
    "Executive MBA": (
        "52.0201",
        "Senior professionals who want USC Marshall's executive M.B.A. without leaving their careers.",
    ),
    "Master of Academic Medicine": (
        "51.1201",
        "Clinicians and educators who want USC's master's training in academic medicine and medical education.",
    ),
    "Master of Advanced Architectural Studies": (
        "04.0201",
        "Architects and designers pursuing advanced graduate study in architectural theory and research at USC.",
    ),
    "Master of Advanced Architectural Research Studies": (
        "04.0201",
        "Architects pursuing USC's research-focused graduate program in advanced architectural studies.",
    ),
    "Master of Heritage Conservation": (
        "04.0801",
        "Students committed to preserving historic buildings and cultural heritage through USC's conservation program.",
    ),
    "Master of Laws": (
        "22.0201",
        "Lawyers who want USC Gould's LL.M. in American and comparative law.",
    ),
    "Master of Studies in Law": (
        "22.0201",
        "Non-lawyer professionals who need a working command of law through USC Gould's M.S.L.",
    ),
    "Master of Public Administration with Seoul National University": (
        "44.0401",
        "Students who want USC Price's dual M.P.A. with Seoul National University for global public leadership.",
    ),
}


def fmt_dict(name: str, d: dict[str, str]) -> list[str]:
    lines = [f"{name}: dict[str, str] = {{"]
    for k, v in sorted(d.items()):
        lines.append(f"    {k!r}: {v!r},")
    lines.append("}")
    return lines


def main() -> None:
    all_fields = {base_field(p["program_name"]) for p in usc.PROGRAMS} - {None}
    cip_by_field: dict[str, str] = {}
    who_by_field: dict[str, str] = {}
    missing: list[str] = []
    for field in sorted(all_fields):
        cip = USC_CIP_OVERRIDES.get(field) or lookup_cip(field)
        if not cip:
            missing.append(field)
            continue
        cip_by_field[field] = cip
        who_by_field[field] = who_lead(field)

    uncovered: list[str] = []
    who_vals: list[str] = []
    for p in usc.PROGRAMS:
        name, dt = p["program_name"], p["degree_type"]
        if name in SPECIAL:
            _, who = SPECIAL[name]
        else:
            bf = base_field(name)
            if not bf or bf not in cip_by_field:
                uncovered.append(name)
                continue
            who = (
                f"{who_by_field[bf]} {bu.LEVEL_TAIL.get(dt, bu.LEVEL_TAIL['masters'])}"
                f"{bu._distinguisher(name)}"
            )
        who_vals.append(who)

    ratio = len(set(who_vals)) / len(who_vals)
    print(
        f"fields={len(all_fields)} cip={len(cip_by_field)} missing={len(missing)} "
        f"uncovered={len(uncovered)} ratio={ratio:.3f}"
    )
    if missing:
        print("missing:", missing)
    if uncovered:
        print("uncovered:", uncovered[:20])
    if missing or uncovered or ratio < 0.9:
        sys.exit(1)

    out = Path(__file__).resolve().parents[1] / "src/unipaith/data/usc_cip_who.py"
    header = '''"""University of Southern California — matcher-core ``cip_code`` + program-DISTINCT ``who_its_for``.

REPAIR_BACKLOG #1 (``cip_code`` STARVATION) + #4a (``who_its_for`` 0%). The base
``usc_profile`` catalog (511 real programs) shipped both fields null — all 511 scored
field-blind and had no audience statement. This module stamps a verified NCES CIP family
and a field-specific, program-DISTINCT ``who_its_for`` on every row.
"""
'''
    lines = header.splitlines() + [
        "",
        "from __future__ import annotations",
        "",
        "import re",
        "",
        "from unipaith.data import bu_cip_who as _bu",
        "",
        "# ruff: noqa: E501",
        "",
        "LEVEL_TAIL = _bu.LEVEL_TAIL",
        "",
        "def _distinguisher(program_name: str) -> str:",
        "    return _bu._distinguisher(program_name)",
        "",
    ]
    lines.extend(fmt_dict("CIP_BY_FIELD", cip_by_field))
    lines.append("")
    lines.extend(fmt_dict("WHO_BY_FIELD", who_by_field))
    lines.append("")
    lines.append("SPECIAL: dict[str, tuple[str, str]] = {")
    for k, (c, w) in sorted(SPECIAL.items()):
        lines.append(f"    {k!r}: ({c!r}, {w!r}),")
    lines.append("}")
    lines.extend(
        """
_DESIG = re.compile(
    r"^(?:Bachelor of Arts|Bachelor of Science|Bachelor of Fine Arts|Bachelor of Music|"
    r"Bachelor of Architecture|Bachelor of Social Work|"
    r"Master of Arts|Master of Science|Master of Fine Arts|Master of Music|"
    r"Master of Engineering|Master of Architecture|Master of Business Administration|"
    r"Master of Public Administration|Master of Public Health|Master of Public Policy|"
    r"Master of Social Work|Master of Education|Master of Accounting|"
    r"Master of Arts in Teaching|Master of Communication Management|"
    r"Master of Laws \\(LL\\.M\\.\\)|Master of Studies in Law|"
    r"Master of Business Taxation|Master of Business for Veterans|"
    r"Master of Communication Law Studies|Master of Dispute Resolution|"
    r"Master of Health Administration|Master of International Public Policy and Management|"
    r"Master of International Trade Law and Economics|Master of Landscape Architecture|"
    r"Master of Management Studies|Master of Management in Library and Information Science|"
    r"Master of Nonprofit Leadership and Management|Master of Public Art Studies|"
    r"Master of Public Diplomacy|Master of Real Estate Development|Master of Urban Planning|"
    r"Master of Visual Anthropology|"
    r"Doctor of Philosophy|Doctor of Musical Arts|Doctor of Education|"
    r"Doctor of Social Work|Doctor of Policy, Planning, and Development|"
    r"Doctor of Regulatory Science|Doctor of Liberal Arts|"
    r"Graduate Diploma|Dual Degree) in (.+)$"
)


def _base_field(program_name: str) -> str | None:
    m = _DESIG.match(program_name)
    if not m:
        return None
    field = re.sub(r"\\s*\\(.*?\\)", "", m.group(1))
    return re.split(r" / | to ", field)[0].strip()


def resolve(program_name: str, degree_type: str) -> tuple[str | None, str | None]:
    sp = SPECIAL.get(program_name)
    if sp is not None:
        return sp[0], sp[1] if sp[1].endswith(".") else sp[1] + "."
    field = _base_field(program_name)
    if field is None:
        return None, None
    cip = CIP_BY_FIELD.get(field)
    lead = WHO_BY_FIELD.get(field)
    if not cip or not lead:
        return None, None
    tail = LEVEL_TAIL.get(degree_type, LEVEL_TAIL["masters"])
    who = f"{lead} {tail}{_distinguisher(program_name)}"
    return cip, who
""".strip().splitlines()
    )
    lines.append("")
    out.write_text("\n".join(lines))
    print(f"Wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
