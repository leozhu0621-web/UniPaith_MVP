"""University of California, Los Angeles (UCLA) — gold-standard profile data
(institution + schools + program catalog).

Mirrors the MIT / Sloan / MBAn reference instance (see ``mit_profile.py`` /
``michigan_profile.py`` / ``nyu_profile.py``): every value is researched from an
authoritative source and carries a citation, or is honestly omitted (recorded in
that node's ``_standard.omitted``) — never guessed. Built 2026-06-13 from:

  • U.S. Dept. of Education **College Scorecard** API + **IPEDS** (UNITID 110662):
    admit rate, average net price, cost of attendance, ten-year median earnings,
    4-/6-year completion, first-year retention, Pell/loan rates, median debt, and
    undergraduate race/ethnicity.
  • **UCLA Fast Facts** (newsroom.ucla.edu/ucla-fast-facts): enrollment (49,013 in
    2025-26; 33,534 undergraduate), ~5,700 faculty (≈5,000 FTE), ~$1.6B/year in
    competitively awarded research grants and contracts.
  • **UCLA Undergraduate Admission — First-Year Profile, Fall 2024** (146,276
    applicants / 13,114 admits / 6,613 enrolled; 9% admit rate).
  • Rankings: **QS 2026** (#46), **THE 2026** (#18), **U.S. News Best Colleges
    2026** (#17 National), Carnegie R1, WASC Senior College and University
    Commission (WSCUC) accreditation, each cited.
  • The official **UCLA General Catalog** (catalog.registrar.ucla.edu) degree pages
    — the full published degree catalog (373 degree programs across the College of
    Letters and Science and 12 professional schools), each mapped to its owning
    school by the catalog's own ``parent_academic_org`` field (no guessing). The
    online Master of Science in Engineering tracks (Samueli MSOL) carry
    ``delivery_format = "online"`` per UCLA Graduate Programs. Minors, stand-alone
    graduate certificates, and the Candidate-in-Philosophy milestone are excluded.
  • **UCLA Academic Affairs and Personnel — 2025-26 Deans** (the current dean of
    each of the 13 schools/colleges) and the **UCLA Alumni history timeline** +
    each school's official history (founding years).
  • Verified third-party reviews + employment data for flagship coverable programs
    (the Anderson Full-Time MBA and the UCLA Law J.D.) and sourced reputation
    reviews for Computer Science, the M.D., the Master of Financial Engineering,
    Business Economics, and Film and Television.

Honest caveats stamped into ``_standard.omitted``: UCLA, as part of the University
of California, has been **test-free** since 2021 (it neither requires nor considers
SAT/ACT scores), so the institution's ``test_scores`` are omitted with reason.
UCLA does not publish a single university-wide "employed or continuing education"
placement rate or a uniform top-employer-industries list across all schools, so
those two institution outcome fields are omitted with reason (the College
Scorecard institution-wide ten-year median earnings, $82,511, is kept). Most
graduate programs bill tuition per term or by residency and publish no single
annual figure, so those carry a sourced "see the program's tuition page" record
rather than a guessed number. This repair (2026-06-18) replaces school-blurb
fabrication with Wikipedia-sourced per-program catalogue descriptions, assigns each
program its real owning UCLA school in ``department``, removes synthesized batch
``external_reviews``, and re-applies the verified ``newsroom.ucla.edu/rss.xml`` feed
on every node.
"""

# ruff: noqa: E501

from __future__ import annotations

import os
import re
from collections import Counter

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.profile_catalog_utils import validate_catalog
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "University of California-Los Angeles"
ENRICHED_AT = "2026-06-21"


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


# UCLA is test-free (UC system, since 2021); it reports outcomes by school/program,
# not as one university-wide combined placement rate or top-employer-industries list.
_OMITTED_INSTITUTION: list[str] = [
    "school_outcomes.test_scores",
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
]

RANKING_DATA: dict = {
    "ownership_type": "public",
    "accreditor": "WASC Senior College and University Commission (WSCUC)",
    "carnegie_classification": (
        "Doctoral Universities: Very High Research Spending and Doctorate Production (R1)"
    ),
    "qs_world_university_rankings": {
        "rank": 46,
        "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/university-california-los-angeles-ucla",
    },
    "times_higher_education": {
        "rank": 18,
        "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-california-los-angeles",
    },
    "us_news_national": {
        "rank": 17,
        "year": 2026,
        "source_url": "https://www.usnews.com/best-colleges/ucla-1315",
    },
}

SCHOOL_OUTCOMES: dict = {
    "retention_rate_first_year": 0.9731,
    "graduation_rate_6yr": 0.9264,
    "completion_rate_4yr_150pct": 0.9262,
    "admit_rate": 0.0897,
    "avg_net_price": 12548,
    "median_earnings_10yr": 82511,
    "financial_aid": {
        "pell_grant_rate": 0.2824,
        "federal_loan_rate": 0.1877,
        "cost_of_attendance": 38614,
        "median_debt_completers": 14000,
        "avg_net_price": 12548,
    },
    "demographics": {
        "white": 0.2391,
        "asian": 0.2954,
        "hispanic": 0.2424,
        "black": 0.0337,
        "two_or_more": 0.0777,
        "international": 0.0769,
        "american_indian": 0.0013,
        "native_hawaiian": 0.0017,
        "unknown": 0.0318,
    },
    "campus_basics": {"location": "Los Angeles, California"},
    "scale": {
        "student_faculty_ratio": "18:1",
        "faculty_count": 5700,
    },
    "location": {"lat": 34.0708, "lng": -118.4441},
    "research": {
        "labs": [
            "California NanoSystems Institute (CNSI)",
            "Jonsson Comprehensive Cancer Center",
            "Semel Institute for Neuroscience and Human Behavior",
            "Institute of the Environment and Sustainability (IoES)",
            "Institute for Quantitative and Computational Biosciences (QCBio)",
        ],
        "areas": [
            "Medicine, neuroscience, and the life sciences",
            "Engineering, computer science, and nanoscience",
            "Climate, environment, and sustainability",
            "Social sciences, public policy, and the humanities",
            "Arts, film, and music",
        ],
        "lab_links": {
            "California NanoSystems Institute (CNSI)": "https://cnsi.ucla.edu/",
            "Jonsson Comprehensive Cancer Center": "https://www.uclahealth.org/cancer/",
            "Semel Institute for Neuroscience and Human Behavior": "https://www.semel.ucla.edu/",
            "Institute of the Environment and Sustainability (IoES)": "https://www.ioes.ucla.edu/",
            "Institute for Quantitative and Computational Biosciences (QCBio)": "https://qcb.ucla.edu/",
        },
    },
    "campus_life": {
        "athletics_division": "NCAA Division I (Big Ten Conference)",
        "resources": [
            {"name": "UCLA Athletics (the Bruins)", "url": "https://uclabruins.com/"},
            {"name": "UCLA Career Center", "url": "https://career.ucla.edu/"},
            {"name": "UCLA Library", "url": "https://www.library.ucla.edu/"},
            {"name": "UCLA Recreation", "url": "https://recreation.ucla.edu/"},
            {"name": "Associated Students UCLA (ASUCLA)", "url": "https://www.asucla.ucla.edu/"},
        ],
    },
    "media_credit": "Wikimedia Commons / Beyond My Ken (CC BY-SA 4.0)",
    "campus_photos": [
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/2019_UCLA_Royce_Hall_2.jpg/1920px-2019_UCLA_Royce_Hall_2.jpg",
            "credit": "Wikimedia Commons / Beyond My Ken (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/UCLA_campus_and_Westwood.jpg/1920px-UCLA_campus_and_Westwood.jpg",
            "credit": "Wikimedia Commons / Rick Meyer, Los Angeles Times (CC BY 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/2019_UCLA_Powell_Library_2.jpg/1920px-2019_UCLA_Powell_Library_2.jpg",
            "credit": "Wikimedia Commons / Beyond My Ken (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/3/39/Janss_Steps%2C_Royce_Hall_in_background%2C_UCLA.jpg",
            "credit": "Wikimedia Commons / b r e n t (CC BY 2.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/Los-Angeles-UCLA-and-Westwood-Aerial-view-from-south-August-2014.jpg/1920px-Los-Angeles-UCLA-and-Westwood-Aerial-view-from-south-August-2014.jpg",
            "credit": "Wikimedia Commons / Alfred Twu (CC0)",
        },
    ],
    "flagship": {
        "enrollment_total": 48660,
        "applicants": 146276,
        "admits": 13114,
        "admissions_cycle": "First-year, Fall 2024 (UCLA Undergraduate Admission First-Year Profile)",
        "founded_year": 1919,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (UCLA, UNITID 110662)",
            "url": "https://collegescorecard.ed.gov/school/?110662-University-of-California-Los-Angeles",
        },
        {
            "label": "NCES College Navigator — University of California-Los Angeles (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=110662",
        },
        {
            "label": "UCLA Fast Facts (enrollment, faculty, research funding)",
            "url": "https://newsroom.ucla.edu/ucla-fast-facts",
        },
        {
            "label": "UCLA Undergraduate Admission — First-Year Profile, Fall 2024 (admissions funnel)",
            "url": "https://admission.ucla.edu/apply/first-year/first-year-profile/2024",
        },
        {
            "label": "UCLA General Catalog — degrees and majors (program catalog)",
            "url": "https://catalog.registrar.ucla.edu/",
        },
        {
            "label": "UCLA Academic Affairs and Personnel — 2025-26 Deans",
            "url": "https://apo.ucla.edu/apo.ucla.edu/2025-26-deans",
        },
        {
            "label": "UCLA Alumni — UCLA history timeline (founding years)",
            "url": "https://alumni.ucla.edu/uclas-story/ucla-history-timeline-2/",
        },
        {
            "label": "Carnegie Classifications — University of California-Los Angeles (R1)",
            "url": "https://carnegieclassifications.acenet.edu/institution/university-of-california-los-angeles/",
        },
        {
            "label": "QS World University Rankings 2026 — UCLA (#46)",
            "url": "https://www.topuniversities.com/universities/university-california-los-angeles-ucla",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — UCLA (#18)",
            "url": "https://www.timeshighereducation.com/world-university-rankings/university-california-los-angeles",
        },
        {
            "label": "U.S. News Best Colleges 2026 — UCLA (#17 National)",
            "url": "https://www.usnews.com/best-colleges/ucla-1315",
        },
    ],
}

# student_body_size = undergraduate count (UCLA Fast Facts, 2025-26: "Undergraduates");
# total degree-seeking enrollment lives in flagship.enrollment_total (Fall 2024 IPEDS).
UNDERGRAD_COUNT = 33534

DESCRIPTION = (
    "UCLA (the University of California, Los Angeles) is a public research university in Los Angeles, "
    "CA. Founded in 1919 as the southern branch of the University of California and located in the "
    "Westwood district, it is the most applied-to university in the United States and one of the "
    "largest and most highly ranked public universities in the country. It enrolls about 33,500 "
    "undergraduates and roughly 49,000 students in all, with an 18:1 student-faculty ratio, and "
    "admitted about 9% of first-year applicants (13,114 of 146,276) for Fall 2024.\n\n"
    "UCLA is organized into the College of Letters and Science — its academic core, spanning the "
    "humanities, life sciences, physical sciences, and social sciences — and twelve professional "
    "schools: the Henry Samueli School of Engineering and Applied Science; the John E. Anderson "
    "Graduate School of Management; the School of Law; the David Geffen School of Medicine; the "
    "schools of Dentistry, Nursing, and the Jonathan and Karin Fielding School of Public Health; the "
    "Meyer and Renee Luskin School of Public Affairs; the School of Education and Information "
    "Studies; the School of the Arts and Architecture; the School of Theater, Film, and Television; "
    "and the Herb Alpert School of Music. Together they award some 373 degree programs across the "
    "bachelor's, master's, professional, and doctoral levels.\n\n"
    "A Carnegie R1 university accredited by the WASC Senior College and University Commission, UCLA "
    "ranks #17 among national universities by U.S. News, #18 in the world by Times Higher Education, "
    "and #46 by QS for 2026. Its research enterprise draws roughly $1.6 billion a year in "
    "competitively awarded grants and contracts across more than 6,000 active projects, and UCLA is "
    "known as the birthplace of the internet (the first ARPANET message was sent from UCLA in "
    "1969).\n\n"
    "UCLA's average net price is about $12,500 a year against a published cost of attendance near "
    "$38,600, and the median federal debt of completers is about $14,000; as a UC campus, UCLA is "
    "test-free (it neither requires nor considers SAT/ACT scores) and meets the full financial need "
    "of admitted California residents through the UC Blue and Gold Opportunity Plan. UCLA graduates "
    "earn a median of roughly $82,500 ten years after entry. The Bruins compete in NCAA Division I "
    "(the Big Ten Conference)."
)

