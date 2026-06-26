"""University of North Carolina at Chapel Hill — gold-standard profile.

Institution + schools + full degree catalog.

Every value below is verified against an authoritative source (UNC's official pages —
unc.edu, the undergraduate catalog at catalog.unc.edu, each school's site, the University
Cashier and Office of Scholarships and Student Aid, the Office of Institutional Research and
Assessment Common Data Set, the U.S. Dept. of Education College Scorecard / NCES for UNITID
199120, and the ranking bodies) and carries a citation, or is honestly omitted (recorded in
that node's ``_standard.omitted``) — never guessed.

Scope note: UNC entered as a 5-stub institution seed (the 2026-06 US-News bulk seed) whose
five programs ALL shipped with an EMPTY ``description_text`` and a NULL ``department`` — a
blank student page and zero matcher embedding (REPAIR_BACKLOG run 86 entry #2, a worst-tier
open defect; the sibling Georgetown, WashU, and UVA seeds were cleared earlier this cycle).
This pass (2026-06-26) takes the institution to gold (filling the seed's missing report-card /
admissions-funnel / diversity / cost-aid / campus-resources / feed fields and adding a verified
4th campus photo) and REPLACES the five empty stubs with a verified, real-named 89-program
catalog across UNC's degree-granting schools — the College of Arts & Sciences, the School of
Data Science and Society, the Hussman School of Journalism and Media, the Kenan-Flagler
Business School, the Gillings School of Global Public Health, the School of Nursing, the
Eshelman School of Pharmacy, the Adams School of Dentistry, the School of Medicine, the School
of Law, the School of Education, the School of Information and Library Science, and the School
of Social Work.

Every program carries a researched, field-specific ``description_text`` (anti-stub clean,
gold contrast), a ``who_its_for`` statement, a real owning ``department``, a ``cip_code``, a
verified ``delivery_format``, and published 2025-26 tuition per credential level. UNC is a
PUBLIC university, so the scalar ``tuition`` the matcher reads is the NON-RESIDENT
(out-of-state) published rate, while ``cost_data.breakdown`` preserves BOTH the NC-resident and
non-resident rates. Working UNC news feeds (the institution feed plus College / Hussman /
Gillings / Law feeds), sourced ``external_reviews`` on the obviously-coverable Kenan-Flagler
MBA and the J.D., and a verified 4-photo campus gallery round out the profile. Nothing is padded.

Tuition (all verified 2025-26, UNC University Cashier): undergraduate (uniform across schools)
NC-resident $7,019 / non-resident $43,152. Graduate / professional non-resident annual figures
(NC-resident in the breakdown): MBA $70,908; Master of Accounting $69,425 (15-month total);
J.D. $51,319; M.D. $61,283; Pharm.D. $48,777; D.D.S. $66,267; M.P.H. $38,530; M.S.W. $33,721;
M.S.N./D.N.P. $37,221; M.S.L.S. $36,171; M.S.I.S. $35,361; M.C.R.P. $32,421; M.P.P. $37,921;
M.A.T. $30,421; M.S. Computer Science $39,421; M.A. Media and Communication $34,403.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "University of North Carolina at Chapel Hill"

ENRICHED_AT = "2026-06-26"


def _standard(omitted: list[str] | None = None) -> dict:
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }


_OMITTED_INSTITUTION: list[str] = [
    # A single current instructional-faculty headcount could not be verified to one citable
    # figure this session, so the count is omitted rather than guessed.
    "school_outcomes.scale.faculty_count",
    # UNC's published undergraduate student-faculty ratio is reported inconsistently across
    # public sources, so it is omitted rather than picking one unverified value.
    "school_outcomes.scale.student_faculty_ratio",
    # UNC reports first-destination outcomes per school rather than as one institution-wide
    # employed-or-continuing-ed percentage / top-industry list, so both are omitted here.
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
]

RANKING_DATA: dict = {
    "ownership_type": "public",
    "accreditor": "SACSCOC",
    "carnegie_classification": "Doctoral Universities: Very High Research Activity (R1)",
    "qs_world_university_rankings": {"rank": 140, "year": 2026},
    "times_higher_education": {"rank": 78, "year": 2026},
    "us_news_national": {"rank": 27, "year": 2025},
}

SCHOOL_OUTCOMES: dict = {
    # Class of 2028 admissions funnel (10,209 admitted of 66,535 applicants).
    "admit_rate": 0.153,
    # College Scorecard average net price after grant aid.
    "avg_net_price": 12414,
    # College Scorecard median earnings 10 years after entry (institution-wide).
    "median_earnings_10yr": 72200,
    # NCES / UNC CDS — six-year graduation rate.
    "graduation_rate_6yr": 0.912,
    # UNC CDS 2024-25 — first-time first-year retention.
    "retention_rate_first_year": 0.966,
    # UNC CDS 2024-25 — SAT/ACT middle ranges of enrolled first-years who submitted scores.
    "test_scores": {
        "sat_total_25_75": [1400, 1530],
        "act_25_75": [28, 34],
        "source": "UNC-Chapel Hill Common Data Set 2024-2025",
        "source_url": (
            "https://oira.unc.edu/wp-content/uploads/sites/297/2025/08/"
            "CDS_UNCCH_2024-25_20250829.pdf"
        ),
    },
    # Undergraduate race/ethnicity (UNC CDS 2024-25, shares of 21,075 undergraduates).
    # Categories do not sum to 100% (unknown and other small groups make up the remainder).
    "demographics": {
        "white": 0.528,
        "asian": 0.159,
        "hispanic": 0.096,
        "black": 0.073,
        "international": 0.064,
        "two_or_more": 0.050,
        "note": (
            "Undergraduate race/ethnicity (UNC Common Data Set 2024-25); race/ethnicity "
            "unknown and other small categories make up the remainder, so shares do not "
            "sum to 100%."
        ),
        "source": "UNC-Chapel Hill Common Data Set 2024-2025",
        "source_url": (
            "https://oira.unc.edu/wp-content/uploads/sites/297/2025/08/"
            "CDS_UNCCH_2024-25_20250829.pdf"
        ),
    },
    "financial_aid": {
        # Share of undergraduates receiving federal Pell grants.
        "pell_grant_rate": 0.20,
        # UNC Office of Scholarships and Student Aid — 2025-26 estimated out-of-state
        # undergraduate total cost of attendance (on-campus, standard budget).
        "cost_of_attendance": 55398,
        "source": (
            "UNC Office of Scholarships and Student Aid — 2025-26 cost of attendance; "
            "College Scorecard net price"
        ),
        "source_url": "https://studentaid.unc.edu/current/costs/",
    },
    "research": {
        "labs": [
            "UNC Lineberger Comprehensive Cancer Center",
            "Renaissance Computing Institute (RENCI)",
            "Carolina Population Center",
            "Frank Porter Graham Child Development Institute",
            "UNC Health",
        ],
        "areas": [
            "Cancer & biomedical research",
            "Public & global health",
            "Population & demographic science",
            "Child development & education",
            "Data science & computing",
            "Marine & environmental science",
        ],
        "lab_links": {
            "UNC Lineberger Comprehensive Cancer Center": "https://unclineberger.org/",
            "Renaissance Computing Institute (RENCI)": "https://renci.org/",
            "Carolina Population Center": "https://www.cpc.unc.edu/",
            "Frank Porter Graham Child Development Institute": "https://fpg.unc.edu/",
            "UNC Health": "https://www.unchealth.org/",
        },
        "source": "University of North Carolina at Chapel Hill — Research",
        "source_url": "https://research.unc.edu/",
    },
    "scale": {
        "research_centers": [
            "UNC Lineberger Comprehensive Cancer Center",
            "Carolina Population Center",
            "Renaissance Computing Institute (RENCI)",
        ],
    },
    "campus_life": {
        "athletics_division": "NCAA Division I (Atlantic Coast Conference)",
        "mascot": "Tar Heels",
        "housing": (
            "Residential campus in Chapel Hill, North Carolina, anchored by "
            "McCorkle Place and the Old Well."
        ),
        "resources": [
            {"label": "Carolina Athletics (Tar Heels)", "url": "https://goheels.com/"},
            {"label": "University Libraries", "url": "https://library.unc.edu/"},
            {"label": "Ackland Art Museum", "url": "https://ackland.org/"},
            {"label": "University Career Services", "url": "https://careers.unc.edu/"},
        ],
    },
    "flagship": {
        "applicants": 66535,
        "admits": 10209,
        "admissions_cycle": "Class of 2028 (entering fall 2024; UNC)",
        "founded_year": 1789,
    },
    "location": {"lat": 35.9049, "lng": -79.0469},
    "campus_basics": {"location": "Chapel Hill, North Carolina"},
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (UNC, UNITID 199120)",
            "url": "https://collegescorecard.ed.gov/school/?199120",
        },
        {
            "label": "NCES College Navigator — UNC-Chapel Hill (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=199120",
        },
        {
            "label": "UNC-Chapel Hill Common Data Set 2024-2025",
            "url": (
                "https://oira.unc.edu/wp-content/uploads/sites/297/2025/08/"
                "CDS_UNCCH_2024-25_20250829.pdf"
            ),
        },
        {
            "label": "UNC University Cashier — 2025-26 Tuition and Fees",
            "url": "https://cashier.unc.edu/tuition-fees/",
        },
        {
            "label": "QS World University Rankings 2026 — UNC-Chapel Hill",
            "url": "https://www.topuniversities.com/universities/university-north-carolina-chapel-hill",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — UNC-Chapel Hill",
            "url": (
                "https://www.timeshighereducation.com/world-university-rankings/"
                "university-north-carolina-chapel-hill"
            ),
        },
        {
            "label": "U.S. News Best Colleges 2025 — UNC-Chapel Hill (#27 National Universities)",
            "url": "https://www.usnews.com/best-colleges/university-of-north-carolina-chapel-hill-2974",
        },
    ],
}

UNDERGRAD_COUNT = 21075

DESCRIPTION = (
    "The University of North Carolina at Chapel Hill is a public research university in "
    "Chapel Hill, North Carolina, chartered in 1789 and the first public university in the "
    "United States to enroll students. A member of the Association of American Universities, "
    "it enrolls about 21,000 undergraduates alongside its graduate and professional students "
    "and is classified as a Carnegie R1 very-high-research-activity university.\n\n"
    "Carolina is organized into the College of Arts & Sciences and a range of professional "
    "schools spanning business, journalism, public health, nursing, pharmacy, dentistry, "
    "medicine, law, education, information and library science, social work, and data "
    "science: the College of Arts & Sciences, the School of Data Science and Society, the "
    "Hussman School of Journalism and Media, the Kenan-Flagler Business School, the Gillings "
    "School of Global Public Health, the School of Nursing, the Eshelman School of Pharmacy, "
    "the Adams School of Dentistry, the School of Medicine, the School of Law, the School of "
    "Education, the School of Information and Library Science, and the School of Social Work."
)

# ── Schools ────────────────────────────────────────────────────────────────
_COLLEGE = "College of Arts & Sciences"
_SDSS = "School of Data Science and Society"
_HUSSMAN = "Hussman School of Journalism and Media"
_KENAN = "Kenan-Flagler Business School"
_GILLINGS = "Gillings School of Global Public Health"
_NURSING = "School of Nursing"
_PHARM = "Eshelman School of Pharmacy"
_DENT = "Adams School of Dentistry"
_MED = "School of Medicine"
_LAW = "School of Law"
_EDUC = "School of Education"
_SILS = "School of Information and Library Science"
_SSW = "School of Social Work"

SCHOOLS: list[dict] = [
    {"name": _COLLEGE, "sort_order": 1, "description": (
        "The College of Arts & Sciences is UNC's largest academic unit and the home of the "
        "liberal arts, teaching the humanities, the natural and physical sciences, and the "
        "social sciences across dozens of departments and curricula, and educating the great "
        "majority of Carolina undergraduates.")},
    {"name": _SDSS, "sort_order": 2, "description": (
        "The School of Data Science and Society — UNC's newest school — awards undergraduate "
        "and graduate degrees in data science, integrating statistics, computing, and machine "
        "learning with attention to the societal and ethical dimensions of data.")},
    {"name": _HUSSMAN, "sort_order": 3, "description": (
        "The Hussman School of Journalism and Media educates undergraduates and graduate "
        "students in reporting, strategic communication, and media, pairing professional "
        "skills with the study of media's role in democracy and society.")},
    {"name": _KENAN, "sort_order": 4, "description": (
        "The Kenan-Flagler Business School educates undergraduates and graduate students in "
        "business, awarding the Bachelor of Science in Business Administration alongside the "
        "MBA and the Master of Accounting.")},
    {"name": _GILLINGS, "sort_order": 5, "description": (
        "The Gillings School of Global Public Health is one of the nation's leading public "
        "health schools, awarding undergraduate B.S.P.H. degrees and graduate degrees across "
        "biostatistics, epidemiology, health policy, environmental health, and nutrition.")},
    {"name": _NURSING, "sort_order": 6, "description": (
        "The School of Nursing prepares nurses from the bachelor's through the doctorate, "
        "pairing classroom science with clinical practice alongside UNC Health, with "
        "advanced-practice and clinical-leadership tracks.")},
    {"name": _PHARM, "sort_order": 7, "description": (
        "The Eshelman School of Pharmacy awards the Doctor of Pharmacy and graduate degrees in "
        "the pharmaceutical sciences, training pharmacists and researchers in medication "
        "therapy, drug discovery, and patient care.")},
    {"name": _DENT, "sort_order": 8, "description": (
        "The Adams School of Dentistry awards the Doctor of Dental Surgery and the Bachelor of "
        "Science in Dental Hygiene, training dentists and hygienists through preclinical "
        "science and supervised patient care.")},
    {"name": _MED, "sort_order": 9, "description": (
        "The School of Medicine awards the Doctor of Medicine and trains physicians and health "
        "scientists alongside UNC Health, and houses allied-health bachelor's programs and the "
        "joint biomedical engineering degree.")},
    {"name": _LAW, "sort_order": 10, "description": (
        "The School of Law awards the Juris Doctor and graduate legal degrees, known for a "
        "collegial culture, a strong public-service tradition, and broad placement into firms, "
        "clerkships, and government.")},
    {"name": _EDUC, "sort_order": 11, "description": (
        "The School of Education prepares teachers, counselors, and education leaders, awarding "
        "undergraduate degrees in elementary education and human development alongside graduate "
        "teaching and leadership programs.")},
    {"name": _SILS, "sort_order": 12, "description": (
        "The School of Information and Library Science awards undergraduate and graduate degrees "
        "in information and library science, studying how knowledge is organized, preserved, "
        "and connected with the people who need it.")},
    {"name": _SSW, "sort_order": 13, "description": (
        "The School of Social Work awards the Master of Social Work and doctoral degrees, "
        "preparing clinicians and leaders to support individuals, families, and communities "
        "through practice, policy, and research.")},
]

_SCHOOL_WEBSITE: dict[str, str] = {
    _COLLEGE: "https://college.unc.edu/",
    _SDSS: "https://datascience.unc.edu/",
    _HUSSMAN: "https://hussman.unc.edu/",
    _KENAN: "https://www.kenan-flagler.unc.edu/",
    _GILLINGS: "https://sph.unc.edu/",
    _NURSING: "https://nursing.unc.edu/",
    _PHARM: "https://pharmacy.unc.edu/",
    _DENT: "https://dentistry.unc.edu/",
    _MED: "https://www.med.unc.edu/",
    _LAW: "https://law.unc.edu/",
    _EDUC: "https://ed.unc.edu/",
    _SILS: "https://sils.unc.edu/",
    _SSW: "https://ssw.unc.edu/",
}

_ABOUT_DETAIL: dict[str, dict] = {
    _COLLEGE: {"founded": "1795"},
    _SDSS: {"founded": "2022"},
    _HUSSMAN: {"founded": "1909"},
    _KENAN: {"founded": "1919"},
    _GILLINGS: {"founded": "1939", "research_centers": ["Carolina Population Center"]},
    _NURSING: {"founded": "1950"},
    _PHARM: {"founded": "1897"},
    _DENT: {"founded": "1950"},
    _MED: {"founded": "1879", "research_centers": ["UNC Lineberger Comprehensive Cancer Center"]},
    _LAW: {"founded": "1845"},
    _EDUC: {"founded": "1885"},
    _SILS: {"founded": "1931"},
    _SSW: {"founded": "1920"},
}
_ABOUT_OMITTED: dict[str, list[str]] = {
    name: (
        ["about_detail.leadership", "about_detail.faculty"]
        + (
            []
            if "research_centers" in _ABOUT_DETAIL.get(name, {})
            else ["about_detail.research_centers"]
        )
    )
    for name in _SCHOOL_WEBSITE
}

# ── Channel feeds + official social links ──────────────────────────────────
# Each feed below was fetched live this session (verified 2026-06-26): the unc.edu feed is the
# institution feed and the shared feed for schools without their own working feed; the College,
# Hussman, Gillings, and Law carry their own working feeds.
_UNIV_RSS = "https://www.unc.edu/feed/"
_SCHOOL_RSS: dict[str, str] = {
    _COLLEGE: "https://college.unc.edu/feed/",
    _SDSS: _UNIV_RSS,
    _HUSSMAN: "https://hussman.unc.edu/feed/",
    _KENAN: _UNIV_RSS,
    _GILLINGS: "https://sph.unc.edu/feed/",
    _NURSING: _UNIV_RSS,
    _PHARM: _UNIV_RSS,
    _DENT: _UNIV_RSS,
    _MED: _UNIV_RSS,
    _LAW: "https://law.unc.edu/feed/",
    _EDUC: _UNIV_RSS,
    _SILS: _UNIV_RSS,
    _SSW: _UNIV_RSS,
}

_SOCIAL_UNC = {
    "instagram": "https://www.instagram.com/uncchapelhill/",
    "linkedin": "https://www.linkedin.com/school/unc-chapel-hill/",
    "x": "https://twitter.com/UNC",
    "youtube": "https://www.youtube.com/user/UNChapelHill",
    "facebook": "https://www.facebook.com/uncchapelhill",
}

_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _COLLEGE: ["Arts & Sciences", "College", "undergraduate"],
    _SDSS: ["Data Science", "data"],
    _HUSSMAN: ["Hussman", "journalism", "media"],
    _KENAN: ["Kenan-Flagler", "business", "MBA"],
    _GILLINGS: ["Gillings", "public health"],
    _NURSING: ["Nursing", "School of Nursing"],
    _PHARM: ["Pharmacy", "Eshelman"],
    _DENT: ["Dentistry", "Adams School", "dental"],
    _MED: ["Medicine", "UNC Health", "medical"],
    _LAW: ["Law", "School of Law", "legal"],
    _EDUC: ["Education", "teaching", "School of Education"],
    _SILS: ["Information", "library science", "SILS"],
    _SSW: ["Social Work", "School of Social Work"],
}


def _school_content(name: str) -> dict:
    return {
        "news_rss": _SCHOOL_RSS[name],
        "news_url": "https://www.unc.edu/news/",
        "news_curated": False,
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": _SOCIAL_UNC,
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


_INSTITUTION_CONTENT: dict = {
    "news_rss": _UNIV_RSS,
    "news_url": "https://www.unc.edu/news/",
    "news_curated": True,
    "social": _SOCIAL_UNC,
}

_COST_SRC = (
    "UNC University Cashier — 2025-26 Tuition and Fees",
    "https://cashier.unc.edu/tuition-fees/",
)
_UG_NET_PRICE = 12414

# A verified 4th campus photo (the seed shipped only 3 — below the >=4 gallery gate).
# The Old Well, UNC's iconic landmark; CC BY-SA 4.0 on Wikimedia Commons.
_EXTRA_CAMPUS_PHOTO = {
    "url": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/"
        "MJK49493_Old_Well_%28Chapel_Hill%2C_North_Carolina%29.jpg/"
        "1920px-MJK49493_Old_Well_%28Chapel_Hill%2C_North_Carolina%29.jpg"
    ),
    "credit": "Wikimedia Commons / Martin Kraft (CC BY-SA 4.0)",
}

# ── The catalog ────────────────────────────────────────────────────────────
_CATALOG: list[dict] = [
    dict(
        slug="unc-african-american-diaspora-studies-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in African, African American, and Diaspora Studies",
        department="Department of African, African American, and Diaspora Studies",
        cip="05.0201", va=7019, oos=43152, duration_months=48,
        keywords=["African, African American, and Diaspora Studies"],
        description=(
            "Spanning history, literature, politics, and the arts, this interdisciplinary "
            "field examines the experiences of African, African American, and Caribbean "
            "peoples and the global movements, cultures, and diasporas they created across "
            "continents and centuries."
        ),
        who_its_for=(
            "It fits students who want to understand Black history and culture across the "
            "world through history, literature, and social science."
        ),
    ),
    dict(
        slug="unc-american-studies-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in American Studies",
        department="Department of American Studies",
        cip="05.0102", va=7019, oos=43152, duration_months=48,
        keywords=["American Studies"],
        description=(
            "Drawing on history, literature, film, music, and material culture, this field "
            "investigates how American identity, power, and everyday life have been shaped, "
            "contested, and represented across the nation's regions and communities."
        ),
        who_its_for=(
            "It suits students curious about U.S. culture and society who prefer connecting "
            "many disciplines over a single one."
        ),
    ),
    dict(
        slug="unc-anthropology-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Anthropology",
        department="Department of Anthropology",
        cip="45.0201", va=7019, oos=43152, duration_months=48,
        keywords=["Anthropology"],
        description=(
            "Studying humanity across time and place, this field combines cultural, "
            "biological, archaeological, and linguistic approaches to understand how people "
            "live, make meaning, and adapt, often grounded in fieldwork and ethnographic "
            "observation."
        ),
        who_its_for=(
            "It fits students fascinated by human cultures and origins who want hands-on "
            "fieldwork and cross-cultural comparison."
        ),
    ),
    dict(
        slug="unc-archaeology-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Archaeology",
        department="Curriculum in Archaeology",
        cip="45.0301", va=7019, oos=43152, duration_months=48,
        keywords=["Archaeology"],
        description=(
            "Reconstructing past societies from their material traces, this field excavates "
            "and analyzes artifacts, structures, and landscapes, using stratigraphy, dating "
            "methods, and scientific analysis to interpret how ancient and historic peoples "
            "lived."
        ),
        who_its_for=(
            "It suits students drawn to uncovering the human past through excavation, lab "
            "analysis, and material evidence."
        ),
    ),
    dict(
        slug="unc-art-history-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Art History",
        department="Department of Art and Art History",
        cip="50.0703", va=7019, oos=43152, duration_months=48,
        keywords=["Art History"],
        description=(
            "Examining painting, sculpture, architecture, and visual culture across periods "
            "and regions, this field interprets how images convey meaning, analyzing style, "
            "iconography, patronage, and the social contexts that shaped artistic production."
        ),
        who_its_for=(
            "It fits students who love looking closely at art and want to interpret it within "
            "its history and culture."
        ),
    ),
    dict(
        slug="unc-asian-studies-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Asian Studies",
        department="Department of Asian and Middle Eastern Studies",
        cip="05.0103", va=7019, oos=43152, duration_months=48,
        keywords=["Asian Studies"],
        description=(
            "Covering the languages, histories, religions, and politics of East, South, and "
            "Southeast Asia, this field builds regional expertise through language study and "
            "interdisciplinary analysis of Asian societies past and present."
        ),
        who_its_for=(
            "It suits students who want deep regional and language grounding in Asia for "
            "careers spanning culture, policy, and business."
        ),
    ),
    dict(
        slug="unc-biology-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Biology",
        department="Department of Biology",
        cip="26.0101", va=7019, oos=43152, duration_months=48,
        keywords=["Biology"],
        description=(
            "Exploring life from molecules to ecosystems, this field studies how organisms "
            "function, evolve, and interact, spanning genetics, cell biology, physiology, "
            "ecology, and evolution through a broad liberal-arts lens."
        ),
        who_its_for=(
            "It fits students who want a flexible grounding in the life sciences alongside "
            "wide humanities and social-science study."
        ),
    ),
    dict(
        slug="unc-chemistry-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Chemistry",
        department="Department of Chemistry",
        cip="40.0501", va=7019, oos=43152, duration_months=48,
        keywords=["Chemistry"],
        description=(
            "Investigating matter and its transformations, this field examines atoms, "
            "molecules, and reactions across organic, inorganic, physical, and analytical "
            "branches, balancing chemical principles with broad study outside the laboratory."
        ),
        who_its_for=(
            "It suits students who want a solid chemistry foundation within a wide-ranging "
            "liberal-arts education."
        ),
    ),
    dict(
        slug="unc-classics-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Classics",
        department="Department of Classics",
        cip="16.1200", va=7019, oos=43152, duration_months=48,
        keywords=["Classics"],
        description=(
            "Centering on the languages, literature, and civilizations of ancient Greece and "
            "Rome, this field reads classical texts in their original tongues and studies the "
            "philosophy, art, and history of the ancient Mediterranean."
        ),
        who_its_for=(
            "It fits students drawn to ancient languages, literature, and the enduring legacy "
            "of the Greco-Roman world."
        ),
    ),
    dict(
        slug="unc-communication-studies-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Communication Studies",
        department="Department of Communication",
        cip="09.0101", va=7019, oos=43152, duration_months=48,
        keywords=["Communication Studies"],
        description=(
            "Analyzing how messages create meaning and shape social life, this field studies "
            "rhetoric, interpersonal and media communication, performance, and culture, "
            "examining persuasion, identity, and the power of words and images."
        ),
        who_its_for=(
            "It suits students interested in how communication and media influence people, "
            "organizations, and public life."
        ),
    ),
    dict(
        slug="unc-computer-science-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Computer Science",
        department="Department of Computer Science",
        cip="11.0701", va=7019, oos=43152, duration_months=48,
        keywords=["Computer Science"],
        description=(
            "Approaching computing through a liberal-arts lens, this field covers "
            "programming, algorithms, data structures, and computational thinking while "
            "leaving room to connect software with humanities and social-science questions."
        ),
        who_its_for=(
            "It fits students who want strong computing skills paired with broad study across "
            "other disciplines."
        ),
    ),
    dict(
        slug="unc-contemporary-european-studies-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Contemporary European Studies",
        department="Center for European Studies",
        cip="05.0106", va=7019, oos=43152, duration_months=48,
        keywords=["Contemporary European Studies"],
        description=(
            "Focusing on the modern continent, this field examines European politics, "
            "history, culture, and integration since the twentieth century, pairing language "
            "study with analysis of the European Union and transatlantic affairs."
        ),
        who_its_for=(
            "It suits students interested in contemporary Europe, its institutions, and its "
            "place in global politics."
        ),
    ),
    dict(
        slug="unc-data-science-ba", school=_SDSS,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Data Science",
        department="School of Data Science and Society",
        cip="30.7001", va=7019, oos=43152, duration_months=48,
        keywords=["Data Science"],
        description=(
            "Combining statistics, programming, and data analysis with humanistic and social "
            "inquiry, this field teaches how to collect, model, and interpret data while "
            "weighing its ethical and societal implications."
        ),
        who_its_for=(
            "It fits students who want to work with data while keeping a foot in social and "
            "humanistic questions."
        ),
    ),
    dict(
        slug="unc-dramatic-art-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Dramatic Art",
        department="Department of Dramatic Art",
        cip="50.0501", va=7019, oos=43152, duration_months=48,
        keywords=["Dramatic Art"],
        description=(
            "Studying theatre as performance and text, this field develops acting, directing, "
            "design, playwriting, and dramatic literature, exploring how live performance "
            "creates meaning and reflects the human condition."
        ),
        who_its_for=(
            "It suits students passionate about theatre who want both performance practice "
            "and the study of dramatic art."
        ),
    ),
    dict(
        slug="unc-economics-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Economics",
        department="Department of Economics",
        cip="45.0601", va=7019, oos=43152, duration_months=48,
        keywords=["Economics"],
        description=(
            "Examining how societies allocate scarce resources, this field analyzes markets, "
            "incentives, and policy across microeconomics and macroeconomics, using theory "
            "and data to explain decisions of individuals, firms, and governments."
        ),
        who_its_for=(
            "It fits students curious about markets and policy who want analytical training "
            "within a liberal-arts setting."
        ),
    ),
    dict(
        slug="unc-english-comparative-literature-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in English and Comparative Literature",
        department="Department of English and Comparative Literature",
        cip="23.0101", va=7019, oos=43152, duration_months=48,
        keywords=["English and Comparative Literature"],
        description=(
            "Reading literature in English across periods, genres, and national traditions, "
            "this field develops close interpretation, critical theory, and persuasive "
            "writing while comparing texts and ideas across languages and cultures."
        ),
        who_its_for=(
            "It suits students who love reading and writing and want to analyze literature "
            "critically and comparatively."
        ),
    ),
    dict(
        slug="unc-exercise-sport-science-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Exercise and Sport Science",
        department="Department of Exercise and Sport Science",
        cip="31.0505", va=7019, oos=43152, duration_months=48,
        keywords=["Exercise and Sport Science"],
        description=(
            "Studying human movement and physical performance, this field examines exercise "
            "physiology, biomechanics, motor behavior, and the social dimensions of sport, "
            "exploring how activity affects health and function across the lifespan."
        ),
        who_its_for=(
            "It fits students interested in fitness, sport, and human movement from a broad "
            "academic perspective."
        ),
    ),
    dict(
        slug="unc-geography-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Geography",
        department="Department of Geography",
        cip="45.0701", va=7019, oos=43152, duration_months=48,
        keywords=["Geography"],
        description=(
            "Bridging the physical and social sciences, this field studies places, "
            "environments, and spatial patterns, examining landscapes, climate, cities, "
            "migration, and the maps and tools used to analyze them."
        ),
        who_its_for=(
            "It suits students interested in how people and the environment interact across "
            "space and place."
        ),
    ),
    dict(
        slug="unc-geological-sciences-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Geological Sciences",
        department="Department of Earth, Marine, and Environmental Sciences",
        cip="40.0601", va=7019, oos=43152, duration_months=48,
        keywords=["Geological Sciences"],
        description=(
            "Investigating the Earth's structure, materials, and history, this field studies "
            "rocks, minerals, tectonics, and surface processes to understand how the planet "
            "formed, changes, and shapes natural resources and hazards."
        ),
        who_its_for=(
            "It fits students fascinated by the Earth, its deep history, and the processes "
            "that shape its surface."
        ),
    ),
    dict(
        slug="unc-global-studies-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Global Studies",
        department="Curriculum in Global Studies",
        cip="30.2001", va=7019, oos=43152, duration_months=48,
        keywords=["Global Studies"],
        description=(
            "Examining the interconnected world, this field studies transnational politics, "
            "economics, culture, and social movements, pairing foreign-language study with "
            "analysis of globalization, development, and cross-border challenges."
        ),
        who_its_for=(
            "It suits students drawn to international affairs who want regional and language "
            "depth alongside global perspective."
        ),
    ),
    dict(
        slug="unc-history-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in History",
        department="Department of History",
        cip="54.0101", va=7019, oos=43152, duration_months=48,
        keywords=["History"],
        description=(
            "Investigating the human past, this field interprets political, social, economic, "
            "and cultural change across eras and regions, weighing primary sources and "
            "competing arguments to explain how the present came to be."
        ),
        who_its_for=(
            "It fits students who want to understand the past through evidence, "
            "interpretation, and rigorous writing."
        ),
    ),
    dict(
        slug="unc-human-organizational-leadership-development-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Human and Organizational Leadership Development",
        department="Program in Human and Organizational Leadership Development",
        cip="52.0213", va=7019, oos=43152, duration_months=48,
        keywords=["Human and Organizational Leadership Development"],
        description=(
            "Drawing on the behavioral and social sciences, this field studies how "
            "individuals, teams, and organizations lead, collaborate, and change, examining "
            "motivation, group dynamics, and the practice of effective leadership."
        ),
        who_its_for=(
            "It suits students aiming to lead people and organizations who want grounding in "
            "human behavior and group dynamics."
        ),
    ),
    dict(
        slug="unc-latin-american-studies-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Latin American Studies",
        department="Institute for the Study of the Americas",
        cip="05.0107", va=7019, oos=43152, duration_months=48,
        keywords=["Latin American Studies"],
        description=(
            "Concentrating on the cultures, histories, and politics of Latin America, this "
            "field combines Spanish or Portuguese language study with interdisciplinary "
            "analysis of the region's societies, economies, and global connections."
        ),
        who_its_for=(
            "It fits students interested in Latin America who want strong language skills and "
            "regional expertise."
        ),
    ),
    dict(
        slug="unc-linguistics-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Linguistics",
        department="Department of Linguistics",
        cip="16.0102", va=7019, oos=43152, duration_months=48,
        keywords=["Linguistics"],
        description=(
            "Studying language as a human system, this field analyzes the sounds, structure, "
            "meaning, and social use of language, examining how languages are acquired, vary, "
            "and change over time."
        ),
        who_its_for=(
            "It suits students fascinated by how language works and how the mind produces and "
            "processes it."
        ),
    ),
    dict(
        slug="unc-management-society-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Management and Society",
        department="Curriculum in Management and Society",
        cip="52.0201", va=7019, oos=43152, duration_months=48,
        keywords=["Management and Society"],
        description=(
            "Connecting business with the social sciences, this field examines how "
            "organizations operate within their legal, ethical, and societal contexts, "
            "studying management, markets, and the responsibilities firms hold to "
            "communities."
        ),
        who_its_for=(
            "It fits students who want a business-minded education grounded in the social "
            "sciences and ethics."
        ),
    ),
    dict(
        slug="unc-mathematics-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Mathematics",
        department="Department of Mathematics",
        cip="27.0101", va=7019, oos=43152, duration_months=48,
        keywords=["Mathematics"],
        description=(
            "Exploring quantity, structure, and abstraction, this field develops reasoning "
            "across calculus, algebra, and analysis, emphasizing proof and problem-solving "
            "within a broad liberal-arts course of study."
        ),
        who_its_for=(
            "It suits students who enjoy mathematical reasoning and want flexibility to pair "
            "it with other disciplines."
        ),
    ),
    dict(
        slug="unc-media-journalism-ba", school=_HUSSMAN,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Media and Journalism",
        department="Hussman School of Journalism and Media",
        cip="09.0401", va=7019, oos=43152, duration_months=48,
        keywords=["Media and Journalism"],
        description=(
            "Examining how news and information move through society, this field develops "
            "reporting, writing, editing, and visual storytelling while analyzing media's "
            "role in democracy, ethics, and public understanding."
        ),
        who_its_for=(
            "It fits students who want to report, produce media, and understand journalism's "
            "place in public life."
        ),
    ),
    dict(
        slug="unc-medical-anthropology-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Medical Anthropology",
        department="Department of Anthropology",
        cip="45.0202", va=7019, oos=43152, duration_months=48,
        keywords=["Medical Anthropology"],
        description=(
            "Applying anthropological methods to health and illness, this field studies how "
            "culture, biology, and social conditions shape disease, healing, and care across "
            "communities and medical systems worldwide."
        ),
        who_its_for=(
            "It suits students interested in health and medicine who want a cultural and "
            "social lens on illness and care."
        ),
    ),
    dict(
        slug="unc-music-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Music",
        department="Department of Music",
        cip="50.0901", va=7019, oos=43152, duration_months=48,
        keywords=["Music"],
        description=(
            "Studying music as art and discipline, this field develops performance, theory, "
            "history, and composition, examining how musical works are structured, created, "
            "and understood across traditions and eras."
        ),
        who_its_for=(
            "It fits students who love music and want to study it broadly within a liberal- "
            "arts education."
        ),
    ),
    dict(
        slug="unc-peace-war-defense-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Peace, War, and Defense",
        department="Curriculum in Peace, War, and Defense",
        cip="30.0501", va=7019, oos=43152, duration_months=48,
        keywords=["Peace, War, and Defense"],
        description=(
            "Examining the causes and conduct of conflict, this field studies war, security, "
            "diplomacy, and peacemaking through history, political science, and ethics, "
            "analyzing how nations and peoples confront violence."
        ),
        who_its_for=(
            "It suits students interested in security, conflict, and the pursuit of peace "
            "across history and policy."
        ),
    ),
    dict(
        slug="unc-philosophy-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Philosophy",
        department="Department of Philosophy",
        cip="38.0101", va=7019, oos=43152, duration_months=48,
        keywords=["Philosophy"],
        description=(
            "Probing fundamental questions about knowledge, reality, ethics, and meaning, "
            "this field develops rigorous argument and analysis, examining the assumptions "
            "behind science, morality, language, and human existence."
        ),
        who_its_for=(
            "It fits students who love asking hard questions and want training in careful "
            "reasoning and argument."
        ),
    ),
    dict(
        slug="unc-physics-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Physics",
        department="Department of Physics and Astronomy",
        cip="40.0801", va=7019, oos=43152, duration_months=48,
        keywords=["Physics"],
        description=(
            "Seeking the principles that govern matter, energy, space, and time, this field "
            "studies mechanics, electromagnetism, and quantum theory, building physical "
            "intuition within a broad liberal-arts framework."
        ),
        who_its_for=(
            "It suits students curious about how the universe works who want physics "
            "alongside wide-ranging study."
        ),
    ),
    dict(
        slug="unc-political-science-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Political Science",
        department="Department of Political Science",
        cip="45.1001", va=7019, oos=43152, duration_months=48,
        keywords=["Political Science"],
        description=(
            "Analyzing power, governance, and political behavior, this field studies "
            "institutions, elections, public policy, and international relations, examining "
            "how decisions are made and how citizens and states shape outcomes."
        ),
        who_its_for=(
            "It fits students interested in government, politics, and the forces that shape "
            "public decisions."
        ),
    ),
    dict(
        slug="unc-psychology-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Psychology",
        department="Department of Psychology and Neuroscience",
        cip="42.0101", va=7019, oos=43152, duration_months=48,
        keywords=["Psychology"],
        description=(
            "Investigating mind and behavior, this field studies cognition, development, "
            "emotion, and social interaction, drawing on research to understand why people "
            "think, feel, and act as they do."
        ),
        who_its_for=(
            "It suits students curious about human behavior who want a broad introduction to "
            "the science of the mind."
        ),
    ),
    dict(
        slug="unc-public-policy-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Public Policy",
        department="Department of Public Policy",
        cip="44.0501", va=7019, oos=43152, duration_months=48,
        keywords=["Public Policy"],
        description=(
            "Examining how governments address public problems, this field studies policy "
            "design, analysis, and evaluation across areas like health, education, and the "
            "economy, weighing evidence, ethics, and political trade-offs."
        ),
        who_its_for=(
            "It fits students who want to analyze and improve the policies that shape "
            "society."
        ),
    ),
    dict(
        slug="unc-religious-studies-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Religious Studies",
        department="Department of Religious Studies",
        cip="38.0201", va=7019, oos=43152, duration_months=48,
        keywords=["Religious Studies"],
        description=(
            "Studying the world's religious traditions, this field examines beliefs, texts, "
            "rituals, and institutions across cultures and history, analyzing how religion "
            "shapes individuals, societies, and ideas of the sacred."
        ),
        who_its_for=(
            "It suits students curious about religion's role in human history, culture, and "
            "thought."
        ),
    ),
    dict(
        slug="unc-romance-languages-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Romance Languages",
        department="Department of Romance Studies",
        cip="16.0900", va=7019, oos=43152, duration_months=48,
        keywords=["Romance Languages"],
        description=(
            "Centering on the languages and literatures descended from Latin, this field "
            "develops fluency and cultural literacy in tongues such as Spanish, French, "
            "Italian, and Portuguese alongside their literary traditions."
        ),
        who_its_for=(
            "It fits students who want advanced command of Romance languages and the cultures "
            "they express."
        ),
    ),
    dict(
        slug="unc-sociology-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Sociology",
        department="Department of Sociology",
        cip="45.1101", va=7019, oos=43152, duration_months=48,
        keywords=["Sociology"],
        description=(
            "Studying social life and structure, this field examines how groups, "
            "institutions, and inequality shape behavior, using theory and research to "
            "analyze families, communities, organizations, and social change."
        ),
        who_its_for=(
            "It suits students interested in how society works and how social forces shape "
            "individual lives."
        ),
    ),
    dict(
        slug="unc-studio-art-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Studio Art",
        department="Department of Art and Art History",
        cip="50.0702", va=7019, oos=43152, duration_months=48,
        keywords=["Studio Art"],
        description=(
            "Developing artistic practice across media, this field cultivates skills in "
            "drawing, painting, sculpture, and other forms while exploring visual ideas "
            "within a broad liberal-arts education."
        ),
        who_its_for=(
            "It fits students who want to make art seriously while keeping a wide academic "
            "foundation."
        ),
    ),
    dict(
        slug="unc-womens-gender-studies-ba", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Women's and Gender Studies",
        department="Department of Women's and Gender Studies",
        cip="05.0207", va=7019, oos=43152, duration_months=48,
        keywords=["Women's and Gender Studies"],
        description=(
            "Examining gender and sexuality as forces in society, this field draws on "
            "history, literature, and the social sciences to analyze how power, identity, and "
            "inequality are shaped across cultures and time."
        ),
        who_its_for=(
            "It suits students who want to study gender, sexuality, and social justice across "
            "many disciplines."
        ),
    ),
    dict(
        slug="unc-applied-sciences-bs", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Science in Applied Sciences",
        department="Department of Applied Physical Sciences",
        cip="14.1201", va=7019, oos=43152, duration_months=48,
        keywords=["Applied Sciences"],
        description=(
            "Bridging physics, chemistry, and engineering, this field studies materials, "
            "energy, and devices, applying physical principles to design and understand "
            "technologies from nanostructures to functional systems."
        ),
        who_its_for=(
            "It fits students drawn to applied physical science who want to connect "
            "fundamental principles with real-world technology."
        ),
    ),
    dict(
        slug="unc-biology-bs", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Science in Biology",
        department="Department of Biology",
        cip="26.0101", va=7019, oos=43152, duration_months=48,
        keywords=["Biology"],
        description=(
            "Grounded in laboratory and quantitative inquiry, this field investigates living "
            "systems through molecular biology, genetics, cell biology, and physiology, "
            "emphasizing experimental methods and rigorous scientific training."
        ),
        who_its_for=(
            "It suits students pursuing research or health careers who want a lab-intensive, "
            "science-heavy biology curriculum."
        ),
    ),
    dict(
        slug="unc-chemistry-bs", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Science in Chemistry",
        department="Department of Chemistry",
        cip="40.0501", va=7019, oos=43152, duration_months=48,
        keywords=["Chemistry"],
        description=(
            "Emphasizing laboratory rigor and quantitative depth, this field studies chemical "
            "structure, reactivity, and analysis across organic, physical, and inorganic "
            "chemistry, preparing students for research and advanced scientific work."
        ),
        who_its_for=(
            "It fits students aiming for chemistry research or professional science who want "
            "intensive laboratory training."
        ),
    ),
    dict(
        slug="unc-computer-science-bs", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Science in Computer Science",
        department="Department of Computer Science",
        cip="11.0701", va=7019, oos=43152, duration_months=48,
        keywords=["Computer Science"],
        description=(
            "Centering on the technical foundations of computing, this field covers "
            "algorithms, systems, software engineering, and theory, with rigorous mathematics "
            "and hands-on building of complex programs and applications."
        ),
        who_its_for=(
            "It suits students pursuing software engineering or computing research who want "
            "deep technical and mathematical training."
        ),
    ),
    dict(
        slug="unc-data-science-bs", school=_SDSS,
        degree_type="bachelors",
        program_name="Bachelor of Science in Data Science",
        department="School of Data Science and Society",
        cip="30.7001", va=7019, oos=43152, duration_months=48,
        keywords=["Data Science"],
        description=(
            "Emphasizing the quantitative core of working with data, this field combines "
            "statistics, machine learning, programming, and computation to build, evaluate, "
            "and deploy models that extract insight from large datasets."
        ),
        who_its_for=(
            "It fits students who want rigorous technical training to build data and machine- "
            "learning systems."
        ),
    ),
    dict(
        slug="unc-earth-marine-sciences-bs", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Science in Earth and Marine Sciences",
        department="Department of Earth, Marine, and Environmental Sciences",
        cip="40.0607", va=7019, oos=43152, duration_months=48,
        keywords=["Earth and Marine Sciences"],
        description=(
            "Examining the Earth's land, oceans, and climate, this field studies geological "
            "and marine processes, from ocean circulation and coastal systems to the forces "
            "shaping the planet's surface and environment."
        ),
        who_its_for=(
            "It suits students fascinated by oceans, climate, and Earth systems who want a "
            "science-focused curriculum."
        ),
    ),
    dict(
        slug="unc-economics-bs", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Science in Economics",
        department="Department of Economics",
        cip="45.0603", va=7019, oos=43152, duration_months=48,
        keywords=["Economics"],
        description=(
            "Stressing mathematical and statistical rigor, this field models economic "
            "behavior with calculus, econometrics, and formal theory, training students to "
            "analyze markets and policy with quantitative precision."
        ),
        who_its_for=(
            "It fits students who want a quantitative, math-intensive approach to economics "
            "and data analysis."
        ),
    ),
    dict(
        slug="unc-environmental-science-bs", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Science in Environmental Science",
        department="Department of Earth, Marine, and Environmental Sciences",
        cip="03.0104", va=7019, oos=43152, duration_months=48,
        keywords=["Environmental Science"],
        description=(
            "Investigating the natural environment and human impact on it, this field "
            "integrates ecology, chemistry, and earth science to study ecosystems, pollution, "
            "climate, and the management of natural resources."
        ),
        who_its_for=(
            "It suits students committed to understanding and addressing environmental "
            "challenges through scientific study."
        ),
    ),
    dict(
        slug="unc-exercise-sport-science-bs", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Science in Exercise and Sport Science",
        department="Department of Exercise and Sport Science",
        cip="31.0505", va=7019, oos=43152, duration_months=48,
        keywords=["Exercise and Sport Science"],
        description=(
            "Applying laboratory and quantitative methods to human movement, this field "
            "studies exercise physiology, biomechanics, and motor control, emphasizing "
            "scientific measurement of how the body performs and adapts."
        ),
        who_its_for=(
            "It fits students headed for health professions or research who want a science- "
            "intensive study of movement."
        ),
    ),
    dict(
        slug="unc-geospatial-data-science-bs", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Science in Geospatial Data Science",
        department="Department of Geography",
        cip="45.0702", va=7019, oos=43152, duration_months=48,
        keywords=["Geospatial Data Science"],
        description=(
            "Combining geography with data science, this field studies spatial data, mapping, "
            "and geographic information systems, using computation to analyze patterns across "
            "landscapes, cities, and environments."
        ),
        who_its_for=(
            "It suits students who want to analyze the world spatially using data, maps, and "
            "geographic technology."
        ),
    ),
    dict(
        slug="unc-information-science-bs", school=_SILS,
        degree_type="bachelors",
        program_name="Bachelor of Science in Information Science",
        department="School of Information and Library Science",
        cip="11.0401", va=7019, oos=43152, duration_months=48,
        keywords=["Information Science"],
        description=(
            "Studying how information is organized, accessed, and used, this field examines "
            "data, systems, and human-information interaction, blending technology, design, "
            "and analysis to connect people with knowledge."
        ),
        who_its_for=(
            "It fits students interested in the technology and design of how information is "
            "managed and shared."
        ),
    ),
    dict(
        slug="unc-mathematics-bs", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Science in Mathematics",
        department="Department of Mathematics",
        cip="27.0101", va=7019, oos=43152, duration_months=48,
        keywords=["Mathematics"],
        description=(
            "Pursuing mathematics with technical depth, this field advances analysis, "
            "algebra, and applied methods, emphasizing rigorous proof and computation for "
            "careers in science, technology, and quantitative fields."
        ),
        who_its_for=(
            "It suits students who want intensive mathematical training for technical, "
            "scientific, or graduate work."
        ),
    ),
    dict(
        slug="unc-neuroscience-bs", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Science in Neuroscience",
        department="Department of Psychology and Neuroscience",
        cip="26.1501", va=7019, oos=43152, duration_months=48,
        keywords=["Neuroscience"],
        description=(
            "Investigating the nervous system, this field studies how neurons, circuits, and "
            "the brain produce perception, cognition, and behavior, integrating biology, "
            "chemistry, and laboratory research on the mind."
        ),
        who_its_for=(
            "It fits students fascinated by the brain who want a science-intensive, research- "
            "oriented path."
        ),
    ),
    dict(
        slug="unc-physics-bs", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Science in Physics",
        department="Department of Physics and Astronomy",
        cip="40.0801", va=7019, oos=43152, duration_months=48,
        keywords=["Physics"],
        description=(
            "Pursuing physics with technical rigor, this field investigates matter, energy, "
            "and forces through advanced mechanics, electromagnetism, and quantum theory, "
            "emphasizing mathematics, experiment, and research preparation."
        ),
        who_its_for=(
            "It suits students aiming for physics research or graduate study who want "
            "intensive quantitative training."
        ),
    ),
    dict(
        slug="unc-psychology-bs", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Science in Psychology",
        department="Department of Psychology and Neuroscience",
        cip="42.0101", va=7019, oos=43152, duration_months=48,
        keywords=["Psychology"],
        description=(
            "Approaching mind and behavior as an experimental science, this field emphasizes "
            "research design, statistics, and biological foundations, examining cognition, "
            "neuroscience, and behavior through rigorous empirical methods."
        ),
        who_its_for=(
            "It fits students who want a research-heavy, scientific path into psychology and "
            "the study of behavior."
        ),
    ),
    dict(
        slug="unc-statistics-analytics-bs", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Science in Statistics and Analytics",
        department="Department of Statistics and Operations Research",
        cip="27.0501", va=7019, oos=43152, duration_months=48,
        keywords=["Statistics and Analytics"],
        description=(
            "Centering on data, inference, and uncertainty, this field develops probability, "
            "statistical modeling, and analytical methods to draw reliable conclusions and "
            "inform decisions from real-world data."
        ),
        who_its_for=(
            "It suits students who want rigorous training in statistics and analytics for "
            "data-driven careers."
        ),
    ),
    dict(
        slug="unc-biomedical-engineering-bs", school=_MED,
        degree_type="bachelors",
        program_name="Bachelor of Science in Biomedical Engineering",
        department="Joint Department of Biomedical Engineering",
        cip="14.0501", va=7019, oos=43152, duration_months=48,
        keywords=["Biomedical Engineering"],
        description=(
            "Uniting engineering with medicine and biology, this field designs devices, "
            "imaging, and biomaterials to solve health problems, applying quantitative and "
            "laboratory methods to improve diagnosis and treatment."
        ),
        who_its_for=(
            "It fits students who want to engineer technologies that advance human health and "
            "medicine."
        ),
    ),
    dict(
        slug="unc-music-bmus", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Music",
        department="Department of Music",
        cip="50.0903", va=7019, oos=43152, duration_months=48,
        keywords=["Bachelor of Music"],
        description=(
            "Offering intensive professional training, this field develops advanced "
            "performance, musicianship, and theory through rigorous studio study, preparing "
            "musicians for conservatory-level mastery of their instrument or voice."
        ),
        who_its_for=(
            "It suits dedicated musicians who want immersive, performance-focused training "
            "toward a professional career."
        ),
    ),
    dict(
        slug="unc-studio-art-bfa", school=_COLLEGE,
        degree_type="bachelors",
        program_name="Bachelor of Fine Arts in Studio Art",
        department="Department of Art and Art History",
        cip="50.0702", va=7019, oos=43152, duration_months=48,
        keywords=["Studio Art"],
        description=(
            "Providing intensive studio training, this field immerses students in sustained "
            "artistic practice across media, developing a professional body of work and a "
            "mature creative voice through concentrated making and critique."
        ),
        who_its_for=(
            "It fits committed artists who want rigorous, professional-level studio training "
            "toward a career in art."
        ),
    ),
    dict(
        slug="unc-clinical-laboratory-science-bs", school=_MED,
        degree_type="bachelors",
        program_name="Bachelor of Science in Clinical Laboratory Science",
        department="Department of Health Sciences",
        cip="51.1005", va=7019, oos=43152, duration_months=48,
        keywords=["Clinical Laboratory Science"],
        description=(
            "Training students in the science behind diagnostic medicine, this field analyzes "
            "blood, tissue, and bodily fluids in the laboratory to detect disease, applying "
            "hematology, microbiology, and clinical chemistry to patient care."
        ),
        who_its_for=(
            "It suits students who want a laboratory-based health career detecting and "
            "diagnosing disease."
        ),
    ),
    dict(
        slug="unc-radiologic-science-bs", school=_MED,
        degree_type="bachelors",
        program_name="Bachelor of Science in Radiologic Science",
        department="Department of Health Sciences",
        cip="51.0911", va=7019, oos=43152, duration_months=48,
        keywords=["Radiologic Science"],
        description=(
            "Preparing students to perform medical imaging, this field studies anatomy, "
            "radiation physics, and patient care, training practitioners to produce "
            "diagnostic images that guide clinical decisions safely and accurately."
        ),
        who_its_for=(
            "It fits students who want a hands-on, patient-facing career in diagnostic "
            "medical imaging."
        ),
    ),
    dict(
        slug="unc-neurodiagnostics-sleep-science-bs", school=_MED,
        degree_type="bachelors",
        program_name="Bachelor of Science in Neurodiagnostics and Sleep Science",
        department="Department of Health Sciences",
        cip="51.0907", va=7019, oos=43152, duration_months=48,
        keywords=["Neurodiagnostics and Sleep Science"],
        description=(
            "Training students to record and interpret electrical activity of the brain and "
            "nervous system, this field combines neuroanatomy, physiology, and clinical "
            "practice to support the diagnosis of neurological and sleep disorders."
        ),
        who_its_for=(
            "It suits students drawn to a clinical, patient-facing career in brain and sleep "
            "diagnostics."
        ),
    ),
    dict(
        slug="unc-business-administration-bsba", school=_KENAN,
        degree_type="bachelors",
        program_name="Bachelor of Science in Business Administration",
        department="Kenan-Flagler Business School",
        cip="52.0201", va=7019, oos=43152, duration_months=48,
        keywords=["Business Administration"],
        tracks=["Accounting", "Finance", "Marketing", "Operations", "Management"],
        description=(
            "Business administration covers the core functions that run an organization \u2014 "
            "accounting, finance, marketing, operations, and management \u2014 paired with "
            "analytical and leadership skills for navigating real markets and decisions."
        ),
        who_its_for=(
            "Best for undergraduates aiming for careers in finance, consulting, marketing, or "
            "entrepreneurship who want a broad, analytical business foundation."
        ),
    ),
    dict(
        slug="unc-biostatistics-bsph", school=_GILLINGS,
        degree_type="bachelors",
        program_name="Bachelor of Science in Public Health in Biostatistics",
        department="Department of Biostatistics",
        cip="26.1102", va=7019, oos=43152, duration_months=48,
        keywords=["Biostatistics"],
        description=(
            "Biostatistics applies statistical theory and computing to biomedical and public "
            "health data, training students to design studies, analyze health datasets, and "
            "quantify uncertainty in questions about disease, treatment, and populations."
        ),
        who_its_for=(
            "Suited to quantitatively minded undergraduates who enjoy mathematics and coding "
            "and want to turn health data into evidence."
        ),
    ),
    dict(
        slug="unc-community-global-public-health-bsph", school=_GILLINGS,
        degree_type="bachelors",
        program_name="Bachelor of Science in Public Health in Community and Global Public Health",
        department="Department of Health Behavior",
        cip="51.2201", va=7019, oos=43152, duration_months=48,
        keywords=["Community and Global Public Health"],
        description=(
            "Community and global public health examines how social, behavioral, and "
            "structural forces shape health across local and international populations, "
            "building skills in program planning, health promotion, and addressing inequities "
            "through community-engaged practice."
        ),
        who_its_for=(
            "For undergraduates drawn to grassroots health work, health equity, and improving "
            "wellbeing across diverse communities at home and abroad."
        ),
    ),
    dict(
        slug="unc-environmental-health-sciences-bsph", school=_GILLINGS,
        degree_type="bachelors",
        program_name="Bachelor of Science in Public Health in Environmental Health Sciences",
        department="Department of Environmental Sciences and Engineering",
        cip="51.2202", va=7019, oos=43152, duration_months=48,
        keywords=["Environmental Health Sciences"],
        description=(
            "Environmental health sciences studies how air, water, soil, and chemical "
            "exposures affect human health, combining biology, toxicology, and exposure "
            "science to identify and reduce environmental hazards."
        ),
        who_its_for=(
            "Fits undergraduates interested in the science linking the environment, "
            "contaminants, and human disease."
        ),
    ),
    dict(
        slug="unc-health-policy-management-bsph", school=_GILLINGS,
        degree_type="bachelors",
        program_name="Bachelor of Science in Public Health in Health Policy and Management",
        department="Department of Health Policy and Management",
        cip="51.2211", va=7019, oos=43152, duration_months=48,
        keywords=["Health Policy and Management"],
        description=(
            "Health policy and management analyzes how health systems are financed, "
            "organized, and governed, equipping students to evaluate policy, manage health "
            "organizations, and improve the delivery and economics of care."
        ),
        who_its_for=(
            "For undergraduates curious about the business, economics, and politics behind "
            "how health care actually works."
        ),
    ),
    dict(
        slug="unc-nutrition-bsph", school=_GILLINGS,
        degree_type="bachelors",
        program_name="Bachelor of Science in Public Health in Nutrition",
        department="Department of Nutrition",
        cip="51.3101", va=7019, oos=43152, duration_months=48,
        keywords=["Nutrition"],
        description=(
            "Nutrition examines how diet, metabolism, and food environments influence health "
            "and disease across the lifespan, blending biochemistry and physiology with "
            "population-level approaches to nourishment and prevention."
        ),
        who_its_for=(
            "Best for science-minded undergraduates interested in food, metabolism, and "
            "preventing chronic disease through nutrition."
        ),
    ),
    dict(
        slug="unc-nursing-bsn", school=_NURSING,
        degree_type="bachelors",
        program_name="Bachelor of Science in Nursing",
        department="School of Nursing",
        cip="51.3801", va=7019, oos=43152, duration_months=48,
        keywords=["Nursing"],
        description=(
            "Nursing prepares students for professional registered-nurse practice, "
            "integrating anatomy, pharmacology, and clinical reasoning with supervised "
            "patient care to deliver safe, evidence-based treatment across hospital and "
            "community settings."
        ),
        who_its_for=(
            "For students committed to direct, hands-on patient care and licensure as a "
            "registered nurse."
        ),
    ),
    dict(
        slug="unc-dental-hygiene-bs", school=_DENT,
        degree_type="bachelors",
        program_name="Bachelor of Science in Dental Hygiene",
        department="Adams School of Dentistry",
        cip="51.0602", va=7019, oos=43152, duration_months=48,
        keywords=["Dental Hygiene"],
        description=(
            "Dental hygiene trains clinicians to assess oral health, perform preventive and "
            "periodontal care, take radiographs, and educate patients, combining biomedical "
            "science with supervised chairside practice."
        ),
        who_its_for=(
            "Suited to detail-oriented students drawn to preventive oral health care and "
            "direct patient interaction."
        ),
    ),
    dict(
        slug="unc-elementary-education-baed", school=_EDUC,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Education in Elementary Education",
        department="School of Education",
        cip="13.1202", va=7019, oos=43152, duration_months=48,
        keywords=["Elementary Education"],
        description=(
            "Elementary education prepares future teachers to instruct children across core "
            "subjects, blending child development, literacy and math pedagogy, and classroom "
            "management with supervised teaching in real schools."
        ),
        who_its_for=(
            "For students who want to teach young learners and earn initial licensure for the "
            "elementary grades."
        ),
    ),
    dict(
        slug="unc-human-development-family-science-baed", school=_EDUC,
        degree_type="bachelors",
        program_name="Bachelor of Arts in Education in Human Development and Family Science",
        department="School of Education",
        cip="19.0701", va=7019, oos=43152, duration_months=48,
        keywords=["Human Development and Family Science"],
        description=(
            "Human development and family science studies how people grow and relate across "
            "the lifespan, drawing on psychology, sociology, and policy to understand "
            "families, child development, and the systems that support them."
        ),
        who_its_for=(
            "Fits students interested in working with children, families, and communities "
            "through human services, counseling, or education."
        ),
    ),
    dict(
        slug="unc-mba", school=_KENAN,
        degree_type="masters",
        program_name="Master of Business Administration",
        department="Kenan-Flagler Business School",
        cip="52.0201", va=52186, oos=70908, duration_months=24,
        keywords=["Business Administration"],
        description=(
            "This management training develops leaders through advanced study of finance, "
            "strategy, marketing, and operations, sharpening decision-making, analytics, and "
            "team leadership for general management and senior business roles."
        ),
        who_its_for=(
            "For working professionals ready to accelerate into leadership, pivot industries, "
            "or move into general management."
        ),
    ),
    dict(
        slug="unc-master-of-accounting-mac", school=_KENAN,
        degree_type="masters",
        program_name="Master of Accounting",
        department="Kenan-Flagler Business School",
        cip="52.0301", va=69425, oos=69425, duration_months=15,
        keywords=["Accounting"],
        description=(
            "Advanced accounting study builds deep expertise in financial reporting, "
            "auditing, taxation, and analytics, preparing graduates for CPA licensure and "
            "professional careers in accounting and assurance."
        ),
        who_its_for=(
            "For students and career-changers aiming for CPA credentials and roles in public "
            "accounting, audit, or corporate finance."
        ),
    ),
    dict(
        slug="unc-juris-doctor-jd", school=_LAW,
        degree_type="professional",
        program_name="Juris Doctor",
        department="School of Law",
        cip="22.0101", va=28081, oos=51319, duration_months=36,
        keywords=["Juris Doctor"],
        description=(
            "Legal education develops rigorous analytical and advocacy skills across "
            "constitutional, contract, criminal, and civil law, combining doctrinal study "
            "with research, writing, and practical lawyering toward bar admission."
        ),
        who_its_for=(
            "For those preparing to practice law or apply legal reasoning in policy, "
            "business, or public service."
        ),
    ),
    dict(
        slug="unc-doctor-of-medicine-md", school=_MED,
        degree_type="professional",
        program_name="Doctor of Medicine",
        department="School of Medicine",
        cip="51.1201", va=32958, oos=61283, duration_months=48,
        keywords=["Medicine"],
        description=(
            "Medical education trains physicians through the basic sciences, clinical "
            "reasoning, and supervised rotations across specialties, building the diagnostic "
            "and patient-care skills required for residency and licensed practice."
        ),
        who_its_for=(
            "For students committed to becoming physicians and pursuing residency across the "
            "clinical specialties."
        ),
    ),
    dict(
        slug="unc-doctor-of-pharmacy-pharmd", school=_PHARM,
        degree_type="professional",
        program_name="Doctor of Pharmacy",
        department="Eshelman School of Pharmacy",
        cip="51.2001", va=25285, oos=48777, duration_months=48,
        keywords=["Pharmacy"],
        description=(
            "Pharmacy education prepares clinicians in pharmacology, therapeutics, and "
            "patient-centered medication management, combining pharmaceutical science with "
            "supervised practice to optimize drug therapy and safety."
        ),
        who_its_for=(
            "For students aiming to become licensed pharmacists in community, hospital, "
            "clinical, or industry settings."
        ),
    ),
    dict(
        slug="unc-doctor-of-dental-surgery-dds", school=_DENT,
        degree_type="professional",
        program_name="Doctor of Dental Surgery",
        department="Adams School of Dentistry",
        cip="51.0401", va=37821, oos=66267, duration_months=48,
        keywords=["Dental Surgery"],
        description=(
            "Dental education trains surgeons of the mouth in oral biology, restorative and "
            "surgical technique, and diagnosis, advancing from preclinical labs to supervised "
            "patient care toward licensure as a dentist."
        ),
        who_its_for=(
            "For students committed to clinical dentistry and licensure as a practicing "
            "dentist."
        ),
    ),
    dict(
        slug="unc-public-health-mph", school=_GILLINGS,
        degree_type="masters",
        program_name="Master of Public Health",
        department="Gillings School of Global Public Health",
        cip="51.2201", va=20630, oos=38530, duration_months=24,
        keywords=["Public Health"],
        description=(
            "Advanced public health study equips practitioners to prevent disease and promote "
            "health at the population scale, spanning epidemiology, biostatistics, policy, "
            "and program management across concentrations and applied fieldwork."
        ),
        who_its_for=(
            "For graduates and professionals pursuing leadership roles in public health "
            "practice, policy, or program management."
        ),
    ),
    dict(
        slug="unc-social-work-msw", school=_SSW,
        degree_type="masters",
        program_name="Master of Social Work",
        department="School of Social Work",
        cip="44.0701", va=14814, oos=33721, duration_months=24,
        keywords=["Social Work"],
        description=(
            "Social work education prepares practitioners to support individuals, families, "
            "and communities through clinical practice, case management, and advocacy, "
            "pairing theories of human behavior with supervised field placements toward "
            "licensure."
        ),
        who_its_for=(
            "For those seeking professional, often clinical, careers helping people navigate "
            "adversity and access services."
        ),
    ),
    dict(
        slug="unc-nursing-msn", school=_NURSING,
        degree_type="masters",
        program_name="Master of Science in Nursing",
        department="School of Nursing",
        cip="51.3801", va=18564, oos=37221, duration_months=24,
        keywords=["Nursing"],
        description=(
            "Advanced nursing study builds specialized clinical and leadership expertise "
            "beyond the bedside, preparing nurses for roles such as educator, administrator, "
            "or advanced practice through deeper science and applied practice."
        ),
        who_its_for=(
            "For registered nurses ready to specialize or move into advanced, leadership, or "
            "education roles."
        ),
    ),
    dict(
        slug="unc-nursing-dnp", school=_NURSING,
        degree_type="professional",
        program_name="Doctor of Nursing Practice",
        department="School of Nursing",
        cip="51.3818", va=18564, oos=37221, duration_months=36,
        keywords=["Nursing Practice"],
        description=(
            "This advanced-practice nursing training develops expert clinicians and system "
            "leaders, emphasizing evidence-based practice, quality improvement, and "
            "translating research into care at the highest level of nursing practice."
        ),
        who_its_for=(
            "For nurses pursuing the terminal practice degree to lead as advanced "
            "practitioners or health-system leaders."
        ),
    ),
    dict(
        slug="unc-library-science-msls", school=_SILS,
        degree_type="masters",
        program_name="Master of Science in Library Science",
        department="School of Information and Library Science",
        cip="25.0101", va=17514, oos=36171, duration_months=24,
        keywords=["Library Science"],
        description=(
            "Library science prepares information professionals to organize, preserve, and "
            "provide access to knowledge, covering cataloging, reference, collection "
            "development, and services across libraries, archives, and digital collections."
        ),
        who_its_for=(
            "For those pursuing professional careers as librarians or archivists in public, "
            "academic, or special collections."
        ),
    ),
    dict(
        slug="unc-information-science-msis", school=_SILS,
        degree_type="masters",
        program_name="Master of Science in Information Science",
        department="School of Information and Library Science",
        cip="11.0401", va=16704, oos=35361, duration_months=24,
        keywords=["Information Science"],
        description=(
            "Information science studies how people create, organize, find, and use "
            "information, blending data management, human-computer interaction, and systems "
            "design to connect users with the knowledge they need."
        ),
        who_its_for=(
            "For graduates aiming for careers in data curation, UX, information architecture, "
            "or knowledge management."
        ),
    ),
    dict(
        slug="unc-city-regional-planning-mcrp", school=_COLLEGE,
        degree_type="masters",
        program_name="Master of City and Regional Planning",
        department="Department of City and Regional Planning",
        cip="04.0301", va=13764, oos=32421, duration_months=24,
        keywords=["City and Regional Planning"],
        description=(
            "City and regional planning trains practitioners to shape land use, "
            "transportation, housing, and the environment, combining policy analysis, design, "
            "and community engagement to build more equitable and sustainable places."
        ),
        who_its_for=(
            "For those pursuing professional careers guiding how cities and regions grow and "
            "function."
        ),
    ),
    dict(
        slug="unc-public-policy-mpp", school=_COLLEGE,
        degree_type="masters",
        program_name="Master of Public Policy",
        department="Department of Public Policy",
        cip="44.0401", va=19264, oos=37921, duration_months=24,
        keywords=["Public Policy"],
        description=(
            "Public policy education develops analysts and leaders who evaluate and design "
            "government and nonprofit programs, integrating economics, statistics, and ethics "
            "to turn evidence into sound decisions."
        ),
        who_its_for=(
            "For graduates aiming to analyze, advise on, or lead policy in government, "
            "nonprofits, or research."
        ),
    ),
    dict(
        slug="unc-master-of-arts-teaching-mat", school=_EDUC,
        degree_type="masters",
        program_name="Master of Arts in Teaching",
        department="School of Education",
        cip="13.0101", va=11764, oos=30421, duration_months=12,
        keywords=["Teaching"],
        description=(
            "This teacher-preparation training readies subject-area graduates for the "
            "classroom, pairing pedagogy, curriculum design, and learning theory with "
            "supervised student teaching toward initial licensure."
        ),
        who_its_for=(
            "For college graduates and career-changers seeking a fast path to a teaching "
            "license."
        ),
    ),
    dict(
        slug="unc-computer-science-ms", school=_COLLEGE,
        degree_type="masters",
        program_name="Master of Science in Computer Science",
        department="Department of Computer Science",
        cip="11.0701", va=20764, oos=39421, duration_months=24,
        keywords=["Computer Science"],
        description=(
            "Advanced computer science study deepens expertise in algorithms, systems, and "
            "software, with opportunities to specialize in areas such as machine learning, "
            "graphics, networking, or security through coursework and research."
        ),
        who_its_for=(
            "For computing graduates and professionals seeking advanced technical depth or a "
            "path toward research."
        ),
    ),
    dict(
        slug="unc-media-communication-ma", school=_HUSSMAN,
        degree_type="masters",
        program_name="Master of Arts in Media and Communication",
        department="Hussman School of Journalism and Media",
        cip="09.0102", va=16573, oos=34403, duration_months=24,
        keywords=["Media and Communication"],
        description=(
            "Media and communication study examines how messages, technology, and audiences "
            "interact, combining communication theory with research methods to analyze "
            "journalism, digital media, and their effects on society."
        ),
        who_its_for=(
            "For students pursuing research, strategy, or scholarship at the intersection of "
            "media, communication, and society."
        ),
    ),
]

_REVIEWS_BY_SLUG: dict[str, dict] = {
    "unc-mba": {
        "summary": (
            "Coverage of the Kenan-Flagler MBA highlights a collaborative culture, strong "
            "general-management and consulting/finance placement, and well-regarded teaching, "
            "alongside flexible full-time, evening, and online formats; common cautions are a "
            "smaller recruiting footprint than the largest coastal programs and the trade-offs "
            "of the online and part-time options versus the residential experience."
        ),
        "themes": [
            {"label": "Collaborative culture", "sentiment": "positive",
             "detail": "Reviewers frequently describe a team-oriented, supportive cohort culture."},
            {"label": "Consulting & finance placement", "sentiment": "positive",
             "detail": ("Employment reports and rankings note solid outcomes in "
                        "consulting and finance.")},
            {"label": "Flexible formats", "sentiment": "mixed",
             "detail": ("Full-time, evening, weekend, and online options add flexibility but "
                        "differ in experience and network.")},
            {"label": "Scale & location", "sentiment": "caution",
             "detail": ("A mid-sized program in a college town has a narrower on-campus "
                        "recruiting footprint than the largest programs.")},
        ],
        "sources": [
            {"label": "Poets&Quants — UNC Kenan-Flagler Business School profile",
             "url": (
                 "https://poetsandquants.com/school/"
                 "university-of-north-carolina-kenan-flagler-business-school/"
             )},
            {"label": "U.S. News Best Business Schools — UNC (Kenan-Flagler)",
             "url": (
                 "https://www.usnews.com/best-graduate-schools/top-business-schools/"
                 "university-of-north-carolina-01800"
             )},
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party coverage and published "
            "outcomes reports; not individual verbatim quotes."
        ),
    },
    "unc-juris-doctor-jd": {
        "summary": (
            "The UNC School of Law draws consistent praise for a collegial, public-service-"
            "minded culture, strong in-state value, and broad placement into firms, clerkships, "
            "and government; common cautions are the competitiveness of national big-law and "
            "clerkship recruiting and out-of-state cost relative to the in-state advantage."
        ),
        "themes": [
            {"label": "Collegial, public-service culture", "sentiment": "positive",
             "detail": ("Students and reviewers describe a supportive environment with a "
                        "strong public-interest tradition.")},
            {"label": "Employment outcomes", "sentiment": "positive",
             "detail": ("Coverage notes solid placement into firms, clerkships, and "
                        "government, especially across the Southeast.")},
            {"label": "In-state value", "sentiment": "positive",
             "detail": ("The resident tuition rate makes it a strong value for North "
                        "Carolina students.")},
            {"label": "National recruiting", "sentiment": "caution",
             "detail": ("National big-law and clerkship recruiting is competitive, as at "
                        "peer programs.")},
        ],
        "sources": [
            {"label": "U.S. News Best Law Schools — University of North Carolina",
             "url": (
                 "https://www.usnews.com/best-graduate-schools/top-law-schools/"
                 "university-of-north-carolina-03103"
             )},
            {"label": "Above the Law — UNC School of Law profile",
             "url": (
                 "https://abovethelaw.com/law-schools/"
                 "university-of-north-carolina-school-of-law/"
             )},
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party coverage and published "
            "outcomes reports; not individual verbatim quotes."
        ),
    },
}

_TRACKS_BY_SLUG: dict[str, dict] = {}
for _row in _CATALOG:
    if _row.get("tracks"):
        _TRACKS_BY_SLUG[_row["slug"]] = {
            "tracks": list(_row["tracks"]),
            "source": f"{_row['department']} — official program page",
            "source_url": _SCHOOL_WEBSITE[_row["school"]],
        }

PROGRAMS: list[dict] = [
    {
        "slug": r["slug"], "school": r["school"], "program_name": r["program_name"],
        "degree_type": r["degree_type"], "department": r["department"],
        "duration_months": r["duration_months"],
        "delivery_format": r.get("delivery_format", "on_campus"),
        "keywords": list(r["keywords"]), "description": r["description"],
        "cip": r["cip"], "who_its_for": r["who_its_for"], "va": r["va"], "oos": r["oos"],
    }
    for r in _CATALOG
]
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

if len(set(PROGRAM_SLUGS)) != len(PROGRAM_SLUGS):
    _seen: set[str] = set()
    _dups = [s for s in PROGRAM_SLUGS if s in _seen or _seen.add(s)]
    raise RuntimeError(f"duplicate program slug(s): {sorted(set(_dups))}")
_name_keys = [(p["program_name"], p["degree_type"]) for p in PROGRAMS]
if len(set(_name_keys)) != len(_name_keys):
    raise RuntimeError("duplicate (program_name, degree_type) in UNC catalog")

_OUTCOMES_CONDITIONS = (
    "Institution-wide median earnings of federally aided students measured 10 years after "
    "entry (U.S. Dept. of Education College Scorecard); not a program-specific figure."
)
_OUTCOMES_INSTITUTION = {
    "median_salary": 72200,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry (institution-wide)",
    "conditions": _OUTCOMES_CONDITIONS,
    "source": "U.S. Dept. of Education College Scorecard (UNC, UNITID 199120)",
    "source_url": "https://collegescorecard.ed.gov/school/?199120",
}

_REQ_UNDERGRAD = {
    "materials": [
        "Common Application",
        "UNC writing supplement",
        "Secondary-school transcript",
        "Letters of recommendation",
        "Standardized test scores (test-optional policy; SAT or ACT if submitted)",
    ],
    "deadlines": {"early_action": "October 15", "regular_decision": "January 15"},
    "source": "https://admissions.unc.edu/apply/",
}
_REQ_GRAD_GENERIC = {
    "materials": [
        "Online application",
        "Transcripts from all prior institutions",
        "Letters of recommendation",
        "Statement of purpose",
        "Standardized / English-proficiency scores where required by the program",
    ],
    "deadlines": {"note": "Deadlines vary by program; see the program's official admissions page."},
    "source": "https://gradschool.unc.edu/admissions/",
}
_REQ_MBA = {
    "materials": [
        "Kenan-Flagler application + essays",
        "GMAT, GRE, or EA score (waivers considered)",
        "Undergraduate transcripts",
        "Recommendation",
        "Resume + interview",
    ],
    "deadlines": {"round_1": "Fall", "round_2": "January", "round_3": "Spring"},
    "source": "https://www.kenan-flagler.unc.edu/programs/full-time-mba/admissions/",
}
_REQ_LAW = {
    "materials": [
        "LSAC application + personal statement",
        "LSAT or GRE score",
        "Undergraduate transcripts (CAS report)",
        "Letters of recommendation",
        "Resume",
    ],
    "deadlines": {"regular_decision": "Rolling (see admissions site)"},
    "source": "https://law.unc.edu/admissions/",
}
_REQ_MED = {
    "materials": [
        "AMCAS application + UNC secondary",
        "MCAT score",
        "Undergraduate transcripts",
        "Letters of recommendation",
        "Interviews as required",
    ],
    "deadlines": {"primary": "AMCAS deadline (see admissions site)"},
    "source": "https://www.med.unc.edu/admit/",
}


def _requirements_for(spec: dict) -> dict:
    if spec["slug"] == "unc-juris-doctor-jd":
        return dict(_REQ_LAW)
    if spec["slug"] == "unc-doctor-of-medicine-md":
        return dict(_REQ_MED)
    if spec["slug"] == "unc-mba":
        return dict(_REQ_MBA)
    if spec["degree_type"] == "bachelors":
        return dict(_REQ_UNDERGRAD)
    return dict(_REQ_GRAD_GENERIC)


def _program_standard(spec: dict) -> dict:
    omitted: list[str] = ["outcomes_data.employment_rate", "outcomes_data.top_industries"]
    if not spec.get("tracks") and spec["slug"] not in _TRACKS_BY_SLUG:
        omitted.append("tracks")
    omitted.append("class_profile.cohort_size")
    omitted.append("faculty_contacts.lead")
    if spec["slug"] not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    return _standard(omitted)


def _lead_campus_photo(school_outcomes: dict) -> str | None:
    photos = (school_outcomes or {}).get("campus_photos") or []
    if photos and isinstance(photos[0], dict):
        return photos[0].get("url")
    return None


def _cost_data(spec: dict) -> dict:
    oos = spec["oos"]
    note = (
        "Published 2025-26 UNC tuition. UNC is a public university; the matcher reads the "
        "non-resident (out-of-state) rate, while the breakdown preserves both the NC-resident "
        "and non-resident rates."
    )
    if spec["slug"] == "unc-master-of-accounting-mac":
        note = (
            "Published 2025-26 UNC Master of Accounting tuition (a 15-month program total; the "
            "same figure applies to NC residents and non-residents)."
        )
    data = {
        "tuition_usd": oos,
        "breakdown": {"tuition_in_state": spec["va"], "tuition_out_of_state": oos},
        "funded": False,
        "note": note,
        "source": _COST_SRC[0],
        "source_url": _COST_SRC[1],
        "year": "2025-26",
    }
    if spec["degree_type"] == "bachelors":
        data["avg_net_price"] = _UG_NET_PRICE
    return data


def apply(session: Session) -> bool:
    """Enrich UNC-Chapel Hill to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when UNC is absent — safe on fresh/CI databases.
    """
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    photos = list(school_outcomes.get("campus_photos") or [])
    if all(p.get("url") != _EXTRA_CAMPUS_PHOTO["url"] for p in photos if isinstance(p, dict)):
        photos.append(dict(_EXTRA_CAMPUS_PHOTO))
    school_outcomes["campus_photos"] = photos
    school_outcomes["_standard"] = _standard(_OMITTED_INSTITUTION)
    inst.school_outcomes = school_outcomes
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    inst.founded_year = 1789
    inst.campus_setting = "suburban"
    if not inst.website_url:
        inst.website_url = "https://www.unc.edu"
    if not inst.social_links:
        inst.social_links = dict(_SOCIAL_UNC)
    lead_photo = _lead_campus_photo(school_outcomes)
    if lead_photo:
        gallery = [u for u in (inst.media_gallery or []) if u != lead_photo]
        inst.media_gallery = [lead_photo, *gallery]
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
    by_name: dict[str, School] = {}
    for spec in SCHOOLS:
        sc = existing.get(spec["name"])
        if sc is None:
            sc = School(institution_id=inst.id, name=spec["name"])
            session.add(sc)
        sc.description_text = spec["description"]
        sc.sort_order = spec["sort_order"]
        sc.catalog_source = "curated"
        sc.website_url = _SCHOOL_WEBSITE.get(spec["name"])
        about = _ABOUT_DETAIL.get(spec["name"])
        if about is not None:
            about = dict(about)
            about["_standard"] = _standard(_ABOUT_OMITTED.get(spec["name"], []))
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
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON tc.constraint_name = ccu.constraint_name
         AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND ccu.table_name = 'programs'
          AND ccu.column_name = 'id'
          AND tc.table_name <> 'programs'
        """)
    ).fetchall()
    for table, col in fks:
        hit = session.execute(
            text(f'SELECT 1 FROM "{table}" WHERE "{col}" = :pid LIMIT 1'),
            {"pid": program_id},
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
        p.department = spec["department"]
        p.duration_months = spec["duration_months"]
        p.description_text = spec["description"]
        p.website_url = _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec["delivery_format"]
        p.content_sources = _program_content(spec["school"], spec["keywords"])
        p.tuition = spec["oos"]
        p.cost_data = _cost_data(spec)
        p.cip_code = spec["cip"]
        p.application_requirements = _requirements_for(spec)
        outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(spec)
        p.outcomes_data = outcomes
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = None
        p.faculty_contacts = None
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        p.who_its_for = spec["who_its_for"]
        p.highlights = None
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
