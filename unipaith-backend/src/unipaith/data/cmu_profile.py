"""Canonical Carnegie Mellon University profile — the single source of truth.

Real, sourced data only (U.S. Dept. of Education College Scorecard / NCES College
Navigator, UNITID 211440 · Carnegie Mellon's official Common Data Set 2024-25,
published by the Office of Institutional Research & Analysis · CMU's official
Rankings & Awards page · the official QS / Times Higher Education / U.S. News
rankings · each college's official leadership / about page). ``apply(session)``
idempotently enriches the Carnegie Mellon institution row, upserts its seven real
degree-granting colleges/schools, and builds CMU's undergraduate program catalog
across them.

Carnegie Mellon admits undergraduates into six colleges (the seventh, Heinz
College, is a graduate college); the platform's ``School`` model carries all seven
so the institution tree is complete, with the undergraduate program catalog mapped
onto the six undergraduate colleges:
  - School of Computer Science (SCS)
  - College of Engineering (Carnegie Institute of Technology)
  - Mellon College of Science (MCS)
  - Dietrich College of Humanities and Social Sciences
  - College of Fine Arts (CFA)
  - Tepper School of Business
  - Heinz College of Information Systems and Public Policy (graduate)

It **flushes but does not commit** — the caller (the Alembic data migration, the
CLI script, or the dev seed) owns the transaction. It is a **no-op** (returns
``False``) when Carnegie Mellon is absent, so it is safe to run against a fresh or
CI database. Re-running is safe: colleges key off ``(institution_id, name)`` and
programs off ``slug``; stale rows are reconciled without breaking foreign keys.

This mirrors ``mit_profile`` / ``berkeley_profile`` so the migration, the
standalone script, and the dev seed all agree (DRY). Every figure traces to a
public, citable source; anything that could not be verified from a first-party or
two-independent-source basis is **omitted** (recorded in the relevant
``_standard.omitted`` list), never guessed. The Computer Science (B.S.) major is
the most-enriched flagship program (its real concentrations, Turing-laureate
faculty, and aggregated reviews), mirroring MIT Sloan's MBAn in the reference
instance — with the honest caveats that CMU publishes its institution-wide
first-destination outcomes only through an interactive dashboard (so the
institution-wide placement rate and industry breakdown are omitted) and that this
run ships Carnegie Mellon's complete UNDERGRADUATE tree; its department-level
graduate programs are the resumption scope for a later run.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Carnegie Mellon University"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-10"


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
    # CMU's Career & Professional Development Center publishes university-wide
    # first-destination outcomes only through an interactive (Tableau/JS) dashboard
    # that does not render to static text, so a verified institution-wide "employed
    # or continuing education" rate and a top-employer-industries breakdown could
    # not be sourced. Program-/college-level figures exist but are not institution
    # wide; we omit rather than assert.
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
    # CMU does not publish a single official count of "research centers"; the named
    # institutes are surfaced under research.labs / per-college research_centers
    # instead.
    "school_outcomes.scale.research_centers",
]

# ── Institution-level data ────────────────────────────────────────────────
# Rankings are stored as {rank, year} objects because the page renders every
# ranking_data entry that is an object with a numeric `rank`. Ownership / Carnegie /
# accreditor + the three world/national ranks are quoted from the official ranking
# bodies and CMU's Rankings & Awards page.
RANKING_DATA: dict = {
    "ownership_type": "private",
    "accreditor": "MSCHE (Middle States Commission on Higher Education)",
    "carnegie_classification": (
        "R1: Doctoral Universities – Very High Research Spending and Doctorate "
        "Production"
    ),
    # QS World University Rankings 2026.
    "qs_world_university_rankings": {
        "rank": 52,
        "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/carnegie-mellon-university",
    },
    # THE World University Rankings 2026.
    "times_higher_education": {
        "rank": 24,
        "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/carnegie-mellon-university",
    },
    # U.S. News Best Colleges (National Universities) 2026.
    "us_news_national": {
        "rank": 20,
        "year": 2026,
        "source_url": "https://www.usnews.com/best-colleges/carnegie-mellon-university-3242",
    },
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below
# is complete, so a shallow merge is correct. Figures are CMU's first-party Common
# Data Set 2024-25 (Office of Institutional Research & Analysis) and the U.S. Dept.
# of Education College Scorecard / NCES College Navigator (UNITID 211440), with the
# source noted per metric below.
SCHOOL_OUTCOMES: dict = {
    # CDS 2024-25 §C1: 3,959 admitted / 33,941 first-year applicants = 11.66%.
    "admit_rate": 0.1166,
    # NCES College Navigator (federal IPEDS) average net price, 2023-24.
    "avg_net_price": 35552,
    # College Scorecard: median earnings 10 years after entry (UNITID 211440).
    "median_earnings_10yr": 114862,
    # CDS 2024-25 §B: six-year graduation rate (Fall 2018 cohort) = 94.1%.
    "completion_rate_4yr_150pct": 0.941,
    # CDS 2024-25 §B22: first-year retention (Fall 2023 → Fall 2024) = 98%.
    "retention_rate_first_year": 0.98,
    "graduation_rate_6yr": 0.941,
    "financial_aid": {
        # NCES College Navigator (federal IPEDS, 2023-24).
        "pell_grant_rate": 0.16,
        "federal_loan_rate": 0.34,
        # CDS 2024-25 §G1: first-year on-campus cost of attendance 2025-26
        # (tuition $67,020 + fees $1,756 + room & board $18,894).
        "cost_of_attendance": 87670,
        # CDS 2024-25 §H5: median federal cumulative principal borrowed by the
        # 2024 bachelor's-degree class who borrowed federal loans.
        "median_debt_completers": 18200,
    },
    # Undergraduate race/ethnicity from the CDS 2024-25 §B2 "Total Undergraduates"
    # column (base 7,824, all campuses, as of Oct 15, 2024). Women share is women
    # ÷ all undergraduates (CMU reports a third gender category).
    "demographics": {
        "white": 0.205,
        "black": 0.038,
        "hispanic": 0.094,
        "asian": 0.323,
        "two_or_more": 0.050,
        "international": 0.233,
        "women": 0.474,
    },
    # SAT/ACT 25th–75th percentile for enrolled first-years (CDS 2024-25 §C9).
    "test_scores": {
        "sat_reading_25_75": [730, 770],
        "sat_math_25_75": [770, 800],
        "act_25_75": [34, 35],
        "policy": "test-optional",
        "note": (
            "CMU is test-optional ('consider if submitted'); 52.6% of enrolled "
            "first-years submitted the SAT and 22.4% the ACT (CDS 2024-25 §C8–C9)."
        ),
    },
    # CMU's main campus in the Oakland neighborhood of Pittsburgh.
    "location": {"lat": 40.4433, "lng": -79.9436},
    "campus_basics": {"location": "Pittsburgh, Pennsylvania"},
    "scale": {
        "faculty_count": 1615,
        "student_faculty_ratio": "6:1",
        # CMU official: endowment ~$3.2 billion as of June 30, 2024 (FY2024).
        "endowment_usd": 3200000000,
        "campus_acres": 157,
    },
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
        # The frontend renders resources as {label, url}.
        "resources": [
            {
                "label": "Get Involved — Student Affairs",
                "url": "https://www.cmu.edu/student-affairs/get-involved/index.html",
            },
            {
                "label": "Student Involvement & Traditions",
                "url": "https://www.cmu.edu/student-affairs/sit/involvement/index.html",
            },
            {
                "label": "Carnegie Mellon Athletics (Tartans)",
                "url": "https://athletics.cmu.edu/",
            },
            {"label": "CMU Events Calendar", "url": "https://events.cmu.edu/"},
            {
                "label": "Center for Student Diversity and Inclusion",
                "url": "https://www.cmu.edu/student-diversity/",
            },
        ],
    },
    "flagship": {
        # CDS 2024-25 §B1 "GRAND TOTAL ALL STUDENTS" (7,824 undergrad + 8,852 grad).
        "enrollment_total": 16676,
        # CDS 2024-25 §C1 first-year admissions cycle (Fall 2024, Pittsburgh campus).
        "applicants": 33941,
        "admits": 3959,
        "admissions_cycle": "Entering class fall 2024 (CMU Common Data Set 2024-25)",
        # CMU official Rankings & Awards page (faculty + alumni).
        "nobel_laureates": 21,
        "turing_awards": 13,
        # Founded by Andrew Carnegie as the Carnegie Technical Schools in 1900.
        "founded_year": 1900,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Carnegie Mellon, UNITID 211440)",
            "url": "https://collegescorecard.ed.gov/school/?211440-Carnegie-Mellon-University",
        },
        {
            "label": (
                "Carnegie Mellon — Common Data Set 2024-2025 (Office of Institutional Research & "
                "Analysis)"
            ),
            "url": "https://www.cmu.edu/ira/CDS/cds_2425.html",
        },
        {
            "label": "NCES College Navigator — Carnegie Mellon University (UNITID 211440)",
            "url": "https://nces.ed.gov/collegenavigator/?id=211440",
        },
        {
            "label": "Carnegie Mellon — Rankings & Awards (Nobel / Turing tally)",
            "url": "https://www.cmu.edu/about/rankings-and-awards",
        },
        {
            "label": "Carnegie Mellon — History (founded 1900)",
            "url": "https://www.cmu.edu/about/history",
        },
        {
            "label": "Carnegie Mellon — endowment $3.2B in FY2024 (CMU News)",
            "url": (
                "https://www.cmu.edu/news/stories/archives/2024/october/"
                "carnegie-mellon-endowment-stands-at-32b-in-2024"
            ),
        },
        {
            "label": "QS World University Rankings 2026 — Carnegie Mellon University",
            "url": "https://www.topuniversities.com/universities/carnegie-mellon-university",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — Carnegie Mellon",
            "url": "https://www.timeshighereducation.com/world-university-rankings/carnegie-mellon-university",
        },
        {
            "label": "U.S. News Best Colleges 2026 — Carnegie Mellon University",
            "url": "https://www.usnews.com/best-colleges/carnegie-mellon-university-3242",
        },
    ],
}

# student_body_size is the undergraduate headcount (the page labels it
# "Undergraduates"); the total (16,676) lives in flagship.enrollment_total and
# renders as "Total enrollment". 7,824 = CDS 2024-25 §B1 total undergraduates.
UNDERGRAD_COUNT = 7824

DESCRIPTION = (
    "Carnegie Mellon University is a private research university in Pittsburgh, "
    "Pennsylvania, formed in 1967 by the merger of the Carnegie Institute of "
    "Technology — founded by the industrialist Andrew Carnegie in 1900 as the "
    "Carnegie Technical Schools — and the Mellon Institute of Industrial Research. "
    "It is an R1 doctoral university accredited by the Middle States Commission on "
    "Higher Education, and it enrolls roughly 7,800 undergraduates and about 8,900 "
    "graduate students, some 16,700 students in all.\n\n"
    "The university is organized into seven colleges and schools: the School of "
    "Computer Science; the College of Engineering (historically the Carnegie "
    "Institute of Technology); the Mellon College of Science; the Dietrich College "
    "of Humanities and Social Sciences; the College of Fine Arts; the Tepper "
    "School of Business; and the graduate Heinz College of Information Systems and "
    "Public Policy. CMU is home to the world's first Robotics Institute (1979) and "
    "to the nation's first undergraduate degree in artificial intelligence (2018), "
    "and it operates the federally funded Software Engineering Institute on behalf "
    "of the U.S. Department of Defense.\n\n"
    "Carnegie Mellon is consistently ranked among the world's leading universities "
    "— No. 24 in the world by Times Higher Education, No. 52 by QS, and No. 20 "
    "nationally by U.S. News — and is especially renowned for computer science, "
    "engineering, and the arts. By the university's own tally, 21 Nobel laureates "
    "and 13 Turing Award winners are associated with CMU, and it admits about 12% "
    "of first-year applicants from a pool of nearly 34,000.\n\n"
    "Admission is highly selective: enrolled first-years post mid-50% SAT scores "
    "of about 730–770 (reading) and 770–800 (math), 98% of first-years return for "
    "a second year, and 94% graduate within six years. The on-campus cost of "
    "attendance is about $87,700 a year and the average net price is roughly "
    "$35,600; CMU graduates earn a median income of about $114,900 a decade after "
    "entry."
)

# ── The seven real degree-granting colleges/schools (display order) ─────────
_SCS = "School of Computer Science"
_ENG = "College of Engineering"
_MCS = "Mellon College of Science"
_DIETRICH = "Dietrich College of Humanities and Social Sciences"
_CFA = "College of Fine Arts"
_TEPPER = "Tepper School of Business"
_HEINZ = "Heinz College of Information Systems and Public Policy"

SCHOOLS: list[dict] = [
    {
        "name": _SCS,
        "sort_order": 1,
        "description": (
            "Carnegie Mellon's School of Computer Science is one of the world's "
            "foremost computing schools, spanning computer science, robotics, "
            "machine learning, language technologies, human-computer interaction, "
            "software and societal systems, and computational biology. Its "
            "departments and institutes grant a family of B.S. degrees, including "
            "the nation's first undergraduate degree in artificial intelligence."
        ),
    },
    {
        "name": _ENG,
        "sort_order": 2,
        "description": (
            "The College of Engineering — historically the Carnegie Institute of "
            "Technology — spans biomedical, chemical, civil and environmental, "
            "electrical and computer, materials science, and mechanical "
            "engineering, together with engineering and public policy, with an "
            "explicitly cross-disciplinary approach to research."
        ),
    },
    {
        "name": _MCS,
        "sort_order": 3,
        "description": (
            "The Mellon College of Science is CMU's basic-sciences college, "
            "spanning biological sciences, chemistry, mathematical sciences, and "
            "physics, together with the Neuroscience Institute."
        ),
    },
    {
        "name": _DIETRICH,
        "sort_order": 4,
        "description": (
            "The Dietrich College of Humanities and Social Sciences houses CMU's "
            "humanities and social-science departments — English; history; "
            "philosophy; psychology; social and decision sciences; statistics and "
            "data science; and languages, cultures and applied linguistics — with "
            "a distinctive analytical, decision-science orientation."
        ),
    },
    {
        "name": _CFA,
        "sort_order": 5,
        "description": (
            "Founded in 1905, the College of Fine Arts is one of the country's "
            "earliest comprehensive arts schools, comprising five degree-granting "
            "schools — Architecture, Art, Design, Drama, and Music — alongside the "
            "BXA intercollege programs that pair the arts with another discipline."
        ),
    },
    {
        "name": _TEPPER,
        "sort_order": 6,
        "description": (
            "The Tepper School of Business, which first appeared on the management "
            "education scene in 1949 as the Graduate School of Industrial "
            "Administration, is known for its analytical, management-science "
            "approach across undergraduate business, the MBA, PhD, and executive "
            "education."
        ),
    },
    {
        "name": _HEINZ,
        "sort_order": 7,
        "description": (
            "The Heinz College of Information Systems and Public Policy is CMU's "
            "graduate college 'at the critical nexus of technology and society,' "
            "spanning analytics, information systems, public policy, cybersecurity, "
            "and arts and entertainment management across its School of Information "
            "Systems and Management and School of Public Policy and Management."
        ),
    },
]

# Each college's official website (verified to resolve at author time).
_SCHOOL_WEBSITE: dict[str, str] = {
    _SCS: "https://www.cs.cmu.edu/",
    _ENG: "https://engineering.cmu.edu/",
    _MCS: "https://www.cmu.edu/mcs/",
    _DIETRICH: "https://www.cmu.edu/dietrich/",
    _CFA: "https://cfa.cmu.edu/",
    _TEPPER: "https://www.cmu.edu/tepper/",
    _HEINZ: "https://www.heinz.cmu.edu/",
}

# Rich, sourced About-tab content per college. Deans + titles are quoted from each
# college's official leadership page (verified 2026-06-10). Founding years are
# included only where an official page states one (SCS 1988; CFA 1905; Tepper
# 1949); the rest are honestly omitted. Notable-faculty rosters are not published
# uniformly per college and are omitted rather than hand-picked — except SCS, where
# CMU's official Turing-Award page names current faculty laureates. Named research
# centers are included only where verified on an official page.
_ABOUT_DETAIL: dict[str, dict] = {
    _SCS: {
        "founded": 1988,
        "leadership": (
            "Martial Hebert — Dean of the School of Computer Science (sixth dean; "
            "University Professor)"
        ),
        "faculty": [
            {
                "name": "Raj Reddy",
                "title": (
                    "Moza Bint Nasser University Professor of Computer Science and "
                    "Robotics; A.M. Turing Award (1994)"
                ),
            },
            {
                "name": "Manuel Blum",
                "title": "University Professor Emeritus; A.M. Turing Award (1995)",
            },
            {
                "name": "Edmund M. Clarke",
                "title": "FORE Systems University Professor Emeritus; A.M. Turing Award (2007)",
            },
        ],
        "research_centers": [
            "Robotics Institute",
            "Language Technologies Institute",
            "Human-Computer Interaction Institute",
            "Machine Learning Department",
        ],
        "source": {
            "label": "Carnegie Mellon — About the School of Computer Science (Dean)",
            "url": "https://www.cs.cmu.edu/about-scs/about-dean",
        },
    },
    _ENG: {
        "leadership": (
            "Burcu Akinci — Dr. William D. and Nancy W. Strecker Dean of the College "
            "of Engineering (16th dean, effective January 1, 2026)"
        ),
        "research_centers": [
            "Manufacturing Futures Institute",
            "Information Networking Institute",
            "Integrated Innovation Institute",
        ],
        "source": {
            "label": "Carnegie Mellon College of Engineering — Dean",
            "url": "https://engineering.cmu.edu/about-us/leadership/dean-bio.html",
        },
    },
    _MCS: {
        "leadership": (
            "Barbara Shinn-Cunningham — Glen de Vries Dean of the Mellon College of Science"
        ),
        "named_for": "The Mellon family (Andrew W. Mellon), via the Mellon Institute",
        "research_centers": [
            "Neuroscience Institute",
            "McWilliams Center for Cosmology and Astrophysics",
            "Center for Nucleic Acids Science and Technology (CNAST)",
            "Center for Nonlinear Analysis",
        ],
        "source": {
            "label": "Carnegie Mellon — Mellon College of Science (Dean)",
            "url": "https://www.cmu.edu/mcs/people/dean-bio.html",
        },
    },
    _DIETRICH: {
        "leadership": (
            "Richard Scheines — Bess Family Dean of the Dietrich College of Humanities and "
            "Social Sciences"
        ),
        "named_for": (
            "Marianna Brown Dietrich (a 2011 gift from her son, trustee William S. Dietrich II)"
        ),
        "research_centers": [
            "Block Center for Technology and Society",
            "Center for Behavioral and Decision Research",
            "The Humanities Center",
            "CMU Sports Analytics Center",
        ],
        "source": {
            "label": "Carnegie Mellon — Dietrich College (About)",
            "url": "https://www.cmu.edu/dietrich/about/",
        },
    },
    _CFA: {
        "founded": 1905,
        "leadership": (
            "Mary Ellen Poole — Stanley and Marcia Gumberg Dean of the College of "
            "Fine Arts; Professor of Music"
        ),
        "research_centers": [
            "Frank-Ratchye STUDIO for Creative Inquiry",
            "Center for the Arts in Society",
            "Entertainment Technology Center",
        ],
        "source": {
            "label": "Carnegie Mellon College of Fine Arts — About",
            "url": "https://cfa.cmu.edu/about",
        },
    },
    _TEPPER: {
        "founded": 1949,
        "leadership": (
            "Isabelle Bajeux-Besnainou — Richard P. Simmons Professor of Finance; "
            "tenth dean of the Tepper School of Business"
        ),
        "named_for": "David A. Tepper (renamed in 2004 following his naming gift)",
        "research_centers": [
            "Carnegie Mellon Electricity Industry Center (CEIC)",
            "Center for Behavioral and Decision Research",
            "PNC Center for Financial Services Innovation",
            "Center for Intelligent Business",
        ],
        "source": {
            "label": "Carnegie Mellon Tepper School — Our History",
            "url": "https://www.cmu.edu/tepper/about/our-history",
        },
    },
    _HEINZ: {
        "leadership": (
            "Kirsten Martin — H. John Heinz III Dean of the Heinz College of "
            "Information Systems and Public Policy"
        ),
        "named_for": "H. John Heinz III (former U.S. Senator from Pennsylvania)",
        "research_centers": [
            "Block Center for Technology and Society",
            "AI Measurement Science and Engineering Center (AIMSEC)",
            "Center for Collaboration Science (CoLab)",
            "Initiative for Digital Entertainment Analytics (IDEA)",
        ],
        "source": {
            "label": "Carnegie Mellon Heinz College — About",
            "url": "https://www.heinz.cmu.edu/about",
        },
    },
}

# About-detail fields omitted per college (verified-unavailable), recorded in each
# college node's _standard.omitted. Notable-faculty rosters are omitted for every
# college except SCS; founding years and named-for are omitted where no official
# page states them.
_ABOUT_OMITTED: dict[str, list[str]] = {
    _SCS: ["about_detail.named_for"],
    _ENG: ["about_detail.founded", "about_detail.faculty", "about_detail.named_for"],
    _MCS: ["about_detail.founded", "about_detail.faculty"],
    _DIETRICH: ["about_detail.founded", "about_detail.faculty"],
    _CFA: ["about_detail.faculty", "about_detail.named_for"],
    _TEPPER: ["about_detail.faculty"],
    _HEINZ: ["about_detail.founded", "about_detail.faculty"],
}

# ── Channel feeds + official social links ──────────────────────────────────
# Institution-wide news RSS + events iCal + official CMU socials. The daily ingest
# fills Updates + Events FROM these.
_INSTITUTION_CONTENT: dict = {
    "news_rss": "https://www.cmu.edu/news/feeds/news.rss",
    "events_feed": {"url": "https://events.cmu.edu/live/ical/events", "type": "ical"},
    "social": {
        "instagram": "https://www.instagram.com/carnegiemellon/",
        "linkedin": "https://www.linkedin.com/company/carnegie-mellon-university/",
        "x": "https://x.com/carnegiemellon",
        "youtube": "https://www.youtube.com/carnegiemellonu",
        "facebook": "https://www.facebook.com/carnegiemellonu",
    },
}

# CS keyword-relevant feed (the flagship program), inheriting the institution
# socials (the School of Computer Science surfaces its news through its own site).
_CS_CONTENT: dict = {
    "news_url": "https://www.scs.cmu.edu/news/",
    "keywords": [
        "computer science",
        "school of computer science",
        "scs",
        "artificial intelligence",
    ],
    "social": _INSTITUTION_CONTENT["social"],
}

# ── The undergraduate program catalog (real majors, organized by college) ───
# slug = idempotency key. Every program is mapped to its owning college from CMU's
# official majors listing and each college's catalog. CMU awards a mix of B.S.,
# B.A., B.Arch, BFA and BXA degrees that varies by major; the platform models them
# with the generic ``bachelors`` degree type rather than asserting a per-major
# designation (Architecture's five-year length is reflected in duration_months).
PROGRAMS: list[dict] = [
    # ── School of Computer Science ──
    {
        "slug": "cmu-computer-science-bs",
        "school": _SCS,
        "program_name": "Computer Science",
        "description": (
            "Carnegie Mellon's flagship Bachelor of Science in Computer Science — a "
            "rigorous CS core paired with an SCS concentration or an outside minor, "
            "in one of the world's leading computer science schools."
        ),
    },
    {
        "slug": "cmu-artificial-intelligence-bs",
        "school": _SCS,
        "program_name": "Artificial Intelligence",
        "description": (
            "The nation's first undergraduate degree in artificial intelligence "
            "(launched 2018) — a math, statistics, CS, and AI core with electives "
            "in machine learning, perception and language, robotics, and human-AI "
            "interaction, plus a required ethics component."
        ),
    },
    {
        "slug": "cmu-computational-biology-bs",
        "school": _SCS,
        "program_name": "Computational Biology",
        "description": (
            "Computational biology — computing, biology, and data at the molecular and systems "
            "scale."
        ),
    },
    # ── College of Engineering ──
    {
        "slug": "cmu-biomedical-engineering-bs",
        "school": _ENG,
        "program_name": "Biomedical Engineering",
        "description": (
            "Biomedical engineering — engineering at the interface of biology and medicine."
        ),
    },
    {
        "slug": "cmu-chemical-engineering-bs",
        "school": _ENG,
        "program_name": "Chemical Engineering",
        "description": (
            "Chemical engineering — reaction engineering, process design, and molecular "
            "systems."
        ),
    },
    {
        "slug": "cmu-civil-environmental-engineering-bs",
        "school": _ENG,
        "program_name": "Civil and Environmental Engineering",
        "description": (
            "Civil and environmental engineering — infrastructure, environment, and sustainable "
            "systems."
        ),
    },
    {
        "slug": "cmu-electrical-computer-engineering-bs",
        "school": _ENG,
        "program_name": "Electrical and Computer Engineering",
        "description": (
            "Electrical and computer engineering — circuits, systems, hardware, and computing."
        ),
    },
    {
        "slug": "cmu-engineering-public-policy-bs",
        "school": _ENG,
        "program_name": "Engineering and Public Policy",
        "description": (
            "Engineering and public policy — engineering joined with policy analysis (an "
            "additional major and degree)."
        ),
    },
    {
        "slug": "cmu-materials-science-engineering-bs",
        "school": _ENG,
        "program_name": "Materials Science and Engineering",
        "description": (
            "Materials science and engineering — structure, properties, and design of "
            "materials."
        ),
    },
    {
        "slug": "cmu-mechanical-engineering-bs",
        "school": _ENG,
        "program_name": "Mechanical Engineering",
        "description": "Mechanical engineering — mechanics, design, energy, and manufacturing.",
    },
    # ── Mellon College of Science ──
    {
        "slug": "cmu-biological-sciences-bs",
        "school": _MCS,
        "program_name": "Biological Sciences",
        "description": "Biological sciences — molecular, cellular, and computational biology.",
    },
    {
        "slug": "cmu-chemistry-bs",
        "school": _MCS,
        "program_name": "Chemistry",
        "description": "Chemistry — organic, inorganic, physical, and biological chemistry.",
    },
    {
        "slug": "cmu-mathematical-sciences-bs",
        "school": _MCS,
        "program_name": "Mathematical Sciences",
        "description": (
            "Mathematical sciences — pure and applied mathematics, with strong ties to CS and "
            "operations research."
        ),
    },
    {
        "slug": "cmu-physics-bs",
        "school": _MCS,
        "program_name": "Physics",
        "description": (
            "Physics — from astrophysics and cosmology to condensed matter and biophysics."
        ),
    },
    {
        "slug": "cmu-neuroscience-bs",
        "school": _MCS,
        "program_name": "Neuroscience",
        "description": (
            "Neuroscience — the biological and computational study of the brain, anchored by "
            "the Neuroscience Institute."
        ),
    },
    # ── Dietrich College of Humanities and Social Sciences ──
    {
        "slug": "cmu-economics-bs",
        "school": _DIETRICH,
        "program_name": "Economics",
        "description": "Economics — micro, macro, and quantitative economic analysis.",
    },
    {
        "slug": "cmu-english-bs",
        "school": _DIETRICH,
        "program_name": "English",
        "description": (
            "English — literary and cultural studies, professional and technical writing, and "
            "creative writing."
        ),
    },
    {
        "slug": "cmu-history-bs",
        "school": _DIETRICH,
        "program_name": "History",
        "description": (
            "History — political, social, and global history with a policy and applied bent."
        ),
    },
    {
        "slug": "cmu-philosophy-bs",
        "school": _DIETRICH,
        "program_name": "Philosophy",
        "description": "Philosophy — logic, ethics, philosophy of science, and formal methods.",
    },
    {
        "slug": "cmu-psychology-bs",
        "school": _DIETRICH,
        "program_name": "Psychology",
        "description": (
            "Psychology — cognitive, developmental, social, and health psychology with a "
            "research focus."
        ),
    },
    {
        "slug": "cmu-social-decision-sciences-bs",
        "school": _DIETRICH,
        "program_name": "Social and Decision Sciences",
        "description": (
            "Social and decision sciences — behavioral economics, decision making, and policy."
        ),
    },
    {
        "slug": "cmu-statistics-data-science-bs",
        "school": _DIETRICH,
        "program_name": "Statistics and Data Science",
        "description": (
            "Statistics and data science — statistical theory, methods, and data-driven "
            "applications."
        ),
    },
    {
        "slug": "cmu-statistics-machine-learning-bs",
        "school": _DIETRICH,
        "program_name": "Statistics and Machine Learning",
        "description": (
            "Statistics and machine learning — a joint major pairing statistical foundations "
            "with machine learning."
        ),
    },
    {
        "slug": "cmu-languages-cultures-linguistics-bs",
        "school": _DIETRICH,
        "program_name": "Languages, Cultures and Applied Linguistics",
        "description": (
            "Languages, cultures and applied linguistics — second-language study, linguistics, "
            "and cultural studies."
        ),
    },
    {
        "slug": "cmu-information-systems-bs",
        "school": _DIETRICH,
        "program_name": "Information Systems",
        "description": (
            "Information systems — the design and management of technology in organizations, "
            "bridging computing, business, and policy."
        ),
    },
    # ── College of Fine Arts ──
    {
        "slug": "cmu-architecture-barch",
        "school": _CFA,
        "program_name": "Architecture",
        "duration_months": 60,
        "description": "Architecture — a five-year, accredited Bachelor of Architecture (B.Arch).",
    },
    {
        "slug": "cmu-art-bfa",
        "school": _CFA,
        "program_name": "Art",
        "description": "Art — a Bachelor of Fine Arts spanning studio practice across media.",
    },
    {
        "slug": "cmu-design-bfa",
        "school": _CFA,
        "program_name": "Design",
        "description": (
            "Design — communications, products, and environments in CMU's design school."
        ),
    },
    {
        "slug": "cmu-drama-bfa",
        "school": _CFA,
        "program_name": "Drama",
        "description": (
            "Drama — a conservatory BFA in acting/music theater, design, production technology "
            "and management, directing, and dramaturgy."
        ),
    },
    {
        "slug": "cmu-music-bfa",
        "school": _CFA,
        "program_name": "Music",
        "description": (
            "Music — performance, composition, and music technology in the School of Music."
        ),
    },
    {
        "slug": "cmu-bha-humanities-arts",
        "school": _CFA,
        "program_name": "Bachelor of Humanities and Arts (BHA)",
        "description": (
            "A BXA intercollege degree pairing the College of Fine Arts with the humanities and "
            "social sciences."
        ),
    },
    {
        "slug": "cmu-bsa-science-arts",
        "school": _CFA,
        "program_name": "Bachelor of Science and Arts (BSA)",
        "description": (
            "A BXA intercollege degree pairing the College of Fine Arts with the sciences."
        ),
    },
    {
        "slug": "cmu-bcsa-computer-science-arts",
        "school": _CFA,
        "program_name": "Bachelor of Computer Science and Arts (BCSA)",
        "description": (
            "A BXA intercollege degree (est. 2008) pairing the College of Fine Arts with the "
            "School of Computer Science."
        ),
    },
    {
        "slug": "cmu-besa-engineering-arts",
        "school": _CFA,
        "program_name": "Bachelor of Engineering Studies and Arts (BESA)",
        "description": (
            "A BXA intercollege degree pairing the College of Fine Arts with the College of "
            "Engineering."
        ),
    },
    # ── Tepper School of Business ──
    {
        "slug": "cmu-business-administration-bs",
        "school": _TEPPER,
        "program_name": "Business Administration",
        "description": (
            "Business administration — the Tepper undergraduate business program, with an "
            "analytical, data-driven core."
        ),
    },
]

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

# Full official major names (program-page title); for CMU these equal the major name
# (the B.S./B.A./BFA/B.Arch/BXA designation varies per major and is not asserted).
_FULL_NAME_BY_SLUG: dict[str, str] = {p["slug"]: p["program_name"] for p in PROGRAMS}

# Official program/department home pages. The flagship CS major has its own verified
# department page; the others use their owning department/college official site.
_CS_URL = "https://csd.cs.cmu.edu/academics/bachelors/overview"
_WEBSITE_BY_SLUG: dict[str, str] = {
    "cmu-computer-science-bs": _CS_URL,
    "cmu-artificial-intelligence-bs": "https://www.cs.cmu.edu/bs-in-artificial-intelligence/",
    "cmu-computational-biology-bs": "https://www.cbd.cmu.edu/",
    "cmu-biomedical-engineering-bs": "https://engineering.cmu.edu/bme/",
    "cmu-chemical-engineering-bs": "https://engineering.cmu.edu/cheme/",
    "cmu-civil-environmental-engineering-bs": "https://engineering.cmu.edu/cee/",
    "cmu-electrical-computer-engineering-bs": "https://engineering.cmu.edu/ece/",
    "cmu-engineering-public-policy-bs": "https://engineering.cmu.edu/epp/",
    "cmu-materials-science-engineering-bs": "https://engineering.cmu.edu/mse/",
    "cmu-mechanical-engineering-bs": "https://engineering.cmu.edu/me/",
    "cmu-biological-sciences-bs": "https://www.cmu.edu/bio/",
    "cmu-chemistry-bs": "https://www.cmu.edu/chemistry/",
    "cmu-mathematical-sciences-bs": "https://www.cmu.edu/math/",
    "cmu-physics-bs": "https://www.cmu.edu/physics/",
    "cmu-neuroscience-bs": "https://www.cmu.edu/ni/",
    "cmu-economics-bs": "https://www.cmu.edu/dietrich/sds/",
    "cmu-english-bs": "https://www.cmu.edu/dietrich/english/",
    "cmu-history-bs": "https://www.cmu.edu/dietrich/history/",
    "cmu-philosophy-bs": "https://www.cmu.edu/dietrich/philosophy/",
    "cmu-psychology-bs": "https://www.cmu.edu/dietrich/psychology/",
    "cmu-social-decision-sciences-bs": "https://www.cmu.edu/dietrich/sds/",
    "cmu-statistics-data-science-bs": "https://www.cmu.edu/dietrich/statistics-datascience/",
    "cmu-statistics-machine-learning-bs": "https://www.cmu.edu/dietrich/statistics-datascience/",
    "cmu-languages-cultures-linguistics-bs": "https://www.cmu.edu/dietrich/modlang/",
    "cmu-information-systems-bs": "https://www.cmu.edu/dietrich/information-systems/",
    "cmu-architecture-barch": "https://soa.cmu.edu/",
    "cmu-art-bfa": "https://art.cmu.edu/",
    "cmu-design-bfa": "https://design.cmu.edu/",
    "cmu-drama-bfa": "https://drama.cmu.edu/",
    "cmu-music-bfa": "https://music.cmu.edu/",
    "cmu-bha-humanities-arts": "https://www.cmu.edu/interdisciplinary/programs/bha.html",
    "cmu-bsa-science-arts": "https://www.cmu.edu/interdisciplinary/programs/bsa.html",
    "cmu-bcsa-computer-science-arts": "https://www.cmu.edu/interdisciplinary/programs/bcsa.html",
    "cmu-besa-engineering-arts": "https://www.cmu.edu/interdisciplinary/programs/besa.html",
    "cmu-business-administration-bs": "https://www.cmu.edu/tepper/programs/undergraduate-business/",
}

# ── Who-it's-for + highlights (catalog baselines) ──────────────────────────
_WHO_BASELINE = (
    "Undergraduates seeking a rigorous, interdisciplinary education at one of the "
    "world's leading research universities, especially in technology, science, and "
    "the arts."
)
_HL_BASELINE = ["Private R1 research university", "6:1 student-faculty ratio", "Pittsburgh, PA"]
_WHO_BY_SLUG = {
    "cmu-computer-science-bs": (
        "Technically exceptional undergraduates who want a rigorous computer "
        "science education with deep access to one of the world's leading "
        "computing faculties and its research."
    ),
    "cmu-artificial-intelligence-bs": (
        "Students who want to specialize early in artificial intelligence in the "
        "nation's first undergraduate AI degree, with a strong math, statistics, "
        "and machine-learning foundation."
    ),
}
_HL_BY_SLUG = {
    "cmu-computer-science-bs": [
        "Flagship CS major",
        "Four SCS concentrations",
        "Turing-laureate faculty",
    ],
    "cmu-artificial-intelligence-bs": [
        "First undergraduate AI degree in the U.S. (2018)",
        "Machine-learning core",
        "Required AI ethics",
    ],
}

# ── Curriculum / concentrations, where published (the flagship) ────────────
# CMU's Computer Science Department publishes four official undergraduate
# concentrations; quoted verbatim from the CSD bachelor's concentrations page.
_TRACKS_BY_SLUG: dict[str, dict] = {
    "cmu-computer-science-bs": {
        "label": "CS undergraduate concentrations",
        "note": (
            "The B.S. in Computer Science combines a CS core with required depth "
            "via either an SCS concentration or an outside minor, plus breadth in "
            "mathematics, science and engineering, and the humanities and arts. "
            "First-year SCS students enter undeclared and choose a major in the "
            "second semester."
        ),
        "items": [
            {"name": "Algorithms and Complexity"},
            {"name": "Computer Graphics"},
            {"name": "Computer Systems"},
            {"name": "Principles of Programming Languages"},
        ],
        "source": "Carnegie Mellon CSD — Undergraduate Concentrations",
        "source_url": "https://csd.cmu.edu/academics/bachelors/bachelors_concentrations",
    },
    "cmu-artificial-intelligence-bs": {
        "label": "AI curriculum structure",
        "note": (
            "The B.S. in Artificial Intelligence is organized into a mathematics "
            "and statistics core, a computer science core, an artificial "
            "intelligence core (including two required machine-learning courses), "
            "AI cluster electives (decision making and robotics; machine learning; "
            "perception and language; human-AI interaction), a required ethics "
            "elective, and general education in the humanities, arts, science and "
            "engineering."
        ),
        "items": [
            {"name": "Mathematics and statistics core"},
            {"name": "Computer science core"},
            {"name": "Artificial intelligence core (incl. two machine-learning courses)"},
            {"name": "AI cluster electives"},
            {"name": "Ethics elective"},
        ],
        "source": "Carnegie Mellon SCS — B.S. in Artificial Intelligence curriculum",
        "source_url": "https://www.cs.cmu.edu/bs-in-artificial-intelligence/curriculum",
    },
}

# ── Program-specific cost (CMU undergraduate published rates, CDS 2024-25 §G1) ──
_TUITION = 67020
_FEES = 1756
_ROOM_BOARD = 18894
_UNDERGRAD_COA = 87670
_AVG_NET_PRICE = 35552
_COST_BY_SLUG: dict[str, dict] = {}

# ── Program-specific outcomes ──────────────────────────────────────────────
# CMU does not publish a per-program first-destination employment rate or industry
# breakdown that we could verify, and its institution-wide first-destination data
# lives only in an interactive dashboard. We therefore use the verified College
# Scorecard institution-wide median earnings (10 years after entry) as the outcomes
# figure for every program, scoped as institution, and omit the program-level
# employment rate and industry breakdown.
_OUTCOMES_INSTITUTION = {
    "median_salary": 114862,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry",
    "conditions": (
        "Carnegie Mellon institution-wide median earnings ten years after entry "
        "(U.S. Dept. of Education College Scorecard, UNITID 211440); a verified "
        "program-level earnings figure is not published for this major."
    ),
    "source": "U.S. Dept. of Education College Scorecard (UNITID 211440)",
    "source_url": "https://collegescorecard.ed.gov/school/?211440-Carnegie-Mellon-University",
}

# ── Faculty (lead + directory link), where confidently sourced (the flagship) ──
_FACULTY_BY_SLUG: dict[str, dict] = {
    "cmu-computer-science-bs": {
        "lead": [
            {
                "name": "Raj Reddy",
                "title": (
                    "Moza Bint Nasser University Professor of Computer Science and "
                    "Robotics; A.M. Turing Award (1994)"
                ),
            },
            {
                "name": "Manuel Blum",
                "title": "University Professor Emeritus; A.M. Turing Award (1995)",
            },
        ],
        "note": (
            "Carnegie Mellon's School of Computer Science counts 13 A.M. Turing "
            "Award winners among its faculty and alumni."
        ),
        "directory_url": "https://csd.cmu.edu/people/faculty",
    },
}

# ── Aggregated, cited student-review themes (≥2 third-party sources) ────────
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "cmu-computer-science-bs": {
        "summary": (
            "Students and third-party guides consistently describe Carnegie Mellon "
            "computer science as exceptionally rigorous and respected, with "
            "advanced, up-to-date coursework, a tight integration of mathematics "
            "and computing, supportive faculty, and outstanding placement into "
            "technology firms and graduate programs; the most common cautions are "
            "an intense workload, a high-stress culture, and large lower-division "
            "lectures."
        ),
        "themes": [
            {
                "label": "Academic rigor",
                "sentiment": "positive",
                "detail": (
                    "An advanced, problem-solving-focused CS curriculum that is highly regarded."
                ),
            },
            {
                "label": "Faculty & resources",
                "sentiment": "positive",
                "detail": (
                    "Knowledgeable faculty and strong research opportunities in a "
                    "premier CS school."
                ),
            },
            {
                "label": "Career placement",
                "sentiment": "positive",
                "detail": (
                    "Strong industry connections and a reputation as a launchpad into tech and "
                    "entrepreneurship."
                ),
            },
            {
                "label": "Intense workload",
                "sentiment": "caution",
                "detail": (
                    "A demanding, high-stress workload and difficult work-life "
                    "balance are recurring themes."
                ),
            },
            {
                "label": "Large lower-level classes",
                "sentiment": "caution",
                "detail": "Some introductory courses are large lectures.",
            },
        ],
        "sources": [
            {
                "label": "Niche — Carnegie Mellon University reviews",
                "url": "https://www.niche.com/colleges/carnegie-mellon-university/reviews/",
            },
            {
                "label": "The Princeton Review — Carnegie Mellon University",
                "url": "https://www.princetonreview.com/college/carnegie-mellon-university-1023851",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
}

# ── Application requirements (undergraduate baseline) ───────────────────────
# Carnegie Mellon undergraduate admission is via the Common Application; the policy
# below is quoted from CMU's official undergraduate admission requirements + plans
# pages. SCS applicants apply directly to the School of Computer Science.
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission.",
}
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application", "required": True},
        {
            "name": "CMU Common Application Writing Supplement (three short-answer questions)",
            "required": True,
        },
        {"name": "Official secondary-school transcript", "required": True},
        {
            "name": "Secondary School Counselor Evaluation + one Teacher Recommendation",
            "required": True,
        },
        {"name": "$75 application fee (fee waivers available)", "required": True},
        {
            "name": "SAT/ACT scores",
            "required": False,
            "note": (
                "CMU is test-optional — scores are considered if submitted but are not required."
            ),
        },
    ],
    "deadlines": [
        {"round": "Early Decision", "date": "November 3 (decision by December 15)"},
        {"round": "Regular Decision", "date": "January 5 (decision by April 1)"},
    ],
    "recommendations": {
        "count": 2,
        "detail": "One Secondary School Counselor Evaluation and one Teacher Recommendation.",
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "Duolingo English Test"],
            "required": False,
            "note": "English-proficiency proof may be required for non-native English speakers.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Carnegie Mellon — Undergraduate Admission Requirements",
                "url": "https://www.cmu.edu/admission/admission/undergraduate-admission-requirements",
            }
        ],
    },
    "application_fee": "$75 (fee waivers available)",
    "source": "Carnegie Mellon Office of Undergraduate Admission",
    "source_url": "https://www.cmu.edu/admission/admission/application-plans-deadlines",
}


# Real Carnegie Mellon campus photo (Hamerschlag Hall and Scott Hall) — Wikimedia
# Commons, hotlinkable landscape JPG. Leads the institution hero.
_CAMPUS_PHOTO = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/"
    "Carnegie_Mellon_Hamerschlag_Hall_and_Scott_Hall.jpg/"
    "1920px-Carnegie_Mellon_Hamerschlag_Hall_and_Scott_Hall.jpg"
)


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich Carnegie Mellon to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when CMU is absent — safe on fresh/CI databases.
    """
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    # Shallow-merge JSONB: every sub-object we provide is complete.
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    # Drop any stale value for a path we explicitly declare omitted, so the merge
    # can't keep serving a figure the enrichment run refused to assert.
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
    inst.founded_year = 1900
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.cmu.edu"
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
        # No college carries its own keyword-relevant feed (only the flagship
        # program does); always assign None so a stale value on a pre-existing row
        # is cleared and never kept in ContentIngestService's selection.
        sc.content_sources = None
        by_name[spec["name"]] = sc
    # Drop legacy colleges — programs.school_id is ON DELETE SET NULL, so this is
    # FK-safe (any orphaned programs are handled by the program reconcile).
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
    # CMU publishes no verified per-program employment report or industry breakdown,
    # so every program omits the program-level employment rate and top industries.
    omitted += [
        "outcomes_data.employment_rate",
        "outcomes_data.top_industries",
    ]
    if slug not in _TRACKS_BY_SLUG:
        omitted.append("tracks")
    # No official per-major entering-cohort size is published for any CMU major.
    omitted.append("class_profile.cohort_size")
    if slug not in _FACULTY_BY_SLUG:
        omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    if slug != "cmu-computer-science-bs":
        # Only the flagship carries its own keyword-relevant feed; catalog programs
        # surface the institution/college feed rather than a per-program one.
        omitted.append("content_sources")
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
                degree_type="bachelors",
                slug=slug,
            )
            session.add(p)
        p.program_name = _FULL_NAME_BY_SLUG.get(slug) or spec["program_name"]
        p.degree_type = "bachelors"
        p.duration_months = spec.get("duration_months", 48)
        p.description_text = spec["description"]
        # Website: verified department page where available, else the owning
        # college's official site (the authoritative home for the major).
        p.website_url = _WEBSITE_BY_SLUG.get(slug) or _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        # Every CMU undergraduate major is taught on campus.
        p.delivery_format = spec.get("delivery_format", "in_person")
        # Always assign so a stale value on a pre-existing row is cleared: only the
        # flagship carries its own feed (content_sources is omitted for the rest).
        p.content_sources = _CS_CONTENT if slug == "cmu-computer-science-bs" else None
        # Cost: published CMU undergraduate rates (Common Data Set 2024-25 §G1).
        cost_override = _COST_BY_SLUG.get(slug)
        if cost_override is not None:
            p.tuition = cost_override.get("tuition_usd")
            p.cost_data = dict(cost_override)
        else:
            p.tuition = _TUITION
            p.cost_data = {
                "tuition_usd": _TUITION,
                "total_cost_of_attendance": _UNDERGRAD_COA,
                "avg_net_price": _AVG_NET_PRICE,
                "breakdown": {
                    "tuition": _TUITION,
                    "fees": _FEES,
                    "room_board": _ROOM_BOARD,
                },
                "funded": False,
                "note": (
                    "First-year on-campus cost of attendance for 2025-26 (tuition + "
                    "required fees + room & board); the average net price is the "
                    "federal figure across aided students."
                ),
                "source": "Carnegie Mellon Common Data Set 2024-25 (§G1)",
                "source_url": "https://www.cmu.edu/ira/CDS/cds_2425.html",
                "year": "2025-26",
            }
        # Admissions: CMU undergraduate baseline.
        p.application_requirements = dict(_REQ_UNDERGRAD)
        # Outcomes: verified institution-wide Scorecard median earnings (scope=institution).
        outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(slug)
        p.outcomes_data = outcomes
        p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_BASELINE
        p.highlights = _HL_BY_SLUG.get(slug) or _HL_BASELINE
        # Always assign so a stale value on a pre-existing row is cleared (tracks is
        # recorded as omitted where unverified, and match_service reads program.tracks).
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = None
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        # Upcoming Regular Decision deadline (January 5).
        p.application_deadline = date(2027, 1, 5)
    session.flush()
    # Reconcile legacy CMU programs (slug not in the canonical set): delete when
    # unreferenced, otherwise unpublish so the catalog stays clean without breaking
    # any application/match rows that point at them.
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
