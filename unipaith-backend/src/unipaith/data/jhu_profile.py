"""Johns Hopkins University — canonical gold-standard profile (data + idempotent apply).

Real, sourced data only. Mirrors the shape of ``mit_profile`` / ``yale_profile``: per-
university constants + an idempotent ``apply(session)`` that enriches the Johns Hopkins
institution row, upserts its real degree-granting schools, and builds its published degree
catalog (breadth-first verified basics + a working ``content_sources`` feed on every node),
then reconciles any legacy/seed rows.

Every value ships only when verified against an authoritative source; anything that could
not be verified is recorded in the relevant node's ``_standard.omitted`` (never guessed).

Primary sources (IPEDS UNITID 162928):
  • U.S. Dept. of Education College Scorecard (UNITID 162928) — admit rate, SAT, net price,
    cost of attendance, Pell/loan rates, institution 10-yr median earnings.
  • NCES College Navigator / IPEDS (UNITID 162928) — applicants/admits/enrolled, retention,
    six-year graduation rate, instructional faculty counts, undergraduate demographics.
  • JHU Admissions "Fast Facts", JHU "About"/History, the JHU Academic Catalogue
    (e-catalogue.jhu.edu) — the authoritative degree catalog for every school.
  • QS World University Rankings 2026, Times Higher Education 2026, U.S. News 2026.

The daily content-ingest reads ``news_rss`` (an RSS feed), an optional ``events_feed``
(an iCalendar URL), ``keywords`` (word-boundary relevance filter) and ``news_curated``
(keep every item) from each node's ``content_sources``. Johns Hopkins publishes a single
university-wide news RSS (the Hub, ``https://hub.jhu.edu/feed/`` — verified live RSS 2.0);
its per-school news sites and the events calendar sit behind a bot challenge and expose no
confirmable static feed, so every school and program here uses the verified Hub feed filtered
by node ``keywords`` (the MIT/MBAn pattern) and ``events_feed`` is honestly omitted.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Johns Hopkins University"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-11"


def _standard(omitted: list[str] | None = None) -> dict:
    """The per-node provenance stamp the routine writes onto every enriched node."""
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }


# Institution-level required fields that could not be verified from a citable, university-wide
# source and are therefore honestly omitted rather than guessed.
_OMITTED_INSTITUTION = [
    # Johns Hopkins reports career/first-destination outcomes per school via interactive
    # dashboards (imagine.jhu.edu, the Bloomberg School dashboard, SAIS, etc.); there is no
    # single university-wide, rank-ordered "top employer industries" list published, so the
    # institution-level value is omitted rather than synthesized from one school's data.
    "school_outcomes.top_employer_industries",
]

# ── Institution-level data ────────────────────────────────────────────────
# Rankings are stored as {rank, year} objects. Each is quoted from the official ranking body
# (or JHU's own first-party announcement) for the 2026 editions.
RANKING_DATA: dict = {
    "ownership_type": "private",
    # Accredited by the Middle States Commission on Higher Education.
    "accreditor": "MSCHE",
    # Carnegie basic classification (R1).
    "carnegie_classification": "Doctoral Universities: Very High Research Activity",
    # QS World University Rankings 2026: #24 worldwide.
    "qs_world_university_rankings": {"rank": 24, "year": 2026},
    # Times Higher Education World University Rankings 2026: #16 (JHU first-party announcement).
    "times_higher_education": {"rank": 16, "year": 2026},
    # U.S. News Best Colleges (National Universities) 2026: #7 nationally.
    "us_news_national": {"rank": 7, "year": 2026},
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below is complete.
# Figures are College Scorecard (UNITID 162928) cross-checked against NCES College Navigator
# (IPEDS, Fall 2024) and JHU's official "Fast Facts".
SCHOOL_OUTCOMES: dict = {
    # College Scorecard overall admission rate.
    "admit_rate": 0.0644,
    # College Scorecard average annual net price (private).
    "avg_net_price": 18809,
    # College Scorecard institution-wide median earnings 10 years after entry.
    "median_earnings_10yr": 87555,
    # College Scorecard four-year completion rate (150% of normal time).
    "completion_rate_4yr_150pct": 0.9378,
    # NCES College Navigator (IPEDS): first-year retention (full-time) = 98%.
    "retention_rate_first_year": 0.98,
    # NCES College Navigator (IPEDS): overall six-year graduation rate = 94%.
    "graduation_rate_6yr": 0.94,
    "financial_aid": {
        # College Scorecard: 19.49% Pell, 9.31% federal loans.
        "pell_grant_rate": 0.1949,
        "federal_loan_rate": 0.0931,
        # JHU 2025-26 published total cost of attendance (apply.jhu.edu "Estimate Your
        # College Costs"); College Scorecard reports $85,947 for its reporting year.
        "cost_of_attendance": 92000,
    },
    # Undergraduate race/ethnicity (NCES College Navigator / IPEDS, Fall 2024).
    "demographics": {
        "white": 0.22,
        "black": 0.09,
        "hispanic": 0.18,
        "asian": 0.28,
        "two_or_more": 0.06,
        "international": 0.15,
    },
    # SAT/ACT 25th-75th percentiles of enrolled first-years (College Scorecard, UNITID 162928).
    "test_scores": {
        "sat_reading_25_75": [740, 770],
        "sat_math_25_75": [780, 800],
        "act_25_75": [34, 36],
    },
    # Homewood campus, Baltimore, Maryland.
    "location": {"lat": 39.3289, "lng": -76.6205},
    "campus_basics": {"location": "Baltimore, Maryland"},
    "scale": {
        # NCES College Navigator (IPEDS, Fall 2024): 4,052 full-time + 161 part-time
        # instructional faculty = 4,213 total instructional faculty.
        "faculty_count": 4213,
        # JHU Fast Facts: 6:1 undergraduate student-faculty ratio.
        "student_faculty_ratio": "6:1",
        # JHU endowment $13.06 billion at fiscal year-end 2024 (FY2024).
        "endowment_usd": 13060000000,
    },
    # JHU Admissions Fast Facts: "Employed Full-Time or in Graduate School Within Six Months
    # of Graduation" = 91%.
    "employed_or_continuing_ed": 0.91,
    "research": {
        "labs": [
            "Johns Hopkins Applied Physics Laboratory (APL)",
            "Space Telescope Science Institute (STScI) — JWST & Hubble science operations",
            "Sidney Kimmel Comprehensive Cancer Center (NCI-designated)",
            "Institute for NanoBioTechnology (INBT)",
            "SNF Agora Institute",
            "Laboratory for Computational Sensing & Robotics (LCSR)",
        ],
        "areas": [
            "Medicine & public health",
            "Biomedical & life sciences",
            "Space science & astrophysics",
            "Engineering & applied physics",
            "International affairs & policy",
            "Data science & artificial intelligence",
        ],
        "lab_links": {
            "Johns Hopkins Applied Physics Laboratory (APL)": "https://www.jhuapl.edu/",
            "Space Telescope Science Institute (STScI) — JWST & Hubble science operations": (
                "https://www.stsci.edu/"
            ),
            "Sidney Kimmel Comprehensive Cancer Center (NCI-designated)": (
                "https://www.hopkinsmedicine.org/kimmel-cancer-center"
            ),
            "Institute for NanoBioTechnology (INBT)": "https://inbt.jhu.edu/",
            "SNF Agora Institute": "https://snfagora.jhu.edu/",
            "Laboratory for Computational Sensing & Robotics (LCSR)": "https://lcsr.jhu.edu/",
        },
    },
    "campus_life": {
        # The Blue Jays compete in NCAA Division III (Centennial Conference); men's and
        # women's lacrosse compete in Division I (Big Ten Conference).
        "athletics_division": (
            "NCAA Division III (Centennial Conference); men's & women's lacrosse Division I "
            "(Big Ten Conference)"
        ),
        "mascot": "Johns Hopkins Blue Jays",
        "housing": "91% of first-year students live on campus (Homewood)",
        "resources": [
            {"label": "Johns Hopkins Blue Jays Athletics", "url": "https://hopkinssports.com/"},
            {"label": "Athletics & Recreation at Johns Hopkins", "url": "https://www.jhu.edu/life/athletics/"},
            {"label": "Imagine — Life Design Lab (career outcomes)", "url": "https://imagine.jhu.edu/"},
        ],
    },
    "flagship": {
        # NCES College Navigator (IPEDS, Fall 2024): total enrollment 30,210.
        "enrollment_total": 30210,
        # NCES College Navigator (IPEDS, Fall 2024) first-year admissions cycle.
        "applicants": 45895,
        "admits": 2754,
        "admissions_cycle": "Entering class fall 2024 (NCES College Navigator / IPEDS)",
        # Founded 1876 — the first research university in the United States.
        "founded_year": 1876,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Johns Hopkins, UNITID 162928)",
            "url": "https://collegescorecard.ed.gov/school/?162928",
        },
        {
            "label": "NCES College Navigator — Johns Hopkins University (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=162928",
        },
        {
            "label": "Johns Hopkins University Admissions — Fast Facts",
            "url": "https://apply.jhu.edu/fast-facts/",
        },
        {
            "label": "Johns Hopkins University — History & Mission",
            "url": "https://www.jhu.edu/about/history/",
        },
        {
            "label": "Johns Hopkins leads nation in research spending for 44th consecutive year",
            "url": "https://hub.jhu.edu/2024/01/05/nsf-higher-education-research-spending-2022/",
        },
        {
            "label": "QS World University Rankings 2026 — Johns Hopkins University",
            "url": "https://www.topuniversities.com/universities/johns-hopkins-university",
        },
        {
            "label": (
                "Johns Hopkins No. 16 in Times Higher Education World University Rankings 2026"
            ),
            "url": "https://hub.jhu.edu/2025/10/09/johns-hopkins-times-higher-education-world-university-rankings/",
        },
        {
            "label": "Johns Hopkins No. 7 in U.S. News Best Colleges 2026 (National Universities)",
            "url": "https://hub.jhu.edu/2025/09/23/us-news-best-colleges-rankings-2025/",
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it "Undergraduates"); the
# total (30,210) lives in flagship.enrollment_total. 6,356 = NCES undergraduate enrollment.
UNDERGRAD_COUNT = 6356

DESCRIPTION = (
    "Johns Hopkins University is a private research university in Baltimore, Maryland, "
    "founded in 1876 as the first research university in the United States — modeled by "
    "founding president Daniel Coit Gilman on the German graduate-research ideal and endowed "
    "by a then-record $7 million bequest from the merchant Johns Hopkins. It enrolls about "
    "6,400 undergraduates and roughly 24,000 graduate and professional students, some 30,200 "
    "in all, taught by more than 4,200 faculty across a 6:1 undergraduate student-faculty "
    "ratio.\n\n"
    "The university is organized into ten divisions: the Krieger School of Arts and Sciences "
    "and the Whiting School of Engineering on the Homewood campus; the School of Medicine, "
    "School of Nursing, and the Bloomberg School of Public Health (the world's first school "
    "of public health) in East Baltimore; the Paul H. Nitze School of Advanced International "
    "Studies (SAIS) in Washington; the Carey Business School, the School of Education, and the "
    "Peabody Institute; plus the new School of Government and Policy. Its degree catalog spans "
    "residential bachelor's, master's, and doctoral programs alongside an extensive set of "
    "online and part-time professional master's degrees (Engineering for Professionals, the "
    "Krieger Advanced Academic Programs, and online public-health and business degrees).\n\n"
    "Johns Hopkins has led all U.S. universities in research and development spending for 44 "
    "consecutive years, directing a record $3.4 billion in fiscal 2022 — a total that includes "
    "its renowned Applied Physics Laboratory, builder of NASA missions such as the Parker "
    "Solar Probe and DART. Its research is anchored by the Applied Physics Laboratory, the "
    "Space Telescope Science Institute (science operations for the Hubble and James Webb space "
    "telescopes), and the NCI-designated Sidney Kimmel Comprehensive Cancer Center.\n\n"
    "Hopkins ranks among the best universities in the world: No. 7 among national universities "
    "by U.S. News, No. 16 in the world by Times Higher Education, and No. 24 by QS. It admits "
    "about 6.4% of first-year applicants, retains 98% of first-year students, and graduates "
    "94% within six years. Its average net price is roughly $18,800 a year, and beginning in "
    "2026-27 it is tuition-free for undergraduates from families earning up to $200,000."
)

# ── The real degree-granting schools (display order) ───────────────────────
_KRIEGER = "Krieger School of Arts and Sciences"
_WHITING = "Whiting School of Engineering"
_MED = "Johns Hopkins University School of Medicine"
_NURSING = "Johns Hopkins School of Nursing"
_SPH = "Johns Hopkins Bloomberg School of Public Health"
_SAIS = "Paul H. Nitze School of Advanced International Studies"
_PEABODY = "Peabody Institute"
_CAREY = "Johns Hopkins Carey Business School"
_EDUCATION = "Johns Hopkins University School of Education"

SCHOOLS: list[dict] = [
    {
        "name": _KRIEGER,
        "sort_order": 1,
        "description": (
            "The Zanvyl Krieger School of Arts and Sciences, the university's original 1876 "
            "faculty, is the home of the liberal arts and sciences at Johns Hopkins. It spans "
            "the humanities, social sciences, and natural sciences across roughly two dozen "
            "departments, awards the B.A. and B.S. across the Homewood undergraduate majors, "
            "and grants residential master's and Ph.D. degrees as well as an extensive set of "
            "part-time and online master's degrees through its Advanced Academic Programs."
        ),
    },
    {
        "name": _WHITING,
        "sort_order": 2,
        "description": (
            "The G.W.C. Whiting School of Engineering, established in 1919 and named in 1979, "
            "educates engineers on the Homewood campus and online. It awards the B.S. across "
            "its engineering majors, residential master's and Ph.D. degrees, the Doctor of "
            "Engineering, and a large catalog of online, part-time master's degrees through "
            "Engineering for Professionals — taught in partnership with the Applied Physics "
            "Laboratory."
        ),
    },
    {
        "name": _MED,
        "sort_order": 3,
        "description": (
            "The Johns Hopkins University School of Medicine, founded in 1893, pioneered the "
            "integration of medical education with bedside teaching and research. Alongside the "
            "M.D. and the Medical Scientist Training Program (M.D.-Ph.D.), it grants a large "
            "portfolio of biomedical Ph.D. and master's degrees in fields from neuroscience and "
            "human genetics to biomedical engineering, medical physics, and the history of "
            "medicine."
        ),
    },
    {
        "name": _NURSING,
        "sort_order": 4,
        "description": (
            "The Johns Hopkins School of Nursing, with roots to 1889, is consistently ranked "
            "among the nation's top nursing schools. It awards the Master of Science in Nursing, "
            "the Doctor of Nursing Practice across advanced-practice and executive tracks, and "
            "the Ph.D. in Nursing."
        ),
    },
    {
        "name": _SPH,
        "sort_order": 5,
        "description": (
            "The Johns Hopkins Bloomberg School of Public Health, founded in 1916, is the "
            "oldest and largest school of public health in the world. It awards the Master of "
            "Public Health (on-campus, part-time, and online), the Doctor of Public Health, and "
            "departmental M.H.S., Sc.M., M.S.P.H., and Ph.D. degrees across ten departments "
            "spanning biostatistics, epidemiology, environmental health, health policy, mental "
            "health, and international health."
        ),
    },
    {
        "name": _SAIS,
        "sort_order": 6,
        "description": (
            "The Paul H. Nitze School of Advanced International Studies (SAIS), founded in 1943 "
            "and part of Johns Hopkins since 1950, is a leading graduate school of international "
            "relations with campuses in Washington, Bologna, and Nanjing. It awards a suite of "
            "master's degrees in international relations, economics and finance, global policy, "
            "and strategy, plus the Ph.D. in International Studies."
        ),
    },
    {
        "name": _PEABODY,
        "sort_order": 7,
        "description": (
            "The Peabody Institute, founded in 1857 and affiliated with Johns Hopkins since "
            "1977, is the oldest conservatory in the United States. Its Conservatory awards the "
            "Bachelor of Music, the Master of Music, master's degrees in audio sciences, and the "
            "Doctor of Musical Arts across performance, composition, conducting, music "
            "education, and computer/recording arts."
        ),
    },
    {
        "name": _CAREY,
        "sort_order": 8,
        "description": (
            "The Johns Hopkins Carey Business School, established in 2007, offers business "
            "education built on the university's strengths in health, technology, and the "
            "public good. It awards the full-time, flexible, and executive MBA and a set of "
            "specialized Master of Science degrees in finance, marketing, health care "
            "management, business analytics and AI, information systems, and real estate."
        ),
    },
    {
        "name": _EDUCATION,
        "sort_order": 9,
        "description": (
            "The Johns Hopkins University School of Education, a separate school since 2007 with "
            "teacher-education roots to 1909, prepares educators and education leaders. It awards "
            "master's degrees in counseling, special education, and education (including online "
            "learning-design and health-professions education), the Doctor of Education (online), "
            "and the Ph.D. in Education."
        ),
    },
]

_SCHOOL_WEBSITE: dict[str, str] = {
    _KRIEGER: "https://krieger.jhu.edu/",
    _WHITING: "https://engineering.jhu.edu/",
    _MED: "https://www.hopkinsmedicine.org/som",
    _NURSING: "https://nursing.jhu.edu/",
    _SPH: "https://publichealth.jhu.edu/",
    _SAIS: "https://sais.jhu.edu/",
    _PEABODY: "https://peabody.jhu.edu/",
    _CAREY: "https://carey.jhu.edu/",
    _EDUCATION: "https://education.jhu.edu/",
}

# ── School "About" detail (founded · leadership · research centers · source) ──
# Deans verified individually for 2025-26 (several changed recently). Faculty rosters are
# omitted school-wide (no citable current roster pulled this pass — only deans are named);
# research_centers are omitted for the conservatory and the two professional schools whose
# named centers were not verified to a first-party page.
_ABOUT_DETAIL: dict[str, dict] = {
    _KRIEGER: {
        "founded": 1876,
        "leadership": (
            "Christopher S. Celenza — James B. Knapp Dean of the Krieger School of Arts and "
            "Sciences"
        ),
        "research_centers": [
            "SNF Agora Institute",
            "Center for Africana Studies",
            "Institute for the American Constitutional Heritage",
        ],
        "source": {
            "label": "Krieger School of Arts and Sciences — Dean",
            "url": "https://krieger.jhu.edu/directory/christopher-s-celenza/",
        },
    },
    _WHITING: {
        "founded": 1919,
        "leadership": (
            "T.E. (Ed) Schlesinger — Benjamin T. Rome Dean of the Whiting School of Engineering"
        ),
        "research_centers": [
            "Laboratory for Computational Sensing & Robotics (LCSR)",
            "Institute for NanoBioTechnology (INBT)",
            "Malone Center for Engineering in Healthcare",
            "Institute for Assured Autonomy",
        ],
        "source": {
            "label": "Whiting School of Engineering — Centers & Institutes",
            "url": "https://engineering.jhu.edu/research/centers-institutes/",
        },
    },
    _MED: {
        "founded": 1893,
        "leadership": (
            "Theodore L. DeWeese — Dean of the Medical Faculty and CEO of Johns Hopkins Medicine"
        ),
        "research_centers": [
            "Sidney Kimmel Comprehensive Cancer Center",
            "Institute for Cell Engineering",
            "Department of Genetic Medicine",
        ],
        "source": {
            "label": "Johns Hopkins Medicine — Leadership (Dean/CEO)",
            "url": "https://www.hopkinsmedicine.org/about/leadership/theodore-deweese",
        },
    },
    _NURSING: {
        "founded": 1889,
        "leadership": (
            "Sarah L. Szanton — Patricia M. Davidson Dean of the Johns Hopkins School of Nursing"
        ),
        "research_centers": [
            "Center for Innovative Care in Aging",
            "Center for Infectious Disease and Nursing Innovation",
        ],
        "source": {
            "label": "Johns Hopkins School of Nursing — Dean",
            "url": "https://nursing.jhu.edu/about-us/dean/",
        },
    },
    _SPH: {
        "founded": 1916,
        "leadership": (
            "Keshia M. Pollack Porter — Dean of the Johns Hopkins Bloomberg School of Public "
            "Health (effective August 2025)"
        ),
        "research_centers": [
            "Johns Hopkins Center for a Livable Future",
            "International Vaccine Access Center (IVAC)",
            "Johns Hopkins Center for Communication Programs",
        ],
        "source": {
            "label": "Bloomberg School of Public Health — Dean announcement",
            "url": "https://hub.jhu.edu/2025/05/27/bloomberg-school-of-public-health-dean-keshia-pollack-porter/",
        },
    },
    _SAIS: {
        "founded": 1943,
        "leadership": (
            "James B. Steinberg — Dean of the Paul H. Nitze School of Advanced International "
            "Studies"
        ),
        "research_centers": [
            "Henry A. Kissinger Center for Global Affairs",
            "Foreign Policy Institute",
        ],
        "source": {
            "label": "Johns Hopkins SAIS — School Leadership",
            "url": "https://sais.jhu.edu/about-us/school-leadership",
        },
    },
    _PEABODY: {
        "founded": 1857,
        "leadership": "Fred Bronstein — Dean of the Peabody Institute",
        # The Peabody Institute is a conservatory + preparatory; it has no named research
        # centers, so research_centers is honestly omitted (see _ABOUT_OMITTED).
        "source": {
            "label": "Peabody Institute — Our Leadership (Dean)",
            "url": "https://peabody.jhu.edu/explore-peabody/our-leadership/fred-bronstein/",
        },
    },
    _CAREY: {
        "founded": 2007,
        "leadership": "Alexander Triantis — Dean of the Johns Hopkins Carey Business School",
        # Carey's named research centers were not verified to a first-party page this pass;
        # research_centers is omitted rather than guessed (see _ABOUT_OMITTED).
        "source": {
            "label": "Johns Hopkins Carey Business School — Leadership",
            "url": "https://carey.jhu.edu/about/leadership",
        },
    },
    _EDUCATION: {
        "founded": 2007,
        "leadership": "Christopher C. Morphew — Dean of the Johns Hopkins School of Education",
        # The School of Education's named research centers were not verified to a first-party
        # page this pass; research_centers is omitted rather than guessed (see _ABOUT_OMITTED).
        "source": {
            "label": "Johns Hopkins School of Education — Dean",
            "url": "https://education.jhu.edu/about/leadership/dean-christopher-morphew/",
        },
    },
}

_FACULTY_OMIT = ["about_detail.faculty"]
_ABOUT_OMITTED: dict[str, list[str]] = {
    _KRIEGER: list(_FACULTY_OMIT),
    _WHITING: list(_FACULTY_OMIT),
    _MED: list(_FACULTY_OMIT),
    _NURSING: list(_FACULTY_OMIT),
    _SPH: list(_FACULTY_OMIT),
    _SAIS: list(_FACULTY_OMIT),
    _PEABODY: [*_FACULTY_OMIT, "about_detail.research_centers"],
    _CAREY: [*_FACULTY_OMIT, "about_detail.research_centers"],
    _EDUCATION: [*_FACULTY_OMIT, "about_detail.research_centers"],
}

# ── Feeds (content_sources) ────────────────────────────────────────────────
# The Johns Hopkins university news RSS — the Hub — is verified live (RSS 2.0 with real
# <item> entries). Per-school news sites and the events calendar are bot-protected and expose
# no confirmable static feed, so every school and program consumes the Hub feed filtered by
# node keywords; events_feed is omitted (no public iCalendar found).
_HUB_RSS = "https://hub.jhu.edu/feed/"

# Official university social handles (verified via brand.jhu.edu social-media directory).
_SOCIAL_JHU = {
    "instagram": "https://www.instagram.com/johnshopkinsu/",
    "linkedin": "https://www.linkedin.com/school/johns-hopkins-university/",
    "x": "https://twitter.com/JohnsHopkins",
    "youtube": "https://www.youtube.com/johnshopkins",
    "facebook": "https://www.facebook.com/johnshopkinsuniversity",
}
# Confirmed school-specific handles merged over the university defaults (a school page also
# carries the university channels). Only individually confirmed handles are overridden.
_SOCIAL_BY_SCHOOL: dict[str, dict] = {
    _WHITING: {
        **_SOCIAL_JHU,
        "facebook": "https://www.facebook.com/jhuengineering",
        "linkedin": "https://www.linkedin.com/school/johns-hopkins-whiting-school-of-engineering/",
    },
    _SPH: {**_SOCIAL_JHU, "instagram": "https://www.instagram.com/johnshopkinssph/"},
    _SAIS: {**_SOCIAL_JHU, "x": "https://twitter.com/SAISHopkins"},
    _CAREY: {**_SOCIAL_JHU, "youtube": "https://www.youtube.com/@JHUCarey"},
    _EDUCATION: {**_SOCIAL_JHU, "facebook": "https://www.facebook.com/JHUeducation"},
}

# Per-school keyword filters (school-naming terms) applied to the shared Hub feed.
_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _KRIEGER: ["Krieger", "Arts and Sciences"],
    _WHITING: ["Whiting", "engineering", "Engineering for Professionals"],
    _MED: ["School of Medicine", "Johns Hopkins Medicine", "medical"],
    _NURSING: ["School of Nursing", "nursing", "nurse"],
    _SPH: ["Bloomberg School", "public health", "epidemiology"],
    _SAIS: ["SAIS", "international studies", "international affairs"],
    _PEABODY: ["Peabody", "Conservatory", "music"],
    _CAREY: ["Carey Business School", "Carey", "MBA"],
    _EDUCATION: ["School of Education", "education", "teaching"],
}


def _school_content(name: str) -> dict:
    """Build a school's content_sources from the verified Hub RSS + school keywords + socials."""
    return {
        "news_rss": _HUB_RSS,
        "news_url": "https://hub.jhu.edu",
        "news_curated": False,
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": _SOCIAL_BY_SCHOOL.get(name, _SOCIAL_JHU),
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    """Build a program's content_sources from its school feed, refined by program keywords."""
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


# Institution-wide feed: the verified Hub RSS (curated — every item is JHU news) with the
# official university social handles. events_feed omitted (no public iCalendar).
_INSTITUTION_CONTENT: dict = {
    "news_rss": _HUB_RSS,
    "news_url": "https://hub.jhu.edu",
    "news_curated": True,
    "social": _SOCIAL_JHU,
}

# ── Full published degree catalog (breadth-first verified basics) ───────────
# Each row = (program_name, degree_type, school, delivery_format). Every program traces to the
# JHU Academic Catalogue (e-catalogue.jhu.edu) and the owning school's official program pages.
# Deeper fields (tracks/outcomes/faculty/reviews/exact tuition) are omitted-pending per
# _program_standard and deepened on resume runs. degree_type ∈ {bachelors, masters, phd,
# professional}; delivery_format ∈ {in_person, online, hybrid}.

# Undergraduate majors — (name, credential, school). credential ∈ {ba, bs}. All residential.
_UG_MAJORS: list[tuple[str, str, str]] = [
    # Krieger School of Arts and Sciences
    ("Africana Studies", "ba", _KRIEGER),
    ("Anthropology", "ba", _KRIEGER),
    ("Archaeology", "ba", _KRIEGER),
    ("Behavioral Biology", "ba", _KRIEGER),
    ("Biology", "ba", _KRIEGER),
    ("Biophysics", "bs", _KRIEGER),
    ("Chemistry", "bs", _KRIEGER),
    ("Classics", "ba", _KRIEGER),
    ("Cognitive Science", "ba", _KRIEGER),
    ("Critical Diaspora Studies", "ba", _KRIEGER),
    ("Earth and Planetary Sciences", "ba", _KRIEGER),
    ("East Asian Studies", "ba", _KRIEGER),
    ("Economics", "ba", _KRIEGER),
    ("English", "ba", _KRIEGER),
    ("Environmental Science", "bs", _KRIEGER),
    ("Environmental Studies", "ba", _KRIEGER),
    ("Film and Media Studies", "ba", _KRIEGER),
    ("French", "ba", _KRIEGER),
    ("German", "ba", _KRIEGER),
    ("History", "ba", _KRIEGER),
    ("History of Art", "ba", _KRIEGER),
    ("History of Science, Medicine, and Technology", "ba", _KRIEGER),
    ("Interdisciplinary Studies", "ba", _KRIEGER),
    ("International Studies", "ba", _KRIEGER),
    ("Italian", "ba", _KRIEGER),
    ("Latin American, Caribbean, and Latinx Studies", "ba", _KRIEGER),
    ("Mathematics", "ba", _KRIEGER),
    ("Medicine, Science, and the Humanities", "ba", _KRIEGER),
    ("Molecular and Cellular Biology", "bs", _KRIEGER),
    ("Moral and Political Economy", "ba", _KRIEGER),
    ("Natural Sciences", "ba", _KRIEGER),
    ("Near Eastern Studies", "ba", _KRIEGER),
    ("Neuroscience", "bs", _KRIEGER),
    ("Philosophy", "ba", _KRIEGER),
    ("Physics", "bs", _KRIEGER),
    ("Political Science", "ba", _KRIEGER),
    ("Psychology", "ba", _KRIEGER),
    ("Public Health Studies", "ba", _KRIEGER),
    ("Romance Languages", "ba", _KRIEGER),
    ("Sociology", "ba", _KRIEGER),
    ("Spanish", "ba", _KRIEGER),
    ("Writing Seminars", "ba", _KRIEGER),
    # Whiting School of Engineering
    ("Applied Mathematics and Statistics", "bs", _WHITING),
    ("Biomedical Engineering", "bs", _WHITING),
    ("Chemical and Biomolecular Engineering", "bs", _WHITING),
    ("Civil Engineering", "bs", _WHITING),
    ("Computer Engineering", "bs", _WHITING),
    ("Computer Science", "bs", _WHITING),
    ("Electrical Engineering", "bs", _WHITING),
    ("Engineering Mechanics", "bs", _WHITING),
    ("Environmental Engineering", "bs", _WHITING),
    ("General Engineering", "ba", _WHITING),
    ("Materials Science and Engineering", "bs", _WHITING),
    ("Mechanical Engineering", "bs", _WHITING),
    ("Systems Engineering", "bs", _WHITING),
]

# Residential graduate degrees — (name, degree_type, school, credential_code). in_person.
# credential_code keeps slugs unique where a name recurs at different degree levels.
_GRAD_RESIDENTIAL: list[tuple[str, str, str, str]] = [
    # Whiting — residential master's
    ("Applied Mathematics and Statistics", "masters", _WHITING, "mse"),
    ("Data Science", "masters", _WHITING, "ms"),
    ("Financial Mathematics", "masters", _WHITING, "mse"),
    ("Biomedical Engineering", "masters", _WHITING, "mse"),
    ("Bioengineering Innovation and Design", "masters", _WHITING, "mse"),
    ("Chemical and Biomolecular Engineering", "masters", _WHITING, "mse"),
    ("Civil Engineering", "masters", _WHITING, "mse"),
    ("Systems Engineering", "masters", _WHITING, "ms"),
    ("Computer Science", "masters", _WHITING, "mse"),
    ("Electrical and Computer Engineering", "masters", _WHITING, "mse"),
    ("Geography and Environmental Engineering", "masters", _WHITING, "ma"),
    ("Geography and Environmental Engineering", "masters", _WHITING, "ms"),
    ("Geography and Environmental Engineering", "masters", _WHITING, "mse"),
    ("Occupational and Environmental Hygiene", "masters", _WHITING, "ms"),
    ("Materials Science and Engineering", "masters", _WHITING, "mse"),
    ("Mechanical Engineering", "masters", _WHITING, "mse"),
    ("Robotics", "masters", _WHITING, "mse"),
    ("Security Informatics", "masters", _WHITING, "ms"),
    ("Engineering Management", "masters", _WHITING, "ms"),
    ("Global Innovation and Leadership Through Engineering", "masters", _WHITING, "ms"),
    # Whiting — residential doctoral
    ("Applied Mathematics and Statistics", "phd", _WHITING, "phd"),
    ("Biomedical Engineering", "phd", _WHITING, "phd"),
    ("Chemical and Biomolecular Engineering", "phd", _WHITING, "phd"),
    ("Civil and Systems Engineering", "phd", _WHITING, "phd"),
    ("Computer Science", "phd", _WHITING, "phd"),
    ("Electrical and Computer Engineering", "phd", _WHITING, "phd"),
    ("Geography and Environmental Engineering", "phd", _WHITING, "phd"),
    ("Materials Science and Engineering", "phd", _WHITING, "phd"),
    ("Mechanical Engineering", "phd", _WHITING, "phd"),
    ("Engineering, Doctor of Engineering", "phd", _WHITING, "engd"),
    # Krieger — residential master's
    ("Writing Seminars (M.F.A.)", "masters", _KRIEGER, "mfa"),
    ("Cognitive Science", "masters", _KRIEGER, "ma"),
    ("Economics", "masters", _KRIEGER, "ma"),
    ("Biophysical Chemistry and Design for Biotechnology", "masters", _KRIEGER, "ms"),
    # Krieger — residential doctoral
    ("Anthropology", "phd", _KRIEGER, "phd"),
    ("Biology", "phd", _KRIEGER, "phd"),
    ("Biophysics", "phd", _KRIEGER, "phd"),
    ("Chemistry", "phd", _KRIEGER, "phd"),
    ("Chemical Biology", "phd", _KRIEGER, "phd"),
    ("Classics", "phd", _KRIEGER, "phd"),
    ("Cognitive Science", "phd", _KRIEGER, "phd"),
    ("Earth and Planetary Sciences", "phd", _KRIEGER, "phd"),
    ("Economics", "phd", _KRIEGER, "phd"),
    ("English", "phd", _KRIEGER, "phd"),
    ("French", "phd", _KRIEGER, "phd"),
    ("German", "phd", _KRIEGER, "phd"),
    ("Italian", "phd", _KRIEGER, "phd"),
    ("Spanish", "phd", _KRIEGER, "phd"),
    ("History", "phd", _KRIEGER, "phd"),
    ("History of Art", "phd", _KRIEGER, "phd"),
    ("History of Science and Technology", "phd", _KRIEGER, "phd"),
    ("Humanistic Studies", "phd", _KRIEGER, "phd"),
    ("Mathematics", "phd", _KRIEGER, "phd"),
    ("Near Eastern Studies", "phd", _KRIEGER, "phd"),
    ("Philosophy", "phd", _KRIEGER, "phd"),
    ("Physics", "phd", _KRIEGER, "phd"),
    ("Astronomy and Astrophysics", "phd", _KRIEGER, "phd"),
    ("Political Science", "phd", _KRIEGER, "phd"),
    ("Psychology", "phd", _KRIEGER, "phd"),
    ("Sociology", "phd", _KRIEGER, "phd"),
    # School of Medicine — professional & combined
    ("Doctor of Medicine (M.D.)", "professional", _MED, "md"),
    ("M.D.-Ph.D. (Medical Scientist Training Program)", "professional", _MED, "mdphd"),
    ("M.D.-M.B.A.", "professional", _MED, "mdmba"),
    # School of Medicine — doctoral (biomedical; BME PhD is owned by Whiting above)
    ("Biochemistry, Cellular and Molecular Biology", "phd", _MED, "phd"),
    ("Biological Chemistry", "phd", _MED, "phd"),
    ("Biophysics and Biophysical Chemistry", "phd", _MED, "phd"),
    ("Cellular and Molecular Medicine", "phd", _MED, "phd"),
    ("Cellular and Molecular Physiology", "phd", _MED, "phd"),
    ("Cross-Disciplinary Program in Graduate Biomedical Sciences", "phd", _MED, "phd"),
    ("Functional Anatomy and Evolution", "phd", _MED, "phd"),
    ("Health Sciences Informatics", "phd", _MED, "phd"),
    ("History of Medicine", "phd", _MED, "phd"),
    ("Human Genetics and Genomics", "phd", _MED, "phd"),
    ("Immunology", "phd", _MED, "phd"),
    ("Medical Physics", "phd", _MED, "phd"),
    ("Neuroscience", "phd", _MED, "phd"),
    ("Pathobiology", "phd", _MED, "phd"),
    ("Pharmacology and Molecular Sciences", "phd", _MED, "phd"),
    # School of Medicine — master's
    ("Anatomy Education", "masters", _MED, "ms"),
    ("Applied Health Sciences Informatics", "masters", _MED, "ms"),
    ("Cellular and Molecular Medicine", "masters", _MED, "ms"),
    ("Clinical Anaplastology", "masters", _MED, "ms"),
    ("Health Sciences Informatics", "masters", _MED, "ms"),
    ("Medical and Biological Illustration", "masters", _MED, "ma"),
    ("Medical Physics", "masters", _MED, "ms"),
    # School of Nursing
    ("Master of Science in Nursing: Entry into Nursing", "masters", _NURSING, "msn-entry"),
    ("Master of Science in Nursing: Healthcare Organizational Leadership", "masters", _NURSING,
     "msn-hol"),
    ("Doctor of Nursing Practice (Advanced Practice)", "professional", _NURSING, "dnp-ap"),
    ("Doctor of Nursing Practice (Executive)", "professional", _NURSING, "dnp-exec"),
    ("Ph.D. in Nursing", "phd", _NURSING, "phd"),
    # Bloomberg School of Public Health — schoolwide
    ("Master of Public Health (M.P.H.)", "masters", _SPH, "mph"),
    ("Doctor of Public Health (Dr.P.H.)", "professional", _SPH, "drph"),
    ("Master of Bioethics", "masters", _SPH, "mbe"),
    # Bloomberg SPH — departmental degrees
    ("Biochemistry and Molecular Biology, M.H.S.", "masters", _SPH, "mhs"),
    ("Biochemistry and Molecular Biology, Sc.M.", "masters", _SPH, "scm"),
    ("Biochemistry and Molecular Biology, Ph.D.", "phd", _SPH, "phd"),
    ("Biostatistics, M.H.S.", "masters", _SPH, "mhs"),
    ("Biostatistics, Sc.M.", "masters", _SPH, "scm"),
    ("Biostatistics, Ph.D.", "phd", _SPH, "phd"),
    ("Environmental Health, M.H.S.", "masters", _SPH, "mhs"),
    ("Environmental Health, Sc.M.", "masters", _SPH, "scm"),
    ("Environmental Health, Ph.D.", "phd", _SPH, "phd"),
    ("Toxicology for Human Risk Assessment, M.S.", "masters", _SPH, "ms"),
    ("Epidemiology, M.H.S.", "masters", _SPH, "mhs"),
    ("Epidemiology, Sc.M.", "masters", _SPH, "scm"),
    ("Epidemiology, Ph.D.", "phd", _SPH, "phd"),
    ("Health, Behavior and Society, M.S.P.H.", "masters", _SPH, "msph"),
    ("Health, Behavior and Society, M.H.S.", "masters", _SPH, "mhs"),
    ("Health, Behavior and Society, Ph.D.", "phd", _SPH, "phd"),
    ("Health Administration, M.H.A.", "masters", _SPH, "mha"),
    ("Health Policy, M.S.P.H.", "masters", _SPH, "msph"),
    ("Health Policy and Management, Ph.D.", "phd", _SPH, "phd"),
    ("International Health, M.H.S.", "masters", _SPH, "mhs"),
    ("International Health, M.S.P.H.", "masters", _SPH, "msph"),
    ("International Health, Ph.D.", "phd", _SPH, "phd"),
    ("Mental Health, M.H.S.", "masters", _SPH, "mhs"),
    ("Mental Health, Ph.D.", "phd", _SPH, "phd"),
    ("Molecular Microbiology and Immunology, M.H.S.", "masters", _SPH, "mhs"),
    ("Molecular Microbiology and Immunology, Sc.M.", "masters", _SPH, "scm"),
    ("Molecular Microbiology and Immunology, Ph.D.", "phd", _SPH, "phd"),
    ("Population, Family and Reproductive Health, M.H.S.", "masters", _SPH, "mhs"),
    ("Population, Family and Reproductive Health, M.S.P.H.", "masters", _SPH, "msph"),
    ("Population, Family and Reproductive Health, Ph.D.", "phd", _SPH, "phd"),
    # SAIS — residential master's & doctoral
    ("Master of Arts in International Relations", "masters", _SAIS, "mair"),
    ("Master of Arts in International Affairs", "masters", _SAIS, "maia"),
    ("Master of Arts in International Economics and Finance", "masters", _SAIS, "mief"),
    ("Master of Arts in International Studies", "masters", _SAIS, "mais"),
    ("Master of Arts in Strategy, Cybersecurity, and Intelligence", "masters", _SAIS, "masci"),
    ("Master of Arts in European Public Policy", "masters", _SAIS, "mepp"),
    ("Master of International Public Policy", "masters", _SAIS, "mipp"),
    ("Ph.D. in International Studies", "phd", _SAIS, "phd"),
    # Peabody — residential degrees (diplomas excluded)
    ("Bachelor of Music", "bachelors", _PEABODY, "bm"),
    ("Bachelor of Fine Arts in Dance", "bachelors", _PEABODY, "bfa"),
    ("Master of Music", "masters", _PEABODY, "mm"),
    ("Master of Music in Music Education", "masters", _PEABODY, "mm-mused"),
    ("Master of Arts in Audio Sciences", "masters", _PEABODY, "ma"),
    ("Doctor of Musical Arts", "professional", _PEABODY, "dma"),
    # Carey Business School — residential
    ("Full-Time MBA", "masters", _CAREY, "mba-ft"),
    ("Master of Science in Finance", "masters", _CAREY, "ms-fin"),
    ("Master of Science in Marketing", "masters", _CAREY, "ms-mktg"),
    ("Master of Science in Health Care Management", "masters", _CAREY, "ms-hcm"),
    ("Master of Science in Information Systems and Artificial Intelligence for Business",
     "masters", _CAREY, "ms-isai"),
    ("Master of Science in Real Estate and Infrastructure", "masters", _CAREY, "ms-rei"),
    ("Master of Science in Management", "masters", _CAREY, "ms-mgmt"),
    # School of Education — residential
    ("Master of Science in Counseling", "masters", _EDUCATION, "ms-couns"),
    ("Master of Science in Special Education", "masters", _EDUCATION, "ms-sped"),
    ("Master of Education for Teaching Professionals", "masters", _EDUCATION, "med-teach"),
    ("Master of Science in Education: Educational Studies", "masters", _EDUCATION, "ms-edstudies"),
    ("Ph.D. in Education", "phd", _EDUCATION, "phd"),
]

# Online / hybrid professional master's — (name, school, delivery_format, division_tag).
# division_tag namespaces the slug so online-division programs never collide with residential.
_ONLINE_PROGRAMS: list[tuple[str, str, str, str]] = [
    # Whiting — Engineering for Professionals (online; three with an on-site capstone = hybrid)
    ("Applied and Computational Mathematics", _WHITING, "online", "ep"),
    ("Applied Biomedical Engineering", _WHITING, "online", "ep"),
    ("Applied Physics", _WHITING, "online", "ep"),
    ("Artificial Intelligence", _WHITING, "online", "ep"),
    ("Chemical and Biomolecular Engineering", _WHITING, "online", "ep"),
    ("Civil Engineering", _WHITING, "online", "ep"),
    ("Climate, Energy, and Environmental Sustainability", _WHITING, "online", "ep"),
    ("Computer Science", _WHITING, "online", "ep"),
    ("Cybersecurity", _WHITING, "online", "ep"),
    ("Data Science", _WHITING, "online", "ep"),
    ("Electrical and Computer Engineering", _WHITING, "online", "ep"),
    ("Engineering Management", _WHITING, "online", "ep"),
    ("Environmental Engineering", _WHITING, "online", "ep"),
    ("Environmental Engineering and Science", _WHITING, "online", "ep"),
    ("Environmental Planning and Management", _WHITING, "online", "ep"),
    ("Financial Mathematics", _WHITING, "online", "ep"),
    ("Healthcare Systems Engineering", _WHITING, "online", "ep"),
    ("Industrial and Operations Engineering", _WHITING, "online", "ep"),
    ("Information Systems Engineering", _WHITING, "online", "ep"),
    ("Materials Science and Engineering", _WHITING, "online", "ep"),
    ("Mechanical Engineering", _WHITING, "online", "ep"),
    ("Occupational and Environmental Hygiene", _WHITING, "online", "ep"),
    ("Robotics and Autonomous Systems", _WHITING, "online", "ep"),
    ("Space Systems Engineering", _WHITING, "hybrid", "ep"),
    ("Systems Engineering", _WHITING, "online", "ep"),
    # Krieger — Advanced Academic Programs (online / hybrid, part-time)
    ("Applied Economics", _KRIEGER, "online", "aap"),
    ("Financial Economics", _KRIEGER, "online", "aap"),
    ("Communication", _KRIEGER, "hybrid", "aap"),
    ("Writing", _KRIEGER, "online", "aap"),
    ("Science Writing", _KRIEGER, "online", "aap"),
    ("Master of Liberal Arts", _KRIEGER, "hybrid", "aap"),
    ("Museum Studies", _KRIEGER, "online", "aap"),
    ("Cultural Heritage Management", _KRIEGER, "online", "aap"),
    ("Government", _KRIEGER, "hybrid", "aap"),
    ("Public Management", _KRIEGER, "hybrid", "aap"),
    ("Global Security Studies", _KRIEGER, "hybrid", "aap"),
    ("Nonprofit Management", _KRIEGER, "online", "aap"),
    ("Data Analytics and Policy", _KRIEGER, "online", "aap"),
    ("Intelligence Analysis", _KRIEGER, "hybrid", "aap"),
    ("Organizational Leadership", _KRIEGER, "online", "aap"),
    ("Biotechnology", _KRIEGER, "hybrid", "aap"),
    ("Bioinformatics", _KRIEGER, "online", "aap"),
    ("Individualized Genomics and Health", _KRIEGER, "online", "aap"),
    ("Regulatory Science", _KRIEGER, "online", "aap"),
    ("Regenerative and Stem Cell Technologies", _KRIEGER, "hybrid", "aap"),
    ("Biotechnology Enterprise and Entrepreneurship", _KRIEGER, "online", "aap"),
    ("Environmental Sciences and Policy", _KRIEGER, "online", "aap"),
    ("Energy Policy and Climate", _KRIEGER, "online", "aap"),
    ("Geographic Information Systems", _KRIEGER, "online", "aap"),
    # Bloomberg SPH — online professional master's
    ("Population Health Management (M.A.S.)", _SPH, "online", "online"),
    ("Patient Safety and Healthcare Quality (M.A.S.)", _SPH, "online", "online"),
    ("Spatial Analysis for Public Health (M.A.S.)", _SPH, "online", "online"),
    ("Humanitarian Health (M.A.S.)", _SPH, "online", "online"),
    # Carey — online / hybrid MBA
    ("Flexible MBA", _CAREY, "online", "online"),
    ("Executive MBA", _CAREY, "hybrid", "online"),
    ("Master of Science in Business Analytics and Artificial Intelligence", _CAREY, "hybrid",
     "online"),
    # SAIS — online / executive master's
    ("Master of Arts in Global Policy", _SAIS, "hybrid", "online"),
    ("Master of Arts in Global Risk (Online)", _SAIS, "online", "online"),
    # School of Education — online
    ("Master of Science in Education: Gifted Education", _EDUCATION, "online", "online"),
    ("Master of Education in Learning Design and Technology", _EDUCATION, "online", "online"),
    ("Master of Education in the Health Professions", _EDUCATION, "online", "online"),
    ("Doctor of Education (Online)", _EDUCATION, "professional", "online"),
]


_SLUG_REPL = {"&": "and", "—": " ", "/": " ", "'": "", ".": "", ",": "", "(": "", ")": "", ":": ""}


def _slugify(text_in: str) -> str:
    s = text_in.lower()
    for a, b in _SLUG_REPL.items():
        s = s.replace(a, b)
    return "-".join(s.split())


_DEG_WORD = {
    "bachelors": "bachelor's",
    "masters": "master's",
    "phd": "doctoral (Ph.D.)",
    "professional": "professional",
}
_SCHOOL_SHORT = {
    _KRIEGER: "Krieger School of Arts and Sciences",
    _WHITING: "Whiting School of Engineering",
    _MED: "School of Medicine",
    _NURSING: "School of Nursing",
    _SPH: "Bloomberg School of Public Health",
    _SAIS: "School of Advanced International Studies (SAIS)",
    _PEABODY: "Peabody Institute",
    _CAREY: "Carey Business School",
    _EDUCATION: "School of Education",
}
_DUR_BY_TYPE = {"bachelors": 48, "masters": 24, "phd": 60, "professional": 48}


def _build_catalog() -> list[dict]:
    """Build every program node (verified basics) for Johns Hopkins's published catalog."""
    out: list[dict] = []
    seen: set[str] = set()

    def _add(spec: dict) -> None:
        if spec["slug"] in seen:
            raise ValueError(f"duplicate program slug: {spec['slug']}")
        seen.add(spec["slug"])
        out.append(spec)

    for name, cred, school in _UG_MAJORS:
        label = "B.S." if cred == "bs" else "B.A."
        short = _SCHOOL_SHORT[school]
        _add({
            "slug": f"jhu-{_slugify(name)}-{cred}",
            "school": school,
            "program_name": name,
            "degree_type": "bachelors",
            "duration_months": 48,
            "delivery_format": "in_person",
            "description": (
                f"{name} — an undergraduate {label} major in the Johns Hopkins {short}, on the "
                f"Homewood campus in Baltimore."
            ),
            "keywords": [name],
        })

    for name, dtype, school, cred in _GRAD_RESIDENTIAL:
        short = _SCHOOL_SHORT[school]
        word = _DEG_WORD[dtype]
        _add({
            "slug": f"jhu-{_slugify(name)}-{cred}",
            "school": school,
            "program_name": name,
            "degree_type": dtype,
            "duration_months": _DUR_BY_TYPE[dtype],
            "delivery_format": "in_person",
            "description": (
                f"{name} — a full-time residential {word} program of the Johns Hopkins {short}."
            ),
            "keywords": [name],
        })

    for name, school, fmt, tag in _ONLINE_PROGRAMS:
        short = _SCHOOL_SHORT[school]
        if tag == "ep":
            desc = (
                f"{name} — an online, part-time master's degree offered through Johns Hopkins "
                f"Engineering for Professionals (Whiting School of Engineering)."
            )
        elif tag == "aap":
            mode = "online" if fmt == "online" else "online or on-site"
            desc = (
                f"{name} — a part-time master's degree ({mode}) offered through the Krieger "
                f"School's Advanced Academic Programs."
            )
        else:
            dtype_word = "professional" if fmt == "professional" else "master's"
            desc = (
                f"{name} — an online/part-time {dtype_word} program of the Johns Hopkins {short}."
            )
        dtype = "professional" if fmt == "professional" else "masters"
        deliver = "online" if fmt == "professional" else fmt
        _add({
            "slug": f"jhu-{tag}-{_slugify(name)}",
            "school": school,
            "program_name": name,
            "degree_type": dtype,
            "duration_months": _DUR_BY_TYPE[dtype],
            "delivery_format": deliver,
            "description": desc,
            "keywords": [name],
        })

    return out


PROGRAMS: list[dict] = _build_catalog()
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

# ── Cost / admissions / outcomes baselines ─────────────────────────────────
_UNDERGRAD_COA = 92000
_AVG_NET_PRICE = 18809

# Undergraduate cost record (no exact sticker tuition asserted — JHU is moving to tuition-free
# for families under $200k; the published total cost of attendance and the College Scorecard
# average net price are recorded instead, and cost_data.tuition_usd is omitted with reason).
_UG_COST: dict = {
    "total_cost_of_attendance": _UNDERGRAD_COA,
    "avg_net_price": _AVG_NET_PRICE,
    "breakdown": {"total_cost_of_attendance": _UNDERGRAD_COA},
    "funded": False,
    "note": (
        "Published 2025-26 total cost of attendance with the College Scorecard average net "
        "price. Johns Hopkins meets full demonstrated need and, beginning in 2026-27, is "
        "tuition-free for undergraduates from families earning up to $200,000, so most "
        "families pay far less than the sticker price (average net price ≈ $18,800)."
    ),
    "source": (
        "JHU Admissions — Estimate Your College Costs (2025-26) + College Scorecard (UNITID 162928)"
    ),
    "source_url": "https://apply.jhu.edu/tuition-aid/estimate-your-college-costs/",
}

# Graduate/professional cost record (per-program tuition varies and is published on each
# school's tuition page; a verified per-program figure is not recorded — tuition_usd omitted).
_GRAD_COST: dict = {
    "note": (
        "Tuition for this graduate/professional program varies and is published on the owning "
        "school's official tuition page; a verified per-program figure is not yet recorded here."
    ),
    "source": "Johns Hopkins University Academic Catalogue — Tuition, Fees, and Cost of Attendance",
    "source_url": "https://e-catalogue.jhu.edu/university-wide-policies-information/admission-aid/tuition-fees/",
}

# Institution-wide outcomes fallback (College Scorecard 10-year median earnings, UNITID 162928).
# Per-program employment rate and top industries are not published per major (Hopkins reports
# first-destination outcomes per school via interactive dashboards), so they are omitted.
_OUTCOMES_INSTITUTION = {
    "median_salary": 87555,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry",
    "conditions": (
        "Institution-wide median earnings ten years after entry for federally-aided students "
        "(U.S. Dept. of Education College Scorecard, UNITID 162928); a verified per-program "
        "earnings figure is not recorded."
    ),
    "source": "U.S. Dept. of Education College Scorecard (UNITID 162928)",
    "source_url": "https://collegescorecard.ed.gov/school/?162928",
}

_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application, Coalition Application, or QuestBridge", "required": True},
        {"name": "Johns Hopkins-specific writing supplement", "required": True},
        {"name": "School report + secondary-school transcript", "required": True},
        {"name": "Counselor recommendation", "required": True},
        {"name": "Two teacher recommendations", "required": True},
        {"name": "$70 application fee; need-based fee waivers available", "required": True},
        {
            "name": "Standardized test scores",
            "required": False,
            "note": "Johns Hopkins is test-optional for first-year applicants.",
        },
    ],
    "deadlines": [
        {"round": "Early Decision I", "date": "November 1"},
        {"round": "Early Decision II", "date": "January 2"},
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
        "sources": [
            {"label": "JHU Undergraduate Admissions — Apply", "url": "https://apply.jhu.edu/application-process/"}
        ],
    },
    "source": "Johns Hopkins Undergraduate Admissions",
    "source_url": "https://apply.jhu.edu/application-process/deadlines-decisions/",
}

