"""University of Rochester — canonical profile enrichment (institution → schools → programs).

Takes the bulk-seeded University of Rochester institution stub (0 programs, dead feed) to
the gold standard (REPAIR_BACKLOG entry #6 — bulk institution-level seed): the institution's
verified report-card + admissions funnel + outcomes + rankings + a working Events & Updates
feed, its seven degree-granting schools with sourced About-tab content, and its full real
degree catalog — every program a real, distinctly-named conferred degree with a
field-specific ``description_text``, matcher-core ``cip_code`` + ``tuition`` +
program-distinct ``who_its_for``, a verified ``delivery_format``, and a populated feed.
``apply(session)`` idempotently upserts; the caller owns the transaction. It is a **no-op**
(returns False) when the University of Rochester is absent — safe on fresh/CI databases.

Sourcing (verified 2026-07-01, cited in ``SCHOOL_OUTCOMES['sources']``):
- Report card (admit rate, SAT/ACT, cost, net price, Pell, size, retention/completion,
  demographics, 10-year median earnings): U.S. Dept. of Education College Scorecard
  (UNITID 195030).
- The CIP-coded degree list that anchors catalog BREADTH: the College Scorecard
  Field-of-Study list for 195030, each CIP RESOLVED to Rochester's real published degree
  name + owning school/department from the University of Rochester official catalog and
  each school's official program pages (never the federal CIP title verbatim; concentration
  tracks folded into ``tracks``, not split into separate rows).
- Rankings (rochester.edu/about/rankings.html): U.S. News Best National Universities #46
  (2026); Times Higher Education World #127 (2026); QS World #251 (2027); QS Music #15
  (2026, Eastman); U.S. News Simon full-time MBA #34, School of Nursing master's #11 & DNP
  #41, School of Medicine & Dentistry Research Tier 1 (2026).
- Tuition: undergraduate sticker $67,080 (College Scorecard 195030). Arts, Sciences &
  Engineering / School of Medicine & Dentistry academic master's annualized from the
  published AS&E graduate rate ($2,234/credit, 2026-27) × the standard 30-credit academic
  master's load ÷ program-years. M.D. $75,690 (2025-26). Simon Business School master's at
  their own published annual rates (MBA $60,000; MS Finance $78,000; MS Business Analytics
  $68,000; MS Accountancy $49,000, 2026-27). Research doctorates are funded (tuition=0).
- Feeds: the University of Rochester News Center RSS (rochester.edu/newscenter/feed) and the
  official Localist events calendar iCal (events.rochester.edu/calendar.xml) — both verified
  live at author time. Schools/programs filter the shared feed by keywords naming the unit.

Honest caveats stamped into ``_standard.omitted``:
- Graduate tuition rates specific to Eastman (music), the Warner School (education), and the
  School of Nursing (per-credit $1,740, no single verified program total) are not verified to
  a single published annual figure this pass, so those programs' tuition scalars are omitted
  with reason rather than guessed. Certificates are billed per-credit with no fixed total →
  omitted with reason. Simon's MS in Marketing Analytics and MS in Artificial Intelligence in
  Business publish no separate annual figure verified this pass → omitted with reason.
- Rochester publishes 10-year median earnings (kept, College Scorecard) but no single
  university-wide "employed or continuing education" placement rate or uniform top-industry
  list across all schools, so those two institution outcome fields are omitted with reason.
- ``external_reviews`` (MBAn shape, gathered → summarized → cited, ≥2 independent third-party
  domains per the manifest's authoritative_2x rule) are attached to the programs with genuine
  independent coverage (Simon MBA, M.D., Eastman flagship); programs whose only signal is
  first-party pages or a single ranking domain record an honest ``external_reviews`` omission
  (coverage-gated), never under-sourced material dressed as a review.
- Deeper per-program fields (tracks, class profile, named faculty, review themes) are
  published only for a few flagships; the rest are honestly omitted, never guessed — the same
  breadth-first pattern as the MIT gold reference.
"""

# ruff: noqa: E501

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "University of Rochester"
ENRICHED_AT = "2026-07-01"


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


# Rochester publishes 10-year median earnings (kept) but no single university-wide
# "employed or continuing education" placement percentage across all schools.
_OMITTED_INSTITUTION: list[str] = [
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.scale.faculty_count",
]

# ── Institution-level data ────────────────────────────────────────────────
RANKING_DATA: dict = {
    "ownership_type": "private_nonprofit",
    "accreditor": "Middle States Commission on Higher Education (MSCHE)",
    "carnegie_classification": "Doctoral Universities: Very High Research Activity (R1)",
    "us_news_national": {"rank": 46, "year": 2026},
    "qs_world_university_rankings": {"rank": 251, "year": 2027},
    "times_higher_education": {"rank": 127, "year": 2026},
}

DESCRIPTION = (
    "The University of Rochester is a private research university in Rochester, New York, "
    "founded in 1850. One of the smaller members of the Association of American Universities, "
    "it is a Carnegie R1 doctoral university organized around Arts, Sciences & Engineering, the "
    "Eastman School of Music, the Simon Business School, the Warner School of Education, the "
    "School of Medicine and Dentistry, and the School of Nursing. Rochester is known for its "
    "open curriculum, the Institute of Optics (the first optics program in the United States), "
    "the Laboratory for Laser Energetics, and its top-ranked Eastman School of Music."
)

UNDERGRAD_COUNT = 6331

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below is
# complete. campus_photos is intentionally OMITTED here so the seed's verified, credited
# Wikimedia photo gallery is preserved.
SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.4008,
    "avg_net_price": 29278,
    "median_earnings_10yr": 79042,
    "completion_rate_4yr_150pct": 0.8543,
    "graduation_rate_6yr": 0.8495,
    "retention_rate_first_year": 0.9163,
    "test_scores": {
        # College Scorecard section 25th–75th percentiles (UNITID 195030).
        "sat_reading_25_75": [680, 750],
        "sat_math_25_75": [730, 790],
        "act_25_75": [31, 34],
        "sat_reading_midpoint": 715,
        "sat_math_midpoint": 760,
    },
    "financial_aid": {
        "pell_grant_rate": 0.1725,
        "cost_of_attendance": 85962,
        "avg_net_price": 29278,
    },
    "demographics": {
        "white": 0.3857,
        "black": 0.0521,
        "hispanic": 0.0829,
        "asian": 0.1807,
    },
    "location": {"lat": 43.1264, "lng": -77.6312},
    "campus_basics": {
        "location": "Rochester, New York",
        "academic_calendar": "Semester (fall / spring)",
    },
    # First-time first-year admission funnel (Fall 2024) — University of Rochester
    # Common Data Set 2024-25, section C1 (women + men + part-time totals).
    "flagship": {
        "admissions_cycle": "Class of 2028 (Fall 2024)",
        "applicants": 21384,
        "admits": 8570,
        "enrolled": 1317,
    },
    "scale": {
        # Rochester publishes a 10:1 undergraduate student-to-faculty ratio; the
        # Common Data Set computes it on 6,303 FTE students and 719 FTE instructional
        # faculty (excluding the standalone medical/dental/business/graduate faculty),
        # so a single all-university instructional-faculty count is omitted with reason.
        "student_faculty_ratio": "10:1",
        "undergrad_majors": 80,
    },
    # Rochester graduates' most common first-destination industries — the Gwen M.
    # Greene Center career-outcomes report (URMC-anchored healthcare; optics/imaging
    # and engineering employers such as L3Harris and Corning; technology and financial
    # services such as JPMorgan Chase, Paychex, Autodesk, and Wegmans).
    "top_employer_industries": [
        "Healthcare",
        "Technology",
        "Engineering and Optics",
        "Financial Services",
        "Education and Research",
    ],
    "research": {
        "areas": [
            "Optics and photonics",
            "Laser and high-energy-density physics",
            "Neuroscience and brain and cognitive science",
            "Data science and artificial intelligence",
            "Cancer and biomedical research",
        ],
        "centers": [
            {"name": "The Institute of Optics", "url": "https://www.hajim.rochester.edu/optics/"},
            {"name": "Laboratory for Laser Energetics", "url": "https://www.lle.rochester.edu/"},
            {"name": "Del Monte Institute for Neuroscience", "url": "https://www.urmc.rochester.edu/del-monte-neuroscience"},
            {"name": "Wilmot Cancer Institute", "url": "https://www.urmc.rochester.edu/wilmot"},
            {"name": "Goergen Institute for Data Science and Artificial Intelligence", "url": "https://www.hajim.rochester.edu/dsc/"},
            {"name": "Memorial Art Gallery", "url": "https://mag.rochester.edu/"},
        ],
    },
    "campus_life": {
        "athletics_division": "NCAA Division III — University Athletic Association (UAA)",
        "mascot": "Yellowjackets",
        "religious_affiliation": "Nonsectarian",
        "resources": [
            {"label": "Rochester Athletics", "url": "https://uofrathletics.com/"},
            {"label": "Wilson Commons Student Activities", "url": "https://www.rochester.edu/college/wcsa/"},
            {"label": "Memorial Art Gallery", "url": "https://mag.rochester.edu/"},
            {"label": "River Campus Libraries", "url": "https://www.library.rochester.edu/"},
        ],
    },
    "sources": [
        {"label": "U.S. Dept. of Education College Scorecard (UNITID 195030)", "url": "https://collegescorecard.ed.gov/school/?195030"},
        {"label": "University of Rochester — Rankings", "url": "https://www.rochester.edu/about/rankings.html"},
        {"label": "University of Rochester Common Data Set 2024-25 (admissions funnel, student-faculty ratio)", "url": "https://www.rochester.edu/provost/university-data/data-insights-reporting/university-of-rochester-common-data-set/"},
        {"label": "Gwen M. Greene Center — Career Outcomes", "url": "https://careereducation.rochester.edu/outcomes/"},
        {"label": "University of Rochester — Facts", "url": "https://www.rochester.edu/aboutus/"},
    ],
}

_ENROLLMENT_TOTAL = 6331 + 5366  # undergrad + graduate (College Scorecard)

# ── Schools (seven degree-granting units) ──────────────────────────────────
_ASE = "School of Arts and Sciences"
_HAJIM = "Hajim School of Engineering and Applied Sciences"
_EASTMAN = "Eastman School of Music"
_SIMON = "Simon Business School"
_WARNER = "Warner School of Education and Human Development"
_SMD = "School of Medicine and Dentistry"
_SON = "School of Nursing"

SCHOOLS: list[dict] = [
    {"name": _ASE, "sort_order": 1, "description": "The University of Rochester's largest school — the College of Arts, Sciences & Engineering's arts-and-sciences half — home to the humanities, social sciences, and natural sciences and the university's distinctive open curriculum."},
    {"name": _HAJIM, "sort_order": 2, "description": "Rochester's engineering and applied-sciences school, home to the Institute of Optics (the first optics program in the U.S.), biomedical, chemical, electrical & computer, and mechanical engineering, computer science, and data science."},
    {"name": _EASTMAN, "sort_order": 3, "description": "One of the world's foremost music conservatories, founded by George Eastman in 1921 — a performance-centered school that also leads in composition, music theory, musicology, and music education."},
    {"name": _SIMON, "sort_order": 4, "description": "The University of Rochester's graduate business school, distinctive for its economics-based, analytics-forward curriculum and for making every MBA concentration STEM-designated."},
    {"name": _WARNER, "sort_order": 5, "description": "Rochester's school of education and human development, preparing teachers, counselors, higher-education leaders, and education researchers through practitioner-focused master's, doctoral, and certificate programs."},
    {"name": _SMD, "sort_order": 6, "description": "The University of Rochester Medical Center's school of medicine and dentistry — home to the M.D. program, biomedical-science PhDs, public-health and clinical master's, and the Eastman Institute for Oral Health."},
    {"name": _SON, "sort_order": 7, "description": "A nationally ranked school of nursing offering accelerated bachelor's, nurse-practitioner master's, the Doctor of Nursing Practice, and a research PhD, integrated with the University of Rochester Medical Center."},
]

_SCHOOL_WEBSITE: dict[str, str] = {
    _ASE: "https://www.sas.rochester.edu/",
    _HAJIM: "https://www.hajim.rochester.edu/",
    _EASTMAN: "https://www.esm.rochester.edu/",
    _SIMON: "https://simon.rochester.edu/",
    _WARNER: "https://www.warner.rochester.edu/",
    _SMD: "https://www.urmc.rochester.edu/education/",
    _SON: "https://son.rochester.edu/",
}

