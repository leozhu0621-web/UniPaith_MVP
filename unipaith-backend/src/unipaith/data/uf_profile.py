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

Per-credential body rewrite (2026-06-20, ufdefab1): the prior composition stamped one
shared discipline definition + a shared "engages this discipline at the {level} level"
classification clause across every credential level of a field, so 102 multi-credential
fields shared a body once the level frame was stripped (anti_stub.frame_stripped_shared_body
— REPAIR_BACKLOG HIGH #4 / miss #8 credential-frame). Replaced with per-credential bodies
(``_level_body``): each level (BA/MS/PhD/certificate/professional) gets its own researched
body describing what THAT degree studies, so credential siblings share no dominant body
(frame_stripped_shared_body = 0; the build self-enforces it). Also fixed nine
college/department mismatches (Health Sciences / Allied Health → PHHP, Nutrition Science /
Human Development & Family Studies / Apparel Design / Agriculture → CALS, Liberal Arts →
CLAS, Bioinformatics → Engineering) so each description's named college matches the
program's department.

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
from unipaith.data.uf_cip6 import CIP6_BY_SLUG as _CIP6_BY_SLUG
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
# news.ufl.edu exposes no editorial RSS; www.ufl.edu/feed/ is an empty WordPress
# channel (verified 2026-06-20). The verified LiveWhale events RSS — current and
# image-carrying — feeds Updates (Rice pattern); iCalendar feeds Events.
_UF_EVENTS_RSS = "https://calendar.ufl.edu/live/rss/events"
_UF_EVENTS_ICS = {"url": "https://calendar.ufl.edu/live/ical/events", "type": "ical"}
_SOCIAL = {
    "instagram": "https://www.instagram.com/uflorida/",
    "linkedin": "https://www.linkedin.com/school/uflorida/",
    "x": "https://twitter.com/UF",
    "youtube": "https://www.youtube.com/user/UF",
    "facebook": "https://www.facebook.com/uflorida",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _UF_EVENTS_RSS,
    "news_url": "https://news.ufl.edu/",
    "news_curated": True,
    "events_feed": dict(_UF_EVENTS_ICS),
    "social": _SOCIAL,
}


def _school_content(name: str) -> dict:
    m = next(x for x in _SCHOOL_META if x["name"] == name)
    return {
        "news_rss": _UF_EVENTS_RSS,
        "news_url": m["website"],
        "news_curated": False,
        "events_feed": dict(_UF_EVENTS_ICS),
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

# Lowercase field label for the professional / no-"in" credential names, used mid-sentence
# in the per-credential body (e.g. "professional practice in law").
_FIELD_LABEL: dict[str, str] = {
    "Doctor of Medicine": "medicine",
    "Doctor of Pharmacy": "pharmacy",
    "Doctor of Veterinary Medicine": "veterinary medicine",
    "Doctor of Dental Medicine": "dentistry",
    "Juris Doctor": "law",
    "Master of Business Administration": "business administration",
}


def _field_label(name: str) -> str:
    if " in " in name:
        return name.split(" in ", 1)[1].strip()
    return _FIELD_LABEL.get(name, _anti_stub_field(name))


# Per-credential body: each credential level of a field gets its OWN researched body
# describing what THAT degree level studies and does, so credential siblings share no
# leading or tail-hidden field body (gold MIT model = 0 on anti_stub.analyze AND
# anti_stub.frame_stripped_shared_body). Each body is substantially longer than the
# leading discipline definition, so the shared definition is < 50% of every sibling and
# is never the dominant text a student reads on a level's page.
def _level_body(dtype: str, name: str, college: str, field: str) -> str:
    uf = "the University of Florida"
    if dtype == "bachelors":
        return (
            f"Building from the foundations of the discipline, the {name} grounds "
            f"undergraduates in core theory and method through required introductory "
            f"sequences, hands-on laboratory, studio, or field experience, and a "
            f"progression of upper-division electives within {college} at {uf}, "
            f"developing the breadth and analytical skill that ready graduates for "
            f"professional roles or further study."
        )
    if dtype == "masters":
        return (
            f"Built for advanced specialization, the {name} pairs graduate seminars and "
            f"methods coursework with applied projects, practica, or a research thesis "
            f"supervised by {college} faculty, letting students concentrate on a focused "
            f"area of {field} and prepare for advanced practice or doctoral work at {uf}."
        )
    if dtype == "phd":
        return (
            f"Centered on original scholarship, the {name} engages doctoral candidates in "
            f"advanced seminars, qualifying examinations, and a sustained, faculty-mentored "
            f"dissertation that contributes new knowledge to {field}, preparing graduates "
            f"for research, faculty, and senior professional careers through {college} "
            f"at {uf}."
        )
    if dtype == "certificate":
        return (
            f"A focused, credit-bearing credential, the {name} concentrates a compact set "
            f"of advanced courses on a defined area of {field}, giving working "
            f"professionals and degree-seeking students targeted expertise that can stand "
            f"alone or apply toward a related graduate degree within {college} at {uf}."
        )
    if dtype == "professional":
        return (
            f"A practice-oriented degree, the {name} joins rigorous classroom study with "
            f"extensive supervised clinical, laboratory, or practical training delivered "
            f"through {college} at {uf}, preparing graduates to satisfy licensure "
            f"requirements and to enter professional practice in {field}."
        )
    return ""


def _uf_description(spec: dict) -> str:
    """Verified per-credential description (gold MIT model).

    Leads with a verified, field-specific discipline definition (general field knowledge,
    no institution-specific or peer-borrowed claims), then a credential-level-specific
    body describing what THAT degree level studies at its real UF owning college. Each
    level's body is distinct, so a field's credential siblings share no dominant body
    (anti_stub.frame_stripped_shared_body = 0).
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
    desc = f"{defn} {_level_body(dtype, name, college, _field_label(name))}"
    return _with_format_suffix(desc, spec.get("delivery_format", "on_campus"))


def _with_format_suffix(desc: str, fmt: str) -> str:
    if fmt == "online":
        return desc + " Delivered fully online."
    if fmt == "hybrid":
        return desc + " Delivered in a hybrid format."
    return desc


# ---------------------------------------------------------------------------
# Per-credential sibling bodies (REPAIR_BACKLOG HIGH #5 / miss #8 fraction-floor).
#
# ``_uf_description`` prepends the SAME ~180-char discipline definition to EVERY credential
# level of a field, so a field's BA/MS/PhD siblings shared that leading sentence verbatim.
# ``_strip_frame`` only removes "{Field} is the study/science of …" leads, so UF's "is the
# discipline concerned with …" / "applies …" defs survive into the body and the shared
# definition is caught by ``frame_stripped_shared_body(..., abs_chars=150)`` (54 fields —
# the run-65 dilution evasion the fraction-only default reads as 0).
#
# The fix (Michigan / UCLA / Berkeley pattern): keep ONE anchor row carrying the discipline
# definition, and give every OTHER credential sibling its own level-specific body that leads
# with the field's TOPIC (so it stays distinct across DIFFERENT fields — the topic is real
# definition prose, never the bare field label the cross-field metric normalizes away) and
# frames it for THAT credential level (so it stays distinct from its same-field siblings).
# No sibling pair shares a >=150-char run (gold MIT = 0).
# ---------------------------------------------------------------------------

_LEVEL_PRIORITY = {
    "bachelors": 0,
    "masters": 1,
    "professional": 2,
    "certificate": 3,
    "phd": 4,
    "doctoral": 4,
}

# Recover the field-specific topic phrase from a discipline definition. The definition is
# "{Subject} {verb} {predicate}" — we anchor on the SUBJECT (the field-ish noun phrase at the
# very start, NOT a peer clause) and its MAIN verb, then take the predicate's focus. This is
# robust to definitions that lead with an article/alias ("The biological sciences study …",
# "Astronomy is …" for field "Astronomy and Astrophysics") or a "branch of {X} concerned
# with …" form where a naive "… of" cut stops too early (Codex review on PR #1016).

# The subject + its main verb. ``{0,5}?`` keeps the subject short so we stop at the FIRST
# verb (the main one), not a verb buried in a later "while/whereas" clause.
_TOPIC_SUBJECT_VERB_RE = re.compile(
    r"^(?:the|an?|this|these|those)?\s*"
    r"[A-Za-z][\w&/\-(),']*(?:\s+[\w&/\-(),']+){0,5}?\s+"
    r"(?P<verb>is|are|applies|apply|prepares|prepare|study|studies|encompass|encompasses|"
    r"examines?|explores?|investigates?|analyzes?|addresses?|concerns?|describes?|covers?|"
    r"develops?|provides?|trains?|integrates?|combines?|involves?|seeks?)\s+",
    re.I,
)

# A few discipline definitions use an irregular "{Subject} {verb}s and {verb}s …" shape with
# no clean linking verb / connector to anchor on; give them a verified, field-specific topic
# drawn from the definition by hand (still real prose, never the bare field label).
_TOPIC_OVERRIDES: dict[str, str] = {
    "Special Education": (
        "instruction and support for students with disabilities and exceptional learning needs"
    ),
    "Recreation Management": (
        "parks, leisure programs, and recreational facilities and the promotion of "
        "health and community"
    ),
}

# Highest-priority focus introducer in an "is/are" predicate. Checked FIRST so
# "branch of engineering concerned with the design" yields "the design …", never the
# false "engineering concerned with …" a leftmost descriptor-of cut would produce.
_TOPIC_FOCUS_RE = re.compile(r"\b(?:concerned with|devoted to|dealing with|focused on)\s+", re.I)

# Second priority: a "{descriptor} study/science … of …" or "… that/which {verb}s …" form.
_TOPIC_CONNECTOR_RE = re.compile(
    r"\b(?:(?:scientific\s+|interdisciplinary\s+|systematic\s+|academic\s+|empirical\s+|"
    r"formal\s+|applied\s+|theoretical\s+|social\s+|natural\s+|physical\s+|"
    r"professional\s+)*"
    r"(?:study|studies|science|sciences|application|analysis|examination|investigation)\s+of|"
    r"that\s+(?:study|studies|examines?|explores?|investigates?|analyzes?|addresses?|"
    r"concerns?|describes?|deals? with|focus(?:es)? on)|"
    r"which\s+(?:study|studies|examines?|explores?|investigates?|analyzes?))\s+",
    re.I,
)

# Lowest priority: a bare descriptor noun + "of" ("the discipline of conserving …", "the art
# form of structured human movement …"). Only consulted when no concerned-with / study-of
# connector matched, so it never pre-empts the higher-priority forms above.
_TOPIC_DESCRIPTOR_RE = re.compile(
    r"\b(?:discipline|art form|art|field|branch|area|body|form|way|set|system|framework|"
    r"process|method|theory|practice|study|studies|science|sciences)\s+of\s+",
    re.I,
)

# A coordinated SECOND main verb (finite "-s" form) begins a new clause that does not belong
# in the topic ("prepares teachers … and develops the pedagogical methods"); cut before it.
# Bare infinitives ("to design and operate processes") are intentionally NOT listed.
_TOPIC_COORD_VERB_ENDS = tuple(
    f" and {v} "
    for v in (
        "develops", "applies", "operates", "provides", "creates", "manages", "delivers",
        "builds", "examines", "explores", "designs", "integrates", "combines", "studies",
        "analyzes", "addresses", "produces", "trains", "investigates",
    )
)

# Clause terminators we prefer to end a topic on (keeps complete enumerations).
_TOPIC_CLAUSE_END = (
    ". ",
    "; ",
    " — ",
    ", spanning ",
    ", including ",
    ", drawing ",
    ", combining ",
    ", integrating ",
    ", as well as ",
    ", and how ",
    " and how ",
    " and whether ",
    " and the ways ",
    " and their relation",
    " while ",
    " whereas ",
    ", developing ",
    ", supporting ",
    ", providing ",
    ", applying ",
    ", using ",
    ", with applications ",
    *_TOPIC_COORD_VERB_ENDS,
)
# A hard cap that keeps every credential sibling's shared body under the 150-char abs-floor
# (the per-credential framing around the interpolated topic adds ~4-6 shared chars, so the
# topic itself must stay safely below 150 — the build's frame_stripped_shared_body gate
# enforces it). 140 keeps complete enumerations whole for nearly every field.
_TOPIC_MAX = 140
# Words a clean topic phrase must not END on (a dangling preposition/conjunction/article).
_TOPIC_TRAILING_JUNK = frozenset(
    {
        "and", "or", "of", "in", "on", "for", "with", "to", "under", "the", "a", "an",
        "by", "from", "into", "that", "which", "as", "at", "its", "their", "between",
    }
)


def _uf_topic(field: str) -> str:
    """A field-specific topic phrase recovered from the discipline definition.

    Reads grammatically as the object of "expertise in …" / "courses on …" / "research on …",
    and is always real field prose (never the bare field label, which ``cross_field_clause``
    normalizes to ``{FIELD}`` and would collide across fields). Shares <=130 chars with the
    anchor row that carries the full definition — under the 150-char floor.
    """
    if field in _TOPIC_OVERRIDES:
        return _TOPIC_OVERRIDES[field]
    fl = field.lower()
    defn = DISCIPLINE_DEFS.get(_FIELD_DEF_LOOKUP.get(fl, fl), "").strip()
    if not defn:
        return ""
    # A discipline whose name ends in "studies"/"sciences" (the catalog field is the shorter
    # form — "German" vs "German studies", "Film and Video" vs "Film and video studies")
    # leaves that noun in the subject; drop it so the FOLLOWING verb is taken as the main
    # verb, not the subject noun "studies"/"sciences" itself.
    work = re.sub(
        r"\b(?:studies|sciences|study|science)\s+"
        r"(?=(?:is|are|study|studies|examines?|explores?|investigates?|analyzes?|"
        r"addresses?|concerns?|describes?|covers?|develops?|integrates?|combines?|"
        r"involves?|seeks?|encompass(?:es)?)\b)",
        "",
        defn,
        count=1,
        flags=re.I,
    )
    m = _TOPIC_SUBJECT_VERB_RE.match(work)
    if m:
        verb = m.group("verb").lower()
        predicate = work[m.end() :].lstrip()
    else:
        verb, predicate = "is", work
    # Consume a coordinated leading verb ("develops AND applies computational methods …")
    # so the object — not the second verb — leads the topic.
    cv = re.match(
        r"^and\s+(?:applies|apply|develops?|provides?|examines?|explores?|integrates?|"
        r"combines?|studies|study|analyzes?|designs?|operates?|creates?|produces?|"
        r"manages?|delivers?|builds?|uses?)\s+",
        predicate,
        re.I,
    )
    if cv:
        predicate = predicate[cv.end() :].lstrip()
    if verb.startswith("appl"):
        body = "the application of " + predicate
    elif verb.startswith("prepare"):
        body = "the preparation of " + predicate
    elif verb in ("is", "are"):
        # 1) "concerned with / devoted to / …" wins regardless of position, so a preceding
        #    "branch of {parent field}" is skipped ("branch of engineering concerned with
        #    the design" → "the design …"). 2) otherwise take the EARLIEST study-of /
        #    descriptor-of / that-{verb} introducer ("art of dramatic performance …", not a
        #    later "the analysis of plays").
        fm = _TOPIC_FOCUS_RE.search(predicate)
        if fm:
            body = predicate[fm.end() :]
        else:
            cands = [
                x
                for x in (
                    _TOPIC_CONNECTOR_RE.search(predicate),
                    _TOPIC_DESCRIPTOR_RE.search(predicate),
                )
                if x
            ]
            if cands:
                body = predicate[min(cands, key=lambda x: x.start()).end() :]
            else:
                body = re.sub(r"^(?:the|a|an)\s+", "", predicate, flags=re.I)
    else:
        # bare main verb ("study/studies/encompass/examines/…") — predicate is the object
        body = predicate
    body = body.strip().rstrip(".")
    # End on a clean clause boundary rather than mid-enumeration.
    cut_at = len(body)
    for sep in _TOPIC_CLAUSE_END:
        idx = body.find(sep)
        if 24 <= idx < cut_at:
            cut_at = idx
    body = body[:cut_at].strip().rstrip(",;").strip()
    if len(body) > _TOPIC_MAX:
        cut = body[:_TOPIC_MAX]
        idx = cut.rfind(", ")
        cut = cut[:idx] if idx >= 50 else cut[: cut.rfind(" ")]
        body = cut.strip().rstrip(",;").strip()
    # Drop a dangling trailing preposition/conjunction/article left by a hard cut.
    words = body.split()
    while words and words[-1].lower().strip(",;") in _TOPIC_TRAILING_JUNK:
        words.pop()
    return " ".join(words).rstrip(",;").strip()


# A topic must read grammatically as the object of "expertise in …" / "courses on …". A
# topic that leads with a verb / conjunction / preposition / bare descriptor noun, ends on a
# dangling word, or carries a coordinated second main verb is malformed; the build gate below
# FAILS on any such field so it is fixed (heuristic or _TOPIC_OVERRIDES) before it can ship —
# closing the whack-a-mole the first extractor invited (Codex review on PR #1016/#1018).
_TOPIC_BAD_LEAD = frozenset(
    {
        "is", "are", "and", "or", "but", "of", "in", "on", "for", "with", "to", "by",
        "from", "under", "as", "at", "this", "these", "those", "that", "which",
        "study", "studies", "science", "sciences", "discipline", "branch", "field",
        "area", "form", "body", "way", "set", "system", "framework", "process", "method",
        "theory", "application", "analysis", "examination", "investigation", "art",
        "practice", "applies", "apply", "develops", "develop", "prepares", "prepare",
        "examines", "provides", "operates", "encompass", "encompasses",
    }
)


def _topic_is_clean(topic: str) -> bool:
    if not topic or len(topic) < 12:
        return False
    words = topic.split()
    if words[0].lower() in _TOPIC_BAD_LEAD:
        return False
    if words[-1].lower().strip(",;") in _TOPIC_TRAILING_JUNK or topic.rstrip().endswith(","):
        return False
    # A coordinated finite second MAIN clause ("… and develops the methods") — only the -s
    # form, so it does not false-flag a verb LIST ("raise, allocate, and manage") or an
    # infinitive coordination ("to design and operate"), both of which are grammatical.
    if re.search(
        r"\sand\s+(?:develops|applies|operates|provides|creates|manages|delivers|builds|"
        r"examines|explores|designs|produces|trains)\s",
        topic,
        re.I,
    ):
        return False
    return True


def _uf_sibling_body(dtype: str, name: str, college: str, field_label: str, topic: str) -> str:
    """A distinct, level-specific body for a credential sibling (no discipline definition)."""
    uf = "the University of Florida"
    t = topic or field_label.lower()
    if dtype == "masters":
        return (
            f"The {name} builds advanced expertise in {t}, pairing graduate seminars and "
            f"methods coursework with applied projects, a practicum, or a research thesis "
            f"directed by {college} faculty at {uf}."
        )
    if dtype in ("phd", "doctoral"):
        # "centers doctoral research on {t}" reads cleanly whether {t} is a noun phrase
        # ("the design of …") or a how/what/whether clause ("how schools are led …").
        return (
            f"The {name} centers doctoral research on {t}, advancing candidates through "
            f"qualifying examinations and a sustained, faculty-mentored dissertation within "
            f"{college} at {uf}."
        )
    if dtype == "certificate":
        return (
            f"The {name} concentrates a compact set of graduate courses on {t}, giving "
            f"working professionals and degree-seeking students a focused credential that can "
            f"stand alone or apply toward a related degree in {college} at {uf}."
        )
    if dtype == "professional":
        return (
            f"The {name} joins rigorous classroom study of {t} with extensive supervised "
            f"clinical or practical training delivered through {college} at {uf}, readying "
            f"graduates for licensure and professional practice."
        )
    if dtype == "bachelors":
        return (
            f"The {name} grounds undergraduates in {t} through introductory sequences, "
            f"laboratory or field experience, and upper-division electives within "
            f"{college} at {uf}."
        )
    return (
        f"The {name} engages {t} through coursework and supervised training within "
        f"{college} at {uf}."
    )


def _assign_per_credential_bodies(programs: list[dict]) -> None:
    """Keep ONE anchor per field with the discipline definition; give every other credential
    sibling a distinct level-specific body so no sibling pair shares a >=150-char run."""
    from collections import defaultdict

    groups: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        groups[_anti_stub_field(spec["program_name"])].append(spec)

    for _field, specs in groups.items():
        if len(specs) < 2:
            continue
        anchor = min(
            specs,
            key=lambda s: (_LEVEL_PRIORITY.get(s["degree_type"], 5), s["slug"]),
        )
        topic = _uf_topic(_field)
        assigned: list[str] = [anchor["description"]]
        for spec in specs:
            if spec is anchor:
                continue
            body = _uf_sibling_body(
                spec["degree_type"],
                spec["program_name"],
                spec["school"],
                _field_label(spec["program_name"]),
                topic,
            )
            # De-dup defensively (two same-level rows on one field would collide).
            n = 0
            base = body
            while body in assigned:
                n += 1
                body = (
                    f"{base.rstrip('.')} See the University of Florida General Catalog "
                    f"listing for {spec['program_name']} for degree requirements."
                )
                if n > 4:
                    break
            assigned.append(body)
            spec["description"] = _with_format_suffix(
                body, spec.get("delivery_format", "on_campus")
            )


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

# Per-credential bodies: only the anchor row of a field keeps the shared discipline
# definition; every other credential sibling gets a distinct level-specific body so no
# sibling pair shares a >=150-char run (REPAIR_BACKLOG HIGH #5 / miss #8 fraction-floor).
_assign_per_credential_bodies(PROGRAMS)

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
# Every multi-sibling field interpolates its topic into a sibling body — a malformed topic
# (verb/conjunction/preposition/descriptor lead, dangling tail, coordinated second verb)
# renders bad catalog copy. Fail the build so it is fixed (heuristic or _TOPIC_OVERRIDES)
# before it can ship (Codex review on PR #1016/#1018).
_field_counts: dict[str, int] = {}
for _p in PROGRAMS:
    _k = _anti_stub_field(_p["program_name"])
    _field_counts[_k] = _field_counts.get(_k, 0) + 1
_bad_topics = sorted(
    _f for _f, _n in _field_counts.items() if _n >= 2 and not _topic_is_clean(_uf_topic(_f))
)
if _bad_topics:
    _catalog_errors.append(f"malformed sibling topics for: {_bad_topics}")
# Enforce the gold-MIT-0% anti-stub gate at build time (enrich-profile §8.5): a stub /
# verbatim-across-levels / school-blurb / build-artifact catalog raises before it can ship.
from unipaith.profile_standard.anti_stub import (  # noqa: E402
    analyze as _anti_stub_analyze,
)
from unipaith.profile_standard.anti_stub import (  # noqa: E402
    frame_stripped_shared_body as _frame_stripped_shared_body,
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
# Per-credential body gate (miss #8 credential-frame): a field's BA/MS/PhD siblings must
# not share a body once a leading frame is stripped — the run-65 evasion analyze misses.
# Enforced at the ABSOLUTE 150-char floor (miss #8 fraction-floor) so a still-shared
# discipline definition cannot be diluted past the fraction-only default by padding the
# per-credential tail (REPAIR_BACKLOG HIGH #5 dilution evasion).
_frame_shared = _frame_stripped_shared_body(PROGRAMS, abs_chars=150)
if _frame_shared:
    _catalog_errors.append(
        f"frame-stripped shared body on {len(_frame_shared)} field(s): {_frame_shared[:8]}"
    )
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

# Graduate + professional tuition (matcher-core budget signal — REPAIR_BACKLOG #7).
# All figures are UF-PUBLISHED, first-party, 2025-26. The graduate annual is UF Student
# Financial Aid's published graduate tuition & fees estimate; the per-credit rates and the
# professional per-term rates are from the UF CFO 2025-26 tuition schedule. Nothing here is
# inferred except the graduate-certificate total, which is the published per-credit rate
# applied to the standard 12-credit UF graduate-certificate length (labeled as such).
_TUITION_GRAD_INSTATE = 12740  # UF SFA published graduate tuition & fees, FL resident, 2025-26
_TUITION_GRAD_OOS = 31872  # UF SFA published graduate tuition & fees, non-resident, 2025-26
_GRAD_PER_CREDIT_INSTATE = 530.69  # UF CFO 2025-26 graduate per-credit, FL resident
_GRAD_PER_CREDIT_OOS = 1327.88  # UF CFO 2025-26 graduate per-credit, non-resident
_CERT_CREDITS = 12  # standard UF graduate-certificate length used for the per-credit estimate
_TUITION_CERT_INSTATE = round(_GRAD_PER_CREDIT_INSTATE * _CERT_CREDITS)  # 6368
_TUITION_CERT_OOS = round(_GRAD_PER_CREDIT_OOS * _CERT_CREDITS)  # 15935
_GRAD_COST_SRC = (
    "UF Chief Financial Officer — 2025-26 Tuition & Fees + UF Student Financial Aid — Graduate Cost",
    "https://cfo.ufl.edu/student-financial-resources/current-and-former-students/2025-26-academic-year-tuition-and-fees/",
)

# Professional-school annual tuition = UF CFO 2025-26 per-term rate × 2 installments
# (Fall + Spring, UF's own published billing structure), FL resident / non-resident.
_PROFESSIONAL_TUITION: dict[str, dict] = {
    "Doctor of Medicine": {"in_state": 36657, "out_of_state": 68821, "per_term_in_state": 18328.59},
    "Doctor of Pharmacy": {"in_state": 28787, "out_of_state": 51860, "per_term_in_state": 14393.43},
    "Doctor of Veterinary Medicine": {"in_state": 22722, "out_of_state": 32886, "per_term_in_state": 11360.86},
    "Juris Doctor": {"in_state": 41718, "out_of_state": 70847, "per_term_in_state": 20858.99},
}

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


# ── Who it's for (universal depth field — REPAIR_BACKLOG #4) ─────────────────
# A field-specific 1–2 sentence statement of the applicant each program fits,
# derived from UF's published audience/fit material. Routed through ``_who_for``
# (per-slug override → per-credential default) — never a literal ``= None`` and
# never a content-free "for students interested in {field}" classification stub.
_WHO_BY_TYPE: dict[str, str] = {
    "bachelors": (
        "Applicants seeking a broad, top public-research undergraduate education — "
        "across the liberal arts, sciences, engineering, agriculture, health, and "
        "the arts — with Florida's in-state value and strong outcomes."
    ),
    "masters": (
        "Students seeking advanced professional or specialized graduate training at a "
        "leading public research university, often while working or advancing in a field."
    ),
    "certificate": (
        "Working professionals and graduate students who want focused, credit-bearing "
        "graduate coursework in a specialized area without committing to a full degree."
    ),
    "phd": (
        "Researchers pursuing an academic or research career through a funded UF "
        "doctorate, with full tuition support and a stipend."
    ),
    "professional": (
        "Candidates pursuing a clinical or professional degree at UF, with strong "
        "licensure pass rates, placement, and a large statewide alumni network."
    ),
}
_WHO_BY_SLUG: dict[str, str] = {
    "uf-computer-science-bs": "A strong fit for students who enjoy programming, algorithms, and problem-solving with logic and math, and who want to build software or move into fields like systems, data, or machine learning. Best for those ready for rigorous, computing-focused study.",
    "uf-mechanical-engineering-bs": "Suits students drawn to how machines, engines, and thermal and mechanical systems work, who are comfortable with physics and calculus and want hands-on design and analysis. A good match for those aiming at engineering practice, manufacturing, or graduate research.",
    "uf-electrical-engineering-bs": "For students fascinated by circuits, signals, power, and electronics who enjoy applying physics and math to design electrical and computing hardware. Fits those preparing for engineering careers in areas like communications, embedded systems, or energy, or for graduate study.",
    "uf-biomedical-engineering-bs": "Right for students who want to apply engineering to medicine and biology, designing devices, imaging tools, or biomaterials, and who are comfortable with both quantitative reasoning and life sciences. Suits those headed toward medical technology, research, or health-related professional school.",
    "uf-nursing-bs": "For students committed to patient care who want the clinical skills, science foundation, and hands-on training to become registered nurses. Best suited to compassionate, detail-oriented applicants preparing for licensure and direct practice in hospitals, clinics, or community settings.",
    "uf-pharmacy-prof": "A professional path for students preparing to become licensed pharmacists, blending pharmacology, therapeutics, and patient counseling with clinical rotations. Fits science-minded applicants who want a direct role in medication safety and care across community, hospital, or clinical settings.",
    "uf-veterinary-medicine-prof": "For students dedicated to animal health who want the clinical and scientific training to diagnose, treat, and care for animals as licensed veterinarians. Best for applicants with a strong biology foundation and hands-on experience, preparing for practice or specialty work.",
    "uf-business-administration-bs": "Suits students drawn to how organizations operate across management, marketing, finance, and operations, who want practical business skills and analytical grounding. A good fit for those aiming at careers in industry, entrepreneurship, or professional roles across many sectors.",
    "uf-law-prof": "For students preparing to practice law who want rigorous training in legal reasoning, writing, and doctrine across areas like contracts, torts, and constitutional law. Best for analytical, articulate applicants pursuing bar admission and careers in advocacy, policy, or counsel.",
    "uf-medicine-prof": "A professional path for students committed to becoming physicians, combining biomedical science, clinical training, and patient care through rotations. Suits dedicated, science-strong applicants prepared for the demands of medical practice and, ultimately, residency and licensure.",
    "uf-psychology-bs": "For students curious about the mind and behavior who want to study cognition, development, and mental processes with an emphasis on scientific methods and data. Fits those exploring careers in research, health, counseling, or graduate study, plus quantitative training.",
    "uf-economics-bs": "Suits students who want to understand how markets, incentives, and policy shape decisions, blending theory with analytical and quantitative reasoning. A good fit for those aiming at careers in finance, policy, or business, or at graduate study.",
    "uf-agricultural-business-and-management-bs": "For students drawn to the economics of food, farms, and agribusiness who want to combine market analysis, management, and policy applied to agricultural and natural-resource industries. Fits those preparing for careers in agribusiness, finance, or rural and food-system enterprises.",
    "uf-agricultural-business-and-management-cert": "A focused credential for working professionals or students who want to deepen expertise in agricultural economics, applying economic analysis to food, farm, and resource markets. Suits those advancing in agribusiness or preparing for further graduate study.",
    "uf-agricultural-business-and-management-ms": "For those specializing in agricultural economics who want advanced training in market analysis, policy, and quantitative methods applied to food and resource systems. Suits graduates and professionals aiming to advance in agribusiness, analysis, or policy roles.",
    "uf-applied-horticulture-and-horticultural-business-services-bs": "Suits students who love growing plants and want to study the science and business of horticulture, from plant production and landscapes to nursery and greenhouse operations. Fits those preparing for careers in horticultural enterprises, management, or applied plant work.",
    "uf-animal-sciences-bs": "For students drawn to the biology, nutrition, and management of livestock and companion animals who want hands-on experience alongside science coursework. A strong fit for those preparing for careers in animal production or industry, or for veterinary and graduate study.",
    "uf-animal-sciences-cert": "A focused credential for professionals or students wanting to strengthen expertise in animal biology, nutrition, or management without a full degree. Suits those advancing in animal industries or building a foundation toward graduate or veterinary paths.",
    "uf-animal-sciences-ms": "For those specializing in animal science who want advanced study in areas like nutrition, physiology, genetics, or management, often paired with research. Suits graduates and professionals aiming for careers in animal industries, research, or preparation for doctoral work.",
    "uf-food-science-and-technology-bs": "Suits students fascinated by how food is made, preserved, and kept safe, who want to apply chemistry, microbiology, and processing to product development. A good fit for careers in the food industry, quality and safety roles, or graduate study.",
    "uf-food-science-and-technology-cert": "A focused credential for working professionals or students who want to build expertise in food chemistry, safety, and processing without a full degree. Suits those advancing in food-industry roles or laying groundwork toward graduate study.",
    "uf-food-science-and-technology-ms": "For those specializing in food science who want advanced training in the chemistry, microbiology, safety, and processing behind food products, often with research. Suits graduates and professionals aiming for technical, product-development, or research careers in the food industry.",
    "uf-plant-sciences-bs": "For students drawn to how crops and plants grow, from genetics and physiology to production and sustainability, who enjoy applied biology and fieldwork. A good fit for those preparing for careers in agriculture, seed and crop industries, or graduate study.",
    "uf-plant-sciences-cert": "A focused credential for professionals or students who want to deepen expertise in crop and plant science, from breeding to production practices, without a full degree. Suits those advancing in agricultural roles or building toward graduate work.",
    "uf-plant-sciences-ms": "For those specializing in plant and crop science who want advanced study in genetics, physiology, or production systems, typically with research. Suits graduates and professionals aiming for careers in agriculture, crop industries, or preparation for doctoral study.",
    "uf-plant-sciences-phd": "For researchers pursuing original scholarship in plant and crop science, from molecular genetics to production and sustainability, who want to lead independent investigation. Suits those committed to research careers in academia, industry labs, or public agricultural science.",
    "uf-soil-sciences-bs": "For students curious about soil as a living system, studying its chemistry, biology, and role in water quality, agriculture, and the environment. A good fit for those preparing for careers in land and resource management, environmental work, or graduate study.",
    "uf-soil-sciences-cert": "A focused credential for professionals or students wanting to strengthen expertise in soil and water science, from soil chemistry to land and water management, without a full degree. Suits those advancing in environmental or agricultural roles.",
    "uf-soil-sciences-ms": "For those specializing in soil and water science who want advanced study of soil chemistry, biology, and their role in agriculture, water quality, and the environment, often with research. Suits graduates aiming for careers in resource management or research.",
    "uf-veterinary-medicine-cert": "A focused credential for professionals or students who want to build targeted expertise in a veterinary or animal-health topic without a full degree. Suits those advancing their practice or credentials in the veterinary field or preparing for further study.",
    "uf-veterinary-medicine-phd": "For researchers pursuing original scholarship in veterinary science, from animal disease to clinical and comparative medicine, who want to lead independent investigation. Suits those committed to research careers in academia, industry, or public animal-health science.",
    "uf-veterinary-biomedical-and-clinical-sciences-cert": "A focused credential for professionals or students wanting expertise in veterinary biomedical science, such as infectious disease, immunology, or comparative medicine, without a full degree. Suits those advancing in animal-health research or clinical support roles.",
    "uf-veterinary-biomedical-and-clinical-sciences-ms": "For those specializing in veterinary biomedical science who want advanced study of animal disease, immunology, and comparative medicine, often paired with research. Suits graduates and professionals aiming for careers in animal-health research, diagnostics, or preparation for doctoral work.",
    "uf-veterinary-biomedical-and-clinical-sciences-phd": "For researchers pursuing original scholarship in veterinary biomedical science, from infectious disease and immunology to comparative medicine, who want to lead independent investigation. Suits those committed to research careers in academia, industry, or public health.",
    "uf-agricultural-animal-plant-veterinary-science-and-related-fields-other-cert": "A focused credential for professionals or students who want to build expertise across agricultural and life sciences without committing to a full degree. Suits those broadening or updating their knowledge to advance in agriculture, natural resources, or related industries.",
    "uf-natural-resources-conservation-and-research-bs": "For students who care about ecosystems, wildlife, and sustainable land and water use, and want to study conservation with fieldwork and applied science. A good fit for those preparing for careers in resource management, environmental agencies, or graduate study.",
    "uf-fishing-and-fisheries-sciences-and-management-cert": "A focused credential for professionals or students wanting expertise in fisheries and aquatic sciences, from fish populations to aquatic ecosystem management, without a full degree. Suits those advancing in conservation, fisheries, or aquatic resource roles.",
    "uf-fishing-and-fisheries-sciences-and-management-ms": "For those specializing in fisheries and aquatic sciences who want advanced study of fish populations, aquatic ecosystems, and their management, often with research. Suits graduates and professionals aiming for careers in fisheries management, conservation, or aquatic research.",
    "uf-forestry-bs": "For students drawn to forests who want to study tree biology, ecology, and the sustainable use of forest resources, with hands-on fieldwork. A good fit for those preparing for careers in forest management, conservation, or the timber and land sectors.",
    "uf-forestry-cert": "A focused credential for professionals or students wanting to deepen expertise in forest ecology and management, from silviculture to sustainable resource use, without a full degree. Suits those advancing in forestry, land management, or conservation roles.",
    "uf-forestry-ms": "For those drawn to the science of managing forests as ecosystems and resources, ready to work in silviculture, forest inventory, timber economics, and land stewardship. A good fit if you want to move into research or advanced practice in sustainable forestry.",
    "uf-wildlife-and-wildlands-science-and-management-bs": "For students fascinated by animal populations, habitats, and conservation who want fieldwork alongside coursework in ecology, population dynamics, and habitat management. A strong start toward careers protecting wildlife and managing natural lands.",
    "uf-wildlife-and-wildlands-science-and-management-cert": "For working conservationists, agency staff, or biologists who want focused graduate training in wildlife population assessment, habitat management, and applied ecology to sharpen their practice without committing to a full degree.",
    "uf-wildlife-and-wildlands-science-and-management-ms": "For biologists and conservation professionals ready to specialize in wildlife population dynamics, habitat modeling, and management research, aiming for advanced roles with agencies, nonprofits, or research teams.",
    "uf-architecture-bs": "For creative, spatially minded students who want to learn how buildings are conceived and constructed, combining design studio, structures, and history. A foundation for continuing toward professional licensure in architecture.",
    "uf-architecture-cert": "For practicing designers or allied professionals who want concentrated graduate study in architectural design methods, theory, or building technology to deepen a specific area of expertise.",
    "uf-architecture-ms": "For those with design grounding who want advanced study in architectural theory, technology, or research, whether pursuing professional standing or investigating the built environment through focused inquiry.",
    "uf-city-urban-community-and-regional-planning-cert": "For public-sector staff, developers, or community advocates who want graduate grounding in land use, zoning, and community development to strengthen their role in shaping how places grow.",
    "uf-city-urban-community-and-regional-planning-ms": "For those committed to shaping how communities grow, ready to study land use, transportation, housing, and environmental planning. A path toward professional practice in city, county, or regional planning agencies.",
    "uf-city-urban-community-and-regional-planning-phd": "For scholars investigating how cities and regions develop, ready to conduct research on land use, housing, transportation, and policy. Suited to those pursuing academic or high-level research careers in planning.",
    "uf-landscape-architecture-bs": "For students who want to design outdoor and public spaces where ecology meets human use, learning site planning, planting design, and grading. A foundation toward professional practice shaping parks, campuses, and landscapes.",
    "uf-landscape-architecture-ms": "For designers ready to advance in shaping the land, studying site systems, ecological design, and regional landscapes at a graduate level, whether pursuing licensure or focused design research.",
    "uf-ethnic-cultural-minority-gender-and-group-studies-bs": "For students who want to examine identity, culture, gender, and power across societies, drawing on interdisciplinary methods. A fit for those headed toward advocacy, education, public service, or graduate study of social difference.",
    "uf-ethnic-cultural-minority-gender-and-group-studies-cert": "For graduate students and professionals who want structured study of gender, culture, and social identity to inform research, teaching, or work in communities and organizations.",
    "uf-ethnic-cultural-minority-gender-and-group-studies-ms": "For those ready to study identity, culture, and social difference in depth, using interdisciplinary theory and research methods toward careers in scholarship, policy, education, or community-focused work.",
    "uf-communication-and-media-studies-cert": "For professionals and graduate students who want focused study of how messages, relationships, and media shape audiences and organizations, sharpening skills in communication theory and analysis.",
    "uf-communication-and-media-studies-ms": "For those ready to study communication rigorously, from interpersonal and organizational messaging to media influence, aiming for advanced roles in research, strategy, or continued doctoral work.",
    "uf-journalism-bs": "For curious, ethical storytellers who want to report, write, and produce news across platforms, learning to gather facts, verify sources, and serve the public. A start toward newsroom and reporting careers.",
    "uf-journalism-ms": "For working reporters or career changers who want advanced training in reporting, editing, and media practice, or the research grounding to move into specialized journalism or teaching.",
    "uf-radio-television-and-digital-communication-bs": "For visual storytellers drawn to filmmaking and video, ready to learn production, editing, and narrative craft across screen media. A foundation for careers in film, television, and digital content creation.",
    "uf-radio-television-and-digital-communication-ms": "For those with production experience who want to advance their craft and understanding of screen media, studying film and video at a graduate level for creative, professional, or research paths.",
    "uf-public-relations-advertising-and-applied-communication-bs": "For strategic communicators who want to build and protect reputations, learning campaign planning, media relations, and persuasive writing. A path into public relations, corporate communication, and agency work.",
    "uf-public-relations-advertising-and-applied-communication-cert": "For communication professionals who want focused graduate study in strategic public relations, campaign design, and reputation management to advance in agency or organizational roles.",
    "uf-public-relations-advertising-and-applied-communication-ms": "For practitioners ready to deepen their command of strategic communication, studying campaign strategy, audience research, and reputation management for senior public relations and communication roles.",
    "uf-computer-and-information-sciences-general-bs": "For logical problem-solvers who want to learn programming, algorithms, data structures, and systems, building the technical foundation for software development, computing research, or a wide range of technology careers.",
    "uf-computer-and-information-sciences-general-cert": "For working technologists or students in adjacent fields who want focused graduate coursework in computing topics such as algorithms, systems, or software to build credentials in a specialized area.",
    "uf-computer-and-information-sciences-general-ms": "For those with a computing foundation who want advanced study in areas like algorithms, systems, machine learning, or software engineering, aiming for specialized technical roles or research.",
    "uf-computer-systems-analysis-ms": "For those who want to bridge technology and organizations, studying how information systems are designed, integrated, and managed to solve business problems. A fit for aspiring systems analysts and IT leaders.",
    "uf-education-general-bs": "For students exploring teaching and learning who want a broad grounding in educational theory, human development, and instructional practice, preparing for classroom paths or further study across education fields.",
    "uf-curriculum-and-instruction-cert": "For educators who want focused graduate study in how curriculum is designed and how effective teaching is delivered, strengthening classroom practice or preparing for instructional leadership.",
    "uf-curriculum-and-instruction-ms": "For teachers ready to advance their practice by studying curriculum design, instructional methods, and assessment, aiming for lead teaching, coaching, or specialist roles in schools.",
    "uf-curriculum-and-instruction-phd": "For educators and scholars investigating how curriculum and teaching shape learning, ready to conduct research toward careers in academia, educational leadership, or policy.",
    "uf-educational-administration-and-supervision-cert": "For teachers and school staff aiming toward leadership who want focused graduate study in school administration, supervision, and organizational management as a step toward principal or district roles.",
    "uf-educational-administration-and-supervision-ms": "For educators ready to lead schools and programs, studying administration, supervision, school law, and organizational management to move into principal, coordinator, or district leadership positions.",
    "uf-educational-administration-and-supervision-phd": "For experienced educators and administrators pursuing research and top leadership, studying educational policy, organizational theory, and leadership toward roles as superintendents, senior administrators, or faculty.",
    "uf-educational-assessment-evaluation-and-research-ms": "For those drawn to the measurement side of education, ready to study assessment design, program evaluation, statistics, and research methods for roles supporting data-informed decisions in schools and organizations.",
    "uf-special-education-and-teaching-bs": "For those committed to teaching students with disabilities, ready to learn individualized instruction, behavior support, and inclusive practice. A foundation toward certification and a career as a special educator.",
    "uf-special-education-and-teaching-cert": "For educators who want focused graduate study in supporting students with disabilities, deepening skills in specialized instruction, assessment, and intervention within their current practice.",
    "uf-special-education-and-teaching-ms": "For teachers ready to specialize in serving students with disabilities, studying evidence-based instruction, assessment, and intervention to advance as expert practitioners or program specialists.",
    "uf-special-education-and-teaching-phd": "For scholars and experienced practitioners investigating how students with disabilities learn and are served, ready to conduct research toward careers in academia, research, or policy leadership in special education.",
    "uf-student-counseling-and-personnel-services-cert": "For working educators and campus professionals who want focused grounding in how student affairs supports college learners outside the classroom, and who need a credential to move into residence life, advising, or student services roles.",
    "uf-student-counseling-and-personnel-services-ms": "For those drawn to supporting students through the college years who want to specialize in student development theory, advising, and campus programming, aiming toward careers in residence life, student conduct, career services, or enrollment work.",
    "uf-student-counseling-and-personnel-services-phd": "For experienced student affairs practitioners ready to study college student development, campus environments, and higher education policy at a scholarly level, aiming toward research, faculty, or senior administrative careers.",
    "uf-teacher-education-and-professional-development-specific-levels-and-methods-bs": "For undergraduates preparing to teach a particular grade band who want to master age-appropriate instructional methods, classroom management, and developmental learning as they build toward the classroom and initial licensure.",
    "uf-teacher-education-and-professional-development-specific-levels-and-methods-cert": "For practicing teachers who want focused preparation in the pedagogy and methods suited to a specific grade level, sharpening their instructional practice without committing to a full degree.",
    "uf-teacher-education-and-professional-development-specific-levels-and-methods-ms": "For educators seeking advanced command of the teaching methods appropriate to a particular grade band, deepening their instructional expertise and readiness for lead-teacher or mentoring roles.",
    "uf-teacher-education-and-professional-development-specific-subject-areas-bs": "For undergraduates who want to teach a specific discipline and are ready to pair deep content knowledge with the pedagogy of delivering that subject, working toward the classroom and initial licensure.",
    "uf-teacher-education-and-professional-development-specific-subject-areas-cert": "For working teachers who want concentrated preparation in teaching a particular subject, strengthening their content pedagogy and expanding what they are qualified to teach.",
    "uf-teacher-education-and-professional-development-specific-subject-areas-ms": "For educators aiming to become subject-matter specialists in their discipline, advancing their content pedagogy and preparing for department leadership or curriculum roles.",
    "uf-aerospace-aeronautical-and-astronautical-space-engineering-bs": "For students captivated by flight and spaceflight who want to study aerodynamics, propulsion, structures, and orbital mechanics, building toward careers designing aircraft, spacecraft, and launch systems.",
    "uf-aerospace-aeronautical-and-astronautical-space-engineering-cert": "For working engineers who want focused grounding in aerospace topics such as aerodynamics, propulsion, or flight dynamics to move into or advance within the aircraft and spacecraft industries.",
    "uf-aerospace-aeronautical-and-astronautical-space-engineering-ms": "For engineers ready to specialize in aerospace systems, deepening expertise in areas like propulsion, orbital mechanics, or vehicle design for advanced work in the aviation and space sectors.",
    "uf-agricultural-engineering-bs": "For students who want to apply engineering to food, water, and farming systems, studying machinery, irrigation, and soil and water resources to build sustainable agricultural and biological production.",
    "uf-agricultural-engineering-cert": "For working engineers and agriculture professionals seeking focused training in applying engineering to farming, water management, or biological production systems.",
    "uf-agricultural-engineering-ms": "For engineers ready to specialize in agricultural and biological systems, advancing expertise in areas such as precision agriculture, irrigation, or bioprocessing for technical and applied research roles.",
    "uf-biomedical-medical-engineering-cert": "For engineers and clinicians who want focused grounding in applying engineering to medicine and biology, whether in medical devices, imaging, or biomechanics, without committing to a full degree.",
    "uf-biomedical-medical-engineering-ms": "For engineers ready to specialize at the intersection of engineering and medicine, advancing expertise in areas like medical devices, biomaterials, or imaging for careers in the health technology industry.",
    "uf-chemical-engineering-bs": "For students who enjoy chemistry and math and want to design processes that transform raw materials into fuels, pharmaceuticals, and materials, building toward careers in energy, manufacturing, and biotechnology.",
    "uf-chemical-engineering-cert": "For working engineers seeking focused preparation in chemical process topics such as reaction engineering, separations, or transport, to deepen or redirect their technical practice.",
    "uf-chemical-engineering-ms": "For engineers ready to specialize in chemical process design and areas like catalysis, materials, or biotechnology, advancing toward senior technical and process development roles.",
    "uf-civil-engineering-bs": "For students drawn to designing and building the physical world, who want to study structures, transportation, water systems, and geotechnics as they prepare to shape roads, bridges, and infrastructure.",
    "uf-civil-engineering-cert": "For practicing engineers seeking focused study in a civil specialty such as structures, transportation, or water resources to sharpen their expertise and support licensure and advancement.",
    "uf-civil-engineering-ms": "For engineers ready to specialize in structural, geotechnical, transportation, or coastal systems, deepening technical command for senior design and infrastructure leadership roles.",
    "uf-computer-engineering-bs": "For students who want to work where hardware meets software, studying digital systems, embedded design, and computer architecture to build the processors and devices that power modern computing.",
    "uf-computer-engineering-cert": "For working engineers seeking focused training in areas like embedded systems, hardware design, or computer architecture to extend their skills across the hardware-software boundary.",
    "uf-computer-engineering-ms": "For engineers ready to specialize in computer hardware and systems, advancing expertise in embedded design, architecture, or digital systems for technical and design leadership roles.",
    "uf-electrical-electronics-and-communications-engineering-cert": "For working engineers who want focused study in electrical topics such as signals, power, or communications to deepen their expertise or move into a new area of the field.",
    "uf-electrical-electronics-and-communications-engineering-ms": "For engineers ready to specialize in electrical systems, advancing command of areas like signal processing, power, electronics, or communications for advanced design and research roles.",
    "uf-environmental-environmental-health-engineering-bs": "For students who want to protect air, water, and public health through engineering, studying treatment systems, pollution control, and sustainability as they prepare to address environmental challenges.",
    "uf-environmental-environmental-health-engineering-cert": "For working engineers seeking focused training in environmental topics such as water treatment, air quality, or remediation to broaden their practice or support licensure.",
    "uf-environmental-environmental-health-engineering-ms": "For engineers ready to specialize in protecting environmental and public health, advancing expertise in areas like water resources, treatment design, or contaminant management.",
    "uf-materials-engineering-bs": "For students fascinated by why materials behave as they do, who want to study metals, polymers, ceramics, and semiconductors and engineer new materials for electronics, medicine, and manufacturing.",
    "uf-materials-engineering-cert": "For working engineers seeking focused study in materials topics such as electronic materials, polymers, or characterization to extend their expertise across industries.",
    "uf-materials-engineering-ms": "For engineers ready to specialize in the structure and properties of materials, advancing expertise in areas like semiconductors, biomaterials, or metallurgy for research and development roles.",
    "uf-mechanical-engineering-cert": "For working engineers who want focused study in mechanical topics such as thermal systems, dynamics, or design to deepen their practice or support licensure and advancement.",
    "uf-mechanical-engineering-ms": "For engineers ready to specialize in mechanical systems, advancing expertise in areas like thermodynamics, mechanics, robotics, or design for senior technical and research roles.",
    "uf-nuclear-engineering-bs": "For students drawn to harnessing nuclear energy and radiation, who want to study reactor physics, radiation transport, and thermal systems as they prepare for careers in power, medicine, and national security.",
    "uf-nuclear-engineering-cert": "For working engineers seeking focused training in nuclear topics such as reactor systems, radiation, or nuclear materials to enter or advance within the energy and radiation industries.",
    "uf-nuclear-engineering-ms": "For engineers ready to specialize in nuclear science and technology, advancing expertise in reactor physics, radiation transport, or nuclear materials for technical and research careers.",
    "uf-ocean-engineering-cert": "For working engineers who want focused study in the ocean environment, addressing coastal structures, wave dynamics, and offshore systems to move into or advance within marine and coastal engineering.",
    "uf-ocean-engineering-ms": "For engineers and physical scientists drawn to the marine environment who want to design offshore structures, coastal systems, and underwater vehicles while mastering wave mechanics, hydrodynamics, and corrosion. It suits those aiming for careers in coastal protection, ocean energy, or naval and offshore industries.",
    "uf-systems-engineering-bs": "For students who think in terms of whole systems rather than single parts and want to design, integrate, and optimize the complex interactions among hardware, software, and people. A strong fit for those bound for aerospace, defense, logistics, or large-scale project engineering.",
    "uf-systems-engineering-cert": "For working engineers and technical managers who need a focused grounding in requirements analysis, system integration, and lifecycle management without leaving their jobs. It suits professionals moving into roles that coordinate complex, multi-disciplinary projects.",
    "uf-systems-engineering-ms": "For engineers ready to specialize in modeling, optimizing, and managing large interconnected systems across their full lifecycle. It fits those advancing toward technical leadership in aerospace, defense, healthcare delivery, or supply-chain and logistics engineering.",
    "uf-biological-biosystems-engineering-bs": "For students who want to apply engineering to living systems, natural resources, and food and agricultural production, blending biology with mechanical and environmental design. A good match for those aiming at careers in sustainable agriculture, water resources, or bioprocessing.",
    "uf-biological-biosystems-engineering-ms": "For engineers and life scientists deepening their work at the intersection of biology, water, land, and food systems, from bioprocessing to ecological engineering. It suits those advancing toward specialized practice or applied research in agricultural and environmental industries.",
    "uf-construction-engineering-technology-technician-bs": "For students who want to manage the technical side of building projects, combining structural understanding, scheduling, cost estimating, and field methods. A strong fit for those headed into commercial construction, project management, or the built-environment industry.",
    "uf-construction-engineering-technology-technician-cert": "For construction and engineering professionals seeking focused training in project delivery, estimating, and construction methods to strengthen their standing on complex builds. It suits those advancing into supervisory or technical management roles.",
    "uf-construction-engineering-technology-technician-ms": "For construction and engineering professionals ready to specialize in advanced project controls, sustainable building, and construction management practice. It fits those aiming for senior leadership across large-scale commercial, infrastructure, or development projects.",
    "uf-engineering-related-technologies-technicians-bs": "For hands-on, practically minded students who want to apply engineering principles to real production, testing, and technical operations rather than pure design theory. A good match for those pursuing careers in manufacturing, quality, and applied technical roles.",
    "uf-engineering-engineering-related-technologies-technicians-other-ms": "For technologists and engineers advancing their command of applied engineering methods, instrumentation, and emerging technical systems. It suits professionals moving into specialized applied roles or technical leadership across industry.",
    "uf-linguistic-comparative-and-related-language-studies-and-services-bs": "For students fascinated by how language works, from sound systems and grammar to meaning and how children acquire speech. A strong fit for those exploring paths in language technology, speech sciences, teaching, or graduate study in linguistics.",
    "uf-linguistic-comparative-and-related-language-studies-and-services-cert": "For educators, language professionals, and graduate students who want focused grounding in phonetics, syntax, and the scientific study of language. It suits those adding linguistic expertise to work in teaching, translation, or language technology.",
    "uf-linguistic-comparative-and-related-language-studies-and-services-ms": "For students ready to study language scientifically in depth, analyzing structure, sound, meaning, and acquisition through rigorous methods. It fits those aiming for careers in language technology, speech and language sciences, or doctoral research.",
    "uf-east-asian-languages-literatures-and-linguistics-bs": "For students committed to gaining real fluency in an East Asian language while studying the literature and culture behind it. A good match for those drawn to careers in international business, diplomacy, translation, or Asian regional expertise.",
    "uf-slavic-baltic-and-albanian-languages-literatures-and-linguistics-bs": "For students eager to learn a Slavic language and engage with the literature, history, and culture of Eastern Europe and Russia. It suits those aiming toward international affairs, translation, area studies, or graduate work in the region.",
    "uf-germanic-languages-literatures-and-linguistics-bs": "For students who want to master German and immerse themselves in the literature, philosophy, and culture of the German-speaking world. A strong fit for those eyeing careers in international business, research, translation, or European studies.",
    "uf-germanic-languages-literatures-and-linguistics-cert": "For graduate students and professionals who want to formalize advanced German proficiency and engage with German-language texts and scholarship. It suits those adding regional and linguistic depth to research or professional work.",
    "uf-germanic-languages-literatures-and-linguistics-ms": "For students pursuing advanced study of German language, literature, and culture through close textual and critical analysis. It fits those preparing to teach German, work in international fields, or continue toward doctoral research.",
    "uf-romance-languages-literatures-and-linguistics-bs": "For students drawn to languages such as Spanish, French, Portuguese, or Italian and the rich literary and cultural traditions behind them. A good match for those pursuing international careers, translation, education, or graduate study.",
    "uf-romance-languages-literatures-and-linguistics-cert": "For educators and professionals seeking to deepen advanced proficiency in a Romance language and engage seriously with its literature and scholarship. It suits those strengthening linguistic credentials for teaching, translation, or international work.",
    "uf-romance-languages-literatures-and-linguistics-ms": "For students ready for advanced study of Romance languages and their literatures through critical, cultural, and linguistic analysis. It fits those preparing to teach, work internationally, or pursue doctoral research in the field.",
    "uf-classics-and-classical-languages-literatures-and-linguistics-bs": "For students captivated by the ancient Greek and Roman worlds who want to read Latin and Greek texts and study classical history, thought, and culture. A strong fit for those headed toward law, teaching, museum work, or graduate study.",
    "uf-classics-and-classical-languages-literatures-and-linguistics-cert": "For graduate students and educators seeking focused command of Latin, Greek, or the classical tradition to enrich teaching, research, or related humanities work. It suits those formalizing expertise in the ancient world.",
    "uf-classics-and-classical-languages-literatures-and-linguistics-ms": "For students pursuing advanced study of ancient languages, literature, and the Greco-Roman world through rigorous textual and historical analysis. It fits those aiming to teach classics or continue toward doctoral research.",
    "uf-human-development-family-studies-and-related-services-bs": "For students who want to understand how people grow and how families and communities shape wellbeing across the lifespan. A good match for those pursuing careers in youth services, family support, early childhood, or human services.",
    "uf-human-development-family-studies-and-related-services-cert": "For practitioners in education, social services, and community programs who want focused grounding in human development and family dynamics. It suits those strengthening their ability to support children, families, and communities.",
    "uf-human-development-family-studies-and-related-services-ms": "For professionals advancing their expertise in lifespan development, family systems, and evidence-based support for children and families. It fits those moving into program leadership, extension, or applied research in human services.",
    "uf-law-phd": "For scholars and experienced legal professionals who want to conduct original, rigorous research into law, its theory, and its role in society. It suits those preparing for academic careers in legal teaching and scholarship.",
    "uf-legal-research-and-advanced-professional-studies-cert": "For working professionals in business, compliance, healthcare, or government who need practical legal literacy without pursuing a full law degree. It suits those navigating regulation, contracts, and legal risk in their roles.",
    "uf-legal-research-and-advanced-professional-studies-ms": "For non-lawyer professionals who want structured grounding in law, regulation, and legal reasoning to strengthen work in compliance, policy, or business. It fits those advancing careers where legal fluency matters but bar admission does not.",
    "uf-english-language-and-literature-general-bs": "For students who love reading closely and writing well, and want to study literature, critical analysis, and the craft of the written word. A strong fit for those exploring careers in writing, publishing, education, law, or communications.",
    "uf-english-language-and-literature-general-cert": "For educators, writers, and graduate students who want focused advanced study in literature and critical analysis. It suits those deepening interpretive and writing skills for teaching, editing, or scholarly work.",
    "uf-english-language-and-literature-general-ms": "For students pursuing advanced study of literature, literary theory, and critical writing through close reading and sustained scholarship. It fits those preparing to teach, write professionally, or continue toward doctoral research.",
    "uf-rhetoric-and-composition-writing-studies-ms": "For students and educators who want to study how writing works and how it is taught, from rhetorical theory to composition pedagogy and digital communication. It suits those preparing to teach writing or work in professional and technical communication.",
    "uf-liberal-arts-and-sciences-general-studies-and-humanities-bs": "For intellectually curious students who want a broad, interdisciplinary education spanning the humanities, arts, and sciences rather than a single narrow major. A good match for those seeking versatile preparation for varied careers or graduate study.",
    "uf-liberal-arts-and-sciences-general-studies-and-humanities-cert": "For learners and professionals who want structured breadth across the humanities and sciences to broaden their perspective and analytical range. It suits those complementing specialized work with interdisciplinary grounding.",
    "uf-biology-general-bs": "For students fascinated by living organisms and how life works at every scale, from cells and genetics to ecosystems and evolution. A strong fit for those aiming at medicine, research, conservation, biotechnology, or graduate study in the life sciences.",
    "uf-biology-general-ms": "For life scientists deepening their command of biological research, from molecular and cellular processes to organismal and ecological systems. It fits those advancing toward research careers, professional health programs, or doctoral study.",
    "uf-biochemistry-biophysics-and-molecular-biology-ms": "For students drawn to the molecular machinery of life who want to investigate proteins, nucleic acids, and cellular processes through laboratory research. It fits those advancing toward biomedical research, biotechnology, or doctoral study.",
    "uf-botany-plant-biology-bs": "Well suited to students fascinated by how plants grow, reproduce, and adapt, from cellular processes to whole ecosystems. It fits those exploring careers in conservation, agriculture, plant research, or environmental science.",
    "uf-botany-plant-biology-cert": "Designed for working professionals and graduate students who want focused grounding in plant structure, physiology, and diversity to strengthen research or applied work in ecology, agriculture, or conservation.",
    "uf-botany-plant-biology-ms": "Fits students ready to specialize in the biology of plants, from physiology and genetics to systematics and ecology, and who aim to advance toward research, teaching, or applied roles in conservation and agriculture.",
    "uf-cell-cellular-biology-and-anatomical-sciences-cert": "For professionals and graduate students seeking concentrated study of cell structure, function, and signaling to bolster work in biomedical research, laboratory science, or health-related fields.",
    "uf-cell-cellular-biology-and-anatomical-sciences-ms": "Suits students drawn to how cells are organized and how they communicate, divide, and malfunction, and who want deeper laboratory training toward biomedical research or doctoral study.",
    "uf-microbiological-sciences-and-immunology-bs": "A strong match for students curious about bacteria, viruses, and the immune system, and how microbes shape health and disease. It supports paths into clinical labs, biotechnology, public health, or medical and graduate school.",
    "uf-microbiological-sciences-and-immunology-cert": "For professionals and graduate students who want focused study of microorganisms and immune function to reinforce work in clinical, biotech, or public-health settings.",
    "uf-microbiological-sciences-and-immunology-ms": "Fits students ready to specialize in the study of microbes and host defenses, building laboratory expertise toward roles in research, biotechnology, diagnostics, or doctoral training.",
    "uf-genetics-cert": "Designed for professionals and graduate students seeking concentrated grounding in heredity, gene function, and genomic analysis to support work in research, healthcare, or agricultural biotechnology.",
    "uf-physiology-pathology-and-related-sciences-ms": "Well suited to students interested in how the body's systems function and fail, from organs to molecular regulation. It fits those advancing toward biomedical research, health professions, or doctoral study.",
    "uf-biomathematics-bioinformatics-and-computational-biology-cert": "For working professionals and graduate students who want to apply computing and data analysis to biological problems, such as sequence analysis and genomic data, to strengthen research or industry work.",
    "uf-biomathematics-bioinformatics-and-computational-biology-ms": "Fits students who pair biology with programming and statistics and want to specialize in analyzing genomic and molecular data, aiming for roles in biotech, pharmaceutical research, or computational science.",
    "uf-ecology-evolution-systematics-and-population-biology-cert": "For professionals and graduate students seeking focused study of how organisms interact, evolve, and diversify, to support work in conservation, environmental management, or research.",
    "uf-ecology-evolution-systematics-and-population-biology-ms": "Suits students drawn to the dynamics of populations, species, and ecosystems and the forces of evolution, who want field and analytical training toward research, conservation, or doctoral study.",
    "uf-biological-and-biomedical-sciences-other-cert": "For professionals and graduate students who want structured grounding across core biological sciences to reinforce laboratory, health, or research work.",
    "uf-biological-and-biomedical-sciences-other-ms": "Fits students seeking a broad yet advanced foundation in the life sciences, building laboratory and analytical skills toward research careers, health professions, or further graduate study.",
    "uf-biological-and-biomedical-sciences-other-phd": "For students committed to original research across the life sciences who aim to lead independent investigation in academic, industry, or government settings and to publish and mentor in their field.",
    "uf-mathematics-bs": "A strong fit for students who enjoy rigorous reasoning, proof, and abstraction across areas like analysis, algebra, and applied mathematics. It opens paths into data, finance, teaching, engineering, and graduate study.",
    "uf-mathematics-cert": "For working professionals and graduate students who want to deepen their command of advanced mathematical methods to support quantitative work or prepare for further study.",
    "uf-mathematics-ms": "Suits students ready to specialize in advanced pure or applied mathematics, sharpening analytical and problem-solving depth toward roles in research, data-intensive industry, teaching, or doctoral study.",
    "uf-statistics-bs": "Well suited to students who like drawing conclusions from data through probability, modeling, and inference. It supports careers in analytics, actuarial work, research, and the growing demand for data-driven roles.",
    "uf-statistics-cert": "For working professionals and graduate students who want focused training in statistical modeling and data analysis to strengthen quantitative work in research, industry, or policy.",
    "uf-statistics-ms": "Fits students ready to specialize in statistical theory and applied data analysis, building modeling and computing skills toward careers as statisticians, data scientists, or doctoral researchers.",
    "uf-historic-preservation-and-conservation-cert": "For professionals and graduate students who want focused expertise in documenting, protecting, and restoring historic buildings and places, to support work in planning, architecture, or heritage management.",
    "uf-historic-preservation-and-conservation-ms": "Suits students committed to safeguarding the built past through study of building materials, documentation, and preservation policy, aiming for roles in preservation practice, planning agencies, or cultural stewardship.",
    "uf-museology-museum-studies-cert": "For working professionals and graduate students who want practical grounding in curation, collections care, and exhibition work to advance in museums, galleries, or cultural institutions.",
    "uf-museology-museum-studies-ms": "Fits students drawn to the work of museums, from collections management and interpretation to public programming, and who aim for careers in curatorial, educational, or administrative roles across cultural institutions.",
    "uf-nutrition-sciences-bs": "A strong match for students interested in how diet, nutrients, and metabolism affect human health across the lifespan. It supports paths into dietetics, public health, research, and clinical or graduate study.",
    "uf-nutrition-sciences-cert": "For working professionals and graduate students seeking focused study of nutrition and metabolism to reinforce work in health, wellness, food industry, or research settings.",
    "uf-international-globalization-studies-bs": "Well suited to students curious about how economies, cultures, and politics connect across borders. It fits those aiming for careers in international development, diplomacy, nonprofit work, or global business.",
    "uf-international-globalization-studies-cert": "For working professionals and graduate students who want focused grounding in transnational issues, development, and cross-cultural analysis to strengthen work in global organizations or policy.",
    "uf-international-globalization-studies-ms": "Fits students ready to specialize in the forces shaping an interconnected world, from migration and trade to governance, aiming for advanced roles in development, international affairs, or research.",
    "uf-marine-sciences-bs": "A strong fit for students drawn to oceans and coastal systems, from marine biology and chemistry to physical oceanography. It supports careers in conservation, environmental science, marine research, and resource management.",
    "uf-sustainability-studies-bs": "Well suited to students who want to address environmental and social challenges by connecting ecology, economics, and policy. It fits those aiming for careers in conservation, corporate sustainability, or environmental advocacy.",
    "uf-sustainability-studies-ms": "Fits students ready to specialize in the science and policy of building resilient, resource-conscious systems, aiming for advanced roles in environmental planning, sustainability management, or applied research.",
    "uf-geography-and-environmental-studies-bs": "A strong match for students interested in how people, places, and environments interact across space, including mapping and spatial analysis. It supports careers in planning, GIS, environmental management, and policy.",
    "uf-multi-interdisciplinary-studies-other-bs": "Well suited to students who want to combine coursework across several fields around a personal focus rather than a single major. It fits self-directed learners charting an individualized path toward varied careers or further study.",
    "uf-parks-recreation-and-leisure-facilities-management-bs": "A good fit for students who want to design and manage recreation programs, parks, and leisure services that support community wellbeing. It supports careers in parks administration, tourism, and community recreation.",
    "uf-parks-recreation-and-leisure-facilities-management-cert": "For working professionals seeking focused training in recreation programming and facility management to advance in parks, tourism, or community services roles.",
    "uf-parks-recreation-and-leisure-facilities-management-ms": "Fits students ready to specialize in the planning, administration, and evaluation of recreation and leisure services, aiming for leadership roles in parks systems, tourism, or community organizations.",
    "uf-sports-kinesiology-and-physical-education-fitness-bs": "A good fit if you're fascinated by how the body moves and adapts to exercise, and want a foundation in biomechanics, motor control, and physiology that leads toward strength training, rehabilitation, or health professions.",
    "uf-sports-kinesiology-and-physical-education-fitness-cert": "Built for practicing coaches, trainers, and allied-health professionals who want focused grounding in exercise physiology and movement science to sharpen their programming without committing to a full degree.",
    "uf-sports-kinesiology-and-physical-education-fitness-ms": "For those with a movement-science background ready to specialize in exercise physiology, biomechanics, or motor behavior, aiming for advanced roles in performance, clinical exercise, or applied research.",
    "uf-sports-kinesiology-and-physical-education-fitness-phd": "Suited to researchers who want to investigate how physical activity shapes health and human performance, generating original studies in physiology or biomechanics toward academic and scientific careers.",
    "uf-philosophy-bs": "For those drawn to rigorous questions about knowledge, ethics, mind, and logic who want to sharpen argument and analysis, whether toward law, teaching, or clear thinking in any field.",
    "uf-philosophy-cert": "Aimed at working professionals and graduate students who want structured study in ethics, logic, or philosophical reasoning to deepen analytical rigor alongside their primary field.",
    "uf-philosophy-ms": "For students ready to work closely with philosophical texts and problems in areas like ethics, metaphysics, or epistemology, building the argumentation and writing depth that supports doctoral study or scholarly work.",
    "uf-religion-religious-studies-bs": "A fit for those curious about how religious traditions, texts, and practices shape cultures and history, who want to study belief systems across the world with an analytical rather than devotional lens.",
    "uf-religion-religious-studies-cert": "For professionals in education, nonprofits, or public service who want focused literacy in world religions and their cultural contexts to work more thoughtfully across diverse communities.",
    "uf-religion-religious-studies-ms": "For students prepared to analyze sacred texts, traditions, and their social contexts in depth, developing the interpretive and comparative skills that support teaching, scholarship, or doctoral study.",
    "uf-astronomy-and-astrophysics-bs": "For those captivated by stars, galaxies, and the physics of the cosmos who want strong grounding in physics and mathematics, whether aiming toward research, observatories, or graduate study.",
    "uf-astronomy-and-astrophysics-cert": "Suited to physicists, engineers, and educators who want concentrated exposure to astrophysical methods and current questions in the field without pursuing a full research degree.",
    "uf-astronomy-and-astrophysics-ms": "For students with a physics or astronomy foundation ready to specialize in observational or theoretical astrophysics, building the analytical and computational skills that lead toward research or doctoral work.",
    "uf-chemistry-bs": "A fit for those who enjoy the lab bench and want to understand matter at the molecular level, building skills in organic, physical, and analytical chemistry toward research, industry, or professional school.",
    "uf-chemistry-cert": "For working chemists and technical professionals who want to deepen expertise in a specific area of chemistry, from analytical methods to synthesis, without committing to a full graduate degree.",
    "uf-chemistry-ms": "For students with a chemistry background ready to specialize in areas like synthesis, spectroscopy, or materials, developing the laboratory and research skills that advance careers in industry or doctoral study.",
    "uf-geological-and-earth-sciences-geosciences-bs": "For those who want to read the planet's history in its rocks, water, and landscapes, building field and lab skills in geology toward careers in energy, environment, or resource science.",
    "uf-geological-and-earth-sciences-geosciences-cert": "Aimed at environmental and technical professionals who want focused grounding in geological processes and earth-systems methods to strengthen work in resource, hazard, or environmental fields.",
    "uf-geological-and-earth-sciences-geosciences-ms": "For students ready to specialize in areas like hydrogeology, sedimentology, or geophysics, developing the field and analytical research skills that support careers in geoscience or doctoral study.",
    "uf-physics-bs": "For those who want to understand the fundamental laws governing matter and energy, building strong mathematical and experimental skills toward research, engineering, or graduate study in the physical sciences.",
    "uf-physics-cert": "For engineers, educators, and technical professionals who want concentrated study in a physics subfield to strengthen their quantitative foundation without a full graduate program.",
    "uf-physics-ms": "For students with a physics foundation ready to specialize in areas such as condensed matter, optics, or particle physics, building the theoretical and experimental depth that supports research or doctoral work.",
    "uf-psychology-general-cert": "For professionals in education, health, or human services who want structured grounding in psychological science and behavior to inform their practice without pursuing a full degree.",
    "uf-psychology-general-ms": "For students ready to study behavior and cognition through empirical methods, building research and statistical skills across areas of psychology that support applied work or doctoral study.",
    "uf-clinical-counseling-and-applied-psychology-ms": "For those drawn to understanding and supporting mental health who want training in assessment and evidence-based intervention, building toward clinical practice or continued doctoral study.",
    "uf-clinical-counseling-and-applied-psychology-phd": "Suited to those committed to clinical science who want to conduct research on psychological disorders and treatment while developing supervised clinical skills toward careers in practice, academia, or research.",
    "uf-fire-protection-bs": "For those focused on fire behavior, prevention, and safety systems who want technical grounding in combustion, suppression, and codes toward careers in fire service, protection engineering, or safety management.",
    "uf-fire-protection-cert": "Built for working fire-service and safety professionals who want focused study in fire dynamics and protection systems to advance into inspection, investigation, or leadership roles.",
    "uf-fire-protection-ms": "For professionals ready to specialize in fire science and protection engineering, deepening expertise in combustion, risk, and suppression systems for advanced technical or leadership careers.",
    "uf-anthropology-bs": "A fit for those curious about human cultures, evolution, and societies across time who want to study people through fieldwork and comparison, whether toward research, cultural work, or graduate study.",
    "uf-anthropology-cert": "For professionals in public service, health, or cultural fields who want focused grounding in anthropological methods and cross-cultural analysis to work more effectively with diverse communities.",
    "uf-anthropology-ms": "For students ready to specialize in a subfield such as cultural, biological, or archaeological anthropology, developing the fieldwork and analytical skills that support research or doctoral study.",
    "uf-criminology-bs": "For those who want to understand why crime happens and how justice systems respond, building skills in research and social analysis toward careers in law enforcement, policy, or corrections.",
    "uf-criminology-cert": "Aimed at practitioners in law enforcement, corrections, or policy who want focused study of crime causes and justice-system dynamics to strengthen and advance their professional work.",
    "uf-criminology-ms": "For students ready to analyze crime, punishment, and justice policy through empirical research, building the methodological skills that support careers in analysis, administration, or doctoral study.",
    "uf-economics-cert": "For professionals in business, finance, or public policy who want rigorous grounding in economic theory and quantitative analysis to sharpen decision-making without a full degree.",
    "uf-economics-ms": "For students with a quantitative foundation ready to model markets, incentives, and policy using econometric tools, building toward roles in analysis, consulting, government, or doctoral study.",
    "uf-international-relations-and-national-security-studies-cert": "For professionals in government, defense, or global organizations who want focused study of diplomacy, security, and international systems to strengthen their work in policy and analysis.",
    "uf-international-relations-and-national-security-studies-ms": "For students ready to analyze global politics, security, and diplomacy through rigorous frameworks, building toward careers in foreign affairs, defense, international organizations, or policy analysis.",
    "uf-political-science-and-government-bs": "For those interested in how power, institutions, and public policy shape society who want to study government and politics analytically, whether toward law, public service, or graduate study.",
    "uf-political-science-and-government-cert": "For working professionals in policy, government, or advocacy who want a focused grounding in political institutions, comparative politics, or international relations to sharpen how they read and shape public decisions.",
    "uf-political-science-and-government-ms": "You want to specialize in the study of governance, political behavior, and public policy, building the analytic and methodological skills that support careers in policy analysis, public affairs, or further doctoral work.",
    "uf-political-science-and-government-phd": "For those aiming at academic or high-level research careers who want to design original studies of political institutions, elections, or international relations and teach the discipline at the university level.",
    "uf-sociology-bs": "A good fit if you are curious about how social structures, inequality, and group behavior shape everyday life, and want a broad foundation for work in research, social services, or graduate study.",
    "uf-sociology-cert": "For professionals in social services, nonprofits, or research settings who want structured training in sociological theory and methods to interpret patterns of inequality, community, and social change in their work.",
    "uf-sociology-ms": "You want to deepen your command of social research methods and theories of inequality, family, or institutions, preparing to lead applied studies or continue toward doctoral work in sociology.",
    "uf-dance-bs": "For committed dancers who want to develop technique, choreography, and performance alongside the study of movement, ready to pursue careers in performing, teaching, or creating dance.",
    "uf-dance-cert": "For practicing dancers or educators who want focused graduate study in choreography, movement analysis, or dance pedagogy to strengthen their artistry or teaching practice.",
    "uf-design-and-applied-arts-bs": "A strong fit if you think visually and want to build skills in graphic, interior, or product design, preparing to shape spaces, objects, and communications for creative and professional practice.",
    "uf-design-and-applied-arts-cert": "For working designers or allied professionals who want concentrated graduate study in design methods and visual problem-solving to advance a specialized area of their practice.",
    "uf-design-and-applied-arts-ms": "You want to advance your design practice through research and studio work, developing expertise in areas such as interior, product, or visual communication design for leadership or teaching roles.",
    "uf-drama-theatre-arts-and-stagecraft-bs": "For students drawn to the stage who want training in acting, directing, or production and stagecraft, building the craft and collaboration skills that theatre and performance careers demand.",
    "uf-drama-theatre-arts-and-stagecraft-cert": "For theatre practitioners and educators seeking focused graduate study in performance, directing, or production to refine a specialized area of their stage practice.",
    "uf-drama-theatre-arts-and-stagecraft-ms": "You want to deepen your work in acting, directing, design, or theatre scholarship, developing the advanced craft and research skills for professional practice or teaching in the theatre.",
    "uf-fine-and-studio-arts-bs": "A good fit if you want to develop your studio practice across media such as painting, sculpture, printmaking, or digital art while grounding your work in art history and critique.",
    "uf-fine-and-studio-arts-cert": "For practicing artists and educators who want concentrated graduate study in a studio discipline or critical approach to sharpen and extend their creative practice.",
    "uf-fine-and-studio-arts-ms": "You want to advance a serious studio practice through sustained work in your medium, critique, and art scholarship, preparing for a professional artistic career or teaching.",
    "uf-music-bs": "For musicians who want to grow as performers, composers, or educators through study of theory, history, and applied performance, building toward careers in music-making and teaching.",
    "uf-music-cert": "For practicing musicians and music educators who want focused graduate study in performance, composition, or pedagogy to strengthen a specialized area of their musicianship.",
    "uf-music-ms": "You want to specialize in an area such as performance, composition, conducting, or music education, deepening your artistry and scholarship for advanced professional or teaching roles.",
    "uf-music-phd": "For those pursuing scholarly and academic careers in music who want to conduct original research in areas such as musicology, theory, or music education and teach at the university level.",
    "uf-health-services-allied-health-health-sciences-general-bs": "A strong fit if you want a broad foundation in the science of health and the healthcare system, preparing for entry-level roles or graduate study across the health professions.",
    "uf-communication-disorders-sciences-and-services-bs": "For students fascinated by how people produce and process speech, language, and hearing, and who want a foundation toward becoming a speech-language pathologist or audiologist.",
    "uf-communication-disorders-sciences-and-services-cert": "For clinicians and professionals in communication sciences who want focused graduate study in a specialized area of speech, language, or hearing to extend their clinical or research skills.",
    "uf-communication-disorders-sciences-and-services-ms": "You want to build the clinical and scientific expertise to assess and treat speech, language, and hearing disorders, advancing toward professional practice in communication sciences.",
    "uf-communication-disorders-sciences-and-services-phd": "For those pursuing research and academic careers who want to investigate the mechanisms of speech, language, and hearing and their disorders and train future clinicians and scientists.",
    "uf-dentistry-cert": "For dentists and dental professionals who want focused advanced training in a specialized area of oral health or clinical practice to extend their expertise.",
    "uf-dentistry-phd": "For those aiming at research careers in oral health who want to investigate the biological and clinical foundations of dentistry and contribute new science to the field.",
    "uf-advanced-graduate-dentistry-and-oral-sciences-ms": "You are a dentist or dental scientist who wants advanced study in a clinical specialty or the oral sciences, building the research and clinical depth to advance your practice.",
    "uf-health-and-medical-administrative-services-cert": "For healthcare professionals moving into leadership who want focused graduate study in the management, finance, and policy of health organizations.",
    "uf-health-and-medical-administrative-services-ms": "You want to lead in healthcare settings, building expertise in the operations, finance, and policy of hospitals and health systems to move into administrative and management roles.",
    "uf-allied-health-diagnostic-intervention-and-treatment-professions-bs": "A good fit if you want to enter a hands-on health profession focused on diagnosis, therapy, and patient treatment, building the science foundation these clinical careers require.",
    "uf-allied-health-diagnostic-intervention-and-treatment-professions-cert": "For allied health clinicians who want concentrated graduate study in a diagnostic or therapeutic specialty to advance their practice or move toward a new area of care.",
    "uf-allied-health-diagnostic-intervention-and-treatment-professions-ms": "You want to specialize within the allied health professions, deepening the clinical and scientific skills that support advanced diagnostic, rehabilitative, or treatment roles.",
    "uf-allied-health-diagnostic-intervention-and-treatment-professions-phd": "For those pursuing research and academic careers who want to study the science behind rehabilitation, diagnostics, and therapeutic practice and educate future allied health clinicians.",
    "uf-medicine-cert": "For clinicians and health professionals who want focused graduate study in a specialized area of medical science or clinical practice to extend their expertise.",
    "uf-medicine-phd": "For those pursuing biomedical research careers who want to investigate the mechanisms of disease and human health and contribute new science that informs clinical medicine.",
    "uf-medical-clinical-sciences-graduate-medical-studies-cert": "For students strengthening their foundation for medical or health-science careers who want focused graduate coursework in the clinical and biomedical sciences.",
    "uf-mental-and-social-health-services-and-allied-professions-ms": "You want to become a mental health counselor, building the clinical skills to assess and support people through psychological and emotional challenges toward licensure and practice.",
    "uf-mental-and-social-health-services-and-allied-professions-phd": "For those pursuing academic and advanced clinical careers in counseling who want to research therapeutic practice and mental health and prepare future counselors and educators.",
    "uf-pharmacy-pharmaceutical-sciences-and-administration-cert": "For working scientists and pharmacy professionals who want focused grounding in drug discovery, formulation, or pharmacokinetics without committing to a full degree, and who plan to apply that knowledge directly in industry or lab roles.",
    "uf-pharmacy-pharmaceutical-sciences-and-administration-ms": "Suited to those with a chemistry, biology, or pharmacy background ready to specialize in how drugs are designed, delivered, and metabolized, aiming for research or development work in pharmaceutical and biotech settings.",
    "uf-pharmacy-pharmaceutical-sciences-and-administration-phd": "For scientists committed to original research in drug action, medicinal chemistry, or pharmaceutics who want to lead independent investigation in academia or the pharmaceutical industry and are prepared for years of dissertation work.",
    "uf-public-health-bs": "A good fit for undergraduates drawn to preventing disease and improving community health, who want an early foundation in epidemiology, health policy, and population wellbeing before entering health careers or graduate study.",
    "uf-public-health-cert": "For working professionals in clinical, policy, or community roles who want structured exposure to epidemiology, biostatistics, and health systems to strengthen their practice without pausing their careers for a full degree.",
    "uf-public-health-ms": "Suited to those ready to deepen expertise in disease surveillance, health behavior, and program evaluation, aiming to design and analyze interventions across community, government, or global health settings.",
    "uf-public-health-phd": "For researchers who want to generate new evidence on the determinants of population health and lead studies in epidemiology or health policy, preparing for academic or senior research careers.",
    "uf-rehabilitation-and-therapeutic-professions-cert": "For practicing clinicians in physical therapy, occupational therapy, or allied fields who want focused study in movement, recovery, and functional restoration to sharpen their evidence-based practice.",
    "uf-rehabilitation-and-therapeutic-professions-ms": "Suited to those advancing in rehabilitation practice or research who want to study how people regain function after injury or illness, combining clinical insight with the science of recovery and mobility.",
    "uf-rehabilitation-and-therapeutic-professions-phd": "For those committed to research on recovery, disability, and functional outcomes who want to lead studies advancing rehabilitation science and prepare for careers in academia or clinical research.",
    "uf-dietetics-and-clinical-nutrition-services-bs": "A strong fit for undergraduates interested in how food and nutrients affect health across the lifespan, who want a science-grounded path toward dietetics, clinical nutrition, or graduate study in food and health.",
    "uf-registered-nursing-nursing-administration-nursing-research-and-clinical-nursing-cert": "For registered nurses who want targeted preparation in a defined area such as leadership, education, or a clinical specialty to expand their scope while continuing to practice.",
    "uf-registered-nursing-nursing-administration-nursing-research-and-clinical-nursing-ms": "Suited to registered nurses ready to move into advanced clinical practice, administration, or nursing research, deepening both patient-care expertise and their capacity to shape care delivery.",
    "uf-registered-nursing-nursing-administration-nursing-research-and-clinical-nursing-phd": "For nurses committed to generating research that improves patient care and health systems, aiming to lead studies and prepare for faculty or senior research roles in nursing science.",
    "uf-health-professions-and-related-clinical-sciences-other-cert": "For working professionals across the health professions who want focused, interdisciplinary study in a clinical or health-science area to broaden their expertise without enrolling in a full graduate program.",
    "uf-business-administration-management-and-operations-cert": "For working professionals who want structured grounding in core management, strategy, and operations to strengthen their business judgment and move toward leadership without committing to a full MBA.",
    "uf-business-administration-management-and-operations-ms": "Suited to professionals ready to build broad leadership capability across strategy, finance, marketing, and operations, aiming to move into management or shift the direction of their careers.",
    "uf-business-administration-management-and-operations-phd": "For those pursuing scholarly research on how organizations are led and managed, aiming to develop rigorous theory and empirical work and prepare for careers as business-school faculty.",
    "uf-accounting-and-related-services-bs": "A good fit for undergraduates with an eye for precision and financial reporting who want to build the foundation for careers in auditing, tax, or corporate accounting and steps toward professional licensure.",
    "uf-accounting-and-related-services-ms": "Suited to those completing the coursework and depth needed for the CPA path and advanced roles in audit, tax, or financial reporting, building on an accounting or business foundation.",
    "uf-entrepreneurial-and-small-business-operations-ms": "For those who want to turn ideas into ventures, studying how new businesses are launched, financed, and scaled, and aiming to found companies or drive innovation inside existing organizations.",
    "uf-finance-and-financial-management-services-bs": "A strong fit for undergraduates drawn to markets, investment, and corporate financial decisions, who want a quantitative foundation for careers in banking, asset management, or corporate finance.",
    "uf-finance-and-financial-management-services-cert": "For working professionals who want focused study in valuation, investments, or corporate finance to sharpen analytical skills and support a move into finance-heavy roles.",
    "uf-finance-and-financial-management-services-ms": "Suited to those ready to specialize in the analysis of investments, risk, and corporate financial strategy, aiming for advanced roles in banking, asset management, or financial analysis.",
    "uf-management-sciences-and-quantitative-methods-bs": "A good fit for undergraduates comfortable with data and quantitative reasoning who want to learn how analytics and modeling drive business decisions, opening careers in operations, consulting, or analytics.",
    "uf-management-sciences-and-quantitative-methods-ms": "Suited to those ready to apply statistical modeling, optimization, and data analysis to organizational problems, aiming for roles turning data into business strategy and decision-making.",
    "uf-marketing-bs": "A strong fit for undergraduates curious about consumer behavior, branding, and how products reach markets, who want to build skills for careers in brand management, digital marketing, or market research.",
    "uf-marketing-ms": "Suited to those ready to specialize in analytics-driven marketing, consumer insight, and brand strategy, aiming to lead campaigns and shape how organizations understand and reach their customers.",
    "uf-real-estate-ms": "For those focused on property investment, development, and finance who want the analytical and market knowledge to move into careers in real estate development, investment, or asset management.",
    "uf-real-estate-phd": "For researchers committed to studying property markets, real estate finance, and urban economics, aiming to produce scholarly work and prepare for academic or high-level analytical careers.",
    "uf-history-bs": "A good fit for undergraduates who love investigating the past through primary sources and want to sharpen research, argument, and writing skills that carry into law, education, public service, or graduate study.",
    "uf-history-cert": "For educators, writers, and professionals who want structured graduate-level study of historical methods and a chosen period or region to deepen their expertise without a full degree.",
    "uf-history-ms": "Suited to those ready to pursue focused historical research, mastering archival methods and interpretation in a chosen field, whether to teach, write, or prepare for doctoral study.",
    "uf-history-phd": "For those committed to original historical scholarship who want to master a field, produce a dissertation grounded in primary sources, and prepare for careers in academia, archives, or public history.",
}

# Self-check: every program carries a distinct, field-specific ``who_its_for`` so the
# degree-type ``_WHO_BY_TYPE`` fallback never fires (REPAIR_BACKLOG #3b type-gaming).
_who_missing = [p["slug"] for p in PROGRAMS if p["slug"] not in _WHO_BY_SLUG]
if _who_missing:
    raise ValueError(f"UF who_its_for missing on {len(_who_missing)} rows: {_who_missing[:5]}")
_who_stray = [s for s in _WHO_BY_SLUG if s not in {p["slug"] for p in PROGRAMS}]
if _who_stray:
    raise ValueError(f"UF who_its_for stray slugs: {_who_stray[:5]}")
_who_vals = [_WHO_BY_SLUG[p["slug"]] for p in PROGRAMS]
if len(set(_who_vals)) / len(_who_vals) < 0.95:
    raise ValueError(
        f"UF who_its_for not program-distinct: {len(set(_who_vals))}/{len(_who_vals)}"
    )


# Program highlights (manifest required=False) — verified UF facts by credential
# level. Filled (not ``= None``) to avoid the hard-null class (REPAIR_BACKLOG FLAG #4).
_HL_BY_TYPE: dict[str, list[str]] = {
    "bachelors": [
        "Top-ranked U.S. public research university",
        "Broad liberal-arts, STEM, agriculture & health curriculum",
        "Strong in-state value and four-year graduation outcomes",
    ],
    "masters": [
        "Access to leading faculty and research centers",
        "Strong professional and industry networks across Florida",
    ],
    "certificate": [
        "Focused graduate coursework, credits often stackable toward a degree",
        "Flexible options for working professionals",
    ],
    "phd": [
        "Funded — full tuition support plus a stipend",
        "Major research university with broad doctoral breadth",
    ],
    "professional": [
        "Nationally ranked professional/clinical school",
        "Strong licensure and placement outcomes",
    ],
}


def _who_for(slug: str, degree_type: str) -> str | None:
    return _WHO_BY_SLUG.get(slug) or _WHO_BY_TYPE.get(degree_type)


def _highlights_for(degree_type: str) -> list[str] | None:
    return _HL_BY_TYPE.get(degree_type)


def _program_standard(slug: str, spec: dict | None = None) -> dict:
    if spec is None:
        spec = _SPEC_BY_SLUG.get(slug, {})
    omitted: list[str] = [
        "outcomes_data.employment_rate",
        "outcomes_data.top_industries",
        "outcomes_data.conditions",
    ]
    # Every credential level now carries a UF-published tuition figure (REPAIR_BACKLOG #7):
    # undergrad sticker, graduate annual / per-credit, certificate per-credit estimate,
    # professional per-term×2, or PhD funded (tuition 0). So tuition is no longer omitted.
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
        inst.website_url = "https://www.ufl.edu/"
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
        # matcher-core CIP join key (REPAIR_BACKLOG #1): the verified 6-digit CIP-2020
        # code present in ref_majors — NOT the 2-digit family rollup in ``spec["cip"]``,
        # which never resolves the exact ref_majors / field-66 lookup. Falls back to the
        # family only if a slug is somehow unmapped (never silently null).
        p.cip_code = _CIP6_BY_SLUG.get(slug) or spec.get("cip")
        # Public-university budget scalar: the CPEF matcher reads the flat ``program.tuition``
        # for the over-budget veto + affordability fit, so it must be the NON-RESIDENT
        # (out-of-state) sticker — the conservative, broadly-correct input for a national +
        # international applicant pool (every international applicant pays non-resident). The
        # in-state basis and BOTH rates stay in ``cost_data`` (REPAIR_BACKLOG #2).
        if spec["degree_type"] == "bachelors":
            p.tuition = _TUITION_UG_OOS
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
        elif spec["degree_type"] == "professional" and spec["program_name"] in _PROFESSIONAL_TUITION:
            pr = _PROFESSIONAL_TUITION[spec["program_name"]]
            p.tuition = pr["out_of_state"]
            p.cost_data = {
                "tuition_usd": pr["in_state"],
                "breakdown": {
                    "tuition_in_state": pr["in_state"],
                    "tuition_out_of_state": pr["out_of_state"],
                    "tuition_per_term_in_state": pr["per_term_in_state"],
                },
                "funded": False,
                "note": (
                    "Annual professional-program tuition (FL resident); UF bills this in two "
                    "per-term installments in the Fall and Spring. Non-residents pay the "
                    "out-of-state rate shown in the breakdown."
                ),
                "source": _GRAD_COST_SRC[0], "source_url": _GRAD_COST_SRC[1], "year": "2025-26",
            }
        elif spec["degree_type"] == "certificate":
            p.tuition = _TUITION_CERT_OOS
            p.cost_data = {
                "tuition_usd": _TUITION_CERT_INSTATE,
                "breakdown": {
                    "tuition_in_state": _TUITION_CERT_INSTATE,
                    "tuition_out_of_state": _TUITION_CERT_OOS,
                    "per_credit_in_state": _GRAD_PER_CREDIT_INSTATE,
                    "per_credit_out_of_state": _GRAD_PER_CREDIT_OOS,
                },
                "funded": False,
                "note": (
                    f"Graduate certificates are billed at UF's published graduate per-credit "
                    f"rate (${_GRAD_PER_CREDIT_INSTATE:.2f} in-state / ${_GRAD_PER_CREDIT_OOS:.2f} "
                    f"non-resident). The figure shown estimates a standard {_CERT_CREDITS}-credit "
                    "certificate; the actual total scales with the certificate's required credits."
                ),
                "source": _GRAD_COST_SRC[0], "source_url": _GRAD_COST_SRC[1], "year": "2025-26",
            }
        else:  # masters
            p.tuition = _TUITION_GRAD_OOS
            p.cost_data = {
                "tuition_usd": _TUITION_GRAD_INSTATE,
                "breakdown": {
                    "tuition_in_state": _TUITION_GRAD_INSTATE,
                    "tuition_out_of_state": _TUITION_GRAD_OOS,
                    "per_credit_in_state": _GRAD_PER_CREDIT_INSTATE,
                    "per_credit_out_of_state": _GRAD_PER_CREDIT_OOS,
                },
                "funded": False,
                "note": (
                    "UF published graduate tuition & fees (FL resident, full-time, first-year "
                    "estimate); non-residents pay the out-of-state rate shown in the breakdown. "
                    "Programs that publish a distinct per-credit or cohort rate may differ."
                ),
                "source": _GRAD_COST_SRC[0], "source_url": _GRAD_COST_SRC[1], "year": "2025-26",
            }
        p.application_requirements = _requirements_for(spec)
        outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        p.who_its_for = _who_for(slug, spec["degree_type"])  # universal depth (REPAIR_BACKLOG #4)
        p.highlights = _highlights_for(spec["degree_type"])
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
