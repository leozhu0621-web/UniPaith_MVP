"""Canonical Cornell University profile — the single source of truth.

Real, sourced data only (U.S. Dept. of Education College Scorecard, UNITID 190415 ·
NCES College Navigator / IPEDS · Cornell Institutional Research & Planning Common Data
Set 2024-25 · the official Cornell University Statement on the FY2025 endowment · the
official QS / Times Higher Education / U.S. News rankings · each college's official
leadership / about page and the Cornell course catalog · Cornell Career Services
First-Destination Annual Report 2023-24 · the College Scorecard Field-of-Study earnings
by CIP). ``apply(session)`` idempotently enriches the Cornell institution row, upserts
its real degree-granting colleges, and builds Cornell's program catalog across them.

Cornell's academic structure: a private Ivy League and land-grant research university
in Ithaca, New York, organized into endowed (private) colleges and four New York State
statutory/contract colleges, plus graduate and professional schools (two of them in New
York City). We model the units that own the degree programs onto the platform's
``School`` model:
  - College of Agriculture and Life Sciences (CALS) — statutory
  - College of Arts and Sciences — endowed
  - Charles H. Dyson School of Applied Economics and Management (SC Johnson) — contract
  - Samuel Curtis Johnson Graduate School of Management (SC Johnson) — endowed
  - Peter and Stephanie Nolan School of Hotel Administration (SC Johnson) — endowed
  - Cornell David A. Duffield College of Engineering — endowed
  - College of Human Ecology — statutory
  - School of Industrial and Labor Relations (ILR) — statutory
  - College of Architecture, Art, and Planning (AAP) — endowed
  - Cornell Ann S. Bowers College of Computing and Information Science — endowed
  - Cornell Jeb E. Brooks School of Public Policy — state-supported
  - Cornell Law School — endowed
  - College of Veterinary Medicine — statutory
  - Weill Cornell Medicine (New York City) — endowed

It **flushes but does not commit** — the caller (the Alembic data migration, the CLI
script, or the dev seed) owns the transaction. It is a **no-op** (returns ``False``)
when Cornell is absent, so it is safe to run against a fresh or CI database. Re-running
is safe: schools key off ``(institution_id, name)`` and programs off ``slug``; stale
rows are reconciled without breaking foreign keys.

This mirrors ``mit_profile`` / ``yale_profile`` so the migration, the standalone script,
and the dev seed all agree (DRY). Every figure traces to a public, citable source;
anything that could not be verified from a first-party or two-independent-source basis is
**omitted** (recorded in the relevant ``_standard.omitted`` list), never guessed.
Computer Science is the most-enriched undergraduate flagship (research areas, faculty,
class profile, and aggregated reviews), and the Johnson Two-Year MBA is the deeply
enriched graduate flagship (employment report, immersions, class profile, cost,
admissions, and aggregated reviews), mirroring MIT Sloan's MBAn in the reference
instance — with the honest caveats that the exact admitted-applicant integer for the
Fall-2024 cohort is not published in a first-party raw count (omitted), that the online /
hybrid professional master's degrees do not publish per-program tuition on a citable page
(omitted), and that Cornell reports first-destination outcomes university-wide rather than
per-program for most degrees (each catalog program omits the program-level employment rate
and industry mix except the Johnson MBA, which publishes a first-party employment report).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.cornell_ipeds_catalog import _IPEDS_CATALOG
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Cornell University"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-12"


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
    # The Fall-2024 first-year admitted-applicant integer is not published in a
    # first-party raw count (College Navigator reports only the percent; the Common Data
    # Set C1 cell did not render in text extraction). The applicant count is published, so
    # only the admits figure is omitted.
    "school_outcomes.flagship.admits",
]

# ── Institution-level data ────────────────────────────────────────────────
# Rankings are stored as {rank, year} objects. All three ranks are quoted from the
# official ranking bodies for the 2026 editions.
RANKING_DATA: dict = {
    # Federal IPEDS / College Scorecard ownership classification is private nonprofit;
    # Cornell is a private Ivy League university that also operates four New York State
    # statutory/land-grant contract colleges (a hybrid private/land-grant structure).
    "ownership_type": "private",
    # Accredited by the Middle States Commission on Higher Education (since 1921).
    "accreditor": "Middle States Commission on Higher Education",
    # Carnegie basic classification (R1).
    "carnegie_classification": "Doctoral Universities: Very High Research Activity",
    # QS World University Rankings 2026: #16 worldwide.
    "qs_world_university_rankings": {"rank": 16, "year": 2026},
    # THE World University Rankings 2026: =18 in the world.
    "times_higher_education": {"rank": 18, "year": 2026},
    # U.S. News Best Colleges (National Universities) 2026: #12 nationally.
    "us_news_national": {"rank": 12, "year": 2026},
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below is
# complete. Figures are College Scorecard (UNITID 190415) cross-checked against Cornell's
# Common Data Set 2024-25, NCES College Navigator (IPEDS), and Cornell's official
# statements where each publishes a metric.
SCHOOL_OUTCOMES: dict = {
    # College Scorecard overall admission rate (latest reported admissions year).
    "admit_rate": 0.0876,
    # College Scorecard average annual net price.
    "avg_net_price": 28690,
    # College Scorecard institution-wide median earnings 10 years after entry.
    "median_earnings_10yr": 104043,
    # College Scorecard four-year completion rate (150% of normal time).
    "completion_rate_4yr_150pct": 0.9538,
    # NCES College Navigator (IPEDS): first-year retention (Fall 2023 → Fall 2024) = 98%.
    "retention_rate_first_year": 0.98,
    # NCES College Navigator (IPEDS): six-year graduation rate (Fall 2018 cohort) = 95%.
    "graduation_rate_6yr": 0.95,
    "financial_aid": {
        # College Scorecard: 18.41% of undergraduates received a Pell grant; 17.81% took
        # federal student loans. Cornell meets 100% of demonstrated need and is need-blind
        # for U.S. applicants.
        "pell_grant_rate": 0.1841,
        "federal_loan_rate": 0.1781,
        # College Scorecard total annual cost of attendance (academic year).
        "cost_of_attendance": 88140,
    },
    # Undergraduate race/ethnicity (NCES College Navigator / IPEDS Fall 2024).
    "demographics": {
        "white": 0.31,
        "black": 0.07,
        "hispanic": 0.13,
        "asian": 0.27,
        "two_or_more": 0.06,
        "international": 0.10,
    },
    # SAT/ACT 25th-75th percentiles of enrolled first-years who submitted scores (NCES
    # College Navigator, Fall 2024; Cornell is test-optional, so submission rates vary).
    "test_scores": {
        "sat_reading_25_75": [730, 770],
        "sat_math_25_75": [770, 800],
        "act_25_75": [33, 35],
    },
    # Cornell main campus, Ithaca, New York.
    "location": {"lat": 42.4492, "lng": -76.4839},
    "campus_basics": {"location": "Ithaca, New York"},
    "scale": {
        # NCES College Navigator: 3,645 faculty (Fall 2024; 3,420 full-time + 225
        # part-time).
        "faculty_count": 3645,
        # NCES College Navigator / Cornell: 9:1 student-faculty ratio.
        "student_faculty_ratio": "9:1",
        # Cornell University Statement: endowment $11.8 billion at fiscal year-end
        # June 30, 2025 (FY2025, 12.3% net return).
        "endowment_usd": 11800000000,
    },
    # Cornell Career Services First-Destination Annual Report 2023-24 (Class of 2023,
    # university-wide; 74% knowledge rate): 69% employed + 24% in graduate/professional
    # school = 93% positive outcome.
    "employed_or_continuing_ed": 0.93,
    # Cornell Career Services Class of 2023 — employment by industry, rank order; the five
    # largest categories.
    "top_employer_industries": [
        "Financial Services",
        "Consulting / Professional Practice",
        "Technology",
        "Education",
        "Human Healthcare Services",
    ],
    "research": {
        "labs": [
            "Cornell Lab of Ornithology",
            "Cornell High Energy Synchrotron Source (CHESS)",
            "Cornell Center for Materials Research (CCMR)",
            "Kavli Institute at Cornell for Nanoscale Science (KIC)",
            "Cornell NanoScale Science and Technology Facility (CNF)",
            "Cornell Atkinson Center for Sustainability",
        ],
        "areas": [
            "Materials science & nanoscale engineering",
            "Accelerator-based & high-energy physics",
            "Ornithology, ecology & conservation science",
            "Plant science & agriculture",
            "Sustainability, climate & environmental science",
            "Computing & information science / AI",
            "Cell & molecular biology / life sciences",
            "Veterinary medicine & animal health",
        ],
        "lab_links": {
            "Cornell Lab of Ornithology": "https://www.birds.cornell.edu/home/",
            "Cornell High Energy Synchrotron Source (CHESS)": "https://www.chess.cornell.edu/",
            "Cornell Center for Materials Research (CCMR)": "https://www.ccmr.cornell.edu/",
            "Kavli Institute at Cornell for Nanoscale Science (KIC)": (
                "https://www.kicnano.cornell.edu/"
            ),
            "Cornell NanoScale Science and Technology Facility (CNF)": (
                "https://www.cnf.cornell.edu/"
            ),
            "Cornell Atkinson Center for Sustainability": "https://www.atkinson.cornell.edu/",
        },
    },
    "campus_life": {
        # Cornell's teams (the Big Red) compete in NCAA Division I (Ivy League; ECAC
        # Hockey).
        "athletics_division": "NCAA Division I (Ivy League)",
        "mascot": "Cornell Big Red",
        "housing": (
            "Two-year residential requirement: all first-year students live on North "
            "Campus; sophomores and upper-level students can join the West Campus House "
            "System (five faculty-in-residence houses)."
        ),
        "resources": [
            {"label": "Cornell Big Red Athletics", "url": "https://cornellbigred.com/"},
            {
                "label": "Cornell Housing & Residential Life",
                "url": "https://scl.cornell.edu/residential-life/housing",
            },
            {
                "label": "West Campus House System",
                "url": "https://westcampushousesystem.cornell.edu/",
            },
            {"label": "Cornell Student & Campus Life", "url": "https://scl.cornell.edu/"},
        ],
    },
    # Wikimedia Commons file page verified 2026-06-12: author Eustress, CC BY-SA 4.0.
    "media_credit": "Wikimedia Commons / Eustress (CC BY-SA 4.0)",
    "flagship": {
        # NCES College Navigator: 26,793 total students (Fall 2024) — 16,128 undergraduate
        # + 10,665 graduate and professional.
        "enrollment_total": 26793,
        # NCES College Navigator / IPEDS first-year admissions cycle (Fall 2024).
        "applicants": 62993,
        "admissions_cycle": "Entering class fall 2024 (NCES College Navigator / IPEDS)",
        # Founded April 27, 1865 (Morrill Land-Grant Act + Ezra Cornell / Andrew D. White).
        "founded_year": 1865,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Cornell, UNITID 190415)",
            "url": "https://collegescorecard.ed.gov/school/?190415-Cornell-University",
        },
        {
            "label": "NCES College Navigator — Cornell University (IPEDS id=190415)",
            "url": "https://nces.ed.gov/collegenavigator/?id=190415",
        },
        {
            "label": "Cornell Institutional Research & Planning — Common Data Set 2024-25",
            "url": "https://irp.cornell.edu/common-data-set",
        },
        {
            "label": "Cornell University Statement — Endowment FY2025 ($11.8B, 12.3% return)",
            "url": "https://statements.cornell.edu/2025/20251028-university-endowment.cfm",
        },
        {
            "label": "QS World University Rankings 2026 — Cornell University (#16)",
            "url": "https://www.topuniversities.com/universities/cornell-university",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — Cornell (=18)",
            "url": "https://www.timeshighereducation.com/world-university-rankings/cornell-university",
        },
        {
            "label": "U.S. News Best Colleges 2026 — Cornell University (#12 National)",
            "url": "https://www.usnews.com/best-colleges/cornell-university-2711",
        },
        {
            "label": "Cornell Career Services — First-Destination Annual Report 2023-24",
            "url": "https://career.cornell.edu/outcomes/",
        },
        {
            "label": "Cornell — 2025-26 budget parameters (tuition & cost of attendance)",
            "url": "https://news.cornell.edu/stories/2025/03/board-trustees-approves-2025-26-budget-parameters",
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it "Undergraduates");
# the total (26,793) lives in flagship.enrollment_total. 16,128 = College Navigator
# undergraduate enrollment (Fall 2024).
UNDERGRAD_COUNT = 16128

DESCRIPTION = (
    "Cornell University is a private Ivy League and land-grant research university in "
    "Ithaca, New York, founded in 1865 by Ezra Cornell and Andrew Dickson White on the "
    "principle of “any person … any study.” It enrolls about 16,100 "
    "undergraduates and roughly 10,700 graduate and professional students — some "
    "26,800 in all — and pairs the resources of a major research university and its "
    "3,645 faculty with a 9:1 student-faculty ratio.\n\n"
    "Cornell is organized into endowed (private) colleges and four New York State "
    "statutory/contract colleges, plus graduate and professional schools — among "
    "them the College of Arts and Sciences, the College of Agriculture and Life Sciences, "
    "the David A. Duffield College of Engineering, the Ann S. Bowers College of Computing "
    "and Information Science, the SC Johnson College of Business (the Dyson, Johnson and "
    "Nolan schools), the College of Human Ecology, the School of Industrial and Labor "
    "Relations, the College of Architecture, Art, and Planning, the Jeb E. Brooks School "
    "of Public Policy, Cornell Law School, the College of Veterinary Medicine, the New "
    "York City graduate campus Cornell Tech, and Weill Cornell Medicine. Its research is "
    "anchored by the Cornell Lab of Ornithology, the Cornell High Energy Synchrotron "
    "Source, and the Cornell Atkinson Center for Sustainability.\n\n"
    "Cornell ranks among the leading universities in the world: No. 12 among national "
    "universities by U.S. News, No. 16 in the world by QS, and No. 18 by Times Higher "
    "Education. It admits under 9% of first-year applicants and holds an endowment of "
    "$11.8 billion as of June 2025.\n\n"
    "Cornell meets 100% of demonstrated financial need for admitted undergraduates and is "
    "need-blind for U.S. applicants: the average net price is about $28,700 a year, 18% "
    "of undergraduates receive Pell grants, and the four New York State statutory colleges "
    "(Agriculture and Life Sciences, Human Ecology, Industrial and Labor Relations, and "
    "Veterinary Medicine) charge a lower tuition to New York residents. Among the Class of "
    "2023, 69% were employed and 24% had entered graduate or professional school within "
    "six months of graduation."
)

# ── The real degree-granting colleges/schools (display order) ──────────────
_CALS = "Cornell University College of Agriculture and Life Sciences"
_AS = "Cornell University College of Arts and Sciences"
_DYSON = "Charles H. Dyson School of Applied Economics and Management"
_JOHNSON = "Samuel Curtis Johnson Graduate School of Management"
_NOLAN = "Peter and Stephanie Nolan School of Hotel Administration"
_ENGINEERING = "Cornell David A. Duffield College of Engineering"
_HUMAN_ECOLOGY = "Cornell University College of Human Ecology"
_ILR = "Cornell University School of Industrial and Labor Relations"
_AAP = "Cornell University College of Architecture, Art, and Planning"
_BOWERS = "Cornell Ann S. Bowers College of Computing and Information Science"
_BROOKS = "Cornell Jeb E. Brooks School of Public Policy"
_LAW = "Cornell Law School"
_VET = "Cornell University College of Veterinary Medicine"
_WEILL = "Weill Cornell Medicine"

SCHOOLS: list[dict] = [
    {
        "name": _AS,
        "sort_order": 1,
        "description": (
            "Cornell's largest and most academically diverse college, part of the "
            "university since its 1865 founding. It grants the B.A. and Ph.D. across the "
            "humanities, natural sciences, social sciences and mathematics."
        ),
    },
    {
        "name": _ENGINEERING,
        "sort_order": 2,
        "description": (
            "Renamed the David A. Duffield College of Engineering in January 2026, "
            "Cornell Engineering traces to the 1870 Sibley College and grants B.S., "
            "M.Eng., M.S. and Ph.D. degrees across engineering disciplines."
        ),
    },
    {
        "name": _BOWERS,
        "sort_order": 3,
        "description": (
            "Established as a named college in December 2020 via Ann S. Bowers's gift, "
            "Cornell Bowers CIS comprises the departments of Computer Science, Information "
            "Science, and Statistics and Data Science, and is affiliated with Cornell Tech."
        ),
    },
    {
        "name": _CALS,
        "sort_order": 4,
        "description": (
            "A New York State statutory land-grant college (state-chartered 1904), CALS "
            "grants B.S., M.S. and Ph.D. degrees across agriculture, the life sciences, "
            "applied economics and environmental and global development sciences."
        ),
    },
    {
        "name": _DYSON,
        "sort_order": 5,
        "description": (
            "Part of the Cornell SC Johnson College of Business and rooted in CALS, the "
            "Dyson School (founded 1911) grants applied-economics and management degrees "
            "and is a New York State contract unit."
        ),
    },
    {
        "name": _JOHNSON,
        "sort_order": 6,
        "description": (
            "The graduate management school of the Cornell SC Johnson College of Business "
            "(founded 1946), Johnson grants the MBA and specialized management master's "
            "degrees, including the residential and Cornell Tech MBA and Executive MBA "
            "formats."
        ),
    },
    {
        "name": _NOLAN,
        "sort_order": 7,
        "description": (
            "Founded in 1922 as the world's first four-year collegiate school of hotel "
            "administration and now part of the SC Johnson College of Business, the Nolan "
            "School grants hospitality-management degrees."
        ),
    },
    {
        "name": _ILR,
        "sort_order": 8,
        "description": (
            "Chartered by New York State in 1945 as the first four-year school of its "
            "kind, the ILR School (a statutory college) grants degrees in the study of "
            "work, labor, employment and organizations."
        ),
    },
    {
        "name": _HUMAN_ECOLOGY,
        "sort_order": 9,
        "description": (
            "A New York State statutory college founded in 1925, the College of Human "
            "Ecology grants degrees in human development, nutrition and health, design and "
            "environmental analysis, policy analysis and management, and fiber science."
        ),
    },
    {
        "name": _AAP,
        "sort_order": 10,
        "description": (
            "Home to the first four-year architecture program in the United States (1871), "
            "the College of Architecture, Art, and Planning grants degrees in "
            "architecture, fine art, and urban and regional planning."
        ),
    },
    {
        "name": _BROOKS,
        "sort_order": 11,
        "description": (
            "Launched in fall 2021, the Jeb E. Brooks School of Public Policy grants "
            "public-policy and public-administration degrees (MPA, EMPA, the Sloan health "
            "administration programs, and undergraduate public policy)."
        ),
    },
    {
        "name": _LAW,
        "sort_order": 12,
        "description": (
            "Founded in 1887, Cornell Law School grants the J.D., LL.M. and J.S.D., along "
            "with an online Master of Science in Legal Studies, and is home to the Legal "
            "Information Institute."
        ),
    },
    {
        "name": _VET,
        "sort_order": 13,
        "description": (
            "Chartered in 1894 as the first statutory college of the SUNY system, the "
            "College of Veterinary Medicine grants the D.V.M. and graduate degrees in "
            "veterinary and biomedical sciences."
        ),
    },
    {
        "name": _WEILL,
        "sort_order": 14,
        "description": (
            "Cornell's New York City medical school (chartered 1898), Weill Cornell "
            "Medicine grants the M.D. and, through its Graduate School of Medical "
            "Sciences, biomedical Ph.D. and M.S. degrees."
        ),
    },
]

# Each school's official website (verified to resolve at author time).
_SCHOOL_WEBSITE: dict[str, str] = {
    _AS: "https://as.cornell.edu/",
    _ENGINEERING: "https://www.duffield.cornell.edu/",
    _BOWERS: "https://www.cis.cornell.edu/",
    _CALS: "https://cals.cornell.edu/",
    _DYSON: "https://dyson.cornell.edu/",
    _JOHNSON: "https://www.johnson.cornell.edu/",
    _NOLAN: "https://sha.cornell.edu/",
    _ILR: "https://www.ilr.cornell.edu/",
    _HUMAN_ECOLOGY: "https://www.human.cornell.edu/",
    _AAP: "https://aap.cornell.edu/",
    _BROOKS: "https://publicpolicy.cornell.edu/",
    _LAW: "https://www.lawschool.cornell.edu/",
    _VET: "https://www.vet.cornell.edu/",
    _WEILL: "https://weill.cornell.edu/",
}

# Rich, sourced About-tab content per school. Deans + titles are quoted from each school's
# official leadership page (verified 2026-06-10). Founding years come from each school's
# official history/about page. Notable-faculty rosters are not published uniformly per
# school and are omitted rather than hand-picked (recorded in _ABOUT_OMITTED).
_ABOUT_DETAIL: dict[str, dict] = {
    _AS: {
        "founded": 1865,
        "leadership": (
            "Peter John Loewen — Harold Tanner Dean of the College of Arts and "
            "Sciences (23rd dean, since August 2024)"
        ),
        "research_centers": [
            "Society for the Humanities",
            "Cornell Center for Social Sciences",
            "Laboratory for Elementary-Particle Physics (LEPP)",
        ],
        "source": {
            "label": "Cornell College of Arts and Sciences — Leadership",
            "url": "https://as.cornell.edu/about/leadership",
        },
    },
    _ENGINEERING: {
        "founded": 1870,
        "leadership": "Lynden A. Archer — Joseph Silbert Dean of Engineering",
        "research_centers": [
            "Cornell NanoScale Science and Technology Facility (CNF)",
            "Cornell High Energy Synchrotron Source (CHESS)",
            "Cornell Center for Materials Research (CCMR)",
        ],
        "source": {
            "label": "Cornell Duffield College of Engineering — College Leadership",
            "url": "https://www.duffield.cornell.edu/college-leadership/",
        },
    },
    _BOWERS: {
        "founded": 2020,
        "leadership": (
            "Sorin Lerner — Dean of the Cornell Ann S. Bowers College of Computing "
            "and Information Science (since November 2025)"
        ),
        "research_centers": [
            "Department of Computer Science",
            "Department of Information Science",
            "Department of Statistics and Data Science",
        ],
        "source": {
            "label": "Cornell Chronicle — Sorin Lerner named dean of Cornell Bowers",
            "url": "https://news.cornell.edu/stories/2025/06/sorin-lerner-named-new-dean-cornell-bowers",
        },
    },
    _CALS: {
        "founded": 1904,
        "leadership": (
            "Benjamin Z. Houlton — Ronald P. Lynch Dean of the College of Agriculture "
            "and Life Sciences"
        ),
        "research_centers": [
            "Cornell Atkinson Center for Sustainability",
            "Cornell Lab of Ornithology",
            "Boyce Thompson Institute (affiliated)",
        ],
        "source": {
            "label": "Cornell CALS — College Leadership",
            "url": "https://cals.cornell.edu/about/college-leadership",
        },
    },
    _DYSON: {
        "founded": 1911,
        "leadership": (
            "Andrew Karolyi — Charles Field Knight Dean of the Cornell SC Johnson "
            "College of Business (umbrella college containing the Dyson School)"
        ),
        "research_centers": [
            "Cornell SC Johnson College of Business",
            "Charles H. Dyson School of Applied Economics and Management",
        ],
        "source": {
            "label": "Cornell Dyson School — History",
            "url": "https://dyson.cornell.edu/about/history/",
        },
    },
    _JOHNSON: {
        "founded": 1946,
        "leadership": (
            "Andrew Karolyi — Charles Field Knight Dean of the Cornell SC Johnson "
            "College of Business"
        ),
        "research_centers": [
            "Parker Center for Investment Research",
            "Center for Sustainable Global Enterprise",
        ],
        "source": {
            "label": "Cornell SC Johnson College of Business — Dean's Welcome",
            "url": "https://business.cornell.edu/about/deans-welcome/",
        },
    },
    _NOLAN: {
        "founded": 1922,
        "leadership": (
            "Andrew Karolyi — Charles Field Knight Dean of the Cornell SC Johnson "
            "College of Business (umbrella college containing the Nolan School)"
        ),
        "research_centers": [
            "Center for Hospitality Research",
            "Cornell Institute for Healthy Futures",
        ],
        "source": {
            "label": "Cornell Nolan School of Hotel Administration — About",
            "url": "https://sha.cornell.edu/about/",
        },
    },
    _ILR: {
        "founded": 1945,
        "leadership": (
            "Alexander J.S. Colvin — Kenneth F. Kahn '69 Dean of the ILR School"
        ),
        "research_centers": [
            "The Worker Institute",
            "Scheinman Institute on Conflict Resolution",
            "ILR Buffalo Co-Lab",
        ],
        "source": {
            "label": "Cornell ILR School — Dean Alexander Colvin",
            "url": "https://www.ilr.cornell.edu/people/alexander-james-colvin",
        },
    },
    _HUMAN_ECOLOGY: {
        "founded": 1925,
        "leadership": (
            "Rachel Dunifon — Rebecca Q. and James C. Morgan Dean of the College of "
            "Human Ecology"
        ),
        "research_centers": [
            "Bronfenbrenner Center for Translational Research",
            "Cornell Institute for Healthy Futures",
        ],
        "source": {
            "label": "Cornell College of Human Ecology — Administration",
            "url": "https://www.human.cornell.edu/about/administration",
        },
    },
    _AAP: {
        "founded": 1871,
        "leadership": (
            "J. Meejin Yoon — Gale and Ira Drukier Dean of the College of "
            "Architecture, Art, and Planning"
        ),
        "research_centers": [
            "Cornell AAP NYC",
            "Cornell Mui Ho Center for Cities",
        ],
        "source": {
            "label": "Cornell AAP — Leadership",
            "url": "https://aap.cornell.edu/about/who-we-are/leadership",
        },
    },
    _BROOKS: {
        "founded": 2021,
        "leadership": (
            "Colleen L. Barry — Dean of the Cornell Jeb E. Brooks School of Public "
            "Policy"
        ),
        "research_centers": [
            "Cornell Institute for Public Affairs (CIPA)",
            "Center for the Study of Inequality",
        ],
        "source": {
            "label": "Cornell Jeb E. Brooks School of Public Policy — About",
            "url": "https://publicpolicy.cornell.edu/about-us/",
        },
    },
    _LAW: {
        "founded": 1887,
        "leadership": (
            "Jens David Ohlin — Allan R. Tessler Dean of Cornell Law School"
        ),
        "research_centers": [
            "Legal Information Institute (LII)",
            "Clarke Program in East Asian Law and Culture",
        ],
        "source": {
            "label": "Cornell Law School — Office of the Dean",
            "url": "https://www.lawschool.cornell.edu/about-cornell-law-school/office-of-the-dean/",
        },
    },
    _VET: {
        "founded": 1894,
        "leadership": (
            "Lorin D. Warnick — Austin O. Hooey Dean of Veterinary Medicine"
        ),
        "research_centers": [
            "Baker Institute for Animal Health",
            "Animal Health Diagnostic Center",
            "Cornell Feline Health Center",
        ],
        "source": {
            "label": "Cornell College of Veterinary Medicine — Leadership",
            "url": "https://www.vet.cornell.edu/about-us/leadership",
        },
    },
    _WEILL: {
        "founded": 1898,
        "leadership": (
            "Robert A. Harrington — Stephen and Suzanne Weiss Dean of Weill Cornell "
            "Medicine (since September 2024)"
        ),
        "research_centers": [
            "Englander Institute for Precision Medicine",
            "Sandra and Edward Meyer Cancer Center",
            "Feil Family Brain & Mind Research Institute",
        ],
        "source": {
            "label": "Weill Cornell Medicine — Office of the Dean",
            "url": "https://news.weill.cornell.edu/units/office-dean",
        },
    },
}

# About-detail fields omitted per school (verified-unavailable), recorded in each school's
# _standard.omitted. Notable-faculty rosters are omitted for every school (not published
# uniformly per college).
_FACULTY_OMIT = ["about_detail.faculty"]
_ABOUT_OMITTED: dict[str, list[str]] = {name: list(_FACULTY_OMIT) for name in _SCHOOL_WEBSITE}

# ── Channel feeds + official social links ──────────────────────────────────
# Verified server-fetchable RSS (HTTP 200, 2026-06-11):
#   • Ithaca campus: https://news.cornell.edu/taxonomy/term/63/feed
#   • Bowers CIS: https://news.cornell.edu/taxonomy/term/14256/feed
#   • Engineering: https://engineering.cornell.edu/feed/
#   • Johnson / SC Johnson: https://www.johnson.cornell.edu/feed/
#   • Hotel School: https://sha.cornell.edu/feed/
#   • Law School: https://www.lawschool.cornell.edu/feed/
#   • SC Johnson umbrella: https://business.cornell.edu/feed/
_CORNELL_ITHACA_RSS = "https://news.cornell.edu/taxonomy/term/63/feed"
_BOWERS_RSS = "https://news.cornell.edu/taxonomy/term/14256/feed"
_ENGINEERING_RSS = "https://engineering.cornell.edu/feed/"
_JOHNSON_RSS = "https://www.johnson.cornell.edu/feed/"
_NOLAN_RSS = "https://sha.cornell.edu/feed/"
_LAW_RSS = "https://www.lawschool.cornell.edu/feed/"
_BUSINESS_RSS = "https://business.cornell.edu/feed/"
_CORNELL_EVENTS_ICS = {"url": "https://events.cornell.edu/calendar/1.ics", "type": "ical"}

_SOCIAL_CORNELL = {
    "instagram": "https://www.instagram.com/cornelluniversity/",
    "linkedin": "https://www.linkedin.com/school/cornell-university/",
    "x": "https://x.com/Cornell",
    "youtube": "https://www.youtube.com/c/cornell",
    "facebook": "https://www.facebook.com/Cornell/",
}
_SOCIAL_JOHNSON = {
    "instagram": "https://www.instagram.com/cornelljohnson/",
    "linkedin": "https://www.linkedin.com/school/cornell-johnson-graduate-school-of-management/",
    "x": "https://x.com/CornellJohnson",
    "youtube": "https://www.youtube.com/user/CornellJohnson",
    "facebook": "https://www.facebook.com/CornellJohnson/",
}
_SOCIAL_LAW = {
    "instagram": "https://www.instagram.com/cornelllaw/",
    "linkedin": "https://www.linkedin.com/school/cornell-law-school/",
    "x": "https://x.com/CornellLaw",
    "facebook": "https://www.facebook.com/CornellLawSchool/",
}

# Each school's verified RSS + keyword filter. Schools without their own fetchable RSS
# inherit the Ithaca-campus feed filtered by school-naming keywords.
_SCHOOL_FEED_SPEC: dict[str, dict] = {
    _AS: {
        "rss": _CORNELL_ITHACA_RSS,
        "keywords": ["Arts and Sciences", "humanities", "social sciences"],
    },
    _ENGINEERING: {
        "rss": _ENGINEERING_RSS,
        "keywords": ["engineering", "Duffield", "Cornell Engineering"],
    },
    _BOWERS: {
        "rss": _BOWERS_RSS,
        "keywords": ["Bowers", "computer science", "information science", "computing"],
    },
    _CALS: {
        "rss": _CORNELL_ITHACA_RSS,
        "keywords": ["CALS", "agriculture", "life sciences", "plant science"],
    },
    _DYSON: {"rss": _BUSINESS_RSS, "keywords": ["Dyson", "applied economics", "business"]},
    _JOHNSON: {
        "rss": _JOHNSON_RSS,
        "keywords": ["Johnson", "MBA", "business school", "management"],
        "social": _SOCIAL_JOHNSON,
    },
    _NOLAN: {
        "rss": _NOLAN_RSS,
        "keywords": ["Hotel Administration", "hospitality", "SHA", "hotel"],
    },
    _HUMAN_ECOLOGY: {
        "rss": _CORNELL_ITHACA_RSS,
        "keywords": ["Human Ecology", "human development", "nutrition"],
    },
    _ILR: {
        "rss": _CORNELL_ITHACA_RSS,
        "keywords": ["ILR", "labor relations", "industrial relations", "workplace"],
    },
    _AAP: {"rss": _CORNELL_ITHACA_RSS, "keywords": ["architecture", "planning", "AAP", "art"]},
    _BROOKS: {
        "rss": _CORNELL_ITHACA_RSS,
        "keywords": ["Brooks School", "public policy", "policy"],
    },
    _LAW: {
        "rss": _LAW_RSS,
        "keywords": ["Cornell Law", "law school", "legal"],
        "social": _SOCIAL_LAW,
    },
    _VET: {
        "rss": _CORNELL_ITHACA_RSS,
        "keywords": ["veterinary", "Vet college", "animal health", "DVM"],
    },
    _WEILL: {
        "rss": _CORNELL_ITHACA_RSS,
        "keywords": ["Weill Cornell", "medical school", "medicine", "physicians"],
    },
}

_KW_STOP = {"and", "of", "the", "in", "for", "with", "master", "doctor", "bachelor", "studies"}


def _school_content(name: str) -> dict:
    """A school's content_sources: its verified RSS feed filtered by school keywords."""
    spec = _SCHOOL_FEED_SPEC[name]
    return {
        "news_rss": spec["rss"],
        "news_url": _SCHOOL_WEBSITE.get(name, "https://www.cornell.edu"),
        "news_curated": False,
        "events_feed": dict(_CORNELL_EVENTS_ICS),
        "keywords": list(spec["keywords"]),
        "social": spec.get("social", _SOCIAL_CORNELL),
    }