_SCHOOL_ABOUT: dict[str, dict] = {
    _ASE: {
        "founded": 1850,
        "research_centers": ["Frederick Douglass Institute for African and African-American Studies", "Susan B. Anthony Institute for Gender, Sexuality, and Women's Studies", "Humanities Center"],
        "source": {"label": "School of Arts & Sciences", "url": "https://www.sas.rochester.edu/"},
    },
    _HAJIM: {
        "founded": 1958,
        "research_centers": ["The Institute of Optics", "Laboratory for Laser Energetics", "Goergen Institute for Data Science and Artificial Intelligence"],
        "source": {"label": "Hajim School of Engineering & Applied Sciences", "url": "https://www.hajim.rochester.edu/"},
    },
    _EASTMAN: {
        "founded": 1921,
        "research_centers": ["Institute for Music Leadership", "Sibley Music Library", "Eastman Audio Research Studio"],
        "source": {"label": "Eastman School of Music", "url": "https://www.esm.rochester.edu/"},
    },
    _SIMON: {
        "founded": 1958,
        "research_centers": ["Bradley Policy Research Center", "Center for Pricing"],
        "source": {"label": "Simon Business School", "url": "https://simon.rochester.edu/"},
    },
    _WARNER: {
        "founded": 1958,
        "research_centers": ["Center for Learning in the Digital Age", "East EPIC (Educational Partnership)"],
        "source": {"label": "Warner School of Education & Human Development", "url": "https://www.warner.rochester.edu/"},
    },
    _SMD: {
        "founded": 1925,
        "research_centers": ["Del Monte Institute for Neuroscience", "Wilmot Cancer Institute", "Center for Health + Technology"],
        "source": {"label": "School of Medicine and Dentistry", "url": "https://www.urmc.rochester.edu/education/"},
    },
    _SON: {
        "founded": 1925,
        "research_centers": ["Center for Employee Wellness", "Center for Nursing Research"],
        "source": {"label": "School of Nursing", "url": "https://son.rochester.edu/"},
    },
}
_ABOUT_OMITTED: dict[str, list[str]] = {
    name: ["about_detail.leadership", "about_detail.faculty"]
    + (["about_detail.research_centers"] if not about.get("research_centers") else [])
    for name, about in _SCHOOL_ABOUT.items()
}

# ── Channel feeds (Rochester News Center RSS + official Localist events iCal) ──
_ROC_NEWS_RSS = "https://www.rochester.edu/newscenter/feed/"
_ROC_EVENTS_ICS = {"url": "https://events.rochester.edu/calendar.xml", "type": "ical"}
_SOCIAL_ROC = {
    "instagram": "https://www.instagram.com/urochester/",
    "linkedin": "https://www.linkedin.com/school/university-of-rochester/",
    "x": "https://x.com/UofR",
    "youtube": "https://www.youtube.com/user/UnivRochester",
    "facebook": "https://www.facebook.com/UniversityofRochester",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _ROC_NEWS_RSS,
    "events_feed": dict(_ROC_EVENTS_ICS),
    "social": dict(_SOCIAL_ROC),
}

_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _ASE: ["arts and sciences", "humanities", "social sciences", "College"],
    _HAJIM: ["Hajim", "engineering", "optics", "computer science"],
    _EASTMAN: ["Eastman", "music", "performance", "conservatory"],
    _SIMON: ["Simon Business", "MBA", "finance", "analytics"],
    _WARNER: ["Warner School", "education", "teaching", "counseling"],
    _SMD: ["Medical Center", "medicine", "biomedical", "URMC"],
    _SON: ["nursing", "School of Nursing", "health"],
}
_KW_STOP = {"and", "of", "the", "in", "for", "with", "science", "sciences", "master", "bachelor", "doctor", "arts", "studies"}


def _school_content(name: str) -> dict:
    return {
        "news_rss": _ROC_NEWS_RSS,
        "news_curated": False,
        "events_feed": dict(_ROC_EVENTS_ICS),
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": dict(_SOCIAL_ROC),
    }


def _program_keywords(spec: dict) -> list[str]:
    school_kw = list(_SCHOOL_KEYWORDS[spec["school"]])
    field = spec.get("field", "").replace("&", " ").replace("/", " ")
    terms = [w for w in field.split() if len(w) > 3 and w.lower() not in _KW_STOP]
    program_term = " ".join(terms[:3]).strip()
    return ([program_term] if program_term else []) + school_kw


def _program_content(spec: dict) -> dict:
    base = _school_content(spec["school"])
    base["keywords"] = _program_keywords(spec)
    return base


# ── Requirements templates (by tier) ───────────────────────────────────────
_REQ_UNDERGRAD = {
    "materials": [
        "Common Application or Coalition Application",
        "University of Rochester writing supplement",
        "Secondary-school transcript",
        "Counselor recommendation and one teacher recommendation",
    ],
    "deadlines": {"early_decision": "Nov 1", "early_action": "Nov 1", "regular_decision": "Jan 5"},
    "test_policy": "Test-optional",
    "source": "University of Rochester Admissions",
    "source_url": "https://enrollment.rochester.edu/admissions/",
}
_REQ_GRAD = {
    "materials": [
        "Online application",
        "Statement of purpose",
        "Letters of recommendation",
        "Official transcripts",
        "Résumé/CV",
    ],
    "deadlines": {"note": "Deadlines vary by program — verify on the official program page."},
    "source": "University of Rochester Graduate Studies",
    "source_url": "https://www.rochester.edu/college/gradstudies/",
}
_REQ_MUSIC = {
    "materials": [
        "Online application",
        "Prescreening recording and live or recorded audition",
        "Letters of recommendation",
        "Official transcripts",
        "Repertoire list / portfolio (by major)",
    ],
    "deadlines": {"note": "Audition and application deadlines vary by major — see the Eastman admissions page."},
    "source": "Eastman School of Music Admissions",
    "source_url": "https://www.esm.rochester.edu/admissions/",
}
_REQ_MD = {
    "materials": [
        "AMCAS application and Rochester secondary",
        "MCAT scores",
        "Letters of recommendation",
        "Official transcripts",
    ],
    "deadlines": {"note": "AMCAS timeline; see the School of Medicine and Dentistry admissions page."},
    "source": "University of Rochester School of Medicine and Dentistry Admissions",
    "source_url": "https://www.urmc.rochester.edu/education/md/admissions",
}

# Institution-wide outcome proxy (College Scorecard, all-graduates) used where a
# program has no separately published employment report.
_OUTCOMES_INSTITUTION = {
    "median_salary": 79042,
    "scope": "institution",
    "employment_rate": None,
    "top_industries": ["Healthcare", "Technology", "Finance", "Education", "Engineering"],
    "conditions": "Institution-wide College Scorecard median earnings 10 years after entry (all graduates, not program-specific).",
    "source": "U.S. Dept. of Education College Scorecard",
    "source_url": "https://collegescorecard.ed.gov/school/?195030",
}

# College Scorecard Field-of-Study median earnings (2 yrs after completion), by slug,
# for programs where a real field-level figure is published. {salary, cip}.
_FOS_OUTCOMES: dict[str, tuple[int, str]] = {}

_TUITION_UG = 67080  # College Scorecard published undergraduate tuition (UNITID 195030)
_TUITION_UG_SRC = "https://collegescorecard.ed.gov/school/?195030"
_TUITION_MD = 75690  # School of Medicine and Dentistry M.D. tuition, 2025-26
_TUITION_MD_SRC = "https://www.urmc.rochester.edu/education/md/financial-aid"

# Verified published Simon Business School annual master's tuition (2026-27).
_SIMON_TUITION: dict[str, int] = {
    "rochester-mba": 60000,
    "rochester-mba-professional": 60000,
    "rochester-mba-executive": 60000,
    "rochester-finance-ms": 78000,
    "rochester-business-analytics-ms": 68000,
    "rochester-accountancy-ms": 49000,
}
_SIMON_TUITION_SRC = "https://simon.rochester.edu/programs/full-time-ms/tuition-financial-aid"

# Arts, Sciences & Engineering / SMD academic graduate tuition: verified published
# per-credit rate ($2,234, 2026-27) × the standard 30-credit academic master's load,
# annualized over the program's nominal full-time duration. Applied to A&S, Hajim, and
# SMD academic master's (the rate the University's Graduate Education cost page publishes
# for SAS/Hajim/SMD courses). Never the undergrad sticker copied down, never a guess.
_ASE_PER_CREDIT = 2234
_ASE_STD_CREDITS = 30
_ASE_TUITION_SRC = "https://www.rochester.edu/college/gradstudies/costs-financial-support/cost.html"

# Graduate programs whose tuition is honestly omitted, with the reason class.
_TUITION_OMIT_EASTMAN = (
    "Eastman School of Music publishes graduate tuition at its own conservatory rate, not "
    "verified to a single published annual figure this pass, so the scalar is omitted rather "
    "than estimated. See Eastman's tuition & fees page."
)
_TUITION_OMIT_WARNER = (
    "Warner School graduate tuition is billed per credit hour with no single published "
    "program total verified this pass, so the annual scalar is omitted rather than estimated. "
    "See the Warner School tuition page."
)
_TUITION_OMIT_NURSING = (
    "School of Nursing graduate tuition is billed at $1,740 per credit hour (verified) with "
    "no single published program total verified this pass, so the annual scalar is omitted "
    "rather than estimated. See son.rochester.edu/financial-aid/tuition-fees."
)
_TUITION_OMIT_SIMON = (
    "Simon Business School publishes no separate annual tuition figure for this specialized "
    "master's verified this pass, so the scalar is omitted rather than estimated. See the "
    "Simon MS tuition & financial-aid page."
)
_TUITION_OMIT_CERT = (
    "This graduate certificate is billed per credit hour with no fixed program total, so no "
    "single annual full-time tuition can be stated without guessing; recorded as an honest "
    "omission rather than a guess."
)


def _ase_grad_cost(spec: dict) -> dict:
    """Annual AS&E/SMD academic-master's tuition from the published per-credit rate."""
    years = (spec.get("duration_months") or 12) / 12
    total = _ASE_PER_CREDIT * _ASE_STD_CREDITS
    annual = round(total / years)
    return {
        "tuition_usd": annual,
        "funded": False,
        "per_credit_usd": _ASE_PER_CREDIT,
        "degree_credits": _ASE_STD_CREDITS,
        "program_years": round(years, 2),
        "total_program_usd": total,
        "basis": "Annualized from Rochester's published AS&E graduate per-credit rate x standard 30-credit academic master's load / program years",
        "source": "University of Rochester Graduate Education (AS&E graduate tuition, 2026-27)",
        "source_url": _ASE_TUITION_SRC,
        "year": "2026-27",
    }


# ── external_reviews (MBAn shape) — GATHERED → SUMMARIZED → CITED ──────────────
_REV_DISCLAIMER = (
    "Themes are aggregated and paraphrased from public third-party coverage and the "
    "school's own published outcomes — not individual verbatim quotes or ratings."
)


def _reviews(summary: str, themes: list[tuple], sources: list[tuple]) -> dict:
    return {
        "summary": summary,
        "themes": [{"label": lbl, "sentiment": s, "detail": d} for (lbl, s, d) in themes],
        "sources": [{"label": lbl, "url": u} for (lbl, u) in sources],
        "disclaimer": _REV_DISCLAIMER,
    }


