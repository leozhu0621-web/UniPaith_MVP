"""Carnegie Mellon University — university-granularity profile, enriched to the
canonical profile standard (institution + every school + a breadth-first program
catalog), mirroring ``mit_profile.py`` / ``harvard_profile.py``.

Every value is verified against an authoritative source and carries a citation;
anything that could not be cleanly verified is honestly recorded in a node's
``_standard.omitted`` rather than guessed. Institution statistics are from CMU's
Common Data Set 2024-2025 (Fall 2024 / Class of 2028 cohort) and the U.S. Dept.
of Education College Scorecard for UNITID 211440, cross-checked where they
overlap. The program set is breadth-first: every substantive degree program
across all seven colleges is created with verified *basics* (name, degree,
delivery format, department, official page); deeper per-program fields (tracks,
class profile, faculty, reviews, program-specific outcomes) are omitted-pending
and deepened on resume runs.

Depth pass (2026-06-15, cmuprof4): merged ``DEPTH_REVIEWS`` for 66 coverable
programs — completes CMU coverable external_reviews (71/71).

Description depth pass (2026-06-16, cmuprof5): replaces all classification-only
``{name} is a {degree} in the {dept} within CMU's {school}`` stubs with
field-specific clauses from ``cmu_field_descriptions.py`` (180/180 programs).

Idempotent: ``apply(session)`` enriches the existing CMU institution (no-op when
absent, e.g. on a fresh CI database), creating/reconciling its schools + programs.
"""

from __future__ import annotations

# ruff: noqa: E501
import re
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.carnegie_mellon_reviews_depth import DEPTH_REVIEWS
from unipaith.data.cmu_field_descriptions import SLUG_DESCRIPTIONS
from unipaith.data.profile_catalog_utils import validate_catalog
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Carnegie Mellon University"
ENRICHED_AT = "2026-06-16"

_CLASSIFICATION_STUB_RE = re.compile(
    r"^.+ is a .+ in the .+ within Carnegie Mellon University's .+",
)


def _standard(omitted: list[str] | None = None) -> dict:
    """The per-node provenance stamp written onto every enriched node."""
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


# ── Institution-level data ────────────────────────────────────────────────────
# University-wide first-destination outcomes are published by CMU only through an
# interactive Tableau dashboard (which itself excludes Heinz/Tepper graduate, the
# Entertainment Technology Center, and the Qatar campus), with no fetchable,
# citable university-wide aggregate — so both institution outcome fields are
# honestly omitted rather than guessed.
_OMITTED_INSTITUTION = [
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
]

# Rankings + ownership/classification/accreditor. ranking entries are {rank, year}
# objects (the detail page renders any ranking_data entry with a numeric `rank`).
RANKING_DATA: dict = {
    "ownership_type": "private",
    "carnegie_classification": (
        "R1: Doctoral Universities – Very High Research Spending and Doctorate Production"
    ),
    "accreditor": "MSCHE (Middle States Commission on Higher Education)",
    "qs_world_university_rankings": {
        "rank": 52,
        "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/carnegie-mellon-university",
    },
    "times_higher_education": {
        "rank": 24,
        "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/carnegie-mellon-university",
    },
    "us_news_national": {
        "rank": 20,
        "year": 2026,
        "source_url": "https://www.usnews.com/best-colleges/carnegie-mellon-university-3242",
    },
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below
# is complete. Every figure is sourced (CDS 2024-25 + College Scorecard 211440).
SCHOOL_OUTCOMES: dict = {
    # College Scorecard (UNITID 211440, latest release).
    "admit_rate": 0.1166,  # CDS 2024-25 §C1: 3,959 admits / 33,941 applicants (Fall 2024)
    "avg_net_price": 31944,
    "median_earnings_10yr": 114862,
    "graduation_rate_6yr": 0.9413,
    "completion_rate_4yr_150pct": 0.9413,
    "retention_rate_first_year": 0.98,
    # CDS 2024-25 §C1 — Fall 2024 entering first-year class (Class of 2028).
    "flagship": {
        "applicants": 33941,
        "admits": 3959,
        "enrolled": 1808,
        "admissions_cycle": "Class of 2028 / Fall 2024 entering",
    },
    # CDS 2024-25 §C9 — enrolled first-years, Fall 2024.
    "test_scores": {
        "sat_reading_25_75": [730, 770],
        "sat_math_25_75": [770, 800],
        "sat_total_25_75": [1510, 1560],
        "act_25_75": [34, 35],
    },
    # CMU Student Financial Services 2025-26 (cost of attendance) + College Scorecard.
    "financial_aid": {
        "cost_of_attendance": 92947,
        "pell_grant_rate": 0.1604,
        "federal_loan_rate": 0.3357,
        "median_debt_completers": 21750,
    },
    # CDS 2024-25 §B2 — degree-seeking undergraduates, all campuses (base 7,744).
    "demographics": {
        "white": 0.205,
        "black": 0.038,
        "hispanic": 0.094,
        "asian": 0.326,
        "two_or_more": 0.051,
        "international": 0.233,
        "american_indian": 0.0001,
        "native_hawaiian": 0.0003,
        "unknown": 0.053,
    },
    # Research areas + labs WITH links (institution scale + research/campus-life).
    "research": {
        "areas": [
            "Artificial intelligence and machine learning",
            "Robotics and autonomous systems",
            "Human-computer interaction",
            "Language technologies and natural language processing",
            "Cybersecurity and privacy",
            "Software engineering",
        ],
        "labs": [
            "Robotics Institute",
            "Software Engineering Institute (SEI)",
            "Human-Computer Interaction Institute (HCII)",
            "Language Technologies Institute (LTI)",
            "Machine Learning Department",
            "CyLab Security and Privacy Institute",
        ],
        "lab_links": {
            "Robotics Institute": "https://www.ri.cmu.edu/",
            "Software Engineering Institute (SEI)": "https://www.sei.cmu.edu/",
            "Human-Computer Interaction Institute (HCII)": "https://hcii.cmu.edu/",
            "Language Technologies Institute (LTI)": "https://www.lti.cs.cmu.edu/",
            "Machine Learning Department": "https://www.ml.cmu.edu/",
            "CyLab Security and Privacy Institute": "https://www.cylab.cmu.edu/",
        },
    },
    "campus_life": {
        "student_orgs": 400,
        "varsity_sports": 19,
        "athletics_division": "NCAA Division III (University Athletic Association)",
        "resources": [
            {
                "name": "Get Involved - Student Affairs",
                "url": "https://www.cmu.edu/student-affairs/get-involved/index.html",
            },
            {
                "name": "Student Involvement & Traditions",
                "url": "https://www.cmu.edu/student-affairs/sit/involvement/index.html",
            },
            {"name": "Carnegie Mellon Athletics (Tartans)", "url": "https://athletics.cmu.edu/"},
            {"name": "CMU Events Calendar", "url": "https://events.cmu.edu/"},
            {
                "name": "Center for Student Diversity and Inclusion",
                "url": "https://www.cmu.edu/student-diversity/",
            },
        ],
    },
    "scale": {
        "faculty_count": 1615,
        "student_faculty_ratio": "6:1",
        "endowment_usd": 3484600000,
        "campus_acres": 157,
    },
    "location": {"lat": 40.4433, "lng": -79.9436},
    "campus_basics": {"location": "Pittsburgh, Pennsylvania"},
    # Verified outdoor campus scenes — Wikimedia Commons API extmetadata (Artist +
    # LicenseShortName), landscape ≥1920px thumburl. Hero uses [0]; gallery lightbox
    # cycles the rest.
    "campus_photos": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/"
                "Hamerschlag_Hall_at_Carnegie_Mellon_University.jpg/"
                "1920px-Hamerschlag_Hall_at_Carnegie_Mellon_University.jpg"
            ),
            "credit": "Wikimedia Commons / Jiuguang Wang (CC BY-SA 2.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/"
                "Carnegie_Mellon_The_Cut_Planet.JPG/"
                "1920px-Carnegie_Mellon_The_Cut_Planet.JPG"
            ),
            "credit": "Wikimedia Commons / 燃灯 (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/"
                "Carnegie_Mellon_University_East-West_walkway.jpg/"
                "1920px-Carnegie_Mellon_University_East-West_walkway.jpg"
            ),
            "credit": "Wikimedia Commons / Dllu (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/"
                "Carnegie_Mellon_University_from_Centre_Avenue%2C_2024-03-07.jpg/"
                "1920px-Carnegie_Mellon_University_from_Centre_Avenue%2C_2024-03-07.jpg"
            ),
            "credit": "Wikimedia Commons / Cbaile19 (CC0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/"
                "Carnegie_Mellon_University_Legacy_Plaza.jpg/"
                "1920px-Carnegie_Mellon_University_Legacy_Plaza.jpg"
            ),
            "credit": "Wikimedia Commons / Dllu (CC BY-SA 4.0)",
        },
    ],
    "media_credit": "Wikimedia Commons / Jiuguang Wang (CC BY-SA 2.0)",
    "sources": [
        {
            "label": "CMU Common Data Set 2024-2025",
            "url": "https://www.cmu.edu/ira/CDS/pdf/cds_2024-25/common-data-set-2024-2025-11apr2025.pdf",
        },
        {
            "label": "U.S. Dept. of Education College Scorecard (UNITID 211440)",
            "url": "https://collegescorecard.ed.gov/school/?211440-Carnegie-Mellon-University",
        },
        {
            "label": "CMU Student Financial Services — Undergraduate Cost 2025-26",
            "url": "https://www.cmu.edu/sfs/tuition/undergraduate/2526.html",
        },
    ],
}

UNDERGRAD_COUNT = 7824  # CDS 2024-25 §B1 (total undergraduates, Oct 15 2024)
FOUNDED_YEAR = 1900
CAMPUS_SETTING = "urban"

DESCRIPTION = (
    "Carnegie Mellon University is a private research university in Pittsburgh, "
    "Pennsylvania, formed in 1967 by the merger of the Carnegie Institute of "
    "Technology (founded by Andrew Carnegie in 1900) and the Mellon Institute of "
    "Industrial Research. It is an R1 doctoral university accredited by the Middle "
    "States Commission on Higher Education, organized into seven colleges, and is "
    "home to the world's first Robotics Institute (1979) and the first academic "
    "Machine Learning Department (2006). CMU is consistently ranked first in the "
    "United States for its computer science and artificial intelligence programs, "
    "and is known for an interdisciplinary culture that pairs technology with the "
    "arts, business, public policy, and the sciences."
)

# Channel feeds + official social links (drives the daily Updates/Events ingest).
# Verified HTTP 200, 2026-06-11:
#   • CMU News RSS — 40 items, each with a media:content webp cover image:
#     https://www.cmu.edu/news/feeds/news.rss
#   • CMU Events iCalendar (BEGIN:VCALENDAR): https://events.cmu.edu/live/ical/events
# CMU runs a single university-wide news system (no per-college RSS), so every school
# and program below filters this shared feed by keywords naming the college/department
# (the MIT/MBAn pattern) — content_sources is never left null, so their Events & Updates
# tabs populate just like the institution's.
_CMU_NEWS_RSS = "https://www.cmu.edu/news/feeds/news.rss"
_CMU_EVENTS_ICS = {"url": "https://events.cmu.edu/live/ical/events", "type": "ical"}
_SOCIAL_CMU = {
    "instagram": "https://www.instagram.com/carnegiemellon/",
    "linkedin": "https://www.linkedin.com/company/carnegie-mellon-university/",
    "x": "https://x.com/carnegiemellon",
    "youtube": "https://www.youtube.com/carnegiemellonu",
    "facebook": "https://www.facebook.com/carnegiemellonu",
}

