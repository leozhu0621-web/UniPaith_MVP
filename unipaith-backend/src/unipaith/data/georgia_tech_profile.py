"""Canonical Georgia Institute of Technology profile — the single source of truth.

Real, sourced data only (U.S. Dept. of Education College Scorecard, UNITID 139755 ·
NCES College Navigator / IPEDS · Georgia Tech Office of Institutional Research &
Planning Fact Book 2025 · Georgia Tech Common Data Set 2024-25 · the official QS /
Times Higher Education / U.S. News rankings · each college's official leadership /
about page · the GT Career Center Career & Salary Survey · the College Scorecard
Field-of-Study earnings by CIP). ``apply(session)`` idempotently enriches the
Georgia Tech institution row, upserts its six real academic colleges, and builds
Georgia Tech's program catalog across them.

Georgia Tech's academic structure (Office of the Provost): six colleges —
the College of Computing, the College of Engineering, the College of Sciences,
the Scheller College of Business, the College of Design, and the Ivan Allen
College of Liberal Arts. We model each onto the platform's ``School`` model.

It **flushes but does not commit** — the caller (the Alembic data migration, the CLI
script, or the dev seed) owns the transaction. It is a **no-op** (returns ``False``)
when Georgia Tech is absent, so it is safe to run against a fresh or CI database.
Re-running is safe: units key off ``(institution_id, name)`` and programs off ``slug``;
stale rows are reconciled without breaking foreign keys.

This mirrors ``mit_profile`` / ``princeton_profile`` / ``berkeley_profile`` so the
migration, the standalone script, and the dev seed all agree (DRY). Every figure
traces to a public, citable source; anything that could not be verified from a
first-party or two-independent-source basis is **omitted** (recorded in the relevant
``_standard.omitted`` list), never guessed. The canonical program set is the complete
federal College Scorecard Field-of-Study list for UNITID 139755, plus Georgia Tech's
flagship online degrees (OMSCS, OMS Analytics, OMS Cybersecurity), which are not in
the federal Field-of-Study rollup but are real, separately-administered programs.
"""

# ruff: noqa: E501

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.georgia_tech_ipeds_catalog import _IPEDS_CATALOG
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Georgia Institute of Technology-Main Campus"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-13"


def _standard(omitted: list[str] | None = None) -> dict:
    """The per-node provenance stamp the routine writes onto every enriched node."""
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }


# Institution-level fields that could NOT be verified from a citable source and are
# therefore honestly omitted rather than guessed.
_OMITTED_INSTITUTION = [
    # Georgia Tech's Career Center publishes full-time job-acceptance rates separately
    # by degree level (73% bachelor's, 81% master's, Class of 2024) at a low survey
    # knowledge rate, not a single combined "employed or continuing education" headline
    # rate across a stated class. The top employers/industries are reported instead.
    "school_outcomes.employed_or_continuing_ed",
]

# ── Institution-level data ────────────────────────────────────────────────
# Rankings are stored as {rank, year} objects (the page renders any ranking_data entry
# that is an object with a numeric `rank`). Ranks are quoted from the official ranking
# bodies for the 2026 editions.
RANKING_DATA: dict = {
    "ownership_type": "public",
    # Georgia Tech is accredited by the Southern Association of Colleges and Schools
    # Commission on Colleges (SACSCOC).
    "accreditor": "SACSCOC",
    # Carnegie basic classification (R1).
    "carnegie_classification": "Doctoral Universities: Very High Research Activity",
    # QS World University Rankings 2026: Georgia Tech is ranked joint #123 worldwide.
    "qs_world_university_rankings": {"rank": 123, "year": 2026},
    # THE World University Rankings 2026: joint #41 in the world.
    "times_higher_education": {"rank": 41, "year": 2026},
    # U.S. News Best Colleges (National Universities) 2026: #32 nationally (tied).
    "us_news_national": {"rank": 32, "year": 2026},
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below is
# complete, so a shallow merge is correct. Figures are College Scorecard (UNITID 139755)
# cross-checked against Georgia Tech's Fact Book 2025, Common Data Set 2024-25, and NCES
# College Navigator (IPEDS) where each publishes a metric.
SCHOOL_OUTCOMES: dict = {
    # College Scorecard overall admission rate (UNITID 139755).
    "admit_rate": 0.1407,
    # College Scorecard average annual net price (public).
    "avg_net_price": 12116,
    # College Scorecard median earnings 10 years after entry.
    "median_earnings_10yr": 102772,
    # College Scorecard six-year (150% of normal time) completion rate.
    "completion_rate_4yr_150pct": 0.9402,
    "graduation_rate_6yr": 0.9402,
    # College Scorecard first-year retention (full-time, pooled).
    "retention_rate_first_year": 0.9791,
    "financial_aid": {
        # College Scorecard: 13.9% Pell-grant rate; 16.97% federal-loan rate.
        "pell_grant_rate": 0.139,
        "federal_loan_rate": 0.1697,
        "median_debt_completers": 21672,
        # College Scorecard average annual cost of attendance (in-state academic year).
        "cost_of_attendance": 28167,
    },
    # Undergraduate race/ethnicity (Georgia Tech Common Data Set 2024-25 / Fact Book).
    "demographics": {
        "white": 0.35,
        "asian": 0.35,
        "hispanic": 0.09,
        "black": 0.09,
        "two_or_more": 0.05,
        "international": 0.08,
        # Fall 2024 undergraduate headcount 8,178 women / 20,592 total = ~0.40 (Fact Book).
        "women": 0.40,
    },
    # SAT/ACT 25th-75th percentiles of enrolled first-years (College Scorecard).
    "test_scores": {
        "sat_reading_25_75": [680, 750],
        "sat_math_25_75": [690, 790],
        "act_25_75": [30, 34],
    },
    # Georgia Tech main campus, Atlanta, Georgia (Tech Tower).
    "location": {"lat": 33.7756, "lng": -84.3963},
    "campus_basics": {"location": "Atlanta, Georgia"},
    "scale": {
        # Georgia Tech Fact Book 2025 faculty profile: 1,544 faculty (1,500 full-time).
        "faculty_count": 1544,
        # Common Data Set 2024-25: 21:1 student-faculty ratio.
        "student_faculty_ratio": "21:1",
        # Georgia Tech Fact Book 2025: research expenditures of ~$1.48 billion (FY2025).
        "research_expenditures_usd": 1476140296,
    },
    # Georgia Tech Career Center Career & Salary Survey (Class of 2024): top full-time
    # employers across degree levels.
    "top_employer_industries": [
        "Technology & software",
        "Engineering & aerospace",
        "Consulting",
        "Financial services",
        "Manufacturing",
    ],
    "research": {
        "labs": [
            "Georgia Tech Research Institute (GTRI)",
            "Institute for Robotics and Intelligent Machines (IRIM)",
            "Institute for Electronics and Nanotechnology (IEN)",
            "Parker H. Petit Institute for Bioengineering and Bioscience (IBB)",
            "Institute for Data Engineering and Science (IDEaS)",
            "Strategic Energy Institute (SEI)",
        ],
        "areas": [
            "Computing & artificial intelligence",
            "Robotics & autonomy",
            "Electronics & nanotechnology",
            "Bioengineering & bioscience",
            "Energy & sustainability",
            "Aerospace & manufacturing",
        ],
        "lab_links": {
            "Georgia Tech Research Institute (GTRI)": "https://gtri.gatech.edu/",
            "Institute for Robotics and Intelligent Machines (IRIM)": (
                "https://research.gatech.edu/robotics"
            ),
            "Institute for Electronics and Nanotechnology (IEN)": "https://ien.gatech.edu/",
            "Parker H. Petit Institute for Bioengineering and Bioscience (IBB)": (
                "https://ibb.gatech.edu/"
            ),
            "Institute for Data Engineering and Science (IDEaS)": "https://ideas.gatech.edu/",
            "Strategic Energy Institute (SEI)": "https://research.gatech.edu/energy",
        },
    },
    "campus_life": {
        # Georgia Tech competes in NCAA Division I (Atlantic Coast Conference) as the
        # Yellow Jackets.
        "athletics_division": "NCAA Division I (Atlantic Coast Conference)",
        "mascot": "Georgia Tech Yellow Jackets (Buzz)",
        "housing": "First-year on-campus housing (themed halls & living-learning communities)",
        "greek_life": "~20-24% of undergraduates join fraternities/sororities",
        "resources": [
            {"label": "Georgia Tech Yellow Jackets Athletics", "url": "https://ramblinwreck.com/"},
            {"label": "Georgia Tech Housing & Residence Life", "url": "https://housing.gatech.edu/"},
            {
                "label": "Campus Recreation Center (CRC)",
                "url": "https://crc.gatech.edu/",
            },
            {"label": "Stamps Health Services", "url": "https://health.gatech.edu/"},
            {"label": "Center for Career Discovery & Development", "url": "https://career.gatech.edu/"},
        ],
    },
    # Verified Wikimedia Commons campus gallery (each carries its own verified credit).
    # The detail hero shows [0] and opens the rest in a lightbox; the explore card uses
    # [0] for its gradient header. Landscape, recognizable outdoor campus scenes only.
    "campus_photos": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6c/GT_Campus.jpg/"
                "1920px-GT_Campus.jpg"
            ),
            "credit": "Wikimedia Commons / Maxicar (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/4/47/"
                "Tech_Tower_and_One_Coca-Cola_Plaza.jpg"
            ),
            "credit": "Wikimedia Commons / JJonahJackalope (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/"
                "Atlantic_Drive%2C_Georgia_Tech.jpg/1920px-Atlantic_Drive%2C_Georgia_Tech.jpg"
            ),
            "credit": "Wikimedia Commons / JJonahJackalope (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/"
                "Harrison_Square%2C_Georgia_Tech.jpg/1920px-Harrison_Square%2C_Georgia_Tech.jpg"
            ),
            "credit": "Wikimedia Commons / JJonahJackalope (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/"
                "Georgia_Tech_Skiles_walkway.jpg/1920px-Georgia_Tech_Skiles_walkway.jpg"
            ),
            "credit": "Wikimedia Commons / Matt Britt (CC BY-SA 3.0)",
        },
    ],
    "media_credit": "Wikimedia Commons / Maxicar (CC BY-SA 4.0)",
    "flagship": {
        # Georgia Tech Fact Book 2025: total enrollment Fall 2024 = 53,363 (driven by the
        # large online master's enrollment); undergraduate headcount 20,592.
        "enrollment_total": 53363,
        # Georgia Tech Office of Undergraduate Admission — 2025 First-Year Profile
        # (entering fall 2025): 66,912 first-year applicants, 8,819 admitted.
        "applicants": 66912,
        "admits": 8819,
        "admissions_cycle": "Entering class fall 2025 (Georgia Tech 2025 First-Year Profile)",
        # Founded 1885 as the Georgia School of Technology; renamed 1948.
        "founded_year": 1885,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Georgia Tech, UNITID 139755)",
            "url": "https://collegescorecard.ed.gov/school/?139755",
        },
        {
            "label": "NCES College Navigator — Georgia Institute of Technology (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=139755",
        },
        {
            "label": "Georgia Tech Office of Institutional Research & Planning — Fact Book",
            "url": "https://irp.gatech.edu/factbook",
        },
        {
            "label": "Georgia Tech Office of Undergraduate Admission — 2025 First-Year Profile",
            "url": "https://admission.gatech.edu/first-year/admission-decisions",
        },
        {
            "label": "QS World University Rankings 2026 — Georgia Institute of Technology",
            "url": "https://www.topuniversities.com/universities/georgia-institute-technology-georgia-tech",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — Georgia Tech (=41)",
            "url": "https://www.timeshighereducation.com/world-university-rankings/georgia-institute-technology",
        },
        {
            "label": "U.S. News — Georgia Tech No. 32 in National Universities (2026)",
            "url": "https://coe.gatech.edu/news/2025/09/undergrad-engineering-program-returns-no-3-us-news-2026-rankings",
        },
        {
            "label": "Georgia Tech Career Center — Career & Salary Survey (Class of 2024)",
            "url": "https://career.gatech.edu/employment-statistics/",
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it "Undergraduates");
# the total (53,363) lives in flagship.enrollment_total and renders as "Total enrollment".
# 20,592 = Georgia Tech Fact Book 2025 undergraduate headcount (Fall 2024).
UNDERGRAD_COUNT = 20592

