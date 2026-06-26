"""University of Virginia — gold-standard profile (institution + schools + catalog).

Every value below is verified against an authoritative source (UVA's official pages —
virginia.edu, the College of Arts & Sciences [college.as.virginia.edu], the Graduate
School of Arts & Sciences [graduate.as.virginia.edu], each professional school's site,
the Board of Visitors 2025-26 tuition & fee rate table [uvafinance.virginia.edu], the
Office of Institutional Research Common Data Set 2024-25 [ira.virginia.edu], the U.S.
Dept. of Education College Scorecard / NCES for UNITID 234076, and the ranking bodies)
and carries a citation, or is honestly omitted (recorded in that node's
``_standard.omitted``) — never guessed.

Scope note: UVA entered as a 5-stub institution seed (the 2026-06 US-News bulk seed)
whose five programs ALL shipped with an EMPTY ``description_text`` — a blank student page
and zero matcher embedding (REPAIR_BACKLOG run 86 entry #2, a worst-tier open defect; the
sibling Georgetown and WashU seeds were cleared earlier this cycle). This pass (2026-06-26)
takes the institution to gold (filling the seed's missing report-card / admissions-funnel /
diversity / cost-aid / campus-resources / rankings / feed fields) and REPLACES the five
empty stubs with a verified, real-named catalog across UVA's degree-granting schools — the
College of Arts & Sciences, the School of Engineering and Applied Science, the McIntire
School of Commerce, the School of Architecture, the School of Nursing, the School of
Education and Human Development, the School of Data Science, the Frank Batten School of
Leadership and Public Policy, the Darden School of Business, the School of Law, the School
of Medicine, and the Graduate School of Arts & Sciences.

Every program carries a researched, field-specific ``description_text`` (anti-stub clean,
gold contrast), a ``who_its_for`` statement, a real owning ``department``, a ``cip_code``
(from the IPEDS/Scorecard CIP list for UNITID 234076), a verified ``delivery_format``,
published tuition per credential level, working UVA news feeds, and sourced
``external_reviews`` on the obviously-coverable flagships (Darden MBA, the J.D., the M.D.,
the McIntire Commerce undergraduate degree, the Batten M.P.P., and the Data Science M.S.).
Nothing is padded.

Public-university tuition (run-83 rule): UVA publishes TWO undergraduate stickers — a
Virginia-resident rate and a much higher non-resident rate. The CPEF matcher reads the flat
``program.tuition`` scalar for its budget veto, so the scalar carries the NON-RESIDENT
(out-of-state) figure — the conservative, broadly-correct input for a national/international
applicant pool — while ``cost_data.breakdown`` preserves BOTH the resident and non-resident
rates. Undergraduate tuition+fees: $21,803 (VA) / $59,512 (non-VA), College Scorecard /
UVA SFS. Graduate/professional tuition is the Board of Visitors 2025-26 non-resident annual
rate where one is published (Darden MBA $80,080; School of Law J.D./LL.M. $76,396; School of
Medicine M.D. $62,846 first-year; Batten M.P.P. $56,536; M.S. in Data Science $53,754;
McIntire M.S. in Commerce $54,754 / M.S. in Business Analytics $69,420; M.P.H. $35,272;
Doctor of Nursing Practice $35,832; Master of Teaching $36,610). Programs billed only per
credit hour (most Engineering and Arts & Sciences master's, the Architecture graduate
degrees) carry no separately-published flat annual figure, so the annual scalar is omitted
with reason and the per-credit rate recorded; funded research doctorates carry
funded=True / tuition=None (tuition is waived for funded Ph.D. students).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "University of Virginia-Main Campus"

ENRICHED_AT = "2026-06-26"


def _standard(omitted: list[str] | None = None) -> dict:
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }


_OMITTED_INSTITUTION: list[str] = [
    # UVA publishes a student-faculty ratio but not a single current instructional-faculty
    # headcount that could be verified this session, so the count is omitted, not guessed.
    "school_outcomes.scale.faculty_count",
    # UVA's career outcomes are published per-school (the College, Engineering, Commerce,
    # Batten, etc.) rather than as one institution-wide employed-or-continuing-education
    # figure, so that headline outcome field is omitted; median earnings are provided.
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
]

# ── Institution-level data ────────────────────────────────────────────────
RANKING_DATA: dict = {
    "ownership_type": "public",
    # Southern Association of Colleges and Schools Commission on Colleges (UVA's regional
    # accreditor).
    "accreditor": "SACSCOC",
    "carnegie_classification": "Doctoral Universities: Very High Research Activity (R1)",
    # QS World University Rankings 2026.
    "qs_world_university_rankings": {"rank": 275, "year": 2026},
    # THE World University Rankings 2026.
    "times_higher_education": {"rank": 166, "year": 2026},
    # U.S. News Best Colleges (National Universities) 2025: #24 nationally
    # (tied), among the top public universities in the country.
    "us_news_national": {"rank": 24, "year": 2025},
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.1681,
    "avg_net_price": 21565,
    "median_earnings_10yr": 86863,
    # UVA CDS 2024-25 — six-year graduation rate (2018 cohort).
    "graduation_rate_6yr": 0.956,
    # UVA CDS 2024-25 — first-year retention (Fall 2023 cohort).
    "retention_rate_first_year": 0.979,
    # UVA CDS 2024-25 — SAT/ACT middle ranges of enrolled first-years who submitted scores.
    "test_scores": {
        "sat_total_25_75": [1410, 1520],
        "act_25_75": [32, 35],
        "source": "University of Virginia Common Data Set 2024-2025",
        "source_url": "https://ira.virginia.edu/university-stats-facts/common-data-set",
    },
    # Undergraduate race/ethnicity (U.S. Dept. of Education College Scorecard, UNITID
    # 234076). International students are reported separately; categories plus
    # two-or-more-races and not-reported make up the remainder, so shares do not sum to 100%.
    "demographics": {
        "white": 0.487,
        "asian": 0.199,
        "hispanic": 0.079,
        "black": 0.075,
        "international": 0.048,
        "two_or_more": 0.058,
        "note": (
            "Undergraduate race/ethnicity (U.S. Dept. of Education College Scorecard); "
            "two-or-more-races and not-reported make up the remainder, so shares do not "
            "sum to 100%."
        ),
        "source": "U.S. Dept. of Education College Scorecard — UVA (UNITID 234076)",
        "source_url": "https://collegescorecard.ed.gov/school/?234076",
    },
    "financial_aid": {
        # College Scorecard — share of undergraduates receiving Pell grants.
        "pell_grant_rate": 0.155,
        # UVA Student Financial Services — 2025-26 first-year non-resident estimated cost of
        # attendance (tuition + fees + housing + dining + books + personal + travel).
        "cost_of_attendance": 78328,
        "source": "UVA Student Financial Services — 2025-26 estimated cost of attendance",
        "source_url": (
            "https://sfs.virginia.edu/estimated-undergraduate-cost-attendance-2025-2026"
        ),
    },
    "research": {
        "labs": [
            "UVA Brain Institute",
            "Biocomplexity Institute",
            "Karsh Institute of Democracy",
            "UVA Comprehensive Cancer Center",
            "Paul and Diane Manning Institute of Biotechnology",
        ],
        "areas": [
            "Neuroscience & brain science",
            "Biotechnology & the biomedical sciences",
            "Democracy, law & public policy",
            "Cancer biology & oncology",
            "Data science & computing",
            "Materials & nanotechnology",
        ],
        "lab_links": {
            "Biocomplexity Institute": "https://biocomplexity.virginia.edu/",
            "Karsh Institute of Democracy": "https://karshinstitute.virginia.edu/",
        },
        "source": "University of Virginia — Research",
        "source_url": "https://research.virginia.edu/",
    },
    "scale": {
        # UVA CDS 2024-25 (Fall 2024) total + undergraduate enrollment.
        "total_enrollment": 26470,
        "undergraduate_enrollment": 17901,
        # Student-faculty ratio (U.S. News Best Colleges — UVA).
        "student_faculty_ratio": "15:1",
        "research_centers": [
            "UVA Brain Institute",
            "Biocomplexity Institute",
            "Karsh Institute of Democracy",
        ],
    },
    "campus_life": {
        # UVA's teams (the Cavaliers) compete in NCAA Division I, Atlantic Coast Conference.
        "athletics_division": "NCAA Division I (Atlantic Coast Conference)",
        "mascot": "Virginia Cavaliers",
        "housing": "Residential Grounds in Charlottesville, Virginia",
        "resources": [
            {"label": "Virginia Cavaliers Athletics", "url": "https://virginiasports.com/"},
            {"label": "UVA Library", "url": "https://www.library.virginia.edu/"},
            {
                "label": "The Fralin Museum of Art",
                "url": "https://uvafralinartmuseum.virginia.edu/",
            },
            {"label": "UVA Career Center", "url": "https://career.virginia.edu/"},
        ],
    },
    "flagship": {
        "enrollment_total": 26470,
        # Undergraduate Class of 2028 admissions funnel (UVA CDS 2024-25, first-time
        # first-year, Fall 2024).
        "applicants": 58951,
        "admits": 9909,
        "admissions_cycle": "Class of 2028 (entering fall 2024; UVA CDS 2024-25)",
        "founded_year": 1819,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (UVA, UNITID 234076)",
            "url": "https://collegescorecard.ed.gov/school/?234076",
        },
        {
            "label": "NCES College Navigator — University of Virginia (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=234076",
        },
        {
            "label": "UVA — 2025-26 Board of Visitors tuition & fee rates",
            "url": "https://uvafinance.virginia.edu/resources/2025-26-tuition-and-fee-rates",
        },
        {
            "label": "University of Virginia Common Data Set 2024-2025",
            "url": "https://ira.virginia.edu/university-stats-facts/common-data-set",
        },
        {
            "label": "QS World University Rankings 2026 — University of Virginia",
            "url": "https://www.topuniversities.com/universities/university-virginia",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — UVA",
            "url": (
                "https://www.timeshighereducation.com/world-university-rankings/"
                "university-virginia-main-campus"
            ),
        },
        {
            "label": "U.S. News Best Colleges 2025 — University of Virginia",
            "url": "https://www.usnews.com/best-colleges/uva-6968",
        },
    ],
}

UNDERGRAD_COUNT = 17901

DESCRIPTION = (
    "The University of Virginia is a public research university in Charlottesville, "
    "Virginia, founded in 1819 by Thomas Jefferson, who designed its Academical Village "
    "and the landmark Rotunda. A member of the Association of American Universities, it "
    "enrolls about 17,900 undergraduates and some 8,600 graduate and professional students "
    "— roughly 26,500 in all — with a 15:1 student-faculty ratio, and is classified as a "
    "Carnegie R1 very-high-research-activity university.\n\n"
    "UVA is organized into a dozen schools spanning the arts and sciences, engineering, "
    "business, architecture, nursing, education, data science, law, and medicine: the "
    "undergraduate-anchored College of Arts & Sciences, the School of Engineering and "
    "Applied Science, the McIntire School of Commerce, the School of Architecture, the "
    "School of Nursing, the School of Education and Human Development, the School of Data "
    "Science, the Frank Batten School of Leadership and Public Policy, the Darden School of "
    "Business, the School of Law, the School of Medicine, and the Graduate School of Arts & "
    "Sciences.\n\n"
    "Accredited by SACSCOC, UVA ranks among the top handful of public universities in the "
    "United States — No. 24 nationally by U.S. News, No. 166 in the world by Times Higher "
    "Education, and No. 275 by QS. It admitted about 17% of applicants to the undergraduate "
    "Class of 2028, graduates about 96% of its undergraduates within six years, and is "
    "known for a strong commitment to meeting demonstrated financial need.\n\n"
    "UVA's published 2025-26 undergraduate tuition is $21,803 for Virginia residents and "
    "$59,512 for non-residents, with an average net price of about $21,600 after aid. Its "
    "teams, the Cavaliers, compete in NCAA Division I in the Atlantic Coast Conference."
)

# ── The real degree-granting schools (display order) ───────────────────────
_ARTSCI = "College of Arts & Sciences"
_SEAS = "School of Engineering and Applied Science"
_MCINTIRE = "McIntire School of Commerce"
_ARCH = "School of Architecture"
_NURSING = "School of Nursing"
_EDUC = "School of Education and Human Development"
_DATASCI = "School of Data Science"
_BATTEN = "Frank Batten School of Leadership and Public Policy"
_DARDEN = "Darden School of Business"
_LAW = "School of Law"
_MEDICINE = "School of Medicine"
_GRAD = "Graduate School of Arts & Sciences"

_SCHOOL_WEBSITE: dict[str, str] = {
    _ARTSCI: "https://college.as.virginia.edu/",
    _SEAS: "https://engineering.virginia.edu/",
    _MCINTIRE: "https://www.commerce.virginia.edu/",
    _ARCH: "https://www.arch.virginia.edu/",
    _NURSING: "https://www.nursing.virginia.edu/",
    _EDUC: "https://education.virginia.edu/",
    _DATASCI: "https://datascience.virginia.edu/",
    _BATTEN: "https://batten.virginia.edu/",
    _DARDEN: "https://www.darden.virginia.edu/",
    _LAW: "https://www.law.virginia.edu/",
    _MEDICINE: "https://med.virginia.edu/",
    _GRAD: "https://graduate.as.virginia.edu/",
}

SCHOOLS: list[dict] = [
    {
        "name": _ARTSCI,
        "sort_order": 1,
        "description": (
            "UVA's largest school and the undergraduate core, the College of Arts & "
            "Sciences spans the humanities, natural and social sciences, and the arts, "
            "with more than fifty majors and a foundation in the liberal arts."
        ),
    },
    {
        "name": _SEAS,
        "sort_order": 2,
        "description": (
            "The School of Engineering and Applied Science educates engineers across "
            "aerospace, biomedical, chemical, civil, computer, electrical, materials, "
            "mechanical, and systems engineering, and is home to one of the few "
            "undergraduate systems-engineering programs in the country."
        ),
    },
    {
        "name": _MCINTIRE,
        "sort_order": 3,
        "description": (
            "The McIntire School of Commerce is UVA's undergraduate and graduate business "
            "school, offering its highly selective Bachelor of Science in Commerce and "
            "specialized master's degrees in commerce, accounting, and business analytics."
        ),
    },
    {
        "name": _ARCH,
        "sort_order": 4,
        "description": (
            "The School of Architecture teaches architecture, landscape architecture, "
            "urban and environmental planning, and architectural history, joining design "
            "studios with history, theory, and the study of the built environment."
        ),
    },
    {
        "name": _NURSING,
        "sort_order": 5,
        "description": (
            "The School of Nursing prepares nurses and nurse scientists from the bachelor's "
            "through the doctoral level, integrating clinical practice at UVA Health with "
            "research in chronic illness, aging, and health equity."
        ),
    },
    {
        "name": _EDUC,
        "sort_order": 6,
        "description": (
            "The School of Education and Human Development (the former Curry School) spans "
            "teaching, kinesiology, counseling, speech and hearing, and human development, "
            "pairing professional preparation with research on learning and well-being."
        ),
    },
    {
        "name": _DATASCI,
        "sort_order": 7,
        "description": (
            "The School of Data Science — UVA's newest school — offers degrees from the "
            "bachelor's through the Ph.D. in the methods, ethics, and applications of data "
            "science, in both residential and fully online formats."
        ),
    },
    {
        "name": _BATTEN,
        "sort_order": 8,
        "description": (
            "The Frank Batten School of Leadership and Public Policy teaches public policy "
            "analysis and leadership in a small-cohort setting, from an undergraduate major "
            "through the Master of Public Policy."
        ),
    },
    {
        "name": _DARDEN,
        "sort_order": 9,
        "description": (
            "The Darden School of Business is UVA's graduate business school, known for its "
            "case-method M.B.A. and for consistently top-ranked teaching and student "
            "experience."
        ),
    },
    {
        "name": _LAW,
        "sort_order": 10,
        "description": (
            "The School of Law is one of the nation's leading law schools, granting the "
            "Juris Doctor along with the LL.M. and S.J.D., and is known for its strong "
            "clerkship and large-firm placement and its collegial student culture."
        ),
    },
    {
        "name": _MEDICINE,
        "sort_order": 11,
        "description": (
            "The School of Medicine grants the M.D. through its 'Cells to Society' "
            "curriculum, the M.P.H., and biomedical-sciences doctorates, and anchors "
            "clinical care and research at UVA Health."
        ),
    },
    {
        "name": _GRAD,
        "sort_order": 12,
        "description": (
            "The Graduate School of Arts & Sciences awards master's and Ph.D. degrees "
            "across the humanities, natural sciences, and social sciences, with funded "
            "doctoral study in dozens of departments."
        ),
    },
]

# ── Content feeds (REQUIRED on institution + every school + every program) ──
# UVA's central newsroom (news.virginia.edu / UVA Today) exposes no machine-readable RSS
# (it runs on a Cludo-powered search index), so the institution and the schools without
# their own feed use the verified-working University of Virginia School of Engineering RSS
# (10 live items) as the best working source — real UVA stories, never a dead/empty feed
# (run-86 miss #9 verify-output rule). The Darden, Law, and Architecture schools have their
# OWN verified-working /rss.xml feeds, so they use those.
_UVA_NEWS_RSS = "https://engineering.virginia.edu/rss.xml"
_UVA_NEWS_URL = "https://news.virginia.edu/"

_SCHOOL_OWN_FEED: dict[str, str] = {
    _SEAS: "https://engineering.virginia.edu/rss.xml",
    _DARDEN: "https://www.darden.virginia.edu/rss.xml",
    _LAW: "https://www.law.virginia.edu/rss.xml",
    _ARCH: "https://www.arch.virginia.edu/rss.xml",
}

_SOCIAL_UVA = {
    "instagram": "https://www.instagram.com/uva/",
    "linkedin": "https://www.linkedin.com/school/university-of-virginia/",
    "x": "https://x.com/UVA",
    "youtube": "https://www.youtube.com/user/UVA",
    "facebook": "https://www.facebook.com/uva",
}

_INSTITUTION_CONTENT: dict = {
    "news_rss": _UVA_NEWS_RSS,
    "news_url": _UVA_NEWS_URL,
    "news_curated": False,
    "social": dict(_SOCIAL_UVA),
}

_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _ARTSCI: ["College of Arts & Sciences", "Arts & Sciences", "undergraduate", "research"],
    _SEAS: ["Engineering", "UVA Engineering", "applied science"],
    _MCINTIRE: ["McIntire", "Commerce", "business"],
    _ARCH: ["Architecture", "design", "planning"],
    _NURSING: ["Nursing", "UVA Nursing", "health"],
    _EDUC: ["Education", "Human Development", "teaching"],
    _DATASCI: ["Data Science", "School of Data Science", "AI"],
    _BATTEN: ["Batten", "public policy", "leadership"],
    _DARDEN: ["Darden", "MBA", "business"],
    _LAW: ["Law", "UVA Law", "legal"],
    _MEDICINE: ["Medicine", "UVA Health", "medical"],
    _GRAD: ["graduate", "Ph.D.", "research", "Arts & Sciences"],
}


def _school_content(name: str) -> dict:
    """A school's content_sources: its own working feed when it has one, else the
    institution feed, filtered by school-naming keywords."""
    feed = _SCHOOL_OWN_FEED.get(name, _UVA_NEWS_RSS)
    return {
        "news_rss": feed,
        "news_url": _SCHOOL_WEBSITE.get(name, _UVA_NEWS_URL),
        "news_curated": False,
        "keywords": list(_SCHOOL_KEYWORDS.get(name, [])),
        "social": dict(_SOCIAL_UVA),
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    feed = _SCHOOL_OWN_FEED.get(school_name, _UVA_NEWS_RSS)
    return {
        "news_rss": feed,
        "news_url": _SCHOOL_WEBSITE.get(school_name, _UVA_NEWS_URL),
        "news_curated": False,
        "keywords": list(keywords),
        "social": dict(_SOCIAL_UVA),
    }


# ── About-detail per school (founded / leadership / focus) ──────────────────
_ABOUT_DETAIL: dict[str, dict] = {
    _ARTSCI: {
        "founded": "1825",
        "focus": "Liberal arts and sciences — the undergraduate heart of UVA.",
        "source_url": "https://college.as.virginia.edu/",
    },
    _SEAS: {
        "founded": "1836",
        "focus": "Engineering and applied science; one of the oldest engineering schools "
        "at a public U.S. university.",
        "source_url": "https://engineering.virginia.edu/",
    },
    _MCINTIRE: {
        "founded": "1921",
        "focus": "Undergraduate and specialized-master's business education.",
        "source_url": "https://www.commerce.virginia.edu/",
    },
    _ARCH: {
        "founded": "1919",
        "focus": "Architecture, landscape architecture, planning, and architectural history.",
        "source_url": "https://www.arch.virginia.edu/",
    },
    _NURSING: {
        "founded": "1901",
        "focus": "Nursing education and research from the bachelor's to the doctorate.",
        "source_url": "https://www.nursing.virginia.edu/",
    },
    _EDUC: {
        "founded": "1905",
        "focus": "Education, human development, kinesiology, and the health professions.",
        "source_url": "https://education.virginia.edu/",
    },
    _DATASCI: {
        "founded": "2019",
        "focus": "Data science research and degrees — UVA's first new school in 12 years.",
        "source_url": "https://datascience.virginia.edu/",
    },
    _BATTEN: {
        "founded": "2007",
        "focus": "Public policy and leadership in a small-cohort, public-service setting.",
        "source_url": "https://batten.virginia.edu/",
    },
    _DARDEN: {
        "founded": "1955",
        "focus": "Case-method graduate business education.",
        "source_url": "https://www.darden.virginia.edu/",
    },
    _LAW: {
        "founded": "1819",
        "focus": "Legal education — among the oldest continuously operating law schools in "
        "the United States.",
        "source_url": "https://www.law.virginia.edu/",
    },
    _MEDICINE: {
        "founded": "1825",
        "focus": "Medical education, the biomedical sciences, and clinical care at UVA Health.",
        "source_url": "https://med.virginia.edu/",
    },
    _GRAD: {
        "founded": "1904",
        "focus": "Master's and doctoral study across the arts and sciences.",
        "source_url": "https://graduate.as.virginia.edu/",
    },
}
_ABOUT_OMITTED: dict[str, list[str]] = {
    # Per-school current dean/leadership names, an instructional-faculty headcount, and a
    # verified named-research-center list could not be confirmed per school this session, so
    # they are honestly omitted rather than guessed (the institution-level research centers
    # are populated in school_outcomes.research).
    name: ["about_detail.leadership", "about_detail.faculty", "about_detail.research_centers"]
    for name in _SCHOOL_WEBSITE
}

# ── Tuition constants (all verified, 2025-26) ───────────────────────────────
# Undergraduate: College Scorecard / UVA SFS tuition+fees. PUBLIC scalar = NON-RESIDENT.
_UG_OOS = 59512
_UG_INSTATE = 21803
_UG_NET = 21565
_UG_SRC = (
    "U.S. Dept. of Education College Scorecard / UVA Student Financial Services (2025-26)",
    "https://collegescorecard.ed.gov/school/?234076",
)
# Graduate / professional flat non-resident annual rates (UVA Board of Visitors 2025-26).
_BOV_SRC = (
    "UVA Board of Visitors — 2025-26 tuition & fee rates (non-resident)",
    "https://uvafinance.virginia.edu/resources/2025-26-tuition-and-fee-rates",
)
_MBA = 80080
_MS_COMMERCE = 54754
_MSBA = 69420
_JD = 76396
_LLM = 76396
_MD = 62846  # M.D. Year 1 non-resident; tuition steps down slightly each subsequent year.
_MPP = 56536
_MSDS = 53754
_MPH = 35272
_DNP = 35832
_MT = 36610

# Per-credit-billed graduate programs publish no flat annual figure, so the annual scalar is
# omitted with reason and the verified non-resident per-credit rate recorded.
_PC_ENG = "Billed per credit hour; UVA's 2025-26 non-resident graduate engineering rate is " \
    "$1,935 per credit ($2,218 for Computer Science). No flat annual tuition is published."
_PC_GSAS = "Billed per credit hour; UVA's 2025-26 non-resident Graduate Arts & Sciences " \
    "master's rate is $1,553 per credit. No flat annual tuition is published."
_PC_ARCH = "Billed per credit hour; UVA's 2025-26 non-resident graduate Architecture " \
    "master's rate is $1,530 per credit. No flat annual tuition is published."
_PC_MSN = "Billed per credit hour; UVA's 2025-26 non-resident graduate Nursing rate is " \
    "$1,493 per credit. No flat annual tuition is published."

_A = _ARTSCI

_CATALOG: list[dict] = [
    # ───────────── College of Arts & Sciences (undergraduate) ─────────────
    dict(
        slug="uva-african-american-african-studies-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in African American and African Studies",
        department="Carter G. Woodson Institute for African-American and African Studies",
        cip="05.02", duration_months=48, keywords=["African American studies", "Africa"],
        description=(
            "African American and African studies examines the history, politics, "
            "literature, and arts of Africa and its diaspora through the interdisciplinary "
            "scholarship of UVA's Carter G. Woodson Institute."
        ),
        who_its_for=(
            "Students drawn to the histories and cultures of Africa and the African "
            "diaspora who want interdisciplinary grounding for law, public service, or "
            "graduate study."
        ),
    ),
    dict(
        slug="uva-american-studies-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in American Studies",
        department="Program in American Studies", cip="05.01", duration_months=48,
        keywords=["American studies"],
        description=(
            "American studies reads the United States across literature, history, art, and "
            "popular culture, combining methods from the humanities and social sciences to "
            "interpret American life."
        ),
        who_its_for=(
            "Students curious about American culture and identity who want a flexible "
            "interdisciplinary major toward law, media, or the humanities."
        ),
    ),
    dict(
        slug="uva-anthropology-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Anthropology",
        department="Department of Anthropology", cip="45.02", duration_months=48,
        keywords=["anthropology"],
        description=(
            "Anthropology studies human societies and cultures across ethnographic, "
            "linguistic, and archaeological subfields, with fieldwork and a focus on "
            "global and comparative perspectives."
        ),
        who_its_for=(
            "Students fascinated by human cultures and difference who want field research "
            "and a path into the social sciences, global work, or medicine."
        ),
    ),
    dict(
        slug="uva-archaeology-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Archaeology",
        department="Interdepartmental Program in Archaeology", cip="45.03", duration_months=48,
        keywords=["archaeology"],
        description=(
            "Archaeology reconstructs past human societies from their material remains, "
            "joining excavation and laboratory analysis with anthropology, classics, and "
            "art history in an interdepartmental program."
        ),
        who_its_for=(
            "Students drawn to the material past who want excavation and lab experience "
            "toward archaeology, museum work, or cultural-heritage careers."
        ),
    ),
    dict(
        slug="uva-art-history-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Art History",
        department="Department of Art", cip="50.07", duration_months=48,
        keywords=["art history"],
        description=(
            "Art history studies painting, sculpture, architecture, and visual culture "
            "from antiquity to the present, building skills in close looking, "
            "interpretation, and the history of style and patronage."
        ),
        who_its_for=(
            "Students drawn to visual art and its history who want training toward "
            "curation, conservation, the art world, or graduate study."
        ),
    ),
    dict(
        slug="uva-studio-art-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Studio Art",
        department="Department of Art", cip="50.07", duration_months=48,
        keywords=["studio art", "art"],
        description=(
            "Studio art develops practice across drawing, painting, sculpture, "
            "printmaking, photography, and new media, pairing studio work with critique "
            "and the study of contemporary art."
        ),
        who_its_for=(
            "Students who make art and want rigorous studio training and critique toward "
            "an arts practice or graduate work in fine arts."
        ),
    ),
    dict(
        slug="uva-astronomy-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Astronomy",
        department="Department of Astronomy", cip="40.02", duration_months=48,
        keywords=["astronomy"],
        description=(
            "Astronomy studies stars, galaxies, and the structure and evolution of the "
            "universe, giving students access to observational data and UVA's "
            "research telescopes and radio-astronomy ties."
        ),
        who_its_for=(
            "Students captivated by the cosmos who want a science major with observational "
            "and research experience, with or without the physics-intensive track."
        ),
    ),
    dict(
        slug="uva-astronomy-physics-bs", school=_A, degree_type="bachelors",
        program_name="Bachelor of Science in Astronomy-Physics",
        department="Department of Astronomy", cip="40.02", duration_months=48,
        keywords=["astrophysics", "physics"],
        description=(
            "Astronomy-physics is a research-intensive joint degree combining the full "
            "physics core with astronomy, preparing students for graduate study in "
            "astrophysics and observational or theoretical research."
        ),
        who_its_for=(
            "Quantitatively strong students aiming for graduate school in astrophysics who "
            "want the rigorous physics-plus-astronomy track."
        ),
    ),
    dict(
        slug="uva-biology-bs", school=_A, degree_type="bachelors",
        program_name="Bachelor of Science in Biology",
        department="Department of Biology", cip="26.01", duration_months=48,
        keywords=["biology"],
        description=(
            "Biology spans molecular, cellular, organismal, and ecological scales, with "
            "extensive laboratory and field research and strong preparation for medicine, "
            "graduate study, and the life sciences."
        ),
        who_its_for=(
            "Aspiring biologists and pre-health students who want a research-rich "
            "foundation from molecules to ecosystems."
        ),
    ),
    dict(
        slug="uva-chemistry-bs", school=_A, degree_type="bachelors",
        program_name="Bachelor of Science in Chemistry",
        department="Department of Chemistry", cip="40.05", duration_months=48,
        keywords=["chemistry", "biochemistry"],
        description=(
            "Chemistry covers organic, inorganic, physical, and analytical chemistry with "
            "biochemistry options, anchoring core coursework in undergraduate research in "
            "faculty laboratories."
        ),
        who_its_for=(
            "Students bound for chemistry, medicine, or materials and energy research who "
            "want rigorous training and early lab access."
        ),
    ),
    dict(
        slug="uva-chinese-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Chinese Language and Literature",
        department="Department of East Asian Languages, Literatures and Cultures",
        cip="16.03", duration_months=48, keywords=["Chinese", "language"],
        description=(
            "Chinese language and literature builds advanced proficiency in Mandarin "
            "alongside the study of Chinese literature, film, and culture from the "
            "classical period to the present."
        ),
        who_its_for=(
            "Students committed to Chinese fluency who want literary and cultural depth for "
            "careers spanning China and East Asia."
        ),
    ),
    dict(
        slug="uva-classics-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Classics",
        department="Department of Classics", cip="16.12", duration_months=48,
        keywords=["classics", "Greek", "Latin"],
        description=(
            "Classics combines Greek and Latin with the literature, history, and "
            "archaeology of the ancient Mediterranean, reading foundational texts in the "
            "original languages."
        ),
        who_its_for=(
            "Students fascinated by antiquity who want to read the classical languages and "
            "build analytic skills prized in law and the humanities."
        ),
    ),
    dict(
        slug="uva-cognitive-science-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Cognitive Science",
        department="Interdisciplinary Program in Cognitive Science", cip="30.25",
        duration_months=48, keywords=["cognitive science"],
        description=(
            "Cognitive science studies the mind across psychology, neuroscience, "
            "linguistics, philosophy, and computer science, with concentrations from "
            "cognition to language and computation."
        ),
        who_its_for=(
            "Students curious about how minds and machines think who want an "
            "interdisciplinary path into research, AI, or the cognitive professions."
        ),
    ),
    dict(
        slug="uva-computer-science-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Computer Science",
        department="Department of Computer Science", cip="11.01", duration_months=48,
        keywords=["computer science", "CS"],
        description=(
            "The B.A. in computer science pairs the computing core — algorithms, systems, "
            "and theory — with the breadth of a liberal-arts degree, for students "
            "combining computing with another field."
        ),
        who_its_for=(
            "Arts & Sciences students who want strong computing skills alongside a "
            "humanities or science focus, without the full engineering curriculum."
        ),
    ),
    dict(
        slug="uva-drama-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Drama",
        department="Department of Drama", cip="50.05", duration_months=48,
        keywords=["drama", "theatre"],
        description=(
            "Drama integrates acting, directing, design, and dramatic literature with "
            "production work in UVA's theatres, joining performance practice with the "
            "study of theatre history and theory."
        ),
        who_its_for=(
            "Students drawn to theatre and performance who want hands-on production "
            "experience alongside the study of dramatic literature."
        ),
    ),
    dict(
        slug="uva-east-asian-studies-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in East Asian Studies",
        department="Department of East Asian Languages, Literatures and Cultures",
        cip="05.01", duration_months=48, keywords=["East Asia", "area studies"],
        description=(
            "East Asian studies combines language study with the history, religion, "
            "literature, and politics of China, Japan, and Korea in an interdisciplinary "
            "area major."
        ),
        who_its_for=(
            "Students focused on East Asia who want language plus regional depth for "
            "international careers or graduate study."
        ),
    ),
    dict(
        slug="uva-economics-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Economics",
        department="Department of Economics", cip="45.06", duration_months=48,
        keywords=["economics"],
        description=(
            "Economics grounds students in micro and macroeconomic theory and "
            "econometrics, with applied fields from labor and public economics to finance "
            "and international trade."
        ),
        who_its_for=(
            "Quantitatively minded students aiming for finance, consulting, policy, or "
            "graduate study who want theory plus empirical method."
        ),
    ),
    dict(
        slug="uva-english-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in English",
        department="Department of English", cip="23.01", duration_months=48,
        keywords=["English", "literature", "writing"],
        description=(
            "English studies literature in English from the medieval period to the "
            "present alongside critical theory and creative writing, in a department known "
            "for its strength in American and modern literature."
        ),
        who_its_for=(
            "Strong readers and writers who want close textual training toward law, "
            "publishing, teaching, or graduate study."
        ),
    ),
    dict(
        slug="uva-environmental-sciences-bs", school=_A, degree_type="bachelors",
        program_name="Bachelor of Science in Environmental Sciences",
        department="Department of Environmental Sciences", cip="03.01", duration_months=48,
        keywords=["environmental science"],
        description=(
            "Environmental sciences studies the atmosphere, hydrology, ecology, and "
            "geosciences as interacting systems, with field stations and long-term "
            "research on coasts, forests, and climate."
        ),
        who_its_for=(
            "Students drawn to the natural environment and climate who want field and lab "
            "science toward environmental research or policy."
        ),
    ),
    dict(
        slug="uva-environmental-thought-practice-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Environmental Thought and Practice",
        department="Program in Environmental Thought and Practice", cip="30.99",
        duration_months=48, keywords=["environment", "sustainability"],
        description=(
            "Environmental thought and practice approaches sustainability through the "
            "humanities and social sciences — ethics, policy, economics, and culture — "
            "rather than the laboratory sciences alone."
        ),
        who_its_for=(
            "Students who want to address environmental challenges through policy, ethics, "
            "and the humanities as much as through science."
        ),
    ),
    dict(
        slug="uva-french-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in French",
        department="Department of French", cip="16.09", duration_months=48,
        keywords=["French", "language"],
        description=(
            "French develops advanced language proficiency alongside the study of French "
            "and Francophone literature, film, and culture across Europe, Africa, and the "
            "Americas."
        ),
        who_its_for=(
            "Students committed to French fluency who want literary and cultural depth for "
            "international, legal, or academic careers."
        ),
    ),
    dict(
        slug="uva-german-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in German Language, Literature, and Culture",
        department="Department of Germanic Languages and Literatures", cip="16.05",
        duration_months=48, keywords=["German", "language"],
        description=(
            "German language, literature, and culture builds proficiency in German "
            "alongside the study of German-language literature, philosophy, and film from "
            "the Enlightenment to the present."
        ),
        who_its_for=(
            "Students drawn to the German-speaking world who want language and cultural "
            "depth for careers in Europe, business, or research."
        ),
    ),
    dict(
        slug="uva-global-studies-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Global Studies",
        department="Program in Global Studies", cip="30.20", duration_months=48,
        keywords=["global studies", "international"],
        description=(
            "Global studies examines globalization through interdisciplinary tracks — "
            "development, public health, security and justice, environments and "
            "sustainability, and the regions of the Middle East and South Asia — built on "
            "language study and time abroad."
        ),
        who_its_for=(
            "Globally minded students who want to combine a regional or thematic focus "
            "with language and study abroad toward international careers."
        ),
    ),
    dict(
        slug="uva-history-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in History",
        department="Corcoran Department of History", cip="54.01", duration_months=48,
        keywords=["history"],
        description=(
            "History studies the human past across regions and eras, teaching research "
            "with primary sources and the construction of evidence-based argument in one "
            "of UVA's oldest departments."
        ),
        who_its_for=(
            "Students who love the past and want research and writing skills toward law, "
            "public service, teaching, or graduate study."
        ),
    ),
    dict(
        slug="uva-human-biology-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Human Biology",
        department="Interdisciplinary Program in Human Biology", cip="26.01",
        duration_months=48, keywords=["human biology", "pre-health"],
        description=(
            "Human biology integrates biology, anthropology, and the social sciences to "
            "study human health, evolution, and disease, an interdisciplinary path "
            "popular with students interested in medicine and public health."
        ),
        who_its_for=(
            "Pre-health and pre-med students who want to study human health across "
            "biology and the social sciences rather than within a single department."
        ),
    ),
    dict(
        slug="uva-italian-studies-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Italian Studies",
        department="Department of Spanish, Italian, and Portuguese", cip="16.09",
        duration_months=48, keywords=["Italian", "language"],
        description=(
            "Italian studies builds proficiency in Italian alongside the study of Italian "
            "literature, cinema, and art from Dante to the present."
        ),
        who_its_for=(
            "Students drawn to Italy and its culture who want language and cultural depth "
            "for the arts, humanities, or international work."
        ),
    ),
    dict(
        slug="uva-japanese-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Japanese Language and Literature",
        department="Department of East Asian Languages, Literatures and Cultures",
        cip="16.03", duration_months=48, keywords=["Japanese", "language"],
        description=(
            "Japanese language and literature builds advanced proficiency in Japanese "
            "alongside the study of Japanese literature, film, and culture across "
            "classical and modern periods."
        ),
        who_its_for=(
            "Students committed to Japanese fluency who want literary and cultural depth "
            "for careers connected to Japan and East Asia."
        ),
    ),
    dict(
        slug="uva-jewish-studies-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Jewish Studies",
        department="Program in Jewish Studies", cip="05.01", duration_months=48,
        keywords=["Jewish studies"],
        description=(
            "Jewish studies examines Jewish history, religion, languages, and culture "
            "across the ancient world to the present in an interdisciplinary program "
            "spanning the humanities."
        ),
        who_its_for=(
            "Students drawn to Jewish history, thought, and culture who want "
            "interdisciplinary humanities training."
        ),
    ),
    dict(
        slug="uva-latin-american-studies-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Latin American Studies",
        department="Program in Latin American Studies", cip="05.01", duration_months=48,
        keywords=["Latin America", "area studies"],
        description=(
            "Latin American studies combines Spanish or Portuguese with the history, "
            "politics, literature, and economics of Latin America in an interdisciplinary "
            "area major."
        ),
        who_its_for=(
            "Students focused on Latin America who want language plus regional depth for "
            "international or policy careers."
        ),
    ),
    dict(
        slug="uva-linguistics-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Linguistics",
        department="Interdepartmental Program in Linguistics", cip="16.01", duration_months=48,
        keywords=["linguistics"],
        description=(
            "Linguistics studies the structure of human language — sound, form, meaning, "
            "and use — drawing on phonology, syntax, semantics, and psycholinguistics "
            "across an interdepartmental program."
        ),
        who_its_for=(
            "Students fascinated by how language works who want analytic training toward "
            "research, computational linguistics, or the language professions."
        ),
    ),
    dict(
        slug="uva-mathematics-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Mathematics",
        department="Department of Mathematics", cip="27.01", duration_months=48,
        keywords=["mathematics"],
        description=(
            "Mathematics develops rigor in analysis, algebra, and geometry with options "
            "in applied and financial mathematics, supporting paths into research, "
            "teaching, finance, and the quantitative sciences."
        ),
        who_its_for=(
            "Students who enjoy mathematical reasoning and want a foundation for graduate "
            "study, finance, data, or teaching."
        ),
    ),
    dict(
        slug="uva-media-studies-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Media Studies",
        department="Department of Media Studies", cip="09.01", duration_months=48,
        keywords=["media studies"],
        description=(
            "Media studies analyzes film, television, digital platforms, and journalism — "
            "their history, theory, and effects — and pairs critical study with "
            "media production."
        ),
        who_its_for=(
            "Students interested in media and communication who want critical analysis "
            "plus production toward journalism, media, or tech."
        ),
    ),
    dict(
        slug="uva-medieval-studies-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Medieval Studies",
        department="Program in Medieval Studies", cip="30.13", duration_months=48,
        keywords=["medieval studies"],
        description=(
            "Medieval studies examines the literature, history, art, and religion of the "
            "European and Mediterranean Middle Ages across an interdisciplinary program."
        ),
        who_its_for=(
            "Students drawn to the medieval world who want interdisciplinary humanities "
            "training across languages, history, and the arts."
        ),
    ),
    dict(
        slug="uva-mesalc-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Middle Eastern and South Asian Languages and Cultures",
        department="Department of Middle Eastern and South Asian Languages and Cultures",
        cip="16.11", duration_months=48, keywords=["Middle East", "South Asia", "language"],
        description=(
            "This major builds proficiency in languages such as Arabic, Persian, Hebrew, "
            "Hindi-Urdu, Sanskrit, or Tibetan alongside the literatures and cultures of "
            "the Middle East and South Asia."
        ),
        who_its_for=(
            "Students committed to a Middle Eastern or South Asian language who want "
            "literary and cultural depth for international or scholarly careers."
        ),
    ),
    dict(
        slug="uva-music-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Music",
        department="Department of Music", cip="50.09", duration_months=48,
        keywords=["music"],
        description=(
            "Music joins performance and composition with music history, theory, and "
            "ethnomusicology, including UVA's strengths in computer music and the study of "
            "popular and world musics."
        ),
        who_its_for=(
            "Musicians and listeners who want to combine performance or composition with "
            "the scholarly study of music."
        ),
    ),
    dict(
        slug="uva-neuroscience-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Neuroscience",
        department="Interdisciplinary Major in Neuroscience", cip="26.15", duration_months=48,
        keywords=["neuroscience"],
        description=(
            "Neuroscience studies the nervous system from molecules and cells to behavior "
            "and cognition, drawing on biology, psychology, and chemistry with access to "
            "UVA's brain-science research."
        ),
        who_its_for=(
            "Students fascinated by the brain and behavior, often pre-health, who want a "
            "research-oriented interdisciplinary science major."
        ),
    ),
    dict(
        slug="uva-philosophy-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Philosophy",
        department="Corcoran Department of Philosophy", cip="38.01", duration_months=48,
        keywords=["philosophy"],
        description=(
            "Philosophy examines fundamental questions of knowledge, ethics, mind, and "
            "reality, training students in rigorous argument across the history of "
            "philosophy and contemporary debates."
        ),
        who_its_for=(
            "Students who love hard questions and careful argument and want training "
            "valued in law, policy, and graduate study."
        ),
    ),
    dict(
        slug="uva-physics-bs", school=_A, degree_type="bachelors",
        program_name="Bachelor of Science in Physics",
        department="Department of Physics", cip="40.08", duration_months=48,
        keywords=["physics"],
        description=(
            "Physics builds from classical mechanics and electromagnetism through quantum "
            "mechanics and relativity, with laboratory and research experience in "
            "condensed-matter, nuclear, and high-energy physics."
        ),
        who_its_for=(
            "Students drawn to the fundamental laws of nature who want a research-oriented "
            "path into physics, engineering, or the quantitative sciences."
        ),
    ),
    dict(
        slug="uva-political-social-thought-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Political and Social Thought",
        department="Program in Political and Social Thought", cip="30.99", duration_months=48,
        keywords=["political and social thought"],
        description=(
            "Political and social thought is a selective interdisciplinary major in which "
            "students design a course of study in political theory, social science, and "
            "the humanities around a self-defined intellectual focus."
        ),
        who_its_for=(
            "Intellectually independent students who want to build a rigorous, "
            "self-designed major around questions of politics and society."
        ),
    ),
    dict(
        slug="uva-ppl-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Political Philosophy, Policy, and Law",
        department="Program in Political Philosophy, Policy, and Law", cip="30.99",
        duration_months=48, keywords=["political philosophy", "law", "policy"],
        description=(
            "Political philosophy, policy, and law is a selective interdisciplinary major "
            "joining political theory, ethics, economics, and law to examine how societies "
            "are justly governed."
        ),
        who_its_for=(
            "Pre-law and policy-minded students who want a rigorous, theory-rich major at "
            "the intersection of philosophy, politics, and law."
        ),
    ),
    dict(
        slug="uva-politics-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Politics",
        department="Woodrow Wilson Department of Politics", cip="45.10", duration_months=48,
        keywords=["politics", "political science"],
        description=(
            "Politics studies government, political behavior, and international relations, "
            "with concentrations in American politics, comparative politics, political "
            "theory, and foreign affairs."
        ),
        who_its_for=(
            "Students interested in government and world affairs who want analytic "
            "training toward law, public service, or graduate study."
        ),
    ),
    dict(
        slug="uva-psychology-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Psychology",
        department="Department of Psychology", cip="42.01", duration_months=48,
        keywords=["psychology"],
        description=(
            "Psychology studies mind and behavior across cognitive, developmental, "
            "clinical, and social psychology, with statistics, research methods, and "
            "opportunities to work in faculty labs."
        ),
        who_its_for=(
            "Students curious about why people think and act as they do who want "
            "research-based training toward health, business, or graduate study."
        ),
    ),
    dict(
        slug="uva-religious-studies-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Religious Studies",
        department="Department of Religious Studies", cip="38.02", duration_months=48,
        keywords=["religious studies"],
        description=(
            "Religious studies examines the world's religious traditions — their texts, "
            "histories, and practices — through the humanities and social sciences in one "
            "of the largest such departments in the country."
        ),
        who_its_for=(
            "Students drawn to religion as a human phenomenon who want comparative, "
            "interdisciplinary training across traditions."
        ),
    ),
    dict(
        slug="uva-slavic-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Slavic Languages and Literatures",
        department="Department of Slavic Languages and Literatures", cip="16.04",
        duration_months=48, keywords=["Russian", "Slavic", "language"],
        description=(
            "Slavic languages and literatures centers on Russian language and literature "
            "alongside the cultures of the Slavic world, from Tolstoy and Dostoevsky to "
            "contemporary writing and film."
        ),
        who_its_for=(
            "Students drawn to Russian and the Slavic world who want language and literary "
            "depth for international, governmental, or scholarly work."
        ),
    ),
    dict(
        slug="uva-sociology-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Sociology",
        department="Department of Sociology", cip="45.11", duration_months=48,
        keywords=["sociology"],
        description=(
            "Sociology studies social structure, inequality, institutions, and group "
            "behavior, teaching quantitative and qualitative methods for analyzing how "
            "society works."
        ),
        who_its_for=(
            "Students interested in social problems and institutions who want research "
            "skills toward policy, law, or the social sciences."
        ),
    ),
    dict(
        slug="uva-south-asian-studies-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in South Asian Studies",
        department="Program in South Asian Studies", cip="05.01", duration_months=48,
        keywords=["South Asia", "area studies"],
        description=(
            "South Asian studies combines language study with the history, religion, "
            "politics, and literature of India and the wider South Asian region in an "
            "interdisciplinary area major."
        ),
        who_its_for=(
            "Students focused on South Asia who want language plus regional depth for "
            "international or academic careers."
        ),
    ),
    dict(
        slug="uva-spanish-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Spanish",
        department="Department of Spanish, Italian, and Portuguese", cip="16.09",
        duration_months=48, keywords=["Spanish", "language"],
        description=(
            "Spanish develops advanced proficiency alongside the study of the literature "
            "and cultures of Spain and Latin America, with options in linguistics and "
            "translation."
        ),
        who_its_for=(
            "Students committed to Spanish fluency who want literary and cultural depth "
            "for careers across the Spanish-speaking world."
        ),
    ),
    dict(
        slug="uva-statistics-bs", school=_A, degree_type="bachelors",
        program_name="Bachelor of Science in Statistics",
        department="Department of Statistics", cip="27.05", duration_months=48,
        keywords=["statistics", "data"],
        description=(
            "Statistics trains students in probability, statistical inference, and data "
            "analysis, building the computational and modeling skills that underpin data "
            "science and quantitative research."
        ),
        who_its_for=(
            "Quantitatively minded students who want rigorous training in data and "
            "inference toward analytics, data science, or graduate study."
        ),
    ),
    dict(
        slug="uva-women-gender-sexuality-ba", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Women, Gender, and Sexuality",
        department="Department of Women, Gender, and Sexuality", cip="05.02",
        duration_months=48, keywords=["gender studies"],
        description=(
            "Women, gender, and sexuality examines how gender and sexuality shape "
            "societies, cultures, and knowledge, drawing on history, literature, and the "
            "social sciences."
        ),
        who_its_for=(
            "Students drawn to questions of gender and power who want interdisciplinary "
            "training toward law, advocacy, health, or graduate study."
        ),
    ),
    # ───────────── School of Engineering and Applied Science (undergraduate) ─────────────
    dict(
        slug="uva-aerospace-engineering-bs", school=_SEAS, degree_type="bachelors",
        program_name="Bachelor of Science in Aerospace Engineering",
        department="Department of Mechanical and Aerospace Engineering", cip="14.02",
        duration_months=48, keywords=["aerospace engineering"],
        description=(
            "Aerospace engineering applies aerodynamics, propulsion, structures, and "
            "control to the design of aircraft and spacecraft, with laboratory and "
            "capstone design work in flight and space systems."
        ),
        who_its_for=(
            "Students drawn to flight and space who want to design aircraft and spacecraft "
            "and enter the aerospace and defense industries."
        ),
    ),
    dict(
        slug="uva-biomedical-engineering-bs", school=_SEAS, degree_type="bachelors",
        program_name="Bachelor of Science in Biomedical Engineering",
        department="Department of Biomedical Engineering", cip="14.05", duration_months=48,
        keywords=["biomedical engineering"],
        description=(
            "Biomedical engineering applies engineering to medicine and biology — imaging, "
            "biomechanics, biomaterials, and medical devices — in a department jointly "
            "held by the Engineering and Medicine schools."
        ),
        who_its_for=(
            "Students at the intersection of engineering and medicine who want to design "
            "devices and technologies that improve health."
        ),
    ),
    dict(
        slug="uva-chemical-engineering-bs", school=_SEAS, degree_type="bachelors",
        program_name="Bachelor of Science in Chemical Engineering",
        department="Department of Chemical Engineering", cip="14.07", duration_months=48,
        keywords=["chemical engineering"],
        description=(
            "Chemical engineering applies chemistry, thermodynamics, and transport "
            "phenomena to the design of processes that turn raw materials into fuels, "
            "materials, pharmaceuticals, and energy."
        ),
        who_its_for=(
            "Students who like chemistry and quantitative problem-solving and want to work "
            "in energy, materials, pharmaceuticals, or process industries."
        ),
    ),
    dict(
        slug="uva-civil-engineering-bs", school=_SEAS, degree_type="bachelors",
        program_name="Bachelor of Science in Civil Engineering",
        department="Department of Civil and Environmental Engineering", cip="14.08",
        duration_months=48, keywords=["civil engineering"],
        description=(
            "Civil engineering designs and builds infrastructure — structures, "
            "transportation, water resources, and the built environment — with an "
            "emphasis on sustainability and resilient systems."
        ),
        who_its_for=(
            "Students who want to design the bridges, buildings, and infrastructure that "
            "shape communities and the environment."
        ),
    ),
    dict(
        slug="uva-computer-engineering-bs", school=_SEAS, degree_type="bachelors",
        program_name="Bachelor of Science in Computer Engineering",
        department="Department of Electrical and Computer Engineering", cip="14.09",
        duration_months=48, keywords=["computer engineering"],
        description=(
            "Computer engineering spans the hardware-software boundary — digital systems, "
            "embedded computing, and computer architecture — joining electrical "
            "engineering with computer science."
        ),
        who_its_for=(
            "Students who want to build computing systems from the chip up, across "
            "hardware and software."
        ),
    ),
    dict(
        slug="uva-computer-science-bs", school=_SEAS, degree_type="bachelors",
        program_name="Bachelor of Science in Computer Science",
        department="Department of Computer Science", cip="11.07", duration_months=48,
        keywords=["computer science", "CS"],
        description=(
            "The B.S. in computer science is the engineering-school computing degree, "
            "covering algorithms, systems, theory, and software with the full mathematics "
            "and engineering foundation."
        ),
        who_its_for=(
            "Students aiming for software, systems, or computing research who want the "
            "rigorous engineering-school computer science degree."
        ),
    ),
    dict(
        slug="uva-electrical-engineering-bs", school=_SEAS, degree_type="bachelors",
        program_name="Bachelor of Science in Electrical Engineering",
        department="Department of Electrical and Computer Engineering", cip="14.10",
        duration_months=48, keywords=["electrical engineering"],
        description=(
            "Electrical engineering covers circuits, signals, electromagnetics, and "
            "devices, from microelectronics and photonics to communications and power "
            "systems."
        ),
        who_its_for=(
            "Students drawn to electronics, signals, and devices who want to work in "
            "semiconductors, communications, or energy."
        ),
    ),
    dict(
        slug="uva-engineering-science-bs", school=_SEAS, degree_type="bachelors",
        program_name="Bachelor of Science in Engineering Science",
        department="Department of Materials Science and Engineering", cip="14.01",
        duration_months=48, keywords=["engineering science"],
        description=(
            "Engineering science is a flexible, interdisciplinary degree that combines a "
            "strong engineering and science core with a concentration the student designs "
            "across the boundaries of traditional fields."
        ),
        who_its_for=(
            "Students whose interests cross engineering disciplines and who want to design "
            "an individualized technical course of study."
        ),
    ),
    dict(
        slug="uva-materials-science-engineering-bs", school=_SEAS, degree_type="bachelors",
        program_name="Bachelor of Science in Materials Science and Engineering",
        department="Department of Materials Science and Engineering", cip="14.18",
        duration_months=48, keywords=["materials science"],
        description=(
            "Materials science and engineering studies the structure, properties, and "
            "processing of metals, ceramics, polymers, and semiconductors that enable new "
            "technologies in energy, electronics, and medicine."
        ),
        who_its_for=(
            "Students fascinated by how materials work at the atomic scale who want to "
            "engineer the materials behind new technology."
        ),
    ),
    dict(
        slug="uva-mechanical-engineering-bs", school=_SEAS, degree_type="bachelors",
        program_name="Bachelor of Science in Mechanical Engineering",
        department="Department of Mechanical and Aerospace Engineering", cip="14.19",
        duration_months=48, keywords=["mechanical engineering"],
        description=(
            "Mechanical engineering applies mechanics, thermodynamics, and design to "
            "machines and energy systems, from robotics and manufacturing to fluid and "
            "thermal systems, capped by a team design project."
        ),
        who_its_for=(
            "Hands-on problem-solvers who want a broad engineering degree spanning "
            "robotics, energy, manufacturing, and design."
        ),
    ),
    dict(
        slug="uva-systems-engineering-bs", school=_SEAS, degree_type="bachelors",
        program_name="Bachelor of Science in Systems Engineering",
        department="Department of Systems and Information Engineering", cip="14.27",
        duration_months=48, keywords=["systems engineering"],
        description=(
            "Systems engineering applies optimization, probability, and data analytics to "
            "design and manage complex systems — in healthcare, transportation, and "
            "industry — in one of the few undergraduate systems-engineering programs in "
            "the country."
        ),
        who_its_for=(
            "Students who like engineering plus data and decision-making and want to "
            "optimize complex systems across industries."
        ),
    ),
    # ───────────── McIntire School of Commerce (undergraduate) ─────────────
    dict(
        slug="uva-commerce-bs", school=_MCINTIRE, degree_type="bachelors",
        program_name="Bachelor of Science in Commerce",
        department="McIntire School of Commerce", cip="52.01", duration_months=48,
        keywords=["commerce", "business", "finance"],
        description=(
            "The B.S. in Commerce is McIntire's selective undergraduate business degree, "
            "with concentrations in finance, accounting, marketing, management, and "
            "information technology built on an integrated core and a global immersion."
        ),
        who_its_for=(
            "High-achieving students recruiting into finance, consulting, or business who "
            "want one of the nation's top undergraduate business degrees."
        ),
    ),
    # ───────────── School of Architecture (undergraduate) ─────────────
    dict(
        slug="uva-architecture-bs", school=_ARCH, degree_type="bachelors",
        program_name="Bachelor of Science in Architecture",
        department="Department of Architecture", cip="04.02", duration_months=48,
        keywords=["architecture", "design"],
        description=(
            "The undergraduate architecture degree joins design studios with the history "
            "and theory of architecture and building technology, on Grounds shaped by "
            "Jefferson's own architecture."
        ),
        who_its_for=(
            "Students drawn to design and the built environment who want a studio-based "
            "path toward architecture or graduate design study."
        ),
    ),
    dict(
        slug="uva-urban-environmental-planning-bup", school=_ARCH, degree_type="bachelors",
        program_name="Bachelor of Urban and Environmental Planning",
        department="Department of Urban and Environmental Planning", cip="04.03",
        duration_months=48, keywords=["urban planning", "environmental planning"],
        description=(
            "Urban and environmental planning studies how cities and regions grow and "
            "change, joining design, policy, and environmental analysis to shape "
            "communities, housing, and land use."
        ),
        who_its_for=(
            "Students who want to shape cities and the environment through planning, "
            "policy, and community design."
        ),
    ),
    dict(
        slug="uva-architectural-history-ba", school=_ARCH, degree_type="bachelors",
        program_name="Bachelor of Arts in Architectural History",
        department="Department of Architectural History", cip="04.08", duration_months=48,
        keywords=["architectural history"],
        description=(
            "Architectural history studies buildings, landscapes, and cities as cultural "
            "documents across periods and places, with UVA's Jeffersonian Grounds — a "
            "UNESCO World Heritage Site — as a living classroom."
        ),
        who_its_for=(
            "Students drawn to the history of the built environment who want a path toward "
            "preservation, museums, or graduate study."
        ),
    ),
    # ───────────── School of Nursing (undergraduate) ─────────────
    dict(
        slug="uva-nursing-bsn", school=_NURSING, degree_type="bachelors",
        program_name="Bachelor of Science in Nursing",
        department="School of Nursing", cip="51.38", duration_months=48,
        keywords=["nursing", "BSN"],
        description=(
            "The Bachelor of Science in Nursing prepares students for registered-nurse "
            "licensure through clinical rotations at UVA Health and coursework in the "
            "sciences, patient care, and population health."
        ),
        who_its_for=(
            "Students committed to a nursing career who want clinical training in an "
            "academic medical center alongside a research university education."
        ),
    ),
    # ───────────── School of Education and Human Development (undergraduate) ─────────────
    dict(
        slug="uva-kinesiology-bsed", school=_EDUC, degree_type="bachelors",
        program_name="Bachelor of Science in Education in Kinesiology",
        department="Department of Kinesiology", cip="31.05", duration_months=48,
        keywords=["kinesiology", "exercise science"],
        description=(
            "Kinesiology studies human movement, exercise physiology, and biomechanics, "
            "preparing students for the health professions, athletic training, and "
            "graduate work in the movement and rehabilitation sciences."
        ),
        who_its_for=(
            "Students interested in human movement and health who are headed for physical "
            "therapy, medicine, or the exercise sciences."
        ),
    ),
    dict(
        slug="uva-youth-social-innovation-bsed", school=_EDUC, degree_type="bachelors",
        program_name="Bachelor of Science in Education in Youth and Social Innovation",
        department="Department of Human Services", cip="19.07", duration_months=48,
        keywords=["youth", "social innovation"],
        description=(
            "Youth and social innovation studies child and adolescent development and the "
            "design of programs and policies that support young people and their "
            "communities."
        ),
        who_its_for=(
            "Students who want to work with and for young people through education, "
            "nonprofits, policy, or social entrepreneurship."
        ),
    ),
    dict(
        slug="uva-speech-communication-disorders-bsed", school=_EDUC, degree_type="bachelors",
        program_name="Bachelor of Science in Education in Speech Communication Disorders",
        department="Department of Human Services", cip="51.02", duration_months=48,
        keywords=["speech", "communication disorders"],
        description=(
            "Speech communication disorders introduces the science of human communication "
            "and its disorders, preparing students for graduate study in "
            "speech-language pathology and audiology."
        ),
        who_its_for=(
            "Students headed for speech-language pathology or audiology who want the "
            "scientific foundation for graduate clinical training."
        ),
    ),
    # ───────────── School of Data Science (undergraduate) ─────────────
    dict(
        slug="uva-data-science-bs", school=_DATASCI, degree_type="bachelors",
        program_name="Bachelor of Science in Data Science",
        department="School of Data Science", cip="30.70", duration_months=48,
        keywords=["data science"],
        description=(
            "The B.S. in Data Science combines statistics, computing, and machine learning "
            "with data ethics and a domain application, in degrees offered through UVA's "
            "School of Data Science."
        ),
        who_its_for=(
            "Students who want to turn data into insight and care about doing it "
            "responsibly across science, business, and society."
        ),
    ),
    # ───────────── Frank Batten School (undergraduate) ─────────────
    dict(
        slug="uva-public-policy-leadership-ba", school=_BATTEN, degree_type="bachelors",
        program_name="Bachelor of Arts in Public Policy and Leadership",
        department="Frank Batten School of Leadership and Public Policy", cip="44.05",
        duration_months=48, keywords=["public policy", "leadership"],
        description=(
            "Public policy and leadership trains students to analyze policy with economics, "
            "statistics, and ethics and to lead in the public interest, in Batten's "
            "small-cohort major that culminates in an applied policy project."
        ),
        who_its_for=(
            "Students committed to public service who want analytic and leadership "
            "training toward government, advocacy, or policy careers."
        ),
    ),
    # ═════════════ GRADUATE & PROFESSIONAL ═════════════
    # ── Darden School of Business ──
    dict(
        slug="uva-darden-mba", school=_DARDEN, degree_type="masters",
        program_name="Master of Business Administration",
        department="Darden School of Business", cip="52.02", duration_months=21,
        keywords=["MBA", "Darden", "business"], tuition=_MBA,
        cost_source=_BOV_SRC,
        cost_note=(
            "2025-26 Darden Full-Time M.B.A. non-resident annual tuition (Board of "
            "Visitors); Virginia residents pay $75,762."
        ),
        description=(
            "Darden's Full-Time M.B.A. teaches general management through the case method, "
            "with first-year learning teams and a curriculum consistently ranked at the "
            "top for teaching quality and student experience."
        ),
        who_its_for=(
            "Early-career professionals seeking general-management and leadership roles in "
            "consulting, finance, or industry who want an immersive case-method M.B.A."
        ),
    ),
    dict(
        slug="uva-mcintire-ms-commerce", school=_MCINTIRE, degree_type="masters",
        program_name="Master of Science in Commerce",
        department="McIntire School of Commerce", cip="52.01", duration_months=10,
        keywords=["commerce", "business", "specialized master's"], tuition=_MS_COMMERCE,
        cost_source=_BOV_SRC,
        cost_note=(
            "2025-26 M.S. in Commerce non-resident annual tuition (Board of Visitors); "
            "Virginia residents pay $47,850."
        ),
        description=(
            "The M.S. in Commerce is a one-year pre-experience master's for non-business "
            "undergraduates, with tracks in finance, business analytics, and marketing and "
            "management and a global immersion."
        ),
        who_its_for=(
            "Recent liberal-arts, science, or engineering graduates who want to convert "
            "their degree into business skills and recruiting access in one year."
        ),
    ),
    dict(
        slug="uva-mcintire-ms-business-analytics", school=_MCINTIRE, degree_type="masters",
        program_name="Master of Science in Business Analytics",
        department="McIntire School of Commerce", cip="52.13", duration_months=12,
        keywords=["business analytics", "data"], tuition=_MSBA,
        cost_source=_BOV_SRC,
        cost_note=(
            "2025-26 M.S. in Business Analytics program tuition (McIntire-Darden joint "
            "degree, Board of Visitors)."
        ),
        description=(
            "The M.S. in Business Analytics, offered jointly by McIntire and Darden, trains "
            "working professionals to apply data analytics, machine learning, and "
            "data-driven decision-making to business problems in a part-time format."
        ),
        who_its_for=(
            "Working professionals who want to add rigorous analytics and data skills to "
            "their business careers without leaving the workforce."
        ),
    ),
    # ── School of Law ──
    dict(
        slug="uva-juris-doctor-jd", school=_LAW, degree_type="professional",
        program_name="Juris Doctor",
        department="School of Law", cip="22.01", duration_months=36,
        keywords=["law", "JD", "juris doctor"], tuition=_JD,
        cost_source=_BOV_SRC,
        cost_note=(
            "2025-26 J.D. non-resident annual tuition (Board of Visitors); Virginia "
            "residents pay $74,078."
        ),
        description=(
            "UVA's three-year Juris Doctor combines a rigorous doctrinal foundation with "
            "deep clinical and pro bono opportunities, and is known for outstanding "
            "clerkship and large-firm placement and a notably collegial student culture."
        ),
        who_its_for=(
            "Aspiring lawyers seeking elite firm, clerkship, or public-interest careers "
            "who want a top law school with a famously supportive community."
        ),
    ),
    dict(
        slug="uva-master-of-laws-llm", school=_LAW, degree_type="masters",
        program_name="Master of Laws",
        department="School of Law", cip="22.02", duration_months=9,
        keywords=["LLM", "law"], tuition=_LLM,
        cost_source=_BOV_SRC,
        cost_note=(
            "2025-26 LL.M. non-resident annual tuition (Board of Visitors); Virginia "
            "residents pay $74,078."
        ),
        description=(
            "The Master of Laws is a one-year graduate law degree for lawyers trained "
            "abroad and other attorneys, offering advanced study in U.S. and "
            "international law alongside J.D. students."
        ),
        who_its_for=(
            "Internationally trained lawyers and attorneys who want a year of advanced "
            "legal study in the U.S. system."
        ),
    ),
    # ── School of Medicine ──
    dict(
        slug="uva-doctor-of-medicine-md", school=_MEDICINE, degree_type="professional",
        program_name="Doctor of Medicine",
        department="School of Medicine", cip="51.12", duration_months=48,
        keywords=["medicine", "MD", "medical school"], tuition=_MD,
        cost_source=_BOV_SRC,
        cost_note=(
            "2025-26 M.D. first-year non-resident tuition (Board of Visitors); tuition "
            "steps down slightly each subsequent year, and Virginia residents pay less."
        ),
        description=(
            "UVA's M.D. is taught through the 'Cells to Society' curriculum, which "
            "integrates basic and clinical science with early patient contact, and "
            "graduates match into residencies across the full range of specialties."
        ),
        who_its_for=(
            "Future physicians who want an integrated, early-clinical medical education at "
            "an academic medical center with strong residency-match outcomes."
        ),
    ),
    dict(
        slug="uva-master-of-public-health-mph", school=_MEDICINE, degree_type="masters",
        program_name="Master of Public Health",
        department="Department of Public Health Sciences", cip="51.22", duration_months=24,
        keywords=["public health", "MPH"], tuition=_MPH,
        cost_source=_BOV_SRC,
        cost_note=(
            "2025-26 M.P.H. non-resident annual tuition (Board of Visitors); Virginia "
            "residents pay $21,370."
        ),
        description=(
            "The Master of Public Health trains students in epidemiology, biostatistics, "
            "and health policy to improve population health, with practice experience "
            "drawing on UVA Health and the surrounding region."
        ),
        who_its_for=(
            "Students and clinicians who want population-health, epidemiology, and policy "
            "skills for careers in public health and health systems."
        ),
    ),
    # ── Frank Batten School ──
    dict(
        slug="uva-master-of-public-policy-mpp", school=_BATTEN, degree_type="masters",
        program_name="Master of Public Policy",
        department="Frank Batten School of Leadership and Public Policy", cip="44.05",
        duration_months=24, keywords=["public policy", "MPP"], tuition=_MPP,
        cost_source=_BOV_SRC,
        cost_note=(
            "2025-26 Batten graduate non-resident annual tuition (Board of Visitors); "
            "Virginia residents pay $31,006."
        ),
        description=(
            "The Master of Public Policy trains analysts and leaders in economics, "
            "statistics, and ethics for evidence-based policymaking, in a small-cohort "
            "program with individualized career support and a strong public-service ethos."
        ),
        who_its_for=(
            "Aspiring policy analysts and public leaders who want quantitative and "
            "leadership training in a close-knit, mission-driven cohort."
        ),
    ),
    # ── School of Data Science ──
    dict(
        slug="uva-ms-data-science", school=_DATASCI, degree_type="masters",
        program_name="Master of Science in Data Science",
        department="School of Data Science", cip="30.70", duration_months=12,
        keywords=["data science", "MSDS"], tuition=_MSDS,
        cost_source=_BOV_SRC,
        cost_note=(
            "2025-26 residential M.S. in Data Science non-resident annual tuition (Board of "
            "Visitors); Virginia residents pay $39,159; a fully online format is also "
            "offered at $1,467 per credit."
        ),
        description=(
            "The M.S. in Data Science is a one-year professional degree in statistics, "
            "machine learning, computing, and data ethics, offered in residential and "
            "fully online formats with strong career outcomes."
        ),
        who_its_for=(
            "Graduates and working professionals who want to move into data-science and "
            "machine-learning roles, in person or online."
        ),
    ),
    dict(
        slug="uva-phd-data-science", school=_DATASCI, degree_type="phd",
        program_name="Doctor of Philosophy in Data Science",
        department="School of Data Science", cip="30.70", duration_months=60,
        keywords=["data science", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. in Data Science supports original research in the methods and "
            "foundations of data science — machine learning, statistics, and responsible "
            "AI — and their application across disciplines."
        ),
        who_its_for=(
            "Students aiming for research careers in data science and AI who want funded "
            "doctoral study spanning methods and applications."
        ),
    ),
    # ── School of Engineering (graduate) ──
    dict(
        slug="uva-ms-computer-science", school=_SEAS, degree_type="masters",
        program_name="Master of Science in Computer Science",
        department="Department of Computer Science", cip="11.07", duration_months=24,
        keywords=["computer science", "CS", "graduate"],
        omit_tuition_reason=_PC_ENG,
        description=(
            "The M.S. in Computer Science offers advanced study and research across "
            "systems, theory, machine learning, and security, with thesis and "
            "course-based paths for students deepening their computing expertise."
        ),
        who_its_for=(
            "Computing graduates who want advanced technical depth or a bridge into "
            "doctoral research before industry or academia."
        ),
    ),
    dict(
        slug="uva-ms-systems-engineering", school=_SEAS, degree_type="masters",
        program_name="Master of Science in Systems Engineering",
        department="Department of Systems and Information Engineering", cip="14.27",
        duration_months=24, keywords=["systems engineering", "graduate"],
        omit_tuition_reason=_PC_ENG,
        description=(
            "The M.S. in Systems Engineering advances optimization, data analytics, and "
            "the modeling of complex sociotechnical systems in domains such as healthcare, "
            "transportation, and risk."
        ),
        who_its_for=(
            "Engineers and analysts who want graduate training in optimizing and managing "
            "complex systems with data."
        ),
    ),
    dict(
        slug="uva-ms-biomedical-engineering", school=_SEAS, degree_type="masters",
        program_name="Master of Science in Biomedical Engineering",
        department="Department of Biomedical Engineering", cip="14.05", duration_months=24,
        keywords=["biomedical engineering", "graduate"],
        omit_tuition_reason=_PC_ENG,
        description=(
            "The M.S. in Biomedical Engineering advances research in imaging, "
            "biomechanics, biomaterials, and medical devices through a department shared "
            "by the Engineering and Medicine schools."
        ),
        who_its_for=(
            "Engineers and scientists who want graduate training at the interface of "
            "engineering and medicine."
        ),
    ),
    dict(
        slug="uva-phd-computer-science", school=_SEAS, degree_type="phd",
        program_name="Doctor of Philosophy in Computer Science",
        department="Department of Computer Science", cip="11.07", duration_months=60,
        keywords=["computer science", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. in Computer Science supports original research across systems, "
            "theory, artificial intelligence, security, and human-computer interaction, "
            "with funded study toward research careers."
        ),
        who_its_for=(
            "Students pursuing research careers in computing who want funded doctoral work "
            "with leading faculty."
        ),
    ),
    dict(
        slug="uva-phd-systems-engineering", school=_SEAS, degree_type="phd",
        program_name="Doctor of Philosophy in Systems Engineering",
        department="Department of Systems and Information Engineering", cip="14.27",
        duration_months=60, keywords=["systems engineering", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. in Systems Engineering supports research in optimization, data "
            "analytics, and the modeling of complex sociotechnical systems across "
            "healthcare, transportation, and risk analysis."
        ),
        who_its_for=(
            "Students aiming for research careers in systems and data who want funded "
            "doctoral study."
        ),
    ),
    dict(
        slug="uva-phd-biomedical-engineering", school=_SEAS, degree_type="phd",
        program_name="Doctor of Philosophy in Biomedical Engineering",
        department="Department of Biomedical Engineering", cip="14.05", duration_months=60,
        keywords=["biomedical engineering", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. in Biomedical Engineering supports research in imaging, "
            "biomechanics, biomaterials, and medical devices, jointly mentored across the "
            "Engineering and Medicine schools."
        ),
        who_its_for=(
            "Students pursuing research careers at the engineering-medicine interface who "
            "want funded doctoral study."
        ),
    ),
    # ── Graduate School of Arts & Sciences (PhD) ──
    dict(
        slug="uva-phd-economics", school=_GRAD, degree_type="phd",
        program_name="Doctor of Philosophy in Economics",
        department="Department of Economics", cip="45.06", duration_months=60,
        keywords=["economics", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. in Economics trains research economists in microeconomic and "
            "macroeconomic theory and econometrics, with fields from public and labor "
            "economics to international and financial economics."
        ),
        who_its_for=(
            "Students aiming for research and faculty careers in economics who want funded "
            "doctoral training."
        ),
    ),
    dict(
        slug="uva-phd-english", school=_GRAD, degree_type="phd",
        program_name="Doctor of Philosophy in English",
        department="Department of English", cip="23.01", duration_months=60,
        keywords=["English", "literature", "PhD"], funded=True,
        description=(
            "The Ph.D. in English supports advanced research in literature in English "
            "across periods, with departmental strengths in American literature, "
            "textual studies, and the digital humanities."
        ),
        who_its_for=(
            "Students pursuing scholarly and teaching careers in literary studies who want "
            "funded doctoral work."
        ),
    ),
    dict(
        slug="uva-phd-history", school=_GRAD, degree_type="phd",
        program_name="Doctor of Philosophy in History",
        department="Corcoran Department of History", cip="54.01", duration_months=60,
        keywords=["history", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. in History trains historians through archival research and "
            "field-defining scholarship across American, European, and global history."
        ),
        who_its_for=(
            "Students aiming for research and teaching careers in history who want funded "
            "doctoral training."
        ),
    ),
    dict(
        slug="uva-phd-psychology", school=_GRAD, degree_type="phd",
        program_name="Doctor of Philosophy in Psychology",
        department="Department of Psychology", cip="42.01", duration_months=60,
        keywords=["psychology", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. in Psychology supports research across cognitive, developmental, "
            "clinical, social, and quantitative psychology, with laboratory training "
            "toward research and academic careers."
        ),
        who_its_for=(
            "Students pursuing research careers in psychology who want funded doctoral "
            "study in a research area of focus."
        ),
    ),
    dict(
        slug="uva-phd-physics", school=_GRAD, degree_type="phd",
        program_name="Doctor of Philosophy in Physics",
        department="Department of Physics", cip="40.08", duration_months=60,
        keywords=["physics", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. in Physics supports research in condensed-matter, nuclear, "
            "high-energy, and biological physics, with funded study toward careers in "
            "research and academia."
        ),
        who_its_for=(
            "Students aiming for research careers in physics who want funded doctoral "
            "study with active research groups."
        ),
    ),
    dict(
        slug="uva-phd-chemistry", school=_GRAD, degree_type="phd",
        program_name="Doctor of Philosophy in Chemistry",
        department="Department of Chemistry", cip="40.05", duration_months=60,
        keywords=["chemistry", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. in Chemistry supports original research across organic, inorganic, "
            "physical, analytical, and biological chemistry, with funded study and "
            "laboratory training toward research careers."
        ),
        who_its_for=(
            "Students pursuing research careers in chemistry who want funded doctoral work "
            "in a faculty research group."
        ),
    ),
    dict(
        slug="uva-phd-biology", school=_GRAD, degree_type="phd",
        program_name="Doctor of Philosophy in Biology",
        department="Department of Biology", cip="26.01", duration_months=60,
        keywords=["biology", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. in Biology supports research from molecular and cellular biology to "
            "ecology and evolution, with funded laboratory and field study toward research "
            "careers."
        ),
        who_its_for=(
            "Students aiming for research careers in the life sciences who want funded "
            "doctoral study across biological scales."
        ),
    ),
    # ── School of Nursing (graduate) ──
    dict(
        slug="uva-msn", school=_NURSING, degree_type="masters",
        program_name="Master of Science in Nursing",
        department="School of Nursing", cip="51.38", duration_months=24,
        keywords=["nursing", "MSN", "graduate"],
        omit_tuition_reason=_PC_MSN,
        description=(
            "The Master of Science in Nursing prepares nurses for advanced roles such as "
            "the clinical nurse leader, building on clinical practice at UVA Health and "
            "graduate coursework in care and leadership."
        ),
        who_its_for=(
            "Registered nurses who want to advance into leadership and specialized "
            "clinical roles."
        ),
    ),
    dict(
        slug="uva-dnp", school=_NURSING, degree_type="phd",
        program_name="Doctor of Nursing Practice",
        department="School of Nursing", cip="51.38", duration_months=36,
        keywords=["nursing", "DNP", "doctoral"], tuition=_DNP,
        cost_source=_BOV_SRC,
        cost_note=(
            "2025-26 Doctor of Nursing Practice non-resident annual tuition (Board of "
            "Visitors); Virginia residents pay $21,942."
        ),
        description=(
            "The Doctor of Nursing Practice is the terminal practice doctorate, preparing "
            "advanced-practice nurses and nurse leaders to translate evidence into "
            "improved clinical care and health systems."
        ),
        who_its_for=(
            "Nurses pursuing the highest level of clinical practice and leadership, "
            "including advanced-practice and nurse-executive roles."
        ),
    ),
    dict(
        slug="uva-phd-nursing", school=_NURSING, degree_type="phd",
        program_name="Doctor of Philosophy in Nursing",
        department="School of Nursing", cip="51.38", duration_months=48,
        keywords=["nursing", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. in Nursing prepares nurse scientists to lead original research in "
            "areas such as chronic illness, aging, and health equity."
        ),
        who_its_for=(
            "Nurses aiming for research and faculty careers who want funded doctoral "
            "training in nursing science."
        ),
    ),
    # ── School of Architecture (graduate) ──
    dict(
        slug="uva-march", school=_ARCH, degree_type="masters",
        program_name="Master of Architecture",
        department="Department of Architecture", cip="04.02", duration_months=36,
        keywords=["architecture", "MArch", "design"],
        omit_tuition_reason=_PC_ARCH,
        description=(
            "The Master of Architecture is the professional, accreditation-track degree, "
            "centered on design studios with history, theory, and building technology for "
            "students entering the practice of architecture."
        ),
        who_its_for=(
            "Students pursuing licensure and a career in architecture, including those "
            "without an undergraduate architecture degree."
        ),
    ),
    dict(
        slug="uva-murp", school=_ARCH, degree_type="masters",
        program_name="Master of Urban and Environmental Planning",
        department="Department of Urban and Environmental Planning", cip="04.03",
        duration_months=24, keywords=["urban planning", "environmental planning"],
        omit_tuition_reason=_PC_ARCH,
        description=(
            "The Master of Urban and Environmental Planning trains planners in land use, "
            "housing, transportation, and environmental policy to shape sustainable and "
            "equitable communities."
        ),
        who_its_for=(
            "Students who want a professional career in city, regional, or environmental "
            "planning."
        ),
    ),
    dict(
        slug="uva-mla", school=_ARCH, degree_type="masters",
        program_name="Master of Landscape Architecture",
        department="Department of Landscape Architecture", cip="04.06", duration_months=36,
        keywords=["landscape architecture", "design"],
        omit_tuition_reason=_PC_ARCH,
        description=(
            "The Master of Landscape Architecture is the professional degree in designing "
            "landscapes and public space, joining ecology and design to address climate, "
            "water, and the built environment."
        ),
        who_its_for=(
            "Students pursuing licensure and a career in landscape architecture and "
            "ecological design."
        ),
    ),
    # ── School of Education and Human Development (graduate) ──
    dict(
        slug="uva-master-of-teaching", school=_EDUC, degree_type="masters",
        program_name="Master of Teaching",
        department="Department of Curriculum, Instruction, and Special Education",
        cip="13.12", duration_months=12, keywords=["teaching", "teacher education"],
        tuition=_MT, cost_source=_BOV_SRC,
        cost_note=(
            "2025-26 Master of Teaching 12-month non-resident tuition (Board of Visitors); "
            "Virginia residents pay $24,810."
        ),
        description=(
            "The Master of Teaching prepares candidates for licensure across elementary, "
            "secondary, and special education, combining coursework with extensive "
            "supervised clinical experience in schools."
        ),
        who_its_for=(
            "Aspiring teachers seeking licensure and a master's degree with substantial "
            "classroom practice."
        ),
    ),
]



PROGRAMS: list[dict] = [
    {
        "slug": r["slug"],
        "school": r["school"],
        "program_name": r["program_name"],
        "degree_type": r["degree_type"],
        "department": r["department"],
        "duration_months": r["duration_months"],
        "delivery_format": r.get("delivery_format", "on_campus"),
        "keywords": list(r["keywords"]),
        "description": r["description"],
        "cip": r["cip"],
        "who_its_for": r["who_its_for"],
        "tuition": r.get("tuition"),
        "funded": r.get("funded", False),
        "cost_note": r.get("cost_note"),
        "cost_source": r.get("cost_source"),
        "omit_tuition_reason": r.get("omit_tuition_reason"),
    }
    for r in _CATALOG
]

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

if len(set(PROGRAM_SLUGS)) != len(PROGRAM_SLUGS):
    _seen: set[str] = set()
    _dups = [s for s in PROGRAM_SLUGS if s in _seen or _seen.add(s)]
    raise RuntimeError(f"duplicate program slug(s): {sorted(set(_dups))}")
_name_keys = [(p["program_name"], p["degree_type"]) for p in PROGRAMS]
if len(set(_name_keys)) != len(_name_keys):
    raise RuntimeError("duplicate (program_name, degree_type) in UVA catalog")

# ── Concentrations / tracks (belong on the program, not as separate rows) ──
_TRACKS_BY_SLUG: dict[str, list[str]] = {
    "uva-commerce-bs": [
        "Finance",
        "Accounting",
        "Marketing",
        "Management",
        "Information Technology",
    ],
    "uva-politics-ba": [
        "American Politics",
        "Comparative Politics",
        "International Relations",
        "Political Theory",
    ],
    "uva-global-studies-ba": [
        "Global Development Studies",
        "Global Public Health",
        "Global Security and Justice",
        "Environments and Sustainability",
        "Middle East and South Asia",
    ],
    "uva-mcintire-ms-commerce": ["Finance", "Business Analytics", "Marketing and Management"],
}

# ── Outcomes (institution-wide; UVA publishes outcomes per-school, not per-program) ──
_OUTCOMES_CONDITIONS = (
    "Institution-wide median earnings of federally aided students measured 10 years after "
    "entry (U.S. Dept. of Education College Scorecard); not a program-specific figure."
)
_OUTCOMES_INSTITUTION = {
    "median_salary": 86863,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry (institution-wide)",
    "conditions": _OUTCOMES_CONDITIONS,
    "source": "U.S. Dept. of Education College Scorecard (UVA, UNITID 234076)",
    "source_url": "https://collegescorecard.ed.gov/school/?234076",
}

# ── Admissions requirement sets ────────────────────────────────────────────
_REQ_UNDERGRAD = {
    "materials": [
        "Common Application",
        "UVA writing supplement",
        "Secondary-school transcript + school report",
        "Counselor and teacher recommendations",
        "Standardized test scores (test-optional policy; SAT or ACT if submitted)",
    ],
    "deadlines": {
        "early_action": "November 1",
        "early_decision": "November 1",
        "regular_decision": "January 1",
    },
    "source": "https://admission.virginia.edu/",
}
_REQ_GRAD_GENERIC = {
    "materials": [
        "Online application",
        "Transcripts from all prior institutions",
        "Letters of recommendation",
        "Statement of purpose",
        "Standardized / English-proficiency scores where required by the program",
    ],
    "deadlines": {
        "note": "Deadlines vary by program; see the program's official admissions page.",
    },
    "source": "https://graduate.as.virginia.edu/admissions",
}
_REQ_MBA = {
    "materials": [
        "Darden application + essays",
        "GMAT, GRE, or Executive Assessment score (waivers considered)",
        "Undergraduate transcripts",
        "Recommendation",
        "Resume + interview",
    ],
    "deadlines": {"round_1": "Fall", "round_2": "January", "round_3": "Spring"},
    "source": "https://www.darden.virginia.edu/mba/admissions",
}
_REQ_LAW = {
    "materials": [
        "LSAC application + personal statement",
        "LSAT or GRE score",
        "Undergraduate transcripts (CAS report)",
        "Letters of recommendation",
        "Resume",
    ],
    "deadlines": {"regular_decision": "Rolling (see admissions site)"},
    "source": "https://www.law.virginia.edu/admissions",
}
_REQ_MED = {
    "materials": [
        "AMCAS application + UVA secondary",
        "MCAT score",
        "Undergraduate transcripts",
        "Letters of recommendation",
        "Interviews as required",
    ],
    "deadlines": {"primary": "AMCAS deadline (see admissions site)"},
    "source": "https://med.virginia.edu/md-program/admissions/",
}


def _requirements_for(spec: dict) -> dict:
    school = spec["school"]
    if school == _LAW:
        return dict(_REQ_LAW)
    if school == _MEDICINE and spec["degree_type"] == "professional":
        return dict(_REQ_MED)
    if spec["slug"] == "uva-darden-mba":
        return dict(_REQ_MBA)
    if spec["degree_type"] == "bachelors":
        return dict(_REQ_UNDERGRAD)
    return dict(_REQ_GRAD_GENERIC)


# ── External reviews — MBAn shape; gathered → summarized → cited (cautions included) ──
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "uva-darden-mba": {
        "summary": (
            "Darden's Full-Time M.B.A. is consistently ranked among the very best public "
            "M.B.A. programs and is celebrated for its case-method teaching and student "
            "experience. The Class of 2025 reported a median base salary of $175,000, with "
            "about 90% of graduates receiving an offer within three months; consulting and "
            "financial services are the largest destinations."
        ),
        "themes": [
            {
                "label": "Top-ranked teaching & experience",
                "sentiment": "positive",
                "detail": (
                    "Darden has repeatedly topped Princeton Review's Best Professors and "
                    "Best Classroom Experience lists."
                ),
            },
            {
                "label": "Strong recruiting outcomes",
                "sentiment": "positive",
                "detail": (
                    "Consulting (about 40%) and finance are the leading destinations, with "
                    "a median base salary of $175,000 for the Class of 2025."
                ),
            },
            {
                "label": "Supportive, collaborative culture",
                "sentiment": "positive",
                "detail": (
                    "First-year learning teams and a close community are frequently cited "
                    "as a defining strength."
                ),
            },
            {
                "label": "Case-method intensity",
                "sentiment": "caution",
                "detail": (
                    "The case method demands heavy daily preparation and active cold-call "
                    "participation — rewarding for some, demanding for those who prefer "
                    "lecture or flexibility."
                ),
            },
            {
                "label": "Cost",
                "sentiment": "caution",
                "detail": (
                    "Two-year non-resident cost of attendance exceeds $240,000; merit "
                    "scholarships are available but debt financing is common."
                ),
            },
        ],
        "sources": [
            {
                "label": "Darden Full-Time M.B.A. — Employment Data",
                "url": "https://www.darden.virginia.edu/mba/career-support/employment-data",
            },
            {
                "label": "Poets & Quants — UVA Darden profile",
                "url": "https://poetsandquants.com/school/university-of-virginia-darden-school-of-business/",
            },
        ],
        "disclaimer": (
            "Themes are aggregated and paraphrased from public third-party coverage and "
            "official employment reports, not individual verbatim reviews."
        ),
    },
    "uva-juris-doctor-jd": {
        "summary": (
            "UVA Law is one of the country's top law schools, known for outstanding "
            "employment and clerkship outcomes alongside an unusually collegial culture. "
            "About 97% of the Class of 2023 secured full-time, long-term, "
            "bar-passage-required or J.D.-advantage jobs, with strong large-firm and "
            "federal-clerkship placement."
        ),
        "themes": [
            {
                "label": "Elite employment outcomes",
                "sentiment": "positive",
                "detail": (
                    "Large-firm and federal-clerkship placement are among the strongest in "
                    "the country, with a $225,000 median private-sector salary."
                ),
            },
            {
                "label": "Collegial culture",
                "sentiment": "positive",
                "detail": (
                    "UVA Law is repeatedly ranked at or near the top for quality of life "
                    "and student community."
                ),
            },
            {
                "label": "Clerkship strength",
                "sentiment": "positive",
                "detail": (
                    "The school consistently places a high share of graduates into "
                    "judicial clerkships, including at the federal level."
                ),
            },
            {
                "label": "Cost and selectivity",
                "sentiment": "caution",
                "detail": (
                    "Tuition is high and admission is extremely selective; outcomes are "
                    "strong but the financial commitment is significant."
                ),
            },
        ],
        "sources": [
            {
                "label": "UVA Law — Employment Data",
                "url": "https://www.law.virginia.edu/career-services/careers/employment-data",
            },
            {
                "label": "UVA Law — Bar Passage Data",
                "url": "https://www.law.virginia.edu/career-services/bar-passage-data-recent-graduates",
            },
        ],
        "disclaimer": (
            "Themes are aggregated and paraphrased from public third-party coverage and "
            "official ABA employment disclosures, not individual verbatim reviews."
        ),
    },
    "uva-doctor-of-medicine-md": {
        "summary": (
            "UVA's School of Medicine pairs its integrated 'Cells to Society' curriculum "
            "with strong residency-match outcomes, placing graduates across a wide range "
            "of specialties each year. Student debt at graduation is notably below the "
            "national average."
        ),
        "themes": [
            {
                "label": "Integrated curriculum",
                "sentiment": "positive",
                "detail": (
                    "The 'Cells to Society' curriculum integrates basic and clinical "
                    "science with early patient contact."
                ),
            },
            {
                "label": "Strong match outcomes",
                "sentiment": "positive",
                "detail": (
                    "Graduates match into residencies across the full range of "
                    "specialties at a high rate each year."
                ),
            },
            {
                "label": "Relatively low debt",
                "sentiment": "positive",
                "detail": (
                    "Average graduating debt is below the national average, aided by "
                    "financial-aid support."
                ),
            },
            {
                "label": "Curriculum still evolving",
                "sentiment": "mixed",
                "detail": (
                    "Some students note that the innovative curriculum's implementation "
                    "and responsiveness to feedback are still maturing."
                ),
            },
        ],
        "sources": [
            {
                "label": "UVA School of Medicine — Residency Match Results",
                "url": "https://med.virginia.edu/md-program/student-affairs/student-resources/residency-match-results/",
            },
            {
                "label": "UVA School of Medicine — Facts & Figures",
                "url": "https://med.virginia.edu/about-uva-som/facts-and-figures/",
            },
        ],
        "disclaimer": (
            "Themes are aggregated and paraphrased from public third-party coverage and "
            "official school reports, not individual verbatim reviews."
        ),
    },
    "uva-commerce-bs": {
        "summary": (
            "McIntire's B.S. in Commerce is regularly ranked among the top undergraduate "
            "business programs in the country, with strong placement into finance and "
            "consulting. Admission is competitive — students apply internally after the "
            "first year and the program now spans three years."
        ),
        "themes": [
            {
                "label": "Top undergraduate business reputation",
                "sentiment": "positive",
                "detail": (
                    "McIntire is consistently ranked among the best undergraduate business "
                    "programs nationally."
                ),
            },
            {
                "label": "Strong finance & consulting recruiting",
                "sentiment": "positive",
                "detail": (
                    "Employers recruit heavily for finance, consulting, and analytics "
                    "roles, supported by an active alumni network."
                ),
            },
            {
                "label": "Competitive internal admission",
                "sentiment": "caution",
                "detail": (
                    "Students apply to McIntire after their first year, and admission is "
                    "selective — not guaranteed for incoming UVA students."
                ),
            },
            {
                "label": "Limited independent placement data",
                "sentiment": "mixed",
                "detail": (
                    "Detailed undergraduate placement and salary figures are reported by "
                    "McIntire rather than audited by third parties."
                ),
            },
        ],
        "sources": [
            {
                "label": "McIntire — Career Outcomes (Destinations)",
                "url": "https://www.commerce.virginia.edu/career-support",
            },
            {
                "label": "McIntire School of Commerce — B.S. in Commerce",
                "url": "https://www.commerce.virginia.edu/bs-commerce",
            },
        ],
        "disclaimer": (
            "Themes are aggregated and paraphrased from public third-party coverage and "
            "official McIntire outcomes reports, not individual verbatim reviews."
        ),
    },
    "uva-master-of-public-policy-mpp": {
        "summary": (
            "Batten's M.P.P. is valued for its small-cohort model and individualized "
            "career support, placing graduates across federal, state, and local "
            "government, consulting, research, and the nonprofit sector. About 94% of "
            "recent graduates reported positive employment or continuing-education "
            "outcomes."
        ),
        "themes": [
            {
                "label": "Small-cohort, personalized support",
                "sentiment": "positive",
                "detail": (
                    "The program's small size enables close faculty contact and one-on-one "
                    "career coaching."
                ),
            },
            {
                "label": "Strong placement",
                "sentiment": "positive",
                "detail": (
                    "About 94% of recent graduates reported positive employment or "
                    "continuing-education outcomes across the public, private, and "
                    "nonprofit sectors."
                ),
            },
            {
                "label": "Public-service focus",
                "sentiment": "positive",
                "detail": (
                    "The mission-driven cohort and curriculum emphasize leadership and "
                    "impact in the public interest."
                ),
            },
            {
                "label": "Limited public salary data",
                "sentiment": "mixed",
                "detail": (
                    "Outcomes are reported by the school; independent salary benchmarking "
                    "is limited compared with business or law programs."
                ),
            },
        ],
        "sources": [
            {
                "label": "Batten — Employment Outcomes",
                "url": "https://batten.virginia.edu/careers/career-services/employment-outcomes",
            },
            {
                "label": "U.S. News — Best Public Affairs Schools (UVA)",
                "url": "https://www.usnews.com/best-graduate-schools/top-public-affairs-schools/university-of-virginia-main-campus-234076",
            },
        ],
        "disclaimer": (
            "Themes are aggregated and paraphrased from public third-party coverage and "
            "official Batten outcomes reports, not individual verbatim reviews."
        ),
    },
    "uva-ms-data-science": {
        "summary": (
            "UVA's M.S. in Data Science reports strong employment outcomes across its "
            "residential and online formats, with the online program (which draws "
            "career-changers and working professionals) reporting the higher recent "
            "median salary. National rankings have recognized the program's career "
            "support and affordability."
        ),
        "themes": [
            {
                "label": "Strong employment outcomes",
                "sentiment": "positive",
                "detail": (
                    "Recent classes report high full-time employment rates and six-figure "
                    "median salaries, especially for the online format."
                ),
            },
            {
                "label": "Flexible formats",
                "sentiment": "positive",
                "detail": (
                    "A full-time residential program and a 100% online, part-time program "
                    "serve different student populations."
                ),
            },
            {
                "label": "Recognized career support",
                "sentiment": "positive",
                "detail": (
                    "National rankings have highlighted the program's career support and "
                    "value among online data-science degrees."
                ),
            },
            {
                "label": "Residential vs. online salary gap",
                "sentiment": "mixed",
                "detail": (
                    "Online graduates (often experienced professionals) have reported "
                    "higher median salaries than residential graduates, reflecting "
                    "different student profiles."
                ),
            },
        ],
        "sources": [
            {
                "label": "UVA School of Data Science — Employment Statistics",
                "url": "https://datascience.virginia.edu/pages/2025-msds-employment-statistics",
            },
            {
                "label": "UVA School of Data Science — Career Outcomes",
                "url": "https://datascience.virginia.edu/career-services/employment",
            },
        ],
        "disclaimer": (
            "Themes are aggregated and paraphrased from public third-party coverage and "
            "official School of Data Science employment reports, not individual verbatim "
            "reviews."
        ),
    },
}


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def _program_standard(spec: dict) -> dict:
    omitted: list[str] = ["outcomes_data.employment_rate", "outcomes_data.top_industries"]
    if spec["degree_type"] != "bachelors" and spec.get("tuition") is None:
        omitted.append("cost_data.tuition_usd")
    if not spec.get("tracks") and spec["slug"] not in _TRACKS_BY_SLUG:
        omitted.append("tracks")
    omitted.append("class_profile.cohort_size")
    omitted.append("faculty_contacts.lead")
    if spec["slug"] not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    return _standard(omitted)


def _lead_campus_photo(school_outcomes: dict) -> str | None:
    photos = (school_outcomes or {}).get("campus_photos") or []
    if photos and isinstance(photos[0], dict):
        return photos[0].get("url")
    return None


def apply(session: Session) -> bool:
    """Enrich UVA to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when UVA is absent — safe on fresh/CI databases.
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
    inst.founded_year = 1819
    inst.campus_setting = "suburban"
    if not inst.website_url:
        inst.website_url = "https://www.virginia.edu"
    lead_photo = _lead_campus_photo(school_outcomes)
    if lead_photo:
        gallery = [u for u in (inst.media_gallery or []) if u != lead_photo]
        inst.media_gallery = [lead_photo, *gallery]
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


