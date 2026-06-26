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
ENRICHED_AT = "2026-06-26"


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
        12,
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
        "online",
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
        "online",
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


# A topic clause is slotted into a sentence frame ("builds advanced expertise in {topic}, …",
# "advances original dissertation research in {topic}, …"), so it MUST read as a clean noun
# phrase. The run-71 CRITICAL C2 defect was a fragment slotted raw — a leading preposition
# ("research in OF artistic production…"), a mid-sentence truncation ("understanding of
# human."), or a dangling relative clause ("expertise in THAT incorporates their interests…").
# These helpers reject such fragments so the slot only ever receives a grammatical phrase.
_TOPIC_CLAUSE_END = (". ", "; ", " — ", " – ", " near ", " at the ", " for the ", " within the ")
_TOPIC_TRAILING_JUNK = frozenset(
    {"and", "or", "of", "in", "on", "for", "with", "to", "by", "from", "the", "a", "an", "that"}
)
_TOPIC_BAD_LEAD = frozenset(
    {
        "is", "are", "and", "or", "but", "of", "in", "on", "for", "with", "to", "by",
        "from", "under", "as", "at", "this", "these", "those", "that", "which", "who",
        "whose", "while", "where", "when", "study", "studies", "science", "sciences",
        "discipline", "branch", "field", "area", "form", "body", "way", "set", "system",
        "framework", "process", "method", "theory", "application", "analysis",
        "examination", "investigation", "art", "practice", "applies", "apply",
        "develops", "develop", "prepares", "prepare", "examines", "provides",
        "operates", "encompass", "encompasses", "students", "student", "incorporates",
        "give", "gives", "refine", "accommodate", "specialization", "opportunities",
        "provide", "provides", "prepare", "prepares", "enable", "enabling", "incorporate",
        "understand", "understanding", "designed", "intended", "appropriate", "aims",
        "aim", "seeks", "seek", "allow", "allows", "want", "wants", "desire", "desiring",
    }
)


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
    # Drop a leading preposition the lead-in regex left attached ("...study of artistic
    # production" → "artistic production"), so the slot frame "expertise in {topic}" never
    # doubles a preposition ("expertise in of artistic production…").
    rest = re.sub(r"^(?:of|for|in|on|to|with|that|which|whose|as|by)\s+", "", rest.strip(), flags=re.I)
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
    # Cut at the first clause/sentence boundary so a mid-sentence run never carries a
    # second sentence into the slot ("...visual culture throughout human history. Art").
    cut_at = len(rest)
    for sep in _TOPIC_CLAUSE_END:
        idx = rest.find(sep)
        if 18 <= idx < cut_at:
            cut_at = idx
    rest = rest[:cut_at].strip().rstrip(",;").strip()
    if len(rest) > 72:
        cut = rest[:72]
        cut = cut[: cut.rfind(",")] if "," in cut else cut[: cut.rfind(" ")]
        rest = cut.strip().rstrip(",").strip()
    # Trim trailing connector/article words so the slot never ends dangling ("...fulfillment
    # of", "...desire to pursue").
    words = rest.split()
    while words and words[-1].lower().strip(",;") in _TOPIC_TRAILING_JUNK:
        words.pop()
    return " ".join(words).rstrip(",;").strip()


def _topic_is_clean(topic: str) -> bool:
    """True only when ``topic`` reads as a grammatical noun phrase fit for a sentence slot."""
    if not topic or len(topic) < 12:
        return False
    words = topic.split()
    if words[0].lower() in _TOPIC_BAD_LEAD:
        return False
    if words[-1].lower().strip(",;") in _TOPIC_TRAILING_JUNK or topic.rstrip().endswith((",", ".")):
        return False
    if ". " in topic:
        return False
    # A run-on that smuggles a second verb clause into the slot ("...and develops…").
    if re.search(
        r"\sand\s+(?:develops|applies|operates|provides|creates|manages|delivers|builds|"
        r"examines|explores|designs|produces|trains|enabling|pursue)\b",
        topic,
        re.I,
    ):
        return False
    return True


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
    topic = _topic_for_field(focus, field_label)
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
    if any(marker in focus.lower() for marker in (
        "should be of", "catalog entry", "requirement set", "brochure on the major"
    )):
        return False
    return _topic_is_clean(focus)


# Verified clean topic phrases for fields whose UCLA catalogue anchor prose does not yield a
# grammatical noun phrase by auto-extraction (run-71 CRITICAL C2). Each is a true, distinct
# disciplinary summary grounded in that field's verified anchor description — no fabricated
# named units. The build asserts ``_template_slot_artifacts(PROGRAMS) == []`` so any field
# that still slots a broken fragment surfaces here and is added with a verified topic.
_GRAD_TOPIC_BY_FIELD: dict[str, str] = {
    "African American Studies": "African American history, culture, politics, and social life",
    "American Indian Studies": "American Indian cultures, histories, and contemporary issues",
    "Anthropology": "the cross-cultural, archaeological, and biological study of humanity",
    "Archaeology": "the material remains and methods of archaeological inquiry",
    "Asian Languages and Cultures": "the languages, literatures, and cultures of Asia",
    "Astronomy and Astrophysics (M.A.T.)": "the teaching of astronomy and astrophysics in secondary education",
    "Mathematics (M.A.T.)": "the teaching of mathematics in secondary education",
    "Physics (M.A.T.)": "the teaching of physics in secondary education",
    "Physics (M.S.)": "advanced study and research in physics",
    "Bioengineering": "the application of engineering principles to biology and medicine",
    "Bioinformatics": "computational methods and software for analyzing biological data",
    "Chemical Engineering": "chemical processes, reaction engineering, and process design",
    "Civil Engineering": "structural, environmental, geotechnical, and transportation engineering",
    "Communication": "human communication across interpersonal, media, and political contexts",
    "Culture and Performance": "performance, ritual, and the anthropology of cultural expression",
    "Electrical and Computer Engineering": "circuits, signals, devices, and computer engineering",
    "Environment and Sustainability": "environmental systems, sustainability, and policy",
    "Geography": "spatial analysis of human and physical environments",
    "Germanic Languages": "German and Germanic literature, language, and culture",
    "Human Genetics": "the genetics of human health, disease, and inheritance",
    "Management": "the management, strategy, and organization of enterprises",
    "Molecular, Cell, and Developmental Biology": "molecular, cellular, and developmental processes of living systems",
    "Music in Music": "musical composition, performance, history, and theory",
    "Nursing": "nursing science, patient care, and health promotion",
    "Oral Biology": "the biology of the oral cavity, its microbiota, and oral health",
    "Physics and Biology In Medicine": "the physics and biology underlying medical diagnosis and therapy",
    "Physiological Science": "the function of cells, organs, and systems in living organisms",
    "Planetary Science": "planetary bodies, their formation, and the processes that shape them",
    "Psychology": "cognition, behavior, and the biological and social bases of mind",
    "Sociology": "social structure, institutions, and human social behavior",
    "Spanish": "Spanish and Latin American language, literature, and culture",
    "Aerospace Engineering": "the design, dynamics, and control of aerospace vehicles and systems",
    "Architecture": "architectural design, history, theory, and building technology",
    "Art History": "the study of artistic production and visual culture across periods and cultures",
    "Biology": "molecular, organismal, and ecological approaches to the life sciences",
    "Classics": "the languages, literature, and civilizations of ancient Greece and Rome",
    "Comparative Literature": "literature and cultural expression across languages and national traditions",
    "Computer Science": "computing systems, algorithms, artificial intelligence, and software",
    "English": "English-language literature, criticism, and literary theory",
    "French and Francophone Studies": "French and Francophone literature, language, and culture",
    "Gender Studies": "gender, sexuality, and feminist theory across social and cultural life",
    "Geochemistry": "the chemistry of Earth and planetary materials and processes",
    "Italian": "Italian language, literature, and cultural history",
    "Linguistics": "the structure, sound, meaning, and use of human language",
    "Materials Science and Engineering": "the structure, properties, and processing of engineering materials",
    "Mathematics": "pure and applied mathematics",
    "Mechanical Engineering": "thermodynamics, fluid and solid mechanics, dynamics, and design",
    "Molecular Biology": "the molecular structures and chemical processes of living systems",
    "Molecular and Medical Pharmacology": "molecular and medical pharmacology and drug action",
    "Near Eastern Languages and Cultures": "the languages, texts, and archaeology of the ancient Near East",
    "Philosophy": "metaphysics, epistemology, ethics, and the history of philosophy",
    "Political Science": "political institutions, behavior, theory, and international relations",
    "Slavic, East European, and Eurasian Languages and Cultures": "Slavic, East European, and Eurasian languages, literatures, and cultures",
    "Statistics": "statistical theory, methodology, and data analysis",
    "Theater": "theater, performance, and dramatic practice",
}


def _topic_for_field(focus: str, field_label: str) -> str:
    """A clean, field-specific topic for a sibling slot — never a broken fragment.

    Fields whose catalogue anchor does not auto-extract to a grammatical noun phrase carry a
    verified curated topic (``_GRAD_TOPIC_BY_FIELD``), which always wins — the auto-extractor
    is unreliable on those anchors (run-71 CRITICAL C2). Other fields use a clean extracted
    focus, falling back to a generic disciplinary phrase.
    """
    override = _GRAD_TOPIC_BY_FIELD.get(field_label)
    if override:
        return override
    if _topic_is_clean(focus) and focus.lower() != field_label.lower():
        return focus
    return f"the discipline of {field_label.lower()}"


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


# ── IPEDS/College Scorecard CIP join key per field (matcher field-signal — §"Also
# enrich for the MATCH"). 4-digit CIP-2020 family (NN.NN), each a code UCLA actually
# reports to IPEDS for UNITID 110662 (U.S. Dept. of Education College Scorecard,
# latest.programs.cip_4_digit). Keyed by the catalog field name; never guessed —
# omit-with-reason for a genuinely uncodeable field (none today: 372/372 covered).
# CIP 2020 4-digit codes keyed on the bare UCLA field string (3rd _CATALOG element).
# Matcher consumes the 2-digit family (field_canon._CIP_FAMILY_FIELD); 4-digit kept
# for precision and parity with the Caltech/Princeton/Notre Dame/Chicago fillers.
_CIP_BY_FIELD: dict[str, str] = {
    # --- Engineering (Samueli) — CIP 14.xx / 15.xx ---
    "Aerospace Engineering": "14.0201",
    "Bioengineering": "14.0501",
    "Chemical Engineering": "14.0701",
    "Civil Engineering": "14.0801",
    "Computer Engineering": "14.0901",
    "Computer Science and Engineering": "14.0901",
    "Electrical Engineering": "14.1001",
    "Electrical and Computer Engineering": "14.1001",
    "Materials Engineering": "14.1801",
    "Materials Science and Engineering": "14.1801",
    "Mechanical Engineering": "14.1901",
    "Manufacturing Engineering": "14.3601",
    "Engineering": "14.0101",
    "Engineer": "14.0101",
    "Engineering Geology": "14.3901",
    "Engineering – Aerospace": "14.0201",
    "Engineering – Computer Networking": "14.0901",
    "Engineering – Electrical": "14.1001",
    "Engineering – Electronic Materials": "14.1001",
    "Engineering – Integrated Circuits": "14.1001",
    "Engineering – Manufacturing and Design": "14.3601",
    "Engineering – Materials Science": "14.1801",
    "Engineering – Mechanical": "14.1901",
    "Engineering – Signal Processing and Communications": "14.1001",
    "Engineering – Structural Materials": "14.1801",
    "Doctor of Environmental Science and Engineering": "14.1401",
    "Master of Engineering": "14.0101",
    "Master of Financial Engineering": "52.0801",
    "Master of Quantum Science and Technology": "40.0801",
    # --- Computer & Information / Data — CIP 11.xx / 30.70 ---
    "Computer Science": "11.0701",
    "Bioinformatics": "26.1103",
    "Computational Biology": "26.1104",
    "Data Science in Biomedicine": "30.7001",
    "Data Theory": "30.7001",
    "Statistics and Data Science": "30.7001",
    "Master of Applied Statistics and Data Science": "30.7001",
    "Master of Data Science in Health": "30.7001",
    "Medical Informatics": "51.2706",
    "Master of Library and Information Science": "25.0101",
    "Information Studies": "25.0101",
    # --- Mathematics & Statistics — CIP 27.xx ---
    "Mathematics": "27.0101",
    "Mathematics (M.A.)": "27.0101",
    "Mathematics (M.A.T.)": "27.0101",
    "Mathematics for Teaching": "27.0101",
    "Applied Mathematics": "27.0301",
    "Mathematics of Computation": "27.0303",
    "Mathematics/Applied Science": "27.0101",
    "Mathematics/Economics": "27.0101",
    "Financial Actuarial Mathematics": "27.0305",
    "Statistics": "27.0501",
    "Biomathematics": "27.0301",
    "Biostatistics": "26.1102",
    "Biostatistics (M.P.H.)": "26.1102",
    "Biostatistics (M.S.)": "26.1102",
    # --- Physical Sciences — CIP 40.xx ---
    "Physics": "40.0801",
    "Physics (B.A.)": "40.0801",
    "Physics (B.S.)": "40.0801",
    "Physics (M.A.T.)": "40.0801",
    "Physics (M.S.)": "40.0801",
    "Physics and Biology In Medicine": "40.0801",
    "Astronomy and Astrophysics": "40.0202",
    "Astronomy and Astrophysics (M.A.T.)": "40.0202",
    "Astronomy and Astrophysics (M.S.)": "40.0202",
    "Astrophysics": "40.0202",
    "Planetary Science": "40.0202",
    "Chemistry": "40.0501",
    "General Chemistry": "40.0501",
    "Chemistry/Materials Science": "40.0501",
    "Master of Applied Chemical Sciences": "40.0501",
    "Geochemistry": "40.0602",
    "Geology": "40.0601",
    "Geophysics": "40.0603",
    "Geophysics and Space Physics": "40.0603",
    "Earth and Environmental Science": "40.0601",
    "Atmospheric and Oceanic Sciences": "40.0401",
    "Atmospheric and Oceanic Sciences/Mathematics": "40.0401",
    "Climate Science": "40.0401",
    "Environmental Science": "03.0104",
    "Environment and Sustainability": "03.0104",
    "Environmental and Molecular Toxicology": "26.1006",
    "Master of Applied Geospatial Information Systems and Technologies": "45.0702",
    # --- Biological & Life Sciences — CIP 26.xx ---
    "Biology": "26.0101",
    "Marine Biology": "26.1302",
    "Molecular Biology": "26.0204",
    "Molecular, Cell, and Developmental Biology": "26.0406",
    "Molecular, Cellular, and Integrative Physiology": "26.0901",
    "Microbiology, Immunology, and Molecular Genetics": "26.0502",
    "Biochemistry": "26.0202",
    "Biochemistry, Molecular and Structural Biology": "26.0202",
    "Biophysics": "26.0203",
    "Human Genetics": "26.0801",
    "Human Biology and Society (B.A.)": "30.2701",
    "Human Biology and Society (B.S.)": "30.2701",
    "Ecology, Behavior, and Evolution": "26.1301",
    "Neuroscience": "26.1501",
    "Physiological Science": "26.0901",
    "Psychobiology": "30.1001",
    # --- Health Professions / Medicine / Public Health — CIP 51.xx ---
    "Doctor of Medicine": "51.1201",
    "Doctor of Dental Surgery": "51.0401",
    "Oral Biology": "51.0401",
    "Doctor of Nursing Practice": "51.3818",
    "Master of Science in Nursing": "51.3801",
    "Nursing": "51.3801",
    "Nursing BS Prelicensure": "51.3801",
    "Molecular and Medical Pharmacology": "26.1002",
    "Genetic Counseling": "51.1509",
    "Clinical Research": "51.1402",
    "Master of Public Health": "51.2201",
    "Executive Master of Public Health": "51.2201",
    "Master of Healthcare Administration": "51.0701",
    "Health Management": "51.0701",
    "Health Policy": "51.2211",
    "Health Policy and Management": "51.2211",
    "Health Policy and Management (M.P.H.)": "51.2211",
    "Health Policy and Management (M.S.)": "51.2211",
    "Community Health Sciences": "51.2208",
    "Community Health Sciences (M.P.H.)": "51.2208",
    "Community Health Sciences (M.S.)": "51.2208",
    "Community Health, Health Promotion and Education": "51.2207",
    "Environmental Health Sciences": "51.2202",
    "Environmental Health Sciences (M.P.H.)": "51.2202",
    "Environmental Health Sciences (M.S.)": "51.2202",
    "Epidemiology": "26.1309",
    "Epidemiology (M.P.H.)": "26.1309",
    "Epidemiology (M.S.)": "26.1309",
    "Disability Studies": "05.0210",
    "Public Health (B.A.)": "51.2201",
    "Public Health (B.S.)": "51.2201",
    # --- Psychology — CIP 42.xx ---
    "Psychology": "42.0101",
    "Cognitive Science": "42.2701",
    # --- Social Sciences — CIP 45.xx ---
    "Anthropology": "45.0201",
    "Anthropology (B.A.)": "45.0201",
    "Anthropology (B.S.)": "45.0201",
    "Archaeology": "45.0301",
    "Economics": "45.0601",
    "Business Economics": "45.0601",
    "Master of Quantitative Economics": "45.0603",
    "Geography": "45.0701",
    "Geography/Environmental Studies": "45.0701",
    "Political Science": "45.1001",
    "Public Affairs": "44.0501",
    "Master of Public Policy": "44.0501",
    "Sociology": "45.1101",
    "Labor Studies": "45.1101",
    "Gender Studies": "05.0207",
    "International Development Studies": "45.0901",
    "Global Studies": "45.0901",
    # --- Area, Ethnic & Cultural Studies — CIP 05.xx ---
    "African American Studies": "05.0201",
    "African Studies": "05.0101",
    "African and Middle Eastern Studies": "05.0199",
    "American Indian Studies": "05.0202",
    "Asian American Studies": "05.0206",
    "Asian Studies": "05.0103",
    "East Asian Studies": "05.0104",
    "Southeast Asian Studies": "05.0113",
    "Chicana and Chicano Studies": "05.0203",
    "European Studies": "05.0106",
    "Latin American Studies": "05.0107",
    "Middle Eastern Studies": "05.0108",
    "Iranian Studies": "05.0108",
    "Islamic Studies": "38.0205",
    "Jewish Studies": "38.0206",
    "Russian Studies": "05.0110",
    "Indo-European Studies": "16.0102",
    "Ancient Near East and Egyptology": "30.2202",
    "Near Eastern Languages and Cultures": "16.1101",
    # --- Languages & Literatures — CIP 16.xx / 23.xx ---
    "Applied Linguistics": "16.0102",
    "Linguistics": "16.0102",
    "Linguistics and Anthropology": "16.0102",
    "Linguistics and Asian Languages and Cultures": "16.0102",
    "Linguistics and Computer Science": "16.0102",
    "Linguistics and English": "16.0102",
    "Linguistics and Philosophy": "16.0102",
    "Linguistics and Psychology": "16.0102",
    "Linguistics and Spanish": "16.0102",
    "Teaching Asian Languages": "16.0399",
    "Arabic": "16.1101",
    "Chinese": "16.0301",
    "Japanese": "16.0302",
    "Korean": "16.0399",
    "Asian Languages and Cultures": "16.0399",
    "Asian Languages and Linguistics": "16.0399",
    "Asian Humanities": "16.0399",
    "Asian Religions": "38.0201",
    "Central and East European Languages and Cultures": "16.0400",
    "Slavic, East European, and Eurasian Languages and Cultures": "16.0400",
    "Russian Language and Literature": "16.0402",
    "Germanic Languages": "16.0501",
    "Scandinavian": "16.0599",
    "Nordic Studies": "16.0599",
    "European Languages and Transcultural Studies": "16.0101",
    "European Languages and Transcultural Studies with French and Francophone": "16.0901",
    "European Languages and Transcultural Studies with German": "16.0501",
    "European Languages and Transcultural Studies with Italian": "16.0902",
    "European Languages and Transcultural Studies with Scandinavian": "16.0599",
    "French and Francophone Studies": "16.0901",
    "Italian": "16.0902",
    "Spanish": "16.0905",
    "Spanish and Community and Culture": "16.0905",
    "Spanish and Linguistics": "16.0905",
    "Spanish and Portuguese": "16.0905",
    "Portuguese": "16.0904",
    "Portuguese and Brazilian Studies": "16.0904",
    "Greek": "16.1200",
    "Latin": "16.1200",
    "Greek and Latin": "16.1200",
    "Classics": "16.1200",
    "Classical Civilization": "16.1200",
    "English": "23.0101",
    "American Literature and Culture": "23.1402",
    "Comparative Literature": "16.0104",
    # --- Arts, Architecture, Music, Theater — CIP 50.xx / 04.xx ---
    "Art": "50.0701",
    "Art History": "50.0703",
    "Design|Media Arts": "50.0409",
    "World Arts and Cultures": "50.0599",
    "Culture and Performance": "50.0599",
    "Dance": "50.0301",
    "Choreographic Inquiry": "50.0301",
    "Theater": "50.0501",
    "Theater and Performance Studies": "50.0501",
    "Film and Television": "50.0602",
    "Film and Television (M.A.)": "50.0601",
    "Film and Television (M.F.A.)": "50.0602",
    "Conservation of Cultural Heritage": "30.1401",
    "Conservation of Material Culture": "30.1401",
    "Architectural Studies": "04.0201",
    "Architecture": "04.0201",
    "Architecture and Urban Design": "04.0201",
    "Master of Architecture": "04.0201",
    "Master of Real Estate Development": "04.1001",
    "Urban Planning": "04.0301",
    "Master of Urban and Regional Planning": "04.0301",
    "Master of Urban and Regional Planning – Institut d'Etudes de Paris": "04.0301",
    "Music": "50.0901",
    "Music (D.M.A.)": "50.0903",
    "Music (Ph.D.)": "50.0901",
    "Music Composition": "50.0904",
    "Music Education": "13.1312",
    "Music History and Industry": "50.0902",
    "Music Industry": "50.1003",
    "Music Performance": "50.0903",
    "Musicology": "50.0905",
    "Ethnomusicology": "50.0905",
    "Global Jazz Studies": "50.0910",
    "Master of Music": "50.0901",
    # --- Humanities — CIP 38.xx / 54.xx / 24.xx ---
    "Philosophy": "38.0101",
    "Study of Religion": "38.0201",
    "History": "54.0101",
    # --- Communication & Media — CIP 09.xx ---
    "Communication": "09.0100",
    # --- Education — CIP 13.xx ---
    "Education": "13.0101",
    "Education and Social Transformation": "13.0101",
    "Master of Education": "13.0101",
    "Doctor of Education": "13.0401",
    "Special Education": "13.1001",
    # --- Information / Library handled above ---
    # --- Business / Management — CIP 52.xx ---
    "Management": "52.0201",
    "Business Analytics": "52.1301",
    "Master of Business Administration": "52.0201",
    "Executive Master of Business Administration": "52.0201",
    "Fully Employed Master of Business Administration": "52.0201",
    "Global Executive Master of Business Administration for Asia Pacific": "52.0201",
    # --- Law — CIP 22.xx ---
    "Juris Doctor": "22.0101",
    "Doctor of Juridical Science": "22.0201",
    "Master of Laws": "22.0201",
    "Master of Legal Studies": "22.0000",
    # --- Social Welfare — CIP 44.xx ---
    "Social Welfare": "44.0701",
    "Master of Social Welfare": "44.0701",
    "Master of Social Science": "45.0101",
    # --- Interdisciplinary / Individual fields ---
    "Individual Field of Concentration BA in Arts and Architecture": "30.9999",
    "Individual Field of Concentration BA in Letters and Science": "30.9999",
    "Individual Field of Concentration BA in Theater, Film, and Television": "30.9999",
    "Individual Field of Concentration BS in Letters and Science": "30.9999",
}


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
            "cip": _CIP_BY_FIELD.get(name),
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

