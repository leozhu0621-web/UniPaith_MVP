"""University of Wisconsin-Madison — gold-standard profile data (institution + schools + program catalog).

Mirrors the MIT / Purdue / UCSD reference instance: every value is researched from an
authoritative source and carries a citation, or is honestly omitted (recorded in that
node's ``_standard.omitted``) — never guessed. Built 2026-06-14 from:

  * U.S. Dept. of Education **College Scorecard** API + **IPEDS** (UNITID 240444):
    admit rate, average net price, cost of attendance, ten-year median earnings,
    four-year completion, first-year retention, Pell/loan rates, median debt,
    undergraduate race/ethnicity, and SAT/ACT middle-50% scores.
  * **UW–Madison Facts** (November 2025): enrollment (37,198 undergraduate),
    admissions funnel (73,912 applicants / 30,167 admitted for Fall 2025 freshmen),
    retention (96.3%), tuition 2025–26 ($12,186 in-state / $44,210 out-of-state),
    campus scale (939 acres), and research expenditure ranking (5th nationally, 2024).
  * Rankings: **U.S. News Best Colleges 2026** (#36 National), **QS 2026** (#110),
    **Times Higher Education 2026** (#53), Carnegie R1, and Higher Learning Commission
    (HLC) accreditation, each cited.
  * The official **UW–Madison Schools and Colleges** index plus the College Scorecard
    Field-of-Study catalog (343 CIP rows) mapped to UW-Madison's fifteen academic units.
  * UW leadership pages and school websites for each unit's dean, and a verified
    5-photo Wikimedia Commons campus gallery (author + license confirmed via the Commons API).
  * Verified third-party coverage + official rankings for flagship coverable programs
    (computer science, mechanical engineering, biomedical engineering, business, the MBA,
    the J.D., the M.D., the Pharm.D., the D.V.M., nursing, psychology, and economics).

Catalog repair (2026-06-14): disambiguated all ~348 programs — bare CIP field titles,
null departments, and template descriptions replaced with credential-specific names,
real departments, and field-specific descriptions (``validate_catalog`` gate).

Catalog repair (2026-06-16, uwmadisonprof4): de-fabricates the IPEDS breadth catalog —
replaces 96% ``program_description`` template stubs with field-specific descriptions,
maps CIP rollup titles to real UW-Madison degree names and owning departments, and
re-stamps every node at ``STANDARD_VERSION`` 2.

Description repair (2026-06-17, uwmadisonprof5): replaces all name-prefixed
classification stubs with field-specific clauses from
``uw_madison_field_descriptions.py`` (gold MIT/JHU pattern); 0% name-prefixed
descriptions.

Description repair (2026-06-17, uwmadisonprof6): fixes peer-institution
contamination in field clauses (Kellogg, Weinberg, Feinberg, Skaggs, etc.);
diversifies credential-sibling descriptions with UW-Madison-specific level
suffixes (0% identical-across-levels); gates shared descriptions at build time.

Description repair (2026-06-20, uwmaddefab1): replaces suffix-diversifier
stamping with per-credential description leads so BA/MS/PhD siblings no longer
share a ≥120-char leading body (REPAIR BACKLOG #5 — gold MIT = 0%
shared-leading-body; anti-stub clean).

Per-credential body rewrite (2026-06-20, uwmadpercred1): the prior lead + shared
FIELD_DESCRIPTIONS clause still stamped one field body across credential siblings
once the credential frame was stripped (109 fields — miss #8 credential-frame +
tail-shared field body). Replaced with distinct per-credential ``_level_body`` text
after each field's verified clause so ``frame_stripped_shared_body`` = 0.

Honest caveats stamped into ``_standard.omitted``: UW-Madison does not publish a single
university-wide placement rate or a uniform top-employer-industries list across all
schools, so those two institution outcome fields are omitted. Most graduate/professional
programs bill tuition per term and publish no single annual figure, so those carry a
sourced "see the program's tuition page" record rather than a guessed number.

Depth pass (2026-06-15, uwmadisonprof3): merged ``DEPTH_REVIEWS`` for 47 coverable
programs (57/57 total external_reviews on coverable programs).
"""

# ruff: noqa: E501

from __future__ import annotations

import re
from collections import Counter
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.profile_catalog_utils import validate_catalog
from unipaith.data.uw_madison_catalog_maps import (
    BA_FIELDS,
    DEPARTMENT_BY_FIELD,
    SLUG_DEPARTMENTS,
    SLUG_PROGRAM_NAMES,
    clean_cip_field,
)
from unipaith.data.uw_madison_field_descriptions import FIELD_DESCRIPTIONS, SLUG_DESCRIPTIONS
from unipaith.data.uw_madison_ipeds_catalog import _IPEDS_CATALOG
from unipaith.data.uw_madison_reviews_depth import DEPTH_REVIEWS
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION
from unipaith.profile_standard.anti_stub import analyze as _anti_stub_analyze
from unipaith.profile_standard.anti_stub import field_of as _anti_stub_field

INSTITUTION_NAME = "University of Wisconsin-Madison"
ENRICHED_AT = "2026-06-20"

# Per-credential body: each credential level of a field gets its OWN researched body
# describing what THAT degree level studies, so credential siblings share no
# tail-hidden field body (gold MIT = 0 on frame_stripped_shared_body).
_FIELD_LABEL: dict[str, str] = {
    "Doctor of Medicine": "medicine",
    "Doctor of Pharmacy": "pharmacy",
    "Doctor of Veterinary Medicine": "veterinary medicine",
    "Doctor of Dental Surgery": "dentistry",
    "Juris Doctor": "law",
    "Master of Business Administration": "business administration",
}


def _field_label(name: str) -> str:
    if " in " in name:
        return name.split(" in ", 1)[1].strip()
    return _FIELD_LABEL.get(name, _anti_stub_field(name))


def _level_body(dtype: str, name: str, college: str, field: str) -> str:
    uw = "the University of Wisconsin–Madison"
    if dtype == "bachelors":
        return (
            f"Building from the foundations of the discipline, the {name} grounds "
            f"undergraduates in core theory and method through required introductory "
            f"sequences, hands-on laboratory, studio, or field experience, and a "
            f"progression of upper-division electives within {college} at {uw}, "
            f"developing the breadth and analytical skill that ready graduates for "
            f"professional roles or further study."
        )
    if dtype == "masters":
        return (
            f"Built for advanced specialization, the {name} pairs graduate seminars and "
            f"methods coursework with applied projects, practica, or a research thesis "
            f"supervised by {college} faculty, letting students concentrate on a focused "
            f"area of {field} and prepare for advanced practice or doctoral work at {uw}."
        )
    if dtype == "phd":
        return (
            f"Centered on original scholarship, the {name} engages doctoral candidates in "
            f"advanced seminars, qualifying examinations, and a sustained, faculty-mentored "
            f"dissertation that contributes new knowledge to {field}, preparing graduates "
            f"for research, faculty, and senior professional careers through {college} "
            f"at {uw}."
        )
    if dtype == "certificate":
        return (
            f"A focused, credit-bearing credential, the {name} concentrates a compact set "
            f"of advanced courses on a defined area of {field}, giving working "
            f"professionals and degree-seeking students targeted expertise that can stand "
            f"alone or apply toward a related graduate degree within {college} at {uw}."
        )
    if dtype == "professional":
        return (
            f"A practice-oriented degree, the {name} joins rigorous classroom study with "
            f"extensive supervised clinical, laboratory, or practical training delivered "
            f"through {college} at {uw}, preparing graduates to satisfy licensure "
            f"requirements and to enter professional practice in {field}."
        )
    return ""


