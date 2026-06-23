"""Duke University — gold-standard profile data (institution + schools + program catalog).

Mirrors the MIT / Sloan / MBAn reference instance (see ``mit_profile.py`` /
``yale_profile.py``): every value is researched from an authoritative source and carries
a citation, or is honestly omitted (recorded in that node's ``_standard.omitted``) — never
guessed. Built 2026-06-11 from:

  • U.S. Dept. of Education **College Scorecard** + **NCES College Navigator** (IPEDS,
    UNITID 198419) — admit rate, net price, earnings, completion/retention, Pell/loan,
    test scores, demographics, locale.
  • **Duke Facts** (facts.duke.edu) and the **Common Data Set 2024-25** — enrollment,
    faculty, endowment, race/ethnicity.
  • **Duke Today** (Class of 2029 admissions release), the **Duke Career Hub** first-
    destination outcomes (Class of 2022), Duke **Giving / DUMAC** (endowment), and the
    Carnegie Classifications, **QS 2026**, **THE 2026**, and **U.S. News 2026** ranking
    pages.
  • Each school's official site + bulletin (deans, founding, research centers) and each
    program's official catalog/tuition page (degree, format, tuition).

Honest caveats stamped into ``_standard.omitted``: Duke is test-optional for the 2026-27
cycle; Duke publishes career outcomes college-wide (no per-program employment/industry
split), so those program fields are omitted; graduate/professional programs without a
verified per-program tuition carry a sourced "see the school's tuition page" record rather
than a guessed number; and notable-faculty rosters are omitted for schools where no
current named-prize holder could be verified from an official page.

Depth pass (2026-06-15, dukeprof4): merged ``DEPTH_REVIEWS`` for 42 coverable
programs (49/49 total external_reviews on coverable programs).

Structural repair (2026-06-16, dukeprof5): replaced classification-only program
descriptions with field-specific clauses from ``duke_field_descriptions.py``.

Graduate-tier tuition (2026-06-23, dukegradtuition1): stamps published 2025-26
professional rates from each school's official tuition page — M.D. $72,297,
JD/LLM dual $93,450, DPT $42,000, OTD $43,000, DNP $32,880 (avg semester × 2),
CRNA DNP $70,460 — never the $70,265 undergraduate sticker. PhD rows remain
funded-omit-with-reason.
"""

from __future__ import annotations

import re
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.duke_field_descriptions import (
    FIELD_ALIASES,
    FIELD_DESCRIPTIONS,
    SLUG_DESCRIPTIONS,
)
from unipaith.data.duke_reviews_depth import DEPTH_REVIEWS
from unipaith.data.profile_catalog_utils import (
    disambiguate_program_name,
    validate_catalog,
)
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Duke University"

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
_OMITTED_INSTITUTION: list[str] = [
    # Duke does not publish a single canonical Nobel/MacArthur headline count on an
    # official page (aggregate counts vary by method), so the recognition figures are
    # omitted rather than asserting a number Duke itself does not state.
    "school_outcomes.flagship.nobel_laureates",
]

# ── Institution-level data ────────────────────────────────────────────────
# Rankings are stored as {rank, year} objects; the page renders any ranking_data entry
# that is an object with a numeric `rank`. Each rank is quoted from the official ranking
# body for the 2026 edition and cross-checked across two independent sources.
RANKING_DATA: dict = {
    "ownership_type": "private",
    # Southern Association of Colleges and Schools Commission on Colleges.
    "accreditor": "SACSCOC",
    # Carnegie 2025 basic classification (R1).
    "carnegie_classification": "Doctoral Universities: Very High Research Activity (R1)",
    # QS World University Rankings 2026: Duke is #62 worldwide.
    "qs_world_university_rankings": {"rank": 62, "year": 2026},
    # THE World University Rankings 2026: #28 in the world.
    "times_higher_education": {"rank": 28, "year": 2026},
    # U.S. News Best Colleges (National Universities) 2026: #7 nationally.
    "us_news_national": {"rank": 7, "year": 2026},
}

# school_outcomes is shallow-merged into the existing JSONB (the College Scorecard seed
# already wrote admit_rate / net price / earnings / completion / test_scores / location);
# each sub-object below is complete, so a shallow merge is correct.
SCHOOL_OUTCOMES: dict = {
    # Duke Today, Class of 2029: 2,818 admits / 58,698 first-year applicants = 4.8%.
    "admit_rate": 0.048,
    # College Scorecard average annual net price.
    "avg_net_price": 29612,
    # College Scorecard institution-wide median earnings 10 years after entry.
    "median_earnings_10yr": 97800,
    # College Scorecard four-year completion rate (150% of normal time).
    "completion_rate_4yr_150pct": 0.9678,
    # NCES College Navigator (IPEDS): first-year retention = 98%.
    "retention_rate_first_year": 0.98,
    # NCES College Navigator (IPEDS): six-year graduation rate = 96% (Duke's Provost
    # reports a 94-96% band over the past decade; the most recent IPEDS figure is ~96-97%).
    "graduation_rate_6yr": 0.96,
    "financial_aid": {
        # NCES College Navigator (IPEDS, 2024-25): 17% of full-time beginning
        # undergraduates received a Pell grant; 14% took federal student loans.
        "pell_grant_rate": 0.17,
        "federal_loan_rate": 0.14,
        # Duke Board of Trustees 2025-26 undergraduate cost of attendance (billed).
        "cost_of_attendance": 92042,
        # College Scorecard median federal debt of completers.
        "median_debt_completers": 13000,
    },
    # Undergraduate race/ethnicity (Duke Common Data Set 2024-25, all undergraduates;
    # cross-checked vs NCES College Navigator / IPEDS Fall 2024).
    "demographics": {
        "white": 0.35,
        "asian": 0.22,
        "hispanic": 0.11,
        "black": 0.09,
        "two_or_more": 0.07,
        "international": 0.11,
        "unknown": 0.06,
    },
    # SAT/ACT 25th-75th percentiles of enrolled first-years (IPEDS via College Scorecard;
    # written by the federal seed). Duke is test-optional for the 2026-27 cycle.
    "test_scores": {
        "sat_reading_25_75": [730, 770],
        "sat_math_25_75": [760, 800],
        "act_25_75": [34, 35],
    },
    # Duke main campus, Durham, North Carolina.
    "location": {"lat": 36.00139, "lng": -78.93833},
    "campus_basics": {"location": "Durham, North Carolina"},
    "scale": {
        # Duke Facts (Fall 2024): 4,236 faculty members (1,655 tenured/tenure-track).
        "faculty_count": 4236,
        # U.S. News / Duke: 6:1 student-faculty ratio.
        "student_faculty_ratio": "6:1",
        # Duke Giving / DUMAC: endowment $12.3 billion at fiscal year-end June 30, 2025.
        "endowment_usd": 12300000000,
    },
    # Duke Career Hub first-destination survey, Class of 2022 (84% knowledge rate): 90%
    # of respondents employed or continuing their education.
    "employed_or_continuing_ed": 0.90,
    # Duke Career Hub Class of 2022 — employment by industry, in rank order.
    "top_employer_industries": [
        "Technology / IT",
        "Finance",
        "Business & Management Consulting",
        "Healthcare & Medicine",
        "Science & Research",
    ],
    "research": {
        "labs": [
            "Duke Institute for Brain Sciences",
            "Duke Global Health Institute",
            "Kenan Institute for Ethics",
            "Robert J. Margolis, MD, Institute for Health Policy",
            "Nicholas Institute for Energy, Environment & Sustainability",
            "Social Science Research Institute",
            "Rhodes Information Initiative at Duke (Rhodes iiD)",
            "Duke Initiative for Science & Society",
            "John Hope Franklin Humanities Institute",
            "Duke Innovation & Entrepreneurship",
            "Duke Clinical Research Institute (DCRI)",
        ],
        "areas": [
            "Biomedical & health sciences",
            "Neuroscience & brain sciences",
            "Global & population health",
            "Environment, energy & sustainability",
            "Data science & information initiatives",
            "Public policy & ethics",
            "Engineering & the physical sciences",
            "Humanities & the arts",
        ],
        "lab_links": {
            "Duke Institute for Brain Sciences": "https://dibs.duke.edu/",
            "Duke Global Health Institute": "https://globalhealth.duke.edu/",
            "Kenan Institute for Ethics": "https://kenan.ethics.duke.edu/",
            "Robert J. Margolis, MD, Institute for Health Policy": (
                "https://healthpolicy.duke.edu/"
            ),
            "Nicholas Institute for Energy, Environment & Sustainability": (
                "https://nicholasinstitute.duke.edu/"
            ),
            "Social Science Research Institute": "https://ssri.duke.edu/",
            "Rhodes Information Initiative at Duke (Rhodes iiD)": "https://bigdata.duke.edu/",
            "Duke Initiative for Science & Society": "https://scienceandsociety.duke.edu/",
            "John Hope Franklin Humanities Institute": "https://fhi.duke.edu/",
            "Duke Innovation & Entrepreneurship": "https://entrepreneurship.duke.edu/",
            "Duke Clinical Research Institute (DCRI)": "https://dcri.org/",
        },
    },
    "campus_life": {
        # Duke's teams (the Blue Devils) compete in NCAA Division I (Atlantic Coast).
        "athletics_division": "NCAA Division I (Atlantic Coast Conference)",
        "mascot": "Duke Blue Devils",
        "housing": "Residential campus (East Campus first-year, West & Central upperclass)",
        "resources": [
            {"label": "Duke Blue Devils Athletics", "url": "https://goduke.com/"},
            {"label": "Duke University Libraries", "url": "https://library.duke.edu/"},
            {"label": "Duke Student Affairs", "url": "https://students.duke.edu/"},
            {"label": "Duke Career Hub", "url": "https://careerhub.students.duke.edu/"},
            {
                "label": "Duke Recreation & Physical Education",
                "url": "https://recreation.duke.edu/",
            },
            {"label": "Nasher Museum of Art", "url": "https://nasher.duke.edu/"},
            {"label": "DukeEngage", "url": "https://dukeengage.duke.edu/"},
            {"label": "Duke Arts", "url": "https://arts.duke.edu/"},
        ],
    },
    # Wikimedia Commons file page verified 2026-06-14: author Sdkb, CC BY-SA 4.0.
    "media_credit": "Wikimedia Commons / Sdkb (CC BY-SA 4.0)",
    "campus_photos": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/"
                "Duke_University_Chapel_side_in_July_2025.jpg/"
                "1920px-Duke_University_Chapel_side_in_July_2025.jpg"
            ),
            "credit": "Wikimedia Commons / Sdkb (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/"
                "West_Campus_path_at_Duke_University_in_July_2025.jpg/"
                "1920px-West_Campus_path_at_Duke_University_in_July_2025.jpg"
            ),
            "credit": "Wikimedia Commons / Sdkb (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/"
                "Davidson_Building%2C_Duke_University_in_July_2025.jpg/"
                "1920px-Davidson_Building%2C_Duke_University_in_July_2025.jpg"
            ),
            "credit": "Wikimedia Commons / Sdkb (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/"
                "Sarah_P._Duke_Gardens_gate.jpg/"
                "1920px-Sarah_P._Duke_Gardens_gate.jpg"
            ),
            "credit": "Wikimedia Commons / Sdkb (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/a/af/"
                "Duke_University_West_Campus_%2824070516%29.jpg"
            ),
            "credit": "Wikimedia Commons / Matt Phillips from Brooklyn, NY, USA (CC BY 2.0)",
        },
    ],
    "flagship": {
        # Duke Facts / NCES College Navigator (Fall 2024): 17,499 total students —
        # 6,523 undergraduate + 10,976 graduate and professional.
        "enrollment_total": 17499,
        # Duke Today — Class of 2029 first-year admissions cycle.
        "applicants": 58698,
        "admits": 2818,
        "admissions_cycle": "Class of 2029 (entering fall 2025; Duke Today)",
        # Traces its origins to 1838; established as Duke University in 1924.
        "founded_year": 1838,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Duke, UNITID 198419)",
            "url": "https://collegescorecard.ed.gov/school/?198419",
        },
        {
            "label": "NCES College Navigator — Duke University (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=198419",
        },
        {
            "label": "Duke University — Duke Facts",
            "url": "https://facts.duke.edu/",
        },
        {
            "label": "Duke Office of the Provost — Common Data Set 2024-25",
            "url": "https://ir.provost.duke.edu/facts-figures/common-data-sets/",
        },
        {
            "label": "Duke Today — Duke welcomes newest members of Class of 2029",
            "url": "https://today.duke.edu/2025/03/duke-welcomes-newest-members-class-2029",
        },
        {
            "label": "Duke Career Hub — First-Destination Outcomes (Class of 2022)",
            "url": "https://careerhub.students.duke.edu/outcome-data-text-version/",
        },
        {
            "label": "Giving to Duke — Endowment ($12.3B, FY2025)",
            "url": "https://giving.duke.edu/endowment/",
        },
        {
            "label": "Carnegie Classifications — Duke University (R1)",
            "url": "https://carnegieclassifications.acenet.edu/institution/duke-university/",
        },
        {
            "label": "QS World University Rankings 2026 — Duke University",
            "url": "https://www.topuniversities.com/universities/duke-university",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — Duke University",
            "url": "https://www.timeshighereducation.com/world-university-rankings/duke-university",
        },
        {
            "label": "U.S. News Best Colleges 2026 — Duke University (#7 National Universities)",
            "url": "https://www.usnews.com/best-colleges/duke-university-2920",
        },
        {
            "label": "Duke University 100 — The Founding of Duke University (1838 / 1924)",
            "url": "https://100.duke.edu/story/the-founding-of-duke-university/",
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it "Undergraduates");
# the total (17,499) lives in flagship.enrollment_total and renders as "Total enrollment".
UNDERGRAD_COUNT = 6523

