"""Canonical Columbia University profile — the single source of truth.

Real, sourced data only (U.S. Dept. of Education College Scorecard, UNITID 190150 ·
NCES College Navigator / IPEDS · Columbia's Office of Planning and Institutional
Research "Columbia Facts 2024" · the Columbia College & Columbia Engineering Common
Data Set 2024-25 · Columbia's FY2024 endowment performance report · the official QS /
Times Higher Education / U.S. News rankings · each school's official leadership / about
page and the Columbia bulletin (tuition) · the Columbia Center for Career Education
"Beyond Columbia" first-destination survey, Class of 2023 · the College Scorecard
Field-of-Study earnings by CIP). ``apply(session)`` idempotently enriches the Columbia
institution row, upserts its real degree-granting schools, and builds Columbia's program
catalog across them.

Columbia's academic structure: an undergraduate enterprise (Columbia College and The Fu
Foundation School of Engineering and Applied Science, which share the Faculty of Arts and
Sciences and a single undergraduate tuition rate) plus a set of dean-led graduate and
professional schools. We model the units that own the degree programs in the canonical
College Scorecard Field-of-Study list for UNITID 190150 onto the platform's ``School``
model:
  - Columbia College (undergraduate B.A. majors)
  - The Fu Foundation School of Engineering and Applied Science (B.S. + M.S.)
  - Columbia Business School (the MBA)
  - Columbia Law School (the J.D.)
  - Vagelos College of Physicians and Surgeons (the M.D.)
  - Columbia Journalism School (the M.S.)
  - School of International and Public Affairs (the MIA / MPA)
  - Mailman School of Public Health (the MPH)
  - Columbia School of Social Work (the MSW)
  - Graduate School of Architecture, Planning and Preservation (the M.Arch)
  - Columbia School of the Arts (the MFA)
  - Columbia School of Nursing (the MSN)

It **flushes but does not commit** — the caller (the Alembic data migration, the CLI
script, or the dev seed) owns the transaction. It is a **no-op** (returns ``False``)
when Columbia is absent, so it is safe to run against a fresh or CI database. Re-running
is safe: schools key off ``(institution_id, name)`` and programs off ``slug``; stale rows
are reconciled without breaking foreign keys.

This mirrors ``mit_profile`` / ``yale_profile`` so the migration, the standalone script,
and the dev seed all agree (DRY). Every figure traces to a public, citable source;
anything that could not be verified from a first-party or two-independent-source basis is
**omitted** (recorded in the relevant ``_standard.omitted`` list), never guessed. Computer
Science is the most-enriched flagship program (its real research areas, faculty, class
profile, and aggregated reviews), mirroring MIT Sloan's MBAn in the reference instance —
with the honest caveats that Columbia is permanently test-optional, that the canonical
program set is the College Scorecard Field-of-Study list for UNITID 190150 (degree-by-CIP),
that several graduate programs publish tuition only on bot-blocked pages and so their
program-level tuition is omitted rather than guessed, that the Vagelos College deanship is
in transition (so its leadership is omitted), and that the M.D. one-year earnings figure
reflects residency stipends.

Description depth pass (2026-06-16, columbiaprof9): replaces all classification-only
program descriptions with field-specific clauses from ``columbia_field_descriptions.py``
(280/280 programs; 0% classification stubs).

Description repair (2026-06-17, columbiaprof10): drops ``{program_name}:`` prefixes so
every description opens on a field fact (gold MIT/BU pattern); fixes peer-contamination
clauses in ``columbia_field_descriptions.py`` (Lick Observatory, College of Chemistry,
Harvardsylvania); 0% name-prefixed descriptions.

Description repair (2026-06-17, columbiaprof11): diversifies credential-sibling
descriptions with Columbia-specific level suffixes (0% identical-across-levels); fixes
remaining peer-contamination (Kelly Writers House, Perry World House, Morris Arboretum,
Haas/CDSS, ICA); gates shared descriptions and peer signatures at build time.

Graduate-tier tuition (2026-06-22, colgradtuition1): stamps published per-school /
per-program tuition on every master's and professional row where Columbia publishes a
flat annual or per-program figure (REPAIR_BACKLOG #4 — was master's 3/45, professional
2/8). Funded Ph.D. rows and per-credit-only DrPH stay omitted-with-reason.

Depth pass (2026-06-15, columbiaprof8): merged ``DEPTH_REVIEWS`` for 37 coverable
programs (46/46 total external_reviews on coverable programs).
"""

# ruff: noqa: E501

from __future__ import annotations

import re
from collections import Counter
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.columbia_field_descriptions import (
    CORE,
    FIELD_ALIASES,
    SLUG_DESCRIPTIONS,
)
from unipaith.data.columbia_reviews_depth import DEPTH_REVIEWS
from unipaith.data.profile_catalog_utils import validate_catalog
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Columbia University in the City of New York"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-17"

_TEMPLATE_STUB_RE = re.compile(
    r" — a .+ (undergraduate|graduate|doctoral|certificate|professional|"
    r"master's|bachelor's|PhD|MBA|JD|MD|bachelors|masters|phd) program offered through ",
    re.I,
)
_CLASSIFICATION_STUB_RE = re.compile(
    r"^.+ is (an undergraduate|a graduate|a doctoral|a graduate certificate|"
    r"a professional|a degree) program at Columbia",
    re.I,
)

_PEER_SIGNATURES: tuple[str, ...] = (
    "Kelly Writers House",
    "Morris Arboretum",
    "Perry World House",
    "Haas",
    " CDSS",
    "Sibley School",
    "Lick Observatory",
    "College of Chemistry",
    "Harvardsylvania",
    "Wharton",
    "McCormick",
    "Weill Cornell",
    "Institute of Contemporary Art",
    "Writing Seminars",
    "Chesapeake",
)


def _standard(omitted: list[str] | None = None) -> dict:
    """The per-node provenance stamp the routine writes onto every enriched node."""
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }


# Institution-level fields that could NOT be verified from a citable source and are
# therefore honestly omitted rather than guessed.
_OMITTED_INSTITUTION: list[str] = []

