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
reference instance. This profile brings the institution and all twelve schools to the gold
standard, and the program catalog now carries at least one verified flagship degree for
**every** school: the undergraduate majors and the Wharton MBA, the Perelman MD, the Penn
Carey Law JD, and — added in the latest resume run — the Penn Dental DMD, the Penn Vet VMD,
the Weitzman Master of Architecture, the SP2 Master of Social Work, the GSE Higher
Education M.S.Ed., and the Annenberg PhD in Communication. Each resume graduate/
professional program carries a first-party-verified cost of attendance, admissions set,
and aggregated third-party ``external_reviews`` (this run). Per-program tracks, class
profiles, and named faculty for those nodes remain honestly omitted where not
individually verified. Coverable reviews also extend to Perelman (MD), Penn Carey Law
(JD), and flagship undergraduate options (Wharton B.S.Econ, CIS, Nursing, PPE,
Bioengineering).

Depth pass (2026-06-15, pennprof7): merged ``DEPTH_REVIEWS`` for 46 coverable
programs (58/58 total external_reviews on coverable programs).

Description depth (2026-06-16, pennprof8): field-specific descriptions for all
250 programs via ``penn_field_descriptions.py`` (0% classification stubs).

Description repair (2026-06-17, pennprof9): drops the ``{program_name}:`` prefix
from every description so each opens on a field-specific clause (gold MIT/JHU
pattern); 0% name-prefixed descriptions.

Structural de-fabrication (2026-06-19, penndefab1): federal CIP rollup titles
resolved to Penn's real published degree names (verified via catalog.upenn.edu) or
dropped when an aggregation bucket; field-echo departments replaced with the real
owning Penn school; per-credential description bodies (anti-stub clean — 0%
verbatim/shared-body across credential siblings).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.penn_field_descriptions import FIELD_DESCRIPTIONS, SLUG_DESCRIPTIONS
from unipaith.data.penn_ipeds_catalog import _IPEDS_CATALOG
from unipaith.data.penn_reviews_depth import DEPTH_REVIEWS
from unipaith.data.profile_catalog_utils import (
    disambiguate_program_name,
    validate_catalog,
)
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "University of Pennsylvania"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-19"


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
            "Penn Center for Innovation": "https://pci.upenn.edu/",
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
    # Hero photo attribution (Wikimedia Commons file page verified 2026-06-14).
    "media_credit": "Wikimedia Commons / Detroit Publishing Co. (public domain)",
    "campus_photos": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/"
                "College_Hall%2C_University_of_Pennsylvania%2C_Philadelphia%2C_PA.jpg/"
                "1920px-College_Hall%2C_University_of_Pennsylvania%2C_Philadelphia%2C_PA.jpg"
            ),
            "credit": "Wikimedia Commons / Detroit Publishing Co. (public domain)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/"
                "University_of_Pennsylvania_Campus_20240528.jpg/"
                "1920px-University_of_Pennsylvania_Campus_20240528.jpg"
            ),
            "credit": "Wikimedia Commons / 颐园居 (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/"
                "Benjamin_Franklin_statue_in_front_of_College_Hall.JPG/"
                "1920px-Benjamin_Franklin_statue_in_front_of_College_Hall.JPG"
            ),
            "credit": "Wikimedia Commons / MatthewMarcucci (public domain)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/"
                "Gateway_to_Campus-_University_of_Pennsylvania_%289045354258%29.jpg/"
                "1920px-Gateway_to_Campus-_University_of_Pennsylvania_%289045354258%29.jpg"
            ),
            "credit": "Wikimedia Commons / Library Company of Philadelphia (no restrictions)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/"
                "Architecture_on_University_of_Pennsylvania_Campus_-_Philadelphia_-_Pennsylvania_-_01.jpg/"
                "1920px-Architecture_on_University_of_Pennsylvania_Campus_-_Philadelphia_-_Pennsylvania_-_01.jpg"
            ),
            "credit": "Wikimedia Commons / Adam Jones, Ph.D. (CC BY-SA 3.0)",
        },
    ],
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
    "The University of Pennsylvania is a private research university in Philadelphia, PA, "
    "founded by Benjamin Franklin and tracing its origins to 1740. Penn pairs "
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
# Penn Today RSS (verified application/rss+xml at author time) + the Almanac
# three-year academic calendar iCal (Google Calendar public feed linked from
# almanac.upenn.edu). Schools/programs filter the shared feed by keywords.
_PENN_NEWS_RSS = "https://penntoday.upenn.edu/rss.xml"
_PENN_EVENTS_ICS = {
    "url": "https://calendar.google.com/calendar/ical/pennalmanac@gmail.com/public/basic.ics",
    "type": "ical",
}
_SOCIAL_PENN = {
    "instagram": "https://www.instagram.com/uofpenn/",
    "linkedin": "https://www.linkedin.com/school/university-of-pennsylvania/",
    "x": "https://x.com/Penn",
    "youtube": "https://www.youtube.com/UnivPennsylvania",
    "facebook": "https://www.facebook.com/UnivPennsylvania",
}

_INSTITUTION_CONTENT: dict = {
    "news_rss": _PENN_NEWS_RSS,
    "news_url": "https://penntoday.upenn.edu/",
    "news_curated": False,
    "events_feed": dict(_PENN_EVENTS_ICS),
    "social": dict(_SOCIAL_PENN),
}

_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _SAS: ["Arts and Sciences", "College of Arts", "SAS", "humanities", "social sciences"],
    _WHARTON: ["Wharton", "business school", "MBA", "finance", "management"],
    _SEAS: ["Engineering", "SEAS", "computer science", "bioengineering", "robotics"],
    _NURSING: ["Nursing", "BSN", "clinical nursing", "Penn Nursing"],
    _MED: ["Perelman", "Medical School", "medicine", "Penn Medicine", "biomedical"],
    _LAW: ["Penn Carey Law", "law school", "legal", "JD"],
    _GSE: ["Graduate School of Education", "GSE", "education", "teaching"],
    _DENTAL: ["Dental Medicine", "DMD", "dentistry", "Penn Dental"],
    _DESIGN: ["Weitzman", "Design", "architecture", "planning", "landscape"],
    _SP2: ["Social Policy", "SP2", "social work", "MSW", "nonprofit"],
    _VET: ["Veterinary", "VMD", "Penn Vet", "animal health"],
    _ANNENBERG: ["Annenberg", "communication", "media studies", "journalism"],
}

_KW_STOP = {
    "and", "of", "the", "in", "for", "with", "science", "sciences", "engineering",
    "master", "doctor", "bachelor", "studies", "general",
}


def _school_content(name: str) -> dict:
    """A school's content_sources: Penn Today RSS + academic calendar filtered by keywords."""
    return {
        "news_rss": _PENN_NEWS_RSS,
        "news_url": _SCHOOL_WEBSITE.get(name, "https://www.upenn.edu"),
        "news_curated": False,
        "events_feed": dict(_PENN_EVENTS_ICS),
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": dict(_SOCIAL_PENN),
    }


def _program_keywords(spec: dict) -> list[str]:
    school_kw = list(_SCHOOL_KEYWORDS[spec["school"]])
    name = spec["program_name"].replace("&", " ").replace("/", " ")
    terms = [w for w in name.split() if len(w) > 3 and w.lower() not in _KW_STOP]
    program_term = " ".join(terms[:3]).strip()
    return ([program_term] if program_term else []) + school_kw


def _program_content(spec: dict) -> dict:
    base = _school_content(spec["school"])
    base["keywords"] = _program_keywords(spec)
    return base


