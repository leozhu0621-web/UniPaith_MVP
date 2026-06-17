"""University of Washington (Seattle) — gold-standard profile data
(institution + schools + program catalog).

Mirrors the MIT / Sloan / MBAn reference instance (see ``mit_profile.py`` /
``uiuc_profile.py``): every value is researched from an authoritative source and
carries a citation, or is honestly omitted (recorded in that node's
``_standard.omitted``) — never guessed. Built 2026-06-13 from:

  * U.S. Dept. of Education **College Scorecard** API + **IPEDS** (UNITID 236948):
    admit rate, average net price, cost of attendance, ten-year median earnings,
    six-year completion, first-year retention, Pell/loan rates, median debt,
    endowment, undergraduate race/ethnicity. UW is test-blind, so SAT/ACT test
    scores are omitted with reason.
  * **UW Office of Planning & Budgeting (OPB) Fast Facts** and the UW Common Data
    Set 2024-2025: the Fall 2024 first-year admissions funnel (69,166 applicants /
    27,076 admitted / 7,196 enrolled), Seattle-campus enrollment (52,316 total;
    36,023 undergraduates), and the 20:1 student-faculty ratio.
  * Rankings: **U.S. News Best Colleges 2026** (#42 National, #16 public), **QS
    2026** (#81), **Times Higher Education 2026** (#25), Carnegie R1, and Northwest
    Commission on Colleges and Universities (NWCCU) accreditation, each cited.
  * The official **UW General Catalog** (washington.edu/students/gencat): the full
    published degree catalog parsed from the college/school program indexes across
    UW Seattle's 16 degree-granting colleges/schools and the interdisciplinary
    Graduate School, plus the professional Doctor of Medicine, Doctor of Dental
    Surgery, Juris Doctor, Doctor of Pharmacy, Doctor of Nursing Practice, Doctor
    of Physical Therapy, and Doctor of Audiology, and UW's online degrees delivered
    through UW Professional & Continuing Education (carrying
    ``delivery_format = "online"``). Minors, certificates, options/concentrations,
    and combined-degree listings are excluded.
  * UW leadership pages (washington.edu/leadership) for each college/school dean,
    and a verified 5-photo Wikimedia Commons campus gallery (author + license
    confirmed via the Commons API).
  * Verified third-party coverage + official rankings for flagship coverable
    programs (computer science, the MD/WWAMI, the DNP, the iSchool MLIS, the Foster
    MBA, the JD, the PharmD, the MSW, bioengineering, aeronautics & astronautics,
    civil engineering, statistics, economics, and oceanography).

Honest caveats stamped into ``_standard.omitted``: UW is test-blind (it does not
consider SAT/ACT in admission), so institution ``test_scores`` is omitted. UW
reports tri-campus academic staff rather than a single Seattle instructional-
faculty headcount, so ``scale.faculty_count`` is omitted (the 20:1 student-faculty
ratio is kept). UW does not publish a single university-wide placement rate or a
uniform top-employer-industries list across all colleges, so those two institution
outcome fields are omitted (the Scorecard ten-year median earnings is kept). Most
graduate/professional programs bill tuition per quarter and publish no single
annual figure, so those carry a sourced "see the program's tuition page" record
rather than a guessed number. This is a large catalog (365 programs), so external
reviews are attached to the flagship coverable programs and the remaining programs
record those deep fields in their ``_standard.omitted`` pending a future depth
pass.
"""

# ruff: noqa: E501

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "University of Washington-Seattle Campus"
ENRICHED_AT = "2026-06-13"


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


# UW is test-blind; reports tri-campus staff (no single Seattle faculty headcount);
# and reports outcomes by college, not as one university-wide placement rate or
# top-employer-industries list.
_OMITTED_INSTITUTION: list[str] = [
    "school_outcomes.test_scores",
    "school_outcomes.scale.faculty_count",
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
]

RANKING_DATA: dict = {
    "ownership_type": "public",
    "accreditor": "Northwest Commission on Colleges and Universities (NWCCU)",
    "carnegie_classification": (
        "Doctoral Universities: Very High Research Spending and Doctorate Production (R1)"
    ),
    "qs_world_university_rankings": {
        "rank": 81,
        "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/university-washington",
    },
    "times_higher_education": {
        "rank": 25,
        "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-washington",
    },
    "us_news_national": {
        "rank": 42,
        "year": 2026,
        "source_url": "https://www.usnews.com/best-colleges/university-of-washington-3798",
    },
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.3915,
    "avg_net_price": 14091,
    "median_earnings_10yr": 78466,
    "graduation_rate_6yr": 0.8518,
    "completion_rate_4yr_150pct": 0.8518,
    "retention_rate_first_year": 0.9482,
    "financial_aid": {
        "pell_grant_rate": 0.1486,
        "federal_loan_rate": 0.1489,
        "median_debt_completers": 14615,
        "cost_of_attendance": 32446,
        "avg_net_price": 14091,
    },
    "demographics": {
        "white": 0.3319,
        "asian": 0.2742,
        "hispanic": 0.1032,
        "black": 0.0433,
        "two_or_more": 0.0821,
        "american_indian": 0.0033,
        "pacific_islander": 0.0034,
        "international": 0.1173,
        "unknown": 0.0414,
        "women": 0.5664,
    },
    "campus_basics": {"location": "Seattle, Washington"},
    "scale": {
        "student_faculty_ratio": "20:1",
        "endowment_usd": 5343000000,
    },
    "location": {"lat": 47.6553, "lng": -122.3035},
    "research": {
        "labs": [
            "Applied Physics Laboratory (APL-UW)",
            "Institute for Health Metrics and Evaluation (IHME)",
            "Institute for Protein Design (IPD)",
            "eScience Institute",
            "Washington National Primate Research Center",
            "Friday Harbor Laboratories",
        ],
        "areas": [
            "Global health, health metrics, and biomedical research",
            "Computer science, artificial intelligence, and data science",
            "Protein design, genome sciences, and bioengineering",
            "Oceanography, atmospheric, and earth sciences",
            "Aerospace, clean energy, and advanced materials",
        ],
        "lab_links": {
            "Applied Physics Laboratory (APL-UW)": "https://www.apl.washington.edu/",
            "Institute for Health Metrics and Evaluation (IHME)": "https://www.healthdata.org/",
            "Institute for Protein Design (IPD)": "https://www.ipd.uw.edu/",
            "eScience Institute": "https://escience.washington.edu/",
            "Washington National Primate Research Center": "https://wanprc.uw.edu/",
            "Friday Harbor Laboratories": "https://fhl.uw.edu/",
        },
    },
    "campus_life": {
        "athletics_division": "NCAA Division I (Big Ten Conference)",
        "resources": [
            {"name": "Washington Huskies Athletics", "url": "https://gohuskies.com/"},
            {
                "name": "University of Washington Libraries",
                "url": "https://www.lib.washington.edu/",
            },
            {"name": "Henry Art Gallery", "url": "https://henryart.org/"},
            {
                "name": "Burke Museum of Natural History and Culture",
                "url": "https://www.burkemuseum.org/",
            },
            {"name": "UW Recreation", "url": "https://www.washington.edu/ima/"},
            {"name": "Meany Center for the Performing Arts", "url": "https://meanycenter.org/"},
        ],
    },
    "media_credit": "Wikimedia Commons / Martin Kraft (CC BY-SA 3.0)",
    "campus_photos": [
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/MK03214_University_of_Washington_Suzzallo_Library.jpg/1920px-MK03214_University_of_Washington_Suzzallo_Library.jpg",
            "credit": "Wikimedia Commons / Martin Kraft (CC BY-SA 3.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/MK03244_University_of_Washington_Drumheller_Fountain.jpg/1920px-MK03244_University_of_Washington_Drumheller_Fountain.jpg",
            "credit": "Wikimedia Commons / Martin Kraft (CC BY-SA 3.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/be/UW_Red_Square.jpg/1920px-UW_Red_Square.jpg",
            "credit": "Wikimedia Commons / Yihang Sun (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/University_of_Washington_Quad_cherry_blossoms_2017_-_03.jpg/1920px-University_of_Washington_Quad_cherry_blossoms_2017_-_03.jpg",
            "credit": "Wikimedia Commons / Joe Mabel (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Rainier_Vista_late_on_a_sunny_November_afternoon.jpg/1920px-Rainier_Vista_late_on_a_sunny_November_afternoon.jpg",
            "credit": "Wikimedia Commons / Joe Mabel (CC BY-SA 4.0)",
        },
    ],
    "flagship": {
        "enrollment_total": 52316,
        "applicants": 69166,
        "admits": 27076,
        "admissions_cycle": "First-year, Fall 2024 (UW Common Data Set 2024-2025)",
        "founded_year": 1861,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (UW, UNITID 236948)",
            "url": "https://collegescorecard.ed.gov/school/?236948-University-of-Washington-Seattle-Campus",
        },
        {
            "label": "NCES College Navigator — University of Washington-Seattle Campus (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=236948",
        },
        {
            "label": "UW Office of Planning & Budgeting — Fast Facts (enrollment, ratio)",
            "url": "https://www.washington.edu/opb/uw-data/fast-facts/",
        },
        {
            "label": "UW Common Data Set 2024-2025 (admissions funnel, enrollment)",
            "url": "https://www.washington.edu/opb/uw-data/common-data-set/",
        },
        {
            "label": "Carnegie Classifications — University of Washington (R1)",
            "url": "https://carnegieclassifications.acenet.edu/institution/university-of-washington-seattle-campus/",
        },
        {
            "label": "NWCCU — University of Washington (accreditation)",
            "url": "https://nwccu.org/member-institutions/university-of-washington/",
        },
        {
            "label": "QS World University Rankings 2026 — University of Washington (#81)",
            "url": "https://www.topuniversities.com/universities/university-washington",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — University of Washington (#25)",
            "url": "https://www.timeshighereducation.com/world-university-rankings/university-washington",
        },
        {
            "label": "U.S. News Best Colleges 2026 — University of Washington (#42 National, #16 public)",
            "url": "https://www.usnews.com/best-colleges/university-of-washington-3798",
        },
        {
            "label": "UW General Catalog — degree programs",
            "url": "https://www.washington.edu/students/gencat/degree_programs.html",
        },
        {
            "label": "UW leadership (deans of colleges and schools)",
            "url": "https://www.washington.edu/leadership/",
        },
    ],
}

# student_body_size = Seattle-campus undergraduate enrollment (UW OPB Fall 2024);
# total degree-seeking enrollment (52,316) lives in flagship.enrollment_total.
UNDERGRAD_COUNT = 36023

DESCRIPTION = (
    "The University of Washington is a public research university in Seattle, WA. Founded in 1861, "
    "it is the flagship of the University of Washington system, a founding member of the Association "
    "of American Universities, and one of the world's leading public research universities by funded "
    "research volume. Its Seattle campus enrolled 52,316 students in Fall 2024 — about 36,023 "
    "undergraduates and roughly 16,000 graduate and professional students — with a 20:1 student-"
    "faculty ratio. For Fall 2024 it admitted about 39.2% of first-year applicants (27,076 of "
    "69,166). UW practices test-blind admission and does not consider SAT/ACT scores.\n\n"
    "UW is organized into 16 degree-granting colleges and schools, including the College of Arts and "
    "Sciences, the College of Engineering (home to the Paul G. Allen School of Computer Science & "
    "Engineering), the Michael G. Foster School of Business, the School of Medicine, the School of "
    "Nursing, the School of Public Health, the Information School, the College of the Environment, "
    "and the Daniel J. Evans School of Public Policy and Governance, plus an interdisciplinary "
    "Graduate School. Together they offer hundreds of degree programs across the bachelor's, "
    "master's, professional, and doctoral levels — including the Doctor of Medicine, Doctor of "
    "Dental Surgery, Juris Doctor, Doctor of Pharmacy, Doctor of Nursing Practice, Doctor of "
    "Physical Therapy, and Doctor of Audiology, and online degrees delivered through UW Professional "
    "& Continuing Education.\n\n"
    "A Carnegie R1 university accredited by the Northwest Commission on Colleges and Universities, "
    "UW ranks #42 among national universities (and #16 among public universities) by U.S. News, #25 "
    "in the world by Times Higher Education, and #81 by QS for 2026. The UW School of Medicine is "
    "ranked #1 in the nation for primary care, family medicine, and rural medicine, anchored by the "
    "five-state WWAMI program; the iSchool's library and information studies and the School of "
    "Nursing's DNP rank among the nation's best; and computer science ranks among the top programs "
    "nationally. Research is anchored by the Applied Physics Laboratory, the Institute for Health "
    "Metrics and Evaluation, the Institute for Protein Design, and the eScience Institute.\n\n"
    "UW's published cost of attendance is about $32,446 a year, but its average net price after grant "
    "aid is about $14,091 and the median federal debt of completers is about $14,615; in-state "
    "students benefit from public tuition. UW graduates earn a median of roughly $78,466 ten years "
    "after entry. The Washington Huskies compete in NCAA Division I in the Big Ten Conference."
)

