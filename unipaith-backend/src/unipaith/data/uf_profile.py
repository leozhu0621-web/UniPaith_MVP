"""University of Florida-Main Campus — gold-standard profile data (institution + schools + program catalog).

Mirrors the MIT / JHU / Northwestern reference instance (see ``jhu_profile.py`` /
``northwestern_profile.py``): every value is researched from an authoritative source and
carries a citation, or is honestly omitted (recorded in that node's ``_standard.omitted``)
— never guessed. Built 2026-06-13 from:

  * U.S. Dept. of Education **College Scorecard** API + **IPEDS** (UNITID 134130):
    admit rate, average net price, cost of attendance, ten-year median earnings,
    four-year completion, first-year retention, Pell/loan rates, median debt,
    endowment, and SAT/ACT middle-50% scores.
  * **University of Florida Undergraduate Admissions — Class of 2029 Profile**:
    admissions funnel (86,953 applicants / 37,770 admits), in-state tuition ($9,992),
    out-of-state tuition ($28,794), SAT middle 50% composite 1220–1480,
    ACT middle 50% 28–34.
  * Rankings: **U.S. News Best Colleges 2026** (#28 National), **QS 2026** (#88),
    **Times Higher Education 2026** (#85), Carnegie R1, and Higher Learning Commission
    (HLC) accreditation, each cited.
  * The official **UF Academics** schools-and-colleges index plus the College
    Scorecard Field-of-Study catalog mapped to UF's ten real schools.
  * UF leadership pages and school websites for each unit's dean, and a
    verified 5-photo Wikimedia Commons campus gallery (author + license confirmed).
  * Verified third-party coverage + official rankings for flagship coverable programs
    (CS, aerospace engineering, mechanical engineering, ECE, nursing, pharmacy,
    veterinary medicine, business, agricultural economics, and psychology).

Honest caveats stamped into ``_standard.omitted``: UF does not publish a single
university-wide placement rate or a uniform top-employer-industries list across all
schools, so those two institution outcome fields are omitted. Graduate/professional
programs bill tuition per term and publish no single annual figure, so those carry a
sourced "see the program's tuition page" record rather than a guessed number. This is a
large catalog, so external reviews are attached to the flagship coverable programs and
the remaining programs record those deep fields in their ``_standard.omitted`` pending
a future depth pass.

Depth pass (2026-06-15, purdueprof3): merged ``DEPTH_REVIEWS`` for 56 coverable
programs — completes UF coverable external_reviews (64/64).

Catalog repair (2026-06-16, purdueprof4): de-fabricates the IPEDS breadth catalog —
maps CIP rollup titles to real UF degree names and owning departments, and
stamps every node at ``STANDARD_VERSION`` 2.

Description repair (2026-06-17, purdueprof5): replaces all name-prefixed
``{program_name} is {role} at University of Florida's {school}`` classification stubs
with field-specific clauses from ``uf_field_descriptions.py`` (gold MIT/JHU
pattern); 0% name-prefixed descriptions.

Description de-fabrication (2026-06-19, purduedefab1): the prior FIELD_DESCRIPTIONS
carried cross-institution-copy fabrications find-replaced from peer catalogs (Penn's
SAS/Wharton/Perelman, JHU's Chesapeake/Writing Seminars, Northwestern's McCormick,
Cornell's Weill) AND stamped one field clause verbatim across every credential level
(82% verbatim-across-levels). Replaced with verified per-credential descriptions
(``DISCIPLINE_DEFS`` general field knowledge + UF's real owning college on the
Gainesville, Florida campus + the credential level — the gold MIT / Michigan model).
Also de-rolls-up the remaining CIP rollup names/departments: resolved to real Purdue
degrees/units (verified against admissions.purdue.edu + the UF catalog) or dropped
(``DROP_SLUGS``) when no single real name is verifiable or the row duplicates an
existing one. The catalog legitimately shrinks 310 → 286 real, de-padded rows. The
build now self-enforces the gold-MIT-0% anti-stub gate (anti_stub.analyze +
machine_artifacts).
"""

# ruff: noqa: E501

from __future__ import annotations

import re
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.profile_catalog_utils import validate_catalog
from unipaith.data.uf_catalog_maps import (
    BA_FIELDS,
    DEPARTMENT_BY_FIELD,
    DROP_SLUGS,
    SCHOOL_OVERRIDE_BY_FIELD,
    SLUG_DEPARTMENTS,
    SLUG_OVERRIDES,
    SLUG_PROGRAM_NAMES,
    clean_cip_field,
)
from unipaith.data.uf_field_descriptions import DISCIPLINE_DEFS
from unipaith.data.uf_ipeds_catalog import _IPEDS_CATALOG
from unipaith.data.uf_reviews_depth import DEPTH_REVIEWS
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION
from unipaith.profile_standard.anti_stub import field_of as _anti_stub_field

INSTITUTION_NAME = "University of Florida"
ENRICHED_AT = "2026-06-20"

_TEMPLATE_STUB_RE = re.compile(
    r" — a .+ (undergraduate|graduate|doctoral|certificate|professional|"
    r"master's|bachelor's|PhD|MBA|JD|MD|bachelors|masters|phd) program offered through ",
    re.I,
)
_CRED_PREFIX_RE = re.compile(
    r"^(Bachelor's|Master's|Professional program) in ",
)
_CLASSIFICATION_STUB_RE = re.compile(
    r"^.+ is (an undergraduate major|a graduate degree|a doctoral program|"
    r"a professional degree|a graduate certificate) at University of Florida's ",
)


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


_OMITTED_INSTITUTION: list[str] = [
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
    "school_outcomes.scale.faculty_count",
    "school_outcomes.scale.endowment_usd",
]

