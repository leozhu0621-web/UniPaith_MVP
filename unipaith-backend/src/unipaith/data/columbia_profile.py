"""Canonical Columbia University profile — the single source of truth.

Real, sourced data only (U.S. Dept. of Education College Scorecard, UNITID 190150 ·
NCES College Navigator / IPEDS · Columbia's Office of Planning and Institutional Research
Common Data Set 2024-25 for Columbia College and Columbia Engineering · Columbia Finance /
UChicago... Columbia News (endowment) · the official QS / Times Higher Education / U.S.
News rankings · each school's official leadership page (Office of the President / the
school's own site) · the Office of the Bursar / each school's tuition page · the Columbia
Center for Career Education "Beyond Columbia" survey (Class of 2024, CC + SEAS) · the
Columbia Business School MBA Employment Report (Class of 2024) · the College Scorecard
Field-of-Study earnings by CIP). ``apply(session)`` idempotently enriches the Columbia
institution row, upserts its real degree-granting schools, and builds its program catalog
across them.

This is a **verified partial** of Columbia's tree (Columbia is a giant — ~20 schools).
Per the routine's resumption design for large universities, this run brings the
**institution node + five schools + their programs to the gold standard**, with the
Columbia Business School MBA as the most-enriched flagship; the remaining schools/programs
(Public Health, Social Work, Law, Nursing, Architecture, Climate, the Graduate School of
Arts and Sciences, and additional Engineering/SEAS master's) are deferred to a resume run
on the SAME university. The five schools modelled here:
  - Columbia College (undergraduate B.A./B.S. majors)
  - The Fu Foundation School of Engineering and Applied Science (Columbia Engineering)
  - Columbia Business School (the MBA — the most-enriched flagship)
  - School of International and Public Affairs (SIPA)
  - Columbia Journalism School

It **flushes but does not commit** — the caller (the Alembic data migration, the CLI
script, or the dev seed) owns the transaction. It is a **no-op** (returns ``False``) when
Columbia is absent, so it is safe to run against a fresh or CI database. Re-running is
safe: schools key off ``(institution_id, name)`` and programs off ``slug``; stale rows are
reconciled without breaking foreign keys.

This mirrors ``mit_profile`` / ``chicago_profile`` so the migration, the standalone
script, and the dev seed all agree (DRY). Every figure traces to a public, citable source;
anything that could not be verified from a first-party or two-independent-source basis is
**omitted** (recorded in the relevant ``_standard.omitted`` list), never guessed. The
Columbia Business School MBA is the most-enriched flagship (its curriculum, faculty, class
profile, employment distribution and aggregated reviews) — with the honest caveats that
Columbia is test-optional for first-year admission, that the university does not publish a
single unambiguous instructional-faculty headline (omitted), and that program-specific
graduate tuition for the divisional/engineering master's is published only on the
JavaScript-rendered Bursar pages and so is recorded as omitted rather than guessed.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Columbia University in the City of New York"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-10"


def _standard(omitted: list[str] | None = None) -> dict:
    """The per-node provenance stamp the routine writes onto every enriched node."""
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }


# Institution-level fields that could NOT be verified from a citable source and are
# therefore honestly omitted rather than guessed. Columbia does not publish a single
# unambiguous instructional-faculty headline count; the CDS faculty grid mixes standalone
# professional-school faculty, so the figure is omitted rather than misread.
_OMITTED_INSTITUTION = [
    "school_outcomes.scale.faculty_count",
]

# ── Institution-level data ────────────────────────────────────────────────
# Rankings are stored as {rank, year} objects (the page renders any ranking_data entry
# that is an object with a numeric `rank`). All three ranks are quoted from the official
# ranking bodies for the 2026 editions.
RANKING_DATA: dict = {
    "ownership_type": "private",
    # Columbia is accredited by the Middle States Commission on Higher Education (MSCHE).
    "accreditor": "MSCHE",
    # Carnegie basic classification (R1).
    "carnegie_classification": "Doctoral Universities: Very High Research Activity",
    # QS World University Rankings 2026: Columbia is ranked #38 worldwide.
    "qs_world_university_rankings": {"rank": 38, "year": 2026},
    # THE World University Rankings 2026: #20 in the world.
    "times_higher_education": {"rank": 20, "year": 2026},
    # U.S. News Best Colleges (National Universities) 2026: #13 nationally.
    "us_news_national": {"rank": 13, "year": 2026},
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below is
# complete, so a shallow merge is correct. Figures are College Scorecard (UNITID 190150)
# cross-checked against Columbia's Common Data Set 2024-25 (Columbia College + Columbia
# Engineering) and NCES College Navigator (IPEDS) where each publishes a metric.
SCHOOL_OUTCOMES: dict = {
    # CDS 2024-25 (CC + SEAS): 2,325 admits / 60,247 first-year applicants = 3.86%.
    "admit_rate": 0.0386,
    # College Scorecard average annual net price.
    "avg_net_price": 21590,
    # College Scorecard institution-wide median earnings 10 years after entry.
    "median_earnings_10yr": 102491,
    # College Scorecard four-year completion rate (150% of normal time).
    "completion_rate_4yr_150pct": 0.961,
    # CDS 2024-25 (item B22): first-year retention (Fall 2023 cohort) = 98%.
    "retention_rate_first_year": 0.98,
    # CDS 2024-25: six-year graduation rate (Fall 2018 cohort), all students = 96%.
    "graduation_rate_6yr": 0.96,
    "financial_aid": {
        # NCES College Navigator (IPEDS), 2023-24 full-time beginning undergraduates: 21%
        # received a Pell grant; 5% took federal student loans. Columbia meets full need.
        "pell_grant_rate": 0.21,
        "federal_loan_rate": 0.05,
        # College Scorecard average annual cost of attendance.
        "cost_of_attendance": 89472,
    },
    # Undergraduate race/ethnicity (Columbia CDS 2024-25, item B2, degree-seeking CC + SEAS
    # undergraduates, n=6,597; shares rounded to whole percents).
    "demographics": {
        "white": 0.26,
        "black": 0.08,
        "hispanic": 0.17,
        "asian": 0.22,
        "two_or_more": 0.07,
        "international": 0.16,
    },
    # SAT/ACT 25th-75th percentiles of enrolled first-years (Columbia CDS 2024-25, item
    # C9). Columbia is test-optional, so percentiles reflect only score-submitters.
    "test_scores": {
        "sat_reading_25_75": [740, 780],
        "sat_math_25_75": [770, 800],
        "act_25_75": [34, 36],
    },
    # Morningside Heights campus, New York City.
    "location": {"lat": 40.8075, "lng": -73.96194},
    "campus_basics": {"location": "Morningside Heights, New York City"},
    "scale": {
        # faculty_count omitted (see _OMITTED_INSTITUTION).
        # CDS 2024-25 (item I2): 6-to-1 student-faculty ratio.
        "student_faculty_ratio": "6:1",
        # Columbia News / Columbia Finance: endowment $14.8 billion at fiscal year-end
        # June 30, 2024 (FY24, 11.5% net return).
        "endowment_usd": 14800000000,
    },
    # Columbia Center for Career Education "Beyond Columbia" survey, Columbia College +
    # Columbia Engineering undergraduates, Class of 2024: 87.9% employed or in graduate
    # school (64.1% working + 23.8% continuing education).
    "employed_or_continuing_ed": 0.879,
    # The industries Columbia College + Engineering graduates most commonly enter (Beyond
    # Columbia Survey 2024 names these as the most popular); not ranked by a precise share.
    "top_employer_industries": [
        "Internet & software",
        "Investment banking",
        "Investment / portfolio management",
        "Consulting",
    ],
    "research": {
        "labs": [
            "Lamont-Doherty Earth Observatory (earth & climate science)",
            "Zuckerman Mind Brain Behavior Institute (neuroscience)",
            "Nevis Laboratories (particle & nuclear physics)",
            "NASA Goddard Institute for Space Studies (climate modeling)",
            "Data Science Institute",
            "Columbia Climate School",
        ],
        "areas": [
            "Earth, climate & sustainability science",
            "Neuroscience & the mind",
            "Physics & particle science",
            "Economics, finance & the social sciences",
            "Journalism, international affairs & public policy",
            "Data science & engineering",
        ],
        "lab_links": {
            "Lamont-Doherty Earth Observatory (earth & climate science)": (
                "https://lamont.columbia.edu/"
            ),
            "Zuckerman Mind Brain Behavior Institute (neuroscience)": (
                "https://zuckermaninstitute.columbia.edu/"
            ),
            "Data Science Institute": "https://datascience.columbia.edu/",
        },
    },
    "campus_life": {
        # The Lions compete in NCAA Division I as members of the Ivy League.
        "athletics_division": "NCAA Division I (Ivy League)",
        "mascot": "Columbia Lions (Roar-ee the Lion)",
        "housing": "Residential housing across the Morningside Heights campus",
        "resources": [
            {"label": "Columbia Lions Athletics", "url": "https://gocolumbialions.com/"},
            {
                "label": "Columbia in New York City",
                "url": "https://www.columbia.edu/content/nyc",
            },
        ],
    },
    "flagship": {
        # CDS 2024-25 total all students (Columbia College + Columbia Engineering CDS).
        "enrollment_total": 28657,
        # Common Data Set 2024-25 first-year admissions cycle (item C1; CC + SEAS).
        "applicants": 60247,
        "admits": 2325,
        "admissions_cycle": (
            "Columbia College + Columbia Engineering, entering class fall 2024 "
            "(Columbia Common Data Set 2024-25)"
        ),
        # Founded in 1754 as King's College by royal charter of King George II; renamed
        # Columbia College in 1784 and Columbia University in 1896.
        "founded_year": 1754,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Columbia, UNITID 190150)",
            "url": "https://collegescorecard.ed.gov/school/?190150-Columbia-University-in-the-City-of-New-York",
        },
        {
            "label": "NCES College Navigator — Columbia University (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=190150",
        },
        {
            "label": "Columbia OPIR — Common Data Set 2024-25 (Columbia College & Engineering)",
            "url": "https://opir.columbia.edu/cds",
        },
        {
            "label": "Columbia University endowment, fiscal 2024 ($14.8B; Columbia Finance)",
            "url": "https://www.finance.columbia.edu/news/financial-statements-released-fiscal-2024",
        },
        {
            "label": "QS World University Rankings 2026 — Columbia University",
            "url": "https://www.topuniversities.com/universities/columbia-university",
        },
        {
            "label": (
                "Times Higher Education World University Rankings 2026 — Columbia University"
            ),
            "url": "https://www.timeshighereducation.com/world-university-rankings/columbia-university",
        },
        {
            "label": (
                "U.S. News Best Colleges 2026 — Columbia University (#13 National Universities)"
            ),
            "url": "https://www.usnews.com/best-colleges/columbia-university-2707",
        },
        {
            "label": (
                "Columbia Center for Career Education — Beyond Columbia Survey 2024 (CC & SEAS)"
            ),
            "url": "https://www.careereducation.columbia.edu/sites/default/files/2025-04/2024-bcs-cc-seas-ug.pdf",
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it "Undergraduates"); the
# total (28,657) lives in flagship.enrollment_total and renders as "Total enrollment".
# 8,344 = CDS 2024-25 total undergraduate students (Columbia College + Engineering + GS).
UNDERGRAD_COUNT = 8344

DESCRIPTION = (
    "Founded in 1754 as King's College by royal charter of King George II, Columbia "
    "University is a private Ivy League research university in the Morningside Heights "
    "neighborhood of New York City — the oldest institution of higher education in New "
    "York and the fifth-oldest in the United States. It enrolls about 8,300 undergraduates "
    "and roughly 20,000 graduate and professional students, some 28,700 in all, pairing "
    "the resources of a major research university with the opportunities of New York "
    "City.\n\n"
    "Columbia College awards the B.A. anchored by the Core Curriculum, and the university "
    "spans the Fu Foundation School of Engineering and Applied Science and a celebrated "
    "set of professional schools — among them Columbia Business School, the Law School, "
    "the Vagelos College of Physicians and Surgeons, the School of International and "
    "Public Affairs, the Mailman School of Public Health, the Journalism School (which "
    "administers the Pulitzer Prizes), and Teachers College. Its research reaches from "
    "the Lamont-Doherty Earth Observatory and the NASA Goddard Institute for Space "
    "Studies to the Zuckerman Mind Brain Behavior Institute.\n\n"
    "Columbia ranks among the world's leading universities: No. 13 among national "
    "universities by U.S. News, No. 20 in the world by Times Higher Education, and No. 38 "
    "by QS. It admits under 4% of first-year applicants and is backed by a $14.8 billion "
    "endowment.\n\n"
    "Columbia is need-blind for domestic first-year applicants and meets 100% of "
    "demonstrated financial need: the average net price is about $21,600 a year, 21% of "
    "undergraduates receive Pell grants, and only 5% take federal student loans. Among "
    "the Columbia College and Engineering Class of 2024, 87.9% were employed or in "
    "graduate school within six months of graduation."
)

# ── The real degree-granting schools modelled in this partial (display order) ──
_COLLEGE = "Columbia College"
_SEAS = "The Fu Foundation School of Engineering and Applied Science"
_CBS = "Columbia Business School"
_SIPA = "School of International and Public Affairs"
_JOURNALISM = "Columbia Journalism School"

SCHOOLS: list[dict] = [
    {
        "name": _COLLEGE,
        "sort_order": 1,
        "description": (
            "Columbia College, founded in 1754 as King's College, is the university's "
            "oldest undergraduate school. Built around the Core Curriculum — a shared "
            "sequence in literature, philosophy, history, science and the arts — it awards "
            "the B.A. across the humanities, social sciences and sciences and is the "
            "historic heart of the university."
        ),
    },
    {
        "name": _SEAS,
        "sort_order": 2,
        "description": (
            "The Fu Foundation School of Engineering and Applied Science (Columbia "
            "Engineering), founded in 1864 as the School of Mines, is the university's "
            "engineering and applied-science school. It awards the B.S., M.S. and Ph.D. "
            "across computer science, electrical and mechanical engineering, operations "
            "research, and the applied sciences, in the heart of New York City."
        ),
    },
    {
        "name": _CBS,
        "sort_order": 3,
        "description": (
            "Founded in 1916, Columbia Business School educates business leaders at the "
            "very center of business. It awards the full-time MBA, the Executive MBA, "
            "specialized master's degrees and the Ph.D., and is distinguished by its New "
            "York City location, value-investing tradition and a curriculum that pairs a "
            "rigorous core with deep engagement in the city's industries."
        ),
    },
    {
        "name": _SIPA,
        "sort_order": 4,
        "description": (
            "The School of International and Public Affairs (SIPA), founded in 1946, "
            "educates leaders in public policy and global affairs. It awards the Master of "
            "Public Administration, the Master of International Affairs and doctoral "
            "degrees, drawing on Columbia's research depth and New York's role as a global "
            "and diplomatic capital."
        ),
    },
    {
        "name": _JOURNALISM,
        "sort_order": 5,
        "description": (
            "The Columbia Journalism School, founded in 1912 from a bequest of Joseph "
            "Pulitzer, is the only Ivy League journalism school and administers the "
            "Pulitzer Prizes. It awards the Master of Science and Master of Arts in "
            "journalism and is among the most influential schools of journalism in the "
            "world."
        ),
    },
]

# Each school's official website (verified to resolve at author time).
_SCHOOL_WEBSITE: dict[str, str] = {
    _COLLEGE: "https://www.college.columbia.edu/",
    _SEAS: "https://www.engineering.columbia.edu/",
    _CBS: "https://business.columbia.edu/",
    _SIPA: "https://www.sipa.columbia.edu/",
    _JOURNALISM: "https://journalism.columbia.edu/",
}

# Rich, sourced About-tab content per school. Deans + titles are quoted from each school's
# official leadership page / the Office of the President (verified 2026-06-10). Founding
# years come from each school's official history. Notable-faculty rosters are not published
# uniformly per school and are omitted rather than hand-picked (recorded in _ABOUT_OMITTED).
_ABOUT_DETAIL: dict[str, dict] = {
    _COLLEGE: {
        "founded": 1754,
        "leadership": (
            "Josef Sorett — Dean of Columbia College and Vice President for Undergraduate "
            "Education"
        ),
        "research_centers": [
            "The Core Curriculum",
            "Center for the Core Curriculum",
            "Undergraduate Research and Fellowships",
        ],
        "named_for": "Originally King's College (1754); renamed Columbia College in 1784",
        "source": {
            "label": "Columbia College — Office of the Dean (Josef Sorett)",
            "url": "https://www.college.columbia.edu/about/dean-josef-sorett",
        },
    },
    _SEAS: {
        "founded": 1864,
        "leadership": (
            "Shih-Fu Chang — Dean of Columbia Engineering and Morris A. and Alma Schapiro "
            "Professor"
        ),
        "research_centers": [
            "Data Science Institute",
            "Columbia Nano Initiative",
            "Fu Foundation laboratories across computer science and engineering",
        ],
        "named_for": "The Fu Foundation (1997 naming gift); founded 1864 as the School of Mines",
        "source": {
            "label": "Columbia Engineering — Dean Shih-Fu Chang",
            "url": "https://www.engineering.columbia.edu/faculty-staff/directory/dean-shih-fu-chang",
        },
    },
    _CBS: {
        "founded": 1916,
        "leadership": (
            "Costis Maglaras — Dean and David and Lyn Silfen Professor of Business"
        ),
        "research_centers": [
            "Heilbrunn Center for Graham & Dodd Investing",
            "Eugene Lang Entrepreneurship Center",
            "Chazen Institute for Global Business",
        ],
        "source": {
            "label": "Columbia Business School — Leadership (Dean Costis Maglaras)",
            "url": "https://business.columbia.edu/about-us/leadership",
        },
    },
    _SIPA: {
        "founded": 1946,
        "leadership": "Keren Yarhi-Milo — Dean of Columbia SIPA",
        "research_centers": [
            "Center on Global Energy Policy",
            "Saltzman Institute of War and Peace Studies",
            "Center for Development Economics and Policy",
        ],
        "source": {
            "label": "Columbia SIPA — Dean Keren Yarhi-Milo",
            "url": "https://www.sipa.columbia.edu/communities-connections/faculty/keren-yarhi-milo",
        },
    },
    _JOURNALISM: {
        "founded": 1912,
        "leadership": "Jelani Cobb — Dean of the Columbia Journalism School",
        "research_centers": [
            "The Pulitzer Prizes",
            "Tow Center for Digital Journalism",
            "Columbia Journalism Review",
        ],
        "named_for": "Endowed by a bequest of Joseph Pulitzer",
        "source": {
            "label": "Columbia Journalism School — Dean Jelani Cobb",
            "url": "https://journalism.columbia.edu/dean-jelani-cobb",
        },
    },
}

# About-detail fields omitted per school (verified-unavailable), recorded in each school's
# _standard.omitted. Notable-faculty rosters are omitted for every school.
_FACULTY_OMIT = ["about_detail.faculty"]
_ABOUT_OMITTED: dict[str, list[str]] = {
    _COLLEGE: list(_FACULTY_OMIT),
    _SEAS: list(_FACULTY_OMIT),
    _CBS: list(_FACULTY_OMIT),
    _SIPA: list(_FACULTY_OMIT),
    _JOURNALISM: list(_FACULTY_OMIT),
}

# ── Channel feeds + official social links ──────────────────────────────────
_INSTITUTION_CONTENT: dict = {
    "news_url": "https://news.columbia.edu",
    "social": {
        "instagram": "https://www.instagram.com/columbia/",
        "linkedin": "https://www.linkedin.com/school/columbia-university/",
        "x": "https://x.com/Columbia",
        "youtube": "https://www.youtube.com/user/Columbia",
        "facebook": "https://www.facebook.com/columbia",
    },
}

# Columbia Business School keyword-relevant feed (the flagship program).
_MBA_CONTENT: dict = {
    "news_url": "https://business.columbia.edu/insights",
    "keywords": ["columbia business school", "mba", "finance", "value investing", "new york"],
    "social": {
        "instagram": "https://www.instagram.com/columbiabusiness/",
        "linkedin": "https://www.linkedin.com/school/columbia-business-school/",
        "x": "https://x.com/Columbia_Biz",
        "youtube": "https://www.youtube.com/user/ColumbiaBusiness",
        "facebook": "https://www.facebook.com/columbiabusiness",
    },
}

# ── The program catalog (real majors/degrees, organized by school) ─────────
# slug = idempotency key. Programs are mapped to their owning school from Columbia's
# official structure. Undergraduate majors and the engineering/affairs/journalism master's
# come from the College Scorecard Field-of-Study list for UNITID 190150 (the deterministic
# federal view); the Columbia Business School MBA (the flagship) is added from the school's
# own catalog with its published employment report. Graduate degrees use the generic
# ``masters`` type with the real degree name carried in the program name.
PROGRAMS: list[dict] = [
    # ── Columbia College (undergraduate B.A. majors) ──
    {
        "slug": "columbia-economics-bs",
        "school": _COLLEGE,
        "program_name": "Economics",
        "degree_type": "bachelors",
        "cip": "45.06",
        "duration_months": 48,
        "description": (
            "Economics — micro and macroeconomic theory, econometrics and applied "
            "economics, with combined majors across mathematics, statistics and political "
            "science."
        ),
    },
    {
        "slug": "columbia-political-science-bs",
        "school": _COLLEGE,
        "program_name": "Political Science",
        "degree_type": "bachelors",
        "cip": "45.10",
        "duration_months": 48,
        "description": (
            "Political science — American, comparative and international politics and "
            "political theory."
        ),
    },
    {
        "slug": "columbia-psychology-bs",
        "school": _COLLEGE,
        "program_name": "Psychology",
        "degree_type": "bachelors",
        "cip": "42.27",
        "duration_months": 48,
        "description": "Psychology — cognitive, developmental, social and neural science.",
    },
    {
        "slug": "columbia-history-bs",
        "school": _COLLEGE,
        "program_name": "History",
        "degree_type": "bachelors",
        "cip": "54.01",
        "duration_months": 48,
        "description": "History — the study of the human past across periods and regions.",
    },
    # ── Columbia Engineering (SEAS) ──
    {
        "slug": "columbia-computer-science-bs",
        "school": _SEAS,
        "program_name": "Computer Science",
        "degree_type": "bachelors",
        "cip": "11.07",
        "duration_months": 48,
        "description": (
            "Computer science — algorithms, systems, machine learning and the theory and "
            "applications of computation, offered through Columbia Engineering."
        ),
    },
    {
        "slug": "columbia-computer-science-ms",
        "school": _SEAS,
        "program_name": "Master of Science in Computer Science",
        "degree_type": "masters",
        "cip": "11.07",
        "duration_months": 18,
        "description": (
            "The M.S. in Computer Science — a track-based professional master's spanning "
            "machine learning, systems, security, vision, NLP and foundations of CS."
        ),
    },
    {
        "slug": "columbia-electrical-engineering-ms",
        "school": _SEAS,
        "program_name": "Master of Science in Electrical Engineering",
        "degree_type": "masters",
        "cip": "14.10",
        "duration_months": 18,
        "description": (
            "The M.S. in Electrical Engineering — signal processing, communications, "
            "circuits, devices and machine learning systems."
        ),
    },
    {
        "slug": "columbia-mechanical-engineering-ms",
        "school": _SEAS,
        "program_name": "Master of Science in Mechanical Engineering",
        "degree_type": "masters",
        "cip": "14.19",
        "duration_months": 18,
        "description": (
            "The M.S. in Mechanical Engineering — robotics, controls, energy, "
            "micro/nanoscale systems and mechanics."
        ),
    },
    {
        "slug": "columbia-management-science-ms",
        "school": _SEAS,
        "program_name": "Master of Science in Management Science and Engineering",
        "degree_type": "masters",
        "cip": "52.13",
        "duration_months": 18,
        "description": (
            "The M.S. in Management Science and Engineering — optimization, stochastic "
            "modeling and analytics for finance, operations and technology, from the "
            "Department of Industrial Engineering and Operations Research."
        ),
    },
    # ── Columbia Business School (the flagship) ──
    {
        "slug": "columbia-mba",
        "school": _CBS,
        "program_name": "Master of Business Administration (MBA)",
        "degree_type": "masters",
        "cip": "52.02",
        "duration_months": 20,
        "description": (
            "Columbia Business School's flagship full-time MBA — a rigorous core paired "
            "with deep engagement in New York's industries and a celebrated value-investing "
            "and entrepreneurship tradition, set at the very center of business."
        ),
    },
    # ── School of International and Public Affairs (SIPA) ──
    {
        "slug": "columbia-public-administration-mpa",
        "school": _SIPA,
        "program_name": "Master of Public Administration (MPA)",
        "degree_type": "masters",
        "cip": "44.04",
        "duration_months": 24,
        "description": (
            "The two-year Master of Public Administration — policy analysis, economics, "
            "management and a professional concentration for leadership in public service."
        ),
    },
    {
        "slug": "columbia-international-affairs-mia",
        "school": _SIPA,
        "program_name": "Master of International Affairs (MIA)",
        "degree_type": "masters",
        "cip": "45.09",
        "duration_months": 24,
        "description": (
            "The two-year Master of International Affairs — international security, "
            "development, economic policy and regional studies for careers in global "
            "affairs."
        ),
    },
    # ── Columbia Journalism School ──
    {
        "slug": "columbia-journalism-ms",
        "school": _JOURNALISM,
        "program_name": "Master of Science in Journalism",
        "degree_type": "masters",
        "cip": "09.04",
        "duration_months": 10,
        "description": (
            "The Master of Science in Journalism — Columbia's signature reporting degree, "
            "an intensive program in reporting, writing and multimedia journalism."
        ),
    },
]

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

# Full official program names (program-page title); equal to the program name here.
_FULL_NAME_BY_SLUG: dict[str, str] = {p["slug"]: p["program_name"] for p in PROGRAMS}

# Official program/department/school home pages.
_WEBSITE_BY_SLUG: dict[str, str] = {
    "columbia-economics-bs": "https://econ.columbia.edu/",
    "columbia-political-science-bs": "https://polisci.columbia.edu/",
    "columbia-psychology-bs": "https://psychology.columbia.edu/",
    "columbia-history-bs": "https://history.columbia.edu/",
    "columbia-computer-science-bs": "https://www.cs.columbia.edu/education/undergraduate/",
    "columbia-computer-science-ms": "https://www.cs.columbia.edu/education/ms/",
    "columbia-electrical-engineering-ms": "https://www.ee.columbia.edu/ms-program",
    "columbia-mechanical-engineering-ms": "https://www.me.columbia.edu/ms-program",
    "columbia-management-science-ms": "https://www.ieor.columbia.edu/",
    "columbia-mba": "https://business.columbia.edu/mba",
    "columbia-public-administration-mpa": "https://www.sipa.columbia.edu/sipa-education/degrees/master-public-administration-mpa",
    "columbia-international-affairs-mia": "https://www.sipa.columbia.edu/sipa-education/degrees/master-international-affairs-mia",
    "columbia-journalism-ms": "https://journalism.columbia.edu/ms-degree",
}

# ── Who-it's-for + highlights (catalog baselines) ──────────────────────────
_WHO_BASELINE = (
    "Intellectually ambitious students who want a rigorous education anchored by the Core "
    "Curriculum, full-need financial aid, and the opportunities of a major research "
    "university in New York City."
)
_HL_BASELINE = ["Ivy League", "The Core Curriculum", "Need-met financial aid"]
_WHO_GRAD_BASELINE = (
    "Graduate and professional students seeking a top-ranked Columbia degree with the "
    "resources of a major research university at the center of New York City."
)
_HL_GRAD_BASELINE = [
    "Top-ranked Columbia degree",
    "World-class faculty",
    "New York City",
]

_WHO_BY_SLUG = {
    "columbia-mba": (
        "Aspiring leaders who want a rigorous MBA at the center of business, with deep "
        "strength in finance, value investing and entrepreneurship and immersion in New "
        "York City's industries."
    ),
}
_HL_BY_SLUG = {
    "columbia-mba": [
        "At the very center of business",
        "Value-investing tradition",
        "New York City network",
    ],
}

# ── Curriculum / structure, where published (the flagship) ─────────────────
# Columbia Business School organizes its faculty and teaching around academic divisions;
# the MBA pairs a required core with extensive electives across them. Quoted from the
# school's official academics pages.
_TRACKS_BY_SLUG: dict[str, dict] = {
    "columbia-mba": {
        "label": "Columbia Business School academic divisions",
        "note": (
            "The full-time MBA pairs a required first-year core with extensive electives. "
            "Faculty and teaching are organized around the school's academic divisions, "
            "across which students build their concentration."
        ),
        "items": [
            {"name": "Accounting"},
            {"name": "Decision, Risk, and Operations"},
            {"name": "Economics"},
            {"name": "Finance"},
            {"name": "Management"},
            {"name": "Marketing"},
        ],
        "source": "Columbia Business School — Academic Divisions",
        "source_url": "https://business.columbia.edu/faculty/divisions",
    },
}

# ── Program-specific cost ──────────────────────────────────────────────────
# Columbia College undergraduate cost: tuition is the College Scorecard 2024-25 figure
# (tuition & fees); cost of attendance and average net price are College Scorecard.
_TUITION_UG = 71845
_UNDERGRAD_COA = 89472
_AVG_NET_PRICE = 21590

# Per-program graduate cost. Columbia's Bursar tuition pages are JavaScript-rendered; where
# a program's exact tuition could not be verified from a static first-party source it is
# OMITTED (recorded in the program's _standard.omitted) and only the source pointer is
# kept. The engineering/affairs/journalism master's are in that omitted state; the Columbia
# Business School MBA carries its verified, published cost.
_COST_BY_SLUG: dict[str, dict] = {
    "columbia-mba": {
        "tuition_usd": 88300,
        "total_cost_of_attendance": 132258,
        "funded": False,
        "breakdown": {
            "tuition": 88300,
            "total_cost_of_attendance": 132258,
        },
        "note": (
            "Full-time MBA tuition for 2024-25; the estimated first-year (August-entry) "
            "single-student cost of attendance is shown as total cost."
        ),
        "source": "Columbia Business School — Full-Time MBA Costs (2024-25)",
        "source_url": "https://business.columbia.edu/financial-aid/costs/full-time",
        "year": "2024-25",
    },
    "columbia-computer-science-ms": {
        "funded": False,
        "note": (
            "Graduate tuition is set per-point on the Office of the Bursar's engineering "
            "page; the exact 2025-26 figure could not be verified from a static source "
            "and is omitted rather than estimated."
        ),
        "source": "Columbia University — Office of the Bursar / SFS Tuition tool",
        "source_url": "https://tuition.sfs.columbia.edu/",
    },
    "columbia-electrical-engineering-ms": {
        "funded": False,
        "note": (
            "Graduate tuition is set per-point on the Office of the Bursar's engineering "
            "page; the exact 2025-26 figure could not be verified from a static source "
            "and is omitted rather than estimated."
        ),
        "source": "Columbia University — Office of the Bursar / SFS Tuition tool",
        "source_url": "https://tuition.sfs.columbia.edu/",
    },
    "columbia-mechanical-engineering-ms": {
        "funded": False,
        "note": (
            "Graduate tuition is set per-point on the Office of the Bursar's engineering "
            "page; the exact 2025-26 figure could not be verified from a static source "
            "and is omitted rather than estimated."
        ),
        "source": "Columbia University — Office of the Bursar / SFS Tuition tool",
        "source_url": "https://tuition.sfs.columbia.edu/",
    },
    "columbia-management-science-ms": {
        "funded": False,
        "note": (
            "Graduate tuition is set per-point on the Office of the Bursar's engineering "
            "page; the exact 2025-26 figure could not be verified from a static source "
            "and is omitted rather than estimated."
        ),
        "source": "Columbia University — Office of the Bursar / SFS Tuition tool",
        "source_url": "https://tuition.sfs.columbia.edu/",
    },
    "columbia-public-administration-mpa": {
        "funded": False,
        "note": (
            "SIPA tuition is set on the Office of the Bursar's SIPA page; the exact "
            "2025-26 figure could not be verified from a static source and is omitted "
            "rather than estimated."
        ),
        "source": "Columbia University — Office of the Bursar / SFS Tuition tool (SIPA)",
        "source_url": "https://tuition.sfs.columbia.edu/",
    },
    "columbia-international-affairs-mia": {
        "funded": False,
        "note": (
            "SIPA tuition is set on the Office of the Bursar's SIPA page; the exact "
            "2025-26 figure could not be verified from a static source and is omitted "
            "rather than estimated."
        ),
        "source": "Columbia University — Office of the Bursar / SFS Tuition tool (SIPA)",
        "source_url": "https://tuition.sfs.columbia.edu/",
    },
    "columbia-journalism-ms": {
        "funded": False,
        "note": (
            "Journalism School tuition is set on the Office of the Bursar's Journalism "
            "page; the exact 2025-26 figure could not be verified from a static source "
            "and is omitted rather than estimated."
        ),
        "source": "Columbia University — Office of the Bursar / SFS Tuition tool (Journalism)",
        "source_url": "https://tuition.sfs.columbia.edu/",
    },
}

# Programs whose program tuition is omitted (recorded per program in _standard.omitted).
_TUITION_OMITTED_SLUGS = {
    slug for slug, cost in _COST_BY_SLUG.items() if cost.get("tuition_usd") is None
}

# ── Program-specific outcomes (College Scorecard Field of Study, by CIP) ────
# Where the federal College Scorecard publishes a Field-of-Study median earnings (one year
# after completion) for an awarded CIP + credential level at UNITID 190150, we use it
# (program scope). The Columbia Business School MBA (flagship) instead carries its own
# published employment distribution (below) and is not in this table. Tuples are
# (median_earnings_1yr, cip).
_FOS_OUTCOMES: dict[str, tuple[int, str]] = {
    "columbia-economics-bs": (83135, "45.06"),
    "columbia-political-science-bs": (61077, "45.10"),
    "columbia-psychology-bs": (53156, "42.27"),
    "columbia-history-bs": (53828, "54.01"),
    "columbia-computer-science-bs": (118636, "11.07"),
    "columbia-computer-science-ms": (161851, "11.07"),
    "columbia-electrical-engineering-ms": (124969, "14.10"),
    "columbia-mechanical-engineering-ms": (104503, "14.19"),
    "columbia-management-science-ms": (197821, "52.13"),
    "columbia-public-administration-mpa": (89478, "44.04"),
    "columbia-international-affairs-mia": (80448, "45.09"),
    "columbia-journalism-ms": (54170, "09.04"),
}

# Verbatim methodology for the program-scope Scorecard FOS earnings figure.
_FOS_CONDITIONS = (
    "Median earnings of graduates who received federal financial aid, measured "
    "approximately one year after program completion; reported by the U.S. Department of "
    "Education College Scorecard Field of Study by 4-digit CIP code and credential level. "
    "Programs with too few completers are suppressed."
)

# Institution-wide outcomes fallback (College Scorecard, UNITID 190150). Unused in this
# partial (every modelled program has a published FOS earnings figure) but kept for the
# resume run and for parity with the reference data modules.
_OUTCOMES_INSTITUTION = {
    "median_salary": 102491,
    "scope": "institution",
    "conditions": (
        "Columbia institution-wide median earnings ten years after entry (College "
        "Scorecard, UNITID 190150); a program-level one-year earnings figure is not "
        "published (suppressed) for this field of study."
    ),
    "source": "U.S. Dept. of Education College Scorecard (UNITID 190150)",
    "source_url": (
        "https://collegescorecard.ed.gov/school/?190150-Columbia-University-in-the-City-of-New-York"
    ),
}

# ── The flagship: Columbia Business School MBA employment distribution ──────
# Columbia Business School MBA Employment Report, Class of 2024. Percentages and counts are
# quoted from that report.
_MBA_OUTCOMES = {
    "median_salary": 175000,
    "median_signing_bonus": 30000,
    "employment_rate": 0.864,
    "employment_timeframe": "accepted an offer within 3 months of graduation",
    "class_size": 844,
    "scope": "program",
    "cip": "52.02",
    "top_industries": [
        "Financial services — 35.9%",
        "Consulting — 30.6%",
        "Technology — 10.0%",
        "Consumer products — 5.2%",
        "Healthcare — 3.8%",
    ],
    "top_employers": [
        "McKinsey & Company",
        "Boston Consulting Group",
        "Amazon",
        "PricewaterhouseCoopers",
        "Bain & Company",
        "JPMorgan Chase",
        "Deloitte",
    ],
    "conditions": [
        "Columbia Business School MBA Employment Report, Class of 2024.",
        "Within three months of graduation, 89.0% of graduates seeking employment "
        "received and 86.4% accepted a full-time offer.",
        "Median base salary $175,000 (100% reporting; high $370,000); median signing "
        "bonus $30,000 received by 71.3% of hires (high $151,000).",
        "Top employers are listed by the school in order of total hires; figures exclude "
        "graduates sponsored, starting a business, or joining a family business, per "
        "Career Services & Employer Alliance standards.",
    ],
    "source": "Columbia Business School MBA Employment Report, Class of 2024",
    "source_url": "https://business.columbia.edu/recruiters/employment-report",
}


def _outcomes_for(slug: str) -> dict:
    """The outcomes_data payload (without _standard) for a program slug.

    Precedence: Columbia Business School MBA distribution → Scorecard FOS (program) →
    institution median fallback. Used by both ``apply()`` and the conformance test (DRY).
    """
    if slug == "columbia-mba":
        return dict(_MBA_OUTCOMES)
    fos = _FOS_OUTCOMES.get(slug)
    if fos is not None:
        salary, cip = fos
        return {
            "median_salary": salary,
            "scope": "program",
            "cip": cip,
            "earnings_timeframe": "median earnings 1 year after completion",
            "conditions": _FOS_CONDITIONS,
            "source": "U.S. Dept. of Education College Scorecard — Field of Study",
            "source_url": (
                "https://collegescorecard.ed.gov/school/?190150-Columbia-University-in-the-City-of-New-York"
            ),
        }
    return dict(_OUTCOMES_INSTITUTION)


# ── Class profile, where published (the flagship) ──────────────────────────
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    "columbia-mba": {
        "cohort_size": "844 students (Full-Time MBA, Class of 2024, entering 2022)",
        "international_pct": 51,
        "note": (
            "Class of 2024: 844 students entered in 2022; 44% women and 51% non-U.S. "
            "citizens; average five years of work experience; average GMAT 729 "
            "(range 700-760)."
        ),
        "source": "Columbia Business School MBA Employment Report, Class of 2024",
        "source_url": "https://business.columbia.edu/recruiters/employment-report",
    },
}

# ── Faculty (lead + directory link), where confidently sourced (the flagship) ──
_FACULTY_BY_SLUG: dict[str, dict] = {
    "columbia-mba": {
        "lead": [
            {
                "name": "Costis Maglaras",
                "title": (
                    "Dean and David and Lyn Silfen Professor of Business "
                    "(Decision, Risk, and Operations)"
                ),
            },
        ],
        "note": (
            "Columbia Business School is led by Dean Costis Maglaras, the David and Lyn "
            "Silfen Professor of Business; its faculty span finance, economics, "
            "marketing, management and operations."
        ),
        "directory_url": "https://business.columbia.edu/faculty",
    },
}

# ── Aggregated, cited student-review themes (≥2 third-party sources, the flagship) ──
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "columbia-mba": {
        "summary": (
            "Students and third-party guides describe Columbia Business School as a "
            "top-tier MBA with exceptional strength in finance and value investing, "
            "unrivaled access to New York City's industries and recruiters, and a rigorous "
            "core curriculum. Common cautions are the high cost of living in New York and a "
            "competitive, finance-heavy culture, though the school has broadened into "
            "technology and entrepreneurship in recent years."
        ),
        "themes": [
            {
                "label": "Finance & value investing",
                "sentiment": "positive",
                "detail": "Deep strength in finance, value investing and asset management.",
            },
            {
                "label": "New York City access",
                "sentiment": "positive",
                "detail": "Unmatched proximity to employers and industries in New York.",
            },
            {
                "label": "Rigorous core",
                "sentiment": "positive",
                "detail": "A demanding first-year core builds broad analytical skills.",
            },
            {
                "label": "Cost of living",
                "sentiment": "caution",
                "detail": "Living in New York City adds significantly to the total cost.",
            },
            {
                "label": "Competitive culture",
                "sentiment": "caution",
                "detail": "A finance-heavy, fast-paced environment can feel competitive.",
            },
        ],
        "sources": [
            {
                "label": "Poets&Quants — Columbia Business School",
                "url": "https://poetsandquants.com/school/columbia-business-school/",
            },
            {
                "label": "U.S. News — Columbia Business School (Best Business Schools)",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/columbia-university-01060",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
}

# ── Application requirements ─────────────────────────────────────────────────
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission.",
}
# Undergraduate (Columbia College) admission via the Common Application. Columbia is
# test-optional: SAT/ACT scores are not required but are considered if submitted
# (CDS 2024-25 item C8).
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application", "required": True},
        {"name": "Columbia-specific writing supplement", "required": True},
        {"name": "Secondary-school report + transcript", "required": True},
        {"name": "Counselor recommendation", "required": True},
        {"name": "Two teacher recommendations", "required": True},
        {"name": "$85 application fee; need-based fee waivers available", "required": True},
        {
            "name": "Standardized test scores (optional)",
            "required": False,
            "note": (
                "Columbia is test-optional: SAT/ACT scores are not required for admission "
                "but are considered if submitted."
            ),
        },
    ],
    "deadlines": [
        {"round": "Early Decision", "date": "November 1"},
        {"round": "Regular Decision", "date": "January 1"},
    ],
    "recommendations": {
        "required": 3,
        "note": "Two teacher recommendations plus a counselor recommendation.",
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "Duolingo English Test"],
            "required": False,
            "note": "English-proficiency proof may be required for non-native speakers.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Columbia Undergraduate Admissions — Apply",
                "url": "https://undergrad.admissions.columbia.edu/apply",
            }
        ],
    },
    "source": "Columbia Undergraduate Admissions",
    "source_url": "https://undergrad.admissions.columbia.edu/apply/first-year",
}

# Graduate (Columbia Business School MBA) admission via the CBS application.
_REQ_MBA = {
    "materials": [
        {"name": "Columbia Business School online application", "required": True},
        {"name": "Essays (per the application prompts)", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "One professional recommendation", "required": True},
        {"name": "Résumé", "required": True},
        {
            "name": "GMAT, GRE or Executive Assessment",
            "required": True,
            "note": "GMAT, GRE or the Executive Assessment accepted; a waiver may be requested.",
        },
        {"name": "Interview (by invitation)", "required": False},
        {"name": "$250 application fee", "required": True},
    ],
    "deadlines": [
        {"round": "Early Decision (binding)", "date": "Early October"},
        {"round": "Regular Decision — January start", "date": "Rolling, see program page"},
        {"round": "Regular Decision — August start", "date": "Rolling, see program page"},
    ],
    "recommendations": {
        "required": 1,
        "note": "One professional recommendation submitted through the application.",
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "PTE"],
            "required": False,
            "note": (
                "An English-proficiency test may be required for applicants whose native "
                "language is not English."
            ),
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Columbia Business School — Full-Time MBA Admissions",
                "url": "https://business.columbia.edu/mba/admissions",
            }
        ],
    },
    "source": "Columbia Business School — Full-Time MBA Admissions",
    "source_url": "https://business.columbia.edu/mba/admissions",
}

# Generic Columbia graduate / professional admission set. Each school administers its own
# admissions; the materials below are common across Columbia graduate programs, and
# deadlines vary by program (commonly winter) — applicants are pointed to the program's own
# admissions page via the program website.
_REQ_GRAD_GENERIC = {
    "materials": [
        {"name": "Program online application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose / personal statement", "required": True},
        {"name": "Résumé / CV", "required": True},
        {
            "name": "Letters of recommendation",
            "required": True,
            "note": "Most Columbia graduate programs require two to three letters.",
        },
        {
            "name": "Standardized test scores (GRE)",
            "required": False,
            "note": "Test requirements vary by program (required, optional or not accepted).",
        },
    ],
    "deadlines": [
        {"round": "Application deadline", "date": "Varies by program — see the program page"},
    ],
    "recommendations": {
        "required": 3,
        "note": (
            "Most Columbia graduate programs require three letters of recommendation "
            "(some require two)."
        ),
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": True,
            "note": (
                "Required for applicants whose native language is not English; an "
                "exemption applies to degrees earned where English is the language of "
                "instruction."
            ),
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Columbia University — Graduate admissions (by school)",
                "url": "https://www.columbia.edu/content/academics/schools",
            }
        ],
    },
    "source": "Columbia University graduate & professional admissions",
    "source_url": "https://www.columbia.edu/content/academics/schools",
}


def _requirements_for(spec: dict) -> dict:
    """Pick the admissions requirement set for a program by slug / degree type."""
    if spec["slug"] == "columbia-mba":
        return dict(_REQ_MBA)
    if spec["degree_type"] == "masters":
        return dict(_REQ_GRAD_GENERIC)
    return dict(_REQ_UNDERGRAD)


# Real Columbia campus photo (Low Memorial Library on the Morningside Heights campus) —
# Wikimedia Commons, hotlinkable landscape JPG (verified HTTP 200). Leads the institution
# hero.
_CAMPUS_PHOTO = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/"
    "Low_Memorial_Library_Columbia_University_NYC.jpg/"
    "1920px-Low_Memorial_Library_Columbia_University_NYC.jpg"
)


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich Columbia to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Columbia is absent — safe on fresh/CI databases.
    """
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    # Shallow-merge JSONB: every sub-object we provide is complete.
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    # Drop any stale value for a path we explicitly declare omitted, so the merge can't
    # keep serving a figure the enrichment run refused to assert.
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
    inst.founded_year = 1754
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.columbia.edu"
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
        # No school carries its own keyword-relevant feed (only the flagship program does);
        # always assign None so a stale value on a pre-existing row is cleared.
        sc.content_sources = None
        by_name[spec["name"]] = sc
    # This is a PARTIAL enrichment: more Columbia schools exist and are added by a resume
    # run. We deliberately DO NOT delete schools outside our canonical set, so the partial
    # composes safely with later runs on the same university.
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