# Wharton MBA keyword-relevant feed (the flagship program).
_WHARTON_MBA_CONTENT: dict = {
    "news_rss": _PENN_NEWS_RSS,
    "news_url": "https://www.wharton.upenn.edu/story/",
    "news_curated": False,
    "events_feed": dict(_PENN_EVENTS_ICS),
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
# MBA, the Perelman School of Medicine MD, the Penn Carey Law JD, and — added in the
# latest resume run — a verified flagship degree for each of the remaining six
# graduate/professional schools: the Penn Dental DMD, the Penn Vet VMD, the Weitzman
# Master of Architecture, the SP2 Master of Social Work, the GSE Higher Education
# M.S.Ed., and the Annenberg PhD in Communication. Every program carries a
# first-party-verified cost of attendance and admissions set, so each of the twelve
# schools now has at least one fully enriched program.
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
    # ── School of Dental Medicine ──
    {
        "slug": "penn-dmd",
        "school": _DENTAL,
        "program_name": "Doctor of Dental Medicine (DMD)",
        "degree_type": "masters",
        "cip": "51.04",
        "duration_months": 48,
        "description": (
            "The Doctor of Dental Medicine at Penn Dental Medicine — founded in 1878 and "
            "among the oldest university-affiliated dental schools in the nation. A "
            "four-year DMD that pairs the biomedical sciences with extensive clinical "
            "training, including care delivered through the school's Personalized Care "
            "(PASS) clinics and its Care Center for Persons with Disabilities."
        ),
    },
    # ── School of Veterinary Medicine ──
    {
        "slug": "penn-vmd",
        "school": _VET,
        "program_name": "Doctor of Veterinary Medicine (VMD)",
        "degree_type": "masters",
        "cip": "51.24",
        "duration_months": 48,
        "description": (
            "Penn Vet's four-year professional doctorate, which uniquely awards the "
            "Veterinariae Medicinae Doctoris (VMD) degree rather than the DVM. Established "
            "in 1884, Penn Vet is one of only a handful of private veterinary schools and "
            "the only one developed in association with a medical school, with a "
            "curriculum that moves from 'the animal in health' to extensive clinical "
            "training in years three and four."
        ),
    },
    # ── Stuart Weitzman School of Design ──
    {
        "slug": "penn-march",
        "school": _DESIGN,
        "program_name": "Master of Architecture (M.Arch)",
        "degree_type": "masters",
        "cip": "04.02",
        "duration_months": 36,
        "description": (
            "The professional Master of Architecture at the Stuart Weitzman School of "
            "Design — a NAAB-accredited, STEM-designated degree leading toward "
            "architectural licensure. The standard track is three years for applicants "
            "with an architecture background and three-and-a-half years (beginning in "
            "the summer) for those entering from another field."
        ),
    },
    # ── School of Social Policy and Practice ──
    {
        "slug": "penn-msw",
        "school": _SP2,
        "program_name": "Master of Social Work (MSW)",
        "degree_type": "masters",
        "cip": "44.07",
        "duration_months": 24,
        "description": (
            "The Master of Social Work at Penn's School of Social Policy & Practice — a "
            "CSWE-accredited clinical and macro practice degree earned over two academic "
            "years full-time, with part-time (three-year) and Advanced Standing "
            "(ten-month, for holders of a CSWE-accredited BSW) pathways."
        ),
    },
    # ── Graduate School of Education ──
    {
        "slug": "penn-gse-higher-education-msed",
        "school": _GSE,
        "program_name": "Higher Education (M.S.Ed.)",
        "degree_type": "masters",
        "cip": "13.04",
        "duration_months": 12,
        "description": (
            "Penn GSE's one-year, ten-course-unit Master of Science in Education in "
            "Higher Education — preparing students for administration, leadership and "
            "research roles across colleges, universities, nonprofits and "
            "education-related government agencies."
        ),
    },
    # ── Annenberg School for Communication ──
    {
        "slug": "penn-communication-phd",
        "school": _ANNENBERG,
        "program_name": "Communication (PhD)",
        "degree_type": "phd",
        "cip": "09.01",
        "duration_months": 60,
        "description": (
            "The fully funded, five-year doctoral program at the Annenberg School for "
            "Communication — one of the leading communication research programs in the "
            "nation, founded in 1958 by Walter Annenberg. Students are admitted directly "
            "into the PhD (a master's is earned en route) to study media, politics, "
            "health, journalism, networks and digital culture with both qualitative and "
            "quantitative methods."
        ),
    },
]

for _ep in PROGRAMS:
    _ep.setdefault("delivery_format", "in_person")

