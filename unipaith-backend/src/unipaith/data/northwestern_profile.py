"""Northwestern University — gold-standard profile data (institution + schools + program catalog).

Mirrors the MIT / Sloan / MBAn reference instance (see ``mit_profile.py`` /
``jhu_profile.py``): every value is researched from an authoritative source and
carries a citation, or is honestly omitted (recorded in that node's ``_standard.omitted``)
— never guessed. Built 2026-06-13 from:

  * U.S. Dept. of Education **College Scorecard** API + **IPEDS** (UNITID 147767):
    admit rate, average net price, cost of attendance, ten-year median earnings,
    four-year completion, first-year retention, Pell/loan rates, median debt,
    endowment, undergraduate race/ethnicity, and SAT/ACT middle-50% scores.
  * **Northwestern Common Data Set 2024-2025** and the Office of Institutional Research:
    the Fall 2024 first-year admissions funnel, total enrollment, and the 6:1
    student-faculty ratio; Class of 2029 funnel (53,284 applicants / 3,710 admits)
    from The Daily Northwestern (April 2025).
  * Rankings: **U.S. News Best Colleges 2026** (#7 National), **QS 2026** (#42),
    **Times Higher Education 2026** (#30), Carnegie R1, and Higher Learning Commission
    (HLC) accreditation, each cited.
  * The official **Northwestern Academics** schools-and-colleges index plus
    the College Scorecard Field-of-Study catalog (306 CIP rows) mapped to Northwestern's
    eleven U.S. main-campus schools (Qatar excluded). School of Professional Studies
    programs carry ``delivery_format = "online"`` where applicable per IPEDS.
  * Northwestern leadership pages and school websites for each unit's dean, and a
    verified 5-photo Wikimedia Commons campus gallery (author + license confirmed
    via the Commons API).
  * Verified third-party coverage + official rankings for coverable programs.

Honest caveats stamped into ``_standard.omitted``: Northwestern does not publish a single
university-wide placement rate or a uniform top-employer-industries list across all
schools, so those two institution outcome fields are omitted. Most graduate/professional
programs bill tuition per term and publish no single annual figure, so those carry a
sourced "see the program's tuition page" record rather than a guessed number.

Depth pass (2026-06-15, northwesternprof2): merged ``DEPTH_REVIEWS`` for 48 coverable
programs — completes Northwestern coverable external_reviews (55/55).
"""

# ruff: noqa: E501

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.northwestern_ipeds_catalog import _IPEDS_CATALOG
from unipaith.data.northwestern_reviews_depth import DEPTH_REVIEWS
from unipaith.data.profile_catalog_utils import (
    disambiguate_program_name,
    program_description,
    validate_catalog,
)
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Northwestern University"
ENRICHED_AT = "2026-06-14"


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


_OMITTED_INSTITUTION: list[str] = [
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
]