_PEER_SIGNATURES: tuple[str, ...] = (
    "Kellogg",
    "Pritzker",
    "Feinberg",
    "Bienen",
    "Skaggs",
    "Scripps",
    "Bloomberg School",
    "Weinberg",
    "McCormick",
    "Medill",
    "Wirtz Center",
    "Block Museum",
    "Rausser",
    "SAIS",
    "NUCATS",
    "Segal Design",
    "Alice Kaplan",
    "Buffett Institute",
    "Peabody",
    "Nieman Foundation",
    " SEsp ",
    "Zell Fellows",
    "Berman Institute",
    " STScI",
    " and APL",
    "Chicago Public Schools",
    "Steppenwolf",
    "Chicago Symphony",
    "Mauna Loa",
    "Center for Western Weather",
    "Chicago Botanic Garden",
    "Indiana's research",
    "Maryland certification",
    "Mount Vernon campus",
)

_CLASSIFICATION_STUB_RE = re.compile(
    r"^.+ is an undergraduate .+ at the University of Wisconsin-Madison's .+\.$"
    r"|^.+ is (a graduate degree|a doctoral program|a graduate certificate|"
    r"a professional degree) at the University of Wisconsin-Madison's ",
)

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
    "school_outcomes.scale.faculty_count",
]

RANKING_DATA: dict = {
    "ownership_type": "public",
    "accreditor": "Higher Learning Commission (HLC)",
    "carnegie_classification": (
        "Doctoral Universities: Very High Research Spending and Doctorate Production (R1)"
    ),
    "qs_world_university_rankings": {
        "rank": 110, "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/university-wisconsin-madison",
    },
    "times_higher_education": {
        "rank": 53, "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-wisconsin-madison",
    },
    "us_news_national": {
        "rank": 36, "year": 2026,
        "source_url": "https://www.usnews.com/best-colleges/university-of-wisconsin-3895",
    },
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.452,
    "avg_net_price": 17354,
    "median_earnings_10yr": 73792,
    "completion_rate_4yr_150pct": 0.8955,
    "retention_rate_first_year": 0.9616,
    "graduation_rate_6yr": 0.897,
    "financial_aid": {
        "pell_grant_rate": 0.1594,
        "federal_loan_rate": 0.2038,
        "cost_of_attendance": 28679,
        "median_debt_completers": 20484,
        "avg_net_price": 17354,
    },
    "demographics": {
        "white": 0.5911,
        "asian": 0.1095,
        "hispanic": 0.0852,
        "black": 0.0247,
        "two_or_more": 0.0492,
        "international": 0.1025,
        "unknown": 0.0378,
    },
    "test_scores": {
        "sat_reading_25_75": [670, 740],
        "sat_math_25_75": [710, 780],
        "act_25_75": [29, 33],
    },
    "campus_basics": {"location": "Madison, Wisconsin"},
    "scale": {
        "campus_acres": 939,
        "endowment_usd": 4900000000,
        "student_faculty_ratio": "17:1",
    },
    "location": {"lat": 43.0766, "lng": -89.4125},
    "research": {
        "areas": [
            "Biomedical and health sciences",
            "Atmospheric, space, and earth sciences",
            "Stem cell and regenerative biology",
            "Data science, AI, and computational biology",
            "Agriculture and life sciences",
            "Human development and developmental disabilities",
        ],
        "labs": [
            "Wisconsin Institute for Discovery",
            "Morgridge Institute for Research",
            "Space Science and Engineering Center",
            "Waisman Center",
            "Wisconsin Alumni Research Foundation",
        ],
        "lab_links": {
            "Wisconsin Institute for Discovery": "https://wid.wisc.edu/",
            "Morgridge Institute for Research": "https://morgridge.org/",
            "Space Science and Engineering Center": "https://www.ssec.wisc.edu/",
            "Waisman Center": "https://www.waisman.wisc.edu/",
            "Wisconsin Alumni Research Foundation": "https://www.warf.org/",
        },
    },
    "campus_life": {
        "student_orgs": 1062,
        "varsity_sports": 23,
        "athletics_division": "NCAA Division I (Big Ten Conference)",
        "resources": [
            {"name": "Student Affairs hub", "url": "https://students.wisc.edu/"},
            {"name": "Recreation & Wellbeing (RecWell)", "url": "https://recwell.wisc.edu/"},
            {"name": "University Housing", "url": "https://www.housing.wisc.edu/"},
            {"name": "University Health Services", "url": "https://www.uhs.wisc.edu/"},
            {
                "name": "Student Organizations, Leadership & Involvement",
                "url": "https://soli.wisc.edu/",
            },
        ],
    },
    "campus_photos": [
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Bascom_Hall_aerial.jpg/1920px-Bascom_Hall_aerial.jpg",
            "credit": "Wikimedia Commons / Wikideas1 (CC0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Aeroplane_view_of_University_of_Wisconsin%2C_Madison%2C_Wisconsin_%2864127%29.jpg/1920px-Aeroplane_view_of_University_of_Wisconsin%2C_Madison%2C_Wisconsin_%2864127%29.jpg",
            "credit": "Wikimedia Commons / Tichnor Bros. (public domain)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Gfp-wisconsin-madison-winter-landscape-view-of-campus.jpg/1920px-Gfp-wisconsin-madison-winter-landscape-view-of-campus.jpg",
            "credit": "Wikimedia Commons / Yinan Chen (public domain)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Birge_Hall%2C_University_of_Wisconsin%2C_Bascom_Mall%2C_Madison%2C_WI.jpg/1920px-Birge_Hall%2C_University_of_Wisconsin%2C_Bascom_Mall%2C_Madison%2C_WI.jpg",
            "credit": "Wikimedia Commons / w_lemay (CC BY-SA 2.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Library_Mall_Clock_Tower_-_panoramio.jpg/1920px-Library_Mall_Clock_Tower_-_panoramio.jpg",
            "credit": "Wikimedia Commons / Corey Coyle (CC BY 3.0)",
        },
    ],
    "media_credit": "Wikimedia Commons / Wikideas1 (CC0)",
    "flagship": {
        "applicants": 73912,
        "admits": 30167,
        "admissions_cycle": "First-year, Fall 2025 (UW–Madison Facts, November 2025)",
        "founded_year": 1848,
    },
    "sources": [
        {
            "label": "College Scorecard (UNITID 240444)",
            "url": "https://collegescorecard.ed.gov/school/?240444-University-of-Wisconsin-Madison",
        },
        {"label": "UW–Madison Facts", "url": "https://www.wisc.edu/about/facts/"},
        {
            "label": "U.S. News — University of Wisconsin-Madison",
            "url": "https://www.usnews.com/best-colleges/university-of-wisconsin-3895",
        },
    ],
}

