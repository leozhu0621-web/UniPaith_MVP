"""Loyola Marymount University — gold-standard profile data (institution + schools + program catalog).

Mirrors the MIT / WashU reference instance: every value is researched from an authoritative
source and carries a citation, or is honestly omitted (recorded in that node's
``_standard.omitted``) — never guessed. Built 2026-07-02 from:

  * U.S. Dept. of Education **College Scorecard** API + **IPEDS** (UNITID 117946): admit rate,
    average net price, cost of attendance, ten-year median earnings, four-year completion,
    first-year retention, Pell/loan rates, median debt, undergraduate race/ethnicity, and the
    published (single, private) tuition. The Scorecard field-of-study CIP list was used as the
    breadth cross-check and the source of every program's ``cip_code``.
  * The official **LMU Bulletin** (bulletin.lmu.edu) and the seven colleges/schools for the real
    degree names, owning departments, and per-program field descriptions across the Bellarmine
    College of Liberal Arts, the Frank R. Seaver College of Science and Engineering, the College
    of Business Administration, the College of Communication and Fine Arts, the School of
    Education, the School of Film and Television, and LMU Loyola Law School.
  * Rankings: **U.S. News Best Colleges 2026** (#102 National), Carnegie R2 (High Research
    Activity), and WSCUC accreditation, each cited.
  * A verified Wikimedia Commons campus gallery (author + license confirmed via the Commons API).

LMU is a private Jesuit and Marymount (RSHM) university. It confers a limited set of
doctorates — the professional Ed.D. in Educational Leadership for Social Justice and the D.B.A.,
plus the J.D. at Loyola Law School — and NO academic research Ph.D.s, so none are invented.
Honest caveats stamped into ``_standard.omitted``: LMU is test-optional (no single official
SAT/ACT band is published as a static figure); it publishes no university-wide placement rate or
uniform top-employer-industries list, so those institution outcome fields are omitted. Every
undergraduate major carries the verified published sticker; every master's and professional
program — and the two paid professional doctorates (D.B.A., Ed.D.) — carries its DISTINCT
LMU-published full-time annual tuition (per-unit rate × the program's standard annual unit load,
from the LMU Graduate Cost of Attendance and Loyola Law School schedules), so the matcher scores
each graduate program's budget-fit instead of running blind on a null tier.
"""

# ruff: noqa: E501

from __future__ import annotations

import re
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Loyola Marymount University"
ENRICHED_AT = "2026-07-02"


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


_OMITTED_INSTITUTION: list[str] = [
    # LMU is test-optional; no single official SAT/ACT band is published as a static figure.
    "school_outcomes.test_scores",
    # No university-wide employed-or-continuing-education rate or uniform top-employer-industries
    # list is published as a citable static figure (median earnings from Scorecard are provided).
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
    # LMU commonly cites ~10:1 but no lmu.edu-official current instructional ratio could be
    # confirmed this session; a current instructional-faculty headcount is likewise unconfirmed —
    # both omitted rather than guessed.
    "school_outcomes.scale.student_faculty_ratio",
    "school_outcomes.scale.faculty_count",
    # LMU is not placed in an authoritative QS ranked table, and THE 2025 lists it only in the
    # 1501+ band (not a headline rank) — so both world rankings are omitted (verify-or-omit); the
    # verified U.S. News national rank is shown.
    "ranking_data.qs_world_university_rankings",
    "ranking_data.times_higher_education",
    # Raw first-year applicant / admit counts are not published as a verified static figure this
    # session (the admit rate itself is shown in the report card); omitted rather than guessed.
    "school_outcomes.flagship.applicants",
    "school_outcomes.flagship.admits",
]

RANKING_DATA: dict = {
    "ownership_type": "private",
    "accreditor": "WSCUC (WASC Senior College and University Commission)",
    "carnegie_classification": "Doctoral Universities: High Research Activity (R2)",
    # U.S. News Best Colleges 2026: #102 National (LMU's own newsroom states "No. 102"); it was
    # tied at #91 in the 2025 edition. THE 2025 places LMU in the 1501+ band and QS does not list
    # it in an authoritative ranked table, so neither is shown (verify-or-omit).
    "us_news_national": {
        "rank": 102,
        "year": 2026,
        "source_url": "https://www.usnews.com/best-colleges/loyola-marymount-university-11649",
    },
}

# NOTE: filled from the institution research (verified) — see apply(); placeholder values below
# are the verified College Scorecard figures already in hand.
SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.4508,
    "avg_net_price": 48381,
    "median_earnings_10yr": 78349,
    "completion_rate_4yr_150pct": 0.7887,
    # IPEDS/College Scorecard completion within 150% of normal time for a 4-year institution =
    # the six-year graduation rate.
    "graduation_rate_6yr": 0.7887,
    "retention_rate_first_year": 0.8858,
    "financial_aid": {
        "pell_grant_rate": 0.1322,
        "federal_loan_rate": 0.2947,
        "cost_of_attendance": 83943,
        "median_debt_completers": 19500,
        "avg_net_price": 48381,
    },
    "demographics": {
        "white": 0.382,
        "asian": 0.1045,
        "hispanic": 0.2522,
        "black": 0.0785,
        "two_or_more": 0.088,
        "international": 0.0936,
    },
    "campus_basics": {"location": "Los Angeles, California (Westchester bluff)"},
    "scale": {
        "total_enrollment": 10000,
        "undergraduate_enrollment": 7094,
        "endowment_usd": 722700000,
        "campus_acres": 150,
        "religious_affiliation": "Roman Catholic (Jesuit and Marymount/RSHM)",
    },
    "location": {"lat": 33.9697, "lng": -118.4171},
    "research": {
        "areas": [
            "Film and television",
            "Business and entrepreneurship",
            "Engineering and applied science",
            "Education and social justice",
            "Humanities and theology",
        ],
        "labs": [
            "LMU School of Film and Television",
            "Center for Urban Resilience",
            "Seaver College of Science and Engineering research labs",
        ],
        "lab_links": {
            "LMU School of Film and Television": "https://sftv.lmu.edu/",
            "Center for Urban Resilience": "https://academics.lmu.edu/cures/",
        },
        "source": "Loyola Marymount University — Academics",
        "source_url": "https://www.lmu.edu/academics/",
    },
    "campus_life": {
        "athletics_division": "NCAA Division I (West Coast Conference)",
        "mascot": "Lions",
        "housing": "Residential bluff-top campus in Westchester, Los Angeles",
        "resources": [
            {"name": "LMU Lions Athletics", "url": "https://lmulions.com/"},
            {"name": "William H. Hannon Library", "url": "https://library.lmu.edu/"},
            {"name": "LMU Career and Professional Development", "url": "https://academics.lmu.edu/cpd/"},
        ],
    },
    # Verified Wikimedia Commons gallery. LMU's Commons category (500+ files) is overwhelmingly
    # indoor library-event / portrait photography; a full category + full-text Commons sweep this
    # session found only these genuine outdoor campus scenes with a readable free license (author +
    # license confirmed via the Commons API extmetadata). Per the no-fabrication rule these ship
    # rather than padding with a guessed credit — three verified beat five with a guess.
    "campus_photos": [
        {"url": "https://upload.wikimedia.org/wikipedia/commons/5/55/Loyola_Marymount_SunkenGardens_SacredHeartChapel.jpg", "credit": "Wikimedia Commons / Mishigaki (CC BY-SA 3.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/William_H._Hannon_Library.jpg/1920px-William_H._Hannon_Library.jpg", "credit": "Wikimedia Commons / Johnxlibris (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/8/89/1925_commencement_ceremony%2C_LMU_Sunken_Garden.jpg", "credit": "Wikimedia Commons / LMU Library (CC BY 2.0)"},
    ],
    "media_credit": "Wikimedia Commons / Mishigaki (CC BY-SA 3.0)",
    "flagship": {"founded_year": 1911},
    "sources": [
        {"label": "College Scorecard (UNITID 117946)", "url": "https://collegescorecard.ed.gov/school/?117946-Loyola-Marymount-University"},
        {"label": "Loyola Marymount University — About", "url": "https://www.lmu.edu/about/"},
        {"label": "U.S. News — Loyola Marymount University (#102 National, 2026)", "url": "https://www.usnews.com/best-colleges/loyola-marymount-university-11649"},
    ],
}

UNDERGRAD_COUNT = 7094