# Generic Johns Hopkins graduate / professional admission set. Each school administers its own
# admissions; deadlines vary by program, so applicants are pointed to the program's own page.
_REQ_GRAD_GENERIC = {
    "materials": [
        {"name": "Program online application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose / personal statement", "required": True},
        {"name": "Résumé / CV", "required": True},
        {
            "name": "Letters of recommendation",
            "required": True,
            "note": (
                "Most Johns Hopkins graduate and professional programs require two to "
                "three letters."
            ),
        },
        {
            "name": "Standardized test scores (GRE/GMAT)",
            "required": False,
            "note": "Test requirements vary by program (required, optional, or not accepted).",
        },
    ],
    "deadlines": [
        {"round": "Application deadline", "date": "Varies by program — see the program page"},
    ],
    "recommendations": {
        "required": 3,
        "note": (
            "Most Johns Hopkins graduate and professional programs require two to three letters."
        ),
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
        "sources": [
            {
                "label": "Johns Hopkins Academic Catalogue — Admission & Aid",
                "url": "https://e-catalogue.jhu.edu/university-wide-policies-information/admission-aid/",
            }
        ],
    },
    "source": "Johns Hopkins graduate & professional admissions",
    "source_url": "https://e-catalogue.jhu.edu/university-wide-policies-information/admission-aid/",
}


