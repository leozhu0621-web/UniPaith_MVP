"""Dartmouth College — gold-standard profile data (institution + schools + program catalog).

Every value below is verified against an authoritative source (Dartmouth's official
pages, the U.S. Dept. of Education College Scorecard / NCES for UNITID 182670, the
2024-25 Common Data Set, and the ranking bodies) and carries a citation, or is honestly
omitted (recorded in that node's ``_standard.omitted``) — never guessed.

The institution-level federal seed already wrote admit_rate, avg_net_price,
median_earnings_10yr, completion_rate_4yr_150pct, location, ownership, the campus-photo
gallery and media_credit; ``apply`` shallow-merges the remaining required fields onto it.

Scope note: Dartmouth was a 5-stub institution seed. Earlier passes took the INSTITUTION
to gold and built the undergraduate + flagship graduate catalog. This pass (2026-06-25)
FINISHES the in-flight deferral — the full Guarini graduate catalog (Math/Earth
Sciences/EEES/MCB/QBS/Computational Science/Integrative Neuroscience/Health Policy PhDs +
Chemistry MS, Comparative Literature MA, Earth Sciences MS, MFA in Sonic Practice, the five
Geisel-based health-sciences master's, and the Master of Energy Transition) — and adds the
matcher-core + universal-depth fields the prior passes left null: `cip_code` on EVERY
program (REPAIR_BACKLOG #1), `who_its_for` on EVERY program (REPAIR_BACKLOG #4), and a
sourced `external_reviews` on the Geisel M.D. alongside the Tuck MBA (REPAIR_BACKLOG #5).
Every value is verified-or-omitted; nothing is padded.

Graduate-tier tuition: stamps published 2026-27 master's/professional rates from each
school's official tuition page — Thayer MEng $71,697 (3 terms) / MEM $95,596 (4 terms),
Tuck MBA $87,536, Geisel M.D. $75,110, Dartmouth Institute on-campus MPH $82,232, Guarini
full-time master's $95,596 (4 terms × $23,899), MALS full-time $66,917 — never the $66,123
undergraduate sticker. PhD rows remain funded-omit-with-reason; the Geisel-based health
master's (per-credit / part-time / online) and the new Master of Energy Transition are
honestly omit-with-reason rather than estimated.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Dartmouth College"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-25"


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
    # NCES lists Dartmouth's student-faculty ratio (7:1) but no single current official
    # instructional-faculty headcount could be verified this session, so the count is
    # omitted (the ratio + endowment are provided); never guessed.
    "school_outcomes.scale.faculty_count",
]

# ── Institution-level data ────────────────────────────────────────────────
RANKING_DATA: dict = {
    "ownership_type": "private",
    # New England Commission of Higher Education.
    "accreditor": "NECHE",
    # Carnegie 2025 basic classification (R1).
    "carnegie_classification": "Doctoral Universities: Very High Research Activity (R1)",
    # QS World University Rankings 2026: #=247 (topuniversities.com, verified directly).
    "qs_world_university_rankings": {"rank": 247, "year": 2026},
    # THE World University Rankings 2026: #180 worldwide.
    "times_higher_education": {"rank": 180, "year": 2026},
    # U.S. News Best Colleges (National Universities) 2026: #13 nationally.
    "us_news_national": {"rank": 13, "year": 2026},
}

# school_outcomes is shallow-merged into the existing JSONB (the federal seed already
# wrote admit_rate / avg_net_price / median_earnings_10yr / completion_rate /
# location / campus_photos); each sub-object below is complete, so a shallow merge is
# correct.
SCHOOL_OUTCOMES: dict = {
    # College Scorecard (federal seed) — first-year admit rate (prior cycle).
    "admit_rate": 0.054,
    "avg_net_price": 29519,
    "median_earnings_10yr": 97434,
    # NCES College Navigator / College Scorecard six-year graduation rate.
    "graduation_rate_6yr": 0.955,
    # NCES College Navigator: first-year retention = 98%.
    "retention_rate_first_year": 0.98,
    "financial_aid": {
        # Dartmouth news: a record 19.4% of the Class of 2028 qualify for a Pell grant.
        "pell_grant_rate": 0.194,
        # Dartmouth Financial Aid — published 2025-26 total cost of attendance.
        "cost_of_attendance": 95490,
    },
    # Undergraduate race/ethnicity (Dartmouth Common Data Set 2024-25 / Office of
    # Institutional Research).
    "demographics": {
        "white": 0.438,
        "asian": 0.125,
        "hispanic": 0.092,
        "two_or_more": 0.075,
        "black": 0.052,
        "american_indian": 0.010,
        "international": 0.145,
        "unknown": 0.062,
    },
    # SAT/ACT 25th-75th percentiles of enrolled first-years (Dartmouth Common Data Set
    # 2024-25). The reading/math split is not separately recorded here (composite + ACT
    # are the verified ranges). Dartmouth reinstated a standardized-testing requirement.
    "test_scores": {
        "sat_total_25_75": [1440, 1550],
        "act_25_75": [32, 35],
    },
    # Dartmouth main campus, Hanover, New Hampshire.
    "location": {"lat": 43.704115, "lng": -72.289949},
    "campus_basics": {"location": "Hanover, New Hampshire"},
    "scale": {
        # NCES College Navigator: 7:1 student-faculty ratio.
        "student_faculty_ratio": "7:1",
        # Dartmouth Investment Office — endowment $8.3 billion at fiscal year-end
        # June 30, 2024 (FY2024 endowment report).
        "endowment_usd": 8300000000,
    },
    # Dartmouth Center for Career Design first-destination outcomes, Class of 2025
    # (86% knowledge rate): 71.7% accepted a full-time job and 21.9% are continuing
    # their education — about 94% employed or in graduate/professional study.
    "employed_or_continuing_ed": 0.94,
    # Dartmouth Center for Career Design — leading fields entered by graduates.
    "top_employer_industries": [
        "Technology & Engineering",
        "Consulting",
        "Finance",
    ],
    "research": {
        "labs": [
            "Neukom Institute for Computational Science",
            "The Dartmouth Institute for Health Policy & Clinical Practice (TDI)",
            "Dartmouth Cancer Center",
            "Arthur L. Irving Institute for Energy & Society",
            "Nelson A. Rockefeller Center for Public Policy",
            "John Sloan Dickey Center for International Understanding",
        ],
        "areas": [
            "Computational science & data",
            "Health policy & clinical practice",
            "Cancer biology & oncology",
            "Energy & society",
            "Public policy",
            "International understanding & security",
            "Engineering & the physical sciences",
        ],
        "lab_links": {
            "Neukom Institute for Computational Science": "https://neukom.dartmouth.edu/",
            "The Dartmouth Institute for Health Policy & Clinical Practice (TDI)": (
                "https://tdi.dartmouth.edu/"
            ),
            "Dartmouth Cancer Center": "https://cancer.dartmouth.edu/",
            "Arthur L. Irving Institute for Energy & Society": "https://irving.dartmouth.edu/",
            "Nelson A. Rockefeller Center for Public Policy": "https://rockefeller.dartmouth.edu/",
            "John Sloan Dickey Center for International Understanding": (
                "https://dickey.dartmouth.edu/"
            ),
        },
    },
    "campus_life": {
        # Dartmouth's teams (the Big Green) compete in NCAA Division I (Ivy League).
        "athletics_division": "NCAA Division I (Ivy League)",
        "mascot": "Dartmouth Big Green",
        "housing": "Residential campus organized into six house communities",
        "resources": [
            {"label": "Dartmouth Big Green Athletics", "url": "https://dartmouthsports.com/"},
            {"label": "Dartmouth Libraries", "url": "https://www.library.dartmouth.edu/"},
            {"label": "Hood Museum of Art", "url": "https://hoodmuseum.dartmouth.edu/"},
            {"label": "Hopkins Center for the Arts", "url": "https://hop.dartmouth.edu/"},
            {"label": "Center for Career Design", "url": "https://careerdesign.dartmouth.edu/"},
        ],
    },
    "flagship": {
        # NCES College Navigator (Fall 2024): 6,938 total students.
        "enrollment_total": 6938,
        # Dartmouth Admissions — Class of 2029 first-year cycle.
        "applicants": 28230,
        "admits": 1702,
        "admissions_cycle": "Class of 2029 (entering fall 2025; Dartmouth Admissions)",
        "founded_year": 1769,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Dartmouth, UNITID 182670)",
            "url": "https://collegescorecard.ed.gov/school/?182670",
        },
        {
            "label": "NCES College Navigator — Dartmouth College (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=182670",
        },
        {
            "label": "Dartmouth Office of Institutional Research — Common Data Set 2024-25",
            "url": "https://www.dartmouth.edu/oir/data-reporting/cds/index.html",
        },
        {
            "label": "Dartmouth Admissions — Class of 2029 admissions release",
            "url": "https://home.dartmouth.edu/news/2025/03/admissions-class-2029",
        },
        {
            "label": "Dartmouth Financial Aid — Cost of Attendance 2025-2026",
            "url": "https://financialaid.dartmouth.edu/cost-attendance/cost-attendance-2025-2026",
        },
        {
            "label": "Dartmouth Investment Office — Endowment Report 2024 ($8.3B, FY2024)",
            "url": "https://www.dartmouth.edu/investments/about/endowment_reports/",
        },
        {
            "label": "Dartmouth Center for Career Design — First-Destination Outcomes",
            "url": "https://careerdesign.dartmouth.edu/",
        },
        {
            "label": "QS World University Rankings 2026 — Dartmouth College",
            "url": "https://www.topuniversities.com/universities/dartmouth-college",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — Dartmouth College",
            "url": "https://www.timeshighereducation.com/world-university-rankings/dartmouth-college",
        },
        {
            "label": "U.S. News Best Colleges 2026 — Dartmouth College (#13 National Universities)",
            "url": "https://www.usnews.com/best-colleges/dartmouth-college-2573",
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it "Undergraduates");
# the total (6,938) lives in flagship.enrollment_total.
UNDERGRAD_COUNT = 4637

DESCRIPTION = (
    "Dartmouth College is a private Ivy League research university in Hanover, New "
    "Hampshire, chartered in 1769 by King George III — the ninth college founded in "
    "colonial America and the smallest university in the Ivy League. It enrolls about "
    "4,600 undergraduates and some 2,300 graduate and professional students — roughly "
    "6,900 in all — with a 7:1 student-faculty ratio and an intensive, year-round "
    "quarter calendar (the \"D-Plan\") built around small classes and undergraduate "
    "research.\n\n"
    "Dartmouth is organized into the undergraduate-focused School of Arts and Sciences "
    "and four graduate and professional schools: the Thayer School of Engineering, the "
    "Tuck School of Business — the world's first graduate school of management — the "
    "Geisel School of Medicine, the nation's fourth-oldest medical school, and the Frank "
    "J. Guarini School of Graduate and Advanced Studies, which oversees the PhD and "
    "master's programs. Its research is anchored by the Neukom Institute for "
    "Computational Science, The Dartmouth Institute for Health Policy & Clinical "
    "Practice, the Dartmouth Cancer Center, and the Irving Institute for Energy & "
    "Society.\n\n"
    "A Carnegie R1 university accredited by NECHE, Dartmouth ranks No. 13 among national "
    "universities by U.S. News, No. 180 in the world by Times Higher Education, and No. "
    "247 by QS. It admitted about 6% of first-year applicants for the Class of 2029 and "
    "holds an endowment of $8.3 billion as of June 2024.\n\n"
    "Dartmouth meets the full demonstrated financial need of admitted undergraduates: "
    "the average net price is about $30,000 a year against a published 2025-26 cost of "
    "attendance near $95,000, and a record 19.4% of the entering Class of 2028 qualified "
    "for a Pell grant. Among the Class of 2025, about 94% of graduates were employed or "
    "continuing their education, most heavily in technology and engineering, consulting, "
    "and finance. Dartmouth's teams, the Big Green, compete in NCAA Division I in the "
    "Ivy League."
)

# ── The real degree-granting schools (display order) ───────────────────────
_ARTS = "School of Arts and Sciences"
_THAYER = "Thayer School of Engineering"
_TUCK = "Tuck School of Business"
_GEISEL = "Geisel School of Medicine"
_GUARINI = "Frank J. Guarini School of Graduate and Advanced Studies"

_SCHOOL_WEBSITE: dict[str, str] = {
    _ARTS: "https://home.dartmouth.edu/academics/undergraduate-arts-sciences",
    _THAYER: "https://engineering.dartmouth.edu/",
    _TUCK: "https://www.tuck.dartmouth.edu/",
    _GEISEL: "https://geiselmed.dartmouth.edu/",
    _GUARINI: "https://graduate.dartmouth.edu/",
}

SCHOOLS: list[dict] = [
    {
        "name": _ARTS,
        "sort_order": 1,
        "description": (
            "The School of Arts and Sciences is Dartmouth's undergraduate liberal-arts "
            "core, teaching across the arts and humanities, the natural and physical "
            "sciences, and the social sciences. It awards the A.B. across more than fifty "
            "majors and houses most of the departments that anchor Dartmouth's PhD "
            "programs."
        ),
    },
    {
        "name": _THAYER,
        "sort_order": 2,
        "description": (
            "Founded in 1867, the Thayer School of Engineering offers a broad, "
            "project-based engineering education spanning the major branches, awarding "
            "the A.B. in engineering sciences, the professional Bachelor of Engineering, "
            "and graduate degrees through the PhD, with a human-centered design ethos."
        ),
    },
    {
        "name": _TUCK,
        "sort_order": 3,
        "description": (
            "Founded in 1900, the Tuck School of Business is the world's first graduate "
            "school of management, awarding a single full-time, two-year MBA known for "
            "its small, tightly connected cohort and residential community."
        ),
    },
    {
        "name": _GEISEL,
        "sort_order": 4,
        "description": (
            "Founded in 1797, the Geisel School of Medicine is the nation's fourth-oldest "
            "medical school, awarding the M.D. alongside master's and doctoral degrees in "
            "the health and biomedical sciences in partnership with Dartmouth Health."
        ),
    },
    {
        "name": _GUARINI,
        "sort_order": 5,
        "description": (
            "The Frank J. Guarini School of Graduate and Advanced Studies oversees "
            "Dartmouth's graduate education, administering PhD and master's programs "
            "across the arts and sciences, engineering, and the health sciences for some "
            "850 graduate students."
        ),
    },
]

# School founded years + research centers (stable, verifiable). Leadership + named-faculty
# rosters are omitted (current deans not re-verified this session — omitted rather than
# risk a stale name; SKILL Verify gate).
_ABOUT_DETAIL: dict[str, dict] = {
    _ARTS: {
        "founded": (
            "Dartmouth chartered 1769; the unified School of Arts and Sciences formed in 2025"
        ),
        "research_centers": [
            "Neukom Institute for Computational Science",
            "Leslie Center for the Humanities",
            "Nelson A. Rockefeller Center for Public Policy",
            "John Sloan Dickey Center for International Understanding",
        ],
    },
    _THAYER: {
        "founded": "1867",
        "research_centers": [
            "Arthur L. Irving Institute for Energy & Society",
            "PhD Innovation Program",
        ],
    },
    _TUCK: {
        "founded": "1900",
        "research_centers": [
            "Center for Business, Government & Society",
            "Center for Private Equity and Venture Capital",
        ],
    },
    _GEISEL: {
        "founded": "1797",
        "research_centers": [
            "The Dartmouth Institute for Health Policy & Clinical Practice (TDI)",
            "Dartmouth Cancer Center",
        ],
    },
    _GUARINI: {
        "founded": "Named in 2016; Dartmouth graduate studies date to the 19th century",
        # Guarini is an administrative/oversight school; its research lives in the
        # departments and professional schools, so research_centers is omitted by design.
    },
}
_ABOUT_OMITTED: dict[str, list[str]] = {
    _ARTS: ["about_detail.leadership", "about_detail.faculty"],
    _THAYER: ["about_detail.leadership", "about_detail.faculty"],
    _TUCK: ["about_detail.leadership", "about_detail.faculty"],
    _GEISEL: ["about_detail.leadership", "about_detail.faculty"],
    _GUARINI: [
        "about_detail.leadership",
        "about_detail.faculty",
        "about_detail.research_centers",
    ],
}

# ── Channel feeds + official social links ──────────────────────────────────
# The daily content-ingest reads news_rss (RSS), keywords (word-boundary relevance
# filter) and social from each node's content_sources. Dartmouth's all-news RSS is the
# only verified working feed (HTTP 200, 10 fresh items); the campus events calendar is a
# CampusGroups ICS that 302-redirects to an auth-gated HTML page (0 VEVENTs on fetch), so
# events_feed is honestly omitted rather than shipping a dead feed (SKILL miss #9).
_DARTMOUTH_NEWS_RSS = "https://home.dartmouth.edu/rss.xml"

_SOCIAL_DARTMOUTH = {
    "instagram": "https://www.instagram.com/dartmouthcollege",
    "linkedin": "https://www.linkedin.com/school/dartmouth-college/",
    "x": "https://x.com/dartmouth",
    "youtube": "https://www.youtube.com/Dartmouth",
    "facebook": "https://www.facebook.com/Dartmouth/",
}
_SOCIAL_BY_SCHOOL: dict[str, dict] = {
    _THAYER: {
        "instagram": "https://www.instagram.com/thayerschool/",
        "linkedin": "https://www.linkedin.com/school/dartmouth-engineering/",
        "x": "https://twitter.com/thayerschool",
        "youtube": "https://www.youtube.com/thayerschool",
        "facebook": "https://www.facebook.com/thayerschool",
    },
    _TUCK: {
        "instagram": "https://instagram.com/tuckschool",
        "linkedin": "https://www.linkedin.com/school/tuck-school-of-business-at-dartmouth/",
        "youtube": "https://www.youtube.com/user/TuckSchoolofBusiness",
    },
}

# Per-school feed keywords (the shared Dartmouth RSS filtered to school-relevant items).
_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _ARTS: ["Arts and Sciences", "undergraduate", "faculty"],
    _THAYER: ["Thayer", "engineering", "engineers"],
    _TUCK: ["Tuck", "business school", "MBA"],
    _GEISEL: ["Geisel", "medical", "medicine"],
    _GUARINI: ["Guarini", "graduate", "PhD"],
}


def _school_content(name: str) -> dict:
    """Build a school's content_sources from the verified Dartmouth RSS + keywords + socials."""
    return {
        "news_rss": _DARTMOUTH_NEWS_RSS,
        "news_url": "https://home.dartmouth.edu/news",
        "news_curated": False,
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": _SOCIAL_BY_SCHOOL.get(name, _SOCIAL_DARTMOUTH),
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    """Build a program's content_sources from its school feed, refined by program keywords."""
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


_INSTITUTION_CONTENT: dict = {
    "news_rss": _DARTMOUTH_NEWS_RSS,
    "news_url": "https://home.dartmouth.edu/news",
    "news_curated": True,
    "social": _SOCIAL_DARTMOUTH,
}

# ── The program catalog ────────────────────────────────────────────────────
# Each tuple: (field_name, program_name, degree_type, school, department, duration_months,
#              keywords, description). Descriptions are field-specific researched prose
# (gold contrast, anti-stub clean) — never a classification/template stub.
_CATALOG: list[tuple] = [
    # ── School of Arts and Sciences — undergraduate A.B. majors ──
    (
        "Anthropology", "Bachelor of Arts in Anthropology", "bachelors", _ARTS,
        "Department of Anthropology", 48, ["anthropology"],
        "Dartmouth's anthropology major studies human societies past and present across "
        "the cultural, archaeological, and biological subfields, combining coursework "
        "with field and laboratory research.",
    ),
    (
        "Art History", "Bachelor of Arts in Art History", "bachelors", _ARTS,
        "Department of Art History", 48, ["art history"],
        "The art history major examines visual culture from antiquity to the present, "
        "drawing on the collections of the Hood Museum of Art for object-based study of "
        "painting, sculpture, architecture, and global visual traditions.",
    ),
    (
        "Biological Sciences", "Bachelor of Arts in Biological Sciences", "bachelors", _ARTS,
        "Department of Biological Sciences", 48, ["biology", "biological sciences"],
        "Biology at Dartmouth spans molecular, cellular, organismal, and ecological "
        "scales, pairing laboratory and field research with pathways into genetics, "
        "neurobiology, and evolutionary biology.",
    ),
    (
        "Chemistry", "Bachelor of Arts in Chemistry", "bachelors", _ARTS,
        "Department of Chemistry", 48, ["chemistry"],
        "The chemistry major covers organic, inorganic, physical, analytical, and "
        "biological chemistry, with core coursework anchored by undergraduate research "
        "in faculty laboratories.",
    ),
    (
        "Classics", "Bachelor of Arts in Classics", "bachelors", _ARTS,
        "Department of Classics", 48, ["classics"],
        "Classics combines the study of Greek and Latin with the history, archaeology, "
        "and literature of the ancient Mediterranean world.",
    ),
    (
        "Cognitive Science", "Bachelor of Arts in Cognitive Science", "bachelors", _ARTS,
        "Program in Cognitive Science", 48, ["cognitive science"],
        "Cognitive science integrates psychology, neuroscience, computer science, "
        "linguistics, and philosophy to study the mind, perception, and intelligent "
        "behavior.",
    ),
    (
        "Computer Science", "Bachelor of Arts in Computer Science", "bachelors", _ARTS,
        "Department of Computer Science", 48, ["computer science"],
        "Dartmouth's computer science major — at the institution where the term "
        "\"artificial intelligence\" was coined in 1956 — spans algorithms, systems, "
        "theory, machine learning, and human-computer interaction, with extensive "
        "undergraduate research.",
    ),
    (
        "Earth Sciences", "Bachelor of Arts in Earth Sciences", "bachelors", _ARTS,
        "Department of Earth Sciences", 48, ["earth sciences", "geology"],
        "Earth sciences studies the solid Earth, oceans, and climate through coursework "
        "and field study, with ties to Dartmouth's polar and climate research.",
    ),
    (
        "Economics", "Bachelor of Arts in Economics", "bachelors", _ARTS,
        "Department of Economics", 48, ["economics", "economist"],
        "Economics grounds students in microeconomic and macroeconomic theory and "
        "econometrics, with applied fields from finance and industrial organization to "
        "development and public economics.",
    ),
    (
        "English", "Bachelor of Arts in English", "bachelors", _ARTS,
        "Department of English and Creative Writing", 48, ["English", "creative writing"],
        "The English and creative writing major studies literature in English across "
        "periods and genres alongside workshops in fiction, poetry, and nonfiction.",
    ),
    (
        "Environmental Studies", "Bachelor of Arts in Environmental Studies", "bachelors", _ARTS,
        "Program in Environmental Studies", 48, ["environmental studies", "environment"],
        "Environmental studies links the natural and social sciences, policy, and the "
        "humanities to address sustainability, conservation, and environmental change.",
    ),
    (
        "Film and Media Studies", "Bachelor of Arts in Film and Media Studies", "bachelors", _ARTS,
        "Department of Film and Media Studies", 48, ["film", "media studies"],
        "Film and media studies pairs critical study of cinema and moving-image culture "
        "with hands-on production in film, video, and digital media.",
    ),
    (
        "Geography", "Bachelor of Arts in Geography", "bachelors", _ARTS,
        "Department of Geography", 48, ["geography"],
        "Geography examines the spatial dimensions of human and physical systems — "
        "urbanization, development, and the environment — using fieldwork and "
        "geospatial analysis.",
    ),
    (
        "Government", "Bachelor of Arts in Government", "bachelors", _ARTS,
        "Department of Government", 48, ["government", "politics"],
        "The government major studies American politics, comparative politics, "
        "international relations, and political theory, with policy engagement through "
        "the Nelson A. Rockefeller Center for Public Policy.",
    ),
    (
        "History", "Bachelor of Arts in History", "bachelors", _ARTS,
        "Department of History", 48, ["history"],
        "History at Dartmouth spans the Americas, Europe, Africa, Asia, and the Middle "
        "East, training students in archival research and historical argument across "
        "premodern and modern periods.",
    ),
    (
        "Mathematics", "Bachelor of Arts in Mathematics", "bachelors", _ARTS,
        "Department of Mathematics", 48, ["mathematics", "math"],
        "The mathematics major covers analysis, algebra, topology, and applied "
        "mathematics, with paths toward pure mathematics, applied and computational "
        "work, and statistics.",
    ),
    (
        "Music", "Bachelor of Arts in Music", "bachelors", _ARTS,
        "Department of Music", 48, ["music"],
        "The music major combines performance, composition, theory, and ethnomusicology, "
        "with ensembles and recital space at the Hopkins Center for the Arts.",
    ),
    (
        "Neuroscience", "Bachelor of Arts in Neuroscience", "bachelors", _ARTS,
        "Program in Neuroscience", 48, ["neuroscience", "brain"],
        "The neuroscience major studies the nervous system from molecules and cells to "
        "cognition and behavior, integrating biology, chemistry, and psychological and "
        "brain sciences.",
    ),
    (
        "Philosophy", "Bachelor of Arts in Philosophy", "bachelors", _ARTS,
        "Department of Philosophy", 48, ["philosophy"],
        "Philosophy covers logic, ethics, metaphysics, epistemology, and the history of "
        "philosophy, with departmental strength in the philosophy of mind and science.",
    ),
    (
        "Physics", "Bachelor of Arts in Physics", "bachelors", _ARTS,
        "Department of Physics and Astronomy", 48, ["physics", "astronomy"],
        "Physics and astronomy spans classical and quantum mechanics, electromagnetism, "
        "and astrophysics, with undergraduate research from cosmology and space physics "
        "to condensed matter.",
    ),
    (
        "Psychological and Brain Sciences",
        "Bachelor of Arts in Psychological and Brain Sciences", "bachelors", _ARTS,
        "Department of Psychological and Brain Sciences", 48, ["psychology", "brain sciences"],
        "The psychological and brain sciences major studies cognition, perception, "
        "social behavior, and the brain, with laboratory research and neuroimaging "
        "facilities.",
    ),
    (
        "Quantitative Social Science",
        "Bachelor of Arts in Quantitative Social Science", "bachelors", _ARTS,
        "Program in Quantitative Social Science", 48, ["quantitative social science", "data"],
        "Quantitative social science trains students in statistics, data analysis, and "
        "causal inference applied to questions in politics, economics, and society.",
    ),
    (
        "Religion", "Bachelor of Arts in Religion", "bachelors", _ARTS,
        "Department of Religion", 48, ["religion"],
        "The religion major studies the world's religious traditions — their texts, "
        "histories, and practices — across Asian, Abrahamic, and indigenous traditions.",
    ),
    (
        "Sociology", "Bachelor of Arts in Sociology", "bachelors", _ARTS,
        "Department of Sociology", 48, ["sociology"],
        "Sociology examines social structure, inequality, institutions, and change, "
        "pairing social theory with quantitative and qualitative research methods.",
    ),
    (
        "Spanish", "Bachelor of Arts in Spanish", "bachelors", _ARTS,
        "Department of Spanish and Portuguese", 48, ["Spanish"],
        "The Spanish major develops advanced language proficiency and studies the "
        "literatures and cultures of Spain and Latin America, with Dartmouth's "
        "off-campus language study programs.",
    ),
    (
        "Studio Art", "Bachelor of Arts in Studio Art", "bachelors", _ARTS,
        "Department of Studio Art", 48, ["studio art", "art"],
        "Studio art offers practice across drawing, painting, sculpture, photography, "
        "and digital media in a studio-intensive, critique-based curriculum.",
    ),
    (
        "Theater", "Bachelor of Arts in Theater", "bachelors", _ARTS,
        "Department of Theater", 48, ["theater", "theatre"],
        "The theater major integrates acting, directing, design, and dramatic literature "
        "with production work at the Hopkins Center for the Arts.",
    ),
    (
        "Linguistics", "Bachelor of Arts in Linguistics", "bachelors", _ARTS,
        "Program in Linguistics", 48, ["linguistics"],
        "Linguistics studies the structure of language — phonology, syntax, semantics, "
        "and sociolinguistics — and its cognitive and computational dimensions.",
    ),
    (
        "African and African American Studies",
        "Bachelor of Arts in African and African American Studies", "bachelors", _ARTS,
        "Department of African and African American Studies", 48, ["African American studies"],
        "African and African American studies examines the histories, cultures, "
        "politics, and creative expression of Africa and its diasporas.",
    ),
    # ── Thayer School of Engineering ──
    (
        "Engineering Sciences", "Bachelor of Arts in Engineering Sciences", "bachelors", _THAYER,
        "Thayer School of Engineering", 48, ["engineering sciences", "Thayer"],
        "The A.B. in engineering sciences offers a broad, project-based engineering "
        "education spanning the major branches, with a human-centered design ethos and "
        "the option to continue to the professional Bachelor of Engineering.",
    ),
    (
        "Engineering", "Bachelor of Engineering", "bachelors", _THAYER,
        "Thayer School of Engineering", 60, ["Bachelor of Engineering", "Thayer"],
        "The Bachelor of Engineering is Thayer's ABET-accredited professional degree, "
        "earned with a fifth year of design and engineering-science coursework beyond "
        "the A.B., emphasizing project-based and human-centered design.",
    ),
    (
        "Engineering Management", "Master of Engineering Management", "masters", _THAYER,
        "Thayer School of Engineering", 18, ["engineering management", "MEM"],
        "The Master of Engineering Management, offered jointly by the Thayer School and "
        "the Tuck School, pairs engineering depth with management, finance, and "
        "operations for engineers moving into leadership and product roles.",
    ),
    (
        "Engineering Graduate", "Master of Engineering", "masters", _THAYER,
        "Thayer School of Engineering", 24, ["Master of Engineering", "Thayer"],
        "Thayer's Master of Engineering is a professional graduate degree extending "
        "technical depth across the school's engineering fields through design projects "
        "and advanced electives.",
    ),
    (
        "Engineering Doctorate", "Doctor of Philosophy in Engineering", "phd", _THAYER,
        "Thayer School of Engineering", 60, ["engineering PhD", "Thayer research"],
        "Thayer's unified engineering PhD supports doctoral research across biomedical, "
        "energy, materials, and computational engineering without rigid departmental "
        "boundaries, including the PhD Innovation Program.",
    ),
    # ── Tuck School of Business (flagship) ──
    (
        "Business Administration", "Master of Business Administration", "masters", _TUCK,
        "Tuck School of Business", 24, ["MBA", "Tuck"],
        "The Tuck MBA is a full-time, two-year general-management program known for its "
        "small, tightly connected cohort, team-based learning, and a residential "
        "community in Hanover, with strong placement in consulting, finance, and "
        "technology.",
    ),
    # ── Geisel School of Medicine ──
    (
        "Medicine", "Doctor of Medicine", "professional", _GEISEL,
        "Geisel School of Medicine", 48, ["Geisel", "medical school", "M.D."],
        "The Geisel School of Medicine — the nation's fourth-oldest, founded in 1797 — "
        "awards the M.D. through a curriculum integrating foundational science, early "
        "clinical experience, and research with Dartmouth Health.",
    ),
    (
        "Public Health", "Master of Public Health", "masters", _GEISEL,
        "The Dartmouth Institute for Health Policy & Clinical Practice", 12,
        ["public health", "MPH", "Dartmouth Institute"],
        "The Master of Public Health, based at The Dartmouth Institute for Health Policy "
        "& Clinical Practice, trains students in epidemiology, biostatistics, and "
        "health-system improvement.",
    ),
    # ── Guarini School of Graduate and Advanced Studies (flagship PhDs/master's) ──
    (
        "Computer Science", "Doctor of Philosophy in Computer Science", "phd", _GUARINI,
        "Department of Computer Science", 60, ["computer science PhD", "Guarini"],
        "The computer science PhD supports doctoral research in systems, theory, machine "
        "learning, security, and computational science, with close faculty mentorship in "
        "a small program.",
    ),
    (
        "Computer Science", "Master of Science in Computer Science", "masters", _GUARINI,
        "Department of Computer Science", 24, ["computer science MS", "Guarini"],
        "The MS in computer science offers advanced coursework and research preparation "
        "across the core areas of computing.",
    ),
    (
        "Chemistry", "Doctor of Philosophy in Chemistry", "phd", _GUARINI,
        "Department of Chemistry", 60, ["chemistry PhD", "Guarini"],
        "The chemistry PhD trains researchers across synthetic, physical, biological, "
        "and materials chemistry in faculty laboratories.",
    ),
    (
        "Physics and Astronomy", "Doctor of Philosophy in Physics and Astronomy", "phd", _GUARINI,
        "Department of Physics and Astronomy", 60, ["physics PhD", "astronomy"],
        "The physics and astronomy PhD supports research in astrophysics and cosmology, "
        "space-plasma physics, and condensed-matter and quantum physics.",
    ),
    (
        "Psychological and Brain Sciences",
        "Doctor of Philosophy in Psychological and Brain Sciences", "phd", _GUARINI,
        "Department of Psychological and Brain Sciences", 60, ["psychology PhD", "brain"],
        "This doctoral program advances research in cognition, systems and cognitive "
        "neuroscience, and social and affective science using behavioral and "
        "neuroimaging methods.",
    ),
    (
        "Liberal Studies", "Master of Arts in Liberal Studies", "masters", _GUARINI,
        "Frank J. Guarini School of Graduate and Advanced Studies", 24,
        ["liberal studies", "MALS"],
        "The interdisciplinary Master of Arts in Liberal Studies lets students design a "
        "graduate course of study across the humanities, sciences, and social sciences, "
        "with concentrations including cultural studies and creative writing.",
    ),
    # ── Guarini doctoral programs (finishing the in-flight catalog) ──
    (
        "Mathematics", "Doctor of Philosophy in Mathematics", "phd", _GUARINI,
        "Department of Mathematics", 60, ["mathematics PhD", "math research"],
        "Dartmouth's mathematics PhD centers on original research in algebra, analysis, "
        "geometry, topology, combinatorics, and applied and computational mathematics, with "
        "small cohorts and individual faculty mentorship.",
    ),
    (
        "Earth Sciences", "Doctor of Philosophy in Earth Sciences", "phd", _GUARINI,
        "Department of Earth Sciences", 60, ["earth sciences PhD", "geoscience research"],
        "The earth sciences PhD supports original research across geobiology, paleoclimate, "
        "polar and glacial science, and tectonics, with extensive field and laboratory work.",
    ),
    (
        "Ecology, Evolution, Environment and Society",
        "Doctor of Philosophy in Ecology, Evolution, Environment and Society", "phd", _GUARINI,
        "Ecology, Evolution, Environment and Society Program", 60,
        ["EEES", "ecology", "evolution"],
        "The Ecology, Evolution, Environment and Society program offers interdisciplinary "
        "doctoral research connecting organismal and ecosystem biology, evolutionary "
        "processes, and the human dimensions of environmental change.",
    ),
    (
        "Molecular and Cellular Biology",
        "Doctor of Philosophy in Molecular and Cellular Biology", "phd", _GUARINI,
        "Molecular and Cellular Biology Program", 60, ["MCB", "molecular biology", "cell biology"],
        "The Molecular and Cellular Biology program is an umbrella PhD whose students rotate "
        "through laboratories in biochemistry, cancer biology, microbiology and immunology, "
        "and molecular and systems biology before choosing a thesis area.",
    ),
    (
        "Quantitative Biomedical Sciences",
        "Doctor of Philosophy in Quantitative Biomedical Sciences", "phd", _GUARINI,
        "Quantitative Biomedical Sciences Program", 60,
        ["QBS", "biostatistics", "bioinformatics"],
        "The Quantitative Biomedical Sciences PhD trains students in biostatistics, "
        "bioinformatics, and computational biology to analyze genomic, clinical, and "
        "epidemiologic data.",
    ),
    (
        "Computational Science and Modeling",
        "Doctor of Philosophy in Computational Science and Modeling", "phd", _GUARINI,
        "Program in Computational Science", 60, ["computational science", "modeling"],
        "This doctoral program builds expertise in numerical methods, high-performance "
        "computing, and mathematical modeling applied to research problems across the "
        "physical, biological, and social sciences.",
    ),
    (
        "Integrative Neuroscience",
        "Doctor of Philosophy in Integrative Neuroscience", "phd", _GUARINI,
        "Integrative Neuroscience at Dartmouth", 60, ["neuroscience PhD", "integrative"],
        "Integrative Neuroscience at Dartmouth is a cross-departmental PhD spanning "
        "molecular, cellular, systems, cognitive, and behavioral neuroscience, with faculty "
        "across the arts and sciences and the Geisel School of Medicine.",
    ),
    (
        "Health Policy and Clinical Practice",
        "Doctor of Philosophy in Health Policy and Clinical Practice", "phd", _GUARINI,
        "The Dartmouth Institute for Health Policy & Clinical Practice", 60,
        ["health policy PhD", "health services research"],
        "Based at The Dartmouth Institute, this PhD trains researchers in health-services "
        "research, health economics, and the rigorous evaluation of clinical practice and "
        "health policy.",
    ),
    # ── Guarini full-time research master's ──
    (
        "Chemistry", "Master of Science in Chemistry", "masters", _GUARINI,
        "Department of Chemistry", 24, ["chemistry MS", "4+1"],
        "The chemistry master's, available as a 4+1 pathway for Dartmouth undergraduates, "
        "extends coursework and independent laboratory research toward a thesis in the "
        "chemical sciences.",
    ),
    (
        "Comparative Literature", "Master of Arts in Comparative Literature", "masters", _GUARINI,
        "Program in Comparative Literature", 24, ["comparative literature", "literary theory"],
        "The comparative literature master's studies literary and cultural texts across "
        "languages and national traditions, with training in literary theory and translation.",
    ),
    (
        "Earth Sciences", "Master of Science in Earth Sciences", "masters", _GUARINI,
        "Department of Earth Sciences", 24, ["earth sciences MS", "geoscience"],
        "The earth sciences master's pairs advanced geoscience coursework with an "
        "independent research project, often as preparation for doctoral study or geoscience "
        "and environmental careers.",
    ),
    (
        "Sonic Practice", "Master of Fine Arts in Sonic Practice", "masters", _GUARINI,
        "Department of Music", 24, ["sonic practice", "sound art", "MFA"],
        "The MFA in Sonic Practice is a studio-based terminal degree in sound art and "
        "experimental music, integrating creative production, audio technology, and the "
        "critical study of sound.",
    ),
    # ── Geisel-based health-sciences master's ──
    (
        "Epidemiology", "Master of Science in Epidemiology", "masters", _GEISEL,
        "Department of Epidemiology", 24, ["epidemiology", "biostatistics"],
        "The epidemiology master's trains students in study design, biostatistics, and "
        "causal inference to investigate the distribution and determinants of disease in "
        "populations.",
    ),
    (
        "Health Data Science", "Master of Science in Health Data Science", "masters", _GEISEL,
        "Department of Biomedical Data Science", 24, ["health data science", "machine learning"],
        "The health data science master's combines statistics, machine learning, and "
        "programming applied to electronic health records, genomic data, and "
        "population-health datasets.",
    ),
    (
        "Healthcare Research", "Master of Science in Healthcare Research", "masters", _GEISEL,
        "The Dartmouth Institute for Health Policy & Clinical Practice", 12,
        ["healthcare research", "health services"],
        "Offered through The Dartmouth Institute, the healthcare research master's trains "
        "clinicians and scientists in health-services research methods, outcomes "
        "measurement, and health-system improvement.",
    ),
    (
        "Implementation Science", "Master of Science in Implementation Science", "masters", _GEISEL,
        "The Dartmouth Institute for Health Policy & Clinical Practice", 24,
        ["implementation science", "improvement science"],
        "This online master's prepares health professionals to translate research into "
        "practice, covering implementation frameworks, program evaluation, and improvement "
        "science.",
    ),
    (
        "Medical Informatics", "Master of Science in Medical Informatics", "masters", _GEISEL,
        "Department of Biomedical Data Science", 24, ["medical informatics", "informatics"],
        "The medical informatics master's studies the application of information systems and "
        "data standards to clinical care, including electronic health records, clinical "
        "decision support, and health-information exchange.",
    ),
    # ── Professional master's (Guarini + Irving Institute) ──
    (
        "Energy Transition", "Master of Energy Transition", "masters", _GUARINI,
        "Arthur L. Irving Institute for Energy & Society", 9, ["energy transition", "clean energy"],
        "The Master of Energy Transition is a nine-month residential professional master's, "
        "offered with the Arthur L. Irving Institute for Energy & Society, that integrates "
        "energy science and technology, policy, economics, and business to prepare "
        "clean-energy leaders.",
    ),
]

_SLUG_REPL = {"&": "and", " ": "-", "'": "", ".": "", ",": "", "(": "", ")": "", ":": ""}


def _slugify(text_value: str) -> str:
    s = text_value.lower()
    for k, v in _SLUG_REPL.items():
        s = s.replace(k, v)
    return "-".join(p for p in s.split("-") if p)


# Programs whose delivery is not the default residential `in_person`.
_DELIVERY_BY_SLUG: dict[str, str] = {
    "dartmouth-health-data-science-ms": "hybrid",  # on-campus & online (health-sciences page)
    "dartmouth-implementation-science-ms": "online",  # online program (health-sciences page)
}


def _build_catalog() -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for field, pname, dtype, school, dept, dur, kw, desc in _CATALOG:
        suffix = {"phd": "phd", "professional": "prof", "masters": "ms"}.get(dtype, "ab")
        slug = f"dartmouth-{_slugify(field)}-{suffix}"
        if slug in seen:
            raise RuntimeError(f"duplicate slug {slug}")
        seen.add(slug)
        out.append({
            "slug": slug,
            "school": school,
            "program_name": pname,
            "degree_type": dtype,
            "department": dept,
            "duration_months": dur,
            "delivery_format": _DELIVERY_BY_SLUG.get(slug, "in_person"),
            "keywords": list(kw),
            "description": desc,
        })
    return out


PROGRAMS: list[dict] = _build_catalog()
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}
_FLAGSHIP = "dartmouth-business-administration-ms"

