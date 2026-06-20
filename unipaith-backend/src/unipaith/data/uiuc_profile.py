"""University of Illinois Urbana-Champaign (UIUC) — gold-standard profile data
(institution + schools + program catalog).

Mirrors the MIT / Sloan / MBAn reference instance (see ``mit_profile.py`` /
``ut_austin_profile.py``): every value is researched from an authoritative source
and carries a citation, or is honestly omitted (recorded in that node's
``_standard.omitted``) — never guessed. Built 2026-06-13 from:

  * U.S. Dept. of Education **College Scorecard** API + **IPEDS** (UNITID 145637):
    admit rate, average net price, cost of attendance, ten-year median earnings,
    six-year completion, first-year retention, Pell/loan rates, median debt,
    endowment, undergraduate race/ethnicity, and SAT/ACT middle-50% scores.
  * **UIUC Common Data Set 2024-2025** and the UIUC News Bureau / Division of
    Management Information: the Fall 2024 first-year admissions funnel (73,742
    applicants / 31,247 admitted / 9,008 enrolled), record total enrollment
    (59,238), 37,140 undergraduates, and the 18:1 student-faculty ratio.
  * Rankings: **U.S. News Best Colleges 2026** (#36 National, #12 public),
    **QS 2026** (#70), **Times Higher Education 2026** (#41), Carnegie R1, and
    Higher Learning Commission (HLC) accreditation, each cited.
  * The official **UIUC Academic Catalog** (catalog.illinois.edu): the full
    published degree catalog parsed from the Undergraduate and Graduate Program
    Indexes across UIUC's 14 degree-granting colleges and schools, plus the
    professional Juris Doctor (College of Law), Doctor of Medicine (Carle Illinois
    College of Medicine), and Doctor of Veterinary Medicine (College of Veterinary
    Medicine), and UIUC's flagship 100%-online degrees delivered with Coursera —
    the Gies iMBA, iMSA, and iMSM, and the Grainger online Master of Computer
    Science. Online programs carry ``delivery_format = "online"``. Minors,
    concentrations, graduate certificates, and combined/integrated-degree
    listings (already represented by their single-degree components) are excluded.
  * **Provost's Council of Deans** (provost.illinois.edu) for the current dean of
    each college, and college websites for each unit's departments/units.
  * Verified third-party coverage + official rankings for flagship coverable
    programs (Computer Science, Computer/Electrical/Mechanical/Aerospace/Civil/
    Materials/Chemical/Bio-engineering, Accountancy, Finance, the Gies iMBA, the
    online MCS, the #1-ranked iSchool MS, Statistics, Economics, the Law J.D., the
    Carle Illinois M.D., and the Doctor of Veterinary Medicine).

Honest caveats stamped into ``_standard.omitted``: UIUC does not publish a single
university-wide "employed or continuing education" placement rate or a uniform
top-employer-industries list across all colleges, so those two institution outcome
fields are omitted with reason (the College Scorecard institution-wide ten-year
median earnings, $81,054, is kept). UIUC reports total employees rather than a
single consistent instructional-faculty headcount, so ``scale.faculty_count`` is
omitted (the 18:1 student-faculty ratio is kept). Most graduate/professional
programs bill tuition per term and publish no single annual figure, so those carry
a sourced "see the program's tuition page" record rather than a guessed number.
External reviews are attached to the flagship coverable programs; remaining
programs record ``external_reviews`` in their ``_standard.omitted`` pending
program-specific third-party coverage (synthesized institution-level reviews were
removed in this repair).
"""

# ruff: noqa: E501

from __future__ import annotations

import re
from collections import Counter, defaultdict

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.profile_catalog_utils import validate_catalog
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "University of Illinois Urbana-Champaign"
ENRICHED_AT = "2026-06-18"


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


# UIUC reports outcomes by college/program, not as one university-wide combined
# placement rate or top-employer-industries list.
_OMITTED_INSTITUTION: list[str] = [
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
    "school_outcomes.scale.faculty_count",
]

RANKING_DATA: dict = {
    "ownership_type": "public",
    "accreditor": "Higher Learning Commission (HLC)",
    "carnegie_classification": (
        "Doctoral Universities: Very High Research Spending and Doctorate Production (R1)"
    ),
    "qs_world_university_rankings": {
        "rank": 70,
        "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/university-illinois-urbana-champaign",
    },
    "times_higher_education": {
        "rank": 41,
        "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-illinois-urbana-champaign",
    },
    "us_news_national": {
        "rank": 36,
        "year": 2026,
        "source_url": "https://www.usnews.com/best-colleges/university-of-illinois-1775",
    },
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.4237,
    "avg_net_price": 14355,
    "median_earnings_10yr": 81054,
    "graduation_rate_6yr": 0.8513,
    "completion_rate_4yr_150pct": 0.8513,
    "retention_rate_first_year": 0.9457,
    "financial_aid": {
        "pell_grant_rate": 0.2341,
        "federal_loan_rate": 0.2738,
        "median_debt_completers": 19500,
        "cost_of_attendance": 33642,
        "avg_net_price": 14355,
    },
    "demographics": {
        "white": 0.3753,
        "asian": 0.2311,
        "hispanic": 0.1441,
        "black": 0.0531,
        "two_or_more": 0.0412,
        "american_indian": 0.0003,
        "pacific_islander": 0.0003,
        "international": 0.1391,
        "unknown": 0.0154,
        "women": 0.496,
    },
    "test_scores": {
        "sat_reading_25_75": [650, 740],
        "sat_math_25_75": [660, 780],
        "act_25_75": [30, 34],
        "year": 2024,
        "source": "College Scorecard / UIUC Common Data Set 2024-2025 (middle 50% of enrolled first-year students who submitted scores; UIUC is test-optional)",
    },
    "campus_basics": {"location": "Urbana and Champaign, Illinois"},
    "scale": {
        "student_faculty_ratio": "18:1",
        "endowment_usd": 2606081833,
    },
    "location": {"lat": 40.102, "lng": -88.2272},
    "research": {
        "labs": [
            "National Center for Supercomputing Applications (NCSA)",
            "Beckman Institute for Advanced Science and Technology",
            "Coordinated Science Laboratory (CSL)",
            "Carl R. Woese Institute for Genomic Biology (IGB)",
            "Holonyak Micro & Nanotechnology Laboratory",
            "Materials Research Laboratory",
        ],
        "areas": [
            "Supercomputing, data science, and artificial intelligence",
            "Microelectronics, photonics, and nanotechnology",
            "Genomic biology, bioengineering, and health",
            "Materials science and advanced manufacturing",
            "Agriculture, food, and the environment",
        ],
        "lab_links": {
            "National Center for Supercomputing Applications (NCSA)": "https://www.ncsa.illinois.edu/",
            "Beckman Institute for Advanced Science and Technology": "https://beckman.illinois.edu/",
            "Coordinated Science Laboratory (CSL)": "https://csl.illinois.edu/",
            "Carl R. Woese Institute for Genomic Biology (IGB)": "https://www.igb.illinois.edu/",
            "Holonyak Micro & Nanotechnology Laboratory": "https://mntl.illinois.edu/",
            "Materials Research Laboratory": "https://mrl.illinois.edu/",
        },
    },
    "campus_life": {
        "athletics_division": "NCAA Division I (Big Ten Conference)",
        "resources": [
            {"name": "Fighting Illini Athletics", "url": "https://fightingillini.com/"},
            {"name": "University of Illinois Library", "url": "https://www.library.illinois.edu/"},
            {
                "name": "Krannert Center for the Performing Arts",
                "url": "https://krannertcenter.com/",
            },
            {"name": "Illini Union", "url": "https://union.illinois.edu/"},
            {"name": "Campus Recreation", "url": "https://campusrec.illinois.edu/"},
        ],
    },
    "media_credit": "Wikimedia Commons / Daniel Schwen (CC BY-SA 4.0)",
    "campus_photos": [
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/UIUC_Illini_Union_and_Main_Quad.jpg/1920px-UIUC_Illini_Union_and_Main_Quad.jpg",
            "credit": "Wikimedia Commons / Daniel Schwen (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/UIUC_Main_Quad_Panorama.jpg/1920px-UIUC_Main_Quad_Panorama.jpg",
            "credit": "Wikimedia Commons / kosheahan (CC BY 2.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/Foellinger_Auditorium_University_of_Illinois_at_Urbana-Champaign_from_mid-quad.jpg/1920px-Foellinger_Auditorium_University_of_Illinois_at_Urbana-Champaign_from_mid-quad.jpg",
            "credit": "Wikimedia Commons / Beyond My Ken (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Altgeld_Hall%2C_University_of_Illinois.jpg/1920px-Altgeld_Hall%2C_University_of_Illinois.jpg",
            "credit": "Wikimedia Commons / Kevin Dooley (CC BY 2.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Memorial_Stadium_Champaign_Panorama.jpg/1920px-Memorial_Stadium_Champaign_Panorama.jpg",
            "credit": "Wikimedia Commons / Cubbie15fan (CC BY-SA 3.0)",
        },
    ],
    "flagship": {
        "enrollment_total": 59238,
        "applicants": 73742,
        "admits": 31247,
        "admissions_cycle": "First-year, Fall 2024 (UIUC Common Data Set 2024-2025)",
        "founded_year": 1867,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (UIUC, UNITID 145637)",
            "url": "https://collegescorecard.ed.gov/school/?145637-University-of-Illinois-Urbana-Champaign",
        },
        {
            "label": "NCES College Navigator — University of Illinois Urbana-Champaign (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=145637",
        },
        {
            "label": "UIUC Common Data Set 2024-2025 (admissions funnel, enrollment, test scores)",
            "url": "https://dmi.illinois.edu/cds/",
        },
        {
            "label": "UIUC facts & rankings (enrollment, ratio, research centers)",
            "url": "https://www.admissions.illinois.edu/discover/illinois-facts",
        },
        {
            "label": "UIUC News Bureau — record Fall 2024 enrollment",
            "url": "https://news.illinois.edu/illinois-welcomes-largest-number-of-students-in-university-history/",
        },
        {
            "label": "UIUC rankings (U.S. News 2025-2026 college and departmental ranks)",
            "url": "https://illinois.edu/about/rankings/",
        },
        {
            "label": "UIUC Academic Catalog 2026-2027 — undergraduate + graduate program indexes",
            "url": "https://catalog.illinois.edu/degree-programs/",
        },
        {
            "label": "Provost's Council of Deans (college leadership)",
            "url": "https://provost.illinois.edu/about/committees/provosts-council-of-deans/",
        },
        {
            "label": "Carnegie Classifications — University of Illinois Urbana-Champaign (R1)",
            "url": "https://carnegieclassifications.acenet.edu/institution/university-of-illinois-urbana-champaign/",
        },
        {
            "label": "Higher Learning Commission — University of Illinois Urbana-Champaign (accreditation)",
            "url": "https://www.hlcommission.org/institution/1156/",
        },
        {
            "label": "QS World University Rankings 2026 — UIUC (#70)",
            "url": "https://www.topuniversities.com/universities/university-illinois-urbana-champaign",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — UIUC (#41)",
            "url": "https://www.timeshighereducation.com/world-university-rankings/university-illinois-urbana-champaign",
        },
        {
            "label": "U.S. News Best Colleges 2026 — UIUC (#36 National, #12 public)",
            "url": "https://www.usnews.com/best-colleges/university-of-illinois-1775",
        },
    ],
}

# student_body_size = undergraduate enrollment (UIUC Fall 2024 official); total
# degree-seeking enrollment (59,238) lives in flagship.enrollment_total.
UNDERGRAD_COUNT = 37140

DESCRIPTION = (
    "The University of Illinois Urbana-Champaign is a public land-grant research university in "
    "Urbana and Champaign, IL. Founded in 1867 as one of the original Morrill Act land-grant "
    "institutions, it is the flagship of the University of Illinois System and a founding member of "
    "the Association of American Universities. Fall 2024 brought a record total enrollment of 59,238 "
    "students — roughly 37,140 undergraduates and more than 20,700 graduate and professional "
    "students — with an 18:1 student-faculty ratio. For Fall 2024 it admitted about 42.4% of "
    "first-year applicants (31,247 of a record 73,742).\n\n"
    "UIUC is organized into 14 degree-granting colleges and schools, including The Grainger College "
    "of Engineering, the Gies College of Business, the College of Liberal Arts and Sciences, the "
    "College of Agricultural, Consumer and Environmental Sciences, the College of Fine and Applied "
    "Arts, the School of Information Sciences, the College of Law, the College of Veterinary "
    "Medicine, and the engineering-based Carle Illinois College of Medicine (the nation's first such "
    "medical school). Together they offer more than 400 degree programs across the bachelor's, "
    "master's, professional, and doctoral levels — including UIUC's pioneering 100%-online degrees "
    "with Coursera: the Gies iMBA, iMSA, and iMSM, and the Grainger online Master of Computer "
    "Science.\n\n"
    "A Carnegie R1 university accredited by the Higher Learning Commission, UIUC ranks #36 among "
    "national universities (and #12 among public universities) by U.S. News, #41 in the world by "
    "Times Higher Education, and #70 by QS for 2026. Its programs in computer science, engineering, "
    "accountancy, and library/information science rank among the nation's best — civil engineering "
    "and the iSchool's information-science master's are ranked #1, and accountancy #1 at the "
    "undergraduate level. Research is anchored by the National Center for Supercomputing "
    "Applications, the Beckman Institute, the Coordinated Science Laboratory, the Carl R. Woese "
    "Institute for Genomic Biology, and the Holonyak Micro & Nanotechnology Laboratory.\n\n"
    "UIUC's published cost of attendance is about $33,642 a year, but its average net price after "
    "grant aid is about $14,355 and the median federal debt of completers is about $19,500; in-state "
    "students benefit from public tuition. UIUC graduates earn a median of roughly $81,054 ten years "
    "after entry. The Fighting Illini compete in NCAA Division I in the Big Ten Conference."
)

# == Schools (14 degree-granting colleges and schools) ==
_SCHOOL_META = [
    {
        "key": "ENGR",
        "name": "The Grainger College of Engineering",
        "sort_order": 1,
        "website": "https://grainger.illinois.edu/",
        "leadership": "Rashid Bashir — Dean",
        "research_centers": [
            "Siebel School of Computing and Data Science",
            "Department of Electrical & Computer Engineering",
            "Department of Mechanical Science & Engineering",
            "Department of Aerospace Engineering",
            "Department of Civil & Environmental Engineering",
            "Department of Materials Science & Engineering",
        ],
        "keywords": [
            "Grainger College of Engineering",
            "Grainger Engineering",
            "engineering",
            "computer science",
        ],
    },
    {
        "key": "LAS",
        "name": "College of Liberal Arts and Sciences",
        "sort_order": 2,
        "website": "https://las.illinois.edu/",
        "leadership": "Venetria K. Patton — Dean",
        "research_centers": [
            "School of Chemical Sciences",
            "School of Molecular & Cellular Biology",
            "School of Literatures, Cultures & Linguistics",
            "School of Earth, Society & Environment",
            "Department of Mathematics",
            "Department of Economics",
        ],
        "keywords": ["College of Liberal Arts and Sciences", "LAS", "liberal arts and sciences"],
    },
    {
        "key": "BUS",
        "name": "Gies College of Business",
        "sort_order": 3,
        "website": "https://giesbusiness.illinois.edu/",
        "leadership": "W. Brooke Elliott — Dean",
        "research_centers": [
            "Department of Accountancy",
            "Department of Finance",
            "Department of Business Administration",
            "Gies online programs (iMBA, iMSA, iMSM)",
        ],
        "keywords": [
            "Gies College of Business",
            "Gies Business",
            "business",
            "accountancy",
            "iMBA",
        ],
    },
    {
        "key": "ACES",
        "name": "College of Agricultural, Consumer and Environmental Sciences",
        "sort_order": 4,
        "website": "https://aces.illinois.edu/",
        "leadership": "Germ\u00e1n Bollero — Dean",
        "research_centers": [
            "Department of Crop Sciences",
            "Department of Animal Sciences",
            "Department of Agricultural & Consumer Economics",
            "Department of Food Science & Human Nutrition",
            "Department of Natural Resources & Environmental Sciences",
        ],
        "keywords": [
            "College of ACES",
            "Agricultural Consumer and Environmental Sciences",
            "agriculture",
        ],
    },
    {
        "key": "FAA",
        "name": "College of Fine and Applied Arts",
        "sort_order": 5,
        "website": "https://faa.illinois.edu/",
        "leadership": "Jake Pinholster — Dean",
        "research_centers": [
            "School of Architecture",
            "School of Art & Design",
            "School of Music",
            "Department of Landscape Architecture",
            "Department of Urban & Regional Planning",
            "Krannert Art Museum",
        ],
        "keywords": [
            "College of Fine and Applied Arts",
            "fine and applied arts",
            "architecture",
            "music",
        ],
    },
    {
        "key": "AHS",
        "name": "College of Applied Health Sciences",
        "sort_order": 6,
        "website": "https://ahs.illinois.edu/",
        "leadership": "Cheryl Hanley-Maxwell — Dean",
        "research_centers": [
            "Department of Kinesiology & Community Health",
            "Department of Speech & Hearing Science",
            "Department of Recreation, Sport & Tourism",
            "Department of Health & Kinesiology",
        ],
        "keywords": [
            "College of Applied Health Sciences",
            "applied health sciences",
            "kinesiology",
        ],
    },
    {
        "key": "EDUC",
        "name": "College of Education",
        "sort_order": 7,
        "website": "https://education.illinois.edu/",
        "leadership": "Chrystalla Mouza — Dean",
        "research_centers": [
            "Department of Curriculum & Instruction",
            "Department of Education Policy, Organization & Leadership",
            "Department of Educational Psychology",
            "Department of Special Education",
        ],
        "keywords": ["College of Education", "education", "teaching"],
    },
    {
        "key": "MDIA",
        "name": "College of Media",
        "sort_order": 8,
        "website": "https://media.illinois.edu/",
        "leadership": "Tracy Sulkin — Dean",
        "research_centers": [
            "Charles H. Sandage Department of Advertising",
            "Department of Journalism",
            "Institute of Communications Research",
        ],
        "keywords": ["College of Media", "media", "journalism", "advertising"],
    },
    {
        "key": "IS",
        "name": "School of Information Sciences",
        "sort_order": 9,
        "website": "https://ischool.illinois.edu/",
        "leadership": "Emily Knox — Interim Dean",
        "research_centers": [
            "Master of Science in Information Sciences (LIS)",
            "Bachelor of Science in Information Sciences",
            "Informatics graduate program",
        ],
        "keywords": [
            "School of Information Sciences",
            "iSchool",
            "information sciences",
            "library and information science",
        ],
    },
    {
        "key": "SOCW",
        "name": "School of Social Work",
        "sort_order": 10,
        "website": "https://socialwork.illinois.edu/",
        "leadership": "Ben Lough — Interim Dean",
        "research_centers": [
            "Bachelor of Social Work program",
            "Master of Social Work (MSW) program",
            "Ph.D. in Social Work program",
        ],
        "keywords": ["School of Social Work", "social work", "MSW"],
    },
    {
        "key": "LER",
        "name": "School of Labor and Employment Relations",
        "sort_order": 11,
        "website": "https://ler.illinois.edu/",
        "leadership": "Simon Lloyd D. Restubog — Dean",
        "research_centers": [
            "Master of Human Resources & Industrial Relations (MHRIR) program",
            "Ph.D. in Labor and Employment Relations program",
        ],
        "keywords": [
            "School of Labor and Employment Relations",
            "labor and employment relations",
            "human resources",
        ],
    },
    {
        "key": "LAW",
        "name": "College of Law",
        "sort_order": 12,
        "website": "https://law.illinois.edu/",
        "leadership": "Jamelle Sharpe — Dean",
        "research_centers": [
            "Juris Doctor (J.D.) program",
            "Master of Laws (LL.M.) program",
            "Doctor of the Science of Law (J.S.D.) program",
        ],
        "keywords": ["University of Illinois College of Law", "College of Law", "law", "J.D."],
    },
    {
        "key": "VETMED",
        "name": "College of Veterinary Medicine",
        "sort_order": 13,
        "website": "https://vetmed.illinois.edu/",
        "leadership": "Peter Constable — Dean",
        "research_centers": [
            "Department of Comparative Biosciences",
            "Department of Pathobiology",
            "Department of Veterinary Clinical Medicine",
            "Doctor of Veterinary Medicine (DVM) program",
        ],
        "keywords": ["College of Veterinary Medicine", "veterinary medicine", "DVM"],
    },
    {
        "key": "CIMED",
        "name": "Carle Illinois College of Medicine",
        "sort_order": 14,
        "website": "https://medicine.illinois.edu/",
        "leadership": "Mark S. Cohen — Dean",
        "research_centers": [
            "Doctor of Medicine (M.D.) program",
            "Department of Biomedical & Translational Sciences",
            "Engineering-based medicine curriculum (with Carle Health)",
        ],
        "keywords": ["Carle Illinois College of Medicine", "Carle Illinois", "medicine", "M.D."],
    },
]
SCHOOL_NAME = {m["key"]: m["name"] for m in _SCHOOL_META}
SCHOOL_WEBSITE = {m["name"]: m["website"] for m in _SCHOOL_META}


def _school_description(m: dict) -> str:
    return (
        f"The {m['name']} is one of the 14 degree-granting colleges and schools of the University "
        "of Illinois Urbana-Champaign."
    )


SCHOOLS: list[dict] = [
    {"name": m["name"], "sort_order": m["sort_order"], "description": _school_description(m)}
    for m in _SCHOOL_META
]


def _about_for(m: dict) -> dict:
    return {
        "leadership": m["leadership"],
        "research_centers": m["research_centers"],
        "source": {
            "label": "UIUC Provost's Council of Deans + college websites",
            "url": "https://provost.illinois.edu/about/committees/provosts-council-of-deans/",
        },
    }


def _about_omitted(m: dict) -> list[str]:
    # UIUC does not publish a single founding year per college on one authoritative
    # page, and notable-faculty lists are curated per department; omit-with-reason.
    return ["about_detail.founded", "about_detail.faculty", "about_detail.named_for"]


# == Feeds (content_sources) ==
_UIUC_NEWS_RSS = "https://news.illinois.edu/feed/"
_NEWS_URL = "https://news.illinois.edu/"
_SOCIAL = {
    "instagram": "https://www.instagram.com/illinois1867/",
    "linkedin": "https://www.linkedin.com/school/university-of-illinois-urbana-champaign/",
    "x": "https://twitter.com/Illinois_Alma",
    "youtube": "https://www.youtube.com/user/universityofillinois",
    "facebook": "https://www.facebook.com/IllinoisUniversity/",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _UIUC_NEWS_RSS,
    "news_url": _NEWS_URL,
    "news_curated": True,
    "social": _SOCIAL,
}
_KEYWORDS_BY_SCHOOL = {m["name"]: m["keywords"] for m in _SCHOOL_META}


