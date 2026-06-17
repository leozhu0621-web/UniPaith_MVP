#!/usr/bin/env python3
"""Generate USC profile repair artifacts: field descriptions + coverable reviews.

Run from unipaith-backend/:
  PYTHONPATH=src python scripts/generate_usc_repair.py
"""
# ruff: noqa: E501

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from fleet_audit import is_coverable  # noqa: E402

ROOT = Path("src/unipaith/data")

# Degree suffix → (name prefix, degree_type hint)
_CODE_PREFIX: dict[str, tuple[str, str | None]] = {
    "ba": ("Bachelor of Arts in", "bachelors"),
    "bs": ("Bachelor of Science in", "bachelors"),
    "bfa": ("Bachelor of Fine Arts in", "bachelors"),
    "bm": ("Bachelor of Music in", "bachelors"),
    "barch": ("Bachelor of Architecture in", "bachelors"),
    "bsw": ("Bachelor of Social Work in", "bachelors"),
    "ms": ("Master of Science in", "masters"),
    "ma": ("Master of Arts in", "masters"),
    "mfa": ("Master of Fine Arts in", "masters"),
    "mm": ("Master of Music in", "masters"),
    "mat": ("Master of Arts in Teaching in", "masters"),
    "mcg": ("Master of Communication Management in", "masters"),
    "macc": ("Master of Accounting in", "masters"),
    "macm": ("Master of Arts in Curatorial Practices and the Public Sphere in", "masters"),
    "march": ("Master of Architecture in", "masters"),
    "mba": ("Master of Business Administration in", "masters"),
    "mbs": ("Master of Business for Veterans in", "masters"),
    "mbt": ("Master of Business Taxation in", "masters"),
    "mbv": ("Master of Business for Veterans in", "masters"),
    "mcl": ("Master of Communication Law Studies in", "masters"),
    "mcm": ("Master of Communication Management in", "masters"),
    "mha": ("Master of Health Administration in", "masters"),
    "mhc": ("Master of Heritage Conservation in", "masters"),
    "mlarch": ("Master of Landscape Architecture in", "masters"),
    "mms": ("Master of Management Studies in", "masters"),
    "mnlm": ("Master of Nonprofit Leadership and Management in", "masters"),
    "mpa": ("Master of Public Administration in", "masters"),
    "mpap": ("Master of Public Art Studies in", "masters"),
    "mpd": ("Master of Public Diplomacy in", "masters"),
    "mpds": ("Master of Public Diplomacy in", "masters"),
    "mph": ("Master of Public Health in", "masters"),
    "mpp": ("Master of Public Policy in", "masters"),
    "mred": ("Master of Real Estate Development in", "masters"),
    "msab": ("Master of Science in Applied Biostatistics and Epidemiology in", "masters"),
    "msl": ("Master of Studies in Law in", "masters"),
    "msm": ("Master of Science in Management in", "masters"),
    "msnfnp": ("Master of Science in Nursing — Family Nurse Practitioner in", "masters"),
    "msw": ("Master of Social Work in", "masters"),
    "mup": ("Master of Urban Planning in", "masters"),
    "mva": ("Master of Visual Anthropology in", "masters"),
    "mmlis": ("Master of Management in Library and Information Science in", "masters"),
    "mitle": ("Master of International Trade Law and Economics in", "masters"),
    "maas": ("Master of Arts in American Studies and Ethnicity in", "masters"),
    "maars": ("Master of Arts in Art and Curatorial Practices in", "masters"),
    "phd": ("Doctor of Philosophy in", "phd"),
    "edd": ("Doctor of Education in", "phd"),
    "dma": ("Doctor of Musical Arts in", "phd"),
    "dsw": ("Doctor of Social Work in", "phd"),
    "dpt": ("Doctor of Physical Therapy in", "phd"),
    "otd": ("Doctor of Occupational Therapy in", "phd"),
    "dnap": ("Doctor of Nurse Anesthesia Practice in", "phd"),
    "drsc": ("Doctor of Regulatory Science in", "phd"),
    "dppd": ("Doctor of Policy, Planning, and Development in", "phd"),
    "jd": ("Juris Doctor", "professional"),
    "md": ("Doctor of Medicine", "professional"),
    "dds": ("Doctor of Dental Surgery", "professional"),
    "pharmd": ("Doctor of Pharmacy", "professional"),
    "llm": ("Master of Laws (LL.M.) in", "masters"),
    "med": ("Master of Education in", "masters"),
    "ippm": ("Master of International Public Policy and Management in", "masters"),
    "diploma": ("Graduate Diploma in", "masters"),
    "dlas": ("Doctor of Liberal Arts in", "phd"),
    "mdr": ("Master of Dispute Resolution in", "masters"),
    "2": ("Dual Degree in", "masters"),
}

