"""Canonical Princeton University profile — the single source of truth.

Real, sourced data only (U.S. Dept. of Education College Scorecard, UNITID 186131 ·
NCES College Navigator / IPEDS · Princeton's Office of Institutional Research Common
Data Set 2024-25 · the official Princeton "Facts & Figures" page · the official QS /
Times Higher Education / U.S. News rankings · Princeton's Office of the Dean of the
Faculty Chapter III "Academic Divisions" · each school's official leadership / about
page · the College Scorecard Field-of-Study earnings by CIP). ``apply(session)``
idempotently enriches the Princeton institution row, upserts its real degree-granting
academic units, and builds Princeton's program catalog across them.

Princeton's academic structure (Office of the Dean of the Faculty, Chapter III):
the faculty is organized into four divisions — I the Humanities (incl. Architecture),
II the Social Sciences (incl. History and the School of Public and International
Affairs), III the Natural Sciences (incl. Mathematics and Psychology), and IV
Engineering and Applied Science. Except for Engineering, the divisions have no
administrative or instructional responsibilities — they group departments. We map
Princeton's units onto the platform's ``School`` model as:
  - School of Engineering and Applied Science (SEAS — Division IV, a real dean-led school)
  - Princeton School of Public and International Affairs (SPIA — a real dean-led school)
  - The Humanities (Division I)
  - The Social Sciences (Division II)
  - The Natural Sciences (Division III)

It **flushes but does not commit** — the caller (the Alembic data migration, the CLI
script, or the dev seed) owns the transaction. It is a **no-op** (returns ``False``)
when Princeton is absent, so it is safe to run against a fresh or CI database.
Re-running is safe: units key off ``(institution_id, name)`` and programs off ``slug``;
stale rows are reconciled without breaking foreign keys.

This mirrors ``mit_profile`` / ``berkeley_profile`` / ``harvard_profile`` so the
migration, the standalone script, and the dev seed all agree (DRY). Every figure
traces to a public, citable source; anything that could not be verified from a
first-party or two-independent-source basis is **omitted** (recorded in the relevant
``_standard.omitted`` list), never guessed. Computer Science is the most-enriched
flagship program (its real research areas, faculty, class profile, and aggregated
reviews), mirroring MIT Sloan's MBAn in the reference instance — with the honest
caveats that Princeton is test-optional through the fall-2027 entry cycle (returning to
required testing for the 2027-28 cycle) and that the canonical program set is the
complete federal College Scorecard Field-of-Study list for UNITID 186131; graduate
School of Architecture M.Arch. and SEAS M.S.E./M.Eng. programs carry verified names,
descriptions, and coverable external reviews.
"""

from __future__ import annotations

import re
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.princeton_field_descriptions import (
    FIELD_ALIASES,
    FIELD_DESCRIPTIONS,
    SLUG_DESCRIPTIONS,
)
from unipaith.data.princeton_ipeds_catalog import _IPEDS_CATALOG
from unipaith.data.profile_catalog_utils import validate_catalog
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Princeton University"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-17"

_CLASSIFICATION_STUB_RE = re.compile(
    r"^.+ is (an undergraduate|a graduate|a doctoral|a graduate certificate|"
    r"a professional|a degree) program at Princeton",
)
_TEMPLATE_STUB_RE = re.compile(
    r" — a .+ (undergraduate|graduate|doctoral|certificate|professional|"
    r"master's|bachelor's|phd|bachelors|masters) program offered through ",
    re.I,
)
_PREFIX_NAME_RE = re.compile(
    r"^(Bachelor's in|Master's in|Doctor of Philosophy in|Graduate Certificate in|"
    r"Professional program in) "
)

_SLUG_TO_FIELD: dict[str, str] = {
    slug: field_name for slug, _, field_name, _, _, _, _, _ in _IPEDS_CATALOG
}

# Standalone master's degrees Princeton publishes (not incidental M.A. along the Ph.D. path).
_IPEDS_MASTERS_ALLOWLIST = frozenset({
    "princeton-architecture-ms",
    "princeton-chemical-engineering-ms",
    "princeton-civil-engineering-ms",
    "princeton-electrical-electronics-and-communications-engineering-ms",
    "princeton-mechanical-engineering-ms",
})


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
    # Princeton's Center for Career Development publishes first-destination outcomes by
    # industry sector but not a single clean university-wide "employed or continuing
    # education" headline rate we could verify across a stated class; the top industry
    # sectors are reported instead, and program-level federal earnings are captured per
    # program. Omitted rather than asserting a conflated rate.
    "school_outcomes.employed_or_continuing_ed",
]