# == Schools (16 degree-granting colleges/schools + interdisciplinary Graduate School) ==
_SCHOOL_META = [
    {
        "key": "ARTSCI",
        "name": "College of Arts and Sciences",
        "sort_order": 1,
        "website": "https://artsci.uw.edu/",
        "leadership": "Dianne Harris — Dean",
        "research_centers": [
            "Division of the Arts",
            "Division of the Humanities",
            "Division of the Natural Sciences",
            "Division of the Social Sciences",
            "Paul G. Allen School of Computer Science & Engineering (CS undergraduate major)",
        ],
        "keywords": ["College of Arts and Sciences", "Arts and Sciences", "liberal arts"],
    },
    {
        "key": "BUILT",
        "name": "College of Built Environments",
        "sort_order": 2,
        "website": "https://be.uw.edu/",
        "leadership": "Ken P. Yocom — Dean",
        "research_centers": [
            "Department of Architecture",
            "Department of Construction Management",
            "Department of Landscape Architecture",
            "Department of Real Estate",
            "Department of Urban Design & Planning",
        ],
        "keywords": [
            "College of Built Environments",
            "built environments",
            "architecture",
            "urban planning",
        ],
    },
    {
        "key": "BUS",
        "name": "Michael G. Foster School of Business",
        "sort_order": 3,
        "website": "https://foster.uw.edu/",
        "leadership": "Frank Hodge — Dean",
        "research_centers": [
            "Department of Accounting",
            "Department of Finance & Business Economics",
            "Department of Marketing & International Business",
            "Department of Information Systems & Operations Management",
            "Department of Management & Organization",
        ],
        "keywords": ["Foster School of Business", "Foster", "business", "MBA"],
    },
    {
        "key": "DENT",
        "name": "School of Dentistry",
        "sort_order": 4,
        "website": "https://dental.washington.edu/",
        "leadership": "André V. Ritter — Dean",
        "research_centers": [
            "Doctor of Dental Surgery (DDS) program",
            "Department of Oral Health Sciences",
            "Graduate specialty programs (orthodontics, periodontics, prosthodontics, endodontics)",
        ],
        "keywords": ["School of Dentistry", "dentistry", "DDS", "dental"],
    },
    {
        "key": "EDUC",
        "name": "College of Education",
        "sort_order": 5,
        "website": "https://education.uw.edu/",
        "leadership": "Mia Tuan — Dean",
        "research_centers": [
            "Area of Curriculum & Instruction",
            "Area of Educational Leadership & Policy Studies",
            "Area of Learning Sciences & Human Development",
            "Area of Measurement & Statistics",
            "Area of School Psychology",
            "Area of Special Education",
        ],
        "keywords": ["College of Education", "education", "teaching"],
    },
    {
        "key": "ENGR",
        "name": "College of Engineering",
        "sort_order": 6,
        "website": "https://www.engr.uw.edu/",
        "leadership": "Nancy Allbritton — Dean",
        "research_centers": [
            "Paul G. Allen School of Computer Science & Engineering",
            "Department of Electrical & Computer Engineering",
            "Department of Mechanical Engineering",
            "William E. Boeing Department of Aeronautics & Astronautics",
            "Department of Civil & Environmental Engineering",
            "Department of Bioengineering",
            "Department of Materials Science & Engineering",
        ],
        "keywords": ["College of Engineering", "engineering", "computer science", "Allen School"],
    },
    {
        "key": "ENV",
        "name": "College of the Environment",
        "sort_order": 7,
        "website": "https://environment.uw.edu/",
        "leadership": "Joel Thornton — Interim Dean",
        "research_centers": [
            "School of Oceanography",
            "School of Aquatic & Fishery Sciences",
            "School of Environmental & Forest Sciences",
            "Department of Atmospheric & Climate Science",
            "Department of Earth & Space Sciences",
        ],
        "keywords": ["College of the Environment", "environment", "oceanography", "earth sciences"],
    },
    {
        "key": "ISCHOOL",
        "name": "The Information School",
        "sort_order": 8,
        "website": "https://ischool.uw.edu/",
        "leadership": "Anind Dey — Dean",
        "research_centers": [
            "Master of Library & Information Science (MLIS)",
            "Master of Science in Information Management (MSIM)",
            "Informatics undergraduate program",
            "Ph.D. in Information Science",
        ],
        "keywords": [
            "The Information School",
            "iSchool",
            "information science",
            "library and information science",
        ],
    },
    {
        "key": "GRAD",
        "name": "The Graduate School",
        "sort_order": 9,
        "website": "https://grad.uw.edu/",
        "leadership": "Joy Williamson-Lott — Dean",
        "research_centers": [
            "Interdisciplinary graduate degree programs",
            "Molecular Engineering & Sciences",
            "Neuroscience",
            "Molecular & Cellular Biology",
            "Data Science",
            "Individual PhD Program",
        ],
        "keywords": ["Graduate School", "interdisciplinary", "graduate program"],
    },
    {
        "key": "LAW",
        "name": "School of Law",
        "sort_order": 10,
        "website": "https://www.law.uw.edu/",
        "leadership": "Tamara F. Lawson — Dean",
        "research_centers": [
            "Juris Doctor (J.D.) program",
            "Master of Laws (LL.M.) program",
            "Master of Jurisprudence program",
            "Ph.D. in Law program",
        ],
        "keywords": ["School of Law", "law", "J.D.", "Juris Doctor"],
    },
    {
        "key": "MED",
        "name": "School of Medicine",
        "sort_order": 11,
        "website": "https://www.uwmedicine.org/school-of-medicine",
        "leadership": "Timothy H. Dellit — Dean",
        "research_centers": [
            "Doctor of Medicine (M.D.) program (WWAMI)",
            "Department of Biochemistry",
            "Department of Genome Sciences",
            "Department of Immunology",
            "Department of Rehabilitation Medicine",
            "Department of Laboratory Medicine & Pathology",
        ],
        "keywords": ["School of Medicine", "UW Medicine", "medicine", "WWAMI", "M.D."],
    },
    {
        "key": "NURS",
        "name": "School of Nursing",
        "sort_order": 12,
        "website": "https://nursing.uw.edu/",
        "leadership": "Hilaire Thompson — Executive Dean",
        "research_centers": [
            "Doctor of Nursing Practice (DNP) program",
            "Master of Nursing program",
            "Ph.D. in Nursing Science program",
        ],
        "keywords": ["School of Nursing", "nursing", "DNP"],
    },
    {
        "key": "PHARM",
        "name": "School of Pharmacy",
        "sort_order": 13,
        "website": "https://sop.washington.edu/",
        "leadership": "Jay Panyam — Dean",
        "research_centers": [
            "Doctor of Pharmacy (PharmD) program",
            "Department of Pharmaceutics",
            "Department of Medicinal Chemistry",
            "Department of Pharmacy (pharmaceutical outcomes research & policy)",
        ],
        "keywords": ["School of Pharmacy", "pharmacy", "PharmD", "pharmaceutics"],
    },
    {
        "key": "EVANS",
        "name": "Daniel J. Evans School of Public Policy and Governance",
        "sort_order": 14,
        "website": "https://evans.uw.edu/",
        "leadership": "Jodi Sandfort — Dean",
        "research_centers": [
            "Master of Public Administration (MPA) program",
            "Executive Master of Public Administration program",
            "Ph.D. in Public Policy & Management program",
        ],
        "keywords": ["Evans School", "public policy", "public administration", "MPA"],
    },
    {
        "key": "PUBH",
        "name": "School of Public Health",
        "sort_order": 15,
        "website": "https://sph.washington.edu/",
        "leadership": "Hilary Godwin — Dean",
        "research_centers": [
            "Department of Biostatistics",
            "Department of Epidemiology",
            "Department of Environmental & Occupational Health Sciences",
            "Department of Health Systems & Population Health",
            "Department of Global Health",
        ],
        "keywords": [
            "School of Public Health",
            "public health",
            "epidemiology",
            "biostatistics",
            "global health",
        ],
    },
    {
        "key": "SOCW",
        "name": "School of Social Work",
        "sort_order": 16,
        "website": "https://socialwork.uw.edu/",
        "leadership": "Michael S. Spencer — Dean",
        "research_centers": [
            "Bachelor of Arts in Social Welfare program",
            "Master of Social Work (MSW) program",
            "Ph.D. in Social Welfare program",
        ],
        "keywords": ["School of Social Work", "social work", "MSW"],
    },
]
SCHOOL_NAME = {m["key"]: m["name"] for m in _SCHOOL_META}
SCHOOL_WEBSITE = {m["name"]: m["website"] for m in _SCHOOL_META}


def _school_description(m: dict) -> str:
    return (
        f"The {m['name']} is one of the 16 degree-granting colleges and schools of the University "
        "of Washington in Seattle."
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
            "label": "UW leadership + college/school websites",
            "url": "https://www.washington.edu/leadership/",
        },
    }


def _about_omitted(m: dict) -> list[str]:
    # UW does not publish a single founding year per college on one authoritative
    # page, and notable-faculty lists are curated per department; omit-with-reason.
    return ["about_detail.founded", "about_detail.faculty", "about_detail.named_for"]