DESCRIPTION = (
    "Georgia Institute of Technology is a public research university in Atlanta, GA, "
    "founded in 1885 as the Georgia School of Technology and renamed the Georgia "
    "Institute of Technology in 1948. One of the nation's leading technological "
    "universities, it enrolls roughly 20,600 undergraduates and more than 30,000 "
    "graduate students — over 53,000 in all, a total swelled by the largest online "
    "master's enrollment in the country.\n\n"
    "Georgia Tech is organized into six colleges: the College of Computing, the "
    "College of Engineering, the College of Sciences, the Scheller College of "
    "Business, the College of Design, and the Ivan Allen College of Liberal Arts. "
    "Its College of Engineering is ranked among the very best in the United States — "
    "No. 3 for undergraduate and No. 4 for graduate programs by U.S. News (2026), with "
    "perennially top-ranked aerospace, biomedical, civil, industrial and mechanical "
    "engineering — and its computing programs rank among the national elite. The "
    "Institute pioneered large-scale, low-cost online graduate education with the "
    "Online MS in Computer Science (OMSCS), Analytics, and Cybersecurity, each priced "
    "under roughly $12,000 in total tuition.\n\n"
    "Georgia Tech ranks No. 32 among national universities by U.S. News, joint No. 41 "
    "in the world by Times Higher Education, and joint No. 123 by QS. It is a top-tier "
    "research enterprise with roughly $1.48 billion in annual research expenditures, "
    "anchored by the Georgia Tech Research Institute and a network of interdisciplinary "
    "research institutes spanning robotics, electronics and nanotechnology, "
    "bioengineering, data science, and energy.\n\n"
    "As a public, in-state-friendly university, Georgia Tech holds the average net "
    "price near $12,000 a year and produces graduates with a median income of roughly "
    "$103,000 a decade after entry — among the strongest return-on-investment outcomes "
    "in American higher education."
)

# ── The six real academic colleges (display order) ──────────────────────────
_COC = "College of Computing"
_COE = "College of Engineering"
_COS = "College of Sciences"
_SCH = "Scheller College of Business"
_DES = "College of Design"
_IAC = "Ivan Allen College of Liberal Arts"

SCHOOLS: list[dict] = [
    {
        "name": _COE,
        "sort_order": 1,
        "description": (
            "Georgia Tech's largest college and one of the nation's best — ranked No. 3 "
            "for undergraduate and No. 4 for graduate engineering by U.S. News (2026), with "
            "all eleven of its programs consistently in the national top ten. It spans "
            "aerospace, biomedical, chemical and biomolecular, civil and environmental, "
            "electrical and computer, industrial and systems, materials science, mechanical, "
            "and nuclear engineering across its schools."
        ),
    },
    {
        "name": _COC,
        "sort_order": 2,
        "description": (
            "Founded in 1990 as one of the first standalone computing colleges in the "
            "United States, the College of Computing spans the Schools of Computer Science, "
            "Interactive Computing, Computational Science & Engineering, and Cybersecurity & "
            "Privacy. It pioneered large-scale online graduate education with the Online MS "
            "in Computer Science (OMSCS)."
        ),
    },
    {
        "name": _COS,
        "sort_order": 3,
        "description": (
            "Organized as a college in 1990, the College of Sciences advances discovery "
            "across six schools — biological sciences; chemistry and biochemistry; Earth and "
            "atmospheric sciences; mathematics; physics; and psychology — and is home to "
            "interdisciplinary institutes in bioengineering, astrophysics, and quantitative "
            "biosciences."
        ),
    },
    {
        "name": _SCH,
        "sort_order": 4,
        "description": (
            "Tracing its roots to 1912 as the School of Commerce and renamed in 2012 for "
            "Ernest Scheller Jr., the Scheller College of Business sits at the intersection "
            "of business and technology, offering AACSB-accredited BS, MS, MBA, PhD and "
            "graduate-certificate programs with nationally ranked full-time and part-time "
            "MBA tracks."
        ),
    },
    {
        "name": _DES,
        "sort_order": 5,
        "description": (
            "Born from architecture education that began at Georgia Tech in 1908 (the "
            "College of Architecture formed in 1975 and was renamed the College of Design "
            "in 2016), the College of Design spans architecture, industrial design, city "
            "and regional planning, building construction, and music technology across its "
            "schools."
        ),
    },
    {
        "name": _IAC,
        "sort_order": 6,
        "description": (
            "Established in 1990 and named for Atlanta civic leader Ivan Allen Jr., the "
            "Ivan Allen College of Liberal Arts grounds a technological university in the "
            "humanities and social sciences — economics, history and sociology, literature, "
            "media and communication, modern languages, public policy, and the Sam Nunn "
            "School of International Affairs."
        ),
    },
]

# Each college's official website (verified to resolve at author time).
_SCHOOL_WEBSITE: dict[str, str] = {
    _COE: "https://coe.gatech.edu/",
    _COC: "https://www.cc.gatech.edu/",
    _COS: "https://cos.gatech.edu/",
    _SCH: "https://www.scheller.gatech.edu/",
    _DES: "https://design.gatech.edu/",
    _IAC: "https://iac.gatech.edu/",
}

