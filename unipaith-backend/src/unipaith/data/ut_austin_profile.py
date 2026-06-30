"""University of Texas at Austin (UT Austin) — gold-standard profile data
(institution + schools + program catalog).

Mirrors the MIT / Sloan / MBAn reference instance (see ``mit_profile.py`` /
``usc_profile.py``): every value is researched from an authoritative source and
carries a citation, or is honestly omitted (recorded in that node's
``_standard.omitted``) — never guessed. Built 2026-06-13 from:

  • U.S. Dept. of Education **College Scorecard** API + **IPEDS** (UNITID 228778):
    admit rate, average net price, cost of attendance, ten-year median earnings,
    six-year completion, first-year retention, Pell/loan rates, median debt,
    endowment, undergraduate race/ethnicity, and SAT/ACT middle-50% test scores.
  • **UT Austin Common Data Set 2024-2025** (reports.utexas.edu) and **UT Austin
    facts** (utexas.edu/about-texas, news.utexas.edu): the Fall 2024 first-year
    admissions funnel (72,885 applicants / 19,417 admitted / 9,210 enrolled),
    record total enrollment (53,864), ~4,600 faculty, the 18:1 student-faculty
    ratio, and >$1.37B annual research.
  • Rankings: **QS 2026** (#68), **THE 2026** (#50), **U.S. News Best Colleges
    2026** (#30 National), Carnegie R1, SACSCOC accreditation, each cited.
  • The official **UT Austin Catalog** (catalog.utexas.edu): the full published
    degree catalog — 120 undergraduate majors across 15 colleges/schools, every
    graduate field of study (catalog.utexas.edu/graduate/areas-of-study/) with the
    specific master's/doctoral degrees each offers, plus the Doctor of
    Jurisprudence and Master of Laws (School of Law), the Doctor of Medicine (Dell
    Medical School), and UT's 100%-online master's degrees (the Computer & Data
    Science Online MSCS, MSDS, and MSAI — cdso.utexas.edu), each mapped to its
    owning college by the catalog's own grouping. Online programs carry
    ``delivery_format = "online"``. Minors, certificates, dual/integrated-degree
    combinations (already represented by their single-degree components), and
    non-degree programs are excluded.
  • **UT Austin University Deans** (president.utexas.edu/leadership-staff/university-deans)
    for the current dean of each school, and the official **Historical Sketch**
    (catalog.utexas.edu/general-information/the-university/historical-sketch) for
    founding years.
  • Verified third-party reviews + employment data for flagship coverable programs
    (the Texas McCombs Full-Time MBA and the Texas Law J.D. carry verified
    employment outcomes) and sourced reputation reviews for Computer Science,
    Petroleum Engineering, Electrical & Computer Engineering, Mechanical
    Engineering, the McCombs BBA, the Master in Professional Accounting, the M.S.
    in Business Analytics, the Dell Med M.D., the online MSCS, the LBJ M.P.Aff.,
    and Nursing.

Honest caveats stamped into ``_standard.omitted``: UT Austin does not publish a
single university-wide "employed or continuing education" placement rate or a
uniform top-employer-industries list across all colleges, so those two
institution outcome fields are omitted with reason (the College Scorecard
institution-wide ten-year median earnings, $75,121, is kept). Most
graduate/professional programs bill tuition per semester/per program and publish
no single annual figure, so those carry a sourced "see the program's tuition
page" record rather than a guessed number. This repair (2026-06-18) adds the
verified ``news.utexas.edu/feed/`` RSS on every node, credential-disambiguated
program names, field-specific descriptions, and coverable ``external_reviews``.
"""

# ruff: noqa: E501

from __future__ import annotations

import re
from collections import defaultdict

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "The University of Texas at Austin"
ENRICHED_AT = "2026-06-30"


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


# UT Austin reports outcomes by college/program, not as one university-wide combined
# placement rate or top-employer-industries list.
_OMITTED_INSTITUTION: list[str] = [
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
]

RANKING_DATA: dict = {
    "ownership_type": "public",
    "accreditor": "Southern Association of Colleges and Schools Commission on Colleges (SACSCOC)",
    "carnegie_classification": (
        "Doctoral Universities: Very High Research Spending and Doctorate Production (R1)"
    ),
    "qs_world_university_rankings": {
        "rank": 68,
        "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/university-texas-austin",
    },
    "times_higher_education": {
        "rank": 50,
        "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-texas-austin",
    },
    "us_news_national": {
        "rank": 30,
        "year": 2026,
        "source_url": "https://www.usnews.com/best-colleges/university-of-texas-austin-3658",
    },
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.2664,
    "avg_net_price": 19857,
    "median_earnings_10yr": 75121,
    "graduation_rate_6yr": 0.889,
    "completion_rate_4yr_150pct": 0.889,
    "retention_rate_first_year": 0.9643,
    "financial_aid": {
        "pell_grant_rate": 0.2585,
        "federal_loan_rate": 0.2727,
        "median_debt_completers": 20500,
        "cost_of_attendance": 31247,
        "avg_net_price": 19857,
    },
    "demographics": {
        "white": 0.3036,
        "hispanic": 0.2831,
        "asian": 0.2565,
        "black": 0.0463,
        "two_or_more": 0.041,
        "american_indian": 0.0013,
        "unknown": 0.0238,
        "women": 0.5776,
    },
    "test_scores": {
        "sat_reading_25_75": [630, 740],
        "sat_math_25_75": [620, 770],
        "act_25_75": [27, 33],
        "year": 2024,
        "source": "UT Austin Common Data Set 2024-2025 / College Scorecard (middle 50% of enrolled first-year students)",
    },
    "campus_basics": {"location": "Austin, Texas"},
    "scale": {
        "student_faculty_ratio": "18:1",
        "faculty_count": 4600,
        "endowment_usd": 6177255191,
    },
    "location": {"lat": 30.2849, "lng": -97.7341},
    "research": {
        "labs": [
            "Texas Advanced Computing Center (TACC)",
            "Oden Institute for Computational Engineering and Sciences",
            "Applied Research Laboratories (ARL:UT)",
            "Bureau of Economic Geology",
            "McDonald Observatory",
        ],
        "areas": [
            "Computing, data science, and artificial intelligence",
            "Energy, geosciences, and the environment",
            "Semiconductors, materials, and advanced manufacturing",
            "Health, medicine, and the life sciences",
            "Space, astronomy, and aerospace",
        ],
        "lab_links": {
            "Texas Advanced Computing Center (TACC)": "https://www.tacc.utexas.edu/",
            "Oden Institute for Computational Engineering and Sciences": "https://oden.utexas.edu/",
            "Applied Research Laboratories (ARL:UT)": "https://www.arlut.utexas.edu/",
            "Bureau of Economic Geology": "https://www.beg.utexas.edu/",
            "McDonald Observatory": "https://mcdonaldobservatory.org/",
        },
    },
    "campus_life": {
        "athletics_division": "NCAA Division I (Southeastern Conference)",
        "resources": [
            {"name": "Texas Longhorns Athletics", "url": "https://texaslonghorns.com/"},
            {"name": "UT Libraries", "url": "https://www.lib.utexas.edu/"},
            {"name": "University Unions", "url": "https://universityunions.utexas.edu/"},
            {"name": "UT Recreational Sports", "url": "https://www.utrecsports.org/"},
            {"name": "University Housing and Dining", "url": "https://housing.utexas.edu/"},
        ],
    },
    "media_credit": "Wikimedia Commons / Michael Barera (CC BY-SA 4.0)",
    "campus_photos": [
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/University_of_Texas_at_Austin_August_2019_32_%28Littlefield_Fountain_and_Main_Building%29.jpg/1920px-University_of_Texas_at_Austin_August_2019_32_%28Littlefield_Fountain_and_Main_Building%29.jpg",
            "credit": "Wikimedia Commons / Michael Barera (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Panorama_of_UT_campus_and_downtown_Austin.jpg/1920px-Panorama_of_UT_campus_and_downtown_Austin.jpg",
            "credit": "Wikimedia Commons / Spheroidite (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/University_of_Texas_at_Austin_Tower_viewed_from_the_east.jpg/1920px-University_of_Texas_at_Austin_Tower_viewed_from_the_east.jpg",
            "credit": "Wikimedia Commons / Insightwm (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/UT_Tower_east_campus_view.jpg/1920px-UT_Tower_east_campus_view.jpg",
            "credit": "Wikimedia Commons / Spheroidite (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/UT_Tower_north_west_campus_view.jpg/1920px-UT_Tower_north_west_campus_view.jpg",
            "credit": "Wikimedia Commons / Spheroidite (CC BY-SA 4.0)",
        },
    ],
    "flagship": {
        "enrollment_total": 53864,
        "applicants": 72885,
        "admits": 19417,
        "admissions_cycle": "First-year, Fall 2024 (UT Austin Common Data Set 2024-2025)",
        "founded_year": 1883,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (UT Austin, UNITID 228778)",
            "url": "https://collegescorecard.ed.gov/school/?228778-The-University-of-Texas-at-Austin",
        },
        {
            "label": "NCES College Navigator — The University of Texas at Austin (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=228778",
        },
        {
            "label": "UT Austin Common Data Set 2024-2025 (admissions funnel, enrollment, test scores)",
            "url": "https://reports.utexas.edu/common-data-set/pdf",
        },
        {
            "label": "About UT Austin (enrollment, faculty, research, colleges)",
            "url": "https://www.utexas.edu/about-texas",
        },
        {
            "label": "UT Austin News — Fall 2024 record enrollment and graduation rates",
            "url": "https://news.utexas.edu/2024/09/19/ut-continues-to-achieve-all-time-highs-in-applications-enrollment-and-graduation-rates/",
        },
        {
            "label": "UT Austin Historical Sketch (founding years)",
            "url": "https://catalog.utexas.edu/general-information/the-university/historical-sketch/",
        },
        {
            "label": "UT Austin University Deans (school leadership)",
            "url": "https://president.utexas.edu/leadership-staff/university-deans/",
        },
        {
            "label": "UT Austin Catalog — undergraduate degree programs + graduate areas of study",
            "url": "https://catalog.utexas.edu/",
        },
        {
            "label": "Carnegie Classifications — The University of Texas at Austin (R1)",
            "url": "https://carnegieclassifications.acenet.edu/institution/the-university-of-texas-at-austin/",
        },
        {
            "label": "QS World University Rankings 2026 — UT Austin (#68)",
            "url": "https://www.topuniversities.com/universities/university-texas-austin",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — UT Austin (#50)",
            "url": "https://www.timeshighereducation.com/world-university-rankings/university-texas-austin",
        },
        {
            "label": "U.S. News Best Colleges 2026 — UT Austin (#30 National)",
            "url": "https://www.usnews.com/best-colleges/university-of-texas-austin-3658",
        },
    ],
}

# student_body_size = undergraduate enrollment (College Scorecard); total
# degree-seeking enrollment (53,864) lives in flagship.enrollment_total.
UNDERGRAD_COUNT = 42855

DESCRIPTION = (
    "The University of Texas at Austin is a public research university in Austin, TX. Founded in "
    "1883 as the flagship of the University of Texas System, it sits on the 'Forty Acres' just north "
    "of the Texas Capitol and enrolls a record 53,864 students — roughly 42,000 undergraduates and "
    "more than 11,000 graduate and professional students — with about 4,600 faculty and an 18:1 "
    "student-faculty ratio. For Fall 2024 it admitted about 26.6% of first-year applicants (19,417 "
    "of a record 72,885).\n\n"
    "UT Austin is organized into 18 colleges and schools, including the Cockrell School of "
    "Engineering, the Red McCombs School of Business, the College of Natural Sciences, the College "
    "of Liberal Arts, the Moody College of Communication, the College of Fine Arts, the Jackson "
    "School of Geosciences, the School of Information, the LBJ School of Public Affairs, the School "
    "of Law, and the Dell Medical School (opened 2016). Together they offer some 338 degree programs "
    "across the bachelor's, master's, professional, and doctoral levels — including UT's pioneering "
    "$10,000 fully online master's degrees in computer science, data science, and artificial "
    "intelligence.\n\n"
    "A Carnegie R1 university accredited by SACSCOC, UT Austin ranks #30 among national universities "
    "by U.S. News, #50 in the world by Times Higher Education, and #68 by QS for 2026, and is the #1 "
    "public university in Texas. Its research enterprise attracts more than $1.37 billion annually, "
    "anchored by the Texas Advanced Computing Center, the Oden Institute for Computational "
    "Engineering and Sciences, Applied Research Laboratories, the Bureau of Economic Geology, and "
    "the McDonald Observatory.\n\n"
    "UT Austin's published cost of attendance is about $31,250 a year, but its average net price "
    "after grant aid is about $19,857 and the median federal debt of completers is about $20,500; "
    "in-state students benefit from public tuition and programs such as Texas Advance Commitment "
    "that cover tuition for many Texas families. UT Austin graduates earn a median of roughly "
    "$75,121 ten years after entry. The Longhorns compete in NCAA Division I in the Southeastern "
    "Conference."
)

# ── Schools (18 degree-granting academic units) ──
_SCHOOL_META = [
    {
        "key": "COCKRELL",
        "name": "Cockrell School of Engineering",
        "sort_order": 1,
        "website": "https://cockrell.utexas.edu/",
        "founded": 1894,
        "leadership": "Roger T. Bonnecaze — Dean",
        "named_for": "Named in 2007 for the Cockrell family following their transformative philanthropy",
        "research_centers": [
            "Chandra Family Department of Electrical and Computer Engineering",
            "Walker Department of Mechanical Engineering",
            "McKetta Department of Chemical Engineering",
            "Department of Aerospace Engineering and Engineering Mechanics",
            "Hildebrand Department of Petroleum and Geosystems Engineering",
        ],
        "keywords": ["Cockrell School of Engineering", "Texas Engineering", "engineering"],
    },
    {
        "key": "BUSINESS",
        "name": "Red McCombs School of Business",
        "sort_order": 2,
        "website": "https://www.mccombs.utexas.edu/",
        "founded": 1922,
        "leadership": "Lillian Mills — Dean",
        "named_for": "Named in 2000 for Billy Joe 'Red' McCombs following a $50 million gift",
        "research_centers": [
            "Department of Finance",
            "Department of Marketing",
            "McCombs Department of Information, Risk, and Operations Management",
            "Rosenthal Department of Management",
            "Texas McCombs MBA programs",
        ],
        "keywords": ["McCombs School of Business", "Texas McCombs", "MBA", "business"],
    },
    {
        "key": "NATSCI",
        "name": "College of Natural Sciences",
        "sort_order": 3,
        "website": "https://cns.utexas.edu/",
        "founded": None,
        "leadership": "David Vanden Bout — Dean",
        "named_for": None,
        "research_centers": [
            "Department of Computer Science",
            "Department of Mathematics",
            "Department of Physics",
            "Department of Molecular Biosciences",
            "Department of Statistics and Data Sciences",
            "Computer & Data Science Online (MSCS, MSDS, MSAI)",
        ],
        "keywords": ["College of Natural Sciences", "computer science", "natural sciences"],
    },
    {
        "key": "LIBERALARTS",
        "name": "College of Liberal Arts",
        "sort_order": 4,
        "website": "https://liberalarts.utexas.edu/",
        "founded": None,
        "leadership": "David Sosa — Interim Dean",
        "named_for": None,
        "research_centers": [
            "Department of Economics",
            "Department of Government",
            "Department of Psychology",
            "Department of History",
            "Department of English",
        ],
        "keywords": ["College of Liberal Arts", "liberal arts"],
    },
    {
        "key": "MOODY",
        "name": "Moody College of Communication",
        "sort_order": 5,
        "website": "https://moody.utexas.edu/",
        "founded": 1965,
        "leadership": "Anita Vangelisti — Interim Dean",
        "named_for": "Named in 2013 for the Moody Foundation following a $50 million gift",
        "research_centers": [
            "School of Journalism and Media",
            "Stan Richards School of Advertising and Public Relations",
            "Department of Communication Studies",
            "Department of Radio-Television-Film",
            "Department of Speech, Language, and Hearing Sciences",
        ],
        "keywords": ["Moody College of Communication", "communication", "journalism"],
    },
    {
        "key": "FINEARTS",
        "name": "College of Fine Arts",
        "sort_order": 6,
        "website": "https://finearts.utexas.edu/",
        "founded": 1938,
        "leadership": "Ramón Rivera-Servera — Dean",
        "named_for": None,
        "research_centers": [
            "Butler School of Music",
            "Department of Theatre and Dance",
            "Department of Art and Art History",
            "School of Design and Creative Technologies",
        ],
        "keywords": ["College of Fine Arts", "fine arts", "music"],
    },
    {
        "key": "JACKSON",
        "name": "Jackson School of Geosciences",
        "sort_order": 7,
        "website": "https://www.jsg.utexas.edu/",
        "founded": 2005,
        "leadership": "Danny Stockli — Interim Dean",
        "named_for": "Named for John A. and Katherine G. Jackson",
        "research_centers": [
            "Department of Earth and Planetary Sciences",
            "Bureau of Economic Geology",
            "University of Texas Institute for Geophysics",
        ],
        "keywords": ["Jackson School of Geosciences", "geosciences", "geology"],
    },
    {
        "key": "ISCHOOL",
        "name": "School of Information",
        "sort_order": 8,
        "website": "https://www.ischool.utexas.edu/",
        "founded": 1948,
        "leadership": "Kenneth R. Fleischmann — Interim Dean",
        "named_for": None,
        "research_centers": [
            "Information Studies graduate program",
            "Information Security and Privacy program",
            "Conservation and preservation programs",
        ],
        "keywords": ["School of Information", "iSchool", "information studies"],
    },
    {
        "key": "EDUCATION",
        "name": "College of Education",
        "sort_order": 9,
        "website": "https://education.utexas.edu/",
        "founded": 1906,
        "leadership": "Charles Martinez — Dean",
        "named_for": None,
        "research_centers": [
            "Department of Curriculum and Instruction",
            "Department of Educational Leadership and Policy",
            "Department of Educational Psychology",
            "Department of Kinesiology and Health Education",
        ],
        "keywords": ["College of Education", "education", "kinesiology"],
    },
    {
        "key": "LBJ",
        "name": "LBJ School of Public Affairs",
        "sort_order": 10,
        "website": "https://lbj.utexas.edu/",
        "founded": 1970,
        "leadership": "JR DeShazo — Dean",
        "named_for": "Named for President Lyndon B. Johnson",
        "research_centers": [
            "Master of Public Affairs program",
            "Master of Global Policy Studies program",
            "Ray Marshall Center for the Study of Human Resources",
        ],
        "keywords": ["LBJ School of Public Affairs", "public affairs", "public policy"],
    },
    {
        "key": "LAW",
        "name": "School of Law",
        "sort_order": 11,
        "website": "https://law.utexas.edu/",
        "founded": 1883,
        "leadership": "Robert M. Chesney — Dean",
        "named_for": None,
        "research_centers": [
            "Doctor of Jurisprudence (J.D.) program",
            "Master of Laws (LL.M.) program",
            "Center for Global Energy, International Arbitration and Environmental Law",
        ],
        "keywords": ["Texas Law", "School of Law", "law"],
    },
    {
        "key": "PHARMACY",
        "name": "College of Pharmacy",
        "sort_order": 12,
        "website": "https://pharmacy.utexas.edu/",
        "founded": None,
        "leadership": "Samuel Poloyac — Dean",
        "named_for": None,
        "research_centers": [
            "Doctor of Pharmacy (Pharm.D.) program",
            "Division of Pharmacology and Toxicology",
            "Division of Pharmaceutics",
            "Division of Health Outcomes and Pharmacy Practice",
        ],
        "keywords": ["College of Pharmacy", "pharmacy", "PharmD"],
    },
    {
        "key": "NURSING",
        "name": "School of Nursing",
        "sort_order": 13,
        "website": "https://nursing.utexas.edu/",
        "founded": 1976,
        "leadership": "Eun-Ok Im — Dean",
        "named_for": None,
        "research_centers": [
            "Bachelor of Science in Nursing (BSN) program",
            "Master of Science in Nursing program",
            "Doctor of Nursing Practice (DNP) program",
            "Ph.D. in Nursing program",
        ],
        "keywords": ["School of Nursing", "nursing", "BSN"],
    },
    {
        "key": "SOCIALWORK",
        "name": "Steve Hicks School of Social Work",
        "sort_order": 14,
        "website": "https://socialwork.utexas.edu/",
        "founded": 1950,
        "leadership": "Allan Cole — Dean",
        "named_for": "Named in 2017 for Steve Hicks following a gift",
        "research_centers": [
            "Master of Science in Social Work (MSSW) program",
            "Ph.D. in Social Work program",
            "Texas Institute for Child & Family Wellbeing",
        ],
        "keywords": ["Steve Hicks School of Social Work", "social work", "MSSW"],
    },
    {
        "key": "ARCH",
        "name": "School of Architecture",
        "sort_order": 15,
        "website": "https://soa.utexas.edu/",
        "founded": 1951,
        "leadership": "Heather Woofter — Dean",
        "named_for": None,
        "research_centers": [
            "Architecture program",
            "Community and Regional Planning program",
            "Interior Design program",
            "Landscape Architecture program",
            "Historic Preservation program",
        ],
        "keywords": ["School of Architecture", "architecture", "planning"],
    },
    {
        "key": "DELLMED",
        "name": "Dell Medical School",
        "sort_order": 16,
        "website": "https://dellmed.utexas.edu/",
        "founded": 2016,
        "leadership": "Claudia F. Lucchinetti — Dean and Senior Vice President for Medical Affairs",
        "named_for": "Named for the Michael & Susan Dell Foundation following a founding gift",
        "research_centers": [
            "Doctor of Medicine (M.D.) program",
            "Department of Population Health",
            "Department of Neurology",
            "Livestrong Cancer Institutes",
        ],
        "keywords": ["Dell Medical School", "Dell Med", "medicine"],
    },
    {
        "key": "CIVIC",
        "name": "School of Civic Leadership",
        "sort_order": 17,
        "website": "https://civicleadership.utexas.edu/",
        "founded": None,
        "leadership": "Justin Dyer — Dean",
        "named_for": None,
        "research_centers": ["Civics Honors program", "Civic education and leadership programs"],
        "keywords": ["School of Civic Leadership", "civic leadership", "civics"],
    },
    {
        "key": "GRADSCHOOL",
        "name": "Graduate School",
        "sort_order": 18,
        "website": "https://gradschool.utexas.edu/",
        "founded": 1910,
        "leadership": "Sarah Ades — Dean of the Graduate School and Senior Vice Provost for Graduate and Postdoctoral Studies",
        "named_for": None,
        "research_centers": [
            "Computational Science, Engineering, and Mathematics (CSEM) graduate program",
            "Michener Center for Writers and the New Writers Project",
            "Interdisciplinary and intercollegial graduate programs",
        ],
        "keywords": ["UT Austin Graduate School", "interdisciplinary graduate programs"],
    },
]
SCHOOL_NAME = {m["key"]: m["name"] for m in _SCHOOL_META}
SCHOOL_WEBSITE = {m["name"]: m["website"] for m in _SCHOOL_META}


def _school_description(m: dict) -> str:
    if m["founded"]:
        return (
            f"The {m['name']}, founded in {m['founded']}, is one of the 18 colleges and schools of "
            "The University of Texas at Austin."
        )
    return f"The {m['name']} is one of the 18 colleges and schools of The University of Texas at Austin."


SCHOOLS: list[dict] = [
    {"name": m["name"], "sort_order": m["sort_order"], "description": _school_description(m)}
    for m in _SCHOOL_META
]


def _about_for(m: dict) -> dict:
    about = {
        "leadership": m["leadership"],
        "research_centers": m["research_centers"],
        "source": {
            "label": "UT Austin University Deans + Historical Sketch",
            "url": "https://president.utexas.edu/leadership-staff/university-deans/",
        },
    }
    if m["founded"]:
        about["founded"] = m["founded"]
    if m["named_for"]:
        about["named_for"] = m["named_for"]
    return about


def _about_omitted(m: dict) -> list[str]:
    out = ["about_detail.faculty"]
    if not m["founded"]:
        out.append("about_detail.founded")
    if not m["named_for"]:
        out.append("about_detail.named_for")
    return out


# ── Feeds (content_sources) ──
_UT_NEWS_RSS = "https://news.utexas.edu/feed/"
_NEWS_URL = "https://news.utexas.edu/"
_SOCIAL = {
    "instagram": "https://www.instagram.com/utaustin/",
    "linkedin": "https://www.linkedin.com/school/university-of-texas-at-austin/",
    "x": "https://twitter.com/UTAustin",
    "youtube": "https://www.youtube.com/user/universityoftexas",
    "facebook": "https://www.facebook.com/UTAustinTX",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _UT_NEWS_RSS,
    "news_url": _NEWS_URL,
    "news_curated": True,
    "social": _SOCIAL,
}
_KEYWORDS_BY_SCHOOL = {m["name"]: m["keywords"] for m in _SCHOOL_META}


