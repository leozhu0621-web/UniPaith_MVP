"""Case Western Reserve University — canonical profile enrichment (institution → schools → programs).

Takes the bulk-seeded Case Western Reserve institution stub (0 programs, dead feed) to
the gold standard: the institution's verified report-card + admissions funnel +
outcomes, its eight degree-granting schools with sourced About-tab content and working
Events & Updates feeds, and its full real degree catalog (every program a real,
distinctly-named conferred degree with a field-specific description, matcher-core
``cip_code`` + ``tuition`` + program-distinct ``who_its_for``, and a populated feed).
``apply(session)`` idempotently upserts; the caller owns the transaction. It is a
**no-op** (returns False) when Case Western Reserve is absent — safe on fresh/CI databases.

Sourcing (verified 2026-07-02, cited in ``SCHOOL_OUTCOMES['sources']``):
- Costs, net price, outcomes, test scores, demographics, retention/completion:
  U.S. Dept. of Education College Scorecard (UNITID 201645).
- The full CIP-coded degree list that anchors catalog BREADTH: the College
  Scorecard Field-of-Study file for 201645 — each CIP RESOLVED to CWRU's real
  published degree name + owning department from the CWRU General Bulletin
  (bulletin.case.edu) and each school's official program pages (never the federal
  CIP title verbatim).
- Admissions funnel (Class of 2028 / Fall 2024 entering class): CWRU Common Data
  Set 2024-25, Section C1 (37,082 applicants; 14,010 admitted; 1,619 enrolled).
- Tuition: CWRU Student Financial Services. Undergraduate $68,660 (2025-26). Research
  doctorates are funded (0). CWRU bills most academic master's/doctoral programs
  through the School of Graduate Studies at $2,316/credit with a $27,774/term
  full-time maximum, so the full-time academic-year matcher scalar is $55,548
  ($27,774 x 2). Professional and named-school programs carry their own published
  rates: M.D. (University Program) $72,526; the Cleveland Clinic Lerner College of
  Medicine M.D. is FREE (full-tuition scholarship for all matriculants, so tuition = 0);
  D.M.D. $89,668; J.D. $64,600; M.S.W. $49,500 (full-time). Weatherhead and named-school
  per-credit programs (MBA $1,661/cr, MAcc $1,648/cr, MFin $1,974/cr, MSCM $1,754/cr,
  MSN $2,377/cr, DNP $2,497/cr, MNO $1,650/cr, LL.M. $2,692/cr, MSA $2,149/cr, Genetic
  Counseling $2,384/cr) carry the annualized full-time cost (per-credit x 24-credit
  full-time academic year), documented per program in ``cost_data``.
- Feeds: CWRU's official Newsroom RSS (case.edu/news/rss.xml) and the official
  University Events Calendar iCal — both verified live to return current items — populate
  Events & Updates on every node.

Honest caveats stamped into ``_standard.omitted``:
- Case Western Reserve is not individually ranked at a value verifiable to two
  independent sources in the QS and Times Higher Education world tables for this
  cycle, so those two ranking fields are omitted with reason; the U.S. News national
  rank (#51, 2026) is kept.
- CWRU does not publish a single university-wide "employed or continuing education"
  placement rate across all schools, so that institution outcome field is omitted with
  reason (the College Scorecard institution-wide ten-year median earnings, $87,989, and
  the Center for Career Success first-destination top industries are both kept).
- Each school's current dean and named faculty are not re-verified per school at author
  time, so ``about_detail.leadership`` and ``about_detail.faculty`` are omitted with
  reason; each school's founding year and — where verified — its research centers are kept.
- A handful of graduate/professional programs whose per-program tuition CWRU does not
  publish in a verifiable form (the six postdoctoral M.S.D. dental specialties, the
  Physician Assistant M.S. published only as a program-year tuition-and-fees figure,
  the Weatherhead MBAI and MSLOC, and the specialized School of Law non-J.D./LL.M.
  master's) keep an honest ``cost_data`` tuition omission rather than a guessed figure.
- Deeper per-program fields (tracks, class profile, named faculty, review themes) are
  published only for a few programs; the rest are honestly omitted, never guessed — the
  same breadth-first pattern as the MIT gold reference. ``external_reviews`` (MBAn shape,
  gathered → summarized → cited, each backed by >= 2 independent third-party domains) are
  attached to the programs with genuine independent coverage; programs whose only signal
  is first-party pages or a single ranking domain record an honest ``external_reviews``
  omission (coverage-gated).
"""

# ruff: noqa: E501

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Case Western Reserve University"
ENRICHED_AT = "2026-07-02"


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


# CWRU publishes ten-year median earnings + a first-destination top-industries list
# (both kept) but no single university-wide "employed or continuing education"
# placement percentage across all schools; QS/THE per-cycle ranks are not
# two-source-verifiable → omitted with reason (U.S. News national rank kept).
_OMITTED_INSTITUTION: list[str] = [
    "school_outcomes.employed_or_continuing_ed",
    "ranking_data.qs_world_university_rankings",
    "ranking_data.times_higher_education",
]

# ── Institution-level data ────────────────────────────────────────────────
RANKING_DATA: dict = {
    "ownership_type": "private_nonprofit",
    "accreditor": "Higher Learning Commission (HLC)",
    "carnegie_classification": "Doctoral Universities: Very High Research Activity (R1)",
    # U.S. News Best National Universities 2026 (#51, held from 2025).
    "us_news_national": {"rank": 51, "year": 2026},
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below
# is complete. campus_photos is intentionally OMITTED here so the seed's five
# verified, credited Wikimedia photos are preserved.
SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.378,
    "avg_net_price": 41190,
    "median_earnings_10yr": 87989,
    "completion_rate_4yr_150pct": 0.8717,
    "graduation_rate_6yr": 0.87,
    "retention_rate_first_year": 0.9207,
    "test_scores": {
        # College Scorecard SAT section 25th-75th (reading 700-760, math 730-780) →
        # composite band; ACT composite 25th-75th 32-34.
        "sat_composite_25_75": [1430, 1540],
        "act_25_75": [32, 34],
        "sat_reading_midpoint": 730,
        "sat_math_midpoint": 755,
    },
    "financial_aid": {
        "pell_grant_rate": 0.1752,
        "cost_of_attendance": 85851,
        "avg_net_price": 41190,
    },
    "demographics": {
        "white": 0.3357,
        "black": 0.0626,
        "hispanic": 0.1164,
        "asian": 0.3048,
    },
    "location": {"lat": 41.5043, "lng": -81.6084},
    # CWRU Center for Career Success first-destination survey — the industries most
    # graduates enter (a published list, not a single placement percentage).
    "top_employer_industries": [
        "Engineering",
        "Research & Science",
        "Nursing",
        "Healthcare",
        "Information Technology",
        "Financial Services",
    ],
    "scale": {
        "faculty_count": 1075,
        "student_faculty_ratio": "9:1",
    },
    "research": {
        "areas": [
            "Cancer & oncology",
            "Regenerative medicine & stem cells",
            "Neuroscience & glial biology",
            "Energy & sustainability",
            "Materials & polymer science",
            "Immersive & human-machine technology",
        ],
        "centers": [
            {"name": "Case Comprehensive Cancer Center (NCI-designated)", "url": "https://case.edu/cancer/"},
            {"name": "National Center for Regenerative Medicine", "url": "https://case.edu/medicine/ncrm/"},
            {"name": "Institute for Glial Sciences", "url": "https://case.edu/medicine/glialsciences/"},
            {"name": "Great Lakes Energy Institute", "url": "https://engineering.case.edu/research/institutes/great-lakes-energy"},
            {"name": "Institute for Smart, Secure and Connected Systems (ISSACS)", "url": "https://case.edu/issacs/"},
            {"name": "Interactive Commons (HoloAnatomy)", "url": "https://interactivecommons.org/"},
        ],
    },
    "campus_life": {
        "athletics_division": "NCAA Division III — University Athletic Association (UAA)",
        "mascot": "Spartans",
        "varsity_sports": 19,
        "religious_affiliation": "Nonsectarian",
        "resources": [
            {"label": "CWRU Athletics", "url": "https://athletics.case.edu/"},
            {"label": "Student Life", "url": "https://case.edu/studentlife/"},
            {"label": "University Circle", "url": "https://www.universitycircle.org/"},
        ],
    },
    "campus_basics": {
        "location": "Cleveland, Ohio",
        "academic_calendar": "Semester (fall / spring)",
    },
    "flagship": {
        "admissions_cycle": "Class of 2028",
        "applicants": 37082,
        "admits": 14010,
        "enrolled": 1619,
    },
    "sources": [
        {
            "label": "Costs, net price, outcomes, test scores, demographics, retention/completion",
            "source": "U.S. Dept. of Education College Scorecard (UNITID 201645)",
            "year": 2024,
            "url": "https://collegescorecard.ed.gov/school/?201645-Case-Western-Reserve-University",
        },
        {
            "label": "Full CIP-coded degree list (catalog breadth cross-check)",
            "source": "College Scorecard Field of Study — Case Western Reserve University",
            "year": 2024,
            "url": "https://collegescorecard.ed.gov/school/?201645-Case-Western-Reserve-University",
        },
        {
            "label": "First-year admission funnel (Class of 2028)",
            "source": "Case Western Reserve University Common Data Set 2024-25 (Section C1)",
            "year": 2024,
            "url": "https://case.edu/ir/sites/default/files/2025-05/CWRU%202024%20-%2025%20CDS%20ADJ.pdf",
        },
        {
            "label": "National ranking",
            "source": "U.S. News Best National Universities",
            "year": 2026,
            "url": "https://www.usnews.com/best-colleges/case-western-reserve-university-3024",
        },
        {
            "label": "Graduate first-destination industries",
            "source": "CWRU Center for Career Success — First Destination Survey",
            "year": 2024,
            "url": "https://case.edu/studentlife/careercenter/about/outcomes-and-data/first-destination-survey",
        },
        {
            "label": "Schools, programs, and degree names",
            "source": "Case Western Reserve University General Bulletin",
            "year": 2025,
            "url": "https://bulletin.case.edu/academic-programs/",
        },
        {
            "label": "Tuition & fees",
            "source": "CWRU Student Financial Services",
            "year": 2025,
            "url": "https://case.edu/studentaccounts/tuition-fees",
        },
    ],
}

# student_body_size renders as "Undergraduates". CWRU's total enrollment (~12,400) is
# larger; the undergraduate figure is the labelled value (CWRU Institutional Research,
# Fall 2025).
UNDERGRAD_COUNT = 6534

DESCRIPTION = (
    "Case Western Reserve University is a private research university in Cleveland, "
    "Ohio, at the heart of University Circle — a dense cluster of museums, hospitals, "
    "and cultural institutions on the city's east side. It was formed in 1967 by the "
    "federation of two neighboring institutions: Western Reserve College, founded in "
    "1826, and the Case School of Applied Science, founded in 1880 — a union that still "
    "shapes CWRU's identity as a place where the liberal arts and rigorous science and "
    "engineering meet.\n\n"
    "The university is organized into eight degree-granting schools: the College of "
    "Arts and Sciences; the Case School of Engineering; the Weatherhead School of "
    "Management; the School of Medicine (including the Cleveland Clinic Lerner College "
    "of Medicine); the Frances Payne Bolton School of Nursing; the School of Dental "
    "Medicine; the School of Law; and the Jack, Joseph and Morton Mandel School of "
    "Applied Social Sciences. About 6,500 undergraduates and 5,900 graduate and "
    "professional students study across these units.\n\n"
    "Case Western Reserve is a selective, R1 very-high-research university — it admitted "
    "about 38% of the roughly 37,000 applicants to its Class of 2028 — and ranks No. 51 "
    "among national universities in the U.S. News list. Its students graduate at a high "
    "rate (an 87% six-year graduation rate and a 92% first-year retention rate) and earn "
    "a median income of roughly $88,000 a decade after entry.\n\n"
    "CWRU is defined by its research depth and its ties to neighboring institutions — "
    "the Cleveland Clinic, University Hospitals, the Cleveland Museum of Art, and the "
    "Cleveland Orchestra among them — anchoring nationally recognized strength in "
    "biomedical engineering, medicine and nursing, materials and polymer science, and "
    "the applied social sciences, and giving undergraduates unusual access to research "
    "and clinical experience."
)

# ── The eight degree-granting schools (display order) ──────────────────────
_CAS = "College of Arts and Sciences"
_ENGR = "Case School of Engineering"
_WEA = "Weatherhead School of Management"
_MED = "School of Medicine"
_NURS = "Frances Payne Bolton School of Nursing"
_DENT = "School of Dental Medicine"
_LAW = "School of Law"
_MANDEL = "Jack, Joseph and Morton Mandel School of Applied Social Sciences"

SCHOOLS: list[dict] = [
    {
        "name": _CAS,
        "sort_order": 1,
        "description": (
            "The College of Arts and Sciences is CWRU's largest school, spanning the "
            "humanities, natural sciences, social sciences, and the arts from the "
            "undergraduate liberal-arts core through master's and Ph.D. programs. It "
            "carries the heritage of Western Reserve College and anchors the "
            "university's broad research and teaching mission."
        ),
    },
    {
        "name": _ENGR,
        "sort_order": 2,
        "description": (
            "The Case School of Engineering traces its lineage to the Case School of "
            "Applied Science (1880) and educates engineers and applied scientists across "
            "biomedical, computer, materials, mechanical, chemical, and systems "
            "engineering — with particular strength in biomedical engineering, polymers "
            "and materials, energy, and data science."
        ),
    },
    {
        "name": _WEA,
        "sort_order": 3,
        "description": (
            "The Weatherhead School of Management educates business leaders across "
            "accounting, finance, marketing, operations, and organizational behavior — "
            "from undergraduate management degrees through the MBA, specialized master's, "
            "and research doctorates — and is known for its work in design, innovation, "
            "and positive organizational development."
        ),
    },
    {
        "name": _MED,
        "sort_order": 4,
        "description": (
            "The School of Medicine educates physicians and biomedical scientists through "
            "the M.D. (in both the University Program and the research-intensive Cleveland "
            "Clinic Lerner College of Medicine), the M.D./Ph.D. Medical Scientist Training "
            "Program, and a broad range of biomedical M.S. and Ph.D. programs and public "
            "health and health-professions degrees, in close partnership with Cleveland's "
            "major teaching hospitals."
        ),
    },
    {
        "name": _NURS,
        "sort_order": 5,
        "description": (
            "The Frances Payne Bolton School of Nursing, among the nation's leading "
            "nursing schools, educates nurses and nurse scientists from the Bachelor of "
            "Science in Nursing through advanced-practice master's, the Doctor of Nursing "
            "Practice, and a research Ph.D. — pairing clinical rigor with a strong "
            "tradition of nursing science."
        ),
    },
    {
        "name": _DENT,
        "sort_order": 6,
        "description": (
            "The School of Dental Medicine, the dental school of CWRU, educates general "
            "dentists through the Doctor of Dental Medicine and trains specialists through "
            "advanced M.S.D. programs in endodontics, oral and maxillofacial surgery, oral "
            "medicine, orthodontics, pediatric dentistry, and periodontics."
        ),
    },
    {
        "name": _LAW,
        "sort_order": 7,
        "description": (
            "Case Western Reserve University School of Law educates lawyers through the "
            "Juris Doctor and offers advanced and specialized law degrees — the LL.M., the "
            "research S.J.D., and professional master's in areas such as compliance and "
            "risk management, financial integrity, and patent practice — with noted "
            "strengths in health law, international law, and intellectual property."
        ),
    },
    {
        "name": _MANDEL,
        "sort_order": 8,
        "description": (
            "The Jack, Joseph and Morton Mandel School of Applied Social Sciences, founded "
            "in 1915, is one of the oldest schools of social work in the country. It "
            "educates social workers and nonprofit leaders through the Master of Social "
            "Work, the Master of Nonprofit Organizations, and a research doctorate in "
            "social welfare."
        ),
    },
]

_SCHOOL_WEBSITE: dict[str, str] = {
    _CAS: "https://case.edu/artsci/",
    _ENGR: "https://engineering.case.edu/",
    _WEA: "https://weatherhead.case.edu/",
    _MED: "https://case.edu/medicine/",
    _NURS: "https://case.edu/nursing/",
    _DENT: "https://case.edu/dental/",
    _LAW: "https://case.edu/law/",
    _MANDEL: "https://case.edu/socialwork/",
}