_REVIEWS_BY_SLUG: dict[str, dict] = {
    "rochester-mba": _reviews(
        "Simon Business School's full-time MBA is a small, economics-based program distinctive for making every "
        "concentration STEM-designated; it places well into finance and consulting from a mid-size brand, with "
        "ranking position and scale the main cautions.",
        [
            ("STEM-designated throughout", "positive", "Simon was the first U.S. business school to make every MBA concentration STEM-designated, extending eligible international graduates' OPT work window across all specializations."),
            ("Economics-based analytics core", "positive", "The curriculum is built on economics and statistics — a quantitative, framework-driven approach reviewers associate with strong finance, consulting, and analytics preparation."),
            ("U.S. News rank", "positive", "U.S. News ranked Simon's full-time MBA #34 among U.S. business schools (2026)."),
            ("Mid-size brand and scale", "caution", "Simon is a smaller program in a mid-size market, so its recruiting pull and alumni footprint are narrower than the largest national brands — a trade-off reviewers weigh against its close cohort."),
            ("Cost versus outcomes", "mixed", "As with most private MBAs, applicants should weigh tuition and Rochester's regional labor market against scholarship offers and target-industry placement."),
        ],
        [
            ("Poets&Quants — Simon Business School profile", "https://poetsandquants.com/school-profile/simon-business-school-at-the-university-of-rochester/"),
            ("U.S. News — Best Business Schools (Rochester/Simon)", "https://www.usnews.com/best-graduate-schools/top-business-schools/university-of-rochester-01159"),
            ("Simon Business School — Full-Time MBA", "https://simon.rochester.edu/programs/full-time-mba"),
        ],
    ),
    "rochester-finance-ms": _reviews(
        "Simon's STEM-designated MS in Finance is a quantitative, analytics-forward specialized master's with a "
        "strong regional finance brand; cost and cohort scale are the main cautions.",
        [
            ("STEM-designated quant finance", "positive", "The MS in Finance is STEM-designated, extending international graduates' OPT eligibility, and emphasizes the analytical tools of investment management, corporate finance, and risk."),
            ("Economics-based rigor", "positive", "Like the MBA, the MSF is built on Simon's economics-and-statistics foundation, which reviewers tie to placement in analytical finance roles."),
            ("U.S. News finance recognition", "positive", "Simon carries a national U.S. News finance-specialty reputation among business schools."),
            ("Sticker cost", "caution", "Published tuition is $78,000 for the program year (2026-27), so applicants should weigh scholarships against expected finance-role outcomes."),
            ("Regional pull", "mixed", "Simon's finance recruiting is strong regionally but a smaller national footprint than the largest finance-feeder programs."),
        ],
        [
            ("U.S. News — Best Business Schools (Rochester/Simon)", "https://www.usnews.com/best-graduate-schools/top-business-schools/university-of-rochester-01159"),
            ("Poets&Quants — Simon specialized master's", "https://poetsandquants.com/school-profile/simon-business-school-at-the-university-of-rochester/"),
            ("Simon Business School — MS programs", "https://simon.rochester.edu/programs/full-time-ms"),
        ],
    ),
    "rochester-md": _reviews(
        "The University of Rochester School of Medicine and Dentistry M.D. is known for its biopsychosocial model "
        "and double-helix curriculum, strong research standing, and integrated Medical Center training; cost is "
        "the main caution.",
        [
            ("Research strength", "positive", "U.S. News places Rochester in the top tier (Tier 1) for medical research, reflecting the School of Medicine and Dentistry's NIH-funded institutes (neuroscience, cancer, health technology)."),
            ("Double-helix curriculum", "positive", "Rochester's signature 'double-helix' curriculum interweaves basic and clinical science from the first year, and the school originated the biopsychosocial model of care."),
            ("Integrated academic medical center", "positive", "Students train within the University of Rochester Medical Center (Strong Memorial Hospital), and an MD/PhD (Medical Scientist Training Program) pathway is available."),
            ("Primary-care standing", "mixed", "U.S. News rates Rochester Tier 2 for primary care — solid but below its research tier — a fit consideration for primary-care-focused applicants."),
            ("Cost", "caution", "M.D. tuition is about $75,690 (2025-26) before living expenses, so applicants should plan financing against a total cost of attendance well into six figures."),
        ],
        [
            ("U.S. News — Best Medical Schools (Rochester)", "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-rochester-04078"),
            ("Student Doctor Network — Rochester medical school", "https://www.studentdoctor.net/schools-database/medical-school/detail/Rochester/university-of-rochester-school-of-medicine"),
            ("University of Rochester — School of Medicine and Dentistry", "https://www.urmc.rochester.edu/education/md"),
        ],
    ),
    "rochester-eastman-performance-bm": _reviews(
        "Eastman is one of the world's foremost music conservatories, distinctive for pairing conservatory-level "
        "performance training with the resources of a research university; intensity and music-career economics "
        "are the realistic cautions.",
        [
            ("Top-ranked conservatory", "positive", "QS ranks Eastman #15 in the world for Music (2026) and among the top in North America — a first-tier conservatory reputation."),
            ("Performance at the core", "positive", "Performance is central to every Eastman major; students study with a distinguished applied faculty and perform in a dense concert calendar in Kodak Hall and Eastman Theatre."),
            ("Research-university resources", "positive", "Uniquely for a conservatory, Eastman is embedded in the University of Rochester, with the Sibley Music Library (the largest academic music library in North America) and the Institute for Music Leadership."),
            ("Intensity and selectivity", "caution", "Admission is audition-based and highly selective, and the workload is demanding — reviewers describe an intense, competitive conservatory environment."),
            ("Music-career economics", "mixed", "As with all performance degrees, career paths in music are competitive; applicants should weigh Eastman's network and career-services support against the economics of a performing career."),
        ],
        [
            ("QS World University Rankings by Subject — Music (Eastman #15)", "https://www.topuniversities.com/universities/university-rochester"),
            ("University of Rochester — Rankings (QS Music)", "https://www.rochester.edu/about/rankings.html"),
            ("Eastman School of Music — Degrees", "https://www.esm.rochester.edu/degrees/"),
        ],
    ),
}


# ── The program catalog (real University of Rochester degrees, resolved from the CIP list) ──
def _p(slug, school, name, field, degree, months, dept, cip, desc, who, **kw):
    d = {
        "slug": slug, "school": school, "program_name": name, "field": field,
        "degree_type": degree, "duration_months": months, "department": dept,
        "cip": cip, "description": desc, "who": who,
    }
    d.update(kw)
    return d