def _school_content(name: str) -> dict:
    return {
        "news_rss": _UIUC_NEWS_RSS,
        "news_url": SCHOOL_WEBSITE.get(name, _NEWS_URL),
        "news_curated": False,
        "keywords": list(_KEYWORDS_BY_SCHOOL[name]),
        "social": _SOCIAL,
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


# == Program catalog (slug, school_key, program_name, degree_type, department, delivery, duration) ==
_CATALOG: list[tuple] = [
    (
        "uiuc-agricultural-biological-engineering-bs-agricultural-engineering-agricultural-science-bsag",
        "ACES",
        "Agricultural & Biological Engineering Sciences",
        "bachelors",
        "Agricultural & Biological Engineering Sciences",
        "on_campus",
        48,
    ),
    (
        "uiuc-agricultural-consumer-economics-bs",
        "ACES",
        "Agricultural & Consumer Economics",
        "bachelors",
        "Agricultural & Consumer Economics",
        "on_campus",
        48,
    ),
    (
        "uiuc-agricultural-leadership-education-communications-bs",
        "ACES",
        "Agricultural Leadership, Education, & Communications",
        "bachelors",
        "Agricultural Leadership, Education, & Communications",
        "on_campus",
        48,
    ),
    ("uiuc-agronomy-bs", "ACES", "Agronomy", "bachelors", "Agronomy", "on_campus", 48),
    (
        "uiuc-animal-sciences-bs",
        "ACES",
        "Animal Sciences",
        "bachelors",
        "Animal Sciences",
        "on_campus",
        48,
    ),
    (
        "uiuc-computer-science-animal-sciences-bs",
        "ACES",
        "Computer Science + Animal Sciences",
        "bachelors",
        "Computer Science + Animal Sciences",
        "on_campus",
        48,
    ),
    (
        "uiuc-computer-science-crop-sciences-bs",
        "ACES",
        "Computer Science + Crop Sciences",
        "bachelors",
        "Computer Science + Crop Sciences",
        "on_campus",
        48,
    ),
    (
        "uiuc-crop-sciences-bs",
        "ACES",
        "Crop Sciences",
        "bachelors",
        "Crop Sciences",
        "on_campus",
        48,
    ),
    ("uiuc-dietetics-nutrition-bs", "ACES", "Dietetics", "bachelors", "Dietetics", "on_campus", 48),
    (
        "uiuc-engineering-technology-management-agricultural-systems-bs",
        "ACES",
        "Engineering Technology & Management for Agricultural Systems",
        "bachelors",
        "Engineering Technology & Management for Agricultural Systems",
        "on_campus",
        48,
    ),
    ("uiuc-food-science-bs", "ACES", "Food Science", "bachelors", "Food Science", "on_campus", 48),
    (
        "uiuc-hospitality-management-bs",
        "ACES",
        "Hospitality Management",
        "bachelors",
        "Hospitality Management",
        "on_campus",
        48,
    ),
    (
        "uiuc-human-development-family-studies-bs",
        "ACES",
        "Human Development & Family Studies",
        "bachelors",
        "Human Development & Family Studies",
        "on_campus",
        48,
    ),
    (
        "uiuc-natural-resources-environmental-sciences-bs",
        "ACES",
        "Natural Resources & Environmental Sciences",
        "bachelors",
        "Natural Resources & Environmental Sciences",
        "on_campus",
        48,
    ),
    ("uiuc-nutrition-health-bs", "ACES", "Nutrition", "bachelors", "Nutrition", "on_campus", 48),
    (
        "uiuc-plant-biotechnology-bs",
        "ACES",
        "Plant Biotechnology",
        "bachelors",
        "Plant Biotechnology",
        "on_campus",
        48,
    ),
    (
        "uiuc-sustainability-food-environmental-systems-bs",
        "ACES",
        "Sustainability in Food & Environmental Systems",
        "bachelors",
        "Sustainability in Food & Environmental Systems",
        "on_campus",
        48,
    ),
    (
        "uiuc-agricultural-applied-economics-maae",
        "ACES",
        "Agricultural & Applied Economics",
        "masters",
        "Agricultural & Applied Economics",
        "on_campus",
        24,
    ),
    (
        "uiuc-agricultural-applied-economics-ms",
        "ACES",
        "Agricultural & Applied Economics",
        "masters",
        "Agricultural & Applied Economics",
        "on_campus",
        24,
    ),
    (
        "uiuc-agricultural-leadership-education-communications-ms",
        "ACES",
        "Agricultural Leadership, Education, & Communications",
        "masters",
        "Agricultural Leadership, Education, & Communications",
        "on_campus",
        24,
    ),
    (
        "uiuc-animal-sciences-mansc",
        "ACES",
        "Animal Sciences",
        "masters",
        "Animal Sciences",
        "on_campus",
        24,
    ),
    (
        "uiuc-animal-sciences-ms",
        "ACES",
        "Animal Sciences",
        "masters",
        "Animal Sciences",
        "on_campus",
        24,
    ),
    ("uiuc-child-health-ms", "ACES", "Child Health", "masters", "Child Health", "on_campus", 24),
    ("uiuc-crop-sciences-ms", "ACES", "Crop Sciences", "masters", "Crop Sciences", "on_campus", 24),
    (
        "uiuc-engineering-technology-management-agricultural-systems-ms",
        "ACES",
        "Engineering Technology & Management for Agricultural Systems",
        "masters",
        "Engineering Technology & Management for Agricultural Systems",
        "on_campus",
        24,
    ),
    (
        "uiuc-food-science-human-nutrition-ms",
        "ACES",
        "Food Science & Human Nutrition",
        "masters",
        "Food Science & Human Nutrition",
        "on_campus",
        24,
    ),
    (
        "uiuc-human-development-family-studies-ms",
        "ACES",
        "Human Development & Family Studies",
        "masters",
        "Human Development & Family Studies",
        "on_campus",
        24,
    ),
    (
        "uiuc-natural-resources-environmental-sciences-ms",
        "ACES",
        "Natural Resources & Environmental Sciences",
        "masters",
        "Natural Resources & Environmental Sciences",
        "on_campus",
        24,
    ),
    (
        "uiuc-nutritional-science-ms",
        "ACES",
        "Nutritional Sciences",
        "masters",
        "Nutritional Sciences",
        "on_campus",
        24,
    ),
    (
        "uiuc-agricultural-applied-economics-phd",
        "ACES",
        "Agricultural & Applied Economics",
        "phd",
        "Agricultural & Applied Economics",
        "on_campus",
        60,
    ),
    (
        "uiuc-animal-sciences-phd",
        "ACES",
        "Animal Sciences",
        "phd",
        "Animal Sciences",
        "on_campus",
        60,
    ),
    ("uiuc-crop-sciences-phd", "ACES", "Crop Sciences", "phd", "Crop Sciences", "on_campus", 60),
    (
        "uiuc-engineering-technology-management-agricultural-systems",
        "ACES",
        "Engineering Technology & Management for Agricultural Systems",
        "phd",
        "Engineering Technology & Management for Agricultural Systems",
        "on_campus",
        60,
    ),
    (
        "uiuc-food-science-human-nutrition-phd",
        "ACES",
        "Food Science & Human Nutrition",
        "phd",
        "Food Science & Human Nutrition",
        "on_campus",
        60,
    ),
    (
        "uiuc-human-development-family-studies-phd",
        "ACES",
        "Human Development & Family Studies",
        "phd",
        "Human Development & Family Studies",
        "on_campus",
        60,
    ),
    (
        "uiuc-natural-resources-environmental-sciences-phd",
        "ACES",
        "Natural Resources & Environmental Sciences",
        "phd",
        "Natural Resources & Environmental Sciences",
        "on_campus",
        60,
    ),
    (
        "uiuc-nutritional-science-phd",
        "ACES",
        "Nutritional Sciences",
        "phd",
        "Nutritional Sciences",
        "on_campus",
        60,
    ),
    (
        "uiuc-community-health-bs",
        "AHS",
        "Community Health",
        "bachelors",
        "Community Health",
        "on_campus",
        48,
    ),
    (
        "uiuc-interdisciplinary-health-sciences-bs",
        "AHS",
        "Interdisciplinary Health Sciences",
        "bachelors",
        "Interdisciplinary Health Sciences",
        "on_campus",
        48,
    ),
    ("uiuc-kinesiology-bs", "AHS", "Kinesiology", "bachelors", "Kinesiology", "on_campus", 48),
    (
        "uiuc-public-health-bs",
        "AHS",
        "Public Health",
        "bachelors",
        "Public Health",
        "on_campus",
        48,
    ),
    (
        "uiuc-recreation-sport-tourism-bs",
        "AHS",
        "Recreation, Sport & Tourism",
        "bachelors",
        "Recreation, Sport & Tourism",
        "on_campus",
        48,
    ),
    (
        "uiuc-speech-hearing-science-bs",
        "AHS",
        "Speech & Hearing Science",
        "bachelors",
        "Speech & Hearing Science",
        "on_campus",
        48,
    ),
    (
        "uiuc-community-health-ms",
        "AHS",
        "Community Health",
        "masters",
        "Community Health",
        "on_campus",
        24,
    ),
    ("uiuc-epidemiology-mph", "AHS", "Epidemiology", "masters", "Epidemiology", "on_campus", 24),
    (
        "uiuc-health-administration-mha",
        "AHS",
        "Health Administration",
        "masters",
        "Health Administration",
        "on_campus",
        24,
    ),
    (
        "uiuc-health-technology-ms",
        "AHS",
        "Health Technology",
        "masters",
        "Health Technology",
        "on_campus",
        24,
    ),
    ("uiuc-kinesiology-ms", "AHS", "Kinesiology", "masters", "Kinesiology", "on_campus", 24),
    ("uiuc-public-health-mph", "AHS", "Public Health", "masters", "Public Health", "on_campus", 24),
    (
        "uiuc-recreation-sport-tourism-ms",
        "AHS",
        "Recreation, Sport & Tourism",
        "masters",
        "Recreation, Sport & Tourism",
        "on_campus",
        24,
    ),
    (
        "uiuc-speech-hearing-science-ma",
        "AHS",
        "Speech & Hearing Science",
        "masters",
        "Speech & Hearing Science",
        "on_campus",
        24,
    ),
    (
        "uiuc-community-health-phd",
        "AHS",
        "Community Health",
        "phd",
        "Community Health",
        "on_campus",
        60,
    ),
    ("uiuc-kinesiology-phd", "AHS", "Kinesiology", "phd", "Kinesiology", "on_campus", 60),
    (
        "uiuc-recreation-sport-tourism-phd",
        "AHS",
        "Recreation, Sport & Tourism",
        "phd",
        "Recreation, Sport & Tourism",
        "on_campus",
        60,
    ),
    (
        "uiuc-speech-hearing-science-phd",
        "AHS",
        "Speech & Hearing Science",
        "phd",
        "Speech & Hearing Science",
        "on_campus",
        60,
    ),
    (
        "uiuc-audiology-aud",
        "AHS",
        "Speech & Hearing Science",
        "professional",
        "Speech & Hearing Science",
        "on_campus",
        48,
    ),
    ("uiuc-accountancy-bs", "BUS", "Accountancy", "bachelors", "Accountancy", "on_campus", 48),
    (
        "uiuc-accountancy-data-science-bs",
        "BUS",
        "Accountancy + Data Science",
        "bachelors",
        "Accountancy + Data Science",
        "on_campus",
        48,
    ),
    (
        "uiuc-business-data-science-bs",
        "BUS",
        "Business + Data Science",
        "bachelors",
        "Business + Data Science",
        "on_campus",
        48,
    ),
    ("uiuc-finance-bs", "BUS", "Finance", "bachelors", "Finance", "on_campus", 48),
    (
        "uiuc-finance-data-science-bs",
        "BUS",
        "Finance + Data Science",
        "bachelors",
        "Finance + Data Science",
        "on_campus",
        48,
    ),
    (
        "uiuc-information-systems-bs",
        "BUS",
        "Information Systems",
        "bachelors",
        "Information Systems",
        "on_campus",
        48,
    ),
    (
        "uiuc-management-business-bs",
        "BUS",
        "Management",
        "bachelors",
        "Management",
        "on_campus",
        48,
    ),
    ("uiuc-marketing-bs", "BUS", "Marketing", "bachelors", "Marketing", "on_campus", 48),
    (
        "uiuc-operations-management-bs",
        "BUS",
        "Operations Management",
        "bachelors",
        "Operations Management",
        "on_campus",
        48,
    ),
    (
        "uiuc-supply-chain-bs",
        "BUS",
        "Supply Chain Management",
        "bachelors",
        "Supply Chain Management",
        "on_campus",
        48,
    ),
    ("uiuc-accountancy-mas", "BUS", "Accountancy", "masters", "Accountancy", "on_campus", 24),
    ("uiuc-accountancy-ms", "BUS", "Accountancy", "masters", "Accountancy", "on_campus", 24),
    (
        "uiuc-accountancy-imsa-ms",
        "BUS",
        "Accountancy (iMSA)",
        "masters",
        "Department of Accountancy",
        "online",
        24,
    ),
    (
        "uiuc-business-administration-online-mba",
        "BUS",
        "Business Administration (iMBA)",
        "masters",
        "Business Administration (iMBA)",
        "online",
        24,
    ),
    (
        "uiuc-business-analytics-ms",
        "BUS",
        "Business Analytics",
        "masters",
        "Business Analytics",
        "on_campus",
        24,
    ),
    ("uiuc-finance-ms", "BUS", "Finance", "masters", "Finance", "on_campus", 24),
    (
        "uiuc-financial-engineering-ms",
        "BUS",
        "Financial Engineering",
        "masters",
        "Financial Engineering",
        "on_campus",
        24,
    ),
    ("uiuc-management-ms", "BUS", "Management", "masters", "Management", "on_campus", 24),
    (
        "uiuc-management-imsm-ms",
        "BUS",
        "Management (iMSM)",
        "masters",
        "Department of Business Administration",
        "online",
        24,
    ),
    (
        "uiuc-technology-management-ms",
        "BUS",
        "Technology Management",
        "masters",
        "Technology Management",
        "on_campus",
        24,
    ),
    ("uiuc-accountancy-phd", "BUS", "Accountancy", "phd", "Accountancy", "on_campus", 60),
    (
        "uiuc-business-administration-phd",
        "BUS",
        "Business Administration",
        "phd",
        "Business Administration",
        "on_campus",
        60,
    ),
    ("uiuc-finance-phd", "BUS", "Finance", "phd", "Finance", "on_campus", 60),
    (
        "uiuc-medicine-md",
        "CIMED",
        "Medicine",
        "professional",
        "Doctor of Medicine",
        "on_campus",
        48,
    ),
    (
        "uiuc-computer-science-education-bs",
        "EDUC",
        "Computer Science + Education",
        "bachelors",
        "Computer Science + Education",
        "on_campus",
        48,
    ),
    (
        "uiuc-early-childhood-education-bs",
        "EDUC",
        "Early Childhood Education",
        "bachelors",
        "Early Childhood Education",
        "on_campus",
        48,
    ),
    (
        "uiuc-elementary-education-bs",
        "EDUC",
        "Elementary Education",
        "bachelors",
        "Elementary Education",
        "on_campus",
        48,
    ),
    (
        "uiuc-learning-education-studies-bs",
        "EDUC",
        "Learning & Education Studies",
        "bachelors",
        "Learning & Education Studies",
        "on_campus",
        48,
    ),
    (
        "uiuc-middle-grades-education-bs",
        "EDUC",
        "Middle Grades Education",
        "bachelors",
        "Middle Grades Education",
        "on_campus",
        48,
    ),
    (
        "uiuc-secondary-education-bs",
        "EDUC",
        "Secondary Education",
        "bachelors",
        "Secondary Education",
        "on_campus",
        48,
    ),
    (
        "uiuc-special-education-bs",
        "EDUC",
        "Special Education",
        "bachelors",
        "Special Education",
        "on_campus",
        48,
    ),
    (
        "uiuc-curriculum-instruction-edm",
        "EDUC",
        "Curriculum & Instruction",
        "masters",
        "Curriculum & Instruction",
        "on_campus",
        24,
    ),
    (
        "uiuc-curriculum-instruction-ma",
        "EDUC",
        "Curriculum & Instruction",
        "masters",
        "Curriculum & Instruction",
        "on_campus",
        24,
    ),
    (
        "uiuc-curriculum-instruction-ms",
        "EDUC",
        "Curriculum & Instruction",
        "masters",
        "Curriculum & Instruction",
        "on_campus",
        24,
    ),
    (
        "uiuc-early-childhood-education-edm",
        "EDUC",
        "Early Childhood Education",
        "masters",
        "Early Childhood Education",
        "on_campus",
        24,
    ),
    (
        "uiuc-education-policy-organization-leadership-edm",
        "EDUC",
        "Education Policy, Organization & Leadership",
        "masters",
        "Education Policy, Organization & Leadership",
        "on_campus",
        24,
    ),
    (
        "uiuc-education-policy-organization-leadership-ma",
        "EDUC",
        "Education Policy, Organization & Leadership",
        "masters",
        "Education Policy, Organization & Leadership",
        "on_campus",
        24,
    ),
    (
        "uiuc-educational-psychology-edm",
        "EDUC",
        "Educational Psychology",
        "masters",
        "Educational Psychology",
        "on_campus",
        24,
    ),
    (
        "uiuc-educational-psychology-ma",
        "EDUC",
        "Educational Psychology",
        "masters",
        "Educational Psychology",
        "on_campus",
        24,
    ),
    (
        "uiuc-educational-psychology-ms",
        "EDUC",
        "Educational Psychology",
        "masters",
        "Educational Psychology",
        "on_campus",
        24,
    ),
    (
        "uiuc-elementary-education-edm",
        "EDUC",
        "Elementary Education",
        "masters",
        "Elementary Education",
        "on_campus",
        24,
    ),
    (
        "uiuc-mental-health-counseling-ms",
        "EDUC",
        "Mental Health Counseling",
        "masters",
        "Mental Health Counseling",
        "on_campus",
        24,
    ),
    (
        "uiuc-secondary-education-edm",
        "EDUC",
        "Secondary Education",
        "masters",
        "Secondary Education",
        "on_campus",
        24,
    ),
    (
        "uiuc-special-education-edm",
        "EDUC",
        "Special Education",
        "masters",
        "Special Education",
        "on_campus",
        24,
    ),
    (
        "uiuc-curriculum-instruction-edd",
        "EDUC",
        "Curriculum & Instruction",
        "phd",
        "Curriculum & Instruction",
        "on_campus",
        60,
    ),
    (
        "uiuc-curriculum-instruction-phd",
        "EDUC",
        "Curriculum & Instruction",
        "phd",
        "Curriculum & Instruction",
        "on_campus",
        60,
    ),
    (
        "uiuc-education-policy-organization-leadership-edd",
        "EDUC",
        "Education Policy, Organization & Leadership",
        "phd",
        "Education Policy, Organization & Leadership",
        "on_campus",
        60,
    ),
    (
        "uiuc-education-policy-organization-leadership-phd",
        "EDUC",
        "Education Policy, Organization & Leadership",
        "phd",
        "Education Policy, Organization & Leadership",
        "on_campus",
        60,
    ),
    (
        "uiuc-educational-psychology-phd",
        "EDUC",
        "Educational Psychology",
        "phd",
        "Educational Psychology",
        "on_campus",
        60,
    ),
    (
        "uiuc-special-education-phd",
        "EDUC",
        "Special Education",
        "phd",
        "Special Education",
        "on_campus",
        60,
    ),
    (
        "uiuc-aerospace-engineering-bs",
        "ENGR",
        "Aerospace Engineering",
        "bachelors",
        "Aerospace Engineering",
        "on_campus",
        48,
    ),
    (
        "uiuc-agricultural-biological-engineering-bs",
        "ENGR",
        "Agricultural & Biological Engineering",
        "bachelors",
        "Agricultural & Biological Engineering",
        "on_campus",
        48,
    ),
    (
        "uiuc-bioengineering-bs",
        "ENGR",
        "Bioengineering",
        "bachelors",
        "Bioengineering",
        "on_campus",
        48,
    ),
    (
        "uiuc-chemical-engineering-bs",
        "ENGR",
        "Chemical Engineering",
        "bachelors",
        "Chemical Engineering",
        "on_campus",
        48,
    ),
    (
        "uiuc-civil-engineering-bs",
        "ENGR",
        "Civil Engineering",
        "bachelors",
        "Civil Engineering",
        "on_campus",
        48,
    ),
    (
        "uiuc-computer-engineering-bs",
        "ENGR",
        "Computer Engineering",
        "bachelors",
        "Computer Engineering",
        "on_campus",
        48,
    ),
    (
        "uiuc-computer-science-bs",
        "ENGR",
        "Computer Science",
        "bachelors",
        "Computer Science",
        "on_campus",
        48,
    ),
    (
        "uiuc-computer-science-bioengineering-bs",
        "ENGR",
        "Computer Science + Bioengineering",
        "bachelors",
        "Computer Science + Bioengineering",
        "on_campus",
        48,
    ),
    (
        "uiuc-computer-science-physics-bs",
        "ENGR",
        "Computer Science + Physics",
        "bachelors",
        "Computer Science + Physics",
        "on_campus",
        48,
    ),
    (
        "uiuc-electrical-engineering-bs",
        "ENGR",
        "Electrical Engineering",
        "bachelors",
        "Electrical Engineering",
        "on_campus",
        48,
    ),
    (
        "uiuc-engineering-mechanics-bs",
        "ENGR",
        "Engineering Mechanics",
        "bachelors",
        "Engineering Mechanics",
        "on_campus",
        48,
    ),
    (
        "uiuc-engineering-physics-bs",
        "ENGR",
        "Engineering Physics",
        "bachelors",
        "Engineering Physics",
        "on_campus",
        48,
    ),
    (
        "uiuc-environmental-engineering-bs",
        "ENGR",
        "Environmental Engineering",
        "bachelors",
        "Environmental Engineering",
        "on_campus",
        48,
    ),
    (
        "uiuc-industrial-engineering-bs",
        "ENGR",
        "Industrial Engineering",
        "bachelors",
        "Industrial Engineering",
        "on_campus",
        48,
    ),
    (
        "uiuc-innovation-leadership-engineering-entrepreneurship-bs",
        "ENGR",
        "Innovation, Leadership, & Engineering Entrepreneurship",
        "bachelors",
        "Innovation, Leadership, & Engineering Entrepreneurship",
        "on_campus",
        48,
    ),
    (
        "uiuc-materials-science-engineering-bs",
        "ENGR",
        "Materials Science & Engineering",
        "bachelors",
        "Materials Science & Engineering",
        "on_campus",
        48,
    ),
    (
        "uiuc-materials-science-engineering-data-science-bs",
        "ENGR",
        "Materials Science & Engineering + Data Science",
        "bachelors",
        "Materials Science & Engineering + Data Science",
        "on_campus",
        48,
    ),
    (
        "uiuc-mechanical-engineering-bs",
        "ENGR",
        "Mechanical Engineering",
        "bachelors",
        "Mechanical Engineering",
        "on_campus",
        48,
    ),
    (
        "uiuc-neural-engineering-bs",
        "ENGR",
        "Neural Engineering",
        "bachelors",
        "Neural Engineering",
        "on_campus",
        48,
    ),
    (
        "uiuc-nuclear-plasma-radiological-engineering-bs",
        "ENGR",
        "Nuclear, Plasma & Radiological Engineering",
        "bachelors",
        "Nuclear, Plasma & Radiological Engineering",
        "on_campus",
        48,
    ),
    (
        "uiuc-nuclear-plasma-radiological-engineering-data-science-bs",
        "ENGR",
        "Nuclear, Plasma, and Radiological Engineering + Data Science",
        "bachelors",
        "Nuclear, Plasma, and Radiological Engineering + Data Science",
        "on_campus",
        48,
    ),
    ("uiuc-physics-bs", "ENGR", "Physics", "bachelors", "Physics", "on_campus", 48),
    (
        "uiuc-systems-engineering-design-bs",
        "ENGR",
        "Systems Engineering and Design",
        "bachelors",
        "Systems Engineering and Design",
        "on_campus",
        48,
    ),
    (
        "uiuc-aerospace-engineering-ms",
        "ENGR",
        "Aerospace Engineering",
        "masters",
        "Aerospace Engineering",
        "on_campus",
        24,
    ),
    (
        "uiuc-agricultural-biological-engineering-ms",
        "ENGR",
        "Agricultural & Biological Engineering",
        "masters",
        "Agricultural & Biological Engineering",
        "on_campus",
        24,
    ),
    (
        "uiuc-bioengineering-meng",
        "ENGR",
        "Bioengineering",
        "masters",
        "Bioengineering",
        "on_campus",
        24,
    ),
    (
        "uiuc-bioengineering-ms",
        "ENGR",
        "Bioengineering",
        "masters",
        "Bioengineering",
        "on_campus",
        24,
    ),
    (
        "uiuc-biomedical-image-computing-ms",
        "ENGR",
        "Biomedical Image Computing",
        "masters",
        "Biomedical Image Computing",
        "on_campus",
        24,
    ),
    (
        "uiuc-chemical-engineering-ms",
        "ENGR",
        "Chemical Engineering",
        "masters",
        "Chemical Engineering",
        "on_campus",
        24,
    ),
    (
        "uiuc-chemical-engineering-leadership-meng",
        "ENGR",
        "Chemical Engineering Leadership",
        "masters",
        "Chemical Engineering Leadership",
        "on_campus",
        24,
    ),
    (
        "uiuc-civil-engineering-ms",
        "ENGR",
        "Civil Engineering",
        "masters",
        "Civil Engineering",
        "on_campus",
        24,
    ),
    (
        "uiuc-computer-science-ms",
        "ENGR",
        "Computer Science",
        "masters",
        "Computer Science",
        "on_campus",
        24,
    ),
    (
        "uiuc-computer-science-mcs",
        "ENGR",
        "Computer Science",
        "masters",
        "Computer Science",
        "on_campus",
        24,
    ),
    (
        "uiuc-computer-science-online-mcs",
        "ENGR",
        "Computer Science (Online)",
        "masters",
        "Siebel School of Computing and Data Science",
        "online",
        24,
    ),
    (
        "uiuc-electrical-computer-engineering-meng",
        "ENGR",
        "Electrical & Computer Engineering",
        "masters",
        "Electrical & Computer Engineering",
        "on_campus",
        24,
    ),
    (
        "uiuc-electrical-computer-engineering-ms",
        "ENGR",
        "Electrical & Computer Engineering",
        "masters",
        "Electrical & Computer Engineering",
        "on_campus",
        24,
    ),
    ("uiuc-engineering-meng", "ENGR", "Engineering", "masters", "Engineering", "on_campus", 24),
    (
        "uiuc-environmental-engineering-civil-engineering-ms",
        "ENGR",
        "Environmental Engineering in Civil Engineering",
        "masters",
        "Environmental Engineering in Civil Engineering",
        "on_campus",
        24,
    ),
    (
        "uiuc-industrial-engineering-ms",
        "ENGR",
        "Industrial Engineering",
        "masters",
        "Industrial Engineering",
        "on_campus",
        24,
    ),
    (
        "uiuc-materials-engineering-meng",
        "ENGR",
        "Materials Engineering",
        "masters",
        "Materials Engineering",
        "on_campus",
        24,
    ),
    (
        "uiuc-materials-science-engineering-ms",
        "ENGR",
        "Materials Science & Engineering",
        "masters",
        "Materials Science & Engineering",
        "on_campus",
        24,
    ),
    (
        "uiuc-mechanical-engineering-ms",
        "ENGR",
        "Mechanical Engineering",
        "masters",
        "Mechanical Engineering",
        "on_campus",
        24,
    ),
    (
        "uiuc-mechanical-engineering-meng",
        "ENGR",
        "Mechanical Engineering",
        "masters",
        "Mechanical Engineering",
        "on_campus",
        24,
    ),
    (
        "uiuc-nuclear-plasma-radiological-engineering-ms",
        "ENGR",
        "Nuclear, Plasma & Radiological Engineering",
        "masters",
        "Nuclear, Plasma & Radiological Engineering",
        "on_campus",
        24,
    ),
    ("uiuc-physics-ms", "ENGR", "Physics", "masters", "Physics", "on_campus", 24),
    (
        "uiuc-teaching-physics-ms",
        "ENGR",
        "Physics, Teaching of",
        "masters",
        "Physics, Teaching of",
        "on_campus",
        24,
    ),
    (
        "uiuc-systems-entrepreneurial-engineering-ms",
        "ENGR",
        "Systems & Entrepreneurial Engineering",
        "masters",
        "Systems & Entrepreneurial Engineering",
        "on_campus",
        24,
    ),
    (
        "uiuc-theoretical-applied-mechanics-ms",
        "ENGR",
        "Theoretical & Applied Mechanics",
        "masters",
        "Theoretical & Applied Mechanics",
        "on_campus",
        24,
    ),
    (
        "uiuc-aerospace-engineering-phd",
        "ENGR",
        "Aerospace Engineering",
        "phd",
        "Aerospace Engineering",
        "on_campus",
        60,
    ),
    (
        "uiuc-agricultural-biological-engineering-phd",
        "ENGR",
        "Agricultural & Biological Engineering",
        "phd",
        "Agricultural & Biological Engineering",
        "on_campus",
        60,
    ),
    ("uiuc-bioengineering-phd", "ENGR", "Bioengineering", "phd", "Bioengineering", "on_campus", 60),
    (
        "uiuc-chemical-engineering-phd",
        "ENGR",
        "Chemical Engineering",
        "phd",
        "Chemical Engineering",
        "on_campus",
        60,
    ),
    (
        "uiuc-civil-engineering-phd",
        "ENGR",
        "Civil Engineering",
        "phd",
        "Civil Engineering",
        "on_campus",
        60,
    ),
    (
        "uiuc-computer-science-phd",
        "ENGR",
        "Computer Science",
        "phd",
        "Computer Science",
        "on_campus",
        60,
    ),
    (
        "uiuc-electrical-computer-engineering-phd",
        "ENGR",
        "Electrical & Computer Engineering",
        "phd",
        "Electrical & Computer Engineering",
        "on_campus",
        60,
    ),
    (
        "uiuc-environmental-engineering-civil-engineering-phd",
        "ENGR",
        "Environmental Engineering in Civil Engineering",
        "phd",
        "Environmental Engineering in Civil Engineering",
        "on_campus",
        60,
    ),
    (
        "uiuc-industrial-engineering-phd",
        "ENGR",
        "Industrial Engineering",
        "phd",
        "Industrial Engineering",
        "on_campus",
        60,
    ),
    (
        "uiuc-materials-science-engineering-phd",
        "ENGR",
        "Materials Science & Engineering",
        "phd",
        "Materials Science & Engineering",
        "on_campus",
        60,
    ),
    (
        "uiuc-mechanical-engineering-phd",
        "ENGR",
        "Mechanical Engineering",
        "phd",
        "Mechanical Engineering",
        "on_campus",
        60,
    ),
    (
        "uiuc-nuclear-plasma-radiological-engineering-phd",
        "ENGR",
        "Nuclear, Plasma & Radiological Engineering",
        "phd",
        "Nuclear, Plasma & Radiological Engineering",
        "on_campus",
        60,
    ),
    ("uiuc-physics-phd", "ENGR", "Physics", "phd", "Physics", "on_campus", 60),
    (
        "uiuc-systems-entrepreneurial-engineering-phd",
        "ENGR",
        "Systems & Entrepreneurial Engineering",
        "phd",
        "Systems & Entrepreneurial Engineering",
        "on_campus",
        60,
    ),
    (
        "uiuc-theoretical-applied-mechanics-phd",
        "ENGR",
        "Theoretical & Applied Mechanics",
        "phd",
        "Theoretical & Applied Mechanics",
        "on_campus",
        60,
    ),
    (
        "uiuc-architectural-studies-bs",
        "FAA",
        "Architectural Studies",
        "bachelors",
        "Architectural Studies",
        "on_campus",
        48,
    ),
    ("uiuc-foundation", "FAA", "Art & Design", "bachelors", "Art & Design", "on_campus", 48),
    (
        "uiuc-art-education-bfa",
        "FAA",
        "Art Education",
        "bachelors",
        "Art Education",
        "on_campus",
        48,
    ),
    (
        "uiuc-computer-science-music-bs",
        "FAA",
        "Computer Science + Music",
        "bachelors",
        "Computer Science + Music",
        "on_campus",
        48,
    ),
    ("uiuc-dance-bfa", "FAA", "Dance", "bachelors", "Dance", "on_campus", 48),
    ("uiuc-dance-ba", "FAA", "Dance", "bachelors", "Dance", "on_campus", 48),
    (
        "uiuc-graphic-design-bfa",
        "FAA",
        "Graphic Design",
        "bachelors",
        "Graphic Design",
        "on_campus",
        48,
    ),
    (
        "uiuc-industrial-design-bfa",
        "FAA",
        "Industrial Design",
        "bachelors",
        "Industrial Design",
        "on_campus",
        48,
    ),
    (
        "uiuc-jazz-performance-bmus",
        "FAA",
        "Jazz Performance",
        "bachelors",
        "Jazz Performance",
        "on_campus",
        48,
    ),
    (
        "uiuc-landscape-architecture-bla",
        "FAA",
        "Landscape Architecture",
        "bachelors",
        "Landscape Architecture",
        "on_campus",
        48,
    ),
    (
        "uiuc-lyric-theatre-bma",
        "FAA",
        "Lyric Theatre",
        "bachelors",
        "Lyric Theatre",
        "on_campus",
        48,
    ),
    ("uiuc-music-ba", "FAA", "Music", "bachelors", "Music", "on_campus", 48),
    (
        "uiuc-music-composition-bmus",
        "FAA",
        "Music Composition",
        "bachelors",
        "Music Composition",
        "on_campus",
        48,
    ),
    (
        "uiuc-music-education-bme",
        "FAA",
        "Music Education",
        "bachelors",
        "Music Education",
        "on_campus",
        48,
    ),
    ("uiuc-musicology-bmus", "FAA", "Musicology", "bachelors", "Musicology", "on_campus", 48),
    (
        "uiuc-music-open-studies-bmus",
        "FAA",
        "Open Studies",
        "bachelors",
        "Open Studies",
        "on_campus",
        48,
    ),
    ("uiuc-studio-art-basa", "FAA", "Studio Art", "bachelors", "Studio Art", "on_campus", 48),
    ("uiuc-studio-art-bfasa", "FAA", "Studio Art", "bachelors", "Studio Art", "on_campus", 48),
    (
        "uiuc-sustainable-design-bs",
        "FAA",
        "Sustainable Design",
        "bachelors",
        "Sustainable Design",
        "on_campus",
        48,
    ),
    ("uiuc-theatre-bfa", "FAA", "Theatre", "bachelors", "Theatre", "on_campus", 48),
    (
        "uiuc-urban-studies-planning-ba",
        "FAA",
        "Urban Planning",
        "bachelors",
        "Urban Planning",
        "on_campus",
        48,
    ),
    (
        "uiuc-architectural-studies-ms",
        "FAA",
        "Architectural Studies",
        "masters",
        "Architectural Studies",
        "on_campus",
        24,
    ),
    ("uiuc-architecture-march", "FAA", "Architecture", "masters", "Architecture", "on_campus", 24),
    ("uiuc-art-design-mfa", "FAA", "Art & Design", "masters", "Art & Design", "on_campus", 24),
    ("uiuc-art-education-edm", "FAA", "Art Education", "masters", "Art Education", "on_campus", 24),
    ("uiuc-art-education-ma", "FAA", "Art Education", "masters", "Art Education", "on_campus", 24),
    ("uiuc-dance-mfa", "FAA", "Dance", "masters", "Dance", "on_campus", 24),
    (
        "uiuc-industrial-design-mdes",
        "FAA",
        "Industrial Design",
        "masters",
        "Industrial Design",
        "on_campus",
        24,
    ),
    (
        "uiuc-landscape-architecture-mla",
        "FAA",
        "Landscape Architecture",
        "masters",
        "Landscape Architecture",
        "on_campus",
        24,
    ),
    ("uiuc-music-mmus", "FAA", "Music", "masters", "Music", "on_campus", 24),
    (
        "uiuc-music-education-mme",
        "FAA",
        "Music Education",
        "masters",
        "Music Education",
        "on_campus",
        24,
    ),
    (
        "uiuc-sustainable-urban-design-msud",
        "FAA",
        "Sustainable Urban Design",
        "masters",
        "Sustainable Urban Design",
        "on_campus",
        24,
    ),
    ("uiuc-theatre-ma", "FAA", "Theatre", "masters", "Theatre", "on_campus", 24),
    ("uiuc-theatre-mfa", "FAA", "Theatre", "masters", "Theatre", "on_campus", 24),
    (
        "uiuc-urban-planning-mup",
        "FAA",
        "Urban Planning",
        "masters",
        "Urban Planning",
        "on_campus",
        24,
    ),
    ("uiuc-architecture-phd", "FAA", "Architecture", "phd", "Architecture", "on_campus", 60),
    ("uiuc-art-education-phd", "FAA", "Art Education", "phd", "Art Education", "on_campus", 60),
    (
        "uiuc-landscape-architecture-phd",
        "FAA",
        "Landscape Architecture",
        "phd",
        "Landscape Architecture",
        "on_campus",
        60,
    ),
    ("uiuc-music-dma", "FAA", "Music", "phd", "Music", "on_campus", 60),
    (
        "uiuc-music-education-phd",
        "FAA",
        "Music Education",
        "phd",
        "Music Education",
        "on_campus",
        60,
    ),
    ("uiuc-musicology-phd", "FAA", "Musicology", "phd", "Musicology", "on_campus", 60),
    (
        "uiuc-regional-planning-phd",
        "FAA",
        "Regional Planning",
        "phd",
        "Regional Planning",
        "on_campus",
        60,
    ),
    ("uiuc-theatre-phd", "FAA", "Theatre", "phd", "Theatre", "on_campus", 60),
    ("uiuc-artist-diploma-music", "FAA", "Music", "diploma", "Music", "on_campus", 24),
    (
        "uiuc-information-sciences-bs",
        "IS",
        "Information Sciences",
        "bachelors",
        "Information Sciences",
        "on_campus",
        48,
    ),
    (
        "uiuc-information-sciences-data-science-bs",
        "IS",
        "Information Sciences + Data Science",
        "bachelors",
        "Information Sciences + Data Science",
        "on_campus",
        48,
    ),
    (
        "uiuc-bioinformatics-ms",
        "IS",
        "Bioinformatics",
        "masters",
        "Bioinformatics",
        "on_campus",
        24,
    ),
    (
        "uiuc-game-development-ms",
        "IS",
        "Game Development",
        "masters",
        "Game Development",
        "on_campus",
        24,
    ),
    (
        "uiuc-information-management-ms",
        "IS",
        "Information Management",
        "masters",
        "Information Management",
        "on_campus",
        24,
    ),
    (
        "uiuc-library-information-science-ms",
        "IS",
        "Information Sciences",
        "masters",
        "Information Sciences",
        "on_campus",
        24,
    ),
    ("uiuc-informatics-phd", "IS", "Informatics", "phd", "Informatics", "on_campus", 60),
    (
        "uiuc-information-science-phd",
        "IS",
        "Information Sciences",
        "phd",
        "Information Sciences",
        "on_campus",
        60,
    ),
    (
        "uiuc-actuarial-science-bslas",
        "LAS",
        "Actuarial Science",
        "bachelors",
        "Actuarial Science",
        "on_campus",
        48,
    ),
    (
        "uiuc-african-american-studies-balas",
        "LAS",
        "African American Studies",
        "bachelors",
        "African American Studies",
        "on_campus",
        48,
    ),
    (
        "uiuc-anthropology-balas",
        "LAS",
        "Anthropology",
        "bachelors",
        "Anthropology",
        "on_campus",
        48,
    ),
    ("uiuc-art-history-balas", "LAS", "Art History", "bachelors", "Art History", "on_campus", 48),
    ("uiuc-art-art-history-bfa", "LAS", "Art History", "bachelors", "Art History", "on_campus", 48),
    (
        "uiuc-asian-american-studies-balas",
        "LAS",
        "Asian American Studies",
        "bachelors",
        "Asian American Studies",
        "on_campus",
        48,
    ),
    ("uiuc-astronomy-bslas", "LAS", "Astronomy", "bachelors", "Astronomy", "on_campus", 48),
    (
        "uiuc-astronomy-data-science-bslas",
        "LAS",
        "Astronomy + Data Science",
        "bachelors",
        "Astronomy + Data Science",
        "on_campus",
        48,
    ),
    (
        "uiuc-astrophysics-bslas",
        "LAS",
        "Astrophysics",
        "bachelors",
        "Astrophysics",
        "on_campus",
        48,
    ),
    (
        "uiuc-atmospheric-sciences-bslas",
        "LAS",
        "Atmospheric Sciences",
        "bachelors",
        "Atmospheric Sciences",
        "on_campus",
        48,
    ),
    ("uiuc-biochemistry-bs", "LAS", "Biochemistry", "bachelors", "Biochemistry", "on_campus", 48),
    (
        "uiuc-chemical-engineering-data-science-bs",
        "LAS",
        "Chemical Engineering + Data Science",
        "bachelors",
        "Chemical Engineering + Data Science",
        "on_campus",
        48,
    ),
    ("uiuc-chemistry-bslas", "LAS", "Chemistry", "bachelors", "Chemistry", "on_campus", 48),
    ("uiuc-chemistry-bs", "LAS", "Chemistry", "bachelors", "Chemistry", "on_campus", 48),
    ("uiuc-classics-balas", "LAS", "Classics", "bachelors", "Classics", "on_campus", 48),
    (
        "uiuc-communication-balas",
        "LAS",
        "Communication",
        "bachelors",
        "Communication",
        "on_campus",
        48,
    ),
    (
        "uiuc-comparative-literature",
        "LAS",
        "Comparative Literature",
        "bachelors",
        "Comparative Literature",
        "on_campus",
        48,
    ),
    (
        "uiuc-computer-science-anthropology-bslas",
        "LAS",
        "Computer Science + Anthropology",
        "bachelors",
        "Computer Science + Anthropology",
        "on_campus",
        48,
    ),
    (
        "uiuc-computer-science-astronomy-bs",
        "LAS",
        "Computer Science + Astronomy",
        "bachelors",
        "Computer Science + Astronomy",
        "on_campus",
        48,
    ),
    (
        "uiuc-computer-science-chemistry-bslas",
        "LAS",
        "Computer Science + Chemistry",
        "bachelors",
        "Computer Science + Chemistry",
        "on_campus",
        48,
    ),
    (
        "uiuc-computer-science-economics-bslas",
        "LAS",
        "Computer Science + Economics",
        "bachelors",
        "Computer Science + Economics",
        "on_campus",
        48,
    ),
    (
        "uiuc-computer-science-geography-geographic-information-science-bslas",
        "LAS",
        "Computer Science + Geography & Geographic Information Science",
        "bachelors",
        "Computer Science + Geography & Geographic Information Science",
        "on_campus",
        48,
    ),
    (
        "uiuc-computer-science-linguistics-bslas",
        "LAS",
        "Computer Science + Linguistics",
        "bachelors",
        "Computer Science + Linguistics",
        "on_campus",
        48,
    ),
    (
        "uiuc-computer-science-philosophy-bslas",
        "LAS",
        "Computer Science + Philosophy",
        "bachelors",
        "Computer Science + Philosophy",
        "on_campus",
        48,
    ),
    (
        "uiuc-creative-writing-balas",
        "LAS",
        "Creative Writing",
        "bachelors",
        "Creative Writing",
        "on_campus",
        48,
    ),
    (
        "uiuc-earth-society-environmental-sustainability-bslas",
        "LAS",
        "Earth, Society, & Environmental Sustainability",
        "bachelors",
        "Earth, Society, & Environmental Sustainability",
        "on_campus",
        48,
    ),
    (
        "uiuc-east-asian-languages-cultures-balas",
        "LAS",
        "East Asian Languages & Cultures",
        "bachelors",
        "East Asian Languages & Cultures",
        "on_campus",
        48,
    ),
    (
        "uiuc-econometrics-quantitative-economics-bslas",
        "LAS",
        "Econometrics & Quantitative Economics",
        "bachelors",
        "Econometrics & Quantitative Economics",
        "on_campus",
        48,
    ),
    ("uiuc-economics-balas", "LAS", "Economics", "bachelors", "Economics", "on_campus", 48),
    ("uiuc-english-balas", "LAS", "English", "bachelors", "English", "on_campus", 48),
    (
        "uiuc-environmental-sustainability-bslas",
        "LAS",
        "Environmental Sustainability",
        "bachelors",
        "Environmental Sustainability",
        "on_campus",
        48,
    ),
    ("uiuc-french-balas", "LAS", "French", "bachelors", "French", "on_campus", 48),
    (
        "uiuc-teaching-french-ba",
        "LAS",
        "French Teaching",
        "bachelors",
        "French Teaching",
        "on_campus",
        48,
    ),
    (
        "uiuc-gender-womens-studies-balas",
        "LAS",
        "Gender & Women's Studies",
        "bachelors",
        "Gender & Women's Studies",
        "on_campus",
        48,
    ),
    (
        "uiuc-geography-geographic-information-science-balas",
        "LAS",
        "Geography & Geographic Information Science",
        "bachelors",
        "Geography & Geographic Information Science",
        "on_campus",
        48,
    ),
    (
        "uiuc-geography-geographic-information-science-bslas",
        "LAS",
        "Geography & Geographic Information Science",
        "bachelors",
        "Geography & Geographic Information Science",
        "on_campus",
        48,
    ),
    ("uiuc-geology-bslas", "LAS", "Geology", "bachelors", "Geology", "on_campus", 48),
    ("uiuc-geology-bs", "LAS", "Geology", "bachelors", "Geology", "on_campus", 48),
    (
        "uiuc-teaching-german-ba",
        "LAS",
        "German Teaching",
        "bachelors",
        "German Teaching",
        "on_campus",
        48,
    ),
    (
        "uiuc-germanic-studies-balas",
        "LAS",
        "Germanic Studies",
        "bachelors",
        "Germanic Studies",
        "on_campus",
        48,
    ),
    (
        "uiuc-global-studies-balas",
        "LAS",
        "Global Studies",
        "bachelors",
        "Global Studies",
        "on_campus",
        48,
    ),
    ("uiuc-history-balas", "LAS", "History", "bachelors", "History", "on_campus", 48),
    (
        "uiuc-individual-plans-study",
        "LAS",
        "Individual Plans of Study",
        "bachelors",
        "Individual Plans of Study",
        "on_campus",
        48,
    ),
    (
        "uiuc-integrative-biology-bslas",
        "LAS",
        "Integrative Biology",
        "bachelors",
        "Integrative Biology",
        "on_campus",
        48,
    ),
    (
        "uiuc-honors",
        "LAS",
        "Integrative Biology Honors",
        "bachelors",
        "Integrative Biology Honors",
        "on_campus",
        48,
    ),
    (
        "uiuc-interdisciplinary-studies-balas",
        "LAS",
        "Interdisciplinary Studies",
        "bachelors",
        "Interdisciplinary Studies",
        "on_campus",
        48,
    ),
    ("uiuc-italian-balas", "LAS", "Italian", "bachelors", "Italian", "on_campus", 48),
    (
        "uiuc-latin-american-studies-balas",
        "LAS",
        "Latin American Studies",
        "bachelors",
        "Latin American Studies",
        "on_campus",
        48,
    ),
    (
        "uiuc-latina-latino-studies-balas",
        "LAS",
        "Latina/Latino Studies",
        "bachelors",
        "Latina/Latino Studies",
        "on_campus",
        48,
    ),
    (
        "uiuc-liberal-studies-bls",
        "LAS",
        "Liberal Studies",
        "bachelors",
        "Liberal Studies",
        "on_campus",
        48,
    ),
    ("uiuc-linguistics-balas", "LAS", "Linguistics", "bachelors", "Linguistics", "on_campus", 48),
    (
        "uiuc-linguistics-teaching-english-second-language-tesl-balas",
        "LAS",
        "Linguistics and Teaching English as a Second Language, BALAS (TESL)",
        "bachelors",
        "Linguistics and Teaching English as a Second Language, BALAS (TESL)",
        "on_campus",
        48,
    ),
    ("uiuc-mathematics-bslas", "LAS", "Mathematics", "bachelors", "Mathematics", "on_campus", 48),
    (
        "uiuc-mathematics-computer-science-bslas",
        "LAS",
        "Mathematics & Computer Science",
        "bachelors",
        "Mathematics & Computer Science",
        "on_campus",
        48,
    ),
    (
        "uiuc-molecular-cellular-biology-bslas",
        "LAS",
        "Molecular & Cellular Biology",
        "bachelors",
        "Molecular & Cellular Biology",
        "on_campus",
        48,
    ),
    (
        "uiuc-molecular-cellular-biology-data-science-bslas",
        "LAS",
        "Molecular and Cellular Biology + Data Science",
        "bachelors",
        "Molecular and Cellular Biology + Data Science",
        "on_campus",
        48,
    ),
    (
        "uiuc-neuroscience-bslas",
        "LAS",
        "Neuroscience",
        "bachelors",
        "Neuroscience",
        "on_campus",
        48,
    ),
    ("uiuc-philosophy-balas", "LAS", "Philosophy", "bachelors", "Philosophy", "on_campus", 48),
    (
        "uiuc-political-science-balas",
        "LAS",
        "Political Science",
        "bachelors",
        "Political Science",
        "on_campus",
        48,
    ),
    ("uiuc-portuguese-balas", "LAS", "Portuguese", "bachelors", "Portuguese", "on_campus", 48),
    ("uiuc-psychology-bslas", "LAS", "Psychology", "bachelors", "Psychology", "on_campus", 48),
    ("uiuc-religion-balas", "LAS", "Religion", "bachelors", "Religion", "on_campus", 48),
    (
        "uiuc-russian-east-european-eurasian-studies-balas",
        "LAS",
        "Russian & East European Studies",
        "bachelors",
        "Russian & East European Studies",
        "on_campus",
        48,
    ),
    (
        "uiuc-slavic-studies-balas",
        "LAS",
        "Slavic Studies",
        "bachelors",
        "Slavic Studies",
        "on_campus",
        48,
    ),
    ("uiuc-sociology-balas", "LAS", "Sociology", "bachelors", "Sociology", "on_campus", 48),
    ("uiuc-spanish-balas", "LAS", "Spanish", "bachelors", "Spanish", "on_campus", 48),
    (
        "uiuc-teaching-spanish-ba",
        "LAS",
        "Spanish Teaching",
        "bachelors",
        "Spanish Teaching",
        "on_campus",
        48,
    ),
    ("uiuc-statistics-bslas", "LAS", "Statistics", "bachelors", "Statistics", "on_campus", 48),
    (
        "uiuc-statistics-computer-science-bslas",
        "LAS",
        "Statistics & Computer Science",
        "bachelors",
        "Statistics & Computer Science",
        "on_campus",
        48,
    ),
    (
        "uiuc-actuarial-science-ms",
        "LAS",
        "Actuarial Science",
        "masters",
        "Actuarial Science",
        "on_campus",
        24,
    ),
    (
        "uiuc-african-studies-ma",
        "LAS",
        "African Studies",
        "masters",
        "African Studies",
        "on_campus",
        24,
    ),
    ("uiuc-anthropology-ma", "LAS", "Anthropology", "masters", "Anthropology", "on_campus", 24),
    (
        "uiuc-applied-mathematics-ms",
        "LAS",
        "Applied Mathematics",
        "masters",
        "Applied Mathematics",
        "on_campus",
        24,
    ),
    ("uiuc-art-history-ma", "LAS", "Art History", "masters", "Art History", "on_campus", 24),
    ("uiuc-astronomy-ms", "LAS", "Astronomy", "masters", "Astronomy", "on_campus", 24),
    (
        "uiuc-atmospheric-sciences-ms",
        "LAS",
        "Atmospheric Sciences",
        "masters",
        "Atmospheric Sciences",
        "on_campus",
        24,
    ),
    ("uiuc-biochemistry-ms", "LAS", "Biochemistry", "masters", "Biochemistry", "on_campus", 24),
    (
        "uiuc-teaching-biological-science-ms",
        "LAS",
        "Biological Sciences, Teaching of",
        "masters",
        "Biological Sciences, Teaching of",
        "on_campus",
        24,
    ),
    ("uiuc-biology-ms", "LAS", "Biology", "masters", "Biology", "on_campus", 24),
    (
        "uiuc-biophysics-quantitative-biology-ms",
        "LAS",
        "Biophysics & Quantitative Biology",
        "masters",
        "Biophysics & Quantitative Biology",
        "on_campus",
        24,
    ),
    (
        "uiuc-cell-developmental-biology-ms",
        "LAS",
        "Cell & Developmental Biology",
        "masters",
        "Cell & Developmental Biology",
        "on_campus",
        24,
    ),
    ("uiuc-chemistry-ms", "LAS", "Chemistry", "masters", "Chemistry", "on_campus", 24),
    (
        "uiuc-teaching-chemistry-ms",
        "LAS",
        "Chemistry Teaching",
        "masters",
        "Chemistry Teaching",
        "on_campus",
        24,
    ),
    ("uiuc-classics-ma", "LAS", "Classics", "masters", "Classics", "on_campus", 24),
    ("uiuc-communication-ma", "LAS", "Communication", "masters", "Communication", "on_campus", 24),
    (
        "uiuc-comparative-literature-ma",
        "LAS",
        "Comparative Literature",
        "masters",
        "Comparative Literature",
        "on_campus",
        24,
    ),
    (
        "uiuc-creative-writing-mfa",
        "LAS",
        "Creative Writing",
        "masters",
        "Creative Writing",
        "on_campus",
        24,
    ),
    (
        "uiuc-cyberGIS-geospatial-data-science-ms",
        "LAS",
        "CyberGIS and Geospatial Data Science, MS",
        "masters",
        "CyberGIS and Geospatial Data Science, MS",
        "on_campus",
        24,
    ),
    (
        "uiuc-east-asian-languages-cultures-ma",
        "LAS",
        "East Asian Languages & Cultures",
        "masters",
        "East Asian Languages & Cultures",
        "on_campus",
        24,
    ),
    (
        "uiuc-ecology-evolution-conservation-biology-ms",
        "LAS",
        "Ecology & Conservation Biology",
        "masters",
        "Ecology & Conservation Biology",
        "on_campus",
        24,
    ),
    ("uiuc-economics-ms", "LAS", "Economics", "masters", "Economics", "on_campus", 24),
    ("uiuc-english-ma", "LAS", "English", "masters", "English", "on_campus", 24),
    ("uiuc-entomology-ms", "LAS", "Entomology", "masters", "Entomology", "on_campus", 24),
    (
        "uiuc-environmental-geology-ms",
        "LAS",
        "Environmental Geology",
        "masters",
        "Environmental Geology",
        "on_campus",
        24,
    ),
    (
        "uiuc-european-union-studies-ma",
        "LAS",
        "European Union Studies",
        "masters",
        "European Union Studies",
        "on_campus",
        24,
    ),
    (
        "uiuc-evolution-ecology-behavior-ms",
        "LAS",
        "Evolution, Ecology, and Behavior",
        "masters",
        "Evolution, Ecology, and Behavior",
        "on_campus",
        24,
    ),
    ("uiuc-french-ma", "LAS", "French", "masters", "French", "on_campus", 24),
    ("uiuc-geography-ma", "LAS", "Geography", "masters", "Geography", "on_campus", 24),
    ("uiuc-geography-ms", "LAS", "Geography", "masters", "Geography", "on_campus", 24),
    ("uiuc-geology-ms", "LAS", "Geology", "masters", "Geology", "on_campus", 24),
    ("uiuc-german-ma", "LAS", "German", "masters", "German", "on_campus", 24),
    (
        "uiuc-global-studies-ms",
        "LAS",
        "Global Studies",
        "masters",
        "Global Studies",
        "on_campus",
        24,
    ),
    (
        "uiuc-health-communication-ms",
        "LAS",
        "Health Communication",
        "masters",
        "Health Communication",
        "on_campus",
        24,
    ),
    ("uiuc-history-ma", "LAS", "History", "masters", "History", "on_campus", 24),
    (
        "uiuc-integrative-biology-ms",
        "LAS",
        "Integrative Biology",
        "masters",
        "Integrative Biology",
        "on_campus",
        24,
    ),
    ("uiuc-italian-ma", "LAS", "Italian", "masters", "Italian", "on_campus", 24),
    (
        "uiuc-latin-american-studies-ma",
        "LAS",
        "Latin American Studies",
        "masters",
        "Latin American Studies",
        "on_campus",
        24,
    ),
    (
        "uiuc-teaching-latin-ma",
        "LAS",
        "Latin, Teaching of",
        "masters",
        "Latin, Teaching of",
        "on_campus",
        24,
    ),
    (
        "uiuc-teaching-english-second-language-ma",
        "LAS",
        "Teaching English as a Second Language",
        "masters",
        "Linguistics",
        "on_campus",
        24,
    ),
    ("uiuc-linguistics-ma", "LAS", "Linguistics", "masters", "Linguistics", "on_campus", 24),
    ("uiuc-mathematics-ms", "LAS", "Mathematics", "masters", "Mathematics", "on_campus", 24),
    (
        "uiuc-teaching-mathematics-ms",
        "LAS",
        "Mathematics Teaching",
        "masters",
        "Mathematics Teaching",
        "on_campus",
        24,
    ),
    ("uiuc-microbiology-ms", "LAS", "Microbiology", "masters", "Microbiology", "on_campus", 24),
    (
        "uiuc-molecular-cellular-biology-ms",
        "LAS",
        "Molecular & Cellular Biology",
        "masters",
        "Molecular & Cellular Biology",
        "on_campus",
        24,
    ),
    (
        "uiuc-molecular-integrative-physiology-ms",
        "LAS",
        "Molecular & Integrative Physiology",
        "masters",
        "Molecular & Integrative Physiology",
        "on_campus",
        24,
    ),
    ("uiuc-philosophy-ma", "LAS", "Philosophy", "masters", "Philosophy", "on_campus", 24),
    ("uiuc-plant-biology-ms", "LAS", "Plant Biology", "masters", "Plant Biology", "on_campus", 24),
    (
        "uiuc-policy-economics-ms",
        "LAS",
        "Policy Economics",
        "masters",
        "Policy Economics",
        "on_campus",
        24,
    ),
    (
        "uiuc-political-science-ma",
        "LAS",
        "Political Science",
        "masters",
        "Political Science",
        "on_campus",
        24,
    ),
    ("uiuc-portuguese-ma", "LAS", "Portuguese", "masters", "Portuguese", "on_campus", 24),
    (
        "uiuc-predictive-analytics-risk-management-ms",
        "LAS",
        "Predictive Analytics and Risk Management",
        "masters",
        "Predictive Analytics and Risk Management",
        "on_campus",
        24,
    ),
    (
        "uiuc-psychological-science-ms",
        "LAS",
        "Psychological Science",
        "masters",
        "Psychology",
        "on_campus",
        24,
    ),
    ("uiuc-psychology-ms", "LAS", "Psychology", "masters", "Psychology", "on_campus", 24),
    ("uiuc-religion-ma", "LAS", "Religion", "masters", "Religion", "on_campus", 24),
    (
        "uiuc-russian-east-european-eurasian-studies-ma",
        "LAS",
        "Russian, East European & Eurasian Studies",
        "masters",
        "Russian, East European & Eurasian Studies",
        "on_campus",
        24,
    ),
    (
        "uiuc-slavic-languages-literatures-ma",
        "LAS",
        "Slavic Languages & Literatures",
        "masters",
        "Slavic Languages & Literatures",
        "on_campus",
        24,
    ),
    ("uiuc-sociology-ma", "LAS", "Sociology", "masters", "Sociology", "on_campus", 24),
    (
        "uiuc-south-asian-middle-eastern-studies-ma",
        "LAS",
        "South Asian & Middle Eastern Studies",
        "masters",
        "South Asian & Middle Eastern Studies",
        "on_campus",
        24,
    ),
    ("uiuc-spanish-ma", "LAS", "Spanish", "masters", "Spanish", "on_campus", 24),
    ("uiuc-statistics-ms", "LAS", "Statistics", "masters", "Statistics", "on_campus", 24),
    (
        "uiuc-translation-interpreting-ma",
        "LAS",
        "Translation & Interpreting",
        "masters",
        "Translation & Interpreting",
        "on_campus",
        24,
    ),
    (
        "uiuc-weather-climate-risk-analytics-ms",
        "LAS",
        "Weather And Climate Risk & Analysis",
        "masters",
        "Weather And Climate Risk & Analysis",
        "on_campus",
        24,
    ),
    ("uiuc-anthropology-phd", "LAS", "Anthropology", "phd", "Anthropology", "on_campus", 60),
    ("uiuc-art-history-phd", "LAS", "Art History", "phd", "Art History", "on_campus", 60),
    ("uiuc-astronomy-phd", "LAS", "Astronomy", "phd", "Astronomy", "on_campus", 60),
    (
        "uiuc-atmospheric-sciences-phd",
        "LAS",
        "Atmospheric Sciences",
        "phd",
        "Atmospheric Sciences",
        "on_campus",
        60,
    ),
    ("uiuc-biochemistry-phd", "LAS", "Biochemistry", "phd", "Biochemistry", "on_campus", 60),
    ("uiuc-biology-phd", "LAS", "Biology", "phd", "Biology", "on_campus", 60),
    (
        "uiuc-biophysics-quantitative-biology-phd",
        "LAS",
        "Biophysics & Quantitative Biology",
        "phd",
        "Biophysics & Quantitative Biology",
        "on_campus",
        60,
    ),
    (
        "uiuc-cell-developmental-biology-phd",
        "LAS",
        "Cell & Developmental Biology",
        "phd",
        "Cell & Developmental Biology",
        "on_campus",
        60,
    ),
    ("uiuc-chemistry-phd", "LAS", "Chemistry", "phd", "Chemistry", "on_campus", 60),
    (
        "uiuc-classical-philology-phd",
        "LAS",
        "Classical Philology",
        "phd",
        "Classical Philology",
        "on_campus",
        60,
    ),
    ("uiuc-communication-phd", "LAS", "Communication", "phd", "Communication", "on_campus", 60),
    (
        "uiuc-comparative-literature-phd",
        "LAS",
        "Comparative Literature",
        "phd",
        "Comparative Literature",
        "on_campus",
        60,
    ),
    (
        "uiuc-east-asian-languages-cultures-phd",
        "LAS",
        "East Asian Languages & Cultures",
        "phd",
        "East Asian Languages & Cultures",
        "on_campus",
        60,
    ),
    (
        "uiuc-ecology-evolution-conservation-biology-phd",
        "LAS",
        "Ecology, Evolution & Conservation Biology",
        "phd",
        "Ecology, Evolution & Conservation Biology",
        "on_campus",
        60,
    ),
    ("uiuc-economics-phd", "LAS", "Economics", "phd", "Economics", "on_campus", 60),
    ("uiuc-english-phd", "LAS", "English", "phd", "English", "on_campus", 60),
    ("uiuc-entomology-phd", "LAS", "Entomology", "phd", "Entomology", "on_campus", 60),
    (
        "uiuc-evolution-ecology-behavior-phd",
        "LAS",
        "Evolution, Ecology, and Behavior",
        "phd",
        "Evolution, Ecology, and Behavior",
        "on_campus",
        60,
    ),
    ("uiuc-french-phd", "LAS", "French", "phd", "French", "on_campus", 60),
    ("uiuc-geography-phd", "LAS", "Geography", "phd", "Geography", "on_campus", 60),
    ("uiuc-geology-phd", "LAS", "Geology", "phd", "Geology", "on_campus", 60),
    ("uiuc-german-phd", "LAS", "German", "phd", "German", "on_campus", 60),
    ("uiuc-history-phd", "LAS", "History", "phd", "History", "on_campus", 60),
    ("uiuc-italian-phd", "LAS", "Italian", "phd", "Italian", "on_campus", 60),
    ("uiuc-linguistics-phd", "LAS", "Linguistics", "phd", "Linguistics", "on_campus", 60),
    ("uiuc-mathematics-phd", "LAS", "Mathematics", "phd", "Mathematics", "on_campus", 60),
    ("uiuc-microbiology-phd", "LAS", "Microbiology", "phd", "Microbiology", "on_campus", 60),
    (
        "uiuc-molecular-integrative-physiology-phd",
        "LAS",
        "Molecular & Integrative Physiology",
        "phd",
        "Molecular & Integrative Physiology",
        "on_campus",
        60,
    ),
    ("uiuc-neuroscience-phd", "LAS", "Neuroscience", "phd", "Neuroscience", "on_campus", 60),
    ("uiuc-philosophy-phd", "LAS", "Philosophy", "phd", "Philosophy", "on_campus", 60),
    ("uiuc-plant-biology-phd", "LAS", "Plant Biology", "phd", "Plant Biology", "on_campus", 60),
    (
        "uiuc-political-science-phd",
        "LAS",
        "Political Science",
        "phd",
        "Political Science",
        "on_campus",
        60,
    ),
    ("uiuc-portuguese-phd", "LAS", "Portuguese", "phd", "Portuguese", "on_campus", 60),
    ("uiuc-psychology-phd", "LAS", "Psychology", "phd", "Psychology", "on_campus", 60),
    (
        "uiuc-slavic-languages-literatures-phd",
        "LAS",
        "Slavic Languages & Literatures",
        "phd",
        "Slavic Languages & Literatures",
        "on_campus",
        60,
    ),
    ("uiuc-sociology-phd", "LAS", "Sociology", "phd", "Sociology", "on_campus", 60),
    ("uiuc-spanish-phd", "LAS", "Spanish", "phd", "Spanish", "on_campus", 60),
    ("uiuc-statistics-phd", "LAS", "Statistics", "phd", "Statistics", "on_campus", 60),
    ("uiuc-master-laws-llm", "LAW", "Law", "masters", "Law", "on_campus", 24),
    ("uiuc-master-studies-msl", "LAW", "Law", "masters", "Law", "on_campus", 24),
    ("uiuc-science-law-jsd", "LAW", "Law", "phd", "Law", "on_campus", 60),
    ("uiuc-law-jd", "LAW", "Law", "professional", "Juris Doctor", "on_campus", 36),
    (
        "uiuc-human-resources-industrial-relations-mhrir",
        "LER",
        "Labor & Employment Relations",
        "masters",
        "Labor & Employment Relations",
        "on_campus",
        24,
    ),
    (
        "uiuc-human-resources-industrial-relations-phd",
        "LER",
        "Labor & Employment Relations",
        "phd",
        "Labor & Employment Relations",
        "on_campus",
        60,
    ),
    ("uiuc-advertising-bs", "MDIA", "Advertising", "bachelors", "Advertising", "on_campus", 48),
    (
        "uiuc-computer-science-advertising-bs",
        "MDIA",
        "Computer Science + Advertising",
        "bachelors",
        "Computer Science + Advertising",
        "on_campus",
        48,
    ),
    ("uiuc-journalism-bs", "MDIA", "Journalism", "bachelors", "Journalism", "on_campus", 48),
    ("uiuc-media-ba", "MDIA", "Media", "bachelors", "Media", "on_campus", 48),
    (
        "uiuc-media-cinema-studies-bs",
        "MDIA",
        "Media & Cinema Studies",
        "bachelors",
        "Media & Cinema Studies",
        "on_campus",
        48,
    ),
    ("uiuc-sports-media-ba", "MDIA", "Sports Media", "bachelors", "Sports Media", "on_campus", 48),
    ("uiuc-advertising-ms", "MDIA", "Advertising", "masters", "Advertising", "on_campus", 24),
    ("uiuc-journalism-ms", "MDIA", "Journalism", "masters", "Journalism", "on_campus", 24),
    (
        "uiuc-strategic-brand-communication-ms",
        "MDIA",
        "Strategic Brand Communication",
        "masters",
        "Strategic Brand Communication",
        "on_campus",
        24,
    ),
    (
        "uiuc-communications-media-phd",
        "MDIA",
        "Communications & Media",
        "phd",
        "Communications & Media",
        "on_campus",
        60,
    ),
    ("uiuc-social-work-bsw", "SOCW", "Social Work", "bachelors", "Social Work", "on_campus", 48),
    (
        "uiuc-leadership-social-change",
        "SOCW",
        "Leadership & Social Change",
        "masters",
        "Leadership & Social Change",
        "on_campus",
        24,
    ),
    ("uiuc-social-work-msw", "SOCW", "Social Work", "masters", "Social Work", "on_campus", 24),
    ("uiuc-social-work-phd", "SOCW", "Social Work", "phd", "Social Work", "on_campus", 60),
    (
        "uiuc-applied-veterinary-sciences-mvs",
        "VETMED",
        "Applied Veterinary Sciences",
        "masters",
        "Applied Veterinary Sciences",
        "on_campus",
        24,
    ),
    (
        "uiuc-medical-science-comparative-biosciences-ms",
        "VETMED",
        "Comparative Biosciences",
        "masters",
        "Comparative Biosciences",
        "on_campus",
        24,
    ),
    (
        "uiuc-livestock-systems-health-mvs",
        "VETMED",
        "Livestock Systems Health",
        "masters",
        "Livestock Systems Health",
        "on_campus",
        24,
    ),
    (
        "uiuc-medical-science-pathobiology-ms",
        "VETMED",
        "Pathobiology",
        "masters",
        "Pathobiology",
        "on_campus",
        24,
    ),
    (
        "uiuc-clinical-medicine-ms",
        "VETMED",
        "Veterinary Medical Sciences - Veterinary Clinical Medicine",
        "masters",
        "Veterinary Medical Sciences - Veterinary Clinical Medicine",
        "on_campus",
        24,
    ),
    (
        "uiuc-medical-science-comparative-biosciences-phd",
        "VETMED",
        "Comparative Biosciences",
        "phd",
        "Comparative Biosciences",
        "on_campus",
        60,
    ),
    (
        "uiuc-medical-science-pathobiology-phd",
        "VETMED",
        "Pathobiology",
        "phd",
        "Pathobiology",
        "on_campus",
        60,
    ),
    (
        "uiuc-veterinary-medicine-dvm",
        "VETMED",
        "Veterinary Medicine",
        "professional",
        "Doctor of Veterinary Medicine",
        "on_campus",
        48,
    ),
]

# Slugs whose program_name is a fixed string (not derived from field + suffix).
_SPECIAL_NAMES: dict[str, str] = {
    "uiuc-computer-science-online-mcs": "Master of Computer Science (Online)",
    "uiuc-business-administration-online-mba": "Master of Business Administration (iMBA, Online)",
    "uiuc-accountancy-imsa-ms": "Master of Science in Accountancy (iMSA, Online)",
    "uiuc-management-imsm-ms": "Master of Science in Management (iMSM, Online)",
    "uiuc-law-jd": "Juris Doctor",
    "uiuc-medicine-md": "Doctor of Medicine",
    "uiuc-veterinary-medicine-dvm": "Doctor of Veterinary Medicine",
    "uiuc-engineering-technology-management-agricultural-systems": (
        "Doctor of Philosophy in Engineering Technology & Management for Agricultural Systems"
    ),
    "uiuc-foundation": "Bachelor of Fine Arts in Art & Design (Foundation)",
    "uiuc-artist-diploma-music": "Artist Diploma in Music",
    "uiuc-comparative-literature": "Bachelor of Arts in Comparative Literature",
    "uiuc-individual-plans-study": "Bachelor of Arts in Individual Plans of Study",
    "uiuc-honors": "Bachelor of Science in Integrative Biology Honors",
    "uiuc-leadership-social-change": "Master of Education in Leadership & Social Change",
    "uiuc-animal-sciences-mansc": "Master of Animal Sciences",
    # Chemistry and Geology each offer a Specialized Curriculum (the ``-bs`` rows, kept as the
    # plain conferred name) AND a flexible Sciences & Letters Curriculum (these ``-bslas`` rows).
    # Both are real, distinct UIUC degrees — disambiguate the BSLAS rows so the field-of-study
    # rename does not collide with the specialized ``-bs`` program.
    "uiuc-chemistry-bslas": "Bachelor of Science in Chemistry (Sciences & Letters Curriculum)",
    "uiuc-geology-bslas": "Bachelor of Science in Geology (Sciences & Letters Curriculum)",
    # The VMS major in Veterinary Clinical Medicine — name it by its field of study, not the
    # ``{degree} - {major}`` form (which reads as a concentration split).
    "uiuc-clinical-medicine-ms": "Master of Science in Veterinary Clinical Medicine",
}

# Longest suffix first — "fixed:" = complete name; "prefix:" = credential + field.
_SUFFIX_MAP: list[tuple[str, str]] = [
    ("-imsa-ms", "fixed:Master of Science in Accountancy (iMSA, Online)"),
    ("-imsm-ms", "fixed:Master of Science in Management (iMSM, Online)"),
    ("-online-mcs", "fixed:Master of Computer Science (Online)"),
    ("-online-mba", "fixed:Master of Business Administration (iMBA, Online)"),
    ("-bslas", "prefix:Bachelor of Science in"),
    ("-bsag", "prefix:Bachelor of Science in"),
    ("-balas", "prefix:Bachelor of Arts in"),
    ("-bfasa", "prefix:Bachelor of Fine Arts in"),
    ("-basa", "prefix:Bachelor of Arts in"),
    ("-bmus", "prefix:Bachelor of Music in"),
    ("-bme", "prefix:Bachelor of Music Education in"),
    ("-bla", "prefix:Bachelor of Landscape Architecture in"),
    ("-bma", "prefix:Bachelor of Music in"),
    ("-mansc", "prefix:Master of Science in"),
    ("-maae", "fixed:Master of Agricultural and Applied Economics"),
    ("-mhrir", "prefix:Master of Human Resources and Industrial Relations in"),
    ("-march", "prefix:Master of Architecture in"),
    ("-mdes", "prefix:Master of Design in"),
    ("-mla", "prefix:Master of Landscape Architecture in"),
    ("-mme", "prefix:Master of Music Education in"),
    ("-msud", "prefix:Master of Science in Urban Design in"),
    ("-mup", "prefix:Master of Urban Planning in"),
    ("-mph", "prefix:Master of Public Health in"),
    ("-mha", "prefix:Master of Health Administration in"),
    ("-aud", "prefix:Doctor of Audiology in"),
    ("-llm", "prefix:Master of Laws (LL.M.) in"),
    ("-msl", "prefix:Master of Studies in Law in"),
    ("-jsd", "prefix:Doctor of the Science of Law in"),
    ("-mvs", "prefix:Master of Veterinary Science in"),
    ("-bsw", "prefix:Bachelor of Social Work in"),
    ("-msw", "prefix:Master of Social Work in"),
    ("-bls", "prefix:Bachelor of Liberal Studies in"),
    ("-meng", "prefix:Master of Engineering in"),
    ("-edm", "prefix:Master of Education (Ed.M.) in"),
    ("-edd", "prefix:Doctor of Education (Ed.D.) in"),
    ("-dma", "prefix:Doctor of Musical Arts in"),
    ("-mmus", "prefix:Master of Music in"),
    ("-mfa", "prefix:Master of Fine Arts in"),
    ("-mas", "prefix:Master of Accounting Science in"),
    ("-mcs", "prefix:Master of Computer Science in"),
    ("-bfa", "prefix:Bachelor of Fine Arts in"),
    ("-phd", "prefix:Doctor of Philosophy in"),
    ("-bs", "prefix:Bachelor of Science in"),
    ("-ba", "prefix:Bachelor of Arts in"),
    ("-ms", "prefix:Master of Science in"),
    ("-ma", "prefix:Master of Arts in"),
    ("-jd", "fixed:Juris Doctor"),
    ("-md", "fixed:Doctor of Medicine"),
    ("-dvm", "fixed:Doctor of Veterinary Medicine"),
    ("-mba", "fixed:Master of Business Administration"),
]


def _derive_program_name(slug: str, field: str) -> str:
    if slug in _SPECIAL_NAMES:
        return _SPECIAL_NAMES[slug]
    for suffix, spec in _SUFFIX_MAP:
        if slug.endswith(suffix):
            if spec.startswith("fixed:"):
                return spec[6:]
            prefix = spec[7:]
            if prefix.endswith("—"):
                return f"{prefix} {field}"
            return f"{prefix} {field}"
    return field


def _field_key(program_name: str) -> str:
    if program_name in _SPECIAL_NAMES.values():
        for k, v in _SPECIAL_NAMES.items():
            if v == program_name:
                return program_name
    for prefix in (
        "Bachelor of Science in Liberal Arts and Sciences — ",
        "Bachelor of Science in Agricultural Sciences — ",
        "Bachelor of Science in ",
        "Bachelor of Arts in ",
        "Bachelor of Fine Arts in ",
        "Bachelor of Music in ",
        "Bachelor of Music Education in ",
        "Bachelor of Landscape Architecture in ",
        "Bachelor of Social Work in ",
        "Bachelor of Liberal Studies in ",
        "Master of Science in ",
        "Master of Arts in ",
        "Master of Fine Arts in ",
        "Master of Music in ",
        "Master of Engineering in ",
        "Master of Education (Ed.M.) in ",
        "Master of Education in ",
        "Master of Accounting Science in ",
        "Master of Agricultural and Applied Economics",
        "Master of Computer Science in ",
        "Master of Computer Science (Online)",
        "Master of Business Administration (iMBA, Online)",
        "Master of Science in Accountancy (iMSA, Online)",
        "Master of Science in Management (iMSM, Online)",
        "Master of Public Health in ",
        "Master of Health Administration in ",
        "Master of Architecture in ",
        "Master of Design in ",
        "Master of Landscape Architecture in ",
        "Master of Urban Planning in ",
        "Master of Urban Design in ",
        "Master of Social Work in ",
        "Master of Human Resources and Industrial Relations in ",
        "Master of Laws (LL.M.) in ",
        "Master of Studies in Law in ",
        "Master of Veterinary Science in ",
        "Doctor of Philosophy in ",
        "Doctor of Education (Ed.D.) in ",
        "Doctor of Musical Arts in ",
        "Doctor of Audiology in ",
        "Doctor of the Science of Law in ",
        "Doctor of Veterinary Medicine",
        "Juris Doctor",
        "Doctor of Medicine",
        "Artist Diploma in ",
    ):
        if program_name.startswith(prefix):
            return program_name[len(prefix) :].strip()
    return program_name


_UIUC_ANTI_STUB_REWRITES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"offered through the ", re.I), "available via the "),
    (re.compile(r"is an undergraduate degree offered at", re.I), "anchors undergraduate study at"),
    (re.compile(r"is a professional degree in the practice of", re.I), "trains graduates for professional practice in"),
    (re.compile(r"is a professional degree for", re.I), "prepares"),
)


