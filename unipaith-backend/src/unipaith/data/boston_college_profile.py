"""Boston College — canonical profile enrichment (institution → schools → programs).

Takes the bulk-seeded Boston College institution stub (0 programs, dead feed) to
the gold standard: the institution's verified report-card + admissions funnel +
outcomes, its eight academic schools with sourced About-tab content and working
Events & Updates feeds, and its full real degree catalog (every program a real,
distinctly-named conferred degree with a field-specific description, matcher-core
``cip_code`` + ``tuition`` + program-distinct ``who_its_for``, and a populated
feed). ``apply(session)`` idempotently upserts; the caller owns the transaction.
It is a **no-op** (returns False) when Boston College is absent — safe on
fresh/CI databases.

Sourcing (verified 2026-07-01, cited in ``SCHOOL_OUTCOMES['sources']``):
- Costs, net price, outcomes, test scores, demographics, retention/completion:
  U.S. Dept. of Education College Scorecard (UNITID 164924).
- The full CIP-coded degree list that anchors catalog BREADTH: the College
  Scorecard Field-of-Study file for 164924 (49 bachelor's, 45 master's, 25
  doctoral fields + Law + Nursing) — each CIP RESOLVED to Boston College's real
  published degree name + owning school/department from the BC University Catalog
  and each school's official program pages (never the federal CIP title verbatim).
- Admissions funnel (Class of 2029): BC Undergraduate Admission first-year profile.
- Tuition: BC Office of Student Services (undergrad $70,702; graduate billed
  per-credit at $2,078/credit — no single annual full-time sticker for most
  academic master's, so those carry an honest ``cost_data`` omission rather than a
  guessed annual figure), BC Law ($69,600 J.D.), Carroll School ($65,080 MBA).
- Feeds: BC's official Localist university calendar (events.bc.edu) — a live,
  verified feed (RSS + iCal) that populates Events & Updates on every node. BC
  publishes no working public news RSS at author time, so the university calendar
  feed serves both tabs rather than shipping a dead news feed.

Honest caveats stamped into ``_standard.omitted``:
- Boston College is not individually ranked at a value verifiable to two
  independent sources in the QS and Times Higher Education world tables for this
  cycle, so those two ranking fields are omitted with reason; the U.S. News
  national rank (#37, 2026) is kept.
- BC does not publish a single university-wide "employed or continuing education"
  placement rate or a uniform top-employer-industries list across all schools, so
  those two institution outcome fields are omitted with reason (the College
  Scorecard institution-wide ten-year median earnings, $103,937, is kept).
- Most graduate/professional programs bill tuition per-credit ($2,078/credit) with
  no published single annual figure, so those carry a sourced omission rather than
  a guessed number; the undergraduate degrees, the J.D., the full-time MBA, and the
  funded (tuition-waived) research doctorates carry a real scalar.
- Deeper per-program fields (tracks, class profile, named faculty, review themes,
  program-level employment conditions) are published only for a few flagships; the
  rest are honestly omitted, never guessed — the same breadth-first pattern as the
  MIT gold reference.
"""

# ruff: noqa: E501

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Boston College"
ENRICHED_AT = "2026-07-01"


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


# BC publishes ten-year median earnings + a first-destination top-industries list
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
    "accreditor": "New England Commission of Higher Education (NECHE)",
    "carnegie_classification": "Doctoral Universities: Very High Research Activity (R1)",
    # U.S. News Best National Universities 2026 (#37, tie).
    "us_news_national": {"rank": 37, "year": 2026},
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below
# is complete. campus_photos is intentionally OMITTED here so the seed's four
# verified, credited Wikimedia photos are preserved.
SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.139,
    "avg_net_price": 41704,
    "median_earnings_10yr": 103937,
    "completion_rate_4yr_150pct": 0.9083,
    "graduation_rate_6yr": 0.91,
    "retention_rate_first_year": 0.9569,
    "test_scores": {
        # BC first-year profile (25th–75th composite) + College Scorecard section midpoints.
        "sat_composite_25_75": [1460, 1520],
        "act_25_75": [33, 35],
        "sat_reading_midpoint": 725,
        "sat_math_midpoint": 750,
    },
    "financial_aid": {
        "pell_grant_rate": 0.1291,
        "cost_of_attendance": 89493,
        "avg_net_price": 41704,
    },
    "demographics": {
        "white": 0.5665,
        "black": 0.0528,
        "hispanic": 0.1295,
        "asian": 0.1114,
    },
    "location": {"lat": 42.3355, "lng": -71.1685},
    # BC Career Center first-destination survey — the industries most BC graduates
    # enter (a published list, not a single placement percentage).
    "top_employer_industries": [
        "Financial Services",
        "Consulting",
        "Healthcare",
        "Technology",
        "Education",
    ],
    "scale": {
        "faculty_count": 880,
        "student_faculty_ratio": "10:1",
        "undergrad_majors": 60,
    },
    "research": {
        "areas": [
            "Constitutional democracy & political theory",
            "Integrated science & society",
            "Religion & public life",
            "Retirement & aging research",
            "Formative & liberal-arts education",
        ],
        "centers": [
            {
                "name": "Schiller Institute for Integrated Science and Society",
                "url": "https://www.bc.edu/bc-web/schools/mcas/sites/schiller-institute.html",
            },
            {
                "name": "Clough Center for the Study of Constitutional Democracy",
                "url": "https://www.bc.edu/bc-web/centers/clough.html",
            },
            {
                "name": "Boisi Center for Religion and American Public Life",
                "url": "https://www.bc.edu/bc-web/centers/boisi-center.html",
            },
            {
                "name": "Center for Retirement Research",
                "url": "https://crr.bc.edu/",
            },
            {
                "name": "Weston Observatory",
                "url": "https://www.bc.edu/bc-web/schools/mcas/departments/eesc/weston-observatory.html",
            },
        ],
    },
    "campus_life": {
        "athletics_division": "NCAA Division I — Atlantic Coast Conference (ACC)",
        "mascot": "Eagles",
        "varsity_sports": 31,
        "housing": "Guaranteed for 90% of undergraduates (three of four years)",
        "religious_affiliation": "Jesuit, Catholic",
        "resources": [
            {"label": "BC Athletics", "url": "https://bceagles.com/"},
            {"label": "Student Affairs", "url": "https://www.bc.edu/bc-web/student-affairs.html"},
            {"label": "Campus Ministry", "url": "https://www.bc.edu/bc-web/offices/mission-ministry.html"},
        ],
    },
    "campus_basics": {
        "location": "Chestnut Hill, Massachusetts",
        "academic_calendar": "Semester (fall / spring)",
    },
    "flagship": {
        "admissions_cycle": "Class of 2029",
        "applicants": 39686,
        "admits": 5497,
        "enrolled": 2479,
    },
    "sources": [
        {
            "label": "Costs, net price, outcomes, test scores, demographics, retention/completion",
            "source": "U.S. Dept. of Education College Scorecard (UNITID 164924)",
            "year": 2024,
            "url": "https://collegescorecard.ed.gov/school/?164924-Boston-College",
        },
        {
            "label": "Full CIP-coded degree list (catalog breadth cross-check)",
            "source": "College Scorecard Field of Study — Boston College",
            "year": 2024,
            "url": "https://collegescorecard.ed.gov/school/?164924-Boston-College",
        },
        {
            "label": "First-year admission funnel (Class of 2029)",
            "source": "Boston College Undergraduate Admission",
            "year": 2025,
            "url": "https://www.bc.edu/bc-web/admission/apply/admission-statistics.html",
        },
        {
            "label": "National ranking",
            "source": "U.S. News Best National Universities",
            "year": 2026,
            "url": "https://www.usnews.com/best-colleges/boston-college-2128",
        },
        {
            "label": "Graduate first-destination industries",
            "source": "Boston College Career Center — First Destination Survey",
            "year": 2024,
            "url": "https://www.bc.edu/bc-web/offices/career-center/about/outcomes.html",
        },
        {
            "label": "Schools, programs, and degree names",
            "source": "Boston College University Catalog",
            "year": 2025,
            "url": "https://www.bc.edu/bc-web/academics/sites/university-catalog.html",
        },
        {
            "label": "Tuition & fees",
            "source": "Boston College Office of Student Services",
            "year": 2025,
            "url": "https://www.bc.edu/bc-web/offices/student-services/billing-student-accounts/tuition-fees.html",
        },
    ],
}