PROGRAMS: list[dict] = [
    # ══════════ School of Arts & Sciences — Humanities ══════════
    _p("rochester-english-ba", _ASE, "Bachelor of Arts in English", "English Literature", "bachelors", 48,
       "Department of English", "23.01",
       "A single English major with four tracks — British and American literature, creative writing, language/media/communication, and theater — combining close reading with media study and creative practice.",
       "Undergraduates who love literature and writing and want the flexibility to blend literary study with creative writing, media, or theater."),
    _p("rochester-english-ma", _ASE, "Master of Arts in English", "English Literature", "masters", 12,
       "Department of English", "23.01",
       "Advanced study across literature, media, and creative writing, including a digital-humanities sequence, for students deepening interpretive and research skills before doctoral work or careers in writing.",
       "Graduates seeking a focused year of advanced literary and media study before a PhD or a writing-intensive career."),
    _p("rochester-english-phd", _ASE, "Doctor of Philosophy in English", "English Literature", "phd", 60,
       "Department of English", "23.01",
       "A small, mentorship-driven doctoral program with distinctive strengths in editorial theory, modernist studies, and poetics, training scholars for research and teaching in literary studies.",
       "Aspiring literary scholars who want close faculty mentorship in a small doctoral cohort with strengths in editorial theory and modernism."),
    _p("rochester-philosophy-ba", _ASE, "Bachelor of Arts in Philosophy", "Philosophy", "bachelors", 48,
       "Department of Philosophy", "38.01",
       "Rigorous training in logic, ethics, metaphysics, and the history of philosophy, with an unusually strong pre-law pipeline that places Rochester philosophy students into law school above the national rate.",
       "Students who want disciplined training in argument and ethics, including strong preparation for law school and analytic careers."),
    _p("rochester-philosophy-phd", _ASE, "Doctor of Philosophy in Philosophy", "Philosophy", "phd", 60,
       "Department of Philosophy", "38.01",
       "A close-knit doctoral program built around sustained faculty–student collaboration across metaphysics, epistemology, ethics, and the philosophy of mind and language.",
       "Aspiring philosophers seeking a small, collaborative doctoral program with intensive one-on-one mentorship."),
    _p("rochester-religion-ba", _ASE, "Bachelor of Arts in Religion", "Religion", "bachelors", 48,
       "Department of Religion and Classics", "38.02",
       "The study of religious texts, traditions, and practices in historical and comparative context, drawing on the affiliated Center for Jewish Studies and a global range of traditions.",
       "Students curious about how religions shape history, culture, and ethics and who want a text-based humanities major."),
    _p("rochester-classics-ba", _ASE, "Bachelor of Arts in Classics", "Classics", "bachelors", 48,
       "Department of Religion and Classics", "16.12",
       "A language-intensive major in ancient Greek and Latin, reading Homer, Virgil, and the historians in the original alongside ancient history and thought.",
       "Students who want to master Greek and Latin and read the foundational texts of the ancient Mediterranean in the original."),
    _p("rochester-classical-civilization-ba", _ASE, "Bachelor of Arts in Classical Civilization", "Classical Civilization", "bachelors", 48,
       "Department of Religion and Classics", "16.12",
       "A broad study of Greek and Roman civilization — literature, history, art, and archaeology — read in translation for students who want the ancient world without the full language requirement.",
       "Students drawn to the ancient Mediterranean world who prefer breadth in translation over intensive language study."),
    _p("rochester-religion-politics-society-ba", _ASE, "Bachelor of Arts in Religion, Politics, and Society", "Religion and Politics", "bachelors", 48,
       "Department of Religion and Classics", "38.02",
       "An interdisciplinary major examining how religion intersects with law, politics, and ethics in contemporary societies, bridging religious studies and the social sciences.",
       "Students interested in the public role of religion in law, politics, and social conflict."),
    _p("rochester-spanish-ba", _ASE, "Bachelor of Arts in Spanish", "Spanish", "bachelors", 48,
       "Department of Modern Languages and Cultures", "16.09",
       "Advanced Spanish language paired with cultural analysis of identity, race, and gender across Spain and Latin America, going well beyond language proficiency.",
       "Students who want fluency in Spanish alongside the study of Hispanic literatures and cultures."),
    _p("rochester-french-ba", _ASE, "Bachelor of Arts in French", "French", "bachelors", 48,
       "Department of Modern Languages and Cultures", "16.09",
       "French language and Francophone cultures across Europe, Africa, and the Americas, emphasizing critical reading of literature, film, and cultural theory.",
       "Students who want French fluency and deep engagement with Francophone literature and culture."),
    _p("rochester-german-ba", _ASE, "Bachelor of Arts in German", "German", "bachelors", 48,
       "Department of Modern Languages and Cultures", "16.05",
       "German language, literature, and thought, from the classics of German philosophy and literature to contemporary German-speaking culture and film.",
       "Students who want German fluency and access to the German intellectual and literary tradition."),
    _p("rochester-italian-ba", _ASE, "Bachelor of Arts in Italian", "Italian", "bachelors", 48,
       "Department of Modern Languages and Cultures", "16.09",
       "Italian language and culture from Dante and the Renaissance to modern Italian literature, cinema, and society, with study-abroad pathways to Italy.",
       "Students drawn to Italian language, art, and literature and the culture of Italy."),
    _p("rochester-japanese-ba", _ASE, "Bachelor of Arts in Japanese", "Japanese", "bachelors", 48,
       "Department of Modern Languages and Cultures", "16.03",
       "Japanese language across all levels combined with the study of Japanese literature, film, and culture, complementing the East Asian Studies program.",
       "Students who want Japanese proficiency and engagement with Japanese literature, media, and culture."),
    _p("rochester-russian-ba", _ASE, "Bachelor of Arts in Russian", "Russian", "bachelors", 48,
       "Department of Modern Languages and Cultures", "16.04",
       "Russian language paired with the great tradition of Russian literature and the study of Russian and Eurasian culture, history, and politics.",
       "Students who want Russian fluency and access to Russian literature and Eurasian culture."),
    _p("rochester-comparative-literature-ba", _ASE, "Bachelor of Arts in Comparative Literature", "Comparative Literature", "bachelors", 48,
       "Department of Modern Languages and Cultures", "16.01",
       "A cross-cultural, theory-driven study of literature across languages and traditions, with heavy cross-listing that supports double and triple majors.",
       "Students who want to read literature across languages and cultures through the lens of critical theory."),
    _p("rochester-art-history-ba", _ASE, "Bachelor of Arts in Art History", "Art History", "bachelors", 48,
       "Department of Art and Art History", "50.07",
       "The history of art, architecture, and visual culture, anchored by the signature 'Art New York' program that places students in New York City museums and galleries.",
       "Students who want to study art and visual culture and pursue museum, gallery, or graduate-school pathways."),
    _p("rochester-studio-arts-ba", _ASE, "Bachelor of Arts in Studio Arts", "Studio Arts", "bachelors", 48,
       "Department of Art and Art History", "50.07",
       "Hands-on training across drawing, painting, sculpture, and new media, culminating in a senior capstone exhibition at the Sage Art Center.",
       "Students who want to make art in a liberal-arts setting and mount a capstone gallery exhibition."),
    _p("rochester-visual-cultural-studies-phd", _ASE, "Doctor of Philosophy in Visual and Cultural Studies", "Visual and Cultural Studies", "phd", 60,
       "Department of Art and Art History", "50.07",
       "An interdisciplinary doctorate relating literary and cultural theory to visual culture, with faculty spanning art history, anthropology, Black studies, English, and modern languages.",
       "Aspiring scholars of visual culture who want an interdisciplinary doctorate bridging art history and critical theory."),
    _p("rochester-linguistics-ba", _ASE, "Bachelor of Arts in Linguistics", "Linguistics", "bachelors", 48,
       "Department of Linguistics", "16.01",
       "The scientific study of language — phonology, syntax, semantics, and psycholinguistics — with independent-research opportunities and ties to computer science and cognitive science.",
       "Students fascinated by how language works who want a science-of-language major with research options."),
    _p("rochester-linguistics-ma", _ASE, "Master of Arts in Linguistics", "Linguistics", "masters", 12,
       "Department of Linguistics", "16.01",
       "Graduate training in core linguistic theory and analysis for students deepening their preparation for doctoral work or language-related careers.",
       "Graduates seeking advanced linguistic training before a PhD or a language-focused career."),
    _p("rochester-language-documentation-ma", _ASE, "Master of Arts in Language Documentation and Description", "Language Documentation", "masters", 12,
       "Department of Linguistics", "16.01",
       "Field-methods training in documenting and describing under-resourced and endangered languages, combining phonetic, grammatical, and archival techniques.",
       "Students who want fieldwork-based training in documenting endangered and under-described languages."),
    _p("rochester-computational-linguistics-ms", _ASE, "Master of Science in Computational Linguistics", "Computational Linguistics", "masters", 12,
       "Department of Linguistics", "16.01",
       "A computationally oriented master's applying natural-language-processing and machine-learning methods to linguistic analysis, distinct from the theory-focused MA.",
       "Students who want to combine linguistics with programming and natural-language processing for language-technology careers."),
    _p("rochester-linguistics-phd", _ASE, "Doctor of Philosophy in Linguistics", "Linguistics", "phd", 60,
       "Department of Linguistics", "16.01",
       "A fully funded, roughly five-year doctoral program with cross-disciplinary ties to brain and cognitive sciences and computer science, training linguists for research careers.",
       "Aspiring linguists seeking a funded, cross-disciplinary doctorate connected to cognitive science and NLP."),
    _p("rochester-asl-ba", _ASE, "Bachelor of Arts in American Sign Language", "American Sign Language", "bachelors", 48,
       "American Sign Language Program", "16.16",
       "The study of American Sign Language as a language, Deaf literature and culture, and the psycholinguistics of signed versus spoken language, drawing on Rochester's large Deaf community.",
       "Students interested in ASL, Deaf culture, and the linguistics of signed languages, including future interpreters and educators."),
    _p("rochester-music-ba", _ASE, "Bachelor of Arts in Music", "Music", "bachelors", 48,
       "Arthur Satz Department of Music", "50.09",
       "A liberal-arts music major — theory, history, and performance — distinct from Eastman's conservatory model, with a pathway to take graduate music coursework at Eastman.",
       "Students who want to study music within a liberal-arts curriculum, with access to Eastman coursework."),
    _p("rochester-film-media-studies-ba", _ASE, "Bachelor of Arts in Film and Media Studies", "Film and Media Studies", "bachelors", 48,
       "Film and Media Studies Program", "50.06",
       "The study of film, television, and electronic media as art forms and cultural phenomena, combining critical analysis with hands-on media practice.",
       "Students who want to analyze and make film and media and pursue creative-industry or graduate paths."),
    _p("rochester-digital-media-studies-ba", _ASE, "Bachelor of Arts in Digital Media Studies", "Digital Media Studies", "bachelors", 48,
       "Digital Media Studies Program", "09.07",
       "An interdisciplinary major linking digital technology, critical analysis, and production, offered as either a humanities or a natural-science track.",
       "Students who want to combine digital-media production with critical study of technology and culture."),
    _p("rochester-dance-ba", _ASE, "Bachelor of Arts in Dance", "Dance", "bachelors", 48,
       "Program of Dance and Movement", "50.03",
       "A dance major spanning Western and African-Diaspora forms across two tracks — Creative Expression and Performance, and Dance Studies — integrating practice with cultural study.",
       "Students who want to study and perform dance across diverse traditions within a liberal-arts degree."),
    _p("rochester-literary-translation-ma", _ASE, "Master of Arts in Literary Translation Studies", "Literary Translation", "masters", 12,
       "Literary Translation Program", "16.01",
       "A graduate program whose thesis is a book-length literary translation of near-publishable quality, with internships through the university's Open Letter literary press.",
       "Writers and linguists who want to become literary translators and complete a book-length translation."),

    # ══════════ School of Arts & Sciences — Social Sciences ══════════
    _p("rochester-anthropology-ba", _ASE, "Bachelor of Arts in Anthropology", "Anthropology", "bachelors", 48,
       "Department of Anthropology", "45.02",
       "Socio-cultural anthropology — kinship, ritual, race and ethnicity, inequality, language, and gender — studied through ethnography and cross-cultural comparison.",
       "Students who want to understand human cultures and social life through ethnographic study."),
    _p("rochester-medical-anthropology-ba", _ASE, "Bachelor of Arts in Medical Anthropology", "Medical Anthropology", "bachelors", 48,
       "Department of Anthropology", "45.02",
       "A dedicated major on how cultural, biological, and political contexts shape health and illness, offering strong preparation for health-professions careers.",
       "Pre-health and social-science students who want to study health and medicine through a cultural lens."),
    _p("rochester-economics-ba", _ASE, "Bachelor of Arts in Economics", "Economics", "bachelors", 48,
       "Department of Economics", "45.06",
       "Micro- and macroeconomic theory with strong econometric training, in a department shaped by Rochester's tradition of rigorous, theory-forward economics.",
       "Students who want analytical training for careers in finance, consulting, policy, or economics graduate study."),
    _p("rochester-financial-economics-ba", _ASE, "Bachelor of Arts in Financial Economics", "Financial Economics", "bachelors", 48,
       "Department of Economics", "45.06",
       "An applied economics major concentrating on financial markets, asset pricing, and corporate finance, blending economic theory with quantitative finance.",
       "Students aiming for finance careers who want an economics foundation focused on financial markets."),
    _p("rochester-economics-phd", _ASE, "Doctor of Philosophy in Economics", "Economics", "phd", 60,
       "Department of Economics", "45.06",
       "A doctoral program with a distinguished tradition in general-equilibrium and economic theory — founded in part by Lionel McKenzie — training research economists.",
       "Aspiring research economists drawn to a theory-strong department with a landmark tradition in general-equilibrium theory."),
    _p("rochester-political-science-ba", _ASE, "Bachelor of Arts in Political Science", "Political Science", "bachelors", 48,
       "Department of Political Science", "45.10",
       "The study of politics and government in a department famous for the 'Rochester School' of positive, formal political theory, blending analytical rigor with substantive study.",
       "Students who want an analytically rigorous political-science major grounded in formal theory and methods."),
    _p("rochester-political-science-bs", _ASE, "Bachelor of Science in Political Science", "Political Science", "bachelors", 48,
       "Department of Political Science", "45.10",
       "A quantitatively intensive version of the political-science major, adding formal theory and statistical methodology for students headed to research or data-driven policy work.",
       "Students who want the most quantitative, methods-heavy path through political science."),
    _p("rochester-international-relations-ba", _ASE, "Bachelor of Arts in International Relations", "International Relations", "bachelors", 48,
       "Department of Political Science", "45.09",
       "The study of world politics — security, international political economy, and foreign policy — combining political science with economics and history.",
       "Students interested in global affairs, diplomacy, and international security."),
    _p("rochester-ppe-ba", _ASE, "Bachelor of Arts in Politics, Philosophy, and Economics", "Politics Philosophy Economics", "bachelors", 48,
       "Department of Political Science", "45.10",
       "An interdisciplinary major co-sponsored with philosophy and economics, integrating normative reasoning, economic analysis, and political theory around questions of justice and policy.",
       "Students who want to reason about policy and justice using tools from politics, philosophy, and economics together."),
    _p("rochester-political-science-phd", _ASE, "Doctor of Philosophy in Political Science", "Political Science", "phd", 60,
       "Department of Political Science", "45.10",
       "The birthplace of positive political theory (William Riker, 1962), this doctoral program remains at the frontier of formal theory and statistical methodology in political science.",
       "Aspiring political scientists who want a doctorate at the cutting edge of formal theory and quantitative methods."),
    _p("rochester-psychology-ba", _ASE, "Bachelor of Arts in Psychology", "Psychology", "bachelors", 48,
       "Department of Psychology", "42.01",
       "A STEM-designated psychology major spanning cognition, development, and social and clinical psychology, in the department that originated Self-Determination Theory.",
       "Students who want a research-grounded psychology major in a department known for motivation and developmental science."),
    _p("rochester-psychological-science-ms", _ASE, "Master of Science in Psychological Science", "Psychological Science", "masters", 12,
       "Department of Psychology", "42.27",
       "A terminal, research-focused master's training students as psychological scientists (not clinicians), with hands-on work in faculty labs.",
       "Graduates who want research training in psychological science before a PhD or a research career."),
    _p("rochester-psychology-phd", _ASE, "Doctor of Philosophy in Psychology", "Psychology", "phd", 60,
       "Department of Psychology", "42.01",
       "Home of Self-Determination Theory, with doctoral strengths in motivation, developmental psychopathology, close relationships, and adolescence.",
       "Aspiring research psychologists drawn to strengths in motivation science and developmental psychopathology."),
    _p("rochester-brain-cognitive-sciences-ba", _ASE, "Bachelor of Arts in Brain and Cognitive Sciences", "Brain and Cognitive Sciences", "bachelors", 48,
       "Department of Brain and Cognitive Sciences", "42.27",
       "The study of the mind at the intersection of cognitive psychology, computer science, and neuroscience — perception, language, and learning through experiment and computation.",
       "Students fascinated by how minds and brains work who want an interdisciplinary cognitive-science major."),
    _p("rochester-brain-cognitive-sciences-bs", _ASE, "Bachelor of Science in Brain and Cognitive Sciences", "Brain and Cognitive Sciences", "bachelors", 48,
       "Department of Brain and Cognitive Sciences", "42.27",
       "The more technical track in brain and cognitive sciences, adding biology, mathematics, computer science, and symbolic-systems coursework for computational and neural study.",
       "Students who want a quantitative, computationally intensive path through cognitive science."),
    _p("rochester-brain-cognitive-sciences-phd", _ASE, "Doctor of Philosophy in Brain and Cognitive Sciences", "Brain and Cognitive Sciences", "phd", 60,
       "Department of Brain and Cognitive Sciences", "42.27",
       "Doctoral research uniting cognitive psychology, computer science, and neuroscience, with strengths in computational modeling of vision, language, perception, and learning.",
       "Aspiring cognitive scientists who want computational and experimental training on mind and brain."),
    _p("rochester-history-ba", _ASE, "Bachelor of Arts in History", "History", "bachelors", 48,
       "Department of History", "54.01",
       "The study of the past across regions and periods, emphasizing primary-source research, argument, and writing in a transnational and comparative frame.",
       "Students who want to research and interpret the past and build strong analytical writing skills."),
    _p("rochester-history-ma", _ASE, "Master of Arts in History", "History", "masters", 12,
       "Department of History", "54.01",
       "A 30-credit, individually tailored master's with a transnational and comparative emphasis, for students deepening historical research skills.",
       "Graduates who want an individually designed year of advanced historical research and writing."),
    _p("rochester-history-phd", _ASE, "Doctor of Philosophy in History", "History", "phd", 60,
       "Department of History", "54.01",
       "A tutorial-style, individually tailored doctoral program at a research university, training historians through close mentorship and archival research.",
       "Aspiring historians who want a small, mentorship-driven doctorate with a transnational orientation."),
    _p("rochester-health-behavior-society-ba", _ASE, "Bachelor of Arts in Health, Behavior, and Society", "Health and Society", "bachelors", 48,
       "Undergraduate Program in Public Health", "51.22",
       "A public-health major examining how behavior, social conditions, and communities shape health, bridging the social sciences and population health.",
       "Students interested in the social and behavioral drivers of health and in public-health careers."),
    _p("rochester-epidemiology-ba", _ASE, "Bachelor of Arts in Epidemiology", "Epidemiology", "bachelors", 48,
       "Undergraduate Program in Public Health", "51.22",
       "An undergraduate epidemiology major studying the patterns, causes, and control of disease in populations, with quantitative and study-design training.",
       "Students drawn to disease detection and population health who want quantitative public-health training."),
    _p("rochester-environmental-health-bs", _ASE, "Bachelor of Science in Environmental Health", "Environmental Health", "bachelors", 48,
       "Undergraduate Program in Public Health", "51.22",
       "A science-based major on how the physical and chemical environment affects human health, spanning toxicology, exposure, and environmental policy.",
       "Students who want to study environmental determinants of health with a strong science foundation."),
    _p("rochester-health-policy-ba", _ASE, "Bachelor of Arts in Health Policy", "Health Policy", "bachelors", 48,
       "Undergraduate Program in Public Health", "51.22",
       "The analysis of health policy at local, national, and global levels — financing, access, and reform — combining public health with economics and political science.",
       "Students interested in how health systems are financed, governed, and reformed."),
    _p("rochester-bioethics-ba", _ASE, "Bachelor of Arts in Bioethics", "Bioethics", "bachelors", 48,
       "Undergraduate Program in Public Health", "51.32",
       "The study of ethical issues in health, medicine, and the life sciences, bridging philosophy, medicine, and public health for pre-health and pre-law students.",
       "Students who want to grapple with ethical questions in medicine and the life sciences."),

    # ══════════ School of Arts & Sciences — Natural Sciences ══════════
    _p("rochester-biology-ba", _ASE, "Bachelor of Arts in Biology", "Biology", "bachelors", 48,
       "Department of Biology", "26.01",
       "A broad, research-oriented biology major without single-field specialization, suited to students combining life science with other interests.",
       "Students who want a flexible life-science major with room to combine biology with other fields."),
    _p("rochester-biological-sciences-bs", _ASE, "Bachelor of Science in Biological Sciences", "Biological Sciences", "bachelors", 48,
       "Department of Biology", "26.01",
       "A rigorous BS with eight concentration tracks — from cell and developmental biology to computational biology and a neuroscience track run jointly with brain and cognitive sciences.",
       "Students preparing for medicine or research who want a deep, concentration-based life-science degree.",
       tracks=["General Biology", "Biochemistry", "Cell and Developmental Biology", "Computational Biology", "Ecology and Evolutionary Biology", "Microbiology", "Molecular Genetics", "Neuroscience"]),
    _p("rochester-biology-ms", _ASE, "Master of Science in Biology", "Biology", "masters", 12,
       "Department of Biology", "26.01",
       "A 30-credit master's offered as a thesis (Plan A) or coursework-and-exam (Plan B) track, for students deepening biological research skills.",
       "Graduates who want a year of advanced biology, by thesis research or coursework, before a PhD or health-professions school."),
    _p("rochester-biology-phd", _ASE, "Doctor of Philosophy in Biology", "Biology", "phd", 60,
       "Department of Biology", "26.01",
       "A doctoral program with first-year rotations through three labs — including affiliated labs at the Medical Center — spanning molecular, cellular, ecological, and evolutionary biology.",
       "Aspiring biologists who want lab-rotation-based doctoral training linked to the Medical Center."),
    _p("rochester-chemistry-ba", _ASE, "Bachelor of Arts in Chemistry", "Chemistry", "bachelors", 48,
       "Department of Chemistry", "40.05",
       "A flexible, interdisciplinary chemistry major well suited to pre-health students, offering four focus areas within a strong research department.",
       "Pre-health and interdisciplinary students who want chemistry with flexibility."),
    _p("rochester-chemistry-bs", _ASE, "Bachelor of Science in Chemistry", "Chemistry", "bachelors", 48,
       "Department of Chemistry", "40.05",
       "The ACS-approved professional-chemist degree, with intensive coursework and undergraduate research in synthesis, materials, and physical chemistry.",
       "Students who want a professional chemistry degree and preparation for chemistry graduate study or industry."),
    _p("rochester-chemistry-phd", _ASE, "Doctor of Philosophy in Chemistry", "Chemistry", "phd", 60,
       "Department of Chemistry", "40.05",
       "A doctoral program with a low student-to-faculty ratio (about 95 doctoral students) and research across organic, inorganic, physical, and materials chemistry.",
       "Aspiring chemists who want close mentorship in a mid-size, research-intensive doctoral program."),
    _p("rochester-physics-ba", _ASE, "Bachelor of Arts in Physics", "Physics", "bachelors", 48,
       "Department of Physics and Astronomy", "40.08",
       "A broad, flexible physics track supporting double majors, covering classical and modern physics with room for interdisciplinary study.",
       "Students who want physics with the flexibility to double major or explore related fields."),
    _p("rochester-physics-bs", _ASE, "Bachelor of Science in Physics", "Physics", "bachelors", 48,
       "Department of Physics and Astronomy", "40.08",
       "The intensive physics track for graduate-school preparation, with deep coursework and research access to the Laboratory for Laser Energetics.",
       "Students headed to physics graduate school who want the most rigorous undergraduate track."),
    _p("rochester-physics-astronomy-ba", _ASE, "Bachelor of Arts in Physics and Astronomy", "Physics and Astronomy", "bachelors", 48,
       "Department of Physics and Astronomy", "40.08",
       "An astrophysics-focused physics major combining core physics with astronomy and cosmology coursework and observational opportunities.",
       "Students drawn to astrophysics who want a flexible physics-and-astronomy major."),
    _p("rochester-physics-astronomy-bs", _ASE, "Bachelor of Science in Physics and Astronomy", "Physics and Astronomy", "bachelors", 48,
       "Department of Physics and Astronomy", "40.08",
       "The intensive astrophysics track, pairing rigorous physics with astronomy and research toward graduate study in astrophysics.",
       "Students preparing for astrophysics graduate study who want the intensive track."),
    _p("rochester-physics-phd", _ASE, "Doctor of Philosophy in Physics", "Physics", "phd", 60,
       "Department of Physics and Astronomy", "40.08",
       "Doctoral research with a signature strength in high-energy-density and laser physics tied to the Laboratory for Laser Energetics, plus quantum optics and astrophysics.",
       "Aspiring physicists drawn to laser and high-energy-density physics, quantum optics, or astrophysics."),
    _p("rochester-mathematics-ba", _ASE, "Bachelor of Arts in Mathematics", "Mathematics", "bachelors", 48,
       "Department of Mathematics", "27.01",
       "A flexible mathematics major covering analysis, algebra, and geometry, suited to students combining math with other fields.",
       "Students who want a flexible mathematics major alongside other interests."),
    _p("rochester-mathematics-bs", _ASE, "Bachelor of Science in Mathematics", "Mathematics", "bachelors", 48,
       "Department of Mathematics", "27.01",
       "The intensive mathematics track with deeper coursework in analysis, algebra, and topology for students headed to graduate study.",
       "Students preparing for mathematics graduate school or quantitative careers."),
    _p("rochester-applied-mathematics-bs", _ASE, "Bachelor of Science in Applied Mathematics", "Applied Mathematics", "bachelors", 48,
       "Department of Mathematics", "27.03",
       "Mathematics oriented toward modeling and computation — differential equations, numerical methods, and applications across science and engineering.",
       "Students who want to apply mathematics to problems in science, engineering, and data."),
    _p("rochester-mathematics-statistics-ba", _ASE, "Bachelor of Arts in Mathematics and Statistics", "Mathematics and Statistics", "bachelors", 48,
       "Department of Mathematics", "27.01",
       "A joint major combining mathematical foundations with statistical theory and methods, offered with the Statistics program.",
       "Students who want both mathematical depth and statistical methods in one major."),
    _p("rochester-mathematics-phd", _ASE, "Doctor of Philosophy in Mathematics", "Mathematics", "phd", 60,
       "Department of Mathematics", "27.01",
       "A doctoral program in pure and applied mathematics with a master's earned en route, training mathematicians for research and academia.",
       "Aspiring mathematicians who want a research doctorate in pure or applied mathematics."),
    _p("rochester-statistics-ba", _ASE, "Bachelor of Arts in Statistics", "Statistics", "bachelors", 48,
       "Statistics Program", "27.05",
       "The study of probability, statistical inference, and data analysis, combining theory with statistical computing.",
       "Students who want a foundation in statistics and data analysis for research or industry."),
    _p("rochester-statistics-bs", _ASE, "Bachelor of Science in Statistics", "Statistics", "bachelors", 48,
       "Statistics Program", "27.05",
       "The intensive statistics track — probability, inference, linear models, and Bayesian methods with statistical computing — for quantitative careers and graduate study.",
       "Students who want rigorous statistical theory and computing for data-intensive careers."),
    _p("rochester-earth-environmental-planetary-bs", _ASE, "Bachelor of Science in Earth, Environmental, and Planetary Science", "Earth and Planetary Science", "bachelors", 48,
       "Department of Earth and Environmental Sciences", "40.06",
       "The study of the Earth and other planetary bodies — geochemistry, tectonics, climate, and planetary processes — with fieldwork and laboratory analysis.",
       "Students fascinated by the Earth and planets who want a quantitative geoscience degree."),
    _p("rochester-geological-sciences-ba", _ASE, "Bachelor of Arts in Geological Sciences", "Geological Sciences", "bachelors", 48,
       "Department of Earth and Environmental Sciences", "40.06",
       "A broad geology major covering the composition, structure, and history of the Earth, with field and laboratory experience.",
       "Students drawn to geology who want a flexible Earth-science major."),
    _p("rochester-environmental-studies-ba", _ASE, "Bachelor of Arts in Environmental Studies", "Environmental Studies", "bachelors", 48,
       "Department of Earth and Environmental Sciences", "03.01",
       "An interdisciplinary environmental major connecting Earth science with policy, economics, and the humanities to address environmental challenges.",
       "Students who want to address environmental problems across science, policy, and society."),
    _p("rochester-geomechanics-bs", _ASE, "Bachelor of Science in Geomechanics", "Geomechanics", "bachelors", 48,
       "Department of Earth and Environmental Sciences", "40.06",
       "A joint Earth-science and mechanical-engineering major applying mechanics to the atmosphere, water, and the solid Earth.",
       "Students who want to apply engineering mechanics to Earth and environmental systems."),
    _p("rochester-earth-environmental-ms", _ASE, "Master of Science in Earth and Environmental Sciences", "Earth and Environmental Sciences", "masters", 12,
       "Department of Earth and Environmental Sciences", "40.06",
       "A research master's with departmental strengths in geochemistry, paleomagnetism, geodynamics, and tectonics.",
       "Graduates who want research training in Earth and environmental science before a PhD or a technical career."),
    _p("rochester-earth-environmental-phd", _ASE, "Doctor of Philosophy in Earth and Environmental Sciences", "Earth and Environmental Sciences", "phd", 60,
       "Department of Earth and Environmental Sciences", "40.06",
       "Doctoral research across geochemistry, geophysics, tectonics, and climate, with fieldwork and laboratory analysis of the Earth system.",
       "Aspiring Earth scientists who want a research doctorate across geochemistry, geophysics, and climate."),

    # ══════════ School of Arts & Sciences — Interdepartmental / area studies ══════════
    _p("rochester-east-asian-studies-ba", _ASE, "Bachelor of Arts in East Asian Studies", "East Asian Studies", "bachelors", 48,
       "East Asian Studies Program", "05.01",
       "An interdisciplinary major integrating East Asian languages, history, and culture across China, Japan, and Korea.",
       "Students who want an interdisciplinary major in East Asian languages, history, and culture."),
    _p("rochester-russian-studies-ba", _ASE, "Bachelor of Arts in Russian Studies", "Russian Studies", "bachelors", 48,
       "Russian Studies Program", "05.01",
       "An interdisciplinary major on Russia and Eurasia, combining Russian language with history, politics, and culture.",
       "Students interested in Russia and Eurasia across language, history, and politics."),
    _p("rochester-black-studies-ba", _ASE, "Bachelor of Arts in Black Studies", "Black Studies", "bachelors", 48,
       "Frederick Douglass Institute for African and African-American Studies", "05.02",
       "The interdisciplinary study of the histories, cultures, and politics of Africa and the African diaspora, based in the Frederick Douglass Institute.",
       "Students drawn to the history, culture, and politics of Africa and the Black diaspora."),
    _p("rochester-gsws-ba", _ASE, "Bachelor of Arts in Gender, Sexuality, and Women's Studies", "Gender and Sexuality Studies", "bachelors", 48,
       "Susan B. Anthony Institute for Gender, Sexuality, and Women's Studies", "05.02",
       "An interdisciplinary major, offered in humanities and social-science versions, examining gender and sexuality across culture, politics, and history through the Susan B. Anthony Institute.",
       "Students who want to study gender and sexuality across the humanities and social sciences."),
    _p("rochester-latin-american-studies-ba", _ASE, "Bachelor of Arts in Latin American, Caribbean, and Latinx Studies", "Latin American Studies", "bachelors", 48,
       "Latin American, Caribbean, and Latinx Studies Program", "05.01",
       "An interdisciplinary major on Latin America, the Caribbean, and U.S. Latinx communities, spanning language, history, politics, and culture.",
       "Students interested in Latin America, the Caribbean, and Latinx communities."),

    # ══════════ Hajim School of Engineering & Applied Sciences ══════════
    _p("rochester-biomedical-engineering-bs", _HAJIM, "Bachelor of Science in Biomedical Engineering", "Biomedical Engineering", "bachelors", 48,
       "Department of Biomedical Engineering", "14.05",
       "Engineering applied to medicine and biology, culminating in a year-long senior design sequence and Design Day; several student projects have led to patents or startups.",
       "Students who want to apply engineering to healthcare and medical-device design."),
    _p("rochester-biomedical-engineering-ms", _HAJIM, "Master of Science in Biomedical Engineering", "Biomedical Engineering", "masters", 18,
       "Department of Biomedical Engineering", "14.05",
       "Graduate biomedical engineering with a one-year Medical Technology and Innovation track centered on medical-device design and an eight-week clinical immersion.",
       "Graduates who want advanced biomedical-engineering training, including hands-on medical-device design.",
       delivery_format="on_campus"),
    _p("rochester-biomedical-engineering-phd", _HAJIM, "Doctor of Philosophy in Biomedical Engineering", "Biomedical Engineering", "phd", 60,
       "Department of Biomedical Engineering", "14.05",
       "Lab-rotation-based doctoral research spanning biomedical imaging, biomechanics, and tissue engineering, with an MD/PhD pathway through the School of Medicine and Dentistry.",
       "Aspiring biomedical-engineering researchers, including MD/PhD candidates."),
    _p("rochester-chemical-engineering-bs", _HAJIM, "Bachelor of Science in Chemical Engineering", "Chemical Engineering", "bachelors", 48,
       "Department of Chemical and Sustainability Engineering", "14.07",
       "ABET-accredited chemical engineering with hands-on lab work beginning in the first semester, including a project designing a solar hot-water system.",
       "Students who want to design chemical and energy processes with early hands-on lab experience."),
    _p("rochester-chemical-engineering-ms", _HAJIM, "Master of Science in Chemical Engineering", "Chemical Engineering", "masters", 18,
       "Department of Chemical and Sustainability Engineering", "14.07",
       "A one-to-two-year master's by coursework plus research or coursework-only, with electives tied to faculty groups in catalysis, batteries, and biological systems.",
       "Graduates who want advanced chemical-engineering study aligned to a faculty research area.",
       delivery_format="on_campus"),
    _p("rochester-chemical-engineering-phd", _HAJIM, "Doctor of Philosophy in Chemical Engineering", "Chemical Engineering", "phd", 60,
       "Department of Chemical and Sustainability Engineering", "14.07",
       "Doctoral research spanning catalysis and electrocatalysis, batteries, biological and medical systems, computational fluid dynamics, and AI-driven simulation.",
       "Aspiring chemical-engineering researchers in energy, catalysis, or biological systems."),
    _p("rochester-electrical-computer-engineering-bs", _HAJIM, "Bachelor of Science in Electrical and Computer Engineering", "Electrical and Computer Engineering", "bachelors", 48,
       "Department of Electrical and Computer Engineering", "14.10",
       "A broad ECE degree letting students concentrate across integrated circuits, waves and fields, semiconductor devices, and robotics.",
       "Students who want to design electronic and computer systems from circuits to robotics."),
    _p("rochester-electrical-engineering-ms", _HAJIM, "Master of Science in Electrical Engineering", "Electrical Engineering", "masters", 18,
       "Department of Electrical and Computer Engineering", "14.10",
       "Graduate electrical engineering spanning signal and image processing, communications, medical imaging, photonics, and nanoscale electronics.",
       "Graduates who want advanced work in signal processing, photonics, or medical imaging.",
       delivery_format="on_campus"),
    _p("rochester-electrical-engineering-phd", _HAJIM, "Doctor of Philosophy in Electrical Engineering", "Electrical Engineering", "phd", 60,
       "Department of Electrical and Computer Engineering", "14.10",
       "Doctoral research in computer engineering and architecture, signal and image processing, medical imaging, and photonics.",
       "Aspiring electrical-engineering researchers in imaging, photonics, or computer engineering."),
    _p("rochester-diagnostic-imaging-ms", _HAJIM, "Master of Science in Diagnostic Imaging", "Diagnostic Imaging", "masters", 18,
       "Department of Electrical and Computer Engineering", "14.10",
       "A multidisciplinary master's pairing engineering imaging fundamentals with radiological applications in a clinical environment.",
       "Graduates who want to specialize in medical and diagnostic imaging engineering.",
       delivery_format="on_campus"),
    _p("rochester-mechanical-engineering-bs", _HAJIM, "Bachelor of Science in Mechanical Engineering", "Mechanical Engineering", "bachelors", 48,
       "Department of Mechanical Engineering", "14.19",
       "ABET-accredited mechanical engineering with hands-on team projects such as the Baja and Solar Splash competition teams.",
       "Students who want to design mechanical systems with hands-on, competition-driven projects."),
    _p("rochester-mechanical-engineering-ms", _HAJIM, "Master of Science in Mechanical Engineering", "Mechanical Engineering", "masters", 18,
       "Department of Mechanical Engineering", "14.19",
       "Graduate mechanical engineering built on two research pillars — solid mechanics and materials science, and fluid mechanics and plasma physics.",
       "Graduates who want advanced study in mechanics, materials, or fluid and plasma physics.",
       delivery_format="on_campus"),
    _p("rochester-aerospace-engineering-ms", _HAJIM, "Master of Science in Aerospace Engineering", "Aerospace Engineering", "masters", 18,
       "Department of Mechanical Engineering", "14.02",
       "Aerospace-focused graduate study within mechanical engineering, covering aerodynamics, propulsion, and structures.",
       "Graduates who want aerospace-focused engineering training.",
       delivery_format="on_campus"),
    _p("rochester-mechanical-engineering-phd", _HAJIM, "Doctor of Philosophy in Mechanical Engineering", "Mechanical Engineering", "phd", 60,
       "Department of Mechanical Engineering", "14.19",
       "Interdisciplinary doctoral research connected to the Laboratory for Laser Energetics and the Rochester Center for Biomedical Ultrasound.",
       "Aspiring mechanical-engineering researchers in mechanics, materials, plasma, or ultrasound."),
    _p("rochester-optics-bs", _HAJIM, "Bachelor of Science in Optics", "Optics", "bachelors", 48,
       "The Institute of Optics", "14.10",
       "An undergraduate degree from the Institute of Optics — the first optics program in the United States — with a senior year built around a comprehensive research thesis.",
       "Students who want to study light and optical science at the nation's founding optics program."),
    _p("rochester-optical-engineering-bs", _HAJIM, "Bachelor of Science in Optical Engineering", "Optical Engineering", "bachelors", 48,
       "The Institute of Optics", "14.10",
       "An ABET-accredited optical-engineering degree culminating in two senior-design courses that solve real, company-sponsored problems.",
       "Students who want to engineer optical systems and instruments for industry."),
    _p("rochester-optics-ms", _HAJIM, "Master of Science in Optics", "Optics", "masters", 12,
       "The Institute of Optics", "14.10",
       "A graduate optics degree completable on campus or virtually through the Institute of Optics distance-learning program, deepening expertise in optical science and instrumentation.",
       "Graduates who want advanced optics training, on campus or online, for the photonics industry.",
       delivery_format="hybrid"),
    _p("rochester-optics-phd", _HAJIM, "Doctor of Philosophy in Optics", "Optics", "phd", 60,
       "The Institute of Optics", "14.10",
       "Doctoral research at the Institute of Optics combining coursework, teaching, and thesis research for careers in academia, industry, or the national labs.",
       "Aspiring optics researchers headed for academia, the photonics industry, or national labs."),
    _p("rochester-computer-science-bs", _HAJIM, "Bachelor of Science in Computer Science", "Computer Science", "bachelors", 48,
       "Department of Computer Science", "11.07",
       "A rigorous computer-science degree with concentration options in artificial intelligence, human-computer interaction, systems, and theory.",
       "Students who want a technical computer-science degree with room to concentrate in AI, systems, or theory."),
    _p("rochester-computer-science-ba", _HAJIM, "Bachelor of Arts in Computer Science", "Computer Science", "bachelors", 48,
       "Department of Computer Science", "11.07",
       "A more flexible computer-science track designed for interdisciplinary students and double majors.",
       "Students who want computer science with the flexibility to double major or combine fields."),
    _p("rochester-computer-science-ms", _HAJIM, "Master of Science in Computer Science", "Computer Science", "masters", 18,
       "Department of Computer Science", "11.07",
       "A graduate computer-science degree typically completed in three semesters, with part-time enrollment supported.",
       "Graduates who want advanced computer-science coursework and research, full- or part-time.",
       delivery_format="on_campus"),
    _p("rochester-computer-science-phd", _HAJIM, "Doctor of Philosophy in Computer Science", "Computer Science", "phd", 60,
       "Department of Computer Science", "11.07",
       "A funded doctoral program known for competitive stipends, with research across AI, systems, theory, and human-computer interaction.",
       "Aspiring computer scientists who want a funded doctorate with strong stipend support."),
    _p("rochester-data-science-ba", _HAJIM, "Bachelor of Arts in Data Science", "Data Science", "bachelors", 48,
       "Goergen Institute for Data Science and Artificial Intelligence", "30.70",
       "A data-science major combining computer science and statistics with an applied-domain track in fields such as business, biology, or political science.",
       "Students who want to combine data science with an applied field of interest."),
    _p("rochester-data-science-bs", _HAJIM, "Bachelor of Science in Data Science", "Data Science", "bachelors", 48,
       "Goergen Institute for Data Science and Artificial Intelligence", "30.70",
       "The more technical data-science track with a deeper computing and methods sequence and a semester-long industry-sponsored capstone.",
       "Students who want a technical data-science degree with an industry capstone."),
    _p("rochester-data-science-ms", _HAJIM, "Master of Science in Data Science", "Data Science", "masters", 18,
       "Goergen Institute for Data Science and Artificial Intelligence", "30.70",
       "A 30-credit, STEM-designated master's with focus options in computational and statistical methods, health and biomedical science, or business and social science.",
       "Graduates who want a STEM-designated data-science master's with a focus area.",
       delivery_format="on_campus"),
    _p("rochester-audio-music-engineering-bs", _HAJIM, "Bachelor of Science in Audio and Music Engineering", "Audio and Music Engineering", "bachelors", 48,
       "Department of Audio and Music Engineering", "14.10",
       "An ABET-accredited engineering degree in audio and music technology — recording arts, acoustics, audio electronics, and signal processing — with music coursework at Eastman and the Satz Department.",
       "Students who want to engineer audio and music technology, blending electrical engineering with music."),

    # ══════════ Eastman School of Music ══════════
    _p("rochester-eastman-performance-bm", _EASTMAN, "Bachelor of Music in Applied Music", "Performance", "bachelors", 48,
       "Eastman School of Music", "50.09",
       "Conservatory performance training on a primary instrument or voice at one of the world's foremost music schools, with a dense concert calendar in Kodak Hall and the Eastman Theatre.",
       "Undergraduate musicians seeking elite conservatory performance training within a research university."),
    _p("rochester-eastman-composition-bm", _EASTMAN, "Bachelor of Music in Composition", "Composition", "bachelors", 48,
       "Eastman School of Music", "50.09",
       "A four-year composition degree developing original creative work alongside performance and academic musicianship, with faculty mentorship and regular readings of student works.",
       "Aspiring composers who want conservatory training in writing and hearing their own music."),
    _p("rochester-eastman-jazz-bm", _EASTMAN, "Bachelor of Music in Jazz Studies and Contemporary Media", "Jazz Studies", "bachelors", 48,
       "Eastman School of Music", "50.09",
       "A combined major in jazz performance, improvisation, arranging, and contemporary media, taught by a nationally recognized jazz faculty.",
       "Musicians who want conservatory-level training in jazz performance and contemporary media."),
    _p("rochester-eastman-music-education-bm", _EASTMAN, "Bachelor of Music in Music Education", "Music Education", "bachelors", 48,
       "Eastman School of Music", "50.09",
       "Training future music teachers across general, vocal, and instrumental emphases, with most students double-majoring in performance or jazz.",
       "Future music educators who want conservatory musicianship alongside teacher preparation."),
    _p("rochester-eastman-musical-arts-bm", _EASTMAN, "Bachelor of Music in Musical Arts", "Musical Arts", "bachelors", 48,
       "Eastman School of Music", "50.09",
       "A flexible conservatory degree combining a music core with broad study, for students who want conservatory training with room for other academic interests.",
       "Musicians who want conservatory training with the flexibility to pursue interests beyond performance."),
    _p("rochester-eastman-theory-bm", _EASTMAN, "Bachelor of Music in Theory", "Music Theory", "bachelors", 48,
       "Eastman School of Music", "50.09",
       "An undergraduate music-theory degree for students with advanced aural and written skills, combining analysis with performance and composition.",
       "Musicians drawn to the analysis and structure of music who have advanced theory skills."),
    _p("rochester-eastman-mm", _EASTMAN, "Master of Music", "Music Performance", "masters", 24,
       "Eastman School of Music", "50.09",
       "A performance-centered graduate degree in applied music, also offered in composition and music education, deepening artistry and repertoire under an elite applied faculty.",
       "Graduate musicians pursuing advanced performance, composition, or music-education training."),
    _p("rochester-eastman-musicology-ma", _EASTMAN, "Master of Arts in Musicology", "Musicology", "masters", 24,
       "Eastman School of Music", "50.09",
       "A research degree emphasizing writing and scholarship on music history and culture, drawing on the Sibley Music Library, the largest academic music library in North America.",
       "Students who want to research and write about music history before doctoral work."),
    _p("rochester-eastman-music-theory-ma", _EASTMAN, "Master of Arts in Music Theory", "Music Theory", "masters", 24,
       "Eastman School of Music", "50.09",
       "A research and writing-focused graduate degree in music theory and analysis, foundational for doctoral study or college teaching.",
       "Musicians pursuing advanced study in music theory and analysis."),
    _p("rochester-eastman-ethnomusicology-ma", _EASTMAN, "Master of Arts in Ethnomusicology", "Ethnomusicology", "masters", 24,
       "Eastman School of Music", "50.09",
       "The study of music in cultural context, combining fieldwork, theory, and analysis of musical traditions worldwide.",
       "Students who want to study music across cultures through fieldwork and scholarship."),
    _p("rochester-eastman-music-leadership-ma", _EASTMAN, "Master of Arts in Music Leadership", "Music Leadership", "masters", 24,
       "Institute for Music Leadership", "50.10",
       "An online degree for musicians who want to lead traditional and non-traditional musical-arts organizations, through the Institute for Music Leadership.",
       "Musicians who want to lead arts organizations and build careers in music administration.",
       delivery_format="online"),
    _p("rochester-eastman-dma", _EASTMAN, "Doctor of Musical Arts", "Music Performance", "professional", 48,
       "Eastman School of Music", "50.09",
       "A practice doctorate awarded for high attainment in performance and teaching, requiring an audition on an applied instrument or voice, distinct from the research PhD.",
       "Accomplished performers pursuing the highest practice doctorate in music."),
    _p("rochester-eastman-musicology-phd", _EASTMAN, "Doctor of Philosophy in Musicology", "Musicology", "phd", 60,
       "Eastman School of Music", "50.09",
       "A research doctorate producing original scholarship in music history and culture, defended in a dissertation, supported by the Sibley Music Library's collections.",
       "Aspiring music scholars pursuing a research doctorate in music history."),
    _p("rochester-eastman-music-theory-phd", _EASTMAN, "Doctor of Philosophy in Music Theory", "Music Theory", "phd", 60,
       "Eastman School of Music", "50.09",
       "A research doctorate in music theory and analysis, training scholars and college teachers through dissertation research.",
       "Aspiring music-theory scholars and college teachers pursuing a research doctorate."),
    _p("rochester-eastman-composition-phd", _EASTMAN, "Doctor of Philosophy in Composition", "Composition", "phd", 60,
       "Eastman School of Music", "50.09",
       "A doctorate awarded for outstanding creative work in composition, combining an original body of music with scholarly study.",
       "Composers pursuing the research doctorate for outstanding creative work."),
    _p("rochester-eastman-music-education-phd", _EASTMAN, "Doctor of Philosophy in Music Education", "Music Education", "phd", 60,
       "Eastman School of Music", "50.09",
       "A research doctorate in music education emphasizing scholarship and inquiry into how music is taught and learned.",
       "Music educators pursuing a research doctorate to lead scholarship in the field."),

    # ══════════ Simon Business School ══════════
    _p("rochester-mba", _SIMON, "Master of Business Administration", "Business Administration", "masters", 21,
       "Simon Business School", "52.02",
       "A two-year, economics-based MBA of about twelve required courses, notable as the first U.S. program to make every concentration STEM-designated.",
       "Early-career professionals seeking an analytical, economics-based MBA with STEM-designated concentrations."),
    _p("rochester-mba-professional", _SIMON, "Professional Master of Business Administration", "Business Administration", "masters", 36,
       "Simon Business School", "52.02",
       "A part-time, weekday-evening MBA delivering Simon's economics-based curriculum on a self-paced schedule for working professionals.",
       "Working professionals who want Simon's MBA part-time while continuing to work.",
       delivery_format="on_campus"),
    _p("rochester-mba-executive", _SIMON, "Executive Master of Business Administration", "Business Administration", "masters", 22,
       "Simon Business School", "52.02",
       "A high-flex executive MBA combining online and in-class study with a global immersion, for experienced leaders advancing their careers.",
       "Experienced managers and executives seeking an MBA built around their leadership work.",
       delivery_format="hybrid"),
    _p("rochester-finance-ms", _SIMON, "Master of Science in Finance", "Finance", "masters", 12,
       "Simon Business School", "52.08",
       "A STEM-designated specialized master's applying analytics and quantitative tools to investment management, corporate finance, and risk.",
       "Aspiring finance professionals who want a quantitative, STEM-designated finance master's."),
    _p("rochester-business-analytics-ms", _SIMON, "Master of Science in Business Analytics", "Business Analytics", "masters", 12,
       "Simon Business School", "52.13",
       "Simon's signature economics-based approach to analytics, training students to turn data into business decisions across functions.",
       "Graduates who want an analytics master's grounded in Simon's economics-based method."),
    _p("rochester-accountancy-ms", _SIMON, "Master of Science in Accountancy", "Accountancy", "masters", 12,
       "Simon Business School", "52.03",
       "A STEM-designated, 150-credit-hour accountancy degree qualifying graduates for the New York State CPA exam.",
       "Graduates pursuing CPA licensure and careers in accounting and audit."),
    _p("rochester-marketing-analytics-ms", _SIMON, "Master of Science in Marketing Analytics", "Marketing Analytics", "masters", 12,
       "Simon Business School", "52.14",
       "A STEM-designated master's applying data and analytics to digital marketing, customer insight, and marketing-analytics careers.",
       "Graduates who want to apply analytics to marketing and customer decisions."),
    _p("rochester-ai-business-ms", _SIMON, "Master of Science in Artificial Intelligence in Business", "AI in Business", "masters", 12,
       "Simon Business School", "52.13",
       "A STEM-designated master's combining programming, statistics, and AI-driven analytics for data- and AI-focused business roles.",
       "Graduates who want to apply artificial intelligence and analytics to business problems."),
    _p("rochester-business-administration-phd", _SIMON, "Doctor of Philosophy in Business Administration", "Business Administration", "phd", 60,
       "Simon Business School", "52.02",
       "A research doctorate rooted in economics and statistics with fields in accounting, finance, information systems, marketing, and operations, funded by a five-year fellowship.",
       "Aspiring business-school researchers seeking a funded, economics-based doctorate.",
       tracks=["Accounting", "Finance", "Information Systems", "Marketing", "Operations Management"]),
    _p("rochester-dba", _SIMON, "Doctor of Business Administration", "Business Administration", "professional", 36,
       "Simon Business School", "52.02",
       "A part-time practice doctorate for senior leaders, combining virtual evening study with on-campus weekends across practice and teaching tracks.",
       "Senior executives who want a practice doctorate while continuing to lead.",
       delivery_format="hybrid"),

    # ══════════ Warner School of Education & Human Development ══════════
    _p("rochester-teaching-curriculum-ms", _WARNER, "Master of Science in Teaching and Curriculum", "Teaching and Curriculum", "masters", 12,
       "Program in Teaching and Curriculum", "13.12",
       "Teacher preparation that embeds New York State initial teaching certification, combining pedagogy, content methods, and supervised field placement.",
       "Aspiring teachers seeking a master's with New York State initial certification."),
    _p("rochester-school-counseling-ms", _WARNER, "Master of Science in School Counseling", "School Counseling", "masters", 24,
       "Program in Counseling and Human Development", "13.11",
       "Preparation for certified school counseling, integrating counseling theory, developmental science, and supervised practice in schools.",
       "Students preparing to become certified school counselors."),
    _p("rochester-mental-health-counseling-ms", _WARNER, "Master of Science in Clinical Mental Health Counseling", "Mental Health Counseling", "masters", 24,
       "Program in Counseling and Human Development", "13.11",
       "A licensure-track master's in clinical mental-health counseling, combining counseling theory, assessment, and supervised clinical practice.",
       "Students pursuing licensure as clinical mental-health counselors."),
    _p("rochester-higher-education-ms", _WARNER, "Master of Science in Higher Education", "Higher Education", "masters", 18,
       "Program in Educational Leadership", "13.04",
       "The study of colleges and universities as organizations — administration, student affairs, and policy — for careers in higher-education leadership.",
       "Professionals pursuing careers in college and university administration and student affairs."),
    _p("rochester-k12-educational-leadership-ms", _WARNER, "Master of Science in K-12 Educational Leadership", "Educational Leadership", "masters", 18,
       "Program in Educational Leadership", "13.04",
       "Preparation for school and district leadership roles, with certification-track coursework in administration, supervision, and school improvement.",
       "Educators moving into K-12 school and district leadership."),
    _p("rochester-education-policy-ms", _WARNER, "Master of Science in Education Policy", "Education Policy", "masters", 18,
       "Program in Educational Leadership", "13.04",
       "The analysis of education policy and its effects, combining policy study with research methods for careers in analysis and advocacy.",
       "Students interested in analyzing and shaping education policy."),
    _p("rochester-health-professions-education-ms", _WARNER, "Master of Science in Health Professions Education", "Health Professions Education", "masters", 18,
       "Program in Health Professions Education", "51.32",
       "Training clinicians and educators to teach in the health professions, combining learning science with instructional design for medical and health education.",
       "Clinicians and educators who want to teach and lead in health-professions education."),
    _p("rochester-human-development-ms", _WARNER, "Master of Science in Human Development", "Human Development", "masters", 18,
       "Program in Human Development", "19.07",
       "The study of development across the lifespan, applying developmental science to education, counseling, and human-services settings.",
       "Students who want to apply developmental science to education and human services."),
    _p("rochester-applied-behavior-analysis-ms", _WARNER, "Master of Science in Applied Behavior Analysis", "Applied Behavior Analysis", "masters", 18,
       "Program in Human Development", "42.28",
       "Preparation for board certification in applied behavior analysis, combining behavioral science with supervised practice in educational and clinical settings.",
       "Students pursuing careers and certification in applied behavior analysis."),
    _p("rochester-teaching-curriculum-edd", _WARNER, "Doctor of Education in Teaching and Curriculum", "Teaching and Curriculum", "professional", 42,
       "Program in Teaching and Curriculum", "13.03",
       "A practitioner-focused, part-time doctorate with a field-based dissertation, designed so working educators can complete it in about three years.",
       "Working educators pursuing a practice doctorate in teaching and curriculum."),
    _p("rochester-teaching-curriculum-phd", _WARNER, "Doctor of Philosophy in Teaching and Curriculum", "Teaching and Curriculum", "phd", 60,
       "Program in Teaching and Curriculum", "13.03",
       "A research doctorate training education scholars in curriculum theory, pedagogy, and learning across subject areas.",
       "Aspiring education researchers focused on teaching, curriculum, and learning."),
    _p("rochester-higher-education-edd", _WARNER, "Doctor of Education in Higher Education", "Higher Education", "professional", 42,
       "Program in Educational Leadership", "13.04",
       "A practice doctorate for higher-education leaders, applying research to administration, policy, and institutional improvement.",
       "Higher-education professionals pursuing a leadership-focused practice doctorate."),
    _p("rochester-counseling-phd", _WARNER, "Doctor of Philosophy in Counseling", "Counseling", "phd", 60,
       "Program in Counseling and Human Development", "13.11",
       "A research doctorate in counselor education and supervision, training scholars and clinical supervisors.",
       "Aspiring counselor educators and researchers pursuing a doctorate."),
    _p("rochester-human-development-phd", _WARNER, "Doctor of Philosophy in Human Development", "Human Development", "phd", 60,
       "Program in Human Development", "19.07",
       "A research doctorate in developmental science, studying learning and development across educational and social contexts.",
       "Aspiring developmental-science researchers in education and human services."),

    # ══════════ School of Nursing ══════════
    _p("rochester-nursing-rn-bs", _SON, "Bachelor of Science in Nursing (RN to BS)", "Nursing", "bachelors", 24,
       "School of Nursing", "51.38",
       "An online bachelor's completion track for licensed RNs, building on prior clinical training with leadership, research, and community-health coursework.",
       "Licensed registered nurses completing a bachelor's degree online.",
       delivery_format="online"),
    _p("rochester-nursing-absn", _SON, "Bachelor of Science in Nursing (Accelerated)", "Nursing", "bachelors", 12,
       "School of Nursing", "51.38",
       "An accelerated second-degree bachelor's preparing college graduates for RN licensure through intensive coursework and clinical rotations.",
       "College graduates changing careers to become registered nurses."),
    _p("rochester-nursing-np-ms", _SON, "Master of Science in Nursing (Nurse Practitioner)", "Nurse Practitioner", "masters", 24,
       "School of Nursing", "51.38",
       "Advanced-practice preparation across nurse-practitioner specialties — family, adult-gerontology, pediatric, and psychiatric-mental-health tracks — for clinical leadership.",
       "Registered nurses pursuing advanced-practice careers as nurse practitioners.",
       delivery_format="hybrid",
       tracks=["Family", "Adult-Gerontology Acute Care", "Psychiatric-Mental Health", "Pediatric Primary Care", "Pediatric Acute Care"]),
    _p("rochester-nursing-cnl-ms", _SON, "Master of Science in Clinical Nurse Leader", "Clinical Nurse Leadership", "masters", 24,
       "School of Nursing", "51.38",
       "A master's preparing clinical nurse leaders to coordinate and improve care at the point of delivery across health systems.",
       "Nurses pursuing clinical-leadership roles improving care at the bedside.",
       delivery_format="hybrid"),
    _p("rochester-nursing-education-ms", _SON, "Master of Science in Nursing Education", "Nursing Education", "masters", 24,
       "School of Nursing", "51.38",
       "Preparation for careers teaching nursing in academic and clinical settings, combining advanced nursing knowledge with instructional science.",
       "Nurses who want to teach and lead in nursing education.",
       delivery_format="hybrid"),
    _p("rochester-nursing-leadership-ms", _SON, "Master of Science in Leadership in Health Care Systems", "Health Care Leadership", "masters", 24,
       "School of Nursing", "51.38",
       "A master's preparing nurses for administrative and systems-leadership roles across health-care organizations.",
       "Nurses moving into administrative and health-systems leadership.",
       delivery_format="hybrid"),
    _p("rochester-nursing-direct-entry-ms", _SON, "Master of Science (Master's Direct Entry to Nursing Practice)", "Nursing", "masters", 24,
       "School of Nursing", "51.38",
       "An accelerated pathway for non-nurse college graduates to earn RN licensure and a master's, integrating pre-licensure and advanced coursework.",
       "College graduates from other fields entering nursing at the master's level."),
    _p("rochester-nursing-dnp", _SON, "Doctor of Nursing Practice", "Nursing Practice", "professional", 36,
       "School of Nursing", "51.38",
       "A post-master's practice doctorate building on advanced-practice expertise to lead evidence-based improvement in clinical care and health systems.",
       "Advanced-practice nurses pursuing the highest clinical practice doctorate.",
       delivery_format="online"),
    _p("rochester-nursing-crna-dnp", _SON, "Doctor of Nursing Practice (Nurse Anesthesia)", "Nurse Anesthesia", "professional", 36,
       "School of Nursing", "51.38",
       "A practice doctorate preparing certified registered nurse anesthetists through advanced anesthesia science and extensive clinical residency.",
       "Registered nurses pursuing careers as certified registered nurse anesthetists."),
    _p("rochester-nursing-phd", _SON, "Doctor of Philosophy in Nursing and Health Science", "Nursing Science", "phd", 60,
       "School of Nursing", "51.38",
       "A research doctorate training nurse-scientists through mentored study of health, illness, and care, with post-master's and post-baccalaureate entry pathways.",
       "Aspiring nurse-scientists pursuing research careers in health and nursing science.",
       delivery_format="hybrid"),

    # ══════════ School of Medicine and Dentistry ══════════
    _p("rochester-md", _SMD, "Doctor of Medicine", "Medicine", "professional", 48,
       "School of Medicine and Dentistry", "51.12",
       "The M.D. program built on Rochester's biopsychosocial model and 'double-helix' curriculum, integrating basic and clinical science from the first year within the University of Rochester Medical Center.",
       "Aspiring physicians drawn to Rochester's integrated basic-and-clinical curriculum and biopsychosocial model."),
    _p("rochester-biochemistry-phd", _SMD, "Doctor of Philosophy in Biochemistry", "Biochemistry", "phd", 60,
       "Department of Biochemistry and Biophysics", "26.02",
       "Doctoral research in the molecular mechanisms of life — protein structure, enzymology, and gene regulation — within the biomedical-science graduate programs.",
       "Aspiring biomedical researchers focused on the molecular basis of biological processes."),
    _p("rochester-biophysics-phd", _SMD, "Doctor of Philosophy in Biophysics", "Biophysics", "phd", 60,
       "Department of Biochemistry and Biophysics", "26.02",
       "Doctoral research on structural, computational, and physical approaches to biology, from macromolecular structure to biological modeling.",
       "Aspiring researchers applying physics and computation to biological systems."),
    _p("rochester-genetics-phd", _SMD, "Doctor of Philosophy in Genetics", "Genetics", "phd", 60,
       "Department of Biomedical Genetics", "26.08",
       "Doctoral research in genetics, genomics, development, and stem-cell biology, studying how genes shape health and disease.",
       "Aspiring geneticists studying genomes, development, and disease."),
    _p("rochester-microbiology-immunology-phd", _SMD, "Doctor of Philosophy in Microbiology and Immunology", "Microbiology and Immunology", "phd", 60,
       "Department of Microbiology and Immunology", "26.05",
       "Doctoral research on immunity, microbes, and virology — host defense, infection, and vaccine science.",
       "Aspiring researchers in immunology, microbiology, and virology."),
    _p("rochester-neuroscience-phd", _SMD, "Doctor of Philosophy in Neuroscience", "Neuroscience", "phd", 60,
       "Department of Neuroscience", "26.15",
       "Doctoral research across molecular, cellular, systems, and cognitive neuroscience, anchored by the Del Monte Institute for Neuroscience.",
       "Aspiring neuroscientists studying the brain from molecules to cognition."),
    _p("rochester-pharmacology-physiology-phd", _SMD, "Doctor of Philosophy in Pharmacology and Physiology", "Pharmacology and Physiology", "phd", 60,
       "Department of Pharmacology and Physiology", "26.10",
       "Doctoral research on how drugs and physiological systems act at the cellular and molecular level, spanning signaling, receptors, and organ function.",
       "Aspiring researchers in cellular and molecular pharmacology and physiology."),
    _p("rochester-pathology-phd", _SMD, "Doctor of Philosophy in Pathology", "Pathology", "phd", 60,
       "Department of Pathology and Laboratory Medicine", "26.09",
       "Doctoral research on the mechanisms of disease at the cellular and molecular level, bridging basic science and clinical pathology.",
       "Aspiring researchers studying the mechanisms of human disease."),
    _p("rochester-toxicology-phd", _SMD, "Doctor of Philosophy in Toxicology", "Toxicology", "phd", 60,
       "Department of Environmental Medicine", "26.10",
       "Doctoral research on how environmental agents affect biological systems and health, from molecular toxicology to environmental health.",
       "Aspiring researchers studying environmental agents and their effects on health."),
    _p("rochester-translational-biomedical-phd", _SMD, "Doctor of Philosophy in Translational Biomedical Science", "Translational Biomedical Science", "phd", 60,
       "School of Medicine and Dentistry", "51.14",
       "Doctoral research bridging laboratory discovery and clinical application, training scientists to move findings toward patient care.",
       "Aspiring researchers who want to translate laboratory discovery into clinical impact."),
    _p("rochester-epidemiology-phd", _SMD, "Doctor of Philosophy in Epidemiology", "Epidemiology", "phd", 60,
       "Department of Public Health Sciences", "51.22",
       "Doctoral research on the distribution and determinants of disease in populations, combining study design and advanced biostatistics.",
       "Aspiring epidemiologists pursuing population-health research."),
    _p("rochester-health-services-research-phd", _SMD, "Doctor of Philosophy in Health Services Research and Policy", "Health Services Research", "phd", 60,
       "Department of Public Health Sciences", "51.22",
       "Doctoral research on how health care is organized, financed, and delivered, and how policy shapes access, cost, and quality.",
       "Aspiring researchers studying health systems, policy, and outcomes."),
    _p("rochester-mph", _SMD, "Master of Public Health", "Public Health", "masters", 24,
       "Department of Public Health Sciences", "51.22",
       "A CEPH-accredited public-health master's covering epidemiology, biostatistics, and health policy, offered with online and hybrid options.",
       "Students pursuing careers in public health, epidemiology, and health policy.",
       delivery_format="hybrid"),
    _p("rochester-biostatistics-ms", _SMD, "Master of Science in Biostatistics", "Biostatistics", "masters", 18,
       "Department of Biostatistics and Computational Biology", "27.05",
       "A master's in the statistical methods of biomedical research — study design, survival analysis, and clinical-trial statistics.",
       "Graduates who want to apply statistics to biomedical and clinical research."),
    _p("rochester-clinical-investigation-ms", _SMD, "Master of Science in Clinical Investigation", "Clinical Investigation", "masters", 18,
       "Clinical and Translational Science Institute", "51.14",
       "Training clinicians and scientists in the methods of patient-oriented research, from trial design to translational study conduct.",
       "Clinicians and scientists building skills in patient-oriented clinical research."),
    _p("rochester-medical-humanities-ms", _SMD, "Master of Science in Medical Humanities", "Medical Humanities", "masters", 18,
       "Division of Medical Humanities and Bioethics", "51.32",
       "The study of medicine through the humanities and bioethics — narrative, history, and ethics — for clinicians and scholars.",
       "Clinicians and scholars who want to study medicine through the humanities and ethics."),
    _p("rochester-genetic-counseling-ms", _SMD, "Master of Science in Genetic Counseling", "Genetic Counseling", "masters", 21,
       "School of Medicine and Dentistry", "51.15",
       "An accredited 21-month program training genetic counselors through core clinical rotations in prenatal, pediatric, and cancer genetics.",
       "Students pursuing certification and careers as genetic counselors."),
    _p("rochester-marriage-family-therapy-ms", _SMD, "Master of Science in Marriage and Family Therapy", "Marriage and Family Therapy", "masters", 24,
       "Department of Psychiatry", "51.15",
       "A licensure-track master's in systemic couple and family therapy, integrating clinical training with supervised practice.",
       "Students pursuing licensure as marriage and family therapists."),
    _p("rochester-dental-sciences-ms", _SMD, "Master of Science in Dental Sciences", "Dental Sciences", "masters", 24,
       "Eastman Institute for Oral Health", "51.05",
       "A research master's through the Eastman Institute for Oral Health, often taken concurrently with advanced dental residency training.",
       "Dentists and researchers pursuing advanced study in oral-health science."),
]

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]


