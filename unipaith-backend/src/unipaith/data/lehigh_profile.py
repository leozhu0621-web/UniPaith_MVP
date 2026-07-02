"""Lehigh University - gold-standard profile data (institution + schools + program catalog).

Mirrors the MIT / LMU reference instance: every value is researched from an authoritative
source and carries a citation, or is honestly omitted (recorded in that node's
``_standard.omitted``) - never guessed. Built 2026-07-02 from:

  * U.S. Dept. of Education **College Scorecard** API + **IPEDS** (UNITID 213543): admit rate,
    average net price, cost of attendance, ten-year median earnings, six-year completion,
    first-year retention, Pell/loan rates, median debt, and undergraduate race/ethnicity.
  * The official **Lehigh University Catalog** (catalog.lehigh.edu) and the five colleges for the
    real degree names, owning departments, and per-program field descriptions across the College
    of Arts and Sciences, the P.C. Rossin College of Engineering and Applied Science, the College
    of Business, the College of Education, and the College of Health.
  * The **Lehigh Common Data Set 2024-25** (data.lehigh.edu): applicants/admits/enrolled, SAT/ACT
    bands, test-optional policy, enrollment, and student-faculty ratio.
  * Rankings: **U.S. News Best Colleges 2025** (#46 National), **Carnegie R1** (Very High Research
    Activity, 2025 reclassification), and Middle States (MSCHE) accreditation, each cited.
  * The 2025-26 published undergraduate tuition ($66,810) and the FY2025-26 per-college graduate
    per-credit rates (finance/admin fee schedule), and a verified Wikimedia Commons campus gallery.

Lehigh is a private research university founded in 1865 by Asa Packer. Its graduate programs bill
per credit hour at published per-college rates (CAS/Engineering/Health $1,660, Business $1,400,
Education $660), so every master's carries its DISTINCT computed graduate tuition (rate x standard
load) - never the undergraduate sticker copied down. Research doctorates are funded (tuition waived
with a stipend) and professional/part-time doctorates bill per credit with no single published
annual figure, so doctoral tuition is honestly omitted-with-reason. External reviews are a
coverage-gated depth field left honestly omitted on this fresh build (structure-before-depth).
"""

# ruff: noqa: E501

from __future__ import annotations

import re
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Lehigh University"
ENRICHED_AT = "2026-07-02"


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


_OMITTED_INSTITUTION: list[str] = [
    # Lehigh is not placed in an authoritative QS or THE ranked table with a headline national
    # rank, so both world rankings are omitted (verify-or-omit); the U.S. News national rank shows.
    "ranking_data.qs_world_university_rankings",
    "ranking_data.times_higher_education",
    # Lehigh publishes no single university-wide employed-or-continuing-education rate or uniform
    # top-employer-industries list as a citable static figure (median earnings from Scorecard shown).
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
]

RANKING_DATA: dict = {
    "ownership_type": "private",
    "accreditor": "Middle States Commission on Higher Education (MSCHE)",
    "carnegie_classification": "Doctoral Universities: Very High Research Activity (R1)",
    # Overwrite the stale bulk-seed values (the seed shipped acceptance_rate 0.3698 and
    # graduation_rate 1.0). The institution-browse cards and the student match fallback read
    # ranking_data.acceptance_rate / graduation_rate directly, so these must carry the current,
    # cited facts (Common Data Set 2024-25 / College Scorecard), not the seed's stale numbers.
    "acceptance_rate": 0.2593,
    "graduation_rate": 0.8791,
    "us_news_national": {
        "rank": 46,
        "year": 2025,
        "source_url": "https://www.usnews.com/best-colleges/lehigh-university-3289",
    },
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.2593,
    "avg_net_price": 36931,
    "median_earnings_10yr": 105584,
    "completion_rate_4yr_150pct": 0.8791,
    "graduation_rate_6yr": 0.8791,
    "retention_rate_first_year": 0.937,
    "test_scores": {
        "sat_total_25th": 1380,
        "sat_total_75th": 1490,
        "act_composite_25th": 31,
        "act_composite_75th": 34,
        "policy": "test-optional",
        "note": (
            "SAT/ACT 25th-75th percentile ranges for enrolled first-years (Common Data Set "
            "2024-25). Lehigh adopted a test-optional policy in 2024; about 30% of enrolled "
            "students submitted an SAT and 9% an ACT."
        ),
        "source": "Lehigh Common Data Set 2024-25",
        "source_url": "https://data.lehigh.edu/common-data-set",
    },
    "financial_aid": {
        "pell_grant_rate": 0.1771,
        "federal_loan_rate": 0.3657,
        "cost_of_attendance": 86100,
        "median_debt_completers": 21960,
        "avg_net_price": 36931,
    },
    "demographics": {
        "white": 0.5966,
        "asian": 0.1077,
        "hispanic": 0.1105,
        "black": 0.0497,
        "two_or_more": 0.0437,
    },
    "campus_basics": {"location": "Bethlehem, Pennsylvania (South Mountain)"},
    "scale": {
        "total_enrollment": 7692,
        "undergraduate_enrollment": 5911,
        "campus_acres": 2350,
        "faculty_count": 599,
        "student_faculty_ratio": "10:1",
    },
    "location": {"lat": 40.6069, "lng": -75.3782},
    "research": {
        "areas": [
            "Engineering and applied science",
            "Business and economics",
            "Integrated, interdisciplinary study",
            "Materials, energy, and data systems",
            "Health and population science",
        ],
        "labs": [
            "Institute for Data, Intelligent Systems, and Computation (I-DISC)",
            "Institute for Cyber Physical Infrastructure and Energy (I-CPIE)",
            "Institute for Functional Materials and Devices (I-FMD)",
            "ATLSS Engineering Research Center",
        ],
        "lab_links": {
            "Institute for Data, Intelligent Systems, and Computation (I-DISC)": "https://idisc.lehigh.edu/",
            "Institute for Cyber Physical Infrastructure and Energy (I-CPIE)": "https://icpie.lehigh.edu/",
            "Institute for Functional Materials and Devices (I-FMD)": "https://ifmd.lehigh.edu/",
            "ATLSS Engineering Research Center": "https://www.lehigh.edu/atlss/",
        },
        "source": "Lehigh University - Research Centers and Institutes",
        "source_url": "https://www2.lehigh.edu/research/research-centers-institutes",
    },
    "campus_life": {
        "athletics_division": "NCAA Division I (Patriot League)",
        "mascot": "Mountain Hawks",
        "housing": "Residential campus on South Mountain in Bethlehem, plus the Mountaintop Campus",
        "resources": [
            {"name": "Lehigh Athletics", "url": "https://lehighsports.com/"},
            {"name": "Lehigh University Libraries", "url": "https://library.lehigh.edu/"},
            {"name": "Center for Career and Professional Development", "url": "https://careercenter.lehigh.edu/"},
        ],
    },
    # Verified Wikimedia Commons gallery (author + license confirmed; carried from the seed).
    "campus_photos": [
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Coxe_Hall.jpg/1920px-Coxe_Hall.jpg", "credit": "Wikimedia Commons / Scu ba (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Lehigh_Quad.jpg/1920px-Lehigh_Quad.jpg", "credit": "Wikimedia Commons / Joseph Giansante '76 (CC BY-SA 3.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Lehigh_University_Mountaintop_Campus.jpg/1920px-Lehigh_University_Mountaintop_Campus.jpg", "credit": "Wikimedia Commons / IR393DEME (CC BY-SA 3.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Lehigh_Price_Hall.jpg/1920px-Lehigh_Price_Hall.jpg", "credit": "Wikimedia Commons / Scu ba (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Ulrich_Student_Center_Lehigh.jpg/1920px-Ulrich_Student_Center_Lehigh.jpg", "credit": "Wikimedia Commons / Peter L Moore (CC BY-SA 3.0)"},
    ],
    "media_credit": "Wikimedia Commons / Scu ba (CC BY-SA 4.0)",
    "flagship": {"founded_year": 1865, "applicants": 20396, "admits": 5289},
    "sources": [
        {"label": "College Scorecard (UNITID 213543)", "url": "https://collegescorecard.ed.gov/school/?213543-Lehigh-University"},
        {"label": "Lehigh University - About", "url": "https://www2.lehigh.edu/about"},
        {"label": "U.S. News - Lehigh University (#46 National, 2025)", "url": "https://www.usnews.com/best-colleges/lehigh-university-3289"},
        {"label": "Lehigh Common Data Set 2024-25", "url": "https://data.lehigh.edu/common-data-set"},
    ],
}

UNDERGRAD_COUNT = 5911

DESCRIPTION = (
    "Lehigh University is a private research university in Bethlehem, Pennsylvania, founded in "
    "1865 by railroad magnate Asa Packer, whose gift established the school on the northern slope "
    "of South Mountain. Classified in 2025 as a Carnegie R1 \"very high research activity\" "
    "institution, Lehigh is known for its integrated, interdisciplinary approach across five "
    "colleges, where students routinely combine engineering, business, and the arts and sciences.\n\n"
    "Lehigh is organized into the College of Arts and Sciences, the P.C. Rossin College of "
    "Engineering and Applied Science, the College of Business, the College of Education, and the "
    "College of Health. Its roughly 2,350-acre campus spans three contiguous sections, including "
    "the Mountaintop Campus, a former Bethlehem Steel research site reborn as a hub for hands-on, "
    "collaborative projects.\n\n"
    "Lehigh enrolls about 5,900 undergraduates and roughly 7,700 students overall at a 10:1 "
    "student-faculty ratio, and ranks #46 among national universities by U.S. News (2025). Its "
    "published 2025-26 undergraduate tuition is $66,810, with an average net price of about "
    "$36,900 after aid; Lehigh graduates earn a median of about $105,600 ten years after entry, "
    "and it admits roughly 26% of applicants.\n\n"
    "The Mountain Hawks compete in NCAA Division I in the Patriot League, and Lehigh's engineering "
    "and business strengths anchor its national reputation."
)

# ── The real degree-granting colleges (display order) ──────────────────────
_CAS = "College of Arts and Sciences"
_ENG = "P.C. Rossin College of Engineering and Applied Science"
_BUS = "College of Business"
_EDU = "College of Education"
_HLTH = "College of Health"

_SCHOOL_WEBSITE: dict[str, str] = {
    _CAS: "https://cas.lehigh.edu/",
    _ENG: "https://engineering.lehigh.edu/",
    _BUS: "https://business.lehigh.edu/",
    _EDU: "https://ed.lehigh.edu/",
    _HLTH: "https://health.lehigh.edu/",
}

SCHOOLS: list[dict] = [
    {"name": _CAS, "sort_order": 1,
     "description": "The College of Arts and Sciences is Lehigh's largest college, teaching the humanities, social sciences, natural sciences, and mathematics and awarding B.A., B.S., M.A., M.S., and Ph.D. degrees across dozens of departments."},
    {"name": _ENG, "sort_order": 2,
     "description": "The P.C. Rossin College of Engineering and Applied Science spans eight core engineering departments plus interdisciplinary programs, conferring the B.S., the M.S. and professional M.Eng., and the Ph.D. in engineering and applied science."},
    {"name": _BUS, "sort_order": 3,
     "description": "The College of Business offers the AACSB-accredited Bachelor of Science in Business and Economics, the MBA in one-year, FLEX, and Executive formats, specialized business master's, and the Ph.D. in Business and Economics."},
    {"name": _EDU, "sort_order": 4,
     "description": "The College of Education prepares counselors, teachers, school psychologists, and educational leaders, awarding the M.Ed., M.S., Ed.S., Ed.D., and Ph.D. along with Pennsylvania certifications."},
    {"name": _HLTH, "sort_order": 5,
     "description": "The College of Health, Lehigh's newest college, combines data science, public health, and policy to study the determinants of population health, awarding the B.S., B.A., M.P.H., and Ph.D."},
]

_ABOUT_DETAIL: dict[str, dict] = {
    _ENG: {"research_centers": [
        "Institute for Data, Intelligent Systems, and Computation (I-DISC)",
        "Institute for Cyber Physical Infrastructure and Energy (I-CPIE)",
        "ATLSS Engineering Research Center",
    ]},
}
_ABOUT_OMITTED: dict[str, list[str]] = {
    name: (
        ["about_detail.leadership", "about_detail.faculty", "about_detail.founded"]
        + ([] if "research_centers" in _ABOUT_DETAIL.get(name, {}) else ["about_detail.research_centers"])
    )
    for name in _SCHOOL_WEBSITE
}

# ── Channel feeds + official social links (verified this session) ──────────
_NEWS_RSS = "https://news.lehigh.edu/rss.xml"
_SOCIAL = {
    "instagram": "https://www.instagram.com/lehighu/",
    "linkedin": "https://www.linkedin.com/school/lehigh-university/",
    "youtube": "https://www.youtube.com/user/lehighuofficial",
    "facebook": "https://www.facebook.com/lehighu",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _NEWS_RSS,
    "news_url": "https://news.lehigh.edu/",
    "news_curated": True,
    "social": _SOCIAL,
}

_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _CAS: ["College of Arts and Sciences", "liberal arts", "humanities"],
    _ENG: ["Rossin College", "engineering", "Lehigh Engineers"],
    _BUS: ["College of Business", "business", "MBA"],
    _EDU: ["College of Education", "education", "teaching"],
    _HLTH: ["College of Health", "population health", "public health"],
}

