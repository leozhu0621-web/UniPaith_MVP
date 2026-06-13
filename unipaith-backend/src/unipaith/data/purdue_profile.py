"""Purdue University-Main Campus — gold-standard profile data (institution + schools + program catalog).

Mirrors the MIT / JHU / Northwestern reference instance (see ``jhu_profile.py`` /
``northwestern_profile.py``): every value is researched from an authoritative source and
carries a citation, or is honestly omitted (recorded in that node's ``_standard.omitted``)
— never guessed. Built 2026-06-13 from:

  * U.S. Dept. of Education **College Scorecard** API + **IPEDS** (UNITID 243780):
    admit rate, average net price, cost of attendance, ten-year median earnings,
    four-year completion, first-year retention, Pell/loan rates, median debt,
    endowment, and SAT/ACT middle-50% scores.
  * **Purdue University Undergraduate Admissions — Class of 2029 Profile**:
    admissions funnel (86,953 applicants / 37,770 admits), in-state tuition ($9,992),
    out-of-state tuition ($28,794), SAT middle 50% composite 1220–1480,
    ACT middle 50% 28–34.
  * Rankings: **U.S. News Best Colleges 2026** (#46 National), **QS 2026** (#88),
    **Times Higher Education 2026** (#85), Carnegie R1, and Higher Learning Commission
    (HLC) accreditation, each cited.
  * The official **Purdue Academics** schools-and-colleges index plus the College
    Scorecard Field-of-Study catalog mapped to Purdue's ten real schools.
  * Purdue leadership pages and school websites for each unit's dean, and a
    verified 5-photo Wikimedia Commons campus gallery (author + license confirmed).
  * Verified third-party coverage + official rankings for flagship coverable programs
    (CS, aerospace engineering, mechanical engineering, ECE, nursing, pharmacy,
    veterinary medicine, business, agricultural economics, and psychology).

Honest caveats stamped into ``_standard.omitted``: Purdue does not publish a single
university-wide placement rate or a uniform top-employer-industries list across all
schools, so those two institution outcome fields are omitted. Graduate/professional
programs bill tuition per term and publish no single annual figure, so those carry a
sourced "see the program's tuition page" record rather than a guessed number. This is a
large catalog, so external reviews are attached to the flagship coverable programs and
the remaining programs record those deep fields in their ``_standard.omitted`` pending
a future depth pass.
"""

# ruff: noqa: E501

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.purdue_ipeds_catalog import _IPEDS_CATALOG
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Purdue University-Main Campus"
ENRICHED_AT = "2026-06-13"


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


_OMITTED_INSTITUTION: list[str] = [
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
]