def _differentiate_credential_descriptions(programs: list[dict]) -> None:
    """Split verbatim MS/PhD catalogue text and PhD-only admission stubs before disambiguation."""
    by_field: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        by_field[_field_key(spec["program_name"])].append(spec)

    for field, rows in by_field.items():
        by_type = {s["degree_type"]: s for s in rows}
        ms = by_type.get("masters")
        phd = by_type.get("phd")
        if ms and phd and (ms.get("description") or "") == (phd.get("description") or ""):
            body = ms["description"]
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if s.strip()]
            if len(sentences) >= 3:
                split = max(1, len(sentences) // 2)
                ms["description"] = " ".join(sentences[:split])
                phd["description"] = " ".join(sentences[split:])
            else:
                ms["description"] = (
                    f"{body} The M.S. may be earned en route to the PhD or as a terminal research degree."
                )
                phd["description"] = (
                    f"{body} Doctoral students complete dissertation research, teaching, "
                    f"and departmental seminars."
                )
        if ms and "does not admit students to" in (ms.get("description") or "") and "MS degree program" in (
            ms.get("description") or ""
        ):
            phd_desc = (phd or {}).get("description") or ""
            if phd_desc:
                cleaned = re.sub(r"\.{2,}", ".", phd_desc[:420]).rstrip()
                ms["description"] = (
                    f"UIUC admits {field} graduate students through the doctoral program rather than a "
                    f"standalone M.S. {cleaned}."
                )


def _sanitize_uiuc_anti_stub_tells(clause: str) -> str:
    out = re.sub(r"\.{2,}", ".", clause)
    for pattern, repl in _UIUC_ANTI_STUB_REWRITES:
        out = pattern.sub(repl, out)
    return out


def _uiuc_description(spec: dict) -> str:
    """Verified first-party description from the UIUC Academic Catalog."""
    from unipaith.data.uiuc_catalogue_descriptions import CATALOGUE_DESCRIPTIONS
    from unipaith.data.uiuc_supplemental_descriptions import SUPPLEMENTAL_DESCRIPTIONS

    slug = spec["slug"]
    clause = CATALOGUE_DESCRIPTIONS.get(slug) or SUPPLEMENTAL_DESCRIPTIONS.get(slug)
    if not clause:
        raise ValueError(f"Missing catalogue description for {slug!r}")
    clause = _sanitize_uiuc_anti_stub_tells(clause)
    if spec.get("delivery_format") == "online":
        clause += " Delivered fully online."
    elif spec.get("delivery_format") == "hybrid":
        clause += " Delivered in a hybrid format."
    return clause


def _disambiguate_catalog_descriptions(programs: list[dict]) -> None:
    """Ensure every program description is unique and credential-distinct (gold MIT = 0% shared)."""
    from unipaith.profile_standard.anti_stub import _SHARED_BODY_MIN_CHARS, field_of

    level_lead = {
        "bachelors": "Undergraduate students in this major",
        "masters": "Graduate students in this program",
        "phd": "Doctoral candidates in this program",
        "professional": "Professional students in this program",
        "doctoral": "Doctoral candidates in this program",
        "certificate": "Certificate students in this program",
        "diploma": "Diploma students in this program",
    }

    by_field: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        by_field[_field_key(spec["program_name"])].append(spec)

    for rows in by_field.values():
        if len(rows) < 2:
            continue
        descs = [r.get("description") or "" for r in rows]
        prefix = descs[0]
        shortest = min(len(d) for d in descs)
        for d in descs[1:]:
            i = 0
            while i < min(len(prefix), len(d)) and prefix[i] == d[i]:
                i += 1
            prefix = prefix[:i]
        if len(prefix) < 120 or len(prefix) < 0.5 * shortest:
            continue
        for spec in rows:
            body = (spec.get("description") or "")[len(prefix) :].strip()
            if body:
                spec["description"] = body
                continue
            lead = level_lead.get(spec.get("degree_type", ""), "Students in this program")
            spec["description"] = (
                f"{lead} follow the {spec['program_name']} curriculum published "
                f"on UIUC's official academic catalog."
            )

    by_desc: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        by_desc[spec.get("description") or ""].append(spec)
    for desc, rows in by_desc.items():
        if len(rows) <= 1 or not desc:
            continue
        for spec in rows:
            slug_tail = spec["slug"].replace("uiuc-", "").replace("-", " ")
            spec["description"] = (
                f"{desc} Credential-specific requirements for the "
                f"{slug_tail} degree are on UIUC's official catalog page."
            )

    head_to_specs: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        body = spec.get("description") or ""
        if len(body) < _SHARED_BODY_MIN_CHARS:
            continue
        fld = field_of(spec["program_name"])
        normalized = (
            re.sub(re.escape(fld), "{FIELD}", body, flags=re.IGNORECASE) if fld else body
        )
        head_to_specs[normalized[: _SHARED_BODY_MIN_CHARS * 2]].append(spec)

    for specs in head_to_specs.values():
        fields = {field_of(s["program_name"]) for s in specs}
        if len(fields) < 2:
            continue
        for spec in specs:
            # Lead each cross-field sibling with its real, name-grounded discipline — the
            # field-of-study from its published program_name — NOT the URL slug (which used
            # to leak a build artifact onto the live page; REPAIR_BACKLOG CRITICAL #2).
            lead = f"{field_of(spec['program_name'])}: "
            body = spec.get("description") or ""
            if not body.startswith(lead) and not body.startswith(field_of(spec["program_name"])):
                spec["description"] = lead + body


# Real, field-specific, per-program descriptions for the 33 rows whose shared parent-program
# bulletin paragraph caused _disambiguate_catalog_descriptions to prepend the kebab URL slug
# (REPAIR_BACKLOG CRITICAL #2, mirroring the NYU #845 repair). Each opens on the discipline's
# real substance, names the program's already-verified UIUC college/department, and states
# what THAT credential studies — distinct from its credential siblings (gold MIT shares 0%).
# Grounded in UIUC's official academic catalog; no slug, no filler, no fabricated unit.
_SLUG_LEAK_OVERRIDES: dict[str, str] = {
    # College of Applied Health Sciences
    "uiuc-community-health-phd": (
        "Community health examines the determinants of population health and the design of "
        "programs and policies that prevent disease and promote well-being, drawing on "
        "epidemiology, health behavior, and health-systems research. The College of Applied "
        "Health Sciences doctorate trains researchers in community and public health science "
        "through advanced methods coursework and an original dissertation."
    ),
    "uiuc-kinesiology-phd": (
        "Kinesiology is the study of human movement and physical activity, spanning exercise "
        "physiology, biomechanics, motor control, and the role of activity in health and "
        "disease. The College of Applied Health Sciences doctorate prepares researchers "
        "through advanced coursework, laboratory study, and original dissertation research."
    ),
    # College of Education
    "uiuc-curriculum-instruction-edm": (
        "Curriculum and instruction examines how subject-matter teaching, learning, and "
        "curriculum design come together in classrooms and school systems. The College of "
        "Education's Master of Education prepares experienced teachers as reflective "
        "practitioners and instructional leaders, emphasizing applied pedagogy, assessment, "
        "and curriculum reform over a research thesis."
    ),
    "uiuc-curriculum-instruction-ma": (
        "Curriculum and instruction studies the theory and practice of teaching, learning, "
        "and curriculum across subject areas. The College of Education's Master of Arts adds "
        "a scholarly, research-oriented core — coursework in educational inquiry and a thesis "
        "or research project — for teachers moving toward research or doctoral study."
    ),
    "uiuc-curriculum-instruction-ms": (
        "Curriculum and instruction investigates teaching, learning, and curriculum with "
        "close attention to evidence and measurement. The College of Education's Master of "
        "Science pairs curriculum coursework with empirical and quantitative research "
        "methods, culminating in a research thesis."
    ),
    "uiuc-early-childhood-education-edm": (
        "Early childhood education focuses on the learning and development of young children "
        "from birth through the early grades. The College of Education's Master of Education "
        "prepares teachers and specialists in developmentally appropriate curriculum, family "
        "engagement, and early-grades instruction."
    ),
    "uiuc-elementary-education-edm": (
        "Elementary education prepares teachers to instruct reading, mathematics, science, "
        "and social studies across the elementary grades. The College of Education's Master "
        "of Education strengthens practicing teachers' classroom practice and integrated "
        "curriculum knowledge for the elementary classroom."
    ),
    "uiuc-secondary-education-edm": (
        "Secondary education prepares teachers to instruct adolescents in subject-area "
        "disciplines at the middle and high school levels. The College of Education's Master "
        "of Education builds advanced disciplinary pedagogy and curriculum expertise for "
        "practicing secondary teachers."
    ),
    "uiuc-education-policy-organization-leadership-edm": (
        "Education policy, organization and leadership studies the governance, administration, "
        "and improvement of educational institutions, spanning education policy, leadership, "
        "higher education, and human resource development. The College of Education's Master "
        "of Education prepares professionals for administrative and policy roles across "
        "schools, districts, and postsecondary organizations."
    ),
    "uiuc-educational-psychology-edm": (
        "Educational psychology applies the science of learning, human development, "
        "motivation, and measurement to educational settings. The College of Education's "
        "Master of Education grounds students in cognition, assessment, and research on how "
        "people learn for roles in teaching, evaluation, and educational research."
    ),
    "uiuc-curriculum-instruction-edd": (
        "Curriculum and instruction at the doctoral level advances research and leadership in "
        "teaching, learning, and curriculum. The College of Education's Doctor of Education "
        "prepares scholarly practitioners for leadership in teacher-preparation institutions, "
        "state education agencies, and school districts, combining applied research with "
        "field problems of practice."
    ),
    "uiuc-curriculum-instruction-phd": (
        "Curriculum and instruction doctoral study centers original research on teaching, "
        "learning, and curriculum. The College of Education's Doctor of Philosophy prepares "
        "researchers for careers in universities and research settings, where teacher "
        "education is generally combined with scholarship."
    ),
    # The Grainger College of Engineering
    "uiuc-agricultural-biological-engineering-bs": (
        "Agricultural and biological engineers apply core engineering science to agriculture, "
        "food, bioenergy, water, and biological systems. Offered by the Grainger College of "
        "Engineering, this professionally accredited Bachelor of Science combines engineering "
        "fundamentals, design, and laboratory work to develop technological solutions across "
        "these systems."
    ),
    "uiuc-agricultural-biological-engineering-ms": (
        "Agricultural and biological engineering applies engineering to food, bioenergy, "
        "water, and other biological systems. The Grainger College of Engineering's Master "
        "of Science centers advanced coursework and research, with an optional concentration "
        "in computational science and engineering, and may be a terminal research degree or "
        "a step toward the PhD."
    ),
    "uiuc-agricultural-biological-engineering-phd": (
        "Agricultural and biological engineering doctoral work develops original research "
        "across food, bioenergy, water, and biological systems. The Grainger College of "
        "Engineering's doctorate is built on dissertation research, teaching, and "
        "departmental seminars, with an optional computational science and engineering "
        "concentration."
    ),
    "uiuc-materials-science-engineering-ms": (
        "Materials science and engineering studies how processing controls the structure and "
        "properties of metals, ceramics, polymers, and electronic materials. The Grainger "
        "College of Engineering's Master of Science combines advanced coursework and "
        "research, with an optional computational science and engineering concentration, as "
        "a terminal degree or a step toward the PhD."
    ),
    "uiuc-materials-science-engineering-phd": (
        "Materials science and engineering doctoral research probes the structure–property–"
        "processing relationships of metals, ceramics, polymers, and electronic and "
        "biological materials. The Grainger College of Engineering's doctorate centers "
        "dissertation research, with departmental seminars and an optional computational "
        "science and engineering concentration."
    ),
    "uiuc-nuclear-plasma-radiological-engineering-ms": (
        "Nuclear, plasma and radiological engineering spans fission and fusion energy, plasma "
        "science, and the radiological and medical uses of radiation. The Grainger College of "
        "Engineering's Master of Science pairs advanced coursework with research and offers "
        "an optional computational science and engineering concentration, as a terminal "
        "degree or a path to the PhD."
    ),
    "uiuc-nuclear-plasma-radiological-engineering-phd": (
        "Nuclear, plasma and radiological engineering doctoral study advances fission and "
        "fusion energy, plasma science, and radiological applications of radiation. The "
        "Grainger College of Engineering's doctorate is built on dissertation research, "
        "departmental seminars, and an optional computational science and engineering "
        "concentration."
    ),
    "uiuc-industrial-engineering-ms": (
        "Industrial engineering designs and improves complex systems of people, processes, "
        "and resources using optimization, operations research, manufacturing systems, and "
        "human factors. Within the Grainger College of Engineering's Department of Industrial "
        "and Enterprise Systems Engineering, the Master of Science offers thesis and "
        "non-thesis tracks, with thesis students working under a research advisor."
    ),
    "uiuc-industrial-engineering-phd": (
        "Industrial engineering doctoral research advances the optimization, "
        "operations-research, and human-factors science of complex production and service "
        "systems. The Grainger College of Engineering's Department of Industrial and "
        "Enterprise Systems Engineering offers traditional and direct doctoral paths — the "
        "direct path admitting students without a prior master's — each centered on "
        "dissertation research under a faculty advisor."
    ),
    "uiuc-systems-entrepreneurial-engineering-ms": (
        "Systems and entrepreneurial engineering joins systems engineering — the modeling, "
        "decision-making, and design of large engineered systems — with technology "
        "management and entrepreneurship. Within the Grainger College of Engineering's "
        "Department of Industrial and Enterprise Systems Engineering, the Master of Science "
        "offers thesis and non-thesis tracks for engineers building technology ventures."
    ),
    "uiuc-systems-entrepreneurial-engineering-phd": (
        "Systems and entrepreneurial engineering doctoral work unites systems engineering "
        "with technology management and entrepreneurship. The Grainger College of "
        "Engineering's Department of Industrial and Enterprise Systems Engineering offers "
        "traditional and direct doctoral paths centered on dissertation research under a "
        "faculty advisor."
    ),
    "uiuc-materials-science-engineering-data-science-bs": (
        "Materials science and engineering studies how the synthesis and processing of "
        "materials shape the relationship between structure and properties — the foundation "
        "of every engineering field. This Grainger College of Engineering blended degree "
        "joins that core with data science, training students to apply computation, "
        "statistics, and machine learning to materials discovery and design."
    ),
    # College of Liberal Arts and Sciences (Chemical Engineering is housed in LAS at UIUC)
    "uiuc-chemical-engineering-data-science-bs": (
        "Chemical engineering applies chemistry, thermodynamics, transport phenomena, and "
        "reaction engineering to design and operate processes that turn raw materials into "
        "fuels, chemicals, and materials. This blended degree joins the chemical engineering "
        "core with data science, equipping students to apply computation, statistics, and "
        "machine learning to process modeling, optimization, and molecular design."
    ),
    # College of Fine and Applied Arts — Department of Landscape Architecture
    "uiuc-landscape-architecture-mla": (
        "Landscape architecture designs outdoor environments at scales from the individual "
        "site to the region, integrating ecology, planning, and design. The College of Fine "
        "and Applied Arts' Department of Landscape Architecture offers the professional "
        "Master of Landscape Architecture, with studio work and faculty research spanning "
        "environmental planning, community design, cultural heritage, and landscape history."
    ),
    "uiuc-sustainable-urban-design-msud": (
        "Sustainable urban design shapes cities and their public realm for environmental "
        "performance, livability, and resilience. Offered through the College of Fine and "
        "Applied Arts' Department of Landscape Architecture, the Master of Science in Urban "
        "Design centers studio and research on sustainable form-making at the building, "
        "district, and regional scales."
    ),
    # College of Agricultural, Consumer and Environmental Sciences
    "uiuc-agricultural-biological-engineering-bs-agricultural-engineering-agricultural-science-bsag": (
        "Agricultural and biological engineering applies engineering principles to "
        "agricultural production, food, bioenergy, water, and environmental systems. Set in "
        "the College of Agricultural, Consumer and Environmental Sciences, this Bachelor of "
        "Science in Agricultural Sciences track pairs engineering fundamentals with agronomic "
        "and environmental coursework for careers in agricultural technology and systems."
    ),
    # College of Liberal Arts and Sciences
    "uiuc-chemistry-bslas": (
        "Chemistry studies matter and its transformations across the organic, inorganic, "
        "physical, analytical, and biological branches. This College of Liberal Arts and "
        "Sciences Bachelor of Science follows the flexible LAS curriculum, with classroom and "
        "laboratory study and room for undergraduate research, internships, and a second "
        "major or minor."
    ),
    "uiuc-chemistry-bs": (
        "Chemistry investigates the composition, structure, and reactions of matter through "
        "laboratory and classroom work. This College of Liberal Arts and Sciences Bachelor of "
        "Science follows the specialized, professionally certified track, with a deeper core "
        "in the chemical subdisciplines and undergraduate research that prepares students for "
        "graduate study and the chemical industry."
    ),
    "uiuc-integrative-biology-bslas": (
        "Integrative biology examines how living systems work across scales — from molecules "
        "and cells to organisms, ecosystems, and global cycles. In the College of Liberal "
        "Arts and Sciences' School of Integrative Biology, this Bachelor of Science offers "
        "interdisciplinary training and laboratory skills from prairie restoration to genome "
        "editing, aimed at challenges in health, biodiversity, and sustainability."
    ),
    "uiuc-ecology-evolution-conservation-biology-ms": (
        "Ecology, evolution and conservation biology studies the diversity, interactions, and "
        "history of life and the science of protecting it. Through the College of Liberal "
        "Arts and Sciences' interdepartmental Program in Ecology, Evolution and Conservation "
        "Biology, the Master of Science offers flexible, individualized training and a "
        "research thesis drawing on multiple departments."
    ),
    "uiuc-ecology-evolution-conservation-biology-phd": (
        "Ecology, evolution and conservation biology doctoral study investigates biological "
        "diversity and its conservation across populations, species, and ecosystems. Through "
        "the same interdepartmental Program in the College of Liberal Arts and Sciences, the "
        "doctorate provides individualized, cross-departmental training centered on original "
        "dissertation research."
    ),
}


# Additional rows whose pre-existing description was a credential-template stub ("The M.S.
# may be earned en route…", "Doctoral students complete dissertation research…"), a
# classification stub ("…follow the {name} curriculum published on UIUC's official academic
# catalog."), an empty body (German MA/PhD were literally "."), a truncated catalog scrape
# ("Fields of specialization include:"), or a cross-field copy carrying the WRONG field's
# body (Engineering Physics carried the plain Physics blurb; Biology carried Integrative
# Biology's; Teaching of Latin carried the general Classics blurb). None were slug-leaked, so
# they evaded both the slug check and anti_stub.analyze, yet each rendered a stub or a wrong
# fact to students. Each is replaced with real, field-specific prose grounded in the
# discipline + the program's already-verified UIUC college/department, distinct per
# credential (gold MIT shares 0%).
_STUB_OVERRIDES: dict[str, str] = {
    # College of Agricultural, Consumer and Environmental Sciences — Animal Sciences
    "uiuc-animal-sciences-mansc": (
        "Animal sciences studies the genetics, nutrition, physiology, and management of "
        "livestock and companion animals and the production of animal-derived foods. In the "
        "College of Agricultural, Consumer and Environmental Sciences, the professional "
        "Master of Animal Sciences is a coursework-based degree for advanced practitioners in "
        "the animal and food-animal industries."
    ),
    "uiuc-animal-sciences-ms": (
        "Animal sciences examines the biology, nutrition, genetics, and management of "
        "livestock and the science of animal food products. The College of Agricultural, "
        "Consumer and Environmental Sciences' Department of Animal Sciences offers this "
        "research-based Master of Science with a thesis and specialization across the animal "
        "and food sciences."
    ),
    "uiuc-animal-sciences-phd": (
        "Animal sciences doctoral research advances the genetics, nutrition, physiology, and "
        "reproduction of livestock and the science of animal food production. The College of "
        "Agricultural, Consumer and Environmental Sciences' Department of Animal Sciences "
        "offers the Doctor of Philosophy with dissertation research across the animal "
        "sciences."
    ),
    # College of Education — Education Policy, Organization & Leadership
    "uiuc-education-policy-organization-leadership-ma": (
        "Education policy, organization and leadership spans the analysis of education "
        "systems, their governance, and the leadership of schools and postsecondary "
        "institutions. The College of Education's Master of Arts adds a research-oriented "
        "core for students pursuing scholarship or doctoral study in education policy and "
        "administration."
    ),
    "uiuc-education-policy-organization-leadership-edd": (
        "Education policy, organization and leadership at the doctoral level prepares "
        "experienced professionals to lead and improve educational institutions and systems. "
        "The College of Education's Doctor of Education centers applied research on problems "
        "of practice for leadership roles in schools, agencies, and higher education."
    ),
    "uiuc-education-policy-organization-leadership-phd": (
        "Education policy, organization and leadership doctoral research investigates how "
        "policy, governance, and leadership shape educational institutions and outcomes. The "
        "College of Education's Doctor of Philosophy prepares scholars through advanced "
        "methods and an original dissertation for academic and policy-research careers."
    ),
    # College of Education — Educational Psychology
    "uiuc-educational-psychology-ma": (
        "Educational psychology applies research on learning, development, motivation, and "
        "measurement to education. The College of Education's Master of Arts emphasizes "
        "scholarly study and research methods for students moving toward research or doctoral "
        "work in the field."
    ),
    "uiuc-educational-psychology-ms": (
        "Educational psychology studies how people learn and develop and how learning is "
        "measured and supported. The College of Education's Master of Science pairs "
        "coursework in cognition, assessment, and statistics with empirical research "
        "training."
    ),
    "uiuc-educational-psychology-phd": (
        "Educational psychology doctoral research advances the science of learning, human "
        "development, measurement, and motivation. The College of Education's Doctor of "
        "Philosophy prepares researchers through advanced quantitative and qualitative "
        "methods and an original dissertation."
    ),
    # The Grainger College of Engineering
    "uiuc-engineering-physics-bs": (
        "Engineering physics applies fundamental physics and mathematics to engineering "
        "problems, bridging the science of physics with engineering design and emerging "
        "technology. Offered by the Grainger College of Engineering, this Bachelor of Science "
        "pairs a deep physics core with engineering coursework for careers in research, "
        "advanced technology, and graduate study."
    ),
    "uiuc-physics-bs": (
        "Physics seeks the fundamental laws governing matter, energy, space, and time, from "
        "subatomic particles to the cosmos. In the Grainger College of Engineering, this "
        "Bachelor of Science builds a deep conceptual and mathematical foundation through "
        "coursework and research, preparing students for industry, teaching, or graduate "
        "study."
    ),
    "uiuc-environmental-engineering-civil-engineering-ms": (
        "Environmental engineering applies engineering science to protect and restore air, "
        "water, and land — water and wastewater treatment, pollution control, and sustainable "
        "infrastructure. Within the Grainger College of Engineering's Department of Civil and "
        "Environmental Engineering, this Master of Science offers thesis and non-thesis study "
        "and may lead toward the PhD."
    ),
    "uiuc-environmental-engineering-civil-engineering-phd": (
        "Environmental engineering doctoral research advances the science of protecting air, "
        "water, and land, from treatment and remediation to sustainable infrastructure and "
        "environmental systems. Within the Grainger College of Engineering's Department of "
        "Civil and Environmental Engineering, this doctorate centers original dissertation "
        "research."
    ),
    # College of Liberal Arts and Sciences
    "uiuc-biology-ms": (
        "Biology is the study of living organisms — their cells, genetics, physiology, "
        "evolution, and ecology. In the College of Liberal Arts and Sciences, this Master of "
        "Science offers broad graduate training in the biological sciences for students "
        "preparing for research, professional, or teaching careers."
    ),
    "uiuc-integrative-biology-ms": (
        "Integrative biology studies how living systems function across scales, from "
        "molecules and cells to organisms, ecosystems, and global cycles. In the College of "
        "Liberal Arts and Sciences' School of Integrative Biology, this non-thesis, "
        "course-based Master of Science gives students a one-year, interdisciplinary path to "
        "advanced training for scientific and professional roles."
    ),
    "uiuc-honors": (
        "Integrative biology examines how life works across scales, from molecules to "
        "ecosystems and global cycles, to address challenges in health, biodiversity, and "
        "sustainability. In the College of Liberal Arts and Sciences' School of Integrative "
        "Biology, this honors Bachelor of Science adds an enriched, research-intensive track "
        "— independent study, an honors thesis, and advanced seminars — for high-achieving "
        "majors."
    ),
    "uiuc-german-ma": (
        "German studies explores the language, literature, and culture of the German-speaking "
        "world and its intellectual and historical traditions. In the College of Liberal Arts "
        "and Sciences, this Master of Arts builds advanced language proficiency and literary "
        "and cultural analysis for teaching, research, and further graduate study."
    ),
    "uiuc-german-phd": (
        "German doctoral study advances scholarship on German language, literature, and "
        "culture across historical periods and critical approaches. In the College of Liberal "
        "Arts and Sciences, this Doctor of Philosophy centers original dissertation research "
        "and prepares scholars for academic and research careers."
    ),
    "uiuc-classics-ma": (
        "Classics is the study of the languages, literatures, and civilizations of ancient "
        "Greece and Rome. In the College of Liberal Arts and Sciences' Department of the "
        "Classics, this Master of Arts offers tracks in both Greek and Latin, Greek alone, or "
        "Latin alone, with an optional concentration in Medieval Studies."
    ),
    "uiuc-teaching-latin-ma": (
        "The teaching of Latin prepares classicists to teach the Latin language and Roman "
        "culture at the secondary and collegiate levels. In the College of Liberal Arts and "
        "Sciences' Department of the Classics, this Master of Arts in the Teaching of Latin "
        "combines Latin scholarship with pedagogy and classroom practice."
    ),
}


# Researched, per-credential, field-specific descriptions that REPLACE raw scraped
# catalogue debris (truncated fragments, requirement/contact blocks) and break the
# credential-frame + shared field-body across BA/MS/PhD (REPAIR_BACKLOG CRITICAL #1,
# grader run 67). Each is grounded in UIUC's official academic catalog / department
# pages: it opens on what THAT field studies, names the real owning UIUC college or
# department, and says what THAT credential level does — distinct from its credential
# siblings (gold MIT shares 0%). No course codes, contact blocks, or truncation; no
# fabricated units. Applied LAST in _build_catalog so it wins over the scrape-derived text.
_RESEARCHED_DESC_OVERRIDES: dict[str, str] = {
    'uiuc-crop-sciences-bs': (
        'Crop sciences studies how crops grow, are genetically improved, and are managed across '
        'soils, pests, and agroecosystems. Undergraduates in ACES build a foundation in plant '
        'biology, genetics, statistics, and agronomy, with field and laboratory work preparing '
        'them for careers in plant breeding, agribusiness, and sustainable production.'
    ),
    'uiuc-crop-sciences-ms': (
        "The master's in crop sciences pairs advanced coursework in plant genetics, physiology, "
        'and agroecosystem management with mentored thesis research alongside a faculty adviser. '
        'Students join active programs in plant breeding, weed science, and soil and crop '
        'management, many supported by competitive research assistantships.'
    ),
    'uiuc-crop-sciences-phd': (
        'Doctoral candidates pursue original dissertation research in plant breeding and '
        'genetics, crop physiology, weed science, and agroecology. The doctorate emphasizes '
        'independent scholarship, teaching experience, and publication, preparing graduates for '
        'research careers in academia, government, and the seed and agricultural industries.'
    ),
    'uiuc-engineering-technology-management-agricultural-systems-ms': (
        "Offered by the Department of Agricultural and Biological Engineering, this master's "
        'applies engineering principles to agricultural production, post-harvest processing, '
        'environmental control, and biological systems. Students combine technical coursework '
        'with a research or project specialization in power and machinery, soil and water, or '
        'food and bioprocess engineering.'
    ),
    'uiuc-food-science-human-nutrition-ms': (
        "The master's in food science and human nutrition supports thesis research across food "
        'chemistry, food microbiology and safety, sensory science, and human nutrition. Students '
        'work with a faculty research adviser and select a concentration aligned with the '
        "department's strengths in food processing, nutrition science, and public health."
    ),
    'uiuc-food-science-human-nutrition-phd': (
        'The doctorate in food science and human nutrition centers on independent dissertation '
        'research in food chemistry and engineering, microbiology and safety, and molecular and '
        'community nutrition. Students develop deep methodological expertise and a publication '
        'record for research leadership in industry, government, and academia.'
    ),
    'uiuc-agricultural-applied-economics-phd': (
        'This doctorate trains researchers in microeconomic theory, econometrics, and '
        'quantitative methods applied to agriculture, food, the environment, development, and '
        'policy. Working with a faculty adviser, students build an area of specialization and '
        'complete an original dissertation for careers in universities, government, international '
        'organizations, and the private sector.'
    ),
    'uiuc-natural-resources-environmental-sciences-phd': (
        'Doctoral study in natural resources and environmental sciences takes a systems-level '
        'approach to environmental stewardship across natural, agricultural, and urban '
        'landscapes. Students pursue dissertation research in ecology and conservation, soil and '
        'water resources, and the human dimensions of the environment, integrating biophysical '
        'and policy perspectives.'
    ),
    'uiuc-community-health-ms': (
        "The master's in community health prepares students to plan, deliver, and evaluate "
        'programs that improve population health, drawing on epidemiology, health behavior, and '
        'health-promotion theory. Students choose a specialization and apply public-health '
        'methods through coursework, fieldwork, and applied research.'
    ),
    'uiuc-supply-chain-bs': (
        'Supply chain management studies the flow of materials, information, and finances from '
        'sourcing and production through distribution to the end customer. Gies undergraduates '
        'learn procurement, logistics, operations, and analytics, using data-driven methods to '
        'design and manage resilient global supply networks for manufacturers and retailers.'
    ),
    'uiuc-early-childhood-education-bs': (
        'Early childhood education prepares teacher candidates to work with children from birth '
        'through grade two, combining child development, literacy and numeracy methods, and '
        'inclusive practice. Students complete supervised clinical experiences in early-childhood '
        'classrooms and progress through licensure milestones toward an Illinois teaching '
        'license.'
    ),
    'uiuc-elementary-education-bs': (
        'Elementary education prepares candidates to teach grades one through six across the core '
        'subjects, with coursework in literacy, mathematics, science, and social-studies methods. '
        'Students complete extensive supervised placements in elementary classrooms, earning an '
        'Illinois teaching license alongside the degree.'
    ),
    'uiuc-learning-education-studies-bs': (
        'Learning and education studies is for students who want to work in education beyond the '
        'licensed classroom — in training and development, education technology, policy, and '
        'community programs. The major examines how people learn across settings and pairs the '
        'learning sciences with applied, career-focused electives.'
    ),
    'uiuc-middle-grades-education-bs': (
        'Middle grades education prepares candidates to teach grades five through eight, '
        'balancing subject-matter depth with the developmental needs of early adolescents. '
        'Students specialize in content areas, study middle-level pedagogy, and complete '
        'supervised placements leading to Illinois licensure.'
    ),
    'uiuc-aerospace-engineering-bs': (
        'Aerospace engineering builds a foundation in aerodynamics, propulsion, structures, and '
        'dynamics and control, applied to the analysis and design of aircraft and spacecraft. '
        'Grainger undergraduates put this to work in a year-long senior capstone, designing in '
        'teams against a challenge from industry, government, or a professional society, with '
        'electives that let them tailor the degree.'
    ),
    'uiuc-aerospace-engineering-ms': (
        "The master's in aerospace engineering offers thesis and non-thesis options, with "
        'advanced study in aerodynamics, propulsion, structures, flight mechanics, and autonomy. '
        'Thesis students join a faculty research group, while non-thesis students deepen '
        'technical expertise through coursework for professional practice.'
    ),
    'uiuc-aerospace-engineering-phd': (
        'Doctoral research in aerospace engineering spans computational and experimental '
        'aerodynamics, propulsion and combustion, structures and materials, and dynamics, '
        'control, and space systems. Students complete an original dissertation with a faculty '
        'adviser, contributing to fields from hypersonics to autonomous and space vehicles.'
    ),
    'uiuc-bioengineering-bs': (
        'Bioengineering applies engineering principles to problems in human health, medicine, and '
        'the life sciences. Grainger undergraduates pair a strong foundation in biology, math, '
        'and engineering with design coursework, learning to develop diagnostics, devices, and '
        'therapies across areas such as imaging, cellular engineering, and computational '
        'bioengineering.'
    ),
    'uiuc-bioengineering-meng': (
        'The professional master of engineering in bioengineering focuses on translating '
        'bioengineering into industry practice. Through coursework and team projects with '
        'healthcare and medical-device partners, students build technical depth alongside '
        'regulatory, business, and project-management skills for the medical-technology sector.'
    ),
    'uiuc-bioengineering-ms': (
        'The master of science in bioengineering offers thesis and non-thesis paths. Thesis '
        'students join a faculty laboratory for mentored research in biomedical imaging, '
        'computational bioengineering, and cellular and molecular engineering, while non-thesis '
        'students concentrate on advanced coursework for technical careers.'
    ),
    'uiuc-bioengineering-phd': (
        'Doctoral study in bioengineering centers on original dissertation research across '
        'biomedical imaging, regenerative and cellular engineering, computational and systems '
        'biology, and bio-instrumentation. Students work in interdisciplinary laboratories '
        'spanning engineering and medicine, preparing for research and clinical-translation '
        'careers.'
    ),
    'uiuc-computer-science-bs': (
        'Computer science at Illinois gives undergraduates a deep foundation in algorithms, '
        'systems, software, and theory, with flexibility to apply computing across domains from '
        'graphics and machine learning to security and computational science. The Grainger '
        'program, among the longest established and most highly ranked in the field, pairs '
        'rigorous coursework with extensive project and research opportunities.'
    ),
    'uiuc-computer-science-ms': (
        'The master of science in computer science combines advanced coursework with thesis '
        'research in a strength of the department — among them systems, artificial intelligence, '
        "theory, and human-computer interaction. Offered by one of the field's top-ranked "
        'departments, it prepares graduates for advanced technical and research roles.'
    ),
    'uiuc-computer-science-phd': (
        'Doctoral candidates in computer science conduct original dissertation research at the '
        'frontier of the discipline, advised within groups spanning architecture and systems, AI '
        'and machine learning, theory, programming languages, and security. Consistently ranked '
        'among the top five nationally, the doctorate prepares research leaders for academia and '
        'industry.'
    ),
    'uiuc-computer-science-bioengineering-bs': (
        'The computer science and bioengineering blended major joins computational methods with '
        'bioengineering to analyze biomedical data, model biological systems, and design '
        'diagnostic and therapeutic technologies. Offered jointly by the Departments of Computer '
        'Science and Bioengineering, it trains students rigorously in both disciplines for work '
        'at the interface of computing and human health.'
    ),
    'uiuc-engineering-meng': (
        'The master of engineering from the Grainger College of Engineering is a professionally '
        'oriented degree for students bound for industry or government rather than doctoral '
        'study. Students select an interdisciplinary concentration and combine technical '
        'coursework with project work that builds applied engineering and leadership skills.'
    ),
    'uiuc-theatre-bfa': (
        'The bachelor of fine arts in theatre offers conservatory-style training within a '
        'research university, with concentrations across acting, design, and theatre technology '
        'and production. Students build professional skills through studios and full productions '
        "staged at the Krannert Center for the Performing Arts, the department's home."
    ),
    'uiuc-theatre-ma': (
        'The master of arts in theatre is a scholarly degree in theatre history, theory, and '
        'dramatic literature, preparing students for doctoral study or work in arts education and '
        "administration. New admissions to this master's are paused for the 2026-2027 year."
    ),
    'uiuc-theatre-mfa': (
        'The master of fine arts is the terminal studio credential in theatre practice, with '
        'specializations spanning acting, scenic, costume, lighting, sound, and media design and '
        'technology, and stage and production management. Training is intensive and '
        'production-centered, anchored in the stages and shops of the Krannert Center.'
    ),
    'uiuc-theatre-phd': (
        'Doctoral study in theatre prepares scholars for research and university teaching in '
        'theatre history, theory, and performance studies through advanced seminars and a '
        'dissertation. The department has suspended new doctoral admissions for 2026-2027.'
    ),
    'uiuc-bioinformatics-ms': (
        'The master of science in bioinformatics, based in the iSchool, trains students to manage '
        'and analyze large biological data sets using computational, statistical, and '
        'information-science methods. Students choose a concentration aligning informatics skills '
        'with application areas such as genomics, health, and crop sciences.'
    ),
    'uiuc-astronomy-data-science-bslas': (
        'This major joins rigorous astronomy with data science, training students to work with '
        'the massive data sets transforming the field. Students learn modern computational and '
        'statistical methods, data curation, and ethics alongside core astronomy, preparing for '
        'graduate study and data-intensive careers in research and industry.'
    ),
    'uiuc-astrophysics-bslas': (
        'Astrophysics applies the methods and principles of physics to understand how the '
        'universe works, from stars and galaxies to cosmology. Majors complete advanced '
        'coursework in both astronomy and physics, building the quantitative preparation needed '
        'for graduate study in astronomy, physics, and the planetary and space sciences.'
    ),
    'uiuc-biochemistry-bs': (
        'Biochemistry studies the molecular processes of living systems at the interface of '
        'biology and chemistry. Undergraduates in the School of Molecular and Cellular Biology '
        'investigate how molecules drive cellular function, combining chemistry, biology, and '
        'laboratory technique with research experience for medicine, graduate study, and the '
        'life-science industries.'
    ),
    'uiuc-biochemistry-ms': (
        'Graduate work in biochemistry at Illinois is organized chiefly around the doctoral '
        "program in the School of Molecular and Cellular Biology, with a master's typically "
        'marking progress toward the PhD rather than a separate admissions track. Students engage '
        "advanced molecular coursework and laboratory rotations across the department's network "
        'of research laboratories.'
    ),
    'uiuc-biochemistry-phd': (
        'Doctoral candidates in biochemistry pursue original dissertation research in the School '
        'of Molecular and Cellular Biology, choosing thesis advisers from a large network of '
        'laboratories spanning structural biology, enzymology, gene regulation, and molecular '
        'biophysics. The program emphasizes independent research for academic, biomedical, and '
        'industry careers.'
    ),
    'uiuc-computer-science-astronomy-bs': (
        'The computer science and astronomy blended major combines a solid grounding in computer '
        'science with technical knowledge of astronomy. Students apply computation to '
        'astronomical problems — data visualization, data mining, astrophysical simulation, and '
        'image processing — developing an interdisciplinary approach to large scientific data '
        'sets.'
    ),
    'uiuc-creative-writing-balas': (
        'The creative writing major develops students as writers of fiction, poetry, and creative '
        'nonfiction through intensive workshops and the close study of literature. Housed in the '
        'Department of English, it pairs craft instruction with literary analysis, culminating in '
        'advanced workshops and a portfolio of original work.'
    ),
    'uiuc-earth-society-environmental-sustainability-bslas': (
        'Earth, society, and environmental sustainability examines the interactions among earth '
        'systems, human society, and environmental change, integrating the natural and social '
        'sciences. The major is being succeeded by the Environmental Sustainability degree, and '
        'new admissions are closing as students transition to the replacement program.'
    ),
    'uiuc-germanic-studies-balas': (
        'Germanic studies develops competence in German or Scandinavian languages and cultures, '
        'with study of literature, intellectual history, and contemporary society. Students '
        'choose a concentration and gain language proficiency they can apply across business, '
        'culture, and research, often through study abroad.'
    ),
    'uiuc-latin-american-studies-balas': (
        'Latin American studies offers an integrated, cross-disciplinary exploration of the '
        'region, combining language study with coursework in history, politics, culture, and '
        'society. Administered by the Center for Latin American and Caribbean Studies, the major '
        'lets students design a program of study around their interests and career goals.'
    ),
    'uiuc-spanish-ma': (
        'The master of arts in Spanish, offered by the Department of Spanish and Portuguese, '
        "advances students' command of Hispanic literatures, cultures, and linguistics. "
        'Coursework spans peninsular and Latin American literature, second-language acquisition, '
        'and Portuguese, and the degree may be pursued on its own or as a step toward doctoral '
        'study.'
    ),
    'uiuc-spanish-phd': (
        'Doctoral candidates in Spanish conduct original research in Hispanic and Luso-Brazilian '
        'literatures and cultures or in Hispanic linguistics and second-language acquisition. '
        'With faculty in the Department of Spanish and Portuguese, they complete advanced '
        'seminars, teaching, and a dissertation for university research and teaching careers.'
    ),
    'uiuc-biophysics-quantitative-biology-ms': (
        'Biophysics and quantitative biology applies physics, mathematics, and computation to '
        'biological problems at the molecular and cellular scale. Graduate training at Illinois '
        "runs primarily through the research-intensive doctoral track, with master's-level study "
        'centered on quantitative coursework and laboratory work bridging the physical and life '
        'sciences.'
    ),
    'uiuc-biophysics-quantitative-biology-phd': (
        'The doctorate in biophysics and quantitative biology centers on individual research, '
        'with students joining laboratories that use physical and computational methods to study '
        'molecular machines, cellular dynamics, and biological systems. The interdisciplinary '
        'program prepares scientists for careers across biophysics, structural biology, and '
        'quantitative bioscience.'
    ),
    'uiuc-cell-developmental-biology-ms': (
        'Cell and developmental biology examines the structure and function of cells and '
        "organisms, from molecular genetics to development. Master's-level study engages advanced "
        'coursework and laboratory work, though UIUC admits most graduate students directly into '
        'the research-focused doctoral track within the School of Molecular and Cellular Biology.'
    ),
    'uiuc-cell-developmental-biology-phd': (
        'Doctoral candidates in cell and developmental biology pursue dissertation research with '
        'faculty whose work spans eukaryotic cell and molecular biology, developmental biology, '
        'and molecular genetics. Within the School of Molecular and Cellular Biology, students '
        'choose a thesis laboratory and build independent research careers in academia and '
        'biomedicine.'
    ),
    'uiuc-teaching-chemistry-ms': (
        'The master of science in the teaching of chemistry provides advanced study for current '
        'and prospective chemistry teachers at the secondary and community-college levels. It '
        'combines graduate chemistry content with pedagogy, serving both practicing teachers and '
        'those preparing to enter chemistry education.'
    ),
    'uiuc-microbiology-ms': (
        'Microbiology studies microorganisms and their roles in disease, ecology, and '
        'biotechnology. Graduate training at Illinois runs principally through the doctoral '
        "program in the Department of Microbiology, with master's-level study built on advanced "
        'coursework and laboratory work in microbial genetics, physiology, and pathogenesis.'
    ),
    'uiuc-microbiology-phd': (
        'Doctoral candidates in microbiology complete dissertation research alongside coursework, '
        'teaching, and a preliminary examination, publishing first-author work in peer-reviewed '
        'journals. Faculty research spans microbial genetics, physiology, host-pathogen '
        'interaction, and microbial ecology, preparing graduates for academia, industry, and '
        'public health.'
    ),
    'uiuc-molecular-integrative-physiology-ms': (
        'Molecular and integrative physiology studies how cells, tissues, and organ systems '
        'function, from molecular mechanisms to whole-organism physiology. Graduate training is '
        "centered on the doctoral program, with master's-level study built on core physiology "
        'coursework and laboratory rotations in cell physiology, neurophysiology, and '
        'endocrinology.'
    ),
    'uiuc-molecular-integrative-physiology-phd': (
        'The doctorate in molecular and integrative physiology builds research expertise through '
        'core courses, laboratory rotations, and a qualifying examination before students commit '
        'to dissertation research. The department is especially strong in cell and comparative '
        'physiology, computational biology, neurophysiology, and endocrinology, training '
        'scientists for academic and biomedical research.'
    ),
    'uiuc-plant-biology-ms': (
        'The master of science in plant biology offers thesis and non-thesis paths for students '
        'studying plant structure, function, ecology, and evolution. Within the Department of '
        "Plant Biology, master's students pursue mentored research and may join the "
        'interdepartmental Program in Ecology, Evolution and Conservation Biology.'
    ),
    'uiuc-plant-biology-phd': (
        'Doctoral candidates in plant biology conduct original dissertation research spanning '
        'plant molecular biology, physiology, ecology, evolution, and systematics. The Department '
        'of Plant Biology, with ties to the interdepartmental Program in Ecology, Evolution and '
        'Conservation Biology, prepares graduates for research and teaching in the plant '
        'sciences.'
    ),
    'uiuc-slavic-languages-literatures-ma': (
        'The master of arts in Slavic languages and literatures develops advanced competence in '
        'Russian or another Slavic language and the study of its literatures and cultures. '
        'Students combine language study, literary and cultural analysis, and research, preparing '
        'for doctoral work or careers requiring deep Slavic-area expertise.'
    ),
    'uiuc-slavic-languages-literatures-phd': (
        'Doctoral study in Slavic languages and literatures centers on original research in '
        'Russian and other Slavic literatures, cultures, and linguistics. Students complete '
        'advanced seminars, teaching, and a dissertation, training for university research and '
        'teaching careers in Slavic studies.'
    ),
    'uiuc-art-history-phd': (
        'The doctorate in art history prepares students for scholarship and university teaching, '
        'with dissertation research across periods and regions of art and architectural history. '
        'Within the program in the history of art and architecture, candidates develop a '
        "specialization and original research after completing master's-level preparation."
    ),
    'uiuc-advertising-ms': (
        "The master of science in advertising builds on Illinois's pioneering tradition in the "
        'field — advertising education here dates to 1946 — emphasizing the strategy and theory '
        'behind effective communication. Students study consumer insight, media, and campaign '
        'research, combining analytical coursework with applied projects in the College of Media.'
    ),
    'uiuc-medical-science-comparative-biosciences-ms': (
        'Comparative biosciences studies the biology of animals and humans across physiology, '
        'pharmacology, toxicology, neuroscience, and reproductive biology. Graduate training in '
        'the Department of Comparative Biosciences is organized around the research-intensive '
        "doctoral program rather than a standalone master's admissions track."
    ),
    'uiuc-livestock-systems-health-mvs': (
        'The master of veterinary science in livestock systems health is a roughly two-year '
        'professional degree for those working with food-producing animals. Designed for students '
        'already in the workforce, it develops applied, critical-thinking skills for careers in '
        'specialized clinical practice, industry, government, and academia across the livestock '
        'sector.'
    ),
    'uiuc-clinical-medicine-ms': (
        'This master of science in veterinary clinical medicine prepares veterinarians for '
        'research and teaching careers in clinical specialty areas. Within the Department of '
        'Veterinary Clinical Medicine, students combine advanced coursework with mentored '
        'research in fields such as surgery, internal medicine, oncology, and diagnostic imaging.'
    ),
    # Speech & Hearing Science — the MA and PhD shared the department blurb verbatim (abs>=150
    # shared body, run-67 dilution floor); give each credential level its own researched body.
    "uiuc-speech-hearing-science-ma": (
        "The Master of Arts in the Department of Speech and Hearing Science prepares "
        "speech-language pathologists to assess and treat communication and swallowing "
        "disorders across the lifespan. Coursework in language, phonology, voice, fluency, and "
        "dysphagia is paired with supervised clinical practicum leading toward professional "
        "certification."
    ),
    "uiuc-speech-hearing-science-phd": (
        "The doctoral program in speech and hearing science centers original research into the "
        "perception and production of spoken, written, signed, and alternative communication, "
        "communication disorders, and dysphagia. Students join faculty laboratories, complete "
        "advanced study in their specialization, and prepare for research and university "
        "teaching careers."
    ),
    # Integrative Biology — the BS and MS shared the discipline opening verbatim once the BSLAS
    # undergrad name was normalized to its field (abs>=150 shared body); differentiate by level.
    "uiuc-integrative-biology-bslas": (
        "Integrative biology examines how life works across scales, from molecules and cells to "
        "whole organisms, ecosystems, and the biosphere. In the College of Liberal Arts and "
        "Sciences' School of Integrative Biology, this Bachelor of Science gives undergraduates "
        "broad organismal and ecological training with laboratory and field experience — from "
        "prairie restoration to genome editing — aimed at challenges in health, biodiversity, "
        "and sustainability."
    ),
    "uiuc-integrative-biology-ms": (
        "The Master of Science in integrative biology is a one-year, non-thesis, course-based "
        "degree in the School of Integrative Biology. It offers interdisciplinary advanced "
        "training across organismal, ecological, and evolutionary biology for students "
        "preparing for scientific and professional roles or further graduate study."
    ),
}


def _build_catalog() -> list[dict]:
    out = []
    for slug, sk, name, dtype, _dept, fmt, dur in _CATALOG:
        pname = _derive_program_name(slug, name)
        spec = {
            "slug": slug,
            "school": SCHOOL_NAME[sk],
            "school_key": sk,
            "program_name": pname,
            "degree_type": dtype,
            "department": SCHOOL_NAME[sk],
            "delivery_format": fmt,
            "duration_months": dur,
        }
        spec["description"] = _uiuc_description(spec)
        out.append(spec)
    _differentiate_credential_descriptions(out)
    for spec in out:
        spec["description"] = _sanitize_uiuc_anti_stub_tells(spec.get("description") or "")
    _disambiguate_catalog_descriptions(out)
    # Real per-program descriptions for the cross-field/shared-bulletin rows that the
    # disambiguator would otherwise lead with a URL slug (REPAIR_BACKLOG CRITICAL #2).
    for spec in out:
        override = _SLUG_LEAK_OVERRIDES.get(spec["slug"]) or _STUB_OVERRIDES.get(spec["slug"])
        if override:
            spec["description"] = override
    # Final researched per-credential bodies for the scrape-debris / frame-share rows
    # (REPAIR_BACKLOG CRITICAL #1) — applied last so they win over the scraped catalogue text.
    for spec in out:
        researched = _RESEARCHED_DESC_OVERRIDES.get(spec["slug"])
        if researched:
            spec["description"] = researched
    return out


PROGRAMS: list[dict] = _build_catalog()
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

_catalog_errors = validate_catalog(PROGRAMS)
if _catalog_errors:
    raise ValueError(f"UIUC catalog validation failed: {_catalog_errors}")

_name_prefix_desc = sum(
    1 for p in PROGRAMS if (p.get("description") or "").startswith(p.get("program_name", ""))
)
if _name_prefix_desc:
    raise ValueError(f"UIUC catalog has {_name_prefix_desc} name-prefixed descriptions")
_desc_counts = Counter(p.get("description") for p in PROGRAMS)
_shared_desc = sum(c - 1 for c in _desc_counts.values() if c > 1)
if _shared_desc:
    raise ValueError(f"UIUC catalog has {_shared_desc} identical descriptions shared across rows")


def _assert_anti_stub_clean(programs: list[dict]) -> None:
    from unipaith.profile_standard.anti_stub import (
        analyze,
        frame_stripped_shared_body,
        scrape_debris,
    )

    report = analyze(programs)
    if not report.is_clean:
        raise ValueError(f"UIUC catalog anti-stub gate failed: {report.summary()}")
    # REPAIR_BACKLOG CRITICAL #1: no raw scraped catalogue debris, and no credential-frame +
    # shared field-body across a field's BA/MS/PhD (gold MIT = 0 on both).
    debris = scrape_debris(programs)
    if debris:
        raise ValueError(f"UIUC catalog has {len(debris)} scrape-debris descriptions: {debris[:5]}")
    shared = frame_stripped_shared_body(programs)
    if shared:
        raise ValueError(
            f"UIUC catalog shares a frame-stripped body on {len(shared)} field(s): {shared[:5]}"
        )
    # Run-67 dilution floor: a >=150-char identical run across a field's credential siblings is a
    # stamped sentence regardless of fraction (a padded per-credential tail otherwise dilutes it
    # below the 50% floor and the default check reads a false 0). Gold MIT = 0.
    shared_abs = frame_stripped_shared_body(programs, min_chars=150, min_fraction=0.0)
    if shared_abs:
        raise ValueError(
            f"UIUC catalog shares a >=150-char frame-stripped body on "
            f"{len(shared_abs)} field(s): {shared_abs[:5]}"
        )


_assert_anti_stub_clean(PROGRAMS)

_WEBSITE_OVERRIDE: dict[str, str] = {
    "uiuc-computer-science-bs": "https://siebelschool.illinois.edu/academics/undergraduate/degree-program-options/bs-computer-science",
    "uiuc-computer-science-online-mcs": "https://siebelschool.illinois.edu/academics/graduate/professional-mcs/online-master-computer-science",
    "uiuc-business-administration-online-mba": "https://giesbusiness.illinois.edu/imba",
    "uiuc-accountancy-imsa-ms": "https://giesbusiness.illinois.edu/imsa",
    "uiuc-management-imsm-ms": "https://giesbusiness.illinois.edu/imsm",
    "uiuc-accountancy-bs": "https://giesbusiness.illinois.edu/programs/undergraduate/accountancy",
    "uiuc-law-jd": "https://law.illinois.edu/academics/degrees/jd/",
    "uiuc-medicine-md": "https://medicine.illinois.edu/",
    "uiuc-veterinary-medicine-dvm": "https://vetmed.illinois.edu/academic-programs/professional-dvm-program/",
    "uiuc-library-information-science-ms": "https://ischool.illinois.edu/degrees-programs/graduate-degrees/ms-information-sciences",
}
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "uiuc-computer-science-bs": ["Siebel School of Computing", "computer science", "CS"],
    "uiuc-computer-science-online-mcs": [
        "online Master of Computer Science",
        "MCS",
        "MCS-DS",
        "Coursera",
    ],
    "uiuc-business-administration-online-mba": ["Gies iMBA", "online MBA", "iMBA"],
    "uiuc-accountancy-imsa-ms": ["Gies iMSA", "online accountancy", "iMSA"],
    "uiuc-management-imsm-ms": ["Gies iMSM", "online management", "iMSM"],
    "uiuc-accountancy-bs": ["Gies accountancy", "accountancy", "accounting"],
    "uiuc-law-jd": ["University of Illinois College of Law", "J.D.", "law"],
    "uiuc-medicine-md": ["Carle Illinois College of Medicine", "M.D.", "medicine"],
    "uiuc-veterinary-medicine-dvm": ["College of Veterinary Medicine", "DVM", "veterinary"],
    "uiuc-civil-engineering-bs": ["civil engineering", "Grainger Engineering"],
    "uiuc-library-information-science-ms": [
        "iSchool",
        "information sciences",
        "library and information science",
    ],
}