# student_body_size renders as "Undergraduates". BC's total enrollment (~14,600)
# is larger; the undergraduate figure is the labelled value.
UNDERGRAD_COUNT = 9484

DESCRIPTION = (
    "Boston College is a private Jesuit, Catholic research university in Chestnut "
    "Hill, Massachusetts, on a wooded campus about six miles west of downtown "
    "Boston. Founded in 1863 by the Society of Jesus to educate the sons of the "
    "city's Irish Catholic immigrants, it has grown into one of the leading "
    "research universities in the United States while keeping the Jesuit ideals of "
    "rigorous liberal-arts formation, care for the whole person (cura "
    "personalis), and service to others at the center of its mission.\n\n"
    "The university is organized into eight schools: the Morrissey College of Arts "
    "and Sciences (its oldest and largest college, home to the humanities, natural "
    "sciences, and social sciences at both the undergraduate and graduate levels); "
    "the Carroll School of Management; the Lynch School of Education and Human "
    "Development; the William F. Connell School of Nursing; the School of Social "
    "Work; the Law School; the Clough School of Theology and Ministry; and the "
    "Woods College of Advancing Studies. Roughly 9,500 undergraduates and 4,700 "
    "graduate and professional students study across these units.\n\n"
    "Boston College is highly selective — it admitted 13.9% of the nearly 40,000 "
    "applicants to the Class of 2029 — and ranks No. 37 among national universities "
    "in the U.S. News list. Its students graduate at a very high rate (a 91% "
    "six-year graduation rate and a 96% first-year retention rate) and earn a "
    "median income of roughly $104,000 a decade after entry.\n\n"
    "Distinctively for a university of its research standing, Boston College asks "
    "every undergraduate to grapple with questions of meaning, ethics, and the "
    "common good through its Core Curriculum and formative programs such as "
    "PULSE and Perspectives — pairing a nationally ranked education in management, "
    "nursing, law, education, and the arts and sciences with a Jesuit commitment to "
    "reflection and social justice."
)

# ── The eight academic schools (display order) ─────────────────────────────
_MCAS = "Morrissey College of Arts and Sciences"
_CSOM = "Carroll School of Management"
_LYNCH = "Lynch School of Education and Human Development"
_CSON = "William F. Connell School of Nursing"
_SSW = "Boston College School of Social Work"
_LAW = "Boston College Law School"
_STM = "Clough School of Theology and Ministry"
_WOODS = "Woods College of Advancing Studies"

SCHOOLS: list[dict] = [
    {
        "name": _MCAS,
        "sort_order": 1,
        "description": (
            "Boston College's oldest and largest college, spanning the humanities, "
            "natural sciences, and social sciences from the undergraduate Core "
            "through the Graduate School of Arts and Sciences' master's and Ph.D. "
            "programs. It anchors the university's Jesuit liberal-arts mission and "
            "its growing research enterprise in fields from biology and physics to "
            "economics, philosophy, and theology."
        ),
    },
    {
        "name": _CSOM,
        "sort_order": 2,
        "description": (
            "One of the nation's top-ranked undergraduate business schools, the "
            "Carroll School of Management educates principled leaders across "
            "accounting, finance, marketing, management, and business analytics, and "
            "offers the full-time MBA, specialized M.S. degrees in finance and "
            "accounting, and research Ph.D. programs — grounded in BC's Jesuit "
            "emphasis on ethics and the common good."
        ),
    },
    {
        "name": _LYNCH,
        "sort_order": 3,
        "description": (
            "The Carolyn A. and Peter S. Lynch School of Education and Human "
            "Development prepares educators, counselors, and researchers to advance "
            "learning, human development, and social justice — from teacher "
            "education and applied psychology through doctoral programs in counseling "
            "psychology, higher education, curriculum, and measurement."
        ),
    },
    {
        "name": _CSON,
        "sort_order": 4,
        "description": (
            "The William F. Connell School of Nursing educates nurses and nurse "
            "scientists from the Bachelor of Science in Nursing through advanced "
            "practice (nurse practitioner and nurse-midwifery tracks), the Doctor of "
            "Nursing Practice, and a research Ph.D. — combining clinical rigor with "
            "BC's ethic of care for the whole person."
        ),
    },
    {
        "name": _SSW,
        "sort_order": 5,
        "description": (
            "The Boston College School of Social Work prepares clinical and "
            "macro social workers through the Master of Social Work — with fields of "
            "practice from children, youth, and families to global practice and "
            "mental health — and a research doctorate, advancing social justice and "
            "the well-being of vulnerable communities."
        ),
    },
    {
        "name": _LAW,
        "sort_order": 6,
        "description": (
            "Boston College Law School educates lawyers in the Jesuit tradition of "
            "service through the Juris Doctor, an LL.M. for internationally trained "
            "lawyers, and a Master of Legal Studies — pairing doctrinal rigor with "
            "clinics, public-interest programs, and a strong ethic of professional "
            "responsibility."
        ),
    },
    {
        "name": _STM,
        "sort_order": 7,
        "description": (
            "The Clough School of Theology and Ministry is an international "
            "theological center in the Jesuit, Catholic tradition, educating lay and "
            "ordained ministers, scholars, and church leaders through the Master of "
            "Divinity, master's degrees in theology and ministry, ecclesiastical "
            "degrees, and a doctorate in theology and education."
        ),
    },
    {
        "name": _WOODS,
        "sort_order": 8,
        "description": (
            "The James A. Woods, S.J. College of Advancing Studies extends a BC "
            "education to working professionals through flexible, part-time and "
            "online master's programs in applied analytics, applied economics, "
            "cybersecurity, healthcare administration, leadership, and sports "
            "administration."
        ),
    },
]

_SCHOOL_WEBSITE: dict[str, str] = {
    _MCAS: "https://www.bc.edu/bc-web/schools/morrissey.html",
    _CSOM: "https://www.bc.edu/bc-web/schools/carroll-school.html",
    _LYNCH: "https://www.bc.edu/bc-web/schools/lynch-school.html",
    _CSON: "https://www.bc.edu/bc-web/schools/cson.html",
    _SSW: "https://www.bc.edu/bc-web/schools/ssw.html",
    _LAW: "https://www.bc.edu/bc-web/schools/law.html",
    _STM: "https://www.bc.edu/bc-web/schools/stm.html",
    _WOODS: "https://www.bc.edu/bc-web/schools/wcas.html",
}

# Founding years + research centers are verified from each school's official site;
# current deans and named faculty are not re-verified per school at author time, so
# they are honestly omitted rather than guessed (recorded in _ABOUT_OMITTED).
_SCHOOL_ABOUT: dict[str, dict] = {
    _MCAS: {
        "founded": 1863,
        "research_centers": [
            "Schiller Institute for Integrated Science and Society",
            "Clough Center for the Study of Constitutional Democracy",
            "Institute for the Liberal Arts",
        ],
        "source": {"label": "Morrissey College of Arts and Sciences", "url": "https://www.bc.edu/bc-web/schools/morrissey.html"},
    },
    _CSOM: {
        "founded": 1938,
        "research_centers": [
            "Center for Asset Management",
            "Edmund H. Shea Jr. Center for Entrepreneurship",
            "Boston College Center for Corporate Citizenship",
        ],
        "source": {"label": "Carroll School of Management", "url": "https://www.bc.edu/bc-web/schools/carroll-school.html"},
    },
    _LYNCH: {
        "founded": 1952,
        "research_centers": [
            "Center for International Higher Education",
            "Mary E. Walsh Center for Thriving Children",
            "Center for Testing, Evaluation, and Educational Policy",
        ],
        "source": {"label": "Lynch School of Education and Human Development", "url": "https://www.bc.edu/bc-web/schools/lynch-school.html"},
    },
    _CSON: {
        "founded": 1947,
        "research_centers": [
            "Connell School Center for Nursing Research",
        ],
        "source": {"label": "Connell School of Nursing", "url": "https://www.bc.edu/bc-web/schools/cson.html"},
    },
    _SSW: {
        "founded": 1936,
        "research_centers": [
            "Research Program on Children and Adversity",
            "Center for Social Innovation",
            "Center for Aging and Work",
        ],
        "source": {"label": "Boston College School of Social Work", "url": "https://www.bc.edu/bc-web/schools/ssw.html"},
    },
    _LAW: {
        "founded": 1929,
        "research_centers": [
            "Rappaport Center for Law and Public Policy",
            "Center for Experiential Learning",
        ],
        "source": {"label": "Boston College Law School", "url": "https://www.bc.edu/bc-web/schools/law.html"},
    },
    _STM: {
        "founded": 2008,
        "research_centers": [
            "Church in the 21st Century Center",
        ],
        "source": {"label": "Clough School of Theology and Ministry", "url": "https://www.bc.edu/bc-web/schools/stm.html"},
    },
    _WOODS: {
        "founded": 1929,
        "research_centers": [],
        "source": {"label": "Woods College of Advancing Studies", "url": "https://www.bc.edu/bc-web/schools/wcas.html"},
    },
}
_ABOUT_OMITTED: dict[str, list[str]] = {
    name: ["about_detail.leadership", "about_detail.faculty"]
    + (["about_detail.research_centers"] if not about.get("research_centers") else [])
    for name, about in _SCHOOL_ABOUT.items()
}