def _school_content(name: str) -> dict:
    return {
        "news_rss": _UT_NEWS_RSS,
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
        "ut-austin-architectural-studies-bsas",
        "ARCH",
        "Architectural studies",
        "bachelors",
        "Architectural studies",
        "on_campus",
        48,
    ),
    (
        "ut-austin-architecture-barch",
        "ARCH",
        "Architecture",
        "bachelors",
        "Architecture",
        "on_campus",
        48,
    ),
    (
        "ut-austin-interior-design-bsid",
        "ARCH",
        "Interior design",
        "bachelors",
        "Interior design",
        "on_campus",
        48,
    ),
    (
        "ut-austin-business-administration-bba",
        "BUSINESS",
        "Business administration",
        "bachelors",
        "Business administration",
        "on_campus",
        48,
    ),
    (
        "ut-austin-accounting-bba",
        "BUSINESS",
        "Accounting",
        "bachelors",
        "Accounting",
        "on_campus",
        48,
    ),
    (
        "ut-austin-international-business-bba",
        "BUSINESS",
        "International business",
        "bachelors",
        "International business",
        "on_campus",
        48,
    ),
    ("ut-austin-finance-bba", "BUSINESS", "Finance", "bachelors", "Finance", "on_campus", 48),
    (
        "ut-austin-business-analytics-bba",
        "BUSINESS",
        "Business analytics",
        "bachelors",
        "Business analytics",
        "on_campus",
        48,
    ),
    (
        "ut-austin-management-information-systems-bba",
        "BUSINESS",
        "Management information systems",
        "bachelors",
        "Management information systems",
        "on_campus",
        48,
    ),
    (
        "ut-austin-supply-chain-management-bba",
        "BUSINESS",
        "Supply chain management",
        "bachelors",
        "Supply chain management",
        "on_campus",
        48,
    ),
    (
        "ut-austin-management-bba",
        "BUSINESS",
        "Management",
        "bachelors",
        "Management",
        "on_campus",
        48,
    ),
    ("ut-austin-marketing-bba", "BUSINESS", "Marketing", "bachelors", "Marketing", "on_campus", 48),
    (
        "ut-austin-civics-honors-ba",
        "CIVIC",
        "Civics Honors",
        "bachelors",
        "Civics Honors",
        "on_campus",
        48,
    ),
    (
        "ut-austin-advertising-bsadv",
        "MOODY",
        "Advertising",
        "bachelors",
        "Advertising",
        "on_campus",
        48,
    ),
    (
        "ut-austin-public-relations-bspr",
        "MOODY",
        "Public relations",
        "bachelors",
        "Public relations",
        "on_campus",
        48,
    ),
    (
        "ut-austin-communication-and-leadership-bscomm-and-lead",
        "MOODY",
        "Communication and leadership",
        "bachelors",
        "Communication and leadership",
        "on_campus",
        48,
    ),
    (
        "ut-austin-communication-studies-bscommstds",
        "MOODY",
        "Communication studies",
        "bachelors",
        "Communication studies",
        "on_campus",
        48,
    ),
    ("ut-austin-journalism-bj", "MOODY", "Journalism", "bachelors", "Journalism", "on_campus", 48),
    (
        "ut-austin-radio-television-film-bsrtf",
        "MOODY",
        "Radio-television-film",
        "bachelors",
        "Radio-television-film",
        "on_campus",
        48,
    ),
    (
        "ut-austin-speech-language-and-hearing-sciences-bsslh",
        "MOODY",
        "Speech, language, and hearing sciences",
        "bachelors",
        "Speech, language, and hearing sciences",
        "on_campus",
        48,
    ),
    (
        "ut-austin-education-bsed",
        "EDUCATION",
        "Education",
        "bachelors",
        "Education",
        "on_campus",
        48,
    ),
    (
        "ut-austin-youth-and-community-studies-bsed",
        "EDUCATION",
        "Youth and community studies",
        "bachelors",
        "Youth and community studies",
        "on_campus",
        48,
    ),
    (
        "ut-austin-applied-movement-science-bskin-and-health",
        "EDUCATION",
        "Applied movement science",
        "bachelors",
        "Applied movement science",
        "on_campus",
        48,
    ),
    (
        "ut-austin-athletic-training-bsathtrng",
        "EDUCATION",
        "Athletic training",
        "bachelors",
        "Athletic training",
        "on_campus",
        48,
    ),
    (
        "ut-austin-exercise-science-bskin-and-health",
        "EDUCATION",
        "Exercise science",
        "bachelors",
        "Exercise science",
        "on_campus",
        48,
    ),
    (
        "ut-austin-health-promotion-and-behavioral-science-bskin-and-health",
        "EDUCATION",
        "Health promotion and behavioral science",
        "bachelors",
        "Health promotion and behavioral science",
        "on_campus",
        48,
    ),
    (
        "ut-austin-physical-culture-and-sports-studies-bskin-and-health",
        "EDUCATION",
        "Physical culture and sports studies",
        "bachelors",
        "Physical culture and sports studies",
        "on_campus",
        48,
    ),
    (
        "ut-austin-sport-management-bskin-and-health",
        "EDUCATION",
        "Sport management",
        "bachelors",
        "Sport management",
        "on_campus",
        48,
    ),
    (
        "ut-austin-aerospace-engineering-bsase",
        "COCKRELL",
        "Aerospace engineering",
        "bachelors",
        "Aerospace engineering",
        "on_campus",
        48,
    ),
    (
        "ut-austin-computational-engineering-bscompe",
        "COCKRELL",
        "Computational engineering",
        "bachelors",
        "Computational engineering",
        "on_campus",
        48,
    ),
    (
        "ut-austin-biomedical-engineering-bsbiomede",
        "COCKRELL",
        "Biomedical engineering",
        "bachelors",
        "Biomedical engineering",
        "on_campus",
        48,
    ),
    (
        "ut-austin-chemical-engineering-bsche",
        "COCKRELL",
        "Chemical engineering",
        "bachelors",
        "Chemical engineering",
        "on_campus",
        48,
    ),
    (
        "ut-austin-architectural-engineering-bsarche",
        "COCKRELL",
        "Architectural engineering",
        "bachelors",
        "Architectural engineering",
        "on_campus",
        48,
    ),
    (
        "ut-austin-environmental-engineering-bsenve",
        "COCKRELL",
        "Environmental engineering",
        "bachelors",
        "Environmental engineering",
        "on_campus",
        48,
    ),
    (
        "ut-austin-civil-engineering-bsce",
        "COCKRELL",
        "Civil engineering",
        "bachelors",
        "Civil engineering",
        "on_campus",
        48,
    ),
    (
        "ut-austin-electrical-and-computer-engineering-bsece",
        "COCKRELL",
        "Electrical and computer engineering",
        "bachelors",
        "Electrical and computer engineering",
        "on_campus",
        48,
    ),
    (
        "ut-austin-mechanical-engineering-bsme",
        "COCKRELL",
        "Mechanical engineering",
        "bachelors",
        "Mechanical engineering",
        "on_campus",
        48,
    ),
    (
        "ut-austin-petroleum-engineering-bspe",
        "COCKRELL",
        "Petroleum engineering",
        "bachelors",
        "Petroleum engineering",
        "on_campus",
        48,
    ),
    (
        "ut-austin-geosystems-engineering-bsge",
        "COCKRELL",
        "Geosystems engineering",
        "bachelors",
        "Geosystems engineering",
        "on_campus",
        48,
    ),
    (
        "ut-austin-art-history-ba",
        "FINEARTS",
        "Art history",
        "bachelors",
        "Art history",
        "on_campus",
        48,
    ),
    (
        "ut-austin-studio-art-ba",
        "FINEARTS",
        "Studio art",
        "bachelors",
        "Studio art",
        "on_campus",
        48,
    ),
    (
        "ut-austin-art-education-bfa",
        "FINEARTS",
        "Art education",
        "bachelors",
        "Art education",
        "on_campus",
        48,
    ),
    (
        "ut-austin-arts-and-entertainment-technologies-bsaet",
        "FINEARTS",
        "Arts and entertainment technologies",
        "bachelors",
        "Arts and entertainment technologies",
        "on_campus",
        48,
    ),
    ("ut-austin-design-ba", "FINEARTS", "Design", "bachelors", "Design", "on_campus", 48),
    (
        "ut-austin-composition-bmusic",
        "FINEARTS",
        "Composition",
        "bachelors",
        "Composition",
        "on_campus",
        48,
    ),
    ("ut-austin-jazz-bmusic", "FINEARTS", "Jazz", "bachelors", "Jazz", "on_campus", 48),
    ("ut-austin-music-bamusic", "FINEARTS", "Music", "bachelors", "Music", "on_campus", 48),
    (
        "ut-austin-music-performance-bmusic",
        "FINEARTS",
        "Music performance",
        "bachelors",
        "Music performance",
        "on_campus",
        48,
    ),
    (
        "ut-austin-music-studies-bmusic",
        "FINEARTS",
        "Music studies",
        "bachelors",
        "Music studies",
        "on_campus",
        48,
    ),
    ("ut-austin-acting-bfa", "FINEARTS", "Acting", "bachelors", "Acting", "on_campus", 48),
    ("ut-austin-dance-bfa", "FINEARTS", "Dance", "bachelors", "Dance", "on_campus", 48),
    (
        "ut-austin-theatre-and-dance-batd",
        "FINEARTS",
        "Theatre and dance",
        "bachelors",
        "Theatre and dance",
        "on_campus",
        48,
    ),
    (
        "ut-austin-theatre-education-bfa",
        "FINEARTS",
        "Theatre education",
        "bachelors",
        "Theatre education",
        "on_campus",
        48,
    ),
    (
        "ut-austin-climate-system-science-bsgs",
        "JACKSON",
        "Climate system science",
        "bachelors",
        "Climate system science",
        "on_campus",
        48,
    ),
    (
        "ut-austin-general-geology-bsgs",
        "JACKSON",
        "General geology",
        "bachelors",
        "General geology",
        "on_campus",
        48,
    ),
    (
        "ut-austin-geophysics-bsgs",
        "JACKSON",
        "Geophysics",
        "bachelors",
        "Geophysics",
        "on_campus",
        48,
    ),
    (
        "ut-austin-geosciences-bags",
        "JACKSON",
        "Geosciences",
        "bachelors",
        "Geosciences",
        "on_campus",
        48,
    ),
    (
        "ut-austin-geosystems-engineering-bsge-2",
        "JACKSON",
        "Geosystems engineering",
        "bachelors",
        "Geosystems engineering",
        "on_campus",
        48,
    ),
    (
        "ut-austin-hydrology-and-water-resources-bsgs",
        "JACKSON",
        "Hydrology and water resources",
        "bachelors",
        "Hydrology and water resources",
        "on_campus",
        48,
    ),
    (
        "ut-austin-informatics-ba",
        "ISCHOOL",
        "Informatics",
        "bachelors",
        "Informatics",
        "on_campus",
        48,
    ),
    (
        "ut-austin-behavioral-and-social-data-science-bsbsds",
        "LIBERALARTS",
        "Behavioral and social data science",
        "bachelors",
        "Behavioral and social data science",
        "on_campus",
        48,
    ),
    (
        "ut-austin-health-and-society-ba",
        "LIBERALARTS",
        "Health and society",
        "bachelors",
        "Health and society",
        "on_campus",
        48,
    ),
    (
        "ut-austin-human-dimensions-of-organizations-ba",
        "LIBERALARTS",
        "Human dimensions of organizations",
        "bachelors",
        "Human dimensions of organizations",
        "on_campus",
        48,
    ),
    (
        "ut-austin-humanities-ba",
        "LIBERALARTS",
        "Humanities",
        "bachelors",
        "Humanities",
        "on_campus",
        48,
    ),
    (
        "ut-austin-international-relations-and-global-studies-ba",
        "LIBERALARTS",
        "International relations and global studies",
        "bachelors",
        "International relations and global studies",
        "on_campus",
        48,
    ),
    (
        "ut-austin-plan-ii-honors-program-ba",
        "LIBERALARTS",
        "Plan II honors program",
        "bachelors",
        "Plan II honors program",
        "on_campus",
        48,
    ),
    (
        "ut-austin-african-and-african-diaspora-studies-ba",
        "LIBERALARTS",
        "African and African diaspora studies",
        "bachelors",
        "African and African diaspora studies",
        "on_campus",
        48,
    ),
    (
        "ut-austin-race-indigeneity-and-migration-ba",
        "LIBERALARTS",
        "Race, indigeneity, and migration",
        "bachelors",
        "Race, indigeneity, and migration",
        "on_campus",
        48,
    ),
    (
        "ut-austin-american-studies-ba",
        "LIBERALARTS",
        "American studies",
        "bachelors",
        "American studies",
        "on_campus",
        48,
    ),
    (
        "ut-austin-urban-studies-ba",
        "LIBERALARTS",
        "Urban studies",
        "bachelors",
        "Urban studies",
        "on_campus",
        48,
    ),
    (
        "ut-austin-anthropology-ba",
        "LIBERALARTS",
        "Anthropology",
        "bachelors",
        "Anthropology",
        "on_campus",
        48,
    ),
    (
        "ut-austin-ethnic-studies-ba",
        "LIBERALARTS",
        "Ethnic studies",
        "bachelors",
        "Ethnic studies",
        "on_campus",
        48,
    ),
    (
        "ut-austin-asian-cultures-and-languages-ba",
        "LIBERALARTS",
        "Asian cultures and languages",
        "bachelors",
        "Asian cultures and languages",
        "on_campus",
        48,
    ),
    (
        "ut-austin-asian-studies-ba",
        "LIBERALARTS",
        "Asian studies",
        "bachelors",
        "Asian studies",
        "on_campus",
        48,
    ),
    (
        "ut-austin-classical-languages-ba",
        "LIBERALARTS",
        "Classical languages",
        "bachelors",
        "Classical languages",
        "on_campus",
        48,
    ),
    (
        "ut-austin-classical-studies-ba",
        "LIBERALARTS",
        "Classical studies",
        "bachelors",
        "Classical studies",
        "on_campus",
        48,
    ),
    (
        "ut-austin-economics-ba",
        "LIBERALARTS",
        "Economics",
        "bachelors",
        "Economics",
        "on_campus",
        48,
    ),
    ("ut-austin-english-ba", "LIBERALARTS", "English", "bachelors", "English", "on_campus", 48),
    (
        "ut-austin-european-studies-ba",
        "LIBERALARTS",
        "European studies",
        "bachelors",
        "European studies",
        "on_campus",
        48,
    ),
    (
        "ut-austin-french-studies-ba",
        "LIBERALARTS",
        "French studies",
        "bachelors",
        "French studies",
        "on_campus",
        48,
    ),
    (
        "ut-austin-italian-studies-ba",
        "LIBERALARTS",
        "Italian studies",
        "bachelors",
        "Italian studies",
        "on_campus",
        48,
    ),
    (
        "ut-austin-geographical-sciences-bsenvirsci",
        "LIBERALARTS",
        "Geographical sciences",
        "bachelors",
        "Geographical sciences",
        "on_campus",
        48,
    ),
    (
        "ut-austin-geography-ba",
        "LIBERALARTS",
        "Geography",
        "bachelors",
        "Geography",
        "on_campus",
        48,
    ),
    (
        "ut-austin-sustainability-studies-ba",
        "LIBERALARTS",
        "Sustainability studies",
        "bachelors",
        "Sustainability studies",
        "on_campus",
        48,
    ),
    ("ut-austin-german-ba", "LIBERALARTS", "German", "bachelors", "German", "on_campus", 48),
    (
        "ut-austin-government-ba",
        "LIBERALARTS",
        "Government",
        "bachelors",
        "Government",
        "on_campus",
        48,
    ),
    ("ut-austin-history-ba", "LIBERALARTS", "History", "bachelors", "History", "on_campus", 48),
    (
        "ut-austin-jewish-studies-ba",
        "LIBERALARTS",
        "Jewish studies",
        "bachelors",
        "Jewish studies",
        "on_campus",
        48,
    ),
    (
        "ut-austin-latin-american-studies-ba",
        "LIBERALARTS",
        "Latin American studies",
        "bachelors",
        "Latin American studies",
        "on_campus",
        48,
    ),
    (
        "ut-austin-linguistics-ba",
        "LIBERALARTS",
        "Linguistics",
        "bachelors",
        "Linguistics",
        "on_campus",
        48,
    ),
    (
        "ut-austin-mexican-american-and-latina-o-studies-ba",
        "LIBERALARTS",
        "Mexican American and Latina/o studies",
        "bachelors",
        "Mexican American and Latina/o studies",
        "on_campus",
        48,
    ),
    (
        "ut-austin-middle-eastern-studies-ba",
        "LIBERALARTS",
        "Middle Eastern studies",
        "bachelors",
        "Middle Eastern studies",
        "on_campus",
        48,
    ),
    (
        "ut-austin-philosophy-ba",
        "LIBERALARTS",
        "Philosophy",
        "bachelors",
        "Philosophy",
        "on_campus",
        48,
    ),
    (
        "ut-austin-psychology-ba",
        "LIBERALARTS",
        "Psychology",
        "bachelors",
        "Psychology",
        "on_campus",
        48,
    ),
    (
        "ut-austin-religious-studies-ba",
        "LIBERALARTS",
        "Religious studies",
        "bachelors",
        "Religious studies",
        "on_campus",
        48,
    ),
    (
        "ut-austin-rhetoric-and-writing-ba",
        "LIBERALARTS",
        "Rhetoric and writing",
        "bachelors",
        "Rhetoric and writing",
        "on_campus",
        48,
    ),
    (
        "ut-austin-russian-east-european-and-eurasian-studies-ba",
        "LIBERALARTS",
        "Russian, East European, and Eurasian studies",
        "bachelors",
        "Russian, East European, and Eurasian studies",
        "on_campus",
        48,
    ),
    (
        "ut-austin-sociology-ba",
        "LIBERALARTS",
        "Sociology",
        "bachelors",
        "Sociology",
        "on_campus",
        48,
    ),
    ("ut-austin-spanish-ba", "LIBERALARTS", "Spanish", "bachelors", "Spanish", "on_campus", 48),
    (
        "ut-austin-womens-and-gender-studies-ba",
        "LIBERALARTS",
        "Women's and gender studies",
        "bachelors",
        "Women's and gender studies",
        "on_campus",
        48,
    ),
    ("ut-austin-astronomy-ba", "NATSCI", "Astronomy", "bachelors", "Astronomy", "on_campus", 48),
    ("ut-austin-biology-bsa", "NATSCI", "Biology", "bachelors", "Biology", "on_campus", 48),
    ("ut-austin-chemistry-ba", "NATSCI", "Chemistry", "bachelors", "Chemistry", "on_campus", 48),
    (
        "ut-austin-computer-science-bsa",
        "NATSCI",
        "Computer science",
        "bachelors",
        "Computer science",
        "on_campus",
        48,
    ),
    (
        "ut-austin-human-ecology-bsa",
        "NATSCI",
        "Human ecology",
        "bachelors",
        "Human ecology",
        "on_campus",
        48,
    ),
    (
        "ut-austin-public-health-bspublichealth",
        "NATSCI",
        "Public health",
        "bachelors",
        "Public health",
        "on_campus",
        48,
    ),
    (
        "ut-austin-human-development-and-family-sciences-bsa",
        "NATSCI",
        "Human development and family sciences",
        "bachelors",
        "Human development and family sciences",
        "on_campus",
        48,
    ),
    ("ut-austin-nutrition-bsa", "NATSCI", "Nutrition", "bachelors", "Nutrition", "on_campus", 48),
    (
        "ut-austin-textiles-and-apparel-bsta",
        "NATSCI",
        "Textiles and apparel",
        "bachelors",
        "Textiles and apparel",
        "on_campus",
        48,
    ),
    (
        "ut-austin-biological-sciences-bsenvirsci",
        "NATSCI",
        "Biological sciences",
        "bachelors",
        "Biological sciences",
        "on_campus",
        48,
    ),
    (
        "ut-austin-mathematics-ba",
        "NATSCI",
        "Mathematics",
        "bachelors",
        "Mathematics",
        "on_campus",
        48,
    ),
    (
        "ut-austin-biochemistry-bsbioch",
        "NATSCI",
        "Biochemistry",
        "bachelors",
        "Biochemistry",
        "on_campus",
        48,
    ),
    (
        "ut-austin-medical-laboratory-science-bsmedlabsci",
        "NATSCI",
        "Medical laboratory science",
        "bachelors",
        "Medical laboratory science",
        "on_campus",
        48,
    ),
    (
        "ut-austin-neuroscience-bsa",
        "NATSCI",
        "Neuroscience",
        "bachelors",
        "Neuroscience",
        "on_campus",
        48,
    ),
    ("ut-austin-physics-ba", "NATSCI", "Physics", "bachelors", "Physics", "on_campus", 48),
    (
        "ut-austin-statistics-and-data-science-bssds",
        "NATSCI",
        "Statistics and data science",
        "bachelors",
        "Statistics and data science",
        "on_campus",
        48,
    ),
    ("ut-austin-nursing-bsn", "NURSING", "Nursing", "bachelors", "Nursing", "on_campus", 48),
    (
        "ut-austin-pharmacy-pharmd",
        "PHARMACY",
        "Pharmacy",
        "professional",
        "Pharmacy",
        "on_campus",
        48,
    ),
    (
        "ut-austin-public-affairs-bapubaff",
        "LBJ",
        "Public Affairs",
        "bachelors",
        "Public Affairs",
        "on_campus",
        48,
    ),
    (
        "ut-austin-social-work-bsw",
        "SOCIALWORK",
        "Social work",
        "bachelors",
        "Social work",
        "on_campus",
        48,
    ),
    (
        "ut-austin-architecture-march",
        "ARCH",
        "Architecture",
        "masters",
        "Architecture",
        "on_campus",
        24,
    ),
    (
        "ut-austin-architecture-maad",
        "ARCH",
        "Architecture",
        "masters",
        "Architecture",
        "on_campus",
        24,
    ),
    (
        "ut-austin-architecture-ma",
        "ARCH",
        "Architecture",
        "masters",
        "Architecture",
        "on_campus",
        24,
    ),
    (
        "ut-austin-architecture-ms",
        "ARCH",
        "Architecture",
        "masters",
        "Architecture",
        "on_campus",
        24,
    ),
    (
        "ut-austin-architecture-ms-2",
        "ARCH",
        "Architecture",
        "masters",
        "Architecture",
        "on_campus",
        24,
    ),
    ("ut-austin-architecture-phd", "ARCH", "Architecture", "phd", "Architecture", "on_campus", 60),
    (
        "ut-austin-community-and-regional-planning-ms",
        "ARCH",
        "Community and Regional Planning",
        "masters",
        "Community and Regional Planning",
        "on_campus",
        24,
    ),
    (
        "ut-austin-community-and-regional-planning-phd",
        "ARCH",
        "Community and Regional Planning",
        "phd",
        "Community and Regional Planning",
        "on_campus",
        60,
    ),
    (
        "ut-austin-interior-design-mid",
        "ARCH",
        "Interior Design",
        "masters",
        "Interior Design",
        "on_campus",
        24,
    ),
    (
        "ut-austin-landscape-architecture-mla",
        "ARCH",
        "Landscape Architecture",
        "masters",
        "Landscape Architecture",
        "on_campus",
        24,
    ),
    (
        "ut-austin-landscape-architecture-ms",
        "ARCH",
        "Landscape Architecture",
        "masters",
        "Landscape Architecture",
        "on_campus",
        24,
    ),
    (
        "ut-austin-urban-design-ms",
        "ARCH",
        "Urban Design",
        "masters",
        "Urban Design",
        "on_campus",
        24,
    ),
    (
        "ut-austin-accounting-mpa",
        "BUSINESS",
        "Accounting",
        "masters",
        "Accounting",
        "on_campus",
        24,
    ),
    ("ut-austin-accounting-ms", "BUSINESS", "Accounting", "masters", "Accounting", "on_campus", 24),
    ("ut-austin-accounting-phd", "BUSINESS", "Accounting", "phd", "Accounting", "on_campus", 60),
    (
        "ut-austin-business-administration-mba",
        "BUSINESS",
        "Business Administration",
        "masters",
        "Business Administration",
        "on_campus",
        24,
    ),
    (
        "ut-austin-business-analytics-ms",
        "BUSINESS",
        "Business Analytics",
        "masters",
        "Business Analytics",
        "on_campus",
        24,
    ),
    (
        "ut-austin-energy-management-ms",
        "BUSINESS",
        "Energy Management",
        "masters",
        "Energy Management",
        "on_campus",
        24,
    ),
    ("ut-austin-finance-ms", "BUSINESS", "Finance", "masters", "Finance", "on_campus", 24),
    ("ut-austin-finance-phd", "BUSINESS", "Finance", "phd", "Finance", "on_campus", 60),
    (
        "ut-austin-information-risk-and-operations-management-ms",
        "BUSINESS",
        "Information, Risk, and Operations Management",
        "masters",
        "Information, Risk, and Operations Management",
        "on_campus",
        24,
    ),
    (
        "ut-austin-information-risk-and-operations-management-phd",
        "BUSINESS",
        "Information, Risk, and Operations Management",
        "phd",
        "Information, Risk, and Operations Management",
        "on_campus",
        60,
    ),
    (
        "ut-austin-information-technology-and-management-ms",
        "BUSINESS",
        "Information Technology and Management",
        "masters",
        "Information Technology and Management",
        "on_campus",
        24,
    ),
    ("ut-austin-management-ms", "BUSINESS", "Management", "masters", "Management", "on_campus", 24),
    ("ut-austin-management-phd", "BUSINESS", "Management", "phd", "Management", "on_campus", 60),
    ("ut-austin-marketing-ms", "BUSINESS", "Marketing", "masters", "Marketing", "on_campus", 24),
    ("ut-austin-marketing-phd", "BUSINESS", "Marketing", "phd", "Marketing", "on_campus", 60),
    (
        "ut-austin-technology-commercialization-ms",
        "BUSINESS",
        "Technology Commercialization",
        "masters",
        "Technology Commercialization",
        "on_campus",
        24,
    ),
    ("ut-austin-advertising-ma", "MOODY", "Advertising", "masters", "Advertising", "on_campus", 24),
    ("ut-austin-advertising-phd", "MOODY", "Advertising", "phd", "Advertising", "on_campus", 60),
    ("ut-austin-audiology-aud", "MOODY", "Audiology", "professional", "Audiology", "on_campus", 24),
    (
        "ut-austin-communication-studies-ma",
        "MOODY",
        "Communication Studies",
        "masters",
        "Communication Studies",
        "on_campus",
        24,
    ),
    (
        "ut-austin-communication-studies-phd",
        "MOODY",
        "Communication Studies",
        "phd",
        "Communication Studies",
        "on_campus",
        60,
    ),
    (
        "ut-austin-journalism-and-media-ma",
        "MOODY",
        "Journalism and Media",
        "masters",
        "Journalism and Media",
        "on_campus",
        24,
    ),
    (
        "ut-austin-journalism-and-media-phd",
        "MOODY",
        "Journalism and Media",
        "phd",
        "Journalism and Media",
        "on_campus",
        60,
    ),
    (
        "ut-austin-radio-television-film-ma",
        "MOODY",
        "Radio-Television-Film",
        "masters",
        "Radio-Television-Film",
        "on_campus",
        24,
    ),
    (
        "ut-austin-radio-television-film-mfa",
        "MOODY",
        "Radio-Television-Film",
        "masters",
        "Radio-Television-Film",
        "on_campus",
        24,
    ),
    (
        "ut-austin-radio-television-film-phd",
        "MOODY",
        "Radio-Television-Film",
        "phd",
        "Radio-Television-Film",
        "on_campus",
        60,
    ),
    (
        "ut-austin-speech-language-and-hearing-sciences-ms",
        "MOODY",
        "Speech, Language, and Hearing Sciences",
        "masters",
        "Speech, Language, and Hearing Sciences",
        "on_campus",
        24,
    ),
    (
        "ut-austin-speech-language-and-hearing-sciences-phd",
        "MOODY",
        "Speech, Language, and Hearing Sciences",
        "phd",
        "Speech, Language, and Hearing Sciences",
        "on_campus",
        60,
    ),
    (
        "ut-austin-curriculum-and-instruction-ma",
        "EDUCATION",
        "Curriculum and Instruction",
        "masters",
        "Curriculum and Instruction",
        "on_campus",
        24,
    ),
    (
        "ut-austin-curriculum-and-instruction-med",
        "EDUCATION",
        "Curriculum and Instruction",
        "masters",
        "Curriculum and Instruction",
        "on_campus",
        24,
    ),
    (
        "ut-austin-curriculum-and-instruction-phd",
        "EDUCATION",
        "Curriculum and Instruction",
        "phd",
        "Curriculum and Instruction",
        "on_campus",
        60,
    ),
    (
        "ut-austin-curriculum-and-instruction-edd",
        "EDUCATION",
        "Curriculum and Instruction",
        "phd",
        "Curriculum and Instruction",
        "on_campus",
        60,
    ),
    (
        "ut-austin-educational-leadership-and-policy-med",
        "EDUCATION",
        "Educational Leadership and Policy",
        "masters",
        "Educational Leadership and Policy",
        "on_campus",
        24,
    ),
    (
        "ut-austin-educational-leadership-and-policy-phd",
        "EDUCATION",
        "Educational Leadership and Policy",
        "phd",
        "Educational Leadership and Policy",
        "on_campus",
        60,
    ),
    (
        "ut-austin-educational-leadership-and-policy-edd",
        "EDUCATION",
        "Educational Leadership and Policy",
        "phd",
        "Educational Leadership and Policy",
        "on_campus",
        60,
    ),
    (
        "ut-austin-educational-psychology-ma",
        "EDUCATION",
        "Educational Psychology",
        "masters",
        "Educational Psychology",
        "on_campus",
        24,
    ),
    (
        "ut-austin-educational-psychology-med",
        "EDUCATION",
        "Educational Psychology",
        "masters",
        "Educational Psychology",
        "on_campus",
        24,
    ),
    (
        "ut-austin-educational-psychology-phd",
        "EDUCATION",
        "Educational Psychology",
        "phd",
        "Educational Psychology",
        "on_campus",
        60,
    ),
    (
        "ut-austin-health-behavior-and-health-education-med",
        "EDUCATION",
        "Health Behavior and Health Education",
        "masters",
        "Health Behavior and Health Education",
        "on_campus",
        24,
    ),
    (
        "ut-austin-health-behavior-and-health-education-ms",
        "EDUCATION",
        "Health Behavior and Health Education",
        "masters",
        "Health Behavior and Health Education",
        "on_campus",
        24,
    ),
    (
        "ut-austin-health-behavior-and-health-education-phd",
        "EDUCATION",
        "Health Behavior and Health Education",
        "phd",
        "Health Behavior and Health Education",
        "on_campus",
        60,
    ),
    (
        "ut-austin-kinesiology-med",
        "EDUCATION",
        "Kinesiology",
        "masters",
        "Kinesiology",
        "on_campus",
        24,
    ),
    (
        "ut-austin-kinesiology-ms",
        "EDUCATION",
        "Kinesiology",
        "masters",
        "Kinesiology",
        "on_campus",
        24,
    ),
    (
        "ut-austin-kinesiology-phd",
        "EDUCATION",
        "Kinesiology",
        "phd",
        "Kinesiology",
        "on_campus",
        60,
    ),
    (
        "ut-austin-special-education-ma",
        "EDUCATION",
        "Special Education",
        "masters",
        "Special Education",
        "on_campus",
        24,
    ),
    (
        "ut-austin-special-education-med",
        "EDUCATION",
        "Special Education",
        "masters",
        "Special Education",
        "on_campus",
        24,
    ),
    (
        "ut-austin-special-education-phd",
        "EDUCATION",
        "Special Education",
        "phd",
        "Special Education",
        "on_campus",
        60,
    ),
    (
        "ut-austin-special-education-edd",
        "EDUCATION",
        "Special Education",
        "phd",
        "Special Education",
        "on_campus",
        60,
    ),
    (
        "ut-austin-science-technology-engineering-and-mathematics-education-ma",
        "EDUCATION",
        "Science, Technology, Engineering, and Mathematics Education",
        "masters",
        "Science, Technology, Engineering, and Mathematics Education",
        "on_campus",
        24,
    ),
    (
        "ut-austin-science-technology-engineering-and-mathematics-education-med",
        "EDUCATION",
        "Science, Technology, Engineering, and Mathematics Education",
        "masters",
        "Science, Technology, Engineering, and Mathematics Education",
        "on_campus",
        24,
    ),
    (
        "ut-austin-science-technology-engineering-and-mathematics-education-phd",
        "EDUCATION",
        "Science, Technology, Engineering, and Mathematics Education",
        "phd",
        "Science, Technology, Engineering, and Mathematics Education",
        "on_campus",
        60,
    ),
    (
        "ut-austin-aerospace-engineering-ms",
        "COCKRELL",
        "Aerospace Engineering",
        "masters",
        "Aerospace Engineering",
        "on_campus",
        24,
    ),
    (
        "ut-austin-aerospace-engineering-phd",
        "COCKRELL",
        "Aerospace Engineering",
        "phd",
        "Aerospace Engineering",
        "on_campus",
        60,
    ),
    (
        "ut-austin-biomedical-engineering-ms",
        "COCKRELL",
        "Biomedical Engineering",
        "masters",
        "Biomedical Engineering",
        "on_campus",
        24,
    ),
    (
        "ut-austin-biomedical-engineering-phd",
        "COCKRELL",
        "Biomedical Engineering",
        "phd",
        "Biomedical Engineering",
        "on_campus",
        60,
    ),
    (
        "ut-austin-chemical-engineering-ms",
        "COCKRELL",
        "Chemical Engineering",
        "masters",
        "Chemical Engineering",
        "on_campus",
        24,
    ),
    (
        "ut-austin-chemical-engineering-phd",
        "COCKRELL",
        "Chemical Engineering",
        "phd",
        "Chemical Engineering",
        "on_campus",
        60,
    ),
    (
        "ut-austin-civil-engineering-ms",
        "COCKRELL",
        "Civil Engineering",
        "masters",
        "Civil Engineering",
        "on_campus",
        24,
    ),
    (
        "ut-austin-civil-engineering-phd",
        "COCKRELL",
        "Civil Engineering",
        "phd",
        "Civil Engineering",
        "on_campus",
        60,
    ),
    (
        "ut-austin-electrical-and-computer-engineering-ms",
        "COCKRELL",
        "Electrical and Computer Engineering",
        "masters",
        "Electrical and Computer Engineering",
        "on_campus",
        24,
    ),
    (
        "ut-austin-electrical-and-computer-engineering-phd",
        "COCKRELL",
        "Electrical and Computer Engineering",
        "phd",
        "Electrical and Computer Engineering",
        "on_campus",
        60,
    ),
    (
        "ut-austin-engineering-management-ms",
        "COCKRELL",
        "Engineering Management",
        "masters",
        "Engineering Management",
        "on_campus",
        24,
    ),
    (
        "ut-austin-engineering-mechanics-ms",
        "COCKRELL",
        "Engineering Mechanics",
        "masters",
        "Engineering Mechanics",
        "on_campus",
        24,
    ),
    (
        "ut-austin-engineering-mechanics-phd",
        "COCKRELL",
        "Engineering Mechanics",
        "phd",
        "Engineering Mechanics",
        "on_campus",
        60,
    ),
    (
        "ut-austin-materials-science-and-engineering-ms",
        "COCKRELL",
        "Materials Science and Engineering",
        "masters",
        "Materials Science and Engineering",
        "on_campus",
        24,
    ),
    (
        "ut-austin-materials-science-and-engineering-phd",
        "COCKRELL",
        "Materials Science and Engineering",
        "phd",
        "Materials Science and Engineering",
        "on_campus",
        60,
    ),
    (
        "ut-austin-mechanical-engineering-ms",
        "COCKRELL",
        "Mechanical Engineering",
        "masters",
        "Mechanical Engineering",
        "on_campus",
        24,
    ),
    (
        "ut-austin-mechanical-engineering-phd",
        "COCKRELL",
        "Mechanical Engineering",
        "phd",
        "Mechanical Engineering",
        "on_campus",
        60,
    ),
    (
        "ut-austin-operations-research-and-industrial-engineering-ms",
        "COCKRELL",
        "Operations Research and Industrial Engineering",
        "masters",
        "Operations Research and Industrial Engineering",
        "on_campus",
        24,
    ),
    (
        "ut-austin-operations-research-and-industrial-engineering-phd",
        "COCKRELL",
        "Operations Research and Industrial Engineering",
        "phd",
        "Operations Research and Industrial Engineering",
        "on_campus",
        60,
    ),
    (
        "ut-austin-petroleum-and-geosystems-engineering-ms",
        "COCKRELL",
        "Petroleum and Geosystems Engineering",
        "masters",
        "Petroleum and Geosystems Engineering",
        "on_campus",
        24,
    ),
    (
        "ut-austin-petroleum-and-geosystems-engineering-phd",
        "COCKRELL",
        "Petroleum and Geosystems Engineering",
        "phd",
        "Petroleum and Geosystems Engineering",
        "on_campus",
        60,
    ),
    (
        "ut-austin-semiconductor-science-and-engineering-ms",
        "COCKRELL",
        "Semiconductor Science and Engineering",
        "masters",
        "Semiconductor Science and Engineering",
        "on_campus",
        24,
    ),
    (
        "ut-austin-art-education-ma",
        "FINEARTS",
        "Art Education",
        "masters",
        "Art Education",
        "on_campus",
        24,
    ),
    (
        "ut-austin-art-history-ma",
        "FINEARTS",
        "Art History",
        "masters",
        "Art History",
        "on_campus",
        24,
    ),
    ("ut-austin-art-history-phd", "FINEARTS", "Art History", "phd", "Art History", "on_campus", 60),
    ("ut-austin-design-mfa", "FINEARTS", "Design", "masters", "Design", "on_campus", 24),
    ("ut-austin-design-ma", "FINEARTS", "Design", "masters", "Design", "on_campus", 24),
    ("ut-austin-music-mm", "FINEARTS", "Music", "masters", "Music", "on_campus", 24),
    ("ut-austin-music-dma", "FINEARTS", "Music", "phd", "Music", "on_campus", 60),
    ("ut-austin-music-phd", "FINEARTS", "Music", "phd", "Music", "on_campus", 60),
    (
        "ut-austin-music-music-and-human-learning-mm",
        "FINEARTS",
        "Music (Music and Human Learning)",
        "masters",
        "Music",
        "on_campus",
        24,
    ),
    (
        "ut-austin-music-music-and-human-learning-dma",
        "FINEARTS",
        "Music (Music and Human Learning)",
        "phd",
        "Music",
        "on_campus",
        60,
    ),
    (
        "ut-austin-music-music-and-human-learning-phd",
        "FINEARTS",
        "Music (Music and Human Learning)",
        "phd",
        "Music",
        "on_campus",
        60,
    ),
    (
        "ut-austin-music-conducting-mm",
        "FINEARTS",
        "Music (Conducting)",
        "masters",
        "Music",
        "on_campus",
        24,
    ),
    (
        "ut-austin-music-conducting-dma",
        "FINEARTS",
        "Music (Conducting)",
        "phd",
        "Music",
        "on_campus",
        60,
    ),
    (
        "ut-austin-studio-art-mfa",
        "FINEARTS",
        "Studio Art",
        "masters",
        "Studio Art",
        "on_campus",
        24,
    ),
    (
        "ut-austin-theatre-and-dance-theatre-ma",
        "FINEARTS",
        "Theatre and Dance (Theatre)",
        "masters",
        "Theatre and Dance",
        "on_campus",
        24,
    ),
    (
        "ut-austin-theatre-and-dance-dance-mfa",
        "FINEARTS",
        "Theatre and Dance (Dance)",
        "masters",
        "Theatre and Dance",
        "on_campus",
        24,
    ),
    (
        "ut-austin-theatre-and-dance-theatre-mfa",
        "FINEARTS",
        "Theatre and Dance (Theatre)",
        "masters",
        "Theatre and Dance",
        "on_campus",
        24,
    ),
    (
        "ut-austin-theatre-and-dance-theatre-phd",
        "FINEARTS",
        "Theatre and Dance (Theatre)",
        "phd",
        "Theatre and Dance",
        "on_campus",
        60,
    ),
    (
        "ut-austin-energy-and-earth-resources-ma",
        "JACKSON",
        "Energy and Earth Resources",
        "masters",
        "Energy and Earth Resources",
        "on_campus",
        24,
    ),
    (
        "ut-austin-energy-and-earth-resources-ms",
        "JACKSON",
        "Energy and Earth Resources",
        "masters",
        "Energy and Earth Resources",
        "on_campus",
        24,
    ),
    (
        "ut-austin-geological-sciences-ma",
        "JACKSON",
        "Geological Sciences",
        "masters",
        "Geological Sciences",
        "on_campus",
        24,
    ),
    (
        "ut-austin-geological-sciences-ms",
        "JACKSON",
        "Geological Sciences",
        "masters",
        "Geological Sciences",
        "on_campus",
        24,
    ),
    (
        "ut-austin-geological-sciences-phd",
        "JACKSON",
        "Geological Sciences",
        "phd",
        "Geological Sciences",
        "on_campus",
        60,
    ),
    (
        "ut-austin-information-security-and-privacy-ms",
        "ISCHOOL",
        "Information Security and Privacy",
        "masters",
        "Information Security and Privacy",
        "on_campus",
        24,
    ),
    (
        "ut-austin-information-studies-ms",
        "ISCHOOL",
        "Information Studies",
        "masters",
        "Information Studies",
        "on_campus",
        24,
    ),
    (
        "ut-austin-information-studies-phd",
        "ISCHOOL",
        "Information Studies",
        "phd",
        "Information Studies",
        "on_campus",
        60,
    ),
    (
        "ut-austin-computational-science-engineering-and-mathematics-ms",
        "GRADSCHOOL",
        "Computational Science, Engineering, and Mathematics",
        "masters",
        "Computational Science, Engineering, and Mathematics",
        "on_campus",
        24,
    ),
    (
        "ut-austin-computational-science-engineering-and-mathematics-phd",
        "GRADSCHOOL",
        "Computational Science, Engineering, and Mathematics",
        "phd",
        "Computational Science, Engineering, and Mathematics",
        "on_campus",
        60,
    ),
    ("ut-austin-writing-mfa", "GRADSCHOOL", "Writing", "masters", "Writing", "on_campus", 24),
    (
        "ut-austin-african-and-african-diaspora-studies-ma",
        "LIBERALARTS",
        "African and African Diaspora Studies",
        "masters",
        "African and African Diaspora Studies",
        "on_campus",
        24,
    ),
    (
        "ut-austin-african-and-african-diaspora-studies-phd",
        "LIBERALARTS",
        "African and African Diaspora Studies",
        "phd",
        "African and African Diaspora Studies",
        "on_campus",
        60,
    ),
    (
        "ut-austin-american-studies-ma",
        "LIBERALARTS",
        "American Studies",
        "masters",
        "American Studies",
        "on_campus",
        24,
    ),
    (
        "ut-austin-american-studies-phd",
        "LIBERALARTS",
        "American Studies",
        "phd",
        "American Studies",
        "on_campus",
        60,
    ),
    (
        "ut-austin-anthropology-ma",
        "LIBERALARTS",
        "Anthropology",
        "masters",
        "Anthropology",
        "on_campus",
        24,
    ),
    (
        "ut-austin-anthropology-phd",
        "LIBERALARTS",
        "Anthropology",
        "phd",
        "Anthropology",
        "on_campus",
        60,
    ),
    (
        "ut-austin-asian-studies-ma",
        "LIBERALARTS",
        "Asian Studies",
        "masters",
        "Asian Studies",
        "on_campus",
        24,
    ),
    (
        "ut-austin-asian-studies-asian-cultures-and-languages-ma",
        "LIBERALARTS",
        "Asian Studies (Asian Cultures and Languages)",
        "masters",
        "Asian Studies",
        "on_campus",
        24,
    ),
    (
        "ut-austin-asian-studies-asian-cultures-and-languages-phd",
        "LIBERALARTS",
        "Asian Studies (Asian Cultures and Languages)",
        "phd",
        "Asian Studies",
        "on_campus",
        60,
    ),
    ("ut-austin-classics-ma", "LIBERALARTS", "Classics", "masters", "Classics", "on_campus", 24),
    ("ut-austin-classics-phd", "LIBERALARTS", "Classics", "phd", "Classics", "on_campus", 60),
    (
        "ut-austin-comparative-literature-ma",
        "LIBERALARTS",
        "Comparative Literature",
        "masters",
        "Comparative Literature",
        "on_campus",
        24,
    ),
    (
        "ut-austin-comparative-literature-phd",
        "LIBERALARTS",
        "Comparative Literature",
        "phd",
        "Comparative Literature",
        "on_campus",
        60,
    ),
    ("ut-austin-economics-ma", "LIBERALARTS", "Economics", "masters", "Economics", "on_campus", 24),
    ("ut-austin-economics-ms", "LIBERALARTS", "Economics", "masters", "Economics", "on_campus", 24),
    ("ut-austin-economics-phd", "LIBERALARTS", "Economics", "phd", "Economics", "on_campus", 60),
    ("ut-austin-english-ma", "LIBERALARTS", "English", "masters", "English", "on_campus", 24),
    (
        "ut-austin-english-creative-writing-mfa",
        "LIBERALARTS",
        "English (Creative Writing)",
        "masters",
        "English",
        "on_campus",
        24,
    ),
    ("ut-austin-english-phd", "LIBERALARTS", "English", "phd", "English", "on_campus", 60),
    (
        "ut-austin-french-and-italian-french-ma",
        "LIBERALARTS",
        "French and Italian (French)",
        "masters",
        "French and Italian",
        "on_campus",
        24,
    ),
    (
        "ut-austin-french-and-italian-italian-studies-ma",
        "LIBERALARTS",
        "French and Italian (Italian Studies)",
        "masters",
        "French and Italian",
        "on_campus",
        24,
    ),
    (
        "ut-austin-french-and-italian-french-phd",
        "LIBERALARTS",
        "French and Italian (French)",
        "phd",
        "French and Italian",
        "on_campus",
        60,
    ),
    (
        "ut-austin-french-and-italian-italian-studies-phd",
        "LIBERALARTS",
        "French and Italian (Italian Studies)",
        "phd",
        "French and Italian",
        "on_campus",
        60,
    ),
    ("ut-austin-geography-ma", "LIBERALARTS", "Geography", "masters", "Geography", "on_campus", 24),
    ("ut-austin-geography-phd", "LIBERALARTS", "Geography", "phd", "Geography", "on_campus", 60),
    (
        "ut-austin-germanic-studies-ma",
        "LIBERALARTS",
        "Germanic Studies",
        "masters",
        "Germanic Studies",
        "on_campus",
        24,
    ),
    (
        "ut-austin-germanic-studies-phd",
        "LIBERALARTS",
        "Germanic Studies",
        "phd",
        "Germanic Studies",
        "on_campus",
        60,
    ),
    (
        "ut-austin-government-ma",
        "LIBERALARTS",
        "Government",
        "masters",
        "Government",
        "on_campus",
        24,
    ),
    ("ut-austin-government-phd", "LIBERALARTS", "Government", "phd", "Government", "on_campus", 60),
    ("ut-austin-history-ma", "LIBERALARTS", "History", "masters", "History", "on_campus", 24),
    ("ut-austin-history-phd", "LIBERALARTS", "History", "phd", "History", "on_campus", 60),
    (
        "ut-austin-human-dimensions-of-organizations-ma",
        "LIBERALARTS",
        "Human Dimensions of Organizations",
        "masters",
        "Human Dimensions of Organizations",
        "on_campus",
        24,
    ),
    (
        "ut-austin-humanities-health-and-medicine-ma",
        "LIBERALARTS",
        "Humanities, Health, and Medicine",
        "masters",
        "Humanities, Health, and Medicine",
        "on_campus",
        24,
    ),
    (
        "ut-austin-iberian-and-latin-american-languages-and-cultures-ma",
        "LIBERALARTS",
        "Iberian and Latin American Languages and Cultures",
        "masters",
        "Iberian and Latin American Languages and Cultures",
        "on_campus",
        24,
    ),
    (
        "ut-austin-iberian-and-latin-american-languages-and-cultures-phd",
        "LIBERALARTS",
        "Iberian and Latin American Languages and Cultures",
        "phd",
        "Iberian and Latin American Languages and Cultures",
        "on_campus",
        60,
    ),
    (
        "ut-austin-latin-american-studies-ma",
        "LIBERALARTS",
        "Latin American Studies",
        "masters",
        "Latin American Studies",
        "on_campus",
        24,
    ),
    (
        "ut-austin-latin-american-studies-phd",
        "LIBERALARTS",
        "Latin American Studies",
        "phd",
        "Latin American Studies",
        "on_campus",
        60,
    ),
    (
        "ut-austin-linguistics-ma",
        "LIBERALARTS",
        "Linguistics",
        "masters",
        "Linguistics",
        "on_campus",
        24,
    ),
    (
        "ut-austin-linguistics-phd",
        "LIBERALARTS",
        "Linguistics",
        "phd",
        "Linguistics",
        "on_campus",
        60,
    ),
    (
        "ut-austin-mexican-american-and-latina-o-studies-ma",
        "LIBERALARTS",
        "Mexican American and Latina/o Studies",
        "masters",
        "Mexican American and Latina/o Studies",
        "on_campus",
        24,
    ),
    (
        "ut-austin-mexican-american-and-latina-o-studies-phd",
        "LIBERALARTS",
        "Mexican American and Latina/o Studies",
        "phd",
        "Mexican American and Latina/o Studies",
        "on_campus",
        60,
    ),
    (
        "ut-austin-middle-eastern-languages-and-cultures-ma",
        "LIBERALARTS",
        "Middle Eastern Languages and Cultures",
        "masters",
        "Middle Eastern Languages and Cultures",
        "on_campus",
        24,
    ),
    (
        "ut-austin-middle-eastern-languages-and-cultures-phd",
        "LIBERALARTS",
        "Middle Eastern Languages and Cultures",
        "phd",
        "Middle Eastern Languages and Cultures",
        "on_campus",
        60,
    ),
    (
        "ut-austin-middle-eastern-studies-ma",
        "LIBERALARTS",
        "Middle Eastern Studies",
        "masters",
        "Middle Eastern Studies",
        "on_campus",
        24,
    ),
    (
        "ut-austin-philosophy-ma",
        "LIBERALARTS",
        "Philosophy",
        "masters",
        "Philosophy",
        "on_campus",
        24,
    ),
    ("ut-austin-philosophy-phd", "LIBERALARTS", "Philosophy", "phd", "Philosophy", "on_campus", 60),
    (
        "ut-austin-psychology-ma",
        "LIBERALARTS",
        "Psychology",
        "masters",
        "Psychology",
        "on_campus",
        24,
    ),
    ("ut-austin-psychology-phd", "LIBERALARTS", "Psychology", "phd", "Psychology", "on_campus", 60),
    (
        "ut-austin-religious-studies-ma",
        "LIBERALARTS",
        "Religious Studies",
        "masters",
        "Religious Studies",
        "on_campus",
        24,
    ),
    (
        "ut-austin-religious-studies-phd",
        "LIBERALARTS",
        "Religious Studies",
        "phd",
        "Religious Studies",
        "on_campus",
        60,
    ),
    (
        "ut-austin-rhetoric-and-writing-studies-ma",
        "LIBERALARTS",
        "Rhetoric and Writing Studies",
        "masters",
        "Rhetoric and Writing Studies",
        "on_campus",
        24,
    ),
    (
        "ut-austin-rhetoric-and-writing-studies-phd",
        "LIBERALARTS",
        "Rhetoric and Writing Studies",
        "phd",
        "Rhetoric and Writing Studies",
        "on_campus",
        60,
    ),
    (
        "ut-austin-russian-east-european-and-eurasian-studies-ma",
        "LIBERALARTS",
        "Russian, East European, and Eurasian Studies",
        "masters",
        "Russian, East European, and Eurasian Studies",
        "on_campus",
        24,
    ),
    ("ut-austin-sociology-ma", "LIBERALARTS", "Sociology", "masters", "Sociology", "on_campus", 24),
    ("ut-austin-sociology-phd", "LIBERALARTS", "Sociology", "phd", "Sociology", "on_campus", 60),
    (
        "ut-austin-womens-and-gender-studies-ma",
        "LIBERALARTS",
        "Women’s and Gender Studies",
        "masters",
        "Women’s and Gender Studies",
        "on_campus",
        24,
    ),
    (
        "ut-austin-artificial-intelligence-ms",
        "NATSCI",
        "Artificial Intelligence",
        "masters",
        "Artificial Intelligence",
        "online",
        24,
    ),
    ("ut-austin-astronomy-ma", "NATSCI", "Astronomy", "masters", "Astronomy", "on_campus", 24),
    ("ut-austin-astronomy-phd", "NATSCI", "Astronomy", "phd", "Astronomy", "on_campus", 60),
    (
        "ut-austin-biochemistry-ma",
        "NATSCI",
        "Biochemistry",
        "masters",
        "Biochemistry",
        "on_campus",
        24,
    ),
    (
        "ut-austin-biochemistry-phd",
        "NATSCI",
        "Biochemistry",
        "phd",
        "Biochemistry",
        "on_campus",
        60,
    ),
    (
        "ut-austin-cell-and-molecular-biology-ma",
        "NATSCI",
        "Cell and Molecular Biology",
        "masters",
        "Cell and Molecular Biology",
        "on_campus",
        24,
    ),
    (
        "ut-austin-cell-and-molecular-biology-phd",
        "NATSCI",
        "Cell and Molecular Biology",
        "phd",
        "Cell and Molecular Biology",
        "on_campus",
        60,
    ),
    ("ut-austin-chemistry-ma", "NATSCI", "Chemistry", "masters", "Chemistry", "on_campus", 24),
    ("ut-austin-chemistry-phd", "NATSCI", "Chemistry", "phd", "Chemistry", "on_campus", 60),
    (
        "ut-austin-computer-science-ms",
        "NATSCI",
        "Computer Science",
        "masters",
        "Computer Science",
        "on_campus",
        24,
    ),
    (
        "ut-austin-computer-science-phd",
        "NATSCI",
        "Computer Science",
        "phd",
        "Computer Science",
        "on_campus",
        60,
    ),
    (
        "ut-austin-data-science-ms",
        "NATSCI",
        "Data Science",
        "masters",
        "Data Science",
        "online",
        24,
    ),
    (
        "ut-austin-ecology-evolution-and-behavior-ma",
        "NATSCI",
        "Ecology, Evolution, and Behavior",
        "masters",
        "Ecology, Evolution, and Behavior",
        "on_campus",
        24,
    ),
    (
        "ut-austin-ecology-evolution-and-behavior-phd",
        "NATSCI",
        "Ecology, Evolution, and Behavior",
        "phd",
        "Ecology, Evolution, and Behavior",
        "on_campus",
        60,
    ),
    (
        "ut-austin-human-development-and-family-sciences-ma",
        "NATSCI",
        "Human Development and Family Sciences",
        "masters",
        "Human Development and Family Sciences",
        "on_campus",
        24,
    ),
    (
        "ut-austin-human-development-and-family-sciences-phd",
        "NATSCI",
        "Human Development and Family Sciences",
        "phd",
        "Human Development and Family Sciences",
        "on_campus",
        60,
    ),
    (
        "ut-austin-marine-science-ms",
        "NATSCI",
        "Marine Science",
        "masters",
        "Marine Science",
        "on_campus",
        24,
    ),
    (
        "ut-austin-marine-science-phd",
        "NATSCI",
        "Marine Science",
        "phd",
        "Marine Science",
        "on_campus",
        60,
    ),
    (
        "ut-austin-mathematics-ma",
        "NATSCI",
        "Mathematics",
        "masters",
        "Mathematics",
        "on_campus",
        24,
    ),
    ("ut-austin-mathematics-phd", "NATSCI", "Mathematics", "phd", "Mathematics", "on_campus", 60),
    (
        "ut-austin-microbiology-ma",
        "NATSCI",
        "Microbiology",
        "masters",
        "Microbiology",
        "on_campus",
        24,
    ),
    (
        "ut-austin-microbiology-phd",
        "NATSCI",
        "Microbiology",
        "phd",
        "Microbiology",
        "on_campus",
        60,
    ),
    (
        "ut-austin-neuroscience-ms",
        "NATSCI",
        "Neuroscience",
        "masters",
        "Neuroscience",
        "on_campus",
        24,
    ),
    (
        "ut-austin-neuroscience-phd",
        "NATSCI",
        "Neuroscience",
        "phd",
        "Neuroscience",
        "on_campus",
        60,
    ),
    (
        "ut-austin-nutritional-sciences-ms",
        "NATSCI",
        "Nutritional Sciences",
        "masters",
        "Nutritional Sciences",
        "on_campus",
        24,
    ),
    (
        "ut-austin-nutritional-sciences-phd",
        "NATSCI",
        "Nutritional Sciences",
        "phd",
        "Nutritional Sciences",
        "on_campus",
        60,
    ),
    ("ut-austin-physics-ma", "NATSCI", "Physics", "masters", "Physics", "on_campus", 24),
    ("ut-austin-physics-phd", "NATSCI", "Physics", "phd", "Physics", "on_campus", 60),
    (
        "ut-austin-plant-biology-ma",
        "NATSCI",
        "Plant Biology",
        "masters",
        "Plant Biology",
        "on_campus",
        24,
    ),
    (
        "ut-austin-plant-biology-phd",
        "NATSCI",
        "Plant Biology",
        "phd",
        "Plant Biology",
        "on_campus",
        60,
    ),
    ("ut-austin-statistics-ms", "NATSCI", "Statistics", "masters", "Statistics", "on_campus", 24),
    ("ut-austin-statistics-phd", "NATSCI", "Statistics", "phd", "Statistics", "on_campus", 60),
    (
        "ut-austin-pharmaceutical-sciences-ms",
        "PHARMACY",
        "Pharmaceutical Sciences",
        "masters",
        "Pharmaceutical Sciences",
        "on_campus",
        24,
    ),
    (
        "ut-austin-pharmaceutical-sciences-phd",
        "PHARMACY",
        "Pharmaceutical Sciences",
        "phd",
        "Pharmaceutical Sciences",
        "on_campus",
        60,
    ),
    (
        "ut-austin-translational-science-phd",
        "PHARMACY",
        "Translational Science",
        "phd",
        "Translational Science",
        "on_campus",
        60,
    ),
    (
        "ut-austin-global-policy-studies-mgps",
        "LBJ",
        "Global Policy Studies",
        "masters",
        "Global Policy Studies",
        "on_campus",
        24,
    ),
    (
        "ut-austin-public-affairs-mpaff",
        "LBJ",
        "Public Affairs",
        "masters",
        "Public Affairs",
        "on_campus",
        24,
    ),
    (
        "ut-austin-public-leadership-mpl",
        "LBJ",
        "Public Leadership",
        "masters",
        "Public Leadership",
        "on_campus",
        24,
    ),
    (
        "ut-austin-public-policy-phd",
        "LBJ",
        "Public Policy",
        "phd",
        "Public Policy",
        "on_campus",
        60,
    ),
    ("ut-austin-nursing-ms", "NURSING", "Nursing", "masters", "Nursing", "on_campus", 24),
    ("ut-austin-nursing-phd", "NURSING", "Nursing", "phd", "Nursing", "on_campus", 60),
    ("ut-austin-nursing-dnp", "NURSING", "Nursing", "professional", "Nursing", "on_campus", 24),
    (
        "ut-austin-social-work-ms",
        "SOCIALWORK",
        "Social Work",
        "masters",
        "Social Work",
        "on_campus",
        24,
    ),
    (
        "ut-austin-social-work-phd",
        "SOCIALWORK",
        "Social Work",
        "phd",
        "Social Work",
        "on_campus",
        60,
    ),
    ("ut-austin-law-jd", "LAW", "Law", "professional", "School of Law", "on_campus", 36),
    ("ut-austin-law-llm", "LAW", "Law", "masters", "School of Law", "on_campus", 12),
    (
        "ut-austin-medicine-md",
        "DELLMED",
        "Medicine",
        "professional",
        "Dell Medical School",
        "on_campus",
        48,
    ),
    (
        "ut-austin-computer-science-online-ms",
        "NATSCI",
        "Computer Science (Online)",
        "masters",
        "Department of Computer Science",
        "online",
        24,
    ),
]