# School-specific news RSS where a verified feed exists (Rossin), else the institution feed.
_SCHOOL_RSS: dict[str, str] = {
    _ENG: "https://engineering.lehigh.edu/rss.xml",
}


def _school_content(name: str) -> dict:
    return {
        "news_rss": _SCHOOL_RSS.get(name, _NEWS_RSS),
        "news_url": _SCHOOL_WEBSITE.get(name, "https://news.lehigh.edu/"),
        "news_curated": False,
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": _SOCIAL,
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


def _program_keywords(spec: dict) -> list[str]:
    """Program-relevant feed filter terms: the field of study + owning department."""
    name = spec["program_name"]
    for sep in (" in ", ": "):
        if sep in name:
            field = name.split(sep, 1)[1]
            break
    else:
        field = name
    field = field.split(" (")[0].strip()
    kws = [field]
    dept = spec.get("department", "")
    if dept and dept not in kws and dept not in (spec["school"],):
        kws.append(dept)
    return kws


# ── Tuition ────────────────────────────────────────────────────────────────
_UG_TUITION = 66810   # published 2025-26 undergraduate tuition
_UG_COA = 86100       # published 2025-26 total cost of attendance
_UG_NET_PRICE = 36931  # College Scorecard average net price
_UG_SRC = (
    "Lehigh University - 2025-26 Tuition (Lehigh News) + College Scorecard (UNITID 213543)",
    "https://news.lehigh.edu/lehigh-announces-tuition-for-upcoming-2025-26-academic-year",
)
# FY2025-26 published per-college graduate per-credit rate (Lehigh Finance & Administration).
_GRAD_RATE = {_CAS: 1660, _ENG: 1660, _BUS: 1400, _EDU: 660, _HLTH: 1660}
_GRAD_RATE_OVERRIDE = {
    "lehigh-mba-engineering": 1660,
    "lehigh-mba-educational-leadership": 1160,
    "lehigh-financial-engineering-ms": 1660,
}
# Real full-time program length (months). Most master's run ~24 months; the accelerated
# one-year MBA, the ~10-month professional M.Eng. tracks, and the ~16-month Executive MBA
# are shorter. duration_months is rendered directly on the student detail page and read by
# the desired-time-to-degree matcher, so these are set to the program's published length.
_DURATION_OVERRIDE = {
    "lehigh-mba-fulltime": 12,       # accelerated one-year full-time MBA
    "lehigh-mba-executive": 16,      # Executive MBA, ~16 months
    "lehigh-energy-systems-engineering-meng": 10,  # 10-month professional M.Eng.
    "lehigh-structural-engineering-meng": 10,      # ~10-month professional M.Eng.
    # The Ed.D. is a part-time professional doctorate for working administrators (~4 years); set
    # explicitly so it does NOT inherit the research-Ph.D. 60-month default (it is degree_type
    # "phd" only so the doctoral degree-LEVEL matcher matches an Ed.D. search).
    "lehigh-educational-leadership-edd": 48,
}
_GRAD_SRC = (
    "Lehigh University Finance & Administration - FY2025-26 Graduate Tuition Fee Schedule",
    "https://financeadmin.lehigh.edu/content/fee-schedule-0",
)


def _undergrad_cost() -> dict:
    return {
        "tuition_usd": _UG_TUITION,
        "total_cost_of_attendance": _UG_COA,
        "avg_net_price": _UG_NET_PRICE,
        "funded": False,
        "breakdown": {"tuition": _UG_TUITION, "total_cost_of_attendance": _UG_COA},
        "note": (
            "Published 2025-26 Lehigh undergraduate tuition with the College Scorecard average "
            "net price after grant aid. Lehigh is a private university with a single published sticker."
        ),
        "source": _UG_SRC[0],
        "source_url": _UG_SRC[1],
        "year": "2025-26",
    }


# Lehigh's registrar defines graduate full-time enrollment as 9 credits per fall/spring semester,
# i.e. 18 credits per academic year. ``Program.tuition`` is consumed as an ANNUAL figure
# (program_features exposes it as ``tuition_usd_per_year``, the matcher compares it to the
# student's annual budget, and the student page labels it "tuition / yr"), so for a MULTI-YEAR
# program the scalar is the published per-credit rate x this full-time annual load - the amount a
# full-time student pays in one academic year - NOT the whole-degree total (which would overstate
# the annual budget signal by the number of program years).
_GRAD_ANNUAL_CREDITS = 18
# ACCELERATED programs that finish inside a single academic year (duration <= 12 months) charge
# their FULL degree credits in that one year, so their annual tuition is the whole program, not the
# 18-credit registrar minimum. Each value is the program's published degree-credit count.
_ANNUAL_CREDITS_OVERRIDE = {
    "lehigh-mba-fulltime": 36,                     # accelerated one-year full-time MBA, 36 credits
    "lehigh-energy-systems-engineering-meng": 30,  # 10-month professional M.Eng., 30 credits
    "lehigh-structural-engineering-meng": 30,      # ~10-month professional M.Eng., 30 credits
}


def _grad_annual(spec: dict) -> int:
    slug, school = spec["slug"], spec["school"]
    rate = _GRAD_RATE_OVERRIDE.get(slug, _GRAD_RATE[school])
    return rate * _ANNUAL_CREDITS_OVERRIDE.get(slug, _GRAD_ANNUAL_CREDITS)


def _grad_cost(spec: dict, annual: int) -> dict:
    slug, school = spec["slug"], spec["school"]
    rate = _GRAD_RATE_OVERRIDE.get(slug, _GRAD_RATE[school])
    credits = _ANNUAL_CREDITS_OVERRIDE.get(slug, _GRAD_ANNUAL_CREDITS)
    if slug in _ANNUAL_CREDITS_OVERRIDE:
        load = f"{credits} credits (the full degree, completed within one academic year)"
    else:
        load = f"{credits} credits (9 credits/semester, the registrar's graduate full-time load)"
    return {
        "tuition_usd": annual,
        "funded": False,
        "breakdown": {"tuition": annual},
        "note": (
            f"Lehigh bills graduate study per credit hour; this is the published FY2025-26 "
            f"{school} rate (${rate:,}/credit) x a full-time academic year of {load} - the annual "
            "full-time tuition, a distinct graduate rate, not the undergraduate sticker."
        ),
        "source": _GRAD_SRC[0],
        "source_url": _GRAD_SRC[1],
        "year": "2025-26",
    }


_DOCTORAL_OMIT_NOTE = (
    "Lehigh funds its research doctoral students (tuition waived with a stipend), and professional "
    "or part-time doctorates bill per credit hour with no single published annual figure, so the "
    "annual tuition scalar is omitted rather than estimated. See the program's official cost page."
)


def _doctoral_omit_cost(spec: dict) -> dict:
    return {
        "funded": True,
        "note": _DOCTORAL_OMIT_NOTE,
        "source": f"{spec['school']} - program cost page",
        "source_url": _SCHOOL_WEBSITE.get(spec["school"], "https://www2.lehigh.edu/"),
    }


# ── Admissions requirement sets ────────────────────────────────────────────
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application", "required": True},
        {"name": "Lehigh writing supplement", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "Counselor recommendation and school report", "required": True},
        {"name": "SAT/ACT scores", "required": False,
         "note": "Lehigh is test-optional - scores are considered only if submitted."},
    ],
    "deadlines": [
        {"round": "Early Decision I", "date": "November 1"},
        {"round": "Early Decision II / Regular Decision", "date": "January 1"},
    ],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS", "Duolingo English Test"], "required": True,
                    "note": "Required for applicants whose first language is not English."},
        "visa": {"types": ["F-1", "J-1"], "note": "International students receive an I-20 after admission."},
        "sources": [{"label": "Lehigh Undergraduate Admissions", "url": "https://admissions.lehigh.edu/"}],
    },
    "source": "Lehigh Undergraduate Admissions",
    "source_url": "https://admissions.lehigh.edu/",
}
_REQ_GRAD = {
    "materials": [
        {"name": "Graduate application", "required": True},
        {"name": "Transcripts from all prior institutions", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Letters of recommendation", "required": True},
        {"name": "Resume / CV", "required": False},
    ],
    "deadlines": [{"round": "Varies by program", "date": "See the program's admissions page"}],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS"], "required": True,
                    "note": "Required for applicants whose first language is not English."},
        "visa": {"types": ["F-1", "J-1"], "note": "International students receive an I-20 after admission."},
        "sources": [{"label": "Lehigh Graduate Admissions", "url": "https://www2.lehigh.edu/academics/graduate-studies"}],
    },
    "source": "Lehigh Graduate Admissions",
    "source_url": "https://www2.lehigh.edu/academics/graduate-studies",
}


def _requirements_for(spec: dict) -> dict:
    return dict(_REQ_UNDERGRAD if spec["degree_type"] == "bachelors" else _REQ_GRAD)


# ── Outcomes (institution-wide; Lehigh publishes no per-program earnings split) ─
_OUTCOMES_CONDITIONS = (
    "Institution-wide median earnings of federally aided students measured 10 years after entry "
    "(U.S. Dept. of Education College Scorecard); not a program-specific figure."
)
_OUTCOMES_INSTITUTION = {
    "median_salary": 105584,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry (institution-wide)",
    "conditions": _OUTCOMES_CONDITIONS,
    "source": "U.S. Dept. of Education College Scorecard (Lehigh, UNITID 213543)",
    "source_url": "https://collegescorecard.ed.gov/school/?213543-Lehigh-University",
}

_REVIEWS_BY_SLUG: dict[str, dict] = {}