# ── Matcher-core CIP family per program (REPAIR_BACKLOG #1) ─────────────────
# The IPEDS/College-Scorecard CIP family (the same 2-digit.2-digit code used for the
# breadth cross-check, UNITID 182670) resolved to each program's field — the join key the
# CPEF matcher uses for the interest/field signal. Never a guess; one code per real field.
_CIP_BY_SLUG: dict[str, str] = {
    # ── School of Arts and Sciences (undergraduate A.B.) ──
    "dartmouth-anthropology-ab": "45.02",
    "dartmouth-art-history-ab": "50.07",
    "dartmouth-biological-sciences-ab": "26.01",
    "dartmouth-chemistry-ab": "40.05",
    "dartmouth-classics-ab": "16.12",
    "dartmouth-cognitive-science-ab": "30.25",
    "dartmouth-computer-science-ab": "11.07",
    "dartmouth-earth-sciences-ab": "40.06",
    "dartmouth-economics-ab": "45.06",
    "dartmouth-english-ab": "23.01",
    "dartmouth-environmental-studies-ab": "03.01",
    "dartmouth-film-and-media-studies-ab": "50.06",
    "dartmouth-geography-ab": "45.07",
    "dartmouth-government-ab": "45.10",
    "dartmouth-history-ab": "54.01",
    "dartmouth-mathematics-ab": "27.01",
    "dartmouth-music-ab": "50.09",
    "dartmouth-neuroscience-ab": "26.15",
    "dartmouth-philosophy-ab": "38.01",
    "dartmouth-physics-ab": "40.08",
    "dartmouth-psychological-and-brain-sciences-ab": "42.27",
    "dartmouth-quantitative-social-science-ab": "45.01",
    "dartmouth-religion-ab": "38.02",
    "dartmouth-sociology-ab": "45.11",
    "dartmouth-spanish-ab": "16.09",
    "dartmouth-studio-art-ab": "50.07",
    "dartmouth-theater-ab": "50.05",
    "dartmouth-linguistics-ab": "16.01",
    "dartmouth-african-and-african-american-studies-ab": "05.02",
    # ── Thayer School of Engineering ──
    "dartmouth-engineering-sciences-ab": "14.01",
    "dartmouth-engineering-ab": "14.01",
    "dartmouth-engineering-management-ms": "15.15",
    "dartmouth-engineering-graduate-ms": "14.01",
    "dartmouth-engineering-doctorate-phd": "14.01",
    # ── Tuck School of Business ──
    "dartmouth-business-administration-ms": "52.02",
    # ── Geisel School of Medicine ──
    "dartmouth-medicine-prof": "51.12",
    "dartmouth-public-health-ms": "51.22",
    # ── Guarini School (existing) ──
    "dartmouth-computer-science-phd": "11.07",
    "dartmouth-computer-science-ms": "11.07",
    "dartmouth-chemistry-phd": "40.05",
    "dartmouth-physics-and-astronomy-phd": "40.08",
    "dartmouth-psychological-and-brain-sciences-phd": "42.27",
    "dartmouth-liberal-studies-ms": "24.01",
    # ── Guarini School (this run) ──
    "dartmouth-mathematics-phd": "27.01",
    "dartmouth-earth-sciences-phd": "40.06",
    "dartmouth-earth-sciences-ms": "40.06",
    "dartmouth-ecology-evolution-environment-and-society-phd": "26.13",
    "dartmouth-molecular-and-cellular-biology-phd": "26.04",
    "dartmouth-quantitative-biomedical-sciences-phd": "26.11",
    "dartmouth-computational-science-and-modeling-phd": "30.08",
    "dartmouth-integrative-neuroscience-phd": "26.15",
    "dartmouth-health-policy-and-clinical-practice-phd": "51.22",
    "dartmouth-chemistry-ms": "40.05",
    "dartmouth-comparative-literature-ms": "16.01",
    "dartmouth-sonic-practice-ms": "50.09",
    "dartmouth-epidemiology-ms": "26.13",
    "dartmouth-health-data-science-ms": "30.70",
    "dartmouth-healthcare-research-ms": "51.22",
    "dartmouth-implementation-science-ms": "51.22",
    "dartmouth-medical-informatics-ms": "51.27",
    "dartmouth-energy-transition-ms": "03.02",
}