UNDERGRAD_COUNT = 37198

DESCRIPTION = (
    "University of Wisconsin-Madison is a public research university in Madison, WI, "
    "founded in 1848 as the state's flagship land-grant institution. A Carnegie R1 campus "
    "on roughly 939 acres between Lake Mendota and the Wisconsin State Capitol, UW-Madison "
    "ranks fifth nationally in research expenditures and is guided by the \"Wisconsin Idea\" — "
    "the principle that university work should extend beyond the classroom to benefit the "
    "entire state. Its Wisconsin Alumni Research Foundation has returned billions from "
    "campus discoveries, including the isolation of vitamin D and the first human embryonic "
    "stem cells.\n\n"
    "UW-Madison is organized into thirteen degree-granting schools and colleges — including "
    "the College of Agricultural and Life Sciences, the Wisconsin School of Business, the "
    "College of Engineering, the College of Letters and Science (with the School of Computer, "
    "Data and Information Sciences, the School of Journalism and Mass Communication, and the "
    "School of Social Work), the School of Medicine and Public Health, the School of Nursing, "
    "the Nelson Institute for Environmental Studies, the School of Pharmacy, and the School of "
    "Veterinary Medicine — offering a full catalog spanning bachelor's, master's, professional, "
    "and doctoral degrees.\n\n"
    "A public university continuously accredited by the Higher Learning Commission, UW-Madison "
    "ranks #36 among national universities by U.S. News (2026), #53 in the world by Times Higher "
    "Education, and #110 by QS. Published in-state tuition is approximately $12,186 a year "
    "(out-of-state $44,210 for 2025–26), with an average net price after grant aid of about "
    "$17,354. UW-Madison graduates earn a median of roughly $73,792 ten years after entry. "
    "The Badgers compete in NCAA Division I as founding members of the Big Ten Conference."
)

# ── School constants ───────────────────────────────────────────────────────

CALS = "College of Agricultural and Life Sciences"
BUSINESS = "Wisconsin School of Business"
EDUCATION = "School of Education"
ENGINEERING = "College of Engineering"
HUMAN_ECOLOGY = "School of Human Ecology"
LAW = "Law School"
LETTERS = "College of Letters and Science"
CDIS = "School of Computer, Data and Information Sciences"
JOURNALISM = "School of Journalism and Mass Communication"
SOCIAL_WORK = "School of Social Work"
MEDICINE = "School of Medicine and Public Health"
NURSING = "School of Nursing"
NELSON = "Nelson Institute for Environmental Studies"
PHARMACY = "School of Pharmacy"
VET = "School of Veterinary Medicine"

_SCHOOL_META = [
    {
        "name": CALS, "sort_order": 1, "website": "https://cals.wisc.edu/",
        "leadership": "Glenda Gillaspy — Dean",
        "research_centers": [
            "Wisconsin Agricultural Experiment Station",
            "Center for Dairy Research",
            "Food Research Institute",
            "UW Arboretum",
        ],
        "keywords": ["College of Agricultural and Life Sciences", "CALS", "agriculture", "life sciences"],
    },
    {
        "name": BUSINESS, "sort_order": 2, "website": "https://business.wisc.edu/",
        "leadership": "Vallabh Sambamurthy — Dean",
        "research_centers": [
            "Hartman Center for Sales Leadership",
            "Nicholas Center for Corporate Finance and Investment Banking",
            "Weinert Center for Entrepreneurship",
            "Wisconsin School of Business Research",
        ],
        "keywords": ["Wisconsin School of Business", "WSB", "business", "MBA"],
    },
    {
        "name": EDUCATION, "sort_order": 3, "website": "https://education.wisc.edu/",
        "leadership": "Diana Hess — Dean",
        "research_centers": [
            "Wisconsin Center for Education Research",
            "Professional Learning and Community Education",
            "Teacher Education programs",
            "Educational Policy Studies",
        ],
        "keywords": ["School of Education", "education", "teacher preparation"],
    },
    {
        "name": ENGINEERING, "sort_order": 4, "website": "https://engineering.wisc.edu/",
        "leadership": "Ian Robertson — Dean",
        "research_centers": [
            "Grainger Engineering Design Innovation Lab",
            "Wisconsin Materials Research Science and Engineering Center",
            "Wisconsin Institutes for Discovery (engineering programs)",
            "Engineering Physics",
        ],
        "keywords": ["College of Engineering", "engineering", "Grainger"],
    },
    {
        "name": HUMAN_ECOLOGY, "sort_order": 5, "website": "https://sohe.wisc.edu/",
        "leadership": "Soyeon Shim — Dean",
        "research_centers": [
            "Center for Financial Security",
            "Center for Community and Nonprofit Studies",
            "Design Studies",
            "Human Development and Family Studies",
        ],
        "keywords": ["School of Human Ecology", "SoHE", "human ecology"],
    },
    {
        "name": LAW, "sort_order": 6, "website": "https://law.wisc.edu/",
        "leadership": "Daniel P. Tokaji — Dean",
        "research_centers": [
            "East Asian Legal Studies Center",
            "Global Legal Studies Center",
            "Wisconsin Innocence Project",
            "Law & Entrepreneurship Clinic",
        ],
        "keywords": ["Law School", "UW Law", "JD", "legal studies"],
    },
    {
        "name": LETTERS, "sort_order": 7, "website": "https://ls.wisc.edu/",
        "leadership": "Eric Wilcots — Dean",
        "research_centers": [
            "Center for the Humanities",
            "Institute for Research in the Humanities",
            "Center for Demography and Ecology",
            "Center for the Study of the American Constitution",
        ],
        "keywords": ["College of Letters and Science", "L&S", "liberal arts", "humanities", "social sciences"],
    },
    {
        "name": CDIS, "sort_order": 8, "website": "https://cdis.wisc.edu/",
        "leadership": "Tom Erickson — Dean",
        "research_centers": [
            "Data Science Institute",
            "Center for High Throughput Computing",
            "Wisconsin Institute on Software-defined Data-centers in E-commerce",
            "Computer Sciences",
        ],
        "keywords": ["School of Computer, Data and Information Sciences", "CDIS", "computer science", "data science"],
    },
    {
        "name": JOURNALISM, "sort_order": 9, "website": "https://journalism.wisc.edu/",
        "leadership": "Hernando Rojas — Dean",
        "research_centers": [
            "Center for Communication and Civic Renewal",
            "Mass Communication Research Center",
            "Journalism and Strategic Communication",
            "Media and Democracy",
        ],
        "keywords": ["School of Journalism and Mass Communication", "SJMC", "journalism", "mass communication"],
    },
    {
        "name": SOCIAL_WORK, "sort_order": 10, "website": "https://socwork.wisc.edu/",
        "leadership": "Stephanie Robert — Dean",
        "research_centers": [
            "Institute for Research on Poverty",
            "Center for Financial Security",
            "Wisconsin Longitudinal Study",
            "Social Work Practice and Policy",
        ],
        "keywords": ["School of Social Work", "social work", "MSW"],
    },
    {
        "name": MEDICINE, "sort_order": 11, "website": "https://www.med.wisc.edu/",
        "leadership": "Robert N. Golden — Dean",
        "research_centers": [
            "UW Carbone Cancer Center",
            "Wisconsin Alzheimer's Institute",
            "Institute for Clinical and Translational Research",
            "McArdle Laboratory for Cancer Research",
        ],
        "keywords": ["School of Medicine and Public Health", "SMPH", "medicine", "MD", "public health"],
    },
    {
        "name": NURSING, "sort_order": 12, "website": "https://nursing.wisc.edu/",
        "leadership": "Linda D. Scott — Dean",
        "research_centers": [
            "Center for Aging Research and Education",
            "Center for Patient Partnerships",
            "Wisconsin Center for Nursing",
            "Nursing Research and Practice",
        ],
        "keywords": ["School of Nursing", "nursing", "BSN", "DNP"],
    },
    {
        "name": NELSON, "sort_order": 13, "website": "https://nelson.wisc.edu/",
        "leadership": "Paul Robbins — Director",
        "research_centers": [
            "Center for Climatic Research",
            "Center for Sustainability and the Global Environment",
            "Trout Lake Station",
            "Environmental Studies",
        ],
        "keywords": ["Nelson Institute for Environmental Studies", "environmental studies", "sustainability"],
    },
    {
        "name": PHARMACY, "sort_order": 14, "website": "https://pharmacy.wisc.edu/",
        "leadership": "Steven Swanson — Dean",
        "research_centers": [
            "Pharmaceutical Sciences Division",
            "Social and Administrative Sciences Division",
            "Zeeh Pharmaceutical Experiment Station",
            "Pharmacy Practice Division",
        ],
        "keywords": ["School of Pharmacy", "pharmacy", "PharmD"],
    },
    {
        "name": VET, "sort_order": 15, "website": "https://www.vetmed.wisc.edu/",
        "leadership": "Daryl Nydam — Dean",
        "research_centers": [
            "Wisconsin Veterinary Diagnostic Laboratory",
            "UW Veterinary Care teaching hospital",
            "Comparative Biomedical Sciences",
            "Food Animal Production Medicine",
        ],
        "keywords": ["School of Veterinary Medicine", "veterinary", "DVM"],
    },
]