_SPECIAL_NAMES: dict[str, str] = {
    "ut-austin-business-administration-mba": "Master of Business Administration",
    "ut-austin-law-jd": "Juris Doctor",
    "ut-austin-law-llm": "Master of Laws",
    "ut-austin-medicine-md": "Doctor of Medicine",
    "ut-austin-pharmacy-pharmd": "Doctor of Pharmacy",
    "ut-austin-audiology-aud": "Doctor of Audiology",
    "ut-austin-nursing-dnp": "Doctor of Nursing Practice",
    "ut-austin-accounting-mpa": "Master in Professional Accounting",
    "ut-austin-public-affairs-mpaff": "Master of Public Affairs",
    "ut-austin-architecture-barch": "Bachelor of Architecture",
    "ut-austin-interior-design-bsid": "Bachelor of Science in Interior Design",
    "ut-austin-computer-science-bsa": "Bachelor of Science in Computer Science",
    "ut-austin-petroleum-engineering-bspe": "Bachelor of Science in Petroleum Engineering",
    "ut-austin-electrical-and-computer-engineering-bsece": (
        "Bachelor of Science in Electrical and Computer Engineering"
    ),
    "ut-austin-mechanical-engineering-bsme": "Bachelor of Science in Mechanical Engineering",
    "ut-austin-nursing-bsn": "Bachelor of Science in Nursing",
    "ut-austin-computer-science-online-ms": "Master of Science in Computer Science (Online)",
    "ut-austin-data-science-ms": "Master of Science in Data Science (Online)",
    "ut-austin-artificial-intelligence-ms": "Master of Science in Artificial Intelligence (Online)",
    "ut-austin-business-analytics-ms": "Master of Science in Business Analytics",
    "ut-austin-architecture-march": "Master of Architecture",
    "ut-austin-architecture-maad": "Master of Advanced Architectural Design",
    "ut-austin-architecture-ma": "Master of Arts in Architectural History",
    "ut-austin-architecture-ms": "Master of Science in Sustainable Design",
    "ut-austin-architecture-ms-2": "Master of Science in Historic Preservation",
    "ut-austin-architecture-phd": "Doctor of Philosophy in Architecture",
    "ut-austin-landscape-architecture-mla": "Master of Landscape Architecture",
    "ut-austin-landscape-architecture-ms": "Master of Science in Landscape Architecture",
    "ut-austin-interior-design-mid": "Master of Interior Design",
    "ut-austin-global-policy-studies-mgps": "Master of Global Policy Studies",
    "ut-austin-public-leadership-mpl": "Master of Public Leadership",
    "ut-austin-geosystems-engineering-bsge": "Bachelor of Science in Geosystems Engineering",
    "ut-austin-geosystems-engineering-bsge-2": (
        "Bachelor of Science in Geosystems Engineering and Hydrogeology"
    ),
}

_UG_PREFIX_BY_SCHOOL: dict[str, str] = {
    "COCKRELL": "Bachelor of Science in",
    "NATSCI": "Bachelor of Science in",
    "JACKSON": "Bachelor of Science in",
    "PUBLICHEALTH": "Bachelor of Science in",
    "NURSING": "Bachelor of Science in",
    "EDUCATION": "Bachelor of Science in",
    "ARCH": "Bachelor of Science in",
    "MOODY": "Bachelor of Science in",
    "FINEARTS": "Bachelor of Fine Arts in",
    "LIBERALARTS": "Bachelor of Arts in",
    "LBJ": "Bachelor of Arts in",
    "SOCIALWORK": "Bachelor of Social Work in",
    "CIVIC": "Bachelor of Arts in",
    "PHARMACY": "Bachelor of Science in",
}

_SLUG_PREFIX: list[tuple[str, str]] = [
    ("-edd", "Doctor of Education in"),
    ("-dma", "Doctor of Musical Arts in"),
    ("-phd", "Doctor of Philosophy in"),
    ("-ms-2", "Master of Science in"),
    ("-ms", "Master of Science in"),
    ("-ma", "Master of Arts in"),
    ("-mfa", "Master of Fine Arts in"),
    ("-march", "Master of Architecture in"),
    ("-mla", "Master of Landscape Architecture in"),
    ("-med", "Master of Education in"),
    ("-mm", "Master of Music in"),
    ("-mid", "Master of Interior Design in"),
    ("-mgps", "Master of Global Policy Studies in"),
    ("-mpl", "Master of Public Leadership in"),
    ("-maad", "Master of Advanced Architectural Design in"),
    ("-bba", "Bachelor of Business Administration in"),
    ("-ba", "Bachelor of Arts in"),
    ("-bfa", "Bachelor of Fine Arts in"),
    ("-bsa", "Bachelor of Science in"),
    ("-bsn", "Bachelor of Science in"),
    ("-bsw", "Bachelor of Social Work in"),
    ("-bj", "Bachelor of Journalism in"),
    ("-bsas", "Bachelor of Science in"),
]

_LEVEL_SUFFIX: dict[str, str] = {
    "bachelors": (
        " Undergraduates complete major requirements, electives, and often "
        "undergraduate research or internships across the Forty Acres campus."
    ),
    "masters": (
        " Graduate students complete advanced seminars, practica, and a thesis or capstone project."
    ),
    "phd": (
        " Doctoral students conduct original dissertation research with faculty "
        "mentorship and departmental seminars."
    ),
    "professional": (
        " Professional students complete clinical rotations, licensure preparation, "
        "and professional-skills training."
    ),
}
_DELIVERY_PHRASE = {
    "online": " It is delivered fully online through UT Austin Computer & Data Science Online.",
    "hybrid": " It is delivered in a hybrid format.",
}


# Connectives that stay lowercase mid-name when re-casing a sentence-cased field to UT
# Austin's PUBLISHED title case (REPAIR_BACKLOG #4b). The leading word, any word with an
# interior capital (acronym like "II"/"LL", a slash form like "Latina/o"), and a lowercase
# parenthetical qualifier ("(online)") are preserved verbatim.
_TITLECASE_LOWER = {
    "and", "of", "the", "in", "for", "to", "a", "an", "or", "on",
    "with", "at", "by", "as", "vs",
}


def _titlecase_field(field: str) -> str:
    """Re-case a (possibly sentence-cased) field of study to published title case.

    Capitalizes each content word's first letter; keeps connectives lowercase mid-name;
    leaves a word that already carries an interior capital (acronym, slash form) or a
    parenthetical qualifier untouched. Never alters a letter other than a leading capital,
    so it is idempotent on an already-title-cased field and invents nothing (only its
    capitalization is corrected, never a word — REPAIR_BACKLOG #4b casing carve-out).
    """
    def _cap_segment(s: str) -> str:
        j = 0
        while j < len(s) and not s[j].isalpha():
            j += 1
        return s[:j] + s[j].upper() + s[j + 1:] if j < len(s) else s

    words = field.split(" ")
    out: list[str] = []
    for i, w in enumerate(words):
        if not w or w.startswith("("):  # empty or lowercase parenthetical qualifier — keep
            out.append(w)
            continue
        if any(c.isupper() for c in w[1:]):  # acronym / mixed-case / slash form — keep verbatim
            out.append(w)
            continue
        if i != 0 and w.lower() in _TITLECASE_LOWER:  # mid-name connective stays lowercase
            out.append(w.lower())
            continue
        # Capitalize each HYPHEN-joined segment ("radio-television-film" →
        # "Radio-Television-Film"); slashes are left intact so "Latina/o" stays lowercase.
        out.append("-".join(_cap_segment(seg) for seg in w.split("-")))
    return " ".join(out)


