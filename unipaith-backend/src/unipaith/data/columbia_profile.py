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
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.columbia_ipeds_catalog import _IPEDS_CATALOG
from unipaith.data.profile_catalog_utils import (
    disambiguate_program_name,
    program_description,
    validate_catalog,
)
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Columbia University in the City of New York"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-14"


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
    # Butler Library campus photo — Wikimedia Commons / Bitterteayen (CC BY-SA 4.0),
    # verified on the file page 2026-06-11.
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

# ── The program catalog (real majors/degrees, organized by school) ─────────
# slug = idempotency key. Every program is mapped to its owning school from Columbia's
# official structure. The program set is built from the College Scorecard Field-of-Study
# list for UNITID 190150 (the deterministic federal view, degree-by-CIP). Graduate degrees
# use the generic ``masters`` type with the real degree name carried in the program name
# (professional doctorates J.D. and M.D. are modelled as ``masters`` to match the platform
# enum, with the degree named in the title).
PROGRAMS: list[dict] = [
    # ── Columbia College (undergraduate B.A. majors) ──
    {
        "slug": "columbia-economics-ba",
        "school": _CC,
        "program_name": "Economics",
        "degree_type": "bachelors",
        "cip": "45.06",
        "duration_months": 48,
        "description": "Economics — micro, macro, econometrics and economic history.",
    },
    {
        "slug": "columbia-political-science-ba",
        "school": _CC,
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
        "slug": "columbia-history-ba",
        "school": _CC,
        "program_name": "History",
        "degree_type": "bachelors",
        "cip": "54.01",
        "duration_months": 48,
        "description": "History — the study of the human past across periods and regions.",
    },
    {
        "slug": "columbia-english-ba",
        "school": _CC,
        "program_name": "English and Comparative Literature",
        "degree_type": "bachelors",
        "cip": "23.01",
        "duration_months": 48,
        "description": "English and comparative literature — literature, criticism and writing.",
    },
    {
        "slug": "columbia-psychology-ba",
        "school": _CC,
        "program_name": "Psychology",
        "degree_type": "bachelors",
        "cip": "42.27",
        "duration_months": 48,
        "description": "Psychology — cognitive, developmental, social and clinical science.",
    },
    {
        "slug": "columbia-sociology-ba",
        "school": _CC,
        "program_name": "Sociology",
        "degree_type": "bachelors",
        "cip": "45.11",
        "duration_months": 48,
        "description": "Sociology — social structure, inequality and the study of society.",
    },
    {
        "slug": "columbia-biology-ba",
        "school": _CC,
        "program_name": "Biology",
        "degree_type": "bachelors",
        "cip": "26.01",
        "duration_months": 48,
        "description": "Biology — molecular, cellular and organismal biology and genetics.",
    },
    # ── The Fu Foundation School of Engineering and Applied Science (undergraduate) ──
    {
        "slug": "columbia-computer-science-bs",
        "school": _SEAS,
        "program_name": "Computer Science",
        "degree_type": "bachelors",
        "cip": "11.07",
        "duration_months": 48,
        "description": (
            "Columbia's flagship computing major — offered as the B.S. (Columbia "
            "Engineering) and the B.A. (Columbia College), spanning AI, machine learning, "
            "systems, theory and graphics through the Department of Computer Science."
        ),
    },
    {
        "slug": "columbia-operations-research-bs",
        "school": _SEAS,
        "program_name": "Operations Research",
        "degree_type": "bachelors",
        "cip": "14.37",
        "duration_months": 48,
        "description": (
            "Operations research — optimization, stochastic modeling and analytics in the "
            "Department of Industrial Engineering and Operations Research."
        ),
    },
    {
        "slug": "columbia-mechanical-engineering-bs",
        "school": _SEAS,
        "program_name": "Mechanical Engineering",
        "degree_type": "bachelors",
        "cip": "14.19",
        "duration_months": 48,
        "description": (
            "Mechanical engineering — mechanics, thermofluids, robotics and design."
        ),
    },
    {
        "slug": "columbia-electrical-engineering-bs",
        "school": _SEAS,
        "program_name": "Electrical Engineering",
        "degree_type": "bachelors",
        "cip": "14.10",
        "duration_months": 48,
        "description": (
            "Electrical engineering — circuits, signals, devices, communications and systems."
        ),
    },
    {
        "slug": "columbia-applied-mathematics-bs",
        "school": _SEAS,
        "program_name": "Applied Mathematics",
        "degree_type": "bachelors",
        "cip": "27.03",
        "duration_months": 48,
        "description": (
            "Applied mathematics — modeling, analysis and computation in the Department of "
            "Applied Physics and Applied Mathematics."
        ),
    },
    {
        "slug": "columbia-biomedical-engineering-bs",
        "school": _SEAS,
        "program_name": "Biomedical Engineering",
        "degree_type": "bachelors",
        "cip": "14.05",
        "duration_months": 48,
        "description": (
            "Biomedical engineering — engineering principles applied to medicine and biology."
        ),
    },
    # ── The Fu Foundation School of Engineering and Applied Science (graduate) ──
    {
        "slug": "columbia-computer-science-ms",
        "school": _SEAS,
        "program_name": "Master of Science in Computer Science (M.S.)",
        "degree_type": "masters",
        "cip": "11.07",
        "duration_months": 18,
        "description": (
            "The 30-point M.S. in Computer Science — advanced study across tracks such as "
            "machine learning, systems, vision, NLP, security and theory."
        ),
    },
    # ── Columbia Business School ──
    {
        "slug": "columbia-mba",
        "school": _CBS,
        "program_name": "Master of Business Administration (MBA)",
        "degree_type": "masters",
        "cip": "52.02",
        "duration_months": 24,
        "description": (
            "The full-time, two-year MBA — connecting academic theory to real-world "
            "practice from the heart of New York City."
        ),
    },
    # ── Columbia Law School ──
    {
        "slug": "columbia-jd",
        "school": _LAW,
        "program_name": "Juris Doctor (J.D.)",
        "degree_type": "masters",
        "cip": "22.01",
        "duration_months": 36,
        "description": (
            "The three-year Juris Doctor — Columbia Law School's professional law degree, "
            "with strength in corporate, constitutional and international law."
        ),
    },
    # ── Vagelos College of Physicians and Surgeons ──
    {
        "slug": "columbia-md",
        "school": _PS,
        "program_name": "Doctor of Medicine (M.D.)",
        "degree_type": "masters",
        "cip": "51.12",
        "duration_months": 48,
        "description": (
            "The four-year Doctor of Medicine — awarded by the first U.S. medical school to "
            "confer the M.D., at Columbia University Irving Medical Center."
        ),
    },
    # ── Columbia Journalism School ──
    {
        "slug": "columbia-journalism-ms",
        "school": _JOUR,
        "program_name": "Master of Science in Journalism (M.S.)",
        "degree_type": "masters",
        "cip": "09.04",
        "duration_months": 10,
        "description": (
            "The Master of Science in Journalism — the flagship reporting degree of the only "
            "Ivy League journalism school, which administers the Pulitzer Prizes."
        ),
    },
    # ── School of International and Public Affairs ──
    {
        "slug": "columbia-sipa-mia",
        "school": _SIPA,
        "program_name": "Master of International Affairs (MIA)",
        "degree_type": "masters",
        "cip": "45.09",
        "duration_months": 24,
        "description": (
            "The two-year Master of International Affairs — policy, security and development "
            "for careers in international and public affairs."
        ),
    },
    {
        "slug": "columbia-sipa-mpa",
        "school": _SIPA,
        "program_name": "Master of Public Administration (MPA)",
        "degree_type": "masters",
        "cip": "44.04",
        "duration_months": 24,
        "description": (
            "The two-year Master of Public Administration — management and policy analysis "
            "for public-service and policy leadership."
        ),
    },
    # ── Mailman School of Public Health ──
    {
        "slug": "columbia-public-health-mph",
        "school": _MAILMAN,
        "program_name": "Master of Public Health (MPH)",
        "degree_type": "masters",
        "cip": "51.22",
        "duration_months": 24,
        "description": (
            "The accredited Master of Public Health — biostatistics, epidemiology, "
            "environmental health, health policy and population health."
        ),
    },
    # ── Columbia School of Social Work ──
    {
        "slug": "columbia-social-work-msw",
        "school": _SSW,
        "program_name": "Master of Science in Social Work (MSW)",
        "degree_type": "masters",
        "cip": "44.07",
        "duration_months": 24,
        "description": (
            "The Master of Science in Social Work — clinical practice and social policy at "
            "the oldest school of social work in the United States."
        ),
    },
    # ── Graduate School of Architecture, Planning and Preservation ──
    {
        "slug": "columbia-architecture-march",
        "school": _GSAPP,
        "program_name": "Master of Architecture (M.Arch)",
        "degree_type": "masters",
        "cip": "04.02",
        "duration_months": 36,
        "description": (
            "The three-year professional Master of Architecture — Columbia GSAPP's flagship "
            "design degree."
        ),
    },
    # ── Columbia School of the Arts ──
    {
        "slug": "columbia-arts-mfa",
        "school": _ARTS,
        "program_name": "Master of Fine Arts (MFA)",
        "degree_type": "masters",
        "cip": "50.06",
        "duration_months": 24,
        "description": (
            "The Master of Fine Arts — Columbia's terminal arts degree in film, theatre, "
            "visual arts or writing."
        ),
    },
    # ── Columbia School of Nursing ──
    {
        "slug": "columbia-nursing-msn",
        "school": _NURSING,
        "program_name": "Master's Direct Entry Program in Nursing (MDE)",
        "degree_type": "masters",
        "cip": "51.38",
        "duration_months": 15,
        "description": (
            "The Master's Direct Entry program — an accelerated path to registered-nurse "
            "licensure for students entering nursing from another field."
        ),
    },
]