_INSTITUTION_CONTENT = {
    "news_rss": _CMU_NEWS_RSS,
    "news_url": "https://www.cmu.edu/news/",
    "news_curated": True,  # the CMU News feed is all-university news — keep every item
    "events_feed": dict(_CMU_EVENTS_ICS),
    "social": dict(_SOCIAL_CMU),
}

# Hamerschlag Hall leads the institution hero; see ``SCHOOL_OUTCOMES["campus_photos"]``.
_CAMPUS_PHOTO = SCHOOL_OUTCOMES["campus_photos"][0]["url"]

# ── The seven real degree-granting colleges (official "Colleges & Schools") ────
_SCS = "School of Computer Science"
_CIT = "College of Engineering"
_DIETRICH = "Marianna Brown Dietrich College of Humanities and Social Sciences"
_MCS = "Mellon College of Science"
_CFA = "College of Fine Arts"
_TEPPER = "Tepper School of Business"
_HEINZ = "Heinz College of Information Systems and Public Policy"

SCHOOLS: list[dict] = [
    {
        "name": _SCS,
        "sort_order": 1,
        "description": (
            "Carnegie Mellon's School of Computer Science spans artificial "
            "intelligence, robotics, machine learning, language technologies, "
            "human-computer interaction, software engineering, and computational "
            "biology across seven academic units."
        ),
    },
    {
        "name": _CIT,
        "sort_order": 2,
        "description": (
            "The College of Engineering (historically the Carnegie Institute of "
            "Technology) educates engineers across electrical and computer, "
            "mechanical, civil and environmental, chemical, materials, and "
            "biomedical engineering, engineering and public policy, and a set of "
            "professional institutes."
        ),
    },
    {
        "name": _DIETRICH,
        "sort_order": 3,
        "description": (
            "The Marianna Brown Dietrich College of Humanities and Social Sciences "
            "sits at the intersection of humanity and technology, spanning English, "
            "history, philosophy, psychology, statistics and data science, social "
            "and decision sciences, languages, and strategy and technology."
        ),
    },
    {
        "name": _MCS,
        "sort_order": 4,
        "description": (
            "The Mellon College of Science comprises biological sciences, "
            "chemistry, mathematical sciences, and physics, combining fundamental "
            "research with educational innovation."
        ),
    },
    {
        "name": _CFA,
        "sort_order": 5,
        "description": (
            "The College of Fine Arts is one of the oldest degree-granting fine "
            "arts institutions in the U.S., comprising the Schools of Architecture, "
            "Art, Design, Drama, and Music."
        ),
    },
    {
        "name": _TEPPER,
        "sort_order": 6,
        "description": (
            "The Tepper School of Business, founded in 1949 as the Graduate School "
            "of Industrial Administration, pioneered management science — an "
            "analytical, quantitative approach to business — and offers business, "
            "analytics, and finance degrees grounded in that tradition."
        ),
    },
    {
        "name": _HEINZ,
        "sort_order": 7,
        "description": (
            "Heinz College of Information Systems and Public Policy educates "
            "students for 'intelligent action,' uniting data analytics, technology, "
            "and policy across its School of Information Systems & Management and "
            "School of Public Policy & Management."
        ),
    },
]

_SCHOOL_WEBSITE = {
    _SCS: "https://www.cs.cmu.edu/",
    _CIT: "https://engineering.cmu.edu/",
    _DIETRICH: "https://www.cmu.edu/dietrich/",
    _MCS: "https://www.cmu.edu/mcs/",
    _CFA: "https://cfa.cmu.edu/",
    _TEPPER: "https://www.cmu.edu/tepper/",
    _HEINZ: "https://www.heinz.cmu.edu/",
}

# Per-school keyword filters over the shared CMU News feed (OR-matched, case-
# insensitive, word-boundary by the ingest). Terms name the college/department as it
# appears in CMU headlines, so each school's Events & Updates tab is populated (never
# null) without inventing a per-school feed CMU does not publish.
_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _SCS: [
        "School of Computer Science",
        "computer science",
        "robotics",
        "machine learning",
        "artificial intelligence",
        "AI",
        "language technologies",
        "software",
        "algorithm",
    ],
    _CIT: [
        "College of Engineering",
        "engineering",
        "engineers",
        "materials",
        "electronics",
        "robotics",
    ],
    _DIETRICH: [
        "Dietrich College",
        "humanities",
        "social sciences",
        "psychology",
        "neuroscience",
        "learning",
        "policy",
        "history",
    ],
    _MCS: [
        "Mellon College",
        "physics",
        "physicist",
        "chemistry",
        "biology",
        "biological",
        "bacteria",
        "brain",
        "neuroscience",
        "quantum",
        "mathematics",
        "mathematical",
        "universe",
        "molecular",
    ],
    _CFA: [
        "College of Fine Arts",
        "School of Drama",
        "School of Music",
        "School of Art",
        "architecture",
        "design",
        "artist",
        "artists",
        "theatre",
        "Broadway",
        "Tony",
    ],
    _TEPPER: [
        "Tepper",
        "business",
        "MBA",
        "management",
        "economics",
        "economist",
        "finance",
        "entrepreneur",
        "entrepreneurship",
    ],
    _HEINZ: [
        "Heinz College",
        "public policy",
        "information systems",
        "policy",
        "data",
        "analytics",
    ],
}


