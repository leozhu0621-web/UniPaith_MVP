"""Boston University — gold-standard profile data (institution + schools + program catalog).

Mirrors the MIT / Sloan / MBAn reference instance (see ``mit_profile.py`` /
``uiuc_profile.py``): every value is researched from an authoritative source and
carries a citation, or is honestly omitted (recorded in that node's
``_standard.omitted``) — never guessed. Built 2026-06-13 from:

  * U.S. Dept. of Education **College Scorecard** API + **IPEDS** (UNITID 164988):
    admit rate, average net price, cost of attendance, ten-year median earnings,
    six-year completion, first-year retention, Pell/loan rates, median debt,
    endowment, undergraduate race/ethnicity, and SAT/ACT middle-50% scores.
  * **Boston University Common Data Set 2024-2025** and the BU Annual Report 2024:
    the Fall 2024 first-year admissions funnel (78,769 applicants / 8,749 admitted /
    3,268 enrolled), total enrollment (37,737 students; 18,805 undergraduates), and
    the 11:1 student-faculty ratio.
  * Rankings: **U.S. News Best Colleges 2026** (#42 National), **QS 2026** (#88),
    **Times Higher Education 2026** (#76), Carnegie R1, and New England Commission
    of Higher Education (NECHE) accreditation, each cited.
  * The official **BU Academics degree-programs index** (bu.edu/academics/degree-programs):
    the full published degree catalog parsed across BU's 22 schools/colleges, plus
    CGS and ROTC programs added from their school indexes. Metropolitan College
    programs carry ``delivery_format = "online"`` where applicable. Minors,
    certificates-only listings, and non-degree options are excluded except ROTC
    commissioning programs.
  * BU leadership pages and school websites for each unit's dean/director, and a
    verified 5-photo Wikimedia Commons campus gallery (author + license confirmed
    via the Commons API).
  * Verified third-party coverage + official rankings for flagship coverable
    programs (computer science, data science, the MBA, the J.D., the M.D., the DMD,
    the MPH, the MSW, engineering, journalism, hospitality, international relations,
    film & television, Questrom MSBA/MS Finance/MSMFT, CDS MSDS, MET online CS,
    and additional CAS sciences/economics majors).

Catalog repair (2026-06-14): disambiguated all 483 programs — bare-abbr names
(BA/MS/PhD stubs), ``department=="Programs"``, and template descriptions replaced
with credential-specific names, real departments, and field-specific descriptions
(``validate_catalog`` gate).

Depth pass (2026-06-15): external_reviews expanded from 14 → 34 coverable
flagship programs (Questrom analytics/finance, CDS MSDS, MET online CS/analytics,
engineering, CAS economics/physics/chemistry/psychology/math, COM journalism MS,
SHA MS, SSW online, SPH MBA/MPH, MD/MBA). Remaining coverable programs record
``external_reviews.summary`` in ``_standard.omitted`` pending future runs.

Honest caveats stamped into ``_standard.omitted``: BU does not publish a single
university-wide placement rate or a uniform top-employer-industries list across all
schools, so those two institution outcome fields are omitted (the Scorecard ten-year
median earnings is kept). Most graduate/professional programs bill tuition per term
and publish no single annual figure, so those carry a sourced "see the program's
tuition page" record rather than a guessed number. This is a large catalog
(483 programs); external reviews are attached to 34 flagship coverable programs and
the remaining programs record deep fields in their ``_standard.omitted`` pending
future depth passes.
"""

# ruff: noqa: E501

from __future__ import annotations

import re
from collections import Counter

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.profile_catalog_utils import (
    BARE_DEGREE_ABBREVIATIONS,
    disambiguate_program_name,
    program_description,
    validate_catalog,
)
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Boston University"
ENRICHED_AT = "2026-06-15"


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


_OMITTED_INSTITUTION: list[str] = [
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
]

RANKING_DATA: dict = {
    "ownership_type": "private",
    "accreditor": "New England Commission of Higher Education (NECHE)",
    "carnegie_classification": (
        "Doctoral Universities: Very High Research Spending and Doctorate Production (R1)"
    ),
    "qs_world_university_rankings": {
        "rank": 88, "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/boston-university",
    },
    "times_higher_education": {
        "rank": 76, "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/boston-university",
    },
    "us_news_national": {
        "rank": 42, "year": 2026,
        "source_url": "https://www.usnews.com/best-colleges/boston-university-2130",
    },
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.1111,
    "avg_net_price": 24402,
    "median_earnings_10yr": 83238,
    "graduation_rate_6yr": 0.8866,
    "completion_rate_4yr_150pct": 0.8866,
    "retention_rate_first_year": 0.9472,
    "financial_aid": {
        "pell_grant_rate": 0.1915,
        "federal_loan_rate": 0.2292,
        "median_debt_completers": 23250,
        "cost_of_attendance": 86285,
        "avg_net_price": 24402,
    },
    "demographics": {
        "white": 0.3222, "asian": 0.2055, "hispanic": 0.1145, "black": 0.0592,
        "two_or_more": 0.0472, "american_indian": 0.0005, "pacific_islander": 0.0009,
        "international": 0.212, "unknown": 0.038, "women": 0.5813,
    },
    "test_scores": {
        "sat_reading_25_75": [690, 750],
        "sat_math_25_75": [730, 780],
        "act_25_75": [32, 34],
        "year": 2024,
        "source": "College Scorecard / BU Common Data Set 2024-2025 (middle 50% of enrolled first-year students who submitted scores; BU is test-optional)",
    },
    "campus_basics": {"location": "Boston, Massachusetts"},
    "scale": {
        "faculty_count": 4309,
        "student_faculty_ratio": "11:1",
        "endowment_usd": 3528624000,
        "campus_acres": 140,
    },
    "location": {"lat": 42.3505, "lng": -71.1054},
    "research": {
        "labs": [
            "Boston University Photonics Center",
            "National Emerging Infectious Diseases Laboratories (NEIDL)",
            "Rafik B. Hariri Institute for Computing and Computational Science & Engineering",
            "Boston University CTE Center",
            "Institute for Global Sustainability",
            "Center for Systems Neuroscience",
            "Frederick S. Pardee Center for the Study of the Longer-Range Future",
        ],
        "areas": [
            "Photonics and optical science",
            "Emerging infectious diseases",
            "Computing, data sciences, and artificial intelligence",
            "Neuroscience and neurodegenerative disease (including CTE)",
            "Climate and global sustainability",
            "Biomedical engineering and life sciences",
        ],
        "lab_links": {
            "Boston University Photonics Center": "https://www.bu.edu/photonics/",
            "National Emerging Infectious Diseases Laboratories (NEIDL)": "https://www.bu.edu/neidl/",
            "Rafik B. Hariri Institute for Computing and Computational Science & Engineering": "https://www.bu.edu/hic/",
            "Boston University CTE Center": "https://www.bu.edu/cte/",
            "Institute for Global Sustainability": "https://www.bu.edu/igs/",
            "Center for Systems Neuroscience": "https://www.bu.edu/csn/",
            "Frederick S. Pardee Center for the Study of the Longer-Range Future": "https://www.bu.edu/pardee/",
        },
    },
    "campus_life": {
        "student_orgs": 450,
        "varsity_sports": 24,
        "athletics_division": "NCAA Division I (Patriot League; Hockey East for ice hockey)",
        "resources": [
            {"name": "Boston University Athletics (GoTerriers)", "url": "https://goterriers.com/"},
            {"name": "Student Leadership & Impact Center (student organizations)", "url": "https://www.bu.edu/studentactivities/"},
            {"name": "Boston University Housing", "url": "https://www.bu.edu/housing/"},
            {"name": "BU Office for the Arts", "url": "https://www.bu.edu/arts/"},
        ],
    },
    "media_credit": "Wikimedia Commons / Pacamah (CC BY-SA 4.0)",
    "campus_photos": [
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Aerial_Boston_University.jpg/1920px-Aerial_Boston_University.jpg",
         "credit": "Wikimedia Commons / Pacamah (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Boston_University_East_Campus_May_2014.jpg/1920px-Boston_University_East_Campus_May_2014.jpg",
         "credit": "Wikimedia Commons / 4300streetcar (CC BY 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Boston_University%2C_West_Campus_Dorms%2C_Claflin_Hall_%28pano%29.jpg/1920px-Boston_University%2C_West_Campus_Dorms%2C_Claflin_Hall_%28pano%29.jpg",
         "credit": "Wikimedia Commons / Beyond My Ken (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Boston_University%2C_West_Campus_Dorms%2C_Sleeper_and_Rich_Halls.jpg/1920px-Boston_University%2C_West_Campus_Dorms%2C_Sleeper_and_Rich_Halls.jpg",
         "credit": "Wikimedia Commons / Beyond My Ken (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Boston_University_Medical_Campus_01.JPG/1920px-Boston_University_Medical_Campus_01.JPG",
         "credit": "Wikimedia Commons / Cmcnicoll at English Wikipedia (Public domain)"},
    ],
    "flagship": {
        "enrollment_total": 37737,
        "applicants": 78769,
        "admits": 8749,
        "admissions_cycle": "First-year, Fall 2024 (BU Common Data Set 2024-2025)",
        "founded_year": 1839,
    },
    "sources": [
        {"label": "U.S. Dept. of Education — College Scorecard (Boston University, UNITID 164988)",
         "url": "https://collegescorecard.ed.gov/school/?164988-Boston-University"},
        {"label": "NCES College Navigator — Boston University (IPEDS)",
         "url": "https://nces.ed.gov/collegenavigator/?id=164988"},
        {"label": "Boston University Common Data Set 2024-2025 (admissions funnel, enrollment, test scores)",
         "url": "https://www.bu.edu/asir/files/2025/03/cds-2025.pdf"},
        {"label": "BU Annual Report 2024 — Class of 2028 admissions",
         "url": "https://ar.bu.edu/2024/town-square/brimming-with-brilliance/"},
        {"label": "Boston University — Academics degree programs index",
         "url": "https://www.bu.edu/academics/degree-programs/"},
        {"label": "Boston University — Schools & Colleges",
         "url": "https://www.bu.edu/academics/schools-colleges/"},
        {"label": "Carnegie Classifications — Boston University (R1)",
         "url": "https://carnegieclassifications.acenet.edu/institution/boston-university/"},
        {"label": "QS World University Rankings 2026 — Boston University (#88)",
         "url": "https://www.topuniversities.com/universities/boston-university"},
        {"label": "Times Higher Education World University Rankings 2026 — Boston University (#76)",
         "url": "https://www.timeshighereducation.com/world-university-rankings/boston-university"},
        {"label": "U.S. News Best Colleges 2026 — Boston University (#42 National)",
         "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
    ],
}

UNDERGRAD_COUNT = 18805

DESCRIPTION = (
    "Boston University is a private research university in Boston, MA, founded in 1839 and "
    "chartered in the city in 1869. One of the largest private universities in the United States, "
    "BU enrolls 37,737 students from more than 140 countries across 22 schools and colleges and "
    "is a member of the Association of American Universities. Fall 2024 brought a record 78,769 "
    "first-year applications and an 11.1% admit rate (8,749 admitted; 3,268 enrolled), with "
    "roughly 18,805 undergraduates and more than 18,900 graduate and professional students and "
    "an 11:1 student-faculty ratio.\n\n"
    "BU is organized into schools and colleges spanning the Charles River Campus and the Medical "
    "Campus — including the College of Arts & Sciences, Questrom School of Business, the College "
    "of Engineering, the Faculty of Computing & Data Sciences, the Chobanian & Avedisian School "
    "of Medicine, the School of Law, Metropolitan College (online and part-time degrees), and "
    "Wheelock College of Education & Human Development. Together they offer more than "
    "483 degree programs across the bachelor's, master's, professional, and doctoral "
    "levels, including online and hybrid programs through Metropolitan College.\n\n"
    "A Carnegie R1 university accredited by the New England Commission of Higher Education, BU "
    "ranks #42 among national universities by U.S. News, #76 in the world by Times Higher Education, "
    "and #88 by QS for 2026. Its research footprint runs from the Photonics Center and the Hariri "
    "Institute for Computing to the National Emerging Infectious Diseases Laboratories (NEIDL), "
    "threaded along the dense urban spine of its 140-acre Charles River Campus.\n\n"
    "BU's published cost of attendance is about $86,285 a year, but its average net price after "
    "grant aid is about $24,402 and the median federal debt of completers is about $23,250. BU "
    "graduates earn a median of roughly $83,238 ten years after entry. The Terriers compete in "
    "NCAA Division I (Patriot League; Hockey East for ice hockey)."
)