# Founding years are verified from CWRU's history pages; research centers are real,
# URL-verified CWRU units housed in each school. Current deans and named faculty are not
# re-verified per school at author time, so they are honestly omitted (in _ABOUT_OMITTED).
_SCHOOL_ABOUT: dict[str, dict] = {
    _CAS: {
        "founded": 1826,
        "research_centers": [],
        "source": {"label": "College of Arts and Sciences", "url": "https://case.edu/artsci/"},
    },
    _ENGR: {
        "founded": 1880,
        "research_centers": [
            "Great Lakes Energy Institute",
            "Institute for Smart, Secure and Connected Systems (ISSACS)",
        ],
        "source": {"label": "Case School of Engineering", "url": "https://engineering.case.edu/"},
    },
    _WEA: {
        "founded": 1952,
        "research_centers": [],
        "source": {"label": "Weatherhead School of Management", "url": "https://weatherhead.case.edu/"},
    },
    _MED: {
        "founded": 1843,
        "research_centers": [
            "Case Comprehensive Cancer Center",
            "National Center for Regenerative Medicine",
            "Institute for Glial Sciences",
        ],
        "source": {"label": "School of Medicine", "url": "https://case.edu/medicine/"},
    },
    _NURS: {
        "founded": 1923,
        "research_centers": [],
        "source": {"label": "Frances Payne Bolton School of Nursing", "url": "https://case.edu/nursing/"},
    },
    _DENT: {
        "founded": 1892,
        "research_centers": [],
        "source": {"label": "School of Dental Medicine", "url": "https://case.edu/dental/"},
    },
    _LAW: {
        "founded": 1892,
        "research_centers": [],
        "source": {"label": "Case Western Reserve University School of Law", "url": "https://case.edu/law/"},
    },
    _MANDEL: {
        "founded": 1915,
        "research_centers": [],
        "source": {"label": "Jack, Joseph and Morton Mandel School of Applied Social Sciences", "url": "https://case.edu/socialwork/"},
    },
}
_ABOUT_OMITTED: dict[str, list[str]] = {
    name: ["about_detail.leadership", "about_detail.faculty"]
    + (["about_detail.research_centers"] if not about.get("research_centers") else [])
    for name, about in _SCHOOL_ABOUT.items()
}

# ── Channel feeds (CWRU's official Newsroom RSS + University Events Calendar) ──
# Both verified live (2026-07-02) to return current items. Schools/programs filter the
# shared feed by keywords naming the unit (the MIT/MBAn pattern).
_CWRU_NEWS_RSS = "https://case.edu/news/rss.xml"
_CWRU_EVENTS_ICS = {
    "url": "http://www.google.com/calendar/ical/case.edu_gupalc7urm7b82taup5h7vge9s@group.calendar.google.com/public/basic.ics",
    "type": "ical",
}
_SOCIAL_CWRU = {
    "instagram": "https://www.instagram.com/cwru/",
    "linkedin": "https://www.linkedin.com/school/case-western-reserve-university/",
    "x": "https://x.com/cwru",
    "youtube": "https://www.youtube.com/case",
    "facebook": "https://www.facebook.com/casewesternreserve",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _CWRU_NEWS_RSS,
    "events_feed": dict(_CWRU_EVENTS_ICS),
    "social": dict(_SOCIAL_CWRU),
}

_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _CAS: ["arts and sciences", "College of Arts", "humanities", "sciences"],
    _ENGR: ["Case School of Engineering", "engineering", "computer", "materials"],
    _WEA: ["Weatherhead", "management", "business", "MBA"],
    _MED: ["School of Medicine", "medicine", "biomedical", "health"],
    _NURS: ["Bolton", "nursing", "nurse", "health"],
    _DENT: ["Dental Medicine", "dental", "dentistry"],
    _LAW: ["School of Law", "law", "legal"],
    _MANDEL: ["Mandel School", "social work", "nonprofit"],
}
_KW_STOP = {"and", "of", "the", "in", "for", "with", "science", "sciences", "master", "bachelor", "doctor", "arts", "engineering"}


def _school_content(name: str) -> dict:
    return {
        "news_rss": _CWRU_NEWS_RSS,
        "news_curated": False,
        "events_feed": dict(_CWRU_EVENTS_ICS),
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": dict(_SOCIAL_CWRU),
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
        "CWRU supplemental essay",
        "School report + counselor recommendation",
        "One teacher evaluation",
        "Official transcript",
    ],
    "deadlines": {"early_action": "Nov 1", "early_decision_i": "Nov 1", "early_decision_ii": "Jan 15", "regular_decision": "Jan 15"},
    "test_policy": "Test-optional",
    "source": "Case Western Reserve University Undergraduate Admission",
    "source_url": "https://case.edu/admission/apply",
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
    "source": "Case Western Reserve University School of Graduate Studies",
    "source_url": "https://case.edu/gradstudies/",
}
_REQ_LAW = {
    "materials": [
        "LSAC application (CAS report)",
        "Personal statement",
        "LSAT or GRE score",
        "Letters of recommendation",
        "Résumé",
    ],
    "deadlines": {"priority": "Mar 1"},
    "source": "Case Western Reserve University School of Law Admissions",
    "source_url": "https://case.edu/law/admissions",
}
_REQ_MED = {
    "materials": [
        "AMCAS application + CWRU secondary",
        "MCAT score",
        "Letters of recommendation / committee letter",
        "Official transcripts",
        "Clinical and research experience",
    ],
    "deadlines": {"note": "AMCAS deadlines apply — verify on the School of Medicine admissions page."},
    "source": "Case Western Reserve University School of Medicine Admissions",
    "source_url": "https://case.edu/medicine/admissions",
}
_REQ_DENTAL = {
    "materials": [
        "AADSAS application (ADEA centralized dental application)",
        "Dental Admission Test (DAT) score",
        "Official transcripts + prerequisite coursework",
        "Letters of recommendation",
        "Interview (by invitation)",
    ],
    "deadlines": {"note": "AADSAS operates on a rolling cycle — verify current dates on the School of Dental Medicine admissions page."},
    "source": "Case Western Reserve University School of Dental Medicine Admissions",
    "source_url": "https://case.edu/dental/admissions",
}
_REQ_PA = {
    "materials": [
        "CASPA application (centralized PA-program application)",
        "Prerequisite coursework",
        "Patient-care / health-care experience hours",
        "Letters of recommendation",
        "Official transcripts",
    ],
    "deadlines": {"note": "CASPA deadlines apply — verify on the Physician Assistant program admissions page."},
    "source": "Case Western Reserve University Physician Assistant Program",
    "source_url": "https://case.edu/medicine/pa",
}

# Institution-wide outcome proxy (College Scorecard, all-graduates) used where a
# program has no separately published employment report.
_OUTCOMES_INSTITUTION = {
    "median_salary": 87989,
    "scope": "institution",
    "employment_rate": None,
    "top_industries": ["Engineering", "Research & Science", "Healthcare", "Information Technology", "Financial Services"],
    "conditions": "Institution-wide College Scorecard median earnings 10 years after entry (all graduates).",
    "source": "U.S. Dept. of Education College Scorecard",
    "source_url": "https://collegescorecard.ed.gov/school/?201645-Case-Western-Reserve-University",
}

# College Scorecard Field-of-Study median earnings (2 yrs after completion), by slug,
# for programs where a real field-level figure is published. {salary, cip}.
_FOS_OUTCOMES: dict[str, tuple[int, str]] = {
    "cwru-computer-science-bs": (71575, "11.07"),
    "cwru-aerospace-engineering-bse": (63501, "14.02"),
    "cwru-biomedical-engineering-bse": (63997, "14.05"),
    "cwru-chemical-engineering-bse": (66325, "14.07"),
    "cwru-civil-engineering-bse": (61814, "14.08"),
    "cwru-electrical-engineering-bse": (68219, "14.10"),
    "cwru-mechanical-engineering-bse": (69854, "14.19"),
    "cwru-english-ba": (38289, "23.01"),
    "cwru-biochemistry-bs": (25053, "26.02"),
    "cwru-psychology-ba": (22192, "42.01"),
    "cwru-anthropology-ba": (27476, "45.02"),
    "cwru-economics-ba": (38289, "45.06"),
    "cwru-political-science-ba": (29685, "45.10"),
    "cwru-nursing-bsn": (60045, "51.38"),
    "cwru-accounting-bs": (54661, "52.03"),
    "cwru-finance-bsm": (57318, "52.08"),
    "cwru-finance-mfin": (76460, "52.08"),
    "cwru-social-work-msw": (44800, "44.07"),
    "cwru-public-health-mph": (39009, "51.22"),
}


# Each program spec: slug · school · program_name (full conferred degree) · field
# (short discipline term for feed keywords) · degree_type · duration_months ·
# department · cip · description (field-specific) · who (program-distinct audience).
# Optional kwargs: delivery_format, tuition (override), tracks, website.
def _p(slug, school, name, field, degree, months, dept, cip, desc, who, **kw):
    d = {
        "slug": slug, "school": school, "program_name": name, "field": field,
        "degree_type": degree, "duration_months": months, "department": dept,
        "cip": cip, "description": desc, "who": who,
    }
    d.update(kw)
    return d