DESCRIPTION = (
    "Duke University is a private research university in Durham, North Carolina. It "
    "traces its origins to 1838 — to Brown's Schoolhouse and the Methodist- and "
    "Quaker-founded Union Institute in Randolph County — and took its present form in "
    "December 1924, when the industrialist James B. Duke created The Duke Endowment and "
    "the trustees renamed Trinity College (which had relocated to Durham in 1892) in "
    "honor of his father, Washington Duke. It enrolls about 6,500 undergraduates and "
    "roughly 11,000 graduate and professional students — some 17,500 in all — with a "
    "6:1 student-faculty ratio and a faculty of about 4,200.\n\n"
    "Duke is organized into ten schools and colleges. Undergraduates study in Trinity "
    "College of Arts & Sciences and the Pratt School of Engineering, and the university "
    "spans the Fuqua School of Business, the School of Law, the School of Medicine, the "
    "School of Nursing, the Nicholas School of the Environment, the Sanford School of "
    "Public Policy, the Divinity School, and The Graduate School, which confers the "
    "Ph.D. across more than fifty programs. Its research — over a billion dollars a year, "
    "much of it in health and the life sciences — is anchored by the Duke Institute for "
    "Brain Sciences, the Duke Global Health Institute, and the Duke Clinical Research "
    "Institute, the world's largest academic clinical-research organization.\n\n"
    "A Carnegie R1 university accredited by SACSCOC, Duke ranks among the strongest "
    "research universities in the world: No. 7 among national universities by U.S. News, "
    "No. 28 in the world by Times Higher Education, and No. 62 by QS. It admitted 4.8% of "
    "first-year applicants for the Class of 2029 and holds an endowment of $12.3 billion "
    "as of June 2025.\n\n"
    "Duke meets the full demonstrated financial need of admitted undergraduates: the "
    "average net price is about $30,000 a year against a sticker cost of attendance near "
    "$92,000, and the median federal debt of completers is about $13,000. Among the Class "
    "of 2022, 90% of graduates were employed or continuing their education within the "
    "survey window, most heavily in technology, finance, and consulting. Duke's teams, "
    "the Blue Devils, compete in NCAA Division I in the Atlantic Coast Conference."
)

# ── The real degree-granting schools (display order) ───────────────────────
_TRINITY = "Trinity College of Arts & Sciences"
_PRATT = "Pratt School of Engineering"
_FUQUA = "The Fuqua School of Business"
_LAW = "Duke University School of Law"
_MED = "Duke University School of Medicine"
_NURSING = "Duke University School of Nursing"
_NICHOLAS = "Nicholas School of the Environment"
_SANFORD = "Sanford School of Public Policy"
_DIVINITY = "Duke Divinity School"
_GRAD = "The Graduate School"

SCHOOLS: list[dict] = [
    {
        "name": _TRINITY,
        "sort_order": 1,
        "description": (
            "Trinity College of Arts & Sciences is Duke's undergraduate liberal-arts "
            "college and its largest academic unit, teaching across the arts & humanities, "
            "natural sciences and social sciences. It awards the A.B. and B.S. across more "
            "than fifty majors and houses the majority of Duke's Ph.D.-granting "
            "departments."
        ),
    },
    {
        "name": _PRATT,
        "sort_order": 2,
        "description": (
            "The Edmund T. Pratt Jr. School of Engineering offers undergraduate (B.S.E.) "
            "and graduate degrees across biomedical, civil & environmental, electrical & "
            "computer, and mechanical engineering & materials science, with more than $100 "
            "million in annual research and close ties to Duke's medical center."
        ),
    },
    {
        "name": _FUQUA,
        "sort_order": 3,
        "description": (
            "The Fuqua School of Business, chartered in 1969 and named for J.B. Fuqua in "
            "1980, educates leaders through the Daytime MBA, executive MBAs, a family of "
            "specialized master's degrees and the Ph.D., and is known for its team-based, "
            "leadership-focused culture."
        ),
    },
    {
        "name": _LAW,
        "sort_order": 4,
        "description": (
            "Duke University School of Law awards the J.D., LL.M., S.J.D. and joint "
            "degrees, with particular strength in international and comparative law, law "
            "and technology, and empirical legal studies, and is home to the Bolch "
            "Judicial Institute."
        ),
    },
    {
        "name": _MED,
        "sort_order": 5,
        "description": (
            "Founded in 1930, the Duke University School of Medicine is a leading academic "
            "medical center awarding the M.D. alongside doctoral and master's degrees in "
            "the health professions and biomedical sciences, and home to the Duke Clinical "
            "Research Institute and the NCI-designated Duke Cancer Institute."
        ),
    },
    {
        "name": _NURSING,
        "sort_order": 6,
        "description": (
            "Established in 1931, the Duke University School of Nursing is a graduate-"
            "focused, NLN Center of Excellence awarding the master's, the Doctor of "
            "Nursing Practice and the Ph.D. across advanced-practice and nurse-anesthesia "
            "specialties."
        ),
    },
    {
        "name": _NICHOLAS,
        "sort_order": 7,
        "description": (
            "The Nicholas School of the Environment, formed in 1991 around Duke's School "
            "of Forestry (1938) and Marine Laboratory, prepares environmental leaders "
            "through the Master of Environmental Management, the Master of Forestry, and "
            "doctoral study across ecology, earth & climate sciences, and marine science "
            "and conservation."
        ),
    },
    {
        "name": _SANFORD,
        "sort_order": 8,
        "description": (
            "The Sanford School of Public Policy — founded in 1971 and named for Terry "
            "Sanford, and a full school since 2009 — offers undergraduate, master's (MPP, "
            "MIDP) and doctoral degrees focused on rigorous policy analysis and leadership."
        ),
    },
    {
        "name": _DIVINITY,
        "sort_order": 9,
        "description": (
            "Duke Divinity School, founded in 1926, is one of North America's leading "
            "Protestant theological schools. Rooted in the Methodist tradition, it forms "
            "Christian leaders through the M.Div., M.T.S., Th.M., D.Min. and Th.D."
        ),
    },
    {
        "name": _GRAD,
        "sort_order": 10,
        "description": (
            "The Graduate School, founded in 1926, oversees Duke's Ph.D. and academic "
            "master's degrees — more than fifty doctoral programs across the humanities, "
            "the natural and social sciences, and engineering — and supports roughly 3,500 "
            "graduate students with funding and professional development."
        ),
    },
]

_SCHOOL_WEBSITE: dict[str, str] = {
    _TRINITY: "https://trinity.duke.edu/",
    _PRATT: "https://pratt.duke.edu/",
    _FUQUA: "https://www.fuqua.duke.edu/",
    _LAW: "https://law.duke.edu/",
    _MED: "https://medschool.duke.edu/",
    _NURSING: "https://nursing.duke.edu/",
    _NICHOLAS: "https://nicholas.duke.edu/",
    _SANFORD: "https://sanford.duke.edu/",
    _DIVINITY: "https://divinity.duke.edu/",
    _GRAD: "https://gradschool.duke.edu/",
}