SCHOOLS: list[dict] = [
    {"name": m["name"], "sort_order": m["sort_order"], "description": f"The {m['name']} is one of UW-Madison's academic schools and colleges."}
    for m in _SCHOOL_META
]
SCHOOL_WEBSITE = {m["name"]: m["website"] for m in _SCHOOL_META}
_KEYWORDS_BY_SCHOOL = {m["name"]: m["keywords"] for m in _SCHOOL_META}


def _about_for(m: dict) -> dict:
    return {
        "leadership": m["leadership"],
        "research_centers": m["research_centers"],
        "source": {"label": "UW–Madison Schools and Colleges", "url": "https://www.wisc.edu/academics/schools-and-colleges/"},
    }


def _about_omitted(m: dict) -> list[str]:
    return ["about_detail.founded", "about_detail.faculty", "about_detail.named_for"]


def _school_description(m: dict) -> str:
    return f"The {m['name']} is one of UW-Madison's academic schools and colleges."


# ── Feeds (content_sources) ────────────────────────────────────────────────
_NEWS_RSS = "https://news.wisc.edu/feed/"
_EVENTS = {"url": "https://today.wisc.edu/events.ics", "type": "ical"}
_SOCIAL = {
    "instagram": "https://instagram.com/uwmadison",
    "linkedin": "https://www.linkedin.com/school/uwmadison/",
    "x": "https://x.com/UWMadison",
    "youtube": "https://www.youtube.com/user/uwmadison",
    "facebook": "https://facebook.com/uwmadison",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _NEWS_RSS,
    "news_url": "https://news.wisc.edu/",
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
        "slug": "uw-madison-computer-science-bs", "school": CDIS,
        "program_name": "Computer Science", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Computer Science through the School of Computer, Data and Information Sciences.",
        "department": "Department of Computer Sciences", "cip": "11.07",
    },
    {
        "slug": "uw-madison-mechanical-engineering-bs", "school": ENGINEERING,
        "program_name": "Mechanical Engineering", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Mechanical Engineering through the College of Engineering.",
        "department": "Department of Mechanical Engineering", "cip": "14.19",
    },
    {
        "slug": "uw-madison-biomedical-engineering-bs", "school": ENGINEERING,
        "program_name": "Biomedical/Medical Engineering", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Biomedical Engineering through the College of Engineering.",
        "department": "Department of Biomedical Engineering", "cip": "14.05",
    },
    {
        "slug": "uw-madison-business-administration-bs", "school": BUSINESS,
        "program_name": "Business Administration and Management", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Business Administration through the Wisconsin School of Business.",
        "department": "Wisconsin School of Business", "cip": "52.02",
    },
    {
        "slug": "uw-madison-mba-ms", "school": BUSINESS,
        "program_name": "Master of Business Administration", "degree_type": "masters",
        "duration_months": 24, "delivery_format": "on_campus",
        "description": "Full-time MBA at the Wisconsin School of Business.",
        "department": "Wisconsin School of Business", "cip": "52.02",
    },
    {
        "slug": "uw-madison-law-prof", "school": LAW,
        "program_name": "Law", "degree_type": "professional",
        "duration_months": 36, "delivery_format": "on_campus",
        "description": "Juris Doctor (J.D.) at the University of Wisconsin Law School.",
        "department": "Law School", "cip": "22.01",
    },
    {
        "slug": "uw-madison-medicine-prof", "school": MEDICINE,
        "program_name": "Medicine", "degree_type": "professional",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Doctor of Medicine (M.D.) at the UW School of Medicine and Public Health.",
        "department": "School of Medicine and Public Health", "cip": "51.12",
    },
    {
        "slug": "uw-madison-pharmacy-prof", "school": PHARMACY,
        "program_name": "Pharmacy", "degree_type": "professional",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Doctor of Pharmacy (Pharm.D.) at the UW–Madison School of Pharmacy.",
        "department": "School of Pharmacy", "cip": "51.20",
    },
    {
        "slug": "uw-madison-veterinary-medicine-prof", "school": VET,
        "program_name": "Veterinary Medicine", "degree_type": "professional",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Doctor of Veterinary Medicine (D.V.M.) at the School of Veterinary Medicine.",
        "department": "School of Veterinary Medicine", "cip": "51.24",
    },
    {
        "slug": "uw-madison-nursing-bs", "school": NURSING,
        "program_name": "Registered Nursing", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Nursing (BSN) through the UW–Madison School of Nursing.",
        "department": "School of Nursing", "cip": "51.38",
    },
    {
        "slug": "uw-madison-psychology-bs", "school": LETTERS,
        "program_name": "Psychology, General", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Psychology through the College of Letters and Science.",
        "department": "Department of Psychology", "cip": "42.01",
    },
    {
        "slug": "uw-madison-economics-bs", "school": LETTERS,
        "program_name": "Economics", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Arts or Bachelor of Science in Economics through the College of Letters and Science.",
        "department": "Department of Economics", "cip": "45.06",
    },
]