# Rich, sourced About-tab content per college. Deans + titles are quoted from the
# official Georgia Tech leadership org chart (May 2026) and each college's leadership
# page. Founding years are quoted from each college's official history page. Faculty
# counts are the Fall 2025 academic-faculty totals from the Georgia Tech Fact Book 2025.
_ABOUT_DETAIL: dict[str, dict] = {
    _COE: {
        "founded": 1885,
        "leadership": (
            "Mitchell L.R. Walker II — Dean and Southern Company Chair (effective June 15, "
            "2026, succeeding interim dean Doug Williams)"
        ),
        "faculty": "≈511 faculty (Fall 2025)",
        "research_centers": [
            "Georgia Tech Manufacturing Institute (GTMI)",
            "Institute for Electronics and Nanotechnology (IEN)",
            "Strategic Energy Institute (SEI)",
            "Parker H. Petit Institute for Bioengineering and Bioscience (IBB)",
        ],
        "source": {
            "label": "Georgia Tech College of Engineering — About / Leadership",
            "url": "https://coe.gatech.edu/about",
        },
    },
    _COC: {
        "founded": 1990,
        "leadership": "Vivek Sarkar — John P. Imlay Jr. Dean of Computing",
        "faculty": "≈145 faculty (Fall 2025)",
        "research_centers": [
            "Machine Learning Center (ML@GT)",
            "GVU Center",
            "Institute for Robotics and Intelligent Machines (IRIM)",
            "Constellations Center for Equity in Computing",
        ],
        "source": {
            "label": "Georgia Tech College of Computing — About",
            "url": "https://www.cc.gatech.edu/about",
        },
    },
    _COS: {
        "founded": 1990,
        "leadership": (
            "Susan Lozier — Dean and Betsy Middleton and John Clark Sutherland Chair"
        ),
        "faculty": "≈312 faculty (Fall 2025)",
        "research_centers": [
            "Parker H. Petit Institute for Bioengineering and Bioscience (IBB)",
            "Center for Relativistic Astrophysics",
            "Southeast Center for Mathematics and Biology (SCMB)",
        ],
        "source": {
            "label": "Georgia Tech College of Sciences — Dean",
            "url": "https://cos.gatech.edu/dean-susan-lozier",
        },
    },
    _SCH: {
        "founded": 1912,
        "leadership": "Anuj Mehrotra — Dean",
        "faculty": "≈103 faculty (Fall 2025)",
        "research_centers": [
            "Institute for Leadership and Social Impact",
            "Ray C. Anderson Center for Sustainable Business",
            "Business Analytics Center",
        ],
        "source": {
            "label": "Georgia Tech Scheller College of Business — About",
            "url": "https://www.scheller.gatech.edu/about-scheller/about-the-college/index.html",
        },
    },
    _DES: {
        "founded": 1908,
        "leadership": "Ellen Bassett — Dean",
        "faculty": "≈84 faculty (Fall 2025)",
        "research_centers": [
            "Center for Geographic Information Systems",
            "Center for Quality Growth and Regional Development",
            "Digital Building Laboratory",
        ],
        "source": {
            "label": "Georgia Tech College of Design — History / Leadership",
            "url": "https://design.gatech.edu/history",
        },
    },
    _IAC: {
        "founded": 1990,
        "leadership": "Amanda Murdie — Dean",
        "faculty": "≈195 faculty (Fall 2025)",
        "research_centers": [
            "Sam Nunn School of International Affairs",
            "Center for the Study of Women, Science, and Technology (WST)",
            "Center for International Strategy, Technology, and Policy (CISTP)",
        ],
        "source": {
            "label": "Georgia Tech Ivan Allen College of Liberal Arts — About",
            "url": "https://iac.gatech.edu/about",
        },
    },
}

# About-detail fields omitted per college (none — every college publishes its dean,
# founding year, faculty count, and research centers).
_ABOUT_OMITTED: dict[str, list[str]] = {}

# ── Channel feeds + official social links ──────────────────────────────────
# The daily content-ingest reads ``news_rss`` (RSS), ``events_feed`` (iCalendar or RSS),
# and ``keywords`` (filter gate). Without a real ``news_rss`` a node's Events & Updates
# tab is empty — so the institution and every college and program below carries a feed.
_GT_NEWS_RSS = "https://news.gatech.edu/rss.xml"
_GT_EVENTS_RSS = {"url": "https://calendar.gatech.edu/event-calendar-month.xml", "type": "rss"}
_SOCIAL_GT = {
    "instagram": "https://www.instagram.com/georgiatech/",
    "linkedin": "https://www.linkedin.com/school/georgia-institute-of-technology/",
    "x": "https://x.com/GeorgiaTech",
    "youtube": "https://www.youtube.com/georgiatech",
    "facebook": "https://www.facebook.com/georgiatech",
}

_INSTITUTION_CONTENT: dict = {
    "news_rss": _GT_NEWS_RSS,
    "news_url": "https://news.gatech.edu/",
    "news_curated": False,
    "events_feed": dict(_GT_EVENTS_RSS),
    "social": dict(_SOCIAL_GT),
}

# Per-college keyword gates so the shared Georgia Tech feed is filtered to
# college-relevant items (the institution has one central newsroom).
_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _COE: ["College of Engineering", "engineering", "aerospace", "biomedical", "mechanical"],
    _COC: ["College of Computing", "computing", "computer science", "machine learning", "OMSCS"],
    _COS: ["College of Sciences", "physics", "chemistry", "biology", "mathematics"],
    _SCH: ["Scheller College of Business", "Scheller", "MBA", "business"],
    _DES: ["College of Design", "architecture", "industrial design", "city planning"],
    _IAC: ["Ivan Allen College", "liberal arts", "public policy", "international affairs"],
}

_KW_STOP = {"and", "of", "the", "in", "for", "with", "science", "sciences", "engineering"}


def _school_content(name: str) -> dict:
    """A college's content_sources: Georgia Tech newsroom + events, filtered by keywords."""
    return {
        "news_rss": _GT_NEWS_RSS,
        "news_url": _SCHOOL_WEBSITE.get(name, "https://news.gatech.edu/"),
        "news_curated": False,
        "events_feed": dict(_GT_EVENTS_RSS),
        "keywords": list(_SCHOOL_KEYWORDS.get(name, [])),
        "social": dict(_SOCIAL_GT),
    }


def _program_keywords(spec: dict) -> list[str]:
    school_kw = list(_SCHOOL_KEYWORDS.get(spec["school"], []))
    name = (_FULL_NAME_BY_SLUG.get(spec["slug"]) or spec["program_name"]).replace("&", " ").replace(
        "/", " "
    )
    terms = [w for w in name.split() if len(w) > 3 and w.lower() not in _KW_STOP]
    program_term = " ".join(terms[:3]).strip()
    return ([program_term] if program_term else []) + school_kw


def _program_content(spec: dict) -> dict:
    base = _school_content(spec["school"])
    base["keywords"] = _program_keywords(spec)
    return base


# ── The program catalog ─────────────────────────────────────────────────────
# Georgia Tech has no hand-picked flagship subset: the breadth set is the full federal
# College Scorecard Field-of-Study list for UNITID 139755 (the deterministic federal
# view, in georgia_tech_ipeds_catalog), plus the flagship online degrees below (which
# the federal Field-of-Study rollup folds into their on-campus CIP — they are listed
# separately here because they are real, separately-administered programs with their own
# admissions, cost, and delivery format).
PROGRAMS: list[dict] = []


def _build_catalog() -> list[dict]:
    """Breadth-first program nodes from the IPEDS Field-of-Study catalog."""
    out: list[dict] = []
    seen: set[str] = set()
    for slug, school, name, dtype, cip, dur, fmt, desc in _IPEDS_CATALOG:
        if slug in seen:
            continue
        seen.add(slug)
        out.append({
            "slug": slug,
            "school": school,
            "program_name": name,
            "degree_type": dtype,
            "cip": cip,
            "duration_months": dur,
            "delivery_format": fmt,
            "description": desc,
        })
    return out


