"""Canonical MIT institution profile — the single source of truth.

Real, sourced data only (U.S. Dept. of Education College Scorecard · MIT Facts ·
QS · Times Higher Education · U.S. News). ``apply(session)`` idempotently
enriches the MIT institution row, upserts the six real academic units, and
builds MIT's program catalog.

It **flushes but does not commit** — the caller (the Alembic data migration, the
CLI script, or the dev seed) owns the transaction. It is a **no-op** (returns
``False``) when MIT is absent, so it is safe to run against a fresh or CI
database. Re-running is safe: schools key off ``(institution_id, name)`` and
programs off ``slug``; stale rows are reconciled without breaking foreign keys.

This module is the home of MIT's data so the migration, the standalone script,
and the dev seed all agree (DRY).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION, check_conformance

INSTITUTION_NAME = "Massachusetts Institute of Technology"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-10"


def _standard(omitted: list[str] | None = None) -> dict:
    """Conformance stamp for a node: standard version + honest omitted list."""
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }

# ── Institution-level data ────────────────────────────────────────────────
# Rankings are stored as {rank, year} objects because the page renders every
# ranking_data entry that is an object with a numeric `rank` (and labels it via
# the frontend `rankingLabel` map, which already knows these keys).
RANKING_DATA: dict = {
    "ownership_type": "private_nonprofit",
    "accreditor": "NECHE",
    "carnegie_classification": "Doctoral Universities: Very High Research Activity",
    # QS World 2025-26 (MIT News 2025-06-18)
    "qs_world_university_rankings": {"rank": 1, "year": 2025},
    # THE WUR 2025 (MIT News 2025-03-03)
    "times_higher_education": {"rank": 2, "year": 2025},
    # US News 2025-26 (MIT News 2025-09-23)
    "us_news_national": {"rank": 2, "year": 2025},
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object
# below is complete, so a shallow merge is correct. Sources back the figures.
SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.0456,
    "avg_net_price": 20111,
    "median_earnings_10yr": 143372,
    "completion_rate_4yr_150pct": 0.9641,
    "retention_rate_first_year": 0.9908,
    "test_scores": {
        "sat_reading_25_75": [740, 780],
        "sat_math_25_75": [780, 800],
        "act_25_75": [34, 36],
    },
    "financial_aid": {
        "pell_grant_rate": 0.1932,
        "federal_loan_rate": 0.0669,
        "median_debt_completers": 14768,
        "cost_of_attendance": 89340,
        "tuition_free_rate": 0.39,
        "scholarship_rate": 0.57,
        "no_loan_debt_rate": 0.88,
        "median_scholarship": 69777,
    },
    "demographics": {
        "white": 0.2126,
        "black": 0.077,
        "hispanic": 0.1409,
        "asian": 0.3517,
        "women": 0.4816,
    },
    "location": {"lat": 42.3597, "lng": -71.0919},
    "employed_or_continuing_ed": 0.94,
    "graduation_rate_6yr": 0.96,
    "top_employer_industries": ["Technology", "Finance", "Consulting", "Research"],
    "scale": {
        "faculty_count": 1466,
        "student_faculty_ratio": "3:1",
        "research_centers": 70,
        "endowment_usd": 24600000000,
        "campus_acres": 168,
        "residence_halls": 20,
        "undergrad_majors": 56,
        "undergrad_minors": 62,
    },
    "research": {
        "labs": [
            "CSAIL",
            "MIT Media Lab",
            "Lincoln Laboratory",
            "Broad Institute",
            "Koch Institute",
            "McGovern Institute",
            "Whitehead Institute",
            "Plasma Science & Fusion Center",
        ],
        "areas": [
            "AI & computing",
            "Climate & energy",
            "Health & life sciences",
            "Robotics & manufacturing",
            "Neuroscience",
            "Fusion energy",
        ],
        "industry_collaborators": 700,
        # Official lab/institute homepages (links on the Campus resources card).
        "lab_links": {
            "CSAIL": "https://www.csail.mit.edu/",
            "MIT Media Lab": "https://www.media.mit.edu/",
            "Lincoln Laboratory": "https://www.ll.mit.edu/",
            "Broad Institute": "https://www.broadinstitute.org/",
            "Koch Institute": "https://ki.mit.edu/",
            "McGovern Institute": "https://mcgovern.mit.edu/",
            "Whitehead Institute": "https://wi.mit.edu/",
            "Plasma Science & Fusion Center": "https://www.psfc.mit.edu/",
        },
    },
    "campus_life": {
        "varsity_sports": 33,
        "athletics_division": "NCAA Division III",
        "arts_groups": 60,
        "residence_halls": 20,
        "student_orgs": "500+",
        "greek_life": "~25% of undergrads",
        "housing": "Guaranteed 4 years",
        # Official student-resource hubs (links on the Campus resources card).
        "resources": [
            {"label": "Athletics", "url": "https://mitathletics.com/"},
            {"label": "Arts at MIT", "url": "https://arts.mit.edu/"},
            {"label": "Housing", "url": "https://studentlife.mit.edu/housing"},
            {"label": "Student life", "url": "https://studentlife.mit.edu/"},
        ],
    },
    "campus_basics": {
        "location": "Cambridge, Massachusetts",
        "academic_calendar": "4-1-4 — fall, January IAP, spring",
    },
    "flagship": {
        "nobel_laureates": 106,
        "macarthur_fellows": 85,
        "national_medal_science": 64,
        "national_medal_tech": 35,
        "enrollment_total": 11816,
        "admissions_cycle": "Class of 2029",
        "applicants": 29281,
        "admits": 1334,
    },
    "sources": [
        {
            "label": "Costs, outcomes, test scores, demographics",
            "source": "U.S. Dept. of Education College Scorecard",
            "year": 2024,
            "url": "https://collegescorecard.ed.gov/school/?166683-Massachusetts-Institute-of-Technology",
        },
        {
            "label": "World ranking",
            "source": "QS World University Rankings",
            "year": 2025,
            "url": "https://www.topuniversities.com/universities/massachusetts-institute-technology-mit",
        },
        {
            "label": "World ranking",
            "source": "Times Higher Education",
            "year": 2025,
            "url": "https://www.timeshighereducation.com/world-university-rankings/massachusetts-institute-technology",
        },
        {
            "label": "National ranking",
            "source": "U.S. News Best National Universities",
            "year": 2025,
            "url": "https://www.usnews.com/best-colleges/massachusetts-institute-of-technology-2178",
        },
        {
            "label": "Schools, scale, distinction, enrollment, aid",
            "source": "MIT Facts",
            "year": 2025,
            "url": "https://facts.mit.edu/",
        },
        {
            "label": "Endowment & financials",
            "source": "MIT News — FY2024 financials",
            "year": 2024,
            "url": "https://news.mit.edu/2024/mit-releases-financials-and-endowment-figures-1011",
        },
        {
            "label": "Research labs & athletics",
            "source": "MIT Research & MIT Athletics",
            "year": 2025,
            "url": "https://www.mit.edu/research/",
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it
# "Undergraduates"); the total (11,816) lives in flagship.enrollment_total
# and renders as "Total enrollment".
UNDERGRAD_COUNT = 4561

DESCRIPTION = (
    "Founded in 1861 in Cambridge, Massachusetts, the Massachusetts Institute "
    "of Technology is a private research university whose motto — Mens et Manus "
    '("mind and hand") — captures its founding commitment to advancing '
    "knowledge in the service of real-world problems. Its campus stretches more "
    "than a mile along the north bank of the Charles River, across from "
    "downtown Boston.\n\n"
    "MIT is organized into five schools and one college: Engineering; Science; "
    "Humanities, Arts, and Social Sciences; the MIT Sloan School of Management; "
    "Architecture and Planning; and the Stephen A. Schwarzman College of "
    "Computing, opened in 2019 to weave computing and artificial intelligence "
    "through every discipline. Roughly 4,500 undergraduates and 7,000 graduate "
    "students study across these units, supported by one of the largest "
    "research enterprises of any U.S. university.\n\n"
    "The Institute ranks among the very best universities in the world — No. 1 "
    "globally by QS, and No. 2 in both the Times Higher Education world ranking "
    "and the U.S. News national-universities list. Its faculty and alumni "
    "include more than 100 Nobel laureates alongside dozens of MacArthur Fellows "
    "and Turing Award winners.\n\n"
    "MIT is also distinctively entrepreneurial: generations of alumni have "
    "founded companies across semiconductors, biotechnology, robotics, "
    "aerospace, and the modern internet. A rigorous education in science, "
    "engineering, and management — paired with need-based aid that holds the "
    "average net price near $20,000 a year — produces graduates with a median "
    "income of roughly $143,000 a decade after entry."
)

# ── The six real academic units (in display order) ────────────────────────
SCHOOLS: list[dict] = [
    {
        "name": "School of Engineering",
        "sort_order": 1,
        "description": (
            "MIT's largest school — home to roughly half of all undergraduates — "
            "tackling climate and energy, health and life sciences, AI, and "
            "advanced manufacturing across eight departments plus the Institute "
            "for Data, Systems & Society (IDSS) and the Institute for Medical "
            "Engineering & Science (IMES)."
        ),
    },
    {
        "name": "School of Science",
        "sort_order": 2,
        "description": (
            "Turns curiosity into discovery across physics, mathematics, biology, "
            "chemistry, brain & cognitive sciences, and earth, atmospheric & "
            "planetary sciences — the home of work like LIGO's gravitational-wave "
            "detection and decades of Nobel-winning research."
        ),
    },
    {
        "name": "School of Humanities, Arts, and Social Sciences",
        "sort_order": 3,
        "description": (
            "Grounds every MIT education in the humanities and social sciences — "
            "economics, linguistics & philosophy, political science, history, "
            "literature, music & theater arts, and more — developing the values, "
            "vision, and ethical compass of tomorrow's leaders."
        ),
    },
    {
        "name": "MIT Sloan School of Management",
        "sort_order": 4,
        "description": (
            "One of the world's leading business schools. Established in 1914 as "
            "MIT's Course 15 and renamed in 1964 for Alfred P. Sloan Jr. — the "
            "MIT-trained engineer who led General Motors — Sloan develops "
            "principled, innovative leaders and advances management practice at the "
            "intersection of management and technology, in the spirit of MIT's motto "
            'Mens et Manus ("mind and hand"). Its evidence-based, data-driven '
            "research spans finance, operations, the digital economy, and "
            "entrepreneurship. Roughly 1,300 students learn from about 116 faculty "
            "across the MBA, Master of Finance, Master of Business Analytics, the "
            "Sloan Fellows MBA, Executive MBA, a research PhD, and executive education."
        ),
    },
    {
        "name": "School of Architecture and Planning",
        "sort_order": 5,
        "description": (
            "Integrates design, planning, and technology across the Department of "
            "Architecture (the oldest in the U.S., founded 1865), Urban Studies & "
            "Planning, the MIT Media Lab (Media Arts & Sciences), the Center for "
            "Real Estate, and the Morningside Academy for Design."
        ),
    },
    {
        "name": "MIT Stephen A. Schwarzman College of Computing",
        "sort_order": 6,
        "description": (
            "Opened in 2019 to advance computer science and AI and weave "
            "computing through every MIT discipline — home to the Common Ground "
            "for Computing Education and the Social and Ethical Responsibilities "
            "of Computing (SERC) initiative."
        ),
    },
]

# Each school's own official website (verified to resolve at author time).
_SCHOOL_WEBSITE: dict[str, str] = {
    "School of Engineering": "https://engineering.mit.edu/",
    "School of Science": "https://science.mit.edu/",
    "School of Humanities, Arts, and Social Sciences": "https://shass.mit.edu/",
    "MIT Sloan School of Management": "https://mitsloan.mit.edu/",
    "School of Architecture and Planning": "https://sap.mit.edu/",
    "MIT Stephen A. Schwarzman College of Computing": "https://computing.mit.edu/",
}

# ── Channel feeds + official social links for keyword-relevant Events/Updates ──
# All URLs live-verified 2026-06-09 and adversarially confirmed official (see
# docs/superpowers/specs/2026-06-09-school-program-events-updates-design.md §3).
#   - Sloan news topic feed is MIT's own Sloan tagging → curated (gate bypassed).
#   - MBAn uses MIT's operations-research topic feed (its home discipline) +
#     keyword gate; events come from the MIT calendar keyword search + gate.
#   - Sloan's 5 social handles are the official mitsloan.mit.edu footer links;
#     MBAn inherits Sloan's links + the ORC's X (no unverified @mit.analytics).
_SLOAN_CONTENT: dict = {
    "news_rss": "https://news.mit.edu/rss/topic/sloan-school-management",
    "news_curated": True,
    "events_feed": {
        "url": "https://calendar.mit.edu/search/events.ics?search=sloan",
        "type": "ical",
    },
    "keywords": ["sloan", "mit sloan"],
    "social": {
        "instagram": "https://www.instagram.com/mitsloan/",
        "linkedin": "https://www.linkedin.com/company/mit-sloan-school-of-management",
        "x": "https://twitter.com/mitsloan",
        "youtube": "https://www.youtube.com/user/MITSloan",
        "facebook": "https://www.facebook.com/MITSloan",
    },
}
# Rich About-tab content for the Sloan school. All facts verified against
# en.wikipedia.org/wiki/MIT_Sloan_School_of_Management and the official faculty
# directory at mitsloan.mit.edu/faculty/directory (2026-06-09). Faculty titles
# are quoted from each professor's official directory page.
_SLOAN_ABOUT_DETAIL: dict = {
    "founded": 1914,
    "named_for": (
        "Alfred P. Sloan Jr. — an 1895 MIT graduate and longtime CEO of General "
        "Motors; the school was renamed in his honor in 1964."
    ),
    "leadership": "Richard M. Locke, Dean",
    "scale": {"faculty": 116, "students": 1300},
    "faculty": [
        {
            "name": "Dimitris Bertsimas",
            "title": "Associate Dean, Online Education & Artificial Intelligence",
            "focus": "Optimization & analytics; faculty lead of the Master of Business Analytics",
        },
        {
            "name": "Andrew W. Lo",
            "title": "Charles E. and Susan T. Harris Professor",
            "focus": "Finance — adaptive markets and financial engineering",
        },
        {
            "name": "Sinan Aral",
            "title": "David Austin Professor of Management",
            "focus": "The digital economy, social networks, and AI",
        },
        {
            "name": "Simon Johnson",
            "title": "Ronald A. Kurtz (1954) Professor of Entrepreneurship",
            "focus": "Economics & entrepreneurship — 2024 Nobel laureate",
        },
        {
            "name": "Antoinette Schoar",
            "title": "Stewart C. Myers-Horn Family Professor of Finance",
            "focus": "Entrepreneurial and household finance",
        },
    ],
    "research_centers": [
        "MIT Initiative on the Digital Economy",
        "MIT Center for Collective Intelligence",
        "MIT Laboratory for Financial Engineering",
        "Operations Research Center",
    ],
    "source": {"label": "MIT Sloan", "url": "https://mitsloan.mit.edu/about-mit-sloan"},
}
_MBAN_CONTENT: dict = {
    "news_rss": "https://news.mit.edu/rss/topic/operations-research",
    "news_curated": False,
    "events_feed": {
        "url": "https://calendar.mit.edu/search/events.ics?search=business+analytics",
        "type": "ical",
    },
    "keywords": [
        "mban",
        "business analytics",
        "master of business analytics",
        "operations research",
    ],
    "social": {
        "instagram": "https://www.instagram.com/mitsloan/",
        "linkedin": "https://www.linkedin.com/company/mit-sloan-school-of-management",
        "x": "https://x.com/orcenter",
        "youtube": "https://www.youtube.com/user/MITSloan",
        "facebook": "https://www.facebook.com/MITSloan",
    },
}

# ── The program catalog (real degree programs, organized by school) ────────
# slug = idempotency key. degree_type ∈ {bachelors, masters, phd}. tuition /
# acceptance_rate are left null: the institution net price and admit rate are
# the sourced truth, and per-program figures aren't reliably published. PhD
# descriptions note that funding is provided.
_ENG = "School of Engineering"
_SCI = "School of Science"
_SHASS = "School of Humanities, Arts, and Social Sciences"
_SLOAN = "MIT Sloan School of Management"
_SAP = "School of Architecture and Planning"
_COMPUTING = "MIT Stephen A. Schwarzman College of Computing"

# ── Per-school About tabs + feeds ──────────────────────────────────────────
# Sloan was the standard-setter; the remaining five schools' about_detail and
# content_sources are merged below (live-verified against each school's
# official site; see each block's source).
_ABOUT_BY_SCHOOL: dict[str, dict] = {
    _SLOAN: _SLOAN_ABOUT_DETAIL,
}
_CONTENT_BY_SCHOOL: dict[str, dict] = {
    _SLOAN: _SLOAN_CONTENT,
}

PROGRAMS: list[dict] = [
    # School of Engineering
    {
        "slug": "mit-eecs-bs",
        "school": _ENG,
        "program_name": "Electrical Engineering & Computer Science",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 6 — MIT's largest major: circuits, systems, AI, and theory.",
    },
    {
        "slug": "mit-eecs-phd",
        "school": _ENG,
        "program_name": "Electrical Engineering & Computer Science",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research in AI, systems, and theory. Fully funded.",
    },
    {
        "slug": "mit-meche-bs",
        "school": _ENG,
        "program_name": "Mechanical Engineering",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 2 — design, mechanics, controls, robotics, and energy.",
    },
    {
        "slug": "mit-meche-phd",
        "school": _ENG,
        "program_name": "Mechanical Engineering",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research in mechanics, design, and energy. Fully funded.",
    },
    {
        "slug": "mit-aeroastro-bs",
        "school": _ENG,
        "program_name": "Aeronautics & Astronautics",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 16 — aerospace vehicles, autonomy, and space systems.",
    },
    {
        "slug": "mit-cheme-bs",
        "school": _ENG,
        "program_name": "Chemical Engineering",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 10 — chemical and biological process engineering.",
    },
    {
        "slug": "mit-dmse-bs",
        "school": _ENG,
        "program_name": "Materials Science & Engineering",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 3 — structure, properties, and processing of materials.",
    },
    {
        "slug": "mit-be-bs",
        "school": _ENG,
        "program_name": "Biological Engineering",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 20 — engineering at the interface of biology.",
    },
    {
        "slug": "mit-cee-bs",
        "school": _ENG,
        "program_name": "Civil & Environmental Engineering",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 1 — infrastructure and sustainable environmental systems.",
    },
    {
        "slug": "mit-nse-bs",
        "school": _ENG,
        "program_name": "Nuclear Science & Engineering",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 22 — fission, fusion, and radiation science.",
    },
    # School of Science
    {
        "slug": "mit-physics-bs",
        "school": _SCI,
        "program_name": "Physics",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 8 — from quantum information to astrophysics.",
    },
    {
        "slug": "mit-physics-phd",
        "school": _SCI,
        "program_name": "Physics",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research in theoretical and experimental physics. Funded.",
    },
    {
        "slug": "mit-math-bs",
        "school": _SCI,
        "program_name": "Mathematics",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 18 — pure and applied mathematics and statistics.",
    },
    {
        "slug": "mit-math-phd",
        "school": _SCI,
        "program_name": "Mathematics",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research in pure and applied mathematics. Funded.",
    },
    {
        "slug": "mit-biology-bs",
        "school": _SCI,
        "program_name": "Biology",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 7 — molecular, cellular, and computational biology.",
    },
    {
        "slug": "mit-chemistry-bs",
        "school": _SCI,
        "program_name": "Chemistry",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 5 — organic, inorganic, physical, and biological chemistry.",
    },
    {
        "slug": "mit-bcs-bs",
        "school": _SCI,
        "program_name": "Brain & Cognitive Sciences",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 9 — from neurons to cognition and machine intelligence.",
    },
    {
        "slug": "mit-eaps-bs",
        "school": _SCI,
        "program_name": "Earth, Atmospheric & Planetary Sciences",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 12 — Earth, climate, oceans, and the planets.",
    },
    # School of Humanities, Arts, and Social Sciences
    {
        "slug": "mit-economics-bs",
        "school": _SHASS,
        "program_name": "Economics",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 14 — a top-ranked, empirically rigorous economics program.",
    },
    {
        "slug": "mit-economics-phd",
        "school": _SHASS,
        "program_name": "Economics",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "A leading economics doctoral program. Fully funded.",
    },
    {
        "slug": "mit-linguistics-philosophy-bs",
        "school": _SHASS,
        "program_name": "Linguistics & Philosophy",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 24 — the study of language and mind.",
    },
    {
        "slug": "mit-political-science-bs",
        "school": _SHASS,
        "program_name": "Political Science",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 17 — security, political economy, and methods.",
    },
    {
        "slug": "mit-cms-writing-bs",
        "school": _SHASS,
        "program_name": "Comparative Media Studies / Writing",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 21 — media, communication, and writing.",
    },
    # MIT Sloan School of Management
    {
        "slug": "mit-management-bs",
        "school": _SLOAN,
        "program_name": "Management",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 15 — analytics, finance, operations, entrepreneurship.",
    },
    {
        "slug": "mit-sloan-mba",
        "school": _SLOAN,
        "program_name": "MBA",
        "degree_type": "masters",
        "duration_months": 24,
        "description": "MIT Sloan's flagship MBA: analytical rigor plus action learning.",
    },
    {
        "slug": "mit-sloan-mfin",
        "school": _SLOAN,
        "program_name": "Master of Finance",
        "degree_type": "masters",
        "duration_months": 18,
        "description": "A rigorous, quantitative master's for careers in finance.",
    },
    {
        "slug": "mit-sloan-mban",
        "school": _SLOAN,
        "program_name": "Master of Business Analytics",
        "degree_type": "masters",
        "duration_months": 12,
        "description": "A one-year master's in business analytics and data science.",
    },
    {
        "slug": "mit-sloan-phd",
        "school": _SLOAN,
        "program_name": "Management",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research across management. Fully funded.",
    },
    # School of Architecture and Planning
    {
        "slug": "mit-architecture-bs",
        "school": _SAP,
        "program_name": "Architecture",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 4 — design, history, and building technology.",
    },
    {
        "slug": "mit-architecture-march",
        "school": _SAP,
        "program_name": "Master of Architecture",
        "degree_type": "masters",
        "duration_months": 42,
        "description": "The accredited professional degree in architecture (M.Arch).",
    },
    {
        "slug": "mit-dusp-bs",
        "school": _SAP,
        "program_name": "Urban Studies & Planning",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 11 — cities, housing, transport, and planning policy.",
    },
    {
        "slug": "mit-mediaarts-sm",
        "school": _SAP,
        "program_name": "Media Arts & Sciences",
        "degree_type": "masters",
        "duration_months": 24,
        "description": "The graduate program of the MIT Media Lab.",
    },
    # MIT Stephen A. Schwarzman College of Computing
    {
        "slug": "mit-cs-6-3-bs",
        "school": _COMPUTING,
        "program_name": "Computer Science & Engineering",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 6-3 — the computer-science track of MIT's Course 6.",
    },
    {
        "slug": "mit-ai-6-4-bs",
        "school": _COMPUTING,
        "program_name": "Artificial Intelligence & Decision Making",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Course 6-4 — machine learning and the foundations of AI.",
    },
    {
        "slug": "mit-cse-phd",
        "school": _COMPUTING,
        "program_name": "Computational Science & Engineering",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research in computational science & engineering. Funded.",
    },
    # ── More degrees from the full degree-charts crawl ────────────────────────
    {
        "slug": "mit-aeroastro-phd",
        "school": _ENG,
        "program_name": "Aeronautics & Astronautics",
        "degree_type": "phd",
        "duration_months": 60,
        "delivery_format": "in_person",
        "description": "Course 16 — doctoral research in aerospace and space systems. Funded.",
    },
    {
        "slug": "mit-statistics-phd",
        "school": _ENG,
        "program_name": "Statistics",
        "degree_type": "phd",
        "duration_months": 60,
        "delivery_format": "in_person",
        "description": "Doctoral program in statistics, run through IDSS. Funded.",
    },
    {
        "slug": "mit-tpp-sm",
        "school": _ENG,
        "program_name": "Technology & Policy",
        "degree_type": "masters",
        "duration_months": 24,
        "delivery_format": "in_person",
        "description": "SM at the intersection of engineering, policy, and society (IDSS).",
    },
    {
        "slug": "mit-chemistry-phd",
        "school": _SCI,
        "program_name": "Chemistry",
        "degree_type": "phd",
        "duration_months": 60,
        "delivery_format": "in_person",
        "description": "Course 5 — doctoral research across the chemical sciences. Funded.",
    },
    {
        "slug": "mit-math-cs-bs",
        "school": _SCI,
        "program_name": "Mathematics with Computer Science",
        "degree_type": "bachelors",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": "Course 18-C — mathematics with a computer-science emphasis.",
    },
    {
        "slug": "mit-anthropology-bs",
        "school": _SHASS,
        "program_name": "Anthropology",
        "degree_type": "bachelors",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": "Course 21A — the study of human societies and cultures.",
    },
    {
        "slug": "mit-history-bs",
        "school": _SHASS,
        "program_name": "History",
        "degree_type": "bachelors",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": "Course 21H — history across periods, regions, and themes.",
    },
    {
        "slug": "mit-literature-bs",
        "school": _SHASS,
        "program_name": "Literature",
        "degree_type": "bachelors",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": "Course 21L — literary study across languages and media.",
    },
    {
        "slug": "mit-music-bs",
        "school": _SHASS,
        "program_name": "Music",
        "degree_type": "bachelors",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": "Course 21M — performance, composition, and music technology.",
    },
    {
        "slug": "mit-sts-bs",
        "school": _SHASS,
        "program_name": "Science, Technology & Society",
        "degree_type": "bachelors",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": "STS — how science and technology shape, and are shaped by, society.",
    },
    {
        "slug": "mit-global-languages-bs",
        "school": _SHASS,
        "program_name": "Global Studies & Languages",
        "degree_type": "bachelors",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": "Course 21G — languages, cultures, and global studies.",
    },
    {
        "slug": "mit-science-writing-sm",
        "school": _SHASS,
        "program_name": "Science Writing",
        "degree_type": "masters",
        "duration_months": 12,
        "delivery_format": "in_person",
        "description": "The MIT Graduate Program in Science Writing (SM).",
    },
    {
        "slug": "mit-business-analytics-bs",
        "school": _SLOAN,
        "program_name": "Business Analytics",
        "degree_type": "bachelors",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": "Course 15-2 — undergraduate business analytics.",
    },
    {
        "slug": "mit-finance-bs",
        "school": _SLOAN,
        "program_name": "Finance",
        "degree_type": "bachelors",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": "Course 15-3 — undergraduate finance.",
    },
    {
        "slug": "mit-sloan-fellows-mba",
        "school": _SLOAN,
        "program_name": "Sloan Fellows MBA",
        "degree_type": "masters",
        "duration_months": 12,
        "delivery_format": "in_person",
        "description": "A one-year MBA for experienced mid-career leaders.",
    },
    {
        "slug": "mit-sdm-sm",
        "school": _SLOAN,
        "program_name": "System Design & Management",
        "degree_type": "masters",
        "duration_months": 24,
        "delivery_format": "hybrid",
        "description": "Joint Sloan/Engineering SM in systems and engineering leadership.",
    },
    {
        "slug": "mit-red-sm",
        "school": _SAP,
        "program_name": "Real Estate Development",
        "degree_type": "masters",
        "duration_months": 12,
        "delivery_format": "in_person",
        "description": "MSRED from the MIT Center for Real Estate.",
    },
    {
        "slug": "mit-city-planning-sm",
        "school": _SAP,
        "program_name": "City Planning",
        "degree_type": "masters",
        "duration_months": 24,
        "delivery_format": "in_person",
        "description": "Master in City Planning (MCP) from DUSP.",
    },
    {
        "slug": "mit-comp-cognition-bs",
        "school": _COMPUTING,
        "program_name": "Computation & Cognition",
        "degree_type": "bachelors",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": "Course 6-9 — computing and the science of intelligence.",
    },
    {
        "slug": "mit-cs-econ-data-bs",
        "school": _COMPUTING,
        "program_name": "Computer Science, Economics & Data Science",
        "degree_type": "bachelors",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": "Course 6-14 — computing, economics, and data science.",
    },
    # ── Online MicroMasters (graduate-level, non-degree credentials) ──────────
    {
        "slug": "mit-mm-supply-chain",
        "school": _ENG,
        "program_name": "Supply Chain Management (MicroMasters)",
        "degree_type": "certificate",
        "duration_months": 12,
        "delivery_format": "online",
        "description": "Online MicroMasters from the MIT Center for Transportation & Logistics.",
    },
    {
        "slug": "mit-mm-statistics-data-science",
        "school": _ENG,
        "program_name": "Statistics & Data Science (MicroMasters)",
        "degree_type": "certificate",
        "duration_months": 12,
        "delivery_format": "online",
        "description": "Online MicroMasters in statistics and data science from IDSS.",
    },
    {
        "slug": "mit-mm-data-econ-policy",
        "school": _SHASS,
        "program_name": "Data, Economics & Design of Policy (MicroMasters)",
        "degree_type": "certificate",
        "duration_months": 12,
        "delivery_format": "online",
        "description": "Online MicroMasters in applied economics and policy (Economics).",
    },
    {
        "slug": "mit-mm-manufacturing",
        "school": _ENG,
        "program_name": "Principles of Manufacturing (MicroMasters)",
        "degree_type": "certificate",
        "duration_months": 12,
        "delivery_format": "online",
        "description": "Online MicroMasters in manufacturing from Mechanical Engineering.",
    },
    {
        "slug": "mit-mm-finance",
        "school": _SLOAN,
        "program_name": "Finance (MicroMasters)",
        "degree_type": "certificate",
        "duration_months": 12,
        "delivery_format": "online",
        "description": "Online MicroMasters in finance from MIT Sloan.",
    },
    # ── MIT Professional Education certificates (non-degree, online / blended) ─
    {
        "slug": "mit-pe-ml-ai",
        "school": _COMPUTING,
        "program_name": "Machine Learning & AI (Professional Certificate)",
        "degree_type": "certificate",
        "duration_months": 12,
        "delivery_format": "online",
        "description": "Non-degree professional certificate in machine learning and AI.",
    },
    {
        "slug": "mit-pe-design-manufacturing",
        "school": _ENG,
        "program_name": "Design & Manufacturing (Professional Certificate)",
        "degree_type": "certificate",
        "duration_months": 12,
        "delivery_format": "online",
        "description": "Non-degree professional certificate in design and manufacturing.",
    },
    {
        "slug": "mit-pe-sustainability",
        "school": _ENG,
        "program_name": "Sustainability (Professional Certificate)",
        "degree_type": "certificate",
        "duration_months": 12,
        "delivery_format": "online",
        "description": "Non-degree professional certificate in sustainability and clean energy.",
    },
    {
        "slug": "mit-pe-cto",
        "school": _SLOAN,
        "program_name": "Chief Technology Officer Program",
        "degree_type": "certificate",
        "duration_months": 6,
        "delivery_format": "hybrid",
        "description": "Blended executive certificate for technology leaders.",
    },
    {
        "slug": "mit-pe-innovation-tech",
        "school": _ENG,
        "program_name": "Innovation & Technology (Professional Certificate)",
        "degree_type": "certificate",
        "duration_months": 12,
        "delivery_format": "online",
        "description": "Non-degree professional certificate in innovation and technology.",
    },
]

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

# Shared international-student building blocks (visa/I-20 is MIT-wide via the ISO).
_INTL_VISA = {
    "type": "F-1 student visa",
    "note": (
        "Admitted international students receive an I-20 from the MIT International "
        "Students Office after showing proof of funding, then use it to apply for the F-1 visa."
    ),
}
_INTL_SOURCES = [{"label": "MIT International Students Office", "url": "https://iso.mit.edu/"}]

# Application-requirement baselines by program type. Official at the degree
# level (undergrad is institute-wide; the Sloan MBA is Sloan-specific). Grad
# specifics vary by department, so the grad baseline is labelled accordingly.
_REQ_UNDERGRAD = {
    "materials": [
        {
            "name": "MIT application (apply.mitadmissions.org — not the Common App)",
            "required": True,
        },
        {"name": "Five short-answer essays", "required": True},
        {"name": "Activities & coursework list with self-reported grades", "required": True},
        {"name": "Secondary School Report + high-school transcript", "required": True},
        {"name": "February Updates & Notes Form (mid-year report)", "required": True},
        {
            "name": "Interview with an MIT Educational Counselor",
            "required": False,
            "note": (
                "Offered to most applicants where available; not held against you if unavailable"
            ),
        },
        {
            "name": "Optional maker / research / arts portfolio",
            "required": False,
            "note": "Submit work via the portfolio platform if it strengthens your application",
        },
    ],
    "test_policy": {
        "stance": "required",
        "note": "SAT or ACT required (reinstated for 2025 entry); scores may be self-reported.",
        "accepted_tests": ["SAT", "ACT"],
        "superscore_enabled": True,
        "typical_ranges": [
            {"test": "SAT", "low": 1520, "high": 1580},
            {"test": "ACT", "low": 34, "high": 36},
        ],
    },
    "recommendations": {
        "required_count": 3,
        "types": [
            "Math or science teacher evaluation",
            "Humanities, arts, or social-science teacher evaluation",
            "Secondary-school counselor report",
        ],
    },
    "deadlines": [
        {"round": "Early Action (non-binding)", "date": "November 1"},
        {"round": "Regular Action", "date": "January 1"},
    ],
    "application_fee": {
        "amount_usd": 75,
        "waiver_available": True,
        "note": "Fee waivers available for students with financial need",
    },
    "evaluation": (
        "Holistic review: academics in the context of your school, alignment with MIT's "
        "hands-on “mens et manus” culture, initiative, collaboration, and what you'd add to "
        "the community. MIT is need-blind for all applicants and meets full demonstrated need; "
        "it does not consider legacy or demonstrated interest."
    ),
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "Duolingo", "Cambridge English"],
            "required": False,
            "note": "Not required, but recommended where English is not your first language.",
        },
        "visa": _INTL_VISA,
        "sources": _INTL_SOURCES,
    },
    "source": "MIT Admissions",
    "source_url": "https://mitadmissions.org/apply/first-year/",
}
_REQ_GRAD = {
    "materials": [
        {"name": "Statement of objectives", "required": True},
        {"name": "Academic transcripts from all institutions", "required": True},
        {"name": "Curriculum vitae / résumé", "required": True},
        {
            "name": "GRE general / subject scores",
            "required": False,
            "note": "Many departments are GRE-optional or GRE-blind — check the department",
        },
        {
            "name": "English proficiency (TOEFL/IELTS) for international applicants",
            "required": False,
            "note": "TOEFL iBT 100 / IELTS 7.0 typical minimums",
        },
    ],
    "test_policy": {
        "stance": "varies",
        "note": "GRE requirement varies by department — many are optional or not accepted.",
    },
    "recommendations": {
        "required_count": 3,
        "types": ["Three letters of recommendation (academic or research)"],
    },
    "deadlines": [
        {"round": "Fall entry (most departments)", "date": "December 15"},
    ],
    "application_fee": {
        "amount_usd": 75,
        "waiver_available": True,
        "note": "Fee waivers available for eligible applicants",
    },
    "evaluation": (
        "Departments weigh research fit and potential, academic preparation, letters, and the "
        "statement of objectives. Admission is by the department/program, not a central office; "
        "PhD admits are typically offered full funding (tuition + stipend)."
    ),
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": True,
            "note": (
                "Required for applicants whose prior degree was not taught in English "
                "(TOEFL iBT 100 / IELTS 7.0 are typical minimums)."
            ),
        },
        "visa": _INTL_VISA,
        "sources": _INTL_SOURCES,
    },
    "source": "MIT Graduate Admissions",
    "source_url": "https://oge.mit.edu/admissions/",
}
_REQ_MBA = {
    "materials": [
        {"name": "Cover letter addressed to the Admissions Committee", "required": True},
        {"name": "One-minute introductory video", "required": True},
        {"name": "Résumé (one page)", "required": True},
        {"name": "Academic transcripts", "required": True},
        {
            "name": "Organizational chart of your current role",
            "required": False,
            "note": "Optional context on where you sit in your organization",
        },
    ],
    "test_policy": {
        "stance": "required",
        "note": "GMAT, GRE, or Executive Assessment — score may be self-reported to apply.",
        "accepted_tests": ["GMAT", "GRE", "Executive Assessment"],
    },
    "recommendations": {
        "required_count": 1,
        "types": ["One professional letter of recommendation (ideally from a supervisor)"],
    },
    "deadlines": [
        {"round": "Round 1", "date": "Late September"},
        {"round": "Round 2", "date": "Mid-January"},
        {"round": "Round 3", "date": "Early April"},
    ],
    "application_fee": {
        "amount_usd": 250,
        "waiver_available": True,
        "note": "Fee waivers for active military, veterans, and select fellows",
    },
    "evaluation": (
        "MIT Sloan looks for evidence of impact, analytical capability, and alignment with its "
        "mission to develop principled, innovative leaders — assessed through the cover letter, "
        "video, recommendation, and interview (by invitation)."
    ),
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": False,
            "note": "Not required to apply; English ability is assessed during the interview.",
        },
        "visa": _INTL_VISA,
        "sources": _INTL_SOURCES,
    },
    "source": "MIT Sloan Admissions",
    "source_url": "https://mitsloan.mit.edu/mba/admissions",
}
_REQ_OPEN = {
    "materials": [{"name": "Open enrollment — no formal admission required", "required": False}],
    "test_policy": {"stance": "not_required"},
    "source": "MIT Open Learning",
    "source_url": "https://openlearning.mit.edu/",
}

# Professional / executive programs (LGO, EMBA, MSMS, SCM, IDM, DEDP, Practice
# School, MEng-Manufacturing) run their OWN application rounds and rates: no
# deadline date is asserted (recorded in _standard.omitted), and applicants are
# pointed at the program's official admissions page.
_REQ_PRO = {
    "materials": [
        {"name": "Statement of purpose / essays (program-specific)", "required": True},
        {"name": "Academic transcripts from all institutions", "required": True},
        {"name": "Curriculum vitae / résumé", "required": True},
        {
            "name": "English proficiency (TOEFL/IELTS) for international applicants",
            "required": False,
            "note": "Required when the prior degree was not taught in English",
        },
    ],
    "test_policy": {
        "stance": "varies",
        "note": "Testing requirements vary by program — check the official admissions page.",
    },
    "recommendations": {
        "required_count": 2,
        "types": ["Letters of recommendation (professional or academic; count varies)"],
    },
    "evaluation": (
        "Professional and executive programs admit in their own rounds with "
        "program-specific criteria (work experience, leadership, fit) — verify "
        "deadlines and materials on the program's official admissions page."
    ),
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": True,
            "note": "Required for applicants whose prior degree was not taught in English.",
        },
        "visa": _INTL_VISA,
        "sources": _INTL_SOURCES,
    },
    "source": "MIT Graduate Admissions — program-specific rounds",
    "source_url": "https://oge.mit.edu/graduate-admissions/programs/",
}

# Outcomes are not published per program by MIT, and the College Scorecard
# Field-of-Study API is key-gated. So degree programs surface MIT's REAL
# institution-wide outcomes, explicitly scoped/labelled "not program-specific"
# (rendered with a disclaimer). Non-degree credentials get none.
_OUTCOMES_INSTITUTION = {
    "median_salary": 143372,
    "employment_rate": 0.94,
    "employment_timeframe": "MIT graduates overall",
    "top_industries": ["Technology", "Finance", "Consulting", "Research"],
    "scope": "institution",
    "scope_note": "MIT-wide figures across all graduates — not specific to this program.",
    "conditions": (
        "Institution-wide, not program-specific: College Scorecard median "
        "earnings cover federally aided former students 10 years after entry; "
        "MIT does not publish per-program outcomes for this program (the "
        "Graduating Student Survey reports institute-level results)."
    ),
    "source": "U.S. Dept. of Education College Scorecard (institution-level)",
    "source_url": "https://collegescorecard.ed.gov/",
}

# Real per-program median earnings (+ debt where reported) from the College
# Scorecard Field-of-Study file (Most-Recent-Cohorts), MIT UNITID 166683. Only
# non-privacy-suppressed fields appear here; every other program falls back to
# the institution figure. Tuple = (median_earnings, median_debt | None, CIP).
_FOS_OUTCOMES: dict[str, tuple[int, int | None, str]] = {
    "mit-aeroastro-bs": (138934, 17724, "14.02"),
    "mit-cs-6-3-bs": (220064, 11077, "11.07"),
    "mit-ai-6-4-bs": (220064, 11077, "11.07"),
    "mit-eecs-bs": (190731, 10967, "14.10"),
    "mit-meche-bs": (106765, 11507, "14.19"),
    "mit-cheme-bs": (124650, 17000, "14.07"),
    "mit-dmse-bs": (98069, None, "14.18"),
    "mit-be-bs": (106402, 13000, "14.05"),
    "mit-physics-bs": (126258, 18500, "40.08"),
    "mit-math-bs": (226193, 9751, "27.01"),
    "mit-biology-bs": (82813, None, "26.01"),
    "mit-management-bs": (142355, None, "52.01"),
    "mit-sloan-mba": (264269, 41000, "52.01"),
    "mit-architecture-march": (87746, None, "04.02"),
    "mit-city-planning-sm": (109410, 40833, "04.03"),
    "mit-sdm-sm": (194940, 44052, "14.27"),
    "mit-eecs-phd": (156904, None, "14.10"),
    "mit-meche-phd": (167643, None, "14.19"),
    "mit-chemistry-phd": (120827, None, "40.05"),
}

# Who-it's-for + highlights — real content, by degree type with per-program
# overrides for flagship programs. Fills the program page's audience +
# highlights sections (previously empty for MIT).
_WHO_BY_TYPE = {
    "bachelors": "Applicants seeking a rigorous, research-grounded undergraduate education.",
    "masters": "Students seeking advanced, specialized graduate training.",
    "phd": "Researchers pursuing an academic or research career through a funded doctorate.",
    "certificate": "Learners worldwide seeking a focused MIT credential, often online.",
}
_WHO_BY_SLUG = {
    "mit-sloan-mba": "Early-to-mid-career professionals targeting management and tech leadership.",
    "mit-sloan-mfin": "Quantitatively-minded graduates targeting careers across modern finance.",
    "mit-sloan-mban": "Graduates who want to turn data into business decisions.",
}
_HL_BY_TYPE = {
    "bachelors": [
        "Need-blind admission with need-based aid",
        "Undergraduate Research Opportunities (UROP)",
        "Hands-on, project-based curriculum",
    ],
    "masters": [
        "Direct access to MIT faculty & labs",
        "Strong industry & startup network",
    ],
    "phd": [
        "Fully funded — tuition + stipend",
        "World-leading research environment",
        "Small, mentored cohorts",
    ],
    "certificate": [
        "Learn online, on your schedule",
        "Earn an MIT credential",
        "Stackable toward an MIT degree",
    ],
}
_HL_BY_SLUG = {
    "mit-eecs-bs": [
        "MIT's largest undergraduate major (Course 6)",
        "Home of CSAIL",
        "Flexible 6-1 / 6-2 / 6-3 tracks",
        "Optional 5th-year MEng",
    ],
    "mit-cs-6-3-bs": [
        "Computer-science track of Course 6",
        "Schwarzman College of Computing",
        "Access to CSAIL",
    ],
    "mit-ai-6-4-bs": [
        "AI & decision-making focus (Course 6-4)",
        "Machine learning, optimization & theory",
        "Schwarzman College of Computing",
    ],
    "mit-meche-bs": [
        "Course 2 — robotics to energy",
        "Renowned design & manufacturing",
        "Pappalardo teaching labs",
    ],
    "mit-aeroastro-bs": [
        "Course 16 — aerospace & autonomy",
        "Space systems & flight research",
        "Ties to Lincoln Laboratory",
    ],
    "mit-physics-bs": [
        "Among the world's top physics programs",
        "Quantum information to astrophysics",
        "LIGO heritage",
    ],
    "mit-math-bs": [
        "Pure & applied math (Course 18)",
        "World-renowned in theory",
        "Highest reported median earnings of MIT majors",
    ],
    "mit-biology-bs": [
        "Course 7 — molecular to computational",
        "Koch Institute & Whitehead nearby",
        "Strong research & pre-med pathways",
    ],
    "mit-cheme-bs": [
        "Course 10 — energy to medicine",
        "Practice School industry immersion",
    ],
    "mit-sloan-mba": [
        "Action Learning labs",
        "Deep tech & entrepreneurship network",
        "Kendall Square innovation hub",
    ],
    "mit-sloan-mban": [
        "STEM-designated (24-month OPT eligible)",
        "Year-long Analytics Capstone with a sponsor company",
        "Built with the MIT Operations Research Center",
        "~$135K median starting salary",
        "98.6% had offers within 6 months",
    ],
    "mit-architecture-march": [
        "Accredited professional M.Arch",
        "Oldest U.S. architecture department",
        "Access to the MIT Media Lab",
    ],
}

# Real MIT concentrations / degree tracks, for the programs that offer them.
# Shape matches the frontend extractTracksMeta: {concentrations: [...], note}.
_TRACKS_BY_SLUG = {
    "mit-eecs-bs": {
        "concentrations": [
            "6-1 Electrical Science & Engineering",
            "6-2 Electrical Engineering & Computer Science",
            "6-3 Computer Science & Engineering",
            "6-9 Computation & Cognition",
            "6-14 Computer Science, Economics & Data Science",
        ],
        "note": "Course 6 offers flexible tracks spanning electrical engineering and CS.",
    },
    "mit-cs-6-3-bs": {
        "concentrations": ["Artificial Intelligence", "Systems", "Theory", "Graphics & HCI"],
        "note": "Course 6-3 students choose focus areas across computer science.",
    },
    "mit-meche-bs": {
        "concentrations": [
            "Course 2 (Mechanical Engineering)",
            "2-A (flexible, concentration-based)",
            "2-OE (with ocean engineering)",
        ],
    },
    "mit-math-bs": {
        "concentrations": [
            "Pure Mathematics",
            "Applied Mathematics",
            "Mathematics with Computer Science (18-C)",
        ],
    },
    "mit-physics-bs": {
        "concentrations": ["Flexible track (8-Flex)", "Focused option (8)"],
    },
    "mit-biology-bs": {
        "concentrations": ["Course 7 (Biology)", "7-A (flexible)"],
    },
    "mit-aeroastro-bs": {
        "concentrations": ["Aerospace Engineering (16)", "Engineering (16-ENG, flexible)"],
    },
    "mit-economics-bs": {
        "concentrations": ["Economics (14-1)", "Mathematical Economics (14-2)"],
    },
    "mit-sloan-mba": {
        "concentrations": [
            "Finance",
            "Entrepreneurship & Innovation",
            "Analytics",
            "Sustainability",
        ],
        "note": "Optional certificates let MBA students specialize.",
    },
    "mit-sloan-mban": {
        "note": (
            "A 12-month sequence: a quantitative fall core, then the year-long Analytics "
            "Capstone solving a live problem for a sponsor company."
        ),
        "curriculum": [
            {
                "term": "Fall",
                "courses": [
                    "Optimization Methods",
                    "Machine Learning",
                    "The Analytics Edge",
                    "Intensive Hands-on Deep Learning",
                    "Analytics Lab",
                    "From Analytics to Action",
                ],
            },
            {
                "term": "IAP (January)",
                "courses": [
                    "Analytics Capstone — matching & scoping",
                    "Communicating with Data",
                    "Ethics & Data Privacy",
                ],
            },
            {
                "term": "Spring",
                "courses": ["Analytics Capstone — company project", "Analytics electives"],
            },
            {
                "term": "Summer",
                "courses": ["Analytics Capstone — full-time, final deliverables"],
            },
        ],
    },
}

# Richer 2-sentence descriptions for the major programs (real). Programs not
# listed keep their canonical one-line description from PROGRAMS above.
_DESC_RICH_BY_SLUG = {
    "mit-eecs-bs": (
        "Course 6 is MIT's largest undergraduate major, spanning circuits and devices, "
        "computer systems, artificial intelligence, applied mathematics, and theory. Students "
        "choose among flexible tracks — 6-1 (electrical science & engineering), 6-2 (electrical "
        "engineering & computer science), and 6-3 (computer science & engineering) — and learn "
        "through project-based labs alongside world-class faculty. It is the academic home of "
        "CSAIL and the Research Laboratory of Electronics, and many students stay a fifth year "
        "to earn the MEng. Graduates are recruited across software, hardware, finance, and "
        "research, and report among the highest early-career earnings at MIT."
    ),
    "mit-cs-6-3-bs": (
        "Course 6-3 is the computer-science track of MIT's Course 6, covering algorithms, "
        "software systems, artificial intelligence, computer architecture, graphics, and "
        "human-computer interaction. Anchored by the Schwarzman College of Computing and "
        "CSAIL — the largest research laboratory at MIT — it pairs rigorous theory with "
        "hands-on systems and AI project work. Students can add an optional fifth-year MEng, "
        "and graduates report among the highest early-career earnings of any MIT major."
    ),
    "mit-ai-6-4-bs": (
        "Course 6-4 focuses on artificial intelligence and decision-making: machine "
        "learning, optimization, robotics, and the mathematics behind them. It blends EECS "
        "with the Schwarzman College of Computing's interdisciplinary approach."
    ),
    "mit-meche-bs": (
        "Course 2 covers mechanics, design, controls, and manufacturing — from robotics and "
        "energy systems to bioengineering. Flexible 2-A and ocean-engineering (2-OE) options "
        "let students tailor the degree."
    ),
    "mit-aeroastro-bs": (
        "Course 16 educates engineers of aerospace vehicles, autonomy, and space systems "
        "through hands-on flight and systems projects. It maintains close ties to labs such "
        "as Lincoln Laboratory."
    ),
    "mit-cheme-bs": (
        "Course 10 applies chemical and biological engineering to energy, materials, and "
        "medicine. Its renowned Practice School places students in real industrial settings."
    ),
    "mit-dmse-bs": (
        "Course 3 studies the structure, properties, and processing of materials — from "
        "semiconductors and metals to polymers and biomaterials — bridging science and "
        "engineering."
    ),
    "mit-be-bs": (
        "Course 20 engineers at the interface of biology, applying quantitative and molecular "
        "tools to medicine, therapeutics, and synthetic biology."
    ),
    "mit-cee-bs": (
        "Course 1 designs resilient infrastructure and environmental systems, combining "
        "mechanics, data, and sustainability to address climate and the built world."
    ),
    "mit-nse-bs": (
        "Course 22 spans fission and fusion energy, radiation science, and quantum "
        "engineering, with access to MIT's research reactor and the Plasma Science & Fusion "
        "Center."
    ),
    "mit-physics-bs": (
        "Course 8 is among the world's foremost physics programs, ranging from quantum "
        "information and particle physics to astrophysics and condensed matter. Flexible "
        "(8-Flex) and focused tracks suit research- or breadth-minded students."
    ),
    "mit-math-bs": (
        "Course 18 offers pure mathematics, applied mathematics, and mathematics with "
        "computer science (18-C), with world-leading strength in theory and combinatorics. "
        "It reports the highest median earnings of any MIT undergraduate major."
    ),
    "mit-biology-bs": (
        "Course 7 spans molecular, cellular, and computational biology, supported by "
        "neighbors like the Koch Institute and Whitehead Institute. It is a common path to "
        "research and medicine."
    ),
    "mit-chemistry-bs": (
        "Course 5 covers organic, inorganic, physical, and biological chemistry, with "
        "extensive undergraduate research across MIT's labs."
    ),
    "mit-bcs-bs": (
        "Course 9 connects molecules and neurons to cognition and machine intelligence, "
        "drawing on the McGovern and Picower Institutes for brain research."
    ),
    "mit-eaps-bs": (
        "Course 12 studies Earth, climate, the oceans, and the planets, combining field, "
        "laboratory, and computational science."
    ),
    "mit-economics-bs": (
        "Course 14 is one of the world's leading economics programs, known for empirical and "
        "theoretical rigor and a faculty that has included multiple Nobel laureates and John "
        "Bates Clark medalists. Offered as Economics (14-1) or the more math-intensive "
        "Mathematical Economics (14-2), the major builds strong foundations in micro- and "
        "macroeconomics, econometrics, and data analysis. Undergraduates work closely with "
        "faculty and labs such as J-PAL and go on to careers in finance, consulting, policy, "
        "and technology, and to top PhD programs."
    ),
    "mit-management-bs": (
        "Course 15 is MIT Sloan's undergraduate major, giving students the analytical and "
        "leadership foundation to approach management problems with an engineer's rigor. The "
        "curriculum spans economics, accounting, finance, marketing, operations, organizational "
        "behavior, and strategy, all built on MIT's quantitative core in mathematics and "
        "computation. Students can follow the general Management track (15-1) or the more "
        "technical Business Analytics (15-2) and Finance (15-3) tracks, and learn by doing "
        "through Action Learning labs that embed them in real companies. Based in Kendall "
        "Square — one of the world's densest innovation ecosystems — it launches careers in "
        "consulting, finance, technology, and entrepreneurship."
    ),
    "mit-sloan-mba": (
        "MIT Sloan's two-year MBA pairs analytical rigor with hands-on Action Learning labs "
        "and a deep technology and entrepreneurship network at the heart of Kendall Square. "
        "Optional certificates focus study in finance, analytics, entrepreneurship, or "
        "sustainability."
    ),
    "mit-sloan-mfin": (
        "A rigorous, quantitative master's preparing graduates for careers across modern "
        "finance — from asset management to fintech — backed by MIT Sloan's research depth."
    ),
    "mit-sloan-mban": (
        "The MIT Sloan Master of Business Analytics (MBAn) is a 12-month, STEM-designated "
        "program — developed with MIT's Operations Research Center — that applies modern data "
        "science, optimization, and machine learning to real business problems. It is built for "
        "aspiring data-science professionals early in their careers, such as engineers, "
        "mathematicians, physicists, and programmers. A rigorous fall core (optimization, machine "
        "learning, the Analytics Edge, deep learning) is paired with the year-long Analytics "
        "Capstone, in which students solve a live problem for a sponsor company through to a "
        "summer deliverable. Graduates move overwhelmingly into data-science roles, reporting a "
        "median base salary near $135,000 and offers for 98.6% of the class within six months."
    ),
    "mit-architecture-bs": (
        "Course 4 combines design studios, history and theory, and building technology in "
        "the oldest architecture program in the United States (founded 1865)."
    ),
    "mit-architecture-march": (
        "The accredited professional Master of Architecture — a studio-based degree with "
        "access to the MIT Media Lab and the school's design and computation faculty."
    ),
    "mit-dusp-bs": (
        "Course 11 studies cities, housing, transportation, and the policy of the built "
        "environment, blending social science with planning and design."
    ),
    "mit-mediaarts-sm": (
        "The graduate program of the MIT Media Lab, inventing across human-computer "
        "interaction, robotics, biotech, and media at the intersection of technology and "
        "design."
    ),
    "mit-mm-finance": (
        "An online MicroMasters credential in finance from MIT Sloan, covering financial "
        "markets, mathematical methods, and modeling — stackable toward a master's."
    ),
    "mit-mm-statistics-data-science": (
        "An online MicroMasters in Statistics and Data Science from MIT's IDSS, spanning "
        "probability, data analysis, and machine learning."
    ),
    "mit-mm-supply-chain": (
        "An online MicroMasters in Supply Chain Management from the MIT Center for "
        "Transportation & Logistics, a pathway to MIT's blended master's."
    ),
    "mit-mm-data-econ-policy": (
        "An online MicroMasters in Data, Economics, and Design of Policy from MIT's J-PAL "
        "and economics faculty, applying rigorous evaluation to real policy questions."
    ),
}


# ── Per-program "gold standard" overrides ─────────────────────────────────
# When a program publishes its own cost, outcomes, admissions, curriculum, and
# class profile, those program-specific (sourced) values take precedence over
# the degree-type fallbacks. Programs without an entry keep the fallbacks.
# MIT Sloan's Master of Business Analytics (MBAn) is the reference example.

# Program-specific cost (official published tuition), overriding the standard rate.
_COST_BY_SLUG: dict[str, dict] = {
    "mit-sloan-mban": {
        "tuition_usd": 93834,
        "year": "2025-26",
        "funded": False,
        "note": "≈ $71,834 after the Analytics Capstone summer tuition subsidy",
        "breakdown": [
            {"label": "Tuition (12-month program)", "amount": 93834},
            {
                "label": "Analytics Capstone summer tuition subsidy",
                "amount": -22000,
                "note": "Applied during the summer Capstone term",
            },
            {
                "label": "Living & personal expenses (estimated)",
                "amount": 50965,
                "note": "Housing, food, transport & personal — varies by lifestyle",
            },
        ],
        "total_cost_of_attendance": 122799,
        "source": "MIT Sloan — Financing Your Education",
        "source_url": (
            "https://mitsloan.mit.edu/master-of-business-analytics/admissions/"
            "tuition-and-financial-aid"
        ),
    },
}

# Program-specific outcomes from the program's own published employment report
# (scope="program"), overriding the institution-level / Field-of-Study fallback.
# Outcomes are quoted verbatim from the official MIT Sloan Career Development
# Office employment reports — never estimated. MBAn = Class of 2025 (most recent;
# the first year MIT Sloan published base-salary percentiles).
_OUTCOMES_BY_SLUG: dict[str, dict] = {
    "mit-sloan-mban": {
        "median_salary": 143000,
        "mean_salary": 139496,
        "salary_25th": 120000,
        "salary_75th": 155000,
        "median_signing_bonus": 15000,
        "employment_rate": 0.985,
        "employment_timeframe": "accepted an offer within 6 months of graduation",
        "class_size": 80,
        "knowledge_rate": 1.0,
        "scope": "program",
        "top_industries": ["Technology", "Consulting", "Finance", "CPG/Retail"],
        "top_employers": [
            "Palantir",
            "Boston Consulting Group",
            "Invisible Technologies",
            "Amazon",
            "Microsoft",
            "McKinsey & Company",
        ],
        "conditions": [
            "Class of 2025 (N = 80); employment data covers 100% of MBAn graduates.",
            "Compensation reported by 96.9% of students who accepted an offer; base "
            "salary in USD, not adjusted for purchasing power parity.",
            "Median signing bonus $15,000; 61.9% of compensation-reporting graduates received one.",
            "Reported under the Career Services & Employer Alliance (CSEA) Standards "
            "for Reporting Employment Statistics.",
        ],
        "source": "MIT Sloan Master of Business Analytics Employment Report, Class of 2025",
        "source_url": (
            "https://mitsloan.mit.edu/sites/default/files/2026-04/"
            "2025%20MBAn%20Employment%20Report.pdf"
        ),
    },
}

# Program-specific application requirements (official), overriding the degree-type
# baseline so the page never shows a wrong note (e.g. PhD funding on a master's).
_REQ_BY_SLUG: dict[str, dict] = {
    "mit-sloan-mban": {
        "materials": [
            {"name": "MIT Sloan online application", "required": True},
            {"name": "Two short essays + a one-minute video statement", "required": True},
            {"name": "Transcripts from all post-secondary institutions", "required": True},
            {"name": "Résumé", "required": True},
            {
                "name": "GRE or GMAT",
                "required": False,
                "note": "Optional — a strong quantitative score can strengthen an application",
            },
            {
                "name": "English proficiency (TOEFL/IELTS) for international applicants",
                "required": False,
            },
            {
                "name": "Programming & quantitative preparation (e.g. Python, linear algebra)",
                "required": False,
                "note": "Expected preparation, not a formal submission",
            },
        ],
        "test_policy": {
            "stance": "optional",
            "note": "GRE/GMAT optional; submit only if it strengthens your quantitative profile.",
            "accepted_tests": ["GRE", "GMAT"],
        },
        "recommendations": {
            "required_count": 2,
            "types": ["Two letters of recommendation (academic or professional)"],
        },
        "deadlines": [
            {"round": "Single annual round", "date": "Early January"},
        ],
        "evaluation": (
            "MIT Sloan looks for exceptional quantitative aptitude, programming readiness, and a "
            "clear fit with a data-science career — assessed through the essays, video, "
            "recommendations, and academic record. GRE/GMAT scores are optional."
        ),
        "international": {
            "english": {
                "tests": ["TOEFL", "IELTS", "Duolingo"],
                "required": False,
                "note": (
                    "Not required to apply — English proficiency is assessed in the "
                    "interview; waived for those educated in English."
                ),
            },
            "visa": _INTL_VISA,
            "opt": (
                "STEM-designated — eligible for up to 36 months of OPT "
                "(12 months + a 24-month STEM extension)."
            ),
            "sources": [
                {
                    "label": "MIT Sloan MBAn — How to Apply",
                    "url": "https://mitsloan.mit.edu/master-of-business-analytics/"
                    "admissions/how-to-apply",
                },
                {"label": "MIT International Students Office", "url": "https://iso.mit.edu/"},
            ],
        },
        "source": "MIT Sloan MBAn Admissions",
        "source_url": (
            "https://mitsloan.mit.edu/master-of-business-analytics/admissions/how-to-apply"
        ),
    },
}

# Program class profile (size + selectivity + composition), where published.
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    "mit-sloan-mban": {
        "cohort_size": "~130 students",
        "international_pct": 0.60,
        "countries": 22,
        "stem_pct": 0.875,
        "median_gpa": 3.92,
        "median_gre_quant": 169,
        "median_gmat": 730,
        "avg_work_experience_months": 15,
        "source": "MIT Sloan MBAn Class Profile",
        "source_url": "https://mitsloan.mit.edu/master-of-business-analytics/meet-class/class-profile",
    },
}

# Program faculty (lead + directory link), where confidently sourced. Kept light
# — a confidently-sourced lead plus a link to the official directory — rather than
# a roster that goes stale.
_FACULTY_BY_SLUG: dict[str, dict] = {
    "mit-sloan-mban": {
        "lead": [
            {
                "name": "Dimitris Bertsimas",
                "title": "Faculty Director · Boeing Professor of Operations Research",
                "url": "https://mitsloan.mit.edu/faculty/directory/dimitris-bertsimas",
            },
            {
                "name": "Georgia Perakis",
                "title": "Professor of Operations Research, Statistics & Operations Management",
            },
            {
                "name": "Negin (Nikki) Golrezaei",
                "title": "Associate Professor of Operations Management",
            },
            {
                "name": "Alexandre Jacquillat",
                "title": "Associate Professor of Operations Research & Statistics",
                "url": "https://mitsloan.mit.edu/faculty/directory/alexandre-jacquillat",
            },
            {
                "name": "Rama Ramakrishnan",
                "title": "Professor of the Practice, AI/ML",
                "url": "https://mitsloan.mit.edu/faculty/directory/rama-ramakrishnan",
            },
            {
                "name": "Daniel Freund",
                "title": "Associate Professor of Operations Management",
                "url": "https://mitsloan.mit.edu/faculty/directory/daniel-freund",
            },
            {
                "name": "Chara Podimata",
                "title": "Assistant Professor of Operations Research & Statistics",
                "url": "https://mitsloan.mit.edu/faculty/directory/chara-podimata",
            },
        ],
        "note": "Taught by MIT Sloan and MIT Operations Research Center faculty.",
        "directory_url": (
            "https://mitsloan.mit.edu/faculty/academic-groups/"
            "operations-research-statistics/faculty"
        ),
    },
}

# Aggregated, cited student-review themes from public third-party sources.
# Paraphrased (never verbatim) and always attributed — honest and copyright-safe.
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "mit-sloan-mban": {
        "summary": (
            "Students and third-party guides consistently praise the program's rigor, its "
            "tight, collaborative cohort, and the seven-month Analytics Capstone with a real "
            "company; the most common cautions are the fast pace, heavy quantitative workload, "
            "and high total cost."
        ),
        "themes": [
            {
                "label": "Rigorous & fast-paced",
                "sentiment": "mixed",
                "detail": "An intense, presentation-heavy year that rewards a genuine passion "
                "for analytics.",
            },
            {
                "label": "Strong, collaborative cohort",
                "sentiment": "positive",
                "detail": "Students describe smart, supportive classmates and a close-knit cohort.",
            },
            {
                "label": "Standout Analytics Capstone",
                "sentiment": "positive",
                "detail": "A ~7-month real-company data-science project with faculty mentorship "
                "is the highlight.",
            },
            {
                "label": "Strong career support",
                "sentiment": "positive",
                "detail": "MIT Sloan's Career Development Office is praised through the job "
                "search.",
            },
            {
                "label": "High total cost",
                "sentiment": "caution",
                "detail": "Tuition plus living expenses runs well over $130K, partly offset by "
                "the Capstone subsidy.",
            },
        ],
        "sources": [
            {
                "label": "Poets&Quants — MIT Sloan MBAn profile",
                "url": "https://poetsandquants.com/specialized-master/"
                "mit-sloan-school-management-master-business-analytics/",
            },
            {
                "label": "Poets&Quants — MBAn student profile",
                "url": "https://poetsandquants.com/2021/03/16/"
                "masters-in-business-analytics-abby-garrett-mit-sloan/",
            },
            {
                "label": "BusinessBecause — MIT MBAn review",
                "url": "https://www.businessbecause.com/news/masters-in-business-analytics/"
                "7460/mit-master-of-business-analytics",
            },
            {
                "label": "MIT Sloan 2024 MBAn Employment Report",
                "url": "https://mitsloan.mit.edu/career-development-office/employment-reports",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
}

# Full official degree names (MIT awards the SB/Bachelor of Science, the SM/
# Master of Science or named professional master's, and the PhD). Shown as the
# program-page title in place of the short PROGRAMS display label.
_FULL_NAME_BY_SLUG: dict[str, str] = {
    # School of Engineering
    "mit-eecs-bs": "Bachelor of Science in Electrical Engineering and Computer Science",
    "mit-eecs-phd": "Doctor of Philosophy in Electrical Engineering and Computer Science",
    "mit-meche-bs": "Bachelor of Science in Mechanical Engineering",
    "mit-meche-phd": "Doctor of Philosophy in Mechanical Engineering",
    "mit-aeroastro-bs": "Bachelor of Science in Aerospace Engineering",
    "mit-aeroastro-phd": "Doctor of Philosophy in Aeronautics and Astronautics",
    "mit-cheme-bs": "Bachelor of Science in Chemical Engineering",
    "mit-dmse-bs": "Bachelor of Science in Materials Science and Engineering",
    "mit-be-bs": "Bachelor of Science in Biological Engineering",
    "mit-cee-bs": "Bachelor of Science in Civil and Environmental Engineering",
    "mit-nse-bs": "Bachelor of Science in Nuclear Science and Engineering",
    "mit-statistics-phd": "Doctor of Philosophy in Statistics",
    "mit-tpp-sm": "Master of Science in Technology and Policy",
    # School of Science
    "mit-physics-bs": "Bachelor of Science in Physics",
    "mit-physics-phd": "Doctor of Philosophy in Physics",
    "mit-math-bs": "Bachelor of Science in Mathematics",
    "mit-math-phd": "Doctor of Philosophy in Mathematics",
    "mit-math-cs-bs": "Bachelor of Science in Mathematics with Computer Science",
    "mit-biology-bs": "Bachelor of Science in Biology",
    "mit-chemistry-bs": "Bachelor of Science in Chemistry",
    "mit-chemistry-phd": "Doctor of Philosophy in Chemistry",
    "mit-bcs-bs": "Bachelor of Science in Brain and Cognitive Sciences",
    "mit-eaps-bs": "Bachelor of Science in Earth, Atmospheric, and Planetary Sciences",
    # School of Humanities, Arts, and Social Sciences
    "mit-economics-bs": "Bachelor of Science in Economics",
    "mit-economics-phd": "Doctor of Philosophy in Economics",
    "mit-linguistics-philosophy-bs": "Bachelor of Science in Linguistics and Philosophy",
    "mit-political-science-bs": "Bachelor of Science in Political Science",
    "mit-cms-writing-bs": "Bachelor of Science in Comparative Media Studies",
    "mit-anthropology-bs": "Bachelor of Science in Anthropology",
    "mit-history-bs": "Bachelor of Science in History",
    "mit-literature-bs": "Bachelor of Science in Literature",
    "mit-music-bs": "Bachelor of Science in Music",
    "mit-sts-bs": "Bachelor of Science in Science, Technology, and Society",
    "mit-global-languages-bs": "Bachelor of Science in Global Studies and Languages",
    "mit-science-writing-sm": "Master of Science in Science Writing",
    # MIT Sloan School of Management
    "mit-management-bs": "Bachelor of Science in Management",
    "mit-business-analytics-bs": "Bachelor of Science in Business Analytics",
    "mit-finance-bs": "Bachelor of Science in Finance",
    "mit-sloan-mba": "Master of Business Administration",
    "mit-sloan-mfin": "Master of Finance",
    "mit-sloan-mban": "Master of Business Analytics",
    "mit-sloan-phd": "Doctor of Philosophy in Management",
    "mit-sloan-fellows-mba": "MIT Sloan Fellows MBA",
    "mit-sdm-sm": "Master of Science in Engineering and Management",
    # School of Architecture and Planning
    "mit-architecture-bs": "Bachelor of Science in Architecture",
    "mit-architecture-march": "Master of Architecture",
    "mit-dusp-bs": "Bachelor of Science in Urban Studies and Planning",
    "mit-city-planning-sm": "Master in City Planning",
    "mit-mediaarts-sm": "Master of Science in Media Arts and Sciences",
    "mit-red-sm": "Master of Science in Real Estate Development",
    # MIT Stephen A. Schwarzman College of Computing
    "mit-cs-6-3-bs": "Bachelor of Science in Computer Science and Engineering",
    "mit-ai-6-4-bs": "Bachelor of Science in Artificial Intelligence and Decision Making",
    "mit-comp-cognition-bs": "Bachelor of Science in Computation and Cognition",
    "mit-cs-econ-data-bs": "Bachelor of Science in Computer Science, Economics, and Data Science",
    "mit-cse-phd": "Doctor of Philosophy in Computational Science and Engineering",
    # Online MicroMasters (non-degree credentials)
    "mit-mm-supply-chain": "MicroMasters Program in Supply Chain Management",
    "mit-mm-statistics-data-science": "MicroMasters Program in Statistics and Data Science",
    "mit-mm-data-econ-policy": "MicroMasters Program in Data, Economics, and Design of Policy",
    "mit-mm-manufacturing": "MicroMasters Program in Principles of Manufacturing",
    "mit-mm-finance": "MicroMasters Program in Finance",
    # MIT Professional Education certificates
    "mit-pe-ml-ai": (
        "Professional Certificate Program in Machine Learning & Artificial Intelligence"
    ),
    "mit-pe-design-manufacturing": "Professional Certificate Program in Design & Manufacturing",
    "mit-pe-sustainability": "Professional Certificate Program in Sustainability",
    "mit-pe-cto": "MIT Chief Technology Officer Program",
    "mit-pe-innovation-tech": "Professional Certificate Program in Innovation & Technology",
}

# Official program-page URLs. Every URL was verified to resolve at author time;
# uncertain deep links fall back to the verified department or program home page
# so the "Visit the official program page" link never 404s.
_WEBSITE_BY_SLUG: dict[str, str] = {
    "mit-eecs-bs": "https://www.eecs.mit.edu/",
    "mit-eecs-phd": "https://www.eecs.mit.edu/academics/graduate-programs/",
    "mit-meche-bs": "https://meche.mit.edu/",
    "mit-meche-phd": "https://meche.mit.edu/education/graduate",
    "mit-aeroastro-bs": "https://aeroastro.mit.edu/",
    "mit-aeroastro-phd": "https://aeroastro.mit.edu/",
    "mit-cheme-bs": "https://cheme.mit.edu/",
    "mit-dmse-bs": "https://dmse.mit.edu/",
    "mit-be-bs": "https://be.mit.edu/",
    "mit-cee-bs": "https://cee.mit.edu/",
    "mit-nse-bs": "https://web.mit.edu/nse/",
    "mit-statistics-phd": "https://idss.mit.edu/",
    "mit-tpp-sm": "https://idss.mit.edu/",
    "mit-physics-bs": "https://physics.mit.edu/",
    "mit-physics-phd": "https://physics.mit.edu/academic-programs/graduate-students/",
    "mit-math-bs": "https://math.mit.edu/",
    "mit-math-phd": "https://math.mit.edu/academics/grad/",
    "mit-math-cs-bs": "https://math.mit.edu/academics/undergrad/",
    "mit-biology-bs": "https://biology.mit.edu/",
    "mit-chemistry-bs": "https://chemistry.mit.edu/",
    "mit-chemistry-phd": "https://chemistry.mit.edu/",
    "mit-bcs-bs": "https://bcs.mit.edu/",
    "mit-eaps-bs": "https://eapsweb.mit.edu/",
    "mit-economics-bs": "https://economics.mit.edu/",
    "mit-economics-phd": "https://economics.mit.edu/graduate",
    "mit-linguistics-philosophy-bs": "https://linguistics.mit.edu/",
    "mit-political-science-bs": "https://polisci.mit.edu/",
    "mit-cms-writing-bs": "https://cmsw.mit.edu/",
    "mit-anthropology-bs": "https://anthropology.mit.edu/",
    "mit-history-bs": "https://history.mit.edu/",
    "mit-literature-bs": "https://lit.mit.edu/",
    "mit-music-bs": "https://mta.mit.edu/",
    "mit-sts-bs": "https://sts-program.mit.edu/",
    "mit-global-languages-bs": "https://languages.mit.edu/",
    "mit-science-writing-sm": "https://sciwrite.mit.edu/",
    "mit-management-bs": "https://mitsloan.mit.edu/undergrad",
    "mit-business-analytics-bs": "https://mitsloan.mit.edu/undergrad",
    "mit-finance-bs": "https://mitsloan.mit.edu/undergrad",
    "mit-sloan-mba": "https://mitsloan.mit.edu/mba",
    "mit-sloan-mfin": "https://mitsloan.mit.edu/mfin",
    "mit-sloan-mban": "https://mitsloan.mit.edu/master-of-business-analytics",
    "mit-sloan-phd": "https://mitsloan.mit.edu/phd",
    "mit-sloan-fellows-mba": "https://mitsloan.mit.edu/fellows",
    "mit-sdm-sm": "https://sdm.mit.edu/",
    "mit-architecture-bs": "https://architecture.mit.edu/",
    "mit-architecture-march": "https://architecture.mit.edu/",
    "mit-dusp-bs": "https://dusp.mit.edu/",
    "mit-city-planning-sm": "https://dusp.mit.edu/",
    "mit-mediaarts-sm": "https://www.media.mit.edu/",
    "mit-red-sm": "https://cre.mit.edu/",
    "mit-cs-6-3-bs": "https://www.eecs.mit.edu/",
    "mit-ai-6-4-bs": "https://www.eecs.mit.edu/",
    "mit-comp-cognition-bs": "https://www.eecs.mit.edu/",
    "mit-cs-econ-data-bs": "https://www.eecs.mit.edu/",
    "mit-cse-phd": "https://computing.mit.edu/",
    "mit-mm-supply-chain": "https://micromasters.mit.edu/scm/",
    "mit-mm-statistics-data-science": "https://micromasters.mit.edu/ds/",
    "mit-mm-data-econ-policy": "https://micromasters.mit.edu/dedp/",
    "mit-mm-manufacturing": "https://micromasters.mit.edu/",
    "mit-mm-finance": "https://mitsloan.mit.edu/",
    "mit-pe-ml-ai": "https://professional.mit.edu/",
    "mit-pe-design-manufacturing": "https://professional.mit.edu/",
    "mit-pe-sustainability": "https://professional.mit.edu/",
    "mit-pe-cto": "https://professional.mit.edu/",
    "mit-pe-innovation-tech": "https://professional.mit.edu/",
}


# Real MIT campus photo (the Great Dome over Killian Court) — Wikimedia Commons,
# hotlinkable, landscape JPG. Leads the hero on the institution detail page.
_CAMPUS_PHOTO = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/"
    "Great_dome_of_MIT%2C_Feb_2021_%282%29_%28cropped%29.jpg/"
    "1920px-Great_dome_of_MIT%2C_Feb_2021_%282%29_%28cropped%29.jpg"
)


# ── 2026-06-10 enrichment-run research (live-verified + cited) ─────────────
# Faculty leads: each unit's CURRENT head/director, verified on the official
# department leadership/people page (source_url per entry).
_DEPT_FACULTY: dict[str, dict] = {
    "eecs": {
        "lead": [
            {
                "name": "Asu Ozdaglar",
                "title": (
                    "Department Head; MathWorks Professor of Electrical Engineering and Computer "
                    "Science"
                ),
            },
        ],
        "directory_url": "https://www.eecs.mit.edu/role/faculty/",
        "source_url": "https://www.eecs.mit.edu/leadership/",
    },
    "meche": {
        "lead": [
            {
                "name": "A. John Hart",
                "title": "Professor; Department Head",
            },
        ],
        "directory_url": "https://meche.mit.edu/people",
        "source_url": "https://meche.mit.edu/people",
    },
    "aeroastro": {
        "lead": [
            {
                "name": "Julie Shah",
                "title": "Department Head; H.N. Slater Professor in Aeronautics and Astronautics",
            },
        ],
        "directory_url": "https://aeroastro.mit.edu/faculty/",
        "source_url": "https://aeroastro.mit.edu/people/julie-shah/",
    },
    "cheme": {
        "lead": [
            {
                "name": "Kristala L. Jones Prather",
                "title": "Department Head",
            },
        ],
        "directory_url": "https://cheme.mit.edu/people/faculty/",
        "source_url": "https://cheme.mit.edu/rank/dep-head/",
    },
    "dmse": {
        "lead": [
            {
                "name": "Polina Anikeeva",
                "title": (
                    "Head, Department of Materials Science and Engineering; Matoula S. Salapatas "
                    "Professor of Materials Science and Engineering"
                ),
            },
        ],
        "directory_url": "https://dmse.mit.edu/people/faculty/",
        "source_url": "https://dmse.mit.edu/people/faculty/polina-anikeeva/",
    },
    "be": {
        "lead": [
            {
                "name": "Christopher A. Voigt",
                "title": "Professor, Department Head",
            },
        ],
        "directory_url": "https://be.mit.edu/faculty/",
        "source_url": "https://be.mit.edu/faculty/",
    },
    "cee": {
        "lead": [
            {
                "name": "Ali Jadbabaie",
                "title": "Department Head; JR East Professor",
            },
        ],
        "directory_url": "https://cee.mit.edu/people_type/faculty/",
        "source_url": "https://cee.mit.edu/about/leadership/",
    },
    "nse": {
        "lead": [
            {
                "name": "Benoit Forget",
                "title": "KEPCO Professor of Nuclear Science and Engineering; Department Head",
            },
        ],
        "directory_url": "https://nse.mit.edu/people/",
        "source_url": "https://nse.mit.edu/people/benoit-forget/",
    },
    "physics": {
        "lead": [
            {
                "name": "Deepto Chakrabarty",
                "title": "Professor of Physics and Department Head",
            },
        ],
        "directory_url": "https://physics.mit.edu/faculty/",
        "source_url": "https://physics.mit.edu/about-physics/",
    },
    "math": {
        "lead": [
            {
                "name": "Michel Goemans",
                "title": "RSA Professor of Mathematics, Department Head",
            },
        ],
        "directory_url": "https://math.mit.edu/directory/faculty/",
        "source_url": "https://math.mit.edu/directory/profile.html?pid=84",
    },
    "biology": {
        "lead": [
            {
                "name": "Amy E. Keating",
                "title": (
                    "Jay A. Stein (1968) Professor of Biology, Professor of Biological "
                    "Engineering, Department Head"
                ),
            },
        ],
        "directory_url": "https://biology.mit.edu/about/faculty-directory/",
        "source_url": "https://biology.mit.edu/profile/amy-e-keating/",
    },
    "chemistry": {
        "lead": [
            {
                "name": "Matthew D. Shoulders",
                "title": "Class of 1942 Professor of Chemistry, Department Head",
            },
        ],
        "directory_url": "https://chemistry.mit.edu/faculty/",
        "source_url": "https://chemistry.mit.edu/profile/matthew-d-shoulders/",
    },
    "bcs": {
        "lead": [
            {
                "name": "Michale Fee",
                "title": "Department Head",
            },
        ],
        "directory_url": "https://bcs.mit.edu/faculty",
        "source_url": "https://bcs.mit.edu/about-bcs/leadership-and-governance",
    },
    "eaps": {
        "lead": [
            {
                "name": "David McGee",
                "title": "Professor, Department Head - EAPS",
            },
        ],
        "directory_url": "https://eaps.mit.edu/people/faculty/",
        "source_url": "https://eaps.mit.edu/people/leadership/",
    },
    "economics": {
        "lead": [
            {
                "name": "Jonathan Gruber",
                "title": "Ford Professor of Economics; Department Head",
            },
        ],
        "directory_url": "https://economics.mit.edu/people/faculty",
        "source_url": "https://economics.mit.edu/people/faculty/jonathan-gruber",
    },
    "ling_phil": {
        "lead": [
            {
                "name": "Kieran Setiya",
                "title": "Department Head, Peter de Florez Professor",
            },
        ],
        "directory_url": "https://philosophy.mit.edu/faculty",
        "source_url": "https://philosophy.mit.edu/faculty",
    },
    "polisci": {
        "lead": [
            {
                "name": "David A. Singer",
                "title": (
                    "Department Head; Raphael Dorman-Helen Starbuck Professor of Political "
                    "Science"
                ),
            },
        ],
        "directory_url": "https://polisci.mit.edu/people/faculty",
        "source_url": "https://polisci.mit.edu/people/faculty",
    },
    "cmsw": {
        "lead": [
            {
                "name": "Seth Mnookin",
                "title": (
                    "Head, Comparative Media Studies/Writing Program; Professor of Science "
                    "Writing"
                ),
            },
        ],
        "directory_url": "https://cmsw.mit.edu/people/",
        "source_url": (
            "https://catalog.mit.edu/schools/humanities-arts-social-sciences/comparative-media-st"
            "udies-writing/"
        ),
    },
    "anthropology": {
        "lead": [
            {
                "name": "Christine J. Walley",
                "title": "Program Head; SHASS Dean's Distinguished Professor of Anthropology",
            },
        ],
        "directory_url": "https://anthropology.mit.edu/people",
        "source_url": "https://anthropology.mit.edu/people",
    },
    "history": {
        "lead": [
            {
                "name": "Malick W. Ghachem",
                "title": "Head of History; Professor of History",
            },
        ],
        "directory_url": "https://history.mit.edu/people/",
        "source_url": "https://history.mit.edu/people/",
    },
    "literature": {
        "lead": [
            {
                "name": "Sandy Alexandre",
                "title": "Associate Professor, Head",
            },
        ],
        "directory_url": "https://lit.mit.edu/people/faculty/",
        "source_url": "https://lit.mit.edu/people/faculty/",
    },
    "music": {
        "lead": [
            {
                "name": "Jay Scheib",
                "title": "Class of 1949 Professor; Section Head for Music & Theater Arts",
            },
        ],
        "directory_url": "https://mta.mit.edu/faculty-staff",
        "source_url": "https://mta.mit.edu/person/jay-scheib",
    },
    "sts": {
        "lead": [
            {
                "name": "Eden Medina",
                "title": "Department Head; Professor of Science, Technology, and Society (STS)",
            },
        ],
        "directory_url": "https://sts-program.mit.edu/people/",
        "source_url": "https://sts-program.mit.edu/people/",
    },
    "languages": {
        "lead": [
            {
                "name": "Per Urlaub",
                "title": (
                    "Director, Global Languages; Professor of the Practice of German and Second "
                    "Language Studies"
                ),
            },
        ],
        "directory_url": "https://languages.mit.edu/people/",
        "source_url": "https://languages.mit.edu/people/",
    },
    "sciwrite": {
        "lead": [
            {
                "name": "Seth Mnookin",
                "title": "Head, CMS/W; Director, Graduate Program in Science Writing; Professor",
            },
        ],
        "directory_url": "https://sciwrite.mit.edu/faculty-and-staff/",
        "source_url": "https://shass.mit.edu/people/seth-mnookin/",
    },
    "sloan": {
        "lead": [
            {
                "name": "Richard M. Locke",
                "title": "John C Head III Dean of MIT Sloan",
            },
        ],
        "directory_url": "https://mitsloan.mit.edu/faculty/directory",
        "source_url": "https://mitsloan.mit.edu/faculty/directory/richard-m-locke",
    },
    "architecture": {
        "lead": [
            {
                "name": "Nicholas de Monchaux",
                "title": "Weber-Shaughness Professor and Head of Architecture at MIT",
            },
        ],
        "directory_url": "https://architecture.mit.edu/people",
        "source_url": "https://architecture.mit.edu/people/nicholas-de-monchaux",
    },
    "dusp": {
        "lead": [
            {
                "name": "Chris Zegras",
                "title": "Professor of Mobility and Urban Planning, Department Head",
            },
        ],
        "directory_url": "https://dusp.mit.edu/people",
        "source_url": "https://dusp.mit.edu/people",
    },
    "media_lab": {
        "lead": [
            {
                "name": "Joseph A. Paradiso",
                "title": "Academic Head, Program in Media Arts and Sciences",
            },
            {
                "name": "Tod Machover",
                "title": "Faculty Director, MIT Media Lab",
            },
        ],
        "directory_url": "https://www.media.mit.edu/people/",
        "source_url": "https://officesdirectory.mit.edu/mas",
    },
    "cre": {
        "lead": [
            {
                "name": "Siqi Zheng",
                "title": (
                    "STL Champion Professor of Urban and Real Estate Sustainability; Faculty "
                    "Director, MIT Center for Real Estate"
                ),
            },
        ],
        "directory_url": "https://cre.mit.edu/people/",
        "source_url": "https://cre.mit.edu/people/",
    },
    "idss": {
        "lead": [
            {
                "name": "Fotini Christia",
                "title": "Director, IDSS; Ford International Professor",
            },
            {
                "name": "Christine Ortiz",
                "title": (
                    "Director, Technology and Policy Program; Morris Cohen Professor in Materials"
                    " Science and Engineering"
                ),
            },
        ],
        "directory_url": "https://idss.mit.edu/about/people/",
        "source_url": "https://idss.mit.edu/about/people/",
    },
    "ccse": {
        "lead": [
            {
                "name": "Laurent Demanet",
                "title": (
                    "Co-Director, Center for Computational Science and Engineering; Professor of "
                    "Applied Mathematics"
                ),
            },
            {
                "name": "Nicolas G. Hadjiconstantinou",
                "title": (
                    "Co-Director, Center for Computational Science and Engineering; Quentin Berg "
                    "(1937) Professor of Mechanical Engineering"
                ),
            },
        ],
        "directory_url": "https://cse.mit.edu/people/",
        "source_url": "https://cse.mit.edu/about/leadership/",
    },
    "sdm": {
        "lead": [
            {
                "name": "Michael Cusumano",
                "title": "SDM Faculty Co-Director, Professor of Management",
            },
            {
                "name": "Warren Seering",
                "title": "SDM Faculty Co-Director, Professor of Mechanical Engineering",
            },
            {
                "name": "Joan Rubin",
                "title": "Executive Director, SDM Program and Senior Lecturer",
            },
        ],
        "directory_url": "https://sdm.mit.edu/people/",
        "source_url": "https://sdm.mit.edu/people/",
    },
}

# news.mit.edu per-department RSS feeds — every news_rss fetched this run and
# confirmed to return RSS/XML. Events: the verified calendar.mit.edu Localist
# .ics endpoint, keyword-filtered per program (the MBAn pattern).
_DEPT_CONTENT: dict[str, dict] = {
    "eecs": {
        "news_rss": "https://news.mit.edu/rss/topic/electrical-engineering-computer-science-eecs",
        "news_url": "https://news.mit.edu/topic/electrical-engineering-computer-science-eecs",
        "keywords": [
            "eecs",
            "computer science",
            "electrical engineering",
            "artificial intelligence",
            "computing",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=eecs",
            "type": "ical",
        },
    },
    "meche": {
        "news_rss": "https://news.mit.edu/rss/topic/mechanical-engineering",
        "news_url": "https://news.mit.edu/topic/mechanical-engineering",
        "keywords": [
            "mechanical engineering",
            "robotics",
            "manufacturing",
            "design",
            "meche",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=mechanical+engineering",
            "type": "ical",
        },
    },
    "aeroastro": {
        "news_rss": "https://news.mit.edu/rss/topic/aeronautics",
        "news_url": "https://news.mit.edu/topic/aeronautics",
        "keywords": [
            "aeronautics",
            "astronautics",
            "aerospace",
            "space",
            "aviation",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=aeronautics",
            "type": "ical",
        },
    },
    "cheme": {
        "news_rss": "https://news.mit.edu/rss/topic/chemical-engineering",
        "news_url": "https://news.mit.edu/topic/chemical-engineering",
        "keywords": [
            "chemical engineering",
            "process engineering",
            "catalysis",
            "energy",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=chemical+engineering",
            "type": "ical",
        },
    },
    "dmse": {
        "news_rss": "https://news.mit.edu/rss/topic/materials-science-and-engineering",
        "news_url": "https://news.mit.edu/topic/materials-science",
        "keywords": [
            "materials science",
            "materials engineering",
            "nanomaterials",
            "metallurgy",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=materials+science",
            "type": "ical",
        },
    },
    "be": {
        "news_rss": "https://news.mit.edu/rss/topic/biological-engineering",
        "news_url": "https://news.mit.edu/topic/biological-engineering",
        "keywords": [
            "biological engineering",
            "biotechnology",
            "synthetic biology",
            "bioengineering",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=biological+engineering",
            "type": "ical",
        },
    },
    "cee": {
        "news_rss": "https://news.mit.edu/rss/topic/civil-engineering",
        "news_url": "https://news.mit.edu/topic/civil-engineering",
        "keywords": [
            "civil engineering",
            "environmental engineering",
            "infrastructure",
            "sustainability",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=civil+engineering",
            "type": "ical",
        },
    },
    "nse": {
        "news_rss": "https://news.mit.edu/rss/topic/nuclear-engineering",
        "news_url": "https://news.mit.edu/topic/nuclear-engineering",
        "keywords": [
            "nuclear engineering",
            "nuclear energy",
            "fusion",
            "reactors",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=nuclear+engineering",
            "type": "ical",
        },
    },
    "physics": {
        "news_rss": "https://news.mit.edu/rss/topic/physics",
        "news_url": "https://news.mit.edu/topic/physics",
        "keywords": [
            "physics",
            "quantum",
            "astrophysics",
            "particle physics",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=physics",
            "type": "ical",
        },
    },
    "math": {
        "news_rss": "https://news.mit.edu/rss/topic/mathematics",
        "news_url": "https://news.mit.edu/topic/mathematics",
        "keywords": [
            "mathematics",
            "applied math",
            "statistics",
            "theory",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=mathematics",
            "type": "ical",
        },
    },
    "biology": {
        "news_rss": "https://news.mit.edu/rss/topic/biology-and-genetics",
        "news_url": "https://news.mit.edu/topic/biology",
        "keywords": [
            "biology",
            "genetics",
            "molecular biology",
            "life sciences",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=biology",
            "type": "ical",
        },
    },
    "chemistry": {
        "news_rss": "https://news.mit.edu/rss/topic/chemistry",
        "news_url": "https://news.mit.edu/topic/chemistry-0",
        "keywords": [
            "chemistry",
            "organic chemistry",
            "chemical synthesis",
            "spectroscopy",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=chemistry",
            "type": "ical",
        },
    },
    "bcs": {
        "news_rss": "https://news.mit.edu/rss/topic/neuroscience-neurology-and-cognitive-sciences",
        "news_url": "https://news.mit.edu/topic/neuroscience",
        "keywords": [
            "neuroscience",
            "cognitive science",
            "brain",
            "psychology",
            "neurology",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=neuroscience",
            "type": "ical",
        },
    },
    "eaps": {
        "news_rss": "https://news.mit.edu/rss/topic/earth-and-atmospheric-sciences",
        "news_url": "https://news.mit.edu/topic/eaps",
        "keywords": [
            "earth science",
            "atmospheric science",
            "planetary science",
            "climate",
            "geology",
            "oceanography",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=earth+science",
            "type": "ical",
        },
    },
    "economics": {
        "news_rss": "https://news.mit.edu/rss/topic/economics",
        "news_url": "https://news.mit.edu/topic/economics",
        "keywords": [
            "economics",
            "econometrics",
            "development economics",
            "policy",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=economics",
            "type": "ical",
        },
    },
    "ling_phil": {
        "news_rss": "https://news.mit.edu/rss/topic/language-and-linguistics",
        "news_url": "https://news.mit.edu/topic/linguistics",
        "keywords": [
            "linguistics",
            "language",
            "syntax",
            "phonology",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=linguistics",
            "type": "ical",
        },
    },
    "polisci": {
        "news_rss": "https://news.mit.edu/rss/topic/political-science",
        "news_url": "https://news.mit.edu/topic/political-science",
        "keywords": [
            "political science",
            "policy",
            "government",
            "international relations",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=political+science",
            "type": "ical",
        },
    },
    "architecture": {
        "news_rss": "https://news.mit.edu/rss/topic/architecture",
        "news_url": "https://news.mit.edu/topic/architecture",
        "keywords": [
            "architecture",
            "design",
            "built environment",
            "urbanism",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=architecture",
            "type": "ical",
        },
    },
    "dusp": {
        "news_rss": "https://news.mit.edu/rss/topic/urban-studies",
        "news_url": "https://news.mit.edu/topic/urban-studies",
        "keywords": [
            "urban planning",
            "urban studies",
            "cities",
            "housing",
            "transportation",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=urban+planning",
            "type": "ical",
        },
    },
}

_DEPT_BY_SLUG: dict[str, str] = {
    "mit-eecs-bs": "eecs",
    "mit-eecs-phd": "eecs",
    "mit-cs-6-3-bs": "eecs",
    "mit-ai-6-4-bs": "eecs",
    "mit-comp-cognition-bs": "eecs",
    "mit-cs-econ-data-bs": "eecs",
    "mit-meche-bs": "meche",
    "mit-meche-phd": "meche",
    "mit-aeroastro-bs": "aeroastro",
    "mit-aeroastro-phd": "aeroastro",
    "mit-cheme-bs": "cheme",
    "mit-dmse-bs": "dmse",
    "mit-be-bs": "be",
    "mit-cee-bs": "cee",
    "mit-nse-bs": "nse",
    "mit-physics-bs": "physics",
    "mit-physics-phd": "physics",
    "mit-math-bs": "math",
    "mit-math-phd": "math",
    "mit-math-cs-bs": "math",
    "mit-biology-bs": "biology",
    "mit-chemistry-bs": "chemistry",
    "mit-chemistry-phd": "chemistry",
    "mit-bcs-bs": "bcs",
    "mit-eaps-bs": "eaps",
    "mit-economics-bs": "economics",
    "mit-economics-phd": "economics",
    "mit-linguistics-philosophy-bs": "ling_phil",
    "mit-political-science-bs": "polisci",
    "mit-cms-writing-bs": "cmsw",
    "mit-anthropology-bs": "anthropology",
    "mit-history-bs": "history",
    "mit-literature-bs": "literature",
    "mit-music-bs": "music",
    "mit-sts-bs": "sts",
    "mit-global-languages-bs": "languages",
    "mit-science-writing-sm": "sciwrite",
    "mit-management-bs": "sloan",
    "mit-business-analytics-bs": "sloan",
    "mit-finance-bs": "sloan",
    "mit-sloan-mba": "sloan",
    "mit-sloan-mfin": "sloan",
    "mit-sloan-fellows-mba": "sloan",
    "mit-sloan-phd": "sloan",
    "mit-architecture-bs": "architecture",
    "mit-architecture-march": "architecture",
    "mit-dusp-bs": "dusp",
    "mit-city-planning-sm": "dusp",
    "mit-mediaarts-sm": "media_lab",
    "mit-red-sm": "cre",
    "mit-tpp-sm": "idss",
    "mit-statistics-phd": "idss",
    "mit-cse-phd": "ccse",
    "mit-sdm-sm": "sdm",
}

# Programs whose home unit has no MIT News department feed use their school's
# verified feed + a program keyword gate (the MBAn home-discipline pattern).
_PROG_CONTENT_EXTRA: dict[str, dict] = {
    "mit-cms-writing-bs": {
        "news_rss": "https://news.mit.edu/rss/school/humanities-arts-and-social-sciences",
        "news_url": "https://news.mit.edu/topic/school-humanities-arts-and-social-sciences",
        "keywords": [
            "comparative media studies",
            "writing",
            "media",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=media+studies",
            "type": "ical",
        },
    },
    "mit-anthropology-bs": {
        "news_rss": "https://news.mit.edu/rss/school/humanities-arts-and-social-sciences",
        "news_url": "https://news.mit.edu/topic/school-humanities-arts-and-social-sciences",
        "keywords": [
            "anthropology",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=anthropology",
            "type": "ical",
        },
    },
    "mit-history-bs": {
        "news_rss": "https://news.mit.edu/rss/school/humanities-arts-and-social-sciences",
        "news_url": "https://news.mit.edu/topic/school-humanities-arts-and-social-sciences",
        "keywords": [
            "history",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=history",
            "type": "ical",
        },
    },
    "mit-literature-bs": {
        "news_rss": "https://news.mit.edu/rss/school/humanities-arts-and-social-sciences",
        "news_url": "https://news.mit.edu/topic/school-humanities-arts-and-social-sciences",
        "keywords": [
            "literature",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=literature",
            "type": "ical",
        },
    },
    "mit-music-bs": {
        "news_rss": "https://news.mit.edu/rss/school/humanities-arts-and-social-sciences",
        "news_url": "https://news.mit.edu/topic/school-humanities-arts-and-social-sciences",
        "keywords": [
            "music",
            "theater",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=music",
            "type": "ical",
        },
    },
    "mit-sts-bs": {
        "news_rss": "https://news.mit.edu/rss/school/humanities-arts-and-social-sciences",
        "news_url": "https://news.mit.edu/topic/school-humanities-arts-and-social-sciences",
        "keywords": [
            "science technology and society",
            "sts",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=science+technology+society",
            "type": "ical",
        },
    },
    "mit-global-languages-bs": {
        "news_rss": "https://news.mit.edu/rss/school/humanities-arts-and-social-sciences",
        "news_url": "https://news.mit.edu/topic/school-humanities-arts-and-social-sciences",
        "keywords": [
            "global languages",
            "language",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=languages",
            "type": "ical",
        },
    },
    "mit-science-writing-sm": {
        "news_rss": "https://news.mit.edu/rss/school/humanities-arts-and-social-sciences",
        "news_url": "https://news.mit.edu/topic/school-humanities-arts-and-social-sciences",
        "keywords": [
            "science writing",
            "science journalism",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=science+writing",
            "type": "ical",
        },
    },
    "mit-management-bs": {
        "news_rss": "https://news.mit.edu/rss/school/management",
        "news_url": "https://news.mit.edu/topic/sloan-school-management",
        "keywords": [
            "management",
            "undergraduate business",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=management",
            "type": "ical",
        },
    },
    "mit-business-analytics-bs": {
        "news_rss": "https://news.mit.edu/rss/school/management",
        "news_url": "https://news.mit.edu/topic/sloan-school-management",
        "keywords": [
            "business analytics",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=business+analytics",
            "type": "ical",
        },
    },
    "mit-finance-bs": {
        "news_rss": "https://news.mit.edu/rss/school/management",
        "news_url": "https://news.mit.edu/topic/sloan-school-management",
        "keywords": [
            "finance",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=finance",
            "type": "ical",
        },
    },
    "mit-sloan-mba": {
        "news_rss": "https://news.mit.edu/rss/school/management",
        "news_url": "https://news.mit.edu/topic/sloan-school-management",
        "keywords": [
            "mba",
            "sloan",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=mba",
            "type": "ical",
        },
    },
    "mit-sloan-mfin": {
        "news_rss": "https://news.mit.edu/rss/school/management",
        "news_url": "https://news.mit.edu/topic/sloan-school-management",
        "keywords": [
            "master of finance",
            "mfin",
            "finance",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=finance",
            "type": "ical",
        },
    },
    "mit-sloan-fellows-mba": {
        "news_rss": "https://news.mit.edu/rss/school/management",
        "news_url": "https://news.mit.edu/topic/sloan-school-management",
        "keywords": [
            "sloan fellows",
            "mid-career",
            "executive",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=sloan+fellows",
            "type": "ical",
        },
    },
    "mit-sloan-phd": {
        "news_rss": "https://news.mit.edu/rss/school/management",
        "news_url": "https://news.mit.edu/topic/sloan-school-management",
        "keywords": [
            "management research",
            "doctoral",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=research",
            "type": "ical",
        },
    },
    "mit-sdm-sm": {
        "news_rss": "https://news.mit.edu/rss/school/engineering",
        "news_url": "https://news.mit.edu/topic/school-engineering",
        "keywords": [
            "system design",
            "engineering management",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=system+design",
            "type": "ical",
        },
    },
    "mit-red-sm": {
        "news_rss": "https://news.mit.edu/rss/school/architecture-and-planning",
        "news_url": "https://news.mit.edu/topic/school-architecture-and-planning",
        "keywords": [
            "real estate",
            "real estate development",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=real+estate",
            "type": "ical",
        },
    },
    "mit-mediaarts-sm": {
        "news_rss": "https://news.mit.edu/rss/school/architecture-and-planning",
        "news_url": "https://news.mit.edu/clp/media-lab",
        "keywords": [
            "media lab",
            "media arts",
            "human-computer interaction",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=media+lab",
            "type": "ical",
        },
    },
    "mit-tpp-sm": {
        "news_rss": "https://news.mit.edu/rss/school/engineering",
        "news_url": "https://news.mit.edu/topic/school-engineering",
        "keywords": [
            "technology policy",
            "policy",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=technology+policy",
            "type": "ical",
        },
    },
    "mit-statistics-phd": {
        "news_rss": "https://news.mit.edu/rss/topic/computing",
        "news_url": "https://news.mit.edu/topic/computing",
        "keywords": [
            "statistics",
            "data science",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=statistics",
            "type": "ical",
        },
    },
    "mit-cse-phd": {
        "news_rss": "https://news.mit.edu/rss/topic/computing",
        "news_url": "https://news.mit.edu/topic/computing",
        "keywords": [
            "computational science",
            "simulation",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=computational+science",
            "type": "ical",
        },
    },
    "mit-mm-supply-chain": {
        "news_rss": "https://news.mit.edu/rss/school/engineering",
        "news_url": "https://news.mit.edu/topic/school-engineering",
        "keywords": [
            "supply chain",
            "logistics",
            "micromasters",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=supply+chain",
            "type": "ical",
        },
    },
    "mit-mm-statistics-data-science": {
        "news_rss": "https://news.mit.edu/rss/topic/computing",
        "news_url": "https://news.mit.edu/topic/computing",
        "keywords": [
            "statistics",
            "data science",
            "micromasters",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=data+science",
            "type": "ical",
        },
    },
    "mit-mm-data-econ-policy": {
        "news_rss": "https://news.mit.edu/rss/school/humanities-arts-and-social-sciences",
        "news_url": "https://news.mit.edu/topic/school-humanities-arts-and-social-sciences",
        "keywords": [
            "development economics",
            "policy",
            "micromasters",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=economics",
            "type": "ical",
        },
    },
    "mit-mm-manufacturing": {
        "news_rss": "https://news.mit.edu/rss/school/engineering",
        "news_url": "https://news.mit.edu/topic/school-engineering",
        "keywords": [
            "manufacturing",
            "micromasters",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=manufacturing",
            "type": "ical",
        },
    },
    "mit-mm-finance": {
        "news_rss": "https://news.mit.edu/rss/school/management",
        "news_url": "https://news.mit.edu/topic/sloan-school-management",
        "keywords": [
            "finance",
            "micromasters",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=finance",
            "type": "ical",
        },
    },
    "mit-pe-ml-ai": {
        "news_rss": "https://news.mit.edu/rss/topic/computing",
        "news_url": "https://news.mit.edu/topic/computing",
        "keywords": [
            "machine learning",
            "artificial intelligence",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=machine+learning",
            "type": "ical",
        },
    },
    "mit-pe-design-manufacturing": {
        "news_rss": "https://news.mit.edu/rss/school/engineering",
        "news_url": "https://news.mit.edu/topic/school-engineering",
        "keywords": [
            "design",
            "manufacturing",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=manufacturing",
            "type": "ical",
        },
    },
    "mit-pe-sustainability": {
        "news_rss": "https://news.mit.edu/rss/school/engineering",
        "news_url": "https://news.mit.edu/topic/school-engineering",
        "keywords": [
            "sustainability",
            "climate",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=sustainability",
            "type": "ical",
        },
    },
    "mit-pe-cto": {
        "news_rss": "https://news.mit.edu/rss/school/management",
        "news_url": "https://news.mit.edu/topic/sloan-school-management",
        "keywords": [
            "technology leadership",
            "innovation",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=technology+leadership",
            "type": "ical",
        },
    },
    "mit-pe-innovation-tech": {
        "news_rss": "https://news.mit.edu/rss/school/engineering",
        "news_url": "https://news.mit.edu/topic/school-engineering",
        "keywords": [
            "innovation",
            "technology",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=innovation",
            "type": "ical",
        },
    },
}

# Joint majors are administered by two departments; both verified heads lead.
_JOINT_FACULTY: dict[str, list[str]] = {
    "mit-comp-cognition-bs": ["eecs", "bcs"],
    "mit-cs-econ-data-bs": ["eecs", "economics"],
}


def _faculty_for(slug: str) -> dict | None:
    """Department-head faculty lead for a program (joint majors get both)."""
    if slug in _JOINT_FACULTY:
        keys = _JOINT_FACULTY[slug]
        return {
            "lead": [d["lead"][0] for d in (_DEPT_FACULTY[k] for k in keys)],
            "directory_url": _DEPT_FACULTY[keys[0]]["directory_url"],
            "source_url": _DEPT_FACULTY[keys[0]]["source_url"],
        }
    key = _DEPT_BY_SLUG.get(slug)
    return _DEPT_FACULTY.get(key) if key else None


def _content_for(slug: str) -> dict | None:
    """Keyword-relevant feed set for a program (dept feed, else school feed)."""
    if slug in _PROG_CONTENT_EXTRA:
        return _PROG_CONTENT_EXTRA[slug]
    key = _DEPT_BY_SLUG.get(slug)
    return _DEPT_CONTENT.get(key) if key else None


# About tabs for the five non-Sloan schools — founded / current dean / notable
# faculty / research centers, live-verified on each school's official site
# (center URLs live at the institution's research.lab_links). SA+P's founding
# year is omitted: official MIT pages conflict (1865 catalog vs 1868 sap.mit.edu
# at department level) and the archives page was unreachable — recorded in its
# _standard.omitted rather than guessed.
_ABOUT_RESEARCH: dict[str, dict] = {
    _ENG: {
        "founded": 1932,
        "leadership": "Paula T. Hammond, Dean of Engineering; Institute Professor",
        "faculty": [
            {
                "name": "Hamsa Balakrishnan",
                "title": (
                    "Associate Dean, School of Engineering; William E. Leonhard (1940) Professor,"
                    " Aeronautics and Astronautics"
                ),
            },
            {
                "name": "Asu Ozdaglar",
                "title": (
                    "MathWorks Professor of Electrical Engineering and Computer Science; "
                    "Department Head, EECS"
                ),
            },
            {
                "name": "Polina Anikeeva",
                "title": "Professor, Materials Science and Engineering (Engineering Council)",
            },
            {
                "name": "A. John Hart",
                "title": "Professor, Mechanical Engineering (Engineering Council)",
            },
            {
                "name": "Antonio Torralba",
                "title": (
                    "Professor, Artificial Intelligence and Decision Making, EECS (Engineering "
                    "Council)"
                ),
            },
        ],
        "research_centers": [
            "Center for Transportation and Logistics",
            "Sociotechnical Systems Research Center",
            "Research Laboratory of Electronics",
            "Microsystems Technology Laboratories",
            "Materials Research Laboratory",
            "MIT.nano",
            "MIT D-Lab",
            "Institute for Medical Engineering and Science",
        ],
        "source": {
            "label": "School of Engineering",
            "url": "https://engineering.mit.edu/about/leadership/",
        },
    },
    _SCI: {
        "founded": 1932,
        "leadership": (
            "Nergis Mavalvala, Dean of the MIT School of Science (MIT's 11th Dean of Science); "
            "Curtis and Kathleen Marble Professor of Astrophysics"
        ),
        "faculty": [
            {
                "name": "Moungi Bawendi",
                "title": "Lester Wolfe Professor of Chemistry; 2023 Nobel laureate in chemistry",
            },
            {
                "name": "Myriam Heiman",
                "title": (
                    "John and Dorothy Wilson Professor of Neuroscience; director of the Picower "
                    "Institute for Learning and Memory effective July 1, 2026"
                ),
            },
            {
                "name": "Li-Huei Tsai",
                "title": (
                    "Picower Professor; director of the Picower Institute for Learning and "
                    "Memory, 2009-2026"
                ),
            },
            {
                "name": "Nergis Mavalvala",
                "title": (
                    "Curtis and Kathleen Marble Professor of Astrophysics; principal "
                    "investigator, MIT Kavli Institute for Astrophysics and Space Research"
                ),
            },
        ],
        "research_centers": [
            "MIT Kavli Institute for Astrophysics and Space Research",
            "McGovern Institute for Brain Research",
            "The Picower Institute for Learning and Memory",
            "Laboratory for Nuclear Science",
            "Center for Sustainability Science and Strategy",
        ],
        "source": {
            "label": "School of Science",
            "url": "https://science.mit.edu/about/",
        },
    },
    _SHASS: {
        "founded": 1950,
        "leadership": (
            "Agustín Rayo, Kenan Sahin Dean, MIT School of Humanities, Arts, and Social Sciences;"
            " professor of philosophy"
        ),
        "faculty": [
            {
                "name": "Esther Duflo",
                "title": (
                    "Abdul Latif Jameel Professor of Poverty Alleviation and Development "
                    "Economics; 2019 Nobel laureate in economics; co-founder of J-PAL"
                ),
            },
            {
                "name": "Abhijit Banerjee",
                "title": (
                    "Ford International Professor of Economics; 2019 Nobel laureate in economics;"
                    " co-founder of J-PAL"
                ),
            },
            {
                "name": "Agustín Rayo",
                "title": "Professor of philosophy; Kenan Sahin Dean of SHASS",
            },
        ],
        "research_centers": [
            "Center for International Studies",
            "MIT Security Studies Program",
            "Knight Science Journalism @MIT",
            "Abdul Latif Jameel Poverty Action Lab (J-PAL)",
        ],
        "source": {
            "label": "School of Humanities, Arts, and Social Sciences",
            "url": "https://shass.mit.edu/about-the-school/academic-units/",
        },
    },
    _SAP: {
        "leadership": (
            "Hashim Sarkis, Dean, MIT School of Architecture and Planning (since 2014); Elizabeth"
            " and James Killian (1926) Professor"
        ),
        "faculty": [
            {
                "name": "Hashim Sarkis",
                "title": (
                    "Dean of the School of Architecture and Planning; Professor of Architecture "
                    "and Professor of Urban Planning"
                ),
            },
            {
                "name": "Caroline Jones",
                "title": "Associate Dean, School of Architecture and Planning",
            },
            {
                "name": "Lawrence Vale",
                "title": "Associate Dean, School of Architecture and Planning",
            },
        ],
        "research_centers": [
            "MIT Media Lab",
            "MIT Center for Real Estate",
            "Program in Art, Culture and Technology",
            "Norman B. Leventhal Center for Advanced Urbanism",
            "MIT Morningside Academy for Design",
        ],
        "source": {
            "label": "School of Architecture and Planning",
            "url": "https://sap.mit.edu/overview",
        },
    },
    _COMPUTING: {
        "founded": 2019,
        "named_for": (
            "Stephen A. Schwarzman, chairman, CEO, and co-founder of Blackstone, whose $350 "
            "million gift made the college possible"
        ),
        "leadership": (
            "Daniel Huttenlocher, Dean, MIT Schwarzman College of Computing; Henry Ellis Warren "
            "(1894) Professor of Electrical Engineering and Computer Science"
        ),
        "faculty": [
            {
                "name": "Asu Ozdaglar",
                "title": (
                    "Deputy Dean of Academics, MIT Schwarzman College of Computing; Department "
                    "Head, Electrical Engineering and Computer Science; MathWorks Professor of "
                    "Electrical Engineering and Computer Science"
                ),
            },
            {
                "name": "Youssef Marzouk",
                "title": (
                    "Associate Dean, MIT Schwarzman College of Computing; Breene M. Kerr "
                    "Professor of Aeronautics and Astronautics"
                ),
            },
            {
                "name": "Brian Hedden",
                "title": (
                    "Associate Dean, Social and Ethical Responsibilities of Computing; Professor "
                    "of Philosophy"
                ),
            },
            {
                "name": "Aude Oliva",
                "title": (
                    "Director of Strategic Industry Engagement, MIT Schwarzman College of "
                    "Computing; MIT Director, MIT-IBM Watson AI Lab; Senior Research Scientist, "
                    "CSAIL"
                ),
            },
        ],
        "research_centers": [
            "Computer Science and Artificial Intelligence Laboratory (CSAIL)",
            "Laboratory for Information and Decision Systems (LIDS)",
            "Institute for Data, Systems, and Society (IDSS)",
            "MIT Siegel Family Quest for Intelligence",
            "MIT-IBM Watson AI Lab",
            "Abdul Latif Jameel Clinic for Machine Learning in Health (Jameel Clinic)",
        ],
        "source": {
            "label": "MIT Stephen A. Schwarzman College of Computing",
            "url": "https://computing.mit.edu/research/",
        },
    },
}
_ABOUT_BY_SCHOOL.update(_ABOUT_RESEARCH)

# School feeds: verified news.mit.edu school RSS + official footer socials +
# keyword-filtered school events (the Sloan pattern). The College of Computing
# has no /rss/school feed (404, verified); its closest official feed is the
# computing topic feed.
_CONTENT_RESEARCH: dict[str, dict] = {
    _ENG: {
        "news_rss": "https://news.mit.edu/rss/school/engineering",
        "news_curated": True,
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=engineering",
            "type": "ical",
        },
        "keywords": [],
        "social": {
            "instagram": "https://www.instagram.com/mit_engineering/",
            "linkedin": "https://www.linkedin.com/school/mit-school-of-engineering/",
            "x": "https://x.com/MITEngineering",
            "youtube": "https://www.youtube.com/channel/UCx-Pk4CGqEb0FO5A6RyRNxA",
            "facebook": "https://www.facebook.com/MITSchoolofEngineering/",
        },
    },
    _SCI: {
        "news_rss": "https://news.mit.edu/rss/school/science",
        "news_curated": True,
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=science",
            "type": "ical",
        },
        "keywords": [],
        "social": {
            "instagram": "https://www.instagram.com/mitscience/",
            "linkedin": "https://www.linkedin.com/company/mitschoolofscience/",
            "x": "https://twitter.com/sciencemit",
        },
    },
    _SHASS: {
        "news_rss": "https://news.mit.edu/rss/school/humanities-arts-and-social-sciences",
        "news_curated": True,
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=humanities",
            "type": "ical",
        },
        "keywords": [],
        "social": {
            "instagram": "https://www.instagram.com/mitshass",
            "linkedin": "https://www.linkedin.com/company/mit-shass",
            "x": "https://x.com/MIT_SHASS",
            "youtube": "https://www.youtube.com/@MITSHASS",
            "facebook": "https://www.facebook.com/MIT.SHASS",
        },
    },
    _SAP: {
        "news_rss": "https://news.mit.edu/rss/school/architecture-and-planning",
        "news_curated": True,
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=architecture",
            "type": "ical",
        },
        "keywords": [],
        "social": {
            "instagram": "https://instagram.com/mitsap",
            "linkedin": "https://www.linkedin.com/company/mitsap/",
            "x": "https://twitter.com/mitsap",
            "youtube": "https://www.youtube.com/user/mitsapcomm",
            "facebook": "https://www.facebook.com/sapmit",
        },
    },
    _COMPUTING: {
        "news_rss": "https://news.mit.edu/rss/topic/computing",
        "news_curated": True,
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=computing",
            "type": "ical",
        },
        "keywords": [],
        "social": {
            "instagram": "https://www.instagram.com/mitcomputing/",
            "linkedin": "https://www.linkedin.com/company/mit-schwarzman-college/",
            "x": "https://twitter.com/MIT_SCC",
            "facebook": "https://www.facebook.com/MITSCC",
        },
    },
}
_CONTENT_BY_SCHOOL.update(_CONTENT_RESEARCH)

# Lab/center links surfaced by the school About research — merged into the
# institution's research.lab_links so every named center keeps its official URL.
_SCHOOL_LAB_LINKS: dict[str, str] = {
    "Abdul Latif Jameel Clinic for Machine Learning in Health (Jameel Clinic)": (
        "https://www.jclinic.mit.edu/"
    ),
    "Abdul Latif Jameel Poverty Action Lab (J-PAL)": "https://www.povertyactionlab.org/",
    "Center for International Studies": "https://cis.mit.edu/",
    "Center for Sustainability Science and Strategy": "https://cs3.mit.edu/",
    "Center for Transportation and Logistics": "https://ctl.mit.edu/",
    "Computer Science and Artificial Intelligence Laboratory (CSAIL)": "https://www.csail.mit.edu/",
    "Institute for Data, Systems, and Society (IDSS)": "https://idss.mit.edu/research/",
    "Institute for Medical Engineering and Science": "https://imes.mit.edu/research",
    "Knight Science Journalism @MIT": "https://ksj.mit.edu/",
    "Laboratory for Information and Decision Systems (LIDS)": "https://lids.mit.edu/",
    "Laboratory for Nuclear Science": "http://web.mit.edu/lns",
    "MIT Center for Real Estate": "https://mitcre.mit.edu/",
    "MIT D-Lab": "https://d-lab.mit.edu/",
    "MIT Kavli Institute for Astrophysics and Space Research": "http://space.mit.edu/",
    "MIT Media Lab": "https://www.media.mit.edu/",
    "MIT Morningside Academy for Design": "https://design.mit.edu",
    "MIT Security Studies Program": "https://ssp.mit.edu/",
    "MIT Siegel Family Quest for Intelligence": "https://quest.mit.edu/",
    "MIT-IBM Watson AI Lab": "https://mitibm.mit.edu/",
    "MIT.nano": "https://mitnano.mit.edu/",
    "Materials Research Laboratory": "https://mrl.mit.edu/",
    "McGovern Institute for Brain Research": "http://mcgovern.mit.edu",
    "Microsystems Technology Laboratories": "https://www.mtl.mit.edu",
    "Norman B. Leventhal Center for Advanced Urbanism": "https://lcau.mit.edu",
    "Program in Art, Culture and Technology": "http://act.mit.edu/",
    "Research Laboratory of Electronics": "https://www.rle.mit.edu/",
    "Sociotechnical Systems Research Center": "https://ssrc.mit.edu/",
    "The Picower Institute for Learning and Memory": "http://picower.mit.edu/",
}

# External reviews — each synthesized from >=2 independent authoritative
# sources (distinct domains), strengths AND cautions, cited per entry.
_REVIEWS_RESEARCH: dict[str, dict] = {
    "mit-aeroastro-bs": {
        "summary": (
            "MIT AeroAstro (Course 16) is ranked No. 1 in the U.S. News undergraduate "
            "aerospace/aeronautical/astronautical engineering specialty for 2025-26, and QS's "
            "2026 mechanical-aeronautical-manufacturing subject ranking — which covers aerospace "
            "— also puts MIT first in the world with perfect reputation scores. Reviewers "
            "highlight the department's hands-on capstone build culture, NASA/SpaceX-caliber "
            "placement, and labs spanning autonomy, propulsion, and space systems. Cautions: "
            "Course 16's unified engineering core is one of MIT's most notoriously demanding "
            "sequences, and the aerospace job market is cyclical and concentrated among a handful"
            " of employers."
        ),
        "themes": [
            {
                "label": "No. 1 undergrad aerospace (U.S. News)",
                "sentiment": "positive",
                "detail": (
                    "First in the U.S. News 2025-26 undergraduate aerospace engineering specialty"
                    " ranking."
                ),
            },
            {
                "label": "No. 1 globally (QS subject)",
                "sentiment": "positive",
                "detail": (
                    "QS 2026 ranks MIT first worldwide in mechanical, aeronautical & "
                    "manufacturing engineering."
                ),
            },
            {
                "label": "Hands-on systems culture",
                "sentiment": "positive",
                "detail": (
                    "Build-fly capstones and labs in autonomy, propulsion, and space systems with"
                    " top-tier employer pull."
                ),
            },
            {
                "label": "'Unified' core is brutal",
                "sentiment": "caution",
                "detail": (
                    "Course 16's unified engineering sequence is famous Institute-wide for its "
                    "difficulty."
                ),
            },
            {
                "label": "Cyclical industry",
                "sentiment": "caution",
                "detail": (
                    "Aerospace hiring is concentrated and cyclical compared with software or "
                    "finance outcomes."
                ),
            },
        ],
        "sources": [
            {
                "label": (
                    "U.S. News — 2026 Best Undergraduate Aerospace Engineering Programs (MIT No. "
                    "1)"
                ),
                "url": (
                    "https://www.usnews.com/best-colleges/rankings/engineering-doctorate-aerospac"
                    "e-aeronautical-astronautical"
                ),
            },
            {
                "label": (
                    "QS / TopUniversities — Mechanical, Aeronautical & Manufacturing Engineering "
                    "2026 (MIT No. 1)"
                ),
                "url": (
                    "https://www.topuniversities.com/university-subject-rankings/mechanical-aeron"
                    "autical-manufacturing-engineering"
                ),
            },
            {
                "label": (
                    "MIT News — U.S. News 2025-26: MIT first in aerospace among undergrad "
                    "engineering specialties"
                ),
                "url": "https://news.mit.edu/2025/mit-named-no-2-university-us-news-2025-26-0923",
            },
        ],
    },
    "mit-architecture-march": {
        "summary": (
            "MIT's professional MArch sits inside a school ranked No. 2 in the world for "
            "Architecture & Built Environment by QS 2026, and before the DesignIntelligence "
            "survey was suspended in 2022 the program was consistently ranked among the top five "
            "US graduate architecture programs; Black Spectacles' program guide also notes one of"
            " the country's highest ARE pass rates (~75%). Reviewers praise its research-driven, "
            "computation- and fabrication-forward approach versus more form-driven peers like "
            "GSD. Cautions: the DI ranking that once benchmarked MArch programs no longer exists "
            "(deans criticized its rigor before suspension), studio culture is famously "
            "consuming, and the degree carries elite-private cost over 3.5 years."
        ),
        "themes": [
            {
                "label": "No. 2 worldwide (QS)",
                "sentiment": "positive",
                "detail": "QS 2026 ranks MIT second globally in Architecture & Built Environment.",
            },
            {
                "label": "Top-five US standing (DI era)",
                "sentiment": "positive",
                "detail": (
                    "Ranked among the top five US graduate architecture programs in the final "
                    "DesignIntelligence surveys."
                ),
            },
            {
                "label": "Licensure outcomes",
                "sentiment": "positive",
                "detail": (
                    "Black Spectacles cites one of the highest ARE pass rates in the country "
                    "(~75%)."
                ),
            },
            {
                "label": "Ranking landscape caveat",
                "sentiment": "caution",
                "detail": (
                    "DesignIntelligence was suspended in 2022 after deans criticized its rigor, "
                    "so current head-to-head MArch rankings are limited."
                ),
            },
            {
                "label": "Studio intensity and cost",
                "sentiment": "caution",
                "detail": (
                    "All-consuming studio culture across a 3.5-year professional degree at "
                    "elite-private tuition levels."
                ),
            },
        ],
        "sources": [
            {
                "label": (
                    "QS / TopUniversities — Architecture & Built Environment 2026 (MIT No. 2 "
                    "worldwide)"
                ),
                "url": (
                    "https://www.topuniversities.com/university-subject-rankings/architecture-bui"
                    "lt-environment"
                ),
            },
            {
                "label": (
                    "Black Spectacles — 'Top 10 Best Masters of Architecture (M.Arch) Programs in"
                    " the US' (MIT QS No. 2; ~75% ARE pass rate; DI suspension context)"
                ),
                "url": (
                    "https://www.blackspectacles.com/blog/top-10-masters-of-architecture-programs"
                    "-in-the-us"
                ),
            },
            {
                "label": (
                    "ArchDaily — QS 2026 architecture rankings coverage (MIT placement) and BAM "
                    "ranking of MIT SMArchS programs"
                ),
                "url": (
                    "https://www.archdaily.com/1040066/discover-the-top-universities-for-architec"
                    "ture-and-the-built-environment-in-2026-according-to-qs-rankings"
                ),
            },
            {
                "label": (
                    "MIT News — DesignIntelligence ranked MIT's graduate architecture program "
                    "among top in nation (pre-suspension)"
                ),
                "url": (
                    "https://news.mit.edu/2017/designintelligence-ranks-mit-graduate-architecture"
                    "-program-among-best-in-nation-0929"
                ),
            },
        ],
    },
    "mit-biology-bs": {
        "summary": (
            "MIT Biology (Course 7) ranks No. 2 in the world in QS Biological Sciences 2026, and "
            "Times Higher Education lists MIT among the very best US universities for "
            "life-science degrees in its 2026 guide; the department is consistently described as "
            "a powerhouse for molecular biology, genetics, and biomedical research via the Broad,"
            " Whitehead, and Koch institutes. Reviewers praise undergraduate research access "
            "(UROP) and the quantitative, mechanism-focused curriculum. Cautions: MIT-wide "
            "student reviews describe a workaholic intensity that hits premeds especially hard, "
            "and biology at MIT is more quantitative and research-oriented than at peer schools —"
            " a mismatch for students wanting a classic premed track."
        ),
        "themes": [
            {
                "label": "Top-tier global rankings",
                "sentiment": "positive",
                "detail": (
                    "No. 2 in QS Biological Sciences 2026; among THE's best US universities for "
                    "life-science degrees 2026."
                ),
            },
            {
                "label": "Institute ecosystem",
                "sentiment": "positive",
                "detail": (
                    "Broad, Whitehead, Koch, and Picower institutes give undergrads frontier "
                    "research placements."
                ),
            },
            {
                "label": "Quantitative curriculum",
                "sentiment": "positive",
                "detail": (
                    "Mechanism- and data-driven teaching distinguishes Course 7 from descriptive "
                    "biology programs."
                ),
            },
            {
                "label": "Intensity, especially for premeds",
                "sentiment": "caution",
                "detail": (
                    "Niche reviews of MIT describe overwhelming rigor; GPA pressure is a real "
                    "concern for med-school-bound students."
                ),
            },
        ],
        "sources": [
            {
                "label": "QS / TopUniversities — Biological Sciences 2026 (MIT No. 2 worldwide)",
                "url": (
                    "https://www.topuniversities.com/university-subject-rankings/biological-scien"
                    "ces"
                ),
            },
            {
                "label": (
                    "Times Higher Education — Best universities for life sciences degrees in the "
                    "US 2026 (MIT among the top)"
                ),
                "url": (
                    "https://www.timeshighereducation.com/student/best-universities/best-universi"
                    "ties-life-science-degrees-us"
                ),
            },
            {
                "label": "Niche — MIT reviews (workload/intensity caution)",
                "url": (
                    "https://www.niche.com/colleges/massachusetts-institute-of-technology/reviews"
                    "/"
                ),
            },
        ],
    },
    "mit-cheme-bs": {
        "summary": (
            "MIT Chemical Engineering (Course 10) has been ranked No. 1 in the world by QS for 14"
            " straight years through 2026, and U.S. News places MIT first in chemical engineering"
            " among its undergraduate engineering specialties; trade press (The Chemical "
            "Engineer) has covered MIT's sustained hold on the top spot. Reviewers credit the "
            "department's practice-oriented options (including the 10-ENG flexible degree), "
            "faculty depth, and pipelines into energy, pharma, and biotech. The cautions echo "
            "across reviews: Course 10 is regarded as one of MIT's heaviest workloads — the core "
            "transport/thermo sequence is notoriously hard — within an already intense Institute "
            "culture."
        ),
        "themes": [
            {
                "label": "14 straight years No. 1 (QS)",
                "sentiment": "positive",
                "detail": (
                    "QS has ranked MIT ChemE first in the world every year for 14 years through "
                    "2026."
                ),
            },
            {
                "label": "No. 1 in U.S. News",
                "sentiment": "positive",
                "detail": (
                    "U.S. News ranks MIT first in undergraduate chemical engineering among "
                    "engineering specialties."
                ),
            },
            {
                "label": "Industry breadth",
                "sentiment": "positive",
                "detail": (
                    "Strong placement across energy, pharmaceuticals, biotech, and consulting."
                ),
            },
            {
                "label": "One of MIT's hardest majors",
                "sentiment": "caution",
                "detail": (
                    "The Course 10 core is widely described as among the most punishing sequences"
                    " at an already demanding school."
                ),
            },
        ],
        "sources": [
            {
                "label": "QS / TopUniversities — Chemical Engineering 2026 (MIT No. 1 worldwide)",
                "url": (
                    "https://www.topuniversities.com/university-subject-rankings/chemical-enginee"
                    "ring"
                ),
            },
            {
                "label": (
                    "The Chemical Engineer — 'MIT retains top university ranking for chemical "
                    "engineering'"
                ),
                "url": (
                    "https://www.thechemicalengineer.com/news/mit-retains-top-university-ranking-"
                    "for-chemical-engineering/"
                ),
            },
            {
                "label": (
                    "MIT News — U.S. News 2025-26: MIT first in five undergrad engineering "
                    "specialties incl. chemical"
                ),
                "url": "https://news.mit.edu/2025/mit-named-no-2-university-us-news-2025-26-0923",
            },
        ],
    },
    "mit-city-planning-sm": {
        "summary": (
            "MIT DUSP's Master in City Planning is one of the two most decorated planning degrees"
            " in North America: Planetizen's guide ranked DUSP No. 1 for multiple editions, and "
            "in the most recent (7th edition, 2023) MIT placed No. 2 behind UCLA — while leading "
            "individual specialties such as international development, housing/community "
            "development, economic development, and planning technology in earlier editions. QS "
            "2026 also ranks MIT No. 2 worldwide in Architecture & Built Environment, the subject"
            " family covering planning. Cautions: MIT no longer holds the undisputed No. 1 spot "
            "in the latest Planetizen edition, the two-year professional degree carries "
            "elite-private tuition, and the program's technology/development orientation suits "
            "some planning career paths better than traditional municipal practice."
        ),
        "themes": [
            {
                "label": "Perennial Planetizen leader",
                "sentiment": "positive",
                "detail": (
                    "Ranked No. 1 in multiple editions of Planetizen's planning-school guide; No."
                    " 2 behind UCLA in the 2023 7th edition."
                ),
            },
            {
                "label": "Specialty dominance",
                "sentiment": "positive",
                "detail": (
                    "Planetizen rated DUSP No. 1 in international development, housing/community "
                    "development, economic development, and technology."
                ),
            },
            {
                "label": "No. 2 worldwide QS subject family",
                "sentiment": "positive",
                "detail": (
                    "QS 2026 Architecture & Built Environment (which covers planning) ranks MIT "
                    "second globally."
                ),
            },
            {
                "label": "No longer undisputed No. 1",
                "sentiment": "caution",
                "detail": (
                    "UCLA took Planetizen's top spot in the latest edition — claims of "
                    "'consistently #1' need that qualifier."
                ),
            },
            {
                "label": "Cost and orientation",
                "sentiment": "caution",
                "detail": (
                    "Elite-private tuition for a public-interest field; the tech/development bent"
                    " fits some planning careers better than others."
                ),
            },
        ],
        "sources": [
            {
                "label": (
                    "Planetizen — Top Schools for Urban Planners (DUSP No. 1 in prior editions; "
                    "No. 2 behind UCLA in 7th edition, 2023)"
                ),
                "url": "https://www.planetizen.com/topschools",
            },
            {
                "label": "Planetizen — MIT Master in City Planning program directory entry",
                "url": "https://www.planetizen.com/schools/mit-mcp",
            },
            {
                "label": (
                    "QS / TopUniversities — Architecture & Built Environment 2026 (MIT No. 2 "
                    "worldwide)"
                ),
                "url": (
                    "https://www.topuniversities.com/university-subject-rankings/architecture-bui"
                    "lt-environment"
                ),
            },
        ],
    },
    "mit-cs-6-3-bs": {
        "summary": (
            "Course 6-3 (Computer Science and Engineering) is the flagship CS track within MIT "
            "EECS, and external reviews of MIT computer science apply directly: U.S. News ranks "
            "MIT No. 1 for undergraduate computer science in 2025-26, leading in four of ten CS "
            "specialty disciplines, ahead of a top five rounded out by Carnegie Mellon, Stanford,"
            " Berkeley, Princeton, and Georgia Tech. Niche rates MIT A+ overall with strongly "
            "positive student reviews of the academics and peer quality. Cautions mirror the "
            "broader Institute: reviewers describe an intense, workaholic culture, and 6-3's "
            "popularity makes it MIT's most crowded major, with heavy psets and competitive "
            "recruiting pipelines."
        ),
        "themes": [
            {
                "label": "No. 1 in U.S. News undergrad CS",
                "sentiment": "positive",
                "detail": (
                    "MIT tops the 2025-26 U.S. News undergraduate CS ranking and leads four of "
                    "ten CS specialty areas."
                ),
            },
            {
                "label": "Flexible, theory-plus-systems curriculum",
                "sentiment": "positive",
                "detail": (
                    "6-3 combines rigorous theory with systems and AI coursework inside the "
                    "top-ranked EECS department."
                ),
            },
            {
                "label": "Elite outcomes",
                "sentiment": "positive",
                "detail": (
                    "Graduates feed top software, AI, and quant employers as well as top PhD "
                    "programs."
                ),
            },
            {
                "label": "Intensity and crowding",
                "sentiment": "caution",
                "detail": (
                    "Niche reviews flag overwhelming rigor; 6-3 is MIT's most popular major, so "
                    "core classes are large."
                ),
            },
        ],
        "sources": [
            {
                "label": (
                    "U.S. News — Best Undergraduate Computer Science Programs (MIT No. 1, "
                    "2025-26)"
                ),
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
            {
                "label": (
                    "MIT News — U.S. News 2025-26 results (undergrad CS No. 1; No. 1 in 4 of 10 "
                    "CS disciplines)"
                ),
                "url": "https://news.mit.edu/2025/mit-named-no-2-university-us-news-2025-26-0923",
            },
            {
                "label": "Niche — MIT reviews (A+ grade; rigor and work-life-balance cautions)",
                "url": (
                    "https://www.niche.com/colleges/massachusetts-institute-of-technology/reviews"
                    "/"
                ),
            },
        ],
    },
    "mit-economics-phd": {
        "summary": (
            "MIT's economics PhD is tied for No. 1 in the U.S. News economics rankings (with "
            "Harvard, Stanford, Berkeley, and Chicago) and ranks No. 2 worldwide in QS Economics "
            "& Econometrics 2026, just behind Harvard; RePEc's citation-based department rankings"
            " also keep MIT in the global top handful. Reviewers consistently describe it as one "
            "of the two or three most influential economics departments — home to a long line of "
            "Nobel laureates and dominant in development, micro theory, and econometrics. The "
            "cautions are stark selectivity (one of the smallest, most competitive PhD admits in "
            "the field) and the well-known intensity of its first-year sequence."
        ),
        "themes": [
            {
                "label": "Tied No. 1 in U.S. News",
                "sentiment": "positive",
                "detail": (
                    "U.S. News economics rankings place MIT in a first-place tie with Harvard, "
                    "Stanford, Berkeley, and Chicago."
                ),
            },
            {
                "label": "No. 2 globally in QS 2026",
                "sentiment": "positive",
                "detail": (
                    "QS Economics & Econometrics 2026 ranks MIT second worldwide behind Harvard."
                ),
            },
            {
                "label": "Placement power",
                "sentiment": "positive",
                "detail": (
                    "Graduates routinely place at top-five departments, the Fed, and leading "
                    "policy institutions."
                ),
            },
            {
                "label": "Brutal selectivity",
                "sentiment": "caution",
                "detail": (
                    "One of the most competitive PhD admits in any field; a typical cohort is "
                    "small relative to applicant volume."
                ),
            },
            {
                "label": "First-year intensity",
                "sentiment": "caution",
                "detail": (
                    "The core micro/macro/econometrics sequence is widely regarded as among the "
                    "most demanding anywhere."
                ),
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Best Economics Programs (MIT tied No. 1)",
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-humanities-schools/economic"
                    "s-rankings"
                ),
            },
            {
                "label": (
                    "QS / TopUniversities — Economics & Econometrics 2026 (MIT No. 2, behind "
                    "Harvard)"
                ),
                "url": (
                    "https://www.topuniversities.com/university-subject-rankings/economics-econom"
                    "etrics"
                ),
            },
            {
                "label": (
                    "IDEAS/RePEc — Top economics departments (citation-based; MIT in global top "
                    "tier, May 2026)"
                ),
                "url": "https://ideas.repec.org/top/top.econdept.html",
            },
        ],
    },
    "mit-eecs-bs": {
        "summary": (
            "MIT's EECS (Course 6) is the largest undergraduate program at MIT and sits at the "
            "top of national rankings: U.S. News placed MIT No. 1 for undergraduate computer "
            "science in its 2025-26 edition (No. 1 in four of ten CS specialty areas), and its "
            "undergraduate engineering program is also ranked No. 1. Niche gives MIT an overall "
            "A+ grade with a 4.2/5 student-review average, with reviewers praising peers and "
            "research access. The consistent caution across student reviews is the workload: "
            "Niche reviewers describe the rigor as overwhelming for some and a 'workaholic' "
            "culture where work-life balance is a real challenge, and intro EECS classes are "
            "famously demanding."
        ),
        "themes": [
            {
                "label": "No. 1 ranked CS and engineering",
                "sentiment": "positive",
                "detail": (
                    "U.S. News 2025-26 ranks MIT No. 1 for undergraduate computer science and No."
                    " 1 in undergraduate engineering."
                ),
            },
            {
                "label": "Research and industry access",
                "sentiment": "positive",
                "detail": (
                    "UROP research placements and the CSAIL ecosystem give undergrads unusual "
                    "access to frontier work."
                ),
            },
            {
                "label": "Exceptional peer group",
                "sentiment": "positive",
                "detail": (
                    "Niche reviewers consistently cite brilliant classmates as a defining "
                    "strength (A+ overall grade, 4.2/5)."
                ),
            },
            {
                "label": "Punishing workload",
                "sentiment": "caution",
                "detail": (
                    "Niche student reviews describe a workaholic culture where the rigor can be "
                    "'manageable or impossible' depending on the person."
                ),
            },
            {
                "label": "Scale of the major",
                "sentiment": "caution",
                "detail": (
                    "Course 6 is MIT's biggest major, so some core classes are large and "
                    "competition for popular labs is real."
                ),
            },
        ],
        "sources": [
            {
                "label": (
                    "U.S. News — Best Undergraduate Computer Science Programs (MIT No. 1, "
                    "2025-26; reported by MIT News)"
                ),
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
            {
                "label": (
                    "MIT News — 'MIT named No. 2 university by U.S. News for 2025-26' (undergrad "
                    "CS and engineering No. 1)"
                ),
                "url": "https://news.mit.edu/2025/mit-named-no-2-university-us-news-2025-26-0923",
            },
            {
                "label": (
                    "Niche — MIT reviews (A+ overall, 4.2/5 from 678 reviews; workload and "
                    "culture cautions)"
                ),
                "url": (
                    "https://www.niche.com/colleges/massachusetts-institute-of-technology/reviews"
                    "/"
                ),
            },
        ],
    },
    "mit-math-bs": {
        "summary": (
            "MIT Mathematics (Course 18) ranks No. 1 in both the QS World University Rankings by "
            "Subject and the U.S. News mathematics rankings — a dual No. 1 the department itself "
            "has highlighted — with a faculty of roughly 50 that includes Abel Prize and National"
            " Medal of Science winners. Reviewers consistently cite the depth of the course "
            "catalog, the Putnam-winning student culture, and pipelines into both academia and "
            "quantitative finance. The caution is competitive intensity: Course 18 attracts "
            "olympiad-level students, so the curve and culture can feel daunting, and MIT-wide "
            "reviews flag a heavy, stress-inducing workload."
        ),
        "themes": [
            {
                "label": "Dual No. 1 ranking",
                "sentiment": "positive",
                "detail": (
                    "No. 1 in QS Mathematics by Subject and No. 1 in U.S. News mathematics "
                    "rankings."
                ),
            },
            {
                "label": "Decorated faculty",
                "sentiment": "positive",
                "detail": (
                    "Roughly 50 faculty holding Abel Prizes, National Medals of Science, and "
                    "Simons Investigator awards."
                ),
            },
            {
                "label": "Dual academia/industry outcomes",
                "sentiment": "positive",
                "detail": "Strong placement into top PhD programs and quant finance alike.",
            },
            {
                "label": "Olympiad-level peer competition",
                "sentiment": "caution",
                "detail": (
                    "The concentration of contest-math talent can be intimidating, and the "
                    "workload is intense."
                ),
            },
        ],
        "sources": [
            {
                "label": "QS / TopUniversities — Mathematics 2026 (MIT No. 1)",
                "url": "https://www.topuniversities.com/university-subject-rankings/mathematics",
            },
            {
                "label": "U.S. News — Best Mathematics Programs (MIT No. 1)",
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-science-schools/mathematics"
                    "-rankings"
                ),
            },
            {
                "label": (
                    "MIT Math department — 'MIT Math #1 by QS World and US News' (corroborating "
                    "both rankings)"
                ),
                "url": "https://math.mit.edu/news/spotlight/archive/2022/2022_04_05_ranking.html",
            },
        ],
    },
    "mit-meche-bs": {
        "summary": (
            "MIT Mechanical Engineering (Course 2) is ranked No. 1 in the world for mechanical, "
            "aeronautical and manufacturing engineering by QS for 2026 — with perfect scores for "
            "academic and employer reputation, ahead of Stanford — and U.S. News places MIT first"
            " in undergraduate mechanical engineering among its 2025-26 engineering specialties. "
            "Reviewers highlight the hands-on, design-and-build culture (2.007 robot competition,"
            " maker spaces) and strong employer pull. The consistent caution is the same as "
            "MIT-wide reviews: a heavy pset-and-lab workload that Niche reviewers describe as "
            "overwhelming for some, plus a demanding core sequence."
        ),
        "themes": [
            {
                "label": "No. 1 in QS and U.S. News",
                "sentiment": "positive",
                "detail": (
                    "QS 2026 ranks MIT No. 1 globally for mechanical/aero/manufacturing "
                    "engineering; U.S. News ranks it No. 1 for undergrad mechanical engineering."
                ),
            },
            {
                "label": "Hands-on design culture",
                "sentiment": "positive",
                "detail": (
                    "Signature build-and-compete classes and maker facilities are repeatedly "
                    "cited as a differentiator."
                ),
            },
            {
                "label": "Perfect reputation scores",
                "sentiment": "positive",
                "detail": (
                    "QS gives MIT MechE perfect academic-reputation and employer-reputation "
                    "scores."
                ),
            },
            {
                "label": "Heavy lab and pset load",
                "sentiment": "caution",
                "detail": (
                    "Student reviews describe the combined problem-set, lab, and project workload"
                    " as relentless."
                ),
            },
        ],
        "sources": [
            {
                "label": (
                    "QS / TopUniversities — Mechanical, Aeronautical & Manufacturing Engineering "
                    "2026 (MIT No. 1, perfect reputation scores)"
                ),
                "url": (
                    "https://www.topuniversities.com/university-subject-rankings/mechanical-aeron"
                    "autical-manufacturing-engineering"
                ),
            },
            {
                "label": (
                    "MIT News — U.S. News 2025-26: MIT first in five undergrad engineering "
                    "specialties incl. mechanical"
                ),
                "url": "https://news.mit.edu/2025/mit-named-no-2-university-us-news-2025-26-0923",
            },
            {
                "label": "Niche — MIT reviews (workload/intensity caution)",
                "url": (
                    "https://www.niche.com/colleges/massachusetts-institute-of-technology/reviews"
                    "/"
                ),
            },
        ],
    },
    "mit-mediaarts-sm": {
        "summary": (
            "The Media Lab's Media Arts & Sciences SM is a research-first, 'antidisciplinary' "
            "two-year master's: alumni reviewers emphasize that the Lab's brand recognition in "
            "industry is exceptional, that only five courses are required (freeing time for "
            "funded research), and that the cross-disciplinary cohort of roughly 40-50 admits per"
            " year spans CS to design to neuroscience. Because it doesn't map onto a conventional"
            " discipline, it isn't captured by U.S. News or QS subject rankings, so external "
            "signals come mainly from alumni and employee reviews. Those reviews carry a "
            "consistent caution: pressure to produce demos and publications is high, with "
            "reviewers on Indeed describing periods of little to no work-life balance, and "
            "outcomes depend heavily on which research group (and advisor) you join."
        ),
        "themes": [
            {
                "label": "Brand and industry pull",
                "sentiment": "positive",
                "detail": (
                    "Alumni reviewers report the 30+-year-old Media Lab brand carries significant"
                    " recognition with employers."
                ),
            },
            {
                "label": "Research-first structure",
                "sentiment": "positive",
                "detail": (
                    "Only five required courses; students are funded RAs spending most time on "
                    "group research."
                ),
            },
            {
                "label": "Antidisciplinary breadth",
                "sentiment": "positive",
                "detail": (
                    "Cohorts of ~40-50 mix engineering, design, music, neuroscience — work hard "
                    "to do in a traditional department."
                ),
            },
            {
                "label": "High pressure, uneven balance",
                "sentiment": "caution",
                "detail": (
                    "Indeed reviewers describe relentless pressure to perform and stretches with "
                    "no work-life balance."
                ),
            },
            {
                "label": "Advisor-dependent experience",
                "sentiment": "caution",
                "detail": (
                    "No conventional subject ranking covers MAS; quality of experience and "
                    "outcomes hinge on the research group."
                ),
            },
        ],
        "sources": [
            {
                "label": (
                    "Tiffany Tseng (Media Lab alumna, Medium) — 'Applying to the MIT Media Lab': "
                    "brand recognition, 5-course requirement, multidisciplinary research "
                    "structure"
                ),
                "url": "https://scientiffic.medium.com/applying-to-the-mit-media-lab-c158b6ef8d78",
            },
            {
                "label": (
                    "Indeed — MIT Media Lab employee/researcher reviews: best-in-class technical "
                    "environment but high pressure and poor work-life balance at times"
                ),
                "url": "https://www.indeed.com/cmp/MIT-Media-Lab/reviews",
            },
            {
                "label": (
                    "MIT Media Lab — MAS program structure (two-year SM, ~40-50 admits/year "
                    "across master's and PhD)"
                ),
                "url": "https://www.media.mit.edu/posts/mas-degree-and-course-requirements/",
            },
        ],
    },
    "mit-physics-bs": {
        "summary": (
            "MIT Physics is ranked the world's No. 1 physics & astronomy program by QS for 2026 —"
            " with perfect scores on three of five indicators, ahead of Harvard and Oxford — and "
            "U.S. News likewise places MIT at No. 1 for physics, citing strength across quantum "
            "physics, astrophysics, and nuclear physics. Reviewers consistently note the "
            "department's research breadth (LIGO, quantum information, Kavli astrophysics) and "
            "the unusually research-active undergraduate path. The standing caution is "
            "difficulty: Course 8 is regarded as one of MIT's most demanding majors, and student "
            "reviews of MIT broadly warn that the pace and rigor can overwhelm work-life balance."
        ),
        "themes": [
            {
                "label": "No. 1 in QS and U.S. News",
                "sentiment": "positive",
                "detail": (
                    "QS 2026 ranks MIT No. 1 globally in physics & astronomy; U.S. News also "
                    "places MIT physics at No. 1."
                ),
            },
            {
                "label": "Frontier research access",
                "sentiment": "positive",
                "detail": (
                    "Undergrads work in world-leading groups across quantum, astrophysics, and "
                    "nuclear/particle physics."
                ),
            },
            {
                "label": "Graduate-school pipeline",
                "sentiment": "positive",
                "detail": (
                    "QS's graduate-employment and research-quality indicators score MIT physics "
                    "at or near perfect."
                ),
            },
            {
                "label": "Among MIT's hardest majors",
                "sentiment": "caution",
                "detail": (
                    "The theory-heavy sequence is famously demanding; reviewers warn the rigor is"
                    " not for everyone."
                ),
            },
        ],
        "sources": [
            {
                "label": (
                    "QS / TopUniversities — Physics & Astronomy 2026 (MIT No. 1, perfect score on"
                    " 3 of 5 indicators)"
                ),
                "url": (
                    "https://www.topuniversities.com/university-subject-rankings/physics-astronom"
                    "y"
                ),
            },
            {
                "label": "U.S. News — Best Physics Programs (MIT No. 1)",
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-science-schools/physics-ran"
                    "kings"
                ),
            },
            {
                "label": "Niche — MIT reviews (rigor caution)",
                "url": (
                    "https://www.niche.com/colleges/massachusetts-institute-of-technology/reviews"
                    "/"
                ),
            },
        ],
    },
    "mit-sloan-fellows-mba": {
        "summary": (
            "The MIT Sloan Fellows MBA is a 12-month, full-time residential program for "
            "accomplished mid-career leaders — Poets&Quants calls the Sloan Fellows degree 'an "
            "elite mid-career degree' offered at only three world-class schools (MIT, Stanford, "
            "LBS), with cohorts of roughly 100-110 students averaging about 15 years of work "
            "experience and heavy international representation. Clear Admit's program profile "
            "confirms the 10+-years-experience bar and the June start with leadership assessment "
            "and executive coaching. The cautions reviewers raise: it is quick, intense, and "
            "highly selective; tuition alone runs over $156K for the year (2025-26) before living"
            " costs and foregone salary; and unlike the flagship MBA it is not separately ranked,"
            " so its value rests on the MIT brand and network rather than league tables."
        ),
        "themes": [
            {
                "label": "Elite mid-career niche",
                "sentiment": "positive",
                "detail": (
                    "Poets&Quants: one of only three Sloan Fellows programs worldwide (MIT, "
                    "Stanford, LBS), highly selective."
                ),
            },
            {
                "label": "Seasoned global cohort",
                "sentiment": "positive",
                "detail": (
                    "~100-110 fellows averaging 15 years' experience, with 70%+ international "
                    "students from 40+ countries."
                ),
            },
            {
                "label": "Leadership-focused design",
                "sentiment": "positive",
                "detail": (
                    "June start with 360-degree leadership assessment, executive coaching, and a "
                    "compressed full MBA core."
                ),
            },
            {
                "label": "Cost and opportunity cost",
                "sentiment": "caution",
                "detail": (
                    "Tuition exceeds $156K for 2025-26, plus Cambridge living costs and a year "
                    "out of a senior-level salary."
                ),
            },
            {
                "label": "Pace and ranking opacity",
                "sentiment": "caution",
                "detail": (
                    "The 12-month format is intense, and the program isn't covered by standard "
                    "MBA rankings."
                ),
            },
        ],
        "sources": [
            {
                "label": (
                    "Poets&Quants — 'Sloan Fellows: An Elite Mid-Career Degree At 3 World Class "
                    "B-Schools' (quick, intense, highly selective; ~15 yrs avg experience)"
                ),
                "url": (
                    "https://poetsandquants.com/2023/01/20/sloan-fellows-an-elite-mid-career-degr"
                    "ee-at-3-world-class-b-schools/"
                ),
            },
            {
                "label": (
                    "Clear Admit — MIT Sloan Fellows Program profile (10+ years experience "
                    "requirement, structure, June start)"
                ),
                "url": (
                    "https://www.clearadmit.com/schools/mit-sloan/program/mit-sloan-fellows-progr"
                    "am/"
                ),
            },
            {
                "label": (
                    "MIT Sloan — Sloan Fellows tuition & financial aid (2025-26 tuition $156,574)"
                ),
                "url": (
                    "https://mitsloan.mit.edu/mit-sloan-fellows-mba/admissions/tuition-expenses-a"
                    "nd-financial-aid"
                ),
            },
        ],
    },
    "mit-sloan-mba": {
        "summary": (
            "MIT Sloan's full-time MBA hit a historic high in 2026: U.S. News placed it in a tie "
            "for No. 1 with Wharton (released Sept 2025), and the Financial Times ranked it No. 1"
            " in the world for the first time in the FT ranking's 28-year history. Reviewers "
            "consistently credit its analytical, data-driven culture, action-learning labs, and "
            "deep integration with MIT's technology ecosystem. The trade-offs reviewers flag are "
            "extreme admissions competitiveness, an all-in cost well into six figures, and a "
            "quant-heavy, rigorous culture that suits analytically minded candidates more than "
            "those seeking a traditional general-management feel."
        ),
        "themes": [
            {
                "label": "Top-of-market rankings",
                "sentiment": "positive",
                "detail": (
                    "Tied No. 1 in U.S. News 2026 Best Business Schools and No. 1 in the FT "
                    "Global MBA Ranking 2026 — Sloan's first-ever FT top spot."
                ),
            },
            {
                "label": "Analytical, tech-integrated curriculum",
                "sentiment": "positive",
                "detail": (
                    "Data-driven, action-learning approach tightly coupled to MIT's engineering "
                    "and entrepreneurship ecosystem."
                ),
            },
            {
                "label": "Strong outcomes",
                "sentiment": "positive",
                "detail": (
                    "Consistently elite employment and salary results underpin its rankings climb"
                    " across U.S. News and FT methodologies."
                ),
            },
            {
                "label": "Competitiveness and cost",
                "sentiment": "caution",
                "detail": (
                    "Admissions are among the most selective of any MBA, and total cost of "
                    "attendance is well over $200K for the two years."
                ),
            },
            {
                "label": "Quant-heavy culture",
                "sentiment": "caution",
                "detail": (
                    "The rigorous, analytics-first style is a poor fit for candidates wanting a "
                    "softer, generalist MBA experience."
                ),
            },
        ],
        "sources": [
            {
                "label": (
                    "Poets&Quants (Sept 2025) — 'U.S. News 2026 Best Business Schools Ranking: "
                    "MIT Joins Wharton At The Top' (tie for No. 1)"
                ),
                "url": (
                    "https://poetsandquants.com/2025/09/23/u-s-news-2026-best-business-schools-ra"
                    "nking-mit-joins-wharton-at-the-top/"
                ),
            },
            {
                "label": (
                    "Poets&Quants (Feb 2026) — '2026 Financial Times MBA Ranking: MIT Tops List "
                    "For The First Time'"
                ),
                "url": (
                    "https://poetsandquants.com/2026/02/16/2026-financial-times-mba-ranking-mit-t"
                    "ops-list-for-the-first-time/"
                ),
            },
            {
                "label": "U.S. News — Best Business Schools (full-time MBA) rankings page",
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-business-schools/mba-rankin"
                    "gs"
                ),
            },
            {
                "label": (
                    "Stacy Blackman Consulting — 'Financial Times MBA Rankings 2026: MIT Sloan "
                    "Tops the World'"
                ),
                "url": "https://www.stacyblackman.com/blog/financial-times-mba-rankings/",
            },
        ],
    },
    "mit-sloan-mfin": {
        "summary": (
            "MIT Sloan's 18-month Master of Finance is rated the No. 1 master's-in-finance in "
            "North America and No. 3 worldwide in the QS Business Masters Rankings 2026, with QS "
            "scoring it near the top for employability and joint first (with Oxford Saïd) for "
            "thought leadership. QuantNet's 2026 data shows it is also one of the most selective "
            "quant-finance programs in the U.S., with an 8.3% acceptance rate and a 70.4% yield. "
            "Reviewers praise its quantitative rigor, STEM designation, and placement into quant "
            "finance, but caution that admissions are brutally selective, the program is intense "
            "and compressed, and European schools (HEC, Oxford) still edge it in QS's overall "
            "global table."
        ),
        "themes": [
            {
                "label": "Elite global ranking",
                "sentiment": "positive",
                "detail": (
                    "No. 3 worldwide and No. 1 in North America in QS Masters in Finance 2026."
                ),
            },
            {
                "label": "Employability and thought leadership",
                "sentiment": "positive",
                "detail": (
                    "QS 2026 places Sloan just behind Wharton on employability and joint first "
                    "globally for thought leadership."
                ),
            },
            {
                "label": "Quantitative rigor",
                "sentiment": "positive",
                "detail": (
                    "STEM-designated, quant-heavy curriculum feeding quant finance, asset "
                    "management, and fintech roles."
                ),
            },
            {
                "label": "Extreme selectivity",
                "sentiment": "caution",
                "detail": (
                    "QuantNet 2026 reports an 8.3% acceptance rate — among the top-10 most "
                    "selective quant programs in the U.S."
                ),
            },
            {
                "label": "Compressed intensity",
                "sentiment": "caution",
                "detail": (
                    "The 18-month format starting in summer is fast-paced and demanding, with "
                    "limited room to ramp up."
                ),
            },
        ],
        "sources": [
            {
                "label": (
                    "QS / TopUniversities — Business Masters Rankings 2026: Finance (MIT No. 3 "
                    "worldwide, No. 1 in North America)"
                ),
                "url": "https://www.topuniversities.com/business-masters-rankings/finance",
            },
            {
                "label": (
                    "QuantNet — 2026 Ranking of Best Financial Engineering Programs (MIT MFin: "
                    "8.3% acceptance, 70.4% yield, top-10 most selective)"
                ),
                "url": "https://quantnet.com/mfe-programs-rankings/",
            },
            {
                "label": (
                    "GMAC — analysis of the QS 2026 Masters in Finance ranking (Sloan near-top "
                    "employability; joint No. 1 thought leadership)"
                ),
                "url": (
                    "https://www.gmac.com/resources/learners/business-programs/explore-programs/b"
                    "est-master-in-finance-degree-qs-ranking"
                ),
            },
        ],
    },
}
_REVIEWS_BY_SLUG.update(_REVIEWS_RESEARCH)

# Class profiles — MIT Registrar enrollment statistics 2025-2026 (fall term;
# basis verbatim per entry: total enrolled majors, not entering class) and the
# official Sloan/SDM class-profile pages for cohort-based programs.
_CLASS_PROFILE_RESEARCH: dict[str, dict] = {
    "mit-eecs-bs": {
        "cohort_size": 159,
        "basis": (
            "total undergraduate majors enrolled in Course 6-2 (Electrical Engineering and "
            "Computer Science), fall term 2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-eecs-phd": {
        "cohort_size": 759,
        "basis": (
            "doctoral (regular) graduate students enrolled in Course 6 (Electrical Engineering "
            "and Computer Science), fall term 2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-meche-bs": {
        "cohort_size": 228,
        "basis": (
            "total undergraduate majors enrolled in Course 2 (Mechanical Engineering), fall term "
            "2025-2026 (total enrolled, not entering class; Course 2-A flexible track counted "
            "separately with 197)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-meche-phd": {
        "cohort_size": 246,
        "basis": (
            "doctoral (regular) graduate students enrolled in Course 2 (Mechanical Engineering), "
            "fall term 2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-aeroastro-bs": {
        "cohort_size": 132,
        "basis": (
            "total undergraduate majors enrolled in Course 16 (Aeronautics and Astronautics), "
            "fall term 2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-aeroastro-phd": {
        "cohort_size": 154,
        "basis": (
            "doctoral (regular) graduate students enrolled in Course 16 (Aeronautics and "
            "Astronautics), fall term 2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-cheme-bs": {
        "cohort_size": 40,
        "basis": (
            "total undergraduate majors enrolled in Course 10 (Chemical Engineering), fall term "
            "2025-2026 (total enrolled, not entering class; Course 10-B Chemical-Biological "
            "Engineering counted separately with 77)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-dmse-bs": {
        "cohort_size": 44,
        "basis": (
            "total undergraduate majors enrolled in Course 3 (Materials Science and Engineering),"
            " fall term 2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-be-bs": {
        "cohort_size": 116,
        "basis": (
            "total undergraduate majors enrolled in Course 20 (Biological Engineering), fall term"
            " 2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-cee-bs": {
        "cohort_size": 29,
        "basis": (
            "total undergraduate majors enrolled in Course 1-ENG (Civil and Environmental "
            "Engineering, flexible engineering degree — the department's undergraduate major), "
            "fall term 2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-nse-bs": {
        "cohort_size": 16,
        "basis": (
            "total undergraduate majors enrolled in Course 22 (Nuclear Science and Engineering), "
            "fall term 2025-2026 (total enrolled, not entering class; Course 22-ENG counted "
            "separately with 17)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-physics-bs": {
        "cohort_size": 173,
        "basis": (
            "total undergraduate majors enrolled in Course 8 (Physics), fall term 2025-2026 "
            "(total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-physics-phd": {
        "cohort_size": 281,
        "basis": (
            "doctoral (regular) graduate students enrolled in Course 8 (Physics), fall term "
            "2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-math-bs": {
        "cohort_size": 261,
        "basis": (
            "total undergraduate majors enrolled in Course 18 (Mathematics), fall term 2025-2026 "
            "(total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-math-phd": {
        "cohort_size": 129,
        "basis": (
            "doctoral (regular) graduate students enrolled in Course 18 (Mathematics), fall term "
            "2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-math-cs-bs": {
        "cohort_size": 84,
        "basis": (
            "total undergraduate majors enrolled in Course 18-C (Mathematics with Computer "
            "Science), fall term 2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-biology-bs": {
        "cohort_size": 36,
        "basis": (
            "total undergraduate majors enrolled in Course 7 (Biology), fall term 2025-2026 "
            "(total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-chemistry-bs": {
        "cohort_size": 28,
        "basis": (
            "total undergraduate majors enrolled in Course 5 (Chemistry), fall term 2025-2026 "
            "(total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-chemistry-phd": {
        "cohort_size": 275,
        "basis": (
            "doctoral (regular) graduate students enrolled in Course 5 (Chemistry), fall term "
            "2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-bcs-bs": {
        "cohort_size": 41,
        "basis": (
            "total undergraduate majors enrolled in Course 9 (Brain and Cognitive Sciences), fall"
            " term 2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-eaps-bs": {
        "cohort_size": 18,
        "basis": (
            "total undergraduate majors enrolled in Course 12 (Earth, Atmospheric, and Planetary "
            "Sciences), fall term 2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-economics-bs": {
        "cohort_size": 10,
        "basis": (
            "total undergraduate majors enrolled in Course 14-1 (Economics), fall term 2025-2026 "
            "(total enrolled, not entering class; Course 14-2 Mathematical Economics counted "
            "separately with 10)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-economics-phd": {
        "cohort_size": 125,
        "basis": (
            "doctoral (regular) graduate students enrolled in Course 14 (Economics), fall term "
            "2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-linguistics-philosophy-bs": {
        "cohort_size": 7,
        "basis": (
            "total undergraduate majors enrolled in Course 24 (Linguistics and Philosophy), fall "
            "term 2025-2026 (total enrolled, not entering class; Course 24-1 Philosophy counted "
            "separately)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-political-science-bs": {
        "cohort_size": 10,
        "basis": (
            "total undergraduate majors enrolled in Course 17 (Political Science), fall term "
            "2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-cms-writing-bs": {
        "cohort_size": 3,
        "basis": (
            "total undergraduate majors enrolled in Course 21-CMS Comparative Media Studies (2) "
            "plus Course 21W Writing and Humanistic Studies (1), fall term 2025-2026 (total "
            "enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-anthropology-bs": {
        "cohort_size": 1,
        "basis": (
            "total undergraduate majors enrolled in Course 21A (Anthropology), fall term "
            "2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-history-bs": {
        "cohort_size": 1,
        "basis": (
            "total undergraduate majors enrolled in Course 21H (History), fall term 2025-2026 "
            "(total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-literature-bs": {
        "cohort_size": 1,
        "basis": (
            "total undergraduate majors enrolled in Course 21L (Literature), fall term 2025-2026 "
            "(total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-music-bs": {
        "cohort_size": 4,
        "basis": (
            "total undergraduate majors enrolled in Course 21M (Music), fall term 2025-2026 "
            "(total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-management-bs": {
        "cohort_size": 16,
        "basis": (
            "total undergraduate majors enrolled in Course 15-1 (Management), fall term 2025-2026"
            " (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-business-analytics-bs": {
        "cohort_size": 26,
        "basis": (
            "total undergraduate majors enrolled in Course 15-2 (Business Analytics), fall term "
            "2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-finance-bs": {
        "cohort_size": 94,
        "basis": (
            "total undergraduate majors enrolled in Course 15-3 (Finance), fall term 2025-2026 "
            "(total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-architecture-bs": {
        "cohort_size": 25,
        "basis": (
            "total undergraduate majors enrolled in Course 4 (Architecture), fall term 2025-2026 "
            "(total enrolled, not entering class; Course 4-B Art and Design counted separately "
            "with 13)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-dusp-bs": {
        "cohort_size": 8,
        "basis": (
            "total undergraduate majors enrolled in Course 11 (Urban Studies and Planning), fall "
            "term 2025-2026 (total enrolled, not entering class; Course 11-6 Urban Science and "
            "Planning with Computer Science counted separately)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-city-planning-sm": {
        "cohort_size": 132,
        "basis": (
            "master's-level graduate students enrolled in Course 11 (Urban Studies and Planning),"
            " fall term 2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-red-sm": {
        "cohort_size": 32,
        "basis": (
            "master's-level graduate students enrolled in Real Estate Development (RED), fall "
            "term 2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-mediaarts-sm": {
        "cohort_size": 49,
        "basis": (
            "master's-level graduate students enrolled in the Program in Media Arts and Sciences "
            "(MAS), fall term 2025-2026 (total enrolled, not entering class; 89 additional "
            "doctoral students)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-science-writing-sm": {
        "cohort_size": 8,
        "basis": (
            "master's-level graduate students enrolled in Writing and Humanistic Studies (Course "
            "21W, the Graduate Program in Science Writing), fall term 2025-2026 (total enrolled, "
            "not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-cs-6-3-bs": {
        "cohort_size": 626,
        "basis": (
            "total undergraduate majors enrolled in Course 6-3 (Computer Science and "
            "Engineering), fall term 2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-ai-6-4-bs": {
        "cohort_size": 328,
        "basis": (
            "total undergraduate majors enrolled in Course 6-4 (Artificial Intelligence and "
            "Decision Making), fall term 2025-2026 (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-comp-cognition-bs": {
        "cohort_size": 91,
        "basis": (
            "total undergraduate students enrolled in Course 6-9 (Computation and Cognition), "
            "fall term 2025-2026 (total enrolled, not entering class; jointly offered major "
            "counted whole here)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-cs-econ-data-bs": {
        "cohort_size": 66,
        "basis": (
            "total undergraduate students enrolled in Course 6-14 (Computer Science, Economics "
            "and Data Science), fall term 2025-2026 (total enrolled, not entering class; jointly "
            "offered major counted whole here)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-cse-phd": {
        "cohort_size": 67,
        "basis": (
            "doctoral (regular) graduate students enrolled in Computational Science and "
            "Engineering, fall term 2025-2026: 12 in the standalone CSE PhD plus 55 in the "
            "department-based CSD track (total enrolled, not entering class)"
        ),
        "source": "Enrollment statistics by year 2025-2026 | MIT Registrar",
        "source_url": "https://registrar.mit.edu/statistics-reports/enrollment-statistics-year",
    },
    "mit-sloan-mba": {
        "cohort_size": 450,
        "basis": "MBA Class of 2027 (includes LGO students) — entering class enrolled fall 2025",
        "international_pct": 42.0,
        "source": "MBA Class of 2027 Profile | MBA | MIT Sloan",
        "source_url": "https://mitsloan.mit.edu/mba/meet-class/class-profile",
    },
    "mit-sloan-mfin": {
        "cohort_size": 126,
        "basis": "MFin students matriculated in 2025 (Class Enrolling in 2025)",
        "international_pct": 86.0,
        "source": "Class Enrolling in 2025 Profile | Master of Finance | MIT Sloan",
        "source_url": "https://mitsloan.mit.edu/mfin/meet-class/class-profile",
    },
    "mit-sloan-fellows-mba": {
        "cohort_size": 116,
        "basis": "MIT Sloan Fellows Class of 2026 enrollment (entering one-year class)",
        "international_pct": 75.0,
        "source": (
            "MIT Sloan Fellows Class of 2026 Profile | MIT Sloan Fellows MBA Program | MIT Sloan"
        ),
        "source_url": "https://mitsloan.mit.edu/mit-sloan-fellows-mba/meet-class/class-profile",
    },
    "mit-sdm-sm": {
        "cohort_size": 60,
        "basis": (
            "Master's Degree Students in the SDM class entering in September 2025 (35 additional "
            "certificate students not counted)"
        ),
        "source": "Class Profile - MIT SDM - System Design and Management",
        "source_url": "https://sdm.mit.edu/admission/class-profile/",
    },
}
_CLASS_PROFILE_BY_SLUG.update(_CLASS_PROFILE_RESEARCH)

# Curricular structure — official catalog.mit.edu degree charts + department
# program pages (source per entry). Refreshes the earlier hand-built entries
# (e.g. the Sloan MBA's seven optional certificates supersede the old
# three-track framing; Course 6-2 is now 6-5 'EE with Computing').
_TRACKS_RESEARCH: dict[str, dict] = {
    "mit-aeroastro-bs": {
        "label": "Course 16 professional areas",
        "note": (
            "Course 16 (Aerospace Engineering) requires four subjects from at least three "
            "professional areas (listed below) on top of a nine-subject departmental core; an "
            "'aerospace information technology' option restricts 36 of the 48 professional-area "
            "units. The companion 16-ENG (SB in Engineering) replaces this with a "
            "department-approved 72-unit concentration; faculty-developed 16-ENG concentrations "
            "include aerospace software engineering, autonomous systems, computational "
            "engineering, energy, environment, space exploration, and transportation (per "
            "aeroastro.mit.edu)."
        ),
        "items": [
            {
                "name": "Fluid Mechanics",
            },
            {
                "name": "Materials and Structures",
            },
            {
                "name": "Propulsion",
            },
            {
                "name": "Computational Tools",
            },
            {
                "name": "Estimation and Control",
            },
            {
                "name": "Computer Systems",
            },
            {
                "name": "Communications Systems",
            },
            {
                "name": "Humans and Automation",
            },
        ],
        "source": (
            "Aerospace Engineering (Course 16) | MIT Course Catalog; Engineering (Course 16-ENG) "
            "| MIT Course Catalog"
        ),
        "source_url": "https://catalog.mit.edu/degree-charts/aerospace-engineering-course-16/",
    },
    "mit-ai-6-4-bs": {
        "label": "Course 6-4 center areas",
        "note": (
            "The 6-4 (Artificial Intelligence and Decision Making) chart requires fundamentals "
            "plus one subject from each of five named 'center' areas (60 units), an application "
            "CI-M, electives, and a SERC subject."
        ),
        "items": [
            {
                "name": "Data-centric",
            },
            {
                "name": "Model-centric",
            },
            {
                "name": "Decision-centric",
            },
            {
                "name": "Computation-centric",
            },
            {
                "name": "Human-centric",
            },
        ],
        "source": "Artificial Intelligence and Decision Making (Course 6-4) | MIT Course Catalog",
        "source_url": (
            "https://catalog.mit.edu/degree-charts/artifical-intelligence-decision-making-course-"
            "6-4/"
        ),
    },
    "mit-architecture-bs": {
        "label": "Course 4 discipline areas (and 4-B)",
        "note": (
            "The BSA (Course 4) organizes its restricted electives across the department's five "
            "discipline areas (below), on top of a required core of design studios, environmental"
            " technologies, structural design, design computation, and a thesis sequence. The "
            "separate SB in Art and Design (Course 4-B) groups its restricted electives into "
            "three thematic categories: Objects; Information; Art and Experience."
        ),
        "items": [
            {
                "name": "Architecture Design and Studies",
            },
            {
                "name": "Art, Culture, and Technology",
            },
            {
                "name": "Building Technology",
            },
            {
                "name": "Computation",
            },
            {
                "name": "History, Theory and Criticism of Architecture, Art and Design",
            },
        ],
        "source": (
            "Architecture (Course 4) | MIT Course Catalog; Art and Design (Course 4-B) | MIT "
            "Course Catalog"
        ),
        "source_url": "https://catalog.mit.edu/degree-charts/architecture-course-4/",
    },
    "mit-architecture-march": {
        "label": "MArch curriculum components",
        "note": (
            "The professional Master of Architecture totals 306-348 units over roughly 3.5 years:"
            " three core design studios plus option studios, building technology and professional"
            " practice subjects, restricted electives in Computation and in "
            "History/Theory/Criticism, one program-area elective in each of four areas (Art, "
            "Culture, and Technology; Computation; History, Theory, and Criticism; Urbanism), and"
            " a thesis sequence."
        ),
        "items": [
            {
                "name": "Architecture Design Core Studios I–III",
            },
            {
                "name": "Architecture Design Option Studios (x3)",
            },
            {
                "name": (
                    "Building Technology + Professional Practice (structures, envelopes, "
                    "environmental technologies)"
                ),
            },
            {
                "name": "Program area: Art, Culture, and Technology",
            },
            {
                "name": "Program area: Computation",
            },
            {
                "name": "Program area: History, Theory, and Criticism",
            },
            {
                "name": "Program area: Urbanism",
            },
            {
                "name": "Preparation for MArch Thesis + Graduate Thesis",
            },
        ],
        "source": "Master of Architecture | MIT Course Catalog",
        "source_url": "https://catalog.mit.edu/degree-charts/master-architecture/",
    },
    "mit-bcs-bs": {
        "label": "Course 9 curriculum tiers",
        "note": (
            "Course 9 (Brain and Cognitive Sciences) structures the major as a tiered system: "
            "Tier I core (Introduction to Psychological Science, Introduction to Neuroscience, "
            "Introduction to Neural Computation), then seven subjects from Tier II/Tier "
            "III/Restricted Electives (at least three from Tier II), plus a laboratory or "
            "research experience."
        ),
        "items": [
            {
                "name": "Tier I — core (psychological science, neuroscience, neural computation)",
            },
            {
                "name": (
                    "Tier II — intermediate (cellular/molecular neurobiology, perception, "
                    "computational cognitive science)"
                ),
            },
            {
                "name": (
                    "Tier III — advanced/clinical (disorders of the nervous system, neural "
                    "interfaces)"
                ),
            },
            {
                "name": "Restricted Electives — complementary technical subjects",
            },
            {
                "name": "Laboratory / Research experience",
            },
        ],
        "source": "Brain and Cognitive Sciences (Course 9) | MIT Course Catalog",
        "source_url": "https://catalog.mit.edu/degree-charts/brain-cognitive-sciences-course-9/",
    },
    "mit-be-bs": {
        "label": "Course 20 curriculum tiers",
        "note": (
            "Course 20 (Biological Engineering) has a single unified curriculum with no named "
            "tracks or concentrations; the departmental program is organized into three tiers "
            "plus restricted electives (33-36 units) and unrestricted electives."
        ),
        "items": [
            {
                "name": (
                    "Tier I — foundational subjects (chemistry, computation, genetics, "
                    "mathematics, thermodynamics)"
                ),
            },
            {
                "name": (
                    "Tier II — biochemistry, cell biology, BE laboratory fundamentals, "
                    "instrumentation, systems analysis"
                ),
            },
            {
                "name": "Tier III — biological physics and engineering design",
            },
            {
                "name": "Restricted Electives (33-36 units)",
            },
        ],
        "source": "Biological Engineering (Course 20) | MIT Course Catalog",
        "source_url": "https://catalog.mit.edu/degree-charts/biological-engineering-course-20/",
    },
    "mit-biology-bs": {
        "label": "Course 7 curriculum structure",
        "note": (
            "Course 7 (Biology) is a single degree path with no named tracks or options; no 7-A "
            "variant appears in the current catalog degree chart. The departmental program "
            "comprises required subjects (7 courses, 90 units), the capstone 'Communication in "
            "Experimental Biology (CI-M)', and three restricted electives chosen from ~25 options"
            " (e.g., Immunology, Human Physiology, Evolutionary Biology)."
        ),
        "items": [
            {
                "name": "Required Subjects (7 courses, 90 units)",
            },
            {
                "name": "Biology Capstone — Communication in Experimental Biology (CI-M)",
            },
            {
                "name": "Restricted Electives (3 subjects, 36 units)",
            },
        ],
        "source": "Biology (Course 7) | MIT Course Catalog",
        "source_url": "https://catalog.mit.edu/degree-charts/biology-course-7/",
    },
    "mit-cee-bs": {
        "label": "Course 1-ENG core coursework areas",
        "note": (
            "The 1-ENG (SB in Engineering, CEE) degree chart directs students to 'select one area"
            " of core coursework' (63-66 units) from three named areas, complemented by at least "
            "four additional restricted electives forming a coherent program supervised by CEE "
            "faculty."
        ),
        "items": [
            {
                "name": "Environment",
            },
            {
                "name": "Mechanics/Materials",
            },
            {
                "name": "Energy, Transportation, and Societal Systems",
            },
        ],
        "source": "Engineering (Course 1-ENG) | MIT Course Catalog",
        "source_url": (
            "https://catalog.mit.edu/degree-charts/engineering-civil-environmental-engineering-co"
            "urse-1-eng/"
        ),
    },
    "mit-cheme-bs": {
        "label": "Chemical Engineering degree options (10 / 10-B / 10-ENG)",
        "note": (
            "ChemE offers three SB options: Course 10 (Chemical Engineering, tiered "
            "foundational/intermediate/advanced subjects), Course 10-B (Chemical-Biological "
            "Engineering), and Course 10-ENG (flexible SB in Engineering). 10-ENG students select"
            " one of seven designated concentrations: Biomedical Engineering; Energy; Engineering"
            " Computation; Environmental Studies; Manufacturing Design; Materials Process and "
            "Design; Process Data Analytics."
        ),
        "items": [
            {
                "name": "Course 10 — Chemical Engineering",
            },
            {
                "name": "Course 10-B — Chemical-Biological Engineering",
            },
            {
                "name": "Course 10-ENG — Engineering (seven designated concentrations)",
            },
        ],
        "source": (
            "Chemical Engineering (Course 10) | MIT Course Catalog; Engineering (Course 10-ENG) |"
            " MIT Course Catalog"
        ),
        "source_url": "https://catalog.mit.edu/degree-charts/chemical-engineering-course-10/",
    },
    "mit-chemistry-bs": {
        "label": "Course 5 degree options",
        "note": (
            "The Chemistry SB offers two options: the Standard Option (fixed core of 5.03, 5.07, "
            "5.12, 5.13, 5.601/5.602, 5.611/5.612 plus advanced electives and laboratory "
            "requirements; 147 units in the major) and the Flexible Option (145 units; students "
            "select a minimum of 36 units 'forming an intellectually coherent unit in some area' "
            "approved by the department)."
        ),
        "items": [
            {
                "name": "Chemistry (Standard Option)",
            },
            {
                "name": "Chemistry (Flexible Option)",
            },
        ],
        "source": "Chemistry (Course 5) | MIT Course Catalog",
        "source_url": "https://catalog.mit.edu/degree-charts/chemistry-course-5/",
    },
    "mit-city-planning-sm": {
        "label": "MCP areas of specialization (DUSP program groups)",
        "note": (
            "MCP applicants select an area of specialization; DUSP's official Masters page lists "
            "city design and development; environmental policy and planning; housing, community, "
            "and economic development; international development; urban science; and mobility. "
            "The first four are DUSP's long-standing Program Groups."
        ),
        "items": [
            {
                "name": "City Design and Development",
            },
            {
                "name": "Environmental Policy and Planning",
            },
            {
                "name": "Housing, Community, and Economic Development",
            },
            {
                "name": "International Development",
            },
            {
                "name": "Urban Science",
            },
            {
                "name": "Mobility",
            },
        ],
        "source": "Masters | DUSP",
        "source_url": "https://dusp.mit.edu/masters",
    },
    "mit-cms-writing-bs": {
        "label": "CMS/W degree options (CMS / 21W)",
        "note": (
            "Comparative Media Studies/Writing offers two SB degrees: Comparative Media Studies "
            "(required core + a Media Practice and Production subject + CI-M subject + capstone "
            "'Current Debates in Media' + six CMS restricted electives) and Writing (Course 21W: "
            "pre-thesis tutorial and thesis, one workshop chosen from options such as Fiction, "
            "Poetry, or Science Writing, plus nine subjects 'that form a cohesive unit' — no "
            "formally named tracks)."
        ),
        "items": [
            {
                "name": "Comparative Media Studies (CMS)",
            },
            {
                "name": "Writing (Course 21W)",
            },
        ],
        "source": (
            "Comparative Media Studies (CMS) | MIT Course Catalog; Writing (Course 21W) | MIT "
            "Course Catalog"
        ),
        "source_url": "https://catalog.mit.edu/degree-charts/comparative-media-studies-cms/",
    },
    "mit-comp-cognition-bs": {
        "label": "Course 6-9 requirement areas",
        "note": (
            "Computation and Cognition (Course 6-9), joint between EECS and BCS, organizes the "
            "major into required foundational subjects plus EECS program subjects, BCS program "
            "subjects (split into 'Brain Systems/Neurophysiology' and 'Computation and Cognition'"
            " subcategories), program electives, laboratory subjects, and an advanced project."
        ),
        "items": [
            {
                "name": "Required Subjects (CS, neuroscience, mathematics foundations)",
            },
            {
                "name": "EECS Program Subjects",
            },
            {
                "name": "BCS Program Subjects — Brain Systems/Neurophysiology",
            },
            {
                "name": "BCS Program Subjects — Computation and Cognition",
            },
            {
                "name": "Program Electives + Laboratory + Advanced Project",
            },
        ],
        "source": "Computation and Cognition (Course 6-9) | MIT Course Catalog",
        "source_url": "https://catalog.mit.edu/degree-charts/computation-cognition-6-9/",
    },
    "mit-cs-6-3-bs": {
        "label": "Course 6-3 Computer Science tracks",
        "note": (
            "The 6-3 degree chart requires core CS subjects plus two subjects from one Computer "
            "Science track and two more from a Computer Science, AI + Decision Making, or "
            "Electrical Engineering track; the named CS tracks are listed below (from the EECS "
            "Tracks catalog page)."
        ),
        "items": [
            {
                "name": "Computer Architecture",
            },
            {
                "name": "Computers and Society",
            },
            {
                "name": "Human Computer Interaction",
            },
            {
                "name": "Programming Principles and Tools",
            },
            {
                "name": "Systems",
            },
            {
                "name": "Theory",
            },
        ],
        "source": (
            "Computer Science and Engineering (Course 6-3) | MIT Course Catalog; EECS Tracks | "
            "MIT Course Catalog"
        ),
        "source_url": (
            "https://catalog.mit.edu/degree-charts/computer-science-engineering-course-6-3/"
        ),
    },
    "mit-cs-econ-data-bs": {
        "label": "Course 6-14 requirement areas",
        "note": (
            "Computer Science, Economics, and Data Science (Course 6-14) subdivides its required "
            "subjects into six areas (below) and adds elective subjects in Computer Science and "
            "in Economics (the economics electives grouped into Data Science and Theory lists)."
        ),
        "items": [
            {
                "name": "Mathematics",
            },
            {
                "name": "Computation / Algorithms",
            },
            {
                "name": "Economics",
            },
            {
                "name": "Introductory Probability and Statistics",
            },
            {
                "name": "Data Science",
            },
            {
                "name": "Project-based subjects",
            },
            {
                "name": "Electives: Computer Science + Economics (Data Science / Theory)",
            },
        ],
        "source": (
            "Computer Science, Economics, and Data Science (Course 6-14) | MIT Course Catalog"
        ),
        "source_url": (
            "https://catalog.mit.edu/degree-charts/computer-science-economics-data-science-course"
            "-6-14/"
        ),
    },
    "mit-dmse-bs": {
        "label": "DMSE degree options (3 / 3-A / 3-C)",
        "note": (
            "DMSE offers Course 3 (SB in Materials Science and Engineering: 11 required core "
            "subjects + 33-36 units of restricted electives, no named tracks), Course 3-A "
            "(flexible: students propose an individualized 66-unit elective program approved by "
            "the department), and Course 3-C (Archaeology and Materials: materials core combined "
            "with archaeological science subjects)."
        ),
        "items": [
            {
                "name": "Course 3 — Materials Science and Engineering",
            },
            {
                "name": (
                    "Course 3-A — Materials Science and Engineering (flexible; self-designed "
                    "66-unit elective program)"
                ),
            },
            {
                "name": "Course 3-C — Archaeology and Materials",
            },
        ],
        "source": (
            "Materials Science and Engineering (Course 3 / 3-A) and Archaeology and Materials "
            "(Course 3-C) | MIT Course Catalog"
        ),
        "source_url": (
            "https://catalog.mit.edu/degree-charts/materials-science-engineering-course-3/"
        ),
    },
    "mit-dusp-bs": {
        "label": "Course 11 core requirements",
        "note": (
            "The Planning SB (Course 11) has no preset named concentrations; it pairs four "
            "required core subjects (below) with 78-81 units of planning electives selected in "
            "consultation with an advisor, an optional urban field experience, and a required "
            "thesis/senior project with seminar."
        ),
        "items": [
            {
                "name": "Introduction to Urban Design and Development",
            },
            {
                "name": "Making Public Policy",
            },
            {
                "name": "Principles of Microeconomics",
            },
            {
                "name": "Introduction to Spatial Analysis and GIS Laboratory",
            },
            {
                "name": "Planning electives (78-81 units, advisor-guided) + thesis/senior project",
            },
        ],
        "source": "Planning (Course 11) | MIT Course Catalog",
        "source_url": "https://catalog.mit.edu/degree-charts/planning-course-11/",
    },
    "mit-eaps-bs": {
        "label": "Course 12 concentration areas",
        "note": (
            "Course 12 (Earth, Atmospheric, and Planetary Sciences) students select one of four "
            "named concentration areas and complete 36-39 units of coursework from that area's "
            "approved list."
        ),
        "items": [
            {
                "name": "Area 1 — Earth Science",
            },
            {
                "name": "Area 2 — Climate, Atmospheres, and Oceans",
            },
            {
                "name": "Area 3 — Planetary Science and Astronomy",
            },
            {
                "name": "Area 4 — Environmental Science",
            },
        ],
        "source": "Earth, Atmospheric, and Planetary Sciences (Course 12) | MIT Course Catalog",
        "source_url": (
            "https://catalog.mit.edu/degree-charts/earth-atmospheric-planetary-sciences-course-12"
            "/"
        ),
    },
    "mit-economics-bs": {
        "label": "Economics degree options (14-1 / 14-2)",
        "note": (
            "The department offers two SB degrees with separate degree charts: Economics (Course "
            "14-1: required micro/macro/statistics/econometrics core, elective categories, four "
            "restricted economics electives, and a thesis) and Mathematical Economics (Course "
            "14-2: adds mathematical rigor with Real Analysis 1 and differential equations or "
            "linear algebra alongside economic theory and econometrics)."
        ),
        "items": [
            {
                "name": "Course 14-1 — Economics",
            },
            {
                "name": "Course 14-2 — Mathematical Economics",
            },
        ],
        "source": (
            "Economics (Course 14-1) | MIT Course Catalog; Mathematical Economics (Course 14-2) |"
            " MIT Course Catalog"
        ),
        "source_url": "https://catalog.mit.edu/degree-charts/economics-course-14/",
    },
    "mit-eecs-bs": {
        "label": "EECS Electrical Engineering tracks (Course 6-2 → 6-5)",
        "note": (
            "Course 6-2 (Electrical Engineering and Computer Science) was renamed and renumbered "
            "as 6-5 Electrical Engineering with Computing starting Fall 2024, per MIT EECS. The "
            "6-5 degree chart requires foundation subjects, system-design 'center' subjects, and "
            "two subjects from each of two different EE tracks plus two further subjects "
            "satisfying 6-3/6-4/6-5 requirements; the named EE tracks are listed below."
        ),
        "items": [
            {
                "name": "Biomedical Systems",
            },
            {
                "name": "Communications and Networks",
            },
            {
                "name": "Computer Architecture",
            },
            {
                "name": "Devices, Circuits, and Systems",
            },
            {
                "name": "Electromagnetics and Photonic Systems",
            },
            {
                "name": "Embedded Systems",
            },
            {
                "name": "Energy Systems",
            },
            {
                "name": "Hardware Design",
            },
            {
                "name": "Hardware and Software",
            },
            {
                "name": "Nanoelectronics",
            },
            {
                "name": "Quantum Systems Engineering",
            },
            {
                "name": "Systems Science",
            },
        ],
        "source": (
            "EECS Tracks | MIT Course Catalog (renaming confirmed on '6-2: Electrical Engineering"
            " and Computer Science - MIT EECS', eecs.mit.edu)"
        ),
        "source_url": (
            "https://catalog.mit.edu/degree-charts/electrical-engineering-computer-science-tracks"
            "/"
        ),
    },
    "mit-eecs-phd": {
        "label": "EECS research areas",
        "note": (
            "MIT EECS organizes doctoral research under three faculty divisions (Electrical "
            "Engineering; Computer Science; Artificial Intelligence + Decision-making) and lists "
            "26 named research areas on its official Research page; a representative subset is "
            "below."
        ),
        "items": [
            {
                "name": "Artificial Intelligence and Machine Learning",
            },
            {
                "name": "AI for Healthcare and Life Sciences",
            },
            {
                "name": "Communications Systems",
            },
            {
                "name": "Computer Architecture",
            },
            {
                "name": "Electronic, Magnetic, Optical and Quantum Materials and Devices",
            },
            {
                "name": "Energy",
            },
            {
                "name": "Graphics and Vision",
            },
            {
                "name": "Human-Computer Interaction",
            },
            {
                "name": "Integrated Circuits and Systems",
            },
            {
                "name": "Natural Language and Speech Processing",
            },
            {
                "name": "Optics + Photonics",
            },
            {
                "name": "Programming Languages and Software Engineering",
            },
            {
                "name": "Quantum Computing, Communication, and Sensing",
            },
            {
                "name": "Robotics",
            },
            {
                "name": "Security and Cryptography",
            },
            {
                "name": "Signal Processing",
            },
            {
                "name": "Systems and Networking",
            },
            {
                "name": "Systems Theory, Control, and Autonomy",
            },
            {
                "name": "Theory of Computation",
            },
        ],
        "source": "Research - MIT EECS",
        "source_url": "https://www.eecs.mit.edu/research/",
    },
    "mit-math-bs": {
        "label": "Course 18 degree options",
        "note": (
            "The Mathematics SB (Course 18) offers three named options — General Mathematics, "
            "Applied Mathematics, and Pure Mathematics — each with distinct required sequences "
            "(e.g., Applied requires 18.03, complex variables, 18.06, 18.300; Pure requires "
            "18.100B, 18.701/18.702, 18.901). A separate joint degree, Mathematics with Computer "
            "Science (Course 18-C), has its own degree chart."
        ),
        "items": [
            {
                "name": "General Mathematics Option",
            },
            {
                "name": "Applied Mathematics Option",
            },
            {
                "name": "Pure Mathematics Option",
            },
            {
                "name": "Mathematics with Computer Science (Course 18-C, separate joint degree)",
            },
        ],
        "source": (
            "Mathematics (Course 18) | MIT Course Catalog; Mathematics with Computer Science "
            "(Course 18-C) | MIT Course Catalog"
        ),
        "source_url": "https://catalog.mit.edu/degree-charts/mathematics-course-18/",
    },
    "mit-math-phd": {
        "label": "Mathematics research areas (Pure / Applied)",
        "note": (
            "MIT Mathematics research is organized into two divisions — Pure Mathematics and "
            "Applied Mathematics — with the named areas below listed on the department's research"
            " page."
        ),
        "items": [
            {
                "name": "Pure: Algebra & Algebraic Geometry",
            },
            {
                "name": "Pure: Algebraic Topology",
            },
            {
                "name": "Pure: Analysis & PDEs",
            },
            {
                "name": "Pure: Geometry & Topology",
            },
            {
                "name": "Pure: Mathematical Logic & Foundations",
            },
            {
                "name": "Pure: Number Theory",
            },
            {
                "name": "Pure: Probability & Statistics",
            },
            {
                "name": "Pure: Representation Theory",
            },
            {
                "name": "Applied: Combinatorics",
            },
            {
                "name": "Applied: Computational Biology",
            },
            {
                "name": "Applied: Physical Applied Mathematics",
            },
            {
                "name": "Applied: Computational Science & Numerical Analysis",
            },
            {
                "name": "Applied: Theoretical Computer Science",
            },
            {
                "name": "Applied: Mathematics of Data",
            },
        ],
        "source": "Research — MIT Department of Mathematics",
        "source_url": "https://math.mit.edu/research/",
    },
    "mit-meche-bs": {
        "label": "Course 2 degree options",
        "note": (
            "MechE offers Course 2 (full SB in Mechanical Engineering: required core of ~135 "
            "units + restricted electives + unrestricted electives, no preset tracks) and Course "
            "2-A (SB in Engineering: a flexible degree where students self-design a 72-unit "
            "concentration forming an engineering topic, approved by the 2-A review committee)."
        ),
        "items": [
            {
                "name": "Course 2 — Mechanical Engineering (required core + restricted electives)",
            },
            {
                "name": (
                    "Course 2-A — Engineering (flexible; self-designed 72-unit concentration "
                    "approved by the 2-A review committee)"
                ),
            },
        ],
        "source": (
            "Mechanical Engineering (Course 2) | MIT Course Catalog; Engineering (Course 2-A) | "
            "MIT Course Catalog"
        ),
        "source_url": "https://catalog.mit.edu/degree-charts/mechanical-engineering-course-2/",
    },
    "mit-meche-phd": {
        "label": "MechE research areas",
        "note": (
            "MIT Mechanical Engineering organizes its research into seven named areas on its "
            "official research page."
        ),
        "items": [
            {
                "name": "Mechanics",
            },
            {
                "name": "Design + Manufacturing",
            },
            {
                "name": "Controls, Instrumentation + Robotics",
            },
            {
                "name": "Energy Science + Engineering",
            },
            {
                "name": "Ocean Science + Engineering",
            },
            {
                "name": "Bioengineering",
            },
            {
                "name": "Micro + Nano Engineering",
            },
        ],
        "source": "RESEARCH @ MIT MECHE",
        "source_url": "https://meche.mit.edu/research",
    },
    "mit-mediaarts-sm": {
        "label": "Media Lab research groups (selection)",
        "note": (
            "Media Arts and Sciences students join a Media Lab research group; the Lab's official"
            " groups listing includes (among others) the ten below. Other current groups include "
            "Conformable Decoders, Critical Matter, Future Sketches, Human Dynamics, Molecular "
            "Machines, Multisensory Intelligence, Responsive Environments, Sculpting Evolution, "
            "Signal Kinetics, and Viral Communications."
        ),
        "items": [
            {
                "name": "Affective Computing",
            },
            {
                "name": "Biomechatronics",
            },
            {
                "name": "Camera Culture",
            },
            {
                "name": "City Science",
            },
            {
                "name": "Fluid Interfaces",
            },
            {
                "name": "Lifelong Kindergarten",
            },
            {
                "name": "Opera of the Future",
            },
            {
                "name": "Personal Robots",
            },
            {
                "name": "Space Enabled",
            },
            {
                "name": "Tangible Media",
            },
        ],
        "source": "Research Groups — MIT Media Lab",
        "source_url": "https://www.media.mit.edu/groups/",
    },
    "mit-nse-bs": {
        "label": "NSE degree options (22 / 22-ENG)",
        "note": (
            "Course 22 (Nuclear Science and Engineering) is a single curriculum: basic "
            "requirements, required core (including Engineering of Nuclear Systems and Fusion "
            "Energy), plus math/materials/NSE restricted electives and a thesis. Course 22-ENG "
            "(SB in Engineering) is flexible: a department-approved 72-unit focus-area elective "
            "program, with a System Specialization choice between 22.06 Engineering of Nuclear "
            "Systems and 22.061 Fusion Energy."
        ),
        "items": [
            {
                "name": "Course 22 — Nuclear Science and Engineering",
            },
            {
                "name": (
                    "Course 22-ENG — Engineering (flexible; department-approved 72-unit focus "
                    "area; system specialization in fission or fusion)"
                ),
            },
        ],
        "source": (
            "Nuclear Science and Engineering (Course 22) | MIT Course Catalog; Engineering "
            "(Course 22-ENG) | MIT Course Catalog"
        ),
        "source_url": (
            "https://catalog.mit.edu/degree-charts/nuclear-science-engineering-course-22/"
        ),
    },
    "mit-physics-bs": {
        "label": "Course 8 degree options",
        "note": (
            "The Physics SB offers two pathways: the Focused Option (full core through "
            "quantum/classical mechanics, experimental physics, restricted electives such as "
            "8.07/8.08/8.09, and a thesis; 174 units in the major) and the Flexible Option "
            "(129-138 units; a choice of experimental experiences plus 'three subjects forming "
            "one intellectually coherent unit in some area, not necessarily physics')."
        ),
        "items": [
            {
                "name": "Physics (Focused Option)",
            },
            {
                "name": "Physics (Flexible Option)",
            },
        ],
        "source": "Physics (Course 8) | MIT Course Catalog",
        "source_url": "https://catalog.mit.edu/degree-charts/physics-course-8/",
    },
    "mit-physics-phd": {
        "label": "Physics research areas",
        "note": (
            "The MIT Physics Department lists 13 named research areas on its official research "
            "page, spanning astrophysics through quantum information."
        ),
        "items": [
            {
                "name": "Astrophysics Observation, Instrumentation, and Experiment",
            },
            {
                "name": "Astrophysics Theory",
            },
            {
                "name": "Atomic Physics",
            },
            {
                "name": "Biophysics",
            },
            {
                "name": "Condensed Matter Experiment",
            },
            {
                "name": "Condensed Matter Theory",
            },
            {
                "name": "High Energy and Particle Theory",
            },
            {
                "name": "Nuclear Physics Experiment",
            },
            {
                "name": "Particle Physics Experiment",
            },
            {
                "name": "Plasma Physics",
            },
            {
                "name": "Quantum Gravity and Field Theory",
            },
            {
                "name": "Quantum Information Science",
            },
            {
                "name": "Strong Interactions and Nuclear Theory",
            },
        ],
        "source": "Research — MIT Department of Physics",
        "source_url": "https://physics.mit.edu/research/",
    },
    "mit-sdm-sm": {
        "label": "SDM curriculum core",
        "note": (
            "The SDM master's centers on 'Foundations of System Design and Management', a "
            "three-term integrated core (fall, IAP, spring) that develops system architecture, "
            "systems engineering, and project management via a spiral approach and culminates in "
            "an industry-sponsored team project; the degree adds foundation (management) and "
            "depth (engineering) courses, electives, and a thesis."
        ),
        "items": [
            {
                "name": (
                    "Foundations of System Design and Management (3-term integrated core, 36 "
                    "units)"
                ),
            },
            {
                "name": "Core skill area: System Architecture",
            },
            {
                "name": "Core skill area: Systems Engineering",
            },
            {
                "name": "Core skill area: Project Management",
            },
            {
                "name": "Foundation courses in management (min 12 units)",
            },
            {
                "name": "Depth courses in engineering (min 12 units)",
            },
            {
                "name": "Electives (min 30 units, balanced engineering/management)",
            },
            {
                "name": "Thesis (24 units)",
            },
        ],
        "source": "Integrated Core & Curriculum - MIT SDM - System Design and Management",
        "source_url": "https://sdm.mit.edu/programs/integrated-core-curriculum/",
    },
    "mit-sloan-mba": {
        "label": "MBA certificates",
        "note": (
            "MIT Sloan's MBA curriculum offers seven optional certificates (the successor "
            "structure to the earlier Finance / Entrepreneurship & Innovation / Enterprise "
            "Management tracks); students may complete up to two."
        ),
        "items": [
            {
                "name": "Business Analytics Certificate",
            },
            {
                "name": "Product Management Certificate",
            },
            {
                "name": "Enterprise Management Certificate",
            },
            {
                "name": "Entrepreneurship & Innovation Certificate",
            },
            {
                "name": "Finance Certificate",
            },
            {
                "name": "Healthcare Certificate",
            },
            {
                "name": "Sustainability Certificate",
            },
        ],
        "source": "MBA Curriculum | MBA | MIT Sloan",
        "source_url": "https://mitsloan.mit.edu/mba/program-components/certificates",
    },
    "mit-sloan-mfin": {
        "label": "MFin concentrations",
        "note": (
            "The Master of Finance is an 18-month degree (four terms with summer internship, "
            "February graduation) with an option to accelerate to 12 months (summer + fall + "
            "spring, May graduation); requirements are identical, only timing differs. Students "
            "may optionally pursue one or more of five concentrations."
        ),
        "items": [
            {
                "name": "Capital Markets",
            },
            {
                "name": "Climate and Social Impact Finance",
            },
            {
                "name": "Corporate Finance",
            },
            {
                "name": "Financial Engineering",
            },
            {
                "name": "FinTech",
            },
        ],
        "source": "Optional Concentrations | Master of Finance | MIT Sloan",
        "source_url": "https://mitsloan.mit.edu/mfin/explore-program/optional-concentrations",
    },
    "mit-tpp-sm": {
        "label": "TPP SM curriculum components",
        "note": (
            "The Technology and Policy Program SM combines a core integrative sequence and "
            "methods/frameworks subjects with a technical concentration and an interdisciplinary "
            "thesis on a technology-policy issue; all students present in the TPP Research "
            "Seminar and complete leadership and communication modules before graduation."
        ),
        "items": [
            {
                "name": "Concepts and Research in Technology & Policy (IDS.411)",
            },
            {
                "name": "Science, Technology and Public Policy (IDS.412)",
            },
            {
                "name": "Quantitative Methods",
            },
            {
                "name": "Microeconomics",
            },
            {
                "name": "Policy Restricted Elective",
            },
            {
                "name": "Technical Concentration (30+ units in a coherent area of study)",
            },
            {
                "name": "TPP Research Seminar + Leadership and Communication modules",
            },
            {
                "name": "Interdisciplinary Thesis (IDS.THG)",
            },
        ],
        "source": "TPP SM Curriculum — Technology and Policy Program",
        "source_url": "https://tpp.mit.edu/academics/tpp-sm-curriculum-2/",
    },
}
_TRACKS_BY_SLUG.update(_TRACKS_RESEARCH)

# Program-published employment reports (CSEA-standard), conditions verbatim.
_OUTCOMES_RESEARCH: dict[str, dict] = {
    "mit-sloan-mba": {
        "employment_rate": 0.871,
        "employment_timeframe": "accepted offers within 3 months of graduation",
        "offers_rate": 0.91,
        "median_salary": 175000,
        "mean_salary": 173132,
        "salary_25th": 154000,
        "salary_75th": 192000,
        "median_signing_bonus": 30000,
        "class_size": 409,
        "top_industries": [
            {
                "name": "Consulting",
                "pct": 0.323,
            },
            {
                "name": "Technology",
                "pct": 0.233,
            },
            {
                "name": "Finance",
                "pct": 0.206,
            },
            {
                "name": "Healthcare / pharma / biotech",
                "pct": 0.081,
            },
        ],
        "top_employers": [
            "Boston Consulting Group",
            "McKinsey & Company",
            "Amazon",
            "Bain & Company",
        ],
        "scope": "program",
        "conditions": (
            "The 2025-2026 Employment Report includes outcomes for 99.2% of the Class of 2025. "
            "89.7% of students accepting an offer provided usable salary data. 67.5% of students "
            "accepting an offer with usable salary data reported a signing bonus. 57.0% reported "
            "receiving other compensation. | Timing of Offers: 'Per MBACSEA Reporting Standards "
            "deadline of August 30, 2025. At time of publication date, 94.1% received offers.'"
        ),
        "methodology": (
            "ACCURACY IN REPORTING EMPLOYMENT STATISTICS: The MIT Sloan School of Management "
            "adheres to the Career Services & Employer Alliance (CSEA) Standards for Reporting "
            "MBA Employment Statistics (cseaglobal.org). Conformance to this business school "
            "industry standard ensures accurate and comparable employment data. Currently, the "
            "majority of the leading MBA programs adhere to these accepted reporting standards. "
            "MIT Sloan takes a leadership role to promote the importance of accurate a"
        ),
        "source": "MIT Sloan 2025-2026 MBA Employment Report (Class of 2025)",
        "source_url": (
            "https://mitsloan.mit.edu/sites/default/files/2025-12/2025-2026-MBA-Employment-Report"
            ".pdf"
        ),
    },
    "mit-sloan-mfin": {
        "employment_rate": 0.942,
        "employment_timeframe": "accepted offers within 6 months of graduation",
        "offers_rate": 0.971,
        "median_salary": 125000,
        "mean_salary": 122858,
        "salary_25th": 100000,
        "salary_75th": 145589,
        "median_signing_bonus": 25000,
        "class_size": 117,
        "top_industries": [
            {
                "name": "Finance",
                "pct": 0.845,
            },
            {
                "name": "Consulting",
                "pct": 0.072,
            },
            {
                "name": (
                    "Technology (includes AI, Cybersecurity, Digital Streaming Platforms, and "
                    "Cloud Services)"
                ),
                "pct": 0.052,
            },
        ],
        "top_employers": [
            "Morgan Stanley (8)",
            "JP Morgan Chase & Co. (5)",
            "Squarepoint Ops (4)",
            "BNP Paribas (3)",
            "Boston Consulting Group (3)",
            "Goldman Sachs (3)",
            "Qube Research & Technologies (3)",
            "Trexquant Investment (3)",
        ],
        "scope": "program",
        "conditions": (
            "Employment data includes responses from 100% of Class of 2025 graduates. 97.1% of "
            "MFin graduates who were seeking employment receiving an offer within six months of "
            "graduation. Of the 94.2% of students who accepted an offer within 6 months of "
            "graduation, 79.8% accepted a full-time position and 13.5% accepted a post-graduate "
            "internship/contract employment."
        ),
        "source": "MIT Sloan 2025 Master of Finance Employment Report",
        "source_url": (
            "https://cdn.cdo.mit.edu/wp-content/uploads/sites/67/2026/02/2025-MFin-Employment-Rep"
            "ort.pdf"
        ),
    },
}
_OUTCOMES_BY_SLUG.update(_OUTCOMES_RESEARCH)

# Catalog breadth: the remaining officially-confirmed MIT degree programs
# (catalog.mit.edu degree charts + OGE programs list + school sites; source per
# entry in the run audit). Verified basics now; deep fields are recorded in
# each program's _standard.omitted and deepened on resume runs.
_PROGRAMS_RESEARCH: list[dict] = [
    {
        "slug": "mit-biology-phd",
        "school": "School of Science",
        "program_name": "Biology PhD (Doctor of Philosophy in Biology)",
        "degree_type": "phd",
        "description": (
            "Doctoral program leading to the PhD in Biology, with research specializations "
            "spanning biochemistry, structural biology, cancer biology, genetics, computational "
            "biology, microbiology, and neurobiology. The Master of Science is not a "
            "prerequisite; students proceed directly to the doctorate."
        ),
        "delivery_format": "in_person",
        "department": "Department of Biology",
    },
    {
        "slug": "mit-bcs-phd",
        "school": "School of Science",
        "program_name": "Brain and Cognitive Sciences PhD",
        "degree_type": "phd",
        "description": (
            "Doctoral program (PhD) in the fields of brain and cognitive sciences, listed as a "
            "degree chart in the MIT catalog under the Department of Brain and Cognitive "
            "Sciences."
        ),
        "delivery_format": "in_person",
        "department": "Department of Brain and Cognitive Sciences",
    },
    {
        "slug": "mit-eaps-phd",
        "school": "School of Science",
        "program_name": "Earth, Atmospheric, and Planetary Sciences PhD/ScD",
        "degree_type": "phd",
        "description": (
            "Doctoral program (PhD/ScD) in the fields of Earth, atmospheric, and planetary "
            "sciences, offered by EAPS and listed as a catalog degree chart."
        ),
        "delivery_format": "in_person",
        "department": "Department of Earth, Atmospheric and Planetary Sciences (EAPS)",
    },
    {
        "slug": "mit-be-phd",
        "school": "School of Engineering",
        "program_name": "Biological Engineering PhD/ScD",
        "degree_type": "phd",
        "description": (
            "Doctoral program (PhD/ScD) in biological engineering offered by the Department of "
            "Biological Engineering, listed as a catalog degree chart."
        ),
        "delivery_format": "in_person",
        "department": "Department of Biological Engineering",
    },
    {
        "slug": "mit-cee-sm",
        "school": "School of Engineering",
        "program_name": "Civil and Environmental Engineering SM (Master of Science)",
        "degree_type": "masters",
        "description": (
            "Research-focused Master of Science in civil and environmental engineering in which "
            "each SM student is matched with a faculty member for a research thesis."
        ),
        "delivery_format": "in_person",
        "department": "Department of Civil and Environmental Engineering",
    },
    {
        "slug": "mit-cee-meng",
        "school": "School of Engineering",
        "program_name": "Civil and Environmental Engineering MEng (Master of Engineering)",
        "degree_type": "masters",
        "duration_months": 9,
        "description": (
            "Nine-month professional Master of Engineering with tracks in Climate, Environment, "
            "and Sustainability; Data Science for Engineering Systems; and Structural Mechanics "
            "and Design."
        ),
        "delivery_format": "in_person",
        "department": "Department of Civil and Environmental Engineering",
    },
    {
        "slug": "mit-cee-phd",
        "school": "School of Engineering",
        "program_name": "Civil and Environmental Engineering PhD/ScD",
        "degree_type": "phd",
        "description": (
            "Research doctoral program (PhD/ScD) in civil and environmental engineering, with "
            "each doctoral student matched to a faculty research advisor."
        ),
        "delivery_format": "in_person",
        "department": "Department of Civil and Environmental Engineering",
    },
    {
        "slug": "mit-dmse-phd",
        "school": "School of Engineering",
        "program_name": "Materials Science and Engineering PhD/ScD",
        "degree_type": "phd",
        "description": (
            "Doctoral program (PhD/ScD) in materials science and engineering offered by DMSE, "
            "listed as a catalog degree chart."
        ),
        "delivery_format": "in_person",
        "department": "Department of Materials Science and Engineering (DMSE)",
    },
    {
        "slug": "mit-nse-phd",
        "school": "School of Engineering",
        "program_name": "Nuclear Science and Engineering PhD/ScD",
        "degree_type": "phd",
        "description": (
            "Doctoral program (PhD/ScD) in nuclear science and engineering offered by NSE, listed"
            " as a catalog degree chart."
        ),
        "delivery_format": "in_person",
        "department": "Department of Nuclear Science and Engineering (NSE)",
    },
    {
        "slug": "mit-eecs-meng",
        "school": "MIT Stephen A. Schwarzman College of Computing",
        "program_name": "Electrical Engineering and Computer Science MEng (Course 6-P)",
        "degree_type": "masters",
        "description": (
            "Master of Engineering (Course 6-P) for EECS undergraduates, a fifth-year "
            "professional degree combining advanced coursework and a thesis."
        ),
        "delivery_format": "in_person",
        "department": "Department of Electrical Engineering and Computer Science (EECS)",
    },
    {
        "slug": "mit-cheme-phd",
        "school": "School of Engineering",
        "program_name": "Chemical Engineering PhD/ScD",
        "degree_type": "phd",
        "description": (
            "Doctoral program (PhD/ScD) in chemical engineering, the department's traditional "
            "research doctorate."
        ),
        "delivery_format": "in_person",
        "department": "Department of Chemical Engineering",
    },
    {
        "slug": "mit-cheme-phdcep",
        "school": "School of Engineering",
        "program_name": "Doctor of Philosophy in Chemical Engineering Practice (PhDCEP)",
        "degree_type": "phd",
        "description": (
            "Doctoral program in Chemical Engineering Practice, a distinctive degree (offered "
            "only at MIT) that pairs doctoral research with the David H. Koch School of Chemical "
            "Engineering Practice and management training."
        ),
        "delivery_format": "in_person",
        "department": "Department of Chemical Engineering",
        "nonstandard_rates": True,
    },
    {
        "slug": "mit-cheme-mscep",
        "school": "School of Engineering",
        "program_name": "Master of Science in Chemical Engineering Practice (MSCEP)",
        "degree_type": "masters",
        "description": (
            "Master's degree in Chemical Engineering Practice built around the David H. Koch "
            "School of Chemical Engineering Practice, a degree offered only at MIT."
        ),
        "delivery_format": "in_person",
        "department": "Department of Chemical Engineering",
        "nonstandard_rates": True,
    },
    {
        "slug": "mit-meche-meng-mfg",
        "school": "School of Engineering",
        "program_name": "Master of Engineering in Manufacturing (MEng)",
        "degree_type": "masters",
        "description": (
            "Professional Master of Engineering in Manufacturing offered by the Department of "
            "Mechanical Engineering."
        ),
        "delivery_format": "in_person",
        "department": "Department of Mechanical Engineering",
        "nonstandard_rates": True,
    },
    {
        "slug": "mit-meche-sm-name",
        "school": "School of Engineering",
        "program_name": (
            "Master of Science in Naval Architecture and Marine Engineering (Naval Construction "
            "and Engineering, 2N)"
        ),
        "degree_type": "masters",
        "description": (
            "Master of Science in naval architecture and marine engineering (and the associated "
            "Naval Engineer's degree) offered by Mechanical Engineering for naval/military "
            "officers and engineers."
        ),
        "delivery_format": "in_person",
        "department": "Department of Mechanical Engineering",
    },
    {
        "slug": "mit-ses-phd",
        "school": "School of Engineering",
        "program_name": "Social and Engineering Systems PhD/ScD",
        "degree_type": "phd",
        "description": (
            "Doctoral program (PhD/ScD) in Social and Engineering Systems offered through IDSS, "
            "listed as a catalog degree chart."
        ),
        "delivery_format": "in_person",
        "department": "Institute for Data, Systems, and Society (IDSS)",
    },
    {
        "slug": "mit-linguistics-phd",
        "school": "School of Humanities, Arts, and Social Sciences",
        "program_name": "Linguistics PhD",
        "degree_type": "phd",
        "duration_months": 60,
        "description": (
            "Doctor of Philosophy in Linguistics; the catalog describes a normal course of study "
            "of five years including the dissertation, aimed at developing general theories of "
            "language structure."
        ),
        "delivery_format": "in_person",
        "department": "Department of Linguistics and Philosophy",
    },
    {
        "slug": "mit-philosophy-phd",
        "school": "School of Humanities, Arts, and Social Sciences",
        "program_name": "Philosophy PhD",
        "degree_type": "phd",
        "description": (
            "Doctoral program in philosophy spanning logic, ethics, metaphysics, epistemology, "
            "philosophy of science, language, and mind."
        ),
        "delivery_format": "in_person",
        "department": "Department of Linguistics and Philosophy",
    },
    {
        "slug": "mit-linguistics-sm",
        "school": "School of Humanities, Arts, and Social Sciences",
        "program_name": (
            "Master of Science in Linguistics (MIT Indigenous Language Initiative, MITILI)"
        ),
        "degree_type": "masters",
        "duration_months": 24,
        "description": (
            "Two-year SM in Linguistics offered through the MIT Indigenous Language Initiative "
            "for members of indigenous communities working to document and preserve endangered "
            "languages."
        ),
        "delivery_format": "in_person",
        "department": "Department of Linguistics and Philosophy",
    },
    {
        "slug": "mit-political-science-phd",
        "school": "School of Humanities, Arts, and Social Sciences",
        "program_name": "Political Science PhD",
        "degree_type": "phd",
        "description": (
            "PhD in Political Science requiring two years of coursework to prepare for general "
            "examinations followed by original dissertation research."
        ),
        "delivery_format": "in_person",
        "department": "Department of Political Science",
    },
    {
        "slug": "mit-hasts-phd",
        "school": "School of Humanities, Arts, and Social Sciences",
        "program_name": "History, Anthropology, and Science, Technology, and Society PhD (HASTS)",
        "degree_type": "phd",
        "description": (
            "Interdisciplinary doctoral program studying how science and technology shape and are"
            " shaped by society, combining history, anthropology, and STS."
        ),
        "delivery_format": "in_person",
        "department": (
            "Program in History, Anthropology, and Science, Technology, and Society (HASTS)"
        ),
    },
    {
        "slug": "mit-smarchs-sm",
        "school": "School of Architecture and Planning",
        "program_name": "Master of Science in Architecture Studies (SMArchS)",
        "degree_type": "masters",
        "duration_months": 24,
        "description": (
            "Two-year post-professional degree of advanced study founded on research and inquiry "
            "in architecture, with multiple disciplinary concentrations."
        ),
        "delivery_format": "in_person",
        "department": "Department of Architecture",
    },
    {
        "slug": "mit-smbt-sm",
        "school": "School of Architecture and Planning",
        "program_name": "Master of Science in Building Technology (SMBT)",
        "degree_type": "masters",
        "description": (
            "Master of Science focused on the development and application of advanced technology "
            "for buildings and cities."
        ),
        "delivery_format": "in_person",
        "department": "Department of Architecture",
    },
    {
        "slug": "mit-smact-sm",
        "school": "School of Architecture and Planning",
        "program_name": "Master of Science in Art, Culture, and Technology (SMACT)",
        "degree_type": "masters",
        "duration_months": 24,
        "description": (
            "Two-year (four-semester) studio-based Master of Science in Art, Culture, and "
            "Technology requiring on-campus academic work. (Existing mit-mediaarts-sm covers "
            "Media Arts; this is a distinct ACT degree.)"
        ),
        "delivery_format": "in_person",
        "department": "Department of Architecture",
    },
    {
        "slug": "mit-architecture-phd",
        "school": "School of Architecture and Planning",
        "program_name": "Architecture PhD",
        "degree_type": "phd",
        "description": (
            "Doctor of Philosophy offered in three concentration areas: History and Theory of "
            "Architecture/Art; Building Technology; and Design and Computation."
        ),
        "delivery_format": "in_person",
        "department": "Department of Architecture",
    },
    {
        "slug": "mit-dusp-phd",
        "school": "School of Architecture and Planning",
        "program_name": "Urban Studies and Planning PhD",
        "degree_type": "phd",
        "description": (
            "Advanced research doctorate (PhD) in urban planning or urban studies; nearly all "
            "admitted students hold a prior master's degree, and the program requires qualifying "
            "exams plus a dissertation."
        ),
        "delivery_format": "in_person",
        "department": "Department of Urban Studies and Planning (DUSP)",
    },
    {
        "slug": "mit-mediaarts-phd",
        "school": "School of Architecture and Planning",
        "program_name": "Media Arts and Sciences PhD",
        "degree_type": "phd",
        "description": (
            "Doctor of Philosophy in Media Arts and Sciences offered through the MIT Media Lab."
        ),
        "delivery_format": "in_person",
        "department": "Program in Media Arts and Sciences (MIT Media Lab)",
    },
    {
        "slug": "mit-lgo-mba-sm",
        "school": "MIT Sloan School of Management",
        "program_name": "Leaders for Global Operations (LGO) — MBA + SM in Engineering",
        "degree_type": "masters",
        "duration_months": 24,
        "description": (
            "Two-year dual-degree program jointly conferred by MIT Sloan and the School of "
            "Engineering, awarding an MBA plus an SM (Master of Science) in an engineering field,"
            " focused on operations, manufacturing, and analytics leadership."
        ),
        "delivery_format": "in_person",
        "department": "Leaders for Global Operations Program (Sloan + School of Engineering)",
        "nonstandard_rates": True,
    },
    {
        "slug": "mit-sloan-emba",
        "school": "MIT Sloan School of Management",
        "program_name": "MIT Executive MBA (EMBA)",
        "degree_type": "masters",
        "duration_months": 20,
        "description": (
            "Twenty-month MBA for mid-career professionals (typically 10+ years' experience) who "
            "continue working full-time while completing the program through periodic on-campus "
            "modules."
        ),
        "delivery_format": "hybrid",
        "department": "MIT Sloan School of Management",
        "nonstandard_rates": True,
    },
    {
        "slug": "mit-sloan-msms",
        "school": "MIT Sloan School of Management",
        "program_name": "Master of Science in Management Studies (MSMS)",
        "degree_type": "masters",
        "duration_months": 9,
        "description": (
            "Nine-month, STEM-designated SM in Management Studies for graduates/current students "
            "of partner and affiliate international business schools; customizable curriculum "
            "culminating in a thesis."
        ),
        "delivery_format": "in_person",
        "department": "MIT Sloan School of Management",
        "nonstandard_rates": True,
    },
    {
        "slug": "mit-scm-residential-sm",
        "school": "School of Engineering",
        "program_name": (
            "Supply Chain Management Master's — Residential (Master of Applied Science)"
        ),
        "degree_type": "masters",
        "duration_months": 10,
        "description": (
            "Ten-month, on-campus master's degree in supply chain management administered by the "
            "MIT Center for Transportation & Logistics. (Existing list has SCM MicroMasters "
            "certificate; this is the full residential degree.)"
        ),
        "delivery_format": "in_person",
        "department": "MIT Center for Transportation & Logistics",
        "nonstandard_rates": True,
    },
    {
        "slug": "mit-scm-blended-sm",
        "school": "School of Engineering",
        "program_name": "Supply Chain Management Master's — Blended (Master of Applied Science)",
        "degree_type": "masters",
        "duration_months": 5,
        "description": (
            "Blended master's pathway open to holders of the MITx MicroMasters in Supply Chain "
            "Management, combining online coursework with five months in residence at MIT."
        ),
        "delivery_format": "hybrid",
        "department": "MIT Center for Transportation & Logistics",
        "nonstandard_rates": True,
    },
    {
        "slug": "mit-orc-sm",
        "school": "MIT Sloan School of Management",
        "program_name": "Operations Research SM (Master of Science in Operations Research)",
        "degree_type": "masters",
        "description": (
            "Master of Science in Operations Research offered through the interdepartmental "
            "Operations Research Center, where students engage in research from the start."
        ),
        "delivery_format": "in_person",
        "department": "Operations Research Center (Sloan + School of Engineering)",
    },
    {
        "slug": "mit-orc-phd",
        "school": "MIT Sloan School of Management",
        "program_name": "Operations Research PhD",
        "degree_type": "phd",
        "description": (
            "Doctoral program (PhD) in Operations Research offered through the interdepartmental "
            "Operations Research Center."
        ),
        "delivery_format": "in_person",
        "department": "Operations Research Center (Sloan + School of Engineering)",
    },
    {
        "slug": "mit-idm-sm",
        "school": "School of Engineering",
        "program_name": "Integrated Design and Management (IDM) — SM in Engineering and Management",
        "degree_type": "masters",
        "duration_months": 24,
        "description": (
            "Master's program teaching an integrated, systems-centered, design-led approach to "
            "sociotechnical problems; 16-24 months with full- and part-time options and a thesis,"
            " jointly grounded in engineering, management, and design."
        ),
        "delivery_format": "hybrid",
        "department": (
            "Integrated Design and Management Program (System Design & Management / School of "
            "Engineering + Sloan)"
        ),
        "nonstandard_rates": True,
    },
    {
        "slug": "mit-dedp-masc",
        "school": "School of Humanities, Arts, and Social Sciences",
        "program_name": "Data, Economics, and Design of Policy — Master of Applied Science (MASc)",
        "degree_type": "masters",
        "duration_months": 5,
        "description": (
            "Five-month blended Master of Applied Science available only to students who complete"
            " the MITx MicroMasters credential in DEDP; combines online coursework with "
            "in-residence study and a summer policy internship, with International Development "
            "and Public Policy tracks."
        ),
        "delivery_format": "hybrid",
        "department": "Department of Economics",
        "nonstandard_rates": True,
    },
    {
        "slug": "mit-music-tech-sm",
        "school": "School of Humanities, Arts, and Social Sciences",
        "program_name": "Music Technology and Computation — SM / Master of Applied Science",
        "degree_type": "masters",
        "description": (
            "Graduate program offering both an SM (thesis-based, 92 units) and a Master of "
            "Applied Science (capstone-based, 92 units) in music technology and computation. "
            "(Existing mit-mediaarts-sm is separate; verify against any prior music-tech entry.)"
        ),
        "delivery_format": "in_person",
        "department": "Music and Theater Arts Section",
    },
    {
        "slug": "mit-csb-phd",
        "school": "School of Engineering",
        "program_name": "Computational and Systems Biology PhD (CSB)",
        "degree_type": "phd",
        "description": (
            "Interdisciplinary doctoral program (PhD) in computational and systems biology, "
            "listed as a catalog degree chart."
        ),
        "delivery_format": "in_person",
        "department": "Computational and Systems Biology Program (interdisciplinary)",
    },
    {
        "slug": "mit-microbiology-phd",
        "school": "School of Science",
        "program_name": "Microbiology PhD",
        "degree_type": "phd",
        "description": (
            "Interdisciplinary doctoral program (PhD) in microbiology, listed as a catalog degree"
            " chart."
        ),
        "delivery_format": "in_person",
        "department": "Microbiology Graduate Program (interdisciplinary)",
    },
    {
        "slug": "mit-bio-oceanography-phd",
        "school": "School of Science",
        "program_name": "Biological Oceanography PhD (MIT-WHOI Joint Program)",
        "degree_type": "phd",
        "description": (
            "Doctoral program (PhD) in biological oceanography offered jointly with the Woods "
            "Hole Oceanographic Institution, listed as a catalog degree chart."
        ),
        "delivery_format": "in_person",
        "department": (
            "MIT-WHOI Joint Program in Oceanography / Earth, Atmospheric and Planetary Sciences"
        ),
    },
    {
        "slug": "mit-phys-oceanography-phd",
        "school": "School of Science",
        "program_name": "Physical Oceanography PhD (MIT-WHOI Joint Program)",
        "degree_type": "phd",
        "description": (
            "Doctoral program (PhD) in physical oceanography offered jointly with the Woods Hole "
            "Oceanographic Institution, listed as a catalog degree chart."
        ),
        "delivery_format": "in_person",
        "department": (
            "MIT-WHOI Joint Program in Oceanography / Earth, Atmospheric and Planetary Sciences"
        ),
    },
    {
        "slug": "mit-transportation-sm",
        "school": "School of Engineering",
        "program_name": "Transportation SM (Master of Science in Transportation)",
        "degree_type": "masters",
        "description": (
            "Master of Science in Transportation offered through MIT's interdepartmental "
            "transportation program."
        ),
        "delivery_format": "in_person",
        "department": "Interdepartmental Program in Transportation",
    },
    {
        "slug": "mit-transportation-phd",
        "school": "School of Engineering",
        "program_name": "Transportation PhD/ScD",
        "degree_type": "phd",
        "description": (
            "Doctoral program (PhD/ScD) in transportation offered through MIT's interdepartmental"
            " transportation program."
        ),
        "delivery_format": "in_person",
        "department": "Interdepartmental Program in Transportation",
    },
    {
        "slug": "mit-comp-cognition-meng",
        "school": "MIT Stephen A. Schwarzman College of Computing",
        "program_name": "Computation and Cognition MEng (Course 6-9P)",
        "degree_type": "masters",
        "description": (
            "Master of Engineering (Course 6-9P) for undergraduates in the Computation and "
            "Cognition major, jointly offered by EECS and Brain and Cognitive Sciences."
        ),
        "delivery_format": "in_person",
        "department": "EECS / Brain and Cognitive Sciences (interdisciplinary)",
    },
    {
        "slug": "mit-cs-molbio-meng",
        "school": "MIT Stephen A. Schwarzman College of Computing",
        "program_name": "Computer Science and Molecular Biology MEng (Course 6-7P)",
        "degree_type": "masters",
        "description": (
            "Master of Engineering (Course 6-7P) in Computer Science and Molecular Biology, "
            "jointly offered by EECS and the Department of Biology."
        ),
        "delivery_format": "in_person",
        "department": "EECS / Department of Biology (interdisciplinary)",
    },
    {
        "slug": "mit-cs-econ-data-meng",
        "school": "MIT Stephen A. Schwarzman College of Computing",
        "program_name": "Computer Science, Economics, and Data Science MEng (Course 6-14P)",
        "degree_type": "masters",
        "description": (
            "Master of Engineering (Course 6-14P) in Computer Science, Economics, and Data "
            "Science, jointly offered by EECS and Economics."
        ),
        "delivery_format": "in_person",
        "department": "EECS / Department of Economics (interdisciplinary)",
    },
    {
        "slug": "mit-cse-sm",
        "school": "MIT Stephen A. Schwarzman College of Computing",
        "program_name": "Computational Science and Engineering SM (Master of Science)",
        "degree_type": "masters",
        "description": (
            "Master of Science in Computational Science and Engineering. (Existing list has "
            "mit-cse-phd; this standalone SM is distinct.)"
        ),
        "delivery_format": "in_person",
        "department": "Center for Computational Science and Engineering (interdisciplinary)",
    },
    {
        "slug": "mit-hst-memp-phd",
        "school": "School of Engineering",
        "program_name": "Medical Engineering and Medical Physics PhD (MEMP, Harvard-MIT HST)",
        "degree_type": "phd",
        "description": (
            "Doctoral program (PhD) in Medical Engineering and Medical Physics through the "
            "Harvard-MIT HST program, in which students ground themselves in a technical "
            "discipline while studying biomedical science alongside MD students and experiencing "
            "clinical training."
        ),
        "delivery_format": "in_person",
        "department": (
            "Harvard-MIT Program in Health Sciences and Technology (HST) / Institute for Medical "
            "Engineering and Science (IMES)"
        ),
    },
    {
        "slug": "mit-art-design-bs",
        "school": "School of Architecture and Planning",
        "program_name": "Bachelor of Science in Art and Design (Course 4-B)",
        "degree_type": "bachelors",
        "description": (
            "Undergraduate Bachelor of Science in Art and Design (Course 4-B) offered by the "
            "Department of Architecture."
        ),
        "delivery_format": "in_person",
        "department": "Department of Architecture",
    },
    {
        "slug": "mit-chem-bio-bs",
        "school": "School of Science",
        "program_name": "Bachelor of Science in Chemistry and Biology (Course 5-7)",
        "degree_type": "bachelors",
        "description": (
            "Joint undergraduate Bachelor of Science in Chemistry and Biology (Course 5-7)."
        ),
        "delivery_format": "in_person",
        "department": "Departments of Chemistry and Biology (joint)",
    },
    {
        "slug": "mit-climate-bs",
        "school": "School of Engineering",
        "program_name": (
            "Bachelor of Science in Climate System Science and Engineering (Course 1-12)"
        ),
        "degree_type": "bachelors",
        "description": (
            "Joint undergraduate Bachelor of Science in Climate System Science and Engineering "
            "(Course 1-12), offered by CEE and EAPS."
        ),
        "delivery_format": "in_person",
        "department": "Department of Civil and Environmental Engineering / EAPS (joint)",
    },
    {
        "slug": "mit-cs-molbio-bs",
        "school": "MIT Stephen A. Schwarzman College of Computing",
        "program_name": (
            "Bachelor of Science in Computer Science and Molecular Biology (Course 6-7)"
        ),
        "degree_type": "bachelors",
        "description": (
            "Joint undergraduate Bachelor of Science in Computer Science and Molecular Biology "
            "(Course 6-7)."
        ),
        "delivery_format": "in_person",
        "department": "EECS / Department of Biology (joint)",
    },
    {
        "slug": "mit-uspcs-bs",
        "school": "School of Architecture and Planning",
        "program_name": (
            "Bachelor of Science in Urban Science and Planning with Computer Science (Course "
            "11-6)"
        ),
        "degree_type": "bachelors",
        "description": (
            "Joint undergraduate Bachelor of Science in Urban Science and Planning with Computer "
            "Science (Course 11-6), offered by DUSP and EECS."
        ),
        "delivery_format": "in_person",
        "department": "Department of Urban Studies and Planning / EECS (joint)",
    },
    {
        "slug": "mit-eecs-6-5-bs",
        "school": "MIT Stephen A. Schwarzman College of Computing",
        "program_name": "Bachelor of Science in Electrical Engineering with Computing (Course 6-5)",
        "degree_type": "bachelors",
        "description": (
            "Undergraduate Bachelor of Science in Electrical Engineering with Computing (Course "
            "6-5)."
        ),
        "delivery_format": "in_person",
        "department": "Department of Electrical Engineering and Computer Science (EECS)",
    },
    {
        "slug": "mit-cheme-10b-bs",
        "school": "School of Engineering",
        "program_name": "Bachelor of Science in Chemical-Biological Engineering (Course 10-B)",
        "degree_type": "bachelors",
        "description": (
            "Undergraduate Bachelor of Science in Chemical-Biological Engineering (Course 10-B)."
        ),
        "delivery_format": "in_person",
        "department": "Department of Chemical Engineering",
    },
    {
        "slug": "mit-meche-2oe-bs",
        "school": "School of Engineering",
        "program_name": "Bachelor of Science in Mechanical and Ocean Engineering (Course 2-OE)",
        "degree_type": "bachelors",
        "description": (
            "Undergraduate Bachelor of Science in Mechanical and Ocean Engineering (Course 2-OE)."
        ),
        "delivery_format": "in_person",
        "department": "Department of Mechanical Engineering",
    },
    {
        "slug": "mit-archaeology-materials-bs",
        "school": "School of Engineering",
        "program_name": "Bachelor of Science in Archaeology and Materials (Course 3-C)",
        "degree_type": "bachelors",
        "description": (
            "Undergraduate Bachelor of Science in Archaeology and Materials (Course 3-C)."
        ),
        "delivery_format": "in_person",
        "department": "Department of Materials Science and Engineering (DMSE)",
    },
    {
        "slug": "mit-math-econ-bs",
        "school": "School of Humanities, Arts, and Social Sciences",
        "program_name": "Bachelor of Science in Mathematical Economics (Course 14-2)",
        "degree_type": "bachelors",
        "description": (
            "Undergraduate Bachelor of Science in Mathematical Economics (Course 14-2), combining"
            " microeconomics, macroeconomics, econometrics, real analysis, and mathematics "
            "electives."
        ),
        "delivery_format": "in_person",
        "department": "Department of Economics",
    },
    {
        "slug": "mit-philosophy-bs",
        "school": "School of Humanities, Arts, and Social Sciences",
        "program_name": "Bachelor of Science in Philosophy (Course 24-1)",
        "degree_type": "bachelors",
        "description": (
            "Undergraduate Bachelor of Science in Philosophy (Course 24-1). (Existing list has a "
            "combined Linguistics and Philosophy BS, Course 24-2; this is the standalone "
            "Philosophy major.)"
        ),
        "delivery_format": "in_person",
        "department": "Department of Linguistics and Philosophy",
    },
    {
        "slug": "mit-theater-arts-bs",
        "school": "School of Humanities, Arts, and Social Sciences",
        "program_name": "Bachelor of Science in Theater Arts (Course 21T)",
        "degree_type": "bachelors",
        "description": "Undergraduate Bachelor of Science in Theater Arts (Course 21T).",
        "delivery_format": "in_person",
        "department": "Music and Theater Arts Section",
    },
]
PROGRAMS.extend(_PROGRAMS_RESEARCH)
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

_WEBSITE_BY_SLUG.update({
    "mit-biology-phd": "https://biology.mit.edu/graduate/",
    "mit-bcs-phd": "https://catalog.mit.edu/degree-charts/phd-brain-cognitive-sciences/",
    "mit-eaps-phd": (
        "https://catalog.mit.edu/degree-charts/phd-earth-atmospheric-planetary-sciences/"
    ),
    "mit-be-phd": "https://catalog.mit.edu/degree-charts/phd-biological-engineering/",
    "mit-cee-sm": "https://catalog.mit.edu/degree-charts/master-civil-environmental-engineering/",
    "mit-cee-meng": "https://cee.mit.edu/graduate/",
    "mit-cee-phd": "https://catalog.mit.edu/degree-charts/phd-civil-environmental-engineering/",
    "mit-dmse-phd": "https://catalog.mit.edu/degree-charts/phd-materials-science-engineering/",
    "mit-nse-phd": "https://catalog.mit.edu/degree-charts/phd-nuclear-science-engineering/",
    "mit-eecs-meng": (
        "https://catalog.mit.edu/degree-charts/master-electrical-engineering-computer-science-cou"
        "rse-6-p/"
    ),
    "mit-cheme-phd": "https://cheme.mit.edu/academics/graduate-students/",
    "mit-cheme-phdcep": "https://cheme.mit.edu/academics/graduate-students/",
    "mit-cheme-mscep": "https://cheme.mit.edu/academics/graduate-students/",
    "mit-meche-meng-mfg": "https://meche.mit.edu/education/graduate",
    "mit-meche-sm-name": "https://meche.mit.edu/education/graduate",
    "mit-ses-phd": "https://catalog.mit.edu/degree-charts/phd-social-engineering-systems/",
    "mit-linguistics-phd": (
        "https://catalog.mit.edu/schools/humanities-arts-social-sciences/linguistics-philosophy/"
    ),
    "mit-philosophy-phd": (
        "https://catalog.mit.edu/schools/humanities-arts-social-sciences/linguistics-philosophy/"
    ),
    "mit-linguistics-sm": (
        "https://catalog.mit.edu/schools/humanities-arts-social-sciences/linguistics-philosophy/"
    ),
    "mit-political-science-phd": "https://polisci.mit.edu/graduate",
    "mit-hasts-phd": "https://hasts.mit.edu/",
    "mit-smarchs-sm": "https://catalog.mit.edu/degree-charts/master-architecture-studies/",
    "mit-smbt-sm": "https://catalog.mit.edu/schools/architecture-planning/architecture/",
    "mit-smact-sm": "https://catalog.mit.edu/degree-charts/master-art-culture-technology/",
    "mit-architecture-phd": "https://catalog.mit.edu/schools/architecture-planning/architecture/",
    "mit-dusp-phd": "https://catalog.mit.edu/schools/architecture-planning/urban-studies-planning/",
    "mit-mediaarts-phd": (
        "https://catalog.mit.edu/schools/architecture-planning/media-arts-sciences/"
    ),
    "mit-lgo-mba-sm": "https://lgo.mit.edu/",
    "mit-sloan-emba": "https://mitsloan.mit.edu/emba",
    "mit-sloan-msms": (
        "https://mitsloan.mit.edu/msms/master-science-management-studies/explore-program"
    ),
    "mit-scm-residential-sm": "https://scm.mit.edu/",
    "mit-scm-blended-sm": "https://scm.mit.edu/",
    "mit-orc-sm": (
        "https://catalog.mit.edu/interdisciplinary/graduate-programs/operations-research/"
    ),
    "mit-orc-phd": (
        "https://catalog.mit.edu/interdisciplinary/graduate-programs/operations-research/"
    ),
    "mit-idm-sm": "https://idm.mit.edu/admissions/",
    "mit-dedp-masc": (
        "https://catalog.mit.edu/degree-charts/master-applied-science-data-economics-design-polic"
        "y/"
    ),
    "mit-music-tech-sm": (
        "https://catalog.mit.edu/degree-charts/master-music-technology-computation/"
    ),
    "mit-csb-phd": "https://catalog.mit.edu/degree-charts/phd-computational-systems-biology/",
    "mit-microbiology-phd": "https://catalog.mit.edu/degree-charts/phd-microbiology/",
    "mit-bio-oceanography-phd": (
        "https://catalog.mit.edu/degree-charts/phd-biological-oceanography/"
    ),
    "mit-phys-oceanography-phd": "https://catalog.mit.edu/degree-charts/phd-physical-oceanography/",
    "mit-transportation-sm": "https://catalog.mit.edu/degree-charts/master-transportation/",
    "mit-transportation-phd": "https://catalog.mit.edu/degree-charts/phd-transportation/",
    "mit-comp-cognition-meng": (
        "https://catalog.mit.edu/interdisciplinary/graduate-programs/computation-cognition/"
    ),
    "mit-cs-molbio-meng": (
        "https://catalog.mit.edu/interdisciplinary/graduate-programs/computer-science-molecular-b"
        "iology/"
    ),
    "mit-cs-econ-data-meng": (
        "https://catalog.mit.edu/interdisciplinary/graduate-programs/computer-science-economics-d"
        "ata-science/"
    ),
    "mit-cse-sm": "https://catalog.mit.edu/degree-charts/master-computational-science-engineering/",
    "mit-hst-memp-phd": "https://hst.mit.edu/academic-programs",
    "mit-art-design-bs": "https://catalog.mit.edu/degree-charts/architecture-course-4-b/",
    "mit-chem-bio-bs": "https://catalog.mit.edu/degree-charts/chemistry-biology-course-5-7/",
    "mit-climate-bs": (
        "https://catalog.mit.edu/degree-charts/climate-system-science-engineering-course-1-12/"
    ),
    "mit-cs-molbio-bs": (
        "https://catalog.mit.edu/degree-charts/computer-science-molecular-biology-course-6-7/"
    ),
    "mit-uspcs-bs": (
        "https://catalog.mit.edu/degree-charts/urban-science-planning-computer-science-11-6"
    ),
    "mit-eecs-6-5-bs": (
        "https://catalog.mit.edu/degree-charts/electrical-engineering-computing-6-5/"
    ),
    "mit-cheme-10b-bs": (
        "https://catalog.mit.edu/degree-charts/chemical-biological-engineering-course-10-b/"
    ),
    "mit-meche-2oe-bs": (
        "https://catalog.mit.edu/degree-charts/mechanical-ocean-engineering-course-2-oe/"
    ),
    "mit-archaeology-materials-bs": (
        "https://catalog.mit.edu/degree-charts/archaeology-materials-course-3-c/"
    ),
    "mit-math-econ-bs": "https://catalog.mit.edu/degree-charts/mathematical-economics-course-14-2/",
    "mit-philosophy-bs": "https://catalog.mit.edu/degree-charts/philosophy-course-24-1/",
    "mit-theater-arts-bs": "https://catalog.mit.edu/degree-charts/theater-arts-course-21t/",
})

_DEPT_BY_SLUG.update({
    "mit-biology-phd": "biology",
    "mit-bcs-phd": "bcs",
    "mit-eaps-phd": "eaps",
    "mit-be-phd": "be",
    "mit-cee-sm": "cee",
    "mit-cee-meng": "cee",
    "mit-cee-phd": "cee",
    "mit-dmse-phd": "dmse",
    "mit-nse-phd": "nse",
    "mit-eecs-meng": "eecs",
    "mit-cheme-phd": "cheme",
    "mit-cheme-phdcep": "cheme",
    "mit-cheme-mscep": "cheme",
    "mit-meche-meng-mfg": "meche",
    "mit-meche-sm-name": "meche",
    "mit-linguistics-phd": "ling_phil",
    "mit-linguistics-sm": "ling_phil",
    "mit-philosophy-phd": "ling_phil",
    "mit-philosophy-bs": "ling_phil",
    "mit-political-science-phd": "polisci",
    "mit-smarchs-sm": "architecture",
    "mit-smbt-sm": "architecture",
    "mit-smact-sm": "architecture",
    "mit-architecture-phd": "architecture",
    "mit-dusp-phd": "dusp",
    "mit-mediaarts-phd": "media_lab",
    "mit-lgo-mba-sm": "sloan",
    "mit-sloan-emba": "sloan",
    "mit-sloan-msms": "sloan",
    "mit-orc-sm": "sloan",
    "mit-orc-phd": "sloan",
    "mit-csb-phd": "biology",
    "mit-microbiology-phd": "biology",
    "mit-bio-oceanography-phd": "biology",
    "mit-phys-oceanography-phd": "eaps",
    "mit-transportation-sm": "cee",
    "mit-transportation-phd": "cee",
    "mit-cse-sm": "ccse",
    "mit-ses-phd": "idss",
    "mit-art-design-bs": "architecture",
    "mit-climate-bs": "cee",
    "mit-eecs-6-5-bs": "eecs",
    "mit-cheme-10b-bs": "cheme",
    "mit-meche-2oe-bs": "meche",
    "mit-archaeology-materials-bs": "dmse",
    "mit-math-econ-bs": "economics",
    "mit-theater-arts-bs": "music",
    "mit-music-tech-sm": "music",
    "mit-comp-cognition-meng": "eecs",
    "mit-cs-molbio-meng": "eecs",
    "mit-cs-molbio-bs": "eecs",
    "mit-cs-econ-data-meng": "eecs",
    "mit-chem-bio-bs": "chemistry",
    "mit-uspcs-bs": "dusp",
})
_JOINT_FACULTY.update({
    "mit-comp-cognition-meng": ["eecs", "bcs"],
    "mit-cs-molbio-meng": ["eecs", "biology"],
    "mit-cs-molbio-bs": ["eecs", "biology"],
    "mit-cs-econ-data-meng": ["eecs", "economics"],
    "mit-chem-bio-bs": ["chemistry", "biology"],
    "mit-uspcs-bs": ["dusp", "eecs"],
})
_PROG_CONTENT_EXTRA.update({
    "mit-hasts-phd": {
        "news_rss": "https://news.mit.edu/rss/school/humanities-arts-and-social-sciences",
        "news_url": "https://news.mit.edu/topic/school-humanities-arts-and-social-sciences",
        "keywords": [
            "history of science",
            "anthropology",
            "sts",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=history+of+science",
            "type": "ical",
        },
    },
    "mit-lgo-mba-sm": {
        "news_rss": "https://news.mit.edu/rss/school/management",
        "news_url": "https://news.mit.edu/topic/sloan-school-management",
        "keywords": [
            "leaders for global operations",
            "lgo",
            "operations",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=operations",
            "type": "ical",
        },
    },
    "mit-sloan-emba": {
        "news_rss": "https://news.mit.edu/rss/school/management",
        "news_url": "https://news.mit.edu/topic/sloan-school-management",
        "keywords": [
            "executive mba",
            "emba",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=executive+mba",
            "type": "ical",
        },
    },
    "mit-sloan-msms": {
        "news_rss": "https://news.mit.edu/rss/school/management",
        "news_url": "https://news.mit.edu/topic/sloan-school-management",
        "keywords": [
            "management studies",
            "msms",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=management+studies",
            "type": "ical",
        },
    },
    "mit-scm-residential-sm": {
        "news_rss": "https://news.mit.edu/rss/school/engineering",
        "news_url": "https://news.mit.edu/topic/school-engineering",
        "keywords": [
            "supply chain",
            "logistics",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=supply+chain",
            "type": "ical",
        },
    },
    "mit-scm-blended-sm": {
        "news_rss": "https://news.mit.edu/rss/school/engineering",
        "news_url": "https://news.mit.edu/topic/school-engineering",
        "keywords": [
            "supply chain",
            "logistics",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=supply+chain",
            "type": "ical",
        },
    },
    "mit-orc-sm": {
        "news_rss": "https://news.mit.edu/rss/school/management",
        "news_url": "https://news.mit.edu/topic/sloan-school-management",
        "keywords": [
            "operations research",
            "optimization",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=operations+research",
            "type": "ical",
        },
    },
    "mit-orc-phd": {
        "news_rss": "https://news.mit.edu/rss/school/management",
        "news_url": "https://news.mit.edu/topic/sloan-school-management",
        "keywords": [
            "operations research",
            "optimization",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=operations+research",
            "type": "ical",
        },
    },
    "mit-idm-sm": {
        "news_rss": "https://news.mit.edu/rss/school/engineering",
        "news_url": "https://news.mit.edu/topic/school-engineering",
        "keywords": [
            "integrated design",
            "design and management",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=integrated+design",
            "type": "ical",
        },
    },
    "mit-dedp-masc": {
        "news_rss": "https://news.mit.edu/rss/school/humanities-arts-and-social-sciences",
        "news_url": "https://news.mit.edu/topic/school-humanities-arts-and-social-sciences",
        "keywords": [
            "development economics",
            "policy",
            "j-pal",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=development+economics",
            "type": "ical",
        },
    },
    "mit-music-tech-sm": {
        "news_rss": "https://news.mit.edu/rss/school/humanities-arts-and-social-sciences",
        "news_url": "https://news.mit.edu/topic/school-humanities-arts-and-social-sciences",
        "keywords": [
            "music technology",
            "music computation",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=music+technology",
            "type": "ical",
        },
    },
    "mit-theater-arts-bs": {
        "news_rss": "https://news.mit.edu/rss/school/humanities-arts-and-social-sciences",
        "news_url": "https://news.mit.edu/topic/school-humanities-arts-and-social-sciences",
        "keywords": [
            "theater",
            "performing arts",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=theater",
            "type": "ical",
        },
    },
    "mit-hst-memp-phd": {
        "news_rss": "https://news.mit.edu/rss/school/engineering",
        "news_url": "https://news.mit.edu/topic/school-engineering",
        "keywords": [
            "medical engineering",
            "medical physics",
            "health sciences",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=medical+engineering",
            "type": "ical",
        },
    },
    "mit-cse-sm": {
        "news_rss": "https://news.mit.edu/rss/topic/computing",
        "news_url": "https://news.mit.edu/topic/computing",
        "keywords": [
            "computational science",
            "simulation",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=computational+science",
            "type": "ical",
        },
    },
    "mit-ses-phd": {
        "news_rss": "https://news.mit.edu/rss/topic/computing",
        "news_url": "https://news.mit.edu/topic/computing",
        "keywords": [
            "social and engineering systems",
            "data",
            "policy",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=data+systems+society",
            "type": "ical",
        },
    },
    "mit-mediaarts-phd": {
        "news_rss": "https://news.mit.edu/rss/school/architecture-and-planning",
        "news_url": "https://news.mit.edu/topic/school-architecture-and-planning",
        "keywords": [
            "media lab",
            "media arts",
            "human-computer interaction",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=media+lab",
            "type": "ical",
        },
    },
    "mit-philosophy-bs": {
        "news_rss": "https://news.mit.edu/topic/mitphilosophy-rss.xml",
        "news_url": "https://news.mit.edu/topic/philosophy",
        "keywords": [
            "philosophy",
            "ethics",
            "epistemology",
            "logic",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=philosophy",
            "type": "ical",
        },
    },
    "mit-philosophy-phd": {
        "news_rss": "https://news.mit.edu/topic/mitphilosophy-rss.xml",
        "news_url": "https://news.mit.edu/topic/philosophy",
        "keywords": [
            "philosophy",
            "ethics",
            "epistemology",
            "logic",
        ],
        "events_feed": {
            "url": "https://calendar.mit.edu/search/events.ics?search=philosophy",
            "type": "ical",
        },
    },
})


# ── Conformance bookkeeping ────────────────────────────────────────────────
_SCHOOL_ABOUT_REQUIRED = ("founded", "leadership", "faculty", "research_centers")


def _school_omitted(about: dict) -> list[str]:
    """Required about_detail fields this run could not verify for a school."""
    return [f"about_detail.{k}" for k in _SCHOOL_ABOUT_REQUIRED if not about.get(k)]


def _program_omitted(p: Program) -> list[str]:
    """Required program fields that remain unverified after this run's research.

    Derived against the manifest itself (via check_conformance) so the omitted
    list always names exactly the required paths the research could not fill —
    each was attempted from official sources before being recorded here.
    """
    snap = {
        "program_name": p.program_name,
        "degree_type": p.degree_type,
        "duration_months": p.duration_months,
        "delivery_format": p.delivery_format,
        "description_text": p.description_text,
        "website_url": p.website_url,
        "department": p.department,
        "tracks": p.tracks,
        "application_requirements": p.application_requirements,
        "cost_data": p.cost_data,
        "outcomes_data": {k: v for k, v in (p.outcomes_data or {}).items() if k != "_standard"},
        "class_profile": p.class_profile,
        "faculty_contacts": p.faculty_contacts,
        "external_reviews": p.external_reviews,
        "content_sources": p.content_sources,
    }
    return check_conformance("program", snap).missing_fields


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich MIT to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when MIT is absent — safe on fresh/CI databases.
    """
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    # Shallow-merge JSONB: every sub-object we provide is complete.
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    # Every named research center from the school About research keeps its
    # official URL in the institution's research.lab_links map.
    research = dict(school_outcomes.get("research") or {})
    lab_links = dict(research.get("lab_links") or {})
    lab_links.update(_SCHOOL_LAB_LINKS)
    research["lab_links"] = lab_links
    school_outcomes["research"] = research
    # Every required institution field is filled from a cited source; nothing omitted.
    school_outcomes["_standard"] = _standard()
    inst.school_outcomes = school_outcomes
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    # Lead the gallery with a real campus photo. The detail-page hero shows the
    # first RASTER image in media_gallery; the gallery otherwise holds only the
    # logo SVG, so the hero fell back to a blank gradient. Idempotent (dedupe +
    # prepend), and the logo is preserved behind it.
    _gallery = [u for u in (inst.media_gallery or []) if u != _CAMPUS_PHOTO]
    inst.media_gallery = [_CAMPUS_PHOTO, *_gallery]
    # Public channel feeds → auto-sourced Updates (news) + Events (calendar).
    # Institution-wide (no keywords) → kept wholesale. Social handles verified
    # official from www.mit.edu / socialmediahub.mit.edu (2026-06-09).
    inst.content_sources = {
        "news_rss": "https://news.mit.edu/rss/feed",
        "events_feed": {"url": "https://calendar.mit.edu/calendar.ics", "type": "ical"},
        "social": {
            "instagram": "https://www.instagram.com/mit/",
            "linkedin": "https://www.linkedin.com/school/mit/",
            "x": "https://x.com/mit",
            "youtube": "https://www.youtube.com/mit",
            "facebook": "https://www.facebook.com/MITnews",
        },
    }
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
        # Every school carries a sourced About tab (founded · leadership · notable
        # faculty · research centers) and, where verified, its own keyword-relevant
        # feeds + official social links. The conformance stamp records what could
        # not be verified for a given school.
        about = dict(_ABOUT_BY_SCHOOL.get(spec["name"]) or {})
        about["_standard"] = _standard(_school_omitted(about))
        sc.about_detail = about
        if spec["name"] in _CONTENT_BY_SCHOOL:
            sc.content_sources = _CONTENT_BY_SCHOOL[spec["name"]]
        by_name[spec["name"]] = sc
    # Drop legacy schools — programs.school_id is ON DELETE SET NULL, so this
    # is FK-safe (any orphaned programs are handled by the program reconcile).
    for name, sc in existing.items():
        if name not in canonical_names:
            session.delete(sc)
    session.flush()
    return by_name