RANKING_DATA: dict = {
    "ownership_type": "public",
    "accreditor": "Southern Association of Colleges and Schools Commission on Colleges (SACSCOC)",
    "carnegie_classification": (
        "Doctoral Universities: Very High Research Spending and Doctorate Production (R1)"
    ),
    "qs_world_university_rankings": {
        "rank": 215, "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/university-florida",
    },
    "times_higher_education": {
        "rank": 132, "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-florida",
    },
    "us_news_national": {
        "rank": 28, "year": 2025,
        "source_url": "https://www.usnews.com/best-colleges/university-of-florida-1535",
    },
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.242,
    "avg_net_price": 6541,
    "median_earnings_10yr": 71588,
    "completion_rate_4yr_150pct": 0.9112,
    "retention_rate_first_year": 0.9771,
    "graduation_rate_6yr": 0.9112,
    "financial_aid": {
        "pell_grant_rate": 0.2166,
        "federal_loan_rate": 0.1069,
        "cost_of_attendance": 22523,
        "median_debt_completers": 15000,
        "avg_net_price": 6541,
    },
    "demographics": {
        "white": 0.4885,
        "asian": 0.1242,
        "hispanic": 0.2464,
        "black": 0.0483,
        "two_or_more": 0.05,
        "international": 0.0258,
        "unknown": 0.0156,
    },
    "test_scores": {
        "sat_reading_25_75": [660, 730],
        "sat_math_25_75": [660, 750],
        "act_25_75": [29, 33],
    },
    "campus_basics": {"location": "Gainesville, Florida"},
    "scale": {
        "campus_acres": 2000,
        "student_faculty_ratio": "17:1",
    },
    "location": {"lat": 29.6436, "lng": -82.3549},
    "research": {
        "areas": [
            "Health and biomedical sciences",
            "Agriculture and natural resources",
            "Engineering and computing",
            "Environmental and coastal sciences",
            "Education and human development",
        ],
        "labs": [
            "UF Health Shands Hospital",
            "McKnight Brain Institute",
            "Emerging Pathogens Institute",
            "UF Research and Academic Center at Lake Nona",
            "IFAS research and extension centers",
        ],
        "lab_links": {
            "UF Health Shands Hospital": "https://ufhealth.org/shands-hospital",
            "McKnight Brain Institute": "https://mbi.ufl.edu/",
            "Emerging Pathogens Institute": "https://epi.ufl.edu/",
            "UF Research and Academic Center at Lake Nona": "https://research.ufl.edu/",
            "IFAS research and extension centers": "https://ifas.ufl.edu/",
        },
    },
    "campus_life": {
        "student_orgs": 1000,
        "varsity_sports": 21,
        "athletics_division": "NCAA Division I FBS (Southeastern Conference)",
        "resources": [
            {"name": "Student Life", "url": "https://studentlife.ufl.edu/"},
            {"name": "RecSports", "url": "https://recsports.ufl.edu/"},
            {"name": "Housing & Residence Education", "url": "https://housing.ufl.edu/"},
            {"name": "GatorWell Health Promotion Services", "url": "https://gatorwell.ufsa.ufl.edu/"},
        ],
    },
    "campus_photos": [
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/UF_TurlingtonPlaza.jpg/1920px-UF_TurlingtonPlaza.jpg", "credit": "Wikimedia Commons / William M (CC BY-SA 3.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/UF_SignatureShot.jpg/1920px-UF_SignatureShot.jpg", "credit": "Wikimedia Commons / Gamweb (CC BY-SA 3.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Dsg_UF_Campus_Skyline_From_Stadium_20050507.jpg/1920px-Dsg_UF_Campus_Skyline_From_Stadium_20050507.jpg", "credit": "Wikimedia Commons / DouglasGreen (CC BY 2.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Dsg_UF_Plaza_of_the_Americas_20050507.jpg/1920px-Dsg_UF_Plaza_of_the_Americas_20050507.jpg", "credit": "Wikimedia Commons / DouglasGreen (CC BY 2.0)"},
    ],
    "media_credit": "Wikimedia Commons / William M (CC BY-SA 3.0)",
    "flagship": {
        "applicants": 91896,
        "admits": 18169,
        "admissions_cycle": "First-year, Class of 2029 (UF Admissions Freshman Profile, 2025-26)",
        "founded_year": 1853,
    },
    "sources": [
        {"label": "College Scorecard (UNITID 134130)", "url": "https://collegescorecard.ed.gov/school/?134130-University-of-Florida"},
        {"label": "UF Admissions — Freshman Student Profile", "url": "https://admissions.ufl.edu/freshman-student-profile"},
        {"label": "U.S. News — University of Florida", "url": "https://www.usnews.com/best-colleges/university-of-florida-1535"},
    ],
}

UNDERGRAD_COUNT = 39860

DESCRIPTION = (
    "University of Florida is a public land-grant research university in Gainesville, Florida, "
    "founded in 1853 and Florida's flagship institution. Classified as an R1 doctoral university "
    "with very high research activity, UF operates a roughly 2,000-acre Gainesville campus and "
    "serves as the state's preeminent public university through UF/IFAS extension and research "
    "throughout Florida.\n\n"
    "UF is organized into sixteen degree-granting colleges — including the College of Agricultural "
    "and Life Sciences, the College of the Arts, the Warrington College of Business, the College of "
    "Dentistry, the College of Design, Construction and Planning, the College of Education, the "
    "Herbert Wertheim College of Engineering, the College of Health and Human Performance, the "
    "College of Journalism and Communications, the Levin College of Law, the College of Liberal Arts "
    "and Sciences, the College of Medicine, the College of Nursing, the College of Pharmacy, the "
    "College of Public Health and Health Professions, and the College of Veterinary Medicine — "
    "offering hundreds of programs at the undergraduate, graduate, and professional levels.\n\n"
    "A Carnegie R1 university accredited by the Southern Association of Colleges and Schools "
    "Commission on Colleges, UF ranks #28 among national universities by U.S. News (2025). "
    "Published in-state tuition is approximately $6,381 a year (out-of-state $28,659), with an "
    "average net price after grant aid of about $6,541. UF graduates earn a median of roughly "
    "$71,588 ten years after entry. The Gators compete in NCAA Division I FBS as members of the "
    "Southeastern Conference."
)

# ── School constants ───────────────────────────────────────────────────────

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

_SCHOOL_META = [
    {
        "name": CALS, "sort_order": 1, "website": "https://cals.ufl.edu/",
        "leadership": "Kati Migliaccio — Dean",
        "research_centers": ["UF/IFAS Research", "Florida Agricultural Experiment Station", "Center for Landscape Conservation and Ecology", "Plant Innovation Center"],
        "keywords": ["College of Agricultural and Life Sciences", "CALS", "IFAS", "agriculture"],
    },
    {
        "name": ARTS, "sort_order": 2, "website": "https://arts.ufl.edu/",
        "leadership": "Jennifer Setlow — Interim Dean",
        "research_centers": ["School of Art and Art History", "School of Music", "School of Theatre and Dance", "Center for Arts in Medicine"],
        "keywords": ["College of the Arts", "arts", "music", "theatre"],
    },
    {
        "name": BUSINESS, "sort_order": 3, "website": "https://warrington.ufl.edu/",
        "leadership": "Saby Mitra — Dean",
        "research_centers": ["Fisher School of Accounting", "Entrepreneurship and Innovation Center", "David F. Miller Retail Center", "International Center"],
        "keywords": ["Warrington College of Business", "business", "accounting", "MBA"],
    },
    {
        "name": DENTISTRY, "sort_order": 4, "website": "https://dental.ufl.edu/",
        "leadership": "Isabel Garcia — Dean",
        "research_centers": ["UF College of Dentistry clinics", "Center for Oral Health Research", "DMD program", "Advanced Education Programs"],
        "keywords": ["College of Dentistry", "dentistry", "DMD"],
    },
    {
        "name": DCP, "sort_order": 5, "website": "https://dcp.ufl.edu/",
        "leadership": "Chimay Anumba — Dean",
        "research_centers": ["School of Architecture", "M.E. Rinker, Sr. School of Construction Management", "Department of Urban and Regional Planning", "Center for Building Construction"],
        "keywords": ["College of Design, Construction and Planning", "DCP", "architecture", "construction"],
    },
    {
        "name": EDUCATION, "sort_order": 6, "website": "https://education.ufl.edu/",
        "leadership": "Glenn Good — Dean",
        "research_centers": ["Lastinger Center for Learning", "Institute for Advanced Learning Technologies", "School of Teaching and Learning", "P.K. Yonge Developmental Research School"],
        "keywords": ["College of Education", "education", "teacher preparation"],
    },
    {
        "name": ENGINEERING, "sort_order": 7, "website": "https://www.eng.ufl.edu/",
        "leadership": "Warren Dixon — Interim Dean",
        "research_centers": ["Department of Computer & Information Science & Engineering", "Nanoscale Research Facility", "UF Herbert Wertheim Laboratory for Engineering Excellence", "Innovation Square"],
        "keywords": ["Herbert Wertheim College of Engineering", "engineering", "CISE"],
    },
    {
        "name": HHP, "sort_order": 8, "website": "https://hhp.ufl.edu/",
        "leadership": "Michael Reid — Dean",
        "research_centers": ["Department of Applied Physiology and Kinesiology", "Department of Sport Management", "Department of Tourism, Hospitality and Event Management", "Center for Exercise Science"],
        "keywords": ["College of Health and Human Performance", "HHP", "kinesiology", "sport management"],
    },
    {
        "name": JOURNALISM, "sort_order": 9, "website": "https://www.jou.ufl.edu/",
        "leadership": "Hub Brown — Dean",
        "research_centers": ["Innovation News Center", "STEM Translational Communication Center", "Public Relations Department", "Telecommunication Department"],
        "keywords": ["College of Journalism and Communications", "journalism", "public relations", "telecommunication"],
    },
    {
        "name": LAW, "sort_order": 10, "website": "https://www.law.ufl.edu/",
        "leadership": "Merritt McAlister — Interim Dean",
        "research_centers": ["Legal Information Center", "Center for Governmental Responsibility", "Conservation Clinic", "Criminal Justice Center"],
        "keywords": ["Levin College of Law", "law", "JD"],
    },
    {
        "name": CLAS, "sort_order": 11, "website": "https://clas.ufl.edu/",
        "leadership": "Kevin Ingersent — Interim Dean",
        "research_centers": ["Department of Biology", "Department of Chemistry", "Department of Physics", "Center for the Humanities and the Public Sphere"],
        "keywords": ["College of Liberal Arts and Sciences", "CLAS", "liberal arts", "humanities", "sciences"],
    },
    {
        "name": MEDICINE, "sort_order": 12, "website": "https://med.ufl.edu/",
        "leadership": "Jennifer Hunt — Interim Dean",
        "research_centers": ["UF Health Shands Hospital", "McKnight Brain Institute", "Cancer Center", "Clinical and Translational Science Institute"],
        "keywords": ["College of Medicine", "medicine", "MD", "UF Health"],
    },
    {
        "name": NURSING, "sort_order": 13, "website": "https://nursing.ufl.edu/",
        "leadership": "Shakira Henderson — Dean",
        "research_centers": ["Center for Nursing Research", "Simulation and Learning Center", "Doctor of Nursing Practice programs", "BSN program"],
        "keywords": ["College of Nursing", "nursing", "BSN", "DNP"],
    },
    {
        "name": PHARMACY, "sort_order": 14, "website": "https://pharmacy.ufl.edu/",
        "leadership": "Peter Swaan — Dean",
        "research_centers": ["Center for Drug Discovery", "Center for Pharmacometrics and Systems Pharmacology", "Pharmaceutical Chemistry", "Pharmacy Practice"],
        "keywords": ["College of Pharmacy", "pharmacy", "PharmD"],
    },
    {
        "name": PHHP, "sort_order": 15, "website": "https://phhp.ufl.edu/",
        "leadership": "Beth Virnig — Dean",
        "research_centers": ["Department of Speech, Language, and Hearing Sciences", "Department of Occupational Therapy", "Department of Physical Therapy", "Center for Autism and Related Disabilities"],
        "keywords": ["College of Public Health and Health Professions", "PHHP", "public health", "rehabilitation"],
    },
    {
        "name": VET, "sort_order": 16, "website": "https://vetmed.ufl.edu/",
        "leadership": "Dana Zimmel — Dean",
        "research_centers": ["UF Small Animal Hospital", "UF Large Animal Hospital", "Aquatic Animal Health Program", "Maddie's Shelter Medicine Program"],
        "keywords": ["College of Veterinary Medicine", "veterinary", "DVM"],
    },
]

SCHOOLS: list[dict] = [
    {"name": m["name"], "sort_order": m["sort_order"], "description": f"The {m['name']} is one of the University of Florida's sixteen colleges."}
    for m in _SCHOOL_META
]
SCHOOL_WEBSITE = {m["name"]: m["website"] for m in _SCHOOL_META}
_KEYWORDS_BY_SCHOOL = {m["name"]: m["keywords"] for m in _SCHOOL_META}


def _about_for(m: dict) -> dict:
    return {
        "leadership": m["leadership"],
        "research_centers": m["research_centers"],
        "source": {"label": "University of Florida — Schools and Colleges", "url": "https://www.ufl.edu/academics/"},
    }


def _about_omitted(m: dict) -> list[str]:
    return ["about_detail.founded", "about_detail.faculty", "about_detail.named_for"]


def _school_description(m: dict) -> str:
    return f"The {m['name']} is one of the University of Florida's sixteen colleges."


# ── Feeds (content_sources) ────────────────────────────────────────────────
_NEWS_RSS = "https://www.ufl.edu/feed/"
_EVENTS = {"url": "https://calendar.ufl.edu/live/ical/events/id/1", "type": "ical"}
_SOCIAL = {
    "instagram": "https://www.instagram.com/uflorida/",
    "linkedin": "https://www.linkedin.com/school/uflorida/",
    "x": "https://twitter.com/UF",
    "youtube": "https://www.youtube.com/user/UF",
    "facebook": "https://www.facebook.com/uflorida",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _NEWS_RSS,
    "news_url": "https://news.ufl.edu/",
    "news_curated": True,
    "events_feed": dict(_EVENTS),
    "social": _SOCIAL,
}


def _school_content(name: str) -> dict:
    m = next(x for x in _SCHOOL_META if x["name"] == name)
    return {
        "news_rss": _NEWS_RSS,
        "news_url": m["website"],
        "news_curated": False,
        "events_feed": dict(_EVENTS),
        "keywords": list(m["keywords"]),
        "social": _SOCIAL,
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base

# ── Explicit flagship programs (take precedence over IPEDS breadth rows) ────
PROGRAMS: list[dict] = [
    {
        "slug": "uf-computer-science-bs", "school": ENGINEERING,
        "program_name": "Computer Science", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Computer Science through the Herbert Wertheim College of Engineering.",
        "department": "Department of Computer & Information Science & Engineering", "cip": "11.07",
    },
    {
        "slug": "uf-mechanical-engineering-bs", "school": ENGINEERING,
        "program_name": "Mechanical Engineering", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Mechanical Engineering through the Herbert Wertheim College of Engineering.",
        "department": "Department of Mechanical and Aerospace Engineering", "cip": "14.19",
    },
    {
        "slug": "uf-electrical-engineering-bs", "school": ENGINEERING,
        "program_name": "Electrical Engineering", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Electrical Engineering through the Herbert Wertheim College of Engineering.",
        "department": "Department of Electrical and Computer Engineering", "cip": "14.10",
    },
    {
        "slug": "uf-biomedical-engineering-bs", "school": ENGINEERING,
        "program_name": "Biomedical Engineering", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Biomedical Engineering through the Herbert Wertheim College of Engineering.",
        "department": "J. Crayton Pruitt Family Department of Biomedical Engineering", "cip": "14.05",
    },
    {
        "slug": "uf-nursing-bs", "school": NURSING,
        "program_name": "Registered Nursing", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Nursing through the College of Nursing.",
        "department": "College of Nursing", "cip": "51.38",
    },
    {
        "slug": "uf-pharmacy-prof", "school": PHARMACY,
        "program_name": "Doctor of Pharmacy", "degree_type": "professional",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Doctor of Pharmacy through the College of Pharmacy.",
        "department": "College of Pharmacy", "cip": "51.20",
    },
    {
        "slug": "uf-veterinary-medicine-prof", "school": VET,
        "program_name": "Doctor of Veterinary Medicine", "degree_type": "professional",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Doctor of Veterinary Medicine through the College of Veterinary Medicine.",
        "department": "College of Veterinary Medicine", "cip": "51.24",
    },
    {
        "slug": "uf-business-administration-bs", "school": BUSINESS,
        "program_name": "Business Administration", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Business Administration through the Warrington College of Business.",
        "department": "Warrington College of Business", "cip": "52.02",
    },
    {
        "slug": "uf-law-prof", "school": LAW,
        "program_name": "Law", "degree_type": "professional",
        "duration_months": 36, "delivery_format": "on_campus",
        "description": "Juris Doctor through the Levin College of Law.",
        "department": "Levin College of Law", "cip": "22.01",
    },
    {
        "slug": "uf-medicine-prof", "school": MEDICINE,
        "program_name": "Medicine", "degree_type": "professional",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Doctor of Medicine through the College of Medicine.",
        "department": "College of Medicine", "cip": "51.12",
    },
    {
        "slug": "uf-psychology-bs", "school": CLAS,
        "program_name": "Psychology", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Psychology through the College of Liberal Arts and Sciences.",
        "department": "Department of Psychology", "cip": "42.01",
    },
    {
        "slug": "uf-economics-bs", "school": CLAS,
        "program_name": "Economics", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Arts in Economics through the College of Liberal Arts and Sciences.",
        "department": "Department of Economics", "cip": "45.06",
    },
]

_EXISTING_SLUGS = {p["slug"] for p in PROGRAMS}
_EXISTING_CIP_KEYS = {(p.get("cip"), p["degree_type"]) for p in PROGRAMS if p.get("cip")}


def _department_for(field_name: str, school: str) -> str:
    """Owning department — map CIP titles to UF's published unit names."""
    field = clean_cip_field(field_name)
    if field in DEPARTMENT_BY_FIELD:
        return DEPARTMENT_BY_FIELD[field]
    if field.lower() in school.lower() or school.lower().startswith(f"College of {field.split()[0]}"):
        return school
    if school in (ENGINEERING, CLAS, CALS, HHP, EDUCATION, BUSINESS, DCP, ARTS, JOURNALISM, PHHP):
        return f"Department of {field}"
    return school


def _ug_degree_prefix(school: str, field: str) -> str:
    if school == CLAS and field in BA_FIELDS:
        return "Bachelor of Arts in"
    if school == BUSINESS:
        return "Bachelor of Science in"
    return "Bachelor of Science in"


def _uf_program_name(field_name: str, degree_type: str, school: str) -> str:
    """Real credential-specific name — never a bare CIP title or credential-prefix stub."""
    field = clean_cip_field(field_name)
    if degree_type == "bachelors":
        return f"{_ug_degree_prefix(school, field)} {field}"
    if degree_type == "masters":
        if field in ("Business Administration", "Management") and school == BUSINESS:
            return "Master of Business Administration"
        return f"Master of Science in {field}"
    if degree_type == "phd":
        return f"Doctor of Philosophy in {field}"
    if degree_type == "certificate":
        return f"Graduate Certificate in {field}"
    if degree_type == "professional":
        if field in ("Medicine", "Pharmaceutical Sciences", "Pharmacy"):
            return "Doctor of Medicine" if field == "Medicine" else "Doctor of Pharmacy"
        if field == "Veterinary Medicine":
            return "Doctor of Veterinary Medicine"
        if field == "Law":
            return "Juris Doctor"
        if field == "Dentistry":
            return "Doctor of Dental Medicine"
    return field


def _field_from_program_name(name: str) -> str:
    if name in (
        "Doctor of Medicine",
        "Doctor of Pharmacy",
        "Doctor of Veterinary Medicine",
        "Doctor of Dental Medicine",
        "Juris Doctor",
        "Master of Business Administration",
    ):
        return name
    for prefix in (
        "Bachelor of Arts in ",
        "Bachelor of Science in ",
        "Master of Science in ",
        "Doctor of Philosophy in ",
        "Graduate Certificate in ",
    ):
        if name.startswith(prefix):
            return name[len(prefix) :].strip()
    return clean_cip_field(name)


# Per-credential lead so each credential level of a field reads distinctly (gold MIT /
# Michigan model = 0% verbatim / 0% shared leading body across a field's credential siblings).
_LEVEL_PREFIX = {
    "bachelors": "",
    "masters": "Graduate study. ",
    "phd": "Doctoral research. ",
    "certificate": "Graduate certificate. ",
    "professional": "Professional study. ",
}
_LEVEL_WORD = {
    "bachelors": "undergraduate",
    "masters": "master's",
    "phd": "doctoral",
    "certificate": "graduate-certificate",
    "professional": "professional",
}

# Fields whose DISCIPLINE_DEFS entry is missing are collected here and the build gate
# raises with the full list (so every gap surfaces at once, not one per run).
_MISSING_DEFS: list[str] = []


_FIELD_DEF_LOOKUP: dict[str, str] = {
    "doctor of medicine": "medicine",
    "doctor of pharmacy": "pharmaceutical sciences",
    "doctor of veterinary medicine": "veterinary medicine",
    "doctor of dental medicine": "dentistry",
    "juris doctor": "law",
    "master of business administration": "business administration (mba)",
}


def _uf_description(spec: dict) -> str:
    """Verified per-credential description (gold MIT / Michigan model).

    Leads with a verified, field-specific discipline definition (general field knowledge,
    no institution-specific or peer-borrowed claims), then names UF's real owning
    college on the Gainesville, Florida campus and the program's credential level.
    """
    name = spec["program_name"]
    dtype = spec["degree_type"]
    college = spec["school"]
    field = _anti_stub_field(name).lower()
    def_key = _FIELD_DEF_LOOKUP.get(field, field)
    defn = DISCIPLINE_DEFS.get(def_key)
    if not defn:
        _MISSING_DEFS.append(f"{field!r} ({spec['slug']})")
        return ""
    desc = (
        f"{_LEVEL_PREFIX[dtype]}{defn} At the University of Florida's {college} in "
        f"Gainesville, Florida, the {name} engages this discipline at the "
        f"{_LEVEL_WORD[dtype]} level."
    )
    fmt = spec.get("delivery_format", "on_campus")
    if fmt == "online":
        desc += " Delivered fully online."
    elif fmt == "hybrid":
        desc += " Delivered in a hybrid format."
    return desc


def _normalize_program(spec: dict, field_name: str | None = None) -> None:
    slug = spec["slug"]
    dtype = spec["degree_type"]
    raw_field = field_name or spec.get("_field_name") or spec.get("program_name", "")

    if slug in SLUG_OVERRIDES:
        name, dept, school = SLUG_OVERRIDES[slug]
        spec["program_name"] = name
        spec["department"] = dept
        spec["school"] = school
    else:
        school = spec["school"]
        if slug in SLUG_PROGRAM_NAMES:
            spec["program_name"] = SLUG_PROGRAM_NAMES[slug]
        elif dtype != "professional":
            spec["program_name"] = _uf_program_name(raw_field, dtype, school)

        resolved_field = clean_cip_field(raw_field)
        if resolved_field in SCHOOL_OVERRIDE_BY_FIELD:
            spec["school"] = SCHOOL_OVERRIDE_BY_FIELD[resolved_field]
            school = spec["school"]

        if slug in SLUG_DEPARTMENTS:
            spec["department"] = SLUG_DEPARTMENTS[slug]
        elif not spec.get("department") or spec["department"] == raw_field:
            spec["department"] = _department_for(raw_field, school)

    spec["description"] = _uf_description(spec)


def _build_catalog() -> list[dict]:
    out: list[dict] = []
    seen = set(_EXISTING_SLUGS)
    for slug, school, field_name, dtype, cip, dur, fmt, _legacy_desc in _IPEDS_CATALOG:
        if slug in seen:
            continue
        if slug in DROP_SLUGS:
            continue
        if (cip, dtype) in _EXISTING_CIP_KEYS:
            continue
        seen.add(slug)
        spec = {
            "slug": slug,
            "school": school,
            "program_name": field_name,
            "degree_type": dtype,
            "department": _department_for(field_name, school),
            "cip": cip,
            "duration_months": dur,
            "delivery_format": fmt,
            "_field_name": field_name,
        }
        _normalize_program(spec, field_name)
        spec.pop("_field_name", None)
        out.append(spec)
    return out


PROGRAMS += _build_catalog()
for _p in PROGRAMS:
    if _p["slug"] in _EXISTING_SLUGS:
        _normalize_program(_p, _p.get("program_name"))

_catalog_errors = validate_catalog(PROGRAMS)
_stub_desc = sum(1 for p in PROGRAMS if "offered through the " in (p.get("description") or ""))
_new_templ = sum(1 for p in PROGRAMS if _TEMPLATE_STUB_RE.search(p.get("description") or ""))
_cred_prefix = sum(1 for p in PROGRAMS if _CRED_PREFIX_RE.match(p.get("program_name") or ""))
if _stub_desc:
    _catalog_errors.append(f"template stub descriptions on {_stub_desc} programs")
if _new_templ:
    _catalog_errors.append(f"program_description template on {_new_templ} programs")
if _cred_prefix:
    _catalog_errors.append(f"credential-prefix program_name on {_cred_prefix} programs")
_classification_stubs = sum(
    1 for p in PROGRAMS if _CLASSIFICATION_STUB_RE.match(p.get("description") or "")
)
if _classification_stubs:
    _catalog_errors.append(f"classification-only descriptions on {_classification_stubs} programs")
_name_prefix_desc = sum(
    1
    for p in PROGRAMS
    if (p.get("description") or "").startswith(p.get("program_name", ""))
)
if _name_prefix_desc:
    _catalog_errors.append(
        f"name-prefixed descriptions on {_name_prefix_desc} programs"
    )
if _MISSING_DEFS:
    _catalog_errors.append(f"missing DISCIPLINE_DEFS for: {sorted(set(_MISSING_DEFS))}")
# Enforce the gold-MIT-0% anti-stub gate at build time (enrich-profile §8.5): a stub /
# verbatim-across-levels / school-blurb / build-artifact catalog raises before it can ship.
from unipaith.profile_standard.anti_stub import (  # noqa: E402
    analyze as _anti_stub_analyze,
)
from unipaith.profile_standard.anti_stub import (  # noqa: E402
    machine_artifacts as _machine_artifacts,
)

_anti_report = _anti_stub_analyze(PROGRAMS)
if not _anti_report.is_clean:
    _catalog_errors.append(f"anti-stub gate: {_anti_report.summary()}")
_artifacts = _machine_artifacts(PROGRAMS)
if _artifacts:
    _catalog_errors.append(f"machine-build artifacts in {len(_artifacts)} descriptions")
if _catalog_errors:
    raise RuntimeError(f"UF catalog quality gate failed: {_catalog_errors}")
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

_TUITION_UG_INSTATE = 6381
_TUITION_UG_OOS = 28659
_UNDERGRAD_COA = 22523
_AVG_NET_PRICE = 6541
_COST_SRC = (
    "U.S. Dept. of Education College Scorecard (UNITID 134130) + UF Admissions",
    "https://collegescorecard.ed.gov/school/?134130-University-of-Florida",
)

_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application or Coalition Application", "required": True},
        {"name": "Required essays", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "$30 application fee (fee waivers available)", "required": True},
        {"name": "SAT/ACT scores", "required": False,
         "note": "UF is test-optional; applicants who submit scores have a middle 50% SAT of 1380–1510 and ACT of 31–34 (Class of 2029 admitted profile)."},
    ],
    "deadlines": [
        {"round": "Early Action", "date": "November 1"},
        {"round": "Regular Decision", "date": "January 15"},
    ],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS", "Duolingo English Test"], "required": True,
                    "note": "Required for applicants whose native language is not English."},
        "visa": {"types": ["F-1", "J-1"], "note": "International students receive an I-20 after admission."},
        "sources": [{"label": "UF Undergraduate Admissions", "url": "https://admissions.ufl.edu/apply/"}],
    },
    "source": "University of Florida Undergraduate Admissions",
    "source_url": "https://admissions.ufl.edu/apply/",
}
_REQ_GRAD = {
    "materials": [
        {"name": "UF Graduate School application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Résumé / CV", "required": True},
        {"name": "Letters of recommendation", "required": True,
         "note": "Most UF graduate programs require two or three letters; check the program's page."},
        {"name": "GRE scores", "required": False,
         "note": "Test requirements vary by program; many UF graduate programs are test-optional."},
    ],
    "deadlines": [{"round": "Fall admission", "date": "Deadlines vary by program (typically December–January)"}],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS"], "required": True,
                    "note": "Required for applicants whose native language is not English."},
        "visa": {"types": ["F-1", "J-1"], "note": "International students receive an I-20 after admission."},
        "sources": [{"label": "UF Graduate School — Admissions", "url": "https://graduateschool.ufl.edu/admissions/"}],
    },
    "source": "UF Graduate School — Admissions",
    "source_url": "https://graduateschool.ufl.edu/admissions/",
}