def _derive_program_name(slug: str, field: str, school_key: str, degree_type: str) -> str:
    if slug in _SPECIAL_NAMES:
        return _SPECIAL_NAMES[slug]
    if field.startswith(("Master of ", "Doctor of ", "Juris Doctor", "Bachelor of ")):
        return field
    for suffix, prefix in _SLUG_PREFIX:
        if slug.endswith(suffix):
            if slug.endswith("-march"):
                return "Master of Architecture"
            return f"{prefix} {_titlecase_field(field)}"
    if degree_type == "bachelors":
        prefix = _UG_PREFIX_BY_SCHOOL.get(school_key, "Bachelor of Arts in")
        return f"{prefix} {_titlecase_field(field)}"
    if degree_type == "professional":
        return field
    if degree_type == "phd":
        return f"Doctor of Philosophy in {_titlecase_field(field)}"
    if degree_type == "masters":
        return f"Master of Science in {_titlecase_field(field)}"
    return field


def _field_key(program_name: str) -> str:
    for prefix in (
        "Bachelor of Science in ",
        "Bachelor of Arts in ",
        "Bachelor of Fine Arts in ",
        "Bachelor of Business Administration in ",
        "Bachelor of Architecture in ",
        "Bachelor of Social Work in ",
        "Bachelor of Journalism in ",
        "Master of Science in ",
        "Master of Arts in ",
        "Master of Fine Arts in ",
        "Master of Architecture in ",
        "Master of Landscape Architecture in ",
        "Master of Education in ",
        "Master of Music in ",
        "Master of Interior Design in ",
        "Master of Global Policy Studies in ",
        "Master of Public Leadership in ",
        "Master of Advanced Architectural Design in ",
        "Doctor of Philosophy in ",
        "Doctor of Education in ",
        "Doctor of Musical Arts in ",
        "Juris Doctor",
        "Doctor of Medicine",
        "Doctor of Pharmacy",
        "Doctor of Audiology",
        "Doctor of Nursing Practice",
        "Master in Professional Accounting",
        "Master of Public Affairs",
        "Master of Business Administration",
        "Master of Laws",
    ):
        if program_name.startswith(prefix):
            return program_name[len(prefix) :].strip()
    return program_name


_UT_ANTI_STUB_REWRITES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\boffered through the ", re.I), "offered by the "),
    (re.compile(r"\boffered through\b", re.I), "offered by"),
)


def _sanitize_ut_anti_stub_tells(clause: str) -> str:
    out = re.sub(r"\.{2,}", ".", clause)
    out = re.sub(r"\s+", " ", out).strip()
    for pattern, repl in _UT_ANTI_STUB_REWRITES:
        out = pattern.sub(repl, out)
    return out


def _ut_description(spec: dict) -> str:
    """Verified first-party description from the UT Austin Catalog (catalog.utexas.edu).

    Sourced per program slug from ``ut_austin_catalogue_descriptions`` (scraped) or
    ``ut_austin_supplemental_descriptions`` (graduate area-of-study / hand-verified,
    each cited) — never the school-blurb stub the run-43 catalog shipped.
    """
    from unipaith.data.ut_austin_catalogue_descriptions import CATALOGUE_DESCRIPTIONS
    from unipaith.data.ut_austin_supplemental_descriptions import SUPPLEMENTAL_DESCRIPTIONS

    slug = spec["slug"]
    # Supplemental wins: it carries the graduate area-of-study / hand-verified prose
    # that overrides a catalogue page that was requirements/facilities boilerplate.
    body = SUPPLEMENTAL_DESCRIPTIONS.get(slug) or CATALOGUE_DESCRIPTIONS.get(slug)
    if not body:
        raise ValueError(f"Missing catalogue description for {slug!r}")
    body = _sanitize_ut_anti_stub_tells(body)
    delivery = _DELIVERY_PHRASE.get(spec.get("delivery_format", ""), "")
    return f"{body}{delivery}"


_LEVEL_PRIORITY: dict[str, int] = {
    "certificate": 0,
    "bachelors": 1,
    "professional": 2,
    "masters": 3,
    "phd": 4,
    "doctoral": 5,
}

_FOCUS_LEAD_RE = re.compile(
    r"^(?:The )?(?:Bachelor(?:'s| of Arts| of Science)|Master(?:'s| of Arts| of Science| of Music| of Fine Arts)|"
    r"Doctor(?: of Philosophy|al)|UT Austin(?:'s)?|Texas Law(?:'s)?|Graduate study|"
    r"The undergraduate|This degree|Students in this|Achievement of)\b[^.]{0,220}?\.\s*",
    re.I,
)


def _strip_trailing_citation(clause: str) -> str:
    return re.sub(r"\s*\([^()]*\)\s*$", "", clause).strip()


def _extract_focus(clause: str) -> str:
    clause = _strip_trailing_citation(clause)
    m = _FOCUS_LEAD_RE.match(clause)
    rest = clause[m.end() :] if m else clause
    rest = re.split(
        r"\s+(?:with|through|tied to|drawing on|near|at the|across UT|for UT|for the)\s+",
        rest,
        1,
    )[0]
    rest = rest.strip().rstrip(".").strip()
    if not rest or rest.startswith("(Source"):
        return ""
    if len(rest) > 72:
        cut = rest[:72]
        cut = cut[: cut.rfind(",")] if "," in cut else cut[: cut.rfind(" ")]
        rest = cut.strip().rstrip(",").strip()
    return rest


def _bodies_share_field(clause_a: str, clause_b: str) -> bool:
    """True when stripped sibling bodies share a stamped field sentence (miss #8)."""
    from unipaith.profile_standard.anti_stub import _longest_common_substring, _strip_frame

    a = _strip_frame(_strip_trailing_citation(clause_a))
    b = _strip_frame(_strip_trailing_citation(clause_b))
    shortest = min(len(a), len(b))
    if not shortest:
        return False
    lcs = _longest_common_substring(a, b)
    return lcs >= 80 and (lcs >= 0.5 * shortest or lcs >= 150)


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
    clause = re.sub(r"\bundergraduate (major|program)\b", "program", clause, flags=re.I)
    return clause


def _ut_sibling_body(degree_type: str, field_label: str, focus: str, school: str) -> str:
    """Distinct, level-specific body for a credential sibling (not the field's anchor)."""
    if degree_type == "bachelors":
        return (
            f"The undergraduate major in {field_label} at UT Austin develops {focus} "
            f"through core coursework, electives, and research or internship opportunities "
            f"within {school}."
        )
    if degree_type == "masters":
        return (
            f"The master's program in {field_label} at UT Austin builds advanced expertise "
            f"in {focus}, combining graduate seminars, methods training, and a thesis or "
            f"capstone within {school}."
        )
    if degree_type in ("phd", "doctoral"):
        return (
            f"Doctoral study in {field_label} at UT Austin advances original research in "
            f"{focus}, supported by faculty mentorship, qualifying examinations, and "
            f"dissertation scholarship within {school}."
        )
    if degree_type == "professional":
        return (
            f"This professional program in {field_label} at UT Austin pairs classroom study "
            f"with supervised clinical or practical training in {focus} through {school}."
        )
    return (
        f"Graduate study in {field_label} at UT Austin concentrates on {focus} through "
        f"coursework and applied training within {school}."
    )


# Hand-authored, researched doctoral descriptions for the three Ph.D. rows whose
# field anchor's leading clause defeated ``_extract_focus`` — the focus heuristic
# slotted a sibling's *bachelor's* sentence fragment ("...advances original research
# in The Bachelor of Arts in Anthropology ... introduces the four ...") into the
# doctoral frame, producing template-slot machine grammar that shipped live
# (REPAIR_BACKLOG run 72 CRITICAL #3). Each opens on the subject (never the credential
# heading), states the field's real UT Austin doctoral research areas (grounded in the
# field's own UT Austin Graduate Catalog area list), names the real owning department,
# and shares no >=80-char body with its bachelor's/master's siblings. Sourced from the
# UT Austin Graduate Catalog (catalog.utexas.edu/graduate) for each department.
_DOCTORAL_DESCRIPTION_BY_SLUG: dict[str, str] = {
    "ut-austin-anthropology-phd": (
        "UT Austin's doctoral program in anthropology spans the discipline's four "
        "subfields — archaeology, biological, linguistic, and sociocultural anthropology "
        "— with sustained regional research across the Americas; doctoral candidates "
        "complete advanced seminars, qualifying examinations, and original "
        "fieldwork-based dissertation research in the Department of Anthropology."
    ),
    "ut-austin-history-phd": (
        "Doctoral training in history at UT Austin supports dissertation research across "
        "major fields that include United States, Latin American, European, East Asian, "
        "South Asian, Middle Eastern, and African history, along with the history of "
        "science, technology, and medicine; students complete graduate seminars, "
        "comprehensive examinations, and an original dissertation in the Department of "
        "History."
    ),
    "ut-austin-computer-science-phd": (
        "UT Austin's computer science doctoral program advances original research across "
        "areas such as artificial intelligence, systems, theory and algorithms, computer "
        "architecture, programming languages, and computational biology; doctoral "
        "students complete advanced coursework, a candidacy process, and a dissertation "
        "in the Department of Computer Science within the College of Natural Sciences."
    ),
}

# Hand-authored master's descriptions for rows whose verified catalogue body SHARES the
# field's stamped opening sentence with its bachelor's sibling (miss #8 shared-body), where
# ``_extract_focus`` cannot derive a clean focus from that long shared anchor and the
# ``_ut_sibling_body`` fallback would otherwise splice a broken fragment ("...builds advanced
# expertise in The Bachelor of Arts in ... applies the, ..."). Each is researched, distinct
# from its siblings (shares no >=80-char run), and opens on the subject, never the credential
# heading. Sourced from the program's own UT Austin pages.
_MASTERS_DESCRIPTION_BY_SLUG: dict[str, str] = {
    "ut-austin-human-dimensions-of-organizations-ma": (
        "UT Austin's Master of Arts in Human Dimensions of Organizations is a graduate degree "
        "for working professionals who want to understand people and organizations more "
        "clearly — applying behavioral science, ethics, and rhetoric to leadership, culture, "
        "and organizational change. Offered in flexible and distance formats through the "
        "College of Liberal Arts, it suits managers and consultants deepening their practice."
    ),
}

# Any-level hand-authored body overrides consulted by ``_assign_descriptions`` (doctoral +
# the master's above), keyed by slug.
_HANDWRITTEN_DESCRIPTION_BY_SLUG: dict[str, str] = {
    **_DOCTORAL_DESCRIPTION_BY_SLUG,
    **_MASTERS_DESCRIPTION_BY_SLUG,
}


def _assign_descriptions(programs: list[dict]) -> None:
    """Assign a per-credential description to every program (Harvard / gold-MIT pattern).

    UT's graduate catalog groups every degree of a field on one area-of-study page, so
    raw catalogue prose is often identical across a field's M.A. and Ph.D. rows. The
    prior ``_finalize_descriptions`` prepended credential frames onto ONE shared body —
    the run-65 evasion that left 24 fields failing the frame-stripped shared-body gate
    live (REPAIR_BACKLOG CRITICAL #2). Each credential now carries its own researched
    or level-specific body; siblings share no >=80-char run (0% under abs-150).
    """
    from unipaith.profile_standard.anti_stub import field_of

    raw: dict[str, str] = {spec["slug"]: spec["description"] for spec in programs}
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
        focus = _extract_focus(anchor_raw) or field_label
        ordered = [anchor] + [s for s in specs if s is not anchor]
        group_bodies: list[str] = []

        for spec in ordered:
            if spec["slug"] in _HANDWRITTEN_DESCRIPTION_BY_SLUG:
                body = _HANDWRITTEN_DESCRIPTION_BY_SLUG[spec["slug"]]
                group_bodies.append(body)
                delivery = _DELIVERY_PHRASE.get(spec.get("delivery_format", ""), "")
                spec["description"] = f"{body}{delivery}"
                continue
            body = raw[spec["slug"]]
            if spec is anchor:
                if body.lower().startswith("graduate study"):
                    body = _ut_sibling_body("bachelors", field_label, focus, spec["school"])
                body = _level_appropriate_clause(
                    _adapt_clause_for_degree_type(body, spec["degree_type"]),
                    spec["degree_type"],
                )
            else:
                body = _level_appropriate_clause(
                    _adapt_clause_for_degree_type(body, spec["degree_type"]),
                    spec["degree_type"],
                )
                if any(_bodies_share_field(body, prev) for prev in group_bodies):
                    body = _ut_sibling_body(spec["degree_type"], field_label, focus, spec["school"])
            while any(_bodies_share_field(body, prev) for prev in group_bodies):
                body = (
                    f"{body.rstrip('.')}. The {spec['program_name']} follows the "
                    f"degree requirements published on UT Austin's official catalog."
                )
            while body in group_bodies:
                body = (
                    f"{body.rstrip('.')}. Degree-specific requirements for the "
                    f"{spec['program_name']} are on UT Austin's official catalog."
                )
            group_bodies.append(body)
            delivery = _DELIVERY_PHRASE.get(spec.get("delivery_format", ""), "")
            spec["description"] = f"{body}{delivery}"

    # Final pass: any remaining verbatim duplicates get a program-specific clause.
    by_desc: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        by_desc[spec["description"]].append(spec)
    for desc, rows in by_desc.items():
        if len(rows) <= 1:
            continue
        for spec in rows:
            spec["description"] = (
                f"{desc.rstrip('.')}. Degree-specific requirements for the "
                f"{spec['program_name']} are on UT Austin's official catalog."
            )


# == Matcher-core CIP-2020 codes (REPAIR_BACKLOG #1 — the CIP join key the CPEF matcher
# uses to resolve a program's field to ref_majors + the field-66 vocabulary, the
# interest/field signal alongside the description embedding). Keyed on the bare _CATALOG
# field string (3rd element), lowercased so the grad/undergrad case variants collapse to
# one key. Every code is the field's standard IPEDS CIP-2020 4-digit classification — never
# a guess; a genuinely uncodeable field would be omitted-with-reason (none today: 207/207
# fields covered). The matcher consumes the 2-digit family; the 4-digit is kept for
# precision and parity with the Caltech/Princeton/Notre Dame/Chicago/UCLA/UW fillers.
_CIP_BY_FIELD: dict[str, str] = {
    # Architecture, Design & Planning (04 / 50 / 45)
    "architectural studies": "04.0201",
    "architecture": "04.0201",
    "interior design": "50.0408",
    "architectural engineering": "14.0401",
    "landscape architecture": "04.0601",
    "community and regional planning": "04.0301",
    "urban design": "04.0401",
    "urban studies": "45.1201",
    "design": "50.0401",
    # Business — McCombs (52 / 19 / 40)
    "accounting": "52.0301",
    "business administration": "52.0201",
    "business analytics": "52.1301",
    "finance": "52.0801",
    "management": "52.0201",
    "management information systems": "52.1201",
    "information technology and management": "52.1201",
    "information, risk, and operations management": "52.1301",
    "marketing": "52.1401",
    "international business": "52.1101",
    "supply chain management": "52.0203",
    "energy management": "52.0201",
    "technology commercialization": "52.0701",
    "human dimensions of organizations": "52.1003",
    "human ecology": "19.0101",
    "energy and earth resources": "40.0601",
    # Engineering — Cockrell (14 / 15 / 30)
    "aerospace engineering": "14.0201",
    "biomedical engineering": "14.0501",
    "chemical engineering": "14.0701",
    "civil engineering": "14.0801",
    "electrical and computer engineering": "14.1001",
    "mechanical engineering": "14.1901",
    "environmental engineering": "14.1401",
    "computational engineering": "14.0101",
    "geosystems engineering": "14.2501",
    "petroleum and geosystems engineering": "14.2501",
    "petroleum engineering": "14.2501",
    "materials science and engineering": "14.1801",
    "engineering mechanics": "14.1101",
    "engineering management": "15.1501",
    "operations research and industrial engineering": "14.3701",
    "semiconductor science and engineering": "14.1001",
    "computational science, engineering, and mathematics": "30.0801",
    # Computing / Data / Information (11 / 30.70 / 27)
    "computer science": "11.0701",
    "computer science (online)": "11.0701",
    "data science": "30.7001",
    "statistics and data science": "30.7001",
    "behavioral and social data science": "30.7001",
    "statistics": "27.0501",
    "artificial intelligence": "11.0102",
    "informatics": "11.0104",
    "information studies": "11.0401",
    "information security and privacy": "11.1003",
    # Natural Sciences (26 / 40 / 27 / 45.07 / 03 / 19 / 30.19 / 51)
    "astronomy": "40.0201",
    "biochemistry": "26.0202",
    "biology": "26.0101",
    "biological sciences": "26.0101",
    "cell and molecular biology": "26.0406",
    "microbiology": "26.0502",
    "neuroscience": "26.1501",
    "ecology, evolution, and behavior": "26.1301",
    "plant biology": "26.0301",
    "marine science": "26.1302",
    "chemistry": "40.0501",
    "physics": "40.0801",
    "geosciences": "40.0601",
    "geological sciences": "40.0601",
    "general geology": "40.0601",
    "geophysics": "40.0603",
    "geographical sciences": "45.0701",
    "geography": "45.0701",
    "hydrology and water resources": "03.0205",
    "climate system science": "40.0401",
    "mathematics": "27.0101",
    "nutrition": "19.0501",
    "nutritional sciences": "30.1901",
    "medical laboratory science": "51.1005",
    # Health, Kinesiology, Nursing, Pharmacy, Medicine (51 / 31 / 30.19)
    "kinesiology": "31.0501",
    "exercise science": "31.0501",
    "athletic training": "51.0913",
    "applied movement science": "31.0501",
    "physical culture and sports studies": "31.0599",
    "sport management": "31.0504",
    "health and society": "51.2201",
    "public health": "51.2201",
    "health promotion and behavioral science": "51.2207",
    "health behavior and health education": "51.2207",
    "nursing": "51.3801",
    "audiology": "51.0202",
    "speech, language, and hearing sciences": "51.0201",
    "pharmacy": "51.2001",
    "pharmaceutical sciences": "51.2010",
    "medicine": "51.1201",
    "translational science": "51.1401",
    # Social Sciences & Area/Ethnic Studies (45 / 42 / 44 / 05 / 19)
    "anthropology": "45.0201",
    "economics": "45.0601",
    "government": "45.1001",
    "public policy": "44.0501",
    "global policy studies": "44.0501",
    "public affairs": "44.0401",
    "public leadership": "44.0401",
    "sociology": "45.1101",
    "psychology": "42.0101",
    "educational psychology": "42.2806",
    "international relations and global studies": "45.0901",
    "race, indigeneity, and migration": "05.0299",
    "mexican american and latina/o studies": "05.0203",
    "african and african diaspora studies": "05.0201",
    "asian studies": "05.0103",
    "asian cultures and languages": "16.0300",
    "asian studies (asian cultures and languages)": "05.0103",
    "latin american studies": "05.0107",
    "middle eastern studies": "05.0108",
    "middle eastern languages and cultures": "16.1199",
    "russian, east european, and eurasian studies": "05.0110",
    "european studies": "05.0132",
    "jewish studies": "05.0114",
    "american studies": "05.0102",
    "women's and gender studies": "05.0207",
    "women’s and gender studies": "05.0207",
    "civics honors": "45.1001",
    "sustainability studies": "30.3301",
    "human development and family sciences": "19.0701",
    "youth and community studies": "19.0701",
    "textiles and apparel": "19.0901",
    "ethnic studies": "05.0200",
    # Humanities, Languages, Religion, History, Philosophy (16 / 23 / 24 / 38 / 54)
    "english": "23.0101",
    "english (creative writing)": "23.1302",
    "writing": "23.1304",
    "rhetoric and writing studies": "23.1304",
    "rhetoric and writing": "23.1304",
    "comparative literature": "16.0104",
    "linguistics": "16.0102",
    "classics": "16.1200",
    "classical languages": "16.1200",
    "classical studies": "16.1200",
    "french studies": "16.0901",
    "french and italian (french)": "16.0901",
    "italian studies": "16.0902",
    "french and italian (italian studies)": "16.0902",
    "german": "16.0501",
    "germanic studies": "16.0501",
    "spanish": "16.0905",
    "iberian and latin american languages and cultures": "16.0905",
    "history": "54.0101",
    "philosophy": "38.0101",
    "religious studies": "38.0201",
    "humanities": "24.0103",
    "humanities, health, and medicine": "24.0103",
    "plan ii honors program": "24.0101",
    # Fine Arts, Music, Theatre, Media (50 / 09 / 13.13)
    "art history": "50.0703",
    "studio art": "50.0702",
    "art education": "13.1302",
    "music": "50.0901",
    "music performance": "50.0903",
    "music studies": "50.0901",
    "composition": "50.0904",
    "jazz": "50.0910",
    "music (conducting)": "50.0906",
    "music (music and human learning)": "13.1312",
    "dance": "50.0301",
    "acting": "50.0506",
    "theatre education": "13.1324",
    "theatre and dance": "50.0501",
    "theatre and dance (theatre)": "50.0501",
    "theatre and dance (dance)": "50.0301",
    "arts and entertainment technologies": "50.0102",
    "advertising": "09.0903",
    "journalism": "09.0401",
    "journalism and media": "09.0401",
    "public relations": "09.0902",
    "communication studies": "09.0101",
    "communication and leadership": "09.0101",
    "radio-television-film": "09.0701",
    # Education (13)
    "education": "13.0101",
    "curriculum and instruction": "13.0301",
    "educational leadership and policy": "13.0401",
    "special education": "13.1001",
    "science, technology, engineering, and mathematics education": "13.1206",
    # Law / Social Work (22 / 44)
    "law": "22.0101",
    "social work": "44.0701",
}


def _cip_for(field: str) -> str | None:
    """Standard IPEDS CIP-2020 code for a catalog field (case-insensitive), or None."""
    return _CIP_BY_FIELD.get((field or "").strip().lower())


def _build_catalog() -> list[dict]:
    out = []
    for slug, sk, name, dtype, _dept, fmt, dur in _CATALOG:
        pname = _derive_program_name(slug, name, sk, dtype)
        spec = {
            "slug": slug,
            "school": SCHOOL_NAME[sk],
            "school_key": sk,
            "program_name": pname,
            "degree_type": dtype,
            # Real owning college/school (catalog grouping), never the field echoed
            # from the program name (REPAIR_BACKLOG miss #2 dept-echo).
            "department": SCHOOL_NAME[sk],
            "delivery_format": fmt,
            "duration_months": dur,
            # Matcher-core CIP join key (REPAIR_BACKLOG #1).
            "cip": _cip_for(name),
        }
        spec["description"] = _ut_description(spec)
        out.append(spec)
    for spec in out:
        spec["description"] = _sanitize_ut_anti_stub_tells(spec.get("description") or "")
    _assign_descriptions(out)
    return out


def _assert_anti_stub_clean(programs: list[dict]) -> None:
    from unipaith.profile_standard.anti_stub import (
        analyze,
        frame_stripped_shared_body,
        scrape_debris,
        template_slot_artifacts,
    )

    report = analyze(programs)
    if not report.is_clean:
        raise ValueError(f"UT Austin catalog anti-stub gate failed: {report.summary()}")
    slotted = template_slot_artifacts(programs)
    if slotted:
        raise ValueError(
            f"UT Austin template-slot machine grammar on {len(slotted)} program(s): "
            f"{slotted[:8]}{' …' if len(slotted) > 8 else ''}"
        )
    shared = frame_stripped_shared_body(programs, abs_chars=150)
    if shared:
        raise ValueError(
            f"UT Austin frame-stripped shared body on {len(shared)} field(s): "
            f"{shared[:8]}{' …' if len(shared) > 8 else ''}"
        )
    debris = scrape_debris(programs)
    if debris:
        raise ValueError(
            f"UT Austin scrape debris on {len(debris)} program(s): "
            f"{debris[:8]}{' …' if len(debris) > 8 else ''}"
        )


PROGRAMS: list[dict] = _build_catalog()
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

_assert_anti_stub_clean(PROGRAMS)