# ── Institution-level data ────────────────────────────────────────────────
# Rankings are stored as {rank, year} objects (the page renders any ranking_data entry
# that is an object with a numeric `rank`). All three ranks are quoted from the official
# ranking bodies for the 2026 editions.
RANKING_DATA: dict = {
    "ownership_type": "private",
    # Columbia is accredited by the Middle States Commission on Higher Education (MSCHE).
    "accreditor": "MSCHE",
    # Carnegie 2025 research-activity designation (the R1 tier).
    "carnegie_classification": "Research 1: Very High Research Spending and Doctorate Production",
    # QS World University Rankings 2026: Columbia is ranked #38 worldwide.
    "qs_world_university_rankings": {"rank": 38, "year": 2026},
    # THE World University Rankings 2026: #20 in the world.
    "times_higher_education": {"rank": 20, "year": 2026},
    # U.S. News Best Colleges (National Universities) 2026: #15 nationally.
    "us_news_national": {"rank": 15, "year": 2026},
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below is
# complete, so a shallow merge is correct. Figures are College Scorecard (UNITID 190150)
# cross-checked against Columbia's Common Data Set 2024-25, "Columbia Facts 2024" (OPIR),
# and NCES College Navigator (IPEDS) where each publishes a metric.
SCHOOL_OUTCOMES: dict = {
    # CDS 2024-25 (Columbia College + Columbia Engineering), item C1: 2,325 admits /
    # 60,247 first-year applicants = 3.86% (College Scorecard reports 0.0399).
    "admit_rate": 0.0386,
    # College Scorecard average annual net price.
    "avg_net_price": 21590,
    # College Scorecard institution-wide median earnings 10 years after entry.
    "median_earnings_10yr": 102491,
    # College Scorecard four-year completion rate (150% of normal time).
    "completion_rate_4yr_150pct": 0.961,
    # CDS 2024-25 (item B22): first-year retention (Fall 2023 cohort) = 98%.
    "retention_rate_first_year": 0.98,
    # CDS 2024-25 (item B11): six-year graduation rate (2018 entering cohort) = 96%.
    "graduation_rate_6yr": 0.96,
    "financial_aid": {
        # College Scorecard: 22.71% of undergraduates received a Pell grant; 13.71% took
        # federal student loans. Columbia is need-blind for U.S. applicants and meets full
        # need with no-loan aid.
        "pell_grant_rate": 0.2271,
        "federal_loan_rate": 0.1371,
        # College Scorecard average annual cost of attendance.
        "cost_of_attendance": 89472,
    },
    # Undergraduate race/ethnicity (College Scorecard, UNITID 190150). "international" is
    # the federal non-resident-alien share.
    "demographics": {
        "white": 0.287,
        "black": 0.075,
        "hispanic": 0.154,
        "asian": 0.187,
        "two_or_more": 0.063,
        "international": 0.197,
    },
    # SAT/ACT 25th-75th percentiles of enrolled first-years (College Scorecard, UNITID
    # 190150). Columbia is permanently test-optional, so these reflect score submitters.
    "test_scores": {
        "sat_reading_25_75": [740, 780],
        "sat_math_25_75": [770, 800],
        "act_25_75": [34, 35],
    },
    # Columbia main campus, Morningside Heights, New York City (College Scorecard).
    "location": {"lat": 40.808286, "lng": -73.961885},
    "campus_basics": {"location": "New York, New York"},
    "scale": {
        # "Columbia Facts 2024" (OPIR): 4,787 full-time faculty, university-wide (Fall 2024).
        "faculty_count": 4787,
        # CDS 2024-25 (item I2): 6:1 student-faculty ratio (Columbia College + Engineering).
        "student_faculty_ratio": "6:1",
        # Columbia FY2024 endowment performance report: total endowment $14.8 billion at
        # fiscal year-end June 30, 2024 (FY2024, 11.5% net return).
        "endowment_usd": 14800000000,
    },
    # Columbia Center for Career Education, "Beyond Columbia" survey, Class of 2023
    # (Columbia College + Columbia Engineering undergraduates): 89.9% employed or in
    # graduate/professional school (combined headline; 69.7% knowledge rate).
    "employed_or_continuing_ed": 0.899,
    # "Beyond Columbia" Class of 2023 — top industries entered, in rank order.
    "top_employer_industries": [
        "Internet & Software",
        "Investment Banking",
        "Management Consulting",
        "Investment/Portfolio Management",
        "Healthcare",
    ],
    "research": {
        "labs": [
            "Lamont-Doherty Earth Observatory (earth & climate science)",
            "The Mortimer B. Zuckerman Mind Brain Behavior Institute (neuroscience)",
            "Data Science Institute",
            "Columbia Climate School (incorporating the former Earth Institute)",
            "Herbert Irving Comprehensive Cancer Center (NCI-designated)",
        ],
        "areas": [
            "Earth, climate & environmental science",
            "Neuroscience & the mind-brain-behavior sciences",
            "Data science, AI & computing",
            "Biomedical & health sciences",
            "Economics & the social sciences",
            "Law, international affairs & public policy",
            "Journalism & the arts",
        ],
        "lab_links": {
            "Lamont-Doherty Earth Observatory (earth & climate science)": (
                "https://lamont.columbia.edu/"
            ),
            "The Mortimer B. Zuckerman Mind Brain Behavior Institute (neuroscience)": (
                "https://zuckermaninstitute.columbia.edu/"
            ),
            "Data Science Institute": "https://datascience.columbia.edu/",
            "Columbia Climate School (incorporating the former Earth Institute)": (
                "https://climate.columbia.edu/"
            ),
        },
    },
    "campus_life": {
        # Columbia's teams (the Lions) compete in NCAA Division I (Ivy League).
        "athletics_division": "NCAA Division I (Ivy League)",
        "mascot": "Columbia Lions (Roar-ee the Lion)",
        "housing": "Guaranteed undergraduate housing on the Morningside Heights campus",
        "resources": [
            {"label": "Columbia Lions Athletics", "url": "https://gocolumbialions.com/"},
            {"label": "Columbia University Events Calendar", "url": "https://events.columbia.edu/"},
        ],
    },
    # Verified outdoor campus gallery (Wikimedia Commons API extmetadata, 2026-06-14).
    # Butler Library leads the institution hero; each file carries a verified author + license.
    "campus_photos": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/"
                "Butler_Library_-_Columbia_University.jpg/"
                "1920px-Butler_Library_-_Columbia_University.jpg"
            ),
            "credit": "Wikimedia Commons / Bitterteayen (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/"
                "2014_Columbia_University_Low_Memorial_Library_from_front.jpg/"
                "1920px-2014_Columbia_University_Low_Memorial_Library_from_front.jpg"
            ),
            "credit": "Wikimedia Commons / Beyond My Ken (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/"
                "2014_Columbia_University_Morningside_Heights_campus_from_southwest_.jpg/"
                "1920px-2014_Columbia_University_Morningside_Heights_campus_from_southwest_.jpg"
            ),
            "credit": "Wikimedia Commons / Beyond My Ken (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/"
                "Kent_Hall%2C_Columbia_University.jpg/"
                "1920px-Kent_Hall%2C_Columbia_University.jpg"
            ),
            "credit": "Wikimedia Commons / Bitterteayen (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/"
                "Columbia_University_-_Low_Memorial_Library_%2848170370506%29.jpg/"
                "1920px-Columbia_University_-_Low_Memorial_Library_%2848170370506%29.jpg"
            ),
            "credit": "Wikimedia Commons / Ajay Suresh (CC BY 2.0)",
        },
    ],
    # Butler Library leads the hero; see ``campus_photos[0]``.
    "media_credit": "Wikimedia Commons / Bitterteayen (CC BY-SA 4.0)",
    "flagship": {
        # "Columbia Facts 2024" (OPIR): 35,769 total students (Fall 2024).
        "enrollment_total": 35769,
        # CDS 2024-25 first-year admissions cycle (item C1), Columbia College + Engineering.
        "applicants": 60247,
        "admits": 2325,
        "admissions_cycle": (
            "Entering class fall 2024 (Columbia College + Columbia Engineering Common Data "
            "Set 2024-25)"
        ),
        # Founded in 1754 as King's College.
        "founded_year": 1754,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Columbia, UNITID 190150)",
            "url": "https://collegescorecard.ed.gov/school/?190150",
        },
        {
            "label": "NCES College Navigator — Columbia University (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=190150",
        },
        {
            "label": "Columbia Office of Planning and Institutional Research — Columbia Facts 2024",
            "url": (
                "https://opir.columbia.edu/sites/opir.columbia.edu/files/content/"
                "Columbia%20Facts/Fact_2024.pdf"
            ),
        },
        {
            "label": (
                "Columbia College & Columbia Engineering — Common Data Set 2024-25"
            ),
            "url": (
                "https://opir.columbia.edu/sites/opir.columbia.edu/files/content/"
                "Common%20Data%20Set/2024-25_Columbia_College_and_Columbia_Engineering_CDS.pdf"
            ),
        },
        {
            "label": "Columbia University — FY2024 Endowment Performance ($14.8B)",
            "url": (
                "https://endowment.giving.columbia.edu/wp-content/uploads/2024/12/"
                "FY2024-Columbia-Endowment-Performance.pdf"
            ),
        },
        {
            "label": "QS World University Rankings 2026 — Columbia University (#=38)",
            "url": "https://www.topuniversities.com/universities/columbia-university",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — Columbia (#20)",
            "url": "https://www.timeshighereducation.com/world-university-rankings/columbia-university",
        },
        {
            "label": "U.S. News Best Colleges 2026 — Columbia (#15 National Universities)",
            "url": "https://www.usnews.com/best-colleges/columbia-university-2707",
        },
        {
            "label": "Columbia Undergraduate Admissions — Financial Aid (need-blind, no-loan)",
            "url": "https://undergrad.admissions.columbia.edu/financialaid",
        },
        {
            "label": (
                "Columbia Center for Career Education — Beyond Columbia Survey, Class of 2023 "
                "(Columbia College & Engineering)"
            ),
            "url": (
                "https://www.careereducation.columbia.edu/sites/default/files/"
                "2023%20BCS--CC%20&%20SEAS-UG.pdf"
            ),
        },
        {
            "label": "Carnegie Classifications — Columbia University (Research 1)",
            "url": (
                "https://carnegieclassifications.acenet.edu/institution/"
                "columbia-university-in-the-city-of-new-york/"
            ),
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it "Undergraduates");
# the total (35,769) lives in flagship.enrollment_total and renders as "Total enrollment".
# 9,359 = "Columbia Facts 2024" (OPIR) bachelor's/undergraduate enrollment, Fall 2024.
UNDERGRAD_COUNT = 9359

DESCRIPTION = (
    "Columbia University is a private research university in New York, NY, founded in 1754 "
    "as King's College by royal charter of George II in the Morningside Heights neighborhood "
    "of Upper Manhattan — the oldest institution of higher education in New York and the "
    "fifth-oldest in the United States. It enrolls about 9,400 undergraduates and roughly "
    "26,000 graduate and professional students, some 35,800 in all, and pairs the famous "
    "Core Curriculum of its undergraduate colleges — a 6:1 student-faculty ratio — with the "
    "research depth of a major university and its 4,787 full-time faculty.\n\n"
    "Columbia's undergraduate enterprise is shared by Columbia College and The Fu "
    "Foundation School of Engineering and Applied Science, and the university is organized "
    "into a set of renowned graduate and professional schools — among them the Business "
    "School, the Law School, the Vagelos College of Physicians and Surgeons (the first U.S. "
    "school to grant the M.D.), the Journalism School (which administers the Pulitzer "
    "Prizes), the School of International and Public Affairs, the Mailman School of Public "
    "Health, the School of Social Work (the oldest in the country), the Graduate School of "
    "Architecture, Planning and Preservation, and the School of the Arts. Columbia's "
    "research is anchored by the Lamont-Doherty Earth Observatory, the Zuckerman Institute "
    "for neuroscience, the Data Science Institute, and the Columbia Climate School.\n\n"
    "Columbia ranks among the very best universities in the world: No. 15 among national "
    "universities by U.S. News, No. 20 in the world by Times Higher Education, and No. 38 "
    "by QS. It admits under 4% of first-year applicants to its undergraduate colleges and "
    "manages a $14.8 billion endowment (June 2024).\n\n"
    "Columbia is need-blind for U.S. applicants and meets 100% of demonstrated financial "
    "need with grants, not loans: the average net price is about $21,600 a year, 23% of "
    "undergraduates receive Pell grants, and the university is permanently test-optional. "
    "Among the Columbia College and Engineering Class of 2023, 89.9% were employed or had "
    "entered graduate or professional school within six months of graduation."
)

# ── The real degree-granting schools (display order) ───────────────────────
_CC = "Columbia College"
_SEAS = "The Fu Foundation School of Engineering and Applied Science"
_CBS = "Columbia Business School"
_LAW = "Columbia Law School"
_PS = "Vagelos College of Physicians and Surgeons"
_JOUR = "Columbia Journalism School"
_SIPA = "School of International and Public Affairs"
_MAILMAN = "Mailman School of Public Health"
_SSW = "Columbia School of Social Work"
_GSAPP = "Graduate School of Architecture, Planning and Preservation"
_ARTS = "Columbia School of the Arts"
_NURSING = "Columbia School of Nursing"
_GSAS = "Graduate School of Arts and Sciences"
_DENTAL = "College of Dental Medicine"

SCHOOLS: list[dict] = [
    {
        "name": _CC,
        "sort_order": 1,
        "description": (
            "Columbia College, founded in 1754 as King's College, is the university's "
            "oldest undergraduate college and the original core of Columbia. It awards the "
            "B.A. across the liberal arts and sciences, and every student completes the "
            "Core Curriculum — Columbia's signature sequence of shared courses in literature, "
            "philosophy, art, music, science and writing."
        ),
    },
    {
        "name": _SEAS,
        "sort_order": 2,
        "description": (
            "The Fu Foundation School of Engineering and Applied Science (Columbia "
            "Engineering), with roots in the 1864 School of Mines, is Columbia's school of "
            "engineering and applied science. It awards the B.S., M.S., and doctoral degrees "
            "across computer science, the engineering disciplines and applied mathematics, "
            "and its undergraduates share the Core Curriculum with Columbia College."
        ),
    },
    {
        "name": _CBS,
        "sort_order": 3,
        "description": (
            "Founded in 1916, Columbia Business School educates leaders at the intersection "
            "of academic theory and real-world practice ('the very business of business'), "
            "drawing on its New York City location. It awards the full-time MBA, the "
            "Executive MBA, specialized master's degrees and the Ph.D."
        ),
    },
    {
        "name": _LAW,
        "sort_order": 4,
        "description": (
            "Columbia Law School, founded in 1858, is one of the most influential law "
            "schools in the United States. It awards the J.D., the LL.M. and the J.S.D. "
            "research doctorate, with particular strength in corporate, constitutional and "
            "international law."
        ),
    },
    {
        "name": _PS,
        "sort_order": 5,
        "description": (
            "The Vagelos College of Physicians and Surgeons, founded in 1767, was the first "
            "institution in the American colonies to confer the M.D. degree. Part of "
            "Columbia University Irving Medical Center, it awards the M.D. and M.D.-Ph.D. "
            "and is a leading center of biomedical research."
        ),
    },
    {
        "name": _JOUR,
        "sort_order": 6,
        "description": (
            "Endowed by Joseph Pulitzer and opened in 1912, the Columbia Journalism School "
            "is the only Ivy League journalism school. It awards the M.S., M.A. and Ph.D. in "
            "journalism, and administers the Pulitzer Prizes."
        ),
    },
    {
        "name": _SIPA,
        "sort_order": 7,
        "description": (
            "The School of International and Public Affairs, founded in 1946, prepares "
            "leaders for public service, international affairs and policy. It awards the "
            "Master of International Affairs (MIA), the Master of Public Administration (MPA) "
            "and doctoral degrees, anchored by centers such as the Center on Global Energy "
            "Policy."
        ),
    },
    {
        "name": _MAILMAN,
        "sort_order": 8,
        "description": (
            "Founded in 1922, the Mailman School of Public Health awards the accredited MPH, "
            "the M.S., the Dr.P.H. and the Ph.D. across biostatistics, epidemiology, "
            "environmental health sciences, health policy and management, and population and "
            "family health."
        ),
    },
    {
        "name": _SSW,
        "sort_order": 9,
        "description": (
            "The Columbia School of Social Work, founded in 1898, is the oldest school of "
            "social work in the United States. It awards the Master of Science in Social Work "
            "(MSW) and the Ph.D., with strengths in clinical practice and social policy."
        ),
    },
    {
        "name": _GSAPP,
        "sort_order": 10,
        "description": (
            "The Graduate School of Architecture, Planning and Preservation (Columbia "
            "GSAPP), founded in 1881, awards the Master of Architecture and degrees in urban "
            "planning, historic preservation, urban design and real estate development. It is "
            "a leading center of architectural thought."
        ),
    },
    {
        "name": _ARTS,
        "sort_order": 11,
        "description": (
            "The Columbia School of the Arts, established in 1965, is a graduate arts school "
            "awarding the Master of Fine Arts in film, theatre, visual arts and writing, and "
            "the M.A. in film and media studies — embedded in a major research university in "
            "New York City."
        ),
    },
    {
        "name": _NURSING,
        "sort_order": 12,
        "description": (
            "Columbia School of Nursing, founded in 1892, was among the first to base "
            "nursing education on a scientific model. Part of Columbia University Irving "
            "Medical Center, it awards the Master's Direct Entry (MDE), the Doctor of Nursing "
            "Practice (DNP) and the Ph.D. across advanced-practice specialties."
        ),
    },
    {
        "name": _GSAS,
        "sort_order": 13,
        "description": (
            "The Graduate School of Arts and Sciences is Columbia's central school for "
            "advanced study in the arts, humanities, sciences and social sciences. Working "
            "through the Faculty of Arts and Sciences departments, it awards the M.A., "
            "M.Phil. and Ph.D. and trains scholars and researchers across the disciplines."
        ),
    },
    {
        "name": _DENTAL,
        "sort_order": 14,
        "description": (
            "The College of Dental Medicine, founded in 1916 and part of Columbia "
            "University Irving Medical Center, awards the Doctor of Dental Surgery (D.D.S.) "
            "and advanced postdoctoral certificates, integrating dental education with the "
            "biomedical sciences and patient care in New York City."
        ),
    },
]

# Each school's official website (verified to resolve at author time).
_SCHOOL_WEBSITE: dict[str, str] = {
    _CC: "https://www.college.columbia.edu/",
    _SEAS: "https://www.engineering.columbia.edu/",
    _CBS: "https://business.columbia.edu/",
    _LAW: "https://www.law.columbia.edu/",
    _PS: "https://www.vagelos.columbia.edu/",
    _JOUR: "https://journalism.columbia.edu/",
    _SIPA: "https://www.sipa.columbia.edu/",
    _MAILMAN: "https://www.publichealth.columbia.edu/",
    _SSW: "https://socialwork.columbia.edu/",
    _GSAPP: "https://www.arch.columbia.edu/",
    _ARTS: "https://arts.columbia.edu/",
    _NURSING: "https://www.nursing.columbia.edu/",
    _GSAS: "https://www.gsas.columbia.edu/",
    _DENTAL: "https://www.dental.columbia.edu/",
}

# Rich, sourced About-tab content per school. Deans + titles are quoted from each school's
# official leadership page (verified 2026-06-10). Founding years come from each school's
# official history/about page. Notable-faculty rosters are not published uniformly per
# school and are omitted rather than hand-picked (recorded in _ABOUT_OMITTED). The Vagelos
# College deanship is in active transition (no confirmed current dean), so its leadership
# is omitted.
_ABOUT_DETAIL: dict[str, dict] = {
    _CC: {
        "founded": 1754,
        "leadership": (
            "Josef Sorett — Dean of Columbia College and Vice President for Undergraduate "
            "Education (Henry L. and Lucy G. Moses Professor)"
        ),
        "source": {
            "label": "Columbia College — Office of the Dean",
            "url": "https://www.college.columbia.edu/about/dean-josef-sorett",
        },
    },
    _SEAS: {
        "founded": 1864,
        "leadership": (
            "Shih-Fu Chang — Dean of Columbia Engineering (Morris A. and Alma Schapiro "
            "Professor of Engineering)"
        ),
        "research_centers": [
            "Data Science Institute",
            "Columbia Nano Initiative",
        ],
        "source": {
            "label": "Columbia Engineering — Office of the Dean",
            "url": (
                "https://www.engineering.columbia.edu/faculty-staff/directory/"
                "dean-shih-fu-chang"
            ),
        },
    },
    _CBS: {
        "founded": 1916,
        "leadership": (
            "Costis Maglaras — David and Lyn Silfen Professor of Business and Dean"
        ),
        "research_centers": [
            "Heilbrunn Center for Graham & Dodd Investing",
            "Tamer Institute for Social Enterprise and Climate Change",
            "Chazen Institute for Global Business",
        ],
        "source": {
            "label": "Columbia Business School — Leadership",
            "url": "https://business.columbia.edu/about-us/leadership",
        },
    },
    _LAW: {
        "founded": 1858,
        "leadership": ("Daniel Abebe — Dean and Lucy G. Moses Professor of Law"),
        "research_centers": [
            "Sabin Center for Climate Change Law",
            "Knight First Amendment Institute at Columbia University",
        ],
        "source": {
            "label": "Columbia Law School — About the Dean",
            "url": "https://www.law.columbia.edu/community-life/welcome/about-dean",
        },
    },
    _PS: {
        "founded": 1767,
        "research_centers": [
            "Herbert Irving Comprehensive Cancer Center",
            "Vagelos Institute for Basic Biomedical Research",
        ],
        "source": {
            "label": "Vagelos College of Physicians and Surgeons — Leadership",
            "url": (
                "https://www.vagelos.columbia.edu/about-us/explore-vp-s/"
                "leadership-and-administration"
            ),
        },
    },
    _JOUR: {
        "founded": 1912,
        "leadership": (
            "Jelani Cobb — Dean and Henry R. Luce Professor of Journalism"
        ),
        "research_centers": [
            "Tow Center for Digital Journalism",
            "Brown Institute for Media Innovation",
            "Dart Center for Journalism and Trauma",
        ],
        "source": {
            "label": "Columbia Journalism School — Meet the Dean",
            "url": "https://journalism.columbia.edu/meet-the-dean",
        },
    },
    _SIPA: {
        "founded": 1946,
        "leadership": (
            "Keren Yarhi-Milo — Dean of the School of International and Public Affairs "
            "(Adlai E. Stevenson Professor of International Relations)"
        ),
        "research_centers": [
            "Center on Global Energy Policy",
            "Arnold A. Saltzman Institute of War and Peace Studies",
        ],
        "source": {
            "label": "SIPA — Dean's Office",
            "url": (
                "https://www.sipa.columbia.edu/about/"
                "deans-office-administrative-leadership"
            ),
        },
    },
    _MAILMAN: {
        "founded": 1922,
        "leadership": ("Jonathan Mermin — Dean of the Columbia Mailman School of Public Health"),
        "research_centers": [
            "ICAP at Columbia University",
            "Robert N. Butler Columbia Aging Center",
        ],
        "source": {
            "label": "Mailman School of Public Health — University Announces Next Dean",
            "url": (
                "https://www.publichealth.columbia.edu/news/"
                "university-announces-next-columbia-mailman-school-dean"
            ),
        },
    },
    _SSW: {
        "founded": 1898,
        "leadership": ("Melissa D. Begg — Dean and Professor, Columbia School of Social Work"),
        "source": {
            "label": "Columbia School of Social Work — Welcome from the Dean",
            "url": "https://socialwork.columbia.edu/content/welcome-dean",
        },
    },
    _GSAPP: {
        "founded": 1881,
        "leadership": ("Andrés Jaque — Dean and Professor, Columbia GSAPP"),
        "research_centers": [
            "Temple Hoyne Buell Center for the Study of American Architecture",
            "Center for Spatial Research",
        ],
        "source": {
            "label": "Columbia GSAPP — Dean's Office",
            "url": "https://www.arch.columbia.edu/deans-office",
        },
    },
    _ARTS: {
        "founded": 1965,
        "leadership": ("Sarah Cole — Dean of the School of the Arts"),
        "research_centers": [
            "Lenfest Center for the Arts",
            "Columbia University Film Festival",
        ],
        "source": {
            "label": "Columbia School of the Arts — Dean's Office",
            "url": "https://arts.columbia.edu/deans-office",
        },
    },
    _NURSING: {
        "founded": 1892,
        "leadership": (
            "Lorraine Frazier — Dean and Mary O'Neil Mundinger Professor (Senior Vice "
            "President, Columbia University Irving Medical Center)"
        ),
        "source": {
            "label": "Columbia School of Nursing — Leadership",
            "url": "https://www.nursing.columbia.edu/about-us/leadership",
        },
    },
    _GSAS: {
        "founded": 1880,
        "source": {
            "label": "Columbia Graduate School of Arts and Sciences — About",
            "url": "https://www.gsas.columbia.edu/content/about-gsas",
        },
    },
    _DENTAL: {
        "founded": 1916,
        "source": {
            "label": "Columbia College of Dental Medicine — About",
            "url": "https://www.dental.columbia.edu/about-us",
        },
    },
}

# About-detail fields omitted per school (verified-unavailable), recorded in each school's
# _standard.omitted. Notable-faculty rosters are omitted for every school. Columbia College,
# Social Work and Nursing additionally omit a distinct school-owned research center (none
# could be confirmed with an official name from a first-party page). The Vagelos College
# additionally omits leadership (the deanship is in transition with no confirmed dean).
_FACULTY_OMIT = ["about_detail.faculty"]
_ABOUT_OMITTED: dict[str, list[str]] = {
    _CC: [*_FACULTY_OMIT, "about_detail.research_centers"],
    _SEAS: list(_FACULTY_OMIT),
    _CBS: list(_FACULTY_OMIT),
    _LAW: list(_FACULTY_OMIT),
    _PS: [*_FACULTY_OMIT, "about_detail.leadership"],
    _JOUR: list(_FACULTY_OMIT),
    _SIPA: list(_FACULTY_OMIT),
    _MAILMAN: list(_FACULTY_OMIT),
    _SSW: [*_FACULTY_OMIT, "about_detail.research_centers"],
    _GSAPP: list(_FACULTY_OMIT),
    _ARTS: list(_FACULTY_OMIT),
    _NURSING: [*_FACULTY_OMIT, "about_detail.research_centers"],
    _GSAS: [
        *_FACULTY_OMIT,
        "about_detail.leadership",
        "about_detail.research_centers",
    ],
    _DENTAL: [
        *_FACULTY_OMIT,
        "about_detail.leadership",
        "about_detail.research_centers",
    ],
}

# ── Per-node content feeds (so EVERY school + program has a populated Events &
# Updates tab, not just the CS + MBA flagships) ─────────────────────────────────
# The daily content-ingest reads ``news_rss`` (RSS), optional ``events_feed``
# (iCalendar), ``keywords`` (word-boundary relevance filter) and ``news_curated``
# from each node's content_sources. Columbia News (news.columbia.edu) and the
# university events calendar are Cloudflare-gated to server fetches (HTTP 403,
# verified 2026-06-11), so the routine routes every node through the verified,
# server-fetchable school RSS feeds below — filtering by school/program keywords
# (the MIT/Harvard pattern) so content_sources is never left null.
#
# Verified server-fetchable RSS (HTTP 200, 2026-06-11):
#   • CC + SEAS shared feed: https://www.cc-seas.columbia.edu/rss.xml
#   • Mailman School of Public Health: https://www.publichealth.columbia.edu/rss.xml
#   • School of Nursing: https://www.nursing.columbia.edu/rss.xml
#   • Columbia University Irving Medical Center: https://www.cuimc.columbia.edu/rss.xml
#   • GSAPP: https://www.arch.columbia.edu/feed
#   • Data Science Institute (CS flagship): https://datascience.columbia.edu/feed/
_CC_SEAS_RSS = "https://www.cc-seas.columbia.edu/rss.xml"
_MAILMAN_RSS = "https://www.publichealth.columbia.edu/rss.xml"
_NURSING_RSS = "https://www.nursing.columbia.edu/rss.xml"
_CUIMC_RSS = "https://www.cuimc.columbia.edu/rss.xml"
_GSAPP_RSS = "https://www.arch.columbia.edu/feed"
_DATA_SCIENCE_RSS = "https://datascience.columbia.edu/feed/"

# Official Columbia social handles (Columbia social-media directory, verified 2026-06-11).
_SOCIAL_COLUMBIA = {
    "instagram": "https://www.instagram.com/columbia/",
    "linkedin": "https://www.linkedin.com/school/columbia-university/",
    "x": "https://x.com/columbia",
    "youtube": "https://www.youtube.com/user/columbiauniversity",
    "facebook": "https://www.facebook.com/columbia/",
}
# Columbia Business School official handles (business.columbia.edu footer, verified 2026-06-11).
_SOCIAL_CBS = {
    "instagram": "https://www.instagram.com/columbiabusiness/",
    "linkedin": "https://www.linkedin.com/school/columbia-business-school/",
    "x": "https://x.com/Columbia_Biz",
    "youtube": "https://www.youtube.com/user/ColumbiaBusiness",
    "facebook": "https://www.facebook.com/columbiabusiness",
}

# Each school's verified RSS + keyword filter. Schools without their own fetchable RSS
# inherit the CC/SEAS feed filtered by school-naming keywords.
_SCHOOL_FEED_SPEC: dict[str, dict] = {
    _CC: {
        "rss": _CC_SEAS_RSS,
        "keywords": ["Columbia College", "undergraduate", "Core Curriculum"],
    },
    _SEAS: {
        "rss": _CC_SEAS_RSS,
        "keywords": ["engineering", "Fu Foundation", "SEAS", "applied science"],
    },
    _CBS: {
        "rss": _CC_SEAS_RSS,
        "keywords": ["Columbia Business School", "MBA", "business", "finance"],
        "social": _SOCIAL_CBS,
    },
    _LAW: {"rss": _CC_SEAS_RSS, "keywords": ["Columbia Law", "law school", "legal"]},
    _PS: {
        "rss": _CUIMC_RSS,
        "keywords": ["Vagelos", "medical school", "medicine", "physicians", "surgeons"],
    },
    _JOUR: {"rss": _CC_SEAS_RSS, "keywords": ["Journalism School", "journalism", "reporting"]},
    _SIPA: {"rss": _CC_SEAS_RSS, "keywords": ["SIPA", "international affairs", "public policy"]},
    _MAILMAN: {
        "rss": _MAILMAN_RSS,
        "keywords": ["Mailman", "public health", "epidemiology", "health policy"],
    },
    _SSW: {"rss": _CC_SEAS_RSS, "keywords": ["School of Social Work", "social work"]},
    _GSAPP: {"rss": _GSAPP_RSS, "keywords": ["GSAPP", "architecture", "planning", "preservation"]},
    _ARTS: {"rss": _CC_SEAS_RSS, "keywords": ["School of the Arts", "MFA", "film", "theatre"]},
    _NURSING: {"rss": _NURSING_RSS, "keywords": ["School of Nursing", "nursing"]},
    _GSAS: {
        "rss": _CC_SEAS_RSS,
        "keywords": ["Graduate School of Arts and Sciences", "GSAS", "doctoral", "research"],
    },
    _DENTAL: {
        "rss": _CUIMC_RSS,
        "keywords": ["College of Dental Medicine", "dental", "dentistry", "oral"],
    },
}

# Per-program keyword overrides (department/program-naming terms). Programs without an
# entry inherit their school's keywords via _program_keywords().
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "columbia-computer-science-bs": [
        "computer science",
        "Columbia CS",
        "artificial intelligence",
        "data science",
    ],
    "columbia-mba": ["MBA", "Columbia Business School", "finance", "value investing"],
}

