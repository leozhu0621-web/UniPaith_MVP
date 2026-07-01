"""University of Washington (Seattle) — gold-standard profile data
(institution + schools + program catalog).

Mirrors the MIT / Sloan / MBAn reference instance (see ``mit_profile.py`` /
``uiuc_profile.py``): every value is researched from an authoritative source and
carries a citation, or is honestly omitted (recorded in that node's
``_standard.omitted``) — never guessed. Built 2026-06-13 from:

  * U.S. Dept. of Education **College Scorecard** API + **IPEDS** (UNITID 236948):
    admit rate, average net price, cost of attendance, ten-year median earnings,
    six-year completion, first-year retention, Pell/loan rates, median debt,
    endowment, undergraduate race/ethnicity. UW is test-blind, so SAT/ACT test
    scores are omitted with reason.
  * **UW Office of Planning & Budgeting (OPB) Fast Facts** and the UW Common Data
    Set 2024-2025: the Fall 2024 first-year admissions funnel (69,166 applicants /
    27,076 admitted / 7,196 enrolled), Seattle-campus enrollment (52,316 total;
    36,023 undergraduates), and the 20:1 student-faculty ratio.
  * Rankings: **U.S. News Best Colleges 2026** (#42 National, #16 public), **QS
    2026** (#81), **Times Higher Education 2026** (#25), Carnegie R1, and Northwest
    Commission on Colleges and Universities (NWCCU) accreditation, each cited.
  * The official **UW General Catalog** (washington.edu/students/gencat): the full
    published degree catalog parsed from the college/school program indexes across
    UW Seattle's 16 degree-granting colleges/schools and the interdisciplinary
    Graduate School, plus the professional Doctor of Medicine, Doctor of Dental
    Surgery, Juris Doctor, Doctor of Pharmacy, Doctor of Nursing Practice, Doctor
    of Physical Therapy, and Doctor of Audiology, and UW's online degrees delivered
    through UW Professional & Continuing Education (carrying
    ``delivery_format = "online"``). Minors, certificates, options/concentrations,
    and combined-degree listings are excluded.
  * UW leadership pages (washington.edu/leadership) for each college/school dean,
    and a verified 5-photo Wikimedia Commons campus gallery (author + license
    confirmed via the Commons API).
  * Verified third-party coverage + official rankings for flagship coverable
    programs (computer science, the MD/WWAMI, the DNP, the iSchool MLIS, the Foster
    MBA, the JD, the PharmD, the MSW, bioengineering, aeronautics & astronautics,
    civil engineering, statistics, economics, and oceanography).

Honest caveats stamped into ``_standard.omitted``: UW is test-blind (it does not
consider SAT/ACT in admission), so institution ``test_scores`` is omitted. UW
reports tri-campus academic staff rather than a single Seattle instructional-
faculty headcount, so ``scale.faculty_count`` is omitted (the 20:1 student-faculty
ratio is kept). UW does not publish a single university-wide placement rate or a
uniform top-employer-industries list across all colleges, so those two institution
outcome fields are omitted (the Scorecard ten-year median earnings is kept).

Matcher-core fields (2026-06-25 repair — REPAIR_BACKLOG #1 cip_code + #2 public scalar):
1. ``cip_code`` — every program now carries its NCES CIP-2020 4-digit code (``_CIP_BY_FIELD``),
   the CIP join key the CPEF matcher uses to resolve a program's field to ref_majors + the
   field-66 vocabulary; the prior null left the whole catalog field-blind for the matcher.
2. ``tuition`` — UW is PUBLIC, so the matcher's flat ``program.tuition`` scalar now carries the
   NON-RESIDENT (out-of-state) annual sticker per tier, because the CPEF budget breaker reads
   that scalar for EVERY student and the out-of-state + ALL-international pool (the flagship
   majority) was being scored 2.5–3.5× too cheap on the resident rate. The editorial
   ``cost_data`` stays on the coherent WA-RESIDENT basis (``tuition_usd`` = resident, matching the
   Scorecard resident COA / net price), with BOTH ``tuition_in_state`` and ``tuition_out_of_state``
   always in ``cost_data.breakdown`` (honest + sourced) — only the matcher scalar uses non-resident.
   Bachelor's
   carry the non-resident undergraduate sticker ($44,460; resident $13,406); master's and PhD
   carry the non-resident graduate Tier I sticker ($33,171; resident $19,011 — UW charges one
   flat graduate operating fee per residency), and a funded research PhD keeps the published
   sticker because funding is a separate matcher signal, not a $0 budget. The bespoke professional
   schools carry their own published non-resident annual rates (Law $58,956, Medicine $102,319,
   Dentistry $84,926, Pharmacy $51,582 [2026-27], DNP $50,037, DPT $43,461). The 14 fee-based /
   self-sustaining programs (2026-07-01 repair — REPAIR_BACKLOG #1 matcher-core coverage) now carry
   their OWN published, residency-independent per-credit rate (``_FEE_BASED_TUITION``), annualized
   over the program's length — a real figure exists and is knowable, so omit-never-guess requires it
   (e.g. MSME $1,330/cr × 42 = $55,860, MSIM $1,132/cr × 65 = $73,580, MHA $950/cr × 76 = $72,200).
   Only two programs keep ``cost_data.tuition_usd`` omitted-with-reason rather than a wrong value:
   the Doctor of Audiology (bills on UW's variable graduate-tier schedule, no single published annual
   figure) and the online BA in Integrated Social Sciences (a per-credit degree-completion program
   with no fixed credits-to-degree total). Tuition sources: UW OPB 2025-26 Seattle quarterly tuition
   & fees PDF + each professional school's published cost page + each fee-based program's own cost
   page (resident figures verified against the prior repair).

    This repair (2026-06-20) replaces generic Wikipedia field definitions and credential-
    frame shared bodies with UW-specific field clauses (``uw_field_descriptions.py``),
    distinct per-credential sibling bodies (``frame_stripped_shared_body`` = 0), and
    collapsed Education PhD concentration splits into ``tracks`` on ``uw-education-phd``.
"""

# ruff: noqa: E501

from __future__ import annotations

import re
from collections import Counter, defaultdict

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.profile_catalog_utils import validate_catalog
from unipaith.data.uw_field_descriptions import (
    FIELD_DESCRIPTIONS,
    FIELD_FOCUS,
    SLUG_DESCRIPTIONS,
)
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION
from unipaith.profile_standard.anti_stub import analyze as _anti_stub_analyze
from unipaith.profile_standard.anti_stub import field_of as _anti_stub_field
from unipaith.profile_standard.anti_stub import frame_stripped_shared_body

INSTITUTION_NAME = "University of Washington-Seattle Campus"
ENRICHED_AT = "2026-07-01"


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


# UW is test-blind; reports tri-campus staff (no single Seattle faculty headcount);
# and reports outcomes by college, not as one university-wide placement rate or
# top-employer-industries list.
_OMITTED_INSTITUTION: list[str] = [
    "school_outcomes.test_scores",
    "school_outcomes.scale.faculty_count",
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
]

RANKING_DATA: dict = {
    "ownership_type": "public",
    "accreditor": "Northwest Commission on Colleges and Universities (NWCCU)",
    "carnegie_classification": (
        "Doctoral Universities: Very High Research Spending and Doctorate Production (R1)"
    ),
    "qs_world_university_rankings": {
        "rank": 81,
        "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/university-washington",
    },
    "times_higher_education": {
        "rank": 25,
        "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-washington",
    },
    "us_news_national": {
        "rank": 42,
        "year": 2026,
        "source_url": "https://www.usnews.com/best-colleges/university-of-washington-3798",
    },
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.3915,
    "avg_net_price": 14091,
    "median_earnings_10yr": 78466,
    "graduation_rate_6yr": 0.8518,
    "completion_rate_4yr_150pct": 0.8518,
    "retention_rate_first_year": 0.9482,
    "financial_aid": {
        "pell_grant_rate": 0.1486,
        "federal_loan_rate": 0.1489,
        "median_debt_completers": 14615,
        "cost_of_attendance": 32446,
        "avg_net_price": 14091,
    },
    "demographics": {
        "white": 0.3319,
        "asian": 0.2742,
        "hispanic": 0.1032,
        "black": 0.0433,
        "two_or_more": 0.0821,
        "american_indian": 0.0033,
        "pacific_islander": 0.0034,
        "international": 0.1173,
        "unknown": 0.0414,
        "women": 0.5664,
    },
    "campus_basics": {"location": "Seattle, Washington"},
    "scale": {
        "student_faculty_ratio": "20:1",
        "endowment_usd": 5343000000,
    },
    "location": {"lat": 47.6553, "lng": -122.3035},
    "research": {
        "labs": [
            "Applied Physics Laboratory (APL-UW)",
            "Institute for Health Metrics and Evaluation (IHME)",
            "Institute for Protein Design (IPD)",
            "eScience Institute",
            "Washington National Primate Research Center",
            "Friday Harbor Laboratories",
        ],
        "areas": [
            "Global health, health metrics, and biomedical research",
            "Computer science, artificial intelligence, and data science",
            "Protein design, genome sciences, and bioengineering",
            "Oceanography, atmospheric, and earth sciences",
            "Aerospace, clean energy, and advanced materials",
        ],
        "lab_links": {
            "Applied Physics Laboratory (APL-UW)": "https://www.apl.washington.edu/",
            "Institute for Health Metrics and Evaluation (IHME)": "https://www.healthdata.org/",
            "Institute for Protein Design (IPD)": "https://www.ipd.uw.edu/",
            "eScience Institute": "https://escience.washington.edu/",
            "Washington National Primate Research Center": "https://wanprc.uw.edu/",
            "Friday Harbor Laboratories": "https://fhl.uw.edu/",
        },
    },
    "campus_life": {
        "athletics_division": "NCAA Division I (Big Ten Conference)",
        "resources": [
            {"name": "Washington Huskies Athletics", "url": "https://gohuskies.com/"},
            {
                "name": "University of Washington Libraries",
                "url": "https://www.lib.washington.edu/",
            },
            {"name": "Henry Art Gallery", "url": "https://henryart.org/"},
            {
                "name": "Burke Museum of Natural History and Culture",
                "url": "https://www.burkemuseum.org/",
            },
            {"name": "UW Recreation", "url": "https://www.washington.edu/ima/"},
            {"name": "Meany Center for the Performing Arts", "url": "https://meanycenter.org/"},
        ],
    },
    "media_credit": "Wikimedia Commons / Martin Kraft (CC BY-SA 3.0)",
    "campus_photos": [
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/MK03214_University_of_Washington_Suzzallo_Library.jpg/1920px-MK03214_University_of_Washington_Suzzallo_Library.jpg",
            "credit": "Wikimedia Commons / Martin Kraft (CC BY-SA 3.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/MK03244_University_of_Washington_Drumheller_Fountain.jpg/1920px-MK03244_University_of_Washington_Drumheller_Fountain.jpg",
            "credit": "Wikimedia Commons / Martin Kraft (CC BY-SA 3.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/be/UW_Red_Square.jpg/1920px-UW_Red_Square.jpg",
            "credit": "Wikimedia Commons / Yihang Sun (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/University_of_Washington_Quad_cherry_blossoms_2017_-_03.jpg/1920px-University_of_Washington_Quad_cherry_blossoms_2017_-_03.jpg",
            "credit": "Wikimedia Commons / Joe Mabel (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Rainier_Vista_late_on_a_sunny_November_afternoon.jpg/1920px-Rainier_Vista_late_on_a_sunny_November_afternoon.jpg",
            "credit": "Wikimedia Commons / Joe Mabel (CC BY-SA 4.0)",
        },
    ],
    "flagship": {
        "enrollment_total": 52316,
        "applicants": 69166,
        "admits": 27076,
        "admissions_cycle": "First-year, Fall 2024 (UW Common Data Set 2024-2025)",
        "founded_year": 1861,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (UW, UNITID 236948)",
            "url": "https://collegescorecard.ed.gov/school/?236948-University-of-Washington-Seattle-Campus",
        },
        {
            "label": "NCES College Navigator — University of Washington-Seattle Campus (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=236948",
        },
        {
            "label": "UW Office of Planning & Budgeting — Fast Facts (enrollment, ratio)",
            "url": "https://www.washington.edu/opb/uw-data/fast-facts/",
        },
        {
            "label": "UW Common Data Set 2024-2025 (admissions funnel, enrollment)",
            "url": "https://www.washington.edu/opb/uw-data/common-data-set/",
        },
        {
            "label": "Carnegie Classifications — University of Washington (R1)",
            "url": "https://carnegieclassifications.acenet.edu/institution/university-of-washington-seattle-campus/",
        },
        {
            "label": "NWCCU — University of Washington (accreditation)",
            "url": "https://nwccu.org/member-institutions/university-of-washington/",
        },
        {
            "label": "QS World University Rankings 2026 — University of Washington (#81)",
            "url": "https://www.topuniversities.com/universities/university-washington",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — University of Washington (#25)",
            "url": "https://www.timeshighereducation.com/world-university-rankings/university-washington",
        },
        {
            "label": "U.S. News Best Colleges 2026 — University of Washington (#42 National, #16 public)",
            "url": "https://www.usnews.com/best-colleges/university-of-washington-3798",
        },
        {
            "label": "UW General Catalog — degree programs",
            "url": "https://www.washington.edu/students/gencat/degree_programs.html",
        },
        {
            "label": "UW leadership (deans of colleges and schools)",
            "url": "https://www.washington.edu/leadership/",
        },
    ],
}

# student_body_size = Seattle-campus undergraduate enrollment (UW OPB Fall 2024);
# total degree-seeking enrollment (52,316) lives in flagship.enrollment_total.
UNDERGRAD_COUNT = 36023

DESCRIPTION = (
    "The University of Washington is a public research university in Seattle, WA. Founded in 1861, "
    "it is the flagship of the University of Washington system, a founding member of the Association "
    "of American Universities, and one of the world's leading public research universities by funded "
    "research volume. Its Seattle campus enrolled 52,316 students in Fall 2024 — about 36,023 "
    "undergraduates and roughly 16,000 graduate and professional students — with a 20:1 student-"
    "faculty ratio. For Fall 2024 it admitted about 39.2% of first-year applicants (27,076 of "
    "69,166). UW practices test-blind admission and does not consider SAT/ACT scores.\n\n"
    "UW is organized into 16 degree-granting colleges and schools, including the College of Arts and "
    "Sciences, the College of Engineering (home to the Paul G. Allen School of Computer Science & "
    "Engineering), the Michael G. Foster School of Business, the School of Medicine, the School of "
    "Nursing, the School of Public Health, the Information School, the College of the Environment, "
    "and the Daniel J. Evans School of Public Policy and Governance, plus an interdisciplinary "
    "Graduate School. Together they offer hundreds of degree programs across the bachelor's, "
    "master's, professional, and doctoral levels — including the Doctor of Medicine, Doctor of "
    "Dental Surgery, Juris Doctor, Doctor of Pharmacy, Doctor of Nursing Practice, Doctor of "
    "Physical Therapy, and Doctor of Audiology, and online degrees delivered through UW Professional "
    "& Continuing Education.\n\n"
    "A Carnegie R1 university accredited by the Northwest Commission on Colleges and Universities, "
    "UW ranks #42 among national universities (and #16 among public universities) by U.S. News, #25 "
    "in the world by Times Higher Education, and #81 by QS for 2026. The UW School of Medicine is "
    "ranked #1 in the nation for primary care, family medicine, and rural medicine, anchored by the "
    "five-state WWAMI program; the iSchool's library and information studies and the School of "
    "Nursing's DNP rank among the nation's best; and computer science ranks among the top programs "
    "nationally. Research is anchored by the Applied Physics Laboratory, the Institute for Health "
    "Metrics and Evaluation, the Institute for Protein Design, and the eScience Institute.\n\n"
    "UW's published cost of attendance is about $32,446 a year, but its average net price after grant "
    "aid is about $14,091 and the median federal debt of completers is about $14,615; in-state "
    "students benefit from public tuition. UW graduates earn a median of roughly $78,466 ten years "
    "after entry. The Washington Huskies compete in NCAA Division I in the Big Ten Conference."
)

# == Schools (16 degree-granting colleges/schools + interdisciplinary Graduate School) ==
_SCHOOL_META = [
    {
        "key": "ARTSCI",
        "name": "College of Arts and Sciences",
        "sort_order": 1,
        "website": "https://artsci.uw.edu/",
        "leadership": "Dianne Harris — Dean",
        "research_centers": [
            "Division of the Arts",
            "Division of the Humanities",
            "Division of the Natural Sciences",
            "Division of the Social Sciences",
            "Paul G. Allen School of Computer Science & Engineering (CS undergraduate major)",
        ],
        "keywords": ["College of Arts and Sciences", "Arts and Sciences", "liberal arts"],
    },
    {
        "key": "BUILT",
        "name": "College of Built Environments",
        "sort_order": 2,
        "website": "https://be.uw.edu/",
        "leadership": "Ken P. Yocom — Dean",
        "research_centers": [
            "Department of Architecture",
            "Department of Construction Management",
            "Department of Landscape Architecture",
            "Department of Real Estate",
            "Department of Urban Design & Planning",
        ],
        "keywords": [
            "College of Built Environments",
            "built environments",
            "architecture",
            "urban planning",
        ],
    },
    {
        "key": "BUS",
        "name": "Michael G. Foster School of Business",
        "sort_order": 3,
        "website": "https://foster.uw.edu/",
        "leadership": "Frank Hodge — Dean",
        "research_centers": [
            "Department of Accounting",
            "Department of Finance & Business Economics",
            "Department of Marketing & International Business",
            "Department of Information Systems & Operations Management",
            "Department of Management & Organization",
        ],
        "keywords": ["Foster School of Business", "Foster", "business", "MBA"],
    },
    {
        "key": "DENT",
        "name": "School of Dentistry",
        "sort_order": 4,
        "website": "https://dental.washington.edu/",
        "leadership": "André V. Ritter — Dean",
        "research_centers": [
            "Doctor of Dental Surgery (DDS) program",
            "Department of Oral Health Sciences",
            "Graduate specialty programs (orthodontics, periodontics, prosthodontics, endodontics)",
        ],
        "keywords": ["School of Dentistry", "dentistry", "DDS", "dental"],
    },
    {
        "key": "EDUC",
        "name": "College of Education",
        "sort_order": 5,
        "website": "https://education.uw.edu/",
        "leadership": "Mia Tuan — Dean",
        "research_centers": [
            "Area of Curriculum & Instruction",
            "Area of Educational Leadership & Policy Studies",
            "Area of Learning Sciences & Human Development",
            "Area of Measurement & Statistics",
            "Area of School Psychology",
            "Area of Special Education",
        ],
        "keywords": ["College of Education", "education", "teaching"],
    },
    {
        "key": "ENGR",
        "name": "College of Engineering",
        "sort_order": 6,
        "website": "https://www.engr.uw.edu/",
        "leadership": "Nancy Allbritton — Dean",
        "research_centers": [
            "Paul G. Allen School of Computer Science & Engineering",
            "Department of Electrical & Computer Engineering",
            "Department of Mechanical Engineering",
            "William E. Boeing Department of Aeronautics & Astronautics",
            "Department of Civil & Environmental Engineering",
            "Department of Bioengineering",
            "Department of Materials Science & Engineering",
        ],
        "keywords": ["College of Engineering", "engineering", "computer science", "Allen School"],
    },
    {
        "key": "ENV",
        "name": "College of the Environment",
        "sort_order": 7,
        "website": "https://environment.uw.edu/",
        "leadership": "Joel Thornton — Interim Dean",
        "research_centers": [
            "School of Oceanography",
            "School of Aquatic & Fishery Sciences",
            "School of Environmental & Forest Sciences",
            "Department of Atmospheric & Climate Science",
            "Department of Earth & Space Sciences",
        ],
        "keywords": ["College of the Environment", "environment", "oceanography", "earth sciences"],
    },
    {
        "key": "ISCHOOL",
        "name": "The Information School",
        "sort_order": 8,
        "website": "https://ischool.uw.edu/",
        "leadership": "Anind Dey — Dean",
        "research_centers": [
            "Master of Library & Information Science (MLIS)",
            "Master of Science in Information Management (MSIM)",
            "Informatics undergraduate program",
            "Ph.D. in Information Science",
        ],
        "keywords": [
            "The Information School",
            "iSchool",
            "information science",
            "library and information science",
        ],
    },
    {
        "key": "GRAD",
        "name": "The Graduate School",
        "sort_order": 9,
        "website": "https://grad.uw.edu/",
        "leadership": "Joy Williamson-Lott — Dean",
        "research_centers": [
            "Interdisciplinary graduate degree programs",
            "Molecular Engineering & Sciences",
            "Neuroscience",
            "Molecular & Cellular Biology",
            "Data Science",
            "Individual PhD Program",
        ],
        "keywords": ["Graduate School", "interdisciplinary", "graduate program"],
    },
    {
        "key": "LAW",
        "name": "School of Law",
        "sort_order": 10,
        "website": "https://www.law.uw.edu/",
        "leadership": "Tamara F. Lawson — Dean",
        "research_centers": [
            "Juris Doctor (J.D.) program",
            "Master of Laws (LL.M.) program",
            "Master of Jurisprudence program",
            "Ph.D. in Law program",
        ],
        "keywords": ["School of Law", "law", "J.D.", "Juris Doctor"],
    },
    {
        "key": "MED",
        "name": "School of Medicine",
        "sort_order": 11,
        "website": "https://www.uwmedicine.org/school-of-medicine",
        "leadership": "Timothy H. Dellit — Dean",
        "research_centers": [
            "Doctor of Medicine (M.D.) program (WWAMI)",
            "Department of Biochemistry",
            "Department of Genome Sciences",
            "Department of Immunology",
            "Department of Rehabilitation Medicine",
            "Department of Laboratory Medicine & Pathology",
        ],
        "keywords": ["School of Medicine", "UW Medicine", "medicine", "WWAMI", "M.D."],
    },
    {
        "key": "NURS",
        "name": "School of Nursing",
        "sort_order": 12,
        "website": "https://nursing.uw.edu/",
        "leadership": "Hilaire Thompson — Executive Dean",
        "research_centers": [
            "Doctor of Nursing Practice (DNP) program",
            "Master of Nursing program",
            "Ph.D. in Nursing Science program",
        ],
        "keywords": ["School of Nursing", "nursing", "DNP"],
    },
    {
        "key": "PHARM",
        "name": "School of Pharmacy",
        "sort_order": 13,
        "website": "https://sop.washington.edu/",
        "leadership": "Jay Panyam — Dean",
        "research_centers": [
            "Doctor of Pharmacy (PharmD) program",
            "Department of Pharmaceutics",
            "Department of Medicinal Chemistry",
            "Department of Pharmacy (pharmaceutical outcomes research & policy)",
        ],
        "keywords": ["School of Pharmacy", "pharmacy", "PharmD", "pharmaceutics"],
    },
    {
        "key": "EVANS",
        "name": "Daniel J. Evans School of Public Policy and Governance",
        "sort_order": 14,
        "website": "https://evans.uw.edu/",
        "leadership": "Jodi Sandfort — Dean",
        "research_centers": [
            "Master of Public Administration (MPA) program",
            "Executive Master of Public Administration program",
            "Ph.D. in Public Policy & Management program",
        ],
        "keywords": ["Evans School", "public policy", "public administration", "MPA"],
    },
    {
        "key": "PUBH",
        "name": "School of Public Health",
        "sort_order": 15,
        "website": "https://sph.washington.edu/",
        "leadership": "Hilary Godwin — Dean",
        "research_centers": [
            "Department of Biostatistics",
            "Department of Epidemiology",
            "Department of Environmental & Occupational Health Sciences",
            "Department of Health Systems & Population Health",
            "Department of Global Health",
        ],
        "keywords": [
            "School of Public Health",
            "public health",
            "epidemiology",
            "biostatistics",
            "global health",
        ],
    },
    {
        "key": "SOCW",
        "name": "School of Social Work",
        "sort_order": 16,
        "website": "https://socialwork.uw.edu/",
        "leadership": "Michael S. Spencer — Dean",
        "research_centers": [
            "Bachelor of Arts in Social Welfare program",
            "Master of Social Work (MSW) program",
            "Ph.D. in Social Welfare program",
        ],
        "keywords": ["School of Social Work", "social work", "MSW"],
    },
]
SCHOOL_NAME = {m["key"]: m["name"] for m in _SCHOOL_META}
SCHOOL_WEBSITE = {m["name"]: m["website"] for m in _SCHOOL_META}


def _school_description(m: dict) -> str:
    return (
        f"The {m['name']} is one of the 16 degree-granting colleges and schools of the University "
        "of Washington in Seattle."
    )


SCHOOLS: list[dict] = [
    {"name": m["name"], "sort_order": m["sort_order"], "description": _school_description(m)}
    for m in _SCHOOL_META
]


def _about_for(m: dict) -> dict:
    return {
        "leadership": m["leadership"],
        "research_centers": m["research_centers"],
        "source": {
            "label": "UW leadership + college/school websites",
            "url": "https://www.washington.edu/leadership/",
        },
    }


def _about_omitted(m: dict) -> list[str]:
    # UW does not publish a single founding year per college on one authoritative
    # page, and notable-faculty lists are curated per department; omit-with-reason.
    return ["about_detail.founded", "about_detail.faculty", "about_detail.named_for"]


# == Feeds (content_sources) ==
_UW_NEWS_RSS = "https://www.washington.edu/news/feed/"
_NEWS_URL = "https://www.washington.edu/news/"
_SOCIAL = {
    "instagram": "https://www.instagram.com/uofwa/",
    "linkedin": "https://www.linkedin.com/school/university-of-washington/",
    "x": "https://twitter.com/UW",
    "youtube": "https://www.youtube.com/user/uwhuskies",
    "facebook": "https://www.facebook.com/UofWA/",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _UW_NEWS_RSS,
    "news_url": _NEWS_URL,
    "news_curated": True,
    "social": _SOCIAL,
}
_KEYWORDS_BY_SCHOOL = {m["name"]: m["keywords"] for m in _SCHOOL_META}