def _program_keywords(spec: dict) -> list[str]:
    """Program keywords = distinctive discipline term(s) from the program name layered
    on the school's keywords, so the program tab stays relevant yet never empty."""
    school_kw = list(_SCHOOL_FEED_SPEC[spec["school"]]["keywords"])
    name = spec["program_name"].replace("&", " ").replace("/", " ")
    terms = [w for w in name.split() if len(w) > 3 and w.lower() not in _KW_STOP]
    program_term = " ".join(terms[:3]).strip()
    return ([program_term] if program_term else []) + school_kw


def _program_content(spec: dict) -> dict:
    """A program's content_sources: its school's shared feed refined by program keywords."""
    base = _school_content(spec["school"])
    base["keywords"] = _program_keywords(spec)
    return base


# Institution-wide feeds (Cornell Chronicle Ithaca RSS + the official events iCal feed) +
# the official Cornell University social accounts. The daily ingest fills Updates + Events
# from news_rss + events_feed; social is rendered on the profile.
_INSTITUTION_CONTENT: dict = {
    "news_rss": _CORNELL_ITHACA_RSS,
    "news_url": "https://news.cornell.edu",
    "news_curated": False,
    "events_feed": dict(_CORNELL_EVENTS_ICS),
    "social": dict(_SOCIAL_CORNELL),
}