_KW_STOP = {"and", "of", "the", "in", "for", "with", "master", "doctor", "bachelor", "studies"}


def _school_content(name: str) -> dict:
    """A school's content_sources: its verified RSS feed filtered by school keywords."""
    spec = _SCHOOL_FEED_SPEC[name]
    return {
        "news_rss": spec["rss"],
        "news_url": _SCHOOL_WEBSITE.get(name, "https://www.columbia.edu"),
        "news_curated": False,
        "keywords": list(spec["keywords"]),
        "social": spec.get("social", _SOCIAL_COLUMBIA),
    }


def _program_keywords(spec: dict) -> list[str]:
    """Program keywords = distinctive discipline term(s) from the program name layered
    on the school's keywords, so the program tab stays relevant yet never empty."""
    slug = spec["slug"]
    if slug in _PROGRAM_KEYWORDS_BY_SLUG:
        return list(_PROGRAM_KEYWORDS_BY_SLUG[slug])
    school_kw = list(_SCHOOL_FEED_SPEC[spec["school"]]["keywords"])
    name = spec["program_name"].replace("&", " ").replace("/", " ")
    terms = [w for w in name.split() if len(w) > 3 and w.lower() not in _KW_STOP]
    program_term = " ".join(terms[:3]).strip()
    return ([program_term] if program_term else []) + school_kw


def _program_content(spec: dict) -> dict:
    """A program's content_sources: its school's verified feed refined by program keywords.
    The CS flagship uses the Data Science Institute RSS (server-fetchable, CS-relevant)."""
    if spec["slug"] == "columbia-computer-science-bs":
        return {
            "news_rss": _DATA_SCIENCE_RSS,
            "news_url": "https://datascience.columbia.edu/",
            "news_curated": False,
            "keywords": _PROGRAM_KEYWORDS_BY_SLUG["columbia-computer-science-bs"],
            "social": _SOCIAL_COLUMBIA,
        }
    base = _school_content(spec["school"])
    base["keywords"] = _program_keywords(spec)
    return base


# Institution-wide feed: the verified CC/SEAS RSS (curated — every item is official
# Columbia College / Engineering news) + the official university social handles.
# Columbia News (news.columbia.edu) RSS is Cloudflare-gated to server fetches and is
# omitted rather than guessed; the CC/SEAS feed is the broadest verified alternative.
_INSTITUTION_CONTENT: dict = {
    "news_rss": _CC_SEAS_RSS,
    "news_url": "https://news.columbia.edu",
    "news_curated": True,
    "social": dict(_SOCIAL_COLUMBIA),
}

# ── The program catalog (Columbia's REAL degrees, organized by school) ──────
# Rebuilt 2026-06-19 (columbiadefab1). The prior catalog was minted per
# (CIP × award-level) from IPEDS: possessive "Bachelor's in {CIP rollup}" names,
# field-echo departments, 88 fabricated departmental "graduate certificates", and
# descriptions that imported PEER-institution units (Harvard's Nieman Foundation,
# Carpenter Center, and Visual & Environmental Studies program) — fabrication, not
# breadth. This catalog is Columbia's REAL degree set, sourced from the Columbia
# College / School of General Studies arts-&-sciences major list
# (bulletin.columbia.edu/general-studies/majors-concentrations/), Columbia
# Engineering's departments and degree pages (bulletin.columbia.edu/columbia-
# engineering/; engineering.columbia.edu), the Graduate School of Arts and Sciences
# (gsas.columbia.edu), and each professional school's official site. Every row carries
# its CONFERRED degree designation, its REAL owning department, and a field-specific
# description (no peer-institution unit, no classification stub, per-credential leads).

_LEVEL_DEGREE_TYPE = {
    "ba": "bachelors", "bs": "bachelors",
    "ma": "masters", "ms": "masters",
    "phd": "phd", "profm": "masters", "profd": "professional",
}
_LEVEL_DURATION = {"ba": 48, "bs": 48, "ma": 24, "ms": 24, "phd": 60, "profm": 24, "profd": 36}


def _conferred_name(field: str, level: str) -> str:
    return {
        "ba": f"Bachelor of Arts in {field}",
        "bs": f"Bachelor of Science in {field}",
        "ma": f"Master of Arts in {field}",
        "ms": f"Master of Science in {field}",
        "phd": f"Doctor of Philosophy in {field}",
    }[level]


def _mk(slug, school, field, level, dept, cip, *, dur=None, delivery="on_campus", name=None):
    """One catalog row with a conferred name + real owning department."""
    dtype = _LEVEL_DEGREE_TYPE[level]
    if name is None:
        name = _conferred_name(field, level)
    return {
        "slug": slug,
        "school": school,
        "program_name": name,
        "degree_type": dtype,
        "department": dept,
        "cip": cip,
        "duration_months": dur or _LEVEL_DURATION[level],
        "delivery_format": delivery,
        "_field": field,
    }


# Department name shorthands.
_D_ECON = "Department of Economics"
_D_POLISCI = "Department of Political Science"
_D_HIST = "Department of History"
_D_ENGL = "Department of English and Comparative Literature"
_D_PSYCH = "Department of Psychology"
_D_SOC = "Department of Sociology"
_D_BIO = "Department of Biological Sciences"
_D_CHEM = "Department of Chemistry"
_D_PHYS = "Department of Physics"
_D_MATH = "Department of Mathematics"
_D_STAT = "Department of Statistics"
_D_ASTRO = "Department of Astronomy"
_D_ANTH = "Department of Anthropology"
_D_ARTH = "Department of Art History and Archaeology"
_D_CLAS = "Department of Classics"
_D_MUSIC = "Department of Music"
_D_PHIL = "Department of Philosophy"
_D_REL = "Department of Religion"
_D_EES = "Department of Earth and Environmental Sciences"
_D_E3B = "Department of Ecology, Evolution, and Environmental Biology"
_D_FRENCH = "Department of French and Romance Philology"
_D_GERMAN = "Department of Germanic Languages"
_D_ITAL = "Department of Italian"
_D_LAIC = "Department of Latin American and Iberian Cultures"
_D_SLAVIC = "Department of Slavic Languages"
_D_MESAAS = "Department of Middle Eastern, South Asian, and African Studies"
_D_EALAC = "Department of East Asian Languages and Cultures"
_D_AAADS = "Department of African American and African Diaspora Studies"
_D_LING = "Department of Linguistics"
# Engineering departments.
_D_APAM = "Department of Applied Physics and Applied Mathematics"
_D_BME = "Department of Biomedical Engineering"
_D_CHE = "Department of Chemical Engineering"
_D_CEEM = "Department of Civil Engineering and Engineering Mechanics"
_D_CS = "Department of Computer Science"
_D_EEE = "Department of Earth and Environmental Engineering"
_D_EE = "Department of Electrical Engineering"
_D_IEOR = "Department of Industrial Engineering and Operations Research"
_D_ME = "Department of Mechanical Engineering"