def _school_content(name: str) -> dict:
    return {
        "news_rss": _UW_NEWS_RSS,
        "news_url": SCHOOL_WEBSITE.get(name, _NEWS_URL),
        "news_curated": False,
        "keywords": list(_KEYWORDS_BY_SCHOOL[name]),
        "social": _SOCIAL,
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


# == Program catalog (slug, school_key, program_name, degree_type, department, delivery, duration) ==
_CATALOG: list[tuple] = [
    (
        "uw-american-ethnic-studies-bs",
        "ARTSCI",
        "American Ethnic Studies",
        "bachelors",
        "American Ethnic Studies",
        "on_campus",
        48,
    ),
    (
        "uw-american-indian-studies-bs",
        "ARTSCI",
        "American Indian Studies",
        "bachelors",
        "American Indian Studies",
        "on_campus",
        48,
    ),
    (
        "uw-american-music-bs",
        "ARTSCI",
        "American Music",
        "bachelors",
        "American Music",
        "on_campus",
        48,
    ),
    ("uw-anthropology-bs", "ARTSCI", "Anthropology", "bachelors", "Anthropology", "on_campus", 48),
    (
        "uw-applied-and-computational-math-sciences-bs",
        "ARTSCI",
        "Applied and Computational Math Sciences",
        "bachelors",
        "Applied and Computational Math Sciences",
        "on_campus",
        48,
    ),
    (
        "uw-applied-mathematics-bs",
        "ARTSCI",
        "Applied Mathematics",
        "bachelors",
        "Applied Mathematics",
        "on_campus",
        48,
    ),
    ("uw-art-bs", "ARTSCI", "Art", "bachelors", "Art", "on_campus", 48),
    ("uw-art-history-bs", "ARTSCI", "Art History", "bachelors", "Art History", "on_campus", 48),
    (
        "uw-asian-languages-and-cultures-bs",
        "ARTSCI",
        "Asian Languages and Cultures",
        "bachelors",
        "Asian Languages and Cultures",
        "on_campus",
        48,
    ),
    ("uw-astronomy-bs", "ARTSCI", "Astronomy", "bachelors", "Astronomy", "on_campus", 48),
    ("uw-biochemistry-bs", "ARTSCI", "Biochemistry", "bachelors", "Biochemistry", "on_campus", 48),
    ("uw-biology-bs", "ARTSCI", "Biology", "bachelors", "Biology", "on_campus", 48),
    ("uw-chemistry-bs", "ARTSCI", "Chemistry", "bachelors", "Chemistry", "on_campus", 48),
    ("uw-chinese-bs", "ARTSCI", "Chinese", "bachelors", "Chinese", "on_campus", 48),
    (
        "uw-cinema-and-media-studies-bs",
        "ARTSCI",
        "Cinema and Media Studies",
        "bachelors",
        "Cinema and Media Studies",
        "on_campus",
        48,
    ),
    (
        "uw-classical-studies-bs",
        "ARTSCI",
        "Classical Studies",
        "bachelors",
        "Classical Studies",
        "on_campus",
        48,
    ),
    ("uw-classics-bs", "ARTSCI", "Classics", "bachelors", "Classics", "on_campus", 48),
    (
        "uw-communication-bs",
        "ARTSCI",
        "Communication",
        "bachelors",
        "Communication",
        "on_campus",
        48,
    ),
    (
        "uw-comparative-history-of-ideas-bs",
        "ARTSCI",
        "Comparative History of Ideas",
        "bachelors",
        "Comparative History of Ideas",
        "on_campus",
        48,
    ),
    (
        "uw-comparative-literature-bs",
        "ARTSCI",
        "Comparative Literature",
        "bachelors",
        "Comparative Literature",
        "on_campus",
        48,
    ),
    (
        "uw-comparative-religion-bs",
        "ARTSCI",
        "Comparative Religion",
        "bachelors",
        "Comparative Religion",
        "on_campus",
        48,
    ),
    ("uw-composition-bs", "ARTSCI", "Composition", "bachelors", "Composition", "on_campus", 48),
    (
        "uw-computational-finance-and-risk-management-bs",
        "ARTSCI",
        "Computational Finance and Risk Management",
        "bachelors",
        "Computational Finance and Risk Management",
        "on_campus",
        48,
    ),
    (
        "uw-computer-science-bs",
        "ARTSCI",
        "Computer Science",
        "bachelors",
        "Computer Science",
        "on_campus",
        48,
    ),
    ("uw-dance-bs", "ARTSCI", "Dance", "bachelors", "Dance", "on_campus", 48),
    ("uw-danish-bs", "ARTSCI", "Danish", "bachelors", "Danish", "on_campus", 48),
    ("uw-drama-bs", "ARTSCI", "Drama", "bachelors", "Drama", "on_campus", 48),
    (
        "uw-eastern-european-languages-literature-and-culture-bs",
        "ARTSCI",
        "Eastern European Languages, Literature, and Culture",
        "bachelors",
        "Eastern European Languages, Literature, and Culture",
        "on_campus",
        48,
    ),
    ("uw-economics-bs", "ARTSCI", "Economics", "bachelors", "Economics", "on_campus", 48),
    ("uw-english-bs", "ARTSCI", "English", "bachelors", "English", "on_campus", 48),
    (
        "uw-ethnomusicology-bs",
        "ARTSCI",
        "Ethnomusicology",
        "bachelors",
        "Ethnomusicology",
        "on_campus",
        48,
    ),
    ("uw-finnish-bs", "ARTSCI", "Finnish", "bachelors", "Finnish", "on_campus", 48),
    ("uw-french-bs", "ARTSCI", "French", "bachelors", "French", "on_campus", 48),
    (
        "uw-gender-women-and-sexuality-studies-bs",
        "ARTSCI",
        "Gender, Women, and Sexuality Studies",
        "bachelors",
        "Gender, Women, and Sexuality Studies",
        "on_campus",
        48,
    ),
    ("uw-geography-bs", "ARTSCI", "Geography", "bachelors", "Geography", "on_campus", 48),
    (
        "uw-german-studies-bs",
        "ARTSCI",
        "German Studies",
        "bachelors",
        "German Studies",
        "on_campus",
        48,
    ),
    (
        "uw-global-literary-studies-bs",
        "ARTSCI",
        "Global Literary Studies",
        "bachelors",
        "Global Literary Studies",
        "on_campus",
        48,
    ),
    ("uw-greek-bs", "ARTSCI", "Greek", "bachelors", "Greek", "on_campus", 48),
    ("uw-guitar-bs", "ARTSCI", "Guitar", "bachelors", "Guitar", "on_campus", 48),
    ("uw-history-bs", "ARTSCI", "History", "bachelors", "History", "on_campus", 48),
    (
        "uw-history-and-philosophy-of-science-bs",
        "ARTSCI",
        "History and Philosophy of Science",
        "bachelors",
        "History and Philosophy of Science",
        "on_campus",
        48,
    ),
    (
        "uw-individualized-studies-bs",
        "ARTSCI",
        "Individualized Studies",
        "bachelors",
        "Individualized Studies",
        "on_campus",
        48,
    ),
    (
        "uw-industrial-design-bs",
        "ARTSCI",
        "Industrial Design",
        "bachelors",
        "Industrial Design",
        "on_campus",
        48,
    ),
    (
        "uw-integrated-social-sciences-bs",
        "ARTSCI",
        "Integrated Social Sciences",
        "bachelors",
        "Integrated Social Sciences",
        "online",
        48,
    ),
    (
        "uw-interaction-design-bs",
        "ARTSCI",
        "Interaction Design",
        "bachelors",
        "Interaction Design",
        "on_campus",
        48,
    ),
    (
        "uw-international-studies-bs",
        "ARTSCI",
        "International Studies",
        "bachelors",
        "International Studies",
        "on_campus",
        48,
    ),
    ("uw-italian-bs", "ARTSCI", "Italian", "bachelors", "Italian", "on_campus", 48),
    ("uw-japanese-bs", "ARTSCI", "Japanese", "bachelors", "Japanese", "on_campus", 48),
    ("uw-jazz-studies-bs", "ARTSCI", "Jazz Studies", "bachelors", "Jazz Studies", "on_campus", 48),
    ("uw-korean-bs", "ARTSCI", "Korean", "bachelors", "Korean", "on_campus", 48),
    ("uw-latin-bs", "ARTSCI", "Latin", "bachelors", "Latin", "on_campus", 48),
    (
        "uw-law-societies-and-justice-bs",
        "ARTSCI",
        "Law, Societies, and Justice",
        "bachelors",
        "Law, Societies, and Justice",
        "on_campus",
        48,
    ),
    ("uw-linguistics-bs", "ARTSCI", "Linguistics", "bachelors", "Linguistics", "on_campus", 48),
    ("uw-mathematics-bs", "ARTSCI", "Mathematics", "bachelors", "Mathematics", "on_campus", 48),
    ("uw-microbiology-bs", "ARTSCI", "Microbiology", "bachelors", "Microbiology", "on_campus", 48),
    (
        "uw-middle-eastern-languages-and-cultures-bs",
        "ARTSCI",
        "Middle Eastern Languages and Cultures",
        "bachelors",
        "Middle Eastern Languages and Cultures",
        "on_campus",
        48,
    ),
    ("uw-music-bs", "ARTSCI", "Music", "bachelors", "Music", "on_campus", 48),
    (
        "uw-music-education-bs",
        "ARTSCI",
        "Music Education",
        "bachelors",
        "Music Education",
        "on_campus",
        48,
    ),
    ("uw-music-theory-bs", "ARTSCI", "Music Theory", "bachelors", "Music Theory", "on_campus", 48),
    ("uw-neuroscience-bs", "ARTSCI", "Neuroscience", "bachelors", "Neuroscience", "on_campus", 48),
    ("uw-norwegian-bs", "ARTSCI", "Norwegian", "bachelors", "Norwegian", "on_campus", 48),
    (
        "uw-orchestral-instruments-bs",
        "ARTSCI",
        "Orchestral Instruments",
        "bachelors",
        "Orchestral Instruments",
        "on_campus",
        48,
    ),
    ("uw-organ-bs", "ARTSCI", "Organ", "bachelors", "Organ", "on_campus", 48),
    ("uw-percussion-bs", "ARTSCI", "Percussion", "bachelors", "Percussion", "on_campus", 48),
    ("uw-philosophy-bs", "ARTSCI", "Philosophy", "bachelors", "Philosophy", "on_campus", 48),
    ("uw-physics-bs", "ARTSCI", "Physics", "bachelors", "Physics", "on_campus", 48),
    ("uw-piano-bs", "ARTSCI", "Piano", "bachelors", "Piano", "on_campus", 48),
    (
        "uw-political-science-bs",
        "ARTSCI",
        "Political Science",
        "bachelors",
        "Political Science",
        "on_campus",
        48,
    ),
    ("uw-psychology-bs", "ARTSCI", "Psychology", "bachelors", "Psychology", "on_campus", 48),
    (
        "uw-romance-linguistics-bs",
        "ARTSCI",
        "Romance Linguistics",
        "bachelors",
        "Romance Linguistics",
        "on_campus",
        48,
    ),
    (
        "uw-russian-language-literature-and-culture-bs",
        "ARTSCI",
        "Russian Language, Literature, and Culture",
        "bachelors",
        "Russian Language, Literature, and Culture",
        "on_campus",
        48,
    ),
    (
        "uw-scandinavian-area-studies-bs",
        "ARTSCI",
        "Scandinavian Area Studies",
        "bachelors",
        "Scandinavian Area Studies",
        "on_campus",
        48,
    ),
    ("uw-sociology-bs", "ARTSCI", "Sociology", "bachelors", "Sociology", "on_campus", 48),
    (
        "uw-south-asian-languages-and-cultures-bs",
        "ARTSCI",
        "South Asian Languages and Cultures",
        "bachelors",
        "South Asian Languages and Cultures",
        "on_campus",
        48,
    ),
    ("uw-spanish-bs", "ARTSCI", "Spanish", "bachelors", "Spanish", "on_campus", 48),
    (
        "uw-speech-and-hearing-sciences-bs",
        "ARTSCI",
        "Speech and Hearing Sciences",
        "bachelors",
        "Speech and Hearing Sciences",
        "on_campus",
        48,
    ),
    ("uw-statistics-bs", "ARTSCI", "Statistics", "bachelors", "Statistics", "on_campus", 48),
    (
        "uw-string-instruments-bs",
        "ARTSCI",
        "String Instruments",
        "bachelors",
        "String Instruments",
        "on_campus",
        48,
    ),
    ("uw-swedish-bs", "ARTSCI", "Swedish", "bachelors", "Swedish", "on_campus", 48),
    (
        "uw-visual-communication-design-bs",
        "ARTSCI",
        "Visual Communication Design",
        "bachelors",
        "Visual Communication Design",
        "on_campus",
        48,
    ),
    ("uw-voice-bs", "ARTSCI", "Voice", "bachelors", "Voice", "on_campus", 48),
    ("uw-anthropology-ms", "ARTSCI", "Anthropology", "masters", "Anthropology", "on_campus", 24),
    (
        "uw-applied-chemical-science-and-technology-ms",
        "ARTSCI",
        "Applied Chemical Science and Technology",
        "masters",
        "Applied Chemical Science and Technology",
        "on_campus",
        24,
    ),
    (
        "uw-applied-child-and-adolescent-psychology-prevention-and-treatment-ms",
        "ARTSCI",
        "Applied Child and Adolescent Psychology: Prevention and Treatment",
        "masters",
        "Applied Child and Adolescent Psychology: Prevention and Treatment",
        "on_campus",
        24,
    ),
    (
        "uw-applied-mathematics-ms",
        "ARTSCI",
        "Applied Mathematics",
        "masters",
        "Applied Mathematics",
        "online",
        24,
    ),
    ("uw-art-history-ms", "ARTSCI", "Art History", "masters", "Art History", "on_campus", 24),
    (
        "uw-asian-languages-and-literature-ms",
        "ARTSCI",
        "Asian Languages & Literature",
        "masters",
        "Asian Languages & Literature",
        "on_campus",
        24,
    ),
    ("uw-astronomy-ms", "ARTSCI", "Astronomy", "masters", "Astronomy", "on_campus", 24),
    ("uw-chemistry-ms", "ARTSCI", "Chemistry", "masters", "Chemistry", "on_campus", 24),
    ("uw-china-studies-ms", "ARTSCI", "China Studies", "masters", "China Studies", "on_campus", 24),
    (
        "uw-cinema-and-media-studies-ms",
        "ARTSCI",
        "Cinema and Media Studies",
        "masters",
        "Cinema and Media Studies",
        "on_campus",
        24,
    ),
    ("uw-communication-ms", "ARTSCI", "Communication", "masters", "Communication", "on_campus", 24),
    (
        "uw-computational-finance-and-risk-management-ms",
        "ARTSCI",
        "Computational Finance & Risk Management",
        "masters",
        "Computational Finance & Risk Management",
        "online",
        24,
    ),
    (
        "uw-computational-linguistics-ms",
        "ARTSCI",
        "Computational Linguistics",
        "masters",
        "Computational Linguistics",
        "online",
        24,
    ),
    ("uw-dance-ms", "ARTSCI", "Dance", "masters", "Dance", "on_campus", 24),
    ("uw-design-ms", "ARTSCI", "Design", "masters", "Design", "on_campus", 24),
    ("uw-drama-ms", "ARTSCI", "Drama", "masters", "Drama", "on_campus", 24),
    (
        "uw-east-asia-studies-ms",
        "ARTSCI",
        "East Asia Studies",
        "masters",
        "East Asia Studies",
        "on_campus",
        24,
    ),
    ("uw-economics-ms", "ARTSCI", "Economics", "masters", "Economics", "on_campus", 24),
    ("uw-english-ms", "ARTSCI", "English", "masters", "English", "on_campus", 24),
    (
        "uw-feminist-studies-ms",
        "ARTSCI",
        "Feminist Studies",
        "masters",
        "Feminist Studies",
        "on_campus",
        24,
    ),
    ("uw-fine-arts-ms", "ARTSCI", "Fine Arts", "masters", "Fine Arts", "on_campus", 24),
    ("uw-geography-ms", "ARTSCI", "Geography", "masters", "Geography", "on_campus", 24),
    (
        "uw-german-studies-ms",
        "ARTSCI",
        "German Studies",
        "masters",
        "German Studies",
        "on_campus",
        24,
    ),
    (
        "uw-hispanic-studies-ms",
        "ARTSCI",
        "Hispanic Studies",
        "masters",
        "Hispanic Studies",
        "on_campus",
        24,
    ),
    (
        "uw-international-studies-ms",
        "ARTSCI",
        "International Studies",
        "masters",
        "International Studies",
        "on_campus",
        24,
    ),
    (
        "uw-italian-studies-ms",
        "ARTSCI",
        "Italian Studies",
        "masters",
        "Italian Studies",
        "on_campus",
        24,
    ),
    ("uw-japan-studies-ms", "ARTSCI", "Japan Studies", "masters", "Japan Studies", "on_campus", 24),
    ("uw-korea-studies-ms", "ARTSCI", "Korea Studies", "masters", "Korea Studies", "on_campus", 24),
    ("uw-linguistics-ms", "ARTSCI", "Linguistics", "masters", "Linguistics", "on_campus", 24),
    ("uw-mathematics-ms", "ARTSCI", "Mathematics", "masters", "Mathematics", "on_campus", 24),
    ("uw-music-ms", "ARTSCI", "Music", "masters", "Music", "on_campus", 24),
    (
        "uw-near-eastern-languages-and-civilization-ms",
        "ARTSCI",
        "Near Eastern Languages & Civilization",
        "masters",
        "Near Eastern Languages & Civilization",
        "on_campus",
        24,
    ),
    ("uw-philosophy-ms", "ARTSCI", "Philosophy", "masters", "Philosophy", "on_campus", 24),
    ("uw-physics-ms", "ARTSCI", "Physics", "masters", "Physics", "on_campus", 24),
    (
        "uw-political-science-ms",
        "ARTSCI",
        "Political Science",
        "masters",
        "Political Science",
        "on_campus",
        24,
    ),
    ("uw-psychology-ms", "ARTSCI", "Psychology", "masters", "Psychology", "on_campus", 24),
    (
        "uw-russia-east-european-and-central-asian-studies-ms",
        "ARTSCI",
        "Russia, East European and Central Asian Studies",
        "masters",
        "Russia, East European and Central Asian Studies",
        "on_campus",
        24,
    ),
    ("uw-scandinavian-ms", "ARTSCI", "Scandinavian", "masters", "Scandinavian", "on_campus", 24),
    (
        "uw-slavic-languages-and-literatures-ms",
        "ARTSCI",
        "Slavic Languages & Literatures",
        "masters",
        "Slavic Languages & Literatures",
        "on_campus",
        24,
    ),
    ("uw-sociology-ms", "ARTSCI", "Sociology", "masters", "Sociology", "on_campus", 24),
    (
        "uw-south-asian-studies-ms",
        "ARTSCI",
        "South Asian Studies",
        "masters",
        "South Asian Studies",
        "on_campus",
        24,
    ),
    (
        "uw-southeast-asian-studies-ms",
        "ARTSCI",
        "Southeast Asian Studies",
        "masters",
        "Southeast Asian Studies",
        "on_campus",
        24,
    ),
    (
        "uw-speech-language-pathology-ms",
        "ARTSCI",
        "Speech-Language Pathology",
        "masters",
        "Speech-Language Pathology",
        "on_campus",
        24,
    ),
    ("uw-statistics-ms", "ARTSCI", "Statistics", "masters", "Statistics", "on_campus", 24),
    ("uw-audiology-prof", "ARTSCI", "Audiology", "professional", "Audiology", "on_campus", 48),
    ("uw-anthropology-phd", "ARTSCI", "Anthropology", "phd", "Anthropology", "on_campus", 60),
    (
        "uw-applied-mathematics-phd",
        "ARTSCI",
        "Applied Mathematics",
        "phd",
        "Applied Mathematics",
        "on_campus",
        60,
    ),
    ("uw-art-history-phd", "ARTSCI", "Art History", "phd", "Art History", "on_campus", 60),
    (
        "uw-asian-languages-and-literature-phd",
        "ARTSCI",
        "Asian Languages & Literature",
        "phd",
        "Asian Languages & Literature",
        "on_campus",
        60,
    ),
    ("uw-astronomy-phd", "ARTSCI", "Astronomy", "phd", "Astronomy", "on_campus", 60),
    ("uw-biology-phd", "ARTSCI", "Biology", "phd", "Biology", "on_campus", 60),
    ("uw-chemistry-phd", "ARTSCI", "Chemistry", "phd", "Chemistry", "on_campus", 60),
    (
        "uw-cinema-and-media-studies-phd",
        "ARTSCI",
        "Cinema and Media Studies",
        "phd",
        "Cinema and Media Studies",
        "on_campus",
        60,
    ),
    ("uw-communication-phd", "ARTSCI", "Communication", "phd", "Communication", "on_campus", 60),
    (
        "uw-digital-arts-and-experimental-media-phd",
        "ARTSCI",
        "Digital Arts & Experimental Media",
        "phd",
        "Digital Arts & Experimental Media",
        "on_campus",
        60,
    ),
    ("uw-drama-phd", "ARTSCI", "Drama", "phd", "Drama", "on_campus", 60),
    ("uw-economics-phd", "ARTSCI", "Economics", "phd", "Economics", "on_campus", 60),
    ("uw-english-phd", "ARTSCI", "English", "phd", "English", "on_campus", 60),
    (
        "uw-feminist-studies-phd",
        "ARTSCI",
        "Feminist Studies",
        "phd",
        "Feminist Studies",
        "on_campus",
        60,
    ),
    ("uw-french-studies-phd", "ARTSCI", "French Studies", "phd", "French Studies", "on_campus", 60),
    ("uw-geography-phd", "ARTSCI", "Geography", "phd", "Geography", "on_campus", 60),
    ("uw-german-studies-phd", "ARTSCI", "German Studies", "phd", "German Studies", "on_campus", 60),
    (
        "uw-hispanic-studies-phd",
        "ARTSCI",
        "Hispanic Studies",
        "phd",
        "Hispanic Studies",
        "on_campus",
        60,
    ),
    ("uw-history-phd", "ARTSCI", "History", "phd", "History", "on_campus", 60),
    ("uw-linguistics-phd", "ARTSCI", "Linguistics", "phd", "Linguistics", "on_campus", 60),
    ("uw-mathematics-phd", "ARTSCI", "Mathematics", "phd", "Mathematics", "on_campus", 60),
    ("uw-music-phd", "ARTSCI", "Music", "phd", "Music", "on_campus", 60),
    ("uw-musical-arts-phd", "ARTSCI", "Musical Arts", "phd", "Musical Arts", "on_campus", 60),
    (
        "uw-near-and-middle-eastern-studies-phd",
        "ARTSCI",
        "Near & Middle Eastern Studies",
        "phd",
        "Near & Middle Eastern Studies",
        "on_campus",
        60,
    ),
    ("uw-philosophy-phd", "ARTSCI", "Philosophy", "phd", "Philosophy", "on_campus", 60),
    ("uw-physics-phd", "ARTSCI", "Physics", "phd", "Physics", "on_campus", 60),
    (
        "uw-political-science-phd",
        "ARTSCI",
        "Political Science",
        "phd",
        "Political Science",
        "on_campus",
        60,
    ),
    ("uw-psychology-phd", "ARTSCI", "Psychology", "phd", "Psychology", "on_campus", 60),
    ("uw-scandinavian-phd", "ARTSCI", "Scandinavian", "phd", "Scandinavian", "on_campus", 60),
    (
        "uw-slavic-languages-and-literatures-phd",
        "ARTSCI",
        "Slavic Languages & Literatures",
        "phd",
        "Slavic Languages & Literatures",
        "on_campus",
        60,
    ),
    ("uw-sociology-phd", "ARTSCI", "Sociology", "phd", "Sociology", "on_campus", 60),
    (
        "uw-speech-and-hearing-sciences-phd",
        "ARTSCI",
        "Speech and Hearing Sciences",
        "phd",
        "Speech and Hearing Sciences",
        "on_campus",
        60,
    ),
    ("uw-statistics-phd", "ARTSCI", "Statistics", "phd", "Statistics", "on_campus", 60),
    (
        "uw-architectural-design-bs",
        "BUILT",
        "Architectural Design",
        "bachelors",
        "Architectural Design",
        "on_campus",
        48,
    ),
    (
        "uw-architectural-design-w-const-mgmt-bs",
        "BUILT",
        "Architectural Design (w/Const Mgmt)",
        "bachelors",
        "Architectural Design (w/Const Mgmt)",
        "on_campus",
        48,
    ),
    (
        "uw-architectural-studies-bs",
        "BUILT",
        "Architectural Studies",
        "bachelors",
        "Architectural Studies",
        "on_campus",
        48,
    ),
    (
        "uw-community-environment-and-planning-bs",
        "BUILT",
        "Community, Environment, and Planning",
        "bachelors",
        "Community, Environment, and Planning",
        "on_campus",
        48,
    ),
    (
        "uw-environmental-design-and-sustainability-bs",
        "BUILT",
        "Environmental Design and Sustainability",
        "bachelors",
        "Environmental Design and Sustainability",
        "on_campus",
        48,
    ),
    ("uw-real-estate-bs", "BUILT", "Real Estate", "bachelors", "Real Estate", "on_campus", 48),
    ("uw-architecture-ms", "BUILT", "Architecture", "masters", "Architecture", "on_campus", 24),
    ("uw-concurrent-ms", "BUILT", "Concurrent", "masters", "Concurrent", "on_campus", 24),
    (
        "uw-construction-management-ms",
        "BUILT",
        "Construction Management",
        "masters",
        "Construction Management",
        "online",
        24,
    ),
    (
        "uw-infrastructure-planning-and-management-ms",
        "BUILT",
        "Infrastructure Planning & Management",
        "masters",
        "Infrastructure Planning & Management",
        "on_campus",
        24,
    ),
    (
        "uw-infrastructure-planning-and-management-ms-2",
        "BUILT",
        "Infrastructure Planning & Management",
        "masters",
        "Infrastructure Planning & Management",
        "online",
        24,
    ),
    (
        "uw-landscape-architecture-ms",
        "BUILT",
        "Landscape Architecture",
        "masters",
        "Landscape Architecture",
        "on_campus",
        24,
    ),
    ("uw-real-estate-ms", "BUILT", "Real Estate", "masters", "Real Estate", "on_campus", 24),
    (
        "uw-urban-planning-ms",
        "BUILT",
        "Urban Planning",
        "masters",
        "Urban Planning",
        "on_campus",
        24,
    ),
    (
        "uw-built-environment-phd",
        "BUILT",
        "Built Environment",
        "phd",
        "Built Environment",
        "on_campus",
        60,
    ),
    (
        "uw-urban-design-and-planning-phd",
        "BUILT",
        "Urban Design & Planning",
        "phd",
        "Urban Design & Planning",
        "on_campus",
        60,
    ),
    ("uw-accounting-bs", "BUS", "Accounting", "bachelors", "Accounting", "on_campus", 48),
    (
        "uw-accounting-for-business-professionals-bs",
        "BUS",
        "Accounting for Business Professionals",
        "bachelors",
        "Accounting for Business Professionals",
        "on_campus",
        48,
    ),
    (
        "uw-entrepreneurship-bs",
        "BUS",
        "Entrepreneurship",
        "bachelors",
        "Entrepreneurship",
        "on_campus",
        48,
    ),
    ("uw-finance-bs", "BUS", "Finance", "bachelors", "Finance", "on_campus", 48),
    (
        "uw-human-resources-management-bs",
        "BUS",
        "Human Resources Management",
        "bachelors",
        "Human Resources Management",
        "on_campus",
        48,
    ),
    (
        "uw-information-systems-bs",
        "BUS",
        "Information Systems",
        "bachelors",
        "Information Systems",
        "on_campus",
        48,
    ),
    ("uw-marketing-bs", "BUS", "Marketing", "bachelors", "Marketing", "on_campus", 48),
    (
        "uw-operations-and-supply-chain-management-bs",
        "BUS",
        "Operations and Supply Chain Management",
        "bachelors",
        "Operations and Supply Chain Management",
        "on_campus",
        48,
    ),
    (
        "uw-business-administration-ms",
        "BUS",
        "Business Administration",
        "masters",
        "Business Administration",
        "on_campus",
        24,
    ),
    (
        "uw-business-analytics-ms",
        "BUS",
        "Business Analytics",
        "masters",
        "Business Analytics",
        "on_campus",
        24,
    ),
    (
        "uw-entrepreneurship-ms",
        "BUS",
        "Entrepreneurship",
        "masters",
        "Entrepreneurship",
        "on_campus",
        24,
    ),
    (
        "uw-information-systems-ms",
        "BUS",
        "Information Systems",
        "masters",
        "Information Systems",
        "on_campus",
        24,
    ),
    (
        "uw-professional-accounting-ms",
        "BUS",
        "Professional Accounting",
        "masters",
        "Professional Accounting",
        "on_campus",
        24,
    ),
    (
        "uw-supply-chain-management-ms",
        "BUS",
        "Supply Chain Management",
        "masters",
        "Supply Chain Management",
        "on_campus",
        24,
    ),
    ("uw-taxation-ms", "BUS", "Taxation", "masters", "Taxation", "on_campus", 24),
    (
        "uw-business-administration-phd",
        "BUS",
        "Business Administration",
        "phd",
        "Business Administration",
        "on_campus",
        60,
    ),
    ("uw-dentistry-ms", "DENT", "Dentistry", "masters", "Dentistry", "on_campus", 24),
    ("uw-endodontics-ms", "DENT", "Endodontics", "masters", "Endodontics", "on_campus", 24),
    (
        "uw-oral-health-sciences-ms",
        "DENT",
        "Oral Health Sciences",
        "masters",
        "Oral Health Sciences",
        "on_campus",
        24,
    ),
    ("uw-oral-medicine-ms", "DENT", "Oral Medicine", "masters", "Oral Medicine", "on_campus", 24),
    ("uw-orthodontics-ms", "DENT", "Orthodontics", "masters", "Orthodontics", "on_campus", 24),
    ("uw-periodontics-ms", "DENT", "Periodontics", "masters", "Periodontics", "on_campus", 24),
    (
        "uw-prosthodontics-ms",
        "DENT",
        "Prosthodontics",
        "masters",
        "Prosthodontics",
        "on_campus",
        24,
    ),
    ("uw-dentistry-prof", "DENT", "Dentistry", "professional", "Dentistry", "on_campus", 48),
    ("uw-dentistry-phd", "DENT", "Dentistry", "phd", "Dentistry", "on_campus", 60),
    (
        "uw-oral-health-sciences-phd",
        "DENT",
        "Oral Health Sciences",
        "phd",
        "Oral Health Sciences",
        "on_campus",
        60,
    ),
    (
        "uw-early-care-and-education-bs",
        "EDUC",
        "Early Care and Education",
        "bachelors",
        "Early Care and Education",
        "on_campus",
        48,
    ),
    (
        "uw-early-care-and-education-fee-based-online-bs",
        "EDUC",
        "Early Care and Education (fee-based) (online)",
        "bachelors",
        "Early Care and Education (fee-based) (online)",
        "on_campus",
        48,
    ),
    (
        "uw-early-childhood-and-family-studies-bs",
        "EDUC",
        "Early Childhood and Family Studies",
        "bachelors",
        "Early Childhood and Family Studies",
        "on_campus",
        48,
    ),
    (
        "uw-education-studies-bs",
        "EDUC",
        "Education Studies",
        "bachelors",
        "Education Studies",
        "on_campus",
        48,
    ),
    (
        "uw-education-communities-and-organizations-bs",
        "EDUC",
        "Education, Communities and Organizations",
        "bachelors",
        "Education, Communities and Organizations",
        "on_campus",
        48,
    ),
    (
        "uw-curriculum-and-instruction-ms",
        "EDUC",
        "Curriculum & Instruction",
        "masters",
        "Curriculum & Instruction",
        "on_campus",
        24,
    ),
    (
        "uw-educational-foundations-leadership-and-policy-ms",
        "EDUC",
        "Educational Foundations, Leadership & Policy",
        "masters",
        "Educational Foundations, Leadership & Policy",
        "on_campus",
        24,
    ),
    (
        "uw-educational-leadership-and-policy-studies-ms",
        "EDUC",
        "Educational Leadership & Policy Studies",
        "masters",
        "Educational Leadership & Policy Studies",
        "on_campus",
        24,
    ),
    (
        "uw-learning-sciences-and-human-development-ms",
        "EDUC",
        "Learning Sciences & Human Development",
        "masters",
        "Learning Sciences & Human Development",
        "on_campus",
        24,
    ),
    (
        "uw-master-in-teaching-ms",
        "EDUC",
        "Master In Teaching",
        "masters",
        "Master In Teaching",
        "on_campus",
        24,
    ),
    (
        "uw-measurement-and-statistics-ms",
        "EDUC",
        "Measurement & Statistics",
        "masters",
        "Measurement & Statistics",
        "on_campus",
        24,
    ),
    (
        "uw-special-education-ms",
        "EDUC",
        "Special Education",
        "masters",
        "Special Education",
        "on_campus",
        24,
    ),
    (
        "uw-curriculum-and-instruction-phd",
        "EDUC",
        "Curriculum & Instruction",
        "phd",
        "Curriculum & Instruction",
        "on_campus",
        60,
    ),
    (
        "uw-education-phd",
        "EDUC",
        "Education",
        "phd",
        "Education",
        "on_campus",
        60,
    ),
    (
        "uw-educational-leadership-and-policy-studies-phd",
        "EDUC",
        "Educational Leadership & Policy Studies",
        "phd",
        "Educational Leadership & Policy Studies",
        "on_campus",
        60,
    ),
    (
        "uw-special-education-phd",
        "EDUC",
        "Special Education",
        "phd",
        "Special Education",
        "on_campus",
        60,
    ),
    ("uw-engineering-bs", "ENGR", "Engineering", "bachelors", "Engineering", "on_campus", 48),
    (
        "uw-aeronautics-and-astronautics-ms",
        "ENGR",
        "Aeronautics and Astronautics",
        "masters",
        "Aeronautics and Astronautics",
        "on_campus",
        24,
    ),
    (
        "uw-aerospace-engineering-ms",
        "ENGR",
        "Aerospace Engineering",
        "masters",
        "Aerospace Engineering",
        "online",
        24,
    ),
    (
        "uw-applied-bioengineering-ms",
        "ENGR",
        "Applied Bioengineering",
        "masters",
        "Applied Bioengineering",
        "on_campus",
        24,
    ),
    (
        "uw-artificial-intelligence-and-machine-learning-for-engineering-ms",
        "ENGR",
        "Artificial Intelligence and Machine Learning for Engineering",
        "masters",
        "Artificial Intelligence and Machine Learning for Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-bioengineering-ms",
        "ENGR",
        "Bioengineering",
        "masters",
        "Bioengineering",
        "on_campus",
        24,
    ),
    (
        "uw-chemical-engineering-ms",
        "ENGR",
        "Chemical Engineering",
        "masters",
        "Chemical Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-civil-engineering-ms",
        "ENGR",
        "Civil Engineering",
        "masters",
        "Civil Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-computer-science-and-engineering-ms",
        "ENGR",
        "Computer Science & Engineering",
        "masters",
        "Computer Science & Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-electrical-and-computer-engineering-ms",
        "ENGR",
        "Electrical and Computer Engineering",
        "masters",
        "Electrical and Computer Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-engineering-in-leadership-and-systems-innovation-ms",
        "ENGR",
        "Engineering in Leadership and Systems Innovation",
        "masters",
        "Engineering in Leadership and Systems Innovation",
        "on_campus",
        24,
    ),
    (
        "uw-engineering-in-multidisciplinary-engineering-ms",
        "ENGR",
        "Engineering in Multidisciplinary Engineering",
        "masters",
        "Engineering in Multidisciplinary Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-human-centered-design-and-engineering-ms",
        "ENGR",
        "Human Centered Design & Engineering",
        "masters",
        "Human Centered Design & Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-industrial-and-systems-engineering-ms",
        "ENGR",
        "Industrial & Systems Engineering",
        "masters",
        "Industrial & Systems Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-industrial-engineering-ms",
        "ENGR",
        "Industrial Engineering",
        "masters",
        "Industrial Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-materials-science-and-engineering-ms",
        "ENGR",
        "Materials Science & Engineering",
        "masters",
        "Materials Science & Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-materials-science-and-engineering-ms-2",
        "ENGR",
        "Materials Science and Engineering",
        "masters",
        "Materials Science and Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-mechanical-engineering-ms",
        "ENGR",
        "Mechanical Engineering",
        "masters",
        "Mechanical Engineering",
        "online",
        24,
    ),
    (
        "uw-pharmaceutical-bioengineering-ms",
        "ENGR",
        "Pharmaceutical Bioengineering",
        "masters",
        "Pharmaceutical Bioengineering",
        "online",
        24,
    ),
    (
        "uw-supply-chain-transportation-and-logistics-ms",
        "ENGR",
        "Supply Chain Transportation & Logistics",
        "masters",
        "Supply Chain Transportation & Logistics",
        "online",
        24,
    ),
    (
        "uw-sustainable-transportation-ms",
        "ENGR",
        "Sustainable Transportation",
        "masters",
        "Sustainable Transportation",
        "online",
        24,
    ),
    (
        "uw-technology-innovation-ms",
        "ENGR",
        "Technology Innovation",
        "masters",
        "Technology Innovation",
        "on_campus",
        24,
    ),
    (
        "uw-aeronautics-and-astronautics-phd",
        "ENGR",
        "Aeronautics & Astronautics",
        "phd",
        "Aeronautics & Astronautics",
        "on_campus",
        60,
    ),
    ("uw-bioengineering-phd", "ENGR", "Bioengineering", "phd", "Bioengineering", "on_campus", 60),
    (
        "uw-chemical-engineering-phd",
        "ENGR",
        "Chemical Engineering",
        "phd",
        "Chemical Engineering",
        "on_campus",
        60,
    ),
    (
        "uw-civil-engineering-phd",
        "ENGR",
        "Civil Engineering",
        "phd",
        "Civil Engineering",
        "on_campus",
        60,
    ),
    (
        "uw-computer-science-and-engineering-phd",
        "ENGR",
        "Computer Science & Engineering",
        "phd",
        "Computer Science & Engineering",
        "on_campus",
        60,
    ),
    (
        "uw-electrical-and-computer-engineering-phd",
        "ENGR",
        "Electrical and Computer Engineering",
        "phd",
        "Electrical and Computer Engineering",
        "on_campus",
        60,
    ),
    (
        "uw-industrial-engineering-phd",
        "ENGR",
        "Industrial Engineering",
        "phd",
        "Industrial Engineering",
        "on_campus",
        60,
    ),
    (
        "uw-materials-science-and-engineering-phd",
        "ENGR",
        "Materials Science & Engineering",
        "phd",
        "Materials Science & Engineering",
        "on_campus",
        60,
    ),
    (
        "uw-mechanical-engineering-phd",
        "ENGR",
        "Mechanical Engineering",
        "phd",
        "Mechanical Engineering",
        "on_campus",
        60,
    ),
    (
        "uw-aquatic-conservation-and-ecology-bs",
        "ENV",
        "Aquatic Conservation and Ecology",
        "bachelors",
        "Aquatic Conservation and Ecology",
        "on_campus",
        48,
    ),
    (
        "uw-atmospheric-and-climate-science-bs",
        "ENV",
        "Atmospheric and Climate Science",
        "bachelors",
        "Atmospheric and Climate Science",
        "on_campus",
        48,
    ),
    (
        "uw-earth-and-space-sciences-bs",
        "ENV",
        "Earth and Space Sciences",
        "bachelors",
        "Earth and Space Sciences",
        "on_campus",
        48,
    ),
    (
        "uw-environmental-science-and-terrestrial-resource-management-bs",
        "ENV",
        "Environmental Science and Terrestrial Resource Management",
        "bachelors",
        "Environmental Science and Terrestrial Resource Management",
        "on_campus",
        48,
    ),
    (
        "uw-environmental-studies-bs",
        "ENV",
        "Environmental Studies",
        "bachelors",
        "Environmental Studies",
        "on_campus",
        48,
    ),
    (
        "uw-marine-biology-bs",
        "ENV",
        "Marine Biology",
        "bachelors",
        "Marine Biology",
        "on_campus",
        48,
    ),
    ("uw-oceanography-bs", "ENV", "Oceanography", "bachelors", "Oceanography", "on_campus", 48),
    (
        "uw-sustainable-bioresource-systems-engineering-bs",
        "ENV",
        "Sustainable Bioresource Systems Engineering",
        "bachelors",
        "Sustainable Bioresource Systems Engineering",
        "on_campus",
        48,
    ),
    (
        "uw-aquatic-and-fishery-sciences-ms",
        "ENV",
        "Aquatic & Fishery Sciences",
        "masters",
        "Aquatic & Fishery Sciences",
        "on_campus",
        24,
    ),
    (
        "uw-atmospheric-and-climate-science-ms",
        "ENV",
        "Atmospheric and Climate Science",
        "masters",
        "Atmospheric and Climate Science",
        "on_campus",
        24,
    ),
    (
        "uw-earth-and-space-sciences-ms",
        "ENV",
        "Earth & Space Sciences",
        "masters",
        "Earth & Space Sciences",
        "on_campus",
        24,
    ),
    (
        "uw-environmental-and-forest-sciences-ms",
        "ENV",
        "Environmental & Forest Sciences",
        "masters",
        "Environmental & Forest Sciences",
        "on_campus",
        24,
    ),
    (
        "uw-forest-resources-ms",
        "ENV",
        "Forest Resources",
        "masters",
        "Forest Resources",
        "on_campus",
        24,
    ),
    ("uw-marine-affairs-ms", "ENV", "Marine Affairs", "masters", "Marine Affairs", "on_campus", 24),
    ("uw-oceanography-ms", "ENV", "Oceanography", "masters", "Oceanography", "on_campus", 24),
    (
        "uw-quantitative-ecology-and-resource-management-ms",
        "ENV",
        "Quantitative Ecology & Resource Management",
        "masters",
        "Quantitative Ecology & Resource Management",
        "on_campus",
        24,
    ),
    (
        "uw-aquatic-and-fishery-sciences-phd",
        "ENV",
        "Aquatic & Fishery Sciences",
        "phd",
        "Aquatic & Fishery Sciences",
        "on_campus",
        60,
    ),
    (
        "uw-atmospheric-and-climate-science-phd",
        "ENV",
        "Atmospheric and Climate Science",
        "phd",
        "Atmospheric and Climate Science",
        "on_campus",
        60,
    ),
    (
        "uw-earth-and-space-sciences-phd",
        "ENV",
        "Earth & Space Sciences",
        "phd",
        "Earth & Space Sciences",
        "on_campus",
        60,
    ),
    (
        "uw-environmental-and-forest-sciences-phd",
        "ENV",
        "Environmental & Forest Sciences",
        "phd",
        "Environmental & Forest Sciences",
        "on_campus",
        60,
    ),
    ("uw-oceanography-phd", "ENV", "Oceanography", "phd", "Oceanography", "on_campus", 60),
    (
        "uw-quantitative-ecology-and-resource-management-phd",
        "ENV",
        "Quantitative Ecology & Resource Management",
        "phd",
        "Quantitative Ecology & Resource Management",
        "on_campus",
        60,
    ),
    (
        "uw-information-management-ms",
        "ISCHOOL",
        "Information Management",
        "masters",
        "Information Management",
        "online",
        24,
    ),
    (
        "uw-information-science-ms",
        "ISCHOOL",
        "Information Science",
        "masters",
        "Information Science",
        "on_campus",
        24,
    ),
    (
        "uw-library-and-information-science-ms",
        "ISCHOOL",
        "Library & Information Science",
        "masters",
        "Library & Information Science",
        "online",
        24,
    ),
    ("uw-museology-ms", "ISCHOOL", "Museology", "masters", "Museology", "on_campus", 24),
    (
        "uw-information-science-phd",
        "ISCHOOL",
        "Information Science",
        "phd",
        "Information Science",
        "on_campus",
        60,
    ),
    ("uw-data-science-ms", "GRAD", "Data Science", "masters", "Data Science", "on_campus", 24),
    (
        "uw-human-computer-interaction-and-design-ms",
        "GRAD",
        "Human-Computer Interaction & Design",
        "masters",
        "Human-Computer Interaction & Design",
        "on_campus",
        24,
    ),
    (
        "uw-molecular-and-cellular-biology-ms",
        "GRAD",
        "Molecular & Cellular Biology",
        "masters",
        "Molecular & Cellular Biology",
        "on_campus",
        24,
    ),
    (
        "uw-molecular-engineering-ms",
        "GRAD",
        "Molecular Engineering",
        "masters",
        "Molecular Engineering",
        "on_campus",
        24,
    ),
    ("uw-neuroscience-ms", "GRAD", "Neuroscience", "masters", "Neuroscience", "on_campus", 24),
    ("uw-individual-phd-phd", "GRAD", "Individual PhD", "phd", "Individual PhD", "on_campus", 60),
    (
        "uw-molecular-and-cellular-biology-phd",
        "GRAD",
        "Molecular & Cellular Biology",
        "phd",
        "Molecular & Cellular Biology",
        "on_campus",
        60,
    ),
    (
        "uw-molecular-engineering-phd",
        "GRAD",
        "Molecular Engineering",
        "phd",
        "Molecular Engineering",
        "on_campus",
        60,
    ),
    ("uw-neuroscience-phd", "GRAD", "Neuroscience", "phd", "Neuroscience", "on_campus", 60),
    ("uw-jurisprudence-ms", "LAW", "Jurisprudence", "masters", "Jurisprudence", "on_campus", 24),
    ("uw-laws-ms", "LAW", "Laws", "masters", "Laws", "on_campus", 24),
    (
        "uw-laws-in-taxation-ms",
        "LAW",
        "Laws In Taxation",
        "masters",
        "Laws In Taxation",
        "on_campus",
        24,
    ),
    ("uw-law-prof", "LAW", "Law", "professional", "Law", "on_campus", 48),
    ("uw-law-phd", "LAW", "Law", "phd", "Law", "on_campus", 60),
    (
        "uw-anatomic-pathology-ms",
        "MED",
        "Anatomic Pathology",
        "masters",
        "Anatomic Pathology",
        "on_campus",
        24,
    ),
    ("uw-biochemistry-ms", "MED", "Biochemistry", "masters", "Biochemistry", "on_campus", 24),
    ("uw-bioethics-ms", "MED", "Bioethics", "masters", "Bioethics", "on_campus", 24),
    (
        "uw-biomedical-and-health-informatics-ms",
        "MED",
        "Biomedical & Health Informatics",
        "masters",
        "Biomedical & Health Informatics",
        "on_campus",
        24,
    ),
    (
        "uw-clinical-health-services-ms",
        "MED",
        "Clinical Health Services",
        "masters",
        "Clinical Health Services",
        "on_campus",
        24,
    ),
    (
        "uw-comparative-medicine-ms",
        "MED",
        "Comparative Medicine",
        "masters",
        "Comparative Medicine",
        "on_campus",
        24,
    ),
    (
        "uw-genetic-counseling-ms",
        "MED",
        "Genetic Counseling",
        "masters",
        "Genetic Counseling",
        "on_campus",
        24,
    ),
    (
        "uw-genome-sciences-ms",
        "MED",
        "Genome Sciences",
        "masters",
        "Genome Sciences",
        "on_campus",
        24,
    ),
    (
        "uw-health-metrics-sciences-ms",
        "MED",
        "Health Metrics Sciences",
        "masters",
        "Health Metrics Sciences",
        "on_campus",
        24,
    ),
    ("uw-immunology-ms", "MED", "Immunology", "masters", "Immunology", "on_campus", 24),
    (
        "uw-laboratory-medicine-ms",
        "MED",
        "Laboratory Medicine",
        "masters",
        "Laboratory Medicine",
        "on_campus",
        24,
    ),
    ("uw-microbiology-ms", "MED", "Microbiology", "masters", "Microbiology", "on_campus", 24),
    (
        "uw-molecular-medicine-and-mechanisms-of-disease-ms",
        "MED",
        "Molecular Medicine and Mechanisms of Disease",
        "masters",
        "Molecular Medicine and Mechanisms of Disease",
        "on_campus",
        24,
    ),
    (
        "uw-neurobiology-and-biophysics-ms",
        "MED",
        "Neurobiology and Biophysics",
        "masters",
        "Neurobiology and Biophysics",
        "on_campus",
        24,
    ),
    (
        "uw-occupational-therapy-ms",
        "MED",
        "Occupational Therapy",
        "masters",
        "Occupational Therapy",
        "on_campus",
        24,
    ),
    ("uw-pharmacology-ms", "MED", "Pharmacology", "masters", "Pharmacology", "on_campus", 24),
    (
        "uw-prosthetics-and-orthotics-ms",
        "MED",
        "Prosthetics & Orthotics",
        "masters",
        "Prosthetics & Orthotics",
        "on_campus",
        24,
    ),
    (
        "uw-rehabilitation-medicine-ms",
        "MED",
        "Rehabilitation Medicine",
        "masters",
        "Rehabilitation Medicine",
        "on_campus",
        24,
    ),
    ("uw-medicine-prof", "MED", "Medicine", "professional", "Medicine", "on_campus", 48),
    (
        "uw-physical-therapy-prof",
        "MED",
        "Physical Therapy",
        "professional",
        "Physical Therapy",
        "on_campus",
        48,
    ),
    ("uw-biochemistry-phd", "MED", "Biochemistry", "phd", "Biochemistry", "on_campus", 60),
    (
        "uw-biomedical-and-health-informatics-phd",
        "MED",
        "Biomedical & Health Informatics",
        "phd",
        "Biomedical & Health Informatics",
        "on_campus",
        60,
    ),
    ("uw-genome-sciences-phd", "MED", "Genome Sciences", "phd", "Genome Sciences", "on_campus", 60),
    (
        "uw-health-metrics-global-health-metrics-and-implementation-sciences-phd",
        "MED",
        "Health Metrics: Global Health Metrics & Implementation Sciences",
        "phd",
        "Health Metrics: Global Health Metrics & Implementation Sciences",
        "on_campus",
        60,
    ),
    ("uw-immunology-phd", "MED", "Immunology", "phd", "Immunology", "on_campus", 60),
    ("uw-microbiology-phd", "MED", "Microbiology", "phd", "Microbiology", "on_campus", 60),
    (
        "uw-molecular-medicine-and-mechanisms-of-disease-phd",
        "MED",
        "Molecular Medicine and Mechanisms of Disease",
        "phd",
        "Molecular Medicine and Mechanisms of Disease",
        "on_campus",
        60,
    ),
    (
        "uw-neurobiology-and-biophysics-phd",
        "MED",
        "Neurobiology and Biophysics",
        "phd",
        "Neurobiology and Biophysics",
        "on_campus",
        60,
    ),
    ("uw-pharmacology-phd", "MED", "Pharmacology", "phd", "Pharmacology", "on_campus", 60),
    (
        "uw-rehabilitation-science-phd",
        "MED",
        "Rehabilitation Science",
        "phd",
        "Rehabilitation Science",
        "on_campus",
        60,
    ),
    ("uw-nursing-ms", "NURS", "Nursing", "masters", "Nursing", "on_campus", 24),
    (
        "uw-nursing-practice-prof",
        "NURS",
        "Nursing Practice",
        "professional",
        "Nursing Practice",
        "on_campus",
        48,
    ),
    ("uw-nursing-phd", "NURS", "Nursing", "phd", "Nursing", "on_campus", 60),
    (
        "uw-biomedical-regulatory-affairs-ms",
        "PHARM",
        "Biomedical Regulatory Affairs",
        "masters",
        "Biomedical Regulatory Affairs",
        "on_campus",
        24,
    ),
    (
        "uw-health-economics-and-outcomes-research-ms",
        "PHARM",
        "Health Economics and Outcomes Research",
        "masters",
        "Health Economics and Outcomes Research",
        "on_campus",
        24,
    ),
    (
        "uw-medicinal-chemistry-ms",
        "PHARM",
        "Medicinal Chemistry",
        "masters",
        "Medicinal Chemistry",
        "on_campus",
        24,
    ),
    ("uw-pharmaceutics-ms", "PHARM", "Pharmaceutics", "masters", "Pharmaceutics", "on_campus", 24),
    ("uw-pharmacy-prof", "PHARM", "Pharmacy", "professional", "Pharmacy", "on_campus", 48),
    (
        "uw-health-economics-and-outcomes-research-phd",
        "PHARM",
        "Health Economics and Outcomes Research",
        "phd",
        "Health Economics and Outcomes Research",
        "on_campus",
        60,
    ),
    (
        "uw-medicinal-chemistry-phd",
        "PHARM",
        "Medicinal Chemistry",
        "phd",
        "Medicinal Chemistry",
        "on_campus",
        60,
    ),
    ("uw-pharmaceutics-phd", "PHARM", "Pharmaceutics", "phd", "Pharmaceutics", "on_campus", 60),
    (
        "uw-public-service-and-policy-bs",
        "EVANS",
        "Public Service and Policy",
        "bachelors",
        "Public Service and Policy",
        "on_campus",
        48,
    ),
    (
        "uw-public-administration-ms",
        "EVANS",
        "Public Administration",
        "masters",
        "Public Administration",
        "on_campus",
        24,
    ),
    (
        "uw-public-policy-and-management-ms",
        "EVANS",
        "Public Policy & Management",
        "masters",
        "Public Policy & Management",
        "on_campus",
        24,
    ),
    (
        "uw-public-policy-and-management-phd",
        "EVANS",
        "Public Policy & Management",
        "phd",
        "Public Policy & Management",
        "on_campus",
        60,
    ),
    (
        "uw-environmental-public-health-bs",
        "PUBH",
        "Environmental Public Health",
        "bachelors",
        "Environmental Public Health",
        "on_campus",
        48,
    ),
    (
        "uw-food-systems-nutrition-and-health-bs",
        "PUBH",
        "Food Systems, Nutrition, and Health",
        "bachelors",
        "Food Systems, Nutrition, and Health",
        "on_campus",
        48,
    ),
    (
        "uw-public-health-global-health-bs",
        "PUBH",
        "Public Health-Global Health",
        "bachelors",
        "Public Health-Global Health",
        "on_campus",
        48,
    ),
    ("uw-biostatistics-ms", "PUBH", "Biostatistics", "masters", "Biostatistics", "on_campus", 24),
    (
        "uw-environmental-health-sciences-ms",
        "PUBH",
        "Environmental Health Sciences",
        "masters",
        "Environmental Health Sciences",
        "on_campus",
        24,
    ),
    ("uw-epidemiology-ms", "PUBH", "Epidemiology", "masters", "Epidemiology", "on_campus", 24),
    (
        "uw-genetic-epidemiology-ms",
        "PUBH",
        "Genetic Epidemiology",
        "masters",
        "Genetic Epidemiology",
        "on_campus",
        24,
    ),
    ("uw-global-health-ms", "PUBH", "Global Health", "masters", "Global Health", "on_campus", 24),
    (
        "uw-health-administration-ms",
        "PUBH",
        "Health Administration",
        "masters",
        "Health Administration",
        "online",
        24,
    ),
    (
        "uw-health-informatics-and-health-information-management-ms",
        "PUBH",
        "Health Informatics & Health Information Management",
        "masters",
        "Health Informatics & Health Information Management",
        "online",
        24,
    ),
    (
        "uw-health-systems-and-population-health-ms",
        "PUBH",
        "Health Systems and Population Health",
        "masters",
        "Health Systems and Population Health",
        "on_campus",
        24,
    ),
    (
        "uw-nutritional-sciences-ms",
        "PUBH",
        "Nutritional Sciences",
        "masters",
        "Nutritional Sciences",
        "on_campus",
        24,
    ),
    ("uw-pathobiology-ms", "PUBH", "Pathobiology", "masters", "Pathobiology", "on_campus", 24),
    (
        "uw-public-health-genetics-ms",
        "PUBH",
        "Public Health Genetics",
        "masters",
        "Public Health Genetics",
        "on_campus",
        24,
    ),
    (
        "uw-public-health-nutrition-ms",
        "PUBH",
        "Public Health Nutrition",
        "masters",
        "Public Health Nutrition",
        "on_campus",
        24,
    ),
    ("uw-biostatistics-phd", "PUBH", "Biostatistics", "phd", "Biostatistics", "on_campus", 60),
    (
        "uw-environmental-health-sciences-phd",
        "PUBH",
        "Environmental Health Sciences",
        "phd",
        "Environmental Health Sciences",
        "on_campus",
        60,
    ),
    ("uw-epidemiology-phd", "PUBH", "Epidemiology", "phd", "Epidemiology", "on_campus", 60),
    (
        "uw-global-health-global-health-metrics-and-implementation-sciences-phd",
        "PUBH",
        "Global Health: Global Health Metrics & Implementation Sciences",
        "phd",
        "Global Health: Global Health Metrics & Implementation Sciences",
        "on_campus",
        60,
    ),
    (
        "uw-health-services-phd",
        "PUBH",
        "Health Services",
        "phd",
        "Health Services",
        "on_campus",
        60,
    ),
    (
        "uw-nutritional-sciences-phd",
        "PUBH",
        "Nutritional Sciences",
        "phd",
        "Nutritional Sciences",
        "on_campus",
        60,
    ),
    ("uw-pathobiology-phd", "PUBH", "Pathobiology", "phd", "Pathobiology", "on_campus", 60),
    (
        "uw-public-health-genetics-phd",
        "PUBH",
        "Public Health Genetics",
        "phd",
        "Public Health Genetics",
        "on_campus",
        60,
    ),
    (
        "uw-social-welfare-bs",
        "SOCW",
        "Social Welfare",
        "bachelors",
        "Social Welfare",
        "on_campus",
        48,
    ),
    ("uw-social-work-ms", "SOCW", "Social Work", "masters", "Social Work", "on_campus", 24),
    ("uw-social-welfare-phd", "SOCW", "Social Welfare", "phd", "Social Welfare", "on_campus", 60),
]

_SPECIAL_NAMES: dict[str, str] = {
    "uw-business-administration-ms": "Master of Business Administration",
    "uw-audiology-prof": "Doctor of Audiology",
    "uw-dentistry-prof": "Doctor of Dental Surgery",
    "uw-law-prof": "Juris Doctor",
    "uw-medicine-prof": "Doctor of Medicine",
    "uw-nursing-practice-prof": "Doctor of Nursing Practice",
    "uw-pharmacy-prof": "Doctor of Pharmacy",
    "uw-physical-therapy-prof": "Doctor of Physical Therapy",
    "uw-infrastructure-planning-and-management-ms-2": (
        "Master of Science in Infrastructure Planning & Management (Online)"
    ),
}

_UG_PREFIX_BY_SCHOOL: dict[str, str] = {
    "ARTSCI": "Bachelor of Arts in",
    "BUILT": "Bachelor of Arts in",
    "BUS": "Bachelor of Arts in",
    "EDUC": "Bachelor of Arts in",
    "ENGR": "Bachelor of Science in",
    "ENV": "Bachelor of Science in",
    "ISCHOOL": "Bachelor of Science in",
    "NURS": "Bachelor of Science in",
    "PHARM": "Bachelor of Science in",
    "EVANS": "Bachelor of Arts in",
    "PUBH": "Bachelor of Science in",
    "SOCW": "Bachelor of Arts in",
}

_SUFFIX_MAP: list[tuple[str, str]] = [
    ("-phd", "prefix:Doctor of Philosophy in"),
    ("-ms-2", "prefix:Master of Science in"),
    ("-ms", "prefix:Master of Science in"),
    ("-bs", "ug"),
]


def _derive_program_name(slug: str, field: str, school_key: str) -> str:
    if slug in _SPECIAL_NAMES:
        return _SPECIAL_NAMES[slug]
    if (
        field.startswith(
            (
                "Master of ",
                "Doctor of ",
                "Juris Doctor",
            )
        )
        or slug.endswith("-prof")
    ):
        return field
    for suffix, spec in _SUFFIX_MAP:
        if slug.endswith(suffix):
            if spec == "ug":
                prefix = _UG_PREFIX_BY_SCHOOL.get(school_key, "Bachelor of Arts in")
                return f"{prefix} {field}"
            prefix = spec[7:]
            return f"{prefix} {field}"
    return field


_FIELD_LABEL: dict[str, str] = {
    "Doctor of Medicine": "medicine",
    "Doctor of Pharmacy": "pharmacy",
    "Juris Doctor": "law",
    "Master of Business Administration": "business administration",
}

_LEVEL_PRIORITY: dict[str, int] = {
    "bachelors": 0,
    "professional": 1,
    "masters": 2,
    "certificate": 3,
    "phd": 4,
}

_FOCUS_LEAD_RE = re.compile(
    r"^(.*?\b(?:covers|combines|spans|includes|integrates|offers?|examines?|trains?|"
    r"prepares?|underpins?|emphasizes?|centers? on|focuses? on|explores?|studies|study|"
    r"pairs?|blends?|joins?|teach(?:es)?|analyze[s]?|bridges?|operate[s]?|run[s]?|use[s]?|"
    r"support[s]?|choose among|connects|develops)\b\s*)",
    re.I,
)


def _field_label(name: str) -> str:
    if " in " in name:
        return name.split(" in ", 1)[1].strip()
    if name in _FIELD_LABEL:
        return _FIELD_LABEL[name]
    for prefix in (
        "Master of ",
        "Bachelor of ",
        "Doctor of ",
        "Graduate Certificate of ",
    ):
        if name.startswith(prefix):
            return name[len(prefix) :].strip()
    return _anti_stub_field(name)


def _extract_focus(clause: str) -> str:
    m = _FOCUS_LEAD_RE.match(clause)
    rest = clause[m.end() :] if m else clause
    rest = re.split(
        r"\s+(?:with|through|tied to|drawing on|near|at the|across|for UW|for the)\s+",
        rest,
        1,
    )[0]
    rest = rest.strip().rstrip(".").strip()
    if len(rest) > 66:
        cut = rest[:66]
        cut = cut[: cut.rfind(",")] if "," in cut else cut[: cut.rfind(" ")]
        rest = cut.strip().rstrip(",").strip()
    return rest


def _focus_for(field: str) -> str:
    focus = FIELD_FOCUS.get(field)
    if focus:
        return focus
    return _extract_focus(FIELD_DESCRIPTIONS.get(field, ""))


def _sibling_body(dtype: str, field_label: str, focus: str, *, school: str = "") -> str:
    """Distinct, level-specific body for a credential sibling (not the field's primary)."""
    uw = "UW"
    place = f" through {school}" if school else " on the Seattle campus"
    if dtype == "masters":
        return (
            f"Master's study in {field_label} at {uw}{place} builds on {focus}, with advanced "
            f"coursework, methods, and a thesis or capstone."
        )
    if dtype == "phd":
        return (
            f"Doctoral research in {field_label} at {uw}{place} advances {focus}, supported by "
            f"a faculty-mentored dissertation and graduate funding."
        )
    if dtype == "certificate":
        return (
            f"This {uw} graduate certificate in {field_label}{place} packages focused coursework "
            f"in {focus} for working professionals and degree-seekers."
        )
    if dtype == "professional":
        return (
            f"This professional {uw} program in {field_label}{place} pairs classroom study with "
            f"supervised clinical or practical training in {focus}."
        )
    return (
        f"The undergraduate major in {field_label} at {uw}{place} develops {focus} through core "
        f"sequences, hands-on labs or studio, and upper-division electives."
    )


def _adapt_clause_for_degree_type(clause: str, degree_type: str) -> str:
    if degree_type == "bachelors":
        if clause.startswith("Graduate "):
            return "Undergraduate " + clause[len("Graduate ") :]
        if clause.startswith("Graduate-level "):
            return "Undergraduate-level " + clause[len("Graduate-level ") :]
    return clause


def _level_appropriate_clause(clause: str, degree_type: str) -> str:
    if degree_type == "bachelors":
        return clause
    clause = re.sub(r"\bthe undergraduate major\b", "the program", clause, flags=re.I)
    clause = re.sub(r"\bundergraduate (major|program)\b", "program", clause, flags=re.I)
    return clause


def _apply_fmt_suffix(desc: str, spec: dict) -> str:
    fmt = spec.get("delivery_format", "on_campus")
    if fmt == "online":
        return desc + " Delivered online."
    if fmt == "hybrid":
        return desc + " Delivered in a hybrid format."
    return desc


def _normalize_field_label(label: str) -> str:
    return re.sub(r"\s*\([^)]+\)$", "", label).strip()


def _group_key(spec: dict) -> str:
    label = _normalize_field_label(_field_label(spec["program_name"]))
    if spec["degree_type"] == "professional":
        return f"{label}::professional"
    return label


def _anchor_clause(spec: dict, field_clause: str | None) -> str:
    """Unique anchor description: verified field lead + UW-specific tie-in when available."""
    from unipaith.data.uw_catalogue_descriptions import CATALOGUE_DESCRIPTIONS

    slug = spec["slug"]
    raw = CATALOGUE_DESCRIPTIONS.get(slug)
    if raw:
        lead = raw.split("At the University of Washington")[0].strip()
        for prefix in ("Graduate study.", "Doctoral research.", "Graduate certificate."):
            if lead.startswith(prefix):
                lead = lead[len(prefix) :].strip()
        if len(lead) >= 40 and not lead.startswith("Catalog entry"):
            label = _normalize_field_label(_field_label(spec["program_name"]))
            uw_tail = FIELD_DESCRIPTIONS.get(label, "")
            if uw_tail and uw_tail not in lead:
                # Append a short UW-specific clause when the lead is generic discipline text.
                uw_bit = uw_tail.split(".")[0].strip()
                if uw_bit.lower().startswith("uw "):
                    return f"{lead} {uw_bit}."
            return lead
    if field_clause:
        return field_clause
    raise ValueError(f"No anchor clause for {slug!r}")


def _assign_descriptions(programs: list[dict]) -> None:
    """Assign a per-credential description to every program (frame_stripped_shared_body = 0)."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        groups[_group_key(spec)].append(spec)

    for label, specs in groups.items():
        fd_field = next((s.get("_fd_field") for s in specs if s.get("_fd_field")), None)
        fd_field = _normalize_field_label(fd_field or label)
        field_clause = (
            FIELD_DESCRIPTIONS.get(fd_field)
            or FIELD_DESCRIPTIONS.get(label)
            or FIELD_DESCRIPTIONS.get(_normalize_field_label(label))
        )

        def _slug_text(s: dict) -> str | None:
            return SLUG_DESCRIPTIONS.get(s["slug"])

        anchor = next(
            (s for s in specs if s["degree_type"] == "bachelors"),
            min(specs, key=lambda s: (_LEVEL_PRIORITY.get(s["degree_type"], 2), s["slug"])),
        )
        focus = (
            _focus_for(fd_field)
            or _focus_for(label)
            or _extract_focus(field_clause or "")
        )

        assigned: set[str] = set()
        for spec in specs:
            slug_text = _slug_text(spec)
            if slug_text and slug_text not in assigned:
                body = slug_text
            elif spec is anchor:
                base = _anchor_clause(spec, field_clause)
                body = _level_appropriate_clause(
                    _adapt_clause_for_degree_type(base, spec["degree_type"]),
                    spec["degree_type"],
                )
            else:
                if not focus:
                    raise ValueError(f"No focus for sibling {spec['slug']!r} ({label})")
                body = _sibling_body(
                    spec["degree_type"],
                    _field_label(spec["program_name"]),
                    focus,
                    school=spec.get("school", ""),
                )
            assigned.add(body)
            spec["description"] = _apply_fmt_suffix(body, spec)
            spec.pop("_fd_field", None)


def _field_key(program_name: str) -> str:
    if program_name in _SPECIAL_NAMES.values():
        for k, v in _SPECIAL_NAMES.items():
            if v == program_name:
                return program_name
    for prefix in (
        "Bachelor of Science in ",
        "Bachelor of Arts in ",
        "Bachelor of Fine Arts in ",
        "Bachelor of Music in ",
        "Master of Science in ",
        "Master of Arts in ",
        "Master of Fine Arts in ",
        "Master of Music in ",
        "Master of Engineering in ",
        "Master of Education in ",
        "Master of Public Health in ",
        "Master of Social Work in ",
        "Doctor of Philosophy in ",
        "Juris Doctor",
        "Doctor of Medicine",
        "Doctor of Dental Surgery",
        "Doctor of Pharmacy",
        "Doctor of Nursing Practice",
        "Doctor of Physical Therapy",
        "Doctor of Audiology",
        "Master of Business Administration",
    ):
        if program_name.startswith(prefix):
            return program_name[len(prefix) :].strip()
    return program_name


# == Matcher-core CIP-2020 codes (REPAIR_BACKLOG #1 — the CIP join key the CPEF matcher
# uses to resolve a program's field to ref_majors + the field-66 vocabulary) ==
# Keyed by _normalize_field_label(_field_label(program_name)) for every program. Each value is
# the standard NCES CIP-2020 4-digit family for that field of study (the IPEDS classification),
# never a guessed fact about the program; a genuinely interdisciplinary field with no
# single-discipline CIP is mapped to its closest CIP family (incl. 30.xx multi/interdisciplinary),
# exactly as IPEDS itself codes such programs. Source: NCES IPEDS CIP-2020 code list.
_CIP_BY_FIELD: dict[str, str] = {
    # --- Engineering & technology (CIP 14.xx / 15.xx / 52.20) ---
    "Aerospace Engineering": "14.0201",
    "Aeronautics & Astronautics": "14.0201",
    "Aeronautics and Astronautics": "14.0201",
    "Applied Bioengineering": "14.0501",
    "Bioengineering": "14.0501",
    "Pharmaceutical Bioengineering": "14.0501",
    "Chemical Engineering": "14.0701",
    "Civil Engineering": "14.0801",
    "Infrastructure Planning & Management": "14.0801",
    "Computer Science & Engineering": "14.0901",
    "Electrical and Computer Engineering": "14.1001",
    "Engineering": "14.0101",
    "Engineering in Leadership and Systems Innovation": "14.0101",
    "Engineering in Multidisciplinary Engineering": "14.0101",
    "Human Centered Design & Engineering": "14.0101",
    "Industrial & Systems Engineering": "14.3501",
    "Industrial Engineering": "14.3501",
    "Materials Science & Engineering": "14.1801",
    "Materials Science and Engineering": "14.1801",
    "Mechanical Engineering": "14.1901",
    "Molecular Engineering": "14.9999",
    "Sustainable Bioresource Systems Engineering": "14.0301",
    "Construction Management": "52.2001",
    "Technology Innovation": "14.0101",
    # --- Computing, data & information (CIP 11.xx / 30.70 / 25.01) ---
    "Computer Science": "11.0701",
    "Artificial Intelligence and Machine Learning for Engineering": "11.0102",
    "Data Science": "30.7001",
    "Human-Computer Interaction & Design": "11.0104",
    "Biomedical & Health Informatics": "51.2706",
    "Health Informatics & Health Information Management": "51.0706",
    "Information Management": "11.0401",
    "Information Science": "11.0401",
    "Information Systems": "11.0401",
    "Library & Information Science": "25.0101",
    "Museology": "30.1401",
    # --- Mathematics & statistics (CIP 27.xx / 30.70) ---
    "Mathematics": "27.0101",
    "Applied Mathematics": "27.0301",
    "Applied and Computational Math Sciences": "27.0303",
    "Computational Finance & Risk Management": "27.0305",
    "Computational Finance and Risk Management": "27.0305",
    "Statistics": "27.0501",
    "Biostatistics": "26.1102",
    "Biochemistry": "26.0202",
    "Measurement & Statistics": "27.0501",
    "Computational Linguistics": "30.4801",
    # --- Physical sciences (CIP 40.xx / 03.xx) ---
    "Physics": "40.0801",
    "Astronomy": "40.0201",
    "Atmospheric and Climate Science": "40.0401",
    "Chemistry": "40.0501",
    "Applied Chemical Science and Technology": "40.0501",
    "Earth & Space Sciences": "40.0601",
    "Earth and Space Sciences": "40.0601",
    "Oceanography": "40.0607",
    "Aquatic & Fishery Sciences": "03.0301",
    "Aquatic Conservation and Ecology": "03.0301",
    "Quantitative Ecology & Resource Management": "03.0104",
    "Environmental Science and Terrestrial Resource Management": "03.0104",
    "Environmental & Forest Sciences": "03.0501",
    "Forest Resources": "03.0501",
    "Environmental Studies": "03.0103",
    "Environmental Design and Sustainability": "03.0104",
    # --- Biological & life sciences (CIP 26.xx) ---
    "Biology": "26.0101",
    "Marine Biology": "26.1302",
    "Microbiology": "26.0502",
    "Immunology": "26.0507",
    "Molecular & Cellular Biology": "26.0204",
    "Genome Sciences": "26.0806",
    "Molecular Medicine and Mechanisms of Disease": "26.0102",
    "Neurobiology and Biophysics": "26.1501",
    "Neuroscience": "26.1501",
    "Pathobiology": "26.0910",
    "Anatomic Pathology": "26.0910",
    "Comparative Medicine": "26.0901",
    "Nutritional Sciences": "30.1901",
    "Public Health Nutrition": "30.1901",
    "Food Systems, Nutrition, and Health": "30.1901",
    # --- Health professions, medicine & public health (CIP 51.xx / 26.13) ---
    "Audiology": "51.0202",
    "Speech and Hearing Sciences": "51.0204",
    "Speech-Language Pathology": "51.0203",
    "Nursing": "51.3801",
    "Nursing Practice": "51.3818",
    "Occupational Therapy": "51.2306",
    "Physical Therapy": "51.2308",
    "Rehabilitation Medicine": "51.2300",
    "Rehabilitation Science": "51.2314",
    "Prosthetics & Orthotics": "51.2307",
    "Bioethics": "51.3201",
    "Biomedical Regulatory Affairs": "51.2003",
    "Laboratory Medicine": "51.1005",
    "Genetic Counseling": "51.1509",
    "Medicinal Chemistry": "51.2004",
    "Pharmaceutics": "51.2003",
    "Pharmacology": "26.1001",
    "Public Health Genetics": "26.0801",
    "Genetic Epidemiology": "26.1309",
    "Epidemiology": "26.1309",
    "Environmental Health Sciences": "51.2202",
    "Environmental Public Health": "51.2202",
    "Public Health-Global Health": "51.2201",
    "Global Health": "51.2201",
    "Global Health: Global Health Metrics & Implementation Sciences": "51.2201",
    "Health Metrics: Global Health Metrics & Implementation Sciences": "51.2201",
    "Health Metrics Sciences": "51.2201",
    "Health Administration": "51.0701",
    "Health Services": "51.2201",
    "Clinical Health Services": "51.2201",
    "Health Systems and Population Health": "51.2201",
    "Health Economics and Outcomes Research": "51.2211",
    # --- Dentistry (CIP 51.04) ---
    "Dental Surgery": "51.0401",
    "Dentistry": "51.0401",
    "Oral Health Sciences": "51.0401",
    "Oral Medicine": "51.0401",
    "Endodontics": "51.0506",
    "Orthodontics": "51.0508",
    "Periodontics": "51.0510",
    "Prosthodontics": "51.0511",
    # --- Psychology & cognitive (CIP 42.xx) ---
    "Psychology": "42.0101",
    "Applied Child and Adolescent Psychology: Prevention and Treatment": "42.2703",
    # --- Social sciences & policy (CIP 45.xx / 44.xx) ---
    "Anthropology": "45.0201",
    "Economics": "45.0601",
    "Geography": "45.0701",
    "Political Science": "45.1001",
    "Sociology": "45.1101",
    "International Studies": "45.0901",
    "China Studies": "05.0123",
    "East Asia Studies": "05.0104",
    "Japan Studies": "05.0127",
    "Korea Studies": "05.0128",
    "South Asian Studies": "05.0112",
    "Southeast Asian Studies": "05.0113",
    "Russia, East European and Central Asian Studies": "05.0110",
    "Near & Middle Eastern Studies": "05.0108",
    "Public Administration": "44.0401",
    "Public Policy & Management": "44.0501",
    "Public Service and Policy": "44.0501",
    "Social Welfare": "44.0701",
    "Social Work": "44.0701",
    "Marine Affairs": "03.0205",
    "Law, Societies, and Justice": "22.0000",
    "Integrated Social Sciences": "45.0101",
    # --- Area, ethnic, gender & cultural studies (CIP 05.xx) ---
    "American Ethnic Studies": "05.0200",
    "American Indian Studies": "05.0202",
    "Feminist Studies": "05.0207",
    "Gender, Women, and Sexuality Studies": "05.0207",
    "Scandinavian Area Studies": "05.0111",
    "Comparative Religion": "38.0201",
    "Comparative History of Ideas": "24.0103",
    "History and Philosophy of Science": "54.0108",
    # --- Languages & literatures (CIP 16.xx / 23.xx) ---
    "Linguistics": "16.0102",
    "Romance Linguistics": "16.0102",
    "Asian Languages & Literature": "16.0399",
    "Asian Languages and Cultures": "16.0399",
    "South Asian Languages and Cultures": "16.0700",
    "Middle Eastern Languages and Cultures": "16.1100",
    "Near Eastern Languages & Civilization": "16.1100",
    "Chinese": "16.0301",
    "Japanese": "16.0302",
    "Korean": "16.0303",
    "Slavic Languages & Literatures": "16.0400",
    "Eastern European Languages, Literature, and Culture": "16.0400",
    "Russian Language, Literature, and Culture": "16.0402",
    "Scandinavian": "16.0502",
    "Danish": "16.0502",
    "Finnish": "16.1502",
    "Norwegian": "16.0502",
    "Swedish": "16.0502",
    "French": "16.0901",
    "French Studies": "16.0901",
    "Italian": "16.0902",
    "Italian Studies": "16.0902",
    "Hispanic Studies": "16.0905",
    "Spanish": "16.0905",
    "German Studies": "16.0501",
    "Classics": "16.1200",
    "Classical Studies": "16.1200",
    "Greek": "16.1200",
    "Latin": "16.1200",
    "Comparative Literature": "16.0104",
    "English": "23.0101",
    "Global Literary Studies": "16.0104",
    # --- Arts, design, architecture, music, drama (CIP 50.xx / 04.xx) ---
    "Art": "50.0701",
    "Art History": "50.0703",
    "Fine Arts": "50.0702",
    "Visual Communication Design": "50.0409",
    "Design": "50.0404",
    "Industrial Design": "50.0404",
    "Interaction Design": "50.0409",
    "Architectural Design": "04.0201",
    "Architecture": "04.0201",
    "Architectural Studies": "04.0201",
    "Landscape Architecture": "04.0601",
    "Urban Design & Planning": "04.0301",
    "Urban Planning": "04.0301",
    "Built Environment": "04.0201",
    "Community, Environment, and Planning": "04.0301",
    "Real Estate": "52.1501",
    "Dance": "50.0301",
    "Drama": "50.0501",
    "Cinema and Media Studies": "50.0601",
    "Digital Arts & Experimental Media": "50.0102",
    "Music": "50.0901",
    "American Music": "50.0901",
    "Composition": "50.0904",
    "Music Theory": "50.0905",
    "Musicology": "50.0905",
    "Ethnomusicology": "50.0905",
    "Jazz Studies": "50.0910",
    "Music Education": "13.1312",
    "Musical Arts": "50.0903",
    "Guitar": "50.0903",
    "Organ": "50.0903",
    "Orchestral Instruments": "50.0903",
    "Percussion": "50.0903",
    "Piano": "50.0903",
    "String Instruments": "50.0903",
    "Voice": "50.0903",
    # --- Humanities & communication (CIP 38.xx / 54.xx / 24.xx / 09.xx) ---
    "Philosophy": "38.0101",
    "History": "54.0101",
    "Communication": "09.0100",
    # --- Education (CIP 13.xx / 19.07) ---
    "Education": "13.0101",
    "Education Studies": "13.0101",
    "Education, Communities and Organizations": "13.0101",
    "Educational Foundations, Leadership & Policy": "13.0401",
    "Educational Leadership & Policy Studies": "13.0401",
    "Curriculum & Instruction": "13.0301",
    "Learning Sciences & Human Development": "13.0601",
    "Special Education": "13.1001",
    "Master In Teaching": "13.0101",
    "Early Care and Education": "13.1210",
    "Early Care and Education (fee-based)": "13.1210",
    "Early Childhood and Family Studies": "19.0706",
    # --- Business & management (CIP 52.xx) ---
    "Business Administration": "52.0201",
    "Business Analytics": "52.1301",
    "Accounting": "52.0301",
    "Accounting for Business Professionals": "52.0301",
    "Professional Accounting": "52.0301",
    "Finance": "52.0801",
    "Marketing": "52.1401",
    "Entrepreneurship": "52.0701",
    "Human Resources Management": "52.1001",
    "Operations and Supply Chain Management": "52.0203",
    "Supply Chain Management": "52.0203",
    "Supply Chain Transportation & Logistics": "52.0209",
    "Sustainable Transportation": "52.0209",
    # --- Law (CIP 22.xx) ---
    "Law": "22.0101",
    "Laws": "22.0201",
    "Jurisprudence": "22.0201",
    "Laws In Taxation": "22.0203",
    "Taxation": "52.1601",
    # --- Professional labels (lowercase, from _FIELD_LABEL) ---
    "business administration": "52.0201",
    "law": "22.0101",
    "medicine": "51.1201",
    "pharmacy": "51.2001",
    # --- Individualized / interdisciplinary (CIP 30.xx) ---
    "Individual PhD": "30.9999",
    "Individualized Studies": "30.9999",
    "Concurrent": "30.9999",
}


def _cip_for(spec: dict) -> str | None:
    """CIP-2020 code for a program, keyed by its normalized field label (omit if uncodeable)."""
    return _CIP_BY_FIELD.get(_normalize_field_label(_field_label(spec["program_name"])))


def _build_catalog() -> list[dict]:
    out = []
    for slug, sk, name, dtype, _dept, fmt, dur in _CATALOG:
        pname = _derive_program_name(slug, name, sk)
        spec = {
            "slug": slug,
            "school": SCHOOL_NAME[sk],
            "school_key": sk,
            "program_name": pname,
            "degree_type": dtype,
            "department": SCHOOL_NAME[sk],
            "delivery_format": fmt,
            "duration_months": dur,
            "_fd_field": _normalize_field_label(
                _field_label(pname) if dtype != "professional" else name
            ),
        }
        spec["cip"] = _cip_for(spec)
        out.append(spec)
    _assign_descriptions(out)
    return out


PROGRAMS: list[dict] = _build_catalog()
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

# Matcher-core coverage gate (REPAIR_BACKLOG #1): every program must carry a valid CIP-2020
# code. A miss is a build error (resolve the field in _CIP_BY_FIELD), never a silent null.
_cip_missing = [p["slug"] for p in PROGRAMS if not p.get("cip")]
if _cip_missing:
    raise ValueError(f"UW catalog missing cip_code on {len(_cip_missing)} rows: {_cip_missing[:5]}")
_cip_bad = sorted({p["cip"] for p in PROGRAMS if not re.fullmatch(r"\d{2}\.\d{4}", p["cip"])})
if _cip_bad:
    raise ValueError(f"UW catalog has malformed cip_code values: {_cip_bad}")

_TRACKS_BY_SLUG: dict[str, list[str]] = {
    "uw-education-phd": [
        "Curriculum & Instruction",
        "Educational Leadership & Policy Studies",
        "Learning Sciences & Human Development",
        "Measurement & Statistics",
        "School Psychology",
        "Special Education",
    ],
}

_catalog_errors = validate_catalog(PROGRAMS)
_name_prefix_desc = sum(
    1 for p in PROGRAMS if (p.get("description") or "").startswith(p.get("program_name", ""))
)
if _name_prefix_desc:
    _catalog_errors.append(f"name-prefixed descriptions on {_name_prefix_desc} programs")
_desc_counts = Counter(p.get("description") for p in PROGRAMS)
_shared_desc = sum(c - 1 for c in _desc_counts.values() if c > 1)
if _shared_desc:
    _catalog_errors.append(f"identical descriptions shared across {_shared_desc} rows")
_frame_shared = frame_stripped_shared_body(PROGRAMS)
if _frame_shared:
    _catalog_errors.append(
        f"frame-stripped shared body on {len(_frame_shared)} fields: {_frame_shared[:8]}"
    )
_anti_stub = _anti_stub_analyze(PROGRAMS)
if not _anti_stub.is_clean:
    _catalog_errors.append(f"anti-stub gate failed: {_anti_stub.summary()}")
if _catalog_errors:
    raise ValueError(f"UW catalog validation failed: {_catalog_errors}")

_WEBSITE_OVERRIDE: dict[str, str] = {
    "uw-computer-science-bs": "https://www.cs.washington.edu/academics/ugrad",
    "uw-computer-science-and-engineering-ms": "https://www.cs.washington.edu/academics/grad",
    "uw-computer-science-and-engineering-phd": "https://www.cs.washington.edu/academics/phd",
    "uw-medicine-prof": "https://www.uwmedicine.org/school-of-medicine/md-program",
    "uw-dentistry-prof": "https://dental.washington.edu/dds-program/",
    "uw-law-prof": "https://www.law.uw.edu/academics/jd",
    "uw-pharmacy-prof": "https://sop.washington.edu/pharmd/",
    "uw-nursing-practice-prof": "https://nursing.uw.edu/program/doctor-of-nursing-practice/",
    "uw-business-administration-ms": "https://foster.uw.edu/academics/degree-programs/full-time-mba/",
    "uw-library-and-information-science-ms": "https://ischool.uw.edu/programs/mlis",
    "uw-information-management-ms": "https://ischool.uw.edu/programs/msim",
}
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "uw-computer-science-bs": ["Paul G. Allen School", "computer science", "CS", "Allen School"],
    "uw-computer-science-and-engineering-ms": [
        "Paul G. Allen School",
        "computer science",
        "Allen School",
    ],
    "uw-computer-science-and-engineering-phd": [
        "Paul G. Allen School",
        "computer science",
        "Allen School",
    ],
    "uw-medicine-prof": ["UW Medicine", "School of Medicine", "M.D.", "WWAMI"],
    "uw-nursing-practice-prof": ["School of Nursing", "DNP", "nursing"],
    "uw-business-administration-ms": ["Foster School of Business", "Foster MBA", "MBA"],
    "uw-law-prof": ["School of Law", "J.D.", "Juris Doctor"],
    "uw-pharmacy-prof": ["School of Pharmacy", "PharmD", "pharmacy"],
    "uw-library-and-information-science-ms": ["iSchool", "MLIS", "library and information science"],
}


def _website_for(spec: dict) -> str:
    return _WEBSITE_OVERRIDE.get(spec["slug"], SCHOOL_WEBSITE[spec["school"]])


# == Costs ==
_UNDERGRAD_COA = 32446
_AVG_NET_PRICE = 14091
_COST_SRC = "U.S. Dept. of Education — College Scorecard (UW, UNITID 236948)"
_COST_SRC_URL = (
    "https://collegescorecard.ed.gov/school/?236948-University-of-Washington-Seattle-Campus"
)


# == Published tuition (2025-26 academic year) ==
# UW is a PUBLIC university and publishes TWO annual stickers per credential level — a WA-
# resident rate and a higher non-resident (out-of-state) rate (UW Office of Planning & Budgeting
# tuition dashboards + UW Student Financial Aid budgets). The CPEF matcher reads the flat scalar
# ``program.tuition`` for its budget breaker + affordability fit, NOT the residency-aware net-price
# estimator (REPAIR_BACKLOG #2): the out-of-state + ALL-international applicant pool is the majority
# at a flagship public, so the scalar must carry the NON-RESIDENT sticker or the over-budget veto
# under-fires 2.5–3.5× for them. So ``_tuition_for`` (the scalar) returns the NON-RESIDENT rate per
# tier, while ``cost_data.breakdown`` keeps BOTH ``tuition_in_state`` and ``tuition_out_of_state``
# (honest + sourced). UW's own statement is that only Dentistry, Law, Medicine, Pharmacy, Nursing
# and PT carry bespoke professional rates; every other graduate program bills the flat graduate
# Tier I schedule. Funding is a SEPARATE signal, so a funded research PhD carries the published
# non-resident graduate sticker (the matcher's budget input), not $0.
_TUITION_UG_RESIDENT = 13406  # UW WA-resident undergraduate annual tuition, 2025-26
_TUITION_UG_NONRES = 44460  # UW non-resident undergraduate annual tuition (admit.washington.edu)
_TUITION_GRAD_RESIDENT = 19011  # UW WA-resident graduate Tier I annual, 2025-26 (OPB: $6,337/qtr×3)
_TUITION_GRAD_NONRES = 33171  # UW non-resident graduate Tier I annual, 2025-26 (OPB: $11,057/qtr×3)
_TUITION_FA_SRC = (
    "UW Office of Planning & Budgeting — 2025-26 Seattle quarterly tuition & fees / UW Student "
    "Financial Aid student budgets"
)
_TUITION_FA_URL = "https://www.washington.edu/financialaid/getting-started/student-budgets/"
_TUITION_OPB_URL = (
    "https://www.washington.edu/opb/tuition-fees/current-tuition-and-fees-dashboards/"
    "quarterly-tuition-and-fees-pdf-files/"
)

# Bespoke per-program annual tuition — each program's own published cost page (resident +
# non-resident). The matcher scalar uses the non-resident figure; both ship in the breakdown.
_PROFESSIONAL_TUITION: dict[str, dict] = {
    "Juris Doctor": {
        "resident": 47073,
        "nonresident": 58956,
        "year": "2025-26",
        "source": "UW School of Law — Tuition & Fees (2025-26)",
        "source_url": "https://www.law.uw.edu/admissions/financing/tuition",
    },
    "Doctor of Medicine": {
        "resident": 57968,
        "nonresident": 102319,
        "year": "2025-26",
        "source": "UW School of Medicine — Cost of Attendance (MS1, 2025-26)",
        "source_url": "https://education.uwmedicine.org/student-affairs/financial-aid/cost-of-attendance/",
    },
    "Doctor of Dental Surgery": {
        "resident": 59226,
        "nonresident": 84926,
        "year": "2025-26",
        "source": "UW School of Dentistry — Projected Costs (first year, 2025-26)",
        "source_url": "https://dental.washington.edu/students/admissions/projected-costs/",
    },
    "Doctor of Pharmacy": {
        "resident": 37482,
        "nonresident": 51582,
        "year": "2026-27",
        "source": "UW School of Pharmacy — Tuition & Financial Aid (2026-27)",
        "source_url": "https://sop.washington.edu/pharmd/admissions/tuition-and-financial-aid/",
    },
    "Doctor of Nursing Practice": {
        "resident": 35064,  # state tracks: $11,688/quarter × 3 quarters
        "nonresident": 50037,  # state tracks: $16,679/quarter × 3 quarters
        "year": "2025-26",
        "source": "UW School of Nursing — Costs (state tracks, 2025-26)",
        "source_url": "https://nursing.uw.edu/admissions/costs/",
    },
    "Doctor of Physical Therapy": {
        "resident": 27807,  # $9,269/quarter × 3 quarters
        "nonresident": 43461,  # $14,487/quarter × 3 quarters
        "year": "2025-26",
        "source": "UW Rehabilitation Medicine — Doctor of Physical Therapy (2025-26)",
        "source_url": "https://rehab.washington.edu/education/degrees/doctor-of-physical-therapy",
    },
    # "Doctor of Audiology" is intentionally absent: it bills on UW's variable graduate-tier
    # schedule and publishes no single verified annual figure, so its tuition is
    # omitted-with-reason rather than guessed.
}


# Fee-based / self-sustaining programs (UW Professional & Continuing Education + the sponsoring
# department) bill a program-specific PER-CREDIT rate that is the SAME for WA-resident, non-resident,
# and international students — NOT the state-supported Tier I sticker (which would understate them).
# Each program publishes its per-credit rate and total credits to the degree, so a real figure DOES
# exist (REPAIR_BACKLOG #1 — a knowable matcher-core field is not an honest omission): omit-never-guess
# requires the PUBLISHED number where one exists. The matcher reads program.tuition as an ANNUAL budget
# signal, so the flat program cost (per_credit × credits) is annualized over the program's published
# length (duration_months). Because the rate is residency-independent, the in-state and out-of-state
# breakdown values are equal. Verified 2026-07-01 against each program's own published cost page.
_FEE_BASED_TUITION: dict[str, dict] = {
    "uw-aerospace-engineering-ms": {
        "per_credit": 1203,
        "credits": 45,
        "year": "2025-26",
        "source": "UW William E. Boeing Dept. of Aeronautics & Astronautics — Master of Aerospace Engineering (online, fee-based)",
        "source_url": "https://www.aa.washington.edu/students/academics/mae",
    },
    "uw-applied-mathematics-ms": {
        "per_credit": 1134,
        "credits": 42,
        "year": "2025-26",
        "source": "UW Department of Applied Mathematics — Online MS in Applied & Computational Mathematics (self-sustaining, fee-based)",
        "source_url": "https://amath.washington.edu/master-science-applied-and-computational-mathematics-online",
    },
    "uw-computational-finance-and-risk-management-ms": {
        "per_credit": 1165,
        "credits": 42,
        "year": "2024-25",
        "source": "UW Computational Finance & Risk Management — MS-CFRM (self-sustaining, fee-based)",
        "source_url": "https://depts.washington.edu/compfin/cfrm-ms/",
    },
    "uw-computational-linguistics-ms": {
        "per_credit": 1058,
        "credits": 43,
        "year": "2026-27",
        "source": "UW Master of Science in Computational Linguistics (CLMS) — Costs & Aid (fee-based)",
        "source_url": "https://www.compling.uw.edu/costs-aid",
    },
    "uw-construction-management-ms": {
        "per_credit": 775,
        "credits": 42,
        "year": "2026-27",
        "source": "UW Online MS in Construction Management — Costs & Financial Aid (fee-based)",
        "source_url": "https://www.constructionmgmt.uw.edu/costs-aid",
    },
    "uw-health-administration-ms": {
        "per_credit": 950,
        "credits": 76,
        "year": "2026-27",
        "source": "UW Master of Health Administration (MHA) — Cost & Aid (fee-based)",
        "source_url": "https://hspop.uw.edu/mha/cost-aid/",
    },
    "uw-health-informatics-and-health-information-management-ms": {
        "per_credit": 990,
        "credits": 54,
        "year": "2026-27",
        "source": "UW Master of Health Informatics & Health Information Management (MHIHIM) — Cost & Aid (fee-based)",
        "source_url": "https://hspop.uw.edu/masterhihim/cost-aid/",
    },
    "uw-information-management-ms": {
        "per_credit": 1132,
        "credits": 65,
        "year": "2025-26",
        "source": "UW Information School — MSIM (Early-Career track) Tuition & Financial Aid (fee-based)",
        "source_url": "https://ischool.uw.edu/programs/msim/tuition-financial-aid",
    },
    "uw-infrastructure-planning-and-management-ms-2": {
        "per_credit": 745,
        "credits": 45,
        "year": "2026-27",
        "source": "UW Online MS in Infrastructure Planning & Management — Costs & Aid (fee-based)",
        "source_url": "https://www.infrastructure-management.uw.edu/costs-aid",
    },
    "uw-library-and-information-science-ms": {
        "per_credit": 990,
        "credits": 63,
        "year": "2026-27",
        "source": "UW Information School — MLIS Tuition & Financial Aid (fee-based)",
        "source_url": "https://ischool.uw.edu/programs/mlis/tuition-financial-aid",
    },
    "uw-mechanical-engineering-ms": {
        "per_credit": 1330,
        "credits": 42,
        "year": "2025-26",
        "source": "UW Department of Mechanical Engineering — Online MSME Costs and Fees (fee-based)",
        "source_url": "https://www.me.washington.edu/msme/tuition",
    },
    "uw-pharmaceutical-bioengineering-ms": {
        "per_credit": 908,
        "credits": 39,
        "year": "2025-26",
        "source": "UW Bioengineering — Online Master of Pharmaceutical Bioengineering, Tuition & Financial Information (fee-based)",
        "source_url": "https://bioe.uw.edu/academic-programs/masters/pharmaceutical-bioengineering/pharbe-faq/",
    },
    "uw-supply-chain-transportation-and-logistics-ms": {
        "per_credit": 1099,
        "credits": 43,
        "year": "2026-27",
        "source": "UW Online MS in Supply Chain Transportation & Logistics — Costs & Aid (fee-based)",
        "source_url": "https://www.supply-chain-transportation.uw.edu/costs-aid",
    },
    "uw-sustainable-transportation-ms": {
        "per_credit": 844,
        "credits": 43,
        "year": "2026-27",
        "source": "UW Online MS in Sustainable Transportation — Costs & Aid (fee-based)",
        "source_url": "https://www.sustainable-transportation.uw.edu/costs-aid",
    },
}


def _fee_based_years(spec: dict) -> int:
    return max(1, round((spec.get("duration_months") or 24) / 12))


def _fee_based_annual(spec: dict) -> int:
    """Flat per-credit program cost annualized over the program's published length."""
    fb = _FEE_BASED_TUITION[spec["slug"]]
    total = fb["per_credit"] * fb["credits"]
    return round(total / _fee_based_years(spec))


def _tuition_for(spec: dict) -> int | None:
    """Matcher budget scalar: UW's published annual tuition for the program's tier
    (REPAIR_BACKLOG #2 — public scalar), or None when honestly omitted."""
    # Fee-based / self-sustaining programs publish a real flat per-credit rate (residency-
    # independent), so they carry the annualized program cost — NOT an omission (REPAIR_BACKLOG #1).
    if spec["slug"] in _FEE_BASED_TUITION:
        return _fee_based_annual(spec)
    # A per-credit online program with no single published figure stays omitted-with-reason
    # rather than understated with the state-supported sticker.
    if spec.get("delivery_format") == "online":
        return None
    if spec["degree_type"] == "professional":
        pr = _PROFESSIONAL_TUITION.get(spec["program_name"])
        return pr["nonresident"] if pr else None
    if spec["degree_type"] == "bachelors":
        return _TUITION_UG_NONRES
    return _TUITION_GRAD_NONRES  # masters + phd: flat non-resident graduate Tier I sticker


def _online_cost(spec: dict) -> dict:
    """Cost record for a fee-based / self-sustaining online program.

    When the program publishes its per-credit rate + credits-to-degree (``_FEE_BASED_TUITION``),
    the flat program cost is annualized over the program's length and stamped as a real, cited
    figure (residency-independent, so in-state == out-of-state). Otherwise — a per-credit program
    with no single published figure — tuition is omitted-with-reason rather than guessed.
    """
    if spec["slug"] in _FEE_BASED_TUITION:
        fb = _FEE_BASED_TUITION[spec["slug"]]
        total = fb["per_credit"] * fb["credits"]
        years = _fee_based_years(spec)
        annual = _fee_based_annual(spec)
        return {
            "tuition_usd": annual,
            "breakdown": {
                "tuition_in_state": annual,
                "tuition_out_of_state": annual,
            },
            "funded": False,
            "note": (
                f"Self-sustaining, fee-based program (UW Professional & Continuing Education with "
                f"the sponsoring department): a flat ${fb['per_credit']:,}/credit charged to WA-"
                f"resident, non-resident, and international students alike, across {fb['credits']} "
                f"credits to the degree (${total:,} total course fees, {fb['year']}). The cost card "
                f"and the matcher budget signal (program.tuition) show this annualized over the "
                f"program's typical {years}-year length (${annual:,}/year); because the rate is "
                "residency-independent, the in-state and out-of-state breakdown values are equal. "
                "Quarterly registration, technology, and U-PASS fees are additional."
            ),
            "source": fb["source"],
            "source_url": fb["source_url"],
            "year": fb["year"],
        }
    return {
        "funded": False,
        "note": (
            "This is a fee-based / self-sustaining online program (UW Professional & Continuing "
            "Education), billed at a program-specific per-credit rate distinct from the state-"
            "supported sticker. UW publishes no single fixed credits-to-degree total for it (a "
            "variable-completion program), so a single annual figure is omitted here rather than "
            "guessed."
        ),
        "source": "UW Professional & Continuing Education — program tuition page",
        "source_url": _website_for(spec),
    }


def _undergrad_cost(spec: dict | None = None) -> dict:
    if spec is not None and spec.get("delivery_format") == "online":
        return _online_cost(spec)
    return {
        "tuition_usd": _TUITION_UG_RESIDENT,
        "total_cost_of_attendance": _UNDERGRAD_COA,
        "avg_net_price": _AVG_NET_PRICE,
        "breakdown": {
            "tuition_in_state": _TUITION_UG_RESIDENT,
            "tuition_out_of_state": _TUITION_UG_NONRES,
        },
        "funded": False,
        "note": (
            "UW is public, so two undergraduate stickers apply: WA-resident annual tuition is "
            "$13,406 and non-resident is $44,460 (UW Office of Planning & Budgeting / Financial "
            "Aid, 2025-26); both rates ship in the breakdown. The cost card shows the WA-resident "
            "basis, coherent with the College Scorecard total cost of attendance ($32,446) and "
            "average net price after grant aid ($14,091) (UNITID 236948, 2023-24). The matcher's "
            "budget signal (program.tuition) separately uses the non-resident rate — the "
            "conservative default for the out-of-state + international pool."
        ),
        # Tuition and the Scorecard COA/net-price carry separate provenance + year.
        "tuition_source": _TUITION_FA_SRC,
        "tuition_source_url": _TUITION_FA_URL,
        "tuition_year": "2025-26",
        "source": _COST_SRC,
        "source_url": _COST_SRC_URL,
        "year": "2023-24",
    }


def _grad_cost(spec: dict) -> dict:
    """Cost record for a graduate / professional program, carrying its published tuition."""
    if spec.get("delivery_format") == "online":
        return _online_cost(spec)
    if spec["degree_type"] == "professional":
        pr = _PROFESSIONAL_TUITION.get(spec["program_name"])
        if pr is None:  # Doctor of Audiology — omitted-with-reason
            return {
                "funded": False,
                "note": (
                    "The Doctor of Audiology bills on UW's variable graduate-tier tuition "
                    "schedule; UW publishes no single verified annual WA-resident figure for it, "
                    "so a tuition number is omitted here rather than guessed."
                ),
                "source": "UW Office of Planning & Budgeting / program tuition page",
                "source_url": _website_for(spec),
            }
        return {
            "tuition_usd": pr["resident"],
            "breakdown": {
                "tuition_in_state": pr["resident"],
                "tuition_out_of_state": pr["nonresident"],
            },
            "funded": False,
            "note": (
                f"Annual professional-program tuition ({pr['year']}): WA-resident "
                f"${pr['resident']:,} and non-resident ${pr['nonresident']:,}; both ship in the "
                "breakdown. The cost card shows the WA-resident rate; the matcher's budget signal "
                "(program.tuition) separately uses the non-resident rate."
            ),
            "source": pr["source"],
            "source_url": pr["source_url"],
            "year": pr["year"],
        }
    funded = spec["degree_type"] == "phd"
    return {
        "tuition_usd": _TUITION_GRAD_RESIDENT,
        "breakdown": {
            "tuition_in_state": _TUITION_GRAD_RESIDENT,
            "tuition_out_of_state": _TUITION_GRAD_NONRES,
        },
        "funded": funded,
        "note": (
            "UW is public and charges one flat graduate Tier I tuition across its state-supported "
            "master's and doctoral programs: WA-resident $19,011 and non-resident $33,171 (UW "
            "Office of Planning & Budgeting, 2025-26); both ship in the breakdown. The cost card "
            "shows the WA-resident rate; the matcher's budget signal (program.tuition) separately "
            "uses the non-resident rate for the out-of-state + international pool. Fee-based "
            "programs pay a higher published rate."
            + (
                " Most UW PhD students are funded through assistantships and fellowships that "
                "cover tuition; the published sticker is shown as the matcher's budget input."
                if funded
                else ""
            )
        ),
        "source": _TUITION_FA_SRC,
        "source_url": _TUITION_OPB_URL,
        "year": "2025-26",
    }


# == Admissions requirement sets ==
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission to an on-campus program.",
}
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Application (Coalition Application or UW application)", "required": True},
        {"name": "Personal statement and required short responses", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "$80 application fee (fee waivers available)", "required": True},
        {
            "name": "SAT/ACT scores",
            "required": False,
            "note": "UW is test-blind and does not consider SAT/ACT scores in admission.",
        },
    ],
    "deadlines": [
        {"round": "First-year application", "date": "November 15"},
    ],
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "Duolingo English Test"],
            "required": True,
            "note": "Required for applicants whose native language is not English.",
        },
        "visa": _INTL_VISA,
        "sources": [{"label": "UW Office of Admissions", "url": "https://admit.washington.edu/"}],
    },
    "source": "UW Office of Admissions",
    "source_url": "https://admit.washington.edu/",
}
_REQ_GRAD_GENERIC = {
    "materials": [
        {"name": "UW Graduate School application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Résumé / CV", "required": True},
        {
            "name": "Letters of recommendation",
            "required": True,
            "note": "Most UW graduate programs require three letters; check the program's page.",
        },
        {
            "name": "GRE/GMAT scores",
            "required": False,
            "note": "Test requirements vary by program; many UW graduate programs are test-optional or do not require the GRE/GMAT.",
        },
    ],
    "deadlines": [
        {
            "round": "Autumn admission",
            "date": "Deadlines vary by program (typically December–January)",
        }
    ],
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": True,
            "note": "Required for applicants whose native language is not English.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {"label": "UW Graduate School — admissions", "url": "https://grad.uw.edu/admissions/"}
        ],
    },
    "source": "UW Graduate School",
    "source_url": "https://grad.uw.edu/admissions/",
}