# Per-school about_detail (founded, leadership, notable faculty, research centers,
# named_for, source). Notable faculty are listed only where a current named-prize holder
# was verified from an official page; otherwise about_detail.faculty is omitted (recorded
# in _ABOUT_OMITTED), never guessed.
_ABOUT_DETAIL: dict[str, dict] = {
    _TRINITY: {
        "founded": 1838,
        "leadership": "Gary G. Bennett — Dean of Trinity College of Arts & Sciences",
        "faculty": [
            "Paul Modrich — James B. Duke Distinguished Professor of Biochemistry; "
            "2015 Nobel Prize in Chemistry",
            "Ingrid Daubechies — James B. Duke Distinguished Professor of Mathematics; "
            "2025 National Medal of Science",
        ],
        "research_centers": [
            "Center for Cognitive Neuroscience",
            "Center for Documentary Studies",
            "Duke Population Research Center",
            "Center for the History of Political Economy",
        ],
        "source": {
            "label": "Trinity College of Arts & Sciences — Dean Gary G. Bennett",
            "url": "https://trinity.duke.edu/dean-gary-g-bennett",
        },
    },
    _PRATT: {
        "founded": 1924,
        "leadership": "Jerome P. Lynch — Vinik Dean of the Pratt School of Engineering",
        "faculty": [
            "Ashutosh Chilkoti — Alan L. Kaganov Distinguished Professor of Biomedical Engineering",
            "Hai 'Helen' Li — Clare Boothe Luce Professor of Electrical & Computer "
            "Engineering; 2025 AAAS Fellow",
        ],
        "research_centers": [
            "Duke Quantum Center",
            "Duke Center for Biomolecular and Tissue Engineering",
            "NSF Engineering Research Center for Precision Microbiome Modulation (PreMiEr)",
        ],
        "named_for": "Edmund T. Pratt Jr. (Duke 1947), former chairman and CEO of Pfizer",
        "source": {
            "label": "Pratt School of Engineering — Dean Jerome P. Lynch",
            "url": "https://today.duke.edu/2025/07/jerome-lynch-reappointed-dean-pratt-school-engineering",
        },
    },
    _FUQUA: {
        "founded": 1969,
        "leadership": (
            "Mary Frances Luce — Robert A. Ingram Professor of Business Administration and Dean"
        ),
        "faculty": [
            "Dan Ariely — James B. Duke Distinguished Professor of Behavioral Economics",
            "Campbell R. Harvey — Professor of Finance; past President of the American "
            "Finance Association",
        ],
        "research_centers": [
            "Center for the Advancement of Social Entrepreneurship (CASE)",
            "Fuqua/Coach K Center on Leadership & Ethics (COLE)",
            "Center for Energy, Development, and the Global Environment (EDGE)",
            "Center for Health Sector Management (HSM)",
        ],
        "named_for": "J.B. Fuqua (1918-2006), business executive and philanthropist",
        "source": {
            "label": "The Fuqua School of Business — Our Dean",
            "url": "https://www.fuqua.duke.edu/about/leadership/our-dean",
        },
    },
    _LAW: {
        "founded": 1868,
        "leadership": (
            "Kerry Abrams — James B. Duke and Benjamin N. Duke Dean of the School of Law"
        ),
        "research_centers": [
            "Bolch Judicial Institute",
            "Wilson Center for Science and Justice",
            "Center for International and Comparative Law",
            "Duke Center on Law & Technology",
        ],
        "source": {
            "label": "Duke University School of Law — Message from the Dean",
            "url": "https://law.duke.edu/about/messagefromthedean",
        },
    },
    _MED: {
        "founded": 1930,
        "leadership": (
            "Mary E. Klotman — Dean of the School of Medicine and Executive Vice President "
            "for Health Affairs"
        ),
        "faculty": [
            "Robert J. Lefkowitz — James B. Duke Professor of Medicine; 2012 Nobel Prize "
            "in Chemistry",
            "Paul Modrich — James B. Duke Distinguished Professor of Biochemistry; 2015 "
            "Nobel Prize in Chemistry",
        ],
        "research_centers": [
            "Duke Clinical Research Institute (DCRI)",
            "Duke Cancer Institute",
            "Duke Human Vaccine Institute",
            "Duke Clinical and Translational Science Institute (CTSI)",
        ],
        "source": {
            "label": "Duke University School of Medicine — About the Dean",
            "url": "https://medschool.duke.edu/about-us/leadership-and-administration/about-dean",
        },
    },
    _NURSING: {
        "founded": 1931,
        "leadership": (
            "Michael V. Relf — Dean and Mary T. Champagne Distinguished Professor of Nursing"
        ),
        "research_centers": [
            "Center for Nursing Research",
            "Institute for Educational Excellence",
            "Center for Nursing Discovery",
            "Duke Advancement of Nursing, Center of Excellence (DANCE)",
        ],
        "source": {
            "label": "Duke University School of Nursing — Dean Michael V. Relf",
            "url": "https://today.duke.edu/2025/04/michael-relf-named-dean-school-nursing",
        },
    },
    _NICHOLAS: {
        "founded": 1991,
        "leadership": "Lori Bennear — Stanback Dean of the Nicholas School of the Environment",
        "research_centers": [
            "Nicholas Institute for Energy, Environment & Sustainability",
            "Juli Plant Grainger Center for River Science",
            "Duke University Wetland and Coasts Center",
            "Duke Marine Laboratory",
        ],
        "named_for": "Peter M. Nicholas (Duke 1964) and the Nicholas family",
        "source": {
            "label": "Nicholas School of the Environment — Dean Lori Bennear",
            "url": "https://today.duke.edu/2025/03/bennear-named-dean-nicholas-school-environment",
        },
    },
    _SANFORD: {
        "founded": 1971,
        "leadership": "JR DeShazo — Joel L. Fleishman Dean of the Sanford School of Public Policy",
        "research_centers": [
            "Duke Center for International Development",
            "DeWitt Wallace Center for Media & Democracy",
            "Samuel DuBois Cook Center on Social Equity",
            "Duke-UNC Rotary Peace Center",
        ],
        "named_for": "Terry Sanford (1917-1998), N.C. Governor, U.S. Senator and Duke President",
        "source": {
            "label": "Sanford School of Public Policy — Dean JR DeShazo",
            "url": "https://today.duke.edu/2026/04/jr-deshazo-appointed-dean-sanford-school-public-policy",
        },
    },
    _DIVINITY: {
        "founded": 1926,
        "leadership": (
            "Edgardo Colón-Emeric — Dean of Duke Divinity School and Williams Professor "
            "of Theology and Christian Ministry"
        ),
        "faculty": [
            "Stanley Hauerwas — Gilbert T. Rowe Professor Emeritus of Divinity and Law; "
            "named 'America's Best Theologian' by Time (2001)",
        ],
        "research_centers": [
            "Center for Reconciliation",
            "Duke Initiatives in Theology and the Arts",
            "Theology, Medicine, and Culture Initiative",
            "Thriving Rural Communities Initiative",
        ],
        "source": {
            "label": "Duke Divinity School — Administration & Faculty (Dean)",
            "url": "https://divinity.bulletins.duke.edu/about/admin-faculty",
        },
    },
    _GRAD: {
        "founded": 1926,
        "leadership": (
            "Suzanne E. Barbour — Dean of The Graduate School and Vice Provost for "
            "Graduate Education"
        ),
        "source": {
            "label": "The Graduate School — Dean Suzanne Barbour",
            "url": "https://today.duke.edu/2022/07/barbour-appointed-dean-graduate-school-and-vice-provost-graduate-education",
        },
    },
}

# Schools whose required about_detail fields are honestly omitted (verified-unavailable).
_FACULTY_OMIT = ["about_detail.faculty"]
_ABOUT_OMITTED: dict[str, list[str]] = {
    # No current Duke Law / Nursing / Nicholas / Sanford faculty member could be verified
    # as a named-prize holder (Nobel/MacArthur) from an official page, so the notable-
    # faculty roster is omitted rather than guessed.
    _LAW: list(_FACULTY_OMIT),
    _NURSING: list(_FACULTY_OMIT),
    _NICHOLAS: list(_FACULTY_OMIT),
    _SANFORD: list(_FACULTY_OMIT),
    # The Graduate School is an administrative/oversight school: it has no resident
    # research faculty or research centers of its own (those live in the departments and
    # the professional schools), so both are omitted by design.
    _GRAD: ["about_detail.faculty", "about_detail.research_centers"],
}

# ── Channel feeds + official social links ──────────────────────────────────
# The daily content-ingest reads news_rss (RSS), an optional events_feed (iCalendar),
# keywords (word-boundary relevance filter) and news_curated (keep every item) from each
# node's content_sources. Without a real news_rss a node's Events & Updates tab is empty —
# so every school and program below carries one. Feeds verified (HTTP 200) 2026-06-11:
#   • Duke Today all-topics RSS: https://today.duke.edu/topics/all/rss
#   • Duke Today per-school tag RSS: https://today.duke.edu/tags/<tag>/rss (10 items each)
#   • Duke events iCalendar: https://calendar.duke.edu/index.ics (BEGIN:VCALENDAR)
_DUKE_NEWS_ALL = "https://today.duke.edu/topics/all/rss"
_DUKE_EVENTS_ICS = {"url": "https://calendar.duke.edu/index.ics", "type": "ical"}


def _school_tag_feed(tag: str) -> str:
    """A verified Duke Today per-school tag RSS feed."""
    return f"https://today.duke.edu/tags/{tag}/rss"


# Official university social handles (Duke News social-media directory, verified 2026-06-11).
_SOCIAL_DUKE = {
    "instagram": "https://www.instagram.com/dukeuniversity/",
    "linkedin": "https://www.linkedin.com/school/duke-university/",
    "x": "https://twitter.com/DukeU",
    "youtube": "https://www.youtube.com/user/Duke",
    "facebook": "https://www.facebook.com/DukeUniv/",
}
# Per-school official handles, verified per channel 2026-06-11 (school sites + footers).
# Only handles confirmed to exist are listed; a school that does not run a given channel
# simply omits that key (never guessed).
_SOCIAL_BY_SCHOOL: dict[str, dict] = {
    _TRINITY: {
        "instagram": "https://www.instagram.com/duketrinitycollege/",
        "linkedin": "https://www.linkedin.com/company/duketrinity/",
        "youtube": "https://www.youtube.com/channel/UCkkjI39uwPgQawx6tw1-VlA",
    },
    _PRATT: {
        "instagram": "https://www.instagram.com/dukeengineering/",
        "linkedin": "https://www.linkedin.com/school/duke-engineering/",
        "x": "https://twitter.com/DukeEngineering",
        "youtube": "https://www.youtube.com/user/DukeEngineering",
        "facebook": "https://www.facebook.com/DukeEngineering/",
    },
    _FUQUA: {
        "instagram": "https://www.instagram.com/dukefuqua/",
        "linkedin": "https://www.linkedin.com/school/fuqua-school-of-business/",
        "x": "https://twitter.com/DukeFuqua",
        "youtube": "https://www.youtube.com/user/FuquaSchOfBusiness",
        "facebook": "https://www.facebook.com/Duke.Fuqua",
    },
    _LAW: {
        "instagram": "https://www.instagram.com/dukelaw/",
        "linkedin": "https://www.linkedin.com/school/dukelaw",
        "x": "https://twitter.com/DukeLaw",
        "youtube": "https://www.youtube.com/user/dukelaw",
        "facebook": "https://www.facebook.com/dukelaw/",
    },
    _MED: {
        "instagram": "https://www.instagram.com/dukeschoolofmedicine/",
        "linkedin": "https://www.linkedin.com/school/duke-med-school/",
        "x": "https://twitter.com/DukeMedSchool",
        "youtube": "https://www.youtube.com/user/DukeMedSchool",
        "facebook": "https://www.facebook.com/DukeSchoolofMedicine",
    },
    _NURSING: {
        "instagram": "https://www.instagram.com/dukeu_nursingschl/",
        "linkedin": "https://www.linkedin.com/school/duke-university-school-of-nursing/",
        "x": "https://twitter.com/DukeU_Nursing",
        "youtube": "https://www.youtube.com/user/DukeSchoolOfNursing",
        "facebook": "https://www.facebook.com/DukeUniversitySchoolofNursing",
    },
    _NICHOLAS: {
        "instagram": "https://www.instagram.com/dukeenvironment/",
        "x": "https://twitter.com/DukeEnvironment",
        "youtube": "https://www.youtube.com/user/nicholasschoolatduke",
        "facebook": "https://www.facebook.com/DukeEnvironment/",
    },
    _SANFORD: {
        "instagram": "https://www.instagram.com/duke_sanford/",
        "linkedin": (
            "https://www.linkedin.com/school/duke-university-sanford-school-of-public-policy/"
        ),
        "x": "https://twitter.com/DukeSanford",
        "youtube": "https://www.youtube.com/channel/UCRfoJqjnOCHU5nKJvw5JIOA",
        "facebook": "https://www.facebook.com/duke.sanfordschool",
    },
    _DIVINITY: {
        "instagram": "https://www.instagram.com/dukedivinity/",
        "linkedin": "https://www.linkedin.com/school/duke-divinity-school/",
        "x": "https://x.com/DukeDivinity",
        "youtube": "https://www.youtube.com/user/DukeDivinitySchool",
        "facebook": "https://www.facebook.com/DukeDivinity/",
    },
    _GRAD: {
        "instagram": "https://www.instagram.com/dukegradschool/",
        "linkedin": "https://www.linkedin.com/school/duke-university-graduate-school/",
        "x": "https://twitter.com/DukeGradSchool",
        "youtube": "https://www.youtube.com/user/dukegraduateschool",
        "facebook": "https://www.facebook.com/DukeGradSchool",
    },
}

# Per-school feed config: the verified Duke Today per-school tag RSS + the Duke events
# iCalendar, filtered to school-relevant items by keywords (the MIT/MBAn pattern).
_SCHOOL_FEED_SPEC: dict[str, dict] = {
    _TRINITY: {
        "tag": "trinity-college-of-arts-sciences",
        "keywords": ["Trinity College", "Arts & Sciences", "undergraduate"],
    },
    _PRATT: {
        "tag": "pratt-school-of-engineering",
        "keywords": ["Pratt", "engineering", "engineers"],
    },
    _FUQUA: {
        "tag": "fuqua-school-of-business",
        "keywords": ["Fuqua", "business school", "MBA"],
    },
    _LAW: {"tag": "school-of-law", "keywords": ["Law School", "Duke Law"]},
    _MED: {
        "tag": "school-of-medicine",
        "keywords": ["School of Medicine", "medical", "physicians"],
    },
    _NURSING: {"tag": "school-of-nursing", "keywords": ["Nursing", "nurse", "nurses"]},
    _NICHOLAS: {
        "tag": "nicholas-school-of-the-environment",
        "keywords": ["Nicholas School", "environment", "environmental"],
    },
    _SANFORD: {
        "tag": "sanford-school-of-public-policy",
        "keywords": ["Sanford School", "public policy", "policy"],
    },
    _DIVINITY: {
        "tag": "divinity-school",
        "keywords": ["Divinity", "theology", "ministry"],
    },
    _GRAD: {
        "tag": "graduate-school",
        "keywords": ["Graduate School", "doctoral", "Ph.D."],
    },
}