# ── "Who it's for" per program (REPAIR_BACKLOG #4, universal-depth field) ───
# A field-specific 1–2 sentence statement of the applicant each program fits (background,
# goals, readiness) — gold-contrast bar, never a "for students interested in {field}" stub.
_WHO_BY_SLUG: dict[str, str] = {
    "dartmouth-anthropology-ab": (
        "Undergraduates curious about human cultures, evolution, and the archaeological "
        "past who want hands-on field and lab research and a flexible path into public "
        "health, law, museums, or graduate study."
    ),
    "dartmouth-art-history-ab": (
        "Students drawn to visual culture and the history of art who want to learn directly "
        "from museum objects at the Hood and pursue curation, conservation, the art world, "
        "or graduate study."
    ),
    "dartmouth-biological-sciences-ab": (
        "Aspiring biologists and pre-health students who want a broad foundation from "
        "molecules to ecosystems with substantial laboratory and field research."
    ),
    "dartmouth-chemistry-ab": (
        "Students headed toward chemistry, the health professions, or materials and energy "
        "research who want rigorous core training and early access to faculty research labs."
    ),
    "dartmouth-classics-ab": (
        "Students fascinated by the ancient Greek and Roman world who want to read original "
        "languages and combine literature, history, and archaeology."
    ),
    "dartmouth-cognitive-science-ab": (
        "Students who want to understand the mind across psychology, neuroscience, computer "
        "science, linguistics, and philosophy and enjoy crossing disciplinary lines."
    ),
    "dartmouth-computer-science-ab": (
        "Future software engineers, researchers, and founders who want strong fundamentals "
        "in algorithms, systems, and machine learning with extensive undergraduate research."
    ),
    "dartmouth-earth-sciences-ab": (
        "Students drawn to the planet — geology, oceans, and climate — who value fieldwork "
        "and want paths into environmental, energy, or geoscience careers."
    ),
    "dartmouth-economics-ab": (
        "Analytically minded students aiming for finance, consulting, policy, or graduate "
        "economics who want rigorous theory plus econometrics."
    ),
    "dartmouth-english-ab": (
        "Strong readers and writers who want to study literature deeply and develop their "
        "own craft in fiction, poetry, or nonfiction."
    ),
    "dartmouth-environmental-studies-ab": (
        "Students committed to sustainability who want to combine science, policy, and the "
        "humanities to address real-world environmental problems."
    ),
    "dartmouth-film-and-media-studies-ab": (
        "Students who want both to analyze moving-image culture and to make films, video, "
        "and digital media."
    ),
    "dartmouth-geography-ab": (
        "Students interested in how people, places, and environments interact who enjoy "
        "fieldwork and geospatial analysis."
    ),
    "dartmouth-government-ab": (
        "Students aiming for law, public service, policy, or political research who want "
        "grounding in American and comparative politics, international relations, and theory."
    ),
    "dartmouth-history-ab": (
        "Students who love archives, argument, and understanding the past across world "
        "regions, with paths into law, public service, and graduate study."
    ),
    "dartmouth-mathematics-ab": (
        "Students with a love of rigorous reasoning who want options in pure, applied, or "
        "computational mathematics and quantitative careers."
    ),
    "dartmouth-music-ab": (
        "Performers, composers, and scholars of music who want conservatory-style "
        "opportunities within a liberal-arts setting."
    ),
    "dartmouth-neuroscience-ab": (
        "Students fascinated by the brain and behavior — often pre-health or research-bound "
        "— who want integrated biology, chemistry, and psychology with lab work."
    ),
    "dartmouth-philosophy-ab": (
        "Students who enjoy rigorous argument about ethics, knowledge, and reality and want "
        "sharp analytical and writing skills for law, policy, or academia."
    ),
    "dartmouth-physics-ab": (
        "Students drawn to how the universe works, from quantum mechanics to astrophysics, "
        "who want strong theory and research toward science or engineering careers."
    ),
    "dartmouth-psychological-and-brain-sciences-ab": (
        "Students interested in mind, behavior, and the brain who want laboratory and "
        "neuroimaging research with paths into health, research, or graduate study."
    ),
    "dartmouth-quantitative-social-science-ab": (
        "Data-minded students who want to apply statistics and causal inference to questions "
        "in politics, economics, and society."
    ),
    "dartmouth-religion-ab": (
        "Students curious about the world's religious traditions and how belief shapes "
        "culture, history, and politics."
    ),
    "dartmouth-sociology-ab": (
        "Students interested in inequality, institutions, and social change who want both "
        "social theory and quantitative and qualitative research methods."
    ),
    "dartmouth-spanish-ab": (
        "Students who want advanced Spanish fluency and deep engagement with the literatures "
        "and cultures of Spain and Latin America, often with study abroad."
    ),
    "dartmouth-studio-art-ab": (
        "Students serious about making art who want studio-intensive training and critique "
        "across drawing, painting, sculpture, photography, and digital media."
    ),
    "dartmouth-theater-ab": (
        "Students passionate about performance and production who want hands-on training in "
        "acting, directing, and design at the Hopkins Center."
    ),
    "dartmouth-linguistics-ab": (
        "Students fascinated by how language works who want to study its structure and its "
        "cognitive and computational dimensions."
    ),
    "dartmouth-african-and-african-american-studies-ab": (
        "Students who want to study the histories, cultures, politics, and creative "
        "expression of Africa and its diasporas across disciplines."
    ),
    "dartmouth-engineering-sciences-ab": (
        "Undergraduates who want a broad, project-based engineering foundation with "
        "liberal-arts breadth and the option to continue to the professional Bachelor of "
        "Engineering."
    ),
    "dartmouth-engineering-ab": (
        "Engineering-sciences students who want an ABET-accredited professional bachelor's "
        "with a fifth year of design and engineering depth before industry or graduate study."
    ),
    "dartmouth-engineering-management-ms": (
        "Early-career engineers and technical graduates who want to add management, finance, "
        "and operations skills to move into product, operations, and leadership roles."
    ),
    "dartmouth-engineering-graduate-ms": (
        "Engineering graduates seeking advanced technical depth and design experience as "
        "preparation for industry practice or further research."
    ),
    "dartmouth-engineering-doctorate-phd": (
        "Students pursuing original engineering research across biomedical, energy, "
        "materials, and computational fields who want a flexible, interdisciplinary doctorate."
    ),
    "dartmouth-business-administration-ms": (
        "Early-career professionals seeking a small, immersive, two-year general-management "
        "MBA with strong consulting and finance placement and a close-knit residential "
        "community."
    ),
    "dartmouth-medicine-prof": (
        "Students committed to becoming physicians who value a small, collaborative class, "
        "early clinical immersion, and a community- and primary-care–oriented curriculum."
    ),
    "dartmouth-public-health-ms": (
        "Clinicians, scientists, and emerging health leaders who want rigorous training in "
        "epidemiology, biostatistics, and health-system improvement at The Dartmouth "
        "Institute."
    ),
    "dartmouth-computer-science-phd": (
        "Students pursuing a research career in computing who want close mentorship in a "
        "small doctoral program spanning systems, theory, machine learning, and security."
    ),
    "dartmouth-computer-science-ms": (
        "Graduates seeking advanced computing coursework and research preparation before a "
        "PhD or a technical industry role."
    ),
    "dartmouth-chemistry-phd": (
        "Students committed to chemistry research who want immersive laboratory training "
        "across synthetic, physical, biological, and materials chemistry."
    ),
    "dartmouth-physics-and-astronomy-phd": (
        "Students pursuing doctoral research in astrophysics, space physics, or "
        "condensed-matter and quantum physics."
    ),
    "dartmouth-psychological-and-brain-sciences-phd": (
        "Students pursuing research careers in cognitive, systems, social, and affective "
        "neuroscience using behavioral and neuroimaging methods."
    ),
    "dartmouth-liberal-studies-ms": (
        "Curious adults and lifelong learners who want a flexible, interdisciplinary "
        "graduate degree across the humanities, sciences, and social sciences, including "
        "creative writing."
    ),
    "dartmouth-mathematics-phd": (
        "Students pursuing doctoral research in pure, applied, or computational mathematics "
        "who want small cohorts and close faculty mentorship."
    ),
    "dartmouth-earth-sciences-phd": (
        "Students pursuing original geoscience research in areas such as paleoclimate, polar "
        "science, geobiology, and tectonics."
    ),
    "dartmouth-earth-sciences-ms": (
        "Graduates seeking advanced geoscience training and a research project as a bridge "
        "to doctoral study or environmental and geoscience careers."
    ),
    "dartmouth-ecology-evolution-environment-and-society-phd": (
        "Students who want interdisciplinary doctoral research spanning ecology, evolution, "
        "environmental science, and the human dimensions of environmental change."
    ),
    "dartmouth-molecular-and-cellular-biology-phd": (
        "Aspiring biomedical researchers who want an umbrella program with rotations across "
        "biochemistry, cancer biology, microbiology and immunology, and molecular systems "
        "biology."
    ),
    "dartmouth-quantitative-biomedical-sciences-phd": (
        "Quantitatively strong students who want to apply biostatistics, bioinformatics, and "
        "computational biology to biomedical and population-health research."
    ),
    "dartmouth-computational-science-and-modeling-phd": (
        "Students from the sciences, engineering, or mathematics who want to build "
        "computational and modeling expertise for research across disciplines."
    ),
    "dartmouth-integrative-neuroscience-phd": (
        "Students pursuing doctoral neuroscience research who want to work across molecules, "
        "systems, cognition, and behavior and across departments."
    ),
    "dartmouth-health-policy-and-clinical-practice-phd": (
        "Clinicians and researchers who want doctoral training in health-services research, "
        "health economics, and the evaluation of clinical practice and policy."
    ),
    "dartmouth-chemistry-ms": (
        "Dartmouth undergraduates and other students who want advanced chemistry coursework "
        "and thesis research, often via the 4+1 pathway or as preparation for doctoral study."
    ),
    "dartmouth-comparative-literature-ms": (
        "Students who want to study literature across languages and cultures with grounding "
        "in literary theory before doctoral work or careers in writing and the humanities."
    ),
    "dartmouth-sonic-practice-ms": (
        "Sound artists, composers, and experimental musicians seeking a studio-based "
        "terminal degree that blends creative practice, technology, and the critical study "
        "of sound."
    ),
    "dartmouth-epidemiology-ms": (
        "Clinicians and researchers who want rigorous training in study design, "
        "biostatistics, and causal inference to investigate disease in populations."
    ),
    "dartmouth-health-data-science-ms": (
        "Quantitatively minded clinicians and analysts who want to apply statistics, machine "
        "learning, and programming to clinical, genomic, and population-health data."
    ),
    "dartmouth-healthcare-research-ms": (
        "Practicing clinicians and researchers who want graduate training in health-services "
        "research methods, outcomes measurement, and health-system improvement."
    ),
    "dartmouth-implementation-science-ms": (
        "Working health professionals who want an online master's to learn how to translate "
        "evidence into practice through implementation and improvement science."
    ),
    "dartmouth-medical-informatics-ms": (
        "Clinicians and technologists who want to apply information systems and data "
        "standards to clinical care, decision support, and health-information exchange."
    ),
    "dartmouth-energy-transition-ms": (
        "Early-career professionals who want an interdisciplinary, residential master's "
        "combining energy science, policy, economics, and business to lead the clean-energy "
        "transition."
    ),
}