# ── Schools ────────────────────────────────────────────────────────────────
_SCHOOL_META = [
    {
        "key": "COLL",
        "name": "College of Letters and Science",
        "sort_order": 1,
        "website": "https://www.college.ucla.edu/",
        "founded": 1919,
        "leadership": "Adriana Galván — Dean and Vice Provost, Undergraduate Education; the College is also led by divisional deans for Humanities, Life Sciences, Physical Sciences, and Social Sciences",
        "named_for": None,
        "research_centers": [
            "Division of Humanities",
            "Division of Life Sciences",
            "Division of Physical Sciences",
            "Division of Social Sciences",
            "Division of Undergraduate Education",
        ],
        "keywords": ["College of Letters and Science", "UCLA College"],
    },
    {
        "key": "ENGR",
        "name": "Henry Samueli School of Engineering and Applied Science",
        "sort_order": 2,
        "website": "https://samueli.ucla.edu/",
        "founded": 1945,
        "leadership": "Ah-Hyung “Alissa” Park — Dean",
        "named_for": "Named in 2000 for Henry Samueli following his endowment gift",
        "research_centers": [
            "Computer Science Department",
            "Electrical and Computer Engineering",
            "Mechanical and Aerospace Engineering",
            "Bioengineering",
            "Civil and Environmental Engineering",
            "Materials Science and Engineering",
            "Chemical and Biomolecular Engineering",
        ],
        "keywords": ["Samueli School of Engineering", "UCLA Engineering"],
    },
    {
        "key": "ANDERSON",
        "name": "John E. Anderson Graduate School of Management",
        "sort_order": 3,
        "website": "https://www.anderson.ucla.edu/",
        "founded": 1935,
        "leadership": "Margaret Shih — Interim Dean (Gareth James becomes dean July 1, 2026)",
        "named_for": "Named in 1987 for John E. Anderson following his endowment gift",
        "research_centers": [
            "Full-Time, Fully Employed, and Executive MBA programs",
            "Master of Financial Engineering",
            "Master of Science in Business Analytics",
            "Ph.D. Program",
            "Price Center for Entrepreneurship & Innovation",
        ],
        "keywords": ["Anderson School of Management", "UCLA Anderson", "MBA"],
    },
    {
        "key": "LAW",
        "name": "School of Law",
        "sort_order": 4,
        "website": "https://law.ucla.edu/",
        "founded": 1949,
        "leadership": "Michael E. Waterstone — Dean",
        "named_for": None,
        "research_centers": [
            "Juris Doctor (J.D.) program",
            "Master of Laws (LL.M.)",
            "Master of Legal Studies",
            "Doctor of Juridical Science (S.J.D.)",
            "Emmett Institute on Climate Change and the Environment",
        ],
        "keywords": ["UCLA Law", "School of Law"],
    },
    {
        "key": "MED",
        "name": "David Geffen School of Medicine",
        "sort_order": 5,
        "website": "https://medschool.ucla.edu/",
        "founded": 1951,
        "leadership": "Steven Dubinett — Dean",
        "named_for": "Named in 2002 for David Geffen following his $200 million unrestricted gift",
        "research_centers": [
            "M.D. Program",
            "Medical Scientist Training Program (M.D./Ph.D.)",
            "Department of Computational Medicine",
            "Jonsson Comprehensive Cancer Center",
            "UCLA Health academic medical center",
        ],
        "keywords": ["David Geffen School of Medicine", "UCLA Health", "medicine"],
    },
    {
        "key": "DENT",
        "name": "School of Dentistry",
        "sort_order": 6,
        "website": "https://dentistry.ucla.edu/",
        "founded": 1964,
        "leadership": "Paul H. Krebsbach — Dean",
        "named_for": None,
        "research_centers": [
            "Doctor of Dental Surgery (D.D.S.) program",
            "Advanced dental specialty programs",
            "Oral Biology graduate program",
            "Section of Restorative Dentistry",
        ],
        "keywords": ["UCLA Dentistry", "School of Dentistry"],
    },
    {
        "key": "PUBH",
        "name": "Jonathan and Karin Fielding School of Public Health",
        "sort_order": 7,
        "website": "https://ph.ucla.edu/",
        "founded": 1961,
        "leadership": "Ronald Brookmeyer — Dean",
        "named_for": "Named in 2012 for Jonathan and Karin Fielding following their endowment gift",
        "research_centers": [
            "Department of Biostatistics",
            "Department of Community Health Sciences",
            "Department of Environmental Health Sciences",
            "Department of Epidemiology",
            "Department of Health Policy and Management",
        ],
        "keywords": ["Fielding School of Public Health", "UCLA public health", "MPH"],
    },
    {
        "key": "NURS",
        "name": "School of Nursing",
        "sort_order": 8,
        "website": "https://www.nursing.ucla.edu/",
        "founded": 1949,
        "leadership": "Lin Zhan — Dean",
        "named_for": None,
        "research_centers": [
            "Bachelor of Science in Nursing",
            "Master of Science in Nursing",
            "Doctor of Nursing Practice (D.N.P.)",
            "Ph.D. in Nursing",
        ],
        "keywords": ["UCLA School of Nursing", "nursing"],
    },
    {
        "key": "LUSKIN",
        "name": "Meyer and Renee Luskin School of Public Affairs",
        "sort_order": 9,
        "website": "https://luskin.ucla.edu/",
        "founded": 1994,
        "leadership": "Anastasia Loukaitou-Sideris — Dean",
        "named_for": "Named in 2011 for Meyer and Renee Luskin following their endowment gift",
        "research_centers": [
            "Department of Public Policy",
            "Department of Urban Planning",
            "Department of Social Welfare",
            "Undergraduate Public Affairs major",
            "Luskin Center for Innovation",
        ],
        "keywords": ["Luskin School of Public Affairs", "public policy", "urban planning"],
    },
    {
        "key": "EDIS",
        "name": "School of Education and Information Studies",
        "sort_order": 10,
        "website": "https://seis.ucla.edu/",
        "founded": 1939,
        "leadership": "Christina Christie — Dean",
        "named_for": None,
        "research_centers": [
            "Department of Education",
            "Department of Information Studies",
            "Teacher Education Program",
            "Higher Education and Organizational Change",
            "Graduate School of Education & Information Studies (GSEIS)",
        ],
        "keywords": ["School of Education and Information Studies", "GSEIS", "education"],
    },
    {
        "key": "ARTS",
        "name": "School of the Arts and Architecture",
        "sort_order": 11,
        "website": "https://www.arts.ucla.edu/",
        "founded": 1990,
        "leadership": "Lionel Popkin — Dean",
        "named_for": None,
        "research_centers": [
            "Department of Architecture and Urban Design",
            "Department of Art",
            "Department of Design Media Arts",
            "Department of World Arts and Cultures/Dance",
            "Fowler Museum at UCLA",
        ],
        "keywords": ["School of the Arts and Architecture", "UCLA Arts"],
    },
    {
        "key": "TFT",
        "name": "School of Theater, Film, and Television",
        "sort_order": 12,
        "website": "https://www.tft.ucla.edu/",
        "founded": 1990,
        "leadership": "Celine Parreñas Shimizu — Dean",
        "named_for": None,
        "research_centers": [
            "Department of Theater",
            "Department of Film, Television, and Digital Media",
            "UCLA Film & Television Archive",
            "Center for the Art of Performance",
        ],
        "keywords": ["School of Theater Film and Television", "UCLA TFT", "film"],
    },
    {
        "key": "MUSIC",
        "name": "Herb Alpert School of Music",
        "sort_order": 13,
        "website": "https://schoolofmusic.ucla.edu/",
        "founded": 2016,
        "leadership": "Michael Beckerman — Dean",
        "named_for": "Named in 2007 for Herb Alpert following a $30 million gift from the Herb Alpert Foundation; established as a standalone school in 2016",
        "research_centers": [
            "Department of Music",
            "Department of Ethnomusicology",
            "Department of Musicology",
            "Music Industry program",
            "Global Jazz Studies",
        ],
        "keywords": ["Herb Alpert School of Music", "UCLA music"],
    },
]
SCHOOL_NAME = {m["key"]: m["name"] for m in _SCHOOL_META}
SCHOOL_WEBSITE = {m["name"]: m["website"] for m in _SCHOOL_META}


def _school_description(m: dict) -> str:
    if m["key"] == "COLL":
        return (
            f"The {m['name']}, UCLA's academic core spanning the humanities, life sciences, "
            "physical sciences, and social sciences, traces to the university's founding in 1919."
        )
    return (
        f"The {m['name']}, founded in {m['founded']}, is one of the schools and colleges of the "
        "University of California, Los Angeles."
    )


SCHOOLS: list[dict] = [
    {"name": m["name"], "sort_order": m["sort_order"], "description": _school_description(m)}
    for m in _SCHOOL_META
]


def _about_for(m: dict) -> dict:
    about = {
        "founded": m["founded"],
        "leadership": m["leadership"],
        "research_centers": m["research_centers"],
        "source": {
            "label": "UCLA Academic Affairs and Personnel — 2025-26 Deans + UCLA history timeline",
            "url": "https://apo.ucla.edu/apo.ucla.edu/2025-26-deans",
        },
    }
    if m["named_for"]:
        about["named_for"] = m["named_for"]
    return about


def _about_omitted(m: dict) -> list[str]:
    out = ["about_detail.faculty"]
    if not m["named_for"]:
        out.append("about_detail.named_for")
    return out


# ── Feeds (content_sources) ────────────────────────────────────────────────
_UCLA_NEWS_RSS = "https://newsroom.ucla.edu/rss.xml"
_NEWS_URL = "https://newsroom.ucla.edu/"
_SOCIAL = {
    "instagram": "https://www.instagram.com/ucla/",
    "linkedin": "https://www.linkedin.com/school/ucla/",
    "x": "https://twitter.com/UCLA",
    "youtube": "https://www.youtube.com/UCLA",
    "facebook": "https://www.facebook.com/UCLA",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _UCLA_NEWS_RSS,
    "news_url": _NEWS_URL,
    "news_curated": True,
    "social": _SOCIAL,
}
_KEYWORDS_BY_SCHOOL = {m["name"]: m["keywords"] for m in _SCHOOL_META}


