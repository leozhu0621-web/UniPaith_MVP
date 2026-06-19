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

Depth pass (2026-06-15, yaleprof5): merged ``DEPTH_REVIEWS`` for 54 coverable
programs — completes Yale coverable external_reviews (60/60).

Structural repair (2026-06-16, yaleprof6): replaced classification-only program
descriptions with field-specific clauses from ``yale_field_descriptions.py``.
"""

from __future__ import annotations

import re
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.profile_catalog_utils import (
    disambiguate_program_name,
    validate_catalog,
)
from unipaith.data.yale_field_descriptions import (
    FIELD_ALIASES,
    FIELD_DESCRIPTIONS,
    GRADUATE_FIELD_DESCRIPTIONS,
    SLUG_DESCRIPTIONS,
)
from unipaith.data.yale_reviews_depth import DEPTH_REVIEWS
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Yale University"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-16"

_TEMPLATE_STUB_RE = re.compile(
    r" — a .+ (undergraduate|graduate|doctoral|certificate|professional|"
    r"master's|bachelor's|PhD|MBA|JD|MD|bachelors|masters|phd) program offered through ",
    re.I,
)
_CLASSIFICATION_STUB_RE = re.compile(
    r"^.+ is (an undergraduate|a graduate|a doctoral|a graduate certificate|"
    r"a professional|a degree) program at ",
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
    "campus_photos": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f2/"
                "Harkness_Tower_-_Yale_University_%2854106458290%29.jpg/"
                "1920px-Harkness_Tower_-_Yale_University_%2854106458290%29.jpg"
            ),
            "credit": "Wikimedia Commons / Ajay Suresh (CC BY 2.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/"
                "Yale_University_Library_-_Sterling_Memorial_Library_%2854105136782%29.jpg/"
                "1920px-Yale_University_Library_-_Sterling_Memorial_Library_%2854105136782%29.jpg"
            ),
            "credit": "Wikimedia Commons / Ajay Suresh (CC BY 2.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/"
                "Beinecke_Rare_Book_%26_Manuscript_Library.jpg/"
                "1920px-Beinecke_Rare_Book_%26_Manuscript_Library.jpg"
            ),
            "credit": "Wikimedia Commons / Karlfonza (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/"
                "Woolsey_Hall_-_Yale_University_%2854106457850%29.jpg/"
                "1920px-Woolsey_Hall_-_Yale_University_%2854106457850%29.jpg"
            ),
            "credit": "Wikimedia Commons / Ajay Suresh (CC BY 2.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/"
                "Yale_Campus_Green_%284138541531%29.jpg/"
                "1920px-Yale_Campus_Green_%284138541531%29.jpg"
            ),
            "credit": "Wikimedia Commons / Francisco Anzola (CC BY 2.0)",
        },
    ],
    # Harkness Tower leads the hero; see ``campus_photos[0]``.
    "media_credit": "Wikimedia Commons / Ajay Suresh (CC BY 2.0)",
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
    "Yale University is a private research university in New Haven, CT, chartered in 1701 "
    "as the Collegiate School and renamed Yale College in 1718 — the third-oldest "
    "institution of higher education in the United States. It enrolls about "
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
_GSAS = "Yale Graduate School of Arts and Sciences"
_LAW = "Yale Law School"
_DRAMA = "David Geffen School of Drama at Yale"
_JACKSON = "Jackson School of Global Affairs"
_SEAS = "Yale School of Engineering & Applied Science"

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
    {
        "name": _GSAS,
        "sort_order": 11,
        "description": (
            "The Yale Graduate School of Arts and Sciences administers Yale's Ph.D. and "
            "terminal master's degrees across the Faculty of Arts and Sciences and allied "
            "departments — more than seventy programs of study spanning the humanities, "
            "social sciences, natural sciences and engineering."
        ),
    },
    {
        "name": _LAW,
        "sort_order": 12,
        "description": (
            "Yale Law School, whose origins trace to the early 1800s, is among the most "
            "selective law schools in the United States. It awards the J.D., the LL.M., the "
            "M.S.L. for non-lawyers, and the doctoral J.S.D. and Ph.D. in Law, and is known "
            "for its small classes and scholarly orientation."
        ),
    },
    {
        "name": _SEAS,
        "sort_order": 13,
        "description": (
            "Yale's School of Engineering & Applied Science traces to one of the first "
            "engineering professorships in the United States (1852) and was formally "
            "established as a school in 1919. Across seven departments it awards the B.S. "
            "(through Yale College) and, through the Graduate School, the M.S. and Ph.D. in "
            "engineering and applied science."
        ),
    },
    {
        "name": _JACKSON,
        "sort_order": 14,
        "description": (
            "The Jackson School of Global Affairs, which opened in 2022 as Yale's newest "
            "professional school, educates leaders in global affairs. It awards the Master "
            "of Public Policy in Global Affairs and the mid-career Master of Advanced Study, "
            "and anchors Yale College's undergraduate Global Affairs major."
        ),
    },
    {
        "name": _DRAMA,
        "sort_order": 15,
        "description": (
            "The David Geffen School of Drama at Yale, founded as a Department of Drama in "
            "1924 and tuition-free since 2021, is one of the foremost professional theater "
            "training conservatories. It awards the M.F.A., the doctoral D.F.A. and a "
            "Certificate in Drama, and is affiliated with the Yale Repertory Theatre."
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
    _GSAS: "https://gsas.yale.edu/",
    _LAW: "https://law.yale.edu/",
    _SEAS: "https://engineering.yale.edu/",
    _JACKSON: "https://jackson.yale.edu/",
    _DRAMA: "https://www.drama.yale.edu/",
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
    _GSAS: {
        # Founding year is omitted: GSAS's own about/history pages do not state a single
        # founding year, so it is recorded in _ABOUT_OMITTED rather than guessed.
        "leadership": (
            "Lynn Cooley — Dean of the Yale Graduate School of Arts and Sciences and "
            "C.N.H. Long Professor of Genetics"
        ),
        "research_centers": [
            "Interdepartmental Neuroscience Program",
        ],
        "source": {
            "label": "Yale Graduate School of Arts and Sciences — Dean's Office",
            "url": "https://gsas.yale.edu/about/deans-welcome-message",
        },
    },
    _LAW: {
        "founded": 1824,
        "leadership": (
            "Cristina Rodríguez — Sol and Lillian Goldman Dean and Professor of Law"
        ),
        "research_centers": [
            "The Information Society Project",
            "Paul Tsai China Center",
        ],
        "source": {
            "label": "Yale Law School — Office of the Dean",
            "url": "https://law.yale.edu/about-yale-law-school/office-dean",
        },
    },
    _SEAS: {
        "founded": 1852,
        "leadership": (
            "Jeffrey F. Brock — Dean of Yale Engineering and William S. Massey Professor "
            "of Mathematics"
        ),
        # Named school-owned research centers could not be verified on the SEAS pages;
        # research_centers is recorded in _ABOUT_OMITTED rather than guessed (the seven
        # academic departments are named in the school description instead).
        "source": {
            "label": "Yale School of Engineering & Applied Science — About",
            "url": "https://engineering.yale.edu/about",
        },
    },
    _JACKSON: {
        "founded": 2022,
        "leadership": (
            "James A. Levinsohn — Dean of the Jackson School of Global Affairs and "
            "Charles Goodyear Professor of Global Affairs"
        ),
        "research_centers": [
            "Johnson Center for the Study of American Diplomacy",
            "Schmidt Program on Artificial Intelligence, Emerging Technologies, and "
            "National Power",
            "Leitner Program on Effective Democratic Governance",
        ],
        "source": {
            "label": "Jackson School of Global Affairs — Centers & Initiatives",
            "url": "https://jackson.yale.edu/centers-initiatives/",
        },
    },
    _DRAMA: {
        "founded": 1924,
        "leadership": (
            "James Bundy — Elizabeth Parker Ware Dean of the David Geffen School of Drama "
            "at Yale and Artistic Director of Yale Repertory Theatre"
        ),
        "research_centers": [
            "Yale Repertory Theatre",
            "Binger Center for New Theatre",
            "Yale Institute for Music Theatre",
        ],
        "source": {
            "label": "David Geffen School of Drama at Yale — About",
            "url": "https://www.drama.yale.edu/about-us/",
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
    # GSAS's own pages state no single founding year; omit founded rather than guess.
    _GSAS: [*_FACULTY_OMIT, "about_detail.founded"],
    _LAW: list(_FACULTY_OMIT),
    # SEAS named research centers were not verifiable on its pages; omit rather than guess.
    _SEAS: [*_FACULTY_OMIT, "about_detail.research_centers"],
    _JACKSON: list(_FACULTY_OMIT),
    _DRAMA: list(_FACULTY_OMIT),
}

# ── Channel feeds + official social links ──────────────────────────────────
# The daily content-ingest reads ``news_rss`` (an RSS feed), an optional ``events_feed``
# (an iCalendar URL), ``keywords`` (word-boundary relevance filter) and ``news_curated``
# (keep every item, no keyword filter) from each node's content_sources. Without a real
# ``news_rss`` a node's Events & Updates tab is empty — so every school and program below
# carries one. Feeds verified 2026-06-11:
#   • Yale News RSS index: https://news.yale.edu/rss-feeds (all-topics + per-topic feeds)
#   • Yale events iCalendar: https://events.yale.edu/calendar.ics (BEGIN:VCALENDAR, VEVENTs)
_YALE_NEWS_RSS = "https://news.yale.edu/news-rss"  # all-topics feed
_YALE_EVENTS_ICS = {"url": "https://events.yale.edu/calendar.ics", "type": "ical"}


def _news_topic(topic: str) -> str:
    """A verified Yale News per-topic RSS feed (news.yale.edu/topics/<topic>/rss)."""
    return f"https://news.yale.edu/topics/{topic}/rss"


# Official social handles, verified per channel 2026-06-11 (school footers + the Yale
# social-media directory at yale.edu/social-media). Only handles confirmed to exist are
# listed; a school that does not run a given channel simply omits that key (never guessed).
_SOCIAL_YALE = {
    "instagram": "https://www.instagram.com/yale/",
    "linkedin": "https://www.linkedin.com/school/yale-university/",
    "x": "https://x.com/yale",
    "youtube": "https://www.youtube.com/user/YaleUniversity",
    "facebook": "https://www.facebook.com/YaleUniversity",
}
_SOCIAL_BY_SCHOOL: dict[str, dict] = {
    _COLLEGE: _SOCIAL_YALE,  # Yale College uses the university @yale channels
    _SOM: {
        "instagram": "https://www.instagram.com/yalesom/",
        "linkedin": "https://www.linkedin.com/school/yale-school-of-management/",
        "youtube": "https://www.youtube.com/yalesom",
        "facebook": "https://www.facebook.com/yalesom",
    },
    _YSE: {
        "instagram": "https://www.instagram.com/EnvironmentYale/",
        "linkedin": "https://www.linkedin.com/school/5527901/",
        "youtube": "https://www.youtube.com/channel/UCMLSDzZ9VCUUFUOT3lD815A",
        "facebook": "https://www.facebook.com/YaleEnvironment",
    },
    _YSPH: {
        "instagram": "https://www.instagram.com/yalesph/",
        "linkedin": "https://www.linkedin.com/school/yale-school-of-public-health/",
        "youtube": "https://www.youtube.com/user/YSPH1",
        "facebook": "https://www.facebook.com/YaleSPH",
    },
    _MED: {
        "instagram": "https://www.instagram.com/yaleschoolofmed/",
        "linkedin": "https://www.linkedin.com/school/yale-university-school-of-medicine/",
        "x": "https://twitter.com/yalemed",
        "facebook": "https://www.facebook.com/YaleSchoolOfMedicine",
    },
    _NURSING: {
        "instagram": "https://www.instagram.com/yalenursing/",
        "linkedin": "https://www.linkedin.com/school/yale-school-of-nursing/",
        "x": "https://twitter.com/YaleNursing",
        "youtube": "https://www.youtube.com/@yaleschoolofnursing4248",
        "facebook": "https://www.facebook.com/yalenurse",
    },
    _DIVINITY: {
        "instagram": "https://www.instagram.com/yaledivinityschool/",
        "linkedin": "https://www.linkedin.com/school/2723646/",
        "youtube": "https://www.youtube.com/user/YaleDivinitySchool",
        "facebook": "https://www.facebook.com/yaledivinityschool",
    },
    _ARCH: {
        "instagram": "https://www.instagram.com/yalearchitecture/",
        "facebook": "https://www.facebook.com/yalearchitecture",
    },
    _ART: {
        "instagram": "https://www.instagram.com/yaleschoolofart/",
        "facebook": "https://www.facebook.com/YaleSchoolofArt/",
    },
    _MUSIC: {
        "instagram": "https://www.instagram.com/yale.music/",
        "youtube": "https://www.youtube.com/c/YaleSchoolofMusicOfficial",
        "facebook": "https://www.facebook.com/yalemusic/",
    },
    _GSAS: {
        "instagram": "https://www.instagram.com/yalegsas/",
        "linkedin": "https://www.linkedin.com/company/yale-graduate-school-of-arts-sciences",
        "x": "https://x.com/yalegsas",
        "facebook": "https://www.facebook.com/YaleGSAS/",
    },
    _LAW: {
        "instagram": "https://www.instagram.com/yalelawschool/",
        "linkedin": "https://www.linkedin.com/school/yale-law-school/",
        "x": "https://x.com/YaleLawSch",
        "youtube": "https://www.youtube.com/user/YaleLawSchool",
        "facebook": "https://www.facebook.com/YaleLawSchool",
    },
    _SEAS: {
        "instagram": "https://www.instagram.com/yaleengineering/",
        "linkedin": "https://www.linkedin.com/school/yaleengineering/",
        "x": "https://x.com/yaleengineering",
        "youtube": "https://www.youtube.com/@yaleengineering",
        "facebook": "https://www.facebook.com/yaleengineering",
    },
    _JACKSON: {
        "instagram": "https://www.instagram.com/yalejacksonschool/",
        "linkedin": "https://www.linkedin.com/company/yalejacksonschool",
        "x": "https://x.com/yalejacksonsch",
        "facebook": "https://www.facebook.com/yalejacksonschool",
    },
    _DRAMA: {
        "instagram": "https://www.instagram.com/geffenyale/",
        "youtube": "https://www.youtube.com/c/DavidGeffenSchoolofDramaatYale",
        "facebook": "https://www.facebook.com/geffenyale/",
    },
}

# Per-school feed config: the best-matching verified Yale News topic RSS + the Yale events
# iCalendar, filtered to school-relevant items by ``keywords`` (the MIT/MBAn pattern). Each
# school that runs its own social channels uses them; the rest inherit the university's.
# (school_name -> {news_topic, keywords}); topic "" means the all-topics feed.
_SCHOOL_FEED_SPEC: dict[str, dict] = {
    _COLLEGE: {"topic": "", "keywords": ["Yale College", "undergraduate", "undergraduates"]},
    _SOM: {"topic": "business", "keywords": ["School of Management", "Yale SOM", "MBA"]},
    _YSE: {
        "topic": "environment",
        "keywords": ["School of the Environment", "forestry", "environmental"],
    },
    _YSPH: {
        "topic": "health-medicine",
        "keywords": ["Public Health", "epidemiology", "YSPH"],
    },
    _MED: {
        "topic": "health-medicine",
        "keywords": ["School of Medicine", "medical school", "physicians"],
    },
    _NURSING: {"topic": "health-medicine", "keywords": ["Nursing", "nurse", "nurses"]},
    _DIVINITY: {"topic": "arts-humanities", "keywords": ["Divinity", "theology", "religion"]},
    _ARCH: {"topic": "arts-humanities", "keywords": ["architecture", "architect"]},
    _ART: {"topic": "arts-humanities", "keywords": ["School of Art", "artist", "exhibition"]},
    _MUSIC: {"topic": "arts-humanities", "keywords": ["School of Music", "music", "musician"]},
    _GSAS: {"topic": "", "keywords": ["Graduate School", "GSAS", "doctoral"]},
    _LAW: {"topic": "law", "keywords": ["Law School", "Yale Law"]},
    _SEAS: {"topic": "science-technology", "keywords": ["engineering", "Yale Engineering"]},
    _JACKSON: {"topic": "international", "keywords": ["Jackson School", "global affairs"]},
    _DRAMA: {
        "topic": "arts-humanities",
        "keywords": ["Drama", "theater", "Geffen", "Yale Repertory"],
    },
}


def _school_content(name: str) -> dict:
    """Build a school's content_sources from its verified topic RSS + keywords + socials."""
    spec = _SCHOOL_FEED_SPEC[name]
    topic = spec["topic"]
    return {
        "news_rss": _news_topic(topic) if topic else _YALE_NEWS_RSS,
        "news_curated": False,
        "events_feed": dict(_YALE_EVENTS_ICS),
        "keywords": list(spec["keywords"]),
        "social": _SOCIAL_BY_SCHOOL.get(name, _SOCIAL_YALE),
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    """Build a program's content_sources from its school feed, refined by program keywords."""
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


# Institution-wide feed: the all-topics Yale News RSS (curated — every item is Yale news)
# + the Yale events calendar, with the official university social handles.
_INSTITUTION_CONTENT: dict = {
    "news_rss": _YALE_NEWS_RSS,
    "news_url": "https://news.yale.edu",
    "news_curated": True,
    "events_feed": dict(_YALE_EVENTS_ICS),
    "social": _SOCIAL_YALE,
}

# Per-program keyword overrides (department/program-naming terms). Programs without an
# entry inherit their school's keywords (still school-scoped). Used by _apply_programs.
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "yale-computer-science-bs": ["computer science", "Yale computer science"],
    "yale-economics-bs": ["economics", "economist"],
    "yale-political-science-bs": ["political science", "politics"],
    "yale-history-bs": ["history", "historian"],
    "yale-mcdb-bs": ["molecular biology", "cell biology", "developmental biology"],
    "yale-psychology-bs": ["psychology", "psychologist"],
    "yale-english-bs": ["English literature", "writing"],
    "yale-statistics-bs": ["statistics", "data science"],
    "yale-mathematics-bs": ["mathematics", "mathematician"],
    "yale-mba": ["MBA", "School of Management"],
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

# Explicit flagship programs — credential-disambiguated names + real departments.
_EXPLICIT_DEPARTMENTS: dict[str, str] = {
    "yale-economics-bs": "Economics",
    "yale-computer-science-bs": "Computer Science",
    "yale-political-science-bs": "Political Science",
    "yale-history-bs": "History",
    "yale-mcdb-bs": "Molecular, Cellular, and Developmental Biology",
    "yale-psychology-bs": "Psychology",
    "yale-global-affairs-bs": "Global Affairs",
    "yale-english-bs": "English",
    "yale-statistics-bs": "Statistics and Data Science",
    "yale-mathematics-bs": "Mathematics",
    "yale-mba": "Yale School of Management",
    "yale-environmental-management-mem": "Yale School of the Environment",
    "yale-environmental-science-mesc": "Yale School of the Environment",
    "yale-public-health-mph": "Yale School of Public Health",
    "yale-physician-associate-mmsc": "Yale School of Medicine",
    "yale-nursing-msn": "Yale School of Nursing",
    "yale-divinity-mdiv": "Yale Divinity School",
    "yale-architecture-march": "Yale School of Architecture",
    "yale-art-mfa": "Yale School of Art",
    "yale-music-mm": "Yale School of Music",
}
_EXPLICIT_FULL_NAMES: dict[str, str] = {
    "yale-economics-bs": "Bachelor of Arts in Economics",
    "yale-computer-science-bs": "Bachelor of Science in Computer Science",
    "yale-political-science-bs": "Bachelor of Arts in Political Science",
    "yale-history-bs": "Bachelor of Arts in History",
    "yale-mcdb-bs": (
        "Bachelor of Science in Molecular, Cellular, and Developmental Biology"
    ),
    "yale-psychology-bs": "Bachelor of Arts in Psychology",
    "yale-global-affairs-bs": "Bachelor of Arts in Global Affairs",
    "yale-english-bs": "Bachelor of Arts in English",
    "yale-statistics-bs": "Bachelor of Arts in Statistics and Data Science",
    "yale-mathematics-bs": "Bachelor of Arts in Mathematics",
}
for _p in PROGRAMS:
    if _p["slug"] in _EXPLICIT_DEPARTMENTS:
        _p["department"] = _EXPLICIT_DEPARTMENTS[_p["slug"]]
    if _p["slug"] in _EXPLICIT_FULL_NAMES:
        _p["program_name"] = _EXPLICIT_FULL_NAMES[_p["slug"]]

# ── Full catalog (breadth) ─────────────────────────────────────────────────
# The explicit PROGRAMS above carry rich, individually-sourced detail. The blocks below
# complete Yale's *published* degree catalog with verified BASICS (full name, degree,
# delivery_format, owning school, factual description) so no real program is missing;
# deeper fields (tracks/outcomes/faculty/reviews) are omitted-pending per _program_standard
# and deepened on resume runs. Cross-checked against the College Scorecard Field-of-Study
# list for UNITID 130794. Sources:
#   • Yale College majors (82): https://catalog.yale.edu/ycps/majors-in-yale-college/
#   • Graduate & professional degrees: each owning school's official degree page
#     (som.yale.edu/programs · law.yale.edu/study-law-yale/degree-programs ·
#     medicine.yale.edu/edu · nursing.yale.edu/academics ·
#     ysph.yale.edu/school-of-public-health/graduate-programs ·
#     environment.yale.edu/academics · divinity.yale.edu/programs/degrees ·
#     architecture.yale.edu/academics · music.yale.edu/degrees-and-programs ·
#     bulletin.yale.edu/bulletins/drama/degrees · jackson.yale.edu/academics ·
#     gsas.yale.edu/programs-of-study).


_SLUG_REPL = {"&": "and", "—": " ", "/": " ", "'": "", ".": "", ",": "", "(": "", ")": ""}


def _slugify(text: str) -> str:
    s = text.lower()
    for a, b in _SLUG_REPL.items():
        s = s.replace(a, b)
    return "-".join(s.split())


_EXISTING_SLUGS = {p["slug"] for p in PROGRAMS}
_EXISTING_CIP_KEYS = {(p.get("cip"), p["degree_type"]) for p in PROGRAMS if p.get("cip")}


def _department_for(field_name: str, school: str) -> str:
    """Owning department — the field title unless it duplicates the school name."""
    if field_name.lower() in school.lower() or school.lower() in field_name.lower():
        return school
    return field_name


def _field_from_program_name(program_name: str) -> str | None:
    """Extract field title from a disambiguated program name."""
    for prefix in (
        "Bachelor of Arts in ",
        "Bachelor of Science in ",
        "Bachelor's in ",
        "Master's in ",
        "Doctor of Philosophy in ",
        "Graduate Certificate in ",
    ):
        if program_name.startswith(prefix):
            return program_name[len(prefix):]
    return None


def _needs_normalize(desc: str) -> bool:
    """True when a description is a classification or template stub."""
    if not desc:
        return True
    if _CLASSIFICATION_STUB_RE.match(desc):
        return True
    if _TEMPLATE_STUB_RE.search(desc):
        return True
    return "offered through the " in desc


def _yale_description(spec: dict, field: str | None = None) -> str:
    """Field-specific description — never the degree-type classification stub."""
    slug = spec["slug"]
    fmt = spec.get("delivery_format", "in_person")
    delivery = ""
    if fmt == "online":
        delivery = " Delivered online."
    elif fmt == "hybrid":
        delivery = " Delivered in hybrid format."
    if slug in SLUG_DESCRIPTIONS:
        return f"{SLUG_DESCRIPTIONS[slug]}{delivery}"
    field_key = (
        field
        or spec.get("_field_name")
        or _field_from_program_name(spec.get("program_name", ""))
        or spec.get("department")
        or spec.get("program_name", "")
    )
    if field_key in FIELD_ALIASES:
        field_key = FIELD_ALIASES[field_key]
    # A field Yale offers at more than one credential level carries a distinct researched
    # body per level (an undergraduate major vs funded doctoral research are different
    # things) so credential siblings never share a leading body — gold MIT = 0% verbatim /
    # shared-leading-body (anti-stub §8.5). Graduate rows take the graduate clause when one
    # exists; everything else takes the (undergraduate/default) FIELD_DESCRIPTIONS clause.
    if spec.get("degree_type") in {"masters", "phd", "doctorate"} and (
        field_key in GRADUATE_FIELD_DESCRIPTIONS
    ):
        clause = GRADUATE_FIELD_DESCRIPTIONS[field_key]
    else:
        clause = FIELD_DESCRIPTIONS.get(field_key)
    if not clause:
        raise ValueError(
            f"Missing FIELD_DESCRIPTIONS entry for {field_key!r} ({slug})"
        )
    # The program name is already the page heading; opening the description on the field
    # fact (never restating the name) keeps the heading from rendering twice (anti-stub
    # name_prefixed = 0, gold-MIT contrast).
    return f"{clause}{delivery}"


def _normalize_program(spec: dict, field_name: str | None = None) -> None:
    """Stamp a field-specific description on stub program nodes."""
    if not _needs_normalize(spec.get("description") or ""):
        return
    spec["description"] = _yale_description(spec, field=field_name)


def _ug_program_name(field_name: str, degree_label: str) -> str:
    """Disambiguate Yale College majors by credential (B.A. vs B.S.)."""
    if degree_label.startswith("B.S."):
        return f"Bachelor of Science in {field_name}"
    if "B.A. or B.S." in degree_label:
        return f"Bachelor's in {field_name}"
    return f"Bachelor of Arts in {field_name}"


# Yale College majors NOT already represented above (the existing 10 carry rich detail).
# (name, degree_label, owning_school). Engineering / applied-physics majors are owned by
# SEAS; all other majors by Yale College. Degree labels are verbatim from the catalog.
_UG_MAJORS: list[tuple[str, str, str]] = [
    ("African Studies", "B.A.", _COLLEGE),
    ("American Studies", "B.A.", _COLLEGE),
    ("Anthropology", "B.A.", _COLLEGE),
    ("Applied Mathematics", "B.A. or B.S.", _COLLEGE),
    ("Applied Physics", "B.S.", _SEAS),
    ("Archaeological Studies", "B.A.", _COLLEGE),
    ("Architecture", "B.A.", _COLLEGE),
    ("Art", "B.A.", _COLLEGE),
    ("Astronomy", "B.A.", _COLLEGE),
    ("Astrophysics", "B.S.", _COLLEGE),
    ("Biomedical Engineering", "B.S.", _SEAS),
    ("Black Studies", "B.A.", _COLLEGE),
    ("Chemical Engineering", "B.S.", _SEAS),
    ("Chemistry", "B.A. or B.S.", _COLLEGE),
    ("Classical Civilization", "B.A.", _COLLEGE),
    ("Classics", "B.A.", _COLLEGE),
    ("Cognitive Science", "B.A. or B.S.", _COLLEGE),
    ("Comparative Literature", "B.A.", _COLLEGE),
    ("Computer Science and Economics", "B.S.", _SEAS),
    ("Computer Science and Mathematics", "B.S.", _SEAS),
    ("Computer Science and Psychology", "B.A.", _SEAS),
    ("Computing and Linguistics", "B.A. or B.S.", _SEAS),
    ("Computing and the Arts", "B.A.", _SEAS),
    ("Earth and Planetary Sciences", "B.A. or B.S.", _COLLEGE),
    ("East Asian Languages and Literatures", "B.A.", _COLLEGE),
    ("East Asian Studies", "B.A.", _COLLEGE),
    ("Ecology and Evolutionary Biology", "B.A. or B.S.", _COLLEGE),
    ("Economics and Mathematics", "B.A.", _COLLEGE),
    ("Electrical Engineering", "B.S.", _SEAS),
    ("Electrical Engineering and Computer Science", "B.S.", _SEAS),
    ("Engineering Sciences (Chemical)", "B.S.", _SEAS),
    ("Engineering Sciences (Electrical)", "B.A. or B.S.", _SEAS),
    ("Engineering Sciences (Environmental)", "B.A.", _SEAS),
    ("Engineering Sciences (Mechanical)", "B.A. or B.S.", _SEAS),
    ("Environmental Engineering", "B.S.", _SEAS),
    ("Environmental Studies", "B.A. or B.S.", _COLLEGE),
    ("Ethics, Politics, and Economics", "B.A.", _COLLEGE),
    ("Ethnicity, Race, and Migration", "B.A.", _COLLEGE),
    ("Film and Media Studies", "B.A.", _COLLEGE),
    ("French", "B.A.", _COLLEGE),
    ("German Studies", "B.A.", _COLLEGE),
    ("Greek, Ancient and Modern", "B.A.", _COLLEGE),
    ("History of Art", "B.A.", _COLLEGE),
    ("History of Science, Medicine, and Public Health", "B.A.", _COLLEGE),
    ("Humanities", "B.A.", _COLLEGE),
    ("Italian Studies", "B.A.", _COLLEGE),
    ("Jewish Studies", "B.A.", _COLLEGE),
    ("Latin American Studies", "B.A.", _COLLEGE),
    ("Linguistics", "B.A.", _COLLEGE),
    ("Mathematics and Philosophy", "B.A.", _COLLEGE),
    ("Mathematics and Physics", "B.S.", _COLLEGE),
    ("Mechanical Engineering", "B.S.", _SEAS),
    ("Modern Middle East Studies", "B.A.", _COLLEGE),
    ("Molecular Biophysics and Biochemistry", "B.A. or B.S.", _COLLEGE),
    ("Music", "B.A.", _COLLEGE),
    ("Near Eastern Languages and Civilizations", "B.A.", _COLLEGE),
    ("Neuroscience", "B.A. or B.S.", _COLLEGE),
    ("Philosophy", "B.A.", _COLLEGE),
    ("Physics", "B.S.", _COLLEGE),
    ("Physics and Geosciences", "B.S.", _COLLEGE),
    ("Physics and Philosophy", "B.A. or B.S.", _COLLEGE),
    ("Portuguese", "B.A.", _COLLEGE),
    ("Religious Studies", "B.A.", _COLLEGE),
    ("Russian", "B.A.", _COLLEGE),
    ("Russian, East European, and Eurasian Studies", "B.A.", _COLLEGE),
    ("Sociology", "B.A.", _COLLEGE),
    ("Spanish", "B.A.", _COLLEGE),
    ("Theater, Dance, and Performance Studies", "B.A.", _COLLEGE),
    ("Urban Studies", "B.A.", _COLLEGE),
    ("Women's, Gender, and Sexuality Studies", "B.A.", _COLLEGE),
]

# Graduate & professional degrees NOT already represented above.
# (program_name, degree_type, owning_school, duration_months, delivery_format, description)
_GRAD_PROGRAMS: list[tuple[str, str, str, int, str, str]] = [
    # ── Law ──
    ("Juris Doctor (J.D.)", "professional", _LAW, 36, "in_person",
     "Yale Law School's three-year professional law degree, known for small classes and a "
     "scholarly, public-interest orientation."),
    ("Master of Laws (LL.M.)", "masters", _LAW, 12, "in_person",
     "A one-year degree for lawyers who already hold a first degree in law, oriented toward "
     "those pursuing careers in legal teaching."),
    ("Master of Studies in Law (M.S.L.)", "masters", _LAW, 12, "in_person",
     "A one-year degree introducing legal reasoning to accomplished professionals in other "
     "fields who are not seeking to practice law."),
    ("Doctor of the Science of Law (J.S.D.)", "phd", _LAW, 36, "in_person",
     "Yale Law School's advanced research doctorate for graduates of its LL.M. program."),
    ("Doctor of Philosophy in Law (Ph.D.)", "phd", _LAW, 48, "in_person",
     "A Ph.D. in Law for J.D. holders preparing for careers as legal scholars, administered "
     "with the Graduate School."),
    # ── School of Management ──
    ("MBA for Executives (EMBA)", "masters", _SOM, 22, "hybrid",
     "A 22-month MBA for working professionals, combining on-campus sessions with distance "
     "learning across a focus in asset management, healthcare or sustainability."),
    ("Master of Advanced Management (MAM)", "masters", _SOM, 12, "in_person",
     "A one-year degree for graduates of top business schools in the Global Network for "
     "Advanced Management."),
    ("Master's Degree in Asset Management", "masters", _SOM, 12, "in_person",
     "A one-year, STEM-designated master's in asset management for early-career investment "
     "professionals."),
    ("Master's Degree in Global Business & Society", "masters", _SOM, 12, "in_person",
     "A one-year master's preparing early-career professionals to lead at the intersection "
     "of business and society."),
    ("Master's Degree in Systemic Risk", "masters", _SOM, 12, "in_person",
     "A one-year master's for early-career central bankers and financial regulators studying "
     "systemic financial risk."),
    ("Master's Degree in Technology Management", "masters", _SOM, 12, "in_person",
     "A one-year master's for Yale College engineering and computer-science graduates, "
     "bridging technology and management."),
    ("Master's Degree in Public Education Management", "masters", _SOM, 12, "in_person",
     "A one-year master's for senior leaders managing large public-school systems."),
    ("Doctor of Philosophy in Management (Ph.D.)", "phd", _SOM, 60, "in_person",
     "A doctoral program training scholars in accounting, financial economics, marketing, "
     "operations and organizations & management."),
    # ── Medicine ──
    ("Doctor of Medicine (M.D.)", "professional", _MED, 48, "in_person",
     "Yale School of Medicine's four-year M.D. program, distinguished by the 'Yale System' "
     "of non-graded, self-directed preclinical study and a required research thesis."),
    ("M.D.–Ph.D. Program", "phd", _MED, 96, "in_person",
     "An NIH-supported Medical Scientist Training Program integrating the M.D. with a Ph.D. "
     "for students preparing for careers as physician-scientists."),
    ("Master of Health Science (M.H.S.)", "masters", _MED, 24, "in_person",
     "A research master's for clinicians and scientists building careers in clinical and "
     "translational investigation."),
    # ── Nursing ──
    ("Doctor of Nursing Practice (D.N.P.)", "phd", _NURSING, 36, "in_person",
     "A practice doctorate for advanced-practice nurses, offered in clinical and leadership "
     "tracks."),
    ("Doctor of Philosophy in Nursing (Ph.D.)", "phd", _NURSING, 48, "in_person",
     "A research doctorate preparing nurse scientists, administered with the Graduate "
     "School."),
    # ── Public Health ──
    ("Master of Science in Public Health (M.S.)", "masters", _YSPH, 24, "in_person",
     "A research-oriented two-year master's across biostatistics, epidemiology, health "
     "informatics and related concentrations."),
    ("Doctor of Philosophy in Public Health (Ph.D.)", "phd", _YSPH, 60, "in_person",
     "A funded research doctorate across the school's departments, administered with the "
     "Graduate School."),
    # ── Environment ──
    ("Master of Forestry (M.F.)", "masters", _YSE, 24, "in_person",
     "A two-year professional forestry degree from the oldest graduate forestry school in "
     "the United States."),
    ("Master of Forest Science (M.F.S.)", "masters", _YSE, 24, "in_person",
     "A two-year, research-oriented master's in forest science."),
    ("Doctor of Philosophy in Environment (Ph.D.)", "phd", _YSE, 60, "in_person",
     "A funded research doctorate in environmental science, management and policy, "
     "administered with the Graduate School."),
    # ── Divinity ──
    ("Master of Arts in Religion (M.A.R.)", "masters", _DIVINITY, 24, "in_person",
     "A two-year academic master's in religion, offered in a comprehensive track or a "
     "concentrated area of study."),
    ("Master of Sacred Theology (S.T.M.)", "masters", _DIVINITY, 12, "in_person",
     "A one-year advanced theological degree for those who already hold an M.Div. or "
     "equivalent first theological degree."),
    # ── Architecture ──
    ("Master of Architecture II (M.Arch II)", "masters", _ARCH, 24, "in_person",
     "A post-professional two-year degree for students who already hold a professional "
     "architecture degree."),
    ("Master of Environmental Design (M.E.D.)", "masters", _ARCH, 24, "in_person",
     "A two-year research and thesis degree in the history, theory and criticism of the "
     "built environment."),
    ("Doctor of Philosophy in Architecture (Ph.D.)", "phd", _ARCH, 60, "in_person",
     "A research doctorate in the history and theory of architecture, administered with the "
     "Graduate School."),
    # ── Music ──
    ("Master of Musical Arts (M.M.A.)", "masters", _MUSIC, 24, "in_person",
     "An advanced performance degree beyond the M.M., tuition-free like all School of Music "
     "degrees."),
    ("Doctor of Musical Arts (D.M.A.)", "phd", _MUSIC, 60, "in_person",
     "The School of Music's terminal performance doctorate, completed after the M.M.A. with "
     "a dissertation."),
    ("Artist Diploma (A.D.)", "certificate", _MUSIC, 12, "in_person",
     "A performance diploma for exceptional instrumentalists, awarded tuition-free."),
    ("Certificate in Performance", "certificate", _MUSIC, 36, "in_person",
     "A three-year performance certificate for outstanding musicians who do not hold a "
     "bachelor's degree."),
    # ── David Geffen School of Drama ──
    ("Master of Fine Arts in Drama (M.F.A.)", "masters", _DRAMA, 36, "in_person",
     "A three-year professional conservatory M.F.A. across acting, directing, design, "
     "dramaturgy, playwriting, stage management, sound design, technical design & "
     "production and theater management."),
    ("Doctor of Fine Arts (D.F.A.)", "phd", _DRAMA, 36, "in_person",
     "A research doctorate in dramaturgy and dramatic criticism for holders of the school's "
     "M.F.A."),
    ("Certificate in Drama", "certificate", _DRAMA, 36, "in_person",
     "The same conservatory training as the M.F.A., awarded to admitted students who do not "
     "hold an undergraduate degree."),
    # ── Jackson School of Global Affairs ──
    ("Master of Public Policy in Global Affairs (M.P.P.)", "masters", _JACKSON, 24, "in_person",
     "A two-year professional degree in global affairs preparing leaders for the public, "
     "private and nonprofit sectors."),
    ("Master of Advanced Study in Global Affairs (M.A.S.)", "masters", _JACKSON, 12, "in_person",
     "A one-year degree for accomplished mid-career professionals in global affairs."),
]

# Yale Graduate School of Arts and Sciences — arts-&-sciences Ph.D./terminal-master's
# programs (the professional-school doctorates above are not duplicated here).
# (name, degree_type). Verbatim from gsas.yale.edu/programs-of-study.
_GSAS_PROGRAMS: list[tuple[str, str]] = [
    ("African Studies", "masters"),
    ("American Studies", "phd"),
    ("Anthropology", "phd"),
    ("Applied and Computational Mathematics", "phd"),
    ("Applied Physics", "phd"),
    ("Archaeological Studies", "masters"),
    ("Astronomy", "phd"),
    ("Biological and Biomedical Sciences", "phd"),
    ("Biomedical Engineering", "phd"),
    ("Cell Biology", "phd"),
    ("Cellular and Molecular Physiology", "phd"),
    ("Chemical and Environmental Engineering", "phd"),
    ("Chemistry", "phd"),
    ("Classics", "phd"),
    ("Comparative Literature", "phd"),
    ("Computational Biology and Biomedical Informatics", "phd"),
    ("Computer Science", "phd"),
    ("Earth and Planetary Sciences", "phd"),
    ("East Asian Languages and Literatures", "phd"),
    ("East Asian Studies", "masters"),
    ("Ecology and Evolutionary Biology", "phd"),
    ("Economics", "phd"),
    ("Electrical and Computer Engineering", "phd"),
    ("English Language and Literature", "phd"),
    ("European and Russian Studies", "masters"),
    ("Film and Media Studies", "phd"),
    ("French", "phd"),
    ("Genetics", "phd"),
    ("Germanic Languages and Literatures", "phd"),
    ("History", "phd"),
    ("History of Art", "phd"),
    ("History of Science and Medicine", "phd"),
    ("Immunobiology", "phd"),
    ("Interdepartmental Neuroscience Program", "phd"),
    ("International and Development Economics", "masters"),
    ("Investigative Medicine", "phd"),
    ("Italian Studies", "phd"),
    ("Linguistics", "phd"),
    ("Materials Science", "phd"),
    ("Mathematics", "phd"),
    ("Mechanical Engineering", "phd"),
    ("Medieval Studies", "phd"),
    ("Microbiology", "phd"),
    ("Molecular Biophysics and Biochemistry", "phd"),
    ("Molecular, Cellular, and Developmental Biology", "phd"),
    ("Music", "phd"),
    ("Near Eastern Languages and Civilizations", "phd"),
    ("Pathology and Molecular Medicine", "phd"),
    ("Personalized Medicine and Applied Engineering", "masters"),
    ("Pharmacology", "phd"),
    ("Philosophy", "phd"),
    ("Physics", "phd"),
    ("Political Science", "phd"),
    ("Psychology", "phd"),
    ("Religious Studies", "phd"),
    ("Slavic Languages and Literatures", "phd"),
    ("Sociology", "phd"),
    ("Spanish and Portuguese", "phd"),
    ("Statistics", "masters"),
    ("Statistics and Data Science", "phd"),
    ("Translational Biomedicine", "phd"),
    ("Women's, Gender, and Sexuality Studies", "phd"),
]


def _build_catalog() -> list[dict]:
    """Append verified-basics program nodes for the rest of Yale's published catalog."""
    out: list[dict] = []
    seen = set(_EXISTING_SLUGS)
    for name, label, school in _UG_MAJORS:
        slug = f"yale-{_slugify(name)}-{'bs' if label == 'B.S.' else 'ba'}"
        if slug in seen:
            continue
        seen.add(slug)
        dept = _department_for(name, school)
        pname = _ug_program_name(name, label)
        fmt = "in_person"
        spec = {
            "slug": slug,
            "school": school,
            "program_name": pname,
            "degree_type": "bachelors",
            "department": dept,
            "duration_months": 48,
            "delivery_format": fmt,
            "_field_name": name,
        }
        _normalize_program(spec, name)
        spec.pop("_field_name", None)
        out.append(spec)
    for name, dtype, school, dur, fmt, desc in _GRAD_PROGRAMS:
        suffix = {"phd": "phd", "professional": "prof", "certificate": "cert"}.get(dtype, "ms")
        slug = f"yale-{_slugify(name)}-{suffix}"
        if slug in seen:
            continue
        seen.add(slug)
        out.append({
            "slug": slug,
            "school": school,
            "program_name": name,
            "degree_type": dtype,
            "department": school,
            "duration_months": dur,
            "delivery_format": fmt,
            "description": desc,
        })
    for name, dtype in _GSAS_PROGRAMS:
        suffix = "phd" if dtype == "phd" else "ma"
        slug = f"yale-{_slugify(name)}-gsas-{suffix}"
        if slug in seen:
            continue
        seen.add(slug)
        dept = _department_for(name, _GSAS)
        pname = disambiguate_program_name(name, dtype)
        fmt = "in_person"
        spec = {
            "slug": slug,
            "school": _GSAS,
            "program_name": pname,
            "degree_type": dtype,
            "department": dept,
            "duration_months": 60 if dtype == "phd" else 24,
            "delivery_format": fmt,
            "_field_name": name,
        }
        _normalize_program(spec, name)
        spec.pop("_field_name", None)
        out.append(spec)
    return out


PROGRAMS += _build_catalog()
for _p in PROGRAMS:
    _normalize_program(_p, _field_from_program_name(_p.get("program_name", "")))

_catalog_errors = validate_catalog(PROGRAMS)
_stub_desc = sum(1 for p in PROGRAMS if "offered through the " in (p.get("description") or ""))
_new_templ = sum(1 for p in PROGRAMS if _TEMPLATE_STUB_RE.search(p.get("description") or ""))
if _stub_desc:
    _catalog_errors.append(f"template stub descriptions on {_stub_desc} programs")
if _new_templ:
    _catalog_errors.append(f"program_description template on {_new_templ} programs")
_classification_stubs = sum(
    1 for p in PROGRAMS if _CLASSIFICATION_STUB_RE.match(p.get("description") or "")
)
if _classification_stubs:
    _catalog_errors.append(
        f"classification-only descriptions on {_classification_stubs} programs"
    )
if _catalog_errors:
    raise RuntimeError(f"Yale catalog quality gate failed: {_catalog_errors}")

# Ensure every program carries a delivery_format (all residential unless noted).
for _p in PROGRAMS:
    _p.setdefault("delivery_format", "in_person")

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

# Full official program names (program-page title).
_FULL_NAME_BY_SLUG: dict[str, str] = {p["slug"]: p["program_name"] for p in PROGRAMS}
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

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
    "yale-mba": {
        "summary": (
            "Students and third-party guides describe Yale SOM's two-year MBA as a "
            "distinctive general-management program — U.S. News ranks it No. 11 (tie, 2026) "
            "and Poets&Quants' composite places it 17th for 2025-2026 — built around an "
            "integrated, multidisciplinary core and a mission to educate leaders for "
            "business and society. Common cautions are a recent slide in composite rankings "
            "(Poets&Quants fell from 8th to 17th), the cost of a residential Ivy MBA, and "
            "a New Haven location that is quieter for finance recruiting than New York or "
            "Boston."
        ),
        "themes": [
            {
                "label": "Integrated curriculum",
                "sentiment": "positive",
                "detail": (
                    "A single, team-taught core spans organizational behavior, economics, "
                    "accounting, and global business rather than siloed functional courses."
                ),
            },
            {
                "label": "Business & society mission",
                "sentiment": "positive",
                "detail": (
                    "The school emphasizes leadership with a public-purpose orientation, "
                    "nonprofit and social-enterprise pathways, and global study options."
                ),
            },
            {
                "label": "National MBA standing",
                "sentiment": "positive",
                "detail": "U.S. News Best Business Schools 2026: No. 11 (tie).",
            },
            {
                "label": "Recent ranking slide",
                "sentiment": "caution",
                "detail": (
                    "Poets&Quants' 2025-2026 composite dropped Yale SOM to 17th from 8th "
                    "after weaker showings on several constituent lists."
                ),
            },
            {
                "label": "Cost & location",
                "sentiment": "caution",
                "detail": (
                    "Two-year residential tuition near $84,900/year before living costs; "
                    "New Haven is less central than NYC for some finance paths."
                ),
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Yale School of Management",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/yale-university-01140",
            },
            {
                "label": "Poets&Quants — Yale School of Management profile",
                "url": "https://poetsandquants.com/school-profile/yale-school-of-management/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "yale-economics-bs": {
        "summary": (
            "Students and guides describe Yale's economics major as one of the university's "
            "most popular and analytically rigorous undergraduate programs — Niche ranks Yale "
            "No. 3 nationally for economics (2026) and U.S. News places Yale among the top "
            "economics departments — with strong faculty in micro, macro, and econometrics "
            "and excellent pipelines to consulting, finance, and graduate study. Common "
            "cautions are that Yale has no standalone undergraduate business school, "
            "quantitative theory courses can be demanding, and Wall Street on-campus "
            "recruiting is lighter than at some peer Ivies."
        ),
        "themes": [
            {
                "label": "National economics standing",
                "sentiment": "positive",
                "detail": "Niche #3 Best Colleges for Economics in America (2026).",
            },
            {
                "label": "Faculty & research depth",
                "sentiment": "positive",
                "detail": (
                    "A top-ranked department with Nobel-caliber faculty and strong "
                    "undergraduate research opportunities."
                ),
            },
            {
                "label": "Career versatility",
                "sentiment": "positive",
                "detail": (
                    "Economics is Yale College's largest social-sciences major with "
                    "strong placement into consulting, finance, and Ph.D. programs."
                ),
            },
            {
                "label": "No undergrad business school",
                "sentiment": "mixed",
                "detail": (
                    "Students interested in finance often pair economics with extracurricular "
                    "clubs rather than a dedicated B-school curriculum."
                ),
            },
            {
                "label": "Quantitative rigor",
                "sentiment": "caution",
                "detail": (
                    "Theory and econometrics sequences are demanding; math preparation "
                    "matters for the honors track."
                ),
            },
        ],
        "sources": [
            {
                "label": "Niche — Best Colleges for Economics (2026)",
                "url": "https://www.niche.com/colleges/search/best-colleges-for-economics/",
            },
            {
                "label": "Yale Department of Economics",
                "url": "https://economics.yale.edu/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "yale-public-health-mph": {
        "summary": (
            "Students and public-health guides describe Yale's M.P.H. as the flagship "
            "degree of an Ivy research school that rose to No. 11 among U.S. public-health "
            "schools in U.S. News (Yale's best ranking to date) — with interdisciplinary "
            "training across biostatistics, epidemiology, health policy, and environmental "
            "health. Common cautions are that peer-assessment rankings can fluctuate, Yale "
            "is smaller than some flagship public schools, and tuition in New Haven is high "
            "despite strong scholarship support for many students."
        ),
        "themes": [
            {
                "label": "Rising national standing",
                "sentiment": "positive",
                "detail": (
                    "YSPH rose to No. 11 in U.S. News public-health schools — Yale's "
                    "highest-ever placement."
                ),
            },
            {
                "label": "Interdisciplinary breadth",
                "sentiment": "positive",
                "detail": (
                    "Two-year M.P.H. with departments in biostatistics, epidemiology, "
                    "health policy, and social & behavioral sciences."
                ),
            },
            {
                "label": "Research & practice links",
                "sentiment": "positive",
                "detail": (
                    "Access to Yale's medical campus, global-health centers, and "
                    "policy institutes in New Haven and beyond."
                ),
            },
            {
                "label": "Peer-assessment volatility",
                "sentiment": "mixed",
                "detail": (
                    "U.S. News public-health rankings rely heavily on dean/faculty surveys "
                    "and can shift year to year."
                ),
            },
            {
                "label": "Scale vs. public giants",
                "sentiment": "caution",
                "detail": (
                    "A smaller cohort than schools like Michigan or Johns Hopkins, which "
                    "some applicants weigh against Ivy prestige."
                ),
            },
        ],
        "sources": [
            {
                "label": "YSPH — rises in national rankings",
                "url": "https://ysph.yale.edu/news-article/ysph-rises-in-national-rankings-for-schools-of-public-health/",
            },
            {
                "label": "U.S. News — Best Public Health Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "yale-juris-doctor-jd-prof": {
        "summary": (
            "Students and legal guides describe Yale Law School's J.D. as among the most "
            "prestigious law degrees in the world — U.S. News ranks it No. 2 (tie with "
            "Chicago, 2026), ending Yale's decades-long solo hold on No. 1 — with "
            "unusually small classes, a faculty-heavy scholarly culture, and extraordinary "
            "clerkship and public-interest placement. Common cautions are extreme "
            "selectivity (roughly 8% acceptance), a culture oriented toward academia and "
            "clerkships over Big Law volume, and the high cost of three years in New Haven."
        ),
        "themes": [
            {
                "label": "Elite national standing",
                "sentiment": "positive",
                "detail": (
                    "U.S. News Best Law Schools 2026: No. 2 (tie with University of "
                    "Chicago); Stanford now holds No. 1 alone."
                ),
            },
            {
                "label": "Clerkships & public interest",
                "sentiment": "positive",
                "detail": (
                    "Historically the leading feeder to federal clerkships and a strong "
                    "public-interest and academic pipeline."
                ),
            },
            {
                "label": "Small classes & faculty access",
                "sentiment": "positive",
                "detail": (
                    "Very small sections and a scholarly, discussion-driven classroom "
                    "culture unlike larger law schools."
                ),
            },
            {
                "label": "Extreme selectivity",
                "sentiment": "caution",
                "detail": (
                    "Among the lowest acceptance rates of any U.S. law school; median "
                    "LSAT and GPA well above national norms."
                ),
            },
            {
                "label": "Academic vs. Big Law tilt",
                "sentiment": "mixed",
                "detail": (
                    "Reviewers note Yale's culture favors clerkships, academia, and "
                    "public service over maximizing large-firm placement volume."
                ),
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Yale Law School",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/yale-university-03094",
            },
            {
                "label": "Yale Law School — About",
                "url": "https://law.yale.edu/about-yale-law-school",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "yale-architecture-march": {
        "summary": (
            "Students and architecture guides describe Yale's NAAB-accredited M.Arch I as "
            "a small, studio-intensive program within a top research university — "
            "historically a DesignIntelligence top-five program (Yale opted out of those "
            "rankings in 2022 over methodology concerns) — with notable alumni including "
            "Maya Lin and Eero Saarinen and a strong global studio culture. Common cautions "
            "are the demanding studio workload, a relatively small cohort, and the school's "
            "decision to stop participating in DesignIntelligence surveys."
        ),
        "themes": [
            {
                "label": "Studio intensity & faculty access",
                "sentiment": "positive",
                "detail": (
                    "Small cohort with personalized crits and direct access to practicing "
                    "architect-faculty in a research-university setting."
                ),
            },
            {
                "label": "Alumni legacy",
                "sentiment": "positive",
                "detail": (
                    "Graduates include Maya Lin, Eero Saarinen, Norman Foster, and "
                    "Richard Rogers among other influential architects."
                ),
            },
            {
                "label": "Global studio opportunities",
                "sentiment": "positive",
                "detail": (
                    "Travel studios and the school's historic leadership in architectural "
                    "education since 1916."
                ),
            },
            {
                "label": "Ranking opt-out",
                "sentiment": "mixed",
                "detail": (
                    "Dean Deborah Berke withdrew Yale Architecture from DesignIntelligence "
                    "rankings in 2022, citing methodology concerns."
                ),
            },
            {
                "label": "Studio workload",
                "sentiment": "caution",
                "detail": (
                    "Three-year professional track with sustained studio and crit "
                    "demands typical of elite M.Arch programs."
                ),
            },
        ],
        "sources": [
            {
                "label": "Yale School of Architecture — M.Arch I",
                "url": "https://www.architecture.yale.edu/academics/programs/1-m-arch-i",
            },
            {
                "label": "Niche — Yale School of Architecture",
                "url": "https://www.niche.com/graduate-schools/yale-school-of-architecture/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "yale-environmental-management-mem": {
        "summary": (
            "Students and environmental guides describe Yale's MEM as the flagship "
            "professional degree at the nation's oldest graduate school of forestry and "
            "environmental studies — Eduniversal ranks it No. 5 among sustainable "
            "development and environmental-management master's programs — with "
            "interdisciplinary training across science, policy, and management and access "
            "to courses across Yale. Common cautions are a research- and policy-heavy "
            "culture that can feel academic for students seeking purely technical tracks, "
            "and the cost of two years in New Haven despite generous aid for many admits."
        ),
        "themes": [
            {
                "label": "Historic school & national rank",
                "sentiment": "positive",
                "detail": (
                    "YSE traces to 1900; Eduniversal ranks the MEM No. 5 in sustainable "
                    "development and environmental management."
                ),
            },
            {
                "label": "Interdisciplinary curriculum",
                "sentiment": "positive",
                "detail": (
                    "Two-year MEM blending natural and social sciences with 18-credit "
                    "specializations and cross-registration across Yale."
                ),
            },
            {
                "label": "Professional network",
                "sentiment": "positive",
                "detail": (
                    "Niche graduate reviews praise engaged cohorts and access to "
                    "environmental leaders on campus."
                ),
            },
            {
                "label": "Academic vs. technical tilt",
                "sentiment": "mixed",
                "detail": (
                    "Some students note a policy- and research-forward culture relative to "
                    "purely technical environmental-engineering programs."
                ),
            },
            {
                "label": "Cost of attendance",
                "sentiment": "caution",
                "detail": (
                    "Two-year residential tuition is published on YSE's site; aid varies "
                    "by program and background."
                ),
            },
        ],
        "sources": [
            {
                "label": "Yale School of the Environment — MEM",
                "url": "https://environment.yale.edu/academics/masters/mem",
            },
            {
                "label": "Eduniversal — Yale MEM ranking",
                "url": (
                    "https://www.best-masters.us/ranking-master-sustainable-development-and-"
                    "environmental-management/master-of-environmental-management-mem-yale-"
                    "university-yale-school-of-forestry-environmental-studies.html"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    **DEPTH_REVIEWS,
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
    if spec["degree_type"] == "bachelors":
        return dict(_REQ_UNDERGRAD)
    # All graduate/professional/doctoral programs share the generic Yale graduate set,
    # which points applicants to the program's own admissions page for exact deadlines.
    return dict(_REQ_GRAD_GENERIC)


# Harkness Tower leads the institution hero; see ``SCHOOL_OUTCOMES["campus_photos"]``.
_CAMPUS_PHOTO = SCHOOL_OUTCOMES["campus_photos"][0]["url"]


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
        # Every school gets a working feed (verified Yale News topic RSS + the Yale events
        # iCalendar, filtered to school-relevant items by keywords) so its Events & Updates
        # tab populates — overwriting any stale value on a pre-existing row.
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
    # Graduate/professional programs without a verified per-program tuition omit tuition_usd
    # (their cost_data carries a sourced "see the school's tuition page" record instead) —
    # never the undergraduate rate.
    spec = _SPEC_BY_SLUG.get(slug)
    if spec and spec["degree_type"] != "bachelors" and slug not in _COST_BY_SLUG:
        omitted.append("cost_data.tuition_usd")
    # content_sources is set on every program now (school feed + program keywords), so it
    # is never omitted.
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
        p.department = spec.get("department")
        p.duration_months = spec.get("duration_months")
        p.description_text = spec["description"]
        # Website: verified program/department page where available, else the owning
        # school's site.
        p.website_url = _WEBSITE_BY_SLUG.get(slug) or _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "in_person")
        # Every program gets a working feed: its school's verified Yale News topic RSS +
        # the Yale events iCalendar, filtered by program-naming keywords where defined
        # (else the school's keywords). This is why each program's Events & Updates tab
        # populates rather than sitting empty.
        _kw = _PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(
            _SCHOOL_FEED_SPEC[spec["school"]]["keywords"]
        )
        p.content_sources = _program_content(spec["school"], _kw)
        # Cost precedence: a verified per-program override → published Yale College rates for
        # undergraduate majors → a sourced "tuition varies, see the school page" record for
        # graduate/professional programs whose per-program tuition is not yet verified (their
        # tuition_usd is recorded omitted, never guessed and never set to the undergrad rate).
        cost_override = _COST_BY_SLUG.get(slug)
        if cost_override is not None:
            p.tuition = cost_override.get("tuition_usd")
            p.cost_data = dict(cost_override)
        elif spec["degree_type"] == "bachelors":
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
        else:
            p.tuition = None
            p.cost_data = {
                "note": (
                    "Tuition for this graduate/professional program varies and is published "
                    "on the school's official tuition page; a verified per-program figure is "
                    "not yet recorded here."
                ),
                "source": "Yale University Catalog — Tuition & Fees",
                "source_url": _SCHOOL_WEBSITE.get(spec["school"], "https://www.yale.edu"),
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
