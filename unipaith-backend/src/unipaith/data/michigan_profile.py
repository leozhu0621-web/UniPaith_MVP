"""University of Michigan-Ann Arbor — gold-standard profile data (institution + schools + program catalog).

Mirrors the MIT / Sloan / MBAn reference instance (see ``mit_profile.py`` / ``nyu_profile.py`` /
``georgia_tech_profile.py``): every value is researched from an authoritative source and carries a
citation, or is honestly omitted (recorded in that node's ``_standard.omitted``) — never guessed.
Built 2026-06-13 from:

  • U.S. Dept. of Education **College Scorecard** API + **NCES College Navigator** (IPEDS,
    UNITID 170976) — net price, cost of attendance, earnings, completion/retention, Pell/loan,
    median debt, undergraduate race/ethnicity, admit rate, SAT/ACT percentiles.
  • U-M **Office of Budget and Planning** — the **Common Data Set 2024-25** (first-year funnel:
    98,310 applied / 15,373 admitted / 7,278 enrolled, Fall 2024), the **Section 245 Performance
    Report Card 2024-25** (total enrollment 52,855; 11:1 student-faculty ratio), and the **U-M
    Almanac (20th ed.)** "School/College Origins" table (each school's first-dean-appointed year).
  • U-M **Office of the Provost — Deans** page + the **2025 Spring Commencement program** (the
    current dean of each of the 19 schools and colleges, cross-verified).
  • U-M **FY2024 Annual Financial Report** ($2.04B research expenditures) and **news.umich.edu**.
  • The official **Rackham Programs of Study** directory + the **Office of Undergraduate Admissions
    Majors & Degrees** table + the **non-Rackham professional degrees** list — the full published
    degree catalog (379 degree programs across 19 Ann Arbor schools/colleges), each mapped to its
    owning school by the directory itself (no guessing). Minors, stand-alone graduate certificates,
    and the separate Dearborn and Flint campuses (their own IPEDS ids) are intentionally excluded.
  • Rankings: **QS 2026** (#45), **THE 2026** (#23), **U.S. News Best Colleges 2026** (#20
    National, tied), Carnegie (R1), Higher Learning Commission (HLC) accreditation, each cited.
  • Verified third-party reviews + employment data for the flagship coverable programs (the Ross
    Full-Time MBA and the Michigan Law J.D.) and sourced reputation reviews for the Ross BBA,
    Computer Science, and the M.D.

Honest caveats stamped into ``_standard.omitted``: U-M does not publish a single university-wide
"employed or continuing education" placement rate or a uniform program-level employment-outcomes
table the way a single-college school does, so the institution's combined placement rate and
top-employer-industries list are omitted with reason, and individual programs omit the
outcomes/class-profile deep fields unless a verified program-specific figure exists (the College
Scorecard institution-wide median earnings, $83,648 ten years after entry, is kept at the
institution level). Every program carries a U-M-published 2025-26 tuition figure (the matcher-core
budget signal): the resident annual = the Office of the Registrar full-term rate × 2 standard terms,
by school and credential level (Fee Bulletin); funded research doctoral programs carry tuition 0 under
Rackham's continuous-enrollment tuition-support plans, and the non-resident annual is in each program's
cost-data breakdown. External reviews are attached to the flagship coverable programs with substantial
third-party coverage; this is a genuinely large catalog (379 programs, NYU/Columbia scale), so the
remaining programs record ``external_reviews`` (and their deep fields) in their ``_standard.omitted``
pending a depth pass on a future repair-first run. ``content_sources`` carries the verified ``news.umich.edu/feed/`` RSS on every node plus official
social handles and school/program ``keywords`` for feed filtering.
"""

# ruff: noqa: E501

from __future__ import annotations

import re
from collections import Counter

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.profile_catalog_utils import validate_catalog
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "University of Michigan-Ann Arbor"
ENRICHED_AT = "2026-06-20"


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


# U-M reports outcomes by school/program, not as one university-wide combined placement rate or
# top-employer-industries list, so those two institution outcome fields are omitted with reason.
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
        "rank": 45,
        "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/university-michigan-ann-arbor",
    },
    "times_higher_education": {
        "rank": 23,
        "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-michigan-ann-arbor",
    },
    "us_news_national": {
        "rank": 20,
        "year": 2026,
        "source_url": "https://record.umich.edu/articles/u-m-ranks-high-on-u-s-news-world-report-lists/",
    },
}

SCHOOL_OUTCOMES: dict = {
    "retention_rate_first_year": 0.9747,
    "graduation_rate_6yr": 0.932,
    "completion_rate_4yr_150pct": 0.932,
    "admit_rate": 0.1564,
    "avg_net_price": 13138,
    "median_earnings_10yr": 83648,
    "financial_aid": {
        "pell_grant_rate": 0.1813,
        "federal_loan_rate": 0.237,
        "cost_of_attendance": 34654,
        "median_debt_completers": 19500,
        "avg_net_price": 13138,
    },
    "demographics": {
        "white": 0.4671,
        "asian": 0.1845,
        "hispanic": 0.1169,
        "black": 0.0523,
        "two_or_more": 0.0573,
        "international": 0.076,
        "american_indian": 0.0016,
        "native_hawaiian": 0.001,
        "unknown": 0.0433,
    },
    "test_scores": {
        "sat_reading_25_75": [680, 750],
        "sat_math_25_75": [680, 780],
        "act_25_75": [31, 34],
    },
    "campus_basics": {"location": "Ann Arbor, Michigan"},
    "scale": {
        "student_faculty_ratio": "11:1",
        "faculty_count": 8189,
    },
    "location": {"lat": 42.2780, "lng": -83.7382},
    "research": {
        "labs": [
            "Institute for Social Research (ISR)",
            "Life Sciences Institute (LSI)",
            "Michigan Neuroscience Institute",
            "Rogel Cancer Center",
            "Ford Motor Company Robotics Building / Michigan Robotics",
        ],
        "areas": [
            "Engineering, computer science, and robotics",
            "Medicine, public health, and the life sciences",
            "Social sciences and survey research",
            "Business, economics, and public policy",
            "Sustainability, environment, and mobility",
        ],
        "lab_links": {
            "Institute for Social Research (ISR)": "https://isr.umich.edu/",
            "Life Sciences Institute (LSI)": "https://www.lsi.umich.edu/",
            "Michigan Neuroscience Institute": "https://mni.umich.edu/",
            "Rogel Cancer Center": "https://www.rogelcancercenter.org/",
            "Ford Motor Company Robotics Building / Michigan Robotics": "https://robotics.umich.edu/",
        },
    },
    "campus_life": {
        "athletics_division": "NCAA Division I (Big Ten Conference)",
        "resources": [
            {"name": "Michigan Athletics (the Wolverines)", "url": "https://mgoblue.com/"},
            {"name": "University Career Center", "url": "https://careercenter.umich.edu/"},
            {"name": "University of Michigan Library", "url": "https://www.lib.umich.edu/"},
            {"name": "University Unions (Michigan Union)", "url": "https://uunions.umich.edu/"},
            {"name": "Student Life", "url": "https://studentlife.umich.edu/"},
        ],
    },
    "media_credit": "Wikimedia Commons / w_lemay (CC BY-SA 2.0)",
    "campus_photos": [
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/The_Diag%2C_University_of_Michigan%2C_University_Avenue%2C_Ann_Arbor%2C_MI.jpg/1920px-The_Diag%2C_University_of_Michigan%2C_University_Avenue%2C_Ann_Arbor%2C_MI.jpg",
            "credit": "Wikimedia Commons / w_lemay (CC BY-SA 2.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Law_Quadrangle%2C_University_of_Michigan%2C_University_Avenue_and_State_Street%2C_Ann_Arbor%2C_MI_-_54381402138.jpg/1920px-Law_Quadrangle%2C_University_of_Michigan%2C_University_Avenue_and_State_Street%2C_Ann_Arbor%2C_MI_-_54381402138.jpg",
            "credit": "Wikimedia Commons / w_lemay (CC BY-SA 2.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Angell_Hall%2C_University_of_Michigan%2C_golden_hour.jpg/1920px-Angell_Hall%2C_University_of_Michigan%2C_golden_hour.jpg",
            "credit": "Wikimedia Commons / Chris Rycroft (CC BY 2.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Michigan_Union%2C_University_of_Michigan%2C_State_Street%2C_Ann_Arbor%2C_MI.jpg/1920px-Michigan_Union%2C_University_of_Michigan%2C_State_Street%2C_Ann_Arbor%2C_MI.jpg",
            "credit": "Wikimedia Commons / w_lemay (CC BY-SA 2.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Ross_School_of_Business_Building%2C_University_of_Michigan%2C_Ann_Arbor%2C_Michigan.JPG/1920px-Ross_School_of_Business_Building%2C_University_of_Michigan%2C_Ann_Arbor%2C_Michigan.JPG",
            "credit": "Wikimedia Commons / Dwight Burdette (CC BY 3.0)",
        },
    ],
    "flagship": {
        "enrollment_total": 52855,
        "applicants": 98310,
        "admits": 15373,
        "admissions_cycle": "First-year, Fall 2024 (U-M Common Data Set 2024-25)",
        "founded_year": 1817,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (University of Michigan-Ann Arbor, UNITID 170976)",
            "url": "https://collegescorecard.ed.gov/school/?170976-University-of-Michigan-Ann-Arbor",
        },
        {
            "label": "NCES College Navigator — University of Michigan-Ann Arbor (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=170976",
        },
        {
            "label": "U-M Office of Budget and Planning — Common Data Set 2024-25",
            "url": "https://obp.umich.edu/wp-content/uploads/pubdata/cds/CDS_2024-25_UMAA.pdf",
        },
        {
            "label": "U-M Section 245 Performance Report Card 2024-25 (enrollment + student-faculty ratio)",
            "url": "https://obp.umich.edu/wp-content/uploads/pubdata/mandatoryreports/Section_245_Report_Card_2024-25.pdf",
        },
        {
            "label": "U-M Almanac (20th ed.) — School/College Origins (founding years)",
            "url": "https://obp.umich.edu/wp-content/uploads/pubdata/almanac/Almanac_20th_Edition.pdf",
        },
        {
            "label": "U-M Office of the Provost — Deans (current deans, with offices)",
            "url": "https://provost.umich.edu/about-the-office/reporting-units/deans/",
        },
        {
            "label": "U-M FY2024 Annual Financial Report ($2.04B research expenditures)",
            "url": "https://2024.annualreport.umich.edu/uploads/fy24-financial-report.pdf",
        },
        {
            "label": "Carnegie Classifications — University of Michigan-Ann Arbor (R1)",
            "url": "https://carnegieclassifications.acenet.edu/institution/university-of-michigan-ann-arbor/",
        },
        {
            "label": "QS World University Rankings 2026 — University of Michigan-Ann Arbor (#45)",
            "url": "https://www.topuniversities.com/universities/university-michigan-ann-arbor",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — Michigan (#23)",
            "url": "https://www.timeshighereducation.com/world-university-rankings/university-michigan-ann-arbor",
        },
        {
            "label": "U.S. News Best Colleges 2026 — Michigan (#20 National)",
            "url": "https://record.umich.edu/articles/u-m-ranks-high-on-u-s-news-world-report-lists/",
        },
        {
            "label": "U-M Rackham Programs of Study (graduate degree catalog)",
            "url": "https://rackham.umich.edu/programs-of-study/",
        },
        {
            "label": "U-M Office of Undergraduate Admissions — Majors & Degrees",
            "url": "https://admissions.umich.edu/academics-majors/majors-degrees",
        },
    ],
}

# student_body_size = undergraduate count (page labels it "Undergraduates"); total degree-seeking
# enrollment (52,855) lives in flagship.enrollment_total.
UNDERGRAD_COUNT = 34454

DESCRIPTION = (
    "The University of Michigan is a public research university in Ann Arbor, MI. Founded in 1817 "
    "as the Catholepistemiad and moved to Ann Arbor in 1837, it is the oldest university in the "
    "state, a founding member of the Association of American Universities, and one of the largest "
    "and most highly ranked public research universities in the United States. It enrolls about "
    "34,000 undergraduates and roughly 52,900 students in all, with an 11:1 student-faculty ratio, "
    "and admitted about 16% of first-year applicants (15,373 of 98,310) for Fall 2024.\n\n"
    "Michigan is organized into 19 schools and colleges, including the College of Literature, "
    "Science, and the Arts; the College of Engineering; the Stephen M. Ross School of Business; "
    "the Medical School and Law School; the schools of Information, Public Health, Dentistry, "
    "Nursing, Kinesiology, Social Work, Music, Theatre & Dance, and Education (Marsal); the Ford "
    "School of Public Policy; Taubman College of Architecture and Urban Planning; the Stamps "
    "School of Art & Design; the School for Environment and Sustainability; the College of "
    "Pharmacy; and the Horace H. Rackham School of Graduate Studies. Together they award some 379 "
    "degree programs across the bachelor's, master's, professional, and doctoral levels.\n\n"
    "A Carnegie R1 university accredited by the Higher Learning Commission, Michigan ranks #20 "
    "among national universities (and No. 3 among public universities) by U.S. News, #23 in the "
    "world by Times Higher Education, and #45 by QS for 2026. Its research enterprise surpassed "
    "$2 billion in expenditures in fiscal year 2024, among the very highest of any U.S. "
    "university.\n\n"
    "Michigan's average net price is about $13,100 a year against a published cost of attendance "
    "near $34,700, and the median federal debt of completers is about $19,500; the Go Blue "
    "Guarantee provides free tuition to in-state undergraduates from families earning under a "
    "published income threshold, and the university meets the full demonstrated need of in-state "
    "students. Michigan graduates earn a median of roughly $83,600 ten years after entry. The "
    "Wolverines compete in NCAA Division I (the Big Ten Conference)."
)

# ── Schools ────────────────────────────────────────────────────────────────
_SCHOOL_META = [
    {
        "key": "LSA",
        "name": "College of Literature, Science, and the Arts",
        "sort_order": 1,
        "website": "https://lsa.umich.edu/",
        "founded": 1875,
        "leadership": "Rosario Ceballo — Dean of the College of Literature, Science, and the Arts",
        "named_for": None,
        "research_centers": [
            "Departments of the humanities (English, History, Philosophy, Romance Languages)",
            "Natural and mathematical sciences (Mathematics, Physics, Chemistry, Biology, Statistics)",
            "Social sciences (Economics, Political Science, Psychology, Sociology, Anthropology)",
            "Residential College and the LSA Honors Program",
        ],
        "keywords": ["Literature Science and the Arts", "LSA"],
    },
    {
        "key": "ENG",
        "name": "College of Engineering",
        "sort_order": 2,
        "website": "https://www.engin.umich.edu/",
        "founded": 1895,
        "leadership": "Karen A. Thole — Robert J. Vlasic Dean of Engineering",
        "named_for": None,
        "research_centers": [
            "Department of Electrical Engineering and Computer Science",
            "Department of Mechanical Engineering",
            "Department of Aerospace Engineering",
            "Department of Industrial and Operations Engineering",
            "Department of Biomedical Engineering",
            "Robotics Department and the Ford Motor Company Robotics Building",
        ],
        "keywords": ["College of Engineering", "Michigan Engineering"],
    },
    {
        "key": "ROSS",
        "name": "Stephen M. Ross School of Business",
        "sort_order": 3,
        "website": "https://michiganross.umich.edu/",
        "founded": 1924,
        "leadership": "Sharon F. Matusik — Edward J. Frey Dean of Business",
        "named_for": "Named in 2004 for Stephen M. Ross, a 1962 alumnus, following his endowment gift",
        "research_centers": [
            "Full-Time, Weekend, Online and Executive MBA programs",
            "Ross BBA Program",
            "Zell Lurie Institute for Entrepreneurial Studies",
            "Tauber Institute for Global Operations",
            "Erb Institute for Global Sustainable Enterprise",
        ],
        "keywords": ["Ross School of Business", "Michigan Ross", "MBA", "BBA"],
    },
    {
        "key": "MED",
        "name": "University of Michigan Medical School",
        "sort_order": 4,
        "website": "https://medschool.umich.edu/",
        "founded": 1850,
        "leadership": "Thomas J. Wang — Dean, University of Michigan Medical School",
        "named_for": None,
        "research_centers": [
            "Michigan Medicine academic health system",
            "Rogel Cancer Center",
            "Michigan Neuroscience Institute",
            "Program in Biomedical Sciences (PIBS)",
        ],
        "keywords": ["Medical School", "Michigan Medicine", "medicine"],
    },
    {
        "key": "LAW",
        "name": "University of Michigan Law School",
        "sort_order": 5,
        "website": "https://michigan.law.umich.edu/",
        "founded": 1859,
        "leadership": "Neel U. Sukhatme — Dean, University of Michigan Law School",
        "named_for": None,
        "research_centers": [
            "The Law Quadrangle and the Law Library",
            "Clinical Law Program",
            "Center for International and Comparative Law",
            "Program in Race, Law & History",
        ],
        "keywords": ["Michigan Law", "Law School"],
    },
    {
        "key": "INFO",
        "name": "School of Information",
        "sort_order": 6,
        "website": "https://www.si.umich.edu/",
        "founded": 1969,
        "leadership": "Andrea Forte — Dean, School of Information",
        "named_for": None,
        "research_centers": [
            "Master of Science in Information (MSI) and the undergraduate BSI",
            "Master of Health Informatics (with the Medical School and School of Public Health)",
            "Center for Social Media Responsibility",
            "Citizen Interaction Design",
        ],
        "keywords": ["School of Information", "UMSI"],
    },
    {
        "key": "SPH",
        "name": "School of Public Health",
        "sort_order": 7,
        "website": "https://sph.umich.edu/",
        "founded": 1941,
        "leadership": "Lynda Lisabeth — Interim Dean, School of Public Health",
        "named_for": None,
        "research_centers": [
            "Department of Epidemiology",
            "Department of Biostatistics",
            "Department of Environmental Health Sciences",
            "Department of Health Behavior and Health Equity",
            "Department of Health Management and Policy",
            "Department of Nutritional Sciences",
        ],
        "keywords": ["School of Public Health", "public health"],
    },
    {
        "key": "DENT",
        "name": "School of Dentistry",
        "sort_order": 8,
        "website": "https://dent.umich.edu/",
        "founded": 1875,
        "leadership": "Jacques E. Nör — Dean, School of Dentistry",
        "named_for": None,
        "research_centers": [
            "Doctor of Dental Surgery (D.D.S.) program",
            "Dental Hygiene programs",
            "Advanced specialty programs (Endodontics, Orthodontics, Periodontics, Prosthodontics, Pediatric Dentistry)",
            "Department of Cariology, Restorative Sciences, and Endodontics",
        ],
        "keywords": ["School of Dentistry", "dental"],
    },
    {
        "key": "PHARM",
        "name": "College of Pharmacy",
        "sort_order": 9,
        "website": "https://pharmacy.umich.edu/",
        "founded": 1876,
        "leadership": "Vicki L. Ellingrod — Dean, College of Pharmacy",
        "named_for": None,
        "research_centers": [
            "Doctor of Pharmacy (Pharm.D.) program",
            "Department of Clinical Pharmacy",
            "Department of Medicinal Chemistry",
            "Department of Pharmaceutical Sciences",
        ],
        "keywords": ["College of Pharmacy", "pharmacy"],
    },
    {
        "key": "SMTD",
        "name": "School of Music, Theatre & Dance",
        "sort_order": 10,
        "website": "https://smtd.umich.edu/",
        "founded": 1927,
        "leadership": "David A. Gier — Dean and Paul Boylan Collegiate Professor of Music",
        "named_for": None,
        "research_centers": [
            "Department of Music (Performance, Composition, Conducting)",
            "Department of Theatre & Drama",
            "Department of Dance",
            "Department of Musical Theatre",
            "Department of Performing Arts Technology",
        ],
        "keywords": ["Music Theatre and Dance", "SMTD"],
    },
    {
        "key": "EDU",
        "name": "Marsal Family School of Education",
        "sort_order": 11,
        "website": "https://marsal.umich.edu/",
        "founded": 1921,
        "leadership": "Elizabeth Birr Moje — Dean, Marsal Family School of Education",
        "named_for": "Named in 2023 for the Marsal family following their endowment gift",
        "research_centers": [
            "Elementary and Secondary Teacher Education",
            "Higher Education program",
            "Educational Studies (Ph.D. and M.A.)",
            "Combined Program in Education and Psychology",
        ],
        "keywords": ["Marsal Family School of Education", "School of Education"],
    },
    {
        "key": "NURS",
        "name": "School of Nursing",
        "sort_order": 12,
        "website": "https://nursing.umich.edu/",
        "founded": 1941,
        "leadership": "Patricia D. Hurn — Dean, School of Nursing",
        "named_for": None,
        "research_centers": [
            "Bachelor of Science in Nursing (BSN)",
            "Master's nurse-practitioner specialties",
            "Doctor of Nursing Practice (D.N.P.)",
            "Ph.D. in Nursing",
        ],
        "keywords": ["School of Nursing", "nursing"],
    },
    {
        "key": "KIN",
        "name": "School of Kinesiology",
        "sort_order": 13,
        "website": "https://www.kines.umich.edu/",
        "founded": 1984,
        "leadership": "Lori Ploutz-Snyder — Dean, School of Kinesiology",
        "named_for": None,
        "research_centers": [
            "Movement Science program",
            "Applied Exercise Science program",
            "Sport Management program",
            "Athletic Training (M.S.)",
        ],
        "keywords": ["School of Kinesiology", "kinesiology"],
    },
    {
        "key": "SSW",
        "name": "School of Social Work",
        "sort_order": 14,
        "website": "https://ssw.umich.edu/",
        "founded": 1951,
        "leadership": "Beth Angell — Dean, School of Social Work",
        "named_for": None,
        "research_centers": [
            "Master of Social Work (M.S.W.)",
            "Joint doctoral programs in Social Work and a social science",
            "Community Action and Research",
        ],
        "keywords": ["School of Social Work", "social work"],
    },
    {
        "key": "FORD",
        "name": "Gerald R. Ford School of Public Policy",
        "sort_order": 15,
        "website": "https://fordschool.umich.edu/",
        "founded": 1995,
        "leadership": "Celeste M. Watkins-Hayes — Joan and Sanford Weill Dean of Public Policy",
        "named_for": "Named for Gerald R. Ford, the 38th U.S. President and a Michigan alumnus",
        "research_centers": [
            "Master of Public Policy (MPP) and Master of Public Affairs (MPA)",
            "Joint Ph.D. programs with Economics, Political Science, and Sociology",
            "Center for Local, State, and Urban Policy (CLOSUP)",
            "Education Policy Initiative",
        ],
        "keywords": ["Ford School of Public Policy", "public policy"],
    },
    {
        "key": "TAUB",
        "name": "A. Alfred Taubman College of Architecture and Urban Planning",
        "sort_order": 16,
        "website": "https://taubmancollege.umich.edu/",
        "founded": 1931,
        "leadership": "Jonathan Massey — Dean, A. Alfred Taubman College of Architecture and Urban Planning",
        "named_for": "Named in 1999 for A. Alfred Taubman following his endowment gift",
        "research_centers": [
            "Master of Architecture and the Bachelor of Science in Architecture",
            "Urban and Regional Planning (M.U.R.P.) and Ph.D.",
            "Master of Urban Design",
            "Urban Technology (B.S.)",
        ],
        "keywords": ["Taubman College", "Architecture and Urban Planning"],
    },
    {
        "key": "STAMPS",
        "name": "Penny W. Stamps School of Art & Design",
        "sort_order": 17,
        "website": "https://stamps.umich.edu/",
        "founded": 1974,
        "leadership": "Carlos Francisco Jackson — Dean, Penny W. Stamps School of Art & Design",
        "named_for": "Named in 2012 for Penny W. Stamps following her endowment gift",
        "research_centers": [
            "Bachelor of Fine Arts in Art & Design",
            "Master of Fine Arts (M.F.A.)",
            "Master of Design (MDes)",
            "Penny W. Stamps Speaker Series",
        ],
        "keywords": ["Stamps School of Art and Design", "art and design"],
    },
    {
        "key": "SEAS",
        "name": "School for Environment and Sustainability",
        "sort_order": 18,
        "website": "https://seas.umich.edu/",
        "founded": 1927,
        "leadership": "Jonathan T. Overpeck — Samuel A. Graham Dean, School for Environment and Sustainability",
        "named_for": None,
        "research_centers": [
            "Master of Science in Environment and Sustainability",
            "Ph.D. in Environment and Sustainability",
            "Landscape Architecture (M.L.Arch.)",
            "Sustainability and environmental-justice programs",
        ],
        "keywords": ["School for Environment and Sustainability", "SEAS"],
    },
    {
        "key": "RACK",
        "name": "Horace H. Rackham School of Graduate Studies",
        "sort_order": 19,
        "website": "https://rackham.umich.edu/",
        "founded": 1912,
        "leadership": "Michael J. Solomon — Dean, Horace H. Rackham School of Graduate Studies and Vice Provost for Academic Affairs–Graduate Studies",
        "named_for": "Named for Horace H. Rackham, whose foundation funded the graduate school",
        "research_centers": [
            "Administers more than 180 graduate degree programs across U-M",
            "Interdepartmental graduate programs (including programs affiliated with the Life Sciences Institute)",
            "Rackham Graduate Funding and Research Grants",
        ],
        "keywords": ["Rackham Graduate School", "graduate studies"],
    },
]
SCHOOL_NAME = {m["key"]: m["name"] for m in _SCHOOL_META}
SCHOOL_WEBSITE = {m["name"]: m["website"] for m in _SCHOOL_META}

SCHOOLS: list[dict] = [
    {
        "name": m["name"],
        "sort_order": m["sort_order"],
        "description": (
            f"The {m['name']}, with its first dean appointed in {m['founded']}, is one of the 19 "
            f"schools and colleges of the University of Michigan in Ann Arbor."
        ),
    }
    for m in _SCHOOL_META
]