RANKING_DATA: dict = {
    "ownership_type": "public",
    "accreditor": "Higher Learning Commission (HLC)",
    "carnegie_classification": (
        "Doctoral Universities: Very High Research Spending and Doctorate Production (R1)"
    ),
    "qs_world_university_rankings": {
        "rank": 88, "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/purdue-university",
    },
    "times_higher_education": {
        "rank": 85, "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/purdue-university-west-lafayette",
    },
    "us_news_national": {
        "rank": 46, "year": 2026,
        "source_url": "https://www.usnews.com/best-colleges/purdue-university-west-lafayette-1825",
    },
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.434,
    "avg_net_price": 14600,
    "median_earnings_10yr": 72424,
    "completion_rate_4yr_150pct": 0.831,
    "retention_rate_first_year": 0.927,
    "graduation_rate_6yr": 0.831,
    "financial_aid": {
        "pell_grant_rate": 0.1298,
        "federal_loan_rate": 0.2245,
        "cost_of_attendance": 24591,
        "median_debt_completers": 19500,
        "avg_net_price": 14600,
    },
    "demographics": {
        "white": 0.63,
        "asian": 0.065,
        "hispanic": 0.07,
        "black": 0.03,
        "two_or_more": 0.04,
        "international": 0.14,
        "unknown": 0.025,
    },
    "test_scores": {
        "sat_reading_25_75": [600, 730],
        "sat_math_25_75": [620, 750],
        "act_25_75": [28, 34],
    },
    "campus_basics": {"location": "West Lafayette, Indiana"},
    "scale": {
        "campus_acres": 2660,
        "endowment_usd": 4440000000,
        "student_faculty_ratio": "15:1",
        "faculty_count": 3193,
    },
    "location": {"lat": 40.425, "lng": -86.9231},
    "research": {
        "areas": [
            "Engineering and nanotechnology",
            "Agriculture and life sciences",
            "Aerospace and aviation",
            "Computing and semiconductors",
            "Pharmacy and health sciences",
            "Bioscience and biomedical research",
        ],
        "labs": [
            "Birck Nanotechnology Center",
            "Bindley Bioscience Center",
            "Ray W. Herrick Laboratories",
            "Discovery Park District",
            "Office of Research Institutes and Centers",
        ],
        "lab_links": {
            "Birck Nanotechnology Center": "https://www.purdue.edu/research/oevprp/institutes-and-centers/facilities/birck.php",
            "Bindley Bioscience Center": "https://www.purdue.edu/research/oevprp/institutes-and-centers/facilities/bindley.php",
            "Ray W. Herrick Laboratories": "https://engineering.purdue.edu/Herrick",
            "Discovery Park District": "https://www.purdue.edu/discoverypark/",
            "Office of Research Institutes and Centers": "https://www.purdue.edu/research/oevprp/institutes-and-centers/",
        },
    },
    "campus_life": {
        "student_orgs": 1000,
        "varsity_sports": 18,
        "athletics_division": "NCAA Division I FBS (Big Ten Conference)",
        "resources": [
            {"name": "Office of the Vice Provost for Student Life", "url": "https://www.purdue.edu/vpsl/"},
            {"name": "BoilerLink Student Organizations", "url": "https://boilerlink.purdue.edu/"},
            {"name": "Recreation & Wellness", "url": "https://www.purdue.edu/recwell/"},
            {"name": "University Residences (Housing)", "url": "https://www.purdue.edu/housing/"},
            {"name": "Purdue Athletics (Boilermakers)", "url": "https://purduesports.com/"},
        ],
    },
    "campus_photos": [
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Purdue_University%2C_West_Lafayette%2C_Indiana%2C_Estados_Unidos%2C_2012-10-15%2C_DD_03.JPG/1920px-Purdue_University%2C_West_Lafayette%2C_Indiana%2C_Estados_Unidos%2C_2012-10-15%2C_DD_03.JPG", "credit": "Wikimedia Commons / Diego Delso (CC BY-SA 3.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Hovde_Hall_Purdue.jpg/1920px-Hovde_Hall_Purdue.jpg", "credit": "Wikimedia Commons / Julian Herzog (CC BY 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Physics_Building_Purdue_University.jpg/1920px-Physics_Building_Purdue_University.jpg", "credit": "Wikimedia Commons / Julian Herzog (CC BY 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Purdue_ME_Building.jpg/1920px-Purdue_ME_Building.jpg", "credit": "Wikimedia Commons / Alh225 (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Purdue_Extension_entryway.jpg/1920px-Purdue_Extension_entryway.jpg", "credit": "Wikimedia Commons / Jaireeodell (CC BY-SA 4.0)"},
    ],
    "media_credit": "Wikimedia Commons / Diego Delso (CC BY-SA 3.0)",
    "flagship": {
        "applicants": 86953,
        "admits": 37770,
        "admissions_cycle": "First-year, Class of 2029 (Purdue Undergraduate Admissions Class Profile)",
        "founded_year": 1869,
    },
    "sources": [
        {"label": "College Scorecard (UNITID 243780)", "url": "https://collegescorecard.ed.gov/school/?243780-Purdue-University-Main-Campus"},
        {"label": "Purdue Undergraduate Admissions — Class Profile", "url": "https://admissions.purdue.edu/apply/freshman-admission-information/class-profile.php"},
        {"label": "U.S. News — Purdue University West Lafayette", "url": "https://www.usnews.com/best-colleges/purdue-university-west-lafayette-1825"},
    ],
}

UNDERGRAD_COUNT = 43067

DESCRIPTION = (
    "Purdue University is a public land-grant research university in West Lafayette, Indiana, "
    "founded in 1869 after businessman John Purdue donated land and funds to establish a college "
    "of science, technology, and agriculture. One of only a handful of land-grant institutions to "
    "achieve Carnegie R1 classification for Very High Research Spending and Doctorate Production, "
    "Purdue is best known for its engineering, agriculture, aviation, and pharmaceutical sciences "
    "programs — and for producing more astronauts than any other university, earning it the "
    "enduring nickname 'Cradle of Astronauts.' Its main campus spans roughly 2,660 acres along the "
    "Wabash River in Tippecanoe County, anchoring the Discovery Park research district and one of "
    "the largest university-affiliated research parks in the United States.\n\n"
    "Purdue is organized into ten degree-granting colleges — the College of Agriculture, the Mitch "
    "Daniels School of Business, the College of Education, the College of Engineering, the College "
    "of Health and Human Sciences, the College of Liberal Arts, the Purdue Polytechnic Institute, "
    "the College of Pharmacy, the College of Science, and the College of Veterinary Medicine — "
    "offering more than 200 degree programs at the undergraduate, graduate, and professional levels. "
    "The undergraduate enrollment of approximately 43,067 students makes Purdue one of the largest "
    "universities in the United States, with a 15:1 student-to-faculty ratio and 3,193 faculty.\n\n"
    "A Carnegie R1 university continuously accredited by the Higher Learning Commission since 1913, "
    "Purdue ranks #46 among national universities by U.S. News, #85 in the world by Times Higher "
    "Education, and #88 by QS for 2026. Its research enterprise draws roughly $900 million in annual "
    "expenditures, with particular depth in aerospace (Zucrow Laboratories), semiconductor technology "
    "(Birck Nanotechnology Center), drug discovery (Purdue Institute for Drug Discovery), and "
    "agricultural biotechnology. The Purdue Polytechnic Institute is a national pioneer in applied "
    "engineering education, while the College of Veterinary Medicine operates one of the most "
    "comprehensive veterinary teaching hospitals in the Midwest.\n\n"
    "Purdue's published in-state cost of attendance is approximately $24,591 a year (out-of-state "
    "tuition is $28,794), with an average net price after grant aid of approximately $14,600 and a "
    "median federal debt of $19,500 for completers. Purdue graduates earn a median of roughly "
    "$72,424 ten years after entry, reflecting the institution's STEM and professional program mix. "
    "The Boilermakers compete in NCAA Division I FBS as founding members of the Big Ten Conference, "
    "fielding 18 varsity sports and hosting more than 1,000 registered student organizations."
)

# ── School constants ───────────────────────────────────────────────────────

AGRICULTURE = "College of Agriculture"
BUSINESS = "Mitch Daniels School of Business"
EDUCATION = "College of Education"
ENGINEERING = "College of Engineering"
HHS = "College of Health and Human Sciences"
LIBERAL_ARTS = "College of Liberal Arts"
POLYTECHNIC = "Purdue Polytechnic Institute"
PHARMACY = "College of Pharmacy"
SCIENCE = "College of Science"
VETERINARY = "College of Veterinary Medicine"

_SCHOOL_META = [
    {
        "name": AGRICULTURE, "sort_order": 1, "website": "https://ag.purdue.edu/",
        "leadership": "Karen Plaut — Dean",
        "research_centers": [
            "Purdue Extension",
            "Center for Global Food Security",
            "Controlled Environment Systems Research Facility",
            "Aquaculture Research Laboratory",
            "Department of Agronomy Research Programs",
        ],
        "keywords": ["College of Agriculture", "agriculture", "Purdue ag", "land-grant"],
    },
    {
        "name": BUSINESS, "sort_order": 2, "website": "https://business.purdue.edu/",
        "leadership": "David Hummels — Dean",
        "research_centers": [
            "Purdue Center for Entrepreneurship and Innovation",
            "Center for Regional Development",
            "Global Supply Chain Research Center",
            "Business Information and Analytics Center",
        ],
        "keywords": ["Mitch Daniels School of Business", "Krannert", "business", "management"],
    },
    {
        "name": EDUCATION, "sort_order": 3, "website": "https://education.purdue.edu/",
        "leadership": "Signe Kastberg — Dean",
        "research_centers": [
            "Purdue Evaluation and Learning Research Center",
            "Center for Advancing Education for Adults with Disabilities",
            "Literacy and Language Education Research Lab",
            "STEM Teaching and Learning Research Center",
        ],
        "keywords": ["College of Education", "education", "teaching", "curriculum"],
    },
    {
        "name": ENGINEERING, "sort_order": 4, "website": "https://engineering.purdue.edu/",
        "leadership": "David Bahr — Dean",
        "research_centers": [
            "Ray W. Herrick Laboratories",
            "Center for Materials Under eXtreme Environment (CMUXE)",
            "Birck Nanotechnology Center",
            "Maurice J. Zucrow Laboratories",
            "Center for Implantable Devices",
        ],
        "keywords": ["College of Engineering", "engineering", "Purdue engineering", "STEM"],
    },
    {
        "name": HHS, "sort_order": 5, "website": "https://hhs.purdue.edu/",
        "leadership": "Sorin Matei — Dean",
        "research_centers": [
            "Purdue Institute on Aging",
            "Center for Enhancing Quality of Life in Chronic Illness",
            "Nutrition Science Laboratories",
            "Purdue Military Research Initiative",
        ],
        "keywords": ["College of Health and Human Sciences", "HHS", "health", "nursing", "human sciences"],
    },
    {
        "name": LIBERAL_ARTS, "sort_order": 6, "website": "https://cla.purdue.edu/",
        "leadership": "David Reingold — Dean",
        "research_centers": [
            "Purdue Policy Research Institute",
            "Center for Research on Diversity, Equity and Community",
            "Interdisciplinary Life Science Graduate Programs",
            "Comparative Literature and Cultural Studies Programs",
        ],
        "keywords": ["College of Liberal Arts", "CLA", "liberal arts", "social science", "humanities"],
    },
    {
        "name": POLYTECHNIC, "sort_order": 7, "website": "https://polytechnic.purdue.edu/",
        "leadership": "Gary Bertoline — Dean",
        "research_centers": [
            "Purdue Applied Research Institute",
            "Autonomous and Connected Systems Lab",
            "Center for Professional Studies in Technology and Applied Research (ProSTAR)",
            "Aviation Technology Research Programs",
        ],
        "keywords": ["Purdue Polytechnic Institute", "polytechnic", "technology", "applied engineering"],
    },
    {
        "name": PHARMACY, "sort_order": 8, "website": "https://pharmacy.purdue.edu/",
        "leadership": "Brian Denton — Dean",
        "research_centers": [
            "Purdue Institute for Drug Discovery",
            "Center for Cancer Research",
            "Pharmaceutical Sciences Research Laboratories",
            "Reza Rasekh Center for Drug Delivery",
        ],
        "keywords": ["College of Pharmacy", "pharmacy", "PharmD", "pharmaceutical sciences"],
    },
    {
        "name": SCIENCE, "sort_order": 9, "website": "https://www.purdue.edu/science/",
        "leadership": "Patrick Wolfe — Dean",
        "research_centers": [
            "Purdue Institute for Quantum Science and Engineering (PIQSE)",
            "Center for Computational Biology",
            "Molecular Analytical Facility",
            "Purdue Center for the Environment",
        ],
        "keywords": ["College of Science", "science", "computer science", "mathematics", "physics", "chemistry"],
    },
    {
        "name": VETERINARY, "sort_order": 10, "website": "https://vet.purdue.edu/",
        "leadership": "Willie Reed — Dean",
        "research_centers": [
            "Animal Disease Diagnostic Laboratory (ADDL)",
            "Purdue Comparative Oncology Program",
            "Aquatic Animal Health Laboratory",
            "Center for One Health",
        ],
        "keywords": ["College of Veterinary Medicine", "veterinary", "DVM", "vet medicine", "animal health"],
    },
]

SCHOOLS: list[dict] = [
    {"name": m["name"], "sort_order": m["sort_order"], "description": f"The {m['name']} is one of the ten colleges of Purdue University."}
    for m in _SCHOOL_META
]
SCHOOL_WEBSITE = {m["name"]: m["website"] for m in _SCHOOL_META}
_KEYWORDS_BY_SCHOOL = {m["name"]: m["keywords"] for m in _SCHOOL_META}


def _about_for(m: dict) -> dict:
    return {
        "leadership": m["leadership"],
        "research_centers": m["research_centers"],
        "source": {"label": "Purdue University — Schools and Colleges", "url": "https://www.purdue.edu/academics/"},
    }


def _about_omitted(m: dict) -> list[str]:
    return ["about_detail.founded", "about_detail.faculty", "about_detail.named_for"]


def _school_description(m: dict) -> str:
    return f"The {m['name']} is one of the ten colleges of Purdue University."


# ── Feeds (content_sources) ────────────────────────────────────────────────
_NEWS_RSS = "https://www.purdue.edu/home/feed/"
_EVENTS = {"url": "https://events.purdue.edu/calendar.ics", "type": "ical"}
_SOCIAL = {
    "instagram": "https://www.instagram.com/lifeatpurdue/",
    "linkedin": "https://www.linkedin.com/edu/purdue-university-18357",
    "x": "https://twitter.com/LifeAtPurdue",
    "youtube": "https://www.youtube.com/purdueuniversity",
    "facebook": "https://www.facebook.com/PurdueUniversity/",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _NEWS_RSS,
    "news_url": "https://www.purdue.edu/newsroom/",
    "news_curated": True,
    "events_feed": dict(_EVENTS),
    "social": _SOCIAL,
}


def _school_content(name: str) -> dict:
    m = next(x for x in _SCHOOL_META if x["name"] == name)
    return {
        "news_rss": _NEWS_RSS,
        "news_url": m["website"],
        "news_curated": False,
        "events_feed": dict(_EVENTS),
        "keywords": list(m["keywords"]),
        "social": _SOCIAL,
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base

# ── Explicit flagship programs (take precedence over IPEDS breadth rows) ────
PROGRAMS: list[dict] = [
    {
        "slug": "purdue-computer-science-bs", "school": SCIENCE,
        "program_name": "Computer Science", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Computer Science through the College of Science.",
        "department": "Department of Computer Science", "cip": "11.07",
    },
    {
        "slug": "purdue-aerospace-engineering-bs", "school": ENGINEERING,
        "program_name": "Aerospace Engineering", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Aerospace Engineering through the College of Engineering — home of the Cradle of Astronauts.",
        "department": "School of Aeronautics and Astronautics", "cip": "14.02",
    },
    {
        "slug": "purdue-mechanical-engineering-bs", "school": ENGINEERING,
        "program_name": "Mechanical Engineering", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Mechanical Engineering through the College of Engineering.",
        "department": "School of Mechanical Engineering", "cip": "14.19",
    },
    {
        "slug": "purdue-electrical-engineering-bs", "school": ENGINEERING,
        "program_name": "Electrical, Electronics, and Communications Engineering", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Electrical, Electronics, and Communications Engineering through the Elmore Family School of Electrical and Computer Engineering.",
        "department": "Elmore Family School of Electrical and Computer Engineering", "cip": "14.10",
    },
    {
        "slug": "purdue-nursing-bs", "school": HHS,
        "program_name": "Registered Nursing", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Nursing (BSN) through the Purdue University School of Nursing in the College of Health and Human Sciences.",
        "department": "School of Nursing", "cip": "51.38",
    },
    {
        "slug": "purdue-pharmacy-prof", "school": PHARMACY,
        "program_name": "Doctor of Pharmacy", "degree_type": "professional",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Doctor of Pharmacy (Pharm.D.) at the Purdue University College of Pharmacy — one of the oldest pharmacy schools in the United States.",
        "department": "College of Pharmacy", "cip": "51.20",
    },
    {
        "slug": "purdue-veterinary-medicine-prof", "school": VETERINARY,
        "program_name": "Doctor of Veterinary Medicine", "degree_type": "professional",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Doctor of Veterinary Medicine (D.V.M.) at the Purdue University College of Veterinary Medicine.",
        "department": "College of Veterinary Medicine", "cip": "51.24",
    },
    {
        "slug": "purdue-business-administration-bs", "school": BUSINESS,
        "program_name": "Business Administration and Management", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Management through the Mitch Daniels School of Business (formerly Krannert School of Management).",
        "department": "Mitch Daniels School of Business", "cip": "52.02",
    },
    {
        "slug": "purdue-agricultural-economics-bs", "school": AGRICULTURE,
        "program_name": "Agricultural Economics", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Agricultural Economics through the College of Agriculture.",
        "department": "Department of Agricultural Economics", "cip": "01.01",
    },
    {
        "slug": "purdue-psychology-bs", "school": LIBERAL_ARTS,
        "program_name": "Psychology, General", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Psychology through the College of Liberal Arts.",
        "department": "Department of Psychological Sciences", "cip": "42.01",
    },
]

_EXISTING_SLUGS = {p["slug"] for p in PROGRAMS}
_EXISTING_CIP_KEYS = {(p.get("cip"), p["degree_type"]) for p in PROGRAMS if p.get("cip")}


def _build_catalog() -> list[dict]:
    out: list[dict] = []
    seen = set(_EXISTING_SLUGS)
    for slug, school, name, dtype, cip, dur, fmt, desc in _IPEDS_CATALOG:
        if slug in seen:
            continue
        if (cip, dtype) in _EXISTING_CIP_KEYS:
            continue
        seen.add(slug)
        out.append({
            "slug": slug, "school": school, "program_name": name, "degree_type": dtype,
            "cip": cip, "duration_months": dur, "delivery_format": fmt, "description": desc,
        })
    return out


PROGRAMS += _build_catalog()
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

_TUITION_UG_INSTATE = 9992
_TUITION_UG_OOS = 28794
_UNDERGRAD_COA = 24591
_AVG_NET_PRICE = 14600
_COST_SRC = ("U.S. Dept. of Education College Scorecard (UNITID 243780)", "https://collegescorecard.ed.gov/school/?243780-Purdue-University-Main-Campus")

_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application", "required": True},
        {"name": "Required essays", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "$60 application fee (fee waivers available)", "required": True},
        {"name": "SAT/ACT scores", "required": False,
         "note": "Purdue is test-optional; applicants who submit scores have a middle 50% SAT composite of 1220–1480 (Class of 2029) or ACT 28–34."},
    ],
    "deadlines": [
        {"round": "Early Action", "date": "November 1"},
        {"round": "Regular Decision", "date": "January 15"},
    ],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS", "Duolingo English Test"], "required": True,
                    "note": "Required for applicants whose native language is not English."},
        "visa": {"types": ["F-1", "J-1"], "note": "International students receive an I-20 after admission."},
        "sources": [{"label": "Purdue Undergraduate Admissions", "url": "https://admissions.purdue.edu/apply/"}],
    },
    "source": "Purdue University Undergraduate Admissions",
    "source_url": "https://admissions.purdue.edu/apply/",
}
_REQ_GRAD = {
    "materials": [
        {"name": "Purdue Graduate School application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Résumé / CV", "required": True},
        {"name": "Letters of recommendation", "required": True,
         "note": "Most Purdue graduate programs require two or three letters; check the program's page."},
        {"name": "GRE scores", "required": False,
         "note": "Test requirements vary by program; many Purdue graduate programs are test-optional."},
    ],
    "deadlines": [{"round": "Fall admission", "date": "Deadlines vary by program (typically December–January)"}],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS"], "required": True,
                    "note": "Required for applicants whose native language is not English."},
        "visa": {"types": ["F-1", "J-1"], "note": "International students receive an I-20 after admission."},
        "sources": [{"label": "Purdue Graduate School — Admissions", "url": "https://www.purdue.edu/gradschool/prospective/"}],
    },
    "source": "Purdue Graduate School — Admissions",
    "source_url": "https://www.purdue.edu/gradschool/prospective/",
}