# Computer Science keyword-relevant feed (the flagship program). The Cornell Chronicle
# Computing & Information Sciences taxonomy feed surfaces CS/Bowers news.
_CS_CONTENT: dict = {
    "news_rss": _BOWERS_RSS,
    "events_feed": dict(_CORNELL_EVENTS_ICS),
    "keywords": [
        "computer science",
        "cornell bowers",
        "machine learning",
        "artificial intelligence",
    ],
    "social": dict(_SOCIAL_CORNELL),
}

# Johnson Two-Year MBA keyword-relevant feed (the management-school flagship).
_MBA_CONTENT: dict = {
    "news_rss": _JOHNSON_RSS,
    "news_url": "https://www.johnson.cornell.edu/",
    "news_curated": False,
    "events_feed": dict(_CORNELL_EVENTS_ICS),
    "keywords": ["Johnson", "MBA", "Two-Year MBA", "business school", "management"],
    "social": dict(_SOCIAL_JOHNSON),
}

_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "cornell-mba": ["Johnson", "MBA", "Two-Year MBA", "business school"],
    "cornell-computer-science-bs": [
        "computer science",
        "cornell bowers",
        "machine learning",
        "artificial intelligence",
    ],
    "cornell-computer-science-ms": ["computer science", "graduate CS", "Bowers"],
    "cornell-jd": ["Cornell Law", "J.D.", "law school"],
    "cornell-md": ["Weill Cornell", "medical school", "M.D."],
    "cornell-dvm": ["veterinary", "DVM", "Vet college"],
    "cornell-march": ["architecture", "M.Arch", "AAP"],
}