# == Feeds (content_sources) ==
_NEWS_URL = "https://www.washington.edu/news/"
_SOCIAL = {
    "instagram": "https://www.instagram.com/uofwa/",
    "linkedin": "https://www.linkedin.com/school/university-of-washington/",
    "x": "https://twitter.com/UW",
    "youtube": "https://www.youtube.com/user/uwhuskies",
    "facebook": "https://www.facebook.com/UofWA/",
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
    (
        "uw-american-ethnic-studies-bs",
        "ARTSCI",
        "American Ethnic Studies",
        "bachelors",
        "American Ethnic Studies",
        "on_campus",
        48,
    ),
    (
        "uw-american-indian-studies-bs",
        "ARTSCI",
        "American Indian Studies",
        "bachelors",
        "American Indian Studies",
        "on_campus",
        48,
    ),
    (
        "uw-american-music-bs",
        "ARTSCI",
        "American Music",
        "bachelors",
        "American Music",
        "on_campus",
        48,
    ),
    ("uw-anthropology-bs", "ARTSCI", "Anthropology", "bachelors", "Anthropology", "on_campus", 48),
    (
        "uw-applied-and-computational-math-sciences-bs",
        "ARTSCI",
        "Applied and Computational Math Sciences",
        "bachelors",
        "Applied and Computational Math Sciences",
        "on_campus",
        48,
    ),
    (
        "uw-applied-mathematics-bs",
        "ARTSCI",
        "Applied Mathematics",
        "bachelors",
        "Applied Mathematics",
        "on_campus",
        48,
    ),
    ("uw-art-bs", "ARTSCI", "Art", "bachelors", "Art", "on_campus", 48),
    ("uw-art-history-bs", "ARTSCI", "Art History", "bachelors", "Art History", "on_campus", 48),
    (
        "uw-asian-languages-and-cultures-bs",
        "ARTSCI",
        "Asian Languages and Cultures",
        "bachelors",
        "Asian Languages and Cultures",
        "on_campus",
        48,
    ),
    ("uw-astronomy-bs", "ARTSCI", "Astronomy", "bachelors", "Astronomy", "on_campus", 48),
    ("uw-biochemistry-bs", "ARTSCI", "Biochemistry", "bachelors", "Biochemistry", "on_campus", 48),
    ("uw-biology-bs", "ARTSCI", "Biology", "bachelors", "Biology", "on_campus", 48),
    ("uw-chemistry-bs", "ARTSCI", "Chemistry", "bachelors", "Chemistry", "on_campus", 48),
    ("uw-chinese-bs", "ARTSCI", "Chinese", "bachelors", "Chinese", "on_campus", 48),
    (
        "uw-cinema-and-media-studies-bs",
        "ARTSCI",
        "Cinema and Media Studies",
        "bachelors",
        "Cinema and Media Studies",
        "on_campus",
        48,
    ),
    (
        "uw-classical-studies-bs",
        "ARTSCI",
        "Classical Studies",
        "bachelors",
        "Classical Studies",
        "on_campus",
        48,
    ),
    ("uw-classics-bs", "ARTSCI", "Classics", "bachelors", "Classics", "on_campus", 48),
    (
        "uw-communication-bs",
        "ARTSCI",
        "Communication",
        "bachelors",
        "Communication",
        "on_campus",
        48,
    ),
    (
        "uw-comparative-history-of-ideas-bs",
        "ARTSCI",
        "Comparative History of Ideas",
        "bachelors",
        "Comparative History of Ideas",
        "on_campus",
        48,
    ),
    (
        "uw-comparative-literature-bs",
        "ARTSCI",
        "Comparative Literature",
        "bachelors",
        "Comparative Literature",
        "on_campus",
        48,
    ),
    (
        "uw-comparative-religion-bs",
        "ARTSCI",
        "Comparative Religion",
        "bachelors",
        "Comparative Religion",
        "on_campus",
        48,
    ),
    ("uw-composition-bs", "ARTSCI", "Composition", "bachelors", "Composition", "on_campus", 48),
    (
        "uw-computational-finance-and-risk-management-bs",
        "ARTSCI",
        "Computational Finance and Risk Management",
        "bachelors",
        "Computational Finance and Risk Management",
        "on_campus",
        48,
    ),
    (
        "uw-computer-science-bs",
        "ARTSCI",
        "Computer Science",
        "bachelors",
        "Computer Science",
        "on_campus",
        48,
    ),
    ("uw-dance-bs", "ARTSCI", "Dance", "bachelors", "Dance", "on_campus", 48),
    ("uw-danish-bs", "ARTSCI", "Danish", "bachelors", "Danish", "on_campus", 48),
    ("uw-drama-bs", "ARTSCI", "Drama", "bachelors", "Drama", "on_campus", 48),
    (
        "uw-eastern-european-languages-literature-and-culture-bs",
        "ARTSCI",
        "Eastern European Languages, Literature, and Culture",
        "bachelors",
        "Eastern European Languages, Literature, and Culture",
        "on_campus",
        48,
    ),
    ("uw-economics-bs", "ARTSCI", "Economics", "bachelors", "Economics", "on_campus", 48),
    ("uw-english-bs", "ARTSCI", "English", "bachelors", "English", "on_campus", 48),
    (
        "uw-ethnomusicology-bs",
        "ARTSCI",
        "Ethnomusicology",
        "bachelors",
        "Ethnomusicology",
        "on_campus",
        48,
    ),
    ("uw-finnish-bs", "ARTSCI", "Finnish", "bachelors", "Finnish", "on_campus", 48),
    ("uw-french-bs", "ARTSCI", "French", "bachelors", "French", "on_campus", 48),
    (
        "uw-gender-women-and-sexuality-studies-bs",
        "ARTSCI",
        "Gender, Women, and Sexuality Studies",
        "bachelors",
        "Gender, Women, and Sexuality Studies",
        "on_campus",
        48,
    ),
    ("uw-geography-bs", "ARTSCI", "Geography", "bachelors", "Geography", "on_campus", 48),
    (
        "uw-german-studies-bs",
        "ARTSCI",
        "German Studies",
        "bachelors",
        "German Studies",
        "on_campus",
        48,
    ),
    (
        "uw-global-literary-studies-bs",
        "ARTSCI",
        "Global Literary Studies",
        "bachelors",
        "Global Literary Studies",
        "on_campus",
        48,
    ),
    ("uw-greek-bs", "ARTSCI", "Greek", "bachelors", "Greek", "on_campus", 48),
    ("uw-guitar-bs", "ARTSCI", "Guitar", "bachelors", "Guitar", "on_campus", 48),
    ("uw-history-bs", "ARTSCI", "History", "bachelors", "History", "on_campus", 48),
    (
        "uw-history-and-philosophy-of-science-bs",
        "ARTSCI",
        "History and Philosophy of Science",
        "bachelors",
        "History and Philosophy of Science",
        "on_campus",
        48,
    ),
    (
        "uw-individualized-studies-bs",
        "ARTSCI",
        "Individualized Studies",
        "bachelors",
        "Individualized Studies",
        "on_campus",
        48,
    ),
    (
        "uw-industrial-design-bs",
        "ARTSCI",
        "Industrial Design",
        "bachelors",
        "Industrial Design",
        "on_campus",
        48,
    ),
    (
        "uw-integrated-social-sciences-bs",
        "ARTSCI",
        "Integrated Social Sciences",
        "bachelors",
        "Integrated Social Sciences",
        "online",
        48,
    ),
    (
        "uw-interaction-design-bs",
        "ARTSCI",
        "Interaction Design",
        "bachelors",
        "Interaction Design",
        "on_campus",
        48,
    ),
    (
        "uw-international-studies-bs",
        "ARTSCI",
        "International Studies",
        "bachelors",
        "International Studies",
        "on_campus",
        48,
    ),
    ("uw-italian-bs", "ARTSCI", "Italian", "bachelors", "Italian", "on_campus", 48),
    ("uw-japanese-bs", "ARTSCI", "Japanese", "bachelors", "Japanese", "on_campus", 48),
    ("uw-jazz-studies-bs", "ARTSCI", "Jazz Studies", "bachelors", "Jazz Studies", "on_campus", 48),
    ("uw-korean-bs", "ARTSCI", "Korean", "bachelors", "Korean", "on_campus", 48),
    ("uw-latin-bs", "ARTSCI", "Latin", "bachelors", "Latin", "on_campus", 48),
    (
        "uw-law-societies-and-justice-bs",
        "ARTSCI",
        "Law, Societies, and Justice",
        "bachelors",
        "Law, Societies, and Justice",
        "on_campus",
        48,
    ),
    ("uw-linguistics-bs", "ARTSCI", "Linguistics", "bachelors", "Linguistics", "on_campus", 48),
    ("uw-mathematics-bs", "ARTSCI", "Mathematics", "bachelors", "Mathematics", "on_campus", 48),
    ("uw-microbiology-bs", "ARTSCI", "Microbiology", "bachelors", "Microbiology", "on_campus", 48),
    (
        "uw-middle-eastern-languages-and-cultures-bs",
        "ARTSCI",
        "Middle Eastern Languages and Cultures",
        "bachelors",
        "Middle Eastern Languages and Cultures",
        "on_campus",
        48,
    ),
    ("uw-music-bs", "ARTSCI", "Music", "bachelors", "Music", "on_campus", 48),
    (
        "uw-music-education-bs",
        "ARTSCI",
        "Music Education",
        "bachelors",
        "Music Education",
        "on_campus",
        48,
    ),
    ("uw-music-theory-bs", "ARTSCI", "Music Theory", "bachelors", "Music Theory", "on_campus", 48),
    ("uw-neuroscience-bs", "ARTSCI", "Neuroscience", "bachelors", "Neuroscience", "on_campus", 48),
    ("uw-norwegian-bs", "ARTSCI", "Norwegian", "bachelors", "Norwegian", "on_campus", 48),
    (
        "uw-orchestral-instruments-bs",
        "ARTSCI",
        "Orchestral Instruments",
        "bachelors",
        "Orchestral Instruments",
        "on_campus",
        48,
    ),
    ("uw-organ-bs", "ARTSCI", "Organ", "bachelors", "Organ", "on_campus", 48),
    ("uw-percussion-bs", "ARTSCI", "Percussion", "bachelors", "Percussion", "on_campus", 48),
    ("uw-philosophy-bs", "ARTSCI", "Philosophy", "bachelors", "Philosophy", "on_campus", 48),
    ("uw-physics-bs", "ARTSCI", "Physics", "bachelors", "Physics", "on_campus", 48),
    ("uw-piano-bs", "ARTSCI", "Piano", "bachelors", "Piano", "on_campus", 48),
    (
        "uw-political-science-bs",
        "ARTSCI",
        "Political Science",
        "bachelors",
        "Political Science",
        "on_campus",
        48,
    ),
    ("uw-psychology-bs", "ARTSCI", "Psychology", "bachelors", "Psychology", "on_campus", 48),
    (
        "uw-romance-linguistics-bs",
        "ARTSCI",
        "Romance Linguistics",
        "bachelors",
        "Romance Linguistics",
        "on_campus",
        48,
    ),
    (
        "uw-russian-language-literature-and-culture-bs",
        "ARTSCI",
        "Russian Language, Literature, and Culture",
        "bachelors",
        "Russian Language, Literature, and Culture",
        "on_campus",
        48,
    ),
    (
        "uw-scandinavian-area-studies-bs",
        "ARTSCI",
        "Scandinavian Area Studies",
        "bachelors",
        "Scandinavian Area Studies",
        "on_campus",
        48,
    ),
    ("uw-sociology-bs", "ARTSCI", "Sociology", "bachelors", "Sociology", "on_campus", 48),
    (
        "uw-south-asian-languages-and-cultures-bs",
        "ARTSCI",
        "South Asian Languages and Cultures",
        "bachelors",
        "South Asian Languages and Cultures",
        "on_campus",
        48,
    ),
    ("uw-spanish-bs", "ARTSCI", "Spanish", "bachelors", "Spanish", "on_campus", 48),
    (
        "uw-speech-and-hearing-sciences-bs",
        "ARTSCI",
        "Speech and Hearing Sciences",
        "bachelors",
        "Speech and Hearing Sciences",
        "on_campus",
        48,
    ),
    ("uw-statistics-bs", "ARTSCI", "Statistics", "bachelors", "Statistics", "on_campus", 48),
    (
        "uw-string-instruments-bs",
        "ARTSCI",
        "String Instruments",
        "bachelors",
        "String Instruments",
        "on_campus",
        48,
    ),
    ("uw-swedish-bs", "ARTSCI", "Swedish", "bachelors", "Swedish", "on_campus", 48),
    (
        "uw-visual-communication-design-bs",
        "ARTSCI",
        "Visual Communication Design",
        "bachelors",
        "Visual Communication Design",
        "on_campus",
        48,
    ),
    ("uw-voice-bs", "ARTSCI", "Voice", "bachelors", "Voice", "on_campus", 48),
    ("uw-anthropology-ms", "ARTSCI", "Anthropology", "masters", "Anthropology", "on_campus", 24),
    (
        "uw-applied-chemical-science-and-technology-ms",
        "ARTSCI",
        "Applied Chemical Science and Technology",
        "masters",
        "Applied Chemical Science and Technology",
        "on_campus",
        24,
    ),
    (
        "uw-applied-child-and-adolescent-psychology-prevention-and-treatment-ms",
        "ARTSCI",
        "Applied Child and Adolescent Psychology: Prevention and Treatment",
        "masters",
        "Applied Child and Adolescent Psychology: Prevention and Treatment",
        "on_campus",
        24,
    ),
    (
        "uw-applied-mathematics-ms",
        "ARTSCI",
        "Applied Mathematics",
        "masters",
        "Applied Mathematics",
        "online",
        24,
    ),
    ("uw-art-history-ms", "ARTSCI", "Art History", "masters", "Art History", "on_campus", 24),
    (
        "uw-asian-languages-and-literature-ms",
        "ARTSCI",
        "Asian Languages & Literature",
        "masters",
        "Asian Languages & Literature",
        "on_campus",
        24,
    ),
    ("uw-astronomy-ms", "ARTSCI", "Astronomy", "masters", "Astronomy", "on_campus", 24),
    ("uw-chemistry-ms", "ARTSCI", "Chemistry", "masters", "Chemistry", "on_campus", 24),
    ("uw-china-studies-ms", "ARTSCI", "China Studies", "masters", "China Studies", "on_campus", 24),
    (
        "uw-cinema-and-media-studies-ms",
        "ARTSCI",
        "Cinema and Media Studies",
        "masters",
        "Cinema and Media Studies",
        "on_campus",
        24,
    ),
    ("uw-communication-ms", "ARTSCI", "Communication", "masters", "Communication", "on_campus", 24),
    (
        "uw-computational-finance-and-risk-management-ms",
        "ARTSCI",
        "Computational Finance & Risk Management",
        "masters",
        "Computational Finance & Risk Management",
        "online",
        24,
    ),
    (
        "uw-computational-linguistics-ms",
        "ARTSCI",
        "Computational Linguistics",
        "masters",
        "Computational Linguistics",
        "online",
        24,
    ),
    ("uw-dance-ms", "ARTSCI", "Dance", "masters", "Dance", "on_campus", 24),
    ("uw-design-ms", "ARTSCI", "Design", "masters", "Design", "on_campus", 24),
    ("uw-drama-ms", "ARTSCI", "Drama", "masters", "Drama", "on_campus", 24),
    (
        "uw-east-asia-studies-ms",
        "ARTSCI",
        "East Asia Studies",
        "masters",
        "East Asia Studies",
        "on_campus",
        24,
    ),
    ("uw-economics-ms", "ARTSCI", "Economics", "masters", "Economics", "on_campus", 24),
    ("uw-english-ms", "ARTSCI", "English", "masters", "English", "on_campus", 24),
    (
        "uw-feminist-studies-ms",
        "ARTSCI",
        "Feminist Studies",
        "masters",
        "Feminist Studies",
        "on_campus",
        24,
    ),
    ("uw-fine-arts-ms", "ARTSCI", "Fine Arts", "masters", "Fine Arts", "on_campus", 24),
    ("uw-geography-ms", "ARTSCI", "Geography", "masters", "Geography", "on_campus", 24),
    (
        "uw-german-studies-ms",
        "ARTSCI",
        "German Studies",
        "masters",
        "German Studies",
        "on_campus",
        24,
    ),
    (
        "uw-hispanic-studies-ms",
        "ARTSCI",
        "Hispanic Studies",
        "masters",
        "Hispanic Studies",
        "on_campus",
        24,
    ),
    (
        "uw-international-studies-ms",
        "ARTSCI",
        "International Studies",
        "masters",
        "International Studies",
        "on_campus",
        24,
    ),
    (
        "uw-italian-studies-ms",
        "ARTSCI",
        "Italian Studies",
        "masters",
        "Italian Studies",
        "on_campus",
        24,
    ),
    ("uw-japan-studies-ms", "ARTSCI", "Japan Studies", "masters", "Japan Studies", "on_campus", 24),
    ("uw-korea-studies-ms", "ARTSCI", "Korea Studies", "masters", "Korea Studies", "on_campus", 24),
    ("uw-linguistics-ms", "ARTSCI", "Linguistics", "masters", "Linguistics", "on_campus", 24),
    ("uw-mathematics-ms", "ARTSCI", "Mathematics", "masters", "Mathematics", "on_campus", 24),
    ("uw-music-ms", "ARTSCI", "Music", "masters", "Music", "on_campus", 24),
    (
        "uw-near-eastern-languages-and-civilization-ms",
        "ARTSCI",
        "Near Eastern Languages & Civilization",
        "masters",
        "Near Eastern Languages & Civilization",
        "on_campus",
        24,
    ),
    ("uw-philosophy-ms", "ARTSCI", "Philosophy", "masters", "Philosophy", "on_campus", 24),
    ("uw-physics-ms", "ARTSCI", "Physics", "masters", "Physics", "on_campus", 24),
    (
        "uw-political-science-ms",
        "ARTSCI",
        "Political Science",
        "masters",
        "Political Science",
        "on_campus",
        24,
    ),
    ("uw-psychology-ms", "ARTSCI", "Psychology", "masters", "Psychology", "on_campus", 24),
    (
        "uw-russia-east-european-and-central-asian-studies-ms",
        "ARTSCI",
        "Russia, East European and Central Asian Studies",
        "masters",
        "Russia, East European and Central Asian Studies",
        "on_campus",
        24,
    ),
    ("uw-scandinavian-ms", "ARTSCI", "Scandinavian", "masters", "Scandinavian", "on_campus", 24),
    (
        "uw-slavic-languages-and-literatures-ms",
        "ARTSCI",
        "Slavic Languages & Literatures",
        "masters",
        "Slavic Languages & Literatures",
        "on_campus",
        24,
    ),
    ("uw-sociology-ms", "ARTSCI", "Sociology", "masters", "Sociology", "on_campus", 24),
    (
        "uw-south-asian-studies-ms",
        "ARTSCI",
        "South Asian Studies",
        "masters",
        "South Asian Studies",
        "on_campus",
        24,
    ),
    (
        "uw-southeast-asian-studies-ms",
        "ARTSCI",
        "Southeast Asian Studies",
        "masters",
        "Southeast Asian Studies",
        "on_campus",
        24,
    ),
    (
        "uw-speech-language-pathology-ms",
        "ARTSCI",
        "Speech-Language Pathology",
        "masters",
        "Speech-Language Pathology",
        "on_campus",
        24,
    ),
    ("uw-statistics-ms", "ARTSCI", "Statistics", "masters", "Statistics", "on_campus", 24),
    ("uw-audiology-prof", "ARTSCI", "Audiology", "professional", "Audiology", "on_campus", 48),
    ("uw-anthropology-phd", "ARTSCI", "Anthropology", "phd", "Anthropology", "on_campus", 60),
    (
        "uw-applied-mathematics-phd",
        "ARTSCI",
        "Applied Mathematics",
        "phd",
        "Applied Mathematics",
        "on_campus",
        60,
    ),
    ("uw-art-history-phd", "ARTSCI", "Art History", "phd", "Art History", "on_campus", 60),
    (
        "uw-asian-languages-and-literature-phd",
        "ARTSCI",
        "Asian Languages & Literature",
        "phd",
        "Asian Languages & Literature",
        "on_campus",
        60,
    ),
    ("uw-astronomy-phd", "ARTSCI", "Astronomy", "phd", "Astronomy", "on_campus", 60),
    ("uw-biology-phd", "ARTSCI", "Biology", "phd", "Biology", "on_campus", 60),
    ("uw-chemistry-phd", "ARTSCI", "Chemistry", "phd", "Chemistry", "on_campus", 60),
    (
        "uw-cinema-and-media-studies-phd",
        "ARTSCI",
        "Cinema and Media Studies",
        "phd",
        "Cinema and Media Studies",
        "on_campus",
        60,
    ),
    ("uw-communication-phd", "ARTSCI", "Communication", "phd", "Communication", "on_campus", 60),
    (
        "uw-digital-arts-and-experimental-media-phd",
        "ARTSCI",
        "Digital Arts & Experimental Media",
        "phd",
        "Digital Arts & Experimental Media",
        "on_campus",
        60,
    ),
    ("uw-drama-phd", "ARTSCI", "Drama", "phd", "Drama", "on_campus", 60),
    ("uw-economics-phd", "ARTSCI", "Economics", "phd", "Economics", "on_campus", 60),
    ("uw-english-phd", "ARTSCI", "English", "phd", "English", "on_campus", 60),
    (
        "uw-feminist-studies-phd",
        "ARTSCI",
        "Feminist Studies",
        "phd",
        "Feminist Studies",
        "on_campus",
        60,
    ),
    ("uw-french-studies-phd", "ARTSCI", "French Studies", "phd", "French Studies", "on_campus", 60),
    ("uw-geography-phd", "ARTSCI", "Geography", "phd", "Geography", "on_campus", 60),
    ("uw-german-studies-phd", "ARTSCI", "German Studies", "phd", "German Studies", "on_campus", 60),
    (
        "uw-hispanic-studies-phd",
        "ARTSCI",
        "Hispanic Studies",
        "phd",
        "Hispanic Studies",
        "on_campus",
        60,
    ),
    ("uw-history-phd", "ARTSCI", "History", "phd", "History", "on_campus", 60),
    ("uw-linguistics-phd", "ARTSCI", "Linguistics", "phd", "Linguistics", "on_campus", 60),
    ("uw-mathematics-phd", "ARTSCI", "Mathematics", "phd", "Mathematics", "on_campus", 60),
    ("uw-music-phd", "ARTSCI", "Music", "phd", "Music", "on_campus", 60),
    ("uw-musical-arts-phd", "ARTSCI", "Musical Arts", "phd", "Musical Arts", "on_campus", 60),
    (
        "uw-near-and-middle-eastern-studies-phd",
        "ARTSCI",
        "Near & Middle Eastern Studies",
        "phd",
        "Near & Middle Eastern Studies",
        "on_campus",
        60,
    ),
    ("uw-philosophy-phd", "ARTSCI", "Philosophy", "phd", "Philosophy", "on_campus", 60),
    ("uw-physics-phd", "ARTSCI", "Physics", "phd", "Physics", "on_campus", 60),
    (
        "uw-political-science-phd",
        "ARTSCI",
        "Political Science",
        "phd",
        "Political Science",
        "on_campus",
        60,
    ),
    ("uw-psychology-phd", "ARTSCI", "Psychology", "phd", "Psychology", "on_campus", 60),
    ("uw-scandinavian-phd", "ARTSCI", "Scandinavian", "phd", "Scandinavian", "on_campus", 60),
    (
        "uw-slavic-languages-and-literatures-phd",
        "ARTSCI",
        "Slavic Languages & Literatures",
        "phd",
        "Slavic Languages & Literatures",
        "on_campus",
        60,
    ),
    ("uw-sociology-phd", "ARTSCI", "Sociology", "phd", "Sociology", "on_campus", 60),
    (
        "uw-speech-and-hearing-sciences-phd",
        "ARTSCI",
        "Speech and Hearing Sciences",
        "phd",
        "Speech and Hearing Sciences",
        "on_campus",
        60,
    ),
    ("uw-statistics-phd", "ARTSCI", "Statistics", "phd", "Statistics", "on_campus", 60),
    (
        "uw-architectural-design-bs",
        "BUILT",
        "Architectural Design",
        "bachelors",
        "Architectural Design",
        "on_campus",
        48,
    ),
    (
        "uw-architectural-design-w-const-mgmt-bs",
        "BUILT",
        "Architectural Design (w/Const Mgmt)",
        "bachelors",
        "Architectural Design (w/Const Mgmt)",
        "on_campus",
        48,
    ),
    (
        "uw-architectural-studies-bs",
        "BUILT",
        "Architectural Studies",
        "bachelors",
        "Architectural Studies",
        "on_campus",
        48,
    ),
    (
        "uw-community-environment-and-planning-bs",
        "BUILT",
        "Community, Environment, and Planning",
        "bachelors",
        "Community, Environment, and Planning",
        "on_campus",
        48,
    ),
    (
        "uw-environmental-design-and-sustainability-bs",
        "BUILT",
        "Environmental Design and Sustainability",
        "bachelors",
        "Environmental Design and Sustainability",
        "on_campus",
        48,
    ),
    ("uw-real-estate-bs", "BUILT", "Real Estate", "bachelors", "Real Estate", "on_campus", 48),
    ("uw-architecture-ms", "BUILT", "Architecture", "masters", "Architecture", "on_campus", 24),
    ("uw-concurrent-ms", "BUILT", "Concurrent", "masters", "Concurrent", "on_campus", 24),
    (
        "uw-construction-management-ms",
        "BUILT",
        "Construction Management",
        "masters",
        "Construction Management",
        "online",
        24,
    ),
    (
        "uw-infrastructure-planning-and-management-ms",
        "BUILT",
        "Infrastructure Planning & Management",
        "masters",
        "Infrastructure Planning & Management",
        "on_campus",
        24,
    ),
    (
        "uw-infrastructure-planning-and-management-ms-2",
        "BUILT",
        "Infrastructure Planning & Management",
        "masters",
        "Infrastructure Planning & Management",
        "online",
        24,
    ),
    (
        "uw-landscape-architecture-ms",
        "BUILT",
        "Landscape Architecture",
        "masters",
        "Landscape Architecture",
        "on_campus",
        24,
    ),
    ("uw-real-estate-ms", "BUILT", "Real Estate", "masters", "Real Estate", "on_campus", 24),
    (
        "uw-urban-planning-ms",
        "BUILT",
        "Urban Planning",
        "masters",
        "Urban Planning",
        "on_campus",
        24,
    ),
    (
        "uw-built-environment-phd",
        "BUILT",
        "Built Environment",
        "phd",
        "Built Environment",
        "on_campus",
        60,
    ),
    (
        "uw-urban-design-and-planning-phd",
        "BUILT",
        "Urban Design & Planning",
        "phd",
        "Urban Design & Planning",
        "on_campus",
        60,
    ),
    ("uw-accounting-bs", "BUS", "Accounting", "bachelors", "Accounting", "on_campus", 48),
    (
        "uw-accounting-for-business-professionals-bs",
        "BUS",
        "Accounting for Business Professionals",
        "bachelors",
        "Accounting for Business Professionals",
        "on_campus",
        48,
    ),
    (
        "uw-entrepreneurship-bs",
        "BUS",
        "Entrepreneurship",
        "bachelors",
        "Entrepreneurship",
        "on_campus",
        48,
    ),
    ("uw-finance-bs", "BUS", "Finance", "bachelors", "Finance", "on_campus", 48),
    (
        "uw-human-resources-management-bs",
        "BUS",
        "Human Resources Management",
        "bachelors",
        "Human Resources Management",
        "on_campus",
        48,
    ),
    (
        "uw-information-systems-bs",
        "BUS",
        "Information Systems",
        "bachelors",
        "Information Systems",
        "on_campus",
        48,
    ),
    ("uw-marketing-bs", "BUS", "Marketing", "bachelors", "Marketing", "on_campus", 48),
    (
        "uw-operations-and-supply-chain-management-bs",
        "BUS",
        "Operations and Supply Chain Management",
        "bachelors",
        "Operations and Supply Chain Management",
        "on_campus",
        48,
    ),
    (
        "uw-business-administration-ms",
        "BUS",
        "Business Administration",
        "masters",
        "Business Administration",
        "on_campus",
        24,
    ),
    (
        "uw-business-analytics-ms",
        "BUS",
        "Business Analytics",
        "masters",
        "Business Analytics",
        "on_campus",
        24,
    ),
    (
        "uw-entrepreneurship-ms",
        "BUS",
        "Entrepreneurship",
        "masters",
        "Entrepreneurship",
        "on_campus",
        24,
    ),
    (
        "uw-information-systems-ms",
        "BUS",
        "Information Systems",
        "masters",
        "Information Systems",
        "on_campus",
        24,
    ),
    (
        "uw-professional-accounting-ms",
        "BUS",
        "Professional Accounting",
        "masters",
        "Professional Accounting",
        "on_campus",
        24,
    ),
    (
        "uw-supply-chain-management-ms",
        "BUS",
        "Supply Chain Management",
        "masters",
        "Supply Chain Management",
        "on_campus",
        24,
    ),
    ("uw-taxation-ms", "BUS", "Taxation", "masters", "Taxation", "on_campus", 24),
    (
        "uw-business-administration-phd",
        "BUS",
        "Business Administration",
        "phd",
        "Business Administration",
        "on_campus",
        60,
    ),
    ("uw-dentistry-ms", "DENT", "Dentistry", "masters", "Dentistry", "on_campus", 24),
    ("uw-endodontics-ms", "DENT", "Endodontics", "masters", "Endodontics", "on_campus", 24),
    (
        "uw-oral-health-sciences-ms",
        "DENT",
        "Oral Health Sciences",
        "masters",
        "Oral Health Sciences",
        "on_campus",
        24,
    ),
    ("uw-oral-medicine-ms", "DENT", "Oral Medicine", "masters", "Oral Medicine", "on_campus", 24),
    ("uw-orthodontics-ms", "DENT", "Orthodontics", "masters", "Orthodontics", "on_campus", 24),
    ("uw-periodontics-ms", "DENT", "Periodontics", "masters", "Periodontics", "on_campus", 24),
    (
        "uw-prosthodontics-ms",
        "DENT",
        "Prosthodontics",
        "masters",
        "Prosthodontics",
        "on_campus",
        24,
    ),
    ("uw-dentistry-prof", "DENT", "Dentistry", "professional", "Dentistry", "on_campus", 48),
    ("uw-dentistry-phd", "DENT", "Dentistry", "phd", "Dentistry", "on_campus", 60),
    (
        "uw-oral-health-sciences-phd",
        "DENT",
        "Oral Health Sciences",
        "phd",
        "Oral Health Sciences",
        "on_campus",
        60,
    ),
    (
        "uw-early-care-and-education-bs",
        "EDUC",
        "Early Care and Education",
        "bachelors",
        "Early Care and Education",
        "on_campus",
        48,
    ),
    (
        "uw-early-care-and-education-fee-based-online-bs",
        "EDUC",
        "Early Care and Education (fee-based) (online)",
        "bachelors",
        "Early Care and Education (fee-based) (online)",
        "on_campus",
        48,
    ),
    (
        "uw-early-childhood-and-family-studies-bs",
        "EDUC",
        "Early Childhood and Family Studies",
        "bachelors",
        "Early Childhood and Family Studies",
        "on_campus",
        48,
    ),
    (
        "uw-education-studies-bs",
        "EDUC",
        "Education Studies",
        "bachelors",
        "Education Studies",
        "on_campus",
        48,
    ),
    (
        "uw-education-communities-and-organizations-bs",
        "EDUC",
        "Education, Communities and Organizations",
        "bachelors",
        "Education, Communities and Organizations",
        "on_campus",
        48,
    ),
    (
        "uw-curriculum-and-instruction-ms",
        "EDUC",
        "Curriculum & Instruction",
        "masters",
        "Curriculum & Instruction",
        "on_campus",
        24,
    ),
    (
        "uw-educational-foundations-leadership-and-policy-ms",
        "EDUC",
        "Educational Foundations, Leadership & Policy",
        "masters",
        "Educational Foundations, Leadership & Policy",
        "on_campus",
        24,
    ),
    (
        "uw-educational-leadership-and-policy-studies-ms",
        "EDUC",
        "Educational Leadership & Policy Studies",
        "masters",
        "Educational Leadership & Policy Studies",
        "on_campus",
        24,
    ),
    (
        "uw-learning-sciences-and-human-development-ms",
        "EDUC",
        "Learning Sciences & Human Development",
        "masters",
        "Learning Sciences & Human Development",
        "on_campus",
        24,
    ),
    (
        "uw-master-in-teaching-ms",
        "EDUC",
        "Master In Teaching",
        "masters",
        "Master In Teaching",
        "on_campus",
        24,
    ),
    (
        "uw-measurement-and-statistics-ms",
        "EDUC",
        "Measurement & Statistics",
        "masters",
        "Measurement & Statistics",
        "on_campus",
        24,
    ),
    (
        "uw-special-education-ms",
        "EDUC",
        "Special Education",
        "masters",
        "Special Education",
        "on_campus",
        24,
    ),
    (
        "uw-curriculum-and-instruction-phd",
        "EDUC",
        "Curriculum & Instruction",
        "phd",
        "Curriculum & Instruction",
        "on_campus",
        60,
    ),
    (
        "uw-education-curriculum-and-instruction-phd",
        "EDUC",
        "Education: Curriculum & Instruction",
        "phd",
        "Education: Curriculum & Instruction",
        "on_campus",
        60,
    ),
    (
        "uw-education-educ-leadershp-and-policy-st-phd",
        "EDUC",
        "Education: Educ Leadershp & Policy St",
        "phd",
        "Education: Educ Leadershp & Policy St",
        "on_campus",
        60,
    ),
    (
        "uw-education-learning-sciences-and-human-development-phd",
        "EDUC",
        "Education: Learning Sciences & Human Development",
        "phd",
        "Education: Learning Sciences & Human Development",
        "on_campus",
        60,
    ),
    (
        "uw-education-measurement-and-statistics-phd",
        "EDUC",
        "Education: Measurement & Statistics",
        "phd",
        "Education: Measurement & Statistics",
        "on_campus",
        60,
    ),
    (
        "uw-education-school-psychology-phd",
        "EDUC",
        "Education: School Psychology",
        "phd",
        "Education: School Psychology",
        "on_campus",
        60,
    ),
    (
        "uw-education-special-education-phd",
        "EDUC",
        "Education: Special Education",
        "phd",
        "Education: Special Education",
        "on_campus",
        60,
    ),
    (
        "uw-educational-leadership-and-policy-studies-phd",
        "EDUC",
        "Educational Leadership & Policy Studies",
        "phd",
        "Educational Leadership & Policy Studies",
        "on_campus",
        60,
    ),
    (
        "uw-special-education-phd",
        "EDUC",
        "Special Education",
        "phd",
        "Special Education",
        "on_campus",
        60,
    ),
    ("uw-engineering-bs", "ENGR", "Engineering", "bachelors", "Engineering", "on_campus", 48),
    (
        "uw-aeronautics-and-astronautics-ms",
        "ENGR",
        "Aeronautics and Astronautics",
        "masters",
        "Aeronautics and Astronautics",
        "on_campus",
        24,
    ),
    (
        "uw-aerospace-engineering-ms",
        "ENGR",
        "Aerospace Engineering",
        "masters",
        "Aerospace Engineering",
        "online",
        24,
    ),
    (
        "uw-applied-bioengineering-ms",
        "ENGR",
        "Applied Bioengineering",
        "masters",
        "Applied Bioengineering",
        "on_campus",
        24,
    ),
    (
        "uw-artificial-intelligence-and-machine-learning-for-engineering-ms",
        "ENGR",
        "Artificial Intelligence and Machine Learning for Engineering",
        "masters",
        "Artificial Intelligence and Machine Learning for Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-bioengineering-ms",
        "ENGR",
        "Bioengineering",
        "masters",
        "Bioengineering",
        "on_campus",
        24,
    ),
    (
        "uw-chemical-engineering-ms",
        "ENGR",
        "Chemical Engineering",
        "masters",
        "Chemical Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-civil-engineering-ms",
        "ENGR",
        "Civil Engineering",
        "masters",
        "Civil Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-computer-science-and-engineering-ms",
        "ENGR",
        "Computer Science & Engineering",
        "masters",
        "Computer Science & Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-electrical-and-computer-engineering-ms",
        "ENGR",
        "Electrical and Computer Engineering",
        "masters",
        "Electrical and Computer Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-engineering-in-leadership-and-systems-innovation-ms",
        "ENGR",
        "Engineering in Leadership and Systems Innovation",
        "masters",
        "Engineering in Leadership and Systems Innovation",
        "on_campus",
        24,
    ),
    (
        "uw-engineering-in-multidisciplinary-engineering-ms",
        "ENGR",
        "Engineering in Multidisciplinary Engineering",
        "masters",
        "Engineering in Multidisciplinary Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-human-centered-design-and-engineering-ms",
        "ENGR",
        "Human Centered Design & Engineering",
        "masters",
        "Human Centered Design & Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-industrial-and-systems-engineering-ms",
        "ENGR",
        "Industrial & Systems Engineering",
        "masters",
        "Industrial & Systems Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-industrial-engineering-ms",
        "ENGR",
        "Industrial Engineering",
        "masters",
        "Industrial Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-materials-science-and-engineering-ms",
        "ENGR",
        "Materials Science & Engineering",
        "masters",
        "Materials Science & Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-materials-science-and-engineering-ms-2",
        "ENGR",
        "Materials Science and Engineering",
        "masters",
        "Materials Science and Engineering",
        "on_campus",
        24,
    ),
    (
        "uw-mechanical-engineering-ms",
        "ENGR",
        "Mechanical Engineering",
        "masters",
        "Mechanical Engineering",
        "online",
        24,
    ),
    (
        "uw-pharmaceutical-bioengineering-ms",
        "ENGR",
        "Pharmaceutical Bioengineering",
        "masters",
        "Pharmaceutical Bioengineering",
        "online",
        24,
    ),
    (
        "uw-supply-chain-transportation-and-logistics-ms",
        "ENGR",
        "Supply Chain Transportation & Logistics",
        "masters",
        "Supply Chain Transportation & Logistics",
        "online",
        24,
    ),
    (
        "uw-sustainable-transportation-ms",
        "ENGR",
        "Sustainable Transportation",
        "masters",
        "Sustainable Transportation",
        "online",
        24,
    ),
    (
        "uw-technology-innovation-ms",
        "ENGR",
        "Technology Innovation",
        "masters",
        "Technology Innovation",
        "on_campus",
        24,
    ),
    (
        "uw-aeronautics-and-astronautics-phd",
        "ENGR",
        "Aeronautics & Astronautics",
        "phd",
        "Aeronautics & Astronautics",
        "on_campus",
        60,
    ),
    ("uw-bioengineering-phd", "ENGR", "Bioengineering", "phd", "Bioengineering", "on_campus", 60),
    (
        "uw-chemical-engineering-phd",
        "ENGR",
        "Chemical Engineering",
        "phd",
        "Chemical Engineering",
        "on_campus",
        60,
    ),
    (
        "uw-civil-engineering-phd",
        "ENGR",
        "Civil Engineering",
        "phd",
        "Civil Engineering",
        "on_campus",
        60,
    ),
    (
        "uw-computer-science-and-engineering-phd",
        "ENGR",
        "Computer Science & Engineering",
        "phd",
        "Computer Science & Engineering",
        "on_campus",
        60,
    ),
    (
        "uw-electrical-and-computer-engineering-phd",
        "ENGR",
        "Electrical and Computer Engineering",
        "phd",
        "Electrical and Computer Engineering",
        "on_campus",
        60,
    ),
    (
        "uw-industrial-engineering-phd",
        "ENGR",
        "Industrial Engineering",
        "phd",
        "Industrial Engineering",
        "on_campus",
        60,
    ),
    (
        "uw-materials-science-and-engineering-phd",
        "ENGR",
        "Materials Science & Engineering",
        "phd",
        "Materials Science & Engineering",
        "on_campus",
        60,
    ),
    (
        "uw-mechanical-engineering-phd",
        "ENGR",
        "Mechanical Engineering",
        "phd",
        "Mechanical Engineering",
        "on_campus",
        60,
    ),
    (
        "uw-aquatic-conservation-and-ecology-bs",
        "ENV",
        "Aquatic Conservation and Ecology",
        "bachelors",
        "Aquatic Conservation and Ecology",
        "on_campus",
        48,
    ),
    (
        "uw-atmospheric-and-climate-science-bs",
        "ENV",
        "Atmospheric and Climate Science",
        "bachelors",
        "Atmospheric and Climate Science",
        "on_campus",
        48,
    ),
    (
        "uw-earth-and-space-sciences-bs",
        "ENV",
        "Earth and Space Sciences",
        "bachelors",
        "Earth and Space Sciences",
        "on_campus",
        48,
    ),
    (
        "uw-environmental-science-and-terrestrial-resource-management-bs",
        "ENV",
        "Environmental Science and Terrestrial Resource Management",
        "bachelors",
        "Environmental Science and Terrestrial Resource Management",
        "on_campus",
        48,
    ),
    (
        "uw-environmental-studies-bs",
        "ENV",
        "Environmental Studies",
        "bachelors",
        "Environmental Studies",
        "on_campus",
        48,
    ),
    (
        "uw-marine-biology-bs",
        "ENV",
        "Marine Biology",
        "bachelors",
        "Marine Biology",
        "on_campus",
        48,
    ),
    ("uw-oceanography-bs", "ENV", "Oceanography", "bachelors", "Oceanography", "on_campus", 48),
    (
        "uw-sustainable-bioresource-systems-engineering-bs",
        "ENV",
        "Sustainable Bioresource Systems Engineering",
        "bachelors",
        "Sustainable Bioresource Systems Engineering",
        "on_campus",
        48,
    ),
    (
        "uw-aquatic-and-fishery-sciences-ms",
        "ENV",
        "Aquatic & Fishery Sciences",
        "masters",
        "Aquatic & Fishery Sciences",
        "on_campus",
        24,
    ),
    (
        "uw-atmospheric-and-climate-science-ms",
        "ENV",
        "Atmospheric and Climate Science",
        "masters",
        "Atmospheric and Climate Science",
        "on_campus",
        24,
    ),
    (
        "uw-earth-and-space-sciences-ms",
        "ENV",
        "Earth & Space Sciences",
        "masters",
        "Earth & Space Sciences",
        "on_campus",
        24,
    ),
    (
        "uw-environmental-and-forest-sciences-ms",
        "ENV",
        "Environmental & Forest Sciences",
        "masters",
        "Environmental & Forest Sciences",
        "on_campus",
        24,
    ),
    (
        "uw-forest-resources-ms",
        "ENV",
        "Forest Resources",
        "masters",
        "Forest Resources",
        "on_campus",
        24,
    ),
    ("uw-marine-affairs-ms", "ENV", "Marine Affairs", "masters", "Marine Affairs", "on_campus", 24),
    ("uw-oceanography-ms", "ENV", "Oceanography", "masters", "Oceanography", "on_campus", 24),
    (
        "uw-quantitative-ecology-and-resource-management-ms",
        "ENV",
        "Quantitative Ecology & Resource Management",
        "masters",
        "Quantitative Ecology & Resource Management",
        "on_campus",
        24,
    ),
    (
        "uw-aquatic-and-fishery-sciences-phd",
        "ENV",
        "Aquatic & Fishery Sciences",
        "phd",
        "Aquatic & Fishery Sciences",
        "on_campus",
        60,
    ),
    (
        "uw-atmospheric-and-climate-science-phd",
        "ENV",
        "Atmospheric and Climate Science",
        "phd",
        "Atmospheric and Climate Science",
        "on_campus",
        60,
    ),
    (
        "uw-earth-and-space-sciences-phd",
        "ENV",
        "Earth & Space Sciences",
        "phd",
        "Earth & Space Sciences",
        "on_campus",
        60,
    ),
    (
        "uw-environmental-and-forest-sciences-phd",
        "ENV",
        "Environmental & Forest Sciences",
        "phd",
        "Environmental & Forest Sciences",
        "on_campus",
        60,
    ),
    ("uw-oceanography-phd", "ENV", "Oceanography", "phd", "Oceanography", "on_campus", 60),
    (
        "uw-quantitative-ecology-and-resource-management-phd",
        "ENV",
        "Quantitative Ecology & Resource Management",
        "phd",
        "Quantitative Ecology & Resource Management",
        "on_campus",
        60,
    ),
    (
        "uw-information-management-ms",
        "ISCHOOL",
        "Information Management",
        "masters",
        "Information Management",
        "online",
        24,
    ),
    (
        "uw-information-science-ms",
        "ISCHOOL",
        "Information Science",
        "masters",
        "Information Science",
        "on_campus",
        24,
    ),
    (
        "uw-library-and-information-science-ms",
        "ISCHOOL",
        "Library & Information Science",
        "masters",
        "Library & Information Science",
        "online",
        24,
    ),
    ("uw-museology-ms", "ISCHOOL", "Museology", "masters", "Museology", "on_campus", 24),
    (
        "uw-information-science-phd",
        "ISCHOOL",
        "Information Science",
        "phd",
        "Information Science",
        "on_campus",
        60,
    ),
    ("uw-data-science-ms", "GRAD", "Data Science", "masters", "Data Science", "on_campus", 24),
    (
        "uw-human-computer-interaction-and-design-ms",
        "GRAD",
        "Human-Computer Interaction & Design",
        "masters",
        "Human-Computer Interaction & Design",
        "on_campus",
        24,
    ),
    (
        "uw-molecular-and-cellular-biology-ms",
        "GRAD",
        "Molecular & Cellular Biology",
        "masters",
        "Molecular & Cellular Biology",
        "on_campus",
        24,
    ),
    (
        "uw-molecular-engineering-ms",
        "GRAD",
        "Molecular Engineering",
        "masters",
        "Molecular Engineering",
        "on_campus",
        24,
    ),
    ("uw-neuroscience-ms", "GRAD", "Neuroscience", "masters", "Neuroscience", "on_campus", 24),
    ("uw-individual-phd-phd", "GRAD", "Individual PhD", "phd", "Individual PhD", "on_campus", 60),
    (
        "uw-molecular-and-cellular-biology-phd",
        "GRAD",
        "Molecular & Cellular Biology",
        "phd",
        "Molecular & Cellular Biology",
        "on_campus",
        60,
    ),
    (
        "uw-molecular-engineering-phd",
        "GRAD",
        "Molecular Engineering",
        "phd",
        "Molecular Engineering",
        "on_campus",
        60,
    ),
    ("uw-neuroscience-phd", "GRAD", "Neuroscience", "phd", "Neuroscience", "on_campus", 60),
    ("uw-jurisprudence-ms", "LAW", "Jurisprudence", "masters", "Jurisprudence", "on_campus", 24),
    ("uw-laws-ms", "LAW", "Laws", "masters", "Laws", "on_campus", 24),
    (
        "uw-laws-in-taxation-ms",
        "LAW",
        "Laws In Taxation",
        "masters",
        "Laws In Taxation",
        "on_campus",
        24,
    ),
    ("uw-law-prof", "LAW", "Law", "professional", "Law", "on_campus", 48),
    ("uw-law-phd", "LAW", "Law", "phd", "Law", "on_campus", 60),
    (
        "uw-anatomic-pathology-ms",
        "MED",
        "Anatomic Pathology",
        "masters",
        "Anatomic Pathology",
        "on_campus",
        24,
    ),
    ("uw-biochemistry-ms", "MED", "Biochemistry", "masters", "Biochemistry", "on_campus", 24),
    ("uw-bioethics-ms", "MED", "Bioethics", "masters", "Bioethics", "on_campus", 24),
    (
        "uw-biomedical-and-health-informatics-ms",
        "MED",
        "Biomedical & Health Informatics",
        "masters",
        "Biomedical & Health Informatics",
        "on_campus",
        24,
    ),
    (
        "uw-clinical-health-services-ms",
        "MED",
        "Clinical Health Services",
        "masters",
        "Clinical Health Services",
        "on_campus",
        24,
    ),
    (
        "uw-comparative-medicine-ms",
        "MED",
        "Comparative Medicine",
        "masters",
        "Comparative Medicine",
        "on_campus",
        24,
    ),
    (
        "uw-genetic-counseling-ms",
        "MED",
        "Genetic Counseling",
        "masters",
        "Genetic Counseling",
        "on_campus",
        24,
    ),
    (
        "uw-genome-sciences-ms",
        "MED",
        "Genome Sciences",
        "masters",
        "Genome Sciences",
        "on_campus",
        24,
    ),
    (
        "uw-health-metrics-sciences-ms",
        "MED",
        "Health Metrics Sciences",
        "masters",
        "Health Metrics Sciences",
        "on_campus",
        24,
    ),
    ("uw-immunology-ms", "MED", "Immunology", "masters", "Immunology", "on_campus", 24),
    (
        "uw-laboratory-medicine-ms",
        "MED",
        "Laboratory Medicine",
        "masters",
        "Laboratory Medicine",
        "on_campus",
        24,
    ),
    ("uw-microbiology-ms", "MED", "Microbiology", "masters", "Microbiology", "on_campus", 24),
    (
        "uw-molecular-medicine-and-mechanisms-of-disease-ms",
        "MED",
        "Molecular Medicine and Mechanisms of Disease",
        "masters",
        "Molecular Medicine and Mechanisms of Disease",
        "on_campus",
        24,
    ),
    (
        "uw-neurobiology-and-biophysics-ms",
        "MED",
        "Neurobiology and Biophysics",
        "masters",
        "Neurobiology and Biophysics",
        "on_campus",
        24,
    ),
    (
        "uw-occupational-therapy-ms",
        "MED",
        "Occupational Therapy",
        "masters",
        "Occupational Therapy",
        "on_campus",
        24,
    ),
    ("uw-pharmacology-ms", "MED", "Pharmacology", "masters", "Pharmacology", "on_campus", 24),
    (
        "uw-prosthetics-and-orthotics-ms",
        "MED",
        "Prosthetics & Orthotics",
        "masters",
        "Prosthetics & Orthotics",
        "on_campus",
        24,
    ),
    (
        "uw-rehabilitation-medicine-ms",
        "MED",
        "Rehabilitation Medicine",
        "masters",
        "Rehabilitation Medicine",
        "on_campus",
        24,
    ),
    ("uw-medicine-prof", "MED", "Medicine", "professional", "Medicine", "on_campus", 48),
    (
        "uw-physical-therapy-prof",
        "MED",
        "Physical Therapy",
        "professional",
        "Physical Therapy",
        "on_campus",
        48,
    ),
    ("uw-biochemistry-phd", "MED", "Biochemistry", "phd", "Biochemistry", "on_campus", 60),
    (
        "uw-biomedical-and-health-informatics-phd",
        "MED",
        "Biomedical & Health Informatics",
        "phd",
        "Biomedical & Health Informatics",
        "on_campus",
        60,
    ),
    ("uw-genome-sciences-phd", "MED", "Genome Sciences", "phd", "Genome Sciences", "on_campus", 60),
    (
        "uw-health-metrics-global-health-metrics-and-implementation-sciences-phd",
        "MED",
        "Health Metrics: Global Health Metrics & Implementation Sciences",
        "phd",
        "Health Metrics: Global Health Metrics & Implementation Sciences",
        "on_campus",
        60,
    ),
    ("uw-immunology-phd", "MED", "Immunology", "phd", "Immunology", "on_campus", 60),
    ("uw-microbiology-phd", "MED", "Microbiology", "phd", "Microbiology", "on_campus", 60),
    (
        "uw-molecular-medicine-and-mechanisms-of-disease-phd",
        "MED",
        "Molecular Medicine and Mechanisms of Disease",
        "phd",
        "Molecular Medicine and Mechanisms of Disease",
        "on_campus",
        60,
    ),
    (
        "uw-neurobiology-and-biophysics-phd",
        "MED",
        "Neurobiology and Biophysics",
        "phd",
        "Neurobiology and Biophysics",
        "on_campus",
        60,
    ),
    ("uw-pharmacology-phd", "MED", "Pharmacology", "phd", "Pharmacology", "on_campus", 60),
    (
        "uw-rehabilitation-science-phd",
        "MED",
        "Rehabilitation Science",
        "phd",
        "Rehabilitation Science",
        "on_campus",
        60,
    ),
    ("uw-nursing-ms", "NURS", "Nursing", "masters", "Nursing", "on_campus", 24),
    (
        "uw-nursing-practice-prof",
        "NURS",
        "Nursing Practice",
        "professional",
        "Nursing Practice",
        "on_campus",
        48,
    ),
    ("uw-nursing-phd", "NURS", "Nursing", "phd", "Nursing", "on_campus", 60),
    (
        "uw-biomedical-regulatory-affairs-ms",
        "PHARM",
        "Biomedical Regulatory Affairs",
        "masters",
        "Biomedical Regulatory Affairs",
        "on_campus",
        24,
    ),
    (
        "uw-health-economics-and-outcomes-research-ms",
        "PHARM",
        "Health Economics and Outcomes Research",
        "masters",
        "Health Economics and Outcomes Research",
        "on_campus",
        24,
    ),
    (
        "uw-medicinal-chemistry-ms",
        "PHARM",
        "Medicinal Chemistry",
        "masters",
        "Medicinal Chemistry",
        "on_campus",
        24,
    ),
    ("uw-pharmaceutics-ms", "PHARM", "Pharmaceutics", "masters", "Pharmaceutics", "on_campus", 24),
    ("uw-pharmacy-prof", "PHARM", "Pharmacy", "professional", "Pharmacy", "on_campus", 48),
    (
        "uw-health-economics-and-outcomes-research-phd",
        "PHARM",
        "Health Economics and Outcomes Research",
        "phd",
        "Health Economics and Outcomes Research",
        "on_campus",
        60,
    ),
    (
        "uw-medicinal-chemistry-phd",
        "PHARM",
        "Medicinal Chemistry",
        "phd",
        "Medicinal Chemistry",
        "on_campus",
        60,
    ),
    ("uw-pharmaceutics-phd", "PHARM", "Pharmaceutics", "phd", "Pharmaceutics", "on_campus", 60),
    (
        "uw-public-service-and-policy-bs",
        "EVANS",
        "Public Service and Policy",
        "bachelors",
        "Public Service and Policy",
        "on_campus",
        48,
    ),
    (
        "uw-public-administration-ms",
        "EVANS",
        "Public Administration",
        "masters",
        "Public Administration",
        "on_campus",
        24,
    ),
    (
        "uw-public-policy-and-management-ms",
        "EVANS",
        "Public Policy & Management",
        "masters",
        "Public Policy & Management",
        "on_campus",
        24,
    ),
    (
        "uw-public-policy-and-management-phd",
        "EVANS",
        "Public Policy & Management",
        "phd",
        "Public Policy & Management",
        "on_campus",
        60,
    ),
    (
        "uw-environmental-public-health-bs",
        "PUBH",
        "Environmental Public Health",
        "bachelors",
        "Environmental Public Health",
        "on_campus",
        48,
    ),
    (
        "uw-food-systems-nutrition-and-health-bs",
        "PUBH",
        "Food Systems, Nutrition, and Health",
        "bachelors",
        "Food Systems, Nutrition, and Health",
        "on_campus",
        48,
    ),
    (
        "uw-public-health-global-health-bs",
        "PUBH",
        "Public Health-Global Health",
        "bachelors",
        "Public Health-Global Health",
        "on_campus",
        48,
    ),
    ("uw-biostatistics-ms", "PUBH", "Biostatistics", "masters", "Biostatistics", "on_campus", 24),
    (
        "uw-environmental-health-sciences-ms",
        "PUBH",
        "Environmental Health Sciences",
        "masters",
        "Environmental Health Sciences",
        "on_campus",
        24,
    ),
    ("uw-epidemiology-ms", "PUBH", "Epidemiology", "masters", "Epidemiology", "on_campus", 24),
    (
        "uw-genetic-epidemiology-ms",
        "PUBH",
        "Genetic Epidemiology",
        "masters",
        "Genetic Epidemiology",
        "on_campus",
        24,
    ),
    ("uw-global-health-ms", "PUBH", "Global Health", "masters", "Global Health", "on_campus", 24),
    (
        "uw-health-administration-ms",
        "PUBH",
        "Health Administration",
        "masters",
        "Health Administration",
        "online",
        24,
    ),
    (
        "uw-health-informatics-and-health-information-management-ms",
        "PUBH",
        "Health Informatics & Health Information Management",
        "masters",
        "Health Informatics & Health Information Management",
        "online",
        24,
    ),
    (
        "uw-health-systems-and-population-health-ms",
        "PUBH",
        "Health Systems and Population Health",
        "masters",
        "Health Systems and Population Health",
        "on_campus",
        24,
    ),
    (
        "uw-nutritional-sciences-ms",
        "PUBH",
        "Nutritional Sciences",
        "masters",
        "Nutritional Sciences",
        "on_campus",
        24,
    ),
    ("uw-pathobiology-ms", "PUBH", "Pathobiology", "masters", "Pathobiology", "on_campus", 24),
    (
        "uw-public-health-genetics-ms",
        "PUBH",
        "Public Health Genetics",
        "masters",
        "Public Health Genetics",
        "on_campus",
        24,
    ),
    (
        "uw-public-health-nutrition-ms",
        "PUBH",
        "Public Health Nutrition",
        "masters",
        "Public Health Nutrition",
        "on_campus",
        24,
    ),
    ("uw-biostatistics-phd", "PUBH", "Biostatistics", "phd", "Biostatistics", "on_campus", 60),
    (
        "uw-environmental-health-sciences-phd",
        "PUBH",
        "Environmental Health Sciences",
        "phd",
        "Environmental Health Sciences",
        "on_campus",
        60,
    ),
    ("uw-epidemiology-phd", "PUBH", "Epidemiology", "phd", "Epidemiology", "on_campus", 60),
    (
        "uw-global-health-global-health-metrics-and-implementation-sciences-phd",
        "PUBH",
        "Global Health: Global Health Metrics & Implementation Sciences",
        "phd",
        "Global Health: Global Health Metrics & Implementation Sciences",
        "on_campus",
        60,
    ),
    (
        "uw-health-services-phd",
        "PUBH",
        "Health Services",
        "phd",
        "Health Services",
        "on_campus",
        60,
    ),
    (
        "uw-nutritional-sciences-phd",
        "PUBH",
        "Nutritional Sciences",
        "phd",
        "Nutritional Sciences",
        "on_campus",
        60,
    ),
    ("uw-pathobiology-phd", "PUBH", "Pathobiology", "phd", "Pathobiology", "on_campus", 60),
    (
        "uw-public-health-genetics-phd",
        "PUBH",
        "Public Health Genetics",
        "phd",
        "Public Health Genetics",
        "on_campus",
        60,
    ),
    (
        "uw-social-welfare-bs",
        "SOCW",
        "Social Welfare",
        "bachelors",
        "Social Welfare",
        "on_campus",
        48,
    ),
    ("uw-social-work-ms", "SOCW", "Social Work", "masters", "Social Work", "on_campus", 24),
    ("uw-social-welfare-phd", "SOCW", "Social Welfare", "phd", "Social Welfare", "on_campus", 60),
]