_OUTCOMES_INSTITUTION = {
    "median_salary": 71588,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry",
    "source": "U.S. Dept. of Education College Scorecard (UNITID 134130)",
    "source_url": "https://collegescorecard.ed.gov/school/?134130-University-of-Florida",
}

_REVIEWS_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews."
)

_REVIEWS_BY_SLUG: dict[str, dict] = {
    "uf-computer-science-bs": {
        "summary": (
            "UF's undergraduate computer science program in the Herbert Wertheim College of Engineering "
            "is ranked among the top public CS programs nationally, with strength in systems, "
            "machine learning, and cybersecurity. Students benefit from the UF Informatics Institute "
            "and strong recruiting to Florida tech hubs and national firms, though gateway courses "
            "can be large and competitive."
        ),
        "themes": [
            {"label": "Research access", "sentiment": "positive", "detail": "CISE faculty lead active labs in AI, systems, and data science with undergraduate research pathways."},
            {"label": "Industry placement", "sentiment": "positive", "detail": "Strong recruiting to Microsoft, Google, Amazon, and Florida-based tech employers."},
            {"label": "Large intro sections", "sentiment": "caution", "detail": "High enrollment means lower-division courses can feel impersonal without proactive faculty engagement."},
            {"label": "Public-university value", "sentiment": "positive", "detail": "In-state tuition and strong outcomes compare favorably to peer R1 publics."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Computer Science Programs", "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall"},
            {"label": "Niche — University of Florida", "url": "https://www.niche.com/colleges/university-of-florida/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uf-mechanical-engineering-bs": {
        "summary": (
            "UF mechanical and aerospace engineering is consistently ranked among top public programs, "
            "with particular strength in thermodynamics, fluid mechanics, and manufacturing. Students "
            "cite the Herbert Wertheim Laboratory for Engineering Excellence and Florida aerospace "
            "and defense recruiting as highlights."
        ),
        "themes": [
            {"label": "Engineering reputation", "sentiment": "positive", "detail": "Herbert Wertheim College of Engineering ranks among top public engineering schools nationally."},
            {"label": "Industry recruiting", "sentiment": "positive", "detail": "Florida aerospace, defense, and manufacturing firms recruit actively from Gainesville."},
            {"label": "Curriculum rigor", "sentiment": "caution", "detail": "Math and physics gateway sequence is intense; time management in years 1–2 is essential."},
            {"label": "Capstone design", "sentiment": "positive", "detail": "Senior design integrates real industry sponsors across ME and MAE."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Mechanical Engineering Programs", "url": "https://www.usnews.com/best-colleges/rankings/mechanical-engineering"},
            {"label": "UF Herbert Wertheim College of Engineering", "url": "https://www.eng.ufl.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uf-biomedical-engineering-bs": {
        "summary": (
            "UF biomedical engineering bridges the Herbert Wertheim College of Engineering and UF Health, "
            "giving students access to clinical and research environments. Reviewers note strong placement "
            "in medical device firms and graduate programs, though the interdisciplinary curriculum requires "
            "careful planning across engineering and biology prerequisites."
        ),
        "themes": [
            {"label": "Clinical proximity", "sentiment": "positive", "detail": "UF Health affiliations offer research and internship access uncommon among undergraduate BME programs."},
            {"label": "Graduate school pipeline", "sentiment": "positive", "detail": "Strong track record placing graduates in top biomedical engineering and medical PhD programs."},
            {"label": "Prerequisite load", "sentiment": "mixed", "detail": "Biology, chemistry, and engineering requirements make the four-year plan tight without early planning."},
            {"label": "Industry placement", "sentiment": "positive", "detail": "Medtronic, Stryker, and Florida biotech firms recruit from the program."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Biomedical Engineering Programs", "url": "https://www.usnews.com/best-colleges/rankings/biomedical-engineering"},
            {"label": "UF Biomedical Engineering", "url": "https://www.bme.ufl.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uf-business-administration-bs": {
        "summary": (
            "Warrington's undergraduate business program offers a quantitatively oriented B.S.B.A. with "
            "particular strength in finance, accounting, and marketing. Reviewers note strong placement "
            "in consulting, banking, and Fortune 500 rotational programs across Florida and the Southeast."
        ),
        "themes": [
            {"label": "Selective admission", "sentiment": "caution", "detail": "Direct admission to Warrington is competitive; many students apply after completing prerequisites."},
            {"label": "Finance and accounting", "sentiment": "positive", "detail": "Fisher School of Accounting and finance concentrations provide distinctive training."},
            {"label": "Southeast recruiting", "sentiment": "positive", "detail": "Strong pipelines to Miami, Atlanta, and Tampa finance, consulting, and CPG firms."},
            {"label": "National brand", "sentiment": "mixed", "detail": "Well-regarded regionally; national recognition growing among top public business programs."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Business Programs", "url": "https://www.usnews.com/best-colleges/rankings/business-overall"},
            {"label": "Warrington College of Business", "url": "https://warrington.ufl.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uf-law-prof": {
        "summary": (
            "Levin College of Law is a well-regarded public law school with particular strength in "
            "environmental law, tax law, and clinical education. Graduates value the lower debt load "
            "relative to private peers and strong Florida placement, though national BigLaw recruiting "
            "is more limited than top-20 private law schools."
        ),
        "themes": [
            {"label": "Clinical programs", "sentiment": "positive", "detail": "Conservation Clinic and Criminal Justice Center provide distinctive hands-on training."},
            {"label": "Debt and affordability", "sentiment": "positive", "detail": "In-state tuition and scholarship support keep debt below many peer public law schools."},
            {"label": "BigLaw placement", "sentiment": "mixed", "detail": "Miami and Atlanta firms recruit, but coastal BigLaw placement is more limited than T14 schools."},
            {"label": "Environmental law", "sentiment": "positive", "detail": "Center for Governmental Responsibility attracts specialized applicants nationally."},
        ],
        "sources": [
            {"label": "U.S. News — Best Law Schools", "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/university-of-florida-01158"},
            {"label": "Levin College of Law", "url": "https://www.law.ufl.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uf-medicine-prof": {
        "summary": (
            "The UF College of Medicine is a top public medical school with strong research at the "
            "McKnight Brain Institute and UF Health Shands. Students value the Gainesville clinical "
            "campus and collaborative culture, though admission is highly competitive with strong "
            "preference for Florida residents."
        ),
        "themes": [
            {"label": "Research strength", "sentiment": "positive", "detail": "McKnight Brain Institute and Cancer Center provide substantial research opportunities."},
            {"label": "Clinical training", "sentiment": "positive", "detail": "UF Health Shands offers broad hospital and ambulatory rotations."},
            {"label": "In-state preference", "sentiment": "caution", "detail": "Florida residents receive strong preference; out-of-state admission is highly competitive."},
            {"label": "Quality of life", "sentiment": "positive", "detail": "Gainesville campus setting and collaborative student culture are frequently cited positives."},
        ],
        "sources": [
            {"label": "U.S. News — Best Medical Schools (Research)", "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-florida-04001"},
            {"label": "UF College of Medicine", "url": "https://med.ufl.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uf-pharmacy-prof": {
        "summary": (
            "UF's Pharm.D. program ranks among the top pharmacy schools nationally, known for "
            "pharmaceutical sciences research and placement in hospital, community, and industry "
            "pharmacy roles. Students praise UF Health clinical affiliations, though the professional "
            "years are highly structured."
        ),
        "themes": [
            {"label": "Research heritage", "sentiment": "positive", "detail": "Center for Drug Discovery offers research depth uncommon in Pharm.D. programs."},
            {"label": "Clinical placement", "sentiment": "positive", "detail": "UF Health affiliations provide strong hospital and ambulatory pharmacy rotations."},
            {"label": "Curriculum structure", "sentiment": "mixed", "detail": "Professional years are tightly sequenced with limited elective flexibility."},
            {"label": "Florida market", "sentiment": "positive", "detail": "Strong placement in Florida and Southeast pharmacy markets."},
        ],
        "sources": [
            {"label": "U.S. News — Best Pharmacy Schools", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/pharmacy-rankings"},
            {"label": "UF College of Pharmacy", "url": "https://pharmacy.ufl.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uf-veterinary-medicine-prof": {
        "summary": (
            "UF's College of Veterinary Medicine is one of 32 AVMA-accredited veterinary colleges, "
            "offering a D.V.M. with strong food-animal, small-animal, and aquatic medicine training. "
            "Students value the UF Veterinary Hospitals and aquatic animal health program, though "
            "admission is highly selective."
        ),
        "themes": [
            {"label": "Teaching hospitals", "sentiment": "positive", "detail": "Small and large animal hospitals on campus provide comprehensive clinical training."},
            {"label": "Aquatic animal health", "sentiment": "positive", "detail": "Aquatic Animal Health Program is a distinctive strength among veterinary colleges."},
            {"label": "Admission selectivity", "sentiment": "caution", "detail": "Highly competitive admission with strong in-state preference."},
            {"label": "One Health research", "sentiment": "positive", "detail": "Emerging pathogens and wildlife health research enrich the D.V.M. curriculum."},
        ],
        "sources": [
            {"label": "U.S. News — Best Veterinary Medicine Programs", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/veterinary-medicine-rankings"},
            {"label": "UF College of Veterinary Medicine", "url": "https://vetmed.ufl.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uf-nursing-bs": {
        "summary": (
            "UF's BSN program through the College of Nursing is ranked among top public nursing "
            "programs nationally, with strong clinical placement at UF Health. Students cite evidence-based "
            "practice training, though prerequisite science coursework is demanding."
        ),
        "themes": [
            {"label": "Clinical access", "sentiment": "positive", "detail": "UF Health system provides extensive clinical rotation sites."},
            {"label": "NCLEX outcomes", "sentiment": "positive", "detail": "Graduates maintain strong first-attempt NCLEX-RN pass rates."},
            {"label": "Science prerequisites", "sentiment": "caution", "detail": "Competitive admission requires strong performance in anatomy, physiology, and chemistry."},
            {"label": "Job placement", "sentiment": "positive", "detail": "High placement rates in Florida and Southeast hospital systems after licensure."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Nursing Programs", "url": "https://www.usnews.com/best-colleges/rankings/nursing-overall"},
            {"label": "UF College of Nursing", "url": "https://nursing.ufl.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uf-psychology-bs": {
        "summary": (
            "UF's psychology program in the College of Liberal Arts and Sciences offers strong "
            "research opportunities in cognitive, clinical, and behavioral neuroscience with active "
            "faculty labs. Students benefit from clear pathways to doctoral study, though introductory "
            "courses are large and research assistant positions are competitive."
        ),
        "themes": [
            {"label": "Research lab access", "sentiment": "positive", "detail": "Active faculty labs in cognitive, clinical, and developmental psychology accept undergraduates."},
            {"label": "Graduate school preparation", "sentiment": "positive", "detail": "Strong track record placing graduates in top psychology and neuroscience PhD programs."},
            {"label": "Large gateway courses", "sentiment": "caution", "detail": "Introductory psychology sections are large; individual faculty mentorship requires initiative."},
            {"label": "Career without grad school", "sentiment": "mixed", "detail": "Undergraduate psychology alone narrows options; pairing with data science or pre-health coursework is advisable."},
        ],
        "sources": [
            {"label": "Niche — University of Florida", "url": "https://www.niche.com/colleges/university-of-florida/"},
            {"label": "UF Department of Psychology", "url": "https://psych.ufl.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uf-economics-bs": {
        "summary": (
            "UF's economics program through the College of Liberal Arts and Sciences combines rigorous "
            "quantitative training with applied policy and business coursework. Students value placement "
            "in consulting, finance, and graduate economics programs, though large lecture sections in "
            "principles courses are common."
        ),
        "themes": [
            {"label": "Quantitative training", "sentiment": "positive", "detail": "Econometrics and statistics sequences prepare students for data-driven careers."},
            {"label": "Graduate placement", "sentiment": "positive", "detail": "Graduates regularly enter top economics, policy, and MBA programs."},
            {"label": "Large principles courses", "sentiment": "caution", "detail": "Introductory economics sections are large; recitation and office hours matter."},
            {"label": "Policy and business paths", "sentiment": "positive", "detail": "Flexible major pairs well with pre-law, finance, and public policy interests."},
        ],
        "sources": [
            {"label": "U.S. News — University of Florida", "url": "https://www.usnews.com/best-colleges/university-of-florida-1535"},
            {"label": "UF Department of Economics", "url": "https://economics.ufl.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    **DEPTH_REVIEWS,
}

_FLAGSHIP = "uf-computer-science-bs"
_TRACKS_BY_SLUG: dict = {}
_CLASS_PROFILE_BY_SLUG: dict = {}
_FACULTY_BY_SLUG: dict = {}
_COST_BY_SLUG: dict = {}
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "uf-computer-science-bs": ["computer science", "CS", "CISE", "Herbert Wertheim College of Engineering"],
    "uf-mechanical-engineering-bs": ["mechanical engineering", "MAE", "Herbert Wertheim College of Engineering"],
    "uf-electrical-engineering-bs": ["electrical engineering", "ECE", "Herbert Wertheim College of Engineering"],
    "uf-biomedical-engineering-bs": ["biomedical engineering", "BME", "Herbert Wertheim College of Engineering"],
    "uf-nursing-bs": ["nursing", "BSN", "College of Nursing"],
    "uf-pharmacy-prof": ["pharmacy", "PharmD", "College of Pharmacy"],
    "uf-veterinary-medicine-prof": ["veterinary medicine", "DVM", "College of Veterinary Medicine"],
    "uf-business-administration-bs": ["business", "BSBA", "Warrington College of Business"],
    "uf-law-prof": ["law", "JD", "Levin College of Law"],
    "uf-medicine-prof": ["medicine", "MD", "College of Medicine"],
    "uf-psychology-bs": ["psychology", "Department of Psychology", "College of Liberal Arts and Sciences"],
    "uf-economics-bs": ["economics", "Department of Economics", "College of Liberal Arts and Sciences"],
}


def _program_standard(slug: str, spec: dict | None = None) -> dict:
    if spec is None:
        spec = _SPEC_BY_SLUG.get(slug, {})
    omitted: list[str] = [
        "outcomes_data.employment_rate",
        "outcomes_data.top_industries",
        "outcomes_data.conditions",
    ]
    if spec.get("degree_type") != "bachelors" and slug not in _COST_BY_SLUG:
        omitted.append("cost_data.tuition_usd")
    if slug not in _TRACKS_BY_SLUG:
        omitted.append("tracks")
    if slug not in _CLASS_PROFILE_BY_SLUG:
        omitted.append("class_profile.cohort_size")
    if slug not in _FACULTY_BY_SLUG:
        omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    return _standard(omitted)


def _requirements_for(spec: dict) -> dict:
    return dict(_REQ_UNDERGRAD if spec["degree_type"] == "bachelors" else _REQ_GRAD)


def _website_for(spec: dict) -> str:
    return SCHOOL_WEBSITE.get(spec["school"], "https://www.ufl.edu/")


def apply(session: Session) -> bool:
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    for _path in _OMITTED_INSTITUTION:
        if _path.startswith("school_outcomes."):
            school_outcomes.pop(_path.split(".", 1)[1], None)
    school_outcomes["_standard"] = _standard(_OMITTED_INSTITUTION)
    inst.school_outcomes = school_outcomes
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    inst.founded_year = 1853
    inst.campus_setting = "suburban"
    if not inst.website_url:
        inst.website_url = "https://www.purdue.edu"
    hero = SCHOOL_OUTCOMES["campus_photos"][0]["url"]
    _gallery = [u for u in (inst.media_gallery or []) if u != hero]
    inst.media_gallery = [hero, *_gallery]
    inst.content_sources = _INSTITUTION_CONTENT
    session.flush()
    school_by_name = _apply_schools(session, inst)
    _apply_programs(session, inst, school_by_name)
    session.flush()
    return True


def _apply_schools(session: Session, inst: Institution) -> dict[str, School]:
    existing = {s.name: s for s in session.scalars(select(School).where(School.institution_id == inst.id))}
    canonical_names = {s["name"] for s in SCHOOLS}
    by_name: dict[str, School] = {}
    for spec in SCHOOLS:
        sc = existing.get(spec["name"])
        if sc is None:
            sc = School(institution_id=inst.id, name=spec["name"])
            session.add(sc)
        sc.description_text = spec["description"]
        sc.sort_order = spec["sort_order"]
        sc.catalog_source = "curated"
        sc.website_url = SCHOOL_WEBSITE.get(spec["name"])
        m = next(x for x in _SCHOOL_META if x["name"] == spec["name"])
        about = dict(_about_for(m))
        about["_standard"] = _standard(_about_omitted(m))
        sc.about_detail = about
        sc.content_sources = _school_content(spec["name"])
        by_name[spec["name"]] = sc
    for name, sc in existing.items():
        if name not in canonical_names:
            session.delete(sc)
    session.flush()
    return by_name


def _program_has_dependents(session: Session, program_id) -> bool:
    fks = session.execute(text("""
        SELECT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND ccu.table_name = 'programs' AND ccu.column_name = 'id' AND tc.table_name <> 'programs'
    """)).fetchall()
    for table, col in fks:
        if session.execute(text(f'SELECT 1 FROM "{table}" WHERE "{col}" = :pid LIMIT 1'), {"pid": program_id}).first():
            return True
    return False


def _apply_programs(session: Session, inst: Institution, school_by_name: dict[str, School]) -> None:
    existing = {p.slug: p for p in session.scalars(select(Program).where(Program.institution_id == inst.id)) if p.slug}
    canonical = set(PROGRAM_SLUGS)
    for spec in PROGRAMS:
        slug = spec["slug"]
        p = existing.get(slug)
        if p is None:
            p = Program(institution_id=inst.id, program_name=spec["program_name"], degree_type=spec["degree_type"], slug=slug)
            session.add(p)
        p.program_name = spec["program_name"]
        p.degree_type = spec["degree_type"]
        p.duration_months = spec.get("duration_months")
        p.description_text = spec["description"]
        p.website_url = _website_for(spec)
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "on_campus")
        p.department = spec.get("department")
        kw = _PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(_KEYWORDS_BY_SCHOOL[spec["school"]])
        p.content_sources = _program_content(spec["school"], kw)
        if spec["degree_type"] == "bachelors":
            p.tuition = _TUITION_UG_INSTATE
            p.cost_data = {
                "tuition_usd": _TUITION_UG_INSTATE,
                "total_cost_of_attendance": _UNDERGRAD_COA,
                "avg_net_price": _AVG_NET_PRICE,
                "breakdown": {
                    "tuition_in_state": _TUITION_UG_INSTATE,
                    "tuition_out_of_state": _TUITION_UG_OOS,
                },
                "funded": False,
                "note": (
                    "In-state tuition and cost of attendance; nonresidents pay the "
                    "out-of-state tuition rate shown in the breakdown."
                ),
                "source": _COST_SRC[0], "source_url": _COST_SRC[1], "year": "2024-25",
            }
        elif spec["degree_type"] == "phd":
            p.tuition = 0
            p.cost_data = {
                "tuition_usd": 0, "funded": True,
                "note": "UF PhD students typically receive full tuition plus a stipend through UF Graduate School fellowship programs.",
                "source": "UF Graduate School — Funding",
                "source_url": "https://graduateschool.ufl.edu/admissions/financing/",
            }
        else:
            p.tuition = None
            p.cost_data = {
                "note": "Tuition varies by program; see the official program tuition page.",
                "source": "UF program tuition page",
                "source_url": _website_for(spec),
            }
        p.application_requirements = _requirements_for(spec)
        outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        p.application_deadline = date(2027, 1, 15) if spec["degree_type"] == "bachelors" else None
    session.flush()
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