# Georgia Tech's flagship online master's degrees (real, separately-administered).
ONLINE_PROGRAMS: list[dict] = [
    {
        "slug": "gatech-oms-computer-science-ms",
        "school": _COC,
        "program_name": "Online Master of Science in Computer Science (OMSCS)",
        "degree_type": "masters",
        "cip": "11.07",
        "duration_months": 36,
        "delivery_format": "online",
        "description": (
            "The Online Master of Science in Computer Science (OMSCS) — delivered by the "
            "College of Computing with the same faculty and curriculum as the on-campus "
            "degree, for a total tuition under roughly $7,000. Launched in 2014, it is the "
            "largest computer science master's program in the world."
        ),
    },
    {
        "slug": "gatech-oms-analytics-ms",
        "school": _COC,
        "program_name": "Online Master of Science in Analytics (OMS Analytics)",
        "degree_type": "masters",
        "cip": "30.71",
        "duration_months": 36,
        "delivery_format": "online",
        "description": (
            "The Online Master of Science in Analytics (OMS Analytics) — an interdisciplinary "
            "degree delivered jointly by the College of Computing, the H. Milton Stewart School "
            "of Industrial & Systems Engineering, and the Scheller College of Business, for a "
            "total tuition under roughly $12,000 with three specialization tracks."
        ),
    },
    {
        "slug": "gatech-oms-cybersecurity-ms",
        "school": _COC,
        "program_name": "Online Master of Science in Cybersecurity (OMS Cybersecurity)",
        "degree_type": "masters",
        "cip": "11.10",
        "duration_months": 36,
        "delivery_format": "online",
        "description": (
            "The Online Master of Science in Cybersecurity (OMS Cybersecurity) — an "
            "interdisciplinary degree spanning the College of Computing, the School of "
            "Electrical & Computer Engineering, and the School of Public Policy, for a total "
            "tuition under roughly $12,000 (32 credit hours, part-time)."
        ),
    },
]

PROGRAMS += _build_catalog()
PROGRAMS += ONLINE_PROGRAMS
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

# Display-name overrides — the federal Field-of-Study titles are generic 4-digit CIP
# rollups; these are Georgia Tech's actual program names (verified against the official
# catalog) for the flagship degrees students search for.
_NAME_OVERRIDES: dict[str, str] = {
    "gatech-computer-and-information-sciences-general-bs": "Computer Science (BS)",
    "gatech-computer-and-information-sciences-general-ms": "Computer Science — HCI / Information (MS)",
    "gatech-computer-science-ms": "Computer Science (MS)",
    "gatech-business-administration-management-and-operations-bs": "Business Administration (BS)",
    "gatech-business-administration-management-and-operations-ms": "Master of Business Administration (MBA)",
    "gatech-research-and-experimental-psychology-bs": "Psychology (BS)",
    "gatech-international-relations-and-national-security-studies-bs": (
        "International Affairs (BS)"
    ),
    "gatech-management-sciences-and-quantitative-methods-ms": "Analytics (MS)",
}

_FULL_NAME_BY_SLUG: dict[str, str] = {p["slug"]: p["program_name"] for p in PROGRAMS}
_FULL_NAME_BY_SLUG.update(_NAME_OVERRIDES)

# Official program/department home pages for the flagship programs; others use their
# owning college's official site.
_WEBSITE_BY_SLUG: dict[str, str] = {
    "gatech-computer-and-information-sciences-general-bs": "https://www.cc.gatech.edu/academics/threads",
    "gatech-computer-science-ms": "https://www.cc.gatech.edu/academics/degree-programs/masters",
    "gatech-oms-computer-science-ms": "https://omscs.gatech.edu/",
    "gatech-oms-analytics-ms": "https://pe.gatech.edu/degrees/analytics",
    "gatech-oms-cybersecurity-ms": "https://pe.gatech.edu/degrees/cybersecurity",
    "gatech-industrial-engineering-bs": "https://www.isye.gatech.edu/academics/bachelors/bsie",
    "gatech-aerospace-aeronautical-and-astronautical-space-engineering-bs": "https://ae.gatech.edu/",
    "gatech-biomedical-medical-engineering-bs": "https://bme.gatech.edu/bme/",
    "gatech-mechanical-engineering-bs": "https://www.me.gatech.edu/",
    "gatech-electrical-electronics-and-communications-engineering-bs": "https://ece.gatech.edu/",
    "gatech-computer-engineering-bs": "https://ece.gatech.edu/computer-engineering",
    "gatech-chemical-engineering-bs": "https://chbe.gatech.edu/",
    "gatech-civil-engineering-bs": "https://ce.gatech.edu/",
    "gatech-business-administration-management-and-operations-bs": "https://www.scheller.gatech.edu/degrees/undergraduate/index.html",
    "gatech-business-administration-management-and-operations-ms": "https://www.scheller.gatech.edu/degrees/full-time-mba/index.html",
}

# ── Who-it's-for + highlights (catalog baselines) ──────────────────────────
_WHO_BASELINE = (
    "Students seeking a rigorous, hands-on technological education at a top public "
    "research university — with strong industry ties, a major-city setting in Atlanta, "
    "and one of the best returns on investment in U.S. higher education."
)
_HL_BASELINE = ["Top public research university", "Atlanta innovation hub", "Strong ROI"]
_WHO_BY_SLUG: dict[str, str] = {
    "gatech-computer-and-information-sciences-general-bs": (
        "Technically driven students who want a flexible, top-ranked CS degree built around "
        "Georgia Tech's eight 'Threads' specializations and deep industry/co-op access."
    ),
    "gatech-oms-computer-science-ms": (
        "Working software professionals seeking an affordable, fully-online, top-ranked "
        "CS master's with the same curriculum as the on-campus degree."
    ),
    "gatech-oms-analytics-ms": (
        "Working professionals who want a top-ranked, fully-online analytics/data-science "
        "master's spanning computing, operations research, and business — for under ~$12K."
    ),
    "gatech-industrial-engineering-bs": (
        "Students drawn to optimization, operations, supply chains, and data — in the "
        "nation's No. 1-ranked industrial engineering program (ISyE)."
    ),
}
_HL_BY_SLUG: dict[str, list[str]] = {
    "gatech-computer-and-information-sciences-general-bs": [
        "Threads curriculum (8 specializations)",
        "Top-tier computing faculty",
        "Strong co-op & tech placement",
    ],
    "gatech-oms-computer-science-ms": [
        "World's largest CS master's",
        "Total tuition under ~$7,000",
        "Same curriculum as on-campus",
    ],
    "gatech-oms-analytics-ms": [
        "Top-5 analytics program",
        "3 specialization tracks",
        "Total tuition under ~$12,000",
    ],
    "gatech-industrial-engineering-bs": [
        "No. 1 ISyE nationally (U.S. News)",
        "Optimization & supply chain",
        "Strong analytics core",
    ],
}

# ── Curriculum / tracks, where published ───────────────────────────────────
_TRACKS_BY_SLUG: dict[str, dict] = {
    "gatech-computer-and-information-sciences-general-bs": {
        "label": "Computer Science 'Threads'",
        "note": (
            "Georgia Tech's BS in Computer Science is built around eight official 'Threads' "
            "— students combine two to shape a personalized specialization."
        ),
        "items": [
            {"name": "Intelligence"},
            {"name": "Information Internetworks"},
            {"name": "Systems & Architecture"},
            {"name": "Theory"},
            {"name": "Modeling & Simulation"},
            {"name": "People (Human-Computer Interaction)"},
            {"name": "Media"},
            {"name": "Devices"},
        ],
        "source": "Georgia Tech College of Computing — Threads",
        "source_url": "https://www.cc.gatech.edu/academics/threads",
    },
    "gatech-oms-analytics-ms": {
        "label": "OMS Analytics specialization tracks",
        "note": "The Online MS in Analytics offers three specialization tracks.",
        "items": [
            {"name": "Analytical Tools"},
            {"name": "Business Analytics"},
            {"name": "Computational Data Analytics"},
        ],
        "source": "Georgia Tech Professional Education — OMS Analytics",
        "source_url": "https://pe.gatech.edu/degrees/analytics",
    },
}

# ── Program cost ────────────────────────────────────────────────────────────
# Undergraduate published tuition (College Scorecard, UNITID 139755): in-state vs
# out-of-state, since Georgia Tech is a public university.
_TUITION_UG_IN = 12058
_TUITION_UG_OUT = 34484
_UNDERGRAD_COA = 28167
_AVG_NET_PRICE = 12116
# Graduate (Atlanta campus) annual tuition (GT Bursar 2024-25; full-time, two semesters).
_TUITION_GRAD_IN = 14416
_TUITION_GRAD_OUT = 30598

_COST_BY_SLUG: dict[str, dict] = {
    "gatech-oms-computer-science-ms": {
        "tuition_usd": 6750,
        "total_cost_of_attendance": 6750,
        "funded": False,
        "note": (
            "Flat $225 per credit hour for all students (30-credit-hour degree ≈ $6,750 total "
            "tuition), plus a small per-term online learning fee. Among the most affordable "
            "graduate degrees in the U.S."
        ),
        "source": "Georgia Tech OMSCS — Cost & Payment Schedule",
        "source_url": "https://omscs.gatech.edu/cost-and-payment-schedule",
        "year": "2024-25",
    },
    "gatech-oms-analytics-ms": {
        "tuition_usd": 11880,
        "total_cost_of_attendance": 11880,
        "funded": False,
        "note": (
            "Flat $327 per credit hour (36-credit-hour degree); total tuition by residency: "
            "GA $11,880 / U.S. $12,348 / International $12,960, plus a small per-term online "
            "learning fee."
        ),
        "source": "Georgia Tech Professional Education — OMS Analytics",
        "source_url": "https://pe.gatech.edu/degrees/analytics",
        "year": "2024-25",
    },
    "gatech-oms-cybersecurity-ms": {
        "tuition_usd": 11808,
        "total_cost_of_attendance": 11808,
        "funded": False,
        "note": (
            "Flat $369 per credit hour (32-credit-hour degree ≈ $11,808 total tuition, under "
            "$12,000), plus a small per-term online learning fee."
        ),
        "source": "Georgia Tech Professional Education — OMS Cybersecurity",
        "source_url": "https://pe.gatech.edu/degrees/cybersecurity",
        "year": "2024-25",
    },
}