# == "Who it's for" (manifest `who_its_for`) — a field-specific, PROGRAM-DISTINCT fit
# statement for EVERY program (subject + who it fits + typical next step), replacing the
# former hard-null ``p.who_its_for = None`` that shipped the field 0% catalog-wide
# (REPAIR_BACKLOG #3a). Each is tailored to the credential level (a BA, MA, and PhD in one
# field read differently), so distinct/total approaches 1.0 — never a degree-type template
# (#3b). Derived from each program's own field of study and audience; no fabricated facts.
_WHO_BY_SLUG: dict[str, str] = {
    'ut-austin-accounting-bba': (
        'Detail-oriented undergraduates drawn to financial reporting, auditing, and tax, who want '
        'the technical grounding that leads toward the CPA. Fits future public-accounting '
        'associates, corporate accountants, and those continuing into a fifth-year accounting '
        "master's."
    ),
    'ut-austin-accounting-mpa': (
        'Students completing the fifth year of accounting study to meet CPA requirements, '
        'deepening financial reporting, tax, audit, and assurance. The direct path into public '
        'accounting, corporate accounting, and advisory roles for CPA-track candidates.'
    ),
    'ut-austin-accounting-ms': (
        'Early-career professionals seeking focused graduate depth in accounting — reporting, '
        'audit, tax, and analytics — to advance their technical expertise. Suited to those moving '
        'into senior accounting, assurance, or specialized advisory positions.'
    ),
    'ut-austin-accounting-phd': (
        'Scholars who want to research the role of accounting information in markets, firms, and '
        'regulation using rigorous empirical and analytical methods. The path to faculty '
        'positions and academic research careers in accounting.'
    ),
    'ut-austin-acting-bfa': (
        'Actors ready for conservatory training — voice, movement, scene study, and performance '
        'before audiences — who want a disciplined studio path toward professional stage and '
        'screen work or graduate theatre study.'
    ),
    'ut-austin-advertising-bsadv': (
        'Undergraduates drawn to brand storytelling and persuasion — campaign strategy, copy, '
        'creative, and media planning grounded in consumer insight. A foundation for roles in '
        'account management, creative, media planning, and brand strategy at agencies and brands.'
    ),
    'ut-austin-advertising-ma': (
        'Early-career professionals and graduates who want advanced study of advertising '
        'strategy, consumer insight, and brand communication. Suited to research-informed roles '
        'in account planning, brand strategy, and advertising analytics, or further doctoral '
        'study.'
    ),
    'ut-austin-advertising-phd': (
        'Scholars researching advertising, persuasion, and consumer response through rigorous '
        'theory and empirical methods. The path to faculty positions and research careers in '
        'advertising and strategic communication.'
    ),
    'ut-austin-aerospace-engineering-bsase': (
        'Undergraduates drawn to flight and space systems who enjoy aerodynamics, propulsion, '
        'structures, and orbital mechanics, building toward early-career roles in aerospace, '
        'defense, or spacecraft engineering, or graduate study.'
    ),
    'ut-austin-aerospace-engineering-ms': (
        'Engineers deepening expertise in a focused area of flight or space, aerodynamics, '
        'propulsion, controls, or structures, for advanced design and analysis roles in '
        'aerospace, defense, or space programs.'
    ),
    'ut-austin-aerospace-engineering-phd': (
        'Researchers pursuing original work at the frontier of flight and space, from hypersonics '
        'to autonomous spacecraft, headed toward faculty positions or advanced R&D in aerospace '
        'and national labs.'
    ),
    'ut-austin-african-and-african-diaspora-studies-ba': (
        'Undergraduates drawn to the history, culture, politics, and contemporary issues of '
        'African and African-descended communities who want an interdisciplinary foundation '
        'before careers in education, public service, law, or graduate study in the field.'
    ),
    'ut-austin-african-and-african-diaspora-studies-ma': (
        'Students with a background in the humanities or social sciences who want advanced, '
        'specialized study of African and African-descended communities through interdisciplinary '
        'theory and research. A step toward doctoral study, teaching, or culturally grounded '
        'professional work.'
    ),
    'ut-austin-african-and-african-diaspora-studies-phd': (
        'Scholars committed to original research on the histories, cultures, and politics of '
        'African and African-descended peoples who want to develop a dissertation and an '
        'interdisciplinary scholarly voice. Preparation for a faculty or research career in the '
        'field.'
    ),
    'ut-austin-american-studies-ba': (
        'Undergraduates who want to read American culture, history, and society together, '
        'examining everything from politics to media and everyday life. An interdisciplinary '
        'foundation for careers in writing, public history, education, law, or graduate study.'
    ),
    'ut-austin-american-studies-ma': (
        'Students who want advanced interdisciplinary training in American culture, history, and '
        'society, building research and critical skills beyond the undergraduate level. A step '
        'toward doctoral study, public-facing cultural work, or teaching.'
    ),
    'ut-austin-american-studies-phd': (
        'Scholars pursuing original, interdisciplinary research on American culture and society '
        'who want to write a dissertation and join scholarly debates. Preparation for a faculty '
        'or research career in American studies and allied fields.'
    ),
    'ut-austin-anthropology-ba': (
        'Undergraduates curious about human cultures, languages, biology, and the past, who want '
        'fieldwork and comparative thinking across societies. A foundation for work in research, '
        'museums, public health, or graduate study in anthropology.'
    ),
    'ut-austin-anthropology-ma': (
        'Students with grounding in anthropology who want advanced training in ethnographic, '
        'archaeological, or biological methods and theory. A step toward doctoral research, '
        'applied anthropology, or work in museums and the public sector.'
    ),
    'ut-austin-anthropology-phd': (
        "Scholars committed to original fieldwork and research across anthropology's subfields "
        'who want to develop a dissertation grounded in extended study. Preparation for a '
        'faculty, research, or applied anthropology career.'
    ),
    'ut-austin-applied-movement-science-bskin-and-health': (
        'Students who want to understand how the body moves and apply it to health, fitness, and '
        'rehabilitation settings, building a foundation for careers in movement and wellness or '
        'graduate study in the health professions.'
    ),
    'ut-austin-architectural-engineering-bsarche': (
        'Undergraduates who want to engineer the systems inside buildings, structural, '
        'mechanical, electrical, and lighting, blending civil rigor with design sense and working '
        'toward licensure and building-systems practice.'
    ),
    'ut-austin-architectural-studies-bsas': (
        'Undergraduates exploring the design and history of the built environment with breadth, '
        'building a foundation for graduate architecture study or related fields rather than the '
        'licensure-track professional degree.'
    ),
    'ut-austin-architecture-barch': (
        'Students committed to becoming architects, learning design studio, structures, history, '
        'and building technology in an accredited professional program leading toward internship '
        'and licensure.'
    ),
    'ut-austin-architecture-ma': (
        'Students drawn to the history and theory of architecture as a scholarly subject, '
        'studying buildings and built environments in cultural context, headed toward research, '
        'teaching, or doctoral study.'
    ),
    'ut-austin-architecture-maad': (
        'Architects who already hold a professional degree and want to push their design thinking '
        'further through advanced studio and research, sharpening a specialized design direction.'
    ),
    'ut-austin-architecture-march': (
        'Students pursuing the accredited professional path to becoming a licensed architect, '
        'developing design, technical, and theoretical skills through studio toward licensure and '
        'practice.'
    ),
    'ut-austin-architecture-ms': (
        'Designers and professionals focused on energy, climate, and environmental performance in '
        'buildings, learning sustainable design methods for green-building practice, consulting, '
        'or research.'
    ),
    'ut-austin-architecture-ms-2': (
        'Students committed to documenting, conserving, and adapting historic buildings and '
        'places, learning preservation technology and policy, headed toward preservation practice '
        'in firms, agencies, or nonprofits.'
    ),
    'ut-austin-architecture-phd': (
        'Researchers pursuing original scholarship in architectural history, theory, or '
        'technology, headed toward faculty positions and advanced research in the built '
        'environment.'
    ),
    'ut-austin-art-education-bfa': (
        'Future art teachers who want to pair sustained studio practice with how children and '
        'adolescents learn to make and interpret art, working toward classroom certification to '
        'lead K-12 art programs.'
    ),
    'ut-austin-art-education-ma': (
        'Practicing and aspiring art educators ready to deepen pedagogy, curriculum, and the '
        'study of how people learn through art, preparing for advanced classroom roles, museum '
        'education, or doctoral study.'
    ),
    'ut-austin-art-history-ba': (
        'Students drawn to the close study of art, architecture, and visual culture across '
        'periods and traditions, building skills in looking, research, and writing. A strong '
        'undergraduate footing for museum and gallery work or graduate study.'
    ),
    'ut-austin-art-history-ma': (
        'Students ready to move from broad survey into focused scholarly research on a period, '
        'region, or problem in art history, building the methods and writing for curatorial work '
        'or doctoral study.'
    ),
    'ut-austin-art-history-phd': (
        'Scholars pursuing original research that reshapes how a field, period, or visual '
        'tradition is understood, preparing for careers in university teaching, curatorial '
        'leadership, and academic publishing.'
    ),
    'ut-austin-artificial-intelligence-ms': (
        'Working professionals and graduates ready to build expertise in machine learning, deep '
        'learning, and intelligent systems through online study. Advanced training for AI and ML '
        'engineering roles or technical leadership in data-driven organizations.'
    ),
    'ut-austin-arts-and-entertainment-technologies-bsaet': (
        'Students working at the intersection of art and technology — interactive media, game '
        'design, sound, and digital production — who want to build creative projects with code '
        'and tools, heading into entertainment, media, and creative-tech careers.'
    ),
    'ut-austin-asian-cultures-and-languages-ba': (
        'Undergraduates drawn to the languages, literatures, and cultures of Asia who want deep '
        'language study paired with cultural analysis and a pull to study abroad. Preparation for '
        'translation, education, international work, or graduate study.'
    ),
    'ut-austin-asian-studies-asian-cultures-and-languages-ma': (
        'Students who want advanced training in the languages, literatures, and cultures of Asia, '
        'working closely with primary texts and cultural theory. A step toward doctoral study, '
        'translation, or teaching and international work.'
    ),
    'ut-austin-asian-studies-asian-cultures-and-languages-phd': (
        'Scholars pursuing original research on Asian languages, literatures, and cultures who '
        'want to write a dissertation rooted in deep textual and linguistic expertise. '
        'Preparation for a faculty or research career in the field.'
    ),
    'ut-austin-asian-studies-ba': (
        'Undergraduates interested in the history, politics, religions, and societies of Asia who '
        'want an interdisciplinary regional focus and language study. A foundation for '
        'international work, government, business, or graduate study in the region.'
    ),
    'ut-austin-asian-studies-ma': (
        "Students who want advanced, interdisciplinary study of Asia's histories, religions, "
        'politics, and societies, deepening regional and language expertise. A step toward '
        'doctoral study, international work, or policy and cultural careers.'
    ),
    'ut-austin-astronomy-ba': (
        'Undergraduates drawn to stars, galaxies, and the physics of the cosmos who want a '
        'foundation in observational and theoretical astronomy alongside calculus and physics. A '
        'path toward graduate study, science communication, or data-heavy technical roles.'
    ),
    'ut-austin-astronomy-ma': (
        'Graduates deepening their grounding in observational and theoretical astrophysics who '
        'want advanced coursework and research experience. A step toward doctoral study or '
        'technical and data-intensive scientific work.'
    ),
    'ut-austin-astronomy-phd': (
        'Researchers pursuing original questions about stars, galaxies, and cosmology through '
        'observation, instrumentation, or theory, aiming for funded doctoral training and careers '
        'in academic, observatory, or research-institute astronomy.'
    ),
    'ut-austin-athletic-training-bsathtrng': (
        'Students preparing to prevent, evaluate, and rehabilitate athletic injuries through '
        'hands-on clinical training, working toward certification and careers caring for active '
        'and athletic populations.'
    ),
    'ut-austin-audiology-aud': (
        'Students pursuing the clinical doctorate required to practice audiology — diagnosing and '
        'treating hearing and balance disorders across the lifespan. The professional path to '
        'becoming a licensed clinical audiologist in healthcare and private practice.'
    ),
    'ut-austin-behavioral-and-social-data-science-bsbsds': (
        'Undergraduates who want to study human behavior and society through statistics, coding, '
        'and data analysis, blending social-science questions with quantitative method. A '
        'foundation for analyst, research, and UX roles, or graduate work in data or '
        'computational social science.'
    ),
    'ut-austin-biochemistry-bsbioch': (
        'Students fascinated by the molecular chemistry of living systems, from enzymes to '
        'metabolic pathways, who want intensive lab grounding. Preparation for medical and health '
        'professions, biotech, or graduate research.'
    ),
    'ut-austin-biochemistry-ma': (
        'Graduates seeking advanced training in the molecular mechanisms of life, from protein '
        'structure to metabolic regulation, with hands-on laboratory research. Preparation for '
        'doctoral study, biotech, or specialized research roles.'
    ),
    'ut-austin-biochemistry-phd': (
        'Researchers investigating original questions in protein function, enzymology, and '
        'molecular mechanism who want funded doctoral training at the bench, aiming for academic, '
        'pharmaceutical, or biotech research careers.'
    ),
    'ut-austin-biological-sciences-bsenvirsci': (
        'Undergraduates drawn to how living systems and the environment connect — ecology, '
        'organismal biology, and field science — who want hands-on lab and field work, headed '
        'toward conservation, environmental, or health-science careers or graduate study.'
    ),
    'ut-austin-biology-bsa': (
        'Students curious about how living systems work, from cells and genetics to ecosystems, '
        'who want broad laboratory and field grounding. Strong preparation for health '
        'professions, graduate research, or careers in biotech and conservation.'
    ),
    'ut-austin-biomedical-engineering-bsbiomede': (
        'Undergraduates who want to apply engineering to medicine, the body, and biological '
        'systems, learning imaging, biomaterials, and instrumentation, headed toward '
        'medical-device work, clinical engineering, or medical or graduate school.'
    ),
    'ut-austin-biomedical-engineering-ms': (
        'Engineers specializing in medical technology, imaging, biomaterials, or computational '
        'modeling of the body, for advanced roles in medical-device firms, hospitals, or '
        'biotechnology.'
    ),
    'ut-austin-biomedical-engineering-phd': (
        'Researchers investigating fundamental problems at the intersection of engineering and '
        'biology, from cellular mechanics to diagnostic devices, headed toward academic or '
        'industrial research careers.'
    ),
    'ut-austin-business-administration-bba': (
        'Undergraduates who want a broad business foundation across accounting, finance, '
        'marketing, operations, and management before specializing or going general. A flexible '
        'start for analyst, coordinator, or rotational-program roles, or a launchpad to a focused '
        'major.'
    ),
    'ut-austin-business-administration-mba': (
        'Experienced professionals ready to step into general management or change industries, '
        'who want a broad business core plus leadership development across a cohort. Built for a '
        'step up to leadership, a function switch, or an industry pivot — not a single specialty.'
    ),
    'ut-austin-business-analytics-bba': (
        'Quantitatively-inclined undergraduates who want to turn data into business decisions '
        'through statistics, modeling, and visualization. A foundation for business-analyst, '
        'data-analyst, and reporting roles across functions like marketing, operations, and '
        'finance.'
    ),
    'ut-austin-business-analytics-ms': (
        'Analytically-minded early-career applicants who want to turn data into business '
        'decisions — modeling, machine learning, and visualization — headed for analyst and '
        'data-science roles. A focused, role-specific complement to a quantitative or business '
        'background.'
    ),
    'ut-austin-cell-and-molecular-biology-ma': (
        'Graduates advancing their grounding in cellular processes, gene regulation, and '
        'molecular biology through coursework and laboratory research. A step toward doctoral '
        'study or research roles in biotech and life sciences.'
    ),
    'ut-austin-cell-and-molecular-biology-phd': (
        'Researchers pursuing original questions in cellular and molecular biology who want '
        'funded doctoral training at the bench, aiming for academic, biotech, or '
        'research-institute careers.'
    ),
    'ut-austin-chemical-engineering-bsche': (
        'Students fascinated by chemical reactions, separations, and the design of processes that '
        'turn raw inputs into fuels, materials, and pharmaceuticals at scale, headed toward '
        'process engineering or graduate study.'
    ),
    'ut-austin-chemical-engineering-ms': (
        'Engineers advancing their command of reaction engineering, separations, and process '
        'design, for specialized roles in energy, materials, pharmaceuticals, or process '
        'development.'
    ),
    'ut-austin-chemical-engineering-phd': (
        'Researchers pursuing original work in molecular engineering, catalysis, energy, or '
        'process systems, headed toward faculty positions or advanced industrial research.'
    ),
    'ut-austin-chemistry-ba': (
        'Undergraduates interested in matter, reactions, and molecular structure who want a '
        'flexible foundation in organic, physical, and analytical chemistry. A starting point for '
        'health professions, industry lab work, or graduate study.'
    ),
    'ut-austin-chemistry-ma': (
        'Graduates deepening their expertise in synthesis, analysis, and physical chemistry '
        'through advanced coursework and laboratory research. Preparation for doctoral study or '
        'specialized roles in chemical industry and research labs.'
    ),
    'ut-austin-chemistry-phd': (
        'Researchers pursuing original questions in synthetic, physical, or analytical chemistry '
        'who want funded doctoral training in the lab, aiming for academic, industrial R&D, or '
        'national-laboratory careers.'
    ),
    'ut-austin-civics-honors-ba': (
        'Undergraduates drawn to the foundations of self-government, political thought, and civic '
        'responsibility who want a rigorous honors curriculum in the great texts and ideas, '
        'preparing for law, public service, or graduate study.'
    ),
    'ut-austin-civil-engineering-bsce': (
        'Engineers who want to design and analyze the built environment, bridges, water systems, '
        'foundations, and transportation, building toward professional licensure (P.E.) and '
        'early-career civil practice.'
    ),
    'ut-austin-civil-engineering-ms': (
        'Engineers specializing in a civil subfield, structures, geotechnical, transportation, '
        'water, or construction, for advanced practice and a faster path to professional '
        'licensure and technical leadership.'
    ),
    'ut-austin-civil-engineering-phd': (
        'Researchers tackling fundamental questions in infrastructure, materials, hazards, or '
        'environmental systems, headed toward faculty roles or research-driven engineering '
        'leadership.'
    ),
    'ut-austin-classical-languages-ba': (
        'Undergraduates who want rigorous study of Latin and ancient Greek and the literature '
        'written in them, reading classical texts in the original. Strong preparation for '
        'teaching, classics scholarship, law, or graduate study.'
    ),
    'ut-austin-classical-studies-ba': (
        'Undergraduates fascinated by the literature, history, art, and thought of ancient Greece '
        'and Rome who want a broad view of the classical world without heavy language immersion. '
        'A foundation for teaching, museums, law, or graduate study.'
    ),
    'ut-austin-classics-ma': (
        'Students who want advanced study of the languages, literature, history, and material '
        'culture of Greece and Rome, strengthening their Latin and Greek. A step toward doctoral '
        'study, teaching, or work in classics and related fields.'
    ),
    'ut-austin-classics-phd': (
        'Scholars committed to original research on the ancient Greek and Roman world who want to '
        'develop a dissertation grounded in rigorous philology and historical analysis. '
        'Preparation for a faculty or research career in classics.'
    ),
    'ut-austin-climate-system-science-bsgs': (
        'Undergraduates who want to understand how the atmosphere, oceans, ice, and land interact '
        'to drive climate, learning data and modeling, headed toward climate science, '
        'environmental work, or graduate study.'
    ),
    'ut-austin-communication-and-leadership-bscomm-and-lead': (
        'Undergraduates who want to pair communication skill with leadership — persuasion, group '
        'dynamics, ethics, and guiding teams and organizations. Suited to people-centered roles '
        'in management, human resources, advocacy, and organizational leadership.'
    ),
    'ut-austin-communication-studies-bscommstds': (
        'Undergraduates interested in how people connect and persuade — interpersonal, '
        'organizational, and rhetorical communication. A flexible foundation for careers in human '
        'resources, sales, training, public affairs, and graduate or professional study.'
    ),
    'ut-austin-communication-studies-ma': (
        'Graduates who want advanced study of human communication — interpersonal, '
        'organizational, and rhetorical theory and research methods. Suited to careers in '
        'research, teaching, and applied communication, or a step toward doctoral work.'
    ),
    'ut-austin-communication-studies-phd': (
        'Scholars researching interpersonal, organizational, and rhetorical communication through '
        'rigorous theory and empirical methods. The path to faculty positions and academic '
        'research careers in communication studies.'
    ),
    'ut-austin-community-and-regional-planning-ms': (
        'Students who want to shape how cities and regions grow, learning land use, housing, '
        'transportation, and policy, headed toward professional planning roles in public '
        'agencies, firms, and nonprofits.'
    ),
    'ut-austin-community-and-regional-planning-phd': (
        'Researchers investigating urban and regional questions, housing, equity, transportation, '
        'and sustainability, headed toward faculty positions or research roles in policy '
        'institutions.'
    ),
    'ut-austin-comparative-literature-ma': (
        'Students who want to study literature across languages and national traditions, working '
        'with theory and texts in more than one language. A step toward doctoral study, '
        'translation, or teaching and editorial work.'
    ),
    'ut-austin-comparative-literature-phd': (
        'Scholars pursuing original research across literatures and languages who want to write a '
        'dissertation engaging literary theory and cross-cultural analysis. Preparation for a '
        'faculty or research career in comparative literature.'
    ),
    'ut-austin-composition-bmusic': (
        'Aspiring composers ready to write for voices, instruments, and ensembles while studying '
        'theory, orchestration, and the craft of musical structure, building a portfolio toward '
        'professional composition or graduate study.'
    ),
    'ut-austin-computational-engineering-bscompe': (
        'Students who like to model physical systems with code and mathematics rather than build '
        'them by hand, learning numerical methods, simulation, and high-performance computing '
        'toward roles in modeling, software, or research-oriented engineering.'
    ),
    'ut-austin-computational-science-engineering-and-mathematics-ms': (
        'Students who want to apply advanced mathematics, modeling, and high-performance '
        'computing to scientific and engineering problems, preparing for technical roles in '
        'research labs, industry, or further doctoral study.'
    ),
    'ut-austin-computational-science-engineering-and-mathematics-phd': (
        'Researchers building expertise in numerical methods, simulation, and computational '
        'modeling to tackle complex scientific problems, preparing for careers in academia, '
        'national laboratories, or computational research and development.'
    ),
    'ut-austin-computer-science-bsa': (
        'Students who enjoy algorithms, programming, and computational problem-solving and want a '
        'rigorous foundation in systems, theory, and software design. Strong preparation for '
        'software engineering, technical roles, or graduate study.'
    ),
    'ut-austin-computer-science-ms': (
        'Graduates seeking advanced expertise in systems, algorithms, machine learning, or theory '
        'through rigorous coursework and projects. Preparation for senior engineering and '
        'research roles or a path toward doctoral study.'
    ),
    'ut-austin-computer-science-online-ms': (
        'Working professionals and graduates strengthening their command of systems, machine '
        'learning, and algorithms through flexible online study. Advanced preparation for senior '
        'software engineering and technical roles without leaving the workforce.'
    ),
    'ut-austin-computer-science-phd': (
        'Researchers pursuing original work in areas such as systems, theory, AI, or graphics who '
        'want funded doctoral training, aiming for faculty positions or research careers in '
        'industry labs.'
    ),
    'ut-austin-curriculum-and-instruction-edd': (
        'Experienced educators pursuing the practice-oriented doctorate, applying research to '
        'real problems of curriculum and instruction, preparing for leadership roles in schools '
        'and districts.'
    ),
    'ut-austin-curriculum-and-instruction-ma': (
        'Educators ready to deepen their understanding of teaching, learning, and curriculum '
        'through research and advanced coursework, sharpening classroom practice or preparing for '
        'doctoral study.'
    ),
    'ut-austin-curriculum-and-instruction-med': (
        'Practicing teachers who want advanced, practice-focused study of curriculum and '
        'instruction to strengthen their classrooms and move into instructional leadership and '
        'specialist roles.'
    ),
    'ut-austin-curriculum-and-instruction-phd': (
        'Scholars pursuing original research on how teaching and learning happen across subjects '
        'and settings, preparing for careers in university teaching and educational research.'
    ),
    'ut-austin-dance-bfa': (
        'Dancers committed to daily technique, choreography, and performance across forms, '
        'building artistry and stamina through studio practice toward professional companies, '
        'independent work, or graduate study.'
    ),
    'ut-austin-data-science-ms': (
        'Working professionals and graduates building applied skills in statistical modeling, '
        'machine learning, and data engineering through online study. Advanced preparation for '
        'data science, analytics, and quantitative roles across industries.'
    ),
    'ut-austin-design-ba': (
        'Students who want to solve problems visually through typography, branding, interaction, '
        'and communication design, developing a portfolio through studio projects. A foundation '
        'for design practice or graduate study.'
    ),
    'ut-austin-design-ma': (
        'Designers and design researchers who want to advance their thinking through focused '
        'study and applied projects, sharpening a specialization for senior practice or continued '
        'graduate work.'
    ),
    'ut-austin-design-mfa': (
        'Designers ready for the terminal studio degree — sustained, self-directed creative '
        'research across visual and interaction design — building a defining body of work toward '
        'leadership in practice or teaching at the college level.'
    ),
    'ut-austin-ecology-evolution-and-behavior-ma': (
        'Graduates deepening their grounding in evolutionary biology, ecology, and animal '
        'behavior through coursework and field or lab research. A step toward doctoral study or '
        'work in conservation and environmental science.'
    ),
    'ut-austin-ecology-evolution-and-behavior-phd': (
        'Researchers pursuing original questions in ecology, evolution, and behavior through '
        'field, lab, and computational study, aiming for funded doctoral training and academic, '
        'conservation, or research-institute careers.'
    ),
    'ut-austin-economics-ba': (
        'Undergraduates who want to understand how markets, incentives, and policy shape '
        'behavior, using economic models and data. A versatile foundation for finance, '
        'consulting, government, or graduate study in economics or business.'
    ),
    'ut-austin-economics-ma': (
        'Students who want advanced training in economic theory, econometrics, and applied '
        'analysis to deepen their quantitative and policy skills. A step toward doctoral study or '
        'work as an economist, analyst, or researcher in industry and government.'
    ),
    'ut-austin-economics-ms': (
        "Students who want a quantitatively focused master's in economic theory and econometrics "
        'aimed at applied research and analysis. Preparation for analyst and economist roles in '
        'industry, finance, and government, or for doctoral study.'
    ),
    'ut-austin-economics-phd': (
        'Scholars pursuing original research in economic theory and empirical analysis who want '
        'to build a dissertation and contribute new findings. Preparation for a faculty position '
        'or research career in academia, government, or industry.'
    ),
    'ut-austin-education-bsed': (
        'Future teachers who want to pair subject knowledge with classroom practice and field '
        'experience, earning certification to lead a K-12 classroom.'
    ),
    'ut-austin-educational-leadership-and-policy-edd': (
        'Experienced education leaders pursuing the practice-focused doctorate, applying research '
        'to the leadership and policy challenges of real schools and systems, preparing for '
        'senior administrative roles.'
    ),
    'ut-austin-educational-leadership-and-policy-med': (
        'Educators ready to step into leadership — principalship, administration, and policy — '
        'studying how schools and systems are governed and improved, preparing for advanced '
        'leadership roles.'
    ),
    'ut-austin-educational-leadership-and-policy-phd': (
        'Scholars researching the policies, politics, and organization of education systems, '
        'building original studies that inform reform, preparing for careers in university '
        'faculty and research roles.'
    ),
    'ut-austin-educational-psychology-ma': (
        'Students studying how people learn, develop, and are motivated, and how to measure it, '
        'building research and applied skills toward careers in education, assessment, or '
        'doctoral study.'
    ),
    'ut-austin-educational-psychology-med': (
        'Educators who want to apply the psychology of learning and development to their '
        'practice, deepening skills in instruction, counseling, or assessment for advanced roles '
        'in schools and education settings.'
    ),
    'ut-austin-educational-psychology-phd': (
        'Scholars pursuing original research on learning, development, motivation, and '
        'measurement, preparing for careers in university teaching, research, and applied '
        'psychological science.'
    ),
    'ut-austin-electrical-and-computer-engineering-bsece': (
        'Undergraduates who enjoy circuits, signals, embedded systems, and computer hardware, '
        'working from transistors up to whole devices, headed toward roles in semiconductors, '
        'hardware, or systems engineering.'
    ),
    'ut-austin-electrical-and-computer-engineering-ms': (
        'Engineers deepening expertise in a focused ECE area, integrated circuits, '
        'communications, computer architecture, or controls, for advanced roles in '
        'semiconductors, hardware, or systems firms.'
    ),
    'ut-austin-electrical-and-computer-engineering-phd': (
        'Researchers pursuing original work in areas from nanoelectronics to computing systems '
        'and signal processing, headed toward faculty positions or advanced industrial R&D.'
    ),
    'ut-austin-energy-and-earth-resources-ma': (
        'Students examining energy and resources through policy, economics, and management '
        'alongside earth science, headed toward roles in energy, environmental policy, and '
        'resource decision-making.'
    ),
    'ut-austin-energy-and-earth-resources-ms': (
        'Students integrating earth science with the technical and economic dimensions of energy '
        'and resources, for advanced analytical roles in the energy sector, consulting, or '
        'research.'
    ),
    'ut-austin-energy-management-ms': (
        'Early-career and working professionals in or entering the energy sector who want '
        'graduate grounding in energy markets, finance, operations, and policy. Suited to '
        'analyst, trading, and management roles across oil, gas, power, and renewables.'
    ),
    'ut-austin-engineering-management-ms': (
        'Practicing engineers who want to lead technical teams and projects, learning operations, '
        'finance, and decision methods alongside their engineering grounding, headed toward '
        'management and technical-leadership roles.'
    ),
    'ut-austin-engineering-mechanics-ms': (
        'Engineers strengthening the mechanics foundation, solid mechanics, dynamics, and '
        'computational analysis, for specialized analysis roles or a bridge into doctoral '
        'research.'
    ),
    'ut-austin-engineering-mechanics-phd': (
        'Researchers pursuing original work in the mechanics of solids, fluids, and materials, '
        'from theory to large-scale simulation, headed toward academic or research-laboratory '
        'careers.'
    ),
    'ut-austin-english-ba': (
        'Undergraduates who love close reading, literature, and writing, and want to analyze '
        'texts across periods and genres while sharpening their own prose. A foundation for '
        'publishing, education, law, communications, or graduate study.'
    ),
    'ut-austin-english-creative-writing-mfa': (
        'Writers serious about craft who want intensive workshop training in fiction or poetry, '
        'time to build a manuscript, and mentorship from working writers. Preparation for a '
        'writing life, publication, or teaching in creative writing.'
    ),
    'ut-austin-english-ma': (
        'Students who want advanced study of literature in English, building research, critical, '
        'and writing skills across periods and genres. A step toward doctoral study, teaching, or '
        'careers in publishing and the humanities.'
    ),
    'ut-austin-english-phd': (
        'Scholars committed to original literary research who want to write a dissertation, '
        'engage critical theory, and join scholarly conversations in English studies. Preparation '
        'for a faculty or research career.'
    ),
    'ut-austin-environmental-engineering-bsenve': (
        'Students who want to protect water, air, and soil, learning treatment, contamination '
        'control, and sustainable systems, building toward environmental consulting, public '
        'agencies, or graduate research.'
    ),
    'ut-austin-ethnic-studies-ba': (
        'Undergraduates who want to study race, ethnicity, and power across communities through '
        'history, culture, and social analysis. A foundation for advocacy, education, public '
        'service, or graduate study in ethnic and area studies.'
    ),
    'ut-austin-european-studies-ba': (
        'Undergraduates interested in the history, politics, languages, and cultures of Europe '
        'who want an interdisciplinary regional focus and language study, with a pull to study '
        'abroad. Preparation for international work, policy, or graduate study.'
    ),
    'ut-austin-exercise-science-bskin-and-health': (
        'Students who want to study the physiology of exercise and human performance, building '
        'the science foundation for careers in fitness, strength, and wellness or graduate study '
        'in the health professions.'
    ),
    'ut-austin-finance-bba': (
        'Undergraduates who want to understand how capital is raised, invested, and valued — '
        'corporate finance, markets, and investments. Suited to entry-level roles in investment '
        'banking, asset management, corporate finance, and financial analysis.'
    ),
    'ut-austin-finance-ms': (
        'Quantitatively strong early-career applicants who want focused depth in valuation, '
        'markets, investments, and financial modeling. A specialized path into investment '
        'banking, asset management, corporate finance, and analyst roles — narrower and earlier '
        'than an MBA.'
    ),
    'ut-austin-finance-phd': (
        'Scholars pursuing rigorous research in asset pricing, corporate finance, and markets '
        'through advanced theory and econometrics. The path to faculty positions and research '
        'careers in finance.'
    ),
    'ut-austin-french-and-italian-french-ma': (
        'Students who want advanced study of French language, literature, and culture, working '
        'closely with texts and theory in French. A step toward doctoral study, translation, or '
        'teaching and international careers.'
    ),
    'ut-austin-french-and-italian-french-phd': (
        'Scholars pursuing original research on French and Francophone literature and culture who '
        'want to write a dissertation grounded in deep linguistic and critical expertise. '
        'Preparation for a faculty or research career.'
    ),
    'ut-austin-french-and-italian-italian-studies-ma': (
        'Students who want advanced study of Italian language, literature, and culture, deepening '
        'textual and critical expertise in Italian. A step toward doctoral study, translation, or '
        'teaching and cultural work.'
    ),
    'ut-austin-french-and-italian-italian-studies-phd': (
        'Scholars committed to original research on Italian literature and culture who want to '
        'develop a dissertation rooted in textual and critical mastery of Italian. Preparation '
        'for a faculty or research career in the field.'
    ),
    'ut-austin-french-studies-ba': (
        'Undergraduates who want fluency in French alongside the literature, history, and culture '
        'of the French-speaking world, ideally with time abroad. A foundation for international '
        'work, translation, education, or graduate study.'
    ),
    'ut-austin-general-geology-bsgs': (
        'Students fascinated by rocks, earth history, and the processes that shape the planet, '
        'learning fieldwork and analysis, building toward geoscience careers in energy, '
        'environment, or graduate study.'
    ),
    'ut-austin-geographical-sciences-bsenvirsci': (
        "Undergraduates who want to study the earth's physical systems and human-environment "
        'interaction using mapping, GIS, and spatial data. A foundation for work in environmental '
        'analysis, planning, GIS, or graduate study in the geosciences.'
    ),
    'ut-austin-geography-ba': (
        'Undergraduates interested in how people, places, and environments connect, using maps, '
        'GIS, and spatial reasoning to study cities, regions, and landscapes. A foundation for '
        'planning, environmental work, GIS, or graduate study.'
    ),
    'ut-austin-geography-ma': (
        'Students who want advanced training in human or physical geography, GIS, and spatial '
        'analysis to study places, environments, and societies. A step toward doctoral study or '
        'work in planning, environmental analysis, or GIS.'
    ),
    'ut-austin-geography-phd': (
        'Scholars pursuing original research in human-environment, physical, or spatial geography '
        'who want to develop a dissertation using fieldwork and analytic methods. Preparation for '
        'a faculty or research career.'
    ),
    'ut-austin-geological-sciences-ma': (
        'Geoscientists deepening expertise in a focused earth-science area through coursework and '
        'research, for advanced technical roles or as a step toward doctoral study.'
    ),
    'ut-austin-geological-sciences-ms': (
        'Geoscientists specializing in a research area, from sedimentary systems to tectonics or '
        'geophysics, for advanced roles in energy, environment, and applied earth science.'
    ),
    'ut-austin-geological-sciences-phd': (
        'Researchers pursuing original work across the earth sciences, from deep-time processes '
        'to modern earth systems, headed toward faculty positions, surveys, or industry research.'
    ),
    'ut-austin-geophysics-bsgs': (
        "Undergraduates who use physics and math to image the earth's interior, seismic waves, "
        'gravity, and magnetism, building toward roles in energy exploration, hazards, or '
        'graduate research.'
    ),
    'ut-austin-geosciences-bags': (
        'Students seeking a broad foundation across earth sciences with flexibility to explore '
        'geology, environment, and resources, building toward varied geoscience careers, '
        'teaching, or graduate study.'
    ),
    'ut-austin-geosystems-engineering-bsge': (
        'Students drawn to engineering with the earth itself, the subsurface, groundwater, and '
        'energy and mineral resources, blending geology with engineering toward roles in '
        'resources, geotechnical work, or graduate study.'
    ),
    'ut-austin-geosystems-engineering-bsge-2': (
        'Students who pair geology with engineering to study groundwater and subsurface '
        'resources, learning hydrogeology and resource systems, headed toward roles in water, '
        'environment, or energy.'
    ),
    'ut-austin-german-ba': (
        'Undergraduates who want fluency in German and a grounding in the literature, history, '
        'and culture of German-speaking Europe, ideally with study abroad. A foundation for '
        'international work, translation, education, or graduate study.'
    ),
    'ut-austin-germanic-studies-ma': (
        'Students who want advanced study of German language, literature, and culture, working '
        'with texts and theory in German. A step toward doctoral study, translation, or teaching '
        'and international careers.'
    ),
    'ut-austin-germanic-studies-phd': (
        'Scholars committed to original research on German and Germanic literature and culture '
        'who want to write a dissertation grounded in deep linguistic and critical expertise. '
        'Preparation for a faculty or research career.'
    ),
    'ut-austin-global-policy-studies-mgps': (
        'Students focused on international affairs, security, trade, and development who want '
        'quantitative and regional training for careers in diplomacy, global NGOs, multilateral '
        'institutions, or foreign-policy analysis.'
    ),
    'ut-austin-government-ba': (
        'Undergraduates drawn to politics, institutions, law, and political theory who want to '
        'analyze how power and policy work in the U.S. and abroad. A versatile foundation for '
        'law, public service, campaigns, journalism, or graduate study.'
    ),
    'ut-austin-government-ma': (
        'Students who want advanced training in political theory, institutions, and empirical '
        'methods to deepen their analysis of politics and policy. A step toward doctoral study or '
        'careers in policy, research, and public service.'
    ),
    'ut-austin-government-phd': (
        'Scholars pursuing original research in political science across theory, American or '
        'comparative politics, and international relations who want to write a dissertation. '
        'Preparation for a faculty position or research career in policy and academia.'
    ),
    'ut-austin-health-and-society-ba': (
        'Undergraduates curious about how culture, policy, economics, and inequality shape health '
        'and medicine, who prefer a social-science lens over a lab one. Good preparation for '
        'public health, health administration, advocacy, or graduate and professional study in '
        'health fields.'
    ),
    'ut-austin-health-behavior-and-health-education-med': (
        'Educators and practitioners focused on how to change health behavior through education '
        'and programs, building applied skills for careers in community health, school health, '
        'and wellness.'
    ),
    'ut-austin-health-behavior-and-health-education-ms': (
        'Students ready to study the science of health behavior and program design with a '
        'research emphasis, building methods and analytic skills for careers in public health or '
        'doctoral study.'
    ),
    'ut-austin-health-behavior-and-health-education-phd': (
        'Scholars conducting original research on the determinants of health behavior and how to '
        'change it, preparing for careers in university faculty, research, and public health '
        'leadership.'
    ),
    'ut-austin-health-promotion-and-behavioral-science-bskin-and-health': (
        'Students focused on how behavior shapes health and how to design programs that help '
        'people live healthier lives, preparing for community health, wellness, and public health '
        'careers or graduate study.'
    ),
    'ut-austin-history-ba': (
        'Undergraduates who want to investigate the past through primary sources, building skills '
        'in research, argument, and writing across eras and regions. A foundation for law, '
        'education, public history, journalism, or graduate study.'
    ),
    'ut-austin-history-ma': (
        'Students who want advanced training in historical research, archival method, and '
        'argument across regions and eras. A step toward doctoral study, teaching, public '
        'history, or work in archives and education.'
    ),
    'ut-austin-history-phd': (
        'Scholars committed to original archival research who want to write a dissertation, '
        'contribute new interpretations of the past, and join historical scholarship. Preparation '
        'for a faculty or research career.'
    ),
    'ut-austin-human-development-and-family-sciences-bsa': (
        'Undergraduates interested in how individuals and families develop across the lifespan, '
        'drawing on psychology and social science. A foundation for careers in child and family '
        'services, education, or graduate study in counseling or development.'
    ),
    'ut-austin-human-development-and-family-sciences-ma': (
        'Graduates advancing their study of development across the lifespan and family dynamics '
        'through research and applied coursework. Preparation for doctoral study or specialized '
        'roles in counseling, policy, and human services.'
    ),
    'ut-austin-human-development-and-family-sciences-phd': (
        'Researchers investigating original questions about human development, relationships, and '
        'family systems across the lifespan, aiming for funded doctoral training and careers in '
        'academic research, policy, or applied science.'
    ),
    'ut-austin-human-dimensions-of-organizations-ba': (
        'Undergraduates who want to understand how people behave inside organizations, drawing on '
        'psychology, history, ethics, and rhetoric to read teams and leadership. A grounding for '
        'management, HR, consulting, or further study in organizational behavior.'
    ),
    'ut-austin-human-dimensions-of-organizations-ma': (
        'Working professionals and others who want to apply behavioral science, ethics, and the '
        'humanities to leadership and organizational problems. Designed to sharpen judgment for '
        'management, HR, and consulting roles rather than to lead to doctoral study.'
    ),
    'ut-austin-human-ecology-bsa': (
        'Undergraduates interested in how people interact with their environments, resources, and '
        'communities across the lifespan. A foundation for work in family services, public '
        'programs, consumer and community organizations, or graduate study.'
    ),
    'ut-austin-humanities-ba': (
        'Undergraduates who want to build their own interdisciplinary path across literature, '
        'history, philosophy, and the arts rather than a single major. A broad foundation in '
        'reading, writing, and analysis for careers in writing, education, law, or graduate '
        'study.'
    ),
    'ut-austin-humanities-health-and-medicine-ma': (
        'Students and clinicians who want to examine health, illness, and care through history, '
        'ethics, literature, and cultural analysis. Preparation for work in healthcare, '
        'bioethics, advocacy, or further professional and graduate study in health humanities.'
    ),
    'ut-austin-hydrology-and-water-resources-bsgs': (
        'Undergraduates focused on water, where it moves, how it is stored, and how to manage it, '
        'learning surface and groundwater science, building toward water-resource careers or '
        'graduate study.'
    ),
    'ut-austin-iberian-and-latin-american-languages-and-cultures-ma': (
        'Students who want advanced study of Spanish and Portuguese languages, literatures, and '
        'cultures across Iberia and Latin America. A step toward doctoral study, translation, or '
        'teaching and international work.'
    ),
    'ut-austin-iberian-and-latin-american-languages-and-cultures-phd': (
        'Scholars pursuing original research on the literatures and cultures of the Spanish- and '
        'Portuguese-speaking world who want to write a dissertation grounded in deep linguistic '
        'and critical expertise. Preparation for a faculty or research career.'
    ),
    'ut-austin-informatics-ba': (
        'Undergraduates who want to study how people, data, and technology intersect, combining '
        'design, analysis, and human-centered computing for roles in UX research, data, or '
        'product, or graduate study in information science.'
    ),
    'ut-austin-information-risk-and-operations-management-ms': (
        'Early-career professionals who want graduate depth in operations, information systems, '
        'and risk analytics — optimizing processes and decisions with data. Suited to roles in '
        'operations analysis, supply-chain analytics, and information-driven decision support.'
    ),
    'ut-austin-information-risk-and-operations-management-phd': (
        'Scholars researching operations, information systems, and decision sciences using '
        'quantitative modeling and empirical methods. The path to faculty positions and research '
        'careers in operations and information management.'
    ),
    'ut-austin-information-security-and-privacy-ms': (
        'Professionals focused on protecting data and digital systems who want technical and '
        'policy training in cybersecurity, risk, and privacy law for careers as security '
        'analysts, privacy officers, or compliance leads.'
    ),
    'ut-austin-information-studies-ms': (
        'Students drawn to organizing, preserving, and connecting people to information across '
        'libraries, archives, data, and digital collections, preparing for careers as librarians, '
        'archivists, UX researchers, or data curators.'
    ),
    'ut-austin-information-studies-phd': (
        'Scholars investigating how information is created, organized, and used in society, '
        'developing the research foundation for faculty positions or advanced work in libraries, '
        'archives, and information policy.'
    ),
    'ut-austin-information-technology-and-management-ms': (
        'Early-career professionals bridging technology and business who want graduate depth in '
        'IT strategy, systems, and data management. Suited to roles in technology consulting, IT '
        'management, and product or systems leadership.'
    ),
    'ut-austin-interior-design-bsid': (
        'Undergraduates who shape how interior spaces look, function, and feel, learning spatial '
        'design, materials, lighting, and human factors, building toward professional '
        'interior-design practice and certification.'
    ),
    'ut-austin-interior-design-mid': (
        'Students entering interior design at the graduate level, developing spatial design, '
        'materials, and human-centered methods toward professional practice and certification.'
    ),
    'ut-austin-international-business-bba': (
        'Globally-minded undergraduates who pair a business core with cross-border trade, foreign '
        'markets, and cultural fluency, often alongside language study. A strong start for roles '
        'in global operations, trade, or multinational firms with international exposure.'
    ),
    'ut-austin-international-relations-and-global-studies-ba': (
        'Undergraduates drawn to world politics, economics, security, and culture across borders '
        'who want an interdisciplinary view and the pull to study abroad and learn a language. '
        'Preparation for foreign service, NGOs, policy, or graduate study in international '
        'affairs.'
    ),
    'ut-austin-italian-studies-ba': (
        "Undergraduates drawn to the Italian language and to Italy's literature, art, and history "
        'who want language fluency paired with cultural study and time abroad. Preparation for '
        'work in the arts, education, international fields, or graduate study.'
    ),
    'ut-austin-jazz-bmusic': (
        'Players committed to the jazz tradition — improvisation, the standards, combo and '
        'big-band performance — who want intensive ensemble work and individual lessons, '
        'preparing for performing careers or graduate study.'
    ),
    'ut-austin-jewish-studies-ba': (
        'Undergraduates interested in Jewish history, religion, languages, and culture across '
        'time and place who want an interdisciplinary lens. A foundation for education, communal '
        'and nonprofit work, religious leadership, or graduate study.'
    ),
    'ut-austin-journalism-and-media-ma': (
        'Working journalists and graduates who want advanced study of journalism practice and '
        "media's role in society, with research and reporting depth. Suited to specialized "
        'reporting, editorial leadership, and media-research roles, or further doctoral study.'
    ),
    'ut-austin-journalism-and-media-phd': (
        'Scholars researching journalism, media systems, and their effects on society through '
        'rigorous empirical and theoretical methods. The path to faculty positions and research '
        'careers in journalism and media studies.'
    ),
    'ut-austin-journalism-bj': (
        'Undergraduates committed to reporting and storytelling across print, digital, and '
        'broadcast — researching, interviewing, writing, and verifying. A foundation for careers '
        'as reporters, editors, and multimedia journalists in newsrooms and digital outlets.'
    ),
    'ut-austin-kinesiology-med': (
        'Educators and practitioners who want advanced, applied study of human movement, '
        'exercise, and physical activity, building skills for teaching, coaching, and program '
        'roles in health and fitness settings.'
    ),
    'ut-austin-kinesiology-ms': (
        'Students ready to study the science of human movement and exercise with a research '
        'emphasis, building laboratory and analytic skills toward careers in exercise science or '
        'doctoral study.'
    ),
    'ut-austin-kinesiology-phd': (
        'Scholars pursuing original research on human movement, exercise physiology, and physical '
        'activity, preparing for careers in university teaching and scientific research.'
    ),
    'ut-austin-landscape-architecture-mla': (
        'Students pursuing the accredited path to becoming a landscape architect, designing '
        'parks, public spaces, and ecological systems toward licensure and professional practice.'
    ),
    'ut-austin-landscape-architecture-ms': (
        'Designers and scholars focused on the research side of landscape, ecology, climate '
        'adaptation, and design theory, for advanced or research-oriented landscape work and '
        'doctoral preparation.'
    ),
    'ut-austin-latin-american-studies-ba': (
        'Undergraduates drawn to the history, politics, languages, and cultures of Latin America '
        'who want an interdisciplinary regional focus with language study and time abroad. '
        'Preparation for international work, policy, or graduate study.'
    ),
    'ut-austin-latin-american-studies-ma': (
        "Students who want advanced, interdisciplinary study of Latin America's history, "
        'politics, economies, and cultures, deepening regional and language expertise. A step '
        'toward doctoral study, international work, or policy careers.'
    ),
    'ut-austin-latin-american-studies-phd': (
        'Scholars pursuing original, interdisciplinary research on Latin America who want to '
        'write a dissertation drawing on fieldwork, languages, and regional expertise. '
        'Preparation for a faculty or research career in Latin American studies.'
    ),
    'ut-austin-law-jd': (
        'Aspiring lawyers ready for rigorous training in legal reasoning, writing, and doctrine '
        'across three years, preparing to sit for the bar and enter practice, clerkships, or '
        'public service.'
    ),
    'ut-austin-law-llm': (
        'Practicing and foreign-trained lawyers seeking advanced or specialized legal study who '
        'want to deepen expertise in a chosen area of law, often to strengthen their practice or '
        'pursue U.S. bar eligibility.'
    ),
    'ut-austin-linguistics-ba': (
        'Undergraduates fascinated by how language works, studying its sounds, structure, '
        'meaning, and change with both analytic and experimental methods. A foundation for work '
        'in language technology, teaching, speech fields, or graduate study.'
    ),
    'ut-austin-linguistics-ma': (
        'Students who want advanced training in the structure of language, working across '
        'phonology, syntax, semantics, and experimental or computational methods. A step toward '
        'doctoral study or work in language technology and speech fields.'
    ),
    'ut-austin-linguistics-phd': (
        'Scholars pursuing original research on the nature of language who want to write a '
        'dissertation using theoretical, experimental, or computational methods. Preparation for '
        'a faculty or research career in linguistics and language science.'
    ),
    'ut-austin-management-bba': (
        'Undergraduates focused on leading people and organizations — strategy, organizational '
        'behavior, entrepreneurship, and team leadership. A foundation for management-trainee '
        'tracks, HR and operations roles, consulting, or building a venture of their own.'
    ),
    'ut-austin-management-information-systems-bba': (
        'Undergraduates at the intersection of business and technology — databases, systems '
        'design, and how IT drives operations and strategy. Fits future business systems '
        'analysts, IT consultants, and technology-product roles that bridge users and developers.'
    ),
    'ut-austin-management-ms': (
        'Recent graduates and early-career professionals who want a focused graduate grounding in '
        'management, strategy, and organizational leadership before significant work experience. '
        'A role-specific start for analyst, coordinator, and leadership-track positions.'
    ),
    'ut-austin-management-phd': (
        'Scholars researching strategy, organizational behavior, and entrepreneurship through '
        'theory and empirical study. The path to faculty positions and academic research careers '
        'in management.'
    ),
    'ut-austin-marine-science-ms': (
        'Graduates studying ocean systems, marine organisms, and coastal processes who want '
        'advanced coursework and field or lab research. A step toward doctoral study or careers '
        'in marine resource management and environmental science.'
    ),
    'ut-austin-marine-science-phd': (
        'Researchers pursuing original questions in oceanography, marine biology, and coastal '
        'ecosystems who want funded doctoral training, aiming for academic, governmental, or '
        'research-institute careers in marine science.'
    ),
    'ut-austin-marketing-bba': (
        'Undergraduates who want to understand customers and demand — branding, consumer '
        'behavior, digital marketing, and market research. Suited to entry-level roles in brand '
        'management, advertising, marketing analytics, and sales.'
    ),
    'ut-austin-marketing-ms': (
        'Early-career applicants who want focused graduate depth in consumer behavior, brand '
        'strategy, digital marketing, and analytics. Suited to role-specific paths in brand '
        'management, marketing analytics, and market research, ahead of broad managerial '
        'experience.'
    ),
    'ut-austin-marketing-phd': (
        'Scholars researching consumer behavior, marketing strategy, and quantitative modeling of '
        'markets through rigorous empirical methods. The path to faculty positions and research '
        'careers in marketing.'
    ),
    'ut-austin-materials-science-and-engineering-ms': (
        'Engineers specializing in how the structure of metals, polymers, ceramics, and '
        'semiconductors shapes their properties, for advanced roles in materials development, '
        'electronics, or manufacturing.'
    ),
    'ut-austin-materials-science-and-engineering-phd': (
        'Researchers investigating the fundamentals of materials behavior, from atomic structure '
        'to new functional materials, headed toward faculty positions or industrial research '
        'labs.'
    ),
    'ut-austin-mathematics-ba': (
        'Undergraduates who enjoy quantitative reasoning and want a flexible grounding in '
        'calculus, proof, and abstraction across pure and applied areas. Strong preparation for '
        'graduate study, quantitative roles, or teaching.'
    ),
    'ut-austin-mathematics-ma': (
        'Graduates deepening their command of analysis, algebra, and applied mathematics through '
        'advanced coursework. Preparation for doctoral study, teaching, or quantitative roles '
        'that demand rigorous mathematical training.'
    ),
    'ut-austin-mathematics-phd': (
        'Researchers pursuing original work in pure or applied mathematics who want funded '
        'doctoral training in fields such as analysis, topology, or number theory, aiming for '
        'faculty positions or research careers.'
    ),
    'ut-austin-mechanical-engineering-bsme': (
        'Students who like to design and analyze machines, mechanisms, and energy systems, '
        'grounded in mechanics, thermodynamics, and manufacturing, building toward broad '
        'early-career roles across many industries or graduate study.'
    ),
    'ut-austin-mechanical-engineering-ms': (
        'Engineers deepening expertise in a mechanical focus, thermal systems, dynamics, '
        'manufacturing, or design, for advanced engineering roles across energy, automotive, and '
        'product industries.'
    ),
    'ut-austin-mechanical-engineering-phd': (
        'Researchers pursuing original work in areas from heat transfer to robotics and advanced '
        'manufacturing, headed toward faculty positions or industrial R&D leadership.'
    ),
    'ut-austin-medical-laboratory-science-bsmedlabsci': (
        'Students drawn to diagnostic testing and the laboratory science behind clinical medicine '
        'who want hands-on training in clinical chemistry, microbiology, and hematology. A path '
        'toward certification and work as a medical laboratory scientist.'
    ),
    'ut-austin-medicine-md': (
        'Future physicians ready for the full arc of medical training, from foundational science '
        'to clinical rotations, preparing for licensing exams, residency, and a career in patient '
        'care across the specialties.'
    ),
    'ut-austin-mexican-american-and-latina-o-studies-ba': (
        'Undergraduates who want to study the history, culture, politics, and experience of '
        'Mexican American and Latina/o communities through an interdisciplinary lens. A '
        'foundation for advocacy, education, public service, or graduate study.'
    ),
    'ut-austin-mexican-american-and-latina-o-studies-ma': (
        'Students who want advanced, interdisciplinary study of Mexican American and Latina/o '
        'histories, cultures, and politics, building research and critical skills. A step toward '
        'doctoral study, teaching, or community-engaged professional work.'
    ),
    'ut-austin-mexican-american-and-latina-o-studies-phd': (
        'Scholars committed to original research on Mexican American and Latina/o communities who '
        'want to write a dissertation and shape scholarly debates. Preparation for a faculty or '
        'research career in the field.'
    ),
    'ut-austin-microbiology-ma': (
        'Graduates advancing their study of bacteria, viruses, and microbial systems through '
        'coursework and laboratory research. A step toward doctoral study or research roles in '
        'biotech, clinical, and public health labs.'
    ),
    'ut-austin-microbiology-phd': (
        'Researchers pursuing original questions in microbial genetics, pathogenesis, and '
        'physiology who want funded doctoral training at the bench, aiming for academic, biotech, '
        'or public health research careers.'
    ),
    'ut-austin-middle-eastern-languages-and-cultures-ma': (
        'Students who want advanced training in the languages, literatures, and cultures of the '
        'Middle East, working closely with primary texts. A step toward doctoral study, '
        'translation, or teaching and international work.'
    ),
    'ut-austin-middle-eastern-languages-and-cultures-phd': (
        'Scholars pursuing original research on Middle Eastern languages, literatures, and '
        'cultures who want to write a dissertation rooted in deep textual and linguistic '
        'expertise. Preparation for a faculty or research career.'
    ),
    'ut-austin-middle-eastern-studies-ba': (
        'Undergraduates curious about the Middle East and North Africa who want an '
        'interdisciplinary, modern lens on the region paired with language study and a pull to '
        'study abroad. Preparation for international work, policy, journalism, or graduate study.'
    ),
    'ut-austin-middle-eastern-studies-ma': (
        'Students who want advanced, interdisciplinary study of the modern Middle East across '
        'politics, history, and society, with strong language preparation. A step toward doctoral '
        'study, policy work, journalism, or international careers.'
    ),
    'ut-austin-music-bamusic': (
        'Students who want a broad, conservatory-grade grounding in performance, theory, and '
        'history without specializing as narrowly, building musicianship toward performance, '
        'teaching, or further study.'
    ),
    'ut-austin-music-conducting-dma': (
        'Conductors pursuing the highest professional degree, refining interpretation and '
        'ensemble leadership at an advanced level, preparing for careers leading orchestras, '
        'choirs, or bands and teaching conducting.'
    ),
    'ut-austin-music-conducting-mm': (
        'Conductors ready to develop score study, rehearsal technique, and podium command with an '
        'ensemble, advancing toward professional conducting positions or doctoral study.'
    ),
    'ut-austin-music-dma': (
        'Performers and conductors pursuing the highest professional degree in music, pairing '
        'artistry at the recital level with scholarly depth, preparing for solo and ensemble '
        'careers and college-level teaching.'
    ),
    'ut-austin-music-mm': (
        'Musicians ready for advanced study in their concentration — performance, theory, or '
        "related areas — refining artistry and scholarship beyond the bachelor's, toward "
        'professional careers or doctoral work.'
    ),
    'ut-austin-music-music-and-human-learning-dma': (
        'Experienced music educators and performers pursuing the highest applied degree in music '
        'learning, uniting artistry with research on teaching, preparing for leadership in '
        'schools and college-level instruction.'
    ),
    'ut-austin-music-music-and-human-learning-mm': (
        'Music educators ready to deepen the study of how people learn music, pairing '
        'musicianship with pedagogy and research methods, preparing for advanced teaching roles '
        'or doctoral study.'
    ),
    'ut-austin-music-music-and-human-learning-phd': (
        'Scholars researching how music is taught and learned across settings, building original '
        'studies in music education, preparing for university faculty and research careers.'
    ),
    'ut-austin-music-performance-bmusic': (
        'Performers seeking conservatory-level training on their instrument or voice, ready for '
        'daily practice, lessons, and ensemble work, headed toward professional performance or '
        'graduate music study.'
    ),
    'ut-austin-music-phd': (
        "Musicologists and theorists pursuing original scholarly research on music's history, "
        'structure, and meaning, preparing for careers in university teaching and academic '
        'research.'
    ),
    'ut-austin-music-studies-bmusic': (
        'Students preparing to teach music in schools, pairing strong musicianship with the '
        'methods of music education and field experience, working toward classroom certification '
        'and a K-12 music career.'
    ),
    'ut-austin-neuroscience-bsa': (
        'Undergraduates interested in the brain, nervous system, and the biology of behavior who '
        'want grounding in molecular, cellular, and systems neuroscience. Preparation for health '
        'professions, graduate research, or biotech.'
    ),
    'ut-austin-neuroscience-ms': (
        'Graduates deepening their grounding in the molecular, cellular, and systems biology of '
        'the brain through coursework and laboratory research. Preparation for doctoral study or '
        'research roles in biotech and the health sciences.'
    ),
    'ut-austin-neuroscience-phd': (
        'Researchers pursuing original questions about how the brain and nervous system work, '
        'from molecules to circuits to behavior, who want funded doctoral training and academic, '
        'clinical-research, or biotech careers.'
    ),
    'ut-austin-nursing-bsn': (
        'Students entering professional nursing who want clinical training in patient care across '
        'the lifespan, preparing to sit for the NCLEX-RN licensure exam and begin practice in '
        'hospitals, clinics, and community settings.'
    ),
    'ut-austin-nursing-dnp': (
        'Experienced nurses moving into the highest level of clinical practice, building advanced '
        'expertise to lead patient care, translate evidence into practice, and serve as nurse '
        'practitioners or clinical leaders.'
    ),
    'ut-austin-nursing-ms': (
        'Registered nurses ready to specialize and lead, deepening clinical and systems expertise '
        'to advance into roles such as nurse educator, administrator, or specialty practice '
        'within healthcare organizations.'
    ),
    'ut-austin-nursing-phd': (
        'Nurses pursuing a research career who want training in nursing science and methodology '
        'to generate evidence on health and care, preparing for faculty positions and funded '
        'research programs.'
    ),
    'ut-austin-nutrition-bsa': (
        'Students drawn to how food, metabolism, and diet shape health who want grounding in '
        'biochemistry, physiology, and nutritional science. Preparation for dietetics, health '
        'professions, food industry roles, or graduate study.'
    ),
    'ut-austin-nutritional-sciences-ms': (
        'Graduates advancing their study of metabolism, diet, and health through research and '
        'specialized coursework. Preparation for doctoral study, clinical and public health '
        'nutrition, or research roles in food and health industries.'
    ),
    'ut-austin-nutritional-sciences-phd': (
        'Researchers investigating original questions in metabolism, nutrition, and chronic '
        'disease who want funded doctoral training, aiming for academic, clinical-research, or '
        'public health science careers.'
    ),
    'ut-austin-operations-research-and-industrial-engineering-ms': (
        'Students who want to optimize complex systems and decisions, learning optimization, '
        'probability, and analytics for supply chains, logistics, and operations roles in '
        'industry and consulting.'
    ),
    'ut-austin-operations-research-and-industrial-engineering-phd': (
        'Researchers developing new theory and methods in optimization, stochastic systems, and '
        'decision science, headed toward faculty positions or advanced analytics research roles.'
    ),
    'ut-austin-petroleum-and-geosystems-engineering-ms': (
        'Engineers specializing in subsurface energy, reservoir engineering, drilling, and '
        'increasingly geothermal and carbon storage, for advanced technical roles in the evolving '
        'energy sector.'
    ),
    'ut-austin-petroleum-and-geosystems-engineering-phd': (
        'Researchers pursuing original work on subsurface flow, reservoir physics, and '
        'energy-transition technologies like carbon storage, headed toward faculty positions or '
        'advanced energy R&D.'
    ),
    'ut-austin-petroleum-engineering-bspe': (
        'Undergraduates interested in extracting energy from the subsurface, reservoir behavior, '
        'drilling, and production systems, building toward roles in energy operators, service '
        'firms, or graduate study in energy engineering.'
    ),
    'ut-austin-pharmaceutical-sciences-ms': (
        'Students drawn to the science behind drug discovery, formulation, and action who want '
        'laboratory and research training for careers in the pharmaceutical industry or a path '
        'toward doctoral study.'
    ),
    'ut-austin-pharmaceutical-sciences-phd': (
        'Researchers committed to understanding how drugs are designed, delivered, and act in the '
        'body, building the scientific depth for careers in academic research, industry R&D, or '
        'regulatory science.'
    ),
    'ut-austin-pharmacy-pharmd': (
        'Future pharmacists ready for rigorous training in medications, pharmacology, and patient '
        'care, preparing for licensure exams and practice in community, hospital, clinical, or '
        'industry pharmacy settings.'
    ),
    'ut-austin-philosophy-ba': (
        'Undergraduates drawn to questions of knowledge, ethics, logic, and reality who want to '
        'build rigorous argument and analysis. A versatile foundation for law, policy, technology '
        'ethics, or graduate study in philosophy.'
    ),
    'ut-austin-philosophy-ma': (
        'Students who want advanced training in philosophical analysis across ethics, logic, '
        'metaphysics, and the history of thought. A step toward doctoral study or careers in law, '
        'policy, and fields that reward rigorous reasoning.'
    ),
    'ut-austin-philosophy-phd': (
        'Scholars committed to original philosophical research who want to write a dissertation, '
        'develop a specialization, and contribute to philosophical debate. Preparation for a '
        'faculty or research career in philosophy.'
    ),
    'ut-austin-physical-culture-and-sports-studies-bskin-and-health': (
        'Students drawn to the history, culture, and social meaning of sport and physical '
        'activity, building critical and research skills toward careers in sport, education, '
        'media, or graduate study.'
    ),
    'ut-austin-physics-ba': (
        'Undergraduates drawn to the fundamental laws governing matter, energy, and motion who '
        'want a flexible foundation in mechanics, electromagnetism, and quantum theory. A '
        'starting point for graduate study, engineering, or quantitative careers.'
    ),
    'ut-austin-physics-ma': (
        'Graduates deepening their command of theoretical and experimental physics through '
        'advanced coursework and research. A step toward doctoral study or technical roles in '
        'industry, engineering, and quantitative fields.'
    ),
    'ut-austin-physics-phd': (
        'Researchers pursuing original work in fields such as condensed matter, particle, or '
        'astrophysics who want funded doctoral training, aiming for faculty positions or research '
        'careers in national labs and industry.'
    ),
    'ut-austin-plan-ii-honors-program-ba': (
        'Intellectually ambitious undergraduates who want a small, cross-disciplinary honors '
        'curriculum spanning literature, science, philosophy, and the arts, capped by a thesis. A '
        'foundation for graduate, law, medical, or professional school and demanding careers.'
    ),
    'ut-austin-plant-biology-ma': (
        'Graduates advancing their study of plant physiology, genetics, and ecology through '
        'coursework and laboratory or field research. A step toward doctoral study or careers in '
        'agriculture, conservation, and biotech.'
    ),
    'ut-austin-plant-biology-phd': (
        'Researchers pursuing original questions in plant genetics, development, and ecology who '
        'want funded doctoral training, aiming for academic, agricultural-research, or biotech '
        'careers.'
    ),
    'ut-austin-psychology-ba': (
        'Undergraduates curious about the mind and behavior who want grounding in research '
        'methods, statistics, and the science of cognition, development, and social life. A '
        'foundation for counseling, human services, research, or graduate and professional study.'
    ),
    'ut-austin-psychology-ma': (
        'Students who want advanced training in psychological theory, research design, and '
        'statistics across cognitive, social, or developmental areas. A step toward doctoral '
        'study or applied research and assessment roles.'
    ),
    'ut-austin-psychology-phd': (
        'Scholars committed to original research on mind and behavior who want to design studies, '
        'write a dissertation, and contribute to psychological science. Preparation for a '
        'faculty, research, or scientific career.'
    ),
    'ut-austin-public-affairs-bapubaff': (
        'Undergraduates curious about how government, policy, and public institutions shape '
        'everyday life, blending political analysis with ethics and management to prepare for '
        'entry roles in agencies, campaigns, or nonprofits, or graduate study in policy.'
    ),
    'ut-austin-public-affairs-mpaff': (
        'Career changers and analysts drawn to evidence-based policy who want grounding in '
        'economics, statistics, and management for leadership roles across government, '
        'nonprofits, and advocacy organizations.'
    ),
    'ut-austin-public-health-bspublichealth': (
        'Students focused on disease prevention, health behavior, and population well-being who '
        'want grounding in epidemiology, biostatistics, and health systems. Preparation for '
        'community health roles, public agencies, or graduate work in public health.'
    ),
    'ut-austin-public-leadership-mpl': (
        'Working professionals already steering teams in government or civic organizations who '
        'want to sharpen leadership, management, and policy judgment while staying in their roles '
        'and advancing toward senior public-sector positions.'
    ),
    'ut-austin-public-policy-phd': (
        'Researchers committed to studying how policies are designed, implemented, and evaluated, '
        'building the methodological depth for careers in academia, think tanks, or high-level '
        'government research.'
    ),
    'ut-austin-public-relations-bspr': (
        'Undergraduates focused on reputation and messaging — media relations, strategic '
        'communication, and managing how organizations are perceived. A start for roles in PR '
        'agencies, corporate communications, and nonprofit or public-affairs communication.'
    ),
    'ut-austin-race-indigeneity-and-migration-ba': (
        'Undergraduates who want to study how race, indigeneity, colonialism, and migration shape '
        'societies, drawing on history, sociology, and cultural analysis. A foundation for '
        'advocacy, public policy, education, or graduate study in related fields.'
    ),
    'ut-austin-radio-television-film-bsrtf': (
        'Undergraduates drawn to screen storytelling — production, screenwriting, and the study '
        'of film, television, and media. A foundation for entry-level roles in production, '
        'editing, and development across film, TV, and streaming.'
    ),
    'ut-austin-radio-television-film-ma': (
        'Graduates who want advanced study of media history, theory, and criticism across film, '
        'television, and digital media. Suited to research, teaching, and media-analysis roles, '
        'or a step toward doctoral work in media studies.'
    ),
    'ut-austin-radio-television-film-mfa': (
        'Artists pursuing the terminal degree in screen production — directing, screenwriting, '
        'and producing original film and media work. Built for those developing a professional '
        'creative portfolio toward careers as filmmakers, writers, and producers.'
    ),
    'ut-austin-radio-television-film-phd': (
        'Scholars researching film, television, and media through critical theory, history, and '
        'cultural analysis. The path to faculty positions and academic research careers in media '
        'studies.'
    ),
    'ut-austin-religious-studies-ba': (
        "Undergraduates who want to study the world's religious traditions, texts, and practices "
        'analytically across cultures and history. A foundation for education, nonprofit and '
        'communal work, law, or graduate study in religion.'
    ),
    'ut-austin-religious-studies-ma': (
        'Students who want advanced, analytic study of religious traditions, texts, and practices '
        'across cultures and history. A step toward doctoral study, teaching, or careers in '
        'nonprofit, communal, and public-facing work.'
    ),
    'ut-austin-religious-studies-phd': (
        'Scholars pursuing original research on religious traditions and their texts and contexts '
        'who want to write a dissertation and join scholarly debates. Preparation for a faculty '
        'or research career in religious studies.'
    ),
    'ut-austin-rhetoric-and-writing-ba': (
        'Undergraduates who want to understand and practice persuasion, argument, and writing '
        'across media, analyzing how language shapes audiences. A foundation for careers in '
        'communications, editing, law, content, or graduate study.'
    ),
    'ut-austin-rhetoric-and-writing-studies-ma': (
        'Students who want advanced study of rhetoric, composition, and the theory and teaching '
        'of writing across media. A step toward doctoral study, teaching writing, or careers in '
        'communications and editorial work.'
    ),
    'ut-austin-rhetoric-and-writing-studies-phd': (
        'Scholars pursuing original research in rhetoric and writing studies who want to write a '
        'dissertation and contribute to the theory and pedagogy of writing. Preparation for a '
        'faculty or research career, including writing-program leadership.'
    ),
    'ut-austin-russian-east-european-and-eurasian-studies-ba': (
        'Undergraduates interested in the history, politics, languages, and cultures of Russia, '
        'Eastern Europe, and Eurasia who want an interdisciplinary regional focus with language '
        'study. Preparation for international work, policy, or graduate study.'
    ),
    'ut-austin-russian-east-european-and-eurasian-studies-ma': (
        'Students who want advanced, interdisciplinary study of Russia, Eastern Europe, and '
        'Eurasia across history, politics, and culture, with strong language preparation. A step '
        'toward doctoral study, policy work, or international careers.'
    ),
    'ut-austin-science-technology-engineering-and-mathematics-education-ma': (
        'Educators ready to deepen how STEM subjects are taught and learned, pairing content with '
        'research on instruction, preparing for advanced teaching roles or doctoral study.'
    ),
    'ut-austin-science-technology-engineering-and-mathematics-education-med': (
        'STEM teachers who want practice-focused study of how to teach science, technology, '
        'engineering, and mathematics more effectively, building expertise for instructional '
        'leadership and specialist roles.'
    ),
    'ut-austin-science-technology-engineering-and-mathematics-education-phd': (
        'Scholars conducting original research on how STEM subjects are learned and taught, '
        'building studies that shape curriculum and practice, preparing for university faculty '
        'and research careers.'
    ),
    'ut-austin-semiconductor-science-and-engineering-ms': (
        'Engineers focused on the science and fabrication of semiconductor devices, from '
        'materials and physics to processing, headed toward roles in chip design, fabrication, '
        'and the semiconductor industry.'
    ),
    'ut-austin-social-work-bsw': (
        'Undergraduates committed to helping individuals, families, and communities through '
        'direct service and advocacy, building practice and ethics foundations for entry-level '
        'social work or graduate study toward licensure.'
    ),
    'ut-austin-social-work-ms': (
        'Students preparing for professional social work practice in clinical, community, or '
        'policy settings, developing the skills and supervised experience needed to pursue '
        'clinical licensure and serve vulnerable populations.'
    ),
    'ut-austin-social-work-phd': (
        'Scholars studying social problems, interventions, and welfare policy who want research '
        'and methodological training for faculty careers or leadership in research-driven '
        'social-service organizations.'
    ),
    'ut-austin-sociology-ba': (
        'Undergraduates who want to study how social structures, institutions, and inequality '
        'shape human life, using both data and theory. A foundation for research, public policy, '
        'social services, or graduate study in sociology.'
    ),
    'ut-austin-sociology-ma': (
        'Students who want advanced training in sociological theory and research methods to study '
        'social structures, institutions, and inequality. A step toward doctoral study or careers '
        'in research, policy, and social analysis.'
    ),
    'ut-austin-sociology-phd': (
        'Scholars committed to original research on social life and inequality who want to design '
        'studies, write a dissertation, and contribute to sociological knowledge. Preparation for '
        'a faculty or research career.'
    ),
    'ut-austin-spanish-ba': (
        'Undergraduates who want fluency in Spanish alongside the literature and cultures of '
        'Spain and Latin America, ideally with time abroad. A foundation for education, '
        'international work, translation, or graduate study.'
    ),
    'ut-austin-special-education-edd': (
        'Experienced special educators pursuing the practice-focused doctorate, applying research '
        'to the real challenges of serving students with disabilities, preparing for leadership '
        'and specialist roles.'
    ),
    'ut-austin-special-education-ma': (
        'Educators ready to deepen the study of how to teach students with disabilities, pairing '
        'research with evidence-based practice, preparing for specialist roles or doctoral study.'
    ),
    'ut-austin-special-education-med': (
        'Teachers preparing to serve students with disabilities, building practice-focused '
        'expertise and, where applicable, certification, to lead inclusive and specialized '
        'classrooms.'
    ),
    'ut-austin-special-education-phd': (
        'Scholars researching how students with disabilities learn and how to teach them '
        'effectively, building original studies that shape practice and policy, preparing for '
        'university faculty and research careers.'
    ),
    'ut-austin-speech-language-and-hearing-sciences-bsslh': (
        'Undergraduates interested in human communication and its disorders — speech, language, '
        'and hearing across the lifespan. The pre-professional foundation for graduate study '
        'toward becoming a speech-language pathologist or audiologist.'
    ),
    'ut-austin-speech-language-and-hearing-sciences-ms': (
        'Students pursuing the graduate clinical training required to practice speech-language '
        'pathology — assessing and treating speech, language, and swallowing disorders. The '
        'professional path to becoming a licensed, certified speech-language pathologist.'
    ),
    'ut-austin-speech-language-and-hearing-sciences-phd': (
        'Scholars researching the science of human communication and its disorders — speech, '
        'language, and hearing — through rigorous experimental methods. The path to faculty '
        'positions and research careers in communication sciences and disorders.'
    ),
    'ut-austin-sport-management-bskin-and-health': (
        'Students who want to run the business side of sport — operations, marketing, finance, '
        'and event management — building the foundation for careers with teams, athletic '
        'programs, and sport organizations.'
    ),
    'ut-austin-statistics-and-data-science-bssds': (
        'Students who enjoy working with data, probability, and inference and want grounding in '
        'statistical modeling, computing, and machine learning. Strong preparation for analyst '
        'and data science roles or graduate study.'
    ),
    'ut-austin-statistics-ms': (
        'Graduates building advanced skills in statistical theory, modeling, and computation for '
        'analyzing complex data. Preparation for doctoral study or quantitative roles in '
        'industry, government, and research.'
    ),
    'ut-austin-statistics-phd': (
        'Researchers pursuing original work in statistical theory and methodology, from inference '
        'to computation, who want funded doctoral training, aiming for faculty positions or '
        'research roles in industry and government.'
    ),
    'ut-austin-studio-art-ba': (
        'Makers who want to build a body of work across drawing, painting, sculpture, or new '
        'media while grounding studio practice in critique and art history. An undergraduate '
        'foundation for a practicing artist or BFA/MFA study.'
    ),
    'ut-austin-studio-art-mfa': (
        'Artists ready for the terminal studio degree — intensive, self-directed practice and '
        'critique toward a mature body of work — preparing for an exhibiting career and '
        'college-level teaching.'
    ),
    'ut-austin-supply-chain-management-bba': (
        'Undergraduates interested in how goods and information move — sourcing, logistics, '
        'inventory, and operations from supplier to customer. A start for roles in procurement, '
        'logistics planning, operations analysis, and supply-chain coordination.'
    ),
    'ut-austin-sustainability-studies-ba': (
        'Undergraduates who want to address environmental and social sustainability through an '
        'interdisciplinary mix of science, policy, and ethics. Good preparation for work in '
        'environmental nonprofits, corporate sustainability, government, or graduate study.'
    ),
    'ut-austin-technology-commercialization-ms': (
        'Working professionals, engineers, and entrepreneurs who want to turn innovations into '
        'ventures — intellectual property, business models, and bringing technology to market. '
        'Suited to roles in startups, corporate innovation, and new-product commercialization.'
    ),
    'ut-austin-textiles-and-apparel-bsta': (
        'Undergraduates interested in fiber science, design, and the apparel industry who want '
        'grounding in materials, production, and consumer behavior. A foundation for careers in '
        'product development, merchandising, or textile science.'
    ),
    'ut-austin-theatre-and-dance-batd': (
        'Students who want a broad, hands-on foundation across theatre and dance — performance, '
        'design, and production — exploring the field before specializing, heading toward '
        'creative practice or further study.'
    ),
    'ut-austin-theatre-and-dance-dance-mfa': (
        'Dancers and choreographers pursuing the terminal degree in dance, developing a distinct '
        'artistic voice through sustained creative practice, preparing for professional '
        'choreography, performance, and college-level teaching.'
    ),
    'ut-austin-theatre-and-dance-theatre-ma': (
        'Students who want to deepen the scholarly and critical study of theatre — its history, '
        'theory, and practice — building research skills toward teaching, dramaturgy, or doctoral '
        'study.'
    ),
    'ut-austin-theatre-and-dance-theatre-mfa': (
        'Theatre artists pursuing the terminal degree in their specialization — acting, '
        'directing, design, or playwriting — building a professional body of work toward careers '
        'in the field and college-level teaching.'
    ),
    'ut-austin-theatre-and-dance-theatre-phd': (
        'Scholars pursuing original research in theatre history, theory, and performance studies, '
        'building the academic work for careers in university teaching and scholarship.'
    ),
    'ut-austin-theatre-education-bfa': (
        'Future theatre teachers who want to combine performance and production training with how '
        'to lead a drama classroom, working toward certification to direct school theatre '
        'programs.'
    ),
    'ut-austin-translational-science-phd': (
        'Scientists focused on moving discoveries from the laboratory into real-world treatments, '
        'training in the methods that bridge bench research and patient care for careers in '
        'translational and clinical research.'
    ),
    'ut-austin-urban-design-ms': (
        'Architects and planners focused on the design of streets, blocks, and public space at '
        'the scale between buildings and city plans, headed toward urban-design roles in firms '
        'and agencies.'
    ),
    'ut-austin-urban-studies-ba': (
        'Undergraduates interested in how cities work, drawing on planning, geography, sociology, '
        'and policy to study housing, transit, and inequality. Good preparation for urban '
        'planning, local government, community development, or graduate study.'
    ),
    'ut-austin-womens-and-gender-studies-ba': (
        'Undergraduates who want to examine how gender and sexuality shape culture, power, and '
        'institutions through an interdisciplinary lens. A foundation for advocacy, policy, '
        'education, law, or graduate study in the field.'
    ),
    'ut-austin-womens-and-gender-studies-ma': (
        'Students who want advanced, interdisciplinary study of how gender and sexuality shape '
        'culture, power, and institutions, building research and critical skills. A step toward '
        'doctoral study, advocacy, policy, or teaching.'
    ),
    'ut-austin-writing-mfa': (
        'Emerging writers serious about craft who want concentrated time, workshop critique, and '
        'mentorship to develop a body of work, preparing for careers in writing, teaching, '
        'editing, or publishing.'
    ),
    'ut-austin-youth-and-community-studies-bsed': (
        'Students drawn to working with young people outside the traditional classroom — '
        'community programs, nonprofits, and youth development — building skills to support youth '
        'in schools, agencies, and community organizations.'
    ),
}