# ── The program catalog (real majors/degrees, organized by school) ─────────
# slug = idempotency key. The residential set is the College Scorecard Field-of-Study list
# for UNITID 190415; the online/hybrid degrees and the four flagship professional degrees
# (J.D., D.V.M., M.Arch, M.D.) are added from each school's official catalog so every real
# college is represented. delivery_format is set on every program.
PROGRAMS: list[dict] = [
    # ── Cornell Ann S. Bowers College of Computing and Information Science ──
    {
        "slug": "cornell-computer-science-bs",
        "school": _BOWERS,
        "program_name": "Computer Science (B.S.)",
        "degree_type": "bachelors",
        "cip": "11.07",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": (
            "Cornell's flagship computing major — offered as the B.S. (College of "
            "Engineering) and the B.A. (College of Arts and Sciences), spanning theory, "
            "systems, AI and machine learning, taught through the Bowers College of "
            "Computing and Information Science."
        ),
    },
    {
        "slug": "cornell-computer-science-ms",
        "school": _BOWERS,
        "program_name": "Computer Science (M.S.)",
        "degree_type": "masters",
        "cip": "11.07",
        "duration_months": 24,
        "delivery_format": "in_person",
        "description": (
            "The graduate Computer Science master's in the Bowers College, covering "
            "advanced systems, theory, artificial intelligence and applications."
        ),
    },
    {
        "slug": "cornell-information-science-bs",
        "school": _BOWERS,
        "program_name": "Computing and Information Sciences (B.S.)",
        "degree_type": "bachelors",
        "cip": "11.01",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": (
            "Information science — the study of computing in social, technical and "
            "design contexts, from data science to human-computer interaction."
        ),
    },
    {
        "slug": "cornell-information-science-ms",
        "school": _BOWERS,
        "program_name": "Computing and Information Sciences (M.S.)",
        "degree_type": "masters",
        "cip": "11.01",
        "duration_months": 24,
        "delivery_format": "in_person",
        "description": (
            "The graduate Information Science master's, spanning data science, "
            "human-computer interaction and the social study of computing."
        ),
    },
    # ── Cornell David A. Duffield College of Engineering ──
    {
        "slug": "cornell-electrical-computer-eng-bs",
        "school": _ENGINEERING,
        "program_name": "Electrical and Computer Engineering (B.S.)",
        "degree_type": "bachelors",
        "cip": "14.10",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": (
            "Electrical and computer engineering — circuits, signals, devices, "
            "computer systems and communications."
        ),
    },
    {
        "slug": "cornell-electrical-computer-eng-ms",
        "school": _ENGINEERING,
        "program_name": "Electrical and Computer Engineering (M.S.)",
        "degree_type": "masters",
        "cip": "14.10",
        "duration_months": 24,
        "delivery_format": "in_person",
        "description": (
            "The research master's in electrical and computer engineering, across "
            "devices, systems, signal processing and communications."
        ),
    },
    {
        "slug": "cornell-mechanical-eng-bs",
        "school": _ENGINEERING,
        "program_name": "Mechanical Engineering (B.S.)",
        "degree_type": "bachelors",
        "cip": "14.19",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": (
            "Mechanical engineering — mechanics, thermal-fluids, dynamics and "
            "controls, materials and design."
        ),
    },
    {
        "slug": "cornell-operations-research-ms",
        "school": _ENGINEERING,
        "program_name": "Operations Research and Information Engineering (M.S.)",
        "degree_type": "masters",
        "cip": "14.37",
        "duration_months": 24,
        "delivery_format": "in_person",
        "description": (
            "Operations research and information engineering — optimization, applied "
            "probability, statistics and financial engineering."
        ),
    },
    {
        "slug": "cornell-systems-eng-ms",
        "school": _ENGINEERING,
        "program_name": "Systems Engineering (M.S.)",
        "degree_type": "masters",
        "cip": "14.27",
        "duration_months": 24,
        "delivery_format": "in_person",
        "description": (
            "Systems engineering — the design, modeling and management of complex "
            "engineered systems."
        ),
    },
    {
        "slug": "cornell-meng-ms",
        "school": _ENGINEERING,
        "program_name": "Master of Engineering (M.Eng.)",
        "degree_type": "masters",
        "cip": "15.15",
        "duration_months": 12,
        "delivery_format": "in_person",
        "description": (
            "The professional Master of Engineering — a course-based, one-year "
            "degree across Cornell Engineering's fields, with an engineering project."
        ),
    },
    # ── College of Arts and Sciences ──
    {
        "slug": "cornell-economics-bs",
        "school": _AS,
        "program_name": "Economics",
        "degree_type": "bachelors",
        "cip": "45.06",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": "Economics — micro, macro, econometrics and economic policy.",
    },
    {
        "slug": "cornell-political-science-bs",
        "school": _AS,
        "program_name": "Government (Political Science)",
        "degree_type": "bachelors",
        "cip": "45.10",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": (
            "Government — American politics, comparative politics, international "
            "relations and political theory."
        ),
    },
    {
        "slug": "cornell-mathematics-bs",
        "school": _AS,
        "program_name": "Mathematics",
        "degree_type": "bachelors",
        "cip": "27.01",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": "Mathematics — analysis, algebra, geometry, topology and logic.",
    },
    {
        "slug": "cornell-biology-bs",
        "school": _AS,
        "program_name": "Biological Sciences",
        "degree_type": "bachelors",
        "cip": "26.01",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": (
            "Biological sciences — a college-spanning major in genetics, cell and "
            "molecular biology, ecology and physiology (offered jointly with CALS)."
        ),
    },
    # ── College of Agriculture and Life Sciences (CALS) ──
    {
        "slug": "cornell-biomedical-sciences-bs",
        "school": _CALS,
        "program_name": "Biological and Biomedical Sciences",
        "degree_type": "bachelors",
        "cip": "26.99",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": (
            "Biological and biomedical sciences in CALS — from molecular and "
            "organismal biology to applied life-science fields."
        ),
    },
    # ── Charles H. Dyson School of Applied Economics and Management ──
    {
        "slug": "cornell-applied-economics-bs",
        "school": _DYSON,
        "program_name": "Applied Economics and Management",
        "degree_type": "bachelors",
        "cip": "01.01",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": (
            "Applied economics and management — the Dyson School's AACSB-accredited "
            "undergraduate business degree, grounded in applied economics."
        ),
    },
    # ── Samuel Curtis Johnson Graduate School of Management ──
    {
        "slug": "cornell-mba",
        "school": _JOHNSON,
        "program_name": "Two-Year MBA",
        "degree_type": "masters",
        "cip": "52.02",
        "duration_months": 24,
        "delivery_format": "in_person",
        "description": (
            "Cornell's flagship Two-Year MBA at the Samuel Curtis Johnson Graduate "
            "School of Management — a full-time residential program in Ithaca with "
            "semester-long immersions, a summer internship, and elective access across "
            "Cornell's graduate schools and Cornell Tech in New York City."
        ),
    },
    {
        "slug": "cornell-business-administration-ms",
        "school": _JOHNSON,
        "program_name": "Business Administration and Management (M.S.)",
        "degree_type": "masters",
        "cip": "52.02",
        "duration_months": 12,
        "delivery_format": "in_person",
        "description": (
            "A specialized management master's in the Johnson School covering business "
            "administration, analytics and management."
        ),
    },
    # ── Peter and Stephanie Nolan School of Hotel Administration ──
    {
        "slug": "cornell-hotel-administration-bs",
        "school": _NOLAN,
        "program_name": "Hotel Administration",
        "degree_type": "bachelors",
        "cip": "52.09",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": (
            "Hospitality administration — the Nolan School's flagship undergraduate "
            "degree, the original four-year collegiate hospitality program."
        ),
    },
    # ── School of Industrial and Labor Relations (ILR) ──
    {
        "slug": "cornell-ilr-bs",
        "school": _ILR,
        "program_name": "Industrial and Labor Relations",
        "degree_type": "bachelors",
        "cip": "52.10",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": (
            "Industrial and labor relations — the ILR School's interdisciplinary "
            "undergraduate degree in work, labor markets, HR and organizations."
        ),
    },
    {
        "slug": "cornell-ilr-ms",
        "school": _ILR,
        "program_name": "Human Resources Management (M.S. / M.I.L.R.)",
        "degree_type": "masters",
        "cip": "52.10",
        "duration_months": 24,
        "delivery_format": "in_person",
        "description": (
            "The ILR School's graduate degree in human resources and labor relations "
            "(Master of Industrial and Labor Relations)."
        ),
    },
    # ── College of Human Ecology ──
    {
        "slug": "cornell-human-development-bs",
        "school": _HUMAN_ECOLOGY,
        "program_name": "Human Development",
        "degree_type": "bachelors",
        "cip": "19.07",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": (
            "Human development — the science of development across the lifespan, in "
            "the College of Human Ecology."
        ),
    },
    # ── Cornell Jeb E. Brooks School of Public Policy ──
    {
        "slug": "cornell-mpa-ms",
        "school": _BROOKS,
        "program_name": "Master of Public Administration (M.P.A.)",
        "degree_type": "masters",
        "cip": "44.04",
        "duration_months": 24,
        "delivery_format": "in_person",
        "description": (
            "The Cornell Institute for Public Affairs MPA — a two-year, multidisciplinary "
            "professional degree in public and nonprofit policy and management."
        ),
    },
    # ── Online / hybrid professional degrees ──
    {
        "slug": "cornell-legal-studies-ms-online",
        "school": _LAW,
        "program_name": "Master of Science in Legal Studies (Online)",
        "degree_type": "masters",
        "cip": "22.02",
        "duration_months": 24,
        "delivery_format": "online",
        "description": (
            "Cornell Law School's fully online Master of Science in Legal Studies — "
            "legal reasoning and frameworks for professionals who do not intend to practice "
            "law."
        ),
    },
    {
        "slug": "cornell-emba-americas",
        "school": _JOHNSON,
        "program_name": "Cornell Executive MBA Americas",
        "degree_type": "masters",
        "cip": "52.02",
        "duration_months": 17,
        "delivery_format": "hybrid",
        "description": (
            "A hybrid Executive MBA delivered through weekend courses with synchronous "
            "online instruction plus residential sessions, for working professionals across "
            "the Americas."
        ),
    },
    {
        "slug": "cornell-engineering-management-meng-online",
        "school": _ENGINEERING,
        "program_name": "Master of Engineering in Engineering Management (Hybrid)",
        "degree_type": "masters",
        "cip": "15.15",
        "duration_months": 24,
        "delivery_format": "hybrid",
        "description": (
            "A hybrid Master of Engineering in Engineering Management combining online "
            "coursework with annual one-week on-campus intensive sessions."
        ),
    },
    {
        "slug": "cornell-emha-online",
        "school": _BROOKS,
        "program_name": "Executive Master of Health Administration (Hybrid)",
        "degree_type": "masters",
        "cip": "51.07",
        "duration_months": 18,
        "delivery_format": "hybrid",
        "description": (
            "The Sloan Program's Executive Master of Health Administration — a "
            "blended 18-month degree mixing synchronous and asynchronous online coursework "
            "with on-campus intensives, for working health-care leaders."
        ),
    },
    {
        "slug": "cornell-empa-online",
        "school": _BROOKS,
        "program_name": "Executive Master of Public Administration (Hybrid)",
        "degree_type": "masters",
        "cip": "44.04",
        "duration_months": 18,
        "delivery_format": "hybrid",
        "description": (
            "The Brooks School's Executive Master of Public Administration — an "
            "18-month blended program for working public-sector and nonprofit "
            "professionals."
        ),
    },
    # ── Flagship professional degrees (one per otherwise-unrepresented school) ──
    {
        "slug": "cornell-jd",
        "school": _LAW,
        "program_name": "Juris Doctor (J.D.)",
        "degree_type": "professional",
        "cip": "22.01",
        "duration_months": 36,
        "delivery_format": "in_person",
        "description": (
            "Cornell Law School's three-year Juris Doctor — a small, collegial "
            "professional law degree emphasizing lawyering in the best sense."
        ),
    },
    {
        "slug": "cornell-dvm",
        "school": _VET,
        "program_name": "Doctor of Veterinary Medicine (D.V.M.)",
        "degree_type": "professional",
        "cip": "51.24",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": (
            "The College of Veterinary Medicine's four-year D.V.M. — a top-ranked "
            "professional program in veterinary clinical and biomedical science."
        ),
    },
    {
        "slug": "cornell-march",
        "school": _AAP,
        "program_name": "Master of Architecture (M.Arch I)",
        "degree_type": "masters",
        "cip": "04.02",
        "duration_months": 42,
        "delivery_format": "in_person",
        "description": (
            "The College of Architecture, Art, and Planning's professional Master of "
            "Architecture (M.Arch I), a STEM-designated accredited degree."
        ),
    },
    {
        "slug": "cornell-md",
        "school": _WEILL,
        "program_name": "Doctor of Medicine (M.D.)",
        "degree_type": "professional",
        "cip": "51.12",
        "duration_months": 48,
        "delivery_format": "in_person",
        "description": (
            "Weill Cornell Medicine's four-year M.D. — the New York City medical "
            "degree of Cornell University, taught alongside its biomedical graduate school."
        ),
    },
]