PROGRAMS: list[dict] = [
    # ══ COLLEGE OF ARTS AND SCIENCES ══
    # ── Department of Anthropology ──
    _p("cwru-anthropology-ba", _CAS, "Bachelor of Arts in Anthropology", "Anthropology", "bachelors", 48,
       "Department of Anthropology", "45.02",
       "The comparative study of humanity across cultures and time — sociocultural anthropology, archaeology, and biological anthropology — grounded in ethnographic and field methods.",
       "Undergraduates curious about human cultures, evolution, and material remains who want ethnographic and archaeological training for the social sciences or health fields."),
    _p("cwru-anthropology-ma", _CAS, "Master of Arts in Anthropology", "Anthropology", "masters", 24,
       "Department of Anthropology", "45.02",
       "Graduate coursework in anthropological theory and ethnographic and archaeological method, deepening the analysis of health, culture, and society.",
       "Students seeking advanced anthropological research training before doctoral study or careers in applied and public-health research."),
    _p("cwru-anthropology-phd", _CAS, "Doctor of Philosophy in Anthropology", "Anthropology", "phd", 60,
       "Department of Anthropology", "45.02",
       "Doctoral research producing original ethnographic or archaeological scholarship, with dissertation fieldwork and preparation for academic and applied careers. Funded.",
       "Aspiring anthropologists pursuing original fieldwork-based dissertation research and university or applied-research careers. Funded with a stipend."),
    # ── Department of Art History and Art ──
    _p("cwru-art-history-ba", _CAS, "Bachelor of Arts in Art History", "Art History", "bachelors", 48,
       "Department of Art History and Art", "50.07",
       "The history of art, architecture, and visual culture from antiquity to the present, taught with close looking and access to Cleveland's museum collections.",
       "Students who want to read images and buildings closely and pursue museums, galleries, conservation, or graduate study in art history."),
    _p("cwru-art-history-ma", _CAS, "Master of Arts in Art History", "Art History", "masters", 24,
       "Department of Art History and Art", "50.07",
       "Graduate study of art-historical scholarship and method, developing research and writing across periods and media.",
       "Students seeking graduate art-historical training before doctoral study or careers in museums and the arts."),
    _p("cwru-art-history-phd", _CAS, "Doctor of Philosophy in Art History", "Art History", "phd", 60,
       "Department of Art History and Art", "50.07",
       "Doctoral research producing original scholarship in the history of art and architecture, culminating in a dissertation. Funded.",
       "Aspiring art historians pursuing original research and careers in university teaching or museum curatorship. Funded with a stipend."),
    _p("cwru-art-history-museum-studies-ma", _CAS, "Master of Arts in Art History and Museum Studies", "Museum Studies", "masters", 24,
       "Department of Art History and Art", "50.07",
       "Graduate training pairing art-historical scholarship with the curatorial, collections, and exhibition practice of museum work.",
       "Students headed for careers in museums, galleries, or collections management who want combined art-historical and curatorial training."),
    _p("cwru-pre-architecture-ba", _CAS, "Bachelor of Arts in Pre-Architecture", "Pre-Architecture", "bachelors", 48,
       "Department of Art History and Art", "04.02",
       "A pre-professional liberal-arts track combining design studio, architectural history, and building science to prepare students for a graduate Master of Architecture.",
       "Students aiming for a graduate architecture degree who want a design, history, and technical foundation before an M.Arch."),
    # ── Department of Astronomy ──
    _p("cwru-astronomy-ba", _CAS, "Bachelor of Arts in Astronomy", "Astronomy", "bachelors", 48,
       "Department of Astronomy", "40.02",
       "The study of stars, galaxies, and the cosmos, combining observational and theoretical astronomy with physics in a flexible degree.",
       "Students drawn to the cosmos who want a broad astronomy major, often paired with another field or education goals."),
    _p("cwru-astronomy-bs", _CAS, "Bachelor of Science in Astronomy", "Astronomy", "bachelors", 48,
       "Department of Astronomy", "40.02",
       "A physics-intensive study of astrophysics — stellar structure, galaxies, and cosmology — with strong mathematics and observational and computational training.",
       "Students preparing for graduate study or research in astrophysics who want a rigorous, quantitative astronomy degree."),
    _p("cwru-astronomy-phd", _CAS, "Doctor of Philosophy in Astronomy", "Astronomy", "phd", 60,
       "Department of Astronomy", "40.02",
       "Doctoral research in astrophysics — from extragalactic astronomy and cosmology to instrumentation — culminating in an original dissertation. Funded.",
       "Students pursuing careers as research astrophysicists in academia or observatories. Funded with a stipend."),
    # ── Department of Biology ──
    _p("cwru-biology-ba", _CAS, "Bachelor of Arts in Biology", "Biology", "bachelors", 48,
       "Department of Biology", "26.01",
       "The life sciences from molecules and cells to organisms and ecosystems, in a flexible degree suited to broad or pre-professional study.",
       "Students who want a flexible life-sciences major for pre-health, education, or interdisciplinary paths."),
    _p("cwru-biology-bs", _CAS, "Bachelor of Science in Biology", "Biology", "bachelors", 48,
       "Department of Biology", "26.01",
       "A rigorous, lab-intensive study of biology across molecular, cellular, and organismal levels, with genetics, physiology, and independent research.",
       "Students preparing for medicine, biomedical research, or graduate study who want a broad, lab-intensive life-sciences foundation."),
    _p("cwru-biology-ms", _CAS, "Master of Science in Biology", "Biology", "masters", 24,
       "Department of Biology", "26.01",
       "Graduate coursework and laboratory research in the biological sciences, deepening research expertise for professional-school or doctoral preparation.",
       "Students seeking advanced biology training for research careers or as a bridge to a Ph.D. or professional school."),
    _p("cwru-biology-phd", _CAS, "Doctor of Philosophy in Biology", "Biology", "phd", 60,
       "Department of Biology", "26.01",
       "Doctoral research in molecular, cellular, developmental, or evolutionary biology, producing an original dissertation. Funded.",
       "Students pursuing careers as research biologists in academia, biotechnology, or medicine. Funded with a stipend."),
    _p("cwru-systems-biology-bs", _CAS, "Bachelor of Science in Systems Biology", "Systems Biology", "bachelors", 48,
       "Department of Biology", "26.01",
       "An integrative study of biological systems using computation, modeling, and genomics to understand how molecular networks produce cellular and organismal behavior.",
       "Quantitatively minded students who want to model living systems and bridge biology with computation and data science."),
    _p("cwru-neuroscience-bs", _CAS, "Bachelor of Science in Neuroscience", "Neuroscience", "bachelors", 48,
       "Department of Biology", "26.15",
       "The biology of the nervous system and behavior, from ion channels and neurons to circuits, cognition, and neurological disease.",
       "Pre-health and research-bound students fascinated by the brain who want an integrated biology, chemistry, and psychology foundation."),
    # ── Department of Chemistry ──
    _p("cwru-chemistry-ba", _CAS, "Bachelor of Arts in Chemistry", "Chemistry", "bachelors", 48,
       "Department of Chemistry", "40.05",
       "The molecular science of matter — organic, inorganic, physical, and analytical chemistry — in a flexible degree for broad or pre-health study.",
       "Students who want a chemistry foundation for pre-health, teaching, or interdisciplinary study."),
    _p("cwru-chemistry-bs", _CAS, "Bachelor of Science in Chemistry", "Chemistry", "bachelors", 48,
       "Department of Chemistry", "40.05",
       "A rigorous, research-oriented study of organic, inorganic, physical, and analytical chemistry with extensive laboratory and instrumentation training.",
       "Students who want to understand and create molecules and pursue chemistry, medicine, or materials science."),
    _p("cwru-chemistry-ms", _CAS, "Master of Science in Chemistry", "Chemistry", "masters", 24,
       "Department of Chemistry", "40.05",
       "Graduate coursework and laboratory research in chemistry, deepening synthetic or analytical expertise for industry or doctoral study.",
       "Students seeking advanced chemistry training for industry research or as a step toward a Ph.D."),
    _p("cwru-chemistry-phd", _CAS, "Doctor of Philosophy in Chemistry", "Chemistry", "phd", 60,
       "Department of Chemistry", "40.05",
       "Doctoral research across synthetic, physical, materials, and biological chemistry, producing an original dissertation. Funded.",
       "Students pursuing careers as research chemists in academia or industry. Funded with a stipend."),
    _p("cwru-chemical-biology-ba", _CAS, "Bachelor of Arts in Chemical Biology", "Chemical Biology", "bachelors", 48,
       "Department of Chemistry", "40.05",
       "The chemistry of biological molecules and processes, using chemical tools to probe and manipulate living systems at the interface of chemistry and biology.",
       "Pre-medical and research-bound students who want a molecular-science degree bridging chemistry and biology."),
    # ── Department of Classics ──
    _p("cwru-classics-ba", _CAS, "Bachelor of Arts in Classics", "Classics", "bachelors", 48,
       "Department of Classics", "16.12",
       "The languages, literature, and history of ancient Greece and Rome, from reading Homer and Virgil in the original to Roman history and archaeology.",
       "Students who love ancient languages and the classical roots of Western literature, philosophy, and law."),
    _p("cwru-classical-studies-ma", _CAS, "Master of Arts in Classical Studies", "Classical Studies", "masters", 24,
       "Department of Classics", "16.12",
       "Graduate study of Greek and Latin texts and the history and culture of the ancient Mediterranean, preparing students for doctoral work or teaching.",
       "Students seeking advanced training in the classical languages before a Ph.D. or a career in teaching."),
    _p("cwru-ancient-near-eastern-studies-ba", _CAS, "Bachelor of Arts in Ancient Near Eastern and Egyptian Studies", "Ancient Near Eastern Studies", "bachelors", 48,
       "Department of Classics", "30.22",
       "The languages, history, and archaeology of the ancient Near East and Egypt — from cuneiform and hieroglyphs to Mesopotamian and Egyptian civilization.",
       "Students drawn to the earliest civilizations who want training in ancient languages and archaeology for scholarship or museum work."),
    # ── Department of Cognitive Science ──
    _p("cwru-cognitive-science-ba", _CAS, "Bachelor of Arts in Cognitive Science", "Cognitive Science", "bachelors", 48,
       "Department of Cognitive Science", "30.25",
       "The interdisciplinary study of the mind — how perception, language, memory, and reasoning work — spanning psychology, linguistics, philosophy, computer science, and neuroscience.",
       "Students curious about how minds and machines think who want an interdisciplinary major bridging the humanities, sciences, and computation."),
    _p("cwru-cognitive-linguistics-ma", _CAS, "Master of Arts in Cognitive Linguistics", "Cognitive Linguistics", "masters", 24,
       "Department of Cognitive Science", "16.01",
       "Graduate study of how language reflects and shapes cognition — meaning, metaphor, and conceptual structure — within the cognitive-science tradition.",
       "Students who want advanced training in language and cognition before doctoral study or careers in research, education, or language technology."),
    # ── Department of Dance ──
    _p("cwru-dance-ba", _CAS, "Bachelor of Arts in Dance", "Dance", "bachelors", 48,
       "Department of Dance", "50.03",
       "The study and practice of contemporary dance — technique, choreography, and performance — integrated with dance history and the science of human movement.",
       "Students who want to perform and make dance within a liberal-arts curriculum that pairs studio practice with movement science."),
    _p("cwru-contemporary-dance-ma", _CAS, "Master of Arts in Contemporary Dance", "Contemporary Dance", "masters", 24,
       "Department of Dance", "50.03",
       "Graduate study integrating choreography, performance, and pedagogy with dance science, serving as the entry stage toward the terminal M.F.A.",
       "Dance artists and teachers seeking graduate training in contemporary practice, pedagogy, and movement science."),
    _p("cwru-contemporary-dance-mfa", _CAS, "Master of Fine Arts in Contemporary Dance", "Contemporary Dance", "masters", 36,
       "Department of Dance", "50.03",
       "A terminal pre-professional degree with emphases in choreography, performance, and pedagogy, grounded in dance science, for advanced dance artists.",
       "Established dancers and choreographers pursuing the terminal degree to teach at the college level or lead a professional practice."),
    # ── Department of Earth, Environmental, and Planetary Sciences ──
    _p("cwru-geological-sciences-ba", _CAS, "Bachelor of Arts in Geological Sciences", "Geological Sciences", "bachelors", 48,
       "Department of Earth, Environmental, and Planetary Sciences", "40.06",
       "The Earth's materials, structure, and history — minerals, rocks, and surface processes — in a flexible degree combining fieldwork with the natural sciences.",
       "Students fascinated by the Earth who want a flexible geoscience major for environmental, education, or interdisciplinary paths."),
    _p("cwru-geological-sciences-bs", _CAS, "Bachelor of Science in Geological Sciences", "Geological Sciences", "bachelors", 48,
       "Department of Earth, Environmental, and Planetary Sciences", "40.06",
       "A quantitative study of the solid Earth and its systems — tectonics, mineralogy, geochemistry, and geophysics — with substantial field and laboratory training.",
       "Students preparing for geoscience careers or graduate study who want a rigorous, field- and lab-intensive Earth-science degree."),
    _p("cwru-geological-sciences-ms", _CAS, "Master of Science in Geological Sciences", "Geological Sciences", "masters", 24,
       "Department of Earth, Environmental, and Planetary Sciences", "40.06",
       "Graduate research in the Earth sciences, combining coursework with field, laboratory, or analytical investigation of geological problems.",
       "Students seeking advanced geoscience training for environmental industry, government survey work, or doctoral study."),
    _p("cwru-geological-sciences-phd", _CAS, "Doctor of Philosophy in Geological Sciences", "Geological Sciences", "phd", 60,
       "Department of Earth, Environmental, and Planetary Sciences", "40.06",
       "Doctoral research on Earth's processes and history — from tectonics and geochemistry to climate and planetary science — producing an original dissertation. Funded.",
       "Students pursuing careers as research geoscientists in academia, government, or industry. Funded with a stipend."),
    _p("cwru-environmental-geology-ba", _CAS, "Bachelor of Arts in Environmental Geology", "Environmental Geology", "bachelors", 48,
       "Department of Earth, Environmental, and Planetary Sciences", "40.06",
       "The application of geology to environmental problems — groundwater, natural hazards, soils, and land use — bridging Earth science and environmental policy.",
       "Students who want to apply Earth science to water resources, hazards, and sustainability challenges."),
    # ── Department of English ──
    _p("cwru-english-ba", _CAS, "Bachelor of Arts in English", "English", "bachelors", 48,
       "Department of English", "23.01",
       "Literature in English from medieval to contemporary, alongside creative and expository writing, emphasizing close reading, argument, and clear prose.",
       "Students who love reading and writing and want the interpretive and communication skills valued in law, publishing, and teaching."),
    _p("cwru-english-ma", _CAS, "Master of Arts in English", "English", "masters", 24,
       "Department of English", "23.01",
       "Advanced study of literature and critical theory, refining research and writing for doctoral preparation or careers in writing and education.",
       "Students seeking graduate literary training before a Ph.D. or a career in teaching, editing, or writing."),
    _p("cwru-english-phd", _CAS, "Doctor of Philosophy in English", "English", "phd", 60,
       "Department of English", "23.01",
       "Doctoral research in literary history, theory, and criticism across periods, culminating in an original dissertation and teaching preparation. Funded.",
       "Aspiring literary scholars and professors pursuing original research in English literature. Funded with a stipend."),
    # ── Department of History ──
    _p("cwru-history-ba", _CAS, "Bachelor of Arts in History", "History", "bachelors", 48,
       "Department of History", "54.01",
       "The study of the past across regions and eras through primary sources, emphasizing evidence-based argument and historical writing.",
       "Students who want to reason from evidence about how societies change — a foundation for law, policy, and the professions."),
    _p("cwru-history-ma", _CAS, "Master of Arts in History", "History", "masters", 24,
       "Department of History", "54.01",
       "Graduate training in historical research, historiography, and writing across fields, preparing students for doctoral study or public-history careers.",
       "Students seeking advanced research training before doctoral study or careers in public history, archives, and education."),
    _p("cwru-history-phd", _CAS, "Doctor of Philosophy in History", "History", "phd", 60,
       "Department of History", "54.01",
       "Doctoral research producing original archival scholarship, with dissertation supervision and preparation for university teaching. Funded.",
       "Future historians and professors pursuing archival dissertation research. Funded with a stipend."),
    # ── Department of Mathematics, Applied Mathematics, and Statistics ──
    _p("cwru-mathematics-ba", _CAS, "Bachelor of Arts in Mathematics", "Mathematics", "bachelors", 48,
       "Department of Mathematics, Applied Mathematics, and Statistics", "27.01",
       "Pure and applied mathematics — calculus, analysis, algebra, and probability — in a flexible degree suited to double majors and broad study.",
       "Students who enjoy mathematical reasoning and want a flexible quantitative major alongside another field."),
    _p("cwru-mathematics-bs", _CAS, "Bachelor of Science in Mathematics", "Mathematics", "bachelors", 48,
       "Department of Mathematics, Applied Mathematics, and Statistics", "27.01",
       "A rigorous, proof-based study of analysis, algebra, geometry, and probability, with depth for graduate study or quantitative careers.",
       "Students who love rigorous proof and theory and want preparation for graduate mathematics, data science, or finance."),
    _p("cwru-mathematics-ms", _CAS, "Master of Science in Mathematics", "Mathematics", "masters", 24,
       "Department of Mathematics, Applied Mathematics, and Statistics", "27.01",
       "Graduate coursework in pure and applied mathematics, deepening theory and technique for doctoral study or quantitative professions.",
       "Students seeking advanced mathematical training before a Ph.D. or for careers in data, finance, or industry research."),
    _p("cwru-mathematics-phd", _CAS, "Doctor of Philosophy in Mathematics", "Mathematics", "phd", 60,
       "Department of Mathematics, Applied Mathematics, and Statistics", "27.01",
       "Doctoral research in areas such as analysis, algebra, geometry, and dynamical systems, producing an original dissertation. Funded.",
       "Students pursuing careers as research mathematicians and professors. Funded with a stipend."),
    _p("cwru-applied-mathematics-bs", _CAS, "Bachelor of Science in Applied Mathematics", "Applied Mathematics", "bachelors", 48,
       "Department of Mathematics, Applied Mathematics, and Statistics", "27.03",
       "Mathematical modeling, differential equations, numerical methods, and scientific computing applied to problems in science and engineering.",
       "Students who want to use mathematics to model and solve real-world problems in science, engineering, or industry."),
    _p("cwru-applied-mathematics-ms", _CAS, "Master of Science in Applied Mathematics", "Applied Mathematics", "masters", 24,
       "Department of Mathematics, Applied Mathematics, and Statistics", "27.03",
       "Graduate training in modeling, computation, and analysis, applying advanced mathematics to scientific, engineering, and data problems.",
       "Students seeking applied quantitative training for industry, national labs, or doctoral study."),
    _p("cwru-applied-mathematics-phd", _CAS, "Doctor of Philosophy in Applied Mathematics", "Applied Mathematics", "phd", 60,
       "Department of Mathematics, Applied Mathematics, and Statistics", "27.03",
       "Doctoral research in applied mathematics — modeling, numerical analysis, and computational science — culminating in an original dissertation. Funded.",
       "Students pursuing careers as applied mathematicians in academia, industry, or national laboratories. Funded with a stipend."),
    _p("cwru-statistics-ba", _CAS, "Bachelor of Arts in Statistics", "Statistics", "bachelors", 48,
       "Department of Mathematics, Applied Mathematics, and Statistics", "27.05",
       "The theory and practice of collecting, modeling, and drawing inferences from data, in a flexible degree pairing statistics with other fields.",
       "Students who want data and inference skills to complement another discipline in the social or natural sciences."),
    _p("cwru-statistics-bs", _CAS, "Bachelor of Science in Statistics", "Statistics", "bachelors", 48,
       "Department of Mathematics, Applied Mathematics, and Statistics", "27.05",
       "A rigorous study of probability, statistical inference, and data analysis, with computing and applied modeling for data-intensive careers.",
       "Students preparing for data science, biostatistics, or actuarial work who want a strong theoretical and computational foundation."),
    _p("cwru-statistics-ms", _CAS, "Master of Science in Statistics", "Statistics", "masters", 24,
       "Department of Mathematics, Applied Mathematics, and Statistics", "27.05",
       "Graduate training in statistical theory, modeling, and computation, preparing students for data-analytic careers or doctoral study.",
       "Students seeking applied statistical training for data science, biostatistics, or industry research."),
    _p("cwru-statistics-phd", _CAS, "Doctor of Philosophy in Statistics", "Statistics", "phd", 60,
       "Department of Mathematics, Applied Mathematics, and Statistics", "27.05",
       "Doctoral research in statistical theory and methodology and their applications, producing an original dissertation. Funded.",
       "Students pursuing careers as research statisticians in academia, industry, or government. Funded with a stipend."),
    _p("cwru-mathematics-and-physics-bs", _CAS, "Bachelor of Science in Mathematics and Physics", "Mathematics and Physics", "bachelors", 48,
       "Department of Mathematics, Applied Mathematics, and Statistics", "27.01",
       "A combined degree integrating advanced mathematics with theoretical and experimental physics, for students working at the interface of the two disciplines.",
       "Students drawn to mathematical physics who want rigorous training in both fields for graduate study in either."),
    # ── Department of Modern Languages and Literatures ──
    _p("cwru-chinese-ba", _CAS, "Bachelor of Arts in Chinese", "Chinese", "bachelors", 48,
       "Department of Modern Languages and Literatures", "16.03",
       "Chinese language, literature, and culture, from spoken and written Mandarin to the history and society of the Chinese-speaking world.",
       "Students who want Chinese fluency and cultural expertise for careers in business, policy, or scholarship."),
    _p("cwru-french-ba", _CAS, "Bachelor of Arts in French", "French", "bachelors", 48,
       "Department of Modern Languages and Literatures", "16.09",
       "French language and the literatures and cultures of France and the Francophone world across Europe, Africa, and the Americas.",
       "Students who want French fluency and deep engagement with Francophone literature and culture."),
    _p("cwru-french-ma", _CAS, "Master of Arts in French", "French", "masters", 24,
       "Department of Modern Languages and Literatures", "16.09",
       "Advanced study of French and Francophone literature, language, and culture, preparing students for teaching or doctoral study.",
       "Students seeking graduate training in French literature and culture for teaching or further doctoral work."),
    _p("cwru-german-ba", _CAS, "Bachelor of Arts in German", "German", "bachelors", 48,
       "Department of Modern Languages and Literatures", "16.05",
       "German language, literature, and culture in their central-European intellectual and historical context.",
       "Students who want German fluency and engagement with the German literary and philosophical tradition."),
    _p("cwru-japanese-studies-ba", _CAS, "Bachelor of Arts in Japanese Studies", "Japanese Studies", "bachelors", 48,
       "Department of Modern Languages and Literatures", "16.03",
       "Japanese language together with the literature, history, and culture of Japan, in an interdisciplinary area-studies major.",
       "Students who want Japanese fluency and interdisciplinary expertise on Japan for careers in business, policy, or scholarship."),
    _p("cwru-spanish-ba", _CAS, "Bachelor of Arts in Spanish", "Spanish", "bachelors", 48,
       "Department of Modern Languages and Literatures", "16.09",
       "Spanish language and the literatures and cultures of Spain and Latin America, with pathways for community engagement and study abroad.",
       "Students who want advanced Spanish and knowledge of the Hispanic world for careers in health, law, education, or the arts."),
    # ── Department of Music ──
    _p("cwru-music-ba", _CAS, "Bachelor of Arts in Music", "Music", "bachelors", 48,
       "Department of Music", "50.09",
       "Music history, theory, composition, and performance across classical and world traditions, within a liberal-arts curriculum.",
       "Students who want to study and make music alongside a broad liberal-arts education."),
    _p("cwru-music-education-bs", _CAS, "Bachelor of Science in Music Education", "Music Education", "bachelors", 48,
       "Department of Music", "50.09",
       "The pedagogy, theory, and practice of teaching music, combining strong musicianship with preparation for K-12 music-teacher licensure.",
       "Students who want to become licensed school music teachers with strong musicianship and pedagogy."),
    _p("cwru-music-education-ma", _CAS, "Master of Arts in Music Education", "Music Education", "masters", 24,
       "Department of Music", "50.09",
       "Graduate study of music pedagogy, curriculum, and research, advancing the practice of experienced music educators.",
       "Practicing music teachers seeking advanced pedagogy and research training or a master's for career advancement."),
    _p("cwru-music-education-phd", _CAS, "Doctor of Philosophy in Music Education", "Music Education", "phd", 60,
       "Department of Music", "50.09",
       "Doctoral research in music education — learning, curriculum, and policy — producing original scholarship for the field. Funded.",
       "Experienced music educators pursuing research careers or university faculty positions in music education. Funded with a stipend."),
    _p("cwru-music-history-ma", _CAS, "Master of Arts in Music History", "Music History", "masters", 24,
       "Department of Music", "50.09",
       "Graduate study of Western music history and historical musicology, developing research and writing skills in the field.",
       "Students seeking graduate musicological training before doctoral study or careers in teaching and the arts."),
    _p("cwru-musicology-phd", _CAS, "Doctor of Philosophy in Musicology", "Musicology", "phd", 60,
       "Department of Music", "50.09",
       "Doctoral research in historical musicology, producing original scholarship on Western music history and culture. Funded.",
       "Aspiring musicologists pursuing original research and university teaching. Funded with a stipend."),
    _p("cwru-historical-performance-practice-ma", _CAS, "Master of Arts in Historical Performance Practice", "Historical Performance", "masters", 24,
       "Department of Music", "50.09",
       "Graduate study of early music and historically informed performance, pairing performance on period instruments with research in performance practice.",
       "Performers and scholars of early music who want graduate training in historically informed performance."),
    _p("cwru-historical-performance-practice-dma", _CAS, "Doctor of Musical Arts in Historical Performance Practice", "Historical Performance", "phd", 60,
       "Department of Music", "50.09",
       "A doctoral performance degree in early music, integrating advanced performance on historical instruments, lecture-recitals, and research in performance practice.",
       "Advanced early-music performers pursuing the terminal performance degree for solo, ensemble, and university careers."),
    # ── Department of Philosophy ──
    _p("cwru-philosophy-ba", _CAS, "Bachelor of Arts in Philosophy", "Philosophy", "bachelors", 48,
       "Department of Philosophy", "38.01",
       "The central questions of knowledge, reality, ethics, and meaning, from ancient thought through contemporary analytic and continental philosophy.",
       "Students who want to think rigorously about fundamental questions — strong preparation for law, medicine, and analytical careers."),
    _p("cwru-military-ethics-ma", _CAS, "Master of Arts in Military Ethics", "Military Ethics", "masters", 24,
       "Department of Philosophy", "38.01",
       "Graduate study of the ethics of war, armed force, and military service — just-war theory, the laws of armed conflict, and professional military ethics.",
       "Military officers, chaplains, and policy professionals who want rigorous grounding in the ethics of armed conflict and service."),
    # ── Department of Physics ──
    _p("cwru-physics-ba", _CAS, "Bachelor of Arts in Physics", "Physics", "bachelors", 48,
       "Department of Physics", "40.08",
       "Classical and modern physics — mechanics, electromagnetism, and quantum theory — in a flexible degree for broad or interdisciplinary study.",
       "Students who want a strong physics foundation alongside another field or a broad liberal-arts path."),
    _p("cwru-physics-bs", _CAS, "Bachelor of Science in Physics", "Physics", "bachelors", 48,
       "Department of Physics", "40.08",
       "A rigorous study of physics from classical mechanics to quantum and statistical physics, with laboratory and research training for graduate study.",
       "Students who want to understand nature's fundamental laws and pursue physics, engineering, or quantitative careers."),
    _p("cwru-physics-ms", _CAS, "Master of Science in Physics", "Physics", "masters", 24,
       "Department of Physics", "40.08",
       "Graduate coursework and research in physics, deepening theoretical and experimental expertise for doctoral study or technical careers.",
       "Students seeking advanced physics training before a Ph.D. or for careers in industry and applied research."),
    _p("cwru-physics-phd", _CAS, "Doctor of Philosophy in Physics", "Physics", "phd", 60,
       "Department of Physics", "40.08",
       "Doctoral research across areas such as condensed-matter, biological, and astrophysical physics, producing an original dissertation. Funded.",
       "Students pursuing careers as research physicists in academia, national labs, or industry. Funded with a stipend."),
    # ── Department of Political Science ──
    _p("cwru-political-science-ba", _CAS, "Bachelor of Arts in Political Science", "Political Science", "bachelors", 48,
       "Department of Political Science", "45.10",
       "American and comparative politics, international relations, and political theory, analyzing power, institutions, and public policy.",
       "Students headed for law, government, policy, or journalism who want to analyze political institutions and ideas."),
    _p("cwru-political-science-ma", _CAS, "Master of Arts in Political Science", "Political Science", "masters", 24,
       "Department of Political Science", "45.10",
       "Graduate study of political theory, comparative politics, and international relations, deepening analytical and research skills.",
       "Students seeking advanced political-science training before doctoral study or careers in policy and government."),
    _p("cwru-political-science-phd", _CAS, "Doctor of Philosophy in Political Science", "Political Science", "phd", 60,
       "Department of Political Science", "45.10",
       "Doctoral research across the subfields of political science, producing original scholarship and preparing students for university teaching. Funded.",
       "Future political scientists pursuing original research and academic careers. Funded with a stipend."),
    _p("cwru-international-studies-ba", _CAS, "Bachelor of Arts in International Studies", "International Studies", "bachelors", 48,
       "Department of Political Science", "30.20",
       "An interdisciplinary major in global politics, economics, and culture, with foreign-language study and a focus on world affairs.",
       "Students headed for diplomacy, international business, or global NGOs who want an interdisciplinary, globally focused major."),
    # ── Department of Psychological Sciences ──
    _p("cwru-psychology-ba", _CAS, "Bachelor of Arts in Psychology", "Psychology", "bachelors", 48,
       "Department of Psychological Sciences", "42.01",
       "The science of mind and behavior — cognitive, developmental, social, and clinical psychology — with training in research methods.",
       "Students interested in human behavior and mental health headed for clinical, research, or applied careers."),
    _p("cwru-psychology-ma", _CAS, "Master of Arts in Psychology", "Psychology", "masters", 24,
       "Department of Psychological Sciences", "42.01",
       "Graduate coursework and research in psychological science, deepening methodological and theoretical expertise for doctoral or applied work.",
       "Students seeking advanced psychology training before doctoral study or for research and applied roles."),
    _p("cwru-psychology-phd", _CAS, "Doctor of Philosophy in Psychology", "Psychology", "phd", 60,
       "Department of Psychological Sciences", "42.01",
       "Doctoral research in areas such as adult development, aging, and quantitative psychology, producing an original dissertation. Funded.",
       "Students pursuing careers as research psychologists and professors. Funded with a stipend."),
    _p("cwru-communication-sciences-ba", _CAS, "Bachelor of Arts in Communication Sciences", "Communication Sciences", "bachelors", 48,
       "Department of Psychological Sciences", "51.02",
       "The science of human communication and its disorders — speech, language, and hearing — foundational to speech-language pathology and audiology.",
       "Students preparing for graduate study and clinical careers in speech-language pathology or audiology."),
    _p("cwru-communication-sciences-ma", _CAS, "Master of Arts in Communication Sciences", "Communication Sciences", "masters", 24,
       "Department of Psychological Sciences", "51.02",
       "Graduate study of communication sciences and disorders, combining coursework with clinical or research training in speech, language, and hearing.",
       "Students pursuing clinical or research careers in speech-language pathology, audiology, or hearing science."),
    _p("cwru-communication-sciences-phd", _CAS, "Doctor of Philosophy in Communication Sciences", "Communication Sciences", "phd", 60,
       "Department of Psychological Sciences", "51.02",
       "Doctoral research in the normal and disordered processes of speech, language, and hearing, producing original scholarship. Funded.",
       "Students pursuing research and academic careers in communication sciences and disorders. Funded with a stipend."),
    # ── Department of Religious Studies ──
    _p("cwru-religious-studies-ba", _CAS, "Bachelor of Arts in Religious Studies", "Religious Studies", "bachelors", 48,
       "Department of Religious Studies", "38.02",
       "The comparative, academic study of the world's religious traditions — their texts, histories, practices, and ethical thought.",
       "Students who want to understand religion's role in culture and society for careers in law, medicine, public service, or scholarship."),
    _p("cwru-religious-studies-ma", _CAS, "Master of Arts in Religious Studies", "Religious Studies", "masters", 24,
       "Department of Religious Studies", "38.02",
       "Graduate study of religious traditions and the methods of the field, preparing students for doctoral work or professional careers.",
       "Students seeking advanced training in the academic study of religion before doctoral study or related professions."),
    # ── Department of Sociology ──
    _p("cwru-sociology-ba", _CAS, "Bachelor of Arts in Sociology", "Sociology", "bachelors", 48,
       "Department of Sociology", "45.11",
       "How social structures, inequality, and institutions shape human life, with training in quantitative and qualitative research methods.",
       "Students who want to understand social inequality and institutions for careers in policy, law, or social research."),
    _p("cwru-sociology-ma", _CAS, "Master of Arts in Sociology", "Sociology", "masters", 24,
       "Department of Sociology", "45.11",
       "Graduate training in sociological theory and research methods, deepening the ability to study social structure and change.",
       "Students seeking advanced sociological research training before doctoral study or applied research careers."),
    _p("cwru-sociology-phd", _CAS, "Doctor of Philosophy in Sociology", "Sociology", "phd", 60,
       "Department of Sociology", "45.11",
       "Doctoral research on social structure, inequality, and change, producing original scholarship and preparing students for research and teaching. Funded.",
       "Aspiring sociologists pursuing original dissertation research and academic careers. Funded with a stipend."),
    # ── Department of Theater ──
    _p("cwru-theater-arts-ba", _CAS, "Bachelor of Arts in Theater Arts", "Theater Arts", "bachelors", 48,
       "Department of Theater", "50.05",
       "Acting, directing, design, and dramatic literature, combining studio practice with the critical study of theater and a full production season.",
       "Students who want to study and make theater within a liberal-arts curriculum."),
    _p("cwru-theater-arts-ma", _CAS, "Master of Arts in Theater Arts", "Theater Arts", "masters", 24,
       "Department of Theater", "50.05",
       "Graduate study of theater history, theory, and practice, serving as a foundation toward advanced study or the terminal M.F.A.",
       "Theater artists and scholars seeking graduate training before the terminal M.F.A. or doctoral study."),
    _p("cwru-theater-arts-mfa", _CAS, "Master of Fine Arts in Theater Arts", "Theater Arts", "masters", 36,
       "Department of Theater", "50.05",
       "A terminal professional degree in acting, directing, or design, preparing theater artists for professional and academic careers.",
       "Established theater artists pursuing the terminal degree for professional practice or college-level teaching."),
    # ══ CASE SCHOOL OF ENGINEERING ══
    # ── Department of Biomedical Engineering ──
    _p("cwru-biomedical-engineering-bse", _ENGR, "Bachelor of Science in Engineering in Biomedical Engineering", "Biomedical Engineering", "bachelors", 48,
       "Department of Biomedical Engineering", "14.05",
       "Engineering applied to medicine and biology — biomechanics, biomaterials, medical imaging, and instrumentation — to design devices and technologies that improve human health.",
       "Undergraduates who want to apply engineering to medicine, whether headed to industry, medical school, or graduate research."),
    _p("cwru-biomedical-engineering-ms", _ENGR, "Master of Science in Biomedical Engineering", "Biomedical Engineering", "masters", 24,
       "Department of Biomedical Engineering", "14.05",
       "Graduate study advancing the design and analysis of biomedical devices, biomaterials, and imaging and signal-processing methods for clinical and research use.",
       "Engineers and scientists seeking advanced biomedical-engineering training for industry research or doctoral study.",
       delivery_format="hybrid"),
    _p("cwru-biomedical-engineering-phd", _ENGR, "Doctor of Philosophy in Biomedical Engineering", "Biomedical Engineering", "phd", 60,
       "Department of Biomedical Engineering", "14.05",
       "Doctoral research at the interface of engineering and medicine — tissue engineering, neural engineering, biomaterials, and medical imaging. Funded.",
       "Students pursuing careers as biomedical-engineering researchers in academia, industry, or medicine. Funded with a stipend."),
    # ── Department of Chemical and Biomolecular Engineering ──
    _p("cwru-chemical-engineering-bse", _ENGR, "Bachelor of Science in Engineering in Chemical Engineering", "Chemical Engineering", "bachelors", 48,
       "Department of Chemical and Biomolecular Engineering", "14.07",
       "The design and operation of processes that transform raw materials into fuels, chemicals, and materials, grounded in thermodynamics, transport phenomena, and reaction engineering.",
       "Undergraduates headed for the chemical, energy, pharmaceutical, or materials industries."),
    _p("cwru-chemical-engineering-ms", _ENGR, "Master of Science in Chemical Engineering", "Chemical Engineering", "masters", 24,
       "Department of Chemical and Biomolecular Engineering", "14.07",
       "Advanced study of reaction engineering, transport phenomena, and biomolecular and materials processing for process and product innovation.",
       "Engineers seeking advanced process-engineering expertise for industry or doctoral study."),
    _p("cwru-chemical-engineering-phd", _ENGR, "Doctor of Philosophy in Chemical Engineering", "Chemical Engineering", "phd", 60,
       "Department of Chemical and Biomolecular Engineering", "14.07",
       "Doctoral research in catalysis, electrochemical energy, and biomolecular engineering, developing new processes and materials. Funded.",
       "Students pursuing careers as chemical-engineering researchers. Funded with a stipend."),
    # ── Department of Civil and Environmental Engineering ──
    _p("cwru-civil-engineering-bse", _ENGR, "Bachelor of Science in Engineering in Civil Engineering", "Civil Engineering", "bachelors", 48,
       "Department of Civil and Environmental Engineering", "14.08",
       "The analysis, design, and construction of the built environment — structures, transportation, water, and geotechnical systems — with attention to safety and sustainability.",
       "Undergraduates preparing to design and build infrastructure as professional civil engineers."),
    _p("cwru-civil-engineering-ms", _ENGR, "Master of Science in Civil Engineering", "Civil Engineering", "masters", 24,
       "Department of Civil and Environmental Engineering", "14.08",
       "Advanced study of structural, geotechnical, and environmental engineering, including resilient and sustainable infrastructure systems.",
       "Engineers seeking advanced civil or environmental engineering expertise for practice or research."),
    _p("cwru-civil-engineering-phd", _ENGR, "Doctor of Philosophy in Civil Engineering", "Civil Engineering", "phd", 60,
       "Department of Civil and Environmental Engineering", "14.08",
       "Doctoral research on structural mechanics, environmental engineering, and the resilience of infrastructure to natural hazards. Funded.",
       "Students pursuing careers as civil- and environmental-engineering researchers. Funded with a stipend."),
    # ── Department of Computer and Data Sciences ──
    _p("cwru-computer-science-bs", _ENGR, "Bachelor of Science in Computer Science", "Computer Science", "bachelors", 48,
       "Department of Computer and Data Sciences", "11.07",
       "Algorithms, systems, software, and theory across areas from artificial intelligence to computer networks, built on rigorous mathematical and programming foundations.",
       "Undergraduates who want a technical, math-intensive computing degree for software, research, or advanced study."),
    _p("cwru-computer-science-ba", _ENGR, "Bachelor of Arts in Computer Science", "Computer Science", "bachelors", 48,
       "Department of Computer and Data Sciences", "11.07",
       "The principles of computation — algorithms, software, and systems — paired with breadth in the arts and sciences for flexible, interdisciplinary paths.",
       "Undergraduates who want a computing foundation combined with a broad liberal-arts education or a double major."),
    _p("cwru-computer-science-ms", _ENGR, "Master of Science in Computer Science", "Computer Science", "masters", 24,
       "Department of Computer and Data Sciences", "11.07",
       "Advanced study of algorithms, machine learning, systems, and software, deepening both the theory and the practice of computing.",
       "Computing graduates and professionals seeking advanced technical training or a bridge to doctoral study.",
       delivery_format="hybrid"),
    _p("cwru-computer-science-phd", _ENGR, "Doctor of Philosophy in Computer Science", "Computer Science", "phd", 60,
       "Department of Computer and Data Sciences", "11.07",
       "Doctoral research across artificial intelligence, systems, security, and the theory of computing. Funded.",
       "Students pursuing careers as computer-science researchers in academia or industry. Funded with a stipend."),
    _p("cwru-data-science-analytics-bs", _ENGR, "Bachelor of Science in Data Science and Analytics", "Data Science and Analytics", "bachelors", 48,
       "Department of Computer and Data Sciences", "30.70",
       "The full pipeline of turning data into insight — statistics, machine learning, data management, and visualization — combined with domain application and data ethics.",
       "Undergraduates who want to analyze data and build models for careers in analytics, data science, or further study."),
    _p("cwru-data-science-ms", _ENGR, "Master of Science in Data Science", "Data Science", "masters", 24,
       "Department of Computer and Data Sciences", "30.71",
       "Graduate training in statistical learning, big-data systems, and predictive modeling for professional data-science practice.",
       "Graduates and professionals seeking applied data-science skills for analytics and machine-learning roles."),
    # ── Department of Electrical, Computer, and Systems Engineering ──
    _p("cwru-computer-engineering-bse", _ENGR, "Bachelor of Science in Engineering in Computer Engineering", "Computer Engineering", "bachelors", 48,
       "Department of Electrical, Computer, and Systems Engineering", "14.09",
       "The design of computing hardware and systems — digital logic, embedded systems, computer architecture, and hardware-software integration.",
       "Undergraduates who want to design computer hardware, embedded systems, and the interface between hardware and software."),
    _p("cwru-computer-engineering-ms", _ENGR, "Master of Science in Computer Engineering", "Computer Engineering", "masters", 24,
       "Department of Electrical, Computer, and Systems Engineering", "14.09",
       "Advanced study of computer architecture, embedded and cyber-physical systems, and hardware for computing and communications.",
       "Engineers seeking advanced computer-engineering expertise for industry or doctoral study."),
    _p("cwru-computer-engineering-phd", _ENGR, "Doctor of Philosophy in Computer Engineering", "Computer Engineering", "phd", 60,
       "Department of Electrical, Computer, and Systems Engineering", "14.09",
       "Doctoral research in embedded systems, hardware security, and computer architecture. Funded.",
       "Students pursuing careers as computer-engineering researchers. Funded with a stipend."),
    _p("cwru-electrical-engineering-bse", _ENGR, "Bachelor of Science in Engineering in Electrical Engineering", "Electrical Engineering", "bachelors", 48,
       "Department of Electrical, Computer, and Systems Engineering", "14.10",
       "The science and design of electrical and electronic systems — circuits, signals, control, electromagnetics, and power — that underpin modern technology.",
       "Undergraduates who want to design electronics, power, and signal systems across industries."),
    _p("cwru-electrical-engineering-ms", _ENGR, "Master of Science in Electrical Engineering", "Electrical Engineering", "masters", 24,
       "Department of Electrical, Computer, and Systems Engineering", "14.10",
       "Advanced study of signal processing, control, electronics, and power systems for engineering practice and research.",
       "Engineers seeking advanced electrical-engineering expertise for industry or doctoral study."),
    _p("cwru-electrical-engineering-phd", _ENGR, "Doctor of Philosophy in Electrical Engineering", "Electrical Engineering", "phd", 60,
       "Department of Electrical, Computer, and Systems Engineering", "14.10",
       "Doctoral research in sensors, control, power systems, and signal processing. Funded.",
       "Students pursuing careers as electrical-engineering researchers. Funded with a stipend."),
    _p("cwru-systems-control-engineering-ms", _ENGR, "Master of Science in Systems and Control Engineering", "Systems and Control Engineering", "masters", 24,
       "Department of Electrical, Computer, and Systems Engineering", "14.27",
       "The modeling, control, and optimization of complex dynamic systems, spanning control theory, systems engineering, and data-driven decision-making.",
       "Engineers seeking expertise in control and systems engineering for industry or doctoral study.",
       delivery_format="hybrid"),
    _p("cwru-systems-control-engineering-phd", _ENGR, "Doctor of Philosophy in Systems and Control Engineering", "Systems and Control Engineering", "phd", 60,
       "Department of Electrical, Computer, and Systems Engineering", "14.27",
       "Doctoral research in control theory, optimization, and the analysis of complex engineered systems. Funded.",
       "Students pursuing careers as systems- and control-engineering researchers. Funded with a stipend."),
    # ── Department of Macromolecular Science and Engineering ──
    _p("cwru-polymer-science-engineering-bse", _ENGR, "Bachelor of Science in Engineering in Polymer Science and Engineering", "Polymer Science and Engineering", "bachelors", 48,
       "Department of Macromolecular Science and Engineering", "14.32",
       "The science and engineering of polymers and soft materials — their synthesis, structure, properties, and processing into plastics, fibers, and advanced materials.",
       "Undergraduates drawn to plastics, soft materials, and polymer engineering for materials-industry or research careers."),
    _p("cwru-macromolecular-science-ms", _ENGR, "Master of Science in Macromolecular Science and Engineering", "Macromolecular Science", "masters", 24,
       "Department of Macromolecular Science and Engineering", "14.32",
       "Advanced study of the synthesis, characterization, and physics of polymers and macromolecular materials.",
       "Scientists and engineers seeking advanced polymer-science training for industry or doctoral study."),
    _p("cwru-macromolecular-science-phd", _ENGR, "Doctor of Philosophy in Macromolecular Science and Engineering", "Macromolecular Science", "phd", 60,
       "Department of Macromolecular Science and Engineering", "14.32",
       "Doctoral research on polymer synthesis, structure, and properties and next-generation macromolecular materials. Funded.",
       "Students pursuing careers as polymer and materials researchers. Funded with a stipend."),
    # ── Department of Materials Science and Engineering ──
    _p("cwru-materials-science-engineering-bse", _ENGR, "Bachelor of Science in Engineering in Materials Science and Engineering", "Materials Science and Engineering", "bachelors", 48,
       "Department of Materials Science and Engineering", "14.18",
       "The relationships between the structure, properties, processing, and performance of metals, ceramics, polymers, and electronic materials.",
       "Undergraduates who want to engineer materials for aerospace, energy, electronics, and biomedical applications."),
    _p("cwru-materials-science-engineering-ms", _ENGR, "Master of Science in Materials Science and Engineering", "Materials Science and Engineering", "masters", 24,
       "Department of Materials Science and Engineering", "14.18",
       "Advanced study of the structure-property relationships and processing of engineering materials, from metals to electronic and energy materials.",
       "Engineers seeking advanced materials-science expertise for industry or doctoral study."),
    _p("cwru-materials-science-engineering-phd", _ENGR, "Doctor of Philosophy in Materials Science and Engineering", "Materials Science and Engineering", "phd", 60,
       "Department of Materials Science and Engineering", "14.18",
       "Doctoral research on materials design and processing across metals, ceramics, and functional materials for energy and electronics. Funded.",
       "Students pursuing careers as materials-science researchers. Funded with a stipend."),
    # ── Department of Mechanical and Aerospace Engineering ──
    _p("cwru-aerospace-engineering-bse", _ENGR, "Bachelor of Science in Engineering in Aerospace Engineering", "Aerospace Engineering", "bachelors", 48,
       "Department of Mechanical and Aerospace Engineering", "14.02",
       "The engineering of aircraft and spacecraft — aerodynamics, propulsion, structures, and flight dynamics — grounded in mechanics and thermal-fluid science.",
       "Undergraduates aiming for careers in aerospace, defense, and the design of flight vehicles."),
    _p("cwru-aerospace-engineering-ms", _ENGR, "Master of Science in Aerospace Engineering", "Aerospace Engineering", "masters", 24,
       "Department of Mechanical and Aerospace Engineering", "14.02",
       "Advanced study of aerodynamics, propulsion, and aerospace structures and dynamics for design and analysis.",
       "Engineers seeking advanced aerospace-engineering expertise for industry or doctoral study."),
    _p("cwru-aerospace-engineering-phd", _ENGR, "Doctor of Philosophy in Aerospace Engineering", "Aerospace Engineering", "phd", 60,
       "Department of Mechanical and Aerospace Engineering", "14.02",
       "Doctoral research in fluid dynamics, propulsion, and aerospace structures and control. Funded.",
       "Students pursuing careers as aerospace-engineering researchers. Funded with a stipend."),
    _p("cwru-mechanical-engineering-bse", _ENGR, "Bachelor of Science in Engineering in Mechanical Engineering", "Mechanical Engineering", "bachelors", 48,
       "Department of Mechanical and Aerospace Engineering", "14.19",
       "The design and analysis of machines and thermal-fluid systems — mechanics, dynamics, materials, and energy — across virtually every industry.",
       "Undergraduates who want a broad engineering degree for design, manufacturing, energy, or robotics careers."),
    _p("cwru-mechanical-engineering-ms", _ENGR, "Master of Science in Mechanical Engineering", "Mechanical Engineering", "masters", 24,
       "Department of Mechanical and Aerospace Engineering", "14.19",
       "Advanced study of mechanics, dynamics and control, thermal-fluid sciences, and mechanical design.",
       "Engineers seeking advanced mechanical-engineering expertise for industry or doctoral study.",
       delivery_format="hybrid"),
    _p("cwru-mechanical-engineering-phd", _ENGR, "Doctor of Philosophy in Mechanical Engineering", "Mechanical Engineering", "phd", 60,
       "Department of Mechanical and Aerospace Engineering", "14.19",
       "Doctoral research in robotics, dynamics and control, and thermal-fluid and energy systems. Funded.",
       "Students pursuing careers as mechanical-engineering researchers. Funded with a stipend."),
    # ══ WEATHERHEAD SCHOOL OF MANAGEMENT ══
    _p("cwru-accounting-bs", _WEA, "Bachelor of Science in Accounting", "Accounting", "bachelors", 48,
       "Department of Accountancy", "52.03",
       "Financial and managerial accounting, auditing, taxation, and accounting information systems, preparing students for the CPA and careers in assurance and advisory.",
       "Undergraduates headed for public accounting, corporate finance, or the CPA credential."),
    _p("cwru-accounting-macc", _WEA, "Master of Accountancy", "Accounting", "masters", 12,
       "Department of Accountancy", "52.03",
       "A graduate accounting degree completing CPA-eligibility credits with advanced financial reporting, audit, tax, and accounting analytics.",
       "Accounting and business graduates completing the 150-credit CPA pathway for careers in public accounting and advisory."),
    _p("cwru-finance-bsm", _WEA, "Bachelor of Science in Management in Finance", "Finance", "bachelors", 48,
       "Department of Banking and Finance", "52.08",
       "Corporate finance, investments, and financial markets, with quantitative training for careers in banking, asset management, and corporate finance.",
       "Undergraduates targeting investment banking, asset management, or corporate finance roles."),
    _p("cwru-finance-mfin", _WEA, "Master of Finance", "Finance", "masters", 12,
       "Department of Banking and Finance", "52.08",
       "A STEM-designated specialized master's in corporate finance, investments, financial modeling, and financial data analysis.",
       "Recent graduates and early-career professionals targeting quantitative finance, investment, and risk roles."),
    _p("cwru-business-information-technology-bsm", _WEA, "Bachelor of Science in Management in Business Information Technology", "Business Information Technology", "bachelors", 48,
       "Department of Design and Innovation", "52.12",
       "The design and management of information systems and business technology — data, analytics, and digital systems that drive organizational decisions.",
       "Undergraduates who want to bridge business and technology in analyst, IT, or product roles."),
    _p("cwru-marketing-bsm", _WEA, "Bachelor of Science in Management in Marketing", "Marketing", "bachelors", 48,
       "Department of Design and Innovation", "52.14",
       "Consumer behavior, brand strategy, digital marketing, and marketing analytics for understanding and shaping customer decisions.",
       "Undergraduates drawn to brand management, market research, and digital marketing."),
    _p("cwru-management-phd", _WEA, "Doctor of Philosophy in Management", "Management", "phd", 60,
       "Department of Design and Innovation", "52.02",
       "Doctoral research on designing sustainable systems and organizations, training scholars across the management disciplines. Funded.",
       "Aspiring business-school professors pursuing original management research. Funded with a stipend."),
    _p("cwru-economics-ba", _WEA, "Bachelor of Arts in Economics", "Economics", "bachelors", 48,
       "Department of Economics", "45.06",
       "Micro- and macroeconomic theory with empirical and econometric methods, applied to markets, policy, and business decisions.",
       "Undergraduates who want analytical economics training for careers in business, finance, policy, or graduate study."),
    _p("cwru-supply-chain-management-mscm", _WEA, "Master of Supply Chain Management", "Supply Chain Management", "masters", 24,
       "Department of Operations", "52.13",
       "A STEM-designated master's in supply-chain analytics, logistics, procurement, and operations, using data and AI-driven tools to design resilient supply chains.",
       "Early-career professionals pursuing roles in supply-chain planning, analytics, procurement, and operations management."),
    _p("cwru-business-analytics-mbai", _WEA, "Master of Business Analytics and Intelligence", "Business Analytics", "masters", 24,
       "Department of Operations", "52.13",
       "A STEM-designated master's integrating machine learning, AI, and big-data analytics with business judgment to drive decisions in operations and marketing.",
       "Graduates and early-career professionals who want to turn data into business decisions in analytics and data-science roles."),
    _p("cwru-leadership-organizational-change-msloc", _WEA, "Master of Science in Leadership and Organizational Change", "Leadership and Organizational Change", "masters", 24,
       "Department of Organizational Behavior", "52.13",
       "A graduate degree in leading organizational change, grounded in appreciative inquiry, emotional intelligence, and positive organization development.",
       "Experienced managers and change agents leading transformation across organizations."),
    _p("cwru-organizational-behavior-phd", _WEA, "Doctor of Philosophy in Organizational Behavior", "Organizational Behavior", "phd", 60,
       "Department of Organizational Behavior", "52.10",
       "Doctoral research on individuals, teams, and organizations — leadership, change, and positive organizational scholarship. Funded.",
       "Aspiring scholars researching organizational behavior and leadership. Funded with a stipend."),
    _p("cwru-mba", _WEA, "Master of Business Administration", "Business Administration", "masters", 24,
       "Weatherhead School of Management", "52.02",
       "A general-management degree integrating finance, marketing, operations, strategy, and leadership, with analytics and experiential learning.",
       "Early-to-mid-career professionals seeking general-management and leadership training to advance or change careers.",
       delivery_format="hybrid"),
    # ══ SCHOOL OF MEDICINE ══
    # ── Doctor of Medicine — the two distinct MD pathways ──
    _p("cwru-medicine-md-university", _MED, "Doctor of Medicine (University Program)", "Medicine", "professional", 48,
       "School of Medicine", "51.12",
       "The traditional four-year M.D., pairing preclinical foundations in the basic sciences with clinical clerkships across Cleveland's teaching hospitals and a scholarly research requirement.",
       "Aspiring physicians who want a rigorous, research-informed M.D. on the standard four-year timeline."),
    _p("cwru-medicine-md-lerner", _MED, "Doctor of Medicine (Cleveland Clinic Lerner College of Medicine)", "Medicine", "professional", 60,
       "Cleveland Clinic Lerner College of Medicine", "51.12",
       "A five-year, research-oriented M.D. with a small class, no course grades, and an embedded thesis, designed to prepare physician-investigators for careers in academic medicine.",
       "Students set on becoming physician-scientists who want a research-intensive, tuition-free M.D. within an academic medical center."),
    _p("cwru-mstp-mdphd", _MED, "Doctor of Medicine and Doctor of Philosophy (MD/PhD)", "Medical Scientist", "professional", 96,
       "Medical Scientist Training Program", "51.12",
       "A fully funded, dual-degree program interleaving the M.D. with doctoral research so graduates are trained both to practice medicine and to lead independent biomedical research.",
       "Future physician-scientists committed to careers that bridge patient care and laboratory discovery. Funded with a stipend."),
    # ── Department of Anatomy ──
    _p("cwru-applied-anatomy-ms", _MED, "Master of Science in Applied Anatomy", "Applied Anatomy", "masters", 24,
       "Department of Anatomy", "26.04",
       "Graduate study of human gross, developmental, and neuro-anatomy anchored in cadaveric dissection, preparing students to teach anatomy and to strengthen health-professions applications.",
       "Students who want deep, hands-on anatomical training as a bridge to medical, dental, or other health-professions study."),
    # ── Department of Anesthesiology ──
    _p("cwru-anesthesia-msa", _MED, "Master of Science in Anesthesia", "Anesthesia", "masters", 24,
       "Department of Anesthesiology", "51.99",
       "Didactic and clinical preparation to become a certified anesthesiologist assistant, delivering anesthesia care as part of the anesthesia care team under physician direction.",
       "Science graduates pursuing a clinical career as an anesthesiologist assistant in the operating room."),
    # ── Department of Biochemistry ──
    _p("cwru-biochemistry-ba", _MED, "Bachelor of Arts in Biochemistry", "Biochemistry", "bachelors", 48,
       "Department of Biochemistry", "26.02",
       "The chemistry of living systems — proteins, nucleic acids, enzymes, and metabolism — with a flexible liberal-arts course structure.",
       "Undergraduates who want a molecular life-science major with room for broad liberal-arts study."),
    _p("cwru-biochemistry-bs", _MED, "Bachelor of Science in Biochemistry", "Biochemistry", "bachelors", 48,
       "Department of Biochemistry", "26.02",
       "A quantitative, laboratory-intensive study of biomolecular structure, enzyme mechanism, and metabolism at the interface of chemistry and biology.",
       "Pre-medical and research-bound students who want a rigorous molecular science major with strong lab training."),
    _p("cwru-biochemistry-ms", _MED, "Master of Science in Biochemistry", "Biochemistry", "masters", 24,
       "Department of Biochemistry", "26.02",
       "Advanced coursework and laboratory research in protein chemistry, molecular biology, and enzymology, preparing students for doctoral study or the biotechnology workforce.",
       "Students seeking graduate biochemistry training before a Ph.D. or a laboratory research career."),
    _p("cwru-biochemistry-phd", _MED, "Doctor of Philosophy in Biochemistry", "Biochemistry", "phd", 60,
       "Department of Biochemistry", "26.02",
       "Doctoral research on the structure, mechanism, and regulation of biological macromolecules, from enzymes and RNA to signaling and metabolism. Funded.",
       "Students pursuing careers as research biochemists in academia or industry. Funded with a stipend."),
    _p("cwru-biotechnology-ms", _MED, "Master of Science in Biotechnology", "Biotechnology", "masters", 24,
       "Department of Biochemistry", "26.12",
       "Applied training in molecular and cellular techniques, bioprocessing, and the business of the life sciences, oriented to the biotechnology and pharmaceutical industries.",
       "Science graduates aiming for laboratory, development, or commercialization roles in biotech and pharma."),
    # ── Department of Bioethics ──
    _p("cwru-bioethics-ma", _MED, "Master of Arts in Bioethics and Medical Humanities", "Bioethics", "masters", 24,
       "Department of Bioethics", "51.32",
       "Interdisciplinary study of the ethical, legal, and humanistic dimensions of medicine and the life sciences, from clinical decision-making to research and health policy.",
       "Clinicians, scholars, and professionals who want formal grounding in bioethics for clinical, research, or policy work."),
    _p("cwru-bioethics-phd", _MED, "Doctor of Philosophy in Bioethics", "Bioethics", "phd", 60,
       "Department of Bioethics", "51.32",
       "Doctoral research producing original scholarship in bioethics and the medical humanities across clinical ethics, research ethics, and health policy. Funded.",
       "Aspiring bioethics scholars pursuing academic, clinical-ethics, or policy careers. Funded with a stipend."),
    # ── Department of Genetics and Genome Sciences ──
    _p("cwru-genetic-counseling-ms", _MED, "Master of Science in Genetic Counseling", "Genetic Counseling", "masters", 24,
       "Department of Genetics and Genome Sciences", "26.08",
       "Accredited clinical training in medical genetics, risk assessment, and counseling technique, with supervised rotations preparing graduates for board certification as genetic counselors.",
       "Students pursuing certification and a clinical career helping patients understand and navigate genetic conditions."),
    _p("cwru-genetics-phd", _MED, "Doctor of Philosophy in Genetics", "Genetics", "phd", 60,
       "Department of Genetics and Genome Sciences", "26.08",
       "Doctoral research in molecular genetics, genomics, and the genetic basis of disease, spanning model organisms and human genetics. Funded.",
       "Students pursuing careers as research geneticists in academia, medicine, or biotech. Funded with a stipend."),
    # ── Department of Molecular Biology and Microbiology ──
    _p("cwru-molecular-biology-microbiology-phd", _MED, "Doctor of Philosophy in Molecular Biology and Microbiology", "Molecular Microbiology", "phd", 60,
       "Department of Molecular Biology and Microbiology", "26.05",
       "Doctoral research on microbial pathogenesis, host-pathogen interaction, and the molecular machinery of the cell, from bacteria and parasites to gene regulation. Funded.",
       "Students pursuing research careers in microbiology and molecular biology. Funded with a stipend."),
    _p("cwru-cell-biology-phd", _MED, "Doctor of Philosophy in Cell Biology", "Cell Biology", "phd", 60,
       "Department of Molecular Biology and Microbiology", "26.04",
       "Doctoral research on the organization and dynamics of the cell — membrane trafficking, the cytoskeleton, organelles, and signaling — and how they go awry in disease. Funded.",
       "Students pursuing careers as cell-biology researchers in academia or industry. Funded with a stipend."),
    _p("cwru-molecular-virology-phd", _MED, "Doctor of Philosophy in Molecular Virology", "Molecular Virology", "phd", 60,
       "Department of Molecular Biology and Microbiology", "26.05",
       "Doctoral research on virus structure, replication, and pathogenesis and the host immune response, informing antiviral and vaccine strategies. Funded.",
       "Students pursuing research careers in virology and infectious-disease science. Funded with a stipend."),
    # ── Department of Molecular Medicine ──
    _p("cwru-molecular-medicine-phd", _MED, "Doctor of Philosophy in Molecular Medicine", "Molecular Medicine", "phd", 60,
       "Department of Molecular Medicine", "26.14",
       "Doctoral research that translates molecular and cellular biology into an understanding of human disease mechanisms and therapeutic targets. Funded.",
       "Students pursuing research careers at the interface of laboratory science and clinical medicine. Funded with a stipend."),
    # ── Department of Neurosciences ──
    _p("cwru-neurosciences-phd", _MED, "Doctor of Philosophy in Neurosciences", "Neurosciences", "phd", 60,
       "Department of Neurosciences", "26.15",
       "Doctoral research on the nervous system from molecules and synapses to neural circuits, development, and disease, spanning cellular and systems neuroscience. Funded.",
       "Students pursuing careers as neuroscience researchers in academia or industry. Funded with a stipend."),
    # ── Department of Nutrition ──
    _p("cwru-nutrition-ba", _MED, "Bachelor of Arts in Nutrition", "Nutrition", "bachelors", 48,
       "Department of Nutrition", "19.05",
       "The science of nutrients, diet, and metabolism and their role in health, with a flexible liberal-arts structure.",
       "Undergraduates interested in nutrition and health who want a broad, liberal-arts course of study."),
    _p("cwru-nutrition-bs", _MED, "Bachelor of Science in Nutrition", "Nutrition", "bachelors", 48,
       "Department of Nutrition", "19.05",
       "A science-intensive study of human nutrition, biochemistry, and metabolism, grounding students for dietetics, health professions, or research.",
       "Pre-health and dietetics-bound students who want a rigorous science foundation in nutrition."),
    _p("cwru-nutrition-ms", _MED, "Master of Science in Nutrition", "Nutrition", "masters", 24,
       "Department of Nutrition", "19.05",
       "Advanced study of nutrient metabolism, nutritional assessment, and diet in health and disease, combining coursework with research or clinical training.",
       "Students seeking advanced nutrition training for research, dietetics, or doctoral study."),
    _p("cwru-nutrition-phd", _MED, "Doctor of Philosophy in Nutrition", "Nutrition", "phd", 60,
       "Department of Nutrition", "19.05",
       "Doctoral research in nutritional science — molecular nutrition, metabolism, and diet-related chronic disease. Funded.",
       "Students pursuing careers as nutrition scientists in academia, industry, or public health. Funded with a stipend."),
    _p("cwru-nutritional-biochemistry-ba", _MED, "Bachelor of Arts in Nutritional Biochemistry and Metabolism", "Nutritional Biochemistry", "bachelors", 48,
       "Department of Nutrition", "19.05",
       "The molecular study of how nutrients are metabolized and regulated in the body, blending nutrition with biochemistry in a liberal-arts structure.",
       "Undergraduates who want to understand nutrition at the molecular and metabolic level."),
    _p("cwru-nutritional-biochemistry-bs", _MED, "Bachelor of Science in Nutritional Biochemistry and Metabolism", "Nutritional Biochemistry", "bachelors", 48,
       "Department of Nutrition", "19.05",
       "A science-intensive major in nutrient biochemistry, metabolic regulation, and the molecular basis of diet-related disease.",
       "Pre-health and research-bound students who want a molecular, lab-focused nutrition major."),
    _p("cwru-public-health-nutrition-ms", _MED, "Master of Science in Public Health Nutrition", "Public Health Nutrition", "masters", 24,
       "Department of Nutrition", "19.05",
       "Population-level nutrition — food policy, community intervention, and nutritional epidemiology — aimed at improving diet and health across communities.",
       "Students who want to shape nutrition at the population and policy level rather than one patient at a time."),
    _p("cwru-systems-biology-bioinformatics-ms", _MED, "Master of Science in Systems Biology and Bioinformatics", "Systems Biology", "masters", 24,
       "Department of Nutrition", "26.11",
       "Computational and quantitative analysis of biological systems — genomics, networks, and high-throughput data — bridging biology, statistics, and computing.",
       "Students who want to apply computation and data science to biological and biomedical problems."),
    _p("cwru-systems-biology-bioinformatics-phd", _MED, "Doctor of Philosophy in Systems Biology and Bioinformatics", "Systems Biology", "phd", 60,
       "Department of Nutrition", "26.11",
       "Doctoral research developing and applying computational methods to model biological systems and interpret large-scale molecular data. Funded.",
       "Students pursuing research careers in computational biology and bioinformatics. Funded with a stipend."),
    # ── Department of Pathology ──
    _p("cwru-molecular-cellular-biology-disease-ms", _MED, "Master of Science in Molecular and Cellular Biology of Disease", "Disease Biology", "masters", 24,
       "Department of Pathology", "26.09",
       "Graduate study of the cellular and molecular mechanisms of human disease, connecting pathology with cell and molecular biology.",
       "Students who want a research-oriented master's in disease mechanisms as a step toward doctoral or professional study."),
    _p("cwru-pathology-phd", _MED, "Doctor of Philosophy in Pathology", "Pathology", "phd", 60,
       "Department of Pathology", "26.09",
       "Doctoral research on the cellular and molecular basis of disease — cancer, immunity, and tissue injury — bridging basic science and diagnostic medicine. Funded.",
       "Students pursuing research careers in experimental pathology and disease biology. Funded with a stipend."),
    # ── Department of Pharmacology ──
    _p("cwru-pharmacology-ms", _MED, "Master of Science in Pharmacology", "Pharmacology", "masters", 24,
       "Department of Pharmacology", "26.10",
       "Graduate study of drug action, receptor signaling, and therapeutics, combining coursework with laboratory research.",
       "Students seeking advanced pharmacology training before doctoral study or a research career in drug discovery."),
    _p("cwru-pharmacology-phd", _MED, "Doctor of Philosophy in Pharmacology", "Pharmacology", "phd", 60,
       "Department of Pharmacology", "26.10",
       "Doctoral research on the molecular mechanisms of drug action, signal transduction, and the development of new therapeutics. Funded.",
       "Students pursuing research careers in pharmacology and drug discovery. Funded with a stipend."),
    _p("cwru-translational-pharmaceutical-science-ms", _MED, "Master of Science in Translational Pharmaceutical Science", "Pharmaceutical Science", "masters", 24,
       "Department of Pharmacology", "51.20",
       "Applied study of how drugs move from discovery through development, regulation, and clinical use, oriented to the pharmaceutical and biotech industries.",
       "Science graduates targeting drug-development, regulatory, or pharmaceutical-industry careers."),
    # ── Physician Assistant Program ──
    _p("cwru-physician-assistant-mspas", _MED, "Master of Science in Physician Assistant Studies", "Physician Assistant", "masters", 27,
       "Physician Assistant Program", "51.09",
       "An accredited professional program combining basic-science and clinical coursework with supervised clinical rotations, preparing graduates to practice as physician assistants across specialties.",
       "Students pursuing certification and licensure to practice as a physician assistant."),
    # ── Department of Physiology and Biophysics ──
    _p("cwru-medical-physiology-ms", _MED, "Master of Science in Medical Physiology", "Medical Physiology", "masters", 24,
       "Department of Physiology and Biophysics", "26.09",
       "An intensive year of medical-level physiology across organ systems, designed to strengthen preparation for medical and other health-professions schools.",
       "Health-professions applicants who want to demonstrate mastery of physiology before entering medical or professional school.",
       delivery_format="hybrid"),
    _p("cwru-physiology-ms", _MED, "Master of Science in Physiology", "Physiology", "masters", 24,
       "Department of Physiology and Biophysics", "26.09",
       "Graduate study of how cells, organs, and systems function, combining physiology coursework with laboratory research.",
       "Students seeking advanced physiology training for research or as a bridge to doctoral or professional study."),
    _p("cwru-aerospace-physiology-ms", _MED, "Master of Science in Aerospace Physiology", "Aerospace Physiology", "masters", 24,
       "Department of Physiology and Biophysics", "26.09",
       "The physiology of the human body under the extreme conditions of flight and space — hypoxia, acceleration, and pressure — and how to protect against them.",
       "Students drawn to human performance in aviation, space, and other extreme environments.",
       delivery_format="hybrid"),
    _p("cwru-physiology-biophysics-phd", _MED, "Doctor of Philosophy in Physiology and Biophysics", "Physiology Biophysics", "phd", 60,
       "Department of Physiology and Biophysics", "26.09",
       "Doctoral research on the physical and molecular mechanisms of physiological function, from ion channels and membranes to whole-organ systems. Funded.",
       "Students pursuing research careers in physiology and biophysics. Funded with a stipend."),
    # ── Department of Population and Quantitative Health Sciences ──
    _p("cwru-public-health-mph", _MED, "Master of Public Health", "Public Health", "masters", 24,
       "Department of Population and Quantitative Health Sciences", "51.22",
       "Professional training across the core public-health disciplines — epidemiology, biostatistics, health policy, and behavioral and environmental health — with an applied practicum.",
       "Students pursuing careers in public health practice, policy, or program leadership."),
    _p("cwru-clinical-research-ms", _MED, "Master of Science in Clinical Research", "Clinical Research", "masters", 24,
       "Department of Population and Quantitative Health Sciences", "51.14",
       "Training in the design, conduct, and analysis of clinical studies, from trial methodology and biostatistics to research ethics and regulation.",
       "Clinicians and scientists who want to lead rigorous patient-oriented and clinical research."),
    _p("cwru-biomedical-health-informatics-ms", _MED, "Master of Science in Biomedical and Health Informatics", "Health Informatics", "masters", 24,
       "Department of Population and Quantitative Health Sciences", "51.27",
       "The science of acquiring, managing, and analyzing biomedical and clinical data to improve care, spanning clinical, imaging, and translational informatics.",
       "Students who want to turn health data into better clinical decisions and research."),
    _p("cwru-biomedical-health-informatics-phd", _MED, "Doctor of Philosophy in Biomedical and Health Informatics", "Health Informatics", "phd", 60,
       "Department of Population and Quantitative Health Sciences", "51.27",
       "Doctoral research developing computational and statistical methods for biomedical, clinical, and public-health data. Funded.",
       "Students pursuing research careers advancing biomedical and health informatics. Funded with a stipend."),
    _p("cwru-epidemiology-biostatistics-ms", _MED, "Master of Science in Epidemiology and Biostatistics", "Epidemiology Biostatistics", "masters", 24,
       "Department of Population and Quantitative Health Sciences", "51.22",
       "Quantitative training in the study of disease distribution and in the statistical methods used to analyze health data and design studies.",
       "Students who want the analytical toolkit to investigate the causes and patterns of disease in populations."),
    _p("cwru-epidemiology-biostatistics-phd", _MED, "Doctor of Philosophy in Epidemiology and Biostatistics", "Epidemiology Biostatistics", "phd", 60,
       "Department of Population and Quantitative Health Sciences", "51.22",
       "Doctoral research advancing epidemiologic and statistical methods and applying them to population-health questions. Funded.",
       "Students pursuing research careers in epidemiology and biostatistics. Funded with a stipend."),
    _p("cwru-clinical-translational-science-phd", _MED, "Doctor of Philosophy in Clinical Translational Science", "Translational Science", "phd", 60,
       "Department of Population and Quantitative Health Sciences", "51.14",
       "Doctoral research on moving discoveries from the laboratory into clinical practice and population health, integrating trial design, implementation, and outcomes science. Funded.",
       "Clinicians and scientists pursuing research careers that translate science into improved patient care. Funded with a stipend."),
    # ══ FRANCES PAYNE BOLTON SCHOOL OF NURSING ══
    _p("cwru-nursing-bsn", _NURS, "Bachelor of Science in Nursing", "Nursing", "bachelors", 48,
       "Frances Payne Bolton School of Nursing", "51.38",
       "A four-year BSN combining nursing science, the liberal arts, and clinical rotations, preparing graduates for RN licensure and professional practice.",
       "Undergraduates preparing to become registered nurses with a strong science and liberal-arts foundation."),
    _p("cwru-nursing-mn", _NURS, "Master of Nursing", "Nursing", "masters", 24,
       "Frances Payne Bolton School of Nursing", "51.38",
       "A graduate-entry pathway for students who hold a bachelor's in another field to earn a nursing degree and qualify for RN licensure.",
       "Career-changers with a non-nursing bachelor's who want to become registered nurses at the graduate level."),
    _p("cwru-nursing-msn", _NURS, "Master of Science in Nursing", "Nursing", "masters", 24,
       "Frances Payne Bolton School of Nursing", "51.38",
       "Advanced-practice and specialty preparation across nurse-practitioner, midwifery, and related roles, combining graduate coursework with supervised clinical placements.",
       "Registered nurses pursuing advanced-practice licensure in a chosen population or specialty.",
       tracks=["Adult-Gerontology Acute Care NP", "Adult-Gerontology Primary Care NP", "Acute Care Pediatric NP", "Family NP", "Family Psychiatric-Mental Health NP", "Neonatal NP", "Nurse Midwifery", "Pediatric Primary Care NP", "Women's Health NP"],
       delivery_format="hybrid"),
    _p("cwru-nursing-dnp", _NURS, "Doctor of Nursing Practice", "Nursing Practice", "professional", 36,
       "Frances Payne Bolton School of Nursing", "51.38",
       "The terminal practice doctorate preparing advanced-practice nurses to lead clinical care, translate evidence into practice, and shape health systems.",
       "Advanced-practice nurses seeking the highest clinical practice degree and leadership roles.",
       delivery_format="hybrid"),
    _p("cwru-nursing-phd", _NURS, "Doctor of Philosophy in Nursing", "Nursing", "phd", 60,
       "Frances Payne Bolton School of Nursing", "51.38",
       "Doctoral research developing nursing science and preparing nurse scientists and faculty. Funded.",
       "Nurses pursuing research careers advancing nursing science. Funded with a stipend."),
    # ══ SCHOOL OF DENTAL MEDICINE ══
    _p("cwru-dental-medicine-dmd", _DENT, "Doctor of Dental Medicine", "Dental Medicine", "professional", 48,
       "School of Dental Medicine", "51.04",
       "A four-year professional program combining basic and dental sciences with extensive supervised patient care, preparing graduates for licensure as general dentists.",
       "Students pursuing licensure to practice as a general dentist."),
    _p("cwru-endodontics-msd", _DENT, "Master of Science in Dentistry in Endodontics", "Endodontics", "masters", 24,
       "School of Dental Medicine", "51.05",
       "Advanced clinical and research training in root-canal therapy and the diagnosis and management of diseases of the dental pulp and periradicular tissues.",
       "Dentists specializing in endodontics who want advanced clinical and research training."),
    _p("cwru-oral-maxillofacial-surgery-msd", _DENT, "Master of Science in Dentistry in Oral and Maxillofacial Surgery", "Oral Maxillofacial Surgery", "masters", 24,
       "School of Dental Medicine", "51.05",
       "Advanced training in the surgical management of diseases, injuries, and defects of the mouth, jaws, and face.",
       "Dentists pursuing the surgical specialty of oral and maxillofacial surgery."),
    _p("cwru-oral-medicine-msd", _DENT, "Master of Science in Dentistry in Oral Medicine", "Oral Medicine", "masters", 24,
       "School of Dental Medicine", "51.05",
       "Advanced training in the diagnosis and non-surgical management of oral diseases and the oral manifestations of systemic conditions.",
       "Dentists specializing in the medical management of oral and orofacial disease."),
    _p("cwru-orthodontics-msd", _DENT, "Master of Science in Dentistry in Orthodontics", "Orthodontics", "masters", 24,
       "School of Dental Medicine", "51.05",
       "Advanced clinical and research training in the diagnosis and correction of malocclusion and dentofacial and skeletal irregularities.",
       "Dentists specializing in orthodontics and dentofacial orthopedics."),
    _p("cwru-pediatric-dentistry-msd", _DENT, "Master of Science in Dentistry in Pediatric Dentistry", "Pediatric Dentistry", "masters", 24,
       "School of Dental Medicine", "51.05",
       "Advanced training in the oral health care of infants, children, adolescents, and patients with special health-care needs.",
       "Dentists specializing in the care of children and patients with special needs."),
    _p("cwru-periodontics-msd", _DENT, "Master of Science in Dentistry in Periodontics", "Periodontics", "masters", 24,
       "School of Dental Medicine", "51.05",
       "Advanced clinical and research training in the treatment of periodontal disease and in the placement and maintenance of dental implants.",
       "Dentists specializing in periodontics and implant therapy."),
    # ══ SCHOOL OF LAW ══
    _p("cwru-law-jd", _LAW, "Juris Doctor", "Law", "professional", 36,
       "Case Western Reserve University School of Law", "22.01",
       "The three-year professional degree that qualifies graduates to sit for the bar, grounding students in the common-law core — contracts, torts, property, constitutional law, criminal law, and civil procedure — alongside legal writing, clinics, and upper-level electives.",
       "Aspiring attorneys seeking bar-qualifying legal training and the doctrinal, clinical, and writing foundation to practice law.",
       delivery_format="hybrid"),
    _p("cwru-laws-llm", _LAW, "Master of Laws (LL.M.)", "Laws", "masters", 12,
       "Case Western Reserve University School of Law", "22.02",
       "A one-year master's that builds internationally educated lawyers' fluency in the U.S. legal system, with concentrations available in intellectual property, international business, and criminal justice.",
       "Lawyers trained outside the United States who want U.S. legal grounding, bar eligibility in some jurisdictions, or specialized advanced study.",
       delivery_format="hybrid"),
    _p("cwru-juridical-science-sjd", _LAW, "Doctor of Juridical Science (S.J.D.)", "Juridical Science", "phd", 60,
       "Case Western Reserve University School of Law", "22.02",
       "The highest research degree in law, culminating in a book-length dissertation of original legal scholarship in a chosen field of specialization under close faculty supervision.",
       "LL.M. graduates and legal scholars pursuing an academic or research career through sustained, doctoral-level legal research."),
    _p("cwru-legal-studies-ml", _LAW, "Master of Law", "Legal Studies", "masters", 12,
       "Case Western Reserve University School of Law", "22.02",
       "A master's that gives non-lawyers a working command of U.S. law and legal reasoning without the full J.D., with coursework tailored to each student's professional field.",
       "Professionals and graduate students who need legal literacy for their field — or a credential before applying to J.D. programs — but do not intend to practice law.",
       delivery_format="hybrid"),
    _p("cwru-financial-integrity-ma", _LAW, "Master of Arts in Financial Integrity", "Financial Integrity", "masters", 12,
       "Case Western Reserve University School of Law", "22.02",
       "A specialized master's in the law, policy, and practice of preventing illicit international financial flows — anti-money-laundering, counter-terrorist-financing, sanctions, and financial-crime compliance.",
       "Compliance, banking, and law-enforcement professionals who want to specialize in detecting and preventing money laundering and financial crime."),
    _p("cwru-patent-practice-ma", _LAW, "Master of Arts in Patent Practice", "Patent Practice", "masters", 12,
       "Case Western Reserve University School of Law", "22.02",
       "A master's built for scientists and engineers, training them to draft and prosecute patent applications before the U.S. Patent and Trademark Office and to qualify as registered patent agents.",
       "STEM graduates who want to enter patent practice as registered patent agents without earning a full law degree.",
       delivery_format="hybrid"),
    _p("cwru-compliance-risk-management-mcrm", _LAW, "Master of Compliance and Risk Management", "Compliance and Risk Management", "masters", 24,
       "Case Western Reserve University School of Law", "22.02",
       "A professional master's in regulatory compliance and enterprise risk, covering the legal frameworks, ethics, controls, and governance organizations use to meet regulatory obligations across industries.",
       "Working professionals building or advancing careers in corporate compliance, risk management, and regulatory affairs.",
       delivery_format="hybrid"),
    # ══ JACK, JOSEPH AND MORTON MANDEL SCHOOL OF APPLIED SOCIAL SCIENCES ══
    _p("cwru-social-work-msw", _MANDEL, "Master of Social Work", "Social Work", "masters", 24,
       "Jack, Joseph and Morton Mandel School of Applied Social Sciences", "44.07",
       "The professional degree for social work practice, pairing clinical and community coursework with supervised field placements across paths from adult behavioral health to community practice for social change.",
       "Students preparing to become licensed social workers in clinical, behavioral-health, child-and-family, or community-practice settings.",
       tracks=["Adult Behavioral Health", "Child and Family Practice", "Community Practice for Social Change", "Trauma and Healing"],
       delivery_format="hybrid"),
    _p("cwru-nonprofit-organizations-mno", _MANDEL, "Master of Nonprofit Organizations", "Nonprofit Organizations", "masters", 24,
       "Jack, Joseph and Morton Mandel School of Applied Social Sciences", "44.02",
       "A management master's for the nonprofit and philanthropic sector, covering fundraising and development, governance, financial management, and the leadership of mission-driven organizations.",
       "Emerging and current nonprofit leaders who want formal management training to lead mission-driven organizations."),
    _p("cwru-social-welfare-phd", _MANDEL, "Doctor of Philosophy in Social Welfare", "Social Welfare", "phd", 60,
       "Jack, Joseph and Morton Mandel School of Applied Social Sciences", "44.07",
       "A research doctorate training scholars to conduct original research on social problems, interventions, and welfare policy, culminating in a dissertation. Funded.",
       "Aspiring social-work researchers and professors pursuing original scholarship on social welfare and social policy. Funded with a stipend."),
]

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