def _cost_for(spec: dict) -> dict:
    """Cost for a program by degree type (online programs use _COST_BY_SLUG override)."""
    override = _COST_BY_SLUG.get(spec["slug"])
    if override is not None:
        return dict(override)
    if spec["degree_type"] == "bachelors":
        return {
            "tuition_usd": _TUITION_UG_IN,
            "tuition_in_state": _TUITION_UG_IN,
            "tuition_out_of_state": _TUITION_UG_OUT,
            "total_cost_of_attendance": _UNDERGRAD_COA,
            "avg_net_price": _AVG_NET_PRICE,
            "breakdown": {
                "tuition_in_state": _TUITION_UG_IN,
                "tuition_out_of_state": _TUITION_UG_OUT,
                "total_cost_of_attendance": _UNDERGRAD_COA,
            },
            "funded": False,
            "note": (
                "Georgia Tech is a public university: published undergraduate tuition is "
                "$12,058 for Georgia residents and $34,484 for non-residents (2024-25). The "
                "average net price after aid is ≈ $12,100 per year."
            ),
            "source": "U.S. Dept. of Education College Scorecard (UNITID 139755)",
            "source_url": "https://collegescorecard.ed.gov/school/?139755",
            "year": "2024-25",
        }
    return {
        "tuition_usd": _TUITION_GRAD_IN,
        "tuition_in_state": _TUITION_GRAD_IN,
        "tuition_out_of_state": _TUITION_GRAD_OUT,
        "funded": False,
        "breakdown": {
            "tuition_in_state": _TUITION_GRAD_IN,
            "tuition_out_of_state": _TUITION_GRAD_OUT,
            "per_credit_in_state": 601,
            "per_credit_out_of_state": 1276,
        },
        "note": (
            "Georgia Tech graduate tuition (Atlanta campus, full-time): ≈ $14,416/yr for "
            "Georgia residents and ≈ $30,598/yr for non-residents ($601 / $1,276 per credit "
            "hour, 2024-25). Many doctoral students are funded via assistantships. "
            "Program-specific rates are set by the GT Bursar."
        ),
        "source": "Georgia Tech Office of the Bursar — Graduate Tuition Rates 2024-25",
        "source_url": "https://bursar.gatech.edu/tuition-fees",
        "year": "2024-25",
    }

# ── Program-specific outcomes (College Scorecard Field of Study, by CIP) ─────
# Where the federal College Scorecard publishes a Field-of-Study median earnings (one
# year after completion) for an awarded CIP at UNITID 139755, we use it (program scope).
# Programs whose CIP earnings are suppressed fall back to the institution 10-year median.
# Tuples are (median_earnings_1yr, cip).
_FOS_OUTCOMES: dict[str, tuple[int, str]] = {
    "gatech-architecture-bs": (52288, "04.02"),
    "gatech-architecture-ms": (53970, "04.02"),
    "gatech-city-urban-community-and-regional-planning-ms": (58367, "04.03"),
    "gatech-architectural-sciences-and-technology-ms": (60914, "04.09"),
    "gatech-radio-television-and-digital-communication-bs": (67997, "09.07"),
    "gatech-computer-and-information-sciences-general-bs": (89428, "11.01"),
    "gatech-computer-and-information-sciences-general-ms": (121610, "11.01"),
    "gatech-computer-science-ms": (98509, "11.07"),
    "gatech-aerospace-aeronautical-and-astronautical-space-engineering-bs": (67907, "14.02"),
    "gatech-aerospace-aeronautical-and-astronautical-space-engineering-ms": (90098, "14.02"),
    "gatech-biomedical-medical-engineering-bs": (67345, "14.05"),
    "gatech-biomedical-medical-engineering-ms": (80304, "14.05"),
    "gatech-chemical-engineering-bs": (75560, "14.07"),
    "gatech-civil-engineering-bs": (66586, "14.08"),
    "gatech-civil-engineering-ms": (70633, "14.08"),
    "gatech-computer-engineering-bs": (81067, "14.09"),
    "gatech-electrical-electronics-and-communications-engineering-bs": (74050, "14.10"),
    "gatech-electrical-electronics-and-communications-engineering-ms": (94709, "14.10"),
    "gatech-environmental-environmental-health-engineering-bs": (60224, "14.14"),
    "gatech-materials-engineering-bs": (69159, "14.18"),
    "gatech-mechanical-engineering-bs": (69872, "14.19"),
    "gatech-mechanical-engineering-ms": (85001, "14.19"),
    "gatech-nuclear-engineering-bs": (73557, "14.23"),
    "gatech-systems-engineering-ms": (117910, "14.27"),
    "gatech-industrial-engineering-bs": (74354, "14.35"),
    "gatech-industrial-engineering-ms": (89941, "14.35"),
    "gatech-biochemistry-biophysics-and-molecular-biology-bs": (32372, "26.02"),
    "gatech-science-technology-and-society-bs": (33322, "30.15"),
    "gatech-physics-bs": (34598, "40.08"),
    "gatech-research-and-experimental-psychology-bs": (29757, "42.27"),
    "gatech-international-relations-and-national-security-studies-ms": (53768, "45.09"),
    "gatech-design-and-applied-arts-bs": (48199, "50.04"),
    "gatech-rehabilitation-and-therapeutic-professions-ms": (39430, "51.23"),
    "gatech-business-administration-management-and-operations-bs": (61121, "52.02"),
    "gatech-business-administration-management-and-operations-ms": (122073, "52.02"),
    "gatech-management-sciences-and-quantitative-methods-ms": (126074, "52.13"),
}

# Verbatim methodology for the program-scope Scorecard FOS earnings figure.
_FOS_CONDITIONS = (
    "Median earnings of graduates who received federal financial aid, measured "
    "approximately one year after program completion; reported by the U.S. Department of "
    "Education College Scorecard Field of Study by 4-digit CIP code. Programs with too "
    "few completers are suppressed."
)

# Institution-wide outcomes fallback (College Scorecard, UNITID 139755), used for degree
# programs whose program-level one-year earnings are suppressed.
_OUTCOMES_INSTITUTION = {
    "median_salary": 102772,
    "scope": "institution",
    "conditions": (
        "Georgia Tech institution-wide median earnings ten years after entry (College "
        "Scorecard, UNITID 139755); a program-level one-year earnings figure is not "
        "published (suppressed) for this field of study."
    ),
    "source": "U.S. Dept. of Education College Scorecard (UNITID 139755)",
    "source_url": "https://collegescorecard.ed.gov/school/?139755",
}

# The online flagship degrees share the on-campus CIP earnings of their home discipline.
_FOS_OUTCOMES["gatech-oms-computer-science-ms"] = (98509, "11.07")
_FOS_OUTCOMES["gatech-oms-analytics-ms"] = (126074, "52.13")
_FOS_OUTCOMES["gatech-oms-cybersecurity-ms"] = (121610, "11.01")

# ── Class profile, where published ─────────────────────────────────────────
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    "gatech-oms-computer-science-ms": {
        "cohort_size": (
            "The largest computer science master's program in the world (enrollment in the "
            "tens of thousands since its 2014 launch)"
        ),
        "note": (
            "Georgia Tech's OMSCS is widely reported as the world's largest CS master's by "
            "enrollment; an exact current-term cohort size is not published as a single figure."
        ),
        "source": "Georgia Tech College of Computing — OMSCS",
        "source_url": "https://omscs.gatech.edu/",
    },
}