_EXPLICIT_DEPARTMENTS: dict[str, str] = {
    "penn-wharton-mba": "The Wharton School",
    "penn-wharton-economics-bs": "The Wharton School",
    "penn-computer-science-bse": "Department of Computer and Information Science",
    "penn-bioengineering-bse": "Department of Bioengineering",
    "penn-mechanical-engineering-bse": (
        "Department of Mechanical Engineering and Applied Mechanics"
    ),
    "penn-nursing-bsn": "School of Nursing",
    "penn-economics-ba": "Department of Economics",
    "penn-biology-ba": "Department of Biology",
    "penn-philosophy-ba": "Department of Philosophy",
    "penn-political-science-ba": "Department of Political Science",
    "penn-ppe-ba": "Program in Philosophy, Politics and Economics",
    "penn-mathematics-ba": "Department of Mathematics",
    "penn-psychology-ba": "Department of Psychology",
    "penn-english-ba": "Department of English",
    "penn-chemistry-ba": "Department of Chemistry",
    "penn-physics-ba": "Department of Physics and Astronomy",
    "penn-md": "Perelman School of Medicine",
    "penn-jd": "University of Pennsylvania Carey Law School",
    "penn-dmd": "School of Dental Medicine",
    "penn-vmd": "School of Veterinary Medicine",
    "penn-march": "Department of Architecture",
    "penn-msw": "School of Social Policy and Practice",
    "penn-gse-higher-education-msed": "Graduate School of Education",
    "penn-communication-phd": "Annenberg School for Communication",
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


# ── De-fabricate the Scorecard rollup catalog (anti-stub miss #2) ──────────────
# College Scorecard rows carry the federal CIP-TAXONOMY title as the field, not Penn's
# real degree name. Each rollup is resolved to Penn's REAL published degree name
# (verified against catalog.upenn.edu) or DROPPED when the CIP is a federal
# "Other"/"General" aggregation bucket with no single named Penn degree.
_ROLLUP_RESOLVE: dict[str, str] = {
    "Biology, General": "Biology",
    "Biomedical/Medical Engineering": "Bioengineering",
    "Cell/Cellular Biology and Anatomical Sciences": "Cell Biology",
    "City/Urban, Community, and Regional Planning": "City Planning",
    "Classics and Classical Languages, Literatures, and Linguistics": "Classics",
    "Drama/Theatre Arts and Stagecraft": "Theatre Arts",
    "East Asian Languages, Literatures, and Linguistics": "East Asian Languages and Civilizations",
    "Educational/Instructional Media Design": "Learning Sciences and Technologies",
    "Engineering-Related Fields": "Engineering Science",
    "English Language and Literature, General": "English",
    "Film/Video and Photographic Arts": "Cinema Studies",
    "Geological and Earth Sciences/Geosciences": "Earth and Environmental Science",
    "Germanic Languages, Literatures, and Linguistics": "German",
    "International/Globalization Studies": "International Relations",
    "Middle/Near Eastern and Semitic Languages, Literatures, and Linguistics": (
        "Near Eastern Languages and Civilizations"
    ),
    "Psychology, General": "Psychology",
    "Religion/Religious Studies": "Religious Studies",
    "Romance Languages, Literatures, and Linguistics": "Romance Languages",
    "Slavic, Baltic and Albanian Languages, Literatures, and Linguistics": (
        "Slavic Languages and Literatures"
    ),
    "Urban Studies/Affairs": "Urban Studies",
    "Visual and Performing Arts, General": "Fine Arts",
}

# Federal "Other"/"General" buckets and CIP-coded mint rows — dropped rather than
# shipped under the rollup title (de-fabrication legitimately shrinks the catalog).
_ROLLUP_DROP: frozenset[str] = frozenset({
    "Area Studies",
    "Business (CIP 52.11)",
    "Business/Commerce, General",
    "Business Administration, Management and Operations",
    "Computer and Information Sciences, General",
    "Computer Software and Media Applications",
    "Education, General",
    "Education, Other",
    "Education (CIP 13.06)",
    "Education (CIP 13.09)",
    "Education (CIP 13.14)",
    "Engineering Technologies (CIP 15.16)",
    "Engineering, Other",
    "English Language and Literature (CIP 23.14)",
    "Ethnic, Cultural Minority, Gender, and Group Studies",
    "Health Professions (CIP 51.04)",
    "Health Professions (CIP 51.05)",
    "Health Professions (CIP 51.11)",
    "Health Professions (CIP 51.12)",
    "Health Professions (CIP 51.14)",
    "Health Professions (CIP 51.15)",
    "Health Professions (CIP 51.27)",
    "Health Professions (CIP 51.32)",
    "Health Professions and Related Clinical Sciences, Other",
    "Liberal Arts and Sciences, General Studies and Humanities",
    "Linguistic, Comparative, and Related Language Studies and Services",
    "Mathematics and Statistics (CIP 27.99)",
    "Multi/Interdisciplinary Studies (CIP 30.30)",
    "Multi/Interdisciplinary Studies (CIP 30.34)",
    "Psychology (CIP 42.99)",
    "Rhetoric and Composition/Writing Studies",
    "Social Sciences (CIP 45.04)",
    "Social Sciences, Other",
    "Teacher Education and Professional Development, Specific Levels and Methods",
    "Teacher Education and Professional Development, Specific Subject Areas",
})


def _resolve_rollup(field_name: str, degree_type: str) -> str | None:
    """Real Penn degree name for a Scorecard field, or None to drop the row."""
    if field_name in _ROLLUP_DROP:
        return None
    if "(CIP " in field_name:
        return None
    return _ROLLUP_RESOLVE.get(field_name, field_name)


def _field_from_program_name(program_name: str) -> str | None:
    """Extract CIP field title from a disambiguated program name."""
    for prefix in (
        "Bachelor's in ",
        "Master's in ",
        "Doctor of Philosophy in ",
        "Graduate Certificate in ",
        "Professional program in ",
    ):
        if program_name.startswith(prefix):
            return program_name[len(prefix):]
    return None


def _field_clause(field_key: str) -> str:
    """Return the verified field-specific fact clause for a catalog field."""
    clause = FIELD_DESCRIPTIONS.get(field_key)
    if not clause:
        raise ValueError(f"Missing FIELD_DESCRIPTIONS entry for {field_key!r}")
    return clause.strip().rstrip(".")


def _penn_description(spec: dict, field: str | None = None) -> str:
    """Field-specific, credential-appropriate description — never a classification stub."""
    slug = spec["slug"]
    fmt = spec.get("delivery_format", "on_campus")
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
    fact = _field_clause(field_key)
    dtype = spec.get("degree_type", "bachelors")
    if dtype == "bachelors":
        body = fact if not fact.startswith("Graduate ") else "Undergraduate " + fact[9:]
        if not body.endswith("."):
            body += "."
    elif dtype == "masters":
        body = (
            f"Master's students in {field_key.lower()} complete graduate seminars, "
            f"research methods, and a thesis project — {fact[0].lower()}{fact[1:]}."
        )
    elif dtype == "phd":
        body = (
            f"Ph.D. training in {field_key.lower()} centers on original dissertation "
            f"research, teaching, and faculty mentorship — "
            f"{fact[0].lower()}{fact[1:]}."
        )
    elif dtype == "professional":
        body = (
            f"Penn's professional {field_key.lower()} program prepares practitioners "
            f"through advanced coursework and field experience — "
            f"{fact[0].lower()}{fact[1:]}."
        )
    elif dtype == "certificate":
        body = (
            f"Penn's graduate certificate in {field_key.lower()} offers focused "
            f"graduate coursework — {fact[0].lower()}{fact[1:]}."
        )
    else:
        body = fact if fact.endswith(".") else fact + "."
    return f"{body}{delivery}"


def _normalize_program(spec: dict, field_name: str | None = None) -> None:
    """Stamp a field-specific description on every program node."""
    spec["description"] = _penn_description(spec, field=field_name)


def _build_catalog() -> list[dict]:
    """Append breadth-first program nodes from the College Scorecard Field-of-Study list."""
    out: list[dict] = []
    seen = set(_EXISTING_SLUGS)
    for slug, school, field_name, dtype, cip, dur, fmt, _legacy_desc in _IPEDS_CATALOG:
        if slug in seen:
            continue
        if (cip, dtype) in _EXISTING_CIP_KEYS:
            continue
        real_name = _resolve_rollup(field_name, dtype)
        if real_name is None:
            continue
        seen.add(slug)
        delivery = _delivery_format(fmt)
        pname = disambiguate_program_name(real_name, dtype)
        spec = {
            "slug": slug,
            "school": school,
            "program_name": pname,
            "degree_type": dtype,
            # department = the real owning Penn school (never the field echoed from the name).
            "department": school,
            "cip": cip,
            "duration_months": dur,
            "delivery_format": delivery,
            # Keep the ORIGINAL Scorecard field so the description clause still resolves.
            "_field_name": field_name,
        }
        _normalize_program(spec, field_name)
        out.append(spec)
    return out


PROGRAMS += _build_catalog()
for _p in PROGRAMS:
    _normalize_program(_p)
_catalog_errors = validate_catalog(PROGRAMS)
_name_prefix_desc = sum(
    1
    for p in PROGRAMS
    if (p.get("description") or "").startswith(p.get("program_name", ""))
)
if _name_prefix_desc:
    _catalog_errors.append(
        f"name-prefixed descriptions on {_name_prefix_desc} programs"
    )
if _catalog_errors:
    raise RuntimeError(f"Penn catalog quality gate failed: {_catalog_errors}")
for _p in PROGRAMS:
    _p["delivery_format"] = _delivery_format(_p.get("delivery_format", "in_person"))

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

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
    "penn-dmd": "https://www.dental.upenn.edu/admissions-academics/dmd-program/",
    "penn-vmd": "https://www.vet.upenn.edu/programs/vmd-program/",
    "penn-march": (
        "https://www.design.upenn.edu/architecture/master-architecture-professional-degree"
    ),
    "penn-msw": "https://sp2.upenn.edu/program/master-of-social-work/",
    "penn-gse-higher-education-msed": "https://www.gse.upenn.edu/academics/higher-education-msed",
    "penn-communication-phd": "https://www.asc.upenn.edu/graduate/doctorate-communication",
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
    "penn-dmd": (
        "Students committed to dentistry who want a four-year DMD at one of the nation's "
        "oldest university-affiliated dental schools, with early and extensive clinical "
        "training inside a major research university."
    ),
    "penn-vmd": (
        "Students pursuing veterinary medicine who want a four-year professional doctorate "
        "at a private, research-intensive school uniquely developed alongside a medical "
        "school, with broad dual-degree pathways."
    ),
    "penn-march": (
        "Designers seeking a NAAB-accredited, STEM-designated professional architecture "
        "degree — including applicants from non-architecture backgrounds, who enter a "
        "three-and-a-half-year track."
    ),
    "penn-msw": (
        "Aspiring and current social workers seeking a CSWE-accredited clinical and macro "
        "practice master's, with full-time, part-time and BSW-holder Advanced Standing "
        "pathways."
    ),
    "penn-gse-higher-education-msed": (
        "Individuals seeking leadership roles in colleges, universities, nonprofits and "
        "education-related government agencies through a focused one-year master's."
    ),
    "penn-communication-phd": (
        "Aspiring communication scholars pursuing a research and academic career, admitted "
        "directly into a fully funded five-year PhD with no terminal research master's."
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
    "penn-dmd": [
        "Founded 1878",
        "Among the oldest university-affiliated dental schools",
        "Care Center for Persons with Disabilities",
    ],
    "penn-vmd": [
        "Awards the distinctive VMD degree",
        "95% NAVLE pass rate (Class of 2025)",
        "Founded 1884",
    ],
    "penn-march": [
        "NAAB-accredited professional degree",
        "STEM-designated",
        "GRE-free admission",
    ],
    "penn-msw": [
        "CSWE-accredited",
        "Full-time, part-time & Advanced Standing tracks",
        ">90% of students receive aid",
    ],
    "penn-gse-higher-education-msed": [
        "One-year, 10-course-unit master's",
        "Higher-ed administration & leadership",
        "Penn GSE",
    ],
    "penn-communication-phd": [
        "Fully funded for five years",
        "Founded 1958 by Walter Annenberg",
        "Leading communication research program",
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
    # Penn Dental Medicine DMD — official Penn SRFS DMD-PASS cost-of-attendance budget,
    # 2026-27 (Year 1, 11 months). Tuition $97,848; total first-year COA $162,342.
    "penn-dmd": {
        "tuition_usd": 97848,
        "total_cost_of_attendance": 162342,
        "breakdown": {
            "tuition": 97848,
            "general_fee": 4268,
            "technology_fee": 1316,
            "clinical_fee": 770,
            "dental_clinical_fee": 1050,
            "instrument_management_service_fee": 15258,
            "housing": 20130,
            "food": 7316,
            "books_supplies": 4958,
            "personal_expenses": 3090,
            "transportation": 1320,
            "health_insurance": 5018,
            "total_cost_of_attendance": 162342,
        },
        "funded": False,
        "note": (
            "Official Penn SRFS DMD (Personalized Care) cost-of-attendance budget for "
            "2026-27 (Year 1, 11 months): tuition $97,848 and a total first-year cost of "
            "attendance of $162,342 including fees, living expenses and health insurance. "
            "Published subsequent-year totals are $151,718 (Year 2), $160,904 (Year 3) and "
            "$161,684 (Year 4). Penn Dental awards need- and merit-based aid that reduces "
            "the net cost for many students."
        ),
        "source": (
            "Penn Student Registration & Financial Services — DMD Cost of Attendance, 2026-27"
        ),
        "source_url": (
            "https://srfs.upenn.edu/costs-budgeting/graduate-cost-attendance/"
            "school-dental-medicine/dmd-pass"
        ),
        "year": "2026-27",
    },
    # Penn Vet VMD — official Penn SRFS cost-of-attendance budget, 2026-27 (Year 1, 9
    # months), out-of-state. Tuition $68,712; total first-year COA $106,764. PA residents
    # pay lower tuition ($58,710) for a Year-1 total of $96,762.
    "penn-vmd": {
        "tuition_usd": 68712,
        "total_cost_of_attendance": 106764,
        "breakdown": {
            "tuition": 68712,
            "general_fee": 4268,
            "technology_fee": 1484,
            "clinical_fee": 770,
            "housing": 12978,
            "food": 5988,
            "books_supplies": 1530,
            "computer_costs": 2050,
            "personal_expenses": 2008,
            "transportation": 1958,
            "health_insurance": 5018,
            "total_cost_of_attendance": 106764,
        },
        "funded": False,
        "note": (
            "Official Penn SRFS VMD cost-of-attendance budget for 2026-27 (Year 1, 9 "
            "months), out-of-state: tuition $68,712 and a total first-year cost of "
            "attendance of $106,764 including fees, living expenses and health insurance. "
            "Pennsylvania residents pay lower tuition ($58,710) for a first-year total of "
            "$96,762. Penn Vet awards need- and merit-based aid."
        ),
        "source": (
            "Penn Student Registration & Financial Services — VMD Cost of Attendance "
            "(Out-of-State), 2026-27"
        ),
        "source_url": "https://srfs.upenn.edu/vmd-out-state-residents",
        "year": "2026-27",
    },
    # Stuart Weitzman School of Design (M.Arch) — official Penn SRFS graduate cost of
    # attendance, 2025-26. Billable tuition + fees $68,158 (tuition $63,308); estimated
    # living up to $29,216. SRFS publishes a school-wide graduate budget (not M.Arch-only).
    "penn-march": {
        "tuition_usd": 63308,
        "total_cost_of_attendance": 97374,
        "breakdown": {
            "tuition": 63308,
            "general_fee": 4108,
            "clinical_fee": 742,
            "tuition_and_fees_subtotal": 68158,
            "housing_max": 12978,
            "food_max": 5988,
            "books_supplies_max": 2500,
            "personal_expenses": 2008,
            "transportation": 1080,
            "health_insurance": 4662,
            "estimated_living_max": 29216,
            "total_cost_of_attendance": 97374,
        },
        "funded": False,
        "note": (
            "Official Penn SRFS Stuart Weitzman School of Design graduate cost of "
            "attendance for 2025-26: billable tuition and fees $68,158 (tuition $63,308) "
            "plus estimated living expenses of $20,500-$29,216, for an estimated total of "
            "up to $97,374. The living-expense figures are the published upper-bound "
            "federal-loan budget and the budget is school-wide for Weitzman graduate "
            "programs (not M.Arch-specific); actual costs vary. Weitzman awards "
            "merit-based scholarships."
        ),
        "source": (
            "Penn Student Registration & Financial Services — Weitzman School of Design "
            "Cost of Attendance, 2025-26"
        ),
        "source_url": "https://srfs.upenn.edu/costs-budgeting/design",
        "year": "2025-26",
    },
    # Penn SP2 MSW — official SP2 tuition & fees + SRFS living budget, 2026-27 (one
    # academic year, full-time, 8 c.u.). Tuition $60,272; tuition+fees $66,054; total
    # academic-year COA $94,538 (tuition+fees + SRFS living $28,484).
    "penn-msw": {
        "tuition_usd": 60272,
        "total_cost_of_attendance": 94538,
        "breakdown": {
            "tuition": 60272,
            "general_fee": 4268,
            "technology_fee": 744,
            "clinical_fee": 770,
            "tuition_and_fees_subtotal": 66054,
            "housing": 12978,
            "food": 5988,
            "books_supplies": 1412,
            "personal_expenses": 2008,
            "transportation": 1080,
            "health_insurance": 5018,
            "total_cost_of_attendance": 94538,
        },
        "funded": False,
        "note": (
            "Official Penn SP2 tuition & fees and SRFS cost of attendance for 2026-27 "
            "(one academic year, full-time, 8 course units): tuition $60,272, tuition and "
            "fees $66,054, and a total academic-year cost of attendance of $94,538 "
            "including living expenses and health insurance. The full-time MSW is "
            "completed over two academic years; more than 90% of MSW students receive "
            "financial assistance."
        ),
        "source": "Penn SP2 Tuition & Fees and SRFS MSW Cost of Attendance, 2026-27",
        "source_url": "https://sp2.upenn.edu/tuition-and-fees/",
        "year": "2026-27",
    },
    # Penn GSE Higher Education M.S.Ed. — derived from Penn GSE's published per-course-unit
    # tuition (2026-27, $8,280/c.u.) × the program's required 10 c.u. = $82,800, plus the
    # $2,134 general fee and the SRFS GSE standard on-campus living budget ($28,484). Penn
    # does not publish a single bundled total; the components are each first-party-sourced.
    "penn-gse-higher-education-msed": {
        "tuition_usd": 82800,
        "total_cost_of_attendance": 113418,
        "breakdown": {
            "tuition_per_course_unit": 8280,
            "course_units": 10,
            "tuition": 82800,
            "general_fee": 2134,
            "tuition_and_fees_subtotal": 84934,
            "living_expenses": 28484,
            "total_cost_of_attendance": 113418,
        },
        "funded": False,
        "note": (
            "Penn GSE bills per course unit; the Higher Education M.S.Ed. requires 10 "
            "course units. At the published 2026-27 master's rate of $8,280 per course "
            "unit, program tuition is $82,800; with the $2,134 general fee and the SRFS "
            "standard on-campus living budget of $28,484, the estimated total cost of "
            "attendance is $113,418. These figures are derived from Penn GSE's published "
            "per-course-unit tuition and the SRFS budget — Penn does not publish a single "
            "bundled total. Penn GSE awards merit- and need-based aid."
        ),
        "source": "Penn GSE Tuition & Fees and SRFS GSE Cost of Attendance, 2026-27",
        "source_url": "https://www.gse.upenn.edu/admissions-and-aid/tuition-and-fees",
        "year": "2026-27",
    },
    # Annenberg PhD in Communication — fully funded. Tuition and fees are waived; admitted
    # students receive an annual stipend ($44,075 in 2025-26) for four guaranteed years
    # plus a fifth after the dissertation proposal defense, with health-premium coverage.
    "penn-communication-phd": {
        "tuition_usd": 0,
        "total_cost_of_attendance": 0,
        "breakdown": {
            "tuition": 0,
            "annual_stipend": 44075,
            "guaranteed_years": 4,
        },
        "funded": True,
        "note": (
            "The Annenberg PhD in Communication is fully funded. Admitted students — "
            "including international students — receive a waiver of tuition and fees, "
            "Penn Student Insurance Plan premium coverage, and an annual stipend of "
            "$44,075 (2025-26) for four guaranteed years of fellowship support, with a "
            "fifth year available after a successful dissertation-proposal defense. There "
            "is no out-of-pocket tuition for students in good standing."
        ),
        "source": "Annenberg School for Communication — Doctoral Program Financial Support",
        "source_url": "https://www.asc.upenn.edu/graduate/doctorate-communication/financial-support",
        "year": "2025-26",
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
    "penn-md": {
        "summary": (
            "Students and guides consistently rank Penn's Perelman School of Medicine "
            "among the nation's elite M.D. programs — it placed sixth (tied with Duke) "
            "in U.S. News' research ranking before Penn withdrew from those surveys in "
            "2024 — praising Penn Medicine's translational research, the first U.S. "
            "medical school (1765), and clinical training across Penn's health system; "
            "common cautions are extreme selectivity, a demanding pre-clinical pace, "
            "and a first-year cost of attendance above $117,000."
        ),
        "themes": [
            {
                "label": "Research & Penn Medicine",
                "sentiment": "positive",
                "detail": (
                    "A top-tier research medical school integrated with Penn Medicine "
                    "hospitals and Abramson Cancer Center."
                ),
            },
            {
                "label": "Historical prestige",
                "sentiment": "positive",
                "detail": (
                    "The nation's first medical school, with a long record of "
                    "physician-scientist training."
                ),
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": (
                    "Among the most competitive M.D. programs; admissions emphasize "
                    "academic excellence and service."
                ),
            },
            {
                "label": "Cost of attendance",
                "sentiment": "caution",
                "detail": (
                    "Official 2026-27 first-year budget exceeds $117,000 including "
                    "living expenses."
                ),
            },
            {
                "label": "Ranking participation",
                "sentiment": "mixed",
                "detail": (
                    "Penn no longer submits data to U.S. News medical-school rankings "
                    "over methodology concerns."
                ),
            },
        ],
        "sources": [
            {
                "label": "Perelman School of Medicine — U.S. News withdrawal announcement",
                "url": "https://www.med.upenn.edu/evpdeancommunications/2023-01-24-314.html",
            },
            {
                "label": "The Philadelphia Inquirer — Penn med school withdraws from U.S. News",
                "url": "https://www.inquirer.com/health/medical-school-rankings-us-news-20230124.html",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "penn-jd": {
        "summary": (
            "Students and legal guides rank Penn Carey Law among the top five J.D. "
            "programs nationally — U.S. News placed it No. 4 (tied with UVA) for 2026 "
            "despite Penn's decision to stop submitting ranking data — praising strong "
            "cross-disciplinary options, corporate-law and public-interest placement, "
            "and a 98.4% two-year ultimate bar-passage rate; common cautions are "
            "Philadelphia's smaller legal market than New York, intense competition for "
            "elite firms, and a total J.D. cost of attendance near $120,000."
        ),
        "themes": [
            {
                "label": "Top-tier national rank",
                "sentiment": "positive",
                "detail": (
                    "U.S. News No. 4 among law schools for 2026 (tied with UVA), with "
                    "strong employment-outcome weighting."
                ),
            },
            {
                "label": "Bar passage & outcomes",
                "sentiment": "positive",
                "detail": (
                    "98.4% ultimate bar-passage rate (two-year average) in the 2026 "
                    "ranking data."
                ),
            },
            {
                "label": "Cross-registration",
                "sentiment": "positive",
                "detail": (
                    "J.D. students can take courses across Penn's twelve schools, "
                    "including Wharton and the medical school."
                ),
            },
            {
                "label": "Cost",
                "sentiment": "caution",
                "detail": (
                    "Official 2026-27 J.D. cost of attendance is budgeted at $120,294."
                ),
            },
            {
                "label": "Market geography",
                "sentiment": "mixed",
                "detail": (
                    "Strong national placement, but fewer on-campus interviews than "
                    "peer schools in major legal hubs."
                ),
            },
        ],
        "sources": [
            {
                "label": "The Daily Pennsylvanian — Penn Carey Law No. 4 (2026 U.S. News)",
                "url": "https://www.thedp.com/article/2026/04/penn-carey-law-us-news-report-ranking-2026",
            },
            {
                "label": "Tipping the Scales — 2026 U.S. News Law School Ranking",
                "url": (
                    "https://tippingthescales.com/rankings/"
                    "2026-u-s-news-law-school-ranking-stanford-replaces-yale-at-the-top/"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "penn-dmd": {
        "summary": (
            "Students and dental guides describe Penn Dental Medicine as one of the "
            "nation's leading D.M.D. programs — QS ranked it fourth in North America "
            "and sixteenth worldwide for dentistry in 2025 — praising early clinical "
            "exposure, oral-medicine strength, and dual-degree options within a "
            "research university; common cautions are a highly selective admissions "
            "process (roughly 6% acceptance in published guides), a demanding "
            "instrument-management fee structure, and a first-year cost of attendance "
            "above $162,000."
        ),
        "themes": [
            {
                "label": "Global QS recognition",
                "sentiment": "positive",
                "detail": (
                    "QS 2025: No. 4 among North American dental schools and No. 16 "
                    "worldwide."
                ),
            },
            {
                "label": "Clinical training",
                "sentiment": "positive",
                "detail": (
                    "A four-year D.M.D. with diverse clinical practice and professional "
                    "development coursework."
                ),
            },
            {
                "label": "Research university setting",
                "sentiment": "positive",
                "detail": (
                    "Affiliated with Penn Medicine in a major academic health center."
                ),
            },
            {
                "label": "Selectivity & cost",
                "sentiment": "caution",
                "detail": (
                    "Highly competitive admissions and among the highest published "
                    "dental-school costs of attendance."
                ),
            },
            {
                "label": "No U.S. News dental rank",
                "sentiment": "mixed",
                "detail": (
                    "U.S. News does not publish dental-school rankings after a 1990s "
                    "industry boycott."
                ),
            },
        ],
        "sources": [
            {
                "label": "Penn Dental Medicine — QS 2025 dental ranking",
                "url": (
                    "https://www.dental.upenn.edu/news-events/2025/11/06/"
                    "penn-dental-medicine-ranked-among-top-dental-schools/"
                ),
            },
            {
                "label": "Shemmassian Academic Consulting — Best Dental Schools",
                "url": "https://www.shemmassianconsulting.com/blog/best-dental-schools",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "penn-vmd": {
        "summary": (
            "Students and veterinary guides rank Penn Vet among the top U.S. veterinary "
            "schools — U.S. News peer surveys place it fifth nationally and QS ranks it "
            "ninth worldwide in veterinary science — praising Ryan Hospital and the New "
            "Bolton Center large-animal hospital, translational research with Perelman "
            "Medicine, and the only Ivy League veterinary school; common cautions are "
            "extreme selectivity, a modernized but demanding competency-based "
            "curriculum, and a first-year cost of attendance above $106,000 "
            "(out-of-state)."
        ),
        "themes": [
            {
                "label": "Teaching hospitals",
                "sentiment": "positive",
                "detail": (
                    "Ryan Veterinary Hospital (companion animals) and New Bolton Center "
                    "(large animals and equine surgery)."
                ),
            },
            {
                "label": "Translational research",
                "sentiment": "positive",
                "detail": (
                    "Co-located with Penn Medicine — unusual among U.S. vet schools — "
                    "for oncology and gene-therapy research."
                ),
            },
            {
                "label": "National reputation",
                "sentiment": "positive",
                "detail": (
                    "Top-five U.S. News veterinary-school placement in recent peer "
                    "assessment cycles."
                ),
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": (
                    "Among the most competitive V.M.D. programs; small entering classes."
                ),
            },
            {
                "label": "Cost",
                "sentiment": "caution",
                "detail": (
                    "Official 2026-27 out-of-state first-year budget totals $106,764."
                ),
            },
        ],
        "sources": [
            {
                "label": "AdmissionSight — Best Veterinary Schools in the US (2026)",
                "url": "https://admissionsight.com/best-veterinary-schools/",
            },
            {
                "label": "Penn Student Registration & Financial Services — VMD Cost of Attendance",
                "url": "https://srfs.upenn.edu/vmd-out-state-residents",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "penn-march": {
        "summary": (
            "Students and architecture guides describe Penn's Weitzman M.Arch as a "
            "small, studio-intensive program within a top research university — "
            "Black Spectacles lists it among the ten best U.S. M.Arch programs for "
            "dual-degree flexibility across Penn's twelve schools — praising the "
            "Advanced Research and Innovation Lab (robotics and digital fabrication) "
            "and Philadelphia's architectural history as a living laboratory; common "
            "cautions are a demanding studio workload, highly portfolio-driven "
            "admissions, and relatively small cohorts compared with larger urban "
            "programs."
        ),
        "themes": [
            {
                "label": "Dual-degree flexibility",
                "sentiment": "positive",
                "detail": (
                    "M.Arch students can combine architecture with business, city "
                    "planning, law, and other Penn degrees."
                ),
            },
            {
                "label": "Digital design & robotics",
                "sentiment": "positive",
                "detail": (
                    "Access to Weitzman's ARI lab for scripting, robotics, and "
                    "environmental building research."
                ),
            },
            {
                "label": "Selective admissions",
                "sentiment": "caution",
                "detail": (
                    "Portfolio and academic record weigh heavily; Ivy M.Arch programs "
                    "are highly selective."
                ),
            },
            {
                "label": "Studio intensity",
                "sentiment": "caution",
                "detail": (
                    "A rigorous, crit-driven studio sequence is the core of the degree."
                ),
            },
            {
                "label": "Small cohort",
                "sentiment": "mixed",
                "detail": (
                    "Smaller than mega-programs at Columbia or SCI-Arc, with fewer "
                    "elective breadth options."
                ),
            },
        ],
        "sources": [
            {
                "label": "Black Spectacles — Top 10 M.Arch Programs in the US",
                "url": (
                    "https://www.blackspectacles.com/blog/"
                    "top-10-masters-of-architecture-programs-in-the-us"
                ),
            },
            {
                "label": "Stuart Weitzman School of Design — Architecture",
                "url": "https://www.design.upenn.edu/architecture",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "penn-msw": {
        "summary": (
            "Students and social-work guides rank Penn's School of Social Policy & "
            "Practice (SP2) among the nation's top M.S.W. programs — U.S. News placed "
            "SP2 No. 8 among schools of social work for 2024, its highest ranking ever "
            "— praising the school's social-innovation focus, Philadelphia field "
            "placements, and interdisciplinary policy work; common cautions are the "
            "intensity of field-education requirements, limited cohort size relative to "
            "large public programs, and the cost of a private-university graduate degree."
        ),
        "themes": [
            {
                "label": "U.S. News top-10 rank",
                "sentiment": "positive",
                "detail": (
                    "No. 8 among graduate schools of social work in the 2024 U.S. News "
                    "Best Health Schools rankings."
                ),
            },
            {
                "label": "Field education",
                "sentiment": "positive",
                "detail": (
                    "Clinical and macro field placements across Philadelphia's health "
                    "and nonprofit sectors."
                ),
            },
            {
                "label": "Social innovation mission",
                "sentiment": "positive",
                "detail": (
                    "SP2 emphasizes impact, justice, and policy alongside direct "
                    "clinical practice."
                ),
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": (
                    "Field hours plus coursework demand strong time management."
                ),
            },
            {
                "label": "Private-university cost",
                "sentiment": "caution",
                "detail": (
                    "Graduate tuition at Penn exceeds most public M.S.W. programs."
                ),
            },
        ],
        "sources": [
            {
                "label": "SP2 — No. 8 U.S. News social work ranking (2024)",
                "url": (
                    "https://sp2.upenn.edu/sp2-ranked-8-among-schools-for-social-work-by-u-s-news-world-report/"
                ),
            },
            {
                "label": "U.S. News — Best Social Work Programs methodology",
                "url": "https://www.usnews.com/education/best-graduate-schools/articles/social-work-rankings-methodology",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "penn-gse-higher-education-msed": {
        "summary": (
            "Students and education guides describe Penn GSE's Higher Education M.S.Ed. "
            "as a top-tier program within a school ranked No. 3 nationally by U.S. News "
            "for 2024 — with the Higher Education specialty ranked No. 4 for the "
            "sixteenth consecutive top-10 year — praising flexible leadership "
            "preparation, access to Penn's policy and finance faculty, and strong "
            "placement into college administration and nonprofit roles; common cautions "
            "are the cost of a private graduate degree and the breadth of the "
            "ten-course curriculum requiring early specialization."
        ),
        "themes": [
            {
                "label": "Top-ranked GSE",
                "sentiment": "positive",
                "detail": (
                    "Penn GSE ranked No. 3 among graduate schools of education (2024 "
                    "U.S. News)."
                ),
            },
            {
                "label": "Higher-ed specialty strength",
                "sentiment": "positive",
                "detail": (
                    "Higher Education program ranked No. 4 — in the top 10 for 16 "
                    "straight years."
                ),
            },
            {
                "label": "Leadership preparation",
                "sentiment": "positive",
                "detail": (
                    "Prepares graduates for roles in postsecondary administration, "
                    "policy, and nonprofits."
                ),
            },
            {
                "label": "Cost",
                "sentiment": "caution",
                "detail": (
                    "Private-university graduate tuition exceeds most public "
                    "education programs."
                ),
            },
            {
                "label": "Broad curriculum",
                "sentiment": "mixed",
                "detail": (
                    "Ten course units span finance, policy, and student development — "
                    "students must focus early."
                ),
            },
        ],
        "sources": [
            {
                "label": "Penn GSE — No. 3 U.S. News ranking (2024)",
                "url": "https://www.gse.upenn.edu/news/penn-gse-ranked-no-3-us-news-world-report-2024",
            },
            {
                "label": "Penn GSE — Higher Education M.S.Ed.",
                "url": "https://www.gse.upenn.edu/academics/higher-education-msed",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "penn-communication-phd": {
        "summary": (
            "Students and communication scholars describe Penn Annenberg's Ph.D. as one "
            "of the world's leading communication doctorates — QS ranks Penn No. 10 "
            "globally in Communication & Media Studies — praising cross-disciplinary "
            "faculty, the Annenberg Public Policy Center, and a selective cohort embedded "
            "in a major research university; common cautions are the small program size, "
            "intense competition for academic jobs, and the expectation of substantial "
            "quantitative or computational methods training."
        ),
        "themes": [
            {
                "label": "Global QS recognition",
                "sentiment": "positive",
                "detail": (
                    "QS Communication & Media Studies: Penn ranked No. 10 among world "
                    "universities."
                ),
            },
            {
                "label": "Research institutes",
                "sentiment": "positive",
                "detail": (
                    "Access to Annenberg Public Policy Center and cross-school "
                    "collaboration across Penn."
                ),
            },
            {
                "label": "Selective cohort",
                "sentiment": "positive",
                "detail": (
                    "A small, research-intensive Ph.D. with visiting scholars and "
                    "practitioners."
                ),
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": (
                    "Communication Ph.D. graduates face a competitive tenure-track "
                    "market."
                ),
            },
            {
                "label": "Methods rigor",
                "sentiment": "mixed",
                "detail": (
                    "Students are expected to develop strong empirical and theoretical "
                    "toolkits."
                ),
            },
        ],
        "sources": [
            {
                "label": "National Communication Association — Penn Annenberg profile",
                "url": (
                    "https://www.natcom.org/resources-library/"
                    "university-pennsylvania-annenberg-school-communication/"
                ),
            },
            {
                "label": "Annenberg School for Communication — About",
                "url": "https://www.asc.upenn.edu/about",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "penn-computer-science-bse": {
        "summary": (
            "Students and guides describe Penn's B.S.E. in Computer Science as a rigorous "
            "CIS major within a top-25 national program — College Factual ranks Penn's "
            "CS bachelor's No. 23 nationally and Penn Engineering moved to No. 21 among "
            "undergraduate engineering programs in U.S. News (2026) — praising theory, "
            "AI/ML, and systems strength in the GRASP robotics ecosystem; common cautions "
            "are competitive grading, large introductory lectures, and fewer CS seats "
            "than at dedicated tech institutes."
        ),
        "themes": [
            {
                "label": "Research & robotics",
                "sentiment": "positive",
                "detail": (
                    "Ties to Penn Engineering's GRASP Lab and AI/ML research groups."
                ),
            },
            {
                "label": "National CS recognition",
                "sentiment": "positive",
                "detail": (
                    "College Factual ranks Penn's CS bachelor's among the top 25 "
                    "nationally."
                ),
            },
            {
                "label": "Engineering school rank",
                "sentiment": "positive",
                "detail": (
                    "Penn Engineering ranked No. 21 among undergraduate engineering "
                    "programs (U.S. News 2026)."
                ),
            },
            {
                "label": "Competitive environment",
                "sentiment": "caution",
                "detail": (
                    "Selective Penn admissions and demanding SEAS coursework."
                ),
            },
            {
                "label": "Scale vs. tech peers",
                "sentiment": "mixed",
                "detail": (
                    "Smaller CS cohort than at CMU or MIT, with fewer specialized "
                    "electives."
                ),
            },
        ],
        "sources": [
            {
                "label": "College Factual — Penn Computer Science Rankings",
                "url": (
                    "https://www.collegefactual.com/colleges/university-of-pennsylvania/"
                    "academic-life/academic-majors/computer-information-sciences/computer-science/"
                ),
            },
            {
                "label": "The Daily Pennsylvanian — Penn U.S. News 2026 (Engineering No. 21)",
                "url": "https://www.thedp.com/article/2025/09/penn-us-news-ranking-2026",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "penn-nursing-bsn": {
        "summary": (
            "Students and nursing guides rank Penn Nursing among the world's top nursing "
            "schools — Penn Nursing reclaimed QS's No. 1 global nursing ranking for 2026 "
            "and U.S. News placed Penn's undergraduate nursing program No. 2 (tied with "
            "Emory) nationally — praising clinical education at Penn Medicine, "
            "research-driven faculty, and strong health-system placement; common cautions "
            "are the intensity of clinical rotations, a competitive admissions pool, and "
            "the cost of a private-university nursing degree."
        ),
        "themes": [
            {
                "label": "World No. 1 (QS nursing)",
                "sentiment": "positive",
                "detail": (
                    "Penn Nursing ranked the world's top nursing school in QS 2026 "
                    "subject rankings."
                ),
            },
            {
                "label": "U.S. undergraduate rank",
                "sentiment": "positive",
                "detail": (
                    "U.S. News No. 2 among undergraduate nursing programs (2026, tied "
                    "with Emory)."
                ),
            },
            {
                "label": "Clinical & research integration",
                "sentiment": "positive",
                "detail": (
                    "Clinical training paired with Penn Medicine and nursing research "
                    "centers."
                ),
            },
            {
                "label": "Clinical workload",
                "sentiment": "caution",
                "detail": (
                    "Demanding rotations and simulation requirements across the B.S.N."
                ),
            },
            {
                "label": "Cost",
                "sentiment": "caution",
                "detail": (
                    "Private-university tuition; need-based aid reduces net price for "
                    "many families."
                ),
            },
        ],
        "sources": [
            {
                "label": "Penn Nursing — QS No. 1 nursing school (2026)",
                "url": (
                    "https://www.nursing.upenn.edu/live/news/3535-penn-nursing-reclaims-the-1-spot-ranked-the-worlds"
                ),
            },
            {
                "label": "The Daily Pennsylvanian — Penn U.S. News 2026 (Nursing No. 2)",
                "url": "https://www.thedp.com/article/2025/09/penn-us-news-ranking-2026",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "penn-wharton-economics-bs": {
        "summary": (
            "Students and guides describe Wharton's undergraduate B.S. in Economics as "
            "the flagship pre-professional business degree at the world's first "
            "collegiate business school — U.S. News tied Wharton with MIT Sloan for No. 1 "
            "among undergraduate business programs in 2026 — praising finance and "
            "analytics concentrations, Wall Street and consulting placement, and access "
            "to Penn's liberal-arts core; common cautions are a competitive internal "
            "culture, the pressure of recruiting cycles, and Wharton's high sticker price "
            "even after need-based aid."
        ),
        "themes": [
            {
                "label": "No. 1 undergrad business (U.S. News)",
                "sentiment": "positive",
                "detail": (
                    "Wharton tied MIT Sloan for the top undergraduate business program "
                    "in U.S. News 2026."
                ),
            },
            {
                "label": "Finance & consulting pipelines",
                "sentiment": "positive",
                "detail": (
                    "Deep recruiting into investment banking, consulting, and technology."
                ),
            },
            {
                "label": "Concentration breadth",
                "sentiment": "positive",
                "detail": (
                    "Concentrations span finance, management, statistics, and "
                    "business analytics."
                ),
            },
            {
                "label": "Recruiting pressure",
                "sentiment": "caution",
                "detail": (
                    "Early internship and full-time recruiting can feel intense from "
                    "sophomore year."
                ),
            },
            {
                "label": "Cost",
                "sentiment": "caution",
                "detail": (
                    "Wharton shares Penn's high sticker price, though need-based aid "
                    "lowers net cost for many."
                ),
            },
        ],
        "sources": [
            {
                "label": "The Daily Pennsylvanian — Wharton No. 1 undergrad business (2026)",
                "url": "https://www.thedp.com/article/2025/09/penn-us-news-ranking-2026",
            },
            {
                "label": "Niche — University of Pennsylvania",
                "url": "https://www.niche.com/colleges/university-of-pennsylvania/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "penn-ppe-ba": {
        "summary": (
            "Students and college guides describe Penn's Philosophy, Politics & Economics "
            "(PPE) major as one of the oldest and most prestigious U.S. PPE programs — "
            "CollegeVine and Penn's program site note it is among the largest majors in "
            "the College of Arts & Sciences — praising interdisciplinary policy and "
            "pre-law preparation across four thematic concentrations; common cautions are "
            "the breadth of required foundation courses, less brand recognition than a "
            "standalone economics major on Wall Street, and the need to self-direct "
            "electives toward a clear career path."
        ),
        "themes": [
            {
                "label": "Pioneer U.S. PPE program",
                "sentiment": "positive",
                "detail": (
                    "One of the oldest and best-known PPE majors in the United States."
                ),
            },
            {
                "label": "Interdisciplinary depth",
                "sentiment": "positive",
                "detail": (
                    "Combines philosophy, political science, and economics with "
                    "thematic concentrations."
                ),
            },
            {
                "label": "Pre-law & policy paths",
                "sentiment": "positive",
                "detail": (
                    "Designed for law, consulting, journalism, and public-policy careers."
                ),
            },
            {
                "label": "Breadth vs. depth",
                "sentiment": "mixed",
                "detail": (
                    "Wide foundation requirements can leave less room for deep "
                    "specialization in one field."
                ),
            },
            {
                "label": "Recruiting brand",
                "sentiment": "caution",
                "detail": (
                    "Finance recruiters may prefer Wharton or pure economics majors."
                ),
            },
        ],
        "sources": [
            {
                "label": "Penn PPE — Considering PPE?",
                "url": "https://ppe.sas.upenn.edu/study/considering-ppe",
            },
            {
                "label": "CollegeVine — Top PPE programs in the US",
                "url": "https://www.collegevine.com/faq/46551/top-ppe-programs-in-the-us",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "penn-bioengineering-bse": {
        "summary": (
            "Students and guides describe Penn's bioengineering B.S.E. as a rigorous "
            "intersection of engineering and medicine — Penn Engineering ranked No. 21 "
            "among undergraduate engineering programs in U.S. News (2026) and Penn "
            "Medicine integration supports biomaterials, imaging, and systems biology "
            "research — praising pre-med and industry flexibility; common cautions are "
            "demanding math and physics prerequisites, limited class size relative to "
            "general engineering majors, and competition for lab positions."
        ),
        "themes": [
            {
                "label": "Engineering + medicine",
                "sentiment": "positive",
                "detail": (
                    "Applies engineering to biomaterials, imaging, and synthetic biology "
                    "alongside Penn Medicine."
                ),
            },
            {
                "label": "Engineering school rank",
                "sentiment": "positive",
                "detail": (
                    "Penn Engineering No. 21 among undergraduate engineering programs "
                    "(U.S. News 2026)."
                ),
            },
            {
                "label": "Career flexibility",
                "sentiment": "positive",
                "detail": (
                    "Paths into med school, biotech, devices, and graduate research."
                ),
            },
            {
                "label": "Prerequisite rigor",
                "sentiment": "caution",
                "detail": (
                    "Heavy math, physics, and chemistry core before upper-level BE "
                    "courses."
                ),
            },
            {
                "label": "Smaller major",
                "sentiment": "mixed",
                "detail": (
                    "Fewer classmates than CIS or ME, with fewer dedicated BE electives."
                ),
            },
        ],
        "sources": [
            {
                "label": "The Daily Pennsylvanian — Penn Engineering No. 21 (U.S. News 2026)",
                "url": "https://www.thedp.com/article/2025/09/penn-us-news-ranking-2026",
            },
            {
                "label": "Penn Engineering — Bioengineering",
                "url": "https://be.seas.upenn.edu/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    **DEPTH_REVIEWS,
}

_COVERABLE_REVIEWS = frozenset(_REVIEWS_BY_SLUG.keys())

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

# Generic graduate/professional admissions pointer for catalog breadth nodes whose
# per-program requirements are not yet individually verified.
_REQ_GRAD_GENERIC = {
    "materials": [
        {
            "name": "Program-specific application materials",
            "required": True,
            "note": (
                "Requirements vary by school and degree; see the program's official "
                "admissions page on the Penn website."
            ),
        },
    ],
    "source": "University of Pennsylvania — Graduate Admissions",
    "source_url": "https://www.upenn.edu/admissions/graduate",
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


# Penn Dental Medicine DMD admission (ADEA AADSAS).
_REQ_DENTAL = {
    "materials": [
        {"name": "ADEA AADSAS application", "required": True},
        {
            "name": "DAT (Dental Admission Test) score",
            "required": True,
            "note": (
                "DAT scores from test dates of January 2024 or later are required for the "
                "2026-27 admissions cycle; the ADA and Canadian DAT are both accepted."
            ),
        },
        {
            "name": "A minimum of two letters of recommendation from professors",
            "required": True,
            "note": "A pre-health committee letter is accepted as an alternative.",
        },
        {
            "name": "A minimum of 100 hours of dental observation (≥50 in general practice)",
            "required": True,
        },
        {"name": "Penn Dental supplemental application", "required": True},
        {"name": "Official transcripts (via AADSAS)", "required": True},
        {"name": "$100 non-refundable application fee", "required": True},
    ],
    "deadlines": [
        {"round": "AADSAS application & supplemental materials", "date": "December 1"},
        {"round": "Official DAT scores", "date": "December 1"},
    ],
    "recommendations": {
        "required": 2,
        "note": (
            "A minimum of two letters from professors, or an accepted pre-health "
            "committee letter."
        ),
    },
    "application_fee": "$100 (non-refundable)",
    "international": {
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Penn Dental Medicine — DMD Admissions",
                "url": "https://www.dental.upenn.edu/admissions-academics/dmd-program/admissions/",
            }
        ],
    },
    "source": "Penn Dental Medicine — DMD Admissions",
    "source_url": "https://www.dental.upenn.edu/admissions-academics/dmd-program/admissions/",
}

# Penn Vet VMD admission (VMCAS). Penn Vet no longer accepts the GRE.
_REQ_VET = {
    "materials": [
        {"name": "VMCAS application (AAVMC)", "required": True},
        {
            "name": "Three electronic letters of recommendation (eLORs)",
            "required": True,
            "note": (
                "One from a faculty member (a science academic is highly recommended), "
                "one from a veterinarian, and one of the applicant's choice."
            ),
        },
        {"name": "VMCAS personal statement essay", "required": True},
        {"name": "Penn Vet Supplemental Information Form", "required": True},
        {"name": "Official transcripts", "required": True},
        {
            "name": "$75 Penn supplemental processing fee",
            "required": True,
            "note": "Payable to The Trustees of the University of Pennsylvania (plus VMCAS fees).",
        },
        {
            "name": "GRE",
            "required": False,
            "note": "Penn Vet no longer considers or accepts the GRE.",
        },
    ],
    "deadlines": [
        {"round": "VMCAS application", "date": "September 15"},
    ],
    "recommendations": {
        "required": 3,
        "note": (
            "Three eLORs: a faculty member (science academic recommended), a "
            "veterinarian, and one of the applicant's choice."
        ),
    },
    "application_fee": "$75 Penn supplemental fee (plus VMCAS fees)",
    "international": {
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Penn Vet — How to Apply",
                "url": "https://www.vet.upenn.edu/admissions/how-to-apply/",
            }
        ],
    },
    "source": "Penn Vet — VMD Admissions",
    "source_url": "https://www.vet.upenn.edu/admissions/how-to-apply/",
}

# Stuart Weitzman School of Design M.Arch admission. GRE not required; portfolio required.
_REQ_DESIGN = {
    "materials": [
        {"name": "Weitzman online application", "required": True},
        {
            "name": "Digital portfolio",
            "required": True,
            "note": "One PDF no larger than 30 MB, with no more than 20 pages.",
        },
        {
            "name": "Personal statement (no more than 500 words)",
            "required": True,
        },
        {"name": "Résumé", "required": True},
        {"name": "Transcripts from each college/university attended", "required": True},
        {
            "name": "Three letters of recommendation (at least two from college instructors)",
            "required": True,
        },
        {"name": "$80 non-refundable application fee", "required": True},
        {
            "name": "GRE",
            "required": False,
            "note": "GRE scores are not required of M.Arch applicants.",
        },
    ],
    "deadlines": [
        {"round": "Application deadline", "date": "January 7"},
    ],
    "recommendations": {
        "required": 3,
        "note": "Three letters of recommendation, at least two from college instructors.",
    },
    "application_fee": "$80 (non-refundable)",
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": False,
            "note": (
                "Required for non-native English speakers without four or more years of "
                "English-medium undergraduate study."
            ),
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Weitzman School of Design — How to Apply",
                "url": "https://www.design.upenn.edu/graduate-admissions/how-apply",
            }
        ],
    },
    "source": "Stuart Weitzman School of Design — Graduate Admissions",
    "source_url": "https://www.design.upenn.edu/graduate-admissions/how-apply",
}

# Penn SP2 MSW admission. GRE not required; three letters of recommendation.
_REQ_SP2 = {
    "materials": [
        {"name": "SP2 online application", "required": True},
        {"name": "Résumé", "required": True},
        {"name": "Application essay (responses to required questions)", "required": True},
        {
            "name": "Transcripts of all undergraduate and postgraduate study",
            "required": True,
        },
        {
            "name": "Three letters of recommendation",
            "required": True,
            "note": (
                "At least one work-related (internship, job, community service) and at "
                "least one academic reference."
            ),
        },
        {
            "name": "Application fee ($25 by December 1, then $65)",
            "required": True,
        },
        {
            "name": "GRE",
            "required": False,
            "note": "Applicants are not required to submit GRE scores.",
        },
    ],
    "deadlines": [
        {"round": "Priority deadline", "date": "December 1"},
        {"round": "Final deadline", "date": "February 1"},
    ],
    "recommendations": {
        "required": 3,
        "note": (
            "Three letters, including at least one work-related and at least one academic "
            "reference."
        ),
    },
    "application_fee": "$25 (by December 1) / $65 (after); non-refundable",
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "Duolingo English Test"],
            "required": False,
            "note": "TOEFL 100+, IELTS 7.5+, or Duolingo 135+ for non-native speakers.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Penn SP2 — How to Apply (MSW)",
                "url": "https://sp2.upenn.edu/how-to-apply-msw/",
            }
        ],
    },
    "source": "Penn SP2 — MSW Admissions",
    "source_url": "https://sp2.upenn.edu/how-to-apply-msw/",
}

# Penn GSE Higher Education M.S.Ed. admission. Program-specific deadline dates are served
# only via a dynamic dropdown on the official page and could not be verified verbatim, so
# the deadlines field is recorded in this program's _standard.omitted rather than guessed.
_REQ_GSE = {
    "materials": [
        {"name": "Penn GSE online application", "required": True},
        {
            "name": "Statement of purpose (750 words or fewer)",
            "required": True,
        },
        {
            "name": "Three references / letters of recommendation",
            "required": True,
            "note": (
                "If you received a degree within the last five years, include at least "
                "one academic reference."
            ),
        },
        {"name": "Transcripts of prior study", "required": True},
        {
            "name": "$75 application fee (waived for applications submitted Sept 1–Mar 1)",
            "required": True,
        },
    ],
    "deadlines": [],
    "recommendations": {
        "required": 3,
        "note": (
            "Three references; at least one academic reference if a degree was received "
            "within the last five years."
        ),
    },
    "application_fee": "$75 (automatically waived for applications submitted Sept 1–Mar 1)",
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": False,
            "note": "Required supplemental materials for applicants with international coursework.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Penn GSE — How to Apply",
                "url": "https://www.gse.upenn.edu/admissions-and-aid/how-to-apply",
            }
        ],
    },
    "source": "Penn GSE — How to Apply",
    "source_url": "https://www.gse.upenn.edu/admissions-and-aid/how-to-apply",
}

# Annenberg PhD in Communication admission. GRE optional.
_REQ_ANNENBERG = {
    "materials": [
        {"name": "Annenberg online application", "required": True},
        {
            "name": "Statement of purpose (must not exceed 1,000 words)",
            "required": True,
            "note": "Should discuss your potential research area or topic.",
        },
        {"name": "CV or résumé", "required": True},
        {"name": "Transcripts", "required": True},
        {
            "name": "Writing sample (optional, no more than 10 pages double-spaced)",
            "required": False,
        },
        {
            "name": "Up to three letters of recommendation",
            "required": True,
            "note": "From individuals familiar with your academic abilities.",
        },
        {"name": "$90 application fee", "required": True},
        {
            "name": "GRE",
            "required": False,
            "note": "The GRE is optional.",
        },
    ],
    "deadlines": [
        {"round": "Application, statement, CV, transcripts & fee", "date": "December 1"},
        {"round": "Letters of recommendation", "date": "December 15"},
    ],
    "recommendations": {
        "required": 3,
        "note": (
            "Submit no more than three letters from individuals familiar with your "
            "academic abilities."
        ),
    },
    "application_fee": (
        "$90 (waivers for U.S. citizens / permanent residents with financial hardship)"
    ),
    "international": {
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Annenberg School — Apply to the PhD Program",
                "url": "https://www.asc.upenn.edu/graduate/doctorate-communication/apply-phd-program",
            }
        ],
    },
    "source": "Annenberg School for Communication — PhD Admissions",
    "source_url": "https://www.asc.upenn.edu/graduate/doctorate-communication/apply-phd-program",
}


def _requirements_for(spec: dict) -> dict:
    """Pick the admissions requirement set for a program by slug / degree type."""
    by_slug = {
        "penn-wharton-mba": _REQ_MBA,
        "penn-md": _REQ_MD,
        "penn-jd": _REQ_LAW,
        "penn-dmd": _REQ_DENTAL,
        "penn-vmd": _REQ_VET,
        "penn-march": _REQ_DESIGN,
        "penn-msw": _REQ_SP2,
        "penn-gse-higher-education-msed": _REQ_GSE,
        "penn-communication-phd": _REQ_ANNENBERG,
    }
    req = by_slug.get(spec["slug"])
    if req is not None:
        return dict(req)
    if spec["degree_type"] == "bachelors":
        return dict(_REQ_UNDERGRAD)
    return dict(_REQ_GRAD_GENERIC)


# Slug-specific persisted application deadline (next upcoming cycle), where a program's
# real deadline differs from the default January 5. Each date matches the admissions set's
# verified first-party deadline; the Penn GSE M.S.Ed. deadline could not be verified from a
# static first-party page (served only via a dynamic dropdown), so it persists None — the
# field is recorded in that program's _standard.omitted rather than carrying a wrong date.
_DEADLINE_BY_SLUG: dict[str, date | None] = {
    "penn-dmd": date(2026, 12, 1),  # AADSAS application & supplemental materials due Dec 1
    "penn-vmd": date(2026, 9, 15),  # VMCAS application deadline (Fall 2027 entry)
    "penn-march": date(2027, 1, 7),  # Weitzman M.Arch application deadline January 7
    "penn-msw": date(2027, 2, 1),  # SP2 MSW final application deadline February 1
    "penn-gse-higher-education-msed": None,  # deadline unverifiable — omitted
    "penn-communication-phd": date(2026, 12, 1),  # Annenberg PhD application deadline Dec 1
}


# Real Penn campus photo (College Hall) — Wikimedia Commons, hotlinkable landscape JPG
# (canonical thumbnail URL verified via the Commons API). Leads the institution hero.
_CAMPUS_PHOTO = SCHOOL_OUTCOMES["campus_photos"][0]["url"]


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


def _program_standard(slug: str, spec: dict | None = None) -> dict:
    """Per-program omitted-field list (verified-unavailable), for _standard."""
    if spec is None:
        spec = _SPEC_BY_SLUG[slug]
    omitted: list[str] = []
    if slug != _FLAGSHIP:
        omitted += [
            "outcomes_data.employment_rate",
            "outcomes_data.top_industries",
        ]
    if spec["degree_type"] != "bachelors" and slug not in _COST_BY_SLUG:
        omitted.append("cost_data.tuition_usd")
    if slug not in _TRACKS_BY_SLUG:
        omitted.append("tracks")
    if slug not in _CLASS_PROFILE_BY_SLUG:
        omitted.append("class_profile.cohort_size")
    if slug not in _FACULTY_BY_SLUG:
        omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    explicit_req_slugs = {
        "penn-wharton-mba", "penn-md", "penn-jd", "penn-dmd", "penn-vmd",
        "penn-march", "penn-msw", "penn-gse-higher-education-msed", "penn-communication-phd",
    }
    if slug not in explicit_req_slugs and spec["degree_type"] != "bachelors":
        omitted.append("application_requirements.deadlines")
    if slug == "penn-gse-higher-education-msed":
        omitted.append("application_requirements.deadlines")
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
        p.department = spec.get("department")
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = _delivery_format(spec.get("delivery_format", "in_person"))
        if slug == _FLAGSHIP:
            p.content_sources = _WHARTON_MBA_CONTENT
        else:
            p.content_sources = _program_content(spec)
        # Cost: Wharton MBA carries its own budget; undergraduate uses published rates.
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
                    "Published undergraduate cost of attendance and average net price. "
                    "Penn is need-blind for domestic applicants and meets 100% of "
                    "demonstrated need with grant-based aid, so most families pay far "
                    "less than the sticker price (average net price ≈ $28,700)."
                ),
                "source": "U.S. Dept. of Education College Scorecard (UNITID 215062)",
                "source_url": "https://collegescorecard.ed.gov/school/?215062",
                "year": "2024-25",
            }
        else:
            p.tuition = None
            p.cost_data = {
                "funded": spec["degree_type"] == "phd",
                "note": (
                    "Penn does not publish a single citable per-program tuition for this "
                    "catalog node; see the program's official admissions/tuition page."
                ),
                "source": "University of Pennsylvania — Graduate Admissions",
                "source_url": "https://www.upenn.edu/admissions/graduate",
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
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_BASELINE
        p.highlights = _HL_BY_SLUG.get(slug) or _HL_BASELINE
        # Always assign so a stale value on a pre-existing row is cleared (tracks is
        # recorded as omitted where unverified, and match_service reads program.tracks).
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        # Application deadline — the single persisted date that catalog / search /
        # reminder flows read. Slug-specific where a program's real deadline differs from
        # the default January 5 (undergraduate Regular Decision / Wharton MBA Round 2);
        # programs whose deadline could not be verified persist None rather than a wrong
        # date. ``_DEADLINE_BY_SLUG`` maps a slug to its real next-cycle deadline (or None).
        p.application_deadline = (
            _DEADLINE_BY_SLUG[slug] if slug in _DEADLINE_BY_SLUG else date(2027, 1, 5)
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