RANKING_DATA: dict = {
    "ownership_type": "private",
    "accreditor": "Higher Learning Commission (HLC)",
    "carnegie_classification": (
        "Doctoral Universities: Very High Research Spending and Doctorate Production (R1)"
    ),
    "qs_world_university_rankings": {
        "rank": 42, "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/northwestern-university",
    },
    "times_higher_education": {
        "rank": 30, "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/northwestern-university",
    },
    "us_news_national": {
        "rank": 7, "year": 2026,
        "source_url": "https://www.usnews.com/best-colleges/northwestern-university-1739",
    },
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.074,
    "avg_net_price": 29167,
    "median_earnings_10yr": 89363,
    "completion_rate_4yr_150pct": 0.9551,
    "retention_rate_first_year": 0.981,
    "graduation_rate_6yr": 0.9551,
    "financial_aid": {
        "pell_grant_rate": 0.1855,
        "federal_loan_rate": 0.1708,
        "cost_of_attendance": 91250,
        "median_debt_completers": 15000,
        "avg_net_price": 29167,
    },
    "demographics": {
        "white": 0.30,
        "asian": 0.21,
        "hispanic": 0.16,
        "black": 0.08,
        "two_or_more": 0.08,
        "international": 0.12,
        "unknown": 0.04,
    },
    "test_scores": {
        "sat_reading_25_75": [740, 770],
        "sat_math_25_75": [770, 800],
        "act_25_75": [34, 35],
    },
    "campus_basics": {"location": "Evanston, Illinois"},
    "scale": {
        "campus_acres": 240,
        "endowment_usd": 15300000000,
        "student_faculty_ratio": "6:1",
        "faculty_count": 3300,
    },
    "location": {"lat": 42.0565, "lng": -87.6753},
    "research": {
        "areas": [
            "Nanotechnology",
            "Sustainability and energy",
            "Clinical and translational sciences",
            "Social policy research",
            "Bioelectronics",
            "Complex systems and network science",
        ],
        "labs": [
            "International Institute for Nanotechnology",
            "Institute for Policy Research",
            "Paula M. Trienens Institute for Sustainability and Energy",
            "Querrey Simpson Institute for Bioelectronics",
            "Northwestern Institute on Complex Systems",
            "Chemistry of Life Processes Institute",
            "Robert H. Lurie Comprehensive Cancer Center",
            "Northwestern University Clinical and Translational Sciences (NUCATS) Institute",
            "Buffett Institute for Global Affairs",
        ],
        "lab_links": {
            "International Institute for Nanotechnology": "https://www.iinano.org/",
            "Institute for Policy Research": "https://www.ipr.northwestern.edu/",
            "Paula M. Trienens Institute for Sustainability and Energy": "https://trienens-institute.northwestern.edu/",
            "Querrey Simpson Institute for Bioelectronics": "https://bioelectronics.northwestern.edu/",
            "Northwestern Institute on Complex Systems": "https://www.nico.northwestern.edu/",
            "Chemistry of Life Processes Institute": "https://clp.northwestern.edu/",
            "Robert H. Lurie Comprehensive Cancer Center": "https://www.cancer.northwestern.edu/",
            "Northwestern University Clinical and Translational Sciences (NUCATS) Institute": "https://www.nucats.northwestern.edu/",
            "Buffett Institute for Global Affairs": "https://buffett.northwestern.edu/",
        },
    },
    "campus_life": {
        "student_orgs": 500,
        "varsity_sports": 19,
        "athletics_division": "NCAA Division I (Big Ten)",
        "resources": [
            {"name": "Northwestern Athletics", "url": "https://nusports.com/"},
            {
                "name": "Student Organizations & Activities",
                "url": "https://www.northwestern.edu/studentorgs/",
            },
            {
                "name": "Norris University Center",
                "url": "https://www.northwestern.edu/norris/",
            },
            {"name": "Residential Services", "url": "https://www.northwestern.edu/living/"},
            {
                "name": "Campus Experience",
                "url": "https://www.northwestern.edu/campus-experience/",
            },
        ],
    },
    "campus_photos": [
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Deering_front.jpg/1920px-Deering_front.jpg", "credit": "Wikimedia Commons / Madcoverboy (CC BY-SA 3.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Aerial_view_of_Northwestern_University.png/1920px-Aerial_view_of_Northwestern_University.png", "credit": "Wikimedia Commons / Sakuav (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Entrance_to_Northwestern_University_Technological_Institute_%2851725404073%29.jpg/1920px-Entrance_to_Northwestern_University_Technological_Institute_%2851725404073%29.jpg", "credit": "Wikimedia Commons / Chris Rycroft (CC BY 2.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Frances_Searle_Building.jpg/1920px-Frances_Searle_Building.jpg", "credit": "Wikimedia Commons / Smandlso (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Ford_Motor_Company_Design_Center%2C_Northwestern_University_%283404284231%29.jpg/1920px-Ford_Motor_Company_Design_Center%2C_Northwestern_University_%283404284231%29.jpg", "credit": "Wikimedia Commons / Clara S. (CC BY 2.0)"},
    ],
    "media_credit": "Wikimedia Commons / Madcoverboy (CC BY-SA 3.0)",
    "flagship": {
        "applicants": 53284,
        "admits": 3710,
        "admissions_cycle": "First-year, Class of 2029 (The Daily Northwestern, April 2025)",
        "founded_year": 1851,
    },
    "sources": [
        {"label": "College Scorecard (UNITID 147767)", "url": "https://collegescorecard.ed.gov/school/?147767-Northwestern-University"},
        {"label": "Northwestern Office of Institutional Research — Common Data Set", "url": "https://enrollment.northwestern.edu/data/"},
        {"label": "U.S. News — Northwestern University", "url": "https://www.usnews.com/best-colleges/northwestern-university-1739"},
    ],
}

UNDERGRAD_COUNT = 9000

DESCRIPTION = (
    "Northwestern University is a private research university in Evanston, IL, founded "
    "in 1851 on the shore of Lake Michigan just north of Chicago. A founding member of "
    "the Big Ten Conference, it pairs a 240-acre lakefront campus and a 6:1 student-faculty "
    "ratio with a research enterprise that draws more than $1 billion in annual funding. "
    "Its International Institute for Nanotechnology, established in 2000, was the first "
    "institute of its kind in the United States.\n\n"
    "Northwestern is organized into eleven degree-granting schools on its U.S. main campus "
    "— Weinberg College of Arts and Sciences, McCormick School of Engineering and Applied "
    "Science, Medill School of Journalism, Media, Integrated Marketing Communications, "
    "the School of Communication, Bienen School of Music, School of Education and Social "
    "Policy, Kellogg School of Management, Pritzker School of Law, Feinberg School of "
    "Medicine, The Graduate School, and the School of Professional Studies — offering "
    "hundreds of programs across the bachelor's, master's, professional, and doctoral levels.\n\n"
    "A Carnegie R1 university accredited by the Higher Learning Commission, Northwestern "
    "ranks #7 among national universities by U.S. News, #30 in the world by Times Higher "
    "Education, and #42 by QS for 2026. Its research footprint runs from the International "
    "Institute for Nanotechnology and the Querrey Simpson Institute for Bioelectronics to "
    "the Robert H. Lurie Comprehensive Cancer Center and the Buffett Institute for Global "
    "Affairs.\n\n"
    "Northwestern's published cost of attendance is about $91,250 a year, but its average "
    "net price after grant aid is about $29,167 and the median federal debt of completers "
    "is about $15,000. Northwestern graduates earn a median of roughly $89,363 ten years "
    "after entry. The Wildcats compete in NCAA Division I as a member of the Big Ten "
    "Conference."
)

# ── School constants ───────────────────────────────────────────────────────

WEINBERG = "Weinberg College of Arts and Sciences"
MCCORMICK = "McCormick School of Engineering and Applied Science"
MEDILL = "Medill School of Journalism, Media, Integrated Marketing Communications"
COMMUNICATION = "School of Communication"
BIENEN = "Bienen School of Music"
SESP = "School of Education and Social Policy"
KELLOGG = "Kellogg School of Management"
LAW = "Pritzker School of Law"
FEINBERG = "Feinberg School of Medicine"
TGS = "The Graduate School"
SPS = "School of Professional Studies"

_SCHOOL_META = [
    {"name": WEINBERG, "sort_order": 1, "website": "https://weinberg.northwestern.edu/", "leadership": "Adrian Randolph — Dean", "research_centers": ["Department of Economics", "Department of Psychology", "Department of Physics and Astronomy", "Institute for Policy Research", "Center for Applied Quantum Information"], "keywords": ["Weinberg College", "Arts and Sciences", "undergraduate"]},
    {"name": MCCORMICK, "sort_order": 2, "website": "https://www.mccormick.northwestern.edu/", "leadership": "Christopher Schuh — Dean", "research_centers": ["Segal Design Institute", "Center for Engineering and Health", "Northwestern Institute on Complex Systems (NICO)", "Center for Interdisciplinary Exploration and Research in Astrophysics (CIERA)", "International Institute for Nanotechnology"], "keywords": ["McCormick School", "engineering", "biomedical engineering"]},
    {"name": MEDILL, "sort_order": 3, "website": "https://www.medill.northwestern.edu/", "leadership": "Charles Whitaker — Dean", "research_centers": ["Knight Lab", "Local News Initiative", "Medill IMC Center", "Washington Program"], "keywords": ["Medill", "journalism", "IMC", "media"]},
    {"name": COMMUNICATION, "sort_order": 4, "website": "https://communication.northwestern.edu/", "leadership": "E. Patrick Johnson — Dean", "research_centers": ["Center for Communication and Health", "Center for Communication Studies", "School of Communication Theatre Program", "Performance Studies"], "keywords": ["School of Communication", "theatre", "RTVF", "performance studies"]},
    {"name": BIENEN, "sort_order": 5, "website": "https://www.music.northwestern.edu/", "leadership": "Jonathan Bailey Holland — Dean", "research_centers": ["Bienen Opera Theater", "Institute for New Music", "Music Performance Studies", "Contemporary Music Ensemble"], "keywords": ["Bienen School of Music", "music", "conservatory"]},
    {"name": SESP, "sort_order": 6, "website": "https://www.sesp.northwestern.edu/", "leadership": "Bryan McKinley Jones Brayboy — Dean", "research_centers": ["Institute for Policy Research", "Center for Learning and Organizational Change", "Developmental Sciences", "Equitable Learning Environments"], "keywords": ["SESP", "School of Education and Social Policy", "education", "social policy"]},
    {"name": KELLOGG, "sort_order": 7, "website": "https://www.kellogg.northwestern.edu/", "leadership": "Francesca Cornelli — Dean", "research_centers": ["Heizer Center for Private Equity and Venture Capital", "Guthrie Center for Real Estate Research", "Kellogg Public-Private Interface", "Healthcare at Kellogg"], "keywords": ["Kellogg School of Management", "MBA", "business"]},
    {"name": LAW, "sort_order": 8, "website": "https://www.law.northwestern.edu/", "leadership": "Zachary D. Clopton — Interim Dean", "research_centers": ["Bluhm Legal Clinic", "Center for International Human Rights", "Center on Law, Business, and Economics", "Program on Negotiation and Mediation"], "keywords": ["Pritzker School of Law", "JD", "law"]},
    {"name": FEINBERG, "sort_order": 9, "website": "https://www.feinberg.northwestern.edu/", "leadership": "Eric G. Neilson — Dean", "research_centers": ["Robert H. Lurie Comprehensive Cancer Center", "NUCATS Institute", "Feinberg Cardiovascular and Renal Research Center", "Institute for Global Health"], "keywords": ["Feinberg School of Medicine", "MD", "medicine"]},
    {"name": TGS, "sort_order": 10, "website": "https://www.tgs.northwestern.edu/", "leadership": "Kelly Mayo — Dean", "research_centers": ["Interdisciplinary Biological Sciences Graduate Program", "Office of Graduate Research", "Mellon Cluster Initiative", "Graduate Research Grant programs"], "keywords": ["The Graduate School", "TGS", "PhD", "graduate"]},
    {"name": SPS, "sort_order": 11, "website": "https://sps.northwestern.edu/", "leadership": "Thomas F. Gibbons — Dean", "research_centers": ["Center for Public Safety", "Osher Lifelong Learning Institute", "Professional Development Programs", "Northwestern Summer Session"], "keywords": ["School of Professional Studies", "SPS", "online", "part-time"]},
]

SCHOOLS: list[dict] = [
    {"name": m["name"], "sort_order": m["sort_order"], "description": f"The {m['name']} is one of the eleven schools of Northwestern University."}
    for m in _SCHOOL_META
]
SCHOOL_WEBSITE = {m["name"]: m["website"] for m in _SCHOOL_META}
_KEYWORDS_BY_SCHOOL = {m["name"]: m["keywords"] for m in _SCHOOL_META}


def _about_for(m: dict) -> dict:
    return {
        "leadership": m["leadership"],
        "research_centers": m["research_centers"],
        "source": {"label": "Northwestern University — Schools and Colleges", "url": "https://www.northwestern.edu/academics/"},
    }


def _about_omitted(m: dict) -> list[str]:
    return ["about_detail.founded", "about_detail.faculty", "about_detail.named_for"]


def _school_description(m: dict) -> str:
    return f"The {m['name']} is one of the eleven schools of Northwestern University."


# ── Feeds (content_sources) ────────────────────────────────────────────────
_NEWS_RSS = "https://news.northwestern.edu/feeds/allStories"
_EVENTS = {"url": "https://planitpurple.northwestern.edu/feed/ical/124", "type": "ical"}
_SOCIAL = {
    "instagram": "https://instagram.com/northwesternu",
    "facebook": "https://www.facebook.com/NorthwesternU",
    "x": "https://x.com/northwesternu",
    "youtube": "https://www.youtube.com/user/NorthwesternU",
    "linkedin": "https://www.linkedin.com/school/northwestern-university/",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _NEWS_RSS,
    "news_url": "https://news.northwestern.edu/",
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
    {"slug": "northwestern-mba-ms", "school": KELLOGG, "program_name": "Master of Business Administration", "degree_type": "masters", "duration_months": 24, "delivery_format": "on_campus", "description": "Full-time MBA at the Kellogg School of Management.", "department": "Kellogg School of Management", "cip": "52.02"},
    {"slug": "northwestern-law-prof", "school": LAW, "program_name": "Doctor of Law", "degree_type": "professional", "duration_months": 36, "delivery_format": "on_campus", "description": "Juris Doctor (J.D.) at the Northwestern Pritzker School of Law.", "department": "Pritzker School of Law", "cip": "22.01"},
    {"slug": "northwestern-medicine-prof", "school": FEINBERG, "program_name": "Doctor of Medicine", "degree_type": "professional", "duration_months": 48, "delivery_format": "on_campus", "description": "Doctor of Medicine (M.D.) at the Feinberg School of Medicine.", "department": "Feinberg School of Medicine", "cip": "51.12"},
    {"slug": "northwestern-computer-science-bs", "school": MCCORMICK, "program_name": "Computer Science", "degree_type": "bachelors", "duration_months": 48, "delivery_format": "on_campus", "description": "Bachelor of Science in Computer Science through the McCormick School of Engineering.", "department": "Department of Computer Science", "cip": "11.07"},
    {"slug": "northwestern-economics-bs", "school": WEINBERG, "program_name": "Economics", "degree_type": "bachelors", "duration_months": 48, "delivery_format": "on_campus", "description": "Bachelor of Arts in Economics through the Weinberg College of Arts and Sciences.", "department": "Department of Economics", "cip": "45.06"},
    {"slug": "northwestern-journalism-bs", "school": MEDILL, "program_name": "Journalism", "degree_type": "bachelors", "duration_months": 48, "delivery_format": "on_campus", "description": "Bachelor of Science in Journalism through the Medill School.", "department": "Medill School of Journalism, Media, Integrated Marketing Communications", "cip": "09.04"},
    {"slug": "northwestern-biomedical-medical-engineering-bs", "school": MCCORMICK, "program_name": "Biomedical/Medical Engineering", "degree_type": "bachelors", "duration_months": 48, "delivery_format": "on_campus", "description": "Bachelor of Science in Biomedical Engineering through McCormick.", "department": "Department of Biomedical Engineering", "cip": "14.05"},
    {"slug": "northwestern-psychology-general-bs", "school": WEINBERG, "program_name": "Psychology, General", "degree_type": "bachelors", "duration_months": 48, "delivery_format": "on_campus", "description": "Bachelor of Arts in Psychology through the Weinberg College.", "department": "Department of Psychology", "cip": "42.01"},
    {"slug": "northwestern-radio-television-and-digital-communication-ms", "school": COMMUNICATION, "program_name": "Radio, Television, and Digital Communication", "degree_type": "masters", "duration_months": 24, "delivery_format": "on_campus", "description": "Master of Science in Radio/Television/Film through the School of Communication.", "department": "Department of Radio/Television/Film", "cip": "09.07"},
    {"slug": "northwestern-management-sciences-and-quantitative-methods-ms", "school": KELLOGG, "program_name": "Management Sciences and Quantitative Methods", "degree_type": "masters", "duration_months": 24, "delivery_format": "on_campus", "description": "Master of Science in Management Studies and analytics-oriented graduate programs at Kellogg.", "department": "Kellogg School of Management", "cip": "52.13"},
]

_EXISTING_SLUGS = {p["slug"] for p in PROGRAMS}
_EXISTING_CIP_KEYS = {(p.get("cip"), p["degree_type"]) for p in PROGRAMS if p.get("cip")}


def _department_for(field_name: str, school: str) -> str:
    """Owning department — the CIP field title unless it duplicates the school name."""
    if field_name.lower() in school.lower() or school.lower() in field_name.lower():
        return school
    return field_name


def _build_catalog() -> list[dict]:
    out: list[dict] = []
    seen = set(_EXISTING_SLUGS)
    for slug, school, field_name, dtype, cip, dur, fmt, _legacy_desc in _IPEDS_CATALOG:
        if slug in seen:
            continue
        if (cip, dtype) in _EXISTING_CIP_KEYS:
            continue
        seen.add(slug)
        dept = _department_for(field_name, school)
        pname = disambiguate_program_name(field_name, dtype)
        out.append({
            "slug": slug,
            "school": school,
            "program_name": pname,
            "degree_type": dtype,
            "department": dept,
            "cip": cip,
            "duration_months": dur,
            "delivery_format": fmt,
            "description": program_description(
                pname, dtype, school, dept, delivery_format=fmt, university_short="Northwestern",
            ),
        })
    return out


PROGRAMS += _build_catalog()
_catalog_errors = validate_catalog(PROGRAMS)
if _catalog_errors:
    raise RuntimeError(f"Northwestern catalog quality gate failed: {_catalog_errors}")
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

_TUITION_UG = 68322
_UNDERGRAD_COA = 91250
_AVG_NET_PRICE = 29167
_COST_SRC = ("U.S. Dept. of Education College Scorecard (UNITID 147767)", "https://collegescorecard.ed.gov/school/?147767-Northwestern-University")

_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Application (Common Application or Coalition Application)", "required": True},
        {"name": "Required essays", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "$75 application fee (fee waivers available)", "required": True},
        {"name": "SAT/ACT scores", "required": False,
         "note": "Northwestern is test-optional; the middle 50% of enrolled students who submitted scored SAT 1510–1560 / ACT 34–35 (CDS 2024-25)."},
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
        "sources": [{"label": "Northwestern Undergraduate Admissions", "url": "https://admissions.northwestern.edu/apply/"}],
    },
    "source": "Northwestern Undergraduate Admissions",
    "source_url": "https://admissions.northwestern.edu/apply/",
}
_REQ_GRAD = {
    "materials": [
        {"name": "Northwestern graduate application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Résumé / CV", "required": True},
        {"name": "Letters of recommendation", "required": True,
         "note": "Most Northwestern graduate programs require two or three letters; check the program's page."},
        {"name": "GRE/GMAT scores", "required": False,
         "note": "Test requirements vary by program; many Northwestern graduate programs are test-optional."},
    ],
    "deadlines": [{"round": "Fall admission", "date": "Deadlines vary by program (typically December–January)"}],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS"], "required": True,
                    "note": "Required for applicants whose native language is not English."},
        "visa": {"types": ["F-1", "J-1"], "note": "International students receive an I-20 after admission."},
        "sources": [{"label": "The Graduate School — Admissions", "url": "https://www.tgs.northwestern.edu/admission/"}],
    },
    "source": "The Graduate School — Admissions",
    "source_url": "https://www.tgs.northwestern.edu/admission/",
}

