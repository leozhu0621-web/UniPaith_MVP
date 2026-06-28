#!/usr/bin/env python3
"""Generate nyu_cip_who.py — run from unipaith-backend with PYTHONPATH=src."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from unipaith.data import bu_cip_who as bu
from unipaith.data import cornell_cip_who as cornell
from unipaith.data import nyu_profile as nyu

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


NYU_CIP_OVERRIDES: dict[str, str] = {
    "Cognition and Perception": "42.01",
    "Developmental Psychology": "42.01",
    "Educational Theatre in Colleges and Communities": "13.13",
    "Higher Education": "13.04",
    "Higher Education Administration": "13.04",
    "Interactive Telecommunications": "11.04",
    "Legal Theory": "22.02",
    "Spanish": "16.09",
    "Virtual Production": "50.06",
    "Public Health": "51.22",
    "Art Therapy": "51.23",
    "Bioethics": "51.22",
    "Biomedical Informatics": "51.27",
    "Biomolecular Science": "26.02",
    "Classical Civilization": "16.12",
    "Creative Writing in Spanish": "23.13",
    "Cybersecurity": "11.10",
    "Drama Therapy": "51.23",
    "Dramatic Writing": "50.05",
    "Education Studies": "13.01",
    "Educational Theatre": "13.13",
    "Educational Theatre, All Grades": "13.13",
    "Educational Theatre, All Grades, and English, 7-12": "13.13",
    "Educational Theatre, All Grades, and Social Studies, 7-12": "13.13",
    "Environmental Conservation Education": "13.13",
    "Financial Engineering": "14.35",
    "Food Studies": "19.05",
    "Hellenic Studies": "16.12",
    "Instrumental Performance": "50.09",
    "Italian": "16.09",
    "Latino Studies": "05.02",
    "Mathematical Sciences": "27.01",
    "Performance Studies": "50.05",
    "Piano Performance": "50.09",
    "Scientific Computing": "11.07",
    "Spanish and Portuguese": "16.09",
    "Translation and Interpreting": "16.01",
    "Vocal Performance": "50.09",
    "Africana Studies": "05.02",
    "American Journalism": "09.04",
    "American Studies": "05.0102",
    "Ancient World": "16.12",
    "Animal Studies": "01.09",
    "Applied General Studies": "24.01",
    "Applied Quantum Science and Technology": "40.08",
    "Archives and Public History": "54.01",
    "Art Education and Community Practice": "13.1302",
    "Arts and Politics": "50.99",
    "Asian/Pacific/American Studies": "05.02",
    "Atmosphere-Ocean Science": "40.04",
    "Bioinformatics Online": "26.11",
    "Biomaterials Science": "14.18",
    "Biotechnology Entrepreneurship": "26.12",
    "Business and Political Economy": "52.02",
    "Business and Technology Management": "52.02",
    "Business, Technology and Entrepreneurship": "52.02",
    "Cinema Studies": "50.06",
    "Cinema Studies — Tisch School of the Arts": "50.06",
    "Collaborative Arts": "50.05",
    "Computer and Data Science": "11.07",
    "Computing, Entrepreneurship, and Innovation": "11.07",
    "Costume Studies": "50.02",
    "Cybersecurity Risk and Strategy": "11.10",
    "Data Analytics and Business Computing": "52.13",
    "Design for Stage and Film": "50.05",
    "Digital Communications and Media": "09.07",
    "Dramatic Literature, Theatre History, and Cinema": "50.05",
    "Economics — Stern School of Business": "45.06",
    "Educational Communications and Technology": "13.05",
    "Educational Leadership, Politics, and Advocacy": "13.04",
    "Emerging Technologies": "15.16",
    "Event Management": "52.09",
    "Executive Coaching and Organizational Consulting": "13.04",
    "Film and Television": "50.06",
    "Financial Planning": "52.08",
    "Fintech": "52.08",
    "Game Design": "50.04",
    "Games for Learning": "13.05",
    "Global Affairs": "45.09",
    "Global Finance": "52.08",
    "Global Hospitality Management": "52.09",
    "Global Liberal Studies": "24.01",
    "Global Public Health and Anthropology": "51.22",
    "Global Public Health and Applied Psychology": "51.22",
    "Global Public Health and Communicative Sciences and Disorders": "51.22",
    "Global Public Health and Food Studies": "51.22",
    "Global Public Health and History": "51.22",
    "Global Public Health and Media, Culture, and Communication": "51.22",
    "Global Public Health and Nursing": "51.22",
    "Global Public Health and Nutrition and Dietetics": "51.22",
    "Global Public Health and Science": "51.22",
    "Global Public Health and Social Work": "51.22",
    "Global Public Health and Sociology": "51.22",
    "Global Security, Conflict, and Cybercrime": "43.01",
    "Global Sport": "31.05",
    "Health Law and Strategy": "51.22",
    "Health and Wellbeing Studies": "51.22",
    "Healthcare Management": "51.22",
    "Hebrew and Judaic Studies": "05.02",
    "Hebrew and Judaic Studies and History": "54.01",
    "Human Skeletal Biology": "45.03",
    "Human-Centered Technology, Innovation, and Design": "14.01",
    "Humanities": "24.01",
    "Individualized Study": "24.01",
    "Integrated Design and Media": "50.04",
    "Integrated Marketing": "52.14",
    "Interactive Media Arts": "50.04",
    "Interdisciplinary Studies": "30.99",
    "International Education": "13.01",
    "Irish and Irish American Studies": "05.02",
    "Journalism and Africana Studies": "09.04",
    "Journalism and East Asian Studies": "09.04",
    "Journalism and European and Mediterranean Studies": "09.04",
    "Journalism and French Studies": "09.04",
    "Journalism and International Relations": "09.04",
    "Journalism and Latin American and Caribbean Studies": "09.04",
    "Journalism and Near Eastern Studies": "09.04",
    "Journalism and Russian and Slavic Studies": "09.04",
    "Language and Mind": "16.01",
    "Leadership and Management": "52.02",
    "Learning, Technology, and Experience Design": "13.05",
    "Literary Reportage": "09.04",
    "Management and Organizational Behavior": "52.02",
    "Management and Systems": "52.02",
    "Management of Organizations and Strategy": "52.02",
    "Management of Technology": "14.01",
    "Marketing Analytics": "52.14",
    "Marketing and Retail Science": "52.14",
    "Mathematics Finance": "27.03",
    "Media Producing": "50.06",
    "Media, Culture, and Communication": "09.01",
    "Middle Eastern and Islamic Studies": "05.02",
    "Moving Image Archiving and Preservation": "50.06",
    "Musical Theatre Writing": "50.05",
    "Music Business": "50.09",
    "Music Therapists": "51.23",
    "Near Eastern Studies": "05.02",
    "Neural Science": "26.13",
    "Nurse-Midwifery": "51.38",
    "Nursing Informatics": "51.38",
    "Nursing Research and Theory Development": "51.38",
    "Operations Management": "52.02",
    "Performing Arts Administration": "50.10",
    "Photography and Imaging": "50.04",
    "Physical Therapists": "51.23",
    "Professional Studies": "24.01",
    "Professional Writing": "23.13",
    "Project Management": "52.02",
    "Public Relations and Corporate Communication": "09.09",
    "Publishing": "09.04",
    "Quantitative Economics": "45.06",
    "Quantitative Finance": "52.08",
    "Real Estate and Urban Sustainability": "52.15",
    "Recorded Music": "50.09",
    "Research in Occupational Therapy": "51.23",
    "Research in Physical Therapy": "51.23",
    "Social and Cultural Analysis": "45.02",
    "Sociology Education": "13.01",
    "Specialized Studies in Education": "13.01",
    "Sport Management": "31.05",
    "Sports Business": "52.02",
    "Studio Art": "50.07",
    "Teacher of Dance, All Grades": "13.13",
    "Teachers of English 7-12": "13.13",
    "Teachers of English Language and Literature in College": "13.13",
    "Teachers of Mathematics 7-12": "13.13",
    "Teaching Art, All Grades": "13.13",
    "Teaching Biology 7-12": "13.13",
    "Teaching Chemistry 7-12": "13.13",
    "Teaching Dance in the Professions": "13.13",
    "Teaching Dance, All Grades": "13.13",
    "Teaching Earth Science 7-12": "13.13",
    "Teaching English": "13.13",
    "Teaching English 7-12": "13.13",
    "Teaching English 7-12 with 5-6 Extension/Students with Disabilities 7-12 Generalist": "13.13",
    "Teaching Mathematics 7-12": "13.13",
    "Teaching Physics 7-12": "13.13",
    "Teaching Social Studies 7-12": "13.13",
    "Teaching Social Studies 7-12 with 5-6 Extension/Students with Disabilities 7-12 Generalist": "13.13",
    "Teaching World Languages 7-12/TESOL": "13.13",
    "Teaching a World Language 7-12: Chinese": "13.13",
    "Teaching a World Language 7-12: French": "13.13",
    "Teaching a World Language 7-12: Italian": "13.13",
    "Teaching a World Language 7-12: Japanese": "13.13",
    "Teaching a World Language 7-12: Spanish": "13.13",
    "Teaching and Learning": "13.01",
    "Teaching — Inclusive Childhood Teacher Residency": "13.12",
    "Teaching — Teacher Residency": "13.12",
    "Teaching — Transformational Teaching Students with Disabilities and Computer Science": "13.13",
    "Teaching — Transformational Teaching in Middle and High Schools": "13.13",
    "Theatre for Social and Civic Engagement": "50.05",
    "Transportation Systems": "14.08",
    "Travel and Tourism Management": "52.09",
    "Urban Infrastructure Systems": "14.08",
    "Urban Systems": "14.08",
    "Visual Arts Administration": "50.10",
    "World Language Education": "13.13",
    "Adult-Gerontology Acute Care Nurse Practitioner": "51.38",
    "Adult-Gerontology Primary Care Nurse Practitioner": "51.38",
    "Family Nurse Practitioner": "51.38",
    "Pediatrics Nurse Practitioner Primary Care/Acute Care": "51.38",
    "Pediatrics Primary Care Nurse Practitioner": "51.38",
    "Psychiatric-Mental Health Nurse Practitioner": "51.38",
    "Advanced Occupational Therapy": "51.23",
    "Clinical Research Nursing": "51.38",
}


def who_lead(field: str) -> str:
    if field in bu.WHO_BY_FIELD:
        return bu.WHO_BY_FIELD[field]
    if field in cornell.WHO_BY_FIELD:
        return cornell.WHO_BY_FIELD[field]
    fl = field.lower()
    if "nurse practitioner" in fl or "adult-gerontology" in fl:
        return (
            f"Registered nurses advancing to advanced practice as {field.lower()} specialists"
        )
    if fl.startswith("teaching") or "teachers of" in fl or "teacher of" in fl:
        return f"Students preparing to teach in {field.lower()}"
    if "global public health and" in fl:
        return (
            f"Students who want to combine population-health training with study of "
            f"{field.split(' and ', 1)[1].lower()}"
        )
    if " and " in field:
        return f"Students drawn to the intersection of {field.lower()}"
    if "engineering" in fl:
        return f"Students focused on {field.lower()} who want to design and build systems"
    if "education" in fl or "teaching" in fl:
        return f"Students preparing for careers in {field.lower()}"
    if any(x in fl for x in ("business", "finance", "marketing", "management", "accounting")):
        return f"Students focused on {field.lower()} in organizations and markets"
    if "nursing" in fl:
        return f"Nurses and health professionals focused on {field.lower()}"
    if any(x in fl for x in ("music", "theatre", "dance", "performance", "acting")):
        return f"Students committed to {field.lower()} as performers, creators, or scholars"
    if any(x in fl for x in ("art", "design", "film", "media", "cinema")):
        return f"Students drawn to {field.lower()} as makers and critical thinkers"
    if any(x in fl for x in ("science", "biology", "chemistry", "physics", "math")):
        return f"Students fascinated by {field.lower()} and how it explains the natural world"
    if any(x in fl for x in ("health", "medical", "clinical", "therapy")):
        return f"Students committed to improving health through {field.lower()}"
    if any(x in fl for x in ("data", "computer", "cyber", "informatics", "computing")):
        return f"Students who want to work with {field.lower()} using rigorous technical methods"
    if any(x in fl for x in ("policy", "public", "urban", "planning", "affairs")):
        return f"Students focused on {field.lower()} to address public challenges"
    if any(x in fl for x in ("language", "linguistics", "literature", "writing", "journalism")):
        return f"Students drawn to {field.lower()} through language, texts, and culture"
    if fl.endswith(" studies"):
        return f"Students drawn to {field.lower()}"
    return f"Students drawn to {field.lower()}"


_DESIG = re.compile(
    r"^(?:Bachelor of Arts|Bachelor of Science|Bachelor of Fine Arts|Bachelor of Music|"
    r"Master of Arts|Master of Science|Master of Fine Arts|Master of Music|"
    r"Master of Engineering|Master of Professional Studies|Master of Public Administration|"
    r"Master of Public Health|Master of Urban Planning|Master of Health Administration|"
    r"Master of Studies in Law \(M\.S\.L\.\)|Master of Laws \(LL\.M\.\)|"
    r"Doctor of Philosophy|Doctor of Musical Arts|Doctor of Education|"
    r"Doctor of Public Health|Doctor of Social Work \(D\.S\.W\.\)|"
    r"Doctor of Juridical Science|Graduate Certificate) in (.+)$|"
    r"^Master of Arts in Teaching — (.+)$|"
    r"^Doctor of (?:Nursing Practice|Occupational Therapy|Physical Therapy)"
    r"(?: \(Post-Professional\))? — (.+)$"
)


def base_field(name: str) -> str | None:
    m = _DESIG.match(name)
    if not m:
        return None
    field = re.sub(r"\s*\(.*?\)", "", m.group(1))
    return re.split(r" / | to ", field)[0].strip()


SPECIAL: dict[str, tuple[str, str]] = {
    "Juris Doctor (J.D.)": (
        "22.01",
        "Students committed to becoming lawyers through the full J.D. legal curriculum at NYU Law.",
    ),
    "Doctor of Juridical Science (J.S.D.)": (
        "22.02",
        "Legal scholars pursuing doctoral research in law at NYU.",
    ),
    "Doctor of Medicine (M.D.)": (
        "51.12",
        "Students committed to becoming physicians through NYU Grossman School of Medicine's M.D. curriculum.",
    ),
    "Doctor of Medicine (M.D.) — Long Island School of Medicine": (
        "51.12",
        "Students committed to becoming physicians through NYU Long Island School of Medicine's M.D. curriculum.",
    ),
    "Doctor of Dental Surgery (D.D.S.)": (
        "51.04",
        "Students committed to becoming dentists through NYU College of Dentistry's D.D.S. program.",
    ),
    "Combined-Degree B.A./D.D.S. in Biology and Dentistry (7-year)": (
        "51.04",
        "Students pursuing NYU's accelerated seven-year combined biology and dental-medicine path.",
    ),
    "Master of Social Work (M.S.W.)": (
        "44.07",
        "Students preparing for professional social-work practice with individuals, families, and communities.",
    ),
    "Doctor of Social Work (D.S.W.) in Clinical Social Work": (
        "44.07",
        "Experienced social-work practitioners pursuing doctoral leadership in clinical social work.",
    ),
    "Doctor of Nursing Practice": (
        "51.38",
        "Advanced-practice nurses pursuing the terminal clinical doctorate in nursing.",
    ),
    "Doctor of Occupational Therapy": (
        "51.23",
        "Students committed to becoming occupational therapists through NYU's entry-level O.T.D.",
    ),
    "Doctor of Occupational Therapy (Post-Professional)": (
        "51.23",
        "Practicing occupational therapists advancing to the post-professional O.T.D.",
    ),
    "Doctor of Physical Therapy": (
        "51.23",
        "Students committed to becoming physical therapists through NYU's entry-level D.P.T.",
    ),
    "Doctor of Physical Therapy (Post-Professional)": (
        "51.23",
        "Practicing physical therapists advancing to the post-professional D.P.T.",
    ),
    "Doctor of Public Health in Public Health": (
        "51.22",
        "Public-health leaders pursuing the Dr.P.H. in population health and policy.",
    ),
    "MBA (Full-Time, Two-Year)": (
        "52.02",
        "Professionals who want Stern's full-time two-year M.B.A. to lead in business and organizations.",
    ),
    "MBA for Executives (Executive MBA)": (
        "52.02",
        "Experienced managers who want Stern's executive M.B.A. without leaving their careers.",
    ),
    "Global Executive MBA": (
        "52.02",
        "Senior professionals who want Stern's global executive M.B.A. with international residencies.",
    ),
    "Fashion & Luxury MBA": (
        "52.02",
        "Professionals focused on fashion, luxury, and retail who want Stern's specialized M.B.A.",
    ),
    "Andre Koo Technology and Entrepreneurship MBA": (
        "52.02",
        "Entrepreneurs and technologists who want Stern's Andre Koo M.B.A. in technology and entrepreneurship.",
    ),
    "Executive MBA — NYU Stern / NYU Abu Dhabi": (
        "52.02",
        "Senior professionals who want Stern's executive M.B.A. delivered with NYU Abu Dhabi.",
    ),
    "Executive Master of Public Administration": (
        "44.04",
        "Mid-career public-service leaders who want Wagner's executive M.P.A.",
    ),
    "Master of Health Administration (Online)": (
        "51.22",
        "Health-care professionals who want Wagner's online master of health administration.",
    ),
    "Master of Public Administration in Health Policy and Management": (
        "44.04",
        "Students focused on health policy and management who want Wagner's M.P.A. in that concentration.",
    ),
    "Master of Public Administration in Public and Nonprofit Management and Policy": (
        "44.04",
        "Students focused on public and nonprofit leadership who want Wagner's flagship M.P.A.",
    ),
    "Master of Public Health in Public Health": (
        "51.22",
        "Students committed to protecting and improving population health through NYU's M.P.H.",
    ),
    "Master of Urban Planning in Urban Planning": (
        "04.03",
        "Students focused on cities and regions who want Wagner's accredited M.U.P.",
    ),
    "Master of Laws (LL.M.) in Law": (
        "22.02",
        "Lawyers who want NYU Law's general LL.M. in American and comparative law.",
    ),
    "Master of Laws (LL.M.) in Taxation": (
        "22.02",
        "Lawyers who want advanced specialized study in tax law at NYU.",
    ),
    "Master of Laws (LL.M.) in Taxation (Executive Program)": (
        "22.02",
        "Practicing tax lawyers who want NYU's executive LL.M. in taxation.",
    ),
    "Master of Laws (LL.M.) in International Taxation": (
        "22.02",
        "Lawyers who want specialized graduate study in international tax law.",
    ),
    "Master of Laws (LL.M.) in Corporate Law": (
        "22.02",
        "Lawyers who want advanced study in corporate and business law.",
    ),
    "Master of Laws (LL.M.) in Competition, Innovation, and Information Law": (
        "22.02",
        "Lawyers focused on antitrust, innovation, and information law.",
    ),
    "Master of Laws (LL.M.) in Environmental and Energy Law": (
        "22.02",
        "Lawyers focused on environmental regulation and energy law.",
    ),
    "Master of Laws (LL.M.) in International Legal Studies": (
        "22.02",
        "Lawyers who want advanced study in international and comparative law.",
    ),
    "Master of Laws (LL.M.) in International Business Regulation, Litigation, and Arbitration": (
        "22.02",
        "Lawyers focused on international business disputes and arbitration.",
    ),
    "Master of Laws (LL.M.) in Legal Theory": (
        "22.02",
        "Lawyers and scholars who want advanced study in legal theory and jurisprudence.",
    ),
    "Master of Studies in Law (M.S.L.) in Taxation": (
        "22.02",
        "Non-lawyer professionals who need a working command of tax law.",
    ),
    "Master of Music in Instrumental Performance": (
        "50.09",
        "Musicians committed to advanced instrumental performance at Steinhardt.",
    ),
    "Master of Music in Piano Performance": (
        "50.09",
        "Pianists committed to advanced performance study at Steinhardt.",
    ),
    "Master of Music in Vocal Performance": (
        "50.09",
        "Vocalists committed to advanced performance study at Steinhardt.",
    ),
    "Master of Music in Music Technology": (
        "50.09",
        "Musicians and technologists focused on music technology and production.",
    ),
    "Master of Music in Music Theory and Composition": (
        "50.09",
        "Musicians committed to advanced study in theory and composition.",
    ),
    "Master of Professional Studies in Interactive Telecommunications (ITP)": (
        "11.04",
        "Creators and technologists who want ITP's hands-on graduate program in interactive media.",
    ),
    "Master of Professional Studies in Virtual Production": (
        "50.06",
        "Creators focused on virtual production for film and immersive media.",
    ),
    "Combined B.S./M.S. in Accounting": (
        "52.03",
        "Undergraduates who want Stern's accelerated combined accounting B.S./M.S.",
    ),
    "Combined B.S./M.S. in Computer Science and Management of Technology": (
        "11.07",
        "Students who want Tandon's accelerated combined computer science and management of technology degrees.",
    ),
    "Combined B.F.A./M.S. in Studio Art and Integrated Design & Media": (
        "50.07",
        "Artists who want Tisch and Tandon's combined studio art and integrated design & media path.",
    ),
    "Dual M.S. in Human Capital Management and Human Capital Analytics & Technology": (
        "52.10",
        "Professionals who want Stern's dual master's in human capital management and analytics.",
    ),
    "Dual M.S./M.A. in Conservation of Historic and Artistic Works and History of Art and Archaeology": (
        "50.07",
        "Students who want IFA's dual conservation and art-history master's.",
    ),
    "Doctor of Education in Educational Leadership and Policy Studies": (
        "13.04",
        "Educators pursuing the Ed.D. in educational leadership and policy at Steinhardt.",
    ),
    "Doctor of Education in Educational Theatre in Colleges and Communities": (
        "13.13",
        "Educators and artists pursuing the Ed.D. in educational theatre.",
    ),
    "Doctor of Education in Higher Education Administration": (
        "13.04",
        "Higher-education professionals pursuing the Ed.D. in administration and leadership.",
    ),
    "Doctor of Education in Leadership and Innovation": (
        "13.04",
        "Educators and leaders pursuing the Ed.D. in leadership and innovation.",
    ),
}
for bs_combo in [
    "Combined B.S. in Biology and Chemical & Biomolecular Engineering",
    "Combined B.S. in Chemistry and Chemical & Biomolecular Engineering",
    "Combined B.S. in Computer Science and Electrical Engineering",
    "Combined B.S. in Computer Science and Engineering",
    "Combined B.S. in Mathematics and Civil Engineering",
    "Combined B.S. in Mathematics and Computer Engineering",
    "Combined B.S. in Mathematics and Electrical Engineering",
    "Combined B.S. in Mathematics and Mechanical Engineering",
    "Combined B.S. in Physics and Civil Engineering",
    "Combined B.S. in Physics and Computer Engineering",
    "Combined B.S. in Physics and Electrical Engineering",
    "Combined B.S. in Physics and Mechanical Engineering",
]:
    SPECIAL[bs_combo] = (
        "14.01",
        f"Students who want Tandon's dual-degree path combining "
        f"{bs_combo.replace('Combined ', '').lower()}.",
    )


def fmt_dict(name: str, d: dict[str, str]) -> list[str]:
    lines = [f"{name}: dict[str, str] = {{"]
    for k, v in sorted(d.items()):
        lines.append(f"    {k!r}: {v!r},")
    lines.append("}")
    return lines


def main() -> None:
    all_fields = {base_field(p["program_name"]) for p in nyu.PROGRAMS} - {None}
    cip_by_field: dict[str, str] = {}
    who_by_field: dict[str, str] = {}
    missing: list[str] = []
    for field in sorted(all_fields):
        cip = NYU_CIP_OVERRIDES.get(field) or lookup_cip(field)
        if not cip:
            missing.append(field)
            continue
        cip_by_field[field] = cip
        who_by_field[field] = who_lead(field)

    uncovered: list[str] = []
    who_vals: list[str] = []
    for p in nyu.PROGRAMS:
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

    out = Path(__file__).resolve().parents[1] / "src/unipaith/data/nyu_cip_who.py"
    header = '''"""New York University — matcher-core ``cip_code`` + program-DISTINCT ``who_its_for``.

REPAIR_BACKLOG #1 (``cip_code`` STARVATION) + #4a (``who_its_for`` 0%). The base
``nyu_profile`` catalog (502 real programs) shipped both fields null — all 502 scored
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
    r"Master of Arts|Master of Science|Master of Fine Arts|Master of Music|"
    r"Master of Engineering|Master of Professional Studies|Master of Public Administration|"
    r"Master of Public Health|Master of Urban Planning|Master of Health Administration|"
    r"Master of Studies in Law \\(M\\.S\\.L\\.\\)|Master of Laws \\(LL\\.M\\.\\)|"
    r"Doctor of Philosophy|Doctor of Musical Arts|Doctor of Education|"
    r"Doctor of Public Health|Doctor of Social Work \\(D\\.S\\.W\\.\\)|"
    r"Doctor of Juridical Science|Graduate Certificate) in (.+)$|"
    r"^Master of Arts in Teaching — (.+)$|"
    r"^Doctor of (?:Nursing Practice|Occupational Therapy|Physical Therapy)"
    r"(?: \\(Post-Professional\\))? — (.+)$"
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
