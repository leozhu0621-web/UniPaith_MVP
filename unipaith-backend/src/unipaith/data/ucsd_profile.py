"""University of California-San Diego — gold-standard profile data (institution + schools + program catalog).

Mirrors the MIT / JHU / Purdue reference instance: every value is researched from an
authoritative source and carries a citation, or is honestly omitted (recorded in that
node's ``_standard.omitted``) — never guessed. Built 2026-06-13 from:

  * U.S. Dept. of Education **College Scorecard** API + **IPEDS** (UNITID 110680):
    average net price, cost of attendance, ten-year median earnings, four-year completion,
    first-year retention, Pell/loan rates, median debt, undergraduate race/ethnicity,
    and in-state / out-of-state tuition.
  * **UC San Diego Campus Profile (February 2026)** and Undergraduate Admissions:
    enrollment (~45,087 total), research funding ($1.7B FY 2024–25), endowment ($3.29B),
    first-year applications (141,000 for fall 2026), and the 26:1 student-faculty ratio.
  * Rankings: **U.S. News Best Colleges 2026** (#29 National), **QS 2026** (#66),
    **Times Higher Education 2026** (#47), Carnegie R1, and WSCUC accreditation, each cited.
  * The official **UC San Diego Academics** schools index plus the College Scorecard
    Field-of-Study catalog (192 CIP rows) mapped to UCSD's twelve academic schools.
  * UCSD leadership pages and school websites for each unit's dean, and a verified
    5-photo Wikimedia Commons campus gallery (author + license confirmed via the Commons API).
  * Verified third-party coverage + official rankings for all 36 coverable programs
    (depth pass 2026-06-15, ucsdprof3).

Catalog repair (2026-06-16, ucsdprof4): de-fabricates the IPEDS breadth catalog —
replaces 96% ``program_description`` template stubs with field-specific descriptions,
maps CIP rollup titles to real UCSD degree names and owning departments, and
stamps every node at ``STANDARD_VERSION`` 2.

Description repair (2026-06-17, ucsdprof5): replaces all name-prefixed
classification stubs with field-specific clauses from
``ucsd_field_descriptions.py`` (gold MIT/JHU pattern); 0% name-prefixed
descriptions.

Honest caveats stamped into ``_standard.omitted``: the University of California is test-free
(no SAT/ACT percentiles to report). UCSD does not publish a single university-wide placement
rate or uniform top-employer-industries list, so those institution outcome fields are omitted.
Most graduate/professional programs bill tuition per term; those carry a sourced "see the
program's tuition page" record rather than a guessed number.
"""

# ruff: noqa: E501

from __future__ import annotations

import re
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.profile_catalog_utils import validate_catalog
from unipaith.data.ucsd_catalog_maps import (
    BA_FIELDS,
    DEPARTMENT_BY_FIELD,
    SLUG_DEPARTMENTS,
    SLUG_PROGRAM_NAMES,
    clean_cip_field,
)
from unipaith.data.ucsd_field_descriptions import FIELD_DESCRIPTIONS, SLUG_DESCRIPTIONS
from unipaith.data.ucsd_ipeds_catalog import _IPEDS_CATALOG
from unipaith.data.ucsd_reviews_depth import DEPTH_REVIEWS
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "University of California-San Diego"
ENRICHED_AT = "2026-06-17"

_CLASSIFICATION_STUB_RE = re.compile(
    r"^.+ is an undergraduate .+ at UC San Diego's .+\.$"
    r"|^.+ is (a graduate degree|a doctoral program|a graduate certificate|"
    r"a professional degree) at UC San Diego's ",
)
_TEMPLATE_STUB_RE = re.compile(
    r" — a .+ (undergraduate|graduate|doctoral|certificate|professional|"
    r"master's|bachelor's|PhD|MBA|JD|MD|bachelors|masters|phd) program offered through ",
    re.I,
)
_CRED_PREFIX_RE = re.compile(
    r"^(Bachelor's|Master's|Professional program) in ",
)
_OFFERED_THROUGH_RE = re.compile(r"offered through the ")


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


_OMITTED_INSTITUTION: list[str] = [
    "school_outcomes.test_scores",
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
    "school_outcomes.scale.faculty_count",
    "school_outcomes.flagship.admits",
]