def _school_content(name: str) -> dict:
    """Build a school's content_sources from its verified tag RSS + keywords + socials."""
    spec = _SCHOOL_FEED_SPEC[name]
    return {
        "news_rss": _school_tag_feed(spec["tag"]),
        "news_curated": False,
        "events_feed": dict(_DUKE_EVENTS_ICS),
        "keywords": list(spec["keywords"]),
        "social": _SOCIAL_BY_SCHOOL.get(name, _SOCIAL_DUKE),
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    """Build a program's content_sources from its school feed, refined by program keywords."""
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


# Institution-wide feed: the all-topics Duke Today RSS (curated — every item is Duke news)
# + the Duke events iCalendar, with the official university social handles.
_INSTITUTION_CONTENT: dict = {
    "news_rss": _DUKE_NEWS_ALL,
    "news_url": "https://today.duke.edu",
    "news_curated": True,
    "events_feed": dict(_DUKE_EVENTS_ICS),
    "social": _SOCIAL_DUKE,
}

# ── The program catalog (real majors/degrees, organized by school) ─────────
# Undergraduate majors of Trinity College and Pratt (Duke's official undergraduate
# Bulletin / majors lists). Each is a residential bachelor's degree.
_TRINITY_MAJORS: list[str] = [
    "African & African American Studies",
    "Art History",
    "Visual Arts",
    "Visual & Media Studies",
    "Asian & Middle Eastern Studies",
    "Biology",
    "Biophysics",
    "Brazilian & Global Portuguese",
    "Chemistry",
    "Classical Civilization",
    "Classical Languages",
    "Computational Media",
    "Computer Science",
    "Cultural Anthropology",
    "Dance",
    "Earth & Climate Sciences",
    "Economics",
    "English",
    "Environmental Sciences & Policy",
    "Evolutionary Anthropology",
    "French & Francophone Studies",
    "Gender, Sexuality & Feminist Studies",
    "German",
    "Global Cultural Studies",
    "Global Health",
    "History",
    "International Comparative Studies",
    "Italian & European Studies",
    "Linguistics",
    "Marine Science & Conservation",
    "Mathematics",
    "Medieval & Renaissance Studies",
    "Music",
    "Neuroscience",
    "Philosophy",
    "Physics",
    "Political Science",
    "Psychology",
    "Public Policy Studies",
    "Religious Studies",
    "Romance Studies",
    "Russian",
    "Slavic & Eurasian Studies",
    "Sociology",
    "Spanish, Latin American & Latino/a Studies",
    "Statistical Science",
    "Theater Studies",
    "Data Science: Mathematics & Computer Science",
    "Linguistics & Computer Science",
    "Program II (self-designed major)",
]
_PRATT_MAJORS: list[str] = [
    "Biomedical Engineering",
    "Civil Engineering",
    "Electrical & Computer Engineering",
    "Environmental Engineering",
    "Mechanical Engineering",
    "Interdisciplinary Engineering & Applied Science (IDEAS)",
]

# Graduate / professional programs (degree-granting), each verified from its school's
# official program/tuition page. Tuple: (name, degree_type, school, duration_months,
# delivery_format, website, tuition_usd | None, tuition_kind, description).
#   tuition_kind ∈ {"year", "total", None}; None tuition → cost recorded "see school page".
_GRAD_EXPLICIT: list[tuple] = [
    # ── The Fuqua School of Business ──
    (
        "Daytime MBA",
        "masters",
        _FUQUA,
        22,
        "on_campus",
        "https://www.fuqua.duke.edu/programs/daytime-mba",
        83700,
        "year",
        "Fuqua's flagship full-time, two-year MBA, built on a team-based, leadership-"
        "focused core and a broad portfolio of electives and concentrations.",
    ),
    (
        "Accelerated Daytime MBA",
        "masters",
        _FUQUA,
        10,
        "on_campus",
        "https://www.fuqua.duke.edu/programs/accelerated-daytime-mba",
        None,
        None,
        "A 10-month MBA for applicants who already hold a master's in management, "
        "joining the Daytime MBA cohort for the second year.",
    ),
    (
        "Weekend Executive MBA",
        "masters",
        _FUQUA,
        22,
        "hybrid",
        "https://www.fuqua.duke.edu/programs/weekend-executive-mba",
        None,
        None,
        "A 22-month executive MBA blending monthly three-day campus residencies with "
        "distance learning for working professionals.",
    ),
    (
        "Master of Management Studies: Foundations of Business",
        "masters",
        _FUQUA,
        10,
        "on_campus",
        "https://www.fuqua.duke.edu/programs/mms-foundations-of-business",
        69900,
        "total",
        "A 10-month pre-experience master's that gives recent graduates the fundamentals "
        "of business and management.",
    ),
    (
        "Master in Business, Climate, and Sustainability (MBCS)",
        "masters",
        _FUQUA,
        10,
        "on_campus",
        "https://www.fuqua.duke.edu/programs/mbcs",
        None,
        None,
        "A 10-month master's preparing graduates to lead at the intersection of business, "
        "climate and sustainability.",
    ),
    (
        "Master of Quantitative Management: Business Analytics",
        "masters",
        _FUQUA,
        10,
        "on_campus",
        "https://www.fuqua.duke.edu/programs/mqm-business-analytics",
        87800,
        "total",
        "A STEM-designated, 10-month master's in business analytics and data-driven "
        "decision-making across four industry tracks.",
    ),
    (
        "MSQM: Business Analytics (online)",
        "masters",
        _FUQUA,
        19,
        "online",
        "https://www.fuqua.duke.edu/programs/msqm-business-analytics",
        None,
        None,
        "A 19-month online master's in business analytics for working professionals.",
    ),
    (
        "MSQM: Health Analytics (online)",
        "masters",
        _FUQUA,
        19,
        "online",
        "https://www.fuqua.duke.edu/programs/msqm-health-analytics",
        None,
        None,
        "A 19-month online master's applying analytics to the healthcare sector for "
        "working professionals.",
    ),
    (
        "PhD in Business Administration",
        "phd",
        _FUQUA,
        60,
        "on_campus",
        "https://www.fuqua.duke.edu/programs/phd",
        None,
        None,
        "A fully funded doctoral program across accounting, decision sciences, finance, "
        "management & organizations, marketing, operations and strategy.",
    ),
    # ── Duke University School of Law ──
    (
        "Juris Doctor (JD)",
        "professional",
        _LAW,
        36,
        "on_campus",
        "https://law.duke.edu/apply/degreeprograms/jd",
        83400,
        "year",
        "Duke Law's three-year J.D. — a rigorous, collaborative legal education with "
        "strength in international, technology and empirical legal studies.",
    ),
    (
        "Master of Laws (LLM)",
        "masters",
        _LAW,
        12,
        "on_campus",
        "https://law.duke.edu/internat/llm",
        80100,
        "total",
        "A one-year master of laws for graduates of foreign law schools seeking exposure "
        "to the U.S. legal system.",
    ),
    (
        "JD/LLM in International & Comparative Law",
        "professional",
        _LAW,
        36,
        "on_campus",
        "https://law.duke.edu/apply/degreeprograms/jdllm",
        93450,
        "year",
        "A three-year dual degree pairing the J.D. with an LL.M. in international and "
        "comparative law.",
    ),
    (
        "JD/LLM in Law & Entrepreneurship",
        "professional",
        _LAW,
        36,
        "on_campus",
        "https://law.duke.edu/llmle/jd",
        93450,
        "year",
        "A three-year dual degree pairing the J.D. with an LL.M. in law and entrepreneurship.",
    ),
    (
        "Doctor of Juridical Science (SJD)",
        "phd",
        _LAW,
        60,
        "on_campus",
        "https://law.duke.edu/internat/",
        None,
        None,
        "Duke Law's most advanced research degree, for scholars pursuing a substantial "
        "doctoral dissertation in law.",
    ),
    (
        "Master of Judicial Studies (MJS)",
        "masters",
        _LAW,
        24,
        "hybrid",
        "https://judicialstudies.duke.edu/",
        None,
        None,
        "A hybrid degree of the Bolch Judicial Institute for sitting judges, combining "
        "summer on-campus sessions with a thesis.",
    ),
    # ── Duke University School of Medicine ──
    (
        "Doctor of Medicine (MD)",
        "professional",
        _MED,
        48,
        "on_campus",
        "https://medschool.duke.edu/education/md-program",
        72297,
        "year",
        "Duke's M.D. program, known for compressing the basic sciences into the first "
        "year to free the third year for scholarly research.",
    ),
    (
        "Medical Scientist Training Program (MD-PhD)",
        "phd",
        _MED,
        84,
        "on_campus",
        "https://medschool.duke.edu/education/health-professions-education-programs/medical-scientist-training-program",
        None,
        None,
        "An NIH-funded, fully supported dual M.D.-Ph.D. program training physician-scientists.",
    ),
    (
        "Doctor of Physical Therapy (DPT)",
        "professional",
        _MED,
        36,
        "on_campus",
        "https://medschool.duke.edu/education/health-professions-education-programs/doctor-physical-therapy",
        42000,
        "year",
        "A clinical doctorate preparing physical therapists for evidence-based practice.",
    ),
    (
        "Occupational Therapy Doctorate (OTD)",
        "professional",
        _MED,
        36,
        "on_campus",
        "https://medschool.duke.edu/education/health-professions-education-programs/occupational-therapy-doctorate",
        43000,
        "year",
        "An entry-level clinical doctorate in occupational therapy.",
    ),
    (
        "Physician Assistant Program (MHS)",
        "masters",
        _MED,
        24,
        "on_campus",
        "https://medschool.duke.edu/education/health-professions-education-programs/physician-assistant-program",
        None,
        None,
        "The nation's first physician assistant program, awarding the Master of Health Sciences.",
    ),
    (
        "Master of Biomedical Sciences (MBS)",
        "masters",
        _MED,
        10,
        "on_campus",
        "https://medschool.duke.edu/education/health-professions-education-programs/master-biomedical-sciences",
        None,
        None,
        "A 10-month master's strengthening the academic record of students preparing for "
        "health-professional school.",
    ),
    (
        "Master of Biostatistics",
        "masters",
        _MED,
        24,
        "on_campus",
        "https://biostat.duke.edu/education-and-training/master-biostatistics",
        None,
        None,
        "A two-year master's in biostatistics across clinical/translational, biomedical "
        "data science, mathematical statistics and health-AI tracks.",
    ),
    (
        "Master of Health Sciences in Clinical Research (online)",
        "masters",
        _MED,
        24,
        "online",
        "https://biostat.duke.edu/education-and-training/master-health-sciences-clinical-research",
        None,
        None,
        "An online, synchronous master's training health professionals in clinical "
        "research methods.",
    ),
    (
        "Master of Science in Medical Physics",
        "masters",
        _MED,
        24,
        "on_campus",
        "https://medicalphysics.duke.edu/",
        None,
        None,
        "A CAMPEP-accredited, two-year master's in medical physics across imaging, "
        "therapy, nuclear-medicine and health-physics tracks.",
    ),
    (
        "Master of Science in Population Health Sciences",
        "masters",
        _MED,
        24,
        "on_campus",
        "https://populationhealth.duke.edu/education/ms-population-health-sciences",
        None,
        None,
        "A two-year master's training researchers in the methods of population health.",
    ),
    (
        "Master of Management in Clinical Informatics (MMCi)",
        "masters",
        _MED,
        12,
        "hybrid",
        "https://medschool.duke.edu/education/health-professions-education-programs/master-management-clinical-informatics",
        None,
        None,
        "A 12-month hybrid master's blending online study with monthly on-campus sessions "
        "in clinical and health informatics.",
    ),
    # ── Duke University School of Nursing ──
    (
        "Master of Nursing (MN, pre-licensure)",
        "masters",
        _NURSING,
        16,
        "on_campus",
        "https://nursing.duke.edu/academic-programs/mn-master-nursing",
        118816,
        "total",
        "An accelerated, pre-licensure master's entry into nursing for students with a "
        "prior bachelor's degree.",
    ),
    (
        "Master of Science in Nursing (MSN)",
        "masters",
        _NURSING,
        24,
        "hybrid",
        "https://nursing.duke.edu/academic-programs/msn-master-science-nursing",
        None,
        None,
        "A hybrid master's preparing advanced-practice nurses across nurse-practitioner "
        "specialties from family to psychiatric-mental-health care.",
    ),
    (
        "Doctor of Nursing Practice (DNP)",
        "professional",
        _NURSING,
        36,
        "hybrid",
        "https://nursing.duke.edu/academic-programs/dnp-program-nursing",
        32880,
        "year",
        "A practice doctorate for advanced-practice and executive-leadership nurses, "
        "delivered in a distance-based format with on-campus intensives.",
    ),
    (
        "Doctor of Nursing Practice — Nurse Anesthesia",
        "professional",
        _NURSING,
        36,
        "on_campus",
        "https://nursing.duke.edu/academic-programs/dnp-program-nursing",
        70460,
        "year",
        "A full-time DNP educating certified registered nurse anesthetists.",
    ),
    (
        "PhD in Nursing",
        "phd",
        _NURSING,
        48,
        "on_campus",
        "https://nursing.duke.edu/academic-programs/phd-program-nursing",
        None,
        None,
        "A research doctorate preparing nurse scientists for academic and research careers.",
    ),
    # ── Nicholas School of the Environment ──
    (
        "Master of Environmental Management (MEM)",
        "masters",
        _NICHOLAS,
        24,
        "on_campus",
        "https://nicholas.duke.edu/academics/masters-programs/master-environmental-management",
        48088,
        "year",
        "A two-year professional master's across concentrations from ecosystem science "
        "to energy and environment, with a management-skills core.",
    ),
    (
        "Master of Forestry (MF)",
        "masters",
        _NICHOLAS,
        24,
        "on_campus",
        "https://nicholas.duke.edu/academics/masters-programs/master-forestry",
        48088,
        "year",
        "A Society of American Foresters-accredited two-year professional master's in "
        "forestry and forest resource management.",
    ),
    (
        "Duke Environmental Leadership MEM (DEL-MEM, online)",
        "masters",
        _NICHOLAS,
        24,
        "online",
        "https://nicholas.duke.edu/academics/masters-programs/duke-environmental-leadership-master-environmental-management",
        48088,
        "year",
        "An online MEM with five place-based sessions, designed for mid-career "
        "environmental professionals.",
    ),
    # ── Sanford School of Public Policy ──
    (
        "Master of Public Policy (MPP)",
        "masters",
        _SANFORD,
        24,
        "on_campus",
        "https://sanford.duke.edu/academics/masters-programs/master-public-policy/",
        63746,
        "year",
        "A two-year, residential professional master's in policy analysis and leadership.",
    ),
    (
        "Master of International Development Policy (MIDP)",
        "masters",
        _SANFORD,
        24,
        "on_campus",
        "https://sanford.duke.edu/academics/midp/",
        63746,
        "year",
        "A residential, mid-career master's in international development policy.",
    ),
    (
        "Master of Public Affairs (MPA)",
        "masters",
        _SANFORD,
        15,
        "hybrid",
        "https://sanford.duke.edu/master-public-affairs/",
        66382,
        "total",
        "A hybrid, mid-career master's combining online study with in-person residencies "
        "in Durham and Washington, D.C.",
    ),
    (
        "Master of National Security Policy (MNSP)",
        "masters",
        _SANFORD,
        12,
        "hybrid",
        "https://sanford.duke.edu/admissions/mnsp-admissions/",
        55722,
        "total",
        "A hybrid, mid-career master's for national-security professionals.",
    ),
    # ── Duke Divinity School ──
    (
        "Master of Divinity (MDiv)",
        "masters",
        _DIVINITY,
        36,
        "on_campus",
        "https://divinity.duke.edu/academics/mdiv",
        30600,
        "year",
        "A three-year master's forming leaders for ordained and lay Christian ministry.",
    ),
    (
        "Master of Theological Studies (MTS)",
        "masters",
        _DIVINITY,
        24,
        "on_campus",
        "https://divinity.duke.edu/academics/mts",
        30600,
        "year",
        "A two-year academic master's for students pursuing theological research or "
        "further graduate study.",
    ),
    (
        "Master of Arts in Christian Practice",
        "masters",
        _DIVINITY,
        24,
        "on_campus",
        "https://divinity.duke.edu/academics/macp",
        30600,
        "year",
        "A part-time master's integrating theological study with Christian practice.",
    ),
    (
        "Master of Theology (ThM)",
        "masters",
        _DIVINITY,
        12,
        "on_campus",
        "https://divinity.duke.edu/academics/thm",
        36750,
        "year",
        "A one-year advanced master's, typically following the M.Div., for focused "
        "theological study.",
    ),
    (
        "Doctor of Ministry (DMin)",
        "professional",
        _DIVINITY,
        36,
        "hybrid",
        "https://divinity.duke.edu/academics/dmin",
        31500,
        "year",
        "A hybrid professional doctorate for active ministry leaders.",
    ),
    (
        "Doctor of Theology (ThD)",
        "phd",
        _DIVINITY,
        60,
        "on_campus",
        "https://divinity.duke.edu/academics/thd",
        52000,
        "year",
        "Duke Divinity's research doctorate in theology.",
    ),
    # ── Pratt School of Engineering — professional master's ──
    (
        "Master of Engineering in AI for Product Innovation",
        "masters",
        _PRATT,
        16,
        "hybrid",
        "https://masters.pratt.duke.edu/aipi/",
        None,
        None,
        "A professional MEng building AI and machine-learning products, offered on campus "
        "or online.",
    ),
    (
        "Master of Science in Biomedical Engineering",
        "masters",
        _PRATT,
        18,
        "on_campus",
        "https://masters.pratt.duke.edu/biomedical/",
        102930,
        "total",
        "An MEng/MS in biomedical engineering, offered on campus or online.",
    ),
    (
        "Master of Engineering in Civil Engineering",
        "masters",
        _PRATT,
        18,
        "on_campus",
        "https://masters.pratt.duke.edu/civil/",
        102930,
        "total",
        "A professional MEng in civil engineering.",
    ),
    (
        "Master of Science in Electrical & Computer Engineering",
        "masters",
        _PRATT,
        18,
        "on_campus",
        "https://masters.pratt.duke.edu/electrical-computer/",
        102930,
        "total",
        "An MEng/MS in electrical and computer engineering.",
    ),
    (
        "Master of Engineering Management",
        "masters",
        _PRATT,
        18,
        "hybrid",
        "https://masters.pratt.duke.edu/management/",
        69600,
        "total",
        "A professional master's combining engineering with business and leadership, "
        "offered on campus or online.",
    ),
    (
        "Master of Engineering in Cybersecurity",
        "masters",
        _PRATT,
        18,
        "hybrid",
        "https://masters.pratt.duke.edu/cybersecurity/",
        None,
        None,
        "A professional MEng in cybersecurity, offered on campus or online.",
    ),
    (
        "Master of Engineering in Financial Technology",
        "masters",
        _PRATT,
        18,
        "hybrid",
        "https://masters.pratt.duke.edu/fintech/",
        None,
        None,
        "A professional MEng in financial technology, offered on campus or online.",
    ),
    (
        "Master of Science in Mechanical Engineering & Materials Science",
        "masters",
        _PRATT,
        18,
        "on_campus",
        "https://masters.pratt.duke.edu/mechanical/",
        102930,
        "total",
        "An MEng/MS in mechanical engineering and materials science.",
    ),
]

# Graduate-School Ph.D. programs (Duke confers the Ph.D. through The Graduate School
# across 50+ programs). Listed from the official Graduate School programs directory.
_PHD_PROGRAMS: list[str] = [
    "Biochemistry",
    "Biology",
    "Biostatistics",
    "Cell & Molecular Biology",
    "Cell Biology",
    "Cognitive Neuroscience",
    "Computational Biology & Bioinformatics",
    "Developmental & Stem Cell Biology",
    "Ecology",
    "Genetics & Genomics",
    "Immunology",
    "Integrated Toxicology & Environmental Health",
    "Molecular Cancer Biology",
    "Molecular Genetics & Microbiology",
    "Neurobiology",
    "Pharmacology",
    "Population Health Sciences",
    "Medical Physics",
    "Art, Art History & Visual Studies",
    "Classical Studies",
    "English",
    "German Studies",
    "Literature",
    "Music",
    "Philosophy",
    "Religion",
    "Romance Studies",
    "Chemistry",
    "Computer Science",
    "Earth & Climate Sciences",
    "Marine Science & Conservation",
    "Materials Science & Engineering",
    "Mathematics",
    "Physics",
    "Statistical Science",
    "Biomedical Engineering",
    "Civil & Environmental Engineering",
    "Electrical & Computer Engineering",
    "Mechanical Engineering & Materials Science",
    "Cultural Anthropology",
    "Economics",
    "Environmental Policy",
    "History",
    "Political Science",
    "Psychology & Neuroscience",
    "Sociology",
]

_SLUG_REPL = {
    "&": "and",
    "—": " ",
    "/": " ",
    "'": "",
    ".": "",
    ",": "",
    "(": "",
    ")": "",
    ":": "",
}

# Professional schools where the owning unit for a degree is the school itself.
_PROFESSIONAL_SCHOOLS = frozenset(
    {
        _FUQUA,
        _LAW,
        _NURSING,
        _NICHOLAS,
        _SANFORD,
        _DIVINITY,
    }
)

# Pratt professional master's → real engineering department (masters.pratt.duke.edu).
_PRATT_GRAD_DEPARTMENT: dict[str, str] = {
    "Master of Engineering in AI for Product Innovation": "Electrical & Computer Engineering",
    "Master of Science in Biomedical Engineering": "Biomedical Engineering",
    "Master of Engineering in Civil Engineering": "Civil Engineering",
    "Master of Science in Electrical & Computer Engineering": "Electrical & Computer Engineering",
    "Master of Engineering Management": "Engineering Management",
    "Master of Engineering in Cybersecurity": "Electrical & Computer Engineering",
    "Master of Engineering in Financial Technology": "Electrical & Computer Engineering",
    "Master of Science in Mechanical Engineering & Materials Science": "Mechanical Engineering",
}

# Duke School of Medicine sub-departments (medschool.duke.edu program pages).
_MED_DEPARTMENT: dict[str, str] = {
    "Master of Biostatistics": "Biostatistics",
    "Master of Health Sciences in Clinical Research (online)": "Biostatistics",
    "Master of Science in Medical Physics": "Medical Physics",
    "Master of Science in Population Health Sciences": "Population Health Sciences",
    "Master of Management in Clinical Informatics (MMCi)": (
        "Department of Family Medicine and Community Health"
    ),
    "Physician Assistant Program (MHS)": "Physician Assistant Program",
}


def _department_for(field_name: str, school: str) -> str:
    """Owning department — field title unless it duplicates the school name."""
    if field_name.lower() in school.lower() or school.lower() in field_name.lower():
        return school
    return field_name


def _ug_program_name(field_name: str, school: str) -> str:
    if school == _PRATT:
        return f"Bachelor of Science in Engineering in {field_name}"
    # Trinity College confers the A.B. (Bachelor of Arts) — offered across all its
    # majors, with the B.S. as an alternative in many science/quantitative fields
    # (trinity.duke.edu/undergraduate/degrees-credentials + majors-minors). Use the
    # conferred designation, not the possessive "Bachelor's in" mint form (REPAIR
    # BACKLOG #9 / SKILL miss #2: gold MIT = 0% possessive names).
    return f"Bachelor of Arts in {field_name}"


def _grad_explicit_department(name: str, school: str) -> str:
    if school == _PRATT:
        return _PRATT_GRAD_DEPARTMENT.get(name, _PRATT)
    if school == _MED:
        return _MED_DEPARTMENT.get(name, _MED)
    if school in _PROFESSIONAL_SCHOOLS:
        return school
    return _department_for(name, school)


def _slugify(text_value: str) -> str:
    s = text_value.lower()
    for k, v in _SLUG_REPL.items():
        s = s.replace(k, v)
    return "-".join(s.split())


def _field_from_program_name(program_name: str) -> str | None:
    """Extract field title from a disambiguated program name."""
    for prefix in (
        "Bachelor of Arts in ",
        "Bachelor of Science in ",
        "Bachelor of Science in Engineering in ",
        "Bachelor's in ",
        "Master's in ",
        "Doctor of Philosophy in ",
        "Graduate Certificate in ",
        "Professional program in ",
    ):
        if program_name.startswith(prefix):
            return program_name[len(prefix) :]
    return None


def _needs_normalize(desc: str) -> bool:
    """True when a description is a classification or template stub."""
    if not desc:
        return True
    if _CLASSIFICATION_STUB_RE.match(desc):
        return True
    if _TEMPLATE_STUB_RE.search(desc):
        return True
    if "offered through the " in desc:
        return True
    return False


def _duke_description(spec: dict, field: str | None = None) -> str:
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
    if field_key == "Computer Science" and spec.get("degree_type") == "phd":
        return (
            "The Computer Science Ph.D. at Duke trains doctoral researchers through "
            "seminars, qualifying milestones, faculty lab work, and an original "
            "dissertation in areas such as AI, theory, systems, security, and "
            f"interdisciplinary computing.{delivery}"
        )
    clause = FIELD_DESCRIPTIONS.get(field_key)
    if not clause:
        raise ValueError(f"Missing FIELD_DESCRIPTIONS entry for {field_key!r} ({slug})")
    # The program_name is already the page heading; prefixing it here doubled the
    # heading (anti-stub `name_prefixed`). Open on the field fact instead.
    return f"{clause}{delivery}"


def _normalize_program(spec: dict, field_name: str | None = None) -> None:
    """Stamp a field-specific description on stub program nodes."""
    if not _needs_normalize(spec.get("description") or ""):
        return
    spec["description"] = _duke_description(spec, field=field_name)


def _build_catalog() -> list[dict]:
    """Assemble the full Duke program catalog (verified-basics nodes)."""
    out: list[dict] = []
    seen: set[str] = set()

    def _add(spec: dict) -> None:
        if spec["slug"] in seen:
            return
        seen.add(spec["slug"])
        out.append(spec)

    for name in _TRINITY_MAJORS:
        dept = _department_for(name, _TRINITY)
        pname = _ug_program_name(name, _TRINITY)
        spec = {
            "slug": f"duke-{_slugify(name)}-ab",
            "school": _TRINITY,
            "program_name": pname,
            "degree_type": "bachelors",
            "department": dept,
            "duration_months": 48,
            "delivery_format": "in_person",
            "_field_name": name,
        }
        _normalize_program(spec, name)
        spec.pop("_field_name", None)
        _add(spec)
    for name in _PRATT_MAJORS:
        dept = _department_for(name, _PRATT)
        pname = _ug_program_name(name, _PRATT)
        spec = {
            "slug": f"duke-{_slugify(name)}-bse",
            "school": _PRATT,
            "program_name": pname,
            "degree_type": "bachelors",
            "department": dept,
            "duration_months": 48,
            "delivery_format": "in_person",
            "_field_name": name,
        }
        _normalize_program(spec, name)
        spec.pop("_field_name", None)
        _add(spec)
    for (
        name,
        dtype,
        school,
        dur,
        fmt,
        website,
        tuition,
        tkind,
        desc,
    ) in _GRAD_EXPLICIT:
        suffix = {"phd": "phd", "professional": "prof"}.get(dtype, "ms")
        dept = _grad_explicit_department(name, school)
        _add(
            {
                "slug": f"duke-{_slugify(name)}-{suffix}",
                "school": school,
                "program_name": name,
                "degree_type": dtype,
                "department": dept,
                "duration_months": dur,
                "delivery_format": fmt,
                "website": website,
                "tuition": tuition,
                "tuition_kind": tkind,
                "description": desc,
            }
        )
    for name in _PHD_PROGRAMS:
        dept = _department_for(name, _GRAD)
        pname = disambiguate_program_name(name, "phd")
        spec = {
            "slug": f"duke-{_slugify(name)}-grad-phd",
            "school": _GRAD,
            "program_name": pname,
            "degree_type": "phd",
            "department": dept,
            "duration_months": 60,
            "delivery_format": "in_person",
            "_field_name": name,
        }
        _normalize_program(spec, name)
        spec.pop("_field_name", None)
        _add(spec)
    return out


PROGRAMS: list[dict] = _build_catalog()
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
    _catalog_errors.append(f"classification-only descriptions on {_classification_stubs} programs")
if _catalog_errors:
    raise RuntimeError(f"Duke catalog quality gate failed: {_catalog_errors}")
# Normalize residential delivery to the fleet-wide "in_person" value (the catalog tuples
# use "on_campus" for readability); "online"/"hybrid" are preserved.
for _p in PROGRAMS:
    if _p["delivery_format"] == "on_campus":
        _p["delivery_format"] = "in_person"
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}
_FULL_NAME_BY_SLUG: dict[str, str] = {p["slug"]: p["program_name"] for p in PROGRAMS}
_WEBSITE_BY_SLUG: dict[str, str] = {p["slug"]: p["website"] for p in PROGRAMS if p.get("website")}