# ── Tuition (verified 2025-26, CWRU Student Financial Services) ──────────────
_TUITION_UG = 68660  # 2025-26 undergraduate tuition
# CWRU School of Graduate Studies bills $2,316/credit with a $27,774/term full-time
# maximum, so the full-time academic-year matcher scalar is $27,774 x 2 = $55,548. This
# is the published full-time graduate rate (distinct from the undergraduate sticker), not
# the undergrad number copied down. Applies to academic master's administered through the
# School of Graduate Studies.
_TUITION_GRAD_ANNUAL = 55548
_FT_CREDITS = 24  # a full-time academic year at CWRU's 12-credit/term graduate maximum
_TUITION_URL = "https://case.edu/studentaccounts/tuition-fees/graduateprofessional-tuition-fees"
_GRAD_STUDIES_URL = f"{_TUITION_URL}/school-graduate-studies"

# Named-school per-credit graduate tuition (2025-26 unless noted). The annual matcher
# scalar is the per-credit rate x 24 (a full-time academic year), documented in cost_data;
# never the undergraduate sticker copied down. slug -> (per_credit_usd, source_url)
_PER_CREDIT: dict[str, tuple[int, str]] = {
    "cwru-mba": (1661, f"{_TUITION_URL}/weatherhead-school-management"),
    "cwru-accounting-macc": (1648, f"{_TUITION_URL}/weatherhead-school-management"),
    "cwru-finance-mfin": (1974, f"{_TUITION_URL}/weatherhead-school-management"),
    "cwru-supply-chain-management-mscm": (1754, f"{_TUITION_URL}/weatherhead-school-management"),
    "cwru-nursing-msn": (2377, f"{_TUITION_URL}/frances-payne-bolton-school-nursing"),
    "cwru-nursing-dnp": (2497, f"{_TUITION_URL}/frances-payne-bolton-school-nursing"),
    "cwru-nonprofit-organizations-mno": (1650, f"{_TUITION_URL}/jack-joseph-and-morton-mandel-school-applied-social"),
    "cwru-laws-llm": (2692, f"{_TUITION_URL}/school-law"),
    "cwru-anesthesia-msa": (2149, f"{_TUITION_URL}/school-medicine"),
    # Genetic Counseling: most recent PUBLISHED per-credit rate is 2026-27.
    "cwru-genetic-counseling-ms": (2384, "https://case.edu/medicine/genetics/graduate-programs/genetic-counseling-training-program/tuition-fees-and-financial-aid"),
}