_EXISTING_SLUGS = {p["slug"] for p in PROGRAMS}


def _build_catalog() -> list[dict]:
    """Append breadth-first program nodes from the College Scorecard Field-of-Study list."""
    out: list[dict] = []
    seen = set(_EXISTING_SLUGS)
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


PROGRAMS += _build_catalog()
for _p in PROGRAMS:
    _p.setdefault("delivery_format", "in_person")

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

# Full official program names (program-page title); equal to the program name here.
_FULL_NAME_BY_SLUG: dict[str, str] = {p["slug"]: p["program_name"] for p in PROGRAMS}

# Official program/department/school home pages.
_WEBSITE_BY_SLUG: dict[str, str] = {
    "cornell-computer-science-bs": "https://www.cs.cornell.edu/undergrad",
    "cornell-computer-science-ms": "https://www.cs.cornell.edu/masters",
    "cornell-information-science-bs": "https://infosci.cornell.edu/undergraduate",
    "cornell-information-science-ms": "https://infosci.cornell.edu/academics/masters",
    "cornell-electrical-computer-eng-bs": "https://www.ece.cornell.edu/ece/programs/undergraduate-programs",
    "cornell-electrical-computer-eng-ms": "https://www.ece.cornell.edu/ece/programs/graduate-programs",
    "cornell-mechanical-eng-bs": "https://www.mae.cornell.edu/mae/programs/undergraduate-programs",
    "cornell-operations-research-ms": "https://www.orie.cornell.edu/",
    "cornell-systems-eng-ms": "https://www.systemseng.cornell.edu/se",
    "cornell-meng-ms": "https://www.engineering.cornell.edu/students/graduate-students/meng-programs",
    "cornell-economics-bs": "https://economics.cornell.edu/",
    "cornell-political-science-bs": "https://government.cornell.edu/",
    "cornell-mathematics-bs": "https://math.cornell.edu/",
    "cornell-biology-bs": "https://biology.cornell.edu/",
    "cornell-biomedical-sciences-bs": "https://cals.cornell.edu/biological-sciences",
    "cornell-applied-economics-bs": "https://dyson.cornell.edu/programs/undergraduate/",
    "cornell-mba": "https://www.johnson.cornell.edu/programs/full-time-mba/two-year-mba/",
    "cornell-business-administration-ms": "https://www.johnson.cornell.edu/programs/masters-programs/",
    "cornell-hotel-administration-bs": "https://sha.cornell.edu/admissions-programs/undergraduate/",
    "cornell-ilr-bs": "https://www.ilr.cornell.edu/academics/undergraduate-programs",
    "cornell-ilr-ms": "https://www.ilr.cornell.edu/academics/graduate-degree-programs",
    "cornell-human-development-bs": "https://www.human.cornell.edu/hd",
    "cornell-mpa-ms": "https://publicpolicy.cornell.edu/masters/mpa/",
    "cornell-legal-studies-ms-online": "https://ecornell.cornell.edu/degrees/",
    "cornell-emba-americas": "https://www.johnson.cornell.edu/programs/emba/americas/",
    "cornell-engineering-management-meng-online": "https://ecornell.cornell.edu/degrees/",
    "cornell-emha-online": "https://publicpolicy.cornell.edu/masters/sloan/emha/",
    "cornell-empa-online": "https://publicpolicy.cornell.edu/masters/empa/",
    "cornell-jd": "https://www.lawschool.cornell.edu/admissions/jd-admissions/",
    "cornell-dvm": "https://www.vet.cornell.edu/education/doctor-veterinary-medicine",
    "cornell-march": "https://aap.cornell.edu/academics/architecture/march",
    "cornell-md": "https://medicalcollege.weill.cornell.edu/",
}

# ── Who-it's-for + highlights (catalog baselines) ──────────────────────────
_WHO_BASELINE = (
    "Academically exceptional students seeking a research-rich education at an Ivy League "
    "and land-grant university with broad cross-college flexibility, need-met financial "
    "aid, and the depth of a major research university."
)
_HL_BASELINE = ["Ivy League", "9:1 student-faculty ratio", "Need-met financial aid"]
_WHO_GRAD_BASELINE = (
    "Graduate and professional students seeking a top-ranked Cornell degree with the "
    "resources of a major research university and an internationally recognized faculty."
)
_HL_GRAD_BASELINE = ["Top-ranked Cornell graduate degree", "World-class faculty", "Ivy League"]

_WHO_BY_SLUG = {
    "cornell-computer-science-bs": (
        "Technically strong students who want a rigorous computer science education — "
        "as the B.S. (Engineering) or B.A. (Arts and Sciences) — in Cornell's Bowers "
        "College of Computing and Information Science."
    ),
    "cornell-legal-studies-ms-online": (
        "Working professionals who need legal frameworks and reasoning without practicing "
        "law, studying fully online through Cornell Law School."
    ),
    "cornell-emba-americas": (
        "Experienced working professionals seeking a Cornell MBA in a hybrid weekend "
        "format with synchronous online instruction."
    ),
    "cornell-mba": (
        "Early- and mid-career professionals seeking a STEM-designated, immersion-based "
        "Two-Year MBA at Cornell Johnson with strong finance and consulting placement."
    ),
}
_HL_BY_SLUG = {
    "cornell-computer-science-bs": [
        "B.S. & B.A. tracks",
        "16 research areas",
        "Cornell Bowers CIS",
    ],
    "cornell-legal-studies-ms-online": [
        "Fully online",
        "Cornell Law School",
        "For non-practicing professionals",
    ],
    "cornell-emba-americas": [
        "Hybrid weekend format",
        "Synchronous online classes",
        "Cornell MBA",
    ],
    "cornell-mba": [
        "Two-Year residential MBA",
        "Semester immersions",
        "STEM-designated",
    ],
}

# ── Curriculum / research areas, where published (the flagship) ────────────
# Cornell CS publishes 16 official research areas; quoted from the department's official
# Research page.
_FLAGSHIP = "cornell-mba"