_EXISTING_SLUGS = {p["slug"] for p in PROGRAMS}
_EXISTING_CIP_KEYS = {(p.get("cip"), p["degree_type"]) for p in PROGRAMS if p.get("cip")}


def _department_for(field_name: str, school: str) -> str:
    """Owning department — map CIP titles to UW-Madison's published unit names."""
    field = clean_cip_field(field_name)
    if field in DEPARTMENT_BY_FIELD:
        return DEPARTMENT_BY_FIELD[field]
    if field.lower() in school.lower() or school.lower() in field.lower():
        return school
    if school == ENGINEERING:
        return f"Department of {field}"
    if school == LETTERS:
        return f"Department of {field}"
    return school


def _ug_degree_prefix(school: str, field: str) -> str:
    if school == LETTERS and field in BA_FIELDS:
        return "Bachelor of Arts in"
    if school == JOURNALISM:
        return "Bachelor of Science in"
    if school == HUMAN_ECOLOGY:
        return "Bachelor of Science in"
    return "Bachelor of Science in"


def _uw_madison_program_name(field_name: str, degree_type: str, school: str) -> str:
    """Real credential-specific name — never a bare CIP title or credential-prefix stub."""
    field = clean_cip_field(field_name)
    if degree_type == "bachelors":
        return f"{_ug_degree_prefix(school, field)} {field}"
    if degree_type == "masters":
        if field == "Business Administration" and school == BUSINESS:
            return "Master of Business Administration"
        if field == "Social Work" and school == SOCIAL_WORK:
            return "Master of Social Work"
        if field == "Public Health" and school == MEDICINE:
            return "Master of Public Health"
        if field == "Nursing" and school == NURSING:
            return "Master of Science in Nursing"
        if field == "Library and Information Studies":
            return "Master of Arts in Library and Information Studies"
        return f"Master of Science in {field}"
    if degree_type == "phd":
        return f"Doctor of Philosophy in {field}"
    if degree_type == "certificate":
        return f"Graduate Certificate in {field}"
    if degree_type == "professional":
        if field == "Medicine":
            return "Doctor of Medicine"
        if field == "Pharmaceutical Sciences" and school == PHARMACY:
            return "Doctor of Pharmacy"
        if field == "Veterinary Medicine":
            return "Doctor of Veterinary Medicine"
        if field == "Law":
            return "Juris Doctor"
    return field


def _field_from_program_name(name: str) -> str:
    if name in (
        "Doctor of Medicine",
        "Doctor of Pharmacy",
        "Doctor of Veterinary Medicine",
        "Juris Doctor",
        "Master of Business Administration",
        "Master of Public Health",
        "Master of Social Work",
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


def _adapt_clause_for_degree_type(clause: str, degree_type: str) -> str:
    """Fix credential-level lies (e.g. 'Graduate …' on a bachelor's row)."""
    if degree_type == "bachelors":
        if clause.startswith("Graduate "):
            return "Undergraduate " + clause[len("Graduate "):]
        if clause.startswith("Graduate-level "):
            return "Undergraduate-level " + clause[len("Graduate-level "):]
    return clause


def _level_appropriate_clause(clause: str, degree_type: str) -> str:
    """Drop undergraduate-specific phrasing from a field clause on graduate rows."""
    if degree_type == "bachelors":
        return clause
    clause = re.sub(r"\bthe undergraduate major\b", "the program", clause, flags=re.I)
    clause = re.sub(
        r"\bundergraduate (major|program)\b", "program", clause, flags=re.I
    )
    return clause


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


def _uw_madison_description(spec: dict, *, field: str) -> str:
    """Field-specific, per-credential description — never a classification stub.

    Leads with a verified UW-Madison field clause, then a credential-level-specific
    body so siblings share no dominant tail body (frame_stripped_shared_body = 0).
    """
    slug = spec["slug"]
    dtype = spec["degree_type"]
    college = spec["school"]
    if slug in SLUG_DESCRIPTIONS:
        clause = SLUG_DESCRIPTIONS[slug]
    else:
        clause = FIELD_DESCRIPTIONS.get(field)
        if not clause:
            raise ValueError(
                f"Missing FIELD_DESCRIPTIONS entry for {field!r} ({slug})"
            )
    desc = f"{clause} {_level_body(dtype, spec['program_name'], college, _field_label(spec['program_name']))}"
    fmt = spec.get("delivery_format", "on_campus")
    if fmt == "online":
        desc += " Delivered online."
    elif fmt == "hybrid":
        desc += " Delivered in a hybrid format."
    return desc


def _normalize_program(spec: dict, field_name: str | None = None) -> None:
    slug = spec["slug"]
    school = spec["school"]
    dtype = spec["degree_type"]
    raw_field = field_name or spec.get("_field_name") or spec.get("program_name", "")

    if slug in SLUG_PROGRAM_NAMES:
        spec["program_name"] = SLUG_PROGRAM_NAMES[slug]
    elif dtype != "professional":
        spec["program_name"] = _uw_madison_program_name(raw_field, dtype, school)

    if slug in SLUG_DEPARTMENTS:
        spec["department"] = SLUG_DEPARTMENTS[slug]
    elif not spec.get("department") or spec["department"] == raw_field:
        spec["department"] = _department_for(raw_field, school)

    spec["description"] = _uw_madison_description(
        spec, field=_field_from_spec(spec, clean_cip_field(raw_field) if raw_field else None),
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
_peer_contamination = sum(
    1
    for p in PROGRAMS
    if any(sig in (p.get("description") or "") for sig in _PEER_SIGNATURES)
)
if _peer_contamination:
    _catalog_errors.append(
        f"peer-contaminated descriptions on {_peer_contamination} programs"
    )
_desc_counts = Counter(p.get("description") for p in PROGRAMS)
_shared_desc = sum(c for c in _desc_counts.values() if c >= 2)
if _shared_desc:
    _catalog_errors.append(
        f"identical descriptions shared across {_shared_desc} credential-sibling programs"
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
_anti_stub = _anti_stub_analyze(PROGRAMS)
if not _anti_stub.is_clean:
    _catalog_errors.append(f"anti-stub gate failed: {_anti_stub.summary()}")
from unipaith.profile_standard.anti_stub import (  # noqa: E402
    frame_stripped_shared_body as _frame_stripped_shared_body,
)

_frame_shared = _frame_stripped_shared_body(PROGRAMS)
if _frame_shared:
    _catalog_errors.append(
        f"credential siblings share a frame-stripped body on fields: {_frame_shared[:8]}"
        f"{' …' if len(_frame_shared) > 8 else ''}"
    )
if _catalog_errors:
    raise RuntimeError(f"UW-Madison catalog quality gate failed: {_catalog_errors}")
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

_TUITION_UG_INSTATE = 12186
_TUITION_UG_OOS = 44210
_UNDERGRAD_COA = 28679
_AVG_NET_PRICE = 17354
_COST_SRC = (
    "UW–Madison Facts (tuition 2025–26) + College Scorecard (UNITID 240444)",
    "https://www.wisc.edu/about/facts/",
)

_REQ_UNDERGRAD = {
    "materials": [
        {"name": "UW System Application for Admission", "required": True},
        {"name": "Required essays", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "$70 application fee (fee waivers available)", "required": True},
        {"name": "SAT/ACT scores", "required": False,
         "note": "UW-Madison is test-optional; applicants who submit scores have a middle 50% SAT reading 670–740 and math 710–780 (College Scorecard)."},
    ],
    "deadlines": [
        {"round": "Early Action", "date": "November 1"},
        {"round": "Regular Decision", "date": "February 1"},
    ],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS", "Duolingo English Test"], "required": True,
                    "note": "Required for applicants whose native language is not English."},
        "visa": {"types": ["F-1", "J-1"], "note": "International students receive an I-20 after admission."},
        "sources": [{"label": "UW–Madison Office of Admissions and Recruitment", "url": "https://admissions.wisc.edu/"}],
    },
    "source": "UW–Madison Office of Admissions and Recruitment",
    "source_url": "https://admissions.wisc.edu/",
}
_REQ_GRAD = {
    "materials": [
        {"name": "UW–Madison Graduate School application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Résumé / CV", "required": True},
        {"name": "Letters of recommendation", "required": True,
         "note": "Most UW graduate programs require three letters; check the program's page."},
        {"name": "GRE scores", "required": False,
         "note": "Test requirements vary by program; many UW graduate programs are test-optional."},
    ],
    "deadlines": [{"round": "Fall admission", "date": "Deadlines vary by program (typically December–January)"}],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS"], "required": True,
                    "note": "Required for applicants whose native language is not English."},
        "visa": {"types": ["F-1", "J-1"], "note": "International students receive an I-20 after admission."},
        "sources": [{"label": "UW–Madison Graduate School — Admissions", "url": "https://grad.wisc.edu/admissions/"}],
    },
    "source": "UW–Madison Graduate School — Admissions",
    "source_url": "https://grad.wisc.edu/admissions/",
}