# ── The catalog ────────────────────────────────────────────────────────────
# Every row is a REAL Lehigh degree read off the Lehigh University Catalog (catalog.lehigh.edu)
# and the five colleges. Concentrations are collapsed into ``tracks`` (never separate rows);
# credential siblings (B.S./M.S./M.Eng./Ph.D. in one field) carry distinct researched bodies.
_CATALOG: list[dict] = [
    {"slug": 'lehigh-africana-studies-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Africana Studies', "degree_type": 'bachelors', "department": 'Department of Africana Studies', "cip": '05.0201', "delivery_format": 'on_campus',
     "description": 'Interdisciplinary study of the histories, cultures, politics, and expressive traditions of Africa and its diaspora across the Americas, the Caribbean, and the African continent.'},
    {"slug": 'lehigh-anthropology-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Anthropology', "degree_type": 'bachelors', "department": 'Department of Sociology and Anthropology', "cip": '45.0201', "delivery_format": 'on_campus',
     "description": 'The comparative study of human societies, cultures, and biological and material life across time, drawing on ethnographic and archaeological methods.'},
    {"slug": 'lehigh-architecture-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Architecture', "degree_type": 'bachelors', "department": 'Department of Art, Architecture and Design', "cip": '04.0201', "delivery_format": 'on_campus',
     "description": 'A pre-professional, liberal-arts-grounded study of the design of buildings and spaces, integrating studio practice with history, theory, and technology.'},
    {"slug": 'lehigh-art-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Art', "degree_type": 'bachelors', "department": 'Department of Art, Architecture and Design', "cip": '50.0702', "delivery_format": 'on_campus',
     "description": 'Studio-based fine arts practice across media, developing visual expression alongside critical and historical understanding of art.'},
    {"slug": 'lehigh-art-history-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Art History', "degree_type": 'bachelors', "department": 'Department of Art, Architecture and Design', "cip": '50.0703', "delivery_format": 'on_campus',
     "description": 'The study of visual art and architecture in historical and cultural context, examining objects, movements, and the theories used to interpret them.'},
    {"slug": 'lehigh-design-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Design', "degree_type": 'bachelors', "department": 'Department of Art, Architecture and Design', "cip": '50.0401', "delivery_format": 'on_campus',
     "description": 'Visual communication through concentrations in graphic and product design, pairing studio practice with design thinking.'},
    {"slug": 'lehigh-asian-studies-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Asian and Asian American Studies', "degree_type": 'bachelors', "department": 'Program in Asian Studies', "cip": '05.0107', "delivery_format": 'on_campus',
     "description": 'Interdisciplinary study of the languages, histories, and cultures of Asia and Asian American communities across the humanities and social sciences.'},
    {"slug": 'lehigh-astronomy-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Astronomy', "degree_type": 'bachelors', "department": 'Department of Physics', "cip": '40.0201', "delivery_format": 'on_campus',
     "description": 'The study of celestial objects and the physical laws governing the universe, combining observational astronomy with foundational physics.'},
    {"slug": 'lehigh-astrophysics-bs', "school": _CAS, "program_name": 'Bachelor of Science in Astrophysics', "degree_type": 'bachelors', "department": 'Department of Physics', "cip": '40.0202', "delivery_format": 'on_campus',
     "description": 'A physics-intensive study of the structure, origin, and evolution of stars, galaxies, and the universe, grounded in advanced physics and mathematics.'},
    {"slug": 'lehigh-biochemistry-bs', "school": _CAS, "program_name": 'Bachelor of Science in Biochemistry', "degree_type": 'bachelors', "department": 'Department of Chemistry', "cip": '26.0202', "delivery_format": 'on_campus',
     "description": 'The chemistry of living systems, studying the molecular basis of biological processes at the interface of chemistry and biology.'},
    {"slug": 'lehigh-biology-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Biology', "degree_type": 'bachelors', "department": 'Department of Biological Sciences', "cip": '26.0101', "delivery_format": 'on_campus',
     "description": 'A broad introduction to the biological sciences, from cells and organisms to ecology and evolution, within a flexible liberal arts framework.'},
    {"slug": 'lehigh-biology-bs', "school": _CAS, "program_name": 'Bachelor of Science in Biology', "degree_type": 'bachelors', "department": 'Department of Biological Sciences', "cip": '26.0101', "delivery_format": 'on_campus',
     "description": 'A comprehensive, laboratory-intensive study of living systems across molecular, cellular, organismal, and ecological scales.'},
    {"slug": 'lehigh-chemistry-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Chemistry', "degree_type": 'bachelors', "department": 'Department of Chemistry', "cip": '40.0501', "delivery_format": 'on_campus',
     "description": 'The study of matter, its composition, and its transformations, offered as a flexible liberal-arts chemistry degree.'},
    {"slug": 'lehigh-chemistry-bs', "school": _CAS, "program_name": 'Bachelor of Science in Chemistry', "degree_type": 'bachelors', "department": 'Department of Chemistry', "cip": '40.0501', "delivery_format": 'on_campus',
     "description": 'An American Chemical Society-approved, laboratory-intensive study of chemical structure, reactivity, and analysis.'},
    {"slug": 'lehigh-chinese-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Chinese', "degree_type": 'bachelors', "department": 'Department of Modern Languages and Literatures', "cip": '16.0301', "delivery_format": 'on_campus',
     "description": 'The study of Chinese language, literature, and culture, developing advanced proficiency and cultural fluency.'},
    {"slug": 'lehigh-cognitive-science-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Cognitive Science', "degree_type": 'bachelors', "department": 'Program in Cognitive Science', "cip": '30.2501', "delivery_format": 'on_campus',
     "description": 'Interdisciplinary study of the mind and intelligence drawing on psychology, philosophy, linguistics, neuroscience, and computer science.'},
    {"slug": 'lehigh-cognitive-science-bs', "school": _CAS, "program_name": 'Bachelor of Science in Cognitive Science', "degree_type": 'bachelors', "department": 'Program in Cognitive Science', "cip": '30.2501', "delivery_format": 'on_campus',
     "description": 'A computationally and empirically intensive study of cognition integrating neuroscience, computation, and experimental methods.'},
    {"slug": 'lehigh-computer-science-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Computer Science', "degree_type": 'bachelors', "department": 'Department of Computer Science and Engineering', "cip": '11.0701', "delivery_format": 'on_campus',
     "description": 'The College of Arts and Sciences path in computer science, pairing core computing and algorithms with the breadth of a liberal-arts curriculum.'},
    {"slug": 'lehigh-earth-environmental-science-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Earth and Environmental Science', "degree_type": 'bachelors', "department": 'Department of Earth and Environmental Sciences', "cip": '40.0601', "delivery_format": 'on_campus',
     "description": "The study of Earth's systems, geology, climate, water, and the environment, and their interactions with human activity."},
    {"slug": 'lehigh-earth-environmental-science-bs', "school": _CAS, "program_name": 'Bachelor of Science in Earth and Environmental Science', "degree_type": 'bachelors', "department": 'Department of Earth and Environmental Sciences', "cip": '40.0601', "delivery_format": 'on_campus',
     "description": 'A quantitative, field- and lab-based study of Earth processes, environmental systems, and geoscience.'},
    {"slug": 'lehigh-economics-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Economics', "degree_type": 'bachelors', "department": 'Department of Economics', "cip": '45.0601', "delivery_format": 'on_campus',
     "description": 'Micro- and macroeconomic theory and policy in a liberal-arts framing, analyzing how societies allocate scarce resources.'},
    {"slug": 'lehigh-economics-bs', "school": _CAS, "program_name": 'Bachelor of Science in Economics', "degree_type": 'bachelors', "department": 'Department of Economics', "cip": '45.0601', "delivery_format": 'on_campus',
     "description": 'A quantitatively intensive economics degree emphasizing econometrics and mathematical modeling for research and analytical careers.'},
    {"slug": 'lehigh-english-ba', "school": _CAS, "program_name": 'Bachelor of Arts in English', "degree_type": 'bachelors', "department": 'Department of English', "cip": '23.0101', "delivery_format": 'on_campus',
     "description": 'Reading, analysis, and interpretation of literature and the craft of writing across genres, periods, and critical traditions.'},
    {"slug": 'lehigh-environmental-studies-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Environmental Studies', "degree_type": 'bachelors', "department": 'Environmental Studies Program', "cip": '03.0104', "delivery_format": 'on_campus',
     "description": 'Interdisciplinary study of environmental challenges combining natural science, social science, policy, and ethics.'},
    {"slug": 'lehigh-french-ba', "school": _CAS, "program_name": 'Bachelor of Arts in French and Francophone Studies', "degree_type": 'bachelors', "department": 'Department of Modern Languages and Literatures', "cip": '16.0901', "delivery_format": 'on_campus',
     "description": 'The study of French language, literatures, and cultures across France and the Francophone world.'},
    {"slug": 'lehigh-german-ba', "school": _CAS, "program_name": 'Bachelor of Arts in German Studies', "degree_type": 'bachelors', "department": 'Department of Modern Languages and Literatures', "cip": '16.0501', "delivery_format": 'on_campus',
     "description": 'The study of German language, literature, and the cultures of the German-speaking world.'},
    {"slug": 'lehigh-global-studies-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Global Studies', "degree_type": 'bachelors', "department": 'Program in Global Studies', "cip": '30.2001', "delivery_format": 'on_campus',
     "description": 'Interdisciplinary study of globalization in its economic, political, cultural, and social dimensions across world regions.'},
    {"slug": 'lehigh-health-medicine-society-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Health, Medicine and Society', "degree_type": 'bachelors', "department": 'Health, Medicine and Society Program', "cip": '51.3202', "delivery_format": 'on_campus',
     "description": 'Interdisciplinary study of health, illness, and medicine as social, cultural, and political phenomena.'},
    {"slug": 'lehigh-history-ba', "school": _CAS, "program_name": 'Bachelor of Arts in History', "degree_type": 'bachelors', "department": 'Department of History', "cip": '54.0101', "delivery_format": 'on_campus',
     "description": 'The study of the human past across regions and eras, developing skills in research, evidence, and the interpretation of historical change.'},
    {"slug": 'lehigh-international-relations-ba', "school": _CAS, "program_name": 'Bachelor of Arts in International Relations', "degree_type": 'bachelors', "department": 'Department of International Relations', "cip": '45.0901', "delivery_format": 'on_campus',
     "description": 'The study of world politics, diplomacy, international security, and the global economy across political and economic systems.'},
    {"slug": 'lehigh-japanese-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Japanese', "degree_type": 'bachelors', "department": 'Department of Modern Languages and Literatures', "cip": '16.0302', "delivery_format": 'on_campus',
     "description": 'The study of Japanese language, literature, and culture, building advanced proficiency and cultural fluency.'},
    {"slug": 'lehigh-journalism-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Journalism', "degree_type": 'bachelors', "department": 'Department of Journalism and Communication', "cip": '09.0401', "delivery_format": 'on_campus',
     "description": 'Reporting, writing, and multimedia storytelling grounded in journalistic ethics and the role of media in society.'},
    {"slug": 'lehigh-latin-american-studies-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Latin American and Latino Studies', "degree_type": 'bachelors', "department": 'Program in Latin American and Latino Studies', "cip": '05.0107', "delivery_format": 'on_campus',
     "description": 'Interdisciplinary study of the histories, cultures, and politics of Latin America and U.S. Latino communities.'},
    {"slug": 'lehigh-mathematics-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Mathematics', "degree_type": 'bachelors', "department": 'Department of Mathematics', "cip": '27.0101', "delivery_format": 'on_campus',
     "description": 'The study of mathematical structures, reasoning, and proof, offered as a flexible liberal-arts mathematics degree.'},
    {"slug": 'lehigh-mathematics-bs', "school": _CAS, "program_name": 'Bachelor of Science in Mathematics', "degree_type": 'bachelors', "department": 'Department of Mathematics', "cip": '27.0101', "delivery_format": 'on_campus',
     "description": 'A rigorous, proof- and application-intensive study of pure and applied mathematics.'},
    {"slug": 'lehigh-molecular-cellular-biology-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Molecular and Cellular Biology', "degree_type": 'bachelors', "department": 'Department of Biological Sciences', "cip": '26.0406', "delivery_format": 'on_campus',
     "description": 'The study of the molecular and cellular basis of life, from gene expression to cell function, within a flexible curriculum.'},
    {"slug": 'lehigh-molecular-cellular-biology-bs', "school": _CAS, "program_name": 'Bachelor of Science in Molecular and Cellular Biology', "degree_type": 'bachelors', "department": 'Department of Biological Sciences', "cip": '26.0406', "delivery_format": 'on_campus',
     "description": 'A laboratory-intensive study of cells and molecules underlying biological processes, from genetics to biochemistry.'},
    {"slug": 'lehigh-music-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Music', "degree_type": 'bachelors', "department": 'Department of Music', "cip": '50.0901', "delivery_format": 'on_campus',
     "description": 'The study of music through performance, theory, history, and composition within a liberal arts context.'},
    {"slug": 'lehigh-neuroscience-bs', "school": _CAS, "program_name": 'Bachelor of Science in Neuroscience', "degree_type": 'bachelors', "department": 'Department of Biological Sciences', "cip": '26.1501', "delivery_format": 'on_campus',
     "description": 'The study of the nervous system and the biological basis of behavior, integrating cellular, molecular, and systems neuroscience.'},
    {"slug": 'lehigh-pharmaceutical-chemistry-bs', "school": _CAS, "program_name": 'Bachelor of Science in Pharmaceutical Chemistry', "degree_type": 'bachelors', "department": 'Department of Chemistry', "cip": '40.0501', "delivery_format": 'on_campus',
     "description": 'The chemistry of drug design, synthesis, and analysis at the interface of chemistry and the pharmaceutical sciences.'},
    {"slug": 'lehigh-philosophy-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Philosophy', "degree_type": 'bachelors', "department": 'Department of Philosophy', "cip": '38.0101', "delivery_format": 'on_campus',
     "description": 'The study of fundamental questions about knowledge, ethics, reality, and reasoning through rigorous argument and analysis.'},
    {"slug": 'lehigh-physics-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Physics', "degree_type": 'bachelors', "department": 'Department of Physics', "cip": '40.0801', "delivery_format": 'on_campus',
     "description": 'The study of matter, energy, and the fundamental laws of nature, offered as a flexible liberal-arts physics degree.'},
    {"slug": 'lehigh-physics-bs', "school": _CAS, "program_name": 'Bachelor of Science in Physics', "degree_type": 'bachelors', "department": 'Department of Physics', "cip": '40.0801', "delivery_format": 'on_campus',
     "description": 'A rigorous, mathematics-intensive study of the physical laws governing matter and energy from quantum to cosmic scales.'},
    {"slug": 'lehigh-political-science-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Political Science', "degree_type": 'bachelors', "department": 'Department of Political Science', "cip": '45.1001', "delivery_format": 'on_campus',
     "description": 'The study of government, political behavior, public policy, and political theory across domestic and comparative contexts.'},
    {"slug": 'lehigh-psychology-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Psychology', "degree_type": 'bachelors', "department": 'Department of Psychology', "cip": '42.0101', "delivery_format": 'on_campus',
     "description": 'The study of mind and behavior across cognitive, developmental, social, and clinical perspectives.'},
    {"slug": 'lehigh-psychology-bs', "school": _CAS, "program_name": 'Bachelor of Science in Psychology', "degree_type": 'bachelors', "department": 'Department of Psychology', "cip": '42.0101', "delivery_format": 'on_campus',
     "description": 'A research- and methods-intensive study of behavior and mental processes emphasizing experimental design and statistics.'},
    {"slug": 'lehigh-religion-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Religion, Culture and Society', "degree_type": 'bachelors', "department": 'Department of Religion Studies', "cip": '38.0201', "delivery_format": 'on_campus',
     "description": 'The study of religious traditions, texts, and practices and their roles in culture, society, and politics worldwide.'},
    {"slug": 'lehigh-sociology-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Sociology', "degree_type": 'bachelors', "department": 'Department of Sociology and Anthropology', "cip": '45.1101', "delivery_format": 'on_campus',
     "description": 'The study of social structures, institutions, inequality, and group behavior using empirical research methods.'},
    {"slug": 'lehigh-spanish-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Spanish and Hispanic Studies', "degree_type": 'bachelors', "department": 'Department of Modern Languages and Literatures', "cip": '16.0905', "delivery_format": 'on_campus',
     "description": 'The study of Spanish language and the literatures and cultures of Spain and Latin America.'},
    {"slug": 'lehigh-statistics-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Statistics and Data Science', "degree_type": 'bachelors', "department": 'Department of Mathematics', "cip": '27.0501', "delivery_format": 'on_campus',
     "description": 'The study of statistical reasoning, data analysis, and modeling, offered with liberal-arts flexibility.'},
    {"slug": 'lehigh-statistics-bs', "school": _CAS, "program_name": 'Bachelor of Science in Statistics and Data Science', "degree_type": 'bachelors', "department": 'Department of Mathematics', "cip": '27.0501', "delivery_format": 'on_campus',
     "description": 'A quantitative, computationally intensive study of statistical methods, data modeling, and machine-learning foundations.'},
    {"slug": 'lehigh-theatre-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Theatre', "degree_type": 'bachelors', "department": 'Department of Theatre', "cip": '50.0501', "delivery_format": 'on_campus',
     "description": 'The study of theatre through performance, design, directing, and dramatic literature within a liberal arts context.'},
    {"slug": 'lehigh-wgss-ba', "school": _CAS, "program_name": 'Bachelor of Arts in Women, Gender and Sexuality Studies', "degree_type": 'bachelors', "department": 'Program in Women, Gender and Sexuality Studies', "cip": '05.0207', "delivery_format": 'on_campus',
     "description": 'Interdisciplinary study of gender and sexuality as they shape culture, society, power, and identity.'},
    {"slug": 'lehigh-american-studies-ma', "school": _CAS, "program_name": 'Master of Arts in American Studies', "degree_type": 'masters', "department": 'Program in American Studies', "cip": '05.0102', "delivery_format": 'on_campus',
     "description": 'Interdisciplinary graduate study of American culture and society across the humanities and social sciences, examining citizenship, identity, and power.'},
    {"slug": 'lehigh-molecular-biology-ms', "school": _CAS, "program_name": 'Master of Science in Molecular Biology', "degree_type": 'masters', "department": 'Department of Biological Sciences', "cip": '26.0204', "delivery_format": 'online',
     "description": 'A distance-delivered graduate program in molecular biology covering gene expression, cellular processes, and modern biotechnology.'},
    {"slug": 'lehigh-biology-phd', "school": _CAS, "program_name": 'Doctor of Philosophy in Biology', "degree_type": 'phd', "department": 'Department of Biological Sciences', "cip": '26.0101', "delivery_format": 'on_campus',
     "description": 'A research-intensive doctoral program with concentrations in biochemistry, cell and molecular biology, neuroscience, and evolution and behavior.'},
    {"slug": 'lehigh-chemistry-phd', "school": _CAS, "program_name": 'Doctor of Philosophy in Chemistry', "degree_type": 'phd', "department": 'Department of Chemistry', "cip": '40.0501', "delivery_format": 'on_campus',
     "description": 'A research-based doctoral program advancing original chemical research across analytical, inorganic, organic, and physical chemistry.'},
    {"slug": 'lehigh-earth-environmental-sciences-ms', "school": _CAS, "program_name": 'Master of Science in Earth and Environmental Sciences', "degree_type": 'masters', "department": 'Department of Earth and Environmental Sciences', "cip": '40.0601', "delivery_format": 'on_campus',
     "description": 'Graduate study of Earth systems and environmental processes combining coursework with original geoscience research.'},
    {"slug": 'lehigh-earth-environmental-sciences-phd', "school": _CAS, "program_name": 'Doctor of Philosophy in Earth and Environmental Sciences', "degree_type": 'phd', "department": 'Department of Earth and Environmental Sciences', "cip": '40.0601', "delivery_format": 'on_campus',
     "description": "A research-intensive doctoral program investigating Earth's systems, climate, and environmental change."},
    {"slug": 'lehigh-english-ma', "school": _CAS, "program_name": 'Master of Arts in English', "degree_type": 'masters', "department": 'Department of English', "cip": '23.0101', "delivery_format": 'on_campus',
     "description": 'Graduate study of literature, criticism, and theory with advanced training in literary research and writing.'},
    {"slug": 'lehigh-english-phd', "school": _CAS, "program_name": 'Doctor of Philosophy in English', "degree_type": 'phd', "department": 'Department of English', "cip": '23.0101', "delivery_format": 'on_campus',
     "description": 'A research-intensive doctoral program producing original scholarship in literature and literary theory.'},
    {"slug": 'lehigh-environmental-policy-ma', "school": _CAS, "program_name": 'Master of Arts in Environmental Policy', "degree_type": 'masters', "department": 'Environmental Policy Program', "cip": '03.0103', "delivery_format": 'on_campus',
     "description": 'Interdisciplinary graduate study of environmental problems and the policy, planning, and governance tools used to address them.'},
    {"slug": 'lehigh-history-ma', "school": _CAS, "program_name": 'Master of Arts in History', "degree_type": 'masters', "department": 'Department of History', "cip": '54.0101', "delivery_format": 'on_campus',
     "description": 'Graduate study of the past with advanced training in historical research, interpretation, and writing.'},
    {"slug": 'lehigh-history-phd', "school": _CAS, "program_name": 'Doctor of Philosophy in History', "degree_type": 'phd', "department": 'Department of History', "cip": '54.0101', "delivery_format": 'on_campus',
     "description": 'A research-intensive doctoral program producing original historical scholarship.'},
    {"slug": 'lehigh-mathematics-ms', "school": _CAS, "program_name": 'Master of Science in Mathematics', "degree_type": 'masters', "department": 'Department of Mathematics', "cip": '27.0101', "delivery_format": 'on_campus',
     "description": 'Graduate study of pure and applied mathematics with advanced coursework in analysis, algebra, and related areas.'},
    {"slug": 'lehigh-applied-mathematics-ms', "school": _CAS, "program_name": 'Master of Science in Applied Mathematics', "degree_type": 'masters', "department": 'Department of Mathematics', "cip": '27.0301', "delivery_format": 'on_campus',
     "description": 'Graduate study applying mathematical modeling, computation, and analysis to scientific and engineering problems.'},
    {"slug": 'lehigh-statistics-ms', "school": _CAS, "program_name": 'Master of Science in Statistics', "degree_type": 'masters', "department": 'Department of Mathematics', "cip": '27.0501', "delivery_format": 'on_campus',
     "description": 'Graduate study of statistical theory and methods for data analysis, inference, and modeling.'},
    {"slug": 'lehigh-mathematics-phd', "school": _CAS, "program_name": 'Doctor of Philosophy in Mathematics', "degree_type": 'phd', "department": 'Department of Mathematics', "cip": '27.0101', "delivery_format": 'on_campus',
     "description": 'A research-intensive doctoral program advancing original scholarship in pure mathematics.'},
    {"slug": 'lehigh-applied-mathematics-phd', "school": _CAS, "program_name": 'Doctor of Philosophy in Applied Mathematics', "degree_type": 'phd', "department": 'Department of Mathematics', "cip": '27.0301', "delivery_format": 'on_campus',
     "description": 'A research-intensive doctoral program producing original scholarship in applied and computational mathematics.'},
    {"slug": 'lehigh-physics-ms', "school": _CAS, "program_name": 'Master of Science in Physics', "degree_type": 'masters', "department": 'Department of Physics', "cip": '40.0801', "delivery_format": 'on_campus',
     "description": 'Graduate study of physical theory and experiment with advanced coursework and research.'},
    {"slug": 'lehigh-physics-phd', "school": _CAS, "program_name": 'Doctor of Philosophy in Physics', "degree_type": 'phd', "department": 'Department of Physics', "cip": '40.0801', "delivery_format": 'on_campus',
     "description": 'A research-intensive doctoral program producing original physics research across theoretical and experimental areas.'},
    {"slug": 'lehigh-political-science-ma', "school": _CAS, "program_name": 'Master of Arts in Political Science', "degree_type": 'masters', "department": 'Department of Political Science', "cip": '45.1001', "delivery_format": 'on_campus',
     "description": 'Graduate study of government, political behavior, and policy with advanced analytical and research training.'},
    {"slug": 'lehigh-public-policy-mpp', "school": _CAS, "program_name": 'Master of Public Policy', "degree_type": 'masters', "department": 'Department of Political Science', "cip": '44.0501', "delivery_format": 'on_campus',
     "description": 'A professional graduate program in policy analysis, program evaluation, and evidence-based decision-making.'},
    {"slug": 'lehigh-psychology-ms', "school": _CAS, "program_name": 'Master of Science in Psychology', "degree_type": 'masters', "department": 'Department of Psychology', "cip": '42.0101', "delivery_format": 'on_campus',
     "description": 'Graduate study of behavior and mental processes with advanced training in research methods and statistics.'},
    {"slug": 'lehigh-psychology-phd', "school": _CAS, "program_name": 'Doctor of Philosophy in Psychology', "degree_type": 'phd', "department": 'Department of Psychology', "cip": '42.0101', "delivery_format": 'on_campus',
     "description": 'A research-intensive doctoral program producing original scholarship in psychological science.'},
    {"slug": 'lehigh-applied-science-bs', "school": _ENG, "program_name": 'Bachelor of Science in Applied Science', "degree_type": 'bachelors', "department": 'Applied Science Program', "cip": '14.0101', "delivery_format": 'on_campus',
     "description": 'An interdisciplinary engineering degree pairing a general engineering foundation with a customized concentration spanning engineering, science, and an area of emphasis.'},
    {"slug": 'lehigh-bioengineering-bs', "school": _ENG, "program_name": 'Bachelor of Science in Bioengineering', "degree_type": 'bachelors', "department": 'Department of Bioengineering', "cip": '14.0501', "delivery_format": 'on_campus',
     "description": 'Engineering principles combined with the life sciences through tracks in biopharmaceutical engineering, biocomputational engineering, and biomechanics and biomaterials.'},
    {"slug": 'lehigh-chemical-engineering-bs', "school": _ENG, "program_name": 'Bachelor of Science in Chemical Engineering', "degree_type": 'bachelors', "department": 'Department of Chemical and Biomolecular Engineering', "cip": '14.0701', "delivery_format": 'on_campus',
     "description": 'The design and optimization of processes that convert raw materials into fuels, pharmaceuticals, materials, and energy at industrial scale.'},
    {"slug": 'lehigh-civil-engineering-bs', "school": _ENG, "program_name": 'Bachelor of Science in Civil Engineering', "degree_type": 'bachelors', "department": 'Department of Civil and Environmental Engineering', "cip": '14.0801', "delivery_format": 'on_campus',
     "description": 'The conception, planning, design, construction, and maintenance of physical works such as bridges, buildings, and transportation and water systems.'},
    {"slug": 'lehigh-environmental-engineering-bs', "school": _ENG, "program_name": 'Bachelor of Science in Environmental Engineering', "degree_type": 'bachelors', "department": 'Department of Civil and Environmental Engineering', "cip": '14.1401', "delivery_format": 'on_campus',
     "description": 'Engineering principles applied to protecting human health and the environment, including the design of water and wastewater treatment systems.'},
    {"slug": 'lehigh-computer-engineering-bs', "school": _ENG, "program_name": 'Bachelor of Science in Computer Engineering', "degree_type": 'bachelors', "department": 'Department of Electrical and Computer Engineering', "cip": '14.0901', "delivery_format": 'on_campus',
     "description": 'The design of intelligent systems spanning hardware and software, from electronic circuits and computer architecture to programming and data structures.'},
    {"slug": 'lehigh-computer-science-bs', "school": _ENG, "program_name": 'Bachelor of Science in Computer Science', "degree_type": 'bachelors', "department": 'Department of Computer Science and Engineering', "cip": '11.0701', "delivery_format": 'on_campus',
     "description": 'The Rossin College engineering degree emphasizing algorithms, software systems, and the effective use of computers to solve real-world problems.'},
    {"slug": 'lehigh-computer-science-business-bs', "school": _ENG, "program_name": 'Bachelor of Science in Computer Science and Business', "degree_type": 'bachelors', "department": 'Department of Computer Science and Engineering', "cip": '11.0701', "delivery_format": 'on_campus',
     "description": 'A joint degree with the College of Business pairing the computer science core with business coursework to build software products and understand the enterprises that deploy them.'},
    {"slug": 'lehigh-electrical-engineering-bs', "school": _ENG, "program_name": 'Bachelor of Science in Electrical Engineering', "degree_type": 'bachelors', "department": 'Department of Electrical and Computer Engineering', "cip": '14.1001', "delivery_format": 'on_campus',
     "description": 'The fundamentals of circuits, systems and control, signals, electronics, electromagnetics, energy conversion, and digital systems.'},
    {"slug": 'lehigh-engineering-mechanics-bs', "school": _ENG, "program_name": 'Bachelor of Science in Engineering Mechanics', "degree_type": 'bachelors', "department": 'Department of Mechanical Engineering and Mechanics', "cip": '14.1101', "delivery_format": 'on_campus',
     "description": 'The analysis of engineering systems with concentrations in applied mathematics, solid mechanics, materials, and fluid mechanics, aimed at research and development.'},
    {"slug": 'lehigh-engineering-physics-bs', "school": _ENG, "program_name": 'Bachelor of Science in Engineering Physics', "degree_type": 'bachelors', "department": 'Department of Physics', "cip": '14.1201', "delivery_format": 'on_campus',
     "description": 'A dual-discipline program centered on electronic device physics, with coursework in quantum mechanics, solids, optics, and computational physics alongside electrical engineering.'},
    {"slug": 'lehigh-industrial-systems-engineering-bs', "school": _ENG, "program_name": 'Bachelor of Science in Industrial and Systems Engineering', "degree_type": 'bachelors', "department": 'Department of Industrial and Systems Engineering', "cip": '14.3501', "delivery_format": 'on_campus',
     "description": 'The analysis, design, and implementation of integrated systems of people, materials, information, and equipment, with tracks in production or information systems.'},
    {"slug": 'lehigh-materials-science-bs', "school": _ENG, "program_name": 'Bachelor of Science in Materials Science and Engineering', "degree_type": 'bachelors', "department": 'Department of Materials Science and Engineering', "cip": '14.1801', "delivery_format": 'on_campus',
     "description": 'The tools to create, test, and invent new materials, from metals and ceramics to polymers and electronic materials, using experimental and computational methods.'},
    {"slug": 'lehigh-mechanical-engineering-bs', "school": _ENG, "program_name": 'Bachelor of Science in Mechanical Engineering', "degree_type": 'bachelors', "department": 'Department of Mechanical Engineering and Mechanics', "cip": '14.1901', "delivery_format": 'on_campus',
     "description": 'One of the broadest engineering disciplines, covering energy conversion, material transport, and the control of motion and forces with an emphasis on product development.'},
    {"slug": 'lehigh-bioengineering-ms', "school": _ENG, "program_name": 'Master of Science in Bioengineering', "degree_type": 'masters', "department": 'Department of Bioengineering', "cip": '14.0501', "delivery_format": 'on_campus',
     "description": 'Advanced interdisciplinary study across life sciences, physical sciences, and engineering, with concentrations in biomaterials, product development, or biomedical analytics.'},
    {"slug": 'lehigh-chemical-engineering-ms', "school": _ENG, "program_name": 'Master of Science in Chemical Engineering', "degree_type": 'masters', "department": 'Department of Chemical and Biomolecular Engineering', "cip": '14.0701', "delivery_format": 'on_campus',
     "description": 'Advanced study of chemical and biomolecular engineering built on biology, chemistry, physics, and mathematics, typically including a research component.'},
    {"slug": 'lehigh-chemical-engineering-meng', "school": _ENG, "program_name": 'Master of Engineering in Chemical Engineering', "degree_type": 'masters', "department": 'Department of Chemical and Biomolecular Engineering', "cip": '14.0701', "delivery_format": 'on_campus',
     "description": "A coursework- and design-oriented professional master's in chemical engineering emphasizing applied practice rather than a research thesis."},
    {"slug": 'lehigh-biological-chemical-engineering-meng', "school": _ENG, "program_name": 'Master of Engineering in Biological Chemical Engineering', "degree_type": 'masters', "department": 'Department of Chemical and Biomolecular Engineering', "cip": '14.0701', "delivery_format": 'on_campus',
     "description": "A professional master's focusing chemical engineering practice on biological and biomolecular processes such as biopharmaceutical and bioprocess systems."},
    {"slug": 'lehigh-chemical-energy-engineering-meng', "school": _ENG, "program_name": 'Master of Engineering in Chemical Energy Engineering', "degree_type": 'masters', "department": 'Department of Chemical and Biomolecular Engineering', "cip": '14.0701', "delivery_format": 'on_campus',
     "description": "A professional master's applying chemical engineering to energy-focused processes, from fuels and conversion to sustainable energy technologies."},
    {"slug": 'lehigh-polymer-science-ms', "school": _ENG, "program_name": 'Master of Science in Polymer Science and Engineering', "degree_type": 'masters', "department": 'Department of Chemical and Biomolecular Engineering', "cip": '14.3201', "delivery_format": 'on_campus',
     "description": "An interdisciplinary research master's in the synthesis, structure, characterization, and processing of polymers across chemistry, materials science, and chemical engineering."},
    {"slug": 'lehigh-polymer-science-meng', "school": _ENG, "program_name": 'Master of Engineering in Polymer Science and Engineering', "degree_type": 'masters', "department": 'Department of Chemical and Biomolecular Engineering', "cip": '14.3201', "delivery_format": 'on_campus',
     "description": "A practice-oriented professional master's in polymer science and engineering emphasizing applied processing and product development."},
    {"slug": 'lehigh-civil-engineering-ms', "school": _ENG, "program_name": 'Master of Science in Civil Engineering', "degree_type": 'masters', "department": 'Department of Civil and Environmental Engineering', "cip": '14.0801', "delivery_format": 'on_campus',
     "description": "The department's broadest graduate degree, with concentrations in structural, geotechnical, water resources, or emerging areas of civil engineering."},
    {"slug": 'lehigh-environmental-engineering-ms', "school": _ENG, "program_name": 'Master of Science in Environmental Engineering', "degree_type": 'masters', "department": 'Department of Civil and Environmental Engineering', "cip": '14.1401', "delivery_format": 'on_campus',
     "description": 'Core coursework and design in environmental engineering processes for water, wastewater, and sustainability challenges.'},
    {"slug": 'lehigh-structural-engineering-ms', "school": _ENG, "program_name": 'Master of Science in Structural Engineering', "degree_type": 'masters', "department": 'Department of Civil and Environmental Engineering', "cip": '14.0803', "delivery_format": 'on_campus',
     "description": "A focus on structural systems with coursework and electives in structural design and analysis, drawing on Lehigh's ATLSS structural research strength."},
    {"slug": 'lehigh-structural-engineering-meng', "school": _ENG, "program_name": 'Master of Engineering in Structural Engineering', "degree_type": 'masters', "department": 'Department of Civil and Environmental Engineering', "cip": '14.0803', "delivery_format": 'on_campus',
     "description": 'A professional degree emphasizing structural engineering applications and design through a dedicated design sequence, completable in roughly ten months.'},
    {"slug": 'lehigh-computer-science-ms', "school": _ENG, "program_name": 'Master of Science in Computer Science', "degree_type": 'masters', "department": 'Department of Computer Science and Engineering', "cip": '11.0701', "delivery_format": 'on_campus',
     "description": 'A graduate program in computer science, optionally including a thesis, covering advanced algorithms, systems, and applications.'},
    {"slug": 'lehigh-computer-science-meng', "school": _ENG, "program_name": 'Master of Engineering in Computer Science', "degree_type": 'masters', "department": 'Department of Computer Science and Engineering', "cip": '11.0701', "delivery_format": 'on_campus',
     "description": "A professional master's including design-oriented courses and an engineering project, emphasizing applied software engineering."},
    {"slug": 'lehigh-computer-engineering-ms', "school": _ENG, "program_name": 'Master of Science in Computer Engineering', "degree_type": 'masters', "department": 'Department of Electrical and Computer Engineering', "cip": '14.0901', "delivery_format": 'on_campus',
     "description": 'Advanced study of intelligent hardware and software systems, from computer architecture to embedded computing, typically with a thesis option.'},
    {"slug": 'lehigh-computer-engineering-meng', "school": _ENG, "program_name": 'Master of Engineering in Computer Engineering', "degree_type": 'masters', "department": 'Department of Electrical and Computer Engineering', "cip": '14.0901', "delivery_format": 'on_campus',
     "description": "A professional, coursework-focused master's in computer engineering emphasizing applied design of hardware and software systems."},
    {"slug": 'lehigh-electrical-engineering-ms', "school": _ENG, "program_name": 'Master of Science in Electrical Engineering', "degree_type": 'masters', "department": 'Department of Electrical and Computer Engineering', "cip": '14.1001', "delivery_format": 'on_campus',
     "description": 'A graduate degree, optionally with a thesis, advancing work in circuits, signals, electromagnetics, electronics, and control.'},
    {"slug": 'lehigh-electrical-engineering-meng', "school": _ENG, "program_name": 'Master of Engineering in Electrical Engineering', "degree_type": 'masters', "department": 'Department of Electrical and Computer Engineering', "cip": '14.1001', "delivery_format": 'on_campus',
     "description": "A professional master's in electrical engineering emphasizing coursework and applied practice over a research thesis."},
    {"slug": 'lehigh-photonics-ms', "school": _ENG, "program_name": 'Master of Science in Photonics', "degree_type": 'masters', "department": 'Department of Electrical and Computer Engineering', "cip": '14.1001', "delivery_format": 'on_campus',
     "description": 'An interdisciplinary degree giving broad training across photonics, spanning physics, electrical engineering, and materials science and engineering.'},
    {"slug": 'lehigh-materials-science-ms', "school": _ENG, "program_name": 'Master of Science in Materials Science and Engineering', "degree_type": 'masters', "department": 'Department of Materials Science and Engineering', "cip": '14.1801', "delivery_format": 'on_campus',
     "description": "A research-focused master's, typically with a thesis, advancing the study of the structure, properties, and processing of engineered materials."},
    {"slug": 'lehigh-materials-science-meng', "school": _ENG, "program_name": 'Master of Engineering in Materials Science and Engineering', "degree_type": 'masters', "department": 'Department of Materials Science and Engineering', "cip": '14.1801', "delivery_format": 'on_campus',
     "description": "A professional master's emphasizing practical materials engineering applications through an engineering project rather than a research thesis."},
    {"slug": 'lehigh-industrial-engineering-ms', "school": _ENG, "program_name": 'Master of Science in Industrial Engineering and Operations Research', "degree_type": 'masters', "department": 'Department of Industrial and Systems Engineering', "cip": '14.3501', "delivery_format": 'on_campus',
     "description": 'Industrial engineering and operations research methods for improving systems and decision-making across industry, business, healthcare, and government.'},
    {"slug": 'lehigh-optimization-ms', "school": _ENG, "program_name": 'Master of Science in Optimization', "degree_type": 'masters', "department": 'Department of Industrial and Systems Engineering', "cip": '14.3501', "delivery_format": 'on_campus',
     "description": 'A focused program in optimization theory and algorithms for engineering and data science, emphasizing mathematical programming and computational methods.'},
    {"slug": 'lehigh-health-systems-engineering-ms', "school": _ENG, "program_name": 'Master of Science in Health Systems Engineering', "degree_type": 'masters', "department": 'Department of Industrial and Systems Engineering', "cip": '14.3501', "delivery_format": 'on_campus',
     "description": 'Industrial and systems engineering fundamentals combined with healthcare systems knowledge to improve the quality and efficiency of health-care delivery.'},
    {"slug": 'lehigh-financial-engineering-ms', "school": _ENG, "program_name": 'Master of Science in Financial Engineering', "degree_type": 'masters', "department": 'Department of Industrial and Systems Engineering', "cip": '52.0806', "delivery_format": 'on_campus',
     "description": 'A STEM-designated program in advanced finance, risk management, and quantitative analysis grounded in financial theory, applied mathematics, and engineering.'},
    {"slug": 'lehigh-data-science-ms', "school": _ENG, "program_name": 'Master of Science in Data Science', "degree_type": 'masters', "department": 'Data Science Program', "cip": '30.7001', "delivery_format": 'on_campus',
     "description": 'A technical graduate program in data-scientific concepts and tools, spanning statistical modeling, machine learning, and large-scale computing.'},
    {"slug": 'lehigh-energy-systems-engineering-meng', "school": _ENG, "program_name": 'Master of Engineering in Energy Systems Engineering', "degree_type": 'masters', "department": 'Energy Systems Engineering Program', "cip": '14.0101', "delivery_format": 'on_campus',
     "description": "A ten-month professional master's preparing technical leaders for the energy and power industries and the challenges facing global energy infrastructure."},
    {"slug": 'lehigh-aerospace-engineering-ms', "school": _ENG, "program_name": 'Master of Science in Aerospace and Space Systems Engineering', "degree_type": 'masters', "department": 'Department of Mechanical Engineering and Mechanics', "cip": '14.0201', "delivery_format": 'on_campus',
     "description": 'An interdisciplinary program with concentrations in aerodynamics, aerospace systems, and space systems engineering, built on core aerospace coursework.'},
    {"slug": 'lehigh-mechanical-engineering-ms', "school": _ENG, "program_name": 'Master of Science in Mechanical Engineering', "degree_type": 'masters', "department": 'Department of Mechanical Engineering and Mechanics', "cip": '14.1901', "delivery_format": 'on_campus',
     "description": 'Advanced coursework in heat transfer, fluid mechanics, controls, and related mechanical engineering topics.'},
    {"slug": 'lehigh-bioengineering-phd', "school": _ENG, "program_name": 'Doctor of Philosophy in Bioengineering', "degree_type": 'phd', "department": 'Department of Bioengineering', "cip": '14.0501', "delivery_format": 'on_campus',
     "description": 'A research doctorate combining life sciences, physical sciences, and engineering to create new knowledge and products through dissertation research.'},
    {"slug": 'lehigh-chemical-engineering-phd', "school": _ENG, "program_name": 'Doctor of Philosophy in Chemical Engineering', "degree_type": 'phd', "department": 'Department of Chemical and Biomolecular Engineering', "cip": '14.0701', "delivery_format": 'on_campus',
     "description": 'An original-research doctorate advancing chemical and biomolecular engineering across catalysis, energy, and biomolecular processes.'},
    {"slug": 'lehigh-polymer-science-phd', "school": _ENG, "program_name": 'Doctor of Philosophy in Polymer Science and Engineering', "degree_type": 'phd', "department": 'Department of Chemical and Biomolecular Engineering', "cip": '14.3201', "delivery_format": 'on_campus',
     "description": 'An interdisciplinary research doctorate on the synthesis, structure, and processing of polymers across chemical engineering, materials science, chemistry, and physics.'},
    {"slug": 'lehigh-civil-engineering-phd', "school": _ENG, "program_name": 'Doctor of Philosophy in Civil Engineering', "degree_type": 'phd', "department": 'Department of Civil and Environmental Engineering', "cip": '14.0801', "delivery_format": 'on_campus',
     "description": 'A research doctorate culminating in an original dissertation, preparing graduates for leadership in the private sector, public sector, and academia.'},
    {"slug": 'lehigh-environmental-engineering-phd', "school": _ENG, "program_name": 'Doctor of Philosophy in Environmental Engineering', "degree_type": 'phd', "department": 'Department of Civil and Environmental Engineering', "cip": '14.1401', "delivery_format": 'on_campus',
     "description": 'A research doctorate addressing environmental engineering challenges in water quality, sustainability, and treatment processes through original investigation.'},
    {"slug": 'lehigh-structural-engineering-phd', "school": _ENG, "program_name": 'Doctor of Philosophy in Structural Engineering', "degree_type": 'phd', "department": 'Department of Civil and Environmental Engineering', "cip": '14.0803', "delivery_format": 'on_campus',
     "description": "An advanced research doctorate in structural systems and mechanics, leveraging Lehigh's large-scale structural testing and ATLSS research infrastructure."},
    {"slug": 'lehigh-computer-science-phd', "school": _ENG, "program_name": 'Doctor of Philosophy in Computer Science', "degree_type": 'phd', "department": 'Department of Computer Science and Engineering', "cip": '11.0701', "delivery_format": 'on_campus',
     "description": 'A research doctorate with qualifying and general examinations and a dissertation defense in an area of computer science research.'},
    {"slug": 'lehigh-computer-engineering-phd', "school": _ENG, "program_name": 'Doctor of Philosophy in Computer Engineering', "degree_type": 'phd', "department": 'Department of Electrical and Computer Engineering', "cip": '14.0901', "delivery_format": 'on_campus',
     "description": 'A research doctorate in the design and analysis of intelligent hardware and software systems, from computer architecture to embedded systems.'},
    {"slug": 'lehigh-electrical-engineering-phd', "school": _ENG, "program_name": 'Doctor of Philosophy in Electrical Engineering', "degree_type": 'phd', "department": 'Department of Electrical and Computer Engineering', "cip": '14.1001', "delivery_format": 'on_campus',
     "description": 'A research doctorate advancing original work in signals, electronics, electromagnetics, and photonics.'},
    {"slug": 'lehigh-materials-science-phd', "school": _ENG, "program_name": 'Doctor of Philosophy in Materials Science and Engineering', "degree_type": 'phd', "department": 'Department of Materials Science and Engineering', "cip": '14.1801', "delivery_format": 'on_campus',
     "description": 'A research doctorate combining coursework and original research on the structure, properties, and processing of materials.'},
    {"slug": 'lehigh-industrial-systems-engineering-phd', "school": _ENG, "program_name": 'Doctor of Philosophy in Industrial and Systems Engineering', "degree_type": 'phd', "department": 'Department of Industrial and Systems Engineering', "cip": '14.3501', "delivery_format": 'on_campus',
     "description": 'A research doctorate emphasizing mathematical optimization, data science, machine learning, and stochastic modeling across energy, healthcare, finance, and supply chains.'},
    {"slug": 'lehigh-mechanical-engineering-phd', "school": _ENG, "program_name": 'Doctor of Philosophy in Mechanical Engineering', "degree_type": 'phd', "department": 'Department of Mechanical Engineering and Mechanics', "cip": '14.1901', "delivery_format": 'on_campus',
     "description": 'A research doctorate requiring core courses, technical electives, and an original-research dissertation in mechanical engineering.'},
    {"slug": 'lehigh-business-economics-bs', "school": _BUS, "program_name": 'Bachelor of Science in Business and Economics', "degree_type": 'bachelors', "department": 'College of Business', "cip": '52.0201', "delivery_format": 'on_campus',
     "description": "Lehigh's core undergraduate business degree, pairing a broad AACSB-accredited business foundation with a chosen major in accounting, finance, marketing, management, economics, business analytics, business information systems, or supply chain management.",
     "tracks": ['Accounting', 'Finance', 'Marketing', 'Management', 'Economics', 'Business Analytics', 'Business Information Systems', 'Supply Chain Management']},
    {"slug": 'lehigh-integrated-business-engineering-bs', "school": _BUS, "program_name": 'Bachelor of Science in Integrated Business and Engineering', "degree_type": 'bachelors', "department": 'College of Business', "cip": '52.0201', "delivery_format": 'on_campus',
     "description": 'A selective honors program offered with the Rossin College of Engineering, built around how business and technology fit together through product development and entrepreneurship.'},
    {"slug": 'lehigh-integrated-business-health-bs', "school": _BUS, "program_name": 'Bachelor of Science in Integrated Business and Health', "degree_type": 'bachelors', "department": 'College of Business', "cip": '51.0701', "delivery_format": 'on_campus',
     "description": 'An inter-college program pairing core business principles with health economics and policy to develop leaders for the health industry.'},
    {"slug": 'lehigh-mba-fulltime', "school": _BUS, "program_name": 'Master of Business Administration (One-Year Full-Time)', "degree_type": 'masters', "department": 'College of Business', "cip": '52.0201', "delivery_format": 'on_campus',
     "description": 'An accelerated one-year, full-time MBA delivering the general-management core plus electives on campus in a compressed cohort format.'},
    {"slug": 'lehigh-mba-flex', "school": _BUS, "program_name": 'Master of Business Administration (FLEX)', "degree_type": 'masters', "department": 'College of Business', "cip": '52.0201', "delivery_format": 'hybrid',
     "description": 'A part-time MBA delivering the full curriculum at a personalized pace, online via ClassroomLIVE, on campus, or a mix of both.'},
    {"slug": 'lehigh-mba-executive', "school": _BUS, "program_name": 'Master of Business Administration (Executive)', "degree_type": 'masters', "department": 'College of Business', "cip": '52.0201', "delivery_format": 'hybrid',
     "description": 'An Executive MBA, typically completed in about sixteen months, offered as a customized program in partnership with employers.'},
    {"slug": 'lehigh-applied-economics-ms', "school": _BUS, "program_name": 'Master of Science in Applied Economics', "degree_type": 'masters', "department": 'Department of Economics', "cip": '45.0603', "delivery_format": 'on_campus',
     "description": 'A STEM-designated applied economics degree combining core economics with a chosen academic or industry-and-policy track for economist and policy-analyst roles.'},
    {"slug": 'lehigh-business-analytics-ms', "school": _BUS, "program_name": 'Master of Science in Business Analytics', "degree_type": 'masters', "department": 'Department of Decision and Technology Analytics', "cip": '52.1301', "delivery_format": 'on_campus',
     "description": 'Cutting-edge data-analytics knowledge and skills, from modeling and machine learning to decision analytics, for the fast-growing analytics field.'},
    {"slug": 'lehigh-management-ms', "school": _BUS, "program_name": 'Master of Science in Management', "degree_type": 'masters', "department": 'Department of Management', "cip": '52.0201', "delivery_format": 'on_campus',
     "description": 'A cohort-based management degree giving non-business graduates the core business and management foundation.'},
    {"slug": 'lehigh-mba-engineering', "school": _BUS, "program_name": 'Master of Business Administration and Engineering', "degree_type": 'masters', "department": 'College of Business', "cip": '52.0201', "delivery_format": 'hybrid',
     "description": 'A joint program with the Rossin College pairing the MBA management core with graduate engineering coursework for technology-leadership roles.'},
    {"slug": 'lehigh-mba-educational-leadership', "school": _BUS, "program_name": 'Master of Business Administration and Educational Leadership', "degree_type": 'masters', "department": 'College of Business', "cip": '52.0201', "delivery_format": 'hybrid',
     "description": 'A joint program with the College of Education combining the MBA management core with graduate study in educational leadership.'},
    {"slug": 'lehigh-business-economics-phd', "school": _BUS, "program_name": 'Doctor of Philosophy in Business and Economics', "degree_type": 'phd', "department": 'College of Business', "cip": '52.0101', "delivery_format": 'on_campus',
     "description": 'A STEM-designated doctoral program with specialization tracks including health economics, applied econometrics, and empirical macroeconomics or labor economics.'},
    {"slug": 'lehigh-school-counseling-med', "school": _EDU, "program_name": 'Master of Education in School Counseling', "degree_type": 'masters', "department": 'Counseling Psychology Program', "cip": '13.1101', "delivery_format": 'on_campus',
     "description": 'A two-year program preparing PreK-12 school counselors, approved for Pennsylvania school-counselor certification, covering counseling theory and school-based practice.'},
    {"slug": 'lehigh-mental-health-counseling-med', "school": _EDU, "program_name": 'Master of Education in Mental Health Counseling', "degree_type": 'masters', "department": 'Counseling Psychology Program', "cip": '51.1508', "delivery_format": 'hybrid',
     "description": 'A program meeting the educational requirements for Pennsylvania Licensed Professional Counselor licensure, preparing graduates for community and agency counseling.'},
    {"slug": 'lehigh-international-school-counseling-med', "school": _EDU, "program_name": 'Master of Education in International School Counseling', "degree_type": 'masters', "department": 'Counseling Psychology Program', "cip": '13.1101', "delivery_format": 'hybrid',
     "description": 'A program preparing counselors to serve the globally mobile communities of overseas and international schools, combining summer institutes with online and in-person coursework.'},
    {"slug": 'lehigh-counseling-psychology-phd', "school": _EDU, "program_name": 'Doctor of Philosophy in Counseling Psychology', "degree_type": 'phd', "department": 'Counseling Psychology Program', "cip": '42.2803', "delivery_format": 'on_campus',
     "description": 'An APA-accredited doctoral program providing advanced research and clinical training in counseling psychology for licensed-psychologist careers.'},
    {"slug": 'lehigh-school-psychology-eds', "school": _EDU, "program_name": 'Educational Specialist in School Psychology', "degree_type": 'masters', "department": 'School Psychology Program', "cip": '42.2805', "delivery_format": 'on_campus',
     "description": 'An Educational Specialist program on the scientist-practitioner model preparing certified school psychologists to deliver assessment, intervention, and consultation.'},
    {"slug": 'lehigh-school-psychology-phd', "school": _EDU, "program_name": 'Doctor of Philosophy in School Psychology', "degree_type": 'phd', "department": 'School Psychology Program', "cip": '42.2805', "delivery_format": 'on_campus',
     "description": 'A scientist-practitioner doctoral program in school psychology spanning school, clinical, and hospital practice as well as research and faculty careers.'},
    {"slug": 'lehigh-educational-leadership-med', "school": _EDU, "program_name": 'Master of Education in Educational Leadership', "degree_type": 'masters', "department": 'Educational Leadership Program', "cip": '13.0401', "delivery_format": 'online',
     "description": 'A program building a core foundation in leadership, organizational development, and change management, supporting PK-12 principal, supervisor, and superintendent certification.'},
    {"slug": 'lehigh-educational-leadership-upal-med', "school": _EDU, "program_name": 'Master of Education in Educational Leadership (Urban Principals Academy at Lehigh)', "degree_type": 'masters', "department": 'Educational Leadership Program', "cip": '13.0401', "delivery_format": 'hybrid',
     "description": 'A cohort program developing urban school leaders with an emphasis on creativity and imagination, delivered online with summer sessions on campus.'},
    {"slug": 'lehigh-educational-leadership-edd', "school": _EDU, "program_name": 'Doctor of Education in Educational Leadership', "degree_type": 'phd', "department": 'Educational Leadership Program', "cip": '13.0401', "delivery_format": 'on_campus',
     "description": "A post-master's professional doctorate developing the leadership of administrators in educational institutions, with paths toward superintendent or principal certification."},
    {"slug": 'lehigh-special-education-med', "school": _EDU, "program_name": 'Master of Education in Special Education', "degree_type": 'masters', "department": 'Special Education Program', "cip": '13.1001', "delivery_format": 'on_campus',
     "description": 'A program emphasizing evidence-based practices for students with disabilities, with concentrations from intensive academic intervention to low-incidence disabilities.'},
    {"slug": 'lehigh-behavior-analysis-med', "school": _EDU, "program_name": 'Master of Education in Behavior Analysis', "degree_type": 'masters', "department": 'Special Education Program', "cip": '42.2814', "delivery_format": 'on_campus',
     "description": 'A program aligned with Behavior Analyst Certification Board standards, focused on evidence-based behavioral support and preparation toward board certification.'},
    {"slug": 'lehigh-special-education-phd', "school": _EDU, "program_name": 'Doctor of Philosophy in Special Education', "degree_type": 'phd', "department": 'Special Education Program', "cip": '13.1001', "delivery_format": 'on_campus',
     "description": "A post-master's doctoral program in which students conduct advanced research and develop competencies in publication, college teaching, grant writing, and program administration."},
    {"slug": 'lehigh-elementary-education-med', "school": _EDU, "program_name": 'Master of Education in Elementary Education and PreK-4 Teacher Certification', "degree_type": 'masters', "department": 'Teaching, Learning, and Technology Program', "cip": '13.1202', "delivery_format": 'on_campus',
     "description": 'A program preparing candidates for Pennsylvania PreK-4 teacher certification through coursework in child development, literacy, mathematics, science, and social studies.'},
    {"slug": 'lehigh-secondary-education-med', "school": _EDU, "program_name": 'Master of Education in Secondary Education and Grades 7-12 Teacher Certification', "degree_type": 'masters', "department": 'Teaching, Learning, and Technology Program', "cip": '13.1205', "delivery_format": 'on_campus',
     "description": 'A program preparing candidates for Pennsylvania 7-12 certification in one of eight subject areas, from biology and chemistry to mathematics and social studies.'},
    {"slug": 'lehigh-teaching-learning-med', "school": _EDU, "program_name": 'Master of Education in Teaching and Learning', "degree_type": 'masters', "department": 'Teaching, Learning, and Technology Program', "cip": '13.0301', "delivery_format": 'on_campus',
     "description": "A program enhancing practicing educators' evidence-based pedagogy, with tracks in technology and design, innovative pedagogy, English as a second language, or social-emotional wellness."},
    {"slug": 'lehigh-instructional-technology-ms', "school": _EDU, "program_name": 'Master of Science in Instructional Technology', "degree_type": 'masters', "department": 'Teaching, Learning, and Technology Program', "cip": '13.0501', "delivery_format": 'hybrid',
     "description": 'A program preparing educators to integrate instructional technology across PreK-12 and post-secondary settings through programming, design, and assessment.'},
    {"slug": 'lehigh-teaching-learning-technology-phd', "school": _EDU, "program_name": 'Doctor of Philosophy in Teaching, Learning, and Technology', "degree_type": 'phd', "department": 'Teaching, Learning, and Technology Program', "cip": '13.0501', "delivery_format": 'on_campus',
     "description": 'A scientist-practitioner doctoral program spanning learning design, instructional technology, and teacher education, with individualized concentrations and research methods.'},
    {"slug": 'lehigh-human-development-med', "school": _EDU, "program_name": 'Master of Education in Human Development', "degree_type": 'masters', "department": 'Education and Human Services Program', "cip": '19.0701', "delivery_format": 'on_campus',
     "description": 'Graduate study of human growth and development as it applies to educational and human-services settings.'},
    {"slug": 'lehigh-population-health-bs', "school": _HLTH, "program_name": 'Bachelor of Science in Population Health', "degree_type": 'bachelors', "department": 'Department of Population Health', "cip": '51.2201', "delivery_format": 'on_campus',
     "description": 'An undergraduate degree combining data science, public health, and policy to investigate the determinants of health and design interventions that advance health equity.'},
    {"slug": 'lehigh-community-global-health-ba', "school": _HLTH, "program_name": 'Bachelor of Arts in Community and Global Health', "degree_type": 'bachelors', "department": 'Department of Community and Global Health', "cip": '51.2201', "delivery_format": 'on_campus',
     "description": 'An undergraduate degree emphasizing the methods and analysis behind health services, interventions, and programs in communities, in domestic and global contexts.'},
    {"slug": 'lehigh-biostatistics-health-data-science-bs', "school": _HLTH, "program_name": 'Bachelor of Science in Biostatistics and Health Data Science', "degree_type": 'bachelors', "department": 'Department of Biostatistics and Health Data Science', "cip": '26.1102', "delivery_format": 'on_campus',
     "description": 'An undergraduate degree drawing on mathematics, statistics, computing, and epidemiology, spanning study design, data management, and analytical-method development for public health.'},
    {"slug": 'lehigh-public-health-mph', "school": _HLTH, "program_name": 'Master of Public Health', "degree_type": 'masters', "department": 'Department of Population Health', "cip": '51.2201', "delivery_format": 'hybrid',
     "description": 'A professional degree preparing students for public-health research, practice, and policymaking through hands-on, data-driven training in population health.'},
    {"slug": 'lehigh-population-health-phd', "school": _HLTH, "program_name": 'Doctor of Philosophy in Population Health', "degree_type": 'phd', "department": 'Department of Population Health', "cip": '51.2201', "delivery_format": 'on_campus',
     "description": 'A doctoral program training scholars to develop and apply innovative methods at the intersection of health, data, and policy to improve health equity and systems.'},
]