_TRACKS_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "tracks": [
            "Corporate Finance",
            "Digital Technology",
            "Investment Banking",
            "Strategy & Consulting",
            "Strategic Product & Marketing",
            "Customized Immersion",
        ],
        "source": "Cornell Johnson — Immersion Learning",
        "source_url": (
            "https://www.johnson.cornell.edu/programs/full-time-mba/two-year-mba/"
            "curriculum/immersion-learning/"
        ),
    },
    "cornell-computer-science-bs": {
        "label": "Computer science research areas",
        "note": (
            "Computer science is offered as both the B.S. (College of Engineering) and the "
            "B.A. (College of Arts and Sciences), both under CIP 11.0701. Upper-level "
            "coursework spans the department's sixteen official research areas."
        ),
        "items": [
            {"name": "Architecture"},
            {"name": "Artificial Intelligence"},
            {"name": "Computational Biology"},
            {"name": "Database Systems"},
            {"name": "Graphics"},
            {"name": "Human Interaction"},
            {"name": "Programming Languages"},
            {"name": "Machine Learning"},
            {"name": "Natural Language Processing"},
            {"name": "Robotics"},
            {"name": "Scientific Computing"},
            {"name": "Security"},
            {"name": "Software Engineering"},
            {"name": "Systems and Networking"},
            {"name": "Theory of Computing"},
            {"name": "Vision"},
        ],
        "source": "Cornell Department of Computer Science — Research",
        "source_url": "https://www.cs.cornell.edu/research/",
    },
}

# ── Program-specific cost ──────────────────────────────────────────────────
# Cornell 2025-26 endowed-college undergraduate tuition; cost of attendance and average
# net price are College Scorecard / Cornell budget figures.
_TUITION_UG_ENDOWED = 71266
_TUITION_UG_STATUTORY_NY = 48010
_UNDERGRAD_COA = 88140
_AVG_NET_PRICE = 28690

# Statutory/contract colleges whose undergraduate programs charge a lower NY-resident
# tuition (non-residents pay the endowed rate).
_STATUTORY_SCHOOLS = {_CALS, _DYSON, _HUMAN_ECOLOGY, _ILR}

_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission.",
}

# Johnson Two-Year MBA admission (official application materials and rounds).
_REQ_MBA = {
    "materials": [
        {"name": "Johnson School online MBA application", "required": True},
        {"name": "Essays (per the current Johnson prompts)", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "One letter of recommendation", "required": True},
        {"name": "Resume", "required": True},
        {
            "name": "GMAT, GRE, or Executive Assessment scores",
            "required": True,
            "note": (
                "Johnson accepts the GMAT (10th or Focus Edition), GRE, or Executive "
                "Assessment; a test score is required for the Two-Year MBA."
            ),
        },
        {"name": "Interview (by invitation only)", "required": False},
        {"name": "$200 application fee (fee waivers available)", "required": True},
    ],
    "deadlines": [
        {"round": "Round 1", "date": "September 17, 2025"},
        {"round": "Round 2", "date": "January 8, 2026"},
        {"round": "Round 3 (final)", "date": "April 7, 2026"},
    ],
    "recommendations": {
        "required": 1,
        "note": "One letter of recommendation submitted through the Johnson application.",
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": True,
            "note": (
                "An English-proficiency test is required for applicants whose first "
                "language is not English (waivers may apply)."
            ),
        },
        "visa": _INTL_VISA,
    },
    "source": "Cornell Johnson — Two-Year MBA Admissions",
    "source_url": "https://www.johnson.cornell.edu/programs/full-time-mba/two-year-mba/",
}

# Johnson Two-Year MBA Class of 2025 employment outcomes (first-party report).
_MBA_OUTCOMES: dict = {
    "median_salary": 175000,
    "employment_rate": 0.85,
    "top_industries": [
        {"name": "Financial Services", "share": 0.41},
        {"name": "Consulting", "share": 0.28},
        {"name": "Technology & Telecommunications", "share": 0.11},
    ],
    "conditions": (
        "Cornell Johnson Two-Year MBA Class of 2025: median base salary $175,000, "
        "average base salary $158,426, average signing bonus $39,795. 239 of 285 "
        "graduates were seeking employment; 85% received job offers and 83% accepted "
        "offers within three months of graduation."
    ),
    "source": "Cornell Johnson — Two-Year MBA Employment Report (Class of 2025)",
    "source_url": (
        "https://www.johnson.cornell.edu/programs/full-time-mba/two-year-mba/"
        "careers/employment-data/"
    ),
}

_COST_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "tuition_usd": 86596,
        "total_cost_of_attendance": 119994,
        "breakdown": {
            "tuition": 86596,
            "student_activity_fee": 110,
            "health_fee": 580,
            "housing": 16796,
            "meals": 5654,
            "books_and_supplies": 2466,
            "transportation": 3544,
            "miscellaneous": 4248,
        },
        "funded": False,
        "note": (
            "Cornell Johnson 2025-26 Two-Year MBA estimated first-year cost of attendance "
            "($86,596 tuition plus billed and non-billed living expenses)."
        ),
        "source": "Cornell Johnson — Tuition & Expenses (2025-26)",
        "source_url": "https://www.johnson.cornell.edu/programs/tuition-expenses/",
        "year": "2025-26",
    },
}

# Programs that publish no citable per-program tuition (graduate/professional/online):
# cost is recorded as omitted with a reason rather than guessed.
_COST_OMIT_SLUGS = {
    "cornell-computer-science-ms",
    "cornell-information-science-ms",
    "cornell-electrical-computer-eng-ms",
    "cornell-operations-research-ms",
    "cornell-systems-eng-ms",
    "cornell-meng-ms",
    "cornell-business-administration-ms",
    "cornell-ilr-ms",
    "cornell-mpa-ms",
    "cornell-legal-studies-ms-online",
    "cornell-emba-americas",
    "cornell-engineering-management-meng-online",
    "cornell-emha-online",
    "cornell-empa-online",
    "cornell-jd",
    "cornell-dvm",
    "cornell-march",
    "cornell-md",
}

# ── Program-specific outcomes (College Scorecard Field of Study, by CIP) ────
# College Scorecard publishes a Field-of-Study median earnings (one year after completion)
# for these awarded CIPs at UNITID 190415 (program scope). Tuples are
# (median_earnings_1yr, cip).
_FOS_OUTCOMES: dict[str, tuple[int, str]] = {
    "cornell-computer-science-bs": (152656, "11.07"),
    "cornell-computer-science-ms": (153588, "11.07"),
    "cornell-information-science-bs": (103650, "11.01"),
    "cornell-information-science-ms": (123586, "11.01"),
    "cornell-electrical-computer-eng-bs": (100516, "14.10"),
    "cornell-electrical-computer-eng-ms": (123494, "14.10"),
    "cornell-mechanical-eng-bs": (85440, "14.19"),
    "cornell-operations-research-ms": (125810, "14.37"),
    "cornell-systems-eng-ms": (117455, "14.27"),
    "cornell-meng-ms": (83323, "15.15"),
    "cornell-economics-bs": (84967, "45.06"),
    "cornell-political-science-bs": (60292, "45.10"),
    "cornell-mathematics-bs": (87251, "27.01"),
    "cornell-biology-bs": (34500, "26.01"),
    "cornell-biomedical-sciences-bs": (38841, "26.99"),
    "cornell-applied-economics-bs": (92163, "01.01"),
    "cornell-business-administration-ms": (179274, "52.02"),
    "cornell-hotel-administration-bs": (77803, "52.09"),
    "cornell-ilr-bs": (73436, "52.10"),
    "cornell-ilr-ms": (112291, "52.10"),
    "cornell-human-development-bs": (38401, "19.07"),
}

# Verbatim methodology for the program-scope Scorecard FOS earnings figure.
_FOS_CONDITIONS = (
    "Median earnings of graduates who received federal financial aid, measured "
    "approximately one year after program completion; reported by the U.S. Department of "
    "Education College Scorecard Field of Study by 4-digit CIP code. Programs with too few "
    "completers are suppressed."
)

# Institution-wide outcomes fallback (College Scorecard, UNITID 190415), used for programs
# whose program-level one-year earnings are not published (suppressed), or that have no
# Scorecard Field-of-Study row (the online and professional degrees).
_OUTCOMES_INSTITUTION = {
    "median_salary": 104043,
    "scope": "institution",
    "conditions": (
        "Cornell institution-wide median earnings ten years after entry (College "
        "Scorecard, UNITID 190415); a program-level one-year earnings figure is not "
        "published (suppressed) for this field of study."
    ),
    "source": "U.S. Dept. of Education College Scorecard (UNITID 190415)",
    "source_url": "https://collegescorecard.ed.gov/school/?190415-Cornell-University",
}

# Annual degrees conferred per CIP (College Scorecard Field of Study), used for the
# flagship class-profile cohort figure.
_AWARDS_BY_SLUG: dict[str, int] = {"cornell-computer-science-bs": 507}

# ── Class profile, where published (the flagship) ──────────────────────────
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "cohort_size": "276 students in the entering Two-Year MBA class (Class of 2027)",
        "international_pct": 0.42,
        "note": (
            "Entering Two-Year MBA Class of 2027: 276 students, 42% international "
            "citizens (34 countries), 38% women, median GMAT 710, median undergraduate "
            "GPA 3.4, average 5.3 years of full-time work experience."
        ),
        "source": "Cornell Johnson — Class Profiles",
        "source_url": "https://www.johnson.cornell.edu/for-recruiters/class-profiles/",
    },
    "cornell-computer-science-bs": {
        "cohort_size": (
            "≈507 computer science bachelor's degrees awarded annually (one of "
            "Cornell's most popular majors)"
        ),
        "note": (
            "Cornell does not publish a per-major entering-cohort size; the figure is the "
            "annual count of computer science bachelor's degrees awarded (College "
            "Scorecard Field of Study, CIP 11.0701)."
        ),
        "source": "U.S. Dept. of Education College Scorecard — Field of Study (CIP 11.07)",
        "source_url": "https://collegescorecard.ed.gov/school/?190415-Cornell-University",
    },
}

# ── Faculty (lead + directory link), where confidently sourced (the flagship) ──
_FACULTY_BY_SLUG: dict[str, dict] = {
    "cornell-computer-science-bs": {
        "lead": [
            {
                "name": "Lorenzo Alvisi",
                "title": (
                    "Tisch University Professor and Chair of the Department of Computer "
                    "Science; distributed systems and dependability"
                ),
            },
            {
                "name": "Jon Kleinberg",
                "title": (
                    "Tisch University Professor of Computer Science and Information "
                    "Science; algorithms, networks and the social web"
                ),
            },
        ],
        "note": (
            "Cornell Computer Science is chaired by Lorenzo Alvisi (Tisch University "
            "Professor); Jon Kleinberg is a Tisch University Professor in the department."
        ),
        "directory_url": "https://www.cs.cornell.edu/people/faculty",
    },
}