# ── Channel feeds (BC's official Localist university calendar) ──────────────
# events.bc.edu is BC's live, official Localist calendar (RSS + iCal), verified to
# return current items. BC publishes no working public news RSS at author time, so
# the calendar RSS serves the Updates tab and the iCal serves Events — every node
# gets a populated feed rather than a dead one. Schools/programs filter the shared
# feed by keywords naming the unit (the MIT/MBAn pattern).
_BC_NEWS_RSS = "https://events.bc.edu/calendar.xml"
_BC_EVENTS_ICS = {"url": "https://events.bc.edu/calendar.ics", "type": "ical"}
_SOCIAL_BC = {
    "instagram": "https://www.instagram.com/bostoncollege/",
    "linkedin": "https://www.linkedin.com/school/boston-college/",
    "x": "https://x.com/BostonCollege",
    "youtube": "https://www.youtube.com/user/bostoncollege",
    "facebook": "https://www.facebook.com/BostonCollege",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _BC_NEWS_RSS,
    "events_feed": dict(_BC_EVENTS_ICS),
    "social": dict(_SOCIAL_BC),
}

_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _MCAS: ["arts and sciences", "Morrissey", "humanities", "sciences"],
    _CSOM: ["Carroll School", "management", "business", "finance"],
    _LYNCH: ["Lynch School", "education", "counseling", "human development"],
    _CSON: ["Connell", "nursing", "health"],
    _SSW: ["social work", "School of Social Work"],
    _LAW: ["Law School", "law", "legal"],
    _STM: ["theology", "ministry", "Clough School"],
    _WOODS: ["Woods College", "advancing studies", "professional"],
}
_KW_STOP = {"and", "of", "the", "in", "for", "with", "science", "sciences", "master", "bachelor", "doctor", "arts"}


def _school_content(name: str) -> dict:
    return {
        "news_rss": _BC_NEWS_RSS,
        "news_curated": False,
        "events_feed": dict(_BC_EVENTS_ICS),
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": dict(_SOCIAL_BC),
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
        "BC Writing Supplement",
        "School report + counselor recommendation",
        "One teacher evaluation",
        "Official transcript",
    ],
    "deadlines": {"early_decision_i": "Nov 1", "early_decision_ii": "Jan 1", "regular_decision": "Jan 1"},
    "test_policy": "Test-optional",
    "source": "Boston College Undergraduate Admission",
    "source_url": "https://www.bc.edu/bc-web/admission/apply.html",
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
    "source": "Boston College Graduate Admission",
    "source_url": "https://www.bc.edu/bc-web/academics/graduate.html",
}
_REQ_OPEN = {
    "materials": [
        "Online application",
        "Statement of purpose",
        "Transcripts",
        "Letters of recommendation",
    ],
    "source": "Boston College Woods College / program office",
    "source_url": "https://www.bc.edu/bc-web/schools/wcas.html",
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
    "source": "Boston College Law School Admissions",
    "source_url": "https://www.bc.edu/bc-web/schools/law/admission-aid.html",
}

# Institution-wide outcome proxy (College Scorecard, all-graduates) used where a
# program has no separately published employment report.
_OUTCOMES_INSTITUTION = {
    "median_salary": 103937,
    "scope": "institution",
    "employment_rate": None,
    "top_industries": ["Finance", "Consulting", "Healthcare", "Education", "Technology"],
    "conditions": "Institution-wide College Scorecard median earnings 10 years after entry (all graduates).",
    "source": "U.S. Dept. of Education College Scorecard",
    "source_url": "https://collegescorecard.ed.gov/school/?164924-Boston-College",
}

# College Scorecard Field-of-Study median earnings (2 yrs after completion), by
# slug, for programs where a real field-level figure is published. {salary, cip}.
_FOS_OUTCOMES: dict[str, tuple[int, str]] = {
    "bc-computer-science-bs": (84100, "11.07"),
    "bc-communication-bs": (46940, "09.01"),
    "bc-economics-bs": (72900, "45.06"),
    "bc-finance-bs": (79600, "52.08"),
    "bc-accounting-bs": (68000, "52.03"),
    "bc-nursing-bsn": (83400, "51.38"),
    "bc-psychology-bs": (41000, "42.01"),
    "bc-biology-bs": (39900, "26.01"),
    "bc-mathematics-bs": (74000, "27.01"),
    "bc-political-science-bs": (55000, "45.10"),
}

_BC_TUITION_UG = 70702
_BC_TUITION_JD = 69600
_BC_TUITION_MBA = 65080

# ── The program catalog (real BC degree programs, resolved from the CIP list) ──
# Each spec: slug · school · program_name (the full conferred degree, exactly as
# BC awards it) · field (short discipline term for feed keywords) · degree_type ·
# duration_months · department · cip (4-digit dotted) · description (field-specific)
# · who (program-distinct audience). Optional: delivery_format, tuition (override),
# website. Helpers derive content_sources, requirements, outcomes, cost, _standard.
def _p(slug, school, name, field, degree, months, dept, cip, desc, who, **kw):
    d = {
        "slug": slug, "school": school, "program_name": name, "field": field,
        "degree_type": degree, "duration_months": months, "department": dept,
        "cip": cip, "description": desc, "who": who,
    }
    d.update(kw)
    return d