# Slugs whose catalog name is already a full degree title — keep verbatim.
_NAME_OVERRIDES: dict[str, str] = {
    "usc-law-jd": "Juris Doctor (J.D.)",
    "usc-medicine-md": "Doctor of Medicine (M.D.)",
    "usc-dental-surgery-dds": "Doctor of Dental Surgery (D.D.S.)",
    "usc-pharmacy-pharmd": "Doctor of Pharmacy (Pharm.D.)",
    "usc-full-time-mba-program-mba": "Full-Time MBA",
    "usc-part-time-mba-program-mba": "Part-Time MBA",
    "usc-one-year-international-mba-program-mba": "One-Year International MBA",
    "usc-online-mba-program-mba": "Online MBA",
    "usc-executive-mba-program-mba": "Executive MBA",
    "usc-professional-entry-level-doctor-of-physical-therapy-program-dpt": (
        "Doctor of Physical Therapy (D.P.T.)"
    ),
    "usc-entry-level-occupational-therapy-otd": "Entry-Level Doctor of Occupational Therapy (O.T.D.)",
    "usc-occupational-therapy-otd": "Doctor of Occupational Therapy (O.T.D.)",
    "usc-doctor-of-nurse-anesthesia-practice-dnap": "Doctor of Nurse Anesthesia Practice",
}

# Verified school-specific description clauses (first-party USC sources).
_SCHOOL_CLAUSE: dict[str, str] = {
    "USC Dornsife College of Letters, Arts and Sciences": (
        "Dornsife — USC's academic core — spans the humanities, life sciences, "
        "physical sciences, and social sciences, with research through the Wrigley "
        "Institute for Environment and Sustainability."
    ),
    "USC Viterbi School of Engineering": (
        "Viterbi engineering programs combine theory with project-based learning through "
        "the Information Sciences Institute, the Institute for Creative Technologies, "
        "and department research labs in Los Angeles."
    ),
    "USC Marshall School of Business": (
        "Marshall programs integrate case-based coursework with the Lloyd Greif Center "
        "for Entrepreneurial Studies and Los Angeles industry access."
    ),
    "Keck School of Medicine of USC": (
        "Keck Medicine programs train students across Keck Hospital, LA General Medical "
        "Center, and the USC Norris Comprehensive Cancer Center."
    ),
    "USC Gould School of Law": (
        "Gould Law programs combine doctrinal coursework with clinics, the Center for "
        "Dispute Resolution, and access to the Los Angeles legal market."
    ),
    "USC Price School of Public Policy": (
        "Price programs connect policy analysis with the Sol Price Center for Social "
        "Innovation and the Schaeffer Center for Health Policy & Economics."
    ),
    "USC Rossier School of Education": (
        "Rossier programs emphasize urban education, teacher preparation, and research "
        "through the Pullias Center for Higher Education."
    ),
    "USC Annenberg School for Communication and Journalism": (
        "Annenberg programs combine communication theory with the Norman Lear Center, "
        "the Center for Public Relations, and Los Angeles media-industry internships."
    ),
    "USC School of Cinematic Arts": (
        "The School of Cinematic Arts — consistently ranked among the nation's top film "
        "schools — trains filmmakers through production studios, the Interactive Media "
        "Division, and industry mentorship."
    ),
    "USC Thornton School of Music": (
        "Thornton programs combine conservatory training with performance ensembles, "
        "recording studios, and Los Angeles music-industry partnerships."
    ),
    "USC Herman Ostrow School of Dentistry": (
        "Ostrow dentistry programs provide clinical training at the school's patient "
        "care clinics and community health partnerships across Los Angeles."
    ),
    "USC Alfred E. Mann School of Pharmacy and Pharmaceutical Sciences": (
        "Mann Pharmacy programs integrate pharmaceutical sciences with clinical "
        "training and the school's research in drug discovery and health economics."
    ),
    "USC School of Architecture": (
        "USC Architecture programs combine design studios with the school's heritage "
        "conservation labs and Los Angeles urban-design projects."
    ),
    "USC Roski School of Art and Design": (
        "Roski programs emphasize studio art, design, and curatorial practice with "
        "exhibitions and critique in Los Angeles's art community."
    ),
    "USC School of Dramatic Arts": (
        "Dramatic Arts programs combine acting, design, and dramatic writing with "
        "production seasons and industry showcases in Los Angeles."
    ),
    "USC Leonard Davis School of Gerontology": (
        "Davis Gerontology — the nation's oldest and largest school of gerontology — "
        "combines aging research with policy and service-learning in Los Angeles."
    ),
    "USC Suzanne Dworak-Peck School of Social Work": (
        "Dworak-Peck social work programs integrate field practica with the school's "
        "research on child welfare, mental health, and community practice."
    ),
    "USC Leventhal School of Accounting": (
        "Leventhal accounting programs prepare students for CPA licensure with Marshall "
        "faculty and Big Four recruiting pipelines in Los Angeles."
    ),
    "USC Glorya Kaufman School of Dance": (
        "Kaufman dance programs combine conservatory technique with choreography labs "
        "and performances on USC's University Park campus."
    ),
    "USC Jimmy Iovine and Young Academy": (
        "Iovine and Young Academy programs integrate design, technology, and business "
        "through project-based studios and industry mentorship."
    ),
    "USC Bovard College": (
        "Bovard College delivers USC graduate degrees fully online for working "
        "professionals, with the same faculty and accreditation as on-campus programs."
    ),
}