def _requirements_for(spec: dict) -> dict:
    if spec["degree_type"] == "bachelors":
        return _REQ_UNDERGRAD
    return _REQ_GRAD_GENERIC


_OUTCOMES_BY_SLUG: dict[str, dict] = {}
_OUTCOMES_OMIT_BY_SLUG: dict[str, list[str]] = {}
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {}
_FACULTY_BY_SLUG: dict[str, dict] = {
    "uw-computer-science-bs": {
        "lead": "The B.S. in Computer Science is taught by the faculty of the Paul G. Allen School of Computer Science & Engineering.",
        "directory_url": "https://www.cs.washington.edu/people/faculty",
    },
    "uw-medicine-prof": {
        "lead": "The M.D. is taught by UW School of Medicine faculty across the basic sciences and the five-state WWAMI clinical network.",
        "directory_url": "https://www.uwmedicine.org/school-of-medicine",
    },
    "uw-nursing-practice-prof": {
        "lead": "The DNP is taught by UW School of Nursing faculty with clinical placements across the UW Medicine system.",
        "directory_url": "https://nursing.uw.edu/faculty/",
    },
    "uw-business-administration-ms": {
        "lead": "The Foster MBA is taught by University of Washington Foster School of Business faculty.",
        "directory_url": "https://foster.uw.edu/faculty-research/directory/",
    },
}