# Professional / named programs with a published ANNUAL full-time rate (2025-26).
# slug -> (annual_usd, source_url)
_PROF_ANNUAL: dict[str, tuple[int, str]] = {
    "cwru-medicine-md-university": (72526, f"{_TUITION_URL}/school-medicine"),
    "cwru-dental-medicine-dmd": (89668, f"{_TUITION_URL}/school-dental-medicine"),
    "cwru-law-jd": (64600, f"{_TUITION_URL}/school-law"),
    # MSW full-time flat semester rate $24,750 x 2 = $49,500/yr (verified 2025-26).
    "cwru-social-work-msw": (49500, f"{_TUITION_URL}/jack-joseph-and-morton-mandel-school-applied-social"),
}

# The Cleveland Clinic Lerner College of Medicine M.D. is tuition-FREE — a full-tuition
# scholarship for every matriculant (verified: case.edu/medicine + Cleveland Clinic).
_FREE_SLUGS = {"cwru-medicine-md-lerner"}

# Programs whose per-program tuition CWRU does not publish in a verifiable form → the
# annual scalar is honestly OMITTED with reason rather than guessed.
_TUITION_OMIT: dict[str, str] = {
    # Postdoctoral M.S.D. dental specialties: CWRU School of Dental Medicine does not
    # publish a per-program annual tuition for these advanced/postdoctoral clinical
    # specialty programs in a verifiable form (residents are typically stipended).
    "cwru-endodontics-msd": "postdoctoral M.S.D. dental specialty; no verifiable per-program tuition published",
    "cwru-oral-maxillofacial-surgery-msd": "postdoctoral M.S.D. dental specialty; no verifiable per-program tuition published",
    "cwru-oral-medicine-msd": "postdoctoral M.S.D. dental specialty; no verifiable per-program tuition published",
    "cwru-orthodontics-msd": "postdoctoral M.S.D. dental specialty; no verifiable per-program tuition published",
    "cwru-pediatric-dentistry-msd": "postdoctoral M.S.D. dental specialty; no verifiable per-program tuition published",
    "cwru-periodontics-msd": "postdoctoral M.S.D. dental specialty; no verifiable per-program tuition published",
    # Physician Assistant M.S.: CWRU publishes only a program-year tuition-and-fees figure,
    # not a clean annual tuition, so the annual scalar is omitted rather than mixing fees in.
    "cwru-physician-assistant-mspas": "CWRU publishes only a combined program-year tuition-and-fees figure for the PA program, not a clean annual tuition; omitted rather than guessed",
    # Weatherhead specialized master's with no separately published per-credit/annual rate.
    "cwru-business-analytics-mbai": "Weatherhead does not publish a separate per-credit/annual tuition for this specialized master's in a verifiable form",
    "cwru-leadership-organizational-change-msloc": "Weatherhead does not publish a separate per-credit/annual tuition for this specialized master's in a verifiable form",
    # School of Law specialized non-J.D./LL.M. master's with no separately published rate.
    "cwru-legal-studies-ml": "CWRU School of Law does not publish a separate verifiable per-program tuition for this master's",
    "cwru-financial-integrity-ma": "CWRU School of Law does not publish a separate verifiable per-program tuition for this master's",
    "cwru-patent-practice-ma": "CWRU School of Law does not publish a separate verifiable per-program tuition for this master's",
    "cwru-compliance-risk-management-mcrm": "CWRU School of Law does not publish a separate verifiable per-program tuition for this master's",
    # Non-research doctorates in the phd degree bucket: unlike a funded research Ph.D., the
    # S.J.D. (research law doctorate) and the D.M.A. (performance doctorate) are NOT covered by
    # a verifiable full-tuition-waiver-plus-stipend package, so their scalar is omitted-with-reason
    # rather than asserting tuition=0/funded (which would falsely tell students they are free).
    "cwru-juridical-science-sjd": "The S.J.D. is a research law doctorate with no verifiable full-tuition-waiver funding convention; tuition omitted rather than marked funded/free",
    "cwru-historical-performance-practice-dma": "The D.M.A. is a performance doctorate with no verifiable full-tuition-waiver funding convention; tuition omitted rather than marked funded/free",
}