_DEGREE_ROLE = {
    "bachelors": "an undergraduate degree program",
    "masters": "a master's degree program",
    "phd": "a doctoral (Ph.D.) program",
    "professional": "a professional degree program",
    "certificate": "a certificate program",
    "diploma": "a diploma program",
}
_DELIVERY_PHRASE = {
    "online": " It is delivered fully online through UW Professional & Continuing Education.",
    "hybrid": " It is delivered in a hybrid format.",
}


def _description(name: str, dtype: str, school_key: str, fmt: str) -> str:
    role = _DEGREE_ROLE.get(dtype, "a graduate program")
    school_disp = SCHOOL_NAME[school_key]
    delivery = _DELIVERY_PHRASE.get(fmt, "")
    return f"{name} is {role} offered through UW's {school_disp}.{delivery}"


def _build_catalog() -> list[dict]:
    out = []
    for slug, sk, name, dtype, dept, fmt, dur in _CATALOG:
        out.append(
            {
                "slug": slug,
                "school": SCHOOL_NAME[sk],
                "school_key": sk,
                "program_name": name,
                "degree_type": dtype,
                "department": dept,
                "delivery_format": fmt,
                "duration_months": dur,
                "description": _description(name, dtype, sk, fmt),
            }
        )
    return out


PROGRAMS: list[dict] = _build_catalog()
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

