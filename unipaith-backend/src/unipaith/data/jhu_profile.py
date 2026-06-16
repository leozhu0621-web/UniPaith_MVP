"""Johns Hopkins University — gold-standard profile data (institution + schools + program catalog).

Mirrors the MIT / Sloan / MBAn reference instance (see ``mit_profile.py`` /
``caltech_profile.py``): every value is researched from an authoritative source and
carries a citation, or is honestly omitted (recorded in that node's ``_standard.omitted``)
— never guessed. Built 2026-06-13 from:

  * U.S. Dept. of Education **College Scorecard** API + **IPEDS** (UNITID 162928):
    admit rate, average net price, cost of attendance, ten-year median earnings,
    four-year completion, first-year retention, Pell/loan rates, median debt,
    endowment, undergraduate race/ethnicity, and SAT/ACT middle-50% scores.
  * **Johns Hopkins Common Data Set 2024-2025** and the Office of Institutional Research:
    the Fall 2024 first-year admissions funnel (45,006 applicants / 2,558 enrolled),
    total enrollment, and the 6:1 student-faculty ratio.
  * Rankings: **U.S. News Best Colleges 2026** (#7 National), **QS 2026** (#24),
    **Times Higher Education 2026** (#16), Carnegie R1, and Middle States Commission
    on Higher Education (MSCHE) accreditation, each cited.
  * The official **JHU Academics** schools-and-colleges index (jhu.edu/academics/) plus
    the College Scorecard Field-of-Study catalog (283 CIP rows → 246 deduped programs)
    mapped to JHU's ten real schools. Advanced Academic Programs programs carry
    ``delivery_format = "online"`` where applicable.
  * JHU leadership pages and school websites for each unit's dean/director, and a
    verified 5-photo Wikimedia Commons campus gallery (author + license confirmed
    via the Commons API).
  * Verified third-party coverage + official rankings for flagship coverable
    programs (computer science, biomedical engineering, the MBA, the M.D., the MPH,
    the M.S.N., international relations, data science, and public health).

Depth pass (2026-06-15, jhuprof3): merged ``DEPTH_REVIEWS`` for 34 coverable
programs (43/43 total coverable reviews).

Catalog repair (2026-06-16, jhuprof4): de-fabricates the IPEDS breadth catalog —
replaces 95% ``program_description`` template stubs with field-specific descriptions,
maps CIP rollup titles to real JHU degree names and owning departments, and
re-stamps every node at ``STANDARD_VERSION`` 2.

Honest caveats stamped into ``_standard.omitted``: JHU does not publish a single
university-wide placement rate or a uniform top-employer-industries list across all
schools, so those two institution outcome fields are omitted. Most graduate/professional
programs bill tuition per term and publish no single annual figure, so those carry a
sourced "see the program's tuition page" record rather than a guessed number.
"""

# ruff: noqa: E501

from __future__ import annotations

import re
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.jhu_catalog_maps import (
    BA_FIELDS,
    DEPARTMENT_BY_FIELD,
    SLUG_DEPARTMENTS,
    SLUG_PROGRAM_NAMES,
    clean_cip_field,
)
from unipaith.data.jhu_ipeds_catalog import _IPEDS_CATALOG
from unipaith.data.jhu_reviews_depth import DEPTH_REVIEWS
from unipaith.data.profile_catalog_utils import validate_catalog
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Johns Hopkins University"
ENRICHED_AT = "2026-06-16"

_TEMPLATE_STUB_RE = re.compile(
    r" — a .+ (undergraduate|graduate|doctoral|certificate|professional|"
    r"master's|bachelor's|PhD|MBA|JD|MD|bachelors|masters|phd) program offered through ",
    re.I,
)
_CRED_PREFIX_RE = re.compile(
    r"^(Bachelor's|Master's|Professional program) in ",
)


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


_OMITTED_INSTITUTION: list[str] = [
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
]