def _cost_data(spec: dict) -> dict:
    """The program's cost_data blob (annual matcher scalar + verified basis/citation)."""
    slug, dt = spec["slug"], spec["degree_type"]
    if slug in _TUITION_OMIT:
        return {"tuition_usd": None, "omitted_reason": _TUITION_OMIT[slug]}
    if slug in _FREE_SLUGS:
        return {
            "tuition_usd": 0, "funded": True,
            "note": "The Cleveland Clinic Lerner College of Medicine awards a full-tuition scholarship to every matriculant; students pay living expenses only.",
            "source": "CWRU School of Medicine / Cleveland Clinic",
            "source_url": "https://case.edu/medicine/md/admission/faqs", "year": "2025-26",
        }
    if dt == "bachelors":
        return {
            "tuition_usd": _TUITION_UG, "funded": False,
            "source": "CWRU Student Financial Services (undergraduate tuition)",
            "source_url": "https://case.edu/studentaccounts/tuition-fees/undergraduate-tuition-fees", "year": "2025-26",
        }
    if dt == "phd" or slug == "cwru-mstp-mdphd":
        return {
            "tuition_usd": 0, "funded": True,
            "note": "Research doctorate — tuition is covered by a full funding package (tuition waiver plus stipend) for admitted students.",
            "source": "CWRU School of Graduate Studies", "source_url": _GRAD_STUDIES_URL, "year": "2025-26",
        }
    if slug in _PROF_ANNUAL:
        annual, url = _PROF_ANNUAL[slug]
        return {"tuition_usd": annual, "funded": False, "source": "CWRU Student Financial Services", "source_url": url, "year": "2025-26"}
    if slug in _PER_CREDIT:
        per_credit, url = _PER_CREDIT[slug]
        year = "2026-27" if slug == "cwru-genetic-counseling-ms" else "2025-26"
        return {
            "tuition_usd": per_credit * _FT_CREDITS, "funded": False,
            "per_credit_usd": per_credit, "full_time_credits_per_year": _FT_CREDITS,
            "basis": f"Annualized from CWRU's published per-credit tuition (${per_credit}/credit) at a {_FT_CREDITS}-credit full-time academic year",
            "source": "CWRU Student Financial Services", "source_url": url, "year": year,
        }
    # Remaining graduate master's are administered through the School of Graduate Studies.
    return {
        "tuition_usd": _TUITION_GRAD_ANNUAL, "funded": False,
        "per_credit_usd": 2316, "full_time_credits_per_year": _FT_CREDITS,
        "basis": "CWRU School of Graduate Studies full-time academic-year tuition ($2,316/credit, capped at $27,774/term)",
        "source": "CWRU Student Financial Services (School of Graduate Studies)", "source_url": _GRAD_STUDIES_URL, "year": "2025-26",
    }