def _tuition_omit_reason(spec: dict) -> str:
    school = spec["school"]
    if spec["degree_type"] == "certificate":
        return _TUITION_OMIT_CERT
    if school == _SON:
        return _TUITION_OMIT_NURSING
    if school == _EASTMAN:
        return _TUITION_OMIT_EASTMAN
    if school == _WARNER:
        return _TUITION_OMIT_WARNER
    if school == _SIMON:
        return _TUITION_OMIT_SIMON
    return _TUITION_OMIT_CERT


def _resolve_tuition(spec: dict) -> int | None:
    if "tuition" in spec:
        return spec["tuition"]
    slug = spec["slug"]
    dt = spec["degree_type"]
    school = spec["school"]
    if slug in _SIMON_TUITION:
        return _SIMON_TUITION[slug]
    if dt == "phd":
        return 0  # funded research doctorate (tuition waived)
    if slug == "rochester-md":
        return _TUITION_MD
    if dt == "bachelors":
        if school == _SON:
            return None  # nursing accelerated/completion billed per-credit → omit
        return _TUITION_UG
    # Academic master's at the verified AS&E per-credit rate: A&S, Hajim, SMD.
    if dt == "masters" and school in (_ASE, _HAJIM, _SMD):
        return _ase_grad_cost(spec)["tuition_usd"]
    return None  # Eastman / Warner / Nursing grad, Simon-specialized, DBA → omit-with-reason