# Fail fast at import if cip / who drift from the catalog (self-validating, SKILL §8.5).
_missing_cip = [s for s in PROGRAM_SLUGS if s not in _CIP_BY_SLUG]
_missing_who = [s for s in PROGRAM_SLUGS if s not in _WHO_BY_SLUG]
_stray_cip = [s for s in _CIP_BY_SLUG if s not in _SPEC_BY_SLUG]
_stray_who = [s for s in _WHO_BY_SLUG if s not in _SPEC_BY_SLUG]
if _missing_cip or _missing_who or _stray_cip or _stray_who:
    raise RuntimeError(
        f"cip/who out of sync with catalog: missing_cip={_missing_cip} "
        f"missing_who={_missing_who} stray_cip={_stray_cip} stray_who={_stray_who}"
    )

# ── Costs ──────────────────────────────────────────────────────────────────
_TUITION_UG = 66123
_UNDERGRAD_COA = 95490
_AVG_NET_PRICE = 29519
_COST_SRC = (
    "Dartmouth Financial Aid 2025-26 cost of attendance + College Scorecard (UNITID 182670)",
    "https://financialaid.dartmouth.edu/cost-attendance/cost-attendance-2025-2026",
)

# ── Published graduate-tier tuition (REPAIR_BACKLOG #4 — master's/professional
# starvation behind a 100% bachelor's tier) ──────────────────────────────────
_THAYER_TUITION_SRC = (
    "Thayer School of Engineering — Tuition & Cost of Attendance 2026-27",
    "https://engineering.dartmouth.edu/about/financial-aid/tuition-cost-of-attendance",
)
_TUCK_TUITION_SRC = (
    "Tuck School of Business — Cost of Attendance 2026-27",
    "https://tuck.dartmouth.edu/admissions/finance-your-degree/cost-attendance",
)
_GEISEL_MD_SRC = (
    "Geisel School of Medicine — M.D. Cost of Attendance 2026-27",
    "https://geiselmed.dartmouth.edu/financial-aid/info/cost-of-attendance/",
)
_MPH_TUITION_SRC = (
    "Dartmouth Health Sciences — MPH and MS tuition 2026-27",
    "https://healthsciences.dartmouth.edu/education/admissions/tuition-fees",
)
_GUARINI_TUITION_SRC = (
    "Guarini School — Tuition & Living Costs 2026-27",
    "https://graduate.dartmouth.edu/admissions-financial-aid/tuition-living-costs",
)
_THAYER_TERM = 23899  # per quarter
_THAYER_MENG = _THAYER_TERM * 3  # MEng on-campus (3 terms)
_THAYER_MEM = _THAYER_TERM * 4  # MEM (4 terms plus summer internship)
_TUCK_MBA = 87536
_GEISEL_MD = 75110
_MPH_ONCAMPUS = 82232
_GUARINI_4TERM = 95596  # standard Guarini full-time (4 quarters)
_MALS_FT_4TERM = 66917  # MALS full-time 4-quarter tuition (rounded from $66,917.20)