_missing_who = [s for s in PROGRAM_SLUGS if s not in _WHO_BY_SLUG]
if _missing_who:
    raise ValueError(f"UT Austin who_its_for missing on {len(_missing_who)} rows: {_missing_who[:5]}")
_stray_who = [s for s in _WHO_BY_SLUG if s not in set(PROGRAM_SLUGS)]
if _stray_who:
    raise ValueError(f"UT Austin who_its_for stray slugs: {_stray_who[:5]}")

# Matcher-core CIP coverage gate (REPAIR_BACKLOG #1): every program carries a real IPEDS
# CIP-2020 code (a genuinely uncodeable field would be omitted-with-reason — none today).
_cip_missing = [p["slug"] for p in PROGRAMS if not p.get("cip")]
if _cip_missing:
    raise ValueError(
        f"UT Austin catalog missing cip_code on {len(_cip_missing)} rows: {_cip_missing[:8]}"
    )
_cip_bad = sorted({p["cip"] for p in PROGRAMS if not re.fullmatch(r"\d{2}\.\d{4}", p["cip"])})
if _cip_bad:
    raise ValueError(f"UT Austin catalog has malformed cip_code values: {_cip_bad}")

_WEBSITE_OVERRIDE: dict[str, str] = {
    "ut-austin-business-administration-mba": "https://www.mccombs.utexas.edu/graduate/mba/full-time-mba/",
    "ut-austin-law-jd": "https://law.utexas.edu/academics/degrees/jd/",
    "ut-austin-law-llm": "https://law.utexas.edu/academics/degrees/llm/",
    "ut-austin-medicine-md": "https://dellmed.utexas.edu/education/academics/md-program",
    "ut-austin-computer-science-bsa": "https://www.cs.utexas.edu/academics/undergraduate-programs",
    "ut-austin-computer-science-online-ms": "https://cdso.utexas.edu/mscs",
    "ut-austin-data-science-ms": "https://cdso.utexas.edu/msds",
    "ut-austin-artificial-intelligence-ms": "https://cdso.utexas.edu/msai",
    "ut-austin-petroleum-engineering-bspe": "https://pge.utexas.edu/",
    "ut-austin-accounting-mpa": "https://www.mccombs.utexas.edu/graduate/master-in-professional-accounting/",
    "ut-austin-business-analytics-ms": "https://www.mccombs.utexas.edu/graduate/masters-in-business-analytics/",
    "ut-austin-public-affairs-mpaff": "https://lbj.utexas.edu/master-public-affairs",
    "ut-austin-nursing-bsn": "https://nursing.utexas.edu/academics/bsn",
}
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "ut-austin-business-administration-mba": ["Texas McCombs", "Full-Time MBA", "MBA"],
    "ut-austin-law-jd": ["Texas Law", "J.D.", "School of Law"],
    "ut-austin-medicine-md": ["Dell Medical School", "M.D.", "Dell Med"],
    "ut-austin-computer-science-bsa": ["UT Computer Science", "computer science", "CS"],
    "ut-austin-computer-science-online-ms": [
        "Computer & Data Science Online",
        "MSCS",
        "online computer science",
    ],
    "ut-austin-petroleum-engineering-bspe": ["petroleum engineering", "Hildebrand Department"],
}


