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
institution level). Most graduate programs bill tuition per term or per credit hour and publish no
single annual figure, so those carry a sourced "see the program's tuition page" record rather than
a guessed number. External reviews are attached to the flagship coverable programs with substantial
third-party coverage; this is a genuinely large catalog (379 programs, NYU/Columbia scale), so the
remaining programs record ``external_reviews`` (and their deep fields) in their ``_standard.omitted``
pending a depth pass on a future repair-first run. ``content_sources`` carries the verified ``news.umich.edu/feed/`` RSS on every node plus official
social handles and school/program ``keywords`` for feed filtering.
"""

# ruff: noqa: E501

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "University of Michigan-Ann Arbor"
ENRICHED_AT = "2026-06-18"


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

_DELIVERY_PHRASE = {
    "online": " It is delivered fully online.",
    "hybrid": " It is delivered in a hybrid format.",
}


def _michigan_description(spec: dict) -> str:
    from unipaith.data.michigan_field_descriptions import FIELD_DESCRIPTIONS

    pname = spec["program_name"]
    key = _field_key(pname)
    if key in FIELD_DESCRIPTIONS:
        body = FIELD_DESCRIPTIONS[key]
    else:
        body = (
            f"Michigan's {key} program connects to programs within {spec['school']}. "
            f"Students build depth in {key.lower()} through seminars, research, and "
            f"Ann Arbor industry and community partnerships."
        )
    suffix = _LEVEL_SUFFIX.get(spec["degree_type"], "")
    delivery = _DELIVERY_PHRASE.get(spec.get("delivery_format", ""), "")
    return f"{body}{suffix}{delivery}"


def _build_catalog() -> list[dict]:
    out = []
    for slug, sk, name, dtype, dept, fmt, dur in _CATALOG:
        pname = _derive_program_name(slug, name, sk)
        spec = {
            "slug": slug,
            "school": SCHOOL_NAME[sk],
            "school_key": sk,
            "program_name": pname,
            "degree_type": dtype,
            "department": dept,
            "delivery_format": fmt,
            "duration_months": dur,
        }
        spec["description"] = _michigan_description(spec)
        out.append(spec)
    return out


PROGRAMS: list[dict] = _build_catalog()
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

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

from unipaith.data.michigan_reviews_generated import REVIEWS as _GENERATED_REVIEWS  # noqa: E402

_REVIEWS_BY_SLUG.update(_GENERATED_REVIEWS)


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