_WEBSITE_OVERRIDE: dict[str, str] = {
    "uw-computer-science-bs": "https://www.cs.washington.edu/academics/ugrad",
    "uw-computer-science-and-engineering-ms": "https://www.cs.washington.edu/academics/grad",
    "uw-computer-science-and-engineering-phd": "https://www.cs.washington.edu/academics/phd",
    "uw-medicine-prof": "https://www.uwmedicine.org/school-of-medicine/md-program",
    "uw-dentistry-prof": "https://dental.washington.edu/dds-program/",
    "uw-law-prof": "https://www.law.uw.edu/academics/jd",
    "uw-pharmacy-prof": "https://sop.washington.edu/pharmd/",
    "uw-nursing-practice-prof": "https://nursing.uw.edu/program/doctor-of-nursing-practice/",
    "uw-business-administration-ms": "https://foster.uw.edu/academics/degree-programs/full-time-mba/",
    "uw-library-and-information-science-ms": "https://ischool.uw.edu/programs/mlis",
    "uw-information-management-ms": "https://ischool.uw.edu/programs/msim",
}
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "uw-computer-science-bs": ["Paul G. Allen School", "computer science", "CS", "Allen School"],
    "uw-computer-science-and-engineering-ms": [
        "Paul G. Allen School",
        "computer science",
        "Allen School",
    ],
    "uw-computer-science-and-engineering-phd": [
        "Paul G. Allen School",
        "computer science",
        "Allen School",
    ],
    "uw-medicine-prof": ["UW Medicine", "School of Medicine", "M.D.", "WWAMI"],
    "uw-nursing-practice-prof": ["School of Nursing", "DNP", "nursing"],
    "uw-business-administration-ms": ["Foster School of Business", "Foster MBA", "MBA"],
    "uw-law-prof": ["School of Law", "J.D.", "Juris Doctor"],
    "uw-pharmacy-prof": ["School of Pharmacy", "PharmD", "pharmacy"],
    "uw-library-and-information-science-ms": ["iSchool", "MLIS", "library and information science"],
}