def _program_standard(slug: str) -> dict:
    """Per-program omitted-field list (verified-unavailable), for _standard."""
    omitted: list[str] = []
    # Only the Columbia Business School MBA flagship carries a per-program employment rate
    # and industry breakdown. Every other program reports a program-scope median earnings
    # (Scorecard FOS) and honestly omits the program-level employment rate / top industries.
    if slug != "columbia-mba":
        omitted += [
            "outcomes_data.employment_rate",
            "outcomes_data.top_industries",
        ]
    if slug not in _TRACKS_BY_SLUG:
        omitted.append("tracks")
    if slug not in _CLASS_PROFILE_BY_SLUG:
        omitted.append("class_profile.cohort_size")
    if slug not in _FACULTY_BY_SLUG:
        omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    if slug != "columbia-mba":
        # Only the flagship carries its own keyword-relevant feed; catalog programs
        # surface the institution feed rather than a per-program one.
        omitted.append("content_sources")
    if slug in _TUITION_OMITTED_SLUGS:
        # Graduate programs whose program tuition is published only on the
        # JavaScript-rendered Bursar pages (omitted rather than guessed).
        omitted.append("cost_data.tuition_usd")
    return _standard(omitted)


def _apply_programs(session: Session, inst: Institution, school_by_name: dict[str, School]) -> None:
    canonical = set(PROGRAM_SLUGS)
    existing = {
        p.slug: p
        for p in session.scalars(select(Program).where(Program.institution_id == inst.id))
        if p.slug
    }
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
        # Website: verified program/department page where available, else the owning
        # school's site.
        p.website_url = _WEBSITE_BY_SLUG.get(slug) or _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "in_person")
        # Only the flagship carries its own feed (content_sources omitted for the rest).
        p.content_sources = _MBA_CONTENT if slug == "columbia-mba" else None
        # Cost: graduate programs use verified per-program cost where available;
        # undergraduate uses the published College rates.
        cost_override = _COST_BY_SLUG.get(slug)
        if cost_override is not None:
            p.tuition = cost_override.get("tuition_usd")
            p.cost_data = dict(cost_override)
        else:
            p.tuition = _TUITION_UG
            p.cost_data = {
                "tuition_usd": _TUITION_UG,
                "total_cost_of_attendance": _UNDERGRAD_COA,
                "avg_net_price": _AVG_NET_PRICE,
                "breakdown": {
                    "tuition": _TUITION_UG,
                    "total_cost_of_attendance": _UNDERGRAD_COA,
                },
                "funded": False,
                "note": (
                    "Published 2024-25 Columbia tuition with the College Scorecard cost of "
                    "attendance and average net price. Columbia is need-blind for domestic "
                    "first-year applicants and meets 100% of demonstrated need, so most "
                    "families pay far less than the sticker price (average net price ≈ "
                    "$21,600)."
                ),
                "source": (
                    "Columbia Student Financial Services (2024-25) + "
                    "College Scorecard (UNITID 190150)"
                ),
                "source_url": (
                    "https://collegescorecard.ed.gov/school/?190150-Columbia-University-in-the-City-of-New-York"
                ),
                "year": "2024-25",
            }
        # Admissions: undergraduate, MBA or generic graduate set by slug / degree type.
        p.application_requirements = _requirements_for(spec)
        # Outcomes precedence: CBS flagship → Scorecard FOS (program) → institution median.
        outcomes = _outcomes_for(slug)
        outcomes["_standard"] = _program_standard(slug)
        p.outcomes_data = outcomes
        if spec["degree_type"] == "masters":
            p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_GRAD_BASELINE
            p.highlights = _HL_BY_SLUG.get(slug) or _HL_GRAD_BASELINE
        else:
            p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_BASELINE
            p.highlights = _HL_BY_SLUG.get(slug) or _HL_BASELINE
        # Always assign so a stale value on a pre-existing row is cleared (tracks is
        # recorded as omitted where unverified, and match_service reads program.tracks).
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        # Application deadline (upcoming undergraduate Regular Decision closes Jan 1).
        p.application_deadline = (
            None if spec["degree_type"] == "masters" and slug != "columbia-mba"
            else date(2026, 1, 6) if slug == "columbia-mba"
            else date(2027, 1, 1)
        )
    session.flush()
    # Reconcile only the programs THIS partial owns (those whose slug starts with the
    # canonical prefix but is no longer in the set). We do NOT touch Columbia's other
    # programs (added/enriched by other runs), so this partial composes safely with the
    # resume run. Unpublish or delete only stale "columbia-*" rows we previously created.
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        sl = p.slug or ""
        if sl in canonical or not sl.startswith("columbia-"):
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