_REVIEWS_BY_SLUG: dict[str, dict] = {
    "uw-computer-science-bs": {
        "summary": "The Paul G. Allen School undergraduate computer science program is one of the strongest in the country (U.S. News ranks UW computer science a tie for #7 nationally). Reviewers cite world-class faculty, deep ties to Seattle's tech industry (Microsoft, Amazon, and a large startup scene), and excellent placement, while noting that direct admission and the upper-division major are highly competitive.",
        "themes": [
            {
                "label": "Top-10 computer science",
                "sentiment": "positive",
                "detail": "U.S. News ranks UW computer science a tie for #7 nationally; the Allen School is a recognized leader in AI, systems, and theory.",
            },
            {
                "label": "Industry adjacency",
                "sentiment": "positive",
                "detail": "Seattle's concentration of Microsoft, Amazon, and startups drives internships, research collaboration, and hiring.",
            },
            {
                "label": "Strong placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into top software, AI, and research roles and competitive graduate programs.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Direct freshman admission and the capacity-constrained major are highly selective; not all applicants are admitted to the major.",
            },
        ],
        "sources": [
            {
                "label": "Paul G. Allen School of Computer Science & Engineering",
                "url": "https://www.cs.washington.edu/",
            },
            {"label": "UW News — U.S. News rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-computer-science-and-engineering-ms": {
        "summary": "The Allen School's graduate computer science programs are top-tier (U.S. News ranks UW computer science a tie for #7), with strengths spanning machine learning, systems, programming languages, HCI, and computational biology. Reviewers praise the research environment and industry partnerships, while noting that doctoral admission is extremely competitive and the professional master's is industry-oriented.",
        "themes": [
            {
                "label": "Elite research program",
                "sentiment": "positive",
                "detail": "UW computer science is a tie for #7 nationally, with leading groups in AI/ML, systems, and theory.",
            },
            {
                "label": "Funding and labs",
                "sentiment": "positive",
                "detail": "Doctoral students are typically funded through research/teaching assistantships with access to strong labs.",
            },
            {
                "label": "Industry partnership",
                "sentiment": "positive",
                "detail": "Close ties to Seattle's tech sector support research and placement.",
            },
            {
                "label": "Highly selective",
                "sentiment": "caution",
                "detail": "Ph.D. admission is very competitive; the professional master's (PMP) is part-time and industry-focused.",
            },
        ],
        "sources": [
            {
                "label": "Paul G. Allen School — graduate programs",
                "url": "https://www.cs.washington.edu/academics/grad",
            },
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-medicine-prof": {
        "summary": "The UW School of Medicine is consistently ranked #1 in the nation for primary care, family medicine, and rural medicine by U.S. News, anchored by the five-state WWAMI program (Washington, Wyoming, Alaska, Montana, Idaho). Reviewers cite outstanding primary-care and community training and research strength, while noting the distributed, travel-intensive WWAMI model and competitive admission. (UW has withdrawn from U.S. News' ranking participation, but its primary-care reputation is long established.)",
        "themes": [
            {
                "label": "#1 primary care",
                "sentiment": "positive",
                "detail": "U.S. News has repeatedly ranked UW School of Medicine #1 for primary care, family medicine, and rural medicine.",
            },
            {
                "label": "WWAMI regional model",
                "sentiment": "positive",
                "detail": "The five-state WWAMI program delivers medical education across WA, WY, AK, MT, and ID with strong community and rural training.",
            },
            {
                "label": "Research strength",
                "sentiment": "positive",
                "detail": "UW Medicine is a major NIH-funded research enterprise with leading clinical and basic science.",
            },
            {
                "label": "Distributed, demanding",
                "sentiment": "caution",
                "detail": "The regional model can involve travel across sites; admission is highly competitive.",
            },
            {
                "label": "Ranking participation",
                "sentiment": "mixed",
                "detail": "UW Medicine has stepped back from U.S. News ranking participation, as several medical schools have.",
            },
        ],
        "sources": [
            {
                "label": "UW School of Medicine",
                "url": "https://www.uwmedicine.org/school-of-medicine",
            },
            {
                "label": "WWAMI Regional Medical Education Program",
                "url": "https://www.uwmedicine.org/education/md-program/wwami",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-nursing-practice-prof": {
        "summary": "The UW School of Nursing is among the very best in the country — U.S. News has ranked its programs #1, and the Doctor of Nursing Practice (DNP) is consistently top-ranked (a tie for #1 among public schools). Reviewers cite outstanding faculty, research, and clinical placements in the Seattle health system, while noting the rigor and clinical-hour demands of the DNP.",
        "themes": [
            {
                "label": "Top-ranked nursing",
                "sentiment": "positive",
                "detail": "UW nursing is repeatedly ranked among the nation's best by U.S. News, with a top-ranked DNP.",
            },
            {
                "label": "Clinical access",
                "sentiment": "positive",
                "detail": "Students train across UW Medicine, Seattle Children's, and regional partners.",
            },
            {
                "label": "Research and faculty",
                "sentiment": "positive",
                "detail": "Strong NIH-funded research and renowned faculty support advanced practice and scholarship.",
            },
            {
                "label": "Rigorous and demanding",
                "sentiment": "caution",
                "detail": "The DNP is intensive, with substantial clinical hours and competitive admission.",
            },
        ],
        "sources": [
            {
                "label": "UW School of Nursing — DNP",
                "url": "https://nursing.uw.edu/program/doctor-of-nursing-practice/",
            },
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-library-and-information-science-ms": {
        "summary": "The UW Information School's Master of Library and Information Science is among the nation's top LIS programs (U.S. News ranks the iSchool's library/information studies a tie for #1), offered on campus and online. Reviewers praise its breadth across data, youth services, archives, and user experience and strong placement, while noting that pay varies by sector.",
        "themes": [
            {
                "label": "#1-ranked LIS",
                "sentiment": "positive",
                "detail": "U.S. News ranks the UW iSchool's library and information studies a tie for #1 nationally.",
            },
            {
                "label": "Flexible delivery",
                "sentiment": "positive",
                "detail": "The MLIS is offered residential and fully online, with concentrations in data, youth, and academic/public libraries.",
            },
            {
                "label": "Strong placement",
                "sentiment": "positive",
                "detail": "Graduates enter libraries, archives, data curation, and information/UX roles.",
            },
            {
                "label": "Sector-dependent pay",
                "sentiment": "caution",
                "detail": "Salaries vary widely between tech/data and public-library sectors.",
            },
        ],
        "sources": [
            {"label": "UW iSchool — MLIS", "url": "https://ischool.uw.edu/programs/mlis"},
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-business-administration-ms": {
        "summary": "The Foster School of Business MBA is a well-regarded program (a U.S. News top-30 full-time MBA) with strong regional pull into Seattle's technology and consulting employers. Reviewers cite excellent tech placement (Amazon, Microsoft, and others), a collaborative culture, and strong value, while noting a smaller class size and a regional (Pacific Northwest) recruiting concentration.",
        "themes": [
            {
                "label": "Top-30 MBA",
                "sentiment": "positive",
                "detail": "Foster's full-time MBA ranks among the nation's best by U.S. News, with standout information-systems and analytics strengths.",
            },
            {
                "label": "Tech placement",
                "sentiment": "positive",
                "detail": "Proximity to Amazon, Microsoft, and a deep tech ecosystem drives strong product, tech, and consulting placement.",
            },
            {
                "label": "Collaborative culture",
                "sentiment": "positive",
                "detail": "Reviewers describe a tight-knit, supportive cohort and accessible faculty.",
            },
            {
                "label": "Regional concentration",
                "sentiment": "caution",
                "detail": "Recruiting skews to the Pacific Northwest; students targeting other regions should network early.",
            },
        ],
        "sources": [
            {
                "label": "Foster School of Business — MBA",
                "url": "https://foster.uw.edu/academics/degree-programs/full-time-mba/",
            },
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-law-prof": {
        "summary": "The UW School of Law is a respected public law school (a U.S. News top-50 program) known for strong value, public-interest and technology-law strengths, and solid placement into the Seattle and Pacific Northwest legal markets. Reviewers cite affordability relative to private peers and a collegial culture, while noting the demands of law school and a regionally focused job market.",
        "themes": [
            {
                "label": "Strong public-law value",
                "sentiment": "positive",
                "detail": "A U.S. News top-50 law school offering strong legal education at public tuition.",
            },
            {
                "label": "Regional placement",
                "sentiment": "positive",
                "detail": "Graduates place well into Seattle and Pacific Northwest firms, government, and tech legal roles.",
            },
            {
                "label": "Specialty strengths",
                "sentiment": "positive",
                "detail": "Notable strengths in intellectual property/technology law, tax, and global/Asian law.",
            },
            {
                "label": "Rigorous, regional market",
                "sentiment": "caution",
                "detail": "The workload is demanding and recruiting concentrates in the Pacific Northwest.",
            },
        ],
        "sources": [
            {"label": "UW School of Law — J.D.", "url": "https://www.law.uw.edu/academics/jd"},
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-pharmacy-prof": {
        "summary": "The UW School of Pharmacy's PharmD is among the nation's top pharmacy programs (a U.S. News top-15, and among the highest-ranked public schools), with strengths in pharmaceutical sciences, pharmacy practice, and health-economics research. Reviewers cite strong clinical training and research, while noting that pharmacy education is lengthy and competitive.",
        "themes": [
            {
                "label": "Top-ranked pharmacy",
                "sentiment": "positive",
                "detail": "U.S. News ranks the UW PharmD among the nation's top pharmacy programs (top-15, leading public schools).",
            },
            {
                "label": "Research and practice",
                "sentiment": "positive",
                "detail": "Strengths span pharmaceutics, medicinal chemistry, and pharmaceutical outcomes/health economics.",
            },
            {
                "label": "Clinical training",
                "sentiment": "positive",
                "detail": "Students train across UW Medicine and regional clinical sites.",
            },
            {
                "label": "Long and competitive",
                "sentiment": "caution",
                "detail": "The PharmD is a multi-year professional program with competitive admission.",
            },
        ],
        "sources": [
            {
                "label": "UW School of Pharmacy — PharmD",
                "url": "https://sop.washington.edu/pharmd/",
            },
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-social-work-ms": {
        "summary": "The UW School of Social Work is among the nation's best (U.S. News ranks its MSW a tie for #7), with strengths in clinical practice, community-centered and anti-racist practice, and behavioral-health research. Reviewers cite strong field placements across the Seattle region and influential faculty, while noting heavy field-hour requirements and the pay realities of the social-work field.",
        "themes": [
            {
                "label": "Top-10 social work",
                "sentiment": "positive",
                "detail": "U.S. News ranks the UW MSW a tie for #7 nationally.",
            },
            {
                "label": "Field placements",
                "sentiment": "positive",
                "detail": "Extensive practicum placements across health, child-welfare, and community organizations.",
            },
            {
                "label": "Research and equity focus",
                "sentiment": "positive",
                "detail": "Strong research and an explicit social-justice and anti-racist practice orientation.",
            },
            {
                "label": "Field hours and pay",
                "sentiment": "caution",
                "detail": "The MSW requires substantial field hours, and social-work salaries vary by sector.",
            },
        ],
        "sources": [
            {
                "label": "UW School of Social Work — MSW",
                "url": "https://socialwork.uw.edu/programs/msw",
            },
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-bioengineering-ms": {
        "summary": "UW Bioengineering (a joint department of the Colleges of Engineering and the School of Medicine) is a top program (U.S. News ranks UW biomedical/bioengineering among the nation's best), with strengths in molecular/cellular engineering, imaging, neural engineering, and regenerative medicine. Reviewers highlight strong faculty and translational research with UW Medicine, while noting the program's rigor and selective admission.",
        "themes": [
            {
                "label": "Top bioengineering",
                "sentiment": "positive",
                "detail": "U.S. News ranks UW bioengineering among the nation's leading programs; it is jointly run with the School of Medicine.",
            },
            {
                "label": "Translational research",
                "sentiment": "positive",
                "detail": "Strong ties to UW Medicine and the Institute for Protein Design support translational work.",
            },
            {
                "label": "Strengths",
                "sentiment": "positive",
                "detail": "Areas include molecular engineering, imaging, neural engineering, and biomaterials.",
            },
            {
                "label": "Rigorous and selective",
                "sentiment": "caution",
                "detail": "The curriculum is demanding and admission is competitive.",
            },
        ],
        "sources": [
            {"label": "UW Department of Bioengineering", "url": "https://bioe.uw.edu/"},
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-aeronautics-and-astronautics-ms": {
        "summary": "UW Aeronautics & Astronautics is a strong, research-active department (William E. Boeing Department) with close ties to the Pacific Northwest aerospace industry, including Boeing and Blue Origin. Reviewers cite strong fluid dynamics, controls, structures, and plasma/space research and excellent regional placement, while noting the field's cyclicality and competitive admission.",
        "themes": [
            {
                "label": "Aerospace strength",
                "sentiment": "positive",
                "detail": "The Boeing Department offers strong research across aerodynamics, controls, structures, and plasma/space.",
            },
            {
                "label": "Industry adjacency",
                "sentiment": "positive",
                "detail": "Proximity to Boeing, Blue Origin, and a deep aerospace cluster drives internships and hiring.",
            },
            {
                "label": "Research breadth",
                "sentiment": "positive",
                "detail": "Active groups span computational fluid dynamics, combustion, and space systems.",
            },
            {
                "label": "Cyclical field",
                "sentiment": "caution",
                "detail": "Aerospace hiring can be cyclical, and graduate admission is competitive.",
            },
        ],
        "sources": [
            {
                "label": "UW William E. Boeing Department of Aeronautics & Astronautics",
                "url": "https://www.aa.washington.edu/",
            },
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-civil-engineering-ms": {
        "summary": "UW Civil & Environmental Engineering is a well-regarded department (a U.S. News top-25 graduate program) with strengths in structural and earthquake engineering, transportation, water/environment, and construction. Reviewers cite strong faculty and regional placement and online options for working professionals, while noting the demanding curriculum.",
        "themes": [
            {
                "label": "Top-25 program",
                "sentiment": "positive",
                "detail": "U.S. News ranks UW civil engineering among the nation's top graduate programs.",
            },
            {
                "label": "Strengths",
                "sentiment": "positive",
                "detail": "Notable in structural/earthquake engineering, transportation, water resources, and construction management.",
            },
            {
                "label": "Flexible options",
                "sentiment": "positive",
                "detail": "Several master's tracks are offered online for working professionals.",
            },
            {
                "label": "Demanding curriculum",
                "sentiment": "caution",
                "detail": "Graduate coursework is rigorous and admission is competitive.",
            },
        ],
        "sources": [
            {
                "label": "UW Civil & Environmental Engineering",
                "url": "https://www.ce.washington.edu/",
            },
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-statistics-bs": {
        "summary": "UW Statistics is a strong, in-demand program with leading research in machine learning, Bayesian methods, and statistical computing, and close ties to the Allen School and eScience Institute. Reviewers cite excellent placement into data-science and analytics roles and rigorous training, while noting that popular courses can be large and competitive.",
        "themes": [
            {
                "label": "Strong, in-demand",
                "sentiment": "positive",
                "detail": "UW statistics has grown with data-science demand and is research-active in ML and Bayesian methods.",
            },
            {
                "label": "Computational focus",
                "sentiment": "positive",
                "detail": "Coursework emphasizes statistical computing, probability, and applied data analysis.",
            },
            {
                "label": "Excellent placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into data-science, analytics, and quantitative roles, including Seattle's tech sector.",
            },
            {
                "label": "Large, competitive courses",
                "sentiment": "caution",
                "detail": "Popular statistics/data courses can be large and entry to some tracks is competitive.",
            },
        ],
        "sources": [
            {"label": "UW Department of Statistics", "url": "https://stat.uw.edu/"},
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-economics-phd": {
        "summary": "UW Economics is a highly regarded research department (U.S. News ranks it among the nation's top economics programs), with strengths in econometrics, microeconomics, and applied fields. Reviewers cite strong faculty and placement into academia, government, and industry, while noting that doctoral admission is very competitive and the program is quantitatively demanding.",
        "themes": [
            {
                "label": "Top economics program",
                "sentiment": "positive",
                "detail": "U.S. News ranks UW economics among the nation's leading departments.",
            },
            {
                "label": "Research strengths",
                "sentiment": "positive",
                "detail": "Notable in econometrics, microeconomics, and applied economics.",
            },
            {
                "label": "Placement",
                "sentiment": "positive",
                "detail": "Graduates place into academia, government, central banks, and industry research.",
            },
            {
                "label": "Quantitative and selective",
                "sentiment": "caution",
                "detail": "The Ph.D. is mathematically demanding and admission is highly competitive.",
            },
        ],
        "sources": [
            {"label": "UW Department of Economics", "url": "https://econ.washington.edu/"},
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-oceanography-bs": {
        "summary": "UW's College of the Environment is a global leader in the earth and ocean sciences (U.S. News ranks UW earth sciences among the nation's best), and oceanography benefits from the research vessel fleet, marine facilities, and proximity to Puget Sound and the Pacific. Reviewers cite outstanding field and research opportunities, while noting that the field is research-oriented and competitive for graduate study.",
        "themes": [
            {
                "label": "Top earth/ocean science",
                "sentiment": "positive",
                "detail": "UW is consistently ranked among the nation's best in the earth and ocean sciences.",
            },
            {
                "label": "Field and fleet access",
                "sentiment": "positive",
                "detail": "Students access research vessels, marine labs, and Puget Sound/Pacific field sites.",
            },
            {
                "label": "Research opportunities",
                "sentiment": "positive",
                "detail": "Strong undergraduate research and ties to NOAA and oceanographic institutions.",
            },
            {
                "label": "Research-oriented",
                "sentiment": "caution",
                "detail": "Career paths often involve graduate study; the field is competitive.",
            },
        ],
        "sources": [
            {
                "label": "UW College of the Environment — Oceanography",
                "url": "https://www.ocean.washington.edu/",
            },
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
}

# Synthesized batch reviews removed (2026-06-18 de-fabrication). Coverable flagships below;
# remaining programs record external_reviews in _standard.omitted pending genuine coverage.


def _program_standard(slug: str, spec: dict) -> dict:
    # Every program now carries UW's published tuition (state-supported sticker, bespoke
    # professional rate, or fee-based per-credit rate) EXCEPT two: the Doctor of Audiology
    # (variable graduate-tier schedule, no single published annual figure) and the online BA in
    # Integrated Social Sciences (per-credit degree-completion, no fixed credits-to-degree total)
    # — tuition is omitted-with-reason only for those two.
    omitted: list[str] = []
    if _tuition_for(spec) is None:
        omitted.append("cost_data.tuition_usd")
    if not spec.get("cip"):
        omitted.append("cip_code")
    if slug not in _TRACKS_BY_SLUG:
        omitted.append("tracks")
    if slug not in _OUTCOMES_BY_SLUG:
        omitted += [
            "outcomes_data.employment_rate",
            "outcomes_data.median_salary",
            "outcomes_data.top_industries",
            "outcomes_data.conditions",
            "outcomes_data.source",
        ]
    else:
        omitted += _OUTCOMES_OMIT_BY_SLUG.get(slug, [])
    if (
        slug not in _CLASS_PROFILE_BY_SLUG
        or _CLASS_PROFILE_BY_SLUG.get(slug, {}).get("cohort_size") is None
    ):
        omitted.append("class_profile.cohort_size")
    if slug not in _FACULTY_BY_SLUG:
        omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    return _standard(omitted)


# ── who_its_for (REPAIR_BACKLOG #3) — a PROGRAM-DISTINCT, field-specific audience
# statement for every program (gold pattern: distinct/total == 1.0). Derived from each
# program's real field + credential level; no fabricated rankings/stats/named entities.
# Replaces the former hard-null ``p.who_its_for = None`` that shipped the field 0% live.
_WHO_BY_SLUG: dict[str, str] = {
    "uw-american-ethnic-studies-bs": (
        "Undergraduates who want to examine how race, ethnicity, and nation shape power in the United "
        "States will find their footing here. It suits students drawn to questions of identity and "
        "justice who plan to bring that analysis into law, education, advocacy, or community work."
    ),
    "uw-american-indian-studies-bs": (
        "Undergraduates curious about the histories, politics, and contemporary lives of Native "
        "peoples in North America belong in this interdisciplinary major. It fits students who want "
        "to study sovereignty, culture, and lived experience, and who may carry that grounding into "
        "tribal governance, education, or public service."
    ),
    "uw-american-music-bs": (
        "Undergraduates who hear the country's many cultures in its music — Indigenous, West African, "
        "European, Latin American, and beyond — will thrive in this major. It suits curious listeners "
        "and players who want to study how American styles formed and influenced one another."
    ),
    "uw-anthropology-bs": (
        "Undergraduates fascinated by what makes us human, across biology, culture, language, and the "
        "deep past, will find a wide home here. It fits students drawn to fieldwork and cross- "
        "cultural comparison who want to understand human behavior in both present and ancient "
        "societies."
    ),
    "uw-applied-and-computational-math-sciences-bs": (
        "Undergraduates who enjoy turning real-world problems into mathematical models and solving "
        "them computationally will fit this major. It suits students comfortable pairing rigorous "
        "math with programming who want to apply both to scientific, engineering, or industry "
        "questions."
    ),
    "uw-applied-mathematics-bs": (
        "Undergraduates who want to use mathematics to tackle problems in physics, engineering, "
        "biology, finance, and beyond will find their place here. It fits students who prefer math "
        "aimed at real applications and scientific computing over purely abstract theory."
    ),
    "uw-art-bs": (
        "Undergraduates with creative drive who want to develop their craft and a personal visual "
        "voice will find room to grow here. It suits students ready to build technical skill and "
        "conceptual depth through sustained studio practice and critique."
    ),
    "uw-art-history-bs": (
        "Undergraduates drawn to looking closely at art and visual culture across time and place will "
        "fit this major. It suits readers and lookers curious about how images carry meaning, with "
        "interests that may lead toward museums, curation, or graduate study."
    ),
    "uw-asian-languages-and-cultures-bs": (
        "Undergraduates eager to study the languages, histories, and cultures of Asia will find a "
        "strong foundation here. It fits students ready to build genuine language proficiency "
        "alongside cultural and political understanding, whether for research, diplomacy, or work "
        "across borders."
    ),
    "uw-astronomy-bs": (
        "Undergraduates captivated by celestial objects and the workings of the cosmos will find this "
        "major a natural fit. It suits students comfortable with physics and mathematics who want to "
        "study the universe and may continue toward research or graduate work."
    ),
    "uw-biochemistry-bs": (
        "Undergraduates who want to understand the chemistry of living systems, from proteins to "
        "metabolism, will fit this major. It suits students at home in both chemistry and biology, "
        "often with their sights on biomedical research, graduate school, or health professions."
    ),
    "uw-biology-bs": (
        "Undergraduates curious about life across every scale, from cells to ecosystems and "
        "evolution, will find a broad foundation here. It suits students who enjoy both lab and "
        "conceptual work and who may head toward research, healthcare, or conservation."
    ),
    "uw-chemistry-bs": (
        "Undergraduates who want to understand matter — its composition, structure, and the reactions "
        "it undergoes — will fit this major. It suits students who enjoy the lab and the problem- "
        "solving behind it, often building toward research, industry, or the health sciences."
    ),
    "uw-chinese-bs": (
        "Undergraduates committed to genuine fluency in Chinese and to the cultures of the Sinitic- "
        "speaking world will find their path here. It fits students ready for serious language study "
        "who want to read, speak, and engage across literature, history, and contemporary life."
    ),
    "uw-cinema-and-media-studies-bs": (
        "Undergraduates who want to think critically about film and media as art forms and cultural "
        "forces will fit this major. It suits curious viewers interested in theory, history, and "
        "analysis rather than primarily production."
    ),
    "uw-classical-studies-bs": (
        "Undergraduates drawn to the literature, history, and thought of ancient Greece and Rome will "
        "find a rich major here. It suits students who enjoy reading deeply across the ancient world "
        "and want a broad grounding in classical antiquity."
    ),
    "uw-classics-bs": (
        "Undergraduates ready to study ancient Greek and Latin in the original, alongside the "
        "literature they open up, will fit this major. It suits language-loving students who want to "
        "read foundational texts firsthand and think carefully about the ancient world."
    ),
    "uw-communication-bs": (
        "Undergraduates interested in how information and meaning move through media, institutions, "
        "and everyday interaction will fit this major. It suits students curious about messages and "
        "their effects who may aim toward journalism, public relations, policy, or research."
    ),
    "uw-comparative-history-of-ideas-bs": (
        "Undergraduates who like to follow ideas across disciplines and traditions will find an "
        "unusually open major here. It suits independent thinkers who want to connect philosophy, "
        "history, and culture and design inquiry around the questions that move them."
    ),
    "uw-comparative-literature-bs": (
        "Undergraduates who read widely across languages and national traditions will fit this major. "
        "It suits students drawn to literature beyond a single culture, comfortable thinking across "
        "linguistic and disciplinary boundaries about how texts speak to one another."
    ),
    "uw-comparative-religion-bs": (
        "Undergraduates curious about the world's religious traditions and how to compare their "
        "beliefs, practices, and impact will fit this major. It suits students who want to study "
        "religion analytically and across cultures rather than from within a single faith."
    ),
    "uw-composition-bs": (
        "Undergraduates who want to create original music and master how a piece is built will find "
        "their place here. It suits students with musical grounding who are ready to develop their "
        "craft as writers of vocal and instrumental work."
    ),
    "uw-computational-finance-and-risk-management-bs": (
        "Undergraduates who want to bring data, algorithms, and quantitative models to financial "
        "decisions will fit this major. It suits students comfortable with mathematics and "
        "programming who aim toward quantitative finance, risk analysis, or related industry roles."
    ),
    "uw-computer-science-bs": (
        "Undergraduates who want to build software and understand the ideas beneath it — algorithms, "
        "systems, machine learning, and how people use technology — will fit this major. It suits "
        "problem-solvers ready for rigorous study who plan to design, research, or engineer "
        "computing."
    ),
    "uw-dance-bs": (
        "Undergraduates who express themselves through movement and want to develop as artists will "
        "find room here. It suits dedicated dancers ready to deepen technique, choreography, and the "
        "study of dance as an art form."
    ),
    "uw-danish-bs": (
        "Undergraduates drawn to Danish language and the culture of Scandinavia will fit this focused "
        "major. It suits students who want real proficiency and a window into Nordic literature, "
        "history, and society, whether for study abroad, research, or work in the region."
    ),
    "uw-drama-bs": (
        "Undergraduates passionate about theatre — acting, directing, and the craft of production — "
        "will find their stage here. It suits students ready for hands-on training and collaboration "
        "who want to study performance as both art and discipline."
    ),
    "uw-eastern-european-languages-literature-and-culture-bs": (
        "Undergraduates curious about the languages, literatures, and histories of Eastern Europe "
        "will fit this major. It suits students drawn to a region rich in cultural and political "
        "complexity who want language skill alongside cultural understanding."
    ),
    "uw-economics-bs": (
        "Undergraduates who want to understand how societies produce, distribute, and consume "
        "resources will fit this major. It suits analytically minded students interested in markets, "
        "policy, and human behavior who may head toward business, government, research, or graduate "
        "study."
    ),
    "uw-english-bs": (
        "Undergraduates who love reading closely and writing well will find a wide home in this "
        "major. It suits students drawn to literature, language, and interpretation who want to "
        "sharpen their analysis and prose across many genres and periods."
    ),
    "uw-ethnomusicology-bs": (
        "Undergraduates fascinated by music as a window into culture will fit this interdisciplinary "
        "major. It suits students curious about how music functions socially and across societies, "
        "blending fieldwork and analysis to study sound in its human context."
    ),
    "uw-finnish-bs": (
        "Undergraduates drawn to the Finnish language and the culture of Finland will fit this "
        "focused major. It suits students ready for serious language study and a deeper look at "
        "Finnish literature, history, and society."
    ),
    "uw-french-bs": (
        "Undergraduates who want fluency in French and a grounding in the cultures it spans will fit "
        "this major. It suits students ready to read, speak, and write at depth, with interests that "
        "may lead toward study abroad, teaching, or international work."
    ),
    "uw-gender-women-and-sexuality-studies-bs": (
        "Undergraduates who want to examine gender, sexuality, and the systems of power that shape "
        "them will fit this interdisciplinary major. It suits students drawn to feminist and "
        "intersectional analysis who plan to carry it into advocacy, policy, healthcare, or research."
    ),
    "uw-geography-bs": (
        "Undergraduates curious about places, people, and the forces that change them will fit this "
        "major. It suits students interested in mapping, spatial analysis, and the link between human "
        "and natural systems, often building skills like GIS and remote sensing."
    ),
    "uw-german-studies-bs": (
        "Undergraduates drawn to the German language and its literature, culture, and history will "
        "fit this major. It suits students ready to build real proficiency and engage critically with "
        "German-speaking Europe, past and present."
    ),
    "uw-global-literary-studies-bs": (
        "Undergraduates who want to read literature across nations, languages, and cultures will fit "
        "this major. It suits students drawn to a global view of writing who like comparing works and "
        "traditions that cross borders."
    ),
    "uw-greek-bs": (
        "Undergraduates ready to study Ancient Greek and read its foundational texts in the original "
        "will fit this major. It suits language-loving students fascinated by the literature, "
        "thought, and world of ancient Greece."
    ),
    "uw-guitar-bs": (
        "Undergraduates who want to develop seriously as guitarists will find their focus here. It "
        "suits committed players ready to deepen technique, musicianship, and repertoire through "
        "dedicated performance study."
    ),
    "uw-history-bs": (
        "Undergraduates who want to understand the past and how evidence becomes narrative will fit "
        "this major. It suits curious readers and writers drawn to analyzing why events unfolded as "
        "they did, across regions from the Pacific Northwest to the wider world."
    ),
    "uw-history-and-philosophy-of-science-bs": (
        "Undergraduates drawn to the big questions behind science itself — how knowledge gets made, "
        "tested, and revised — will find their footing here. It suits curious thinkers who want to "
        "pair scientific literacy with historical context and philosophical reasoning rather than "
        "bench work alone."
    ),
    "uw-individualized-studies-bs": (
        "Undergraduates whose interests cut across sociology, anthropology, psychology, economics, "
        "and beyond, and who don't see themselves in a single named major, can design a coherent path "
        "here. It rewards self-directed students ready to justify their own course of study."
    ),
    "uw-industrial-design-bs": (
        "Undergraduates who want to shape the physical products people use every day — sketching, "
        "prototyping, and thinking through how things get manufactured at scale — will feel at home. "
        "It fits makers who care equally about form, function, and how an object reaches mass "
        "production."
    ),
    "uw-integrated-social-sciences-bs": (
        "Built for working adults and transfer students who need a fully online path, this degree "
        "suits undergraduates studying how societies and relationships work but who require "
        "flexibility around job or family commitments. Self-motivated remote learners thrive here."
    ),
    "uw-interaction-design-bs": (
        "Undergraduates fascinated by how people behave with digital products, environments, and "
        "services — and who want to design that behavior, not just the look — will find their fit. It "
        "suits students who pair an interest in form with applied, research-minded inquiry."
    ),
    "uw-international-studies-bs": (
        "Undergraduates who follow global politics, cross-border relationships, and how nations and "
        "institutions interact belong here. It suits students preparing for diplomacy, policy, "
        "development, or global work, and those who want to read the world through more than one "
        "region or language."
    ),
    "uw-italian-bs": (
        "Undergraduates drawn to the Italian language and the literary and cultural world of Italy "
        "will find a place to build real fluency. It suits students who want to read closely, study a "
        "Romance language with deep roots in Latin, and connect language to history and the arts."
    ),
    "uw-japanese-bs": (
        "Undergraduates committed to mastering Japanese and engaging seriously with Japan's culture, "
        "literature, and society will thrive here. It fits students ready for the sustained practice "
        "a language of this depth requires, whether for research, work abroad, or cultural study."
    ),
    "uw-jazz-studies-bs": (
        "Undergraduate musicians who hear themselves in improvisation, ensemble playing, and the "
        "African-American roots of jazz will find their community. It suits performers ready to study "
        "the tradition seriously while developing their own voice on stage and in the practice room."
    ),
    "uw-korean-bs": (
        "Undergraduates set on speaking, reading, and understanding Korean — and on engaging with the "
        "cultures of the Korean peninsula — belong here. It fits students prepared to commit to a "
        "language with a growing global reach, whether for research, work, or heritage connection."
    ),
    "uw-latin-bs": (
        "Undergraduates captivated by the classical world and the language that shaped so much of "
        "Western literature and thought will find rigor and reward here. It suits students who enjoy "
        "careful translation, grammar, and reading the texts of the ancient Roman world in the "
        "original."
    ),
    "uw-law-societies-and-justice-bs": (
        "Undergraduates interested in how law, society, and justice intersect — and in the social "
        "forces behind legal systems — will find their footing. It suits students weighing law "
        "school, policy, or advocacy who want to study the law critically rather than memorize it."
    ),
    "uw-linguistics-bs": (
        "Undergraduates who treat language as a puzzle to analyze — sound systems, sentence "
        "structure, meaning, and how languages are documented — belong here. It suits scientifically "
        "minded students curious about how human language actually works, not just how to speak one."
    ),
    "uw-mathematics-bs": (
        "Undergraduates who enjoy abstraction and proof — numbers, shapes, functions, probability — "
        "and want the flexibility of a Bachelor of Arts track will find their place. It suits "
        "students pairing mathematical reasoning with other interests rather than aiming purely at "
        "theory."
    ),
    "uw-microbiology-bs": (
        "Undergraduates fascinated by the unseen world of bacteria, viruses, and other microorganisms "
        "— and how they shape health and ecosystems — will thrive here. It fits students who like "
        "laboratory science and want a foundation for research, medicine, or biotech."
    ),
    "uw-middle-eastern-languages-and-cultures-bs": (
        "Undergraduates drawn to the languages, histories, and cultures of the Middle East — its "
        "politics, literatures, and societies — belong here. It suits students ready to study a "
        "region in depth, often building language skills alongside cultural and historical "
        "understanding."
    ),
    "uw-music-bs": (
        "Undergraduate musicians and listeners who want a broad foundation in performance, history, "
        "and musicianship will find a flexible home. It suits students exploring music seriously "
        "across genres before committing to a single instrument or specialty."
    ),
    "uw-music-education-bs": (
        "Undergraduates who want to teach music in schools — leading ensembles and shaping young "
        "musicians — belong here. It fits students drawn equally to musicianship and to the "
        "classroom, preparing for careers as elementary or secondary music teachers and directors."
    ),
    "uw-music-theory-bs": (
        "Undergraduates who want to understand how music works under the surface — its structures, "
        "patterns, and the frameworks composers use — will find their fit. It suits analytically "
        "minded musicians who enjoy dissecting scores as much as performing them."
    ),
    "uw-neuroscience-bs": (
        "Undergraduates curious about the brain and nervous system — how they function and what "
        "happens when they don't — belong here. It fits students drawn to the biology of behavior and "
        "cognition who want a foundation for research, medicine, or graduate study."
    ),
    "uw-norwegian-bs": (
        "Undergraduates eager to learn Norwegian and explore the culture and society of Norway will "
        "find a focused path. It suits students interested in Nordic life, literature, and a North "
        "Germanic language, whether for heritage, study abroad, or comparative cultural work."
    ),
    "uw-orchestral-instruments-bs": (
        "Undergraduate instrumentalists aiming to perform in orchestral and ensemble settings will "
        "find serious training here. It suits dedicated players ready to refine their craft on their "
        "instrument while developing the musicianship that ensemble performance demands."
    ),
    "uw-organ-bs": (
        "Undergraduate keyboardists drawn specifically to the organ — its vast range, repertoire, and "
        "place in sacred and concert music — belong here. It fits committed players ready for the "
        "technical and musical demands of this distinctive instrument."
    ),
    "uw-percussion-bs": (
        "Undergraduate percussionists who thrive across the wide world of struck, scraped, and mallet "
        "instruments will find their place. It suits versatile players ready to build technique and "
        "musicianship for orchestral, ensemble, and solo performance."
    ),
    "uw-philosophy-bs": (
        "Undergraduates who like to reason carefully about existence, knowledge, ethics, mind, and "
        "language belong here. It suits students who enjoy argument and logic, value clear thinking "
        "over easy answers, and want skills that carry into law, policy, or research."
    ),
    "uw-physics-bs": (
        "Undergraduates who want to understand matter, energy, motion, and the rules governing the "
        "universe will find rigor here. This Bachelor of Arts track suits students who pair a love of "
        "physics with breadth in other fields, rather than aiming solely at theoretical research."
    ),
    "uw-piano-bs": (
        "Undergraduate pianists ready to deepen their technique, repertoire, and musicianship will "
        "find dedicated training. It suits committed players who want to build a serious foundation "
        "in performance, whether for the stage, teaching, or further study."
    ),
    "uw-political-science-bs": (
        "Undergraduates who follow governance, power, and the workings of political life — "
        "institutions, behavior, ideas, and law — belong here. It suits students eyeing public "
        "service, law, policy, or research who want to analyze politics with discipline and evidence."
    ),
    "uw-psychology-bs": (
        "Undergraduates fascinated by the mind and behavior — how people think, feel, and act — will "
        "find a strong foundation here. It suits students drawn to the science behind human nature, "
        "preparing for research, counseling, health fields, or graduate study."
    ),
    "uw-romance-linguistics-bs": (
        "Undergraduates intrigued by how the Romance languages descended from Latin and relate to one "
        "another will find a distinctive focus. It suits language lovers who want to study structure "
        "and change across French, Spanish, Italian, and their kin rather than one alone."
    ),
    "uw-russian-language-literature-and-culture-bs": (
        "Undergraduates committed to Russian language and drawn to its rich literary and cultural "
        "tradition belong here. It fits students ready for a rigorous Slavic language and serious "
        "engagement with the texts, history, and society behind it."
    ),
    "uw-scandinavian-area-studies-bs": (
        "Undergraduates curious about the Nordic region — its cultures, societies, and place in the "
        "wider world — will find a focused path. It suits students who want to study Northern Europe "
        "across language, literature, and history rather than a single country in isolation."
    ),
    "uw-sociology-bs": (
        "Undergraduates who want to understand how societies work — social relationships, "
        "institutions, inequality, and everyday culture — belong here. It suits students drawn to "
        "evidence about human behavior and social patterns, with an eye toward policy, research, or "
        "social work."
    ),
    "uw-south-asian-languages-and-cultures-bs": (
        "Undergraduates drawn to the histories, languages, and cultures of South Asia will find their "
        "footing here. It suits students who want regional depth — across literature, religion, and "
        "society — and who may build language skills alongside cultural study."
    ),
    "uw-spanish-bs": (
        "Undergraduates set on real Spanish fluency and on exploring the literatures and cultures of "
        "the Spanish-speaking world will thrive here. It fits students who want to read, write, and "
        "converse with depth, whether for work, research, or cultural connection."
    ),
    "uw-speech-and-hearing-sciences-bs": (
        "Undergraduates interested in human hearing, speech, and communication — and in the clinical "
        "fields that address disorders — belong here. It suits students eyeing audiology or speech- "
        "language work who want a science-grounded foundation for graduate or clinical study."
    ),
    "uw-statistics-bs": (
        "Undergraduates who want to draw sound conclusions from data — building models, testing them, "
        "and reasoning about uncertainty — will find their fit. It suits analytically minded students "
        "preparing for data-driven work or research across the sciences and social sciences."
    ),
    "uw-string-instruments-bs": (
        "Undergraduate string players — violinists, violists, cellists, bassists — ready to refine "
        "their artistry will find dedicated training. It suits committed performers building "
        "technique and ensemble musicianship for the stage and beyond."
    ),
    "uw-swedish-bs": (
        "Undergraduates eager to learn Swedish and explore the culture and society of Sweden will "
        "find a focused path. It suits students interested in Nordic life and a North Germanic "
        "language, whether for heritage, study abroad, or comparative cultural work."
    ),
    "uw-visual-communication-design-bs": (
        "Undergraduates who want to shape how media communicates with people — through type, image, "
        "and information — will find their place. It suits visually driven students drawn to the "
        "intersection of design and clear communication across print and screen."
    ),
    "uw-voice-bs": (
        "Undergraduates with a singing instrument they want to train seriously will find their "
        "footing here, balancing repertoire, vocal technique, and performance. It suits aspiring "
        "soloists, ensemble singers, and music educators who learn best by doing and want disciplined "
        "studio work alongside a broad liberal arts foundation."
    ),
    "uw-anthropology-ms": (
        "Graduate students drawn to how people make meaning across cultures, deep time, and bodies "
        "will find a home in this program. It fits those weighing archaeology, medical anthropology, "
        "or sociocultural work who want methods training and a focused thesis before doctoral study "
        "or applied research."
    ),
    "uw-applied-chemical-science-and-technology-ms": (
        "This master's suits chemists and engineers ready to move from bench fundamentals toward how "
        "chemical processes are designed, scaled, and improved in practice. It fits graduates aiming "
        "for industry roles in production, materials, or process work who want applied depth rather "
        "than a research-heavy track."
    ),
    "uw-applied-child-and-adolescent-psychology-prevention-and-treatment-ms": (
        "Graduate students who want to translate developmental science into real help for young "
        "people belong here. It fits those headed toward prevention, intervention, or clinical- "
        "adjacent work with children and teens, who value coursework grounded in how the developing "
        "mind grows, struggles, and responds to support."
    ),
    "uw-applied-mathematics-ms": (
        "Built for graduate students who reach for mathematics to model real systems, this online "
        "program suits working professionals and recent graduates alike. If you enjoy optimization, "
        "scientific computing, and turning messy problems into tractable models, and you need a "
        "schedule that flexes around a job, it fits."
    ),
    "uw-art-history-ms": (
        "Graduate students who think hard about images, objects, and the institutions that frame them "
        "will thrive here. It suits those drawn to visual culture, museum work, or global art "
        "histories, who want rigorous methods and a thesis as preparation for doctoral study, "
        "curatorial paths, or the gallery world."
    ),
    "uw-asian-languages-and-literature-ms": (
        "This master's fits graduate students committed to reading Asian literatures in their "
        "original languages and tracing the cultures behind them. It suits those with prior language "
        "study who want advanced philological and literary training as a foundation for teaching, "
        "translation, or further doctoral research."
    ),
    "uw-astronomy-ms": (
        "Graduate students captivated by the physics of stars, galaxies, and the wider cosmos will "
        "find their level here. It fits those who want hands-on grounding in observation, cosmology, "
        "and instrumentation, whether as a step toward a doctorate or toward technical roles in data- "
        "rich scientific work."
    ),
    "uw-chemistry-ms": (
        "Graduate students who want to deepen their command of molecules before committing to a "
        "career or doctorate will find this fitting. It suits those drawn to synthesis, physical "
        "chemistry, or chemical biology who want advanced coursework and focused laboratory research "
        "at the master's level."
    ),
    "uw-china-studies-ms": (
        "This program suits graduate students building genuine expertise on China across its "
        "language, history, and contemporary society. It fits those headed toward policy, business, "
        "journalism, or academia who want interdisciplinary grounding and the language facility to "
        "engage Chinese sources directly."
    ),
    "uw-cinema-and-media-studies-ms": (
        "Graduate students who analyze film and media as culture, not just craft, will feel at home "
        "here. It fits those drawn to film history, media theory, and digital culture who want "
        "critical methods and a thesis, whether for doctoral study, teaching, or thoughtful work in "
        "the media industries."
    ),
    "uw-communication-ms": (
        "This master's suits graduate students curious about how messages move through media, "
        "publics, and politics. It fits those drawn to rhetoric, media studies, or political "
        "communication who want research methods and a focused project to prepare for doctoral work "
        "or analysis-heavy professional roles."
    ),
    "uw-computational-finance-and-risk-management-ms": (
        "Built for professionals and quantitatively minded graduates who want to bring computation to "
        "financial problems, this online program fits those pursuing quant, risk, or trading-adjacent "
        "careers. If you are comfortable with mathematics and programming and want to model markets "
        "and risk rigorously, it suits."
    ),
    "uw-computational-linguistics-ms": (
        "This online program fits graduate students and working professionals who sit at the meeting "
        "point of language and code. It suits those drawn to natural language processing who want to "
        "model how language works computationally, with the flexibility to study while holding a "
        "technical job."
    ),
    "uw-dance-ms": (
        "Graduate students who think with their bodies and want to deepen both practice and inquiry "
        "will find this fitting. It suits committed movers and choreographers ready to pair studio "
        "work with theory and methods, building toward teaching, performance, or scholarship in "
        "dance."
    ),
    "uw-design-ms": (
        "This master's suits graduate students who treat design as deliberate problem-solving across "
        "objects, processes, and systems. It fits practitioners and recent graduates who want to "
        "sharpen both craft and theory, building a research-informed practice for studio work, "
        "teaching, or design leadership."
    ),
    "uw-drama-ms": (
        "Graduate students serious about the stage will find rigorous footing here. It fits actors, "
        "directors, and theatre-makers who want to deepen their craft alongside production work and "
        "dramatic study, building toward professional practice or further training in performance."
    ),
    "uw-east-asia-studies-ms": (
        "This program fits graduate students seeking broad, humanistic command of East Asia past and "
        "present. It suits those headed toward policy, research, or further graduate work who want "
        "interdisciplinary grounding across the region's histories, languages, and societies rather "
        "than a single national focus."
    ),
    "uw-economics-ms": (
        "Graduate students who want analytical tools to study how people, markets, and institutions "
        "allocate resources will find this fitting. It suits those drawn to health, trade, or "
        "development economics who want rigorous methods, preparing for doctoral study or research- "
        "oriented roles in policy and industry."
    ),
    "uw-english-ms": (
        "This master's suits graduate students devoted to literature, language, and the written word. "
        "It fits those drawn to literary history, creative writing, or rhetoric who want focused "
        "study and a thesis as a foundation for doctoral work, teaching, or a writing-centered "
        "career."
    ),
    "uw-feminist-studies-ms": (
        "Graduate students who use gender as a lens to question power, identity, and justice belong "
        "here. This interdisciplinary program fits those drawn to feminist theory and social-justice "
        "research who want rigorous analytical training for academia, advocacy, or policy work."
    ),
    "uw-fine-arts-ms": (
        "This program suits graduate artists committed to studio practice as serious inquiry. It fits "
        "makers who want sustained time, critique, and conceptual grounding to develop a body of "
        "work, building toward exhibition, teaching, or a self-directed creative career."
    ),
    "uw-geography-ms": (
        "Graduate students who study how human and physical processes play out across space will find "
        "this fitting. It suits those drawn to GIS, remote sensing, and urban spatial analysis who "
        "want technical and analytical methods for research, planning, or environmental and policy "
        "work."
    ),
    "uw-german-studies-ms": (
        "This master's fits graduate students with strong German who want to engage the language, "
        "literature, and culture at an advanced level. It suits those preparing for doctoral study, "
        "teaching, or work that draws on deep regional and linguistic expertise."
    ),
    "uw-hispanic-studies-ms": (
        "Graduate students immersed in the literatures and cultures of the Spanish-speaking world "
        "will find their place here. It suits those with advanced Spanish drawn to texts from Spain "
        "and the Americas, preparing for doctoral research, teaching, or culturally grounded "
        "professional work."
    ),
    "uw-international-studies-ms": (
        "This program suits graduate students who think across borders about politics, economies, and "
        "cultures. It fits those headed toward foreign affairs, development, or global policy who "
        "want interdisciplinary methods and a focused project to anchor their regional or thematic "
        "expertise."
    ),
    "uw-italian-studies-ms": (
        "Graduate students drawn to Italy's language, literature, art, and history across its long "
        "cultural arc will find this fitting. It suits those with Italian proficiency seeking "
        "interdisciplinary depth as preparation for doctoral study, teaching, or culturally engaged "
        "careers."
    ),
    "uw-japan-studies-ms": (
        "This master's fits graduate students building serious, interdisciplinary expertise on Japan. "
        "It suits those drawn to its society, history, and language, headed toward research, policy, "
        "business, or further graduate work who want the facility to engage Japanese sources "
        "directly."
    ),
    "uw-korea-studies-ms": (
        "Graduate students focused on the Korean peninsula and its global diaspora will find their "
        "footing here. It fits those drawn to Korea's politics, culture, and language across both "
        "Koreas, preparing for research, policy, or professional work that demands regional fluency."
    ),
    "uw-linguistics-ms": (
        "This program suits graduate students fascinated by the structure of language itself. It fits "
        "those drawn to phonology, syntax, or language documentation who want rigorous methods and a "
        "thesis, whether as a step toward a doctorate or toward applied and computational language "
        "work."
    ),
    "uw-mathematics-ms": (
        "Graduate students who want to deepen their mathematical maturity will find this fitting. It "
        "suits those drawn to analysis, algebra, or applied mathematics who want advanced coursework "
        "before a doctorate or quantitative careers in industry, teaching, and research."
    ),
    "uw-music-ms": (
        "This master's fits graduate musicians ready to deepen their art at a high level. It suits "
        "performers and scholars drawn to orchestral, jazz, or ethnomusicological work who want to "
        "pair advanced practice with study, building toward performance, teaching, or further "
        "graduate research."
    ),
    "uw-near-eastern-languages-and-civilization-ms": (
        "Graduate students drawn to the languages and civilizations of the ancient and modern Near "
        "East will find their home here. It suits those wanting advanced language training and "
        "historical depth across the region as preparation for doctoral study, teaching, or "
        "specialized scholarship."
    ),
    "uw-philosophy-ms": (
        "This program suits graduate students who want to argue carefully about meaning, knowledge, "
        "and value. It fits those drawn to logic, ethics, or philosophy of science who want rigorous "
        "training and a focused thesis, whether toward doctoral study or analytically demanding "
        "careers."
    ),
    "uw-physics-ms": (
        "Graduate students who want to understand nature at its most fundamental will find this "
        "fitting. It suits those drawn to condensed matter, particle physics, or biophysics who want "
        "advanced coursework and research, whether as a path to a doctorate or to technical and "
        "scientific careers."
    ),
    "uw-political-science-ms": (
        "This master's fits graduate students who study power, institutions, and political behavior "
        "with analytical rigor. It suits those drawn to American politics, comparative methods, or "
        "international relations who want research training and a focused project, preparing for "
        "doctoral study or policy and analysis roles."
    ),
    "uw-psychology-ms": (
        "Graduate students who want to study the mind and behavior with scientific rigor will find "
        "this fitting. It suits those drawn to clinical, cognitive, or developmental psychology who "
        "want advanced coursework and research methods as a foundation for doctoral study or applied "
        "work."
    ),
    "uw-russia-east-european-and-central-asian-studies-ms": (
        "This interdisciplinary program suits graduate students building expertise on Russia, Eastern "
        "Europe, and Central Asia. It fits those headed toward policy, research, or further graduate "
        "study who want regional grounding across the area's politics, histories, and cultures, with "
        "language to engage primary sources."
    ),
    "uw-scandinavian-ms": (
        "Graduate students drawn to the Nordic world, its languages, literatures, and cultures, will "
        "find their place here. It suits those with relevant language background seeking "
        "interdisciplinary depth as preparation for doctoral study, teaching, or work tied to the "
        "region."
    ),
    "uw-slavic-languages-and-literatures-ms": (
        "This master's fits graduate students devoted to the languages and literary traditions of the "
        "Slavic world. It suits those with relevant language preparation who want advanced study of "
        "texts and cultures across the region, building toward doctoral research, teaching, or "
        "translation."
    ),
    "uw-sociology-ms": (
        "Graduate students drawn to questions of urban inequality, health disparities, and how social "
        "networks shape life chances will find their footing here. It suits those who want rigorous "
        "methods training and a thesis or capstone before pursuing applied research or a doctorate."
    ),
    "uw-south-asian-studies-ms": (
        "Graduate students fascinated by India and the wider South Asian region — its languages, "
        "histories, and cultures — belong here. It fits those building area expertise for careers in "
        "research, policy, education, or international work, and who value interdisciplinary depth "
        "over a single discipline."
    ),
    "uw-southeast-asian-studies-ms": (
        "This program is for graduate students drawn to the languages, cultures, and histories of "
        "Southeast Asia's many states and peoples. It suits those building regional fluency for work "
        "in research, diplomacy, development, or education, and who enjoy crossing disciplinary "
        "lines."
    ),
    "uw-speech-language-pathology-ms": (
        "Future speech-language pathologists who want to evaluate and treat communication and "
        "swallowing disorders will find their clinical path here. It fits people headed for "
        "certification and practice in schools, hospitals, or clinics who care about restoring how "
        "others connect and speak."
    ),
    "uw-statistics-ms": (
        "Graduate students who want to turn data into sound conclusions — through biostatistics, "
        "machine learning, and data mining — fit this program. It suits quantitatively minded people "
        "seeking applied analytics roles or a foundation for doctoral study, capped by a thesis or "
        "capstone."
    ),
    "uw-audiology-prof": (
        "This clinical doctorate is for those committed to becoming audiologists — diagnosing and "
        "treating hearing and balance disorders and helping prevent further loss. It suits patient- "
        "centered people who pair scientific curiosity about how we hear with a desire for hands-on, "
        "lifelong clinical care."
    ),
    "uw-anthropology-phd": (
        "Prospective doctoral students drawn to archaeology, medical anthropology, or the study of "
        "culture and society will thrive here. It fits those ready for years of fieldwork, faculty- "
        "mentored research, and an original dissertation, typically supported by graduate funding."
    ),
    "uw-applied-mathematics-phd": (
        "PhD applicants who want to model real-world systems through optimization, scientific "
        "computing, and mathematical analysis fit this program. It suits researchers who enjoy "
        "bridging rigorous theory and practical problems across science and engineering, and who are "
        "ready to commit to dissertation work."
    ),
    "uw-art-history-phd": (
        "Prospective doctoral students examining visual culture, museums, and art across global "
        "traditions belong here. It fits those preparing for scholarly or curatorial careers who want "
        "sustained archival and theoretical research culminating in a faculty-mentored dissertation."
    ),
    "uw-asian-languages-and-literature-phd": (
        "This doctorate is for scholars devoted to the languages and literary traditions of Asia. It "
        "suits those with strong language preparation who want to pursue deep textual and cultural "
        "research, mentored toward an original dissertation and supported by graduate funding."
    ),
    "uw-astronomy-phd": (
        "PhD applicants captivated by the cosmos — observational astronomy, cosmology, and the "
        "instruments that reveal them — fit this program. It suits those ready for telescope time, "
        "data analysis, and several years of faculty-mentored research toward an original "
        "dissertation."
    ),
    "uw-biology-phd": (
        "Prospective doctoral students investigating ecology, genomics, or marine life will find "
        "their place here. It fits researchers eager for sustained lab and field work, mentored "
        "discovery, and a dissertation that advances how we understand living systems."
    ),
    "uw-chemistry-phd": (
        "This doctorate suits those drawn to synthesis, physical chemistry, or chemical biology who "
        "want to work at the bench for years toward original discovery. It fits people who pair "
        "experimental patience with curiosity about how molecules behave and transform."
    ),
    "uw-cinema-and-media-studies-phd": (
        "Prospective doctoral students analyzing film history, media theory, and digital culture "
        "belong here. It fits scholars who want to interrogate moving images and emerging media "
        "critically, building toward a faculty-mentored dissertation and a research or teaching "
        "career."
    ),
    "uw-communication-phd": (
        "PhD applicants studying media, rhetoric, and political communication fit this program. It "
        "suits those who want to examine how messages shape publics and power, pursuing original "
        "research and a dissertation toward academic or research careers."
    ),
    "uw-digital-arts-and-experimental-media-phd": (
        "This doctorate is for artist-scholars who make and theorize work built with digital "
        "technology. It fits those combining studio practice with critical research, ready to push "
        "experimental media forward through creative production and a faculty-mentored dissertation."
    ),
    "uw-drama-phd": (
        "Prospective doctoral students examining acting, directing, and production as objects of "
        "scholarship belong here. It fits those who pair theatrical practice with rigorous inquiry "
        "and want to pursue research and teaching in drama, culminating in a dissertation."
    ),
    "uw-economics-phd": (
        "PhD applicants drawn to health, trade, and development economics fit this program. It suits "
        "quantitatively rigorous thinkers ready to build formal models, analyze data, and produce "
        "original research toward a dissertation and academic or policy careers."
    ),
    "uw-english-phd": (
        "This doctorate suits scholars of literary history, rhetoric, or creative writing who want "
        "sustained immersion in texts and ideas. It fits those preparing for research and teaching "
        "careers, working toward a faculty-mentored dissertation with graduate funding."
    ),
    "uw-feminist-studies-phd": (
        "Prospective doctoral students committed to feminist epistemologies, qualitative methods, and "
        "interdisciplinary inquiry belong here. It fits scholars who want to ask critical questions "
        "about gender, power, and knowledge across fields, building toward an original dissertation."
    ),
    "uw-french-studies-phd": (
        "This doctorate is for scholars devoted to French language, literature, and culture. It fits "
        "those with strong language preparation ready to pursue deep literary and cultural research, "
        "mentored toward a dissertation and supported by graduate funding."
    ),
    "uw-geography-phd": (
        "PhD applicants who study space and place through GIS, remote sensing, and urban spatial "
        "analysis fit this program. It suits researchers who want to combine spatial methods with "
        "social and environmental questions across years of mentored dissertation work."
    ),
    "uw-german-studies-phd": (
        "This doctorate suits scholars devoted to German language, literature, and culture who want "
        "sustained, mentored research. It fits those with strong language preparation ready to pursue "
        "original inquiry toward a dissertation and an academic career."
    ),
    "uw-hispanic-studies-phd": (
        "Prospective doctoral students drawn to Hispanic languages, literatures, and cultures belong "
        "here. It fits those with strong language preparation who want to pursue deep literary and "
        "cultural research, mentored toward an original dissertation."
    ),
    "uw-history-phd": (
        "PhD applicants drawn to the Pacific Northwest, global history, or the history of science and "
        "medicine fit this program. It suits those ready for archival research and years of faculty- "
        "mentored work toward an original, evidence-grounded dissertation."
    ),
    "uw-linguistics-phd": (
        "This doctorate is for those fascinated by the structure of language — phonology, syntax, and "
        "documentation of living languages. It fits researchers ready to combine analytical rigor "
        "with fieldwork, building toward a faculty-mentored dissertation."
    ),
    "uw-mathematics-phd": (
        "Prospective doctoral students drawn to analysis, algebra, or applied mathematics belong "
        "here. It fits those who relish proof and abstraction and are ready to commit several years "
        "to original research and a faculty-mentored dissertation."
    ),
    "uw-music-phd": (
        "PhD applicants studying orchestral and jazz performance or ethnomusicology fit this program. "
        "It suits musician-scholars who want to pair artistry with research, examining music across "
        "traditions toward a faculty-mentored dissertation."
    ),
    "uw-musical-arts-phd": (
        "This doctorate is for advanced performers and composers who treat music as both art and "
        "scholarship. It fits those ready to deepen their practice while pursuing research into music "
        "as a human universal, culminating in a dissertation."
    ),
    "uw-near-and-middle-eastern-studies-phd": (
        "Prospective doctoral students drawn to the languages, histories, and cultures of the Near "
        "and Middle East belong here. It fits those building interdisciplinary regional expertise "
        "through faculty-led research toward an original dissertation."
    ),
    "uw-philosophy-phd": (
        "This doctorate suits those captivated by logic, ethics, and the philosophy of science who "
        "want rigorous, sustained argument. It fits people ready to read deeply, reason carefully, "
        "and produce an original dissertation toward academic careers."
    ),
    "uw-physics-phd": (
        "PhD applicants drawn to condensed matter, particle physics, or biophysics fit this program. "
        "It suits those ready for several years of theoretical or experimental research, faculty "
        "mentorship, and an original dissertation that advances the field."
    ),
    "uw-political-science-phd": (
        "Prospective doctoral students studying American politics, comparative methods, or "
        "international relations belong here. It fits those who want to investigate power and "
        "governance with rigorous methods, working toward a faculty-mentored dissertation."
    ),
    "uw-psychology-phd": (
        "PhD applicants drawn to clinical, cognitive, or developmental psychology fit this program. "
        "It suits those ready for empirical research on mind and behavior, faculty mentorship, and an "
        "original dissertation toward research or applied careers."
    ),
    "uw-scandinavian-phd": (
        "This doctorate is for scholars devoted to Scandinavian languages, literatures, and cultures. "
        "It fits those ready to build regional and theoretical expertise through faculty-mentored "
        "research and an original dissertation, supported by graduate funding."
    ),
    "uw-slavic-languages-and-literatures-phd": (
        "Prospective doctoral students drawn to Slavic languages and literary traditions belong here. "
        "It fits those with strong language preparation ready to pursue deep textual and cultural "
        "research, mentored toward an original dissertation."
    ),
    "uw-sociology-phd": (
        "PhD applicants investigating urban inequality, health disparities, and social networks fit "
        "this program. It suits those ready to design original studies, master research methods, and "
        "produce a faculty-mentored dissertation toward academic or research careers."
    ),
    "uw-speech-and-hearing-sciences-phd": (
        "Prospective doctoral students researching audiology and communication disorders belong here. "
        "It fits those who want to study how we hear and speak — and what disrupts it — through "
        "rigorous, faculty-mentored research toward an original dissertation."
    ),
    "uw-statistics-phd": (
        "PhD applicants drawn to biostatistics, machine learning, and data mining fit this program. "
        "It suits quantitatively rigorous researchers ready to develop new methods and theory, "
        "working toward a faculty-mentored dissertation and graduate funding."
    ),
    "uw-architectural-design-bs": (
        "Undergraduates who think in space and form, sketching ideas and building models as readily "
        "as they reason through structure. If you want a studio-driven path that treats buildings as "
        "both a visual art and an engineering problem, this design major will fit how you work."
    ),
    "uw-architectural-design-w-const-mgmt-bs": (
        "Undergraduates drawn to design who also want to understand how buildings actually get built, "
        "budgeted, and sequenced. This combined track suits students who like moving between the "
        "studio and the construction site and want both the architect's eye and the builder's "
        "discipline."
    ),
    "uw-architectural-studies-bs": (
        "Undergraduates curious about how buildings are conceived, planned, and constructed who want "
        "to read the built world as much as design it. If you are drawn to inquiry, history, and the "
        "culture of architecture rather than a single professional track, this studies major gives "
        "you room to explore."
    ),
    "uw-community-environment-and-planning-bs": (
        "Undergraduates who care about how cities, land, and infrastructure shape daily life and want "
        "to help make communities more livable. This major fits students energized by transportation, "
        "the environment, and public process who prefer collaborative, community-grounded work to "
        "solitary technical study."
    ),
    "uw-environmental-design-and-sustainability-bs": (
        "Undergraduates who want their design work to answer to climate, ecology, and resource "
        "limits. If you care about sustainability and like weaving environmental thinking into "
        "buildings, products, and policy, this major is built for students who design with the planet "
        "in mind."
    ),
    "uw-real-estate-bs": (
        "Undergraduates interested in how land and property gain value, get financed, and reshape "
        "neighborhoods. This major suits students who pair an analytical, numbers-minded streak with "
        "curiosity about cities and development, and who want a business-facing entry into the built "
        "environment."
    ),
    "uw-architecture-ms": (
        "Graduate students ready to deepen their command of architectural design and the craft of "
        "conceiving and constructing buildings. This master's fits those who want advanced studio "
        "work and a research-minded approach to practice, whether you are sharpening a focus or "
        "pivoting toward a specialization."
    ),
    "uw-concurrent-ms": (
        "Graduate students who want to study the designed spaces that shape human activity across "
        "more than one built-environment discipline at once. This concurrent path suits those whose "
        "interests cross boundaries and who would rather combine perspectives than commit to a single "
        "department."
    ),
    "uw-construction-management-ms": (
        "Working professionals in construction and the building trades who want to lead larger, more "
        "complex projects. Delivered online, this master's fits those balancing a job while building "
        "rigor in planning, scheduling, and project delivery from groundbreaking through completion."
    ),
    "uw-infrastructure-planning-and-management-ms": (
        "Graduate students and practitioners focused on the systems that keep cities and economies "
        "running, from transportation to utilities. This master's suits those who want to plan, "
        "finance, and manage infrastructure and enjoy working at the intersection of engineering, "
        "policy, and operations."
    ),
    "uw-infrastructure-planning-and-management-ms-2": (
        "Working professionals responsible for the infrastructure that serves communities and firms "
        "who want graduate credentials without leaving their jobs. Delivered online and capped by a "
        "thesis or capstone, this fits mid-career practitioners ready to plan and manage complex "
        "systems more strategically."
    ),
    "uw-landscape-architecture-ms": (
        "Graduate students who want to shape outdoor places, landmarks, and public spaces for "
        "ecological and social good. This master's fits those drawn to studio work grounded in "
        "ecological planning, who care as much about how land performs as how it looks."
    ),
    "uw-real-estate-ms": (
        "Graduate students and early-career professionals who want to specialize in urban land "
        "economics and property development. With advanced coursework and a thesis or capstone, this "
        "master's suits analytically minded people aiming to lead in finance, investment, or "
        "development."
    ),
    "uw-urban-planning-ms": (
        "Graduate students committed to the public welfare of cities, weighing efficiency, equity, "
        "and the environment in how places grow. This master's fits those who want to shape land use "
        "and policy and who see planning as a tool for healthier, fairer communities."
    ),
    "uw-built-environment-phd": (
        "Prospective doctoral students who want to investigate how the human-made world shapes "
        "health, society, and behavior across architecture, planning, and allied fields. This PhD "
        "suits researchers ready to commit to original, faculty-mentored inquiry and a dissertation "
        "at the crossroads of design and the social sciences."
    ),
    "uw-urban-design-and-planning-phd": (
        "PhD applicants who want to question how cities are planned and designed, moving past top- "
        "down master planning toward new theory and evidence. This doctoral program fits scholars "
        "ready for sustained research and a dissertation that advances how settlements are shaped."
    ),
    "uw-accounting-bs": (
        "Undergraduates who like order, precision, and seeing exactly where money moves will feel at "
        "home here. If you want to read the financial story behind a business and translate raw "
        "transactions into reports that investors, managers, and regulators can trust, accounting "
        "gives you that grounding."
    ),
    "uw-accounting-for-business-professionals-bs": (
        "Best for undergraduates who want accounting fluency as a foundation for a broader business "
        "career rather than a purely technical specialty. If you expect to manage, advise, or lead "
        "and want to understand how economic activity is measured and reported to stakeholders, this "
        "track builds that literacy."
    ),
    "uw-entrepreneurship-bs": (
        "Undergraduates with ideas they actually want to build will thrive here. If you are "
        "comfortable with ambiguity and risk, energized by spotting an opportunity and turning it "
        "into a product or service, and willing to start before everything is certain, "
        "entrepreneurship gives that drive a structure."
    ),
    "uw-finance-bs": (
        "Undergraduates drawn to how money, assets, and risk move over time belong in finance. If you "
        "enjoy quantitative reasoning, weighing trade-offs between consumption and saving, and the "
        "discipline of valuing decisions under uncertainty, this major sharpens the judgment that "
        "investing and corporate finance demand."
    ),
    "uw-human-resources-management-bs": (
        "Undergraduates who care about how organizations get the best from their people will find "
        "their fit here. If you are interested in the strategic side of hiring, developing, and "
        "supporting employees, and you like balancing individual needs with organizational goals, HRM "
        "channels that interest into practice."
    ),
    "uw-information-systems-bs": (
        "A strong match for undergraduates who sit comfortably between business and technology. If "
        "you want to design how an organization collects, processes, and shares information, and you "
        "enjoy connecting technical systems to the people and decisions they serve, information "
        "systems is built for you."
    ),
    "uw-marketing-bs": (
        "Undergraduates curious about what makes customers choose, stay, and come back will enjoy "
        "this major. If you like reading human behavior, shaping how a product is positioned, and "
        "working at the intersection of creativity and business strategy, marketing turns that "
        "curiosity into a craft."
    ),
    "uw-operations-and-supply-chain-management-bs": (
        "Undergraduates who like solving real logistical puzzles will find their place here. If you "
        "want to understand how raw materials become finished products and reach customers "
        "efficiently, and you enjoy optimizing procurement, logistics, and the systems behind "
        "delivery, this Foster major suits you."
    ),
    "uw-business-administration-ms": (
        "Graduate students and early-career professionals ready to step into leadership belong in "
        "this full-time MBA. If you want to sharpen your strategic, analytical, and management "
        "judgment in Seattle's technology and health-care economy, and you value learning through "
        "cases alongside ambitious peers, this is your launchpad."
    ),
    "uw-business-analytics-ms": (
        "Graduate students who want to turn data into business decisions will fit this program well. "
        "If you have a quantitative bent and want to master the tools and methods for exploring "
        "performance, generating insight, and driving planning, this master's bridges technical skill "
        "and managerial impact."
    ),
    "uw-entrepreneurship-ms": (
        "Graduate students and aspiring founders ready to go deeper than a first idea belong here. If "
        "you want advanced grounding in entrepreneurship theory and methods, and you intend to test a "
        "venture seriously through a capstone or thesis, this master's gives your ambition rigor and "
        "structure."
    ),
    "uw-information-systems-ms": (
        "Graduate students and working professionals who want to lead at the meeting point of "
        "technology and organizations will fit this program. If you are ready for advanced study in "
        "how information systems are designed and managed, and you want to deepen your skills through "
        "methods-driven coursework, this is your path."
    ),
    "uw-professional-accounting-ms": (
        "Best for graduate students and aspiring accountants preparing for professional practice and "
        "licensure. If you want to move from foundational coursework to the depth that practicing "
        "accountants and financial reporting demand, this focused master's builds the technical "
        "command and credentials that public and corporate accounting expect."
    ),
    "uw-supply-chain-management-ms": (
        "Working professionals and graduate students who want mastery over how goods and value flow "
        "will fit this program. If you are drawn to the design, planning, and control of supply "
        "chains, and you want to synchronize supply with demand and measure performance globally, "
        "this master's deepens that expertise."
    ),
    "uw-taxation-ms": (
        "Graduate students and accounting professionals who want to specialize in tax belong here. If "
        "you are intrigued by how levies are structured, how they shape individual and corporate "
        "behavior, and the technical reasoning behind compliance and planning, this master's builds "
        "the specialized depth that tax practice rewards."
    ),
    "uw-business-administration-phd": (
        "Prospective doctoral students aiming for research and academic careers in business will fit "
        "this program. Typically funded and research-intensive, it suits those who want to study how "
        "commercial enterprises are organized and managed at a theoretical level, and who are ready "
        "to produce original scholarship over several years."
    ),
    "uw-dentistry-ms": (
        "Graduate students who want a research-grounded master's in oral-health science rather than "
        "chairside clinical training. Best for those drawn to laboratory inquiry into the biology of "
        "teeth and disease, and comfortable spending their time on bench work and a thesis."
    ),
    "uw-endodontics-ms": (
        "Dentists pursuing advanced training in the dental pulp and root canal therapy who want to "
        "specialize in saving teeth. A fit for clinicians ready to pair deep diagnostic skill with "
        "the precise, microscope-level work that defines endodontic practice."
    ),
    "uw-oral-health-sciences-ms": (
        "Graduate students who want a broad scientific foundation in the diagnosis, prevention, and "
        "management of oral disease. Suited to those weighing a research or academic path in oral "
        "health and willing to ground that interest in coursework and a thesis."
    ),
    "uw-oral-medicine-ms": (
        "Clinicians focused on the diagnosis and management of oral mucosal disease, including oral "
        "cancer, salivary disorders, and facial pain. A strong fit for dentists who enjoy complex "
        "medical detective work at the border of dentistry and medicine."
    ),
    "uw-orthodontics-ms": (
        "Dentists who want to specialize in correcting malpositioned teeth, misaligned jaws, and bite "
        "problems. Best for clinicians who think in terms of growth, mechanics, and long-horizon "
        "treatment plans, and who find satisfaction in gradual, measurable change."
    ),
    "uw-periodontics-ms": (
        "Dentists pursuing specialty training in the supporting structures of teeth and the diseases "
        "that threaten them. A fit for clinicians who want to combine surgical skill with the long- "
        "term management of gum health and implant therapy."
    ),
    "uw-prosthodontics-ms": (
        "Dentists drawn to restoring and replacing teeth through crowns, bridges, dentures, and "
        "implants. Suited to clinicians who care about both function and appearance, and who enjoy "
        "the technical artistry of rebuilding a patient's bite and smile."
    ),
    "uw-dentistry-prof": (
        "Future dentists ready to commit to four years of didactic coursework and supervised clinical "
        "training before licensure. Best for people who want hands-on patient care, value steady "
        "manual precision, and are motivated to lead a community's oral health."
    ),
    "uw-dentistry-phd": (
        "Prospective doctoral students aiming to advance oral-health and clinical dentistry research "
        "through original, faculty-mentored inquiry. A fit for those committed to a multi-year, "
        "typically funded dissertation and a future in academic or scientific dentistry rather than "
        "full-time practice."
    ),
    "uw-oral-health-sciences-phd": (
        "PhD applicants who want to build a research career investigating the biology of oral disease "
        "and its prevention. Suited to those ready for a funded, dissertation-length project and the "
        "patient, independent work that scientific discovery demands."
    ),
    "uw-early-care-and-education-bs": (
        "Undergraduates drawn to the earliest years of learning, who want to understand how children "
        "from birth through age eight grow, play, and develop. A fit if you picture yourself in a "
        "preschool or child-care setting and care about giving young children a strong start."
    ),
    "uw-early-care-and-education-fee-based-online-bs": (
        "Working professionals already in child-care, Head Start, or family-support roles across "
        "Washington who want to finish a bachelor's without leaving the job. Built for adult learners "
        "who need an online, fee-based path that fits around shifts and family responsibilities."
    ),
    "uw-early-childhood-and-family-studies-bs": (
        "Undergraduates who see a child's development as inseparable from the family around them, and "
        "who want coursework and research that treat both together. A good match if you're curious "
        "about parenting, caregiving, and the systems that support young families."
    ),
    "uw-education-studies-bs": (
        "Undergraduates who want to think critically about how people learn before committing to the "
        "classroom, examining teaching as it intersects with social, political, and psychological "
        "development. Suited to those exploring education broadly rather than seeking immediate "
        "teacher licensure."
    ),
    "uw-education-communities-and-organizations-bs": (
        "Undergraduates interested in learning that happens beyond the classroom, in schools as "
        "institutions and in the communities and organizations around them. A fit if you're drawn to "
        "youth programs, nonprofits, or education policy rather than to teaching a class of your own."
    ),
    "uw-curriculum-and-instruction-ms": (
        "Educators and recent graduates who want to deepen how they design lessons and improve "
        "student achievement. Choose this master's if you're focused on the craft of curriculum and "
        "instruction itself and want practical, research-informed tools to bring back to a learning "
        "setting."
    ),
    "uw-educational-foundations-leadership-and-policy-ms": (
        "Graduate students drawn to the big questions of how education is governed across local, "
        "state, and federal levels, and how policy shapes whole systems. A fit if you want to analyze "
        "and influence schooling rather than lead a single classroom."
    ),
    "uw-educational-leadership-and-policy-studies-ms": (
        "Educators ready to step into leadership, guiding teachers, students, and families toward "
        "shared goals. Choose this master's if you aspire to be a principal, administrator, or "
        "program leader and want to study how leadership and policy come together in practice."
    ),
    "uw-learning-sciences-and-human-development-ms": (
        "Graduate students fascinated by how people actually learn, across cognitive, sociocultural, "
        "and critical perspectives, and how learning environments can be designed well. Suited to "
        "those who want to bridge research on the mind with the practical work of building better "
        "educational experiences."
    ),
    "uw-master-in-teaching-ms": (
        "Aspiring teachers preparing to lead their own classrooms, ready to build the knowledge, "
        "methods, and classroom skills the work demands. This is the path for career-changers and "
        "recent graduates seeking the preparation that opens the door to teaching in schools."
    ),
    "uw-measurement-and-statistics-ms": (
        "Graduate students who like working with data and want to apply measurement and statistics to "
        "questions in education and the social sciences. A strong fit if you're analytical, "
        "comfortable with quantitative methods, and want skills in assessment, research design, and "
        "interpretation."
    ),
    "uw-special-education-ms": (
        "Educators committed to teaching students with disabilities through individually planned, "
        "carefully monitored instruction and accessible learning settings. Choose this master's if "
        "you want to specialize in adapting curriculum and supports so every learner can succeed."
    ),
    "uw-curriculum-and-instruction-phd": (
        "Prospective doctoral students aiming to become researchers in literacy, STEM pedagogy, or "
        "classroom practice, typically with funding and close faculty mentorship through a "
        "dissertation. A fit if you want to generate new knowledge about teaching rather than apply "
        "existing methods."
    ),
    "uw-education-phd": (
        "Prospective doctoral students pursuing scholarly careers across teacher preparation, the "
        "learning sciences, or education policy. Suited to those ready for several years of funded, "
        "mentored research and a dissertation that contributes original findings to the field."
    ),
    "uw-educational-leadership-and-policy-studies-phd": (
        "Prospective doctoral students who want to study school leadership and analyze education "
        "policy at the research level, supported by faculty mentorship and graduate funding. A fit if "
        "you aim for a career in scholarship, policy analysis, or higher-education faculty work."
    ),
    "uw-special-education-phd": (
        "Prospective doctoral students drawn to research on inclusive classrooms and disability "
        "studies, ready for funded, faculty-mentored work toward a dissertation. Choose this if you "
        "want to advance the evidence behind how students with disabilities are taught and supported."
    ),
    "uw-engineering-bs": (
        "Undergraduates who like solving real problems with math and science under genuine "
        "constraints. If you want to design and improve the systems, devices, and processes people "
        "depend on, this broad engineering foundation fits builders and problem-solvers exploring "
        "where their interests point."
    ),
    "uw-aeronautics-and-astronautics-ms": (
        "Graduate students drawn to flight, from aircraft to spacecraft and the avionics that run "
        "them. This master's fits engineers ready to specialize in aeronautical or astronautical work "
        "and to deepen the analysis and design skills the aerospace field demands."
    ),
    "uw-aerospace-engineering-ms": (
        "Working engineers who want to advance in aerospace, including the electronics and avionics "
        "side of the field, while staying on the job. Delivered online, this master's suits "
        "practitioners ready to extend their expertise in aircraft and spacecraft systems on a "
        "flexible schedule."
    ),
    "uw-applied-bioengineering-ms": (
        "Graduate students and professionals who want to apply engineering principles to medicine and "
        "biology for real healthcare uses. This applied master's fits those drawn to devices, "
        "diagnostics, and the practical translation of engineering into patient-facing solutions."
    ),
    "uw-artificial-intelligence-and-machine-learning-for-engineering-ms": (
        "Graduate students and practicing engineers who want to put machine learning to work on "
        "engineering problems. This master's suits those ready to build statistical models that learn "
        "from data, aiming to bring AI methods into design, analysis, and decision-making across "
        "technical fields."
    ),
    "uw-bioengineering-ms": (
        "Graduate students who want to merge biology with engineering to create usable, tangible "
        "products, from tissue engineering to clinical tools. This master's fits those drawn to "
        "translational work and the immersive bridge between the lab and medicine."
    ),
    "uw-chemical-engineering-ms": (
        "Graduate students who want to turn raw materials into useful products through economical, "
        "well-designed processes. This master's fits those with a foundation in chemistry and "
        "engineering who are ready for advanced study and research in process design and applied "
        "inquiry."
    ),
    "uw-civil-engineering-ms": (
        "Graduate students focused on the physical and built environment, from roads and bridges to "
        "dams, pipelines, and structures. This master's suits those drawn to infrastructure "
        "resilience and regional hydrology who want to design and maintain the public works "
        "communities rely on."
    ),
    "uw-computer-science-and-engineering-ms": (
        "Graduate students ready for advanced work in systems, AI, and human-computer interaction. "
        "This master's fits those who want rigorous coursework with research or thesis options, "
        "whether you are deepening technical depth or moving toward a specialized area of computing."
    ),
    "uw-electrical-and-computer-engineering-ms": (
        "Graduate students working at the intersection of electricity, electronics, and "
        "electromagnetism, from devices to large systems. This master's fits those ready to deepen "
        "their command of electrical and computer engineering through advanced coursework and "
        "research."
    ),
    "uw-engineering-in-leadership-and-systems-innovation-ms": (
        "Engineers ready to lead, integrating and managing complex systems across their life cycles "
        "rather than working on a single component. This master's fits those who want to pair "
        "technical depth with the systems thinking and leadership skills to guide teams and large- "
        "scale projects."
    ),
    "uw-engineering-in-multidisciplinary-engineering-ms": (
        "Graduate students whose interests cross traditional engineering boundaries and who want to "
        "design solutions that meet real human needs. This master's fits those who prefer to combine "
        "disciplines, building breadth across the field rather than committing to a single "
        "specialization."
    ),
    "uw-human-centered-design-and-engineering-ms": (
        "Graduate students who want to design products, services, and systems around the people who "
        "use them. This master's fits those drawn to user research and a human-centered approach to "
        "problem-solving, bridging engineering rigor with empathy for the human perspective."
    ),
    "uw-industrial-and-systems-engineering-ms": (
        "Graduate students focused on designing and improving integrated systems of people, "
        "materials, information, and equipment. This master's suits those who want to make complex "
        "operations run more efficiently and enjoy optimizing how the parts of a system work "
        "together."
    ),
    "uw-industrial-engineering-ms": (
        "Graduate students who want to specify, predict, and evaluate the performance of complex "
        "systems using mathematical, physical, and social science methods. This master's fits "
        "analytically minded engineers drawn to the design and analysis side of industrial systems."
    ),
    "uw-materials-science-and-engineering-ms": (
        "Graduate students fascinated by how a material's structure governs its properties, and how "
        "that knowledge yields new materials by design. This master's fits those ready for advanced, "
        "research-minded study at the interdisciplinary heart of the field."
    ),
    "uw-materials-science-and-engineering-ms-2": (
        "Graduate students who want to trace how atomic and microscopic structure shapes a material's "
        "mechanical, electrical, thermal, and optical behavior. This master's suits those drawn to "
        "metallurgy, polymers, and nanomaterials and ready for advanced coursework and research."
    ),
    "uw-mechanical-engineering-ms": (
        "Working engineers who want to deepen their mastery of machines, mechanisms, force, and "
        "motion while keeping their careers in motion. Delivered online, this master's fits "
        "practitioners ready to advance their mechanical engineering expertise on a flexible "
        "schedule."
    ),
    "uw-pharmaceutical-bioengineering-ms": (
        "Working professionals in drug development and manufacturing who want to advance how "
        "medications are formulated, produced, and quality-controlled. Delivered online, this "
        "master's fits those ready to deepen expertise in pharmaceutical engineering without stepping "
        "away from their roles."
    ),
    "uw-supply-chain-transportation-and-logistics-ms": (
        "Working professionals managing the flow of goods, services, and information from origin to "
        "customer. Delivered online, this master's fits logisticians and operations specialists who "
        "want to make supply chains more efficient and resilient while staying on the job."
    ),
    "uw-sustainable-transportation-ms": (
        "Graduate students and professionals who want transportation systems that answer to their "
        "social and environmental impacts. Delivered online, this master's fits those committed to "
        "mobility that is cleaner, fairer, and more sustainable for communities and the planet."
    ),
    "uw-technology-innovation-ms": (
        "Graduate students and practitioners who want to turn ideas into real products and services. "
        "This master's fits those drawn to the practical work of innovation, who want to combine "
        "technical grounding with the skills to bring new goods and services to life."
    ),
    "uw-aeronautics-and-astronautics-phd": (
        "Prospective doctoral students focused on the development of aircraft and spacecraft. This "
        "PhD suits researchers ready to commit to original work in aerospace engineering, supported "
        "by a faculty mentor and graduate funding through a substantial dissertation."
    ),
    "uw-bioengineering-phd": (
        "Prospective doctoral students who want to push the frontiers of medical devices, imaging, "
        "and tissue engineering. This funded, faculty-mentored PhD fits researchers ready to commit "
        "to a dissertation that advances the engineering of human health."
    ),
    "uw-chemical-engineering-phd": (
        "PhD applicants ready to advance chemical engineering through original research, from process "
        "science to applied inquiry. This funded, faculty-mentored program fits those prepared to "
        "dedicate years to a dissertation at the field's research frontier."
    ),
    "uw-civil-engineering-phd": (
        "Prospective doctoral students who want to advance structural design, transportation, or "
        "hydrology through original research. This funded, faculty-mentored PhD fits those ready to "
        "commit to a dissertation that strengthens the infrastructure communities depend on."
    ),
    "uw-computer-science-and-engineering-phd": (
        "PhD applicants ready to pursue funded dissertation research across theory, systems, "
        "robotics, and data-intensive science. This doctoral program fits those committed to "
        "advancing the field through sustained, mentored inquiry at the research frontier."
    ),
    "uw-electrical-and-computer-engineering-phd": (
        "Prospective doctoral students ready to advance electrical and computer engineering through "
        "original research. This funded, faculty-mentored PhD fits those prepared to commit to a "
        "dissertation that pushes the boundaries of devices, systems, and computing."
    ),
    "uw-industrial-engineering-phd": (
        "PhD applicants who want to advance industrial engineering and the analysis of complex "
        "systems through original research. This funded, faculty-mentored program fits those ready to "
        "dedicate years to a dissertation that improves how integrated systems perform."
    ),
    "uw-materials-science-and-engineering-phd": (
        "Prospective doctoral students ready to advance materials science and engineering through "
        "original research on structure, properties, and design. This funded, faculty-mentored PhD "
        "fits those prepared to commit to a dissertation at the interdisciplinary research frontier."
    ),
    "uw-mechanical-engineering-phd": (
        "PhD applicants who want to advance robotics, thermodynamics, or biomechanics through "
        "original research. This funded, faculty-mentored doctoral program fits those ready to commit "
        "to a dissertation that deepens our understanding of machines and motion."
    ),
    "uw-aquatic-conservation-and-ecology-bs": (
        "Undergraduates drawn to rivers, lakes, and coastal waters who want to understand how aquatic "
        "ecosystems function and how to protect the species that depend on them. A good fit if you "
        "picture fieldwork, water-quality science, and conservation rather than a desk-bound major."
    ),
    "uw-atmospheric-and-climate-science-bs": (
        "Undergraduates fascinated by weather, storms, and a changing climate who enjoy physics and "
        "math applied to the real atmosphere. Suited to students who want to read the sky "
        "quantitatively and trace the processes that drive heat, wind, and precipitation."
    ),
    "uw-earth-and-space-sciences-bs": (
        "Undergraduates curious about how the planet works across rock, water, ice, and air, and how "
        "those systems connect. A fit if you like getting into the field and the lab to investigate "
        "Earth's deep history and the forces still shaping it."
    ),
    "uw-environmental-science-and-terrestrial-resource-management-bs": (
        "Undergraduates who want to pair physical and biological science with the practical "
        "management of land, soils, and forests. Built for students aiming to solve real "
        "environmental problems on the ground rather than study them only in the abstract."
    ),
    "uw-environmental-studies-bs": (
        "Undergraduates interested in the intersection of people, policy, and the environment who "
        "think across disciplines rather than within one. A strong match if you want to understand "
        "human impact on natural systems and work toward more sustainable choices."
    ),
    "uw-marine-biology-bs": (
        "Undergraduates captivated by life in the sea, from plankton to marine mammals, who want "
        "hands-on time studying ocean organisms. Suited to students ready for shoreline and "
        "laboratory work and the biology of marine ecosystems."
    ),
    "uw-oceanography-bs": (
        "Undergraduates who want to study the ocean as a whole system, weaving together its physics, "
        "chemistry, biology, and geology. A fit for students drawn to research at sea and at coastal "
        "labs more than to a single narrow specialty."
    ),
    "uw-sustainable-bioresource-systems-engineering-bs": (
        "Undergraduates who want to apply engineering to biological systems and renewable resources "
        "rather than to machines or circuits alone. Built for students set on designing sustainable "
        "solutions at the meeting point of biology, engineering, and the environment."
    ),
    "uw-aquatic-and-fishery-sciences-ms": (
        "Graduate students who want to manage and understand fisheries and aquatic populations "
        "through rigorous science. A fit if you bring a quantitative bent and aim to apply ecology "
        "and stock assessment to real conservation and management decisions."
    ),
    "uw-atmospheric-and-climate-science-ms": (
        "Graduate students ready to deepen their command of atmospheric and climate science through "
        "advanced coursework, modeling methods, and a thesis or capstone. Suited to those building "
        "toward research or applied work on weather, climate, and air systems."
    ),
    "uw-earth-and-space-sciences-ms": (
        "Graduate students who want to advance their study of Earth's interconnected spheres with "
        "specialized coursework and a focused thesis or project. A good match if you are sharpening "
        "field, lab, or analytical skills for a geoscience career."
    ),
    "uw-environmental-and-forest-sciences-ms": (
        "Graduate students focused on forests and woodlands who want to manage, restore, and sustain "
        "these landscapes through science. Suited to those seeking advanced training in conservation "
        "and forest ecosystem management before professional or research work."
    ),
    "uw-forest-resources-ms": (
        "Graduate students who want to bridge the biological, physical, and managerial sides of "
        "forestry across plantations and natural stands. A fit if you aim to lead resource decisions "
        "that balance ecology, economics, and stewardship."
    ),
    "uw-marine-affairs-ms": (
        "Graduate students drawn to ocean policy and governance who want to work where science meets "
        "law, economics, and society. Built for those preparing to shape how coasts and oceans are "
        "managed by agencies, communities, and stakeholders."
    ),
    "uw-oceanography-ms": (
        "Graduate students who want to build advanced expertise in physical oceanography, marine "
        "ecology, and climate through coursework, quantitative methods, and a thesis or capstone. "
        "Suited to those preparing for research or applied ocean science."
    ),
    "uw-quantitative-ecology-and-resource-management-ms": (
        "Graduate students who love mathematics and statistics and want to turn those tools on "
        "ecological and resource problems. A strong fit if you aim to model populations, ecosystems, "
        "and management strategies with analytical rigor."
    ),
    "uw-aquatic-and-fishery-sciences-phd": (
        "Prospective doctoral students pursuing original research on aquatic and fishery science, "
        "typically with funding and faculty mentorship. A fit if you want to lead independent "
        "investigation into aquatic populations, ecosystems, and their management."
    ),
    "uw-atmospheric-and-climate-science-phd": (
        "PhD applicants aiming to drive original research on the atmosphere and climate, supported by "
        "a faculty-mentored dissertation and graduate funding. Suited to those committed to advancing "
        "understanding of weather, climate dynamics, and the changing earth system."
    ),
    "uw-earth-and-space-sciences-phd": (
        "Prospective doctoral students set on original research across the solid earth, oceans, ice, "
        "and atmosphere, backed by mentorship and funding. A fit for those ready to contribute new "
        "knowledge about how the planet evolves and behaves."
    ),
    "uw-environmental-and-forest-sciences-phd": (
        "PhD applicants pursuing deep, independent research in forest and environmental science, with "
        "a faculty-mentored dissertation and graduate funding. Suited to those who want to generate "
        "the science behind conservation and ecosystem stewardship."
    ),
    "uw-oceanography-phd": (
        "Prospective doctoral students committed to original research in physical oceanography, "
        "marine ecology, and climate, with mentorship and funding. A fit if you want to spend years "
        "investigating the ocean and its role in the earth system."
    ),
    "uw-quantitative-ecology-and-resource-management-phd": (
        "PhD applicants who want to push the methods of quantitative ecology forward, applying "
        "advanced mathematics and statistics to ecological research. Suited to those pursuing a "
        "funded, dissertation-driven path at the analytical edge of the field."
    ),
    "uw-information-management-ms": (
        "Working professionals who want to lead how organizations capture, store, and use information "
        "will fit this online master's well. If you are balancing a career with study and want "
        "optimized, practical command of information management, the flexible delivery lets you build "
        "that expertise without stepping away from work."
    ),
    "uw-information-science-ms": (
        "Graduate students fascinated by how information is organized, retrieved, moved, and "
        "protected will find their fit here. If you want rigorous study across the analysis, "
        "classification, and stewardship of information, paired with applied inquiry and methods, "
        "this iSchool master's matches that intellectual curiosity."
    ),
    "uw-library-and-information-science-ms": (
        "Best for graduate students drawn to service-minded information work as librarians or "
        "archivists. If you care about digital curation, information ethics, and connecting "
        "communities to knowledge, and you want a flexible online path into the profession, this MLIS "
        "prepares you for that calling."
    ),
    "uw-museology-ms": (
        "Graduate students who love museums and want to shape what they do belong here. If you are "
        "drawn to curation, preservation, public programming, and education, and you want to "
        "understand the role museums play in society, this program prepares you for thoughtful work "
        "inside cultural institutions."
    ),
    "uw-information-science-phd": (
        "Prospective doctoral students who want to advance how we understand and steward information "
        "will fit this funded, research-intensive program. It suits those ready to commit to a "
        "faculty-mentored dissertation and original scholarship across the analysis, organization, "
        "and protection of information, with academic or research careers in view."
    ),
    "uw-data-science-ms": (
        "Graduate students who want to extract meaning from messy, large-scale data will fit this "
        "interdisciplinary master's. If you enjoy working across statistics, computing, and "
        "visualization to draw knowledge from structured and unstructured data, and you want both "
        "technical depth and breadth, this program meets that ambition."
    ),
    "uw-human-computer-interaction-and-design-ms": (
        "Graduate students who care how people actually experience technology will thrive here. If "
        "you want to study and shape how people operate and engage with computer systems, blending "
        "design sensibility with research and method, this master's prepares you to make technology "
        "more usable and humane."
    ),
    "uw-molecular-and-cellular-biology-ms": (
        "Graduate students drawn to the molecular machinery of life will fit this master's. If you "
        "want to understand the structures and chemical processes underlying activity within and "
        "between cells, and you are ready for advanced, lab-grounded study, this program builds the "
        "foundation for research or further graduate work."
    ),
    "uw-molecular-engineering-ms": (
        "Graduate students who want to design matter at the molecular level will find their fit here. "
        "If you are drawn to engineering molecular properties and interactions to build better "
        "materials, systems, and processes, and you enjoy work at the boundary of science and "
        "engineering, this master's suits you."
    ),
    "uw-neuroscience-ms": (
        "Graduate students captivated by the brain will fit this master's. If you want advanced study "
        "of neural circuits and cognitive neuroscience, and you are ready to develop the methods and "
        "lab skills that brain research demands, this program prepares you for research roles or "
        "doctoral study."
    ),
    "uw-individual-phd-phd": (
        "Prospective doctoral students whose questions cross the boundaries of established "
        "disciplines belong in this individualized PhD. Typically funded and research-driven, it "
        "suits independent scholars who need to combine multiple fields into one coherent program of "
        "study and are ready to chart and defend an original research path."
    ),
    "uw-molecular-and-cellular-biology-phd": (
        "Prospective doctoral students aiming for careers in life-science research will fit this "
        "funded program. It suits those ready to commit to a faculty-mentored dissertation "
        "investigating the molecular and cellular basis of biological activity, and who want the "
        "sustained, independent inquiry that doctoral science requires."
    ),
    "uw-molecular-engineering-phd": (
        "Prospective doctoral students who want to engineer at the molecular scale will fit this "
        "funded, research-intensive program. It suits those ready for a faculty-mentored dissertation "
        "designing molecular properties and interactions into new materials and systems, working "
        "across the frontier where science and engineering meet."
    ),
    "uw-neuroscience-phd": (
        "Prospective doctoral students determined to understand the brain will fit this funded "
        "program. It suits those ready to dedicate years to a faculty-mentored dissertation on neural "
        "circuits and cognitive neuroscience, and who want the deep, independent research training "
        "that a career in neuroscience demands."
    ),
    "uw-jurisprudence-ms": (
        "Graduate students and professionals who want to engage seriously with legal theory, "
        "examining what law is and what it ought to be, without pursuing the bar. A fit for those "
        "whose work intersects with the law and who want a deeper, philosophical grounding in it."
    ),
    "uw-laws-ms": (
        "Practitioners and graduate students, often already trained in law, who want advanced study "
        "of how statutes, regulations, and judicial decisions shape justice. Suited to those seeking "
        "specialized legal expertise rather than a first professional law degree."
    ),
    "uw-laws-in-taxation-ms": (
        "Lawyers and finance professionals who want to specialize in tax law, mastering how "
        "authorities assess and collect taxes within a legal framework. A strong fit if your career "
        "centers on tax planning, compliance, or advisory work and you want rigorous, applied "
        "expertise."
    ),
    "uw-law-prof": (
        "Future lawyers ready to commit to the full professional degree, drawn to Pacific Rim law, "
        "tribal sovereignty, or technology and intellectual-property practice. Choose this if you "
        "intend to practice law and want preparation grounded in the legal questions shaping the "
        "region."
    ),
    "uw-law-phd": (
        "Prospective doctoral students aiming to become legal scholars, with interests in "
        "jurisprudence, empirical legal studies, or interdisciplinary research. A fit for those who "
        "already hold a law degree and want a research career in academia rather than legal practice."
    ),
    "uw-anatomic-pathology-ms": (
        "Graduate students fascinated by diagnosing disease through the examination of organs and "
        "tissues at every scale, from gross specimens to molecular markers. A fit for detail-oriented "
        "learners drawn to the laboratory side of medicine and careful microscopic analysis."
    ),
    "uw-biochemistry-ms": (
        "Graduate students who want advanced grounding in protein structure, enzymology, and the "
        "molecular machinery of life. Suited to those who enjoy rigorous laboratory methods and want "
        "a thesis-level foundation before a research career or further doctoral study."
    ),
    "uw-bioethics-ms": (
        "Graduate students wrestling with the moral questions raised by medicine, biology, and "
        "emerging health technologies. A fit for thoughtful people, including clinicians and "
        "researchers, who want rigorous training in ethical reasoning to inform care, policy, or "
        "scholarship."
    ),
    "uw-biomedical-and-health-informatics-ms": (
        "Graduate students at the intersection of computing and medicine who want to improve how "
        "health information is managed and used. Best for those comfortable with data and software "
        "who want to make clinical knowledge more accurate, connected, and useful."
    ),
    "uw-clinical-health-services-ms": (
        "Graduate students who want to study how health care is organized, delivered, and paid for, "
        "and how to make it work better. A fit for analytically minded learners drawn to evidence, "
        "policy, and the systems-level questions behind patient outcomes."
    ),
    "uw-comparative-medicine-ms": (
        "Graduate students interested in animal health and disease and its connections to human "
        "medicine and research. Suited to those drawn to veterinary science, laboratory animal "
        "medicine, or translational research bridging species."
    ),
    "uw-genetic-counseling-ms": (
        "Graduate students who want to guide individuals and families through the medical and "
        "emotional realities of genetic risk. A strong fit for empathetic communicators who can "
        "translate complex genetics into clear, compassionate, and actionable counsel."
    ),
    "uw-genome-sciences-ms": (
        "Graduate students drawn to the structure, function, and editing of genomes and the "
        "computation that makes genomics possible. Best for those who enjoy bridging molecular "
        "biology and data, and want a thesis-grounded entry into genome research."
    ),
    "uw-health-metrics-sciences-ms": (
        "Graduate students who want to measure population health with rigor, turning data into "
        "evidence that describes how communities fare. A fit for quantitatively minded learners drawn "
        "to indicators, estimation, and the numbers behind public health decisions."
    ),
    "uw-immunology-ms": (
        "Graduate students captivated by how the immune system defends the body across organisms and "
        "disease. Suited to those who want advanced coursework and laboratory training in immune "
        "mechanisms before a research career or doctoral study."
    ),
    "uw-laboratory-medicine-ms": (
        "Graduate students drawn to the clinical laboratory, where testing of patient specimens "
        "guides diagnosis and treatment. A fit for precise, methodical learners who want to master "
        "the science behind reliable medical testing."
    ),
    "uw-microbiology-ms": (
        "Graduate students fascinated by microbes, from the mechanisms of pathogenesis to the "
        "microbial life of the environment. Suited to those who enjoy hands-on laboratory inquiry and "
        "want a thesis-level foundation in microbial science."
    ),
    "uw-molecular-medicine-and-mechanisms-of-disease-ms": (
        "Graduate students who want to understand disease at its molecular roots and how those "
        "insights become treatments. A fit for learners drawn to the convergence of chemistry, "
        "biology, and medicine in pursuit of new interventions."
    ),
    "uw-neurobiology-and-biophysics-ms": (
        "Graduate students intrigued by the nervous system and by applying the tools of physics to "
        "living systems. Best for those who enjoy quantitative, interdisciplinary inquiry and want "
        "laboratory grounding in how brains and biology work."
    ),
    "uw-occupational-therapy-ms": (
        "Graduate students preparing to help people regain the everyday activities that give life "
        "meaning after injury, illness, or disability. A fit for hands-on, person-centered learners "
        "who want a clinical career built on practical problem-solving and care."
    ),
    "uw-pharmacology-ms": (
        "Graduate students drawn to how drugs interact with the body, from absorption and action to "
        "therapeutic use and toxicity. Suited to those who want laboratory grounding in drug science "
        "before a research career or further study."
    ),
    "uw-prosthetics-and-orthotics-ms": (
        "Graduate students who want to design and fit artificial limbs and supportive devices that "
        "restore movement and independence. A fit for hands-on learners who blend clinical care, "
        "biomechanics, and craftsmanship to improve patients' mobility."
    ),
    "uw-rehabilitation-medicine-ms": (
        "Graduate students focused on restoring function and quality of life for people living with "
        "physical impairment or disability. Suited to those drawn to a practical, whole-person "
        "approach to recovery across the rehabilitation field."
    ),
    "uw-medicine-prof": (
        "Future physicians ready for the full arc of medical training, from foundational science to "
        "supervised clinical rotations. Best for people committed to patient care across a region's "
        "diverse communities and prepared for the rigor and length of becoming a doctor."
    ),
    "uw-physical-therapy-prof": (
        "Future physical therapists who want to help people move better and recover from injury, "
        "surgery, and chronic conditions. A fit for hands-on, motivating clinicians-in-training drawn "
        "to movement science and direct, long-term patient relationships."
    ),
    "uw-biochemistry-phd": (
        "Prospective doctoral students aiming to uncover the molecular mechanisms of life through "
        "original research in protein structure and enzymology. A fit for those ready for a funded, "
        "dissertation-length commitment to discovery at the bench."
    ),
    "uw-biomedical-and-health-informatics-phd": (
        "PhD applicants who want to advance the science of how computing transforms biomedicine and "
        "health care. Suited to those ready to lead original, funded research spanning data, clinical "
        "systems, and the future of medical information."
    ),
    "uw-genome-sciences-phd": (
        "Prospective doctoral students aiming to push the frontier of genomics, epigenetics, and "
        "computational biology. Best for those who thrive at the meeting of wet-lab and data science "
        "and are ready for a funded, dissertation-length research career."
    ),
    "uw-health-metrics-global-health-metrics-and-implementation-sciences-phd": (
        "PhD applicants focused on measuring global health and tracing how research becomes real- "
        "world practice. A fit for quantitatively rigorous scholars committed to a funded "
        "dissertation that turns evidence into impact across populations."
    ),
    "uw-immunology-phd": (
        "Prospective doctoral students drawn to host defense and vaccine science who want to lead "
        "original immunology research. Suited to those ready for a funded, multi-year dissertation "
        "investigating how the immune system protects and sometimes fails us."
    ),
    "uw-microbiology-phd": (
        "PhD applicants captivated by microbial pathogenesis and the microbial world beyond the "
        "clinic. A fit for those ready for a funded, dissertation-length research career probing how "
        "microbes cause disease and shape their environments."
    ),
    "uw-molecular-medicine-and-mechanisms-of-disease-phd": (
        "Prospective doctoral students who want to dissect the molecular origins of disease and "
        "translate them toward new therapies. Best for those committed to a funded, faculty-mentored "
        "dissertation at the interface of chemistry, biology, and medicine."
    ),
    "uw-neurobiology-and-biophysics-phd": (
        "PhD applicants drawn to the nervous system and to physics-based approaches to biology. A fit "
        "for quantitatively minded scholars ready for a funded, dissertation-length investigation "
        "into how brains and living systems function."
    ),
    "uw-pharmacology-phd": (
        "Prospective doctoral students who want to lead original research into how drugs act on the "
        "body and become therapies. Suited to those ready for a funded, multi-year dissertation in "
        "drug discovery and mechanism."
    ),
    "uw-rehabilitation-science-phd": (
        "PhD applicants committed to advancing the science of recovery, function, and disability "
        "through research. A fit for scholars ready for a funded, dissertation-length program that "
        "strengthens the evidence behind rehabilitation care."
    ),
    "uw-nursing-ms": (
        "Graduate nurses ready to step into advanced practice, health-systems leadership, or "
        "research. A fit for registered nurses who want to deepen their clinical expertise and take "
        "on broader responsibility for patient care and the systems around it."
    ),
    "uw-nursing-practice-prof": (
        "Nurses pursuing the highest level of clinical practice, blending the art and science of "
        "caring with advanced training. Best for those ready to lead at the bedside and beyond, "
        "translating evidence into better care for patients and communities."
    ),
    "uw-nursing-phd": (
        "Prospective doctoral students aiming to build the science of nursing and shape health- "
        "systems leadership through research. A fit for those ready for a funded, faculty-mentored "
        "dissertation that advances how care is understood and delivered."
    ),
    "uw-biomedical-regulatory-affairs-ms": (
        "Graduate students who want to navigate the rules that govern medical products from "
        "development to market. A fit for detail-driven learners drawn to the compliance, strategy, "
        "and communication that bring safe therapies and devices into patients' hands."
    ),
    "uw-health-economics-and-outcomes-research-ms": (
        "Graduate students who want to study the value, cost, and behavior behind health care "
        "decisions. Suited to analytically minded learners drawn to economics and evidence, and "
        "interested in how care is produced, priced, and improved."
    ),
    "uw-medicinal-chemistry-ms": (
        "Graduate students drawn to designing the molecules that become medicines, at the meeting "
        "point of chemistry and pharmacy. A fit for those who enjoy synthesis and molecular problem- "
        "solving and want a thesis-level foundation in drug design."
    ),
    "uw-pharmaceutics-ms": (
        "Graduate students interested in how a drug becomes a safe, effective medication a patient "
        "can actually use. Suited to those drawn to formulation, delivery, and the science of turning "
        "compounds into reliable therapies."
    ),
    "uw-pharmacy-prof": (
        "Future pharmacists committed to the safe, effective, and accessible use of medicines. A fit "
        "for people who want to be the medication expert on a care team, combining science, "
        "counseling, and a steady, detail-oriented approach to patient safety."
    ),
    "uw-health-economics-and-outcomes-research-phd": (
        "PhD applicants who want to lead research on the value, cost, and outcomes of health care. A "
        "fit for rigorous, quantitatively minded scholars ready for a funded dissertation shaping how "
        "treatments are evaluated and resources allocated."
    ),
    "uw-medicinal-chemistry-phd": (
        "Prospective doctoral students aiming to discover and design new drug molecules through "
        "original research. Suited to those ready for a funded, dissertation-length commitment to "
        "synthesis and the chemistry behind future medicines."
    ),
    "uw-pharmaceutics-phd": (
        "PhD applicants focused on advancing how drugs are formulated, delivered, and made effective "
        "in the body. A fit for those ready for a funded, faculty-mentored dissertation in the "
        "science of turning compounds into dependable therapies."
    ),
    "uw-public-service-and-policy-bs": (
        "Undergraduates who want to put public purpose into practice will fit this Evans School "
        "major. If you care about how policy is analyzed and made, value civic engagement, and want "
        "hands-on experience through internships with public agencies, this program connects your "
        "sense of service to real-world work."
    ),
    "uw-public-administration-ms": (
        "Graduate students and emerging public-sector leaders belong in this Master of Public "
        "Administration. If you want to lead in government, nonprofit, or policy roles and are ready "
        "to build the management and analytical skills those careers demand, this Evans School "
        "program prepares you for that responsibility."
    ),
    "uw-public-policy-and-management-ms": (
        "Graduate students who want to shape and run effective policy will fit this program. If you "
        "are drawn to designing the laws, regulations, and programs that address social problems, and "
        "you want both the analytical and management tools to carry policy from idea to "
        "implementation, this master's fits."
    ),
    "uw-public-policy-and-management-phd": (
        "Prospective doctoral students who want to study policy and governance rigorously will fit "
        "this funded program. It suits those ready for a faculty-mentored dissertation advancing how "
        "public policy and management are understood and improved, with academic, research, or high- "
        "level analytical careers in mind."
    ),
    "uw-environmental-public-health-bs": (
        "Undergraduates who want to protect human health by understanding the air, water, food, and "
        "surroundings people live in. A fit for students set on identifying environmental hazards and "
        "the science of controlling them to keep communities well."
    ),
    "uw-food-systems-nutrition-and-health-bs": (
        "Undergraduates interested in how food and nutrition shape health, from biochemistry to the "
        "systems that feed communities. Suited to students who want to connect what we eat to "
        "wellbeing, equity, and public health outcomes."
    ),
    "uw-public-health-global-health-bs": (
        "Undergraduates who want to prevent disease and promote health at the community and global "
        "scale through organized, evidence-based action. A strong match if you care about health "
        "equity across borders and want a foundation in public and global health."
    ),
    "uw-biostatistics-ms": (
        "Graduate students with a quantitative foundation who want to develop and apply statistical "
        "methods to biomedical and public health questions. Suited to those preparing for analytical "
        "roles in research, where data shapes clinical and population decisions."
    ),
    "uw-environmental-health-sciences-ms": (
        "Graduate students focused on how the natural and built environment affects human health, "
        "from exposures to interventions. A fit if you want advanced training to assess and reduce "
        "environmental risks across workplaces and communities."
    ),
    "uw-epidemiology-ms": (
        "Graduate students who want to study the patterns and determinants of disease in populations "
        "and turn that analysis into prevention. Suited to those building the methodological skills "
        "to investigate outbreaks, risk factors, and health trends."
    ),
    "uw-genetic-epidemiology-ms": (
        "Graduate students interested in how genetic factors and the environment together shape "
        "health and disease across families and populations. A fit for those who want to combine "
        "epidemiologic methods with genetics to understand inherited risk."
    ),
    "uw-global-health-ms": (
        "Graduate students committed to improving health and advancing equity for populations "
        "worldwide. Suited to those who want rigorous training to research and address health "
        "challenges in a global, cross-cultural context."
    ),
    "uw-health-administration-ms": (
        "Working professionals aiming to lead and manage health care systems, hospitals, and "
        "networks, with this program delivered online. A fit if you want to build administrative and "
        "leadership skills while staying in your current role."
    ),
    "uw-health-informatics-and-health-information-management-ms": (
        "Graduate students drawn to the intersection of health care, data, and information systems, "
        "in an online program. Suited to those who want to manage and apply health information to "
        "improve how care is delivered and measured."
    ),
    "uw-health-systems-and-population-health-ms": (
        "Graduate students focused on the health outcomes of whole populations and how systems can "
        "improve them. A fit for those who want to study the distribution of health across groups and "
        "work to make it more equitable."
    ),
    "uw-nutritional-sciences-ms": (
        "Graduate students who want a deeper, science-based command of how the body uses nutrients "
        "and how diet affects health. Suited to those pursuing research or advanced practice grounded "
        "in the biochemistry and physiology of nutrition."
    ),
    "uw-pathobiology-ms": (
        "Graduate students fascinated by the biology of disease who want to study its mechanisms "
        "across organisms and systems. A fit for those building toward laboratory research in "
        "infectious disease, pathology, and the processes that drive illness."
    ),
    "uw-public-health-genetics-ms": (
        "Graduate students who want to use genomic information to benefit population health through "
        "more targeted prevention and care. Suited to those bridging genetics, ethics, and public "
        "health to translate discoveries into community benefit."
    ),
    "uw-public-health-nutrition-ms": (
        "Graduate students who want to apply nutrition science to the health of communities and "
        "populations rather than individuals alone. A fit if you aim to shape food and nutrition "
        "programs, policy, and interventions that improve public wellbeing."
    ),
    "uw-biostatistics-phd": (
        "Prospective doctoral students who want to develop new statistical methods for biomedical "
        "research, with a faculty-mentored dissertation and funding. Suited to those drawn to the "
        "theory and innovation behind data analysis in health science."
    ),
    "uw-environmental-health-sciences-phd": (
        "PhD applicants pursuing original research on how environmental exposures affect human "
        "health, supported by mentorship and graduate funding. A fit for those who want to generate "
        "the evidence that protects workers and communities."
    ),
    "uw-epidemiology-phd": (
        "Prospective doctoral students committed to advancing population health and the methods that "
        "measure it, through a funded, dissertation-driven path. Suited to those who want to lead "
        "independent research into the causes and prevention of disease."
    ),
    "uw-global-health-global-health-metrics-and-implementation-sciences-phd": (
        "PhD applicants focused on measuring global health and getting evidence into policy and "
        "practice. A fit for those who want to research how health metrics and implementation science "
        "can close the gap between knowledge and real-world impact."
    ),
    "uw-health-services-phd": (
        "Prospective doctoral students drawn to how people access care, what it costs, and what "
        "happens to patients as a result. Suited to those pursuing original, multidisciplinary "
        "research on health systems and the policies that shape them."
    ),
    "uw-nutritional-sciences-phd": (
        "PhD applicants who want to advance the science of nutrition, from metabolic biochemistry to "
        "community-level study, with mentorship and funding. A fit for those committed to original "
        "research on how diet shapes health across populations."
    ),
    "uw-pathobiology-phd": (
        "Prospective doctoral students set on investigating infectious disease and comparative "
        "pathology through original, funded research. Suited to those who want to spend years "
        "uncovering the biological mechanisms behind illness and its spread."
    ),
    "uw-public-health-genetics-phd": (
        "PhD applicants who want to research how genetics and genomics can serve population health, "
        "supported by a faculty-mentored dissertation and funding. A fit for those bridging science, "
        "ethics, and policy to apply genetic knowledge for public benefit."
    ),
    "uw-social-welfare-bs": (
        "Undergraduates who want to help meet people's basic needs and strengthen the well-being of "
        "individuals, families, and communities. A good match if you're drawn to direct service and "
        "social justice and are considering a career in the social-work profession."
    ),
    "uw-social-work-ms": (
        "Graduate students preparing to practice social work, ready to draw on psychology, sociology, "
        "policy, and community knowledge to assess needs and design interventions. The professional "
        "degree for those who want to work directly with people and the systems that shape their "
        "lives."
    ),
    "uw-social-welfare-phd": (
        "Prospective doctoral students who want to research social policy and community-based "
        "intervention at the highest level, with faculty mentorship and graduate funding. Suited to "
        "experienced practitioners and scholars aiming to build the evidence behind effective, just "
        "social services."
    ),
}

_missing_who = [s for s in PROGRAM_SLUGS if s not in _WHO_BY_SLUG]
if _missing_who:
    raise ValueError(f"UW who_its_for missing on {len(_missing_who)} rows: {_missing_who[:5]}")
_stray_who = [s for s in _WHO_BY_SLUG if s not in set(PROGRAM_SLUGS)]
if _stray_who:
    raise ValueError(f"UW who_its_for has stray slugs: {_stray_who[:5]}")
# Distinctness gate (REPAIR_BACKLOG #3b) — program-distinct, never a degree-type template.
_who_vals = [v.strip() for v in _WHO_BY_SLUG.values()]
if len(set(_who_vals)) / max(1, len(_who_vals)) < 0.9:
    raise ValueError(
        f"UW who_its_for not program-distinct: {len(set(_who_vals))}/{len(_who_vals)} distinct"
    )


def apply(session: Session) -> bool:
    """Enrich UW to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when the institution is absent — safe on fresh/CI databases.
    """
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    school_outcomes["_standard"] = _standard(_OMITTED_INSTITUTION)
    inst.school_outcomes = school_outcomes
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    inst.founded_year = 1861
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.washington.edu"
    _hero = SCHOOL_OUTCOMES["campus_photos"][0]["url"]
    _gallery = [u for u in (inst.media_gallery or []) if u != _hero]
    inst.media_gallery = [_hero, *_gallery]
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
    meta_by_name = {m["name"]: m for m in _SCHOOL_META}
    by_name: dict[str, School] = {}
    for spec in SCHOOLS:
        sc = existing.get(spec["name"])
        if sc is None:
            sc = School(institution_id=inst.id, name=spec["name"])
            session.add(sc)
        sc.description_text = spec["description"]
        sc.sort_order = spec["sort_order"]
        sc.catalog_source = "curated"
        sc.website_url = SCHOOL_WEBSITE.get(spec["name"])
        m = meta_by_name[spec["name"]]
        about = _about_for(m)
        about["_standard"] = _standard(_about_omitted(m))
        sc.about_detail = about
        sc.content_sources = _school_content(spec["name"])
        by_name[spec["name"]] = sc
    for name, sc in existing.items():
        if name not in canonical_names:
            session.delete(sc)
    session.flush()
    return by_name


def _program_has_dependents(session: Session, program_id) -> bool:
    fks = session.execute(
        text("""
        SELECT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND ccu.table_name = 'programs' AND ccu.column_name = 'id'
          AND tc.table_name <> 'programs'
        """)
    ).fetchall()
    for table, col in fks:
        hit = session.execute(
            text(f'SELECT 1 FROM "{table}" WHERE "{col}" = :pid LIMIT 1'), {"pid": program_id}
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
        p.website_url = _website_for(spec)
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "on_campus")
        p.cip_code = spec.get("cip")  # matcher-core CIP join key (REPAIR_BACKLOG #1)
        _kw = _PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(_KEYWORDS_BY_SCHOOL[spec["school"]])
        p.content_sources = _program_content(spec["school"], _kw)
        p.tuition = _tuition_for(spec)
        if spec["degree_type"] == "bachelors":
            p.cost_data = _undergrad_cost(spec)
        else:
            p.cost_data = _grad_cost(spec)
        p.application_requirements = _requirements_for(spec)
        outcomes = dict(_OUTCOMES_BY_SLUG.get(slug, {}))
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        p.who_its_for = _WHO_BY_SLUG.get(slug)
        p.highlights = None
        p.application_deadline = None
    session.flush()
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