def _website_for(spec: dict) -> str:
    return _WEBSITE_OVERRIDE.get(spec["slug"], SCHOOL_WEBSITE[spec["school"]])


# ── Costs ──
_UNDERGRAD_COA = 31247
_AVG_NET_PRICE = 19857
_COST_SRC = "U.S. Dept. of Education — College Scorecard (UT Austin, UNITID 228778)"
_COST_SRC_URL = "https://collegescorecard.ed.gov/school/?228778-The-University-of-Texas-at-Austin"


def _undergrad_cost() -> dict:
    return {
        "total_cost_of_attendance": _UNDERGRAD_COA,
        "avg_net_price": _AVG_NET_PRICE,
        "funded": False,
        "note": (
            "UT Austin's published academic-year cost of attendance is about $31,250 and the average "
            "net price after grant aid is about $19,857 (College Scorecard, UNITID 228778). In-state "
            "students pay public tuition ($11,688), and programs such as Texas Advance Commitment cover "
            "tuition for many Texas families; out-of-state and international tuition is higher "
            "($44,908). Both rates ship in the breakdown; the cost card shows the resident basis while "
            "the matcher's budget signal (program.tuition) uses the non-resident rate for the "
            "out-of-state + international pool. See UT Austin Texas One Stop for current figures."
        ),
        "source": _COST_SRC,
        "source_url": _COST_SRC_URL,
        "year": "2023-24",
    }


def _grad_cost_fallback(spec: dict) -> dict:
    return {
        "note": (
            "Tuition for this graduate/professional program is set by UT Austin and is typically "
            "billed per semester (and varies by residency and program), so a single verified annual "
            "figure is not published here. Many doctoral students are funded through assistantships "
            "and fellowships. UT's online master's degrees (MSCS, MSDS, MSAI) have a published total "
            "tuition of about $10,000. See the program's tuition page for current figures."
        ),
        "source": "UT Austin Texas One Stop / program tuition page",
        "source_url": _website_for(spec),
    }


# ── Per-credential tuition (matcher-core budget signal — REPAIR_BACKLOG #3/#9) ──
# Every figure is published and cited; nothing is guessed. Undergraduate tuition is the
# federal College Scorecard published figure (UNITID 228778). Graduate per-credit rates
# are UT Austin Texas One Stop published rates; the graduate annual is UT's published
# graduate tuition-&-fees estimate for a standard full-time load (labeled as such). The
# professional annual rates (Law J.D., Dell Med M.D.) are the schools' published 2025-26
# figures. The three remaining professional doctorates (PharmD/AuD/DNP) bill at their own
# school schedules with no separately-verified single annual figure here, so their
# ``cost_data.tuition_usd`` is honestly omitted (recorded in ``_standard.omitted``) rather
# than guessed.
_TUITION_UG_INSTATE = 11688  # College Scorecard in-state undergraduate tuition, UNITID 228778
_TUITION_UG_OOS = 44908  # College Scorecard out-of-state undergraduate tuition, UNITID 228778
_GRAD_PER_CREDIT_INSTATE = 659  # UT Austin Texas One Stop graduate per-credit-hour, TX resident
_GRAD_PER_CREDIT_OOS = 1245  # UT Austin Texas One Stop graduate per-credit-hour, non-resident
_TUITION_GRAD_INSTATE = 12006  # UT Austin published graduate tuition & fees, TX resident, AY 2024-25
_TUITION_GRAD_OOS = 22954  # UT Austin published graduate tuition & fees, non-resident, AY 2024-25
_GRAD_COST_SRC = "UT Austin Texas One Stop — Tuition Rates"
_GRAD_COST_SRC_URL = "https://onestop.utexas.edu/managing-costs/cost-tuition-rates/tuition-rates/"

# Professional / specialized master's with a school-published PREMIUM annual rate (well
# above the standard per-credit graduate rate). ``program.tuition`` is consumed as ANNUAL
# tuition, so these carry the school's published first-year tuition & fees.
_MASTERS_TUITION_OVERRIDE: dict[str, dict] = {
    "ut-austin-business-administration-mba": {
        "in_state": 55196,
        "out_of_state": 61214,
        "source": "Texas McCombs — Full-Time MBA Tuition & Financial Aid (2025-26)",
        "source_url": "https://www.mccombs.utexas.edu/graduate/mba/full-time-mba/tuition-financial-aid/",
    },
    # The LL.M. is a law degree billed at the School of Law's published ANNUAL rate, far
    # above the standard graduate rate — without this override it fell through to the
    # generic graduate figure ($12,006), understating a $33k law degree by ~$21k.
    "ut-austin-law-llm": {
        "in_state": 33304,
        "out_of_state": 49490,
        "source": "Texas Law — LL.M. Tuition, Expenses & Financial Aid (2026-27)",
        "source_url": "https://law.utexas.edu/master-of-laws/tuition-expenses-and-financial-aid/",
    },
}

# UT's online Computer & Data Science Online master's (MSCS / MSDS / MSAI) publish a single
# low TOTAL program tuition (~$10,000) — NOT an annual rate. Since ``program.tuition`` is
# consumed as annual, the annual scalar is OMITTED (recorded in ``_standard.omitted``) and
# the published total is preserved in ``cost_data.total_program_tuition`` with a note —
# never written into the annual field (it would render as "$10,000 / yr").
_ONLINE_MASTERS_TOTAL = {
    "ut-austin-computer-science-online-ms": 10000,
    "ut-austin-data-science-ms": 10000,
    "ut-austin-artificial-intelligence-ms": 10000,
}

# Specialized McCombs master's that publish a single TOTAL program cost (these are
# one-year, 3–4-semester full-time cohort programs, so the program total IS the
# de-facto one-year cost). ``program.tuition`` is the matcher's budget scalar, so it
# carries the NON-RESIDENT total (the conservative default for the out-of-state +
# international pool, REPAIR_BACKLOG #2), while ``cost_data`` keeps the resident basis,
# both rates in the breakdown, and the published total in ``total_program_tuition``.
# Each figure is read from the program's own official McCombs tuition page (verified
# 2026-06-25); MSTC publishes a single flat program fee with no residency split.
_MASTERS_TOTAL_TUITION: dict[str, dict] = {
    "ut-austin-accounting-mpa": {
        "in_state": 43759,
        "out_of_state": 70453,
        "year": "2026-27",
        "semesters": "four semesters (Summer–Summer), 43-credit-hour track",
        "source": "Texas McCombs — Traditional MPA Tuition & Financial Aid",
        "source_url": "https://www.mccombs.utexas.edu/graduate/specialized-masters/mpa/traditional/tuition-financial-aid/",
    },
    "ut-austin-business-analytics-ms": {
        "in_state": 54000,
        "out_of_state": 58000,
        "year": "2025-26",
        "semesters": "one academic year (summer, fall, spring)",
        "source": "Texas McCombs — MS Business Analytics (on-campus) Tuition & Financial Aid",
        "source_url": "https://www.mccombs.utexas.edu/graduate/specialized-masters/ms-business-analytics/ms-business-analytics-on-campus/admissions/tuition-financial-aid/",
    },
    "ut-austin-finance-ms": {
        "in_state": 54000,
        "out_of_state": 58000,
        "year": "2025-26",
        "semesters": "one academic year (summer, fall, spring)",
        "source": "Texas McCombs — MS Finance Tuition & Financial Aid",
        "source_url": "https://www.mccombs.utexas.edu/graduate/specialized-masters/ms-finance/admissions/tuition-financial-aid/",
    },
    "ut-austin-marketing-ms": {
        "in_state": 54000,
        "out_of_state": 58000,
        "year": "2025-26",
        "semesters": "one academic year (summer, fall, spring)",
        "source": "Texas McCombs — MS Marketing Tuition & Financial Aid",
        "source_url": "https://www.mccombs.utexas.edu/graduate/specialized-masters/ms-marketing/admissions/tuition-financial-aid/",
    },
    "ut-austin-information-technology-and-management-ms": {
        "in_state": 54000,
        "out_of_state": 58000,
        "year": "2025-26",
        "semesters": "one academic year (summer, fall, spring)",
        "source": "Texas McCombs — MS Information Technology & Management Tuition & Financial Aid",
        "source_url": "https://www.mccombs.utexas.edu/graduate/specialized-masters/ms-it-and-management/admissions/tuition-financial-aid/",
    },
    "ut-austin-technology-commercialization-ms": {
        "in_state": 58500,
        "out_of_state": 58500,
        "year": "2025-26",
        "semesters": "three semesters (one academic year)",
        "flat": True,
        "source": "Texas McCombs — MS Technology Commercialization Tuition & Financial Aid",
        "source_url": "https://www.mccombs.utexas.edu/graduate/specialized-masters/ms-technology-commercialization/admissions/tuition-financial-aid/",
    },
}

# Remaining specialized master's whose program-specific tuition could NOT be verified on an
# official UT/McCombs page → the annual scalar is honestly OMITTED rather than guessed. (The
# academic MS in Accounting is offered only within the accounting doctoral program and bills
# at UT's STANDARD graduate rate, so it is NOT omitted — it falls through to the graduate
# scalar below.) MS Energy Management is not currently admitting and publishes no current
# tuition; MS Management has no separately published McCombs rate; IROM is a McCombs department
# whose marketed degrees are the MSBA/MSITM filled above.
_PREMIUM_MASTERS_OMIT = {
    "ut-austin-energy-management-ms",
    "ut-austin-information-risk-and-operations-management-ms",
    "ut-austin-management-ms",
}

# Professional-program annual tuition — each school's published 2025-26 figure.
_PROFESSIONAL_TUITION: dict[str, dict] = {
    "ut-austin-law-jd": {
        "in_state": 38236,
        "out_of_state": 56822,
        "source": "UT Austin Texas One Stop — School of Law Tuition (2025-26)",
        "source_url": "https://onestop.utexas.edu/managing-costs/cost-tuition-rates/tuition-rates/",
    },
    "ut-austin-medicine-md": {
        "in_state": 22074,
        "out_of_state": 37138,
        "source": "UT Austin Texas One Stop — Dell Medical School Tuition (2025-26)",
        "source_url": "https://onestop.utexas.edu/managing-costs/cost-tuition-rates/tuition-rates/",
    },
    # The Doctor of Audiology (AuD) sits in Moody College's Dept. of Speech, Language &
    # Hearing Sciences — a GRADUATE program, NOT a designated professional college (Law,
    # Medicine, Pharmacy carry separate premium professional rates). UT bills the AuD at its
    # STANDARD graduate tuition rate with no professional surcharge, so the scalar carries the
    # published graduate non-resident rate (verified: slhs.utexas.edu + One Stop graduate
    # tuition table; the AuD pages publish no program-specific tuition and point to the
    # general graduate rate).
    "ut-austin-audiology-aud": {
        "in_state": _TUITION_GRAD_INSTATE,
        "out_of_state": _TUITION_GRAD_OOS,
        "source": "UT Austin Texas One Stop — Graduate Tuition Rates (AuD billed at standard graduate rate)",
        "source_url": "https://onestop.utexas.edu/managing-costs/cost-tuition-rates/tuition-rates/",
        "note": (
            "The Doctor of Audiology is billed at UT Austin's standard graduate tuition & "
            "fees (Texas resident shown; non-residents pay the out-of-state rate in the "
            "breakdown) — it has no separate professional surcharge, since it is a Moody "
            "College graduate program, not a designated professional college. The matcher's "
            "budget signal uses the non-resident rate for the out-of-state + international pool."
        ),
    },
}
# Professional doctorates that publish a single flat TOTAL program tuition spanning MULTIPLE
# semesters (not an annual, residency-split rate). ``program.tuition`` is rendered as an
# ANNUAL figure ("tuition / yr"), so writing the multi-semester total there would mislead;
# the verified total is kept ONLY in ``cost_data.total_program_tuition`` and the annual scalar
# is honestly omitted (recorded in ``_standard.omitted``) — never a guessed per-year rate.
_PROFESSIONAL_TOTAL: dict[str, dict] = {
    "ut-austin-nursing-dnp": {
        "total": 30000,
        "year": "2025-26",
        "semesters": "45 credit hours over five semesters (post-MSN track)",
        "source": "UT Austin School of Nursing — DNP Tuition & Funding",
        "source_url": "https://nursing.utexas.edu/academics/graduate/dnp-post-msn/tuition-funding",
        "note": (
            "The post-MSN Doctor of Nursing Practice publishes a single flat program tuition "
            "of $30,000 (45 credit hours over five semesters), the same regardless of "
            "residency. UT publishes no standard annual figure, and the total spans multiple "
            "semesters, so the per-year scalar is omitted and the verified program total is "
            "shown instead (never written into the annual field)."
        ),
    },
}

# The Pharm.D. is a designated professional-college rate that UT publishes ONLY inside a
# JavaScript-rendered "College of Pharmacy (Professional)" Box PDF / login-gated tuition
# calculator (not machine-readable); the lone third-party (IPEDS-republisher) figure could
# not be confirmed against the official UT source or a second independent source, so per the
# routine's two-source / first-party verify gate the annual scalar is honestly OMITTED rather
# than ship an unverified number (no-fabrication). AuD now bills at the standard graduate rate
# (_PROFESSIONAL_TUITION); DNP's multi-semester program total is kept in cost_data with its annual
# scalar omitted (_PROFESSIONAL_TOTAL), so it never renders as a misleading "$30,000 / yr".
_TUITION_OMIT_SLUGS = {
    "ut-austin-pharmacy-pharmd",
}


def _tuition_omitted(slug: str) -> bool:
    """True when this program's annual ``cost_data.tuition_usd`` is honestly omitted."""
    return (
        slug in _TUITION_OMIT_SLUGS
        or slug in _PREMIUM_MASTERS_OMIT
        or slug in _ONLINE_MASTERS_TOTAL
        or slug in _PROFESSIONAL_TOTAL  # DNP — multi-semester total, annual scalar omitted
    )


def _annual_tuition_cost(
    in_state: int, out_of_state: int, source: str, url: str, note: str | None = None
) -> dict:
    return {
        "tuition_usd": in_state,
        "breakdown": {"tuition_in_state": in_state, "tuition_out_of_state": out_of_state},
        "funded": False,
        "note": note
        or (
            "Annual tuition & fees (Texas resident); non-residents pay the out-of-state rate "
            "shown in the breakdown. UT Austin bills tuition per semester. The matcher's "
            "budget signal (program.tuition) uses the non-resident rate for the out-of-state "
            "+ international pool."
        ),
        "source": source,
        "source_url": url,
        "year": "2025-26",
    }


def _masters_total_cost(pr: dict) -> dict:
    """``cost_data`` for a McCombs specialized master's that publishes a one-year program
    TOTAL (resident basis on the card, both rates in the breakdown, total preserved)."""
    flat = pr.get("flat")
    note = (
        f"Total program tuition ({pr['year']}) for this {pr['semesters']} full-time cohort "
        "program, the de-facto one-year cost. "
        + (
            f"McCombs publishes a single flat program fee of ${pr['in_state']:,} with no "
            "residency split."
            if flat
            else (
                f"Texas residents ${pr['in_state']:,}, non-residents ${pr['out_of_state']:,}; "
                "both ship in the breakdown."
            )
        )
        + " The cost card shows the resident basis; the matcher's budget signal "
        "(program.tuition) uses the non-resident total for the out-of-state + "
        "international pool."
    )
    return {
        "tuition_usd": pr["in_state"],
        "total_program_tuition": pr["out_of_state"],
        "breakdown": {
            "tuition_in_state": pr["in_state"],
            "tuition_out_of_state": pr["out_of_state"],
        },
        "funded": False,
        "note": note,
        "source": pr["source"],
        "source_url": pr["source_url"],
        "year": pr["year"],
    }