# Per-program keyword overrides (department/program-naming terms). Programs without an
# entry inherit their school's keywords (still school-scoped).
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "duke-computer-science-ab": ["computer science", "Duke computer science"],
    "duke-economics-ab": ["economics", "economist"],
    "duke-political-science-ab": ["political science", "politics"],
    "duke-biology-ab": ["biology", "biologist"],
    "duke-neuroscience-ab": ["neuroscience", "brain"],
    "duke-public-policy-studies-ab": ["public policy", "Sanford"],
    "duke-daytime-mba-ms": ["MBA", "Fuqua"],
    "duke-juris-doctor-jd-prof": ["Duke Law", "law school"],
    "duke-doctor-of-medicine-md-prof": ["School of Medicine", "medical"],
}

# ── Costs ──────────────────────────────────────────────────────────────────
# Published 2025-26 Duke undergraduate figures (Duke Board of Trustees / College
# Scorecard). Used for every residential bachelor's major.
_TUITION_UG = 70265
_UNDERGRAD_COA = 92042
_AVG_NET_PRICE = 29612
_COST_SRC = (
    "Duke Board of Trustees 2025-26 cost of attendance + College Scorecard (UNITID 198419)",
    "https://collegescorecard.ed.gov/school/?198419",
)


_COST_SRC = (
    "Duke Board of Trustees 2025-26 cost of attendance + College Scorecard (UNITID 198419)",
    "https://collegescorecard.ed.gov/school/?198419",
)

