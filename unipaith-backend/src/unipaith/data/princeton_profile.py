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
complete federal College Scorecard Field-of-Study list for UNITID 186131; the School
of Architecture and the broader Graduate School are the resumption scope for a later run.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.princeton_ipeds_catalog import _IPEDS_CATALOG
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Princeton University"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-11"


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

_EXISTING_SLUGS = {p["slug"] for p in PROGRAMS}
_EXISTING_CIP_KEYS = {(p.get("cip"), p["degree_type"]) for p in PROGRAMS if p.get("cip")}


def _build_catalog() -> list[dict]:
    """Append breadth-first program nodes from the IPEDS Field-of-Study catalog."""
    out: list[dict] = []
    seen = set(_EXISTING_SLUGS)
    for slug, school, name, dtype, cip, dur, fmt, desc in _IPEDS_CATALOG:
        if slug in seen:
            continue
        if (cip, dtype) in _EXISTING_CIP_KEYS:
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

# ── Aggregated, cited student-review themes (≥2 third-party sources, the flagship) ──
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "princeton-computer-science-bs": {
        "summary": (
            "Students and third-party guides consistently describe Princeton Computer "
            "Science as academically elite and rigorous, with world-class faculty, strong "
            "undergraduate research access, and exceptional placement into top technology "
            "firms and graduate programs; common cautions are a fast pace, demanding "
            "problem sets, and the senior independent-work (thesis) requirement."
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
                "label": "U.S. News — Princeton University",
                "url": "https://www.usnews.com/best-colleges/princeton-university-2627",
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


# Real Princeton campus photo (Nassau Hall) — Wikimedia Commons, CC0, hotlinkable
# landscape JPG. Leads the institution hero.
_CAMPUS_PHOTO = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/"
    "Nassau_Hall_Princeton.JPG/1920px-Nassau_Hall_Princeton.JPG"
)


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