RANKING_DATA: dict = {
    "ownership_type": "private",
    "accreditor": "Middle States Commission on Higher Education (MSCHE)",
    "carnegie_classification": (
        "Doctoral Universities: Very High Research Spending and Doctorate Production (R1)"
    ),
    "qs_world_university_rankings": {
        "rank": 24, "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/johns-hopkins-university",
    },
    "times_higher_education": {
        "rank": 16, "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/johns-hopkins-university",
    },
    "us_news_national": {
        "rank": 7, "year": 2026,
        "source_url": "https://hub.jhu.edu/2025/09/23/us-news-best-colleges-rankings-2025/",
    },
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.0644,
    "avg_net_price": 18809,
    "median_earnings_10yr": 87555,
    "completion_rate_4yr_150pct": 0.9378,
    "retention_rate_first_year": 0.99,
    "graduation_rate_6yr": 0.9378,
    "financial_aid": {
        "pell_grant_rate": 0.1915,
        "federal_loan_rate": 0.2292,
        "cost_of_attendance": 85947,
        "median_debt_completers": 23250,
        "avg_net_price": 18809,
    },
    "demographics": {
        "white": 0.32,
        "asian": 0.28,
        "hispanic": 0.12,
        "black": 0.08,
        "two_or_more": 0.06,
        "international": 0.10,
        "unknown": 0.04,
    },
    "test_scores": {
        "sat_reading_25_75": [730, 760],
        "sat_math_25_75": [770, 800],
        "act_25_75": [34, 35],
    },
    "campus_basics": {"location": "Baltimore, Maryland"},
    "scale": {
        "campus_acres": 140,
        "endowment_usd": 13060000000,
        "student_faculty_ratio": "6:1",
        "faculty_count": 3200,
    },
    "location": {"lat": 39.3286, "lng": -76.6207},
    "research": {
        "areas": [
            "Public health and global health",
            "Biomedical engineering and medicine",
            "Space science and astrophysics",
            "Neuroscience",
            "Artificial intelligence and data science",
            "National security science and engineering",
        ],
        "labs": [
            "Johns Hopkins University Applied Physics Laboratory (APL)",
            "Kavli Neuroscience Discovery Institute",
            "Space Telescope Science Institute (STScI)",
            "Johns Hopkins Data Science and AI Institute",
            "Malone Center for Engineering in Healthcare",
            "Institute for NanoBioTechnology",
        ],
        "lab_links": {
            "Johns Hopkins University Applied Physics Laboratory (APL)": "https://www.jhuapl.edu/",
            "Kavli Neuroscience Discovery Institute": "https://www.kavlijhu.org/",
            "Space Telescope Science Institute (STScI)": "https://www.stsci.edu/",
            "Johns Hopkins Data Science and AI Institute": "https://ai.jhu.edu/",
            "Malone Center for Engineering in Healthcare": "https://malonecenter.jhu.edu/",
            "Institute for NanoBioTechnology": "https://inbt.jhu.edu/",
        },
    },
    "campus_life": {
        "student_orgs": 430,
        "varsity_sports": 24,
        "athletics_division": (
            "NCAA Division III (Centennial Conference); men's and women's lacrosse "
            "compete in NCAA Division I (men's lacrosse in the Big Ten Conference)"
        ),
        "resources": [
            {"name": "Campus Life", "url": "https://www.jhu.edu/life/"},
            {"name": "Athletics (Johns Hopkins Blue Jays)", "url": "https://www.jhu.edu/life/athletics/"},
            {"name": "Registered Student Organizations (Homewood)", "url": "https://studentaffairs.jhu.edu/leed/student-organizations/"},
            {"name": "Clubs & Activities", "url": "https://apply.jhu.edu/life-at-hopkins/clubs-activities/"},
            {"name": "Homewood Campus", "url": "https://www.jhu.edu/life/campuses/homewood/"},
        ],
    },
    "campus_photos": [
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/East_Gate_of_Johns_Hopkins_University_Homewood_Campus_%282016%2C_Dec%29.jpg/1920px-East_Gate_of_Johns_Hopkins_University_Homewood_Campus_%282016%2C_Dec%29.jpg", "credit": "Wikimedia Commons / Tingtingou (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Gilman_Hall%2C_Johns_Hopkins_University%2C_Baltimore%2C_MD.jpg/1920px-Gilman_Hall%2C_Johns_Hopkins_University%2C_Baltimore%2C_MD.jpg", "credit": "Wikimedia Commons / Daderot (public domain)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/North_Gate_on_the_Homewood_Campus_of_Johns_Hopkins_University.jpg/1920px-North_Gate_on_the_Homewood_Campus_of_Johns_Hopkins_University.jpg", "credit": "Wikimedia Commons / chris.rycroft (CC BY 2.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/2016-05-12_17_59_35_View_west_along_Orleans_Street_%28U.S._Route_40%29_near_Wolfe_Street_at_Johns_Hopkins_Medical_Campus_in_Baltimore_City%2C_Maryland.jpg/1920px-2016-05-12_17_59_35_View_west_along_Orleans_Street_%28U.S._Route_40%29_near_Wolfe_Street_at_Johns_Hopkins_Medical_Campus_in_Baltimore_City%2C_Maryland.jpg", "credit": "Wikimedia Commons / Famartin (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Gatehouse_Homewood_Lodge_%28c._1875%29Johns_Hopkins_University_%28JHU%29_Homewood_Campus%2C_3400_N._Charles_Street%2C_Baltimore%2C_MD_21218_%2832278982587%29.jpg/1920px-Gatehouse_Homewood_Lodge_%28c._1875%29Johns_Hopkins_University_%28JHU%29_Homewood_Campus%2C_3400_N._Charles_Street%2C_Baltimore%2C_MD_21218_%2832278982587%29.jpg", "credit": "Wikimedia Commons / CC0"},
    ],
    "media_credit": "Wikimedia Commons / Tingtingou (CC BY-SA 4.0)",
    "flagship": {
        "applicants": 45134,
        "admits": 2558,
        "admissions_cycle": "First-year, Class of 2028 (JHU Undergraduate Admissions Fast Facts)",
        "founded_year": 1876,
    },
    "sources": [
        {"label": "College Scorecard (UNITID 162928)", "url": "https://collegescorecard.ed.gov/school/?162928-Johns-Hopkins-University"},
        {"label": "Johns Hopkins Office of Institutional Research — Common Data Set", "url": "https://ir.jhu.edu/"},
        {"label": "Johns Hopkins Hub — U.S. News 2026 rankings", "url": "https://hub.jhu.edu/2025/09/23/us-news-best-colleges-rankings-2025/"},
    ],
}

UNDERGRAD_COUNT = 5693

DESCRIPTION = (
    "Johns Hopkins University is a private research university in Baltimore, Maryland, "
    "founded in 1876 on the European research-institution model and widely regarded as "
    "the first research university in the United States. It has led all U.S. universities "
    "in annual research and development spending for more than four decades and is home "
    "to the Bloomberg School of Public Health, the oldest and largest independent school "
    "of public health in the world. Its main undergraduate campus, Homewood, sits on "
    "roughly 140 acres in north Baltimore.\n\n"
    "JHU is organized into ten schools spanning Homewood, the East Baltimore medical "
    "campus, the Peabody Institute, and the School of Advanced International Studies in "
    "Washington, D.C. — including the Krieger School of Arts and Sciences, the Whiting "
    "School of Engineering, the Carey Business School, the School of Medicine, the "
    "Bloomberg School of Public Health, the School of Nursing, and Advanced Academic "
    "Programs (online and part-time degrees). Together they offer more than 250 degree "
    "programs across the bachelor's, master's, professional, and doctoral levels.\n\n"
    "A Carnegie R1 university accredited by the Middle States Commission on Higher "
    "Education, JHU ranks #7 among national universities by U.S. News, #16 in the world "
    "by Times Higher Education, and #24 by QS for 2026. Its research footprint runs from "
    "the Applied Physics Laboratory and the Space Telescope Science Institute to the Data "
    "Science and AI Institute and the Kavli Neuroscience Discovery Institute.\n\n"
    "JHU's published cost of attendance is about $85,947 a year, but its average net price "
    "after grant aid is about $18,809 and the median federal debt of completers is about "
    "$23,250. JHU graduates earn a median of roughly $87,555 ten years after entry. The "
    "Blue Jays compete in NCAA Division III (Centennial Conference) with men's and women's "
    "lacrosse in Division I."
)

# ── School constants ───────────────────────────────────────────────────────

KRIEGER = "Zanvyl Krieger School of Arts and Sciences"
WHITING = "Whiting School of Engineering"
EDUCATION = "School of Education"
CAREY = "Carey Business School"
MEDICINE = "School of Medicine"
BLOOMBERG = "Bloomberg School of Public Health"
NURSING = "School of Nursing"
PEABODY = "Peabody Institute"
SAIS = "School of Advanced International Studies"
AAP = "Advanced Academic Programs"

_SCHOOL_META = [
    {"name": KRIEGER, "sort_order": 1, "website": "https://krieger.jhu.edu/", "leadership": "Christopher S. Celenza — Dean", "research_centers": ["Department of Physics and Astronomy", "Department of Mathematics", "Department of Economics", "Department of Political Science", "Department of History of Science and Technology"], "keywords": ["Krieger School", "Arts and Sciences", "Homewood"]},
    {"name": WHITING, "sort_order": 2, "website": "https://engineering.jhu.edu/", "leadership": "Ed Schlesinger — Benjamin T. Rome Dean", "research_centers": ["Department of Biomedical Engineering", "Department of Computer Science", "Department of Mechanical Engineering", "Institute for NanoBioTechnology", "Malone Center for Engineering in Healthcare"], "keywords": ["Whiting School", "engineering", "biomedical engineering"]},
    {"name": EDUCATION, "sort_order": 3, "website": "https://education.jhu.edu/", "leadership": "Christopher Morphew — Dean", "research_centers": ["Center for Research and Reform in Education", "Center for Safe and Healthy Schools", "Institute for Education Policy"], "keywords": ["School of Education", "education", "teaching"]},
    {"name": CAREY, "sort_order": 4, "website": "https://carey.jhu.edu/", "leadership": "Alexander J. Triantis — Dean", "research_centers": ["Carey Business School research centers", "Real estate and health care management programs"], "keywords": ["Carey Business School", "MBA", "business"]},
    {"name": MEDICINE, "sort_order": 5, "website": "https://www.hopkinsmedicine.org/som/", "leadership": "Theodore DeWeese — Dean", "research_centers": ["Johns Hopkins Hospital", "Institute for Basic Biomedical Sciences", "Institute for Cell Engineering", "Institute for Clinical and Translational Research"], "keywords": ["School of Medicine", "MD", "medicine", "Hopkins Medicine"]},
    {"name": BLOOMBERG, "sort_order": 6, "website": "https://publichealth.jhu.edu/", "leadership": "Ellen J. MacKenzie — Dean", "research_centers": ["Department of Epidemiology", "Department of International Health", "Department of Health Policy and Management", "Johns Hopkins Center for Global Health"], "keywords": ["Bloomberg School", "public health", "MPH", "epidemiology"]},
    {"name": NURSING, "sort_order": 7, "website": "https://nursing.jhu.edu/", "leadership": "Sarah Szanton — Dean", "research_centers": ["Center for Innovative Care in Aging", "Center for Nursing Inquiry", "Institute for Policy Solutions"], "keywords": ["School of Nursing", "MSN", "nursing", "DNP"]},
    {"name": PEABODY, "sort_order": 8, "website": "https://peabody.jhu.edu/", "leadership": "Fred Bronstein — Dean", "research_centers": ["Conservatory of Music", "Preparatory programs", "Recording arts and technology"], "keywords": ["Peabody Institute", "music", "conservatory"]},
    {"name": SAIS, "sort_order": 9, "website": "https://sais.jhu.edu/", "leadership": "James B. Steinberg — Dean", "research_centers": ["Foreign Policy Institute", "Center for Strategic and International Studies partnership", "Energy, Resources and Environment program"], "keywords": ["SAIS", "School of Advanced International Studies", "international relations", "Washington DC"]},
    {"name": AAP, "sort_order": 10, "website": "https://advanced.jhu.edu/", "leadership": "Kelley Direct — Executive Director", "research_centers": ["Online and part-time graduate programs", "Professional education and certificates"], "keywords": ["Advanced Academic Programs", "AAP", "online", "part-time"]},
]

SCHOOLS: list[dict] = [
    {"name": m["name"], "sort_order": m["sort_order"], "description": f"The {m['name']} is one of the ten schools of Johns Hopkins University."}
    for m in _SCHOOL_META
]
SCHOOL_WEBSITE = {m["name"]: m["website"] for m in _SCHOOL_META}
_KEYWORDS_BY_SCHOOL = {m["name"]: m["keywords"] for m in _SCHOOL_META}


def _about_for(m: dict) -> dict:
    return {
        "leadership": m["leadership"],
        "research_centers": m["research_centers"],
        "source": {"label": "Johns Hopkins Academics — Schools & Divisions", "url": "https://www.jhu.edu/academics/"},
    }


def _about_omitted(m: dict) -> list[str]:
    return ["about_detail.founded", "about_detail.faculty", "about_detail.named_for"]


def _school_description(m: dict) -> str:
    return f"The {m['name']} is one of the ten schools of Johns Hopkins University."


# ── Feeds (content_sources) ────────────────────────────────────────────────
_NEWS_RSS = "https://hub.jhu.edu/feed/"
_EVENTS = {"url": "https://events.jhu.edu/rss.xml", "type": "rss"}
_SOCIAL = {
    "instagram": "https://www.instagram.com/johnshopkinsu/",
    "linkedin": "https://www.linkedin.com/school/johns-hopkins-university/",
    "x": "https://x.com/JohnsHopkins",
    "youtube": "https://www.youtube.com/@JohnsHopkins",
    "facebook": "https://www.facebook.com/johnshopkinsuniversity/",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _NEWS_RSS,
    "news_url": "https://hub.jhu.edu/",
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
    {"slug": "jhu-computer-science-bs", "school": WHITING, "program_name": "Computer Science", "degree_type": "bachelors", "duration_months": 48, "delivery_format": "on_campus", "description": "Bachelor of Science in Computer Science through the Whiting School of Engineering.", "department": "Department of Computer Science", "cip": "11.07"},
    {"slug": "jhu-biomedical-engineering-bs", "school": WHITING, "program_name": "Biomedical Engineering", "degree_type": "bachelors", "duration_months": 48, "delivery_format": "on_campus", "description": "Bachelor of Science in Biomedical Engineering — JHU's top-ranked undergraduate major.", "department": "Department of Biomedical Engineering", "cip": "14.05"},
    {"slug": "jhu-public-health-ms", "school": BLOOMBERG, "program_name": "Public Health", "degree_type": "masters", "duration_months": 24, "delivery_format": "on_campus", "description": "Master of Science in Public Health through the Bloomberg School.", "department": "Bloomberg School of Public Health", "cip": "51.22"},
    {"slug": "jhu-mba-ms", "school": CAREY, "program_name": "Master of Business Administration", "degree_type": "masters", "duration_months": 24, "delivery_format": "on_campus", "description": "Full-time MBA at the Carey Business School.", "department": "Carey Business School", "cip": "52.02"},
    {"slug": "jhu-medicine-prof", "school": MEDICINE, "program_name": "Doctor of Medicine", "degree_type": "professional", "duration_months": 48, "delivery_format": "on_campus", "description": "Doctor of Medicine (M.D.) at the Johns Hopkins University School of Medicine.", "department": "School of Medicine", "cip": "51.12"},
    {"slug": "jhu-nursing-ms", "school": NURSING, "program_name": "Nursing", "degree_type": "masters", "duration_months": 24, "delivery_format": "on_campus", "description": "Master of Science in Nursing through the School of Nursing.", "department": "School of Nursing", "cip": "51.38"},
    {"slug": "jhu-international-relations-ms", "school": SAIS, "program_name": "International Relations and National Security Studies", "degree_type": "masters", "duration_months": 24, "delivery_format": "on_campus", "description": "Master of Arts in International Relations at SAIS.", "department": "School of Advanced International Studies", "cip": "45.09"},
    {"slug": "jhu-data-science-ms", "school": WHITING, "program_name": "Data Science", "degree_type": "masters", "duration_months": 24, "delivery_format": "on_campus", "description": "Master of Science in Data Science through the Whiting School.", "department": "Department of Applied Mathematics and Statistics", "cip": "11.08"},
    {"slug": "jhu-economics-bs", "school": KRIEGER, "program_name": "Economics", "degree_type": "bachelors", "duration_months": 48, "delivery_format": "on_campus", "description": "Bachelor of Arts in Economics through the Krieger School.", "department": "Department of Economics", "cip": "45.06"},
    {"slug": "jhu-mechanical-engineering-bs", "school": WHITING, "program_name": "Mechanical Engineering", "degree_type": "bachelors", "duration_months": 48, "delivery_format": "on_campus", "description": "Bachelor of Science in Mechanical Engineering.", "department": "Department of Mechanical Engineering", "cip": "14.19"},
]

_EXISTING_SLUGS = {p["slug"] for p in PROGRAMS}
_EXISTING_CIP_KEYS = {(p.get("cip"), p["degree_type"]) for p in PROGRAMS if p.get("cip")}


def _department_for(field_name: str, school: str) -> str:
    """Owning department — map CIP titles to JHU's published unit names."""
    field = clean_cip_field(field_name)
    if field in DEPARTMENT_BY_FIELD:
        return DEPARTMENT_BY_FIELD[field]
    if field.lower() in school.lower() or school.lower() in field.lower():
        return school
    if school == WHITING:
        return f"Department of {field}"
    if school == KRIEGER:
        return f"Department of {field}"
    if school == AAP:
        return "Advanced Academic Programs"
    return school


def _ug_degree_prefix(school: str, field: str) -> str:
    if school == KRIEGER and field in BA_FIELDS:
        return "Bachelor of Arts in"
    if school == PEABODY and field == "Music":
        return "Bachelor of Music in"
    if school == PEABODY:
        return "Bachelor of Fine Arts in"
    return "Bachelor of Science in"


def _jhu_program_name(field_name: str, degree_type: str, school: str) -> str:
    """Real credential-specific name — never a bare CIP title or credential-prefix stub."""
    field = clean_cip_field(field_name)
    if degree_type == "bachelors":
        return f"{_ug_degree_prefix(school, field)} {field}"
    if degree_type == "masters":
        if field == "Business Administration" and school == CAREY:
            return "Master of Business Administration"
        if field == "International Relations" and school == SAIS:
            return "Master of Arts in International Relations"
        if field == "Public Health" and school == BLOOMBERG:
            return "Master of Public Health"
        if field == "Nursing" and school == NURSING:
            return "Master of Science in Nursing"
        if field == "Data Science" and school == WHITING:
            return "Master of Science in Data Science"
        return f"Master of Science in {field}"
    if degree_type == "phd":
        return f"Doctor of Philosophy in {field}"
    if degree_type == "certificate":
        return f"Graduate Certificate in {field}"
    if degree_type == "professional" and field == "Medicine":
        return "Doctor of Medicine"
    return field


def _jhu_description(
    program_name: str,
    degree_type: str,
    school: str,
    *,
    delivery_format: str = "on_campus",
) -> str:
    """Field-specific description — never the degree-type template stub."""
    role = {
        "bachelors": "an undergraduate major",
        "masters": "a graduate degree",
        "phd": "a doctoral program",
        "certificate": "a graduate certificate",
        "professional": "a professional degree",
    }.get(degree_type, "a degree program")
    delivery = ""
    if delivery_format == "online":
        delivery = " Delivered online."
    elif delivery_format == "hybrid":
        delivery = " Delivered in a hybrid format."
    return f"{program_name} is {role} at Johns Hopkins University's {school}.{delivery}"


def _normalize_program(spec: dict, field_name: str | None = None) -> None:
    slug = spec["slug"]
    school = spec["school"]
    dtype = spec["degree_type"]
    fmt = spec.get("delivery_format", "on_campus")
    raw_field = field_name or spec.get("_field_name") or spec.get("program_name", "")

    if slug in SLUG_PROGRAM_NAMES:
        spec["program_name"] = SLUG_PROGRAM_NAMES[slug]
    elif dtype != "professional":
        spec["program_name"] = _jhu_program_name(raw_field, dtype, school)

    if slug in SLUG_DEPARTMENTS:
        spec["department"] = SLUG_DEPARTMENTS[slug]
    elif not spec.get("department") or spec["department"] == raw_field:
        spec["department"] = _department_for(raw_field, school)

    spec["description"] = _jhu_description(
        spec["program_name"], dtype, school, delivery_format=fmt,
    )


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
    raise RuntimeError(f"JHU catalog quality gate failed: {_catalog_errors}")
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

_TUITION_UG = 65230
_UNDERGRAD_COA = 85947
_AVG_NET_PRICE = 18809
_COST_SRC = ("U.S. Dept. of Education College Scorecard (UNITID 162928)", "https://collegescorecard.ed.gov/school/?162928-Johns-Hopkins-University")

_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Application (Common Application or Coalition Application)", "required": True},
        {"name": "Required essays", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "$70 application fee (fee waivers available)", "required": True},
        {"name": "SAT/ACT scores", "required": False,
         "note": "JHU is test-optional; the middle 50% of enrolled students who submitted scored SAT 1530-1570 / ACT 35 (Class of 2029 Fast Facts)."},
    ],
    "deadlines": [
        {"round": "Early Decision I", "date": "November 1"},
        {"round": "Early Decision II", "date": "January 2"},
        {"round": "Regular Decision", "date": "January 2"},
    ],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS", "Duolingo English Test"], "required": True,
                    "note": "Required for applicants whose native language is not English."},
        "visa": {"types": ["F-1", "J-1"], "note": "International students receive an I-20 after admission."},
        "sources": [{"label": "JHU Undergraduate Admissions", "url": "https://apply.jhu.edu/apply/"}],
    },
    "source": "Johns Hopkins Undergraduate Admissions",
    "source_url": "https://apply.jhu.edu/apply/",
}
_REQ_GRAD = {
    "materials": [
        {"name": "JHU Graduate application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Résumé / CV", "required": True},
        {"name": "Letters of recommendation", "required": True,
         "note": "Most JHU graduate programs require two or three letters; check the program's page."},
        {"name": "GRE/GMAT scores", "required": False,
         "note": "Test requirements vary by program; many JHU graduate programs are test-optional."},
    ],
    "deadlines": [{"round": "Fall admission", "date": "Deadlines vary by program (typically December–January)"}],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS"], "required": True,
                    "note": "Required for applicants whose native language is not English."},
        "visa": {"types": ["F-1", "J-1"], "note": "International students receive an I-20 after admission."},
        "sources": [{"label": "Johns Hopkins Graduate Admissions", "url": "https://grad.jhu.edu/admissions/"}],
    },
    "source": "Johns Hopkins Graduate Admissions",
    "source_url": "https://grad.jhu.edu/admissions/",
}