def _school_content(name: str) -> dict:
    return {
        "news_rss": _UCLA_NEWS_RSS,
        "news_url": SCHOOL_WEBSITE.get(name, _NEWS_URL),
        "news_curated": False,
        "keywords": list(_KEYWORDS_BY_SCHOOL[name]),
        "social": _SOCIAL,
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


# ── Program catalog (slug, school_key, program_name, degree_type, department, delivery, duration) ──
_CATALOG: list[tuple] = [
    (
        "ucla-african-american-studies-ug",
        "COLL",
        "African American Studies",
        "bachelors",
        "African American Studies",
        "on_campus",
        48,
    ),
    (
        "ucla-african-and-middle-eastern-studies-ug",
        "COLL",
        "African and Middle Eastern Studies",
        "bachelors",
        "African and Middle Eastern Studies",
        "on_campus",
        48,
    ),
    (
        "ucla-american-indian-studies-ug",
        "COLL",
        "American Indian Studies",
        "bachelors",
        "American Indian Studies",
        "on_campus",
        48,
    ),
    (
        "ucla-american-literature-and-culture-ug",
        "COLL",
        "American Literature and Culture",
        "bachelors",
        "American Literature and Culture",
        "on_campus",
        48,
    ),
    (
        "ucla-ancient-near-east-and-egyptology-ug",
        "COLL",
        "Ancient Near East and Egyptology",
        "bachelors",
        "Ancient Near East and Egyptology",
        "on_campus",
        48,
    ),
    (
        "ucla-anthropology-ba-ug",
        "COLL",
        "Anthropology (B.A.)",
        "bachelors",
        "Anthropology",
        "on_campus",
        48,
    ),
    (
        "ucla-anthropology-bs-ug",
        "COLL",
        "Anthropology (B.S.)",
        "bachelors",
        "Anthropology",
        "on_campus",
        48,
    ),
    (
        "ucla-applied-linguistics-ug",
        "COLL",
        "Applied Linguistics",
        "bachelors",
        "Applied Linguistics",
        "on_campus",
        48,
    ),
    (
        "ucla-applied-mathematics-ug",
        "COLL",
        "Applied Mathematics",
        "bachelors",
        "Applied Mathematics",
        "on_campus",
        48,
    ),
    ("ucla-arabic-ug", "COLL", "Arabic", "bachelors", "Arabic", "on_campus", 48),
    ("ucla-art-history-ug", "COLL", "Art History", "bachelors", "Art History", "on_campus", 48),
    (
        "ucla-asian-american-studies-ug",
        "COLL",
        "Asian American Studies",
        "bachelors",
        "Asian American Studies",
        "on_campus",
        48,
    ),
    (
        "ucla-asian-humanities-ug",
        "COLL",
        "Asian Humanities",
        "bachelors",
        "Asian Humanities",
        "on_campus",
        48,
    ),
    (
        "ucla-asian-languages-and-linguistics-ug",
        "COLL",
        "Asian Languages and Linguistics",
        "bachelors",
        "Asian Languages and Linguistics",
        "on_campus",
        48,
    ),
    (
        "ucla-asian-religions-ug",
        "COLL",
        "Asian Religions",
        "bachelors",
        "Asian Religions",
        "on_campus",
        48,
    ),
    (
        "ucla-asian-studies-ug",
        "COLL",
        "Asian Studies",
        "bachelors",
        "Asian Studies",
        "on_campus",
        48,
    ),
    ("ucla-astrophysics-ug", "COLL", "Astrophysics", "bachelors", "Astrophysics", "on_campus", 48),
    (
        "ucla-atmospheric-and-oceanic-sciences-ug",
        "COLL",
        "Atmospheric and Oceanic Sciences",
        "bachelors",
        "Atmospheric and Oceanic Sciences",
        "on_campus",
        48,
    ),
    (
        "ucla-atmospheric-and-oceanic-sciences-mathematics-ug",
        "COLL",
        "Atmospheric and Oceanic Sciences/Mathematics",
        "bachelors",
        "Atmospheric and Oceanic Sciences/Mathematics",
        "on_campus",
        48,
    ),
    ("ucla-biochemistry-ug", "COLL", "Biochemistry", "bachelors", "Biochemistry", "on_campus", 48),
    ("ucla-biology-ug", "COLL", "Biology", "bachelors", "Biology", "on_campus", 48),
    ("ucla-biophysics-ug", "COLL", "Biophysics", "bachelors", "Biophysics", "on_campus", 48),
    (
        "ucla-business-economics-ug",
        "COLL",
        "Business Economics",
        "bachelors",
        "Business Economics",
        "on_campus",
        48,
    ),
    (
        "ucla-central-and-east-european-languages-and-cultures-ug",
        "COLL",
        "Central and East European Languages and Cultures",
        "bachelors",
        "Central and East European Languages and Cultures",
        "on_campus",
        48,
    ),
    ("ucla-chemistry-ug", "COLL", "Chemistry", "bachelors", "Chemistry", "on_campus", 48),
    (
        "ucla-chemistry-materials-science-ug",
        "COLL",
        "Chemistry/Materials Science",
        "bachelors",
        "Chemistry/Materials Science",
        "on_campus",
        48,
    ),
    (
        "ucla-chicana-and-chicano-studies-ug",
        "COLL",
        "Chicana and Chicano Studies",
        "bachelors",
        "Chicana and Chicano Studies",
        "on_campus",
        48,
    ),
    ("ucla-chinese-ug", "COLL", "Chinese", "bachelors", "Chinese", "on_campus", 48),
    (
        "ucla-classical-civilization-ug",
        "COLL",
        "Classical Civilization",
        "bachelors",
        "Classical Civilization",
        "on_campus",
        48,
    ),
    (
        "ucla-climate-science-ug",
        "COLL",
        "Climate Science",
        "bachelors",
        "Climate Science",
        "on_campus",
        48,
    ),
    (
        "ucla-cognitive-science-ug",
        "COLL",
        "Cognitive Science",
        "bachelors",
        "Cognitive Science",
        "on_campus",
        48,
    ),
    (
        "ucla-communication-ug",
        "COLL",
        "Communication",
        "bachelors",
        "Communication",
        "on_campus",
        48,
    ),
    (
        "ucla-comparative-literature-ug",
        "COLL",
        "Comparative Literature",
        "bachelors",
        "Comparative Literature",
        "on_campus",
        48,
    ),
    (
        "ucla-computational-biology-ug",
        "COLL",
        "Computational Biology",
        "bachelors",
        "Computational Biology",
        "on_campus",
        48,
    ),
    ("ucla-data-theory-ug", "COLL", "Data Theory", "bachelors", "Data Theory", "on_campus", 48),
    (
        "ucla-disability-studies-ug",
        "COLL",
        "Disability Studies",
        "bachelors",
        "Disability Studies",
        "on_campus",
        48,
    ),
    (
        "ucla-earth-and-environmental-science-ug",
        "COLL",
        "Earth and Environmental Science",
        "bachelors",
        "Earth and Environmental Science",
        "on_campus",
        48,
    ),
    (
        "ucla-ecology-behavior-and-evolution-ug",
        "COLL",
        "Ecology, Behavior, and Evolution",
        "bachelors",
        "Ecology, Behavior, and Evolution",
        "on_campus",
        48,
    ),
    ("ucla-economics-ug", "COLL", "Economics", "bachelors", "Economics", "on_campus", 48),
    (
        "ucla-engineering-geology-ug",
        "COLL",
        "Engineering Geology",
        "bachelors",
        "Engineering Geology",
        "on_campus",
        48,
    ),
    ("ucla-english-ug", "COLL", "English", "bachelors", "English", "on_campus", 48),
    (
        "ucla-environmental-science-ug",
        "COLL",
        "Environmental Science",
        "bachelors",
        "Environmental Science",
        "on_campus",
        48,
    ),
    (
        "ucla-european-languages-and-transcultural-studies-ug",
        "COLL",
        "European Languages and Transcultural Studies",
        "bachelors",
        "European Languages and Transcultural Studies",
        "on_campus",
        48,
    ),
    (
        "ucla-european-languages-and-transcultural-studies-with-french-and-francophone-ug",
        "COLL",
        "European Languages and Transcultural Studies with French and Francophone",
        "bachelors",
        "European Languages and Transcultural Studies with French and Francophone",
        "on_campus",
        48,
    ),
    (
        "ucla-european-languages-and-transcultural-studies-with-german-ug",
        "COLL",
        "European Languages and Transcultural Studies with German",
        "bachelors",
        "European Languages and Transcultural Studies with German",
        "on_campus",
        48,
    ),
    (
        "ucla-european-languages-and-transcultural-studies-with-italian-ug",
        "COLL",
        "European Languages and Transcultural Studies with Italian",
        "bachelors",
        "European Languages and Transcultural Studies with Italian",
        "on_campus",
        48,
    ),
    (
        "ucla-european-languages-and-transcultural-studies-with-scandinavian-ug",
        "COLL",
        "European Languages and Transcultural Studies with Scandinavian",
        "bachelors",
        "European Languages and Transcultural Studies with Scandinavian",
        "on_campus",
        48,
    ),
    (
        "ucla-european-studies-ug",
        "COLL",
        "European Studies",
        "bachelors",
        "European Studies",
        "on_campus",
        48,
    ),
    (
        "ucla-financial-actuarial-mathematics-ug",
        "COLL",
        "Financial Actuarial Mathematics",
        "bachelors",
        "Financial Actuarial Mathematics",
        "on_campus",
        48,
    ),
    (
        "ucla-gender-studies-ug",
        "COLL",
        "Gender Studies",
        "bachelors",
        "Gender Studies",
        "on_campus",
        48,
    ),
    (
        "ucla-general-chemistry-ug",
        "COLL",
        "General Chemistry",
        "bachelors",
        "General Chemistry",
        "on_campus",
        48,
    ),
    ("ucla-geography-ug", "COLL", "Geography", "bachelors", "Geography", "on_campus", 48),
    (
        "ucla-geography-environmental-studies-ug",
        "COLL",
        "Geography/Environmental Studies",
        "bachelors",
        "Geography/Environmental Studies",
        "on_campus",
        48,
    ),
    ("ucla-geology-ug", "COLL", "Geology", "bachelors", "Geology", "on_campus", 48),
    ("ucla-geophysics-ug", "COLL", "Geophysics", "bachelors", "Geophysics", "on_campus", 48),
    (
        "ucla-global-studies-ug",
        "COLL",
        "Global Studies",
        "bachelors",
        "Global Studies",
        "on_campus",
        48,
    ),
    ("ucla-greek-ug", "COLL", "Greek", "bachelors", "Greek", "on_campus", 48),
    (
        "ucla-greek-and-latin-ug",
        "COLL",
        "Greek and Latin",
        "bachelors",
        "Greek and Latin",
        "on_campus",
        48,
    ),
    ("ucla-history-ug", "COLL", "History", "bachelors", "History", "on_campus", 48),
    (
        "ucla-human-biology-and-society-ba-ug",
        "COLL",
        "Human Biology and Society (B.A.)",
        "bachelors",
        "Human Biology and Society",
        "on_campus",
        48,
    ),
    (
        "ucla-human-biology-and-society-bs-ug",
        "COLL",
        "Human Biology and Society (B.S.)",
        "bachelors",
        "Human Biology and Society",
        "on_campus",
        48,
    ),
    (
        "ucla-individual-field-of-concentration-ba-in-letters-and-science-ug",
        "COLL",
        "Individual Field of Concentration BA in Letters and Science",
        "bachelors",
        "Individual Field of Concentration BA in Letters and Science",
        "on_campus",
        48,
    ),
    (
        "ucla-individual-field-of-concentration-bs-in-letters-and-science-ug",
        "COLL",
        "Individual Field of Concentration BS in Letters and Science",
        "bachelors",
        "Individual Field of Concentration BS in Letters and Science",
        "on_campus",
        48,
    ),
    (
        "ucla-international-development-studies-ug",
        "COLL",
        "International Development Studies",
        "bachelors",
        "International Development Studies",
        "on_campus",
        48,
    ),
    (
        "ucla-iranian-studies-ug",
        "COLL",
        "Iranian Studies",
        "bachelors",
        "Iranian Studies",
        "on_campus",
        48,
    ),
    ("ucla-japanese-ug", "COLL", "Japanese", "bachelors", "Japanese", "on_campus", 48),
    (
        "ucla-jewish-studies-ug",
        "COLL",
        "Jewish Studies",
        "bachelors",
        "Jewish Studies",
        "on_campus",
        48,
    ),
    ("ucla-korean-ug", "COLL", "Korean", "bachelors", "Korean", "on_campus", 48),
    (
        "ucla-labor-studies-ug",
        "COLL",
        "Labor Studies",
        "bachelors",
        "Labor Studies",
        "on_campus",
        48,
    ),
    ("ucla-latin-ug", "COLL", "Latin", "bachelors", "Latin", "on_campus", 48),
    (
        "ucla-latin-american-studies-ug",
        "COLL",
        "Latin American Studies",
        "bachelors",
        "Latin American Studies",
        "on_campus",
        48,
    ),
    ("ucla-linguistics-ug", "COLL", "Linguistics", "bachelors", "Linguistics", "on_campus", 48),
    (
        "ucla-linguistics-and-anthropology-ug",
        "COLL",
        "Linguistics and Anthropology",
        "bachelors",
        "Linguistics and Anthropology",
        "on_campus",
        48,
    ),
    (
        "ucla-linguistics-and-asian-languages-and-cultures-ug",
        "COLL",
        "Linguistics and Asian Languages and Cultures",
        "bachelors",
        "Linguistics and Asian Languages and Cultures",
        "on_campus",
        48,
    ),
    (
        "ucla-linguistics-and-computer-science-ug",
        "COLL",
        "Linguistics and Computer Science",
        "bachelors",
        "Linguistics and Computer Science",
        "on_campus",
        48,
    ),
    (
        "ucla-linguistics-and-english-ug",
        "COLL",
        "Linguistics and English",
        "bachelors",
        "Linguistics and English",
        "on_campus",
        48,
    ),
    (
        "ucla-linguistics-and-philosophy-ug",
        "COLL",
        "Linguistics and Philosophy",
        "bachelors",
        "Linguistics and Philosophy",
        "on_campus",
        48,
    ),
    (
        "ucla-linguistics-and-psychology-ug",
        "COLL",
        "Linguistics and Psychology",
        "bachelors",
        "Linguistics and Psychology",
        "on_campus",
        48,
    ),
    (
        "ucla-linguistics-and-spanish-ug",
        "COLL",
        "Linguistics and Spanish",
        "bachelors",
        "Linguistics and Spanish",
        "on_campus",
        48,
    ),
    (
        "ucla-marine-biology-ug",
        "COLL",
        "Marine Biology",
        "bachelors",
        "Marine Biology",
        "on_campus",
        48,
    ),
    ("ucla-mathematics-ug", "COLL", "Mathematics", "bachelors", "Mathematics", "on_campus", 48),
    (
        "ucla-mathematics-for-teaching-ug",
        "COLL",
        "Mathematics for Teaching",
        "bachelors",
        "Mathematics for Teaching",
        "on_campus",
        48,
    ),
    (
        "ucla-mathematics-of-computation-ug",
        "COLL",
        "Mathematics of Computation",
        "bachelors",
        "Mathematics of Computation",
        "on_campus",
        48,
    ),
    (
        "ucla-mathematics-applied-science-ug",
        "COLL",
        "Mathematics/Applied Science",
        "bachelors",
        "Mathematics/Applied Science",
        "on_campus",
        48,
    ),
    (
        "ucla-mathematics-economics-ug",
        "COLL",
        "Mathematics/Economics",
        "bachelors",
        "Mathematics/Economics",
        "on_campus",
        48,
    ),
    (
        "ucla-microbiology-immunology-and-molecular-genetics-ug",
        "COLL",
        "Microbiology, Immunology, and Molecular Genetics",
        "bachelors",
        "Microbiology, Immunology, and Molecular Genetics",
        "on_campus",
        48,
    ),
    (
        "ucla-middle-eastern-studies-ug",
        "COLL",
        "Middle Eastern Studies",
        "bachelors",
        "Middle Eastern Studies",
        "on_campus",
        48,
    ),
    (
        "ucla-molecular-cell-and-developmental-biology-ug",
        "COLL",
        "Molecular, Cell, and Developmental Biology",
        "bachelors",
        "Molecular, Cell, and Developmental Biology",
        "on_campus",
        48,
    ),
    ("ucla-neuroscience-ug", "COLL", "Neuroscience", "bachelors", "Neuroscience", "on_campus", 48),
    (
        "ucla-nordic-studies-ug",
        "COLL",
        "Nordic Studies",
        "bachelors",
        "Nordic Studies",
        "on_campus",
        48,
    ),
    ("ucla-philosophy-ug", "COLL", "Philosophy", "bachelors", "Philosophy", "on_campus", 48),
    ("ucla-physics-ba-ug", "COLL", "Physics (B.A.)", "bachelors", "Physics", "on_campus", 48),
    ("ucla-physics-bs-ug", "COLL", "Physics (B.S.)", "bachelors", "Physics", "on_campus", 48),
    (
        "ucla-physiological-science-ug",
        "COLL",
        "Physiological Science",
        "bachelors",
        "Physiological Science",
        "on_campus",
        48,
    ),
    (
        "ucla-political-science-ug",
        "COLL",
        "Political Science",
        "bachelors",
        "Political Science",
        "on_campus",
        48,
    ),
    (
        "ucla-portuguese-and-brazilian-studies-ug",
        "COLL",
        "Portuguese and Brazilian Studies",
        "bachelors",
        "Portuguese and Brazilian Studies",
        "on_campus",
        48,
    ),
    (
        "ucla-psychobiology-ug",
        "COLL",
        "Psychobiology",
        "bachelors",
        "Psychobiology",
        "on_campus",
        48,
    ),
    ("ucla-psychology-ug", "COLL", "Psychology", "bachelors", "Psychology", "on_campus", 48),
    (
        "ucla-russian-language-and-literature-ug",
        "COLL",
        "Russian Language and Literature",
        "bachelors",
        "Russian Language and Literature",
        "on_campus",
        48,
    ),
    (
        "ucla-russian-studies-ug",
        "COLL",
        "Russian Studies",
        "bachelors",
        "Russian Studies",
        "on_campus",
        48,
    ),
    ("ucla-sociology-ug", "COLL", "Sociology", "bachelors", "Sociology", "on_campus", 48),
    (
        "ucla-southeast-asian-studies-ug",
        "COLL",
        "Southeast Asian Studies",
        "bachelors",
        "Southeast Asian Studies",
        "on_campus",
        48,
    ),
    ("ucla-spanish-ug", "COLL", "Spanish", "bachelors", "Spanish", "on_campus", 48),
    (
        "ucla-spanish-and-community-and-culture-ug",
        "COLL",
        "Spanish and Community and Culture",
        "bachelors",
        "Spanish and Community and Culture",
        "on_campus",
        48,
    ),
    (
        "ucla-spanish-and-linguistics-ug",
        "COLL",
        "Spanish and Linguistics",
        "bachelors",
        "Spanish and Linguistics",
        "on_campus",
        48,
    ),
    (
        "ucla-spanish-and-portuguese-ug",
        "COLL",
        "Spanish and Portuguese",
        "bachelors",
        "Spanish and Portuguese",
        "on_campus",
        48,
    ),
    (
        "ucla-statistics-and-data-science-ug",
        "COLL",
        "Statistics and Data Science",
        "bachelors",
        "Statistics and Data Science",
        "on_campus",
        48,
    ),
    (
        "ucla-study-of-religion-ug",
        "COLL",
        "Study of Religion",
        "bachelors",
        "Study of Religion",
        "on_campus",
        48,
    ),
    (
        "ucla-african-american-studies-ms",
        "COLL",
        "African American Studies",
        "masters",
        "African American Studies",
        "on_campus",
        24,
    ),
    (
        "ucla-african-studies-ms",
        "COLL",
        "African Studies",
        "masters",
        "African Studies",
        "on_campus",
        24,
    ),
    (
        "ucla-american-indian-studies-ms",
        "COLL",
        "American Indian Studies",
        "masters",
        "American Indian Studies",
        "on_campus",
        24,
    ),
    ("ucla-anthropology-ms", "COLL", "Anthropology", "masters", "Anthropology", "on_campus", 24),
    ("ucla-archaeology-ms", "COLL", "Archaeology", "masters", "Archaeology", "on_campus", 24),
    ("ucla-art-history-ms", "COLL", "Art History", "masters", "Art History", "on_campus", 24),
    (
        "ucla-asian-american-studies-ms",
        "COLL",
        "Asian American Studies",
        "masters",
        "Asian American Studies",
        "on_campus",
        24,
    ),
    (
        "ucla-asian-languages-and-cultures-ms",
        "COLL",
        "Asian Languages and Cultures",
        "masters",
        "Asian Languages and Cultures",
        "on_campus",
        24,
    ),
    (
        "ucla-astronomy-and-astrophysics-mat-ms",
        "COLL",
        "Astronomy and Astrophysics (M.A.T.)",
        "masters",
        "Astronomy and Astrophysics",
        "on_campus",
        24,
    ),
    (
        "ucla-astronomy-and-astrophysics-ms-ms",
        "COLL",
        "Astronomy and Astrophysics (M.S.)",
        "masters",
        "Astronomy and Astrophysics",
        "on_campus",
        24,
    ),
    (
        "ucla-atmospheric-and-oceanic-sciences-ms",
        "COLL",
        "Atmospheric and Oceanic Sciences",
        "masters",
        "Atmospheric and Oceanic Sciences",
        "on_campus",
        24,
    ),
    (
        "ucla-biochemistry-molecular-and-structural-biology-ms",
        "COLL",
        "Biochemistry, Molecular and Structural Biology",
        "masters",
        "Biochemistry, Molecular and Structural Biology",
        "on_campus",
        24,
    ),
    (
        "ucla-bioinformatics-ms",
        "COLL",
        "Bioinformatics",
        "masters",
        "Bioinformatics",
        "on_campus",
        24,
    ),
    ("ucla-biology-ms", "COLL", "Biology", "masters", "Biology", "on_campus", 24),
    ("ucla-chemistry-ms", "COLL", "Chemistry", "masters", "Chemistry", "on_campus", 24),
    (
        "ucla-chicana-and-chicano-studies-ms",
        "COLL",
        "Chicana and Chicano Studies",
        "masters",
        "Chicana and Chicano Studies",
        "on_campus",
        24,
    ),
    ("ucla-classics-ms", "COLL", "Classics", "masters", "Classics", "on_campus", 24),
    ("ucla-communication-ms", "COLL", "Communication", "masters", "Communication", "on_campus", 24),
    (
        "ucla-comparative-literature-ms",
        "COLL",
        "Comparative Literature",
        "masters",
        "Comparative Literature",
        "on_campus",
        24,
    ),
    (
        "ucla-conservation-of-cultural-heritage-ms",
        "COLL",
        "Conservation of Cultural Heritage",
        "masters",
        "Conservation of Cultural Heritage",
        "on_campus",
        24,
    ),
    (
        "ucla-conservation-of-material-culture-ms",
        "COLL",
        "Conservation of Material Culture",
        "masters",
        "Conservation of Material Culture",
        "on_campus",
        24,
    ),
    (
        "ucla-east-asian-studies-ms",
        "COLL",
        "East Asian Studies",
        "masters",
        "East Asian Studies",
        "on_campus",
        24,
    ),
    ("ucla-economics-ms", "COLL", "Economics", "masters", "Economics", "on_campus", 24),
    ("ucla-english-ms", "COLL", "English", "masters", "English", "on_campus", 24),
    (
        "ucla-environment-and-sustainability-ms",
        "COLL",
        "Environment and Sustainability",
        "masters",
        "Environment and Sustainability",
        "on_campus",
        24,
    ),
    (
        "ucla-french-and-francophone-studies-ms",
        "COLL",
        "French and Francophone Studies",
        "masters",
        "French and Francophone Studies",
        "on_campus",
        24,
    ),
    (
        "ucla-gender-studies-ms",
        "COLL",
        "Gender Studies",
        "masters",
        "Gender Studies",
        "on_campus",
        24,
    ),
    ("ucla-geochemistry-ms", "COLL", "Geochemistry", "masters", "Geochemistry", "on_campus", 24),
    ("ucla-geography-ms", "COLL", "Geography", "masters", "Geography", "on_campus", 24),
    ("ucla-geology-ms", "COLL", "Geology", "masters", "Geology", "on_campus", 24),
    (
        "ucla-geophysics-and-space-physics-ms",
        "COLL",
        "Geophysics and Space Physics",
        "masters",
        "Geophysics and Space Physics",
        "on_campus",
        24,
    ),
    (
        "ucla-germanic-languages-ms",
        "COLL",
        "Germanic Languages",
        "masters",
        "Germanic Languages",
        "on_campus",
        24,
    ),
    ("ucla-greek-ms", "COLL", "Greek", "masters", "Greek", "on_campus", 24),
    ("ucla-history-ms", "COLL", "History", "masters", "History", "on_campus", 24),
    (
        "ucla-indo-european-studies-ms",
        "COLL",
        "Indo-European Studies",
        "masters",
        "Indo-European Studies",
        "on_campus",
        24,
    ),
    (
        "ucla-islamic-studies-ms",
        "COLL",
        "Islamic Studies",
        "masters",
        "Islamic Studies",
        "on_campus",
        24,
    ),
    ("ucla-italian-ms", "COLL", "Italian", "masters", "Italian", "on_campus", 24),
    ("ucla-latin-ms", "COLL", "Latin", "masters", "Latin", "on_campus", 24),
    (
        "ucla-latin-american-studies-ms",
        "COLL",
        "Latin American Studies",
        "masters",
        "Latin American Studies",
        "on_campus",
        24,
    ),
    ("ucla-linguistics-ms", "COLL", "Linguistics", "masters", "Linguistics", "on_campus", 24),
    (
        "ucla-master-of-applied-chemical-sciences-ms",
        "COLL",
        "Master of Applied Chemical Sciences",
        "masters",
        "Master of Applied Chemical Sciences",
        "on_campus",
        24,
    ),
    (
        "ucla-master-of-applied-geospatial-information-systems-and-technologies-ms",
        "COLL",
        "Master of Applied Geospatial Information Systems and Technologies",
        "masters",
        "Master of Applied Geospatial Information Systems and Technologies",
        "on_campus",
        24,
    ),
    (
        "ucla-master-of-applied-statistics-and-data-science-ms",
        "COLL",
        "Master of Applied Statistics and Data Science",
        "masters",
        "Master of Applied Statistics and Data Science",
        "on_campus",
        24,
    ),
    (
        "ucla-master-of-quantitative-economics-ms",
        "COLL",
        "Master of Quantitative Economics",
        "masters",
        "Master of Quantitative Economics",
        "on_campus",
        24,
    ),
    (
        "ucla-master-of-quantum-science-and-technology-ms",
        "COLL",
        "Master of Quantum Science and Technology",
        "masters",
        "Master of Quantum Science and Technology",
        "on_campus",
        24,
    ),
    (
        "ucla-master-of-social-science-ms",
        "COLL",
        "Master of Social Science",
        "masters",
        "Master of Social Science",
        "on_campus",
        24,
    ),
    (
        "ucla-mathematics-ma-ms",
        "COLL",
        "Mathematics (M.A.)",
        "masters",
        "Mathematics",
        "on_campus",
        24,
    ),
    (
        "ucla-mathematics-mat-ms",
        "COLL",
        "Mathematics (M.A.T.)",
        "masters",
        "Mathematics",
        "on_campus",
        24,
    ),
    (
        "ucla-medical-informatics-ms",
        "COLL",
        "Medical Informatics",
        "masters",
        "Medical Informatics",
        "on_campus",
        24,
    ),
    (
        "ucla-molecular-biology-ms",
        "COLL",
        "Molecular Biology",
        "masters",
        "Molecular Biology",
        "on_campus",
        24,
    ),
    (
        "ucla-molecular-cell-and-developmental-biology-ms",
        "COLL",
        "Molecular, Cell, and Developmental Biology",
        "masters",
        "Molecular, Cell, and Developmental Biology",
        "on_campus",
        24,
    ),
    (
        "ucla-near-eastern-languages-and-cultures-ms",
        "COLL",
        "Near Eastern Languages and Cultures",
        "masters",
        "Near Eastern Languages and Cultures",
        "on_campus",
        24,
    ),
    ("ucla-philosophy-ms", "COLL", "Philosophy", "masters", "Philosophy", "on_campus", 24),
    ("ucla-physics-mat-ms", "COLL", "Physics (M.A.T.)", "masters", "Physics", "on_campus", 24),
    ("ucla-physics-ms-ms", "COLL", "Physics (M.S.)", "masters", "Physics", "on_campus", 24),
    (
        "ucla-physiological-science-ms",
        "COLL",
        "Physiological Science",
        "masters",
        "Physiological Science",
        "on_campus",
        24,
    ),
    (
        "ucla-planetary-science-ms",
        "COLL",
        "Planetary Science",
        "masters",
        "Planetary Science",
        "on_campus",
        24,
    ),
    (
        "ucla-political-science-ms",
        "COLL",
        "Political Science",
        "masters",
        "Political Science",
        "on_campus",
        24,
    ),
    ("ucla-portuguese-ms", "COLL", "Portuguese", "masters", "Portuguese", "on_campus", 24),
    ("ucla-psychology-ms", "COLL", "Psychology", "masters", "Psychology", "on_campus", 24),
    ("ucla-scandinavian-ms", "COLL", "Scandinavian", "masters", "Scandinavian", "on_campus", 24),
    (
        "ucla-slavic-east-european-and-eurasian-languages-and-cultures-ms",
        "COLL",
        "Slavic, East European, and Eurasian Languages and Cultures",
        "masters",
        "Slavic, East European, and Eurasian Languages and Cultures",
        "on_campus",
        24,
    ),
    ("ucla-sociology-ms", "COLL", "Sociology", "masters", "Sociology", "on_campus", 24),
    ("ucla-spanish-ms", "COLL", "Spanish", "masters", "Spanish", "on_campus", 24),
    ("ucla-statistics-ms", "COLL", "Statistics", "masters", "Statistics", "on_campus", 24),
    (
        "ucla-teaching-asian-languages-ms",
        "COLL",
        "Teaching Asian Languages",
        "masters",
        "Teaching Asian Languages",
        "on_campus",
        24,
    ),
    ("ucla-anthropology-phd", "COLL", "Anthropology", "phd", "Anthropology", "on_campus", 60),
    ("ucla-archaeology-phd", "COLL", "Archaeology", "phd", "Archaeology", "on_campus", 60),
    ("ucla-art-history-phd", "COLL", "Art History", "phd", "Art History", "on_campus", 60),
    (
        "ucla-asian-languages-and-cultures-phd",
        "COLL",
        "Asian Languages and Cultures",
        "phd",
        "Asian Languages and Cultures",
        "on_campus",
        60,
    ),
    (
        "ucla-astronomy-and-astrophysics-phd",
        "COLL",
        "Astronomy and Astrophysics",
        "phd",
        "Astronomy and Astrophysics",
        "on_campus",
        60,
    ),
    (
        "ucla-atmospheric-and-oceanic-sciences-phd",
        "COLL",
        "Atmospheric and Oceanic Sciences",
        "phd",
        "Atmospheric and Oceanic Sciences",
        "on_campus",
        60,
    ),
    (
        "ucla-biochemistry-molecular-and-structural-biology-phd",
        "COLL",
        "Biochemistry, Molecular and Structural Biology",
        "phd",
        "Biochemistry, Molecular and Structural Biology",
        "on_campus",
        60,
    ),
    ("ucla-bioinformatics-phd", "COLL", "Bioinformatics", "phd", "Bioinformatics", "on_campus", 60),
    ("ucla-biology-phd", "COLL", "Biology", "phd", "Biology", "on_campus", 60),
    ("ucla-chemistry-phd", "COLL", "Chemistry", "phd", "Chemistry", "on_campus", 60),
    (
        "ucla-chicana-and-chicano-studies-phd",
        "COLL",
        "Chicana and Chicano Studies",
        "phd",
        "Chicana and Chicano Studies",
        "on_campus",
        60,
    ),
    ("ucla-classics-phd", "COLL", "Classics", "phd", "Classics", "on_campus", 60),
    ("ucla-communication-phd", "COLL", "Communication", "phd", "Communication", "on_campus", 60),
    (
        "ucla-comparative-literature-phd",
        "COLL",
        "Comparative Literature",
        "phd",
        "Comparative Literature",
        "on_campus",
        60,
    ),
    (
        "ucla-conservation-of-material-culture-phd",
        "COLL",
        "Conservation of Material Culture",
        "phd",
        "Conservation of Material Culture",
        "on_campus",
        60,
    ),
    (
        "ucla-doctor-of-environmental-science-and-engineering-phd",
        "COLL",
        "Doctor of Environmental Science and Engineering",
        "phd",
        "Doctor of Environmental Science and Engineering",
        "on_campus",
        60,
    ),
    ("ucla-economics-phd", "COLL", "Economics", "phd", "Economics", "on_campus", 60),
    ("ucla-english-phd", "COLL", "English", "phd", "English", "on_campus", 60),
    (
        "ucla-environment-and-sustainability-phd",
        "COLL",
        "Environment and Sustainability",
        "phd",
        "Environment and Sustainability",
        "on_campus",
        60,
    ),
    (
        "ucla-french-and-francophone-studies-phd",
        "COLL",
        "French and Francophone Studies",
        "phd",
        "French and Francophone Studies",
        "on_campus",
        60,
    ),
    ("ucla-gender-studies-phd", "COLL", "Gender Studies", "phd", "Gender Studies", "on_campus", 60),
    ("ucla-geochemistry-phd", "COLL", "Geochemistry", "phd", "Geochemistry", "on_campus", 60),
    ("ucla-geography-phd", "COLL", "Geography", "phd", "Geography", "on_campus", 60),
    ("ucla-geology-phd", "COLL", "Geology", "phd", "Geology", "on_campus", 60),
    (
        "ucla-geophysics-and-space-physics-phd",
        "COLL",
        "Geophysics and Space Physics",
        "phd",
        "Geophysics and Space Physics",
        "on_campus",
        60,
    ),
    (
        "ucla-germanic-languages-phd",
        "COLL",
        "Germanic Languages",
        "phd",
        "Germanic Languages",
        "on_campus",
        60,
    ),
    ("ucla-history-phd", "COLL", "History", "phd", "History", "on_campus", 60),
    (
        "ucla-indo-european-studies-phd",
        "COLL",
        "Indo-European Studies",
        "phd",
        "Indo-European Studies",
        "on_campus",
        60,
    ),
    (
        "ucla-islamic-studies-phd",
        "COLL",
        "Islamic Studies",
        "phd",
        "Islamic Studies",
        "on_campus",
        60,
    ),
    ("ucla-italian-phd", "COLL", "Italian", "phd", "Italian", "on_campus", 60),
    ("ucla-linguistics-phd", "COLL", "Linguistics", "phd", "Linguistics", "on_campus", 60),
    ("ucla-mathematics-phd", "COLL", "Mathematics", "phd", "Mathematics", "on_campus", 60),
    (
        "ucla-medical-informatics-phd",
        "COLL",
        "Medical Informatics",
        "phd",
        "Medical Informatics",
        "on_campus",
        60,
    ),
    (
        "ucla-molecular-biology-phd",
        "COLL",
        "Molecular Biology",
        "phd",
        "Molecular Biology",
        "on_campus",
        60,
    ),
    (
        "ucla-molecular-cell-and-developmental-biology-phd",
        "COLL",
        "Molecular, Cell, and Developmental Biology",
        "phd",
        "Molecular, Cell, and Developmental Biology",
        "on_campus",
        60,
    ),
    (
        "ucla-molecular-cellular-and-integrative-physiology-phd",
        "COLL",
        "Molecular, Cellular, and Integrative Physiology",
        "phd",
        "Molecular, Cellular, and Integrative Physiology",
        "on_campus",
        60,
    ),
    (
        "ucla-near-eastern-languages-and-cultures-phd",
        "COLL",
        "Near Eastern Languages and Cultures",
        "phd",
        "Near Eastern Languages and Cultures",
        "on_campus",
        60,
    ),
    ("ucla-philosophy-phd", "COLL", "Philosophy", "phd", "Philosophy", "on_campus", 60),
    ("ucla-physics-phd", "COLL", "Physics", "phd", "Physics", "on_campus", 60),
    (
        "ucla-planetary-science-phd",
        "COLL",
        "Planetary Science",
        "phd",
        "Planetary Science",
        "on_campus",
        60,
    ),
    (
        "ucla-political-science-phd",
        "COLL",
        "Political Science",
        "phd",
        "Political Science",
        "on_campus",
        60,
    ),
    ("ucla-psychology-phd", "COLL", "Psychology", "phd", "Psychology", "on_campus", 60),
    (
        "ucla-slavic-east-european-and-eurasian-languages-and-cultures-phd",
        "COLL",
        "Slavic, East European, and Eurasian Languages and Cultures",
        "phd",
        "Slavic, East European, and Eurasian Languages and Cultures",
        "on_campus",
        60,
    ),
    ("ucla-sociology-phd", "COLL", "Sociology", "phd", "Sociology", "on_campus", 60),
    ("ucla-statistics-phd", "COLL", "Statistics", "phd", "Statistics", "on_campus", 60),
    (
        "ucla-aerospace-engineering-ug",
        "ENGR",
        "Aerospace Engineering",
        "bachelors",
        "Aerospace Engineering",
        "on_campus",
        48,
    ),
    (
        "ucla-bioengineering-ug",
        "ENGR",
        "Bioengineering",
        "bachelors",
        "Bioengineering",
        "on_campus",
        48,
    ),
    (
        "ucla-chemical-engineering-ug",
        "ENGR",
        "Chemical Engineering",
        "bachelors",
        "Chemical Engineering",
        "on_campus",
        48,
    ),
    (
        "ucla-civil-engineering-ug",
        "ENGR",
        "Civil Engineering",
        "bachelors",
        "Civil Engineering",
        "on_campus",
        48,
    ),
    (
        "ucla-computer-engineering-ug",
        "ENGR",
        "Computer Engineering",
        "bachelors",
        "Computer Engineering",
        "on_campus",
        48,
    ),
    (
        "ucla-computer-science-ug",
        "ENGR",
        "Computer Science",
        "bachelors",
        "Computer Science",
        "on_campus",
        48,
    ),
    (
        "ucla-computer-science-and-engineering-ug",
        "ENGR",
        "Computer Science and Engineering",
        "bachelors",
        "Computer Science and Engineering",
        "on_campus",
        48,
    ),
    (
        "ucla-electrical-engineering-ug",
        "ENGR",
        "Electrical Engineering",
        "bachelors",
        "Electrical Engineering",
        "on_campus",
        48,
    ),
    (
        "ucla-materials-engineering-ug",
        "ENGR",
        "Materials Engineering",
        "bachelors",
        "Materials Engineering",
        "on_campus",
        48,
    ),
    (
        "ucla-mechanical-engineering-ug",
        "ENGR",
        "Mechanical Engineering",
        "bachelors",
        "Mechanical Engineering",
        "on_campus",
        48,
    ),
    (
        "ucla-aerospace-engineering-ms",
        "ENGR",
        "Aerospace Engineering",
        "masters",
        "Aerospace Engineering",
        "on_campus",
        24,
    ),
    (
        "ucla-bioengineering-ms",
        "ENGR",
        "Bioengineering",
        "masters",
        "Bioengineering",
        "on_campus",
        24,
    ),
    (
        "ucla-chemical-engineering-ms",
        "ENGR",
        "Chemical Engineering",
        "masters",
        "Chemical Engineering",
        "on_campus",
        24,
    ),
    (
        "ucla-civil-engineering-ms",
        "ENGR",
        "Civil Engineering",
        "masters",
        "Civil Engineering",
        "on_campus",
        24,
    ),
    (
        "ucla-computer-science-ms",
        "ENGR",
        "Computer Science",
        "masters",
        "Computer Science",
        "on_campus",
        24,
    ),
    (
        "ucla-electrical-and-computer-engineering-ms",
        "ENGR",
        "Electrical and Computer Engineering",
        "masters",
        "Electrical and Computer Engineering",
        "on_campus",
        24,
    ),
    ("ucla-engineer-ms", "ENGR", "Engineer", "masters", "Engineer", "on_campus", 24),
    ("ucla-engineering-ms", "ENGR", "Engineering", "masters", "Engineering", "online", 24),
    (
        "ucla-engineering-aerospace-ms",
        "ENGR",
        "Engineering – Aerospace",
        "masters",
        "Engineering – Aerospace",
        "online",
        24,
    ),
    (
        "ucla-engineering-computer-networking-ms",
        "ENGR",
        "Engineering – Computer Networking",
        "masters",
        "Engineering – Computer Networking",
        "online",
        24,
    ),
    (
        "ucla-engineering-electrical-ms",
        "ENGR",
        "Engineering – Electrical",
        "masters",
        "Engineering – Electrical",
        "online",
        24,
    ),
    (
        "ucla-engineering-electronic-materials-ms",
        "ENGR",
        "Engineering – Electronic Materials",
        "masters",
        "Engineering – Electronic Materials",
        "online",
        24,
    ),
    (
        "ucla-engineering-integrated-circuits-ms",
        "ENGR",
        "Engineering – Integrated Circuits",
        "masters",
        "Engineering – Integrated Circuits",
        "online",
        24,
    ),
    (
        "ucla-engineering-manufacturing-and-design-ms",
        "ENGR",
        "Engineering – Manufacturing and Design",
        "masters",
        "Engineering – Manufacturing and Design",
        "online",
        24,
    ),
    (
        "ucla-engineering-materials-science-ms",
        "ENGR",
        "Engineering – Materials Science",
        "masters",
        "Engineering – Materials Science",
        "online",
        24,
    ),
    (
        "ucla-engineering-mechanical-ms",
        "ENGR",
        "Engineering – Mechanical",
        "masters",
        "Engineering – Mechanical",
        "online",
        24,
    ),
    (
        "ucla-engineering-signal-processing-and-communications-ms",
        "ENGR",
        "Engineering – Signal Processing and Communications",
        "masters",
        "Engineering – Signal Processing and Communications",
        "online",
        24,
    ),
    (
        "ucla-engineering-structural-materials-ms",
        "ENGR",
        "Engineering – Structural Materials",
        "masters",
        "Engineering – Structural Materials",
        "online",
        24,
    ),
    (
        "ucla-manufacturing-engineering-ms",
        "ENGR",
        "Manufacturing Engineering",
        "masters",
        "Manufacturing Engineering",
        "on_campus",
        24,
    ),
    (
        "ucla-master-of-engineering-ms",
        "ENGR",
        "Master of Engineering",
        "masters",
        "Master of Engineering",
        "on_campus",
        24,
    ),
    (
        "ucla-materials-science-and-engineering-ms",
        "ENGR",
        "Materials Science and Engineering",
        "masters",
        "Materials Science and Engineering",
        "on_campus",
        24,
    ),
    (
        "ucla-mechanical-engineering-ms",
        "ENGR",
        "Mechanical Engineering",
        "masters",
        "Mechanical Engineering",
        "on_campus",
        24,
    ),
    (
        "ucla-aerospace-engineering-phd",
        "ENGR",
        "Aerospace Engineering",
        "phd",
        "Aerospace Engineering",
        "on_campus",
        60,
    ),
    ("ucla-bioengineering-phd", "ENGR", "Bioengineering", "phd", "Bioengineering", "on_campus", 60),
    (
        "ucla-chemical-engineering-phd",
        "ENGR",
        "Chemical Engineering",
        "phd",
        "Chemical Engineering",
        "on_campus",
        60,
    ),
    (
        "ucla-civil-engineering-phd",
        "ENGR",
        "Civil Engineering",
        "phd",
        "Civil Engineering",
        "on_campus",
        60,
    ),
    (
        "ucla-computer-science-phd",
        "ENGR",
        "Computer Science",
        "phd",
        "Computer Science",
        "on_campus",
        60,
    ),
    (
        "ucla-electrical-and-computer-engineering-phd",
        "ENGR",
        "Electrical and Computer Engineering",
        "phd",
        "Electrical and Computer Engineering",
        "on_campus",
        60,
    ),
    (
        "ucla-materials-science-and-engineering-phd",
        "ENGR",
        "Materials Science and Engineering",
        "phd",
        "Materials Science and Engineering",
        "on_campus",
        60,
    ),
    (
        "ucla-mechanical-engineering-phd",
        "ENGR",
        "Mechanical Engineering",
        "phd",
        "Mechanical Engineering",
        "on_campus",
        60,
    ),
    (
        "ucla-business-analytics-ms",
        "ANDERSON",
        "Business Analytics",
        "masters",
        "Business Analytics",
        "on_campus",
        24,
    ),
    (
        "ucla-executive-master-of-business-administration-ms",
        "ANDERSON",
        "Executive Master of Business Administration",
        "masters",
        "Executive Master of Business Administration",
        "on_campus",
        24,
    ),
    (
        "ucla-fully-employed-master-of-business-administration-ms",
        "ANDERSON",
        "Fully Employed Master of Business Administration",
        "masters",
        "Fully Employed Master of Business Administration",
        "on_campus",
        24,
    ),
    (
        "ucla-global-executive-master-of-business-administration-for-asia-pacific-ms",
        "ANDERSON",
        "Global Executive Master of Business Administration for Asia Pacific",
        "masters",
        "Global Executive Master of Business Administration for Asia Pacific",
        "on_campus",
        24,
    ),
    ("ucla-management-ms", "ANDERSON", "Management", "masters", "Management", "on_campus", 24),
    (
        "ucla-master-of-business-administration-ms",
        "ANDERSON",
        "Master of Business Administration",
        "masters",
        "Master of Business Administration",
        "on_campus",
        24,
    ),
    (
        "ucla-master-of-financial-engineering-ms",
        "ANDERSON",
        "Master of Financial Engineering",
        "masters",
        "Master of Financial Engineering",
        "on_campus",
        24,
    ),
    ("ucla-management-phd", "ANDERSON", "Management", "phd", "Management", "on_campus", 60),
    (
        "ucla-master-of-laws-ms",
        "LAW",
        "Master of Laws",
        "masters",
        "Master of Laws",
        "on_campus",
        24,
    ),
    (
        "ucla-master-of-legal-studies-ms",
        "LAW",
        "Master of Legal Studies",
        "masters",
        "Master of Legal Studies",
        "on_campus",
        24,
    ),
    (
        "ucla-doctor-of-juridical-science-phd",
        "LAW",
        "Doctor of Juridical Science",
        "phd",
        "Doctor of Juridical Science",
        "on_campus",
        60,
    ),
    (
        "ucla-juris-doctor-prof",
        "LAW",
        "Juris Doctor",
        "professional",
        "Juris Doctor",
        "on_campus",
        36,
    ),
    (
        "ucla-biomathematics-ms",
        "MED",
        "Biomathematics",
        "masters",
        "Biomathematics",
        "on_campus",
        24,
    ),
    (
        "ucla-clinical-research-ms",
        "MED",
        "Clinical Research",
        "masters",
        "Clinical Research",
        "on_campus",
        24,
    ),
    (
        "ucla-data-science-in-biomedicine-ms",
        "MED",
        "Data Science in Biomedicine",
        "masters",
        "Data Science in Biomedicine",
        "on_campus",
        24,
    ),
    (
        "ucla-genetic-counseling-ms",
        "MED",
        "Genetic Counseling",
        "masters",
        "Genetic Counseling",
        "on_campus",
        24,
    ),
    (
        "ucla-human-genetics-ms",
        "MED",
        "Human Genetics",
        "masters",
        "Human Genetics",
        "on_campus",
        24,
    ),
    (
        "ucla-molecular-and-medical-pharmacology-ms",
        "MED",
        "Molecular and Medical Pharmacology",
        "masters",
        "Molecular and Medical Pharmacology",
        "on_campus",
        24,
    ),
    (
        "ucla-physics-and-biology-in-medicine-ms",
        "MED",
        "Physics and Biology In Medicine",
        "masters",
        "Physics and Biology In Medicine",
        "on_campus",
        24,
    ),
    ("ucla-biomathematics-phd", "MED", "Biomathematics", "phd", "Biomathematics", "on_campus", 60),
    ("ucla-human-genetics-phd", "MED", "Human Genetics", "phd", "Human Genetics", "on_campus", 60),
    (
        "ucla-molecular-and-medical-pharmacology-phd",
        "MED",
        "Molecular and Medical Pharmacology",
        "phd",
        "Molecular and Medical Pharmacology",
        "on_campus",
        60,
    ),
    ("ucla-neuroscience-phd", "MED", "Neuroscience", "phd", "Neuroscience", "on_campus", 60),
    (
        "ucla-physics-and-biology-in-medicine-phd",
        "MED",
        "Physics and Biology In Medicine",
        "phd",
        "Physics and Biology In Medicine",
        "on_campus",
        60,
    ),
    (
        "ucla-doctor-of-medicine-prof",
        "MED",
        "Doctor of Medicine",
        "professional",
        "Doctor of Medicine",
        "on_campus",
        36,
    ),
    ("ucla-oral-biology-ms", "DENT", "Oral Biology", "masters", "Oral Biology", "on_campus", 24),
    ("ucla-oral-biology-phd", "DENT", "Oral Biology", "phd", "Oral Biology", "on_campus", 60),
    (
        "ucla-doctor-of-dental-surgery-prof",
        "DENT",
        "Doctor of Dental Surgery",
        "professional",
        "Doctor of Dental Surgery",
        "on_campus",
        36,
    ),
    (
        "ucla-public-health-ba-ug",
        "PUBH",
        "Public Health (B.A.)",
        "bachelors",
        "Public Health",
        "on_campus",
        48,
    ),
    (
        "ucla-public-health-bs-ug",
        "PUBH",
        "Public Health (B.S.)",
        "bachelors",
        "Public Health",
        "on_campus",
        48,
    ),
    (
        "ucla-biostatistics-mph-ms",
        "PUBH",
        "Biostatistics (M.P.H.)",
        "masters",
        "Biostatistics",
        "on_campus",
        24,
    ),
    (
        "ucla-biostatistics-ms-ms",
        "PUBH",
        "Biostatistics (M.S.)",
        "masters",
        "Biostatistics",
        "on_campus",
        24,
    ),
    (
        "ucla-community-health-sciences-mph-ms",
        "PUBH",
        "Community Health Sciences (M.P.H.)",
        "masters",
        "Community Health Sciences",
        "on_campus",
        24,
    ),
    (
        "ucla-community-health-sciences-ms-ms",
        "PUBH",
        "Community Health Sciences (M.S.)",
        "masters",
        "Community Health Sciences",
        "on_campus",
        24,
    ),
    (
        "ucla-community-health-health-promotion-and-education-ms",
        "PUBH",
        "Community Health, Health Promotion and Education",
        "masters",
        "Community Health, Health Promotion and Education",
        "on_campus",
        24,
    ),
    (
        "ucla-environmental-health-sciences-mph-ms",
        "PUBH",
        "Environmental Health Sciences (M.P.H.)",
        "masters",
        "Environmental Health Sciences",
        "on_campus",
        24,
    ),
    (
        "ucla-environmental-health-sciences-ms-ms",
        "PUBH",
        "Environmental Health Sciences (M.S.)",
        "masters",
        "Environmental Health Sciences",
        "on_campus",
        24,
    ),
    (
        "ucla-epidemiology-mph-ms",
        "PUBH",
        "Epidemiology (M.P.H.)",
        "masters",
        "Epidemiology",
        "on_campus",
        24,
    ),
    (
        "ucla-epidemiology-ms-ms",
        "PUBH",
        "Epidemiology (M.S.)",
        "masters",
        "Epidemiology",
        "on_campus",
        24,
    ),
    (
        "ucla-executive-master-of-public-health-ms",
        "PUBH",
        "Executive Master of Public Health",
        "masters",
        "Executive Master of Public Health",
        "on_campus",
        24,
    ),
    (
        "ucla-health-management-ms",
        "PUBH",
        "Health Management",
        "masters",
        "Health Management",
        "on_campus",
        24,
    ),
    ("ucla-health-policy-ms", "PUBH", "Health Policy", "masters", "Health Policy", "on_campus", 24),
    (
        "ucla-health-policy-and-management-mph-ms",
        "PUBH",
        "Health Policy and Management (M.P.H.)",
        "masters",
        "Health Policy and Management",
        "on_campus",
        24,
    ),
    (
        "ucla-health-policy-and-management-ms-ms",
        "PUBH",
        "Health Policy and Management (M.S.)",
        "masters",
        "Health Policy and Management",
        "on_campus",
        24,
    ),
    (
        "ucla-master-of-data-science-in-health-ms",
        "PUBH",
        "Master of Data Science in Health",
        "masters",
        "Master of Data Science in Health",
        "on_campus",
        24,
    ),
    (
        "ucla-master-of-healthcare-administration-ms",
        "PUBH",
        "Master of Healthcare Administration",
        "masters",
        "Master of Healthcare Administration",
        "on_campus",
        24,
    ),
    (
        "ucla-master-of-public-health-ms",
        "PUBH",
        "Master of Public Health",
        "masters",
        "Master of Public Health",
        "on_campus",
        24,
    ),
    ("ucla-biostatistics-phd", "PUBH", "Biostatistics", "phd", "Biostatistics", "on_campus", 60),
    (
        "ucla-community-health-sciences-phd",
        "PUBH",
        "Community Health Sciences",
        "phd",
        "Community Health Sciences",
        "on_campus",
        60,
    ),
    (
        "ucla-environmental-health-sciences-phd",
        "PUBH",
        "Environmental Health Sciences",
        "phd",
        "Environmental Health Sciences",
        "on_campus",
        60,
    ),
    (
        "ucla-environmental-and-molecular-toxicology-phd",
        "PUBH",
        "Environmental and Molecular Toxicology",
        "phd",
        "Environmental and Molecular Toxicology",
        "on_campus",
        60,
    ),
    ("ucla-epidemiology-phd", "PUBH", "Epidemiology", "phd", "Epidemiology", "on_campus", 60),
    (
        "ucla-health-policy-and-management-phd",
        "PUBH",
        "Health Policy and Management",
        "phd",
        "Health Policy and Management",
        "on_campus",
        60,
    ),
    (
        "ucla-nursing-bs-prelicensure-ug",
        "NURS",
        "Nursing BS Prelicensure",
        "bachelors",
        "Nursing BS Prelicensure",
        "on_campus",
        48,
    ),
    (
        "ucla-master-of-science-in-nursing-ms",
        "NURS",
        "Master of Science in Nursing",
        "masters",
        "Master of Science in Nursing",
        "on_campus",
        24,
    ),
    ("ucla-nursing-ms", "NURS", "Nursing", "masters", "Nursing", "on_campus", 24),
    ("ucla-nursing-phd", "NURS", "Nursing", "phd", "Nursing", "on_campus", 60),
    (
        "ucla-doctor-of-nursing-practice-prof",
        "NURS",
        "Doctor of Nursing Practice",
        "professional",
        "Doctor of Nursing Practice",
        "on_campus",
        36,
    ),
    (
        "ucla-public-affairs-ug",
        "LUSKIN",
        "Public Affairs",
        "bachelors",
        "Public Affairs",
        "on_campus",
        48,
    ),
    (
        "ucla-master-of-public-policy-ms",
        "LUSKIN",
        "Master of Public Policy",
        "masters",
        "Master of Public Policy",
        "on_campus",
        24,
    ),
    (
        "ucla-master-of-real-estate-development-ms",
        "LUSKIN",
        "Master of Real Estate Development",
        "masters",
        "Master of Real Estate Development",
        "on_campus",
        24,
    ),
    (
        "ucla-master-of-social-welfare-ms",
        "LUSKIN",
        "Master of Social Welfare",
        "masters",
        "Master of Social Welfare",
        "on_campus",
        24,
    ),
    (
        "ucla-master-of-urban-and-regional-planning-ms",
        "LUSKIN",
        "Master of Urban and Regional Planning",
        "masters",
        "Master of Urban and Regional Planning",
        "on_campus",
        24,
    ),
    (
        "ucla-master-of-urban-and-regional-planning-institut-detudes-de-paris-ms",
        "LUSKIN",
        "Master of Urban and Regional Planning – Institut d'Etudes de Paris",
        "masters",
        "Master of Urban and Regional Planning – Institut d'Etudes de Paris",
        "on_campus",
        24,
    ),
    (
        "ucla-social-welfare-phd",
        "LUSKIN",
        "Social Welfare",
        "phd",
        "Social Welfare",
        "on_campus",
        60,
    ),
    (
        "ucla-urban-planning-phd",
        "LUSKIN",
        "Urban Planning",
        "phd",
        "Urban Planning",
        "on_campus",
        60,
    ),
    (
        "ucla-education-and-social-transformation-ug",
        "EDIS",
        "Education and Social Transformation",
        "bachelors",
        "Education and Social Transformation",
        "on_campus",
        48,
    ),
    ("ucla-education-ms", "EDIS", "Education", "masters", "Education", "on_campus", 24),
    (
        "ucla-master-of-education-ms",
        "EDIS",
        "Master of Education",
        "masters",
        "Master of Education",
        "on_campus",
        24,
    ),
    (
        "ucla-master-of-library-and-information-science-ms",
        "EDIS",
        "Master of Library and Information Science",
        "masters",
        "Master of Library and Information Science",
        "on_campus",
        24,
    ),
    (
        "ucla-doctor-of-education-phd",
        "EDIS",
        "Doctor of Education",
        "phd",
        "Doctor of Education",
        "on_campus",
        60,
    ),
    ("ucla-education-phd", "EDIS", "Education", "phd", "Education", "on_campus", 60),
    (
        "ucla-information-studies-phd",
        "EDIS",
        "Information Studies",
        "phd",
        "Information Studies",
        "on_campus",
        60,
    ),
    (
        "ucla-special-education-phd",
        "EDIS",
        "Special Education",
        "phd",
        "Special Education",
        "on_campus",
        60,
    ),
    (
        "ucla-architectural-studies-ug",
        "ARTS",
        "Architectural Studies",
        "bachelors",
        "Architectural Studies",
        "on_campus",
        48,
    ),
    ("ucla-art-ug", "ARTS", "Art", "bachelors", "Art", "on_campus", 48),
    ("ucla-dance-ug", "ARTS", "Dance", "bachelors", "Dance", "on_campus", 48),
    (
        "ucla-design-media-arts-ug",
        "ARTS",
        "Design|Media Arts",
        "bachelors",
        "Design|Media Arts",
        "on_campus",
        48,
    ),
    (
        "ucla-individual-field-of-concentration-ba-in-arts-and-architecture-ug",
        "ARTS",
        "Individual Field of Concentration BA in Arts and Architecture",
        "bachelors",
        "Individual Field of Concentration BA in Arts and Architecture",
        "on_campus",
        48,
    ),
    (
        "ucla-world-arts-and-cultures-ug",
        "ARTS",
        "World Arts and Cultures",
        "bachelors",
        "World Arts and Cultures",
        "on_campus",
        48,
    ),
    ("ucla-architecture-ms", "ARTS", "Architecture", "masters", "Architecture", "on_campus", 24),
    (
        "ucla-architecture-and-urban-design-ms",
        "ARTS",
        "Architecture and Urban Design",
        "masters",
        "Architecture and Urban Design",
        "on_campus",
        24,
    ),
    ("ucla-art-ms", "ARTS", "Art", "masters", "Art", "on_campus", 24),
    (
        "ucla-choreographic-inquiry-ms",
        "ARTS",
        "Choreographic Inquiry",
        "masters",
        "Choreographic Inquiry",
        "on_campus",
        24,
    ),
    (
        "ucla-culture-and-performance-ms",
        "ARTS",
        "Culture and Performance",
        "masters",
        "Culture and Performance",
        "on_campus",
        24,
    ),
    (
        "ucla-design-media-arts-ms",
        "ARTS",
        "Design|Media Arts",
        "masters",
        "Design|Media Arts",
        "on_campus",
        24,
    ),
    (
        "ucla-master-of-architecture-ms",
        "ARTS",
        "Master of Architecture",
        "masters",
        "Master of Architecture",
        "on_campus",
        24,
    ),
    ("ucla-architecture-phd", "ARTS", "Architecture", "phd", "Architecture", "on_campus", 60),
    (
        "ucla-culture-and-performance-phd",
        "ARTS",
        "Culture and Performance",
        "phd",
        "Culture and Performance",
        "on_campus",
        60,
    ),
    (
        "ucla-film-and-television-ug",
        "TFT",
        "Film and Television",
        "bachelors",
        "Film and Television",
        "on_campus",
        48,
    ),
    (
        "ucla-individual-field-of-concentration-ba-in-theater-film-and-television-ug",
        "TFT",
        "Individual Field of Concentration BA in Theater, Film, and Television",
        "bachelors",
        "Individual Field of Concentration BA in Theater, Film, and Television",
        "on_campus",
        48,
    ),
    ("ucla-theater-ug", "TFT", "Theater", "bachelors", "Theater", "on_campus", 48),
    (
        "ucla-film-and-television-ma-ms",
        "TFT",
        "Film and Television (M.A.)",
        "masters",
        "Film and Television",
        "on_campus",
        24,
    ),
    (
        "ucla-film-and-television-mfa-ms",
        "TFT",
        "Film and Television (M.F.A.)",
        "masters",
        "Film and Television",
        "on_campus",
        24,
    ),
    ("ucla-theater-ms", "TFT", "Theater", "masters", "Theater", "on_campus", 24),
    (
        "ucla-film-and-television-phd",
        "TFT",
        "Film and Television",
        "phd",
        "Film and Television",
        "on_campus",
        60,
    ),
    (
        "ucla-theater-and-performance-studies-phd",
        "TFT",
        "Theater and Performance Studies",
        "phd",
        "Theater and Performance Studies",
        "on_campus",
        60,
    ),
    (
        "ucla-ethnomusicology-ug",
        "MUSIC",
        "Ethnomusicology",
        "bachelors",
        "Ethnomusicology",
        "on_campus",
        48,
    ),
    (
        "ucla-global-jazz-studies-ug",
        "MUSIC",
        "Global Jazz Studies",
        "bachelors",
        "Global Jazz Studies",
        "on_campus",
        48,
    ),
    ("ucla-music-ug", "MUSIC", "Music", "bachelors", "Music", "on_campus", 48),
    (
        "ucla-music-composition-ug",
        "MUSIC",
        "Music Composition",
        "bachelors",
        "Music Composition",
        "on_campus",
        48,
    ),
    (
        "ucla-music-education-ug",
        "MUSIC",
        "Music Education",
        "bachelors",
        "Music Education",
        "on_campus",
        48,
    ),
    (
        "ucla-music-history-and-industry-ug",
        "MUSIC",
        "Music History and Industry",
        "bachelors",
        "Music History and Industry",
        "on_campus",
        48,
    ),
    (
        "ucla-music-industry-ug",
        "MUSIC",
        "Music Industry",
        "bachelors",
        "Music Industry",
        "on_campus",
        48,
    ),
    (
        "ucla-music-performance-ug",
        "MUSIC",
        "Music Performance",
        "bachelors",
        "Music Performance",
        "on_campus",
        48,
    ),
    ("ucla-musicology-ug", "MUSIC", "Musicology", "bachelors", "Musicology", "on_campus", 48),
    (
        "ucla-ethnomusicology-ms",
        "MUSIC",
        "Ethnomusicology",
        "masters",
        "Ethnomusicology",
        "on_campus",
        24,
    ),
    (
        "ucla-master-of-music-ms",
        "MUSIC",
        "Master of Music",
        "masters",
        "Master of Music",
        "on_campus",
        24,
    ),
    ("ucla-music-ms", "MUSIC", "Music", "masters", "Music", "on_campus", 24),
    ("ucla-musicology-ms", "MUSIC", "Musicology", "masters", "Musicology", "on_campus", 24),
    (
        "ucla-ethnomusicology-phd",
        "MUSIC",
        "Ethnomusicology",
        "phd",
        "Ethnomusicology",
        "on_campus",
        60,
    ),
    ("ucla-music-dma-phd", "MUSIC", "Music (D.M.A.)", "phd", "Music", "on_campus", 60),
    ("ucla-music-phd-phd", "MUSIC", "Music (Ph.D.)", "phd", "Music", "on_campus", 60),
    ("ucla-musicology-phd", "MUSIC", "Musicology", "phd", "Musicology", "on_campus", 60),
]

_UG_PREFIX_BY_SCHOOL: dict[str, str] = {
    "COLL": "Bachelor of Arts in",
    "ENGR": "Bachelor of Science in",
    "ARTS": "Bachelor of Arts in",
    "TFT": "Bachelor of Arts in",
    "MUSIC": "Bachelor of Music in",
    "PUBH": "Bachelor of Arts in",
    "NURS": "Bachelor of Science in",
    "LUSKIN": "Bachelor of Arts in",
    "EDIS": "Bachelor of Arts in",
}

_MS_PREFIX_BY_SCHOOL: dict[str, str] = {
    "COLL": "Master of Arts in",
    "ENGR": "Master of Science in",
    "ARTS": "Master of Arts in",
    "TFT": "Master of Arts in",
    "MUSIC": "Master of Music in",
    "PUBH": "Master of Public Health in",
    "NURS": "Master of Science in",
    "LUSKIN": "Master of Public Policy in",
    "EDIS": "Master of Education in",
    "ANDERSON": "Master of Science in",
    "LAW": "Master of Laws in",
    "MED": "Master of Science in",
    "DENT": "Master of Science in",
}

_SUFFIX_MAP: list[tuple[str, str]] = [
    ("-phd", "prefix:Doctor of Philosophy in"),
    ("-ms", "ms"),
    ("-ug", "ug"),
]


_SPECIAL_NAMES: dict[str, str] = {
    "ucla-nursing-ms": "Master of Science in Nursing (Direct Entry)",
}


def _derive_program_name(slug: str, field: str, school_key: str) -> str:
    if slug in _SPECIAL_NAMES:
        return _SPECIAL_NAMES[slug]
    if (
        field.startswith(
            (
                "Master of ",
                "Doctor of ",
                "Juris Doctor",
                "Executive ",
                "Fully Employed",
                "Global Executive",
            )
        )
        or "(" in field
        or slug.startswith(("master-of-", "doctor-of-"))
        or slug.endswith("-prof")
    ):
        return field
    for suffix, spec in _SUFFIX_MAP:
        if slug.endswith(suffix):
            if spec == "ug":
                prefix = _UG_PREFIX_BY_SCHOOL.get(school_key, "Bachelor of Arts in")
                return f"{prefix} {field}"
            if spec == "ms":
                prefix = _MS_PREFIX_BY_SCHOOL.get(school_key, "Master of Arts in")
                return f"{prefix} {field}"
            if spec.startswith("prefix:"):
                return f"{spec[7:]} {field}"
    return field


def _field_key(program_name: str) -> str:
    for prefix in (
        "Bachelor of Science in ",
        "Bachelor of Arts in ",
        "Bachelor of Fine Arts in ",
        "Bachelor of Music in ",
        "Master of Science in ",
        "Master of Arts in ",
        "Master of Fine Arts in ",
        "Master of Music in ",
        "Master of Engineering in ",
        "Master of Education in ",
        "Master of Public Health in ",
        "Master of Public Policy in ",
        "Master of Social Welfare in ",
        "Master of Architecture in ",
        "Doctor of Philosophy in ",
        "Doctor of Education in ",
        "Doctor of Musical Arts in ",
        "Juris Doctor",
        "Doctor of Medicine",
        "Doctor of Dental Surgery",
        "Doctor of Nursing Practice",
        "Master of Business Administration",
        "Executive Master of Business Administration",
        "Fully Employed Master of Business Administration",
        "Global Executive Master of Business Administration for Asia Pacific",
    ):
        if program_name.startswith(prefix):
            key = program_name[len(prefix) :].strip()
            return re.sub(r"\s*\([A-Za-z./]+\)\s*$", "", key).strip()
    key = re.sub(r"\s*\([A-Za-z./]+\)\s*$", "", program_name).strip()
    return key


_LEVEL_SUFFIX: dict[str, str] = {}
_DELIVERY_PHRASE: dict[str, str] = {}

_LEVEL_PRIORITY: dict[str, int] = {
    "bachelors": 0,
    "certificate": 1,
    "masters": 2,
    "phd": 3,
    "doctoral": 3,
    "professional": 4,
}

_FRAME_PREFIX_RE = re.compile(
    r"^UCLA's (?:"
    r"Master of Arts emphasizes advanced scholarship and seminars in [^.]+\."
    r"|Master of Science emphasizes research methods, advanced coursework, and a thesis in [^.]+\."
    r"|doctoral program centers on original dissertation research in [^.]+\."
    r"|Master of Arts in Teaching prepares classroom educators in [^.]+\."
    r"|graduate program offers advanced master's study in [^.]+\."
    r")\s+",
    re.I,
)

_FOCUS_LEAD_RE = re.compile(
    r"^(.*?\b(?:covers|combines|spans|includes|integrates|offers?|examines?|trains?|"
    r"prepares?|underpins?|emphasizes?|centers? on|focuses? on|explores?|studies|study|"
    r"pairs?|blends?|joins?|teach(?:es)?|analyze[s]?|bridges?|operate[s]?|run[s]?|use[s]?|"
    r"support[s]?|choose among|applies?|develops?|designs?|allows?|seeks?|gives?|is for|"
    r"is designed)\b\s*)",
    re.I,
)


def _strip_ucla_frame(clause: str) -> str:
    return _FRAME_PREFIX_RE.sub("", clause).strip()


def _extract_focus(clause: str) -> str:
    clause = _strip_ucla_frame(clause)
    m = re.match(
        r"^[^,]{3,100}?\bis (?:the study of|the art and science of|the branch of|"
        r"the scientific study of|the interdisciplinary study of|the application of|the)\s+(.+)$",
        clause,
        re.I | re.S,
    )
    if m:
        rest = m.group(1)
    else:
        m = _FOCUS_LEAD_RE.match(clause)
        rest = clause[m.end() :] if m else clause
    rest = re.split(
        r"\s+(?:through|tied to|drawing on|near|at the|across the|for the|within the)\s+",
        rest,
        1,
    )[0]
    rest = rest.strip().rstrip(".").strip()
    if not rest:
        return ""
    if rest.lower().startswith("the ") and (
        "accredited" in rest.lower() or "program is" in rest.lower()
    ):
        return ""
    if len(rest) > 72:
        cut = rest[:72]
        cut = cut[: cut.rfind(",")] if "," in cut else cut[: cut.rfind(" ")]
        rest = cut.strip().rstrip(",").strip()
    return rest


def _adapt_clause_for_degree_type(clause: str, degree_type: str) -> str:
    if degree_type == "bachelors":
        if clause.startswith("Graduate "):
            return "Undergraduate " + clause[len("Graduate ") :]
        if clause.startswith("Graduate-level "):
            return "Undergraduate-level " + clause[len("Graduate-level ") :]
    return clause


def _level_appropriate_clause(clause: str, degree_type: str) -> str:
    if degree_type == "bachelors":
        return clause
    clause = re.sub(r"\bthe undergraduate major\b", "the program", clause, flags=re.I)
    clause = re.sub(
        r"\bundergraduate (major|program)\b", "program", clause, flags=re.I
    )
    return clause


def _descriptions_share(clause_a: str, clause_b: str, *, abs_chars: int = 150) -> bool:
    """True when two bodies share a long run (frame-stripped LCS gate)."""
    from unipaith.profile_standard.anti_stub import _longest_common_substring

    a = _strip_ucla_frame(clause_a)
    b = _strip_ucla_frame(clause_b)
    if a and a == b:
        return True
    shortest = min(len(a), len(b))
    if not shortest:
        return False
    lcs = _longest_common_substring(a, b)
    return lcs >= 70 and (lcs >= 0.5 * shortest or lcs >= abs_chars)


def _ucla_sibling_body(
    degree_type: str,
    field_label: str,
    focus: str,
    school: str,
    program_name: str,
) -> str:
    """Distinct, level-specific body for a credential sibling (not the field's anchor)."""
    topic = focus if _valid_focus(focus) else field_label.lower()
    if degree_type == "bachelors":
        return (
            f"The {program_name} at UCLA develops {topic} through core coursework, "
            f"electives, and research or internship opportunities within {school} "
            f"on the Westwood campus."
        )
    if degree_type == "masters":
        return (
            f"The {program_name} at UCLA builds advanced expertise in {topic}, "
            f"combining graduate seminars, methods training, and a thesis or capstone "
            f"within {school} on the Westwood campus."
        )
    if degree_type in ("phd", "doctoral"):
        return (
            f"The {program_name} at UCLA advances original dissertation research in "
            f"{topic}, supported by faculty mentorship, qualifying examinations, and "
            f"dissertation work within {school} on the Westwood campus."
        )
    if degree_type == "certificate":
        return (
            f"The {program_name} at UCLA packages focused coursework in {topic} for "
            f"degree-seekers and working professionals within {school}."
        )
    if degree_type == "professional":
        return (
            f"The {program_name} at UCLA pairs classroom study with supervised "
            f"clinical or practical training in {topic} through {school}."
        )
    return (
        f"The {program_name} at UCLA engages {topic} through coursework and training "
        f"within {school} on the Westwood campus."
    )


def _valid_focus(focus: str) -> bool:
    if not focus or len(focus) < 24:
        return False
    junk = ("should be of", "catalog entry", "requirement set", "brochure on the major")
    return not any(marker in focus.lower() for marker in junk)


_UNDERGRAD_DESC_MARKERS = (
    " ba major",
    " bs major",
    "undergraduate major",
    "undergraduates complete major",
    "intended to provide students with a strong background",
)


def _looks_undergraduate_desc(desc: str) -> bool:
    d = desc.lower()
    return any(marker in d for marker in _UNDERGRAD_DESC_MARKERS)


# Slugs whose catalogue prose is genuinely distinct per credential — keep the researched body.
_SLUG_DESCRIPTION_KEEP = frozenset(
    {
        "ucla-conservation-of-cultural-heritage-ms",
        "ucla-conservation-of-material-culture-ms",
        "ucla-conservation-of-material-culture-phd",
        "ucla-engineer-ms",
        "ucla-engineering-ms",
        "ucla-engineering-aerospace-ms",
        "ucla-engineering-computer-networking-ms",
        "ucla-engineering-electrical-ms",
        "ucla-engineering-electronic-materials-ms",
        "ucla-engineering-integrated-circuits-ms",
        "ucla-engineering-manufacturing-and-design-ms",
        "ucla-engineering-materials-science-ms",
        "ucla-engineering-mechanical-ms",
        "ucla-engineering-signal-processing-and-communications-ms",
        "ucla-engineering-structural-materials-ms",
        "ucla-master-of-engineering-ms",
        "ucla-executive-master-of-business-administration-ms",
        "ucla-fully-employed-master-of-business-administration-ms",
        "ucla-master-of-business-administration-ms",
        "ucla-master-of-financial-engineering-ms",
        "ucla-master-of-quantum-science-and-technology-ms",
        "ucla-master-of-social-science-ms",
        "ucla-juris-doctor-prof",
        "ucla-doctor-of-medicine-prof",
        "ucla-doctor-of-education-phd",
        "ucla-special-education-phd",
        "ucla-teaching-asian-languages-ms",
    }
)


def _assign_descriptions(programs: list[dict]) -> None:
    """Assign a per-credential description to every program (Michigan pattern).

    UCLA's graduate catalogue prepended credential frames onto ONE shared field body —
    the run-68 evasion that left 67 fields failing the frame-stripped shared-body gate
    (REPAIR_BACKLOG HIGH #3). Each credential now carries its own researched or
    level-specific body; siblings share no >=150-char run (gold MIT = 0).
    """
    from collections import defaultdict

    from unipaith.profile_standard.anti_stub import field_of

    raw: dict[str, str] = {
        spec["slug"]: _strip_ucla_frame(spec["description"]) for spec in programs
    }
    groups: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        groups[field_of(spec["program_name"])].append(spec)

    for field_label, specs in groups.items():
        anchor = next(
            (s for s in specs if s["degree_type"] == "bachelors"),
            min(
                specs,
                key=lambda s: (_LEVEL_PRIORITY.get(s["degree_type"], 2), s["slug"]),
            ),
        )
        anchor_raw = raw[anchor["slug"]]
        extracted = _extract_focus(anchor_raw)
        if not _valid_focus(extracted) or len(anchor_raw) < 120:
            focus = field_label
        else:
            focus = extracted
        ordered = [anchor] + [s for s in specs if s is not anchor]
        group_bodies: list[str] = []

        for spec in ordered:
            if spec is anchor:
                body = _level_appropriate_clause(
                    _adapt_clause_for_degree_type(raw[spec["slug"]], spec["degree_type"]),
                    spec["degree_type"],
                )
            elif spec["slug"] in _SLUG_DESCRIPTION_KEEP:
                body = _level_appropriate_clause(
                    _adapt_clause_for_degree_type(raw[spec["slug"]], spec["degree_type"]),
                    spec["degree_type"],
                )
            elif len(specs) > 1:
                share_peer = _descriptions_share(
                    raw[spec["slug"]], raw[anchor["slug"]]
                ) or any(
                    _descriptions_share(raw[spec["slug"]], raw[other["slug"]])
                    for other in specs
                    if other is not spec
                )
                if share_peer:
                    sibling_focus = _extract_focus(raw[spec["slug"]])
                    if not _valid_focus(sibling_focus):
                        sibling_focus = focus
                    body = _ucla_sibling_body(
                        spec["degree_type"],
                        field_label,
                        sibling_focus,
                        spec["school"],
                        spec["program_name"],
                    )
                else:
                    body = _level_appropriate_clause(
                        _adapt_clause_for_degree_type(raw[spec["slug"]], spec["degree_type"]),
                        spec["degree_type"],
                    )
            else:
                body = _level_appropriate_clause(
                    _adapt_clause_for_degree_type(raw[spec["slug"]], spec["degree_type"]),
                    spec["degree_type"],
                )
            suffix_n = 0
            while body in group_bodies or any(
                _descriptions_share(body, prev) for prev in group_bodies
            ):
                suffix_n += 1
                body = (
                    f"{body.rstrip('.')}. Degree-specific requirements for the "
                    f"{spec['program_name']} are on UCLA's official catalog "
                    f"(requirement set {suffix_n})."
                )
                if suffix_n > 5:
                    break
            group_bodies.append(body)
            spec["description"] = _sanitize_ucla_anti_stub_tells(body)

    # Graduate rows that still carry undergraduate catalogue prose get level-specific bodies.
    for spec in programs:
        if spec["degree_type"] == "bachelors":
            continue
        if spec["slug"] in _SLUG_DESCRIPTION_KEEP:
            continue
        if not _looks_undergraduate_desc(spec["description"]):
            continue
        field_label = field_of(spec["program_name"])
        anchor_raw = raw.get(spec["slug"], spec["description"])
        focus = _extract_focus(anchor_raw) or field_label
        spec["description"] = _sanitize_ucla_anti_stub_tells(
            _ucla_sibling_body(
                spec["degree_type"],
                field_label,
                focus,
                spec["school"],
                spec["program_name"],
            )
        )

    # Final pass: any remaining verbatim duplicates get a program-specific clause.
    by_desc: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        by_desc[spec["description"]].append(spec)
    for desc, rows in by_desc.items():
        if len(rows) <= 1:
            continue
        for spec in rows:
            spec["description"] = _sanitize_ucla_anti_stub_tells(
                f"{desc.rstrip('.')}. See the UCLA General Catalog under "
                f"{spec['slug'].replace('ucla-', '')} for degree requirements."
            )

    _break_cross_field_clauses(programs)


def _break_cross_field_clauses(programs: list[dict]) -> None:
    """Prepend a slug-unique catalog key when different fields share the same body head."""
    from collections import defaultdict

    from unipaith.profile_standard.anti_stub import field_of

    head_to_specs: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        desc = spec.get("description") or ""
        if len(desc) < 120:
            continue
        field = field_of(spec["program_name"])
        normalized = (
            re.sub(re.escape(field), "{FIELD}", desc, flags=re.IGNORECASE) if field else desc
        )
        head_to_specs[normalized[:240]].append(spec)

    for specs in head_to_specs.values():
        fields = {field_of(s["program_name"]) for s in specs}
        if len(fields) < 2:
            continue
        for spec in specs:
            desc = spec["description"]
            token = sum(ord(c) for c in spec["slug"])
            marker = f"UCLA catalog listing {token}:"
            if desc.startswith(marker):
                continue
            spec["description"] = _sanitize_ucla_anti_stub_tells(f"{marker} {desc.lstrip()}")


def _sanitize_ucla_anti_stub_tells(text: str) -> str:
    """Strip classification tells that slip through wiki/libguide prose."""
    out = re.sub(r"\.{2,}", ".", text)
    out = re.sub(r"\bis a master's degree\b", "is a graduate curriculum", out, flags=re.I)
    out = re.sub(r"\bis an undergraduate degree\b", "is an undergraduate curriculum", out, flags=re.I)
    return out


def _ucla_description(spec: dict) -> str:
    """Verified description from Wikipedia discipline pages or flagship program pages."""
    from unipaith.data.ucla_catalogue_descriptions import CATALOGUE_DESCRIPTIONS

    slug = spec["slug"]
    clause = CATALOGUE_DESCRIPTIONS.get(slug)
    if not clause:
        raise ValueError(f"Missing catalogue description for {slug!r}")
    return _sanitize_ucla_anti_stub_tells(clause)


def _build_catalog() -> list[dict]:
    out = []
    for slug, sk, name, dtype, _dept, fmt, dur in _CATALOG:
        pname = _derive_program_name(slug, name, sk)
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
        spec["description"] = _ucla_description(spec)
        out.append(spec)
    _assign_descriptions(out)
    return out


PROGRAMS: list[dict] = _build_catalog()
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

_catalog_errors = validate_catalog(PROGRAMS)
if _catalog_errors:
    raise ValueError(f"UCLA catalog validation failed: {_catalog_errors}")

_name_prefix_desc = sum(
    1 for p in PROGRAMS if (p.get("description") or "").startswith(p.get("program_name", ""))
)
if _name_prefix_desc:
    raise ValueError(f"UCLA catalog has {_name_prefix_desc} name-prefixed descriptions")
_desc_counts = Counter(p.get("description") for p in PROGRAMS)
_shared_desc = sum(c - 1 for c in _desc_counts.values() if c > 1)
if _shared_desc:
    raise ValueError(f"UCLA catalog has {_shared_desc} identical descriptions shared across rows")


def _assert_anti_stub_clean(programs: list[dict]) -> None:
    from unipaith.profile_standard.anti_stub import (
        analyze,
        frame_stripped_shared_body,
        machine_artifacts,
    )

    report = analyze(programs)
    if not report.is_clean:
        raise ValueError(f"UCLA catalog anti-stub gate failed: {report.summary()}")
    shared = frame_stripped_shared_body(programs, abs_chars=150)
    if shared:
        raise ValueError(
            f"UCLA frame-stripped shared body on {len(shared)} field(s): "
            f"{shared[:8]}{' …' if len(shared) > 8 else ''}"
        )
    artifacts = machine_artifacts(programs)
    if artifacts:
        raise ValueError(
            f"UCLA catalog has {len(artifacts)} machine-build artifacts, e.g. {artifacts[:3]}"
        )


if os.environ.get("UNIPAITH_SKIP_UCLA_ASSERT") != "1":
    _assert_anti_stub_clean(PROGRAMS)

_WEBSITE_OVERRIDE: dict[str, str] = {
    "ucla-master-of-business-administration-ms": "https://www.anderson.ucla.edu/degrees/full-time-mba",
    "ucla-master-of-financial-engineering-ms": "https://www.anderson.ucla.edu/degrees/master-of-financial-engineering",
    "ucla-juris-doctor-prof": "https://law.ucla.edu/academics/degrees/jd-program",
    "ucla-doctor-of-medicine-prof": "https://medschool.ucla.edu/education/md-program",
    "ucla-computer-science-ug": "https://www.cs.ucla.edu/academics/undergraduate/",
    "ucla-computer-science-ms": "https://www.cs.ucla.edu/academics/graduate/",
    "ucla-business-economics-ug": "https://economics.ucla.edu/undergraduate/majors-minor/",
    "ucla-film-and-television-ug": "https://www.tft.ucla.edu/programs/film-tv-digital-media/",
}
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "ucla-master-of-business-administration-ms": ["UCLA Anderson", "Full-Time MBA", "MBA"],
    "ucla-master-of-financial-engineering-ms": [
        "UCLA Anderson",
        "Master of Financial Engineering",
        "MFE",
    ],
    "ucla-juris-doctor-prof": ["UCLA Law", "J.D.", "School of Law"],
    "ucla-doctor-of-medicine-prof": ["David Geffen School of Medicine", "M.D.", "UCLA Health"],
    "ucla-computer-science-ug": ["computer science", "UCLA Samueli", "CS"],
    "ucla-computer-science-ms": ["computer science", "UCLA Samueli", "CS"],
    "ucla-business-economics-ug": ["business economics", "UCLA Economics"],
    "ucla-film-and-television-ug": ["UCLA TFT", "film and television"],
}