def _cost_data(spec: dict) -> dict:
    slug = spec["slug"]
    dt = spec["degree_type"]
    school = spec["school"]
    if slug in _SIMON_TUITION:
        return {
            "tuition_usd": _SIMON_TUITION[slug],
            "funded": False,
            "source": "Simon Business School — tuition & financial aid (2026-27)",
            "source_url": _SIMON_TUITION_SRC,
            "year": "2026-27",
        }
    if slug == "rochester-md":
        return {
            "tuition_usd": _TUITION_MD,
            "funded": False,
            "source": "University of Rochester School of Medicine and Dentistry (M.D. tuition, 2025-26)",
            "source_url": _TUITION_MD_SRC,
            "year": "2025-26",
        }
    if dt == "phd":
        return {
            "tuition_usd": 0,
            "funded": True,
            "note": "Research doctorates at the University of Rochester are funded (tuition waived) with a stipend for admitted students.",
            "source": "University of Rochester Graduate Education",
            "source_url": _ASE_TUITION_SRC,
            "year": "2026-27",
        }
    if dt == "bachelors" and school != _SON:
        return {
            "tuition_usd": _TUITION_UG,
            "funded": False,
            "source": "U.S. Dept. of Education College Scorecard (published undergraduate tuition, UNITID 195030)",
            "source_url": _TUITION_UG_SRC,
            "year": "2024-25",
        }
    if dt == "masters" and school in (_ASE, _HAJIM, _SMD):
        return _ase_grad_cost(spec)
    return {"tuition_usd": None, "omitted_reason": _tuition_omit_reason(spec)}