_OUTCOMES_INSTITUTION = {
    "median_salary": 89363,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry",
    "source": "U.S. Dept. of Education College Scorecard (UNITID 147767)",
    "source_url": "https://collegescorecard.ed.gov/school/?147767-Northwestern-University",
}

_REVIEWS_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews."
)

_REVIEWS_BY_SLUG: dict[str, dict] = {
    "northwestern-computer-science-bs": {
        "summary": (
            "Northwestern's undergraduate computer science program combines McCormick engineering "
            "rigor with strong ties to AI, data science, and interdisciplinary research through "
            "NICO and the CS+X joint majors. Students praise small upper-level classes and Chicago "
            "tech recruiting access, though the core is theory-heavy and some wish for more "
            "industry-facing project courses than peer programs offer."
        ),
        "themes": [
            {"label": "Interdisciplinary breadth", "sentiment": "positive", "detail": "CS+X majors and NICO partnerships connect computing to journalism, music, and design."},
            {"label": "Theory-heavy core", "sentiment": "mixed", "detail": "Strong mathematical foundations; fewer applied-software electives than some peers."},
            {"label": "Research access", "sentiment": "positive", "detail": "Undergraduates join labs in AI, HCI, and computational social science."},
            {"label": "Chicago recruiting", "sentiment": "positive", "detail": "Graduates land at major tech firms, startups, and PhD programs nationwide."},
        ],
        "sources": [
            {"label": "Niche — Northwestern University", "url": "https://www.niche.com/colleges/northwestern-university/"},
            {"label": "U.S. News — Best Undergraduate Computer Science Programs", "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "northwestern-economics-bs": {
        "summary": (
            "Economics is one of the largest majors at Weinberg, known for rigorous quantitative "
            "training and a path to consulting, finance, and graduate school. Students appreciate "
            "the math-heavy curriculum and faculty research access, though introductory courses can "
            "be large and competitive grading is common."
        ),
        "themes": [
            {"label": "Quantitative training", "sentiment": "positive", "detail": "Math-intensive core prepares students for grad school and analytics roles."},
            {"label": "Research access", "sentiment": "positive", "detail": "Undergraduates join faculty labs in applied micro, macro, and econometrics."},
            {"label": "Large intro courses", "sentiment": "mixed", "detail": "Popular major means big lectures in introductory sequences."},
            {"label": "Career outcomes", "sentiment": "positive", "detail": "Strong placement in consulting, finance, and PhD programs."},
        ],
        "sources": [
            {"label": "Niche — Northwestern University", "url": "https://www.niche.com/colleges/northwestern-university/"},
            {"label": "Weinberg — Department of Economics", "url": "https://economics.northwestern.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "northwestern-mba-ms": {
        "summary": (
            "Kellogg's full-time MBA is a top-tier program known for its collaborative culture, "
            "marketing strength, and Chicago finance and consulting pipelines. Reviewers highlight "
            "team-based learning and strong alumni network, though the quarter system is fast-paced "
            "and tuition is among the highest nationally."
        ),
        "themes": [
            {"label": "Collaborative culture", "sentiment": "positive", "detail": "Team-based learning and a non-cutthroat cohort culture are program hallmarks."},
            {"label": "Marketing strength", "sentiment": "positive", "detail": "Kellogg is perennially ranked among the top marketing MBA programs."},
            {"label": "Fast pace", "sentiment": "caution", "detail": "The quarter system compresses coursework; time management is essential."},
            {"label": "Tuition cost", "sentiment": "caution", "detail": "Private MBA tuition is steep; merit aid is limited compared to some peers."},
        ],
        "sources": [
            {"label": "Poets&Quants — Kellogg School of Management", "url": "https://poetsandquants.com/schools/kellogg-school-of-management-northwestern-university/"},
            {"label": "U.S. News — Best Business Schools", "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/northwestern-university-01027"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "northwestern-law-prof": {
        "summary": (
            "Northwestern Pritzker Law is a top-20 law school known for its accelerated J.D. option, "
            "strong clinical programs through the Bluhm Legal Clinic, and Chicago legal market "
            "placement. Students praise practical training and faculty access, though the workload "
            "is intense and Big Law placement is competitive at the very top firms."
        ),
        "themes": [
            {"label": "Clinical training", "sentiment": "positive", "detail": "Bluhm Legal Clinic offers extensive hands-on litigation and advocacy experience."},
            {"label": "Chicago placement", "sentiment": "positive", "detail": "Strong pipelines to Chicago Big Law, corporate counsel, and federal clerkships."},
            {"label": "Accelerated option", "sentiment": "positive", "detail": "Two-year J.D. track attracts experienced professionals and career changers."},
            {"label": "Intense workload", "sentiment": "caution", "detail": "Quarter system and competitive grading demand strong time management."},
        ],
        "sources": [
            {"label": "U.S. News — Best Law Schools", "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/northwestern-university-03058"},
            {"label": "Pritzker School of Law — About", "url": "https://www.law.northwestern.edu/about/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "northwestern-medicine-prof": {
        "summary": (
            "Feinberg School of Medicine is a top research medical school affiliated with "
            "Northwestern Memorial Hospital, known for its Health & Society curriculum and strong "
            "NIH-funded research. Admission is extraordinarily competitive and the environment is "
            "demanding, though Chicago clinical exposure is exceptional."
        ),
        "themes": [
            {"label": "Research excellence", "sentiment": "positive", "detail": "Feinberg ranks among the top NIH-funded medical schools nationally."},
            {"label": "Clinical training", "sentiment": "positive", "detail": "Northwestern Memorial and affiliated hospitals provide diverse patient-care exposure."},
            {"label": "Extreme selectivity", "sentiment": "caution", "detail": "Acceptance rate below 3% with exceptional MCAT/GPA profiles expected."},
            {"label": "Demanding environment", "sentiment": "mixed", "detail": "High expectations and workload; support systems exist but stress is real."},
        ],
        "sources": [
            {"label": "U.S. News — Best Medical Schools: Research", "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/northwestern-university-feinberg-school-of-medicine-040101"},
            {"label": "Feinberg School of Medicine — About", "url": "https://www.feinberg.northwestern.edu/about/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "northwestern-journalism-bs": {
        "summary": (
            "Medill's undergraduate journalism program is among the most respected in the country, "
            "combining reporting fundamentals with digital and data journalism through the Knight "
            "Lab. Students praise faculty practitioners and Chicago media access, though the "
            "industry's contraction makes career planning essential early."
        ),
        "themes": [
            {"label": "Industry reputation", "sentiment": "positive", "detail": "Medill is perennially ranked among the top journalism schools nationally."},
            {"label": "Digital innovation", "sentiment": "positive", "detail": "Knight Lab and data-journalism courses keep the curriculum current."},
            {"label": "Practitioner faculty", "sentiment": "positive", "detail": "Working journalists and editors teach core reporting courses."},
            {"label": "Industry headwinds", "sentiment": "caution", "detail": "Traditional newsroom jobs are scarce; students must build versatile skill sets."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Journalism Programs", "url": "https://www.usnews.com/best-colleges/rankings/journalism"},
            {"label": "Medill — Undergraduate Journalism", "url": "https://www.medill.northwestern.edu/journalism/undergraduate/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "northwestern-biomedical-medical-engineering-bs": {
        "summary": (
            "Northwestern's biomedical engineering major combines McCormick engineering with "
            "Feinberg Medicine proximity and strong bioelectronics research. Students highlight "
            "interdisciplinary labs and pre-med flexibility, though the workload is intense and "
            "course sequencing requires careful planning."
        ),
        "themes": [
            {"label": "Interdisciplinary research", "sentiment": "positive", "detail": "Querrey Simpson Institute for Bioelectronics and Feinberg partnerships enrich the major."},
            {"label": "Pre-med pathway", "sentiment": "positive", "detail": "Many BME graduates pursue medical school or industry med-device roles."},
            {"label": "Heavy workload", "sentiment": "caution", "detail": "Engineering core plus biology prerequisites demand strong time management."},
            {"label": "Graduate outcomes", "sentiment": "positive", "detail": "Strong placement in med school, biotech, and PhD programs."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Biomedical Engineering Programs", "url": "https://www.usnews.com/best-colleges/rankings/biological-engineering-overall"},
            {"label": "McCormick — Biomedical Engineering", "url": "https://www.mccormick.northwestern.edu/biomedical/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "northwestern-psychology-general-bs": {
        "summary": (
            "Psychology is one of Weinberg's most popular majors, offering research opportunities "
            "in clinical, cognitive, and social psychology. Students value faculty labs and the "
            "path to graduate study, though large introductory sections and competitive research "
            "assistant placements are common."
        ),
        "themes": [
            {"label": "Research opportunities", "sentiment": "positive", "detail": "Undergraduates join faculty labs across clinical, cognitive, and social areas."},
            {"label": "Graduate preparation", "sentiment": "positive", "detail": "Strong track record for PhD and clinical psychology program admission."},
            {"label": "Large intro courses", "sentiment": "mixed", "detail": "High enrollment means big lectures in introductory psychology sequences."},
            {"label": "Competitive RA spots", "sentiment": "caution", "detail": "Research assistant positions are sought-after and require early outreach."},
        ],
        "sources": [
            {"label": "Niche — Northwestern University", "url": "https://www.niche.com/colleges/northwestern-university/"},
            {"label": "Weinberg — Department of Psychology", "url": "https://psychology.northwestern.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "northwestern-radio-television-and-digital-communication-ms": {
        "summary": (
            "The School of Communication's RTVF graduate program is a respected pipeline to film, "
            "television, and digital media production, with strong ties to Chicago and Los Angeles "
            "industry networks. Students praise hands-on production training, though funding is "
            "limited and career outcomes vary by concentration."
        ),
        "themes": [
            {"label": "Production training", "sentiment": "positive", "detail": "Hands-on film, TV, and digital media production courses are program strengths."},
            {"label": "Industry networks", "sentiment": "positive", "detail": "Alumni work across Hollywood, Chicago media, and streaming platforms."},
            {"label": "Limited funding", "sentiment": "caution", "detail": "Graduate funding is scarcer than in STEM PhD programs."},
            {"label": "Career variability", "sentiment": "mixed", "detail": "Outcomes depend heavily on portfolio quality and industry connections."},
        ],
        "sources": [
            {"label": "U.S. News — Best Fine Arts Programs", "url": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/northwestern-university-03058"},
            {"label": "School of Communication — RTVF", "url": "https://communication.northwestern.edu/departments/rtvf/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "northwestern-management-sciences-and-quantitative-methods-ms": {
        "summary": (
            "Kellogg's MS in Management Studies and analytics-oriented graduate offerings attract "
            "students seeking quantitative business training without a full MBA timeline. Reviewers "
            "note strong analytics curriculum and Kellogg brand access, though the program is newer "
            "than dedicated M.S. in Business Analytics peers and career services are MBA-centric."
        ),
        "themes": [
            {"label": "Quantitative curriculum", "sentiment": "positive", "detail": "Analytics, statistics, and decision-science courses anchor the program."},
            {"label": "Kellogg brand", "sentiment": "positive", "detail": "Access to Kellogg recruiting events and alumni network."},
            {"label": "Program maturity", "sentiment": "mixed", "detail": "Younger than dedicated MSBA programs at MIT Sloan or USC Marshall."},
            {"label": "MBA-centric services", "sentiment": "caution", "detail": "Career services are primarily oriented toward full-time MBA students."},
        ],
        "sources": [
            {"label": "Poets&Quants — Kellogg School of Management", "url": "https://poetsandquants.com/schools/kellogg-school-of-management-northwestern-university/"},
            {"label": "Kellogg — MS in Management Studies", "url": "https://www.kellogg.northwestern.edu/programs/msms.aspx"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    **DEPTH_REVIEWS,
}

_FLAGSHIP = "northwestern-mba-ms"
_TRACKS_BY_SLUG: dict = {}
_CLASS_PROFILE_BY_SLUG: dict = {}
_FACULTY_BY_SLUG: dict = {}
_COST_BY_SLUG: dict = {}
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "northwestern-computer-science-bs": ["computer science", "CS", "McCormick"],
    "northwestern-economics-bs": ["economics", "Weinberg"],
    "northwestern-mba-ms": ["MBA", "Kellogg"],
    "northwestern-law-prof": ["JD", "Pritzker School of Law"],
    "northwestern-medicine-prof": ["MD", "Feinberg", "medicine"],
    "northwestern-journalism-bs": ["journalism", "Medill"],
    "northwestern-biomedical-medical-engineering-bs": ["biomedical engineering", "BME"],
    "northwestern-psychology-general-bs": ["psychology", "Weinberg"],
    "northwestern-radio-television-and-digital-communication-ms": ["RTVF", "film", "television"],
    "northwestern-management-sciences-and-quantitative-methods-ms": ["MSMS", "analytics", "Kellogg"],
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
    return SCHOOL_WEBSITE.get(spec["school"], "https://www.northwestern.edu/")


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
    inst.founded_year = 1851
    inst.campus_setting = "suburban"
    if not inst.website_url:
        inst.website_url = "https://www.northwestern.edu"
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
                "note": "Northwestern PhD students typically receive full tuition plus a stipend.",
                "source": "The Graduate School — Funding",
                "source_url": "https://www.tgs.northwestern.edu/funding/",
            }
        else:
            p.tuition = None
            p.cost_data = {
                "note": "Tuition varies by program; see the official program tuition page.",
                "source": "Northwestern program tuition page",
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