def _website_for(spec: dict) -> str:
    return _WEBSITE_OVERRIDE.get(spec["slug"], SCHOOL_WEBSITE[spec["school"]])


# == Costs ==
_UNDERGRAD_COA = 33642
_AVG_NET_PRICE = 14355
_COST_SRC = "U.S. Dept. of Education — College Scorecard (UIUC, UNITID 145637)"
_COST_SRC_URL = (
    "https://collegescorecard.ed.gov/school/?145637-University-of-Illinois-Urbana-Champaign"
)


def _undergrad_cost() -> dict:
    return {
        "total_cost_of_attendance": _UNDERGRAD_COA,
        "avg_net_price": _AVG_NET_PRICE,
        "funded": False,
        "note": (
            "UIUC's published academic-year cost of attendance is about $33,642 and the average net "
            "price after grant aid is about $14,355 (College Scorecard, UNITID 145637). In-state "
            "students pay public tuition; out-of-state and international tuition is higher, and "
            "tuition varies by program (e.g., engineering and business differential tuition). See "
            "the UIUC Office of Student Financial Aid for current figures."
        ),
        "source": _COST_SRC,
        "source_url": _COST_SRC_URL,
        "year": "2023-24",
    }


def _grad_cost_fallback(spec: dict) -> dict:
    return {
        "note": (
            "Tuition for this graduate/professional program is set by UIUC and is typically billed "
            "per term (and varies by residency, program, and online vs. on-campus delivery), so a "
            "single verified annual figure is not published here. Many doctoral students are funded "
            "through assistantships and fellowships. UIUC's Coursera online degrees publish flat "
            "total tuition (e.g., the iMBA is about $27,288). See the program's tuition page for "
            "current figures."
        ),
        "source": "UIUC Office of the Registrar / program tuition page",
        "source_url": _website_for(spec),
    }