# ── Derived defaults ───────────────────────────────────────────────────────
_DEFAULT_DURATION = {"bachelors": 48, "masters": 24, "phd": 60, "professional": 36}
for _p in _CATALOG:
    _p.setdefault("delivery_format", "on_campus")
    _p.setdefault(
        "duration_months",
        _DURATION_OVERRIDE.get(_p["slug"], _DEFAULT_DURATION.get(_p["degree_type"], 24)),
    )

PROGRAMS: list[dict] = _CATALOG
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

# ── Quality gates (fail the build on fabrication tells) ─────────────────────
if len(set(PROGRAM_SLUGS)) != len(PROGRAM_SLUGS):
    _seen: set[str] = set()
    _dups = [s for s in PROGRAM_SLUGS if s in _seen or _seen.add(s)]
    raise RuntimeError(f"duplicate program slug(s): {sorted(set(_dups))}")
_name_keys = [(p["program_name"], p["degree_type"]) for p in PROGRAMS]
if len(set(_name_keys)) != len(_name_keys):
    _seen2: set[tuple] = set()
    _dn = [k for k in _name_keys if k in _seen2 or _seen2.add(k)]
    raise RuntimeError(f"duplicate (program_name, degree_type): {_dn}")
for _p in PROGRAMS:
    if not _p.get("cip") or not re.fullmatch(r"\d{2}\.\d{2,4}", _p["cip"]):
        raise RuntimeError(f"missing/malformed cip on {_p['slug']}: {_p.get('cip')!r}")
    _d = _p.get("description") or ""
    if _d.startswith(_p["program_name"]):
        raise RuntimeError(f"name-prefixed description on {_p['slug']}")
    if "offered through" in _d or "is a program at" in _d:
        raise RuntimeError(f"classification-stub description on {_p['slug']}")