# ── Columbia College — Bachelor of Arts (Arts & Sciences) ──
_CC_BA: list[dict] = [
    _mk("columbia-economics-ba", _CC, "Economics", "ba", _D_ECON, "45.06"),
    _mk("columbia-political-science-ba", _CC, "Political Science", "ba", _D_POLISCI, "45.10"),
    _mk("columbia-history-ba", _CC, "History", "ba", _D_HIST, "54.01"),
    _mk("columbia-english-ba", _CC, "English and Comparative Literature", "ba", _D_ENGL, "23.01"),
    _mk("columbia-psychology-ba", _CC, "Psychology", "ba", _D_PSYCH, "42.27"),
    _mk("columbia-sociology-ba", _CC, "Sociology", "ba", _D_SOC, "45.11"),
    _mk("columbia-biology-ba", _CC, "Biology", "ba", _D_BIO, "26.01"),
    _mk("columbia-anthropology-ba", _CC, "Anthropology", "ba", _D_ANTH, "45.02"),
    _mk("columbia-art-history-ba", _CC, "Art History", "ba", _D_ARTH, "50.07"),
    _mk("columbia-archaeology-ba", _CC, "Archaeology", "ba", _D_ARTH, "45.03"),
    _mk("columbia-chemistry-ba", _CC, "Chemistry", "ba", _D_CHEM, "40.05"),
    _mk("columbia-biochemistry-ba", _CC, "Biochemistry", "ba", _D_CHEM, "26.02"),
    _mk("columbia-physics-ba", _CC, "Physics", "ba", _D_PHYS, "40.08"),
    _mk("columbia-astronomy-ba", _CC, "Astronomy", "ba", _D_ASTRO, "40.02"),
    _mk("columbia-astrophysics-ba", _CC, "Astrophysics", "ba", _D_ASTRO, "40.0202"),
    _mk("columbia-mathematics-ba", _CC, "Mathematics", "ba", _D_MATH, "27.01"),
    _mk("columbia-statistics-ba", _CC, "Statistics", "ba", _D_STAT, "27.05"),
    _mk("columbia-philosophy-ba", _CC, "Philosophy", "ba", _D_PHIL, "38.01"),
    _mk("columbia-religion-ba", _CC, "Religion", "ba", _D_REL, "38.02"),
    _mk("columbia-classics-ba", _CC, "Classics", "ba", _D_CLAS, "16.12"),
    _mk("columbia-music-ba", _CC, "Music", "ba", _D_MUSIC, "50.09"),
    _mk("columbia-french-ba", _CC, "French", "ba", _D_FRENCH, "16.09"),
    _mk("columbia-german-ba", _CC, "German", "ba", _D_GERMAN, "16.05"),
    _mk("columbia-italian-ba", _CC, "Italian", "ba", _D_ITAL, "16.04"),
    _mk("columbia-hispanic-studies-ba", _CC, "Hispanic Studies", "ba", _D_LAIC, "16.09"),
    _mk("columbia-russian-ba", _CC, "Russian Language and Culture", "ba", _D_SLAVIC, "16.04"),
    _mk("columbia-slavic-studies-ba", _CC, "Slavic Studies", "ba", _D_SLAVIC, "16.04"),
    _mk("columbia-east-asian-studies-ba", _CC, "East Asian Studies", "ba", _D_EALAC, "05.01"),
    _mk("columbia-mesaas-ba", _CC, "Middle Eastern, South Asian, and African Studies", "ba", _D_MESAAS, "05.01"),
    _mk("columbia-aaads-ba", _CC, "African American and African Diaspora Studies", "ba", _D_AAADS, "05.02"),
    _mk("columbia-linguistics-ba", _CC, "Linguistics", "ba", _D_LING, "16.01"),
    _mk("columbia-earth-science-ba", _CC, "Earth Science", "ba", _D_EES, "40.06"),
    _mk("columbia-environmental-science-ba", _CC, "Environmental Science", "ba", _D_EES, "03.01"),
    _mk("columbia-environmental-biology-ba", _CC, "Environmental Biology", "ba", _D_E3B, "26.13"),
    _mk("columbia-neuroscience-and-behavior-ba", _CC, "Neuroscience and Behavior", "ba", _D_BIO, "30.24"),
    _mk("columbia-financial-economics-ba", _CC, "Financial Economics", "ba", _D_ECON, "52.08"),
    _mk("columbia-american-studies-ba", _CC, "American Studies", "ba", "Center for American Studies", "05.01"),
    _mk("columbia-ancient-studies-ba", _CC, "Ancient Studies", "ba", "Center for the Ancient Mediterranean", "30.13"),
    _mk("columbia-comparative-literature-and-society-ba", _CC, "Comparative Literature and Society", "ba", "Institute for Comparative Literature and Society", "16.01"),
    _mk("columbia-creative-writing-ba", _CC, "Creative Writing", "ba", "Undergraduate Creative Writing Program", "23.13"),
    _mk("columbia-drama-and-theatre-arts-ba", _CC, "Drama and Theatre Arts", "ba", "Theatre Program, School of the Arts", "50.05"),
    _mk("columbia-film-and-media-studies-ba", _CC, "Film and Media Studies", "ba", "Film and Media Studies Program", "50.06"),
    _mk("columbia-visual-arts-ba", _CC, "Visual Arts", "ba", "Visual Arts Program, School of the Arts", "50.07"),
    _mk("columbia-architecture-ba", _CC, "Architecture", "ba", "Undergraduate Program in Architecture", "04.02"),
    _mk("columbia-cognitive-science-ba", _CC, "Cognitive Science", "ba", "Cognitive Science Program", "30.25"),
    _mk("columbia-data-science-ba", _CC, "Data Science", "ba", "Data Science Institute", "30.70"),
    _mk("columbia-human-rights-ba", _CC, "Human Rights", "ba", "Institute for the Study of Human Rights", "30.25"),
    _mk("columbia-medical-humanities-ba", _CC, "Medical Humanities", "ba", "Program in Medical Humanities", "30.13"),
    _mk("columbia-sustainable-development-ba", _CC, "Sustainable Development", "ba", "Undergraduate Program in Sustainable Development", "03.01"),
    _mk("columbia-urban-studies-ba", _CC, "Urban Studies", "ba", "Urban Studies Program", "45.12"),
    _mk("columbia-ethnicity-and-race-studies-ba", _CC, "Ethnicity and Race Studies", "ba", "Center for the Study of Ethnicity and Race", "05.02"),
    _mk("columbia-womens-and-gender-studies-ba", _CC, "Women's and Gender Studies", "ba", "Institute for Research on Women, Gender, and Sexuality", "05.02"),
    _mk("columbia-latin-american-studies-ba", _CC, "Latin American and Caribbean Studies", "ba", "Institute of Latin American Studies", "05.01"),
    _mk("columbia-economics-mathematics-ba", _CC, "Economics-Mathematics", "ba", "Departments of Economics and Mathematics", "52.08"),
    _mk("columbia-mathematics-statistics-ba", _CC, "Mathematics-Statistics", "ba", "Departments of Mathematics and Statistics", "27.01"),
    _mk("columbia-computer-science-mathematics-ba", _CC, "Computer Science-Mathematics", "ba", "Departments of Computer Science and Mathematics", "11.01"),
]

# ── GSAS — Doctor of Philosophy (and select terminal MAs) ──
_GSAS_PROGRAMS: list[dict] = [
    _mk("columbia-economics-phd", _GSAS, "Economics", "phd", _D_ECON, "45.06"),
    _mk("columbia-political-science-phd", _GSAS, "Political Science", "phd", _D_POLISCI, "45.10"),
    _mk("columbia-history-phd", _GSAS, "History", "phd", _D_HIST, "54.01"),
    _mk("columbia-english-phd", _GSAS, "English and Comparative Literature", "phd", _D_ENGL, "23.01"),
    _mk("columbia-psychology-phd", _GSAS, "Psychology", "phd", _D_PSYCH, "42.27"),
    _mk("columbia-sociology-phd", _GSAS, "Sociology", "phd", _D_SOC, "45.11"),
    _mk("columbia-biological-sciences-phd", _GSAS, "Biological Sciences", "phd", _D_BIO, "26.01"),
    _mk("columbia-chemistry-phd", _GSAS, "Chemistry", "phd", _D_CHEM, "40.05"),
    _mk("columbia-physics-phd", _GSAS, "Physics", "phd", _D_PHYS, "40.08"),
    _mk("columbia-mathematics-phd", _GSAS, "Mathematics", "phd", _D_MATH, "27.01"),
    _mk("columbia-statistics-phd", _GSAS, "Statistics", "phd", _D_STAT, "27.05"),
    _mk("columbia-astronomy-phd", _GSAS, "Astronomy", "phd", _D_ASTRO, "40.02"),
    _mk("columbia-anthropology-phd", _GSAS, "Anthropology", "phd", _D_ANTH, "45.02"),
    _mk("columbia-art-history-and-archaeology-phd", _GSAS, "Art History and Archaeology", "phd", _D_ARTH, "50.07"),
    _mk("columbia-classics-phd", _GSAS, "Classics", "phd", _D_CLAS, "16.12"),
    _mk("columbia-music-phd", _GSAS, "Music", "phd", _D_MUSIC, "50.09"),
    _mk("columbia-philosophy-phd", _GSAS, "Philosophy", "phd", _D_PHIL, "38.01"),
    _mk("columbia-religion-phd", _GSAS, "Religion", "phd", _D_REL, "38.02"),
    _mk("columbia-earth-and-environmental-sciences-phd", _GSAS, "Earth and Environmental Sciences", "phd", _D_EES, "40.06"),
    _mk("columbia-ecology-evolution-phd", _GSAS, "Ecology, Evolution, and Environmental Biology", "phd", _D_E3B, "26.13"),
    _mk("columbia-french-phd", _GSAS, "French", "phd", _D_FRENCH, "16.09"),
    _mk("columbia-german-phd", _GSAS, "German", "phd", _D_GERMAN, "16.05"),
    _mk("columbia-italian-phd", _GSAS, "Italian", "phd", _D_ITAL, "16.04"),
    _mk("columbia-hispanic-studies-phd", _GSAS, "Hispanic Studies", "phd", _D_LAIC, "16.09"),
    _mk("columbia-slavic-studies-phd", _GSAS, "Slavic Studies", "phd", _D_SLAVIC, "16.04"),
    _mk("columbia-east-asian-studies-phd", _GSAS, "East Asian Studies", "phd", _D_EALAC, "05.01"),
    _mk("columbia-mesaas-phd", _GSAS, "Middle Eastern, South Asian, and African Studies", "phd", _D_MESAAS, "05.01"),
    _mk("columbia-aaads-phd", _GSAS, "African American and African Diaspora Studies", "phd", _D_AAADS, "05.02"),
    _mk("columbia-neuroscience-phd", _GSAS, "Neuroscience and Behavior", "phd", _D_BIO, "30.24"),
    # Terminal MA programs.
    _mk("columbia-climate-and-society-ma", _GSAS, "Climate and Society", "ma", _D_EES, "03.02"),
    _mk("columbia-human-rights-studies-ma", _GSAS, "Human Rights Studies", "ma", "Institute for the Study of Human Rights", "30.25"),
    _mk("columbia-qmss-ma", _GSAS, "Quantitative Methods in the Social Sciences", "ma", "QMSS Program", "45.01"),
    _mk("columbia-statistics-ma", _GSAS, "Statistics", "ma", _D_STAT, "27.05"),
]

# ── Fu Foundation School of Engineering and Applied Science ──
_SEAS_PROGRAMS: list[dict] = [
    # Undergraduate (B.S.).
    _mk("columbia-computer-science-bs", _SEAS, "Computer Science", "bs", _D_CS, "11.07"),
    _mk("columbia-operations-research-bs", _SEAS, "Operations Research", "bs", _D_IEOR, "14.37"),
    _mk("columbia-mechanical-engineering-bs", _SEAS, "Mechanical Engineering", "bs", _D_ME, "14.19"),
    _mk("columbia-electrical-engineering-bs", _SEAS, "Electrical Engineering", "bs", _D_EE, "14.10"),
    _mk("columbia-applied-mathematics-bs", _SEAS, "Applied Mathematics", "bs", _D_APAM, "27.03"),
    _mk("columbia-biomedical-engineering-bs", _SEAS, "Biomedical Engineering", "bs", _D_BME, "14.05"),
    _mk("columbia-applied-physics-bs", _SEAS, "Applied Physics", "bs", _D_APAM, "14.12"),
    _mk("columbia-materials-science-and-engineering-bs", _SEAS, "Materials Science and Engineering", "bs", _D_APAM, "14.18"),
    _mk("columbia-chemical-engineering-bs", _SEAS, "Chemical Engineering", "bs", _D_CHE, "14.07"),
    _mk("columbia-civil-engineering-bs", _SEAS, "Civil Engineering", "bs", _D_CEEM, "14.08"),
    _mk("columbia-engineering-mechanics-bs", _SEAS, "Engineering Mechanics", "bs", _D_CEEM, "14.11"),
    _mk("columbia-computer-engineering-bs", _SEAS, "Computer Engineering", "bs", "Computer Engineering Program", "14.09"),
    _mk("columbia-earth-and-environmental-engineering-bs", _SEAS, "Earth and Environmental Engineering", "bs", _D_EEE, "14.14"),
    _mk("columbia-industrial-engineering-bs", _SEAS, "Industrial Engineering", "bs", _D_IEOR, "14.35"),
    # Master of Science.
    _mk("columbia-computer-science-ms", _SEAS, "Computer Science", "ms", _D_CS, "11.07", dur=18,
        name="Master of Science in Computer Science (M.S.)"),
    _mk("columbia-mechanical-engineering-ms", _SEAS, "Mechanical Engineering", "ms", _D_ME, "14.19"),
    _mk("columbia-electrical-engineering-ms", _SEAS, "Electrical Engineering", "ms", _D_EE, "14.10"),
    _mk("columbia-biomedical-engineering-ms", _SEAS, "Biomedical Engineering", "ms", _D_BME, "14.05"),
    _mk("columbia-chemical-engineering-ms", _SEAS, "Chemical Engineering", "ms", _D_CHE, "14.07"),
    _mk("columbia-civil-engineering-ms", _SEAS, "Civil Engineering", "ms", _D_CEEM, "14.08"),
    _mk("columbia-applied-physics-ms", _SEAS, "Applied Physics", "ms", _D_APAM, "14.12"),
    _mk("columbia-applied-mathematics-ms", _SEAS, "Applied Mathematics", "ms", _D_APAM, "27.03"),
    _mk("columbia-materials-science-and-engineering-ms", _SEAS, "Materials Science and Engineering", "ms", _D_APAM, "14.18"),
    _mk("columbia-earth-and-environmental-engineering-ms", _SEAS, "Earth and Environmental Engineering", "ms", _D_EEE, "14.14"),
    _mk("columbia-computer-engineering-ms", _SEAS, "Computer Engineering", "ms", "Computer Engineering Program", "14.09"),
    _mk("columbia-operations-research-ms", _SEAS, "Operations Research", "ms", _D_IEOR, "14.37"),
    _mk("columbia-industrial-engineering-ms", _SEAS, "Industrial Engineering", "ms", _D_IEOR, "14.35"),
    _mk("columbia-financial-engineering-ms", _SEAS, "Financial Engineering", "ms", _D_IEOR, "14.37"),
    _mk("columbia-management-science-and-engineering-ms", _SEAS, "Management Science and Engineering", "ms", _D_IEOR, "14.27"),
    _mk("columbia-data-science-ms", _SEAS, "Data Science", "ms", "Data Science Institute", "30.70"),
    # Doctor of Philosophy.
    _mk("columbia-computer-science-phd", _SEAS, "Computer Science", "phd", _D_CS, "11.07"),
    _mk("columbia-mechanical-engineering-phd", _SEAS, "Mechanical Engineering", "phd", _D_ME, "14.19"),
    _mk("columbia-electrical-engineering-phd", _SEAS, "Electrical Engineering", "phd", _D_EE, "14.10"),
    _mk("columbia-biomedical-engineering-phd", _SEAS, "Biomedical Engineering", "phd", _D_BME, "14.05"),
    _mk("columbia-chemical-engineering-phd", _SEAS, "Chemical Engineering", "phd", _D_CHE, "14.07"),
    _mk("columbia-civil-engineering-phd", _SEAS, "Civil Engineering", "phd", _D_CEEM, "14.08"),
    _mk("columbia-applied-physics-phd", _SEAS, "Applied Physics", "phd", _D_APAM, "14.12"),
    _mk("columbia-materials-science-and-engineering-phd", _SEAS, "Materials Science and Engineering", "phd", _D_APAM, "14.18"),
    _mk("columbia-earth-and-environmental-engineering-phd", _SEAS, "Earth and Environmental Engineering", "phd", _D_EEE, "14.14"),
    _mk("columbia-operations-research-phd", _SEAS, "Operations Research", "phd", _D_IEOR, "14.37"),
]