for _ep in PROGRAMS:
    _ep.setdefault("delivery_format", "in_person")

_EXPLICIT_DEPARTMENTS: dict[str, str] = {
    "columbia-economics-ba": "Department of Economics",
    "columbia-political-science-ba": "Department of Political Science",
    "columbia-history-ba": "Department of History",
    "columbia-english-ba": "Department of English and Comparative Literature",
    "columbia-psychology-ba": "Department of Psychology",
    "columbia-sociology-ba": "Department of Sociology",
    "columbia-biology-ba": "Department of Biological Sciences",
    "columbia-computer-science-bs": "Department of Computer Science",
    "columbia-operations-research-bs": (
        "Department of Industrial Engineering and Operations Research"
    ),
    "columbia-mechanical-engineering-bs": "Department of Mechanical Engineering",
    "columbia-electrical-engineering-bs": "Department of Electrical Engineering",
    "columbia-applied-mathematics-bs": (
        "Department of Applied Physics and Applied Mathematics"
    ),
    "columbia-biomedical-engineering-bs": "Department of Biomedical Engineering",
    "columbia-computer-science-ms": "Department of Computer Science",
    "columbia-mba": "Columbia Business School",
    "columbia-jd": "Columbia Law School",
    "columbia-md": "Vagelos College of Physicians and Surgeons",
    "columbia-journalism-ms": "Columbia Journalism School",
    "columbia-sipa-mia": "School of International and Public Affairs",
    "columbia-sipa-mpa": "School of International and Public Affairs",
    "columbia-public-health-mph": "Mailman School of Public Health",
    "columbia-social-work-msw": "Columbia School of Social Work",
    "columbia-architecture-march": (
        "Graduate School of Architecture, Planning and Preservation"
    ),
    "columbia-arts-mfa": "Columbia School of the Arts",
    "columbia-nursing-msn": "Columbia School of Nursing",
}
for _p in PROGRAMS:
    if _p["slug"] in _EXPLICIT_DEPARTMENTS:
        _p["department"] = _EXPLICIT_DEPARTMENTS[_p["slug"]]