# ── Application requirements ────────────────────────────────────────────────
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission.",
}
# Undergraduate (first-year) admission via the Common Application; Georgia Tech offers a
# two-tier Early Action plan (EA I for Georgia students, EA II for non-Georgia) plus
# Regular Decision.
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application + Georgia Tech questions", "required": True},
        {"name": "Secondary-school transcript", "required": True},
        {"name": "Counselor recommendation / school report", "required": True},
        {
            "name": "SAT or ACT scores",
            "required": True,
            "note": "Georgia Tech requires SAT or ACT scores for first-year applicants; verify the current testing policy on the admission site.",
        },
        {"name": "Application fee ($75 domestic / $85 international); fee waivers available", "required": True},
    ],
    "deadlines": [
        {"round": "Early Action I (Georgia students)", "date": "Mid-October"},
        {"round": "Early Action II (non-Georgia students)", "date": "Early November"},
        {"round": "Regular Decision", "date": "Early January"},
    ],
    "recommendations": {
        "required": 1,
        "note": "A counselor recommendation/school report is required; teacher recommendations are optional.",
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "Duolingo English Test"],
            "required": True,
            "note": "Required for applicants whose first language is not English (waivers may apply).",
        },
        "visa": _INTL_VISA,
        "sources": [
            {"label": "Georgia Tech Undergraduate Admission — Apply", "url": "https://admission.gatech.edu/"}
        ],
    },
    "source": "Georgia Tech Office of Undergraduate Admission",
    "source_url": "https://admission.gatech.edu/first-year/apply",
}

# Graduate admission via Georgia Tech Graduate Studies + the academic program/department.
_REQ_GRAD = {
    "materials": [
        {"name": "Georgia Tech Graduate Studies online application", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Three letters of recommendation", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Résumé / CV", "required": True},
        {
            "name": "GRE scores",
            "required": False,
            "note": "GRE requirements vary by program; many Georgia Tech graduate programs are GRE-optional.",
        },
        {"name": "Application fee ($75 domestic / $85 international)", "required": True},
    ],
    "deadlines": [
        {"round": "Fall admission (typical)", "date": "December–January (varies by program)"},
    ],
    "recommendations": {
        "required": 3,
        "note": "Three letters of recommendation submitted through the graduate application.",
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": True,
            "note": "Required for applicants whose first language is not English (waivers may apply).",
        },
        "visa": _INTL_VISA,
        "sources": [
            {"label": "Georgia Tech Graduate Studies — Apply", "url": "https://grad.gatech.edu/admissions"}
        ],
    },
    "source": "Georgia Tech Graduate Studies",
    "source_url": "https://grad.gatech.edu/admissions",
}

# Online flagship degrees (OMSCS / OMS Analytics / OMS Cybersecurity) admission via
# Georgia Tech Professional Education / the College of Computing.
_REQ_ONLINE = {
    "materials": [
        {"name": "Online graduate application", "required": True},
        {"name": "Statement of purpose / background statement", "required": True},
        {"name": "Three letters of recommendation", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Résumé / CV", "required": True},
        {"name": "GRE", "required": False, "note": "No GRE/GMAT required for the online MS degrees."},
        {"name": "Application fee", "required": True},
    ],
    "deadlines": [
        {"round": "Fall (August) start", "date": "Spring application window"},
        {"round": "Spring (January) start", "date": "Fall application window"},
    ],
    "recommendations": {
        "required": 3,
        "note": "Three letters of recommendation; no GRE/GMAT required.",
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": True,
            "note": "Required for applicants whose first language is not English (waivers may apply).",
        },
        "visa": {"types": [], "note": "Fully online — no U.S. student visa is issued for these programs."},
        "sources": [
            {"label": "Georgia Tech Professional Education — Online Degrees", "url": "https://pe.gatech.edu/degrees"}
        ],
    },
    "source": "Georgia Tech Professional Education",
    "source_url": "https://pe.gatech.edu/degrees",
}


def _requirements_for(spec: dict) -> dict:
    """Pick the admissions requirement set for a program by delivery / degree type."""
    if spec.get("delivery_format") == "online":
        return dict(_REQ_ONLINE)
    if spec["degree_type"] == "bachelors":
        return dict(_REQ_UNDERGRAD)
    return dict(_REQ_GRAD)

# ── Faculty (lead + directory link) ────────────────────────────────────────
# Georgia Tech does not publish a single per-program lead-faculty contact with durable
# titles; rather than risk a stale title, faculty leads are omitted per program (recorded
# in _standard.omitted) and students are pointed to each department's faculty directory.
_FACULTY_BY_SLUG: dict[str, dict] = {}

# Annual degrees-conferred per CIP is not used as a class-profile proxy here (the federal
# award counts are not consistently published per Georgia Tech program in a citable form).
_AWARDS_BY_SLUG: dict[str, int] = {}

# ── Aggregated, cited student/third-party review themes (coverable programs) ──
_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not individual verbatim "
    "reviews."
)
_SRC_USNEWS_UG_ENG = {
    "label": "U.S. News 2026 — Georgia Tech undergraduate engineering rankings (College of Engineering)",
    "url": "https://coe.gatech.edu/news/2025/09/undergrad-engineering-program-returns-no-3-us-news-2026-rankings",
}
_SRC_USNEWS_GRAD = {
    "label": "Georgia Tech — Graduate Programs in 2026 U.S. News rankings",
    "url": "https://news.gatech.edu/news/2026/04/07/georgia-tech-graduate-programs-stand-among-nations-best-2026-rankings",
}
_SRC_NICHE = {
    "label": "Niche — Georgia Institute of Technology",
    "url": "https://www.niche.com/colleges/georgia-institute-of-technology/",
}
_CAUTION_RIGOR = {
    "label": "Demanding & rigorous",
    "sentiment": "caution",
    "detail": (
        "A heavy workload, rigorous grading, and a competitive culture are recurring themes; "
        "students are expected to be proactive about opportunities."
    ),
}