# ── Aggregated, cited student-review themes (≥2 third-party sources, the flagship) ──
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "cornell-computer-science-bs": {
        "summary": (
            "Students and third-party guides describe Cornell as academically rigorous and "
            "intellectually broad, with strong, dedicated professors and exceptional "
            "cross-college flexibility on a beautiful campus; computer science is one of "
            "Cornell's strongest and most popular majors with excellent industry and "
            "graduate placement. Common cautions are the high cost, a competitive and "
            "demanding atmosphere with a reputation for tough grading, large introductory "
            "lectures, and Ithaca's cold winters and relative isolation."
        ),
        "themes": [
            {
                "label": "Academic rigor & breadth",
                "sentiment": "positive",
                "detail": "Challenging academics with broad cross-college course flexibility.",
            },
            {
                "label": "Strong faculty & CS strength",
                "sentiment": "positive",
                "detail": "Dedicated professors; CS is a top, popular major with strong placement.",
            },
            {
                "label": "Campus & opportunities",
                "sentiment": "positive",
                "detail": "A beautiful campus with wide research and career opportunities.",
            },
            {
                "label": "Cost & competitiveness",
                "sentiment": "caution",
                "detail": "High cost and a competitive, demanding atmosphere with tough grading.",
            },
            {
                "label": "Large classes & winters",
                "sentiment": "caution",
                "detail": "Large intro lectures, and cold Ithaca winters with some isolation.",
            },
        ],
        "sources": [
            {
                "label": "Niche — Cornell University reviews",
                "url": "https://www.niche.com/colleges/cornell-university/reviews/",
            },
            {
                "label": "U.S. News — Cornell University",
                "url": "https://www.usnews.com/best-colleges/cornell-university-2711",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    _FLAGSHIP: {
        "summary": (
            "Students and third-party guides describe Cornell Johnson's Two-Year MBA as "
            "an immersion-driven, STEM-designated program with strong finance and "
            "consulting placement and a collaborative Ithaca cohort; the Class of 2025 "
            "reported a $175,000 median base salary with financial services and consulting "
            "as top destinations. Common cautions are the demanding mini-semester pace, "
            "Ithaca's relative isolation compared with coastal MBA hubs, and a brand "
            "footprint that trails M7 peers despite improving U.S. News rankings."
        ),
        "themes": [
            {
                "label": "Immersion-based curriculum",
                "sentiment": "positive",
                "detail": (
                    "Semester-long immersions in finance, consulting, tech, and marketing "
                    "prepare students for summer internships."
                ),
            },
            {
                "label": "Finance & consulting outcomes",
                "sentiment": "positive",
                "detail": (
                    "Class of 2025: $175K median base; financial services (41%) and "
                    "consulting (28%) lead placements."
                ),
            },
            {
                "label": "Collaborative cohort",
                "sentiment": "positive",
                "detail": (
                    "A large but tight-knit class (276) with strong veteran and "
                    "international representation."
                ),
            },
            {
                "label": "Location & brand",
                "sentiment": "mixed",
                "detail": (
                    "Ithaca campus life is beautiful but remote; Johnson ranks below "
                    "M7 peers in national MBA brand perception."
                ),
            },
            {
                "label": "Academic intensity",
                "sentiment": "caution",
                "detail": (
                    "Core courses and immersions move quickly; students cite a heavy "
                    "workload across mini-semesters."
                ),
            },
        ],
        "sources": [
            {
                "label": "Cornell Johnson — Class of 2025 Employment Report",
                "url": (
                    "https://www.johnson.cornell.edu/programs/full-time-mba/two-year-mba/"
                    "careers/employment-data/"
                ),
            },
            {
                "label": "Clear Admit — Cornell Johnson Class of 2027 Profile",
                "url": (
                    "https://www.clearadmit.com/2025/09/"
                    "cornell-johnson-two-year-mba-class-of-2027-profile/"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "cornell-computer-science-ms": {
        "summary": (
            "Graduate CS applicants and guides describe Cornell's M.S. as a rigorous, "
            "research-oriented program within the Bowers College with strong faculty in "
            "AI, systems, and theory and excellent industry placement for terminal "
            "master's graduates. Cautions include competitive funding for Ph.D.-bound "
            "applicants, a smaller cohort than peer CS giants, and Ithaca's limited "
            "local tech market compared with coastal hubs."
        ),
        "themes": [
            {
                "label": "Research depth",
                "sentiment": "positive",
                "detail": "Sixteen official CS research areas with top faculty in AI and systems.",
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": (
                    "Scorecard reports strong one-year post-completion earnings for the "
                    "CS master's (CIP 11.07)."
                ),
            },
            {
                "label": "Funding clarity",
                "sentiment": "caution",
                "detail": (
                    "Terminal M.S. funding is limited; Ph.D. admits receive stronger "
                    "financial support."
                ),
            },
            {
                "label": "Location",
                "sentiment": "mixed",
                "detail": (
                    "Ithaca campus is collaborative but geographically distant from major "
                    "tech hubs."
                ),
            },
        ],
        "sources": [
            {
                "label": "Cornell CS — Graduate Program",
                "url": "https://www.cs.cornell.edu/masters",
            },
            {
                "label": "U.S. News — Cornell University",
                "url": "https://www.usnews.com/best-colleges/cornell-university-2711",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "cornell-jd": {
        "summary": (
            "Students and third-party guides describe Cornell Law as a rigorous Ivy "
            "program with strong clinical offerings, a close-knit community, and "
            "improving employment outcomes — U.S. News ranked it tied for 13th nationally "
            "in 2026-27 and No. 1 for graduates at large law firms. Common cautions are "
            "grade opacity and high-stakes finals, limited criminal-law and tax course "
            "breadth for niche interests, and a public-interest minority among students "
            "despite an expanded LRAP."
        ),
        "themes": [
            {
                "label": "Big Law placement",
                "sentiment": "positive",
                "detail": (
                    "U.S. News ranks Cornell No. 1 for graduates at large law firms "
                    "(2026-27)."
                ),
            },
            {
                "label": "Clinical & lawyering skills",
                "sentiment": "positive",
                "detail": (
                    "Experiential clinics and the Lawyering Program emphasize real-world "
                    "litigation skills."
                ),
            },
            {
                "label": "Close-knit community",
                "sentiment": "positive",
                "detail": "Small cohort fosters collaboration despite heavy workload.",
            },
            {
                "label": "Grading stress",
                "sentiment": "caution",
                "detail": (
                    "Opaque grading on high-stakes finals affects journal and "
                    "employment opportunities."
                ),
            },
            {
                "label": "Course breadth",
                "sentiment": "mixed",
                "detail": (
                    "Fewer criminal-law and tax offerings than some peer schools for "
                    "specialized interests."
                ),
            },
        ],
        "sources": [
            {
                "label": "Cornell Daily Sun — U.S. News 2026-27 Law Rankings",
                "url": (
                    "https://www.cornellsun.com/article/2026/04/"
                    "cornell-law-school-ranked-no-13-in-the-country"
                ),
            },
            {
                "label": "Niche — Cornell Law School reviews",
                "url": "https://www.niche.com/graduate-schools/cornell-law-school/reviews/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "cornell-dvm": {
        "summary": (
            "Applicants and guides describe Cornell's College of Veterinary Medicine as "
            "one of the nation's top D.V.M. programs — the only veterinary college in "
            "the Ivy League — with exceptional clinical training at the Cornell University "
            "Hospital for Animals and strong research in animal health. Common cautions are "
            "extremely competitive admission, high total cost of attendance, and the "
            "intensity of the four-year professional curriculum."
        ),
        "themes": [
            {
                "label": "Top-tier clinical training",
                "sentiment": "positive",
                "detail": (
                    "Teaching hospital and specialty services provide hands-on caseload "
                    "experience."
                ),
            },
            {
                "label": "Research & specialty depth",
                "sentiment": "positive",
                "detail": (
                    "Strong programs in wildlife, production medicine, and biomedical "
                    "sciences."
                ),
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": (
                    "Highly competitive applicant pool with strong academic and "
                    "experience prerequisites."
                ),
            },
            {
                "label": "Cost & workload",
                "sentiment": "caution",
                "detail": (
                    "Professional veterinary training is expensive and academically "
                    "demanding across four years."
                ),
            },
        ],
        "sources": [
            {
                "label": "Cornell College of Veterinary Medicine — D.V.M. Program",
                "url": "https://www.vet.cornell.edu/education/doctor-veterinary-medicine",
            },
            {
                "label": "U.S. News — Best Veterinary Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/veterinary-rankings",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "cornell-md": {
        "summary": (
            "Students and guides describe Weill Cornell Medicine as a top-tier New York "
            "City medical school with exceptional clinical access through affiliated "
            "hospitals, strong research funding, and a diverse patient population. Common "
            "cautions are the high cost of living in Manhattan, intense workload across "
            "the MD curriculum, and the competitive residency match environment shared by "
            "all elite medical schools."
        ),
        "themes": [
            {
                "label": "NYC clinical access",
                "sentiment": "positive",
                "detail": (
                    "Affiliated NewYork-Presbyterian/Weill Cornell network offers diverse "
                    "clinical training."
                ),
            },
            {
                "label": "Research excellence",
                "sentiment": "positive",
                "detail": (
                    "Major biomedical research enterprise with strong NIH funding and "
                    "specialty institutes."
                ),
            },
            {
                "label": "Cost of attendance",
                "sentiment": "caution",
                "detail": (
                    "Manhattan living costs add substantially to medical-school expenses."
                ),
            },
            {
                "label": "Academic intensity",
                "sentiment": "caution",
                "detail": (
                    "Fast-paced MD curriculum with high expectations across basic and "
                    "clinical sciences."
                ),
            },
        ],
        "sources": [
            {
                "label": "Weill Cornell Medicine — MD Program",
                "url": "https://medicalcollege.weill.cornell.edu/education/md-program",
            },
            {
                "label": "U.S. News — Best Medical Schools (Research)",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/research-rankings",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "cornell-hotel-administration-bs": {
        "summary": (
            "Students and industry guides describe the Nolan School as the world's first "
            "and top-ranked collegiate hospitality program — teaching business through a "
            "service lens with strong finance, real-estate, and consulting placement beyond "
            "traditional hotel operations. Common cautions are that the hospitality brand "
            "can read niche to recruiters outside service industries unless students "
            "actively translate skills, and the program is smaller than general business "
            "schools at peer universities."
        ),
        "themes": [
            {
                "label": "Hospitality business foundation",
                "sentiment": "positive",
                "detail": (
                    "Core business curriculum (finance, accounting, analytics) taught "
                    "through a service-industry lens."
                ),
            },
            {
                "label": "Versatile outcomes",
                "sentiment": "positive",
                "detail": (
                    "Graduates enter financial services, consulting, and real estate as "
                    "well as hospitality."
                ),
            },
            {
                "label": "Industry network",
                "sentiment": "positive",
                "detail": (
                    "Deep alumni and employer ties across global hospitality and "
                    "related sectors."
                ),
            },
            {
                "label": "Niche major perception",
                "sentiment": "mixed",
                "detail": (
                    "Applicants targeting pure investment banking may prefer a general "
                    "business major."
                ),
            },
        ],
        "sources": [
            {
                "label": "Cornell Nolan School — About",
                "url": "https://sha.cornell.edu/",
            },
            {
                "label": "Poets&Quants For Undergrads — Cornell Hotelie career paths",
                "url": (
                    "https://poetsandquantsforundergrads.com/students/"
                    "the-cornell-connection-using-an-unorthodox-college-major-for-career-success/"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "cornell-emba-americas": {
        "summary": (
            "Working professionals describe the Cornell Executive MBA Americas as a "
            "demanding hybrid program pairing weekend residencies with synchronous online "
            "coursework across North and South America, yielding a Cornell MBA without "
            "leaving employment. Positive themes include a strong peer network of senior "
            "leaders and Johnson's analytics-forward curriculum; cautions are the travel "
            "commitment, limited time for recruiting pivots, and less on-campus immersion "
            "than the full-time Two-Year MBA."
        ),
        "themes": [
            {
                "label": "Hybrid for working leaders",
                "sentiment": "positive",
                "detail": (
                    "Weekend format lets executives earn a Cornell MBA while employed."
                ),
            },
            {
                "label": "Senior peer network",
                "sentiment": "positive",
                "detail": (
                    "Cohorts bring substantial management experience across industries."
                ),
            },
            {
                "label": "Travel & time commitment",
                "sentiment": "caution",
                "detail": (
                    "Residential weekends and online sync sessions require significant "
                    "schedule sacrifice."
                ),
            },
            {
                "label": "Career-switch limits",
                "sentiment": "mixed",
                "detail": (
                    "Better suited to advancement within a career than a full pivot "
                    "versus the Two-Year MBA."
                ),
            },
        ],
        "sources": [
            {
                "label": "Cornell Johnson — Executive MBA Americas",
                "url": "https://www.johnson.cornell.edu/programs/emba/americas/",
            },
            {
                "label": "Clear Admit — Cornell Johnson School Overview",
                "url": "https://www.clearadmit.com/schools/johnson/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "cornell-ilr-bs": {
        "summary": (
            "Students and guides describe Cornell ILR as a unique Ivy League program "
            "combining labor relations, human resources, economics, and law — with strong "
            "placement into HR, consulting, finance, and law school. Positive themes "
            "include small classes, passionate faculty, and a tight ILR community; cautions "
            "include that the specialized major requires explanation to employers outside "
            "HR/consulting and that coursework can feel interdisciplinary rather than "
            "purely quantitative."
        ),
        "themes": [
            {
                "label": "Distinctive HR & labor focus",
                "sentiment": "positive",
                "detail": (
                    "Only Ivy League undergraduate school dedicated to work, labor, and "
                    "organizations."
                ),
            },
            {
                "label": "Versatile placement",
                "sentiment": "positive",
                "detail": (
                    "Graduates enter HR, consulting, finance, and top law schools."
                ),
            },
            {
                "label": "Community & faculty",
                "sentiment": "positive",
                "detail": "Small-school feel within Cornell with engaged ILR faculty.",
            },
            {
                "label": "Major branding",
                "sentiment": "mixed",
                "detail": (
                    "Applicants must articulate how ILR translates outside HR-focused "
                    "roles."
                ),
            },
        ],
        "sources": [
            {
                "label": "Cornell ILR — Undergraduate Programs",
                "url": "https://www.ilr.cornell.edu/academics/undergraduate-programs",
            },
            {
                "label": "Niche — Cornell University reviews",
                "url": "https://www.niche.com/colleges/cornell-university/reviews/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
}

# ── Application requirements ─────────────────────────────────────────────────
# Undergraduate (Cornell) admission via the Common Application, by specific college/school.
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application", "required": True},
        {"name": "Cornell-specific writing supplement (by college/school)", "required": True},
        {"name": "School report + secondary-school transcript", "required": True},
        {"name": "Counselor recommendation", "required": True},
        {"name": "Two teacher recommendations", "required": True},
        {"name": "$85 application fee; need-based fee waivers available", "required": True},
        {
            "name": "Standardized test scores (SAT/ACT)",
            "required": False,
            "note": (
                "Cornell's standardized-testing policy varies by entering cycle and "
                "college; confirm the current requirement on the admissions site before "
                "applying."
            ),
        },
    ],
    "deadlines": [
        {"round": "Early Decision (binding)", "date": "November 1"},
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
            {
                "label": "Cornell Undergraduate Admissions — First-Year Applicants",
                "url": "https://admissions.cornell.edu/how-to-apply/first-year-applicants",
            }
        ],
    },
    "source": "Cornell Undergraduate Admissions",
    "source_url": "https://admissions.cornell.edu/how-to-apply/first-year-applicants",
}

# Generic Cornell graduate / professional admission set. Each school administers its own
# admissions; the materials below are common across Cornell graduate and professional
# programs, and deadlines vary by program — applicants are pointed to the program's own
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
            "note": "Most Cornell graduate and professional programs require two to three letters.",
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
            "Most Cornell graduate and professional programs require two to three letters "
            "of recommendation."
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
                "label": "Cornell Graduate School — Admissions",
                "url": "https://gradschool.cornell.edu/admissions/",
            }
        ],
    },
    "source": "Cornell graduate & professional admissions",
    "source_url": "https://gradschool.cornell.edu/admissions/",
}


def _requirements_for(spec: dict) -> dict:
    """Pick the admissions requirement set for a program by degree type."""
    if spec["slug"] == _FLAGSHIP:
        return dict(_REQ_MBA)
    if spec["degree_type"] == "bachelors":
        return dict(_REQ_UNDERGRAD)
    return dict(_REQ_GRAD_GENERIC)


# Real Cornell campus photo (Arts Quad with McGraw Tower) — Wikimedia Commons, CC BY-SA,
# hotlinkable landscape JPG (verified HTTP 200). Leads the institution hero.
_CAMPUS_PHOTO = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/"
    "Cornell_University_arts_quad.JPG/1280px-Cornell_University_arts_quad.JPG"
)


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich Cornell to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Cornell is absent — safe on fresh/CI databases.
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
    inst.founded_year = 1865
    inst.campus_setting = "college_town"
    if not inst.website_url:
        inst.website_url = "https://www.cornell.edu"
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
        # Every school carries a populated Events & Updates feed: the Chronicle news
        # feed filtered by school keywords + the university events calendar. Always
        # assign so a stale value on a pre-existing row is cleared. None is never left.
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


def _cost_for(spec: dict) -> dict | None:
    """Return the program's cost_data dict, or None when cost is omitted-with-reason."""
    slug = spec["slug"]
    if slug in _COST_BY_SLUG:
        return dict(_COST_BY_SLUG[slug])
    if slug in _COST_OMIT_SLUGS:
        return None
    # Undergraduate: 2025-26 endowed-college tuition; statutory colleges add the lower
    # NY-resident rate as a note.
    note = (
        "Published 2025-26 Cornell endowed-college undergraduate tuition with the College "
        "Scorecard cost of attendance and average net price. Cornell meets 100% of "
        "demonstrated need and is need-blind for U.S. applicants, so most families pay far "
        "less than the sticker price (average net price ≈ $28,700)."
    )
    if spec["school"] in _STATUTORY_SCHOOLS:
        note = (
            "Cornell 2025-26 tuition: the New York State statutory/contract colleges charge "
            f"${_TUITION_UG_STATUTORY_NY:,} for New York residents and the endowed rate of "
            f"${_TUITION_UG_ENDOWED:,} for non-residents. College Scorecard cost of "
            "attendance and average net price shown; Cornell meets 100% of demonstrated "
            "need for admitted undergraduates."
        )
    return {
        "tuition_usd": _TUITION_UG_ENDOWED,
        "total_cost_of_attendance": _UNDERGRAD_COA,
        "avg_net_price": _AVG_NET_PRICE,
        "breakdown": {
            "tuition": _TUITION_UG_ENDOWED,
            "total_cost_of_attendance": _UNDERGRAD_COA,
        },
        "funded": False,
        "note": note,
        "source": "Cornell 2025-26 budget parameters + College Scorecard (UNITID 190415)",
        "source_url": (
            "https://news.cornell.edu/stories/2025/03/"
            "board-trustees-approves-2025-26-budget-parameters"
        ),
        "year": "2025-26",
    }


def _program_standard(slug: str, spec: dict) -> dict:
    """Per-program omitted-field list (verified-unavailable), for _standard."""
    omitted: list[str] = []
    # Cornell reports first-destination outcomes university-wide (captured at the
    # institution level), so every program except the Johnson MBA omits the program-level
    # employment rate and industry breakdown.
    if slug != _FLAGSHIP:
        omitted += [
            "outcomes_data.employment_rate",
            "outcomes_data.top_industries",
        ]
    if slug in _COST_OMIT_SLUGS:
        # No citable per-program tuition is published for these graduate/professional/online
        # degrees.
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
        if slug == "cornell-computer-science-bs":
            p.content_sources = _CS_CONTENT
        elif slug == _FLAGSHIP:
            p.content_sources = dict(_MBA_CONTENT)
        elif slug in _PROGRAM_KEYWORDS_BY_SLUG:
            cs = _program_content(spec)
            cs["keywords"] = list(_PROGRAM_KEYWORDS_BY_SLUG[slug])
            p.content_sources = cs
        else:
            p.content_sources = _program_content(spec)
        # Cost: undergraduate uses published Cornell rates; graduate/professional/online
        # programs omit a per-program tuition (recorded in _standard.omitted).
        cost = _cost_for(spec)
        if cost is not None:
            p.tuition = cost.get("tuition_usd")
            p.cost_data = cost
        else:
            p.tuition = None
            p.cost_data = {
                "funded": False,
                "note": (
                    "Cornell does not publish a single citable per-program tuition for this "
                    "degree on a public page; see the program website for current tuition."
                ),
                "source": "Cornell program website",
                "source_url": _WEBSITE_BY_SLUG.get(slug) or _SCHOOL_WEBSITE.get(spec["school"]),
            }
        # Admissions: undergraduate or generic graduate/professional set by degree type.
        p.application_requirements = _requirements_for(spec)
        # Outcomes precedence: Johnson MBA report → Scorecard FOS (program) → institution.
        fos = _FOS_OUTCOMES.get(slug)
        if slug == _FLAGSHIP:
            outcomes = dict(_MBA_OUTCOMES)
        elif fos is not None:
            salary, cip = fos
            outcomes = {
                "median_salary": salary,
                "scope": "program",
                "cip": cip,
                "earnings_timeframe": "median earnings 1 year after completion",
                "conditions": _FOS_CONDITIONS,
                "source": "U.S. Dept. of Education College Scorecard — Field of Study",
                "source_url": "https://collegescorecard.ed.gov/school/?190415-Cornell-University",
            }
            awards = _AWARDS_BY_SLUG.get(slug)
            if awards is not None:
                outcomes["degrees_conferred_annual"] = awards
        else:
            outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        if spec["degree_type"] == "bachelors":
            p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_BASELINE
            p.highlights = _HL_BY_SLUG.get(slug) or _HL_BASELINE
        else:
            p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_GRAD_BASELINE
            p.highlights = _HL_BY_SLUG.get(slug) or _HL_GRAD_BASELINE
        # Always assign so a stale value on a pre-existing row is cleared (tracks is
        # recorded as omitted where unverified, and match_service reads program.tracks).
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        # Application deadline (upcoming undergraduate Regular Decision closes Jan 2).
        p.application_deadline = (
            date(2026, 1, 8)
            if slug == _FLAGSHIP
            else (date(2027, 1, 2) if spec["degree_type"] == "bachelors" else None)
        )
    session.flush()
    # Reconcile legacy Cornell programs (slug not in the canonical set): delete when
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