def _annual_grad_cost(
    tuition_usd: int,
    *,
    note: str,
    source: str,
    source_url: str,
    year: str = "2026-27",
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
    "dartmouth-engineering-graduate-ms": _annual_grad_cost(
        _THAYER_MENG,
        note=(
            f"Thayer on-campus Master of Engineering tuition: "
            f"${_THAYER_TERM:,} per quarter × three quarters "
            f"(${_THAYER_MENG:,} program tuition for the three-term MEng)."
        ),
        source=_THAYER_TUITION_SRC[0],
        source_url=_THAYER_TUITION_SRC[1],
    ),
    "dartmouth-engineering-management-ms": _annual_grad_cost(
        _THAYER_MEM,
        note=(
            f"Thayer/Tuck Master of Engineering Management: "
            f"${_THAYER_TERM:,} per quarter × four quarters "
            f"(${_THAYER_MEM:,} program tuition; includes a summer internship term)."
        ),
        source=_THAYER_TUITION_SRC[0],
        source_url=_THAYER_TUITION_SRC[1],
    ),
    "dartmouth-business-administration-ms": _annual_grad_cost(
        _TUCK_MBA,
        note=(
            f"Tuck full-time MBA academic-year tuition (${_TUCK_MBA:,}; "
            "2026-27 rate, billed in equal installments across the MBA terms)."
        ),
        source=_TUCK_TUITION_SRC[0],
        source_url=_TUCK_TUITION_SRC[1],
    ),
    "dartmouth-medicine-prof": _annual_grad_cost(
        _GEISEL_MD,
        note=(
            f"Geisel School of Medicine M.D. tuition (${_GEISEL_MD:,} per year; "
            "direct cost billed each academic year of the four-year program)."
        ),
        source=_GEISEL_MD_SRC[0],
        source_url=_GEISEL_MD_SRC[1],
    ),
    "dartmouth-public-health-ms": _annual_grad_cost(
        _MPH_ONCAMPUS,
        note=(
            f"On-campus Master of Public Health tuition (${_MPH_ONCAMPUS:,} per "
            "academic year at The Dartmouth Institute for Health Policy & Clinical "
            "Practice)."
        ),
        source=_MPH_TUITION_SRC[0],
        source_url=_MPH_TUITION_SRC[1],
    ),
    "dartmouth-computer-science-ms": _annual_grad_cost(
        _GUARINI_4TERM,
        note=(
            f"Guarini full-time graduate tuition: ${_THAYER_TERM:,} per quarter "
            f"× four quarters (${_GUARINI_4TERM:,} annual full-time rate)."
        ),
        source=_GUARINI_TUITION_SRC[0],
        source_url=_GUARINI_TUITION_SRC[1],
    ),
    "dartmouth-liberal-studies-ms": _annual_grad_cost(
        _MALS_FT_4TERM,
        note=(
            f"MALS full-time tuition: four-quarter rate of ${_MALS_FT_4TERM:,} "
            "(Guarini published MALS full-time cost of attendance table)."
        ),
        source=_GUARINI_TUITION_SRC[0],
        source_url=_GUARINI_TUITION_SRC[1],
    ),
    # Guarini full-time on-campus research master's — the published uniform Guarini rate
    # ($23,899/quarter × 4 quarters = $95,596). Verified on the Guarini tuition page.
    "dartmouth-chemistry-ms": _annual_grad_cost(
        _GUARINI_4TERM,
        note=(
            f"Guarini full-time graduate tuition: ${_THAYER_TERM:,} per quarter × four "
            f"quarters (${_GUARINI_4TERM:,} annual full-time rate)."
        ),
        source=_GUARINI_TUITION_SRC[0],
        source_url=_GUARINI_TUITION_SRC[1],
    ),
    "dartmouth-comparative-literature-ms": _annual_grad_cost(
        _GUARINI_4TERM,
        note=(
            f"Guarini full-time graduate tuition: ${_THAYER_TERM:,} per quarter × four "
            f"quarters (${_GUARINI_4TERM:,} annual full-time rate)."
        ),
        source=_GUARINI_TUITION_SRC[0],
        source_url=_GUARINI_TUITION_SRC[1],
    ),
    "dartmouth-earth-sciences-ms": _annual_grad_cost(
        _GUARINI_4TERM,
        note=(
            f"Guarini full-time graduate tuition: ${_THAYER_TERM:,} per quarter × four "
            f"quarters (${_GUARINI_4TERM:,} annual full-time rate)."
        ),
        source=_GUARINI_TUITION_SRC[0],
        source_url=_GUARINI_TUITION_SRC[1],
    ),
    "dartmouth-sonic-practice-ms": _annual_grad_cost(
        _GUARINI_4TERM,
        note=(
            f"Guarini full-time graduate tuition: ${_THAYER_TERM:,} per quarter × four "
            f"quarters (${_GUARINI_4TERM:,} annual full-time rate; the MFA is a two-year "
            "studio program billed at the standard Guarini full-time rate)."
        ),
        source=_GUARINI_TUITION_SRC[0],
        source_url=_GUARINI_TUITION_SRC[1],
    ),
}