def _school_content(name: str) -> dict:
    """A school's content_sources: the shared, verified CMU feeds filtered to
    school-relevant items by keywords (the MIT/MBAn pattern)."""
    return {
        "news_rss": _CMU_NEWS_RSS,
        "news_curated": False,
        "events_feed": dict(_CMU_EVENTS_ICS),
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": dict(_SOCIAL_CMU),
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    """A program's content_sources: its school's feed, refined by program keywords
    (defaults to the school keywords so the program tab is never empty)."""
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


# Rich, sourced About-tab content per school. faculty are verified-current; where
# a required about field could not be cleanly verified it is listed in _ABOUT_OMITTED.
_ABOUT_DETAIL: dict[str, dict] = {
    _SCS: {
        "founded": 1988,
        "leadership": "Martial Hebert, Dean and University Professor of Robotics",
        "faculty": [
            "Tom M. Mitchell — Founders University Professor; machine-learning pioneer",
            "Maria-Florina (Nina) Balcan — Cadence Design Systems Professor; ML theory",
            "Guy Blelloch — Professor; parallel algorithms",
            "Jodi Forlizzi — Herbert A. Simon Professor; human-computer interaction",
        ],
        "research_centers": [
            {"name": "Robotics Institute", "url": "https://www.ri.cmu.edu/"},
            {"name": "Human-Computer Interaction Institute", "url": "https://hcii.cmu.edu/"},
            {"name": "Language Technologies Institute", "url": "https://www.lti.cs.cmu.edu/"},
            {"name": "Machine Learning Department", "url": "https://www.ml.cmu.edu/"},
            {"name": "Computer Science Department", "url": "https://csd.cmu.edu/"},
            {"name": "Software and Societal Systems Department", "url": "https://s3d.cmu.edu/"},
        ],
        "source": "https://www.cs.cmu.edu/about",
    },
    _CIT: {
        "founded": 1905,
        "leadership": (
            "Burcu Akinci, William D. and Nancy W. Strecker Dean of the College of Engineering"
        ),
        "research_centers": [
            {"name": "Information Networking Institute", "url": "https://www.cmu.edu/ini/"},
            {"name": "Integrated Innovation Institute", "url": "https://www.cmu.edu/iii/"},
            {
                "name": "Engineering and Public Policy",
                "url": "https://www.epp.engineering.cmu.edu/",
            },
            {"name": "CyLab Security and Privacy Institute", "url": "https://www.cylab.cmu.edu/"},
            {
                "name": "Manufacturing Futures Institute",
                "url": "https://engineering.cmu.edu/mfi.html",
            },
            {"name": "Parallel Data Lab", "url": "https://www.pdl.cmu.edu/"},
        ],
        "named_for": "Andrew Carnegie (as the Carnegie Institute of Technology)",
        "source": "https://engineering.cmu.edu/about-us/index.html",
    },
    _MCS: {
        "leadership": "Barbara Shinn-Cunningham, Glen de Vries Dean of the Mellon College of Science",
        "research_centers": [
            {"name": "Neuroscience Institute", "url": "https://www.cmu.edu/ni/"},
            {"name": "Pittsburgh Supercomputing Center", "url": "https://www.psc.edu/"},
            {"name": "Department of Biological Sciences", "url": "https://www.cmu.edu/bio/"},
            {"name": "Department of Chemistry", "url": "https://www.cmu.edu/chemistry/"},
            {"name": "Department of Mathematical Sciences", "url": "https://www.cmu.edu/math/"},
            {"name": "Department of Physics", "url": "https://www.cmu.edu/physics/"},
        ],
        "named_for": "the Mellon family and the Mellon Institute of Industrial Research",
        "source": "https://www.cmu.edu/mcs/about/index.html",
    },
    _CFA: {
        "founded": 1905,
        "leadership": "Mary Ellen Poole, Stanley and Marcia Gumberg Dean of the College of Fine Arts",
        "research_centers": [
            {
                "name": "Frank-Ratchye STUDIO for Creative Inquiry",
                "url": "https://studioforcreativeinquiry.org/",
            },
            {
                "name": "Institute for Contemporary Art Pittsburgh",
                "url": "https://cfa.cmu.edu/research-and-creative-practice/ica-pittsburgh",
            },
            {"name": "School of Architecture", "url": "https://www.architecture.cmu.edu/"},
            {"name": "School of Design", "url": "https://design.cmu.edu/"},
            {"name": "School of Drama", "url": "https://drama.cmu.edu/"},
            {"name": "School of Music", "url": "https://www.cmu.edu/cfa/music/"},
        ],
        "source": "https://cfa.cmu.edu/about",
    },
    _DIETRICH: {
        "founded": 1969,
        "leadership": "Richard Scheines, Bess Family Dean of the Dietrich College",
        "faculty": [
            "George Loewenstein — Herbert A. Simon University Professor of Economics and "
            "Psychology; co-founder of behavioral economics and neuroeconomics",
            "Cleotilde (Coty) Gonzalez — Research Professor; AAAS Fellow; directs the "
            "Dynamic Decision Making Lab",
        ],
        "research_centers": [
            {"name": "Neuroscience Institute", "url": "https://www.cmu.edu/ni/"},
            {"name": "Institute for Strategy & Technology (CMIST)", "url": "https://www.cmu.edu/cmist/"},
            {
                "name": "Department of Statistics & Data Science",
                "url": "https://www.cmu.edu/dietrich/statistics-datascience/",
            },
            {
                "name": "Department of Social and Decision Sciences",
                "url": "https://www.cmu.edu/dietrich/sds/",
            },
        ],
        "named_for": (
            "Marianna Brown Dietrich, mother of trustee William S. Dietrich II, whose "
            "2011 gift named the college"
        ),
        "source": "https://www.cmu.edu/dietrich/about/index.html",
    },
    _TEPPER: {
        "founded": 1949,
        "leadership": (
            "Isabelle Bajeux-Besnainou, Dean and Richard P. Simmons Professor of Finance "
            "(term through July 1, 2026)"
        ),
        "faculty": [
            "Sridhar Tayur — Ford Distinguished Research Chair and University Professor of "
            "Operations Management; member of the National Academy of Engineering",
            "Isabelle Bajeux-Besnainou — Richard P. Simmons Professor of Finance",
        ],
        "research_centers": [
            {"name": "Carnegie Mellon Electricity Industry Center (CEIC)", "url": "https://www.cmu.edu/ceic/"},
            {"name": "Center for Behavioral & Decision Research (CBDR)", "url": "https://www.cmu.edu/cbdr/"},
            {
                "name": "PNC Center for Financial Services Innovation",
                "url": "https://www.cmu.edu/tepper/pnc-center-for-financial-services-innovation/",
            },
            {"name": "Center for Intelligent Business", "url": "https://www.cmu.edu/intelligentbusiness/"},
        ],
        "named_for": "David A. Tepper (MBA 1982), following his 2004 gift renaming GSIA",
        "source": "https://www.cmu.edu/tepper/about/our-history",
    },
    _HEINZ: {
        "founded": 1968,
        "leadership": "Kirsten Martin, H. John Heinz III Dean of Heinz College",
        "faculty": [
            "Rema Padman — Trustees Professor of Management Science and Healthcare "
            "Informatics; Fellow of the American Medical Informatics Association",
            "Ramayya Krishnan — W. W. Cooper and Ruth F. Cooper Professor of Management "
            "Science and Information Systems; 25th President of INFORMS",
        ],
        "research_centers": [
            {"name": "Block Center for Technology and Society", "url": "https://www.cmu.edu/block-center/"},
            {"name": "Metro21: Smart Cities Institute", "url": "https://www.cmu.edu/metro21/"},
            {"name": "iLab", "url": "https://ilab.heinz.cmu.edu/"},
            {"name": "CyLab Security and Privacy Institute", "url": "https://www.cylab.cmu.edu/"},
        ],
        "named_for": "U.S. Senator H. John Heinz III",
        "source": "https://www.heinz.cmu.edu/about/history",
    },
}

# Required about_detail fields we could not cleanly verify this run (per school).
_ABOUT_OMITTED: dict[str, list[str]] = {
    _CIT: ["about_detail.faculty"],  # notable-faculty enumeration deferred to a resume run
    _MCS: ["about_detail.founded", "about_detail.faculty"],
    _CFA: ["about_detail.faculty"],
}

# ── Program catalog (breadth-first; every node carries verified basics) ─────────
# Each spec: (slug, program_name, degree_type, school, department, delivery_format,
# duration_months, website_url). delivery_format ∈ in_person | online | hybrid.
_P = "in_person"
_ON = "online"
_HY = "hybrid"

_PROGRAM_SPECS: list[tuple] = [
    # ===== School of Computer Science — undergraduate =====
    ("cmu-cs-bs", "Computer Science", "bachelors", _SCS, "Computer Science Department", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/school-of-computer-science"),
    ("cmu-ai-bs", "Artificial Intelligence", "bachelors", _SCS, "School of Computer Science", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/school-of-computer-science"),
    ("cmu-compbio-bs", "Computational Biology", "bachelors", _SCS,
     "Ray and Stephanie Lane Computational Biology Department", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/school-of-computer-science"),
    ("cmu-hci-bs", "Human-Computer Interaction", "bachelors", _SCS,
     "Human-Computer Interaction Institute", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/school-of-computer-science"),
    ("cmu-robotics-bs", "Robotics", "bachelors", _SCS, "Robotics Institute", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/school-of-computer-science"),
    # ===== School of Computer Science — graduate =====
    ("cmu-mscs", "Master of Science in Computer Science", "masters", _SCS,
     "Computer Science Department", _P, 16,
     "https://www.csd.cmu.edu/academics/masters/ms-in-computer-science"),
    ("cmu-cs-phd", "Ph.D. in Computer Science", "phd", _SCS, "Computer Science Department", _P, 60,
     "https://csd.cmu.edu/academics/doctoral/overview"),
    ("cmu-ms-ml", "Master of Science in Machine Learning", "masters", _SCS,
     "Machine Learning Department", _P, 16,
     "https://ml.cmu.edu/academics/primary-ms-machine-learning-masters"),
    ("cmu-ml-phd", "Ph.D. in Machine Learning", "phd", _SCS, "Machine Learning Department", _P, 60,
     "https://ml.cmu.edu/academics/machine-learning-phd"),
    ("cmu-mlt", "Master of Science in Language Technologies", "masters", _SCS,
     "Language Technologies Institute", _P, 24,
     "https://lti.cmu.edu/academics/masters-programs/mlt.html"),
    ("cmu-miis", "Master of Science in Intelligent Information Systems", "masters", _SCS,
     "Language Technologies Institute", _P, 16,
     "https://lti.cmu.edu/academics/masters-programs/miis.html"),
    ("cmu-mcds", "Master of Computational Data Science", "masters", _SCS,
     "Language Technologies Institute", _P, 16,
     "https://lti.cmu.edu/academics/masters-programs/mcds.html"),
    ("cmu-msaii", "Master of Science in Artificial Intelligence and Innovation", "masters", _SCS,
     "Language Technologies Institute", _P, 16,
     "https://lti.cmu.edu/academics/masters-programs/msaii.html"),
    ("cmu-lti-phd", "Ph.D. in Language and Information Technologies", "phd", _SCS,
     "Language Technologies Institute", _P, 60,
     "https://www.lti.cs.cmu.edu/academics/phd-programs/phd-lti.html"),
    ("cmu-msr", "Master of Science in Robotics", "masters", _SCS, "Robotics Institute", _P, 24,
     "https://www.ri.cmu.edu/education/academic-programs/master-of-science-robotics/"),
    ("cmu-mrsd", "Master of Science in Robotic Systems Development", "masters", _SCS,
     "Robotics Institute", _P, 21, "https://mrsd.ri.cmu.edu/"),
    ("cmu-mscv", "Master of Science in Computer Vision", "masters", _SCS, "Robotics Institute", _P,
     16, "https://www.ri.cmu.edu/education/academic-programs/masters/"),
    ("cmu-robotics-phd", "Ph.D. in Robotics", "phd", _SCS, "Robotics Institute", _P, 60,
     "https://www.ri.cmu.edu/education/academic-programs/doctoral-robotics-program/"),
    ("cmu-mhci", "Master of Human-Computer Interaction", "masters", _SCS,
     "Human-Computer Interaction Institute", _P, 12, "https://www.hcii.cmu.edu/academics/mhci"),
    ("cmu-msle", "Master of Science in Learning Engineering", "masters", _SCS,
     "Human-Computer Interaction Institute", _P, 16, "https://metals.hcii.cmu.edu/"),
    ("cmu-hci-phd", "Ph.D. in Human-Computer Interaction", "phd", _SCS,
     "Human-Computer Interaction Institute", _P, 60, "https://www.hcii.cmu.edu/academics/phd-hci"),
    ("cmu-mse", "Master of Software Engineering", "masters", _SCS,
     "Software and Societal Systems Department", _P, 16,
     "https://mse.s3d.cmu.edu/applicants/mse-as/index.html"),
    ("cmu-mse-online", "Master of Science in Software Engineering (Online)", "masters", _SCS,
     "Software and Societal Systems Department", _ON, 30,
     "https://mse.s3d.cmu.edu/applicants/mse-as-online/index.html"),
    ("cmu-msit-privacy", "Master of Science in Information Technology — Privacy Engineering",
     "masters", _SCS, "Software and Societal Systems Department", _P, 12,
     "https://privacy.cs.cmu.edu/masters/index.html"),
    ("cmu-se-phd", "Ph.D. in Software Engineering", "phd", _SCS,
     "Software and Societal Systems Department", _P, 60, "https://se-phd.s3d.cmu.edu/"),
    ("cmu-societal-computing-phd", "Ph.D. in Societal Computing", "phd", _SCS,
     "Software and Societal Systems Department", _P, 60, "https://sc.cs.cmu.edu/"),
    ("cmu-ms-compbio", "Master of Science in Computational Biology", "masters", _SCS,
     "Ray and Stephanie Lane Computational Biology Department", _P, 16,
     "https://www.cmu.edu/ms-compbio/"),
    ("cmu-compbio-phd", "Ph.D. in Computational Biology", "phd", _SCS,
     "Ray and Stephanie Lane Computational Biology Department", _P, 60,
     "https://www.compbio.cmu.edu/"),
    ("cmu-ms-automated-science", "Master of Science in Automated Science: Biological Experimentation",
     "masters", _SCS, "Ray and Stephanie Lane Computational Biology Department", _P, 16,
     "http://msas.cbd.cmu.edu/"),

    # ===== College of Engineering — undergraduate =====
    ("cmu-cheme-bs", "Chemical Engineering", "bachelors", _CIT, "Chemical Engineering", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/college-of-engineering"),
    ("cmu-civil-bs", "Civil Engineering", "bachelors", _CIT,
     "Civil & Environmental Engineering", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/college-of-engineering"),
    ("cmu-environ-bs", "Environmental Engineering", "bachelors", _CIT,
     "Civil & Environmental Engineering", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/college-of-engineering"),
    ("cmu-ece-bs", "Electrical and Computer Engineering", "bachelors", _CIT,
     "Electrical & Computer Engineering", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/college-of-engineering"),
    ("cmu-mse-bs", "Materials Science and Engineering", "bachelors", _CIT,
     "Materials Science & Engineering", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/college-of-engineering"),
    ("cmu-meche-bs", "Mechanical Engineering", "bachelors", _CIT, "Mechanical Engineering", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/college-of-engineering"),
    ("cmu-bme-bs", "Biomedical Engineering (Additional Major)", "bachelors", _CIT,
     "Biomedical Engineering", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/college-of-engineering"),
    # ===== College of Engineering — ECE graduate =====
    ("cmu-ms-ece", "Master of Science in Electrical & Computer Engineering", "masters", _CIT,
     "Electrical & Computer Engineering", _P, 16, "https://www.ece.cmu.edu/academics/ms-ece/index.html"),
    ("cmu-ms-se-sv", "Master of Science in Software Engineering (Silicon Valley)", "masters", _CIT,
     "Electrical & Computer Engineering", _P, 16, "https://www.ece.cmu.edu/academics/ms-se/index.html"),
    ("cmu-msaie-ece", "Master of Science in Artificial Intelligence Engineering — ECE", "masters",
     _CIT, "Electrical & Computer Engineering", _P, 16, "https://www.ece.cmu.edu/academics/ms-ai/index.html"),
    ("cmu-ece-phd", "Ph.D. in Electrical & Computer Engineering", "phd", _CIT,
     "Electrical & Computer Engineering", _P, 60, "https://www.ece.cmu.edu/academics/phd-ece/index.html"),
    # ===== College of Engineering — MechE graduate =====
    ("cmu-ms-meche", "Master of Science in Mechanical Engineering", "masters", _CIT,
     "Mechanical Engineering", _P, 12,
     "https://www.meche.engineering.cmu.edu/education/graduate-programs/masters/masters-meche.html"),
    ("cmu-ms-meche-research", "Master of Science in Mechanical Engineering — Research", "masters",
     _CIT, "Mechanical Engineering", _P, 24,
     "https://www.meche.engineering.cmu.edu/education/graduate-programs/masters/masters-research.html"),
    ("cmu-ms-meche-advanced", "Master of Science in Mechanical Engineering — Advanced Study",
     "masters", _CIT, "Mechanical Engineering", _P, 16,
     "https://www.meche.engineering.cmu.edu/education/graduate-programs/masters/masters-advanced-study.html"),
    ("cmu-msaie-meche", "Master of Science in Artificial Intelligence Engineering — Mechanical Engineering",
     "masters", _CIT, "Mechanical Engineering", _P, 16,
     "https://www.meche.engineering.cmu.edu/education/graduate-programs/masters/masters-artificial-intelligence-engineering.html"),
    ("cmu-meche-phd", "Ph.D. in Mechanical Engineering", "phd", _CIT, "Mechanical Engineering", _P,
     60, "https://www.meche.engineering.cmu.edu/education/graduate-programs/phd/index.html"),
    # ===== College of Engineering — CEE graduate =====
    ("cmu-ms-cee", "Master of Science in Civil & Environmental Engineering", "masters", _CIT,
     "Civil & Environmental Engineering", _P, 16,
     "https://cee.engineering.cmu.edu/education/graduate/ms-programs/ms-cee.html"),
    ("cmu-ms-cee-research", "Master of Science in Civil & Environmental Engineering — Research",
     "masters", _CIT, "Civil & Environmental Engineering", _P, 24,
     "https://cee.engineering.cmu.edu/education/graduate/ms-programs/ms-cee-research.html"),
    ("cmu-msaie-civil", "Master of Science in AI Engineering — Civil Engineering", "masters", _CIT,
     "Civil & Environmental Engineering", _P, 16,
     "https://cee.engineering.cmu.edu/education/graduate/ms-programs/ai-engineering.html"),
    ("cmu-ms-cce", "Master of Science in Civil & Computer Engineering", "masters", _CIT,
     "Civil & Environmental Engineering", _P, 16,
     "https://cee.engineering.cmu.edu/education/graduate/ms-programs/ms-cce.html"),
    ("cmu-cee-phd", "Ph.D. in Civil & Environmental Engineering", "phd", _CIT,
     "Civil & Environmental Engineering", _P, 60,
     "https://cee.engineering.cmu.edu/education/graduate/phd-programs/index.html"),
    # ===== College of Engineering — ChemE graduate =====
    ("cmu-ms-cheme", "Master of Science in Chemical Engineering — Applied Study", "masters", _CIT,
     "Chemical Engineering", _P, 24,
     "https://www.cheme.engineering.cmu.edu/education/graduate-programs/masters/ms-and-mche.html"),
    ("cmu-mche", "Master of Chemical Engineering", "masters", _CIT, "Chemical Engineering", _P, 12,
     "https://www.cheme.engineering.cmu.edu/education/graduate-programs/masters/ms-and-mche.html"),
    ("cmu-ms-cse", "Master of Science in Computational Systems Engineering", "masters", _CIT,
     "Chemical Engineering", _P, 16,
     "https://www.cheme.engineering.cmu.edu/education/graduate-programs/masters/ms-cse.html"),
    ("cmu-msaie-cheme", "Master of Science in AI Engineering — Chemical Engineering", "masters",
     _CIT, "Chemical Engineering", _P, 16,
     "https://www.cheme.engineering.cmu.edu/education/graduate-programs/masters/aie-che.html"),
    ("cmu-ms-btpe", "Master of Science in Biotechnology & Pharmaceutical Engineering", "masters",
     _CIT, "Chemical Engineering", _P, 16,
     "https://www.cheme.engineering.cmu.edu/education/graduate-programs/masters/ms-btpe.html"),
    ("cmu-cheme-phd", "Ph.D. in Chemical Engineering", "phd", _CIT, "Chemical Engineering", _P, 60,
     "https://www.cheme.engineering.cmu.edu/education/graduate-programs/phd/index.html"),
    # ===== College of Engineering — MSE graduate =====
    ("cmu-ms-matsci", "Master of Science in Materials Science & Engineering", "masters", _CIT,
     "Materials Science & Engineering", _P, 12,
     "https://mse.engineering.cmu.edu/education/graduate/masters-programs/materials-engineering.html"),
    ("cmu-ms-matsci-research", "Master of Science in Materials Science (Research)", "masters", _CIT,
     "Materials Science & Engineering", _P, 24,
     "https://mse.engineering.cmu.edu/education/graduate/masters-programs/ms-materials.html"),
    ("cmu-ms-cmse", "Master of Science in Computational Materials Science & Engineering", "masters",
     _CIT, "Materials Science & Engineering", _P, 16,
     "https://mse.engineering.cmu.edu/education/graduate/masters-programs/ms-computational-materials-science-engineering.html"),
    ("cmu-matsci-phd", "Ph.D. in Materials Science & Engineering", "phd", _CIT,
     "Materials Science & Engineering", _P, 60,
     "https://mse.engineering.cmu.edu/education/graduate/doctoral-program/index.html"),
    # ===== College of Engineering — BME graduate =====
    ("cmu-ms-bme", "Master of Science in Biomedical Engineering — Research", "masters", _CIT,
     "Biomedical Engineering", _P, 21,
     "https://www.cmu.edu/bme/Academics/graduate-programs/ms_program.html"),
    ("cmu-ms-bme-applied", "Master of Science in Biomedical Engineering — Applied Study", "masters",
     _CIT, "Biomedical Engineering", _P, 16,
     "https://www.cmu.edu/bme/Academics/graduate-programs/ms_program.html"),
    ("cmu-bme-phd", "Ph.D. in Biomedical Engineering", "phd", _CIT, "Biomedical Engineering", _P,
     60, "https://www.cmu.edu/bme/Academics/graduate-programs/phd_program.html"),
    # ===== College of Engineering — EPP graduate =====
    ("cmu-ms-epp", "Master of Science in Engineering & Public Policy", "masters", _CIT,
     "Engineering & Public Policy", _P, 16,
     "https://epp.engineering.cmu.edu/education/graduate/masters-programs/ms-in-epp/index.html"),
    ("cmu-epp-phd", "Ph.D. in Engineering & Public Policy", "phd", _CIT,
     "Engineering & Public Policy", _P, 60,
     "https://epp.engineering.cmu.edu/education/graduate/phd-program/index.html"),
    # ===== College of Engineering — INI =====
    ("cmu-msin", "Master of Science in Information Networking", "masters", _CIT,
     "Information Networking Institute", _P, 16, "https://www.cmu.edu/ini/academics/msin/index.html"),
    ("cmu-msis", "Master of Science in Information Security", "masters", _CIT,
     "Information Networking Institute", _P, 16, "https://www.cmu.edu/ini/academics/msis/index.html"),
    ("cmu-msaie-is", "Master of Science in AI Engineering — Information Security", "masters", _CIT,
     "Information Networking Institute", _P, 16, "https://www.cmu.edu/ini/academics/msaie-is/index.html"),
    ("cmu-msit-is", "Master of Science in Information Technology — Information Security (Bicoastal)",
     "masters", _CIT, "Information Networking Institute", _HY, 16,
     "https://www.cmu.edu/ini/academics/bicoastal/index.html"),
    ("cmu-msmite", "Master of Science in Mobile & IoT Engineering (Bicoastal)", "masters", _CIT,
     "Information Networking Institute", _HY, 16,
     "https://www.cmu.edu/ini/academics/bicoastal/index.html"),
    # ===== College of Engineering — Integrated Innovation Institute =====
    ("cmu-miips", "Master of Integrated Innovation for Products & Services", "masters", _CIT,
     "Integrated Innovation Institute", _P, 16, "https://www.cmu.edu/iii/graduate-programs/miips/index.html"),
    ("cmu-miips-online", "Master of Integrated Innovation for Products & Services (Online)",
     "masters", _CIT, "Integrated Innovation Institute", _ON, 24,
     "https://www.cmu.edu/iii/online-programs/degree.html"),
    ("cmu-mssm", "Master of Science in Software Management", "masters", _CIT,
     "Integrated Innovation Institute", _HY, 16, "https://www.cmu.edu/iii/graduate-programs/mssm/index.html"),
    # ===== College of Engineering — Engineering & Technology Innovation Management =====
    ("cmu-ms-etim", "Master of Science in Engineering & Technology Innovation Management", "masters",
     _CIT, "Engineering & Technology Innovation Management", _P, 12,
     "https://engineering.cmu.edu/etim/programs/ms-etim.html"),
    # ===== College of Engineering — CMU-Africa (Kigali, Rwanda) =====
    ("cmu-africa-msece", "Master of Science in Electrical & Computer Engineering (Kigali)", "masters",
     _CIT, "CMU-Africa", _P, 16, "https://www.africa.engineering.cmu.edu/programs/msece/index.html"),
    ("cmu-africa-msit", "Master of Science in Information Technology (Kigali)", "masters", _CIT,
     "CMU-Africa", _P, 20, "https://www.africa.engineering.cmu.edu/programs/msit.html"),
    ("cmu-africa-mseai", "Master of Science in Engineering Artificial Intelligence (Kigali)",
     "masters", _CIT, "CMU-Africa", _P, 20, "https://www.africa.engineering.cmu.edu/programs/mseai.html"),

    # ===== Mellon College of Science — undergraduate =====
    ("cmu-biosci-bs", "Biological Sciences", "bachelors", _MCS, "Biological Sciences", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/mellon-college-of-science"),
    ("cmu-neuro-bs", "Neuroscience", "bachelors", _MCS, "Biological Sciences", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/mellon-college-of-science"),
    ("cmu-chem-bs", "Chemistry", "bachelors", _MCS, "Chemistry", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/mellon-college-of-science"),
    ("cmu-math-bs", "Mathematical Sciences", "bachelors", _MCS, "Mathematical Sciences", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/mellon-college-of-science"),
    ("cmu-compfin-bs", "Computational Finance", "bachelors", _MCS, "Mathematical Sciences", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/mellon-college-of-science"),
    ("cmu-physics-bs", "Physics", "bachelors", _MCS, "Physics", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/mellon-college-of-science"),
    # ===== Mellon College of Science — graduate =====
    ("cmu-ms-qbb", "Master of Science in Quantitative Biology and Bioinformatics", "masters", _MCS,
     "Biological Sciences", _P, 16, "https://www.cmu.edu/bio/graduate/ms-qbb/index.html"),
    ("cmu-biosci-phd", "Ph.D. in Biological Sciences", "phd", _MCS, "Biological Sciences", _P, 60,
     "https://www.cmu.edu/bio/graduate/phd_bs/index.html"),
    ("cmu-chem-phd", "Ph.D. in Chemistry", "phd", _MCS, "Chemistry", _P, 60,
     "https://www.cmu.edu/chemistry/grad/"),
    ("cmu-physics-phd", "Ph.D. in Physics", "phd", _MCS, "Physics", _P, 60,
     "https://www.cmu.edu/physics/graduate-program/index.html"),
    ("cmu-astro-phd", "Ph.D. in Astronomy and Astrophysics", "phd", _MCS, "Physics", _P, 60,
     "https://www.cmu.edu/mcs/academics/grad/programs/phd-astronomy-and-astrophysics"),
    ("cmu-ms-modern-physics", "Master of Science in Modern Physics", "masters", _MCS, "Physics", _P,
     16, "https://www.cmu.edu/physics/graduate-program/master/ms-modern-physics.html"),
    ("cmu-math-phd", "Ph.D. in Mathematical Sciences", "phd", _MCS, "Mathematical Sciences", _P, 60,
     "https://www.cmu.edu/math/grad/phd/index.html"),
    ("cmu-da-math", "Doctor of Arts in Mathematical Sciences", "phd", _MCS, "Mathematical Sciences",
     _P, 60, "https://www.cmu.edu/math/grad/phd/index.html"),
    ("cmu-aco-phd", "Ph.D. in Algorithms, Combinatorics and Optimization", "phd", _MCS,
     "Mathematical Sciences", _P, 60, "https://www.cmu.edu/math/grad/phd/index.html"),
    ("cmu-ms-das", "Master of Science in Data Analytics for Science", "masters", _MCS,
     "Mellon College of Science", _P, 12, "https://www.cmu.edu/mcs/academics/grad/ms-data-analytics"),

    # ===== Dietrich College — undergraduate =====
    ("cmu-econ-bs", "Economics", "bachelors", _DIETRICH, "Undergraduate Economics Program", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/dietrich-college-of-humanities-social-sciences"),
    ("cmu-creative-writing-ba", "Creative Writing", "bachelors", _DIETRICH, "English", _P, 48,
     "https://www.cmu.edu/dietrich/english/"),
    ("cmu-professional-writing-ba", "Professional Writing", "bachelors", _DIETRICH, "English", _P,
     48, "https://www.cmu.edu/dietrich/english/"),
    ("cmu-history-ba", "History (Social and Political History)", "bachelors", _DIETRICH, "History",
     _P, 48, "https://www.cmu.edu/dietrich/history/"),
    ("cmu-global-studies-ba", "Global Studies", "bachelors", _DIETRICH, "History", _P, 48,
     "https://www.cmu.edu/dietrich/history/"),
    ("cmu-ir-bs", "International Relations and Politics", "bachelors", _DIETRICH,
     "Institute for Strategy & Technology (CMIST)", _P, 48, "https://www.cmu.edu/cmist/"),
    ("cmu-linguistics-ba", "Linguistics", "bachelors", _DIETRICH,
     "Languages, Cultures & Applied Linguistics", _P, 48, "https://www.cmu.edu/dietrich/lcal/"),
    ("cmu-philosophy-ba", "Philosophy", "bachelors", _DIETRICH, "Philosophy", _P, 48,
     "https://www.cmu.edu/dietrich/philosophy/"),
    ("cmu-logic-computation-bs", "Logic and Computation", "bachelors", _DIETRICH, "Philosophy", _P,
     48, "https://www.cmu.edu/dietrich/philosophy/"),
    ("cmu-psychology-bs", "Psychology", "bachelors", _DIETRICH, "Psychology", _P, 48,
     "https://www.cmu.edu/dietrich/psychology/"),
    ("cmu-cognitive-science-bs", "Cognitive Science", "bachelors", _DIETRICH, "Psychology", _P, 48,
     "https://www.cmu.edu/dietrich/psychology/"),
    ("cmu-decision-science-bs", "Decision Science", "bachelors", _DIETRICH,
     "Social and Decision Sciences", _P, 48, "https://www.cmu.edu/dietrich/sds/"),
    ("cmu-statistics-bs", "Statistics", "bachelors", _DIETRICH, "Statistics & Data Science", _P, 48,
     "https://www.cmu.edu/dietrich/statistics-datascience/"),
    ("cmu-stats-ml-bs", "Statistics and Machine Learning", "bachelors", _DIETRICH,
     "Statistics & Data Science", _P, 48, "https://www.cmu.edu/dietrich/statistics-datascience/"),
    ("cmu-information-systems-bs", "Information Systems", "bachelors", _DIETRICH,
     "Information Systems Program", _P, 48, "https://www.cmu.edu/information-systems/"),
    # ===== Dietrich College — graduate =====
    ("cmu-mads", "Master of Science in Applied Data Science", "masters", _DIETRICH,
     "Statistics & Data Science", _P, 9,
     "https://www.cmu.edu/dietrich/statistics-datascience/academics/mads/index.html"),
    ("cmu-ms-statistics", "Master of Science in Statistics", "masters", _DIETRICH,
     "Statistics & Data Science", _P, 16,
     "https://www.cmu.edu/dietrich/statistics-datascience/academics/phd/ms-statistics.html"),
    ("cmu-statistics-phd", "Ph.D. in Statistics", "phd", _DIETRICH, "Statistics & Data Science", _P,
     60, "https://www.cmu.edu/dietrich/statistics-datascience/academics/phd/index.html"),
    ("cmu-stats-ml-phd", "Joint Ph.D. in Statistics and Machine Learning", "phd", _DIETRICH,
     "Statistics & Data Science", _P, 60,
     "https://www.cmu.edu/dietrich/statistics-datascience/academics/phd/statistics-machine-learning/index.html"),
    ("cmu-cert-fds-online", "Online Graduate Certificate in Foundations of Data Science",
     "certificate", _DIETRICH, "Statistics & Data Science", _ON, 12,
     "https://www.cmu.edu/online/fds/index.html"),
    ("cmu-psychology-phd", "Ph.D. in Psychology", "phd", _DIETRICH, "Psychology", _P, 60,
     "https://www.cmu.edu/dietrich/psychology/graduate/psychology-phd/index.html"),
    ("cmu-cogneuro-phd", "Ph.D. in Cognitive Neuroscience", "phd", _DIETRICH, "Psychology", _P, 60,
     "https://www.cmu.edu/dietrich/psychology/graduate/cog-neuro/index.html"),
    ("cmu-ma-gcat", "Master of Arts in Global Communication & Applied Translation", "masters",
     _DIETRICH, "English", _P, 16,
     "https://www.cmu.edu/dietrich/english/academic-programs/ma-gcat/index.html"),
    ("cmu-ma-lcs", "Master of Arts in Literary & Cultural Studies", "masters", _DIETRICH, "English",
     _P, 16, "https://www.cmu.edu/dietrich/english/academic-programs/ma-lcs/index.html"),
    ("cmu-mapw", "Master of Arts in Professional Writing", "masters", _DIETRICH, "English", _P, 16,
     "https://www.cmu.edu/dietrich/english/academic-programs/ma-pw/index.html"),
    ("cmu-phd-rhetoric", "Ph.D. in Rhetoric", "phd", _DIETRICH, "English", _P, 60,
     "https://www.cmu.edu/dietrich/english/academic-programs/phd-rhetoric/index.html"),
    ("cmu-phd-lcs", "Ph.D. in Literary & Cultural Studies", "phd", _DIETRICH, "English", _P, 60,
     "https://www.cmu.edu/dietrich/english/academic-programs/phd-lcs/index.html"),
    ("cmu-history-phd", "Ph.D. in History", "phd", _DIETRICH, "History", _P, 60,
     "https://www.cmu.edu/dietrich/history/graduate/index.html"),
    ("cmu-philosophy-phd", "Ph.D. in Philosophy", "phd", _DIETRICH, "Philosophy", _P, 60,
     "https://www.cmu.edu/dietrich/philosophy/graduate/phd/index.html"),
    ("cmu-ms-lcm", "Master of Science in Logic, Computation, and Methodology", "masters", _DIETRICH,
     "Philosophy", _P, 16, "https://www.cmu.edu/dietrich/philosophy/graduate/masters/index.html"),
    ("cmu-bdr-phd", "Ph.D. in Behavioral Decision Research", "phd", _DIETRICH,
     "Social and Decision Sciences", _P, 60, "https://www.cmu.edu/dietrich/sds/graduate/index.html"),
    ("cmu-ma-alsla", "Master of Arts in Applied Linguistics & Second Language Acquisition",
     "masters", _DIETRICH, "Languages, Cultures & Applied Linguistics", _P, 12,
     "https://www.cmu.edu/dietrich/lcal/academics/graduate/ma-alsla/index.html"),
    ("cmu-mits", "Master of Information Technology Strategy", "masters", _DIETRICH,
     "Institute for Strategy & Technology (CMIST)", _P, 16,
     "https://www.cmu.edu/cmist/academics/graduate-programs/mits/index.html"),
    ("cmu-msstair", "Master of Science in Security, Technology, and International Relations",
     "masters", _DIETRICH, "Institute for Strategy & Technology (CMIST)", _P, 16,
     "https://www.cmu.edu/cmist/academics/graduate-programs/msstair/index.html"),

    # ===== College of Fine Arts — undergraduate =====
    ("cmu-barch", "Architecture", "bachelors", _CFA, "School of Architecture", _P, 60,
     "https://www.cmu.edu/admission/majors-programs/college-of-fine-arts"),
    ("cmu-art-bfa", "Art", "bachelors", _CFA, "School of Art", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/college-of-fine-arts"),
    ("cmu-design-bdes", "Design", "bachelors", _CFA, "School of Design", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/college-of-fine-arts"),
    ("cmu-drama-bfa", "Drama", "bachelors", _CFA, "School of Drama", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/college-of-fine-arts"),
    ("cmu-music-bfa", "Music", "bachelors", _CFA, "School of Music", _P, 48,
     "https://www.cmu.edu/admission/majors-programs/college-of-fine-arts"),
    ("cmu-music-technology-bs", "Music and Technology", "bachelors", _CFA, "School of Music", _P,
     48, "https://www.cmu.edu/admission/majors-programs/college-of-fine-arts"),
    # ===== College of Fine Arts — graduate =====
    ("cmu-march", "Master of Architecture", "masters", _CFA, "School of Architecture", _P, 36,
     "https://www.architecture.cmu.edu/graduate-programs"),
    ("cmu-maad", "Master of Advanced Architectural Design", "masters", _CFA,
     "School of Architecture", _P, 12, "https://www.architecture.cmu.edu/graduate-programs"),
    ("cmu-ms-msrsd", "Master of Science in Regenerative and Sustainable Design", "masters", _CFA,
     "School of Architecture", _P, 12, "https://www.architecture.cmu.edu/graduate-programs"),
    ("cmu-mud", "Master of Urban Design", "masters", _CFA, "School of Architecture", _P, 12,
     "https://www.architecture.cmu.edu/graduate-programs"),
    ("cmu-arch-phd", "Ph.D. in Architecture", "phd", _CFA, "School of Architecture", _P, 60,
     "https://www.architecture.cmu.edu/graduate-programs"),
    ("cmu-art-mfa", "Master of Fine Arts in Art", "masters", _CFA, "School of Art", _P, 36,
     "https://art.cmu.edu/mfa/"),
    ("cmu-mdes", "Master of Design in Design for Interactions", "masters", _CFA, "School of Design",
     _P, 24, "https://design.cmu.edu/about-our-programs/masters-degrees/master-design-design-interactions"),
    ("cmu-ma-design", "Master of Arts in Design", "masters", _CFA, "School of Design", _P, 12,
     "https://design.cmu.edu/about-our-programs/masters-degrees/master-arts-design"),
    ("cmu-design-phd", "Ph.D. in Transition Design", "phd", _CFA, "School of Design", _P, 60,
     "https://design.cmu.edu/about-our-programs/phd-transition-design"),
    ("cmu-drama-mfa-directing", "Master of Fine Arts in Directing", "masters", _CFA,
     "School of Drama", _P, 36, "https://drama.cmu.edu/programs/graduate-programs/"),
    ("cmu-drama-mfa-writing", "Master of Fine Arts in Dramatic Writing", "masters", _CFA,
     "School of Drama", _P, 36, "https://drama.cmu.edu/programs/graduate-programs/"),
    ("cmu-drama-mfa-design", "Master of Fine Arts in Design (Drama)", "masters", _CFA,
     "School of Drama", _P, 36, "https://drama.cmu.edu/programs/graduate-programs/"),
    ("cmu-mm", "Master of Music", "masters", _CFA, "School of Music", _P, 24,
     "https://www.cmu.edu/cfa/music/programs/graduate-programs/index.html"),
    ("cmu-ms-music-tech", "Master of Science in Music & Technology", "masters", _CFA,
     "School of Music", _P, 21,
     "https://www.cmu.edu/cfa/music/programs/graduate-programs/grad-music-technology.html"),
    ("cmu-mm-music-ed", "Master of Music in Music Education", "masters", _CFA, "School of Music",
     _P, 24, "https://www.cmu.edu/cfa/music/programs/graduate-programs/grad-music-education.html"),
    ("cmu-mscd", "Master of Science in Computational Design", "masters", _CFA,
     "School of Architecture", _P, 16, "https://www.architecture.cmu.edu/graduate-programs"),
    ("cmu-msbpd", "Master of Science in Building Performance & Diagnostics", "masters", _CFA,
     "School of Architecture", _P, 16, "https://www.architecture.cmu.edu/graduate-programs"),
    ("cmu-msaecm", "Master of Science in Architecture-Engineering-Construction Management",
     "masters", _CFA, "School of Architecture", _P, 16,
     "https://www.architecture.cmu.edu/graduate-programs"),
    ("cmu-ddes", "Doctor of Design", "phd", _CFA, "School of Architecture", _P, 36,
     "https://www.architecture.cmu.edu/graduate-programs"),

    # ===== Dietrich College — Neuroscience Institute + additional graduate =====
    ("cmu-mint", "Master of Science in Neural Technologies", "masters", _DIETRICH,
     "Neuroscience Institute", _P, 16,
     "https://www.cmu.edu/ni/academics/grad/programs/ms-neural-technologies"),
    ("cmu-pnc-phd", "Ph.D. in Neural Computation", "phd", _DIETRICH, "Neuroscience Institute", _P,
     60, "https://www.cmu.edu/ni/academics/pnc/pnc-machine-learning.html"),
    ("cmu-psn-phd", "Ph.D. in Systems Neuroscience", "phd", _DIETRICH, "Neuroscience Institute", _P,
     60, "https://www.cmu.edu/ni/academics/psn/index.html"),
    ("cmu-comp-cultural-phd", "Ph.D. in Computational Cultural Studies", "phd", _DIETRICH, "English",
     _P, 60,
     "https://www.cmu.edu/dietrich/english/academic-programs/computational-cultural-studies/index.html"),
    ("cmu-alsla-phd", "Ph.D. in Applied Linguistics & Second Language Acquisition", "phd",
     _DIETRICH, "Languages, Cultures & Applied Linguistics", _P, 60,
     "https://www.cmu.edu/dietrich/lcal/academics/graduate/phd-alsla/index.html"),

    # ===== Tepper School of Business =====
    ("cmu-mba", "Full-Time MBA", "masters", _TEPPER, "Tepper MBA Program", _P, 21,
     "https://www.cmu.edu/tepper/programs/mba/full-time"),
    ("cmu-mba-online", "Online Hybrid MBA", "masters", _TEPPER, "Tepper MBA Program", _HY, 32,
     "https://www.cmu.edu/tepper/programs/mba/online-hybrid"),
    ("cmu-msba", "Master of Science in Business Analytics", "masters", _TEPPER,
     "Tepper School of Business", _P, 9,
     "https://www.cmu.edu/tepper/programs/master-business-analytics"),
    ("cmu-msba-online", "Master of Science in Business Analytics (Online)", "masters", _TEPPER,
     "Tepper School of Business", _ON, 20,
     "https://www.cmu.edu/tepper/programs/master-business-analytics"),
    ("cmu-msm", "Master of Science in Management", "masters", _TEPPER, "Tepper School of Business",
     _P, 9, "https://www.cmu.edu/tepper/programs/master-science-management"),
    ("cmu-mspm", "Master of Science in Product Management", "masters", _TEPPER,
     "Tepper School of Business (joint with the School of Computer Science)", _P, 12,
     "https://www.cmu.edu/tepper/programs/master-product-management"),
    ("cmu-mscf", "Master of Science in Computational Finance", "masters", _TEPPER,
     "Tepper School of Business (Pittsburgh + New York City)", _P, 16, "https://www.cmu.edu/mscf/"),
    ("cmu-tepper-phd", "Ph.D. in Business Administration", "phd", _TEPPER,
     "Tepper School of Business", _P, 60, "https://www.cmu.edu/tepper/programs/phd"),

    # ===== Heinz College — School of Information Systems & Management =====
    ("cmu-mism", "Master of Information Systems Management", "masters", _HEINZ,
     "School of Information Systems & Management", _P, 16,
     "https://www.heinz.cmu.edu/programs/information-systems-management-master/16-month"),
    ("cmu-mism-bida", "Master of Information Systems Management — Business Intelligence & Data Analytics",
     "masters", _HEINZ, "School of Information Systems & Management", _P, 16,
     "https://www.heinz.cmu.edu/programs/information-systems-management-master/bida"),
    ("cmu-msit-online", "Master of Science in Information Technology (Online)", "masters", _HEINZ,
     "School of Information Systems & Management", _ON, 24,
     "https://www.heinz.cmu.edu/programs/information-technology-master/it-management"),
    ("cmu-msispm", "Master of Science in Information Security Policy & Management", "masters",
     _HEINZ, "School of Information Systems & Management", _P, 16,
     "https://www.heinz.cmu.edu/programs/information-security-policy-management-master/index"),
    ("cmu-aim", "Master of Science in Artificial Intelligence Systems Management", "masters",
     _HEINZ, "School of Information Systems & Management", _P, 16,
     "https://www.heinz.cmu.edu/programs/artificial-intelligence-masters/index"),
    ("cmu-heinz-ism-phd", "Ph.D. in Information Systems & Management", "phd", _HEINZ,
     "School of Information Systems & Management", _P, 60,
     "https://www.heinz.cmu.edu/programs/phd-programs/information-systems-management"),
    # ===== Heinz College — School of Public Policy & Management =====
    ("cmu-msppm", "Master of Science in Public Policy & Management", "masters", _HEINZ,
     "School of Public Policy & Management", _P, 21,
     "https://www.heinz.cmu.edu/programs/public-policy-management-master/index"),
    ("cmu-msppm-da", "Master of Science in Public Policy & Management — Data Analytics", "masters",
     _HEINZ, "School of Public Policy & Management", _P, 21,
     "https://www.heinz.cmu.edu/programs/public-policy-management-master/data-analytics"),
    ("cmu-msppm-dc", "Master of Science in Public Policy & Management — Washington, D.C.", "masters",
     _HEINZ, "School of Public Policy & Management", _P, 16,
     "https://www.heinz.cmu.edu/programs/public-policy-management-master/washington-dc"),
    ("cmu-mshca", "Master of Science in Health Care Analytics", "masters", _HEINZ,
     "School of Public Policy & Management", _P, 16,
     "https://www.heinz.cmu.edu/programs/health-care-analytics-master/index"),
    ("cmu-mmm", "Master of Medical Management", "masters", _HEINZ,
     "School of Public Policy & Management", _P, 13,
     "https://www.heinz.cmu.edu/programs/medical-management-master/index"),
    ("cmu-mpm", "Master of Public Management", "masters", _HEINZ,
     "School of Public Policy & Management", _P, 24,
     "https://www.heinz.cmu.edu/programs/public-management-master/index"),
    ("cmu-heinz-ppm-phd", "Ph.D. in Public Policy & Management", "phd", _HEINZ,
     "School of Public Policy & Management", _P, 60,
     "https://www.heinz.cmu.edu/programs/phd-programs/public-policy-management"),
    # ===== Heinz College — Arts & Entertainment Management (joint with CFA) =====
    ("cmu-mam", "Master of Arts Management", "masters", _HEINZ, "Arts & Entertainment Management",
     _P, 24, "https://www.heinz.cmu.edu/programs/arts-management-master/index"),
    ("cmu-meim", "Master of Entertainment Industry Management", "masters", _HEINZ,
     "Arts & Entertainment Management (Pittsburgh + Los Angeles)", _P, 24,
     "https://www.heinz.cmu.edu/programs/entertainment-industry-management-master/index"),
]


# ── Per-degree-type baselines (curated; applied uniformly for breadth-first) ────
_DEGREE_LABEL = {
    "bachelors": "undergraduate bachelor's degree",
    "masters": "master's degree",
    "phd": "doctoral (Ph.D.) program",
    "certificate": "graduate certificate",
    "professional": "professional degree",
}

_REQ_UNDERGRAD = {
    "materials": [
        "Common Application or Coalition Application",
        "Secondary school transcript",
        "Two academic recommendations (counselor + teacher)",
        "CMU writing supplement",
    ],
    "deadlines": "Early Decision Nov 1; Regular Decision Jan 3",
    "recommendations": 2,
    "application_fee": 75,
    "source": "https://www.cmu.edu/admission/apply",
}
_REQ_GRAD = {
    "materials": [
        "Online graduate application",
        "Transcripts from all institutions attended",
        "Statement of purpose",
        "Letters of recommendation",
        "GRE where required by the program",
    ],
    "deadlines": "Varies by program; most fall-entry deadlines are December–January",
    "recommendations": 3,
    "source": "https://www.cmu.edu/graduate/admissions/index.html",
}
_REQ_ONLINE = {
    "materials": [
        "Online application",
        "Transcripts",
        "Statement of purpose",
        "Letters of recommendation",
    ],
    "deadlines": "Rolling / multiple start terms — see the program page",
    "source": "https://www.cmu.edu/graduate/admissions/index.html",
}

# Institution-wide outcomes proxy used for degree programs (clearly labelled). CMU
# does not publish program-level employment rate / top industries / methodology in
# a citable static form, so those required outcome fields are honestly omitted.
_OUTCOMES_INSTITUTION = {
    "median_salary": 114862,
    "scope": "institution",
    "source": "U.S. Dept. of Education College Scorecard (median earnings 10 years after entry)",
    "source_url": "https://collegescorecard.ed.gov/school/?211440-Carnegie-Mellon-University",
}

# Per-school cost-source citation.
_COST_SRC = (
    "Carnegie Mellon University — Tuition & Fees",
    "https://www.cmu.edu/sfs/tuition/index.html",
)
_TUITION_UNDERGRAD = 67020  # CMU SFS 2025-26 undergraduate tuition

_FLAGSHIP = "cmu-mba"

_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission.",
}

# Tepper Full-Time MBA admission (official application materials and rounds).
_REQ_MBA = {
    "materials": [
        {"name": "Tepper School online MBA application", "required": True},
        {"name": "Essays (per the current Tepper prompts)", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "One letter of recommendation", "required": True},
        {"name": "Resume", "required": True},
        {
            "name": "GMAT, GRE, or Executive Assessment scores",
            "required": True,
            "note": (
                "Tepper accepts the GMAT (10th or Focus Edition), GRE, or Executive "
                "Assessment; a test score is required for the Full-Time MBA."
            ),
        },
        {"name": "Interview (by invitation only)", "required": False},
        {"name": "$200 application fee (fee waivers available)", "required": True},
    ],
    "deadlines": [
        {"round": "Round 1", "date": "September 30, 2025"},
        {"round": "Round 2", "date": "January 8, 2026"},
        {"round": "Round 3", "date": "March 3, 2026"},
        {"round": "Round 4", "date": "May 5, 2026"},
    ],
    "recommendations": {
        "required": 1,
        "note": "One letter of recommendation submitted through the Tepper application.",
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
    "source": "Tepper School of Business — Full-Time MBA Admissions",
    "source_url": "https://www.cmu.edu/tepper/programs/mba/full-time/",
}

# Verified per-program tuition overrides (annual or per-semester as noted).
_COST_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "tuition_usd": 84186,
        "funded": False,
        "note": (
            "2026-27 academic year: $42,093 per semester (four semesters over the "
            "two-year Full-Time MBA)."
        ),
        "source": "CMU Student Financial Services — Tepper Full-Time MBA",
        "source_url": "https://www.cmu.edu/sfs/tuition/graduate/index.html",
        "year": "2026-27",
    },
}

# Tepper MBA employment-report outcomes (Class of 2025 Full-Time MBA).
_MBA_OUTCOMES: dict = {
    "median_salary": 160000,
    "scope": "program",
    "earnings_timeframe": "median base salary at graduation",
    "conditions": (
        "Tepper School Full-Time MBA Class of 2025: median base salary $160,000 and "
        "average signing bonus $38,610 (Masters Career Center 2025 MBA Summary "
        "Employment Report). Approximately 83% of the class reported receiving a job "
        "offer within three months of graduation; nearly 90% by six months."
    ),
    "source": "Tepper School — 2025 MBA Summary Employment Report",
    "source_url": (
        "https://www.cmu.edu/tepper/news/stories/2025-mba-summary-employment-report"
    ),
}

# MBA curriculum tracks (official Full-Time MBA page).
_TRACKS_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "tracks": [
            "Business Analytics",
            "Energy and Sustainability Business",
            "Entrepreneurship",
            "Management of Innovation and Product Development",
            "Technology Strategy and Product Management",
        ],
        "source": "Tepper School — Full-Time MBA Curriculum",
        "source_url": "https://www.cmu.edu/tepper/programs/mba/full-time/",
    },
}

_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "cohort_size": "144 students in the entering Full-Time MBA class (Class of 2027)",
        "international_pct": 0.38,
        "note": (
            "Entering Full-Time MBA Class of 2027: 144 students, 38% international "
            "citizens, median GMAT 710 (10th Edition), median 5 years of work "
            "experience."
        ),
        "source": "Tepper School — Full-Time MBA Class Profile",
        "source_url": "https://www.cmu.edu/tepper/programs/mba/admissions/ft-class-profile",
    },
}

_FACULTY_BY_SLUG: dict[str, dict] = {}

# Program-specific keyword filters for Events & Updates (the MBAn pattern).
_PROGRAM_KEYWORDS: dict[str, list[str]] = {
    _FLAGSHIP: ["Tepper", "MBA", "business school", "management"],
    "cmu-cs-bs": ["computer science", "School of Computer Science", "SCS"],
    "cmu-mscs": ["computer science", "SCS", "graduate"],
    "cmu-ms-ml": ["machine learning", "School of Computer Science"],
    "cmu-mhci": ["human-computer interaction", "HCII", "MHCI"],
    "cmu-msba": ["business analytics", "Tepper", "MSBA"],
    "cmu-mscf": ["computational finance", "MSCF", "quantitative finance"],
    "cmu-mism": ["information systems", "Heinz", "MISM"],
}

_MBA_CONTENT = {
    "news_rss": _CMU_NEWS_RSS,
    "news_curated": False,
    "events_feed": dict(_CMU_EVENTS_ICS),
    "keywords": list(_PROGRAM_KEYWORDS[_FLAGSHIP]),
    "social": dict(_SOCIAL_CMU),
}

# Aggregated, cited student-review themes (≥2 third-party sources per coverable program).
_REVIEWS_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "summary": (
            "Students and third-party guides consistently describe the Tepper MBA as a "
            "STEM-designated, analytics-forward program that pairs quantitative rigor "
            "with leadership coaching and a tight-knit Pittsburgh cohort; common "
            "cautions are a smaller brand footprint than M7 peers, a demanding "
            "mini-semester pace, and placement volatility in contracting MBA markets."
        ),
        "themes": [
            {
                "label": "Analytics & STEM curriculum",
                "sentiment": "positive",
                "detail": (
                    "A data-driven core (optimization, predictive modeling) plus "
                    "optional tracks in analytics, entrepreneurship, and product."
                ),
            },
            {
                "label": "Tight cohort culture",
                "sentiment": "positive",
                "detail": (
                    "A deliberately small full-time class (~144) fosters close "
                    "collaboration and community."
                ),
            },
            {
                "label": "Career outcomes",
                "sentiment": "positive",
                "detail": (
                    "Class of 2025 reported a $160,000 median base salary; consulting "
                    "and technology are top destinations."
                ),
            },
            {
                "label": "Brand vs. M7 peers",
                "sentiment": "caution",
                "detail": (
                    "Strong regionally and in analytics-heavy roles, but less global "
                    "name recognition than the largest MBA brands."
                ),
            },
            {
                "label": "Intense pace",
                "sentiment": "caution",
                "detail": (
                    "Mini-semesters and a quant-heavy core create a fast, demanding "
                    "schedule."
                ),
            },
        ],
        "sources": [
            {
                "label": "Poets&Quants — Tepper School profile",
                "url": (
                    "https://poetsandquants.com/school-profile/"
                    "carnegie-mellon-university-tepper-school-of-business/"
                ),
            },
            {
                "label": "Poets&Quants — Meet Tepper MBA Class of 2026",
                "url": (
                    "https://poetsandquants.com/2025/01/10/"
                    "meet-carnegie-mellon-teppers-mba-class-of-2026/"
                ),
            },
            {
                "label": "Tepper School — 2025 MBA Employment Report",
                "url": (
                    "https://www.cmu.edu/tepper/news/stories/"
                    "2025-mba-summary-employment-report"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "cmu-cs-bs": {
        "summary": (
            "Students and third-party guides consistently rank CMU's undergraduate "
            "computer science among the nation's best — #1 in multiple U.S. News "
            "specialties — praising world-class faculty, deep research access, and "
            "strong tech placement; common cautions are an intense workload, large "
            "introductory classes, and a highly competitive culture."
        ),
        "themes": [
            {
                "label": "Top-ranked program",
                "sentiment": "positive",
                "detail": (
                    "U.S. News ranks CMU #1 in AI, cybersecurity, software engineering, "
                    "and related CS specialties."
                ),
            },
            {
                "label": "Research & faculty",
                "sentiment": "positive",
                "detail": (
                    "Undergraduates access leading labs in AI, robotics, and systems "
                    "from the School of Computer Science."
                ),
            },
            {
                "label": "Tech placement",
                "sentiment": "positive",
                "detail": (
                    "Graduates place strongly into top technology firms and PhD programs."
                ),
            },
            {
                "label": "Rigor & workload",
                "sentiment": "caution",
                "detail": (
                    "A fast-paced, demanding curriculum with long hours is a recurring "
                    "theme."
                ),
            },
            {
                "label": "Competitive environment",
                "sentiment": "caution",
                "detail": (
                    "Large lower-division courses and peer competition can feel intense."
                ),
            },
        ],
        "sources": [
            {
                "label": "Niche — Carnegie Mellon University",
                "url": "https://www.niche.com/colleges/carnegie-mellon-university/",
            },
            {
                "label": "CMU News — U.S. News 2025 specialty rankings",
                "url": (
                    "https://www.cmu.edu/news/stories/archives/2024/september/"
                    "us-news-and-world-report-ranks-carnegie-mellon-university-"
                    "no-1-in-5-categories-21st-among-national"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "cmu-mscs": {
        "summary": (
            "Students and guides describe CMU's MS in Computer Science as a selective, "
            "research-oriented master's within the world's top-ranked CS school, with "
            "strong placement into industry R&D and PhD paths; cautions include "
            "limited seats, a thesis- or project-heavy workload, and Pittsburgh's "
            "smaller tech market versus coastal hubs."
        ),
        "themes": [
            {
                "label": "Elite CS pedigree",
                "sentiment": "positive",
                "detail": (
                    "Built inside the School of Computer Science with access to its "
                    "departments and institutes."
                ),
            },
            {
                "label": "Research depth",
                "sentiment": "positive",
                "detail": (
                    "Thesis and project options connect students to faculty-led research."
                ),
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is highly competitive with a small cohort.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Graduate CS courses are fast-paced and technically demanding.",
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Best Computer Science Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-science-schools/computer-science-rankings",
            },
            {
                "label": "Niche — Carnegie Mellon University Academics",
                "url": "https://www.niche.com/colleges/carnegie-mellon-university/academics/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "cmu-ms-ml": {
        "summary": (
            "The MS in Machine Learning is widely regarded as a premier specialized "
            "master's — CMU founded the first academic ML department — blending theory, "
            "systems, and applied research; students praise faculty depth but note "
            "steep prerequisites and an intense, research-heavy pace."
        ),
        "themes": [
            {
                "label": "Pioneering ML department",
                "sentiment": "positive",
                "detail": (
                    "Home to the first Machine Learning Department (2006) with leading "
                    "faculty."
                ),
            },
            {
                "label": "Technical depth",
                "sentiment": "positive",
                "detail": (
                    "Rigorous coursework spanning theory, optimization, and large-scale "
                    "learning."
                ),
            },
            {
                "label": "Prerequisites",
                "sentiment": "caution",
                "detail": (
                    "Strong math and CS background is expected; the pace is demanding."
                ),
            },
        ],
        "sources": [
            {
                "label": "CMU Machine Learning Department",
                "url": "https://www.ml.cmu.edu/",
            },
            {
                "label": "U.S. News — CMU AI specialty #1",
                "url": (
                    "https://www.cmu.edu/news/stories/archives/2024/september/"
                    "us-news-and-world-report-ranks-carnegie-mellon-university-"
                    "no-1-in-5-categories-21st-among-national"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "cmu-mhci": {
        "summary": (
            "Students and industry guides consistently rank CMU's MHCI as the "
            "longest-running and most influential HCI master's, highlighting its "
            "seven-month industry capstone and interdisciplinary electives; common "
            "cautions are an intense year-long schedule (often 60+ hour weeks), no "
            "built-in summer internship, and the cost of a full-time Pittsburgh year."
        ),
        "themes": [
            {
                "label": "Industry capstone",
                "sentiment": "positive",
                "detail": (
                    "A seven-month team project with an external client is the "
                    "program's signature experience."
                ),
            },
            {
                "label": "Interdisciplinary breadth",
                "sentiment": "positive",
                "detail": (
                    "Electives span design, CS, psychology, and business across CMU."
                ),
            },
            {
                "label": "UX career outcomes",
                "sentiment": "positive",
                "detail": (
                    "Alumni place into user research, product design, and PM roles at "
                    "major tech firms."
                ),
            },
            {
                "label": "Intense workload",
                "sentiment": "caution",
                "detail": (
                    "The three-semester calendar is consistently described as "
                    "demanding."
                ),
            },
            {
                "label": "No summer internship term",
                "sentiment": "caution",
                "detail": (
                    "The continuous August–August schedule leaves no dedicated "
                    "internship semester."
                ),
            },
        ],
        "sources": [
            {
                "label": "CMU HCII — Master of Human-Computer Interaction",
                "url": "https://www.hcii.cmu.edu/academics/mhci",
            },
            {
                "label": "Animation Career Review — Top Graduate HCI Programs 2025",
                "url": (
                    "https://www.animationcareerreview.com/articles/"
                    "top-10-private-graduate-uxuihci-schools-and-colleges-us-2025-rankings"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "cmu-msba": {
        "summary": (
            "Third-party guides rank Tepper's MS in Business Analytics highly (U.S. "
            "News #1 in business analytics among business schools), praising its "
            "quantitative curriculum and STEM designation; cautions include a "
            "shorter, intensive format and competition for analytics roles versus "
            "longer MBA paths."
        ),
        "themes": [
            {
                "label": "Top-ranked analytics",
                "sentiment": "positive",
                "detail": (
                    "U.S. News ranks CMU #1 in business analytics at the business-school "
                    "level."
                ),
            },
            {
                "label": "STEM & quant focus",
                "sentiment": "positive",
                "detail": (
                    "Analytics, machine learning, and optimization integrated with "
                    "business decision-making."
                ),
            },
            {
                "label": "Intensive timeline",
                "sentiment": "caution",
                "detail": (
                    "The nine-month full-time format moves quickly with heavy project "
                    "work."
                ),
            },
        ],
        "sources": [
            {
                "label": "CMU News — U.S. News business analytics #1",
                "url": (
                    "https://www.cmu.edu/news/stories/archives/2024/september/"
                    "us-news-and-world-report-ranks-carnegie-mellon-university-"
                    "no-1-in-5-categories-21st-among-national"
                ),
            },
            {
                "label": "Tepper School — MS in Business Analytics",
                "url": "https://www.cmu.edu/tepper/programs/master-business-analytics",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "cmu-mscf": {
        "summary": (
            "Industry observers regard CMU's MSCF as a pioneering quantitative-finance "
            "master's — celebrating 30 years in 2024 — with an interdisciplinary "
            "math-finance-stats-CS curriculum and strong sell-side placement; cautions "
            "include extreme selectivity, a heavy workload, and cyclical hiring in "
            "quant finance."
        ),
        "themes": [
            {
                "label": "Quant finance pioneer",
                "sentiment": "positive",
                "detail": (
                    "Among the oldest and best-known computational finance programs "
                    "globally."
                ),
            },
            {
                "label": "Placement record",
                "sentiment": "positive",
                "detail": (
                    "MSCF reports 99% of students received offers within three months "
                    "(recent three-year average)."
                ),
            },
            {
                "label": "Interdisciplinary rigor",
                "sentiment": "positive",
                "detail": (
                    "Faculty span math, statistics, finance, and computer science."
                ),
            },
            {
                "label": "Selectivity & pace",
                "sentiment": "caution",
                "detail": (
                    "Admission is highly competitive with a demanding technical workload."
                ),
            },
        ],
        "sources": [
            {
                "label": "CMU MSCF program site",
                "url": "https://www.cmu.edu/mscf/",
            },
            {
                "label": "CMU MSCF — Careers",
                "url": "https://www.cmu.edu/mscf/careers/index.html",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "cmu-mism": {
        "summary": (
            "Students and rankings sources highlight Heinz's MISM as a top "
            "information-systems master's (U.S. News #1 in MIS), blending analytics, "
            "technology, and policy with strong tech-consulting placement; cautions "
            "include a fast 16-month schedule and the need to self-direct recruiting "
            "outside core on-campus paths."
        ),
        "themes": [
            {
                "label": "Top MIS ranking",
                "sentiment": "positive",
                "detail": (
                    "U.S. News ranks CMU #1 in management information systems."
                ),
            },
            {
                "label": "Analytics + policy blend",
                "sentiment": "positive",
                "detail": (
                    "Combines data analytics with organizational and policy context."
                ),
            },
            {
                "label": "Tech & consulting paths",
                "sentiment": "positive",
                "detail": (
                    "Graduates enter product, consulting, and data roles at major firms."
                ),
            },
            {
                "label": "Accelerated schedule",
                "sentiment": "caution",
                "detail": (
                    "The 16-month curriculum packs internships and coursework tightly."
                ),
            },
        ],
        "sources": [
            {
                "label": "CMU News — U.S. News MIS #1",
                "url": (
                    "https://www.cmu.edu/news/stories/archives/2024/september/"
                    "us-news-and-world-report-ranks-carnegie-mellon-university-"
                    "no-1-in-5-categories-21st-among-national"
                ),
            },
            {
                "label": "Heinz College — MISM program",
                "url": (
                    "https://www.heinz.cmu.edu/programs/"
                    "information-systems-management-master/16-month"
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


# Built at import (after Tepper/Heinz specs are appended): the canonical program list.
def _description_for(spec: dict) -> str:
    """Field-specific description — never the degree-type classification stub."""
    clause = SLUG_DESCRIPTIONS.get(spec["slug"])
    if not clause:
        raise ValueError(f"Missing SLUG_DESCRIPTIONS entry for {spec['slug']!r}")
    fmt = spec["delivery_format"]
    delivery = ""
    if fmt == "online":
        delivery = " Delivered online."
    elif fmt == "hybrid":
        delivery = " Delivered in a hybrid format."
    return f"{clause}{delivery}"


def _build_programs() -> list[dict]:
    out: list[dict] = []
    for slug, name, dtype, school, dept, fmt, dur, url in _PROGRAM_SPECS:
        out.append(
            {
                "slug": slug,
                "program_name": name,
                "degree_type": dtype,
                "school": school,
                "department": dept,
                "delivery_format": fmt,
                "duration_months": dur,
                "website_url": url,
            }
        )
    return out


PROGRAMS: list[dict] = _build_programs()
for _p in PROGRAMS:
    _p["description"] = _description_for(_p)

_catalog_errors = validate_catalog(PROGRAMS)
_classification_stubs = sum(
    1 for p in PROGRAMS if _CLASSIFICATION_STUB_RE.match(p.get("description") or "")
)
_missing_desc = [p["slug"] for p in PROGRAMS if p["slug"] not in SLUG_DESCRIPTIONS]
if _missing_desc:
    _catalog_errors.append(f"missing SLUG_DESCRIPTIONS for {len(_missing_desc)} programs")
if _classification_stubs:
    _catalog_errors.append(f"classification-only descriptions on {_classification_stubs} programs")
if _catalog_errors:
    raise RuntimeError(f"CMU catalog quality gate failed: {_catalog_errors}")

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG = {p["slug"]: p for p in PROGRAMS}


def _requirements_for(spec: dict) -> dict:
    if spec["slug"] == _FLAGSHIP:
        return dict(_REQ_MBA)
    if spec["delivery_format"] == "online" or spec["degree_type"] == "certificate":
        return dict(_REQ_ONLINE)
    if spec["degree_type"] == "bachelors":
        return dict(_REQ_UNDERGRAD)
    return dict(_REQ_GRAD)


def _deadline_for(spec: dict) -> date | None:
    if spec["delivery_format"] == "online" or spec["degree_type"] == "certificate":
        return None
    if spec["degree_type"] == "bachelors":
        return date(2027, 1, 3)  # Regular Decision
    return date(2026, 12, 15)  # graduate baseline (varies by program)


# Professional/terminal doctorates registered under degree_type "phd" that are
# NOT funded research Ph.D.s (so they must not inherit zero, fully-funded tuition).
_UNFUNDED_DOCTORATE_SLUGS = {"cmu-ddes", "cmu-da-math"}


def _is_funded_phd(spec: dict) -> bool:
    return spec["degree_type"] == "phd" and spec["slug"] not in _UNFUNDED_DOCTORATE_SLUGS


def _tuition_for(spec: dict) -> int | None:
    if spec["degree_type"] == "bachelors":
        return _TUITION_UNDERGRAD
    if _is_funded_phd(spec):
        return 0  # funded research doctorates
    return None  # per-program graduate tuition deepened on a resume run


def _program_content_for(spec: dict) -> dict:
    """Program-level content_sources with program-specific keywords when defined."""
    kw = _PROGRAM_KEYWORDS.get(spec["slug"], _SCHOOL_KEYWORDS[spec["school"]])
    return _program_content(spec["school"], list(kw))


def _program_standard(slug: str, spec: dict | None = None) -> dict:
    """Per-program omitted-field list (verified-unavailable), for _standard."""
    if spec is None:
        spec = _SPEC_BY_SLUG[slug]
    has_tuition = slug in _COST_BY_SLUG or _tuition_for(spec) is not None
    has_outcomes = spec["degree_type"] in ("bachelors", "masters", "phd")
    omitted: list[str] = []
    if slug not in _TRACKS_BY_SLUG:
        omitted.append("tracks")
    if slug != _FLAGSHIP:
        if not has_tuition:
            omitted += ["cost_data.tuition_usd", "cost_data.source"]
        if has_outcomes:
            omitted += [
                "outcomes_data.employment_rate",
                "outcomes_data.top_industries",
                "outcomes_data.conditions",
            ]
        else:
            omitted += [
                "outcomes_data.employment_rate",
                "outcomes_data.median_salary",
                "outcomes_data.top_industries",
                "outcomes_data.conditions",
                "outcomes_data.source",
            ]
    else:
        omitted += [
            "outcomes_data.employment_rate",
            "outcomes_data.top_industries",
        ]
    if slug not in _CLASS_PROFILE_BY_SLUG:
        omitted.append("class_profile.cohort_size")
    if slug not in _FACULTY_BY_SLUG:
        omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    return _standard(omitted)


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich CMU to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when CMU is absent — safe on fresh/CI databases.
    """
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    for _path in _OMITTED_INSTITUTION:
        if _path.startswith("school_outcomes."):
            school_outcomes.pop(_path.split(".", 1)[1], None)
    school_outcomes["_standard"] = _standard(_OMITTED_INSTITUTION)
    inst.school_outcomes = school_outcomes
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    inst.founded_year = FOUNDED_YEAR
    inst.campus_setting = CAMPUS_SETTING
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
    for name, sc in existing.items():
        if name not in canonical_names:
            session.delete(sc)
    session.flush()
    return by_name


def _program_has_dependents(session: Session, program_id) -> bool:
    """True if any FK references this programs row (delete unsafe)."""
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
        p.duration_months = spec["duration_months"]
        p.description_text = _description_for(spec)
        p.website_url = spec["website_url"]
        p.department = spec["department"]
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec["delivery_format"]
        cost_override = _COST_BY_SLUG.get(slug)
        if cost_override is not None:
            p.tuition = cost_override.get("tuition_usd")
            p.cost_data = dict(cost_override)
        else:
            tuition = _tuition_for(spec)
            if tuition is not None:
                p.tuition = tuition
                p.cost_data = {
                    "tuition_usd": tuition,
                    "funded": _is_funded_phd(spec),
                    "source": _COST_SRC[0],
                    "source_url": _COST_SRC[1],
                    "year": "2025-26",
                }
            else:
                p.tuition = None
                p.cost_data = None
        p.application_requirements = _requirements_for(spec)
        if slug == _FLAGSHIP:
            outcomes = dict(_MBA_OUTCOMES)
        elif spec["degree_type"] in ("bachelors", "masters", "phd"):
            outcomes = dict(_OUTCOMES_INSTITUTION)
        else:
            outcomes = None
        if outcomes is not None:
            outcomes["_standard"] = _program_standard(slug, spec)
        else:
            outcomes = {"_standard": _program_standard(slug, spec)}
        p.outcomes_data = outcomes
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        if slug == _FLAGSHIP:
            p.content_sources = dict(_MBA_CONTENT)
        else:
            p.content_sources = _program_content_for(spec)
        p.application_deadline = date(2026, 1, 8) if slug == _FLAGSHIP else _deadline_for(spec)
    session.flush()
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