# Paid professional doctorates: doctoral-LEVEL degrees (kept degree_type "phd" so the matcher's
# doctoral degree-level fit still matches an Ed.D. search) that are NOT funded - the student pays
# a published per-credit rate, so they carry a filled annual scalar (unlike funded research Ph.D.s).
_PAID_DOCTORATE_SLUGS = {"lehigh-educational-leadership-edd"}


def _is_paid_grad(spec: dict) -> bool:
    return spec["degree_type"] == "masters" or spec["slug"] in _PAID_DOCTORATE_SLUGS


# Matcher-core tuition COVERAGE gate: every master's AND every paid professional doctorate
# (the Ed.D.) must carry a computed published graduate rate. Research doctorates are funded/omitted.
_uncovered = [p["slug"] for p in PROGRAMS if _is_paid_grad(p)
              and _grad_annual(p) is None]
if _uncovered:
    raise RuntimeError(f"master's/paid-doctorate tuition not covered: {_uncovered}")
_copydown = [p["slug"] for p in PROGRAMS if _is_paid_grad(p)
             and _grad_annual(p) == _UG_TUITION]
if _copydown:
    raise RuntimeError(f"graduate tuition equals undergrad sticker (copy-down): {_copydown}")


# ── who_its_for (derived, program-distinct, grounded in the verified description) ──
def _who_focus(spec: dict) -> str:
    desc = (spec.get("description") or "").strip().rstrip(".")
    for verb in (" - ", ": ", " study of ", " studies ", " study ", " covering ", " spanning ",
                 " on how ", " on the ", " of how ", " applies ", " combines ", " examines ",
                 " analyzes ", " builds ", " trains ", " grounds ", " in which ", " where ",
                 " bridging ", " across ", " preparing ", " developing ", " turning ",
                 " integrating ", " emphasizing ", " for ", " with "):
        i = desc.lower().find(verb)
        if i > 0:
            tail = desc[i + len(verb):].strip()
            for stop in (";", ",", " - "):
                j = tail.find(stop)
                if 0 < j < 150:
                    tail = tail[:j]
            if 8 <= len(tail) <= 170:
                return tail.rstrip(".")
    return spec.get("description", spec["program_name"])[:120]