# ── Published professional-tier tuition (REPAIR_BACKLOG #4 — professional-tier
# starvation behind a 100% bachelor's tier) ─────────────────────────────────
_LAW_TUITION_SRC = (
    "Duke University School of Law — Tuition & Fees 2025-26",
    "https://law.bulletins.duke.edu/policies/tuition",
)
_MED_MD_SRC = (
    "Duke University School of Medicine — M.D. Financial Aid 2025-26",
    "https://medschool.duke.edu/education/health-professions-education-programs/"
    "doctor-medicine-md-program/financial-aid-doctor",
)
_DPT_TUITION_SRC = (
    "Duke Doctor of Physical Therapy — Tuition",
    "https://medschool.duke.edu/education/health-professions-education-programs/"
    "doctor-physical-therapy-program/admissions/tuition",
)
_OTD_TUITION_SRC = (
    "Duke Occupational Therapy Doctorate — Financial Aid 2025-26",
    "https://medschool.duke.edu/education/health-professions-education-programs/"
    "occupational-therapy-doctorate/apply-duke-otd/financial-aid",
)
_DNP_TUITION_SRC = (
    "Duke University School of Nursing — DNP Tuition & Fees 2025-26",
    "https://nursing.duke.edu/academic-programs/dnp-program-nursing/dnp-tuition-fees",
)
_DIVINITY_TUITION_SRC = (
    "Duke Divinity School — Tuition & Financial Aid",
    "https://divinity.duke.edu/admissions/tuition-financial-aid",
)

_LAW_JD_ANNUAL = 83400  # JD (2025-26 bulletin; existing verified rate)
_LAW_JDLLM_ANNUAL = 93450  # JD/LLM dual (2025-26 bulletin)
_MED_MD_ANNUAL = 72297  # fall $36,149 + spring $36,148
_DPT_ANNUAL = 42000
_OTD_ANNUAL = 43000
_DNP_SEMESTER = 16440  # published average DNP tuition per semester
_DNP_ANNUAL = _DNP_SEMESTER * 2  # fall + spring academic year
_CRNA_SEMESTER = 35230  # published average nurse-anesthesia DNP per semester
_CRNA_ANNUAL = _CRNA_SEMESTER * 2
_DMIN_ANNUAL = 31500


def _annual_grad_cost(
    tuition_usd: int,
    *,
    note: str,
    source: str,
    source_url: str,
    year: str = "2025-26",
) -> dict:
    return {
        "tuition_usd": tuition_usd,
        "funded": False,
        "note": note,
        "source": source,
        "source_url": source_url,
        "year": year,
    }


_COST_BY_SLUG: dict[str, dict] = {
    "duke-juris-doctor-jd-prof": _annual_grad_cost(
        _LAW_JD_ANNUAL,
        note=(
            f"Duke Law J.D. academic-year tuition (${_LAW_JD_ANNUAL:,}; 2025-26 "
            "School of Law bulletin)."
        ),
        source=_LAW_TUITION_SRC[0],
        source_url=_LAW_TUITION_SRC[1],
    ),
    "duke-jd-llm-in-international-and-comparative-law-prof": _annual_grad_cost(
        _LAW_JDLLM_ANNUAL,
        note=(
            f"JD/LLM dual-degree academic-year tuition (${_LAW_JDLLM_ANNUAL:,}; "
            "2025-26 School of Law bulletin — higher than the standalone J.D. rate)."
        ),
        source=_LAW_TUITION_SRC[0],
        source_url=_LAW_TUITION_SRC[1],
    ),
    "duke-jd-llm-in-law-and-entrepreneurship-prof": _annual_grad_cost(
        _LAW_JDLLM_ANNUAL,
        note=(
            f"JD/LLM in Law & Entrepreneurship academic-year tuition "
            f"(${_LAW_JDLLM_ANNUAL:,}; 2025-26 School of Law bulletin)."
        ),
        source=_LAW_TUITION_SRC[0],
        source_url=_LAW_TUITION_SRC[1],
    ),
    "duke-doctor-of-medicine-md-prof": _annual_grad_cost(
        _MED_MD_ANNUAL,
        note=(
            f"Duke School of Medicine M.D. tuition (${_MED_MD_ANNUAL:,} per academic "
            "year; fall + spring billing)."
        ),
        source=_MED_MD_SRC[0],
        source_url=_MED_MD_SRC[1],
    ),
    "duke-doctor-of-physical-therapy-dpt-prof": _annual_grad_cost(
        _DPT_ANNUAL,
        note=(
            f"DPT program tuition (${_DPT_ANNUAL:,} per program year; billed in equal "
            "installments across fall, spring, and summer in year one)."
        ),
        source=_DPT_TUITION_SRC[0],
        source_url=_DPT_TUITION_SRC[1],
    ),
    "duke-occupational-therapy-doctorate-otd-prof": _annual_grad_cost(
        _OTD_ANNUAL,
        note=(
            f"OTD program tuition (${_OTD_ANNUAL:,} per program year; fall + spring + "
            "summer billing in year one)."
        ),
        source=_OTD_TUITION_SRC[0],
        source_url=_OTD_TUITION_SRC[1],
    ),
    "duke-doctor-of-nursing-practice-dnp-prof": _annual_grad_cost(
        _DNP_ANNUAL,
        note=(
            f"Average DNP tuition (${_DNP_SEMESTER:,} per fall/spring semester × 2 = "
            f"${_DNP_ANNUAL:,} academic-year tuition; Duke publishes per-credit rates "
            "with this published semester average for a fall start)."
        ),
        source=_DNP_TUITION_SRC[0],
        source_url=_DNP_TUITION_SRC[1],
    ),
    "duke-doctor-of-nursing-practice-nurse-anesthesia-prof": _annual_grad_cost(
        _CRNA_ANNUAL,
        note=(
            f"Average nurse-anesthesia DNP tuition (${_CRNA_SEMESTER:,} per "
            f"fall/spring semester × 2 = ${_CRNA_ANNUAL:,} academic-year tuition)."
        ),
        source=_DNP_TUITION_SRC[0],
        source_url=_DNP_TUITION_SRC[1],
    ),
    "duke-doctor-of-ministry-dmin-prof": _annual_grad_cost(
        _DMIN_ANNUAL,
        note=(
            f"Duke Divinity D.Min. academic-year tuition (${_DMIN_ANNUAL:,}; "
            "hybrid professional doctorate)."
        ),
        source=_DIVINITY_TUITION_SRC[0],
        source_url=_DIVINITY_TUITION_SRC[1],
    ),
}