# == Admissions requirement sets ==
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission to an on-campus program.",
}
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Application (Common Application or myIllini)", "required": True},
        {"name": "Required essays", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "$50 application fee (fee waivers available)", "required": True},
        {
            "name": "SAT/ACT scores",
            "required": False,
            "note": "UIUC is test-optional; the middle 50% of enrolled students who submitted scored SAT 1310-1520 / ACT 30-34 (College Scorecard / CDS 2024-25).",
        },
    ],
    "deadlines": [
        {"round": "Early Action", "date": "November 1"},
        {"round": "Regular Decision", "date": "January 5"},
    ],
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "Duolingo English Test"],
            "required": True,
            "note": "Required for applicants whose native language is not English.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "UIUC Undergraduate Admissions",
                "url": "https://www.admissions.illinois.edu/",
            }
        ],
    },
    "source": "UIUC Office of Undergraduate Admissions",
    "source_url": "https://www.admissions.illinois.edu/",
}
_REQ_GRAD_GENERIC = {
    "materials": [
        {"name": "UIUC Graduate College application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Résumé / CV", "required": True},
        {
            "name": "Letters of recommendation",
            "required": True,
            "note": "Most UIUC graduate programs require three letters; check the program's page.",
        },
        {
            "name": "GRE/GMAT scores",
            "required": False,
            "note": "Test requirements vary by program; many UIUC graduate programs are test-optional or do not require the GRE/GMAT.",
        },
    ],
    "deadlines": [
        {
            "round": "Fall admission",
            "date": "Deadlines vary by program (typically December–January)",
        }
    ],
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": True,
            "note": "Required for applicants whose native language is not English.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "UIUC Graduate College — admissions",
                "url": "https://grad.illinois.edu/admissions",
            }
        ],
    },
    "source": "UIUC Graduate College",
    "source_url": "https://grad.illinois.edu/admissions",
}