_EXISTING_SLUGS = {p["slug"] for p in PROGRAMS}
_EXISTING_CIP_KEYS = {(p.get("cip"), p["degree_type"]) for p in PROGRAMS if p.get("cip")}


def _delivery_format(raw: str) -> str:
    """Normalize IPEDS delivery labels to the platform's canonical values."""
    if raw == "in_person":
        return "on_campus"
    return raw


def _department_for(field_name: str, school: str) -> str:
    """Owning department — the CIP field title unless it duplicates the school name."""
    if field_name.lower() in school.lower() or school.lower() in field_name.lower():
        return school
    return field_name


def _build_catalog() -> list[dict]:
    """Append breadth-first program nodes from the College Scorecard Field-of-Study list."""
    out: list[dict] = []
    seen = set(_EXISTING_SLUGS)
    for slug, school, field_name, dtype, cip, dur, fmt, _legacy_desc in _IPEDS_CATALOG:
        if slug in seen:
            continue
        if (cip, dtype) in _EXISTING_CIP_KEYS:
            continue
        seen.add(slug)
        dept = _department_for(field_name, school)
        delivery = _delivery_format(fmt)
        pname = disambiguate_program_name(field_name, dtype)
        out.append({
            "slug": slug,
            "school": school,
            "program_name": pname,
            "degree_type": dtype,
            "department": dept,
            "cip": cip,
            "duration_months": dur,
            "delivery_format": delivery,
            "description": program_description(
                pname,
                dtype,
                school,
                dept,
                delivery_format=delivery,
                university_short="Columbia",
            ),
        })
    return out