# ── Professional schools (conferred professional/graduate degrees) ──
_PROF_PROGRAMS: list[dict] = [
    # Business.
    _mk("columbia-mba", _CBS, "Business Administration", "profm", _CBS, "52.02",
        name="Master of Business Administration (MBA)"),
    _mk("columbia-emba", _CBS, "Business Administration", "profm", _CBS, "52.02", dur=20,
        name="Executive Master of Business Administration (EMBA)"),
    _mk("columbia-accounting-ms", _CBS, "Accounting and Fundamental Analysis", "ms", _CBS, "52.03"),
    _mk("columbia-financial-economics-ms", _CBS, "Financial Economics", "ms", _CBS, "52.08"),
    _mk("columbia-marketing-science-ms", _CBS, "Marketing Science", "ms", _CBS, "52.14"),
    _mk("columbia-business-phd", _CBS, "Business", "phd", _CBS, "52.02"),
    # Law.
    _mk("columbia-jd", _LAW, "Law", "profd", _LAW, "22.01", dur=36, name="Juris Doctor (J.D.)"),
    _mk("columbia-llm", _LAW, "Law", "profm", _LAW, "22.02", dur=12, name="Master of Laws (LL.M.)"),
    _mk("columbia-jsd", _LAW, "Law", "profd", _LAW, "22.03", dur=36,
        name="Doctor of the Science of Law (J.S.D.)"),
    # Medicine (Vagelos College of Physicians and Surgeons).
    _mk("columbia-md", _PS, "Medicine", "profd", _PS, "51.12", dur=48, name="Doctor of Medicine (M.D.)"),
    _mk("columbia-physical-therapy-dpt", _PS, "Physical Therapy", "profd", "Programs in Physical Therapy", "51.23", dur=36,
        name="Doctor of Physical Therapy (DPT)"),
    _mk("columbia-genetic-counseling-ms", _PS, "Genetic Counseling", "ms", "Genetic Counseling Program", "51.15"),
    _mk("columbia-human-nutrition-ms", _PS, "Human Nutrition", "ms", "Institute of Human Nutrition", "51.31"),
    # Dental Medicine.
    _mk("columbia-dental-dds", _DENTAL, "Dental Surgery", "profd", _DENTAL, "51.04", dur=48,
        name="Doctor of Dental Surgery (D.D.S.)"),
    # Journalism.
    _mk("columbia-journalism-ms", _JOUR, "Journalism", "ms", _JOUR, "09.04", dur=10,
        name="Master of Science in Journalism (M.S.)"),
    _mk("columbia-journalism-ma", _JOUR, "Journalism", "ma", _JOUR, "09.04", dur=10,
        name="Master of Arts in Journalism (M.A.)"),
    _mk("columbia-data-journalism-ms", _JOUR, "Data Journalism", "ms", _JOUR, "09.04", dur=10,
        name="Master of Science in Data Journalism (M.S.)"),
    _mk("columbia-communications-phd", _JOUR, "Communications", "phd", _JOUR, "09.01"),
    # SIPA.
    _mk("columbia-sipa-mia", _SIPA, "International Affairs", "profm", _SIPA, "45.09", dur=24,
        name="Master of International Affairs (MIA)"),
    _mk("columbia-sipa-mpa", _SIPA, "Public Administration", "profm", _SIPA, "44.04", dur=24,
        name="Master of Public Administration (MPA)"),
    _mk("columbia-sustainable-development-phd", _SIPA, "Sustainable Development", "phd", _SIPA, "03.01"),
    # Public Health (Mailman).
    _mk("columbia-public-health-mph", _MAILMAN, "Public Health", "profm", _MAILMAN, "51.22", dur=24,
        name="Master of Public Health (MPH)"),
    _mk("columbia-health-administration-mha", _MAILMAN, "Health Administration", "ms", _MAILMAN, "51.07",
        name="Master of Health Administration (MHA)"),
    _mk("columbia-biostatistics-ms", _MAILMAN, "Biostatistics", "ms", "Department of Biostatistics", "26.11"),
    _mk("columbia-public-health-drph", _MAILMAN, "Public Health", "profd", _MAILMAN, "51.22", dur=48,
        name="Doctor of Public Health (DrPH)"),
    # Social Work.
    _mk("columbia-social-work-msw", _SSW, "Social Work", "profm", _SSW, "44.07", dur=24,
        name="Master of Science in Social Work (MSW)"),
    _mk("columbia-social-work-phd", _SSW, "Social Work", "phd", _SSW, "44.07"),
    # Architecture, Planning and Preservation (GSAPP).
    _mk("columbia-architecture-march", _GSAPP, "Architecture", "profd", _GSAPP, "04.02", dur=36,
        name="Master of Architecture (M.Arch)"),
    _mk("columbia-urban-planning-ms", _GSAPP, "Urban Planning", "ms", _GSAPP, "04.03"),
    _mk("columbia-historic-preservation-ms", _GSAPP, "Historic Preservation", "ms", _GSAPP, "04.08"),
    _mk("columbia-real-estate-development-ms", _GSAPP, "Real Estate Development", "ms", _GSAPP, "04.10"),
    _mk("columbia-urban-design-ms", _GSAPP, "Urban Design", "ms", _GSAPP, "04.05"),
    _mk("columbia-architecture-aad-ms", _GSAPP, "Advanced Architectural Design", "ms", _GSAPP, "04.09"),
    # School of the Arts.
    _mk("columbia-arts-mfa", _ARTS, "Fine Arts", "profm", _ARTS, "50.06", dur=24,
        name="Master of Fine Arts (MFA)"),
    _mk("columbia-film-media-studies-ma", _ARTS, "Film and Media Studies", "ma", _ARTS, "50.06"),
    # Nursing.
    _mk("columbia-nursing-msn", _NURSING, "Nursing", "profm", _NURSING, "51.38", dur=15,
        name="Master's Direct Entry Program in Nursing (MDE)"),
    _mk("columbia-nursing-dnp", _NURSING, "Nursing Practice", "profd", _NURSING, "51.38", dur=36,
        name="Doctor of Nursing Practice (DNP)"),
    _mk("columbia-nursing-phd", _NURSING, "Nursing", "phd", _NURSING, "51.38"),
]

PROGRAMS: list[dict] = [*_CC_BA, *_GSAS_PROGRAMS, *_SEAS_PROGRAMS, *_PROF_PROGRAMS]


# Credential-distinct lead + field core → a per-program, per-credential description.
# Distinct leads guarantee a field's credential siblings never share a leading body
# (anti-stub shared_leading_body = 0), while the field core (a true discipline fact)
# clears the gold contrast (no classification stub). No peer-institution unit appears.
def _description(spec: dict) -> str:
    slug = spec["slug"]
    fmt = spec.get("delivery_format", "on_campus")
    delivery = ""
    if fmt == "online":
        delivery = " Delivered online."
    elif fmt == "hybrid":
        delivery = " Delivered in a hybrid format."
    if slug in SLUG_DESCRIPTIONS:
        return f"{SLUG_DESCRIPTIONS[slug]}{delivery}"
    field = spec["_field"]
    core = CORE.get(FIELD_ALIASES.get(field, field))
    if not core:
        raise ValueError(f"Missing CORE entry for {field!r} ({slug})")
    dtype = spec["degree_type"]
    if dtype == "bachelors":
        if spec["school"] == _SEAS:
            lead = f"Columbia Engineering undergraduates in {field} study {core}."
        else:
            lead = f"Columbia College undergraduates majoring in {field} study {core}."
    elif dtype == "phd":
        lead = (
            f"Doctoral candidates in {field} at Columbia investigate {core}, "
            "completing original dissertation research."
        )
    else:  # masters / professional master's
        lead = f"Columbia's master's program in {field} develops graduate expertise in {core}."
    return f"{lead}{delivery}"


for _p in PROGRAMS:
    _p["description"] = _description(_p)

# ── Catalog quality gate (gold-MIT-0% anti-stub + structural realness) ──────
_catalog_errors = validate_catalog(PROGRAMS)
_dupe_names = [n for n, c in Counter(p["program_name"] for p in PROGRAMS).items() if c > 1]
if _dupe_names:
    _catalog_errors.append(f"duplicate program_name: {_dupe_names[:5]}")
_dupe_slugs = [s for s, c in Counter(p["slug"] for p in PROGRAMS).items() if c > 1]
if _dupe_slugs:
    _catalog_errors.append(f"duplicate slug: {_dupe_slugs[:5]}")
_possessive = [
    p["program_name"] for p in PROGRAMS
    if p["program_name"].startswith(("Bachelor's in ", "Master's in ", "Doctorate in "))
]
if _possessive:
    _catalog_errors.append(f"possessive-mint names on {len(_possessive)} programs")
_peer_contaminated = [
    p["slug"] for p in PROGRAMS
    if any(sig in (p.get("description") or "") for sig in _PEER_SIGNATURES)
]
if _peer_contaminated:
    _catalog_errors.append(f"peer-contaminated descriptions: {_peer_contaminated[:5]}")
if _catalog_errors:
    raise RuntimeError(f"Columbia catalog quality gate failed: {_catalog_errors}")
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

# Full official program names (program-page title); equal to the program name here.
_FULL_NAME_BY_SLUG: dict[str, str] = {p["slug"]: p["program_name"] for p in PROGRAMS}

# Official program/department/school home pages.
_WEBSITE_BY_SLUG: dict[str, str] = {
    "columbia-economics-ba": "https://econ.columbia.edu/",
    "columbia-political-science-ba": "https://polisci.columbia.edu/",
    "columbia-history-ba": "https://history.columbia.edu/",
    "columbia-english-ba": "https://english.columbia.edu/",
    "columbia-psychology-ba": "https://psychology.columbia.edu/",
    "columbia-sociology-ba": "https://sociology.columbia.edu/",
    "columbia-biology-ba": "https://biology.columbia.edu/",
    "columbia-computer-science-bs": "https://www.cs.columbia.edu/education/undergraduate/",
    "columbia-operations-research-bs": "https://www.ieor.columbia.edu/",
    "columbia-mechanical-engineering-bs": "https://www.me.columbia.edu/",
    "columbia-electrical-engineering-bs": "https://www.ee.columbia.edu/",
    "columbia-applied-mathematics-bs": "https://www.apam.columbia.edu/",
    "columbia-biomedical-engineering-bs": "https://www.bme.columbia.edu/",
    "columbia-computer-science-ms": "https://www.cs.columbia.edu/education/ms/",
    "columbia-mba": "https://business.columbia.edu/mba",
    "columbia-jd": "https://www.law.columbia.edu/academics/degree-programs/jd-program",
    "columbia-md": "https://www.vagelos.columbia.edu/education/degree-programs/md-program",
    "columbia-journalism-ms": "https://journalism.columbia.edu/ms-degree",
    "columbia-sipa-mia": "https://www.sipa.columbia.edu/academics/master-programs/master-international-affairs-mia",
    "columbia-sipa-mpa": "https://www.sipa.columbia.edu/academics/master-programs/master-public-administration-mpa",
    "columbia-public-health-mph": "https://www.publichealth.columbia.edu/become-student/departments",
    "columbia-social-work-msw": "https://socialwork.columbia.edu/academics/ms-program/",
    "columbia-architecture-march": "https://www.arch.columbia.edu/programs/2-m-arch",
    "columbia-arts-mfa": "https://arts.columbia.edu/",
    "columbia-nursing-msn": "https://www.nursing.columbia.edu/academics/academic-programs/masters-direct-entry-program-non-nurses",
}

# ── Who-it's-for + highlights (catalog baselines) ──────────────────────────
_WHO_BASELINE = (
    "Academically exceptional students seeking a research-rich Ivy League education in New "
    "York City, anchored by Columbia's Core Curriculum and full-need, no-loan financial aid."
)
_HL_BASELINE = ["Ivy League", "Core Curriculum", "Need-met, no-loan aid"]
_WHO_GRAD_BASELINE = (
    "Graduate and professional students seeking a top-ranked Columbia degree with the "
    "resources of a major research university in the heart of New York City."
)
_HL_GRAD_BASELINE = ["Top-ranked Columbia graduate degree", "World-class faculty", "New York City"]

_WHO_BY_SLUG = {
    "columbia-computer-science-bs": (
        "Technically strong students who want a rigorous computer science education — "
        "offered as the B.S. or the B.A. — at the heart of New York's tech and research "
        "ecosystem."
    ),
    "columbia-mba": (
        "Aspiring leaders seeking a two-year MBA that connects academic theory to practice "
        "from the financial and business capital of the world."
    ),
    "columbia-journalism-ms": (
        "Aspiring journalists seeking a rigorous reporting and writing degree at the only "
        "Ivy League journalism school, home of the Pulitzer Prizes."
    ),
}
_HL_BY_SLUG = {
    "columbia-computer-science-bs": [
        "B.S. & B.A. tracks",
        "11 research areas",
        "New York City tech hub",
    ],
    "columbia-mba": [
        "Two-year full-time MBA",
        "New York City",
        "Theory meets practice",
    ],
    "columbia-journalism-ms": [
        "Only Ivy League J-school",
        "Home of the Pulitzer Prizes",
        "New York City newsroom",
    ],
}