# ── Institution-level data ────────────────────────────────────────────────
# Rankings are stored as {rank, year} objects (the page renders any ranking_data entry
# that is an object with a numeric `rank`). All three ranks are quoted from the official
# ranking bodies for the 2026 editions.
RANKING_DATA: dict = {
    "ownership_type": "private",
    # Princeton is accredited by the Middle States Commission on Higher Education.
    "accreditor": "MSCHE",
    # Carnegie basic classification (R1).
    "carnegie_classification": "Doctoral Universities: Very High Research Activity",
    # QS World University Rankings 2026: Princeton is ranked #25 worldwide.
    "qs_world_university_rankings": {"rank": 25, "year": 2026},
    # THE World University Rankings 2026: joint #3 in the world (Princeton's best-ever).
    "times_higher_education": {"rank": 3, "year": 2026},
    # U.S. News Best Colleges (National Universities) 2026: #1 nationally (15th year).
    "us_news_national": {"rank": 1, "year": 2026},
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below is
# complete, so a shallow merge is correct. Figures are College Scorecard (UNITID 186131)
# cross-checked against Princeton's Common Data Set 2024-25, NCES College Navigator
# (IPEDS), and Princeton's official "Facts & Figures" page where each publishes a metric.
SCHOOL_OUTCOMES: dict = {
    # CDS 2024-25: 1,868 admits / 40,468 first-year applicants = 4.62% (Scorecard 0.0462).
    "admit_rate": 0.0462,
    "avg_net_price": 6128,
    "median_earnings_10yr": 110066,
    "completion_rate_4yr_150pct": 0.9761,
    # NCES College Navigator (IPEDS): first-year retention (Fall 2023 cohort) = 98%.
    "retention_rate_first_year": 0.98,
    # NCES College Navigator (IPEDS): six-year graduation rate (Fall 2018 cohort) = 98%.
    "graduation_rate_6yr": 0.98,
    "financial_aid": {
        # College Navigator (IPEDS): 20% of undergraduates received a Pell grant; 2%
        # took federal student loans (Princeton meets full need with grants, not loans).
        "pell_grant_rate": 0.20,
        "federal_loan_rate": 0.02,
        # College Scorecard average annual cost of attendance.
        "cost_of_attendance": 84040,
    },
    # Undergraduate race/ethnicity (NCES College Navigator / IPEDS, Fall 2024).
    "demographics": {
        "white": 0.33,
        "black": 0.09,
        "hispanic": 0.10,
        "asian": 0.23,
        "two_or_more": 0.07,
        "international": 0.13,
    },
    # SAT/ACT 25th-75th percentiles of enrolled first-years (College Navigator, Fall 2024).
    "test_scores": {
        "sat_reading_25_75": [740, 780],
        "sat_math_25_75": [770, 800],
        "act_25_75": [34, 35],
    },
    # Princeton main campus, Princeton, New Jersey.
    "location": {"lat": 40.34528, "lng": -74.65611},
    "campus_basics": {"location": "Princeton, New Jersey"},
    "scale": {
        # Princeton "Facts & Figures": 1,313 faculty (full-time, part-time and visiting).
        "faculty_count": 1313,
        # Princeton "Facts & Figures": 5:1 student-faculty ratio.
        "student_faculty_ratio": "5:1",
        # PRINCO / Princeton: endowment $36.4 billion at fiscal year-end June 30, 2025.
        "endowment_usd": 36400000000,
    },
    # Princeton Center for Career Development first-destination industry sectors (the
    # categories graduates enter; business is the largest, ~30% annually).
    "top_employer_industries": [
        "Business",
        "Engineering, health, science & technology",
        "Service & government",
        "Social impact",
        "Creative, arts & entertainment",
    ],
    "research": {
        "labs": [
            "Princeton Plasma Physics Laboratory (a U.S. DOE national laboratory)",
            "Princeton Neuroscience Institute",
            "Lewis-Sigler Institute for Integrative Genomics",
            "Andlinger Center for Energy and the Environment",
            "Princeton Materials Institute",
        ],
        "areas": [
            "Engineering & applied science",
            "Physical & quantitative sciences",
            "Life sciences & neuroscience",
            "Plasma physics & fusion energy",
            "Public & international affairs",
            "Economics & the social sciences",
            "Humanities",
        ],
        "lab_links": {
            "Princeton Plasma Physics Laboratory (a U.S. DOE national laboratory)": (
                "https://www.pppl.gov/"
            ),
            "Princeton Neuroscience Institute": "https://pni.princeton.edu/",
            "Lewis-Sigler Institute for Integrative Genomics": "https://lsi.princeton.edu/",
            "Andlinger Center for Energy and the Environment": (
                "https://andlinger.princeton.edu/"
            ),
            "Princeton Materials Institute": "https://materials.princeton.edu/",
        },
    },
    "campus_life": {
        # Princeton's teams (the Tigers) compete in NCAA Division I (Ivy League).
        "athletics_division": "NCAA Division I (Ivy League)",
        "mascot": "Princeton Tigers",
        "housing": "Residential-college system (six residential colleges)",
        "resources": [
            {"label": "Princeton Tigers Athletics", "url": "https://goprincetontigers.com/"},
            {"label": "Princeton Residential Colleges", "url": "https://collegelife.princeton.edu/"},
        ],
    },
    # Verified outdoor campus scenes — Wikimedia Commons API extmetadata (Artist +
    # LicenseShortName), landscape ≥1920px thumburl. Hero uses [0]; gallery lightbox
    # cycles the rest.
    "campus_photos": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/"
                "Nassau_Hall_Princeton.JPG/1920px-Nassau_Hall_Princeton.JPG"
            ),
            "credit": "Wikimedia Commons / Smallbones (CC0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/"
                "At_Princeton_University_2024_010.jpg/"
                "1920px-At_Princeton_University_2024_010.jpg"
            ),
            "credit": "Wikimedia Commons / Mike Peel (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/"
                "Blair_Arch%2C_Princeton%2C_New_Jersey.jpg/"
                "1920px-Blair_Arch%2C_Princeton%2C_New_Jersey.jpg"
            ),
            "credit": "Wikimedia Commons / Julian Lupyan (CC0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/"
                "Ivy_Covered_Building_in_the_Princeton_University_Campus%2C_New_Jersey.jpg/"
                "1920px-Ivy_Covered_Building_in_the_Princeton_University_Campus%2C_New_Jersey.jpg"
            ),
            "credit": "Wikimedia Commons / Julian Lupyan (CC0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/"
                "Campus_Club_Princeton_b.JPG/1920px-Campus_Club_Princeton_b.JPG"
            ),
            "credit": "Wikimedia Commons / Smallbones (CC0)",
        },
    ],
    "flagship": {
        # Princeton "Facts & Figures": 5,826 undergraduate + 3,280 graduate = 9,106 total.
        "enrollment_total": 9106,
        # Common Data Set 2024-25 first-year admissions cycle.
        "applicants": 40468,
        "admits": 1868,
        "admissions_cycle": "Entering class fall 2024 (Princeton Common Data Set 2024-25)",
        # Princeton "Facts & Figures": 54 Nobel laureates (faculty, staff and alumni).
        "nobel_laureates": 54,
        # Chartered in 1746 as the College of New Jersey; renamed Princeton University 1896.
        "founded_year": 1746,
    },
    "media_credit": "Wikimedia Commons / Smallbones (CC0)",
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Princeton, UNITID 186131)",
            "url": "https://collegescorecard.ed.gov/school/?186131",
        },
        {
            "label": "NCES College Navigator — Princeton University (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=186131",
        },
        {
            "label": "Princeton Office of Institutional Research — Common Data Set",
            "url": "https://ir.princeton.edu/other-university-data/common-data-set",
        },
        {
            "label": "Princeton University — Facts & Figures",
            "url": "https://www.princeton.edu/meet-princeton/facts-figures",
        },
        {
            "label": "Princeton — endowment reaches $36.4 billion (FY2025)",
            "url": "https://paw.princeton.edu/article/princeton-endowment-earns-11-return-reaches-364-billion",
        },
        {
            "label": "QS World University Rankings 2026 — Princeton University",
            "url": "https://www.topuniversities.com/universities/princeton-university",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — Princeton (joint #3)",
            "url": "https://www.timeshighereducation.com/world-university-rankings/princeton-university",
        },
        {
            "label": (
                "U.S. News — Princeton No. 1 in National Universities "
                "for the 15th year (2026)"
            ),
            "url": "https://njbiz.com/princeton-tops-us-news-2026-college-rankings/",
        },
        {
            "label": (
                "Princeton Office of the Dean of the Faculty — "
                "Chapter III, Academic Divisions"
            ),
            "url": (
                "https://dof.princeton.edu/rules-and-procedures-faculty-princeton-university-"
                "and-other-provisions-concern-faculty/chapter-iii-0"
            ),
        },
        {
            "label": "Princeton Center for Career Development — First-Destination Data",
            "url": "https://careerdevelopment.princeton.edu/exploring-options/next-steps/first-destination",
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it "Undergraduates");
# the total (9,106) lives in flagship.enrollment_total and renders as "Total enrollment".
# 5,826 = Princeton "Facts & Figures" undergraduate enrollment.
UNDERGRAD_COUNT = 5826

DESCRIPTION = (
    "Princeton University is a private research university in Princeton, NJ, chartered "
    "in 1746 as the College of New Jersey and renamed Princeton University in 1896. "
    "It is distinctively small for its stature — about 5,800 undergraduates and "
    "3,300 graduate students, some 9,100 in all — and pairs a deep commitment to "
    "undergraduate teaching with a 5:1 student-faculty ratio and 1,313 faculty.\n\n"
    "Princeton's faculty are organized into four academic divisions: the humanities, the "
    "social sciences, the natural sciences, and engineering and applied science. Two "
    "dean-led professional schools sit alongside them — the School of Engineering and "
    "Applied Science (founded 1921) and the School of Public and International Affairs "
    "(founded 1930) — and undergraduates earn the A.B. or the B.S.E. across 36 academic "
    "departments. The university manages the Princeton Plasma Physics Laboratory, a U.S. "
    "Department of Energy national laboratory, and is home to the Princeton Neuroscience "
    "Institute and the Lewis-Sigler Institute for Integrative Genomics.\n\n"
    "Princeton ranks among the very best universities in the world: No. 1 among national "
    "universities by U.S. News for the 15th consecutive year, a joint No. 3 in the world "
    "by Times Higher Education (its best-ever finish), and No. 25 by QS. Fifty-four Nobel "
    "laureates are associated with the university, and it admits about 5% of first-year "
    "applicants.\n\n"
    "Princeton is need-blind and meets 100% of demonstrated financial need with grants "
    "rather than loans: the average net price is roughly $6,100 a year, 20% of "
    "undergraduates receive Pell grants, and only 2% take federal student loans. "
    "Princeton graduates earn a median income of about $110,000 a decade after entry."
)

# ── The real degree-granting academic units (display order) ─────────────────
_SEAS = "School of Engineering and Applied Science"
_SPIA = "Princeton School of Public and International Affairs"
_HUM = "The Humanities"
_SOC = "The Social Sciences"
_NAT = "The Natural Sciences"

SCHOOLS: list[dict] = [
    {
        "name": _SEAS,
        "sort_order": 1,
        "description": (
            "Founded in 1921, Princeton's School of Engineering and Applied Science "
            "(Division IV) educates and conducts research across six departments: "
            "chemical and biological engineering; civil and environmental engineering; "
            "computer science; electrical and computer engineering; mechanical and "
            "aerospace engineering; and operations research and financial engineering. "
            "Its B.S.E. degree is paired with interdisciplinary centers in energy, "
            "bioengineering, materials, quantum science and technology policy."
        ),
    },
    {
        "name": _SPIA,
        "sort_order": 2,
        "description": (
            "Launched in 1930 (and renamed the Princeton School of Public and "
            "International Affairs in 2020), SPIA is Princeton's multidisciplinary "
            "school for public service, spanning an undergraduate A.B. in public and "
            "international affairs and graduate degrees including the Master in Public "
            "Affairs. It fully funds all of its MPA, MPP and PhD students."
        ),
    },
    {
        "name": _HUM,
        "sort_order": 3,
        "description": (
            "Division I of Princeton's faculty, the humanities span the departments and "
            "programs in literature, languages, history of art, music, philosophy, "
            "religion and the classical and modern world. (Per the Office of the Dean of "
            "the Faculty, the divisions group departments for faculty representation and "
            "are not administrative units.)"
        ),
    },
    {
        "name": _SOC,
        "sort_order": 4,
        "description": (
            "Division II of Princeton's faculty, the social sciences span anthropology, "
            "economics, history, politics, sociology and the School of Public and "
            "International Affairs — studying human behavior, institutions and society "
            "with both quantitative and interpretive methods."
        ),
    },
    {
        "name": _NAT,
        "sort_order": 5,
        "description": (
            "Division III of Princeton's faculty, the natural sciences span astrophysical "
            "sciences, chemistry, ecology and evolutionary biology, geosciences, "
            "mathematics, molecular biology, neuroscience, physics and psychology — "
            "anchored by institutes such as the Princeton Neuroscience Institute and the "
            "Lewis-Sigler Institute for Integrative Genomics."
        ),
    },
]

# Each unit's official website (verified to resolve at author time). The divisions have
# no standalone site; they point to Princeton's official academics / areas-of-study page.
_ACADEMICS_URL = "https://www.princeton.edu/academics"
_SCHOOL_WEBSITE: dict[str, str] = {
    _SEAS: "https://engineering.princeton.edu/",
    _SPIA: "https://spia.princeton.edu/",
    _HUM: _ACADEMICS_URL,
    _SOC: _ACADEMICS_URL,
    _NAT: _ACADEMICS_URL,
}

# Rich, sourced About-tab content per unit. Deans + titles are quoted from each school's
# official leadership page (verified 2026-06-10). Founding years are included only where
# an official page states one (SEAS 1921; SPIA 1930). Notable-faculty rosters are not
# published uniformly per unit and are omitted rather than hand-picked without an
# official list (recorded in _ABOUT_OMITTED). The three faculty divisions have no dean
# or founding date (they are non-administrative groupings per the Dean of the Faculty),
# so those fields are honestly omitted; verified research institutes are included.
_ABOUT_DETAIL: dict[str, dict] = {
    _SEAS: {
        "founded": 1921,
        "leadership": (
            "Andrew Houck — Dean (Anthony H.P. Lee '79 Professor of Electrical and "
            "Computer Engineering)"
        ),
        "research_centers": [
            "Andlinger Center for Energy and the Environment",
            "Center for Information Technology Policy",
            "Keller Center for Innovation in Engineering Education",
            "Princeton Materials Institute",
            "Omenn-Darling Bioengineering Institute",
            "Princeton Quantum Initiative",
        ],
        "source": {
            "label": "Princeton Engineering — About",
            "url": "https://engineering.princeton.edu/about",
        },
    },
    _SPIA: {
        "founded": 1930,
        "leadership": (
            "Amaney A. Jamal — Dean (Edwards S. Sanford Professor of Politics)"
        ),
        "research_centers": [
            "Center for the Study of Democratic Politics",
            "Bendheim-Thoman Center for Research on Child Wellbeing",
            "Center for Health and Wellbeing",
            "Center for International Security Studies",
        ],
        "source": {
            "label": "Princeton SPIA — Leadership",
            "url": "https://spia.princeton.edu/about/leadership",
        },
    },
    _HUM: {
        "research_centers": [
            "Humanities Council (Council of the Humanities)",
            "Center for Digital Humanities",
            "University Center for Human Values",
        ],
        "source": {
            "label": "Princeton — Academics (Areas of Study)",
            "url": _ACADEMICS_URL,
        },
    },
    _SOC: {
        "research_centers": [
            "Office of Population Research",
            "Industrial Relations Section (Economics)",
            "Center for the Study of Religion",
        ],
        "source": {
            "label": "Princeton — Academics (Areas of Study)",
            "url": _ACADEMICS_URL,
        },
    },
    _NAT: {
        "research_centers": [
            "Princeton Neuroscience Institute",
            "Lewis-Sigler Institute for Integrative Genomics",
            "Princeton Plasma Physics Laboratory",
        ],
        "source": {
            "label": "Princeton — Academics (Areas of Study)",
            "url": _ACADEMICS_URL,
        },
    },
}

# About-detail fields omitted per unit (verified-unavailable), recorded in each unit's
# _standard.omitted. Faculty rosters omitted for every unit; the three faculty divisions
# additionally omit founded + leadership (they have no dean or founding date).
_DIVISION_OMITTED = ["about_detail.founded", "about_detail.leadership", "about_detail.faculty"]
_ABOUT_OMITTED: dict[str, list[str]] = {
    _SEAS: ["about_detail.faculty"],
    _SPIA: ["about_detail.faculty"],
    _HUM: _DIVISION_OMITTED,
    _SOC: _DIVISION_OMITTED,
    _NAT: _DIVISION_OMITTED,
}

# ── Channel feeds + official social links ──────────────────────────────────
# The daily content-ingest reads ``news_rss`` (RSS), ``events_feed`` (iCalendar or RSS),
# and ``keywords`` (filter gate). Without a real ``news_rss`` a node's Events & Updates
# tab is empty — so every school and program below carries a feed.
_PRINCETON_NEWS_RSS = "https://www.princeton.edu/feed"
_PRINCETON_EVENTS_RSS = {"url": "https://www.princeton.edu/feed/events", "type": "rss"}
_SOCIAL_PRINCETON = {
    "instagram": "https://www.instagram.com/princeton/",
    "linkedin": "https://www.linkedin.com/school/princeton-university/",
    "x": "https://x.com/Princeton",
    "youtube": "https://www.youtube.com/princetonuniversity",
    "facebook": "https://www.facebook.com/princetonu",
}

_INSTITUTION_CONTENT: dict = {
    "news_rss": _PRINCETON_NEWS_RSS,
    "news_url": "https://www.princeton.edu/news",
    "news_curated": False,
    "events_feed": dict(_PRINCETON_EVENTS_RSS),
    "social": dict(_SOCIAL_PRINCETON),
}

_SCHOOL_FEED_SPEC: dict[str, dict] = {
    _SEAS: {"keywords": ["engineering", "SEAS", "computer science", "B.S.E.", "robotics"]},
    _SPIA: {
        "keywords": ["SPIA", "public affairs", "public policy", "international affairs", "MPA"]
    },
    _HUM: {
        "keywords": ["humanities", "English", "philosophy", "classics", "literature", "history"]
    },
    _SOC: {
        "keywords": [
            "social sciences",
            "economics",
            "politics",
            "sociology",
            "anthropology",
            "history",
        ]
    },
    _NAT: {
        "keywords": [
            "natural sciences",
            "physics",
            "chemistry",
            "biology",
            "mathematics",
            "neuroscience",
        ]
    },
}

_KW_STOP = {"and", "of", "the", "in", "for", "with", "science", "sciences", "engineering"}


def _school_content(name: str) -> dict:
    """A school's content_sources: Princeton News RSS + public events filtered by keywords."""
    spec = _SCHOOL_FEED_SPEC[name]
    return {
        "news_rss": _PRINCETON_NEWS_RSS,
        "news_url": _SCHOOL_WEBSITE.get(name, "https://www.princeton.edu"),
        "news_curated": False,
        "events_feed": dict(_PRINCETON_EVENTS_RSS),
        "keywords": list(spec["keywords"]),
        "social": dict(_SOCIAL_PRINCETON),
    }


def _program_keywords(spec: dict) -> list[str]:
    school_kw = list(_SCHOOL_FEED_SPEC[spec["school"]]["keywords"])
    name = spec["program_name"].replace("&", " ").replace("/", " ")
    terms = [w for w in name.split() if len(w) > 3 and w.lower() not in _KW_STOP]
    program_term = " ".join(terms[:3]).strip()
    return ([program_term] if program_term else []) + school_kw


def _program_content(spec: dict) -> dict:
    base = _school_content(spec["school"])
    base["keywords"] = _program_keywords(spec)
    return base


# Computer Science keyword-relevant feed (the flagship program) — department news + shared feeds.
_CS_CONTENT: dict = {
    "news_rss": _PRINCETON_NEWS_RSS,
    "news_url": "https://www.cs.princeton.edu/news",
    "news_curated": False,
    "events_feed": dict(_PRINCETON_EVENTS_RSS),
    "keywords": ["computer science", "princeton cs", "machine learning", "princeton engineering"],
    "social": dict(_SOCIAL_PRINCETON),
}

# ── The program catalog (real majors, organized by academic unit) ──────────
# slug = idempotency key. Every program is mapped to its owning unit from Princeton's
# official department structure (Dean of the Faculty divisions). The program set is the
# complete College Scorecard Field-of-Study list for UNITID 186131 (the deterministic
# federal view). Princeton awards the A.B. and the B.S.E.; the platform models the
# undergraduate degrees with the generic ``bachelors`` type and the SPIA MPA as
# ``masters``.
PROGRAMS: list[dict] = [
    # ── School of Engineering and Applied Science (Division IV) ──
    {
        "slug": "princeton-computer-science-bs",
        "school": _SEAS,
        "program_name": "Computer Science",
        "degree_type": "bachelors",
        "cip": "11.07",
        "duration_months": 48,
        "description": (
            "Princeton's flagship and largest major — computer science, offered as both "
            "the A.B. and the B.S.E., spanning theory, systems, AI and machine learning."
        ),
    },
    {
        "slug": "princeton-operations-research-bs",
        "school": _SEAS,
        "program_name": "Operations Research and Financial Engineering",
        "degree_type": "bachelors",
        "cip": "14.37",
        "duration_months": 48,
        "description": (
            "Operations research and financial engineering — optimization, probability, "
            "statistics and financial mathematics."
        ),
    },
    {
        "slug": "princeton-mechanical-engineering-bs",
        "school": _SEAS,
        "program_name": "Mechanical and Aerospace Engineering",
        "degree_type": "bachelors",
        "cip": "14.19",
        "duration_months": 48,
        "description": "Mechanical and aerospace engineering — mechanics, design and propulsion.",
    },
    {
        "slug": "princeton-electrical-engineering-bs",
        "school": _SEAS,
        "program_name": "Electrical and Computer Engineering",
        "degree_type": "bachelors",
        "cip": "14.10",
        "duration_months": 48,
        "description": "Electrical and computer engineering — circuits, devices and systems.",
    },
    {
        "slug": "princeton-civil-engineering-bs",
        "school": _SEAS,
        "program_name": "Civil and Environmental Engineering",
        "degree_type": "bachelors",
        "cip": "14.08",
        "duration_months": 48,
        "description": (
            "Civil and environmental engineering — structures, mechanics and environment."
        ),
    },
    {
        "slug": "princeton-chemical-engineering-bs",
        "school": _SEAS,
        "program_name": "Chemical and Biological Engineering",
        "degree_type": "bachelors",
        "cip": "14.07",
        "duration_months": 48,
        "description": "Chemical and biological engineering — reaction engineering and design.",
    },
    # ── Princeton School of Public and International Affairs ──
    {
        "slug": "princeton-public-affairs-ab",
        "school": _SPIA,
        "program_name": "Public and International Affairs",
        "degree_type": "bachelors",
        "cip": "44.05",
        "duration_months": 48,
        "description": (
            "The undergraduate A.B. in public and international affairs — policy analysis "
            "grounded in the social sciences, with policy research seminars and task forces."
        ),
    },
    {
        "slug": "princeton-public-affairs-mpa",
        "school": _SPIA,
        "program_name": "Master in Public Affairs (MPA)",
        "degree_type": "masters",
        "cip": "44.05",
        "duration_months": 24,
        "description": (
            "The two-year Master in Public Affairs — a fully-funded graduate degree in "
            "policy analysis and leadership for public service."
        ),
    },
    # ── The Humanities (Division I) ──
    {
        "slug": "princeton-english-bs",
        "school": _HUM,
        "program_name": "English",
        "degree_type": "bachelors",
        "cip": "23.01",
        "duration_months": 48,
        "description": "English — literature in English, criticism and creative writing.",
    },
    {
        "slug": "princeton-philosophy-bs",
        "school": _HUM,
        "program_name": "Philosophy",
        "degree_type": "bachelors",
        "cip": "38.01",
        "duration_months": 48,
        "description": "Philosophy — logic, ethics, metaphysics and the history of philosophy.",
    },
    # ── The Social Sciences (Division II) ──
    {
        "slug": "princeton-economics-bs",
        "school": _SOC,
        "program_name": "Economics",
        "degree_type": "bachelors",
        "cip": "45.06",
        "duration_months": 48,
        "description": "Economics — micro, macro and econometrics.",
    },
    {
        "slug": "princeton-politics-bs",
        "school": _SOC,
        "program_name": "Politics",
        "degree_type": "bachelors",
        "cip": "45.10",
        "duration_months": 48,
        "description": (
            "Politics — American, comparative and international politics and political theory."
        ),
    },
    {
        "slug": "princeton-sociology-bs",
        "school": _SOC,
        "program_name": "Sociology",
        "degree_type": "bachelors",
        "cip": "45.11",
        "duration_months": 48,
        "description": "Sociology — social structure, inequality and institutions.",
    },
    {
        "slug": "princeton-anthropology-bs",
        "school": _SOC,
        "program_name": "Anthropology",
        "degree_type": "bachelors",
        "cip": "45.02",
        "duration_months": 48,
        "description": "Anthropology — the comparative study of human societies and cultures.",
    },
    {
        "slug": "princeton-history-bs",
        "school": _SOC,
        "program_name": "History",
        "degree_type": "bachelors",
        "cip": "54.01",
        "duration_months": 48,
        "description": "History — the study of the human past across periods and regions.",
    },
    # ── The Natural Sciences (Division III) ──
    {
        "slug": "princeton-molecular-biology-bs",
        "school": _NAT,
        "program_name": "Molecular Biology",
        "degree_type": "bachelors",
        "cip": "26.02",
        "duration_months": 48,
        "description": "Molecular biology — biochemistry, biophysics, genetics and cell biology.",
    },
    {
        "slug": "princeton-psychology-bs",
        "school": _NAT,
        "program_name": "Psychology",
        "degree_type": "bachelors",
        "cip": "42.27",
        "duration_months": 48,
        "description": "Psychology — cognitive, developmental, social and systems neuroscience.",
    },
    {
        "slug": "princeton-mathematics-bs",
        "school": _NAT,
        "program_name": "Mathematics",
        "degree_type": "bachelors",
        "cip": "27.01",
        "duration_months": 48,
        "description": "Mathematics — analysis, algebra, geometry and number theory.",
    },
    {
        "slug": "princeton-eeb-bs",
        "school": _NAT,
        "program_name": "Ecology and Evolutionary Biology",
        "degree_type": "bachelors",
        "cip": "26.13",
        "duration_months": 48,
        "description": "Ecology and evolutionary biology — organisms, populations and ecosystems.",
    },
    {
        "slug": "princeton-physics-bs",
        "school": _NAT,
        "program_name": "Physics",
        "degree_type": "bachelors",
        "cip": "40.08",
        "duration_months": 48,
        "description": "Physics — from particles and fields to condensed matter and biophysics.",
    },
    {
        "slug": "princeton-chemistry-bs",
        "school": _NAT,
        "program_name": "Chemistry",
        "degree_type": "bachelors",
        "cip": "40.05",
        "duration_months": 48,
        "description": "Chemistry — organic, inorganic, physical and chemical biology.",
    },
    {
        "slug": "princeton-neuroscience-bs",
        "school": _NAT,
        "program_name": "Neuroscience",
        "degree_type": "bachelors",
        "cip": "26.15",
        "duration_months": 48,
        "description": "Neuroscience — the molecular, cellular and systems study of the brain.",
    },
]

# Explicit flagship programs — credential-disambiguated names + real departments.
_EXPLICIT_DEPARTMENTS: dict[str, str] = {
    "princeton-computer-science-bs": "Computer Science",
    "princeton-operations-research-bs": "Operations Research and Financial Engineering",
    "princeton-mechanical-engineering-bs": "Mechanical and Aerospace Engineering",
    "princeton-electrical-engineering-bs": "Electrical and Computer Engineering",
    "princeton-civil-engineering-bs": "Civil and Environmental Engineering",
    "princeton-chemical-engineering-bs": "Chemical and Biological Engineering",
    "princeton-public-affairs-ab": "Public and International Affairs",
    "princeton-public-affairs-mpa": "Princeton School of Public and International Affairs",
    "princeton-english-bs": "English",
    "princeton-philosophy-bs": "Philosophy",
    "princeton-economics-bs": "Economics",
    "princeton-politics-bs": "Politics",
    "princeton-sociology-bs": "Sociology",
    "princeton-anthropology-bs": "Anthropology",
    "princeton-history-bs": "History",
    "princeton-molecular-biology-bs": "Molecular Biology",
    "princeton-psychology-bs": "Psychology",
    "princeton-mathematics-bs": "Mathematics",
    "princeton-eeb-bs": "Ecology and Evolutionary Biology",
    "princeton-physics-bs": "Physics",
    "princeton-chemistry-bs": "Chemistry",
    "princeton-neuroscience-bs": "Neuroscience",
    "princeton-architecture-bs": "School of Architecture",
    "princeton-architecture-ms": "School of Architecture",
    "princeton-chemical-engineering-ms": "Chemical and Biological Engineering",
    "princeton-civil-engineering-ms": "Civil and Environmental Engineering",
    "princeton-electrical-electronics-and-communications-engineering-ms": (
        "Electrical and Computer Engineering"
    ),
    "princeton-mechanical-engineering-ms": "Mechanical and Aerospace Engineering",
}
_EXPLICIT_FULL_NAMES: dict[str, str] = {
    "princeton-computer-science-bs": "Bachelor of Science in Computer Science",
    "princeton-operations-research-bs": (
        "Bachelor of Science in Engineering in Operations Research and Financial Engineering"
    ),
    "princeton-mechanical-engineering-bs": (
        "Bachelor of Science in Engineering in Mechanical and Aerospace Engineering"
    ),
    "princeton-electrical-engineering-bs": (
        "Bachelor of Science in Engineering in Electrical and Computer Engineering"
    ),
    "princeton-civil-engineering-bs": (
        "Bachelor of Science in Engineering in Civil and Environmental Engineering"
    ),
    "princeton-chemical-engineering-bs": (
        "Bachelor of Science in Engineering in Chemical and Biological Engineering"
    ),
    "princeton-public-affairs-ab": "Bachelor of Arts in Public and International Affairs",
    "princeton-english-bs": "Bachelor of Arts in English",
    "princeton-philosophy-bs": "Bachelor of Arts in Philosophy",
    "princeton-economics-bs": "Bachelor of Arts in Economics",
    "princeton-politics-bs": "Bachelor of Arts in Politics",
    "princeton-sociology-bs": "Bachelor of Arts in Sociology",
    "princeton-anthropology-bs": "Bachelor of Arts in Anthropology",
    "princeton-history-bs": "Bachelor of Arts in History",
    "princeton-molecular-biology-bs": "Bachelor of Arts in Molecular Biology",
    "princeton-psychology-bs": "Bachelor of Arts in Psychology",
    "princeton-mathematics-bs": "Bachelor of Arts in Mathematics",
    "princeton-eeb-bs": "Bachelor of Arts in Ecology and Evolutionary Biology",
    "princeton-physics-bs": "Bachelor of Science in Physics",
    "princeton-chemistry-bs": "Bachelor of Arts in Chemistry",
    "princeton-neuroscience-bs": "Bachelor of Arts in Neuroscience",
    "princeton-architecture-bs": "Bachelor of Arts in Architecture",
    "princeton-architecture-ms": "Master of Architecture (M.Arch.)",
    "princeton-chemical-engineering-ms": (
        "Master of Science in Engineering in Chemical and Biological Engineering"
    ),
    "princeton-civil-engineering-ms": (
        "Master of Science in Engineering in Civil and Environmental Engineering"
    ),
    "princeton-electrical-electronics-and-communications-engineering-ms": (
        "Master of Engineering in Electrical and Computer Engineering"
    ),
    "princeton-mechanical-engineering-ms": (
        "Master of Science in Engineering in Mechanical and Aerospace Engineering"
    ),
}
for _p in PROGRAMS:
    if _p["slug"] in _EXPLICIT_DEPARTMENTS:
        _p["department"] = _EXPLICIT_DEPARTMENTS[_p["slug"]]
    if _p["slug"] in _EXPLICIT_FULL_NAMES:
        _p["program_name"] = _EXPLICIT_FULL_NAMES[_p["slug"]]

_EXISTING_SLUGS = {p["slug"] for p in PROGRAMS}
_EXISTING_CIP_KEYS = {(p.get("cip"), p["degree_type"]) for p in PROGRAMS if p.get("cip")}


# Federal CIP field titles → Princeton's published department / program names.
_CIP_TO_DEPARTMENT: dict[str, str] = {
    "Political Science and Government": "Politics",
    "Research and Experimental Psychology": "Psychology",
    "Biochemistry, Biophysics and Molecular Biology": "Molecular Biology",
    "Ecology, Evolution, Systematics, and Population Biology": "Ecology and Evolutionary Biology",
    "Neurobiology and Neurosciences": "Neuroscience",
    "Geological and Earth Sciences/Geosciences": "Geosciences",
    "Public Policy Analysis": "Public and International Affairs",
    "Electrical, Electronics, and Communications Engineering": (
        "Electrical and Computer Engineering"
    ),
    "Mechanical Engineering": "Mechanical and Aerospace Engineering",
    "Operations Research": "Operations Research and Financial Engineering",
    "Computer Engineering": "Electrical and Computer Engineering",
    "English Language and Literature, General": "English",
    "Fine and Studio Arts": "Art and Archaeology",
    "Architectural Sciences and Technology": "Architecture",
}


def _department_for(field_name: str, school: str) -> str:
    """Owning department — map federal CIP titles to Princeton's published names."""
    mapped = _CIP_TO_DEPARTMENT.get(field_name, field_name)
    if mapped.lower() in school.lower() or school.lower() in mapped.lower():
        return school
    return mapped


def _delivery_format(raw: str) -> str:
    if raw == "in_person":
        return "on_campus"
    return raw


def _field_from_program_name(program_name: str) -> str | None:
    for prefix in (
        "Bachelor of Science in Engineering in ",
        "Bachelor of Arts in ",
        "Master of Science in Engineering in ",
        "Master of Engineering in ",
        "Master of Architecture (M.Arch.)",
        "Master in Public Affairs (MPA)",
        "Bachelor's in ",
        "Master's in ",
    ):
        if program_name.startswith(prefix):
            return program_name[len(prefix):]
    return None


def _needs_normalize(desc: str, program_name: str = "") -> bool:
    if not desc:
        return True
    if program_name and desc.startswith(program_name):
        return True
    if _CLASSIFICATION_STUB_RE.match(desc):
        return True
    if _TEMPLATE_STUB_RE.search(desc):
        return True
    return "offered through the " in desc


def _princeton_program_name(
    field_name: str, degree_type: str, school: str, slug: str
) -> str:
    """Real Princeton degree designation — never a CIP-rollup credential prefix."""
    dept = _department_for(field_name, school)
    if degree_type == "bachelors":
        if school == _SEAS:
            return f"Bachelor of Science in Engineering in {dept}"
        return f"Bachelor of Arts in {dept}"
    if degree_type == "masters":
        if slug == "princeton-architecture-ms":
            return "Master of Architecture (M.Arch.)"
        if slug == "princeton-public-affairs-mpa":
            return "Master in Public Affairs (MPA)"
        if slug == "princeton-electrical-electronics-and-communications-engineering-ms":
            return f"Master of Engineering in {dept}"
        if school == _SEAS:
            return f"Master of Science in Engineering in {dept}"
    return dept


def _princeton_description(spec: dict, field: str | None = None) -> str:
    """Field-specific description — never the degree-type classification stub."""
    slug = spec["slug"]
    fmt = spec.get("delivery_format", "on_campus")
    delivery = ""
    if fmt == "online":
        delivery = " Delivered online."
    elif fmt == "hybrid":
        delivery = " Delivered in a hybrid format."
    if slug in SLUG_DESCRIPTIONS:
        return f"{SLUG_DESCRIPTIONS[slug]}{delivery}"
    field_key = (
        field
        or spec.get("_field_name")
        or _SLUG_TO_FIELD.get(slug)
        or _field_from_program_name(spec.get("program_name", ""))
        or spec.get("department")
        or spec.get("program_name", "")
    )
    if field_key in FIELD_ALIASES:
        field_key = FIELD_ALIASES[field_key]
    clause = FIELD_DESCRIPTIONS.get(field_key)
    if not clause:
        raise ValueError(
            f"Missing FIELD_DESCRIPTIONS entry for {field_key!r} ({slug})"
        )
    # Open on the field fact — never restate program_name (already the page heading).
    return f"{clause}{delivery}"


def _normalize_program(spec: dict, field_name: str | None = None) -> None:
    """Stamp a field-specific description on stub program nodes."""
    if not _needs_normalize(spec.get("description") or "", spec.get("program_name", "")):
        return
    spec["description"] = _princeton_description(spec, field=field_name)


def _build_catalog() -> list[dict]:
    """Append breadth-first program nodes from the IPEDS Field-of-Study catalog."""
    out: list[dict] = []
    seen = set(_EXISTING_SLUGS)
    for slug, school, field_name, dtype, cip, dur, fmt, _legacy in _IPEDS_CATALOG:
        if slug in seen:
            continue
        if (cip, dtype) in _EXISTING_CIP_KEYS:
            continue
        # Princeton does not publish standalone graduate certificates; incidental M.A.
        # degrees along the Ph.D. path are not separate application programs.
        if dtype == "certificate":
            continue
        if dtype == "masters" and slug not in _IPEDS_MASTERS_ALLOWLIST:
            continue
        seen.add(slug)
        dept = _department_for(field_name, school)
        delivery = _delivery_format(fmt)
        pname = _princeton_program_name(field_name, dtype, school, slug)
        spec = {
            "slug": slug,
            "school": school,
            "program_name": pname,
            "degree_type": dtype,
            "department": dept,
            "cip": cip,
            "duration_months": dur,
            "delivery_format": delivery,
            "_field_name": field_name,
        }
        _normalize_program(spec, field_name)
        spec.pop("_field_name", None)
        out.append(spec)
    return out


PROGRAMS += _build_catalog()

for _p in PROGRAMS:
    if _p["slug"] in _EXPLICIT_DEPARTMENTS:
        _p["department"] = _EXPLICIT_DEPARTMENTS[_p["slug"]]
    if _p["slug"] in _EXPLICIT_FULL_NAMES:
        _p["program_name"] = _EXPLICIT_FULL_NAMES[_p["slug"]]
    _normalize_program(_p)

_catalog_errors = validate_catalog(PROGRAMS)
_classification_stubs = sum(
    1 for p in PROGRAMS if _CLASSIFICATION_STUB_RE.match(p.get("description") or "")
)
if _classification_stubs:
    _catalog_errors.append(
        f"classification-only descriptions on {_classification_stubs} programs"
    )
_name_prefix_desc = sum(
    1
    for p in PROGRAMS
    if (p.get("description") or "").startswith(p.get("program_name", ""))
)
if _name_prefix_desc:
    _catalog_errors.append(
        f"name-prefixed descriptions on {_name_prefix_desc} programs"
    )
_prefix_names = sum(1 for p in PROGRAMS if _PREFIX_NAME_RE.match(p.get("program_name", "")))
if _prefix_names:
    _catalog_errors.append(f"CIP-prefix program_name on {_prefix_names} programs")
if _catalog_errors:
    raise RuntimeError(f"Princeton catalog quality gate failed: {_catalog_errors}")

for _p in PROGRAMS:
    _p.setdefault("delivery_format", "on_campus")

for _p in PROGRAMS:
    _p.setdefault("delivery_format", "in_person")

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

# Full official program names (program-page title); equal to the major name here.
_FULL_NAME_BY_SLUG: dict[str, str] = {p["slug"]: p["program_name"] for p in PROGRAMS}

# Official program/department home pages. The flagship CS major has its own verified
# department page; the others use their owning unit's official site.
_WEBSITE_BY_SLUG: dict[str, str] = {
    "princeton-computer-science-bs": "https://www.cs.princeton.edu/",
    "princeton-operations-research-bs": "https://orfe.princeton.edu/",
    "princeton-mechanical-engineering-bs": "https://mae.princeton.edu/",
    "princeton-electrical-engineering-bs": "https://ece.princeton.edu/",
    "princeton-civil-engineering-bs": "https://cee.princeton.edu/",
    "princeton-chemical-engineering-bs": "https://cbe.princeton.edu/",
    "princeton-public-affairs-ab": "https://spia.princeton.edu/undergraduate-program",
    "princeton-public-affairs-mpa": "https://spia.princeton.edu/graduate-admissions/master-public-affairs",
    "princeton-english-bs": "https://english.princeton.edu/",
    "princeton-philosophy-bs": "https://philosophy.princeton.edu/",
    "princeton-economics-bs": "https://economics.princeton.edu/",
    "princeton-politics-bs": "https://politics.princeton.edu/",
    "princeton-sociology-bs": "https://sociology.princeton.edu/",
    "princeton-anthropology-bs": "https://anthropology.princeton.edu/",
    "princeton-history-bs": "https://history.princeton.edu/",
    "princeton-molecular-biology-bs": "https://molbio.princeton.edu/",
    "princeton-psychology-bs": "https://psych.princeton.edu/",
    "princeton-mathematics-bs": "https://www.math.princeton.edu/",
    "princeton-eeb-bs": "https://eeb.princeton.edu/",
    "princeton-physics-bs": "https://phy.princeton.edu/",
    "princeton-chemistry-bs": "https://chemistry.princeton.edu/",
    "princeton-neuroscience-bs": "https://pni.princeton.edu/",
    "princeton-architecture-bs": "https://soa.princeton.edu/undergraduate",
    "princeton-architecture-ms": (
        "https://soa.princeton.edu/school/professional-master-architecture-program"
    ),
    "princeton-chemical-engineering-ms": "https://cbe.princeton.edu/graduate",
    "princeton-civil-engineering-ms": "https://cee.princeton.edu/graduate",
    "princeton-electrical-electronics-and-communications-engineering-ms": (
        "https://ece.princeton.edu/academics/graduate"
    ),
    "princeton-mechanical-engineering-ms": "https://mae.princeton.edu/graduate",
}

# ── Who-it's-for + highlights (catalog baselines) ──────────────────────────
_WHO_BASELINE = (
    "Academically exceptional students seeking a research-rich education at a university "
    "uniquely devoted to undergraduate teaching, with full-need financial aid met by grants."
)
_HL_BASELINE = ["Ivy League", "5:1 student-faculty ratio", "Need-met-with-grants aid"]
_WHO_BY_SLUG = {
    "princeton-computer-science-bs": (
        "Technically exceptional students who want a rigorous computer science education "
        "— offered as the A.B. or the B.S.E. — with deep access to a leading CS faculty "
        "and its research."
    ),
    "princeton-public-affairs-mpa": (
        "Aspiring public-service leaders seeking a fully-funded, two-year policy degree "
        "grounded in the social sciences."
    ),
}
_HL_BY_SLUG = {
    "princeton-computer-science-bs": [
        "Flagship & largest major",
        "13 research areas",
        "Turing Award winner on faculty",
    ],
    "princeton-public-affairs-mpa": [
        "Fully funded (tuition + stipend)",
        "Two-year MPA",
        "Policy research seminars",
    ],
}

# ── Curriculum / research areas, where published (the flagship) ────────────
# Princeton CS publishes 13 official research areas; quoted from the department's
# official Research Areas page.
_TRACKS_BY_SLUG: dict[str, dict] = {
    "princeton-computer-science-bs": {
        "label": "Computer science research areas",
        "note": (
            "Computer science is offered as both the A.B. and the B.S.E.; after a shared "
            "programming, theory and systems core, students pursue upper-level coursework "
            "across the department's thirteen official research areas."
        ),
        "items": [
            {"name": "Theory"},
            {"name": "Systems & Networking"},
            {"name": "Machine Learning"},
            {"name": "Natural Language Processing"},
            {"name": "Vision & Graphics"},
            {"name": "Security & Privacy"},
            {"name": "Programming Languages & Compilers"},
            {"name": "Computer Architecture"},
            {"name": "Computational Biology"},
            {"name": "Human-Computer Interaction"},
            {"name": "Robotics"},
            {"name": "Economics & Computation"},
            {"name": "Law & Public Policy"},
        ],
        "source": "Princeton Computer Science — Research Areas",
        "source_url": "https://www.cs.princeton.edu/research/areas",
    },
}

# ── Program-specific cost ──────────────────────────────────────────────────
# Princeton undergraduate cost (College Scorecard, UNITID 186131). The SPIA MPA is
# fully funded (handled per-slug below).
_TUITION_UG = 62688
_UNDERGRAD_COA = 84040
_AVG_NET_PRICE = 6128
# Graduate full-time tuition 2024-25 (Princeton Graduate School rates).
_TUITION_GRAD = 65210
_COST_BY_SLUG: dict[str, dict] = {
    "princeton-public-affairs-mpa": {
        "tuition_usd": _TUITION_GRAD,
        "total_cost_of_attendance": _TUITION_GRAD,
        "funded": True,
        "note": (
            "Princeton SPIA fully funds all admitted MPA students — 100% of tuition and "
            "required fees (including health insurance) plus a need-based living stipend "
            "for the two years of the program. Published full-time graduate tuition shown."
        ),
        "source": "Princeton SPIA — MPA Financial Aid",
        "source_url": "https://spia.princeton.edu/graduate-admissions/master-public-affairs/financial-aid",
        "year": "2024-25",
    }
}

# ── Program-specific outcomes (College Scorecard Field of Study, by CIP) ────
# Where the federal College Scorecard publishes a Field-of-Study median earnings (one
# year after completion) for an awarded CIP at UNITID 186131, we use it (program scope).
# Programs whose CIP earnings are suppressed fall back to the institution 10-year median.
# Tuples are (median_earnings_1yr, cip).
_FOS_OUTCOMES: dict[str, tuple[int, str]] = {
    "princeton-computer-science-bs": (146624, "11.07"),
    "princeton-operations-research-bs": (100354, "14.37"),
    "princeton-mechanical-engineering-bs": (85328, "14.19"),
    "princeton-public-affairs-ab": (73630, "44.05"),
    "princeton-public-affairs-mpa": (85111, "44.05"),
    "princeton-economics-bs": (103041, "45.06"),
    "princeton-politics-bs": (63317, "45.10"),
    "princeton-sociology-bs": (32914, "45.11"),
    "princeton-history-bs": (45363, "54.01"),
    "princeton-english-bs": (35178, "23.01"),
    "princeton-molecular-biology-bs": (41848, "26.02"),
    "princeton-psychology-bs": (47050, "42.27"),
    "princeton-eeb-bs": (53038, "26.13"),
    "princeton-neuroscience-bs": (32647, "26.15"),
}

# Verbatim methodology for the program-scope Scorecard FOS earnings figure.
_FOS_CONDITIONS = (
    "Median earnings of graduates who received federal financial aid, measured "
    "approximately one year after program completion; reported by the U.S. Department of "
    "Education College Scorecard Field of Study by 4-digit CIP code. Programs with too "
    "few completers are suppressed."
)

# Institution-wide outcomes fallback (College Scorecard, UNITID 186131), used for degree
# programs whose program-level one-year earnings are suppressed.
_OUTCOMES_INSTITUTION = {
    "median_salary": 110066,
    "scope": "institution",
    "conditions": (
        "Princeton institution-wide median earnings ten years after entry (College "
        "Scorecard, UNITID 186131); a program-level one-year earnings figure is not "
        "published (suppressed) for this field of study."
    ),
    "source": "U.S. Dept. of Education College Scorecard (UNITID 186131)",
    "source_url": "https://collegescorecard.ed.gov/school/?186131",
}

# Annual degrees conferred per CIP (College Scorecard Field of Study), used for the
# flagship class-profile cohort figure.
_AWARDS_BY_SLUG: dict[str, int] = {"princeton-computer-science-bs": 201}

# ── Class profile, where published (the flagship) ──────────────────────────
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    "princeton-computer-science-bs": {
        "cohort_size": (
            "≈201 computer science bachelor's degrees awarded annually (Princeton's "
            "largest major)"
        ),
        "note": (
            "Princeton does not publish a per-major entering-cohort size; the figure is "
            "the annual count of computer science bachelor's degrees awarded (College "
            "Scorecard Field of Study, CIP 11.07)."
        ),
        "source": "U.S. Dept. of Education College Scorecard — Field of Study (CIP 11.07)",
        "source_url": "https://collegescorecard.ed.gov/school/?186131",
    },
}