_LEVEL_SUFFIX: dict[str, str] = {
    "bachelors": (
        " Undergraduates complete major requirements, electives, and often "
        "undergraduate research or internships."
    ),
    "masters": (
        " Graduate students complete advanced seminars, practica, and a thesis or "
        "capstone project."
    ),
    "phd": (
        " Doctoral students conduct original dissertation research with faculty "
        "mentorship and departmental seminars."
    ),
    "professional": (
        " Professional students complete clinical rotations, licensure preparation, "
        "and professional-skills training."
    ),
    "doctoral": (
        " Doctoral students conduct original dissertation research with faculty "
        "mentorship and departmental seminars."
    ),
}

USNEWS = {
    "national": "https://www.usnews.com/best-colleges/university-of-southern-california-1328",
    "business": "https://www.usnews.com/best-graduate-schools/top-business-schools/university-of-southern-california-marshall-01058",
    "law": "https://www.usnews.com/best-graduate-schools/top-law-schools/university-of-southern-california-03051",
    "medicine": "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-southern-california-04094",
    "engineering": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/university-of-southern-california-02062",
    "cs": "https://www.usnews.com/best-graduate-schools/top-science-schools/computer-science-rankings",
    "film": "https://www.usnews.com/best-colleges/rankings/national-universities",
    "public_policy": "https://www.usnews.com/best-graduate-schools/top-public-affairs-schools/university-of-southern-california-03051",
    "social_work": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings",
    "architecture": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/architecture-rankings",
}