_SCHOOL_META = [
    {"key": "CAS", "name": "College of Arts & Sciences", "sort_order": 1, "website": "https://www.bu.edu/cas/", "leadership": "Stanley S. Sclaroff — Dean", "research_centers": ["Department of Computer Science", "Department of Economics", "Department of Physics", "Department of Earth & Environment", "Center for the Humanities"], "keywords": ["College of Arts & Sciences", "CAS", "arts and sciences"]},
    {"key": "COM", "name": "College of Communication", "sort_order": 2, "website": "https://www.bu.edu/com/", "leadership": "Maggie Little — Dean", "research_centers": ["Department of Journalism", "Department of Film & Television", "Department of Mass Communication, Advertising & Public Relations"], "keywords": ["College of Communication", "COM", "journalism", "film"]},
    {"key": "ENG", "name": "College of Engineering", "sort_order": 3, "website": "https://www.bu.edu/eng/", "leadership": "Kenneth R. Lutchen — Dean", "research_centers": ["Department of Biomedical Engineering", "Department of Electrical & Computer Engineering", "Department of Mechanical Engineering", "Division of Materials Science & Engineering"], "keywords": ["College of Engineering", "engineering", "ENG"]},
    {"key": "CFA", "name": "College of Fine Arts", "sort_order": 4, "website": "https://www.bu.edu/cfa/", "leadership": "Andre de Quadros — Dean", "research_centers": ["School of Music", "School of Theatre", "School of Visual Arts"], "keywords": ["College of Fine Arts", "CFA", "music", "theatre", "visual arts"]},
    {"key": "CGS", "name": "College of General Studies", "sort_order": 5, "website": "https://www.bu.edu/cgs/", "leadership": "Nathaniel M. Simmons — Dean", "research_centers": ["Two-year liberal arts core curriculum", "Interdisciplinary studies"], "keywords": ["College of General Studies", "CGS", "general studies"]},
    {"key": "CDS", "name": "Faculty of Computing & Data Sciences", "sort_order": 6, "website": "https://www.bu.edu/cds/", "leadership": "Azer Bestavros — Founding Director", "research_centers": ["Center for Computing & Data Sciences", "Data Science, AI, and computing across disciplines"], "keywords": ["Faculty of Computing & Data Sciences", "CDS", "data science", "computing"]},
    {"key": "PARDEE", "name": "Frederick S. Pardee School of Global Studies", "sort_order": 7, "website": "https://www.bu.edu/pardee/", "leadership": "Adil Najam — Dean", "research_centers": ["International relations and regional studies", "Global development and security"], "keywords": ["Pardee School of Global Studies", "Pardee", "international relations"]},
    {"key": "QUESTROM", "name": "Questrom School of Business", "sort_order": 8, "website": "https://www.bu.edu/questrom/", "leadership": "Susan F. Fournier — Dean", "research_centers": ["Department of Finance", "Department of Markets, Public Policy & Law", "Digital Business & AI initiatives"], "keywords": ["Questrom School of Business", "Questrom", "business", "MBA"]},
    {"key": "SHA", "name": "School of Hospitality Administration", "sort_order": 9, "website": "https://www.bu.edu/hospitality/", "leadership": "Arun Upneja — Dean", "research_centers": ["Hospitality management", "Hotel, restaurant, and tourism industries"], "keywords": ["School of Hospitality Administration", "SHA", "hospitality"]},
    {"key": "WHEEL", "name": "Wheelock College of Education & Human Development", "sort_order": 10, "website": "https://www.bu.edu/wheelock/", "leadership": "David Chard — Dean", "research_centers": ["Teaching & learning", "Educational leadership & policy studies", "Counseling & applied human development"], "keywords": ["Wheelock College of Education", "Wheelock", "education"]},
    {"key": "SAR", "name": "Sargent College of Health & Rehabilitation Sciences", "sort_order": 11, "website": "https://www.bu.edu/sargent/", "leadership": "Christopher A. Moore — Dean", "research_centers": ["Department of Physical Therapy", "Department of Occupational Therapy", "Department of Speech, Language & Hearing Sciences"], "keywords": ["Sargent College", "Sargent", "health sciences", "physical therapy"]},
    {"key": "GRS", "name": "Graduate School of Arts & Sciences", "sort_order": 12, "website": "https://www.bu.edu/grs/", "leadership": "Nathaniel M. Simmons — Dean", "research_centers": ["Graduate programs across the humanities, sciences, and social sciences"], "keywords": ["Graduate School of Arts & Sciences", "GRS", "graduate arts and sciences"]},
    {"key": "GMS", "name": "Graduate Medical Sciences", "sort_order": 13, "website": "https://www.bumc.bu.edu/gms/", "leadership": "Terence R. Flotte — Dean", "research_centers": ["Biomedical sciences graduate programs", "MD/PhD and research training"], "keywords": ["Graduate Medical Sciences", "GMS", "biomedical sciences"]},
    {"key": "BUSM", "name": "Chobanian & Avedisian School of Medicine", "sort_order": 14, "website": "https://www.bumc.bu.edu/busm/", "leadership": "Karen Antman — Dean", "research_centers": ["Doctor of Medicine (M.D.) program", "Clinical and translational research on the Medical Campus"], "keywords": ["Chobanian & Avedisian School of Medicine", "BU School of Medicine", "M.D."]},
    {"key": "SDM", "name": "Henry M. Goldman School of Dental Medicine", "sort_order": 15, "website": "https://www.bu.edu/dental/", "leadership": "Cataldo Leone — Dean", "research_centers": ["Doctor of Dental Medicine (D.M.D.)", "Advanced dental specialty programs"], "keywords": ["Goldman School of Dental Medicine", "dental medicine", "DMD"]},
    {"key": "SPH", "name": "School of Public Health", "sort_order": 16, "website": "https://www.bumc.bu.edu/sph/", "leadership": "Sandro Galea — Dean", "research_centers": ["Epidemiology", "Environmental health", "Health law, policy & management"], "keywords": ["School of Public Health", "SPH", "public health", "MPH"]},
    {"key": "LAW", "name": "School of Law", "sort_order": 17, "website": "https://www.bu.edu/law/", "leadership": "Angela Onwuachi-Willig — Dean", "research_centers": ["Juris Doctor (J.D.)", "LL.M. and specialty law programs"], "keywords": ["Boston University School of Law", "BU Law", "J.D.", "law"]},
    {"key": "SSW", "name": "School of Social Work", "sort_order": 18, "website": "https://www.bu.edu/ssw/", "leadership": "Jennifer Greif Green — Dean", "research_centers": ["Master of Social Work (M.S.W.)", "Clinical and macro social work"], "keywords": ["School of Social Work", "SSW", "MSW", "social work"]},
    {"key": "STH", "name": "School of Theology", "sort_order": 19, "website": "https://www.bu.edu/sth/", "leadership": "Mary Elizabeth Moore — Dean", "research_centers": ["Master of Divinity", "Doctor of Ministry", "Theological research"], "keywords": ["School of Theology", "STH", "theology", "ministry"]},
    {"key": "MET", "name": "Metropolitan College & Extended Education", "sort_order": 20, "website": "https://www.bu.edu/met/", "leadership": "Tanya Zlateva — Dean", "research_centers": ["Part-time and online undergraduate and graduate degrees", "Professional education and degree completion"], "keywords": ["Metropolitan College", "MET", "online", "continuing education"]},
    {"key": "ROTC", "name": "Division of Military Education", "sort_order": 21, "website": "https://www.bu.edu/rotc/", "leadership": "U.S. Army, Navy, and Air Force ROTC programs", "research_centers": ["Army ROTC", "Naval ROTC", "Air Force ROTC"], "keywords": ["ROTC", "military education", "Army", "Navy", "Air Force"]},
    {"key": "KILA", "name": "Arvind & Chandan Nandlal Kilachand Honors College", "sort_order": 22, "website": "https://www.bu.edu/khc/", "leadership": "Anne E. C. McCants — Director", "research_centers": ["Honors seminars and keystone projects across BU schools"], "keywords": ["Kilachand Honors College", "KHC", "honors"]}
]
SCHOOL_NAME = {m["key"]: m["name"] for m in _SCHOOL_META}
SCHOOL_WEBSITE = {m["name"]: m["website"] for m in _SCHOOL_META}


def _school_description(m: dict) -> str:
    return (
        f"The {m['name']} is one of the 22 schools and colleges of Boston University."
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
            "label": "Boston University Schools & Colleges + unit websites",
            "url": "https://www.bu.edu/academics/schools-colleges/",
        },
    }


def _about_omitted(m: dict) -> list[str]:
    return ["about_detail.founded", "about_detail.faculty", "about_detail.named_for"]


_NEWS_URL = "https://www.bu.edu/today/"
_EVENTS = {"url": "https://www.bu.edu/phpbin/calendar/ical.php", "type": "ical"}
_SOCIAL = {
    "instagram": "https://www.instagram.com/bostonu/",
    "linkedin": "https://www.linkedin.com/school/boston-university/",
    "x": "https://twitter.com/BU_Tweets",
    "youtube": "https://www.youtube.com/channel/UCuNjAAXrEmQyxLAanISnZUw",
    "facebook": "https://www.facebook.com/BostonUniversity/",
    "tiktok": "https://www.tiktok.com/@bostonu",
}
_INSTITUTION_CONTENT: dict = {
    "news_url": _NEWS_URL,
    "news_rss": "https://www.bu.edu/today/feed/",
    "events_feed": _EVENTS,
    "news_curated": True,
    "social": _SOCIAL,
}
_KEYWORDS_BY_SCHOOL = {m["name"]: m["keywords"] for m in _SCHOOL_META}


