"""Canonical Princeton University profile — the single source of truth.

Real, sourced data only (U.S. Dept. of Education College Scorecard, UNITID 186131 ·
NCES College Navigator / IPEDS · Princeton's Office of Institutional Research Common
Data Set 2024-25 · the official Princeton "Facts & Figures" page · the official QS /
Times Higher Education / U.S. News rankings · Princeton's official "Areas of Study"
catalog and the Graduate School "Fields of Study" listing · each department's official
site · the College Scorecard Field-of-Study earnings by CIP). ``apply(session)``
idempotently enriches the Princeton institution row, upserts its real degree-granting
academic units, and builds Princeton's FULL published degree catalog across them.

Princeton's academic structure (Office of the Dean of the Faculty, Chapter III):
the faculty is organized into four divisions — I the Humanities (incl. Architecture),
II the Social Sciences (incl. History and the School of Public and International
Affairs), III the Natural Sciences (incl. Mathematics and Psychology), and IV
Engineering and Applied Science. Except for Engineering, the divisions have no
administrative or instructional responsibilities — they group departments. We map
Princeton's units onto the platform's ``School`` model as:
  - School of Engineering and Applied Science (SEAS — Division IV, a real dean-led school)
  - Princeton School of Public and International Affairs (SPIA — a real dean-led school)
  - The Humanities (Division I — incl. the School of Architecture)
  - The Social Sciences (Division II)
  - The Natural Sciences (Division III)

The program set is the FULL published catalog: all 37 undergraduate concentrations
(A.B. / B.S.E., from Princeton's official "Areas of Study" + Admission "Degrees &
Departments" pages) and every degree-granting Graduate School field of study
(Ph.D. fields plus the professional/terminal master's — MPA, MPP, M.Arch, M.Fin,
M.S.E./M.Eng — from the Graduate School "Fields of Study" listing). Graduate
certificate-only areas (Statistics & Machine Learning, Hellenic Studies) and
joint-only add-ons (Interdisciplinary Humanities) are excluded because they grant no
standalone degree. Every program carries its ``delivery_format`` (Princeton's degrees
are residential / ``in_person``).

Every node also carries ``content_sources`` so its Events & Updates tab populates:
the institution, every school, and every program point at Princeton's official news
RSS (``/news/feed/all`` — RSS 2.0 with ``<enclosure>`` cover images) filtered by
node-relevant ``keywords`` (the MIT/MBAn pattern), plus the official social handles.
Princeton publishes no public university-wide events iCalendar (its event feeds sit
behind NetID at ``my.princeton.edu``), so ``events_feed`` is honestly omitted rather
than guessed; Updates still populate from the verified news feed.

It **flushes but does not commit** — the caller (the Alembic data migration, the CLI
script, or the dev seed) owns the transaction. It is a **no-op** (returns ``False``)
when Princeton is absent, so it is safe to run against a fresh or CI database.
Re-running is safe: units key off ``(institution_id, name)`` and programs off ``slug``;
stale rows are reconciled without breaking foreign keys.

Every figure traces to a public, citable source; anything that could not be verified
from a first-party or two-independent-source basis is **omitted** (recorded in the
relevant ``_standard.omitted`` list), never guessed. Computer Science is the
most-enriched flagship program (its real research areas, faculty, class profile and
aggregated reviews); the breadth-first catalog carries verified basics on every other
program with deeper fields omitted-pending for resume runs.
"""

from __future__ import annotations