def _grad_has_verified_tuition(spec: dict) -> bool:
    return spec["slug"] in _COST_BY_SLUG


# ── Outcomes ──────────────────────────────────────────────────────────────
# Dartmouth reports career outcomes college-wide (no per-program employment split), so
# every program carries the institution-wide College Scorecard median earnings and omits
# the program-level employment_rate / top_industries (recorded in _program_standard).
_OUTCOMES_CONDITIONS = (
    "Institution-wide median earnings of federally aided students measured 10 years after "
    "entry (U.S. Dept. of Education College Scorecard); not a program-specific figure."
)
_OUTCOMES_INSTITUTION = {
    "median_salary": 97434,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry (institution-wide)",
    "conditions": _OUTCOMES_CONDITIONS,
    "source": "U.S. Dept. of Education College Scorecard (Dartmouth, UNITID 182670)",
    "source_url": "https://collegescorecard.ed.gov/school/?182670",
}

# ── Admissions requirement sets ────────────────────────────────────────────
_REQ_UNDERGRAD = {
    "materials": [
        "Common Application or Coalition Application",
        "Dartmouth writing supplement",
        "Secondary-school report + transcript",
        "Two teacher evaluations + counselor recommendation",
        "SAT or ACT scores (standardized testing required for 2025-26)",
    ],
    "deadlines": {
        "early_decision": "November 1",
        "regular_decision": "January 3",
    },
    "source": "https://admissions.dartmouth.edu/apply",
}
_REQ_GRAD_GENERIC = {
    "materials": [
        "Online application",
        "Transcripts from all prior institutions",
        "Letters of recommendation",
        "Statement of purpose",
        "Standardized/English-proficiency scores where required by the program",
    ],
    "deadlines": {
        "note": "Deadlines vary by program; see the program's official admissions page.",
    },
    "source": "https://graduate.dartmouth.edu/admissions",
}
_REQ_MBA = {
    "materials": [
        "Tuck application + essays",
        "GMAT, GRE, or EA score (Tuck accepts test waivers in some cases)",
        "Undergraduate transcripts",
        "Two recommendations",
        "Resume + interview",
    ],
    "deadlines": {
        "round_1": "September (early action)",
        "round_2": "January",
        "round_3": "March",
    },
    "source": "https://www.tuck.dartmouth.edu/admissions",
}