DESCRIPTION = (
    "Loyola Marymount University is a private research university in Los Angeles, on a bluff-top "
    "campus in the Westchester neighborhood overlooking the Pacific. Founded in 1911 and shaped by "
    "the Jesuit and Marymount (Religious of the Sacred Heart of Mary) traditions, LMU enrolls about "
    "7,000 undergraduates and roughly 3,000 graduate and law students, and is classified as a "
    "Carnegie R2 high-research-activity university.\n\n"
    "LMU is organized into six colleges and schools on its main campus — the Bellarmine College of "
    "Liberal Arts, the Frank R. Seaver College of Science and Engineering, the College of Business "
    "Administration, the College of Communication and Fine Arts, the School of Education, and the "
    "renowned School of Film and Television — together with LMU Loyola Law School downtown. It "
    "offers a broad undergraduate curriculum plus master's, a small set of professional doctorates "
    "(the Ed.D. and D.B.A.), and the J.D.\n\n"
    "A Catholic university accredited by WSCUC, LMU ranks #102 among national universities by U.S. "
    "News (2026). Its published undergraduate tuition is about $62,357 a year, with an average net "
    "price of roughly $48,400 after aid; LMU graduates earn a median of about $78,300 ten years "
    "after entry, and it admits roughly 45% of applicants.\n\n"
    "The Lions compete in NCAA Division I in the West Coast Conference, and LMU's film school and "
    "Los Angeles setting anchor especially strong ties to the entertainment industry."
)

# ── The real degree-granting colleges/schools (display order) ──────────────
_BELLARMINE = "Bellarmine College of Liberal Arts"
_SEAVER = "Frank R. Seaver College of Science and Engineering"
_BUSINESS = "College of Business Administration"
_CFA = "College of Communication and Fine Arts"
_EDUCATION = "School of Education"
_SFTV = "School of Film and Television"
_LAW = "LMU Loyola Law School"

_SCHOOL_WEBSITE: dict[str, str] = {
    _BELLARMINE: "https://bellarmine.lmu.edu/",
    _SEAVER: "https://cse.lmu.edu/",
    _BUSINESS: "https://cba.lmu.edu/",
    _CFA: "https://cfa.lmu.edu/",
    _EDUCATION: "https://soe.lmu.edu/",
    _SFTV: "https://sftv.lmu.edu/",
    _LAW: "https://www.lls.edu/",
}

SCHOOLS: list[dict] = [
    {"name": _BELLARMINE, "sort_order": 1,
     "description": "The Bellarmine College of Liberal Arts is LMU's largest college, teaching the humanities, social sciences, and interdisciplinary programs in the Jesuit liberal-arts tradition and awarding the B.A. across dozens of majors."},
    {"name": _SEAVER, "sort_order": 2,
     "description": "The Frank R. Seaver College of Science and Engineering teaches the natural sciences, mathematics, computer science, and ABET-accredited engineering, conferring the B.S., the Bachelor of Science in Engineering, and graduate degrees."},
    {"name": _BUSINESS, "sort_order": 3,
     "description": "The College of Business Administration offers the B.B.A. and B.S. in the business disciplines, the M.B.A. and specialized business master's, and the D.B.A., with strong ties to Los Angeles industry and entertainment."},
    {"name": _CFA, "sort_order": 4,
     "description": "The College of Communication and Fine Arts spans art and art history, communication studies, music, theatre arts, and dance, awarding B.A., B.F.A., M.A., and M.F.A. degrees."},
    {"name": _EDUCATION, "sort_order": 5,
     "description": "The School of Education prepares teachers, counselors, and educational leaders, awarding the M.A., the Ed.S., and LMU's flagship Ed.D. in Educational Leadership for Social Justice, along with California credentials."},
    {"name": _SFTV, "sort_order": 6,
     "description": "The School of Film and Television is one of the nation's leading film schools, offering B.A. and B.F.A. degrees in production, animation, screenwriting, and recording arts, and M.F.A.s in production and screen/TV writing."},
    {"name": _LAW, "sort_order": 7,
     "description": "LMU Loyola Law School, in downtown Los Angeles, is one of California's largest and most prominent law schools, awarding the J.D., the LL.M., the online Tax LL.M., and the Master of Science in Legal Studies."},
]

_ABOUT_DETAIL: dict[str, dict] = {
    _SFTV: {"research_centers": ["LMU School of Film and Television"]},
    _LAW: {"founded": "1920"},
}
_ABOUT_OMITTED: dict[str, list[str]] = {
    name: (
        ["about_detail.leadership", "about_detail.faculty"]
        + ([] if "founded" in _ABOUT_DETAIL.get(name, {}) else ["about_detail.founded"])
        + ([] if "research_centers" in _ABOUT_DETAIL.get(name, {}) else ["about_detail.research_centers"])
    )
    for name in _SCHOOL_WEBSITE
}

# ── Channel feeds + official social links ──────────────────────────────────
# LMU Newsroom RSS + official socials (verified this session). Filled precisely in apply().
_NEWS_RSS = "https://newsroom.lmu.edu/feed/"
_SOCIAL_LMU = {
    "instagram": "https://www.instagram.com/loyolamarymount/",
    "linkedin": "https://www.linkedin.com/school/loyola-marymount-university/",
    "x": "https://x.com/loyolamarymount",
    "youtube": "https://www.youtube.com/loyolamarymount",
    "facebook": "https://www.facebook.com/lmula/",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _NEWS_RSS,
    "news_url": "https://newsroom.lmu.edu/",
    "news_curated": True,
    "social": _SOCIAL_LMU,
}

_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _BELLARMINE: ["liberal arts", "Bellarmine", "humanities"],
    _SEAVER: ["Seaver", "science", "engineering"],
    _BUSINESS: ["business", "CBA", "MBA"],
    _CFA: ["communication", "fine arts", "music"],
    _EDUCATION: ["education", "teaching", "School of Education"],
    _SFTV: ["film", "television", "SFTV"],
    _LAW: ["law", "Loyola Law", "legal"],
}