def _grad_has_verified_tuition(spec: dict) -> bool:
    return spec["slug"] in _COST_BY_SLUG or spec.get("tuition") is not None


def _grad_cost(spec: dict) -> dict | None:
    """A verified per-program graduate cost record, or None when tuition is unverified."""
    tuition = spec.get("tuition")
    if tuition is None:
        return None
    kind = spec.get("tuition_kind")
    label = "annual tuition" if kind == "year" else "total program tuition"
    return {
        "tuition_usd": tuition,
        "tuition_basis": kind,
        "funded": False,
        "note": (
            f"Published {label} from the program's official Duke tuition page "
            "(2025-26 / 2026-27). Many graduate and professional students receive "
            "scholarship or assistantship support; doctoral students are typically funded."
        ),
        "source": "Duke program tuition page",
        "source_url": spec.get("website") or _SCHOOL_WEBSITE.get(spec["school"]),
        "year": "2025-26",
    }


# ── Outcomes ──────────────────────────────────────────────────────────────
# Duke publishes career outcomes college-wide (no per-program employment/industry split),
# so every program carries the institution-wide median earnings as its outcomes record and
# omits the program-level employment_rate / top_industries (recorded in _program_standard).
_OUTCOMES_CONDITIONS = (
    "Institution-wide median earnings of federally aided students measured 10 years after "
    "entry (U.S. Dept. of Education College Scorecard); not a program-specific figure."
)
_OUTCOMES_INSTITUTION = {
    "median_salary": 97800,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry (institution-wide)",
    "conditions": _OUTCOMES_CONDITIONS,
    "source": "U.S. Dept. of Education College Scorecard (Duke, UNITID 198419)",
    "source_url": "https://collegescorecard.ed.gov/school/?198419",
}

# ── Admissions requirement sets ────────────────────────────────────────────
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission.",
}
# Undergraduate (first-year) admission via the Common Application; Duke is test-optional
# for the 2026-27 cycle.
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application", "required": True},
        {"name": "Duke-specific writing supplement", "required": True},
        {"name": "Secondary-school transcript + school report", "required": True},
        {"name": "Counselor recommendation", "required": True},
        {"name": "Two teacher recommendations", "required": True},
        {"name": "$85 application fee; need-based fee waivers available", "required": True},
        {
            "name": "Standardized test scores (SAT/ACT)",
            "required": False,
            "note": "Duke is test-optional for the 2026-27 admissions cycle.",
        },
    ],
    "deadlines": [
        {"round": "Early Decision", "date": "November 3"},
        {"round": "Regular Decision", "date": "January 5"},
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
                "label": "Duke Undergraduate Admissions — Apply",
                "url": "https://admissions.duke.edu/apply/",
            }
        ],
    },
    "source": "Duke Undergraduate Admissions",
    "source_url": "https://admissions.duke.edu/checklist/",
}

# Fuqua Daytime MBA admission.
_REQ_MBA = {
    "materials": [
        {"name": "Fuqua online application", "required": True},
        {"name": "Required essays (including the '25 Random Things' essay)", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Two recommendations", "required": True},
        {"name": "Resume", "required": True},
        {
            "name": "GMAT, GRE or EA scores",
            "required": False,
            "note": "A test waiver is available for qualified applicants.",
        },
        {"name": "Interview (by invitation)", "required": False},
        {"name": "Application fee", "required": True},
    ],
    "deadlines": [
        {"round": "Early Action", "date": "September"},
        {"round": "Round 1", "date": "October"},
        {"round": "Round 2", "date": "January"},
        {"round": "Round 3", "date": "March"},
    ],
    "recommendations": {
        "required": 2,
        "note": "Two recommendations submitted through the Fuqua application.",
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": True,
            "note": "Required for applicants whose first language is not English (waivers apply).",
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Fuqua — Daytime MBA Admissions",
                "url": "https://www.fuqua.duke.edu/programs/daytime-mba/admissions",
            }
        ],
    },
    "source": "The Fuqua School of Business — Daytime MBA Admissions",
    "source_url": "https://www.fuqua.duke.edu/programs/daytime-mba/admissions",
}

# Generic Duke graduate / professional admission set. Each school administers its own
# admissions; the materials below are common, and deadlines vary by program — applicants
# are pointed to the program's own admissions page via the program website.
_REQ_GRAD_GENERIC = {
    "materials": [
        {"name": "Program online application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose / personal statement", "required": True},
        {"name": "Résumé / CV", "required": True},
        {
            "name": "Letters of recommendation",
            "required": True,
            "note": "Most Duke graduate and professional programs require two to three letters.",
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
        "note": "Most Duke graduate and professional programs require three letters (some two).",
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
                "label": "Duke Graduate School — Application Instructions",
                "url": "https://gradschool.duke.edu/admissions/application-instructions/",
            }
        ],
    },
    "source": "Duke graduate & professional admissions",
    "source_url": "https://gradschool.duke.edu/admissions/",
}


def _requirements_for(spec: dict) -> dict:
    """Pick the admissions requirement set for a program by slug / degree type."""
    if spec["slug"] == _FLAGSHIP:
        return dict(_REQ_MBA)
    if spec["degree_type"] == "bachelors":
        return dict(_REQ_UNDERGRAD)
    return dict(_REQ_GRAD_GENERIC)


# ── Flagship + coverable-program depth ─────────────────────────────────────
_FLAGSHIP = "duke-daytime-mba-ms"

# Fuqua Daytime MBA employment-report outcomes (Class of 2025).
_MBA_OUTCOMES: dict = {
    "median_salary": 160000,
    "employment_rate": 0.79,
    "top_industries": [
        {"name": "Consulting", "share": 0.34},
        {"name": "Financial Services", "share": 0.209},
        {"name": "Technology", "share": 0.156},
    ],
    "scope": "program",
    "earnings_timeframe": "median base salary at graduation",
    "conditions": (
        "Fuqua Daytime MBA Class of 2025: median base salary $160,000 and median "
        "signing bonus $30,000; 79% of job seekers accepted offers within three "
        "months of graduation (82.2% received offers). Top industries: consulting "
        "34%, financial services 20.9%, technology 15.6%."
    ),
    "source": "The Fuqua School of Business — Daytime MBA Employment Report 2025",
    "source_url": (
        "https://www.fuqua.duke.edu/sites/default/files/media/programs/daytime/"
        "duke-mba-employment-2025.pdf"
    ),
}

_TRACKS_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "tracks": [
            "Decision Sciences",
            "Marketing",
            "Operations",
            "Strategic Consulting",
            "FinTech",
            "Entrepreneurship & Innovation",
            "Energy & Environment",
            "Leadership & Ethics",
            "Certificate in Finance",
            "Certificate in Health Sector Management (HSM)",
        ],
        "source": "Fuqua School of Business — Daytime MBA Concentrations + Certificates",
        "source_url": (
            "https://www.fuqua.duke.edu/programs/daytime-mba/concentrations-certificates"
        ),
    },
}

_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "cohort_size": "426 students in the entering Daytime MBA class (Class of 2027)",
        "international_pct": 0.35,
        "note": (
            "Entering Daytime MBA Class of 2027: 426 students, 35% international "
            "citizens, 47% women, 5.8 average years of work experience, middle 80% "
            "GMAT range 680–770."
        ),
        "source": "Fuqua School of Business — Daytime MBA Class Profile",
        "source_url": "https://www.fuqua.duke.edu/programs/daytime-mba/class-profile",
    },
}

_FACULTY_BY_SLUG: dict[str, dict] = {}