def _requirements_for(spec: dict) -> dict:
    """Pick the admissions requirement set for a program by degree type."""
    if spec["degree_type"] == "bachelors":
        return dict(_REQ_UNDERGRAD)
    return dict(_REQ_GRAD_GENERIC)


# Baseline who-it's-for / highlights (breadth-first; deeper per-program copy is omitted).
_WHO_UG = (
    "Prospective undergraduates seeking a rigorous, research-driven education at a top "
    "national university."
)
_WHO_GRAD = (
    "Prospective graduate and professional students seeking advanced study with leading "
    "faculty at Johns Hopkins."
)
_HL_BASELINE = ["No. 1 in U.S. research spending", "First U.S. research university", "Founded 1876"]


def _program_standard(slug: str) -> dict:
    """Per-program omitted-field list (verified-unavailable / pending-depth), for _standard."""
    omitted = [
        # Johns Hopkins reports first-destination outcomes per school via interactive
        # dashboards, not per major, so program-level employment rate and top industries are
        # not asserted (the institution-wide median earnings is recorded as the outcome).
        "outcomes_data.employment_rate",
        "outcomes_data.top_industries",
        # Deep, individually-sourced program detail is deepened on resume runs; these are
        # recorded as pending rather than guessed.
        "tracks",
        "class_profile.cohort_size",
        "faculty_contacts.lead",
        "external_reviews.summary",
        # No exact per-program sticker tuition is asserted (see _UG_COST / _GRAD_COST notes).
        "cost_data.tuition_usd",
    ]
    return _standard(omitted)


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