def _program_has_dependents(session: Session, program_id) -> bool:
    """True if any FK in the schema references this programs row (delete unsafe).

    Introspects FKs pointing at programs.id rather than hard-coding table names,
    so it stays correct as the schema grows.
    """
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
        p = existing.get(spec["slug"])
        if p is None:
            p = Program(
                institution_id=inst.id,
                program_name=spec["program_name"],
                degree_type=spec["degree_type"],
                slug=spec["slug"],
            )
            session.add(p)
        # Full official degree name as the title (falls back to the short label).
        p.program_name = _FULL_NAME_BY_SLUG.get(spec["slug"]) or spec["program_name"]
        p.degree_type = spec["degree_type"]
        p.duration_months = spec.get("duration_months")
        p.description_text = _DESC_RICH_BY_SLUG.get(spec["slug"]) or spec["description"]
        # Official program-page URL (read-more link on the program page).
        p.website_url = _WEBSITE_BY_SLUG.get(spec["slug"])
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        # MBAn keeps its hand-built feed set; every other program carries its
        # department's verified MIT News feed (or its school's, keyword-gated).
        if spec["slug"] == "mit-sloan-mban":
            p.content_sources = _MBAN_CONTENT
        else:
            p.content_sources = _content_for(spec["slug"])
        if spec.get("department"):
            p.department = spec["department"]
        p.delivery_format = spec.get("delivery_format", "in_person")
        # Tuition by program (MIT official 2025-26 rates). Standard degree
        # programs pay MIT's single published tuition; PhDs are fully funded;
        # the Sloan MBA has its own professional rate; online / MicroMasters /
        # certificate pricing varies per course → left null rather than guessed.
        # Program-specific cost (official) takes precedence over the standard rate.
        cost_override = _COST_BY_SLUG.get(spec["slug"])
        if cost_override is not None:
            p.tuition = cost_override.get("tuition_usd")
            p.cost_data = dict(cost_override)
        else:
            if spec.get("nonstandard_rates"):
                # Professional programs charge their own (unverified) rate —
                # tuition is omitted rather than defaulted to the standard rate.
                p.tuition = None
            elif spec.get("tuition") is not None:
                p.tuition = spec["tuition"]
            elif spec["slug"] == "mit-sloan-mba":
                p.tuition = 89000
            elif spec["degree_type"] == "phd":
                p.tuition = 0
            elif p.delivery_format == "online" or spec["degree_type"] == "certificate":
                p.tuition = None
            else:
                p.tuition = 64730
            p.cost_data = (
                {
                    "tuition_usd": p.tuition,
                    "funded": spec["degree_type"] == "phd",
                    "source": "MIT Student Financial Services",
                    "source_url": "https://sfs.mit.edu/",
                    "year": "2025-26",
                }
                if (
                    (p.tuition is not None or spec["degree_type"] == "phd")
                    and not spec.get("nonstandard_rates")
                )
                else None
            )
        # Program-specific admission requirements (official) take precedence.
        req_override = _REQ_BY_SLUG.get(spec["slug"])
        if req_override is not None:
            p.application_requirements = dict(req_override)
        elif spec["slug"] == "mit-sloan-mba":
            p.application_requirements = dict(_REQ_MBA)
        elif spec.get("nonstandard_rates"):
            p.application_requirements = dict(_REQ_PRO)
        elif p.delivery_format == "online" or spec["degree_type"] == "certificate":
            p.application_requirements = dict(_REQ_OPEN)
        elif spec["degree_type"] == "bachelors":
            p.application_requirements = dict(_REQ_UNDERGRAD)
        else:
            p.application_requirements = dict(_REQ_GRAD)
        # Outcomes precedence: program's own published employment report, else
        # College Scorecard Field-of-Study, else MIT-wide institution figures
        # (explicitly labelled), else none for non-degree credentials.
        out_override = _OUTCOMES_BY_SLUG.get(spec["slug"])
        fos = _FOS_OUTCOMES.get(spec["slug"])
        if out_override is not None:
            p.outcomes_data = dict(out_override)
        elif fos is not None:
            salary, debt, cip = fos
            p.outcomes_data = {
                "median_salary": salary,
                "scope": "program",
                "cip": cip,
                # Scorecard field-of-study methodology (glossary, verified
                # 2026-06-10): federally aided completers, working and not
                # enrolled, measured in the fourth full year after the award.
                "conditions": (
                    "College Scorecard field-of-study median: graduates who "
                    "received federal financial aid, working and not enrolled, "
                    "measured in the fourth full year after completing the award."
                ),
                "source": "U.S. Dept. of Education College Scorecard — Field of Study",
                "source_url": "https://collegescorecard.ed.gov/data/glossary/",
            }
            if debt is not None:
                p.outcomes_data["median_debt_completers"] = debt
        elif spec["degree_type"] in ("bachelors", "masters", "phd"):
            p.outcomes_data = dict(_OUTCOMES_INSTITUTION)
        else:
            p.outcomes_data = None
        # Audience + highlights: per-program for flagship, else by degree type.
        p.who_its_for = _WHO_BY_SLUG.get(spec["slug"]) or _WHO_BY_TYPE.get(spec["degree_type"])
        p.highlights = _HL_BY_SLUG.get(spec["slug"]) or _HL_BY_TYPE.get(spec["degree_type"])
        if spec["slug"] in _TRACKS_BY_SLUG:
            p.tracks = _TRACKS_BY_SLUG[spec["slug"]]
        # Class profile (size + selectivity + composition) where published.
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(spec["slug"])
        # Faculty: per-slug override, else the verified department head(s).
        p.faculty_contacts = _FACULTY_BY_SLUG.get(spec["slug"]) or _faculty_for(spec["slug"])
        p.external_reviews = _REVIEWS_BY_SLUG.get(spec["slug"])
        # Application deadline (upcoming cycle). Undergrad Regular Action is stable
        # (Jan 1); graduate dates vary by department — the program-page footer
        # notes "verify on the official program page".
        if spec["slug"] == "mit-sloan-mba":
            p.application_deadline = date(2027, 1, 13)
        elif spec["degree_type"] == "bachelors":
            p.application_deadline = date(2027, 1, 1)
        elif (
            spec.get("nonstandard_rates")
            or p.delivery_format == "online"
            or spec["degree_type"] == "certificate"
        ):
            # Professional programs run their own rounds — no date is asserted.
            p.application_deadline = None
        else:
            p.application_deadline = date(2026, 12, 15)
        # Conformance stamp: record exactly which required fields remain
        # unverified for this program (each was researched before omission).
        outcomes = dict(p.outcomes_data or {})
        outcomes["_standard"] = _standard(_program_omitted(p))
        p.outcomes_data = outcomes
    session.flush()
    # Reconcile legacy MIT programs (slug not in the canonical set): delete when
    # unreferenced, otherwise unpublish so the catalog is clean without breaking
    # any application/match rows that point at them.
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