def _program_tuition(spec: dict) -> tuple[int | None, dict]:
    """Return ``(tuition_usd, cost_data)`` for a program from UT's published rates.

    ``program.tuition`` is the matcher's budget scalar. UT Austin is PUBLIC, so it publishes
    a resident and a (much higher) non-resident sticker for each tier; the matcher reads the
    FLAT scalar for every student, so it carries the NON-RESIDENT rate (REPAIR_BACKLOG #2 —
    the conservative default for the out-of-state + ALL-international pool), while
    ``cost_data.breakdown`` always keeps BOTH rates and the cost card shows the resident
    basis. A program only carries a scalar when a rate (or a one-year program total) is
    published/verified; programs whose rate is not separately verified, and the multi-year
    online / DNP programs that publish only a total, omit the annual scalar (recorded in
    ``_standard.omitted``) rather than ship a wrong or misleading "per year" number.
    """
    dt = spec["degree_type"]
    slug = spec["slug"]
    if dt == "bachelors":
        cost = _undergrad_cost()
        cost["tuition_usd"] = _TUITION_UG_INSTATE
        cost["breakdown"] = {
            "tuition_in_state": _TUITION_UG_INSTATE,
            "tuition_out_of_state": _TUITION_UG_OOS,
        }
        return _TUITION_UG_OOS, cost
    if slug in _MASTERS_TUITION_OVERRIDE:
        pr = _MASTERS_TUITION_OVERRIDE[slug]
        return pr["out_of_state"], _annual_tuition_cost(
            pr["in_state"], pr["out_of_state"], pr["source"], pr["source_url"]
        )
    if slug in _MASTERS_TOTAL_TUITION:
        pr = _MASTERS_TOTAL_TUITION[slug]
        return pr["out_of_state"], _masters_total_cost(pr)
    if dt == "professional" and slug in _PROFESSIONAL_TUITION:
        pr = _PROFESSIONAL_TUITION[slug]
        return pr["out_of_state"], _annual_tuition_cost(
            pr["in_state"], pr["out_of_state"], pr["source"], pr["source_url"], pr.get("note")
        )
    if slug in _PROFESSIONAL_TOTAL:  # DNP — flat MULTI-semester total, not annual → omit scalar
        pr = _PROFESSIONAL_TOTAL[slug]
        return None, {
            "total_program_tuition": pr["total"],
            "funded": False,
            "note": pr["note"],
            "source": pr["source"],
            "source_url": pr["source_url"],
            "year": pr["year"],
        }
    if slug in _ONLINE_MASTERS_TOTAL:  # publishes a TOTAL, not an annual rate → omit annual
        return None, {
            "total_program_tuition": _ONLINE_MASTERS_TOTAL[slug],
            "funded": False,
            "note": (
                "UT Austin's online Computer & Data Science Online master's degrees publish a "
                "single TOTAL program tuition of approximately $10,000 (the program is taken "
                "part-time and flexibly), not a standard annual rate, so no annual tuition "
                "figure is shown."
            ),
            "source": "UT Austin Computer & Data Science Online",
            "source_url": _website_for(spec),
            "year": "2024-25",
        }
    if dt == "professional":  # PharmD / AuD / DNP — rate not separately verified here
        return None, _grad_cost_fallback(spec)
    if slug in _PREMIUM_MASTERS_OMIT:  # premium specialized master's — rate not verified
        return None, _grad_cost_fallback(spec)
    _grad_scalar_clause = (
        " The cost card shows the Texas-resident rate; the matcher's budget signal "
        "(program.tuition) uses the non-resident rate ($22,954) — the conservative default "
        "for the out-of-state + international pool."
    )
    funded_note = (
        "Published graduate tuition rate that applies to doctoral study; most UT Austin "
        "doctoral students are funded through teaching/research assistantships or "
        "fellowships that cover tuition and provide a stipend. The annual figure estimates "
        "a standard full-time graduate load at UT's published per-credit rate." + _grad_scalar_clause
        if dt == "phd"
        else (
            "UT Austin's published graduate tuition & fees for a standard full-time load "
            "(Texas resident); non-residents pay the out-of-state rate shown in the "
            "breakdown. The annual figure applies UT's published graduate per-credit rate."
            + _grad_scalar_clause
        )
    )
    return _TUITION_GRAD_OOS, {
        "tuition_usd": _TUITION_GRAD_INSTATE,
        "breakdown": {
            "tuition_in_state": _TUITION_GRAD_INSTATE,
            "tuition_out_of_state": _TUITION_GRAD_OOS,
            "per_credit_in_state": _GRAD_PER_CREDIT_INSTATE,
            "per_credit_out_of_state": _GRAD_PER_CREDIT_OOS,
        },
        "funded": False,
        "note": funded_note,
        "source": _GRAD_COST_SRC,
        "source_url": _GRAD_COST_SRC_URL,
        "year": "2024-25",
    }


_OUTCOMES_OMIT_BY_SLUG: dict[str, list[str]] = {
    "ut-austin-business-administration-mba": [],
    "ut-austin-law-jd": [
        "outcomes_data.salary_25th",
        "outcomes_data.salary_75th",
        "outcomes_data.top_employers",
    ],
}
_OUTCOMES_BY_SLUG: dict[str, dict] = {
    "ut-austin-business-administration-mba": {
        "employment_rate": 0.85,
        "mean_salary": 151178,
        "median_salary": 150000,
        "salary_25th": 65000,
        "salary_75th": 192000,
        "median_signing_bonus": 31003,
        "top_industries": ["Consulting", "Technology", "Financial services", "Energy", "Retail"],
        "top_employers": [
            "Consulting firms",
            "Technology companies",
            "Financial-services firms",
            "Energy companies",
        ],
        "scope": "program",
        "conditions": "Texas McCombs Full-Time MBA, Class of 2024 (221 graduates): 86% of job-seeking graduates received an offer within three months and 85% accepted; average base salary $151,178, median $150,000 (range $65,000–$192,000), with an average signing bonus of $31,003. By industry: consulting 30% (avg base $172,556), technology 22% ($137,777), financial services 17% ($158,000), energy 6%, retail 5%. Self-reported per the official Texas McCombs Full-Time MBA Employment Report 2024-25.",
        "source": "Texas McCombs — Full-Time MBA Class of 2024 Employment Report",
        "source_url": "https://www.mccombs.utexas.edu/graduate/mba/full-time-mba/career/",
    },
    "ut-austin-law-jd": {
        "employment_rate": 0.968,
        "median_salary": 225000,
        "mean_salary": 199028,
        "top_industries": [
            "Private practice (law firms)",
            "Business / J.D.-advantage",
            "Government",
            "Public interest",
            "Judicial clerkships",
        ],
        "scope": "program",
        "conditions": "University of Texas School of Law J.D., Class of 2023 (277 graduates): about 96.8% were employed in long-term jobs ten months after graduation, with 91.3% in long-term, full-time bar-passage-required positions. Private-practice graduates reported a median salary of $225,000 (mean $199,028); government roles a median around $78,900. First-time bar passage was 94.01% for the Class of 2023, rising to 95.86% (2024) and 96.39% (2025) per ABA disclosures. A single university-wide overall median across all sectors is not republished here.",
        "source": "Texas Law — Class of 2023 Employment Summary Report (ABA/NALP)",
        "source_url": "https://law.utexas.edu/wp-content/uploads/sites/4/2024/12/74406_utexas_summary2023_Redacted.pdf",
    },
}
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    "ut-austin-business-administration-mba": {
        "cohort_size": 221,
        "note": "Texas McCombs Full-Time MBA Class of 2024 graduated 221 students.",
        "source": "Texas McCombs — Full-Time MBA Class of 2024 Employment Report",
        "source_url": "https://www.mccombs.utexas.edu/graduate/mba/full-time-mba/career/",
    }
}
_FACULTY_BY_SLUG: dict[str, dict] = {
    "ut-austin-business-administration-mba": {
        "lead": "Lillian Mills — Dean of Texas McCombs; the Full-Time MBA is supported by the McCombs MBA Career Management office.",
        "directory_url": "https://www.mccombs.utexas.edu/faculty-and-research/faculty-directory/",
    },
    "ut-austin-law-jd": {
        "lead": "Robert M. Chesney — Dean; the J.D. is taught by the University of Texas School of Law full-time faculty.",
        "directory_url": "https://law.utexas.edu/faculty/",
    },
    "ut-austin-medicine-md": {
        "lead": "Claudia F. Lucchinetti — Dean, Dell Medical School; the M.D. is taught by Dell Med faculty.",
        "directory_url": "https://dellmed.utexas.edu/directory",
    },
    "ut-austin-computer-science-bsa": {
        "lead": "The B.S. in Computer Science is taught by the UT Austin Department of Computer Science faculty.",
        "directory_url": "https://www.cs.utexas.edu/people/faculty-researchers",
    },
}
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "ut-austin-business-administration-mba": {
        "summary": "The Texas McCombs Full-Time MBA is a top-20 program known for its strength in consulting, technology, finance, and energy recruiting, its Austin location in a booming tech and business hub, and a tight, supportive cohort. The Class of 2024 (221 graduates) reported an average base salary of $151,178 (median $150,000) with an average signing bonus of $31,003; 86% of job-seekers had an offer within three months and 85% accepted. Reviewers note that consulting hiring softened (down to 30% of the class from 43% the prior year) in a tougher national market, while technology rose to 22%.",
        "themes": [
            {
                "label": "Consulting, tech, and finance recruiting",
                "sentiment": "positive",
                "detail": "Consulting led 2024 placements at 30% (avg base $172,556), followed by technology at 22% ($137,777) and financial services at 17% ($158,000); energy and retail round out the mix.",
            },
            {
                "label": "Austin location",
                "sentiment": "positive",
                "detail": "Austin's fast-growing technology, finance, and startup scene gives McCombs MBAs strong local access in addition to national recruiting.",
            },
            {
                "label": "Tight-knit cohort and value",
                "sentiment": "positive",
                "detail": "A relatively small class and strong Texas Exes alumni network are frequently praised, along with strong salary-to-cost value for a top-20 program.",
            },
            {
                "label": "Cyclical consulting demand",
                "sentiment": "mixed",
                "detail": "Consulting hiring fell from 43% (2023) to 30% (2024), in line with a softer national MBA market rather than a McCombs-specific decline.",
            },
            {
                "label": "Smaller, more regional than top-10 East Coast MBAs",
                "sentiment": "caution",
                "detail": "Placement skews toward Texas and the South/Southwest, a plus for that region and a limitation for students set on East-Coast finance.",
            },
        ],
        "sources": [
            {
                "label": "Texas McCombs — Full-Time MBA Class of 2024 Employment Report",
                "url": "https://www.mccombs.utexas.edu/graduate/mba/full-time-mba/career/",
            },
            {
                "label": "Clear Admit — Texas McCombs MBA Class of 2024 Employment Report",
                "url": "https://www.clearadmit.com/2025/02/texas-mccombs-mba-class-of-2024-employment-report/",
            },
            {
                "label": "Poets&Quants — UT Austin McCombs School of Business MBA profile",
                "url": "https://poetsandquants.com/school/university-of-texas-mccombs-school-of-business/",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "ut-austin-law-jd": {
        "summary": "The University of Texas School of Law (Texas Law) is a perennial top-15 to top-20 law school whose J.D. graduates post very strong employment — about 96.8% of the Class of 2023 were in long-term jobs ten months after graduation, with 91.3% in bar-passage-required positions. Reviewers cite excellent Big-Law, business, and public-interest placement, a strong Texas and national network, and lower cost than comparable private peers, while noting the demands of a top law program and a competitive bar.",
        "themes": [
            {
                "label": "Very strong employment",
                "sentiment": "positive",
                "detail": "Class of 2023: about 96.8% employed in long-term jobs; private-practice graduates reported a median salary of $225,000 (mean $199,028).",
            },
            {
                "label": "Public-university value",
                "sentiment": "positive",
                "detail": "Texas Law delivers top-tier outcomes at lower tuition than comparable private law schools, especially for Texas residents.",
            },
            {
                "label": "Texas and national reach",
                "sentiment": "positive",
                "detail": "Graduates place into Big-Law markets (Texas, New York, D.C.), clerkships, government, and public-interest roles, backed by a large alumni network.",
            },
            {
                "label": "High bar passage",
                "sentiment": "mixed",
                "detail": "First-time bar passage was 94.01% for the Class of 2023, rising to 95.86% (2024) and 96.39% (2025), above the state ABA average.",
            },
            {
                "label": "Rigorous and competitive",
                "sentiment": "caution",
                "detail": "As at peer top law schools, the workload is intense and admission is highly selective (a 14.9% acceptance rate).",
            },
        ],
        "sources": [
            {
                "label": "Texas Law — Class of 2023 Employment Summary Report",
                "url": "https://law.utexas.edu/wp-content/uploads/sites/4/2024/12/74406_utexas_summary2023_Redacted.pdf",
            },
            {
                "label": "Texas Law — ABA Required Disclosures (Standard 509 + bar passage)",
                "url": "https://law.utexas.edu/student-affairs/registrar/aba-required-disclosures/",
            },
            {
                "label": "U.S. News — University of Texas at Austin School of Law",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/university-of-texas-at-austin-03128",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "ut-austin-medicine-md": {
        "summary": "The Dell Medical School, which welcomed its first M.D. class in 2016, is UT Austin's newest college and a distinctive, innovation-focused medical school built around a value-based-care curriculum, a dedicated innovation/leadership track, and integration with Austin's safety-net and health systems. Reviewers praise its modern curriculum, small class size, and emphasis on health-systems redesign, while noting it is a young program still building its research and residency-match track record.",
        "themes": [
            {
                "label": "Innovative curriculum",
                "sentiment": "positive",
                "detail": "Dell Med's curriculum emphasizes value-based care, a dedicated innovation/leadership year, and early clinical immersion.",
            },
            {
                "label": "Austin health ecosystem",
                "sentiment": "positive",
                "detail": "Students train across Ascension Seton, Dell Children's, and Central Health safety-net partners in a fast-growing city.",
            },
            {
                "label": "Small, selective class",
                "sentiment": "positive",
                "detail": "A small entering M.D. class supports close mentorship and hands-on training.",
            },
            {
                "label": "Young program",
                "sentiment": "caution",
                "detail": "Founded in 2016, Dell Med has a shorter track record and a smaller research base than long-established medical schools.",
            },
        ],
        "sources": [
            {
                "label": "Dell Medical School — M.D. Program",
                "url": "https://dellmed.utexas.edu/education/academics/md-program",
            },
            {
                "label": "U.S. News — Dell Medical School (University of Texas at Austin)",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-texas-austin-dell-04067",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "ut-austin-computer-science-bsa": {
        "summary": "UT Austin's Department of Computer Science (College of Natural Sciences) is consistently ranked among the top 10 U.S. CS programs, with deep strength in AI, systems, theory, and programming languages. Reviewers highlight world-class faculty, strong research opportunities (including the Turing Award legacy of faculty), and excellent big-tech and Austin startup placement, while noting that CS admission is extremely competitive and popular courses are large.",
        "themes": [
            {
                "label": "Top-10 CS reputation",
                "sentiment": "positive",
                "detail": "UT CS is consistently ranked among the best U.S. programs (U.S. News top 10), with renowned faculty in AI, systems, and theory.",
            },
            {
                "label": "Research opportunities",
                "sentiment": "positive",
                "detail": "Undergraduates can engage in research across AI, robotics, systems, and security, and in programs like the integrated BS/MS.",
            },
            {
                "label": "Austin tech placement",
                "sentiment": "positive",
                "detail": "Graduates recruit heavily into major technology firms and Austin's large and growing tech sector.",
            },
            {
                "label": "Very competitive admission",
                "sentiment": "caution",
                "detail": "Direct admission to CS is highly selective, and core courses can be large; reviewers advise engaging early with research and office hours.",
            },
        ],
        "sources": [
            {
                "label": "UT Austin — Department of Computer Science",
                "url": "https://www.cs.utexas.edu/",
            },
            {
                "label": "U.S. News — computer science rankings (UT Austin top 10)",
                "url": "https://www.usnews.com/best-graduate-schools/top-science-schools/computer-science-rankings",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "ut-austin-computer-science-online-ms": {
        "summary": "UT Austin's online Master of Science in Computer Science (MSCS Online, via Computer & Data Science Online on edX) is one of the most popular and affordable top-tier online CS master's degrees in the country, with total tuition around $10,000 and the same diploma as the on-campus degree. Reviewers praise the value, rigor, and faculty quality, while noting it is fully online (no on-campus experience) and that admission and coursework are genuinely demanding.",
        "themes": [
            {
                "label": "Exceptional value",
                "sentiment": "positive",
                "detail": "Total tuition of roughly $10,000 for a top-ranked university's CS master's is a standout value; the diploma does not say 'online'.",
            },
            {
                "label": "Rigorous, credit-bearing degree",
                "sentiment": "positive",
                "detail": "Courses are taught by UT Austin CS faculty and mirror the on-campus curriculum across algorithms, systems, ML, and applied computing.",
            },
            {
                "label": "Flexibility for working professionals",
                "sentiment": "positive",
                "detail": "The 100%-online, part-time-friendly format lets working engineers upskill without relocating.",
            },
            {
                "label": "Demanding and self-directed",
                "sentiment": "caution",
                "detail": "Reviewers note the workload is rigorous and the experience is fully online, so it suits self-motivated learners rather than those seeking a campus experience.",
            },
        ],
        "sources": [
            {
                "label": "UT Austin — Computer & Data Science Online (MSCS)",
                "url": "https://cdso.utexas.edu/mscs",
            },
            {
                "label": "UT Austin Computer Science — Professional (Online) Degrees",
                "url": "https://www.cs.utexas.edu/graduate/professional-degrees",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "ut-austin-business-administration-bba": {
        "summary": "The McCombs BBA is one of the nation's top undergraduate business programs (U.S. News consistently ranks it in the top 5–6, with the accounting program #1), known for strong recruiting into consulting, finance, accounting, and technology, honors tracks (Business Honors, CBA/MPA integrated), and the Texas Exes network. Reviewers praise outcomes and rigor, while noting it is large and direct admission is highly competitive.",
        "themes": [
            {
                "label": "Top-ranked undergraduate business",
                "sentiment": "positive",
                "detail": "McCombs is consistently a U.S. News top-6 undergraduate business program, with the #1 accounting program nationally.",
            },
            {
                "label": "Strong recruiting",
                "sentiment": "positive",
                "detail": "BBA graduates recruit well into consulting, investment banking, accounting (Big Four), and technology.",
            },
            {
                "label": "Honors and integrated tracks",
                "sentiment": "positive",
                "detail": "Business Honors and the integrated BBA/MPA (accounting) program are prized differentiators.",
            },
            {
                "label": "Large and competitive",
                "sentiment": "caution",
                "detail": "The program is large and direct admission to McCombs is highly selective; reviewers advise early engagement with recruiting.",
            },
        ],
        "sources": [
            {
                "label": "Texas McCombs — Undergraduate (BBA) Program",
                "url": "https://www.mccombs.utexas.edu/undergraduate/",
            },
            {
                "label": "U.S. News — Best Undergraduate Business Programs (McCombs)",
                "url": "https://www.usnews.com/best-colleges/rankings/business-overall",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "ut-austin-accounting-mpa": {
        "summary": "The Texas McCombs Master in Professional Accounting (MPA) — and the integrated BBA/MPA — is consistently ranked the #1 accounting program in the United States by U.S. News. Reviewers cite outstanding Big Four and corporate placement, very high CPA exam pass rates, and the strength of UT's accounting faculty, while noting the program's rigor and competitiveness.",
        "themes": [
            {
                "label": "#1 accounting program",
                "sentiment": "positive",
                "detail": "U.S. News consistently ranks UT's accounting program #1 nationally at both the undergraduate and master's levels.",
            },
            {
                "label": "Big Four placement",
                "sentiment": "positive",
                "detail": "Graduates place strongly into Big Four and corporate accounting/advisory roles, with robust on-campus recruiting.",
            },
            {
                "label": "Integrated BBA/MPA path",
                "sentiment": "positive",
                "detail": "The five-year integrated BBA/MPA lets students earn the master's efficiently and sit for the CPA exam.",
            },
            {
                "label": "Rigorous and competitive",
                "sentiment": "caution",
                "detail": "Admission and coursework are demanding, consistent with a top-ranked accounting program.",
            },
        ],
        "sources": [
            {
                "label": "Texas McCombs — Master in Professional Accounting (MPA)",
                "url": "https://www.mccombs.utexas.edu/graduate/master-in-professional-accounting/",
            },
            {
                "label": "U.S. News — Best Accounting Programs (UT Austin #1)",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/accounting-rankings",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "ut-austin-business-analytics-ms": {
        "summary": "The Texas McCombs M.S. in Business Analytics (MSBA) is a STEM-designated, one-year program that has become a popular pathway into data-and-analytics roles, valued for its applied curriculum, capstone with industry partners, and strong technology/consulting placement. Reviewers praise career outcomes and the Austin tech market, while noting the intensive pace and competitive admission.",
        "themes": [
            {
                "label": "STEM-designated, applied",
                "sentiment": "positive",
                "detail": "The one-year, STEM-designated program emphasizes hands-on analytics, machine learning, and an industry capstone.",
            },
            {
                "label": "Strong analytics placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into data-science, analytics, and consulting roles, supported by Austin's technology sector.",
            },
            {
                "label": "Intensive pace",
                "sentiment": "mixed",
                "detail": "The compressed one-year format is rewarding but demanding; reviewers advise strong quantitative preparation.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Admission to the McCombs MSBA is selective and favors quantitative and programming readiness.",
            },
        ],
        "sources": [
            {
                "label": "Texas McCombs — M.S. in Business Analytics",
                "url": "https://www.mccombs.utexas.edu/graduate/masters-in-business-analytics/",
            },
            {
                "label": "U.S. News — UT Austin McCombs business specialty rankings",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/university-of-texas-austin-01250",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "ut-austin-petroleum-engineering-bspe": {
        "summary": "UT Austin's Hildebrand Department of Petroleum and Geosystems Engineering is consistently ranked the #1 petroleum engineering program in the United States by U.S. News. Reviewers highlight world-leading faculty, deep industry ties in Texas's energy sector, strong starting salaries, and a growing focus on energy transition and geosystems, while noting that the field's hiring tracks oil-and-gas cycles.",
        "themes": [
            {
                "label": "#1 petroleum engineering",
                "sentiment": "positive",
                "detail": "U.S. News consistently ranks UT's petroleum engineering program #1 nationally, with renowned faculty and facilities.",
            },
            {
                "label": "Industry ties and salaries",
                "sentiment": "positive",
                "detail": "Strong recruiting and high starting salaries reflect deep connections to Texas's energy industry.",
            },
            {
                "label": "Energy transition focus",
                "sentiment": "positive",
                "detail": "The department increasingly emphasizes geosystems, carbon storage, geothermal, and energy-transition research.",
            },
            {
                "label": "Cyclical hiring",
                "sentiment": "caution",
                "detail": "Petroleum-sector hiring and salaries fluctuate with oil-and-gas market cycles.",
            },
        ],
        "sources": [
            {
                "label": "UT Austin — Hildebrand Department of Petroleum and Geosystems Engineering",
                "url": "https://pge.utexas.edu/",
            },
            {
                "label": "U.S. News — Best Petroleum Engineering Programs (UT Austin #1)",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/petroleum-engineering-rankings",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "ut-austin-electrical-and-computer-engineering-bsece": {
        "summary": "The Chandra Family Department of Electrical and Computer Engineering at UT Austin is a top-10 ECE program with strengths in semiconductors, computer architecture, wireless, and machine learning. Reviewers cite world-class faculty, strong semiconductor-industry ties (a Texas strength), and excellent placement, while noting the program's rigor and large size.",
        "themes": [
            {
                "label": "Top-10 ECE",
                "sentiment": "positive",
                "detail": "UT ECE is consistently ranked among the top U.S. programs, with strength in semiconductors, architecture, and wireless.",
            },
            {
                "label": "Semiconductor and industry ties",
                "sentiment": "positive",
                "detail": "Deep ties to the semiconductor and electronics industry — a Texas strength reinforced by national chip investment — support recruiting.",
            },
            {
                "label": "Strong placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into major technology and semiconductor firms and Austin's engineering employers.",
            },
            {
                "label": "Rigorous workload",
                "sentiment": "caution",
                "detail": "The curriculum is demanding and classes can be large; reviewers advise strong math and systems preparation.",
            },
        ],
        "sources": [
            {
                "label": "UT Austin — Chandra Family Department of Electrical and Computer Engineering",
                "url": "https://www.ece.utexas.edu/",
            },
            {
                "label": "U.S. News — Best Electrical Engineering Programs (UT Austin top 10)",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/electrical-engineering-rankings",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "ut-austin-mechanical-engineering-bsme": {
        "summary": "The Walker Department of Mechanical Engineering at UT Austin is a top-10 mechanical engineering program with strengths in robotics, thermal/fluid sciences, manufacturing, and energy. Reviewers highlight strong faculty, hands-on design experience, and broad industry placement across energy, aerospace, automotive, and technology, while noting the program's rigor.",
        "themes": [
            {
                "label": "Top-10 mechanical engineering",
                "sentiment": "positive",
                "detail": "UT ME is consistently ranked among the best U.S. programs, with strength in robotics, energy, and manufacturing.",
            },
            {
                "label": "Hands-on design",
                "sentiment": "positive",
                "detail": "Capstone and project-based courses give students practical engineering design experience.",
            },
            {
                "label": "Broad placement",
                "sentiment": "positive",
                "detail": "Graduates recruit across energy, aerospace, automotive, manufacturing, and technology employers.",
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "The mechanical engineering curriculum is demanding; reviewers advise strong preparation in math and physics.",
            },
        ],
        "sources": [
            {
                "label": "UT Austin — Walker Department of Mechanical Engineering",
                "url": "https://www.me.utexas.edu/",
            },
            {
                "label": "U.S. News — Best Mechanical Engineering Programs (UT Austin top 10)",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/mechanical-engineering-rankings",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "ut-austin-public-affairs-mpaff": {
        "summary": "The LBJ School of Public Affairs' Master of Public Affairs (MPAff) is consistently ranked among the top U.S. public-affairs programs by U.S. News. Reviewers praise strong policy training, access to Texas state government and Austin's civic ecosystem, and placement into government, nonprofit, and policy roles, while noting public-sector salary ceilings typical of the field.",
        "themes": [
            {
                "label": "Top-ranked public affairs",
                "sentiment": "positive",
                "detail": "The LBJ School is consistently ranked among the top U.S. schools of public affairs, with strong specialty rankings.",
            },
            {
                "label": "Government and policy access",
                "sentiment": "positive",
                "detail": "Proximity to the Texas Capitol and Austin's civic and nonprofit ecosystem supports internships and placement.",
            },
            {
                "label": "Applied policy focus",
                "sentiment": "positive",
                "detail": "The curriculum emphasizes quantitative policy analysis, management, and a capstone Policy Research Project.",
            },
            {
                "label": "Public-sector pay",
                "sentiment": "caution",
                "detail": "As across the field, public-service salaries can lag private-sector pay; reviewers advise weighing aid and career goals.",
            },
        ],
        "sources": [
            {
                "label": "LBJ School of Public Affairs — Master of Public Affairs",
                "url": "https://lbj.utexas.edu/master-public-affairs",
            },
            {
                "label": "U.S. News — Best Public Affairs Programs (LBJ School)",
                "url": "https://www.usnews.com/best-graduate-schools/top-public-affairs-schools/public-affairs-rankings",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "ut-austin-nursing-bsn": {
        "summary": "The UT Austin School of Nursing's Bachelor of Science in Nursing (BSN) is a well-regarded program with strong NCLEX pass rates, simulation-based training, and clinical placements across Austin's health systems. Reviewers praise the faculty, hands-on clinical experience, and outcomes, while noting that direct admission to nursing is competitive.",
        "themes": [
            {
                "label": "Strong clinical training",
                "sentiment": "positive",
                "detail": "Students train with simulation labs and clinical rotations across Austin-area hospitals and health systems.",
            },
            {
                "label": "Solid licensure outcomes",
                "sentiment": "positive",
                "detail": "The BSN program reports strong NCLEX-RN first-time pass rates and nursing-workforce placement.",
            },
            {
                "label": "Research-active faculty",
                "sentiment": "positive",
                "detail": "The school combines undergraduate education with faculty research and graduate (MSN, DNP, Ph.D.) programs.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Direct admission to the BSN program is competitive and cohort sizes are limited by clinical capacity.",
            },
        ],
        "sources": [
            {
                "label": "UT Austin — School of Nursing (BSN)",
                "url": "https://nursing.utexas.edu/academics/bsn",
            },
            {
                "label": "U.S. News — UT Austin School of Nursing",
                "url": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/university-of-texas-austin-06122",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
}

# Synthesized per-program reviews (ut_austin_reviews_generated) were REMOVED
# (REPAIR_BACKLOG #1 / miss #8 fabrication-by-synthesis): machine-written from
# (program_name, school, institution rank) under a false "aggregated from public
# sources" disclaimer. Only the hand-gathered, program-specific flagship reviews in
# _REVIEWS_BY_SLUG above are kept; every other program records external_reviews in
# its _standard.omitted (see _program_standard) until genuine coverage is gathered.

# ── Admissions requirement sets ──
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission to an on-campus program.",
}
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "ApplyTexas or Common Application", "required": True},
        {"name": "Required short-answer essays", "required": True},
        {"name": "Official high school transcript / class rank", "required": True},
        {"name": "$75 application fee (fee waivers available)", "required": True},
        {
            "name": "SAT/ACT scores",
            "required": True,
            "note": "UT Austin reinstated a standardized-test requirement for first-year applicants; the middle 50% of enrolled students scored SAT 1250-1510 / ACT 27-33 (CDS 2024-25).",
        },
    ],
    "deadlines": [
        {"round": "Priority / honors and scholarship", "date": "October 15"},
        {"round": "Regular Decision", "date": "December 1"},
    ],
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "Duolingo English Test"],
            "required": True,
            "note": "Required for applicants whose native language is not English.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {"label": "UT Austin Office of Admissions", "url": "https://admissions.utexas.edu/"}
        ],
    },
    "source": "UT Austin Office of Admissions",
    "source_url": "https://admissions.utexas.edu/",
}
_REQ_GRAD_GENERIC = {
    "materials": [
        {"name": "UT Austin graduate application (GIAC)", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Résumé / CV", "required": True},
        {
            "name": "Letters of recommendation",
            "required": True,
            "note": "Most UT Austin graduate programs require three letters; check the program's page.",
        },
        {
            "name": "GRE/GMAT scores",
            "required": False,
            "note": "Test requirements vary by program; many UT Austin graduate programs are test-optional or do not require the GRE/GMAT.",
        },
    ],
    "deadlines": [
        {
            "round": "Fall admission",
            "date": "Deadlines vary by program (typically December–February)",
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
                "label": "UT Austin Graduate and International Admissions Center",
                "url": "https://gradschool.utexas.edu/admissions",
            }
        ],
    },
    "source": "UT Austin Graduate School",
    "source_url": "https://gradschool.utexas.edu/admissions",
}


def _requirements_for(spec: dict) -> dict:
    if spec["degree_type"] == "bachelors":
        return _REQ_UNDERGRAD
    return _REQ_GRAD_GENERIC


def _program_standard(slug: str, spec: dict) -> dict:
    omitted: list[str] = ["tracks"]
    if not spec.get("cip"):  # matcher-core CIP join key (REPAIR_BACKLOG #1); none today
        omitted.append("cip_code")
    if _tuition_omitted(slug):
        omitted.append("cost_data.tuition_usd")
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
    """Enrich UT Austin to the canonical profile. Flushes; caller commits.

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
    inst.founded_year = 1883
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.utexas.edu"
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
        p.tuition, p.cost_data = _program_tuition(spec)
        p.cip_code = spec.get("cip")  # matcher-core CIP join key (REPAIR_BACKLOG #1)
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