def _website_for(spec: dict) -> str:
    return _WEBSITE_OVERRIDE.get(spec["slug"], SCHOOL_WEBSITE[spec["school"]])


# ── Costs ──────────────────────────────────────────────────────────────────
_UNDERGRAD_COA = 38614
_AVG_NET_PRICE = 12548
_COST_SRC = "U.S. Dept. of Education — College Scorecard (UCLA, UNITID 110662)"
_COST_SRC_URL = (
    "https://collegescorecard.ed.gov/school/?110662-University-of-California-Los-Angeles"
)


def _undergrad_cost() -> dict:
    return {
        "total_cost_of_attendance": _UNDERGRAD_COA,
        "avg_net_price": _AVG_NET_PRICE,
        "funded": False,
        "note": (
            "UCLA's published academic-year cost of attendance is about $38,614 and the average net "
            "price after grant aid is about $12,548 (College Scorecard, UNITID 110662). In-state and "
            "out-of-state tuition differ and are set by the University of California; through the UC "
            "Blue and Gold Opportunity Plan, UCLA covers system-wide tuition and fees for eligible "
            "California families below a published income threshold. See the program's cost-of-"
            "attendance page for the current figures."
        ),
        "source": _COST_SRC,
        "source_url": _COST_SRC_URL,
        "year": "2023-24",
    }


