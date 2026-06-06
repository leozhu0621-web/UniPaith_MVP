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

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School

INSTITUTION_NAME = "Massachusetts Institute of Technology"

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
    },
    "campus_life": {
        "varsity_sports": 33,
        "athletics_division": "NCAA Division III",
        "arts_groups": 60,
        "residence_halls": 20,
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
            "One of the world's leading business schools, dedicated to developing "
            "principled, innovative leaders and advancing management practice — "
            "offering the MBA, Master of Finance, Master of Business Analytics, "
            "PhD, and executive programs at the intersection of management and "
            "technology."
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
    inst.school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
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
        p.program_name = spec["program_name"]
        p.degree_type = spec["degree_type"]
        p.duration_months = spec.get("duration_months")
        p.description_text = spec["description"]
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "in_person")
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