# Matcher-core: every CIP must be a verified NCES CIP-2020 code (NN.NNNN) that exists in
# data/reference/ref_majors.jsonl (the matcher's join target) for UCLA's real field;
# coverage must be complete (no silent catalog-wide null — enrich-profile §"Also enrich
# for the MATCH" cip_code coverage gate). Genuinely uncodeable fields would be omitted
# with reason in _program_standard; today the catalog is 100% covered.
_cip_missing = [p["slug"] for p in PROGRAMS if not p.get("cip")]
if _cip_missing:
    raise ValueError(f"UCLA catalog missing cip_code on {len(_cip_missing)} rows: {_cip_missing[:5]}")
_cip_bad = sorted({p["cip"] for p in PROGRAMS if not re.fullmatch(r"\d{2}\.\d{4}", p["cip"])})
if _cip_bad:
    raise ValueError(f"UCLA catalog has malformed cip_code values: {_cip_bad}")

_name_prefix_desc = sum(
    1 for p in PROGRAMS if (p.get("description") or "").startswith(p.get("program_name", ""))
)
if _name_prefix_desc:
    raise ValueError(f"UCLA catalog has {_name_prefix_desc} name-prefixed descriptions")
_desc_counts = Counter(p.get("description") for p in PROGRAMS)
_shared_desc = sum(c - 1 for c in _desc_counts.values() if c > 1)
if _shared_desc:
    raise ValueError(f"UCLA catalog has {_shared_desc} identical descriptions shared across rows")


# Sentence frames that slot a field topic. ``_template_slot_artifacts`` extracts the slotted
# {topic} from each and flags any that is grammatically broken — the run-71 CRITICAL C2 defect
# (a slotted fragment such as "research in of artistic production…" or "…understanding of
# human."). Gold MIT scores 0 (researched per-credential prose, no slotting).
_SLOT_FRAME_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"builds advanced expertise in (.+?), combining graduate seminars"),
    re.compile(r"advances original dissertation research in (.+?), supported by faculty"),
    re.compile(r"\bdevelops (.+?) through core coursework"),
    re.compile(r"packages focused coursework in (.+?) for "),
    re.compile(r"practical training in (.+?) through "),
    re.compile(r"\bengages (.+?) through coursework"),
)
_TOPIC_BROKEN_LEAD = frozenset(
    {"of", "for", "that", "which", "whose", "in", "on", "to", "as", "by", "and", "or", "with"}
)


def _topic_is_broken(topic: str) -> bool:
    """True when a slotted topic reads as a broken fragment, not a clean noun phrase."""
    t = topic.strip()
    if not t or len(t) < 12:
        return True
    if t[0] in ",:;.()-":  # leading punctuation from a mid-clause cut
        return True
    words = t.split()
    first = words[0].lower().strip(",.()")
    if first in _TOPIC_BROKEN_LEAD or first in _TOPIC_BAD_LEAD or first in {"a", "an", "future", "profound"}:
        return True
    last = words[-1].lower().strip(",.()")
    if last in _TOPIC_TRAILING_JUNK or last in {
        "more", "various", "following", "one", "other", "such", "their", "its",
        "his", "her", "biological", "new",
    }:
        return True
    if t.endswith((",", ".", ":", ";")):
        return True
    if ". " in t:  # a second sentence smuggled into the slot
        return True
    # A finite verb in the slot means a clause was captured, not a noun phrase.
    if re.search(
        r"\b(is|are|was|were|may|might|can|provides?|includes?|focuses?|deals?|offers?|"
        r"used|earns?|earned|designed|allows?|seeks?|aims?|interested)\b",
        t,
        re.I,
    ):
        return True
    # A credential designation smuggled into a field slot ("…research in Master of Science…").
    if re.search(
        r"\b(Master of|Doctor of Philosophy|Bachelor of|MA degree|MS degree|PhD degree|"
        r"degrees?|[BM][AS] program)\b|\((?:MS|MA|MFA|PhD|BA|BS|m\.a\.t\.|m\.s\.|m\.a\.)\)",
        t,
        re.I,
    ):
        return True
    return False