def _website_for(spec: dict) -> str:
    return _WEBSITE_OVERRIDE.get(spec["slug"], SCHOOL_WEBSITE[spec["school"]])


# == Costs ==
_UNDERGRAD_COA = 32446
_AVG_NET_PRICE = 14091
_COST_SRC = "U.S. Dept. of Education — College Scorecard (UW, UNITID 236948)"
_COST_SRC_URL = (
    "https://collegescorecard.ed.gov/school/?236948-University-of-Washington-Seattle-Campus"
)


def _undergrad_cost() -> dict:
    return {
        "total_cost_of_attendance": _UNDERGRAD_COA,
        "avg_net_price": _AVG_NET_PRICE,
        "funded": False,
        "note": (
            "UW's published academic-year cost of attendance is about $32,446 and the average net "
            "price after grant aid is about $14,091 (College Scorecard, UNITID 236948). In-state "
            "students pay public tuition; out-of-state and international tuition is higher, and "
            "tuition varies by program. See UW Student Fiscal Services for current figures."
        ),
        "source": _COST_SRC,
        "source_url": _COST_SRC_URL,
        "year": "2023-24",
    }


def _grad_cost_fallback(spec: dict) -> dict:
    return {
        "note": (
            "Tuition for this graduate/professional program is set by UW and is typically billed "
            "per quarter (and varies by residency, program, and online vs. on-campus delivery), so "
            "a single verified annual figure is not published here. Many doctoral students are "
            "funded through assistantships and fellowships. See the program's tuition page for "
            "current figures."
        ),
        "source": "UW Office of Planning & Budgeting / program tuition page",
        "source_url": _website_for(spec),
    }