def _has_tuition(spec: dict) -> bool:
    return spec["slug"] not in _TUITION_OMIT


# ── external_reviews (MBAn shape) — GATHERED → SUMMARIZED → CITED ──────────────
# Themes are aggregated and paraphrased from real third-party coverage (U.S. News,
# Poets&Quants, Crain's Cleveland Business, Law School Transparency/LawHub, SCImago,
# Blue Ridge Institute, Cleveland Clinic newsroom) plus school-reported ABA/outcomes
# data — never fabricated quotes/ratings, every source resolves, and cautions are
# included. Each program carries >= 2 independent third-party domains. Programs without
# such coverage record external_reviews as an honest omission (coverage-gated).
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
    "cwru-law-jd": _reviews(
        "Case Western Reserve University School of Law is a solid national school (U.S. News 2025-26: #100 tie of 194) that punches above its overall rank in health law and international law and posts strong overall employment; first-time bar passage trails top-tier schools and placement is regionally concentrated.",
        [
            ("Rising overall rank", "mixed", "Ranked #100 (tie) of 194 in U.S. News 2025-26 Best Law Schools, up seven spots year-over-year — the largest jump of Ohio's nine law schools (Crain's Cleveland Business)."),
            ("Health-law and international-law strength", "positive", "U.S. News 2025-26 specialty tables rank CWRU #13 in Health Care Law and #13 in International Law — far above its overall rank."),
            ("Strong employment outcomes", "positive", "For the Class of 2024, 98.7% of graduates with known status (152 of 154) were employed or in further graduate study, per the school's ABA-reported employment statistics."),
            ("Well-regarded part-time program", "positive", "The part-time J.D. ranks #19 (tie) of 78 in U.S. News Part-time Law (2025-26)."),
            ("Bar passage trails elite peers", "caution", "First-time bar-pass rates sit below national top-20 schools per ABA 509 / Law School Transparency data — a consideration to verify on the current ABA 509 report."),
            ("Regional placement", "caution", "Outside its health- and international-law specialties, placement is concentrated in Ohio and the Midwest rather than national big-law markets."),
        ],
        [
            ("U.S. News — Best Law Schools (CWRU)", "https://www.usnews.com/best-graduate-schools/top-law-schools/case-western-reserve-university-03123"),
            ("Crain's Cleveland Business — Ohio law schools", "https://www.crainscleveland.com/education/ccl-law-schools-ohio-20260421/"),
            ("CWRU Law — ABA employment statistics (Class of 2024)", "https://case.edu/law/students/career-development/prospective-students/employment-statistics-2024"),
            ("Law School Transparency / LawHub — CWRU ABA data", "https://app.lawhub.org/schools/casewestern/aba"),
        ],
    ),
    "cwru-mba": _reviews(
        "Weatherhead's full-time MBA is a small, mid-tier program (U.S. News 2025-26 ~#66; Poets&Quants #63 in 2023-24) whose intimate cohort and specialty concentrations are genuine strengths but whose modest scale and mid-pack placement are honest limitations; its online MBA is notably stronger.",
        [
            ("Full-time rank mid-tier", "mixed", "U.S. News 2025-26 placed the full-time MBA around #66 (up two spots); Poets&Quants ranked it #63 in its 2023-24 top-100 list."),
            ("Online MBA is the standout", "positive", "Weatherhead's online MBA rose to #11 in the Poets&Quants 2026 ranking of top U.S. online MBA programs."),
            ("Small, personalized cohort", "mixed", "Poets&Quants describes a small full-time cohort (roughly 45-50 students) enabling close faculty contact — a plus for attention, a minus for network scale and recruiter draw."),
            ("High international share", "mixed", "Per Poets&Quants the full-time class is heavily international (~59%), relevant for students weighing cohort composition and network."),
            ("Part-time program climbing", "positive", "The part-time MBA jumped ten spots to #40 in U.S. News 2025-26."),
            ("Limited public salary transparency", "caution", "Poets&Quants notes Weatherhead lists hiring firms rather than headline salary/placement stats, so median-salary and three-month-placement figures are not readily published."),
        ],
        [
            ("U.S. News — Best Business Schools (Weatherhead)", "https://www.usnews.com/best-graduate-schools/top-business-schools/case-western-reserve-university-01169"),
            ("Poets&Quants — Weatherhead school profile", "https://poetsandquants.com/school-profile/case-western-reserve-university-weatherhead-school-of-management/"),
        ],
    ),
    "cwru-social-work-msw": _reviews(
        "The Mandel School is one of the nation's elite social-work schools — ranked #9 in the most recent U.S. News social-work survey and #1 in Ohio — though the ranking cadence is biennial and the rank is reputation-weighted rather than outcome-weighted.",
        [
            ("Top-10 nationally", "positive", "Ranked #9 among nearly 300 accredited programs in the most recent U.S. News social-work survey; #1 in Ohio."),
            ("Ranking cadence caveat", "caution", "U.S. News ranks social-work schools at most biennially, so the #9 figure reflects the latest available survey rather than a fresh annual re-rank."),
            ("Historic, high-reputation school", "positive", "One of the oldest schools of applied social sciences in the U.S. (founded 1915), underpinning durable academic-reputation scores."),
            ("Independent reputation corroboration", "positive", "Independent aggregators of social-work/welfare program reputation list CWRU among top U.S. programs, consistent with its U.S. News standing."),
            ("Reputation-weighted methodology", "mixed", "The U.S. News social-work ranking is driven heavily by peer academic-reputation surveys rather than measured graduate earnings, so it speaks to prestige more than outcomes."),
        ],
        [
            ("U.S. News — Best Colleges/Grad (CWRU)", "https://www.usnews.com/best-colleges/case-western-reserve-university-3024"),
            ("SocialPsychology.org — U.S. social-work/welfare program ranking", "https://www.socialpsychology.org/gsocwork.htm"),
            ("CWRU — Mandel School maintains #9 (attrib. U.S. News)", "https://case.edu/news/mandel-school-maintains-9-spot-us-news-graduate-school-rankings"),
        ],
    ),
    "cwru-medicine-md-university": _reviews(
        "CWRU School of Medicine is a top-tier research medical school — placed in U.S. News' Tier 1 for research (2025) and a top-25 NIH-funded institution — with a distinctive tuition-free Cleveland Clinic Lerner College physician-investigator track; the main caveats are U.S. News' new tier methodology and federal research-funding exposure.",
        [
            ("Tier 1 research school", "positive", "In the U.S. News 2025 tier methodology, CWRU is among ~16 medical schools in Tier 1 for research, alongside schools such as Vanderbilt, Northwestern, and Mayo."),
            ("Top-25 NIH funding", "positive", "Received $294.7 million in NIH funding and ranked 22nd nationally per the Blue Ridge Institute for Medical Research FY2022 report."),
            ("Tuition-free Lerner track", "positive", "The Cleveland Clinic Lerner College of Medicine — a five-year physician-investigator program — has offered a full-tuition scholarship to all students since 2008."),
            ("Regional research anchor", "positive", "Independent local coverage (Crain's Cleveland) confirms CWRU's standing as a top research medical school and a major Cleveland biomedical-research engine."),
            ("Ranking methodology change", "caution", "U.S. News replaced numeric med-school ranks with a four-tier system in 2025 after many schools withdrew; 'Tier 1' is a band of ~16 schools, not a precise number."),
            ("Federal-funding exposure", "caution", "Local reporting notes CWRU, like peers, is navigating potential federal/NIH research-funding cuts — a real risk to a school so reliant on NIH dollars."),
        ],
        [
            ("U.S. News — Best Medical Schools (CWRU)", "https://www.usnews.com/best-graduate-schools/top-medical-schools/case-western-reserve-university-04086"),
            ("Crain's Cleveland Business — top research med school", "https://www.crainscleveland.com/health-care/case-western-reserve-top-us-news-med-school-research/"),
            ("Cleveland Clinic Newsroom — Lerner free tuition since 2008", "https://newsroom.clevelandclinic.org/2018/08/20/cleveland-clinic-lerner-college-of-medicine-has-offered-free-tuition-since-2008"),
            ("Signal Cleveland — federal research-cut exposure", "https://signalcleveland.org/how-case-western-reserve-cwru-ohio-research-universities-trump-administration-cuts/"),
        ],
    ),
    "cwru-nursing-msn": _reviews(
        "Frances Payne Bolton is a nationally elite nursing school: its master's ranks #15 in U.S. News, several nurse-practitioner specialties rank top-10, and its DNP ranks #14; the main caveat is that many headline figures are specialty-specific rather than a single overall rank.",
        [
            ("Top-15 master's program", "positive", "The M.S.N. program is ranked #15 nationally in the U.S. News nursing-master's ranking (2025/2026 editions)."),
            ("Elite NP specialties", "positive", "U.S. News specialty ranks include Adult Primary Care NP #4 and Acute Care NP #7, with strength across multiple NP tracks."),
            ("Strong doctoral program", "positive", "The Doctor of Nursing Practice ranks #14 (up from #17), with the DNP Leadership specialty at #6."),
            ("Historic, high-reputation school", "positive", "Frances Payne Bolton is one of the oldest and most established U.S. nursing schools, underpinning durable peer-reputation scores."),
            ("Specialty-fragmented picture", "caution", "'Top-5' claims apply to individual NP specialties, not the overall M.S.N. (which is #15) — be precise about which sub-ranking is cited."),
            ("Reputation-weighted methodology", "mixed", "Like other U.S. News grad-nursing ranks, results lean heavily on academic peer reputation rather than direct graduate-outcome metrics."),
        ],
        [
            ("U.S. News — Best Nursing Schools (CWRU)", "https://www.usnews.com/best-graduate-schools/top-nursing-schools/case-western-reserve-university-33220"),
            ("AllNurses — CWRU school profile", "https://allnurses.com/schools/ohio/case-western-reserve-university-r2097/"),
        ],
    ),
    "cwru-biomedical-engineering-bse": _reviews(
        "CWRU's biomedical engineering is one of its strongest programs nationally — the graduate program ranks #19 and the undergraduate program #18 in U.S. News (2025) — and is a recognized research strength within the Case School of Engineering, though it is a relative bright spot rather than a reflection of the whole college.",
        [
            ("Top-20 graduate BME", "positive", "The biomedical/bioengineering graduate program ranked #19 in the U.S. News 2025 Best Graduate Schools (Engineering), up two positions."),
            ("Top-20 undergraduate BME", "positive", "The undergraduate biomedical engineering program ranked #18 (up one) in the U.S. News 2025 rankings."),
            ("Independent research corroboration", "positive", "The SCImago Institutions Rankings (Biomedical Engineering, U.S.) list CWRU among ranked institutions, corroborating its research standing beyond reputation surveys."),
            ("Program-specific strength", "mixed", "BME's ~#18-19 national placement is stronger than CWRU's overall engineering-school rank, so it is a bright spot within Case Engineering rather than a reflection of the whole college."),
            ("Mixed methodology basis", "mixed", "The U.S. News graduate-engineering specialty rank is reputation-survey-driven while the SCImago corroboration is bibliometric — best read together."),
        ],
        [
            ("U.S. News — Best Engineering Schools (CWRU)", "https://www.usnews.com/best-graduate-schools/top-engineering-schools/case-western-reserve-university-02138"),
            ("SCImago Institutions Rankings — Biomedical Engineering (USA)", "https://www.scimagoir.com/rankings.php?area=2204"),
        ],
    ),
}