# ── Faculty (lead + directory link), where confidently sourced (the flagship) ──
_FACULTY_BY_SLUG: dict[str, dict] = {
    "princeton-computer-science-bs": {
        "lead": [
            {
                "name": "Robert E. Tarjan",
                "title": (
                    "James S. McDonnell Distinguished University Professor of Computer "
                    "Science; 1986 ACM A.M. Turing Award laureate"
                ),
            },
            {
                "name": "Brian Kernighan",
                "title": (
                    "Professor of Computer Science (co-author of the C programming "
                    "language book)"
                ),
            },
        ],
        "note": (
            "Princeton Computer Science faculty include an ACM A.M. Turing Award laureate "
            "(Robert Tarjan); Jennifer Rexford, a professor in the department, serves as "
            "Princeton's Provost."
        ),
        "directory_url": "https://www.cs.princeton.edu/people/faculty",
    },
}

# ── Aggregated, cited student-review themes (≥2 third-party sources per coverable program) ──
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "princeton-computer-science-bs": {
        "summary": (
            "Students and third-party guides consistently describe Princeton Computer "
            "Science as academically elite and rigorous, with world-class faculty, strong "
            "undergraduate research access, and exceptional placement into top technology "
            "firms and graduate programs; U.S. News ranks Princeton fifth in computer "
            "science among national universities (2026); common cautions are a fast pace, "
            "demanding problem sets, and the senior independent-work (thesis) requirement."
        ),
        "themes": [
            {
                "label": "Academic strength",
                "sentiment": "positive",
                "detail": "Among the strongest CS programs anywhere, with leading faculty.",
            },
            {
                "label": "Research & resources",
                "sentiment": "positive",
                "detail": (
                    "Deep undergraduate research access and a famous "
                    "independent-work tradition."
                ),
            },
            {
                "label": "Strong tech & grad placement",
                "sentiment": "positive",
                "detail": "Graduates place strongly into top technology firms and PhD programs.",
            },
            {
                "label": "Rigorous & fast-paced",
                "sentiment": "caution",
                "detail": "A demanding workload and challenging problem sets are recurring themes.",
            },
            {
                "label": "Independent work required",
                "sentiment": "caution",
                "detail": "The required junior/senior independent work is substantial.",
            },
        ],
        "sources": [
            {
                "label": "Niche — Princeton University",
                "url": "https://www.niche.com/colleges/princeton-university/",
            },
            {
                "label": "NorthJersey.com — Princeton tops U.S. News 2026 (CS ranked 5th)",
                "url": (
                    "https://www.northjersey.com/story/news/2024/09/26/"
                    "princeton-beats-out-harvard-mit-fous-news-ranks-princeton-university-"
                    "ranked-the-top-school-heres-why/75377405007/"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-public-affairs-mpa": {
        "summary": (
            "Students and policy guides consistently rank Princeton SPIA's Master in Public "
            "Affairs among the nation's elite MPA programs — a two-year, quantitatively "
            "rigorous degree with full tuition funding for all admitted students — praising "
            "policy workshops, qualifying exams, and strong public-sector placement; common "
            "cautions are extreme selectivity (~70 students per cohort), a demanding methods "
            "core, and less flexibility than larger policy schools in major cities."
        ),
        "themes": [
            {
                "label": "Full tuition funding",
                "sentiment": "positive",
                "detail": (
                    "Princeton covers full tuition and required fees for every MPA student, "
                    "a rare access policy among elite policy schools."
                ),
            },
            {
                "label": "Quantitative rigor",
                "sentiment": "positive",
                "detail": (
                    "A methods-heavy core with qualifying exams and a required policy workshop."
                ),
            },
            {
                "label": "Public-service mission",
                "sentiment": "positive",
                "detail": (
                    "Admissions emphasize professional public-service experience and "
                    "substantive policy careers."
                ),
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": (
                    "Roughly 70 students per entering MPA class; admission is highly competitive."
                ),
            },
            {
                "label": "Structured curriculum",
                "sentiment": "mixed",
                "detail": (
                    "Less elective flexibility than programs in larger cities like Washington "
                    "or New York."
                ),
            },
        ],
        "sources": [
            {
                "label": "Princeton SPIA — Master in Public Affairs",
                "url": "https://spia.princeton.edu/graduate-admissions/master-public-affairs",
            },
            {
                "label": "Model Diplomat — Top Graduate International Relations Programs 2026",
                "url": (
                    "https://blog.modeldiplomat.com/top-graduate-international-relations-programs"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-public-affairs-ab": {
        "summary": (
            "Students and college guides rank Princeton's undergraduate public and "
            "international affairs major among the nation's strongest policy programs — "
            "Niche ranks Princeton No. 1 for public policy (2026) — praising a "
            "quantitatively rigorous core (microeconomics, macroeconomics, econometrics), "
            "SPIA Policy Task Forces with real-world clients, and a two-year independent-work "
            "sequence; common cautions are heavy econometrics requirements, limited "
            "pre-professional flexibility, and Princeton's overall demanding workload."
        ),
        "themes": [
            {
                "label": "Quantitative policy core",
                "sentiment": "positive",
                "detail": (
                    "Required economics and econometrics sequence plus core domestic and "
                    "international policy courses."
                ),
            },
            {
                "label": "Applied task forces",
                "sentiment": "positive",
                "detail": (
                    "Semester-long policy projects commissioned by organizations like the "
                    "World Bank or U.S. Treasury."
                ),
            },
            {
                "label": "Independent work",
                "sentiment": "positive",
                "detail": (
                    "A two-year junior and senior independent-work sequence culminating in "
                    "a senior thesis."
                ),
            },
            {
                "label": "Methods intensity",
                "sentiment": "caution",
                "detail": (
                    "Econometrics and quantitative requirements are heavier than at most "
                    "peer policy majors."
                ),
            },
            {
                "label": "Campus workload",
                "sentiment": "caution",
                "detail": (
                    "SPIA students share Princeton's senior-thesis culture and fast academic "
                    "pace."
                ),
            },
        ],
        "sources": [
            {
                "label": (
                    "AdmissionSight — Best Colleges for Public Policy 2026 "
                    "(Princeton #1 Niche)"
                ),
                "url": "https://admissionsight.com/best-colleges-for-public-policy/",
            },
            {
                "label": "Princeton SPIA — Undergraduate Program",
                "url": "https://spia.princeton.edu/undergraduate-program",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-economics-bs": {
        "summary": (
            "Students and academic guides consistently rank Princeton Economics among the "
            "world's premier undergraduate programs — Niche places it ninth nationally "
            "(2026) and IDEAS/RePEc ranks Princeton's economics department fourth globally "
            "by graduate placement — praising a research-focused curriculum with junior and "
            "senior independent work, world-class faculty, and strong finance and PhD "
            "placement; common cautions are a fast theoretical pace, heavy econometrics "
            "requirements, and that the major attracts more than 250 juniors and seniors "
            "each year, making advising competitive."
        ),
        "themes": [
            {
                "label": "Research-focused curriculum",
                "sentiment": "positive",
                "detail": (
                    "Two major research projects plus core courses in micro, macro, and "
                    "econometrics."
                ),
            },
            {
                "label": "Faculty & reputation",
                "sentiment": "positive",
                "detail": (
                    "A top-ranked department whose graduates place into leading PhD programs "
                    "and finance roles."
                ),
            },
            {
                "label": "Career outcomes",
                "sentiment": "positive",
                "detail": (
                    "Princeton Economics reports that more than 90% of seniors accept job "
                    "offers or graduate-school admission."
                ),
            },
            {
                "label": "Theoretical pace",
                "sentiment": "caution",
                "detail": (
                    "Proof- and model-heavy coursework moves quickly for students without "
                    "strong math preparation."
                ),
            },
            {
                "label": "Large major",
                "sentiment": "mixed",
                "detail": (
                    "Among Princeton's most popular majors, which can mean competitive "
                    "access to small seminars."
                ),
            },
        ],
        "sources": [
            {
                "label": "Princeton Economics — Undergraduate Program",
                "url": "https://economics.princeton.edu/undergraduate-program/",
            },
            {
                "label": "Niche — 2026 Best Colleges for Economics (Princeton #9)",
                "url": "https://www.niche.com/colleges/search/best-colleges-for-economics/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-physics-bs": {
        "summary": (
            "Students and guides describe Princeton Physics as one of the strongest "
            "undergraduate programs in the United States — Times Higher Education ranks "
            "Princeton fifth globally in physical sciences (2026) and home to the Princeton "
            "Plasma Physics Laboratory — praising deep theoretical training, early research "
            "access, and a pipeline to top PhD programs; common cautions are mathematically "
            "demanding coursework, limited applied-industry pathways, and Princeton's "
            "required senior thesis."
        ),
        "themes": [
            {
                "label": "World-class physics",
                "sentiment": "positive",
                "detail": (
                    "A leading department with ties to PPPL and major experimental and "
                    "theoretical groups."
                ),
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": (
                    "Students access faculty labs and independent work from the junior year."
                ),
            },
            {
                "label": "PhD pipeline",
                "sentiment": "positive",
                "detail": (
                    "Graduates frequently continue to leading physics and engineering PhD "
                    "programs."
                ),
            },
            {
                "label": "Math intensity",
                "sentiment": "caution",
                "detail": (
                    "A rigorous mathematical core is expected from early in the major."
                ),
            },
            {
                "label": "Senior thesis",
                "sentiment": "caution",
                "detail": (
                    "All Princeton undergraduates complete substantial independent work."
                ),
            },
        ],
        "sources": [
            {
                "label": (
                    "Times Higher Education — Princeton University "
                    "(Physical Sciences #5, 2026)"
                ),
                "url": "https://www.timeshighereducation.com/world-university-rankings/princeton-university",
            },
            {
                "label": "Niche — Princeton University (Physics #5 nationally)",
                "url": "https://www.niche.com/colleges/princeton-university/majors/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-mathematics-bs": {
        "summary": (
            "Students and academic guides describe Princeton Mathematics as a deeply "
            "theoretical undergraduate major within a research powerhouse — Times Higher "
            "Education ranks Princeton third globally (2026) with leading physical-sciences "
            "strength — praising proof-based coursework, small seminars, and a pipeline to "
            "top PhD programs; common cautions are abstract, fast-paced material, limited "
            "pre-professional business pathways, and the shared Princeton workload."
        ),
        "themes": [
            {
                "label": "Proof-based rigor",
                "sentiment": "positive",
                "detail": (
                    "A pure-mathematics core emphasizing analysis, algebra, and topology."
                ),
            },
            {
                "label": "Research culture",
                "sentiment": "positive",
                "detail": (
                    "Faculty in mathematics and affiliated institutes collaborate on theory "
                    "and applied work."
                ),
            },
            {
                "label": "PhD pipeline",
                "sentiment": "positive",
                "detail": (
                    "Graduates frequently continue to leading mathematics and quantitative "
                    "PhD programs."
                ),
            },
            {
                "label": "Abstract pace",
                "sentiment": "caution",
                "detail": (
                    "Courses move quickly through graduate-level material for undergraduates."
                ),
            },
            {
                "label": "Limited pre-professional focus",
                "sentiment": "mixed",
                "detail": (
                    "The major targets research careers more than corporate finance tracks."
                ),
            },
        ],
        "sources": [
            {
                "label": "Times Higher Education — Princeton University (2026)",
                "url": "https://www.timeshighereducation.com/world-university-rankings/princeton-university",
            },
            {
                "label": "Niche — Princeton University",
                "url": "https://www.niche.com/colleges/princeton-university/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-electrical-engineering-bs": {
        "summary": (
            "Students and engineering guides describe Princeton Electrical and Computer "
            "Engineering as a rigorous B.S.E. program within SEAS — U.S. News ranks "
            "Princeton eleventh nationally for engineering (2026) — praising strong "
            "theoretical foundations, research labs, and placement into technology and "
            "graduate programs; common cautions are a demanding math and physics core, "
            "the B.S.E. declaration deadline in freshman spring, and limited class size "
            "versus larger engineering colleges."
        ),
        "themes": [
            {
                "label": "Rigorous ECE core",
                "sentiment": "positive",
                "detail": (
                    "A mathematically demanding curriculum spanning circuits, signals, and "
                    "computer systems."
                ),
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": (
                    "Undergraduates join SEAS labs in communications, robotics, and quantum "
                    "systems."
                ),
            },
            {
                "label": "Tech placement",
                "sentiment": "positive",
                "detail": (
                    "Graduates place into top technology firms and leading ECE PhD programs."
                ),
            },
            {
                "label": "B.S.E. timeline",
                "sentiment": "caution",
                "detail": (
                    "Engineering students must declare in freshman spring, earlier than A.B. "
                    "majors."
                ),
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": (
                    "Shared Princeton problem-set culture and senior independent project "
                    "requirements."
                ),
            },
        ],
        "sources": [
            {
                "label": "Princeton Engineering — Electrical and Computer Engineering",
                "url": "https://ece.princeton.edu/",
            },
            {
                "label": "Niche — Princeton University (Engineering #11 nationally)",
                "url": "https://www.niche.com/colleges/princeton-university/majors/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-mechanical-engineering-bs": {
        "summary": (
            "Students and guides describe Princeton Mechanical and Aerospace Engineering "
            "as a selective B.S.E. program with strong ties to robotics, fluid mechanics, "
            "and materials research — praising design-and-analysis depth, faculty mentorship, "
            "and graduate-school placement; common cautions are heavy physics and math "
            "prerequisites, the freshman-spring major declaration, and a demanding "
            "independent-project requirement."
        ),
        "themes": [
            {
                "label": "Design & analysis depth",
                "sentiment": "positive",
                "detail": (
                    "A quantitative curriculum spanning dynamics, thermodynamics, and "
                    "modern fabrication."
                ),
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": (
                    "Access to robotics, fluid mechanics, and aerospace labs within SEAS."
                ),
            },
            {
                "label": "Graduate placement",
                "sentiment": "positive",
                "detail": (
                    "Many graduates continue to top PhD programs or aerospace and tech roles."
                ),
            },
            {
                "label": "Core intensity",
                "sentiment": "caution",
                "detail": (
                    "Shared engineering physics and math requirements create a heavy first "
                    "two years."
                ),
            },
            {
                "label": "Independent project",
                "sentiment": "caution",
                "detail": (
                    "B.S.E. students complete a senior thesis or independent project."
                ),
            },
        ],
        "sources": [
            {
                "label": "Princeton Engineering — Mechanical and Aerospace Engineering",
                "url": "https://mae.princeton.edu/",
            },
            {
                "label": "Niche — Princeton University",
                "url": "https://www.niche.com/colleges/princeton-university/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-chemical-engineering-bs": {
        "summary": (
            "Students and engineering guides describe Princeton Chemical and Biological "
            "Engineering as a small, elite B.S.E. program blending molecular science with "
            "quantitative transport and reaction engineering — praising faculty mentorship, "
            "ties to the Andlinger Center and genomics institutes, and interdisciplinary "
            "research; common cautions are demanding thermodynamics prerequisites, a "
            "limited alumni network versus larger ChemE schools, and Princeton's heavy "
            "workload."
        ),
        "themes": [
            {
                "label": "Quantitative ChemE core",
                "sentiment": "positive",
                "detail": (
                    "Transport, thermodynamics, and reaction engineering with rigorous "
                    "mathematical modeling."
                ),
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": (
                    "Links to energy, bioengineering, and materials labs across campus."
                ),
            },
            {
                "label": "Small-class mentoring",
                "sentiment": "positive",
                "detail": (
                    "A compact ChemE cohort enables close faculty advising and lab placement."
                ),
            },
            {
                "label": "Prerequisite intensity",
                "sentiment": "caution",
                "detail": (
                    "Shared engineering physics and chemistry sequences are time-consuming."
                ),
            },
            {
                "label": "Career breadth",
                "sentiment": "mixed",
                "detail": (
                    "Placement skews toward PhD study and specialized R&D rather than "
                    "large-process engineering roles."
                ),
            },
        ],
        "sources": [
            {
                "label": "Princeton Engineering — Chemical and Biological Engineering",
                "url": "https://cbe.princeton.edu/",
            },
            {
                "label": "Niche — Princeton University",
                "url": "https://www.niche.com/colleges/princeton-university/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-operations-research-bs": {
        "summary": (
            "Students and quantitative-finance guides describe Princeton ORFE as a "
            "mathematically rigorous engineering major centered on statistics, probability, "
            "optimization, and stochastic processes — one of Princeton's most popular majors "
            "— praising flexibility across finance, machine learning, and operations "
            "research electives and strong placement into quant finance, consulting, and "
            "PhD programs; common cautions are a heavy math core, that the program is more "
            "quantitative than a traditional finance major, and competitive recruiting for "
            "top banking roles versus dedicated MFin programs."
        ),
        "themes": [
            {
                "label": "Quantitative depth",
                "sentiment": "positive",
                "detail": (
                    "A statistics-and-optimization core with electives in ML, finance, and "
                    "econometrics."
                ),
            },
            {
                "label": "Career flexibility",
                "sentiment": "positive",
                "detail": (
                    "Graduates place into quant finance, consulting, tech, and top PhD "
                    "programs."
                ),
            },
            {
                "label": "Popular major",
                "sentiment": "positive",
                "detail": (
                    "Consistently among Princeton's most chosen B.S.E. options for "
                    "quantitatively minded students."
                ),
            },
            {
                "label": "Math intensity",
                "sentiment": "caution",
                "detail": (
                    "A fast probability-and-stochastic-processes sequence is foundational."
                ),
            },
            {
                "label": "Not a finance degree",
                "sentiment": "mixed",
                "detail": (
                    "Students seeking a banking-focused curriculum may prefer dedicated "
                    "MFin or MBA paths."
                ),
            },
        ],
        "sources": [
            {
                "label": "Princeton ORFE — Undergraduate Program",
                "url": "https://orfe.princeton.edu/undergraduate",
            },
            {
                "label": "Career Karma — Princeton University Review (popular majors)",
                "url": "https://careerkarma.com/blog/princeton-review-college/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-civil-engineering-bs": {
        "summary": (
            "Students and guides describe Princeton Civil and Environmental Engineering "
            "as a research-oriented B.S.E. program with strengths in structures, "
            "environment, and sustainable infrastructure — praising ties to the "
            "Andlinger Center for Energy and the Environment, interdisciplinary policy "
            "electives, and graduate-school placement; common cautions are a smaller program "
            "than peer civil-engineering colleges, limited corporate recruiting relative to "
            "larger schools, and demanding independent-project requirements."
        ),
        "themes": [
            {
                "label": "Environmental strength",
                "sentiment": "positive",
                "detail": (
                    "Close ties to the Andlinger Center and campus sustainability research."
                ),
            },
            {
                "label": "Interdisciplinary options",
                "sentiment": "positive",
                "detail": (
                    "Students cross-register in SPIA, economics, and architecture courses."
                ),
            },
            {
                "label": "Research placement",
                "sentiment": "positive",
                "detail": (
                    "Graduates frequently pursue PhD programs or specialized environmental "
                    "roles."
                ),
            },
            {
                "label": "Small program",
                "sentiment": "caution",
                "detail": (
                    "Fewer civil-engineering peers on campus than at large public "
                    "engineering colleges."
                ),
            },
            {
                "label": "Corporate recruiting",
                "sentiment": "mixed",
                "detail": (
                    "On-campus construction and infrastructure firm recruiting is lighter "
                    "than at Big Ten engineering schools."
                ),
            },
        ],
        "sources": [
            {
                "label": "Princeton Engineering — Civil and Environmental Engineering",
                "url": "https://cee.princeton.edu/",
            },
            {
                "label": "Andlinger Center for Energy and the Environment",
                "url": "https://andlinger.princeton.edu/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-architecture-bs": {
        "summary": (
            "Students and design guides describe Princeton's B.A. in Architecture as a "
            "theory- and history-rich program within a top research university — praising "
            "studio access, ties to the humanities division, and a strong pipeline to "
            "leading M.Arch and PhD programs; common cautions are that the undergraduate "
            "degree is not a professional NAAB-accredited architecture license, limited "
            "studio space versus dedicated art schools, and Princeton's overall academic "
            "intensity."
        ),
        "themes": [
            {
                "label": "Theory & history depth",
                "sentiment": "positive",
                "detail": (
                    "A humanities-grounded curriculum spanning architectural history, "
                    "theory, and urbanism."
                ),
            },
            {
                "label": "Graduate pipeline",
                "sentiment": "positive",
                "detail": (
                    "Graduates frequently continue to leading M.Arch and architectural "
                    "PhD programs."
                ),
            },
            {
                "label": "Interdisciplinary campus",
                "sentiment": "positive",
                "detail": (
                    "Access to engineering, policy, and visual-arts courses across Princeton."
                ),
            },
            {
                "label": "Not a professional degree",
                "sentiment": "caution",
                "detail": (
                    "The B.A. does not confer NAAB professional licensure; an M.Arch is "
                    "typically required."
                ),
            },
            {
                "label": "Studio resources",
                "sentiment": "mixed",
                "detail": (
                    "Fewer dedicated studio facilities than at RISD or architecture-only "
                    "colleges."
                ),
            },
        ],
        "sources": [
            {
                "label": "Princeton School of Architecture — Undergraduate",
                "url": "https://soa.princeton.edu/undergraduate",
            },
            {
                "label": "Niche — Princeton University",
                "url": "https://www.niche.com/colleges/princeton-university/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-psychology-bs": {
        "summary": (
            "Students and guides rank Princeton Psychology among the strongest "
            "undergraduate programs nationally — U.S. News ranks Princeton second in "
            "psychology among national universities (2026) — praising neuroscience "
            "integration, early research access through the Princeton Neuroscience "
            "Institute, and graduate-school placement; common cautions are a competitive "
            "major with limited clinical-training pathways at the undergraduate level and "
            "Princeton's required independent-work sequence."
        ),
        "themes": [
            {
                "label": "Research integration",
                "sentiment": "positive",
                "detail": (
                    "Close ties to neuroscience, genomics, and cognitive-science labs on "
                    "campus."
                ),
            },
            {
                "label": "National ranking",
                "sentiment": "positive",
                "detail": (
                    "Consistently top-ranked among national universities for psychology."
                ),
            },
            {
                "label": "PhD pipeline",
                "sentiment": "positive",
                "detail": (
                    "Graduates frequently continue to leading psychology and neuroscience "
                    "PhD programs."
                ),
            },
            {
                "label": "Limited clinical focus",
                "sentiment": "caution",
                "detail": (
                    "The program emphasizes research over practitioner or counseling "
                    "training."
                ),
            },
            {
                "label": "Independent work",
                "sentiment": "caution",
                "detail": (
                    "Junior and senior independent projects add substantial workload."
                ),
            },
        ],
        "sources": [
            {
                "label": (
                    "NorthJersey.com — Princeton psychology ranked 2nd nationally "
                    "(U.S. News 2026)"
                ),
                "url": (
                    "https://www.northjersey.com/story/news/2024/09/26/"
                    "princeton-beats-out-harvard-mit-fous-news-ranks-princeton-university-"
                    "ranked-the-top-school-heres-why/75377405007/"
                ),
            },
            {
                "label": "Princeton Neuroscience Institute",
                "url": "https://pni.princeton.edu/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-molecular-biology-bs": {
        "summary": (
            "Students and guides describe Princeton Molecular Biology as a research-intensive "
            "undergraduate major with ties to the Lewis-Sigler Institute and genomics "
            "facilities — praising early lab access, Nobel-caliber faculty, and strong "
            "medical- and PhD-school placement; common cautions are long lab hours stacked "
            "on Princeton's core requirements, limited pre-med advising relative to larger "
            "universities, and a competitive pre-health culture."
        ),
        "themes": [
            {
                "label": "Research-intensive labs",
                "sentiment": "positive",
                "detail": (
                    "Undergraduates join genomics, structural biology, and systems-biology "
                    "groups early."
                ),
            },
            {
                "label": "Institute ties",
                "sentiment": "positive",
                "detail": (
                    "Access to Lewis-Sigler and Princeton Genomics Center facilities."
                ),
            },
            {
                "label": "Graduate & pre-med outcomes",
                "sentiment": "positive",
                "detail": (
                    "Graduates place strongly into top PhD and medical programs."
                ),
            },
            {
                "label": "Lab workload",
                "sentiment": "caution",
                "detail": (
                    "Multi-hour lab sections on top of Princeton's core are a recurring theme."
                ),
            },
            {
                "label": "Pre-health competition",
                "sentiment": "mixed",
                "detail": (
                    "A large share of majors pursue medicine, intensifying peer competition."
                ),
            },
        ],
        "sources": [
            {
                "label": "Lewis-Sigler Institute for Integrative Genomics",
                "url": "https://lsi.princeton.edu/",
            },
            {
                "label": "Niche — Princeton University",
                "url": "https://www.niche.com/colleges/princeton-university/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-neuroscience-bs": {
        "summary": (
            "Students and guides describe Princeton Neuroscience as an interdisciplinary "
            "undergraduate certificate and concentration leveraging the Princeton "
            "Neuroscience Institute — praising cross-department coursework, early research "
            "in cognitive and systems neuroscience, and graduate-school placement; common "
            "cautions are that the program spans multiple departments with varying advising "
            "structures, limited clinical-neuroscience training, and demanding "
            "prerequisites in biology, chemistry, and math."
        ),
        "themes": [
            {
                "label": "PNI integration",
                "sentiment": "positive",
                "detail": (
                    "Direct access to the Princeton Neuroscience Institute's research "
                    "community."
                ),
            },
            {
                "label": "Interdisciplinary breadth",
                "sentiment": "positive",
                "detail": (
                    "Courses span psychology, molecular biology, engineering, and computer "
                    "science."
                ),
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": (
                    "Undergraduates join cognitive, computational, and systems-neuroscience "
                    "labs."
                ),
            },
            {
                "label": "Cross-department advising",
                "sentiment": "caution",
                "detail": (
                    "Requirements span multiple units, which can complicate course planning."
                ),
            },
            {
                "label": "Prerequisite load",
                "sentiment": "caution",
                "detail": (
                    "A heavy biology, chemistry, and math foundation is required."
                ),
            },
        ],
        "sources": [
            {
                "label": "Princeton Neuroscience Institute",
                "url": "https://pni.princeton.edu/",
            },
            {
                "label": "Niche — Princeton University",
                "url": "https://www.niche.com/colleges/princeton-university/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-chemistry-bs": {
        "summary": (
            "Students and guides rank Princeton Chemistry among the strongest undergraduate "
            "programs nationally — Niche places it fourth for chemistry (2026) — praising "
            "early lab research, Nobel-caliber faculty, and depth in physical and synthetic "
            "chemistry; common cautions are long lab hours stacked on Princeton's heavy "
            "core, limited non-research career advising, and the pressure of a "
            "high-achieving peer group."
        ),
        "themes": [
            {
                "label": "Research-intensive labs",
                "sentiment": "positive",
                "detail": (
                    "Undergraduates join synthesis, catalysis, and chemical-biology groups "
                    "from early terms."
                ),
            },
            {
                "label": "Faculty depth",
                "sentiment": "positive",
                "detail": (
                    "A leading department with direct access to experimental and theoretical "
                    "chemists."
                ),
            },
            {
                "label": "Graduate-school outcomes",
                "sentiment": "positive",
                "detail": (
                    "Most graduates pursue PhD programs or research careers in industry R&D."
                ),
            },
            {
                "label": "Lab workload",
                "sentiment": "caution",
                "detail": (
                    "Multi-hour lab sections on top of problem sets are a recurring theme."
                ),
            },
            {
                "label": "Research-focused careers",
                "sentiment": "mixed",
                "detail": (
                    "Career paths skew toward academia and research labs versus large "
                    "corporate recruiting."
                ),
            },
        ],
        "sources": [
            {
                "label": "Niche — Princeton University (Chemistry #4 nationally)",
                "url": "https://www.niche.com/colleges/princeton-university/majors/",
            },
            {
                "label": "Princeton Department of Chemistry",
                "url": "https://chemistry.princeton.edu/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-computer-science-ms": {
        "summary": (
            "Students and guides describe Princeton's M.S.E. in Computer Science as a "
            "selective, research-oriented graduate degree within a top-ranked department — "
            "Times Higher Education ranks Princeton fifth globally in computer science "
            "(2026) — praising faculty depth, thesis or project options, and placement into "
            "PhD programs and technology roles; common cautions are that the M.S.E. is not "
            "a large professional cohort like industry-focused CS master's programs, "
            "limited career-services infrastructure versus dedicated professional degrees, "
            "and a demanding qualifying-course sequence."
        ),
        "themes": [
            {
                "label": "Research depth",
                "sentiment": "positive",
                "detail": (
                    "A faculty-led program with thesis and independent-project pathways."
                ),
            },
            {
                "label": "Department reputation",
                "sentiment": "positive",
                "detail": (
                    "Among the highest-ranked CS departments globally for theory and systems."
                ),
            },
            {
                "label": "PhD & industry placement",
                "sentiment": "positive",
                "detail": (
                    "Graduates place into leading PhD programs and top technology firms."
                ),
            },
            {
                "label": "Small cohort",
                "sentiment": "caution",
                "detail": (
                    "A selective program with fewer students than large professional CS "
                    "master's degrees."
                ),
            },
            {
                "label": "Not industry-focused",
                "sentiment": "mixed",
                "detail": (
                    "Less structured career coaching than dedicated MEng or professional "
                    "master's programs."
                ),
            },
        ],
        "sources": [
            {
                "label": "Times Higher Education — Princeton (Computer Science #5, 2026)",
                "url": "https://www.timeshighereducation.com/world-university-rankings/princeton-university",
            },
            {
                "label": "Princeton Computer Science — Graduate Program",
                "url": "https://www.cs.princeton.edu/grad",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-architecture-ms": {
        "summary": (
            "Students and architecture guides rank Princeton's professional M.Arch. among "
            "the nation's elite NAAB-accredited programs — Study Architecture and design "
            "media consistently place Princeton in the top tier — praising studio rigor, "
            "building-technology depth, and a design thesis; common cautions are a "
            "three-year timeline for non-pre-professional entrants, prerequisite math and "
            "physics requirements, and limited studio space versus dedicated art schools."
        ),
        "themes": [
            {
                "label": "NAAB professional degree",
                "sentiment": "positive",
                "detail": (
                    "An accredited M.Arch. that qualifies graduates for architectural "
                    "licensure after internship."
                ),
            },
            {
                "label": "Studio sequence",
                "sentiment": "positive",
                "detail": (
                    "A rigorous design-studio core paired with history/theory and building "
                    "technology."
                ),
            },
            {
                "label": "Design thesis",
                "sentiment": "positive",
                "detail": (
                    "A culminating independent design thesis in the final term."
                ),
            },
            {
                "label": "Prerequisites",
                "sentiment": "caution",
                "detail": (
                    "College-level math, physics, and architectural history required before "
                    "matriculation."
                ),
            },
            {
                "label": "Program length",
                "sentiment": "mixed",
                "detail": (
                    "Typically three years for students without a pre-professional "
                    "architecture background."
                ),
            },
        ],
        "sources": [
            {
                "label": "Princeton School of Architecture — Professional M.Arch.",
                "url": (
                    "https://soa.princeton.edu/school/"
                    "professional-master-architecture-program"
                ),
            },
            {
                "label": "Study Architecture — Princeton University",
                "url": "https://www.studyarchitecture.com/school/princeton-university/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-chemical-engineering-ms": {
        "summary": (
            "Graduate guides describe Princeton's M.S.E. in Chemical and Biological "
            "Engineering as a research-intensive master's within a top-ranked department "
            "— praising quantitative transport and reaction-engineering training, "
            "interdisciplinary ties to energy and bio institutes, and a pipeline to "
            "leading Ph.D. programs and R&D roles; common cautions are that the degree is "
            "research-based (not a professional M.Eng.), limited cohort size, and "
            "Princeton's demanding general-exam culture for students who continue to the "
            "Ph.D."
        ),
        "themes": [
            {
                "label": "Research M.S.E.",
                "sentiment": "positive",
                "detail": (
                    "A thesis-based master's typically completed in 1.5–2 years with "
                    "faculty-supervised research."
                ),
            },
            {
                "label": "Quantitative core",
                "sentiment": "positive",
                "detail": (
                    "Transport, thermodynamics, and reaction engineering with rigorous "
                    "mathematical modeling."
                ),
            },
            {
                "label": "Interdisciplinary labs",
                "sentiment": "positive",
                "detail": (
                    "Links to the Andlinger Center, genomics institutes, and materials "
                    "research across campus."
                ),
            },
            {
                "label": "Ph.D. pipeline",
                "sentiment": "positive",
                "detail": (
                    "Many M.S.E. students continue to top chemical-engineering Ph.D. "
                    "programs."
                ),
            },
            {
                "label": "Selective cohort",
                "sentiment": "caution",
                "detail": (
                    "A small department with competitive admission and limited funded "
                    "master's slots."
                ),
            },
        ],
        "sources": [
            {
                "label": "Princeton CBE — Graduate Program",
                "url": "https://cbe.princeton.edu/graduate",
            },
            {
                "label": "Princeton Graduate School — Chemical and Biological Engineering",
                "url": (
                    "https://gradschool.princeton.edu/academics/degrees-requirements/"
                    "fields-study/chemical-and-biological-engineering"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-civil-engineering-ms": {
        "summary": (
            "Graduate guides describe Princeton's M.S.E. in Civil and Environmental "
            "Engineering as a research-focused master's spanning structures, "
            "environmental systems, and sustainable infrastructure — praising "
            "interdisciplinary tracks in hydrology, materials, and urban resilience, "
            "faculty mentorship, and placement into Ph.D. programs and engineering "
            "consulting; common cautions are a small cohort, a thesis requirement, and "
            "less industry-oriented coursework than one-year M.Eng. programs at larger "
            "engineering schools."
        ),
        "themes": [
            {
                "label": "Research breadth",
                "sentiment": "positive",
                "detail": (
                    "Tracks spanning structures, environmental engineering, hydrology, and "
                    "sustainable cities."
                ),
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": (
                    "Close advising within a compact department with leading researchers."
                ),
            },
            {
                "label": "Ph.D. placement",
                "sentiment": "positive",
                "detail": (
                    "Graduates frequently continue to top civil and environmental Ph.D. "
                    "programs."
                ),
            },
            {
                "label": "Thesis requirement",
                "sentiment": "caution",
                "detail": (
                    "The M.S.E. is research-based — not a coursework-only professional "
                    "master's."
                ),
            },
            {
                "label": "Small cohort",
                "sentiment": "mixed",
                "detail": (
                    "Limited class size versus large civil-engineering programs at public "
                    "universities."
                ),
            },
        ],
        "sources": [
            {
                "label": "Princeton CEE — Graduate Studies",
                "url": "https://cee.princeton.edu/graduate",
            },
            {
                "label": "Princeton Graduate School — Civil and Environmental Engineering",
                "url": (
                    "https://gradschool.princeton.edu/academics/degrees-requirements/"
                    "fields-study/civil-and-environmental-engineering"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-electrical-electronics-and-communications-engineering-ms": {
        "summary": (
            "Engineering guides describe Princeton's M.Eng. in Electrical and Computer "
            "Engineering as a one-year, coursework-based master's for practicing "
            "engineers — ECE does not offer an M.S.E. — praising access to Princeton's "
            "communications, robotics, and quantum-systems faculty; common cautions are "
            "that Princeton provides no institutional funding (employer or fellowship "
            "support required), no thesis or research component, and a narrow cohort "
            "focused on professional advancement rather than Ph.D. preparation."
        ),
        "themes": [
            {
                "label": "One-year M.Eng.",
                "sentiment": "positive",
                "detail": (
                    "A coursework-based master's typically completed in one academic year."
                ),
            },
            {
                "label": "ECE faculty access",
                "sentiment": "positive",
                "detail": (
                    "Courses spanning communications, computer systems, and quantum "
                    "engineering."
                ),
            },
            {
                "label": "Professional focus",
                "sentiment": "positive",
                "detail": (
                    "Designed for practicing engineers advancing technical depth without "
                    "a research thesis."
                ),
            },
            {
                "label": "No institutional funding",
                "sentiment": "caution",
                "detail": (
                    "Candidates must demonstrate external financial support — Princeton "
                    "does not fund M.Eng. students."
                ),
            },
            {
                "label": "No M.S.E. option",
                "sentiment": "mixed",
                "detail": (
                    "ECE is the only SEAS department that does not offer a research-based "
                    "M.S.E."
                ),
            },
        ],
        "sources": [
            {
                "label": "Princeton ECE — Graduate Programs",
                "url": "https://ece.princeton.edu/academics/graduate",
            },
            {
                "label": "Princeton Engineering — Graduate FAQ (M.Eng. vs M.S.E.)",
                "url": "https://engineering.princeton.edu/graduate-studies/faq",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "princeton-mechanical-engineering-ms": {
        "summary": (
            "Graduate guides describe Princeton's M.S.E. in Mechanical and Aerospace "
            "Engineering as a research-intensive master's in dynamics, fluid mechanics, "
            "robotics, and propulsion — praising faculty-led thesis research, ties to "
            "aerospace and robotics labs, and placement into leading Ph.D. programs and "
            "aerospace R&D; common cautions are a demanding general-exam culture for "
            "Ph.D. continuers, a small cohort, and less structured career coaching than "
            "professional M.Eng. programs."
        ),
        "themes": [
            {
                "label": "Research M.S.E.",
                "sentiment": "positive",
                "detail": (
                    "A thesis-based master's with faculty-supervised research in MAE labs."
                ),
            },
            {
                "label": "Aerospace & robotics",
                "sentiment": "positive",
                "detail": (
                    "Strengths in fluid mechanics, propulsion, robotics, and materials."
                ),
            },
            {
                "label": "Ph.D. pipeline",
                "sentiment": "positive",
                "detail": (
                    "Many graduates continue to top mechanical and aerospace Ph.D. programs."
                ),
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": (
                    "Competitive admission within a small, research-focused department."
                ),
            },
            {
                "label": "Research intensity",
                "sentiment": "caution",
                "detail": (
                    "The M.S.E. requires substantial thesis work — not a coursework-only "
                    "professional degree."
                ),
            },
        ],
        "sources": [
            {
                "label": "Princeton MAE — Graduate Program",
                "url": "https://mae.princeton.edu/graduate",
            },
            {
                "label": "Princeton Graduate School — Mechanical and Aerospace Engineering",
                "url": (
                    "https://gradschool.princeton.edu/academics/degrees-requirements/"
                    "fields-study/mechanical-and-aerospace-engineering"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
}

_COVERABLE_REVIEWS = frozenset(_REVIEWS_BY_SLUG.keys())

# ── Application requirements ─────────────────────────────────────────────────
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission.",
}
# Undergraduate (A.B. / B.S.E.) admission via the Common Application, Coalition (Scoir)
# or QuestBridge. Princeton is test-optional for fall-2026 and fall-2027 entry, returning
# to required SAT/ACT for the 2027-28 admission cycle (fall-2028 entry).
_REQ_UNDERGRAD = {
    "materials": [
        {
            "name": "Common Application, Coalition Application (Scoir) or QuestBridge",
            "required": True,
        },
        {"name": "Princeton-specific writing supplement", "required": True},
        {"name": "Graded written paper (preferably English or history)", "required": True},
        {"name": "School report + secondary-school transcript", "required": True},
        {"name": "Counselor recommendation", "required": True},
        {"name": "$75 application fee; fee waivers available", "required": True},
        {
            "name": "SAT or ACT scores",
            "required": False,
            "note": (
                "Test-optional for fall-2026 and fall-2027 entry; required again starting "
                "the 2027-28 admission cycle (fall-2028 entry)."
            ),
        },
    ],
    "deadlines": [
        {"round": "Single-Choice Early Action", "date": "November 1"},
        {"round": "Regular Decision", "date": "January 1"},
    ],
    "recommendations": {
        "required": 2,
        "note": (
            "Two recommendations from teachers in core academic subjects, plus a "
            "counselor recommendation."
        ),
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "Duolingo English Test"],
            "required": False,
            "note": "English-proficiency proof may be required for non-native speakers.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {"label": "Princeton Admission — Apply", "url": "https://admission.princeton.edu/apply"}
        ],
    },
    "source": "Princeton Undergraduate Admission",
    "source_url": "https://admission.princeton.edu/apply/application-checklist",
}

# Graduate (SPIA MPA) admission via the Princeton Graduate School application.
_REQ_GRAD_MPA = {
    "materials": [
        {"name": "Princeton Graduate School online application", "required": True},
        {"name": "Statement of purpose / policy memo", "required": True},
        {"name": "Three letters of recommendation", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Résumé / CV", "required": True},
        {"name": "GRE scores", "required": False, "note": "Optional for the MPA."},
        {"name": "$75 application fee; fee waivers available", "required": True},
    ],
    "deadlines": [
        {"round": "MPA application deadline", "date": "Early December"},
    ],
    "recommendations": {
        "required": 3,
        "note": (
            "Three letters of recommendation submitted through the Graduate School application."
        ),
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": True,
            "note": (
                "Required for applicants whose native language is not English "
                "(waivers may apply)."
            ),
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Princeton SPIA — Graduate Admissions",
                "url": "https://spia.princeton.edu/graduate-admissions",
            }
        ],
    },
    "source": "Princeton SPIA — Master in Public Affairs Admissions",
    "source_url": "https://spia.princeton.edu/graduate-admissions/master-public-affairs",
}


def _requirements_for(spec: dict) -> dict:
    """Pick the admissions requirement set for a program by degree type."""
    if spec["degree_type"] == "masters":
        return dict(_REQ_GRAD_MPA)
    return dict(_REQ_UNDERGRAD)


# Nassau Hall leads the institution hero; see ``SCHOOL_OUTCOMES["campus_photos"]`` for gallery.
_CAMPUS_PHOTO = SCHOOL_OUTCOMES["campus_photos"][0]["url"]


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich Princeton to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Princeton is absent — safe on fresh/CI databases.
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
    inst.founded_year = 1746
    inst.campus_setting = "suburban"
    if not inst.website_url:
        inst.website_url = "https://www.princeton.edu"
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
        # Every school carries Princeton News RSS + public events filtered by keywords.
        sc.content_sources = _school_content(spec["name"])
        by_name[spec["name"]] = sc
    # Drop legacy units — programs.school_id is ON DELETE SET NULL, so this is FK-safe.
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
    # Princeton publishes no per-program employment report or industry breakdown, so every
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
        p.department = spec.get("department")
        p.description_text = spec["description"]
        # Website: verified department page where available, else the owning unit's site.
        p.website_url = _WEBSITE_BY_SLUG.get(slug) or _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "in_person")
        if slug == "princeton-computer-science-bs":
            p.content_sources = _CS_CONTENT
        else:
            p.content_sources = _program_content(spec)
        # Cost: SPIA MPA is fully funded (per-slug); undergraduate uses published rates.
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
                    "Princeton is need-blind and meets 100% of demonstrated need with "
                    "grants rather than loans, so most families pay far less than the "
                    "sticker price (average net price ≈ $6,100)."
                ),
                "source": "U.S. Dept. of Education College Scorecard (UNITID 186131)",
                "source_url": "https://collegescorecard.ed.gov/school/?186131",
                "year": "2024-25",
            }
        # Admissions: undergraduate or MPA graduate set by degree type.
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
                "source_url": "https://collegescorecard.ed.gov/school/?186131",
            }
            awards = _AWARDS_BY_SLUG.get(slug)
            if awards is not None:
                outcomes["degrees_conferred_annual"] = awards
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
        # Application deadline (upcoming undergraduate Regular Decision closes Jan 1).
        p.application_deadline = (
            date(2026, 12, 1) if spec["degree_type"] == "masters" else date(2027, 1, 1)
        )
    session.flush()
    # Reconcile legacy Princeton programs (slug not in the canonical set): delete when
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