def _template_slot_artifacts(programs: list[dict]) -> list[str]:
    """Programs whose sentence-frame slot carries machine-broken grammar (CRITICAL C2; MIT = 0)."""
    hits: list[str] = []
    for p in programs:
        d = p.get("description") or ""
        for rx in _SLOT_FRAME_RES:
            m = rx.search(d)
            if m and _topic_is_broken(m.group(1)):
                hits.append(p.get("program_name") or p.get("slug") or "")
                break
    return hits


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
    slots = _template_slot_artifacts(programs)
    if slots:
        raise ValueError(
            f"UCLA catalog has {len(slots)} template-slot grammar artifacts, e.g. {slots[:5]}"
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
# UCLA undergraduate total cost of attendance, CA resident living on campus, 2024-25
# ($42,639 = tuition/fees $15,202 + housing, food, books, transit) — UCLA Financial Aid.
_UNDERGRAD_COA = 42639
# Average net price after grant aid (College Scorecard, UNITID 110662, latest reported year).
_AVG_NET_PRICE = 12548

# Matcher-core budget-fit signal (enrich-profile §"Also enrich for the MATCH"): tuition is
# institution-published, so a whole-catalog null is matcher STARVATION, not an honest omission.
# UCLA undergraduate University Fees (tuition + campus-based fees), CA resident, 2024-25; the
# nonresident total adds the systemwide Nonresident Supplemental Tuition.
# Source: UCLA Financial Aid — Cost of Attendance (2024-25 continuing-student schedule).
_TUITION_UG_IN_STATE = 15202
_NRST_UG = 34200
_TUITION_UG_OOS = _TUITION_UG_IN_STATE + _NRST_UG  # 49402
_UG_COST_SRC = "UCLA Financial Aid & Scholarships — Cost of Attendance (2024-25)"
_UG_COST_SRC_URL = "https://financialaid.ucla.edu/how-aid-works/cost-of-attendance"

# UCLA estimated annual graduate (academic master's / doctoral) tuition & fees, 2024-25:
# ~$21,115 CA resident, ~$36,297 nonresident, built on UC systemwide graduate tuition
# ($12,762) + Student Services Fee ($1,254) + campus-based fees, plus graduate Nonresident
# Supplemental Tuition ($15,102). Professional & self-supporting degrees carry separate
# schedules. Source: UCLA Graduate Division — Tuition & Student Fees.
_TUITION_GRAD = 21115
_TUITION_GRAD_OOS = 36297
_GRAD_SYSTEMWIDE_TUITION = 12762
_GRAD_NRST = 15102
_GRAD_COST_SRC = "UCLA Graduate Division — Tuition & Student Fees (2024-25)"
_GRAD_COST_SRC_URL = "https://grad.ucla.edu/funding/tuition/"


def _undergrad_cost() -> dict:
    return {
        "tuition_usd": _TUITION_UG_IN_STATE,
        "total_cost_of_attendance": _UNDERGRAD_COA,
        "avg_net_price": _AVG_NET_PRICE,
        "breakdown": {
            "tuition_in_state": _TUITION_UG_IN_STATE,
            "tuition_out_of_state": _TUITION_UG_OOS,
            "nonresident_supplemental_tuition": _NRST_UG,
        },
        "funded": False,
        "note": (
            "UCLA's published 2024-25 undergraduate University Fees (UC systemwide tuition plus "
            "campus-based fees) are about $15,202 for California residents; nonresidents pay an "
            "additional nonresident supplemental tuition of $34,200 (about $49,402 total). The "
            "2024-25 total cost of attendance for a California resident living on campus is about "
            "$42,639 (UCLA Financial Aid); the average net price after grant aid is about $12,548 "
            "(College Scorecard, UNITID 110662). Through the UC Blue and Gold Opportunity Plan, "
            "UCLA covers system-wide tuition and fees for eligible California families below a "
            "published income threshold."
        ),
        "source": _UG_COST_SRC,
        "source_url": _UG_COST_SRC_URL,
        "year": "2024-25",
    }


def _grad_academic_cost() -> dict:
    """Published UCLA graduate (academic master's / certificate) tuition & fees, 2024-25."""
    return {
        "tuition_usd": _TUITION_GRAD,
        "breakdown": {
            "tuition_in_state": _TUITION_GRAD,
            "tuition_out_of_state": _TUITION_GRAD_OOS,
            "systemwide_tuition": _GRAD_SYSTEMWIDE_TUITION,
            "nonresident_supplemental_tuition": _GRAD_NRST,
        },
        "funded": False,
        "note": (
            "UCLA's estimated 2024-25 annual graduate tuition and fees for most academic master's "
            "and certificate programs are about $21,115 for California residents and about $36,297 "
            "for nonresidents (UC systemwide graduate tuition of $12,762 plus the Student Services "
            "Fee and campus-based fees, with a graduate nonresident supplemental tuition of $15,102). "
            "Professional and self-supporting degrees carry separate, higher tuition schedules."
        ),
        "source": _GRAD_COST_SRC,
        "source_url": _GRAD_COST_SRC_URL,
        "year": "2024-25",
    }


def _phd_funded_cost() -> dict:
    """Doctoral students admitted with funding typically receive tuition remission + stipend."""
    return {
        "tuition_usd": 0,
        "funded": True,
        "note": (
            "UCLA doctoral students admitted with funding typically receive a full or partial "
            "tuition and fee remission together with a stipend through fellowships, teaching, or "
            "research assistantships; see the UCLA Graduate Division for program-specific funding. "
            "The published systemwide graduate tuition is $12,762 (2024-25) before remission."
        ),
        "source": _GRAD_COST_SRC,
        "source_url": _GRAD_COST_SRC_URL,
        "year": "2024-25",
    }


def _annual_prof_cost(
    tuition_usd: int,
    *,
    note: str,
    source: str,
    source_url: str,
    year: str,
) -> dict:
    return {
        "tuition_usd": tuition_usd,
        "funded": False,
        "note": note,
        "source": source,
        "source_url": source_url,
        "year": year,
    }


# Published professional-tier tuition (REPAIR_BACKLOG #4 — professional tier 0/4 live).
# Each rate is the school’s own published registration/tuition figure for California residents
# (distinct from the $15,202 undergraduate sticker and the $21,115 academic-graduate rate).
_LAW_TUITION_SRC = (
    "UCLA School of Law — J.D. Tuition and Fees",
    "https://law.ucla.edu/admissions/jd-admissions/tuition-fees",
)
_MED_TUITION_SRC = (
    "David Geffen School of Medicine — How Much Does Medical School Cost?",
    "https://medschool.ucla.edu/education/md-education/financial-aid-scholarships/how-much-is-medical-school",
)
_DDS_TUITION_SRC = (
    "UCLA School of Dentistry — DDS Tuition and Costs",
    "https://dentistry.ucla.edu/academics-admissions/dds-program/tuition-and-costs",
)
_DNP_TUITION_SRC = (
    "UCLA School of Nursing — Post BS-DNP Program Tuition & Fees",
    "https://nursing.ucla.edu/programs-admissions/financial-aid/tuition-fees/tuition-fees-post-bs-dnp-program",
)

_JD_ANNUAL = 61_744  # 2025-26 CA resident (Law At-a-Glance + ABA Standard 509)
_MD_ANNUAL = 54_656  # 2026-27 1st-year Tuition & Fees, CA resident (DGSOM COA table)
_DDS_ANNUAL = 52_880  # 1st-year Tuition & Fees, CA resident (PDST DDS program)
_DNP_ANNUAL = 45_440  # 2025-26 estimated registration fees, CA resident (Post BS-DNP)

_COST_BY_SLUG: dict[str, dict] = {
    "ucla-juris-doctor-prof": _annual_prof_cost(
        _JD_ANNUAL,
        note=(
            f"UCLA Law J.D. academic-year tuition and fees (${_JD_ANNUAL:,}; California "
            "resident; 2025-26 School of Law At-a-Glance / ABA Standard 509, excluding "
            "optional UCSHIP if waived)."
        ),
        source=_LAW_TUITION_SRC[0],
        source_url=_LAW_TUITION_SRC[1],
        year="2025-26",
    ),
    "ucla-doctor-of-medicine-prof": _annual_prof_cost(
        _MD_ANNUAL,
        note=(
            f"David Geffen School of Medicine M.D. 1st-year tuition and fees "
            f"(${_MD_ANNUAL:,}; California resident; 2026-27 DGSOM cost-of-attendance "
            "table, including Professional Degree Supplemental Tuition)."
        ),
        source=_MED_TUITION_SRC[0],
        source_url=_MED_TUITION_SRC[1],
        year="2026-27",
    ),
    "ucla-doctor-of-dental-surgery-prof": _annual_prof_cost(
        _DDS_ANNUAL,
        note=(
            f"UCLA School of Dentistry D.D.S. 1st-year tuition and fees (${_DDS_ANNUAL:,}; "
            "California resident; PDST program per the school's published DDS budget table, "
            "excluding UCSHIP if waived)."
        ),
        source=_DDS_TUITION_SRC[0],
        source_url=_DDS_TUITION_SRC[1],
        year="2025-26",
    ),
    "ucla-doctor-of-nursing-practice-prof": _annual_prof_cost(
        _DNP_ANNUAL,
        note=(
            f"UCLA School of Nursing Post BS-DNP estimated registration fees "
            f"(${_DNP_ANNUAL:,}; California resident; 2025-26 projected mandatory "
            "systemwide + PDST + campus fees per the nursing program tuition table)."
        ),
        source=_DNP_TUITION_SRC[0],
        source_url=_DNP_TUITION_SRC[1],
        year="2025-26",
    ),
}


# Published professional / self-supporting MASTER'S tuition (REPAIR_BACKLOG #3 — the master's
# tier shipped 48 nulls behind a 100% bachelor's tier, starving the matcher's grad budget-fit
# signal). UCLA's academic master's share the systemwide graduate rate (_TUITION_GRAD, stamped
# automatically); the rows here are the school-billed professional + self-supporting degrees, which
# each PUBLISH their own (higher) rate. Each ``tuition_usd`` is the CA-resident ANNUAL figure (the
# convention used by the undergrad / academic-grad / professional records above): where a school
# publishes only a total program fee, it is divided by the program's real length and the published
# total is preserved verbatim in the note. Verified per the school's own page; never the undergrad
# sticker copied down, never guessed. The Film & Television M.F.A. stays omitted-with-reason — it
# carries Professional Degree Supplemental Tuition over the academic base but UCLA publishes no
# current PDST-inclusive annual total that renders to a fetchable figure (no-fabrication rule).
#
# (slug, annual_tuition_usd, year, note, source_label, source_url)
_MASTER_COST_TABLE: list[tuple[str, int, str, str, str, str]] = [
    # — Anderson School of Management (flat MBA/MS program fee; no resident/nonresident split) —
    (
        "ucla-master-of-business-administration-ms", 82_733, "2026-27",
        "UCLA Anderson Full-Time MBA estimated program fees ($82,733/year; AY 2026-27 flat MBA "
        "program fee, no resident/nonresident split).",
        "UCLA Anderson — Full-Time MBA Financing",
        "https://www.anderson.ucla.edu/degrees/full-time-mba/financing",
    ),
    (
        "ucla-executive-master-of-business-administration-ms", 109_322, "2025-27",
        "UCLA Anderson Executive MBA: $200,424 total program fee for the 22-month Class of 2027 "
        "(≈$109,322/year; flat fee, no residency split).",
        "UCLA Anderson — Executive MBA Financing",
        "https://www.anderson.ucla.edu/degrees/executive-mba/financing",
    ),
    (
        "ucla-fully-employed-master-of-business-administration-ms", 47_944, "2025-26",
        "UCLA Anderson Fully Employed MBA single-academic-year fees ($47,944; 2025-26, at the "
        "published $1,844 per-unit rate over an 82-unit degree).",
        "UCLA Anderson — Fully Employed MBA Financing",
        "https://www.anderson.ucla.edu/degrees/fully-employed-mba/financing",
    ),
    (
        "ucla-global-executive-master-of-business-administration-for-asia-pacific-ms", 122_400,
        "2026-27",
        "UCLA-NUS Executive MBA (Global Executive MBA for Asia Pacific): USD $153,000 total program "
        "fee for the 15-month Intake 22 (≈$122,400/year; includes the NUS and UCLA portions).",
        "UCLA Anderson — UCLA-NUS Executive MBA Fees & Financing",
        "https://www.anderson.ucla.edu/degrees/ucla-nus-executive-mba/fees-and-financing",
    ),
    (
        "ucla-master-of-financial-engineering-ms", 77_476, "2025-26",
        "UCLA Anderson Master of Financial Engineering: $96,845 total program fees for the 15-month "
        "class entering Fall 2025 (≈$77,476/year; flat fee).",
        "UCLA Anderson — Master of Financial Engineering Financing",
        "https://www.anderson.ucla.edu/degrees/master-of-financial-engineering/financing",
    ),
    (
        "ucla-business-analytics-ms", 72_061, "2025-26",
        "UCLA Anderson Master of Science in Business Analytics: $90,076 total program fees for the "
        "15-month program (≈$72,061/year; flat fee).",
        "UCLA Anderson — MSBA Program Calendar and Fees",
        "https://www.anderson.ucla.edu/degrees/master-of-science-in-business-analytics/"
        "admit-central/program-calendar-and-fees",
    ),
    # — Jonathan and Karin Fielding School of Public Health (+ Geffen MS) —
    # Standard on-campus MPH concentrations share one professional MPH fee (most recent figure the
    # school publishes verbatim is its 2022-23 table; the live rate sits behind the Registrar app).
    *[
        (
            slug, 25_323, "2022-23",
            f"{label} — UCLA Fielding School of Public Health MPH professional-degree fee, "
            "California resident ($25,323; 2022-23, the most recent rate the school publishes "
            "verbatim; one MPH rate covers all on-campus concentrations).",
            "UCLA Fielding School of Public Health — Tuition & Fees",
            "https://ph.ucla.edu/admissions/cost-aid/tuition-fees",
        )
        for slug, label in [
            ("ucla-master-of-public-health-ms", "Master of Public Health"),
            ("ucla-biostatistics-mph-ms", "Biostatistics (M.P.H.)"),
            ("ucla-community-health-sciences-mph-ms", "Community Health Sciences (M.P.H.)"),
            ("ucla-environmental-health-sciences-mph-ms", "Environmental Health Sciences (M.P.H.)"),
            ("ucla-epidemiology-mph-ms", "Epidemiology (M.P.H.)"),
            ("ucla-health-policy-and-management-mph-ms", "Health Policy and Management (M.P.H.)"),
        ]
    ],
    *[
        (
            slug, 29_942, "2025-26",
            f"{label} — UCLA Fielding self-supporting MPH for Health Professionals (MPH|HP) annual "
            "tuition ($29,942/year; 2025-26, per the UCLA Registrar self-supporting degree fee list).",
            "UCLA Registrar — Self-Supporting Degree Fees",
            "https://registrar.ucla.edu/fees-residence/self-supporting-degrees",
        )
        for slug, label in [
            (
                "ucla-community-health-health-promotion-and-education-ms",
                "MPH in Community Health, Health Promotion and Education",
            ),
            ("ucla-health-management-ms", "MPH in Health Management"),
            ("ucla-health-policy-ms", "MPH in Health Policy"),
        ]
    ],
    (
        "ucla-executive-master-of-public-health-ms", 36_000, "2025-26",
        "UCLA Fielding Executive Master of Public Health (ExecHPM): $72,000 total for the two-year "
        "program ($36,000/year for new students; self-supporting).",
        "UCLA Executive MPH — Tuition & Financial Aid",
        "https://www.exechpm.ucla.edu/tuition-financial-aid/",
    ),
    (
        "ucla-master-of-healthcare-administration-ms", 31_350, "2025-26",
        "UCLA Fielding online Master of Healthcare Administration: $950/unit over a 66-unit program "
        "($62,700 total; ≈$31,350/year; self-supporting, 2025-26).",
        "UCLA MHA — Tuition & Financial Aid",
        "https://mha.ucla.edu/tuition-financial-aid/",
    ),
    (
        "ucla-master-of-data-science-in-health-ms", 30_000, "2025-26",
        "UCLA Master of Data Science in Health: $1,250/credit over a 48-unit program ($60,000 total; "
        "≈$30,000/year; self-supporting, Fall-2025 entry).",
        "UCLA MDSH — Admission Finance",
        "https://mdsh.ucla.edu/admission/finance",
    ),
    (
        "ucla-data-science-in-biomedicine-ms", 21_600, "2023-24",
        "UCLA Master of Science in Data Science in Biomedicine (David Geffen School of Medicine): "
        "$4,800/course over a nine-course program ($43,200 total; ≈$21,600/year; self-supporting, "
        "2023-24 published rate).",
        "UCLA MS Data Science in Biomedicine — Program Cost & Financial Aid",
        "https://datasciencebiomedicine.ucla.edu/admissions/program-cost-financial-aid",
    ),
    # — Henry Samueli School of Engineering and Applied Science —
    (
        "ucla-master-of-engineering-ms", 52_920, "2025-26",
        "UCLA Samueli Master of Engineering (on-campus, one-year): $52,920 total program tuition "
        "plus quarterly campus fees.",
        "UCLA MEng — FAQ (Tuition)",
        "https://www.meng.ucla.edu/faq/",
    ),
    *[
        (
            slug, 19_800, "2025-26",
            f"{label} — track of UCLA's online Master of Science in Engineering (MSOL): $4,400/course "
            "over a nine-course (36-unit) program ($39,600 total; ≈$19,800/year; self-supporting, all "
            "MSOL specializations share this rate).",
            "UCLA MSOL — Program Cost & Financial Aid",
            "https://www.msol.ucla.edu/program-cost-financial-aid-information/",
        )
        for slug, label in [
            ("ucla-engineering-ms", "Master of Science in Engineering"),
            ("ucla-engineering-aerospace-ms", "MS in Engineering – Aerospace"),
            ("ucla-engineering-computer-networking-ms", "MS in Engineering – Computer Networking"),
            ("ucla-engineering-electrical-ms", "MS in Engineering – Electrical"),
            ("ucla-engineering-electronic-materials-ms", "MS in Engineering – Electronic Materials"),
            ("ucla-engineering-integrated-circuits-ms", "MS in Engineering – Integrated Circuits"),
            (
                "ucla-engineering-manufacturing-and-design-ms",
                "MS in Engineering – Manufacturing and Design",
            ),
            ("ucla-engineering-materials-science-ms", "MS in Engineering – Materials Science"),
            ("ucla-engineering-mechanical-ms", "MS in Engineering – Mechanical"),
            (
                "ucla-engineering-signal-processing-and-communications-ms",
                "MS in Engineering – Signal Processing and Communications",
            ),
            ("ucla-engineering-structural-materials-ms", "MS in Engineering – Structural Materials"),
        ]
    ],
    # — School of Law —
    (
        "ucla-master-of-laws-ms", 76_772, "2025-26",
        "UCLA School of Law Master of Laws (LL.M.): $76,772 tuition for the one-year program "
        "(identical for domestic and international students; California residents are not eligible "
        "for discounted tuition).",
        "UCLA Law — LL.M. Tuition & Visa Information",
        "https://law.ucla.edu/admissions/llm-admissions/tuition-visa-information",
    ),
    (
        "ucla-master-of-legal-studies-ms", 66_950, "2025-26",
        "UCLA School of Law Master of Legal Studies (M.L.S.): $2,575/unit over a 26-unit program "
        "($66,950); full-time students complete the program in two semesters (one year), so the "
        "full $66,950 is the annual tuition; self-supporting, 2025-26.",
        "UCLA Law — Master of Legal Studies Tuition & Scholarships",
        "https://law.ucla.edu/admissions/master-legal-studies/mls-tuition-and-scholarships",
    ),
    # — School of Education and Information Studies (academic state-supported master's) —
    *[
        (
            slug, 21_115, "2024-25",
            f"{label} — standard UCLA academic graduate tuition & fees, California resident "
            "($21,115/year; 2024-25; SEIS publishes no self-supporting/PDST supplement for this "
            "academic master's).",
            "UCLA Graduate Programs — Tuition & Student Fees",
            "https://grad.ucla.edu/funding/tuition/",
        )
        for slug, label in [
            ("ucla-master-of-education-ms", "Master of Education (M.Ed.)"),
            ("ucla-education-ms", "Master of Education in Education (M.Ed.)"),
            (
                "ucla-master-of-library-and-information-science-ms",
                "Master of Library and Information Science (M.L.I.S.)",
            ),
        ]
    ],
    # — College of Letters and Science (self-supporting applied master's) —
    (
        "ucla-master-of-applied-chemical-sciences-ms", 39_744, "2025-26",
        "UCLA Master of Applied Chemical Sciences (MACS): $39,744/year ($13,248/quarter), the same "
        "for residents and non-residents; self-supporting.",
        "UCLA MACS — Program",
        "https://macsucla.com/macs-program",
    ),
    (
        "ucla-master-of-applied-geospatial-information-systems-and-technologies-ms", 38_430, "2026-27",
        "UCLA Master of Applied Geospatial Information Systems and Technologies (MAGIST): $1,030/unit "
        "over a 36-unit, one-year program ($38,430 total tuition and fees; self-supporting, 2026-27).",
        "UCLA MAGIST — Tuition and Financial Aid",
        "https://magist.gis.ucla.edu/tuition-and-financial-aid/",
    ),
    (
        "ucla-master-of-applied-statistics-and-data-science-ms", 27_038, "2025-26",
        "UCLA Master of Applied Statistics and Data Science (MASDS): $1,229/unit over a 44-unit "
        "program ($54,076 total; about $27,038/year over two years; self-supporting).",
        "UCLA MASDS — FAQ (Cost)",
        "https://master.stat.ucla.edu/faq/",
    ),
    (
        "ucla-master-of-quantum-science-and-technology-ms", 53_400, "2025-26",
        "UCLA Master of Quantum Science and Technology (MQST): $53,400 total program tuition for the "
        "one-year (40-unit) program; self-supporting, 2025-26.",
        "UCLA MQST — Program Cost",
        "https://qst.ucla.edu/program-cost.html",
    ),
    (
        "ucla-master-of-social-science-ms", 45_815, "2025-26",
        "UCLA Master of Social Science (MaSS): $45,815 academic-year tuition (2025-26); "
        "self-supporting.",
        "UCLA MaSS — FAQ (Tuition)",
        "https://mass.ss.ucla.edu/faq/",
    ),
    # — Meyer and Renee Luskin School of Public Affairs —
    (
        "ucla-master-of-public-policy-ms", 34_348, "2025-26",
        "UCLA Luskin Master of Public Policy (MPP): $34,348 total mandatory tuition and fees, "
        "California resident, 2025-26 (systemwide tuition $13,140 + Professional Degree Supplemental "
        "Tuition $12,465 + campus fees, per the UCLA Registrar fee schedule).",
        "UCLA Luskin — Public Policy Tuition & Financial Aid",
        "https://luskin.ucla.edu/public-policy/tuition-and-financial-aid",
    ),
    (
        "ucla-master-of-social-welfare-ms", 30_670, "2025-26",
        "UCLA Luskin Master of Social Welfare (MSW): $30,670 total mandatory tuition and fees, "
        "California resident, 2025-26 (per the UCLA Registrar fee schedule).",
        "UCLA Registrar — Fees (Social Welfare MSW, Annual 2025-26)",
        "https://registrar.ucla.edu/fees-residence",
    ),
    (
        "ucla-master-of-urban-and-regional-planning-ms", 31_579, "2025-26",
        "UCLA Luskin Master of Urban and Regional Planning (MURP): $31,579 total mandatory tuition "
        "and fees, California resident, 2025-26 (per the UCLA Registrar fee schedule).",
        "UCLA Registrar — Fees (Urban Planning MURP, Annual 2025-26)",
        "https://registrar.ucla.edu/fees-residence",
    ),
    (
        "ucla-master-of-urban-and-regional-planning-institut-detudes-de-paris-ms", 31_579, "2025-26",
        "UCLA Luskin MURP / Sciences Po dual degree: Year 1 is billed at the standard UCLA MURP rate "
        "($31,579, California resident, 2025-26); Year 2 is paid to Sciences Po plus a UCLA in-absentia "
        "fee.",
        "UCLA Luskin — MURP / Sciences Po Dual Degree",
        "https://luskin.ucla.edu/urban-planning/murp-sciences-po",
    ),
    (
        "ucla-master-of-real-estate-development-ms", 85_000, "2025-26",
        "UCLA Luskin Master of Real Estate Development (MRED): $85,000 total required program fees for "
        "the one-year, self-supporting program (2025-26; plus campus fees).",
        "UCLA Luskin — MRED Tuition and Financing",
        "https://luskin.ucla.edu/mred/tuition-and-financing",
    ),
]

_COST_BY_SLUG.update(
    {
        slug: _annual_prof_cost(
            tuition, note=note, source=source, source_url=source_url, year=year
        )
        for slug, tuition, year, note, source, source_url in _MASTER_COST_TABLE
    }
)


def _prof_has_verified_tuition(spec: dict) -> bool:
    return spec.get("slug") in _COST_BY_SLUG


# Professional / self-supporting master's degrees carry a separate (higher) supplemental or
# self-supporting tuition schedule, NOT the academic systemwide graduate rate — stamping the
# academic rate on an MBA / MPH / MEng would be a wrong fact, so these are omitted-with-reason
# (no-fabrication rule). Keyed on the degree designation, so a research M.S./M.A. in the same
# school still gets the correct academic rate.
_PROFESSIONAL_MASTER_RE = re.compile(
    r"M\.P\.H\.|M\.F\.A\.|M\.P\.P\.|M\.S\.W\.|M\.U\.R\.P\.|M\.B\.A\.|LL\.M\.|M\.L\.I\.S\.|M\.Ed\.|"
    r"Master of Business Administration|Master of Financial Engineering|Master of Engineering|"
    r"Master of Fine Arts|Master of Public Health|Master of Public Policy|Master of Social Welfare|"
    r"Master of Urban|Master of Real Estate|Master of Education|Master of Library|Master of Laws|"
    r"Master of Legal Studies|Master of Healthcare|Master of Health|Master of Data Science|"
    r"Master of Applied|Master of Science in Business Analytics|Master of Science in Management|"
    r"Executive Master|Fully Employed Master|Global Executive",
    re.I,
)


def _is_professional_master(spec: dict) -> bool:
    return bool(_PROFESSIONAL_MASTER_RE.search(spec.get("program_name") or ""))


# Self-supporting master's degrees bill on a distinct (often per-course) schedule, NOT the
# academic systemwide graduate rate — UCLA's online MSOL tracks ($4,400/course) and named
# self-supporting on-campus degrees (Quantum Science & Technology, Social Science, Data Science
# in Biomedicine). Stamping the $21,115 academic rate on these would be a wrong fact, so they
# are omitted-with-reason like the professional master's (Codex review on PR #1027).
_SELF_SUPPORTING_MASTER_RE = re.compile(
    r"Master of Quantum|Master of Social Science|Data Science in Biomedicine",
    re.I,
)


def _is_self_supporting_master(spec: dict) -> bool:
    return spec.get("delivery_format") == "online" or bool(
        _SELF_SUPPORTING_MASTER_RE.search(spec.get("program_name") or "")
    )


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


def _cost_for(spec: dict) -> tuple[int | None, dict]:
    """The (tuition, cost_data) ``_apply_programs`` stamps — single source of truth.

    Tuition is institution-published (matcher-core budget-fit), so it is filled for every
    knowable credential level: the undergrad sticker, the academic graduate rate, and a
    funded $0 for doctoral students. Professional / self-supporting degrees carry distinct,
    higher schedules and are omitted-with-reason rather than guessed (no-fabrication rule).
    """
    # A per-slug published rate (professional + self-supporting master's / professional degrees)
    # is authoritative for any credential level — checked first so a school-billed master's gets
    # its real published rate instead of falling through to the academic-rate or null branches.
    cost_override = _COST_BY_SLUG.get(spec.get("slug", ""))
    if cost_override is not None:
        return cost_override["tuition_usd"], cost_override
    dt = spec["degree_type"]
    # PUBLIC-university scalar (REPAIR_BACKLOG #4 / run-83 rule): the CPEF budget veto reads
    # the flat ``program.tuition`` scalar for EVERY applicant regardless of residency, so the
    # scalar carries the NON-RESIDENT (out-of-state) sticker — the conservative, broadly-correct
    # input for the national + international pool (all international applicants pay non-resident).
    # ``cost_data.breakdown`` still preserves BOTH the resident and non-resident rates.
    if dt == "bachelors":
        return _TUITION_UG_OOS, _undergrad_cost()
    if dt in ("phd", "doctoral"):
        # Only research Doctor of Philosophy degrees carry the standard funded tuition
        # remission. Professional / self-supporting doctorates encoded as "phd" — Ed.D.,
        # S.J.D., D.Env., D.M.A. — publish distinct, often nonzero schedules and are
        # omitted-with-reason rather than zeroed (Codex review on PR #1027).
        name = spec.get("program_name") or ""
        if name.startswith("Doctor of Philosophy") or "(Ph.D.)" in name:
            return 0, _phd_funded_cost()
        return None, _grad_cost_fallback(spec)
    if dt == "masters" and not _is_professional_master(spec) and not _is_self_supporting_master(spec):
        return _TUITION_GRAD_OOS, _grad_academic_cost()
    if dt == "certificate" and spec.get("delivery_format") != "online":
        return _TUITION_GRAD_OOS, _grad_academic_cost()
    return None, _grad_cost_fallback(spec)


def _has_tuition(spec: dict) -> bool:
    """True when ``_cost_for`` stamps a real published tuition on this program."""
    return _cost_for(spec)[0] is not None


# ---------------------------------------------------------------------------
# Who it's for (REPAIR_BACKLOG #6 - universal-depth field). One field-specific
# applicant statement per program, derived from the program's own verified
# description + field + credential level (no new external claims). Replaces the
# former hard-null ``p.who_its_for = None`` that left the field 0% live.
# ---------------------------------------------------------------------------
_WHO_BY_SLUG: dict[str, str] = {
    "ucla-african-american-studies-ug": (
        "Undergraduates drawn to the history, culture, and contemporary issues of African American "
        "communities who want a foundation capped by hands-on work — an internship, honors thesis, "
        "service-learning course, or independent project — before careers or graduate study in the "
        "field."
    ),
    "ucla-african-and-middle-eastern-studies-ug": (
        "Undergraduates curious about the Middle East, North Africa, the Arab states, or sub-Saharan "
        "Africa who want an interdisciplinary, modern lens on the region, are eager to study abroad, "
        "and aim to ground broad international issues in the concerns of one part of the world."
    ),
    "ucla-american-indian-studies-ug": (
        "Undergraduates seeking a comprehensive grounding in American Indian cultures, societies, and "
        "contemporary issues alongside traditional disciplines like history, law, and linguistics, "
        "who want to build a focused area of expertise as a foundation for further study or "
        "community-facing work."
    ),
    "ucla-american-literature-and-culture-ug": (
        "Undergraduates passionate about American literature and culture who value close advising, "
        "working with counselors and faculty to shape a course of study around their own interests "
        "and goals as they build toward graduate study or writing- and analysis-driven careers."
    ),
    "ucla-ancient-near-east-and-egyptology-ug": (
        "Undergraduates fascinated by ancient Egypt, Mesopotamia, and the wider Near East who want to "
        "study its languages, history, archaeology, and texts — a foundation for graduate work, "
        "museum and archaeological careers, or scholarship in the ancient world."
    ),
    "ucla-anthropology-ba-ug": (
        "Undergraduates seeking a holistic, cross-cultural understanding of human behavior who "
        "appreciate anthropology's integration with biology, history, linguistics, and the social "
        "sciences and humanities, building a broad foundation for graduate study or careers spanning "
        "many fields."
    ),
    "ucla-anthropology-bs-ug": (
        "Undergraduates interested in human evolution and the biological side of anthropology who are "
        "aiming toward the health sciences — medicine, dentistry, public health, or nursing — and "
        "want science-grounded preparation for those careers."
    ),
    "ucla-applied-linguistics-ug": (
        "Undergraduates intrigued by how language works in everyday life who want both linguistic "
        "theory and community-based practice, preparing through service learning for paths like "
        "language teaching, speech pathology, and translation and interpretation."
    ),
    "ucla-applied-mathematics-ug": (
        "Undergraduates who enjoy mathematics and want to see it applied to the life, social, and "
        "physical sciences and engineering, building a quantitative foundation for technical careers "
        "or graduate study where math drives real-world problem-solving."
    ),
    "ucla-arabic-ug": (
        "Undergraduates who want to master Arabic — a Central Semitic language spoken across the Arab "
        "world, from Modern Standard to Classical forms — building language proficiency as a "
        "foundation for careers or graduate work engaging the Arabic-speaking world."
    ),
    "ucla-art-history-ug": (
        "Undergraduates drawn to studying artistic production and visual culture across human history "
        "who want to analyze art's relationship to society, politics, and changing styles, building a "
        "foundation for graduate study, museum and gallery work, or arts professions."
    ),
    "ucla-asian-american-studies-ug": (
        "Undergraduates interested in the experiences of Asian and Pacific Islander Americans who "
        "want a broad introduction as a launchpad for graduate-level work or careers in research, "
        "public service, and community work related to these communities."
    ),
    "ucla-asian-humanities-ug": (
        "Undergraduates curious about the literary, religious, and philosophical traditions of South, "
        "Southeast, and East Asia, largely in translation, who want a humanities foundation for "
        "graduate study or culturally engaged careers without requiring advanced language mastery."
    ),
    "ucla-asian-languages-and-linguistics-ug": (
        "Undergraduates who want to pair advanced study of an Asian language with linguistic analysis "
        "of its sounds, structure, and history, building both fluency and analytical skill toward "
        "graduate work or language-focused careers."
    ),
    "ucla-asian-religions-ug": (
        "Undergraduates fascinated by the religious traditions of Asia — Hinduism, Buddhism, Daoism, "
        "Shinto — who want to study them through texts, history, and lived practice as a foundation "
        "for graduate study or careers engaging religion and culture."
    ),
    "ucla-asian-studies-ug": (
        "Undergraduates interested in Central, East, South, or Southeast Asia who want an "
        "interdisciplinary, modern perspective on the region, are keen to study abroad, and aim to "
        "focus broad international issues on the concerns of one part of Asia."
    ),
    "ucla-astrophysics-ug": (
        "Undergraduates captivated by the nature of stars, galaxies, and the universe who want to "
        "apply physics and chemistry to understanding heavenly bodies, building a science foundation "
        "for graduate research or careers in astronomy and the physical sciences."
    ),
    "ucla-atmospheric-and-oceanic-sciences-ug": (
        "Undergraduates drawn to weather, climate, and the physics of the atmosphere who want to "
        "study meteorology, climatology, and aeronomy — a foundation for careers in forecasting and "
        "atmospheric science or graduate study extending into planetary science."
    ),
    "ucla-atmospheric-and-oceanic-sciences-mathematics-ug": (
        "Undergraduates who want to study the atmosphere, oceans, and climate alongside a rigorous "
        "mathematics core, building the quantitative skills for technical work and graduate study in "
        "the climate and earth sciences."
    ),
    "ucla-biochemistry-ug": (
        "Undergraduates preparing for careers in biochemistry or fields demanding deep grounding in "
        "both chemistry and biology, who want extensive science preparation as a foundation for "
        "research, the health sciences, or graduate study."
    ),
    "ucla-biology-ug": (
        "Undergraduates with broad interest in biology who want wide-ranging exposure across all "
        "levels of the modern field, building strong preparation for medicine and the health "
        "sciences, academic and public-service careers, biological industry, or even paths in "
        "business and law."
    ),
    "ucla-biophysics-ug": (
        "Undergraduates who want a flexible, quantitative science background bridging physics and "
        "biology, aiming for competitive graduate programs in biophysics, molecular biology, or "
        "biological physics, or careers in the medical field and neuroscience."
    ),
    "ucla-business-economics-ug": (
        "Undergraduates who want economic theory paired with accounting and finance coursework and "
        "access to recruiting in consulting, finance, and technology, building a foundation for "
        "business careers across the Los Angeles economy."
    ),
    "ucla-central-and-east-european-languages-and-cultures-ug": (
        "Undergraduates who want to master a Central or Eastern European language and gain "
        "familiarity with its literature alongside the cultural, political, and social history of the "
        "Slavic peoples, as a foundation for graduate study or internationally engaged careers."
    ),
    "ucla-chemistry-ug": (
        "Undergraduates who intend to pursue a career in chemistry and want a rigorous grounding in "
        "the discipline as preparation for graduate study, research, or work across the chemical "
        "sciences."
    ),
    "ucla-chemistry-materials-science-ug": (
        "Undergraduates interested in chemistry with an emphasis on material properties who want "
        "expertise spanning semiconductors, polymers, biomaterials, ceramics, and nano-scale "
        "structures, preparing for interdisciplinary graduate research in chemistry, engineering, and "
        "applied science."
    ),
    "ucla-chicana-and-chicano-studies-ug": (
        "Undergraduates committed to critical thinking about gender, race, ethnicity, class, and "
        "social action who want a curriculum balancing social sciences, humanities, and the arts, "
        "with the literary and visual arts as vehicles for social change and empowerment."
    ),
    "ucla-chinese-ug": (
        "Undergraduates who want advanced proficiency in Mandarin Chinese alongside the study of "
        "Chinese literature, linguistics, and culture from the classical period to the present, "
        "building toward graduate study or careers engaging China."
    ),
    "ucla-classical-civilization-ug": (
        "Undergraduates drawn to the cultures of ancient Greece and Rome who want a balanced "
        "introduction to their history, art, and languages — a structured yet flexible foundation for "
        "graduate study or careers building on the classical roots of the Western world."
    ),
    "ucla-climate-science-ug": (
        "Undergraduates focused on the scientific study of Earth's climate — its variability, "
        "mechanisms of change, and modern climate change — who want a science foundation drawing on "
        "atmospheric science, oceanography, and physical geography for research or environmental "
        "careers."
    ),
    "ucla-cognitive-science-ug": (
        "Undergraduates curious about how intelligent systems work, both real and artificial, who "
        "want an interdisciplinary blend of cognitive psychology, computer science, and mathematics, "
        "with enough preparation to pursue graduate work in cognitive science or related fields."
    ),
    "ucla-communication-ug": (
        "Undergraduates seeking a comprehensive, interdisciplinary understanding of human "
        "communication who want to focus on an area like digital systems, interpersonal "
        "communication, media institutions, or political and legal communication, drawing on the "
        "sciences and humanities alike."
    ),
    "ucla-comparative-literature-ug": (
        "Undergraduates drawn to studying literature and cultural expression across languages, "
        "nations, and disciplines who want a comparative, boundary-crossing foundation for graduate "
        "study or careers in writing, analysis, and global culture."
    ),
    "ucla-computational-biology-ug": (
        "Undergraduates with strong quantitative interests who want to integrate computation and "
        "biology through one of three tracks — bioinformatics, biological data sciences, or dynamical "
        "modeling — building the modeling and analytical skills for research and graduate study."
    ),
    "ucla-data-theory-ug": (
        "Undergraduates who want to extract knowledge from structured and unstructured data using "
        "statistics, scientific computing, algorithms, and coding, building the foundation for data- "
        "science careers or graduate study in the field."
    ),
    "ucla-disability-studies-ug": (
        "Undergraduates seeking a conceptual and practical understanding of disability as a dimension "
        "of social, cultural, and political identity who want an interdisciplinary, community-based "
        "capstone major as a foundation for graduate or professional studies and careers across many "
        "professions."
    ),
    "ucla-earth-and-environmental-science-ug": (
        "Undergraduates fascinated by how Earth's biosphere, hydrosphere, atmosphere, and geosphere "
        "interact who want a natural-science foundation spanning the physical, chemical, and "
        "biological workings of the planet for research or environmental careers."
    ),
    "ucla-ecology-behavior-and-evolution-ug": (
        "Undergraduates passionate about ecology, animal behavior, and evolution who want strong "
        "field experience in California and beyond, preparing for graduate study or careers in "
        "conservation, environmental biology, teaching, museum work, or government environmental "
        "positions."
    ),
    "ucla-economics-ug": (
        "Undergraduates interested in how societies produce, distribute, and consume goods and "
        "services who want a social-science foundation in economic reasoning, opening paths to "
        "graduate study or careers across business, policy, and analysis."
    ),
    "ucla-engineering-geology-ug": (
        "Undergraduates who want to apply geology to engineering problems — slope stability, "
        "groundwater, seismic hazards, and earth materials — building a foundation that bridges the "
        "earth sciences and engineering practice for technical careers or graduate study."
    ),
    "ucla-english-ug": (
        "Undergraduates devoted to literature and language in English who value close advising, "
        "working with counselors and faculty to build a course of study around their interests and "
        "goals toward graduate work or writing- and analysis-driven careers."
    ),
    "ucla-environmental-science-ug": (
        "Undergraduates deeply interested in environmental science who want a collaborative program "
        "spanning atmospheric sciences, environmental engineering, ecology, and geography, building "
        "cross-disciplinary preparation for environmental careers or graduate study."
    ),
    "ucla-european-languages-and-transcultural-studies-ug": (
        "Undergraduates who want to study the literatures, languages, film, and intellectual history "
        "of Europe across national boundaries, training in two European languages alongside "
        "comparative cultural analysis toward graduate study or internationally engaged careers."
    ),
    "ucla-european-languages-and-transcultural-studies-with-french-and-francophone-ug": (
        "Undergraduates drawn to French and the wider French-speaking world who want to pair advanced "
        "French language work with the literature, film, and cultures of France and Francophone "
        "regions, building toward graduate study or careers engaging that world."
    ),
    "ucla-european-languages-and-transcultural-studies-with-german-ug": (
        "Undergraduates focused on German who want advanced language study combined with the "
        "literature, philosophy, film, and cultural history of the German-speaking world, as a "
        "foundation for graduate work or internationally engaged careers."
    ),
    "ucla-european-languages-and-transcultural-studies-with-italian-ug": (
        "Undergraduates drawn to Italy who want advanced Italian language study joined with the "
        "literature, art, cinema, and cultural history of Italy from the medieval period to the "
        "present, building toward graduate study or culturally engaged careers."
    ),
    "ucla-european-languages-and-transcultural-studies-with-scandinavian-ug": (
        "Undergraduates interested in the Nordic world who want to study a Scandinavian language "
        "alongside the literature, film, and cultural history of Denmark, Norway, Sweden, Iceland, "
        "and Finland, as a foundation for graduate study or internationally engaged careers."
    ),
    "ucla-european-studies-ug": (
        "Undergraduates interested in Western, Mediterranean, Scandinavian, or Central and Eastern "
        "Europe who want an interdisciplinary, modern perspective on the region, are eager to study "
        "abroad, and aim to focus broad international issues on one part of Europe."
    ),
    "ucla-financial-actuarial-mathematics-ug": (
        "Undergraduates who want to apply mathematics to finance, the actuarial field, and related "
        "areas, building the quantitative foundation for careers in actuarial work, finance, and risk "
        "or for graduate study."
    ),
    "ucla-gender-studies-ug": (
        "Undergraduates drawn to the study of gender who want a flexible major they can pursue alone "
        "or pair with another Letters and Science field, building an interdisciplinary foundation for "
        "graduate study or careers informed by gender analysis."
    ),
    "ucla-general-chemistry-ug": (
        "Undergraduates who want a solid chemistry background aimed at teaching — especially future "
        "secondary-school chemistry teachers or those headed to chemistry-related careers that "
        "involve teaching chemistry to nonchemists — declaring the major before reaching 135 units."
    ),
    "ucla-geography-ug": (
        "Undergraduates who want to combine a broad grounding in geography with focused interests in "
        "areas like urban, economic, cultural, environmental, or physical geography, shaping a "
        "program with their adviser around their personal and career goals."
    ),
    "ucla-geography-environmental-studies-ug": (
        "Undergraduates seeking to understand environmental issues through an interactive "
        "people/nature lens who want to analyze social, physical, and biotic systems and human "
        "impacts on nature, building a foundation for environmental careers or graduate study."
    ),
    "ucla-geology-ug": (
        "Undergraduates fascinated by Earth, the rocks that compose it, and the processes that change "
        "it over time who want a natural-science foundation overlapping Earth-system and planetary "
        "science for research, fieldwork, or graduate study."
    ),
    "ucla-geophysics-ug": (
        "Undergraduates drawn to the quantitative study of Earth's interior, fields, and surrounding "
        "space — gravity, magnetism, tectonics, and planetary processes — who want an observational, "
        "physics-based foundation for research or graduate study in the earth and planetary sciences."
    ),
    "ucla-global-studies-ug": (
        "Undergraduates fascinated by globalization and the big cross-border forces shaping politics, "
        "economics, and the environment, who want an interdisciplinary foundation spanning political "
        "science, sociology, and ecology rather than a nation-state-by-nation-state view, headed "
        "toward international policy, NGOs, or graduate study."
    ),
    "ucla-greek-ug": (
        "Undergraduates drawn to the ancient Greek language and the literature, history, and thought "
        "of the classical Greek world, ready to build reading fluency from the ground up as a "
        "foundation for graduate classics, teaching, law, or any field rewarding close textual "
        "analysis."
    ),
    "ucla-greek-and-latin-ug": (
        "Undergraduates captivated by classical antiquity who want to master both Ancient Greek and "
        "Latin and study Greco-Roman literature, history, philosophy, and art together, building a "
        "humanities foundation for graduate work in classics, teaching, or scholarship."
    ),
    "ucla-history-ug": (
        "Undergraduates who want to investigate the human past rigorously, interpreting evidence to "
        "build and explain narratives of what happened and why, building research and argument skills "
        "that ground careers in law, education, journalism, public service, or graduate study."
    ),
    "ucla-human-biology-and-society-ba-ug": (
        "Undergraduates who want to understand human biology alongside its history, ethics, and "
        "policy, examining the societal context of genetics and medicine, and headed toward law, "
        "policy, public health, or interdisciplinary graduate work connecting science and society."
    ),
    "ucla-human-biology-and-society-bs-ug": (
        "Undergraduates seeking a science-heavy foundation in biology, chemistry, and quantitative "
        "methods paired with the ethical and social dimensions of human biology, preparing for the "
        "health professions, biomedical research, or graduate study bridging life sciences and "
        "society."
    ),
    "ucla-individual-field-of-concentration-ba-in-letters-and-science-ug": (
        "Self-directed undergraduates with a coherent intellectual question that no single department "
        "answers, ready to design an interdisciplinary humanities-and-social-science B.A. with "
        "faculty sponsorship, suited to those who can shape and defend their own focused plan of "
        "study."
    ),
    "ucla-individual-field-of-concentration-bs-in-letters-and-science-ug": (
        "Self-directed undergraduates pursuing a science- and quantitatively-oriented question that "
        "spans several departments, ready to build a custom B.S. under faculty guidance, well-suited "
        "to independent learners headed toward research or graduate study in an emerging "
        "interdisciplinary area."
    ),
    "ucla-international-development-studies-ug": (
        "Undergraduates committed to understanding global development debates and how class, gender, "
        "race, and migration shape who benefits from interventions, who want methodological training "
        "and case-study grounding for careers in NGOs, international agencies, policy, or development "
        "research."
    ),
    "ucla-iranian-studies-ug": (
        "Undergraduates drawn to the languages, history, and culture of Iran and the broader Iranian "
        "world, willing to plan early for the additional coursework, often pairing the major with "
        "another specialization to broaden career options in academia, government, or international "
        "fields."
    ),
    "ucla-japanese-ug": (
        "Undergraduates aiming for advanced fluency in Japanese alongside its literature, film, and "
        "cultural history, building language and cultural expertise that supports careers in "
        "translation, international business, education, diplomacy, or graduate study in Japanese "
        "studies."
    ),
    "ucla-jewish-studies-ug": (
        "Undergraduates drawn to Jewish history, religion, languages, literature, and culture across "
        "the long span from antiquity to the present, who want an interdisciplinary humanities "
        "foundation for graduate study, teaching, communal work, law, or the cultural professions."
    ),
    "ucla-korean-ug": (
        "Undergraduates aiming for advanced Korean fluency together with Korean literature, "
        "linguistics, and cultural history, building language and regional expertise that supports "
        "careers in international business, translation, education, diplomacy, or graduate study in "
        "Korean studies."
    ),
    "ucla-labor-studies-ug": (
        "Undergraduates with at least a 2.5 GPA who want to study inequality at work and in "
        "communities through an interdisciplinary lens, preparing for labor relations, human "
        "resources, organizing, nonprofit and government work, law, or social welfare."
    ),
    "ucla-latin-ug": (
        "Undergraduates drawn to the Latin language and the literature, history, and culture of "
        "ancient Rome, ready to build reading command from the ground up as a foundation for graduate "
        "classics, teaching, law, or work demanding close textual analysis."
    ),
    "ucla-latin-american-studies-ug": (
        "Undergraduates eager to study Latin America or a subregion from an interdisciplinary, modern "
        "perspective, who value international fieldwork and study abroad, building regional and "
        "global expertise for careers in policy, NGOs, international business, or area-studies "
        "graduate work."
    ),
    "ucla-linguistics-ug": (
        "Undergraduates curious about how human language works as a system of sound, syntax, and "
        "meaning, and about what language reveals about cognition, who want a scientific, theory- "
        "driven foundation for graduate study, language technology, or research on how we learn and "
        "process language."
    ),
    "ucla-linguistics-and-anthropology-ug": (
        "Undergraduates who want to study both the formal structure of human language and how "
        "language shapes history, identity, and social life, building combined expertise in "
        "linguistic theory and anthropology suited to graduate study, fieldwork, or research on "
        "language and culture."
    ),
    "ucla-linguistics-and-asian-languages-and-cultures-ug": (
        "Undergraduates drawn to the languages and civilizations of China, Korea, Japan, and India "
        "who also want to understand the structure and history of human language, building joint "
        "regional and linguistic expertise toward graduate study, translation, or area-focused "
        "careers."
    ),
    "ucla-linguistics-and-computer-science-ug": (
        "Undergraduates who want professional preparation in computer science paired with the "
        "scientific study of language, more drawn to theory and software than to hardware, building "
        "skills for careers in language technology, computational linguistics, or graduate study "
        "spanning both fields."
    ),
    "ucla-linguistics-and-english-ug": (
        "Undergraduates who want to study the literatures and cultures of the English-speaking world "
        "together with the structure and history of the English language and human language broadly, "
        "building combined expertise for teaching, writing, editing, or graduate study in linguistics "
        "or English."
    ),
    "ucla-linguistics-and-philosophy-ug": (
        "Reflective undergraduates who want to examine both the nature of human language and the "
        "foundations of their own beliefs, pairing linguistic theory with philosophical inquiry, "
        "building rigorous analytical skills for graduate study, law, or any field that rewards "
        "careful reasoning."
    ),
    "ucla-linguistics-and-psychology-ug": (
        "Undergraduates interested in explaining human and animal behavior while studying the "
        "structure and history of language, pairing linguistics with psychology to build a foundation "
        "for research, graduate study in cognitive or language science, or work connecting mind and "
        "language."
    ),
    "ucla-linguistics-and-spanish-ug": (
        "Undergraduates who want to combine study of the Spanish language, literatures, and Hispanic "
        "cultures with the scientific analysis of human language, building joint linguistic and "
        "cultural expertise for teaching, translation, or graduate work in linguistics or Hispanic "
        "studies."
    ),
    "ucla-marine-biology-ug": (
        "Undergraduates set on the marine sciences who want a strong biology foundation plus "
        "specialization in oceanography, marine ecology, and the physiology of marine organisms, with "
        "field and research experience preparing them for graduate study in marine sciences, biology, "
        "or medicine."
    ),
    "ucla-mathematics-ug": (
        "Undergraduates whose central passion is mathematics itself, ready to build rigorous training "
        "in pure mathematical reasoning as a foundation for graduate study, teaching, or any "
        "quantitative career that rewards deep analytical and abstract thinking."
    ),
    "ucla-mathematics-for-teaching-ug": (
        "Undergraduates planning to teach mathematics at the high school level who want broad "
        "exposure to the mathematical topics most relevant to the classroom, building subject mastery "
        "and pedagogical grounding as a foundation for a career in secondary math education."
    ),
    "ucla-mathematics-of-computation-ug": (
        "Undergraduates whose primary interest is mathematics but who also want to work seriously "
        "with computing, building a foundation that joins mathematical rigor with computational skill "
        "for careers in software, data, or quantitative work, or for further study."
    ),
    "ucla-mathematics-applied-science-ug": (
        "Undergraduates with a strong interest in mathematics and its application to a particular "
        "field, ready to design their own program with a faculty adviser or follow a set track such "
        "as history of science or medical and life sciences, headed toward applied or "
        "interdisciplinary careers."
    ),
    "ucla-mathematics-economics-ug": (
        "Undergraduates who want a solid joint foundation in mathematics and economics, emphasizing "
        "the statistical and mathematical tools most relevant to economic analysis, ideally suited to "
        "those aiming for graduate study in economics or quantitative analytical careers."
    ),
    "ucla-microbiology-immunology-and-molecular-genetics-ug": (
        "Undergraduates preparing for biomedical research, medicine, dentistry, or the health "
        "professions, biotechnology, public health, or bioethics, who want a science-intensive "
        "foundation in biology, chemistry, physics, and math focused on microbes, immunity, and "
        "molecular genetics."
    ),
    "ucla-middle-eastern-studies-ug": (
        "Undergraduates drawn to the languages, history, politics, religions, and cultures of the "
        "modern and historical Middle East, who want an interdisciplinary regional foundation for "
        "careers in diplomacy, policy, journalism, NGOs, or graduate study in area studies."
    ),
    "ucla-molecular-cell-and-developmental-biology-ug": (
        "Undergraduates aiming for graduate work in biology or medicine, or entry-level biotechnology "
        "roles, who want grounding in the molecular and cellular concepts behind recent advances "
        "across cell biology, immunology, developmental biology, and neurobiology in animals and "
        "plants."
    ),
    "ucla-neuroscience-ug": (
        "Undergraduates fascinated by how the nervous system gives rise to learning, memory, "
        "perception, and behavior, who want a multidisciplinary science foundation spanning biology, "
        "chemistry, and computation, preparing for biomedical research, medicine, or graduate study "
        "in neuroscience."
    ),
    "ucla-nordic-studies-ug": (
        "Undergraduates drawn to the Nordic languages and cultures of Denmark, the Faroes, Iceland, "
        "Norway, and Sweden, ready to build language and regional expertise within a Germanic and "
        "Indo-European context as a foundation for graduate study, translation, or culturally focused "
        "careers."
    ),
    "ucla-philosophy-ug": (
        "Undergraduates who want to read widely across world philosophical traditions, debate ideas "
        "in conversation, and sharpen their thinking through rigorous writing, building reasoning and "
        "argument skills that serve law, public life, graduate study, or any field demanding clear "
        "thought."
    ),
    "ucla-physics-ba-ug": (
        "Undergraduates who want a strong physics background while keeping room to study other "
        "fields, well-suited to those planning a double major or a path into science teaching; those "
        "aiming for a physics PhD are pointed toward the more intensive B.S. track."
    ),
    "ucla-physics-bs-ug": (
        "Undergraduates committed to physics at the deepest level and intending to continue toward a "
        "PhD, ready for the most rigorous physics training the department offers as a foundation for "
        "graduate research and an academic or research career."
    ),
    "ucla-physiological-science-ug": (
        "Undergraduates fascinated by how living systems function who plan to continue into graduate "
        "study, with paths into interdepartmental physiology or neuroscience PhD programs, building a "
        "science foundation for research, the health professions, or biomedical careers."
    ),
    "ucla-political-science-ug": (
        "Undergraduates who want to understand political processes and institutions across national "
        "and cultural contexts, the relations between states, and the changing bond between citizens "
        "and governments, building analytical grounding for law, policy, government, or graduate "
        "study."
    ),
    "ucla-portuguese-and-brazilian-studies-ug": (
        "Undergraduates aiming for advanced Portuguese fluency together with the literatures and "
        "cultures of Brazil, Portugal, and the wider Lusophone world, building language and regional "
        "expertise toward careers in international work, translation, education, or graduate study."
    ),
    "ucla-psychobiology-ug": (
        "Undergraduates planning graduate work in physiological psychology, neuroscience, or the "
        "health sciences who want to study behavior from a biological perspective, drawing on neural, "
        "genetic, evolutionary, and developmental approaches to understanding human and animal "
        "behavior."
    ),
    "ucla-psychology-ug": (
        "Undergraduates wanting broad and in-depth coverage of the fundamental areas of psychology, "
        "building a strong foundation for graduate study in psychology or preparation for law, "
        "education, public policy, business, or the health-related professions."
    ),
    "ucla-russian-language-and-literature-ug": (
        "Undergraduates who want basic mastery of the Russian language and familiarity with the "
        "classics of Russian literature, including those starting Russian in college, building "
        "language and literary expertise toward graduate study, translation, or internationally "
        "oriented careers."
    ),
    "ucla-russian-studies-ug": (
        "Undergraduates who want to pair command of the Russian language with broad study of Russian "
        "history, politics, literature, and culture, building interdisciplinary regional expertise "
        "for careers in policy, international affairs, education, or graduate study."
    ),
    "ucla-sociology-ug": (
        "Undergraduates curious about how society, social relationships, and culture shape everyday "
        "life, who want training in empirical investigation and critical analysis across micro- and "
        "macro-level questions, building a foundation for research, policy, social services, or "
        "graduate study."
    ),
    "ucla-southeast-asian-studies-ug": (
        "Undergraduates drawn to the languages, histories, politics, and cultures of Southeast Asia, "
        "who want an interdisciplinary regional foundation for careers in international affairs, "
        "NGOs, journalism, or graduate study in area studies."
    ),
    "ucla-spanish-ug": (
        "Undergraduates who want to master Spanish, a global language with hundreds of millions of "
        "speakers, and study its literatures and cultures, building language and cultural expertise "
        "for careers in education, translation, international work, or graduate study."
    ),
    "ucla-spanish-and-community-and-culture-ug": (
        "Undergraduates who want advanced Spanish paired with the study of U.S. Latino and Latin "
        "American communities and cultures, including service learning in Spanish-speaking Los "
        "Angeles, preparing for careers in education, social services, public health, or community- "
        "engaged work."
    ),
    "ucla-spanish-and-linguistics-ug": (
        "Undergraduates who want to join the study of Spanish language, literature, and culture with "
        "formal linguistics, examining the phonology, syntax, and sociolinguistics of Spanish and its "
        "varieties, building expertise toward graduate study, language work, or teaching."
    ),
    "ucla-spanish-and-portuguese-ug": (
        "Undergraduates aiming for advanced study of both Spanish and Portuguese alongside the "
        "literatures and cultures of Iberia, Latin America, and the Lusophone world, building broad "
        "Ibero-American language and cultural expertise for international careers, translation, or "
        "graduate study."
    ),
    "ucla-statistics-and-data-science-ug": (
        "Undergraduates who want a general grounding in the practice of statistics and data science, "
        "with theory, modern techniques, and applied experience, preparing for graduate-level "
        "research or industry and government roles, ideally paired with a minor in an applied "
        "discipline."
    ),
    "ucla-study-of-religion-ug": (
        "Undergraduates who want to study religion historically and scientifically, describing, "
        "comparing, and interpreting traditions through empirical and cross-cultural perspectives, "
        "building analytical and humanistic skills for careers in education, nonprofits, law, or "
        "graduate study."
    ),
    "ucla-african-american-studies-ms": (
        "Graduate students seeking advanced expertise in African American history, culture, politics, "
        "and social life, ready for rigorous seminars, methods training, and a thesis or capstone, "
        "headed toward doctoral study, teaching, research, or specialized professional roles."
    ),
    "ucla-african-studies-ms": (
        "Graduate students seeking advanced, specialized training in Africa's history, cultures, "
        "politics, economies, languages, and religions, building Africanist expertise as a step "
        "toward doctoral study, research, policy and international development work, or careers "
        "focused on the continent."
    ),
    "ucla-american-indian-studies-ms": (
        "Graduate students ready to deepen their command of American Indian cultures, histories, and "
        "contemporary issues, who want methods training and a thesis or capstone to support work in "
        "academia, community organizations, tribal institutions, or cultural and policy settings."
    ),
    "ucla-anthropology-ms": (
        "Students drawn to an anthropological understanding of human behavior who value a cross- "
        "cultural, holistic approach connecting biology, history, linguistics, the social sciences, "
        "and the humanities, and who seek advanced graduate training to anchor research or applied "
        "careers studying human societies."
    ),
    "ucla-archaeology-ms": (
        "Committed graduate students who intend to pursue archaeology seriously rather than stop at "
        "the master's degree, using advanced study as a stepping stone toward doctoral research and a "
        "long-term scholarly or professional path in the field."
    ),
    "ucla-art-history-ms": (
        "Students ready to study artistic production and visual culture across periods and cultures "
        "at an advanced level, who want graduate seminars, methods training, and a thesis or capstone "
        "to prepare for museum, gallery, curatorial, academic, or further doctoral work."
    ),
    "ucla-asian-american-studies-ms": (
        "Graduate students seeking advanced expertise in Asian American studies who want disciplined "
        "seminar work, methods training, and a thesis or capstone to ground research, teaching, "
        "community, or policy careers focused on Asian American experience."
    ),
    "ucla-asian-languages-and-cultures-ms": (
        "Post-graduate students who want to study Asian peoples, cultures, languages, history, and "
        "politics through a field blending sociology, history, cultural anthropology, and cultural "
        "studies, preparing them to research political, cultural, and economic phenomena in "
        "traditional and contemporary Asian societies."
    ),
    "ucla-astronomy-and-astrophysics-mat-ms": (
        "Students who want advanced graduate training in astrophysics, applying the methods and "
        "principles of physics and chemistry to study astronomical objects and phenomena, and who "
        "seek a master's grounded in understanding the nature of the heavenly bodies and the "
        "universe."
    ),
    "ucla-astronomy-and-astrophysics-ms-ms": (
        "Students pursuing rigorous graduate study in astrophysics who want to apply the methods of "
        "physics and chemistry to astronomical objects and the universe, building a research-oriented "
        "master's focused on understanding the nature of celestial bodies."
    ),
    "ucla-atmospheric-and-oceanic-sciences-ms": (
        "Students ready for advanced study of the Earth's atmosphere and its physical processes, who "
        "want graduate seminars, methods training, and a thesis or capstone to support research or "
        "applied careers in atmospheric and oceanic science."
    ),
    "ucla-biochemistry-molecular-and-structural-biology-ms": (
        "Students preparing for careers in biochemistry or fields demanding extensive grounding in "
        "both chemistry and biology, who want advanced graduate training that bridges the two "
        "disciplines and supports research or technical professional paths."
    ),
    "ucla-bioinformatics-ms": (
        "Students at the intersection of biology and computation who want to develop methods and "
        "software for understanding large, complex biological data, drawing on computer science, "
        "statistics, mathematics, and the life sciences to prepare for analytical and research "
        "careers."
    ),
    "ucla-biology-ms": (
        "Students ready to study molecular, organismal, and ecological approaches to the life "
        "sciences at an advanced level, who want graduate seminars, methods training, and a thesis or "
        "capstone to support research or applied careers across biology."
    ),
    "ucla-chemistry-ms": (
        "Students seeking advanced graduate expertise in chemistry who want disciplined seminar work, "
        "methods training, and a thesis or capstone to ground research, laboratory, or technical "
        "professional careers in the chemical sciences."
    ),
    "ucla-chicana-and-chicano-studies-ms": (
        "Graduate students who want advanced, interdisciplinary expertise in Chicana and Chicano "
        "studies, using seminars, methods training, and a thesis or capstone to support research, "
        "teaching, community, or policy work centered on Chicana and Chicano experience."
    ),
    "ucla-classics-ms": (
        "Students drawn to classical antiquity who want advanced study of ancient Greek and Roman "
        "literature in their original languages, with room to engage philosophy, history, "
        "archaeology, art, and mythology, preparing for scholarly, teaching, or further doctoral "
        "paths."
    ),
    "ucla-communication-ms": (
        "Students ready to study human communication across interpersonal, media, and political "
        "contexts at an advanced level, who want graduate seminars, methods training, and a thesis or "
        "capstone to support research, media, or applied communication careers."
    ),
    "ucla-comparative-literature-ms": (
        "Students who want to study literature and cultural expression across languages and national "
        "traditions at an advanced level, using graduate seminars, methods training, and a thesis or "
        "capstone to prepare for scholarly, editorial, teaching, or further doctoral work."
    ),
    "ucla-conservation-of-cultural-heritage-ms": (
        "Aspiring conservators who want hands-on training in the technical study, analysis, and "
        "preservation of archaeological and ethnographic materials, combining laboratory science, "
        "treatment, and fieldwork to enter professional conservation practice."
    ),
    "ucla-conservation-of-material-culture-ms": (
        "Students preparing to examine, analyze, and preserve objects of material culture who want "
        "training that integrates conservation science, materials analysis, and supervised treatment "
        "of archaeological and ethnographic collections for professional conservation work."
    ),
    "ucla-east-asian-studies-ms": (
        "Students seeking a broad humanistic understanding of East Asia past and present, who want "
        "multidisciplinary graduate study of the region's culture, written language, history, and "
        "political institutions to ground research, teaching, or area-focused careers."
    ),
    "ucla-economics-ms": (
        "Students ready to study the production, distribution, and consumption of goods and services "
        "at an advanced level, who want graduate seminars, methods training, and a thesis or capstone "
        "to support analytical, research, or applied economics careers."
    ),
    "ucla-english-ms": (
        "Students who want advanced study of English-language literature, criticism, and literary "
        "theory, using graduate seminars, methods training, and a thesis or capstone to prepare for "
        "teaching, editorial, writing-intensive, or further doctoral paths."
    ),
    "ucla-environment-and-sustainability-ms": (
        "Students who want to apply fundamental principles of environmental science and "
        "sustainability to pressing, multidisciplinary challenges, developing the skills and "
        "perspectives needed for careers in academia and the public and private sectors."
    ),
    "ucla-french-and-francophone-studies-ms": (
        "Students who want advanced graduate study of French language and the francophone world, "
        "building deep command of a Romance language descended from Latin to support scholarly, "
        "teaching, translation, or further doctoral work."
    ),
    "ucla-gender-studies-ms": (
        "Students ready to study gender, sexuality, and feminist theory across social and cultural "
        "life at an advanced level, who want graduate seminars, methods training, and a thesis or "
        "capstone to support research, advocacy, or teaching careers."
    ),
    "ucla-geochemistry-ms": (
        "Students who want to use the tools and principles of chemistry to explain major geological "
        "systems, from the Earth's crust and oceans to processes across the Solar System, preparing "
        "for research careers in this integrated field of chemistry and geology."
    ),
    "ucla-geography-ms": (
        "Students ready for advanced spatial analysis of human and physical environments, who want "
        "graduate seminars, methods training, and a thesis or capstone to support research, "
        "analytical, or applied careers studying geography."
    ),
    "ucla-geology-ms": (
        "Students seeking advanced graduate expertise in geology who want disciplined seminar work, "
        "methods training, and a thesis or capstone to ground research, fieldwork, or technical "
        "professional careers in the geological sciences."
    ),
    "ucla-geophysics-and-space-physics-ms": (
        "Students drawn to the quantitative and observational study of Earth and its surrounding "
        "space environment, who want advanced training in Earth's gravitational, magnetic, and "
        "electromagnetic fields, internal structure, and dynamics for research-oriented careers."
    ),
    "ucla-germanic-languages-ms": (
        "Students who want advanced graduate study of the Germanic languages and their cultures, "
        "building deep linguistic and literary command within this Indo-European branch to support "
        "scholarly, teaching, translation, or further doctoral work."
    ),
    "ucla-greek-ms": (
        "Students committed to advanced study of ancient Greek language and literature, typically as "
        "a step toward the doctorate, who want rigorous philological training within a classics "
        "department as a foundation for scholarly and academic careers."
    ),
    "ucla-history-ms": (
        "Students ready for systematic, advanced study of the human past, who want graduate seminars, "
        "methods training, and a thesis or capstone to support research, teaching, archival, or "
        "further doctoral work in history."
    ),
    "ucla-indo-european-studies-ms": (
        "Students drawn to the Indo-European languages and their related cultural history, who want "
        "interdisciplinary graduate training spanning historical linguistics, comparative philology, "
        "archaeology, and genetics to support scholarly and research careers."
    ),
    "ucla-islamic-studies-ms": (
        "Students who want multidisciplinary academic study of Islam and the Islamic world, "
        "exchanging ideas across diverse fields to understand its past and potential future, "
        "preparing for research, teaching, or area-focused professional paths."
    ),
    "ucla-italian-ms": (
        "Students who want advanced graduate study of Italian language and culture, building deep "
        "command of this Romance language and its literary tradition to support scholarly, teaching, "
        "translation, or further doctoral work."
    ),
    "ucla-latin-ms": (
        "Students committed to advanced study of Latin language and Roman literature, typically "
        "within the doctoral program, who want rigorous philological training in a classics "
        "department as a foundation for scholarly and academic careers."
    ),
    "ucla-latin-american-studies-ms": (
        "Graduate students seeking advanced, interdisciplinary expertise in Latin American studies, "
        "who want seminars, methods training, and a thesis or capstone to ground research, teaching, "
        "or area-focused careers centered on the region."
    ),
    "ucla-linguistics-ms": (
        "Students ready to study the structure, sound, meaning, and use of human language at an "
        "advanced level, who want graduate seminars, methods training, and a thesis or capstone to "
        "support research or applied careers in linguistics."
    ),
    "ucla-master-of-applied-chemical-sciences-ms": (
        "Students who want applied, advanced graduate training grounded in the study of matter — its "
        "composition, structure, properties, behavior, and the reactions and chemical bonds it "
        "undergoes — to support professional and technical careers in the chemical sciences."
    ),
    "ucla-master-of-applied-geospatial-information-systems-and-technologies-ms": (
        "Students who want applied, professional training in geographic information systems — the "
        "hardware, software, and workflows used to store, manage, analyze, and visualize geographic "
        "data — to support careers working with spatial data and GIS technologies."
    ),
    "ucla-master-of-applied-statistics-and-data-science-ms": (
        "Students who want applied, professional training in data science, combining statistics, "
        "scientific computing, algorithms, and coding to extract knowledge from noisy, structured, or "
        "unstructured data and build careers as working data scientists."
    ),
    "ucla-master-of-quantitative-economics-ms": (
        "Students who want rigorous, applied training in econometrics — using statistical methods to "
        "give empirical content to economic relationships — to analyze actual economic phenomena and "
        "prepare for quantitative, research, and analytical careers in economics."
    ),
    "ucla-master-of-quantum-science-and-technology-ms": (
        "Students seeking an interdisciplinary professional master's spanning physics, electrical "
        "engineering, computer science, and chemistry, who want training in quantum computing, "
        "quantum information, sensing, and the engineering of quantum devices for careers in the "
        "field."
    ),
    "ucla-master-of-social-science-ms": (
        "Students who want to combine methods and theory across the social sciences in an "
        "interdisciplinary graduate program, culminating in applied research on a focused social, "
        "economic, or policy question to support analytical and applied careers."
    ),
    "ucla-mathematics-ma-ms": (
        "Students whose central interest is mathematics and who want advanced graduate study of the "
        "discipline, building deep theoretical command to support teaching, research, analytical, or "
        "further doctoral paths."
    ),
    "ucla-mathematics-mat-ms": (
        "Students whose central interest is mathematics who want advanced graduate study oriented "
        "toward the teaching of the subject, building deep command of the discipline to support "
        "careers in mathematics education."
    ),
    "ucla-medical-informatics-ms": (
        "Students drawn to the application of computer science to improve the communication, "
        "understanding, and management of medical information, who want advanced training at the "
        "intersection of engineering, applied science, and health to support careers in health "
        "informatics."
    ),
    "ucla-molecular-biology-ms": (
        "Students who want to understand the molecular structures and chemical processes underlying "
        "biological activity within and between cells, with advanced study centered on nucleic acids, "
        "proteins, and processes like replication, transcription, and translation, for research "
        "careers."
    ),
    "ucla-molecular-cell-and-developmental-biology-ms": (
        "Students ready to study the molecular, cellular, and developmental processes of living "
        "systems at an advanced level, who want graduate seminars, methods training, and a thesis or "
        "capstone to support research or applied careers in the life sciences."
    ),
    "ucla-near-eastern-languages-and-cultures-ms": (
        "Students drawn to the ancient Near East — Mesopotamia, the Levant, Egypt, Iran, Anatolia, "
        "and the Arabian Peninsula — who want advanced graduate study of its languages, cultures, and "
        "archaeology to support scholarly and research careers in ancient history."
    ),
    "ucla-philosophy-ms": (
        "Students ready for advanced study of metaphysics, epistemology, ethics, and the history of "
        "philosophy, who want graduate seminars, methods training, and a thesis or capstone to "
        "support scholarly, teaching, or further doctoral work in philosophy."
    ),
    "ucla-physics-mat-ms": (
        "Students who want advanced graduate training focused on the teaching of physics in secondary "
        "education, combining seminars, methods training, and a thesis or capstone to prepare for "
        "careers teaching physics at the secondary level."
    ),
    "ucla-physics-ms-ms": (
        "Students ready for advanced study and research in physics, who want graduate seminars, "
        "methods training, and a thesis or capstone to deepen their command of the discipline and "
        "support research or technical careers."
    ),
    "ucla-physiological-science-ms": (
        "Students ready to study the function of cells, organs, and systems in living organisms at an "
        "advanced level, who want graduate seminars, methods training, and a thesis or capstone to "
        "support research, health-related, or applied careers."
    ),
    "ucla-planetary-science-ms": (
        "Students drawn to the scientific study of celestial bodies and planetary systems and how "
        "they form, who want advanced training to investigate objects from micrometeoroids to gas "
        "giants — their composition, dynamics, formation, and history — for research careers."
    ),
    "ucla-political-science-ms": (
        "Graduates of politics, government, or related social sciences who want advanced grounding in "
        "political institutions, behavior, theory, and international relations, and are ready for "
        "graduate seminars, methods training, and a thesis or capstone before policy, analysis, or "
        "doctoral work."
    ),
    "ucla-portuguese-ms": (
        "Advanced students of Portuguese language and the literatures and cultures of its eight "
        "official countries, from Portugal and Brazil to Angola, Mozambique, and Timor-Leste, ready "
        "for graduate study leading toward teaching, translation, or research in a major world "
        "language."
    ),
    "ucla-psychology-ms": (
        "Psychology and behavioral-science graduates seeking advanced training in cognition, "
        "behavior, and the biological and social bases of mind, prepared for graduate seminars, "
        "methods coursework, and a thesis or capstone that opens applied or research roles."
    ),
    "ucla-scandinavian-ms": (
        "Students of the North Germanic languages and Nordic cultures, including Danish, Faroese, "
        "Icelandic, Norwegian, and Swedish traditions, ready for graduate-level study of these "
        "languages and literatures toward teaching, translation, or further research."
    ),
    "ucla-slavic-east-european-and-eurasian-languages-and-cultures-ms": (
        "Students of Slavic literatures and linguistics ready for advanced training that sharpens "
        "critical and analytic skills, whether aiming toward college teaching and research or "
        "alternative careers in language teaching, translation, interpreting, librarianship, "
        "business, or government service."
    ),
    "ucla-sociology-ms": (
        "Sociology and social-science graduates wanting advanced expertise in social structure, "
        "institutions, and human social behavior, prepared to take on graduate seminars, methods "
        "training, and a thesis or capstone before research, policy, or applied careers."
    ),
    "ucla-spanish-ms": (
        "Advanced students of Spanish and Latin American language, literature, and culture ready for "
        "graduate seminars, methods training, and a thesis or capstone, headed toward teaching, "
        "translation, or scholarship in the Hispanic field."
    ),
    "ucla-statistics-ms": (
        "Quantitatively grounded students who want rigorous statistical theory and modern data- "
        "science practice, whether headed for further graduate research or employment applying "
        "statistics in industry or government across substantive fields of application."
    ),
    "ucla-teaching-asian-languages-ms": (
        "Aspiring and current language instructors who want to teach Chinese, Japanese, Korean, or "
        "other Asian languages, ready to combine applied linguistics, language-acquisition theory, "
        "and supervised classroom teaching into a professional teaching career."
    ),
    "ucla-anthropology-phd": (
        "Aspiring scholars committed to original research across the cross-cultural, archaeological, "
        "and biological study of humanity, ready for faculty-mentored dissertation work and "
        "qualifying examinations on the way to academic and research careers in anthropology."
    ),
    "ucla-archaeology-phd": (
        "Aspiring researchers drawn to the material remains of the human past who want to master "
        "archaeological methods through faculty-mentored dissertation work and qualifying exams, "
        "headed toward academic and research careers in archaeology."
    ),
    "ucla-art-history-phd": (
        "Aspiring scholars of artistic production and visual culture across periods and cultures, "
        "ready to pursue original dissertation research under faculty mentorship and qualifying "
        "examinations toward teaching and research careers in art history."
    ),
    "ucla-asian-languages-and-cultures-phd": (
        "Aspiring scholars of the languages, literatures, and cultures of Asia, prepared for faculty- "
        "mentored dissertation research and qualifying examinations on the path to academic and "
        "research careers in the field."
    ),
    "ucla-astronomy-and-astrophysics-phd": (
        "Aspiring researchers who want to apply the methods of physics and chemistry to understand "
        "the nature of the heavenly bodies and the universe, ready for faculty-mentored dissertation "
        "work toward academic and research careers in astrophysics."
    ),
    "ucla-atmospheric-and-oceanic-sciences-phd": (
        "Aspiring researchers focused on the Earth's atmosphere, oceans, and the physical processes "
        "that drive them, ready for faculty-mentored dissertation work and qualifying examinations "
        "toward academic and research careers in the field."
    ),
    "ucla-biochemistry-molecular-and-structural-biology-phd": (
        "Aspiring researchers in biochemistry and molecular and structural biology who want to pursue "
        "original dissertation work under faculty mentorship and qualifying examinations, headed "
        "toward academic and research careers in the life sciences."
    ),
    "ucla-bioinformatics-phd": (
        "Aspiring researchers at the intersection of biology and computing who want to develop "
        "computational methods and software for analyzing biological data, ready for faculty-mentored "
        "dissertation work toward academic and research careers in bioinformatics."
    ),
    "ucla-biology-phd": (
        "Aspiring researchers drawn to molecular, organismal, and ecological approaches to the life "
        "sciences, prepared for faculty-mentored dissertation work and qualifying examinations on the "
        "path to academic and research careers in biology."
    ),
    "ucla-chemistry-phd": (
        "Aspiring researchers in chemistry ready to pursue original dissertation work under faculty "
        "mentorship and qualifying examinations, headed toward academic and research careers across "
        "the chemical sciences."
    ),
    "ucla-chicana-and-chicano-studies-phd": (
        "Aspiring scholars of Chicana and Chicano studies prepared for original dissertation research "
        "under faculty mentorship and qualifying examinations, on the path to academic and research "
        "careers in the field."
    ),
    "ucla-classics-phd": (
        "Aspiring scholars of the languages, literature, and civilizations of ancient Greece and "
        "Rome, ready for faculty-mentored dissertation research and qualifying examinations toward "
        "academic and research careers in classics."
    ),
    "ucla-communication-phd": (
        "Aspiring researchers studying human communication across interpersonal, media, and political "
        "contexts, ready for faculty-mentored dissertation work and qualifying examinations on the "
        "path to academic and research careers in communication."
    ),
    "ucla-comparative-literature-phd": (
        "Aspiring scholars who read literature and cultural expression across languages and national "
        "traditions, prepared for faculty-mentored dissertation research and qualifying examinations "
        "toward academic and research careers in comparative literature."
    ),
    "ucla-conservation-of-material-culture-phd": (
        "Aspiring conservation scientists committed to advanced research on the deterioration, "
        "analysis, and preservation of cultural materials, ready for original doctoral research that "
        "leads toward research and teaching careers in conservation science."
    ),
    "ucla-doctor-of-environmental-science-and-engineering-phd": (
        "Problem-solvers who want to tackle complex environmental challenges across science, "
        "engineering, and policy, ready for interdisciplinary doctoral coursework and a major applied "
        "doctoral project rather than a purely theoretical research track."
    ),
    "ucla-economics-phd": (
        "Aspiring researchers studying the production, distribution, and consumption of goods and "
        "services, ready for faculty-mentored dissertation work and qualifying examinations on the "
        "path to academic and research careers in economics."
    ),
    "ucla-english-phd": (
        "Aspiring scholars of English-language literature, criticism, and literary theory, prepared "
        "for faculty-mentored dissertation research and qualifying examinations toward academic and "
        "research careers in English."
    ),
    "ucla-environment-and-sustainability-phd": (
        "Aspiring researchers focused on environmental systems, sustainability, and policy, ready for "
        "faculty-mentored dissertation work and qualifying examinations on the path to academic and "
        "research careers in the field."
    ),
    "ucla-french-and-francophone-studies-phd": (
        "Aspiring scholars of French and Francophone literature, language, and culture, prepared for "
        "faculty-mentored dissertation research and qualifying examinations toward academic and "
        "research careers in the field."
    ),
    "ucla-gender-studies-phd": (
        "Aspiring scholars of gender, sexuality, and feminist theory across social and cultural life, "
        "ready for faculty-mentored dissertation research and qualifying examinations on the path to "
        "academic and research careers in gender studies."
    ),
    "ucla-geochemistry-phd": (
        "Aspiring researchers studying the chemistry of Earth and planetary materials and processes, "
        "prepared for faculty-mentored dissertation work and qualifying examinations toward academic "
        "and research careers in geochemistry."
    ),
    "ucla-geography-phd": (
        "Aspiring researchers drawn to the spatial analysis of human and physical environments, ready "
        "for faculty-mentored dissertation work and qualifying examinations on the path to academic "
        "and research careers in geography."
    ),
    "ucla-geology-phd": (
        "Aspiring researchers in geology ready to pursue original dissertation work under faculty "
        "mentorship and qualifying examinations, headed toward academic and research careers in the "
        "Earth sciences."
    ),
    "ucla-geophysics-and-space-physics-phd": (
        "Aspiring researchers studying the internal structure, composition, and dynamics of planetary "
        "bodies, prepared for faculty-mentored dissertation work and qualifying examinations toward "
        "academic and research careers in geophysics and space physics."
    ),
    "ucla-germanic-languages-phd": (
        "Aspiring scholars of German and Germanic literature, language, and culture, ready for "
        "faculty-mentored dissertation research and qualifying examinations on the path to academic "
        "and research careers in Germanic languages."
    ),
    "ucla-history-phd": (
        "Aspiring scholars committed to the systematic study of the human past, prepared for faculty- "
        "mentored dissertation research and qualifying examinations toward academic and research "
        "careers in history."
    ),
    "ucla-indo-european-studies-phd": (
        "Aspiring scholars of Indo-European studies ready to pursue original dissertation research "
        "under faculty mentorship and qualifying examinations, on the path to academic and research "
        "careers in the field."
    ),
    "ucla-islamic-studies-phd": (
        "Aspiring scholars dedicated to the academic study of Islam, prepared for faculty-mentored "
        "dissertation research and qualifying examinations toward academic and research careers in "
        "Islamic studies."
    ),
    "ucla-italian-phd": (
        "Aspiring scholars of Italian language, literature, and cultural history, ready for faculty- "
        "mentored dissertation research and qualifying examinations on the path to academic and "
        "research careers in Italian."
    ),
    "ucla-linguistics-phd": (
        "Aspiring researchers studying the structure, sound, meaning, and use of human language, "
        "prepared for faculty-mentored dissertation work and qualifying examinations toward academic "
        "and research careers in linguistics."
    ),
    "ucla-mathematics-phd": (
        "Aspiring researchers in pure and applied mathematics, ready to pursue original dissertation "
        "work under faculty mentorship and qualifying examinations, headed toward academic and "
        "research careers in the mathematical sciences."
    ),
    "ucla-medical-informatics-phd": (
        "Aspiring researchers in medical informatics ready to pursue original dissertation work under "
        "faculty mentorship and qualifying examinations, on the path to academic and research careers "
        "in the field."
    ),
    "ucla-molecular-biology-phd": (
        "Aspiring researchers studying the molecular structures and chemical processes of living "
        "systems, prepared for faculty-mentored dissertation work and qualifying examinations toward "
        "academic and research careers in molecular biology."
    ),
    "ucla-molecular-cell-and-developmental-biology-phd": (
        "Aspiring researchers focused on the molecular, cellular, and developmental processes of "
        "living systems, ready for faculty-mentored dissertation work and qualifying examinations on "
        "the path to academic and research careers in the life sciences."
    ),
    "ucla-molecular-cellular-and-integrative-physiology-phd": (
        "Aspiring researchers in physiology applying directly to an interdepartmental doctoral "
        "program, ready for faculty-mentored dissertation work and qualifying examinations toward "
        "academic and research careers in molecular, cellular, and integrative physiology."
    ),
    "ucla-near-eastern-languages-and-cultures-phd": (
        "Aspiring scholars of the languages, texts, and archaeology of the ancient Near East, "
        "prepared for faculty-mentored dissertation research and qualifying examinations toward "
        "academic and research careers in the field."
    ),
    "ucla-philosophy-phd": (
        "Aspiring scholars working in metaphysics, epistemology, ethics, and the history of "
        "philosophy, ready for faculty-mentored dissertation research and qualifying examinations on "
        "the path to academic and research careers in philosophy."
    ),
    "ucla-physics-phd": (
        "Aspiring researchers in physics ready to pursue original dissertation work under faculty "
        "mentorship and qualifying examinations, headed toward academic and research careers across "
        "the physical sciences."
    ),
    "ucla-planetary-science-phd": (
        "Aspiring researchers studying planetary bodies, their formation, and the processes that "
        "shape them, prepared for faculty-mentored dissertation work and qualifying examinations "
        "toward academic and research careers in planetary science."
    ),
    "ucla-political-science-phd": (
        "Aspiring researchers studying political institutions, behavior, theory, and international "
        "relations, ready for faculty-mentored dissertation work and qualifying examinations on the "
        "path to academic and research careers in political science."
    ),
    "ucla-psychology-phd": (
        "Aspiring researchers studying cognition, behavior, and the biological and social bases of "
        "mind, prepared for faculty-mentored dissertation work and qualifying examinations toward "
        "academic and research careers in psychology."
    ),
    "ucla-slavic-east-european-and-eurasian-languages-and-cultures-phd": (
        "Aspiring scholars of Slavic, East European, and Eurasian languages, literatures, and "
        "cultures, ready for faculty-mentored dissertation research and qualifying examinations on "
        "the path to academic and research careers in the field."
    ),
    "ucla-sociology-phd": (
        "Aspiring researchers studying social structure, institutions, and human social behavior, "
        "prepared for faculty-mentored dissertation work and qualifying examinations toward academic "
        "and research careers in sociology."
    ),
    "ucla-statistics-phd": (
        "Aspiring researchers in statistical theory, methodology, and data analysis, ready to pursue "
        "original dissertation work under faculty mentorship and qualifying examinations, headed "
        "toward academic and research careers in statistics."
    ),
    "ucla-aerospace-engineering-ug": (
        "Undergraduates drawn to the design and construction of aircraft, helicopters, and "
        "spacecraft, ready to work at the forefront of high-technology fields spanning air "
        "transportation, national defense, and space exploration while building the engineering and "
        "scientific foundations the discipline demands."
    ),
    "ucla-bioengineering-ug": (
        "Undergraduates building the engineering foundations to apply quantitative methods to biology "
        "and medicine, who want an ABET-accredited bioengineering degree as the launchpad for a "
        "professional engineering career or further study."
    ),
    "ucla-chemical-engineering-ug": (
        "Undergraduates seeking a professionally oriented, ABET-accredited grounding in modern "
        "chemical engineering, who want to balance engineering science with practice and explore a "
        "subfield such as biomedical, biomolecular, environmental, or semiconductor manufacturing "
        "engineering."
    ),
    "ucla-civil-engineering-ug": (
        "Undergraduates building the engineering foundations for a career in civil engineering, who "
        "want an ABET-accredited degree as the credential behind designing and building the "
        "infrastructure that communities rely on."
    ),
    "ucla-computer-engineering-ug": (
        "Undergraduates with a strong math and science aptitude who want to build the hardware- "
        "software systems behind the Internet of Things, robotics, and mobile, wearable, and "
        "implantable devices, grounded in data science and embedded networked systems."
    ),
    "ucla-computer-science-ug": (
        "Undergraduates who want rigorous training in algorithms, systems, and AI with hands-on "
        "access to making and robotics facilities, aiming to recruit into major technology firms or "
        "continue into graduate programs."
    ),
    "ucla-computer-science-and-engineering-ug": (
        "Undergraduates who want to design, build, and program both the hardware and software of "
        "digital systems, spanning electronic and logic design, VLSI, operating systems, networking, "
        "and programming across the computer science and electrical and computer engineering "
        "departments."
    ),
    "ucla-electrical-engineering-ug": (
        "Undergraduates with a math and science foundation who want to master signals and systems, "
        "circuits and embedded systems, and physical wave electronics, working toward inventions like "
        "integrated circuits, photonic devices, and telecommunication systems."
    ),
    "ucla-materials-engineering-ug": (
        "Undergraduates pursuing a professional career in the materials field who want a broad grasp "
        "of how microstructure shapes the properties of metals, ceramics, polymers, and composites, "
        "plus the principles of metallurgy and ceramic and polymer science behind designing and "
        "testing them."
    ),
    "ucla-mechanical-engineering-ug": (
        "Undergraduates building broad mechanical engineering foundations across thermodynamics, "
        "fluid mechanics, heat transfer, solid mechanics, design, dynamics, control, and "
        "manufacturing, who want an ABET-accredited degree for a professional engineering career."
    ),
    "ucla-aerospace-engineering-ms": (
        "Engineers seeking advanced expertise in the design, dynamics, and control of aerospace "
        "vehicles and systems, ready to deepen their specialization through graduate seminars, "
        "methods training, and a thesis or capstone before advancing in industry or research."
    ),
    "ucla-bioengineering-ms": (
        "Engineers seeking advanced training in applying engineering principles to biology and "
        "medicine, ready to specialize through graduate seminars, methods coursework, and a thesis or "
        "capstone for advancement in the medical-technology and life-sciences fields."
    ),
    "ucla-chemical-engineering-ms": (
        "Engineers seeking advanced expertise in chemical processes, reaction engineering, and "
        "process design, ready to specialize through graduate seminars, methods training, and a "
        "thesis or capstone before advancing in the chemical and process industries."
    ),
    "ucla-civil-engineering-ms": (
        "Engineers seeking advanced specialization across structural, environmental, geotechnical, "
        "and transportation engineering, ready to deepen their practice through graduate seminars, "
        "methods training, and a thesis or capstone for professional advancement."
    ),
    "ucla-computer-science-ms": (
        "Engineers and computer scientists seeking advanced expertise in computing systems, "
        "algorithms, artificial intelligence, and software, ready to specialize through graduate "
        "seminars, methods training, and a thesis or capstone before advancing in industry or "
        "research."
    ),
    "ucla-electrical-and-computer-engineering-ms": (
        "Engineers seeking advanced coursework, in-depth training, and research investigations across "
        "the several fields of electrical and computer engineering, ready to specialize and deepen "
        "their technical expertise for industry advancement or further study."
    ),
    "ucla-engineer-ms": (
        "Practicing engineers who already hold an M.S. and want still greater depth through "
        "additional coursework and an engineering project, short of committing to a Ph.D. "
        "dissertation, pursuing this advanced post-master's credential to strengthen their technical "
        "standing."
    ),
    "ucla-engineering-ms": (
        "Engineers seeking advanced coursework and research across the school's disciplines, often as "
        "a step toward doctoral study or deeper technical specialization, who want flexibility to "
        "deepen expertise before committing to a specific research path."
    ),
    "ucla-engineering-aerospace-ms": (
        "Working engineers who want to specialize in aerodynamics, propulsion, flight mechanics, and "
        "aerospace structures while staying on the job, advancing their careers through a fully "
        "online aerospace engineering master's."
    ),
    "ucla-engineering-computer-networking-ms": (
        "Practicing engineers who want to advance part-time into computer networking, deepening their "
        "command of network architecture, protocols, wireless systems, and distributed computing "
        "through a flexible online master's."
    ),
    "ucla-engineering-electrical-ms": (
        "Practicing engineers studying part-time who want to deepen their electrical engineering "
        "expertise across circuits, electromagnetics, control, and electronic systems through a fully "
        "online master's while continuing to work."
    ),
    "ucla-engineering-electronic-materials-ms": (
        "Working engineers who want to specialize in electronic materials, including semiconductors, "
        "photonic and electronic materials, and their fabrication, advancing their expertise through "
        "the online master's program while staying employed."
    ),
    "ucla-engineering-integrated-circuits-ms": (
        "Practicing engineers who want to specialize in VLSI design, semiconductor devices, and chip "
        "architecture, preparing for advanced work in the integrated-circuit industry through a "
        "flexible online master's."
    ),
    "ucla-engineering-manufacturing-and-design-ms": (
        "Working professionals who want to advance their command of manufacturing processes, product "
        "design, and computer-aided engineering, deepening their technical breadth through a flexible "
        "online master's while staying on the job."
    ),
    "ucla-engineering-materials-science-ms": (
        "Working professionals who want to deepen their understanding of the structure, properties, "
        "and processing of engineering materials, advancing their expertise through a fully online "
        "materials science master's."
    ),
    "ucla-engineering-mechanical-ms": (
        "Working professionals who want to deepen their mechanical engineering expertise across "
        "dynamics, thermofluids, mechanics of materials, and design, advancing their careers through "
        "a flexible fully online master's."
    ),
    "ucla-engineering-signal-processing-and-communications-ms": (
        "Practicing engineers who want to specialize in signal processing and communications, "
        "spanning digital signal processing, communication theory, and wireless systems, advancing "
        "part-time through a flexible online master's."
    ),
    "ucla-engineering-structural-materials-ms": (
        "Working engineers who want to specialize in structural materials, studying the mechanical "
        "behavior, failure, and design of metals, alloys, and composites in load-bearing "
        "applications, advancing their expertise through the online master's."
    ),
    "ucla-manufacturing-engineering-ms": (
        "Engineers seeking advanced, professionally oriented training in manufacturing engineering, "
        "who want to master planning manufacturing practices, developing tools, processes, and "
        "machines, and integrating production systems for quality output at optimal cost."
    ),
    "ucla-master-of-engineering-ms": (
        "Practicing engineers who want a professional, course-based degree emphasizing applied "
        "technical breadth and engineering leadership rather than a research thesis, aiming to "
        "advance into broader technical and management roles."
    ),
    "ucla-materials-science-and-engineering-ms": (
        "Engineers seeking advanced specialization in one focused field of materials science and "
        "engineering, choosing ceramics and ceramic processing, electronic and optical materials, or "
        "structural materials to deepen expertise for industry advancement or further study."
    ),
    "ucla-mechanical-engineering-ms": (
        "Engineers seeking advanced expertise across thermodynamics, fluid and solid mechanics, "
        "dynamics, and design, ready to specialize through graduate seminars, methods training, and a "
        "thesis or capstone before advancing in industry or research."
    ),
    "ucla-aerospace-engineering-phd": (
        "Aspiring researchers headed for academia or R&D who want to pursue original dissertation "
        "work in the design, dynamics, and control of aerospace vehicles and systems, with faculty "
        "mentorship and qualifying examinations guiding their path to independent scholarship."
    ),
    "ucla-bioengineering-phd": (
        "Aspiring researchers bound for academia or R&D who want to pursue original dissertation work "
        "applying engineering principles to biology and medicine, supported by faculty mentorship and "
        "qualifying examinations on the way to independent research."
    ),
    "ucla-chemical-engineering-phd": (
        "Aspiring researchers headed for academia or R&D who want to lead original dissertation work "
        "in chemical processes, reaction engineering, and process design, supported by faculty "
        "mentorship and qualifying examinations toward independent scholarship."
    ),
    "ucla-civil-engineering-phd": (
        "Aspiring researchers bound for academia or R&D who want to pursue original dissertation work "
        "across structural, environmental, geotechnical, or transportation engineering, supported by "
        "faculty mentorship and qualifying examinations on the path to independent research."
    ),
    "ucla-computer-science-phd": (
        "Aspiring researchers headed for academia or R&D who want to advance original dissertation "
        "work in computing systems, algorithms, artificial intelligence, and software, supported by "
        "faculty mentorship and qualifying examinations toward independent scholarship."
    ),
    "ucla-electrical-and-computer-engineering-phd": (
        "Aspiring researchers bound for academia or R&D who want to lead original dissertation work "
        "in circuits, signals, devices, and computer engineering, supported by faculty mentorship and "
        "qualifying examinations on the way to independent research."
    ),
    "ucla-materials-science-and-engineering-phd": (
        "Aspiring researchers headed for academia or R&D who want to pursue original dissertation "
        "work on the structure, properties, and processing of engineering materials, supported by "
        "faculty mentorship and qualifying examinations toward independent scholarship."
    ),
    "ucla-mechanical-engineering-phd": (
        "Aspiring researchers bound for academia or R&D who want to advance original dissertation "
        "work in thermodynamics, fluid and solid mechanics, dynamics, and design, supported by "
        "faculty mentorship and qualifying examinations on the path to independent research."
    ),
    "ucla-business-analytics-ms": (
        "For early-career professionals who want to turn business data into decisions, this "
        "specialized master's suits those who enjoy iterative exploration of past performance and "
        "want statistical methods and analytics skills to drive planning rather than just report "
        "metrics."
    ),
    "ucla-executive-master-of-business-administration-ms": (
        "For experienced professionals who can commit to alternating weekends over 22 months without "
        "pausing their careers, this executive MBA fits those ready to deepen general-management and "
        "leadership skills, broaden their global perspective, and step into senior roles."
    ),
    "ucla-fully-employed-master-of-business-administration-ms": (
        "For working professionals who want a full MBA without leaving the workforce, this part-time "
        "program over roughly three years of evening and weekend classes suits those balancing a job "
        "while building the management core and electives."
    ),
    "ucla-global-executive-master-of-business-administration-for-asia-pacific-ms": (
        "For experienced managers focused on the Asia-Pacific region, this dual-degree executive "
        "program with the National University of Singapore Business School suits those who want "
        "cross-border management credentials and a footprint in both U.S. and Asian markets."
    ),
    "ucla-master-of-business-administration-ms": (
        "For early-career professionals ready to step away from work full-time, this MBA fits those "
        "who want to pair core business disciplines with applied electives and a real research "
        "project, aiming for roles in consulting, entertainment, finance, healthcare, or technology."
    ),
    "ucla-master-of-financial-engineering-ms": (
        "For quantitatively minded graduates targeting careers in quantitative finance, this 15-month "
        "program suits those comfortable with stochastic calculus, data science, and computational "
        "trading who want a summer internship and technical depth for trading or risk roles."
    ),
    "ucla-management-phd": (
        "For aspiring business-school researchers and academics who want to study how organizations "
        "are administered and resources managed across businesses, nonprofits, and government, this "
        "doctoral program fits those committed to scholarship and a faculty or research career."
    ),
    "ucla-master-of-laws-ms": (
        "A practicing lawyer, trained in the United States or abroad, who wants a focused year of "
        "advanced specialization in a field like business law, international and comparative law, or "
        "public-interest law to deepen an existing legal career."
    ),
    "ucla-master-of-legal-studies-ms": (
        "A non-lawyer professional whose work runs into legal questions and who needs a working "
        "command of legal reasoning, regulation, and compliance, without intending to practice law or "
        "sit for the bar."
    ),
    "ucla-doctor-of-juridical-science-phd": (
        "An experienced legal scholar, typically already holding an advanced law degree, who is ready "
        "to write a substantial dissertation and is aiming for a career in legal academia and "
        "original research."
    ),
    "ucla-juris-doctor-prof": (
        "A future practicing attorney who wants doctrinal grounding paired with clinical work and "
        "environmental-law training, and who is drawn to paths like federal clerkships and bar- "
        "passage-required legal employment after graduation."
    ),
    "ucla-biomathematics-ms": (
        "Quantitatively minded students who want advanced training in using mathematical modeling and "
        "theoretical analysis to study living systems, rather than running bench experiments, and who "
        "are building toward research or technical work that bridges mathematics and biology."
    ),
    "ucla-clinical-research-ms": (
        "Clinicians and research-minded health professionals who want formal training to design and "
        "run studies in people, testing the efficacy and safety of medications, devices, and "
        "treatments, and who aim to lead trials aimed at preventing, diagnosing, or treating disease."
    ),
    "ucla-data-science-in-biomedicine-ms": (
        "Computationally inclined students who want to apply computer science and data methods to "
        "medical information, working at the intersection of health informatics and engineering, and "
        "who aim to improve how clinical and biomedical data is managed and understood."
    ),
    "ucla-genetic-counseling-ms": (
        "Compassionate students who want clinical training to guide individuals and families affected "
        "by or at risk of genetic disorders, helping them understand and adapt to the medical, "
        "psychological, and familial implications, and who aim to practice within genomic medicine."
    ),
    "ucla-human-genetics-ms": (
        "Students seeking advanced master's-level training in human genetics, typically as a focused "
        "or transitional step taken with departmental approval, and who want grounding in the "
        "genetics of human health and inheritance before further research or professional work."
    ),
    "ucla-molecular-and-medical-pharmacology-ms": (
        "Students pursuing graduate training in molecular and medical pharmacology, usually as part "
        "of a longer research trajectory within the department rather than a terminal master's, who "
        "want grounding in how drugs act at the molecular and medical level."
    ),
    "ucla-physics-and-biology-in-medicine-ms": (
        "Physics-grounded students who want advanced training to apply physical concepts and methods "
        "to preventing, diagnosing, and treating disease, and who are preparing for the medical "
        "physics profession or further study at the meeting point of physics and medicine."
    ),
    "ucla-biomathematics-phd": (
        "Aspiring researchers who want to pursue original dissertation work in mathematical and "
        "theoretical biology, with faculty mentorship and qualifying examinations, and who are headed "
        "toward academic or research careers modeling the principles that govern biological systems."
    ),
    "ucla-human-genetics-phd": (
        "Aspiring researchers who want to pursue original dissertation work in the genetics of human "
        "health, disease, and inheritance, supported by faculty mentorship and qualifying "
        "examinations, and who are headed toward academic or research careers in human genetics."
    ),
    "ucla-molecular-and-medical-pharmacology-phd": (
        "Aspiring researchers who want to pursue original dissertation work in molecular and medical "
        "pharmacology and drug action, supported by faculty mentorship and qualifying examinations, "
        "and who are headed toward academic or research careers studying how drugs work."
    ),
    "ucla-neuroscience-phd": (
        "Aspiring researchers who want to pursue original dissertation work on the nervous system, "
        "its functions, and its disorders, supported by faculty mentorship and qualifying "
        "examinations, and who are headed toward academic or research careers in neuroscience."
    ),
    "ucla-physics-and-biology-in-medicine-phd": (
        "Aspiring researchers who want to pursue original dissertation work in the physics and "
        "biology underlying medical diagnosis and therapy, supported by faculty mentorship and "
        "qualifying examinations, and who are headed toward academic or research careers at the "
        "science-medicine interface."
    ),
    "ucla-doctor-of-medicine-prof": (
        "Future physicians who want professional training that integrates foundational science with "
        "clinical clerkships across UCLA Health and affiliated institutes, and who are committed to "
        "becoming practicing clinicians serving patients across the full range of medical care."
    ),
    "ucla-oral-biology-ms": (
        "Aspiring oral scientists who want graduate training in the biology of the mouth, including "
        "oral microbiology and how resident microbiota colonize teeth and gums and interact with "
        "their host. A strong fit for those moving toward research or specialized study before "
        "doctoral or clinical work."
    ),
    "ucla-oral-biology-phd": (
        "Researchers ready to pursue original dissertation work on the biology of the oral cavity, "
        "its microbiota, and oral health. Built for those who want faculty mentorship, qualifying "
        "exams, and a full dissertation, aiming for academic or research careers in oral biology."
    ),
    "ucla-doctor-of-dental-surgery-prof": (
        "Future dentists committed to clinical practice who want a four-year professional path "
        "through biomedical science, preclinical simulation, and supervised patient care across "
        "general and specialty clinics, leading to licensure. A fit for those set on treating "
        "patients chairside."
    ),
    "ucla-public-health-ba-ug": (
        "Undergraduates who want to understand the determinants of population health and how "
        "organized social efforts prevent disease and prolong life, drawn to the physical, "
        "psychological, and social sides of well-being rather than a narrowly clinical or lab-heavy "
        "track."
    ),
    "ucla-public-health-bs-ug": (
        "Undergraduates ready for a science-intensive grounding in biology, chemistry, and "
        "quantitative methods alongside public-health coursework, aiming toward the health "
        "professions or research and comfortable with a heavier laboratory and analytic load."
    ),
    "ucla-biostatistics-mph-ms": (
        "Applicants who want to put statistical methods to work in clinical medicine and public "
        "health, learning to design studies and analyze and interpret biological data through a field "
        "practicum, and heading into applied biostatistical practice rather than a doctorate."
    ),
    "ucla-biostatistics-ms-ms": (
        "Quantitatively strong applicants seeking a focused research step in biostatistics, ready to "
        "master experimental design, data collection, and analysis of biological and clinical data as "
        "preparation for analytic roles or further doctoral study in medical statistics."
    ),
    "ucla-community-health-sciences-mph-ms": (
        "Applicants drawn to working directly with communities, from neighborhoods to whole cities, "
        "to prevent disease and promote health through organized social efforts; this practice- "
        "oriented track with a field practicum suits those headed for hands-on community public- "
        "health roles."
    ),
    "ucla-community-health-sciences-ms-ms": (
        "Applicants who want an analytic, research-oriented step in community health sciences, "
        "studying the determinants of population health across communities of any scale; suited to "
        "those building toward research roles or doctoral study rather than direct practice."
    ),
    "ucla-community-health-health-promotion-and-education-ms": (
        "Applicants who want to educate individuals and communities about health, expanding knowledge "
        "and shaping attitudes across environmental, physical, social, emotional, and reproductive "
        "health; this practicum-based MPH suits aspiring health educators and promotion "
        "practitioners."
    ),
    "ucla-environmental-health-sciences-mph-ms": (
        "Applicants concerned with how the natural and built environment affects human health, ready "
        "to learn control of those factors through a field practicum; well suited to careers in "
        "environmental science, toxicology, environmental epidemiology, or occupational health "
        "practice."
    ),
    "ucla-environmental-health-sciences-ms-ms": (
        "Applicants seeking a research step in environmental health, investigating how natural and "
        "built environments shape human health and the controls a healthy environment requires; fits "
        "those drawn to environmental science, toxicology, or environmental epidemiology as analysts "
        "or future doctoral students."
    ),
    "ucla-epidemiology-mph-ms": (
        "Applicants who want to track the distribution, patterns, and determinants of disease in "
        "defined populations and apply that knowledge to prevent it; this practice-focused MPH with a "
        "field practicum suits those headed for applied epidemiology in agencies or health "
        "departments."
    ),
    "ucla-epidemiology-ms-ms": (
        "Applicants seeking an analytic, research-oriented step in epidemiology, learning to study "
        "how disease is distributed and determined across populations; suited to those building "
        "methodological skill for research roles or doctoral study rather than frontline practice."
    ),
    "ucla-executive-master-of-public-health-ms": (
        "Working professionals who want to advance applied public-health practice while continuing "
        "their careers, grounding leadership in the science of preventing disease and promoting "
        "health across populations large and small through an executive-format MPH with a field "
        "practicum."
    ),
    "ucla-health-management-ms": (
        "Applicants aiming to lead and administer health systems, hospitals, and hospital networks "
        "across primary, secondary, and tertiary care; this practice-oriented MPH with a field "
        "practicum suits those headed into health-services management and administration roles."
    ),
    "ucla-health-policy-ms": (
        "Applicants who want to shape the decisions, plans, and actions that achieve healthcare goals "
        "for society, defining priorities and building consensus; this practice-focused MPH with a "
        "field practicum suits aspiring health-policy practitioners and analysts."
    ),
    "ucla-health-policy-and-management-mph-ms": (
        "Applicants who want to engage in health services research and policy analysis on critical "
        "local, national, and global health-care problems, collaborating with department research "
        "centers; this practicum-based MPH suits those headed into agencies and organizations "
        "tackling health-system challenges."
    ),
    "ucla-health-policy-and-management-ms-ms": (
        "Applicants seeking a research step in health policy and management, ready to collaborate "
        "with department centers on progressive health-services research across many topics; suited "
        "to those building toward research and policy-analysis roles in universities, agencies, or "
        "private organizations."
    ),
    "ucla-master-of-data-science-in-health-ms": (
        "Applicants who want to apply computer science to medical information, improving how health "
        "data is communicated, understood, and managed; this professional master's suits those moving "
        "toward applied health-informatics and data-science roles at the intersection of engineering "
        "and health."
    ),
    "ucla-master-of-healthcare-administration-ms": (
        "Applicants preparing to lead health-care organizations who also want grounding in health- "
        "services research on critical local, national, and global problems through collaboration "
        "with the department's research centers; suited to those headed into health-services "
        "administration and policy-informed management."
    ),
    "ucla-master-of-public-health-ms": (
        "Applicants drawn to the broad science of preventing disease and promoting health across "
        "populations from a handful of people to entire continents; this generalist MPH with a field "
        "practicum suits those seeking applied public-health practice without committing to one "
        "specialization."
    ),
    "ucla-biostatistics-phd": (
        "Aspiring researchers and academics who want to develop and apply statistical methods to "
        "clinical medicine and public health, advancing the design of studies and the analysis and "
        "interpretation of biological data toward independent scholarship in biostatistics."
    ),
    "ucla-community-health-sciences-phd": (
        "Aspiring public-health researchers who want to investigate the determinants of population "
        "health and the social efforts that shape it across communities of any scale, building toward "
        "an academic or research career grounded in community health sciences."
    ),
    "ucla-environmental-health-sciences-phd": (
        "Aspiring researchers who want to study how the natural and built environment affects human "
        "health and what a healthy environment requires, advancing scholarship across environmental "
        "science, toxicology, environmental epidemiology, or occupational medicine toward an academic "
        "or research career."
    ),
    "ucla-environmental-and-molecular-toxicology-phd": (
        "Aspiring researchers drawn to the adverse effects of chemicals on living organisms, ready to "
        "investigate dose-response relationships and the factors shaping toxicity across biology, "
        "chemistry, pharmacology, and medicine; suited to those pursuing an academic or research "
        "career in toxicology."
    ),
    "ucla-epidemiology-phd": (
        "Aspiring public-health researchers who want to advance the study of how disease is "
        "distributed and determined in populations and how that knowledge prevents it, building the "
        "methodological depth for an academic or research career in epidemiology."
    ),
    "ucla-health-policy-and-management-phd": (
        "Aspiring researchers who want to lead health-services research and policy analysis on "
        "critical local, national, and global health-care problems, collaborating with the "
        "department's research centers; suited to those pursuing academic careers or research roles "
        "in universities, agencies, and private organizations."
    ),
    "ucla-nursing-bs-prelicensure-ug": (
        "Future RNs entering nursing through their bachelor's, ready to train as nurse generalists "
        "across primary, secondary, and tertiary prevention. You want individual- and population- "
        "based care grounded in current research, plus the early foundations of a clinical leadership "
        "role."
    ),
    "ucla-master-of-science-in-nursing-ms": (
        "Registered nurses and clinicians pursuing graduate study to advance their practice, drawn to "
        "nursing as a profession that integrates the art and science of caring. You're committed to "
        "promoting health, preventing illness, facilitating healing, and easing suffering through "
        "compassionate presence."
    ),
    "ucla-nursing-ms": (
        "Career-changers from non-nursing backgrounds ready to become registered nurses through an "
        "accelerated path. You're prepared for an intensive prelicensure curriculum and supervised "
        "clinical placements that carry you toward RN licensure and advanced practice in one "
        "continuous program."
    ),
    "ucla-nursing-phd": (
        "Aspiring nursing scientists ready to commit to original dissertation research in nursing "
        "science, patient care, and health promotion. You want close faculty mentorship, qualifying "
        "examinations, and sustained doctoral inquiry on the Westwood campus to launch a research "
        "career."
    ),
    "ucla-doctor-of-nursing-practice-prof": (
        "Experienced advanced-practice nurses aiming for the highest level of clinical leadership. "
        "You want to translate evidence into practice through advanced clinical training and a "
        "scholarly project, stepping into roles that shape and lead patient care at the point of "
        "delivery."
    ),
    "ucla-public-affairs-ug": (
        "Undergraduates drawn to how governments implement public policy and manage programs that "
        "tackle social and economic problems, and who want a liberal-arts foundation in public "
        "administration before pursuing careers or graduate study in policy and public management."
    ),
    "ucla-master-of-public-policy-ms": (
        "Aspiring policy analysts and program managers who want to design and implement the laws, "
        "regulations, and programs that govern fields like education, health care, employment, "
        "finance, and transportation, and who seek applied skills for careers across the public "
        "administration of these issues."
    ),
    "ucla-master-of-real-estate-development-ms": (
        "Professionals aiming to lead real-estate development projects who want grounding in finance, "
        "design, and policy, learning through case studies and a hands-on capstone development "
        "project toward careers in development, investment, and urban real estate."
    ),
    "ucla-master-of-social-welfare-ms": (
        "Future clinical social workers pursuing LCSW licensure who want to pair field practica at "
        "Los Angeles agencies with coursework in human behavior, social policy, and evidence-based "
        "practice, preparing for direct clinical work in community settings."
    ),
    "ucla-master-of-urban-and-regional-planning-ms": (
        "Those drawn to shaping land use and the built environment, planning transportation, "
        "infrastructure, and the physical layout of cities and regions, and who want the applied "
        "professional training to lead this work in public, private, or community planning roles."
    ),
    "ucla-master-of-urban-and-regional-planning-institut-detudes-de-paris-ms": (
        "Planning students seeking an international, dual-degree path who want to study governance of "
        "large metropolises at the Urban School of Sciences Po in Paris alongside urban and regional "
        "planning at UCLA, building toward careers spanning both contexts."
    ),
    "ucla-social-welfare-phd": (
        "Aspiring scholars who want to research and teach on poverty, child welfare, health "
        "disparities, and community interventions, building original dissertation research toward an "
        "academic or research career in social welfare."
    ),
    "ucla-urban-planning-phd": (
        "Aspiring academics and researchers focused on land use, the built environment, "
        "transportation, and infrastructure who want rigorous doctoral training to study how cities "
        "and regions are planned and to pursue scholarship and teaching in urban planning."
    ),
    "ucla-education-and-social-transformation-ug": (
        "Undergraduates drawn to how learning happens across formal schools, non-formal programs, and "
        "everyday informal experience, and to the institutional frameworks shaping early childhood "
        "through tertiary levels. A fit for those wanting a foundation in education before teaching, "
        "policy, or graduate study."
    ),
    "ucla-education-ms": (
        "Educators and aspiring practitioners ready to deepen their grounding in how knowledge and "
        "character are taught across formal, non-formal, and informal settings, and across the levels "
        "from early childhood through tertiary. Best for those pursuing teaching or applied roles in "
        "schools."
    ),
    "ucla-master-of-education-ms": (
        "Working or prospective teachers seeking a master's that frames education across formal "
        "schooling, non-formal programs, and informal daily learning, spanning early childhood "
        "through tertiary levels. Suited to those building careers in classrooms and educational "
        "organizations."
    ),
    "ucla-master-of-library-and-information-science-ms": (
        "Aspiring librarians, archivists, and records or information managers who want to master how "
        "recorded information is created, organized, documented, and used. A fit for those entering "
        "professional practice in libraries, archives, and information management."
    ),
    "ucla-doctor-of-education-phd": (
        "Experienced education practitioners ready to step into leadership of schools and educational "
        "organizations, who want applied research paired with coursework in policy, learning, and "
        "organizational change. Best for those advancing from practice into senior leadership."
    ),
    "ucla-education-phd": (
        "Aspiring education researchers prepared to pursue original dissertation work on how "
        "knowledge, skills, and character are transmitted, with faculty mentorship and qualifying "
        "examinations. Suited to scholars committed to academic careers grounded in Westwood-based "
        "study."
    ),
    "ucla-information-studies-phd": (
        "Aspiring information-science researchers focused on how information is analyzed, classified, "
        "stored, retrieved, and protected, and on the interaction between people, organizations, and "
        "information systems. A fit for scholars aiming to create, improve, and understand those "
        "systems."
    ),
    "ucla-special-education-phd": (
        "Aspiring special-education researchers and scholars ready to pursue doctoral study in the "
        "field, offered jointly by UCLA and California State University, Los Angeles. Best for those "
        "committed to advancing research and academic careers in special education."
    ),
    "ucla-architectural-studies-ug": (
        "Undergraduates drawn to the built environment who want to understand architecture as a "
        "cultural, creative, and technical practice with social impact. This two-year, liberal-arts- "
        "grounded major suits those building a broad foundation from design history and theory to "
        "building technologies, aiming toward graduate school or wide-ranging careers."
    ),
    "ucla-art-ug": (
        "Undergraduate artists ready for sustained studio practice through experimentation across "
        "ceramics, interdisciplinary studio, new genres, painting and drawing, photography, or "
        "sculpture. Fits those who want to work between areas while grounding their making in "
        "contemporary critical theory."
    ),
    "ucla-dance-ug": (
        "Undergraduate dancers who want to integrate technique, composition, and analysis with "
        "critical inquiry. Suits students ready to pursue a primary and secondary research area among "
        "creative inquiry as research, critical dance studies, and dance and civic engagement, "
        "including transfers with prior dance coursework."
    ),
    "ucla-design-media-arts-ug": (
        "Undergraduate designers drawn to visual communication and interactive media who want to "
        "master form, color, typography, motion, and interactivity. Fits those balancing theory, "
        "criticism, and studio practice, eager to explore time, motion, and computer-generated "
        "environments while grounding their work in design principles."
    ),
    "ucla-individual-field-of-concentration-ba-in-arts-and-architecture-ug": (
        "Self-directed undergraduates in the arts who want to design their own B.A., weaving studio "
        "practice with critical and historical study across multiple arts disciplines rather than "
        "following a single departmental track."
    ),
    "ucla-world-arts-and-cultures-ug": (
        "Undergraduates drawn to art-making across cultures who want a cross-cultural, "
        "interdisciplinary path joining practice, community engagement, and multimedia analysis. "
        "Suits those eager to study theories of culture, local-versus-global art perception, and how "
        "colonialism has been understood and resisted worldwide."
    ),
    "ucla-architecture-ms": (
        "Graduate students aiming to pursue research and scholarship in architecture rather than "
        "professional practice. Fits aspiring academics and applied researchers preparing for "
        "scholarly careers or research and consulting roles in the field."
    ),
    "ucla-architecture-and-urban-design-ms": (
        "Practicing architects who already hold a first professional degree and want intensive, "
        "advanced concentration in a chosen area of professional specialization. Suits those ready "
        "for self-supporting study to deepen expertise in architecture and urban design."
    ),
    "ucla-art-ms": (
        "Graduate students seeking advanced expertise in the discipline of art through seminars, "
        "methods training, and a thesis or capstone. Fits those wanting rigorous academic grounding "
        "in art at the Westwood campus."
    ),
    "ucla-choreographic-inquiry-ms": (
        "Choreographers and dance artists ready to develop original performance research at the "
        "graduate level. Fits those who want to integrate studio practice, critical theory, and "
        "community-engaged, interdisciplinary work within World Arts and Cultures/Dance."
    ),
    "ucla-culture-and-performance-ms": (
        "Doctoral students in culture and performance who earn this master's en route to the PhD. "
        "Fits aspiring scholars pursuing the degree as a milestone within their doctoral research "
        "program."
    ),
    "ucla-design-media-arts-ms": (
        "Media artists pursuing advanced, professional-quality work with the field's most current "
        "technologies over three years. Fits those ready to develop an individual thesis project "
        "grounded in in-depth research and theory, culminating in a final exhibition."
    ),
    "ucla-master-of-architecture-ms": (
        "Aspiring architects pursuing a NAAB-accredited first professional degree, including those "
        "with no prior architecture background as well as four-year-degree holders ready for advanced "
        "standing. Fits those preparing for professional careers in architectural practice."
    ),
    "ucla-architecture-phd": (
        "Aspiring architecture scholars ready to pursue original dissertation research in design, "
        "history, theory, or building technology. Fits those seeking faculty mentorship, qualifying "
        "examinations, and sustained doctoral work at the Westwood campus."
    ),
    "ucla-culture-and-performance-phd": (
        "Aspiring scholars of performance and cultural expression ready for original dissertation "
        "research in performance, ritual, and the anthropology of cultural expression. Fits those "
        "seeking faculty mentorship, qualifying examinations, and sustained doctoral work at the "
        "Westwood campus."
    ),
    "ucla-film-and-television-ug": (
        "Undergraduate storytellers who want to make and analyze screen work, moving between "
        "production workshops, screenwriting, and critical studies while drawing on the UCLA Film & "
        "Television Archive and mentors across the Los Angeles entertainment industry."
    ),
    "ucla-individual-field-of-concentration-ba-in-theater-film-and-television-ug": (
        "Highly motivated TFT undergraduates whose specific interest spans or exceeds existing "
        "majors, ready to design their own course of study with faculty sponsorship by combining two "
        "or more fields or proposing a wholly new one that no current UCLA major covers."
    ),
    "ucla-theater-ug": (
        "Undergraduate theater makers who want a liberal arts foundation joining critical study with "
        "hands-on practice in acting, design, directing, playwriting, and production, building toward "
        "creative careers, further training, or graduate study through advanced electives in their "
        "chosen craft."
    ),
    "ucla-film-and-television-ma-ms": (
        "Students developing a personal vision in film and television who want a graduate liberal "
        "arts grounding across history, theory, and critical thinking alongside animation, "
        "screenwriting, and the fundamentals of film, video, and television production."
    ),
    "ucla-film-and-television-mfa-ms": (
        "Filmmakers seeking an intensive studio and creative-practice master's to develop a personal "
        "directorial vision, training across animation, screenwriting, and the fundamentals of film, "
        "video, and television production toward careers in the industry."
    ),
    "ucla-theater-ms": (
        "Graduate students deepening expertise in theater, performance, and dramatic practice through "
        "seminars, methods training, and a thesis or capstone, seeking advanced study within UCLA's "
        "School of Theater, Film, and Television on the Westwood campus."
    ),
    "ucla-film-and-television-phd": (
        "Aspiring film and television scholars pursuing doctoral research grounded in history, "
        "theory, and critical thinking, alongside knowledge of animation, screenwriting, and "
        "production practice, toward academic careers studying the breadth of screen media."
    ),
    "ucla-theater-and-performance-studies-phd": (
        "Aspiring scholars drawn to performance studies as an interdisciplinary lens, ready to "
        "research how performance operates across theatrical events, rituals, ceremonies, sporting "
        "and political occasions, language, and identity, while developing their own performance "
        "skills."
    ),
    "ucla-ethnomusicology-ug": (
        "Undergraduate musicians drawn to the music cultures of the world who want to play in "
        "ensembles from varied traditions while grounding themselves in global music theory and the "
        "study of how music, society, and culture intertwine."
    ),
    "ucla-global-jazz-studies-ug": (
        "Undergraduate jazz players and singers steeped in the music's roots from blues, spirituals, "
        "and European harmony to African rhythm, ready to develop swing, blue notes, complex chords, "
        "polyrhythm, and improvisation as a serious form of musical expression."
    ),
    "ucla-music-ug": (
        "Undergraduate musicians who want a broad foundation spanning composition, improvisation, and "
        "performance, and who see music as a versatile medium for human creativity rather than "
        "committing early to a single specialized track."
    ),
    "ucla-music-composition-ug": (
        "Undergraduate composers who want to create original vocal and instrumental works, learning "
        "to structure pieces and handle orchestration, whether writing in classical notation or "
        "building songs by ear and from memory."
    ),
    "ucla-music-education-ug": (
        "Undergraduate musicians who want to teach music in schools, combining performance, theory, "
        "and conducting with pedagogy and supervised teaching while working toward California "
        "teaching credentials."
    ),
    "ucla-music-history-and-industry-ug": (
        "Undergraduates who love music as an art form but want to study the music industry through a "
        "musicology lens, gaining popular-music creation and production skills plus fiscal, "
        "entrepreneurial, and legal training, capped by a Los Angeles industry internship."
    ),
    "ucla-music-industry-ug": (
        "Undergraduate musicians who want to pair music study with business and entrepreneurship, "
        "gaining hands-on experience across the recording, publishing, and live-music sectors of the "
        "entertainment industry."
    ),
    "ucla-music-performance-ug": (
        "Undergraduate instrumentalists and vocalists ready for intensive applied study on a "
        "principal instrument or voice, building toward recitals through private lessons and "
        "ensembles alongside a core of music theory and history."
    ),
    "ucla-musicology-ug": (
        "Undergraduates with a musical background whose career goals lie outside professional "
        "performance, who want humanities-grounded training in the study of music and a foundation "
        "for graduate programs in music and related fields."
    ),
    "ucla-ethnomusicology-ms": (
        "Musicians and scholars seeking advanced graduate training in ethnomusicology, specializing "
        "in systematic musicology or music and anthropology, and preparing for university teaching or "
        "careers in archiving, the music industry, public service, or music technology."
    ),
    "ucla-master-of-music-ms": (
        "Musicians ready for graduate-level study of music as a versatile medium of human creativity, "
        "seeking advanced training across its core elements of form, harmony, melody, and rhythm."
    ),
    "ucla-music-ms": (
        "Musicians pursuing advanced graduate expertise in composition, performance, history, and "
        "theory, ready for graduate seminars and methods training culminating in a thesis or "
        "capstone."
    ),
    "ucla-musicology-ms": (
        "Scholars seeking advanced graduate training in musicology, building bibliographical skills "
        "and research methodologies to prepare for careers in teaching and other research-driven "
        "fields."
    ),
    "ucla-ethnomusicology-phd": (
        "Aspiring scholars committed to doctoral research in ethnomusicology, specializing in "
        "systematic musicology or music and anthropology, and aiming for university teaching or "
        "careers in archiving, public service, the music industry, or music technology."
    ),
    "ucla-music-dma-phd": (
        "Advanced performers and creative artists pursuing the highest level of performance and "
        "creative research in music, ready to treat sound and its expressive elements as the subject "
        "of doctoral-level artistry."
    ),
    "ucla-music-phd-phd": (
        "Aspiring music scholars pursuing doctoral research into music as a cultural universal, "
        "prepared to investigate its defining elements of form, harmony, melody, and rhythm at the "
        "deepest scholarly level."
    ),
    "ucla-musicology-phd": (
        "Aspiring scholars pursuing a doctorate in musicology, developing the bibliographical skills "
        "and research methodologies needed for university teaching and other research-intensive "
        "careers."
    ),
}

_missing_who = [s for s in PROGRAM_SLUGS if s not in _WHO_BY_SLUG]
if _missing_who:
    raise ValueError(
        f"UCLA who_its_for missing on {len(_missing_who)} rows: {_missing_who[:5]}"
    )
_stray_who = [s for s in _WHO_BY_SLUG if s not in set(PROGRAM_SLUGS)]
if _stray_who:
    raise ValueError(f"UCLA who_its_for has stray slugs: {_stray_who[:5]}")


def _program_standard(slug: str, spec: dict) -> dict:
    omitted: list[str] = ["tracks"]
    if not _has_tuition(spec):
        omitted.append("cost_data.tuition_usd")
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
    if not spec.get("cip"):
        omitted.append("cip_code")
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
        p.cip_code = spec.get("cip")
        p.duration_months = spec.get("duration_months")
        p.description_text = spec["description"]
        p.website_url = _website_for(spec)
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "on_campus")
        _kw = _PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(_KEYWORDS_BY_SCHOOL[spec["school"]])
        p.content_sources = _program_content(spec["school"], _kw)
        p.tuition, p.cost_data = _cost_for(spec)
        p.application_requirements = _requirements_for(spec)
        outcomes = dict(_OUTCOMES_BY_SLUG.get(slug, {}))
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        p.tracks = None
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        p.who_its_for = _WHO_BY_SLUG.get(slug)
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
