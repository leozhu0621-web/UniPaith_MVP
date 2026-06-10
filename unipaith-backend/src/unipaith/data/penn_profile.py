"""Canonical University of Pennsylvania profile — the single source of truth.

Real, sourced data only (U.S. Dept. of Education College Scorecard, UNITID 215062 ·
NCES College Navigator / IPEDS · IPEDS admissions survey via the Urban Institute
Education Data API · the official Penn "Facts" page · Penn's Office of Institutional
Research & Analysis Common Data Set · the official QS / Times Higher Education / U.S.
News rankings · each school's official leadership / about page · the Wharton MBA Career
Report · Penn Career Services first-destination outcomes · the College Scorecard
Field-of-Study earnings by CIP). ``apply(session)`` idempotently enriches the Penn
institution row, upserts its real degree-granting schools, and builds Penn's program
catalog across them.

Penn's academic structure (official "Facts" page): the University is organized into
twelve schools — four with undergraduate programs (the School of Arts & Sciences, the
Wharton School, the School of Engineering and Applied Science, and the School of
Nursing) and eight graduate/professional schools (Perelman School of Medicine, Penn
Carey Law, the Graduate School of Education, the School of Dental Medicine, the Stuart
Weitzman School of Design, the School of Social Policy & Practice, the School of
Veterinary Medicine, and the Annenberg School for Communication). All twelve are modeled
as real, dean-led ``School`` rows with sourced About-tab detail.

It **flushes but does not commit** — the caller (the Alembic data migration, the CLI
script, or the dev seed) owns the transaction. It is a **no-op** (returns ``False``)
when Penn is absent, so it is safe to run against a fresh or CI database. Re-running is
safe: schools key off ``(institution_id, name)`` and programs off ``slug``; stale rows
are reconciled without breaking foreign keys.

This mirrors ``mit_profile`` / ``princeton_profile`` so the migration, the standalone
script, and the dev seed all agree (DRY). Every figure traces to a public, citable
source; anything that could not be verified from a first-party or two-independent-source
basis is **omitted** (recorded in the relevant ``_standard.omitted`` list), never guessed.
The Wharton MBA is the most-enriched flagship program (its real Class-of-2024 employment
report, majors, class profile, and aggregated reviews), mirroring MIT Sloan's MBAn in the
reference instance — with the honest caveat that this run brings the institution, all
twelve schools, and the undergraduate + Wharton-MBA program catalog to the gold standard;
the eight graduate/professional schools' own program catalogs are the resumption scope
for a later run on the same university (their cost-of-attendance budgets vary per program
and were not yet individually verified).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "University of Pennsylvania"

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
    # Penn Career Services publishes first-destination outcomes by school (e.g. the
    # College of Arts & Sciences Class of 2024 reports 93.5% employed/continuing/
    # serving), but not a single clean university-wide "employed or continuing
    # education" headline rate across all schools we could verify. The recurring top
    # first-destination industries are reported instead. Omitted rather than asserting
    # a conflated rate.
    "school_outcomes.employed_or_continuing_ed",
]

# ── Institution-level data ────────────────────────────────────────────────
# Rankings are stored as {rank, year} objects. All three ranks are quoted from the
# official ranking bodies for the 2026 editions.
RANKING_DATA: dict = {
    "ownership_type": "private",
    # Penn is accredited by the Middle States Commission on Higher Education
    # (reaffirmed 2024).
    "accreditor": "MSCHE",
    # Carnegie 2025 research-activity designation (the revamped methodology).
    "carnegie_classification": "Research 1: Very High Spending and Doctorate Production",
    # QS World University Rankings 2026: Penn is ranked #15 worldwide.
    "qs_world_university_rankings": {"rank": 15, "year": 2026},
    # THE World University Rankings 2026: #14 in the world.
    "times_higher_education": {"rank": 14, "year": 2026},
    # U.S. News Best Colleges (National Universities) 2026: #7 nationally.
    "us_news_national": {"rank": 7, "year": 2026},
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below is
# complete, so a shallow merge is correct. Figures are College Scorecard (UNITID 215062)
# cross-checked against NCES College Navigator (IPEDS), Penn's official "Facts" page,
# and the IPEDS admissions survey where each publishes a metric.
SCHOOL_OUTCOMES: dict = {
    # College Scorecard admit rate (UNITID 215062); cross-checks Penn's published ~5%
    # (Class of 2029, 4.87%) and the Common Data Set 2024-25 (5.4%).
    "admit_rate": 0.054,
    # College Scorecard average annual cost (net price across Title IV aid recipients).
    "avg_net_price": 28699,
    # College Scorecard institution-wide median earnings 10 years after entry.
    "median_earnings_10yr": 111371,
    # College Scorecard completion rate within 150% of normal time.
    "completion_rate_4yr_150pct": 0.9654,
    # NCES College Navigator (IPEDS): full-time first-year retention = 99%.
    "retention_rate_first_year": 0.99,
    # NCES College Navigator (IPEDS): six-year graduation rate (Fall 2018 cohort) = 97%.
    "graduation_rate_6yr": 0.97,
    "financial_aid": {
        # College Navigator (IPEDS): 20% of full-time beginning students received a
        # Pell grant; 9% took federal student loans (2023-24).
        "pell_grant_rate": 0.20,
        "federal_loan_rate": 0.09,
        # College Navigator (IPEDS): total on-campus cost of attendance 2024-25.
        "cost_of_attendance": 92288,
    },
    # Undergraduate race/ethnicity (NCES College Navigator / IPEDS, Fall 2024).
    "demographics": {
        "white": 0.27,
        "black": 0.09,
        "hispanic": 0.11,
        "asian": 0.28,
        "two_or_more": 0.05,
        "international": 0.14,
    },
    # SAT/ACT 25th-75th percentiles of enrolled first-years (College Navigator, Fall 2024).
    "test_scores": {
        "sat_reading_25_75": [740, 770],
        "sat_math_25_75": [770, 800],
        "act_25_75": [34, 36],
    },
    # Penn's University City campus, Philadelphia, Pennsylvania.
    "location": {"lat": 39.95028, "lng": -75.19472},
    "campus_basics": {"location": "Philadelphia, Pennsylvania"},
    "scale": {
        # Penn "Facts" (Fall 2025): 6,049 faculty (2,995 standing + 3,054 associated).
        "faculty_count": 6049,
        # Penn "Facts": 8:1 student-faculty ratio.
        "student_faculty_ratio": "8:1",
        # Penn "Facts": 209 research centers and institutes.
        "research_centers": 209,
        # Penn Office of Investments: endowment $24.81 billion at fiscal year-end 2025.
        "endowment_usd": 24810000000,
    },
    # Penn Career Services first-destination data — the leading industries Penn graduates
    # enter (Financial Services and Consulting lead across the undergraduate schools; the
    # College of Arts & Sciences Class of 2024 reports Financial Services, Consulting,
    # Healthcare, Education and Technology as its top sectors).
    "top_employer_industries": [
        "Financial services",
        "Consulting",
        "Health care",
        "Technology",
        "Education",
    ],
    "research": {
        "labs": [
            "Abramson Cancer Center (Perelman School of Medicine)",
            "Singh Center for Nanotechnology (Penn Engineering)",
            "GRASP Lab — General Robotics, Automation, Sensing & Perception",
            "Annenberg Public Policy Center",
            "Penn Center for Innovation",
        ],
        "areas": [
            "Biomedicine & the life sciences",
            "Engineering & applied science",
            "Business, finance & management",
            "Social sciences & public policy",
            "Communication & media",
            "Nursing & health systems",
        ],
        "lab_links": {
            "Abramson Cancer Center (Perelman School of Medicine)": (
                "https://www.pennmedicine.org/cancer"
            ),
            "Singh Center for Nanotechnology (Penn Engineering)": (
                "https://www.nano.upenn.edu/"
            ),
            "GRASP Lab — General Robotics, Automation, Sensing & Perception": (
                "https://www.grasp.upenn.edu/"
            ),
            "Annenberg Public Policy Center": "https://www.annenbergpublicpolicycenter.org/",
        },
    },
    "campus_life": {
        # Penn's teams (the Quakers) compete in NCAA Division I (Ivy League).
        "athletics_division": "NCAA Division I (Ivy League)",
        "mascot": "Penn Quakers",
        "housing": "College House system (residential)",
        "resources": [
            {"label": "Penn Athletics", "url": "https://pennathletics.com/"},
            {"label": "Penn College Houses & Academic Services", "url": "https://www.collegehouses.upenn.edu/"},
        ],
    },
    "flagship": {
        # Penn "Facts" (Fall 2025): 29,384 total students (10,325 undergraduate + 14,006
        # graduate/professional full-time, plus part-time).
        "enrollment_total": 29384,
        # IPEDS admissions survey (Fall 2022, the most recent year with itemized
        # applicant/admit/enroll counts), via the Urban Institute Education Data API.
        "applicants": 54588,
        "admits": 3549,
        "admissions_cycle": (
            "Itemized applicant/admit counts: entering class fall 2022 (U.S. Dept. of "
            "Education IPEDS admissions survey, the most recent year with itemized "
            "counts). Penn's current first-year admit rate is ~5% (Class of 2029: 72,544 "
            "applications, 4.87%)."
        ),
        # Chartered 1755; Penn's Trustees adopted 1740 as the founding date.
        "founded_year": 1740,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Penn, UNITID 215062)",
            "url": "https://collegescorecard.ed.gov/school/?215062",
        },
        {
            "label": "NCES College Navigator — University of Pennsylvania (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=215062",
        },
        {
            "label": "University of Pennsylvania — Facts",
            "url": "https://www.upenn.edu/about/facts",
        },
        {
            "label": "Penn Office of Institutional Research & Analysis — Common Data Set",
            "url": "https://ira.upenn.edu/penn-numbers/common-data-set",
        },
        {
            "label": "Penn Office of Investments — endowment $24.81B (FY2025)",
            "url": "https://investments.upenn.edu/about-us",
        },
        {
            "label": "QS World University Rankings 2026 — University of Pennsylvania",
            "url": "https://www.topuniversities.com/universities/university-pennsylvania",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — Penn",
            "url": "https://www.timeshighereducation.com/world-university-rankings/university-pennsylvania",
        },
        {
            "label": "U.S. News — Penn No. 7 in National Universities (2026)",
            "url": "https://www.usnews.com/best-colleges/university-of-pennsylvania-3378",
        },
        {
            "label": "University of Pennsylvania — Middle States Commission on Higher Education",
            "url": "https://www.msche.org/institution/0567/",
        },
        {
            "label": "Penn Career Services — Undergraduate Post-Graduate Outcomes",
            "url": "https://careerservices.upenn.edu/post-graduate-outcomes/",
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it "Undergraduates");
# the total (29,384) lives in flagship.enrollment_total and renders as "Total enrollment".
# 10,325 = Penn "Facts" full-time undergraduate enrollment (Fall 2025).
UNDERGRAD_COUNT = 10325

DESCRIPTION = (
    "Founded by Benjamin Franklin and tracing its origins to 1740, the University of "
    "Pennsylvania is a private Ivy League research university in Philadelphia. Penn pairs "
    "the breadth of a large research university — about 10,300 undergraduates and roughly "
    "29,400 students in all, taught by some 6,000 faculty — with Franklin's founding idea "
    "of a practical, interdisciplinary education.\n\n"
    "Penn is organized into twelve schools. Four enroll undergraduates — the School of "
    "Arts & Sciences, the Wharton School (the world's first collegiate business school, "
    "founded 1881), the School of Engineering and Applied Science, and the School of "
    "Nursing — and undergraduates routinely combine them through coordinated dual-degree "
    "and interdisciplinary programs. Eight graduate and professional schools complete the "
    "University, including the Perelman School of Medicine (the first medical school in "
    "the United States, 1765), Penn Carey Law, the Annenberg School for Communication, "
    "and the Stuart Weitzman School of Design.\n\n"
    "Penn ranks among the leading universities in the world: No. 7 among national "
    "universities by U.S. News, No. 14 in the world by Times Higher Education, and No. 15 "
    "by QS. It is a Carnegie R1 research university and manages a research enterprise of "
    "more than $1.3 billion a year across 209 centers and institutes, anchored by Penn "
    "Medicine, Penn Engineering's Singh Center for Nanotechnology, and the Annenberg "
    "Public Policy Center.\n\n"
    "Penn is need-blind for domestic applicants and meets 100% of demonstrated need with "
    "grant-based aid: the average net price is roughly $28,700 a year, 20% of "
    "undergraduates receive Pell grants, and only 9% take federal student loans. Penn "
    "graduates earn a median income of about $111,000 a decade after entry."
)

# ── The real degree-granting schools (display order) ───────────────────────
_SAS = "School of Arts and Sciences"
_WHARTON = "The Wharton School"
_SEAS = "School of Engineering and Applied Science"
_NURSING = "School of Nursing"
_MED = "Perelman School of Medicine"
_LAW = "University of Pennsylvania Carey Law School"
_GSE = "Graduate School of Education"
_DENTAL = "School of Dental Medicine"
_DESIGN = "Stuart Weitzman School of Design"
_SP2 = "School of Social Policy and Practice"
_VET = "School of Veterinary Medicine"
_ANNENBERG = "Annenberg School for Communication"

SCHOOLS: list[dict] = [
    {
        "name": _SAS,
        "sort_order": 1,
        "description": (
            "Penn Arts & Sciences is the intellectual core of the University, home to the "
            "College of Arts & Sciences (the undergraduate liberal-arts program), the "
            "Graduate Division, and the College of Liberal & Professional Studies. Its "
            "departments span the humanities, the social sciences and the natural "
            "sciences, and it teaches a large share of every Penn undergraduate's coursework."
        ),
    },
    {
        "name": _WHARTON,
        "sort_order": 2,
        "description": (
            "Founded in 1881 by industrialist Joseph Wharton, the Wharton School is the "
            "world's first collegiate business school. It educates undergraduates (the "
            "Bachelor of Science in Economics), MBAs, doctoral students and executives "
            "across finance, marketing, management, operations, analytics and "
            "entrepreneurship, and houses research centers in financial research, real "
            "estate and retailing."
        ),
    },
    {
        "name": _SEAS,
        "sort_order": 3,
        "description": (
            "Penn Engineering traces to 1852 and educates and conducts research across "
            "departments including bioengineering; chemical and biomolecular engineering; "
            "computer and information science; electrical and systems engineering; "
            "materials science; and mechanical engineering and applied mechanics. It is "
            "home to the Singh Center for Nanotechnology and the GRASP robotics lab."
        ),
    },
    {
        "name": _NURSING,
        "sort_order": 4,
        "description": (
            "Established as an independent school in 1950, Penn Nursing is consistently "
            "ranked among the very best nursing schools in the world. It offers the "
            "BSN, master's, DNP and PhD, and pairs clinical education with leading "
            "research on health outcomes, aging and global women's health."
        ),
    },
    {
        "name": _MED,
        "sort_order": 5,
        "description": (
            "The Raymond and Ruth Perelman School of Medicine, founded in 1765, is the "
            "first medical school in the United States. Part of Penn Medicine, it spans "
            "MD and MD-PhD education and a vast biomedical research enterprise anchored "
            "by the Abramson Cancer Center and institutes in aging, neuroscience and "
            "transplantation."
        ),
    },
    {
        "name": _LAW,
        "sort_order": 6,
        "description": (
            "The University of Pennsylvania Carey Law School, whose full-time legal "
            "program dates to 1850, is one of the nation's leading law schools, known for "
            "cross-disciplinary study with Penn's business, medical and policy schools. "
            "It houses the Institute for Law & Economics and centers on technology, "
            "innovation and the rule of law."
        ),
    },
    {
        "name": _GSE,
        "sort_order": 7,
        "description": (
            "The Penn Graduate School of Education, established in 1914, is one of the "
            "nation's premier education schools, advancing research and practice in "
            "teaching, learning analytics, education policy and higher education through "
            "centers such as the Consortium for Policy Research in Education."
        ),
    },
    {
        "name": _DENTAL,
        "sort_order": 8,
        "description": (
            "Penn Dental Medicine, founded in 1878, educates DMD and advanced-standing "
            "dental students and conducts oral-health research through the Center for "
            "Innovation & Precision Dentistry and the Center for Integrative Global Oral "
            "Health."
        ),
    },
    {
        "name": _DESIGN,
        "sort_order": 9,
        "description": (
            "The Stuart Weitzman School of Design (whose architecture department dates to "
            "1890) educates designers of the built and natural environment — in "
            "architecture, city and regional planning, landscape architecture, historic "
            "preservation and fine arts — through studios and research units including "
            "PennPraxis and the Center for Environmental Building & Design."
        ),
    },
    {
        "name": _SP2,
        "sort_order": 10,
        "description": (
            "The School of Social Policy & Practice, founded in 1908, advances social "
            "justice through education and research in social work, social policy, "
            "nonprofit leadership and clinical practice, addressing inequality, health "
            "equity and mass incarceration."
        ),
    },
    {
        "name": _VET,
        "sort_order": 11,
        "description": (
            "Penn Vet, founded in 1884, is one of the world's leading veterinary schools, "
            "educating VMD students and running two teaching hospitals (Ryan in "
            "Philadelphia and New Bolton Center in Kennett Square) alongside research on "
            "infectious disease, cancer and food-animal health."
        ),
    },
    {
        "name": _ANNENBERG,
        "sort_order": 12,
        "description": (
            "The Annenberg School for Communication, founded in 1959, is a graduate "
            "school and research center for the study of communication and media, home "
            "to the Annenberg Public Policy Center and the Center for Advanced Research "
            "in Global Communication."
        ),
    },
]

# Each school's official website (verified to resolve at author time).
_SCHOOL_WEBSITE: dict[str, str] = {
    _SAS: "https://www.sas.upenn.edu/",
    _WHARTON: "https://www.wharton.upenn.edu/",
    _SEAS: "https://www.seas.upenn.edu/",
    _NURSING: "https://www.nursing.upenn.edu/",
    _MED: "https://www.med.upenn.edu/",
    _LAW: "https://www.law.upenn.edu/",
    _GSE: "https://www.gse.upenn.edu/",
    _DENTAL: "https://www.dental.upenn.edu/",
    _DESIGN: "https://www.design.upenn.edu/",
    _SP2: "https://www.sp2.upenn.edu/",
    _VET: "https://www.vet.upenn.edu/",
    _ANNENBERG: "https://www.asc.upenn.edu/",
}

# Rich, sourced About-tab content per school. Deans + titles and founding years are
# quoted from each school's official leadership / history / archives page (verified
# 2026-06-10). Notable-faculty rosters are not published uniformly per school and are
# omitted rather than hand-picked without an official list (recorded in _ABOUT_OMITTED).
# SAS and Weitzman state no single school founding year (their founding traces to Penn's
# origins / the 1890 architecture department), so founded is honestly omitted there.
_ABOUT_DETAIL: dict[str, dict] = {
    _SAS: {
        "leadership": (
            "Mark Trodden — Dean (Thomas S. Gates, Jr. Professor of Physics & Astronomy)"
        ),
        "research_centers": [
            "MindCORE",
            "Center for Mathematical Biology",
            "Positive Psychology Center",
            "Price Lab for Digital Humanities",
        ],
        "source": {
            "label": "Penn Arts & Sciences — Leadership",
            "url": "https://www.sas.upenn.edu/leadership/",
        },
    },
    _WHARTON: {
        "founded": 1881,
        "leadership": "Erika H. James — Dean of the Wharton School",
        "named_for": "Joseph Wharton, the industrialist who founded the school in 1881",
        "research_centers": [
            "Rodney L. White Center for Financial Research",
            "Samuel Zell and Robert Lurie Real Estate Center",
            "Jay H. Baker Retailing Center",
            "Wharton Accountable AI Lab",
        ],
        "source": {
            "label": "The Wharton School — About the Dean / History",
            "url": "https://www.wharton.upenn.edu/history/",
        },
    },
    _SEAS: {
        "founded": 1852,
        "leadership": "Vijay Kumar — Nemirovsky Family Dean of Penn Engineering",
        "research_centers": [
            "Singh Center for Nanotechnology",
            "GRASP Lab (General Robotics, Automation, Sensing & Perception)",
            "SIG Center for Computer Graphics",
        ],
        "source": {
            "label": "Penn Engineering — School Leadership",
            "url": "https://www.seas.upenn.edu/about/school-leadership/",
        },
    },
    _NURSING: {
        "founded": 1950,
        "leadership": "Antonia M. Villarruel — Margaret Bond Simon Dean of Nursing",
        "research_centers": [
            "Barbara Bates Center for the Study of the History of Nursing",
            "Center for Global Women's Health",
            "Center for Health Outcomes and Policy Research (CHOPR)",
            "NewCourtland Center for Transitions and Health",
        ],
        "source": {
            "label": "Penn Nursing — Research Centers",
            "url": "https://www.nursing.upenn.edu/research/research-centers/",
        },
    },
    _MED: {
        "founded": 1765,
        "leadership": (
            "Jonathan A. Epstein — Dean of the Perelman School of Medicine and EVP of "
            "the University for the Health System"
        ),
        "named_for": "Raymond and Ruth Perelman",
        "research_centers": [
            "Abramson Cancer Center",
            "Institute on Aging",
            "Mahoney Institute for Neurosciences",
            "Penn Transplant Institute",
        ],
        "source": {
            "label": "Perelman School of Medicine — History Timeline",
            "url": "https://www.med.upenn.edu/evpdean/perelman-school-of-medicine-history-timeline.html",
        },
    },
    _LAW: {
        "founded": 1850,
        "leadership": "Sophia Z. Lee — Dean (Bernard G. Segal Professor of Law)",
        "named_for": "the W.P. Carey Foundation (renamed Penn Carey Law in 2019)",
        "research_centers": [
            "Institute for Law & Economics",
            "Center for Technology, Innovation & Competition",
            "Center for Ethics and the Rule of Law",
        ],
        "source": {
            "label": "Penn Carey Law — Dean's Office",
            "url": "https://www.law.upenn.edu/dean/",
        },
    },
    _GSE: {
        "founded": 1914,
        "leadership": (
            "Katharine O. Strunk — Dean (George and Diane Weiss Professor of Education)"
        ),
        "research_centers": [
            "Consortium for Policy Research in Education (CPRE)",
            "Penn Center for Learning Analytics",
            "Institute for Research on Higher Education (IRHE)",
        ],
        "source": {
            "label": "Penn GSE — Leadership",
            "url": "https://www.gse.upenn.edu/about-us/leadership",
        },
    },
    _DENTAL: {
        "founded": 1878,
        "leadership": "Mark S. Wolff — Morton Amsterdam Dean",
        "research_centers": [
            "Center for Innovation & Precision Dentistry (CiPD)",
            "Center for Integrative Global Oral Health (CIGOH)",
            "Leon Levy Center for Oral Health Research",
        ],
        "source": {
            "label": "Penn Dental Medicine — School Leadership",
            "url": "https://www.dental.upenn.edu/about-us/school-leadership/",
        },
    },
    _DESIGN: {
        "leadership": "Frederick Steiner — Dean and Paley Professor",
        "named_for": "Stuart Weitzman (named the Weitzman School of Design in 2019)",
        "research_centers": [
            "PennPraxis",
            "Center for Environmental Building & Design",
            "Center for the Preservation of Civil Rights Sites (CPCRS)",
        ],
        "source": {
            "label": "Stuart Weitzman School of Design — About",
            "url": "https://www.design.upenn.edu/about-weitzman-school",
        },
    },
    _SP2: {
        "founded": 1908,
        "leadership": "Sara S. Bachman — Dean",
        "source": {
            "label": "Penn SP2 — Who We Are",
            "url": "https://www.sp2.upenn.edu/who-we-are/",
        },
    },
    _VET: {
        "founded": 1884,
        "leadership": "Andrew M. Hoffman — Gilbert S. Kahn Dean of Veterinary Medicine",
        "research_centers": [
            "Penn Vet Cancer Center",
            "Center for Animal Transgenesis & Germ Cell Research",
            "Institute for Infectious & Zoonotic Diseases",
        ],
        "source": {
            "label": "Penn Vet — Research",
            "url": "https://www.vet.upenn.edu/research/",
        },
    },
    _ANNENBERG: {
        "founded": 1959,
        "leadership": "Sarah Banet-Weiser — Dean",
        "named_for": "Walter H. Annenberg",
        "research_centers": [
            "Annenberg Public Policy Center",
            "Center for Advanced Research in Global Communication",
            "Institute for the Study of Citizens and Politics",
        ],
        "source": {
            "label": "Annenberg School for Communication — Research Centers",
            "url": "https://www.asc.upenn.edu/research/centers",
        },
    },
}

# About-detail fields omitted per school (verified-unavailable), recorded in each
# school's _standard.omitted. Faculty rosters are omitted for every school (no uniform
# official notable-faculty list). SAS and Weitzman additionally omit founded (no single
# school founding year stated officially). SP2's official "Who We Are" page lists
# thematic research areas rather than named centers, so SP2 omits research_centers.
_ABOUT_OMITTED: dict[str, list[str]] = {
    _SAS: ["about_detail.founded", "about_detail.faculty"],
    _WHARTON: ["about_detail.faculty"],
    _SEAS: ["about_detail.faculty"],
    _NURSING: ["about_detail.faculty"],
    _MED: ["about_detail.faculty"],
    _LAW: ["about_detail.faculty"],
    _GSE: ["about_detail.faculty"],
    _DENTAL: ["about_detail.faculty"],
    _DESIGN: ["about_detail.founded", "about_detail.faculty"],
    _SP2: ["about_detail.faculty", "about_detail.research_centers"],
    _VET: ["about_detail.faculty"],
    _ANNENBERG: ["about_detail.faculty"],
}

# ── Channel feeds + official social links ──────────────────────────────────
# Institution-wide socials (official Penn handles) + news page (Penn Today).
_INSTITUTION_CONTENT: dict = {
    "news_url": "https://penntoday.upenn.edu/",
    "social": {
        "instagram": "https://www.instagram.com/uofpenn/",
        "linkedin": "https://www.linkedin.com/school/university-of-pennsylvania/",
        "x": "https://x.com/Penn",
        "youtube": "https://www.youtube.com/UnivPennsylvania",
        "facebook": "https://www.facebook.com/UnivPennsylvania",
    },
}

# Wharton MBA keyword-relevant feed (the flagship program).
_WHARTON_MBA_CONTENT: dict = {
    "news_url": "https://www.wharton.upenn.edu/story/",
    "keywords": ["wharton", "mba", "business school", "finance", "consulting"],
    "social": {
        "instagram": "https://www.instagram.com/whartonschool/",
        "linkedin": "https://www.linkedin.com/school/the-wharton-school/",
        "x": "https://x.com/Wharton",
        "youtube": "https://www.youtube.com/wharton",
        "facebook": "https://www.facebook.com/whartonschool",
    },
}

# ── The program catalog (real majors, organized by school) ─────────────────
# slug = idempotency key. Every program maps to its owning school from Penn's official
# structure. The profile covers the institution and all twelve schools; the program
# catalog spans the undergraduate majors (A.B./B.A., B.S.E. and B.S.N.), the Wharton
# MBA, and — added in the resume run — the Perelman School of Medicine MD and the Penn
# Carey Law JD (each with a first-party-verified cost of attendance and admissions set).
# The remaining graduate/professional schools (Dental, Vet, GSE, Weitzman/Design, SP2,
# Annenberg) are enriched at the school level and are queued for a later resume run,
# pending first-party-verifiable per-program tuition.
_FLAGSHIP = "penn-wharton-mba"
PROGRAMS: list[dict] = [
    # ── The Wharton School ──
    {
        "slug": "penn-wharton-mba",
        "school": _WHARTON,
        "program_name": "Master of Business Administration (MBA)",
        "degree_type": "masters",
        "cip": "52.02",
        "duration_months": 21,
        "description": (
            "Wharton's full-time MBA — the flagship two-year program of the world's first "
            "collegiate business school, with 18+ majors and one of the deepest finance "
            "and analytics faculties anywhere."
        ),
    },
    {
        "slug": "penn-wharton-economics-bs",
        "school": _WHARTON,
        "program_name": "Bachelor of Science in Economics (Wharton)",
        "degree_type": "bachelors",
        "cip": "52.02",
        "duration_months": 48,
        "description": (
            "Wharton's undergraduate Bachelor of Science in Economics — a business degree "
            "with concentrations in finance, management, marketing, statistics and more, "
            "grounded in Penn's liberal-arts core."
        ),
    },
    # ── School of Engineering and Applied Science ──
    {
        "slug": "penn-computer-science-bse",
        "school": _SEAS,
        "program_name": "Computer Science (BSE)",
        "degree_type": "bachelors",
        "cip": "11.01",
        "duration_months": 48,
        "description": (
            "The Bachelor of Science in Engineering in Computer Science, in Penn's "
            "Department of Computer and Information Science — theory, systems, AI and "
            "machine learning."
        ),
    },
    {
        "slug": "penn-bioengineering-bse",
        "school": _SEAS,
        "program_name": "Bioengineering (BSE)",
        "degree_type": "bachelors",
        "cip": "14.05",
        "duration_months": 48,
        "description": (
            "Bioengineering — engineering principles applied to medicine and biology, "
            "from biomaterials and imaging to systems and synthetic biology."
        ),
    },
    {
        "slug": "penn-mechanical-engineering-bse",
        "school": _SEAS,
        "program_name": "Mechanical Engineering and Applied Mechanics (BSE)",
        "degree_type": "bachelors",
        "cip": "14.19",
        "duration_months": 48,
        "description": (
            "Mechanical engineering and applied mechanics — mechanics, design, robotics "
            "and energy systems."
        ),
    },
    # ── School of Nursing ──
    {
        "slug": "penn-nursing-bsn",
        "school": _NURSING,
        "program_name": "Nursing (BSN)",
        "degree_type": "bachelors",
        "cip": "51.38",
        "duration_months": 48,
        "description": (
            "The Bachelor of Science in Nursing at the top-ranked Penn Nursing — clinical "
            "education paired with the science and research of a leading nursing school."
        ),
    },
    # ── School of Arts and Sciences ──
    {
        "slug": "penn-economics-ba",
        "school": _SAS,
        "program_name": "Economics",
        "degree_type": "bachelors",
        "cip": "45.06",
        "duration_months": 48,
        "description": "Economics in the College of Arts & Sciences — micro, macro, econometrics.",
    },
    {
        "slug": "penn-biology-ba",
        "school": _SAS,
        "program_name": "Biology",
        "degree_type": "bachelors",
        "cip": "26.01",
        "duration_months": 48,
        "description": "Biology — molecular, cellular, organismal and ecological life science.",
    },
    {
        "slug": "penn-philosophy-ba",
        "school": _SAS,
        "program_name": "Philosophy",
        "degree_type": "bachelors",
        "cip": "38.01",
        "duration_months": 48,
        "description": "Philosophy — logic, ethics, metaphysics and the history of philosophy.",
    },
    {
        "slug": "penn-political-science-ba",
        "school": _SAS,
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
        "slug": "penn-ppe-ba",
        "school": _SAS,
        "program_name": "Philosophy, Politics and Economics (PPE)",
        "degree_type": "bachelors",
        "cip": "30.05",
        "duration_months": 48,
        "description": (
            "Penn's interdisciplinary Philosophy, Politics & Economics major — analytic "
            "tools from three disciplines applied to questions of policy and ethics."
        ),
    },
    {
        "slug": "penn-mathematics-ba",
        "school": _SAS,
        "program_name": "Mathematics",
        "degree_type": "bachelors",
        "cip": "27.01",
        "duration_months": 48,
        "description": "Mathematics — analysis, algebra, geometry and probability.",
    },
    {
        "slug": "penn-psychology-ba",
        "school": _SAS,
        "program_name": "Psychology",
        "degree_type": "bachelors",
        "cip": "42.01",
        "duration_months": 48,
        "description": "Psychology — cognitive, developmental, social and clinical science.",
    },
    {
        "slug": "penn-english-ba",
        "school": _SAS,
        "program_name": "English",
        "degree_type": "bachelors",
        "cip": "23.01",
        "duration_months": 48,
        "description": "English — literature in English, criticism and creative writing.",
    },
    {
        "slug": "penn-chemistry-ba",
        "school": _SAS,
        "program_name": "Chemistry",
        "degree_type": "bachelors",
        "cip": "40.05",
        "duration_months": 48,
        "description": "Chemistry — organic, inorganic, physical and chemical biology.",
    },
    {
        "slug": "penn-physics-ba",
        "school": _SAS,
        "program_name": "Physics",
        "degree_type": "bachelors",
        "cip": "40.08",
        "duration_months": 48,
        "description": "Physics — from particles and fields to condensed matter and astrophysics.",
    },
    # ── Perelman School of Medicine ──
    {
        "slug": "penn-md",
        "school": _MED,
        # Professional doctorate — modeled as a graduate ("masters") program, matching
        # the fleet convention for MD/JD/DMD professional degrees.
        "program_name": "Doctor of Medicine (MD)",
        "degree_type": "masters",
        "cip": "51.12",
        "duration_months": 48,
        "description": (
            "The Doctor of Medicine at the Perelman School of Medicine — founded in 1765 "
            "as the first medical school in the United States. A four-year MD combining "
            "foundational biomedical science, early and extensive clinical training "
            "across the Penn Medicine academic health system, and broad research and "
            "dual-degree pathways (including MD-PhD and MD-MBA)."
        ),
    },
    # ── University of Pennsylvania Carey Law School ──
    {
        "slug": "penn-jd",
        "school": _LAW,
        "program_name": "Juris Doctor (JD)",
        "degree_type": "masters",
        "cip": "22.01",
        "duration_months": 36,
        "description": (
            "The Juris Doctor at the University of Pennsylvania Carey Law School, one of "
            "the nation's leading law schools. A three-year program distinguished by "
            "cross-disciplinary study with Penn's business, medical and policy schools "
            "and by a wide range of joint degrees, certificates and clinics."
        ),
    },
]

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

# Full official program names (program-page title); equal to the program name here.
_FULL_NAME_BY_SLUG: dict[str, str] = {p["slug"]: p["program_name"] for p in PROGRAMS}

# Official program/department home pages (verified to resolve at author time).
_WEBSITE_BY_SLUG: dict[str, str] = {
    "penn-wharton-mba": "https://mba.wharton.upenn.edu/",
    "penn-wharton-economics-bs": "https://undergrad.wharton.upenn.edu/",
    "penn-computer-science-bse": "https://www.cis.upenn.edu/",
    "penn-bioengineering-bse": "https://be.seas.upenn.edu/",
    "penn-mechanical-engineering-bse": "https://www.me.upenn.edu/",
    "penn-nursing-bsn": "https://www.nursing.upenn.edu/",
    "penn-economics-ba": "https://economics.sas.upenn.edu/",
    "penn-biology-ba": "https://www.bio.upenn.edu/",
    "penn-philosophy-ba": "https://philosophy.sas.upenn.edu/",
    "penn-political-science-ba": "https://www.polisci.upenn.edu/",
    "penn-ppe-ba": "https://ppe.sas.upenn.edu/",
    "penn-mathematics-ba": "https://www.math.upenn.edu/",
    "penn-psychology-ba": "https://psychology.sas.upenn.edu/",
    "penn-english-ba": "https://www.english.upenn.edu/",
    "penn-chemistry-ba": "https://www.chem.upenn.edu/",
    "penn-physics-ba": "https://www.physics.upenn.edu/",
    "penn-md": "https://www.med.upenn.edu/admiss/",
    "penn-jd": "https://www.law.upenn.edu/admissions/jd/",
}

# ── Who-it's-for + highlights (catalog baselines) ──────────────────────────
_WHO_BASELINE = (
    "Academically exceptional students seeking an Ivy League education that pairs "
    "research depth with Penn's interdisciplinary, pre-professional culture, with "
    "full-need financial aid met by grants."
)
_HL_BASELINE = ["Ivy League", "Carnegie R1 research university", "Need-met-with-grants aid"]
_WHO_BY_SLUG = {
    "penn-wharton-mba": (
        "Ambitious professionals seeking a top-ranked, finance- and analytics-strong MBA "
        "with deep recruiting into consulting, financial services and technology."
    ),
    "penn-wharton-economics-bs": (
        "Undergraduates who want a rigorous, quantitative business education from the "
        "world's first collegiate business school, within an Ivy League liberal-arts core."
    ),
    "penn-computer-science-bse": (
        "Technically strong students who want an Ivy League computer science degree with "
        "deep access to AI, robotics and systems research."
    ),
    "penn-nursing-bsn": (
        "Students drawn to nursing and health who want a clinical education at the "
        "top-ranked Penn Nursing inside a major research university and health system."
    ),
    "penn-md": (
        "Students committed to medicine who want an MD at the first U.S. medical school, "
        "within one of the nation's leading academic health systems, with strong "
        "research and dual-degree pathways."
    ),
    "penn-jd": (
        "Aspiring lawyers seeking a top-tier JD with deep cross-disciplinary access to "
        "Penn's business, medical and policy schools and a wide range of joint degrees."
    ),
}
_HL_BY_SLUG = {
    "penn-wharton-mba": [
        "World's first business school",
        "$175,000 median base salary",
        "18+ MBA majors",
    ],
    "penn-wharton-economics-bs": [
        "Undergraduate business degree",
        "Liberal-arts core",
        "Finance & analytics depth",
    ],
    "penn-computer-science-bse": [
        "GRASP robotics lab",
        "AI & machine learning",
        "Ivy League engineering",
    ],
    "penn-nursing-bsn": [
        "Top-ranked nursing school",
        "Clinical + research",
        "Penn Medicine health system",
    ],
    "penn-md": [
        "First U.S. medical school (1765)",
        "Penn Medicine academic health system",
        "MD-PhD & dual-degree options",
    ],
    "penn-jd": [
        "Top-tier law school",
        "Cross-disciplinary joint degrees",
        "University City, Philadelphia",
    ],
}

# ── Curriculum / tracks, where published (the flagship) ────────────────────
# Wharton MBA majors (real, from the Wharton MBA program). Students choose at least one.
_TRACKS_BY_SLUG: dict[str, dict] = {
    "penn-wharton-mba": {
        "label": "Wharton MBA majors",
        "note": (
            "After a flexible core, Wharton MBA students complete at least one of the "
            "school's majors (and may double-major); finance, management and the "
            "analytics-heavy majors are among the largest."
        ),
        "items": [
            {"name": "Finance"},
            {"name": "Management"},
            {"name": "Marketing"},
            {"name": "Entrepreneurship & Innovation"},
            {"name": "Business Analytics"},
            {"name": "Operations, Information and Decisions"},
            {"name": "Real Estate"},
            {"name": "Health Care Management"},
            {"name": "Statistics"},
            {"name": "Strategic Management"},
        ],
        "source": "The Wharton School — MBA Program",
        "source_url": "https://mba.wharton.upenn.edu/academics/",
    },
}

# ── Program-specific cost ──────────────────────────────────────────────────
# Penn undergraduate cost (Penn "Facts" tuition/fees + College Navigator on-campus COA;
# College Scorecard average net price). The Wharton MBA carries its own verified budget.
_TUITION_UG = 71236
_UNDERGRAD_COA = 92288
_AVG_NET_PRICE = 28699
# Wharton MBA 2026-27 cost of attendance (official Wharton MBA budget).
_MBA_TUITION = 87970
_MBA_COA = 135441
_COST_BY_SLUG: dict[str, dict] = {
    "penn-wharton-mba": {
        "tuition_usd": _MBA_TUITION,
        "total_cost_of_attendance": _MBA_COA,
        "breakdown": {
            "tuition": _MBA_TUITION,
            "general_fee": 4268,
            "clinical_fee": 770,
            "housing": 21258,
            "food": 9287,
            "books_supplies": 1123,
            "health_insurance": 5018,
            "total_cost_of_attendance": _MBA_COA,
        },
        "funded": False,
        "note": (
            "Official Wharton full-time MBA cost-of-attendance budget for 2026-27 "
            "(tuition $87,970; total $135,441). Wharton awards need- and merit-based "
            "fellowships that reduce the net cost for many students."
        ),
        "source": "The Wharton School — MBA Tuition & Fees",
        "source_url": "https://mba-inside.wharton.upenn.edu/financial-aid/tuition-fees/",
        "year": "2026-27",
    },
    # Perelman School of Medicine MD — official PSOM student budget for 2026-27
    # (Year 1, 10 months). Tuition $73,852; tuition+fees subtotal $80,511; grand total
    # (incl. health insurance + living expenses) $117,173.
    "penn-md": {
        "tuition_usd": 73852,
        "total_cost_of_attendance": 117173,
        "breakdown": {
            "tuition": 73852,
            "general_fee": 4268,
            "clinical_fee": 770,
            "technology_fee": 1566,
            "disability_fee": 55,
            "tuition_and_fees_subtotal": 80511,
            "health_insurance": 4662,
            "total_cost_of_attendance": 117173,
        },
        "funded": False,
        "note": (
            "Official Perelman School of Medicine MD student budget for 2026-27 (first "
            "year, 10 months): tuition $73,852, tuition and fees $80,511, and a total "
            "first-year cost of attendance of $117,173 including health insurance and "
            "living expenses. Penn Medicine offers need-based scholarships that reduce "
            "the net cost for many students."
        ),
        "source": "Perelman School of Medicine — MD Student Budget, Academic Year 2026-27",
        "source_url": (
            "https://www.med.upenn.edu/student/assets/user-content/documents/policies/"
            "tuition-2026-27.pdf"
        ),
        "year": "2026-27",
    },
    # Penn Carey Law JD — official SRFS JD cost of attendance for 2026-27.
    # Tuition $81,796; fees general $4,268 + clinical $770 + learning support $1,350;
    # total budgeted cost of attendance $120,294.
    "penn-jd": {
        "tuition_usd": 81796,
        "total_cost_of_attendance": 120294,
        "breakdown": {
            "tuition": 81796,
            "general_fee": 4268,
            "clinical_fee": 770,
            "learning_support_fee": 1350,
            "total_cost_of_attendance": 120294,
        },
        "funded": False,
        "note": (
            "Official Penn Student Registration & Financial Services JD cost of "
            "attendance for 2026-27: tuition $81,796 plus the general ($4,268), clinical "
            "($770) and learning-support ($1,350) fees, for a total budgeted cost of "
            "attendance of $120,294. Penn Carey Law awards need- and merit-based grants "
            "that reduce the net cost for many students."
        ),
        "source": "Penn Student Registration & Financial Services — Penn Carey Law JD",
        "source_url": "https://srfs.upenn.edu/penn-carey-law-jd",
        "year": "2026-27",
    },
}

# ── Program-specific outcomes ──────────────────────────────────────────────
# The flagship Wharton MBA carries its full official employment report (below). The other
# programs use the College Scorecard Field-of-Study median earnings (one year after
# completion) for an awarded CIP at UNITID 215062 where the federal data publishes one;
# programs whose CIP earnings are suppressed fall back to the institution 10-year median.
# Tuples are (median_earnings_1yr, cip).
_FOS_OUTCOMES: dict[str, tuple[int, str]] = {
    "penn-computer-science-bse": (146204, "11.01"),
    "penn-economics-ba": (89097, "45.06"),
    "penn-nursing-bsn": (80943, "51.38"),
    "penn-philosophy-ba": (73053, "38.01"),
    "penn-political-science-ba": (65473, "45.10"),
    "penn-biology-ba": (31055, "26.01"),
}

# Verbatim methodology for the program-scope Scorecard FOS earnings figure.
_FOS_CONDITIONS = (
    "Median earnings of graduates who received federal financial aid, measured "
    "approximately one year after program completion; reported by the U.S. Department of "
    "Education College Scorecard Field of Study by 4-digit CIP code. Programs with too "
    "few completers are suppressed."
)

# Institution-wide outcomes fallback (College Scorecard, UNITID 215062), used for degree
# programs whose program-level one-year earnings are suppressed.
_OUTCOMES_INSTITUTION = {
    "median_salary": 111371,
    "scope": "institution",
    "conditions": (
        "Penn institution-wide median earnings ten years after entry (College Scorecard, "
        "UNITID 215062); a program-level one-year earnings figure is not published "
        "(suppressed) for this field of study."
    ),
    "source": "U.S. Dept. of Education College Scorecard (UNITID 215062)",
    "source_url": "https://collegescorecard.ed.gov/school/?215062",
}

# The flagship Wharton MBA outcomes — quoted from the official Wharton MBA Career Report
# (Class of 2024 full-time), overriding the institution/FOS fallback.
_WHARTON_MBA_OUTCOMES: dict = {
    "median_salary": 175000,
    "employment_rate": 0.931,
    "employment_timeframe": "reported job offers within three months of graduation",
    "class_size": 916,
    "scope": "program",
    "top_industries": [
        "Financial Services",
        "Consulting",
        "Technology",
        "Health Care",
        "Media, Entertainment & Sports",
    ],
    "top_employers": [
        "McKinsey & Company",
        "Boston Consulting Group (BCG)",
        "Bain & Company",
        "Goldman Sachs",
        "J.P. Morgan",
        "Morgan Stanley",
        "Amazon",
        "Google",
    ],
    "conditions": [
        "Wharton MBA Class of 2024, full-time employment reported within three months of "
        "graduation (N = 916 graduates).",
        "Of 916 graduates, 634 (69.2%) sought employment; of those, 590 (93.1%) reported "
        "job offers and 559 (88.2%) accepted.",
        "Median base salary is for the first year only and does not include signing or "
        "other bonuses, options, or carried interest.",
        "Financial Services drew 36.6% of the class, Consulting 25.2%, Technology 14.1%.",
        "Data collected and reported in accordance with MBA Career Services & Employer "
        "Alliance (MBA CSEA) standards.",
    ],
    "source": "The Wharton School — MBA Career Report, Class of 2024",
    "source_url": (
        "https://statistics.mbacareers.wharton.upenn.edu/wp-content/uploads/2024/12/"
        "2024-Career-Report-FINAL.pdf"
    ),
}

# ── Class profile, where published (the flagship) ──────────────────────────
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    "penn-wharton-mba": {
        "cohort_size": "≈877 enrolled (Wharton MBA Class of 2024)",
        "international_pct": 0.35,
        "note": (
            "Wharton MBA Class of 2024 at enrollment: 877 students, 50% women, 35% "
            "international, 77 countries represented, median 5 years of work experience "
            "(MBA Admissions, at time of enrollment)."
        ),
        "source": "The Wharton School — MBA Career Report, Class of 2024 (Demographics)",
        "source_url": (
            "https://statistics.mbacareers.wharton.upenn.edu/wp-content/uploads/2024/12/"
            "2024-Career-Report-FINAL.pdf"
        ),
    },
}

# ── Faculty (lead + directory link), where confidently sourced (the flagship) ──
_FACULTY_BY_SLUG: dict[str, dict] = {
    "penn-wharton-mba": {
        "lead": [
            {
                "name": "Erika H. James",
                "title": (
                    "Dean of the Wharton School (Reliance Professor of Management "
                    "and Private Enterprise)"
                ),
            },
            {
                "name": "Adam Grant",
                "title": (
                    "Saul P. Steinberg Professor of Management; organizational "
                    "psychologist and author"
                ),
            },
        ],
        "note": (
            "Wharton's faculty spans finance, management, marketing, operations and "
            "statistics; Dean Erika H. James leads the school and organizational "
            "psychologist Adam Grant is among its most widely known professors."
        ),
        "directory_url": "https://www.wharton.upenn.edu/faculty/",
    },
}

# ── Aggregated, cited student-review themes (≥2 third-party sources, the flagship) ──
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "penn-wharton-mba": {
        "summary": (
            "Students and third-party guides consistently describe the Wharton MBA as an "
            "elite, finance- and analytics-strong program with an enormous course "
            "catalog, deep recruiting into consulting and financial services, and a "
            "powerful global alumni network; common cautions are a large class size, a "
            "high cost of attendance, and an intense, quantitatively demanding pace."
        ),
        "themes": [
            {
                "label": "Academic strength & breadth",
                "sentiment": "positive",
                "detail": "World-class faculty and one of the largest MBA course catalogs.",
            },
            {
                "label": "Finance & consulting recruiting",
                "sentiment": "positive",
                "detail": "Exceptional placement into financial services, consulting and tech.",
            },
            {
                "label": "Alumni network",
                "sentiment": "positive",
                "detail": "A large, influential global alumni network opens doors widely.",
            },
            {
                "label": "Cost",
                "sentiment": "caution",
                "detail": "Total cost of attendance exceeds $135,000 per year.",
            },
            {
                "label": "Large & fast-paced",
                "sentiment": "caution",
                "detail": "A big class and a quantitatively intense pace can feel competitive.",
            },
        ],
        "sources": [
            {
                "label": "Poets&Quants — Wharton MBA Employment Report 2024",
                "url": "https://poetsandquants.com/2024/12/27/wharton-mba-employment-report-2024/",
            },
            {
                "label": "U.S. News — Wharton (Penn) Best Business Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/the-wharton-school-01099",
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
# Undergraduate admission via the Common Application, Coalition Application, or QuestBridge.
# Penn reinstated standardized testing for the 2025-26 cycle (fall-2026 entry); a hardship
# waiver is available.
_REQ_UNDERGRAD = {
    "materials": [
        {
            "name": "Common Application, Coalition Application, or QuestBridge",
            "required": True,
        },
        {"name": "Penn-specific essays/supplement", "required": True},
        {"name": "School report + secondary-school transcript", "required": True},
        {"name": "Counselor recommendation", "required": True},
        {"name": "Two teacher recommendations", "required": True},
        {"name": "$75 application fee; fee waivers available", "required": True},
        {
            "name": "SAT or ACT scores",
            "required": True,
            "note": (
                "Required for the 2025-26 cycle (fall-2026 entry) — Penn reinstated "
                "standardized testing; a hardship waiver is available."
            ),
        },
    ],
    "deadlines": [
        {"round": "Early Decision", "date": "November 1"},
        {"round": "Regular Decision", "date": "January 5"},
    ],
    "recommendations": {
        "required": 3,
        "note": (
            "Two teacher recommendations in core academic subjects plus a counselor "
            "recommendation."
        ),
    },
    "application_fee": "$75 (fee waivers available)",
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "Duolingo English Test"],
            "required": False,
            "note": "English-proficiency proof may be required for non-native speakers.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Penn Admissions — First-Year Applicants",
                "url": "https://admissions.upenn.edu/how-to-apply/first-year-applicants",
            }
        ],
    },
    "source": "Penn Undergraduate Admissions",
    "source_url": "https://admissions.upenn.edu/how-to-apply/first-year-applicants",
}

# Wharton full-time MBA admission (official requirements).
_REQ_MBA = {
    "materials": [
        {"name": "Wharton MBA online application", "required": True},
        {
            "name": "GMAT or GRE",
            "required": True,
            "note": "All applicants must submit a GMAT or GRE score (no test-optional path).",
        },
        {"name": "Two required essays", "required": True},
        {"name": "One letter of recommendation (preferably from a supervisor)", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Résumé", "required": True},
        {"name": "$275 application fee", "required": True},
    ],
    "deadlines": [
        {"round": "Round 1", "date": "Early September"},
        {"round": "Round 2", "date": "Early January"},
        {"round": "Round 3", "date": "Late March / Early April"},
    ],
    "recommendations": {
        "required": 1,
        "note": (
            "One letter of recommendation from someone well acquainted with your "
            "performance in a work setting, preferably a current or former supervisor."
        ),
    },
    "application_fee": "$275 (non-refundable)",
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": False,
            "note": (
                "International applicants follow Wharton's published "
                "English-proficiency guidance."
            ),
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "The Wharton School — MBA Admissions",
                "url": "https://mba.wharton.upenn.edu/admissions/",
            }
        ],
    },
    "source": "The Wharton School — MBA Admissions",
    "source_url": "https://mba.wharton.upenn.edu/admissions/",
}


# Perelman School of Medicine MD admission (AMCAS). Letters-of-evaluation counts and the
# secondary fee are not asserted without an official figure; the universal AMCAS
# materials and Penn's published deadlines are listed.
_REQ_MD = {
    "materials": [
        {"name": "AMCAS primary application", "required": True},
        {"name": "MCAT score", "required": True},
        {
            "name": "AMCAS letters of evaluation",
            "required": True,
            "note": (
                "A committee / health-professions advisory letter where available, or "
                "individual letters of evaluation submitted through AMCAS."
            ),
        },
        {"name": "Perelman secondary (supplemental) application", "required": True},
        {"name": "Official transcripts (via AMCAS)", "required": True},
    ],
    "deadlines": [
        {"round": "AMCAS primary application", "date": "October 15"},
        {"round": "Secondary application", "date": "November 15"},
    ],
    "international": {
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Perelman School of Medicine — Admissions",
                "url": "https://www.med.upenn.edu/admiss/",
            }
        ],
    },
    "source": "Perelman School of Medicine — Admissions",
    "source_url": "https://www.med.upenn.edu/admiss/",
}

# University of Pennsylvania Carey Law School JD admission (LSAC). Penn accepts the LSAT,
# GRE or GMAT; two recommendations are required (up to four accepted).
_REQ_LAW = {
    "materials": [
        {
            "name": "LSAT, GRE, or GMAT score",
            "required": True,
            "note": "Penn Carey Law accepts the LSAT, the GRE General Test, or the GMAT.",
        },
        {"name": "LSAC Credential Assembly Service (transcripts)", "required": True},
        {"name": "Personal statement", "required": True},
        {
            "name": "Two letters of recommendation (up to four accepted)",
            "required": True,
            "note": "Submitted through the LSAC Letter of Recommendation Service.",
        },
        {"name": "Résumé", "required": True},
        {"name": "$80 application fee; fee waivers available", "required": True},
    ],
    "deadlines": [
        {"round": "Early Decision I", "date": "November 15"},
        {"round": "Early Decision II", "date": "January 7"},
        {"round": "Regular Decision", "date": "March 1"},
    ],
    "recommendations": {
        "required": 2,
        "note": (
            "At least two letters of recommendation (up to four accepted), submitted "
            "through the LSAC Letter of Recommendation Service."
        ),
    },
    "application_fee": "$80 (fee waivers available)",
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": False,
            "note": (
                "International applicants follow Penn Carey Law's "
                "English-proficiency guidance."
            ),
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Penn Carey Law — JD Admissions",
                "url": "https://www.law.upenn.edu/admissions/jd/",
            }
        ],
    },
    "source": "University of Pennsylvania Carey Law School — JD Admissions",
    "source_url": "https://www.law.upenn.edu/admissions/jd/",
}


def _requirements_for(spec: dict) -> dict:
    """Pick the admissions requirement set for a program by slug / degree type."""
    if spec["slug"] == "penn-wharton-mba":
        return dict(_REQ_MBA)
    if spec["slug"] == "penn-md":
        return dict(_REQ_MD)
    if spec["slug"] == "penn-jd":
        return dict(_REQ_LAW)
    return dict(_REQ_UNDERGRAD)


# Real Penn campus photo (College Hall) — Wikimedia Commons, hotlinkable landscape JPG
# (canonical thumbnail URL verified via the Commons API). Leads the institution hero.
_CAMPUS_PHOTO = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/"
    "College_Hall%2C_University_of_Pennsylvania%2C_Philadelphia%2C_PA.jpg/"
    "1920px-College_Hall%2C_University_of_Pennsylvania%2C_Philadelphia%2C_PA.jpg"
)


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich Penn to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Penn is absent — safe on fresh/CI databases.
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
    inst.founded_year = 1740
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.upenn.edu"
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
        # No school carries its own keyword-relevant feed (only the flagship program
        # does); always assign None so a stale value on a pre-existing row is cleared.
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
    if slug != _FLAGSHIP:
        # Only the flagship carries the program-level employment report; catalog programs
        # report a Scorecard/institution median earnings figure and omit the rest.
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
    if slug != _FLAGSHIP:
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
        # Website: verified department page where available, else the owning school's site.
        p.website_url = _WEBSITE_BY_SLUG.get(slug) or _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "in_person")
        # Only the flagship carries its own feed (content_sources omitted for the rest).
        p.content_sources = _WHARTON_MBA_CONTENT if slug == _FLAGSHIP else None
        # Cost: Wharton MBA carries its own budget; undergraduate uses published rates.
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
                    "Published undergraduate cost of attendance and average net price. "
                    "Penn is need-blind for domestic applicants and meets 100% of "
                    "demonstrated need with grant-based aid, so most families pay far "
                    "less than the sticker price (average net price ≈ $28,700)."
                ),
                "source": "U.S. Dept. of Education College Scorecard (UNITID 215062)",
                "source_url": "https://collegescorecard.ed.gov/school/?215062",
                "year": "2024-25",
            }
        # Admissions: Wharton MBA set or undergraduate set.
        p.application_requirements = _requirements_for(spec)
        # Outcomes precedence: flagship report → Scorecard FOS (program) → institution.
        if slug == _FLAGSHIP:
            outcomes = dict(_WHARTON_MBA_OUTCOMES)
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
                    "source_url": "https://collegescorecard.ed.gov/school/?215062",
                }
            else:
                outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(slug)
        p.outcomes_data = outcomes
        p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_BASELINE
        p.highlights = _HL_BY_SLUG.get(slug) or _HL_BASELINE
        # Always assign so a stale value on a pre-existing row is cleared (tracks is
        # recorded as omitted where unverified, and match_service reads program.tracks).
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        # Application deadline (upcoming undergraduate Regular Decision closes Jan 5;
        # Wharton MBA Round 2 closes early January).
        p.application_deadline = (
            date(2027, 1, 5) if spec["degree_type"] == "masters" else date(2027, 1, 5)
        )
    session.flush()
    # Reconcile legacy Penn programs (slug not in the canonical set): delete when
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
