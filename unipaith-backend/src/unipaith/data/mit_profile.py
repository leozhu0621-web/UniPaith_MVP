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
    "source": "MIT Sloan Admissions",
    "source_url": "https://mitsloan.mit.edu/mba/admissions",
}
_REQ_OPEN = {
    "materials": [{"name": "Open enrollment — no formal admission required", "required": False}],
    "test_policy": {"stance": "not_required"},
    "source": "MIT Open Learning",
    "source_url": "https://openlearning.mit.edu/",
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
        "A one-year Master of Business Analytics, run with the Operations Research Center, "
        "that turns data and optimization into business decisions."
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
        p.delivery_format = spec.get("delivery_format", "in_person")
        # Tuition by program (MIT official 2025-26 rates). Standard degree
        # programs pay MIT's single published tuition; PhDs are fully funded;
        # the Sloan MBA has its own professional rate; online / MicroMasters /
        # certificate pricing varies per course → left null rather than guessed.
        if spec.get("tuition") is not None:
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
            if (p.tuition is not None or spec["degree_type"] == "phd")
            else None
        )
        if spec["slug"] == "mit-sloan-mba":
            p.application_requirements = dict(_REQ_MBA)
        elif p.delivery_format == "online" or spec["degree_type"] == "certificate":
            p.application_requirements = dict(_REQ_OPEN)
        elif spec["degree_type"] == "bachelors":
            p.application_requirements = dict(_REQ_UNDERGRAD)
        else:
            p.application_requirements = dict(_REQ_GRAD)
        # Real per-program outcomes from College Scorecard Field-of-Study where
        # MIT reports non-suppressed figures; otherwise MIT-wide institution
        # outcomes, explicitly labelled (degree programs only); non-degree: none.
        fos = _FOS_OUTCOMES.get(spec["slug"])
        if fos is not None:
            salary, debt, cip = fos
            p.outcomes_data = {
                "median_salary": salary,
                "scope": "program",
                "cip": cip,
                "source": "U.S. Dept. of Education College Scorecard — Field of Study",
                "source_url": "https://collegescorecard.ed.gov/",
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
        # Application deadline (upcoming cycle). Undergrad Regular Action is stable
        # (Jan 1); graduate dates vary by department — the program-page footer
        # notes "verify on the official program page".
        if spec["slug"] == "mit-sloan-mba":
            p.application_deadline = date(2027, 1, 13)
        elif spec["degree_type"] == "bachelors":
            p.application_deadline = date(2027, 1, 1)
        elif p.delivery_format == "online" or spec["degree_type"] == "certificate":
            p.application_deadline = None
        else:
            p.application_deadline = date(2026, 12, 15)
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
