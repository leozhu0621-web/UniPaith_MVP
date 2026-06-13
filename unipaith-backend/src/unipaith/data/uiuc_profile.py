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
This is a large catalog (419 programs), so external reviews are attached to the
flagship coverable programs and the remaining programs record those deep fields in
their ``_standard.omitted`` pending a future depth pass.
"""

# ruff: noqa: E501

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "University of Illinois Urbana-Champaign"
ENRICHED_AT = "2026-06-13"


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
        "rank": 70, "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/university-illinois-urbana-champaign",
    },
    "times_higher_education": {
        "rank": 41, "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-illinois-urbana-champaign",
    },
    "us_news_national": {
        "rank": 36, "year": 2026,
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
        "white": 0.3753, "asian": 0.2311, "hispanic": 0.1441, "black": 0.0531,
        "two_or_more": 0.0412, "american_indian": 0.0003, "pacific_islander": 0.0003,
        "international": 0.1391, "unknown": 0.0154, "women": 0.496,
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
            {"name": "Krannert Center for the Performing Arts", "url": "https://krannertcenter.com/"},
            {"name": "Illini Union", "url": "https://union.illinois.edu/"},
            {"name": "Campus Recreation", "url": "https://campusrec.illinois.edu/"},
        ],
    },
    "media_credit": "Wikimedia Commons / Daniel Schwen (CC BY-SA 4.0)",
    "campus_photos": [
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/UIUC_Illini_Union_and_Main_Quad.jpg/1920px-UIUC_Illini_Union_and_Main_Quad.jpg",
         "credit": "Wikimedia Commons / Daniel Schwen (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/UIUC_Main_Quad_Panorama.jpg/1920px-UIUC_Main_Quad_Panorama.jpg",
         "credit": "Wikimedia Commons / kosheahan (CC BY 2.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/Foellinger_Auditorium_University_of_Illinois_at_Urbana-Champaign_from_mid-quad.jpg/1920px-Foellinger_Auditorium_University_of_Illinois_at_Urbana-Champaign_from_mid-quad.jpg",
         "credit": "Wikimedia Commons / Beyond My Ken (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Altgeld_Hall%2C_University_of_Illinois.jpg/1920px-Altgeld_Hall%2C_University_of_Illinois.jpg",
         "credit": "Wikimedia Commons / Kevin Dooley (CC BY 2.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Memorial_Stadium_Champaign_Panorama.jpg/1920px-Memorial_Stadium_Champaign_Panorama.jpg",
         "credit": "Wikimedia Commons / Cubbie15fan (CC BY-SA 3.0)"},
    ],
    "flagship": {
        "enrollment_total": 59238,
        "applicants": 73742,
        "admits": 31247,
        "admissions_cycle": "First-year, Fall 2024 (UIUC Common Data Set 2024-2025)",
        "founded_year": 1867,
    },
    "sources": [
        {"label": "U.S. Dept. of Education — College Scorecard (UIUC, UNITID 145637)",
         "url": "https://collegescorecard.ed.gov/school/?145637-University-of-Illinois-Urbana-Champaign"},
        {"label": "NCES College Navigator — University of Illinois Urbana-Champaign (IPEDS)",
         "url": "https://nces.ed.gov/collegenavigator/?id=145637"},
        {"label": "UIUC Common Data Set 2024-2025 (admissions funnel, enrollment, test scores)",
         "url": "https://dmi.illinois.edu/cds/"},
        {"label": "UIUC facts & rankings (enrollment, ratio, research centers)",
         "url": "https://www.admissions.illinois.edu/discover/illinois-facts"},
        {"label": "UIUC News Bureau — record Fall 2024 enrollment",
         "url": "https://news.illinois.edu/illinois-welcomes-largest-number-of-students-in-university-history/"},
        {"label": "UIUC rankings (U.S. News 2025-2026 college and departmental ranks)",
         "url": "https://illinois.edu/about/rankings/"},
        {"label": "UIUC Academic Catalog 2026-2027 — undergraduate + graduate program indexes",
         "url": "https://catalog.illinois.edu/degree-programs/"},
        {"label": "Provost's Council of Deans (college leadership)",
         "url": "https://provost.illinois.edu/about/committees/provosts-council-of-deans/"},
        {"label": "Carnegie Classifications — University of Illinois Urbana-Champaign (R1)",
         "url": "https://carnegieclassifications.acenet.edu/institution/university-of-illinois-urbana-champaign/"},
        {"label": "Higher Learning Commission — University of Illinois Urbana-Champaign (accreditation)",
         "url": "https://www.hlcommission.org/institution/1156/"},
        {"label": "QS World University Rankings 2026 — UIUC (#70)",
         "url": "https://www.topuniversities.com/universities/university-illinois-urbana-champaign"},
        {"label": "Times Higher Education World University Rankings 2026 — UIUC (#41)",
         "url": "https://www.timeshighereducation.com/world-university-rankings/university-illinois-urbana-champaign"},
        {"label": "U.S. News Best Colleges 2026 — UIUC (#36 National, #12 public)",
         "url": "https://www.usnews.com/best-colleges/university-of-illinois-1775"},
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
    {'key': 'ENGR', 'name': 'The Grainger College of Engineering', 'sort_order': 1, 'website': 'https://grainger.illinois.edu/', 'leadership': 'Rashid Bashir — Dean', 'research_centers': ['Siebel School of Computing and Data Science', 'Department of Electrical & Computer Engineering', 'Department of Mechanical Science & Engineering', 'Department of Aerospace Engineering', 'Department of Civil & Environmental Engineering', 'Department of Materials Science & Engineering'], 'keywords': ['Grainger College of Engineering', 'Grainger Engineering', 'engineering', 'computer science']},
    {'key': 'LAS', 'name': 'College of Liberal Arts and Sciences', 'sort_order': 2, 'website': 'https://las.illinois.edu/', 'leadership': 'Venetria K. Patton — Dean', 'research_centers': ['School of Chemical Sciences', 'School of Molecular & Cellular Biology', 'School of Literatures, Cultures & Linguistics', 'School of Earth, Society & Environment', 'Department of Mathematics', 'Department of Economics'], 'keywords': ['College of Liberal Arts and Sciences', 'LAS', 'liberal arts and sciences']},
    {'key': 'BUS', 'name': 'Gies College of Business', 'sort_order': 3, 'website': 'https://giesbusiness.illinois.edu/', 'leadership': 'W. Brooke Elliott — Dean', 'research_centers': ['Department of Accountancy', 'Department of Finance', 'Department of Business Administration', 'Gies online programs (iMBA, iMSA, iMSM)'], 'keywords': ['Gies College of Business', 'Gies Business', 'business', 'accountancy', 'iMBA']},
    {'key': 'ACES', 'name': 'College of Agricultural, Consumer and Environmental Sciences', 'sort_order': 4, 'website': 'https://aces.illinois.edu/', 'leadership': 'Germ\u00e1n Bollero — Dean', 'research_centers': ['Department of Crop Sciences', 'Department of Animal Sciences', 'Department of Agricultural & Consumer Economics', 'Department of Food Science & Human Nutrition', 'Department of Natural Resources & Environmental Sciences'], 'keywords': ['College of ACES', 'Agricultural Consumer and Environmental Sciences', 'agriculture']},
    {'key': 'FAA', 'name': 'College of Fine and Applied Arts', 'sort_order': 5, 'website': 'https://faa.illinois.edu/', 'leadership': 'Jake Pinholster — Dean', 'research_centers': ['School of Architecture', 'School of Art & Design', 'School of Music', 'Department of Landscape Architecture', 'Department of Urban & Regional Planning', 'Krannert Art Museum'], 'keywords': ['College of Fine and Applied Arts', 'fine and applied arts', 'architecture', 'music']},
    {'key': 'AHS', 'name': 'College of Applied Health Sciences', 'sort_order': 6, 'website': 'https://ahs.illinois.edu/', 'leadership': 'Cheryl Hanley-Maxwell — Dean', 'research_centers': ['Department of Kinesiology & Community Health', 'Department of Speech & Hearing Science', 'Department of Recreation, Sport & Tourism', 'Department of Health & Kinesiology'], 'keywords': ['College of Applied Health Sciences', 'applied health sciences', 'kinesiology']},
    {'key': 'EDUC', 'name': 'College of Education', 'sort_order': 7, 'website': 'https://education.illinois.edu/', 'leadership': 'Chrystalla Mouza — Dean', 'research_centers': ['Department of Curriculum & Instruction', 'Department of Education Policy, Organization & Leadership', 'Department of Educational Psychology', 'Department of Special Education'], 'keywords': ['College of Education', 'education', 'teaching']},
    {'key': 'MDIA', 'name': 'College of Media', 'sort_order': 8, 'website': 'https://media.illinois.edu/', 'leadership': 'Tracy Sulkin — Dean', 'research_centers': ['Charles H. Sandage Department of Advertising', 'Department of Journalism', 'Institute of Communications Research'], 'keywords': ['College of Media', 'media', 'journalism', 'advertising']},
    {'key': 'IS', 'name': 'School of Information Sciences', 'sort_order': 9, 'website': 'https://ischool.illinois.edu/', 'leadership': 'Emily Knox — Interim Dean', 'research_centers': ['Master of Science in Information Sciences (LIS)', 'Bachelor of Science in Information Sciences', 'Informatics graduate program'], 'keywords': ['School of Information Sciences', 'iSchool', 'information sciences', 'library and information science']},
    {'key': 'SOCW', 'name': 'School of Social Work', 'sort_order': 10, 'website': 'https://socialwork.illinois.edu/', 'leadership': 'Ben Lough — Interim Dean', 'research_centers': ['Bachelor of Social Work program', 'Master of Social Work (MSW) program', 'Ph.D. in Social Work program'], 'keywords': ['School of Social Work', 'social work', 'MSW']},
    {'key': 'LER', 'name': 'School of Labor and Employment Relations', 'sort_order': 11, 'website': 'https://ler.illinois.edu/', 'leadership': 'Simon Lloyd D. Restubog — Dean', 'research_centers': ['Master of Human Resources & Industrial Relations (MHRIR) program', 'Ph.D. in Labor and Employment Relations program'], 'keywords': ['School of Labor and Employment Relations', 'labor and employment relations', 'human resources']},
    {'key': 'LAW', 'name': 'College of Law', 'sort_order': 12, 'website': 'https://law.illinois.edu/', 'leadership': 'Jamelle Sharpe — Dean', 'research_centers': ['Juris Doctor (J.D.) program', 'Master of Laws (LL.M.) program', 'Doctor of the Science of Law (J.S.D.) program'], 'keywords': ['University of Illinois College of Law', 'College of Law', 'law', 'J.D.']},
    {'key': 'VETMED', 'name': 'College of Veterinary Medicine', 'sort_order': 13, 'website': 'https://vetmed.illinois.edu/', 'leadership': 'Peter Constable — Dean', 'research_centers': ['Department of Comparative Biosciences', 'Department of Pathobiology', 'Department of Veterinary Clinical Medicine', 'Doctor of Veterinary Medicine (DVM) program'], 'keywords': ['College of Veterinary Medicine', 'veterinary medicine', 'DVM']},
    {'key': 'CIMED', 'name': 'Carle Illinois College of Medicine', 'sort_order': 14, 'website': 'https://medicine.illinois.edu/', 'leadership': 'Mark S. Cohen — Dean', 'research_centers': ['Doctor of Medicine (M.D.) program', 'Department of Biomedical & Translational Sciences', 'Engineering-based medicine curriculum (with Carle Health)'], 'keywords': ['Carle Illinois College of Medicine', 'Carle Illinois', 'medicine', 'M.D.']},
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
_NEWS_URL = "https://news.illinois.edu/"
_SOCIAL = {
    "instagram": "https://www.instagram.com/illinois1867/",
    "linkedin": "https://www.linkedin.com/school/university-of-illinois-urbana-champaign/",
    "x": "https://twitter.com/Illinois_Alma",
    "youtube": "https://www.youtube.com/user/universityofillinois",
    "facebook": "https://www.facebook.com/IllinoisUniversity/",
}
_INSTITUTION_CONTENT: dict = {"news_url": _NEWS_URL, "news_curated": True, "social": _SOCIAL}
_KEYWORDS_BY_SCHOOL = {m["name"]: m["keywords"] for m in _SCHOOL_META}


def _school_content(name: str) -> dict:
    return {
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
    ('uiuc-agricultural-biological-engineering-bs-agricultural-engineering-agricultural-science-bsag', 'ACES', 'Agricultural & Biological Engineering Sciences', 'bachelors', 'Agricultural & Biological Engineering Sciences', 'on_campus', 48),
    ('uiuc-agricultural-consumer-economics-bs', 'ACES', 'Agricultural & Consumer Economics', 'bachelors', 'Agricultural & Consumer Economics', 'on_campus', 48),
    ('uiuc-agricultural-leadership-education-communications-bs', 'ACES', 'Agricultural Leadership, Education, & Communications', 'bachelors', 'Agricultural Leadership, Education, & Communications', 'on_campus', 48),
    ('uiuc-agronomy-bs', 'ACES', 'Agronomy', 'bachelors', 'Agronomy', 'on_campus', 48),
    ('uiuc-animal-sciences-bs', 'ACES', 'Animal Sciences', 'bachelors', 'Animal Sciences', 'on_campus', 48),
    ('uiuc-computer-science-animal-sciences-bs', 'ACES', 'Computer Science + Animal Sciences', 'bachelors', 'Computer Science + Animal Sciences', 'on_campus', 48),
    ('uiuc-computer-science-crop-sciences-bs', 'ACES', 'Computer Science + Crop Sciences', 'bachelors', 'Computer Science + Crop Sciences', 'on_campus', 48),
    ('uiuc-crop-sciences-bs', 'ACES', 'Crop Sciences', 'bachelors', 'Crop Sciences', 'on_campus', 48),
    ('uiuc-dietetics-nutrition-bs', 'ACES', 'Dietetics', 'bachelors', 'Dietetics', 'on_campus', 48),
    ('uiuc-engineering-technology-management-agricultural-systems-bs', 'ACES', 'Engineering Technology & Management for Agricultural Systems', 'bachelors', 'Engineering Technology & Management for Agricultural Systems', 'on_campus', 48),
    ('uiuc-food-science-bs', 'ACES', 'Food Science', 'bachelors', 'Food Science', 'on_campus', 48),
    ('uiuc-hospitality-management-bs', 'ACES', 'Hospitality Management', 'bachelors', 'Hospitality Management', 'on_campus', 48),
    ('uiuc-human-development-family-studies-bs', 'ACES', 'Human Development & Family Studies', 'bachelors', 'Human Development & Family Studies', 'on_campus', 48),
    ('uiuc-natural-resources-environmental-sciences-bs', 'ACES', 'Natural Resources & Environmental Sciences', 'bachelors', 'Natural Resources & Environmental Sciences', 'on_campus', 48),
    ('uiuc-nutrition-health-bs', 'ACES', 'Nutrition', 'bachelors', 'Nutrition', 'on_campus', 48),
    ('uiuc-plant-biotechnology-bs', 'ACES', 'Plant Biotechnology', 'bachelors', 'Plant Biotechnology', 'on_campus', 48),
    ('uiuc-sustainability-food-environmental-systems-bs', 'ACES', 'Sustainability in Food & Environmental Systems', 'bachelors', 'Sustainability in Food & Environmental Systems', 'on_campus', 48),
    ('uiuc-agricultural-applied-economics-maae', 'ACES', 'Agricultural & Applied Economics', 'masters', 'Agricultural & Applied Economics', 'on_campus', 24),
    ('uiuc-agricultural-applied-economics-ms', 'ACES', 'Agricultural & Applied Economics', 'masters', 'Agricultural & Applied Economics', 'on_campus', 24),
    ('uiuc-agricultural-leadership-education-communications-ms', 'ACES', 'Agricultural Leadership, Education, & Communications', 'masters', 'Agricultural Leadership, Education, & Communications', 'on_campus', 24),
    ('uiuc-animal-sciences-mansc', 'ACES', 'Animal Sciences', 'masters', 'Animal Sciences', 'on_campus', 24),
    ('uiuc-animal-sciences-ms', 'ACES', 'Animal Sciences', 'masters', 'Animal Sciences', 'on_campus', 24),
    ('uiuc-child-health-ms', 'ACES', 'Child Health', 'masters', 'Child Health', 'on_campus', 24),
    ('uiuc-crop-sciences-ms', 'ACES', 'Crop Sciences', 'masters', 'Crop Sciences', 'on_campus', 24),
    ('uiuc-engineering-technology-management-agricultural-systems-ms', 'ACES', 'Engineering Technology & Management for Agricultural Systems', 'masters', 'Engineering Technology & Management for Agricultural Systems', 'on_campus', 24),
    ('uiuc-food-science-human-nutrition-ms', 'ACES', 'Food Science & Human Nutrition', 'masters', 'Food Science & Human Nutrition', 'on_campus', 24),
    ('uiuc-human-development-family-studies-ms', 'ACES', 'Human Development & Family Studies', 'masters', 'Human Development & Family Studies', 'on_campus', 24),
    ('uiuc-natural-resources-environmental-sciences-ms', 'ACES', 'Natural Resources & Environmental Sciences', 'masters', 'Natural Resources & Environmental Sciences', 'on_campus', 24),
    ('uiuc-nutritional-science-ms', 'ACES', 'Nutritional Sciences', 'masters', 'Nutritional Sciences', 'on_campus', 24),
    ('uiuc-agricultural-applied-economics-phd', 'ACES', 'Agricultural & Applied Economics', 'phd', 'Agricultural & Applied Economics', 'on_campus', 60),
    ('uiuc-animal-sciences-phd', 'ACES', 'Animal Sciences', 'phd', 'Animal Sciences', 'on_campus', 60),
    ('uiuc-crop-sciences-phd', 'ACES', 'Crop Sciences', 'phd', 'Crop Sciences', 'on_campus', 60),
    ('uiuc-engineering-technology-management-agricultural-systems', 'ACES', 'Engineering Technology & Management for Agricultural Systems', 'phd', 'Engineering Technology & Management for Agricultural Systems', 'on_campus', 60),
    ('uiuc-food-science-human-nutrition-phd', 'ACES', 'Food Science & Human Nutrition', 'phd', 'Food Science & Human Nutrition', 'on_campus', 60),
    ('uiuc-human-development-family-studies-phd', 'ACES', 'Human Development & Family Studies', 'phd', 'Human Development & Family Studies', 'on_campus', 60),
    ('uiuc-natural-resources-environmental-sciences-phd', 'ACES', 'Natural Resources & Environmental Sciences', 'phd', 'Natural Resources & Environmental Sciences', 'on_campus', 60),
    ('uiuc-nutritional-science-phd', 'ACES', 'Nutritional Sciences', 'phd', 'Nutritional Sciences', 'on_campus', 60),
    ('uiuc-community-health-bs', 'AHS', 'Community Health', 'bachelors', 'Community Health', 'on_campus', 48),
    ('uiuc-interdisciplinary-health-sciences-bs', 'AHS', 'Interdisciplinary Health Sciences', 'bachelors', 'Interdisciplinary Health Sciences', 'on_campus', 48),
    ('uiuc-BS', 'AHS', 'Kinesiology', 'bachelors', 'Kinesiology', 'on_campus', 48),
    ('uiuc-public-health-bs', 'AHS', 'Public Health', 'bachelors', 'Public Health', 'on_campus', 48),
    ('uiuc-recreation-sport-tourism-bs', 'AHS', 'Recreation, Sport & Tourism', 'bachelors', 'Recreation, Sport & Tourism', 'on_campus', 48),
    ('uiuc-speech-hearing-science-bs', 'AHS', 'Speech & Hearing Science', 'bachelors', 'Speech & Hearing Science', 'on_campus', 48),
    ('uiuc-community-health-ms', 'AHS', 'Community Health', 'masters', 'Community Health', 'on_campus', 24),
    ('uiuc-epidemiology-mph', 'AHS', 'Epidemiology', 'masters', 'Epidemiology', 'on_campus', 24),
    ('uiuc-health-administration-mha', 'AHS', 'Health Administration', 'masters', 'Health Administration', 'on_campus', 24),
    ('uiuc-health-technology-ms', 'AHS', 'Health Technology', 'masters', 'Health Technology', 'on_campus', 24),
    ('uiuc-kinesiology-ms', 'AHS', 'Kinesiology', 'masters', 'Kinesiology', 'on_campus', 24),
    ('uiuc-public-health-mph', 'AHS', 'Public Health', 'masters', 'Public Health', 'on_campus', 24),
    ('uiuc-recreation-sport-tourism-ms', 'AHS', 'Recreation, Sport & Tourism', 'masters', 'Recreation, Sport & Tourism', 'on_campus', 24),
    ('uiuc-speech-hearing-science-ma', 'AHS', 'Speech & Hearing Science', 'masters', 'Speech & Hearing Science', 'on_campus', 24),
    ('uiuc-community-health-phd', 'AHS', 'Community Health', 'phd', 'Community Health', 'on_campus', 60),
    ('uiuc-kinesiology-phd', 'AHS', 'Kinesiology', 'phd', 'Kinesiology', 'on_campus', 60),
    ('uiuc-recreation-sport-tourism-phd', 'AHS', 'Recreation, Sport & Tourism', 'phd', 'Recreation, Sport & Tourism', 'on_campus', 60),
    ('uiuc-speech-hearing-science-phd', 'AHS', 'Speech & Hearing Science', 'phd', 'Speech & Hearing Science', 'on_campus', 60),
    ('uiuc-audiology-aud', 'AHS', 'Speech & Hearing Science', 'professional', 'Speech & Hearing Science', 'on_campus', 48),
    ('uiuc-accountancy-bs', 'BUS', 'Accountancy', 'bachelors', 'Accountancy', 'on_campus', 48),
    ('uiuc-accountancy-data-science-bs', 'BUS', 'Accountancy + Data Science', 'bachelors', 'Accountancy + Data Science', 'on_campus', 48),
    ('uiuc-business-data-science-bs', 'BUS', 'Business + Data Science', 'bachelors', 'Business + Data Science', 'on_campus', 48),
    ('uiuc-finance-bs', 'BUS', 'Finance', 'bachelors', 'Finance', 'on_campus', 48),
    ('uiuc-finance-data-science-bs', 'BUS', 'Finance + Data Science', 'bachelors', 'Finance + Data Science', 'on_campus', 48),
    ('uiuc-information-systems-bs', 'BUS', 'Information Systems', 'bachelors', 'Information Systems', 'on_campus', 48),
    ('uiuc-management-business-bs', 'BUS', 'Management', 'bachelors', 'Management', 'on_campus', 48),
    ('uiuc-marketing-bs', 'BUS', 'Marketing', 'bachelors', 'Marketing', 'on_campus', 48),
    ('uiuc-operations-management-bs', 'BUS', 'Operations Management', 'bachelors', 'Operations Management', 'on_campus', 48),
    ('uiuc-supply-chain-bs', 'BUS', 'Supply Chain Management', 'bachelors', 'Supply Chain Management', 'on_campus', 48),
    ('uiuc-accountancy-mas', 'BUS', 'Accountancy', 'masters', 'Accountancy', 'on_campus', 24),
    ('uiuc-accountancy-ms', 'BUS', 'Accountancy', 'masters', 'Accountancy', 'on_campus', 24),
    ('uiuc-accountancy-imsa-ms', 'BUS', 'Accountancy (iMSA)', 'masters', 'Department of Accountancy', 'online', 24),
    ('uiuc-business-administration-online-mba', 'BUS', 'Business Administration (iMBA)', 'masters', 'Business Administration (iMBA)', 'online', 24),
    ('uiuc-business-analytics-ms', 'BUS', 'Business Analytics', 'masters', 'Business Analytics', 'on_campus', 24),
    ('uiuc-finance-ms', 'BUS', 'Finance', 'masters', 'Finance', 'on_campus', 24),
    ('uiuc-financial-engineering-ms', 'BUS', 'Financial Engineering', 'masters', 'Financial Engineering', 'on_campus', 24),
    ('uiuc-management-ms', 'BUS', 'Management', 'masters', 'Management', 'on_campus', 24),
    ('uiuc-management-imsm-ms', 'BUS', 'Management (iMSM)', 'masters', 'Department of Business Administration', 'online', 24),
    ('uiuc-technology-management-ms', 'BUS', 'Technology Management', 'masters', 'Technology Management', 'on_campus', 24),
    ('uiuc-accountancy-phd', 'BUS', 'Accountancy', 'phd', 'Accountancy', 'on_campus', 60),
    ('uiuc-business-administration-phd', 'BUS', 'Business Administration', 'phd', 'Business Administration', 'on_campus', 60),
    ('uiuc-finance-phd', 'BUS', 'Finance', 'phd', 'Finance', 'on_campus', 60),
    ('uiuc-medicine-md', 'CIMED', 'Medicine', 'professional', 'Doctor of Medicine', 'on_campus', 48),
    ('uiuc-computer-science-education-bs', 'EDUC', 'Computer Science + Education', 'bachelors', 'Computer Science + Education', 'on_campus', 48),
    ('uiuc-early-childhood-education-bs', 'EDUC', 'Early Childhood Education', 'bachelors', 'Early Childhood Education', 'on_campus', 48),
    ('uiuc-elementary-education-bs', 'EDUC', 'Elementary Education', 'bachelors', 'Elementary Education', 'on_campus', 48),
    ('uiuc-learning-education-studies-bs', 'EDUC', 'Learning & Education Studies', 'bachelors', 'Learning & Education Studies', 'on_campus', 48),
    ('uiuc-middle-grades-education-bs', 'EDUC', 'Middle Grades Education', 'bachelors', 'Middle Grades Education', 'on_campus', 48),
    ('uiuc-secondary-education-bs', 'EDUC', 'Secondary Education', 'bachelors', 'Secondary Education', 'on_campus', 48),
    ('uiuc-special-education-bs', 'EDUC', 'Special Education', 'bachelors', 'Special Education', 'on_campus', 48),
    ('uiuc-curriculum-instruction-edm', 'EDUC', 'Curriculum & Instruction', 'masters', 'Curriculum & Instruction', 'on_campus', 24),
    ('uiuc-curriculum-instruction-ma', 'EDUC', 'Curriculum & Instruction', 'masters', 'Curriculum & Instruction', 'on_campus', 24),
    ('uiuc-curriculum-instruction-ms', 'EDUC', 'Curriculum & Instruction', 'masters', 'Curriculum & Instruction', 'on_campus', 24),
    ('uiuc-early-childhood-education-edm', 'EDUC', 'Early Childhood Education', 'masters', 'Early Childhood Education', 'on_campus', 24),
    ('uiuc-education-policy-organization-leadership-edm', 'EDUC', 'Education Policy, Organization & Leadership', 'masters', 'Education Policy, Organization & Leadership', 'on_campus', 24),
    ('uiuc-education-policy-organization-leadership-ma', 'EDUC', 'Education Policy, Organization & Leadership', 'masters', 'Education Policy, Organization & Leadership', 'on_campus', 24),
    ('uiuc-educational-psychology-edm', 'EDUC', 'Educational Psychology', 'masters', 'Educational Psychology', 'on_campus', 24),
    ('uiuc-educational-psychology-ma', 'EDUC', 'Educational Psychology', 'masters', 'Educational Psychology', 'on_campus', 24),
    ('uiuc-educational-psychology-ms', 'EDUC', 'Educational Psychology', 'masters', 'Educational Psychology', 'on_campus', 24),
    ('uiuc-elementary-education-edm', 'EDUC', 'Elementary Education', 'masters', 'Elementary Education', 'on_campus', 24),
    ('uiuc-mental-health-counseling-ms', 'EDUC', 'Mental Health Counseling', 'masters', 'Mental Health Counseling', 'on_campus', 24),
    ('uiuc-secondary-education-edm', 'EDUC', 'Secondary Education', 'masters', 'Secondary Education', 'on_campus', 24),
    ('uiuc-special-education-edm', 'EDUC', 'Special Education', 'masters', 'Special Education', 'on_campus', 24),
    ('uiuc-curriculum-instruction-edd', 'EDUC', 'Curriculum & Instruction', 'phd', 'Curriculum & Instruction', 'on_campus', 60),
    ('uiuc-curriculum-instruction-phd', 'EDUC', 'Curriculum & Instruction', 'phd', 'Curriculum & Instruction', 'on_campus', 60),
    ('uiuc-education-policy-organization-leadership-edd', 'EDUC', 'Education Policy, Organization & Leadership', 'phd', 'Education Policy, Organization & Leadership', 'on_campus', 60),
    ('uiuc-education-policy-organization-leadership-phd', 'EDUC', 'Education Policy, Organization & Leadership', 'phd', 'Education Policy, Organization & Leadership', 'on_campus', 60),
    ('uiuc-educational-psychology-phd', 'EDUC', 'Educational Psychology', 'phd', 'Educational Psychology', 'on_campus', 60),
    ('uiuc-special-education-phd', 'EDUC', 'Special Education', 'phd', 'Special Education', 'on_campus', 60),
    ('uiuc-aerospace-engineering-bs', 'ENGR', 'Aerospace Engineering', 'bachelors', 'Aerospace Engineering', 'on_campus', 48),
    ('uiuc-agricultural-biological-engineering-bs', 'ENGR', 'Agricultural & Biological Engineering', 'bachelors', 'Agricultural & Biological Engineering', 'on_campus', 48),
    ('uiuc-bioengineering-bs', 'ENGR', 'Bioengineering', 'bachelors', 'Bioengineering', 'on_campus', 48),
    ('uiuc-chemical-engineering-bs', 'ENGR', 'Chemical Engineering', 'bachelors', 'Chemical Engineering', 'on_campus', 48),
    ('uiuc-civil-engineering-bs', 'ENGR', 'Civil Engineering', 'bachelors', 'Civil Engineering', 'on_campus', 48),
    ('uiuc-computer-engineering-bs', 'ENGR', 'Computer Engineering', 'bachelors', 'Computer Engineering', 'on_campus', 48),
    ('uiuc-computer-science-bs', 'ENGR', 'Computer Science', 'bachelors', 'Computer Science', 'on_campus', 48),
    ('uiuc-computer-science-bioengineering-bs', 'ENGR', 'Computer Science + Bioengineering', 'bachelors', 'Computer Science + Bioengineering', 'on_campus', 48),
    ('uiuc-computer-science-physics-bs', 'ENGR', 'Computer Science + Physics', 'bachelors', 'Computer Science + Physics', 'on_campus', 48),
    ('uiuc-electrical-engineering-bs', 'ENGR', 'Electrical Engineering', 'bachelors', 'Electrical Engineering', 'on_campus', 48),
    ('uiuc-engineering-mechanics-bs', 'ENGR', 'Engineering Mechanics', 'bachelors', 'Engineering Mechanics', 'on_campus', 48),
    ('uiuc-engineering-physics-bs', 'ENGR', 'Engineering Physics', 'bachelors', 'Engineering Physics', 'on_campus', 48),
    ('uiuc-environmental-engineering-bs', 'ENGR', 'Environmental Engineering', 'bachelors', 'Environmental Engineering', 'on_campus', 48),
    ('uiuc-industrial-engineering-bs', 'ENGR', 'Industrial Engineering', 'bachelors', 'Industrial Engineering', 'on_campus', 48),
    ('uiuc-innovation-leadership-engineering-entrepreneurship-bs', 'ENGR', 'Innovation, Leadership, & Engineering Entrepreneurship', 'bachelors', 'Innovation, Leadership, & Engineering Entrepreneurship', 'on_campus', 48),
    ('uiuc-materials-science-engineering-bs', 'ENGR', 'Materials Science & Engineering', 'bachelors', 'Materials Science & Engineering', 'on_campus', 48),
    ('uiuc-materials-science-engineering-data-science-bs', 'ENGR', 'Materials Science & Engineering + Data Science', 'bachelors', 'Materials Science & Engineering + Data Science', 'on_campus', 48),
    ('uiuc-mechanical-engineering-bs', 'ENGR', 'Mechanical Engineering', 'bachelors', 'Mechanical Engineering', 'on_campus', 48),
    ('uiuc-neural-engineering-bs', 'ENGR', 'Neural Engineering', 'bachelors', 'Neural Engineering', 'on_campus', 48),
    ('uiuc-nuclear-plasma-radiological-engineering-bs', 'ENGR', 'Nuclear, Plasma & Radiological Engineering', 'bachelors', 'Nuclear, Plasma & Radiological Engineering', 'on_campus', 48),
    ('uiuc-nuclear-plasma-radiological-engineering-data-science-bs', 'ENGR', 'Nuclear, Plasma, and Radiological Engineering + Data Science', 'bachelors', 'Nuclear, Plasma, and Radiological Engineering + Data Science', 'on_campus', 48),
    ('uiuc-physics-bs', 'ENGR', 'Physics', 'bachelors', 'Physics', 'on_campus', 48),
    ('uiuc-systems-engineering-design-bs', 'ENGR', 'Systems Engineering and Design', 'bachelors', 'Systems Engineering and Design', 'on_campus', 48),
    ('uiuc-aerospace-engineering-ms', 'ENGR', 'Aerospace Engineering', 'masters', 'Aerospace Engineering', 'on_campus', 24),
    ('uiuc-agricultural-biological-engineering-ms', 'ENGR', 'Agricultural & Biological Engineering', 'masters', 'Agricultural & Biological Engineering', 'on_campus', 24),
    ('uiuc-bioengineering-meng', 'ENGR', 'Bioengineering', 'masters', 'Bioengineering', 'on_campus', 24),
    ('uiuc-bioengineering-ms', 'ENGR', 'Bioengineering', 'masters', 'Bioengineering', 'on_campus', 24),
    ('uiuc-biomedical-image-computing-ms', 'ENGR', 'Biomedical Image Computing', 'masters', 'Biomedical Image Computing', 'on_campus', 24),
    ('uiuc-chemical-engineering-ms', 'ENGR', 'Chemical Engineering', 'masters', 'Chemical Engineering', 'on_campus', 24),
    ('uiuc-chemical-engineering-leadership-meng', 'ENGR', 'Chemical Engineering Leadership', 'masters', 'Chemical Engineering Leadership', 'on_campus', 24),
    ('uiuc-civil-engineering-ms', 'ENGR', 'Civil Engineering', 'masters', 'Civil Engineering', 'on_campus', 24),
    ('uiuc-computer-science-ms', 'ENGR', 'Computer Science', 'masters', 'Computer Science', 'on_campus', 24),
    ('uiuc-computer-science-mcs', 'ENGR', 'Computer Science', 'masters', 'Computer Science', 'on_campus', 24),
    ('uiuc-computer-science-online-mcs', 'ENGR', 'Computer Science (Online)', 'masters', 'Siebel School of Computing and Data Science', 'online', 24),
    ('uiuc-electrical-computer-engineering-meng', 'ENGR', 'Electrical & Computer Engineering', 'masters', 'Electrical & Computer Engineering', 'on_campus', 24),
    ('uiuc-electrical-computer-engineering-ms', 'ENGR', 'Electrical & Computer Engineering', 'masters', 'Electrical & Computer Engineering', 'on_campus', 24),
    ('uiuc-engineering-meng', 'ENGR', 'Engineering', 'masters', 'Engineering', 'on_campus', 24),
    ('uiuc-environmental-engineering-civil-engineering-ms', 'ENGR', 'Environmental Engineering in Civil Engineering', 'masters', 'Environmental Engineering in Civil Engineering', 'on_campus', 24),
    ('uiuc-industrial-engineering-ms', 'ENGR', 'Industrial Engineering', 'masters', 'Industrial Engineering', 'on_campus', 24),
    ('uiuc-materials-engineering-meng', 'ENGR', 'Materials Engineering', 'masters', 'Materials Engineering', 'on_campus', 24),
    ('uiuc-materials-science-engineering-ms', 'ENGR', 'Materials Science & Engineering', 'masters', 'Materials Science & Engineering', 'on_campus', 24),
    ('uiuc-mechanical-engineering-ms', 'ENGR', 'Mechanical Engineering', 'masters', 'Mechanical Engineering', 'on_campus', 24),
    ('uiuc-mechanical-engineering-meng', 'ENGR', 'Mechanical Engineering', 'masters', 'Mechanical Engineering', 'on_campus', 24),
    ('uiuc-nuclear-plasma-radiological-engineering-ms', 'ENGR', 'Nuclear, Plasma & Radiological Engineering', 'masters', 'Nuclear, Plasma & Radiological Engineering', 'on_campus', 24),
    ('uiuc-physics-ms', 'ENGR', 'Physics', 'masters', 'Physics', 'on_campus', 24),
    ('uiuc-teaching-physics-ms', 'ENGR', 'Physics, Teaching of', 'masters', 'Physics, Teaching of', 'on_campus', 24),
    ('uiuc-systems-entrepreneurial-engineering-ms', 'ENGR', 'Systems & Entrepreneurial Engineering', 'masters', 'Systems & Entrepreneurial Engineering', 'on_campus', 24),
    ('uiuc-theoretical-applied-mechanics-ms', 'ENGR', 'Theoretical & Applied Mechanics', 'masters', 'Theoretical & Applied Mechanics', 'on_campus', 24),
    ('uiuc-aerospace-engineering-phd', 'ENGR', 'Aerospace Engineering', 'phd', 'Aerospace Engineering', 'on_campus', 60),
    ('uiuc-agricultural-biological-engineering-phd', 'ENGR', 'Agricultural & Biological Engineering', 'phd', 'Agricultural & Biological Engineering', 'on_campus', 60),
    ('uiuc-bioengineering-phd', 'ENGR', 'Bioengineering', 'phd', 'Bioengineering', 'on_campus', 60),
    ('uiuc-chemical-engineering-phd', 'ENGR', 'Chemical Engineering', 'phd', 'Chemical Engineering', 'on_campus', 60),
    ('uiuc-civil-engineering-phd', 'ENGR', 'Civil Engineering', 'phd', 'Civil Engineering', 'on_campus', 60),
    ('uiuc-computer-science-phd', 'ENGR', 'Computer Science', 'phd', 'Computer Science', 'on_campus', 60),
    ('uiuc-electrical-computer-engineering-phd', 'ENGR', 'Electrical & Computer Engineering', 'phd', 'Electrical & Computer Engineering', 'on_campus', 60),
    ('uiuc-environmental-engineering-civil-engineering-phd', 'ENGR', 'Environmental Engineering in Civil Engineering', 'phd', 'Environmental Engineering in Civil Engineering', 'on_campus', 60),
    ('uiuc-industrial-engineering-phd', 'ENGR', 'Industrial Engineering', 'phd', 'Industrial Engineering', 'on_campus', 60),
    ('uiuc-materials-science-engineering-phd', 'ENGR', 'Materials Science & Engineering', 'phd', 'Materials Science & Engineering', 'on_campus', 60),
    ('uiuc-mechanical-engineering-phd', 'ENGR', 'Mechanical Engineering', 'phd', 'Mechanical Engineering', 'on_campus', 60),
    ('uiuc-nuclear-plasma-radiological-engineering-phd', 'ENGR', 'Nuclear, Plasma & Radiological Engineering', 'phd', 'Nuclear, Plasma & Radiological Engineering', 'on_campus', 60),
    ('uiuc-physics-phd', 'ENGR', 'Physics', 'phd', 'Physics', 'on_campus', 60),
    ('uiuc-systems-entrepreneurial-engineering-phd', 'ENGR', 'Systems & Entrepreneurial Engineering', 'phd', 'Systems & Entrepreneurial Engineering', 'on_campus', 60),
    ('uiuc-theoretical-applied-mechanics-phd', 'ENGR', 'Theoretical & Applied Mechanics', 'phd', 'Theoretical & Applied Mechanics', 'on_campus', 60),
    ('uiuc-architectural-studies-bs', 'FAA', 'Architectural Studies', 'bachelors', 'Architectural Studies', 'on_campus', 48),
    ('uiuc-foundation', 'FAA', 'Art & Design', 'bachelors', 'Art & Design', 'on_campus', 48),
    ('uiuc-art-education-bfa', 'FAA', 'Art Education', 'bachelors', 'Art Education', 'on_campus', 48),
    ('uiuc-computer-science-music-bs', 'FAA', 'Computer Science + Music', 'bachelors', 'Computer Science + Music', 'on_campus', 48),
    ('uiuc-dance-bfa', 'FAA', 'Dance', 'bachelors', 'Dance', 'on_campus', 48),
    ('uiuc-dance-ba', 'FAA', 'Dance', 'bachelors', 'Dance', 'on_campus', 48),
    ('uiuc-graphic-design-bfa', 'FAA', 'Graphic Design', 'bachelors', 'Graphic Design', 'on_campus', 48),
    ('uiuc-industrial-design-bfa', 'FAA', 'Industrial Design', 'bachelors', 'Industrial Design', 'on_campus', 48),
    ('uiuc-jazz-performance-bmus', 'FAA', 'Jazz Performance', 'bachelors', 'Jazz Performance', 'on_campus', 48),
    ('uiuc-landscape-architecture-bla', 'FAA', 'Landscape Architecture', 'bachelors', 'Landscape Architecture', 'on_campus', 48),
    ('uiuc-lyric-theatre-bma', 'FAA', 'Lyric Theatre', 'bachelors', 'Lyric Theatre', 'on_campus', 48),
    ('uiuc-music-ba', 'FAA', 'Music', 'bachelors', 'Music', 'on_campus', 48),
    ('uiuc-music-composition-bmus', 'FAA', 'Music Composition', 'bachelors', 'Music Composition', 'on_campus', 48),
    ('uiuc-music-education-bme', 'FAA', 'Music Education', 'bachelors', 'Music Education', 'on_campus', 48),
    ('uiuc-musicology-bmus', 'FAA', 'Musicology', 'bachelors', 'Musicology', 'on_campus', 48),
    ('uiuc-music-open-studies-bmus', 'FAA', 'Open Studies', 'bachelors', 'Open Studies', 'on_campus', 48),
    ('uiuc-studio-art-basa', 'FAA', 'Studio Art', 'bachelors', 'Studio Art', 'on_campus', 48),
    ('uiuc-studio-art-bfasa', 'FAA', 'Studio Art', 'bachelors', 'Studio Art', 'on_campus', 48),
    ('uiuc-sustainable-design-bs', 'FAA', 'Sustainable Design', 'bachelors', 'Sustainable Design', 'on_campus', 48),
    ('uiuc-theatre-bfa', 'FAA', 'Theatre', 'bachelors', 'Theatre', 'on_campus', 48),
    ('uiuc-urban-studies-planning-ba', 'FAA', 'Urban Planning', 'bachelors', 'Urban Planning', 'on_campus', 48),
    ('uiuc-architectural-studies-ms', 'FAA', 'Architectural Studies', 'masters', 'Architectural Studies', 'on_campus', 24),
    ('uiuc-architecture-march', 'FAA', 'Architecture', 'masters', 'Architecture', 'on_campus', 24),
    ('uiuc-art-design-mfa', 'FAA', 'Art & Design', 'masters', 'Art & Design', 'on_campus', 24),
    ('uiuc-art-education-edm', 'FAA', 'Art Education', 'masters', 'Art Education', 'on_campus', 24),
    ('uiuc-art-education-ma', 'FAA', 'Art Education', 'masters', 'Art Education', 'on_campus', 24),
    ('uiuc-dance-mfa', 'FAA', 'Dance', 'masters', 'Dance', 'on_campus', 24),
    ('uiuc-industrial-design-mdes', 'FAA', 'Industrial Design', 'masters', 'Industrial Design', 'on_campus', 24),
    ('uiuc-landscape-architecture-mla', 'FAA', 'Landscape Architecture', 'masters', 'Landscape Architecture', 'on_campus', 24),
    ('uiuc-music-mmus', 'FAA', 'Music', 'masters', 'Music', 'on_campus', 24),
    ('uiuc-music-education-mme', 'FAA', 'Music Education', 'masters', 'Music Education', 'on_campus', 24),
    ('uiuc-sustainable-urban-design-msud', 'FAA', 'Sustainable Urban Design', 'masters', 'Sustainable Urban Design', 'on_campus', 24),
    ('uiuc-theatre-ma', 'FAA', 'Theatre', 'masters', 'Theatre', 'on_campus', 24),
    ('uiuc-theatre-mfa', 'FAA', 'Theatre', 'masters', 'Theatre', 'on_campus', 24),
    ('uiuc-urban-planning-mup', 'FAA', 'Urban Planning', 'masters', 'Urban Planning', 'on_campus', 24),
    ('uiuc-architecture-phd', 'FAA', 'Architecture', 'phd', 'Architecture', 'on_campus', 60),
    ('uiuc-art-education-phd', 'FAA', 'Art Education', 'phd', 'Art Education', 'on_campus', 60),
    ('uiuc-landscape-architecture-phd', 'FAA', 'Landscape Architecture', 'phd', 'Landscape Architecture', 'on_campus', 60),
    ('uiuc-music-dma', 'FAA', 'Music', 'phd', 'Music', 'on_campus', 60),
    ('uiuc-music-education-phd', 'FAA', 'Music Education', 'phd', 'Music Education', 'on_campus', 60),
    ('uiuc-musicology-phd', 'FAA', 'Musicology', 'phd', 'Musicology', 'on_campus', 60),
    ('uiuc-regional-planning-phd', 'FAA', 'Regional Planning', 'phd', 'Regional Planning', 'on_campus', 60),
    ('uiuc-theatre-phd', 'FAA', 'Theatre', 'phd', 'Theatre', 'on_campus', 60),
    ('uiuc-artist-diploma-music', 'FAA', 'Music', 'diploma', 'Music', 'on_campus', 24),
    ('uiuc-information-sciences-bs', 'IS', 'Information Sciences', 'bachelors', 'Information Sciences', 'on_campus', 48),
    ('uiuc-information-sciences-data-science-bs', 'IS', 'Information Sciences + Data Science', 'bachelors', 'Information Sciences + Data Science', 'on_campus', 48),
    ('uiuc-bioinformatics-ms', 'IS', 'Bioinformatics', 'masters', 'Bioinformatics', 'on_campus', 24),
    ('uiuc-game-development-ms', 'IS', 'Game Development', 'masters', 'Game Development', 'on_campus', 24),
    ('uiuc-information-management-ms', 'IS', 'Information Management', 'masters', 'Information Management', 'on_campus', 24),
    ('uiuc-library-information-science-ms', 'IS', 'Information Sciences', 'masters', 'Information Sciences', 'on_campus', 24),
    ('uiuc-informatics-phd', 'IS', 'Informatics', 'phd', 'Informatics', 'on_campus', 60),
    ('uiuc-information-science-phd', 'IS', 'Information Sciences', 'phd', 'Information Sciences', 'on_campus', 60),
    ('uiuc-actuarial-science-bslas', 'LAS', 'Actuarial Science', 'bachelors', 'Actuarial Science', 'on_campus', 48),
    ('uiuc-african-american-studies-balas', 'LAS', 'African American Studies', 'bachelors', 'African American Studies', 'on_campus', 48),
    ('uiuc-anthropology-balas', 'LAS', 'Anthropology', 'bachelors', 'Anthropology', 'on_campus', 48),
    ('uiuc-art-history-balas', 'LAS', 'Art History', 'bachelors', 'Art History', 'on_campus', 48),
    ('uiuc-art-art-history-bfa', 'LAS', 'Art History', 'bachelors', 'Art History', 'on_campus', 48),
    ('uiuc-asian-american-studies-balas', 'LAS', 'Asian American Studies', 'bachelors', 'Asian American Studies', 'on_campus', 48),
    ('uiuc-astronomy-bslas', 'LAS', 'Astronomy', 'bachelors', 'Astronomy', 'on_campus', 48),
    ('uiuc-astronomy-data-science-bslas', 'LAS', 'Astronomy + Data Science', 'bachelors', 'Astronomy + Data Science', 'on_campus', 48),
    ('uiuc-astrophysics-bslas', 'LAS', 'Astrophysics', 'bachelors', 'Astrophysics', 'on_campus', 48),
    ('uiuc-atmospheric-sciences-bslas', 'LAS', 'Atmospheric Sciences', 'bachelors', 'Atmospheric Sciences', 'on_campus', 48),
    ('uiuc-biochemistry-bs', 'LAS', 'Biochemistry', 'bachelors', 'Biochemistry', 'on_campus', 48),
    ('uiuc-index.html', 'LAS', 'Chemical Engineering + Data Science', 'bachelors', 'Chemical Engineering + Data Science', 'on_campus', 48),
    ('uiuc-chemistry-bslas', 'LAS', 'Chemistry', 'bachelors', 'Chemistry', 'on_campus', 48),
    ('uiuc-chemistry-bs', 'LAS', 'Chemistry', 'bachelors', 'Chemistry', 'on_campus', 48),
    ('uiuc-classics-balas', 'LAS', 'Classics', 'bachelors', 'Classics', 'on_campus', 48),
    ('uiuc-communication-balas', 'LAS', 'Communication', 'bachelors', 'Communication', 'on_campus', 48),
    ('uiuc-comparative-literature', 'LAS', 'Comparative Literature', 'bachelors', 'Comparative Literature', 'on_campus', 48),
    ('uiuc-computer-science-anthropology-bslas', 'LAS', 'Computer Science + Anthropology', 'bachelors', 'Computer Science + Anthropology', 'on_campus', 48),
    ('uiuc-computer-science-astronomy-bs', 'LAS', 'Computer Science + Astronomy', 'bachelors', 'Computer Science + Astronomy', 'on_campus', 48),
    ('uiuc-computer-science-chemistry-bslas', 'LAS', 'Computer Science + Chemistry', 'bachelors', 'Computer Science + Chemistry', 'on_campus', 48),
    ('uiuc-computer-science-economics-bslas', 'LAS', 'Computer Science + Economics', 'bachelors', 'Computer Science + Economics', 'on_campus', 48),
    ('uiuc-computer-science-geography-geographic-information-science-bslas', 'LAS', 'Computer Science + Geography & Geographic Information Science', 'bachelors', 'Computer Science + Geography & Geographic Information Science', 'on_campus', 48),
    ('uiuc-computer-science-linguistics-bslas', 'LAS', 'Computer Science + Linguistics', 'bachelors', 'Computer Science + Linguistics', 'on_campus', 48),
    ('uiuc-computer-science-philosophy-bslas', 'LAS', 'Computer Science + Philosophy', 'bachelors', 'Computer Science + Philosophy', 'on_campus', 48),
    ('uiuc-creative-writing-balas', 'LAS', 'Creative Writing', 'bachelors', 'Creative Writing', 'on_campus', 48),
    ('uiuc-earth-society-environmental-sustainability-bslas', 'LAS', 'Earth, Society, & Environmental Sustainability', 'bachelors', 'Earth, Society, & Environmental Sustainability', 'on_campus', 48),
    ('uiuc-east-asian-languages-cultures-balas', 'LAS', 'East Asian Languages & Cultures', 'bachelors', 'East Asian Languages & Cultures', 'on_campus', 48),
    ('uiuc-econometrics-quantitative-economics-bslas', 'LAS', 'Econometrics & Quantitative Economics', 'bachelors', 'Econometrics & Quantitative Economics', 'on_campus', 48),
    ('uiuc-economics-balas', 'LAS', 'Economics', 'bachelors', 'Economics', 'on_campus', 48),
    ('uiuc-english-balas', 'LAS', 'English', 'bachelors', 'English', 'on_campus', 48),
    ('uiuc-environmental-sustainability-bslas', 'LAS', 'Environmental Sustainability', 'bachelors', 'Environmental Sustainability', 'on_campus', 48),
    ('uiuc-french-balas', 'LAS', 'French', 'bachelors', 'French', 'on_campus', 48),
    ('uiuc-teaching-french-ba', 'LAS', 'French Teaching', 'bachelors', 'French Teaching', 'on_campus', 48),
    ('uiuc-gender-womens-studies-balas', 'LAS', "Gender & Women's Studies", 'bachelors', "Gender & Women's Studies", 'on_campus', 48),
    ('uiuc-geography-geographic-information-science-balas', 'LAS', 'Geography & Geographic Information Science', 'bachelors', 'Geography & Geographic Information Science', 'on_campus', 48),
    ('uiuc-geography-geographic-information-science-bslas', 'LAS', 'Geography & Geographic Information Science', 'bachelors', 'Geography & Geographic Information Science', 'on_campus', 48),
    ('uiuc-geology-bslas', 'LAS', 'Geology', 'bachelors', 'Geology', 'on_campus', 48),
    ('uiuc-geology-bs', 'LAS', 'Geology', 'bachelors', 'Geology', 'on_campus', 48),
    ('uiuc-teaching-german-ba', 'LAS', 'German Teaching', 'bachelors', 'German Teaching', 'on_campus', 48),
    ('uiuc-germanic-studies-balas', 'LAS', 'Germanic Studies', 'bachelors', 'Germanic Studies', 'on_campus', 48),
    ('uiuc-global-studies-balas', 'LAS', 'Global Studies', 'bachelors', 'Global Studies', 'on_campus', 48),
    ('uiuc-history-balas', 'LAS', 'History', 'bachelors', 'History', 'on_campus', 48),
    ('uiuc-individual-plans-study', 'LAS', 'Individual Plans of Study', 'bachelors', 'Individual Plans of Study', 'on_campus', 48),
    ('uiuc-integrative-biology-bslas', 'LAS', 'Integrative Biology', 'bachelors', 'Integrative Biology', 'on_campus', 48),
    ('uiuc-honors', 'LAS', 'Integrative Biology Honors', 'bachelors', 'Integrative Biology Honors', 'on_campus', 48),
    ('uiuc-interdisciplinary-studies-balas', 'LAS', 'Interdisciplinary Studies', 'bachelors', 'Interdisciplinary Studies', 'on_campus', 48),
    ('uiuc-italian-balas', 'LAS', 'Italian', 'bachelors', 'Italian', 'on_campus', 48),
    ('uiuc-latin-american-studies-balas', 'LAS', 'Latin American Studies', 'bachelors', 'Latin American Studies', 'on_campus', 48),
    ('uiuc-latina-latino-studies-balas', 'LAS', 'Latina/Latino Studies', 'bachelors', 'Latina/Latino Studies', 'on_campus', 48),
    ('uiuc-liberal-studies-bls', 'LAS', 'Liberal Studies', 'bachelors', 'Liberal Studies', 'on_campus', 48),
    ('uiuc-linguistics-balas', 'LAS', 'Linguistics', 'bachelors', 'Linguistics', 'on_campus', 48),
    ('uiuc-linguistics-teaching-english-second-language-tesl-balas', 'LAS', 'Linguistics and Teaching English as a Second Language, BALAS (TESL)', 'bachelors', 'Linguistics and Teaching English as a Second Language, BALAS (TESL)', 'on_campus', 48),
    ('uiuc-mathematics-bslas', 'LAS', 'Mathematics', 'bachelors', 'Mathematics', 'on_campus', 48),
    ('uiuc-mathematics-computer-science-bslas', 'LAS', 'Mathematics & Computer Science', 'bachelors', 'Mathematics & Computer Science', 'on_campus', 48),
    ('uiuc-molecular-cellular-biology-bslas', 'LAS', 'Molecular & Cellular Biology', 'bachelors', 'Molecular & Cellular Biology', 'on_campus', 48),
    ('uiuc-molecular-cellular-biology-data-science-bslas', 'LAS', 'Molecular and Cellular Biology + Data Science', 'bachelors', 'Molecular and Cellular Biology + Data Science', 'on_campus', 48),
    ('uiuc-neuroscience-bslas', 'LAS', 'Neuroscience', 'bachelors', 'Neuroscience', 'on_campus', 48),
    ('uiuc-philosophy-balas', 'LAS', 'Philosophy', 'bachelors', 'Philosophy', 'on_campus', 48),
    ('uiuc-political-science-balas', 'LAS', 'Political Science', 'bachelors', 'Political Science', 'on_campus', 48),
    ('uiuc-portuguese-balas', 'LAS', 'Portuguese', 'bachelors', 'Portuguese', 'on_campus', 48),
    ('uiuc-psychology-bslas', 'LAS', 'Psychology', 'bachelors', 'Psychology', 'on_campus', 48),
    ('uiuc-religion-balas', 'LAS', 'Religion', 'bachelors', 'Religion', 'on_campus', 48),
    ('uiuc-russian-east-european-eurasian-studies-balas', 'LAS', 'Russian & East European Studies', 'bachelors', 'Russian & East European Studies', 'on_campus', 48),
    ('uiuc-slavic-studies-balas', 'LAS', 'Slavic Studies', 'bachelors', 'Slavic Studies', 'on_campus', 48),
    ('uiuc-sociology-balas', 'LAS', 'Sociology', 'bachelors', 'Sociology', 'on_campus', 48),
    ('uiuc-spanish-balas', 'LAS', 'Spanish', 'bachelors', 'Spanish', 'on_campus', 48),
    ('uiuc-teaching-spanish-ba', 'LAS', 'Spanish Teaching', 'bachelors', 'Spanish Teaching', 'on_campus', 48),
    ('uiuc-statistics-bslas', 'LAS', 'Statistics', 'bachelors', 'Statistics', 'on_campus', 48),
    ('uiuc-statistics-computer-science-bslas', 'LAS', 'Statistics & Computer Science', 'bachelors', 'Statistics & Computer Science', 'on_campus', 48),
    ('uiuc-actuarial-science-ms', 'LAS', 'Actuarial Science', 'masters', 'Actuarial Science', 'on_campus', 24),
    ('uiuc-african-studies-ma', 'LAS', 'African Studies', 'masters', 'African Studies', 'on_campus', 24),
    ('uiuc-anthropology-ma', 'LAS', 'Anthropology', 'masters', 'Anthropology', 'on_campus', 24),
    ('uiuc-applied-mathematics-ms', 'LAS', 'Applied Mathematics', 'masters', 'Applied Mathematics', 'on_campus', 24),
    ('uiuc-art-history-ma', 'LAS', 'Art History', 'masters', 'Art History', 'on_campus', 24),
    ('uiuc-astronomy-ms', 'LAS', 'Astronomy', 'masters', 'Astronomy', 'on_campus', 24),
    ('uiuc-atmospheric-sciences-ms', 'LAS', 'Atmospheric Sciences', 'masters', 'Atmospheric Sciences', 'on_campus', 24),
    ('uiuc-biochemistry-ms', 'LAS', 'Biochemistry', 'masters', 'Biochemistry', 'on_campus', 24),
    ('uiuc-teaching-biological-science-ms', 'LAS', 'Biological Sciences, Teaching of', 'masters', 'Biological Sciences, Teaching of', 'on_campus', 24),
    ('uiuc-biology-ms', 'LAS', 'Biology', 'masters', 'Biology', 'on_campus', 24),
    ('uiuc-biophysics-quantitative-biology-ms', 'LAS', 'Biophysics & Quantitative Biology', 'masters', 'Biophysics & Quantitative Biology', 'on_campus', 24),
    ('uiuc-cell-developmental-biology-ms', 'LAS', 'Cell & Developmental Biology', 'masters', 'Cell & Developmental Biology', 'on_campus', 24),
    ('uiuc-chemistry-ms', 'LAS', 'Chemistry', 'masters', 'Chemistry', 'on_campus', 24),
    ('uiuc-teaching-chemistry-ms', 'LAS', 'Chemistry Teaching', 'masters', 'Chemistry Teaching', 'on_campus', 24),
    ('uiuc-classics-ma', 'LAS', 'Classics', 'masters', 'Classics', 'on_campus', 24),
    ('uiuc-communication-ma', 'LAS', 'Communication', 'masters', 'Communication', 'on_campus', 24),
    ('uiuc-comparative-literature-ma', 'LAS', 'Comparative Literature', 'masters', 'Comparative Literature', 'on_campus', 24),
    ('uiuc-creative-writing-mfa', 'LAS', 'Creative Writing', 'masters', 'Creative Writing', 'on_campus', 24),
    ('uiuc-cyberGIS-geospatial-data-science-ms', 'LAS', 'CyberGIS and Geospatial Data Science, MS', 'masters', 'CyberGIS and Geospatial Data Science, MS', 'on_campus', 24),
    ('uiuc-east-asian-languages-cultures-ma', 'LAS', 'East Asian Languages & Cultures', 'masters', 'East Asian Languages & Cultures', 'on_campus', 24),
    ('uiuc-ecology-evolution-conservation-biology-ms', 'LAS', 'Ecology & Conservation Biology', 'masters', 'Ecology & Conservation Biology', 'on_campus', 24),
    ('uiuc-economics-ms', 'LAS', 'Economics', 'masters', 'Economics', 'on_campus', 24),
    ('uiuc-english-ma', 'LAS', 'English', 'masters', 'English', 'on_campus', 24),
    ('uiuc-entomology-ms', 'LAS', 'Entomology', 'masters', 'Entomology', 'on_campus', 24),
    ('uiuc-environmental-geology-ms', 'LAS', 'Environmental Geology', 'masters', 'Environmental Geology', 'on_campus', 24),
    ('uiuc-european-union-studies-ma', 'LAS', 'European Union Studies', 'masters', 'European Union Studies', 'on_campus', 24),
    ('uiuc-evolution-ecology-behavior-ms', 'LAS', 'Evolution, Ecology, and Behavior', 'masters', 'Evolution, Ecology, and Behavior', 'on_campus', 24),
    ('uiuc-french-ma', 'LAS', 'French', 'masters', 'French', 'on_campus', 24),
    ('uiuc-geography-ma', 'LAS', 'Geography', 'masters', 'Geography', 'on_campus', 24),
    ('uiuc-geography-ms', 'LAS', 'Geography', 'masters', 'Geography', 'on_campus', 24),
    ('uiuc-geology-ms', 'LAS', 'Geology', 'masters', 'Geology', 'on_campus', 24),
    ('uiuc-german-ma', 'LAS', 'German', 'masters', 'German', 'on_campus', 24),
    ('uiuc-global-studies-ms', 'LAS', 'Global Studies', 'masters', 'Global Studies', 'on_campus', 24),
    ('uiuc-health-communication-ms', 'LAS', 'Health Communication', 'masters', 'Health Communication', 'on_campus', 24),
    ('uiuc-history-ma', 'LAS', 'History', 'masters', 'History', 'on_campus', 24),
    ('uiuc-integrative-biology-ms', 'LAS', 'Integrative Biology', 'masters', 'Integrative Biology', 'on_campus', 24),
    ('uiuc-italian-ma', 'LAS', 'Italian', 'masters', 'Italian', 'on_campus', 24),
    ('uiuc-latin-american-studies-ma', 'LAS', 'Latin American Studies', 'masters', 'Latin American Studies', 'on_campus', 24),
    ('uiuc-teaching-latin-ma', 'LAS', 'Latin, Teaching of', 'masters', 'Latin, Teaching of', 'on_campus', 24),
    ('uiuc-teaching-english-second-language-ma', 'LAS', 'Linguistics', 'masters', 'Linguistics', 'on_campus', 24),
    ('uiuc-linguistics-ma', 'LAS', 'Linguistics', 'masters', 'Linguistics', 'on_campus', 24),
    ('uiuc-mathematics-ms', 'LAS', 'Mathematics', 'masters', 'Mathematics', 'on_campus', 24),
    ('uiuc-teaching-mathematics-ms', 'LAS', 'Mathematics Teaching', 'masters', 'Mathematics Teaching', 'on_campus', 24),
    ('uiuc-microbiology-ms', 'LAS', 'Microbiology', 'masters', 'Microbiology', 'on_campus', 24),
    ('uiuc-molecular-cellular-biology-ms', 'LAS', 'Molecular & Cellular Biology', 'masters', 'Molecular & Cellular Biology', 'on_campus', 24),
    ('uiuc-molecular-integrative-physiology-ms', 'LAS', 'Molecular & Integrative Physiology', 'masters', 'Molecular & Integrative Physiology', 'on_campus', 24),
    ('uiuc-philosophy-ma', 'LAS', 'Philosophy', 'masters', 'Philosophy', 'on_campus', 24),
    ('uiuc-plant-biology-ms', 'LAS', 'Plant Biology', 'masters', 'Plant Biology', 'on_campus', 24),
    ('uiuc-policy-economics-ms', 'LAS', 'Policy Economics', 'masters', 'Policy Economics', 'on_campus', 24),
    ('uiuc-political-science-ma', 'LAS', 'Political Science', 'masters', 'Political Science', 'on_campus', 24),
    ('uiuc-portuguese-ma', 'LAS', 'Portuguese', 'masters', 'Portuguese', 'on_campus', 24),
    ('uiuc-predictive-analytics-risk-management-ms', 'LAS', 'Predictive Analytics and Risk Management', 'masters', 'Predictive Analytics and Risk Management', 'on_campus', 24),
    ('uiuc-psychological-science-ms', 'LAS', 'Psychology', 'masters', 'Psychology', 'on_campus', 24),
    ('uiuc-psychology-ms', 'LAS', 'Psychology', 'masters', 'Psychology', 'on_campus', 24),
    ('uiuc-religion-ma', 'LAS', 'Religion', 'masters', 'Religion', 'on_campus', 24),
    ('uiuc-russian-east-european-eurasian-studies-ma', 'LAS', 'Russian, East European & Eurasian Studies', 'masters', 'Russian, East European & Eurasian Studies', 'on_campus', 24),
    ('uiuc-slavic-languages-literatures-ma', 'LAS', 'Slavic Languages & Literatures', 'masters', 'Slavic Languages & Literatures', 'on_campus', 24),
    ('uiuc-sociology-ma', 'LAS', 'Sociology', 'masters', 'Sociology', 'on_campus', 24),
    ('uiuc-south-asian-middle-eastern-studies-ma', 'LAS', 'South Asian & Middle Eastern Studies', 'masters', 'South Asian & Middle Eastern Studies', 'on_campus', 24),
    ('uiuc-spanish-ma', 'LAS', 'Spanish', 'masters', 'Spanish', 'on_campus', 24),
    ('uiuc-statistics-ms', 'LAS', 'Statistics', 'masters', 'Statistics', 'on_campus', 24),
    ('uiuc-translation-interpreting-ma', 'LAS', 'Translation & Interpreting', 'masters', 'Translation & Interpreting', 'on_campus', 24),
    ('uiuc-weather-climate-risk-analytics-ms', 'LAS', 'Weather And Climate Risk & Analysis', 'masters', 'Weather And Climate Risk & Analysis', 'on_campus', 24),
    ('uiuc-anthropology-phd', 'LAS', 'Anthropology', 'phd', 'Anthropology', 'on_campus', 60),
    ('uiuc-art-history-phd', 'LAS', 'Art History', 'phd', 'Art History', 'on_campus', 60),
    ('uiuc-astronomy-phd', 'LAS', 'Astronomy', 'phd', 'Astronomy', 'on_campus', 60),
    ('uiuc-atmospheric-sciences-phd', 'LAS', 'Atmospheric Sciences', 'phd', 'Atmospheric Sciences', 'on_campus', 60),
    ('uiuc-biochemistry-phd', 'LAS', 'Biochemistry', 'phd', 'Biochemistry', 'on_campus', 60),
    ('uiuc-biology-phd', 'LAS', 'Biology', 'phd', 'Biology', 'on_campus', 60),
    ('uiuc-biophysics-quantitative-biology-phd', 'LAS', 'Biophysics & Quantitative Biology', 'phd', 'Biophysics & Quantitative Biology', 'on_campus', 60),
    ('uiuc-cell-developmental-biology-phd', 'LAS', 'Cell & Developmental Biology', 'phd', 'Cell & Developmental Biology', 'on_campus', 60),
    ('uiuc-chemistry-phd', 'LAS', 'Chemistry', 'phd', 'Chemistry', 'on_campus', 60),
    ('uiuc-classical-philology-phd', 'LAS', 'Classical Philology', 'phd', 'Classical Philology', 'on_campus', 60),
    ('uiuc-communication-phd', 'LAS', 'Communication', 'phd', 'Communication', 'on_campus', 60),
    ('uiuc-comparative-literature-phd', 'LAS', 'Comparative Literature', 'phd', 'Comparative Literature', 'on_campus', 60),
    ('uiuc-east-asian-languages-cultures-phd', 'LAS', 'East Asian Languages & Cultures', 'phd', 'East Asian Languages & Cultures', 'on_campus', 60),
    ('uiuc-ecology-evolution-conservation-biology-phd', 'LAS', 'Ecology, Evolution & Conservation Biology', 'phd', 'Ecology, Evolution & Conservation Biology', 'on_campus', 60),
    ('uiuc-economics-phd', 'LAS', 'Economics', 'phd', 'Economics', 'on_campus', 60),
    ('uiuc-english-phd', 'LAS', 'English', 'phd', 'English', 'on_campus', 60),
    ('uiuc-entomology-phd', 'LAS', 'Entomology', 'phd', 'Entomology', 'on_campus', 60),
    ('uiuc-evolution-ecology-behavior-phd', 'LAS', 'Evolution, Ecology, and Behavior', 'phd', 'Evolution, Ecology, and Behavior', 'on_campus', 60),
    ('uiuc-french-phd', 'LAS', 'French', 'phd', 'French', 'on_campus', 60),
    ('uiuc-geography-phd', 'LAS', 'Geography', 'phd', 'Geography', 'on_campus', 60),
    ('uiuc-geology-phd', 'LAS', 'Geology', 'phd', 'Geology', 'on_campus', 60),
    ('uiuc-german-phd', 'LAS', 'German', 'phd', 'German', 'on_campus', 60),
    ('uiuc-history-phd', 'LAS', 'History', 'phd', 'History', 'on_campus', 60),
    ('uiuc-italian-phd', 'LAS', 'Italian', 'phd', 'Italian', 'on_campus', 60),
    ('uiuc-linguistics-phd', 'LAS', 'Linguistics', 'phd', 'Linguistics', 'on_campus', 60),
    ('uiuc-mathematics-phd', 'LAS', 'Mathematics', 'phd', 'Mathematics', 'on_campus', 60),
    ('uiuc-microbiology-phd', 'LAS', 'Microbiology', 'phd', 'Microbiology', 'on_campus', 60),
    ('uiuc-molecular-integrative-physiology-phd', 'LAS', 'Molecular & Integrative Physiology', 'phd', 'Molecular & Integrative Physiology', 'on_campus', 60),
    ('uiuc-neuroscience-phd', 'LAS', 'Neuroscience', 'phd', 'Neuroscience', 'on_campus', 60),
    ('uiuc-philosophy-phd', 'LAS', 'Philosophy', 'phd', 'Philosophy', 'on_campus', 60),
    ('uiuc-plant-biology-phd', 'LAS', 'Plant Biology', 'phd', 'Plant Biology', 'on_campus', 60),
    ('uiuc-political-science-phd', 'LAS', 'Political Science', 'phd', 'Political Science', 'on_campus', 60),
    ('uiuc-portuguese-phd', 'LAS', 'Portuguese', 'phd', 'Portuguese', 'on_campus', 60),
    ('uiuc-psychology-phd', 'LAS', 'Psychology', 'phd', 'Psychology', 'on_campus', 60),
    ('uiuc-slavic-languages-literatures-phd', 'LAS', 'Slavic Languages & Literatures', 'phd', 'Slavic Languages & Literatures', 'on_campus', 60),
    ('uiuc-sociology-phd', 'LAS', 'Sociology', 'phd', 'Sociology', 'on_campus', 60),
    ('uiuc-spanish-phd', 'LAS', 'Spanish', 'phd', 'Spanish', 'on_campus', 60),
    ('uiuc-statistics-phd', 'LAS', 'Statistics', 'phd', 'Statistics', 'on_campus', 60),
    ('uiuc-master-laws-llm', 'LAW', 'Law', 'masters', 'Law', 'on_campus', 24),
    ('uiuc-master-studies-msl', 'LAW', 'Law', 'masters', 'Law', 'on_campus', 24),
    ('uiuc-science-law-jsd', 'LAW', 'Law', 'phd', 'Law', 'on_campus', 60),
    ('uiuc-law-jd', 'LAW', 'Law', 'professional', 'Juris Doctor', 'on_campus', 36),
    ('uiuc-human-resources-industrial-relations-mhrir', 'LER', 'Labor & Employment Relations', 'masters', 'Labor & Employment Relations', 'on_campus', 24),
    ('uiuc-human-resources-industrial-relations-phd', 'LER', 'Labor & Employment Relations', 'phd', 'Labor & Employment Relations', 'on_campus', 60),
    ('uiuc-advertising-bs', 'MDIA', 'Advertising', 'bachelors', 'Advertising', 'on_campus', 48),
    ('uiuc-computer-science-advertising-bs', 'MDIA', 'Computer Science + Advertising', 'bachelors', 'Computer Science + Advertising', 'on_campus', 48),
    ('uiuc-journalism-bs', 'MDIA', 'Journalism', 'bachelors', 'Journalism', 'on_campus', 48),
    ('uiuc-media-ba', 'MDIA', 'Media', 'bachelors', 'Media', 'on_campus', 48),
    ('uiuc-media-cinema-studies-bs', 'MDIA', 'Media & Cinema Studies', 'bachelors', 'Media & Cinema Studies', 'on_campus', 48),
    ('uiuc-sports-media-ba', 'MDIA', 'Sports Media', 'bachelors', 'Sports Media', 'on_campus', 48),
    ('uiuc-advertising-ms', 'MDIA', 'Advertising', 'masters', 'Advertising', 'on_campus', 24),
    ('uiuc-journalism-ms', 'MDIA', 'Journalism', 'masters', 'Journalism', 'on_campus', 24),
    ('uiuc-strategic-brand-communication-ms', 'MDIA', 'Strategic Brand Communication', 'masters', 'Strategic Brand Communication', 'on_campus', 24),
    ('uiuc-communications-media-phd', 'MDIA', 'Communications & Media', 'phd', 'Communications & Media', 'on_campus', 60),
    ('uiuc-social-work-bsw', 'SOCW', 'Social Work', 'bachelors', 'Social Work', 'on_campus', 48),
    ('uiuc-leadership-social-change', 'SOCW', 'Leadership & Social Change', 'masters', 'Leadership & Social Change', 'on_campus', 24),
    ('uiuc-social-work-msw', 'SOCW', 'Social Work', 'masters', 'Social Work', 'on_campus', 24),
    ('uiuc-social-work-phd', 'SOCW', 'Social Work', 'phd', 'Social Work', 'on_campus', 60),
    ('uiuc-applied-veterinary-sciences-mvs', 'VETMED', 'Applied Veterinary Sciences', 'masters', 'Applied Veterinary Sciences', 'on_campus', 24),
    ('uiuc-medical-science-comparative-biosciences-ms', 'VETMED', 'Comparative Biosciences', 'masters', 'Comparative Biosciences', 'on_campus', 24),
    ('uiuc-livestock-systems-health-mvs', 'VETMED', 'Livestock Systems Health', 'masters', 'Livestock Systems Health', 'on_campus', 24),
    ('uiuc-medical-science-pathobiology-ms', 'VETMED', 'Pathobiology', 'masters', 'Pathobiology', 'on_campus', 24),
    ('uiuc-clinical-medicine-ms', 'VETMED', 'Veterinary Medical Sciences - Veterinary Clinical Medicine', 'masters', 'Veterinary Medical Sciences - Veterinary Clinical Medicine', 'on_campus', 24),
    ('uiuc-medical-science-comparative-biosciences-phd', 'VETMED', 'Comparative Biosciences', 'phd', 'Comparative Biosciences', 'on_campus', 60),
    ('uiuc-medical-science-pathobiology-phd', 'VETMED', 'Pathobiology', 'phd', 'Pathobiology', 'on_campus', 60),
    ('uiuc-veterinary-medicine-dvm', 'VETMED', 'Veterinary Medicine', 'professional', 'Doctor of Veterinary Medicine', 'on_campus', 48),
]

_DEGREE_ROLE = {
    "phd": "a doctoral program",
    "masters": "a master's program",
    "professional": "a professional degree program",
    "bachelors": "an undergraduate major",
    "diploma": "a diploma program",
}
_DELIVERY_PHRASE = {"online": " It is delivered fully online.", "hybrid": " It is delivered in a hybrid format."}


def _description(name: str, dtype: str, school_key: str, fmt: str) -> str:
    role = _DEGREE_ROLE.get(dtype, "a graduate program")
    school_disp = SCHOOL_NAME[school_key]
    delivery = _DELIVERY_PHRASE.get(fmt, "")
    return f"{name} is {role} offered through UIUC's {school_disp}.{delivery}"


def _build_catalog() -> list[dict]:
    out = []
    for slug, sk, name, dtype, dept, fmt, dur in _CATALOG:
        out.append({
            "slug": slug, "school": SCHOOL_NAME[sk], "school_key": sk,
            "program_name": name, "degree_type": dtype, "department": dept,
            "delivery_format": fmt, "duration_months": dur,
            "description": _description(name, dtype, sk, fmt),
        })
    return out


PROGRAMS: list[dict] = _build_catalog()
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

_WEBSITE_OVERRIDE: dict[str, str] = {
    'uiuc-computer-science-bs': 'https://siebelschool.illinois.edu/academics/undergraduate/degree-program-options/bs-computer-science',
    'uiuc-computer-science-online-mcs': 'https://siebelschool.illinois.edu/academics/graduate/professional-mcs/online-master-computer-science',
    'uiuc-business-administration-online-mba': 'https://giesbusiness.illinois.edu/imba',
    'uiuc-accountancy-imsa-ms': 'https://giesbusiness.illinois.edu/imsa',
    'uiuc-management-imsm-ms': 'https://giesbusiness.illinois.edu/imsm',
    'uiuc-accountancy-bs': 'https://giesbusiness.illinois.edu/programs/undergraduate/accountancy',
    'uiuc-law-jd': 'https://law.illinois.edu/academics/degrees/jd/',
    'uiuc-medicine-md': 'https://medicine.illinois.edu/',
    'uiuc-veterinary-medicine-dvm': 'https://vetmed.illinois.edu/academic-programs/professional-dvm-program/',
    'uiuc-library-information-science-ms': 'https://ischool.illinois.edu/degrees-programs/graduate-degrees/ms-information-sciences',
}
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    'uiuc-computer-science-bs': ['Siebel School of Computing', 'computer science', 'CS'],
    'uiuc-computer-science-online-mcs': ['online Master of Computer Science', 'MCS', 'MCS-DS', 'Coursera'],
    'uiuc-business-administration-online-mba': ['Gies iMBA', 'online MBA', 'iMBA'],
    'uiuc-accountancy-imsa-ms': ['Gies iMSA', 'online accountancy', 'iMSA'],
    'uiuc-management-imsm-ms': ['Gies iMSM', 'online management', 'iMSM'],
    'uiuc-accountancy-bs': ['Gies accountancy', 'accountancy', 'accounting'],
    'uiuc-law-jd': ['University of Illinois College of Law', 'J.D.', 'law'],
    'uiuc-medicine-md': ['Carle Illinois College of Medicine', 'M.D.', 'medicine'],
    'uiuc-veterinary-medicine-dvm': ['College of Veterinary Medicine', 'DVM', 'veterinary'],
    'uiuc-civil-engineering-bs': ['civil engineering', 'Grainger Engineering'],
    'uiuc-library-information-science-ms': ['iSchool', 'information sciences', 'library and information science'],
}


def _website_for(spec: dict) -> str:
    return _WEBSITE_OVERRIDE.get(spec["slug"], SCHOOL_WEBSITE[spec["school"]])


# == Costs ==
_UNDERGRAD_COA = 33642
_AVG_NET_PRICE = 14355
_COST_SRC = "U.S. Dept. of Education — College Scorecard (UIUC, UNITID 145637)"
_COST_SRC_URL = "https://collegescorecard.ed.gov/school/?145637-University-of-Illinois-Urbana-Champaign"


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
        "source": _COST_SRC, "source_url": _COST_SRC_URL, "year": "2023-24",
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
        {"name": "SAT/ACT scores", "required": False,
         "note": "UIUC is test-optional; the middle 50% of enrolled students who submitted scored SAT 1310-1520 / ACT 30-34 (College Scorecard / CDS 2024-25)."},
    ],
    "deadlines": [
        {"round": "Early Action", "date": "November 1"},
        {"round": "Regular Decision", "date": "January 5"},
    ],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS", "Duolingo English Test"], "required": True,
                    "note": "Required for applicants whose native language is not English."},
        "visa": _INTL_VISA,
        "sources": [{"label": "UIUC Undergraduate Admissions", "url": "https://www.admissions.illinois.edu/"}],
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
        {"name": "Letters of recommendation", "required": True,
         "note": "Most UIUC graduate programs require three letters; check the program's page."},
        {"name": "GRE/GMAT scores", "required": False,
         "note": "Test requirements vary by program; many UIUC graduate programs are test-optional or do not require the GRE/GMAT."},
    ],
    "deadlines": [{"round": "Fall admission", "date": "Deadlines vary by program (typically December–January)"}],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS"], "required": True,
                    "note": "Required for applicants whose native language is not English."},
        "visa": _INTL_VISA,
        "sources": [{"label": "UIUC Graduate College — admissions", "url": "https://grad.illinois.edu/admissions"}],
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
        "directory_url": "https://siebelschool.illinois.edu/about/people/all-faculty"
    },
    "uiuc-business-administration-online-mba": {
        "lead": "The Gies iMBA is taught by University of Illinois Gies College of Business faculty, delivered online with Coursera.",
        "directory_url": "https://giesbusiness.illinois.edu/about/faculty-directory"
    },
    "uiuc-law-jd": {
        "lead": "The J.D. is taught by the University of Illinois College of Law full-time faculty.",
        "directory_url": "https://law.illinois.edu/faculty-research/faculty-profiles/"
    },
    "uiuc-medicine-md": {
        "lead": "The M.D. is taught by Carle Illinois College of Medicine faculty across engineering, the basic sciences, and Carle Health clinical partners.",
        "directory_url": "https://medicine.illinois.edu/"
    }
}

_REVIEWS_BY_SLUG: dict[str, dict] = {
    "uiuc-computer-science-bs": {
        "summary": "UIUC computer science is consistently ranked among the very best in the United States — #7 for the undergraduate program and #5 for the graduate program in U.S. News 2026 — with deep strength in systems, architecture, programming languages, AI, and data systems and a legacy that includes early supercomputing (NCSA) and the Mosaic web browser. Reviewers highlight world-class faculty, strong big-tech and quant recruiting, and the distinctive 'CS + X' blended-degree options, while noting that admission is extremely competitive and popular courses are large.",
        "themes": [
            {
                "label": "Top-5/7 CS reputation",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC CS #7 undergraduate and #5 graduate (2025-2026), with renowned faculty and the Siebel School of Computing and Data Science."
            },
            {
                "label": "Industry and research placement",
                "sentiment": "positive",
                "detail": "Graduates recruit heavily into major technology firms; undergraduates can join research across AI, systems, and HCI."
            },
            {
                "label": "'CS + X' blended degrees",
                "sentiment": "positive",
                "detail": "UIUC pioneered 'CS + X' majors (with anthropology, economics, linguistics, music, and more) that pair computing with another discipline."
            },
            {
                "label": "Very competitive admission",
                "sentiment": "caution",
                "detail": "Direct admission to CS is highly selective and core courses are large; reviewers advise engaging early with research and office hours."
            }
        ],
        "sources": [
            {
                "label": "Siebel School of Computing and Data Science — B.S. in Computer Science",
                "url": "https://siebelschool.illinois.edu/academics/undergraduate"
            },
            {
                "label": "UIUC rankings (U.S. News CS #7 ug / #5 grad)",
                "url": "https://illinois.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "uiuc-computer-science-online-mcs": {
        "summary": "UIUC's online Master of Computer Science (MCS, with an optional Data Science track, MCS-DS), delivered with Coursera, is one of the most popular and affordable top-ranked online CS master's degrees in the country. It is a 32-credit, eight-course professional degree taught by Grainger Engineering faculty; graduates earn the same MCS degree and diploma as on-campus students, with no notation of online study. Reviewers praise the value, flexibility, and rigor, while noting it is fully online and self-directed.",
        "themes": [
            {
                "label": "Same Illinois degree, online",
                "sentiment": "positive",
                "detail": "Graduates earn the same Master of Computer Science degree and diploma as on-campus students; the diploma and transcript do not note online study."
            },
            {
                "label": "Affordable and flexible",
                "sentiment": "positive",
                "detail": "Eight credit-bearing courses can be completed at the student's pace (about one to five years), pay-as-you-go, with a data-science track requiring no extra coursework."
            },
            {
                "label": "Rigorous, faculty-assessed",
                "sentiment": "positive",
                "detail": "Lectures run through Coursera, but students are advised and assessed by Illinois faculty and TAs on degree-credit assignments, projects, and exams."
            },
            {
                "label": "Demanding and self-directed",
                "sentiment": "caution",
                "detail": "The workload is rigorous and the experience is fully online, so it best suits motivated working professionals rather than those seeking a campus experience."
            }
        ],
        "sources": [
            {
                "label": "Online Master of Computer Science — Siebel School (Illinois)",
                "url": "https://siebelschool.illinois.edu/academics/graduate/professional-mcs/online-master-computer-science"
            },
            {
                "label": "Master of Computer Science (Illinois) — Coursera",
                "url": "https://www.coursera.org/degrees/master-of-computer-science-illinois"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "uiuc-computer-engineering-bs": {
        "summary": "UIUC computer engineering, in the Department of Electrical & Computer Engineering, is ranked #5 in the United States by U.S. News and is known for strength in computer architecture, embedded systems, VLSI, and machine learning hardware. Reviewers cite world-class faculty, the Coordinated Science Laboratory and Holonyak nanotechnology lab, and strong placement, while noting the program's rigor.",
        "themes": [
            {
                "label": "Top-5 computer engineering",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC computer engineering #5 nationally, with research anchored by the Coordinated Science Laboratory."
            },
            {
                "label": "Hardware-software breadth",
                "sentiment": "positive",
                "detail": "Strength spans computer architecture, embedded and VLSI systems, networking, and ML hardware."
            },
            {
                "label": "Strong placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into semiconductor, systems, and technology firms."
            },
            {
                "label": "Rigorous workload",
                "sentiment": "caution",
                "detail": "The ECE curriculum is demanding; reviewers advise strong math and systems preparation."
            }
        ],
        "sources": [
            {
                "label": "UIUC Electrical & Computer Engineering",
                "url": "https://ece.illinois.edu/"
            },
            {
                "label": "UIUC rankings (computer engineering #5)",
                "url": "https://illinois.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "uiuc-electrical-engineering-bs": {
        "summary": "UIUC electrical engineering (Department of Electrical & Computer Engineering) is ranked #5 in the U.S. by U.S. News, with a storied history in solid-state electronics (the visible LED was invented here) and strength in photonics, power, communications, and signal processing. Reviewers praise faculty, research opportunities, and recruiting, while noting the heavy course load.",
        "themes": [
            {
                "label": "Top-5 electrical engineering",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC EE #5 nationally; the department's faculty include pioneers of modern microelectronics and photonics."
            },
            {
                "label": "Research opportunities",
                "sentiment": "positive",
                "detail": "Students engage with the Coordinated Science Laboratory, Holonyak Micro & Nanotechnology Lab, and power/energy research."
            },
            {
                "label": "Strong industry recruiting",
                "sentiment": "positive",
                "detail": "Graduates place into semiconductor, energy, communications, and technology employers."
            },
            {
                "label": "Demanding curriculum",
                "sentiment": "caution",
                "detail": "Reviewers note the workload is intense and the program is highly selective."
            }
        ],
        "sources": [
            {
                "label": "UIUC Electrical & Computer Engineering",
                "url": "https://ece.illinois.edu/"
            },
            {
                "label": "UIUC rankings (electrical engineering #5)",
                "url": "https://illinois.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "uiuc-mechanical-engineering-bs": {
        "summary": "UIUC mechanical engineering (Department of Mechanical Science & Engineering) is ranked #4 for the undergraduate program by U.S. News, with strengths in thermal-fluid sciences, dynamics and controls, robotics, and energy. Reviewers highlight hands-on design experience and broad placement across energy, aerospace, automotive, and manufacturing, while noting the rigor.",
        "themes": [
            {
                "label": "Top-5 mechanical engineering",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC mechanical engineering #4 undergraduate (#6 graduate), with strong faculty and labs."
            },
            {
                "label": "Hands-on design",
                "sentiment": "positive",
                "detail": "Project- and capstone-based courses give students practical engineering design experience."
            },
            {
                "label": "Broad placement",
                "sentiment": "positive",
                "detail": "Graduates recruit across energy, aerospace, automotive, manufacturing, and technology employers."
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "The mechanical engineering curriculum is demanding; reviewers advise strong math and physics preparation."
            }
        ],
        "sources": [
            {
                "label": "UIUC Mechanical Science & Engineering",
                "url": "https://mechse.illinois.edu/"
            },
            {
                "label": "Grainger facts & rankings (mechanical #4 ug)",
                "url": "https://grainger.illinois.edu/about/facts-and-rankings"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "uiuc-aerospace-engineering-bs": {
        "summary": "UIUC aerospace engineering is ranked #7 in the U.S. by U.S. News, with strengths in aerodynamics, propulsion, structures, and autonomy, and research ties to NASA and industry. Reviewers cite strong faculty and recruiting into aerospace and defense, while noting the field's cyclicality and rigor.",
        "themes": [
            {
                "label": "Top-10 aerospace engineering",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC aerospace engineering #7 nationally."
            },
            {
                "label": "Research breadth",
                "sentiment": "positive",
                "detail": "Strength spans aerodynamics, propulsion, structures, controls, and autonomy."
            },
            {
                "label": "Aerospace and defense placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into aerospace, defense, and space employers, as well as adjacent technology fields."
            },
            {
                "label": "Rigorous and specialized",
                "sentiment": "caution",
                "detail": "The curriculum is demanding and hiring can track aerospace-industry cycles."
            }
        ],
        "sources": [
            {
                "label": "UIUC Department of Aerospace Engineering",
                "url": "https://aerospace.illinois.edu/"
            },
            {
                "label": "Grainger facts & rankings (aerospace #7)",
                "url": "https://grainger.illinois.edu/about/facts-and-rankings"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "uiuc-civil-engineering-bs": {
        "summary": "UIUC civil engineering is one of the best in the world — ranked #1 in the U.S. for the graduate program and #4 for the undergraduate program by U.S. News — with leading work in structures, transportation, environmental and water resources, and construction. Reviewers praise faculty, research facilities, and placement, noting the rigor and breadth of the program.",
        "themes": [
            {
                "label": "#1 graduate civil engineering",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC civil engineering #1 graduate and #4 undergraduate (2025-2026)."
            },
            {
                "label": "Comprehensive specialties",
                "sentiment": "positive",
                "detail": "Strength spans structures, transportation, geotechnical, environmental/water resources, and construction engineering & management."
            },
            {
                "label": "Strong placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into engineering firms, public agencies, and construction and infrastructure employers."
            },
            {
                "label": "Rigorous and broad",
                "sentiment": "caution",
                "detail": "The curriculum is demanding and spans many subfields; reviewers advise focusing a specialization."
            }
        ],
        "sources": [
            {
                "label": "UIUC Civil & Environmental Engineering",
                "url": "https://cee.illinois.edu/"
            },
            {
                "label": "UIUC rankings (civil engineering #1 grad / #4 ug)",
                "url": "https://illinois.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "uiuc-materials-science-engineering-bs": {
        "summary": "UIUC materials science & engineering is ranked among the nation's best (#5 undergraduate, #3 graduate by U.S. News), with strengths in electronic and photonic materials, nanomaterials, and computational materials, supported by the Materials Research Laboratory. Reviewers cite strong research and placement, while noting the program's rigor.",
        "themes": [
            {
                "label": "Top-5 materials science",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC MatSE #5 undergraduate and #3 graduate, with the Materials Research Laboratory a major asset."
            },
            {
                "label": "Research strength",
                "sentiment": "positive",
                "detail": "Strength spans electronic/photonic materials, nanomaterials, polymers, and computational materials."
            },
            {
                "label": "Strong placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into semiconductor, energy, and advanced-manufacturing employers and graduate study."
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "The curriculum is demanding with heavy chemistry, physics, and math foundations."
            }
        ],
        "sources": [
            {
                "label": "UIUC Materials Science & Engineering",
                "url": "https://matse.illinois.edu/"
            },
            {
                "label": "UIUC rankings (materials #5 ug / #3 grad)",
                "url": "https://illinois.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "uiuc-chemical-engineering-bs": {
        "summary": "UIUC chemical & biomolecular engineering (in the School of Chemical Sciences) is ranked #8 for the undergraduate program by U.S. News, with strengths in catalysis, energy, biomolecular engineering, and materials. Reviewers praise faculty and recruiting into energy, materials, and pharma, while noting the demanding curriculum.",
        "themes": [
            {
                "label": "Top-10 chemical engineering",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC chemical engineering #8 undergraduate, with strong research in catalysis, energy, and biomolecular engineering."
            },
            {
                "label": "Research and labs",
                "sentiment": "positive",
                "detail": "Students access strong laboratories within the School of Chemical Sciences."
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into energy, materials, chemicals, and pharmaceutical employers."
            },
            {
                "label": "Demanding curriculum",
                "sentiment": "caution",
                "detail": "The chemical engineering curriculum is rigorous and quantitatively intensive."
            }
        ],
        "sources": [
            {
                "label": "UIUC Chemical & Biomolecular Engineering",
                "url": "https://chbe.illinois.edu/"
            },
            {
                "label": "Grainger facts & rankings (chemical #8 ug)",
                "url": "https://grainger.illinois.edu/about/facts-and-rankings"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "uiuc-bioengineering-bs": {
        "summary": "UIUC bioengineering, ranked #14 for the undergraduate program by U.S. News, combines engineering with the life sciences and benefits from ties to the Carle Illinois College of Medicine and campus health-technology research. Reviewers highlight interdisciplinary opportunities and growth, while noting it is a younger, smaller department than UIUC's largest engineering programs.",
        "themes": [
            {
                "label": "Ranked bioengineering",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC bioengineering #14 nationally; the field is growing alongside the Carle Illinois medical partnership."
            },
            {
                "label": "Interdisciplinary opportunities",
                "sentiment": "positive",
                "detail": "Students work at the intersection of engineering, biology, and medicine, including imaging, biomechanics, and computational biology."
            },
            {
                "label": "Medical-school ties",
                "sentiment": "positive",
                "detail": "Proximity to Carle Illinois and the Beckman Institute supports translational research."
            },
            {
                "label": "Younger, smaller program",
                "sentiment": "caution",
                "detail": "Bioengineering is newer and smaller than UIUC's flagship engineering departments."
            }
        ],
        "sources": [
            {
                "label": "UIUC Department of Bioengineering",
                "url": "https://bioengineering.illinois.edu/"
            },
            {
                "label": "Grainger facts & rankings (bioengineering #14)",
                "url": "https://grainger.illinois.edu/about/facts-and-rankings"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "uiuc-accountancy-bs": {
        "summary": "The Gies Department of Accountancy is consistently ranked the #1 undergraduate accounting program in the United States by U.S. News (and #6 at the graduate level). Reviewers cite outstanding Big Four and corporate placement, very high CPA exam performance, and strong faculty, along with the option to continue into the Master of Accountancy. Some note the program's size and competitiveness.",
        "themes": [
            {
                "label": "#1 undergraduate accounting",
                "sentiment": "positive",
                "detail": "U.S. News ranks UIUC accountancy #1 at the undergraduate level (and #6 graduate)."
            },
            {
                "label": "Big Four placement",
                "sentiment": "positive",
                "detail": "Graduates place strongly into Big Four and corporate accounting and advisory roles."
            },
            {
                "label": "Pathway to the master's",
                "sentiment": "positive",
                "detail": "Students can continue into the Gies Master of Accountancy and the online iMSA to meet CPA requirements."
            },
            {
                "label": "Large and competitive",
                "sentiment": "caution",
                "detail": "The program is large and admission and recruiting are competitive."
            }
        ],
        "sources": [
            {
                "label": "Gies College of Business — Accountancy",
                "url": "https://giesbusiness.illinois.edu/programs/undergraduate/accountancy"
            },
            {
                "label": "UIUC rankings (accountancy #1 ug / #6 grad)",
                "url": "https://illinois.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "uiuc-finance-bs": {
        "summary": "The Gies undergraduate finance program is a strong, well-recruited business major at a top public business school, with offerings in corporate finance, investments, and financial markets and a data-science blended option. Reviewers cite solid placement into banking, consulting, and corporate finance and strong value, while noting that the most competitive finance roles favor early networking.",
        "themes": [
            {
                "label": "Top public business school",
                "sentiment": "positive",
                "detail": "Gies is a respected AACSB-accredited business school with strong finance offerings and recruiting."
            },
            {
                "label": "Applied and data-driven",
                "sentiment": "positive",
                "detail": "The finance curriculum includes investments, corporate finance, and a Finance + Data Science blended degree."
            },
            {
                "label": "Solid placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into banking, consulting, corporate finance, and analytics roles."
            },
            {
                "label": "Networking matters",
                "sentiment": "caution",
                "detail": "As elsewhere, the most competitive finance roles reward early internships and networking."
            }
        ],
        "sources": [
            {
                "label": "Gies College of Business — Finance",
                "url": "https://giesbusiness.illinois.edu/programs/undergraduate/finance"
            },
            {
                "label": "UIUC rankings (Gies business)",
                "url": "https://illinois.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "uiuc-business-administration-online-mba": {
        "summary": "The Gies iMBA is a pioneering, highly affordable online MBA (total tuition about $27,288) delivered with Coursera and taught by University of Illinois faculty. Now a decade old, it is AACSB-accredited and awards the same MBA as an on-campus program (the diploma does not say 'online'). Reviewers praise the value, flexibility, and engaged global community, while noting that, like most online MBAs, it relies on self-direction and offers limited in-person networking.",
        "themes": [
            {
                "label": "Exceptional value",
                "sentiment": "positive",
                "detail": "Total tuition of about $27,288 for an AACSB-accredited MBA from a top public university is a standout value; GMAT/GRE are not required."
            },
            {
                "label": "Flexible, pay-as-you-go",
                "sentiment": "positive",
                "detail": "Students complete the degree in 24-60 months at their own pace, starting in multiple terms and paying per course."
            },
            {
                "label": "Engaged global community",
                "sentiment": "positive",
                "detail": "Reviewers describe an active global cohort and real-time application of coursework to their jobs."
            },
            {
                "label": "Online by design",
                "sentiment": "mixed",
                "detail": "The program is fully online with no on-campus commitment, with engagement built into the courses; some students still miss in-person networking."
            },
            {
                "label": "Self-directed",
                "sentiment": "caution",
                "detail": "As with most online MBAs, success depends on motivation and time management."
            }
        ],
        "sources": [
            {
                "label": "Gies College of Business — iMBA",
                "url": "https://giesbusiness.illinois.edu/imba"
            },
            {
                "label": "iMBA (Online MBA) overview — Gies",
                "url": "https://giesonline.illinois.edu/explore-programs/online-mba"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "uiuc-library-information-science-ms": {
        "summary": "The iSchool's Master of Science in Information Sciences is consistently ranked the #1 library and information science program in the United States by U.S. News. Reviewers praise its breadth across data, information organization, and user-centered design, flexible on-campus and online delivery, and strong placement into libraries, archives, data, and UX roles, while noting the field's salary range varies by sector.",
        "themes": [
            {
                "label": "#1-ranked information sciences",
                "sentiment": "positive",
                "detail": "U.S. News consistently ranks the UIUC iSchool's library/information science master's #1 nationally."
            },
            {
                "label": "Broad, flexible curriculum",
                "sentiment": "positive",
                "detail": "Students can focus on data and analytics, information organization, UX, youth services, or archives, on campus or online."
            },
            {
                "label": "Strong placement",
                "sentiment": "positive",
                "detail": "Graduates place into academic and public libraries, archives, data curation, and information/UX roles across sectors."
            },
            {
                "label": "Sector-dependent pay",
                "sentiment": "caution",
                "detail": "Salaries vary widely by sector (tech/data vs. public libraries); reviewers advise targeting coursework to career goals."
            }
        ],
        "sources": [
            {
                "label": "UIUC iSchool — MS in Information Sciences",
                "url": "https://ischool.illinois.edu/degrees-programs/graduate-degrees/ms-information-sciences"
            },
            {
                "label": "UIUC rankings (iSchool #1)",
                "url": "https://illinois.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "uiuc-law-jd": {
        "summary": "The University of Illinois College of Law is a well-regarded public law school (a U.S. News top-50 program) known for strong value, a collegial culture, and solid Illinois and national placement, particularly into the Chicago legal market. First-time bar passage for the Class of 2024 was 93.56% (well above the ABA weighted average of about 79%), though the 2023 cohort's rate dipped below average. Reviewers cite affordability and outcomes relative to private peers, while noting the demands of law school and year-to-year bar variability.",
        "themes": [
            {
                "label": "Strong public-law value",
                "sentiment": "positive",
                "detail": "A U.S. News top-50 law school offering top-tier legal education at lower public tuition than comparable private peers."
            },
            {
                "label": "Chicago and Illinois placement",
                "sentiment": "positive",
                "detail": "Graduates place well into the Chicago legal market, Illinois firms and government, and national markets."
            },
            {
                "label": "High recent bar passage",
                "sentiment": "mixed",
                "detail": "First-time bar passage was 93.56% for the Class of 2024 (vs. an ABA weighted average near 79%), though the 2023 cohort dipped to 72.48%."
            },
            {
                "label": "Rigorous and competitive",
                "sentiment": "caution",
                "detail": "As at peer law schools, the workload is intense and admission is selective."
            }
        ],
        "sources": [
            {
                "label": "University of Illinois College of Law — ABA Required Disclosures",
                "url": "https://law.illinois.edu/about/college-profile/aba-disclosures/"
            },
            {
                "label": "UIUC College of Law — ABA Bar Passage Report",
                "url": "https://law.illinois.edu/wp-content/uploads/2024/02/ABA-Bar-Passage-Report.pdf"
            },
            {
                "label": "U.S. News — University of Illinois College of Law",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/university-of-illinois-urbana-champaign-03077"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "uiuc-medicine-md": {
        "summary": "The Carle Illinois College of Medicine, which enrolled its first M.D. class in 2018, is the nation's first engineering-based college of medicine — a partnership between UIUC and Carle Health that weaves engineering, data, and innovation through the entire M.D. curriculum. Reviewers praise the distinctive curriculum, small class size, and innovation focus, while noting it is a young program still building its research and residency-match track record.",
        "themes": [
            {
                "label": "Engineering-based M.D.",
                "sentiment": "positive",
                "detail": "Carle Illinois is the first U.S. medical school built on an engineering and innovation foundation, integrating it throughout the curriculum."
            },
            {
                "label": "Clinical partnership",
                "sentiment": "positive",
                "detail": "The partnership with Carle Health gives students early, integrated clinical training in a working health system."
            },
            {
                "label": "Small, innovative cohort",
                "sentiment": "positive",
                "detail": "A small class size supports close mentorship and a project- and innovation-oriented experience."
            },
            {
                "label": "Young program",
                "sentiment": "caution",
                "detail": "Founded in 2015 with its first class in 2018, Carle Illinois has a shorter track record than long-established medical schools."
            }
        ],
        "sources": [
            {
                "label": "Carle Illinois College of Medicine",
                "url": "https://medicine.illinois.edu/"
            },
            {
                "label": "Carle Illinois — Dean Mark Cohen",
                "url": "https://medicine.illinois.edu/about/dean-cohen"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "uiuc-veterinary-medicine-dvm": {
        "summary": "The University of Illinois College of Veterinary Medicine offers a well-regarded Doctor of Veterinary Medicine through a teaching hospital and a broad clinical and research enterprise. Reviewers cite strong clinical training, a large caseload, and faculty expertise across companion, food, and zoo/wildlife animal medicine, while noting that veterinary education is costly and admission is highly competitive.",
        "themes": [
            {
                "label": "Comprehensive clinical training",
                "sentiment": "positive",
                "detail": "Students train through the Veterinary Teaching Hospital with a broad caseload across species."
            },
            {
                "label": "Research and specialties",
                "sentiment": "positive",
                "detail": "Faculty span comparative biosciences, pathobiology, and clinical medicine, with strong specialty and research programs."
            },
            {
                "label": "Public-university access",
                "sentiment": "positive",
                "detail": "As a public veterinary college, it offers strong value, especially for Illinois residents."
            },
            {
                "label": "Costly and competitive",
                "sentiment": "caution",
                "detail": "Veterinary education is expensive and DVM admission is highly competitive nationwide."
            }
        ],
        "sources": [
            {
                "label": "University of Illinois College of Veterinary Medicine — DVM program",
                "url": "https://vetmed.illinois.edu/academic-programs/professional-dvm-program/"
            },
            {
                "label": "U.S. News — best veterinary schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-veterinary-schools"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "uiuc-statistics-bslas": {
        "summary": "UIUC's statistics program (Department of Statistics, College of LAS) is a large, well-regarded program that has grown rapidly with demand for data skills, offering pathways in statistics, actuarial science, and statistics & computer science. Reviewers cite strong faculty, applied and computational coursework, and excellent placement into data, analytics, and actuarial roles.",
        "themes": [
            {
                "label": "Strong, in-demand program",
                "sentiment": "positive",
                "detail": "Statistics at UIUC has grown with data-science demand and offers blended Statistics & Computer Science and actuarial pathways."
            },
            {
                "label": "Applied and computational",
                "sentiment": "positive",
                "detail": "Coursework emphasizes statistical computing, probability, and applied data analysis."
            },
            {
                "label": "Excellent placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into data-science, analytics, actuarial, and quantitative roles."
            },
            {
                "label": "Large courses",
                "sentiment": "caution",
                "detail": "Popular statistics and data courses can be large; reviewers advise engaging with office hours and projects."
            }
        ],
        "sources": [
            {
                "label": "UIUC Department of Statistics",
                "url": "https://stat.illinois.edu/"
            },
            {
                "label": "UIUC rankings",
                "url": "https://illinois.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "uiuc-economics-balas": {
        "summary": "Economics at UIUC (College of LAS) is a strong, research-active program offering a flexible B.A. plus quantitative options such as econometrics & quantitative economics and computer science + economics. Reviewers value the analytical training and breadth, and placement into business, finance, policy, and graduate study, while noting that the most quantitative careers reward additional math and computing coursework.",
        "themes": [
            {
                "label": "Research-active department",
                "sentiment": "positive",
                "detail": "UIUC economics is a well-regarded program with strong faculty and broad course offerings."
            },
            {
                "label": "Quantitative options",
                "sentiment": "positive",
                "detail": "Students can pursue econometrics & quantitative economics or the computer science + economics blended degree."
            },
            {
                "label": "Broad placement",
                "sentiment": "positive",
                "detail": "Graduates enter business, finance, consulting, public policy, and graduate/professional study."
            },
            {
                "label": "Quant skills pay off",
                "sentiment": "caution",
                "detail": "Reviewers advise adding math, statistics, and computing coursework for the most quantitative careers."
            }
        ],
        "sources": [
            {
                "label": "UIUC Department of Economics",
                "url": "https://economics.illinois.edu/"
            },
            {
                "label": "UIUC rankings",
                "url": "https://illinois.edu/about/rankings/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department, employment and bar-passage reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    }
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