def _has_tuition(spec: dict) -> bool:
    return _resolve_tuition(spec) is not None or spec["degree_type"] == "phd"


def _requirements_for(spec: dict) -> dict:
    if spec["school"] == _EASTMAN:
        return dict(_REQ_MUSIC)
    if spec["slug"] == "rochester-md":
        return dict(_REQ_MD)
    if spec["degree_type"] == "bachelors":
        return dict(_REQ_UNDERGRAD)
    return dict(_REQ_GRAD)


def _program_standard(spec: dict) -> dict:
    omitted: list[str] = ["outcomes_data.employment_rate", "outcomes_data.top_industries"]
    if "tracks" not in spec:
        omitted.append("tracks")
    omitted += ["class_profile.cohort_size", "faculty_contacts.lead"]
    if spec["slug"] not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    if not _has_tuition(spec):
        omitted += ["cost_data.tuition_usd", "cost_data.source"]
    return _standard(omitted)


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich the University of Rochester to the canonical profile. Flushes; caller commits.

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
    # Lead media_gallery with the verified hero campus photo (the seed's gallery),
    # preserving existing entries behind it (idempotent dedupe).
    photos = (inst.school_outcomes or {}).get("campus_photos") or []
    hero = photos[0]["url"] if photos and isinstance(photos[0], dict) else (inst.media_gallery or [None])[0]
    if hero:
        rest = [u for u in (inst.media_gallery or []) if u != hero]
        inst.media_gallery = [hero, *rest]
    inst.content_sources = dict(_INSTITUTION_CONTENT)
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
        sc.content_sources = _school_content(spec["name"])
        about = dict(_SCHOOL_ABOUT[spec["name"]])
        about["_standard"] = _standard(_ABOUT_OMITTED.get(spec["name"], []))
        sc.about_detail = about
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
        p = existing.get(spec["slug"])
        if p is None:
            p = Program(
                institution_id=inst.id,
                program_name=spec["program_name"],
                degree_type=spec["degree_type"],
                slug=spec["slug"],
            )
            session.add(p)
        p.program_name = spec["program_name"]
        p.degree_type = spec["degree_type"]
        p.duration_months = spec.get("duration_months")
        p.description_text = spec["description"]
        p.website_url = spec.get("website") or _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.department = spec.get("department")
        p.is_published = True
        p.catalog_source = "curated"
        p.content_sources = _program_content(spec)
        p.delivery_format = spec.get("delivery_format", "in_person")
        p.tuition = _resolve_tuition(spec)
        p.cost_data = _cost_data(spec)
        p.application_requirements = _requirements_for(spec)
        fos = _FOS_OUTCOMES.get(spec["slug"])
        if fos is not None:
            salary, cip = fos
            p.outcomes_data = {
                "median_salary": salary,
                "scope": "program",
                "cip": cip,
                "source": "U.S. Dept. of Education College Scorecard — Field of Study",
                "source_url": "https://collegescorecard.ed.gov/school/?195030",
            }
        else:
            p.outcomes_data = dict(_OUTCOMES_INSTITUTION)
        p.outcomes_data["_standard"] = _program_standard(spec)
        p.cip_code = spec["cip"]
        p.who_its_for = spec["who"]
        p.tracks = spec.get("tracks")
        p.class_profile = None
        p.faculty_contacts = None
        p.external_reviews = _REVIEWS_BY_SLUG.get(spec["slug"])
        if spec["degree_type"] == "bachelors":
            p.application_deadline = date(2027, 1, 5)
        else:
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