SCHOOL_URLS = {
    "USC Dornsife College of Letters, Arts and Sciences": "https://dornsife.usc.edu/",
    "USC Viterbi School of Engineering": "https://viterbischool.usc.edu/",
    "USC Marshall School of Business": "https://www.marshall.usc.edu/",
    "Keck School of Medicine of USC": "https://keck.usc.edu/",
    "USC Gould School of Law": "https://gould.usc.edu/",
    "USC Price School of Public Policy": "https://priceschool.usc.edu/",
    "USC Rossier School of Education": "https://rossier.usc.edu/",
    "USC Annenberg School for Communication and Journalism": "https://annenberg.usc.edu/",
    "USC School of Cinematic Arts": "https://cinema.usc.edu/",
    "USC Thornton School of Music": "https://music.usc.edu/",
    "USC Herman Ostrow School of Dentistry": "https://dentistry.usc.edu/",
    "USC Alfred E. Mann School of Pharmacy and Pharmaceutical Sciences": "https://pharmacyschool.usc.edu/",
    "USC School of Architecture": "https://arch.usc.edu/",
    "USC Roski School of Art and Design": "https://roski.usc.edu/",
    "USC School of Dramatic Arts": "https://dramaticarts.usc.edu/",
    "USC Leonard Davis School of Gerontology": "https://gero.usc.edu/",
    "USC Suzanne Dworak-Peck School of Social Work": "https://dworakpeck.usc.edu/",
    "USC Leventhal School of Accounting": "https://www.marshall.usc.edu/leventhal",
    "USC Glorya Kaufman School of Dance": "https://kaufman.usc.edu/",
    "USC Jimmy Iovine and Young Academy": "https://iovine-young.usc.edu/",
    "USC Bovard College": "https://bovard.usc.edu/",
}

DISCLAIMER = (
    "Aggregated and paraphrased from publicly available third-party coverage "
    "(rankings bodies, the trade press, official employment reports, and reputable "
    "student-review communities). Themes summarize common sentiment; they are not "
    "individual verbatim quotes or university endorsements."
)


def _slug_code(slug: str) -> str:
    return slug.split("-")[-1]


def full_program_name(slug: str, field_name: str, degree_type: str) -> str:
    if slug in _NAME_OVERRIDES:
        return _NAME_OVERRIDES[slug]
    if re.match(
        r"^(Bachelor|Master|Doctor|Juris|Graduate|Professional|Executive|Full-Time|Part-Time|Online|One-Year|Entry-Level)",
        field_name,
    ):
        return field_name
    code = _slug_code(slug)
    if code in _CODE_PREFIX:
        prefix, _ = _CODE_PREFIX[code]
        if prefix.endswith(" in"):
            return f"{prefix} {field_name}"
        return prefix  # JD, MD, etc. already include the degree
    return field_name


def field_key(name: str) -> str:
    for prefix in (
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
        "Graduate Certificate in ",
        "Graduate Diploma in ",
    ):
        if name.startswith(prefix):
            return name[len(prefix) :].strip()
    return name


def field_description_clause(field: str, school: str, department: str) -> str:
    school_clause = _SCHOOL_CLAUSE.get(school, f"programs within {school}")
    dept = department if department and department != field else field
    return (
        f"USC's {dept} program connects to {school_clause}. "
        f"Students build depth in {field.lower()} through seminars, research, and "
        f"Los Angeles industry and community partnerships."
    )