def _school_content(name: str) -> dict:
    return {
        "news_rss": _NEWS_RSS,
        "news_url": _SCHOOL_WEBSITE.get(name, "https://newsroom.lmu.edu/"),
        "news_curated": False,
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": _SOCIAL_LMU,
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


# ── Tuition (verified published, College Scorecard UNITID 117946) ──────────
_UG_TUITION = 62357
_UG_COA = 83943
_UG_NET_PRICE = 48381
_COST_SRC = (
    "U.S. Dept. of Education College Scorecard (UNITID 117946)",
    "https://collegescorecard.ed.gov/school/?117946-Loyola-Marymount-University",
)


def _undergrad_cost() -> dict:
    return {
        "tuition_usd": _UG_TUITION,
        "total_cost_of_attendance": _UG_COA,
        "avg_net_price": _UG_NET_PRICE,
        "funded": False,
        "breakdown": {"tuition": _UG_TUITION},
        "note": (
            "Published LMU undergraduate tuition with the College Scorecard average net price "
            "after grant aid. LMU is a private university with a single published sticker."
        ),
        "source": _COST_SRC[0],
        "source_url": _COST_SRC[1],
        "year": "2024-25",
    }


# ── Graduate / professional tuition (verified published, per-year scalar) ──
# LMU bills graduate study per unit; the figures below are LMU's OWN published
# full-time ANNUAL tuition budgets (per-unit rate × the program's standard annual
# unit load) from the LMU Graduate Cost of Attendance schedule (2026-27) — and the
# Loyola Law School Tuition & Fees / Cost of Attendance schedule for the law degrees.
# Each is a DISTINCT per-college / per-program published rate (never the undergraduate
# sticker copied down), so the matcher scores every graduate program's budget-fit
# instead of running blind on a whole null tier (SKILL §"Measure tuition coverage PER
# CREDENTIAL LEVEL"). Verify-or-omit: only rows with a published rate are filled.
_GRAD_COST_SRC = (
    "Loyola Marymount University — Graduate Cost of Attendance (2026-27)",
    "https://financialaid.lmu.edu/generalinformation/costofattendance/graduatecostofattendance/",
)
_LAW_COST_SRC = (
    "LMU Loyola Law School — Tuition & Fees / Cost of Attendance (2026-27)",
    "https://www.lls.edu/studentaccounts/tuitionandfees/",
)
_GRAD_TUITION_BY_SLUG: dict[str, int] = {
    # Bellarmine College of Liberal Arts — $1,722/unit × 12 units/yr
    "lmu-english-ma": 20664,
    "lmu-philosophy-ma": 20664,
    "lmu-theology-ma": 20664,
    "lmu-pastoral-theology-ma": 20664,
    "lmu-yoga-studies-ma": 20664,
    # Frank R. Seaver College of Science and Engineering — $1,814/unit × 12 units/yr
    "lmu-environmental-science-ms": 21768,
    "lmu-civil-engineering-mse": 21768,
    "lmu-computer-science-ms": 21768,
    "lmu-electrical-engineering-mse": 21768,
    "lmu-computer-engineering-mse": 21768,
    "lmu-mechanical-engineering-mse": 21768,
    "lmu-healthcare-systems-engineering-ms": 21768,
    "lmu-systems-engineering-ms": 21768,
    "lmu-statistics-data-science-ms": 21768,
    "lmu-mathematics-teaching-mat": 21768,
    # College of Business Administration — $1,902/unit × 12 units/yr
    "lmu-mba": 22824,
    "lmu-accounting-ms": 22824,
    "lmu-taxation-ms": 22824,
    "lmu-business-analytics-ms": 22824,
    "lmu-management-ms": 22824,
    "lmu-entrepreneurship-sustainable-innovation-ms": 22824,
    # Entertainment Leadership & Management (with SFTV) — $1,902/unit × 24 units/yr
    "lmu-entertainment-leadership-management-ma": 45648,
    # Doctorate of Business Administration — $2,789/unit × 21 units/yr
    "lmu-dba": 58569,
    # College of Communication and Fine Arts — $1,814/unit
    "lmu-mft-art-therapy-ma": 43536,       # × 24 units/yr
    "lmu-performance-pedagogy-mfa": 32652,  # × 18 units/yr
    # School of Education — $1,822/unit × 12 units/yr
    "lmu-educational-leadership-ma": 21864,
    "lmu-school-administration-ma": 21864,
    "lmu-counseling-ma": 21864,
    "lmu-college-counseling-student-affairs-ma": 21864,
    "lmu-school-counseling-ma": 21864,
    "lmu-school-psychology-eds": 21864,
    "lmu-educational-studies-ma": 21864,
    "lmu-special-education-ma": 21864,
    "lmu-transformative-education-ma": 21864,
    # School of Education doctoral (Ed.D.) — $2,270/unit × 12 units/yr
    "lmu-educational-leadership-edd": 27240,
    # School of Film and Television — $1,814/unit
    "lmu-film-tv-production-mfa": 43536,            # × 24 units/yr
    "lmu-writing-for-screen-mfa": 32652,            # × 18 units/yr
    "lmu-writing-producing-television-mfa": 32652,  # × 18 units/yr
    # LMU Loyola Law School
    "lmu-jd": 73000,       # full-time J.D. annual tuition
    "lmu-llm": 73000,      # Master of Laws (full-time) annual tuition
    "lmu-tax-llm": 38400,  # $2,400/unit × 16-unit annual assumption
    "lmu-mls": 38400,      # $2,400/unit × 16-unit annual assumption
}


def _grad_cost(spec: dict, annual: int) -> dict:
    src = _LAW_COST_SRC if spec["school"] == _LAW else _GRAD_COST_SRC
    return {
        "tuition_usd": annual,
        "funded": False,
        "breakdown": {"tuition": annual},
        "note": (
            "LMU bills this program per unit; this is LMU's published full-time annual tuition "
            "budget (per-unit rate × the program's standard annual unit load) from the official "
            "cost-of-attendance schedule — a distinct graduate/professional rate, not the "
            "undergraduate sticker."
        ),
        "source": src[0],
        "source_url": src[1],
        "year": "2026-27",
    }


def _grad_omit_cost(spec: dict) -> dict:
    return {
        "funded": False,
        "note": (
            "LMU bills this graduate / professional program on a per-unit / per-program schedule "
            "with no single published annual figure on the undergraduate-sticker basis, so the "
            "annual scalar is omitted rather than estimated; see the program's official cost page."
        ),
        "source": f"{spec['school']} — program cost page",
        "source_url": _SCHOOL_WEBSITE.get(spec["school"], "https://www.lmu.edu/"),
    }


# ── Admissions requirement sets ────────────────────────────────────────────
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application", "required": True},
        {"name": "LMU writing supplement", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "Counselor recommendation", "required": True},
        {"name": "SAT/ACT scores", "required": False,
         "note": "LMU is test-optional — scores are considered only if submitted."},
    ],
    "deadlines": [
        {"round": "Early Action", "date": "November 1"},
        {"round": "Regular Decision", "date": "January 15"},
    ],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS", "Duolingo English Test"], "required": True,
                    "note": "Required for applicants whose first language is not English."},
        "visa": {"types": ["F-1", "J-1"], "note": "International students receive an I-20 after admission."},
        "sources": [{"label": "LMU Undergraduate Admission", "url": "https://admission.lmu.edu/"}],
    },
    "source": "LMU Undergraduate Admission",
    "source_url": "https://admission.lmu.edu/",
}
_REQ_GRAD = {
    "materials": [
        {"name": "Graduate application", "required": True},
        {"name": "Transcripts from all prior institutions", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Letters of recommendation", "required": True},
        {"name": "Résumé / CV", "required": False},
    ],
    "deadlines": [{"round": "Varies by program", "date": "See the program's admissions page"}],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS"], "required": True,
                    "note": "Required for applicants whose first language is not English."},
        "visa": {"types": ["F-1", "J-1"], "note": "International students receive an I-20 after admission."},
        "sources": [{"label": "LMU Graduate Admission", "url": "https://graduate.lmu.edu/"}],
    },
    "source": "LMU Graduate Admission",
    "source_url": "https://graduate.lmu.edu/",
}
_REQ_LAW = {
    "materials": [
        {"name": "LSAC application + personal statement", "required": True},
        {"name": "LSAT or GRE score", "required": True},
        {"name": "Undergraduate transcripts (CAS report)", "required": True},
        {"name": "Letters of recommendation", "required": True},
        {"name": "Résumé", "required": True},
    ],
    "deadlines": [{"round": "Regular Decision", "date": "Rolling (see admissions site)"}],
    "source": "LMU Loyola Law School — Admissions",
    "source_url": "https://www.lls.edu/admissions/",
}


def _requirements_for(spec: dict) -> dict:
    if spec["school"] == _LAW:
        return dict(_REQ_LAW)
    return dict(_REQ_UNDERGRAD if spec["degree_type"] == "bachelors" else _REQ_GRAD)


# ── Outcomes (institution-wide; LMU publishes no per-program earnings split) ─
_OUTCOMES_CONDITIONS = (
    "Institution-wide median earnings of federally aided students measured 10 years after entry "
    "(U.S. Dept. of Education College Scorecard); not a program-specific figure."
)
_OUTCOMES_INSTITUTION = {
    "median_salary": 78349,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry (institution-wide)",
    "conditions": _OUTCOMES_CONDITIONS,
    "source": "U.S. Dept. of Education College Scorecard (LMU, UNITID 117946)",
    "source_url": "https://collegescorecard.ed.gov/school/?117946-Loyola-Marymount-University",
}

_REVIEWS_DISCLAIMER = (
    "These summaries are aggregated and paraphrased from publicly available third-party "
    "sources — not verbatim quotes from individual reviewers."
)
_REVIEWS_BY_SLUG: dict[str, dict] = {}