def _school_content(name: str) -> dict:
    return {
        "news_url": SCHOOL_WEBSITE.get(name, _NEWS_URL),
        "news_rss": "https://www.bu.edu/today/feed/",
        "events_feed": _EVENTS,
        "keywords": list(_KEYWORDS_BY_SCHOOL[name]),
        "news_curated": False,
        "social": _SOCIAL,
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


_CATALOG: list[tuple] = [
    ("bu-academics-busm-four-year-program", "BUSM", "MD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/busm/programs/four-year-program/"),
    ("bu-academics-busm-combined-mdjd", "BUSM", "MD/JD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/busm/programs/combined-mdjd/"),
    ("bu-academics-busm-combined-md-mba", "BUSM", "MD/MBA", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/busm/programs/combined-md-mba/"),
    ("bu-academics-busm-md-phd-combined-degree", "BUSM", "MD/PhD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/busm/programs/md-phd-combined-degree/"),
    ("bu-academics-cas-african-american-black-diaspora-studies-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/african-american-black-diaspora-studies/ba/"),
    ("bu-academics-cas-american-new-england-studies-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/american-new-england-studies/ba/"),
    ("bu-academics-cas-classical-studies-ba-ancient-greek-latin", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/classical-studies/ba-ancient-greek-latin/"),
    ("bu-academics-cas-classical-studies-ba-ancient-greek", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/classical-studies/ba-ancient-greek/"),
    ("bu-academics-cas-anthropology-anthropology-health-medicine", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/anthropology/anthropology-health-medicine/"),
    ("bu-academics-cas-anthropology-biological-anthropology", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/anthropology/biological-anthropology/"),
    ("bu-academics-cas-anthropology-sociocultural-anthropology", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/anthropology/sociocultural-anthropology/"),
    ("bu-academics-cas-anthropology-ba-anthropology-religion", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/anthropology/ba-anthropology-religion/"),
    ("bu-academics-cas-archaeology-ba-in-archaeological-environmental-sciences", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/archaeology/ba-in-archaeological-environmental-sciences/"),
    ("bu-academics-cas-archaeology-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/archaeology/ba/"),
    ("bu-academics-cas-art-history-ba-architectural-studies", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/art-history/ba-architectural-studies/"),
    ("bu-academics-cas-art-history-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/art-history/ba/"),
    ("bu-academics-cas-astronomy-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/astronomy/ba/"),
    ("bu-academics-cas-astronomy-ba-astronomy-physics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/astronomy/ba-astronomy-physics/"),
    ("bu-academics-cas-biochemistry-molecular-biology-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/biochemistry-molecular-biology/ba/"),
    ("bu-academics-cas-biology-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/biology/ba/"),
    ("bu-academics-cas-biology-ba-behavioral", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/biology/ba-behavioral/"),
    ("bu-academics-cas-biology-ba-cell-molecular-genetics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/biology/ba-cell-molecular-genetics/"),
    ("bu-academics-cas-biology-ba-ecology-conservation", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/biology/ba-ecology-conservation/"),
    ("bu-academics-cas-biology-ba-neurobiology", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/biology/ba-neurobiology/"),
    ("bu-academics-cas-chemistry-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/chemistry/ba/"),
    ("bu-academics-cas-physics-ba-in-chemistry-physics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/physics/ba-in-chemistry-physics/"),
    ("bu-academics-cas-chemistry-ba-in-chemistry-chemical-biology", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/chemistry/ba-in-chemistry-chemical-biology/"),
    ("bu-academics-cas-chemistry-ba-in-chemistry-materials-and-nanoscience", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/chemistry/ba-in-chemistry-materials-and-nanoscience/"),
    ("bu-academics-cas-chemistry-ba-teaching", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/chemistry/ba-teaching/"),
    ("bu-academics-cas-world-languages-literatures-ba-chinese", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/world-languages-literatures/ba-chinese/"),
    ("bu-academics-cas-cinema-media-studies-ba-in-cinema-media-studies", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/cinema-media-studies/ba-in-cinema-media-studies/"),
    ("bu-academics-cas-classical-studies-ba-classical-civilization", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/classical-studies/ba-classical-civilization/"),
    ("bu-academics-cas-classical-studies-ba-in-classics-archaeology", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/classical-studies/ba-in-classics-archaeology/"),
    ("bu-academics-cas-classical-studies-ba-classics-philosophy", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/classical-studies/ba-classics-philosophy/"),
    ("bu-academics-cas-classical-studies-ba-classics-religion", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/classical-studies/ba-classics-religion/"),
    ("bu-academics-cas-world-languages-literatures-ba-comparative-literature", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/world-languages-literatures/ba-comparative-literature/"),
    ("bu-academics-cas-computer-science-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/computer-science/ba/"),
    ("bu-academics-cas-earth-environment-ba-in-earth-environmental-sciences", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/earth-environment/ba-in-earth-environmental-sciences/"),
    ("bu-academics-cas-economics-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/economics/ba/"),
    ("bu-academics-cas-economics-ba-mathematics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/economics/ba-mathematics/"),
    ("bu-academics-cas-english-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/english/ba/"),
    ("bu-academics-cas-earth-environment-ba-environmental-analysis-policy", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/earth-environment/ba-environmental-analysis-policy/"),
    ("bu-academics-cas-european-studies-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/european-studies/ba/"),
    ("bu-academics-cas-linguistics-ba-french-linguistics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/linguistics/ba-french-linguistics/"),
    ("bu-academics-cas-romance-studies-ba-french", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-french/"),
    ("bu-academics-cas-world-languages-literatures-ba-german", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/world-languages-literatures/ba-german/"),
    ("bu-academics-cas-history-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/history/ba/"),
    ("bu-academics-cas-holocaust-genocide-human-rights-studies-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/holocaust-genocide-human-rights-studies/ba/"),
    ("bu-academics-cas-international-relations-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/international-relations/ba/"),
    ("bu-academics-cas-linguistics-ba-italian-linguistics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/linguistics/ba-italian-linguistics/"),
    ("bu-academics-cas-romance-studies-ba-italian", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-italian/"),
    ("bu-academics-cas-linguistics-ba-japanese-linguistics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/linguistics/ba-japanese-linguistics/"),
    ("bu-academics-cas-world-languages-literatures-ba-japanese", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/world-languages-literatures/ba-japanese/"),
    ("bu-academics-cas-world-languages-literatures-korean-ba-in-korean-language-literature", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/world-languages-literatures/korean/ba-in-korean-language-literature/"),
    ("bu-academics-cas-latin-american-studies-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/latin-american-studies/ba/"),
    ("bu-academics-cas-classical-studies-ba-latin", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/classical-studies/ba-latin/"),
    ("bu-academics-cas-linguistics-ba-linguistics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/linguistics/ba-linguistics/"),
    ("bu-academics-cas-linguistics-ba-linguistics-philosophy", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/linguistics/ba-linguistics-philosophy/"),
    ("bu-academics-cas-linguistics-ba-in-linguistics-speech-language-and-hearing-sciences", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/linguistics/ba-in-linguistics-speech-language-and-hearing-sciences/"),
    ("bu-academics-cas-marine-science-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/marine-science/ba/"),
    ("bu-academics-cas-mathematics-statistics-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/mathematics-statistics/ba/"),
    ("bu-academics-cas-mathematics-statistics-ba-mathematics-computer-science", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/mathematics-statistics/ba-mathematics-computer-science/"),
    ("bu-academics-cas-mathematics-statistics-ba-mathematics-education", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/mathematics-statistics/ba-mathematics-education/"),
    ("bu-academics-cas-mathematics-statistics-ba-mathematics-philosophy", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/mathematics-statistics/ba-mathematics-philosophy/"),
    ("bu-academics-cas-mathematics-statistics-ba-in-mathematics-physics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/mathematics-statistics/ba-in-mathematics-physics/"),
    ("bu-academics-cas-ba-in-middle-east-north-africa-studies", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/ba-in-middle-east-north-africa-studies/"),
    ("bu-academics-cas-world-languages-literatures-bachelor-of-arts-in-middle-eastern-and-south-asian-languages-literatures", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/world-languages-literatures/bachelor-of-arts-in-middle-eastern-and-south-asian-languages-literatures/"),
    ("bu-academics-cas-neuroscience", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/neuroscience/"),
    ("bu-academics-cas-philosophy-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/philosophy/ba/"),
    ("bu-academics-cas-philosophy-ba-in-philosophy-neuroscience", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/philosophy/ba-in-philosophy-neuroscience/"),
    ("bu-academics-cas-philosophy-ba-physics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/philosophy/ba-physics/"),
    ("bu-academics-cas-philosophy-ba-political-science", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/philosophy/ba-political-science/"),
    ("bu-academics-cas-philosophy-ba-psychology", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/philosophy/ba-psychology/"),
    ("bu-academics-cas-philosophy-ba-philosophy-religion", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/philosophy/ba-philosophy-religion/"),
    ("bu-academics-cas-physics-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/physics/ba/"),
    ("bu-academics-cas-physics-ba-in-physics-computer-science", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/physics/ba-in-physics-computer-science/"),
    ("bu-academics-cas-political-science-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/political-science/ba/"),
    ("bu-academics-cas-psychology-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/psychology/ba/"),
    ("bu-academics-cas-religion-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/religion/ba/"),
    ("bu-academics-cas-world-languages-literatures-ba-russian", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/world-languages-literatures/ba-russian/"),
    ("bu-academics-cas-ba-in-science-education", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/ba-in-science-education/"),
    ("bu-academics-cas-sociology-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/sociology/ba/"),
    ("bu-academics-cas-romance-studies-ba-spanish", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-spanish/"),
    ("bu-academics-cas-linguistics-ba-spanish-linguistics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/linguistics/ba-spanish-linguistics/"),
    ("bu-academics-cas-mathematics-statistics-ba-in-statistics-computer-science", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/mathematics-statistics/ba-in-statistics-computer-science/"),
    ("bu-academics-cas-archaeology-ba-ma", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/archaeology/ba-ma/"),
    ("bu-academics-cas-archaeology-bama-in-archaeology", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/archaeology/bama-in-archaeology/"),
    ("bu-academics-cas-astronomy-ba-ma-astrophysics", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/astronomy/ba-ma-astrophysics/"),
    ("bu-academics-cas-classical-studies-ba-ma", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/classical-studies/ba-ma/"),
    ("bu-academics-cas-classical-studies-ba-ma-in-classics-archaeology", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/classical-studies/ba-ma-in-classics-archaeology/"),
    ("bu-academics-cas-english-bama-in-english", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/english/bama-in-english/"),
    ("bu-academics-cas-international-relations-ba-in-international-relationsma-in-international-affairs", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/international-relations/ba-in-international-relationsma-in-international-affairs/"),
    ("bu-academics-cas-linguistics-bama-in-linguistics", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/linguistics/bama-in-linguistics/"),
    ("bu-academics-cas-mathematics-statistics-ba-ma", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/mathematics-statistics/ba-ma/"),
    ("bu-academics-cas-physics-ba-ma", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/physics/ba-ma/"),
    ("bu-academics-cas-romance-studies-ba-in-ancient-greek-mfa-in-literary-translation", "CAS", "BA-to-MFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-ancient-greek-mfa-in-literary-translation/"),
    ("bu-academics-cas-romance-studies-ba-in-chinese-mfa-in-literary-translation", "CAS", "BA-to-MFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-chinese-mfa-in-literary-translation/"),
    ("bu-academics-cas-romance-studies-ba-in-french-studies-mfa-in-literary-translation", "CAS", "BA-to-MFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-french-studies-mfa-in-literary-translation/"),
    ("bu-academics-cas-romance-studies-ba-in-german-mfa-in-literary-translation", "CAS", "BA-to-MFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-german-mfa-in-literary-translation/"),
    ("bu-academics-cas-romance-studies-ba-in-japanese-mfa-in-literary-translation", "CAS", "BA-to-MFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-japanese-mfa-in-literary-translation/"),
    ("bu-academics-cas-romance-studies-ba-in-latin-mfa-in-literary-translation", "CAS", "BA-to-MFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-latin-mfa-in-literary-translation/"),
    ("bu-academics-cas-romance-studies-ba-in-spanish-mfa-in-literary-translation", "CAS", "BA-to-MFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-spanish-mfa-in-literary-translation/"),
    ("bu-academics-cas-bamph-program", "CAS", "BA-to-MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/bamph-program/"),
    ("bu-academics-cas-computer-science-ba-ms", "CAS", "BA-to-MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/computer-science/ba-ms/"),
    ("bu-academics-cas-economics-ba-ma", "CAS", "BA-to-MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/economics/ba-ma/"),
    ("bu-academics-cas-economics-ba-econ-math-ma", "CAS", "BA-to-MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/economics/ba-econ-math-ma/"),
    ("bu-academics-cas-earth-environment-bama-energy-environment", "CAS", "BA-to-MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/earth-environment/bama-energy-environment/"),
    ("bu-academics-cas-mathematics-statistics-ba-in-mathematics-computer-science-ms-in-computer-science", "CAS", "BA-to-MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/mathematics-statistics/ba-in-mathematics-computer-science-ms-in-computer-science/"),
    ("bu-academics-cas-earth-environment-bama-in-remote-sensing-geospatial-sciences", "CAS", "BA-to-MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/earth-environment/bama-in-remote-sensing-geospatial-sciences/"),
    ("bu-academics-cas-biochemistry-molecular-biology-ba-ma", "CAS", "BA/MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/biochemistry-molecular-biology/ba-ma/"),
    ("bu-academics-cas-chemistry-ba-ma", "CAS", "BA/MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/chemistry/ba-ma/"),
    ("bu-academics-cas-world-languages-literatures-ba-in-comparative-literature-mfa-in-literary-translation", "CAS", "BA/MFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/world-languages-literatures/ba-in-comparative-literature-mfa-in-literary-translation/"),
    ("bu-academics-cds-bs-in-data-science", "CDS", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cds/programs/bs-in-data-science/"),
    ("bu-academics-cds-bs-ms", "CDS", "BS-to-MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cds/programs/bs-ms/"),
    ("bu-academics-cds-bs-data-science-ms-bioinformatics", "CDS", "BS-to-MS (Bioinformatics)", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cds/programs/bs-data-science-ms-bioinformatics/"),
    ("bu-academics-cds-ms-in-bioinformatics", "CDS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cds/programs/ms-in-bioinformatics/"),
    ("bu-academics-cds-ms-in-data-science", "CDS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cds/programs/ms-in-data-science/"),
    ("bu-academics-cds-ms-in-data-science-online", "CDS", "MS (online)", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/cds/programs/ms-in-data-science-online/"),
    ("bu-academics-cds-phd-in-bioinformatics", "CDS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/cds/programs/phd-in-bioinformatics/"),
    ("bu-academics-cds-phd-in-computing-data-sciences", "CDS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/cds/programs/phd-in-computing-data-sciences/"),
    ("bu-academics-cfa-school-of-visual-arts-ba-in-art", "CFA", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/ba-in-art/"),
    ("bu-academics-cfa-school-of-music-music", "CFA", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-music/music/"),
    ("bu-academics-cfa-school-of-theatre-acting", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-theatre/acting/"),
    ("bu-academics-cfa-school-of-visual-arts-art-education-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/art-education/bfa/"),
    ("bu-academics-cfa-school-of-visual-arts-graphic-design-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/graphic-design/bfa/"),
    ("bu-academics-cfa-school-of-theatre-lighting-design-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-theatre/lighting-design/bfa/"),
    ("bu-academics-cfa-school-of-visual-arts-painting-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/painting/bfa/"),
    ("bu-academics-cfa-school-of-visual-arts-printmaking-2-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/printmaking-2/bfa/"),
    ("bu-academics-cfa-school-of-theatre-scene-design-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-theatre/scene-design/bfa/"),
    ("bu-academics-cfa-school-of-visual-arts-sculpture-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/sculpture/bfa/"),
    ("bu-academics-cfa-school-of-theatre-sound-design-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-theatre/sound-design/bfa/"),
    ("bu-academics-cfa-school-of-theatre-stage-management-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-theatre/stage-management/bfa/"),
    ("bu-academics-cfa-school-of-theatre-technical-production-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-theatre/technical-production/bfa/"),
    ("bu-academics-cfa-school-of-visual-arts-bfa-ma", "CFA", "BFA/MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/bfa-ma/"),
    ("bu-academics-cfa-school-of-theatre-theatre-arts-bfa-design-production", "CFA", "BFA—Design &amp; Production", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-theatre/theatre-arts/bfa-design-production/"),
    ("bu-academics-cfa-school-of-theatre-theatre-arts-bfa-performance", "CFA", "BFA—Performance", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-theatre/theatre-arts/bfa-performance/"),
    ("bu-academics-cfa-school-of-music-composition-bm", "CFA", "BM", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-music/composition/bm/"),
    ("bu-academics-cfa-school-of-music-music-education-bm", "CFA", "BM", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-music/music-education/bm/"),
    ("bu-academics-cfa-school-of-music-performance-bm", "CFA", "BM", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-music/performance/bm/"),
    ("bu-academics-cfa-school-of-music-music-education-bm-mm", "CFA", "BM-to-MM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/music-education/bm-mm/"),
    ("bu-academics-cfa-school-of-music-music-education-cags", "CFA", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/cfa/programs/school-of-music/music-education/cags/"),
    ("bu-academics-cfa-school-of-music-composition-dma", "CFA", "DMA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/composition/dma/"),
    ("bu-academics-cfa-school-of-music-conducting-dma", "CFA", "DMA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/conducting/dma/"),
    ("bu-academics-cfa-school-of-music-historical-performance-dma", "CFA", "DMA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/historical-performance/dma/"),
    ("bu-academics-cfa-school-of-music-performance-dma", "CFA", "DMA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/performance/dma/"),
    ("bu-academics-cfa-school-of-visual-arts-art-education-online-ma-in-art-education", "CFA", "MA", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/art-education/online-ma-in-art-education/"),
    ("bu-academics-cfa-school-of-visual-arts-art-education-art-education-with-initial-license", "CFA", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/art-education/art-education-with-initial-license/"),
    ("bu-academics-cfa-school-of-visual-arts-museum-education", "CFA", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/museum-education/"),
    ("bu-academics-cfa-school-of-music-musicology-ma", "CFA", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/musicology/ma/"),
    ("bu-academics-cfa-school-of-music-music-theory", "CFA", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/music-theory/"),
    ("bu-academics-cfa-school-of-music-composition-mm", "CFA", "MM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/composition/mm/"),
    ("bu-academics-cfa-school-of-music-conducting-mm", "CFA", "MM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/conducting/mm/"),
    ("bu-academics-cfa-school-of-music-historical-performance-mm", "CFA", "MM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/historical-performance/mm/"),
    ("bu-academics-cfa-school-of-music-musicology-mm", "CFA", "MM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/musicology/mm/"),
    ("bu-academics-cfa-school-of-music-music-education-mm", "CFA", "MM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/music-education/mm/"),
    ("bu-academics-cfa-school-of-music-performance-mm", "CFA", "MM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/performance/mm/"),
    ("bu-academics-cfa-school-of-music-musicology-phd", "CFA", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/cfa/programs/school-of-music/musicology/phd/"),
    ("bu-cgs-liberal-arts-bs", "CGS", "Liberal Arts", "bachelors", "College of General Studies", "on_campus", 24, "https://www.bu.edu/academics/cgs/programs/september-program/"),
    ("bu-cgs-january-liberal-arts-bs", "CGS", "Liberal Arts (January Program)", "bachelors", "College of General Studies", "on_campus", 24, "https://www.bu.edu/academics/cgs/programs/september-program/"),
    ("bu-academics-com-advertising-advertising-bs", "COM", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/com/programs/advertising/advertising-bs/"),
    ("bu-academics-com-film-television-film-televisionbs", "COM", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/com/programs/film-television/film-televisionbs/"),
    ("bu-academics-com-journalism-bs", "COM", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/com/programs/journalism/bs/"),
    ("bu-academics-com-media-science-bs-in-media-science", "COM", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/com/programs/media-science/bs-in-media-science/"),
    ("bu-academics-com-public-relations-bs-in-public-relations", "COM", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/com/programs/public-relations/bs-in-public-relations/"),
    ("bu-academics-com-emerging-media-studies-ma", "COM", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/com/programs/emerging-media-studies/ma"),
    ("bu-academics-com-advertising-advertising-ms", "COM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/com/programs/advertising/advertising-ms/"),
    ("bu-academics-com-journalism-ms", "COM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/com/programs/journalism/ms/"),
    ("bu-academics-com-media-science-ms-in-media-science", "COM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/com/programs/media-science/ms-in-media-science/"),
    ("bu-academics-com-ms", "COM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/com/programs/ms/"),
    ("bu-academics-com-public-relations-ms-in-public-relations", "COM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/com/programs/public-relations/ms-in-public-relations/"),
    ("bu-academics-com-television", "COM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/com/programs/television/"),
    ("bu-academics-com-emerging-media-studies-phd", "COM", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/com/programs/emerging-media-studies/phd"),
    ("bu-academics-eng-biomedical-engineering-bs", "ENG", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/eng/programs/biomedical-engineering/bs/"),
    ("bu-academics-eng-computer-engineering-bs", "ENG", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/eng/programs/computer-engineering/bs/"),
    ("bu-academics-eng-electrical-engineering-bs", "ENG", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/eng/programs/electrical-engineering/bs/"),
    ("bu-academics-eng-mechanical-engineering-bs", "ENG", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/eng/programs/mechanical-engineering/bs/"),
    ("bu-academics-eng-product-design-manufacture-msmba", "ENG", "MBA/MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/product-design-manufacture/msmba/"),
    ("bu-academics-eng-biomedical-engineering-meng", "ENG", "MEng", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/biomedical-engineering/meng/"),
    ("bu-academics-eng-materials-science-engineering-meng", "ENG", "MEng", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/materials-science-engineering/meng/"),
    ("bu-academics-eng-systems-engineering-meng", "ENG", "MEng", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/systems-engineering/meng/"),
    ("bu-academics-eng-biomedical-engineering-ms", "ENG", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/biomedical-engineering/ms/"),
    ("bu-academics-eng-computer-engineering-ms", "ENG", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/computer-engineering/ms/"),
    ("bu-academics-eng-electrical-engineering-ms", "ENG", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/electrical-engineering/ms/"),
    ("bu-academics-eng-materials-science-engineering-ms", "ENG", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/materials-science-engineering/ms/"),
    ("bu-academics-eng-mechanical-engineering-ms", "ENG", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/mechanical-engineering/ms/"),
    ("bu-academics-eng-product-design-manufacture-product-design-manufacture", "ENG", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/product-design-manufacture/product-design-manufacture/"),
    ("bu-academics-eng-systems-engineering-ms", "ENG", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/systems-engineering/ms/"),
    ("bu-academics-eng-biomedical-engineering-phd", "ENG", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/eng/programs/biomedical-engineering/phd/"),
    ("bu-academics-eng-computer-engineering-phd", "ENG", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/eng/programs/computer-engineering/phd/"),
    ("bu-academics-eng-electrical-engineering-phd", "ENG", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/eng/programs/electrical-engineering/phd/"),
    ("bu-academics-eng-materials-science-engineering-phd", "ENG", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/eng/programs/materials-science-engineering/phd/"),
    ("bu-academics-eng-mechanical-engineering-phd", "ENG", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/eng/programs/mechanical-engineering/phd/"),
    ("bu-academics-eng-systems-engineering-phd", "ENG", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/eng/programs/systems-engineering/phd/"),
    ("bu-academics-gms-dermatology", "GMS", "DSC", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/dermatology/"),
    ("bu-academics-gms-mental-health-counseling-behavioral-medicine-program-ma", "GMS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/mental-health-counseling-behavioral-medicine-program/ma/"),
    ("bu-academics-gms-anatomy-neurobiology-mdphd", "GMS", "MD/PhD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/gms/programs/anatomy-neurobiology/mdphd/"),
    ("bu-academics-gms-biochemistry-mdphd", "GMS", "MD/PhD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/gms/programs/biochemistry/mdphd/"),
    ("bu-academics-gms-mdphd-in-bioinformatics", "GMS", "MD/PhD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/gms/programs/mdphd-in-bioinformatics/"),
    ("bu-academics-gms-chemistry", "GMS", "MD/PhD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/gms/programs/chemistry/"),
    ("bu-academics-gms-genetics-genomics", "GMS", "MD/PhD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/gms/programs/genetics-genomics/"),
    ("bu-academics-gms-molecular-medicine", "GMS", "MD/PhD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/gms/programs/molecular-medicine/"),
    ("bu-academics-gms-pathology-laboratory-medicine-phd", "GMS", "MD/PhD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/gms/programs/pathology-laboratory-medicine/phd/"),
    ("bu-academics-gms-anatomy-neurobiology-ms", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/anatomy-neurobiology/ms/"),
    ("bu-academics-gms-bioimaging", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/bioimaging/"),
    ("bu-academics-gms-biomedical-forensic-sciences", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/biomedical-forensic-sciences/"),
    ("bu-academics-gms-ms-in-biomedical-research-technologies", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/ms-in-biomedical-research-technologies/"),
    ("bu-academics-gms-clinical-investigation-ms", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/clinical-investigation/ms/"),
    ("bu-academics-gms-forensic-anthropology", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/forensic-anthropology/"),
    ("bu-academics-gms-genetic-counseling", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/genetic-counseling/"),
    ("bu-academics-gms-healthcare-emergency-management", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/healthcare-emergency-management/"),
    ("bu-academics-gms-medical-anthropology-and-cross-cultural-practice", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/medical-anthropology-and-cross-cultural-practice/"),
    ("bu-academics-gms-medical-sciences-ms", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/medical-sciences/ms/"),
    ("bu-academics-gms-medical-sciences-dual-degree-masters-program-in-medical-sciences-and-mental-health-counseling-behaviora", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/medical-sciences/dual-degree-masters-program-in-medical-sciences-and-mental-health-counseling-behavioral-medicine/"),
    ("bu-academics-gms-nutrition-metabolism-ms", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/nutrition-metabolism/ms/"),
    ("bu-academics-gms-oral-health-sciences-ms", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/oral-health-sciences-ms/"),
    ("bu-academics-gms-pathology-laboratory-medicine-ma", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/pathology-laboratory-medicine/ma/"),
    ("bu-academics-gms-physician-assistant", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/physician-assistant/"),
    ("bu-academics-gms-anatomy-neurobiology-phd", "GMS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/anatomy-neurobiology/phd/"),
    ("bu-academics-gms-behavioral-neuroscience", "GMS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/behavioral-neuroscience/"),
    ("bu-academics-gms-biochemistry-phd", "GMS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/biochemistry/phd/"),
    ("bu-academics-gms-pibs", "GMS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/pibs/"),
    ("bu-academics-gms-neuroscience", "GMS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/neuroscience/"),
    ("bu-academics-gms-nutrition-metabolism-phd", "GMS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/nutrition-metabolism/phd/"),
    ("bu-academics-gms-oral-biology", "GMS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/oral-biology/"),
    ("bu-academics-gms-pharmacology-experimental-therapeutics", "GMS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/pharmacology-experimental-therapeutics/"),
    ("bu-academics-gms-physiology-biophysics", "GMS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/physiology-biophysics/"),
    ("bu-academics-gms-virology-immunology-microbiology-program", "GMS", "PhD, MD/PhD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/gms/programs/virology-immunology-microbiology-program/"),
    ("bu-academics-grs-african-american-studies", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/african-american-studies/"),
    ("bu-academics-grs-anthropology-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/anthropology/ma/"),
    ("bu-academics-grs-archaeology-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/archaeology/ma/"),
    ("bu-academics-grs-history-art-architecture-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/history-art-architecture/ma/"),
    ("bu-academics-grs-astronomy-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/astronomy/ma/"),
    ("bu-academics-grs-chemistry-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/chemistry/ma/"),
    ("bu-academics-grs-classical-studies-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/classical-studies/ma/"),
    ("bu-academics-grs-classical-studies-ma-in-classics-archaeology", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/classical-studies/ma-in-classics-archaeology/"),
    ("bu-academics-grs-cognitive-neural-systems-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/cognitive-neural-systems/ma/"),
    ("bu-academics-grs-economics-ma-global-development-economics", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/economics/ma-global-development-economics/"),
    ("bu-academics-grs-editorial-studies-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/editorial-studies/ma/"),
    ("bu-academics-grs-english-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/english/ma/"),
    ("bu-academics-grs-romance-studies-ma-french", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/romance-studies/ma-french/"),
    ("bu-academics-grs-earth-environment-geoarchaeology-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/earth-environment/geoarchaeology-ma/"),
    ("bu-academics-grs-romance-studies-ma-hispanic", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/romance-studies/ma-hispanic/"),
    ("bu-academics-grs-history-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/history/ma/"),
    ("bu-academics-grs-international-relations-international-affairs-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/international-relations/international-affairs-ma/"),
    ("bu-academics-grs-international-relations", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/international-relations/"),
    ("bu-academics-grs-latin-american-studies-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/latin-american-studies-ma/"),
    ("bu-academics-grs-linguistics-ma-in-linguistics", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/linguistics/ma-in-linguistics/"),
    ("bu-academics-grs-mathematics-statistics-ma-mathematics", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/mathematics-statistics/ma-mathematics/"),
    ("bu-academics-grs-molecular-biology-cell-biology-biochemistry-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/molecular-biology-cell-biology-biochemistry/ma/"),
    ("bu-academics-grs-neuroscience-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/neuroscience/ma/"),
    ("bu-academics-grs-philosophy-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/philosophy/ma/"),
    ("bu-academics-grs-physics-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/physics/ma/"),
    ("bu-academics-grs-political-science-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/political-science/ma/"),
    ("bu-academics-grs-preservation-studies", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/preservation-studies/"),
    ("bu-academics-grs-psychology-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/psychology/ma/"),
    ("bu-academics-grs-religious-studies-ma-in-religious-studies", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/religious-studies/ma-in-religious-studies/"),
    ("bu-academics-grs-sociology-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/sociology/ma/"),
    ("bu-academics-grs-mathematics-statistics-ma-statistics", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/mathematics-statistics/ma-statistics/"),
    ("bu-academics-grs-international-relations-international-relations-ma-mba", "GRS", "MA/MBA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/international-relations/international-relations-ma-mba/"),
    ("bu-academics-grs-classical-studies-ma-phd-phil", "GRS", "MA/PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/classical-studies/ma-phd-phil/"),
    ("bu-academics-grs-economics-ma-phd", "GRS", "MA/PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/economics/ma-phd/"),
    ("bu-academics-grs-computer-science-ms-in-artificial-intelligence", "GRS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/computer-science/ms-in-artificial-intelligence/"),
    ("bu-academics-grs-biology-master-of-science-in-biology", "GRS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/biology/master-of-science-in-biology//"),
    ("bu-academics-grs-biostatistics-ms", "GRS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/biostatistics/ms/"),
    ("bu-academics-grs-computer-science-ms", "GRS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/computer-science/ms/"),
    ("bu-academics-grs-economics-ma-economic-policy", "GRS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/economics/ma-economic-policy/"),
    ("bu-academics-grs-economics-ma", "GRS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/economics/ma/"),
    ("bu-academics-grs-earth-environment-ma-energy-environment", "GRS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/earth-environment/ma-energy-environment/"),
    ("bu-academics-grs-earth-environment-ma-remote-sensing", "GRS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/earth-environment/ma-remote-sensing/"),
    ("bu-academics-grs-mathematics-statistics-ms-in-statistical-practice", "GRS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/mathematics-statistics/ms-in-statistical-practice/"),
    ("bu-academics-grs-economics-ma-mba", "GRS", "MS/MBA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/economics/ma-mba/"),
    ("bu-academics-grs-earth-environment-ma-in-energy-environment-mba-dual-degree-program", "GRS", "MS/MBA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/earth-environment/ma-in-energy-environment-mba-dual-degree-program/"),
    ("bu-academics-grs-american-new-england-studies", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/american-new-england-studies/"),
    ("bu-academics-grs-anthropology-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/anthropology/phd/"),
    ("bu-academics-grs-archaeology-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/archaeology/phd/"),
    ("bu-academics-grs-history-art-architecture-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/history-art-architecture/phd/"),
    ("bu-academics-grs-astronomy-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/astronomy/phd/"),
    ("bu-academics-grs-biology-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/biology/phd/"),
    ("bu-academics-grs-biostatistics-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/biostatistics/phd/"),
    ("bu-academics-grs-chemistry-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/chemistry/phd/"),
    ("bu-academics-grs-classical-studies-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/classical-studies/phd/"),
    ("bu-academics-grs-cognitive-neural-systems-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/cognitive-neural-systems/phd/"),
    ("bu-academics-grs-computer-science-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/computer-science/phd"),
    ("bu-academics-grs-editorial-studies-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/editorial-studies/phd/"),
    ("bu-academics-grs-english-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/english/phd/"),
    ("bu-academics-grs-romance-studies-phd-french", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/romance-studies/phd-french/"),
    ("bu-academics-grs-romance-studies-phd-hispanic", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/romance-studies/phd-hispanic/"),
    ("bu-academics-grs-history-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/history/phd/"),
    ("bu-academics-grs-linguistics-phd-in-linguistics", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/linguistics/phd-in-linguistics/"),
    ("bu-academics-grs-mathematics-statistics-phd-mathematics", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/mathematics-statistics/phd-mathematics/"),
    ("bu-academics-grs-molecular-biology-cell-biology-biochemistry-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/molecular-biology-cell-biology-biochemistry/phd/"),
    ("bu-academics-grs-neuroscience-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/neuroscience/phd/"),
    ("bu-academics-grs-philosophy-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/philosophy/phd/"),
    ("bu-academics-grs-physics-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/physics/phd/"),
    ("bu-academics-grs-political-science-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/political-science/phd/"),
    ("bu-academics-grs-psychology-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/psychology/phd/"),
    ("bu-academics-grs-religion", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/religion/"),
    ("bu-academics-grs-sociology-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/sociology/phd/"),
    ("bu-academics-grs-sociology-sociology-social-work", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/sociology/sociology-social-work/"),
    ("bu-academics-grs-mathematics-statistics-phd-statistics", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/mathematics-statistics/phd-statistics/"),
    ("bu-academics-law-jd", "LAW", "JD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jd/"),
    ("bu-academics-law-accelerated-llm-in-banking-financial-law", "LAW", "JD/LLM", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/accelerated-llm-in-banking-financial-law/"),
    ("bu-academics-law-jdllm-in-european-law-at-paris-ii", "LAW", "JD/LLM", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdllm-in-european-law-at-paris-ii/"),
    ("bu-academics-law-jdllm-in-finance", "LAW", "JD/LLM", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdllm-in-finance/"),
    ("bu-academics-law-jd-llm-in-international-commercial-and-investment-arbitration-at-paris2", "LAW", "JD/LLM", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jd-llm-in-international-commercial-and-investment-arbitration-at-paris2/"),
    ("bu-academics-law-jdllm-in-international-and-european-business-law-at-icade", "LAW", "JD/LLM", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdllm-in-international-and-european-business-law-at-icade/"),
    ("bu-academics-law-accelerated-llm-in-taxation", "LAW", "JD/LLM", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/accelerated-llm-in-taxation/"),
    ("bu-academics-law-jdma-english", "LAW", "JD/MA", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdma-english/"),
    ("bu-academics-law-jdma-history", "LAW", "JD/MA", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdma-history/"),
    ("bu-academics-law-jdma-ir", "LAW", "JD/MA", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdma-ir/"),
    ("bu-academics-law-jdma-philosophy", "LAW", "JD/MA", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdma-philosophy/"),
    ("bu-academics-law-jdmba", "LAW", "JD/MBA", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdmba/"),
    ("bu-academics-law-jdmba-health", "LAW", "JD/MBA—Health Sector Management", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdmba-health/"),
    ("bu-academics-law-jdmph", "LAW", "JD/MPH", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdmph/"),
    ("bu-academics-law-american-law", "LAW", "LLM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/law/programs/american-law/"),
    ("bu-academics-law-graduate-program-in-banking-financial-law", "LAW", "LLM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/law/programs/graduate-program-in-banking-financial-law/"),
    ("bu-academics-law-intellectual-property-law", "LAW", "LLM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/law/programs/intellectual-property-law/"),
    ("bu-academics-law-graduate-tax-program", "LAW", "LLM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/law/programs/graduate-tax-program/"),
    ("bu-academics-law-jdma-preservation", "LAW", "MA/JD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdma-preservation/"),
    ("bu-academics-law-two-year-master-of-laws-llm-in-american-law", "LAW", "Two-Year LLM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/law/programs/two-year-master-of-laws-llm-in-american-law/"),
    ("bu-academics-law-two-year-master-of-laws-llm-in-banking-financial-law", "LAW", "Two-Year LLM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/law/programs/two-year-master-of-laws-llm-in-banking-financial-law/"),
    ("bu-academics-law-two-year-master-of-laws-llm-in-intellectual-property-information-law", "LAW", "Two-Year LLM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/law/programs/two-year-master-of-laws-llm-in-intellectual-property-information-law/"),
    ("bu-academics-law-two-year-master-of-laws-llm-in-tax-law", "LAW", "Two-Year MSL-TAX", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/law/programs/two-year-master-of-laws-llm-in-tax-law/"),
    ("bu-academics-met-biology", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/biology/"),
    ("bu-academics-met-computer-science-bs", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/computer-science/bs/"),
    ("bu-academics-met-criminal-justice-bs", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/criminal-justice/bs/"),
    ("bu-academics-met-economics", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/economics/"),
    ("bu-academics-met-interdisciplinary-studies", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/interdisciplinary-studies/"),
    ("bu-academics-met-administrative-sciences-bs", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/administrative-sciences/bs/"),
    ("bu-academics-met-mathematics", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/mathematics/"),
    ("bu-academics-met-psychology", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/psychology/"),
    ("bu-academics-met-sociology-bs", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/sociology/bs/"),
    ("bu-academics-met-urban-affairs-bs", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/urban-affairs/bs/"),
    ("bu-academics-met-gastronomy", "MET", "MA", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/gastronomy/"),
    ("bu-academics-met-actuarial-science-ms", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/actuarial-science/ms/"),
    ("bu-academics-met-advertising", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/advertising/"),
    ("bu-academics-met-computer-science-master-of-science-in-applied-data-analytics", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/computer-science/master-of-science-in-applied-data-analytics/"),
    ("bu-academics-met-arts-administration-ms", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/arts-administration/ms/"),
    ("bu-academics-met-computer-science-mscis", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/computer-science/mscis/"),
    ("bu-academics-met-computer-science-ms", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/computer-science/ms/"),
    ("bu-academics-met-criminal-justice-mcj", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/criminal-justice/mcj/"),
    ("bu-academics-met-health-communication-ms", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/health-communication/ms/"),
    ("bu-academics-met-computer-science-ms-in-health-informatics", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/computer-science/ms-in-health-informatics/"),
    ("bu-academics-met-administrative-sciences-ms-in-human-resources-management", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/administrative-sciences/ms-in-human-resources-management/"),
    ("bu-academics-met-administrative-sciences-ms", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/administrative-sciences/ms/"),
    ("bu-academics-met-administrative-sciences-ms-insurance-management", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/administrative-sciences/ms-insurance-management/"),
    ("bu-academics-met-administrative-sciences-ms-project-management", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/administrative-sciences/ms-project-management/"),
    ("bu-academics-met-computer-science-ms-in-software-development", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/computer-science/ms-in-software-development/"),
    ("bu-academics-met-computer-science-telecommunication", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/computer-science/telecommunication/"),
    ("bu-academics-met-computer-science-bs-accelerated", "MET", "accelerated degree completion program", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/computer-science/bs-accelerated/"),
    ("bu-academics-met-administrative-sciences-bs-accelerated", "MET", "accelerated degree completion program", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/administrative-sciences/bs-accelerated/"),
    ("bu-academics-questrom-undergrad", "QUESTROM", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/questrom/programs/undergrad/"),
    ("bu-academics-questrom-bachelor-of-science-in-business-administration-bsba-to-master-of-science-in-business-analytics-msb", "QUESTROM", "BSBA-to-MSBA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/questrom/programs/bachelor-of-science-in-business-administration-bsba-to-master-of-science-in-business-analytics-msba-program/"),
    ("bu-academics-questrom-mba", "QUESTROM", "MBA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/questrom/programs/mba/"),
    ("bu-academics-questrom-msdt", "QUESTROM", "MBA/MSDT", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/questrom/programs/msdt/"),
    ("bu-academics-questrom-ms-in-business-analytics", "QUESTROM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/questrom/programs/ms-in-business-analytics/"),
    ("bu-academics-questrom-ms-in-finance", "QUESTROM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/questrom/programs/ms-in-finance/"),
    ("bu-academics-questrom-mathematical-finance-ms", "QUESTROM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/questrom/programs/mathematical-finance/ms/"),
    ("bu-academics-questrom-ms-in-management-studies", "QUESTROM", "MiM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/questrom/programs/ms-in-management-studies/"),
    ("bu-academics-questrom-phd-in-management", "QUESTROM", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/questrom/programs/phd-in-management/"),
    ("bu-academics-questrom-phd-in-business-economics", "QUESTROM", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/questrom/programs/phd-in-business-economics/"),
    ("bu-academics-questrom-mathematical-finance-phd", "QUESTROM", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/questrom/programs/mathematical-finance/phd/"),
    ("bu-rotc-air-force-ms", "ROTC", "Aerospace Studies (Air Force ROTC)", "certificate", "Division of Military Education", "on_campus", 48, "https://www.bu.edu/academics/rotc/programs/aerospace-studies/"),
    ("bu-rotc-army-ms", "ROTC", "Military Science (Army ROTC)", "certificate", "Division of Military Education", "on_campus", 48, "https://www.bu.edu/academics/rotc/programs/military-science/"),
    ("bu-rotc-navy-ms", "ROTC", "Naval Science (Navy ROTC)", "certificate", "Division of Military Education", "on_campus", 48, "https://www.bu.edu/academics/rotc/programs/naval-science/"),
    ("bu-academics-sar-bs-in-behavior-and-health", "SAR", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sar/programs/bs-in-behavior-and-health/"),
    ("bu-academics-sar-health-science", "SAR", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sar/programs/health-science/"),
    ("bu-academics-sar-human-physiology-bs", "SAR", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sar/programs/human-physiology/bs/"),
    ("bu-academics-sar-speech-language-hearing-sciences-bs-in-linguistics-speech-language-and-hearing-sciences", "SAR", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sar/programs/speech-language-hearing-sciences/bs-in-linguistics-speech-language-and-hearing-sciences/"),
    ("bu-academics-sar-nutrition-dietetics-bs", "SAR", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sar/programs/nutrition-dietetics/bs/"),
    ("bu-academics-sar-speech-language-hearing-sciences-bs", "SAR", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sar/programs/speech-language-hearing-sciences/bs/"),
    ("bu-academics-sar-human-physiology-bsms", "SAR", "BS-to-MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sar/programs/human-physiology/bsms/"),
    ("bu-academics-sar-speech-language-hearing-sciences-bs-ms", "SAR", "BS-to-MS-SLP", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sar/programs/speech-language-hearing-sciences/bs-ms/"),
    ("bu-academics-sar-physical-therapy-bs-dpt", "SAR", "BS/DPT", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sar/programs/physical-therapy/bs-dpt/"),
    ("bu-academics-sar-physical-therapy-dpt-phd", "SAR", "DPT/PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sar/programs/physical-therapy/dpt-phd/"),
    ("bu-academics-sar-human-physiology-ms", "SAR", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sar/programs/human-physiology/ms/"),
    ("bu-academics-sar-nutrition-dietetics-ms", "SAR", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sar/programs/nutrition-dietetics/ms/"),
    ("bu-academics-sar-speech-language-hearing-sciences-ms", "SAR", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sar/programs/speech-language-hearing-sciences/ms/"),
    ("bu-academics-sar-speech-language-hearing-sciences-ms-phd", "SAR", "MS/PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sar/programs/speech-language-hearing-sciences/ms-phd/"),
    ("bu-academics-sar-occupational-therapy-otd-phd", "SAR", "OTD/PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sar/programs/occupational-therapy/otd-phd/"),
    ("bu-academics-sar-human-physiology-phd", "SAR", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sar/programs/human-physiology/phd/"),
    ("bu-academics-sar-rehabilitation-sciences", "SAR", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sar/programs/rehabilitation-sciences/"),
    ("bu-academics-sar-speech-language-hearing-sciences-phd", "SAR", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sar/programs/speech-language-hearing-sciences/phd/"),
    ("bu-academics-sar-public-health-bs-mph", "SAR", "minor", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sar/programs/public-health/bs-mph/"),
    ("bu-academics-sdm-dental-public-health-cags", "SDM", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/dental-public-health/cags/"),
    ("bu-academics-sdm-endodontics-cags", "SDM", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/endodontics/cags/"),
    ("bu-academics-sdm-operative-dentistry-cags", "SDM", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/operative-dentistry/cags/"),
    ("bu-academics-sdm-oral-and-maxillofacial-surgery-cags", "SDM", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/oral-and-maxillofacial-surgery/cags/"),
    ("bu-academics-sdm-pediatric-dentistry-cags", "SDM", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/pediatric-dentistry/cags/"),
    ("bu-academics-sdm-periodontology-cags", "SDM", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/periodontology/cags/"),
    ("bu-academics-sdm-prosthodontics-cags", "SDM", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/prosthodontics/cags/"),
    ("bu-academics-sdm-doctor-of-dental-medicine", "SDM", "DMD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sdm/programs/doctor-of-dental-medicine/"),
    ("bu-academics-sdm-oral-biology-dsc", "SDM", "DSc", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/oral-biology/dsc/"),
    ("bu-academics-sdm-dscd-dental-biomaterials", "SDM", "DScD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/dscd-dental-biomaterials/"),
    ("bu-academics-sdm-endodontics-dscd", "SDM", "DScD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/endodontics/dscd/"),
    ("bu-academics-sdm-operative-dentistry-dscd", "SDM", "DScD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/operative-dentistry/dscd/"),
    ("bu-academics-sdm-oral-and-maxillofacial-surgery-dscd", "SDM", "DScD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/oral-and-maxillofacial-surgery/dscd/"),
    ("bu-academics-sdm-orthodontics-dentofacial-orthopedics-dscd", "SDM", "DScD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/orthodontics-dentofacial-orthopedics/dscd/"),
    ("bu-academics-sdm-pediatric-dentistry-dscd", "SDM", "DScD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/pediatric-dentistry/dscd/"),
    ("bu-academics-sdm-periodontology-dscd", "SDM", "DScD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/periodontology/dscd/"),
    ("bu-academics-sdm-prosthodontics-cags-dscd", "SDM", "DScD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/prosthodontics/cags-dscd"),
    ("bu-academics-sdm-dental-biomaterials-dscd-cags", "SDM", "DScD/CAGS", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/dental-biomaterials/dscd-cags/"),
    ("bu-academics-sdm-dental-public-health-dscd", "SDM", "DScD/CAGS", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/dental-public-health/dscd/"),
    ("bu-academics-sdm-dental-public-health-ms", "SDM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sdm/programs/dental-public-health/ms/"),
    ("bu-academics-sdm-dental-public-health-msd", "SDM", "MSD", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sdm/programs/dental-public-health/msd/"),
    ("bu-academics-sdm-endodontics-msd", "SDM", "MSD", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sdm/programs/endodontics/msd/"),
    ("bu-academics-sdm-operative-dentistry-msd", "SDM", "MSD", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sdm/programs/operative-dentistry/msd/"),
    ("bu-academics-sdm-oral-biology-msd", "SDM", "MSD", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sdm/programs/oral-biology/msd/"),
    ("bu-academics-sdm-oral-and-maxillofacial-surgery-msd", "SDM", "MSD", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sdm/programs/oral-and-maxillofacial-surgery/msd/"),
    ("bu-academics-sdm-orthodontics-dentofacial-orthopedics-cags-msd", "SDM", "MSD", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/orthodontics-dentofacial-orthopedics/cags-msd/"),
    ("bu-academics-sdm-pediatric-dentistry-msd", "SDM", "MSD", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sdm/programs/pediatric-dentistry/msd/"),
    ("bu-academics-sdm-periodontology-msd", "SDM", "MSD", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sdm/programs/periodontology/msd/"),
    ("bu-academics-sdm-prosthodontics-cags-msd", "SDM", "MSD", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/prosthodontics/cags-msd"),
    ("bu-academics-sdm-dental-biomaterials-msd-cags", "SDM", "MSD/CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/dental-biomaterials/msd-cags/"),
    ("bu-academics-sdm-oral-biology-phd", "SDM", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/oral-biology/phd/"),
    ("bu-academics-sha-bachelor-of-science-in-hospitality-administration", "SHA", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sha/programs/bachelor-of-science-in-hospitality-administration/"),
    ("bu-academics-sha-bs-in-hospitality-communication", "SHA", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sha/programs/bs-in-hospitality-communication/"),
    ("bu-academics-sha-bs-mla", "SHA", "BS/MLA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sha/programs/bs-mla/"),
    ("bu-academics-sha-ms", "SHA", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sha/programs/ms/"),
    ("bu-academics-sph-mba-mph", "SPH", "MBA/MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mba-mph/"),
    ("bu-academics-sph-medicine-and-public-health", "SPH", "MD/MPH", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sph/programs/medicine-and-public-health/"),
    ("bu-academics-sph-mph-chronic-and-non-communicable-diseases", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/chronic-and-non-communicable-diseases/"),
    ("bu-academics-sph-mph-community-assessment", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/community-assessment/"),
    ("bu-academics-sph-mph-environmental-health", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/environmental-health/"),
    ("bu-academics-sph-mph-epidemiology-and-biostatistics", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/epidemiology-and-biostatistics/"),
    ("bu-academics-sph-mph-global-health-2", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/global-health-2/"),
    ("bu-academics-sph-mph-monitoring-and-evaluation", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/monitoring-and-evaluation/"),
    ("bu-academics-sph-mph-healthcare-management", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/healthcare-management/"),
    ("bu-academics-sph-programs-health-communication-and-promotion", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/programs/health-communication-and-promotion/"),
    ("bu-academics-sph-mph-in-health-equity", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph-in-health-equity/"),
    ("bu-academics-sph-mph-health-policy-and-law", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/health-policy-and-law/"),
    ("bu-academics-sph-mph-human-rights-and-social-justice", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/human-rights-and-social-justice/"),
    ("bu-academics-sph-mph-infectious-disease", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/infectious-disease/"),
    ("bu-academics-sph-mph-maternal-and-child-health", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/maternal-and-child-health/"),
    ("bu-academics-sph-mph-mental-health-and-substance-use", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/mental-health-and-substance-use/"),
    ("bu-academics-sph-mph-pharmaceutical-development-delivery-and-access", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/pharmaceutical-development-delivery-and-access/"),
    ("bu-academics-sph-mph", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/"),
    ("bu-academics-sph-mph-sex-sexuality-and-gender", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/sex-sexuality-and-gender/"),
    ("bu-academics-sph-ms-in-genetic-counseling-master-of-public-health-ms-mph", "SPH", "MS/MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/ms-in-genetic-counseling-master-of-public-health-ms-mph/"),
    ("bu-academics-sph-medical-sciences-and-public-health", "SPH", "MS/MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/medical-sciences-and-public-health/"),
    ("bu-academics-sph-social-work-and-public-health", "SPH", "MSW/MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/social-work-and-public-health/"),
    ("bu-academics-sph-environmental-health-phd", "SPH", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sph/programs/environmental-health/phd/"),
    ("bu-academics-sph-epidemiology-phd", "SPH", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sph/programs/epidemiology/phd/"),
    ("bu-academics-sph-health-services-research-phd", "SPH", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sph/programs/health-services-research/phd/"),
    ("bu-academics-ssw-clinical-social-work-practice", "SSW", "MSW", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/ssw/programs/clinical-social-work-practice/"),
    ("bu-academics-ssw-macro-social-work-practice", "SSW", "MSW", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/ssw/programs/macro-social-work-practice/"),
    ("bu-academics-ssw-msw", "SSW", "MSW Online", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/ssw/programs/msw/"),
    ("bu-academics-ssw-dual-degree-programs-in-social-work-and-education", "SSW", "MSW/EdD", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/ssw/programs/dual-degree-programs-in-social-work-and-education/"),
    ("bu-academics-ssw-dual-degree-in-theology-and-social-work", "SSW", "MSW/MTS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/ssw/programs/dual-degree-in-theology-and-social-work/"),
    ("bu-academics-ssw-phd-in-social-work", "SSW", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/ssw/programs/phd-in-social-work/"),
    ("bu-academics-sth-marpl", "STH", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sth/programs/marpl/"),
    ("bu-academics-sth-theological-studies-phd", "STH", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sth/programs/theological-studies-phd/"),
    ("bu-academics-wheelock-bilingual-education-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/bilingual-education/bs/"),
    ("bu-academics-wheelock-deaf-studies-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/deaf-studies/bs/"),
    ("bu-academics-wheelock-early-childhood-education-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/early-childhood-education/bs/"),
    ("bu-academics-wheelock-bs-in-education-human-development", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/bs-in-education-human-development/"),
    ("bu-academics-wheelock-elementary-education-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/elementary-education/bs/"),
    ("bu-academics-wheelock-english-education-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/english-education/bs/"),
    ("bu-academics-wheelock-mathematics-education-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/mathematics-education/bs/"),
    ("bu-academics-wheelock-modern-foreign-language-education-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/modern-foreign-language-education/bs/"),
    ("bu-academics-wheelock-science-education-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/science-education/bs/"),
    ("bu-academics-wheelock-social-studies-education-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/social-studies-education/bs/"),
    ("bu-academics-wheelock-special-education-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/special-education/bs/"),
    ("bu-academics-wheelock-applied-human-development-bs-edm-applied-human-development", "WHEEL", "BS-to-EdM", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/applied-human-development/bs-edm-applied-human-development/"),
    ("bu-academics-wheelock-bilingual-education-bs-edm-tesol-applied-linguistics", "WHEEL", "BS-to-EdM", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/bilingual-education/bs-edm-tesol-applied-linguistics/"),
    ("bu-academics-wheelock-bilingual-education-bs-ms-tesol-multilingual-learner-education", "WHEEL", "BS-to-EdM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/wheelock/programs/bilingual-education/bs-ms-tesol-multilingual-learner-education/"),
    ("bu-academics-wheelock-policy-planning-administration-bs-ma-educational-policy-studies", "WHEEL", "BS-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/wheelock/programs/policy-planning-administration/bs-ma-educational-policy-studies/"),
    ("bu-academics-wheelock-bilingual-education", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/bilingual-education/"),
    ("bu-academics-wheelock-curriculum-teaching-cags", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/curriculum-teaching/cags/"),
    ("bu-academics-wheelock-deaf-studies-cags", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/deaf-studies/cags/"),
    ("bu-academics-wheelock-developmental-studies-cags-lit-language", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/developmental-studies/cags-lit-language/"),
    ("bu-academics-wheelock-early-childhood-education-cags", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/early-childhood-education/cags/"),
    ("bu-academics-wheelock-policy-planning-administration-cags", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/policy-planning-administration/cags/"),
    ("bu-academics-wheelock-english-education-cags", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/english-education/cags/"),
    ("bu-academics-wheelock-literacy-education-cags", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/literacy-education/cags/"),
    ("bu-academics-wheelock-science-education-cags", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/science-education/cags/"),
    ("bu-academics-wheelock-social-studies-education-cags", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/social-studies-education/cags/"),
    ("bu-academics-wheelock-special-education-cags", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/special-education/cags/"),
    ("bu-academics-wheelock-policy-planning-administration-ma-in-educational-policy-studies", "WHEEL", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/wheelock/programs/policy-planning-administration/ma-in-educational-policy-studies/"),
    ("bu-academics-wheelock-early-childhood-education-ma-in-leadership-policy-advocacy-for-early-childhood-well-being", "WHEEL", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/wheelock/programs/early-childhood-education/ma-in-leadership-policy-advocacy-for-early-childhood-well-being/"),
    ("bu-academics-wheelock-ms-in-child-life-family-centered-care", "WHEEL", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/wheelock/programs/ms-in-child-life-family-centered-care/"),
    ("bu-academics-wheelock-applied-human-development-phd-counseling-psychology-applied-human-development", "WHEEL", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/wheelock/programs/applied-human-development/phd-counseling-psychology-applied-human-development/"),
    ("bu-academics-wheelock-deaf-studies", "WHEEL", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/wheelock/programs/deaf-studies/")
]

_DEGREE_TOKENS = frozenset({
    "ba", "bs", "bfa", "bm", "bachelors", "ms", "ma", "mph", "msw", "meng", "mba", "mm",
    "msd", "cags", "phd", "dsc", "dscd", "dmd", "jd", "md", "minor", "online",
})
_LEGACY_COUNTS = Counter(name for _s, _sk, name, *_ in _CATALOG)
_PROGRAM_NAME_OVERRIDES: dict[str, str] = {
    "bu-academics-busm-four-year-program": "Doctor of Medicine",
    "bu-academics-law-jd": "Juris Doctor",
    "bu-academics-questrom-mba": "Master of Business Administration",
    "bu-academics-sdm-doctor-of-dental-medicine": "Doctor of Dental Medicine",
    "bu-academics-com-ms": "Master's in Communication",
    "bu-academics-sha-ms": "Master's in Hospitality Administration",
    "bu-academics-sph-mph": "Master of Public Health",
    "bu-academics-sph-programs-health-communication-and-promotion": (
        "Master of Public Health in Health Communication and Promotion"
    ),
}


def _clean_segment(seg: str) -> str:
    s = seg.replace("-", " ").title()
    for prefix in (
        "Ba In ", "Ba ", "Bs In ", "Bs ", "Ms In ", "Ms ", "Ma In ", "Ma ",
        "Phd In ", "Phd ", "Msd ", "Cags ", "Programs ",
    ):
        if s.startswith(prefix):
            s = s[len(prefix):]
    return s.strip()


def _field_from_url(url: str, *, strip_degree: bool = True) -> str:
    m = re.search(r"/programs/(.+)", url.rstrip("/"))
    if not m:
        return ""
    parts = [p for p in m.group(1).split("/") if p and p != "programs"]
    if strip_degree:
        while parts and parts[-1].lower() in _DEGREE_TOKENS:
            parts.pop()
    if not parts:
        return ""
    return " — ".join(_clean_segment(p) for p in parts)


def _department_for(field: str, school: str) -> str:
    if not field:
        return school
    base = field.split(" — ")[0]
    if base.lower() in school.lower() or school.lower() in base.lower():
        return school
    return base


def _use_url_name(legacy: str) -> bool:
    return legacy in BARE_DEGREE_ABBREVIATIONS or _LEGACY_COUNTS[legacy] > 1


def _base_program_name(slug: str, legacy: str, dtype: str, url: str) -> str:
    if slug in _PROGRAM_NAME_OVERRIDES:
        return _PROGRAM_NAME_OVERRIDES[slug]
    if not _use_url_name(legacy):
        return legacy.replace("&amp;", "&")
    field = _field_from_url(url)
    if legacy == "MEng":
        return f"Master of Engineering in {field.split(' — ')[0]}"
    return disambiguate_program_name(field, dtype)


def _build_catalog() -> list[dict]:
    out: list[dict] = []
    for slug, sk, legacy, dtype, dept, fmt, dur, url in _CATALOG:
        school = SCHOOL_NAME[sk]
        pname = _base_program_name(slug, legacy, dtype, url)
        field = _field_from_url(url) if _use_url_name(legacy) else legacy
        department = dept if dept and dept != "Programs" else _department_for(field, school)
        out.append({
            "slug": slug,
            "school": school,
            "school_key": sk,
            "program_name": pname,
            "degree_type": dtype,
            "department": department,
            "delivery_format": fmt,
            "duration_months": dur,
            "catalog_url": url,
            "legacy_credential": legacy,
        })

    counts = Counter(p["program_name"] for p in out)
    for p in out:
        if counts[p["program_name"]] > 1:
            field = _field_from_url(p["catalog_url"], strip_degree=False)
            if field and p["legacy_credential"] != "MEng":
                p["program_name"] = disambiguate_program_name(field, p["degree_type"])

    counts = Counter(p["program_name"] for p in out)
    for p in out:
        if counts[p["program_name"]] > 1:
            suffix = " (Online)" if p["delivery_format"] == "online" else f" ({p['school']})"
            p["program_name"] += suffix

    counts = Counter(p["program_name"] for p in out)
    for p in out:
        legacy = p["legacy_credential"]
        if counts[p["program_name"]] > 1 and legacy not in BARE_DEGREE_ABBREVIATIONS:
            p["program_name"] += f" — {legacy}"

    for p in out:
        p["description"] = program_description(
            p["program_name"],
            p["degree_type"],
            p["school"],
            p["department"],
            delivery_format=p["delivery_format"],
            university_short="Boston University",
        )
        p.pop("legacy_credential", None)
    return out


PROGRAMS: list[dict] = _build_catalog()
_catalog_errors = validate_catalog(PROGRAMS)
if _catalog_errors:
    raise RuntimeError(f"Boston University catalog quality gate failed: {_catalog_errors}")
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

_WEBSITE_OVERRIDE: dict[str, str] = {}
for _spec in PROGRAMS:
    _WEBSITE_OVERRIDE[_spec["slug"]] = _spec["catalog_url"]

_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "bu-academics-cas-computer-science-ba": ["computer science", "BU CS", "Department of Computer Science"],
    "bu-academics-cds-bs-in-data-science": ["data science", "CDS", "Computing & Data Sciences"],
    "bu-academics-questrom-mba": ["Questrom MBA", "Questrom", "business school"],
    "bu-academics-law-jd": ["BU Law", "J.D.", "School of Law"],
    "bu-academics-busm-four-year-program": ["BU School of Medicine", "M.D.", "Chobanian & Avedisian"],
    "bu-academics-sdm-doctor-of-dental-medicine": ["Goldman School of Dental Medicine", "DMD", "dental"],
    "bu-academics-sph-mph": ["School of Public Health", "MPH", "public health"],
    "bu-academics-ssw-clinical-social-work-practice": ["School of Social Work", "MSW", "social work"],
    "bu-academics-eng-electrical-engineering-bs": ["electrical engineering", "ECE", "College of Engineering"],
    "bu-academics-com-journalism-bs": ["College of Communication", "journalism", "COM"],
    "bu-academics-sha-bachelor-of-science-in-hospitality-administration": ["School of Hospitality Administration", "SHA", "hospitality"],
    "bu-academics-cas-international-relations-ba": ["international relations", "Pardee", "global studies"],
    "bu-academics-com-film-television-film-televisionbs": ["film & television", "COM", "film production"],
    "bu-academics-eng-biomedical-engineering-bs": ["biomedical engineering", "BME", "College of Engineering"],
}

_UNDERGRAD_COA = 86285
_AVG_NET_PRICE = 24402
_COST_SRC = "U.S. Dept. of Education — College Scorecard (Boston University, UNITID 164988)"
_COST_SRC_URL = "https://collegescorecard.ed.gov/school/?164988-Boston-University"


def _undergrad_cost() -> dict:
    return {
        "total_cost_of_attendance": _UNDERGRAD_COA,
        "avg_net_price": _AVG_NET_PRICE,
        "funded": False,
        "note": (
            "BU's published academic-year cost of attendance is about $86,285 and the average net "
            "price after grant aid is about $24,402 (College Scorecard, UNITID 164988). Tuition "
            "varies by school and program. See BU Student Financial Assistance for current figures."
        ),
        "source": _COST_SRC, "source_url": _COST_SRC_URL, "year": "2023-24",
    }


def _grad_cost_fallback(spec: dict) -> dict:
    return {
        "note": (
            "Tuition for this graduate/professional program is set by BU and is typically billed "
            "per term (and varies by school, program, and online vs. on-campus delivery), so a "
            "single verified annual figure is not published here. See the program's tuition page "
            "for current figures."
        ),
        "source": "Boston University Office of the Registrar / program tuition page",
        "source_url": _website_for(spec),
    }


_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission to an on-campus program.",
}
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Application (Common Application or BU application)", "required": True},
        {"name": "Required essays", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "$80 application fee (fee waivers available)", "required": True},
        {"name": "SAT/ACT scores", "required": False,
         "note": "BU is test-optional; the middle 50% of enrolled students who submitted scored SAT 1420-1530 / ACT 32-34 (College Scorecard / CDS 2024-25)."},
    ],
    "deadlines": [
        {"round": "Early Decision I", "date": "November 1"},
        {"round": "Early Decision II", "date": "January 4"},
        {"round": "Regular Decision", "date": "January 4"},
    ],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS", "Duolingo English Test"], "required": True,
                    "note": "Required for applicants whose native language is not English."},
        "visa": _INTL_VISA,
        "sources": [{"label": "BU Undergraduate Admissions", "url": "https://www.bu.edu/admissions/"}],
    },
    "source": "Boston University Undergraduate Admissions",
    "source_url": "https://www.bu.edu/admissions/",
}
_REQ_GRAD_GENERIC = {
    "materials": [
        {"name": "BU Graduate application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Résumé / CV", "required": True},
        {"name": "Letters of recommendation", "required": True,
         "note": "Most BU graduate programs require two or three letters; check the program's page."},
        {"name": "GRE/GMAT scores", "required": False,
         "note": "Test requirements vary by program; many BU graduate programs are test-optional."},
    ],
    "deadlines": [{"round": "Fall admission", "date": "Deadlines vary by program (typically December–January)"}],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS"], "required": True,
                    "note": "Required for applicants whose native language is not English."},
        "visa": _INTL_VISA,
        "sources": [{"label": "BU Graduate Admissions", "url": "https://www.bu.edu/grad/admissions/"}],
    },
    "source": "Boston University Graduate Admissions",
    "source_url": "https://www.bu.edu/grad/admissions/",
}


def _requirements_for(spec: dict) -> dict:
    if spec["degree_type"] == "bachelors":
        return _REQ_UNDERGRAD
    return _REQ_GRAD_GENERIC


_OUTCOMES_BY_SLUG: dict[str, dict] = {}
_OUTCOMES_OMIT_BY_SLUG: dict[str, list[str]] = {}
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {}
_FACULTY_BY_SLUG: dict[str, dict] = {}

_REVIEWS_BY_SLUG: dict[str, dict] = {
    "bu-academics-cas-computer-science-ba": {
        "summary": "BU computer science (Department of Computer Science, CAS and CDS) is a well-regarded program in a major research university, with strength in AI, data systems, security, and robotics and access to the Hariri Institute and NEIDL-adjacent computing research. Reviewers highlight strong faculty, Boston's tech and startup ecosystem, and flexible combined majors (including CS + economics and CS + biology), while noting that core courses can be large and admission to the major is competitive.",
        "themes": [
            {
                "label": "Strong CS in a research university",
                "sentiment": "positive",
                "detail": "BU CS sits in a Carnegie R1 university with the Faculty of Computing & Data Sciences and major Boston industry access."
            },
            {
                "label": "AI, systems, and robotics",
                "sentiment": "positive",
                "detail": "Faculty and labs span AI, data science, security, graphics/Vision, and robotics."
            },
            {
                "label": "Boston tech ecosystem",
                "sentiment": "positive",
                "detail": "Graduates recruit into Boston-area tech, finance, and startups plus national firms."
            },
            {
                "label": "Large intro courses",
                "sentiment": "caution",
                "detail": "Popular CS courses can be large; reviewers advise engaging with office hours and research early."
            }
        ],
        "sources": [
            {
                "label": "BU Department of Computer Science",
                "url": "https://www.bu.edu/cs/"
            },
            {
                "label": "Faculty of Computing & Data Sciences",
                "url": "https://www.bu.edu/cds/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-cds-bs-in-data-science": {
        "summary": "BU's data science offerings through the Faculty of Computing & Data Sciences combine computing, statistics, and domain applications in a dedicated interdisciplinary unit housed in the Center for Computing & Data Sciences. Reviewers praise the modern curriculum, cross-college integration, and Boston industry ties, while noting the program is relatively new compared with long-established peer departments.",
        "themes": [
            {
                "label": "Interdisciplinary CDS unit",
                "sentiment": "positive",
                "detail": "CDS integrates computing and data science across BU's colleges in a purpose-built academic unit."
            },
            {
                "label": "Modern curriculum",
                "sentiment": "positive",
                "detail": "Coursework spans statistics, machine learning, and responsible/data-driven computing."
            },
            {
                "label": "Industry-relevant skills",
                "sentiment": "positive",
                "detail": "Graduates target data science, analytics, and tech roles in Boston and nationally."
            },
            {
                "label": "Younger program",
                "sentiment": "mixed",
                "detail": "CDS is newer than peer CS/DS departments; track record is still building compared with decades-old programs."
            }
        ],
        "sources": [
            {
                "label": "BU Faculty of Computing & Data Sciences",
                "url": "https://www.bu.edu/cds/"
            },
            {
                "label": "U.S. News \u2014 BU rankings",
                "url": "https://www.usnews.com/best-colleges/boston-university-2130"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-questrom-mba": {
        "summary": "The Questrom MBA is a nationally ranked business program (U.S. News top-50 full-time MBA) known for digital technologies, health/life sciences, and energy/sustainability themes woven through the curriculum. Reviewers cite strong value in Boston's health and tech economy, team-based learning, and improving career outcomes, while noting the brand is somewhat below the very top tier of M7 schools.",
        "themes": [
            {
                "label": "Top-50 MBA with thematic focus",
                "sentiment": "positive",
                "detail": "Questrom emphasizes digital business, health sector, and sustainability across MBA concentrations."
            },
            {
                "label": "Boston health & tech market",
                "sentiment": "positive",
                "detail": "Location supports internships and placement in biotech, consulting, finance, and tech."
            },
            {
                "label": "Team-based learning",
                "sentiment": "positive",
                "detail": "Reviewers describe a collaborative, case- and project-driven culture."
            },
            {
                "label": "Brand tier",
                "sentiment": "mixed",
                "detail": "Questrom is well regarded but sits below the M7; outcomes depend on networking and specialization."
            }
        ],
        "sources": [
            {
                "label": "Questrom School of Business \u2014 MBA",
                "url": "https://www.bu.edu/questrom/"
            },
            {
                "label": "U.S. News \u2014 Questrom MBA rankings",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/boston-university-01097"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-law-jd": {
        "summary": "Boston University School of Law is a well-established national law school (U.S. News top-35) with strengths in health law, intellectual property, international law, and banking/financial law. Reviewers highlight strong bar passage and employment outcomes relative to peers, a collegial culture, and Boston's legal market access, while noting the cost of a private urban legal education.",
        "themes": [
            {
                "label": "National law school reputation",
                "sentiment": "positive",
                "detail": "BU Law ranks among the top U.S. law schools with recognized specialty programs."
            },
            {
                "label": "Health and IP strengths",
                "sentiment": "positive",
                "detail": "Health law, IP, and financial-services law are signature strengths aligned with Boston's economy."
            },
            {
                "label": "Strong outcomes",
                "sentiment": "positive",
                "detail": "ABA disclosures show solid bar passage and employment in law and business roles."
            },
            {
                "label": "Cost",
                "sentiment": "caution",
                "detail": "Private law school tuition in Boston is expensive; reviewers weigh scholarships carefully."
            }
        ],
        "sources": [
            {
                "label": "BU School of Law \u2014 ABA Required Disclosures",
                "url": "https://www.bu.edu/law/about/aba-disclosures/"
            },
            {
                "label": "U.S. News \u2014 BU School of Law",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/boston-university-01058"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-busm-four-year-program": {
        "summary": "The Chobanian & Avedisian School of Medicine grants the M.D. on BU's Medical Campus with integrated clinical training across Boston hospitals and research strengths in infectious disease, neuroscience, and cardiovascular medicine. Reviewers praise early clinical exposure, research opportunities at NEIDL and affiliated hospitals, and Boston's medical ecosystem, while noting the intensity and cost of medical education.",
        "themes": [
            {
                "label": "Integrated Boston clinical network",
                "sentiment": "positive",
                "detail": "Students train across BU-affiliated hospitals and the Medical Campus."
            },
            {
                "label": "Research-intensive",
                "sentiment": "positive",
                "detail": "NEIDL, biomedical engineering ties, and NIH-funded research are major assets."
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Medical school admission is highly competitive with demanding coursework."
            }
        ],
        "sources": [
            {
                "label": "Chobanian & Avedisian School of Medicine",
                "url": "https://www.bumc.bu.edu/busm/"
            },
            {
                "label": "U.S. News \u2014 Best Medical Schools (Research)",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/boston-university-04086"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-sdm-doctor-of-dental-medicine": {
        "summary": "The Henry M. Goldman School of Dental Medicine offers a D.M.D. with clinical training in Boston and recognized specialty and advanced graduate programs. Reviewers cite hands-on clinical volume, diverse patient populations, and strong specialty options, while noting the demanding schedule and cost of dental education.",
        "themes": [
            {
                "label": "Clinical volume",
                "sentiment": "positive",
                "detail": "Students gain substantial patient care experience in Boston clinics."
            },
            {
                "label": "Specialty pathways",
                "sentiment": "positive",
                "detail": "Advanced certificates and graduate degrees are available across dental specialties."
            },
            {
                "label": "Demanding program",
                "sentiment": "caution",
                "detail": "Dental school is intensive with high clinical and academic workload."
            }
        ],
        "sources": [
            {
                "label": "Henry M. Goldman School of Dental Medicine",
                "url": "https://www.bu.edu/dental/"
            },
            {
                "label": "U.S. News \u2014 dental school rankings",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/dental"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-sph-mph": {
        "summary": "BU's School of Public Health is a top-ranked program (U.S. News #8) with strengths in epidemiology, health law and policy, and global health under Dean Sandro Galea. Reviewers highlight interdisciplinary faculty, Boston health-sector access, and flexible MPH concentrations, while noting workload intensity in quant-heavy tracks.",
        "themes": [
            {
                "label": "Top-10 public health school",
                "sentiment": "positive",
                "detail": "BU SPH ranks among the nation's best schools of public health."
            },
            {
                "label": "Epidemiology and policy",
                "sentiment": "positive",
                "detail": "Faculty leadership in epidemiology, health law, and global health is widely cited."
            },
            {
                "label": "Quant-heavy coursework",
                "sentiment": "caution",
                "detail": "Biostatistics and epidemiology tracks require strong quantitative preparation."
            }
        ],
        "sources": [
            {
                "label": "BU School of Public Health",
                "url": "https://www.bumc.bu.edu/sph/"
            },
            {
                "label": "U.S. News \u2014 public health rankings",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-ssw-clinical-social-work-practice": {
        "summary": "BU's Master of Social Work is a long-established program with clinical and macro tracks and field placements across Boston and internationally. Reviewers praise rigorous field education, faculty expertise, and licensure preparation, while noting field hours and emotional demands of clinical training.",
        "themes": [
            {
                "label": "Strong field education",
                "sentiment": "positive",
                "detail": "MSW students complete extensive supervised field placements in diverse settings."
            },
            {
                "label": "Clinical and macro options",
                "sentiment": "positive",
                "detail": "Tracks span direct clinical practice and policy/administration."
            },
            {
                "label": "Emotionally demanding",
                "sentiment": "caution",
                "detail": "Clinical social work training is intensive; self-care and supervision matter."
            }
        ],
        "sources": [
            {
                "label": "BU School of Social Work \u2014 MSW",
                "url": "https://www.bu.edu/ssw/academics/msw/"
            },
            {
                "label": "U.S. News \u2014 social work rankings",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-eng-electrical-engineering-bs": {
        "summary": "BU electrical engineering (College of Engineering) is a solid program in a research-intensive engineering college with ties to the Photonics Center and Boston's tech and defense industries. Reviewers highlight hands-on labs, co-op/internship access, and ECE strength in photonics and communications, while noting engineering workload and competitive grading.",
        "themes": [
            {"label": "Research and photonics ties", "sentiment": "positive", "detail": "BU's Photonics Center and ECE research span optics, RF, and embedded systems."},
            {"label": "Boston industry access", "sentiment": "positive", "detail": "Internships and co-ops are available across Boston tech, defense, and biotech firms."},
            {"label": "Rigorous workload", "sentiment": "caution", "detail": "Engineering core courses are demanding; time management is essential."},
        ],
        "sources": [
            {"label": "BU Electrical & Computer Engineering", "url": "https://www.bu.edu/ece/"},
            {"label": "BU College of Engineering", "url": "https://www.bu.edu/eng/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-com-journalism-bs": {
        "summary": "BU journalism (College of Communication) is one of the best-known undergraduate journalism programs in the country, with deep ties to Boston and national media outlets and a professional, newsroom-oriented curriculum. Reviewers praise faculty practitioners, internship pipelines, and COM facilities, while noting the competitive nature of media careers.",
        "themes": [
            {"label": "Top journalism reputation", "sentiment": "positive", "detail": "BU COM journalism is widely cited among the strongest undergraduate journalism programs."},
            {"label": "Practitioner faculty", "sentiment": "positive", "detail": "Courses are taught by working journalists and media professionals."},
            {"label": "Internship pipelines", "sentiment": "positive", "detail": "Boston and national outlets recruit BU journalism interns regularly."},
            {"label": "Media career competition", "sentiment": "caution", "detail": "Journalism remains a competitive field; networking and clips matter."},
        ],
        "sources": [
            {"label": "BU College of Communication — Journalism", "url": "https://www.bu.edu/com/academics/journalism/"},
            {"label": "U.S. News — BU rankings", "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-sha-bachelor-of-science-in-hospitality-administration": {
        "summary": "BU's School of Hospitality Administration is a specialized hospitality management program with industry-connected faculty, required internships, and study-abroad options. Reviewers highlight strong hotel and restaurant industry placement and Boston's tourism economy, while noting the niche focus compared with general business degrees.",
        "themes": [
            {"label": "Industry-connected curriculum", "sentiment": "positive", "detail": "SHA integrates internships, industry speakers, and property visits into the degree."},
            {"label": "Strong hospitality placement", "sentiment": "positive", "detail": "Graduates place into hotel, restaurant, and tourism management roles nationally."},
            {"label": "Niche vs. general business", "sentiment": "mixed", "detail": "The degree is hospitality-specific; career pivots may require additional credentials."},
        ],
        "sources": [
            {"label": "BU School of Hospitality Administration", "url": "https://www.bu.edu/hospitality/"},
            {"label": "Poets&Quants — hospitality programs overview", "url": "https://poetsandquants.com/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-cas-international-relations-ba": {
        "summary": "BU international relations (CAS and the Pardee School ecosystem) draws on Boston's global policy and diplomatic community with strengths in security, regional studies, and language study. Reviewers value study-abroad options, Pardee-affiliated faculty, and DC/Boston internship paths, while noting large introductory courses.",
        "themes": [
            {"label": "Global policy hub", "sentiment": "positive", "detail": "Boston and Pardee connections support internships in policy, NGOs, and government."},
            {"label": "Language and regional depth", "sentiment": "positive", "detail": "Students combine IR with language study and regional concentrations."},
            {"label": "Large intro classes", "sentiment": "caution", "detail": "Popular IR prerequisites can be large; seminars improve with upper-level courses."},
        ],
        "sources": [
            {"label": "Frederick S. Pardee School of Global Studies", "url": "https://www.bu.edu/pardee/"},
            {"label": "BU Department of Political Science / IR", "url": "https://www.bu.edu/polisci/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-com-film-television-film-televisionbs": {
        "summary": "BU film & television (College of Communication) is a production-oriented program with professional facilities and faculty active in the industry. Reviewers praise hands-on production courses, Boston and LA internship paths, and COM's creative community, while noting equipment demands and competitive entertainment careers.",
        "themes": [
            {"label": "Production-focused training", "sentiment": "positive", "detail": "Students gain hands-on experience in writing, directing, and production crafts."},
            {"label": "Industry faculty", "sentiment": "positive", "detail": "Working filmmakers and television professionals teach core courses."},
            {"label": "Competitive entertainment careers", "sentiment": "caution", "detail": "Breaking into film/TV remains competitive; portfolio and networking are critical."},
        ],
        "sources": [
            {"label": "BU College of Communication — Film & Television", "url": "https://www.bu.edu/com/academics/film-television/"},
            {"label": "U.S. News — BU rankings", "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-eng-biomedical-engineering-bs": {
        "summary": "BU biomedical engineering integrates engineering with BU's medical campus and hospitals, with research in neural, cardiac, and imaging systems. Reviewers highlight interdisciplinary projects, clinical proximity, and grad-school/industry placement, while noting a demanding pre-med and engineering double workload for some students.",
        "themes": [
            {"label": "Medical campus integration", "sentiment": "positive", "detail": "BME students collaborate with Medical Campus researchers and clinicians."},
            {"label": "Interdisciplinary research", "sentiment": "positive", "detail": "Projects span neural engineering, medical devices, and imaging."},
            {"label": "Heavy courseload", "sentiment": "caution", "detail": "Combining BME with pre-med or double majors is academically intense."},
        ],
        "sources": [
            {"label": "BU Biomedical Engineering", "url": "https://www.bu.edu/bme/"},
            {"label": "BU College of Engineering", "url": "https://www.bu.edu/eng/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-questrom-ms-in-business-analytics": {
        "summary": "Questrom's STEM-designated MS in Business Analytics is a 10-month, on-campus program that blends programming, statistics, machine learning, and business fundamentals with a capstone project. Poets&Quants and official Questrom materials highlight the Feld Center's career coaching, a dedicated analytics career fair, and strong placement into analytics, consulting, and tech roles in Boston and nationally, while noting the intensive pace and competitive admissions.",
        "themes": [
            {"label": "STEM analytics + business blend", "sentiment": "positive", "detail": "Curriculum spans Python/SQL, causal and predictive modeling, and business application areas."},
            {"label": "Career support", "sentiment": "positive", "detail": "Feld Center coaching, mock interviews, and a Questrom analytics career fair support recruiting."},
            {"label": "Boston industry access", "sentiment": "positive", "detail": "Location supports internships and hiring across healthcare, tech, and consulting."},
            {"label": "Intensive 10-month pace", "sentiment": "caution", "detail": "The compressed schedule demands strong quantitative preparation and time management."},
        ],
        "sources": [
            {"label": "Poets&Quants — Questrom MSBA", "url": "https://poetsandquants.com/specialized-master/boston-universitys-questrom-school-of-business-ms-in-business-analytics/"},
            {"label": "Questrom MSBA careers", "url": "https://www.bu.edu/questrom/graduate-programs/specialty-masters-programs/ms-in-business-analytics/careers/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-questrom-ms-in-finance": {
        "summary": "Questrom's STEM-eligible MS in Finance offers 9- and 16-month tracks for both finance-background students and career changers, with a hands-on curriculum aligned to CFA foundations and electives in corporate finance, investments, and risk. Reviewers cite Boston's financial-hub location, Feld Center career coaching, and day-one-ready modeling skills, while noting tuition cost and that outcomes depend on prior finance exposure and networking.",
        "themes": [
            {"label": "STEM finance curriculum", "sentiment": "positive", "detail": "Program emphasizes financial modeling, valuation, and risk with CFA-aligned foundations."},
            {"label": "Flexible 9/16-month tracks", "sentiment": "positive", "detail": "Accelerated and extended tracks accommodate different backgrounds and internship goals."},
            {"label": "Boston finance market", "sentiment": "positive", "detail": "Proximity to asset managers, banks, and fintech supports recruiting."},
            {"label": "Background-dependent outcomes", "sentiment": "mixed", "detail": "Career changers may need the longer track and extra networking to break in."},
        ],
        "sources": [
            {"label": "Questrom MS in Finance", "url": "https://www.bu.edu/questrom/graduate-programs/specialty-masters-programs/ms-in-finance/"},
            {"label": "QS — Questrom School of Business", "url": "https://www.topuniversities.com/universities/boston-university/questrom-school-business"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-questrom-mathematical-finance-ms": {
        "summary": "BU's MS in Mathematical Finance & Financial Technology (MSMFT) at Questrom is a quant-focused program combining stochastic modeling, programming, and financial engineering with access to Boston's trading and fintech employers. Third-party guides and forum applicants describe rigorous coursework and strong quant placement for prepared students, while warning that the program is math-intensive and selective.",
        "themes": [
            {"label": "Quant and fintech focus", "sentiment": "positive", "detail": "Curriculum targets stochastic calculus, derivatives, and computational finance."},
            {"label": "Rigorous preparation required", "sentiment": "caution", "detail": "Students need strong math and programming; the pace is demanding."},
            {"label": "Boston quant hiring", "sentiment": "positive", "detail": "Graduates recruit into asset management, trading, and fintech in the Northeast."},
        ],
        "sources": [
            {"label": "Questrom — Mathematical Finance", "url": "https://www.bu.edu/questrom/graduate-programs/specialty-masters-programs/ms-in-mathematical-finance/"},
            {"label": "QS — Questrom School of Business", "url": "https://www.topuniversities.com/universities/boston-university/questrom-school-business"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cds-ms-in-data-science": {
        "summary": "BU's Faculty of Computing & Data Sciences MS in Data Science is a flexible, STEM-designated 32-credit program completable in 9–16 months with only one required course and concentrations in core or applied methods. Program director materials and admissions guides emphasize project-based learning, rapid curriculum updates for AI/LLMs, and optional thesis or Boston internships, while noting selective admissions and the need for strong CS/math prerequisites.",
        "themes": [
            {"label": "Flexible, student-built pathway", "sentiment": "positive", "detail": "Electives span ML, cloud, security, and social-impact data science with minimal fixed core."},
            {"label": "AI-forward curriculum", "sentiment": "positive", "detail": "Recent additions include deep learning and large-language-model coursework."},
            {"label": "Project-based DS 701", "sentiment": "positive", "detail": "Semester-long client projects build portfolio-ready experience."},
            {"label": "Selective admissions", "sentiment": "caution", "detail": "Applicants need substantial CS, stats, and math preparation."},
        ],
        "sources": [
            {"label": "BU CDS — MS in Data Science", "url": "https://www.bu.edu/cds-faculty/programs-admissions/ms-data-science/"},
            {"label": "MSDS director Q&A", "url": "https://www.bu.edu/cds-faculty/2025/09/09/adapting-to-an-evolving-field-qa-with-msds-director-tom-gardos/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-met-computer-science-ms": {
        "summary": "Metropolitan College's online MS in Computer Science is one of BU's longest-running professional graduate computing degrees, aimed at working technologists seeking depth in software engineering, databases, and systems while studying part-time or online. Reviewers value the flexibility, BU credential, and Boston-area employer recognition, while noting that online delivery requires self-direction and that the experience differs from the residential CDS/ENG CS paths.",
        "themes": [
            {"label": "Working-professional flexibility", "sentiment": "positive", "detail": "Evening and online formats suit engineers advancing without leaving work."},
            {"label": "BU-branded CS credential", "sentiment": "positive", "detail": "Degree carries the university's R1 research reputation in the Boston market."},
            {"label": "Self-directed online pace", "sentiment": "caution", "detail": "Online students must manage time and networking proactively."},
        ],
        "sources": [
            {"label": "BU Metropolitan College — Computer Science", "url": "https://www.bu.edu/met/academics/graduate/computer-science/"},
            {"label": "U.S. News — BU rankings", "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-met-computer-science-master-of-science-in-applied-data-analytics": {
        "summary": "MET's MS in Applied Data Analytics targets practitioners who need Python, SQL, visualization, and machine-learning skills for business and government roles, delivered online through Metropolitan College. Coverage highlights practical project work, affordability relative to residential analytics degrees, and Boston employer familiarity with MET credentials, while noting less campus immersion than Questrom MSBA or CDS MSDS.",
        "themes": [
            {"label": "Applied analytics for practitioners", "sentiment": "positive", "detail": "Coursework emphasizes tools and projects over theory-heavy research."},
            {"label": "Online accessibility", "sentiment": "positive", "detail": "Format suits career changers and working analysts upskilling."},
            {"label": "Less residential networking", "sentiment": "mixed", "detail": "Online MET students build fewer on-campus recruiting ties than full-time programs."},
        ],
        "sources": [
            {"label": "BU MET — Applied Data Analytics", "url": "https://www.bu.edu/met/academics/graduate/applied-data-analytics/"},
            {"label": "BU Metropolitan College", "url": "https://www.bu.edu/met/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-computer-engineering-bs": {
        "summary": "BU's undergraduate computer engineering (ECE) combines hardware, embedded systems, and software with access to the Photonics Center and Boston tech/defense employers. Student guides and department materials praise hands-on labs, co-op pathways, and interdisciplinary ties to CS and BME, while noting competitive grading and large lower-division engineering cores.",
        "themes": [
            {"label": "Hardware + software integration", "sentiment": "positive", "detail": "ECE spans embedded systems, communications, and digital design."},
            {"label": "Photonics and Boston industry", "sentiment": "positive", "detail": "Research centers and co-ops connect to optics, defense, and tech firms."},
            {"label": "Demanding engineering core", "sentiment": "caution", "detail": "Shared engineering prerequisites are workload-heavy in the first two years."},
        ],
        "sources": [
            {"label": "BU Electrical & Computer Engineering", "url": "https://www.bu.edu/ece/"},
            {"label": "BU College of Engineering", "url": "https://www.bu.edu/eng/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-mechanical-engineering-bs": {
        "summary": "BU mechanical engineering is a broad, ABET-accredited program emphasizing design, thermofluids, materials, and robotics with project-based capstones and co-op options. Reviewers highlight solid fundamentals, access to BU research labs, and placement into aerospace, robotics, and manufacturing roles, while noting the generalist curriculum requires students to specialize through electives and projects.",
        "themes": [
            {"label": "Broad ME fundamentals", "sentiment": "positive", "detail": "Curriculum covers design, fluids, heat transfer, and dynamics with lab work."},
            {"label": "Co-op and project experience", "sentiment": "positive", "detail": "Senior design and co-ops connect students to Boston-area manufacturers and robotics firms."},
            {"label": "Generalist — specialize via electives", "sentiment": "mixed", "detail": "Students must choose tracks and projects to stand out for niche ME roles."},
        ],
        "sources": [
            {"label": "BU Mechanical Engineering", "url": "https://www.bu.edu/me/"},
            {"label": "BU College of Engineering", "url": "https://www.bu.edu/eng/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cas-economics-ba": {
        "summary": "BU's undergraduate economics (CAS) is a large, research-oriented major with strengths in econometrics, international economics, and policy, supported by the Hariri Institute and Boston's finance and policy employers. Reviewers praise rigorous quantitative training and faculty research access, while noting large lecture sections in introductory courses and that recruiting into finance/consulting requires proactive networking.",
        "themes": [
            {"label": "Quantitative economics training", "sentiment": "positive", "detail": "Major emphasizes econometrics, micro/macro theory, and data analysis."},
            {"label": "Boston policy and finance pipeline", "sentiment": "positive", "detail": "Internships span consulting, banking, NGOs, and government in the region."},
            {"label": "Large intro sections", "sentiment": "caution", "detail": "Lower-division courses can be big; seminars improve at the upper level."},
        ],
        "sources": [
            {"label": "BU Department of Economics", "url": "https://www.bu.edu/econ/"},
            {"label": "U.S. News — BU rankings", "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cas-physics-ba": {
        "summary": "BU physics (CAS) offers a traditional bachelor's with research opportunities in condensed matter, photonics, and astrophysics tied to campus labs and the Photonics Center. Student guides note strong preparation for graduate school and engineering crossover, while cautioning that advanced labs are demanding and undergraduate research slots are competitive.",
        "themes": [
            {"label": "Research-intensive physics", "sentiment": "positive", "detail": "Faculty labs span photonics, condensed matter, and astronomy."},
            {"label": "Grad-school preparation", "sentiment": "positive", "detail": "Rigorous coursework supports PhD and engineering graduate paths."},
            {"label": "Competitive research slots", "sentiment": "caution", "detail": "Undergraduate research requires early faculty outreach."},
        ],
        "sources": [
            {"label": "BU Department of Physics", "url": "https://www.bu.edu/physics/"},
            {"label": "BU Photonics Center", "url": "https://www.bu.edu/photonics/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cas-chemistry-ba": {
        "summary": "BU chemistry (CAS) provides ACS-aligned training with tracks in chemical biology, materials, and environmental chemistry, plus access to interdisciplinary research at the Medical Campus and Photonics Center. Reviewers highlight strong lab instruction and graduate-school placement, while noting pre-med overlap makes some courses competitive and crowded.",
        "themes": [
            {"label": "ACS-aligned chemistry training", "sentiment": "positive", "detail": "Program covers analytical, organic, physical, and inorganic chemistry with labs."},
            {"label": "Interdisciplinary research", "sentiment": "positive", "detail": "Ties to biomedical and materials research across BU campuses."},
            {"label": "Pre-med competition", "sentiment": "caution", "detail": "Popular pre-med sequences can mean competitive grading in gateway courses."},
        ],
        "sources": [
            {"label": "BU Department of Chemistry", "url": "https://www.bu.edu/chemistry/"},
            {"label": "U.S. News — BU rankings", "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cas-psychology-ba": {
        "summary": "BU's undergraduate psychology (CAS) is one of the university's largest majors, offering breadth in clinical, cognitive, and behavioral neuroscience with research labs and a Boston hospital ecosystem for internships. Niche and guide coverage praise research opportunities and pre-graduate training, while noting large lectures and that clinical careers require graduate study beyond the BA.",
        "themes": [
            {"label": "Broad psychology research", "sentiment": "positive", "detail": "Faculty span cognitive, developmental, clinical, and neuroscience areas."},
            {"label": "Boston clinical ecosystem", "sentiment": "positive", "detail": "Hospitals and labs provide internship and research placements."},
            {"label": "Graduate study required for practice", "sentiment": "caution", "detail": "The BA alone is insufficient for licensed clinical roles."},
        ],
        "sources": [
            {"label": "BU Department of Psychological & Brain Sciences", "url": "https://www.bu.edu/psych/"},
            {"label": "U.S. News — BU rankings", "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-com-journalism-ms": {
        "summary": "BU's MS in Journalism (College of Communication) extends the undergraduate program's practitioner faculty model to graduate students seeking advanced reporting, multimedia, and investigative skills. Reviewers cite working-journalist instructors, Boston and national internship pipelines, and COM facilities, while noting the competitive media job market and tuition cost of a private graduate degree.",
        "themes": [
            {"label": "Practitioner-led training", "sentiment": "positive", "detail": "Courses are taught by working reporters and editors with current industry practice."},
            {"label": "Multimedia reporting skills", "sentiment": "positive", "detail": "Graduate curriculum spans investigative, digital, and broadcast reporting."},
            {"label": "Tough media job market", "sentiment": "caution", "detail": "Graduates must build strong portfolios and networks to land staff roles."},
        ],
        "sources": [
            {"label": "BU COM — Journalism graduate programs", "url": "https://www.bu.edu/com/academics/journalism/"},
            {"label": "U.S. News — BU rankings", "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sha-ms": {
        "summary": "BU's MS in Hospitality Administration (SHA) is a specialized graduate degree combining revenue management, operations, and leadership with required industry internships and global study options. Poets&Quants and hospitality rankings cite strong hotel-industry placement and faculty practitioner ties, while noting the niche focus compared with general MBA paths.",
        "themes": [
            {"label": "Industry-connected SHA", "sentiment": "positive", "detail": "Curriculum integrates property visits, internships, and hotel-management case work."},
            {"label": "Strong hospitality placement", "sentiment": "positive", "detail": "Graduates place into hotel, restaurant, and tourism leadership roles."},
            {"label": "Niche vs. general management", "sentiment": "mixed", "detail": "Degree is hospitality-specific; pivots may need supplemental business training."},
        ],
        "sources": [
            {"label": "BU School of Hospitality Administration", "url": "https://www.bu.edu/hospitality/"},
            {"label": "Poets&Quants — hospitality programs", "url": "https://poetsandquants.com/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-ssw-msw": {
        "summary": "BU's online MSW extends the School of Social Work's clinically focused training to working students, with the same CSWE-accredited curriculum as the on-campus program and extensive field-education requirements. Reviewers praise field-placement support and licensure preparation, while noting that online students must arrange local placements and that clinical social work is emotionally demanding.",
        "themes": [
            {"label": "CSWE-accredited online MSW", "sentiment": "positive", "detail": "Online students complete the same accredited curriculum and field hours."},
            {"label": "Field-education strength", "sentiment": "positive", "detail": "BU SSW is known for supervised clinical placements across diverse settings."},
            {"label": "Local placement logistics", "sentiment": "caution", "detail": "Online students must secure approved field sites near their residence."},
        ],
        "sources": [
            {"label": "BU School of Social Work — MSW Online", "url": "https://www.bu.edu/ssw/academics/msw/"},
            {"label": "U.S. News — social work rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-mba-mph": {
        "summary": "BU's dual MBA/MPH combines Questrom business training with the School of Public Health's top-10 MPH, aimed at health-sector leaders managing programs, policy, and operations. Coverage highlights interdisciplinary health-management careers in hospitals, biotech, and NGOs, while warning of the workload and cost of completing two graduate degrees concurrently.",
        "themes": [
            {"label": "Health-management dual credential", "sentiment": "positive", "detail": "Combines business strategy with accredited public-health training."},
            {"label": "Top-10 SPH foundation", "sentiment": "positive", "detail": "SPH ranks among the nation's leading schools of public health."},
            {"label": "Heavy dual-degree workload", "sentiment": "caution", "detail": "Pursuing MBA and MPH requirements simultaneously is time-intensive."},
        ],
        "sources": [
            {"label": "BU School of Public Health — dual degrees", "url": "https://www.bumc.bu.edu/sph/education/degrees-and-programs/dual-degrees/"},
            {"label": "U.S. News — public health rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-busm-combined-md-mba": {
        "summary": "BU's MD/MBA dual degree trains physician-leaders through the Chobanian & Avedisian School of Medicine and Questrom, targeting students pursuing health-care administration, biotech entrepreneurship, or policy roles. Reviewers value the combination of clinical training with business fundamentals and Boston's health-sector ecosystem, while noting the extended timeline and cost of two demanding degrees.",
        "themes": [
            {"label": "Physician-leader pipeline", "sentiment": "positive", "detail": "Program targets clinicians moving into management, policy, or venture roles."},
            {"label": "Boston health ecosystem", "sentiment": "positive", "detail": "Medical Campus and Questrom connect students to hospitals, biotech, and payers."},
            {"label": "Long, expensive dual path", "sentiment": "caution", "detail": "Completing MD and MBA requirements adds years and tuition beyond medicine alone."},
        ],
        "sources": [
            {"label": "BU School of Medicine — MD/MBA", "url": "https://www.bumc.bu.edu/busm/education/md-programs/dual-degree-programs/md-mba/"},
            {"label": "Questrom School of Business", "url": "https://www.bu.edu/questrom/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-computer-engineering-ms": {
        "summary": "BU's MS in Computer Engineering (ECE) offers graduate depth in embedded systems, communications, and hardware-software co-design with ties to photonics and robotics research. Reviewers highlight research lab access and Boston tech hiring, while noting that funding is limited compared with PhD paths and applicants should clarify thesis vs. coursework tracks.",
        "themes": [
            {"label": "Graduate ECE depth", "sentiment": "positive", "detail": "MS students specialize in communications, embedded systems, or signal processing."},
            {"label": "Research lab access", "sentiment": "positive", "detail": "ECE labs connect to photonics, robotics, and sensing research."},
            {"label": "Limited MS funding", "sentiment": "caution", "detail": "Most financial support targets PhD students; MS students often self-fund."},
        ],
        "sources": [
            {"label": "BU Electrical & Computer Engineering — graduate", "url": "https://www.bu.edu/ece/academics/graduate-programs/"},
            {"label": "BU College of Engineering", "url": "https://www.bu.edu/eng/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cas-mathematics-statistics-ba": {
        "summary": "BU's mathematics & statistics undergraduate major (CAS) provides rigorous pure and applied training with pathways into actuarial science, data science, and graduate math. Reviewers praise proof-based coursework and faculty research exposure, while noting that students aiming for industry analytics often pair the major with CS or economics coursework.",
        "themes": [
            {"label": "Rigorous math foundation", "sentiment": "positive", "detail": "Major covers analysis, algebra, probability, and statistics with proof-based courses."},
            {"label": "Graduate-school and quant paths", "sentiment": "positive", "detail": "Graduates pursue PhDs, actuarial exams, and quantitative industry roles."},
            {"label": "Add CS/econ for industry analytics", "sentiment": "mixed", "detail": "Industry data roles often require supplemental computing coursework."},
        ],
        "sources": [
            {"label": "BU Department of Mathematics & Statistics", "url": "https://www.bu.edu/math/"},
            {"label": "U.S. News — BU rankings", "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-met-computer-science-bs": {
        "summary": "Metropolitan College's part-time/online BS in Computer Science serves working adults and transfer students seeking a BU undergraduate credential with flexibility. Reviewers value the accessibility and career-upgrading potential, while noting differences from the residential CAS/CDS CS paths in research exposure and campus recruiting.",
        "themes": [
            {"label": "Flexible undergraduate CS", "sentiment": "positive", "detail": "Evening and online options support working students completing a BS."},
            {"label": "Career-upgrading credential", "sentiment": "positive", "detail": "BU bachelor's helps professionals pivot into software roles."},
            {"label": "Less residential recruiting", "sentiment": "mixed", "detail": "Part-time students have fewer on-campus career-fair touchpoints."},
        ],
        "sources": [
            {"label": "BU MET — Computer Science undergraduate", "url": "https://www.bu.edu/met/academics/undergraduate/computer-science/"},
            {"label": "BU Metropolitan College", "url": "https://www.bu.edu/met/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
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
    if slug not in _CLASS_PROFILE_BY_SLUG or _CLASS_PROFILE_BY_SLUG.get(slug, {}).get("cohort_size") is None:
        omitted.append("class_profile.cohort_size")
    if slug not in _FACULTY_BY_SLUG:
        omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    return _standard(omitted)


def apply(session: Session) -> bool:
    """Enrich Boston University to the canonical profile. Flushes; caller commits."""
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    school_outcomes["_standard"] = _standard(_OMITTED_INSTITUTION)
    inst.school_outcomes = school_outcomes
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    inst.founded_year = 1839
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.bu.edu"
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
    existing = {s.name: s for s in session.scalars(select(School).where(School.institution_id == inst.id))}
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


def _website_for(spec: dict) -> str:
    return _WEBSITE_OVERRIDE.get(spec["slug"], SCHOOL_WEBSITE[spec["school"]])


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
                institution_id=inst.id, program_name=spec["program_name"],
                degree_type=spec["degree_type"], slug=slug,
            )
            session.add(p)
        p.program_name = spec["program_name"]
        p.degree_type = spec["degree_type"]
        p.department = spec.get("department")
        p.duration_months = spec.get("duration_months")
        p.description_text = spec["description"]
        p.website_url = _website_for(spec)
        p.delivery_format = spec.get("delivery_format", "on_campus")
        p.tracks = None
        p.application_requirements = _requirements_for(spec)
        p.cost_data = _undergrad_cost() if spec["degree_type"] == "bachelors" else _grad_cost_fallback(spec)
        outcomes = dict(_OUTCOMES_BY_SLUG.get(slug, {}))
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        kw = _PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(_KEYWORDS_BY_SCHOOL[spec["school"]])
        p.content_sources = _program_content(spec["school"], kw)
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
    for slug, p in existing.items():
        if slug not in canonical:
            if _program_has_dependents(session, p.id):
                p.is_published = False
            else:
                session.delete(p)
    session.flush()