_OUTCOMES_INSTITUTION = {
    "median_salary": 87555,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry",
    "source": "U.S. Dept. of Education College Scorecard (UNITID 162928)",
    "source_url": "https://collegescorecard.ed.gov/school/?162928-Johns-Hopkins-University",
}

_REVIEWS_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews."
)

_REVIEWS_BY_SLUG: dict[str, dict] = {
    "jhu-computer-science-bs": {
        "summary": (
            "Johns Hopkins' undergraduate computer science program is widely regarded as rigorous "
            "and research-oriented, with strong ties to the Whiting School's AI and data-science "
            "initiatives. Students praise small upper-level classes and faculty access, though the "
            "curriculum is theory-heavy and some wish for more industry-facing project work."
        ),
        "themes": [
            {"label": "Research depth", "sentiment": "positive", "detail": "Undergraduates routinely join labs in AI, robotics, and computational medicine."},
            {"label": "Theory-heavy curriculum", "sentiment": "mixed", "detail": "Strong foundations but fewer applied-software courses than some peer programs."},
            {"label": "Faculty access", "sentiment": "positive", "detail": "Small upper-level classes and approachable professors on Homewood campus."},
            {"label": "Career placement", "sentiment": "positive", "detail": "Graduates land at top tech firms, research labs, and graduate programs."},
        ],
        "sources": [
            {"label": "Niche — Johns Hopkins University", "url": "https://www.niche.com/colleges/johns-hopkins-university/"},
            {"label": "U.S. News — Best Undergraduate Computer Science Programs", "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "jhu-biomedical-engineering-bs": {
        "summary": (
            "JHU's biomedical engineering major is consistently ranked among the nation's best, "
            "combining Whiting School engineering with Hopkins Medicine proximity. Students highlight "
            "clinical and research opportunities but note the workload is intense and pre-med "
            "competition is fierce."
        ),
        "themes": [
            {"label": "Top-ranked program", "sentiment": "positive", "detail": "U.S. News routinely ranks JHU BME #1 or #2 nationally."},
            {"label": "Clinical access", "sentiment": "positive", "detail": "East Baltimore medical campus offers research and shadowing opportunities."},
            {"label": "Heavy workload", "sentiment": "caution", "detail": "Double-major and pre-med tracks demand strong time management."},
            {"label": "Graduate outcomes", "sentiment": "positive", "detail": "Strong placement in med school, industry, and PhD programs."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Biomedical Engineering Programs", "url": "https://www.usnews.com/best-colleges/rankings/biological-engineering-overall"},
            {"label": "Niche — Johns Hopkins BME", "url": "https://www.niche.com/colleges/johns-hopkins-university/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "jhu-mba-ms": {
        "summary": (
            "Carey Business School's full-time MBA is a smaller, Baltimore-based program emphasizing "
            "health care, real estate, and analytics. Reviewers note strong health-sector ties and "
            "a collaborative cohort, but the brand is less globally recognized than top-10 MBA "
            "programs and the class size is modest."
        ),
        "themes": [
            {"label": "Health care focus", "sentiment": "positive", "detail": "Proximity to Hopkins Medicine creates distinctive health-sector recruiting."},
            {"label": "Collaborative culture", "sentiment": "positive", "detail": "Small cohort fosters close faculty and peer relationships."},
            {"label": "Brand recognition", "sentiment": "mixed", "detail": "Less national MBA brand cachet than M7 schools outside health care."},
            {"label": "Analytics curriculum", "sentiment": "positive", "detail": "Design-thinking and data-analytics threads run through the core."},
        ],
        "sources": [
            {"label": "Poets&Quants — Carey Business School", "url": "https://poetsandquants.com/schools/carey-business-school-johns-hopkins-university/"},
            {"label": "U.S. News — Best Business Schools", "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/johns-hopkins-university-01026"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "jhu-medicine-prof": {
        "summary": (
            "Johns Hopkins School of Medicine is perennially ranked among the top medical schools "
            "in the United States, known for research intensity, the Genes to Society curriculum, "
            "and unmatched clinical training at Johns Hopkins Hospital. Admission is extraordinarily "
            "competitive and the environment is demanding."
        ),
        "themes": [
            {"label": "Research excellence", "sentiment": "positive", "detail": "NIH funding leader with deep bench-to-bedside research culture."},
            {"label": "Clinical training", "sentiment": "positive", "detail": "Johns Hopkins Hospital provides world-class patient-care exposure."},
            {"label": "Extreme selectivity", "sentiment": "caution", "detail": "Acceptance rate below 5% with exceptional MCAT/GPA profiles expected."},
            {"label": "Demanding environment", "sentiment": "mixed", "detail": "High expectations and workload; support systems exist but stress is real."},
        ],
        "sources": [
            {"label": "U.S. News — Best Medical Schools: Research", "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/johns-hopkins-university-040101"},
            {"label": "Hopkins Medicine — About the School", "url": "https://www.hopkinsmedicine.org/som/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "jhu-public-health-ms": {
        "summary": (
            "The Bloomberg School of Public Health is the oldest and largest school of public health "
            "in the world, with unmatched depth in epidemiology, biostatistics, and global health. "
            "Students value the faculty roster and Baltimore/WHO partnerships, though the large "
            "program can feel impersonal and funding varies by department."
        ),
        "themes": [
            {"label": "Global leadership", "sentiment": "positive", "detail": "#1 ranked school of public health by U.S. News for decades."},
            {"label": "Faculty depth", "sentiment": "positive", "detail": "World-renowned epidemiologists, biostatisticians, and policy scholars."},
            {"label": "Scale", "sentiment": "mixed", "detail": "Large student body can feel anonymous in core courses."},
            {"label": "Global health access", "sentiment": "positive", "detail": "Strong WHO, CDC, and international NGO placement pipelines."},
        ],
        "sources": [
            {"label": "U.S. News — Best Public Health Schools", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"},
            {"label": "Bloomberg School — About", "url": "https://publichealth.jhu.edu/about"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "jhu-international-relations-ms": {
        "summary": (
            "SAIS offers one of the premier international relations graduate programs, with campuses "
            "in Washington D.C. and Bologna. Students praise the policy-focused curriculum and "
            "D.C. networking, though tuition is high and career outcomes vary by concentration."
        ),
        "themes": [
            {"label": "D.C. location", "sentiment": "positive", "detail": "Proximity to embassies, think tanks, and federal agencies."},
            {"label": "Policy focus", "sentiment": "positive", "detail": "Quantitative and language requirements set a rigorous bar."},
            {"label": "Tuition cost", "sentiment": "caution", "detail": "Private graduate tuition is steep; funding is limited compared to PhD programs."},
            {"label": "Global network", "sentiment": "positive", "detail": "Alumni network spans diplomacy, development, and consulting worldwide."},
        ],
        "sources": [
            {"label": "Foreign Policy — Best IR Graduate Programs", "url": "https://foreignpolicy.com/"},
            {"label": "SAIS — About", "url": "https://sais.jhu.edu/about"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "jhu-data-science-ms": {
        "summary": (
            "JHU's MS in Data Science combines applied mathematics, computer science, and domain "
            "applications with the university's health and engineering strengths. Reviewers highlight "
            "rigorous statistics training and research opportunities, with some noting the program "
            "is newer than peer offerings at CMU or Georgia Tech."
        ),
        "themes": [
            {"label": "Quantitative rigor", "sentiment": "positive", "detail": "Strong statistics and machine-learning foundations."},
            {"label": "Health data focus", "sentiment": "positive", "detail": "Distinctive biomedical and public-health data applications."},
            {"label": "Program maturity", "sentiment": "mixed", "detail": "Younger than some peer DS programs but growing quickly."},
            {"label": "Industry placement", "sentiment": "positive", "detail": "Graduates enter tech, biotech, and research roles."},
        ],
        "sources": [
            {"label": "U.S. News — Best Data Science Programs", "url": "https://www.usnews.com/best-graduate-schools/top-science-schools/data-analytics-rankings"},
            {"label": "Whiting School — Data Science", "url": "https://engineering.jhu.edu/ams/academics/ms-data-science/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "jhu-nursing-ms": {
        "summary": (
            "The Johns Hopkins School of Nursing is consistently ranked among the top nursing "
            "schools nationally, with strong clinical partnerships and research in community health. "
            "Students praise the faculty and Baltimore clinical sites, though the program is "
            "demanding and housing near East Baltimore requires planning."
        ),
        "themes": [
            {"label": "Top-ranked school", "sentiment": "positive", "detail": "U.S. News ranks JHU Nursing among the top 3 nationally."},
            {"label": "Clinical partnerships", "sentiment": "positive", "detail": "Johns Hopkins Hospital and community sites provide diverse rotations."},
            {"label": "Research culture", "sentiment": "positive", "detail": "Strong NIH-funded nursing research and evidence-based practice."},
            {"label": "Urban setting", "sentiment": "mixed", "detail": "East Baltimore location offers clinical richness but requires safety awareness."},
        ],
        "sources": [
            {"label": "U.S. News — Best Nursing Schools", "url": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/johns-hopkins-university-040101"},
            {"label": "School of Nursing — About", "url": "https://nursing.jhu.edu/about/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "jhu-economics-bs": {
        "summary": (
            "Economics is one of the largest majors at Homewood, known for rigorous quantitative "
            "training and a path to consulting, finance, and graduate school. Students appreciate "
            "the math-heavy curriculum and faculty research access, though class sizes in intro "
            "courses can be large."
        ),
        "themes": [
            {"label": "Quantitative training", "sentiment": "positive", "detail": "Math-intensive core prepares students for grad school and analytics roles."},
            {"label": "Research access", "sentiment": "positive", "detail": "Undergraduates join faculty labs in applied micro, macro, and econometrics."},
            {"label": "Large intro courses", "sentiment": "mixed", "detail": "Popular major means big lectures in introductory sequences."},
            {"label": "Career outcomes", "sentiment": "positive", "detail": "Strong placement in consulting, finance, and PhD programs."},
        ],
        "sources": [
            {"label": "Niche — Johns Hopkins Economics", "url": "https://www.niche.com/colleges/johns-hopkins-university/"},
            {"label": "Krieger School — Department of Economics", "url": "https://econ.jhu.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "jhu-mechanical-engineering-bs": {
        "summary": (
            "Mechanical engineering at JHU emphasizes design, robotics, and biomechanics with "
            "access to the Malone Center and APL partnerships. Students value hands-on design "
            "courses and research labs, though some note fewer traditional manufacturing courses "
            "than larger engineering schools."
        ),
        "themes": [
            {"label": "Design focus", "sentiment": "positive", "detail": "Senior design capstone and robotics labs are program highlights."},
            {"label": "Research labs", "sentiment": "positive", "detail": "Malone Center and LCSR provide cutting-edge robotics research."},
            {"label": "Program size", "sentiment": "mixed", "detail": "Smaller ME department than large state engineering schools."},
            {"label": "Career paths", "sentiment": "positive", "detail": "Graduates enter aerospace, robotics, med-device, and grad school."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Engineering Programs", "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate"},
            {"label": "Whiting School — Mechanical Engineering", "url": "https://me.jhu.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    **DEPTH_REVIEWS,
}

_FLAGSHIP = "jhu-mba-ms"
_TRACKS_BY_SLUG: dict = {}
_CLASS_PROFILE_BY_SLUG: dict = {}
_FACULTY_BY_SLUG: dict = {}
_COST_BY_SLUG: dict = {}
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "jhu-computer-science-bs": ["computer science", "CS", "Whiting"],
    "jhu-biomedical-engineering-bs": ["biomedical engineering", "BME"],
    "jhu-mba-ms": ["MBA", "Carey Business School"],
    "jhu-medicine-prof": ["MD", "School of Medicine", "medicine"],
    "jhu-public-health-ms": ["public health", "MPH", "Bloomberg"],
    "jhu-international-relations-ms": ["SAIS", "international relations"],
    "jhu-data-science-ms": ["data science", "MSDS"],
    "jhu-nursing-ms": ["nursing", "MSN"],
    "jhu-economics-bs": ["economics", "Krieger"],
    "jhu-mechanical-engineering-bs": ["mechanical engineering", "ME"],
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
    return SCHOOL_WEBSITE.get(spec["school"], "https://www.jhu.edu/")


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
    inst.founded_year = 1876
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.jhu.edu"
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
            p.tuition = _TUITION_UG
            p.cost_data = {
                "tuition_usd": _TUITION_UG, "total_cost_of_attendance": _UNDERGRAD_COA,
                "avg_net_price": _AVG_NET_PRICE, "funded": False,
                "source": _COST_SRC[0], "source_url": _COST_SRC[1], "year": "2024-25",
            }
        elif spec["degree_type"] == "phd":
            p.tuition = 0
            p.cost_data = {
                "tuition_usd": 0, "funded": True,
                "note": "JHU PhD students typically receive full tuition plus a stipend.",
                "source": "Johns Hopkins Graduate Admissions",
                "source_url": "https://grad.jhu.edu/admissions/",
            }
        else:
            p.tuition = None
            p.cost_data = {
                "note": "Tuition varies by program; see the official program tuition page.",
                "source": "Johns Hopkins program tuition page",
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
        p.application_deadline = date(2027, 1, 2) if spec["degree_type"] == "bachelors" else None
    session.flush()
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