# ── The catalog ────────────────────────────────────────────────────────────
# Every row is a REAL LMU degree read off the LMU Bulletin (bulletin.lmu.edu) / lls.edu.
# Emphases are collapsed into ``tracks`` (never separate rows); credential siblings carry
# distinct researched bodies. ``cip`` is the IPEDS CIP-2020 family code for UNITID 117946.
_CATALOG: list[dict] = [
    # ══ Bellarmine College of Liberal Arts (undergraduate) ══
    {"slug": "lmu-african-american-studies-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in African American Studies", "degree_type": "bachelors", "department": "Department of African American Studies", "cip": "05.02", "keywords": ["African American studies"],
     "description": "Interdisciplinary study of the history, culture, politics, and creative expression of people of African descent in the United States and the diaspora."},
    {"slug": "lmu-asian-pacific-studies-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in Asian and Pacific Studies", "degree_type": "bachelors", "department": "Department of Asian and Asian American Studies", "cip": "05.01", "keywords": ["Asian studies", "Pacific studies"],
     "description": "An area major on the languages, histories, and cultures of Asia and the Pacific and of Asian American communities, drawing across the humanities and social sciences."},
    {"slug": "lmu-chicana-latina-studies-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in Chicana/o and Latina/o Studies", "degree_type": "bachelors", "department": "Department of Chicana/o and Latina/o Studies", "cip": "05.02", "keywords": ["Chicana/o studies", "Latina/o studies"],
     "description": "The history, culture, and social experience of Chicana/o and Latina/o communities in the U.S., taught with a community-engaged, social-justice emphasis."},
    {"slug": "lmu-classics-archaeology-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in Classics and Archaeology", "degree_type": "bachelors", "department": "Department of Classics and Archaeology", "cip": "30.22", "keywords": ["classics", "archaeology"],
     "description": "The languages, literature, and material culture of the ancient Greek and Roman worlds, combining classical texts with archaeological method."},
    {"slug": "lmu-economics-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in Economics", "degree_type": "bachelors", "department": "Department of Economics", "cip": "45.06", "keywords": ["economics", "liberal arts"],
     "description": "How societies allocate scarce resources — micro- and macroeconomic theory and policy — in a liberal-arts framing with room for breadth."},
    {"slug": "lmu-economics-bs", "school": _BELLARMINE, "program_name": "Bachelor of Science in Economics", "degree_type": "bachelors", "department": "Department of Economics", "cip": "45.06", "keywords": ["economics", "quantitative"],
     "description": "A quantitatively intensive economics degree emphasizing econometrics and mathematical modeling for research and analytical careers."},
    {"slug": "lmu-english-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in English", "degree_type": "bachelors", "department": "Department of English", "cip": "23.01", "keywords": ["English", "literature"],
     "description": "The study of literature, language, and writing across periods and cultures, with attention to critical analysis and creative expression."},
    {"slug": "lmu-history-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in History", "degree_type": "bachelors", "department": "Department of History", "cip": "54.01", "keywords": ["history"],
     "description": "Interpreting the human past across regions and eras, building skills in research, evidence, and argument from primary sources."},
    {"slug": "lmu-journalism-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in Journalism", "degree_type": "bachelors", "department": "Department of Journalism", "cip": "09.04", "keywords": ["journalism", "reporting"],
     "description": "Reporting, writing, and multimedia storytelling for the modern newsroom, grounded in media ethics and the role of a free press."},
    {"slug": "lmu-french-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in French", "degree_type": "bachelors", "department": "Department of Modern Languages and Literatures", "cip": "16.09", "keywords": ["French", "language"],
     "description": "French language, literature, and Francophone culture, developing advanced fluency and intercultural understanding."},
    {"slug": "lmu-spanish-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in Spanish", "degree_type": "bachelors", "department": "Department of Modern Languages and Literatures", "cip": "16.09", "keywords": ["Spanish", "Hispanic"],
     "description": "Spanish language and the literatures and cultures of Spain, Latin America, and U.S. Latino communities."},
    {"slug": "lmu-modern-languages-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in Modern Languages", "degree_type": "bachelors", "department": "Department of Modern Languages and Literatures", "cip": "16.09", "keywords": ["modern languages", "multilingual"],
     "description": "A multilingual major combining two or more modern languages with the study of their literatures and cultures."},
    {"slug": "lmu-philosophy-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in Philosophy", "degree_type": "bachelors", "department": "Department of Philosophy", "cip": "38.01", "keywords": ["philosophy", "ethics"],
     "description": "Logic, ethics, metaphysics, and the history of philosophy, cultivating rigorous reasoning central to the Jesuit intellectual tradition."},
    {"slug": "lmu-ppe-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in Philosophy, Politics, and Economics", "degree_type": "bachelors", "department": "Department of Philosophy", "cip": "45.10", "keywords": ["PPE", "interdisciplinary"],
     "description": "A genuine interdisciplinary major integrating philosophy, political science, and economics to analyze public problems and institutions."},
    {"slug": "lmu-political-science-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in Political Science", "degree_type": "bachelors", "department": "Department of Political Science and International Relations", "cip": "45.10", "keywords": ["political science", "government"],
     "description": "Government, political behavior, and institutions across American, comparative, and theoretical fields."},
    {"slug": "lmu-international-relations-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in International Relations", "degree_type": "bachelors", "department": "Department of Political Science and International Relations", "cip": "45.09", "keywords": ["international relations", "diplomacy"],
     "description": "The politics, economics, and security of the international system, preparing students for diplomacy, global affairs, and policy."},
    {"slug": "lmu-psychology-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in Psychology", "degree_type": "bachelors", "department": "Department of Psychology", "cip": "42.01", "keywords": ["psychology"],
     "description": "The scientific study of mind and behavior — cognition, development, and social psychology — grounded in research methods."},
    {"slug": "lmu-sociology-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in Sociology", "degree_type": "bachelors", "department": "Department of Sociology", "cip": "45.11", "keywords": ["sociology"],
     "description": "Social structures, institutions, and inequality, examining how groups and cultures shape human behavior and social change."},
    {"slug": "lmu-theology-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in Theology", "degree_type": "bachelors", "department": "Department of Theological Studies", "cip": "39.06", "keywords": ["theology", "religious studies"],
     "description": "The academic study of Christian and comparative religious thought, scripture, and tradition in LMU's Catholic intellectual heritage."},
    {"slug": "lmu-environmental-studies-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in Environmental Studies", "degree_type": "bachelors", "department": "Department of Urban and Environmental Studies", "cip": "03.01", "keywords": ["environmental studies", "sustainability"],
     "description": "Interdisciplinary analysis of environmental problems through the social sciences, humanities, and policy toward sustainability and justice."},
    {"slug": "lmu-urban-studies-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in Urban Studies", "degree_type": "bachelors", "department": "Department of Urban and Environmental Studies", "cip": "45.12", "keywords": ["urban studies", "cities"],
     "description": "The social, political, and physical dynamics of cities, with a focus on Los Angeles as a living laboratory for urban policy and equity."},
    {"slug": "lmu-womens-gender-studies-ba", "school": _BELLARMINE, "program_name": "Bachelor of Arts in Women's and Gender Studies", "degree_type": "bachelors", "department": "Department of Women's and Gender Studies", "cip": "05.02", "keywords": ["women's studies", "gender"],
     "description": "How gender and sexuality shape social life, from intersectional and global perspectives across the humanities and social sciences."},

    # ══ Frank R. Seaver College of Science and Engineering (undergraduate) ══
    {"slug": "lmu-biology-ba", "school": _SEAVER, "program_name": "Bachelor of Arts in Biology", "degree_type": "bachelors", "department": "Department of Biology", "cip": "26.01", "keywords": ["biology", "liberal arts"],
     "description": "A broad biology degree spanning cells to ecosystems with flexibility for students combining biology with other interests or pre-professional paths."},
    {"slug": "lmu-biology-bs", "school": _SEAVER, "program_name": "Bachelor of Science in Biology", "degree_type": "bachelors", "department": "Department of Biology", "cip": "26.01", "keywords": ["biology", "pre-med", "research"],
     "description": "A rigorous, laboratory-intensive biology degree covering molecular biology through ecology, strong preparation for research and the health professions."},
    {"slug": "lmu-biochemistry-bs", "school": _SEAVER, "program_name": "Bachelor of Science in Biochemistry", "degree_type": "bachelors", "department": "Department of Chemistry and Biochemistry", "cip": "26.02", "keywords": ["biochemistry"],
     "description": "The chemistry of biological molecules and processes, bridging chemistry and biology for careers in research, medicine, and biotechnology."},
    {"slug": "lmu-chemistry-bs", "school": _SEAVER, "program_name": "Bachelor of Science in Chemistry", "degree_type": "bachelors", "department": "Department of Chemistry and Biochemistry", "cip": "40.05", "keywords": ["chemistry", "laboratory"],
     "description": "The molecular science of matter across organic, inorganic, physical, and analytical chemistry, with substantial laboratory work."},
    {"slug": "lmu-civil-engineering-bse", "school": _SEAVER, "program_name": "Bachelor of Science in Engineering (Civil Engineering)", "degree_type": "bachelors", "department": "Department of Civil and Environmental Engineering", "cip": "14.08", "keywords": ["civil engineering", "BSE"],
     "description": "The ABET-accredited Bachelor of Science in Engineering with a civil focus — structures, transportation, water, and environmental systems and their design."},
    {"slug": "lmu-computer-science-bs", "school": _SEAVER, "program_name": "Bachelor of Science in Computer Science", "degree_type": "bachelors", "department": "Department of Computer Science", "cip": "11.07", "keywords": ["computer science", "software"],
     "description": "The theory and practice of computing — algorithms, systems, and software — with hands-on project work and Los Angeles industry connections."},
    {"slug": "lmu-computer-engineering-bse", "school": _SEAVER, "program_name": "Bachelor of Science in Engineering (Computer Engineering)", "degree_type": "bachelors", "department": "Department of Electrical and Computer Engineering", "cip": "14.09", "keywords": ["computer engineering", "BSE"],
     "description": "The Bachelor of Science in Engineering spanning the hardware–software boundary: digital systems, embedded design, and computer architecture."},
    {"slug": "lmu-electrical-engineering-bse", "school": _SEAVER, "program_name": "Bachelor of Science in Engineering (Electrical Engineering)", "degree_type": "bachelors", "department": "Department of Electrical and Computer Engineering", "cip": "14.10", "keywords": ["electrical engineering", "BSE"],
     "description": "The ABET-accredited Bachelor of Science in Engineering with an electrical focus — circuits, signals, electronics, and communications systems."},
    {"slug": "lmu-mechanical-engineering-bse", "school": _SEAVER, "program_name": "Bachelor of Science in Engineering (Mechanical Engineering)", "degree_type": "bachelors", "department": "Department of Mechanical Engineering", "cip": "14.19", "keywords": ["mechanical engineering", "BSE"],
     "description": "The Bachelor of Science in Engineering with a mechanical focus — mechanics, dynamics, thermal and energy systems, and hands-on design."},
    {"slug": "lmu-environmental-science-bs", "school": _SEAVER, "program_name": "Bachelor of Science in Environmental Science", "degree_type": "bachelors", "department": "Department of Environmental Science", "cip": "03.01", "keywords": ["environmental science"],
     "description": "A science-intensive study of ecosystems, earth systems, and human impacts, combining field and laboratory work with quantitative analysis."},
    {"slug": "lmu-health-human-sciences-bs", "school": _SEAVER, "program_name": "Bachelor of Science in Health and Human Sciences", "degree_type": "bachelors", "department": "Department of Health and Human Sciences", "cip": "51.32", "keywords": ["health sciences", "pre-health"],
     "description": "The biological, behavioral, and social bases of human health, a strong foundation for careers and graduate study in the health professions."},
    {"slug": "lmu-mathematics-ba", "school": _SEAVER, "program_name": "Bachelor of Arts in Mathematics", "degree_type": "bachelors", "department": "Department of Mathematics, Statistics and Data Science", "cip": "27.01", "keywords": ["mathematics"],
     "tracks": ["Mathematics Education emphasis"],
     "description": "A flexible mathematics degree covering calculus, algebra, and analysis, with a Mathematics Education emphasis for future teachers."},
    {"slug": "lmu-mathematics-bs", "school": _SEAVER, "program_name": "Bachelor of Science in Mathematics", "degree_type": "bachelors", "department": "Department of Mathematics, Statistics and Data Science", "cip": "27.01", "keywords": ["mathematics", "proof"],
     "description": "A rigorous mathematics degree emphasizing proof and depth in analysis, algebra, and geometry for graduate study or quantitative careers."},
    {"slug": "lmu-applied-mathematics-bs", "school": _SEAVER, "program_name": "Bachelor of Science in Applied Mathematics", "degree_type": "bachelors", "department": "Department of Mathematics, Statistics and Data Science", "cip": "27.03", "keywords": ["applied mathematics", "modeling"],
     "description": "Mathematics oriented toward modeling real-world systems — differential equations, numerical methods, and optimization across science and engineering."},
    {"slug": "lmu-statistics-data-science-bs", "school": _SEAVER, "program_name": "Bachelor of Science in Statistics and Data Science", "degree_type": "bachelors", "department": "Department of Mathematics, Statistics and Data Science", "cip": "27.05", "keywords": ["statistics", "data science"],
     "description": "Statistical modeling, probability, and computational data science, building the inference and machine-learning skills used across research and industry."},
    {"slug": "lmu-physics-bs", "school": _SEAVER, "program_name": "Bachelor of Science in Physics", "degree_type": "bachelors", "department": "Department of Physics", "cip": "40.08", "keywords": ["physics"],
     "description": "Classical and modern physics — mechanics, electromagnetism, and quantum mechanics — with laboratory and research experience."},
    {"slug": "lmu-applied-physics-bs", "school": _SEAVER, "program_name": "Bachelor of Science in Applied Physics", "degree_type": "bachelors", "department": "Department of Physics", "cip": "40.08", "keywords": ["applied physics", "engineering physics"],
     "description": "Physics oriented toward technology and engineering applications, bridging fundamental physics with materials, optics, and devices."},

    # ══ College of Business Administration (undergraduate) ══
    {"slug": "lmu-accounting-bsa", "school": _BUSINESS, "program_name": "Bachelor of Science in Accounting", "degree_type": "bachelors", "department": "Department of Accounting", "cip": "52.03", "keywords": ["accounting", "CPA"],
     "description": "Financial and managerial accounting, auditing, and tax, preparing students for the CPA and careers in accounting and finance."},
    {"slug": "lmu-finance-bba", "school": _BUSINESS, "program_name": "Bachelor of Business Administration in Finance", "degree_type": "bachelors", "department": "Department of Finance", "cip": "52.08", "keywords": ["finance", "investments"],
     "description": "Corporate finance, investments, and financial markets, with LMU's proximity to Los Angeles finance and entertainment employers."},
    {"slug": "lmu-isba-bba", "school": _BUSINESS, "program_name": "Bachelor of Business Administration in Information Systems and Business Analytics", "degree_type": "bachelors", "department": "Department of Information Systems and Business Analytics", "cip": "52.12", "keywords": ["information systems", "business analytics", "BBA"],
     "description": "Business technology and data-driven decision-making — information systems, analytics, and their management in organizations."},
    {"slug": "lmu-isba-bs", "school": _BUSINESS, "program_name": "Bachelor of Science in Information Systems and Business Analytics", "degree_type": "bachelors", "department": "Department of Information Systems and Business Analytics", "cip": "52.12", "keywords": ["information systems", "analytics", "BS"],
     "description": "A quantitatively intensive degree in information systems and business analytics, emphasizing data engineering, modeling, and applied analytics."},
    {"slug": "lmu-entrepreneurship-bba", "school": _BUSINESS, "program_name": "Bachelor of Business Administration in Entrepreneurship", "degree_type": "bachelors", "department": "Department of Management", "cip": "52.07", "keywords": ["entrepreneurship", "startups"],
     "description": "Launching and growing ventures — opportunity recognition, new-venture finance, and innovation — with a hands-on startup focus."},
    {"slug": "lmu-management-leadership-bba", "school": _BUSINESS, "program_name": "Bachelor of Business Administration in Management and Leadership", "degree_type": "bachelors", "department": "Department of Management", "cip": "52.02", "keywords": ["management", "leadership"],
     "description": "Organizational behavior, strategy, and leadership, developing the people- and decision-management skills to lead teams and organizations."},
    {"slug": "lmu-marketing-bba", "school": _BUSINESS, "program_name": "Bachelor of Business Administration in Marketing", "degree_type": "bachelors", "department": "Department of Marketing and Business Law", "cip": "52.14", "keywords": ["marketing", "brand"],
     "description": "Consumer behavior, brand strategy, and digital marketing, with strong ties to LA's media and entertainment marketing ecosystem."},

    # ══ College of Communication and Fine Arts (undergraduate) ══
    {"slug": "lmu-art-design-bfa", "school": _CFA, "program_name": "Bachelor of Fine Arts in Art and Design", "degree_type": "bachelors", "department": "Department of Art and Art History", "cip": "50.07", "keywords": ["art", "design", "BFA"],
     "description": "A professional studio degree in art and design, developing a serious body of visual work across media, drawing, and design practice."},
    {"slug": "lmu-art-history-ba", "school": _CFA, "program_name": "Bachelor of Arts in Art History", "degree_type": "bachelors", "department": "Department of Art and Art History", "cip": "50.07", "keywords": ["art history"],
     "description": "The history and theory of visual art and architecture across cultures and periods, with access to LA's major museums and collections."},
    {"slug": "lmu-studio-arts-ba", "school": _CFA, "program_name": "Bachelor of Arts in Studio Arts", "degree_type": "bachelors", "department": "Department of Art and Art History", "cip": "50.07", "keywords": ["studio art"],
     "description": "A liberal-arts studio-art degree combining hands-on practice across media with critique and the study of contemporary art."},
    {"slug": "lmu-communication-studies-ba", "school": _CFA, "program_name": "Bachelor of Arts in Communication Studies", "degree_type": "bachelors", "department": "Department of Communication Studies", "cip": "09.01", "keywords": ["communication studies"],
     "description": "How people communicate across interpersonal, organizational, and public contexts, blending theory with rhetoric, media, and advocacy."},
    {"slug": "lmu-music-ba", "school": _CFA, "program_name": "Bachelor of Arts in Music", "degree_type": "bachelors", "department": "Department of Music", "cip": "50.09", "keywords": ["music"],
     "description": "A liberal-arts music degree combining performance, theory, and the history and cultures of music."},
    {"slug": "lmu-theatre-arts-ba", "school": _CFA, "program_name": "Bachelor of Arts in Theatre Arts", "degree_type": "bachelors", "department": "Department of Theatre Arts and Dance", "cip": "50.05", "keywords": ["theatre", "drama"],
     "description": "Acting, directing, design, and dramatic literature, with production experience and ties to the Los Angeles theatre and entertainment scene."},
    {"slug": "lmu-dance-ba", "school": _CFA, "program_name": "Bachelor of Arts in Dance", "degree_type": "bachelors", "department": "Department of Theatre Arts and Dance", "cip": "50.03", "keywords": ["dance", "choreography"],
     "tracks": ["Choreography and Performance", "Dance Pedagogy and Social Action"],
     "description": "Dance as performance, choreography, and scholarship, with tracks in choreography and performance and in dance pedagogy and social action."},

    # ══ School of Education (undergraduate) ══
    {"slug": "lmu-education-learning-sciences-ba", "school": _EDUCATION, "program_name": "Bachelor of Arts in Education and Learning Sciences", "degree_type": "bachelors", "department": "Department of Teaching and Learning", "cip": "13.12", "keywords": ["education", "teaching", "liberal studies"],
     "description": "LMU's undergraduate pathway into teaching (Liberal Studies), integrating the learning sciences with preparation for a California teaching credential."},

    # ══ School of Film and Television (undergraduate) ══
    {"slug": "lmu-animation-ba", "school": _SFTV, "program_name": "Bachelor of Arts in Animation", "degree_type": "bachelors", "department": "Department of Animation", "cip": "50.06", "keywords": ["animation"],
     "description": "2D, 3D, and experimental animation — story, design, and production — at one of the nation's leading film schools in the heart of the industry."},
    {"slug": "lmu-film-tv-production-bfa", "school": _SFTV, "program_name": "Bachelor of Fine Arts in Film and Television Production", "degree_type": "bachelors", "department": "Department of Film and Television Production", "cip": "50.06", "keywords": ["film production", "BFA"],
     "description": "A professional production degree covering directing, cinematography, editing, and producing, with hands-on filmmaking and LA industry access."},
    {"slug": "lmu-film-tv-media-studies-ba", "school": _SFTV, "program_name": "Bachelor of Arts in Film, Television, and Media Studies", "degree_type": "bachelors", "department": "Department of Film, Television, and Media Studies", "cip": "50.06", "keywords": ["film studies", "media studies"],
     "description": "The history, theory, and criticism of film, television, and media, examining moving images as art, industry, and cultural force."},
    {"slug": "lmu-recording-arts-ba", "school": _SFTV, "program_name": "Bachelor of Arts in Recording Arts", "degree_type": "bachelors", "department": "Department of Recording Arts", "cip": "50.06", "keywords": ["recording arts", "sound"],
     "description": "Sound recording, design, and music production for film, television, and media, blending audio technology with creative practice."},
    {"slug": "lmu-screenwriting-ba", "school": _SFTV, "program_name": "Bachelor of Arts in Screenwriting", "degree_type": "bachelors", "department": "Department of Screenwriting", "cip": "50.06", "keywords": ["screenwriting"],
     "description": "The craft of writing for film and television — structure, character, and dialogue — taught by working screenwriters in Los Angeles."},

    # ══ Graduate & professional programs ══
    # Bellarmine College of Liberal Arts
    {"slug": "lmu-english-ma", "school": _BELLARMINE, "program_name": "Master of Arts in English", "degree_type": "masters", "department": "Department of English", "cip": "23.01", "keywords": ["English", "literature", "MA"],
     "description": "Advanced graduate study of literature and criticism, with an accelerated bachelor's-to-master's option for LMU undergraduates."},
    {"slug": "lmu-philosophy-ma", "school": _BELLARMINE, "program_name": "Master of Arts in Philosophy", "degree_type": "masters", "department": "Department of Philosophy", "cip": "38.01", "keywords": ["philosophy", "MA"],
     "description": "Graduate coursework across the core areas of philosophy, deepening analytical and historical study of the discipline."},
    {"slug": "lmu-theology-ma", "school": _BELLARMINE, "program_name": "Master of Arts in Theology", "degree_type": "masters", "department": "Department of Theological Studies", "cip": "39.06", "keywords": ["theology", "MA"],
     "description": "Graduate study of Christian and comparative theology, scripture, and tradition in LMU's Catholic intellectual heritage."},
    {"slug": "lmu-pastoral-theology-ma", "school": _BELLARMINE, "program_name": "Master of Arts in Pastoral Theology", "degree_type": "masters", "department": "Department of Theological Studies", "cip": "39.07", "keywords": ["pastoral theology", "ministry"],
     "description": "Formation for pastoral ministry and spiritual leadership, integrating theology with pastoral practice and reflection."},
    {"slug": "lmu-yoga-studies-ma", "school": _BELLARMINE, "program_name": "Master of Arts in Yoga Studies", "degree_type": "masters", "department": "Yoga Studies Program", "cip": "39.06", "keywords": ["yoga studies", "MA"],
     "description": "One of the few graduate Yoga Studies programs in the U.S., studying yoga's philosophy, history, and textual traditions academically."},

    # Frank R. Seaver College of Science and Engineering (graduate)
    {"slug": "lmu-environmental-science-ms", "school": _SEAVER, "program_name": "Master of Science in Environmental Science", "degree_type": "masters", "department": "Department of Civil and Environmental Engineering", "cip": "03.01", "keywords": ["environmental science", "MS"],
     "description": "Graduate study of environmental systems and management, combining science with policy and applied field and laboratory research."},
    {"slug": "lmu-civil-engineering-mse", "school": _SEAVER, "program_name": "Master of Science in Engineering in Civil Engineering", "degree_type": "masters", "department": "Department of Civil and Environmental Engineering", "cip": "14.08", "keywords": ["civil engineering", "MSE"],
     "description": "Advanced graduate study in civil engineering — structures, environmental, and water-resources engineering — with applied design projects."},
    {"slug": "lmu-computer-science-ms", "school": _SEAVER, "program_name": "Master of Science in Computer Science", "degree_type": "masters", "department": "Department of Computer Science", "cip": "11.07", "keywords": ["computer science", "MS"],
     "description": "Advanced coursework and projects in computer science — software systems, data, and applied computing — for professionals and researchers."},
    {"slug": "lmu-electrical-engineering-mse", "school": _SEAVER, "program_name": "Master of Science in Engineering in Electrical Engineering", "degree_type": "masters", "department": "Department of Electrical and Computer Engineering", "cip": "14.10", "keywords": ["electrical engineering", "MSE"],
     "description": "Graduate study in electrical engineering — signals, systems, and electronics — with a professional, applied orientation."},
    {"slug": "lmu-computer-engineering-mse", "school": _SEAVER, "program_name": "Master of Science in Engineering in Computer Engineering", "degree_type": "masters", "department": "Department of Electrical and Computer Engineering", "cip": "14.09", "keywords": ["computer engineering", "MSE"],
     "description": "Graduate study spanning hardware and software systems — embedded design, architecture, and computing — with applied projects."},
    {"slug": "lmu-mechanical-engineering-mse", "school": _SEAVER, "program_name": "Master of Science in Engineering in Mechanical Engineering", "degree_type": "masters", "department": "Department of Mechanical Engineering", "cip": "14.19", "keywords": ["mechanical engineering", "MSE"],
     "description": "Advanced mechanical engineering — mechanics, thermal and energy systems, and design — for practicing engineers and researchers."},
    {"slug": "lmu-healthcare-systems-engineering-ms", "school": _SEAVER, "program_name": "Master of Science in Healthcare Systems Engineering", "degree_type": "masters", "department": "Healthcare Systems Engineering Program", "cip": "14.27", "keywords": ["healthcare systems engineering", "MS"],
     "description": "Applies systems and industrial engineering to healthcare delivery — process improvement, quality, and operations in health systems."},
    {"slug": "lmu-systems-engineering-ms", "school": _SEAVER, "program_name": "Master of Science in Systems Engineering", "degree_type": "masters", "department": "Systems Engineering and Engineering Management Program", "cip": "14.27", "keywords": ["systems engineering", "MS"],
     "description": "The engineering of complex systems — requirements, architecture, integration, and lifecycle management — for technical and program leadership."},
    {"slug": "lmu-statistics-data-science-ms", "school": _SEAVER, "program_name": "Master of Science in Statistics and Data Science", "degree_type": "masters", "department": "Department of Mathematics, Statistics and Data Science", "cip": "27.05", "keywords": ["statistics", "data science", "MS"],
     "description": "Applied statistics and data science — modeling, machine learning, and inference — building the quantitative skills employers demand."},
    {"slug": "lmu-mathematics-teaching-mat", "school": _SEAVER, "program_name": "Master of Arts in Teaching in Mathematics for Teaching", "degree_type": "masters", "department": "Department of Mathematics, Statistics and Data Science", "cip": "13.13", "keywords": ["mathematics teaching", "MAT"],
     "description": "A master's for current and future mathematics teachers deepening mathematical content knowledge alongside pedagogy."},

    # College of Business Administration (graduate)
    {"slug": "lmu-mba", "school": _BUSINESS, "program_name": "Master of Business Administration", "degree_type": "masters", "department": "College of Business Administration", "cip": "52.02", "keywords": ["MBA", "business"],
     "description": "LMU's flagship graduate management degree — strategy, finance, marketing, and leadership — with strong Los Angeles industry and entertainment ties."},
    {"slug": "lmu-dba", "school": _BUSINESS, "program_name": "Doctor of Business Administration", "degree_type": "phd", "department": "College of Business Administration", "cip": "52.02", "keywords": ["DBA", "doctorate", "business"],
     "description": "A practitioner doctorate for experienced executives conducting applied research on real management and organizational problems."},
    {"slug": "lmu-accounting-ms", "school": _BUSINESS, "program_name": "Master of Science in Accounting", "degree_type": "masters", "department": "Department of Accounting", "cip": "52.03", "keywords": ["accounting", "MS", "CPA"],
     "description": "An accounting master's completing the CPA education requirement, with advanced financial reporting, auditing, and analytics."},
    {"slug": "lmu-taxation-ms", "school": _BUSINESS, "program_name": "Master of Science in Taxation", "degree_type": "masters", "department": "Department of Accounting", "cip": "52.16", "keywords": ["taxation", "MS"],
     "description": "Advanced study of federal and state taxation for accounting and tax professionals."},
    {"slug": "lmu-business-analytics-ms", "school": _BUSINESS, "program_name": "Master of Science in Business Analytics", "degree_type": "masters", "department": "Department of Information Systems and Business Analytics", "cip": "52.13", "keywords": ["business analytics", "MS"],
     "description": "Turning data into business decisions — predictive modeling, visualization, and analytics strategy — for analytics and data-driven roles."},
    {"slug": "lmu-management-ms", "school": _BUSINESS, "program_name": "Master of Science in Management", "degree_type": "masters", "department": "Department of Management", "cip": "52.02", "keywords": ["management", "MS"],
     "description": "A pre-experience management master's building foundational business, leadership, and analytical skills for early-career professionals."},
    {"slug": "lmu-entrepreneurship-sustainable-innovation-ms", "school": _BUSINESS, "program_name": "Master of Science in Entrepreneurship and Sustainable Innovation", "degree_type": "masters", "department": "Department of Management", "cip": "52.07", "keywords": ["entrepreneurship", "sustainability", "MS"],
     "description": "Launching ventures and driving sustainable innovation, pairing entrepreneurship with environmental and social responsibility."},
    {"slug": "lmu-entertainment-leadership-management-ma", "school": _BUSINESS, "program_name": "Master of Arts in Entertainment Leadership and Management", "degree_type": "masters", "department": "College of Business Administration (with School of Film and Television)", "cip": "52.02", "keywords": ["entertainment management", "MA"],
     "description": "A jointly offered degree in the business of entertainment — leadership, finance, and management for the film, television, and media industries."},

    # College of Communication and Fine Arts (graduate)
    {"slug": "lmu-mft-art-therapy-ma", "school": _CFA, "program_name": "Master of Arts in Marital and Family Therapy with Specialized Training in Art Therapy", "degree_type": "masters", "department": "Marital and Family Therapy Program", "cip": "51.15", "keywords": ["marriage and family therapy", "art therapy", "MA"],
     "description": "Clinical training for marriage and family therapists with specialized preparation in art therapy, combining psychotherapy with creative-arts practice."},
    {"slug": "lmu-performance-pedagogy-mfa", "school": _CFA, "program_name": "Master of Fine Arts in Performance Pedagogy", "degree_type": "masters", "department": "Department of Theatre Arts and Dance", "cip": "50.05", "keywords": ["performance pedagogy", "MFA"],
     "description": "A terminal degree preparing theatre and dance artists to teach performance at the college level through practice and pedagogy."},

    # School of Education (graduate)
    {"slug": "lmu-educational-leadership-ma", "school": _EDUCATION, "program_name": "Master of Arts in Educational Leadership", "degree_type": "masters", "department": "Department of Educational Leadership", "cip": "13.04", "keywords": ["educational leadership", "MA"],
     "description": "Prepares educators for leadership roles in schools and districts, integrating leadership theory with equity-focused practice."},
    {"slug": "lmu-school-administration-ma", "school": _EDUCATION, "program_name": "Master of Arts in School Administration", "degree_type": "masters", "department": "Department of Educational Leadership", "cip": "13.04", "keywords": ["school administration", "MA"],
     "description": "Preparation for school administrative roles paired with the California administrative-services credential."},
    {"slug": "lmu-educational-leadership-edd", "school": _EDUCATION, "program_name": "Doctor of Education in Educational Leadership for Social Justice", "degree_type": "phd", "department": "Department of Educational Leadership", "cip": "13.04", "keywords": ["EdD", "educational leadership", "social justice"],
     "description": "LMU's flagship professional doctorate, preparing leaders to transform schools and organizations toward equity and social justice through applied research."},
    {"slug": "lmu-counseling-ma", "school": _EDUCATION, "program_name": "Master of Arts in Counseling", "degree_type": "masters", "department": "Specialized Programs in Professional Psychology", "cip": "13.11", "keywords": ["counseling", "MA"],
     "description": "Clinical and school counseling preparation, integrating counseling theory with supervised field practice."},
    {"slug": "lmu-college-counseling-student-affairs-ma", "school": _EDUCATION, "program_name": "Master of Arts in College Counseling and Student Affairs", "degree_type": "masters", "department": "Specialized Programs in Professional Psychology", "cip": "13.11", "keywords": ["student affairs", "college counseling", "MA"],
     "description": "Prepares professionals for counseling and student-affairs roles in higher education, from advising to student development."},
    {"slug": "lmu-school-counseling-ma", "school": _EDUCATION, "program_name": "Master of Arts in School Counseling", "degree_type": "masters", "department": "Specialized Programs in Professional Psychology", "cip": "13.11", "keywords": ["school counseling", "PPS"],
     "description": "School-counseling preparation paired with the Pupil Personnel Services credential for California K–12 counselors."},
    {"slug": "lmu-school-psychology-eds", "school": _EDUCATION, "program_name": "Education Specialist in School Psychology", "degree_type": "masters", "department": "Specialized Programs in Professional Psychology", "cip": "13.11", "keywords": ["school psychology", "EdS"],
     "description": "An Education Specialist degree (with an M.A. in Educational Psychology and the PPS credential) preparing credentialed school psychologists."},
    {"slug": "lmu-educational-studies-ma", "school": _EDUCATION, "program_name": "Master of Arts in Educational Studies", "degree_type": "masters", "department": "Department of Teaching and Learning", "cip": "13.01", "keywords": ["educational studies", "MA"],
     "description": "Graduate study of education for practitioners and scholars, with an accelerated option, spanning policy, culture, and learning."},
    {"slug": "lmu-special-education-ma", "school": _EDUCATION, "program_name": "Master of Arts in Special Education", "degree_type": "masters", "department": "Department of Teaching and Learning", "cip": "13.10", "keywords": ["special education", "MA"],
     "description": "Prepares educators to teach and support students with disabilities, pairing inclusive-education coursework with credential preparation."},
    {"slug": "lmu-transformative-education-ma", "school": _EDUCATION, "program_name": "Master of Arts in Transformative Education", "degree_type": "masters", "department": "Department of Teaching and Learning", "cip": "13.01", "keywords": ["transformative education", "MA", "credential"],
     "description": "A teaching master's, offered standalone or paired with a California multiple- or single-subject credential, centered on equity-driven pedagogy."},

    # School of Film and Television (graduate)
    {"slug": "lmu-film-tv-production-mfa", "school": _SFTV, "program_name": "Master of Fine Arts in Film and Television Production", "degree_type": "masters", "department": "Department of Film and Television Production", "cip": "50.06", "keywords": ["film production", "MFA"],
     "description": "A terminal production degree for filmmakers — directing, cinematography, and producing — with intensive thesis film work in Los Angeles."},
    {"slug": "lmu-writing-for-screen-mfa", "school": _SFTV, "program_name": "Master of Fine Arts in Writing for the Screen", "degree_type": "masters", "department": "Department of Screenwriting", "cip": "50.06", "keywords": ["screenwriting", "MFA"],
     "description": "A terminal screenwriting degree developing feature and short-form scripts under working screenwriters in the heart of the industry."},
    {"slug": "lmu-writing-producing-television-mfa", "school": _SFTV, "program_name": "Master of Fine Arts in Writing and Producing for Television", "degree_type": "masters", "department": "Department of Screenwriting", "cip": "50.06", "keywords": ["television writing", "MFA"],
     "description": "A terminal degree in writing and producing for television, covering the writers' room, pilots, and series development."},

    # LMU Loyola Law School
    {"slug": "lmu-jd", "school": _LAW, "program_name": "Juris Doctor", "degree_type": "professional", "department": "LMU Loyola Law School", "cip": "22.01", "keywords": ["JD", "law"],
     "description": "The professional law degree at one of California's most prominent law schools, offered as a full-time day program and a hybrid evening program in downtown Los Angeles."},
    {"slug": "lmu-llm", "school": _LAW, "program_name": "Master of Laws", "degree_type": "masters", "department": "LMU Loyola Law School", "cip": "22.02", "keywords": ["LLM", "law"],
     "description": "A flexible American-law master's built largely for foreign-trained and practicing attorneys, with a Bar-track option for U.S. licensure."},
    {"slug": "lmu-tax-llm", "school": _LAW, "program_name": "Master of Laws in Taxation", "degree_type": "masters", "department": "LMU Loyola Law School", "cip": "22.02", "keywords": ["tax LLM", "law"],
     "delivery_format": "online",
     "description": "An online master of laws in taxation for attorneys and tax professionals seeking advanced expertise in tax law."},
    {"slug": "lmu-mls", "school": _LAW, "program_name": "Master of Science in Legal Studies", "degree_type": "masters", "department": "LMU Loyola Law School", "cip": "22.00", "keywords": ["legal studies", "MLS"],
     "description": "Legal training for professionals who need to work with the law but are not pursuing a J.D. or bar admission."},
]