def _outcomes_kind(spec: dict) -> str:
    if spec["slug"] in _FOS_OUTCOMES:
        return "fos"
    if spec["degree_type"] in ("bachelors", "masters", "phd", "professional"):
        return "institution"
    return "none"


def _program_standard(spec: dict) -> dict:
    omitted: list[str] = ["tracks"] if "tracks" not in spec else []
    omitted += ["class_profile.cohort_size", "faculty_contacts.lead"]
    if spec["slug"] not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    if not _has_tuition(spec):
        omitted += ["cost_data.tuition_usd", "cost_data.source"]
    kind = _outcomes_kind(spec)
    if kind == "fos":
        omitted += ["outcomes_data.employment_rate", "outcomes_data.top_industries", "outcomes_data.conditions"]
    elif kind == "institution":
        omitted.append("outcomes_data.employment_rate")
    return _standard(omitted)


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich Case Western Reserve to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Case Western Reserve is absent — safe on fresh/CI databases.
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
    # Lead media_gallery with the verified hero campus photo (seed's first gallery photo),
    # preserving any existing gallery entries behind it (idempotent dedupe).
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
        p.delivery_format = spec.get("delivery_format", "on_campus")
        cost = _cost_data(spec)
        p.tuition = cost.get("tuition_usd")
        p.cost_data = cost
        # Requirements by tier / school. Dental (AADSAS/DAT), PA (CASPA), and MD (AMCAS/MCAT)
        # each use their own centralized application system — never the medical-school template
        # on a dental or PA program.
        dt = spec["degree_type"]
        if spec["school"] == _LAW and dt == "professional":
            p.application_requirements = dict(_REQ_LAW)
        elif spec["slug"] == "cwru-physician-assistant-mspas":
            p.application_requirements = dict(_REQ_PA)
        elif spec["school"] == _DENT and dt == "professional":
            p.application_requirements = dict(_REQ_DENTAL)
        elif spec["school"] == _MED and dt == "professional":
            p.application_requirements = dict(_REQ_MED)
        elif dt == "bachelors":
            p.application_requirements = dict(_REQ_UNDERGRAD)
        else:
            p.application_requirements = dict(_REQ_GRAD)
        # Outcomes: Field-of-Study where published, else institution-wide proxy.
        fos = _FOS_OUTCOMES.get(spec["slug"])
        if fos is not None:
            salary, cip = fos
            p.outcomes_data = {
                "median_salary": salary,
                "scope": "program",
                "cip": cip,
                "source": "U.S. Dept. of Education College Scorecard — Field of Study",
                "source_url": "https://collegescorecard.ed.gov/school/?201645-Case-Western-Reserve-University",
            }
        else:
            p.outcomes_data = dict(_OUTCOMES_INSTITUTION)
        p.outcomes_data["_standard"] = _program_standard(spec)
        p.cip_code = spec["cip"]
        p.who_its_for = spec["who"]
        if "tracks" in spec:
            p.tracks = spec["tracks"]
        else:
            p.tracks = None
        p.class_profile = None
        p.faculty_contacts = None
        p.external_reviews = _REVIEWS_BY_SLUG.get(spec["slug"])
        if dt == "bachelors":
            p.application_deadline = date(2027, 1, 15)
        elif spec["school"] == _LAW and dt == "professional":
            p.application_deadline = date(2027, 3, 1)
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