# Aggregated, cited student-review themes (≥2 third-party sources per coverable program).
_REVIEWS_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "summary": (
            "Students and third-party guides describe Fuqua's Daytime MBA as a "
            "STEM-designated, team-based program built on the 'Team Fuqua' culture — "
            "collaborative rather than cutthroat — with strong finance and consulting "
            "placement (Class of 2025 median base salary $160,000). Common cautions are "
            "that the brand footprint trails M7 peers, Durham's location is less central "
            "than coastal MBA hubs, and the intensive mini-term pace demands heavy "
            "teamwork from day one."
        ),
        "themes": [
            {
                "label": "Team Fuqua culture",
                "sentiment": "positive",
                "detail": (
                    "Collaborative, values-driven community with six Defining Principles "
                    "and team-based learning."
                ),
            },
            {
                "label": "Finance & consulting outcomes",
                "sentiment": "positive",
                "detail": (
                    "Class of 2025: $160K median base; financial services and consulting "
                    "are top destinations."
                ),
            },
            {
                "label": "STEM designation",
                "sentiment": "positive",
                "detail": (
                    "The full Daytime MBA carries an official STEM designation, extending "
                    "OPT for eligible international graduates."
                ),
            },
            {
                "label": "Brand vs. M7 peers",
                "sentiment": "mixed",
                "detail": (
                    "Strong outcomes but a smaller national MBA brand than M7 schools "
                    "in some markets."
                ),
            },
            {
                "label": "Pace & location",
                "sentiment": "caution",
                "detail": (
                    "Six-week terms move quickly; Durham is livable but not a major "
                    "finance/consulting hub."
                ),
            },
        ],
        "sources": [
            {
                "label": "Fuqua — Daytime MBA Employment Report 2025",
                "url": (
                    "https://www.fuqua.duke.edu/sites/default/files/media/programs/"
                    "daytime/duke-mba-employment-2025.pdf"
                ),
            },
            {
                "label": "Poets&Quants — Meet Duke Fuqua's MBA Class Of 2027",
                "url": (
                    "https://poetsandquants.com/2025/12/06/meet-duke-fuquas-mba-class-of-2027/"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "duke-computer-science-ab": {
        "summary": (
            "Students and guides describe Duke's computer science major as rigorous and "
            "research-oriented — Niche ranks it #15 nationally for CS (2026) and the "
            "department notes a U.S. News graduate ranking of #20 — with flexible "
            "B.S./B.A. paths and concentrations in AI, data science, and software "
            "systems. Common cautions are competitive grading, large introductory "
            "lectures, and a smaller CS cohort than peer giants like CMU or MIT."
        ),
        "themes": [
            {
                "label": "Research depth",
                "sentiment": "positive",
                "detail": (
                    "Interdisciplinary research in AI, systems, and computational biology "
                    "with strong faculty."
                ),
            },
            {
                "label": "Flexible degree paths",
                "sentiment": "positive",
                "detail": (
                    "B.S., B.A., and interdepartmental majors plus AI/data-science concentrations."
                ),
            },
            {
                "label": "National CS standing",
                "sentiment": "positive",
                "detail": (
                    "Niche #15 for undergraduate CS; graduate program ranked #20 by U.S. News."
                ),
            },
            {
                "label": "Competitive atmosphere",
                "sentiment": "caution",
                "detail": (
                    "Selective major with demanding coursework and pre-professional pressure."
                ),
            },
        ],
        "sources": [
            {
                "label": "Niche — Best Colleges for Computer Science",
                "url": "https://www.niche.com/colleges/search/best-colleges-for-computer-science/",
            },
            {
                "label": "Duke CS — About the Department",
                "url": "https://cs.duke.edu/about",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "duke-juris-doctor-jd-prof": {
        "summary": (
            "Students and third-party guides describe Duke Law as a rigorous top-tier "
            "program — U.S. News ranked it #7 nationally in 2026 — with strong clinical "
            "offerings, accessible faculty, and excellent Big Law and clerkship "
            "placement (97.5% bar passage among takers). Common cautions are high tuition, "
            "graded legal-writing pressure, and a competitive admissions pool (12.9% "
            "acceptance rate)."
        ),
        "themes": [
            {
                "label": "Top-tier national rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Duke Law #7 nationally (2026).",
            },
            {
                "label": "Clinical & writing skills",
                "sentiment": "positive",
                "detail": (
                    "Experiential clinics and a graded legal-writing program build "
                    "practical skills."
                ),
            },
            {
                "label": "Collegial community",
                "sentiment": "positive",
                "detail": (
                    "Small class size and non-competitive grading foster collaboration "
                    "(Princeton Review student surveys)."
                ),
            },
            {
                "label": "Cost & selectivity",
                "sentiment": "caution",
                "detail": (
                    "High tuition and a 12.9% acceptance rate make admission and "
                    "financing demanding."
                ),
            },
        ],
        "sources": [
            {
                "label": "Above the Law — 2026 U.S. News Law Rankings",
                "url": (
                    "https://davidlat.substack.com/p/"
                    "2026-us-news-law-school-rankings-stanford-new-number-one-over-yale"
                ),
            },
            {
                "label": "The Princeton Review — Duke Law student surveys",
                "url": "https://www.princetonreview.com/law/duke-university-school-law-1035810",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "duke-doctor-of-medicine-md-prof": {
        "summary": (
            "Applicants and guides describe Duke's School of Medicine as a top-tier "
            "research medical school — U.S. News ranks Duke #6 for research in 2025 — "
            "with an innovative curriculum, strong clinical training at Duke University "
            "Hospital, and interdisciplinary research through the Duke Clinical Research "
            "Institute. Common cautions are extremely competitive admission, high cost of "
            "attendance, and the intensity of the four-year professional curriculum."
        ),
        "themes": [
            {
                "label": "Top research ranking",
                "sentiment": "positive",
                "detail": "U.S. News ranks Duke #6 among medical schools for research (2025).",
            },
            {
                "label": "Clinical & research integration",
                "sentiment": "positive",
                "detail": (
                    "Duke University Hospital and DCRI provide hands-on clinical and "
                    "research training."
                ),
            },
            {
                "label": "Innovative curriculum",
                "sentiment": "positive",
                "detail": ("Patient-first, team-based curriculum with early clinical exposure."),
            },
            {
                "label": "Selectivity & cost",
                "sentiment": "caution",
                "detail": (
                    "Highly selective admission with substantial tuition and living "
                    "expenses in Durham."
                ),
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Best Medical Schools: Research",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/research-rankings",
            },
            {
                "label": "Duke University School of Medicine — About",
                "url": "https://medschool.duke.edu/about",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "duke-master-of-public-policy-mpp-ms": {
        "summary": (
            "Students and guides describe Duke's Sanford MPP as a quantitative, "
            "policy-analytic program with strong faculty in economics, health, and "
            "environmental policy and placement in government, consulting, and "
            "nonprofits. Common cautions are a smaller cohort than peer MPP programs "
            "at Harvard or Princeton, limited DC proximity compared with Georgetown, "
            "and the quantitative rigor of the core curriculum."
        ),
        "themes": [
            {
                "label": "Quantitative policy training",
                "sentiment": "positive",
                "detail": (
                    "Econometrics and data-driven policy analysis are core to the two-year MPP."
                ),
            },
            {
                "label": "Interdisciplinary faculty",
                "sentiment": "positive",
                "detail": (
                    "Strength in health, environment, and development policy with "
                    "Duke research centers."
                ),
            },
            {
                "label": "Career versatility",
                "sentiment": "positive",
                "detail": (
                    "Graduates enter federal/state government, consulting, and "
                    "international organizations."
                ),
            },
            {
                "label": "Cohort size & location",
                "sentiment": "mixed",
                "detail": (
                    "Smaller program than some peer MPPs; Durham is not adjacent to "
                    "Washington, D.C."
                ),
            },
        ],
        "sources": [
            {
                "label": "Sanford School of Public Policy — Master of Public Policy",
                "url": "https://sanford.duke.edu/master-public-policy",
            },
            {
                "label": "Niche — Duke University reviews",
                "url": "https://www.niche.com/colleges/duke-university/reviews/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "duke-economics-ab": {
        "summary": (
            "Students and guides describe Duke's economics major as rigorous and "
            "quantitatively demanding, with strong faculty in micro, macro, and "
            "econometrics and excellent placement in finance, consulting, and graduate "
            "programs. Common cautions are large intermediate courses, competitive "
            "grading relative to some peer departments, and the need to self-direct "
            "research opportunities beyond the core."
        ),
        "themes": [
            {
                "label": "Quantitative rigor",
                "sentiment": "positive",
                "detail": (
                    "Strong econometrics and theory sequence prepares students for "
                    "graduate study and finance."
                ),
            },
            {
                "label": "Career placement",
                "sentiment": "positive",
                "detail": (
                    "Graduates enter investment banking, consulting, and top Ph.D. programs."
                ),
            },
            {
                "label": "Faculty depth",
                "sentiment": "positive",
                "detail": (
                    "Research-active faculty in applied micro, development, and "
                    "financial economics."
                ),
            },
            {
                "label": "Course scale",
                "sentiment": "caution",
                "detail": (
                    "Large intermediate lectures can feel impersonal before students "
                    "reach seminars."
                ),
            },
        ],
        "sources": [
            {
                "label": "Duke Department of Economics — Undergraduate",
                "url": "https://econ.duke.edu/undergraduate",
            },
            {
                "label": "Niche — Duke University reviews",
                "url": "https://www.niche.com/colleges/duke-university/reviews/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "duke-electrical-and-computer-engineering-bse": {
        "summary": (
            "Students and guides describe Duke's ECE major as rigorous and "
            "research-oriented within Pratt, with strengths in signal processing, "
            "computer engineering, and photonics and strong placement in tech and "
            "graduate programs. Common cautions are demanding prerequisites, limited "
            "course flexibility in the first two years, and a smaller engineering "
            "community than large public tech schools."
        ),
        "themes": [
            {
                "label": "Research & lab access",
                "sentiment": "positive",
                "detail": (
                    "Undergraduates can join labs in photonics, AI hardware, and "
                    "biomedical devices."
                ),
            },
            {
                "label": "Tech placement",
                "sentiment": "positive",
                "detail": (
                    "Graduates enter semiconductor, software, and consulting roles at major firms."
                ),
            },
            {
                "label": "Pratt integration",
                "sentiment": "positive",
                "detail": (
                    "Small engineering school with close faculty access on a research "
                    "university campus."
                ),
            },
            {
                "label": "Curriculum rigidity",
                "sentiment": "caution",
                "detail": ("Structured core limits early electives; prerequisites are demanding."),
            },
        ],
        "sources": [
            {
                "label": "Pratt School of Engineering — ECE",
                "url": "https://ece.duke.edu/undergrad",
            },
            {
                "label": "Niche — Duke University reviews",
                "url": "https://www.niche.com/colleges/duke-university/reviews/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "duke-public-policy-studies-ab": {
        "summary": (
            "Students describe Duke's public policy studies major (Sanford) as an "
            "interdisciplinary, analytically rigorous program bridging economics, "
            "political science, and ethics with strong internship placement in "
            "government and nonprofits. Common cautions are that the major is smaller "
            "than economics or political science alone, course offerings can be "
            "limited in niche subfields, and pre-professional students may need to "
            "supplement with quantitative coursework."
        ),
        "themes": [
            {
                "label": "Interdisciplinary breadth",
                "sentiment": "positive",
                "detail": (
                    "Combines economics, politics, and ethics for policy analysis across sectors."
                ),
            },
            {
                "label": "Sanford connection",
                "sentiment": "positive",
                "detail": ("Access to Sanford faculty, research centers, and policy internships."),
            },
            {
                "label": "Internship placement",
                "sentiment": "positive",
                "detail": (
                    "Students intern in federal/state government, NGOs, and research organizations."
                ),
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": (
                    "Smaller major with fewer specialized electives than standalone departments."
                ),
            },
        ],
        "sources": [
            {
                "label": "Sanford School — Public Policy Studies (Trinity)",
                "url": "https://sanford.duke.edu/academics/undergraduate/public-policy-studies",
            },
            {
                "label": "Niche — Duke University reviews",
                "url": "https://www.niche.com/colleges/duke-university/reviews/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    **DEPTH_REVIEWS,
}


# Real Duke campus photo (Duke Chapel) — Wikimedia Commons landscape JPG (verified HTTP
# 200). Leads the institution hero; see ``SCHOOL_OUTCOMES["campus_photos"]`` for gallery.
_CAMPUS_PHOTO = SCHOOL_OUTCOMES["campus_photos"][0]["url"]


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich Duke to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Duke is absent — safe on fresh/CI databases.
    """
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
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
    inst.founded_year = 1838
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.duke.edu"
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
        # Every school gets a working feed (verified Duke Today tag RSS + the Duke events
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


def _program_standard(slug: str, spec: dict | None = None) -> dict:
    """Per-program omitted-field list (verified-unavailable), for _standard."""
    if spec is None:
        spec = _SPEC_BY_SLUG.get(slug, {})
    omitted: list[str] = []
    # Duke publishes no per-program employment report or industry breakdown (its first-
    # destination data is reported college-wide, captured at the institution level), so
    # every program except the Fuqua Daytime MBA omits the program-level employment rate
    # and top industries.
    if slug != _FLAGSHIP:
        omitted += [
            "outcomes_data.employment_rate",
            "outcomes_data.top_industries",
        ]
    # Graduate/professional programs without a verified per-program tuition omit tuition_usd
    # (their cost_data carries a sourced "see the school's tuition page" record instead).
    if spec.get("degree_type") != "bachelors" and not _grad_has_verified_tuition(spec):
        omitted.append("cost_data.tuition_usd")
    if slug not in _TRACKS_BY_SLUG:
        omitted.append("tracks")
    if slug not in _CLASS_PROFILE_BY_SLUG:
        omitted.append("class_profile.cohort_size")
    if slug not in _FACULTY_BY_SLUG:
        omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    # content_sources is set on every program (school feed + program keywords), never omitted.
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
        p.program_name = spec["program_name"]
        p.degree_type = spec["degree_type"]
        p.department = spec.get("department")
        p.duration_months = spec.get("duration_months")
        p.description_text = spec["description"]
        p.website_url = _WEBSITE_BY_SLUG.get(slug) or _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "in_person")
        _kw = _PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(
            _SCHOOL_FEED_SPEC[spec["school"]]["keywords"]
        )
        p.content_sources = _program_content(spec["school"], _kw)
        # Cost precedence: published Duke College rates for bachelor's majors → a verified
        # per-program graduate tuition → a sourced "see the school page" record (tuition_usd
        # recorded omitted, never guessed and never set to the undergraduate rate).
        if spec["degree_type"] == "bachelors":
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
                    "Published 2025-26 Duke undergraduate tuition with the Board of "
                    "Trustees cost of attendance and the College Scorecard average net "
                    "price. Duke meets 100% of demonstrated financial need, so most "
                    "families pay far less than the sticker price (average net price "
                    "≈ $30,000)."
                ),
                "source": _COST_SRC[0],
                "source_url": _COST_SRC[1],
                "year": "2025-26",
            }
        else:
            cost_override = _COST_BY_SLUG.get(slug)
            grad_cost = cost_override or _grad_cost(spec)
            if grad_cost is not None:
                p.tuition = grad_cost["tuition_usd"]
                p.cost_data = grad_cost
            else:
                p.tuition = None
                p.cost_data = {
                    "note": (
                        "Tuition for this graduate/professional program varies and is "
                        "published on the school's official tuition page; a verified "
                        "per-program figure is not yet recorded here."
                    ),
                    "source": "Duke University — program tuition page",
                    "source_url": spec.get("website") or _SCHOOL_WEBSITE.get(spec["school"]),
                }
        p.application_requirements = _requirements_for(spec)
        if slug == _FLAGSHIP:
            outcomes = dict(_MBA_OUTCOMES)
        else:
            outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        p.who_its_for = None
        p.highlights = None
        p.application_deadline = date(2027, 1, 5) if spec["degree_type"] == "bachelors" else None
        if slug == _FLAGSHIP:
            p.application_deadline = date(2027, 1, 5)
    session.flush()
    # Reconcile legacy Duke programs (slug not in the canonical set): delete when
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