def _undergrad_cost() -> dict:
    # PUBLIC scalar = NON-RESIDENT (out-of-state); breakdown keeps BOTH rates (run-83 rule).
    return {
        "tuition_usd": _UG_OOS,
        "avg_net_price": _UG_NET,
        "breakdown": {
            "tuition": _UG_OOS,
            "tuition_in_state": _UG_INSTATE,
            "tuition_out_of_state": _UG_OOS,
        },
        "funded": False,
        "note": (
            "UVA is a public university with two published undergraduate stickers: "
            "$21,803 for Virginia residents and $59,512 for non-residents (2025-26, "
            "tuition + fees). The scalar shown is the non-resident rate — the "
            "broadly-correct budget input for a national and international applicant "
            "pool; the resident rate is preserved in the breakdown. The College "
            "Scorecard average net price after aid is about $21,600."
        ),
        "source": _UG_SRC[0],
        "source_url": _UG_SRC[1],
        "year": "2025-26",
    }


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
        if spec["degree_type"] == "bachelors":
            p.tuition = _UG_OOS
            p.cost_data = _undergrad_cost()
        elif spec.get("tuition") is not None:
            p.tuition = spec["tuition"]
            p.cost_data = {
                "tuition_usd": spec["tuition"],
                "funded": False,
                "note": spec.get("cost_note", ""),
                "source": (spec.get("cost_source") or _BOV_SRC)[0],
                "source_url": (spec.get("cost_source") or _BOV_SRC)[1],
                "year": "2025-26",
            }
        elif spec.get("funded"):
            p.tuition = None
            p.cost_data = {
                "funded": True,
                "note": (
                    "Funded doctoral students at UVA receive a tuition waiver plus a "
                    "stipend, so the sticker is not the price admitted students pay."
                ),
                "source": "UVA Graduate School of Arts & Sciences / school funding pages",
                "source_url": _SCHOOL_WEBSITE.get(spec["school"], "https://www.virginia.edu"),
            }
        else:
            p.tuition = None
            p.cost_data = {
                "funded": False,
                "note": spec.get("omit_tuition_reason", (
                    "A verified per-program annual tuition figure is omitted here rather "
                    "than estimated; see the program's official cost page."
                )),
                "source": _BOV_SRC[0],
                "source_url": _BOV_SRC[1],
            }
        p.cip_code = spec["cip"]
        p.application_requirements = _requirements_for(spec)
        outcomes = dict(_OUTCOMES_INSTITUTION)
        spec_with_tracks = dict(spec)
        spec_with_tracks["tracks"] = _TRACKS_BY_SLUG.get(slug)
        outcomes["_standard"] = _program_standard(spec_with_tracks)
        p.outcomes_data = outcomes
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = None
        p.faculty_contacts = None
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        p.who_its_for = spec["who_its_for"]
        p.highlights = None
        p.application_deadline = date(2027, 1, 1) if spec["degree_type"] == "bachelors" else None
    session.flush()
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