PROGRAMS: list[dict] = [
    # ── Morrissey College of Arts and Sciences — undergraduate ──
    _p("bc-aads-ba", _MCAS, "Bachelor of Arts in African and African Diaspora Studies", "African Diaspora Studies", "bachelors", 48,
       "Department of African and African Diaspora Studies", "05.02",
       "Interdisciplinary study of the histories, cultures, and politics of Africa and its diaspora across the Americas, Europe, and the Caribbean.",
       "Undergraduates drawn to the history, literature, and social movements of Africa and the Black Atlantic who want an interdisciplinary humanities and social-science major."),
    _p("bc-art-history-ba", _MCAS, "Bachelor of Arts in Art History", "Art History", "bachelors", 48,
       "Department of Art, Art History, and Film", "50.07",
       "Study of art, architecture, and visual culture from antiquity to the present, with access to Boston's museums and BC's McMullen Museum of Art.",
       "Students who want to read images and buildings closely and pursue careers in museums, galleries, conservation, or graduate study in the history of art."),
    _p("bc-biochemistry-bs", _MCAS, "Bachelor of Science in Biochemistry", "Biochemistry", "bachelors", 48,
       "Department of Chemistry", "26.02",
       "The chemistry of living systems — protein structure, enzymes, and metabolism — bridging molecular biology and organic and physical chemistry.",
       "Pre-medical and research-bound students who want a rigorous molecular science major at the interface of chemistry and biology."),
    _p("bc-biology-bs", _MCAS, "Bachelor of Science in Biology", "Biology", "bachelors", 48,
       "Department of Biology", "26.01",
       "From molecular and cellular biology through genetics, physiology, and ecology, with extensive laboratory and independent-research opportunities.",
       "Students preparing for medicine, biomedical research, or graduate study who want a broad, lab-intensive foundation in the life sciences."),
    _p("bc-chemistry-bs", _MCAS, "Bachelor of Science in Chemistry", "Chemistry", "bachelors", 48,
       "Department of Chemistry", "40.05",
       "Organic, inorganic, physical, and analytical chemistry with a strong undergraduate research culture in synthesis and materials.",
       "Students who want to understand and create molecules and pursue chemistry, medicine, or materials science."),
    _p("bc-classics-ba", _MCAS, "Bachelor of Arts in Classics", "Classics", "bachelors", 48,
       "Department of Classical Studies", "16.12",
       "The languages, literature, history, and thought of ancient Greece and Rome, from Homer and Virgil to Roman law and archaeology.",
       "Students who love ancient languages and the classical foundations of Western literature, philosophy, and law."),
    _p("bc-communication-ba", _MCAS, "Bachelor of Arts in Communication", "Communication", "bachelors", 48,
       "Department of Communication", "09.01",
       "How messages, media, and culture shape society — rhetoric, media studies, and interpersonal and organizational communication.",
       "Students headed for media, public relations, marketing, or law who want to analyze and craft persuasive communication."),
    _p("bc-computer-science-bs", _MCAS, "Bachelor of Science in Computer Science", "Computer Science", "bachelors", 48,
       "Department of Computer Science", "11.07",
       "Algorithms, systems, theory, and applications from machine learning to human-computer interaction, with a liberal-arts foundation.",
       "Students who want to build software and reason about computation, whether headed to industry or graduate research."),
    _p("bc-economics-ba", _MCAS, "Bachelor of Arts in Economics", "Economics", "bachelors", 48,
       "Department of Economics", "45.06",
       "Micro- and macroeconomic theory with strong empirical and econometric training, and applications from policy to finance.",
       "Students who want rigorous analytical tools for careers in finance, consulting, policy, or economics graduate study."),
    _p("bc-english-ba", _MCAS, "Bachelor of Arts in English", "English", "bachelors", 48,
       "Department of English", "23.01",
       "Literature in English from medieval to contemporary, plus creative writing and film, emphasizing close reading and critical writing.",
       "Students who love reading and writing and want the interpretive and communication skills prized in law, publishing, and teaching."),
    _p("bc-environmental-geoscience-bs", _MCAS, "Bachelor of Science in Environmental Geoscience", "Environmental Geoscience", "bachelors", 48,
       "Department of Earth and Environmental Sciences", "40.06",
       "The Earth's physical systems — climate, water, and geohazards — with fieldwork and quantitative analysis of environmental change.",
       "Students who want a quantitative Earth-science major to address climate, natural hazards, and environmental sustainability."),
    _p("bc-environmental-studies-ba", _MCAS, "Bachelor of Arts in Environmental Studies", "Environmental Studies", "bachelors", 48,
       "Environmental Studies Program", "03.01",
       "An interdisciplinary major connecting the natural sciences, social sciences, and humanities to environmental policy, ethics, and justice.",
       "Students who want to understand and address environmental challenges through policy, ethics, and the humanities as well as science."),
    _p("bc-film-studies-ba", _MCAS, "Bachelor of Arts in Film Studies", "Film Studies", "bachelors", 48,
       "Department of Art, Art History, and Film", "50.06",
       "The history, theory, and analysis of cinema and moving-image media, with production and screenwriting electives.",
       "Students who want to analyze and make film and media and pursue work in the creative industries or graduate study."),
    _p("bc-french-ba", _MCAS, "Bachelor of Arts in French", "French", "bachelors", 48,
       "Department of Romance Languages and Literatures", "16.09",
       "French language, literature, and Francophone cultures across Europe, Africa, and the Americas, with study-abroad pathways.",
       "Students who want fluency in French and deep engagement with Francophone literature and culture."),
    _p("bc-geological-sciences-bs", _MCAS, "Bachelor of Science in Geological Sciences", "Geological Sciences", "bachelors", 48,
       "Department of Earth and Environmental Sciences", "40.06",
       "The composition, structure, and history of the Earth — from plate tectonics and mineralogy to seismology at BC's Weston Observatory.",
       "Students fascinated by the solid Earth who want field and lab training for geoscience or environmental careers."),
    _p("bc-german-studies-ba", _MCAS, "Bachelor of Arts in German Studies", "German Studies", "bachelors", 48,
       "Department of Eastern, Slavic, and German Studies", "16.05",
       "German language, literature, philosophy, and film in their central-European cultural and intellectual context.",
       "Students who want German fluency and engagement with the German intellectual and literary tradition."),
    _p("bc-hispanic-studies-ba", _MCAS, "Bachelor of Arts in Hispanic Studies", "Hispanic Studies", "bachelors", 48,
       "Department of Romance Languages and Literatures", "16.09",
       "Spanish language and the literatures and cultures of Spain and Latin America, with community-engagement and study-abroad options.",
       "Students who want advanced Spanish and deep knowledge of the Hispanic world for careers in law, health, education, or the arts."),
    _p("bc-history-ba", _MCAS, "Bachelor of Arts in History", "History", "bachelors", 48,
       "Department of History", "54.01",
       "The study of the past across regions and eras, emphasizing primary-source research, argument, and historical writing.",
       "Students who want to reason from evidence about how societies change — a foundation for law, policy, and the professions."),
    _p("bc-hce-bs", _MCAS, "Bachelor of Science in Human-Centered Engineering", "Human-Centered Engineering", "bachelors", 48,
       "Department of Engineering", "14.01",
       "Boston College's distinctive engineering major, integrating design, energy, and health engineering with ethics and the liberal arts to serve human needs.",
       "Students who want to engineer solutions to human and societal problems within a values-driven, liberal-arts setting."),
    _p("bc-international-studies-ba", _MCAS, "Bachelor of Arts in International Studies", "International Studies", "bachelors", 48,
       "International Studies Program", "30.20",
       "An interdisciplinary major in global politics, economics, and history with a required foreign language and study abroad.",
       "Students headed for diplomacy, international business, or global NGOs who want an interdisciplinary, globally focused major."),
    _p("bc-islamic-civ-ba", _MCAS, "Bachelor of Arts in Islamic Civilization and Societies", "Islamic Civilization", "bachelors", 48,
       "Islamic Civilization and Societies Program", "05.01",
       "The religion, history, languages, and cultures of the Islamic world from its origins to the contemporary Middle East and beyond.",
       "Students who want interdisciplinary expertise in the Islamic world for careers in policy, security, journalism, or scholarship."),
    _p("bc-italian-ba", _MCAS, "Bachelor of Arts in Italian", "Italian", "bachelors", 48,
       "Department of Romance Languages and Literatures", "16.09",
       "Italian language, literature, and culture from Dante to contemporary cinema, with study abroad in Italy.",
       "Students who want Italian fluency and engagement with one of Europe's great literary and artistic traditions."),
    _p("bc-linguistics-ba", _MCAS, "Bachelor of Arts in Linguistics", "Linguistics", "bachelors", 48,
       "Program in Linguistics", "16.01",
       "The scientific study of language — sound, structure, meaning, and change — bridging the humanities, cognitive science, and computation.",
       "Students curious about how language works who want an analytical major spanning the humanities and cognitive science."),
    _p("bc-mathematics-bs", _MCAS, "Bachelor of Science in Mathematics", "Mathematics", "bachelors", 48,
       "Department of Mathematics", "27.01",
       "Pure and applied mathematics — analysis, algebra, geometry, and probability — with a strong theory and proof foundation.",
       "Students who love rigorous mathematical reasoning and want preparation for graduate study, data science, finance, or teaching."),
    _p("bc-music-ba", _MCAS, "Bachelor of Arts in Music", "Music", "bachelors", 48,
       "Department of Music", "50.09",
       "Music history, theory, composition, and performance across classical and global traditions, with BC's ensembles and performance opportunities.",
       "Students who want to study and make music within a liberal-arts curriculum."),
    _p("bc-neuroscience-bs", _MCAS, "Bachelor of Science in Neuroscience", "Neuroscience", "bachelors", 48,
       "Department of Psychology and Neuroscience", "26.15",
       "The biology of the nervous system and behavior, from molecules and neurons to cognition, integrating biology, chemistry, and psychology.",
       "Pre-health and research-bound students who want to understand the brain across molecular, cellular, and cognitive levels."),
    _p("bc-philosophy-ba", _MCAS, "Bachelor of Arts in Philosophy", "Philosophy", "bachelors", 48,
       "Department of Philosophy", "38.01",
       "The central questions of knowledge, reality, ethics, and meaning, from ancient thought to contemporary analytic and continental philosophy.",
       "Students who want to think rigorously about fundamental questions — excellent preparation for law, medicine, and any analytical career."),
    _p("bc-physics-bs", _MCAS, "Bachelor of Science in Physics", "Physics", "bachelors", 48,
       "Department of Physics", "40.08",
       "Classical and modern physics from mechanics to quantum theory, with condensed-matter and biophysics research opportunities.",
       "Students who want to understand nature's fundamental laws and pursue physics, engineering, or quantitative fields."),
    _p("bc-political-science-ba", _MCAS, "Bachelor of Arts in Political Science", "Political Science", "bachelors", 48,
       "Department of Political Science", "45.10",
       "American and comparative politics, international relations, and political theory, with a strong tradition in constitutional democracy.",
       "Students headed for law, government, policy, or journalism who want to analyze power, institutions, and political ideas."),
    _p("bc-psychology-bs", _MCAS, "Bachelor of Science in Psychology", "Psychology", "bachelors", 48,
       "Department of Psychology and Neuroscience", "42.01",
       "The science of mind and behavior — cognitive, developmental, clinical, and social psychology — with research-methods training.",
       "Students interested in human behavior and mental health headed for clinical, research, or applied careers."),
    _p("bc-russian-ba", _MCAS, "Bachelor of Arts in Russian", "Russian", "bachelors", 48,
       "Department of Eastern, Slavic, and German Studies", "16.04",
       "Russian language, literature, and culture, and the history and politics of Russia and Eastern Europe.",
       "Students who want Russian fluency and expertise in a strategically important region for careers in policy, security, or scholarship."),
    _p("bc-sociology-ba", _MCAS, "Bachelor of Arts in Sociology", "Sociology", "bachelors", 48,
       "Department of Sociology", "45.11",
       "How social structures, inequality, and institutions shape human life, with quantitative and qualitative research methods.",
       "Students who want to understand social inequality and institutions for careers in policy, law, social research, or advocacy."),
    _p("bc-studio-art-ba", _MCAS, "Bachelor of Arts in Studio Art", "Studio Art", "bachelors", 48,
       "Department of Art, Art History, and Film", "50.07",
       "Studio practice across drawing, painting, sculpture, photography, and digital media, grounded in critical study of art history.",
       "Students who want to develop as visual artists within a liberal-arts curriculum."),
    _p("bc-theatre-ba", _MCAS, "Bachelor of Arts in Theatre", "Theatre", "bachelors", 48,
       "Department of Theatre", "50.05",
       "Acting, directing, design, dramatic literature, and production, with a full season of mainstage and student theatre.",
       "Students who want to study and make theatre — performance, design, and dramaturgy — in a liberal-arts setting."),
    _p("bc-theology-ba", _MCAS, "Bachelor of Arts in Theology", "Theology", "bachelors", 48,
       "Department of Theology", "39.06",
       "The academic study of Christian and comparative religious traditions — scripture, history, ethics, and systematic theology.",
       "Students who want to study religion and theology critically within BC's Jesuit intellectual tradition."),
    # ── Morrissey / Graduate School of Arts and Sciences — graduate ──
    _p("bc-english-ma", _MCAS, "Master of Arts in English", "English", "masters", 24,
       "Department of English", "23.01",
       "Advanced study of literature in English and critical theory, preparing students for doctoral work or careers in writing and teaching.",
       "Students seeking graduate literary training before a Ph.D. or a career in teaching, editing, or writing."),
    _p("bc-english-phd", _MCAS, "Doctor of Philosophy in English", "English", "phd", 60,
       "Department of English", "23.01",
       "Doctoral research in literary history, theory, and criticism across periods, with dissertation supervision and teaching preparation. Funded.",
       "Aspiring literary scholars and professors pursuing original research in English literature. Funded with a stipend."),
    _p("bc-history-ma", _MCAS, "Master of Arts in History", "History", "masters", 24,
       "Department of History", "54.01",
       "Graduate training in historical research and writing across fields, from early modern Europe to U.S. and Atlantic history.",
       "Students who want advanced historical research training before doctoral study or careers in public history and education."),
    _p("bc-history-phd", _MCAS, "Doctor of Philosophy in History", "History", "phd", 60,
       "Department of History", "54.01",
       "Doctoral research producing original scholarship across BC's strengths in early modern, modern European, and American history. Funded.",
       "Future historians and professors pursuing archival dissertation research. Funded with a stipend."),
    _p("bc-philosophy-ma", _MCAS, "Master of Arts in Philosophy", "Philosophy", "masters", 24,
       "Department of Philosophy", "38.01",
       "Graduate study spanning the history of philosophy and contemporary analytic and continental thought.",
       "Students seeking rigorous philosophical training before doctoral work or professional and academic careers."),
    _p("bc-philosophy-phd", _MCAS, "Doctor of Philosophy in Philosophy", "Philosophy", "phd", 60,
       "Department of Philosophy", "38.01",
       "Doctoral research distinctive for its integration of the history of philosophy with systematic contemporary inquiry. Funded.",
       "Aspiring philosophers pursuing original dissertation research and university teaching. Funded with a stipend."),
    _p("bc-economics-phd", _MCAS, "Doctor of Philosophy in Economics", "Economics", "phd", 60,
       "Department of Economics", "45.06",
       "Doctoral research in micro- and macroeconomics, econometrics, and applied fields, training research economists. Funded.",
       "Students pursuing careers as research economists in academia, government, or industry. Funded with a stipend."),
    _p("bc-political-science-ma", _MCAS, "Master of Arts in Political Science", "Political Science", "masters", 24,
       "Department of Political Science", "45.10",
       "Graduate study of political theory, American and comparative politics, and international relations.",
       "Students seeking advanced political-science training before doctoral study or policy careers."),
    _p("bc-political-science-phd", _MCAS, "Doctor of Philosophy in Political Science", "Political Science", "phd", 60,
       "Department of Political Science", "45.10",
       "Doctoral research across political theory, comparative politics, and international relations, with a noted strength in political philosophy. Funded.",
       "Future political scientists pursuing original research and university teaching. Funded with a stipend."),
    _p("bc-sociology-ma", _MCAS, "Master of Arts in Sociology", "Sociology", "masters", 24,
       "Department of Sociology", "45.11",
       "Graduate training in sociological theory and research methods, with strengths in inequality, globalization, and social movements.",
       "Students seeking advanced sociological research training before doctoral study or applied research careers."),
    _p("bc-sociology-phd", _MCAS, "Doctor of Philosophy in Sociology", "Sociology", "phd", 60,
       "Department of Sociology", "45.11",
       "Doctoral research on inequality, globalization, and social change, training sociologists for research and teaching. Funded.",
       "Aspiring sociologists pursuing original dissertation research. Funded with a stipend."),
    _p("bc-biology-phd", _MCAS, "Doctor of Philosophy in Biology", "Biology", "phd", 60,
       "Department of Biology", "26.01",
       "Doctoral research in molecular, cellular, and developmental biology, genetics, and global public health science. Funded.",
       "Students pursuing careers as research biologists in academia, biotech, or medicine. Funded with a stipend."),
    _p("bc-chemistry-phd", _MCAS, "Doctor of Philosophy in Chemistry", "Chemistry", "phd", 60,
       "Department of Chemistry", "40.05",
       "Doctoral research across organic, inorganic, physical, and biological chemistry, with strengths in synthesis and catalysis. Funded.",
       "Students pursuing careers as research chemists in academia or industry. Funded with a stipend."),
    _p("bc-physics-phd", _MCAS, "Doctor of Philosophy in Physics", "Physics", "phd", 60,
       "Department of Physics", "40.08",
       "Doctoral research with a strong emphasis on condensed-matter and materials physics, both experimental and theoretical. Funded.",
       "Students pursuing careers as research physicists. Funded with a stipend."),
    _p("bc-mathematics-phd", _MCAS, "Doctor of Philosophy in Mathematics", "Mathematics", "phd", 60,
       "Department of Mathematics", "27.01",
       "Doctoral research in number theory, geometry, topology, and representation theory, training research mathematicians. Funded.",
       "Students pursuing careers as research mathematicians and professors. Funded with a stipend."),
    _p("bc-cs-phd", _MCAS, "Doctor of Philosophy in Computer Science", "Computer Science", "phd", 60,
       "Department of Computer Science", "11.07",
       "Doctoral research across systems, machine learning, and the theory and applications of computing. Funded.",
       "Students pursuing careers as computer-science researchers in academia or industry. Funded with a stipend."),
    _p("bc-ees-phd", _MCAS, "Doctor of Philosophy in Earth and Environmental Sciences", "Earth Environmental Sciences", "phd", 60,
       "Department of Earth and Environmental Sciences", "40.06",
       "Doctoral research on the Earth's systems, climate, and environmental change, including seismology at Weston Observatory. Funded.",
       "Students pursuing careers as geoscientists and environmental researchers. Funded with a stipend."),
    _p("bc-psychology-phd", _MCAS, "Doctor of Philosophy in Psychology", "Psychology", "phd", 60,
       "Department of Psychology and Neuroscience", "42.27",
       "Doctoral research in developmental, cognitive, and social psychology and neuroscience, training research psychologists. Funded.",
       "Students pursuing careers as research psychologists and professors. Funded with a stipend."),
    _p("bc-geology-ms", _MCAS, "Master of Science in Geology", "Geology", "masters", 24,
       "Department of Earth and Environmental Sciences", "40.06",
       "Graduate training in geology and Earth-system science, combining coursework with field and laboratory research.",
       "Students seeking advanced geoscience training for research, industry, or doctoral study."),
    _p("bc-hispanic-studies-ma", _MCAS, "Master of Arts in Hispanic Studies", "Hispanic Studies", "masters", 24,
       "Department of Romance Languages and Literatures", "16.09",
       "Advanced study of the literatures and cultures of Spain and Latin America.",
       "Students seeking graduate training in Hispanic literature and culture for teaching or doctoral study."),
    _p("bc-classical-studies-ma", _MCAS, "Master of Arts in Classical Studies", "Classical Studies", "masters", 24,
       "Department of Classical Studies", "16.12",
       "Graduate study of Greek and Latin languages, literature, and ancient Mediterranean history.",
       "Students seeking advanced training in the classical languages before doctoral study or teaching."),
    # ── Carroll School of Management ──
    _p("bc-accounting-bs", _CSOM, "Bachelor of Science in Accounting", "Accounting", "bachelors", 48,
       "Carroll School of Management", "52.03",
       "Financial and managerial accounting, auditing, and tax within the Carroll School's ethics-focused management core.",
       "Undergraduates headed for public accounting, corporate finance, or the CPA who want a rigorous, well-recruited accounting major."),
    _p("bc-finance-bs", _CSOM, "Bachelor of Science in Finance", "Finance", "bachelors", 48,
       "Carroll School of Management", "52.08",
       "Corporate finance, investments, and financial markets, taught with analytical rigor and strong recruiting into banking and asset management.",
       "Undergraduates targeting investment banking, asset management, or corporate finance."),
    _p("bc-marketing-bs", _CSOM, "Bachelor of Science in Marketing", "Marketing", "bachelors", 48,
       "Carroll School of Management", "52.14",
       "Consumer behavior, brand strategy, analytics, and digital marketing within a management education grounded in ethics.",
       "Undergraduates drawn to brand strategy, market research, and consumer insight."),
    _p("bc-management-leadership-bs", _CSOM, "Bachelor of Science in Management and Leadership", "Management Leadership", "bachelors", 48,
       "Carroll School of Management", "52.02",
       "Organizational behavior, strategy, and leadership, developing principled managers who can lead teams and organizations.",
       "Undergraduates who want to lead people and organizations across sectors."),
    _p("bc-business-analytics-bs", _CSOM, "Bachelor of Science in Business Analytics", "Business Analytics", "bachelors", 48,
       "Carroll School of Management", "52.13",
       "Statistics, data modeling, and optimization applied to business decisions, bridging management and quantitative methods.",
       "Undergraduates who want to turn data into business decisions and enter analytics, consulting, or operations roles."),
    _p("bc-mba", _CSOM, "Master of Business Administration", "Business Administration", "masters", 24,
       "Carroll School of Management", "52.02",
       "A full-time, STEM-eligible MBA integrating analytics, leadership, and ethics, with concentrations and experiential consulting.",
       "Early-to-mid-career professionals seeking general-management and leadership training to accelerate or pivot their careers.",
       tuition=_BC_TUITION_MBA),
    _p("bc-msf", _CSOM, "Master of Science in Finance", "Finance", "masters", 12,
       "Carroll School of Management", "52.08",
       "A STEM-designated specialized master's in corporate finance, investments, and financial modeling for early-career finance roles.",
       "Recent graduates and early-career professionals targeting quantitative finance, investment, and risk roles."),
    _p("bc-msa", _CSOM, "Master of Science in Accounting", "Accounting", "masters", 12,
       "Carroll School of Management", "52.03",
       "A STEM-designated master's completing the 150-credit CPA pathway with advanced financial reporting, audit, and analytics.",
       "Accounting and business graduates completing CPA-eligibility credits for careers in public accounting and advisory."),
    _p("bc-mgmt-phd", _CSOM, "Doctor of Philosophy in Management (Organization Studies)", "Organization Studies", "phd", 60,
       "Carroll School of Management", "52.02",
       "Doctoral research in organizational behavior and theory, training management scholars for research and teaching. Funded.",
       "Aspiring business-school professors researching organizations and leadership. Funded with a stipend."),
    _p("bc-finance-phd", _CSOM, "Doctor of Philosophy in Finance", "Finance", "phd", 60,
       "Carroll School of Management", "52.08",
       "Doctoral research in asset pricing, corporate finance, and financial markets, training finance scholars. Funded.",
       "Aspiring finance professors pursuing original research. Funded with a stipend."),
    _p("bc-accounting-phd", _CSOM, "Doctor of Philosophy in Accounting", "Accounting", "phd", 60,
       "Carroll School of Management", "52.03",
       "Doctoral research in financial and managerial accounting, training accounting scholars for academic careers. Funded.",
       "Aspiring accounting professors pursuing original research. Funded with a stipend."),
    # ── Lynch School of Education and Human Development ──
    _p("bc-aphd-ba", _LYNCH, "Bachelor of Arts in Applied Psychology and Human Development", "Applied Psychology Human Development", "bachelors", 48,
       "Department of Counseling, Developmental, and Educational Psychology", "42.28",
       "How people develop across the lifespan and how psychology can be applied to schools, families, and communities.",
       "Undergraduates interested in child and human development, counseling, and social impact careers."),
    _p("bc-elementary-education-ba", _LYNCH, "Bachelor of Arts in Elementary Education", "Elementary Education", "bachelors", 48,
       "Department of Teaching, Curriculum, and Society", "13.12",
       "Teacher preparation for elementary classrooms, pairing a liberal-arts major with licensure coursework and school placements.",
       "Undergraduates preparing to become licensed elementary-school teachers."),
    _p("bc-secondary-education-ba", _LYNCH, "Bachelor of Arts in Secondary Education", "Secondary Education", "bachelors", 48,
       "Department of Teaching, Curriculum, and Society", "13.13",
       "Teacher preparation for middle- and high-school subjects, combining a content major with pedagogy and clinical placements.",
       "Undergraduates preparing to teach a subject at the secondary level."),
    _p("bc-mental-health-counseling-ma", _LYNCH, "Master of Arts in Mental Health Counseling", "Mental Health Counseling", "masters", 24,
       "Department of Counseling, Developmental, and Educational Psychology", "51.15",
       "Clinical training toward licensure as a mental-health counselor, integrating theory, practice, and supervised fieldwork.",
       "Students preparing to become licensed clinical mental-health counselors."),
    _p("bc-school-counseling-ma", _LYNCH, "Master of Arts in School Counseling", "School Counseling", "masters", 24,
       "Department of Counseling, Developmental, and Educational Psychology", "13.11",
       "Preparation for school-counselor licensure, supporting students' academic, social, and emotional development.",
       "Students preparing to become licensed school counselors in K–12 settings."),
    _p("bc-curriculum-instruction-med", _LYNCH, "Master of Education in Curriculum and Instruction", "Curriculum Instruction", "masters", 12,
       "Department of Teaching, Curriculum, and Society", "13.03",
       "Advanced study of teaching, curriculum design, and learning for practicing and aspiring educators.",
       "Teachers and educators seeking to deepen their practice in curriculum and instruction."),
    _p("bc-higher-education-ma", _LYNCH, "Master of Arts in Higher Education", "Higher Education", "masters", 24,
       "Department of Educational Leadership and Higher Education", "13.04",
       "Preparation for leadership in colleges and universities across administration, student affairs, and international education.",
       "Students pursuing careers in student affairs, administration, and leadership in higher education."),
    _p("bc-educational-leadership-med", _LYNCH, "Master of Education in Educational Leadership and Policy", "Educational Leadership", "masters", 12,
       "Department of Educational Leadership and Higher Education", "13.04",
       "Leadership and policy training for aspiring principals and education administrators.",
       "Educators pursuing school and district leadership or education-policy roles."),
    _p("bc-applied-statistics-ms", _LYNCH, "Master of Science in Applied Statistics and Psychometrics", "Applied Statistics Psychometrics", "masters", 24,
       "Department of Measurement, Evaluation, Statistics, and Assessment", "13.06",
       "Advanced statistical modeling, measurement, and psychometrics for educational and social-science research.",
       "Students seeking quantitative and measurement expertise for research, assessment, or data-analysis careers."),
    _p("bc-counseling-psych-phd", _LYNCH, "Doctor of Philosophy in Counseling Psychology", "Counseling Psychology", "phd", 60,
       "Department of Counseling, Developmental, and Educational Psychology", "42.28",
       "APA-accredited doctoral training in counseling psychology, integrating research, practice, and social justice. Funded.",
       "Students pursuing licensure and research careers as counseling psychologists. Funded with a stipend."),
    _p("bc-adep-phd", _LYNCH, "Doctor of Philosophy in Applied Developmental and Educational Psychology", "Applied Developmental Educational Psychology", "phd", 60,
       "Department of Counseling, Developmental, and Educational Psychology", "13.06",
       "Doctoral research on human development and learning in educational and community contexts. Funded.",
       "Students pursuing research careers on child development, learning, and education. Funded with a stipend."),
    _p("bc-higher-education-phd", _LYNCH, "Doctor of Philosophy in Higher Education", "Higher Education", "phd", 60,
       "Department of Educational Leadership and Higher Education", "13.04",
       "Doctoral research on higher-education policy, organization, and international higher education. Funded.",
       "Students pursuing research and leadership careers in higher education. Funded with a stipend."),
    _p("bc-curriculum-instruction-phd", _LYNCH, "Doctor of Philosophy in Curriculum and Instruction", "Curriculum Instruction", "phd", 60,
       "Department of Teaching, Curriculum, and Society", "13.03",
       "Doctoral research on teaching, learning, and curriculum, including language, literacy, and STEM education. Funded.",
       "Students pursuing research careers on teaching and learning. Funded with a stipend."),
    _p("bc-mesa-phd", _LYNCH, "Doctor of Philosophy in Measurement, Evaluation, Statistics, and Assessment", "Measurement Evaluation Statistics", "phd", 60,
       "Department of Measurement, Evaluation, Statistics, and Assessment", "13.06",
       "Doctoral research in educational measurement, psychometrics, and quantitative methods. Funded.",
       "Students pursuing research careers in measurement, assessment, and applied statistics. Funded with a stipend."),
    _p("bc-edd-educational-leadership", _LYNCH, "Doctor of Education in Educational Leadership", "Educational Leadership", "professional", 36,
       "Department of Educational Leadership and Higher Education", "13.04",
       "A practitioner doctorate developing leaders to drive equity and improvement in schools and educational organizations.",
       "Experienced educators and administrators seeking a leadership doctorate for systems-level roles."),
    # ── Connell School of Nursing ──
    _p("bc-nursing-bsn", _CSON, "Bachelor of Science in Nursing", "Nursing", "bachelors", 48,
       "William F. Connell School of Nursing", "51.38",
       "A four-year BSN combining nursing science, the liberal arts, and clinical rotations across Boston's teaching hospitals.",
       "Undergraduates preparing to become registered nurses with a strong science and liberal-arts foundation."),
    _p("bc-nursing-ms", _CSON, "Master of Science in Nursing", "Nursing", "masters", 24,
       "William F. Connell School of Nursing", "51.38",
       "Advanced-practice nursing preparation across nurse-practitioner specialties and nurse-midwifery, with clinical placements.",
       "Registered nurses and direct-entry students pursuing advanced-practice nursing licensure.",
       tracks=["Adult-Gerontology Primary Care NP", "Family NP", "Pediatric Primary Care NP", "Psychiatric-Mental Health NP", "Women's Health NP", "Nurse-Midwifery"]),
    _p("bc-nursing-dnp", _CSON, "Doctor of Nursing Practice", "Nursing Practice", "professional", 36,
       "William F. Connell School of Nursing", "51.38",
       "The terminal practice doctorate preparing advanced-practice nurse leaders and, via the CRNA track, nurse anesthetists.",
       "Advanced-practice nurses seeking the highest clinical practice degree, including nurse anesthesia."),
    _p("bc-nursing-phd", _CSON, "Doctor of Philosophy in Nursing", "Nursing", "phd", 60,
       "William F. Connell School of Nursing", "51.38",
       "Doctoral research developing nursing science and preparing nurse scientists and faculty. Funded.",
       "Nurses pursuing research careers advancing nursing science. Funded with a stipend."),
    _p("bc-global-public-health-bs", _CSON, "Bachelor of Science in Global Public Health and the Common Good", "Global Public Health", "bachelors", 48,
       "William F. Connell School of Nursing", "51.22",
       "An interdisciplinary major linking population health, ethics, and the common good, drawing on nursing, biology, and the social sciences.",
       "Undergraduates drawn to public health, health equity, and global health careers."),
    # ── School of Social Work ──
    _p("bc-msw", _SSW, "Master of Social Work", "Social Work", "masters", 24,
       "Boston College School of Social Work", "44.07",
       "Clinical and macro social-work practice with fields of practice from children, youth, and families to global practice and mental health.",
       "Students preparing for licensed clinical or community/macro social-work careers.",
       tracks=["Children, Youth, and Families", "Global Practice", "Health", "Mental Health"]),
    _p("bc-social-work-phd", _SSW, "Doctor of Philosophy in Social Work", "Social Work", "phd", 60,
       "Boston College School of Social Work", "44.07",
       "Doctoral research advancing social-work science and social justice, training scholars and faculty. Funded.",
       "Experienced social workers pursuing research and academic careers. Funded with a stipend."),
    # ── Law School ──
    _p("bc-jd", _LAW, "Juris Doctor", "Law", "professional", 36,
       "Boston College Law School", "22.01",
       "The three-year J.D. combining doctrinal rigor, clinics, and public-interest programs in the Jesuit tradition of service.",
       "Aspiring lawyers seeking a highly regarded J.D. with strong clinical and public-interest opportunities.",
       tuition=_BC_TUITION_JD),
    _p("bc-llm", _LAW, "Master of Laws (LL.M.)", "Laws", "masters", 12,
       "Boston College Law School", "22.99",
       "A one-year advanced law degree for internationally trained lawyers, building U.S. legal knowledge within a small cohort.",
       "Internationally trained lawyers seeking U.S. legal training and credentials."),
    _p("bc-mls-cybersecurity", _LAW, "Master of Legal Studies in Cybersecurity", "Legal Studies Cybersecurity", "masters", 12,
       "Boston College Law School", "22.99",
       "A master's for non-lawyers and professionals covering the law, policy, and governance of cybersecurity and data.",
       "Professionals who need legal and regulatory fluency in cybersecurity without a full J.D."),
    # ── Clough School of Theology and Ministry ──
    _p("bc-mdiv", _STM, "Master of Divinity", "Divinity", "masters", 36,
       "Clough School of Theology and Ministry", "39.06",
       "A three-year professional degree integrating theology, ministry practice, and spiritual formation for ecclesial leadership.",
       "Students preparing for ordained or lay ecclesial ministry in the Catholic and Christian traditions."),
    _p("bc-mts", _STM, "Master of Theological Studies", "Theological Studies", "masters", 24,
       "Clough School of Theology and Ministry", "39.06",
       "An academic master's giving a broad, rigorous grounding in theology as preparation for doctoral study or informed ministry.",
       "Students seeking a strong academic foundation in theology for doctoral work, teaching, or ministry."),
    _p("bc-ma-theology-ministry", _STM, "Master of Arts in Theology and Ministry", "Theology Ministry", "masters", 24,
       "Clough School of Theology and Ministry", "39.06",
       "Theological study joined to pastoral practice and personal spiritual formation, offered on campus and in a hybrid format.",
       "Students preparing for pastoral, educational, and lay ministry roles.",
       delivery_format="hybrid"),
    _p("bc-thm", _STM, "Master of Theology (Th.M.)", "Theology", "masters", 12,
       "Clough School of Theology and Ministry", "39.06",
       "An advanced, customizable degree for those who already hold an M.Div. or master's, deepening theology or ministerial practice.",
       "Ministers and scholars with a prior theology degree seeking advanced, focused study."),
    _p("bc-theology-education-phd", _STM, "Doctor of Philosophy in Theology and Education", "Theology Education", "phd", 60,
       "Clough School of Theology and Ministry", "39.04",
       "Doctoral research at the intersection of theology, religious education, and formation, preparing scholars and educators. Funded.",
       "Students pursuing research and teaching careers in theology and religious education. Funded with a stipend."),
    # ── Woods College of Advancing Studies ──
    _p("bc-applied-analytics-ms", _WOODS, "Master of Science in Applied Analytics", "Applied Analytics", "masters", 20,
       "Woods College of Advancing Studies", "30.71",
       "A part-time, flexible master's in data analytics — statistics, data management, machine learning, and visualization — for working professionals.",
       "Working professionals who want to build applied data-analytics skills without pausing their careers.",
       delivery_format="hybrid"),
    _p("bc-applied-economics-ms", _WOODS, "Master of Science in Applied Economics", "Applied Economics", "masters", 20,
       "Woods College of Advancing Studies", "45.06",
       "Applied micro- and macroeconomics and econometrics oriented to real-world policy and business analysis.",
       "Professionals who want practical economic and quantitative analysis skills for policy and business roles.",
       delivery_format="hybrid"),
    _p("bc-cybersecurity-ms", _WOODS, "Master of Science in Cybersecurity Policy and Governance", "Cybersecurity", "masters", 20,
       "Woods College of Advancing Studies", "11.10",
       "The management, policy, and governance of cybersecurity risk, bridging technology, law, and organizational leadership.",
       "Professionals moving into cybersecurity leadership, risk, and governance roles.",
       delivery_format="hybrid"),
    _p("bc-healthcare-admin-ms", _WOODS, "Master of Healthcare Administration", "Healthcare Administration", "masters", 20,
       "Woods College of Advancing Studies", "51.07",
       "Leadership, operations, finance, and policy for healthcare organizations, designed for working professionals.",
       "Professionals advancing into management and leadership roles across the healthcare system.",
       delivery_format="hybrid"),
    _p("bc-leadership-ms", _WOODS, "Master of Science in Leadership and Administration", "Leadership Administration", "masters", 20,
       "Woods College of Advancing Studies", "52.02",
       "Organizational leadership, strategy, and management for professionals leading teams and organizations across sectors.",
       "Working professionals building leadership and management skills to advance into senior roles.",
       delivery_format="hybrid"),
    _p("bc-sports-admin-ms", _WOODS, "Master of Science in Sports Administration", "Sports Administration", "masters", 20,
       "Woods College of Advancing Studies", "31.05",
       "The business and management of sport — operations, marketing, finance, and analytics — for the sports industry.",
       "Professionals pursuing management careers in collegiate, professional, and community sport.",
       delivery_format="hybrid"),
]

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