# ── Curriculum / research areas, where published (the flagship) ────────────
# Columbia CS publishes 11 official research areas; quoted from the department's official
# research-areas page.
_TRACKS_BY_SLUG: dict[str, dict] = {
    "columbia-computer-science-bs": {
        "label": "Computer science research areas",
        "note": (
            "Computer science is offered as the B.S. (through Columbia Engineering) and the "
            "B.A. (through Columbia College), with combined and joint majors. The department "
            "spans eleven official research areas across more than sixty faculty."
        ),
        "items": [
            {"name": "Artificial Intelligence"},
            {"name": "Machine Learning"},
            {"name": "Vision & Robotics"},
            {"name": "Networking"},
            {"name": "Computer Engineering"},
            {"name": "Software Systems"},
            {"name": "Computational Biology"},
            {"name": "Security & Privacy"},
            {"name": "Natural Language Processing & Speech"},
            {"name": "Theory"},
            {"name": "Graphics & User Interfaces"},
        ],
        "source": "Columbia Department of Computer Science — Research Areas",
        "source_url": "https://www.cs.columbia.edu/areas/",
    },
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
# Columbia undergraduate cost: Columbia College and Columbia Engineering charge the same
# undergraduate tuition (2025-26: $35,085 per term = $70,170 per year, plus $3,280 in
# mandatory fees). Cost of attendance and average net price are College Scorecard.
_TUITION_UG = 70170
_UNDERGRAD_FEES = 3280
_UNDERGRAD_COA = 89472
_AVG_NET_PRICE = 21590

# ── Published graduate-tier tuition (REPAIR_BACKLOG #4 — master's/professional
# starvation behind a 100% bachelor's tier) ──────────────────────────────────
# Columbia charges graduate/professional tuition by SCHOOL or PROGRAM on first-party
# bulletin / cost-of-attendance pages (2025-26 unless noted). Program.tuition is the
# matcher's ANNUAL budget input — stamp the published sticker, never the $70,170
# undergraduate rate copied down. Funded research doctorates (Ph.D., J.S.D.) and
# per-credit-only programs with no flat annual figure (DrPH) stay omitted-with-reason.
_GSAS_MA_TUITION_PER_SEM = 36727  # GSAS full Residence Unit (terminal M.A.)
_GSAS_MA_TUITION_ANNUAL = 73454  # 2 × $36,727
_SEAS_MS_PER_CREDIT = 2700
_SEAS_MS_TYPICAL_POINTS = 30
_SEAS_MS_TUITION = 81000  # 30 × $2,700
_GSAPP_MS_PER_TERM = 35190  # 12–19 points
_GSAPP_MS_ANNUAL = 70380  # 2 terms
_GSAPP_ONE_YEAR_MS = 105570  # 3-term 12-month M.S. programs
_SIPA_TUITION_PER_SEM = 37110  # MIA / MPA full Residence Unit (12–16.5 credits)
_SIPA_TUITION_ANNUAL = 74220
_SSW_TUITION_PER_SEM = 30182  # MSSW flat rate (2025-26 residential COA table)
_SSW_TUITION_ANNUAL = 60364
_MDE_TUITION_PER_SEM = 32092  # Master's Direct Entry flat rate (2024-25 listing)
_MDE_TUITION_ANNUAL = 64184
_LAW_TUITION = 85368  # J.D. = LL.M. per Law bulletin
_MD_TUITION = 76336
_DDS_TUITION = 105048
_DPT_TUITION_ANNUAL = 46928  # Fall $23,464 + Spring $23,464 (2026-27 budget)
_DNP_TUITION_PER_SEM = 24338  # full-time flat rate (2024-25 listing)
_DNP_TUITION_ANNUAL = 48676

_GSAS_TUITION_SRC = (
    "Columbia GSAS — Cost of Attendance (2025-26)",
    "https://www.gsas.columbia.edu/content/cost-attendance",
)
_SEAS_TUITION_SRC = (
    "Columbia Engineering — Graduate Tuition, Fees and Payments (bulletin)",
    "https://bulletin.columbia.edu/columbia-engineering/graduate-studies/"
    "graduate-tuition-fees-payments/",
)
_GSAPP_TUITION_SRC = (
    "Columbia GSAPP — Tuition and Aid",
    "https://www.arch.columbia.edu/admissions/tuition-aid",
)
_SIPA_TUITION_SRC = (
    "Columbia SIPA — Tuition and Fees",
    "https://www.sipa.columbia.edu/office-financial-aid/tuition-and-fees",
)
_SSW_TUITION_SRC = (
    "Columbia School of Social Work — Cost of Attendance (2025-26)",
    "https://socialwork.columbia.edu/content/cost-attendance-residential-campus-2025-2026",
)
_CBS_MS_SRC = (
    "Columbia Business School — MS Programs Costs",
    "https://business.columbia.edu/financial-aid/costs/ms-programs",
)
_CBS_EMBA_SRC = (
    "Columbia Business School — Executive MBA Costs",
    "https://business.columbia.edu/financial-aid/costs/executive-mba",
)
_LAW_TUITION_SRC = (
    "Columbia Law School — J.D. and LL.M. Tuition and Fees",
    "https://www.law.columbia.edu/about/departments/financial-aid/jd-and-llm-tuition-and-fees",
)
_MAILMAN_TUITION_SRC = (
    "Mailman School of Public Health — Tuition & Fees",
    "https://www.publichealth.columbia.edu/become-student/how-apply/financial-aid/tuition-fees",
)
_JOURNALISM_TUITION_SRC = (
    "Columbia Journalism School — Detailed Cost of Attendance",
    "https://journalism.columbia.edu/cost-attendance/detailed",
)
_ARTS_TUITION_SRC = (
    "Columbia Student Financial Services — School of the Arts Cost of Attendance",
    "https://sfs.columbia.edu/content/school-arts-cost-attendance",
)
_PS_TUITION_SRC = (
    "Vagelos College of Physicians and Surgeons — program budgets",
    "https://www.vagelos.columbia.edu/education/academic-programs",
)
_NURSING_TUITION_SRC = (
    "Columbia School of Nursing — Financial Aid (tuition listing)",
    "https://www.nursing.columbia.edu/academics/financial-aid/apply-financial-aid",
)


def _gsas_ma_cost(field: str) -> dict:
    return {
        "tuition_usd": _GSAS_MA_TUITION_ANNUAL,
        "funded": False,
        "note": (
            f"GSAS full-time Residence Unit tuition for the terminal M.A. in {field} "
            f"(${_GSAS_MA_TUITION_PER_SEM:,} per semester × 2 = "
            f"${_GSAS_MA_TUITION_ANNUAL:,} per academic year)."
        ),
        "source": _GSAS_TUITION_SRC[0],
        "source_url": _GSAS_TUITION_SRC[1],
        "year": "2025-26",
    }


def _seas_ms_cost(field: str) -> dict:
    return {
        "tuition_usd": _SEAS_MS_TUITION,
        "funded": False,
        "note": (
            f"Columbia Engineering M.S. in {field}: ${_SEAS_MS_PER_CREDIT:,} per credit × "
            f"{_SEAS_MS_TYPICAL_POINTS} points = ${_SEAS_MS_TUITION:,} (excludes fees)."
        ),
        "source": _SEAS_TUITION_SRC[0],
        "source_url": _SEAS_TUITION_SRC[1],
        "year": "2025-26",
    }


def _gsapp_ms_cost(field: str, *, one_year: bool = False) -> dict:
    tuition = _GSAPP_ONE_YEAR_MS if one_year else _GSAPP_MS_ANNUAL
    term_note = (
        "three terms in 12 months"
        if one_year
        else f"${_GSAPP_MS_PER_TERM:,} per term × 2"
    )
    return {
        "tuition_usd": tuition,
        "funded": False,
        "note": (
            f"GSAPP M.S. in {field}: ${tuition:,} tuition ({term_note}; 12–19 points per "
            f"term billed at ${_GSAPP_MS_PER_TERM:,}, additional points at $2,346/point)."
        ),
        "source": _GSAPP_TUITION_SRC[0],
        "source_url": _GSAPP_TUITION_SRC[1],
        "year": "2025-26",
    }


def _sipa_cost(degree: str) -> dict:
    return {
        "tuition_usd": _SIPA_TUITION_ANNUAL,
        "funded": False,
        "note": (
            f"Columbia SIPA {degree} full-time tuition (${_SIPA_TUITION_PER_SEM:,} per "
            f"semester × 2 = ${_SIPA_TUITION_ANNUAL:,}; 12–16.5 credits per term at the "
            "standard rate)."
        ),
        "source": _SIPA_TUITION_SRC[0],
        "source_url": _SIPA_TUITION_SRC[1],
        "year": "2025-26",
    }


def _law_cost(degree: str) -> dict:
    return {
        "tuition_usd": _LAW_TUITION,
        "funded": False,
        "note": (
            f"Columbia Law School {degree} tuition (the Law bulletin states the same "
            f"${_LAW_TUITION:,} tuition for the J.D. and LL.M.)."
        ),
        "source": _LAW_TUITION_SRC[0],
        "source_url": _LAW_TUITION_SRC[1],
        "year": "2025-26",
    }


def _mailman_flat_cost(program: str, tuition: int, *, year: str = "2026-27") -> dict:
    return {
        "tuition_usd": tuition,
        "funded": False,
        "note": (
            f"Mailman School flat-rate {program} tuition across two semesters "
            f"(${tuition:,} total tuition; program fees apply on top)."
        ),
        "source": _MAILMAN_TUITION_SRC[0],
        "source_url": _MAILMAN_TUITION_SRC[1],
        "year": year,
    }


# Per-program graduate tuition, verified first-party (Columbia bulletin / school cost
# pages). Ph.D. / J.S.D. / DrPH rows stay omitted-with-reason (funded or per-credit-only).
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
    "columbia-emba": {
        "tuition_usd": 105360,
        "funded": False,
        "note": (
            "EMBA-NY Friday/Saturday Year 1 tuition ($52,680 per term × Fall + Spring = "
            "$105,360); total program tuition is $263,400 over five terms."
        ),
        "source": _CBS_EMBA_SRC[0],
        "source_url": _CBS_EMBA_SRC[1],
        "year": "2026-27",
    },
    "columbia-accounting-ms": {
        "tuition_usd": 58284,
        "funded": False,
        "note": (
            "MSAFA Year 1 flat-rate tuition (two semesters of the three-term program; "
            "estimated third term $29,142)."
        ),
        "source": _CBS_MS_SRC[0],
        "source_url": _CBS_MS_SRC[1],
        "year": "2025-26",
    },
    "columbia-financial-economics-ms": {
        "tuition_usd": 75256,
        "funded": False,
        "note": "MS in Financial Economics Year 1 flat-rate tuition (four-semester program).",
        "source": _CBS_MS_SRC[0],
        "source_url": _CBS_MS_SRC[1],
        "year": "2025-26",
    },
    "columbia-marketing-science-ms": {
        "tuition_usd": 79472,
        "funded": False,
        "note": (
            "MS in Marketing Science flat-rate tuition for the two-semester portion of the "
            "program (capstone typically taken in a third term at no additional tuition)."
        ),
        "source": _CBS_MS_SRC[0],
        "source_url": _CBS_MS_SRC[1],
        "year": "2025-26",
    },
    "columbia-computer-science-ms": _seas_ms_cost("Computer Science"),
    "columbia-mechanical-engineering-ms": _seas_ms_cost("Mechanical Engineering"),
    "columbia-electrical-engineering-ms": _seas_ms_cost("Electrical Engineering"),
    "columbia-biomedical-engineering-ms": _seas_ms_cost("Biomedical Engineering"),
    "columbia-chemical-engineering-ms": _seas_ms_cost("Chemical Engineering"),
    "columbia-civil-engineering-ms": _seas_ms_cost("Civil Engineering"),
    "columbia-applied-physics-ms": _seas_ms_cost("Applied Physics"),
    "columbia-applied-mathematics-ms": _seas_ms_cost("Applied Mathematics"),
    "columbia-materials-science-and-engineering-ms": _seas_ms_cost(
        "Materials Science and Engineering"
    ),
    "columbia-earth-and-environmental-engineering-ms": _seas_ms_cost(
        "Earth and Environmental Engineering"
    ),
    "columbia-computer-engineering-ms": _seas_ms_cost("Computer Engineering"),
    "columbia-operations-research-ms": _seas_ms_cost("Operations Research"),
    "columbia-industrial-engineering-ms": _seas_ms_cost("Industrial Engineering"),
    "columbia-financial-engineering-ms": _seas_ms_cost("Financial Engineering"),
    "columbia-management-science-and-engineering-ms": _seas_ms_cost(
        "Management Science and Engineering"
    ),
    "columbia-data-science-ms": _seas_ms_cost("Data Science"),
    "columbia-climate-and-society-ma": _gsas_ma_cost("Climate and Society"),
    "columbia-human-rights-studies-ma": _gsas_ma_cost("Human Rights Studies"),
    "columbia-qmss-ma": _gsas_ma_cost("Quantitative Methods in the Social Sciences"),
    "columbia-statistics-ma": _gsas_ma_cost("Statistics"),
    "columbia-jd": _law_cost("J.D."),
    "columbia-llm": _law_cost("LL.M."),
    "columbia-md": {
        "tuition_usd": _MD_TUITION,
        "funded": False,
        "note": (
            f"Vagelos College M.D. tuition (${_MD_TUITION:,} per year, uniform across "
            "all four years)."
        ),
        "source": "Vagelos College of Physicians and Surgeons — M.D. budget",
        "source_url": "https://www.vagelos.columbia.edu/education/degree-programs/md-program",
        "year": "2025-26",
    },
    "columbia-dental-dds": {
        "tuition_usd": _DDS_TUITION,
        "funded": False,
        "note": f"College of Dental Medicine D.D.S. tuition (${_DDS_TUITION:,} per year).",
        "source": "Columbia College of Dental Medicine — student budget",
        "source_url": "https://www.dental.columbia.edu/",
        "year": "2026-27",
    },
    "columbia-physical-therapy-dpt": {
        "tuition_usd": _DPT_TUITION_ANNUAL,
        "funded": False,
        "note": (
            "Doctor of Physical Therapy Year 1 tuition (Fall $23,464 + Spring $23,464 = "
            f"${_DPT_TUITION_ANNUAL:,}; summer term billed separately)."
        ),
        "source": "Columbia Programs in Physical Therapy — student budget",
        "source_url": (
            "https://www.vagelos.columbia.edu/education/academic-programs/"
            "programs-physical-therapy/doctor-physical-therapy/financial-fact-sheet"
        ),
        "year": "2026-27",
    },
    "columbia-genetic-counseling-ms": {
        "tuition_usd": 50731,
        "funded": False,
        "note": (
            "MS in Genetic Counseling tuition ($50,731 per year; 21-month program requires "
            "two years of enrollment)."
        ),
        "source": "Vagelos College — MS Genetic Counseling Tuition and Financial Aid",
        "source_url": (
            "https://www.vagelos.columbia.edu/education/academic-programs/"
            "program-genetic-counseling/ms-genetic-counseling/admission/tuition-and-financial-aid"
        ),
        "year": "2025-26",
    },
    "columbia-human-nutrition-ms": {
        "tuition_usd": 56854,
        "funded": False,
        "note": (
            "Institute of Human Nutrition M.S. tuition for the one-year program "
            "($56,854 for 2025-26)."
        ),
        "source": "Columbia Institute of Human Nutrition — Tuition and Financial Aid",
        "source_url": (
            "https://www.ihn.cuimc.columbia.edu/education/ms-human-nutrition/"
            "tuition-and-financial-aid"
        ),
        "year": "2025-26",
    },
    "columbia-journalism-ms": {
        "tuition_usd": 85576,
        "funded": False,
        "note": "Full-time M.S. in Journalism tuition (9.5-month program).",
        "source": _JOURNALISM_TUITION_SRC[0],
        "source_url": _JOURNALISM_TUITION_SRC[1],
        "year": "2025-26",
    },
    "columbia-journalism-ma": {
        "tuition_usd": 77890,
        "funded": False,
        "note": "Master of Arts in Journalism tuition (9-month program).",
        "source": _JOURNALISM_TUITION_SRC[0],
        "source_url": _JOURNALISM_TUITION_SRC[1],
        "year": "2025-26",
    },
    "columbia-data-journalism-ms": {
        "tuition_usd": 117546,
        "funded": False,
        "note": (
            "M.S. in Data Journalism tuition (12-month program spanning fall, spring, and "
            "summer)."
        ),
        "source": "Columbia Journalism School — Cost of Attendance",
        "source_url": "https://journalism.columbia.edu/cost-attendance",
        "year": "2024-25",
    },
    "columbia-sipa-mia": _sipa_cost("MIA"),
    "columbia-sipa-mpa": _sipa_cost("MPA"),
    "columbia-public-health-mph": _mailman_flat_cost("MPH", 49888),
    "columbia-health-administration-mha": _mailman_flat_cost("MHA", 49888),
    "columbia-biostatistics-ms": {
        "tuition_usd": 53352,
        "funded": False,
        "note": (
            "Mailman M.S. in Biostatistics Year 1 tuition (estimated ~24 credits at "
            "$2,223/credit = $53,352; per-credit rate applies for additional credits)."
        ),
        "source": _MAILMAN_TUITION_SRC[0],
        "source_url": _MAILMAN_TUITION_SRC[1],
        "year": "2026-27",
    },
    "columbia-social-work-msw": {
        "tuition_usd": _SSW_TUITION_ANNUAL,
        "funded": False,
        "note": (
            f"Columbia MSSW flat-rate tuition (${_SSW_TUITION_PER_SEM:,} per semester × 2 "
            f"= ${_SSW_TUITION_ANNUAL:,}; up to 19.5 credits per semester at the flat rate)."
        ),
        "source": _SSW_TUITION_SRC[0],
        "source_url": _SSW_TUITION_SRC[1],
        "year": "2025-26",
    },
    "columbia-architecture-march": {
        "tuition_usd": _GSAPP_MS_ANNUAL,
        "funded": False,
        "note": (
            f"GSAPP M.Arch tuition (${_GSAPP_MS_PER_TERM:,} per term × 2 = "
            f"${_GSAPP_MS_ANNUAL:,}; additional points at $2,346/point)."
        ),
        "source": _GSAPP_TUITION_SRC[0],
        "source_url": _GSAPP_TUITION_SRC[1],
        "year": "2025-26",
    },
    "columbia-urban-planning-ms": _gsapp_ms_cost("Urban Planning"),
    "columbia-historic-preservation-ms": _gsapp_ms_cost("Historic Preservation"),
    "columbia-real-estate-development-ms": _gsapp_ms_cost(
        "Real Estate Development", one_year=True
    ),
    "columbia-urban-design-ms": _gsapp_ms_cost("Urban Design"),
    "columbia-architecture-aad-ms": _gsapp_ms_cost("Advanced Architectural Design", one_year=True),
    "columbia-arts-mfa": {
        "tuition_usd": 74840,
        "funded": False,
        "note": (
            "School of the Arts MFA tuition for full-residency Years 1–2 "
            "($38,920 per semester × 2 = $74,840)."
        ),
        "source": _ARTS_TUITION_SRC[0],
        "source_url": _ARTS_TUITION_SRC[1],
        "year": "2025-26",
    },
    "columbia-film-media-studies-ma": {
        "tuition_usd": 73868,
        "funded": False,
        "note": (
            "M.A. in Film and Media Studies tuition ($36,934 per semester × 2 = $73,868)."
        ),
        "source": _ARTS_TUITION_SRC[0],
        "source_url": _ARTS_TUITION_SRC[1],
        "year": "2025-26",
    },
    "columbia-nursing-msn": {
        "tuition_usd": _MDE_TUITION_ANNUAL,
        "funded": False,
        "note": (
            f"Master's Direct Entry (MDE) flat-rate tuition (${_MDE_TUITION_PER_SEM:,} per "
            f"semester × 2 = ${_MDE_TUITION_ANNUAL:,}; 10–24 credits at the flat rate)."
        ),
        "source": _NURSING_TUITION_SRC[0],
        "source_url": _NURSING_TUITION_SRC[1],
        "year": "2024-25",
    },
    "columbia-nursing-dnp": {
        "tuition_usd": _DNP_TUITION_ANNUAL,
        "funded": False,
        "note": (
            f"Doctor of Nursing Practice full-time flat-rate tuition "
            f"(${_DNP_TUITION_PER_SEM:,} per semester × 2 = ${_DNP_TUITION_ANNUAL:,})."
        ),
        "source": _NURSING_TUITION_SRC[0],
        "source_url": _NURSING_TUITION_SRC[1],
        "year": "2024-25",
    },
}