PROGRAMS += _build_catalog()
_catalog_errors = validate_catalog(PROGRAMS)
if _catalog_errors:
    raise RuntimeError(f"Columbia catalog quality gate failed: {_catalog_errors}")
for _p in PROGRAMS:
    _p["delivery_format"] = _delivery_format(_p.get("delivery_format", "in_person"))

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

# Per-program graduate tuition, verified first-party (Columbia bulletin / school cost
# pages). Programs whose tuition is published only on bot-blocked pages and could not be
# confirmed first-party are omitted (recorded in _program_standard) rather than guessed:
# MBA, M.S. Journalism, MIA/MPA, MSW and MFA.
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
        "tuition_usd": 81000,
        "funded": False,
        "note": (
            "Columbia Engineering charges $2,700 per credit for M.S. students; the 30-point "
            "M.S. in Computer Science is shown as 30 × $2,700 = $81,000 in tuition (excludes "
            "fees)."
        ),
        "source": "Columbia Engineering — Graduate Tuition, Fees and Payments (bulletin)",
        "source_url": (
            "https://bulletin.columbia.edu/columbia-engineering/graduate-studies/"
            "graduate-tuition-fees-payments/"
        ),
        "year": "2025-26",
    },
    "columbia-jd": {
        "tuition_usd": 85368,
        "total_cost_of_attendance": 93757,
        "funded": False,
        "note": (
            "J.D. tuition; total university charges of $93,757 add the student activity, "
            "university-services, health-services fees and (waivable) student health "
            "insurance."
        ),
        "source": "Columbia Law School — J.D. and LL.M. Tuition and Fees",
        "source_url": (
            "https://www.law.columbia.edu/about/departments/financial-aid/"
            "jd-and-llm-tuition-and-fees"
        ),
        "year": "2025-26",
    },
    "columbia-architecture-march": {
        "tuition_usd": 70380,
        "funded": False,
        "note": (
            "GSAPP charges $35,190 per term (12-19 points); the figure shown is two terms = "
            "$70,380 per year, with coursework beyond the band billed at $2,346 per point."
        ),
        "source": "Columbia GSAPP — Tuition and Aid",
        "source_url": "https://www.arch.columbia.edu/admissions/tuition-aid",
        "year": "2025-26",
    },
    "columbia-public-health-mph": {
        "tuition_usd": 49888,
        "funded": False,
        "note": (
            "Full-time MPH flat-rate tuition across two semesters (the earliest year the "
            "official page publishes is 2026-27); program fees apply on top."
        ),
        "source": "Mailman School of Public Health — Tuition & Fees",
        "source_url": (
            "https://www.publichealth.columbia.edu/become-student/how-apply/financial-aid/"
            "tuition-fees"
        ),
        "year": "2026-27",
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


# Real Columbia campus photo (Butler Library) — Wikimedia Commons, CC BY-SA 4.0,
# hotlinkable landscape JPG (verified HTTP 200). Leads the institution hero.
_CAMPUS_PHOTO = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/"
    "Butler_Library_-_Columbia_University.jpg/"
    "1920px-Butler_Library_-_Columbia_University.jpg"
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
    # graduate programs carry tuition only where it was verified first-party. Programs
    # whose graduate tuition is published only on bot-blocked pages omit the figure.
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