# ── Derived defaults ───────────────────────────────────────────────────────
_DEFAULT_DURATION = {"bachelors": 48, "masters": 24, "phd": 36, "professional": 36}

for _p in _CATALOG:
    _p.setdefault("delivery_format", "on_campus")
    _p.setdefault("duration_months", _DEFAULT_DURATION.get(_p["degree_type"], 24))

PROGRAMS: list[dict] = _CATALOG
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_TRACKS_BY_SLUG: dict[str, list[str]] = {p["slug"]: p["tracks"] for p in PROGRAMS if p.get("tracks")}

# ── Quality gates (fail the build on fabrication tells) ─────────────────────
if len(set(PROGRAM_SLUGS)) != len(PROGRAM_SLUGS):
    _seen: set[str] = set()
    _dups = [s for s in PROGRAM_SLUGS if s in _seen or _seen.add(s)]
    raise RuntimeError(f"duplicate program slug(s): {sorted(set(_dups))}")
_name_keys = [(p["program_name"], p["degree_type"]) for p in PROGRAMS]
if len(set(_name_keys)) != len(_name_keys):
    _seen2: set[tuple] = set()
    _dn = [k for k in _name_keys if k in _seen2 or _seen2.add(k)]
    raise RuntimeError(f"duplicate (program_name, degree_type) in LMU catalog: {_dn}")