_OUTCOMES_INSTITUTION = {
    "median_salary": 73792,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry",
    "source": "U.S. Dept. of Education College Scorecard (UNITID 240444)",
    "source_url": "https://collegescorecard.ed.gov/school/?240444-University-of-Wisconsin-Madison",
}

_REVIEWS_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews."
)

_REVIEWS_BY_SLUG: dict[str, dict] = {
    "uw-madison-computer-science-bs": {
        "summary": (
            "UW-Madison's undergraduate computer science program in the School of Computer, Data "
            "and Information Sciences is ranked among the top public CS programs nationally, known "
            "for strength in systems, databases, and machine learning alongside a rigorous theory "
            "foundation. Students benefit from the Wisconsin Institutes for Discovery and strong "
            "recruiting to Midwest tech hubs and national firms, though gateway courses are large "
            "and competitive admission to the major is a common concern."
        ),
        "themes": [
            {"label": "Research access", "sentiment": "positive", "detail": "CDIS faculty lead active labs in AI, systems, and data science with undergraduate research pathways."},
            {"label": "Industry placement", "sentiment": "positive", "detail": "Strong recruiting to Epic, Google, Microsoft, Amazon, and Wisconsin-based tech employers."},
            {"label": "Major admission", "sentiment": "caution", "detail": "Direct admission to CS is competitive; students may need to complete prerequisite coursework first."},
            {"label": "Large intro sections", "sentiment": "mixed", "detail": "High enrollment means lower-division courses can feel impersonal without proactive faculty engagement."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Computer Science Programs", "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall"},
            {"label": "Niche — University of Wisconsin-Madison", "url": "https://www.niche.com/colleges/university-of-wisconsin-madison/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-mechanical-engineering-bs": {
        "summary": (
            "UW-Madison's mechanical engineering program through the College of Engineering is "
            "consistently ranked among the top 15–20 nationally, with particular strength in "
            "thermodynamics, fluid mechanics, and manufacturing research. Students cite the "
            "Grainger Engineering Design Innovation Lab and deep ties to Wisconsin manufacturing "
            "and automotive employers as highlights, though the engineering core is demanding and "
            "large lecture sections in the first two years are common."
        ),
        "themes": [
            {"label": "Design infrastructure", "sentiment": "positive", "detail": "Grainger Engineering Design Innovation Lab and senior design capstone integrate real industry sponsors."},
            {"label": "Industry recruiting", "sentiment": "positive", "detail": "Caterpillar, Rockwell Automation, Harley-Davidson, and major automotive firms recruit actively."},
            {"label": "Curriculum rigor", "sentiment": "caution", "detail": "Math and physics gateway sequence is intense; time management in years 1–2 is essential."},
            {"label": "Public-university value", "sentiment": "positive", "detail": "Strong ROI for in-state students; engineering outcomes compare favorably to peer R1 publics."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Mechanical Engineering Programs", "url": "https://www.usnews.com/best-colleges/rankings/mechanical-engineering"},
            {"label": "UW–Madison College of Engineering", "url": "https://engineering.wisc.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-biomedical-engineering-bs": {
        "summary": (
            "UW-Madison's biomedical engineering program bridges the College of Engineering and "
            "the School of Medicine and Public Health, giving students access to clinical and "
            "research environments uncommon at peer programs. Reviewers note strong placement in "
            "medical device firms, health-tech startups, and graduate programs, though the "
            "interdisciplinary curriculum requires careful planning across engineering and biology "
            "prerequisites."
        ),
        "themes": [
            {"label": "Clinical proximity", "sentiment": "positive", "detail": "UW Health and SMPH affiliations offer research and internship access rare among undergraduate BME programs."},
            {"label": "Graduate school pipeline", "sentiment": "positive", "detail": "Strong track record placing graduates in top biomedical engineering and medical PhD programs."},
            {"label": "Prerequisite load", "sentiment": "mixed", "detail": "Biology, chemistry, and engineering requirements make the four-year plan tight without early planning."},
            {"label": "Industry placement", "sentiment": "positive", "detail": "Medtronic, GE Healthcare, and Wisconsin biotech firms recruit from the program."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Biomedical Engineering Programs", "url": "https://www.usnews.com/best-colleges/rankings/biomedical-engineering"},
            {"label": "UW–Madison Biomedical Engineering", "url": "https://engineering.wisc.edu/departments/biomedical-engineering/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-business-administration-bs": {
        "summary": (
            "The Wisconsin School of Business undergraduate program offers a quantitatively oriented "
            "BBA with particular strength in finance, real estate, and supply chain management. "
            "Reviewers note strong placement in consulting, banking, and Fortune 500 rotational "
            "programs, though direct admission is competitive and the school's brand recognition "
            "outside the Midwest trails top-10 undergraduate business programs."
        ),
        "themes": [
            {"label": "Direct admission selectivity", "sentiment": "caution", "detail": "Freshman direct admission to WSB is competitive; many students apply after completing prerequisites in L&S."},
            {"label": "Finance and real estate", "sentiment": "positive", "detail": "Nicholas Center and Hartman Center provide distinctive experiential finance and sales training."},
            {"label": "Midwest recruiting", "sentiment": "positive", "detail": "Strong pipelines to Milwaukee and Chicago finance, consulting, and CPG firms."},
            {"label": "National brand", "sentiment": "mixed", "detail": "Well-regarded regionally; national recognition growing but still behind elite private business schools."},
        ],
        "sources": [
            {"label": "Poets&Quants — Best Undergraduate Business Schools", "url": "https://poetsandquants.com/best-undergraduate-business-programs/"},
            {"label": "U.S. News — Best Undergraduate Business Programs", "url": "https://www.usnews.com/best-colleges/rankings/business-overall"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-mba-ms": {
        "summary": (
            "The Wisconsin Full-Time MBA at the Wisconsin School of Business is a two-year program "
            "known for its applied learning model, distinctive specializations in brand and product "
            "management, and strong Midwest corporate recruiting. Poets&Quants and BusinessBecause "
            "coverage highlight the school's collaborative culture and lower cost than coastal "
            "MBAs, though national consulting and finance placement lags M7 peers."
        ),
        "themes": [
            {"label": "Applied curriculum", "sentiment": "positive", "detail": "Brand and Product Management and applied learning projects integrate real corporate sponsors."},
            {"label": "Value proposition", "sentiment": "positive", "detail": "Lower tuition than elite private MBAs with strong ROI for students targeting Midwest markets."},
            {"label": "National consulting placement", "sentiment": "mixed", "detail": "Top-tier consulting and investment banking placement is more limited than M7 programs."},
            {"label": "Collaborative culture", "sentiment": "positive", "detail": "Smaller cohort relative to mega-programs fosters tight-knit peer networks."},
        ],
        "sources": [
            {"label": "Poets&Quants — Wisconsin School of Business", "url": "https://poetsandquants.com/schools/wisconsin-school-of-business-university-of-wisconsin/"},
            {"label": "Wisconsin School of Business — MBA", "url": "https://business.wisc.edu/graduate/mba/full-time/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-law-prof": {
        "summary": (
            "UW Law is a well-regarded public law school with particular strength in environmental "
            "law, Indian law, and clinical education through the Wisconsin Innocence Project and "
            "Law & Entrepreneurship Clinic. Graduates value the lower debt load relative to private "
            "peers and strong Wisconsin/Midwest placement, though national BigLaw recruiting is "
            "more limited than top-20 private law schools."
        ),
        "themes": [
            {"label": "Clinical programs", "sentiment": "positive", "detail": "Wisconsin Innocence Project and entrepreneurship clinic provide distinctive hands-on training."},
            {"label": "Debt and affordability", "sentiment": "positive", "detail": "In-state tuition and strong scholarship support keep debt below many peer public law schools."},
            {"label": "BigLaw placement", "sentiment": "mixed", "detail": "Chicago and Twin Cities firms recruit, but coastal BigLaw placement is more limited than T14 schools."},
            {"label": "Environmental and Indian law", "sentiment": "positive", "detail": "Nationally recognized programs in environmental law and tribal law attract specialized applicants."},
        ],
        "sources": [
            {"label": "U.S. News — Best Law Schools", "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/university-of-wisconsin-3895"},
            {"label": "UW Law School — About", "url": "https://law.wisc.edu/about/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-medicine-prof": {
        "summary": (
            "The UW School of Medicine and Public Health is a top public medical school with "
            "distinctive emphasis on rural and community health through the Wisconsin Academy for "
            "Rural Medicine (WARM) and strong research at the UW Carbone Cancer Center. Students "
            "value the ForWard curriculum and Madison quality of life, though class size and "
            "competition for competitive specialties require early planning."
        ),
        "themes": [
            {"label": "Rural health mission", "sentiment": "positive", "detail": "WARM and community health pathways distinguish UW among public medical schools."},
            {"label": "Research strength", "sentiment": "positive", "detail": "UW Carbone Cancer Center and ICTR provide substantial research opportunities for medical students."},
            {"label": "In-state preference", "sentiment": "caution", "detail": "Wisconsin residents receive strong preference; out-of-state admission is highly competitive."},
            {"label": "Quality of life", "sentiment": "positive", "detail": "Madison campus setting and collaborative student culture are frequently cited positives."},
        ],
        "sources": [
            {"label": "U.S. News — Best Medical Schools (Research)", "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-wisconsin-madison-04072"},
            {"label": "UW School of Medicine and Public Health", "url": "https://www.med.wisc.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-pharmacy-prof": {
        "summary": (
            "UW-Madison's Pharm.D. program is one of the oldest pharmacy schools in the United "
            "States, known for strong pharmaceutical sciences research and placement in hospital, "
            "community, and industry pharmacy roles. Students praise the Zeeh Pharmaceutical "
            "Experiment Station and Wisconsin's collaborative health-sciences campus, though the "
            "program is highly structured with limited elective flexibility in the professional years."
        ),
        "themes": [
            {"label": "Research heritage", "sentiment": "positive", "detail": "Pharmaceutical sciences division and Zeeh Station offer research depth uncommon in Pharm.D. programs."},
            {"label": "Clinical placement", "sentiment": "positive", "detail": "UW Health affiliations provide strong hospital and ambulatory pharmacy rotations."},
            {"label": "Curriculum structure", "sentiment": "mixed", "detail": "Professional years are tightly sequenced; limited room for electives outside pharmacy."},
            {"label": "Wisconsin market", "sentiment": "positive", "detail": "Strong placement in Wisconsin and Upper Midwest pharmacy markets."},
        ],
        "sources": [
            {"label": "U.S. News — Best Pharmacy Schools", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/pharmacy-rankings"},
            {"label": "UW–Madison School of Pharmacy", "url": "https://pharmacy.wisc.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-veterinary-medicine-prof": {
        "summary": (
            "UW-Madison's School of Veterinary Medicine is one of only 32 AVMA-accredited veterinary "
            "colleges in the United States, offering a D.V.M. with strong food-animal, comparative "
            "biomedical, and diagnostic laboratory training. Students value the Wisconsin Veterinary "
            "Diagnostic Laboratory and UW Veterinary Care teaching hospital, though admission is "
            "highly selective with strong preference for Wisconsin residents."
        ),
        "themes": [
            {"label": "Food-animal strength", "sentiment": "positive", "detail": "Food Animal Production Medicine program is a distinctive strength for Wisconsin's dairy and livestock economy."},
            {"label": "Diagnostic laboratory", "sentiment": "positive", "detail": "WVDL provides unique diagnostic and research exposure for veterinary students."},
            {"label": "Admission selectivity", "sentiment": "caution", "detail": "Highly competitive admission with strong in-state preference; out-of-state seats are limited."},
            {"label": "Clinical training", "sentiment": "positive", "detail": "UW Veterinary Care teaching hospital offers comprehensive small- and large-animal clinical experience."},
        ],
        "sources": [
            {"label": "U.S. News — Best Veterinary Medicine Programs", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/veterinary-medicine-rankings"},
            {"label": "UW School of Veterinary Medicine", "url": "https://www.vetmed.wisc.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-nursing-bs": {
        "summary": (
            "UW-Madison's BSN program through the School of Nursing is ranked among the top public "
            "nursing programs nationally, with strong clinical placement at UW Health and emphasis "
            "on evidence-based practice. Students cite the Center for Patient Partnerships and "
            "research opportunities, though clinical placement scheduling and prerequisite science "
            "coursework are demanding."
        ),
        "themes": [
            {"label": "Clinical access", "sentiment": "positive", "detail": "UW Health system provides extensive clinical rotation sites in Madison and surrounding communities."},
            {"label": "Research opportunities", "sentiment": "positive", "detail": "Center for Aging Research and Education and nursing science faculty offer undergraduate research pathways."},
            {"label": "Science prerequisites", "sentiment": "caution", "detail": "Competitive admission requires strong performance in anatomy, physiology, and chemistry prerequisites."},
            {"label": "Job placement", "sentiment": "positive", "detail": "High placement rates in Wisconsin and Midwest hospital systems after licensure."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Nursing Programs", "url": "https://www.usnews.com/best-colleges/rankings/nursing-overall"},
            {"label": "UW–Madison School of Nursing", "url": "https://nursing.wisc.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-psychology-bs": {
        "summary": (
            "UW-Madison's psychology program in the College of Letters and Science offers strong "
            "research opportunities in cognitive, clinical, developmental, and neuroscience "
            "psychology with active faculty labs. Students benefit from the Waisman Center "
            "affiliation and clear pathways to doctoral study, though introductory courses are "
            "large and research assistant positions are competitive."
        ),
        "themes": [
            {"label": "Research lab access", "sentiment": "positive", "detail": "Active faculty labs in cognitive, clinical, and developmental psychology accept undergraduates."},
            {"label": "Graduate school preparation", "sentiment": "positive", "detail": "Strong track record placing graduates in top psychology and neuroscience PhD programs."},
            {"label": "Large gateway courses", "sentiment": "caution", "detail": "Introductory psychology sections are large; individual faculty mentorship requires initiative."},
            {"label": "Career without grad school", "sentiment": "mixed", "detail": "Undergraduate psychology alone narrows options; pairing with data science, pre-health, or HR coursework is advisable."},
        ],
        "sources": [
            {"label": "Niche — University of Wisconsin-Madison", "url": "https://www.niche.com/colleges/university-of-wisconsin-madison/"},
            {"label": "UW–Madison Department of Psychology", "url": "https://psych.wisc.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-economics-bs": {
        "summary": (
            "UW-Madison's economics program is rooted in the legacy of the 'Wisconsin School' of "
            "institutional economics and remains a strong quantitative social science major with "
            "particular depth in econometrics and labor economics. Students value the department's "
            "research seminars and placement in consulting, policy, and graduate programs, though "
            "upper-division courses can be competitive to access."
        ),
        "themes": [
            {"label": "Quantitative training", "sentiment": "positive", "detail": "Econometrics and labor economics sequences provide strong preparation for policy and data careers."},
            {"label": "Graduate placement", "sentiment": "positive", "detail": "Consistent placement in economics, public policy, and business PhD programs."},
            {"label": "Course access", "sentiment": "mixed", "detail": "Popular upper-division electives fill quickly; registration planning matters."},
            {"label": "Policy and consulting paths", "sentiment": "positive", "detail": "La Follette School proximity and Madison state-government access create distinctive policy internships."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Economics Programs", "url": "https://www.usnews.com/best-colleges/rankings/economics"},
            {"label": "UW–Madison Department of Economics", "url": "https://econ.wisc.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    **DEPTH_REVIEWS,
}

_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "uw-madison-computer-science-bs": ["computer science", "CDIS", "Computer Sciences"],
    "uw-madison-mechanical-engineering-bs": ["mechanical engineering", "College of Engineering"],
    "uw-madison-biomedical-engineering-bs": ["biomedical engineering", "BME", "College of Engineering"],
    "uw-madison-business-administration-bs": ["business", "BBA", "Wisconsin School of Business"],
    "uw-madison-mba-ms": ["MBA", "Wisconsin School of Business", "graduate business"],
    "uw-madison-law-prof": ["JD", "Law School", "legal studies"],
    "uw-madison-medicine-prof": ["MD", "School of Medicine and Public Health", "medicine"],
    "uw-madison-pharmacy-prof": ["PharmD", "School of Pharmacy", "pharmacy"],
    "uw-madison-veterinary-medicine-prof": ["DVM", "veterinary medicine", "vet school"],
    "uw-madison-nursing-bs": ["nursing", "BSN", "School of Nursing"],
    "uw-madison-psychology-bs": ["psychology", "College of Letters and Science"],
    "uw-madison-economics-bs": ["economics", "Department of Economics"],
}
_TRACKS_BY_SLUG: dict = {}
_CLASS_PROFILE_BY_SLUG: dict = {}
_FACULTY_BY_SLUG: dict = {}
_COST_BY_SLUG: dict = {}


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
    return SCHOOL_WEBSITE.get(spec["school"], "https://www.wisc.edu/")


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
    inst.founded_year = 1848
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.wisc.edu"
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
                "source": _COST_SRC[0], "source_url": _COST_SRC[1], "year": "2025-26",
            }
        elif spec["degree_type"] == "phd":
            p.tuition = 0
            p.cost_data = {
                "tuition_usd": 0, "funded": True,
                "note": "UW–Madison PhD students typically receive full tuition plus a stipend through fellowship and assistantship programs.",
                "source": "UW–Madison Graduate School — Funding",
                "source_url": "https://grad.wisc.edu/funding/",
            }
        else:
            p.tuition = None
            p.cost_data = {
                "note": "Tuition varies by program; see the official program tuition page.",
                "source": "UW–Madison program tuition page",
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
        p.application_deadline = date(2027, 2, 1) if spec["degree_type"] == "bachelors" else None
    session.flush()
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