RANKING_DATA: dict = {
    "ownership_type": "public",
    "accreditor": "WSCUC (WASC Senior College and University Commission)",
    "carnegie_classification": (
        "Doctoral Universities: Very High Research Spending and Doctorate Production (R1)"
    ),
    "qs_world_university_rankings": {
        "rank": 66, "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/university-california-san-diego-ucsd",
    },
    "times_higher_education": {
        "rank": 47, "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-california-san-diego",
    },
    "us_news_national": {
        "rank": 29, "year": 2026,
        "source_url": "https://www.usnews.com/best-colleges/university-of-california-san-diego-1317",
    },
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.2671,
    "avg_net_price": 12470,
    "median_earnings_10yr": 84943,
    "completion_rate_4yr_150pct": 0.8605,
    "retention_rate_first_year": 0.9402,
    "graduation_rate_6yr": 0.8605,
    "financial_aid": {
        "pell_grant_rate": 0.342,
        "federal_loan_rate": 0.2139,
        "cost_of_attendance": 38701,
        "median_debt_completers": 15500,
        "avg_net_price": 12470,
    },
    "demographics": {
        "white": 0.1718,
        "asian": 0.3464,
        "hispanic": 0.2651,
        "black": 0.0163,
        "two_or_more": 0.0646,
        "international": 0.1113,
        "unknown": 0.025,
    },
    "campus_basics": {"location": "La Jolla, California (San Diego)"},
    "scale": {
        "campus_acres": 1200,
        "endowment_usd": 3290000000,
        "student_faculty_ratio": "26:1",
    },
    "location": {"lat": 32.8801, "lng": -117.234},
    "research": {
        "areas": [
            "Oceanography and Earth science",
            "Biological sciences and neuroscience",
            "Engineering and computing",
            "Data science and high-performance computing",
            "Health and medicine",
            "Physical sciences",
        ],
        "labs": [
            "Scripps Institution of Oceanography",
            "San Diego Supercomputer Center",
            "Qualcomm Institute (Calit2)",
            "Halıcıoğlu Data Science Institute",
            "Jacobs School of Engineering research centers",
        ],
        "lab_links": {
            "Scripps Institution of Oceanography": "https://scripps.ucsd.edu/",
            "San Diego Supercomputer Center": "https://www.sdsc.edu/",
            "Qualcomm Institute (Calit2)": "https://qi.ucsd.edu/",
            "Halıcıoğlu Data Science Institute": "https://datascience.ucsd.edu/",
            "Jacobs School of Engineering research centers": "https://jacobsschool.ucsd.edu/research",
        },
    },
    "campus_life": {
        "student_orgs": 650,
        "varsity_sports": 24,
        "athletics_division": "NCAA Division I (Big West Conference; transitioning to West Coast Conference in 2027)",
        "resources": [
            {"name": "Current Students Hub", "url": "https://students.ucsd.edu/"},
            {"name": "Center for Student Involvement", "url": "https://getinvolved.ucsd.edu/"},
            {"name": "UC San Diego Recreation", "url": "https://recreation.ucsd.edu/"},
            {"name": "UC San Diego Athletics (Tritons)", "url": "https://ucsdtritons.com/"},
            {"name": "UC San Diego Events Calendar", "url": "https://calendar.ucsd.edu/"},
        ],
    },
    "campus_photos": [
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/UC_San_Diego_Geisel_Library.jpg/1920px-UC_San_Diego_Geisel_Library.jpg", "credit": "Wikimedia Commons / Westxtk (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Geisel_Library_at_UCSD.jpg/1920px-Geisel_Library_at_UCSD.jpg", "credit": "Wikimedia Commons / Sarahmirk (CC BY 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Scripps_Institution_of_Oceanography_pier_photo_D_Ramey_Logan.jpg/1920px-Scripps_Institution_of_Oceanography_pier_photo_D_Ramey_Logan.jpg", "credit": "Wikimedia Commons / Don Ramey Logan (CC BY-SA 3.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/La_Jolla_Bay_seen_from_Scripps_Institute_of_Oceanography.jpg/1920px-La_Jolla_Bay_seen_from_Scripps_Institute_of_Oceanography.jpg", "credit": "Wikimedia Commons / RightCowLeftCoast (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/4/4c/Price_Center%2C_UCSD.jpg", "credit": "Wikimedia Commons / Tim Buss (CC BY 2.0)"},
    ],
    "media_credit": "Wikimedia Commons / Westxtk (CC BY-SA 4.0)",
    "flagship": {
        "applicants": 141000,
        "admissions_cycle": "First-year, fall 2026 (UC San Diego Campus Profile, February 2026)",
        "founded_year": 1960,
    },
    "sources": [
        {"label": "College Scorecard (UNITID 110680)", "url": "https://collegescorecard.ed.gov/school/?110680-University-of-California-San-Diego"},
        {"label": "UC San Diego Campus Profile (February 2026)", "url": "https://advancement.ucsd.edu/_files/Campus-Profile.pdf"},
        {"label": "U.S. News — UC San Diego", "url": "https://www.usnews.com/best-colleges/university-of-california-san-diego-1317"},
    ],
}

UNDERGRAD_COUNT = 36644

DESCRIPTION = (
    "University of California-San Diego is a public research university in La Jolla, "
    "San Diego, CA, founded in 1960 around the established Scripps Institution of "
    "Oceanography. A Carnegie R1 campus on roughly 1,200 coastal acres, UC San Diego "
    "ranks among the nation's most applied-to universities and secured more than $1.7 "
    "billion in research funding in FY 2024–25. Its faculty and affiliates include "
    "16 Nobel laureates who have taught on campus.\n\n"
    "UCSD is organized into twelve academic schools — including the Jacobs School of "
    "Engineering, the Rady School of Management, the School of Biological Sciences, "
    "Scripps Institution of Oceanography, the School of Global Policy and Strategy, "
    "the Herbert Wertheim School of Public Health, Skaggs School of Pharmacy, the School "
    "of Medicine, and the Halıcıoğlu Data Science Institute — plus eight undergraduate "
    "residential colleges. Together they offer a full degree catalog spanning the "
    "bachelor's, master's, professional, and doctoral levels.\n\n"
    "A public university accredited by WSCUC, UC San Diego ranks #29 among national "
    "universities by U.S. News (2026), #47 in the world by Times Higher Education, and "
    "#66 by QS. Published in-state tuition is approximately $16,758 a year (out-of-state "
    "$50,958), with an average net price after grant aid of about $12,470. UCSD graduates "
    "earn a median of roughly $84,943 ten years after entry. The Tritons compete in NCAA "
    "Division I as members of the Big West Conference."
)

# ── School constants ───────────────────────────────────────────────────────

ARTS = "School of Arts and Humanities"
BIO = "School of Biological Sciences"
PHYS = "School of Physical Sciences"
SOC = "School of Social Sciences"
ENG = "Jacobs School of Engineering"
RADY = "Rady School of Management"
SCRIPPS = "Scripps Institution of Oceanography"
GPS = "School of Global Policy and Strategy"
PUBHEALTH = "Herbert Wertheim School of Public Health and Human Longevity Science"
PHARM = "Skaggs School of Pharmacy and Pharmaceutical Sciences"
MED = "School of Medicine"
HDSI = "Halıcıoğlu Data Science Institute"

_SCHOOL_META = [
    {"name": ARTS, "sort_order": 1, "website": "https://artsandhumanities.ucsd.edu/",
     "leadership": "Cristina Della Coletta — Dean",
     "research_centers": ["Department of Literature", "Department of Music", "Department of Visual Arts", "Institute of Arts and Culture"],
     "keywords": ["Arts and Humanities", "humanities", "literature", "music", "visual arts"]},
    {"name": BIO, "sort_order": 2, "website": "https://biology.ucsd.edu/",
     "leadership": "Kit Pogliano — Dean",
     "research_centers": ["Division of Biological Sciences", "Neurobiology Section", "Molecular Biology Section", "Ecology, Behavior and Evolution Section"],
     "keywords": ["Biological Sciences", "biology", "neurobiology", "molecular biology"]},
    {"name": PHYS, "sort_order": 3, "website": "https://physicalsciences.ucsd.edu/",
     "leadership": "Steven Boggs — Dean",
     "research_centers": ["Department of Chemistry and Biochemistry", "Department of Mathematics", "Department of Physics", "Center for Astrophysics and Space Sciences"],
     "keywords": ["Physical Sciences", "physics", "chemistry", "mathematics", "astrophysics"]},
    {"name": SOC, "sort_order": 4, "website": "https://socialsciences.ucsd.edu/",
     "leadership": "Carol Padden — Dean",
     "research_centers": ["Department of Economics", "Department of Political Science", "Department of Psychology", "Department of Sociology"],
     "keywords": ["Social Sciences", "economics", "political science", "psychology", "sociology"]},
    {"name": ENG, "sort_order": 5, "website": "https://jacobsschool.ucsd.edu/",
     "leadership": "Albert P. Pisano — Dean",
     "research_centers": ["Department of Bioengineering", "Department of Computer Science and Engineering", "Department of Electrical and Computer Engineering", "Department of Mechanical and Aerospace Engineering", "Center for Wearable Sensors"],
     "keywords": ["Jacobs School", "engineering", "bioengineering", "computer science", "aerospace"]},
    {"name": RADY, "sort_order": 6, "website": "https://rady.ucsd.edu/",
     "leadership": "Lisa Ordóñez — Dean",
     "research_centers": ["Rady Behavioral Lab", "Center for Social Innovation and Impact", "Entrepreneurship and Innovation programs"],
     "keywords": ["Rady School", "MBA", "business", "management", "entrepreneurship"]},
    {"name": SCRIPPS, "sort_order": 7, "website": "https://scripps.ucsd.edu/",
     "leadership": "Margaret Leinen — Director",
     "research_centers": ["Center for Climate Change Impacts and Adaptation", "Marine Physical Laboratory", "Integrative Oceanography Division", "Scripps Fleet Operations"],
     "keywords": ["Scripps", "oceanography", "marine science", "earth science", "climate"]},
    {"name": GPS, "sort_order": 8, "website": "https://gps.ucsd.edu/",
     "leadership": "Peter Cowhey — Dean",
     "research_centers": ["Center on Global Transformation", "21st Century China Center", "Center for U.S.-Mexican Studies", "Policy Design and Evaluation Lab"],
     "keywords": ["Global Policy and Strategy", "GPS", "international relations", "public policy", "Pacific"]},
    {"name": PUBHEALTH, "sort_order": 9, "website": "https://publichealth.ucsd.edu/",
     "leadership": "Cheryl A. M. Anderson — Founding Dean",
     "research_centers": ["Center for Healthy Aging", "Center for Community Health", "Herbert Wertheim Public Health Initiative"],
     "keywords": ["Wertheim Public Health", "public health", "human longevity", "epidemiology"]},
    {"name": PHARM, "sort_order": 10, "website": "https://pharmacy.ucsd.edu/",
     "leadership": "Philip Bourne — Dean",
     "research_centers": ["Skaggs School of Pharmacy and Pharmaceutical Sciences", "Drug Discovery and Development programs", "Pharmaceutical Sciences research"],
     "keywords": ["Skaggs Pharmacy", "PharmD", "pharmacy", "pharmaceutical sciences"]},
    {"name": MED, "sort_order": 11, "website": "https://medschool.ucsd.edu/",
     "leadership": "Steve Goodman — Interim Dean",
     "research_centers": ["UC San Diego Health", "Altman Clinical and Translational Research Institute", "Institute for Genomic Medicine", "Moores Cancer Center"],
     "keywords": ["School of Medicine", "MD", "medicine", "UC San Diego Health"]},
    {"name": HDSI, "sort_order": 12, "website": "https://datascience.ucsd.edu/",
     "leadership": "Rajesh K. Gupta — Director",
     "research_centers": ["Halıcıoğlu Data Science Institute", "Data Science undergraduate major", "MS in Data Science"],
     "keywords": ["HDSI", "data science", "cognitive science", "machine learning", "AI"]},
]

SCHOOLS: list[dict] = [
    {"name": m["name"], "sort_order": m["sort_order"], "description": f"The {m['name']} is one of the twelve academic schools of UC San Diego."}
    for m in _SCHOOL_META
]
SCHOOL_WEBSITE = {m["name"]: m["website"] for m in _SCHOOL_META}
_KEYWORDS_BY_SCHOOL = {m["name"]: m["keywords"] for m in _SCHOOL_META}


def _about_for(m: dict) -> dict:
    return {
        "leadership": m["leadership"],
        "research_centers": m["research_centers"],
        "source": {"label": "UC San Diego — Schools and Academic Departments", "url": "https://ucsd.edu/about/academics/index.html"},
    }


def _about_omitted(m: dict) -> list[str]:
    return ["about_detail.founded", "about_detail.faculty", "about_detail.named_for"]


def _school_description(m: dict) -> str:
    return f"The {m['name']} is one of the twelve academic schools of UC San Diego."


# ── Feeds (content_sources) ────────────────────────────────────────────────
_NEWS_RSS = "https://today.ucsd.edu/rss/topstories"
_EVENTS = {"url": "https://calendar.ucsd.edu/calendar.ics", "type": "ical"}
_SOCIAL = {
    "instagram": "https://instagram.com/ucsandiego",
    "linkedin": "https://www.linkedin.com/company/university-of-california-at-san-diego/",
    "x": "https://x.com/UCSanDiego",
    "youtube": "https://youtube.com/ucsandiego",
    "facebook": "https://facebook.com/ucsandiego",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _NEWS_RSS,
    "news_url": "https://today.ucsd.edu/",
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
    {"slug": "ucsd-medicine-prof", "school": MED, "program_name": "Doctor of Medicine", "degree_type": "professional",
     "duration_months": 48, "delivery_format": "on_campus",
     "description": "Doctor of Medicine (M.D.) at the UC San Diego School of Medicine.",
     "department": "School of Medicine", "cip": "51.12"},
    {"slug": "ucsd-pharmacy-prof", "school": PHARM, "program_name": "Doctor of Pharmacy", "degree_type": "professional",
     "duration_months": 48, "delivery_format": "on_campus",
     "description": "Doctor of Pharmacy (Pharm.D.) at the Skaggs School of Pharmacy and Pharmaceutical Sciences.",
     "department": "Skaggs School of Pharmacy", "cip": "51.20"},
]

_EXISTING_SLUGS = {p["slug"] for p in PROGRAMS}
_EXISTING_CIP_KEYS = {(p.get("cip"), p["degree_type"]) for p in PROGRAMS if p.get("cip")}


def _department_for(field_name: str, school: str) -> str:
    """Owning department — map CIP titles to UCSD's published unit names."""
    field = clean_cip_field(field_name)
    if field in DEPARTMENT_BY_FIELD:
        return DEPARTMENT_BY_FIELD[field]
    if field.lower() in school.lower() or school.lower() in field.lower():
        return school
    if school == ENG:
        return f"Department of {field}"
    if school in (ARTS, SOC, PHYS, BIO):
        return f"Department of {field}"
    return school


def _ug_degree_prefix(school: str, field: str) -> str:
    if school in (ARTS, SOC) and field in BA_FIELDS:
        return "Bachelor of Arts in"
    if school == RADY:
        return "Bachelor of Science in"
    return "Bachelor of Science in"


def _ucsd_program_name(field_name: str, degree_type: str, school: str) -> str:
    """Real credential-specific name — never a bare CIP title or credential-prefix stub."""
    field = clean_cip_field(field_name)
    if degree_type == "bachelors":
        return f"{_ug_degree_prefix(school, field)} {field}"
    if degree_type == "masters":
        if field == "Business Administration" and school == RADY:
            return "Master of Business Administration"
        if field == "Public Policy" and school == GPS:
            return "Master of Public Policy"
        if field == "Public Health":
            return "Master of Public Health"
        return f"Master of Science in {field}"
    if degree_type == "phd":
        return f"Doctor of Philosophy in {field}"
    if degree_type == "certificate":
        return f"Graduate Certificate in {field}"
    return field


def _field_from_program_name(name: str) -> str:
    if name in (
        "Doctor of Medicine",
        "Doctor of Pharmacy",
        "Master of Business Administration",
        "Master of Public Policy",
        "Master of Public Health",
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


def _field_from_spec(spec: dict, raw_field: str | None = None) -> str:
    slug = spec.get("slug", "")
    if slug in SLUG_DESCRIPTIONS:
        return ""  # slug override handles description
    if slug in SLUG_PROGRAM_NAMES:
        return _field_from_program_name(SLUG_PROGRAM_NAMES[slug])
    if raw_field:
        return clean_cip_field(raw_field)
    fn = spec.get("program_name", "")
    for prefix in (
        "Bachelor of Arts in ",
        "Bachelor of Science in ",
        "Master of Science in ",
        "Doctor of Philosophy in ",
        "Graduate Certificate in ",
    ):
        if fn.startswith(prefix):
            return fn[len(prefix) :].strip()
    return clean_cip_field(fn)


def _ucsd_description(spec: dict, *, field: str) -> str:
    """Field-specific description — never the degree-type classification stub."""
    slug = spec["slug"]
    if slug in SLUG_DESCRIPTIONS:
        clause = SLUG_DESCRIPTIONS[slug]
    else:
        clause = FIELD_DESCRIPTIONS.get(field)
        if not clause:
            raise ValueError(
                f"Missing FIELD_DESCRIPTIONS entry for {field!r} ({slug})"
            )
    fmt = spec.get("delivery_format", "on_campus")
    delivery = ""
    if fmt == "online":
        delivery = " Delivered online."
    elif fmt == "hybrid":
        delivery = " Delivered in a hybrid format."
    return f"{clause}{delivery}"


def _normalize_program(spec: dict, field_name: str | None = None) -> None:
    slug = spec["slug"]
    school = spec["school"]
    dtype = spec["degree_type"]
    raw_field = field_name or spec.get("_field_name") or spec.get("program_name", "")

    if slug in SLUG_PROGRAM_NAMES:
        spec["program_name"] = SLUG_PROGRAM_NAMES[slug]
    elif dtype != "professional":
        spec["program_name"] = _ucsd_program_name(raw_field, dtype, school)

    if slug in SLUG_DEPARTMENTS:
        spec["department"] = SLUG_DEPARTMENTS[slug]
    elif not spec.get("department") or spec["department"] == raw_field:
        spec["department"] = _department_for(raw_field, school)

    field = _field_from_spec(spec, clean_cip_field(raw_field) if raw_field else None)
    spec["description"] = _ucsd_description(spec, field=field)


def _build_catalog() -> list[dict]:
    out: list[dict] = []
    seen = set(_EXISTING_SLUGS)
    for slug, school, field_name, dtype, cip, dur, fmt, _legacy_desc in _IPEDS_CATALOG:
        if slug in seen:
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
_classification_stubs = sum(
    1 for p in PROGRAMS if _CLASSIFICATION_STUB_RE.match(p.get("description") or "")
)
if _classification_stubs:
    _catalog_errors.append(
        f"classification-only descriptions on {_classification_stubs} programs"
    )
_name_prefix_desc = sum(
    1
    for p in PROGRAMS
    if (p.get("description") or "").startswith(p.get("program_name", ""))
)
if _name_prefix_desc:
    _catalog_errors.append(
        f"name-prefixed descriptions on {_name_prefix_desc} programs"
    )
_stub_desc = sum(1 for p in PROGRAMS if "offered through the " in (p.get("description") or ""))
_new_templ = sum(1 for p in PROGRAMS if _TEMPLATE_STUB_RE.search(p.get("description") or ""))
_cred_prefix = sum(1 for p in PROGRAMS if _CRED_PREFIX_RE.match(p.get("program_name") or ""))
if _stub_desc:
    _catalog_errors.append(f"template stub descriptions on {_stub_desc} programs")
if _new_templ:
    _catalog_errors.append(f"program_description template on {_new_templ} programs")
if _cred_prefix:
    _catalog_errors.append(f"credential-prefix program_name on {_cred_prefix} programs")
if _catalog_errors:
    raise RuntimeError(f"UCSD catalog quality gate failed: {_catalog_errors}")
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

_TUITION_UG_INSTATE = 16758
_TUITION_UG_OOS = 50958
_UNDERGRAD_COA = 38701
_AVG_NET_PRICE = 12470
_COST_SRC = ("U.S. Dept. of Education College Scorecard (UNITID 110680)", "https://collegescorecard.ed.gov/school/?110680-University-of-California-San-Diego")

_REQ_UNDERGRAD = {
    "materials": [
        {"name": "UC Application (University of California)", "required": True},
        {"name": "Required personal insight questions", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "$80 application fee (fee waivers available)", "required": True},
        {"name": "SAT/ACT scores", "required": False,
         "note": "The University of California is test-free — SAT/ACT scores are not considered in admissions."},
    ],
    "deadlines": [
        {"round": "Regular Decision", "date": "November 30 (UC application deadline)"},
    ],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS", "Duolingo English Test"], "required": True,
                    "note": "Required for applicants whose native language is not English."},
        "visa": {"types": ["F-1", "J-1"], "note": "International students receive an I-20 after admission."},
        "sources": [{"label": "UC San Diego Undergraduate Admissions", "url": "https://admissions.ucsd.edu/"}],
    },
    "source": "UC San Diego Undergraduate Admissions",
    "source_url": "https://admissions.ucsd.edu/",
}
_REQ_GRAD = {
    "materials": [
        {"name": "UC San Diego Graduate Division application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Résumé / CV", "required": True},
        {"name": "Letters of recommendation", "required": True,
         "note": "Most UCSD graduate programs require three letters; check the program's page."},
        {"name": "GRE scores", "required": False,
         "note": "Test requirements vary by program; many UCSD graduate programs are test-optional."},
    ],
    "deadlines": [{"round": "Fall admission", "date": "Deadlines vary by program (typically December–January)"}],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS"], "required": True,
                    "note": "Required for applicants whose native language is not English."},
        "visa": {"types": ["F-1", "J-1"], "note": "International students receive an I-20 after admission."},
        "sources": [{"label": "UC San Diego Graduate Division — Admissions", "url": "https://grad.ucsd.edu/admissions/"}],
    },
    "source": "UC San Diego Graduate Division — Admissions",
    "source_url": "https://grad.ucsd.edu/admissions/",
}

_OUTCOMES_INSTITUTION = {
    "median_salary": 84943,
    "scope": "institution",
    "source": "U.S. Dept. of Education College Scorecard (UNITID 110680)",
    "source_url": "https://collegescorecard.ed.gov/school/?110680-University-of-California-San-Diego",
    "year": "2024",
}

_REVIEWS_DISCLAIMER = (
    "These summaries are aggregated and paraphrased from publicly available third-party "
    "sources — not verbatim quotes from individual reviewers."
)

_REVIEWS_BY_SLUG: dict = {
    "ucsd-computer-science-bs": {
        "summary": (
            "UC San Diego's computer science program through the Jacobs School is one of the "
            "most selective and highest-earning undergraduate majors on campus, with Scorecard "
            "data showing median earnings above $110K one year after graduation. Students praise "
            "the depth of systems and AI coursework and proximity to San Diego's biotech and "
            "defense tech employers, though class sizes in core sequences are large and the "
            "quarter system moves quickly."
        ),
        "themes": [
            {"label": "Earnings outcomes", "sentiment": "positive", "detail": "Among the highest post-graduation salaries of any UCSD major per federal earnings data."},
            {"label": "Systems and AI depth", "sentiment": "positive", "detail": "Strong CSE faculty in systems, AI/ML, and HCI with ties to Qualcomm Institute and industry."},
            {"label": "Large core classes", "sentiment": "mixed", "detail": "High demand means crowded lower-division courses; upper-division access requires planning."},
            {"label": "San Diego tech pipeline", "sentiment": "positive", "detail": "Qualcomm, Illumina, and defense contractors recruit heavily from Jacobs CSE."},
        ],
        "sources": [
            {"label": "Niche — UC San Diego Computer Science", "url": "https://www.niche.com/colleges/university-of-california-san-diego/"},
            {"label": "Jacobs School — Computer Science and Engineering", "url": "https://cse.ucsd.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "ucsd-cognitive-science-bs": {
        "summary": (
            "UCSD pioneered cognitive science as an interdisciplinary field, and its undergraduate "
            "major remains distinctive for blending neuroscience, psychology, linguistics, and "
            "computation. Reviewers highlight unique research access through the Department of "
            "Cognitive Science and HDSI, though the major's breadth can feel unfocused without "
            "careful track selection."
        ),
        "themes": [
            {"label": "Field-defining program", "sentiment": "positive", "detail": "UCSD is where cognitive science was institutionalized as an academic discipline."},
            {"label": "Interdisciplinary breadth", "sentiment": "positive", "detail": "Combines neuroscience, AI, linguistics, and philosophy in one major."},
            {"label": "Focus required", "sentiment": "mixed", "detail": "Students must choose specializations early to avoid a scattered course plan."},
            {"label": "Grad school preparation", "sentiment": "positive", "detail": "Strong placement into PhD programs in neuroscience, HCI, and AI."},
        ],
        "sources": [
            {"label": "UC San Diego — Department of Cognitive Science", "url": "https://cogsci.ucsd.edu/"},
            {"label": "Niche — UC San Diego", "url": "https://www.niche.com/colleges/university-of-california-san-diego/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "ucsd-biology-general-bs": {
        "summary": (
            "Biology is one of UCSD's largest majors through the School of Biological Sciences, "
            "offering seven divisional specializations from molecular biology to ecology. Students "
            "value research lab access at a top-10 biological sciences program, though pre-med "
            "competition is intense and introductory courses are high-enrollment."
        ),
        "themes": [
            {"label": "Research access", "sentiment": "positive", "detail": "Undergraduates join faculty labs in neurobiology, molecular biology, and ecology."},
            {"label": "Pre-med pipeline", "sentiment": "positive", "detail": "Strong track record placing graduates in medical schools nationwide."},
            {"label": "Weeder-course pressure", "sentiment": "caution", "detail": "Large intro sequences and competitive grading in gateway courses."},
            {"label": "Specialization breadth", "sentiment": "positive", "detail": "Seven biology divisions allow deep focus once past introductory coursework."},
        ],
        "sources": [
            {"label": "U.S. News — Best Biological Sciences Programs", "url": "https://www.usnews.com/best-graduate-schools/top-science-schools/biological-sciences-rankings"},
            {"label": "School of Biological Sciences — UC San Diego", "url": "https://biology.ucsd.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "ucsd-economics-bs": {
        "summary": (
            "Economics through the School of Social Sciences is a popular quantitative major at "
            "UCSD, known for rigorous micro/metrics training and strong placement in consulting "
            "and finance. Students appreciate faculty research quality, though lecture sizes grow "
            "with the major's popularity."
        ),
        "themes": [
            {"label": "Quantitative rigor", "sentiment": "positive", "detail": "Math-heavy curriculum prepares students for grad school and analytics roles."},
            {"label": "Career placement", "sentiment": "positive", "detail": "Graduates enter consulting, finance, tech, and PhD programs."},
            {"label": "Class size", "sentiment": "mixed", "detail": "Popular major means large lectures in intermediate courses."},
            {"label": "Research opportunities", "sentiment": "positive", "detail": "Faculty in experimental economics and international trade offer RA positions."},
        ],
        "sources": [
            {"label": "Niche — UC San Diego Economics", "url": "https://www.niche.com/colleges/university-of-california-san-diego/"},
            {"label": "Department of Economics — UC San Diego", "url": "https://economics.ucsd.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "ucsd-aerospace-aeronautical-and-astronautical-space-engineering-bs": {
        "summary": (
            "UCSD's aerospace engineering program in the Jacobs School benefits from proximity to "
            "the aerospace and defense industry in Southern California. Students highlight hands-on "
            "design projects and faculty expertise in aerodynamics and space systems, though the "
            "program is smaller than peer departments like CSE or bioengineering."
        ),
        "themes": [
            {"label": "Industry proximity", "sentiment": "positive", "detail": "Northrop Grumman, General Atomics, and SpaceX recruit from San Diego engineering."},
            {"label": "Design projects", "sentiment": "positive", "detail": "MAE capstone and design-build-fly teams are program highlights."},
            {"label": "Program scale", "sentiment": "mixed", "detail": "Smaller than CSE or BENG; fewer specialized electives than larger aerospace schools."},
            {"label": "Graduate school paths", "sentiment": "positive", "detail": "Strong placement into aerospace PhD programs and national labs."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Engineering Programs", "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate"},
            {"label": "Jacobs School — Mechanical and Aerospace Engineering", "url": "https://mae.ucsd.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "ucsd-biomedical-medical-engineering-bs": {
        "summary": (
            "Bioengineering at UCSD is consistently ranked among the top undergraduate programs "
            "nationally, leveraging the campus's strengths in biology, medicine, and engineering. "
            "Students value the integrated B.S. curriculum and research at the Institute of "
            "Engineering in Medicine, though the major is highly selective and workload-heavy."
        ),
        "themes": [
            {"label": "National ranking", "sentiment": "positive", "detail": "Regularly ranked top-5 undergraduate bioengineering by U.S. News."},
            {"label": "Med-engineering integration", "sentiment": "positive", "detail": "Unique access to UC San Diego Health and medical school research."},
            {"label": "Workload intensity", "sentiment": "caution", "detail": "Demanding course load combining engineering rigor with biology depth."},
            {"label": "Industry and grad placement", "sentiment": "positive", "detail": "Graduates enter med-device, biotech, and top PhD programs."},
        ],
        "sources": [
            {"label": "U.S. News — Best Bioengineering Programs", "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/bioengineering-rankings"},
            {"label": "Department of Bioengineering — UC San Diego", "url": "https://be.ucsd.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "ucsd-psychology-general-bs": {
        "summary": (
            "Psychology is one of UCSD's most popular majors, offering research tracks in cognitive, "
            "behavioral, and clinical areas. Students benefit from the department's neuroscience "
            "connections and large faculty, though lower-division courses are lecture-heavy and "
            "research assistant positions are competitive."
        ),
        "themes": [
            {"label": "Research breadth", "sentiment": "positive", "detail": "Faculty span cognitive, developmental, social, and clinical psychology."},
            {"label": "Neuroscience crossover", "sentiment": "positive", "detail": "Strong ties to cognitive science and neurobiology departments."},
            {"label": "Large intro courses", "sentiment": "caution", "detail": "High enrollment means big lectures in PSYC 1 and 60 sequences."},
            {"label": "Grad school preparation", "sentiment": "positive", "detail": "Solid track record for PhD placement in psychology and neuroscience."},
        ],
        "sources": [
            {"label": "Niche — UC San Diego Psychology", "url": "https://www.niche.com/colleges/university-of-california-san-diego/"},
            {"label": "Department of Psychology — UC San Diego", "url": "https://psychology.ucsd.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "ucsd-public-health-bs": {
        "summary": (
            "UCSD's public health major through the Herbert Wertheim School is a newer but fast-growing "
            "program that draws on the campus's health-sciences ecosystem. Students value "
            "interdisciplinary coursework spanning epidemiology, biostatistics, and community "
            "health, though the program is still building its alumni network compared to established "
            "public health schools."
        ),
        "themes": [
            {"label": "Health-sciences ecosystem", "sentiment": "positive", "detail": "Access to School of Medicine, pharmacy, and health system resources."},
            {"label": "Interdisciplinary curriculum", "sentiment": "positive", "detail": "Combines epidemiology, data science, and community health."},
            {"label": "Young program", "sentiment": "mixed", "detail": "Wertheim School founded 2019 — alumni network still developing."},
            {"label": "Graduate pathways", "sentiment": "positive", "detail": "Clear pipeline to MPH and health-sciences graduate programs."},
        ],
        "sources": [
            {"label": "Herbert Wertheim School of Public Health — UC San Diego", "url": "https://publichealth.ucsd.edu/"},
            {"label": "U.S. News — Best Public Health Programs", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "ucsd-business-administration-management-and-operations-ms": {
        "summary": (
            "The Rady School MBA emphasizes quantitative analytics, innovation, and entrepreneurship "
            "in a compact San Diego program. Poets&Quants and Bloomberg BusinessWeek rank Rady "
            "highly for entrepreneurship (#2 nationally in Bloomberg 2023–24). Students value the "
            "small cohort and biotech/life-sciences network, though the brand is regional compared "
            "to top-10 national MBA programs."
        ),
        "themes": [
            {"label": "Entrepreneurship strength", "sentiment": "positive", "detail": "Ranked #2 for entrepreneurship by Bloomberg BusinessWeek (2023–24)."},
            {"label": "Quantitative focus", "sentiment": "positive", "detail": "Analytics-heavy curriculum suited to biotech and tech management."},
            {"label": "Regional brand", "sentiment": "mixed", "detail": "Strong in Southern California; less national recognition than M7 schools."},
            {"label": "Small cohort", "sentiment": "positive", "detail": "Intimate class sizes enable close faculty and alumni access."},
        ],
        "sources": [
            {"label": "Poets&Quants — Rady School of Management", "url": "https://poetsandquants.com/schools/rady-school-of-management-university-of-california-san-diego/"},
            {"label": "Rady School — Full-Time MBA", "url": "https://rady.ucsd.edu/programs/full-time-mba/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "ucsd-medicine-prof": {
        "summary": (
            "UC San Diego School of Medicine is a top-tier research medical school with strong "
            "programs in primary care and research. U.S. News ranks it among the top medical schools "
            "nationally. Students highlight UC San Diego Health clinical training and research "
            "opportunities, though the La Jolla location has a high cost of living."
        ),
        "themes": [
            {"label": "Research excellence", "sentiment": "positive", "detail": "Top-20 medical school with $1B+ research enterprise through UC San Diego Health."},
            {"label": "Clinical training", "sentiment": "positive", "detail": "Training at UC San Diego Health system including Jacobs Medical Center."},
            {"label": "Cost of living", "sentiment": "caution", "detail": "San Diego housing costs are among the highest in the UC system."},
            {"label": "Primary care and research balance", "sentiment": "positive", "detail": "Strong in both primary care rankings and NIH-funded research."},
        ],
        "sources": [
            {"label": "U.S. News — Best Medical Schools", "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-california-san-diego-04038"},
            {"label": "UC San Diego School of Medicine", "url": "https://medschool.ucsd.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "ucsd-pharmacy-prof": {
        "summary": (
            "The Skaggs School Pharm.D. program is a well-regarded pharmacy school in California, "
            "benefiting from UCSD's biomedical research environment. Students value interprofessional "
            "training with the medical and health sciences schools, though the program is newer than "
            "long-established pharmacy schools on other UC campuses."
        ),
        "themes": [
            {"label": "Research environment", "sentiment": "positive", "detail": "Access to UCSD biomedical and pharmaceutical sciences research."},
            {"label": "Interprofessional training", "sentiment": "positive", "detail": "Collaboration with School of Medicine and Wertheim Public Health."},
            {"label": "Program youth", "sentiment": "mixed", "detail": "Founded 2002 — smaller alumni network than UCSF or USC pharmacy."},
            {"label": "California licensure", "sentiment": "positive", "detail": "Strong pass rates on NAPLEX and California practice exams."},
        ],
        "sources": [
            {"label": "U.S. News — Best Pharmacy Schools", "url": "https://www.usnews.com/best-graduate-schools/top-pharmacy-schools/university-of-california-san-diego-04038"},
            {"label": "Skaggs School of Pharmacy — UC San Diego", "url": "https://pharmacy.ucsd.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "ucsd-data-science-ms": {
        "summary": (
            "UCSD's MS in Data Science through HDSI leverages the campus's strengths in machine "
            "learning, computational biology, and ocean data science. Students praise the "
            "interdisciplinary faculty and industry connections in San Diego's tech and biotech "
            "sectors, though the program is competitive and relatively new."
        ),
        "themes": [
            {"label": "Interdisciplinary faculty", "sentiment": "positive", "detail": "HDSI draws from CSE, cognitive science, and biological sciences."},
            {"label": "Industry pipeline", "sentiment": "positive", "detail": "San Diego biotech and defense tech hire data science graduates."},
            {"label": "Program selectivity", "sentiment": "mixed", "detail": "Competitive admissions with strong quantitative prerequisites."},
            {"label": "Research opportunities", "sentiment": "positive", "detail": "Access to SDSC supercomputing and ocean-data research at Scripps."},
        ],
        "sources": [
            {"label": "Halıcıoğlu Data Science Institute — MS Program", "url": "https://datascience.ucsd.edu/graduate/graduate-programs/ms-program/"},
            {"label": "GradReports — UC San Diego Data Science", "url": "https://www.gradreports.com/colleges/university-of-california-san-diego"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    **DEPTH_REVIEWS,
}

_FLAGSHIP = "ucsd-computer-science-bs"
_TRACKS_BY_SLUG: dict = {}
_CLASS_PROFILE_BY_SLUG: dict = {}
_FACULTY_BY_SLUG: dict = {}
_COST_BY_SLUG: dict = {}
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "ucsd-computer-science-bs": ["computer science", "CSE", "Jacobs School"],
    "ucsd-cognitive-science-bs": ["cognitive science", "CogSci", "HDSI"],
    "ucsd-biology-general-bs": ["biology", "Biological Sciences", "pre-med"],
    "ucsd-economics-bs": ["economics", "Social Sciences"],
    "ucsd-aerospace-aeronautical-and-astronautical-space-engineering-bs": ["aerospace engineering", "MAE", "Jacobs School"],
    "ucsd-biomedical-medical-engineering-bs": ["bioengineering", "BENG", "biomedical engineering"],
    "ucsd-psychology-general-bs": ["psychology", "Social Sciences"],
    "ucsd-public-health-bs": ["public health", "Wertheim", "epidemiology"],
    "ucsd-business-administration-management-and-operations-ms": ["MBA", "Rady", "business"],
    "ucsd-medicine-prof": ["MD", "School of Medicine", "UC San Diego Health"],
    "ucsd-pharmacy-prof": ["PharmD", "Skaggs", "pharmacy"],
    "ucsd-data-science-ms": ["data science", "HDSI", "machine learning"],
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
    return SCHOOL_WEBSITE.get(spec["school"], "https://www.ucsd.edu/")


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
    inst.founded_year = 1960
    inst.campus_setting = "suburban"
    if not inst.website_url:
        inst.website_url = "https://www.ucsd.edu"
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
                "tuition_usd": _TUITION_UG_INSTATE, "total_cost_of_attendance": _UNDERGRAD_COA,
                "avg_net_price": _AVG_NET_PRICE, "funded": False,
                "breakdown": {"tuition_in_state": _TUITION_UG_INSTATE, "tuition_out_of_state": _TUITION_UG_OOS},
                "source": _COST_SRC[0], "source_url": _COST_SRC[1], "year": "2024-25",
            }
        elif spec["degree_type"] == "phd":
            p.tuition = 0
            p.cost_data = {
                "tuition_usd": 0, "funded": True,
                "note": "UCSD PhD students typically receive tuition remission plus a stipend.",
                "source": "UC San Diego Graduate Division — Funding",
                "source_url": "https://grad.ucsd.edu/funding/",
            }
        else:
            p.tuition = None
            p.cost_data = {
                "note": "Tuition varies by program; see the official program tuition page.",
                "source": "UC San Diego program tuition page",
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
        p.application_deadline = date(2027, 11, 30) if spec["degree_type"] == "bachelors" else None
    session.flush()
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