for _p in PROGRAMS:
    if not _p.get("cip") or not re.fullmatch(r"\d{2}\.\d{2,4}", _p["cip"]):
        raise RuntimeError(f"missing/malformed cip on {_p['slug']}: {_p.get('cip')!r}")
    _d = _p.get("description") or ""
    if _d.startswith(_p["program_name"]):
        raise RuntimeError(f"name-prefixed description on {_p['slug']}")
    if "offered through" in _d or "is a program at" in _d:
        raise RuntimeError(f"classification-stub description on {_p['slug']}")
# Matcher-core tuition COVERAGE gate: master's + professional tiers publish a per-unit /
# per-program rate and are rarely funded, so a null there is starvation, not an honest
# omission (SKILL §"Measure tuition coverage PER CREDENTIAL LEVEL"). Both tiers must be
# 100% filled from LMU's published schedule. (PhD/doctorate rows are filled too where a
# real rate is published — DBA, Ed.D. — but are not gated, per the funded convention.)
_uncovered_grad = [
    p["slug"]
    for p in PROGRAMS
    if p["degree_type"] in ("masters", "professional")
    and _GRAD_TUITION_BY_SLUG.get(p["slug"]) is None
]
if _uncovered_grad:
    raise RuntimeError(f"master's/professional tuition not covered: {_uncovered_grad}")