# == Admissions requirement sets ==
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission to an on-campus program.",
}
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Application (Coalition Application or UW application)", "required": True},
        {"name": "Personal statement and required short responses", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "$80 application fee (fee waivers available)", "required": True},
        {
            "name": "SAT/ACT scores",
            "required": False,
            "note": "UW is test-blind and does not consider SAT/ACT scores in admission.",
        },
    ],
    "deadlines": [
        {"round": "First-year application", "date": "November 15"},
    ],
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "Duolingo English Test"],
            "required": True,
            "note": "Required for applicants whose native language is not English.",
        },
        "visa": _INTL_VISA,
        "sources": [{"label": "UW Office of Admissions", "url": "https://admit.washington.edu/"}],
    },
    "source": "UW Office of Admissions",
    "source_url": "https://admit.washington.edu/",
}
_REQ_GRAD_GENERIC = {
    "materials": [
        {"name": "UW Graduate School application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Résumé / CV", "required": True},
        {
            "name": "Letters of recommendation",
            "required": True,
            "note": "Most UW graduate programs require three letters; check the program's page.",
        },
        {
            "name": "GRE/GMAT scores",
            "required": False,
            "note": "Test requirements vary by program; many UW graduate programs are test-optional or do not require the GRE/GMAT.",
        },
    ],
    "deadlines": [
        {
            "round": "Autumn admission",
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
            {"label": "UW Graduate School — admissions", "url": "https://grad.uw.edu/admissions/"}
        ],
    },
    "source": "UW Graduate School",
    "source_url": "https://grad.uw.edu/admissions/",
}


def _requirements_for(spec: dict) -> dict:
    if spec["degree_type"] == "bachelors":
        return _REQ_UNDERGRAD
    return _REQ_GRAD_GENERIC


_OUTCOMES_BY_SLUG: dict[str, dict] = {}
_OUTCOMES_OMIT_BY_SLUG: dict[str, list[str]] = {}
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {}
_FACULTY_BY_SLUG: dict[str, dict] = {
    "uw-computer-science-bs": {
        "lead": "The B.S. in Computer Science is taught by the faculty of the Paul G. Allen School of Computer Science & Engineering.",
        "directory_url": "https://www.cs.washington.edu/people/faculty",
    },
    "uw-medicine-prof": {
        "lead": "The M.D. is taught by UW School of Medicine faculty across the basic sciences and the five-state WWAMI clinical network.",
        "directory_url": "https://www.uwmedicine.org/school-of-medicine",
    },
    "uw-nursing-practice-prof": {
        "lead": "The DNP is taught by UW School of Nursing faculty with clinical placements across the UW Medicine system.",
        "directory_url": "https://nursing.uw.edu/faculty/",
    },
    "uw-business-administration-ms": {
        "lead": "The Foster MBA is taught by University of Washington Foster School of Business faculty.",
        "directory_url": "https://foster.uw.edu/faculty-research/directory/",
    },
}