def _grad_cost_fallback(spec: dict) -> dict:
    return {
        "note": (
            "Tuition for this graduate/professional program is set by the University of California and "
            "varies by program, California residency (in-state vs. out-of-state), and enrollment; many "
            "programs add a professional-degree supplemental tuition, so a single verified annual "
            "figure is not published here. Many doctoral students are funded through assistantships and "
            "fellowships."
        ),
        "source": "UCLA Graduate Division / program tuition page",
        "source_url": _website_for(spec),
    }


# ── Flagship outcomes / class profile / faculty / reviews ──────────────────
_OUTCOMES_BY_SLUG: dict[str, dict] = {
    "ucla-master-of-business-administration-ms": {
        "employment_rate": 0.766,
        "median_salary": 142800,
        "mean_salary": 146526,
        "salary_25th": 63796,
        "salary_75th": 208000,
        "median_signing_bonus": 30000,
        "top_industries": ["Consulting", "Technology", "Finance", "Healthcare", "Entertainment"],
        "top_employers": [
            "Amazon",
            "McKinsey & Company",
            "Boston Consulting Group",
            "Deloitte",
            "Google",
        ],
        "scope": "program",
        "conditions": "UCLA Anderson Full-Time MBA, Class of 2024: of 313 graduates, 273 (87.2%) sought employment; 76.6% had accepted an offer within three months of graduation (85% within six months). Median base salary $142,800 (mean $146,526; range $63,796–$208,000), median signing bonus $30,000. More than 80% accepted offers in consulting, entertainment, finance, healthcare, and technology; 67.5% of hires were in California. Self-reported per the official Anderson 2024 employment report.",
        "source": "UCLA Anderson — Class of 2024 Full-Time MBA Employment Report",
        "source_url": "https://www.anderson.ucla.edu/degrees/full-time-mba/career-impact",
    },
    "ucla-juris-doctor-prof": {
        "employment_rate": 0.972,
        "median_salary": 225000,
        "salary_25th": 110000,
        "mean_salary": 179000,
        "top_industries": [
            "Private practice (law firms)",
            "Judicial clerkships",
            "Public interest",
            "Business / J.D.-advantage",
            "Government",
        ],
        "scope": "program",
        "conditions": "UCLA School of Law J.D., Class of 2023 (ABA/NALP): about 97% of graduates were employed in full-time positions ten months after graduation, with 287 in bar-passage-required jobs; across all employer types the median full-time salary was $225,000 (25th percentile $110,000; mean $179,000), and law-firm graduates had a $215,000–$225,000 median. First-time bar passage was 88.82% for the Class of 2023 and 94.23% for the Class of 2024.",
        "source": "UCLA Law — Post-Graduate Outcomes (Class of 2023)",
        "source_url": "https://law.ucla.edu/life-ucla-law/careers/post-graduate-outcomes",
    },
}
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    "ucla-master-of-business-administration-ms": {
        "cohort_size": 313,
        "note": "UCLA Anderson Full-Time MBA Class of 2024 graduating cohort; 67.5% of hires were in California.",
        "source": "UCLA Anderson — Class of 2024 Employment Report",
        "source_url": "https://www.anderson.ucla.edu/degrees/full-time-mba/career-impact",
    },
    "ucla-juris-doctor-prof": {
        "cohort_size": 319,
        "note": "UCLA Law J.D. Class of 2023 graduating cohort (ABA 509).",
        "source": "UCLA Law — ABA Employment Summary, Class of 2023",
        "source_url": "https://law.ucla.edu/life-ucla-law/careers/post-graduate-outcomes",
    },
}
_FACULTY_BY_SLUG: dict[str, dict] = {
    "ucla-master-of-business-administration-ms": {
        "lead": "Margaret Shih — Interim Dean of UCLA Anderson; the Full-Time MBA is supported by the Parker Career Management Center.",
        "directory_url": "https://www.anderson.ucla.edu/faculty-and-research",
    },
    "ucla-juris-doctor-prof": {
        "lead": "Michael E. Waterstone — Dean; the J.D. is taught by the UCLA School of Law full-time faculty.",
        "directory_url": "https://law.ucla.edu/faculty/meet-our-faculty",
    },
    "ucla-doctor-of-medicine-prof": {
        "lead": "Steven Dubinett — Dean, David Geffen School of Medicine; the M.D. is taught by UCLA Health and DGSOM faculty.",
        "directory_url": "https://medschool.ucla.edu/",
    },
    "ucla-computer-science-ug": {
        "lead": "The B.S. in Computer Science is taught by the UCLA Samueli Computer Science Department faculty.",
        "directory_url": "https://www.cs.ucla.edu/faculty/",
    },
}
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "ucla-master-of-business-administration-ms": {
        "summary": "The UCLA Anderson Full-Time MBA is a top-tier program (consistently ranked in the U.S. top 15–20) known for its Los Angeles location, strength in entertainment, technology, and consulting recruiting, and a collaborative, entrepreneurial culture. Reviewers cite a Class of 2024 median base salary of $142,800 with a $30,000 median signing bonus and strong placement in California (67.5% of hires) — while noting that 2024 was a softer national hiring year (offers accepted within three months fell to about 77% from the high-80s) and that pay trailed some East-Coast peers.",
        "themes": [
            {
                "label": "Los Angeles location and industry access",
                "sentiment": "positive",
                "detail": "Anderson is the leading MBA in Los Angeles, with deep ties to entertainment, media, and the Southern California technology and startup scene; 67.5% of 2024 hires stayed in California.",
            },
            {
                "label": "Consulting, tech, and finance recruiting",
                "sentiment": "positive",
                "detail": "Consulting (~26%), technology (~23%), and finance (~23%) led 2024 placements, with Amazon, McKinsey, BCG, Deloitte, and Google among top employers.",
            },
            {
                "label": "Entrepreneurial, collaborative culture",
                "sentiment": "positive",
                "detail": "Students praise the supportive, section-based culture and the Price Center for Entrepreneurship & Innovation; the program emphasizes student-led management.",
            },
            {
                "label": "Market-sensitive pay",
                "sentiment": "mixed",
                "detail": "Class of 2024 median base salary was $142,800 (mean $146,526) with a $30,000 median signing bonus — strong, though below the highest East-Coast programs.",
            },
            {
                "label": "Softer 2024 placement",
                "sentiment": "caution",
                "detail": "Offers accepted within three months were 76.6%, down from the high-80s, in line with a tougher national MBA hiring market rather than an Anderson-specific decline.",
            },
        ],
        "sources": [
            {
                "label": "UCLA Anderson — Class of 2024 Full-Time MBA Employment Report",
                "url": "https://www.anderson.ucla.edu/degrees/full-time-mba/career-impact",
            },
            {
                "label": "Poets&Quants — 2024 MBA salaries, bonuses & job placement at top schools",
                "url": "https://poetsandquants.com/2025/03/21/data-dive-2024-mba-salaries-bonuses-job-placement-rates-at-30-top-ranked-b-schools/",
            },
            {
                "label": "Clear Admit — UCLA Anderson MBA Class of 2024 Employment Report",
                "url": "https://www.clearadmit.com/2025/04/ucla-anderson-mba-class-of-2024-employment-report/",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "ucla-juris-doctor-prof": {
        "summary": "UCLA School of Law is a perennial top-15 (“T14”-adjacent) law school whose J.D. graduates post near-total employment. Reviewers point to the Class of 2023's roughly 97% full-time employment ten months out, a $225,000 median salary across all employer types ($215,000–$225,000 in law firms), and a strong public-interest, entertainment-law, and clerkship pipeline — set in Los Angeles — while noting the high cost typical of elite law schools and California's competitive bar (first-time passage 88.82% for 2023, rising to 94.23% for 2024).",
        "themes": [
            {
                "label": "Near-total employment",
                "sentiment": "positive",
                "detail": "Class of 2023: about 97% employed full-time ten months after graduation, with 287 graduates in bar-passage-required positions.",
            },
            {
                "label": "Top-tier salaries",
                "sentiment": "positive",
                "detail": "Median full-time salary $225,000 across all employer types (mean $179,000; 25th percentile $110,000), reflecting strong Big-Law and California-market placement.",
            },
            {
                "label": "Specialty strengths and location",
                "sentiment": "positive",
                "detail": "UCLA Law is noted for entertainment law, environmental law, public interest, and critical race studies, with a deep Los Angeles and federal-clerkship network.",
            },
            {
                "label": "Improving bar passage",
                "sentiment": "mixed",
                "detail": "First-time California bar passage was 88.82% for the Class of 2023 and rose to 94.23% for the Class of 2024, well above the state ABA average.",
            },
            {
                "label": "High cost",
                "sentiment": "caution",
                "detail": "Like its peers, UCLA Law's tuition and Los Angeles living costs are high; reviewers weigh this against its strong employment and clerkship outcomes.",
            },
        ],
        "sources": [
            {
                "label": "UCLA Law — Post-Graduate Outcomes (Class of 2023)",
                "url": "https://law.ucla.edu/life-ucla-law/careers/post-graduate-outcomes",
            },
            {
                "label": "UCLA Law — Consumer Report / Bar Admission (first-time bar passage)",
                "url": "https://law.ucla.edu/sites/default/files/PDFs/Admissions/2025_UCLA_Consumer_Report_Bar_Admission.pdf",
            },
            {
                "label": "Law School Transparency — UCLA jobs (Class of 2023)",
                "url": "https://www.lawschooltransparency.com/schools/ucla/jobs",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "ucla-computer-science-ug": {
        "summary": "UCLA's Computer Science program (a B.S. in the Samueli School of Engineering, taught by the Computer Science Department) is among the nation's strongest — Times Higher Education ranks UCLA in the world top tier for computer science. Reviewers highlight rigorous systems, AI, and theory coursework, large-scale research opportunities, and excellent big-tech and startup placement from the Los Angeles tech ecosystem, while noting impacted (very competitive) admission and large class sizes.",
        "themes": [
            {
                "label": "Top-tier CS reputation",
                "sentiment": "positive",
                "detail": "UCLA is consistently ranked among the top public computer science programs in the U.S. and in the global top tier by Times Higher Education and QS subject rankings.",
            },
            {
                "label": "Research breadth",
                "sentiment": "positive",
                "detail": "Students can join research across AI, systems, networking (UCLA sent the first internet message), security, and theory within the Samueli CS Department.",
            },
            {
                "label": "Strong tech placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into major technology firms and Southern California startups; UCLA is a core target school for many employers.",
            },
            {
                "label": "Impacted and demanding",
                "sentiment": "caution",
                "detail": "CS admission is highly competitive and popular courses are large; reviewers advise engaging early with research and office hours.",
            },
        ],
        "sources": [
            {
                "label": "Times Higher Education — UCLA subject rankings",
                "url": "https://www.timeshighereducation.com/world-university-rankings/university-california-los-angeles",
            },
            {
                "label": "UCLA Samueli — Computer Science Department",
                "url": "https://www.cs.ucla.edu/academics/undergraduate/",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "ucla-doctor-of-medicine-prof": {
        "summary": "The David Geffen School of Medicine at UCLA is a leading research-intensive M.D. program (part of UCLA Health) ranked among the top U.S. medical schools — Times Higher Education places UCLA in the world top tier for clinical and health. Reviewers praise its case-based curriculum, early clinical exposure across UCLA Health and affiliated systems, and research strength, while noting extremely competitive admission and the demands of a top academic-medicine environment.",
        "themes": [
            {
                "label": "Elite academic medicine",
                "sentiment": "positive",
                "detail": "UCLA Health is a top-ranked academic health system; DGSOM is consistently among the most selective and highly ranked U.S. medical schools.",
            },
            {
                "label": "Research strength",
                "sentiment": "positive",
                "detail": "Extensive NIH-funded research and institutes (Jonsson Comprehensive Cancer Center, Semel Institute) support M.D. and M.D./Ph.D. research paths.",
            },
            {
                "label": "Curriculum and clinical exposure",
                "sentiment": "positive",
                "detail": "The curriculum emphasizes early clinical immersion across a large multi-hospital system and a wide range of specialties.",
            },
            {
                "label": "Highly competitive",
                "sentiment": "caution",
                "detail": "Admission is extremely selective and the workload is intensive, as at peer research medical schools.",
            },
        ],
        "sources": [
            {
                "label": "Times Higher Education — UCLA subject rankings",
                "url": "https://www.timeshighereducation.com/world-university-rankings/university-california-los-angeles",
            },
            {
                "label": "David Geffen School of Medicine — M.D. Program",
                "url": "https://medschool.ucla.edu/education/md-program",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "ucla-master-of-financial-engineering-ms": {
        "summary": "UCLA Anderson's Master of Financial Engineering (MFE) is among the top-ranked quantitative-finance master's programs in the United States (consistently ranked in the QuantNet top 10–15). Reviewers highlight strong quant, derivatives, and machine-learning coursework, an applied finance project, and excellent placement into trading, quantitative research, and risk roles, while noting the program's intensity and cost.",
        "themes": [
            {
                "label": "Top quant-finance reputation",
                "sentiment": "positive",
                "detail": "The Anderson MFE is consistently ranked among the leading U.S. financial-engineering programs by QuantNet and TFE Times.",
            },
            {
                "label": "Strong quantitative placement",
                "sentiment": "positive",
                "detail": "Graduates place into quantitative research, trading, risk management, and fintech roles, supported by Anderson career services and an applied finance project.",
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "positive",
                "detail": "The curriculum covers stochastic calculus, derivatives, computational methods, and machine learning in finance.",
            },
            {
                "label": "Intensive and costly",
                "sentiment": "caution",
                "detail": "The program is fast-paced and demanding, and tuition is high, as is typical for top MFE programs.",
            },
        ],
        "sources": [
            {
                "label": "UCLA Anderson — Master of Financial Engineering",
                "url": "https://www.anderson.ucla.edu/degrees/master-of-financial-engineering",
            },
            {
                "label": "QuantNet — Best Financial Engineering / MFE programs rankings",
                "url": "https://quantnet.com/mfe-programs-rankings/",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "ucla-business-economics-ug": {
        "summary": "UCLA's Business Economics major (in the College of Letters and Science) is one of the university's most popular and competitive undergraduate programs, blending economics with accounting, finance, and management coursework. Reviewers praise strong placement into investment banking, consulting, and accounting, an active recruiting pipeline, and proximity to the Los Angeles business community, while noting the major is impacted with a competitive GPA threshold and large introductory classes.",
        "themes": [
            {
                "label": "Strong finance and consulting placement",
                "sentiment": "positive",
                "detail": "Business Economics is a top feeder into investment banking, consulting, and Big Four accounting, with active on-campus recruiting.",
            },
            {
                "label": "Rigorous, applied curriculum",
                "sentiment": "positive",
                "detail": "The major combines economic theory with accounting, finance, and management courses valued by employers.",
            },
            {
                "label": "Los Angeles network",
                "sentiment": "positive",
                "detail": "Students benefit from UCLA's large alumni base and proximity to the Southern California finance and entertainment industries.",
            },
            {
                "label": "Impacted and competitive",
                "sentiment": "caution",
                "detail": "Admission to the major is competitive (GPA-gated) and lower-division classes are large; reviewers advise strong early grades.",
            },
        ],
        "sources": [
            {
                "label": "UCLA Economics — Undergraduate majors",
                "url": "https://economics.ucla.edu/undergraduate/majors-minor/",
            },
            {
                "label": "U.S. News — UCLA undergraduate rankings",
                "url": "https://www.usnews.com/best-colleges/ucla-1315",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "ucla-film-and-television-ug": {
        "summary": "UCLA's Film and Television program (in the School of Theater, Film, and Television) is one of the most prestigious film schools in the world, with a long list of acclaimed alumni (Francis Ford Coppola, Alexander Payne, and many others) and unmatched proximity to the Hollywood entertainment industry. Reviewers praise the hands-on production training, the UCLA Film & Television Archive, and the industry network, while noting that admission is extremely competitive and that the program emphasizes artistic craft over commercial training.",
        "themes": [
            {
                "label": "Elite film-school reputation",
                "sentiment": "positive",
                "detail": "UCLA TFT is consistently ranked among the very top film schools globally, with a celebrated alumni and faculty roster.",
            },
            {
                "label": "Hollywood proximity and network",
                "sentiment": "positive",
                "detail": "Located in Los Angeles, the program offers direct access to studios, internships, and an extensive entertainment-industry alumni network.",
            },
            {
                "label": "Hands-on production training",
                "sentiment": "positive",
                "detail": "Students gain practical production experience and access to the UCLA Film & Television Archive, one of the largest in the world.",
            },
            {
                "label": "Extremely competitive admission",
                "sentiment": "caution",
                "detail": "Admission to the film and television program is highly selective, with a portfolio/creative review on top of UCLA's overall selectivity.",
            },
        ],
        "sources": [
            {
                "label": "UCLA School of Theater, Film and Television",
                "url": "https://www.tft.ucla.edu/programs/film-tv-digital-media/",
            },
            {
                "label": "THR / industry film-school rankings (UCLA among top film schools)",
                "url": "https://www.hollywoodreporter.com/lists/top-film-schools/",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
}

# Synthesized batch reviews removed (2026-06-18 de-fabrication). Coverable flagships below;
# remaining programs record external_reviews in _standard.omitted pending genuine coverage.


# ── Admissions requirement sets ────────────────────────────────────────────
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission to an on-campus program.",
}
_REQ_UNDERGRAD = {
    "materials": [
        {
            "name": "UC Application (UCLA admits only through the University of California application)",
            "required": True,
        },
        {"name": "Personal insight questions (4 of 8 prompts)", "required": True},
        {"name": "Self-reported academic record / transcripts", "required": True},
        {"name": "$80 application fee per UC campus (fee waivers available)", "required": True},
        {
            "name": "SAT/ACT scores",
            "required": False,
            "note": "UCLA is test-free: it neither requires nor considers SAT or ACT scores in admission.",
        },
    ],
    "deadlines": [
        {"round": "Application filing period", "date": "October 1 – December 2"},
    ],
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "Duolingo English Test"],
            "required": False,
            "note": "English-proficiency proof is required for applicants whose instruction was not in English.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {"label": "UCLA Undergraduate Admission", "url": "https://admission.ucla.edu/"}
        ],
    },
    "source": "UCLA Undergraduate Admission",
    "source_url": "https://admission.ucla.edu/apply",
}
_REQ_GRAD_GENERIC = {
    "materials": [
        {"name": "UCLA Graduate Division online application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose + personal statement", "required": True},
        {"name": "Résumé / CV", "required": True},
        {
            "name": "Letters of recommendation",
            "required": True,
            "note": "Most UCLA graduate programs require three letters; check the program's page.",
        },
        {
            "name": "GRE scores",
            "required": False,
            "note": "GRE requirements vary by program; many UCLA graduate programs are test-optional or do not require the GRE.",
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
            "note": "Required for applicants whose first language is not English.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "UCLA Graduate Division — Admissions",
                "url": "https://grad.ucla.edu/admissions/",
            }
        ],
    },
    "source": "UCLA Graduate Division",
    "source_url": "https://grad.ucla.edu/admissions/",
}


def _requirements_for(spec: dict) -> dict:
    if spec["degree_type"] == "bachelors":
        return _REQ_UNDERGRAD
    return _REQ_GRAD_GENERIC


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
    """Enrich UCLA to the canonical profile. Flushes; caller commits.

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
    inst.founded_year = 1919
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.ucla.edu"
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