def _who_its_for(spec: dict) -> str:
    name = spec["program_name"]
    focus = _who_focus(spec)
    dt = spec["degree_type"]
    if dt == "bachelors":
        return (
            f"Undergraduates choosing {name} at Lehigh who want to study {focus}. "
            "A fit for students headed toward graduate study, professional work, or research in the field."
        )
    if dt == "phd":
        if spec["slug"] in _PAID_DOCTORATE_SLUGS:
            return (
                f"Working professionals pursuing Lehigh's {name} for advanced practice in {focus}, "
                "aiming for senior leadership and applied roles rather than a research career."
            )
        return (
            f"Students pursuing Lehigh's {name} to conduct original research in {focus}, "
            "aiming for academic, national-lab, or industry research careers."
        )
    return (
        f"Graduate students in Lehigh's {name} seeking advanced, applied study of {focus}. "
        "Best for professional practice, specialization, or further graduate work."
    )


_who_values = [_who_its_for(p) for p in PROGRAMS]
if len(set(_who_values)) != len(_who_values):
    raise RuntimeError(f"who_its_for not program-distinct: {len(set(_who_values))}/{len(_who_values)}")


def _program_standard(spec: dict) -> dict:
    slug = spec["slug"]
    omitted: list[str] = ["outcomes_data.employment_rate", "outcomes_data.top_industries"]
    if spec["degree_type"] != "bachelors" and not _is_paid_grad(spec):
        omitted.append("cost_data.tuition_usd")
    if not spec.get("tracks"):
        omitted.append("tracks")
    omitted.append("class_profile.cohort_size")
    omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    return _standard(omitted)