# ruff: noqa: E501
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

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
            "label": "Princeton University — Areas of Study (full catalog)",
            "url": "https://www.princeton.edu/academics/areas-of-study",
        },
        {
            "label": "Princeton Graduate School — Fields of Study",
            "url": "https://gradschool.princeton.edu/academics/degrees-requirements/fields-study",
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
    "Chartered in 1746 as the College of New Jersey and renamed Princeton University "
    "in 1896, Princeton is a private Ivy League research university in Princeton, New "
    "Jersey. It is distinctively small for its stature — about 5,800 undergraduates and "
    "3,300 graduate students, some 9,100 in all — and pairs a deep commitment to "
    "undergraduate teaching with a 5:1 student-faculty ratio and 1,313 faculty.\n\n"
    "Princeton's faculty are organized into four academic divisions: the humanities, the "
    "social sciences, the natural sciences, and engineering and applied science. Two "
    "dean-led professional schools sit alongside them — the School of Engineering and "
    "Applied Science (founded 1921) and the School of Public and International Affairs "
    "(founded 1930) — and undergraduates earn the A.B. or the B.S.E. across 37 academic "
    "concentrations, while the Graduate School awards the Ph.D. and professional master's "
    "degrees across more than forty fields of study. The university manages the Princeton "
    "Plasma Physics Laboratory, a U.S. Department of Energy national laboratory, and is "
    "home to the Princeton Neuroscience Institute and the Lewis-Sigler Institute for "
    "Integrative Genomics.\n\n"
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
            "Affairs, the Master in Public Policy and the Ph.D. It fully funds all of its "
            "MPA, MPP and PhD students."
        ),
    },
    {
        "name": _HUM,
        "sort_order": 3,
        "description": (
            "Division I of Princeton's faculty, the humanities span the departments and "
            "programs in literature, languages, history of art, music, philosophy, "
            "religion, architecture and the classical and modern world. (Per the Office "
            "of the Dean of the Faculty, the divisions group departments for faculty "
            "representation and are not administrative units.)"
        ),
    },
    {
        "name": _SOC,
        "sort_order": 4,
        "description": (
            "Division II of Princeton's faculty, the social sciences span anthropology, "
            "economics, history, politics, sociology, population studies and the School "
            "of Public and International Affairs — studying human behavior, institutions "
            "and society with both quantitative and interpretive methods."
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
_ACADEMICS_URL = "https://www.princeton.edu/academics/areas-of-study"
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
            "School of Architecture",
        ],
        "source": {
            "label": "Princeton — Areas of Study",
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
            "label": "Princeton — Areas of Study",
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
            "label": "Princeton — Areas of Study",
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
# Princeton's official news RSS (Site Builder ``/news/feed/all`` — RSS 2.0 whose items
# carry <enclosure> cover images the ingest captures) is the single verified, fetchable
# feed. Princeton publishes NO public university-wide events iCalendar (its event feeds
# sit behind NetID at my.princeton.edu/ics_helper), so events_feed is honestly omitted
# rather than guessed; the daily ingest still populates each node's Updates from the news
# RSS, filtered by node-relevant keywords (the MIT/MBAn pattern).
_PRINCETON_NEWS_RSS = "https://www.princeton.edu/news/feed/all"
_PRINCETON_NEWS_URL = "https://www.princeton.edu/news"

_SOCIAL_PRINCETON: dict = {
    "instagram": "https://www.instagram.com/princeton/",
    "linkedin": "https://www.linkedin.com/school/princeton-university/",
    "x": "https://x.com/Princeton",
    "youtube": "https://www.youtube.com/princetonuniversity",
    "facebook": "https://www.facebook.com/princetonu",
}

# Institution-wide feed: the all-news Princeton RSS (curated — every item is Princeton
# news) with the official university social handles.
_INSTITUTION_CONTENT: dict = {
    "news_rss": _PRINCETON_NEWS_RSS,
    "news_url": _PRINCETON_NEWS_URL,
    "news_curated": True,
    "social": _SOCIAL_PRINCETON,
}

# Per-unit feed config: the shared Princeton news RSS filtered to unit-relevant items by
# ``keywords`` (no Princeton unit publishes its own fetchable topic RSS, so each inherits
# the university feed + a keyword filter naming the unit's departments).
_SCHOOL_FEED_SPEC: dict[str, list[str]] = {
    _SEAS: [
        "engineering",
        "School of Engineering",
        "Princeton Engineering",
        "computer science",
        "robotics",
    ],
    _SPIA: [
        "School of Public and International Affairs",
        "SPIA",
        "public policy",
        "public affairs",
    ],
    _HUM: [
        "humanities",
        "English",
        "philosophy",
        "history of art",
        "music",
        "classics",
        "architecture",
        "religion",
    ],
    _SOC: [
        "economics",
        "politics",
        "sociology",
        "anthropology",
        "history",
        "social science",
    ],
    _NAT: [
        "physics",
        "chemistry",
        "biology",
        "neuroscience",
        "mathematics",
        "astrophysics",
        "geosciences",
    ],
}


def _school_content(name: str) -> dict:
    """Build a unit's content_sources from the Princeton news RSS + unit keywords + socials."""
    return {
        "news_rss": _PRINCETON_NEWS_RSS,
        "news_url": _PRINCETON_NEWS_URL,
        "news_curated": False,
        "keywords": list(_SCHOOL_FEED_SPEC[name]),
        "social": _SOCIAL_PRINCETON,
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    """Build a program's content_sources from its unit feed, refined by program keywords."""
    base = _school_content(school_name)
    base["keywords"] = list(keywords) or list(_SCHOOL_FEED_SPEC[school_name])
    return base


# ── The program catalog (the FULL published degree catalog, by academic unit) ──
# slug = idempotency key. Each program maps to its owning unit. Undergraduate degrees use
# the generic ``bachelors`` type (A.B./B.S.E. noted in the program name + description);
# graduate degrees use ``masters`` (terminal/professional master's) or ``phd``. Every
# program's website is its official department/program page; ``delivery_format`` is
# in_person (Princeton's degrees are residential).

# Short factual blurbs (what each field studies) — shared between a field's undergraduate
# concentration and its doctoral program so descriptions stay DRY and program-specific.
_BLURB: dict[str, str] = {
    "computer-science": (
        "Princeton's flagship and largest major, spanning theory, systems, AI and machine "
        "learning across the department's thirteen official research areas"
    ),
    "orfe": "optimization, probability, statistics and financial mathematics for decisions under uncertainty",
    "mae": "mechanics, dynamics, propulsion, robotics and aerospace systems",
    "ece": "circuits, devices, signals, computer architecture and photonics",
    "cee": "structures, mechanics, environmental engineering and sustainable infrastructure",
    "cbe": "reaction engineering, thermodynamics, materials and bioengineering",
    "public-affairs": "policy analysis grounded in the social sciences, with policy task forces and junior seminars",
    "african-american-studies": "the history, politics, culture and social life of people of African descent",
    "architecture": "the design, history and theory of the built environment",
    "art-archaeology": "the history of art and archaeology from antiquity to the present",
    "classics": "the languages, literature, history and philosophy of the ancient Greek and Roman worlds",
    "comparative-literature": "literature across languages, national traditions and media",
    "east-asian-studies": "the languages, history and cultures of China, Japan and Korea",
    "english": "literatures in English, literary criticism and creative writing",
    "french-italian": "French and Italian language, literature and culture",
    "german": "German language, literature, philosophy and intellectual history",
    "linguistics": "the scientific study of language — phonology, syntax, semantics and psycholinguistics",
    "music": "musical composition, history, theory and performance",
    "near-eastern-studies": "the languages, history, religions and politics of the Near East",
    "philosophy": "logic, ethics, metaphysics, epistemology and the history of philosophy",
    "religion": "the comparative and historical study of the world's religious traditions",
    "slavic": "Russian and other Slavic languages, literatures and cultures",
    "spanish-portuguese": "the languages, literatures and cultures of the Spanish- and Portuguese-speaking world",
    "anthropology": "the comparative study of human societies, cultures and institutions",
    "economics": "microeconomics, macroeconomics and econometrics",
    "history": "the human past across periods, regions and methods",
    "politics": "American, comparative and international politics and political theory",
    "sociology": "social structure, inequality, institutions and social change",
    "astrophysical-sciences": "stars, galaxies, cosmology and the physics of the universe",
    "chemistry": "organic, inorganic, physical and biological chemistry",
    "eeb": "organisms, populations, ecosystems and evolution",
    "geosciences": "the Earth's structure, climate history and surface processes",
    "mathematics": "analysis, algebra, geometry, topology and number theory",
    "molecular-biology": "biochemistry, genetics, genomics, cell and developmental biology",
    "neuroscience": "the molecular, cellular, systems and computational study of the brain",
    "physics": "from particles and fields to condensed matter, biophysics and cosmology",
    "psychology": "cognition, perception, development, social behavior and systems neuroscience",
    # graduate-only fields
    "pacm": "interdisciplinary applied mathematics, numerical analysis and mathematical modeling across science and engineering",
    "aos": "the dynamics, physics and chemistry of the atmosphere, oceans and climate",
    "biophysics": "quantitative and physical approaches to biological systems at the Lewis-Sigler Institute",
    "plasma-physics": "the physics of plasmas and fusion energy, in partnership with the Princeton Plasma Physics Laboratory",
    "qcb": "genomics, systems biology and computational approaches to living systems at the Lewis-Sigler Institute",
    "population-studies": "demography, health and the social and economic dynamics of populations at the Office of Population Research",
    "history-of-science": "the history of science, medicine and technology",
    "music-composition": "original musical composition and the creation of new work",
    "musicology": "the historical and critical study of music",
    "materials-science": "the structure, properties and processing of advanced materials",
    "quantum-science": "the science and engineering of quantum information, devices and materials",
}

# Undergraduate concentrations (37). Tuple: (slug, school, name, degree_label, dept_url,
# blurb_key). Princeton awards the A.B. for all non-engineering concentrations and the
# B.S.E. for the six engineering departments (Computer Science is offered as both).
_UG_SPECS: list[tuple] = [
    # School of Engineering and Applied Science (B.S.E.; CS also A.B.)
    ("princeton-computer-science-bs", _SEAS, "Computer Science", "A.B. or B.S.E.",
     "https://www.cs.princeton.edu/", "computer-science"),
    ("princeton-operations-research-bs", _SEAS, "Operations Research and Financial Engineering",
     "B.S.E.", "https://orfe.princeton.edu/", "orfe"),
    ("princeton-mechanical-engineering-bs", _SEAS, "Mechanical and Aerospace Engineering",
     "B.S.E.", "https://mae.princeton.edu/", "mae"),
    ("princeton-electrical-engineering-bs", _SEAS, "Electrical and Computer Engineering",
     "B.S.E.", "https://ece.princeton.edu/", "ece"),
    ("princeton-civil-engineering-bs", _SEAS, "Civil and Environmental Engineering",
     "B.S.E.", "https://cee.princeton.edu/", "cee"),
    ("princeton-chemical-engineering-bs", _SEAS, "Chemical and Biological Engineering",
     "B.S.E.", "https://cbe.princeton.edu/", "cbe"),
    # School of Public and International Affairs (A.B.)
    ("princeton-public-affairs-ab", _SPIA, "Public and International Affairs", "A.B.",
     "https://spia.princeton.edu/undergraduate-program", "public-affairs"),
    # The Humanities (A.B.)
    ("princeton-african-american-studies-ab", _HUM, "African American Studies", "A.B.",
     "https://aas.princeton.edu/", "african-american-studies"),
    ("princeton-architecture-ab", _HUM, "Architecture", "A.B.",
     "https://soa.princeton.edu/", "architecture"),
    ("princeton-art-archaeology-ab", _HUM, "Art and Archaeology", "A.B.",
     "https://artandarchaeology.princeton.edu/", "art-archaeology"),
    ("princeton-classics-ab", _HUM, "Classics", "A.B.",
     "https://classics.princeton.edu/", "classics"),
    ("princeton-comparative-literature-ab", _HUM, "Comparative Literature", "A.B.",
     "https://complit.princeton.edu/", "comparative-literature"),
    ("princeton-east-asian-studies-ab", _HUM, "East Asian Studies", "A.B.",
     "https://eas.princeton.edu/", "east-asian-studies"),
    ("princeton-english-bs", _HUM, "English", "A.B.",
     "https://english.princeton.edu/", "english"),
    ("princeton-french-italian-ab", _HUM, "French and Italian", "A.B.",
     "https://fit.princeton.edu/", "french-italian"),
    ("princeton-german-ab", _HUM, "German", "A.B.",
     "https://german.princeton.edu/", "german"),
    ("princeton-linguistics-ab", _HUM, "Linguistics", "A.B.",
     "https://linguistics.princeton.edu/", "linguistics"),
    ("princeton-music-ab", _HUM, "Music", "A.B.",
     "https://music.princeton.edu/", "music"),
    ("princeton-near-eastern-studies-ab", _HUM, "Near Eastern Studies", "A.B.",
     "https://nes.princeton.edu/", "near-eastern-studies"),
    ("princeton-philosophy-bs", _HUM, "Philosophy", "A.B.",
     "https://philosophy.princeton.edu/", "philosophy"),
    ("princeton-religion-ab", _HUM, "Religion", "A.B.",
     "https://religion.princeton.edu/", "religion"),
    ("princeton-slavic-ab", _HUM, "Slavic Languages and Literatures", "A.B.",
     "https://slavic.princeton.edu/", "slavic"),
    ("princeton-spanish-portuguese-ab", _HUM, "Spanish and Portuguese", "A.B.",
     "https://spo.princeton.edu/", "spanish-portuguese"),
    # The Social Sciences (A.B.)
    ("princeton-anthropology-bs", _SOC, "Anthropology", "A.B.",
     "https://anthropology.princeton.edu/", "anthropology"),
    ("princeton-economics-bs", _SOC, "Economics", "A.B.",
     "https://economics.princeton.edu/", "economics"),
    ("princeton-history-bs", _SOC, "History", "A.B.",
     "https://history.princeton.edu/", "history"),
    ("princeton-politics-bs", _SOC, "Politics", "A.B.",
     "https://politics.princeton.edu/", "politics"),
    ("princeton-sociology-bs", _SOC, "Sociology", "A.B.",
     "https://sociology.princeton.edu/", "sociology"),
    # The Natural Sciences (A.B.)
    ("princeton-astrophysical-sciences-ab", _NAT, "Astrophysical Sciences", "A.B.",
     "https://web.astro.princeton.edu/", "astrophysical-sciences"),
    ("princeton-chemistry-bs", _NAT, "Chemistry", "A.B.",
     "https://chemistry.princeton.edu/", "chemistry"),
    ("princeton-eeb-bs", _NAT, "Ecology and Evolutionary Biology", "A.B.",
     "https://eeb.princeton.edu/", "eeb"),
    ("princeton-geosciences-ab", _NAT, "Geosciences", "A.B.",
     "https://geosciences.princeton.edu/", "geosciences"),
    ("princeton-mathematics-bs", _NAT, "Mathematics", "A.B.",
     "https://www.math.princeton.edu/", "mathematics"),
    ("princeton-molecular-biology-bs", _NAT, "Molecular Biology", "A.B.",
     "https://molbio.princeton.edu/", "molecular-biology"),
    ("princeton-neuroscience-bs", _NAT, "Neuroscience", "A.B.",
     "https://pni.princeton.edu/", "neuroscience"),
    ("princeton-physics-bs", _NAT, "Physics", "A.B.",
     "https://phy.princeton.edu/", "physics"),
    ("princeton-psychology-bs", _NAT, "Psychology", "A.B.",
     "https://psychology.princeton.edu/", "psychology"),
]

# Graduate degree programs (Graduate School fields of study). Tuple:
# (slug, school, name, degree_type, duration_months, dept_url, blurb_key_or_None, desc_override_or_None).
# Ph.D. programs are fully funded by Princeton; professional master's carry published
# tuition (SPIA's MPA/MPP are fully funded). blurb_key reuses the shared _BLURB; where a
# program needs a bespoke line, desc_override is given.
_GRAD_SPECS: list[tuple] = [
    # ── School of Engineering and Applied Science — Ph.D. ──
    ("princeton-cbe-phd", _SEAS, "Chemical and Biological Engineering (Ph.D.)", "phd", 60,
     "https://cbe.princeton.edu/", "cbe", None),
    ("princeton-cee-phd", _SEAS, "Civil and Environmental Engineering (Ph.D.)", "phd", 60,
     "https://cee.princeton.edu/", "cee", None),
    ("princeton-cs-phd", _SEAS, "Computer Science (Ph.D.)", "phd", 60,
     "https://www.cs.princeton.edu/grad", "computer-science", None),
    ("princeton-ece-phd", _SEAS, "Electrical and Computer Engineering (Ph.D.)", "phd", 60,
     "https://ece.princeton.edu/", "ece", None),
    ("princeton-mae-phd", _SEAS, "Mechanical and Aerospace Engineering (Ph.D.)", "phd", 60,
     "https://mae.princeton.edu/", "mae", None),
    ("princeton-orfe-phd", _SEAS, "Operations Research and Financial Engineering (Ph.D.)", "phd", 60,
     "https://orfe.princeton.edu/", "orfe", None),
    ("princeton-materials-science-phd", _SEAS, "Materials Science and Engineering (Ph.D.)", "phd", 60,
     "https://materials.princeton.edu/", "materials-science", None),
    ("princeton-quantum-science-phd", _SEAS, "Quantum Science and Engineering (Ph.D.)", "phd", 60,
     "https://quantum.princeton.edu/", "quantum-science", None),
    # ── School of Engineering and Applied Science — professional master's (M.S.E./M.Eng.) ──
    ("princeton-cbe-mse", _SEAS, "Chemical and Biological Engineering (M.S.E. / M.Eng.)", "masters", 24,
     "https://cbe.princeton.edu/", None,
     "Graduate master's program (M.S.E. or M.Eng.) in chemical and biological engineering — advanced coursework with a research thesis (M.S.E.) or professional non-thesis track (M.Eng.)."),
    ("princeton-cee-mse", _SEAS, "Civil and Environmental Engineering (M.S.E. / M.Eng.)", "masters", 24,
     "https://cee.princeton.edu/", None,
     "Graduate master's program (M.S.E. or M.Eng.) in civil and environmental engineering — advanced coursework with a research thesis (M.S.E.) or professional non-thesis track (M.Eng.)."),
    ("princeton-cs-mse", _SEAS, "Computer Science (M.S.E.)", "masters", 24,
     "https://www.cs.princeton.edu/grad", None,
     "Graduate master's program (M.S.E.) in computer science — advanced coursework and research, with an optional non-thesis M.Eng. track."),
    ("princeton-ece-mse", _SEAS, "Electrical and Computer Engineering (M.Eng.)", "masters", 24,
     "https://ece.princeton.edu/", None,
     "Professional master's program (M.Eng.) in electrical and computer engineering — advanced coursework across circuits, devices, signals and computer architecture."),
    ("princeton-mae-mse", _SEAS, "Mechanical and Aerospace Engineering (M.S.E. / M.Eng.)", "masters", 24,
     "https://mae.princeton.edu/", None,
     "Graduate master's program (M.S.E. or M.Eng.) in mechanical and aerospace engineering — advanced coursework with a research thesis (M.S.E.) or professional non-thesis track (M.Eng.)."),
    ("princeton-orfe-mse", _SEAS, "Operations Research and Financial Engineering (M.S.E.)", "masters", 24,
     "https://orfe.princeton.edu/", None,
     "Graduate master's program (M.S.E.) in operations research and financial engineering — optimization, probability, statistics and financial mathematics."),
    # ── Bendheim Center for Finance (interdisciplinary; grouped under Social Sciences) ──
    ("princeton-finance-mfin", _SOC, "Master in Finance (M.Fin.)", "masters", 24,
     "https://bcf.princeton.edu/academic-programs/master-in-finance/", None,
     "The Bendheim Center for Finance Master in Finance (M.Fin.) — a quantitative, four-semester degree in financial and monetary economics with analytical and computational methods."),
    # ── School of Public and International Affairs — MPP + Ph.D. (MPA modeled separately) ──
    ("princeton-public-affairs-mpp", _SPIA, "Master in Public Policy (MPP)", "masters", 12,
     "https://spia.princeton.edu/graduate-admissions/master-public-policy", None,
     "The one-year Master in Public Policy — a fully-funded mid-career degree for experienced professionals in public service."),
    ("princeton-public-affairs-phd", _SPIA, "Public Affairs (Ph.D.)", "phd", 60,
     "https://spia.princeton.edu/graduate-admissions/phd-program", None,
     "The Ph.D. in Public Affairs — fully-funded doctoral training in policy-relevant social science (economics, politics, sociology, demography and security studies)."),
    # ── The Humanities — Ph.D. (+ Architecture M.Arch) ──
    ("princeton-art-archaeology-phd", _HUM, "Art and Archaeology (Ph.D.)", "phd", 60,
     "https://artandarchaeology.princeton.edu/", "art-archaeology", None),
    ("princeton-classics-phd", _HUM, "Classics (Ph.D.)", "phd", 60,
     "https://classics.princeton.edu/", "classics", None),
    ("princeton-comparative-literature-phd", _HUM, "Comparative Literature (Ph.D.)", "phd", 60,
     "https://complit.princeton.edu/", "comparative-literature", None),
    ("princeton-east-asian-studies-phd", _HUM, "East Asian Studies (Ph.D.)", "phd", 60,
     "https://eas.princeton.edu/", "east-asian-studies", None),
    ("princeton-english-phd", _HUM, "English (Ph.D.)", "phd", 60,
     "https://english.princeton.edu/", "english", None),
    ("princeton-french-italian-phd", _HUM, "French and Italian (Ph.D.)", "phd", 60,
     "https://fit.princeton.edu/", "french-italian", None),
    ("princeton-german-phd", _HUM, "German (Ph.D.)", "phd", 60,
     "https://german.princeton.edu/", "german", None),
    ("princeton-history-of-science-phd", _HUM, "History of Science (Ph.D.)", "phd", 60,
     "https://history.princeton.edu/graduate/phd-history-science", "history-of-science", None),
    ("princeton-music-composition-phd", _HUM, "Music Composition (Ph.D.)", "phd", 60,
     "https://music.princeton.edu/", "music-composition", None),
    ("princeton-musicology-phd", _HUM, "Musicology (Ph.D.)", "phd", 60,
     "https://music.princeton.edu/", "musicology", None),
    ("princeton-near-eastern-studies-phd", _HUM, "Near Eastern Studies (Ph.D.)", "phd", 60,
     "https://nes.princeton.edu/", "near-eastern-studies", None),
    ("princeton-philosophy-phd", _HUM, "Philosophy (Ph.D.)", "phd", 60,
     "https://philosophy.princeton.edu/", "philosophy", None),
    ("princeton-religion-phd", _HUM, "Religion (Ph.D.)", "phd", 60,
     "https://religion.princeton.edu/", "religion", None),
    ("princeton-slavic-phd", _HUM, "Slavic Languages and Literatures (Ph.D.)", "phd", 60,
     "https://slavic.princeton.edu/", "slavic", None),
    ("princeton-spanish-portuguese-phd", _HUM, "Spanish and Portuguese (Ph.D.)", "phd", 60,
     "https://spo.princeton.edu/", "spanish-portuguese", None),
    ("princeton-architecture-phd", _HUM, "Architecture (Ph.D.)", "phd", 60,
     "https://soa.princeton.edu/", "architecture", None),
    ("princeton-architecture-march", _HUM, "Architecture (M.Arch.)", "masters", 36,
     "https://soa.princeton.edu/content/master-architecture", None,
     "The professional Master of Architecture (M.Arch.) — a three-year, NAAB-accredited degree in architectural design, history, theory and technology (a two-year post-professional track is also offered)."),
    # ── The Social Sciences — Ph.D. ──
    ("princeton-anthropology-phd", _SOC, "Anthropology (Ph.D.)", "phd", 60,
     "https://anthropology.princeton.edu/", "anthropology", None),
    ("princeton-economics-phd", _SOC, "Economics (Ph.D.)", "phd", 60,
     "https://economics.princeton.edu/", "economics", None),
    ("princeton-history-phd", _SOC, "History (Ph.D.)", "phd", 60,
     "https://history.princeton.edu/", "history", None),
    ("princeton-politics-phd", _SOC, "Politics (Ph.D.)", "phd", 60,
     "https://politics.princeton.edu/", "politics", None),
    ("princeton-population-studies-phd", _SOC, "Population Studies (Ph.D.)", "phd", 60,
     "https://opr.princeton.edu/", "population-studies", None),
    ("princeton-sociology-phd", _SOC, "Sociology (Ph.D.)", "phd", 60,
     "https://sociology.princeton.edu/", "sociology", None),
    # ── The Natural Sciences — Ph.D. ──
    ("princeton-pacm-phd", _NAT, "Applied and Computational Mathematics (Ph.D.)", "phd", 60,
     "https://www.pacm.princeton.edu/", "pacm", None),
    ("princeton-astrophysical-sciences-phd", _NAT, "Astrophysical Sciences (Ph.D.)", "phd", 60,
     "https://web.astro.princeton.edu/", "astrophysical-sciences", None),
    ("princeton-aos-phd", _NAT, "Atmospheric and Oceanic Sciences (Ph.D.)", "phd", 60,
     "https://aos.princeton.edu/", "aos", None),
    ("princeton-biophysics-phd", _NAT, "Biophysics (Ph.D.)", "phd", 60,
     "https://lsi.princeton.edu/education/graduate-program-biophysics", "biophysics", None),
    ("princeton-chemistry-phd", _NAT, "Chemistry (Ph.D.)", "phd", 60,
     "https://chemistry.princeton.edu/", "chemistry", None),
    ("princeton-eeb-phd", _NAT, "Ecology and Evolutionary Biology (Ph.D.)", "phd", 60,
     "https://eeb.princeton.edu/", "eeb", None),
    ("princeton-geosciences-phd", _NAT, "Geosciences (Ph.D.)", "phd", 60,
     "https://geosciences.princeton.edu/", "geosciences", None),
    ("princeton-mathematics-phd", _NAT, "Mathematics (Ph.D.)", "phd", 60,
     "https://www.math.princeton.edu/", "mathematics", None),
    ("princeton-molecular-biology-phd", _NAT, "Molecular Biology (Ph.D.)", "phd", 60,
     "https://molbio.princeton.edu/", "molecular-biology", None),
    ("princeton-neuroscience-phd", _NAT, "Neuroscience (Ph.D.)", "phd", 60,
     "https://pni.princeton.edu/", "neuroscience", None),
    ("princeton-physics-phd", _NAT, "Physics (Ph.D.)", "phd", 60,
     "https://phy.princeton.edu/", "physics", None),
    ("princeton-plasma-physics-phd", _NAT, "Plasma Physics (Ph.D.)", "phd", 60,
     "https://plasma.princeton.edu/", "plasma-physics", None),
    ("princeton-psychology-phd", _NAT, "Psychology (Ph.D.)", "phd", 60,
     "https://psychology.princeton.edu/", "psychology", None),
    ("princeton-qcb-phd", _NAT, "Quantitative and Computational Biology (Ph.D.)", "phd", 60,
     "https://lsi.princeton.edu/education/quantitative-computational-biology-graduate-program",
     "qcb", None),
]

_AB_DESC_SUFFIX = {
    "A.B.": "Princeton awards the A.B.",
    "B.S.E.": "Princeton awards the B.S.E.",
    "A.B. or B.S.E.": "Princeton awards the A.B. or the B.S.E.",
}


def _build_programs() -> list[dict]:
    out: list[dict] = []
    for slug, school, name, degree_label, url, blurb_key in _UG_SPECS:
        out.append(
            {
                "slug": slug,
                "school": school,
                "program_name": name,
                "degree_type": "bachelors",
                "duration_months": 48,
                "delivery_format": "in_person",
                "website_url": url,
                "description": f"{name} — {_BLURB[blurb_key]}. {_AB_DESC_SUFFIX[degree_label]}.",
            }
        )
    for slug, school, name, degree_type, dur, url, blurb_key, desc_override in _GRAD_SPECS:
        if desc_override is not None:
            desc = desc_override
        else:
            desc = (
                f"Doctoral (Ph.D.) program in {name.split(' (')[0].lower()} — "
                f"{_BLURB[blurb_key]}, with original dissertation research. Princeton fully "
                f"funds all Ph.D. students."
            )
        out.append(
            {
                "slug": slug,
                "school": school,
                "program_name": name,
                "degree_type": degree_type,
                "duration_months": dur,
                "delivery_format": "in_person",
                "website_url": url,
                "description": desc,
            }
        )
    return out


# The SPIA MPA keeps its original slug + bespoke description (fully-funded two-year degree).
PROGRAMS: list[dict] = _build_programs() + [
    {
        "slug": "princeton-public-affairs-mpa",
        "school": _SPIA,
        "program_name": "Master in Public Affairs (MPA)",
        "degree_type": "masters",
        "duration_months": 24,
        "delivery_format": "in_person",
        "website_url": "https://spia.princeton.edu/graduate-admissions/master-public-affairs",
        "description": (
            "The two-year Master in Public Affairs — a fully-funded graduate degree in "
            "policy analysis and leadership for public service."
        ),
    },
]

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

# Full official program names (program-page title); equal to the program name here.
_FULL_NAME_BY_SLUG: dict[str, str] = {p["slug"]: p["program_name"] for p in PROGRAMS}

# Official program/department home pages (built from the specs; verified at author time).
_WEBSITE_BY_SLUG: dict[str, str] = {p["slug"]: p["website_url"] for p in PROGRAMS}

# Per-program feed keywords (department/program-naming terms) so the shared Princeton news
# RSS is filtered to program-relevant items. Derived from the program's blurb key / name.
_PROGRAM_KEYWORDS: dict[str, list[str]] = {
    "computer-science": ["computer science", "Princeton CS"],
    "orfe": ["operations research", "financial engineering", "ORFE"],
    "mae": ["mechanical engineering", "aerospace"],
    "ece": ["electrical engineering", "computer engineering"],
    "cee": ["civil engineering", "environmental engineering"],
    "cbe": ["chemical engineering", "biological engineering"],
    "public-affairs": ["public affairs", "public policy", "SPIA"],
    "african-american-studies": ["African American Studies"],
    "architecture": ["architecture", "School of Architecture"],
    "art-archaeology": ["art and archaeology", "art history"],
    "classics": ["classics", "classical"],
    "comparative-literature": ["comparative literature"],
    "east-asian-studies": ["East Asian"],
    "english": ["English literature", "creative writing"],
    "french-italian": ["French", "Italian"],
    "german": ["German"],
    "linguistics": ["linguistics"],
    "music": ["music"],
    "music-composition": ["music", "composition", "composer"],
    "musicology": ["music", "musicology"],
    "near-eastern-studies": ["Near Eastern"],
    "philosophy": ["philosophy"],
    "religion": ["religion"],
    "slavic": ["Slavic", "Russian"],
    "spanish-portuguese": ["Spanish", "Portuguese"],
    "anthropology": ["anthropology"],
    "economics": ["economics", "economist"],
    "history": ["history", "historian"],
    "history-of-science": ["history of science"],
    "politics": ["politics", "political science"],
    "population-studies": ["population", "demography"],
    "sociology": ["sociology"],
    "astrophysical-sciences": ["astrophysics", "astronomy", "astronomer"],
    "chemistry": ["chemistry", "chemist"],
    "eeb": ["ecology", "evolutionary biology"],
    "geosciences": ["geosciences", "geology", "climate"],
    "mathematics": ["mathematics", "mathematician"],
    "molecular-biology": ["molecular biology", "genomics"],
    "neuroscience": ["neuroscience", "brain"],
    "physics": ["physics", "physicist"],
    "psychology": ["psychology", "psychologist"],
    "pacm": ["applied mathematics", "computational"],
    "aos": ["atmospheric", "oceanic", "climate"],
    "biophysics": ["biophysics"],
    "plasma-physics": ["plasma physics", "fusion"],
    "qcb": ["computational biology", "genomics"],
    "materials-science": ["materials science"],
    "quantum-science": ["quantum"],
}

# Map each program slug → its keyword list (via the spec's blurb key where available).
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {}
for _slug, _sch, _name, _dl, _url, _bk in _UG_SPECS:
    _PROGRAM_KEYWORDS_BY_SLUG[_slug] = _PROGRAM_KEYWORDS.get(_bk, [_name])
for _slug, _sch, _name, _dt, _dur, _url, _bk, _ov in _GRAD_SPECS:
    if _bk and _bk in _PROGRAM_KEYWORDS:
        _PROGRAM_KEYWORDS_BY_SLUG[_slug] = _PROGRAM_KEYWORDS[_bk]
    else:
        _PROGRAM_KEYWORDS_BY_SLUG[_slug] = [_name.split(" (")[0]]
_PROGRAM_KEYWORDS_BY_SLUG["princeton-public-affairs-mpa"] = ["public affairs", "public policy", "SPIA"]
_PROGRAM_KEYWORDS_BY_SLUG["princeton-finance-mfin"] = ["finance", "Bendheim"]
_PROGRAM_KEYWORDS_BY_SLUG["princeton-public-affairs-mpp"] = ["public policy", "SPIA"]
_PROGRAM_KEYWORDS_BY_SLUG["princeton-public-affairs-phd"] = ["public affairs", "public policy", "SPIA"]

# ── Who-it's-for + highlights (catalog baselines) ──────────────────────────
_WHO_BASELINE = (
    "Academically exceptional students seeking a research-rich education at a university "
    "uniquely devoted to undergraduate teaching, with full-need financial aid met by grants."
)
_HL_BASELINE = ["Ivy League", "5:1 student-faculty ratio", "Need-met-with-grants aid"]
_WHO_GRAD_BASELINE = (
    "Prospective doctoral and master's students seeking research-intensive graduate study "
    "at a small, research-first Ivy League university; Princeton fully funds its Ph.D. students."
)
_HL_GRAD_BASELINE = ["Research-first graduate study", "Fully-funded Ph.D.", "World-class faculty"]
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
# Princeton undergraduate cost (College Scorecard, UNITID 186131). The SPIA MPA/MPP are
# fully funded, and Princeton fully funds all Ph.D. students.
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
    },
    "princeton-public-affairs-mpp": {
        "tuition_usd": _TUITION_GRAD,
        "total_cost_of_attendance": _TUITION_GRAD,
        "funded": True,
        "note": (
            "Princeton SPIA fully funds all admitted MPP students — 100% of tuition and "
            "required fees plus a living stipend. Published full-time graduate tuition shown."
        ),
        "source": "Princeton SPIA — Graduate Funding",
        "source_url": "https://spia.princeton.edu/graduate-admissions",
        "year": "2024-25",
    },
}


def _cost_for(spec: dict) -> dict:
    """Cost block for a program: undergrad COA, per-slug override, funded Ph.D., or master's."""
    slug = spec["slug"]
    if slug in _COST_BY_SLUG:
        return dict(_COST_BY_SLUG[slug])
    if spec["degree_type"] == "bachelors":
        return {
            "tuition_usd": _TUITION_UG,
            "total_cost_of_attendance": _UNDERGRAD_COA,
            "avg_net_price": _AVG_NET_PRICE,
            "breakdown": {"tuition": _TUITION_UG, "total_cost_of_attendance": _UNDERGRAD_COA},
            "funded": False,
            "note": (
                "Published undergraduate cost of attendance and average net price. "
                "Princeton is need-blind and meets 100% of demonstrated need with grants "
                "rather than loans, so most families pay far less than the sticker price "
                "(average net price ≈ $6,100)."
            ),
            "source": "U.S. Dept. of Education College Scorecard (UNITID 186131)",
            "source_url": "https://collegescorecard.ed.gov/school/?186131",
            "year": "2024-25",
        }
    if spec["degree_type"] == "phd":
        return {
            "tuition_usd": _TUITION_GRAD,
            "total_cost_of_attendance": _TUITION_GRAD,
            "funded": True,
            "note": (
                "Princeton fully funds all Ph.D. students — a full tuition fellowship plus "
                "a stipend for the regular period of enrollment. Published full-time "
                "graduate tuition shown."
            ),
            "source": "Princeton Graduate School — Financial Support",
            "source_url": "https://gradschool.princeton.edu/costs-funding",
            "year": "2024-25",
        }
    # Professional / terminal master's (M.S.E./M.Eng./M.Arch/M.Fin): published tuition.
    return {
        "tuition_usd": _TUITION_GRAD,
        "total_cost_of_attendance": _TUITION_GRAD,
        "funded": False,
        "note": (
            "Published full-time Princeton Graduate School tuition. Funding for "
            "professional master's programs varies by program and year."
        ),
        "source": "Princeton Graduate School — Tuition & Fees",
        "source_url": "https://gradschool.princeton.edu/costs-funding",
        "year": "2024-25",
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

# Graduate admission via the Princeton Graduate School application (Ph.D. + master's,
# incl. SPIA MPA/MPP). The Graduate School is the common application portal for all fields.
_REQ_GRAD = {
    "materials": [
        {"name": "Princeton Graduate School online application", "required": True},
        {"name": "Statement of academic purpose", "required": True},
        {"name": "Three letters of recommendation", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Résumé / CV", "required": True},
        {
            "name": "GRE scores",
            "required": False,
            "note": "Required only by some fields; many programs are GRE-optional.",
        },
        {"name": "$75 application fee; fee waivers available", "required": True},
    ],
    "deadlines": [
        {"round": "Most fall-entry fields", "date": "Early-to-mid December (varies by field)"},
    ],
    "recommendations": {
        "required": 3,
        "note": "Three letters of recommendation submitted through the Graduate School application.",
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": True,
            "note": "Required for applicants whose native language is not English (waivers may apply).",
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Princeton Graduate School — How to Apply",
                "url": "https://gradschool.princeton.edu/admission/how-apply",
            }
        ],
    },
    "source": "Princeton Graduate School — Admission",
    "source_url": "https://gradschool.princeton.edu/admission/how-apply",
}


def _requirements_for(spec: dict) -> dict:
    """Pick the admissions requirement set for a program by degree type."""
    if spec["degree_type"] in {"masters", "phd"}:
        return dict(_REQ_GRAD)
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
        # Every unit gets a working feed (Princeton news RSS filtered to unit-relevant
        # items by keywords) so its Events & Updates tab populates — overwriting any stale
        # value on a pre-existing row.
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
        # Every program carries a working feed: the Princeton news RSS filtered to
        # program-relevant items by keywords (the MBAn pattern) so its Events & Updates
        # populate — never null.
        kw = _PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(_SCHOOL_FEED_SPEC[spec["school"]])
        p.content_sources = _program_content(spec["school"], kw)
        # Cost: undergrad COA / funded Ph.D. / professional master's / per-slug override.
        cost = _cost_for(spec)
        p.tuition = cost.get("tuition_usd")
        p.cost_data = cost
        # Admissions: undergraduate or graduate set by degree type.
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
        # Application deadline (upcoming undergraduate Regular Decision closes Jan 1;
        # graduate fall-entry deadlines cluster in December).
        p.application_deadline = (
            date(2026, 12, 1) if spec["degree_type"] in {"masters", "phd"} else date(2027, 1, 1)
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