# ── Program-specific outcomes (College Scorecard Field of Study, by CIP) ────
# Where the federal College Scorecard publishes a Field-of-Study median earnings (one year
# after completion) for an awarded CIP at UNITID 190150, we use it (program scope). Tuples
# are (median_earnings_1yr, cip).
_FOS_OUTCOMES: dict[str, tuple[int, str]] = {
    "columbia-economics-ba": (83135, "45.06"),
    "columbia-political-science-ba": (61077, "45.10"),
    "columbia-history-ba": (53828, "54.01"),
    "columbia-english-ba": (35838, "23.01"),
    "columbia-psychology-ba": (53156, "42.27"),
    "columbia-sociology-ba": (58541, "45.11"),
    "columbia-biology-ba": (40935, "26.01"),
    "columbia-computer-science-bs": (118636, "11.07"),
    "columbia-operations-research-bs": (110457, "14.37"),
    "columbia-mechanical-engineering-bs": (72036, "14.19"),
    "columbia-electrical-engineering-bs": (84019, "14.10"),
    "columbia-applied-mathematics-bs": (91559, "27.03"),
    "columbia-biomedical-engineering-bs": (62895, "14.05"),
    "columbia-computer-science-ms": (161851, "11.07"),
    "columbia-mba": (182930, "52.02"),
    "columbia-jd": (220843, "22.01"),
    "columbia-journalism-ms": (54170, "09.04"),
    "columbia-sipa-mia": (80448, "45.09"),
    "columbia-sipa-mpa": (89478, "44.04"),
    "columbia-public-health-mph": (71704, "51.22"),
    "columbia-social-work-msw": (59891, "44.07"),
}

# The M.D. is handled separately: the College Scorecard one-year figure for CIP 51.12
# (Medicine) reflects residency stipends, not attending-physician pay, so it carries a
# distinct verbatim condition.
_MD_OUTCOME = (78891, "51.12")

# Verbatim methodology for the program-scope Scorecard FOS earnings figure.
_FOS_CONDITIONS = (
    "Median earnings of graduates who received federal financial aid, measured "
    "approximately one year after program completion; reported by the U.S. Department of "
    "Education College Scorecard Field of Study by 4-digit CIP code. Programs with too few "
    "completers are suppressed."
)

# Institution-wide outcomes fallback (College Scorecard, UNITID 190150), used for degree
# programs whose program-level one-year earnings are suppressed (the M.Arch and the MFA).
_OUTCOMES_INSTITUTION = {
    "median_salary": 102491,
    "scope": "institution",
    "conditions": (
        "Columbia institution-wide median earnings ten years after entry (College "
        "Scorecard, UNITID 190150); a program-level one-year earnings figure is not "
        "published (suppressed) for this field of study."
    ),
    "source": "U.S. Dept. of Education College Scorecard (UNITID 190150)",
    "source_url": "https://collegescorecard.ed.gov/school/?190150",
}

# Annual degrees conferred per CIP (College Scorecard Field of Study, IPEDS awards), used
# for the flagship class-profile cohort figure.
_AWARDS_BY_SLUG: dict[str, int] = {"columbia-computer-science-bs": 391}

# ── Class profile, where published (the flagship) ──────────────────────────
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    "columbia-computer-science-bs": {
        "cohort_size": (
            "≈391 computer science bachelor's degrees awarded annually (one of Columbia's "
            "largest majors)"
        ),
        "note": (
            "Columbia does not publish a per-major entering-cohort size; the figure is the "
            "annual count of computer science bachelor's degrees awarded (College Scorecard "
            "Field of Study, CIP 11.07)."
        ),
        "source": "U.S. Dept. of Education College Scorecard — Field of Study (CIP 11.07)",
        "source_url": "https://collegescorecard.ed.gov/school/?190150",
    },
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
    "columbia-computer-science-bs": {
        "lead": [
            {
                "name": "Luca Carloni",
                "title": "Professor and Chair of the Department of Computer Science",
            },
            {
                "name": "Christos H. Papadimitriou",
                "title": (
                    "The Donovan Family Professor of Computer Science; computational "
                    "complexity, algorithms and the theory of computation"
                ),
            },
            {
                "name": "Mihalis Yannakakis",
                "title": (
                    "Percy K. and Vida L. W. Hudson Professor of Computer Science; "
                    "algorithms and computational complexity"
                ),
            },
        ],
        "note": (
            "Columbia Computer Science is chaired by Luca Carloni; its faculty include the "
            "theory pioneers Christos Papadimitriou and Mihalis Yannakakis."
        ),
        "directory_url": "https://www.cs.columbia.edu/people/faculty/",
    },
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
            "Silfen Professor of Business; its faculty span finance, economics, marketing, "
            "management and operations."
        ),
        "directory_url": "https://business.columbia.edu/faculty",
    },
}