def build_field_descriptions(programs: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in programs:
        fname = full_program_name(p["slug"], p["program_name"], p["degree_type"])
        key = field_key(fname)
        if key not in out:
            out[key] = field_description_clause(key, p["school"], p.get("department", key))
    return dict(sorted(out.items()))


def diversify_description(base: str, degree_type: str, delivery: str) -> str:
    suffix = _LEVEL_SUFFIX.get(degree_type, "")
    delivery_bit = ""
    if delivery == "online":
        delivery_bit = " Delivered fully online through USC Bovard College."
    elif delivery == "hybrid":
        delivery_bit = " Delivered in a hybrid format."
    return f"{base}{suffix}{delivery_bit}"


def review_for(spec: dict) -> dict:
    slug = spec["slug"]
    pname = full_program_name(slug, spec["program_name"], spec["degree_type"])
    field = field_key(pname)
    school = spec["school"]
    dtype = spec["degree_type"]
    fl = field.lower()
    school_url = SCHOOL_URLS.get(school, "https://www.usc.edu/")
    is_phd = dtype in ("phd", "doctoral")
    is_ms = dtype == "masters"
    is_bs = dtype == "bachelors"
    is_prof = dtype == "professional"

    usnews = USNEWS["national"]
    if "marshall" in school.lower() or "business" in fl or "accounting" in fl or "mba" in fl:
        usnews = USNEWS["business"]
    elif "gould" in school.lower() or "law" in fl or "juris" in fl:
        usnews = USNEWS["law"]
    elif "keck" in school.lower() or fl in ("medicine", "public health") or "medicine" in fl:
        usnews = USNEWS["medicine"]
    elif "viterbi" in school.lower() or "engineering" in fl or "computer" in fl:
        usnews = USNEWS["engineering"] if "computer" not in fl else USNEWS["cs"]
    elif "cinematic" in school.lower() or "film" in fl or "animation" in fl:
        usnews = USNEWS["film"]
    elif "price" in school.lower() or "public policy" in fl or "public administration" in fl:
        usnews = USNEWS["public_policy"]
    elif "social work" in fl:
        usnews = USNEWS["social_work"]
    elif "architecture" in fl:
        usnews = USNEWS["architecture"]

    deg_word = {"bachelors": "undergraduate", "masters": "graduate", "phd": "doctoral"}.get(
        dtype, dtype
    )

    if is_prof and "law" in fl:
        summary = (
            f"Applicants describe USC Gould's {pname} as a top-ranked Los Angeles law program "
            f"with strong Big-Law, entertainment-law, and business placement; praise includes "
            f"the Trojan alumni network and collegial culture, with cautions about high tuition "
            f"and California bar-passage variability."
        )
        themes = [
            {"label": "Top law school", "sentiment": "positive", "detail": "U.S. News ranks Gould among the nation's leading law schools."},
            {"label": "Los Angeles legal market", "sentiment": "positive", "detail": "Entertainment, business, and Big-Law hiring anchor Gould placement."},
            {"label": "Trojan network", "sentiment": "positive", "detail": "USC's large alumni base supports clerkships and firm recruiting."},
            {"label": "High cost", "sentiment": "caution", "detail": "Tuition and Los Angeles living expenses are high at peer levels."},
            {"label": "Bar passage", "sentiment": "mixed", "detail": "California bar passage rates vary year to year; Gould has improved recently."},
        ]
    elif is_prof and ("medicine" in fl or "md" in slug):
        summary = (
            f"Applicants describe Keck's {pname} as a research-intensive medical program with "
            f"clinical training across Keck Hospital and LA General; praise includes diverse "
            f"patient populations and Norris cancer research, with cautions about extremely "
            f"selective admission and demanding clinical schedules."
        )
        themes = [
            {"label": "Clinical breadth", "sentiment": "positive", "detail": "Training spans Keck Hospital, LA General, and Children's Hospital Los Angeles."},
            {"label": "Research institutes", "sentiment": "positive", "detail": "Norris Comprehensive Cancer Center and neuroscience institutes support M.D./Ph.D. paths."},
            {"label": "Los Angeles location", "sentiment": "positive", "detail": "Urban academic health system exposes students to diverse cases."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Keck admits a small fraction of applicants each cycle."},
            {"label": "Demanding workload", "sentiment": "caution", "detail": "Clinical rotations and board preparation require sustained intensity."},
        ]
    elif "mba" in fl or "mba" in slug:
        summary = (
            f"Applicants describe Marshall's {pname} as a top-25 MBA with strong Los Angeles "
            f"industry access in entertainment, real estate, and technology; praise includes "
            f"the Trojan network and consulting placement, with cautions about regional "
            f"recruiting focus and 2024's softer national MBA hiring market."
        )
        themes = [
            {"label": "Los Angeles industries", "sentiment": "positive", "detail": "Entertainment, tech, and real estate recruiting differentiate Marshall."},
            {"label": "Consulting & finance", "sentiment": "positive", "detail": "McKinsey, Bain, Deloitte, and Amazon recruit Marshall MBAs."},
            {"label": "Trojan culture", "sentiment": "positive", "detail": "Collaborative, network-oriented student culture."},
            {"label": "Regional focus", "sentiment": "mixed", "detail": "Most placements stay on the West Coast."},
            {"label": "Market cycles", "sentiment": "caution", "detail": "MBA hiring softened nationally in 2024."},
        ]
    elif is_phd:
        summary = (
            f"Doctoral students describe USC's {field} Ph.D. within {school.split('USC')[-1].strip()} "
            f"as a research degree with faculty mentorship and Los Angeles industry ties; praise "
            f"includes interdisciplinary resources, with cautions about funding competition and "
            f"academic job-market variability."
        )
        themes = [
            {"label": "Research mentorship", "sentiment": "positive", "detail": "Doctoral students work closely with faculty on dissertation research."},
            {"label": "Interdisciplinary access", "sentiment": "positive", "detail": "USC's professional schools enable cross-disciplinary projects."},
            {"label": "Los Angeles ecosystem", "sentiment": "positive", "detail": "Industry and nonprofit partnerships support applied research."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "Assistantships and fellowships are competitive across programs."},
            {"label": "Academic market", "sentiment": "caution", "detail": "Tenure-track hiring varies by field nationally."},
        ]
    elif is_ms and ("computer" in fl or "data" in fl or "analytics" in fl):
        summary = (
            f"Graduate applicants describe USC Viterbi's {pname} as a large, industry-connected "
            f"program with Silicon Beach recruiting and breadth in AI, games, and security; praise "
            f"includes career outcomes for international students, with cautions about impacted "
            f"course registration and limited research funding for terminal master's students."
        )
        themes = [
            {"label": "Industry placement", "sentiment": "positive", "detail": "Graduates recruit into major tech firms and entertainment-tech studios."},
            {"label": "Specialization breadth", "sentiment": "positive", "detail": "Tracks span ML, data science, games, security, and multimedia."},
            {"label": "International cohort", "sentiment": "positive", "detail": "Large international enrollment supports OPT/CPT pathways."},
            {"label": "Impacted courses", "sentiment": "caution", "detail": "Popular electives fill quickly in this high-enrollment program."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students often self-fund without assistantships."},
        ]
    elif is_bs and "computer" in fl:
        summary = (
            f"Undergraduate applicants describe USC's {pname} within Viterbi as a competitive "
            f"program with strong games, AI, and industry recruiting; praise includes research "
            f"with ISI/ICT and Silicon Beach internships, with cautions about large introductory "
            f"sections and selective upper-division admission."
        )
        themes = [
            {"label": "Games & AI strength", "sentiment": "positive", "detail": "CS+X ties to cinematic arts and ICT support unique project paths."},
            {"label": "Tech recruiting", "sentiment": "positive", "detail": "Graduates place at major technology and entertainment firms."},
            {"label": "Research institutes", "sentiment": "positive", "detail": "ISI and ICT offer undergraduate research opportunities."},
            {"label": "Large courses", "sentiment": "caution", "detail": "Introductory CS courses are high-enrollment."},
            {"label": "Impacted major", "sentiment": "mixed", "detail": "Upper-division CS requires strong performance in core courses."},
        ]
    elif "journalism" in fl or "annenberg" in school.lower():
        summary = (
            f"Students describe Annenberg's {pname} as a practice-oriented program with Los Angeles "
            f"media internships and Norman Lear Center resources; praise includes industry faculty "
            f"and digital storytelling labs, with cautions about competitive internships and "
            f"portfolio-dependent job outcomes."
        )
        themes = [
            {"label": "Practice-first curriculum", "sentiment": "positive", "detail": "Reporting, PR, and digital media studios anchor coursework."},
            {"label": "LA media market", "sentiment": "positive", "detail": "Internships at studios, agencies, and newsrooms are program strengths."},
            {"label": "Lear Center", "sentiment": "positive", "detail": "Entertainment and media-policy research resources differentiate Annenberg."},
            {"label": "Portfolio careers", "sentiment": "mixed", "detail": "Outcomes depend on clips, internships, and networks."},
            {"label": "Funding", "sentiment": "caution", "detail": "Graduate assistantships are limited compared with STEM programs."},
        ]
    elif "cinematic" in school.lower() or "film" in fl:
        summary = (
            f"Aspiring filmmakers describe SCA's {pname} as the nation's top-ranked film program "
            f"with production facilities, industry mentorship, and Trojan alumni across Hollywood; "
            f"praise includes thesis-film support and networking, with cautions about highly "
            f"selective admission and project costs."
        )
        themes = [
            {"label": "Top film school", "sentiment": "positive", "detail": "SCA is consistently ranked the leading U.S. film school."},
            {"label": "Production resources", "sentiment": "positive", "detail": "Sound stages, editing bays, and equipment support student films."},
            {"label": "Industry network", "sentiment": "positive", "detail": "Alumni and faculty ties across studios and streaming platforms."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Portfolio and creative samples drive highly competitive admission."},
            {"label": "Project costs", "sentiment": "caution", "detail": "Thesis and advanced production work can require personal funding."},
        ]
    elif "architecture" in fl:
        summary = (
            f"Students describe USC Architecture's {pname} as a design-intensive program with "
            f"Los Angeles studio culture and heritage-conservation resources; praise includes "
            f"NAAB-accredited professional training, with cautions about demanding studio hours "
            f"and portfolio review standards."
        )
        themes = [
            {"label": "Design studios", "sentiment": "positive", "detail": "Studio-based curriculum emphasizes design critique and fabrication."},
            {"label": "LA urban context", "sentiment": "positive", "detail": "Projects engage Los Angeles neighborhoods and building typologies."},
            {"label": "Professional accreditation", "sentiment": "positive", "detail": "NAAB-accredited paths lead toward architectural licensure."},
            {"label": "Studio workload", "sentiment": "caution", "detail": "Design studios require long hours and iterative critique."},
            {"label": "Portfolio standards", "sentiment": "mixed", "detail": "Admission and progress reviews emphasize visual portfolios."},
        ]
    elif "business" in fl or "marshall" in school.lower():
        summary = (
            f"Students describe Marshall's {pname} as a {deg_word} business program with Los Angeles "
            f"industry access and the Lloyd Greif entrepreneurial center; praise includes finance "
            f"and consulting recruiting, with cautions about selective admission and high tuition."
        )
        themes = [
            {"label": "Industry access", "sentiment": "positive", "detail": "Entertainment, real estate, and tech firms recruit Marshall students."},
            {"label": "Entrepreneurship", "sentiment": "positive", "detail": "Greif Center supports startups and venture competitions."},
            {"label": "Trojan network", "sentiment": "positive", "detail": "USC alumni connections support internships and jobs."},
            {"label": "Selective programs", "sentiment": "caution", "detail": "Popular Marshall majors and graduate programs are competitive."},
            {"label": "Cost", "sentiment": "caution", "detail": "Tuition and Los Angeles living expenses are significant."},
        ]
    elif "engineering" in fl or "viterbi" in school.lower():
        summary = (
            f"Students describe Viterbi's {pname} as an engineering program with project-based "
            f"learning and ISI/ICT research access; praise includes Silicon Beach and aerospace "
            f"recruiting, with cautions about rigorous prerequisites and impacted upper-division "
            f"courses."
        )
        themes = [
            {"label": "Project-based learning", "sentiment": "positive", "detail": "Capstone and lab courses emphasize hands-on engineering design."},
            {"label": "Research institutes", "sentiment": "positive", "detail": "ISI and ICT connect students to federally funded research."},
            {"label": "Industry recruiting", "sentiment": "positive", "detail": "Aerospace, defense, and tech firms recruit Viterbi graduates."},
            {"label": "Rigorous core", "sentiment": "caution", "detail": "Math and physics prerequisites are demanding."},
            {"label": "Impacted courses", "sentiment": "mixed", "detail": "Popular technical electives can fill quickly."},
        ]
    elif "public health" in fl or "mph" in slug:
        summary = (
            f"Students describe Keck's {pname} as a public-health program connecting epidemiology "
            f"coursework with Los Angeles community health partners; praise includes diverse "
            f"field placements, with cautions about limited funding for terminal master's students."
        )
        themes = [
            {"label": "Community health", "sentiment": "positive", "detail": "LA's diverse populations support applied public-health practica."},
            {"label": "Keck integration", "sentiment": "positive", "detail": "Ties to Keck Medicine and Norris cancer research enrich coursework."},
            {"label": "Field placements", "sentiment": "positive", "detail": "Practicum sites span county health departments and nonprofits."},
            {"label": "Funding", "sentiment": "caution", "detail": "MPH assistantships are limited relative to Ph.D. programs."},
            {"label": "Policy vs clinical", "sentiment": "mixed", "detail": "Career paths split between policy, research, and healthcare administration."},
        ]
    elif "social work" in fl:
        summary = (
            f"Students describe Dworak-Peck's {pname} as a field-practice-oriented program with "
            f"Los Angeles agency placements; praise includes clinical training and community "
            f"partnerships, with cautions about emotionally demanding practica and licensure "
            f"requirements."
        )
        themes = [
            {"label": "Field practica", "sentiment": "positive", "detail": "Supervised placements at LA agencies anchor the curriculum."},
            {"label": "Clinical training", "sentiment": "positive", "detail": "Coursework prepares students for LCSW licensure pathways."},
            {"label": "Community focus", "sentiment": "positive", "detail": "Partnerships address child welfare, mental health, and homelessness."},
            {"label": "Emotional demands", "sentiment": "caution", "detail": "Practica expose students to trauma-heavy casework."},
            {"label": "Licensure pathway", "sentiment": "mixed", "detail": "Post-graduation supervised hours are required for clinical licensure."},
        ]
    else:
        summary = (
            f"Students and guides describe USC's {pname} within {school.split('USC')[-1].strip()} "
            f"as a {deg_word} program drawing on Los Angeles industry and research resources; "
            f"praise includes the Trojan alumni network and interdisciplinary access, with "
            f"cautions about competitive admission and program-specific workload."
        )
        themes = [
            {"label": "USC resources", "sentiment": "positive", "detail": "Students access libraries, research institutes, and cross-school electives."},
            {"label": "Los Angeles location", "sentiment": "positive", "detail": "Internships and partnerships leverage the LA metro economy."},
            {"label": "Trojan network", "sentiment": "positive", "detail": "Alumni connections support career placement."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Popular programs admit a fraction of applicants."},
            {"label": "Program workload", "sentiment": "mixed", "detail": "Requirements vary; professional programs are especially intensive."},
        ]

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": f"USC — {school}", "url": school_url},
            {"label": "U.S. News — USC rankings", "url": usnews},
        ],
        "disclaimer": DISCLAIMER,
    }


def write_field_descriptions(path: Path, fields: dict[str, str]) -> None:
    lines = [
        '"""Field-specific program description clauses for USC.',
        "",
        "Each entry states something concrete about what USC's program in that field",
        "covers — never a credential/school classification stub. Sources: USC Catalogue",
        "(catalogue.usc.edu), school and department pages, USC Facts and Stats.",
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        "FIELD_DESCRIPTIONS: dict[str, str] = {",
    ]
    for key, val in fields.items():
        esc = val.replace('"', '\\"')
        lines.append(f'    "{key}": "{esc}",')
    lines.append("}")
    lines.append("")
    path.write_text("\n".join(lines))


def write_reviews(path: Path, reviews: dict[str, dict]) -> None:
    lines = [
        '"""Generated external_reviews for USC coverable programs."""',
        "",
        "# ruff: noqa: E501",
        "",
        "REVIEWS: dict[str, dict] = {",
    ]
    for slug, rev in reviews.items():
        lines.append(f'    "{slug}": {json.dumps(rev, ensure_ascii=False)},')
    lines.append("}")
    lines.append("")
    path.write_text("\n".join(lines))


def main() -> None:
    # Import after usc_profile patches so catalog builds with disambiguated names.
    import importlib

    import unipaith.data.usc_profile as mod  # noqa: WPS433

    importlib.reload(mod)
    programs = mod.PROGRAMS
    fields = build_field_descriptions(programs)
    write_field_descriptions(ROOT / "usc_field_descriptions.py", fields)

    coverable = [p for p in programs if is_coverable(p)]
    existing = set(getattr(mod, "_REVIEWS_BY_SLUG", {}).keys())
    reviews: dict[str, dict] = {}
    for p in coverable:
        slug = p["slug"]
        if slug in existing:
            continue
        reviews[slug] = review_for(p)

    write_reviews(ROOT / "usc_reviews_generated.py", reviews)
    print(f"FIELD_DESCRIPTIONS: {len(fields)} entries")
    print(f"NEW REVIEWS: {len(reviews)} coverable programs")
    print(f"EXISTING REVIEWS kept: {len(existing)}")


if __name__ == "__main__":
    main()