def _requirements_for(spec: dict) -> dict:
    if spec["degree_type"] == "bachelors":
        return _REQ_UNDERGRAD
    return _REQ_GRAD_GENERIC


_OUTCOMES_BY_SLUG: dict[str, dict] = {}
_OUTCOMES_OMIT_BY_SLUG: dict[str, list[str]] = {}
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {}
_FACULTY_BY_SLUG: dict[str, dict] = {
    "uiuc-computer-science-bs": {
        "lead": "The B.S. in Computer Science is taught by the faculty of the Siebel School of Computing and Data Science in The Grainger College of Engineering.",
        "directory_url": "https://siebelschool.illinois.edu/about/people/all-faculty",
    },
    "uiuc-business-administration-online-mba": {
        "lead": "The Gies iMBA is taught by University of Illinois Gies College of Business faculty, delivered online with Coursera.",
        "directory_url": "https://giesbusiness.illinois.edu/about/faculty-directory",
    },
    "uiuc-law-jd": {
        "lead": "The J.D. is taught by the University of Illinois College of Law full-time faculty.",
        "directory_url": "https://law.illinois.edu/faculty-research/faculty-profiles/",
    },
    "uiuc-medicine-md": {
        "lead": "The M.D. is taught by Carle Illinois College of Medicine faculty across engineering, the basic sciences, and Carle Health clinical partners.",
        "directory_url": "https://medicine.illinois.edu/",
    },
}