def _program_cost(spec: dict) -> tuple[int | None, dict]:
    if spec["degree_type"] == "bachelors":
        return _UG_TUITION, _undergrad_cost()
    # Master's AND the paid professional doctorate (the Ed.D., kept degree_type "phd" for doctoral
    # matching) bill per credit at a published rate and are not funded, so they carry a computed
    # annual scalar. Funded research doctorates omit the figure with a reason.
    if _is_paid_grad(spec):
        annual = _grad_annual(spec)
        return annual, _grad_cost(spec, annual)
    return None, _doctoral_omit_cost(spec)


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich Lehigh to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Lehigh is absent - safe on fresh/CI databases.
    """
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    school_outcomes["_standard"] = _standard(_OMITTED_INSTITUTION)
    inst.school_outcomes = school_outcomes
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    inst.founded_year = 1865
    inst.campus_setting = "suburban"
    if not inst.website_url:
        inst.website_url = "https://www.lehigh.edu"
    photos = SCHOOL_OUTCOMES["campus_photos"]
    if photos:
        hero = photos[0]["url"]
        gallery = [u for u in (inst.media_gallery or []) if u != hero]
        inst.media_gallery = [hero, *gallery]
    inst.content_sources = _INSTITUTION_CONTENT
    session.flush()
    school_by_name = _apply_schools(session, inst)
    _apply_programs(session, inst, school_by_name)
    session.flush()
    return True


def _apply_schools(session: Session, inst: Institution) -> dict[str, School]:
    existing = {
        s.name: s for s in session.scalars(select(School).where(School.institution_id == inst.id))
    }
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
        sc.website_url = _SCHOOL_WEBSITE.get(spec["name"])
        about = dict(_ABOUT_DETAIL.get(spec["name"], {}))
        about["source"] = {"label": "Lehigh University - Academics", "url": "https://www2.lehigh.edu/academics"}
        about["_standard"] = _standard(_ABOUT_OMITTED[spec["name"]])
        sc.about_detail = about
        sc.content_sources = _school_content(spec["name"])
        by_name[spec["name"]] = sc
    for name, sc in existing.items():
        if name not in canonical_names:
            session.delete(sc)
    session.flush()
    return by_name


def _program_has_dependents(session: Session, program_id) -> bool:
    fks = session.execute(
        text("""
        SELECT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND ccu.table_name = 'programs' AND ccu.column_name = 'id' AND tc.table_name <> 'programs'
        """)
    ).fetchall()
    for table, col in fks:
        if session.execute(
            text(f'SELECT 1 FROM "{table}" WHERE "{col}" = :pid LIMIT 1'), {"pid": program_id}
        ).first():
            return True
    return False


def _apply_programs(session: Session, inst: Institution, school_by_name: dict[str, School]) -> None:
    existing = {
        p.slug: p
        for p in session.scalars(select(Program).where(Program.institution_id == inst.id))
        if p.slug
    }
    canonical = set(PROGRAM_SLUGS)
    for spec in PROGRAMS:
        slug = spec["slug"]
        p = existing.get(slug)
        if p is None:
            p = Program(
                institution_id=inst.id,
                program_name=spec["program_name"],
                degree_type=spec["degree_type"],
                slug=slug,
            )
            session.add(p)
        p.program_name = spec["program_name"]
        p.degree_type = spec["degree_type"]
        p.department = spec["department"]
        p.duration_months = spec["duration_months"]
        p.description_text = spec["description"]
        p.website_url = _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec["delivery_format"]
        p.content_sources = _program_content(spec["school"], _program_keywords(spec))
        tuition, cost = _program_cost(spec)
        p.tuition = tuition
        p.cost_data = cost
        p.cip_code = spec["cip"]
        p.application_requirements = _requirements_for(spec)
        outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(spec)
        p.outcomes_data = outcomes
        p.tracks = spec.get("tracks")
        p.class_profile = None
        p.faculty_contacts = None
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        p.who_its_for = _who_its_for(spec)
        p.highlights = None
        p.application_deadline = date(2027, 1, 1) if spec["degree_type"] == "bachelors" else None
    session.flush()
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