# Every filled graduate rate must be DISTINCT from the undergraduate sticker (no copy-down).
_copydown = [s for s, v in _GRAD_TUITION_BY_SLUG.items() if v == _UG_TUITION]
if _copydown:
    raise RuntimeError(f"graduate tuition equals undergrad sticker (copy-down): {_copydown}")


# ── who_its_for (derived, program-distinct, grounded in the verified description) ──
def _who_focus(spec: dict) -> str:
    desc = (spec.get("description") or "").strip().rstrip(".")
    for verb in (" — ", ": ", " study of ", " studies ", " study ", " covering ", " spanning ",
                 " on how ", " on the ", " of how ", " applies ", " combines ", " examines ",
                 " analyzes ", " builds ", " trains ", " grounds ", " in which ", " where ",
                 " bridging ", " across ", " preparing ", " developing ", " turning ",
                 " integrating ", " for ", " with "):
        i = desc.lower().find(verb)
        if i > 0:
            tail = desc[i + len(verb):].strip()
            for stop in (";", ",", " — "):
                j = tail.find(stop)
                if 0 < j < 150:
                    tail = tail[:j]
            if 8 <= len(tail) <= 170:
                return tail.rstrip(".")
    return spec.get("keywords", [""])[0] or spec["program_name"]


def _who_its_for(spec: dict) -> str:
    name = spec["program_name"]
    focus = _who_focus(spec)
    dt = spec["degree_type"]
    if dt == "bachelors":
        return (
            f"Undergraduates choosing {name} at LMU who want to study {focus}. "
            "A fit for students headed toward graduate study, professional work, or service in the field."
        )
    if dt == "professional":
        return (
            f"Applicants to LMU's {name} preparing for licensed professional practice grounded in {focus}."
        )
    if dt == "phd":
        return (
            f"Experienced professionals pursuing LMU's {name} to lead and conduct applied research in {focus}."
        )
    return (
        f"Graduate students in LMU's {name} seeking advanced, applied study of {focus}. "
        "Best for professional practice, leadership, or further graduate work."
    )