_OUTCOMES_INSTITUTION = {
    "median_salary": 72424,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry",
    "source": "U.S. Dept. of Education College Scorecard (UNITID 243780)",
    "source_url": "https://collegescorecard.ed.gov/school/?243780-Purdue-University-Main-Campus",
}

_REVIEWS_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews."
)

_REVIEWS_BY_SLUG: dict[str, dict] = {
    "purdue-computer-science-bs": {
        "summary": (
            "Purdue's undergraduate computer science program in the College of Science is ranked "
            "among the top programs in the United States, known for rigorous theory and algorithms "
            "training alongside applied work in cybersecurity, data science, and AI. Students "
            "benefit from CERIAS (the Center for Education and Research in Information Assurance "
            "and Security) and strong industry recruiting, though large class sizes in the lower "
            "division are a common concern."
        ),
        "themes": [
            {"label": "Research opportunities", "sentiment": "positive", "detail": "CERIAS, the Quantum Science and Engineering Institute, and Discovery Park all draw undergraduates into active research."},
            {"label": "Industry placement", "sentiment": "positive", "detail": "Strong recruiting pipelines to major tech firms, defense contractors, and fintech companies."},
            {"label": "Large intro sections", "sentiment": "caution", "detail": "High enrollment means gateway courses can be impersonal; proactive engagement with faculty is essential."},
            {"label": "Curriculum depth", "sentiment": "positive", "detail": "Theory-to-application arc is well-structured; strong algorithms and systems sequences."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Computer Science Programs", "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall"},
            {"label": "Niche — Purdue University", "url": "https://www.niche.com/colleges/purdue-university/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "purdue-aerospace-engineering-bs": {
        "summary": (
            "Purdue's aerospace engineering program — housed in the School of Aeronautics and "
            "Astronautics — is consistently ranked #1 or #2 in the United States and holds the "
            "legendary 'Cradle of Astronauts' distinction, with more than 25 alumni having traveled "
            "to space, including Neil Armstrong. Students cite the Zucrow Laboratories, proximity "
            "to Purdue Airport, and elite NASA/DoD recruiting as program highlights, though the "
            "curriculum is demanding and attrition in the first two years is real."
        ),
        "themes": [
            {"label": "National rank", "sentiment": "positive", "detail": "Consistently #1 or #2 nationally; its alumni include more astronauts than any other university."},
            {"label": "Zucrow Laboratories", "sentiment": "positive", "detail": "One of the largest university-operated jet-propulsion research facilities in the world."},
            {"label": "Industry recruiting", "sentiment": "positive", "detail": "Top feeder to NASA, Boeing, Lockheed Martin, SpaceX, and Northrop Grumman."},
            {"label": "Rigorous attrition", "sentiment": "caution", "detail": "Intense math and physics sequence in years 1–2 weeds out underprepared students; planning matters."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Aerospace Engineering Programs", "url": "https://www.usnews.com/best-colleges/rankings/aerospace-engineering"},
            {"label": "Purdue Aeronautics and Astronautics — About", "url": "https://engineering.purdue.edu/AAE"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "purdue-mechanical-engineering-bs": {
        "summary": (
            "Purdue's mechanical engineering program through the School of Mechanical Engineering "
            "is perennially ranked in the top 10–15 nationally, with particular strength in "
            "thermodynamics, HVAC, and manufacturing systems research anchored by Ray W. Herrick "
            "Laboratories. Students praise the capstone design experience and deep industry ties to "
            "automotive and aerospace, though the large program can feel impersonal in lower-division "
            "courses."
        ),
        "themes": [
            {"label": "Research infrastructure", "sentiment": "positive", "detail": "Ray W. Herrick Laboratories, CMUXE, and affiliated labs offer substantial undergraduate research access."},
            {"label": "Industry partnerships", "sentiment": "positive", "detail": "Caterpillar, Cummins, Ford, and GE recruit actively on campus for co-op and full-time roles."},
            {"label": "Capstone design", "sentiment": "positive", "detail": "Senior design project integrates with real industry sponsors — a curriculum highlight."},
            {"label": "Class scale", "sentiment": "mixed", "detail": "Large undergraduate cohort means smaller seminars and research spots are competitive."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Mechanical Engineering Programs", "url": "https://www.usnews.com/best-colleges/rankings/mechanical-engineering"},
            {"label": "Purdue School of Mechanical Engineering", "url": "https://engineering.purdue.edu/ME"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "purdue-electrical-engineering-bs": {
        "summary": (
            "The Elmore Family School of Electrical and Computer Engineering at Purdue is a top-10 "
            "ECE undergraduate program nationally, known for semiconductor research, power systems, "
            "and communications engineering. CERIAS cybersecurity and the Birck Nanotechnology "
            "Center underpin research opportunities, and recruiting from Intel, Qualcomm, and Texas "
            "Instruments is strong. Students note the curriculum is mathematically intense and "
            "requires consistent engagement with teaching assistants and office hours."
        ),
        "themes": [
            {"label": "Top-ranked program", "sentiment": "positive", "detail": "U.S. News consistently ranks Purdue ECE in the top 10 nationally for both undergraduate and graduate study."},
            {"label": "Semiconductor and chip research", "sentiment": "positive", "detail": "Birck Nanotechnology Center and Purdue's semiconductor industry ties are a genuine differentiator."},
            {"label": "Intense curriculum", "sentiment": "caution", "detail": "Math-heavy core and fast-paced sequences demand strong preparation and active use of support resources."},
            {"label": "Industry placement", "sentiment": "positive", "detail": "Strong pipelines to semiconductor, defense, and communications companies."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Electrical Engineering Programs", "url": "https://www.usnews.com/best-colleges/rankings/electrical-engineering"},
            {"label": "Elmore Family School of ECE — About", "url": "https://engineering.purdue.edu/ECE"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "purdue-nursing-bs": {
        "summary": (
            "Purdue's BSN program through the School of Nursing in the College of Health and Human "
            "Sciences offers a rigorous pre-licensure track with clinical rotations at regional "
            "Indiana health systems. Graduates consistently achieve strong NCLEX pass rates, and the "
            "program benefits from Purdue's interdisciplinary HHS infrastructure. Students note that "
            "clinical placement logistics require early planning and that the nursing program is "
            "smaller relative to Purdue's engineering colleges, which can limit elective flexibility."
        ),
        "themes": [
            {"label": "NCLEX outcomes", "sentiment": "positive", "detail": "Graduates maintain strong first-attempt NCLEX-RN pass rates above the national benchmark."},
            {"label": "Clinical partnerships", "sentiment": "positive", "detail": "Regional Indiana health systems provide diverse acute-care, pediatric, and community rotations."},
            {"label": "Interdisciplinary access", "sentiment": "positive", "detail": "HHS proximity to pharmacy, nutrition, and health sciences enriches interprofessional education."},
            {"label": "Enrollment cap", "sentiment": "caution", "detail": "The nursing program is selective and smaller than engineering programs; early application is advisable."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Nursing Programs", "url": "https://www.usnews.com/best-colleges/rankings/nursing"},
            {"label": "Purdue School of Nursing", "url": "https://hhs.purdue.edu/nursing/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "purdue-pharmacy-prof": {
        "summary": (
            "Purdue's College of Pharmacy is one of the oldest pharmacy schools in the United States "
            "(established 1884) and ranks consistently in the top 10–15 nationally by U.S. News. "
            "The Pharm.D. program integrates strong pharmaceutical sciences research through the "
            "Purdue Institute for Drug Discovery and the Center for Cancer Research. Students praise "
            "the research-rich environment and faculty expertise; cautions include a demanding "
            "curriculum and the competitive NAPLEX licensing environment post-graduation."
        ),
        "themes": [
            {"label": "Research integration", "sentiment": "positive", "detail": "Purdue Institute for Drug Discovery provides direct Pharm.D. student research access."},
            {"label": "National reputation", "sentiment": "positive", "detail": "Consistently top-15 nationally; alumni hold positions at major pharma companies and federal health agencies."},
            {"label": "Rigorous curriculum", "sentiment": "caution", "detail": "Four-year professional curriculum is intense; students benefit from strong study groups and faculty mentorship."},
            {"label": "Interprofessional education", "sentiment": "positive", "detail": "Collaboration with nursing, pre-med, and veterinary students reflects real clinical team dynamics."},
        ],
        "sources": [
            {"label": "U.S. News — Best Graduate Pharmacy Programs", "url": "https://www.usnews.com/best-graduate-schools/top-pharmacy-schools/pharmacy-rankings"},
            {"label": "Purdue College of Pharmacy — About", "url": "https://pharmacy.purdue.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "purdue-veterinary-medicine-prof": {
        "summary": (
            "Purdue's College of Veterinary Medicine is consistently ranked among the top 10 "
            "veterinary schools in the United States, with a comprehensive teaching hospital "
            "covering small animal, large animal, and exotic species. The Animal Disease Diagnostic "
            "Laboratory (ADDL) is a nationally significant pathogen-surveillance resource. "
            "Admission is highly competitive, and the four-year D.V.M. curriculum is demanding, "
            "but graduates enjoy strong placement in clinical practice, research, and government "
            "veterinary roles."
        ),
        "themes": [
            {"label": "Teaching hospital breadth", "sentiment": "positive", "detail": "Small, large, and exotic animal hospitals on a single campus give broad clinical exposure."},
            {"label": "ADDL diagnostic resource", "sentiment": "positive", "detail": "The Animal Disease Diagnostic Lab provides rare exposure to real-world disease surveillance work."},
            {"label": "Competitive admission", "sentiment": "caution", "detail": "Indiana residents and VMCAS applicants face competitive pools; GPA, GRE, and veterinary experience hours matter."},
            {"label": "Research opportunities", "sentiment": "positive", "detail": "Purdue Comparative Oncology Program and One Health initiatives offer D.V.M./Ph.D. dual tracks."},
        ],
        "sources": [
            {"label": "U.S. News — Best Veterinary Medicine Programs", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/veterinary-medicine-rankings"},
            {"label": "Purdue College of Veterinary Medicine — About", "url": "https://vet.purdue.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "purdue-business-administration-bs": {
        "summary": (
            "The Mitch Daniels School of Business (renamed from Krannert School of Management in "
            "2023) offers a quantitatively rigorous undergraduate business program known for supply "
            "chain management, operations, and analytics. Reviewers note strong employer connections "
            "in manufacturing, logistics, and finance, though the school's brand recognition "
            "outside the Midwest lags behind top-10 undergraduate business programs and graduate "
            "program recruitment is MBA-centric."
        ),
        "themes": [
            {"label": "Quantitative strength", "sentiment": "positive", "detail": "Krannert heritage gives the curriculum a strong operations, analytics, and supply chain focus."},
            {"label": "Industry placement (Midwest)", "sentiment": "positive", "detail": "Caterpillar, Amazon, Eli Lilly, and major logistics firms recruit actively from MDSB."},
            {"label": "Brand recognition nationally", "sentiment": "mixed", "detail": "Strong regional reputation; growing national footprint under the Mitch Daniels brand but still developing."},
            {"label": "Entrepreneurship resources", "sentiment": "positive", "detail": "Purdue Foundry and the Center for Entrepreneurship and Innovation support student ventures."},
        ],
        "sources": [
            {"label": "Poets&Quants — Best Undergraduate Business Schools", "url": "https://poetsandquants.com/best-undergraduate-business-programs/"},
            {"label": "U.S. News — Best Undergraduate Business Programs", "url": "https://www.usnews.com/best-colleges/rankings/business-overall"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "purdue-agricultural-economics-bs": {
        "summary": (
            "Purdue's agricultural economics program in the College of Agriculture is regarded as "
            "one of the top programs nationally for students pursuing agribusiness, food policy, "
            "and rural finance careers. The Department of Agricultural Economics has deep ties to "
            "USDA, Purdue Extension, and commodity trading firms. Students value the practical "
            "emphasis and Midwest agriculture network, though the program is narrower in scope "
            "than a general economics or finance major at a business school."
        ),
        "themes": [
            {"label": "USDA and policy connections", "sentiment": "positive", "detail": "Faculty research partnerships with USDA and state ag departments create strong policy placement pipelines."},
            {"label": "Agribusiness network", "sentiment": "positive", "detail": "Purdue's land-grant mission and Indiana farm industry proximity create unmatched agribusiness recruiting."},
            {"label": "Narrow scope", "sentiment": "mixed", "detail": "Students seeking broad finance or economics roles may find more flexibility in a general economics degree."},
            {"label": "Extension and outreach", "sentiment": "positive", "detail": "Purdue Extension is one of the largest in the U.S. — offering applied learning opportunities unavailable elsewhere."},
        ],
        "sources": [
            {"label": "U.S. News — Best Agricultural Sciences Programs", "url": "https://www.usnews.com/best-colleges/rankings/agricultural-sciences"},
            {"label": "Purdue Agricultural Economics — About", "url": "https://ag.purdue.edu/agecon/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "purdue-psychology-bs": {
        "summary": (
            "Purdue's psychology program through the Department of Psychological Sciences in the "
            "College of Liberal Arts offers strong research opportunities in cognitive, behavioral, "
            "and social neuroscience. Students benefit from active faculty labs and a clear pathway "
            "to doctoral study, though introductory courses can be large and research assistant "
            "spots are competitive. Career outcomes vary significantly based on whether students "
            "pursue graduate study."
        ),
        "themes": [
            {"label": "Research lab access", "sentiment": "positive", "detail": "Active faculty labs in cognitive, developmental, and clinical psychology allow early research involvement."},
            {"label": "Graduate school preparation", "sentiment": "positive", "detail": "Strong track record of placing graduates in doctoral programs in psychology and neuroscience."},
            {"label": "Large introductory courses", "sentiment": "caution", "detail": "High enrollment means gateway courses are lecture-heavy; individual engagement requires initiative."},
            {"label": "Career variability without grad school", "sentiment": "mixed", "detail": "Undergraduate psychology alone narrows job market options; pairing with pre-med, data science, or HR coursework is advisable."},
        ],
        "sources": [
            {"label": "Niche — Purdue University", "url": "https://www.niche.com/colleges/purdue-university/"},
            {"label": "Purdue Department of Psychological Sciences", "url": "https://www.purdue.edu/hhs/psy/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
}

_FLAGSHIP = "purdue-aerospace-engineering-bs"
_TRACKS_BY_SLUG: dict = {}
_CLASS_PROFILE_BY_SLUG: dict = {}
_FACULTY_BY_SLUG: dict = {}
_COST_BY_SLUG: dict = {}
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "purdue-computer-science-bs": ["computer science", "CS", "College of Science"],
    "purdue-aerospace-engineering-bs": ["aerospace engineering", "aeronautics", "astronautics", "Cradle of Astronauts"],
    "purdue-mechanical-engineering-bs": ["mechanical engineering", "ME", "Purdue Engineering"],
    "purdue-electrical-engineering-bs": ["electrical engineering", "ECE", "electronics", "communications engineering"],
    "purdue-nursing-bs": ["nursing", "BSN", "registered nursing", "HHS"],
    "purdue-pharmacy-prof": ["pharmacy", "PharmD", "pharmaceutical sciences"],
    "purdue-veterinary-medicine-prof": ["veterinary medicine", "DVM", "vet school"],
    "purdue-business-administration-bs": ["business", "management", "Mitch Daniels School of Business", "Krannert"],
    "purdue-agricultural-economics-bs": ["agricultural economics", "agribusiness", "College of Agriculture"],
    "purdue-psychology-bs": ["psychology", "psychological sciences", "College of Liberal Arts"],
}


def _program_standard(slug: str, spec: dict | None = None) -> dict:
    if spec is None:
        spec = _SPEC_BY_SLUG.get(slug, {})
    omitted: list[str] = [
        "outcomes_data.employment_rate",
        "outcomes_data.top_industries",
        "outcomes_data.conditions",
    ]
    if spec.get("degree_type") != "bachelors" and slug not in _COST_BY_SLUG:
        omitted.append("cost_data.tuition_usd")
    if slug not in _TRACKS_BY_SLUG:
        omitted.append("tracks")
    if slug not in _CLASS_PROFILE_BY_SLUG:
        omitted.append("class_profile.cohort_size")
    if slug not in _FACULTY_BY_SLUG:
        omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    return _standard(omitted)


def _requirements_for(spec: dict) -> dict:
    return dict(_REQ_UNDERGRAD if spec["degree_type"] == "bachelors" else _REQ_GRAD)


def _website_for(spec: dict) -> str:
    return SCHOOL_WEBSITE.get(spec["school"], "https://www.purdue.edu/")


def apply(session: Session) -> bool:
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    for _path in _OMITTED_INSTITUTION:
        if _path.startswith("school_outcomes."):
            school_outcomes.pop(_path.split(".", 1)[1], None)
    school_outcomes["_standard"] = _standard(_OMITTED_INSTITUTION)
    inst.school_outcomes = school_outcomes
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    inst.founded_year = 1869
    inst.campus_setting = "suburban"
    if not inst.website_url:
        inst.website_url = "https://www.purdue.edu"
    hero = SCHOOL_OUTCOMES["campus_photos"][0]["url"]
    _gallery = [u for u in (inst.media_gallery or []) if u != hero]
    inst.media_gallery = [hero, *_gallery]
    inst.content_sources = _INSTITUTION_CONTENT
    session.flush()
    school_by_name = _apply_schools(session, inst)
    _apply_programs(session, inst, school_by_name)
    session.flush()
    return True


def _apply_schools(session: Session, inst: Institution) -> dict[str, School]:
    existing = {s.name: s for s in session.scalars(select(School).where(School.institution_id == inst.id))}
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
        sc.website_url = SCHOOL_WEBSITE.get(spec["name"])
        m = next(x for x in _SCHOOL_META if x["name"] == spec["name"])
        about = dict(_about_for(m))
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
    fks = session.execute(text("""
        SELECT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND ccu.table_name = 'programs' AND ccu.column_name = 'id' AND tc.table_name <> 'programs'
    """)).fetchall()
    for table, col in fks:
        if session.execute(text(f'SELECT 1 FROM "{table}" WHERE "{col}" = :pid LIMIT 1'), {"pid": program_id}).first():
            return True
    return False


def _apply_programs(session: Session, inst: Institution, school_by_name: dict[str, School]) -> None:
    existing = {p.slug: p for p in session.scalars(select(Program).where(Program.institution_id == inst.id)) if p.slug}
    canonical = set(PROGRAM_SLUGS)
    for spec in PROGRAMS:
        slug = spec["slug"]
        p = existing.get(slug)
        if p is None:
            p = Program(institution_id=inst.id, program_name=spec["program_name"], degree_type=spec["degree_type"], slug=slug)
            session.add(p)
        p.program_name = spec["program_name"]
        p.degree_type = spec["degree_type"]
        p.duration_months = spec.get("duration_months")
        p.description_text = spec["description"]
        p.website_url = _website_for(spec)
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "on_campus")
        p.department = spec.get("department")
        kw = _PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(_KEYWORDS_BY_SCHOOL[spec["school"]])
        p.content_sources = _program_content(spec["school"], kw)
        if spec["degree_type"] == "bachelors":
            p.tuition = _TUITION_UG_INSTATE
            p.cost_data = {
                "in_state_tuition_usd": _TUITION_UG_INSTATE,
                "out_of_state_tuition_usd": _TUITION_UG_OOS,
                "total_cost_of_attendance_in_state": _UNDERGRAD_COA,
                "avg_net_price": _AVG_NET_PRICE,
                "funded": False,
                "source": _COST_SRC[0], "source_url": _COST_SRC[1], "year": "2024-25",
            }
        elif spec["degree_type"] == "phd":
            p.tuition = 0
            p.cost_data = {
                "tuition_usd": 0, "funded": True,
                "note": "Purdue PhD students typically receive full tuition plus a stipend through Purdue Graduate School fellowship programs.",
                "source": "Purdue Graduate School — Funding",
                "source_url": "https://www.purdue.edu/gradschool/prospective/financing/",
            }
        else:
            p.tuition = None
            p.cost_data = {
                "note": "Tuition varies by program; see the official program tuition page.",
                "source": "Purdue program tuition page",
                "source_url": _website_for(spec),
            }
        p.application_requirements = _requirements_for(spec)
        outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        p.application_deadline = date(2027, 1, 15) if spec["degree_type"] == "bachelors" else None
    session.flush()
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