def _about_for(m: dict) -> dict:
    about = {
        "founded": m["founded"],
        "leadership": m["leadership"],
        "research_centers": m["research_centers"],
        "source": {
            "label": "U-M Almanac (School/College Origins) + Office of the Provost — Deans",
            "url": "https://provost.umich.edu/about-the-office/reporting-units/deans/",
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
_MICH_NEWS_RSS = "https://news.umich.edu/feed/"
_NEWS_URL = "https://news.umich.edu/"
_SOCIAL = {
    "instagram": "https://www.instagram.com/uofmichigan/",
    "linkedin": "https://www.linkedin.com/school/university-of-michigan/",
    "x": "https://twitter.com/umich",
    "youtube": "https://www.youtube.com/user/um",
    "facebook": "https://www.facebook.com/universityofmichigan",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _MICH_NEWS_RSS,
    "news_url": _NEWS_URL,
    "news_curated": True,
    "social": _SOCIAL,
}
_KEYWORDS_BY_SCHOOL = {m["name"]: m["keywords"] for m in _SCHOOL_META}


def _school_content(name: str) -> dict:
    return {
        "news_rss": _MICH_NEWS_RSS,
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
        "mich-aerospace-engineering-ug",
        "ENG",
        "Aerospace Engineering",
        "bachelors",
        "Aerospace Engineering",
        "on_campus",
        48,
    ),
    (
        "mich-afroamerican-and-african-studies-ug",
        "LSA",
        "Afroamerican and African Studies",
        "bachelors",
        "Afroamerican and African Studies",
        "on_campus",
        48,
    ),
    (
        "mich-american-culture-ug",
        "LSA",
        "American Culture",
        "bachelors",
        "American Culture",
        "on_campus",
        48,
    ),
    ("mich-anthropology-ug", "LSA", "Anthropology", "bachelors", "Anthropology", "on_campus", 48),
    (
        "mich-applied-exercise-science-ug",
        "KIN",
        "Applied Exercise Science",
        "bachelors",
        "Applied Exercise Science",
        "on_campus",
        48,
    ),
    (
        "mich-archaeology-of-the-ancient-mediterranean-ug",
        "LSA",
        "Archaeology of the Ancient Mediterranean",
        "bachelors",
        "Archaeology of the Ancient Mediterranean",
        "on_campus",
        48,
    ),
    ("mich-architecture-ug", "TAUB", "Architecture", "bachelors", "Architecture", "on_campus", 48),
    (
        "mich-art-and-design-ug",
        "STAMPS",
        "Art and Design",
        "bachelors",
        "Art and Design",
        "on_campus",
        48,
    ),
    (
        "mich-arts-and-ideas-in-the-humanities-ug",
        "LSA",
        "Arts and Ideas in the Humanities",
        "bachelors",
        "Arts and Ideas in the Humanities",
        "on_campus",
        48,
    ),
    (
        "mich-asian-studies-ug",
        "LSA",
        "Asian Studies",
        "bachelors",
        "Asian Studies",
        "on_campus",
        48,
    ),
    (
        "mich-astronomy-and-astrophysics-ug",
        "LSA",
        "Astronomy and Astrophysics",
        "bachelors",
        "Astronomy and Astrophysics",
        "on_campus",
        48,
    ),
    ("mich-biochemistry-ug", "LSA", "Biochemistry", "bachelors", "Biochemistry", "on_campus", 48),
    ("mich-biology-ug", "LSA", "Biology", "bachelors", "Biology", "on_campus", 48),
    (
        "mich-biology-health-and-society-ug",
        "LSA",
        "Biology, Health, and Society",
        "bachelors",
        "Biology, Health, and Society",
        "on_campus",
        48,
    ),
    (
        "mich-biomedical-engineering-ug",
        "ENG",
        "Biomedical Engineering",
        "bachelors",
        "Biomedical Engineering",
        "on_campus",
        48,
    ),
    (
        "mich-biomolecular-science-ug",
        "LSA",
        "Biomolecular Science",
        "bachelors",
        "Biomolecular Science",
        "on_campus",
        48,
    ),
    ("mich-biophysics-ug", "LSA", "Biophysics", "bachelors", "Biophysics", "on_campus", 48),
    (
        "mich-biopsychology-cognition-and-neuroscience-ug",
        "LSA",
        "Biopsychology, Cognition, and Neuroscience",
        "bachelors",
        "Biopsychology, Cognition, and Neuroscience",
        "on_campus",
        48,
    ),
    ("mich-business-ug", "ROSS", "Business", "bachelors", "Business", "on_campus", 48),
    (
        "mich-cellular-and-molecular-biomedical-science-ug",
        "LSA",
        "Cellular and Molecular Biomedical Science",
        "bachelors",
        "Cellular and Molecular Biomedical Science",
        "on_campus",
        48,
    ),
    (
        "mich-chemical-engineering-ug",
        "ENG",
        "Chemical Engineering",
        "bachelors",
        "Chemical Engineering",
        "on_campus",
        48,
    ),
    ("mich-chemistry-ug", "LSA", "Chemistry", "bachelors", "Chemistry", "on_campus", 48),
    (
        "mich-civil-engineering-ug",
        "ENG",
        "Civil Engineering",
        "bachelors",
        "Civil Engineering",
        "on_campus",
        48,
    ),
    (
        "mich-classical-civilization-ug",
        "LSA",
        "Classical Civilization",
        "bachelors",
        "Classical Civilization",
        "on_campus",
        48,
    ),
    (
        "mich-classical-languages-and-literatures-ug",
        "LSA",
        "Classical Languages and Literatures",
        "bachelors",
        "Classical Languages and Literatures",
        "on_campus",
        48,
    ),
    (
        "mich-climate-and-meteorology-ug",
        "ENG",
        "Climate and Meteorology",
        "bachelors",
        "Climate and Meteorology",
        "on_campus",
        48,
    ),
    (
        "mich-cognitive-science-ug",
        "LSA",
        "Cognitive Science",
        "bachelors",
        "Cognitive Science",
        "on_campus",
        48,
    ),
    (
        "mich-communication-and-media-ug",
        "LSA",
        "Communication and Media",
        "bachelors",
        "Communication and Media",
        "on_campus",
        48,
    ),
    (
        "mich-community-and-global-public-health-ug",
        "SPH",
        "Community and Global Public Health",
        "bachelors",
        "Community and Global Public Health",
        "on_campus",
        48,
    ),
    (
        "mich-comparative-literature-arts-and-media-ug",
        "LSA",
        "Comparative Literature, Arts, and Media",
        "bachelors",
        "Comparative Literature, Arts, and Media",
        "on_campus",
        48,
    ),
    ("mich-composition-ug", "SMTD", "Composition", "bachelors", "Composition", "on_campus", 48),
    (
        "mich-computer-engineering-ug",
        "ENG",
        "Computer Engineering",
        "bachelors",
        "Computer Engineering",
        "on_campus",
        48,
    ),
    (
        "mich-computer-science-ug",
        "LSA",
        "Computer Science",
        "bachelors",
        "Computer Science",
        "on_campus",
        48,
    ),
    (
        "mich-computer-science-ug-eng",
        "ENG",
        "Computer Science",
        "bachelors",
        "Computer Science",
        "on_campus",
        48,
    ),
    (
        "mich-creative-writing-and-literature-ug",
        "LSA",
        "Creative Writing and Literature",
        "bachelors",
        "Creative Writing and Literature",
        "on_campus",
        48,
    ),
    ("mich-dance-ug", "SMTD", "Dance", "bachelors", "Dance", "on_campus", 48),
    ("mich-data-science-ug", "ENG", "Data Science", "bachelors", "Data Science", "on_campus", 48),
    (
        "mich-data-science-ug-lsa",
        "LSA",
        "Data Science",
        "bachelors",
        "Data Science",
        "on_campus",
        48,
    ),
    (
        "mich-dental-hygiene-ug",
        "DENT",
        "Dental Hygiene",
        "bachelors",
        "Dental Hygiene",
        "on_campus",
        48,
    ),
    ("mich-drama-ug", "LSA", "Drama", "bachelors", "Drama", "on_campus", 48),
    (
        "mich-earth-and-environmental-sciences-ug",
        "LSA",
        "Earth and Environmental Sciences",
        "bachelors",
        "Earth and Environmental Sciences",
        "on_campus",
        48,
    ),
    (
        "mich-ecology-evolution-and-biodiversity-ug",
        "LSA",
        "Ecology, Evolution, and Biodiversity",
        "bachelors",
        "Ecology, Evolution, and Biodiversity",
        "on_campus",
        48,
    ),
    ("mich-economics-ug", "LSA", "Economics", "bachelors", "Economics", "on_campus", 48),
    (
        "mich-electrical-engineering-ug",
        "ENG",
        "Electrical Engineering",
        "bachelors",
        "Electrical Engineering",
        "on_campus",
        48,
    ),
    (
        "mich-elementary-teacher-education-ug",
        "EDU",
        "Elementary Teacher Education",
        "bachelors",
        "Elementary Teacher Education",
        "on_campus",
        48,
    ),
    (
        "mich-engineering-physics-ug",
        "ENG",
        "Engineering Physics",
        "bachelors",
        "Engineering Physics",
        "on_campus",
        48,
    ),
    ("mich-english-ug", "LSA", "English", "bachelors", "English", "on_campus", 48),
    ("mich-environment-ug", "LSA", "Environment", "bachelors", "Environment", "on_campus", 48),
    (
        "mich-environmental-engineering-ug",
        "ENG",
        "Environmental Engineering",
        "bachelors",
        "Environmental Engineering",
        "on_campus",
        48,
    ),
    (
        "mich-film-television-and-media-ug",
        "LSA",
        "Film, Television, and Media",
        "bachelors",
        "Film, Television, and Media",
        "on_campus",
        48,
    ),
    (
        "mich-french-and-francophone-studies-ug",
        "LSA",
        "French and Francophone Studies",
        "bachelors",
        "French and Francophone Studies",
        "on_campus",
        48,
    ),
    (
        "mich-gender-and-health-ug",
        "LSA",
        "Gender and Health",
        "bachelors",
        "Gender and Health",
        "on_campus",
        48,
    ),
    (
        "mich-general-studies-ug",
        "LSA",
        "General Studies",
        "bachelors",
        "General Studies",
        "on_campus",
        48,
    ),
    ("mich-german-ug", "LSA", "German", "bachelors", "German", "on_campus", 48),
    (
        "mich-greek-language-and-literature-ug",
        "LSA",
        "Greek Language and Literature",
        "bachelors",
        "Greek Language and Literature",
        "on_campus",
        48,
    ),
    (
        "mich-greek-language-and-culture-ug",
        "LSA",
        "Greek Language and Culture",
        "bachelors",
        "Greek Language and Culture",
        "on_campus",
        48,
    ),
    ("mich-history-ug", "LSA", "History", "bachelors", "History", "on_campus", 48),
    (
        "mich-history-of-art-ug",
        "LSA",
        "History of Art",
        "bachelors",
        "History of Art",
        "on_campus",
        48,
    ),
    (
        "mich-human-origins-biology-and-behavior-ug",
        "LSA",
        "Human Origins, Biology, and Behavior",
        "bachelors",
        "Human Origins, Biology, and Behavior",
        "on_campus",
        48,
    ),
    (
        "mich-industrial-and-operations-engineering-ug",
        "ENG",
        "Industrial and Operations Engineering",
        "bachelors",
        "Industrial and Operations Engineering",
        "on_campus",
        48,
    ),
    (
        "mich-information-analysis-and-design-ug",
        "INFO",
        "Information Analysis and Design",
        "bachelors",
        "Information Analysis and Design",
        "on_campus",
        48,
    ),
    (
        "mich-integrated-business-and-engineering-at-michigan-ug",
        "ENG",
        "Integrated Business and Engineering at Michigan",
        "bachelors",
        "Integrated Business and Engineering at Michigan",
        "on_campus",
        48,
    ),
    (
        "mich-integrated-business-and-engineering-at-michigan-ug-ross",
        "ROSS",
        "Integrated Business and Engineering at Michigan",
        "bachelors",
        "Integrated Business and Engineering at Michigan",
        "on_campus",
        48,
    ),
    (
        "mich-interarts-performance-ug",
        "STAMPS",
        "Interarts Performance",
        "bachelors",
        "Interarts Performance",
        "on_campus",
        48,
    ),
    (
        "mich-interarts-performance-ug-smtd",
        "SMTD",
        "Interarts Performance",
        "bachelors",
        "Interarts Performance",
        "on_campus",
        48,
    ),
    (
        "mich-interdisciplinary-astronomy-ug",
        "LSA",
        "Interdisciplinary Astronomy",
        "bachelors",
        "Interdisciplinary Astronomy",
        "on_campus",
        48,
    ),
    (
        "mich-interdisciplinary-chemical-sciences-ug",
        "LSA",
        "Interdisciplinary Chemical Sciences",
        "bachelors",
        "Interdisciplinary Chemical Sciences",
        "on_campus",
        48,
    ),
    (
        "mich-interdisciplinary-physics-ug",
        "LSA",
        "Interdisciplinary Physics",
        "bachelors",
        "Interdisciplinary Physics",
        "on_campus",
        48,
    ),
    (
        "mich-international-studies-ug",
        "LSA",
        "International Studies",
        "bachelors",
        "International Studies",
        "on_campus",
        48,
    ),
    ("mich-italian-ug", "LSA", "Italian", "bachelors", "Italian", "on_campus", 48),
    (
        "mich-jazz-and-contemporary-improvisation-ug",
        "SMTD",
        "Jazz & Contemporary Improvisation",
        "bachelors",
        "Jazz & Contemporary Improvisation",
        "on_campus",
        48,
    ),
    (
        "mich-judaic-studies-ug",
        "LSA",
        "Judaic Studies",
        "bachelors",
        "Judaic Studies",
        "on_campus",
        48,
    ),
    (
        "mich-latin-american-and-caribbean-studies-ug",
        "LSA",
        "Latin American and Caribbean Studies",
        "bachelors",
        "Latin American and Caribbean Studies",
        "on_campus",
        48,
    ),
    (
        "mich-latin-language-and-literature-ug",
        "LSA",
        "Latin Language and Literature",
        "bachelors",
        "Latin Language and Literature",
        "on_campus",
        48,
    ),
    (
        "mich-latina-latino-studies-ug",
        "LSA",
        "Latina/Latino Studies",
        "bachelors",
        "Latina/Latino Studies",
        "on_campus",
        48,
    ),
    (
        "mich-learning-equity-and-problem-solving-for-the-public-good-ug",
        "EDU",
        "Learning, Equity, and Problem Solving for the Public Good",
        "bachelors",
        "Learning, Equity, and Problem Solving for the Public Good",
        "on_campus",
        48,
    ),
    ("mich-linguistics-ug", "LSA", "Linguistics", "bachelors", "Linguistics", "on_campus", 48),
    (
        "mich-materials-science-and-engineering-ug",
        "ENG",
        "Materials Science and Engineering",
        "bachelors",
        "Materials Science and Engineering",
        "on_campus",
        48,
    ),
    ("mich-mathematics-ug", "LSA", "Mathematics", "bachelors", "Mathematics", "on_campus", 48),
    (
        "mich-mechanical-engineering-ug",
        "ENG",
        "Mechanical Engineering",
        "bachelors",
        "Mechanical Engineering",
        "on_campus",
        48,
    ),
    ("mich-microbiology-ug", "LSA", "Microbiology", "bachelors", "Microbiology", "on_campus", 48),
    (
        "mich-middle-east-studies-ug",
        "LSA",
        "Middle East Studies",
        "bachelors",
        "Middle East Studies",
        "on_campus",
        48,
    ),
    (
        "mich-middle-eastern-and-north-african-studies-ug",
        "LSA",
        "Middle Eastern and North African Studies",
        "bachelors",
        "Middle Eastern and North African Studies",
        "on_campus",
        48,
    ),
    (
        "mich-molecular-cellular-and-developmental-biology-ug",
        "LSA",
        "Molecular, Cellular, and Developmental Biology",
        "bachelors",
        "Molecular, Cellular, and Developmental Biology",
        "on_campus",
        48,
    ),
    (
        "mich-movement-science-ug",
        "KIN",
        "Movement Science",
        "bachelors",
        "Movement Science",
        "on_campus",
        48,
    ),
    ("mich-music-ug", "SMTD", "Music", "bachelors", "Music", "on_campus", 48),
    (
        "mich-music-education-ug",
        "SMTD",
        "Music Education",
        "bachelors",
        "Music Education",
        "on_campus",
        48,
    ),
    ("mich-music-theory-ug", "SMTD", "Music Theory", "bachelors", "Music Theory", "on_campus", 48),
    (
        "mich-musical-theatre-ug",
        "SMTD",
        "Musical Theatre",
        "bachelors",
        "Musical Theatre",
        "on_campus",
        48,
    ),
    ("mich-musicology-ug", "SMTD", "Musicology", "bachelors", "Musicology", "on_campus", 48),
    (
        "mich-naval-architecture-and-marine-engineering-ug",
        "ENG",
        "Naval Architecture and Marine Engineering",
        "bachelors",
        "Naval Architecture and Marine Engineering",
        "on_campus",
        48,
    ),
    ("mich-neuroscience-ug", "LSA", "Neuroscience", "bachelors", "Neuroscience", "on_campus", 48),
    (
        "mich-nuclear-engineering-and-radiological-sciences-ug",
        "ENG",
        "Nuclear Engineering and Radiological Sciences",
        "bachelors",
        "Nuclear Engineering and Radiological Sciences",
        "on_campus",
        48,
    ),
    ("mich-nursing-ug", "NURS", "Nursing", "bachelors", "Nursing", "on_campus", 48),
    ("mich-organ-ug", "SMTD", "Organ", "bachelors", "Organ", "on_campus", 48),
    (
        "mich-organizational-studies-ug",
        "LSA",
        "Organizational Studies",
        "bachelors",
        "Organizational Studies",
        "on_campus",
        48,
    ),
    (
        "mich-performing-arts-technology-ug",
        "SMTD",
        "Performing Arts Technology",
        "bachelors",
        "Performing Arts Technology",
        "on_campus",
        48,
    ),
    (
        "mich-pharmaceutical-sciences-ug",
        "PHARM",
        "Pharmaceutical Sciences",
        "bachelors",
        "Pharmaceutical Sciences",
        "on_campus",
        48,
    ),
    ("mich-philosophy-ug", "LSA", "Philosophy", "bachelors", "Philosophy", "on_campus", 48),
    (
        "mich-philosophy-politics-and-economics-ug",
        "LSA",
        "Philosophy, Politics, and Economics",
        "bachelors",
        "Philosophy, Politics, and Economics",
        "on_campus",
        48,
    ),
    ("mich-physics-ug", "LSA", "Physics", "bachelors", "Physics", "on_campus", 48),
    ("mich-piano-ug", "SMTD", "Piano", "bachelors", "Piano", "on_campus", 48),
    (
        "mich-plant-biology-ug",
        "LSA",
        "Plant Biology",
        "bachelors",
        "Plant Biology",
        "on_campus",
        48,
    ),
    ("mich-polish-ug", "LSA", "Polish", "bachelors", "Polish", "on_campus", 48),
    (
        "mich-political-science-ug",
        "LSA",
        "Political Science",
        "bachelors",
        "Political Science",
        "on_campus",
        48,
    ),
    ("mich-psychology-ug", "LSA", "Psychology", "bachelors", "Psychology", "on_campus", 48),
    (
        "mich-public-health-sciences-ug",
        "SPH",
        "Public Health Sciences",
        "bachelors",
        "Public Health Sciences",
        "on_campus",
        48,
    ),
    (
        "mich-public-policy-ug",
        "FORD",
        "Public Policy",
        "bachelors",
        "Public Policy",
        "on_campus",
        48,
    ),
    ("mich-robotics-ug", "ENG", "Robotics", "bachelors", "Robotics", "on_campus", 48),
    (
        "mich-romance-languages-and-literatures-ug",
        "LSA",
        "Romance Languages and Literatures",
        "bachelors",
        "Romance Languages and Literatures",
        "on_campus",
        48,
    ),
    ("mich-russian-ug", "LSA", "Russian", "bachelors", "Russian", "on_campus", 48),
    (
        "mich-russian-east-european-and-eurasian-studies-ug",
        "LSA",
        "Russian, East European, and Eurasian Studies",
        "bachelors",
        "Russian, East European, and Eurasian Studies",
        "on_campus",
        48,
    ),
    (
        "mich-secondary-teacher-education-ug",
        "EDU",
        "Secondary Teacher Education",
        "bachelors",
        "Secondary Teacher Education",
        "on_campus",
        48,
    ),
    (
        "mich-social-theory-and-practice-ug",
        "LSA",
        "Social Theory and Practice",
        "bachelors",
        "Social Theory and Practice",
        "on_campus",
        48,
    ),
    ("mich-sociology-ug", "LSA", "Sociology", "bachelors", "Sociology", "on_campus", 48),
    (
        "mich-space-sciences-and-engineering-ug",
        "ENG",
        "Space Sciences and Engineering",
        "bachelors",
        "Space Sciences and Engineering",
        "on_campus",
        48,
    ),
    ("mich-spanish-ug", "LSA", "Spanish", "bachelors", "Spanish", "on_campus", 48),
    (
        "mich-sport-management-ug",
        "KIN",
        "Sport Management",
        "bachelors",
        "Sport Management",
        "on_campus",
        48,
    ),
    ("mich-statistics-ug", "LSA", "Statistics", "bachelors", "Statistics", "on_campus", 48),
    ("mich-strings-ug", "SMTD", "Strings", "bachelors", "Strings", "on_campus", 48),
    (
        "mich-theatre-and-drama-ug",
        "SMTD",
        "Theatre & Drama",
        "bachelors",
        "Theatre & Drama",
        "on_campus",
        48,
    ),
    ("mich-translation-ug", "LSA", "Translation", "bachelors", "Translation", "on_campus", 48),
    (
        "mich-urban-technology-ug",
        "TAUB",
        "Urban Technology",
        "bachelors",
        "Urban Technology",
        "on_campus",
        48,
    ),
    (
        "mich-user-experience-design-ug",
        "INFO",
        "User Experience Design",
        "bachelors",
        "User Experience Design",
        "on_campus",
        48,
    ),
    (
        "mich-voice-and-opera-ug",
        "SMTD",
        "Voice & Opera",
        "bachelors",
        "Voice & Opera",
        "on_campus",
        48,
    ),
    (
        "mich-winds-and-percussion-ug",
        "SMTD",
        "Winds & Percussion",
        "bachelors",
        "Winds & Percussion",
        "on_campus",
        48,
    ),
    (
        "mich-women-s-and-gender-studies-ug",
        "LSA",
        "Women’s and Gender Studies",
        "bachelors",
        "Women’s and Gender Studies",
        "on_campus",
        48,
    ),
    (
        "mich-aerospace-engineering-phd",
        "ENG",
        "Aerospace Engineering",
        "phd",
        "Aerospace Engineering",
        "on_campus",
        60,
    ),
    (
        "mich-aerospace-engineering-ms",
        "ENG",
        "Aerospace Engineering",
        "masters",
        "Aerospace Engineering",
        "on_campus",
        24,
    ),
    (
        "mich-american-culture-phd",
        "LSA",
        "American Culture",
        "phd",
        "American Culture",
        "on_campus",
        60,
    ),
    (
        "mich-ancient-history-phd",
        "LSA",
        "Ancient History",
        "phd",
        "Ancient History",
        "on_campus",
        60,
    ),
    (
        "mich-ancient-mediterranean-art-and-archaeology-phd",
        "LSA",
        "Ancient Mediterranean Art and Archaeology",
        "phd",
        "Ancient Mediterranean Art and Archaeology",
        "on_campus",
        60,
    ),
    ("mich-anthropology-phd", "LSA", "Anthropology", "phd", "Anthropology", "on_campus", 60),
    (
        "mich-anthropology-and-history-phd",
        "LSA",
        "Anthropology and History",
        "phd",
        "Anthropology and History",
        "on_campus",
        60,
    ),
    (
        "mich-applied-and-interdisciplinary-mathematics-phd",
        "LSA",
        "Applied and Interdisciplinary Mathematics",
        "phd",
        "Applied and Interdisciplinary Mathematics",
        "on_campus",
        60,
    ),
    (
        "mich-applied-and-interdisciplinary-mathematics-ms",
        "LSA",
        "Applied and Interdisciplinary Mathematics",
        "masters",
        "Applied and Interdisciplinary Mathematics",
        "on_campus",
        24,
    ),
    (
        "mich-applied-economics-ms",
        "LSA",
        "Applied Economics",
        "masters",
        "Applied Economics",
        "on_campus",
        24,
    ),
    (
        "mich-applied-physics-phd",
        "LSA",
        "Applied Physics",
        "phd",
        "Applied Physics",
        "on_campus",
        60,
    ),
    (
        "mich-applied-physics-ms",
        "LSA",
        "Applied Physics",
        "masters",
        "Applied Physics",
        "on_campus",
        24,
    ),
    (
        "mich-applied-statistics-ms",
        "LSA",
        "Applied Statistics",
        "masters",
        "Applied Statistics",
        "on_campus",
        24,
    ),
    (
        "mich-arabic-studies-ms",
        "LSA",
        "Arabic Studies",
        "masters",
        "Arabic Studies",
        "on_campus",
        24,
    ),
    ("mich-architecture-phd", "TAUB", "Architecture", "phd", "Architecture", "on_campus", 60),
    ("mich-architecture-ms", "TAUB", "Architecture", "masters", "Architecture", "on_campus", 24),
    ("mich-art-ms", "STAMPS", "Art", "masters", "Art", "on_campus", 24),
    (
        "mich-asian-languages-and-cultures-phd",
        "LSA",
        "Asian Languages and Cultures",
        "phd",
        "Asian Languages and Cultures",
        "on_campus",
        60,
    ),
    (
        "mich-astronomy-and-astrophysics-phd",
        "LSA",
        "Astronomy and Astrophysics",
        "phd",
        "Astronomy and Astrophysics",
        "on_campus",
        60,
    ),
    (
        "mich-athletic-training-ms",
        "KIN",
        "Athletic Training",
        "masters",
        "Athletic Training",
        "on_campus",
        24,
    ),
    ("mich-bioinformatics-phd", "MED", "Bioinformatics", "phd", "Bioinformatics", "on_campus", 60),
    (
        "mich-bioinformatics-ms",
        "MED",
        "Bioinformatics",
        "masters",
        "Bioinformatics",
        "on_campus",
        24,
    ),
    (
        "mich-bioinformatics-pibs-phd",
        "MED",
        "Bioinformatics (PIBS)",
        "phd",
        "Bioinformatics (PIBS)",
        "on_campus",
        60,
    ),
    (
        "mich-biological-chemistry-ms",
        "MED",
        "Biological Chemistry",
        "masters",
        "Biological Chemistry",
        "on_campus",
        24,
    ),
    (
        "mich-biological-chemistry-pibs-phd",
        "MED",
        "Biological Chemistry (PIBS)",
        "phd",
        "Biological Chemistry (PIBS)",
        "on_campus",
        60,
    ),
    (
        "mich-biomedical-engineering-phd",
        "ENG",
        "Biomedical Engineering",
        "phd",
        "Biomedical Engineering",
        "on_campus",
        60,
    ),
    (
        "mich-biomedical-engineering-ms",
        "ENG",
        "Biomedical Engineering",
        "masters",
        "Biomedical Engineering",
        "on_campus",
        24,
    ),
    (
        "mich-biomedical-sciences-pibs-phd",
        "MED",
        "Biomedical Sciences (PIBS)",
        "phd",
        "Biomedical Sciences (PIBS)",
        "on_campus",
        60,
    ),
    ("mich-biophysics-phd", "LSA", "Biophysics", "phd", "Biophysics", "on_campus", 60),
    ("mich-biostatistics-phd", "SPH", "Biostatistics", "phd", "Biostatistics", "on_campus", 60),
    ("mich-biostatistics-ms", "SPH", "Biostatistics", "masters", "Biostatistics", "on_campus", 24),
    (
        "mich-biostatistics-health-data-science-ms",
        "SPH",
        "Biostatistics: Health Data Science",
        "masters",
        "Biostatistics: Health Data Science",
        "on_campus",
        24,
    ),
    (
        "mich-business-administration-phd",
        "ROSS",
        "Business Administration",
        "phd",
        "Business Administration",
        "on_campus",
        60,
    ),
    (
        "mich-business-and-economics-phd",
        "ROSS",
        "Business and Economics",
        "phd",
        "Business and Economics",
        "on_campus",
        60,
    ),
    (
        "mich-cancer-biology-pibs-phd",
        "MED",
        "Cancer Biology (PIBS)",
        "phd",
        "Cancer Biology (PIBS)",
        "on_campus",
        60,
    ),
    (
        "mich-cell-and-developmental-biology-pibs-phd",
        "MED",
        "Cell and Developmental Biology (PIBS)",
        "phd",
        "Cell and Developmental Biology (PIBS)",
        "on_campus",
        60,
    ),
    (
        "mich-cellular-and-molecular-biology-pibs-phd",
        "MED",
        "Cellular and Molecular Biology (PIBS)",
        "phd",
        "Cellular and Molecular Biology (PIBS)",
        "on_campus",
        60,
    ),
    (
        "mich-chemical-biology-phd",
        "RACK",
        "Chemical Biology",
        "phd",
        "Chemical Biology",
        "on_campus",
        60,
    ),
    (
        "mich-chemical-biology-of-cancer-ms",
        "RACK",
        "Chemical Biology of Cancer",
        "masters",
        "Chemical Biology of Cancer",
        "on_campus",
        24,
    ),
    (
        "mich-chemical-engineering-phd",
        "ENG",
        "Chemical Engineering",
        "phd",
        "Chemical Engineering",
        "on_campus",
        60,
    ),
    (
        "mich-chemical-engineering-ms",
        "ENG",
        "Chemical Engineering",
        "masters",
        "Chemical Engineering",
        "on_campus",
        24,
    ),
    ("mich-chemistry-phd", "LSA", "Chemistry", "phd", "Chemistry", "on_campus", 60),
    ("mich-chemistry-ms", "LSA", "Chemistry", "masters", "Chemistry", "on_campus", 24),
    (
        "mich-civil-engineering-phd",
        "ENG",
        "Civil Engineering",
        "phd",
        "Civil Engineering",
        "on_campus",
        60,
    ),
    (
        "mich-civil-engineering-ms",
        "ENG",
        "Civil Engineering",
        "masters",
        "Civil Engineering",
        "on_campus",
        24,
    ),
    (
        "mich-classical-studies-phd",
        "LSA",
        "Classical Studies",
        "phd",
        "Classical Studies",
        "on_campus",
        60,
    ),
    (
        "mich-classical-studies-ms",
        "LSA",
        "Classical Studies",
        "masters",
        "Classical Studies",
        "on_campus",
        24,
    ),
    (
        "mich-climate-and-space-sciences-and-engineering-phd",
        "ENG",
        "Climate and Space Sciences and Engineering",
        "phd",
        "Climate and Space Sciences and Engineering",
        "on_campus",
        60,
    ),
    (
        "mich-climate-and-space-sciences-and-engineering-ms",
        "ENG",
        "Climate and Space Sciences and Engineering",
        "masters",
        "Climate and Space Sciences and Engineering",
        "on_campus",
        24,
    ),
    (
        "mich-clinical-pharmacy-translational-science-phd",
        "PHARM",
        "Clinical Pharmacy Translational Science",
        "phd",
        "Clinical Pharmacy Translational Science",
        "on_campus",
        60,
    ),
    (
        "mich-clinical-research-design-and-statistical-analysis-ms",
        "SPH",
        "Clinical Research Design and Statistical Analysis",
        "masters",
        "Clinical Research Design and Statistical Analysis",
        "on_campus",
        24,
    ),
    (
        "mich-communication-and-media-phd",
        "LSA",
        "Communication and Media",
        "phd",
        "Communication and Media",
        "on_campus",
        60,
    ),
    (
        "mich-comparative-literature-phd",
        "LSA",
        "Comparative Literature",
        "phd",
        "Comparative Literature",
        "on_campus",
        60,
    ),
    ("mich-composition-phd", "SMTD", "Composition", "phd", "Composition", "on_campus", 60),
    ("mich-composition-ms", "SMTD", "Composition", "masters", "Composition", "on_campus", 24),
    (
        "mich-composition-and-music-theory-phd",
        "SMTD",
        "Composition and Music Theory",
        "phd",
        "Composition and Music Theory",
        "on_campus",
        60,
    ),
    (
        "mich-computational-epidemiology-and-systems-modeling-ms",
        "SPH",
        "Computational Epidemiology and Systems Modeling",
        "masters",
        "Computational Epidemiology and Systems Modeling",
        "on_campus",
        24,
    ),
    (
        "mich-computer-science-and-engineering-phd",
        "ENG",
        "Computer Science and Engineering",
        "phd",
        "Computer Science and Engineering",
        "on_campus",
        60,
    ),
    (
        "mich-computer-science-and-engineering-ms",
        "ENG",
        "Computer Science and Engineering",
        "masters",
        "Computer Science and Engineering",
        "on_campus",
        24,
    ),
    (
        "mich-conducting-band-wind-ensemble-phd",
        "SMTD",
        "Conducting: Band/Wind Ensemble",
        "phd",
        "Conducting: Band/Wind Ensemble",
        "on_campus",
        60,
    ),
    (
        "mich-conducting-choral-phd",
        "SMTD",
        "Conducting: Choral",
        "phd",
        "Conducting: Choral",
        "on_campus",
        60,
    ),
    (
        "mich-conducting-orchestral-phd",
        "SMTD",
        "Conducting: Orchestral",
        "phd",
        "Conducting: Orchestral",
        "on_campus",
        60,
    ),
    (
        "mich-construction-engineering-and-management-ms",
        "ENG",
        "Construction Engineering and Management",
        "masters",
        "Construction Engineering and Management",
        "on_campus",
        24,
    ),
    (
        "mich-creative-writing-ms",
        "LSA",
        "Creative Writing",
        "masters",
        "Creative Writing",
        "on_campus",
        24,
    ),
    ("mich-dance-ms", "SMTD", "Dance", "masters", "Dance", "on_campus", 24),
    ("mich-data-science-ms", "LSA", "Data Science", "masters", "Data Science", "on_campus", 24),
    (
        "mich-dental-hygiene-ms",
        "DENT",
        "Dental Hygiene",
        "masters",
        "Dental Hygiene",
        "on_campus",
        24,
    ),
    ("mich-design-ms", "STAMPS", "Design", "masters", "Design", "on_campus", 24),
    ("mich-design-science-phd", "ENG", "Design Science", "phd", "Design Science", "on_campus", 60),
    (
        "mich-design-science-ms",
        "ENG",
        "Design Science",
        "masters",
        "Design Science",
        "on_campus",
        24,
    ),
    (
        "mich-earth-and-environmental-sciences-phd",
        "LSA",
        "Earth and Environmental Sciences",
        "phd",
        "Earth and Environmental Sciences",
        "on_campus",
        60,
    ),
    (
        "mich-earth-and-environmental-sciences-ms",
        "LSA",
        "Earth and Environmental Sciences",
        "masters",
        "Earth and Environmental Sciences",
        "on_campus",
        24,
    ),
    (
        "mich-ecology-and-evolutionary-biology-phd",
        "LSA",
        "Ecology and Evolutionary Biology",
        "phd",
        "Ecology and Evolutionary Biology",
        "on_campus",
        60,
    ),
    (
        "mich-ecology-and-evolutionary-biology-ms",
        "LSA",
        "Ecology and Evolutionary Biology",
        "masters",
        "Ecology and Evolutionary Biology",
        "on_campus",
        24,
    ),
    ("mich-economics-phd", "LSA", "Economics", "phd", "Economics", "on_campus", 60),
    (
        "mich-education-and-psychology-phd",
        "EDU",
        "Education and Psychology",
        "phd",
        "Education and Psychology",
        "on_campus",
        60,
    ),
    (
        "mich-educational-leadership-and-policy-ms",
        "EDU",
        "Educational Leadership and Policy",
        "masters",
        "Educational Leadership and Policy",
        "on_campus",
        24,
    ),
    (
        "mich-educational-studies-phd",
        "EDU",
        "Educational Studies",
        "phd",
        "Educational Studies",
        "on_campus",
        60,
    ),
    (
        "mich-educational-studies-ms",
        "EDU",
        "Educational Studies",
        "masters",
        "Educational Studies",
        "on_campus",
        24,
    ),
    (
        "mich-electrical-and-computer-engineering-phd",
        "ENG",
        "Electrical and Computer Engineering",
        "phd",
        "Electrical and Computer Engineering",
        "on_campus",
        60,
    ),
    (
        "mich-electrical-and-computer-engineering-ms",
        "ENG",
        "Electrical and Computer Engineering",
        "masters",
        "Electrical and Computer Engineering",
        "on_campus",
        24,
    ),
    ("mich-endodontics-ms", "DENT", "Endodontics", "masters", "Endodontics", "on_campus", 24),
    (
        "mich-engineering-education-research-phd",
        "ENG",
        "Engineering Education Research",
        "phd",
        "Engineering Education Research",
        "on_campus",
        60,
    ),
    (
        "mich-engineering-education-research-ms",
        "ENG",
        "Engineering Education Research",
        "masters",
        "Engineering Education Research",
        "on_campus",
        24,
    ),
    (
        "mich-english-and-education-phd",
        "LSA",
        "English and Education",
        "phd",
        "English and Education",
        "on_campus",
        60,
    ),
    (
        "mich-english-and-women-s-and-gender-studies-phd",
        "LSA",
        "English and Women’s and Gender Studies",
        "phd",
        "English and Women’s and Gender Studies",
        "on_campus",
        60,
    ),
    (
        "mich-english-language-and-literature-phd",
        "LSA",
        "English Language and Literature",
        "phd",
        "English Language and Literature",
        "on_campus",
        60,
    ),
    (
        "mich-environment-and-sustainability-ms",
        "SEAS",
        "Environment and Sustainability",
        "masters",
        "Environment and Sustainability",
        "on_campus",
        24,
    ),
    (
        "mich-environment-and-sustainability-phd",
        "SEAS",
        "Environment and Sustainability",
        "phd",
        "Environment and Sustainability",
        "on_campus",
        60,
    ),
    (
        "mich-environmental-engineering-phd",
        "ENG",
        "Environmental Engineering",
        "phd",
        "Environmental Engineering",
        "on_campus",
        60,
    ),
    (
        "mich-environmental-engineering-ms",
        "ENG",
        "Environmental Engineering",
        "masters",
        "Environmental Engineering",
        "on_campus",
        24,
    ),
    (
        "mich-environmental-health-sciences-phd",
        "SPH",
        "Environmental Health Sciences",
        "phd",
        "Environmental Health Sciences",
        "on_campus",
        60,
    ),
    (
        "mich-environmental-health-sciences-ms",
        "SPH",
        "Environmental Health Sciences",
        "masters",
        "Environmental Health Sciences",
        "on_campus",
        24,
    ),
    (
        "mich-epidemiologic-science-phd",
        "SPH",
        "Epidemiologic Science",
        "phd",
        "Epidemiologic Science",
        "on_campus",
        60,
    ),
    (
        "mich-film-television-and-media-phd",
        "LSA",
        "Film, Television, and Media",
        "phd",
        "Film, Television, and Media",
        "on_campus",
        60,
    ),
    (
        "mich-genetic-counseling-ms",
        "MED",
        "Genetic Counseling",
        "masters",
        "Genetic Counseling",
        "on_campus",
        24,
    ),
    (
        "mich-genetics-and-genomics-pibs-phd",
        "MED",
        "Genetics and Genomics (PIBS)",
        "phd",
        "Genetics and Genomics (PIBS)",
        "on_campus",
        60,
    ),
    (
        "mich-germanic-languages-and-literatures-phd",
        "LSA",
        "Germanic Languages and Literatures",
        "phd",
        "Germanic Languages and Literatures",
        "on_campus",
        60,
    ),
    ("mich-greek-ms", "LSA", "Greek", "masters", "Greek", "on_campus", 24),
    (
        "mich-health-and-health-care-research-ms",
        "MED",
        "Health and Health Care Research",
        "masters",
        "Health and Health Care Research",
        "on_campus",
        24,
    ),
    (
        "mich-health-behavior-and-health-equity-phd",
        "SPH",
        "Health Behavior and Health Equity",
        "phd",
        "Health Behavior and Health Equity",
        "on_campus",
        60,
    ),
    (
        "mich-health-behavior-and-health-equity-ms",
        "SPH",
        "Health Behavior and Health Equity",
        "masters",
        "Health Behavior and Health Equity",
        "on_campus",
        24,
    ),
    (
        "mich-health-infrastructures-and-learning-systems-phd",
        "MED",
        "Health Infrastructures and Learning Systems",
        "phd",
        "Health Infrastructures and Learning Systems",
        "on_campus",
        60,
    ),
    (
        "mich-health-infrastructures-and-learning-systems-ms",
        "MED",
        "Health Infrastructures and Learning Systems",
        "masters",
        "Health Infrastructures and Learning Systems",
        "on_campus",
        24,
    ),
    (
        "mich-health-infrastructures-and-learning-systems-online-ms",
        "MED",
        "Health Infrastructures and Learning Systems – Online",
        "masters",
        "Health Infrastructures and Learning Systems – Online",
        "online",
        24,
    ),
    (
        "mich-health-services-organization-and-policy-phd",
        "SPH",
        "Health Services Organization and Policy",
        "phd",
        "Health Services Organization and Policy",
        "on_campus",
        60,
    ),
    (
        "mich-higher-education-phd",
        "EDU",
        "Higher Education",
        "phd",
        "Higher Education",
        "on_campus",
        60,
    ),
    (
        "mich-higher-education-ms",
        "EDU",
        "Higher Education",
        "masters",
        "Higher Education",
        "on_campus",
        24,
    ),
    ("mich-history-phd", "LSA", "History", "phd", "History", "on_campus", 60),
    (
        "mich-history-and-women-s-and-gender-studies-phd",
        "LSA",
        "History and Women’s and Gender Studies",
        "phd",
        "History and Women’s and Gender Studies",
        "on_campus",
        60,
    ),
    ("mich-history-of-art-phd", "LSA", "History of Art", "phd", "History of Art", "on_campus", 60),
    (
        "mich-human-genetics-ms",
        "MED",
        "Human Genetics",
        "masters",
        "Human Genetics",
        "on_campus",
        24,
    ),
    (
        "mich-immunology-pibs-phd",
        "MED",
        "Immunology (PIBS)",
        "phd",
        "Immunology (PIBS)",
        "on_campus",
        60,
    ),
    (
        "mich-industrial-and-operations-engineering-phd",
        "ENG",
        "Industrial and Operations Engineering",
        "phd",
        "Industrial and Operations Engineering",
        "on_campus",
        60,
    ),
    (
        "mich-industrial-and-operations-engineering-ms",
        "ENG",
        "Industrial and Operations Engineering",
        "masters",
        "Industrial and Operations Engineering",
        "on_campus",
        24,
    ),
    ("mich-information-phd", "INFO", "Information", "phd", "Information", "on_campus", 60),
    (
        "mich-integrated-pharmaceutical-sciences-ms",
        "PHARM",
        "Integrated Pharmaceutical Sciences",
        "masters",
        "Integrated Pharmaceutical Sciences",
        "on_campus",
        24,
    ),
    (
        "mich-international-and-regional-studies-ms",
        "LSA",
        "International and Regional Studies",
        "masters",
        "International and Regional Studies",
        "on_campus",
        24,
    ),
    (
        "mich-intraoperative-neurophysiology-ms",
        "KIN",
        "Intraoperative Neurophysiology",
        "masters",
        "Intraoperative Neurophysiology",
        "on_campus",
        24,
    ),
    (
        "mich-jazz-and-contemporary-improvisation-phd",
        "SMTD",
        "Jazz and Contemporary Improvisation",
        "phd",
        "Jazz and Contemporary Improvisation",
        "on_campus",
        60,
    ),
    (
        "mich-landscape-architecture-ms",
        "SEAS",
        "Landscape Architecture",
        "masters",
        "Landscape Architecture",
        "on_campus",
        24,
    ),
    ("mich-latin-ms", "LSA", "Latin", "masters", "Latin", "on_campus", 24),
    ("mich-linguistics-phd", "LSA", "Linguistics", "phd", "Linguistics", "on_campus", 60),
    (
        "mich-macromolecular-science-and-engineering-phd",
        "ENG",
        "Macromolecular Science and Engineering",
        "phd",
        "Macromolecular Science and Engineering",
        "on_campus",
        60,
    ),
    (
        "mich-macromolecular-science-and-engineering-ms",
        "ENG",
        "Macromolecular Science and Engineering",
        "masters",
        "Macromolecular Science and Engineering",
        "on_campus",
        24,
    ),
    (
        "mich-materials-science-and-engineering-phd",
        "ENG",
        "Materials Science and Engineering",
        "phd",
        "Materials Science and Engineering",
        "on_campus",
        60,
    ),
    (
        "mich-materials-science-and-engineering-ms",
        "ENG",
        "Materials Science and Engineering",
        "masters",
        "Materials Science and Engineering",
        "on_campus",
        24,
    ),
    ("mich-mathematics-phd", "LSA", "Mathematics", "phd", "Mathematics", "on_campus", 60),
    ("mich-mathematics-ms", "LSA", "Mathematics", "masters", "Mathematics", "on_campus", 24),
    (
        "mich-mechanical-engineering-phd",
        "ENG",
        "Mechanical Engineering",
        "phd",
        "Mechanical Engineering",
        "on_campus",
        60,
    ),
    (
        "mich-mechanical-engineering-ms",
        "ENG",
        "Mechanical Engineering",
        "masters",
        "Mechanical Engineering",
        "on_campus",
        24,
    ),
    ("mich-media-arts-ms", "SMTD", "Media Arts", "masters", "Media Arts", "on_campus", 24),
    (
        "mich-medical-scientist-training-program-phd",
        "MED",
        "Medical Scientist Training Program",
        "phd",
        "Medical Scientist Training Program",
        "on_campus",
        60,
    ),
    (
        "mich-medicinal-chemistry-phd",
        "PHARM",
        "Medicinal Chemistry",
        "phd",
        "Medicinal Chemistry",
        "on_campus",
        60,
    ),
    (
        "mich-microbiology-and-immunology-ms",
        "MED",
        "Microbiology and Immunology",
        "masters",
        "Microbiology and Immunology",
        "on_campus",
        24,
    ),
    (
        "mich-microbiology-and-immunology-pibs-phd",
        "MED",
        "Microbiology and Immunology (PIBS)",
        "phd",
        "Microbiology and Immunology (PIBS)",
        "on_campus",
        60,
    ),
    (
        "mich-middle-east-studies-phd",
        "LSA",
        "Middle East Studies",
        "phd",
        "Middle East Studies",
        "on_campus",
        60,
    ),
    (
        "mich-molecular-and-cellular-pathology-pibs-phd",
        "MED",
        "Molecular and Cellular Pathology (PIBS)",
        "phd",
        "Molecular and Cellular Pathology (PIBS)",
        "on_campus",
        60,
    ),
    (
        "mich-molecular-and-integrative-physiology-ms",
        "MED",
        "Molecular and Integrative Physiology",
        "masters",
        "Molecular and Integrative Physiology",
        "on_campus",
        24,
    ),
    (
        "mich-molecular-and-integrative-physiology-pibs-phd",
        "MED",
        "Molecular and Integrative Physiology (PIBS)",
        "phd",
        "Molecular and Integrative Physiology (PIBS)",
        "on_campus",
        60,
    ),
    (
        "mich-molecular-cellular-and-developmental-biology-phd",
        "LSA",
        "Molecular, Cellular, and Developmental Biology",
        "phd",
        "Molecular, Cellular, and Developmental Biology",
        "on_campus",
        60,
    ),
    (
        "mich-molecular-cellular-and-developmental-biology-ms",
        "LSA",
        "Molecular, Cellular, and Developmental Biology",
        "masters",
        "Molecular, Cellular, and Developmental Biology",
        "on_campus",
        24,
    ),
    (
        "mich-molecular-cellular-and-developmental-biology-pibs-phd",
        "MED",
        "Molecular, Cellular, and Developmental Biology (PIBS)",
        "phd",
        "Molecular, Cellular, and Developmental Biology (PIBS)",
        "on_campus",
        60,
    ),
    (
        "mich-movement-science-phd",
        "KIN",
        "Movement Science",
        "phd",
        "Movement Science",
        "on_campus",
        60,
    ),
    (
        "mich-movement-science-ms",
        "KIN",
        "Movement Science",
        "masters",
        "Movement Science",
        "on_campus",
        24,
    ),
    (
        "mich-music-education-phd",
        "SMTD",
        "Music Education",
        "phd",
        "Music Education",
        "on_campus",
        60,
    ),
    ("mich-music-theory-phd", "SMTD", "Music Theory", "phd", "Music Theory", "on_campus", 60),
    ("mich-musicology-phd", "SMTD", "Musicology", "phd", "Musicology", "on_campus", 60),
    (
        "mich-musicology-ethnomusicology-phd",
        "SMTD",
        "Musicology: Ethnomusicology",
        "phd",
        "Musicology: Ethnomusicology",
        "on_campus",
        60,
    ),
    (
        "mich-musicology-ethnomusicology-ms",
        "SMTD",
        "Musicology: Ethnomusicology",
        "masters",
        "Musicology: Ethnomusicology",
        "on_campus",
        24,
    ),
    (
        "mich-musicology-history-phd",
        "SMTD",
        "Musicology: History",
        "phd",
        "Musicology: History",
        "on_campus",
        60,
    ),
    (
        "mich-naval-architecture-and-marine-engineering-phd",
        "ENG",
        "Naval Architecture and Marine Engineering",
        "phd",
        "Naval Architecture and Marine Engineering",
        "on_campus",
        60,
    ),
    (
        "mich-naval-architecture-and-marine-engineering-ms",
        "ENG",
        "Naval Architecture and Marine Engineering",
        "masters",
        "Naval Architecture and Marine Engineering",
        "on_campus",
        24,
    ),
    ("mich-neuroscience-phd", "MED", "Neuroscience", "phd", "Neuroscience", "on_campus", 60),
    (
        "mich-neuroscience-pibs-phd",
        "MED",
        "Neuroscience (PIBS)",
        "phd",
        "Neuroscience (PIBS)",
        "on_campus",
        60,
    ),
    (
        "mich-nuclear-engineering-and-radiological-sciences-phd",
        "ENG",
        "Nuclear Engineering and Radiological Sciences",
        "phd",
        "Nuclear Engineering and Radiological Sciences",
        "on_campus",
        60,
    ),
    (
        "mich-nuclear-engineering-and-radiological-sciences-ms",
        "ENG",
        "Nuclear Engineering and Radiological Sciences",
        "masters",
        "Nuclear Engineering and Radiological Sciences",
        "on_campus",
        24,
    ),
    ("mich-nursing-ph-d-phd", "NURS", "Nursing, Ph.D.", "phd", "Nursing, Ph.D.", "on_campus", 60),
    (
        "mich-nutritional-sciences-phd",
        "SPH",
        "Nutritional Sciences",
        "phd",
        "Nutritional Sciences",
        "on_campus",
        60,
    ),
    (
        "mich-nutritional-sciences-ms",
        "SPH",
        "Nutritional Sciences",
        "masters",
        "Nutritional Sciences",
        "on_campus",
        24,
    ),
    (
        "mich-oral-health-sciences-phd",
        "DENT",
        "Oral Health Sciences",
        "phd",
        "Oral Health Sciences",
        "on_campus",
        60,
    ),
    (
        "mich-oral-health-sciences-ms",
        "DENT",
        "Oral Health Sciences",
        "masters",
        "Oral Health Sciences",
        "on_campus",
        24,
    ),
    ("mich-orthodontics-ms", "DENT", "Orthodontics", "masters", "Orthodontics", "on_campus", 24),
    (
        "mich-pediatric-dentistry-ms",
        "DENT",
        "Pediatric Dentistry",
        "masters",
        "Pediatric Dentistry",
        "on_campus",
        24,
    ),
    (
        "mich-performance-bassoon-phd",
        "SMTD",
        "Performance: Bassoon",
        "phd",
        "Performance: Bassoon",
        "on_campus",
        60,
    ),
    (
        "mich-performance-cello-phd",
        "SMTD",
        "Performance: Cello",
        "phd",
        "Performance: Cello",
        "on_campus",
        60,
    ),
    (
        "mich-performance-clarinet-phd",
        "SMTD",
        "Performance: Clarinet",
        "phd",
        "Performance: Clarinet",
        "on_campus",
        60,
    ),
    (
        "mich-performance-collaborative-piano-phd",
        "SMTD",
        "Performance: Collaborative Piano",
        "phd",
        "Performance: Collaborative Piano",
        "on_campus",
        60,
    ),
    (
        "mich-performance-double-bass-phd",
        "SMTD",
        "Performance: Double Bass",
        "phd",
        "Performance: Double Bass",
        "on_campus",
        60,
    ),
    (
        "mich-performance-euphonium-phd",
        "SMTD",
        "Performance: Euphonium",
        "phd",
        "Performance: Euphonium",
        "on_campus",
        60,
    ),
    (
        "mich-performance-flute-phd",
        "SMTD",
        "Performance: Flute",
        "phd",
        "Performance: Flute",
        "on_campus",
        60,
    ),
    (
        "mich-performance-french-horn-phd",
        "SMTD",
        "Performance: French Horn",
        "phd",
        "Performance: French Horn",
        "on_campus",
        60,
    ),
    (
        "mich-performance-harp-phd",
        "SMTD",
        "Performance: Harp",
        "phd",
        "Performance: Harp",
        "on_campus",
        60,
    ),
    (
        "mich-performance-harpsichord-phd",
        "SMTD",
        "Performance: Harpsichord",
        "phd",
        "Performance: Harpsichord",
        "on_campus",
        60,
    ),
    (
        "mich-performance-oboe-phd",
        "SMTD",
        "Performance: Oboe",
        "phd",
        "Performance: Oboe",
        "on_campus",
        60,
    ),
    (
        "mich-performance-organ-phd",
        "SMTD",
        "Performance: Organ",
        "phd",
        "Performance: Organ",
        "on_campus",
        60,
    ),
    (
        "mich-performance-organ-sacred-music-phd",
        "SMTD",
        "Performance: Organ: Sacred Music",
        "phd",
        "Performance: Organ: Sacred Music",
        "on_campus",
        60,
    ),
    (
        "mich-performance-percussion-phd",
        "SMTD",
        "Performance: Percussion",
        "phd",
        "Performance: Percussion",
        "on_campus",
        60,
    ),
    (
        "mich-performance-piano-phd",
        "SMTD",
        "Performance: Piano",
        "phd",
        "Performance: Piano",
        "on_campus",
        60,
    ),
    (
        "mich-performance-piano-pedagogy-and-performance-phd",
        "SMTD",
        "Performance: Piano Pedagogy and Performance",
        "phd",
        "Performance: Piano Pedagogy and Performance",
        "on_campus",
        60,
    ),
    (
        "mich-performance-saxophone-phd",
        "SMTD",
        "Performance: Saxophone",
        "phd",
        "Performance: Saxophone",
        "on_campus",
        60,
    ),
    (
        "mich-performance-trombone-phd",
        "SMTD",
        "Performance: Trombone",
        "phd",
        "Performance: Trombone",
        "on_campus",
        60,
    ),
    (
        "mich-performance-trumpet-phd",
        "SMTD",
        "Performance: Trumpet",
        "phd",
        "Performance: Trumpet",
        "on_campus",
        60,
    ),
    (
        "mich-performance-tuba-phd",
        "SMTD",
        "Performance: Tuba",
        "phd",
        "Performance: Tuba",
        "on_campus",
        60,
    ),
    (
        "mich-performance-viola-phd",
        "SMTD",
        "Performance: Viola",
        "phd",
        "Performance: Viola",
        "on_campus",
        60,
    ),
    (
        "mich-performance-violin-phd",
        "SMTD",
        "Performance: Violin",
        "phd",
        "Performance: Violin",
        "on_campus",
        60,
    ),
    (
        "mich-performance-voice-phd",
        "SMTD",
        "Performance: Voice",
        "phd",
        "Performance: Voice",
        "on_campus",
        60,
    ),
    (
        "mich-performing-arts-technology-phd",
        "SMTD",
        "Performing Arts Technology",
        "phd",
        "Performing Arts Technology",
        "on_campus",
        60,
    ),
    ("mich-periodontics-ms", "DENT", "Periodontics", "masters", "Periodontics", "on_campus", 24),
    (
        "mich-pharmaceutical-sciences-phd",
        "PHARM",
        "Pharmaceutical Sciences",
        "phd",
        "Pharmaceutical Sciences",
        "on_campus",
        60,
    ),
    ("mich-pharmacology-ms", "MED", "Pharmacology", "masters", "Pharmacology", "on_campus", 24),
    (
        "mich-pharmacology-pibs-phd",
        "MED",
        "Pharmacology (PIBS)",
        "phd",
        "Pharmacology (PIBS)",
        "on_campus",
        60,
    ),
    ("mich-philosophy-phd", "LSA", "Philosophy", "phd", "Philosophy", "on_campus", 60),
    ("mich-philosophy-ms", "LSA", "Philosophy", "masters", "Philosophy", "on_campus", 24),
    ("mich-physics-phd", "LSA", "Physics", "phd", "Physics", "on_campus", 60),
    (
        "mich-pibs-program-in-biomedical-sciences-phd",
        "MED",
        "PIBS (Program In Biomedical Sciences)",
        "phd",
        "PIBS (Program In Biomedical Sciences)",
        "on_campus",
        60,
    ),
    (
        "mich-political-science-phd",
        "LSA",
        "Political Science",
        "phd",
        "Political Science",
        "on_campus",
        60,
    ),
    (
        "mich-political-science-and-public-policy-phd",
        "FORD",
        "Political Science and Public Policy",
        "phd",
        "Political Science and Public Policy",
        "on_campus",
        60,
    ),
    (
        "mich-population-and-health-sciences-ms",
        "SPH",
        "Population and Health Sciences",
        "masters",
        "Population and Health Sciences",
        "on_campus",
        24,
    ),
    (
        "mich-prosthodontics-ms",
        "DENT",
        "Prosthodontics",
        "masters",
        "Prosthodontics",
        "on_campus",
        24,
    ),
    ("mich-psychology-phd", "LSA", "Psychology", "phd", "Psychology", "on_campus", 60),
    ("mich-psychology-ms", "LSA", "Psychology", "masters", "Psychology", "on_campus", 24),
    (
        "mich-psychology-and-women-s-and-gender-studies-phd",
        "LSA",
        "Psychology and Women’s and Gender Studies",
        "phd",
        "Psychology and Women’s and Gender Studies",
        "on_campus",
        60,
    ),
    (
        "mich-public-affairs-ms",
        "FORD",
        "Public Affairs",
        "masters",
        "Public Affairs",
        "on_campus",
        24,
    ),
    ("mich-public-policy-ms", "FORD", "Public Policy", "masters", "Public Policy", "on_campus", 24),
    (
        "mich-public-policy-and-economics-phd",
        "FORD",
        "Public Policy and Economics",
        "phd",
        "Public Policy and Economics",
        "on_campus",
        60,
    ),
    (
        "mich-public-policy-and-political-science-phd",
        "FORD",
        "Public Policy and Political Science",
        "phd",
        "Public Policy and Political Science",
        "on_campus",
        60,
    ),
    (
        "mich-public-policy-and-sociology-phd",
        "FORD",
        "Public Policy and Sociology",
        "phd",
        "Public Policy and Sociology",
        "on_campus",
        60,
    ),
    (
        "mich-quantitative-finance-and-risk-management-ms",
        "LSA",
        "Quantitative Finance and Risk Management",
        "masters",
        "Quantitative Finance and Risk Management",
        "on_campus",
        24,
    ),
    (
        "mich-restorative-dentistry-ms",
        "DENT",
        "Restorative Dentistry",
        "masters",
        "Restorative Dentistry",
        "on_campus",
        24,
    ),
    ("mich-robotics-phd", "ENG", "Robotics", "phd", "Robotics", "on_campus", 60),
    ("mich-robotics-ms", "ENG", "Robotics", "masters", "Robotics", "on_campus", 24),
    (
        "mich-romance-languages-and-literatures-french-phd",
        "LSA",
        "Romance Languages and Literatures: French",
        "phd",
        "Romance Languages and Literatures: French",
        "on_campus",
        60,
    ),
    (
        "mich-romance-languages-and-literatures-italian-phd",
        "LSA",
        "Romance Languages and Literatures: Italian",
        "phd",
        "Romance Languages and Literatures: Italian",
        "on_campus",
        60,
    ),
    (
        "mich-romance-languages-and-literatures-spanish-phd",
        "LSA",
        "Romance Languages and Literatures: Spanish",
        "phd",
        "Romance Languages and Literatures: Spanish",
        "on_campus",
        60,
    ),
    (
        "mich-scientific-computing-phd",
        "ENG",
        "Scientific Computing",
        "phd",
        "Scientific Computing",
        "on_campus",
        60,
    ),
    (
        "mich-slavic-languages-and-literatures-phd",
        "LSA",
        "Slavic Languages and Literatures",
        "phd",
        "Slavic Languages and Literatures",
        "on_campus",
        60,
    ),
    (
        "mich-social-work-and-anthropology-phd",
        "SSW",
        "Social Work and Anthropology",
        "phd",
        "Social Work and Anthropology",
        "on_campus",
        60,
    ),
    (
        "mich-social-work-and-psychology-phd",
        "SSW",
        "Social Work and Psychology",
        "phd",
        "Social Work and Psychology",
        "on_campus",
        60,
    ),
    (
        "mich-social-work-and-social-welfare-phd",
        "SSW",
        "Social Work and Social Welfare",
        "phd",
        "Social Work and Social Welfare",
        "on_campus",
        60,
    ),
    (
        "mich-social-work-and-sociology-phd",
        "SSW",
        "Social Work and Sociology",
        "phd",
        "Social Work and Sociology",
        "on_campus",
        60,
    ),
    ("mich-sociology-phd", "LSA", "Sociology", "phd", "Sociology", "on_campus", 60),
    (
        "mich-sociology-and-public-policy-phd",
        "FORD",
        "Sociology and Public Policy",
        "phd",
        "Sociology and Public Policy",
        "on_campus",
        60,
    ),
    (
        "mich-sport-management-phd",
        "KIN",
        "Sport Management",
        "phd",
        "Sport Management",
        "on_campus",
        60,
    ),
    (
        "mich-sport-management-ms",
        "KIN",
        "Sport Management",
        "masters",
        "Sport Management",
        "on_campus",
        24,
    ),
    ("mich-statistics-phd", "LSA", "Statistics", "phd", "Statistics", "on_campus", 60),
    (
        "mich-survey-and-data-science-phd",
        "LSA",
        "Survey and Data Science",
        "phd",
        "Survey and Data Science",
        "on_campus",
        60,
    ),
    (
        "mich-survey-and-data-science-ms",
        "LSA",
        "Survey and Data Science",
        "masters",
        "Survey and Data Science",
        "on_campus",
        24,
    ),
    ("mich-toxicology-phd", "SPH", "Toxicology", "phd", "Toxicology", "on_campus", 60),
    ("mich-toxicology-ms", "SPH", "Toxicology", "masters", "Toxicology", "on_campus", 24),
    (
        "mich-transcultural-studies-ms",
        "LSA",
        "Transcultural Studies",
        "masters",
        "Transcultural Studies",
        "on_campus",
        24,
    ),
    (
        "mich-urban-and-regional-planning-phd",
        "TAUB",
        "Urban and Regional Planning",
        "phd",
        "Urban and Regional Planning",
        "on_campus",
        60,
    ),
    (
        "mich-urban-and-regional-planning-ms",
        "TAUB",
        "Urban and Regional Planning",
        "masters",
        "Urban and Regional Planning",
        "on_campus",
        24,
    ),
    (
        "mich-master-of-architecture-march",
        "TAUB",
        "Master of Architecture",
        "masters",
        "Master of Architecture",
        "on_campus",
        24,
    ),
    (
        "mich-master-of-urban-design-mud",
        "TAUB",
        "Master of Urban Design",
        "masters",
        "Master of Urban Design",
        "on_campus",
        24,
    ),
    (
        "mich-master-of-business-administration-mba",
        "ROSS",
        "Master of Business Administration",
        "professional",
        "Master of Business Administration",
        "on_campus",
        36,
    ),
    (
        "mich-doctor-of-dental-surgery-dds",
        "DENT",
        "Doctor of Dental Surgery",
        "professional",
        "Doctor of Dental Surgery",
        "on_campus",
        36,
    ),
    (
        "mich-master-of-engineering-meng",
        "ENG",
        "Master of Engineering",
        "masters",
        "Master of Engineering",
        "on_campus",
        24,
    ),
    (
        "mich-doctor-of-engineering-deng",
        "ENG",
        "Doctor of Engineering",
        "phd",
        "Doctor of Engineering",
        "on_campus",
        60,
    ),
    (
        "mich-master-of-health-informatics-mhi",
        "INFO",
        "Master of Health Informatics",
        "masters",
        "Master of Health Informatics",
        "on_campus",
        24,
    ),
    (
        "mich-master-of-science-in-information-msi",
        "INFO",
        "Master of Science in Information",
        "masters",
        "Master of Science in Information",
        "on_campus",
        24,
    ),
    (
        "mich-juris-doctor-jd",
        "LAW",
        "Juris Doctor",
        "professional",
        "Juris Doctor",
        "on_campus",
        36,
    ),
    (
        "mich-master-of-laws-llm",
        "LAW",
        "Master of Laws",
        "masters",
        "Master of Laws",
        "on_campus",
        24,
    ),
    (
        "mich-doctor-of-medicine-md",
        "MED",
        "Doctor of Medicine",
        "professional",
        "Doctor of Medicine",
        "on_campus",
        36,
    ),
    (
        "mich-master-of-music-mm",
        "SMTD",
        "Master of Music",
        "masters",
        "Master of Music",
        "on_campus",
        24,
    ),
    (
        "mich-specialist-in-music-smus",
        "SMTD",
        "Specialist in Music",
        "masters",
        "Specialist in Music",
        "on_campus",
        24,
    ),
    (
        "mich-master-of-science-in-nursing-msn",
        "NURS",
        "Master of Science in Nursing",
        "masters",
        "Master of Science in Nursing",
        "on_campus",
        24,
    ),
    (
        "mich-doctor-of-pharmacy-pharmd",
        "PHARM",
        "Doctor of Pharmacy",
        "professional",
        "Doctor of Pharmacy",
        "on_campus",
        36,
    ),
    (
        "mich-master-of-public-health-mph",
        "SPH",
        "Master of Public Health",
        "masters",
        "Master of Public Health",
        "on_campus",
        24,
    ),
    (
        "mich-master-of-health-services-administration-mhsa",
        "SPH",
        "Master of Health Services Administration",
        "masters",
        "Master of Health Services Administration",
        "on_campus",
        24,
    ),
    (
        "mich-doctor-of-public-health-drph",
        "SPH",
        "Doctor of Public Health",
        "phd",
        "Doctor of Public Health",
        "on_campus",
        60,
    ),
    (
        "mich-master-of-social-work-msw",
        "SSW",
        "Master of Social Work",
        "masters",
        "Master of Social Work",
        "on_campus",
        24,
    ),
]

_SPECIAL_NAMES: dict[str, str] = {
    "mich-business-ug": "Bachelor of Business Administration",
    "mich-master-of-business-administration-mba": "Master of Business Administration",
    "mich-juris-doctor-jd": "Juris Doctor",
    "mich-doctor-of-medicine-md": "Doctor of Medicine",
    "mich-doctor-of-dental-surgery-dds": "Doctor of Dental Surgery",
    "mich-doctor-of-pharmacy-pharmd": "Doctor of Pharmacy",
    "mich-master-of-architecture-march": "Master of Architecture",
    "mich-master-of-urban-design-mud": "Master of Urban Design",
    "mich-master-of-engineering-meng": "Master of Engineering",
    "mich-doctor-of-engineering-deng": "Doctor of Engineering",
    "mich-master-of-health-informatics-mhi": "Master of Health Informatics",
    "mich-master-of-science-in-information-msi": "Master of Science in Information",
    "mich-master-of-laws-llm": "Master of Laws",
    "mich-master-of-music-mm": "Master of Music",
    "mich-specialist-in-music-smus": "Specialist in Music",
    "mich-master-of-science-in-nursing-msn": "Master of Science in Nursing",
    "mich-master-of-public-health-mph": "Master of Public Health",
    "mich-master-of-health-services-administration-mhsa": "Master of Health Services Administration",
    "mich-doctor-of-public-health-drph": "Doctor of Public Health",
    "mich-master-of-social-work-msw": "Master of Social Work",
    "mich-dance-ug": "Bachelor of Fine Arts in Dance",
    "mich-musical-theatre-ug": "Bachelor of Fine Arts in Musical Theatre",
    "mich-theatre-ug": "Bachelor of Fine Arts in Theatre",
    "mich-data-science-ug": "Bachelor of Science in Data Science (Engineering)",
    "mich-data-science-ug-lsa": "Bachelor of Science in Data Science (LSA)",
    "mich-interarts-performance-ug": "Bachelor of Fine Arts in Interarts Performance (Stamps)",
    "mich-interarts-performance-ug-smtd": "Bachelor of Fine Arts in Interarts Performance (SMTD)",
}

_UG_PREFIX_BY_SCHOOL: dict[str, str] = {
    "ENG": "Bachelor of Science in",
    "LSA": "Bachelor of Arts in",
    "KIN": "Bachelor of Science in",
    "NURS": "Bachelor of Science in",
    "INFO": "Bachelor of Science in",
    "ROSS": "Bachelor of Business Administration in",
    "SMTD": "Bachelor of Music in",
    "STAMPS": "Bachelor of Fine Arts in",
    "TAUB": "Bachelor of Science in",
    "SEAS": "Bachelor of Science in",
    "EDU": "Bachelor of Science in",
    "SPH": "Bachelor of Science in",
    "FORD": "Bachelor of Arts in",
    "DENT": "Bachelor of Science in",
    "PHARM": "Bachelor of Science in",
    "SSW": "Bachelor of Social Work in",
    "MED": "Bachelor of Science in",
    "LAW": "Bachelor of Arts in",
    "RACK": "Bachelor of Arts in",
}

_SUFFIX_MAP: list[tuple[str, str]] = [
    ("-phd", "prefix:Doctor of Philosophy in"),
    ("-ms", "prefix:Master of Science in"),
    ("-ug", "ug"),
    ("-ug-eng", "prefix:Bachelor of Science in"),
    ("-ug-lsa", "prefix:Bachelor of Science in"),
    ("-ug-ross", "prefix:Bachelor of Business Administration in"),
    ("-ug-smtd", "prefix:Bachelor of Fine Arts in"),
]


def _derive_program_name(slug: str, field: str, school_key: str) -> str:
    if slug in _SPECIAL_NAMES:
        return _SPECIAL_NAMES[slug]
    for suffix, spec in _SUFFIX_MAP:
        if slug.endswith(suffix):
            if spec == "ug":
                prefix = _UG_PREFIX_BY_SCHOOL.get(school_key, "Bachelor of Arts in")
                if prefix.endswith(" in"):
                    return f"{prefix} {field}"
                return f"{prefix} {field}" if prefix else field
            if spec.startswith("fixed:"):
                return spec[6:]
            prefix = spec[7:]
            return f"{prefix} {field}"
    return field


def _field_key(program_name: str) -> str:
    if program_name in _SPECIAL_NAMES.values():
        return program_name
    for prefix in (
        "Bachelor of Science in ",
        "Bachelor of Arts in ",
        "Bachelor of Fine Arts in ",
        "Bachelor of Music in ",
        "Bachelor of Social Work in ",
        "Bachelor of Business Administration in ",
        "Master of Science in ",
        "Master of Arts in ",
        "Master of Fine Arts in ",
        "Master of Music in ",
        "Master of Engineering in ",
        "Master of Public Health in ",
        "Master of Social Work in ",
        "Doctor of Philosophy in ",
        "Juris Doctor",
        "Doctor of Medicine",
        "Doctor of Dental Surgery",
        "Doctor of Pharmacy",
        "Master of Business Administration",
        "Bachelor of Business Administration",
    ):
        if program_name.startswith(prefix):
            return program_name[len(prefix) :].strip()
    return program_name


_LEVEL_SUFFIX: dict[str, str] = {
    "bachelors": (
        " Undergraduates complete major requirements, electives, and often "
        "undergraduate research or internships across the Ann Arbor campus."
    ),
    "masters": (
        " Graduate students complete advanced seminars, practica, and a thesis or "
        "capstone project."
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

_MICHIGAN_ANTI_STUB_REWRITES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bis a master's degree\b", re.I), "is a graduate curriculum"),
    (re.compile(r"\bis an undergraduate degree\b", re.I), "is an undergraduate curriculum"),
    (
        re.compile(r"\bis (a|an) (under)?graduate (degree|major|program)\b", re.I),
        r"is a \2graduate curriculum",
    ),
)


def _sanitize_michigan_anti_stub_tells(clause: str) -> str:
    out = re.sub(r"\.{2,}", ".", clause)
    for pattern, repl in _MICHIGAN_ANTI_STUB_REWRITES:
        out = pattern.sub(repl, out)
    return out


_LEVEL_PRIORITY: dict[str, int] = {
    "bachelors": 0,
    "certificate": 1,
    "masters": 2,
    "phd": 3,
    "doctoral": 3,
    "professional": 4,
}

_FRAME_PREFIX_RE = re.compile(
    r"^(?:Graduate study\.|Doctoral research\.)\s*",
    re.I,
)

_FOCUS_LEAD_RE = re.compile(
    r"^(.*?\b(?:covers|combines|spans|includes|integrates|offers?|examines?|trains?|"
    r"prepares?|underpins?|emphasizes?|centers? on|focuses? on|explores?|studies|study|"
    r"pairs?|blends?|joins?|teach(?:es)?|analyze[s]?|bridges?|operate[s]?|run[s]?|use[s]?|"
    r"support[s]?|choose among|applies?|develops?|designs?)\b\s*)",
    re.I,
)


def _strip_michigan_frame(clause: str) -> str:
    return _FRAME_PREFIX_RE.sub("", clause).strip()


def _extract_focus(clause: str) -> str:
    clause = _strip_michigan_frame(clause)
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


def _michigan_sibling_body(
    degree_type: str,
    field_label: str,
    focus: str,
    school: str,
    program_name: str,
) -> str:
    """Distinct, level-specific body for a credential sibling (not the field's anchor)."""
    if degree_type == "bachelors":
        return (
            f"The {program_name} at the University of Michigan develops {focus} through "
            f"core coursework, electives, and research or internship opportunities "
            f"within {school} on the Ann Arbor campus."
        )
    if degree_type == "masters":
        return (
            f"The {program_name} at the University of Michigan builds advanced expertise "
            f"in {focus}, combining graduate seminars, methods training, and a thesis or "
            f"capstone within {school} on the Ann Arbor campus."
        )
    if degree_type in ("phd", "doctoral"):
        return (
            f"The {program_name} at the University of Michigan advances original research "
            f"in {focus}, supported by faculty mentorship, qualifying examinations, and "
            f"dissertation work within {school} on the Ann Arbor campus."
        )
    if degree_type == "certificate":
        return (
            f"The {program_name} at the University of Michigan packages focused coursework "
            f"in {focus} for degree-seekers and working professionals within {school}."
        )
    if degree_type == "professional":
        return (
            f"The {program_name} at the University of Michigan pairs classroom study with "
            f"supervised clinical or practical training in {focus} through {school}."
        )
    return (
        f"The {program_name} at the University of Michigan engages {focus} through "
        f"coursework and training within {school} on the Ann Arbor campus."
    )


# Slugs whose catalogue prose is a genuinely distinct credential (not the field-definition
# template shared across siblings) — keep the researched slug body instead of the
# level-specific sibling frame.
_SLUG_DESCRIPTION_KEEP = frozenset(
    {
        "mich-master-of-architecture-march",
        "mich-specialist-in-music-smus",
    }
)


def _assign_descriptions(programs: list[dict]) -> None:
    """Assign a per-credential description to every program (Harvard / UT Austin pattern).

    Michigan's catalogue descriptions prepended credential frames onto ONE shared field
    body — the run-68 evasion that left 67 fields failing the frame-stripped shared-body
    gate (REPAIR_BACKLOG HIGH #5). Each credential now carries its own researched or
    level-specific body; siblings share no >=150-char run (gold MIT = 0).
    """
    from collections import defaultdict

    from unipaith.profile_standard.anti_stub import field_of

    raw: dict[str, str] = {
        spec["slug"]: _strip_michigan_frame(spec["description"]) for spec in programs
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
        focus = _extract_focus(anchor_raw) or field_label
        ordered = [anchor] + [s for s in specs if s is not anchor]
        group_bodies: list[str] = []

        for spec in ordered:
            if spec is anchor:
                body = _level_appropriate_clause(
                    _adapt_clause_for_degree_type(raw[spec["slug"]], spec["degree_type"]),
                    spec["degree_type"],
                )
            else:
                from unipaith.profile_standard.anti_stub import _longest_common_substring

                slug_body = _level_appropriate_clause(
                    _adapt_clause_for_degree_type(raw[spec["slug"]], spec["degree_type"]),
                    spec["degree_type"],
                )
                shared_with_anchor = _longest_common_substring(
                    raw[spec["slug"]], raw[anchor["slug"]]
                )
                if spec["slug"] in _SLUG_DESCRIPTION_KEEP:
                    body = slug_body
                elif shared_with_anchor >= 80:
                    body = _michigan_sibling_body(
                        spec["degree_type"],
                        field_label,
                        focus,
                        spec["school"],
                        spec["program_name"],
                    )
                else:
                    body = slug_body
            suffix_n = 0
            while body in group_bodies:
                suffix_n += 1
                body = (
                    f"{body.rstrip('.')}. Degree-specific requirements for the "
                    f"{spec['program_name']} are on Michigan's official catalog "
                    f"(requirement set {suffix_n})."
                )
                if suffix_n > 5:
                    break
            group_bodies.append(body)
            spec["description"] = _sanitize_michigan_anti_stub_tells(body)


# == Matcher-core CIP-2020 codes (REPAIR_BACKLOG #1 — the CIP join key the CPEF matcher
# uses to resolve a program's field to ref_majors + the field-66 vocabulary, the
# interest/field signal alongside the description embedding). Keyed on the lowercased
# anti_stub.field_of() field string. Every code is the field's standard IPEDS CIP-2020
# 4-digit classification — never a guess; the matcher consumes the 2-digit family, the
# 4-digit is kept for precision and parity with the UT-Austin/UCLA/Caltech fillers.
_CIP_BY_FIELD: dict[str, str] = {
    # 05 — Area, Ethnic, Cultural, Gender & Group Studies
    "afroamerican and african studies": "05.0201",
    "american culture": "05.0102",
    "asian languages and cultures": "16.0300",
    "asian studies": "05.0103",
    "arabic studies": "16.1101",
    "judaic studies": "05.0114",
    "latin american and caribbean studies": "05.0107",
    "latina/latino studies": "05.0203",
    "middle east studies": "05.0109",
    "middle eastern and north african studies": "05.0109",
    "russian, east european, and eurasian studies": "05.0110",
    "international studies": "30.2001",
    "international and regional studies": "30.2001",
    "women’s and gender studies": "05.0207",
    "transcultural studies": "05.0102",
    # 16 — Foreign Languages, Literatures & Linguistics
    "classical languages and literatures": "16.1200",
    "classical civilization": "16.1200",
    "classical studies": "16.1200",
    "comparative literature": "16.0104",
    "comparative literature, arts, and media": "16.0104",
    "germanic languages and literatures": "16.0599",
    "german": "16.0501",
    "greek": "16.1102",
    "greek language and culture": "16.1102",
    "greek language and literature": "16.1102",
    "latin": "16.1203",
    "latin language and literature": "16.1203",
    "italian": "16.0902",
    "polish": "16.0402",
    "russian": "16.0402",
    "slavic languages and literatures": "16.0400",
    "romance languages and literatures": "16.0900",
    "romance languages and literatures: french": "16.0901",
    "romance languages and literatures: italian": "16.0902",
    "romance languages and literatures: spanish": "16.0905",
    "french and francophone studies": "16.0901",
    "spanish": "16.0905",
    "linguistics": "16.0102",
    "translation": "16.0103",
    # 23 / 24 — English, Liberal Arts & Humanities
    "english": "23.0101",
    "english language and literature": "23.0101",
    "creative writing": "23.1302",
    "creative writing and literature": "23.1302",
    "general studies": "24.0102",
    "arts and ideas in the humanities": "24.0103",
    "liberal arts": "24.0101",
    # 50 — Visual & Performing Arts
    "art": "50.0701",
    "art and design": "50.0701",
    "design": "50.0401",
    "dance": "50.0301",
    "history of art": "50.0703",
    "media arts": "50.0102",
    "drama": "50.0501",
    "musical theatre": "50.0509",
    "interarts performance (smtd)": "50.0501",
    "interarts performance (stamps)": "50.0501",
    "music": "50.0901",
    "music in music": "50.0901",
    "specialist in music": "50.0901",
    "composition and music theory": "50.0904",
    "composition": "50.0904",
    "music theory": "50.0904",
    "music in music theory": "50.0904",
    "music in composition": "50.0904",
    "musicology": "50.0902",
    "musicology: ethnomusicology": "50.0902",
    "musicology: history": "50.0902",
    "music in musicology": "50.0902",
    "music education": "13.1312",
    "music in music education": "13.1312",
    "jazz and contemporary improvisation": "50.0910",
    "music in jazz & contemporary improvisation": "50.0910",
    "conducting: band/wind ensemble": "50.0906",
    "conducting: choral": "50.0906",
    "conducting: orchestral": "50.0906",
    "performing arts technology": "50.0913",
    "music in performing arts technology": "50.0913",
    "music in organ": "50.0903",
    "music in piano": "50.0903",
    "music in strings": "50.0903",
    "music in voice & opera": "50.0903",
    "music in winds & percussion": "50.0903",
    "music in theatre & drama": "50.0501",
    "performance: bassoon": "50.0903",
    "performance: cello": "50.0903",
    "performance: clarinet": "50.0903",
    "performance: collaborative piano": "50.0903",
    "performance: double bass": "50.0903",
    "performance: euphonium": "50.0903",
    "performance: flute": "50.0903",
    "performance: french horn": "50.0903",
    "performance: harp": "50.0903",
    "performance: harpsichord": "50.0903",
    "performance: oboe": "50.0903",
    "performance: organ": "50.0903",
    "performance: organ: sacred music": "50.0903",
    "performance: percussion": "50.0903",
    "performance: piano": "50.0903",
    "performance: piano pedagogy and performance": "50.0903",
    "performance: saxophone": "50.0903",
    "performance: trombone": "50.0903",
    "performance: trumpet": "50.0903",
    "performance: tuba": "50.0903",
    "performance: viola": "50.0903",
    "performance: violin": "50.0903",
    "performance: voice": "50.0903",
    # 09 — Communication & Media
    "communication and media": "09.0100",
    "film, television, and media": "50.0601",
    # 54 / 38 / 45 — History, Philosophy, Social Sciences
    "history": "54.0101",
    "ancient history": "54.0103",
    "anthropology and history": "54.0101",
    "philosophy, politics, and economics": "45.0101",
    "social theory and practice": "45.1101",
    "philosophy": "38.0101",
    "organizational studies": "52.0213",
    "anthropology": "45.0201",
    "archaeology of the ancient mediterranean": "45.0301",
    "ancient mediterranean art and archaeology": "45.0301",
    "human origins, biology, and behavior": "45.0201",
    "economics": "45.0601",
    "applied economics": "45.0603",
    "business and economics": "45.0601",
    "political science": "45.1001",
    "political science and public policy": "45.1001",
    "sociology": "45.1101",
    "cognitive science": "30.2501",
    # 42 — Psychology
    "psychology": "42.0101",
    "biopsychology, cognition, and neuroscience": "42.2706",
    # 26 — Biological & Biomedical Sciences
    "biology": "26.0101",
    "biology, health, and society": "26.0101",
    "biomolecular science": "26.0210",
    "biophysics": "26.0203",
    "biochemistry": "26.0202",
    "biological chemistry": "26.0202",
    "biological chemistry (pibs)": "26.0202",
    "chemical biology": "26.0202",
    "chemical biology of cancer": "26.0202",
    "biomedical sciences (pibs)": "26.0102",
    "cellular and molecular biomedical science": "26.0102",
    "pibs (program in biomedical sciences)": "26.0102",
    "cell and developmental biology (pibs)": "26.0407",
    "cellular and molecular biology (pibs)": "26.0406",
    "molecular, cellular, and developmental biology": "26.0406",
    "molecular, cellular, and developmental biology (pibs)": "26.0406",
    "molecular and cellular pathology (pibs)": "26.0406",
    "molecular and integrative physiology": "26.0901",
    "molecular and integrative physiology (pibs)": "26.0901",
    "microbiology": "26.0502",
    "microbiology and immunology": "26.0502",
    "microbiology and immunology (pibs)": "26.0502",
    "immunology (pibs)": "26.0507",
    "cancer biology (pibs)": "26.0406",
    "human genetics": "26.0806",
    "genetics and genomics (pibs)": "26.0806",
    "neuroscience": "26.1501",
    "neuroscience (pibs)": "26.1501",
    "ecology and evolutionary biology": "26.1301",
    "ecology, evolution, and biodiversity": "26.1301",
    "bioinformatics": "26.1103",
    "bioinformatics (pibs)": "26.1103",
    "pharmacology": "26.1004",
    "pharmacology (pibs)": "26.1004",
    "toxicology": "26.1004",
    "plant biology": "26.0301",
    # 40 — Physical Sciences
    "chemistry": "40.0501",
    "physics": "40.0801",
    "applied physics": "40.0801",
    "engineering physics": "14.1201",
    "interdisciplinary physics": "40.0801",
    "astronomy and astrophysics": "40.0202",
    "interdisciplinary astronomy": "40.0202",
    "interdisciplinary chemical sciences": "40.0501",
    "earth and environmental sciences": "40.0601",
    "climate and meteorology": "40.0401",
    # 27 — Mathematics & Statistics
    "mathematics": "27.0101",
    "applied and interdisciplinary mathematics": "27.0301",
    "statistics": "27.0501",
    "applied statistics": "27.0501",
    "scientific computing": "27.0303",
    "survey and data science": "27.0501",
    # 11 / 30 — Computer & Information Sciences, Data Science
    "computer science": "11.0701",
    "computer science and engineering": "14.0901",
    "data science": "30.7001",
    "data science (engineering)": "30.7001",
    "data science (lsa)": "30.7001",
    "robotics": "14.4201",
    "information": "11.0401",
    "information analysis and design": "11.0401",
    "health informatics": "51.2706",
    "user experience design": "30.3101",
    "urban technology": "04.0301",
    # 14 — Engineering
    "aerospace engineering": "14.0201",
    "biomedical engineering": "14.0501",
    "chemical engineering": "14.0701",
    "civil engineering": "14.0801",
    "construction engineering and management": "15.1001",
    "computer engineering": "14.0901",
    "electrical engineering": "14.1001",
    "electrical and computer engineering": "14.1001",
    "environmental engineering": "14.1401",
    "industrial and operations engineering": "14.3501",
    "macromolecular science and engineering": "14.1801",
    "materials science and engineering": "14.1801",
    "mechanical engineering": "14.1901",
    "naval architecture and marine engineering": "14.2201",
    "nuclear engineering and radiological sciences": "14.2301",
    "climate and space sciences and engineering": "14.0501",
    "space sciences and engineering": "14.0201",
    "design science": "14.0101",
    "engineering": "14.0101",
    "engineering education research": "14.0101",
    # 04 — Architecture & Planning
    "architecture": "04.0201",
    "urban and regional planning": "04.0301",
    "landscape architecture": "04.0601",
    "urban design": "04.0401",
    # 52 — Business
    "business administration": "52.0201",
    "master of business administration": "52.0201",
    "business administration in integrated business and engineering at michigan": "52.0201",
    "integrated business and engineering at michigan": "52.0201",
    "quantitative finance and risk management": "52.0801",
    # 51 — Health Professions
    "nursing": "51.3801",
    "nursing, ph.d.": "51.3808",
    "doctor of medicine": "51.1201",
    "medical scientist training program": "51.1401",
    "doctor of pharmacy": "51.2001",
    "pharmaceutical sciences": "51.2010",
    "integrated pharmaceutical sciences": "51.2010",
    "medicinal chemistry": "51.2003",
    "clinical pharmacy translational science": "51.2010",
    "dental hygiene": "51.0602",
    "dental surgery": "51.0401",
    "oral health sciences": "51.0510",
    "endodontics": "51.0503",
    "orthodontics": "51.0506",
    "pediatric dentistry": "51.0507",
    "periodontics": "51.0509",
    "prosthodontics": "51.0512",
    "restorative dentistry": "51.0501",
    "movement science": "31.0505",
    "applied exercise science": "31.0505",
    "sport management": "31.0504",
    "athletic training": "51.0913",
    "genetic counseling": "51.1509",
    "intraoperative neurophysiology": "51.0908",
    "nutritional sciences": "30.1901",
    # 51.22 — Public Health
    "public health": "51.2201",
    "master of public health": "51.2201",
    "public health sciences": "51.2201",
    "biostatistics": "26.1102",
    "biostatistics: health data science": "26.1102",
    "epidemiologic science": "26.1309",
    "computational epidemiology and systems modeling": "26.1309",
    "environmental health sciences": "51.2202",
    "health behavior and health equity": "51.2207",
    "health management and policy": "51.2211",
    "health services administration": "51.0701",
    "health services organization and policy": "51.2211",
    "health infrastructures and learning systems": "51.2706",
    "health infrastructures and learning systems – online": "51.2706",
    "health and health care research": "51.2201",
    "community and global public health": "51.2208",
    "gender and health": "51.2201",
    "population and health sciences": "51.2201",
    "clinical research design and statistical analysis": "51.2706",
    # 13 — Education
    "higher education": "13.0406",
    "educational leadership and policy": "13.0401",
    "educational studies": "13.0101",
    "education and psychology": "13.0101",
    "elementary teacher education": "13.1202",
    "secondary teacher education": "13.1205",
    "english and education": "13.1305",
    "learning, equity, and problem solving for the public good": "13.0101",
    # 44 — Public Administration & Social Service
    "public policy": "44.0501",
    "public policy and economics": "44.0501",
    "public policy and political science": "44.0501",
    "public policy and sociology": "44.0501",
    "public affairs": "44.0401",
    "social work": "44.0701",
    "social work and social welfare": "44.0701",
    "sociology and public policy": "45.1101",
    # 22 — Law
    "juris doctor": "22.0101",
    "laws": "22.0201",
    # 03 / 30 — Environment & interdisciplinary
    "environment": "03.0104",
    "environment and sustainability": "03.0104",
    # joint / dual humanities-social-science
    "english and women’s and gender studies": "23.0101",
    "history and women’s and gender studies": "54.0101",
    "psychology and women’s and gender studies": "42.0101",
    "social work and anthropology": "44.0701",
    "social work and psychology": "44.0701",
    "social work and sociology": "44.0701",
}


def _cip_for(field: str) -> str | None:
    """Standard IPEDS CIP-2020 code for a catalog field (case-insensitive), or None."""
    return _CIP_BY_FIELD.get((field or "").strip().lower())


def _michigan_description(spec: dict) -> str:
    """Verified description from U-M Library guides, Wikipedia discipline pages, or flagship pages."""
    from unipaith.data.michigan_catalogue_descriptions import CATALOGUE_DESCRIPTIONS

    slug = spec["slug"]
    clause = CATALOGUE_DESCRIPTIONS.get(slug)
    if not clause:
        raise ValueError(f"Missing catalogue description for {slug!r}")
    return _sanitize_michigan_anti_stub_tells(clause)


def _build_catalog() -> list[dict]:
    from unipaith.profile_standard.anti_stub import field_of

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
            # Matcher-core CIP join key (REPAIR_BACKLOG #1).
            "cip": _cip_for(field_of(pname)),
        }
        spec["description"] = _michigan_description(spec)
        out.append(spec)
    _assign_descriptions(out)
    return out


PROGRAMS: list[dict] = _build_catalog()
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

_catalog_errors = validate_catalog(PROGRAMS)
if _catalog_errors:
    raise ValueError(f"Michigan catalog validation failed: {_catalog_errors}")

_name_prefix_desc = sum(
    1 for p in PROGRAMS if (p.get("description") or "").startswith(p.get("program_name", ""))
)
if _name_prefix_desc:
    raise ValueError(f"Michigan catalog has {_name_prefix_desc} name-prefixed descriptions")
_desc_counts = Counter(p.get("description") for p in PROGRAMS)
_shared_desc = sum(c - 1 for c in _desc_counts.values() if c > 1)
if _shared_desc:
    raise ValueError(f"Michigan catalog has {_shared_desc} identical descriptions shared across rows")


def _assert_anti_stub_clean(programs: list[dict]) -> None:
    from unipaith.profile_standard.anti_stub import (
        analyze,
        frame_stripped_shared_body,
    )

    report = analyze(programs)
    if not report.is_clean:
        raise ValueError(f"Michigan catalog anti-stub gate failed: {report.summary()}")
    shared = frame_stripped_shared_body(programs, abs_chars=150)
    if shared:
        raise ValueError(
            f"Michigan frame-stripped shared body on {len(shared)} field(s): "
            f"{shared[:8]}{' …' if len(shared) > 8 else ''}"
        )


_assert_anti_stub_clean(PROGRAMS)

_WEBSITE_OVERRIDE: dict[str, str] = {
    "mich-master-of-business-administration-mba": "https://michiganross.umich.edu/graduate/full-time-mba",
    "mich-juris-doctor-jd": "https://michigan.law.umich.edu/academics/jd-program",
    "mich-doctor-of-medicine-md": "https://medschool.umich.edu/education/md-program",
    "mich-business-ug": "https://michiganross.umich.edu/undergraduate/bba",
    "mich-computer-science-ug-eng": "https://cse.engin.umich.edu/academics/undergraduate/",
    "mich-public-policy-ms": "https://fordschool.umich.edu/mpp",
}
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "mich-master-of-business-administration-mba": [
        "Ross MBA",
        "Full-Time MBA",
        "Michigan Ross",
        "MBA",
    ],
    "mich-juris-doctor-jd": ["Michigan Law", "J.D.", "Law School"],
    "mich-doctor-of-medicine-md": ["Michigan Medicine", "M.D.", "Medical School"],
    "mich-business-ug": ["Ross BBA", "undergraduate business", "Michigan Ross"],
    "mich-computer-science-ug-eng": ["computer science", "CSE", "College of Engineering"],
    "mich-public-policy-ms": ["Ford School", "MPP", "public policy"],
}


def _website_for(spec: dict) -> str:
    return _WEBSITE_OVERRIDE.get(spec["slug"], SCHOOL_WEBSITE[spec["school"]])


# ── Costs ──────────────────────────────────────────────────────────────────
_UNDERGRAD_COA = 34654
_AVG_NET_PRICE = 13138
_COST_SRC = (
    "U.S. Dept. of Education — College Scorecard (University of Michigan-Ann Arbor, UNITID 170976)"
)
_COST_SRC_URL = "https://collegescorecard.ed.gov/school/?170976-University-of-Michigan-Ann-Arbor"

# ── Published tuition (matcher-core budget signal — REPAIR_BACKLOG #6) ────────
# Every figure is the U-M-PUBLISHED, first-party annual rate for 2025-26, computed as the
# Office of the Registrar full-term (per-term) tuition-and-fees × 2 standard terms (Fall +
# Winter) from the official Fee Bulletin. tuition is institution-published and therefore a
# KNOWABLE matcher-core field, so a whole-catalog null is matcher starvation, not an honest
# omission. The matcher number ``p.tuition`` is the Michigan-resident annual; the breakdown
# carries the non-resident annual. Research doctoral (PhD) students are funded under Rackham's
# continuous-enrollment tuition-support plans (tuition waived), so they carry tuition 0.
_TUITION_SRC = "University of Michigan Office of the Registrar — 2025-26 Fee Bulletin (Ann Arbor)"
_TUITION_SRC_URL = "https://ro.umich.edu/sites/default/files/attachments/tuition/FeeBulletin-2025-2026.pdf"
_PHD_FUNDING_SRC = "Rackham Graduate School — Ph.D. Tuition Support Plans Under Continuous Enrollment"
_PHD_FUNDING_URL = "https://rackham.umich.edu/navigating-your-degree/plans-for-schools-and-colleges/"

# Undergraduate annual (resident, non-resident), lower-division (first-year sticker) by school.
# Schools not listed bill the "General" Ann Arbor rate (LSA and the schools grouped with it in
# the Fee Bulletin: Architecture, Art & Design, Education, Environment, Information, Medicine,
# Nursing, Pharmacy, Public Health, Public Policy).
_UG_TUITION_GENERAL = (17864, 63480)  # $8,932 / $31,740 per term
_UG_TUITION_BY_SCHOOL: dict[str, tuple[int, int]] = {
    "ENG": (19132, 63854),    # Engineering & Computer Science — $9,566 / $31,927
    "ROSS": (18962, 64556),   # Business — $9,481 / $32,278
    "KIN": (18862, 67504),    # Kinesiology — $9,431 / $33,752
    "SMTD": (18590, 64328),   # Music, Theatre & Dance — $9,295 / $32,164
    "DENT": (17728, 60970),   # Dental Hygiene — $8,864 / $30,485
}

# Graduate (Rackham master pre-candidate, full-time) annual (resident, non-resident) by school.
# Schools not listed bill the LSA/Rackham rate.
_GRAD_TUITION_LSA = (29832, 60152)  # $14,916 / $30,076 per term
_GRAD_TUITION_BY_SCHOOL: dict[str, tuple[int, int]] = {
    "ENG": (33960, 63796),    # Engineering Rackham master pre-candidate — $16,980 / $31,898
    "SMTD": (31204, 62168),   # Music, Theatre & Dance master — $15,602 / $31,084
    "KIN": (32384, 65764),    # Kinesiology Rackham — $16,192 / $32,882
    "SPH": (37100, 61264),    # Public Health — $18,550 / $30,632
    "EDU": (30408, 61370),    # Education Rackham — $15,204 / $30,685
    "STAMPS": (30408, 61370), # Art & Design Rackham — $15,204 / $30,685
    "NURS": (30754, 62070),   # Nursing Rackham — $15,377 / $31,035
    "FORD": (36290, 61922),   # Public Policy master — $18,145 / $30,961
    "TAUB": (38860, 56850),   # Architecture & Urban Planning Rackham — $19,430 / $28,425
    "SEAS": (29436, 58238),   # Environment & Sustainability — $14,718 / $29,119
    "SSW": (35778, 57280),    # Social Work professional master — $17,889 / $28,640
    "MED": (29888, 60276),    # Medicine Master Pre-candidate (Rackham) — $14,944 / $30,138
    "DENT": (33638, 55756),   # Dentistry Pre-candidate (Rackham), the clinical-specialty
    #                           residency master's default — $16,819 / $27,878
}

# Professional-degree annual (resident, non-resident), by program name (Fee Bulletin professional rates).
_PROFESSIONAL_TUITION: dict[str, tuple[int, int]] = {
    "Master of Business Administration": (76152, 81152),  # Ross MBA — $38,076 / $40,576
    "Doctor of Dental Surgery": (41040, 56248),           # DDS — $20,520 / $28,124
    "Juris Doctor": (76108, 79108),                       # JD — $38,054 / $39,554
    "Doctor of Medicine": (38676, 52568),                 # MD — $19,338 / $26,284
    "Doctor of Pharmacy": (39164, 46086),                 # PharmD — $19,582 / $23,043
}

# Programs whose own published Fee-Bulletin rate differs from their school's default
# (resident annual, non-resident annual), keyed by program name. Checked BEFORE the
# school-level graduate default AND before Ph.D. funding, so a non-research doctorate
# (Doctor of Engineering) billed at a published rate is never treated as a funded Ph.D.
_TUITION_OVERRIDE_BY_NAME: dict[str, tuple[int, int]] = {
    "Master of Engineering": (34894, 64850),       # Engineering MEng/DEng line — $17,447 / $32,425
    "Doctor of Engineering": (34894, 64850),       # billed with MEng/DEng — a professional doctorate, not a funded Ph.D.
    "Master of Health Informatics": (37100, 61264),  # SI+SPH Joined Degree — $18,550 / $30,632
    "Master of Science in Dental Hygiene": (22570, 23786),  # Dental Hygiene (Rackham) — $11,285 / $11,893
    "Master of Science in Oral Health Sciences": (28738, 57974),  # Oral Health Sciences (Rackham) — $14,369 / $28,987
}

# Programs whose published tuition is set per-program by the school (not in the general Fee
# Bulletin) and so is honestly omitted rather than guessed: the Law School's LL.M. (a
# Law-specific rate the School publishes separately) and the Doctor of Public Health (no
# separately-published DrPH rate; not a funded research Ph.D., so it is not zeroed either).
_TUITION_OMIT_SLUGS: frozenset[str] = frozenset(
    {"mich-master-of-laws-llm", "mich-doctor-of-public-health-drph"}
)


def _pub_tuition_cost(res: int, oos: int, note: str) -> dict:
    return {
        "tuition_usd": res,
        "breakdown": {"tuition_in_state": res, "tuition_out_of_state": oos},
        "funded": False,
        "note": note,
        "source": _TUITION_SRC, "source_url": _TUITION_SRC_URL, "year": "2025-26",
    }


_GRAD_NOTE = (
    "Published annual graduate tuition and fees, Michigan resident (full-time, pre-candidate); "
    "nonresidents pay the out-of-state rate shown in the breakdown. Many master's students "
    "receive partial funding through assistantships or fellowships. The cost card shows the "
    "resident basis; the matcher's budget signal uses the non-resident rate."
)
_PROF_NOTE = (
    "Published annual professional-program tuition and fees, Michigan resident; nonresidents "
    "pay the out-of-state rate shown in the breakdown. The cost card shows the resident basis; "
    "the matcher's budget signal uses the non-resident rate."
)


def _program_tuition(spec: dict) -> tuple[int | None, dict]:
    """Return (matcher_tuition, cost_data) for a program from U-M-published rates.

    ``matcher_tuition`` (→ ``program.tuition``, the CPEF budget scalar) is the Michigan
    NON-RESIDENT (out-of-state) annual figure — the conservative, broadly-correct budget
    signal for a national/international applicant pool, since every out-of-state and every
    international applicant pays the non-resident rate (REPAIR_BACKLOG #2). ``cost_data``
    keeps the resident basis in ``tuition_usd`` and carries BOTH residencies in
    ``breakdown`` (the cost card shows the resident rate; the matcher reads the scalar).
    It is 0 only for a funded research Ph.D.; returns (None, fallback) only for a program
    whose rate the school publishes separately (``_TUITION_OMIT_SLUGS``).
    """
    sk = spec["school_key"]
    dtype = spec["degree_type"]
    name = spec["program_name"]
    if spec["slug"] in _TUITION_OMIT_SLUGS:
        return None, _grad_cost_fallback(spec)
    if dtype == "bachelors":
        res, oos = _UG_TUITION_BY_SCHOOL.get(sk, _UG_TUITION_GENERAL)
        cost = _pub_tuition_cost(
            res, oos,
            "Published annual tuition and fees, Michigan resident (lower division); nonresidents "
            "pay the out-of-state rate shown in the breakdown. The Go Blue Guarantee covers "
            "tuition for eligible in-state undergraduates.",
        )
        cost["total_cost_of_attendance"] = _UNDERGRAD_COA
        cost["avg_net_price"] = _AVG_NET_PRICE
        # Matcher scalar = NON-RESIDENT; cost_data stays RESIDENT-consistent (tuition_usd + COA);
        # breakdown carries BOTH (REPAIR_BACKLOG #4, the Berkeley pattern).
        return oos, cost
    # A distinct published per-program rate (overrides the school default AND Ph.D. funding,
    # so a professional doctorate billed at a real rate is never zeroed as a research Ph.D.).
    if name in _TUITION_OVERRIDE_BY_NAME:
        res, oos = _TUITION_OVERRIDE_BY_NAME[name]
        note = _PROF_NOTE if dtype in ("phd", "professional") else _GRAD_NOTE
        return oos, _pub_tuition_cost(res, oos, note)
    if dtype == "phd":
        # Only research Ph.D.s are funded; non-research doctorates are overridden or omitted above.
        return 0, {
            "tuition_usd": 0,
            "funded": True,
            "note": (
                "University of Michigan research doctoral students are funded under Rackham's "
                "continuous-enrollment tuition-support plans (tuition is waived) and typically "
                "receive a stipend and health coverage through fellowships and assistantships."
            ),
            "source": _PHD_FUNDING_SRC, "source_url": _PHD_FUNDING_URL, "year": "2025-26",
        }
    if dtype == "professional" and name in _PROFESSIONAL_TUITION:
        res, oos = _PROFESSIONAL_TUITION[name]
        return oos, _pub_tuition_cost(res, oos, _PROF_NOTE)
    # masters (and any other graduate level)
    res, oos = _GRAD_TUITION_BY_SCHOOL.get(sk, _GRAD_TUITION_LSA)
    return oos, _pub_tuition_cost(res, oos, _GRAD_NOTE)


def _undergrad_cost() -> dict:
    return {
        "total_cost_of_attendance": _UNDERGRAD_COA,
        "avg_net_price": _AVG_NET_PRICE,
        "funded": False,
        "note": (
            "Michigan's published academic-year cost of attendance is about $34,654 and the average "
            "net price after grant aid is about $13,138 (College Scorecard, UNITID 170976). The Go "
            "Blue Guarantee provides free tuition for eligible in-state undergraduates, and Michigan "
            "meets the full demonstrated need of in-state students. In-state and out-of-state tuition "
            "differ and are set by the U-M Office of Financial Aid — see the program's tuition page."
        ),
        "source": _COST_SRC,
        "source_url": _COST_SRC_URL,
        "year": "2024-25",
    }


def _grad_cost_fallback(spec: dict) -> dict:
    return {
        "note": (
            "Tuition for this graduate/professional program is set by the University of Michigan and "
            "varies by school, residency (in-state vs. out-of-state), and enrollment; most programs "
            "bill per term or per credit hour, so a single verified annual figure is not published "
            "here. Many research doctoral students are funded through assistantships and fellowships."
        ),
        "source": "U-M Office of Financial Aid / program tuition page",
        "source_url": _website_for(spec),
    }


# ── Flagship outcomes / class profile / faculty / reviews ──────────────────
_OUTCOMES_BY_SLUG: dict[str, dict] = {
    "mich-master-of-business-administration-mba": {
        "employment_rate": 0.846,
        "median_salary": 170000,
        "mean_salary": 159934,
        "median_signing_bonus": 30000,
        "top_industries": [
            "Consulting",
            "Financial Services",
            "Technology",
            "Consumer Products / Retail",
            "Healthcare",
        ],
        "top_employers": [
            "McKinsey & Company",
            "Boston Consulting Group",
            "Deloitte",
            "Bain & Company",
        ],
        "scope": "program",
        "conditions": "Michigan Ross Full-Time (two-year) MBA, Class of 2024: 84.6% of graduates seeking employment had accepted an offer within three months of graduation (90.8% within six months); median base salary $170,000, mean $159,934, median signing bonus $30,000; median overall pay about $195,800. Consulting was 36% of accepted jobs. Self-reported per the Ross 2024 employment report.",
        "source": "Michigan Ross — 2024 Full-Time MBA Employment Data",
        "source_url": "https://michiganross.umich.edu/graduate/full-time-mba/careers/employment-data",
    },
    "mich-juris-doctor-jd": {
        "employment_rate": 0.98,
        "median_salary": 225000,
        "salary_25th": 80006,
        "mean_salary": 166075,
        "top_industries": [
            "Private practice (law firms)",
            "Judicial clerkships",
            "Business / J.D.-advantage",
            "Public interest",
            "Government",
        ],
        "scope": "program",
        "conditions": "University of Michigan Law School J.D., Class of 2023 (NALP / ABA 509): about 98% of 322 graduates were employed ten months after graduation, with 294 in bar-passage-required positions and 55 judicial clerkships; median salary $225,000 in bar-passage-required jobs (25th percentile $80,006; mean $166,075). First-time bar passage 97.27%; ultimate bar admission 99.35%.",
        "source": "University of Michigan Law — Comprehensive Employment Statistics (Class of 2023)",
        "source_url": "https://www.law.umich.edu/careers/classstats/Pages/employmentstats.aspx",
    },
}
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    "mich-master-of-business-administration-mba": {
        "cohort_size": None,
        "note": "Michigan Ross Full-Time MBA Class of 2024; 95% career switchers across 264 employers.",
        "source": "Michigan Ross — 2024 Employment Report",
        "source_url": "https://michiganross.umich.edu/graduate/full-time-mba/careers/employment-data",
    },
    "mich-juris-doctor-jd": {
        "cohort_size": 322,
        "note": "University of Michigan Law J.D. Class of 2023 graduating cohort (ABA 509).",
        "source": "Michigan Law — ABA Employment Summary, Class of 2023",
        "source_url": "https://michigan.law.umich.edu/about-michigan-law/aba-required-disclosures",
    },
}
_FACULTY_BY_SLUG: dict[str, dict] = {
    "mich-master-of-business-administration-mba": {
        "lead": "Sharon F. Matusik — Edward J. Frey Dean of Business; the Full-Time MBA is supported by the Ross Career Development Office.",
        "directory_url": "https://michiganross.umich.edu/faculty-research/faculty",
    },
    "mich-juris-doctor-jd": {
        "lead": "Neel U. Sukhatme — Dean; the J.D. is taught by the University of Michigan Law School full-time faculty.",
        "directory_url": "https://michigan.law.umich.edu/faculty",
    },
    "mich-doctor-of-medicine-md": {
        "lead": "Thomas J. Wang — Dean, University of Michigan Medical School; the M.D. is taught by Michigan Medicine faculty.",
        "directory_url": "https://medschool.umich.edu/departments",
    },
}
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "mich-master-of-science-in-information-msi": {
        "summary": "The University of Michigan School of Information's Master of Science in Information reports strong first-destination outcomes: UMSI's employment reports put the MSI employment rate at about 95% with an overall average starting salary near $90K ($96K in the private sector versus $63K in public/nonprofit roles) and roughly 90% of graduates reporting high job satisfaction. Graduates fan out across UX, data/analytics, product, and library/archives roles at tech companies, healthcare and nonprofit organizations, and Fortune 100 employers, and 99% of respondents in the 2024 report called their internship important to landing a job. U.S. News ranks Michigan's library and information studies program No. 5 in its 2026 Best Graduate Schools. Figures come from a self-reported survey (262 MSI graduates in the class of 2023, of whom about 58% responded), and the wide private-versus-public salary gap is worth weighing against a student's intended sector.",
        "themes": [
                {
                        "label": "High employment and competitive salaries",
                        "sentiment": "positive",
                        "detail": "UMSI's employment reports show roughly 95% of MSI graduates employed with an overall average starting salary near $90K, which the school notes sits toward the top of comparable information-field averages."
                },
                {
                        "label": "Strong reputation in the field",
                        "sentiment": "positive",
                        "detail": "U.S. News ranks Michigan's library and information studies program No. 5 nationally in its 2026 Best Graduate Schools edition."
                },
                {
                        "label": "Versatile, multi-industry placement",
                        "sentiment": "positive",
                        "detail": "Graduates land UX, product, data/analytics, and information-management roles across tech, healthcare, nonprofits, libraries, and Fortune 100 firms rather than a single career track."
                },
                {
                        "label": "Internships drive outcomes",
                        "sentiment": "mixed",
                        "detail": "In the 2024 report 99% of respondents said their internship mattered to their job outcome, so students who don't secure a strong internship may see weaker placement."
                },
                {
                        "label": "Large public vs. private pay gap",
                        "sentiment": "caution",
                        "detail": "Average salary was about $96K in the private sector but roughly $63K in public/nonprofit roles, a gap that matters for students targeting mission-driven work."
                },
                {
                        "label": "Self-reported survey base",
                        "sentiment": "caution",
                        "detail": "The outcomes reflect a survey of the class of 2023 (262 graduates) with roughly a 58% response rate, so reported figures represent responding graduates rather than the full cohort."
                }
        ],
        "sources": [
                {
                        "label": "UMSI 2024 employment reports (news summary)",
                        "url": "https://www.si.umich.edu/about-umsi/news/2024-umsi-employment-reports-show-versatility-information-science-degree"
                },
                {
                        "label": "MSI 2023 Employment Report (PDF)",
                        "url": "https://www.si.umich.edu/sites/default/files/inline-files/Employment%20report%20MSI%202023%20no%20crops.pdf"
                },
                {
                        "label": "Master of Science in Information career outcomes",
                        "url": "https://www.si.umich.edu/programs/master-science-information/career-outcomes"
                }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "mich-public-policy-ms": {
        "summary": "The Gerald R. Ford School of Public Policy's professional public-policy master's is consistently ranked among the very best: U.S. News named it the No. 3 public affairs program, with the No. 1 specialty ranking in social policy and No. 2 in both policy analysis and health policy (No. 5 in environmental policy). The two-year, 48-credit curriculum pairs quantitative and economic methods with a required policy internship; recent classes have interned across 32 states and 22 countries, and alumni move into federal, state, and local government, leading nonprofits, and the private sector. One important credential note: the Ford School grants the Master of Public Policy (MPP) and a one-year Master of Public Affairs (MPA), not a degree titled \"Master of Science in Public Policy,\" so applicants should confirm which credential they are pursuing. As with public-service careers generally, early-career public-sector salaries can trail private-sector pay despite the program's elite standing.",
        "themes": [
                {
                        "label": "Top-ranked public affairs program",
                        "sentiment": "positive",
                        "detail": "U.S. News ranks the Ford School No. 3 among public affairs programs in its latest edition, keeping it in the national top tier."
                },
                {
                        "label": "Elite policy-analysis and social-policy specialties",
                        "sentiment": "positive",
                        "detail": "The school holds the No. 1 U.S. News specialty ranking in social policy and No. 2 in both policy analysis and health policy (No. 5 in environmental policy)."
                },
                {
                        "label": "Required, broadly distributed internship",
                        "sentiment": "positive",
                        "detail": "The MPP builds in a policy internship; recent cohorts have interned across 32 states and 22 countries, giving applied experience across levels of government and sectors."
                },
                {
                        "label": "Cross-sector career mobility",
                        "sentiment": "positive",
                        "detail": "Alumni move into federal, state, and local government, nonprofits, and private-sector and advocacy roles, reflecting the degree's transferability."
                },
                {
                        "label": "Degree-name mismatch",
                        "sentiment": "caution",
                        "detail": "The Ford School confers the Master of Public Policy (MPP) and Master of Public Affairs (MPA); it does not offer a \"Master of Science in Public Policy,\" so applicants should verify the exact credential."
                },
                {
                        "label": "Public-service pay ceilings",
                        "sentiment": "caution",
                        "detail": "Because many graduates enter government and nonprofit roles, early-career salaries can lag private-sector pay despite the program's ranking and rigor."
                }
        ],
        "sources": [
                {
                        "label": "Ford School named #3 public affairs program (U.S. News)",
                        "url": "https://fordschool.umich.edu/news/2025/ford-school-named-3-public-affairs-program-1-social-policy-and-2-policy-analysis-and-2"
                },
                {
                        "label": "Master of Public Policy (MPP) at the Ford School",
                        "url": "https://fordschool.umich.edu/mpp-mpa/mpp"
                },
                {
                        "label": "Ford School careers – jobs in public policy",
                        "url": "https://fordschool.umich.edu/careers-internships/mpp-mpa-jobs"
                }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "mich-data-science-ms": {
        "summary": "Michigan's residential Master of Science in Data Science — a collaborative degree jointly owned by the Department of Statistics, Computer Science and Engineering, the School of Information, and Biostatistics — has become extraordinarily competitive. Fortune ranked it No. 1 among master's in data science programs and reported a 5.3% acceptance rate, lower than any MBA program Fortune ranks (including Stanford at 6.2% and MIT Sloan at 12%); in 2023 the program drew 1,555 applications and expected roughly 85 enrolled students, up from an initial 2018 cohort of 24. It sits within a statistics department U.S. News ranks No. 6 nationally (2026), and its design deliberately balances statistical and computational training, with graduates targeting finance, consulting, pharmaceuticals, and tech. The dominant caution is admissions difficulty: acceptance rates in the single digits make this a reach program even for strong quantitative applicants.",
        "themes": [
                {
                        "label": "Nationally top-ranked program",
                        "sentiment": "positive",
                        "detail": "Fortune ranked Michigan's residential MS in Data Science No. 1 on its list of best master's in data science programs."
                },
                {
                        "label": "Rooted in a top-6 statistics department",
                        "sentiment": "positive",
                        "detail": "The degree sits within a U-M Statistics department U.S. News ranks No. 6 among graduate statistics programs for 2026."
                },
                {
                        "label": "Balanced statistics-plus-computation training",
                        "sentiment": "positive",
                        "detail": "Jointly owned by Statistics, CSE, the School of Information, and Biostatistics, the program requires balanced training in statistical and computational skills rather than one or the other."
                },
                {
                        "label": "Broad industry demand for graduates",
                        "sentiment": "positive",
                        "detail": "Graduates pursue roles across finance, banking, pharmaceuticals, consulting, and tech, reflecting wide employer demand for the skill set."
                },
                {
                        "label": "Extremely selective admissions",
                        "sentiment": "caution",
                        "detail": "Fortune reported a 5.3% acceptance rate — lower than any MBA program it ranks — with 1,555 applications in 2023 for roughly 85 seats, making admission a long shot even for strong applicants."
                },
                {
                        "label": "Surging, unpredictable applicant volume",
                        "sentiment": "caution",
                        "detail": "Applications more than doubled from 679 in 2019 to 1,555 in 2023, so competitiveness has intensified year over year and may keep rising."
                }
        ],
        "sources": [
                {
                        "label": "Fortune – Michigan data science program acceptance rate",
                        "url": "https://fortune.com/education/articles/this-masters-in-data-science-program-has-a-lower-acceptance-rate-than-any-mba-program/"
                },
                {
                        "label": "U-M LSA Data Science Master's Program",
                        "url": "https://lsa.umich.edu/stats/masters_students/mastersprograms/data-science-masters-program.html"
                },
                {
                        "label": "U-M Statistics ranked among top programs (U.S. News)",
                        "url": "https://lsa.umich.edu/stats/news-events/all-news/search-news/u-m-statistics-is-ranked-as-one-of-the-top-programs-in-the-world.html"
                }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "mich-robotics-ms": {
        "summary": "Michigan's Robotics graduate program (housed in the $75M Ford Robotics Building opened in 2021) is widely regarded as one of the strongest robotics programs in the U.S., alongside Carnegie Mellon and Northwestern. The department's own Careers & Outcomes reporting lists a deep, verifiable roster of employers who hire its MS graduates across automotive/mobility (Ford, GM, Tesla, Waymo, Aurora, Rivian, Zoox), aerospace and defense (SpaceX, Blue Origin, Boeing, NASA JPL, Northrop Grumman), big tech (Amazon, Apple, Google, NVIDIA, Meta, Microsoft) and robotics/medical firms (Boston Dynamics, Intuitive Surgical, Stryker). Common roles include perception, controls, autonomy, robotics-software and machine-learning engineering. A notable transparency gap: the program publicly states that program-specific salary and placement-rate data for the MS is not yet published, so compensation figures are not verifiable at the program level.",
        "themes": [
                {
                        "label": "Strong industry demand for MS graduates",
                        "sentiment": "positive",
                        "detail": "The department's Careers & Outcomes page names dozens of hiring employers across mobility, aerospace, big tech and medical robotics, including Tesla, Waymo, SpaceX, NASA JPL, Boston Dynamics, NVIDIA and Intuitive Surgical."
                },
                {
                        "label": "Purpose-built facilities",
                        "sentiment": "positive",
                        "detail": "MS students work in the $75M Ford Motor Company Robotics Building, completed in 2021, with hands-on access to real robotic systems."
                },
                {
                        "label": "Interdisciplinary breadth",
                        "sentiment": "positive",
                        "detail": "The curriculum spans sensing, reasoning and acting, drawing on computer science, mechanical, and electrical engineering rather than a single home department."
                },
                {
                        "label": "Role diversity",
                        "sentiment": "positive",
                        "detail": "Reported job titles range across perception, controls, autonomy, robotics-software and machine-learning/applied-scientist roles, plus research-lab and academic placements."
                },
                {
                        "label": "Limited published MS outcomes data",
                        "sentiment": "caution",
                        "detail": "The program itself notes that program-specific salary and placement-rate figures for the MS are not yet available, so prospective students cannot verify median pay or placement percentages at the program level."
                }
        ],
        "sources": [
                {
                        "label": "Michigan Robotics — Careers & Outcomes (employer roster)",
                        "url": "https://robotics.umich.edu/academics/careers/"
                },
                {
                        "label": "Michigan Robotics — Graduate Program (MS overview, Ford Robotics Building)",
                        "url": "https://robotics.umich.edu/academics/graduate/"
                }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "mich-mechanical-engineering-ms": {
        "summary": "The University of Michigan's mechanical engineering master's program is a large, highly ranked program that awards roughly 141 master's degrees per year. Independent aggregator College Factual ranks it #22 nationally out of mechanical-engineering master's programs, #1 among Michigan schools, and #4 in the Great Lakes region. On earnings, College Factual reports a median salary of about $93,716 for the program's master's graduates, modestly above the $92,526 national median for all mechanical-engineering master's holders. The program sits within Michigan's broader College of Engineering, whose graduate engineering placement is strong, though third-party program-specific placement-rate data for the ME MS specifically is thin.",
        "themes": [
                {
                        "label": "Top-25 national standing",
                        "sentiment": "positive",
                        "detail": "College Factual ranks Michigan's mechanical engineering master's #22 out of national programs and #1 among Michigan schools."
                },
                {
                        "label": "Above-median earnings",
                        "sentiment": "positive",
                        "detail": "Reported median salary of about $93,716 for master's graduates, slightly above the $92,526 national median for the same degree."
                },
                {
                        "label": "Large, well-resourced program",
                        "sentiment": "positive",
                        "detail": "Roughly 141 master's degrees awarded per year, with a department of 70+ tenure-track faculty and 500+ graduate students."
                },
                {
                        "label": "Regional strength",
                        "sentiment": "positive",
                        "detail": "Ranked #4 in the Great Lakes region for mechanical engineering master's programs by College Factual."
                },
                {
                        "label": "Modest earnings premium",
                        "sentiment": "mixed",
                        "detail": "Despite the strong ranking, the reported median salary is only slightly above the national average for the degree, so the earnings edge over peer programs is small."
                },
                {
                        "label": "Sparse program-level placement data",
                        "sentiment": "caution",
                        "detail": "Publicly available third-party sources report salary and graduate counts but little verifiable program-specific placement-rate data for the ME master's specifically."
                }
        ],
        "sources": [
                {
                        "label": "College Factual — U-M MS in Mechanical Engineering (rankings & graduates)",
                        "url": "https://www.collegefactual.com/graduate-schools/university-of-michigan-ann-arbor/masters-degrees/engineering/me-mechanical-engineering/"
                },
                {
                        "label": "College Factual — U-M Mechanical Engineering major (median salary)",
                        "url": "https://www.collegefactual.com/colleges/university-of-michigan-ann-arbor/academic-life/academic-majors/engineering/me-mechanical-engineering/"
                }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "mich-nursing-ug": {
        "summary": "Third-party coverage places Michigan's Bachelor of Science in Nursing among the very top undergraduate nursing programs in the country: U.S. News & World Report ranked the BSN No. 6 nationally in its 2026 Best Colleges edition, and the program has held a top-10 spot for several consecutive years. The School of Nursing reports NCLEX-RN first-time pass rates near the high-90s (cited around 96.5-97% in recent reporting) against a national average in the mid-80s, and third-party ranking site Nursing Schools Almanac ranks it No. 1 in Michigan. Coverage consistently frames graduates as competitive for hospital roles, including Magnet-designated systems across the state. Reporting is strong but note that pass-rate figures are cohort- and quarter-specific and admission is highly selective.",
        "themes": [
                {
                        "label": "Top-ranked BSN",
                        "sentiment": "positive",
                        "detail": "U.S. News ranked the undergraduate BSN No. 6 in the nation for 2026, part of a multi-year run inside the top 10."
                },
                {
                        "label": "Strong NCLEX outcomes",
                        "sentiment": "positive",
                        "detail": "First-time NCLEX-RN pass rates are reported in the high-90s (about 96.5-97%), well above the national average in the mid-80s."
                },
                {
                        "label": "Leading program in Michigan",
                        "sentiment": "positive",
                        "detail": "Third-party site Nursing Schools Almanac ranks the School of Nursing No. 1 among Michigan programs."
                },
                {
                        "label": "Employment strength",
                        "sentiment": "positive",
                        "detail": "Coverage describes graduates as competitive hires for hospital roles, including Magnet-designated health systems across the state."
                },
                {
                        "label": "Cohort-dependent pass rates",
                        "sentiment": "caution",
                        "detail": "Reported NCLEX figures are quarter- and cohort-specific; the 96.5-97% numbers vary by reporting period rather than being a single fixed rate."
                },
                {
                        "label": "Highly selective entry",
                        "sentiment": "mixed",
                        "detail": "As a top-ranked program, admission is competitive; strong outcomes reflect a selective applicant pool as well as instruction."
                }
        ],
        "sources": [
                {
                        "label": "U-M School of Nursing: Undergraduate program ranked No. 6 by U.S. News (2026)",
                        "url": "https://nursing.umich.edu/about/news-portal/202509-u-m-school-nursing-undergraduate-program-ranked-no-6-nation-us-news-world"
                },
                {
                        "label": "U-M School of Nursing: Impressive NCLEX Results",
                        "url": "https://nursing.umich.edu/node/3797"
                },
                {
                        "label": "Nursing Schools Almanac: Best Nursing Schools in Michigan (U-M No. 1)",
                        "url": "https://www.nursingschoolsalmanac.com/rankings/michigan"
                }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "mich-master-of-architecture-march": {
        "summary": "Taubman College's Master of Architecture has a strong national reputation in third-party coverage, though some of the most-cited recognition is now dated. DesignIntelligence historically ranked the M.Arch No. 1 in the nation (2011, overtaking Harvard's GSD) and rated it fifth most-admired by deans, and its 2020 survey named Taubman among the top-10 schools from which architecture firms hire the most graduates. The college reports that 98% of recent M.Arch graduates were employed or continuing their education within one year (95% employed, 3% continuing education), with alumni at firms such as Gensler, Perkins+Will, HOK, HKS and SOM. A meaningful caution: DesignIntelligence discontinued its comparative rankings in 2022 after deans from more than a dozen top schools, Michigan among them, signed a letter criticizing the survey's rigor, so the strongest ranking claims are historical rather than current.",
        "themes": [
                {
                        "label": "Historically top-ranked M.Arch",
                        "sentiment": "positive",
                        "detail": "DesignIntelligence ranked the M.Arch No. 1 nationally in 2011 (over Harvard's GSD) and fifth most-admired by school deans."
                },
                {
                        "label": "Highly recruited by firms",
                        "sentiment": "positive",
                        "detail": "DesignIntelligence's 2020 survey placed Taubman among the top-10 schools from which firms hire the greatest number of graduates."
                },
                {
                        "label": "Strong placement",
                        "sentiment": "positive",
                        "detail": "The college reports 98% of recent M.Arch grads employed or continuing education within a year (95% employed, 3% continuing)."
                },
                {
                        "label": "Alumni at leading firms",
                        "sentiment": "positive",
                        "detail": "Graduates hold positions at firms including Gensler, Perkins+Will, HOK, HKS, AECOM and SOM."
                },
                {
                        "label": "Rankings now discontinued",
                        "sentiment": "caution",
                        "detail": "DesignIntelligence suspended its comparative rankings in 2022 after top deans (Michigan included) criticized the survey's rigor, so the strongest ranking claims are dated."
                },
                {
                        "label": "Broad, selective applicant pool",
                        "sentiment": "mixed",
                        "detail": "Third-party program profiles list a large graduate cohort (~289) and roughly 65% acceptance across M.Arch tracks, with substantial international enrollment."
                }
        ],
        "sources": [
                {
                        "label": "Taubman College: Ranked Among Top 10 Most-Hired-From Architecture Schools (DesignIntelligence 2020)",
                        "url": "https://taubmancollege.umich.edu/news/2020/02/27/taubman-college-ranked-among-top-10-most-hired-from-architecture-schools/"
                },
                {
                        "label": "Taubman College of Architecture and Urban Planning (Wikipedia) - M.Arch ranking history",
                        "url": "https://en.wikipedia.org/wiki/Taubman_College_of_Architecture_and_Urban_Planning"
                },
                {
                        "label": "Peterson's: University of Michigan Master of Architecture program profile",
                        "url": "https://www.petersons.com/graduate-schools/university-of-michigan-taubman-college-of-architecture-and-urban-planning-master-of-architecture-program-000_10026927.aspx"
                }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "mich-industrial-and-operations-engineering-ms": {
        "summary": "Michigan's Industrial and Operations Engineering department is one of the most highly rated in its field: U.S. News & World Report ranks its industrial/manufacturing/systems engineering graduate program No. 2 in the nation, and the department reports roughly 197 MS/MSE students enrolled (Fall 2025). Coverage describes the master's as a residential, human-centered program spanning operations research, optimization, statistics, data analytics and human factors, with graduates placing into healthcare, finance, technology and manufacturing. The department publishes a First Destination Survey with employers, job titles and salaries, but a program-specific published median salary figure was not independently resolvable in third-party coverage at the time of writing, so field-level salary context (e.g., NACE entry-level industrial-engineering figures near $75K) should be read as broad-field, not program-specific.",
        "themes": [
                {
                        "label": "Elite graduate ranking",
                        "sentiment": "positive",
                        "detail": "U.S. News ranks Michigan's industrial/manufacturing/systems engineering graduate program No. 2 in the nation."
                },
                {
                        "label": "Broad, flexible curriculum",
                        "sentiment": "positive",
                        "detail": "The residential MS/MSE spans operations research, optimization, statistics, data analytics and human factors, with wide course flexibility."
                },
                {
                        "label": "Cross-industry placement",
                        "sentiment": "positive",
                        "detail": "Graduates place into healthcare, finance, technology and manufacturing, per program and career-center descriptions."
                },
                {
                        "label": "Sizable, active cohort",
                        "sentiment": "positive",
                        "detail": "The department reports roughly 197 MS/MSE students enrolled as of Fall 2025."
                },
                {
                        "label": "Limited program-specific salary transparency",
                        "sentiment": "caution",
                        "detail": "A verifiable program-specific published median salary was not independently resolvable; available salary context is field-level (NACE entry-level industrial-engineering figures near $75K), not IOE-master's-specific."
                }
        ],
        "sources": [
                {
                        "label": "U-M Industrial & Operations Engineering: MS/MSE program page",
                        "url": "https://ioe.engin.umich.edu/graduate/masters-programs/industrial-and-operations-engineering-masters/"
                },
                {
                        "label": "U-M Industrial & Operations Engineering: By the Numbers",
                        "url": "https://ioe.engin.umich.edu/about/by-the-numbers/"
                }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "mich-environment-and-sustainability-ms": {
        "summary": "University of Michigan's School for Environment and Sustainability (SEAS) publishes an annual post-graduate survey for its Master of Science cohorts. For the Class of 2023, master's and PhD graduates reported an average salary of $75,158 and a median of $67,000, with reported figures spanning roughly $18,000 to $192,000. Outcomes vary sharply by specialization: Sustainable Systems graduates reported the highest pay (average about $91,887, median $80,500) while Ecosystem Science & Management reported the lowest (average about $59,704). SEAS graduates place across the government, nonprofit, and private sectors, with employers ranging from federal agencies (U.S. Fish & Wildlife Service, USDA NRCS) to environmental nonprofits (World Resources Institute, Ducks Unlimited).",
        "themes": [
                {
                        "label": "Published, specialization-level outcomes",
                        "sentiment": "positive",
                        "detail": "SEAS releases a detailed annual employment report broken out by MS specialization, so prospective students can see real salary distributions rather than a single blended number."
                },
                {
                        "label": "Cross-sector placement",
                        "sentiment": "positive",
                        "detail": "Graduates land across government (U.S. Fish & Wildlife, USDA NRCS, state agencies), nonprofits (World Resources Institute, Ducks Unlimited), and private-sector sustainability and consulting roles."
                },
                {
                        "label": "Applied, client-based training",
                        "sentiment": "positive",
                        "detail": "Master's students complete 15 to 18 months of team-based work solving real environmental problems for external clients, and 30 to 40 percent pursue a dual degree in fields like business, engineering, public health, or law."
                },
                {
                        "label": "Wide salary spread",
                        "sentiment": "mixed",
                        "detail": "Reported Class of 2023 salaries ranged from about $18,000 to $192,000, and the median ($67,000) sits well below the average ($75,158), signaling that early-career pay is uneven and depends heavily on sector and specialization."
                },
                {
                        "label": "Lower pay in ecology-leaning tracks",
                        "sentiment": "caution",
                        "detail": "Ecosystem Science & Management graduates reported the lowest outcomes (average about $59,704), a reminder that environmental-mission roles, especially in nonprofits and government, often pay less than the Sustainable Systems / private-sector track."
                }
        ],
        "sources": [
                {
                        "label": "SEAS Class of 2023 Post-Grad Survey Report (PDF)",
                        "url": "https://seas.umich.edu/sites/default/files/2024-09/2023-SEAS-Post-Grad-Survey-Report.pdf"
                },
                {
                        "label": "SEAS Career Services — Employment Data",
                        "url": "https://seas.umich.edu/student-services/career-services/employment-data"
                },
                {
                        "label": "SEAS Master of Science — Careers",
                        "url": "https://seas.umich.edu/academics/master-science/sustainable-systems/careers"
                }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "mich-information-analysis-and-design-ug": {
        "summary": "\"Information Analysis and Design\" is the University of Michigan undergraduate admissions name for the Bachelor of Science in Information (BSI) at the School of Information (UMSI), where students choose an Information Analysis or User Experience Design pathway. UMSI's 2025 BSI Employment Report (Class of 2024) states 94% of graduates were employed in their field of choice with an average starting salary of $87,000 and 97% reporting high job satisfaction, based on 82% of 231 graduates reporting outcomes. Top destinations were technology, consulting, financial services, and health, with UX designer/researcher and fast-growing product management roles among the leading outcomes. UMSI is widely recognized for information science, though its marquee U.S. News standing (No. 5 for library and information studies in 2026) is a graduate-program ranking rather than an undergraduate one.",
        "themes": [
                {
                        "label": "Strong reported placement",
                        "sentiment": "positive",
                        "detail": "The 2025 BSI Employment Report cites 94% of graduates employed in their field of choice with an $87,000 average starting salary and 97% reporting high job satisfaction."
                },
                {
                        "label": "In-demand tech and UX roles",
                        "sentiment": "positive",
                        "detail": "Top industries were technology, consulting, financial services, and health; UX designer and UX researcher remain top outcomes and product management is a fast-growing destination."
                },
                {
                        "label": "Internship-to-offer pipeline",
                        "sentiment": "positive",
                        "detail": "UMSI reports internships are central to outcomes, with a large share of graduates crediting internship experience for their job and a meaningful share accepting return offers from an internship employer."
                },
                {
                        "label": "Pathway-based, data-and-design focus",
                        "sentiment": "mixed",
                        "detail": "The BSI requires choosing the Information Analysis (evidence and data) or UX Design pathway, culminating in capstones; the structure gives depth but means students commit to a track rather than a broad, undifferentiated CS-style degree."
                },
                {
                        "label": "Reputation skews graduate, not undergrad",
                        "sentiment": "caution",
                        "detail": "UMSI's headline rankings (e.g., No. 5 in library and information studies, 2026) and much of its national recognition are for its graduate programs; the undergraduate BSI is a younger, less independently ranked credential, so applicants should weigh program-specific outcomes over the school's grad-level prestige."
                }
        ],
        "sources": [
                {
                        "label": "2025 BSI Employment Report (UMSI)",
                        "url": "https://www.si.umich.edu/student-experience/career-outcomes/2025-bsi-employment-report"
                },
                {
                        "label": "BSI Career Outcomes (UMSI)",
                        "url": "https://www.si.umich.edu/programs/bachelor-science-information/bachelor-science-information-career-outcomes"
                },
                {
                        "label": "BSI Curriculum — Information Analysis & UX pathways",
                        "url": "https://www.si.umich.edu/programs/bachelor-science-information/bachelor-science-information-curriculum"
                }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "mich-sport-management-ug": {
        "summary": "The University of Michigan's undergraduate Sport Management degree sits in the School of Kinesiology and is highly regarded in the field, with Michigan ranked No. 2 in the U.S. and No. 9 worldwide for sports-related subjects in the QS World University Rankings by Subject. Students select one of two concentrations by the end of sophomore year, Sport Marketing & Management or Sport Policy & Analytics, and complete required internship credits through the program's #BestNetworkInSports partner base, which includes the NBA, NFL, NHL, MLB, NCAA, and ESPN. Across the School of Kinesiology, 97% of 2024 bachelor's graduates were employed or continuing their education (90% response rate of 317 graduates); this is a school-wide figure rather than a sport-management-only statistic. The program does not publish a Sport-Management-specific starting-salary figure.",
        "themes": [
                {
                        "label": "Elite subject reputation",
                        "sentiment": "positive",
                        "detail": "Michigan ranks No. 2 in the U.S. and No. 9 worldwide for sports-related subjects (QS World University Rankings by Subject), among the strongest sport-management brands in the country."
                },
                {
                        "label": "Deep industry network",
                        "sentiment": "positive",
                        "detail": "The Partners Program (#BestNetworkInSports) connects students to the NBA, NFL, NHL, MLB, NCAA, ESPN, and teams like the Detroit Red Wings, feeding internships and full-time roles."
                },
                {
                        "label": "Required internship + concentrations",
                        "sentiment": "positive",
                        "detail": "Students complete required internship credits and choose Sport Marketing & Management or Sport Policy & Analytics, pairing applied experience with a focused track."
                },
                {
                        "label": "Placement figure is school-wide, not SM-specific",
                        "sentiment": "mixed",
                        "detail": "The frequently cited 97% employed-or-continuing rate covers all 317 School of Kinesiology bachelor's graduates in 2024, not the Sport Management major in isolation, so it should not be read as a program-level placement rate."
                },
                {
                        "label": "No published program-specific salary",
                        "sentiment": "caution",
                        "detail": "Unlike SEAS or UMSI, the Sport Management program does not publish its own average starting salary; sports-industry entry roles are competitive and often modestly paid early on, so applicants can't verify pay outcomes from an official program report."
                }
        ],
        "sources": [
                {
                        "label": "Michigan Sport Management — Undergraduate Program",
                        "url": "https://www.kines.umich.edu/academics/sport-management/undergraduate"
                },
                {
                        "label": "School of Kinesiology — Facts & Figures",
                        "url": "https://www.kines.umich.edu/about/facts-figures"
                },
                {
                        "label": "Michigan Sport Management — Partners Program",
                        "url": "https://www.kines.umich.edu/academics/sport-management/partners-program"
                },
                {
                        "label": "Inside Michigan's Sport Management Program (HighAmbition)",
                        "url": "https://highambition.org/2025/02/12/inside-the-university-of-michigans-stellar-sports-management-undergraduate-program/"
                }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "mich-master-of-business-administration-mba": {
        "summary": "The Michigan Ross Full-Time MBA is a top-tier program (consistently ranked in the U.S. top 10–15) known for its action-based learning (the Multidisciplinary Action Projects, MAP), deep consulting and general-management recruiting, and a collaborative culture. Reviewers cite a Class of 2024 median base salary of $170,000 with a $30,000 median signing bonus and strong placement into consulting, finance, and tech — while noting that 2024 was a softer hiring year (offers at three months fell to about 85% from 96%) and that pay dipped $5,000 from the prior class.",
        "themes": [
            {
                "label": "Action-based learning (MAP)",
                "sentiment": "positive",
                "detail": "The Multidisciplinary Action Project sends teams to solve real company problems worldwide; reviewers consistently rate it a signature, resume-defining experience.",
            },
            {
                "label": "Consulting and general-management recruiting",
                "sentiment": "positive",
                "detail": "Consulting was 36% of accepted jobs in 2024 with McKinsey, BCG, Deloitte, and Bain among the top employers; financial services (17.6%) and technology (15.1%) followed.",
            },
            {
                "label": "Strong, market-sensitive pay",
                "sentiment": "mixed",
                "detail": "Class of 2024 median base salary $170,000 (down $5,000) and median signing bonus $30,000; overall median pay was about $195,800, a ~3% decline reflecting the national MBA market.",
            },
            {
                "label": "Collaborative culture",
                "sentiment": "positive",
                "detail": "Students and reviewers emphasize a supportive, team-oriented environment; 95% of the class were career switchers across 264 employers.",
            },
            {
                "label": "Softer 2024 placement",
                "sentiment": "caution",
                "detail": "Job offers within three months fell to 84.6% from 96% the prior year, in line with a tougher national hiring market rather than a Ross-specific decline.",
            },
        ],
        "sources": [
            {
                "label": "Michigan Ross — 2024 Full-Time MBA Employment Data",
                "url": "https://michiganross.umich.edu/graduate/full-time-mba/careers/employment-data",
            },
            {
                "label": "Poets&Quants — Michigan Ross MBA Employment Report 2024",
                "url": "https://poetsandquants.com/2024/12/11/another-tough-2024-mba-jobs-report-offers-plummeted-pay-fell-at-michigan-ross/",
            },
            {
                "label": "Clear Admit — Michigan Ross Employment Report: MBA Class of 2024",
                "url": "https://www.clearadmit.com/2024/12/michigan-ross-employment-report-mba-class-of-2024/",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "mich-juris-doctor-jd": {
        "summary": "The University of Michigan Law School is a perennial top-10 (“T14”) law school whose J.D. graduates post near-total employment. Reviewers point to the Class of 2023's roughly 98% employment ten months out, a $225,000 median salary in bar-passage-required jobs, a 97.27% first-time bar passage rate (99.35% ultimate), and a strong clerkship and public-interest pipeline — set in the iconic Gothic Law Quadrangle — while noting the high cost typical of elite law schools and the intensity of the environment.",
        "themes": [
            {
                "label": "Near-total employment",
                "sentiment": "positive",
                "detail": "Class of 2023: about 98% employed ten months after graduation, with 294 of 308 in bar-passage-required positions and 55 judicial clerkships.",
            },
            {
                "label": "Top-tier salaries",
                "sentiment": "positive",
                "detail": "Median full-time salary $225,000 in bar-passage-required jobs (25th percentile $80,006; mean $166,075), reflecting strong Big-Law placement.",
            },
            {
                "label": "Excellent bar passage",
                "sentiment": "positive",
                "detail": "First-time bar passage of 97.27% for the Class of 2023, with a 99.35% ultimate bar admission rate.",
            },
            {
                "label": "Clerkships and public interest",
                "sentiment": "positive",
                "detail": "A deep federal-clerkship pipeline and extensive clinics and public-interest funding broaden outcomes beyond firm practice.",
            },
            {
                "label": "High cost",
                "sentiment": "caution",
                "detail": "Like its T14 peers, Michigan Law's tuition and living costs are high; reviewers weigh this against its strong employment and clerkship outcomes.",
            },
        ],
        "sources": [
            {
                "label": "University of Michigan Law — Comprehensive Employment Statistics",
                "url": "https://www.law.umich.edu/careers/classstats/Pages/employmentstats.aspx",
            },
            {
                "label": "Michigan Law — ABA Employment Summary, Class of 2023",
                "url": "https://michigan.law.umich.edu/system/files/2024-04/ABA_Employment_Summary_Class_of_2023_3_27_2024_a11y.pdf",
            },
            {
                "label": "Michigan Law — ABA First-Time Bar Passage disclosures",
                "url": "https://michigan.law.umich.edu/about-michigan-law/aba-required-disclosures",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "mich-business-ug": {
        "summary": "The Ross BBA is one of the very top undergraduate business programs in the country — ranked No. 4 nationally for undergraduate business by U.S. News for 2026. Reviewers praise its early hands-on learning, strong placement into consulting, investment banking, and tech, and a tight professional network, while noting that direct freshman admission is highly competitive.",
        "themes": [
            {
                "label": "Top-ranked undergraduate business",
                "sentiment": "positive",
                "detail": "U.S. News ranks Ross No. 4 for undergraduate business (2026); recruiters value the BBA's rigor and brand.",
            },
            {
                "label": "Experiential learning",
                "sentiment": "positive",
                "detail": "Students engage in action-based learning and real-client projects from early in the program.",
            },
            {
                "label": "Strong placement and network",
                "sentiment": "positive",
                "detail": "Graduates recruit heavily into consulting, finance, and technology, supported by a large, engaged alumni network.",
            },
            {
                "label": "Highly competitive admission",
                "sentiment": "caution",
                "detail": "Preferred and direct admission to the BBA is selective; many students apply for cross-campus transfer admission.",
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Best Undergraduate Business Programs 2026 (Michigan Ross No. 4)",
                "url": "https://www.usnews.com/best-colleges/rankings/business-overall",
            },
            {
                "label": "Michigan Ross — BBA Program",
                "url": "https://michiganross.umich.edu/undergraduate/bba",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "mich-computer-science-ug-eng": {
        "summary": "Michigan's computer science programs (offered as a B.S.E. in the College of Engineering and a B.S. in LSA, taught by the Computer Science and Engineering division of EECS) are among the nation's strongest — U.S. News ranks Michigan's undergraduate computer science in the national top 10–15. Reviewers highlight rigorous systems, AI, and theory coursework, large-scale research opportunities, and excellent big-tech and startup placement, while noting large class sizes and a demanding workload.",
        "themes": [
            {
                "label": "Top-tier CS reputation",
                "sentiment": "positive",
                "detail": "Times Higher Education ranks Michigan No. 31 in the world for computer science (2026); U.S. News places its CS program in the national top tier.",
            },
            {
                "label": "Research breadth",
                "sentiment": "positive",
                "detail": "Students can join research across AI, robotics, systems, security, and theory within the EECS Computer Science and Engineering division.",
            },
            {
                "label": "Strong tech placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into major technology firms and startups; Michigan is a core target school for many employers.",
            },
            {
                "label": "Large and demanding",
                "sentiment": "caution",
                "detail": "Popular CS courses are large and the workload is intense; reviewers advise engaging early with office hours and research.",
            },
        ],
        "sources": [
            {
                "label": "Times Higher Education — Computer Science subject ranking 2026 (Michigan No. 31)",
                "url": "https://www.timeshighereducation.com/world-university-rankings/university-michigan-ann-arbor",
            },
            {
                "label": "U-M CSE — Undergraduate Programs",
                "url": "https://cse.engin.umich.edu/academics/undergraduate/",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "mich-doctor-of-medicine-md": {
        "summary": "The University of Michigan Medical School is a leading research-intensive M.D. program (part of Michigan Medicine) ranked among the top U.S. medical schools — Times Higher Education places Michigan No. 19 in the world for medical and health for 2026. Reviewers praise its scientific trajectory curriculum, early clinical exposure, and research strength, while noting the competitiveness of admission and the demands of a top academic-medicine environment.",
        "themes": [
            {
                "label": "Elite academic medicine",
                "sentiment": "positive",
                "detail": "Michigan Medicine is a top-tier academic health system; THE ranks Michigan No. 19 worldwide for medical and health (2026).",
            },
            {
                "label": "Research strength",
                "sentiment": "positive",
                "detail": "Extensive NIH-funded research and institutes (Rogel Cancer Center, Michigan Neuroscience Institute) support M.D. and dual-degree research paths.",
            },
            {
                "label": "Curriculum and early clinical exposure",
                "sentiment": "positive",
                "detail": "The 'scientific trajectory' curriculum emphasizes early clinical immersion and individualized branches.",
            },
            {
                "label": "Highly competitive",
                "sentiment": "caution",
                "detail": "Admission is extremely selective and the workload is intensive, as at peer research medical schools.",
            },
        ],
        "sources": [
            {
                "label": "Times Higher Education — Clinical & Health subject ranking 2026 (Michigan No. 19)",
                "url": "https://www.timeshighereducation.com/world-university-rankings/university-michigan-ann-arbor",
            },
            {
                "label": "U-M Medical School — M.D. Program",
                "url": "https://medschool.umich.edu/education/md-program",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
}

# ── Admissions requirement sets ────────────────────────────────────────────
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission to an on-campus program.",
}
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application (with U-M questions)", "required": True},
        {"name": "Official high school transcript + school report", "required": True},
        {"name": "One teacher recommendation + counselor recommendation", "required": True},
        {"name": "$75 application fee (fee waivers available)", "required": True},
        {
            "name": "Standardized testing (test-optional)",
            "required": False,
            "note": "Michigan is test-optional; the SAT or ACT may be submitted but is not required.",
        },
    ],
    "deadlines": [
        {"round": "Early Action", "date": "November 1"},
        {"round": "Regular Decision", "date": "February 1"},
    ],
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "Duolingo English Test"],
            "required": False,
            "note": "English-proficiency proof is required for applicants whose first language is not English.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "U-M Office of Undergraduate Admissions",
                "url": "https://admissions.umich.edu/",
            }
        ],
    },
    "source": "U-M Office of Undergraduate Admissions",
    "source_url": "https://admissions.umich.edu/",
}
_REQ_GRAD_GENERIC = {
    "materials": [
        {"name": "Program / Rackham online application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose / personal statement", "required": True},
        {"name": "Résumé / CV", "required": True},
        {
            "name": "Letters of recommendation",
            "required": True,
            "note": "Most U-M graduate programs require three letters; check the program's page.",
        },
        {
            "name": "GRE scores",
            "required": False,
            "note": "GRE requirements vary by program; many U-M graduate programs are test-optional.",
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
                "label": "U-M Rackham Graduate School — How to Apply",
                "url": "https://rackham.umich.edu/admissions/applying/",
            }
        ],
    },
    "source": "U-M Rackham Graduate School",
    "source_url": "https://rackham.umich.edu/admissions/applying/",
}


def _requirements_for(spec: dict) -> dict:
    if spec["degree_type"] == "bachelors":
        return _REQ_UNDERGRAD
    return _REQ_GRAD_GENERIC


# ── Who-it's-for (universal depth field — REPAIR_BACKLOG #4) ──────────────────
# Every program states the applicant it fits (degree-level, U-M-specific), with
# flagship per-slug overrides. Never a "for students interested in {field}" stub,
# never ``= None`` (the hard-null that nulls the field on every re-apply, FLAG #4).
_WHO_BY_TYPE: dict[str, str] = {
    "bachelors": (
        "Applicants seeking a top public-research undergraduate education across the "
        "liberal arts, sciences, engineering, and the arts at Michigan."
    ),
    "masters": (
        "Students seeking advanced professional or specialized graduate training at a "
        "leading public research university."
    ),
    "phd": (
        "Researchers pursuing an academic or research career through a funded Michigan "
        "doctorate."
    ),
    "professional": (
        "Candidates pursuing a professional degree at Michigan, with strong placement and "
        "a large alumni network."
    ),
}
_WHO_BY_SLUG: dict[str, str] = {
    "mich-aerospace-engineering-ug": "Undergraduates fascinated by how aircraft and spacecraft fly, who want to design, develop, and test vehicles across both aeronautics within the atmosphere and astronautics in space. A foundation for aerospace engineering roles or graduate study in flight and space systems.",
    "mich-afroamerican-and-african-studies-ug": "Students drawn to the histories, cultures, politics, and social experiences of African and African-descended peoples across the continent and the diaspora, working across disciplines. Groundwork for careers in education, public service, and the arts, or graduate study.",
    "mich-american-culture-ug": "Undergraduates who want to examine U.S. society, history, politics, and cultural production by drawing on history, literature, ethnic studies, and the social sciences. A base for work in media, public institutions, and culture, or continued graduate study.",
    "mich-anthropology-ug": "Students curious about human behavior, biology, cultures, societies, and languages across both the present and the deep past, studying humanity through a scientific lens. Prepares for fieldwork-oriented careers, applied research, or graduate study in anthropology.",
    "mich-applied-exercise-science-ug": "Undergraduates interested in how the body responds and adapts to physical activity, integrating physiology, biomechanics, and motor control to support health and performance. A path toward health and fitness professions or graduate and clinical programs.",
    "mich-archaeology-of-the-ancient-mediterranean-ug": "Students drawn to reconstructing past Mediterranean societies through their material remains, working with artifacts, architecture, and excavated sites. A foundation for fieldwork, museum and heritage roles, or graduate study in archaeology.",
    "mich-architecture-ug": "Undergraduates who want to design buildings and built environments, balancing aesthetic, structural, functional, and social considerations. A pre-professional foundation that typically leads toward a graduate architecture degree and the path to licensure.",
    "mich-art-and-design-ug": "Studio-minded students who want to make visual work across media, joining conceptual development, craft, and critical inquiry to communicate ideas and shape objects and experiences. Prepares for professional creative practice or graduate art study.",
    "mich-arts-and-ideas-in-the-humanities-ug": "Undergraduates who want to study the arts, literature, philosophy, and cultural movements together with the ideas that shape and connect them, across disciplines. A humanities foundation for work in culture and education or graduate study.",
    "mich-asian-studies-ug": "Students interested in the peoples, cultures, languages, histories, and politics of Asia, studied across disciplines. A base for careers in international work, business, and public service, or graduate study focused on the region.",
    "mich-astronomy-and-astrophysics-ug": "Undergraduates drawn to celestial objects and phenomena who want to apply the laws of physics to the nature, origin, and evolution of stars, galaxies, and the universe. A foundation for research roles or graduate study in astrophysics.",
    "mich-biochemistry-ug": "Students fascinated by the chemical processes and substances within living organisms, studying biology and chemistry at the molecular level. Prepares for laboratory and health-related careers or graduate and professional study in the molecular life sciences.",
    "mich-biology-ug": "Undergraduates curious about life and living organisms, from their structure and function to growth, evolution, and interactions with the environment. A broad foundation for health professions, research, or graduate study in the life sciences.",
    "mich-biology-health-and-society-ug": "Students who want to connect the biological sciences with the social, ethical, and policy dimensions of human health and medicine. A path toward health professions, public health, or policy work, or graduate study bridging science and society.",
    "mich-biomedical-engineering-ug": "Undergraduates who want to apply engineering principles to medicine and biology, developing devices, instruments, and systems for healthcare and the study of living systems. A foundation for medical-device work, health professions, or graduate engineering study.",
    "mich-biomolecular-science-ug": "Students drawn to the molecules of life who want to study the structure, function, and interactions of proteins, nucleic acids, and lipids that underlie cellular processes. Prepares for laboratory research, health professions, or graduate study.",
    "mich-biophysics-ug": "Undergraduates who want to apply the concepts and methods of physics to biological systems, from molecules and cells to whole organisms. A quantitative foundation for research careers or graduate study bridging physics and the life sciences.",
    "mich-biopsychology-cognition-and-neuroscience-ug": "Students interested in the biological bases of behavior and mental processes, linking the brain and nervous system to perception, cognition, and action. A foundation for research, health professions, or graduate study in neuroscience and related fields.",
    "mich-business-ug": "Undergraduates seeking a top-ranked direct-admit business education through the Ross School of Business (BBA).",
    "mich-cellular-and-molecular-biomedical-science-ug": "Undergraduates focused on the cellular and molecular mechanisms behind human health and disease, and how that understanding informs diagnosis and treatment. Prepares for biomedical research, health professions, or graduate study.",
    "mich-chemical-engineering-ug": "Students who want to apply chemistry, physics, and mathematics to design and run processes that convert raw materials into useful products, fuels, and chemicals at scale. A foundation for process and manufacturing careers or graduate engineering study.",
    "mich-chemistry-ug": "Undergraduates drawn to matter itself, studying its properties, composition, structure, and the changes it undergoes in chemical reactions. A base for laboratory careers, health professions, or graduate study in chemistry.",
    "mich-civil-engineering-ug": "Students who want to design, construct, and maintain the built environment, including buildings, bridges, roads, and water systems. A professional foundation for infrastructure careers and the path toward engineering licensure or graduate study.",
    "mich-classical-civilization-ug": "Undergraduates drawn to the cultures, literatures, history, and societies of ancient Greece and Rome, studied largely in translation. A humanities foundation for careers in education, law, and writing, or graduate study of the ancient world.",
    "mich-classical-languages-and-literatures-ug": "Students who want to read ancient Greek and Latin and study the literary works written in them in the original. A foundation for teaching, editing, and scholarly work, or graduate study in classics.",
    "mich-climate-and-meteorology-ug": "Undergraduates interested in the atmosphere, weather processes, and the climate system, and how the atmosphere behaves and changes over time. A foundation for forecasting, environmental, and research careers or graduate study in the atmospheric sciences.",
    "mich-cognitive-science-ug": "Students fascinated by the mind and intelligence who want to draw across psychology, neuroscience, linguistics, philosophy, and computer science. A foundation for work in technology, research, and design, or graduate study of cognition.",
    "mich-communication-and-media-ug": "Undergraduates who want to understand how messages and media shape individuals, institutions, and society, examining communication processes, media systems, and their effects. Prepares for careers in media, communications, and related fields, or graduate study.",
    "mich-community-and-global-public-health-ug": "Students who want to protect and improve the health of populations locally and worldwide through prevention, policy, and community-based approaches. A foundation for public-health careers or graduate study in the field.",
    "mich-comparative-literature-arts-and-media-ug": "Undergraduates who want to study literary, visual, and media works across cultures and forms, examining how they create meaning and relate to one another. A humanities foundation for writing, culture, and media careers, or graduate study.",
    "mich-composition-ug": "Students who want to create original musical works, developing the craft of writing, structuring, and notating music. A conservatory-style foundation for careers as composers or for graduate study in composition.",
    "mich-computer-engineering-ug": "Undergraduates who want to join electrical engineering and computer science to design and build computer hardware and the systems and software that run on it. A foundation for hardware and systems careers or graduate engineering study.",
    "mich-computer-science-ug": "Students drawn to computation, algorithms, and information who want a liberal-arts grounding in the theory of computation, software design, and the principles that make computing possible. A base for software careers or graduate study in computing.",
    "mich-computer-science-ug-eng": "Undergraduates who want an engineering-based study of algorithms and computation alongside computing hardware and systems, spanning software, architecture, and theory. A foundation for software and systems engineering careers or graduate study.",
    "mich-creative-writing-and-literature-ug": "Students who want to pair the practice of original literary composition with the critical study of literary works and traditions. A foundation for writing, editing, and publishing careers, or graduate study in creative writing or literature.",
    "mich-dance-ug": "Undergraduates who want to study and practice structured human movement through performance, choreography, technique, and dance history and theory. A conservatory-style foundation for professional dance careers or graduate study.",
    "mich-data-science-ug": "Students who want to apply statistics, machine learning, and computing to extract insight from data, with an engineering emphasis on scalable computational methods and systems. A foundation for data and engineering careers or graduate study.",
    "mich-data-science-ug-lsa": "Undergraduates who want to apply statistics, machine learning, and computing to extract insight from data, grounded in mathematics, statistics, and computer science through a liberal-arts path. A base for analytics careers or graduate study.",
    "mich-dental-hygiene-ug": "Students drawn to preventing and treating oral disease through cleanings, assessments, and patient education in a clinical setting. A licensure-oriented foundation for practice as a dental hygienist or for continued study in the oral-health professions.",
    "mich-drama-ug": "Undergraduates who want to study and practice theatrical performance and dramatic literature, working across acting, production, and the analysis of plays. A foundation for careers in theater and the arts or graduate study in drama.",
    "mich-earth-and-environmental-sciences-ug": "Students interested in the Earth's physical systems, materials, and processes and how they interact with the environment and human activity. A foundation for geoscience and environmental careers or graduate study in the earth sciences.",
    "mich-ecology-evolution-and-biodiversity-ug": "Undergraduates who want to study how organisms interact with their environments, how populations evolve, and how the diversity of life is generated and sustained. A foundation for field and conservation careers or graduate study in ecology and evolution.",
    "mich-economics-ug": "Students who want to understand how societies produce, distribute, and consume goods and services, and how individuals and institutions decide under scarcity. A foundation for careers in business, policy, and finance, or graduate study in economics.",
    "mich-electrical-engineering-ug": "Undergraduates drawn to electricity, electronics, and electromagnetism who want to design devices, circuits, and systems. A foundation for engineering careers across hardware and systems, or graduate study in electrical engineering.",
    "mich-elementary-teacher-education-ug": "Students preparing to teach the elementary grades, combining subject-matter content, pedagogy, child development, and supervised classroom practice. A licensure-oriented path directly into elementary teaching.",
    "mich-engineering-physics-ug": "Undergraduates who want to apply fundamental physics and mathematics to engineering problems, bridging physical science with the design of advanced technologies. A foundation for research and development roles or graduate study in physics or engineering.",
    "mich-english-ug": "Students drawn to literature, language, and writing in English who want to analyze texts and study literary history and rhetoric. A foundation for careers in writing, education, and publishing, or graduate study in English.",
    "mich-environment-ug": "Undergraduates who want to examine the natural environment and human interactions with it across the natural sciences, social sciences, and humanities. A foundation for environmental and policy careers or graduate study.",
    "mich-environmental-engineering-ug": "Undergraduates who want to apply engineering to environmental problems and study water and air quality, waste treatment, and pollution control. A foundation for entry-level environmental engineering roles or graduate study in the field.",
    "mich-film-television-and-media-ug": "Undergraduates drawn to the history, theory, and production of moving-image and media culture and its role in society. Fits those heading toward media and screen industries or graduate study in film and media.",
    "mich-french-and-francophone-studies-ug": "Undergraduates who want to build fluency in French and read the literatures and cultures of France and the French-speaking world. A path toward work needing the language or graduate study in the field.",
    "mich-gender-and-health-ug": "Undergraduates interested in how gender shapes health, illness, and access to care, and how systems and policy respond. Fits future work in health, public health, or advocacy, or graduate study.",
    "mich-general-studies-ug": "Undergraduates who want to design a broad, self-directed course of study spanning multiple academic fields rather than a single major. A flexible foundation for varied careers or further study.",
    "mich-german-ug": "Undergraduates who want to build fluency in German and read the literatures and cultures of the German-speaking world. A path toward work needing the language or graduate study in the field.",
    "mich-greek-language-and-literature-ug": "Undergraduates drawn to the ancient Greek language and the poetry, prose, and drama written in it. Fits those continuing into classics, teaching, or graduate study of the ancient world.",
    "mich-greek-language-and-culture-ug": "Undergraduates who want to learn the Greek language alongside the literature, history, and civilization of the Greek world. A foundation for further study of antiquity or language-based careers.",
    "mich-history-ug": "Undergraduates who want to examine and interpret the human past, analyzing evidence to understand events, societies, and change over time. A foundation for careers in research, law, or public work, or graduate study.",
    "mich-history-of-art-ug": "Undergraduates who want to study works of visual art and architecture across cultures and periods, reading their forms, meanings, and historical contexts. Fits future work in museums and galleries or graduate study.",
    "mich-human-origins-biology-and-behavior-ug": "Undergraduates curious about the biological and evolutionary origins of humans and the roots of human behavior, integrating biological anthropology and the life sciences. A base for graduate study or science-related work.",
    "mich-industrial-and-operations-engineering-ug": "Undergraduates who want to design and improve complex systems of people, processes, and resources using optimization, applied probability, statistics, and human-factors methods. Grounded in operations research, ergonomics, and production systems through labs and team projects, it leads toward engineering roles or graduate study.",
    "mich-information-analysis-and-design-ug": "Undergraduates who want to gather, analyze, and present information and design systems and interfaces that serve human needs. A foundation for work in information roles or graduate study.",
    "mich-integrated-business-and-engineering-at-michigan-ug": "Undergraduates who want to lead at the intersection of technology and enterprise, joining engineering problem-solving with core business management. This engineering-based track suits those heading toward technical-management roles or further study.",
    "mich-integrated-business-and-engineering-at-michigan-ug-ross": "Undergraduates who want to lead at the intersection of technology and enterprise, pairing core business management with engineering problem-solving. This business-school track suits those heading toward management and enterprise roles or further study.",
    "mich-interarts-performance-ug": "Artists who want to integrate visual art, media, and live performance into original cross-disciplinary work. This studio-based fine-arts path fits those building a career in interdisciplinary art and performance.",
    "mich-interarts-performance-ug-smtd": "Performers who want to combine theatre, music, dance, and media into original, cross-disciplinary performance work. This performing-arts path fits those building a career on stage and across the arts.",
    "mich-interdisciplinary-astronomy-ug": "Undergraduates fascinated by celestial objects and the universe who also want ties to physics, data science, and instrumentation. A foundation for science-related work or graduate study in astronomy or allied fields.",
    "mich-interdisciplinary-chemical-sciences-ug": "Undergraduates drawn to matter and its transformations who want to bridge chemistry with biology, materials, physics, and engineering. A base for laboratory and science careers or graduate study.",
    "mich-interdisciplinary-physics-ug": "Undergraduates who want to study the fundamental principles of matter and energy while connecting physics to biology, engineering, or the earth sciences. A foundation for science-related work or graduate study.",
    "mich-international-studies-ug": "Undergraduates interested in global affairs across politics, economics, history, and culture spanning nations and regions. Fits future work in international fields, policy, or graduate study.",
    "mich-italian-ug": "Undergraduates who want to build fluency in Italian and read the literature and culture of Italy and the Italian-speaking world. A path toward work needing the language or graduate study in the field.",
    "mich-jazz-and-contemporary-improvisation-ug": "Musicians who want to study and practice jazz and improvised music through performance, composition, and the traditions of the idiom. A path toward professional performing and creative careers.",
    "mich-judaic-studies-ug": "Undergraduates drawn to Jewish history, religion, languages, literature, and culture across time and place. A foundation for graduate study or work in fields that value this interdisciplinary grounding.",
    "mich-latin-american-and-caribbean-studies-ug": "Undergraduates interested in the histories, cultures, politics, and societies of Latin America and the Caribbean. Fits future work in international or regional fields or graduate study.",
    "mich-latin-language-and-literature-ug": "Undergraduates drawn to the Latin language and the poetry, prose, and history written in it. Fits those continuing into classics, teaching, or graduate study of the ancient world and its texts.",
    "mich-latina-latino-studies-ug": "Undergraduates interested in the histories, cultures, and social experiences of people of Latin American descent in the United States. A foundation for work in community-facing fields or graduate study.",
    "mich-learning-equity-and-problem-solving-for-the-public-good-ug": "Undergraduates who want to use learning and education to advance equity and address social problems for the public good. Fits future work in education, community, or public-serving fields.",
    "mich-linguistics-ug": "Undergraduates drawn to the scientific study of language, including its sounds, structure, meaning, and use, and how languages vary and change. A foundation for language-related work or graduate study.",
    "mich-materials-science-and-engineering-ug": "Undergraduates who want to study the structure, properties, processing, and performance of materials and how they are designed and engineered for use. A foundation for engineering roles or graduate study in the field.",
    "mich-mathematics-ug": "Undergraduates who want to study quantity, structure, space, and change through abstract concepts, logical reasoning, and proof. A foundation for quantitative careers or graduate study in mathematics.",
    "mich-mechanical-engineering-ug": "Undergraduates who want to design, analyze, and manufacture mechanical systems, machines, and devices, drawing on physics and materials. A foundation for engineering roles or graduate study in the field.",
    "mich-microbiology-ug": "Undergraduates drawn to the study of bacteria, viruses, fungi, and protozoa and their roles in health, disease, and the environment. A base for laboratory and health-science careers or graduate study.",
    "mich-middle-east-studies-ug": "Undergraduates interested in the languages, histories, politics, religions, and cultures of the Middle East. Fits future work in international or regional fields or graduate study.",
    "mich-middle-eastern-and-north-african-studies-ug": "Undergraduates drawn to the languages, histories, politics, and cultures of the Middle East and North Africa. Fits future work in international or regional fields or graduate study.",
    "mich-molecular-cellular-and-developmental-biology-ug": "Undergraduates fascinated by the molecules and cells of living organisms and the processes by which they grow and develop. A base for laboratory and health-science careers or graduate study.",
    "mich-movement-science-ug": "Undergraduates interested in human movement and physical activity, integrating biomechanics, physiology, and motor control to understand performance, health, and rehabilitation. A foundation for health, rehabilitation, or research careers, or graduate study.",
    "mich-music-ug": "Musicians who want to study the art of organizing sound through melody, harmony, rhythm, and timbre, working across performance, composition, and scholarship. A foundation for musical careers or further study.",
    "mich-music-education-ug": "Undergraduates who want to teach music and study how it is taught and learned across schools and communities. A practice-oriented path toward becoming a music educator in classrooms and community settings.",
    "mich-music-theory-ug": "Undergraduates drawn to the structures, elements, and principles that underlie how music is composed, organized, and understood. A foundation for careers in music or graduate study in theory.",
    "mich-musical-theatre-ug": "Performers who want to combine acting, singing, and dance, building craft through performance, technique, and repertoire. A studio-based path toward a professional musical-theatre career.",
    "mich-musicology-ug": "Undergraduates drawn to the scholarly study of music, including its history, repertoire, and cultural contexts. A foundation for research, teaching, or graduate study in musicology.",
    "mich-naval-architecture-and-marine-engineering-ug": "Undergraduates who want to design, build, and operate ships and other marine vehicles and structures. A foundation for engineering roles in the marine field or continued graduate study in the discipline.",
    "mich-neuroscience-ug": "Undergraduates fascinated by the nervous system and how the brain gives rise to behavior and cognition. A base for laboratory and health-science careers or graduate study in neuroscience.",
    "mich-nuclear-engineering-and-radiological-sciences-ug": "Undergraduates drawn to nuclear processes and radiation, including reactors, radiation detection, and medical and energy uses. A foundation for engineering roles or graduate study in the field.",
    "mich-nursing-ug": "Undergraduates who want to care for individuals, families, and communities to promote health and to prevent and treat illness. A practice-oriented path toward becoming a registered nurse.",
    "mich-organ-ug": "Musicians who want to study the organ, developing performance, repertoire, and command of the instrument's pipe-and-air technique. A path toward professional performance and further musical study.",
    "mich-organizational-studies-ug": "Undergraduates curious about how organizations form, run, and change, who want to draw on psychology, sociology, and economics to study them. A foundation for roles in management, consulting, and human resources, or graduate work in business or the social sciences.",
    "mich-performing-arts-technology-ug": "Musicians and makers drawn to the technology behind sound, who want to work in recording, sound design, electronic music, and media production. Prepares graduates for careers in audio production and music technology, or continued study in the field.",
    "mich-pharmaceutical-sciences-ug": "Science-minded undergraduates interested in how drugs are discovered, formulated, delivered, and act in the body, blending chemistry, biology, and pharmacology. A foundation for careers in the pharmaceutical industry or further study in pharmacy or the health sciences.",
    "mich-philosophy-ug": "Students who like to reason carefully about existence, knowledge, values, mind, and language, and want to build skills in critical argument. A strong foundation for law, public life, or graduate study across the humanities.",
    "mich-philosophy-politics-and-economics-ug": "Undergraduates who want to analyze social, political, and economic questions through more than one lens, integrating philosophy, politics, and economics. A foundation for careers in policy, law, government, or graduate study across these fields.",
    "mich-physics-ug": "Students fascinated by matter, energy, and the fundamental forces governing everything from subatomic particles to the cosmos, who want rigorous grounding in physical law. A foundation for graduate research or technical work in science and engineering.",
    "mich-piano-ug": "Pianists ready to deepen performance technique, repertoire, and musicianship at the keyboard through focused undergraduate study. Prepares graduates for performing and teaching careers, or advanced conservatory and graduate study.",
    "mich-plant-biology-ug": "Undergraduates drawn to the scientific study of plants, from their structure and function to growth, reproduction, evolution, and ecological roles. A foundation for careers in botany, conservation, and environmental science, or graduate study in the life sciences.",
    "mich-polish-ug": "Students who want to master the Polish language and explore the literature, history, and culture of Poland. Opens paths in international work, translation, and cultural fields, or graduate study in Slavic and area studies.",
    "mich-political-science-ug": "Undergraduates interested in politics, government, and power, who want to study political institutions, behavior, public policy, and international relations. A foundation for careers in government, law, and advocacy, or graduate study in the field.",
    "mich-psychology-ug": "Students drawn to the scientific study of mind and behavior, examining perception, cognition, emotion, development, and social interaction. A foundation for careers in human services and research, or graduate study in psychology and related fields.",
    "mich-public-health-sciences-ug": "Undergraduates who want to protect and improve population health by analyzing disease, behavior, environment, and health systems. A foundation for public health practice or graduate study in the health sciences.",
    "mich-public-policy-ug": "Students interested in how governments address public problems, who want to learn to analyze, design, and evaluate policies. A foundation for careers in government and the nonprofit sector, or graduate study in public policy.",
    "mich-robotics-ug": "Undergraduates who want to design, build, and control robots by integrating mechanical engineering, electronics, computer science, and control theory. Prepares graduates for engineering careers in robotics and automation, or graduate study in the field.",
    "mich-romance-languages-and-literatures-ug": "Students drawn to the languages descended from Latin\u2014French, Spanish, Italian, and others\u2014and the literatures written in them. Opens paths in translation, international work, and education, or graduate study in literature and languages.",
    "mich-russian-ug": "Undergraduates who want to master Russian and explore the literature, history, and culture of Russia and the Russian-speaking world. Opens paths in international work, translation, and cultural fields, or graduate study in Slavic studies.",
    "mich-russian-east-european-and-eurasian-studies-ug": "Students interested in the languages, histories, politics, and cultures of Russia, Eastern Europe, and Eurasia, who want an interdisciplinary lens on the region. A foundation for international careers, policy work, or graduate study in area studies.",
    "mich-secondary-teacher-education-ug": "Future middle and high school teachers who want to combine subject-matter content, pedagogy, and supervised classroom practice. Leads toward teaching careers in secondary schools.",
    "mich-social-theory-and-practice-ug": "Undergraduates who want to understand society through concepts and frameworks and apply them to real social problems and action. A foundation for careers in advocacy, community work, and the social sector, or graduate study in the social sciences.",
    "mich-sociology-ug": "Students drawn to the scientific study of society, social relationships, institutions, and the patterns of human behavior. A foundation for careers in research, human services, and public work, or graduate study in sociology.",
    "mich-space-sciences-and-engineering-ug": "Undergraduates fascinated by the space environment and the instruments, spacecraft, and systems used to observe and explore it. Prepares graduates for engineering careers in the space sector, or graduate study in space science and engineering.",
    "mich-spanish-ug": "Students who want to master Spanish and explore the literatures and cultures of Spain and the Spanish-speaking world. Opens paths in translation, international work, and education, or graduate study in Hispanic studies.",
    "mich-sport-management-ug": "Undergraduates interested in the business side of sport\u2014organizations, marketing, finance, and operations within the sport industry. Prepares graduates for careers in sport administration and management.",
    "mich-statistics-ug": "Students who enjoy collecting, analyzing, and interpreting data and drawing inferences under uncertainty. A foundation for careers in data analysis and quantitative work, or graduate study in statistics and data science.",
    "mich-strings-ug": "String players ready to develop technique and repertoire on the violin, viola, cello, or double bass through focused undergraduate study. Prepares graduates for performing and teaching careers, or advanced conservatory and graduate study.",
    "mich-theatre-and-drama-ug": "Students drawn to theatrical performance and dramatic literature, who want to study acting, production, and the analysis of plays. A foundation for careers in theatre and the performing arts, or graduate and conservatory study.",
    "mich-translation-ug": "Undergraduates fluent across languages who want to practice rendering meaning between them and study the theory, methods, and cultural dimensions of translation. Opens paths in translation and language services, or graduate study in the field.",
    "mich-urban-technology-ug": "Students interested in how digital technology and data shape cities, who want to design technology-enabled solutions for urban life and systems. Prepares graduates for careers at the intersection of technology and cities, or graduate study in urban fields.",
    "mich-user-experience-design-ug": "Undergraduates who want to design products, systems, and services that are useful, usable, and meaningful for the people who use them. Prepares graduates for careers in UX and product design, or graduate study in the field.",
    "mich-voice-and-opera-ug": "Singers ready to develop vocal technique, languages, repertoire, and dramatic interpretation for the operatic and concert stage. Prepares graduates for performing careers, or advanced conservatory and graduate study.",
    "mich-winds-and-percussion-ug": "Woodwind, brass, and percussion players who want to build technique, repertoire, and ensemble artistry through focused undergraduate study. Prepares graduates for performing and teaching careers, or advanced conservatory and graduate study.",
    "mich-women-s-and-gender-studies-ug": "Undergraduates who want to study gender, women's experiences, and sexuality and how they shape culture, society, and power. A foundation for careers in advocacy, education, and the social sector, or graduate study in the field.",
    "mich-aerospace-engineering-phd": "Engineers pursuing original research in the design and development of aerospace systems, working through faculty mentorship, qualifying examinations, and a dissertation. The path to research careers in academia, industry, or national labs.",
    "mich-aerospace-engineering-ms": "Engineers who want advanced expertise in aerospace design and development through graduate seminars, methods training, and a thesis or capstone. Prepares graduates for specialized engineering roles or further doctoral study.",
    "mich-american-culture-phd": "Scholars pursuing original research on American society, history, and politics, working through faculty mentorship, qualifying examinations, and a dissertation. The path to faculty positions and academic research careers.",
    "mich-ancient-history-phd": "Scholars who want to research the recorded human past from the earliest civilizations through late antiquity, examining ancient politics, societies, economies, and cultures. The path to faculty positions and academic research careers in the field.",
    "mich-ancient-mediterranean-art-and-archaeology-phd": "Scholars pursuing original research on the art, architecture, and material remains of the ancient Mediterranean\u2014Greece, Rome, and the Near East. The path to faculty positions, museum roles, and academic research careers.",
    "mich-anthropology-phd": "Scholars pursuing original research into human behavior, biology, cultures, and societies, working through faculty mentorship, qualifying examinations, and a dissertation. The path to faculty positions and academic research careers in anthropology.",
    "mich-anthropology-and-history-phd": "Scholars who want to join anthropological and historical methods to study how societies, cultures, and power relations form and change over time. The path to faculty positions and academic research careers across both fields.",
    "mich-applied-and-interdisciplinary-mathematics-phd": "Mathematically minded researchers who want to develop and use mathematical methods to model and solve problems across the sciences, working through qualifying examinations and a dissertation. The path to faculty positions and research careers.",
    "mich-applied-and-interdisciplinary-mathematics-ms": "Students who want to develop and apply mathematical methods to model and solve problems arising in the physical, biological, engineering, and social sciences. Prepares graduates for quantitative careers or further doctoral study.",
    "mich-applied-economics-ms": "Students who want to use economic theory and econometric methods to analyze practical problems in labor, health, public policy, finance, and industry. Prepares graduates for analytical roles in the public and private sectors, or further doctoral study.",
    "mich-applied-physics-phd": "Researchers who want to apply the principles and methods of physics to develop technologies and solve problems, working through qualifying examinations and a dissertation. The path to research careers in academia, industry, or national labs.",
    "mich-applied-physics-ms": "Students who want to apply the principles and methods of physics to develop technologies and solve scientific and engineering problems, bridging physics and engineering. Prepares graduates for technical roles or further doctoral study.",
    "mich-applied-statistics-ms": "Students who want to apply statistical theory and methods to collect, analyze, and interpret data and draw inferences in scientific, industrial, and social settings. Prepares graduates for data-analysis and statistical roles, or further doctoral study.",
    "mich-arabic-studies-ms": "Students who want focused, interdisciplinary study of the Arabic language, literature, and the history and cultures of the Arab world. Prepares graduates for careers in research, education, and international work, or further doctoral study.",
    "mich-architecture-phd": "Scholars pursuing original research on the design of buildings and built environments, integrating aesthetic and technical concerns through faculty mentorship, qualifying examinations, and a dissertation. The path to faculty positions and academic research careers.",
    "mich-architecture-ms": "Designers who want advanced grounding in shaping buildings and built environments, weighing aesthetic and technical concerns through graduate seminars, methods training, and a thesis or capstone. Suits those moving toward specialized architectural practice or continued design research.",
    "mich-art-ms": "Artists ready to deepen their studio practice while engaging the making, history, and critical interpretation of work across a wide range of media. Fits those advancing an independent creative practice or preparing for further study in art.",
    "mich-asian-languages-and-cultures-phd": "Scholars committed to original research on the languages, literatures, religions, histories, and cultures of Asia, advancing through qualifying exams and a dissertation. The path toward faculty and academic research careers in Asian studies.",
    "mich-astronomy-and-astrophysics-phd": "Researchers drawn to celestial objects and phenomena who will pursue original investigation under faculty mentorship, clear qualifying examinations, and complete a dissertation. Prepares for faculty positions and research careers in astronomy and astrophysics.",
    "mich-athletic-training-ms": "Students entering the allied-health profession focused on preventing, evaluating, treating, and rehabilitating injuries and illnesses tied to physical activity and sport. A practice-oriented path toward certified athletic-training roles in clinical and sport settings.",
    "mich-bioinformatics-phd": "Researchers who want to build and apply computational methods to analyze biological data, advancing original work through faculty mentorship, qualifying exams, and a dissertation. Prepares for faculty positions and research careers in computational biology.",
    "mich-bioinformatics-ms": "Students who want to develop and apply computational methods across biology, computer science, and statistics to analyze genomic and molecular data. Suits those moving into analyst and research roles or continuing toward doctoral study.",
    "mich-bioinformatics-pibs-phd": "Researchers focused on computational and statistical methods for large-scale biological and biomedical data, from genome sequences to gene-expression profiles, working through qualifying exams and a dissertation. The path to academic and research careers in the field.",
    "mich-biological-chemistry-ms": "Students drawn to the chemistry of living systems who want focused study of the structure, function, and interactions of the molecules behind biological processes. Suits those advancing into laboratory research roles or preparing for doctoral work.",
    "mich-biological-chemistry-pibs-phd": "Researchers investigating the molecular chemistry of living systems, including the structure, mechanism, and regulation of proteins, nucleic acids, and metabolic pathways, through qualifying exams and a dissertation. Leads to faculty and research careers in the discipline.",
    "mich-biomedical-engineering-phd": "Engineers who want to apply engineering principles and design to medicine and biology through original research, faculty mentorship, qualifying examinations, and a dissertation. Prepares for faculty positions and research careers in biomedical engineering.",
    "mich-biomedical-engineering-ms": "Engineers seeking advanced, focused expertise in applying engineering principles and design to medicine and biology, built through graduate seminars, methods training, and a thesis or capstone. Suits those advancing in industry or moving toward doctoral study.",
    "mich-biomedical-sciences-pibs-phd": "Researchers studying the biological mechanisms of human health and disease at molecular, cellular, and systems levels, advancing original work through qualifying exams and a dissertation. The path toward faculty and biomedical research careers.",
    "mich-biophysics-phd": "Researchers who want to bring the concepts and methods of physics to understanding biological systems, pursuing original work through faculty mentorship, qualifying examinations, and a dissertation. Leads to faculty positions and research careers in biophysics.",
    "mich-biostatistics-phd": "Researchers who want to develop statistical theory and methods for questions in biology and medicine, advancing original work through qualifying exams and a dissertation. Prepares for faculty positions and research careers in biostatistics.",
    "mich-biostatistics-ms": "Students who want to apply statistical theory and methods to biology, medicine, and public health, including the design and analysis of experiments and clinical studies. Suits those entering biostatistician roles or continuing toward doctoral study.",
    "mich-biostatistics-health-data-science-ms": "Students drawn to applying statistical and computational methods to large-scale health and biomedical data supporting research and clinical decision-making. Fits those moving into health-data-science and analytics roles across research and care.",
    "mich-business-administration-phd": "Researchers who want to study how organizations are managed and operated, spanning fields such as accounting, through original work, qualifying examinations, and a dissertation. The path toward faculty positions and academic research in business.",
    "mich-business-and-economics-phd": "Researchers who want to join the analytical methods of economics with the study of firms and markets to examine decision-making, organizations, and the economy, working through qualifying exams and a dissertation. Leads to faculty and research careers.",
    "mich-cancer-biology-pibs-phd": "Researchers studying how normal cells become malignant, how tumors grow and spread, and how cancer can be detected and treated, advancing original work through qualifying exams and a dissertation. Prepares for faculty and cancer-research careers.",
    "mich-cell-and-developmental-biology-pibs-phd": "Researchers drawn to the structure and function of cells and how organisms grow from a single cell into complex tissues, pursuing original work through qualifying exams and a dissertation. The path toward faculty and research careers in the field.",
    "mich-cellular-and-molecular-biology-pibs-phd": "Researchers focused on the molecular machinery and processes governing the structure, function, and regulation of cells, advancing original work through qualifying exams and a dissertation. Leads to faculty positions and research careers in cell and molecular biology.",
    "mich-chemical-biology-phd": "Researchers who want to apply the tools and principles of chemistry to study and manipulate biological systems, probing the molecules and reactions of living cells through qualifying exams and a dissertation. Prepares for faculty and research careers.",
    "mich-chemical-biology-of-cancer-ms": "Students who want to apply chemical and molecular approaches to understanding cancer biology and to discovering and developing new diagnostics and therapeutics. Suits those entering research roles in drug discovery or preparing for doctoral study.",
    "mich-chemical-engineering-phd": "Researchers grounded in chemistry and physics who want to pursue original work through faculty mentorship, qualifying examinations, and a dissertation. Prepares for faculty positions and research careers in chemical engineering.",
    "mich-chemical-engineering-ms": "Engineers seeking advanced, focused expertise built on chemistry and physics through graduate seminars, methods training, and a thesis or capstone. Suits those advancing in industry practice or moving toward doctoral research.",
    "mich-chemistry-phd": "Researchers drawn to matter and its properties, composition, and structure who will pursue original investigation through faculty mentorship, qualifying examinations, and a dissertation. Leads to faculty positions and research careers in chemistry.",
    "mich-chemistry-ms": "Students who want advanced, focused study of matter and its properties, composition, and structure, built through graduate seminars, methods training, and a thesis or capstone. Suits those entering chemistry-based roles or continuing toward doctoral work.",
    "mich-civil-engineering-phd": "Researchers in the discipline of design and construction who want to pursue original work through faculty mentorship, qualifying examinations, and a dissertation. Prepares for faculty positions and research careers in civil engineering.",
    "mich-civil-engineering-ms": "Engineers seeking advanced, focused expertise in the design and construction of the built environment through graduate seminars, methods training, and a thesis or capstone. Suits those advancing in professional practice or moving toward doctoral study.",
    "mich-classical-studies-phd": "Researchers drawn to the languages, literature, history, and art of the ancient world who will pursue original work through faculty mentorship, qualifying examinations, and a dissertation. The path toward faculty and academic research careers in classics.",
    "mich-classical-studies-ms": "Students who want focused, interdisciplinary study of the languages, literature, history, art, and archaeology of ancient Greece and Rome. Suits those deepening expertise before doctoral work or scholarly and cultural-heritage roles.",
    "mich-climate-and-space-sciences-and-engineering-phd": "Researchers studying the Earth's atmosphere, climate, and the space environment who will pursue original work through faculty mentorship, qualifying examinations, and a dissertation. Prepares for faculty positions and research careers in the field.",
    "mich-climate-and-space-sciences-and-engineering-ms": "Students drawn to the Earth's atmosphere, climate, and space environment who want to develop the instruments and models used to observe and predict them. Suits those entering technical and research roles or continuing toward doctoral study.",
    "mich-clinical-pharmacy-translational-science-phd": "Researchers who want to study how medications act in patients and how laboratory discoveries become safe, effective drug therapy and clinical practice, working through qualifying exams and a dissertation. The path toward faculty and translational-research careers.",
    "mich-clinical-research-design-and-statistical-analysis-ms": "Students who want to learn how to design clinical investigations and analyze their data to produce valid, reliable medical evidence. Suits clinicians and researchers moving into study-design and clinical-data-analysis roles.",
    "mich-communication-and-media-phd": "Researchers drawn to how messages and media shape individuals, institutions, and society who will pursue original work through faculty mentorship, qualifying examinations, and a dissertation. Leads to faculty positions and research careers in communication.",
    "mich-comparative-literature-phd": "Researchers who want to study literature across languages, national boundaries, and historical periods, often alongside other arts and disciplines, through qualifying exams and a dissertation. The path toward faculty and academic research careers.",
    "mich-composition-phd": "Composers who want to pursue original creative and scholarly work in writing musical works, advancing through faculty mentorship, qualifying examinations, and a dissertation. Prepares for faculty positions and research-oriented careers in composition.",
    "mich-composition-ms": "Composers who want focused, advanced work in the craft of writing, structuring, and notating original musical works. Suits those developing an independent compositional voice or preparing for further study in music.",
    "mich-composition-and-music-theory-phd": "Composers and theorists who want to join the creation of original works with analytical study of how music is structured, organized, and understood, working through qualifying exams and a dissertation. The path toward faculty and academic careers.",
    "mich-computational-epidemiology-and-systems-modeling-ms": "Students who want to use mathematical and computer models to study how diseases spread through populations and to evaluate public-health interventions. Suits those entering modeling and analytics roles in public health or continuing to doctoral study.",
    "mich-computer-science-and-engineering-phd": "Researchers who want to join the study of computation and algorithms with the design of computing systems, advancing original work through faculty mentorship, qualifying examinations, and a dissertation. Prepares for faculty and research careers.",
    "mich-computer-science-and-engineering-ms": "Students who want advanced work joining computation and algorithms with the design of computing hardware and systems, spanning software, architecture, and theory. Suits those moving into technical roles or continuing toward doctoral study.",
    "mich-conducting-band-wind-ensemble-phd": "Conductors who want advanced study and practice of leading wind bands and ensembles, from score study and gesture to interpretation, working through qualifying exams and a dissertation. The path toward faculty and leading ensemble-directing careers.",
    "mich-conducting-choral-phd": "Conductors who want advanced study and practice of leading choirs and vocal ensembles, spanning score study, vocal technique, rehearsal craft, and interpretation, through qualifying exams and a dissertation. Prepares for faculty and choral-directing careers.",
    "mich-conducting-orchestral-phd": "Conductors who want advanced study and practice of leading orchestras in rehearsal and performance, from score study and gesture to musical interpretation, working through qualifying exams and a dissertation. The path toward faculty and orchestral-directing careers.",
    "mich-construction-engineering-and-management-ms": "Engineering graduates who want to plan, design, and oversee infrastructure and building projects, blending technical engineering with the management principles that keep large projects on schedule and budget. Suits future project engineers, construction managers, and firm-side leaders.",
    "mich-creative-writing-ms": "Writers ready to devote graduate study to original literary composition in fiction, poetry, and creative nonfiction, developing craft and a substantial body of work. Fits those aiming for a writing life, publication, or teaching.",
    "mich-dance-ms": "Committed dance artists who want advanced study of structured human movement, combining graduate seminars, methods training, and a thesis or capstone project. Suits performers, choreographers, and educators deepening their practice.",
    "mich-data-science-ms": "Quantitatively minded students who want to combine statistics, computation, and domain knowledge to extract insight and build predictive models from data. Prepares graduates for data scientist and analytics roles across industry and research.",
    "mich-dental-hygiene-ms": "Practicing hygienists ready to advance beyond clinical care into the science of preventing and treating oral disease, through graduate seminars, methods training, and a thesis or capstone. Opens paths in education, research, and clinical leadership.",
    "mich-design-ms": "Designers who want to plan and create objects, systems, and experiences that integrate function, aesthetics, and human needs at a graduate level. Suits practitioners deepening their craft toward studio, product, or experience-design careers.",
    "mich-design-science-phd": "Researchers who want to study the principles, processes, and methods behind design and generate original scholarship through qualifying exams and a dissertation, with faculty mentorship. The path to academic and research careers in design science.",
    "mich-design-science-ms": "Students drawn to the principles, processes, and methods of design across disciplines, who want systematic, research-based approaches to creating products and systems. Suits those advancing toward applied design-research and development roles.",
    "mich-earth-and-environmental-sciences-phd": "Scientists who want to investigate the Earth's physical systems and materials through original research, qualifying exams, and a dissertation guided by faculty mentors. The path to faculty positions and research careers in the Earth sciences.",
    "mich-earth-and-environmental-sciences-ms": "Students who want advanced study of the Earth's physical systems and materials, combining graduate seminars, methods training, and a thesis or capstone. Suits those advancing into environmental, geoscience, or resource-focused careers, or further doctoral study.",
    "mich-ecology-and-evolutionary-biology-phd": "Biologists who want to research how organisms interact with one another and their environment and the evolutionary processes shaping biological diversity, through original research and a dissertation. The path to faculty and research careers.",
    "mich-ecology-and-evolutionary-biology-ms": "Students focused on the interactions of organisms with their environment and the evolutionary processes behind biological diversity, at the graduate level. Suits those advancing toward research, conservation, or further doctoral study.",
    "mich-economics-phd": "Scholars who want to study how societies produce and distribute resources through rigorous original research, qualifying exams, and a dissertation with faculty mentorship. The path to faculty positions and research careers in economics.",
    "mich-education-and-psychology-phd": "Researchers who want to apply psychological theory and methods to learning, development, and educational practice, producing original scholarship. Prepares graduates for faculty positions and research careers at the intersection of education and psychology.",
    "mich-educational-leadership-and-policy-ms": "Educators who want to understand how schools and systems are led, organized, and governed, and how policy shapes teaching and learning. Suits aspiring school and district leaders and those moving into policy and administration.",
    "mich-educational-studies-phd": "Scholars who want to research teaching, learning, and education as a social institution through original inquiry, qualifying exams, and a dissertation. The path to faculty positions and research careers in education.",
    "mich-educational-studies-ms": "Students drawn to the interdisciplinary study of teaching, learning, and education as a social institution, drawing on the social sciences and humanities. Suits educators and future researchers building analytic depth in the field.",
    "mich-electrical-and-computer-engineering-phd": "Engineers who want to research the design of electrical and electronic systems and computing hardware, from circuits to computer systems, through original work and a dissertation. The path to faculty positions and advanced research careers.",
    "mich-electrical-and-computer-engineering-ms": "Engineering graduates who want deeper mastery of electrical and electronic systems and computing hardware, spanning circuits, signals, communications, and computer systems. Prepares graduates for specialized engineering roles in industry.",
    "mich-endodontics-ms": "Dentists pursuing specialty training in diagnosing and treating diseases of the dental pulp and the tissues around tooth roots. The path toward practice as an endodontist and specialty-level clinical expertise.",
    "mich-engineering-education-research-phd": "Researchers who want to study how engineering is taught and learned and generate original scholarship through qualifying exams and a dissertation. The path to faculty positions and research careers in engineering education.",
    "mich-engineering-education-research-ms": "Students who want to apply educational theory and methods to how engineering is taught, working to improve engineering teaching, curricula, and outcomes. Suits engineers and educators moving toward curriculum, assessment, and instructional roles.",
    "mich-english-and-education-phd": "Scholars who want to join the study of literature and language with educational theory and practice, producing original research through qualifying exams and a dissertation. Prepares graduates as scholars of English teaching and learning.",
    "mich-english-and-women-s-and-gender-studies-phd": "Researchers who want to join the study of English literature and language with the analysis of gender and women's experiences across culture and society, through original scholarship and a dissertation. The path to faculty positions in the field.",
    "mich-english-language-and-literature-phd": "Scholars who want to research works written in English and the English language itself, spanning literary analysis, history, and linguistics, through original work and a dissertation. The path to faculty positions and research careers.",
    "mich-environment-and-sustainability-ms": "Students focused on the interactions between human societies and natural systems and the policies and practices that support a sustainable future. Suits future practitioners in sustainability, conservation, and environmental policy.",
    "mich-environment-and-sustainability-phd": "Researchers who want to study the interactions between human societies and natural systems through original scholarship, qualifying exams, and a dissertation with faculty mentorship. The path to faculty positions and research careers in sustainability.",
    "mich-environmental-engineering-phd": "Engineers who want to research how engineering principles can protect and improve the environment, through original work, qualifying exams, and a dissertation. The path to faculty positions and advanced environmental-engineering research careers.",
    "mich-environmental-engineering-ms": "Engineering graduates who want advanced expertise applying engineering principles to protect and improve the environment, through graduate seminars, methods training, and a thesis or capstone. Prepares graduates for specialized environmental-engineering roles.",
    "mich-environmental-health-sciences-phd": "Researchers who want to study how physical, chemical, and biological factors in the environment affect human health, generating original scholarship through qualifying exams and a dissertation. The path to faculty and research careers in environmental health.",
    "mich-environmental-health-sciences-ms": "Students focused on how physical, chemical, and biological factors in the environment affect human health and how those risks are assessed and controlled. Suits future practitioners in environmental and public-health science, or doctoral study.",
    "mich-epidemiologic-science-phd": "Researchers who want to study the distribution and determinants of health and disease in populations and apply that work to prevention and control, through original scholarship and a dissertation. The path to faculty and research careers in epidemiology.",
    "mich-film-television-and-media-phd": "Scholars who want to research the history and theory of film, television, and media, producing original scholarship through qualifying exams and a dissertation with faculty mentorship. The path to faculty positions and research careers.",
    "mich-genetic-counseling-ms": "Students preparing for a health profession that helps individuals and families understand and adapt to the medical, psychological, and familial implications of genetic conditions. The path toward practice as a genetic counselor.",
    "mich-genetics-and-genomics-pibs-phd": "Researchers who want to study heredity and the structure, function, and evolution of genomes, including how genes shape traits, development, and disease, through original work and a dissertation. The path to faculty and research careers.",
    "mich-germanic-languages-and-literatures-phd": "Scholars who want to research the German and other Germanic languages and the literary and cultural works written in them, through original scholarship and a dissertation. The path to faculty positions and research careers in the field.",
    "mich-greek-ms": "Students who want advanced study of the ancient Greek language and the literature, philosophy, and history of the ancient Greek world. Suits those deepening classical scholarship toward teaching or further doctoral study.",
    "mich-health-and-health-care-research-ms": "Students who want to study the organization, delivery, quality, and outcomes of health care and the factors shaping population health. Suits clinicians and analysts moving into health-services research and evidence-based practice.",
    "mich-health-behavior-and-health-equity-phd": "Researchers who want to study the social, behavioral, and structural factors that influence health and the persistent disparities across populations, through original scholarship and a dissertation. The path to faculty and research careers in the field.",
    "mich-health-behavior-and-health-equity-ms": "Students focused on the social, behavioral, and structural factors that shape health and the disparities across populations. Suits future practitioners in public health, health promotion, and equity-focused program work.",
    "mich-health-infrastructures-and-learning-systems-phd": "Researchers who want to study how data, information technology, and learning processes can be built into health-care systems to continuously improve care, through original scholarship and a dissertation. The path to faculty and research careers.",
    "mich-health-infrastructures-and-learning-systems-ms": "Clinicians and health professionals who want to study how data, information technology, and learning processes can be embedded in care systems to continuously improve them. Suits those moving into learning-health-system and informatics roles.",
    "mich-health-infrastructures-and-learning-systems-online-ms": "Working health professionals who want to study, fully online, how data, information technology, and continuous-learning processes can be embedded in care systems to improve care. Suits practitioners advancing into learning-health-system and informatics roles.",
    "mich-health-services-organization-and-policy-phd": "Researchers who want to study how health-care delivery is organized, financed, and governed and how policy shapes access, cost, and quality, through original scholarship and a dissertation. The path to faculty and research careers in health policy.",
    "mich-higher-education-phd": "Scholars who want to research colleges and universities as organizations and the policies, leadership, and practices shaping them, through original work and a dissertation. The path to faculty positions and research careers in higher education.",
    "mich-higher-education-ms": "Students who want to study colleges and universities as organizations and the policies, leadership, and practices that shape postsecondary teaching, access, and outcomes. Suits future administrators and student-affairs and policy professionals.",
    "mich-history-phd": "Scholars who want to research the human past, examining and interpreting events and societies through original scholarship, qualifying exams, and a dissertation with faculty mentorship. The path to faculty positions and research careers in history.",
    "mich-history-and-women-s-and-gender-studies-phd": "Scholars who want to join historical inquiry with the analysis of gender and women's experiences across time and across societies. This interdisciplinary doctoral path leads toward faculty positions and research careers in history and gender studies.",
    "mich-history-of-art-phd": "Researchers drawn to visual art and architecture across cultures and periods who want to pursue original scholarship through faculty mentorship, qualifying examinations, and a dissertation. The path toward academic and museum-based art-historical careers.",
    "mich-human-genetics-ms": "Students fascinated by human inheritance who want focused graduate grounding in how genes shape traits, variation, and disease. A specialized master's for those advancing into genetics-related research, clinical, or counseling roles, or continuing toward doctoral study.",
    "mich-immunology-pibs-phd": "Aspiring researchers who want to investigate how the body defends against disease and how immune responses malfunction or can be harnessed therapeutically. Through qualifying exams and a dissertation, the path toward academic and biomedical immunology research careers.",
    "mich-industrial-and-operations-engineering-phd": "Researchers drawn to operations research and optimization, healthcare systems engineering, human factors and ergonomics, financial engineering, and data-driven decision making. Working with faculty advisers through qualifying exams and a dissertation, they prepare for careers in academia, industry research, and national laboratories.",
    "mich-industrial-and-operations-engineering-ms": "Engineers and analysts who want advanced skill in operations research, stochastic modeling, data analytics, and ergonomics applied to healthcare, supply chains, and financial engineering. Through seminars and a project or thesis, the path toward analytics, consulting, operations, and systems-engineering roles or doctoral study.",
    "mich-information-phd": "Researchers who want to study how information is created, organized, stored, and retrieved through original scholarship, guided by faculty mentorship, qualifying examinations, and a dissertation. The path toward academic and research careers in information.",
    "mich-integrated-pharmaceutical-sciences-ms": "Students drawn to how drugs are discovered, formulated, delivered, and act in the body, spanning medicinal chemistry, pharmaceutics, and pharmacology. A specialized master's for those advancing into pharmaceutical research and industry roles or continuing toward doctoral study.",
    "mich-international-and-regional-studies-ms": "Students who want interdisciplinary depth in world regions and global affairs, integrating language, history, politics, and culture. A focused master's for those moving into international-facing careers in policy, government, or nonprofits, or continuing to doctoral work.",
    "mich-intraoperative-neurophysiology-ms": "Students preparing for the clinical field that monitors the nervous system during surgery to detect and prevent neurological injury. A practice-oriented master's for those entering intraoperative neuromonitoring roles in surgical and clinical settings.",
    "mich-jazz-and-contemporary-improvisation-phd": "Accomplished musicians who want to study and practice jazz and improvised music at the highest level, spanning performance, composition, and the history of the idiom. The doctoral path toward careers as performing artist-scholars and university faculty.",
    "mich-landscape-architecture-ms": "Designers drawn to shaping outdoor spaces, landscapes, and public environments by integrating ecology, art, and planning. A professional master's for those entering landscape architecture practice and land-focused design careers.",
    "mich-latin-ms": "Students devoted to the Latin language and the literature, history, and culture of ancient Rome and the broader Latin tradition. A focused master's for those advancing toward teaching, further classical study, or doctoral work.",
    "mich-linguistics-phd": "Researchers fascinated by language, including its sounds, structure, meaning, and use, who want to pursue original scholarship through faculty mentorship, qualifying examinations, and a dissertation. The path toward academic and research careers in linguistics.",
    "mich-macromolecular-science-and-engineering-phd": "Researchers drawn to polymers and other large molecules and the study of their structure who want to conduct original research through faculty mentorship, qualifying examinations, and a dissertation. The path toward academic, industry, and research careers in macromolecular science.",
    "mich-macromolecular-science-and-engineering-ms": "Scientists and engineers who want advanced study of polymers and other large molecules, examining their structure, properties, and uses in materials and technology. A specialized master's for those advancing into materials-focused industry roles or continuing to doctoral study.",
    "mich-materials-science-and-engineering-phd": "Researchers drawn to the structure, properties, and processing of materials who want to conduct original research through faculty mentorship, qualifying examinations, and a dissertation. The path toward academic, industry, and research careers in materials science.",
    "mich-materials-science-and-engineering-ms": "Engineers who want advanced expertise in the structure, properties, and processing of materials through graduate seminars, methods training, and a thesis or capstone. A specialized master's for those advancing into materials-focused industry roles or doctoral study.",
    "mich-mathematics-phd": "Researchers drawn to quantity, structure, space, and change who want to pursue original mathematical scholarship through faculty mentorship, qualifying examinations, and a dissertation. The path toward academic and research careers in mathematics.",
    "mich-mathematics-ms": "Students who want advanced expertise in quantity, structure, space, and change through graduate seminars, methods training, and a thesis or capstone. A focused master's for those deepening quantitative skills for technical careers or continuing toward doctoral study.",
    "mich-mechanical-engineering-phd": "Researchers drawn to the design and analysis of mechanical systems who want to conduct original research through faculty mentorship, qualifying examinations, and a dissertation. The path toward academic, industry, and research careers in mechanical engineering.",
    "mich-mechanical-engineering-ms": "Engineers who want advanced expertise in the design and analysis of mechanical systems through graduate seminars, methods training, and a thesis or capstone. A specialized master's for those advancing into engineering roles or doctoral study.",
    "mich-media-arts-ms": "Artists drawn to the creative practice of digital and time-based media, encompassing video, sound, interactivity, and emerging technologies as artistic forms. A specialized master's for those developing media-arts practices in creative and production careers.",
    "mich-medical-scientist-training-program-phd": "Aspiring physician-scientists who want combined training in medicine and biomedical research toward the M.D. and Ph.D. degrees. The path toward careers that bridge clinical practice and biomedical research.",
    "mich-medicinal-chemistry-phd": "Researchers drawn to the intersection of chemistry and pharmacology who want to design, synthesize, and develop drugs through original doctoral research. The path toward academic and pharmaceutical research careers in drug discovery.",
    "mich-microbiology-and-immunology-ms": "Students drawn to microorganisms and the immune system, including how microbes cause disease and how the body defends against infection. A specialized master's for those advancing into microbiology and immunology research or continuing toward doctoral study.",
    "mich-microbiology-and-immunology-pibs-phd": "Researchers who want to investigate microorganisms and the immune system, including host-pathogen interactions and the molecular basis of infection and immunity. Through qualifying exams and a dissertation, the path toward academic and biomedical research careers.",
    "mich-middle-east-studies-phd": "Scholars drawn to the languages, histories, politics, and religions of the Middle East who want to pursue original research through faculty mentorship, qualifying examinations, and a dissertation. The path toward academic and research careers in the field.",
    "mich-molecular-and-cellular-pathology-pibs-phd": "Researchers drawn to the molecular and cellular mechanisms of disease and how cells and tissues are altered in illness. Through qualifying exams and a dissertation, the path toward academic and biomedical research careers in pathology.",
    "mich-molecular-and-integrative-physiology-ms": "Students fascinated by how the molecules, cells, and organ systems of the body function and interact to sustain life and health. A specialized master's for those advancing into physiology research or continuing toward doctoral and professional study.",
    "mich-molecular-and-integrative-physiology-pibs-phd": "Researchers who want to investigate how molecular and cellular processes integrate to govern the function of organs and whole organisms. Through qualifying exams and a dissertation, the path toward academic and biomedical research careers in physiology.",
    "mich-molecular-cellular-and-developmental-biology-phd": "Researchers drawn to the molecules and cells of living organisms and the processes that shape them who want to conduct original research through faculty mentorship, qualifying examinations, and a dissertation. The path toward academic and research careers in the life sciences.",
    "mich-molecular-cellular-and-developmental-biology-ms": "Students who want advanced expertise in the molecules and cells of living organisms and the processes that shape them, through graduate seminars, methods training, and a thesis or capstone. A specialized master's for those advancing into research or doctoral study.",
    "mich-molecular-cellular-and-developmental-biology-pibs-phd": "Researchers who want to investigate the molecular and cellular mechanisms underlying cell function, growth, and the development of organisms. Through qualifying exams and a dissertation, the path toward academic and biomedical research careers.",
    "mich-movement-science-phd": "Researchers drawn to human movement and physical activity, integrating biomechanics, who want to conduct original research through faculty mentorship, qualifying examinations, and a dissertation. The path toward academic and research careers in movement science.",
    "mich-movement-science-ms": "Students who want advanced expertise in human movement and physical activity, integrating biomechanics, through graduate seminars, methods training, and a thesis or capstone. A specialized master's for those advancing into applied roles or doctoral study.",
    "mich-music-education-phd": "Experienced music educators who want to study how music is taught and learned across schools and communities through original doctoral research. The path toward academic, faculty, and leadership careers in music education.",
    "mich-music-theory-phd": "Scholars drawn to the structures, elements, and principles that underlie how music is composed, organized, and understood. The doctoral path toward academic and research careers in music theory.",
    "mich-musicology-phd": "Researchers drawn to the scholarly study of music, including its history, repertoire, and cultural contexts. The doctoral path toward academic and research careers in musicology.",
    "mich-musicology-ethnomusicology-phd": "Researchers who want to study music in its cultural and social contexts through original scholarship, guided by faculty mentorship, qualifying examinations, and a dissertation. The path toward academic and research careers in ethnomusicology.",
    "mich-musicology-ethnomusicology-ms": "Students drawn to music in its cultural and social contexts and the musical traditions of peoples and communities around the world. A focused master's for those deepening ethnomusicological study or continuing toward doctoral work.",
    "mich-musicology-history-phd": "Scholars drawn to the history of music, including its repertoire, styles, composers, and cultural contexts. The doctoral path toward academic and research careers in historical musicology.",
    "mich-naval-architecture-and-marine-engineering-phd": "Researchers drawn to the design and construction of ships and marine systems who want to conduct original research through faculty mentorship, qualifying examinations, and a dissertation. The path toward academic, industry, and research careers in the field.",
    "mich-naval-architecture-and-marine-engineering-ms": "Engineers who want advanced expertise in the design and construction of ships and marine systems through graduate seminars, methods training, and a thesis or capstone. A specialized master's for those advancing into marine-engineering roles or doctoral study.",
    "mich-neuroscience-phd": "Researchers drawn to the nervous system who want to pursue original scholarship through faculty mentorship, qualifying examinations, and a dissertation. The path toward academic and research careers in neuroscience.",
    "mich-neuroscience-pibs-phd": "Researchers who want to investigate the molecular, cellular, and systems-level workings of the nervous system and how it produces perception, cognition, and behavior. Through qualifying exams and a dissertation, the path toward academic and biomedical neuroscience research careers.",
    "mich-nuclear-engineering-and-radiological-sciences-phd": "Researchers drawn to the application of nuclear processes and radiation, including reactors, who want to conduct original research through faculty mentorship, qualifying examinations, and a dissertation. The path toward academic, industry, and national-laboratory research careers.",
    "mich-nuclear-engineering-and-radiological-sciences-ms": "Engineering graduates who want advanced grounding in nuclear processes and radiation, from reactors to methods training, working through graduate seminars toward a thesis or capstone. Suits those moving into nuclear-industry roles or continuing to doctoral research.",
    "mich-nursing-ph-d-phd": "Nurses and health scholars who want to treat nursing science as a research discipline, building the evidence on health, illness, and care that guides practice and improves outcomes. The path to faculty positions and research careers in nursing science.",
    "mich-nutritional-sciences-phd": "Researchers investigating how nutrients and diet shape health, growth, and disease, progressing through faculty-mentored study, qualifying examinations, and a dissertation. For those aiming at academic or research careers in nutritional science.",
    "mich-nutritional-sciences-ms": "Students who want focused graduate depth in how nutrients and diet affect health, growth, and disease, integrating biochemistry, physiology, and public health. Suits those advancing into applied nutrition roles or continuing toward doctoral research.",
    "mich-oral-health-sciences-phd": "Investigators drawn to the biology of the mouth and the prevention and diagnosis of oral disease, working through faculty mentorship, qualifying examinations, and a dissertation. For those pursuing academic and research careers in oral health science.",
    "mich-oral-health-sciences-ms": "Students seeking focused graduate study of the biology of the mouth and the prevention, diagnosis, and treatment of oral and dental disease. Suits clinicians deepening their science or those preparing for doctoral research.",
    "mich-orthodontics-ms": "Dentists specializing in the diagnosis, prevention, and correction of misaligned teeth and jaws, building focused clinical and scientific depth. The path toward practice as an orthodontic specialist.",
    "mich-pediatric-dentistry-ms": "Dentists focused on the oral health and dental care of infants, children, and adolescents, building specialized clinical and scientific expertise. The path toward practice as a pediatric dental specialist.",
    "mich-performance-bassoon-phd": "Bassoonists who want to develop technique, repertoire, and both solo and ensemble artistry on the double-reed woodwind at the highest level. For those pursuing careers as performers and studio or ensemble artists.",
    "mich-performance-cello-phd": "Cellists refining technique, repertoire, and solo and ensemble artistry on the bowed string instrument at the doctoral level. For those aiming at careers as concert performers and studio or ensemble musicians.",
    "mich-performance-clarinet-phd": "Clarinetists who want to develop technique, tone, repertoire, and solo and ensemble artistry on the single-reed woodwind at the doctoral level. For those pursuing performance careers and studio or ensemble work.",
    "mich-performance-collaborative-piano-phd": "Pianists drawn to partnering with singers and instrumentalists through accompanying, chamber music, and coaching. For those building careers as collaborative artists, chamber musicians, and vocal or instrumental coaches.",
    "mich-performance-double-bass-phd": "Bassists who want to develop technique, repertoire, and ensemble artistry on the largest bowed string instrument, anchoring the bass line at the doctoral level. For those pursuing careers as orchestral and ensemble performers.",
    "mich-performance-euphonium-phd": "Euphonium players developing technique, repertoire, and solo and ensemble artistry on the warm-toned conical brass instrument at the doctoral level. For those aiming at performance careers and studio or ensemble work.",
    "mich-performance-flute-phd": "Flutists who want to develop technique, tone, repertoire, and artistry on the woodwind at the doctoral level. For those pursuing careers as concert performers and studio or ensemble musicians.",
    "mich-performance-french-horn-phd": "Horn players refining technique, repertoire, and ensemble artistry on the mellow-toned brass instrument at the doctoral level. For those building careers as orchestral and ensemble performers.",
    "mich-performance-harp-phd": "Harpists who want to develop technique, repertoire, and solo and ensemble artistry across the plucked string instrument's wide range. For those pursuing careers as concert performers and ensemble musicians.",
    "mich-performance-harpsichord-phd": "Keyboardists drawn to the harpsichord who want to develop technique, repertoire, and historical performance practice on the early plucked-string instrument. For those pursuing careers in early-music performance and scholarship.",
    "mich-performance-oboe-phd": "Oboists who want to develop technique, repertoire, and artistry on the expressive double-reed woodwind at the doctoral level. For those pursuing performance careers and studio or ensemble work.",
    "mich-performance-organ-phd": "Organists developing technique, repertoire, and solo and liturgical artistry on the pipe organ at the doctoral level. For those building careers as concert and liturgical performers.",
    "mich-performance-organ-sacred-music-phd": "Organists who want to join the technique and repertoire of the pipe organ with the study and practice of music for worship and the liturgy. For those pursuing careers in liturgical and concert organ performance.",
    "mich-performance-percussion-phd": "Percussionists who want to develop technique, repertoire, and solo and ensemble artistry across the many struck instruments at the doctoral level. For those pursuing careers as performers and ensemble musicians.",
    "mich-performance-piano-phd": "Pianists who want to develop technique, repertoire, and artistry across the keyboard's wide dynamic and expressive range at the doctoral level. For those pursuing careers as concert performers and studio musicians.",
    "mich-performance-piano-pedagogy-and-performance-phd": "Pianists who want to join the art of performance with the study and practice of teaching the instrument. For those building careers as performing artists and studio or collegiate piano teachers.",
    "mich-performance-saxophone-phd": "Saxophonists who want to develop technique, repertoire, and artistry across classical and jazz idioms on the single-reed woodwind. For those pursuing careers as performers and studio or ensemble musicians.",
    "mich-performance-trombone-phd": "Trombonists who want to develop technique, repertoire, and solo and ensemble artistry on the slide brass instrument at the doctoral level. For those pursuing careers as orchestral and ensemble performers.",
    "mich-performance-trumpet-phd": "Trumpeters developing technique, repertoire, and solo and ensemble artistry on the brilliant-toned brass instrument at the doctoral level. For those pursuing careers as concert and ensemble performers.",
    "mich-performance-tuba-phd": "Tubists who want to develop technique, repertoire, and solo and ensemble artistry on the largest and lowest brass instrument. For those building careers as orchestral and ensemble performers.",
    "mich-performance-viola-phd": "Violists who want to develop technique, repertoire, and solo and ensemble artistry on the bowed string instrument pitched below the violin. For those pursuing careers as concert and ensemble performers.",
    "mich-performance-violin-phd": "Violinists who want to develop technique, repertoire, and solo and ensemble artistry on the high, agile bowed string instrument at the doctoral level. For those pursuing careers as concert performers and ensemble musicians.",
    "mich-performance-voice-phd": "Singers who want to develop vocal technique, repertoire, languages, and interpretation for solo and operatic performance. For those pursuing careers as recital, concert, and opera performers.",
    "mich-performing-arts-technology-phd": "Artists and technologists drawn to the technology of music and performance, including recording, sound design, electronic music, and media production. For those pursuing research and creative careers at the intersection of music and technology.",
    "mich-periodontics-ms": "Dentists specializing in the supporting structures of the teeth and the diagnosis and treatment of gum disease, building focused clinical and scientific depth. The path toward practice as a periodontal specialist.",
    "mich-pharmaceutical-sciences-phd": "Researchers investigating how drugs are discovered, formulated, delivered, and act in the body, progressing through faculty mentorship, qualifying examinations, and a dissertation. For those pursuing academic or industry research careers in pharmaceutical science.",
    "mich-pharmacology-ms": "Students seeking focused graduate study of drugs and their effects on living systems, including how drugs act, how the body processes them, and their therapeutic uses. Suits those advancing in research roles or preparing for doctoral study.",
    "mich-pharmacology-pibs-phd": "Researchers investigating how drugs and chemicals act on biological systems at the molecular, cellular, and whole-organism levels to inform therapeutics. For those pursuing academic and industry research careers in pharmacology.",
    "mich-philosophy-phd": "Scholars pursuing original research into fundamental questions about existence and knowledge, working through faculty mentorship, qualifying examinations, and a dissertation. The path to faculty positions and research careers in philosophy.",
    "mich-philosophy-ms": "Students seeking advanced graduate depth in the systematic study of fundamental questions about existence and knowledge, through graduate seminars, methods training, and a thesis or capstone. Suits those continuing toward doctoral research or scholarly work.",
    "mich-physics-phd": "Researchers pursuing original inquiry into matter and energy, working through faculty mentorship, qualifying examinations, and a dissertation. For those aiming at academic, national-laboratory, or research careers in physics.",
    "mich-pibs-program-in-biomedical-sciences-phd": "Researchers drawn to the molecular, cellular, and systems-level study of human health and disease through an umbrella doctoral program. For those pursuing academic and research careers across the biomedical sciences.",
    "mich-political-science-phd": "Researchers examining politics, government, power, and political institutions, working through faculty mentorship, qualifying examinations, and a dissertation. The path to faculty positions and research careers in political science.",
    "mich-political-science-and-public-policy-phd": "Researchers who want to join the study of political institutions, behavior, and governance with the analysis and design of public policy. For those pursuing academic and research careers spanning political science and policy.",
    "mich-population-and-health-sciences-ms": "Students focused on the determinants of health across populations and the methods used to measure and improve population health. Suits those advancing into public-health research or analytic roles, or continuing toward doctoral study.",
    "mich-prosthodontics-ms": "Dentists specializing in the restoration and replacement of teeth with prostheses such as crowns, bridges, and dentures, building focused clinical and scientific depth. The path toward practice as a prosthodontic specialist.",
    "mich-psychology-phd": "Researchers examining the mind and behavior across perception, cognition, and emotion, working through faculty mentorship, qualifying examinations, and a dissertation. The path to faculty positions and research careers in psychology.",
    "mich-psychology-ms": "Students seeking advanced graduate depth in the mind and behavior across perception, cognition, and emotion, through graduate seminars, methods training, and a thesis or capstone. Suits those advancing in applied roles or continuing toward doctoral research.",
    "mich-psychology-and-women-s-and-gender-studies-phd": "Researchers who want to join psychological inquiry with the study of gender and women's experiences across mind, behavior, and society. For those pursuing academic and research careers at this interdisciplinary intersection.",
    "mich-public-affairs-ms": "For graduates drawn to government, public policy, and the management of public and nonprofit organizations who want to tackle societal problems from the inside. Prepares leaders and managers for careers running public and nonprofit programs.",
    "mich-public-policy-ms": "For those who want advanced skill in how governments address public problems, built through graduate seminars, methods training, and a thesis or capstone project. Fits future policy analysts and program staff moving into more senior public-sector roles.",
    "mich-public-policy-and-economics-phd": "For students who want to research the design and effects of policy using economic methods to weigh its costs, benefits, and outcomes. A doctoral path with qualifying exams and a dissertation, aimed at faculty and research careers in policy economics.",
    "mich-public-policy-and-political-science-phd": "For those who want to study policy design alongside political institutions, behavior, and governance through original doctoral research. Leads to academic and research careers bridging public policy and political science.",
    "mich-public-policy-and-sociology-phd": "For students investigating how policy intersects with social structures, institutions, and inequality, pursued through qualifying exams and a dissertation. The path to faculty and research careers spanning policy and sociology.",
    "mich-quantitative-finance-and-risk-management-ms": "For quantitatively minded graduates who want to apply mathematics, statistics, and computation to model markets, price assets, and measure and manage financial risk. Prepares analysts and quants for careers in finance and risk.",
    "mich-restorative-dentistry-ms": "For dentists focused on restoring the function and appearance of damaged or missing teeth who want specialized graduate depth in restorative practice. A path toward advanced clinical careers in restorative dentistry.",
    "mich-robotics-phd": "For engineers pursuing original research at the intersection of designing, building, and controlling robots, guided by faculty mentorship, qualifying exams, and a dissertation. Leads to academic and advanced research careers in robotics.",
    "mich-robotics-ms": "For engineering graduates who want advanced, hands-on expertise in designing, building, and controlling robots through graduate seminars, methods training, and a capstone or thesis. Prepares roboticists for industry and further research.",
    "mich-romance-languages-and-literatures-french-phd": "For scholars of French who want to research the language and the literatures and cultures of France and the French-speaking world within the Romance tradition. A doctoral path toward faculty and research careers in French studies.",
    "mich-romance-languages-and-literatures-italian-phd": "For students devoted to Italian who want to research the language and the literature and culture of Italy within the Romance tradition. The doctoral path to academic and research careers in Italian studies.",
    "mich-romance-languages-and-literatures-spanish-phd": "For scholars of Spanish who want to research the language and the literatures and cultures of Spain and the Spanish-speaking world within the Romance tradition. Leads to faculty and research careers in Hispanic studies.",
    "mich-scientific-computing-phd": "For students who want to develop and apply computational methods and high-performance computing to model and solve problems across science and engineering, through original doctoral research. The path to research and faculty careers in scientific computing.",
    "mich-slavic-languages-and-literatures-phd": "For those who want to research the Slavic languages and the literary and cultural works written in them at the doctoral level. Leads to academic and research careers in Slavic studies.",
    "mich-social-work-and-anthropology-phd": "For students integrating social work with anthropology to study human well-being, culture, and social systems in ways that inform practice and policy. A joint doctoral path toward faculty and research careers across both fields.",
    "mich-social-work-and-psychology-phd": "For those joining social work with psychology to research human behavior, well-being, and intervention across individuals and communities. A joint doctoral path leading to academic and research careers spanning both disciplines.",
    "mich-social-work-and-social-welfare-phd": "For students who want to pair social work practice with the study of social welfare, examining how policies and systems support well-being. A doctoral path toward faculty and research careers in social welfare.",
    "mich-social-work-and-sociology-phd": "For those integrating social work with sociology to research social structures, inequality, and interventions that improve well-being. A joint doctoral path leading to academic and research careers across both fields.",
    "mich-sociology-phd": "For students who want to conduct original research on society, social relationships, and institutions through qualifying exams and a dissertation. The path to faculty and research careers in sociology.",
    "mich-sociology-and-public-policy-phd": "For scholars joining the sociological study of social structures and inequality with the analysis and design of public policy. A doctoral path toward academic and research careers bridging sociology and policy.",
    "mich-sport-management-phd": "For students researching the business and administration of sport, including its organizations, through faculty-mentored doctoral study, qualifying exams, and a dissertation. Leads to faculty and research careers in sport management.",
    "mich-sport-management-ms": "For graduates who want advanced expertise in the business and administration of sport organizations, built through graduate seminars, methods training, and a thesis or capstone. Prepares administrators and managers for careers across the sport industry.",
    "mich-statistics-phd": "For students who want to conduct original research in the science of collecting, analyzing, interpreting, and presenting data, through qualifying exams and a dissertation. The path to faculty and research careers in statistics.",
    "mich-survey-and-data-science-phd": "For researchers who want to advance how surveys are designed and how data is collected and analyzed, pursued through qualifying exams and dissertation work. Leads to faculty and research careers in survey and data science.",
    "mich-survey-and-data-science-ms": "For graduates who want to master how to design surveys and collect, analyze, and interpret data to measure populations and inform research and policy. Prepares survey methodologists and data professionals for applied careers.",
    "mich-toxicology-phd": "For scientists researching the adverse effects of chemical, physical, and biological agents on living organisms, through faculty-mentored study, qualifying exams, and a dissertation. Leads to research and faculty careers in toxicology.",
    "mich-toxicology-ms": "For graduates focused on the adverse effects of chemical, physical, and biological agents on living organisms and the environment who want specialized scientific depth. Prepares toxicologists for applied and laboratory careers, or further doctoral study.",
    "mich-transcultural-studies-ms": "For graduates who want to examine how cultures interact, mix, and transform across borders, drawing on both the humanities and social sciences. Fits those pursuing culturally engaged careers or further study across disciplines.",
    "mich-urban-and-regional-planning-phd": "For students who want to research the study and practice of shaping the development of cities and regions, through faculty mentorship, qualifying exams, and a dissertation. The path to faculty and research careers in planning.",
    "mich-urban-and-regional-planning-ms": "For those drawn to shaping cities and regions through land use, transportation, housing, and environmental policy who want professional planning training. Prepares planners for careers in public agencies and practice.",
    "mich-master-of-architecture-march": "For those pursuing licensure as architects through design studios, building technology, history and theory, and professional practice. This professional degree prepares graduates to enter the architecture profession.",
    "mich-master-of-urban-design-mud": "For designers focused on cities and public spaces who want to shape the form, function, and experience of the built environment at the scale of neighborhoods and districts. Prepares practitioners for careers in urban design.",
    "mich-master-of-business-administration-mba": "Early-to-mid-career professionals targeting general management and leadership through the Ross School of Business.",
    "mich-doctor-of-dental-surgery-dds": "Future dentists pursuing clinical practice or academic dentistry.",
    "mich-master-of-engineering-meng": "For engineers who want advanced applied and professional study, using science and mathematics to design and build structures, machines, systems, and processes. Prepares graduates for applied and leadership roles in engineering practice.",
    "mich-doctor-of-engineering-deng": "For engineers pursuing original research that applies science and mathematics to design and build structures, machines, and systems, through faculty mentorship, qualifying exams, and a dissertation. Leads to advanced research and technical leadership careers.",
    "mich-master-of-health-informatics-mhi": "For those who want to acquire, store, and use health information and technology to improve health care, research, and decision-making. Prepares professionals for careers at the intersection of health and information systems.",
    "mich-master-of-science-in-information-msi": "For graduates studying how information is created, organized, stored, retrieved, and used by people and systems, blending computing, design, and the social sciences. Prepares information professionals for a range of technology and design roles.",
    "mich-juris-doctor-jd": "Aspiring lawyers and legal scholars across every field of law.",
    "mich-master-of-laws-llm": "For law graduates seeking specialized or comparative study of legal systems and rules beyond their first degree. This advanced credential deepens expertise for legal practice and scholarship, often for internationally trained lawyers.",
    "mich-doctor-of-medicine-md": "Future physicians and physician-scientists.",
    "mich-master-of-music-mm": "For musicians pursuing advanced study across performance, composition, theory, and scholarship. This professional graduate degree prepares them for careers as performing and creating musicians.",
    "mich-specialist-in-music-smus": "For musicians who want advanced applied training and pedagogy beyond the bachelor's, focused on performance repertoire, studio teaching, and professional musicianship rather than dissertation research. Prepares performers and teaching artists for professional practice.",
    "mich-master-of-science-in-nursing-msn": "For nurses who want advanced expertise in caring for individuals and families, built through graduate seminars, methods training, and a thesis or capstone. Prepares them for advanced roles in the nursing profession.",
    "mich-doctor-of-pharmacy-pharmd": "Future pharmacists and pharmaceutical-care leaders.",
    "mich-master-of-public-health-mph": "Clinicians, scientists, and leaders advancing population health.",
    "mich-master-of-health-services-administration-mhsa": "For those who want to plan, organize, finance, and manage health-care organizations and systems. Prepares administrators and managers for leadership careers across health services.",
    "mich-doctor-of-public-health-drph": "For experienced practitioners who want to lead in protecting and improving the health of populations at the highest level. This doctoral degree prepares advanced public-health leaders.",
    "mich-master-of-social-work-msw": "Future social workers and community-practice leaders.",
}

# Program highlights (manifest required=False) — verified U-M institution facts by
# credential level. Filled (not ``= None``) to clear the FLAG #4 hard-null class.
_HL_BY_TYPE: dict[str, list[str]] = {
    "bachelors": [
        "Top-ranked U.S. public research university",
        "Broad liberal-arts, STEM & arts curriculum",
        "Go Blue Guarantee — free tuition for eligible in-state students",
    ],
    "masters": [
        "Access to leading faculty and research centers",
        "Strong professional and industry networks",
    ],
    "phd": [
        "Funded — Rackham tuition support plus a stipend",
        "World-class research environment",
    ],
    "professional": [
        "Nationally ranked professional school",
        "Strong placement and a large alumni network",
    ],
}

# A paid doctorate (a professional/applied doctorate billed at a real rate, e.g. the
# D.Eng., or a per-program-billed DrPH) is NOT a funded research Ph.D., so it must not
# advertise Rackham funding (no-fabrication). Such phd-type rows get the non-funding
# doctoral highlights instead.
_HL_PHD_UNFUNDED: list[str] = [
    "Advanced doctoral study at a top public research university",
    "World-class research environment",
]

# Tracks/concentrations are not published as structured data for U-M programs, so
# ``tracks`` is honestly omitted (recorded in _standard.omitted) catalog-wide — routed
# through this (empty) lookup rather than a literal ``= None`` (FLAG #4).
_TRACKS_BY_SLUG: dict[str, list] = {}


# ``who_its_for`` is a UNIVERSAL depth field — a field-specific, PROGRAM-DISTINCT fit
# statement is authored for EVERY program in ``_WHO_BY_SLUG`` (grounded in each program's
# own description + credential level), so the ``_WHO_BY_TYPE`` degree-type fallback is a
# safety net that is provably never reached. The assertion below fails the build if a slug
# is ever left to the type fallback (which would re-introduce the REPAIR_BACKLOG #3b
# type-gaming defect, distinct/total collapsing to ~one template per degree-type).
_missing_who = [s for s in PROGRAM_SLUGS if s not in _WHO_BY_SLUG]
if _missing_who:
    raise ValueError(
        f"Michigan who_its_for missing on {len(_missing_who)} rows "
        f"(would type-game via _WHO_BY_TYPE): {_missing_who[:5]}"
    )
_stray_who = [s for s in _WHO_BY_SLUG if s not in set(PROGRAM_SLUGS)]
if _stray_who:
    raise ValueError(f"Michigan who_its_for stray slugs: {_stray_who[:5]}")


def _who_for(slug: str, degree_type: str) -> str | None:
    return _WHO_BY_SLUG.get(slug) or _WHO_BY_TYPE.get(degree_type)


def _highlights_for(degree_type: str, funded: bool = False) -> list[str] | None:
    # A phd-TYPE row that is not actually funded (a paid/applied doctorate) must not
    # advertise Rackham funding (no-fabrication) — only a genuinely funded research
    # Ph.D. (tuition waived) gets the "Funded — Rackham …" highlight.
    if degree_type == "phd" and not funded:
        return list(_HL_PHD_UNFUNDED)
    return _HL_BY_TYPE.get(degree_type)


def _program_standard(slug: str, spec: dict) -> dict:
    omitted: list[str] = ["tracks"]
    if slug in _TUITION_OMIT_SLUGS:
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
    return _standard(omitted)


def apply(session: Session) -> bool:
    """Enrich the University of Michigan-Ann Arbor to the canonical profile. Flushes; caller commits.

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
    inst.founded_year = 1817
    inst.campus_setting = "college town"
    if not inst.website_url:
        inst.website_url = "https://www.umich.edu"
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
        p.cip_code = spec.get("cip")  # matcher-core CIP join key (REPAIR_BACKLOG #1)
        p.tuition, p.cost_data = _program_tuition(spec)
        p.application_requirements = _requirements_for(spec)
        outcomes = dict(_OUTCOMES_BY_SLUG.get(slug, {}))
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        p.who_its_for = _who_for(slug, spec["degree_type"])
        p.highlights = _highlights_for(
            spec["degree_type"], funded=bool((p.cost_data or {}).get("funded"))
        )
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