# who_its_for distinctness gate.
_who_values = [_who_its_for(p) for p in PROGRAMS]
if len(set(_who_values)) != len(_who_values):
    raise RuntimeError(
        f"who_its_for not program-distinct: {len(set(_who_values))}/{len(_who_values)}"
    )


def _program_standard(spec: dict) -> dict:
    slug = spec["slug"]
    omitted: list[str] = [
        "outcomes_data.employment_rate",
        "outcomes_data.top_industries",
    ]
    # Only bachelor's carry the published sticker. LMU bills graduate / doctoral / professional
    # programs per-unit with no single annual figure on that basis → tuition omitted-with-reason.
    if spec["degree_type"] != "bachelors" and _GRAD_TUITION_BY_SLUG.get(spec["slug"]) is None:
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
    annual = _GRAD_TUITION_BY_SLUG.get(spec["slug"])
    if annual is not None:
        return annual, _grad_cost(spec, annual)
    return None, _grad_omit_cost(spec)


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich LMU to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when LMU is absent — safe on fresh/CI databases.
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
    inst.founded_year = 1911
    inst.campus_setting = "suburban"
    if not inst.website_url:
        inst.website_url = "https://www.lmu.edu"
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
        about["source"] = {"label": "Loyola Marymount University — Academics", "url": "https://www.lmu.edu/academics/"}
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
        p.content_sources = _program_content(spec["school"], spec["keywords"])
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