_REVIEWS_BY_SLUG: dict[str, dict] = {
    "uw-computer-science-bs": {
        "summary": "The Paul G. Allen School undergraduate computer science program is one of the strongest in the country (U.S. News ranks UW computer science a tie for #7 nationally). Reviewers cite world-class faculty, deep ties to Seattle's tech industry (Microsoft, Amazon, and a large startup scene), and excellent placement, while noting that direct admission and the upper-division major are highly competitive.",
        "themes": [
            {
                "label": "Top-10 computer science",
                "sentiment": "positive",
                "detail": "U.S. News ranks UW computer science a tie for #7 nationally; the Allen School is a recognized leader in AI, systems, and theory.",
            },
            {
                "label": "Industry adjacency",
                "sentiment": "positive",
                "detail": "Seattle's concentration of Microsoft, Amazon, and startups drives internships, research collaboration, and hiring.",
            },
            {
                "label": "Strong placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into top software, AI, and research roles and competitive graduate programs.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Direct freshman admission and the capacity-constrained major are highly selective; not all applicants are admitted to the major.",
            },
        ],
        "sources": [
            {
                "label": "Paul G. Allen School of Computer Science & Engineering",
                "url": "https://www.cs.washington.edu/",
            },
            {"label": "UW News — U.S. News rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-computer-science-and-engineering-ms": {
        "summary": "The Allen School's graduate computer science programs are top-tier (U.S. News ranks UW computer science a tie for #7), with strengths spanning machine learning, systems, programming languages, HCI, and computational biology. Reviewers praise the research environment and industry partnerships, while noting that doctoral admission is extremely competitive and the professional master's is industry-oriented.",
        "themes": [
            {
                "label": "Elite research program",
                "sentiment": "positive",
                "detail": "UW computer science is a tie for #7 nationally, with leading groups in AI/ML, systems, and theory.",
            },
            {
                "label": "Funding and labs",
                "sentiment": "positive",
                "detail": "Doctoral students are typically funded through research/teaching assistantships with access to strong labs.",
            },
            {
                "label": "Industry partnership",
                "sentiment": "positive",
                "detail": "Close ties to Seattle's tech sector support research and placement.",
            },
            {
                "label": "Highly selective",
                "sentiment": "caution",
                "detail": "Ph.D. admission is very competitive; the professional master's (PMP) is part-time and industry-focused.",
            },
        ],
        "sources": [
            {
                "label": "Paul G. Allen School — graduate programs",
                "url": "https://www.cs.washington.edu/academics/grad",
            },
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-medicine-prof": {
        "summary": "The UW School of Medicine is consistently ranked #1 in the nation for primary care, family medicine, and rural medicine by U.S. News, anchored by the five-state WWAMI program (Washington, Wyoming, Alaska, Montana, Idaho). Reviewers cite outstanding primary-care and community training and research strength, while noting the distributed, travel-intensive WWAMI model and competitive admission. (UW has withdrawn from U.S. News' ranking participation, but its primary-care reputation is long established.)",
        "themes": [
            {
                "label": "#1 primary care",
                "sentiment": "positive",
                "detail": "U.S. News has repeatedly ranked UW School of Medicine #1 for primary care, family medicine, and rural medicine.",
            },
            {
                "label": "WWAMI regional model",
                "sentiment": "positive",
                "detail": "The five-state WWAMI program delivers medical education across WA, WY, AK, MT, and ID with strong community and rural training.",
            },
            {
                "label": "Research strength",
                "sentiment": "positive",
                "detail": "UW Medicine is a major NIH-funded research enterprise with leading clinical and basic science.",
            },
            {
                "label": "Distributed, demanding",
                "sentiment": "caution",
                "detail": "The regional model can involve travel across sites; admission is highly competitive.",
            },
            {
                "label": "Ranking participation",
                "sentiment": "mixed",
                "detail": "UW Medicine has stepped back from U.S. News ranking participation, as several medical schools have.",
            },
        ],
        "sources": [
            {
                "label": "UW School of Medicine",
                "url": "https://www.uwmedicine.org/school-of-medicine",
            },
            {
                "label": "WWAMI Regional Medical Education Program",
                "url": "https://www.uwmedicine.org/education/md-program/wwami",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-nursing-practice-prof": {
        "summary": "The UW School of Nursing is among the very best in the country — U.S. News has ranked its programs #1, and the Doctor of Nursing Practice (DNP) is consistently top-ranked (a tie for #1 among public schools). Reviewers cite outstanding faculty, research, and clinical placements in the Seattle health system, while noting the rigor and clinical-hour demands of the DNP.",
        "themes": [
            {
                "label": "Top-ranked nursing",
                "sentiment": "positive",
                "detail": "UW nursing is repeatedly ranked among the nation's best by U.S. News, with a top-ranked DNP.",
            },
            {
                "label": "Clinical access",
                "sentiment": "positive",
                "detail": "Students train across UW Medicine, Seattle Children's, and regional partners.",
            },
            {
                "label": "Research and faculty",
                "sentiment": "positive",
                "detail": "Strong NIH-funded research and renowned faculty support advanced practice and scholarship.",
            },
            {
                "label": "Rigorous and demanding",
                "sentiment": "caution",
                "detail": "The DNP is intensive, with substantial clinical hours and competitive admission.",
            },
        ],
        "sources": [
            {
                "label": "UW School of Nursing — DNP",
                "url": "https://nursing.uw.edu/program/doctor-of-nursing-practice/",
            },
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-library-and-information-science-ms": {
        "summary": "The UW Information School's Master of Library and Information Science is among the nation's top LIS programs (U.S. News ranks the iSchool's library/information studies a tie for #1), offered on campus and online. Reviewers praise its breadth across data, youth services, archives, and user experience and strong placement, while noting that pay varies by sector.",
        "themes": [
            {
                "label": "#1-ranked LIS",
                "sentiment": "positive",
                "detail": "U.S. News ranks the UW iSchool's library and information studies a tie for #1 nationally.",
            },
            {
                "label": "Flexible delivery",
                "sentiment": "positive",
                "detail": "The MLIS is offered residential and fully online, with concentrations in data, youth, and academic/public libraries.",
            },
            {
                "label": "Strong placement",
                "sentiment": "positive",
                "detail": "Graduates enter libraries, archives, data curation, and information/UX roles.",
            },
            {
                "label": "Sector-dependent pay",
                "sentiment": "caution",
                "detail": "Salaries vary widely between tech/data and public-library sectors.",
            },
        ],
        "sources": [
            {"label": "UW iSchool — MLIS", "url": "https://ischool.uw.edu/programs/mlis"},
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-business-administration-ms": {
        "summary": "The Foster School of Business MBA is a well-regarded program (a U.S. News top-30 full-time MBA) with strong regional pull into Seattle's technology and consulting employers. Reviewers cite excellent tech placement (Amazon, Microsoft, and others), a collaborative culture, and strong value, while noting a smaller class size and a regional (Pacific Northwest) recruiting concentration.",
        "themes": [
            {
                "label": "Top-30 MBA",
                "sentiment": "positive",
                "detail": "Foster's full-time MBA ranks among the nation's best by U.S. News, with standout information-systems and analytics strengths.",
            },
            {
                "label": "Tech placement",
                "sentiment": "positive",
                "detail": "Proximity to Amazon, Microsoft, and a deep tech ecosystem drives strong product, tech, and consulting placement.",
            },
            {
                "label": "Collaborative culture",
                "sentiment": "positive",
                "detail": "Reviewers describe a tight-knit, supportive cohort and accessible faculty.",
            },
            {
                "label": "Regional concentration",
                "sentiment": "caution",
                "detail": "Recruiting skews to the Pacific Northwest; students targeting other regions should network early.",
            },
        ],
        "sources": [
            {
                "label": "Foster School of Business — MBA",
                "url": "https://foster.uw.edu/academics/degree-programs/full-time-mba/",
            },
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-law-prof": {
        "summary": "The UW School of Law is a respected public law school (a U.S. News top-50 program) known for strong value, public-interest and technology-law strengths, and solid placement into the Seattle and Pacific Northwest legal markets. Reviewers cite affordability relative to private peers and a collegial culture, while noting the demands of law school and a regionally focused job market.",
        "themes": [
            {
                "label": "Strong public-law value",
                "sentiment": "positive",
                "detail": "A U.S. News top-50 law school offering strong legal education at public tuition.",
            },
            {
                "label": "Regional placement",
                "sentiment": "positive",
                "detail": "Graduates place well into Seattle and Pacific Northwest firms, government, and tech legal roles.",
            },
            {
                "label": "Specialty strengths",
                "sentiment": "positive",
                "detail": "Notable strengths in intellectual property/technology law, tax, and global/Asian law.",
            },
            {
                "label": "Rigorous, regional market",
                "sentiment": "caution",
                "detail": "The workload is demanding and recruiting concentrates in the Pacific Northwest.",
            },
        ],
        "sources": [
            {"label": "UW School of Law — J.D.", "url": "https://www.law.uw.edu/academics/jd"},
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-pharmacy-prof": {
        "summary": "The UW School of Pharmacy's PharmD is among the nation's top pharmacy programs (a U.S. News top-15, and among the highest-ranked public schools), with strengths in pharmaceutical sciences, pharmacy practice, and health-economics research. Reviewers cite strong clinical training and research, while noting that pharmacy education is lengthy and competitive.",
        "themes": [
            {
                "label": "Top-ranked pharmacy",
                "sentiment": "positive",
                "detail": "U.S. News ranks the UW PharmD among the nation's top pharmacy programs (top-15, leading public schools).",
            },
            {
                "label": "Research and practice",
                "sentiment": "positive",
                "detail": "Strengths span pharmaceutics, medicinal chemistry, and pharmaceutical outcomes/health economics.",
            },
            {
                "label": "Clinical training",
                "sentiment": "positive",
                "detail": "Students train across UW Medicine and regional clinical sites.",
            },
            {
                "label": "Long and competitive",
                "sentiment": "caution",
                "detail": "The PharmD is a multi-year professional program with competitive admission.",
            },
        ],
        "sources": [
            {
                "label": "UW School of Pharmacy — PharmD",
                "url": "https://sop.washington.edu/pharmd/",
            },
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-social-work-ms": {
        "summary": "The UW School of Social Work is among the nation's best (U.S. News ranks its MSW a tie for #7), with strengths in clinical practice, community-centered and anti-racist practice, and behavioral-health research. Reviewers cite strong field placements across the Seattle region and influential faculty, while noting heavy field-hour requirements and the pay realities of the social-work field.",
        "themes": [
            {
                "label": "Top-10 social work",
                "sentiment": "positive",
                "detail": "U.S. News ranks the UW MSW a tie for #7 nationally.",
            },
            {
                "label": "Field placements",
                "sentiment": "positive",
                "detail": "Extensive practicum placements across health, child-welfare, and community organizations.",
            },
            {
                "label": "Research and equity focus",
                "sentiment": "positive",
                "detail": "Strong research and an explicit social-justice and anti-racist practice orientation.",
            },
            {
                "label": "Field hours and pay",
                "sentiment": "caution",
                "detail": "The MSW requires substantial field hours, and social-work salaries vary by sector.",
            },
        ],
        "sources": [
            {
                "label": "UW School of Social Work — MSW",
                "url": "https://socialwork.uw.edu/programs/msw",
            },
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-bioengineering-ms": {
        "summary": "UW Bioengineering (a joint department of the Colleges of Engineering and the School of Medicine) is a top program (U.S. News ranks UW biomedical/bioengineering among the nation's best), with strengths in molecular/cellular engineering, imaging, neural engineering, and regenerative medicine. Reviewers highlight strong faculty and translational research with UW Medicine, while noting the program's rigor and selective admission.",
        "themes": [
            {
                "label": "Top bioengineering",
                "sentiment": "positive",
                "detail": "U.S. News ranks UW bioengineering among the nation's leading programs; it is jointly run with the School of Medicine.",
            },
            {
                "label": "Translational research",
                "sentiment": "positive",
                "detail": "Strong ties to UW Medicine and the Institute for Protein Design support translational work.",
            },
            {
                "label": "Strengths",
                "sentiment": "positive",
                "detail": "Areas include molecular engineering, imaging, neural engineering, and biomaterials.",
            },
            {
                "label": "Rigorous and selective",
                "sentiment": "caution",
                "detail": "The curriculum is demanding and admission is competitive.",
            },
        ],
        "sources": [
            {"label": "UW Department of Bioengineering", "url": "https://bioe.uw.edu/"},
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-aeronautics-and-astronautics-ms": {
        "summary": "UW Aeronautics & Astronautics is a strong, research-active department (William E. Boeing Department) with close ties to the Pacific Northwest aerospace industry, including Boeing and Blue Origin. Reviewers cite strong fluid dynamics, controls, structures, and plasma/space research and excellent regional placement, while noting the field's cyclicality and competitive admission.",
        "themes": [
            {
                "label": "Aerospace strength",
                "sentiment": "positive",
                "detail": "The Boeing Department offers strong research across aerodynamics, controls, structures, and plasma/space.",
            },
            {
                "label": "Industry adjacency",
                "sentiment": "positive",
                "detail": "Proximity to Boeing, Blue Origin, and a deep aerospace cluster drives internships and hiring.",
            },
            {
                "label": "Research breadth",
                "sentiment": "positive",
                "detail": "Active groups span computational fluid dynamics, combustion, and space systems.",
            },
            {
                "label": "Cyclical field",
                "sentiment": "caution",
                "detail": "Aerospace hiring can be cyclical, and graduate admission is competitive.",
            },
        ],
        "sources": [
            {
                "label": "UW William E. Boeing Department of Aeronautics & Astronautics",
                "url": "https://www.aa.washington.edu/",
            },
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-civil-engineering-ms": {
        "summary": "UW Civil & Environmental Engineering is a well-regarded department (a U.S. News top-25 graduate program) with strengths in structural and earthquake engineering, transportation, water/environment, and construction. Reviewers cite strong faculty and regional placement and online options for working professionals, while noting the demanding curriculum.",
        "themes": [
            {
                "label": "Top-25 program",
                "sentiment": "positive",
                "detail": "U.S. News ranks UW civil engineering among the nation's top graduate programs.",
            },
            {
                "label": "Strengths",
                "sentiment": "positive",
                "detail": "Notable in structural/earthquake engineering, transportation, water resources, and construction management.",
            },
            {
                "label": "Flexible options",
                "sentiment": "positive",
                "detail": "Several master's tracks are offered online for working professionals.",
            },
            {
                "label": "Demanding curriculum",
                "sentiment": "caution",
                "detail": "Graduate coursework is rigorous and admission is competitive.",
            },
        ],
        "sources": [
            {
                "label": "UW Civil & Environmental Engineering",
                "url": "https://www.ce.washington.edu/",
            },
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-statistics-bs": {
        "summary": "UW Statistics is a strong, in-demand program with leading research in machine learning, Bayesian methods, and statistical computing, and close ties to the Allen School and eScience Institute. Reviewers cite excellent placement into data-science and analytics roles and rigorous training, while noting that popular courses can be large and competitive.",
        "themes": [
            {
                "label": "Strong, in-demand",
                "sentiment": "positive",
                "detail": "UW statistics has grown with data-science demand and is research-active in ML and Bayesian methods.",
            },
            {
                "label": "Computational focus",
                "sentiment": "positive",
                "detail": "Coursework emphasizes statistical computing, probability, and applied data analysis.",
            },
            {
                "label": "Excellent placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into data-science, analytics, and quantitative roles, including Seattle's tech sector.",
            },
            {
                "label": "Large, competitive courses",
                "sentiment": "caution",
                "detail": "Popular statistics/data courses can be large and entry to some tracks is competitive.",
            },
        ],
        "sources": [
            {"label": "UW Department of Statistics", "url": "https://stat.uw.edu/"},
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-economics-phd": {
        "summary": "UW Economics is a highly regarded research department (U.S. News ranks it among the nation's top economics programs), with strengths in econometrics, microeconomics, and applied fields. Reviewers cite strong faculty and placement into academia, government, and industry, while noting that doctoral admission is very competitive and the program is quantitatively demanding.",
        "themes": [
            {
                "label": "Top economics program",
                "sentiment": "positive",
                "detail": "U.S. News ranks UW economics among the nation's leading departments.",
            },
            {
                "label": "Research strengths",
                "sentiment": "positive",
                "detail": "Notable in econometrics, microeconomics, and applied economics.",
            },
            {
                "label": "Placement",
                "sentiment": "positive",
                "detail": "Graduates place into academia, government, central banks, and industry research.",
            },
            {
                "label": "Quantitative and selective",
                "sentiment": "caution",
                "detail": "The Ph.D. is mathematically demanding and admission is highly competitive.",
            },
        ],
        "sources": [
            {"label": "UW Department of Economics", "url": "https://econ.washington.edu/"},
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "uw-oceanography-bs": {
        "summary": "UW's College of the Environment is a global leader in the earth and ocean sciences (U.S. News ranks UW earth sciences among the nation's best), and oceanography benefits from the research vessel fleet, marine facilities, and proximity to Puget Sound and the Pacific. Reviewers cite outstanding field and research opportunities, while noting that the field is research-oriented and competitive for graduate study.",
        "themes": [
            {
                "label": "Top earth/ocean science",
                "sentiment": "positive",
                "detail": "UW is consistently ranked among the nation's best in the earth and ocean sciences.",
            },
            {
                "label": "Field and fleet access",
                "sentiment": "positive",
                "detail": "Students access research vessels, marine labs, and Puget Sound/Pacific field sites.",
            },
            {
                "label": "Research opportunities",
                "sentiment": "positive",
                "detail": "Strong undergraduate research and ties to NOAA and oceanographic institutions.",
            },
            {
                "label": "Research-oriented",
                "sentiment": "caution",
                "detail": "Career paths often involve graduate study; the field is competitive.",
            },
        ],
        "sources": [
            {
                "label": "UW College of the Environment — Oceanography",
                "url": "https://www.ocean.washington.edu/",
            },
            {"label": "UW News — rankings", "url": "https://www.washington.edu/news/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment/outcomes reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
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
    """Enrich UW to the canonical profile. Flushes; caller commits.

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
    inst.founded_year = 1861
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.washington.edu"
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