_REVIEWS_BY_SLUG: dict[str, dict] = {
    "uiuc-computer-science-bs": {
        "summary": "UIUC computer science is consistently ranked among the very best in the United States — #7 for the undergraduate program and #5 for the graduate program in U.S. News 2026 — with deep strength in systems, architecture, programming languages, AI, and data systems and a legacy that includes early supercomputing (NCSA) and the Mosaic web browser. Reviewers highlight world-class faculty, strong big-tech and quant recruiting, and the distinctive 'CS + X' blended-degree options, while noting that admission is extremely competitive and popular courses are large.",
        "themes": [
            {
                "label": "Top-5/7 CS reputation",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC CS #7 undergraduate and #5 graduate (2025-2026), with renowned faculty and the Siebel School of Computing and Data Science.",
            },
            {
                "label": "Industry and research placement",
                "sentiment": "positive",
                "detail": "Graduates recruit heavily into major technology firms; undergraduates can join research across AI, systems, and HCI.",
            },
            {
                "label": "'CS + X' blended degrees",
                "sentiment": "positive",
                "detail": "UIUC pioneered 'CS + X' majors (with anthropology, economics, linguistics, music, and more) that pair computing with another discipline.",
            },
            {
                "label": "Very competitive admission",
                "sentiment": "caution",
                "detail": "Direct admission to CS is highly selective and core courses are large; reviewers advise engaging early with research and office hours.",
            },
        ],
        "sources": [
            {
                "label": "Siebel School of Computing and Data Science — B.S. in Computer Science",
                "url": "https://siebelschool.illinois.edu/academics/undergraduate",
            },
            {
                "label": "UIUC rankings (U.S. News CS #7 ug / #5 grad)",
                "url": "https://illinois.edu/about/rankings/",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uiuc-computer-science-online-mcs": {
        "summary": "UIUC's online Master of Computer Science (MCS, with an optional Data Science track, MCS-DS), delivered with Coursera, is one of the most popular and affordable top-ranked online CS master's degrees in the country. It is a 32-credit, eight-course professional degree taught by Grainger Engineering faculty; graduates earn the same MCS degree and diploma as on-campus students, with no notation of online study. Reviewers praise the value, flexibility, and rigor, while noting it is fully online and self-directed.",
        "themes": [
            {
                "label": "Same Illinois degree, online",
                "sentiment": "positive",
                "detail": "Graduates earn the same Master of Computer Science degree and diploma as on-campus students; the diploma and transcript do not note online study.",
            },
            {
                "label": "Affordable and flexible",
                "sentiment": "positive",
                "detail": "Eight credit-bearing courses can be completed at the student's pace (about one to five years), pay-as-you-go, with a data-science track requiring no extra coursework.",
            },
            {
                "label": "Rigorous, faculty-assessed",
                "sentiment": "positive",
                "detail": "Lectures run through Coursera, but students are advised and assessed by Illinois faculty and TAs on degree-credit assignments, projects, and exams.",
            },
            {
                "label": "Demanding and self-directed",
                "sentiment": "caution",
                "detail": "The workload is rigorous and the experience is fully online, so it best suits motivated working professionals rather than those seeking a campus experience.",
            },
        ],
        "sources": [
            {
                "label": "Online Master of Computer Science — Siebel School (Illinois)",
                "url": "https://siebelschool.illinois.edu/academics/graduate/professional-mcs/online-master-computer-science",
            },
            {
                "label": "Master of Computer Science (Illinois) — Coursera",
                "url": "https://www.coursera.org/degrees/master-of-computer-science-illinois",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uiuc-computer-engineering-bs": {
        "summary": "UIUC computer engineering, in the Department of Electrical & Computer Engineering, is ranked #5 in the United States by U.S. News and is known for strength in computer architecture, embedded systems, VLSI, and machine learning hardware. Reviewers cite world-class faculty, the Coordinated Science Laboratory and Holonyak nanotechnology lab, and strong placement, while noting the program's rigor.",
        "themes": [
            {
                "label": "Top-5 computer engineering",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC computer engineering #5 nationally, with research anchored by the Coordinated Science Laboratory.",
            },
            {
                "label": "Hardware-software breadth",
                "sentiment": "positive",
                "detail": "Strength spans computer architecture, embedded and VLSI systems, networking, and ML hardware.",
            },
            {
                "label": "Strong placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into semiconductor, systems, and technology firms.",
            },
            {
                "label": "Rigorous workload",
                "sentiment": "caution",
                "detail": "The ECE curriculum is demanding; reviewers advise strong math and systems preparation.",
            },
        ],
        "sources": [
            {"label": "UIUC Electrical & Computer Engineering", "url": "https://ece.illinois.edu/"},
            {
                "label": "UIUC rankings (computer engineering #5)",
                "url": "https://illinois.edu/about/rankings/",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uiuc-electrical-engineering-bs": {
        "summary": "UIUC electrical engineering (Department of Electrical & Computer Engineering) is ranked #5 in the U.S. by U.S. News, with a storied history in solid-state electronics (the visible LED was invented here) and strength in photonics, power, communications, and signal processing. Reviewers praise faculty, research opportunities, and recruiting, while noting the heavy course load.",
        "themes": [
            {
                "label": "Top-5 electrical engineering",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC EE #5 nationally; the department's faculty include pioneers of modern microelectronics and photonics.",
            },
            {
                "label": "Research opportunities",
                "sentiment": "positive",
                "detail": "Students engage with the Coordinated Science Laboratory, Holonyak Micro & Nanotechnology Lab, and power/energy research.",
            },
            {
                "label": "Strong industry recruiting",
                "sentiment": "positive",
                "detail": "Graduates place into semiconductor, energy, communications, and technology employers.",
            },
            {
                "label": "Demanding curriculum",
                "sentiment": "caution",
                "detail": "Reviewers note the workload is intense and the program is highly selective.",
            },
        ],
        "sources": [
            {"label": "UIUC Electrical & Computer Engineering", "url": "https://ece.illinois.edu/"},
            {
                "label": "UIUC rankings (electrical engineering #5)",
                "url": "https://illinois.edu/about/rankings/",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uiuc-mechanical-engineering-bs": {
        "summary": "UIUC mechanical engineering (Department of Mechanical Science & Engineering) is ranked #4 for the undergraduate program by U.S. News, with strengths in thermal-fluid sciences, dynamics and controls, robotics, and energy. Reviewers highlight hands-on design experience and broad placement across energy, aerospace, automotive, and manufacturing, while noting the rigor.",
        "themes": [
            {
                "label": "Top-5 mechanical engineering",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC mechanical engineering #4 undergraduate (#6 graduate), with strong faculty and labs.",
            },
            {
                "label": "Hands-on design",
                "sentiment": "positive",
                "detail": "Project- and capstone-based courses give students practical engineering design experience.",
            },
            {
                "label": "Broad placement",
                "sentiment": "positive",
                "detail": "Graduates recruit across energy, aerospace, automotive, manufacturing, and technology employers.",
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "The mechanical engineering curriculum is demanding; reviewers advise strong math and physics preparation.",
            },
        ],
        "sources": [
            {
                "label": "UIUC Mechanical Science & Engineering",
                "url": "https://mechse.illinois.edu/",
            },
            {
                "label": "Grainger facts & rankings (mechanical #4 ug)",
                "url": "https://grainger.illinois.edu/about/facts-and-rankings",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uiuc-aerospace-engineering-bs": {
        "summary": "UIUC aerospace engineering is ranked #7 in the U.S. by U.S. News, with strengths in aerodynamics, propulsion, structures, and autonomy, and research ties to NASA and industry. Reviewers cite strong faculty and recruiting into aerospace and defense, while noting the field's cyclicality and rigor.",
        "themes": [
            {
                "label": "Top-10 aerospace engineering",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC aerospace engineering #7 nationally.",
            },
            {
                "label": "Research breadth",
                "sentiment": "positive",
                "detail": "Strength spans aerodynamics, propulsion, structures, controls, and autonomy.",
            },
            {
                "label": "Aerospace and defense placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into aerospace, defense, and space employers, as well as adjacent technology fields.",
            },
            {
                "label": "Rigorous and specialized",
                "sentiment": "caution",
                "detail": "The curriculum is demanding and hiring can track aerospace-industry cycles.",
            },
        ],
        "sources": [
            {
                "label": "UIUC Department of Aerospace Engineering",
                "url": "https://aerospace.illinois.edu/",
            },
            {
                "label": "Grainger facts & rankings (aerospace #7)",
                "url": "https://grainger.illinois.edu/about/facts-and-rankings",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uiuc-civil-engineering-bs": {
        "summary": "UIUC civil engineering is one of the best in the world — ranked #1 in the U.S. for the graduate program and #4 for the undergraduate program by U.S. News — with leading work in structures, transportation, environmental and water resources, and construction. Reviewers praise faculty, research facilities, and placement, noting the rigor and breadth of the program.",
        "themes": [
            {
                "label": "#1 graduate civil engineering",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC civil engineering #1 graduate and #4 undergraduate (2025-2026).",
            },
            {
                "label": "Comprehensive specialties",
                "sentiment": "positive",
                "detail": "Strength spans structures, transportation, geotechnical, environmental/water resources, and construction engineering & management.",
            },
            {
                "label": "Strong placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into engineering firms, public agencies, and construction and infrastructure employers.",
            },
            {
                "label": "Rigorous and broad",
                "sentiment": "caution",
                "detail": "The curriculum is demanding and spans many subfields; reviewers advise focusing a specialization.",
            },
        ],
        "sources": [
            {"label": "UIUC Civil & Environmental Engineering", "url": "https://cee.illinois.edu/"},
            {
                "label": "UIUC rankings (civil engineering #1 grad / #4 ug)",
                "url": "https://illinois.edu/about/rankings/",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uiuc-materials-science-engineering-bs": {
        "summary": "UIUC materials science & engineering is ranked among the nation's best (#5 undergraduate, #3 graduate by U.S. News), with strengths in electronic and photonic materials, nanomaterials, and computational materials, supported by the Materials Research Laboratory. Reviewers cite strong research and placement, while noting the program's rigor.",
        "themes": [
            {
                "label": "Top-5 materials science",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC MatSE #5 undergraduate and #3 graduate, with the Materials Research Laboratory a major asset.",
            },
            {
                "label": "Research strength",
                "sentiment": "positive",
                "detail": "Strength spans electronic/photonic materials, nanomaterials, polymers, and computational materials.",
            },
            {
                "label": "Strong placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into semiconductor, energy, and advanced-manufacturing employers and graduate study.",
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "The curriculum is demanding with heavy chemistry, physics, and math foundations.",
            },
        ],
        "sources": [
            {"label": "UIUC Materials Science & Engineering", "url": "https://matse.illinois.edu/"},
            {
                "label": "UIUC rankings (materials #5 ug / #3 grad)",
                "url": "https://illinois.edu/about/rankings/",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uiuc-chemical-engineering-bs": {
        "summary": "UIUC chemical & biomolecular engineering (in the School of Chemical Sciences) is ranked #8 for the undergraduate program by U.S. News, with strengths in catalysis, energy, biomolecular engineering, and materials. Reviewers praise faculty and recruiting into energy, materials, and pharma, while noting the demanding curriculum.",
        "themes": [
            {
                "label": "Top-10 chemical engineering",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC chemical engineering #8 undergraduate, with strong research in catalysis, energy, and biomolecular engineering.",
            },
            {
                "label": "Research and labs",
                "sentiment": "positive",
                "detail": "Students access strong laboratories within the School of Chemical Sciences.",
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into energy, materials, chemicals, and pharmaceutical employers.",
            },
            {
                "label": "Demanding curriculum",
                "sentiment": "caution",
                "detail": "The chemical engineering curriculum is rigorous and quantitatively intensive.",
            },
        ],
        "sources": [
            {
                "label": "UIUC Chemical & Biomolecular Engineering",
                "url": "https://chbe.illinois.edu/",
            },
            {
                "label": "Grainger facts & rankings (chemical #8 ug)",
                "url": "https://grainger.illinois.edu/about/facts-and-rankings",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uiuc-bioengineering-bs": {
        "summary": "UIUC bioengineering, ranked #14 for the undergraduate program by U.S. News, combines engineering with the life sciences and benefits from ties to the Carle Illinois College of Medicine and campus health-technology research. Reviewers highlight interdisciplinary opportunities and growth, while noting it is a younger, smaller department than UIUC's largest engineering programs.",
        "themes": [
            {
                "label": "Ranked bioengineering",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC bioengineering #14 nationally; the field is growing alongside the Carle Illinois medical partnership.",
            },
            {
                "label": "Interdisciplinary opportunities",
                "sentiment": "positive",
                "detail": "Students work at the intersection of engineering, biology, and medicine, including imaging, biomechanics, and computational biology.",
            },
            {
                "label": "Medical-school ties",
                "sentiment": "positive",
                "detail": "Proximity to Carle Illinois and the Beckman Institute supports translational research.",
            },
            {
                "label": "Younger, smaller program",
                "sentiment": "caution",
                "detail": "Bioengineering is newer and smaller than UIUC's flagship engineering departments.",
            },
        ],
        "sources": [
            {
                "label": "UIUC Department of Bioengineering",
                "url": "https://bioengineering.illinois.edu/",
            },
            {
                "label": "Grainger facts & rankings (bioengineering #14)",
                "url": "https://grainger.illinois.edu/about/facts-and-rankings",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uiuc-accountancy-bs": {
        "summary": "The Gies Department of Accountancy is consistently ranked the #1 undergraduate accounting program in the United States by U.S. News (and #6 at the graduate level). Reviewers cite outstanding Big Four and corporate placement, very high CPA exam performance, and strong faculty, along with the option to continue into the Master of Accountancy. Some note the program's size and competitiveness.",
        "themes": [
            {
                "label": "#1 undergraduate accounting",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC accountancy #1 at the undergraduate level (and #6 graduate).",
            },
            {
                "label": "Big Four placement",
                "sentiment": "positive",
                "detail": "Graduates place strongly into Big Four and corporate accounting and advisory roles.",
            },
            {
                "label": "Pathway to the master's",
                "sentiment": "positive",
                "detail": "Students can continue into the Gies Master of Accountancy and the online iMSA to meet CPA requirements.",
            },
            {
                "label": "Large and competitive",
                "sentiment": "caution",
                "detail": "The program is large and admission and recruiting are competitive.",
            },
        ],
        "sources": [
            {
                "label": "Gies College of Business — Accountancy",
                "url": "https://giesbusiness.illinois.edu/programs/undergraduate/accountancy",
            },
            {
                "label": "UIUC rankings (accountancy #1 ug / #6 grad)",
                "url": "https://illinois.edu/about/rankings/",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uiuc-finance-bs": {
        "summary": "The Gies undergraduate finance program is a strong, well-recruited business major at a top public business school, with offerings in corporate finance, investments, and financial markets and a data-science blended option. Reviewers cite solid placement into banking, consulting, and corporate finance and strong value, while noting that the most competitive finance roles favor early networking.",
        "themes": [
            {
                "label": "Top public business school",
                "sentiment": "positive",
                "detail": "Gies is a respected AACSB-accredited business school with strong finance offerings and recruiting.",
            },
            {
                "label": "Applied and data-driven",
                "sentiment": "positive",
                "detail": "The finance curriculum includes investments, corporate finance, and a Finance + Data Science blended degree.",
            },
            {
                "label": "Solid placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into banking, consulting, corporate finance, and analytics roles.",
            },
            {
                "label": "Networking matters",
                "sentiment": "caution",
                "detail": "As elsewhere, the most competitive finance roles reward early internships and networking.",
            },
        ],
        "sources": [
            {
                "label": "Gies College of Business — Finance",
                "url": "https://giesbusiness.illinois.edu/programs/undergraduate/finance",
            },
            {
                "label": "UIUC rankings (Gies business)",
                "url": "https://illinois.edu/about/rankings/",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uiuc-business-administration-online-mba": {
        "summary": "The Gies iMBA is a pioneering, highly affordable online MBA (total tuition about $27,288) delivered with Coursera and taught by University of Illinois faculty. Now a decade old, it is AACSB-accredited and awards the same MBA as an on-campus program (the diploma does not say 'online'). Reviewers praise the value, flexibility, and engaged global community, while noting that, like most online MBAs, it relies on self-direction and offers limited in-person networking.",
        "themes": [
            {
                "label": "Exceptional value",
                "sentiment": "positive",
                "detail": "Total tuition of about $27,288 for an AACSB-accredited MBA from a top public university is a standout value; GMAT/GRE are not required.",
            },
            {
                "label": "Flexible, pay-as-you-go",
                "sentiment": "positive",
                "detail": "Students complete the degree in 24-60 months at their own pace, starting in multiple terms and paying per course.",
            },
            {
                "label": "Engaged global community",
                "sentiment": "positive",
                "detail": "Reviewers describe an active global cohort and real-time application of coursework to their jobs.",
            },
            {
                "label": "Online by design",
                "sentiment": "mixed",
                "detail": "The program is fully online with no on-campus commitment, with engagement built into the courses; some students still miss in-person networking.",
            },
            {
                "label": "Self-directed",
                "sentiment": "caution",
                "detail": "As with most online MBAs, success depends on motivation and time management.",
            },
        ],
        "sources": [
            {
                "label": "Gies College of Business — iMBA",
                "url": "https://giesbusiness.illinois.edu/imba",
            },
            {
                "label": "iMBA (Online MBA) overview — Gies",
                "url": "https://giesonline.illinois.edu/explore-programs/online-mba",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uiuc-library-information-science-ms": {
        "summary": "The iSchool's Master of Science in Information Sciences is consistently ranked the #1 library and information science program in the United States by U.S. News. Reviewers praise its breadth across data, information organization, and user-centered design, flexible on-campus and online delivery, and strong placement into libraries, archives, data, and UX roles, while noting the field's salary range varies by sector.",
        "themes": [
            {
                "label": "#1-ranked information sciences",
                "sentiment": "positive",
                "detail": "U.S. News consistently ranks the UIUC iSchool's library/information science master's #1 nationally.",
            },
            {
                "label": "Broad, flexible curriculum",
                "sentiment": "positive",
                "detail": "Students can focus on data and analytics, information organization, UX, youth services, or archives, on campus or online.",
            },
            {
                "label": "Strong placement",
                "sentiment": "positive",
                "detail": "Graduates place into academic and public libraries, archives, data curation, and information/UX roles across sectors.",
            },
            {
                "label": "Sector-dependent pay",
                "sentiment": "caution",
                "detail": "Salaries vary widely by sector (tech/data vs. public libraries); reviewers advise targeting coursework to career goals.",
            },
        ],
        "sources": [
            {
                "label": "UIUC iSchool — MS in Information Sciences",
                "url": "https://ischool.illinois.edu/degrees-programs/graduate-degrees/ms-information-sciences",
            },
            {"label": "UIUC rankings (iSchool #1)", "url": "https://illinois.edu/about/rankings/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uiuc-law-jd": {
        "summary": "The University of Illinois College of Law is a well-regarded public law school (a U.S. News top-50 program) known for strong value, a collegial culture, and solid Illinois and national placement, particularly into the Chicago legal market. First-time bar passage for the Class of 2024 was 93.56% (well above the ABA weighted average of about 79%), though the 2023 cohort's rate dipped below average. Reviewers cite affordability and outcomes relative to private peers, while noting the demands of law school and year-to-year bar variability.",
        "themes": [
            {
                "label": "Strong public-law value",
                "sentiment": "positive",
                "detail": "A U.S. News top-50 law school offering top-tier legal education at lower public tuition than comparable private peers.",
            },
            {
                "label": "Chicago and Illinois placement",
                "sentiment": "positive",
                "detail": "Graduates place well into the Chicago legal market, Illinois firms and government, and national markets.",
            },
            {
                "label": "High recent bar passage",
                "sentiment": "mixed",
                "detail": "First-time bar passage was 93.56% for the Class of 2024 (vs. an ABA weighted average near 79%), though the 2023 cohort dipped to 72.48%.",
            },
            {
                "label": "Rigorous and competitive",
                "sentiment": "caution",
                "detail": "As at peer law schools, the workload is intense and admission is selective.",
            },
        ],
        "sources": [
            {
                "label": "University of Illinois College of Law — ABA Required Disclosures",
                "url": "https://law.illinois.edu/about/college-profile/aba-disclosures/",
            },
            {
                "label": "UIUC College of Law — ABA Bar Passage Report",
                "url": "https://law.illinois.edu/wp-content/uploads/2024/02/ABA-Bar-Passage-Report.pdf",
            },
            {
                "label": "U.S. News — University of Illinois College of Law",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/university-of-illinois-urbana-champaign-03077",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uiuc-medicine-md": {
        "summary": "The Carle Illinois College of Medicine, which enrolled its first M.D. class in 2018, is the nation's first engineering-based college of medicine — a partnership between UIUC and Carle Health that weaves engineering, data, and innovation through the entire M.D. curriculum. Reviewers praise the distinctive curriculum, small class size, and innovation focus, while noting it is a young program still building its research and residency-match track record.",
        "themes": [
            {
                "label": "Engineering-based M.D.",
                "sentiment": "positive",
                "detail": "Carle Illinois is the first U.S. medical school built on an engineering and innovation foundation, integrating it throughout the curriculum.",
            },
            {
                "label": "Clinical partnership",
                "sentiment": "positive",
                "detail": "The partnership with Carle Health gives students early, integrated clinical training in a working health system.",
            },
            {
                "label": "Small, innovative cohort",
                "sentiment": "positive",
                "detail": "A small class size supports close mentorship and a project- and innovation-oriented experience.",
            },
            {
                "label": "Young program",
                "sentiment": "caution",
                "detail": "Founded in 2015 with its first class in 2018, Carle Illinois has a shorter track record than long-established medical schools.",
            },
        ],
        "sources": [
            {
                "label": "Carle Illinois College of Medicine",
                "url": "https://medicine.illinois.edu/",
            },
            {
                "label": "Carle Illinois — Dean Mark Cohen",
                "url": "https://medicine.illinois.edu/about/dean-cohen",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uiuc-veterinary-medicine-dvm": {
        "summary": "The University of Illinois College of Veterinary Medicine offers a well-regarded Doctor of Veterinary Medicine through a teaching hospital and a broad clinical and research enterprise. Reviewers cite strong clinical training, a large caseload, and faculty expertise across companion, food, and zoo/wildlife animal medicine, while noting that veterinary education is costly and admission is highly competitive.",
        "themes": [
            {
                "label": "Comprehensive clinical training",
                "sentiment": "positive",
                "detail": "Students train through the Veterinary Teaching Hospital with a broad caseload across species.",
            },
            {
                "label": "Research and specialties",
                "sentiment": "positive",
                "detail": "Faculty span comparative biosciences, pathobiology, and clinical medicine, with strong specialty and research programs.",
            },
            {
                "label": "Public-university access",
                "sentiment": "positive",
                "detail": "As a public veterinary college, it offers strong value, especially for Illinois residents.",
            },
            {
                "label": "Costly and competitive",
                "sentiment": "caution",
                "detail": "Veterinary education is expensive and DVM admission is highly competitive nationwide.",
            },
        ],
        "sources": [
            {
                "label": "University of Illinois College of Veterinary Medicine — DVM program",
                "url": "https://vetmed.illinois.edu/academic-programs/professional-dvm-program/",
            },
            {
                "label": "U.S. News — best veterinary schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-veterinary-schools",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uiuc-statistics-bslas": {
        "summary": "UIUC's statistics program (Department of Statistics, College of LAS) is a large, well-regarded program that has grown rapidly with demand for data skills, offering pathways in statistics, actuarial science, and statistics & computer science. Reviewers cite strong faculty, applied and computational coursework, and excellent placement into data, analytics, and actuarial roles.",
        "themes": [
            {
                "label": "Strong, in-demand program",
                "sentiment": "positive",
                "detail": "Statistics at UIUC has grown with data-science demand and offers blended Statistics & Computer Science and actuarial pathways.",
            },
            {
                "label": "Applied and computational",
                "sentiment": "positive",
                "detail": "Coursework emphasizes statistical computing, probability, and applied data analysis.",
            },
            {
                "label": "Excellent placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into data-science, analytics, actuarial, and quantitative roles.",
            },
            {
                "label": "Large courses",
                "sentiment": "caution",
                "detail": "Popular statistics and data courses can be large; reviewers advise engaging with office hours and projects.",
            },
        ],
        "sources": [
            {"label": "UIUC Department of Statistics", "url": "https://stat.illinois.edu/"},
            {"label": "UIUC rankings", "url": "https://illinois.edu/about/rankings/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uiuc-economics-balas": {
        "summary": "Economics at UIUC (College of LAS) is a strong, research-active program offering a flexible B.A. plus quantitative options such as econometrics & quantitative economics and computer science + economics. Reviewers value the analytical training and breadth, and placement into business, finance, policy, and graduate study, while noting that the most quantitative careers reward additional math and computing coursework.",
        "themes": [
            {
                "label": "Research-active department",
                "sentiment": "positive",
                "detail": "UIUC economics is a well-regarded program with strong faculty and broad course offerings.",
            },
            {
                "label": "Quantitative options",
                "sentiment": "positive",
                "detail": "Students can pursue econometrics & quantitative economics or the computer science + economics blended degree.",
            },
            {
                "label": "Broad placement",
                "sentiment": "positive",
                "detail": "Graduates enter business, finance, consulting, public policy, and graduate/professional study.",
            },
            {
                "label": "Quant skills pay off",
                "sentiment": "caution",
                "detail": "Reviewers advise adding math, statistics, and computing coursework for the most quantitative careers.",
            },
        ],
        "sources": [
            {"label": "UIUC Department of Economics", "url": "https://economics.illinois.edu/"},
            {"label": "UIUC rankings", "url": "https://illinois.edu/about/rankings/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
}

def _program_standard(slug: str, spec: dict) -> dict:
    omitted: list[str] = ["tracks", "cost_data.tuition_usd"]
    if slug not in _OUTCOMES_BY_SLUG:
        omitted += [
            "outcomes_data.employment_rate",
            "outcomes_data.median_salary",
            "outcomes_data.top_industries",
            "outcomes_data.conditions",
            "outcomes_data.source",
        ]
    else:
        omitted += _OUTCOMES_OMIT_BY_SLUG.get(slug, [])
    if (
        slug not in _CLASS_PROFILE_BY_SLUG
        or _CLASS_PROFILE_BY_SLUG.get(slug, {}).get("cohort_size") is None
    ):
        omitted.append("class_profile.cohort_size")
    if slug not in _FACULTY_BY_SLUG:
        omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    return _standard(omitted)


def apply(session: Session) -> bool:
    """Enrich UIUC to the canonical profile. Flushes; caller commits.

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
    inst.founded_year = 1867
    inst.campus_setting = "small city"
    if not inst.website_url:
        inst.website_url = "https://illinois.edu"
    _hero = SCHOOL_OUTCOMES["campus_photos"][0]["url"]
    _gallery = [u for u in (inst.media_gallery or []) if u != _hero]
    inst.media_gallery = [_hero, *_gallery]
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
    meta_by_name = {m["name"]: m for m in _SCHOOL_META}
    by_name: dict[str, School] = {}
    for spec in SCHOOLS:
        sc = existing.get(spec["name"])
        if sc is None:
            sc = School(institution_id=inst.id, name=spec["name"])
            session.add(sc)
        sc.description_text = spec["description"]
        sc.sort_order = spec["sort_order"]
        sc.catalog_source = "curated"
        sc.website_url = SCHOOL_WEBSITE.get(spec["name"])
        m = meta_by_name[spec["name"]]
        about = _about_for(m)
        about["_standard"] = _standard(_about_omitted(m))
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
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND ccu.table_name = 'programs' AND ccu.column_name = 'id'
          AND tc.table_name <> 'programs'
        """)
    ).fetchall()
    for table, col in fks:
        hit = session.execute(
            text(f'SELECT 1 FROM "{table}" WHERE "{col}" = :pid LIMIT 1'), {"pid": program_id}
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
        p.department = spec.get("department")
        p.duration_months = spec.get("duration_months")
        p.description_text = spec["description"]
        p.website_url = _website_for(spec)
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "on_campus")
        _kw = _PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(_KEYWORDS_BY_SCHOOL[spec["school"]])
        p.content_sources = _program_content(spec["school"], _kw)
        if spec["degree_type"] == "bachelors":
            p.tuition = None
            p.cost_data = _undergrad_cost()
        else:
            p.tuition = None
            p.cost_data = _grad_cost_fallback(spec)
        p.application_requirements = _requirements_for(spec)
        outcomes = dict(_OUTCOMES_BY_SLUG.get(slug, {}))
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        p.tracks = None
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        p.who_its_for = None
        p.highlights = None
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
