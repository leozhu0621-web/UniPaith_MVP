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

Tuition backfill (2026-06-22, cmutuition1): every program carries a CMU-published
2026-27 tuition figure from Student Financial Services college/program tables;
funded research doctorates stamp tuition 0 with the published sticker in the note.
Per-credit, online-only, and CMU-Africa need-based programs without a single flat
annual figure are recorded as honest omissions (omit-never-guess).

Idempotent: ``apply(session)`` enriches the existing CMU institution (no-op when
absent, e.g. on a fresh CI database), creating/reconciling its schools + programs.
"""

from __future__ import annotations

# ruff: noqa: E501
import re
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.carnegie_mellon_cip_who import CIP6_BY_SLUG, WHO_BY_SLUG
from unipaith.data.carnegie_mellon_reviews_depth import DEPTH_REVIEWS
from unipaith.data.cmu_field_descriptions import SLUG_DESCRIPTIONS
from unipaith.data.profile_catalog_utils import validate_catalog
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Carnegie Mellon University"
ENRICHED_AT = "2026-06-22"

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
_TUITION_UNDERGRAD = 67020  # CMU SFS undergraduate tuition (2025-26 table; 2026-27 pending)

# Published tuition (matcher-core budget signal — REPAIR_BACKLOG run 75 HIGH #3).
# All figures are CMU SFS 2026-27 academic-year rates unless noted; funding is a
# separate signal — funded research Ph.D.s stamp tuition 0 with the sticker in note.
_TUI_SRC = "Carnegie Mellon University — Student Financial Services, Tuition & Fees (2026-27)"
_TUI_SRC_URL = "https://www.cmu.edu/sfs/tuition/graduate/index.html"
_TUI_AFRICA_SRC = "Carnegie Mellon University Africa — Tuition and financial aid (2025-26)"
_TUI_AFRICA_URL = "https://www.africa.engineering.cmu.edu/admissions/tuition.html"
_PHD_FUNDING_SRC = "Carnegie Mellon University — Graduate Admissions"
_PHD_FUNDING_URL = "https://www.cmu.edu/graduate/admissions/index.html"

# College annual graduate rates (CMU SFS 2026-27).
_TUITION_SCS_MASTERS = 62200
_TUITION_SCS_PHD_STICKER = 52000
_TUITION_CIT_MASTERS = 61510
_TUITION_CIT_PHD_STICKER = 52780
_TUITION_MCS_MASTERS = 60900
_TUITION_MCS_PHD_STICKER = 52300
_TUITION_DIETRICH = 53000
_TUITION_III = 61510
_TUITION_MSCF = 71800
_TUITION_HEINZ_SEMESTER = 29570
_TUITION_HEINZ_ANNUAL = 59140  # 2 semesters × $29,570 (Heinz full-time standard)
_TUITION_TEPPER_PHD_STICKER = 47000  # $23,500 × 2 semesters
_TUITION_AFRICA_INTL = 60300  # CMU-Africa international students, 2025-26

_CFA_DEPT_TUITION: dict[str, int] = {
    "School of Architecture": 44300,
    "School of Art": 36720,
    "School of Design": 45000,
    "School of Drama": 38496,
    "School of Music": 45950,
}

# Per-unit Tepper rates (annualized at a published full-time load for the matcher).
_TEPPER_MSBA_UNIT = 743
_TEPPER_MSM_UNIT = 695
_TEPPER_UNITS_PER_YEAR = 36

# Heinz per-unit programs (MPM, MSIT online).
_HEINZ_UNIT = 620
_HEINZ_UNITS_PER_YEAR = 48

# Programs whose tuition is per-credit/online-only with no flat annual figure.
_TUITION_OMIT_SLUGS = frozenset({
    "cmu-cert-fds-online",
})

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


# ── Depth-pass reviews (2026-06-12): coverable programs across SCS, Robotics, ──
# ── Engineering/INI, Heinz, Tepper, and CFA. Aggregated + cited; never quoted. ─
_DISC = (
    "Aggregated and paraphrased from public third-party sources — not individual "
    "verbatim reviews."
)
_SRC_USNEWS_GRAD_2026 = {
    "label": "U.S. News — CMU No. 1 in six 2026 Best Graduate Schools categories",
    "url": (
        "https://www.cmu.edu/news/stories/archives/2026/april/"
        "cmu-ranks-no-1-in-2026-us-news-graduate-rankings"
    ),
}
_SRC_CSD_GRAD = {
    "label": "CMU Computer Science Department — tops U.S. News graduate CS rankings",
    "url": "https://www.csd.cs.cmu.edu/news/cmu-tops-us-news-graduate-cs-rankings",
}
_SRC_USNEWS_UG_2025 = {
    "label": "U.S. News — CMU No. 1 in five undergraduate specialties (2025 Best Colleges)",
    "url": (
        "https://www.cmu.edu/news/stories/archives/2024/september/"
        "us-news-and-world-report-ranks-carnegie-mellon-university-"
        "no-1-in-5-categories-21st-among-national"
    ),
}
_SRC_HEINZ_RANK = {
    "label": "Heinz College — Rankings & Reputation",
    "url": "https://heinz.cmu.edu/about/rankings",
}
_SRC_NICHE_GRAD = {
    "label": "Niche — Carnegie Mellon University graduate student reviews",
    "url": "https://www.niche.com/graduate-schools/carnegie-mellon-university/reviews/",
}
_SRC_NICHE_CMU = {
    "label": "Niche — Carnegie Mellon University",
    "url": "https://www.niche.com/colleges/carnegie-mellon-university/",
}
_SRC_RI_EDU = {
    "label": "CMU Robotics Institute — academic programs",
    "url": "https://www.ri.cmu.edu/ri-education/",
}


def _rev(summary: str, themes: list[dict], sources: list[dict]) -> dict:
    return {"summary": summary, "themes": themes, "sources": sources, "disclaimer": _DISC}


_REVIEWS_BY_SLUG.update(
    {
        # ── School of Computer Science (No. 1 graduate CS, tied MIT/Stanford) ──
        "cmu-mcds": _rev(
            "Third-party guides and student reviews describe CMU's Master of "
            "Computational Data Science as a rigorous, systems-heavy data program "
            "housed in the nation's top-ranked computer science school, with deep "
            "engineering content and strong tech placement; common cautions are an "
            "intense workload, a high cost of attendance, and a more engineering- "
            "than-statistics orientation that suits builders more than pure analysts.",
            [
                {
                    "label": "Top-ranked CS school",
                    "sentiment": "positive",
                    "detail": (
                        "U.S. News ranks CMU No. 1 for graduate computer science "
                        "(tied with MIT and Stanford) and No. 1 in AI and systems."
                    ),
                },
                {
                    "label": "Systems + data engineering",
                    "sentiment": "positive",
                    "detail": (
                        "Coursework emphasizes large-scale data systems, cloud, and "
                        "machine learning over pure statistics."
                    ),
                },
                {
                    "label": "Tech placement",
                    "sentiment": "positive",
                    "detail": (
                        "Recruiters know the SCS brand; graduates place into data "
                        "engineering and ML roles at major technology firms."
                    ),
                },
                {
                    "label": "Heavy workload",
                    "sentiment": "caution",
                    "detail": (
                        "Reviewers consistently flag tight deadlines and a fast, "
                        "demanding pace."
                    ),
                },
                {
                    "label": "Cost",
                    "sentiment": "caution",
                    "detail": (
                        "A high total cost of attendance is a recurring consideration "
                        "for prospective students."
                    ),
                },
            ],
            [_SRC_CSD_GRAD, _SRC_USNEWS_GRAD_2026, _SRC_NICHE_GRAD],
        ),
        "cmu-msaii": _rev(
            "Students and third-party coverage view the MS in Artificial "
            "Intelligence and Innovation as a practitioner-focused SCS degree that "
            "pairs CMU's top-ranked AI faculty with applied, product-oriented "
            "capstones; cautions center on its demanding pace and a self-directed "
            "structure that rewards students who already have strong CS foundations.",
            [
                {
                    "label": "No. 1 AI faculty",
                    "sentiment": "positive",
                    "detail": (
                        "Built on the School of Computer Science, which U.S. News "
                        "ranks No. 1 for graduate artificial intelligence."
                    ),
                },
                {
                    "label": "Applied + product focus",
                    "sentiment": "positive",
                    "detail": (
                        "Emphasizes deploying AI into real products through team "
                        "capstones rather than research alone."
                    ),
                },
                {
                    "label": "Strong recruiting",
                    "sentiment": "positive",
                    "detail": "Graduates are sought for applied-ML and AI engineering roles.",
                },
                {
                    "label": "Prerequisite-heavy",
                    "sentiment": "caution",
                    "detail": (
                        "Best suited to applicants with solid programming and math "
                        "preparation; the curriculum moves quickly."
                    ),
                },
            ],
            [_SRC_CSD_GRAD, _SRC_USNEWS_GRAD_2026, _SRC_NICHE_GRAD],
        ),
        "cmu-mscv": _rev(
            "CMU's MS in Computer Vision, run out of the Robotics Institute, is "
            "described by program pages and student reviews as a short, intensive, "
            "industry-oriented degree concentrating on recognition and geometry; "
            "cautions are its narrow specialization and a compressed 16-month "
            "timeline that leaves little slack.",
            [
                {
                    "label": "Robotics Institute pedigree",
                    "sentiment": "positive",
                    "detail": (
                        "Taught within CMU's Robotics Institute, a global leader in "
                        "perception and vision research."
                    ),
                },
                {
                    "label": "Industry placement",
                    "sentiment": "positive",
                    "detail": (
                        "A project-based, applied focus aimed at vision roles in "
                        "industry and applied labs."
                    ),
                },
                {
                    "label": "Narrow specialization",
                    "sentiment": "caution",
                    "detail": (
                        "Deeply focused on computer vision rather than broad CS, which "
                        "may not fit students wanting flexibility."
                    ),
                },
                {
                    "label": "Compressed timeline",
                    "sentiment": "caution",
                    "detail": "A 16-month structure packs coursework and a group project tightly.",
                },
            ],
            [_SRC_RI_EDU, _SRC_USNEWS_GRAD_2026],
        ),
        "cmu-mlt": _rev(
            "The MS in Language Technologies, from CMU's Language Technologies "
            "Institute, is regarded by students and guides as a rigorous, "
            "research-adjacent NLP degree with access to leading faculty and a "
            "common PhD pipeline; cautions are a heavy research expectation and a "
            "demanding, fast-moving curriculum.",
            [
                {
                    "label": "Leading NLP faculty",
                    "sentiment": "positive",
                    "detail": (
                        "Part of the No. 1-ranked School of Computer Science, with "
                        "deep strength in natural language processing."
                    ),
                },
                {
                    "label": "Research access",
                    "sentiment": "positive",
                    "detail": (
                        "Strong thesis and lab opportunities; a recognized feeder to "
                        "top PhD programs and research roles."
                    ),
                },
                {
                    "label": "Research-heavy",
                    "sentiment": "caution",
                    "detail": (
                        "Best for students who want a research orientation rather than "
                        "a purely course-based professional track."
                    ),
                },
                {
                    "label": "Rigor",
                    "sentiment": "caution",
                    "detail": "A demanding workload and high expectations are recurring themes.",
                },
            ],
            [_SRC_CSD_GRAD, _SRC_USNEWS_GRAD_2026, _SRC_NICHE_GRAD],
        ),
        "cmu-mse": _rev(
            "CMU's Master of Software Engineering is widely cited as a flagship of "
            "the discipline — U.S. News ranks CMU No. 1 in software engineering — "
            "praised for a practice-based, team-project pedagogy from the Software "
            "Engineering Institute lineage; cautions are its cost and a curriculum "
            "geared toward experienced engineers rather than career-changers.",
            [
                {
                    "label": "No. 1 in software engineering",
                    "sentiment": "positive",
                    "detail": (
                        "U.S. News has ranked CMU No. 1 in software engineering at "
                        "both graduate and undergraduate levels."
                    ),
                },
                {
                    "label": "Practice-based studios",
                    "sentiment": "positive",
                    "detail": (
                        "A studio/project model with real clients develops engineering "
                        "leadership, not just coding."
                    ),
                },
                {
                    "label": "Industry credibility",
                    "sentiment": "positive",
                    "detail": "A long-recognized brand in software-engineering practice.",
                },
                {
                    "label": "Built for experienced engineers",
                    "sentiment": "caution",
                    "detail": (
                        "Several tracks expect prior professional experience; not a "
                        "first-coding-job program."
                    ),
                },
                {
                    "label": "Cost",
                    "sentiment": "caution",
                    "detail": "A high cost of attendance is a recurring consideration.",
                },
            ],
            [_SRC_CSD_GRAD, _SRC_USNEWS_UG_2025, _SRC_USNEWS_GRAD_2026],
        ),
        "cmu-mse-online": _rev(
            "The online MS in Software Engineering applies CMU's top-ranked "
            "software-engineering curriculum to a part-time, distance format aimed "
            "at working professionals; cautions are the self-discipline required "
            "for remote study and a cost comparable to on-campus study.",
            [
                {
                    "label": "Top-ranked curriculum",
                    "sentiment": "positive",
                    "detail": (
                        "Built on CMU's U.S. News No. 1 software-engineering "
                        "discipline strength."
                    ),
                },
                {
                    "label": "Flexible for professionals",
                    "sentiment": "positive",
                    "detail": "A part-time online format lets engineers study while working.",
                },
                {
                    "label": "Self-directed",
                    "sentiment": "caution",
                    "detail": (
                        "Remote delivery rewards strong time management and intrinsic "
                        "motivation."
                    ),
                },
            ],
            [_SRC_CSD_GRAD, _SRC_USNEWS_UG_2025],
        ),
        "cmu-ms-se-sv": _rev(
            "The Silicon Valley MS in Software Engineering co-locates CMU's "
            "software-engineering program with the Bay Area tech ecosystem, valued "
            "by students for proximity to employers; cautions are a high cost of "
            "living and a curriculum oriented to experienced engineers.",
            [
                {
                    "label": "Bay Area access",
                    "sentiment": "positive",
                    "detail": (
                        "Located at CMU's Silicon Valley campus, close to major "
                        "technology employers."
                    ),
                },
                {
                    "label": "Top-ranked discipline",
                    "sentiment": "positive",
                    "detail": "Carries CMU's No. 1 software-engineering reputation.",
                },
                {
                    "label": "Cost of living",
                    "sentiment": "caution",
                    "detail": "Silicon Valley living costs add to an already high tuition.",
                },
            ],
            [_SRC_CSD_GRAD, _SRC_USNEWS_UG_2025],
        ),
        "cmu-miis": _rev(
            "The MS in Intelligent Information Systems, from the Language "
            "Technologies Institute, is described as a project-driven SCS degree "
            "blending NLP, machine learning, and information retrieval; cautions are "
            "a heavy workload and a breadth that demands strong CS fundamentals.",
            [
                {
                    "label": "SCS / LTI faculty",
                    "sentiment": "positive",
                    "detail": (
                        "Taught within the No. 1-ranked School of Computer Science's "
                        "Language Technologies Institute."
                    ),
                },
                {
                    "label": "Applied ML + IR",
                    "sentiment": "positive",
                    "detail": (
                        "Combines machine learning, NLP, and information retrieval in "
                        "directed-study projects."
                    ),
                },
                {
                    "label": "Workload",
                    "sentiment": "caution",
                    "detail": "Reviewers cite an intense, deadline-driven pace.",
                },
            ],
            [_SRC_CSD_GRAD, _SRC_NICHE_GRAD],
        ),
        # ── Robotics Institute ─────────────────────────────────────────────────
        "cmu-msr": _rev(
            "CMU's MS in Robotics, run by the Robotics Institute, is described by "
            "program pages and students as a research-oriented, thesis-based degree "
            "with access to one of the world's largest robotics faculties; cautions "
            "are its research expectation and a competitive lab-placement process.",
            [
                {
                    "label": "World-leading robotics",
                    "sentiment": "positive",
                    "detail": (
                        "Housed in CMU's Robotics Institute, a pioneer in robotics "
                        "education and research."
                    ),
                },
                {
                    "label": "Research + thesis",
                    "sentiment": "positive",
                    "detail": (
                        "A 24-month coursework-and-thesis structure aimed at applied "
                        "research careers."
                    ),
                },
                {
                    "label": "Research-first fit",
                    "sentiment": "caution",
                    "detail": (
                        "Better suited to research-minded students than those wanting "
                        "a purely course-based path."
                    ),
                },
                {
                    "label": "Lab placement",
                    "sentiment": "caution",
                    "detail": "Securing a desired lab/advisor can be competitive.",
                },
            ],
            [_SRC_RI_EDU, _SRC_USNEWS_GRAD_2026],
        ),
        "cmu-mrsd": _rev(
            "The MS in Robotic Systems Development is reviewed as an industry- "
            "focused, systems-and-business robotics degree whose hallmark is a "
            "year-long team project; alumni report strong placement at robotics and "
            "tech firms (Amazon, NVIDIA, Microsoft and others), while cautions are a "
            "demanding 21-month pace and a practitioner rather than research focus.",
            [
                {
                    "label": "Systems + business blend",
                    "sentiment": "positive",
                    "detail": (
                        "Pairs robotics engineering with product development and "
                        "project-management training."
                    ),
                },
                {
                    "label": "Hands-on team project",
                    "sentiment": "positive",
                    "detail": (
                        "A signature multi-semester project builds production-ready "
                        "systems experience."
                    ),
                },
                {
                    "label": "Strong industry placement",
                    "sentiment": "positive",
                    "detail": (
                        "Alumni are recruited by major robotics and technology "
                        "employers per the program's placement data."
                    ),
                },
                {
                    "label": "Intense pace",
                    "sentiment": "caution",
                    "detail": "A 180-unit, 21-month schedule is demanding.",
                },
                {
                    "label": "Practitioner, not research",
                    "sentiment": "caution",
                    "detail": (
                        "Geared to industry roles rather than a research/PhD "
                        "trajectory."
                    ),
                },
            ],
            [
                {
                    "label": "CMU MRSD — about the program",
                    "url": "https://mrsd.ri.cmu.edu/about-mrsd/",
                },
                {
                    "label": "CMU MRSD — career placement",
                    "url": "https://mrsd.ri.cmu.edu/program-statistics/career-placement/",
                },
                _SRC_RI_EDU,
            ],
        ),
        "cmu-robotics-bs": _rev(
            "CMU's undergraduate robotics offering draws on the Robotics Institute "
            "and the No. 1-ranked School of Computer Science, praised for hands-on "
            "labs and research access; cautions mirror CMU broadly — an intense "
            "workload and a highly competitive environment.",
            [
                {
                    "label": "Robotics Institute access",
                    "sentiment": "positive",
                    "detail": "Undergraduates tap a world-leading robotics research community.",
                },
                {
                    "label": "Hands-on learning",
                    "sentiment": "positive",
                    "detail": "Strong lab, project, and research opportunities.",
                },
                {
                    "label": "Workload & competition",
                    "sentiment": "caution",
                    "detail": (
                        "A demanding curriculum and competitive peer culture are "
                        "recurring themes for CMU undergrads."
                    ),
                },
            ],
            [_SRC_RI_EDU, _SRC_NICHE_CMU],
        ),
        # ── College of Engineering / Information Networking Institute ──────────
        "cmu-ms-ece": _rev(
            "The MS in Electrical & Computer Engineering is described as a flexible, "
            "rigorous degree letting students draw on CMU's No. 4 (U.S. News) "
            "computer-engineering strength and adjacent CS courses; cautions are a "
            "self-directed course-selection model and a demanding workload.",
            [
                {
                    "label": "Top-ranked computer engineering",
                    "sentiment": "positive",
                    "detail": "U.S. News ranks CMU No. 4 in computer engineering (2026).",
                },
                {
                    "label": "Curricular flexibility",
                    "sentiment": "positive",
                    "detail": (
                        "Students customize across hardware, systems, ML, and "
                        "security with cross-listed CS courses."
                    ),
                },
                {
                    "label": "Self-directed",
                    "sentiment": "caution",
                    "detail": (
                        "Light hand-holding; students must plan their own course of "
                        "study."
                    ),
                },
                {
                    "label": "Workload",
                    "sentiment": "caution",
                    "detail": "A rigorous, fast-paced curriculum.",
                },
            ],
            [_SRC_USNEWS_GRAD_2026, _SRC_NICHE_GRAD],
        ),
        "cmu-msin": _rev(
            "The Information Networking Institute's flagship MS in Information "
            "Networking (founded 1989) is reviewed as a rigorous, security- and "
            "systems-heavy degree with strong tech placement under the CMU brand; "
            "the most common caution, echoed by alumni, is that the INI is "
            "relatively unknown outside CMU, though the university's name and the "
            "program's difficulty compensate.",
            [
                {
                    "label": "Systems + security depth",
                    "sentiment": "positive",
                    "detail": (
                        "Combines networking, software, distributed systems, and "
                        "information security with business and policy context."
                    ),
                },
                {
                    "label": "Strong placement",
                    "sentiment": "positive",
                    "detail": "Alumni become engineers and leaders across the tech industry.",
                },
                {
                    "label": "Rigorous courses",
                    "sentiment": "positive",
                    "detail": (
                        "Pittsburgh residency gives access to highly regarded CMU "
                        "systems and security courses."
                    ),
                },
                {
                    "label": "Lower name recognition",
                    "sentiment": "caution",
                    "detail": (
                        "Alumni note the INI is relatively unknown outside CMU, with "
                        "the CMU brand making up for it."
                    ),
                },
            ],
            [
                {
                    "label": "CMU INI — Master of Science in Information Networking",
                    "url": "https://www.cmu.edu/ini/academics/msin/index.html",
                },
                {
                    "label": "Quora — how good is MSIN at CMU INI (alumni discussion)",
                    "url": "https://www.quora.com/How-good-is-MSIN-at-Carnegie-Mellon-INI",
                },
            ],
        ),
        "cmu-msis": _rev(
            "The MS in Information Security (INI) is regarded as a deeply technical "
            "security degree backed by CMU's U.S. News No. 1 cybersecurity "
            "reputation, with rigorous coursework and strong recruiting; cautions "
            "match MSIN — a lesser-known department offset by the CMU brand and a "
            "heavy workload.",
            [
                {
                    "label": "Top cybersecurity reputation",
                    "sentiment": "positive",
                    "detail": "CMU is ranked No. 1 in cybersecurity by U.S. News.",
                },
                {
                    "label": "Technical rigor",
                    "sentiment": "positive",
                    "detail": (
                        "A demanding curriculum spanning systems, cryptography, and "
                        "applied security."
                    ),
                },
                {
                    "label": "Strong recruiting",
                    "sentiment": "positive",
                    "detail": "Graduates are competitive for security engineering roles.",
                },
                {
                    "label": "Department visibility",
                    "sentiment": "caution",
                    "detail": (
                        "Like MSIN, the INI is less known outside CMU; the brand and "
                        "rigor compensate."
                    ),
                },
            ],
            [_SRC_USNEWS_UG_2025, _SRC_HEINZ_RANK],
        ),
        "cmu-ece-bs": _rev(
            "CMU's undergraduate Electrical and Computer Engineering is praised for "
            "world-class faculty, deep ties to the No. 1 CS school, and strong tech "
            "placement; U.S. News ranks CMU No. 1 in cybersecurity and mobile/web "
            "applications. Cautions are an intense workload and a highly competitive "
            "culture.",
            [
                {
                    "label": "Elite engineering + CS ties",
                    "sentiment": "positive",
                    "detail": (
                        "ECE students leverage CMU's top-ranked computing ecosystem "
                        "across hardware and software."
                    ),
                },
                {
                    "label": "Top specialty rankings",
                    "sentiment": "positive",
                    "detail": (
                        "U.S. News ranks CMU No. 1 in cybersecurity and mobile/web "
                        "applications among undergraduate specialties."
                    ),
                },
                {
                    "label": "Strong placement",
                    "sentiment": "positive",
                    "detail": "Graduates place into top technology and hardware firms.",
                },
                {
                    "label": "Workload & competition",
                    "sentiment": "caution",
                    "detail": "A demanding, fast-paced, competitive environment.",
                },
            ],
            [_SRC_USNEWS_UG_2025, _SRC_NICHE_CMU],
        ),
        "cmu-meche-bs": _rev(
            "Undergraduate Mechanical Engineering at CMU earns a U.S. News top "
            "specialty ranking and is valued for hands-on design, robotics, and "
            "mechatronics tied to the wider CMU engineering and CS ecosystem; "
            "cautions are the broad workload and competitive culture common across "
            "CMU.",
            [
                {
                    "label": "Ranked specialty",
                    "sentiment": "positive",
                    "detail": (
                        "Mechanical engineering is among CMU's U.S. News top-five "
                        "undergraduate specialties."
                    ),
                },
                {
                    "label": "Interdisciplinary design",
                    "sentiment": "positive",
                    "detail": (
                        "Strong in mechatronics and robotics, drawing on CMU's "
                        "computing strengths."
                    ),
                },
                {
                    "label": "Workload",
                    "sentiment": "caution",
                    "detail": "A demanding curriculum and competitive peers are recurring themes.",
                },
            ],
            [_SRC_USNEWS_UG_2025, _SRC_NICHE_CMU],
        ),
        # ── Heinz College of Information Systems and Public Policy ─────────────
        "cmu-msppm": _rev(
            "Heinz College's MS in Public Policy & Management is described as a "
            "uniquely analytics-forward policy degree — U.S. News ranks Heinz No. 8 "
            "in public policy analysis and No. 1 in information & technology "
            "management — that fuses statistics, economics, and management; cautions "
            "are a quant-heavy core some policy-focused applicants find demanding and "
            "a required internship.",
            [
                {
                    "label": "Analytics-forward policy",
                    "sentiment": "positive",
                    "detail": (
                        "A STEM-designated curriculum infusing statistics, economics, "
                        "and finance into policy analysis."
                    ),
                },
                {
                    "label": "Top rankings",
                    "sentiment": "positive",
                    "detail": (
                        "U.S. News ranks Heinz No. 8 in public policy analysis and "
                        "No. 1 in information & technology management."
                    ),
                },
                {
                    "label": "Career flexibility",
                    "sentiment": "positive",
                    "detail": (
                        "Data skills open roles across government, consulting, and "
                        "the private sector."
                    ),
                },
                {
                    "label": "Quant-heavy",
                    "sentiment": "caution",
                    "detail": (
                        "The statistics and optimization core is demanding for "
                        "applicants seeking a purely qualitative policy program."
                    ),
                },
            ],
            [
                {
                    "label": "Heinz College — MS in Public Policy & Management",
                    "url": "https://www.heinz.cmu.edu/programs/public-policy-management-master/",
                },
                _SRC_HEINZ_RANK,
            ],
        ),
        "cmu-mpm": _rev(
            "The Master of Public Management is a part-time Heinz degree built for "
            "working professionals in the Pittsburgh region, applying the school's "
            "evidence-based, analytics-driven approach to leadership; cautions are "
            "its regional, part-time orientation and the same quantitative rigor "
            "Heinz is known for.",
            [
                {
                    "label": "Built for working professionals",
                    "sentiment": "positive",
                    "detail": (
                        "Evening/flexible classes let employed students continue "
                        "working while they study."
                    ),
                },
                {
                    "label": "Evidence-based leadership",
                    "sentiment": "positive",
                    "detail": (
                        "Applies Heinz's data and management toolkit to public-sector "
                        "leadership."
                    ),
                },
                {
                    "label": "Regional focus",
                    "sentiment": "caution",
                    "detail": (
                        "Oriented to Western Pennsylvania professionals rather than a "
                        "national full-time cohort."
                    ),
                },
            ],
            [
                {
                    "label": "Heinz College — Master of Public Management",
                    "url": "https://www.heinz.cmu.edu/programs/public-management-master/right-for-me",
                },
                _SRC_HEINZ_RANK,
            ],
        ),
        "cmu-mits": _rev(
            "The MS in Information Technology Strategy bridges Heinz College, the "
            "School of Computer Science, and the College of Engineering, valued for "
            "its interdisciplinary tech-and-management positioning under CMU's No. 1 "
            "information-systems reputation; cautions are a broad scope and the "
            "rigor of spanning three colleges.",
            [
                {
                    "label": "Interdisciplinary",
                    "sentiment": "positive",
                    "detail": (
                        "Joint Heinz/SCS/Engineering curriculum across technology, "
                        "policy, and management."
                    ),
                },
                {
                    "label": "Top information-systems brand",
                    "sentiment": "positive",
                    "detail": (
                        "Heinz is ranked No. 1 in information systems and information "
                        "& technology management by U.S. News."
                    ),
                },
                {
                    "label": "Broad scope",
                    "sentiment": "caution",
                    "detail": (
                        "The cross-college breadth demands focus to convert into a "
                        "clear specialization."
                    ),
                },
            ],
            [_SRC_HEINZ_RANK, _SRC_USNEWS_GRAD_2026],
        ),
        "cmu-msispm": _rev(
            "The MS in Information Security Policy & Management sits at Heinz "
            "College's intersection of cybersecurity and policy, backed by CMU's "
            "No. 1 cybersecurity standing; reviewers value the technical-plus-policy "
            "blend, while cautions are that it is less purely technical than the "
            "INI security degrees.",
            [
                {
                    "label": "Security + policy blend",
                    "sentiment": "positive",
                    "detail": (
                        "Combines technical security with governance, risk, and "
                        "management."
                    ),
                },
                {
                    "label": "Top cybersecurity reputation",
                    "sentiment": "positive",
                    "detail": "CMU is ranked No. 1 in cybersecurity by U.S. News.",
                },
                {
                    "label": "Less deeply technical",
                    "sentiment": "caution",
                    "detail": (
                        "Applicants wanting a pure engineering track may prefer the "
                        "INI's MSIS."
                    ),
                },
            ],
            [_SRC_HEINZ_RANK, _SRC_USNEWS_UG_2025],
        ),
        # ── Tepper School of Business ──────────────────────────────────────────
        "cmu-mba-online": _rev(
            "Tepper's Online Hybrid MBA is consistently top-ranked among online "
            "programs — U.S. News No. 3 and Poets&Quants No. 7 for 2025, with its "
            "online business-analytics specialty No. 1 for five straight years — and "
            "praised for delivering the same STEM-designated, analytics-forward "
            "curriculum and faculty as the full-time MBA; the standout caution is "
            "cost, as it is among the most expensive online MBAs.",
            [
                {
                    "label": "Top-ranked online MBA",
                    "sentiment": "positive",
                    "detail": (
                        "U.S. News ranked Tepper's online MBA No. 3 and P&Q No. 7 for "
                        "2025; its online MSBA specialty is No. 1."
                    ),
                },
                {
                    "label": "Same rigor as full-time",
                    "sentiment": "positive",
                    "detail": (
                        "A STEM-designated, analytics-heavy curriculum taught by the "
                        "same faculty as the residential MBA."
                    ),
                },
                {
                    "label": "Strong outcomes",
                    "sentiment": "positive",
                    "detail": (
                        "Online-hybrid graduates report competitive salaries and "
                        "signing bonuses in Tepper's outcomes data."
                    ),
                },
                {
                    "label": "High cost",
                    "sentiment": "caution",
                    "detail": (
                        "At roughly $149K it ranked as the most expensive program in "
                        "the 2025 P&Q online-MBA ranking."
                    ),
                },
                {
                    "label": "Self-paced demands",
                    "sentiment": "caution",
                    "detail": "A hybrid format rewards disciplined, self-directed learners.",
                },
            ],
            [
                {
                    "label": "Poets&Quants — best online MBA programs for 2025",
                    "url": (
                        "https://poetsandquants.com/2024/12/15/"
                        "best-online-mba-programs-in-the-u-s-for-2025/"
                    ),
                },
                {
                    "label": "Tepper School — 2025 U.S. News online rankings",
                    "url": "https://www.cmu.edu/tepper/news/stories/2025/0121-online-rankings",
                },
            ],
        ),
        "cmu-msm": _rev(
            "Tepper's MS in Management is described as a one-year, STEM-designated "
            "business master's that gives recent graduates the analytical and "
            "leadership grounding of the MBA core; cautions are that it is an early- "
            "career degree without the work-experience cohort or full recruiting "
            "depth of the MBA.",
            [
                {
                    "label": "Analytics-forward core",
                    "sentiment": "positive",
                    "detail": (
                        "Delivers Tepper's quantitative, STEM-designated business "
                        "foundation in a compact year."
                    ),
                },
                {
                    "label": "Early-career launch",
                    "sentiment": "positive",
                    "detail": (
                        "Targets recent graduates seeking a business credential before "
                        "extensive work experience."
                    ),
                },
                {
                    "label": "Not an MBA substitute",
                    "sentiment": "caution",
                    "detail": (
                        "Lacks the experienced-cohort network and recruiting breadth "
                        "of the full-time MBA."
                    ),
                },
            ],
            [_SRC_USNEWS_GRAD_2026, _SRC_NICHE_GRAD],
        ),
        # ── College of Fine Arts ───────────────────────────────────────────────
        "cmu-drama-bfa": _rev(
            "CMU's School of Drama — the oldest degree-granting drama program in the "
            "U.S. — is repeatedly ranked among the world's best (No. 4 in The "
            "Hollywood Reporter's 2025 list), with alumni holding 66 Tony Awards and "
            "the school named the Tony Awards' first higher-education partner; "
            "cautions are an extremely selective, conservatory-intensive experience "
            "and the inherent uncertainty of arts careers.",
            [
                {
                    "label": "Among the world's best",
                    "sentiment": "positive",
                    "detail": (
                        "Ranked No. 4 by The Hollywood Reporter (2025); the first U.S. "
                        "degree-granting drama program."
                    ),
                },
                {
                    "label": "Exceptional alumni record",
                    "sentiment": "positive",
                    "detail": (
                        "Alumni have won 66 Tony Awards; CMU is the Tony Awards' first "
                        "exclusive higher-education partner."
                    ),
                },
                {
                    "label": "Industry showcases",
                    "sentiment": "positive",
                    "detail": (
                        "NYC and LA showcases connect graduating students with "
                        "industry professionals."
                    ),
                },
                {
                    "label": "Highly selective + intense",
                    "sentiment": "caution",
                    "detail": (
                        "Conservatory training is rigorous and admission is extremely "
                        "competitive."
                    ),
                },
                {
                    "label": "Career uncertainty",
                    "sentiment": "caution",
                    "detail": "Outcomes depend on the unpredictable performing-arts market.",
                },
            ],
            [
                {
                    "label": "Hollywood Reporter ranking coverage (OnStage Pittsburgh, 2025)",
                    "url": (
                        "https://onstagepittsburgh.com/2025/06/24/"
                        "cmu-ranked-near-the-top-in-hollywood-reporters-best-drama-schools-list/"
                    ),
                },
                {
                    "label": "CMU — alumni Tony nominations and 66 wins (2026)",
                    "url": (
                        "https://www.cmu.edu/news/stories/archives/2026/may/"
                        "10-cmu-alumni-earn-record-breaking-15-tony-nominations"
                    ),
                },
            ],
        ),
        "cmu-design-bdes": _rev(
            "The School of Design is described as among the oldest and most "
            "respected design programs in North America — U.S. News has ranked it a "
            "top-five design school for over a decade — distinguished by a "
            "systems/interaction-design orientation within a top research "
            "university; cautions are an intense studio workload and a competitive "
            "admissions process.",
            [
                {
                    "label": "Top-five design school",
                    "sentiment": "positive",
                    "detail": (
                        "Recognized by U.S. News as a top-five design program for "
                        "over a decade."
                    ),
                },
                {
                    "label": "Interaction + systems focus",
                    "sentiment": "positive",
                    "detail": (
                        "Strong in communication, product, and interaction design "
                        "with a systems-thinking approach."
                    ),
                },
                {
                    "label": "Studio intensity",
                    "sentiment": "caution",
                    "detail": "A demanding studio culture with heavy time commitments.",
                },
            ],
            [
                {
                    "label": "CMU College of Fine Arts — School of Design",
                    "url": "https://cfa.cmu.edu/schools-and-academic-programs/school-of-design",
                },
                _SRC_NICHE_CMU,
            ],
        ),
        # ── Flagship undergraduate majors ──────────────────────────────────────
        "cmu-ai-bs": _rev(
            "CMU's undergraduate Artificial Intelligence degree — the first of its "
            "kind in the U.S. (launched 2018) — is built on the No. 1-ranked School "
            "of Computer Science and praised for a deep ML, math, and ethics "
            "curriculum with elite research access; cautions are CMU's hallmark "
            "intensity and a highly competitive, prerequisite-heavy path.",
            [
                {
                    "label": "First U.S. AI bachelor's",
                    "sentiment": "positive",
                    "detail": (
                        "CMU launched the nation's first undergraduate AI degree in "
                        "2018, within its top-ranked SCS."
                    ),
                },
                {
                    "label": "Rigorous, ethics-aware curriculum",
                    "sentiment": "positive",
                    "detail": (
                        "Spans machine learning, math, statistics, and courses on "
                        "ethics and societal impact."
                    ),
                },
                {
                    "label": "Elite research access",
                    "sentiment": "positive",
                    "detail": "Undergraduates work alongside leading AI faculty and labs.",
                },
                {
                    "label": "Intensity & competition",
                    "sentiment": "caution",
                    "detail": (
                        "A heavy workload and competitive culture are recurring CMU "
                        "themes."
                    ),
                },
            ],
            [
                {
                    "label": "CMU SCS — launch of the undergraduate AI degree",
                    "url": (
                        "https://www.cs.cmu.edu/news/2018/"
                        "carnegie-mellon-launches-undergraduate-degree-artificial-intelligence"
                    ),
                },
                _SRC_USNEWS_UG_2025,
            ],
        ),
        "cmu-information-systems-bs": _rev(
            "CMU's undergraduate Information Systems program (Dietrich College / "
            "Heinz ecosystem) is ranked U.S. News No. 1 in management information "
            "systems and valued for blending computing, business, and human-centered "
            "design with strong tech and consulting placement; cautions are a broad "
            "curriculum and CMU's demanding pace.",
            [
                {
                    "label": "No. 1 in MIS",
                    "sentiment": "positive",
                    "detail": (
                        "U.S. News ranks CMU No. 1 in management information systems "
                        "among undergraduate specialties."
                    ),
                },
                {
                    "label": "Tech + business + design",
                    "sentiment": "positive",
                    "detail": (
                        "Combines software, data, and user-centered design with "
                        "business context."
                    ),
                },
                {
                    "label": "Strong placement",
                    "sentiment": "positive",
                    "detail": "Graduates enter product, consulting, and software roles.",
                },
                {
                    "label": "Breadth & pace",
                    "sentiment": "caution",
                    "detail": (
                        "A wide-ranging curriculum and CMU's intensity demand strong "
                        "time management."
                    ),
                },
            ],
            [_SRC_USNEWS_UG_2025, _SRC_NICHE_CMU],
        ),
    }
)


# ── Depth-pass reviews, batch 2 (2026-06-12): Heinz analytics/policy, the joint ─
# ── CFA programs, Tepper/MCS computational finance, Dietrich statistics, and the ─
# ── College of Fine Arts architecture degrees. Aggregated + cited; never quoted. ─
_SRC_HEINZ_BIDA = {
    "label": "Heinz College — Business Intelligence & Data Analytics (MISM-BIDA)",
    "url": "https://www.heinz.cmu.edu/programs/information-systems-management-master/bida",
}
_SRC_HEINZ_MEIM_CAREERS = {
    "label": "Heinz College — Master of Entertainment Industry Management career outcomes",
    "url": (
        "https://www.heinz.cmu.edu/programs/entertainment-industry-management-master/"
        "meim-career-outcomes"
    ),
}
_SRC_NICHE_MEIM = {
    "label": "Niche — student profile, Heinz College Entertainment Industry Management",
    "url": (
        "https://www.niche.com/blog/i-found-my-niche-at-heinz-college-of-information-"
        "systems-and-public-policy/"
    ),
}
_SRC_HEINZ_MAM = {
    "label": "Heinz College — Master of Arts Management (joint with the College of Fine Arts)",
    "url": "https://www.heinz.cmu.edu/programs/arts-management-master/",
}
_SRC_BSCF = {
    "label": "Carnegie Mellon — Computational Finance (BSCF) program overview",
    "url": "https://www.math.cmu.edu/~bscf/cfatcmu.html",
}
_SRC_TEPPER_UG_2025 = {
    "label": "Tepper School — undergraduate U.S. News rankings (No. 6; No. 1 Analytics)",
    "url": "https://www.cmu.edu/tepper/news/stories/2025/0923-usnwr-rankings-ug-2025",
}
_SRC_ARCH_BARCH = {
    "label": "CMU School of Architecture — Bachelor of Architecture (B.Arch)",
    "url": "https://www.architecture.cmu.edu/barch",
}
_SRC_ARCH_ARE = {
    "label": "Black Spectacles — M.Arch programs and NCARB ARE 5.0 pass rates (2021–25)",
    "url": "https://www.blackspectacles.com/blog/top-10-masters-of-architecture-programs-in-the-us",
}
_SRC_CFA_ARCH = {
    "label": "CMU College of Fine Arts — School of Architecture",
    "url": "https://cfa.cmu.edu/schools-and-academic-programs/school-of-architecture",
}
_SRC_MADS_HANDBOOK = {
    "label": "CMU Dietrich — Master of Science in Applied Data Science (MADS) handbook",
    "url": "https://www.cmu.edu/dietrich/statistics-datascience/resources/docs/mads-grad-handbook.pdf",
}

_REVIEWS_BY_SLUG.update(
    {
        # ── Heinz College — analytics & public policy ──
        "cmu-mism-bida": _rev(
            "Third-party rankings and student reviews place CMU's Master of "
            "Information Systems Management — Business Intelligence & Data Analytics "
            "pathway among the strongest analytics-management master's in the country, "
            "pairing a top-ranked information-systems faculty with a STEM-designated, "
            "internship-anchored curriculum; common cautions are a heavy quantitative "
            "workload, a high cost of attendance, and a required internship that adds "
            "to the timeline for students without prior full-time experience.",
            [
                {
                    "label": "No. 1 information systems",
                    "sentiment": "positive",
                    "detail": (
                        "U.S. News ranks Heinz College No. 1 for Information Systems and "
                        "No. 2 for Business Analytics; INFORMS named it No. 1 in analytics "
                        "education."
                    ),
                },
                {
                    "label": "Applied analytics curriculum",
                    "sentiment": "positive",
                    "detail": (
                        "The BIDA pathway adds machine learning, predictive modeling, and "
                        "structured/unstructured data analytics on top of the MISM core."
                    ),
                },
                {
                    "label": "Experiential learning",
                    "sentiment": "positive",
                    "detail": (
                        "A required internship and client capstones connect coursework to "
                        "industry hiring."
                    ),
                },
                {
                    "label": "Quantitative intensity",
                    "sentiment": "caution",
                    "detail": (
                        "Reviewers describe a demanding, fast-paced quantitative load that "
                        "rewards strong analytical preparation."
                    ),
                },
                {
                    "label": "Cost",
                    "sentiment": "caution",
                    "detail": (
                        "A high total cost of attendance is a recurring consideration for "
                        "prospective students."
                    ),
                },
            ],
            [_SRC_HEINZ_BIDA, _SRC_HEINZ_RANK, _SRC_USNEWS_GRAD_2026],
        ),
        "cmu-mads": _rev(
            "CMU's Master of Science in Applied Data Science is described by program "
            "materials and student guides as an intensive nine-month professional "
            "degree run by Dietrich College's Department of Statistics & Data Science, "
            "emphasizing applied statistics, statistical computing, and professional "
            "skills; cautions center on its very compressed timeline and a "
            "statistics-forward orientation that suits analysts more than pure "
            "software engineers.",
            [
                {
                    "label": "Top statistics department",
                    "sentiment": "positive",
                    "detail": (
                        "Housed in a department U.S. News ranks No. 6 nationally for "
                        "graduate statistics."
                    ),
                },
                {
                    "label": "Applied, professional focus",
                    "sentiment": "positive",
                    "detail": (
                        "A core of applied linear models, statistical computing, data "
                        "engineering, and professional-skills coursework targets industry "
                        "roles."
                    ),
                },
                {
                    "label": "Fast completion",
                    "sentiment": "positive",
                    "detail": "A two-semester, nine-month structure gets graduates to market quickly.",
                },
                {
                    "label": "Compressed pace",
                    "sentiment": "caution",
                    "detail": (
                        "The short calendar leaves little slack and assumes solid "
                        "quantitative preparation on entry."
                    ),
                },
            ],
            [_SRC_MADS_HANDBOOK, _SRC_USNEWS_GRAD_2026, _SRC_HEINZ_RANK],
        ),
        "cmu-msppm-da": _rev(
            "Heinz College's Master of Science in Public Policy & Management — Data "
            "Analytics track is portrayed by third-party guides as a quantitatively "
            "rigorous policy degree that distinguishes CMU from traditional MPP "
            "programs; cautions are that its analytics emphasis is heavier than many "
            "policy applicants expect and that public-sector salary ranges can trail "
            "private-sector analytics roles.",
            [
                {
                    "label": "Analytics-driven policy",
                    "sentiment": "positive",
                    "detail": (
                        "Combines policy analysis with data, statistics, and management "
                        "coursework in CMU's data-forward Heinz tradition."
                    ),
                },
                {
                    "label": "Strong public-affairs standing",
                    "sentiment": "positive",
                    "detail": (
                        "U.S. News ranks Heinz No. 7 in Public Policy Analysis and No. 1 in "
                        "Information & Technology Management."
                    ),
                },
                {
                    "label": "Quantitative expectations",
                    "sentiment": "caution",
                    "detail": (
                        "The data-analytics emphasis is more technical than a conventional "
                        "MPP, which can surprise less quantitative applicants."
                    ),
                },
                {
                    "label": "Public-sector pay",
                    "sentiment": "caution",
                    "detail": (
                        "Graduates entering government or nonprofit roles may see lower pay "
                        "than peers in private analytics."
                    ),
                },
            ],
            [_SRC_HEINZ_RANK, _SRC_USNEWS_GRAD_2026],
        ),
        "cmu-msppm-dc": _rev(
            "The Washington, D.C. variant of Heinz College's MSPPM is described as "
            "pairing the program's quantitative policy core with a year based in the "
            "capital for direct access to federal agencies and think tanks; cautions "
            "are the higher cost of living in D.C. and the same analytics intensity "
            "that defines the Pittsburgh track.",
            [
                {
                    "label": "Washington access",
                    "sentiment": "positive",
                    "detail": (
                        "A D.C.-based curriculum places students near federal agencies, "
                        "Congress, and policy organizations."
                    ),
                },
                {
                    "label": "Data-forward policy training",
                    "sentiment": "positive",
                    "detail": (
                        "Retains Heinz's quantitative public-management core, a No. 7 "
                        "U.S. News public-policy-analysis program."
                    ),
                },
                {
                    "label": "Cost of living",
                    "sentiment": "caution",
                    "detail": "Living in Washington raises the overall cost of attendance.",
                },
            ],
            [_SRC_HEINZ_RANK, _SRC_USNEWS_GRAD_2026],
        ),
        "cmu-mshca": _rev(
            "CMU's Master of Science in Health Care Analytics & Information Technology "
            "is presented by ranking aggregators and Heinz materials as a specialized, "
            "data-intensive degree at the intersection of health policy and analytics; "
            "cautions are its narrow focus and a quantitative load that assumes "
            "comfort with statistics and information systems.",
            [
                {
                    "label": "Specialty leadership",
                    "sentiment": "positive",
                    "detail": (
                        "Ranked No. 1 in Health Care Analytics & Information Technology by "
                        "AnalyticsDegrees.org and backed by Heinz's No. 15 U.S. News health "
                        "policy standing."
                    ),
                },
                {
                    "label": "Cross-disciplinary fit",
                    "sentiment": "positive",
                    "detail": (
                        "Bridges health systems, policy, and analytics for roles in "
                        "providers, payers, and health-tech."
                    ),
                },
                {
                    "label": "Narrow specialization",
                    "sentiment": "caution",
                    "detail": (
                        "A tightly focused curriculum best suits students committed to the "
                        "health-care sector."
                    ),
                },
                {
                    "label": "Quantitative prerequisites",
                    "sentiment": "caution",
                    "detail": "Coursework assumes comfort with statistics and information systems.",
                },
            ],
            [_SRC_HEINZ_RANK, _SRC_USNEWS_GRAD_2026],
        ),
        "cmu-meim": _rev(
            "CMU's dual-city Master of Entertainment Industry Management — a joint "
            "Heinz College and College of Fine Arts degree split between Pittsburgh "
            "and Los Angeles — is widely described as a rare, data-driven path into "
            "entertainment with a strong alumni network and high placement; cautions "
            "are the travel-heavy structure, a famously competitive industry, and a "
            "small cohort that makes admission selective.",
            [
                {
                    "label": "Industry placement",
                    "sentiment": "positive",
                    "detail": (
                        "Heinz reports about 90% of graduates find full-time entertainment "
                        "roles within six months of graduating."
                    ),
                },
                {
                    "label": "Dual-city access",
                    "sentiment": "positive",
                    "detail": (
                        "A first year in Pittsburgh and second year in Los Angeles pairs "
                        "analytics training with direct industry internships."
                    ),
                },
                {
                    "label": "Alumni network",
                    "sentiment": "positive",
                    "detail": (
                        "Students and alumni cite an engaged, mentorship-oriented network "
                        "across film, TV, gaming, and music."
                    ),
                },
                {
                    "label": "Competitive field",
                    "sentiment": "caution",
                    "detail": (
                        "Entertainment is a notoriously difficult industry to break into, "
                        "even with strong support."
                    ),
                },
                {
                    "label": "Travel-heavy structure",
                    "sentiment": "caution",
                    "detail": (
                        "The cross-country, two-city format and required relocation are "
                        "demanding for some students."
                    ),
                },
            ],
            [_SRC_HEINZ_MEIM_CAREERS, _SRC_NICHE_MEIM, _SRC_HEINZ_RANK],
        ),
        "cmu-mam": _rev(
            "CMU's Master of Arts Management, a joint degree between Heinz College and "
            "the College of Fine Arts, is described as one of the most quantitative "
            "arts-administration programs in the country, blending analytics and "
            "management with arts and cultural-policy content; cautions are the "
            "limited salary ceilings common to nonprofit and cultural careers and a "
            "niche focus relative to a general management degree.",
            [
                {
                    "label": "Quantitative arts management",
                    "sentiment": "positive",
                    "detail": (
                        "Reviewers note an unusually analytics- and management-heavy "
                        "curriculum versus most arts-administration master's."
                    ),
                },
                {
                    "label": "Joint Heinz + CFA strength",
                    "sentiment": "positive",
                    "detail": (
                        "Draws on Heinz's management faculty and CMU's top-ranked College "
                        "of Fine Arts (No. 2 fine arts, U.S. News)."
                    ),
                },
                {
                    "label": "Nonprofit pay ceilings",
                    "sentiment": "caution",
                    "detail": (
                        "Arts and cultural-sector roles often carry lower salaries than "
                        "general-management paths."
                    ),
                },
                {
                    "label": "Niche focus",
                    "sentiment": "caution",
                    "detail": "Best suited to applicants committed to the arts and culture sector.",
                },
            ],
            [_SRC_HEINZ_MAM, _SRC_HEINZ_RANK, _SRC_USNEWS_GRAD_2026],
        ),
        # ── Tepper / Mellon College of Science — computational finance ──
        "cmu-compfin-bs": _rev(
            "The Bachelor of Science in Computational Finance — a joint program of the "
            "Mellon College of Science, Tepper School, and Heinz College — is "
            "described by the program and finance-industry coverage as a demanding "
            "applied-mathematics degree built as an undergraduate counterpart to CMU's "
            "pioneering MSCF, with a strong pipeline into major banks and trading "
            "firms; cautions are an exceptionally heavy math and programming load and "
            "a narrow orientation toward quantitative finance.",
            [
                {
                    "label": "Quant-finance pedigree",
                    "sentiment": "positive",
                    "detail": (
                        "Grew out of CMU's MSCF — the world's first computational-finance "
                        "master's — and shares its rigorous quantitative foundation."
                    ),
                },
                {
                    "label": "Wall Street placement",
                    "sentiment": "positive",
                    "detail": (
                        "Graduates have taken positions at firms including Goldman Sachs, "
                        "Citigroup, Bank of America, Deutsche Bank, UBS, and Citadel."
                    ),
                },
                {
                    "label": "Top business standing",
                    "sentiment": "positive",
                    "detail": (
                        "Tepper's undergraduate business program is No. 6 (U.S. News) with "
                        "No. 1 Analytics and No. 3 Quantitative Analysis specialties."
                    ),
                },
                {
                    "label": "Heavy workload",
                    "sentiment": "caution",
                    "detail": (
                        "Advanced math, probability/statistics, and programming make this "
                        "one of CMU's most demanding majors."
                    ),
                },
                {
                    "label": "Narrow orientation",
                    "sentiment": "caution",
                    "detail": (
                        "The curriculum is tightly aimed at quantitative finance rather "
                        "than broad business or CS."
                    ),
                },
            ],
            [_SRC_BSCF, _SRC_TEPPER_UG_2025, _SRC_USNEWS_GRAD_2026],
        ),
        # ── Dietrich College — statistics & machine learning ──
        "cmu-ms-statistics": _rev(
            "CMU's Master of Science in Statistics, in Dietrich College's Department of "
            "Statistics & Data Science, is described as a rigorous, methodology-focused "
            "degree from a top-ranked statistics department; cautions are a "
            "theory-heavy orientation and a smaller cohort than the university's larger "
            "data-science master's.",
            [
                {
                    "label": "Top-ranked department",
                    "sentiment": "positive",
                    "detail": (
                        "U.S. News ranks CMU No. 6 nationally for graduate statistics "
                        "(tied with Duke, Michigan, and Washington)."
                    ),
                },
                {
                    "label": "Methodological depth",
                    "sentiment": "positive",
                    "detail": (
                        "Emphasizes statistical theory and computing that transfer to "
                        "research and advanced analytics roles."
                    ),
                },
                {
                    "label": "Theory intensity",
                    "sentiment": "caution",
                    "detail": (
                        "The curriculum leans theoretical, which suits future "
                        "statisticians more than applied generalists."
                    ),
                },
            ],
            [_SRC_USNEWS_GRAD_2026, _SRC_HEINZ_RANK],
        ),
        "cmu-statistics-bs": _rev(
            "Carnegie Mellon's undergraduate Statistics major sits in a department "
            "U.S. News ranks among the nation's best for statistics, and student "
            "guides describe rigorous training in statistical reasoning and computing "
            "with strong analytics and graduate-school outcomes; cautions are a "
            "demanding quantitative core typical of CMU.",
            [
                {
                    "label": "Top statistics department",
                    "sentiment": "positive",
                    "detail": (
                        "Taught by a department ranked No. 6 for graduate statistics by "
                        "U.S. News."
                    ),
                },
                {
                    "label": "Computing-forward training",
                    "sentiment": "positive",
                    "detail": (
                        "Coursework blends statistical theory with heavy computing, fitting "
                        "data and analytics careers."
                    ),
                },
                {
                    "label": "Quantitative rigor",
                    "sentiment": "caution",
                    "detail": "The major carries the demanding quantitative load common across CMU.",
                },
            ],
            [_SRC_HEINZ_RANK, _SRC_NICHE_CMU],
        ),
        "cmu-stats-ml-bs": _rev(
            "CMU's Statistics and Machine Learning major is described as a "
            "distinctive joint undergraduate degree combining the Department of "
            "Statistics & Data Science with the Machine Learning Department, aimed at "
            "students who want both statistical foundations and modern ML; cautions "
            "are a heavy combined workload and prerequisites spanning two demanding "
            "fields.",
            [
                {
                    "label": "Two top departments",
                    "sentiment": "positive",
                    "detail": (
                        "Joins a No. 6 U.S. News statistics department with CMU's "
                        "No. 1-ranked AI/computer-science faculty."
                    ),
                },
                {
                    "label": "Statistics + ML balance",
                    "sentiment": "positive",
                    "detail": (
                        "Pairs statistical inference with machine-learning methods for "
                        "data-science and research careers."
                    ),
                },
                {
                    "label": "Demanding load",
                    "sentiment": "caution",
                    "detail": (
                        "Spanning two quantitative fields makes for a heavy, "
                        "prerequisite-rich program."
                    ),
                },
            ],
            [_SRC_HEINZ_RANK, _SRC_USNEWS_GRAD_2026, _SRC_NICHE_CMU],
        ),
        # ── College of Fine Arts — architecture ──
        "cmu-barch": _rev(
            "CMU's five-year Bachelor of Architecture is described by the school and "
            "design-industry coverage as a rigorous, NAAB-accredited, STEM-designated "
            "professional degree distinguished by early and deep integration of "
            "computational design, robotics, and digital fabrication; cautions are an "
            "intense studio culture, a long five-year commitment, and an architecture "
            "ranking landscape that has been unsettled since DesignIntelligence was "
            "discontinued.",
            [
                {
                    "label": "Technology-forward studio",
                    "sentiment": "positive",
                    "detail": (
                        "Pioneered integrating computational design, robotics, and digital "
                        "fabrication into architectural education."
                    ),
                },
                {
                    "label": "Licensure preparation",
                    "sentiment": "positive",
                    "detail": (
                        "NAAB-accredited with a roughly 74% NCARB ARE 5.0 pass rate "
                        "(2021–25 average across divisions)."
                    ),
                },
                {
                    "label": "STEM-designated",
                    "sentiment": "positive",
                    "detail": (
                        "Its STEM CIP code lets eligible international graduates access the "
                        "24-month OPT STEM extension."
                    ),
                },
                {
                    "label": "Demanding studio culture",
                    "sentiment": "caution",
                    "detail": (
                        "Students and reviewers describe a famously rigorous, time-intensive "
                        "studio sequence."
                    ),
                },
                {
                    "label": "Long commitment",
                    "sentiment": "caution",
                    "detail": "The first-professional path is a five-year degree.",
                },
            ],
            [_SRC_ARCH_BARCH, _SRC_ARCH_ARE, _SRC_CFA_ARCH],
        ),
        "cmu-march": _rev(
            "CMU's Master of Architecture is described as a graduate professional "
            "degree within a College of Fine Arts that U.S. News ranks among the "
            "nation's top fine-arts programs, sharing the school's computational- and "
            "sustainable-design emphasis; cautions are that it is a smaller, more "
            "recently re-established program and that the broader architecture-ranking "
            "picture is in flux.",
            [
                {
                    "label": "Top fine-arts college",
                    "sentiment": "positive",
                    "detail": (
                        "Housed in CMU's College of Fine Arts, ranked No. 2 in fine arts "
                        "by U.S. News."
                    ),
                },
                {
                    "label": "Computational & sustainable design",
                    "sentiment": "positive",
                    "detail": (
                        "Shares the school's research-driven focus on computational design, "
                        "building science, and sustainability."
                    ),
                },
                {
                    "label": "Smaller, newer program",
                    "sentiment": "caution",
                    "detail": (
                        "The graduate M.Arch is more recently re-established and smaller "
                        "than the long-running B.Arch."
                    ),
                },
            ],
            [_SRC_CFA_ARCH, _SRC_USNEWS_GRAD_2026, _SRC_ARCH_ARE],
        ),
    }
)


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

# Matcher-core gate (REPAIR_BACKLOG #1 / #4a): every program MUST carry a verified
# ``cip_code`` and a program-DISTINCT ``who_its_for`` (never a degree-type template).
# Fail the build if either is missing or if ``who_its_for`` collapses below ~0.9
# distinct/total (the type-gaming tell).
_cip_missing = [s for s in PROGRAM_SLUGS if s not in CIP6_BY_SLUG]
_who_missing = [s for s in PROGRAM_SLUGS if s not in WHO_BY_SLUG]
if _cip_missing:
    raise RuntimeError(f"CMU cip_code missing on {len(_cip_missing)} rows: {_cip_missing[:5]}")
if _who_missing:
    raise RuntimeError(f"CMU who_its_for missing on {len(_who_missing)} rows: {_who_missing[:5]}")
_who_values = [WHO_BY_SLUG[s] for s in PROGRAM_SLUGS]
_who_ratio = len(set(_who_values)) / len(_who_values)
if _who_ratio < 0.9:
    raise RuntimeError(
        f"CMU who_its_for type-gamed: distinct/total {_who_ratio:.2f} < 0.9 "
        "(field-specific statements required, not a degree-type template)"
    )


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


def _pub_tuition_cost(
    tuition: int,
    note: str,
    *,
    source: str = _TUI_SRC,
    source_url: str = _TUI_SRC_URL,
    funded: bool = False,
    extra: dict | None = None,
) -> dict:
    cost: dict = {
        "tuition_usd": tuition,
        "funded": funded,
        "note": note,
        "source": source,
        "source_url": source_url,
        "year": "2026-27",
    }
    if extra:
        cost.update(extra)
    return cost


def _omit_tuition_cost(
    note: str,
    *,
    source: str | None = None,
    source_url: str | None = None,
) -> dict:
    return {
        "note": note,
        "source": source or _TUI_SRC,
        "source_url": source_url or _TUI_SRC_URL,
        "year": "2026-27",
    }


def _annualize_per_unit(unit_rate: int, units: int = _TEPPER_UNITS_PER_YEAR) -> int:
    return unit_rate * units


def _cfa_annual_rate(department: str) -> int:
    for key, rate in _CFA_DEPT_TUITION.items():
        if key in department:
            return rate
    return _CFA_DEPT_TUITION["School of Architecture"]


def _phd_sticker_for(spec: dict) -> int:
    school = spec["school"]
    if school == _SCS:
        return _TUITION_SCS_PHD_STICKER
    if school == _CIT:
        return _TUITION_CIT_PHD_STICKER
    if school == _MCS:
        return _TUITION_MCS_PHD_STICKER
    if school == _TEPPER:
        return _TUITION_TEPPER_PHD_STICKER
    if school == _HEINZ:
        return _TUITION_HEINZ_ANNUAL
    if school == _CFA:
        return _cfa_annual_rate(spec["department"])
    return _TUITION_DIETRICH


def _program_tuition(spec: dict) -> tuple[int | None, dict]:
    """Return (matcher_tuition, cost_data) from CMU-published 2026-27 rates."""
    slug = spec["slug"]
    dtype = spec["degree_type"]
    school = spec["school"]

    if slug in _COST_BY_SLUG:
        cost = dict(_COST_BY_SLUG[slug])
        return cost.get("tuition_usd"), cost

    if slug in _TUITION_OMIT_SLUGS:
        return None, _omit_tuition_cost(
            "Tuition for this program is billed per credit hour or per term with no "
            "single flat annual figure published; see the program's CMU tuition page "
            "for current rates.",
        )

    if slug == "cmu-mse-online":
        return _TUITION_SCS_MASTERS, _pub_tuition_cost(
            _TUITION_SCS_MASTERS,
            "Published SCS master's tuition (2026-27); the online MSE program uses the "
            "same per-academic-year tuition table as on-campus SCS master's programs.",
            source_url="https://www.cmu.edu/sfs/tuition/graduate/scs.html",
        )
    if slug == "cmu-miips-online":
        return _TUITION_III, _pub_tuition_cost(
            _TUITION_III,
            "Published Integrated Innovation Institute tuition (2026-27).",
            source_url="https://www.cmu.edu/sfs/tuition/graduate/iii.html",
        )
    if slug == "cmu-msba-online":
        annual = _annualize_per_unit(_TEPPER_MSBA_UNIT)
        return annual, _pub_tuition_cost(
            annual,
            f"Published part-time/online Tepper MSBA tuition at ${_TEPPER_MSBA_UNIT:,} "
            f"per unit; annualized at {_TEPPER_UNITS_PER_YEAR} units.",
            source_url="https://www.cmu.edu/sfs/tuition/graduate/tepper/msba.html",
            extra={"per_unit": _TEPPER_MSBA_UNIT},
        )
    if slug == "cmu-mba-online":
        unit = 769
        annual = _annualize_per_unit(unit)
        return annual, _pub_tuition_cost(
            annual,
            f"Published Online Hybrid MBA tuition at ${unit:,} per unit; annualized at "
            f"{_TEPPER_UNITS_PER_YEAR} units for the matcher budget signal.",
            source_url="https://www.cmu.edu/sfs/tuition/graduate/tepper/online-hybrid-mba.html",
            extra={"per_unit": unit},
        )
    if slug == "cmu-msit-online":
        annual = _HEINZ_UNIT * _HEINZ_UNITS_PER_YEAR
        return annual, _pub_tuition_cost(
            annual,
            f"Published online Heinz MSIT tuition at ${_HEINZ_UNIT:,} per unit; "
            f"annualized at {_HEINZ_UNITS_PER_YEAR} units.",
            source_url="https://www.cmu.edu/sfs/tuition/graduate/heinz/mpm-msit.html",
            extra={"per_unit": _HEINZ_UNIT},
        )

    if dtype == "bachelors":
        return _TUITION_UNDERGRAD, {
            "tuition_usd": _TUITION_UNDERGRAD,
            "funded": False,
            "source": _COST_SRC[0],
            "source_url": _COST_SRC[1],
            "year": "2025-26",
        }

    if slug.startswith("cmu-africa-"):
        return _TUITION_AFRICA_INTL, _pub_tuition_cost(
            _TUITION_AFRICA_INTL,
            "Published CMU-Africa tuition for international students (2025-26); "
            "African students may receive need-based aid covering a substantial "
            "fraction of cost.",
            source=_TUI_AFRICA_SRC,
            source_url=_TUI_AFRICA_URL,
        )

    if dtype == "phd":
        if slug == "cmu-da-math":
            return _TUITION_MCS_PHD_STICKER, _pub_tuition_cost(
                _TUITION_MCS_PHD_STICKER,
                "Published Mellon College of Science doctoral tuition sticker "
                "(2026-27); the Doctor of Arts is not fully funded like research Ph.D.s.",
            )
        if slug == "cmu-ddes":
            rate = _cfa_annual_rate(spec["department"])
            return rate, _pub_tuition_cost(
                rate,
                "Published College of Fine Arts graduate tuition for the School of "
                "Architecture (2026-27); the Doctor of Design is a terminal professional "
                "degree, not a funded research doctorate.",
                source_url="https://www.cmu.edu/sfs/tuition/graduate/cfa.html",
            )
        sticker = _phd_sticker_for(spec)
        return 0, _pub_tuition_cost(
            0,
            (
                "CMU Ph.D. students typically receive full tuition plus a stipend "
                "through fellowship and assistantship support; the published "
                f"doctoral tuition sticker is ${sticker:,} per year before aid."
            ),
            source=_PHD_FUNDING_SRC,
            source_url=_PHD_FUNDING_URL,
            funded=True,
            extra={"published_tuition_sticker": sticker},
        )

    if dtype == "certificate":
        return None, _omit_tuition_cost(
            "Graduate certificates are billed per credit hour; CMU publishes no "
            "single flat annual certificate tuition figure.",
        )

    if school == _TEPPER:
        if slug == "cmu-mscf":
            return _TUITION_MSCF, _pub_tuition_cost(
                _TUITION_MSCF,
                "Published MSCF tuition for the 2026-27 academic year (Pittsburgh "
                "and New York tracks).",
                source_url="https://www.cmu.edu/sfs/tuition/graduate/mscf.html",
            )
        if slug == "cmu-mspm":
            rate = 79272  # $39,636 × 2 semesters (Spring 2026 cohort table)
            return rate, _pub_tuition_cost(
                rate,
                "Published Tepper MSPM tuition at $39,636 per semester for the Spring 2026 "
                "cohort (spring + fall semesters; summer internship billed separately).",
                source_url="https://www.cmu.edu/sfs/tuition/graduate/tepper/mspm-spring2026.html",
            )
        if slug == "cmu-msba":
            annual = _annualize_per_unit(_TEPPER_MSBA_UNIT)
            return annual, _pub_tuition_cost(
                annual,
                f"Published Tepper MSBA tuition at ${_TEPPER_MSBA_UNIT:,} per unit; "
                f"annualized at {_TEPPER_UNITS_PER_YEAR} units for the matcher budget signal.",
                source_url="https://www.cmu.edu/sfs/tuition/graduate/tepper/full-msba.html",
                extra={"per_unit": _TEPPER_MSBA_UNIT},
            )
        if slug == "cmu-msm":
            annual = _annualize_per_unit(_TEPPER_MSM_UNIT)
            return annual, _pub_tuition_cost(
                annual,
                f"Published Tepper MSM tuition at ${_TEPPER_MSM_UNIT:,} per unit; "
                f"annualized at {_TEPPER_UNITS_PER_YEAR} units for the matcher budget signal.",
                source_url="https://www.cmu.edu/sfs/tuition/graduate/tepper/msm.html",
                extra={"per_unit": _TEPPER_MSM_UNIT},
            )

    if school == _HEINZ:
        if slug == "cmu-mpm":
            annual = _HEINZ_UNIT * _HEINZ_UNITS_PER_YEAR
            return annual, _pub_tuition_cost(
                annual,
                f"Published Heinz MPM tuition at ${_HEINZ_UNIT:,} per unit; "
                f"annualized at {_HEINZ_UNITS_PER_YEAR} units for the matcher budget signal.",
                source_url="https://www.cmu.edu/sfs/tuition/graduate/heinz/mpm-msit.html",
                extra={"per_unit": _HEINZ_UNIT},
            )
        return _TUITION_HEINZ_ANNUAL, _pub_tuition_cost(
            _TUITION_HEINZ_ANNUAL,
            f"Published Heinz full-time tuition at ${_TUITION_HEINZ_SEMESTER:,} per "
            "semester (standard two-semester academic year).",
            source_url="https://www.cmu.edu/sfs/tuition/graduate/heinz/mism.html",
        )

    if school == _SCS:
        return _TUITION_SCS_MASTERS, _pub_tuition_cost(
            _TUITION_SCS_MASTERS,
            "Published SCS master's program tuition for the 2026-27 academic year.",
            source_url="https://www.cmu.edu/sfs/tuition/graduate/scs.html",
        )

    if school == _CIT:
        dept = spec.get("department", "")
        if dept in ("Integrated Innovation Institute", "Engineering & Technology Innovation Management"):
            rate = _TUITION_III if dept == "Integrated Innovation Institute" else _TUITION_CIT_MASTERS
            url = (
                "https://www.cmu.edu/sfs/tuition/graduate/iii.html"
                if dept == "Integrated Innovation Institute"
                else "https://www.cmu.edu/sfs/tuition/graduate/cit.html"
            )
            return rate, _pub_tuition_cost(
                rate,
                f"Published CMU {dept} master's tuition for the 2026-27 academic year.",
                source_url=url,
            )
        return _TUITION_CIT_MASTERS, _pub_tuition_cost(
            _TUITION_CIT_MASTERS,
            "Published College of Engineering master's tuition for the 2026-27 "
            "academic year.",
            source_url="https://www.cmu.edu/sfs/tuition/graduate/cit.html",
        )

    if school == _MCS:
        return _TUITION_MCS_MASTERS, _pub_tuition_cost(
            _TUITION_MCS_MASTERS,
            "Published Mellon College of Science master's tuition for the 2026-27 "
            "academic year.",
            source_url="https://www.cmu.edu/sfs/tuition/graduate/mcs.html",
        )

    if school == _DIETRICH:
        return _TUITION_DIETRICH, _pub_tuition_cost(
            _TUITION_DIETRICH,
            "Published Dietrich College graduate tuition for the 2026-27 academic year.",
            source_url="https://www.cmu.edu/sfs/tuition/graduate/dc.html",
        )

    if school == _CFA:
        rate = _cfa_annual_rate(spec["department"])
        return rate, _pub_tuition_cost(
            rate,
            f"Published College of Fine Arts graduate tuition for {spec['department']} "
            "(2026-27 academic year).",
            source_url="https://www.cmu.edu/sfs/tuition/graduate/cfa.html",
        )

    return None, _omit_tuition_cost(
        "Tuition varies by program; see the official CMU tuition page for current rates.",
    )


def _is_funded_phd(spec: dict) -> bool:
    return spec["degree_type"] == "phd" and spec["slug"] not in _UNFUNDED_DOCTORATE_SLUGS


def _program_content_for(spec: dict) -> dict:
    """Program-level content_sources with program-specific keywords when defined."""
    kw = _PROGRAM_KEYWORDS.get(spec["slug"], _SCHOOL_KEYWORDS[spec["school"]])
    return _program_content(spec["school"], list(kw))


def _program_standard(slug: str, spec: dict | None = None) -> dict:
    """Per-program omitted-field list (verified-unavailable), for _standard."""
    if spec is None:
        spec = _SPEC_BY_SLUG[slug]
    has_tuition = _program_tuition(spec)[0] is not None
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
        p.cip_code = CIP6_BY_SLUG.get(slug)
        p.who_its_for = WHO_BY_SLUG.get(slug)
        tuition, cost = _program_tuition(spec)
        p.tuition = tuition
        p.cost_data = cost
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