_REVIEWS_BY_SLUG: dict[str, dict] = {
    "gatech-computer-and-information-sciences-general-bs": {
        "summary": (
            "Students and college guides rate Georgia Tech's BS in Computer Science among the "
            "best in the country — praised for its flexible 'Threads' curriculum, world-class "
            "computing faculty, strong co-op/internship pipeline, and excellent placement into "
            "top tech firms; U.S. News ranks Georgia Tech's computer science among the national "
            "elite. Common cautions are large introductory classes, a demanding workload, and "
            "a fast pace."
        ),
        "themes": [
            {"label": "Academic strength", "sentiment": "positive", "detail": "A top-ranked CS program with leading faculty and research."},
            {"label": "Flexible Threads curriculum", "sentiment": "positive", "detail": "The eight-Thread structure lets students tailor a specialization."},
            {"label": "Tech placement & co-op", "sentiment": "positive", "detail": "Strong co-op program and placement into major technology employers."},
            {"label": "Large intro classes", "sentiment": "caution", "detail": "Popular introductory courses can be very large."},
            _CAUTION_RIGOR,
        ],
        "sources": [_SRC_USNEWS_GRAD, _SRC_NICHE],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-computer-science-ms": {
        "summary": (
            "Georgia Tech's on-campus MS in Computer Science is widely regarded as a top-tier "
            "graduate degree — U.S. News ranks Georgia Tech No. 7 nationally among computer "
            "science graduate programs (2026) — with deep specialization options and strong "
            "research and industry ties; common cautions are intense rigor and high competition "
            "for advisors and funding."
        ),
        "themes": [
            {"label": "Top-7 CS graduate program", "sentiment": "positive", "detail": "Among the nation's elite CS graduate programs (U.S. News 2026)."},
            {"label": "Specialization depth", "sentiment": "positive", "detail": "Strong breadth across AI, systems, theory, HCI, and security."},
            {"label": "Research & industry ties", "sentiment": "positive", "detail": "Extensive research labs and Atlanta-area industry connections."},
            _CAUTION_RIGOR,
        ],
        "sources": [_SRC_USNEWS_GRAD, _SRC_NICHE],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-oms-computer-science-ms": {
        "summary": (
            "OMSCS is consistently praised as one of the best values in graduate education — "
            "the same top-ranked curriculum as the on-campus degree for under roughly $7,000 "
            "total, fully online and flexible for working professionals; it is the largest CS "
            "master's program in the world. Common cautions are that it demands strong "
            "self-discipline, offers limited synchronous interaction, and that some courses are "
            "very challenging."
        ),
        "themes": [
            {"label": "Exceptional value", "sentiment": "positive", "detail": "Total tuition under ~$7,000 for a top-ranked CS master's."},
            {"label": "Flexible & online", "sentiment": "positive", "detail": "Fully online and part-time — designed for working professionals."},
            {"label": "Same curriculum & faculty", "sentiment": "positive", "detail": "Shares the on-campus curriculum and instructors."},
            {"label": "Requires self-discipline", "sentiment": "caution", "detail": "Asynchronous format demands strong time management and motivation."},
            {"label": "Limited interaction", "sentiment": "caution", "detail": "Less direct faculty/peer interaction than an on-campus program."},
        ],
        "sources": [
            {"label": "Georgia Tech College of Computing — OMSCS", "url": "https://omscs.gatech.edu/"},
            _SRC_USNEWS_GRAD,
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-oms-analytics-ms": {
        "summary": (
            "OMS Analytics is highly rated as an affordable, top-ranked online analytics/data "
            "science master's — under roughly $12,000 total, with three specialization tracks "
            "spanning computing, operations research, and business, and no GRE requirement. "
            "Common cautions are a quantitatively demanding core and the self-discipline an "
            "online, part-time format requires."
        ),
        "themes": [
            {"label": "Top-ranked & affordable", "sentiment": "positive", "detail": "A top-5 analytics program for total tuition under ~$12,000."},
            {"label": "Interdisciplinary tracks", "sentiment": "positive", "detail": "Three tracks across computing, ISyE, and Scheller business."},
            {"label": "Flexible for professionals", "sentiment": "positive", "detail": "Fully online, part-time, with no GRE/GMAT required."},
            {"label": "Quantitatively demanding", "sentiment": "caution", "detail": "A rigorous statistics/programming core challenges many students."},
            {"label": "Self-paced discipline", "sentiment": "caution", "detail": "The online format requires strong self-motivation."},
        ],
        "sources": [
            {"label": "Georgia Tech Professional Education — OMS Analytics", "url": "https://pe.gatech.edu/degrees/analytics"},
            _SRC_NICHE,
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-oms-cybersecurity-ms": {
        "summary": (
            "OMS Cybersecurity is praised as the only fully-online interdisciplinary "
            "cybersecurity master's from a top-10 public university, for under roughly $12,000 "
            "total — spanning the College of Computing, ECE, and public policy. Common cautions "
            "are a technically rigorous core and the discipline an online, part-time format "
            "requires."
        ),
        "themes": [
            {"label": "Affordable & online", "sentiment": "positive", "detail": "Total tuition under ~$12,000 from a top-10 public university."},
            {"label": "Interdisciplinary scope", "sentiment": "positive", "detail": "Spans computing, electrical & computer engineering, and policy."},
            {"label": "Built for professionals", "sentiment": "positive", "detail": "Part-time, fully online, designed around working schedules."},
            {"label": "Technically demanding", "sentiment": "caution", "detail": "A rigorous technical core challenges less-prepared students."},
        ],
        "sources": [
            {"label": "Georgia Tech Professional Education — OMS Cybersecurity", "url": "https://pe.gatech.edu/degrees/cybersecurity"},
            _SRC_USNEWS_GRAD,
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-industrial-engineering-bs": {
        "summary": (
            "Georgia Tech's BS in Industrial Engineering (ISyE) is ranked No. 1 in the nation "
            "by U.S. News (2026) — students praise the optimization, supply-chain, and analytics "
            "training and outstanding recruiting; common cautions are heavy quantitative rigor "
            "and large core classes."
        ),
        "themes": [
            {"label": "No. 1 ISyE nationally", "sentiment": "positive", "detail": "Ranked first among undergraduate industrial engineering programs (U.S. News 2026)."},
            {"label": "Optimization & analytics", "sentiment": "positive", "detail": "Strong training in operations research, supply chain, and data analytics."},
            {"label": "Excellent recruiting", "sentiment": "positive", "detail": "Broad employer demand across consulting, logistics, and tech."},
            _CAUTION_RIGOR,
        ],
        "sources": [_SRC_USNEWS_UG_ENG, {"label": "Georgia Tech ISyE", "url": "https://www.isye.gatech.edu/"}],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-aerospace-aeronautical-and-astronautical-space-engineering-bs": {
        "summary": (
            "Georgia Tech's BS in Aerospace Engineering (Daniel Guggenheim School) is ranked "
            "No. 2 nationally (No. 1 among publics) by U.S. News (2026) — praised for its "
            "rigorous aero/astro curriculum, research opportunities, and aerospace-industry "
            "ties; common cautions are an intense workload and demanding coursework."
        ),
        "themes": [
            {"label": "No. 2 aerospace nationally", "sentiment": "positive", "detail": "Among the top aerospace programs (U.S. News 2026; No. 1 public)."},
            {"label": "Research & industry ties", "sentiment": "positive", "detail": "Strong ties to NASA, defense, and the aerospace industry."},
            {"label": "Rigorous curriculum", "sentiment": "positive", "detail": "A comprehensive aeronautics and astronautics core."},
            _CAUTION_RIGOR,
        ],
        "sources": [_SRC_USNEWS_UG_ENG, {"label": "Georgia Tech Aerospace Engineering", "url": "https://ae.gatech.edu/"}],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-biomedical-medical-engineering-bs": {
        "summary": (
            "Georgia Tech's BS in Biomedical Engineering (the Coulter Department, joint with "
            "Emory) is ranked No. 1 in the nation by U.S. News (2026) — praised for its "
            "problem-based design curriculum and research access; common cautions are a "
            "demanding workload and a competitive path to industry/medical careers."
        ),
        "themes": [
            {"label": "No. 1 BME nationally", "sentiment": "positive", "detail": "Ranked first among undergraduate biomedical engineering programs (U.S. News 2026)."},
            {"label": "Problem-based design", "sentiment": "positive", "detail": "A distinctive design-focused, hands-on curriculum."},
            {"label": "Joint with Emory", "sentiment": "positive", "detail": "The Coulter Department spans Georgia Tech and Emory medicine."},
            _CAUTION_RIGOR,
        ],
        "sources": [_SRC_USNEWS_UG_ENG, {"label": "Georgia Tech Coulter BME", "url": "https://bme.gatech.edu/bme/"}],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-mechanical-engineering-bs": {
        "summary": (
            "Georgia Tech's BS in Mechanical Engineering (the Woodruff School) is ranked No. 4 "
            "nationally by U.S. News (2026) — praised for breadth, design and lab experience, "
            "and recruiting; common cautions are a heavy workload and large class sizes in the "
            "core."
        ),
        "themes": [
            {"label": "No. 4 mechanical nationally", "sentiment": "positive", "detail": "Among the top mechanical engineering programs (U.S. News 2026)."},
            {"label": "Breadth & design labs", "sentiment": "positive", "detail": "Strong hands-on design and laboratory experience."},
            {"label": "Strong recruiting", "sentiment": "positive", "detail": "Broad employer demand across industries."},
            _CAUTION_RIGOR,
        ],
        "sources": [_SRC_USNEWS_UG_ENG, {"label": "Georgia Tech Woodruff School of ME", "url": "https://www.me.gatech.edu/"}],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-electrical-electronics-and-communications-engineering-bs": {
        "summary": (
            "Georgia Tech's BS in Electrical Engineering is ranked No. 3 nationally by U.S. "
            "News (2026) — praised for its rigorous ECE curriculum, research breadth, and "
            "industry ties; common cautions are demanding coursework and a fast pace."
        ),
        "themes": [
            {"label": "No. 3 electrical nationally", "sentiment": "positive", "detail": "Among the top electrical engineering programs (U.S. News 2026)."},
            {"label": "Research breadth", "sentiment": "positive", "detail": "Wide-ranging research across electronics, signals, and systems."},
            {"label": "Industry ties", "sentiment": "positive", "detail": "Strong connections to semiconductor, telecom, and tech employers."},
            _CAUTION_RIGOR,
        ],
        "sources": [_SRC_USNEWS_UG_ENG, {"label": "Georgia Tech School of ECE", "url": "https://ece.gatech.edu/"}],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-computer-engineering-bs": {
        "summary": (
            "Georgia Tech's BS in Computer Engineering (offered jointly by ECE and Computing) "
            "is ranked No. 6 nationally by U.S. News (2026) — praised for bridging hardware and "
            "software with strong recruiting; common cautions are heavy rigor and a demanding "
            "core."
        ),
        "themes": [
            {"label": "No. 6 computer engineering", "sentiment": "positive", "detail": "Among the top computer engineering programs (U.S. News 2026)."},
            {"label": "Hardware + software", "sentiment": "positive", "detail": "Bridges electrical engineering and computing."},
            {"label": "Strong placement", "sentiment": "positive", "detail": "Broad demand across tech and embedded-systems employers."},
            _CAUTION_RIGOR,
        ],
        "sources": [_SRC_USNEWS_UG_ENG, {"label": "Georgia Tech Computer Engineering", "url": "https://ece.gatech.edu/computer-engineering"}],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-chemical-engineering-bs": {
        "summary": (
            "Georgia Tech's BS in Chemical & Biomolecular Engineering is ranked No. 2 nationally "
            "by U.S. News (2026) — praised for rigorous fundamentals, research, and recruiting; "
            "common cautions are a demanding workload and challenging core courses."
        ),
        "themes": [
            {"label": "No. 2 chemical nationally", "sentiment": "positive", "detail": "Among the top chemical engineering programs (U.S. News 2026)."},
            {"label": "Strong fundamentals", "sentiment": "positive", "detail": "Rigorous training in reaction engineering and process design."},
            {"label": "Research & recruiting", "sentiment": "positive", "detail": "Strong research opportunities and employer demand."},
            _CAUTION_RIGOR,
        ],
        "sources": [_SRC_USNEWS_UG_ENG, {"label": "Georgia Tech ChBE", "url": "https://chbe.gatech.edu/"}],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-civil-engineering-bs": {
        "summary": (
            "Georgia Tech's BS in Civil Engineering is ranked No. 2 nationally by U.S. News "
            "(2026) — praised for its structures, environmental, and transportation strengths "
            "and design experience; common cautions are heavy coursework and a competitive "
            "environment."
        ),
        "themes": [
            {"label": "No. 2 civil nationally", "sentiment": "positive", "detail": "Among the top civil engineering programs (U.S. News 2026)."},
            {"label": "Broad specializations", "sentiment": "positive", "detail": "Strengths in structures, environmental, and transportation."},
            {"label": "Design experience", "sentiment": "positive", "detail": "Hands-on design and laboratory work."},
            _CAUTION_RIGOR,
        ],
        "sources": [_SRC_USNEWS_UG_ENG, {"label": "Georgia Tech School of Civil & Environmental Engineering", "url": "https://ce.gatech.edu/"}],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-business-administration-management-and-operations-bs": {
        "summary": (
            "Scheller's BS in Business Administration is rated highly for blending business with "
            "Georgia Tech's technology strength — students praise analytics, IT-management, and "
            "operations concentrations and strong recruiting in Atlanta; common cautions are a "
            "quantitatively rigorous core and a smaller business-school community within a "
            "STEM-dominated campus."
        ),
        "themes": [
            {"label": "Tech-infused business", "sentiment": "positive", "detail": "A business degree grounded in analytics and technology."},
            {"label": "Concentrations", "sentiment": "positive", "detail": "Tracks in IT management, analytics, operations, finance, and more."},
            {"label": "Atlanta recruiting", "sentiment": "positive", "detail": "Strong corporate recruiting in a major business hub."},
            {"label": "Quant-heavy core", "sentiment": "caution", "detail": "A more quantitative core than many business programs."},
        ],
        "sources": [
            {"label": "Georgia Tech Scheller College of Business — Undergraduate", "url": "https://www.scheller.gatech.edu/degrees/undergraduate/index.html"},
            _SRC_NICHE,
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-business-administration-management-and-operations-ms": {
        "summary": (
            "Scheller's Full-time MBA is well-regarded for technology, analytics, and "
            "operations strengths and a strong ROI; its part-time MBA is ranked No. 9 nationally "
            "by U.S. News (2026), and recent graduates placed at employers including Amazon, "
            "Bain & Company, Honeywell, PwC, and UPS. Common cautions are a smaller cohort than "
            "the largest national MBAs and a quantitatively rigorous, tech-focused curriculum."
        ),
        "themes": [
            {"label": "Top-10 part-time MBA", "sentiment": "positive", "detail": "Scheller's part-time MBA is ranked No. 9 nationally (U.S. News 2026)."},
            {"label": "Tech & analytics focus", "sentiment": "positive", "detail": "Distinctive strength at the business–technology intersection."},
            {"label": "Strong placement", "sentiment": "positive", "detail": "Graduates placed at Amazon, Bain, Honeywell, PwC, UPS, and more."},
            {"label": "Smaller cohort", "sentiment": "caution", "detail": "A smaller program than the largest national MBAs."},
        ],
        "sources": [
            {"label": "Georgia Tech — Scheller MBA in 2026 U.S. News rankings", "url": "https://news.gatech.edu/news/2026/04/07/georgia-tech-graduate-programs-stand-among-nations-best-2026-rankings"},
            {"label": "Scheller — MBA Class of 2024 Career Outcomes", "url": "https://www.scheller.gatech.edu/news/2024/mba-class-of-2024-career-outcomes-point-to-vital-partnerships-and-practiced-resilience.html"},
        ],
        "disclaimer": _DISCLAIMER,
    },
}

_COVERABLE_REVIEWS = frozenset(_REVIEWS_BY_SLUG.keys())

# Real Georgia Tech campus photo (campus view) — Wikimedia Commons, CC BY-SA 4.0,
# landscape JPG. Leads the institution hero (also in school_outcomes.campus_photos[0]).
_CAMPUS_PHOTO = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6c/GT_Campus.jpg/"
    "1920px-GT_Campus.jpg"
)


def _program_standard(spec: dict) -> dict:
    """Per-program omitted-field list (verified-unavailable), for _standard."""
    slug = spec["slug"]
    omitted: list[str] = [
        # Georgia Tech publishes full-time job-acceptance rates by degree level and the
        # College Scorecard publishes per-CIP earnings, but not a per-program employment
        # rate or industry breakdown — those are omitted per program.
        "outcomes_data.employment_rate",
        "outcomes_data.top_industries",
        # No durable per-program lead-faculty contact is published; see the department
        # faculty directory.
        "faculty_contacts.lead",
    ]
    if slug not in _TRACKS_BY_SLUG:
        omitted.append("tracks")
    if slug not in _CLASS_PROFILE_BY_SLUG:
        omitted.append("class_profile.cohort_size")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    return _standard(omitted)


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich Georgia Tech to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Georgia Tech is absent — safe on fresh/CI databases.
    """
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    for _path in _OMITTED_INSTITUTION:
        if _path.startswith("school_outcomes."):
            rest = _path.split(".", 1)[1]
            if "." not in rest:
                school_outcomes.pop(rest, None)
            else:
                head, leaf = rest.split(".", 1)
                if isinstance(school_outcomes.get(head), dict):
                    school_outcomes[head].pop(leaf, None)
    school_outcomes["_standard"] = _standard(_OMITTED_INSTITUTION)
    inst.school_outcomes = school_outcomes
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    inst.founded_year = 1885
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.gatech.edu"
    # Lead the gallery with a real campus photo (dedupe + prepend; idempotent).
    _gallery = [u for u in (inst.media_gallery or []) if u != _CAMPUS_PHOTO]
    inst.media_gallery = [_CAMPUS_PHOTO, *_gallery]
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
        about = _ABOUT_DETAIL.get(spec["name"])
        if about is not None:
            about = dict(about)
            about["_standard"] = _standard(_ABOUT_OMITTED.get(spec["name"], []))
            sc.about_detail = about
        sc.content_sources = _school_content(spec["name"])
        by_name[spec["name"]] = sc
    # Drop legacy units — programs.school_id is ON DELETE SET NULL, so this is FK-safe.
    for name, sc in existing.items():
        if name not in canonical_names:
            session.delete(sc)
    session.flush()
    return by_name


def _program_has_dependents(session: Session, program_id) -> bool:
    """True if any FK in the schema references this programs row (delete unsafe)."""
    fks = session.execute(
        text("""
        SELECT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON tc.constraint_name = ccu.constraint_name
         AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND ccu.table_name = 'programs'
          AND ccu.column_name = 'id'
          AND tc.table_name <> 'programs'
        """)
    ).fetchall()
    for table, col in fks:
        hit = session.execute(
            text(f'SELECT 1 FROM "{table}" WHERE "{col}" = :pid LIMIT 1'),
            {"pid": program_id},
        ).first()
        if hit:
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
        p.program_name = _FULL_NAME_BY_SLUG.get(slug) or spec["program_name"]
        p.degree_type = spec["degree_type"]
        p.duration_months = spec.get("duration_months")
        p.description_text = spec["description"]
        p.website_url = _WEBSITE_BY_SLUG.get(slug) or _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "in_person")
        p.content_sources = _program_content(spec)
        # Cost: online overrides, else undergraduate/graduate published rates.
        cost = _cost_for(spec)
        p.tuition = cost.get("tuition_usd")
        p.cost_data = cost
        # Admissions: online / undergraduate / graduate set by delivery + degree type.
        p.application_requirements = _requirements_for(spec)
        # Outcomes precedence: Scorecard FOS (program) → institution median.
        fos = _FOS_OUTCOMES.get(slug)
        if fos is not None:
            salary, cip = fos
            outcomes = {
                "median_salary": salary,
                "scope": "program",
                "cip": cip,
                "earnings_timeframe": "median earnings 1 year after completion",
                "conditions": _FOS_CONDITIONS,
                "source": "U.S. Dept. of Education College Scorecard — Field of Study",
                "source_url": "https://collegescorecard.ed.gov/school/?139755",
            }
        else:
            outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(spec)
        p.outcomes_data = outcomes
        p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_BASELINE
        p.highlights = _HL_BY_SLUG.get(slug) or _HL_BASELINE
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        if spec["degree_type"] == "bachelors" and spec.get("delivery_format") != "online":
            p.application_deadline = date(2027, 1, 1)
        else:
            p.application_deadline = None
    session.flush()
    # Reconcile legacy Georgia Tech programs (slug not in the canonical set): delete when
    # unreferenced, otherwise unpublish so the catalog stays clean without breaking any
    # application/match rows that point at them.
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
