"""Canonical Yale University profile — the single source of truth.

Real, sourced data only (U.S. Dept. of Education College Scorecard, UNITID 130794 ·
NCES College Navigator / IPEDS · Yale's Office of Institutional Research Common Data
Set 2024-25 · the official "Yale Facts" page · Yale Investments Office / Yale News
(endowment) · the official QS / Times Higher Education / U.S. News rankings · each
school's official leadership / about page and the Yale University Catalog (tuition) ·
the Yale Office of Career Strategy First-Destination Report (Class of 2023) · the
College Scorecard Field-of-Study earnings by CIP). ``apply(session)`` idempotently
enriches the Yale institution row, upserts its real degree-granting schools, and builds
Yale's program catalog across them.

Yale's academic structure: Yale College (the undergraduate liberal-arts college,
chartered 1701, organized around 14 residential colleges) plus the Graduate School of
Arts and Sciences and a set of dean-led professional schools. We model the units that
own the degree programs in the canonical College Scorecard Field-of-Study list for
UNITID 130794 onto the platform's ``School`` model:
  - Yale College (undergraduate B.A./B.S. majors)
  - Yale School of Management (the MBA)
  - Yale School of the Environment (MEM / MESc)
  - Yale School of Public Health (MPH)
  - Yale School of Medicine (the Physician Associate program)
  - Yale School of Nursing (MSN)
  - Yale Divinity School (MDiv)
  - Yale School of Architecture (MArch)
  - Yale School of Art (MFA)
  - Yale School of Music (MM)

It **flushes but does not commit** — the caller (the Alembic data migration, the CLI
script, or the dev seed) owns the transaction. It is a **no-op** (returns ``False``)
when Yale is absent, so it is safe to run against a fresh or CI database. Re-running is
safe: schools key off ``(institution_id, name)`` and programs off ``slug``; stale rows
are reconciled without breaking foreign keys.

This mirrors ``mit_profile`` / ``princeton_profile`` so the migration, the standalone
script, and the dev seed all agree (DRY). Every figure traces to a public, citable
source; anything that could not be verified from a first-party or two-independent-source
basis is **omitted** (recorded in the relevant ``_standard.omitted`` list), never
guessed. Computer Science is the most-enriched flagship program (its real research
areas, faculty, class profile, and aggregated reviews), mirroring MIT Sloan's MBAn in
the reference instance — with the honest caveats that Yale's undergraduate testing
policy is test-flexible for fall-2026 entry (ACT, SAT, AP or IB) and becomes ACT/SAT
required for the fall-2027 cycle, that the canonical program set is the College
Scorecard Field-of-Study list for UNITID 130794 (two federal multi/interdisciplinary
CIP rows that cannot be mapped to a single named Yale degree are omitted, not guessed),
and that Yale does not publish a single official Nobel-laureate headline count (omitted).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Yale University"

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
# therefore honestly omitted rather than guessed.
_OMITTED_INSTITUTION = [
    # Yale does not publish a single canonical Nobel-laureate headline count on an
    # official page; aggregate third-party counts vary by counting method, so the figure
    # is omitted rather than asserting a number Yale itself does not state.
    "school_outcomes.flagship.nobel_laureates",
]

# ── Institution-level data ────────────────────────────────────────────────
# Rankings are stored as {rank, year} objects (the page renders any ranking_data entry
# that is an object with a numeric `rank`). All three ranks are quoted from the official
# ranking bodies for the 2026 editions.
RANKING_DATA: dict = {
    "ownership_type": "private",
    # Yale is accredited by the New England Commission of Higher Education (NECHE).
    "accreditor": "NECHE",
    # Carnegie basic classification (R1).
    "carnegie_classification": "Doctoral Universities: Very High Research Activity",
    # QS World University Rankings 2026: Yale is ranked #21 worldwide.
    "qs_world_university_rankings": {"rank": 21, "year": 2026},
    # THE World University Rankings 2026: #10 in the world.
    "times_higher_education": {"rank": 10, "year": 2026},
    # U.S. News Best Colleges (National Universities) 2026: #4 nationally.
    "us_news_national": {"rank": 4, "year": 2026},
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below is
# complete, so a shallow merge is correct. Figures are College Scorecard (UNITID 130794)
# cross-checked against Yale's Common Data Set 2024-25, NCES College Navigator (IPEDS),
# and Yale's official "Yale Facts" page where each publishes a metric.
SCHOOL_OUTCOMES: dict = {
    # CDS 2024-25: 2,227 admits / 57,517 first-year applicants = 3.87% (Scorecard 0.0387).
    "admit_rate": 0.0387,
    # College Scorecard average annual net price.
    "avg_net_price": 23777,
    # College Scorecard institution-wide median earnings 10 years after entry.
    "median_earnings_10yr": 100533,
    # College Scorecard four-year completion rate (150% of normal time).
    "completion_rate_4yr_150pct": 0.9574,
    # NCES College Navigator (IPEDS): first-year retention (Fall 2023 cohort) = 99%.
    "retention_rate_first_year": 0.99,
    # NCES College Navigator (IPEDS): six-year graduation rate (Fall 2018 cohort) = 96%.
    "graduation_rate_6yr": 0.96,
    "financial_aid": {
        # College Navigator (IPEDS): 22% of beginning undergraduates received a Pell
        # grant; 5% took federal student loans. Yale meets full need with no-loan aid.
        "pell_grant_rate": 0.22,
        "federal_loan_rate": 0.05,
        # College Scorecard average annual cost of attendance.
        "cost_of_attendance": 88300,
    },
    # Undergraduate race/ethnicity (Yale CDS 2024-25, cross-checked vs NCES College
    # Navigator / IPEDS Fall 2024; the two agree within rounding).
    "demographics": {
        "white": 0.31,
        "black": 0.09,
        "hispanic": 0.16,
        "asian": 0.22,
        "two_or_more": 0.07,
        "international": 0.11,
    },
    # SAT/ACT 25th-75th percentiles of enrolled first-years (Yale CDS 2024-25, item C9).
    "test_scores": {
        "sat_reading_25_75": [730, 780],
        "sat_math_25_75": [740, 790],
        "act_25_75": [33, 35],
    },
    # Yale main campus, New Haven, Connecticut.
    "location": {"lat": 41.31639, "lng": -72.92222},
    "campus_basics": {"location": "New Haven, Connecticut"},
    "scale": {
        # "Yale Facts": 5,842 faculty members (all ranks and schools).
        "faculty_count": 5842,
        # "Yale Facts": 5:1 student-faculty ratio (undergraduate).
        "student_faculty_ratio": "5:1",
        # Yale Investments Office / Yale News: endowment $44.1 billion at fiscal year-end
        # June 30, 2025 (FY2025, 11.1% net return).
        "endowment_usd": 44100000000,
    },
    # Yale Office of Career Strategy First-Destination Report, Class of 2023: among
    # graduates with confirmed plans six months after graduation, 73.6% employed and
    # 19.0% in graduate/professional school = 92.6% (90.3% knowledge rate; 6.0% of the
    # class still seeking).
    "employed_or_continuing_ed": 0.926,
    # Yale OCS Class of 2023 — employment by industry (industries with ≥10 respondents),
    # in rank order; the five largest categories.
    "top_employer_industries": [
        "Academia/Education",
        "Finance/Insurance/Real Estate",
        "Technology",
        "Consulting",
        "Healthcare/Pharmaceutical/Biotech/Global Health",
    ],
    "research": {
        "labs": [
            "Wright Laboratory (nuclear, particle & astrophysics; quantum sensing)",
            "Yale Cancer Center (NCI-designated comprehensive cancer center)",
            "Wu Tsai Institute (neuroscience & cognition)",
            "Yale Stem Cell Center",
            "Yale West Campus institutes (nanobiology, systems biology, quantitative biology)",
        ],
        "areas": [
            "Biomedical & health sciences",
            "Neuroscience & cognition",
            "Physical sciences & quantum",
            "Environment & forestry",
            "Economics & the social sciences",
            "Law, public policy & global affairs",
            "Humanities & the arts",
        ],
        "lab_links": {
            "Wright Laboratory (nuclear, particle & astrophysics; quantum sensing)": (
                "https://wlab.yale.edu/"
            ),
            "Yale Cancer Center (NCI-designated comprehensive cancer center)": (
                "https://medicine.yale.edu/cancer/"
            ),
            "Wu Tsai Institute (neuroscience & cognition)": "https://wti.yale.edu/",
        },
    },
    "campus_life": {
        # Yale's teams (the Bulldogs) compete in NCAA Division I (Ivy League).
        "athletics_division": "NCAA Division I (Ivy League)",
        "mascot": "Yale Bulldogs (Handsome Dan)",
        "housing": "Residential-college system (14 residential colleges)",
        "resources": [
            {"label": "Yale Bulldogs Athletics", "url": "https://yalebulldogs.com/"},
            {
                "label": "Yale Residential Colleges",
                "url": "https://yalecollege.yale.edu/residential-colleges",
            },
        ],
    },
    "flagship": {
        # "Yale Facts": 15,657 total students — 6,667 undergraduate + 8,990 graduate
        # and professional.
        "enrollment_total": 15657,
        # Common Data Set 2024-25 first-year admissions cycle (item C1).
        "applicants": 57517,
        "admits": 2227,
        "admissions_cycle": "Entering class fall 2024 (Yale Common Data Set 2024-25)",
        # Chartered in 1701 as the Collegiate School; renamed Yale College in 1718.
        "founded_year": 1701,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Yale, UNITID 130794)",
            "url": "https://collegescorecard.ed.gov/school/?130794",
        },
        {
            "label": "NCES College Navigator — Yale University (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=130794",
        },
        {
            "label": "Yale Office of Institutional Research — Common Data Set 2024-25",
            "url": "https://oir.yale.edu/sites/default/files/yale_cds_2024-25_rmd_20250612.pdf",
        },
        {
            "label": "Yale University — Yale Facts",
            "url": "https://www.yale.edu/about-yale/yale-facts",
        },
        {
            "label": "Yale reports investment return for fiscal 2025 (endowment $44.1B)",
            "url": "https://news.yale.edu/2025/10/24/yale-reports-investment-return-fiscal-2025",
        },
        {
            "label": "QS World University Rankings 2026 — Yale University",
            "url": "https://www.topuniversities.com/universities/yale-university",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — Yale University",
            "url": "https://www.timeshighereducation.com/world-university-rankings/yale-university",
        },
        {
            "label": "U.S. News Best Colleges 2026 — Yale University (#4 National Universities)",
            "url": "https://www.usnews.com/best-colleges/yale-university-1426",
        },
        {
            "label": "Yale Undergraduate Financial Aid — Affordability (no-loan, need-met)",
            "url": "https://finaid.yale.edu/affordability",
        },
        {
            "label": "Yale Office of Career Strategy — First-Destination Report, Class of 2023",
            "url": "https://cdn.ocs.yale.edu/wp-content/uploads/sites/77/2025/01/Final-Class-of-2023-Report-6-months.pdf",
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it "Undergraduates");
# the total (15,657) lives in flagship.enrollment_total and renders as "Total enrollment".
# 6,667 = "Yale Facts" undergraduate enrollment.
UNDERGRAD_COUNT = 6667

DESCRIPTION = (
    "Chartered in 1701 as the Collegiate School and renamed Yale College in 1718, Yale "
    "is a private Ivy League research university in New Haven, Connecticut — the "
    "third-oldest institution of higher education in the United States. It enrolls about "
    "6,700 undergraduates and roughly 9,000 graduate and professional students, some "
    "15,700 in all, and pairs a famously close undergraduate education — a 5:1 "
    "student-faculty ratio and 14 residential colleges — with the research depth of a "
    "major university and its 5,842 faculty.\n\n"
    "Yale College awards the B.A. and B.S. across roughly eighty majors, and the "
    "university is organized into the Graduate School of Arts and Sciences and a set of "
    "renowned professional schools — among them the School of Management, the School of "
    "Medicine, the Law School, the School of the Environment (the oldest in the country), "
    "the School of Architecture, the School of Art, the Divinity School, the School of "
    "Music (which is tuition-free), the School of Nursing, and the newly independent "
    "School of Public Health. Yale's research is anchored by Wright Laboratory, the "
    "NCI-designated Yale Cancer Center, and the Wu Tsai Institute for neuroscience.\n\n"
    "Yale ranks among the very best universities in the world: No. 4 among national "
    "universities by U.S. News, No. 10 in the world by Times Higher Education, and No. 21 "
    "by QS. It admits under 4% of first-year applicants and backs the largest endowment "
    "of any school but one — $44.1 billion as of June 2025.\n\n"
    "Yale is need-blind for all applicants (including international students) and meets "
    "100% of demonstrated financial need with grants, not loans: the average net price "
    "is about $24,000 a year, 22% of undergraduates receive Pell grants, and only 5% "
    "take federal student loans. Among the Class of 2023, 73.6% were employed and 19.0% "
    "had entered graduate or professional school within six months of graduation."
)

# ── The real degree-granting schools (display order) ───────────────────────
_COLLEGE = "Yale College"
_SOM = "Yale School of Management"
_YSE = "Yale School of the Environment"
_YSPH = "Yale School of Public Health"
_MED = "Yale School of Medicine"
_NURSING = "Yale School of Nursing"
_DIVINITY = "Yale Divinity School"
_ARCH = "Yale School of Architecture"
_ART = "Yale School of Art"
_MUSIC = "Yale School of Music"

SCHOOLS: list[dict] = [
    {
        "name": _COLLEGE,
        "sort_order": 1,
        "description": (
            "Yale College, chartered in 1701, is the university's undergraduate "
            "liberal-arts college. Organized around fourteen residential colleges, it "
            "awards the B.A. and B.S. across roughly eighty majors and is the historic "
            "core of the university. Its computer science, engineering and applied-science "
            "degrees are offered through Yale's Faculty of Engineering and Applied Science."
        ),
    },
    {
        "name": _SOM,
        "sort_order": 2,
        "description": (
            "Founded in 1976, the Yale School of Management educates leaders for business "
            "and society. It awards the MBA, the MBA for Executives, specialized master's "
            "degrees and the Ph.D., and is known for its integrated, multidisciplinary "
            "curriculum taught across the wider university."
        ),
    },
    {
        "name": _YSE,
        "sort_order": 3,
        "description": (
            "The Yale School of the Environment, founded in 1900, is the oldest graduate "
            "environment and forestry school in the United States. It awards the Master of "
            "Environmental Management, the Master of Environmental Science, the Master of "
            "Forestry and doctoral degrees across environmental management, science and "
            "policy."
        ),
    },
    {
        "name": _YSPH,
        "sort_order": 4,
        "description": (
            "Founded in 1915 and an independent, self-supporting school of the university "
            "since 2024, the Yale School of Public Health awards the accredited MPH, the "
            "M.S. and the Ph.D. across biostatistics, epidemiology, environmental health "
            "and health policy and management."
        ),
    },
    {
        "name": _MED,
        "sort_order": 5,
        "description": (
            "Chartered in 1810, the Yale School of Medicine is known for the 'Yale System' "
            "of self-directed, non-graded preclinical study. Alongside the M.D. and "
            "M.D.-Ph.D., it educates physician associates in a graduate Physician Associate "
            "Program awarding the M.M.Sc."
        ),
    },
    {
        "name": _NURSING,
        "sort_order": 6,
        "description": (
            "Established in 1923 as the first university-based school to educate nurses on "
            "an educational rather than apprenticeship model, the Yale School of Nursing "
            "awards the Master of Science in Nursing, the Doctor of Nursing Practice and "
            "the Ph.D. across advanced-practice specialties."
        ),
    },
    {
        "name": _DIVINITY,
        "sort_order": 7,
        "description": (
            "The Yale Divinity School, established in 1822, is an ecumenical graduate "
            "school of theology awarding the Master of Divinity, the Master of Arts in "
            "Religion and the Master of Sacred Theology, with the affiliated Berkeley "
            "Divinity School and the Institute of Sacred Music on its quadrangle."
        ),
    },
    {
        "name": _ARCH,
        "sort_order": 8,
        "description": (
            "The Yale School of Architecture, with roots in a 1916 program, awards the "
            "Master of Architecture (I and II), the Master of Environmental Design and the "
            "Ph.D. It is distinguished by the Jim Vlock First Year Building Project, a "
            "design-build requirement for every first-year M.Arch I student."
        ),
    },
    {
        "name": _ART,
        "sort_order": 9,
        "description": (
            "Opened in 1869 as the first art school connected to a U.S. university, the "
            "Yale School of Art awards the Master of Fine Arts — its only degree — in four "
            "areas: graphic design, painting/printmaking, photography and sculpture."
        ),
    },
    {
        "name": _MUSIC,
        "sort_order": 10,
        "description": (
            "The Yale School of Music, which conferred its first degrees in 1894, is a "
            "graduate, fully tuition-free professional music school awarding the M.M., "
            "M.M.A., D.M.A., Artist Diploma and Certificate in Performance — one of the few "
            "conservatory-level schools embedded in a research university."
        ),
    },
]

# Each school's official website (verified to resolve at author time).
_SCHOOL_WEBSITE: dict[str, str] = {
    _COLLEGE: "https://college.yale.edu/",
    _SOM: "https://som.yale.edu/",
    _YSE: "https://environment.yale.edu/",
    _YSPH: "https://ysph.yale.edu/",
    _MED: "https://medicine.yale.edu/",
    _NURSING: "https://nursing.yale.edu/",
    _DIVINITY: "https://divinity.yale.edu/",
    _ARCH: "https://www.architecture.yale.edu/",
    _ART: "https://www.art.yale.edu/",
    _MUSIC: "https://music.yale.edu/",
}

# Rich, sourced About-tab content per school. Deans + titles are quoted from each
# school's official leadership page (verified 2026-06-10). Founding years come from each
# school's official history/about page. Notable-faculty rosters are not published
# uniformly per school and are omitted rather than hand-picked (recorded in _ABOUT_OMITTED).
_ABOUT_DETAIL: dict[str, dict] = {
    _COLLEGE: {
        "founded": 1701,
        "leadership": (
            "Pericles Lewis — Dean of Yale College (Douglas Tracy Smith Professor of "
            "Comparative Literature and Professor of English)"
        ),
        "research_centers": [
            "Fourteen residential colleges",
            "Center for Teaching and Learning",
            "Science & Quantitative Reasoning Education",
        ],
        "source": {
            "label": "Yale College — Office of the Dean (Leadership)",
            "url": (
                "https://college.yale.edu/get-to-know-yale-college/office-of-the-dean/"
                "yale-college-leadership"
            ),
        },
    },
    _SOM: {
        "founded": 1976,
        "leadership": (
            "Kerwin K. Charles — Indra K. Nooyi Dean and Frederick W. Beinecke Professor "
            "of Economics, Policy, and Management"
        ),
        "research_centers": [
            "International Center for Finance",
            "Chief Executive Leadership Institute",
            "Program on Social Enterprise, Innovation, and Impact",
        ],
        "source": {
            "label": "Yale SOM — Dean's Leadership Team",
            "url": "https://som.yale.edu/about/school-leadership-boards/deans-leadership-team",
        },
    },
    _YSE: {
        "founded": 1900,
        "leadership": (
            "Indy Burke — Carl W. Knobloch, Jr. Dean and Professor of Ecosystem Ecology"
        ),
        "research_centers": [
            "The Forest School at the Yale School of the Environment",
            "Yale Center for Environmental Justice",
            "Yale Center for Business and the Environment",
        ],
        "source": {
            "label": "Yale School of the Environment — Leadership Team",
            "url": "https://environment.yale.edu/about/leadership-team",
        },
    },
    _YSPH: {
        "founded": 1915,
        "leadership": (
            "Megan L. Ranney — Dean and C.-E. A. Winslow Professor of Public Health"
        ),
        "research_centers": [
            "Center for Methods in Implementation and Prevention Science",
            "Yale Center for Perinatal, Pediatric and Environmental Epidemiology",
            "Public Health Modeling Unit",
        ],
        "source": {
            "label": "Yale School of Public Health — Dean's Office",
            "url": "https://ysph.yale.edu/about-school-of-public-health/deans-office/",
        },
    },
    _MED: {
        "founded": 1810,
        "leadership": (
            "Nancy J. Brown — Jean and David W. Wallace Dean of the Yale School of "
            "Medicine and C.N.H. Long Professor of Internal Medicine"
        ),
        "research_centers": [
            "Yale Cancer Center",
            "Yale Stem Cell Center",
            "Yale Child Study Center",
        ],
        "source": {
            "label": "Yale School of Medicine — Leadership",
            "url": "https://medicine.yale.edu/about/leadership-administration/ysm-dean-deputy-deans/",
        },
    },
    _NURSING: {
        "founded": 1923,
        "leadership": (
            "Azita Emami — Dean and Linda Koch Lorimer Professor of Nursing"
        ),
        "source": {
            "label": "Yale School of Nursing — Office of the Dean",
            "url": "https://nursing.yale.edu/faculty/office-dean",
        },
    },
    _DIVINITY: {
        "founded": 1822,
        "leadership": (
            "Gregory E. Sterling — The Reverend Henry L. Slack Dean of Yale Divinity "
            "School and Lillian Claus Professor of New Testament"
        ),
        "research_centers": [
            "Yale Institute of Sacred Music",
            "Berkeley Divinity School at Yale",
            "Andover Newton Seminary at Yale",
        ],
        "source": {
            "label": "Yale Divinity School — Dean's Office",
            "url": "https://divinity.yale.edu/about/deans-office",
        },
    },
    _ARCH: {
        "founded": 1916,
        "leadership": (
            "Deborah Berke — Edward P. Bass Dean of the Yale School of Architecture"
        ),
        "research_centers": [
            "Jim Vlock First Year Building Project",
            "Yale Center for Ecosystems in Architecture",
        ],
        "source": {
            "label": "Yale School of Architecture — leadership (provost announcement)",
            "url": "https://provost.yale.edu/news/deborah-berke-reappointed-dean-yale-school-architecture",
        },
    },
    _ART: {
        "founded": 1869,
        "leadership": (
            "Kymberly Pinder — Stavros Niarchos Foundation Dean of the Yale School of Art"
        ),
        "research_centers": [
            "Green Hall galleries",
            "32 Edgewood Avenue Gallery",
        ],
        "source": {
            "label": "Yale School of Art — history",
            "url": "https://www.art.yale.edu/about/history",
        },
    },
    _MUSIC: {
        "founded": 1894,
        "leadership": (
            "José García-León — Henry and Lucy Moses Dean of Music"
        ),
        "research_centers": [
            "Yale Opera",
            "Oneppo Chamber Music Series",
            "Yale Collection of Musical Instruments",
        ],
        "source": {
            "label": "Yale School of Music — About",
            "url": "https://music.yale.edu/about",
        },
    },
}

# About-detail fields omitted per school (verified-unavailable), recorded in each
# school's _standard.omitted. Notable-faculty rosters are omitted for every school; the
# School of Nursing additionally omits a distinct school-owned research center (only
# global-health affiliations could be verified).
_FACULTY_OMIT = ["about_detail.faculty"]
_ABOUT_OMITTED: dict[str, list[str]] = {
    _COLLEGE: list(_FACULTY_OMIT),
    _SOM: list(_FACULTY_OMIT),
    _YSE: list(_FACULTY_OMIT),
    _YSPH: list(_FACULTY_OMIT),
    _MED: list(_FACULTY_OMIT),
    _NURSING: [*_FACULTY_OMIT, "about_detail.research_centers"],
    _DIVINITY: list(_FACULTY_OMIT),
    _ARCH: list(_FACULTY_OMIT),
    _ART: list(_FACULTY_OMIT),
    _MUSIC: list(_FACULTY_OMIT),
}

# ── Channel feeds + official social links ──────────────────────────────────
# Institution-wide socials (official Yale handles) + news page.
_INSTITUTION_CONTENT: dict = {
    "news_url": "https://news.yale.edu",
    "social": {
        "instagram": "https://www.instagram.com/yale/",
        "linkedin": "https://www.linkedin.com/school/yale-university/",
        "x": "https://x.com/yale",
        "youtube": "https://www.youtube.com/user/YaleUniversity",
        "facebook": "https://www.facebook.com/YaleUniversity",
    },
}

# Computer Science keyword-relevant feed (the flagship program), inheriting the
# institution socials (the department surfaces its news through Yale Engineering).
_CS_CONTENT: dict = {
    "news_url": "https://news.yale.edu/topics/science-technology",
    "keywords": ["computer science", "yale cs", "machine learning", "yale engineering"],
    "social": _INSTITUTION_CONTENT["social"],
}

# ── The program catalog (real majors/degrees, organized by school) ─────────
# slug = idempotency key. Every program is mapped to its owning school from Yale's
# official structure. The program set is the College Scorecard Field-of-Study list for
# UNITID 130794 (the deterministic federal view); two federal multi/interdisciplinary
# CIP rows (30.99 "Multi/Interdisciplinary Studies, Other" and 51.07 "Health and Medical
# Administrative Services") that cannot be mapped to a single named Yale degree are
# omitted rather than guessed. Graduate degrees use the generic ``masters`` type with the
# real degree name carried in the program name.
PROGRAMS: list[dict] = [
    # ── Yale College (undergraduate B.A./B.S. majors) ──
    {
        "slug": "yale-economics-bs",
        "school": _COLLEGE,
        "program_name": "Economics",
        "degree_type": "bachelors",
        "cip": "45.06",
        "duration_months": 48,
        "description": "Economics — micro, macro, econometrics and economic history.",
    },
    {
        "slug": "yale-computer-science-bs",
        "school": _COLLEGE,
        "program_name": "Computer Science",
        "degree_type": "bachelors",
        "cip": "11.01",
        "duration_months": 48,
        "description": (
            "Yale's flagship computing major — offered as both the B.S. and the B.A., with "
            "four combined majors, spanning theory, systems, AI and machine learning, "
            "taught through Yale's Faculty of Engineering and Applied Science."
        ),
    },
    {
        "slug": "yale-political-science-bs",
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
        "slug": "yale-history-bs",
        "school": _COLLEGE,
        "program_name": "History",
        "degree_type": "bachelors",
        "cip": "54.01",
        "duration_months": 48,
        "description": "History — the study of the human past across periods and regions.",
    },
    {
        "slug": "yale-mcdb-bs",
        "school": _COLLEGE,
        "program_name": "Molecular, Cellular, and Developmental Biology",
        "degree_type": "bachelors",
        "cip": "26.04",
        "duration_months": 48,
        "description": (
            "Molecular, cellular and developmental biology — genetics, cell biology and "
            "the molecular basis of development."
        ),
    },
    {
        "slug": "yale-psychology-bs",
        "school": _COLLEGE,
        "program_name": "Psychology",
        "degree_type": "bachelors",
        "cip": "42.27",
        "duration_months": 48,
        "description": "Psychology — cognitive, developmental, social and clinical science.",
    },
    {
        "slug": "yale-global-affairs-bs",
        "school": _COLLEGE,
        "program_name": "Global Affairs",
        "degree_type": "bachelors",
        "cip": "45.09",
        "duration_months": 48,
        "description": (
            "Global affairs — interdisciplinary study of international policy, security "
            "and development, anchored by the Jackson School of Global Affairs."
        ),
    },
    {
        "slug": "yale-english-bs",
        "school": _COLLEGE,
        "program_name": "English",
        "degree_type": "bachelors",
        "cip": "23.01",
        "duration_months": 48,
        "description": "English — literature in English, criticism and creative writing.",
    },
    {
        "slug": "yale-statistics-bs",
        "school": _COLLEGE,
        "program_name": "Statistics and Data Science",
        "degree_type": "bachelors",
        "cip": "27.05",
        "duration_months": 48,
        "description": (
            "Statistics and data science — probability, statistical inference and "
            "data-driven computation."
        ),
    },
    {
        "slug": "yale-mathematics-bs",
        "school": _COLLEGE,
        "program_name": "Mathematics",
        "degree_type": "bachelors",
        "cip": "27.01",
        "duration_months": 48,
        "description": "Mathematics — analysis, algebra, geometry and number theory.",
    },
    # ── Yale School of Management ──
    {
        "slug": "yale-mba",
        "school": _SOM,
        "program_name": "Master of Business Administration (MBA)",
        "degree_type": "masters",
        "cip": "52.02",
        "duration_months": 24,
        "description": (
            "The full-time, two-year MBA — an integrated, multidisciplinary core that "
            "educates leaders for business and society."
        ),
    },
    # ── Yale School of the Environment ──
    {
        "slug": "yale-environmental-management-mem",
        "school": _YSE,
        "program_name": "Master of Environmental Management (MEM)",
        "degree_type": "masters",
        "cip": "03.01",
        "duration_months": 24,
        "description": (
            "The two-year Master of Environmental Management — environmental policy, "
            "management and science for environmental leadership."
        ),
    },
    {
        "slug": "yale-environmental-science-mesc",
        "school": _YSE,
        "program_name": "Master of Environmental Science (MESc)",
        "degree_type": "masters",
        "cip": "26.13",
        "duration_months": 24,
        "description": (
            "The two-year, research-oriented Master of Environmental Science — ecology, "
            "ecosystems and environmental science."
        ),
    },
    # ── Yale School of Public Health ──
    {
        "slug": "yale-public-health-mph",
        "school": _YSPH,
        "program_name": "Master of Public Health (MPH)",
        "degree_type": "masters",
        "cip": "51.22",
        "duration_months": 24,
        "description": (
            "The accredited Master of Public Health — biostatistics, epidemiology, "
            "environmental health and health policy and management."
        ),
    },
    # ── Yale School of Medicine ──
    {
        "slug": "yale-physician-associate-mmsc",
        "school": _MED,
        "program_name": "Physician Associate Program (MMSc)",
        "degree_type": "masters",
        "cip": "51.09",
        "duration_months": 28,
        "description": (
            "The Yale Physician Associate Program — a graduate program awarding the Master "
            "of Medical Science and preparing physician associates for clinical practice."
        ),
    },
    # ── Yale School of Nursing ──
    {
        "slug": "yale-nursing-msn",
        "school": _NURSING,
        "program_name": "Master of Science in Nursing (MSN)",
        "degree_type": "masters",
        "cip": "51.38",
        "duration_months": 24,
        "description": (
            "The Master of Science in Nursing — advanced-practice nursing specialties "
            "preparing nurse practitioners and nurse-midwives."
        ),
    },
    # ── Yale Divinity School ──
    {
        "slug": "yale-divinity-mdiv",
        "school": _DIVINITY,
        "program_name": "Master of Divinity (MDiv)",
        "degree_type": "masters",
        "cip": "39.06",
        "duration_months": 36,
        "description": (
            "The three-year Master of Divinity — Yale Divinity School's professional "
            "degree in theological and ministerial studies."
        ),
    },
    # ── Yale School of Architecture ──
    {
        "slug": "yale-architecture-march",
        "school": _ARCH,
        "program_name": "Master of Architecture (MArch I)",
        "degree_type": "masters",
        "cip": "04.09",
        "duration_months": 36,
        "description": (
            "The three-year professional Master of Architecture (MArch I), including the "
            "Jim Vlock First Year Building Project required of every first-year student."
        ),
    },
    # ── Yale School of Art ──
    {
        "slug": "yale-art-mfa",
        "school": _ART,
        "program_name": "Master of Fine Arts (MFA)",
        "degree_type": "masters",
        "cip": "50.07",
        "duration_months": 24,
        "description": (
            "The two-year Master of Fine Arts — Yale's only art degree, in graphic design, "
            "painting/printmaking, photography or sculpture."
        ),
    },
    # ── Yale School of Music ──
    {
        "slug": "yale-music-mm",
        "school": _MUSIC,
        "program_name": "Master of Music (MM)",
        "degree_type": "masters",
        "cip": "50.09",
        "duration_months": 24,
        "description": (
            "The Master of Music — a tuition-free, conservatory-level performance and "
            "composition degree embedded in a research university."
        ),
    },
]

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

# Full official program names (program-page title); equal to the program name here.
_FULL_NAME_BY_SLUG: dict[str, str] = {p["slug"]: p["program_name"] for p in PROGRAMS}

# Official program/department/school home pages.
_WEBSITE_BY_SLUG: dict[str, str] = {
    "yale-economics-bs": "https://economics.yale.edu/",
    "yale-computer-science-bs": "https://cpsc.yale.edu/",
    "yale-political-science-bs": "https://politicalscience.yale.edu/",
    "yale-history-bs": "https://history.yale.edu/",
    "yale-mcdb-bs": "https://mcdb.yale.edu/",
    "yale-psychology-bs": "https://psychology.yale.edu/",
    "yale-global-affairs-bs": "https://jackson.yale.edu/academics/undergraduate-major/",
    "yale-english-bs": "https://english.yale.edu/",
    "yale-statistics-bs": "https://statistics.yale.edu/",
    "yale-mathematics-bs": "https://math.yale.edu/",
    "yale-mba": "https://som.yale.edu/programs/mba",
    "yale-environmental-management-mem": "https://environment.yale.edu/academics/degrees/master-environmental-management",
    "yale-environmental-science-mesc": "https://environment.yale.edu/academics/degrees/master-environmental-science",
    "yale-public-health-mph": "https://ysph.yale.edu/academics/degrees-programs/",
    "yale-physician-associate-mmsc": "https://medicine.yale.edu/pa/",
    "yale-nursing-msn": "https://nursing.yale.edu/academics/msn",
    "yale-divinity-mdiv": "https://divinity.yale.edu/academics/degree-programs/master-divinity-mdiv",
    "yale-architecture-march": "https://www.architecture.yale.edu/academics/programs/1-m-arch-i",
    "yale-art-mfa": "https://www.art.yale.edu/",
    "yale-music-mm": "https://music.yale.edu/academics",
}

# ── Who-it's-for + highlights (catalog baselines) ──────────────────────────
_WHO_BASELINE = (
    "Academically exceptional students seeking a research-rich education at a university "
    "with a famously close undergraduate college, full-need financial aid met without "
    "loans, and the depth of a major research university."
)
_HL_BASELINE = ["Ivy League", "5:1 student-faculty ratio", "Need-met, no-loan aid"]
_WHO_GRAD_BASELINE = (
    "Graduate and professional students seeking a top-ranked Yale degree with the "
    "resources of a major research university and an internationally recognized faculty."
)
_HL_GRAD_BASELINE = ["Top-ranked Yale graduate degree", "World-class faculty", "Ivy League"]

_WHO_BY_SLUG = {
    "yale-computer-science-bs": (
        "Technically strong students who want a rigorous computer science education — "
        "offered as the B.S. or the B.A., with four combined majors — inside Yale's "
        "liberal-arts college."
    ),
    "yale-mba": (
        "Aspiring leaders seeking an integrated, multidisciplinary two-year MBA that "
        "bridges business and the broader university and society."
    ),
    "yale-music-mm": (
        "Conservatory-level musicians seeking a tuition-free graduate performance or "
        "composition degree within a research university."
    ),
}
_HL_BY_SLUG = {
    "yale-computer-science-bs": [
        "B.S. & B.A. tracks",
        "16 research areas",
        "Sterling Professor on faculty",
    ],
    "yale-mba": [
        "Integrated core curriculum",
        "Two-year full-time MBA",
        "Business and society mission",
    ],
    "yale-music-mm": [
        "Full-tuition award for all",
        "Conservatory in a university",
        "Yale Opera & chamber series",
    ],
}

# ── Curriculum / research areas, where published (the flagship) ────────────
# Yale CS publishes 16 official research areas; quoted from the department's official
# Research Areas page (Yale Engineering).
_TRACKS_BY_SLUG: dict[str, dict] = {
    "yale-computer-science-bs": {
        "label": "Computer science research areas",
        "note": (
            "Computer science is offered as both the B.S. (12 term courses) and the B.A. "
            "(10 term courses), plus four combined majors (with electrical engineering, "
            "economics, mathematics or psychology). Upper-level coursework spans the "
            "department's sixteen official research areas."
        ),
        "items": [
            {"name": "Algorithms & Complexity Theory"},
            {"name": "Artificial Intelligence & Machine Learning"},
            {"name": "Computer Architecture"},
            {"name": "Computer Graphics"},
            {"name": "Computer Music"},
            {"name": "Computer Networks"},
            {"name": "Database Systems"},
            {"name": "Distributed Computing"},
            {"name": "Natural Language Processing"},
            {"name": "Operating Systems"},
            {"name": "Programming Languages & Compilers"},
            {"name": "Quantum Computing"},
            {"name": "Social Robotics"},
            {"name": "Scientific Computing & Applied Math"},
            {"name": "Security & Cryptography"},
            {"name": "Societal & Humanistic Aspects of Computation"},
        ],
        "source": "Yale Engineering — Computer Science Research Areas",
        "source_url": (
            "https://engineering.yale.edu/academic-study/departments/computer-science/"
            "research-areas"
        ),
    },
}

# ── Program-specific cost ──────────────────────────────────────────────────
# Yale College undergraduate cost: tuition is the official 2024-25 figure; cost of
# attendance and average net price are College Scorecard (UNITID 130794).
_TUITION_UG = 67250
_UNDERGRAD_COA = 88300
_AVG_NET_PRICE = 23777

# Per-program graduate tuition (Yale University Catalog / school financial-aid pages,
# academic year 2025-26 unless noted). Music is fully tuition-free.
_COST_BY_SLUG: dict[str, dict] = {
    "yale-mba": {
        "tuition_usd": 87800,
        "total_cost_of_attendance": 123936,
        "funded": False,
        "note": (
            "Full-time MBA tuition plus a $500 program fee; estimated single-student "
            "budget shown as total cost of attendance."
        ),
        "source": "Yale University Catalog — School of Management, Tuition & Fees",
        "source_url": "https://catalog.yale.edu/management/tuition-fees/",
        "year": "2025-26",
    },
    "yale-environmental-management-mem": {
        "tuition_usd": 53550,
        "funded": False,
        "note": "Master's-program tuition (applies to the M.E.M., M.E.Sc., M.F. and M.F.S.).",
        "source": "Yale University Catalog — School of the Environment, Tuition",
        "source_url": (
            "https://catalog.yale.edu/environment/tuition-fees-other-expenses/"
            "masters-program-tuition-fees/"
        ),
        "year": "2025-26",
    },
    "yale-environmental-science-mesc": {
        "tuition_usd": 53550,
        "funded": False,
        "note": "Master's-program tuition (applies to the M.E.M., M.E.Sc., M.F. and M.F.S.).",
        "source": "Yale University Catalog — School of the Environment, Tuition",
        "source_url": (
            "https://catalog.yale.edu/environment/tuition-fees-other-expenses/"
            "masters-program-tuition-fees/"
        ),
        "year": "2025-26",
    },
    "yale-public-health-mph": {
        "tuition_usd": 55320,
        "funded": False,
        "note": "Full-time MPH tuition for the nine-month academic year.",
        "source": "Yale University Catalog — School of Public Health, Tuition & Expenses",
        "source_url": "https://catalog.yale.edu/ysph/tuition-expenses-financial-aid/",
        "year": "2025-26",
    },
    "yale-physician-associate-mmsc": {
        "tuition_usd": 52314,
        "total_cost_of_attendance": 97576,
        "funded": False,
        "note": "First-year (PA1) tuition; total first-year student budget shown.",
        "source": "Yale School of Medicine — Physician Associate Program, Student Budget",
        "source_url": "https://medicine.yale.edu/pa/tuition-financial-aid/student-budget/",
        "year": "2025-26",
    },
    "yale-nursing-msn": {
        "tuition_usd": 51748,
        "funded": False,
        "note": "Full-time MSN tuition ($25,874 per term).",
        "source": "Yale School of Nursing — Tuition and Fees",
        "source_url": "https://nursing.yale.edu/admissions-aid/financial-aid/tuition-and-fees",
        "year": "2025-26",
    },
    "yale-divinity-mdiv": {
        "tuition_usd": 30576,
        "funded": False,
        "note": (
            "Tuition at three-quarter-time or more. Yale Divinity School offers "
            "full-tuition scholarships to all students with demonstrated need."
        ),
        "source": "Yale University Catalog — Divinity School, Tuition & Fees",
        "source_url": "https://catalog.yale.edu/div/educational-expenses-financial-aid/tuition-fees/",
        "year": "2025-26",
    },
    "yale-architecture-march": {
        "tuition_usd": 64400,
        "total_cost_of_attendance": 92997,
        "funded": False,
        "note": "M.Arch tuition; estimated total cost for a single off-campus student shown.",
        "source": "Yale University Catalog — School of Architecture, Tuition",
        "source_url": "https://catalog.yale.edu/architecture/tuition/",
        "year": "2025-26",
    },
    "yale-art-mfa": {
        "tuition_usd": 48500,
        "funded": False,
        "note": "Full-time MFA tuition.",
        "source": "Yale University Catalog — School of Art, Tuition",
        "source_url": "https://catalog.yale.edu/art/tuition-fees/tuition/",
        "year": "2025-26",
    },
    "yale-music-mm": {
        "tuition_usd": 0,
        "total_cost_of_attendance": 0,
        "funded": True,
        "note": (
            "The Yale School of Music is tuition-free: every admitted student receives a "
            "full-tuition award and fellowship. Students still pay living costs, fees and "
            "insurance."
        ),
        "source": "Yale School of Music — Financial Aid",
        "source_url": "https://music.yale.edu/financial-aid",
        "year": "2025-26",
    },
}

# ── Program-specific outcomes (College Scorecard Field of Study, by CIP) ────
# Where the federal College Scorecard publishes a Field-of-Study median earnings (one
# year after completion) for an awarded CIP at UNITID 130794, we use it (program scope).
# Programs whose CIP earnings are suppressed fall back to the institution 10-year median.
# Tuples are (median_earnings_1yr, cip).
_FOS_OUTCOMES: dict[str, tuple[int, str]] = {
    "yale-economics-bs": (82617, "45.06"),
    "yale-computer-science-bs": (133293, "11.01"),
    "yale-political-science-bs": (57466, "45.10"),
    "yale-history-bs": (54700, "54.01"),
    "yale-mcdb-bs": (40299, "26.04"),
    "yale-psychology-bs": (47874, "42.27"),
    "yale-english-bs": (41045, "23.01"),
    "yale-mba": (192686, "52.02"),
    "yale-environmental-management-mem": (75985, "03.01"),
    "yale-environmental-science-mesc": (58008, "26.13"),
    "yale-public-health-mph": (72627, "51.22"),
    "yale-physician-associate-mmsc": (124979, "51.09"),
    "yale-nursing-msn": (113472, "51.38"),
    "yale-divinity-mdiv": (45451, "39.06"),
    "yale-architecture-march": (65244, "04.09"),
    "yale-art-mfa": (24521, "50.07"),
    "yale-music-mm": (21250, "50.09"),
}

# Verbatim methodology for the program-scope Scorecard FOS earnings figure.
_FOS_CONDITIONS = (
    "Median earnings of graduates who received federal financial aid, measured "
    "approximately one year after program completion; reported by the U.S. Department of "
    "Education College Scorecard Field of Study by 4-digit CIP code. Programs with too "
    "few completers are suppressed."
)

# Institution-wide outcomes fallback (College Scorecard, UNITID 130794), used for degree
# programs whose program-level one-year earnings are suppressed (Global Affairs,
# Statistics and Data Science, Mathematics).
_OUTCOMES_INSTITUTION = {
    "median_salary": 100533,
    "scope": "institution",
    "conditions": (
        "Yale institution-wide median earnings ten years after entry (College Scorecard, "
        "UNITID 130794); a program-level one-year earnings figure is not published "
        "(suppressed) for this field of study."
    ),
    "source": "U.S. Dept. of Education College Scorecard (UNITID 130794)",
    "source_url": "https://collegescorecard.ed.gov/school/?130794",
}

# Annual degrees conferred per CIP (College Scorecard Field of Study), used for the
# flagship class-profile cohort figure.
_AWARDS_BY_SLUG: dict[str, int] = {"yale-computer-science-bs": 164}

# ── Class profile, where published (the flagship) ──────────────────────────
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    "yale-computer-science-bs": {
        "cohort_size": (
            "≈164 computer science bachelor's degrees awarded annually (one of Yale "
            "College's most popular majors)"
        ),
        "note": (
            "Yale does not publish a per-major entering-cohort size; the figure is the "
            "annual count of computer science bachelor's degrees awarded (College "
            "Scorecard Field of Study, CIP 11.01)."
        ),
        "source": "U.S. Dept. of Education College Scorecard — Field of Study (CIP 11.01)",
        "source_url": "https://collegescorecard.ed.gov/school/?130794",
    },
}

# ── Faculty (lead + directory link), where confidently sourced (the flagship) ──
_FACULTY_BY_SLUG: dict[str, dict] = {
    "yale-computer-science-bs": {
        "lead": [
            {
                "name": "Daniel A. Spielman",
                "title": (
                    "Sterling Professor of Computer Science (Yale's highest faculty "
                    "honor); algorithms, spectral graph theory and network science"
                ),
            },
            {
                "name": "Zhong Shao",
                "title": (
                    "Thomas L. Kempner Professor of Computer Science and Chair of the "
                    "Department of Computer Science; programming languages and formal methods"
                ),
            },
        ],
        "note": (
            "Yale Computer Science faculty include a Sterling Professor (Daniel Spielman); "
            "the department is chaired by Zhong Shao."
        ),
        "directory_url": "https://cpsc.yale.edu/people/faculty",
    },
}

# ── Aggregated, cited student-review themes (≥2 third-party sources, the flagship) ──
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "yale-computer-science-bs": {
        "summary": (
            "Students and third-party guides describe the Yale undergraduate experience "
            "as academically excellent with small classes and unusually invested "
            "professors, a strong residential-college community, and good research and "
            "career support; computer science is among Yale's most popular majors with "
            "strong industry and graduate placement. Common cautions are that STEM "
            "teaching quality can be uneven across departments and that Yale's CS, while "
            "strong, is regarded a notch below the very top CS-flagship schools."
        ),
        "themes": [
            {
                "label": "Academic strength & small classes",
                "sentiment": "positive",
                "detail": "Small classes and professors invested in undergraduate teaching.",
            },
            {
                "label": "Residential-college community",
                "sentiment": "positive",
                "detail": "A supportive residential-college system anchors student life.",
            },
            {
                "label": "Research & career support",
                "sentiment": "positive",
                "detail": "Strong undergraduate research access and career advising.",
            },
            {
                "label": "Uneven STEM teaching",
                "sentiment": "caution",
                "detail": "Reviewers note STEM teaching quality can vary by department.",
            },
            {
                "label": "Not a top CS-flagship",
                "sentiment": "caution",
                "detail": "Yale CS is strong but ranked below the very top CS schools.",
            },
        ],
        "sources": [
            {
                "label": "Niche — Yale University",
                "url": "https://www.niche.com/colleges/yale-university/",
            },
            {
                "label": "U.S. News — Yale University",
                "url": "https://www.usnews.com/best-colleges/yale-university-1426",
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
# Undergraduate (Yale College) admission via the Common Application, Coalition (Scoir)
# or QuestBridge. Yale is test-flexible for fall-2026 entry (ACT, SAT, AP or IB) and
# becomes ACT/SAT required for the fall-2027 admission cycle.
_REQ_UNDERGRAD = {
    "materials": [
        {
            "name": "Common Application, Coalition Application (Scoir) or QuestBridge",
            "required": True,
        },
        {"name": "Yale-specific writing supplement", "required": True},
        {"name": "School report + secondary-school transcript", "required": True},
        {"name": "Counselor recommendation", "required": True},
        {"name": "Two teacher recommendations", "required": True},
        {"name": "$80 application fee; need-based fee waivers available", "required": True},
        {
            "name": "Standardized test scores",
            "required": True,
            "note": (
                "Test-flexible for fall-2026 entry — ACT, SAT, AP or IB scores accepted; "
                "the ACT or SAT becomes required starting the 2026-27 cycle (fall-2027 "
                "entry), when AP/IB no longer satisfy the requirement."
            ),
        },
    ],
    "deadlines": [
        {"round": "Single-Choice Early Action", "date": "November 1"},
        {"round": "Regular Decision", "date": "January 2"},
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
            {"label": "Yale Admissions — Apply", "url": "https://admissions.yale.edu/apply"}
        ],
    },
    "source": "Yale Undergraduate Admissions",
    "source_url": "https://admissions.yale.edu/application-deadlines",
}

# Graduate (Yale SOM MBA) admission via the SOM application.
_REQ_MBA = {
    "materials": [
        {"name": "Yale SOM online application", "required": True},
        {"name": "One essay (from three prompts, 500-word limit)", "required": True},
        {"name": "Unofficial transcripts from all degree-credit institutions", "required": True},
        {"name": "Two recommendations", "required": True},
        {"name": "One-page resume", "required": True},
        {
            "name": "GMAT or GRE scores",
            "required": True,
            "note": (
                "GMAT or GRE accepted with no committee preference; scores must be "
                "less than five years old."
            ),
        },
        {"name": "Behavioral Assessment + two video questions", "required": True},
        {"name": "Interview (by invitation only)", "required": False},
        {"name": "$250 application fee (reduced for lower incomes)", "required": True},
    ],
    "deadlines": [
        {"round": "Round 1", "date": "September 10, 2025"},
        {"round": "Round 2", "date": "January 6, 2026"},
        {"round": "Round 3", "date": "April 14, 2026"},
    ],
    "recommendations": {
        "required": 2,
        "note": "Two professional recommendations submitted through the SOM application.",
    },
    "international": {
        "english": {
            "tests": [],
            "required": False,
            "note": (
                "Yale SOM does not require an English-proficiency test for "
                "non-native speakers."
            ),
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Yale SOM — MBA Application Guide",
                "url": (
                    "https://som.yale.edu/programs/mba/admissions/application-information/"
                    "application-guide"
                ),
            }
        ],
    },
    "source": "Yale SOM — Full-time MBA Admissions",
    "source_url": "https://som.yale.edu/programs/mba/admissions",
}

# Generic Yale graduate / professional admission set. Each professional school
# administers its own admissions; the materials below are common across Yale graduate
# and professional programs, and deadlines vary by program (commonly late-fall to winter)
# — applicants are pointed to the program's own admissions page via the program website.
_REQ_GRAD_GENERIC = {
    "materials": [
        {"name": "Program online application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose / personal statement", "required": True},
        {"name": "Résumé / CV", "required": True},
        {
            "name": "Letters of recommendation",
            "required": True,
            "note": "Most Yale graduate and professional programs require two to three letters.",
        },
        {
            "name": "Standardized test scores (GRE/GMAT)",
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
            "Most Yale graduate and professional programs require three letters of "
            "recommendation (some require two)."
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
                "label": "Yale Graduate School of Arts & Sciences — Application Process",
                "url": "https://gsas.yale.edu/admissions/phdmasters-application-process",
            }
        ],
    },
    "source": "Yale graduate & professional admissions",
    "source_url": "https://gsas.yale.edu/admissions/phdmasters-application-process",
}


def _requirements_for(spec: dict) -> dict:
    """Pick the admissions requirement set for a program by slug / degree type."""
    if spec["slug"] == "yale-mba":
        return dict(_REQ_MBA)
    if spec["degree_type"] == "masters":
        return dict(_REQ_GRAD_GENERIC)
    return dict(_REQ_UNDERGRAD)


# Real Yale campus photo (Harkness Tower) — Wikimedia Commons, CC BY 2.0, hotlinkable
# landscape JPG (verified HTTP 200). Leads the institution hero.
_CAMPUS_PHOTO = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f2/"
    "Harkness_Tower_-_Yale_University_%2854106458290%29.jpg/"
    "1920px-Harkness_Tower_-_Yale_University_%2854106458290%29.jpg"
)


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich Yale to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Yale is absent — safe on fresh/CI databases.
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
    inst.founded_year = 1701
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.yale.edu"
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
        # No school carries its own keyword-relevant feed (only the flagship program does);
        # always assign None so a stale value on a pre-existing row is cleared.
        sc.content_sources = None
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
    # Yale publishes no per-program employment report or industry breakdown (its
    # first-destination data is reported college-wide, captured at the institution level),
    # so every program omits the program-level employment rate and top industries.
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
    if slug != "yale-computer-science-bs":
        # Only the flagship carries its own keyword-relevant feed; catalog programs
        # surface the institution feed rather than a per-program one.
        omitted.append("content_sources")
    return _standard(omitted)


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
        # Website: verified program/department page where available, else the owning
        # school's site.
        p.website_url = _WEBSITE_BY_SLUG.get(slug) or _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "in_person")
        # Only the flagship carries its own feed (content_sources omitted for the rest).
        p.content_sources = _CS_CONTENT if slug == "yale-computer-science-bs" else None
        # Cost: graduate programs use verified per-program tuition; undergraduate uses the
        # published Yale College rates.
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
                    "Published 2024-25 Yale College tuition with the College Scorecard "
                    "cost of attendance and average net price. Yale is need-blind (including "
                    "for international students) and meets 100% of demonstrated need with "
                    "grants rather than loans, so most families pay far less than the "
                    "sticker price (average net price ≈ $24,000)."
                ),
                "source": "Yale Student Accounts (2024-25) + College Scorecard (UNITID 130794)",
                "source_url": "https://collegescorecard.ed.gov/school/?130794",
                "year": "2024-25",
            }
        # Admissions: undergraduate, MBA or generic graduate set by slug / degree type.
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
                "source_url": "https://collegescorecard.ed.gov/school/?130794",
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
        # Application deadline (upcoming undergraduate Regular Decision closes Jan 2).
        p.application_deadline = (
            date(2026, 9, 10) if slug == "yale-mba" else date(2027, 1, 2)
        )
    session.flush()
    # Reconcile legacy Yale programs (slug not in the canonical set): delete when
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