# Programs whose ordinary tier tuition is intentionally null (per-credit graduate
# billing with no annual sticker) → omit-with-reason; the reason is recorded per
# program in _standard. PhDs are funded (tuition 0). Undergrad, J.D., MBA carry a
# real scalar. This dict is only for building the honest omission reason strings.
_TUITION_OMIT_REASON = (
    "Boston College bills graduate tuition per-credit ($2,078/credit, 2024-25) with "
    "no single published annual full-time rate for this program; see the program's "
    "cost page — not guessed into the annual matcher field."
)


def _resolve_tuition(spec: dict) -> int | None:
    if "tuition" in spec:
        return spec["tuition"]
    dt = spec["degree_type"]
    if dt == "bachelors":
        return _BC_TUITION_UG
    if dt == "phd":
        return 0  # funded research doctorate (tuition waived)
    return None  # masters / professional / certificate billed per-credit → omit


def _has_tuition(spec: dict) -> bool:
    return _resolve_tuition(spec) is not None or spec["degree_type"] == "phd"


def _outcomes_kind(spec: dict) -> str:
    if spec["slug"] in _FOS_OUTCOMES:
        return "fos"
    if spec["degree_type"] in ("bachelors", "masters", "phd", "professional"):
        return "institution"
    return "none"


def _program_standard(spec: dict) -> dict:
    omitted: list[str] = ["tracks"] if "tracks" not in spec else []
    omitted += [
        "class_profile.cohort_size",
        "faculty_contacts.lead",
        "external_reviews.summary",
    ]
    if not _has_tuition(spec):
        omitted += ["cost_data.tuition_usd", "cost_data.source"]
    # Woods College hybrid/online programs admit on a rolling basis with no fixed
    # deadline (they use _REQ_OPEN, which carries no deadlines) → honest omission.
    if spec.get("delivery_format") in ("online", "hybrid"):
        omitted.append("application_requirements.deadlines")
    kind = _outcomes_kind(spec)
    if kind == "fos":
        omitted += [
            "outcomes_data.employment_rate",
            "outcomes_data.top_industries",
            "outcomes_data.conditions",
        ]
    elif kind == "institution":
        omitted.append("outcomes_data.employment_rate")
    return _standard(omitted)


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich Boston College to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Boston College is absent — safe on fresh/CI databases.
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
    # Lead media_gallery with the verified hero campus photo (seed's aerial),
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
        p.delivery_format = spec.get("delivery_format", "in_person")
        # Tuition (2024-25). Undergrad sticker; PhDs funded (0); J.D./MBA their own
        # published rate; other graduate tiers billed per-credit → null + omit-reason.
        tuition = _resolve_tuition(spec)
        p.tuition = tuition
        if tuition is not None:
            p.cost_data = {
                "tuition_usd": tuition,
                "funded": spec["degree_type"] == "phd",
                "source": "Boston College Office of Student Services",
                "source_url": "https://www.bc.edu/bc-web/offices/student-services/billing-student-accounts/tuition-fees.html",
                "year": "2024-25",
            }
        else:
            p.cost_data = {"tuition_usd": None, "omitted_reason": _TUITION_OMIT_REASON}
        # Requirements by tier.
        dt = spec["degree_type"]
        if spec["school"] == _LAW and dt == "professional":
            p.application_requirements = dict(_REQ_LAW)
        elif spec.get("delivery_format") in ("online", "hybrid"):
            p.application_requirements = dict(_REQ_OPEN)
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
                "source_url": "https://collegescorecard.ed.gov/school/?164924-Boston-College",
            }
        elif dt in ("bachelors", "masters", "phd", "professional"):
            p.outcomes_data = dict(_OUTCOMES_INSTITUTION)
        else:
            p.outcomes_data = None
        if p.outcomes_data is None:
            p.outcomes_data = {"_standard": _program_standard(spec)}
        else:
            p.outcomes_data["_standard"] = _program_standard(spec)
        p.cip_code = spec["cip"]
        p.who_its_for = spec["who"]
        if "tracks" in spec:
            p.tracks = spec["tracks"]
        p.class_profile = None
        p.faculty_contacts = None
        p.external_reviews = None
        if dt == "bachelors":
            p.application_deadline = date(2027, 1, 1)
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