# ── Tracks / class profile / reviews (depth on the flagship) ───────────────
_TRACKS_BY_SLUG: dict[str, dict] = {
    "dartmouth-liberal-studies-ms": {
        "tracks": [
            "Cultural Studies",
            "Globalization Studies",
            "Creative Writing",
            "General Liberal Studies",
        ],
        "source": "Master of Arts in Liberal Studies — concentrations",
        "source_url": "https://graduate.dartmouth.edu/",
    },
    "dartmouth-molecular-and-cellular-biology-phd": {
        "tracks": [
            "Biochemistry and Cell Biology",
            "Cancer Biology",
            "Microbiology and Immunology",
            "Molecular and Systems Biology",
            "Biological Sciences",
        ],
        "source": "Guarini — Molecular and Cellular Biology PhD specializations",
        "source_url": "https://graduate.dartmouth.edu/academics/programs",
    },
}
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "cohort_size": "About 290 students per entering Tuck MBA class",
        "source": "Tuck School of Business — class profile",
        "source_url": "https://www.tuck.dartmouth.edu/admissions/class-profile",
    },
}
_FACULTY_BY_SLUG: dict[str, dict] = {}

# Gathered third-party coverage of the Tuck MBA (the obvious coverable flagship). The rest
# of the catalog's review depth is IN-FLIGHT (omitted-with-reason) for the next run.
_REVIEWS_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "summary": (
            "Reviewers and rankings consistently describe the Tuck MBA as a small, "
            "intensely collaborative, residential general-management program with "
            "exceptional alumni loyalty and strong consulting/finance placement. Common "
            "cautions are Hanover's rural isolation, a smaller recruiting footprint than "
            "MBAs in major cities, and a tight-knit culture that suits students seeking "
            "community over a large urban program."
        ),
        "themes": [
            {
                "label": "Tight-knit cohort",
                "sentiment": "positive",
                "detail": (
                    "A small, fully residential class drives close faculty access and "
                    "famously loyal alumni who answer student outreach."
                ),
            },
            {
                "label": "Consulting & finance placement",
                "sentiment": "positive",
                "detail": (
                    "Graduates place strongly into management consulting and financial "
                    "services, with technology a growing share."
                ),
            },
            {
                "label": "General-management depth",
                "sentiment": "positive",
                "detail": (
                    "A team-based, leadership-focused core curriculum over two full "
                    "years builds broad management capability."
                ),
            },
            {
                "label": "Rural location",
                "sentiment": "mixed",
                "detail": (
                    "Hanover's setting is a draw for community but means less proximity "
                    "to a major-city employer market than urban MBAs."
                ),
            },
        ],
        "sources": [
            {
                "label": "Poets&Quants — Dartmouth Tuck MBA coverage",
                "url": (
                    "https://poetsandquants.com/2024/12/09/"
                    "dartmouth-tuck-mbas-got-results-dodged-worst-of-what-2024-threw-at-them/"
                ),
            },
            {
                "label": "Clear Admit — Dartmouth Tuck MBA Employment Report (Class of 2024)",
                "url": (
                    "https://www.clearadmit.com/2024/12/"
                    "dartmouth-tuck-mba-employment-report-class-of-2024/"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "dartmouth-medicine-prof": {
        "summary": (
            "Coverage of the Geisel School of Medicine consistently highlights a small, "
            "tightly knit class, early and longitudinal clinical exposure, and strengths in "
            "primary care and community medicine; U.S. News places Geisel in the top tier "
            "for primary care. Common cautions are the rural Hanover/Lebanon setting, a "
            "smaller research-funding base than the largest academic medical centers, and "
            "limited big-city clinical volume relative to urban schools."
        ),
        "themes": [
            {
                "label": "Small, collaborative class",
                "sentiment": "positive",
                "detail": (
                    "About 92 students per entering class supports close faculty contact "
                    "and a community the Princeton Review describes as collaborative rather "
                    "than competitive."
                ),
            },
            {
                "label": "Early clinical immersion",
                "sentiment": "positive",
                "detail": (
                    "An integrated curriculum (Foundations, Clinical Immersion, and "
                    "Exploration phases) moves students into required clerkships across six "
                    "disciplines early in the second year."
                ),
            },
            {
                "label": "Primary care & community focus",
                "sentiment": "positive",
                "detail": (
                    "Geisel ranks in U.S. News's top tier for primary care, with strong "
                    "community-service participation and population-health teaching."
                ),
            },
            {
                "label": "Rural location",
                "sentiment": "mixed",
                "detail": (
                    "The Hanover/Lebanon setting offers community and access to Dartmouth "
                    "Health but less big-city clinical volume than urban medical schools."
                ),
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Dartmouth (Geisel) Best Medical Schools",
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-medical-schools/"
                    "dartmouth-college-04065"
                ),
            },
            {
                "label": "Student Doctor Network — Dartmouth Geisel School of Medicine",
                "url": (
                    "https://www.studentdoctor.net/schools-database/medical-school/detail/"
                    "DMS/dartmouth-geisel-school-of-medicine"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources (U.S. News, "
            "Student Doctor Network, Princeton Review) — not individual verbatim reviews."
        ),
    },
}

# Dartmouth's campus-photo gallery (4–5 verified, credited entries) is already on the
# institution seed; apply() leads media_gallery with its [0] rather than a module constant.
def _lead_campus_photo(school_outcomes: dict) -> str | None:
    photos = (school_outcomes or {}).get("campus_photos") or []
    if photos and isinstance(photos[0], dict):
        return photos[0].get("url")
    return None


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def _program_standard(slug: str, spec: dict) -> dict:
    omitted: list[str] = []
    # Every program carries the institution-wide College Scorecard earnings (Dartmouth
    # publishes no per-program employment rate or industry split), so the program-level
    # employment_rate / top_industries are omitted on every node.
    omitted += ["outcomes_data.employment_rate", "outcomes_data.top_industries"]
    if spec["degree_type"] != "bachelors" and not _grad_has_verified_tuition(spec):
        omitted.append("cost_data.tuition_usd")
    if slug not in _TRACKS_BY_SLUG:
        omitted.append("tracks")
    if slug not in _CLASS_PROFILE_BY_SLUG:
        omitted.append("class_profile.cohort_size")
    if slug not in _FACULTY_BY_SLUG:
        omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    return _standard(omitted)


def _requirements_for(spec: dict) -> dict:
    if spec["slug"] == _FLAGSHIP:
        return dict(_REQ_MBA)
    if spec["degree_type"] == "bachelors":
        return dict(_REQ_UNDERGRAD)
    return dict(_REQ_GRAD_GENERIC)


def apply(session: Session) -> bool:
    """Enrich Dartmouth to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Dartmouth is absent — safe on fresh/CI databases.
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
    inst.founded_year = 1769
    inst.campus_setting = "rural"
    if not inst.website_url:
        inst.website_url = "https://home.dartmouth.edu"
    lead_photo = _lead_campus_photo(school_outcomes)
    if lead_photo:
        _gallery = [u for u in (inst.media_gallery or []) if u != lead_photo]
        inst.media_gallery = [lead_photo, *_gallery]
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
        p.department = spec["department"]
        p.duration_months = spec["duration_months"]
        p.description_text = spec["description"]
        p.website_url = _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec["delivery_format"]
        p.content_sources = _program_content(spec["school"], spec["keywords"])
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
                    "Published 2025-26 Dartmouth undergraduate tuition with the financial-"
                    "aid office's cost of attendance and the College Scorecard average net "
                    "price. Dartmouth meets 100% of demonstrated financial need, so most "
                    "families pay far less than the sticker price (average net price "
                    "≈ $30,000)."
                ),
                "source": _COST_SRC[0],
                "source_url": _COST_SRC[1],
                "year": "2025-26",
            }
        else:
            # Tuition honestly omitted-with-reason: PhDs are funded; the Geisel-based
            # health master's bill per-credit / part-time / online; the new Master of
            # Energy Transition publishes its own rate. Never the undergrad sticker copied
            # down, never an estimate (SKILL omit-never-guess).
            p.tuition = None
            school_src = _SCHOOL_WEBSITE.get(spec["school"], "https://graduate.dartmouth.edu/")
            p.cost_data = {
                "funded": spec["degree_type"] == "phd",
                "note": (
                    "Doctoral students at Dartmouth are typically funded via research "
                    "grants or fellowships; tuition is waived for funded PhD students. "
                    "See the Guarini School or Thayer School tuition schedule for the "
                    "published sticker."
                    if spec["degree_type"] == "phd"
                    else (
                        "Tuition for this professional/health-sciences master's is "
                        "published on the program's official cost page (per-credit, "
                        "part-time, or program-specific); a verified per-program figure is "
                        "omitted here rather than estimated."
                    )
                ),
                "source": f"{spec['school']} — official program page",
                "source_url": school_src,
            }
        p.cip_code = _CIP_BY_SLUG.get(slug)
        p.application_requirements = _requirements_for(spec)
        outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        p.who_its_for = _WHO_BY_SLUG.get(slug)
        p.highlights = None
        p.application_deadline = (
            date(2027, 1, 3) if spec["degree_type"] == "bachelors" else None
        )
    session.flush()
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