# Real Johns Hopkins campus photo (Gilman Hall and the Keyser Quad, Homewood campus) —
# Wikimedia Commons, CC BY 2.0, hotlinkable landscape JPG (verified HTTP 200). Leads the hero.
_CAMPUS_PHOTO = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/7/76/"
    "Gilman_Hall_and_the_Keyser_Quad.jpg/1920px-Gilman_Hall_and_the_Keyser_Quad.jpg"
)


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich Johns Hopkins to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Johns Hopkins is absent — safe on fresh/CI databases.
    """
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    # Drop any stale value for a path we explicitly declare omitted.
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
    inst.founded_year = 1876
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.jhu.edu"
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
        # Every school gets a working feed (the verified Hub RSS filtered by school keywords)
        # so its Events & Updates tab populates — overwriting any stale value on a pre-existing
        # row.
        sc.content_sources = _school_content(spec["name"])
        by_name[spec["name"]] = sc
    # Drop legacy schools — programs.school_id is ON DELETE SET NULL, so this is FK-safe.
    for name, sc in existing.items():
        if name not in canonical_names:
            session.delete(sc)
    session.flush()
    return by_name


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
        p.duration_months = spec.get("duration_months")
        p.description_text = spec["description"]
        p.website_url = _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec["delivery_format"]
        # Every program gets a working feed (the verified Hub RSS filtered by program keywords)
        # so its Events & Updates tab populates rather than sitting empty.
        p.content_sources = _program_content(spec["school"], spec["keywords"])
        if spec["degree_type"] == "bachelors":
            p.tuition = None
            p.cost_data = dict(_UG_COST)
            p.who_its_for = _WHO_UG
        else:
            p.tuition = None
            p.cost_data = dict(_GRAD_COST)
            p.who_its_for = _WHO_GRAD
        p.highlights = list(_HL_BASELINE)
        p.application_requirements = _requirements_for(spec)
        outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(slug)
        p.outcomes_data = outcomes
        # Deep fields recorded as omitted-pending (cleared on any pre-existing row).
        p.tracks = None
        p.class_profile = None
        p.faculty_contacts = None
        p.external_reviews = None
        p.application_deadline = date(2027, 1, 2) if spec["degree_type"] == "bachelors" else None
    session.flush()
    # Reconcile legacy/seed programs (slug not in the canonical set): delete when unreferenced,
    # otherwise unpublish so the catalog stays clean without breaking any application/match rows.
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