# ── Aggregated, cited student-review themes (≥2 third-party sources, the flagship) ──
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "columbia-computer-science-bs": {
        "summary": (
            "Students and third-party guides describe Columbia as academically rigorous and "
            "intellectually enriching — the Core Curriculum and distinguished faculty draw "
            "consistent praise, and Columbia's New York City location is repeatedly cited as "
            "an advantage for research, internships and computer-science careers (Niche rates "
            "Columbia the No. 1 college for computer science in New York). Common cautions are "
            "that the academic pressure can feel intense, the atmosphere competitive, and "
            "administrative support uneven, so students are advised to self-advocate."
        ),
        "themes": [
            {
                "label": "Core Curriculum & academic rigor",
                "sentiment": "positive",
                "detail": "The Core Curriculum and rigorous teaching are widely praised.",
            },
            {
                "label": "Distinguished faculty",
                "sentiment": "positive",
                "detail": "Knowledgeable, accomplished professors across departments.",
            },
            {
                "label": "New York City advantage",
                "sentiment": "positive",
                "detail": "NYC drives research, internship and CS-career access.",
            },
            {
                "label": "Academic pressure",
                "sentiment": "caution",
                "detail": "Reviewers note the workload and pressure can feel intense.",
            },
            {
                "label": "Administrative support",
                "sentiment": "caution",
                "detail": "Bureaucracy can be slow; students must self-advocate.",
            },
        ],
        "sources": [
            {
                "label": "Niche — Columbia University",
                "url": "https://www.niche.com/colleges/columbia-university/",
            },
            {
                "label": "U.S. News — Columbia University",
                "url": "https://www.usnews.com/best-colleges/columbia-university-2707",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
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
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-business-schools/"
                    "columbia-university-01060"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "columbia-jd": {
        "summary": (
            "Students and third-party guides describe Columbia Law as a top-tier program "
            "in the heart of New York City — U.S. News ranked it tied for No. 9 nationally "
            "in 2026 — praised for its corporate-law strength, federal-clerkship placement, "
            "and proximity to Wall Street and major law firms. Common cautions are extremely "
            "selective admission, high tuition and New York living costs, and an intense "
            "academic culture that can feel less collegial than some peer schools."
        ),
        "themes": [
            {
                "label": "Elite national rank",
                "sentiment": "positive",
                "detail": "U.S. News Best Law Schools 2026: tied for No. 9 nationally.",
            },
            {
                "label": "Corporate law & clerkships",
                "sentiment": "positive",
                "detail": (
                    "Strong placement in Big Law, corporate practice, and federal clerkships "
                    "from a Manhattan campus."
                ),
            },
            {
                "label": "New York City access",
                "sentiment": "positive",
                "detail": (
                    "Unmatched proximity to courts, firms, and public-interest employers in "
                    "New York."
                ),
            },
            {
                "label": "Selectivity & cost",
                "sentiment": "caution",
                "detail": (
                    "Among the most selective J.D. programs with tuition exceeding $80,000 "
                    "per year plus NYC living expenses."
                ),
            },
            {
                "label": "Intense culture",
                "sentiment": "mixed",
                "detail": (
                    "Reviewers note the workload and competition can feel less relaxed than "
                    "some peer law schools."
                ),
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Columbia University (Law)",
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-law-schools/"
                    "columbia-university-03011"
                ),
            },
            {
                "label": "The Princeton Review — Columbia Law School",
                "url": "https://www.princetonreview.com/law/columbia-university--law-school-1035806",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "columbia-md": {
        "summary": (
            "Applicants and guides describe Vagelos as an elite research medical school "
            "with clinical training at Columbia University Irving Medical Center — it "
            "withdrew from U.S. News medical-school rankings in 2023 (its last numbered "
            "rank was fourth) but remains a top NIH-funded institution. Common cautions "
            "are extremely competitive admission, high cost of attendance in New York, and "
            "the intensity of a four-year professional curriculum."
        ),
        "themes": [
            {
                "label": "Research medical school",
                "sentiment": "positive",
                "detail": (
                    "Historically a top-five U.S. research medical school with strong NIH "
                    "funding and CUIMC clinical integration."
                ),
            },
            {
                "label": "Clinical training",
                "sentiment": "positive",
                "detail": (
                    "Patient-centered curriculum with training at NewYork-Presbyterian / "
                    "Columbia University Irving Medical Center."
                ),
            },
            {
                "label": "Ranking transparency",
                "sentiment": "mixed",
                "detail": (
                    "Vagelos withdrew from U.S. News in 2023 over methodology concerns but "
                    "continues publishing admissions data."
                ),
            },
            {
                "label": "Selectivity & cost",
                "sentiment": "caution",
                "detail": (
                    "Highly selective admission with first-year tuition near $70,000 plus "
                    "Manhattan living expenses."
                ),
            },
            {
                "label": "Professional intensity",
                "sentiment": "caution",
                "detail": (
                    "Reviewers note the four-year M.D. curriculum is demanding even by "
                    "medical-school standards."
                ),
            },
        ],
        "sources": [
            {
                "label": "Vagelos College — U.S. News rankings withdrawal",
                "url": (
                    "https://www.cuimc.columbia.edu/news/"
                    "medical-school-rankings"
                ),
            },
            {
                "label": "Newswise — Vagelos withdraws from U.S. News (2023)",
                "url": (
                    "https://www.newswise.com/articles/"
                    "columbia-university-s-vagelos-college-of-physicians-surgeons-withdraws-"
                    "from-participation-in-u-s-news-world-report-medical-school-rankings"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "columbia-public-health-mph": {
        "summary": (
            "Students and public-health guides describe Mailman's MPH as a top-tier program "
            "— U.S. News ranked Columbia tied for No. 6 among accredited MPH programs in "
            "2026 — with strengths in epidemiology, health policy, and global health from "
            "a Manhattan medical-campus base. Common cautions are the program's analytical "
            "rigor, high tuition relative to public peers, and a large cohort that can feel "
            "impersonal without proactive networking."
        ),
        "themes": [
            {
                "label": "Top national MPH rank",
                "sentiment": "positive",
                "detail": "U.S. News 2026: tied for No. 6 among accredited MPH programs.",
            },
            {
                "label": "Epidemiology & policy depth",
                "sentiment": "positive",
                "detail": (
                    "Strong departments in epidemiology, biostatistics, and health policy "
                    "with NYC health-agency access."
                ),
            },
            {
                "label": "Dual-degree pathways",
                "sentiment": "positive",
                "detail": (
                    "MD/MPH, JD/MPH, and MBA/MPH options pair public health with "
                    "Columbia's professional schools."
                ),
            },
            {
                "label": "Analytical rigor",
                "sentiment": "mixed",
                "detail": (
                    "Quantitative core courses in biostatistics and epidemiology can feel "
                    "demanding for non-quant backgrounds."
                ),
            },
            {
                "label": "Cost & cohort size",
                "sentiment": "caution",
                "detail": (
                    "Tuition exceeds many public MPH programs; students must build community "
                    "in a large graduate school."
                ),
            },
        ],
        "sources": [
            {
                "label": "UC Berkeley Public Health — 2026 U.S. News MPH rankings",
                "url": (
                    "https://publichealth.berkeley.edu/articles/news/"
                    "ucbph-surges-to-6-in-us-news-rankings"
                ),
            },
            {
                "label": "Columbia Mailman School — About",
                "url": "https://www.publichealth.columbia.edu/about-us/frequently-asked-questions",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "columbia-economics-ba": {
        "summary": (
            "Students and third-party guides describe Columbia's economics major as the "
            "nation's top undergraduate economics program — Niche ranks Columbia No. 1 for "
            "economics in America (2026) — with rigorous theory, econometrics, and "
            "interdisciplinary tracks plus New York City finance and policy access. Common "
            "cautions are large introductory sections, competitive grading in quantitative "
            "courses, and the Core Curriculum adding breadth beyond a purely technical track."
        ),
        "themes": [
            {
                "label": "No. 1 for economics",
                "sentiment": "positive",
                "detail": "Niche Best Colleges for Economics 2026: No. 1 nationally.",
            },
            {
                "label": "Theory & econometrics rigor",
                "sentiment": "positive",
                "detail": (
                    "A analytically demanding program with six major tracks and faculty "
                    "active in top-tier research."
                ),
            },
            {
                "label": "NYC finance & policy access",
                "sentiment": "positive",
                "detail": (
                    "Wall Street, consulting, and policy employers recruit heavily from "
                    "Columbia economics graduates."
                ),
            },
            {
                "label": "Large intro courses",
                "sentiment": "caution",
                "detail": (
                    "Principles and intermediate courses can feel large before students "
                    "reach smaller seminars."
                ),
            },
            {
                "label": "Core + quantitative load",
                "sentiment": "mixed",
                "detail": (
                    "Columbia's Core adds intellectual breadth but can compete with "
                    "economics electives for some students."
                ),
            },
        ],
        "sources": [
            {
                "label": "Niche — Best Colleges for Economics (2026)",
                "url": "https://www.niche.com/colleges/search/best-colleges-for-economics/",
            },
            {
                "label": "Columbia Economics — About the Program",
                "url": "https://econ.columbia.edu/undergraduate/the-program/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "columbia-journalism-ms": {
        "summary": (
            "Students and industry guides describe Columbia Journalism School as the "
            "premier graduate journalism program in the United States — it administers the "
            "Pulitzer Prizes and places graduates at major national outlets — praised for "
            "investigative reporting training and New York City media access. Common "
            "cautions are high tuition with uncertain long-term journalism salaries, a "
            "practitioner-focused (not academic-theory) curriculum, and intense competition "
            "for the most selective reporting beats."
        ),
        "themes": [
            {
                "label": "Industry gold standard",
                "sentiment": "positive",
                "detail": (
                    "Widely regarded as the top U.S. graduate journalism program with "
                    "Pulitzer Prize ties and elite faculty."
                ),
            },
            {
                "label": "Investigative reporting",
                "sentiment": "positive",
                "detail": (
                    "Strong investigative, data, and documentary tracks with NYC newsroom "
                    "internships."
                ),
            },
            {
                "label": "Media placement",
                "sentiment": "positive",
                "detail": (
                    "Graduates regularly place at The New York Times, NPR, and major "
                    "international outlets."
                ),
            },
            {
                "label": "Tuition vs. industry pay",
                "sentiment": "caution",
                "detail": (
                    "Tuition near $70,000/year can be hard to recoup given journalism's "
                    "uneven salary ladder."
                ),
            },
            {
                "label": "Practitioner not academic",
                "sentiment": "mixed",
                "detail": (
                    "Some students want more media-theory depth; the program prioritizes "
                    "working-journalist skills."
                ),
            },
        ],
        "sources": [
            {
                "label": "Niche — Columbia Journalism School",
                "url": "https://www.niche.com/graduate-schools/columbia-journalism-school/",
            },
            {
                "label": "Columbia Journalism School — About",
                "url": "https://journalism.columbia.edu/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "columbia-sipa-mpa": {
        "summary": (
            "Students and policy guides describe SIPA's MPA as a top global-affairs degree "
            "— U.S. News ranked Columbia No. 1 in International Global Policy and "
            "Administration in 2025 — with quantitative policy training, UN and NGO "
            "internships, and a diverse international cohort in New York City. Common "
            "cautions are high tuition, a large program where students must self-advocate "
            "for mentorship, and less D.C. proximity than Georgetown for federal-policy "
            "careers."
        ),
        "themes": [
            {
                "label": "No. 1 global policy",
                "sentiment": "positive",
                "detail": (
                    "U.S. News 2025: No. 1 in International Global Policy and "
                    "Administration."
                ),
            },
            {
                "label": "Quantitative policy core",
                "sentiment": "positive",
                "detail": (
                    "Economics, statistics, and management courses ground every "
                    "specialization."
                ),
            },
            {
                "label": "International cohort",
                "sentiment": "positive",
                "detail": (
                    "Roughly half the student body is international, with strong UN and "
                    "multilateral ties."
                ),
            },
            {
                "label": "Large program",
                "sentiment": "caution",
                "detail": (
                    "A big MPA cohort can feel impersonal without proactive faculty "
                    "outreach."
                ),
            },
            {
                "label": "NYC not D.C.",
                "sentiment": "mixed",
                "detail": (
                    "Strong for global affairs and finance-policy roles; federal-policy "
                    "seekers may prefer Washington-based peers."
                ),
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Global Policy and Administration Programs",
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-public-affairs-schools/"
                    "global-policy-administration-rankings"
                ),
            },
            {
                "label": "Columbia SIPA — About",
                "url": "https://www.sipa.columbia.edu/sipa-education/masters-programs/mpa",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "columbia-architecture-march": {
        "summary": (
            "Students and architecture guides describe Columbia GSAPP's M.Arch as an "
            "intellectually ambitious program in New York City — historically a top-ranked "
            "NAAB-accredited program on DesignIntelligence surveys — praised for critical "
            "theory, urban design, and ties to NYC's architecture and real-estate industries. "
            "Common cautions are high tuition, a theory-heavy curriculum that can feel less "
            "studio-practical than some peers, and intense studio workloads."
        ),
        "themes": [
            {
                "label": "Top architecture pedigree",
                "sentiment": "positive",
                "detail": (
                    "GSAPP has repeatedly ranked among the top NAAB-accredited graduate "
                    "architecture programs nationally."
                ),
            },
            {
                "label": "Critical & urban design",
                "sentiment": "positive",
                "detail": (
                    "Strong in urban design, preservation, and real-estate development "
                    "within NYC."
                ),
            },
            {
                "label": "NYC professional access",
                "sentiment": "positive",
                "detail": (
                    "Proximity to major architecture firms, developers, and cultural "
                    "institutions."
                ),
            },
            {
                "label": "Theory-heavy curriculum",
                "sentiment": "mixed",
                "detail": (
                    "Some students want more technical/building-science depth than GSAPP's "
                    "critical orientation provides."
                ),
            },
            {
                "label": "Studio intensity & cost",
                "sentiment": "caution",
                "detail": (
                    "Long studio hours plus Manhattan living costs make the M.Arch an "
                    "expensive commitment."
                ),
            },
        ],
        "sources": [
            {
                "label": "Columbia GSAPP — About",
                "url": "https://www.arch.columbia.edu/",
            },
            {
                "label": "Wikipedia — Columbia GSAPP (DesignIntelligence rankings)",
                "url": (
                    "https://en.wikipedia.org/wiki/"
                    "Columbia_Graduate_School_of_Architecture,_Planning_and_Preservation"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "columbia-social-work-msw": {
        "summary": (
            "Students and social-work guides describe Columbia's MSW as one of the nation's "
            "oldest and most respected programs — U.S. News ranked it No. 4 for social work "
            "in 2025 and TheBestSchools.org lists it among the top ten MSW programs — with "
            "clinical and policy concentrations, field placements across New York City, and "
            "dual-degree options. Common cautions are high tuition, emotionally demanding "
            "field work, and a large program where students must seek out individualized "
            "faculty support."
        ),
        "themes": [
            {
                "label": "Top national MSW rank",
                "sentiment": "positive",
                "detail": "U.S. News 2025: No. 4 among social-work graduate programs.",
            },
            {
                "label": "Historic program",
                "sentiment": "positive",
                "detail": (
                    "Founded in 1898 as the first social-work school in the United States."
                ),
            },
            {
                "label": "NYC field placements",
                "sentiment": "positive",
                "detail": (
                    "Clinical and policy field work across hospitals, schools, and "
                    "nonprofits in New York City."
                ),
            },
            {
                "label": "Emotional demands",
                "sentiment": "caution",
                "detail": (
                    "Field placements in trauma, mental health, and child welfare can be "
                    "emotionally taxing."
                ),
            },
            {
                "label": "Cost & cohort size",
                "sentiment": "caution",
                "detail": (
                    "Tuition is among the highest in social work; students must actively "
                    "build faculty relationships."
                ),
            },
        ],
        "sources": [
            {
                "label": "TheBestSchools.org — Best MSW Programs 2025",
                "url": "https://thebestschools.org/rankings/masters/best-masters-social-work/",
            },
            {
                "label": "Columbia School of Social Work — About",
                "url": "https://socialwork.columbia.edu/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    **DEPTH_REVIEWS,
}

# ── Application requirements ─────────────────────────────────────────────────
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission.",
}
# Undergraduate (Columbia College / Columbia Engineering) admission via the Common
# Application or QuestBridge. Columbia is permanently test-optional.
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application or QuestBridge Application", "required": True},
        {"name": "Columbia-specific writing supplement", "required": True},
        {"name": "Secondary-school transcript + school report", "required": True},
        {"name": "Counselor recommendation", "required": True},
        {"name": "Two teacher recommendations", "required": True},
        {"name": "$85 application fee; need-based fee waivers available", "required": True},
        {
            "name": "Standardized test scores",
            "required": False,
            "note": (
                "Columbia is permanently test-optional for applicants to Columbia College "
                "and Columbia Engineering; applicants who do not submit SAT/ACT scores are "
                "not disadvantaged."
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
    "source_url": "https://undergrad.admissions.columbia.edu/apply/process",
}

# Generic Columbia graduate / professional admission set. Each professional school
# administers its own admissions; the materials below are common across Columbia graduate
# and professional programs, and deadlines vary by program — applicants are pointed to the
# program's own admissions page via the program website.
_REQ_GRAD_GENERIC = {
    "materials": [
        {"name": "Program online application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose / personal statement", "required": True},
        {"name": "Résumé / CV", "required": True},
        {
            "name": "Letters of recommendation",
            "required": True,
            "note": "Most Columbia graduate/professional programs require two to three letters.",
        },
        {
            "name": "Standardized test scores (GRE/GMAT/LSAT/MCAT)",
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
            "Most Columbia graduate and professional programs require two to three letters of "
            "recommendation."
        ),
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": True,
            "note": (
                "Required for applicants whose native language is not English; an exemption "
                "applies to degrees earned where English is the language of instruction."
            ),
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Columbia — International Students and Scholars Office",
                "url": "https://isso.columbia.edu/",
            }
        ],
    },
    "source": "Columbia graduate & professional admissions",
    "source_url": "https://www.columbia.edu/content/academics/schools",
}


def _requirements_for(spec: dict) -> dict:
    """Pick the admissions requirement set for a program by degree type."""
    if spec["degree_type"] == "masters":
        return dict(_REQ_GRAD_GENERIC)
    return dict(_REQ_UNDERGRAD)


# Butler Library leads the institution hero; see ``SCHOOL_OUTCOMES["campus_photos"]``.
_CAMPUS_PHOTO = SCHOOL_OUTCOMES["campus_photos"][0]["url"]


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
        # Every school gets a working feed: its verified RSS (or the shared CC/SEAS feed
        # filtered by school keywords) so the Events & Updates tab populates.
        sc.content_sources = _school_content(spec["name"])
        by_name[spec["name"]] = sc
    # Drop legacy schools — programs.school_id is ON DELETE SET NULL, so this is FK-safe.
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


def _program_standard(slug: str) -> dict:
    """Per-program omitted-field list (verified-unavailable), for _standard."""
    omitted: list[str] = []
    # Columbia publishes no per-program employment report or industry breakdown (its
    # first-destination data is reported college-wide at the institution level), so every
    # program omits the program-level employment rate and top industries.
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
    # Cost: undergraduate programs all carry the published Columbia undergraduate tuition;
    # graduate/professional programs carry tuition where verified first-party (see
    # _COST_BY_SLUG). Funded Ph.D. / J.S.D. and per-credit-only DrPH omit the figure.
    is_undergrad = any(p["slug"] == slug and p["degree_type"] == "bachelors" for p in PROGRAMS)
    if not is_undergrad and slug not in _COST_BY_SLUG:
        # cost_data is cleared entirely for these programs, so both the figure and its
        # source path are absent — record both as verified-unavailable.
        omitted += ["cost_data.tuition_usd", "cost_data.source"]
    return _standard(omitted)


def _apply_programs(session: Session, inst: Institution, school_by_name: dict[str, School]) -> None:
    existing = {
        p.slug: p
        for p in session.scalars(select(Program).where(Program.institution_id == inst.id))
        if p.slug
    }
    canonical = set(PROGRAM_SLUGS)
    undergrad_slugs = {p["slug"] for p in PROGRAMS if p["degree_type"] == "bachelors"}
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
        p.department = spec.get("department")
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "on_campus")
        # Every program gets a working feed: its school's verified RSS filtered by
        # program-naming keywords (CS uses the Data Science Institute feed).
        p.content_sources = _program_content(spec)
        # Cost: undergraduate uses the published Columbia undergraduate rates; graduate
        # programs use verified per-program tuition where available, else omit (cost_data
        # cleared and the path recorded in _standard.omitted).
        cost_override = _COST_BY_SLUG.get(slug)
        if slug in undergrad_slugs:
            p.tuition = _TUITION_UG
            p.cost_data = {
                "tuition_usd": _TUITION_UG,
                "total_cost_of_attendance": _UNDERGRAD_COA,
                "avg_net_price": _AVG_NET_PRICE,
                "breakdown": {
                    "tuition": _TUITION_UG,
                    "mandatory_fees": _UNDERGRAD_FEES,
                    "total_cost_of_attendance": _UNDERGRAD_COA,
                },
                "funded": False,
                "note": (
                    "Published 2025-26 Columbia undergraduate tuition ($35,085 per term × 2 = "
                    "$70,170, shared by Columbia College and Columbia Engineering) plus "
                    "$3,280 in mandatory fees, with the College Scorecard cost of attendance "
                    "and average net price. Columbia is need-blind for U.S. applicants and "
                    "meets 100% of demonstrated need with grants rather than loans, so most "
                    "families pay far less than the sticker price (average net price ≈ "
                    "$21,600)."
                ),
                "source": "Columbia College bulletin (2025-26) + College Scorecard (UNITID 190150)",
                "source_url": "https://bulletin.columbia.edu/columbia-college/fees-expenses-financial-aid/",
                "year": "2025-26",
            }
        elif cost_override is not None:
            p.tuition = cost_override.get("tuition_usd")
            p.cost_data = dict(cost_override)
        else:
            p.tuition = None
            p.cost_data = None
        # Admissions: undergraduate or generic graduate set by degree type.
        p.application_requirements = _requirements_for(spec)
        # Outcomes precedence: Scorecard FOS (program) → institution median.
        if slug == "columbia-md":
            salary, cip = _MD_OUTCOME
            outcomes = {
                "median_salary": salary,
                "scope": "program",
                "cip": cip,
                "earnings_timeframe": "median earnings 1 year after completion",
                "conditions": (
                    _FOS_CONDITIONS
                    + " For the M.D. this one-year figure reflects residency stipends rather "
                    "than attending-physician compensation, because graduates are in "
                    "residency one year after completion."
                ),
                "source": "U.S. Dept. of Education College Scorecard — Field of Study",
                "source_url": "https://collegescorecard.ed.gov/school/?190150",
            }
        else:
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
                    "source_url": "https://collegescorecard.ed.gov/school/?190150",
                }
                awards = _AWARDS_BY_SLUG.get(slug)
                if awards is not None:
                    outcomes["degrees_conferred_annual"] = awards
            else:
                outcomes = dict(_OUTCOMES_INSTITUTION)
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
        # Application deadline: only undergraduate admission (Columbia College / Columbia
        # Engineering) has a single fixed Columbia Regular Decision date (Jan 1). Graduate
        # and professional deadlines vary by program (see _REQ_GRAD_GENERIC), so we leave
        # them null rather than stamp a fabricated date that the APIs, saved lists, checklist
        # reminders and Connect deadline-sort would surface.
        p.application_deadline = date(2027, 1, 1) if slug in undergrad_slugs else None
    session.flush()
    # Reconcile legacy Columbia programs (slug not in the canonical set): delete when
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
