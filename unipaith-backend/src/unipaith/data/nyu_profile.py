"""New York University — gold-standard profile data (institution + schools + program catalog).

Mirrors the MIT / Sloan / MBAn reference instance (see ``mit_profile.py`` /
``georgia_tech_profile.py``): every value is researched from an authoritative source and
carries a citation, or is honestly omitted (recorded in that node's ``_standard.omitted``) —
never guessed. Built 2026-06-13 from:

  • U.S. Dept. of Education **College Scorecard** API + **NCES College Navigator** (IPEDS,
    UNITID 193900) — net price, cost of attendance, earnings, completion/retention, Pell/loan,
    median debt, undergraduate race/ethnicity, admit rate, SAT/ACT percentiles.
  • NYU **Common Data Set 2024-25** (Office of Institutional Research) — first-year admissions
    funnel (110,807 applicants / 10,232 admits, Fall 2024) and the 8:1 student-faculty ratio.
  • NYU **2025 All-University Commencement program** + the official **Deans & Directors** page —
    each school's founding year and current dean.
  • The official **NYU Bulletin Program Finder** (bulletins.nyu.edu/programs) — the full published
    degree catalog (507 degree programs across 17 schools at the New York campus); each program's
    bulletin page is its website. Abu Dhabi and Shanghai (separate degree-granting portal campuses
    with their own IPEDS ids), minors, and stand-alone certificates are intentionally excluded.
  • Rankings: **QS 2026** (#55), **THE 2026** (=#31), **U.S. News Best Colleges 2026** (#32
    National), Carnegie (R1), Middle States (MSCHE) accreditation, each cited.
  • Verified third-party reviews + employment data for the flagship coverable programs (the
    NYU Stern Full-Time MBA and the NYU School of Law J.D.) and a sourced reputation review for
    the Tisch Film & Television BFA.

Honest caveats stamped into ``_standard.omitted``: NYU does not publish a single university-wide
"employed or continuing education" placement rate or a uniform program-level employment-outcomes
table the way a single-college school does, so the institution's combined placement rate and
top-employer-industries list are omitted with reason, and individual programs omit the
outcomes/class-profile/tuition deep fields unless a verified program-specific figure exists
(the College Scorecard institution-wide median earnings, $82,509 ten years after entry, is kept
at the institution level). Most graduate programs bill tuition per credit hour or per the school's
own schedule and publish no single annual figure, so those carry a sourced "see the program's
tuition page" record rather than a guessed number. External reviews are attached to the flagship
coverable programs with substantial third-party coverage; this is a genuinely large catalog
(507 programs, Columbia-scale), so the remaining programs record ``external_reviews`` (and their
deep fields) in their ``_standard.omitted`` pending a depth pass on a future repair-first run.
NYU's official news site (Adobe Experience Manager) is captcha-gated and exposes no verified
university RSS endpoint; ``content_sources`` uses the verified Washington Square News RSS
(``nyunews.com/feed/``, NYU's independent student newspaper since 1973) plus official social
handles + keywords on every node so the daily ingest can populate Updates.
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

INSTITUTION_NAME = "New York University"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-17"


def _standard(omitted: list[str] | None = None) -> dict:
    """The per-node provenance stamp the routine writes onto every enriched node."""
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }


# NYU reports outcomes by program/school, not as one university-wide combined placement rate or
# top-employer-industries list, so those two institution outcome fields are omitted with reason.
_OMITTED_INSTITUTION: list[str] = [
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
    "school_outcomes.scale.faculty_count",
]

# ── Institution-level data ────────────────────────────────────────────────
RANKING_DATA: dict = {
    "ownership_type": "private",
    "accreditor": "Middle States Commission on Higher Education (MSCHE)",
    # Carnegie 2025 basic classification (R1).
    "carnegie_classification": (
        "Doctoral Universities: Very High Research Spending and Doctorate Production (R1)"
    ),
    # QS World University Rankings 2026: NYU is #55 worldwide.
    "qs_world_university_rankings": {
        "rank": 55,
        "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/new-york-university-nyu",
    },
    # THE World University Rankings 2026: =#31 in the world.
    "times_higher_education": {
        "rank": 31,
        "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/new-york-university",
    },
    # U.S. News Best Colleges (National Universities) 2026: #32 nationally.
    "us_news_national": {
        "rank": 32,
        "year": 2026,
        "source_url": "https://www.collegekickstart.com/blog/item/u-s-news-world-report-posts-2026-college-rankings",
    },
}

# school_outcomes is shallow-merged into the existing JSONB. The College Scorecard seed already
# wrote some fields; the sub-objects below fill the verified gaps the conformance check flags.
SCHOOL_OUTCOMES: dict = {
    # College Scorecard (UNITID 193900): first-year retention 95.77%.
    "retention_rate_first_year": 0.9577,
    # College Scorecard completion rate at 150% of normal time (i.e. the six-year graduation
    # rate) = 87.57%.
    "graduation_rate_6yr": 0.8757,
    "completion_rate_4yr_150pct": 0.8757,
    # NYU Common Data Set 2024-25 (C1): 10,232 admits / 110,807 first-year applicants (Fall 2024).
    "admit_rate": 0.0923,
    # College Scorecard average annual net price + institution-wide median earnings 10 years
    # after entry (both cited to College Scorecard for UNITID 193900).
    "avg_net_price": 37050,
    "median_earnings_10yr": 82509,
    "financial_aid": {
        # College Scorecard (IPEDS): 17.88% of undergraduates received a Pell grant; 19.08% took
        # federal student loans.
        "pell_grant_rate": 0.1788,
        "federal_loan_rate": 0.1908,
        # College Scorecard academic-year cost of attendance.
        "cost_of_attendance": 84374,
        # College Scorecard median federal debt of completers.
        "median_debt_completers": 20500,
        "avg_net_price": 37050,
    },
    # Undergraduate race/ethnicity shares (College Scorecard / IPEDS, UNITID 193900).
    "demographics": {
        "white": 0.2196,
        "asian": 0.2224,
        "hispanic": 0.1437,
        "black": 0.0685,
        "two_or_more": 0.0432,
        "international": 0.2608,
        "american_indian": 0.0017,
        "native_hawaiian": 0.0007,
        "unknown": 0.0395,
    },
    # SAT/ACT 25th-75th percentiles of enrolled first-years (College Scorecard, UNITID 193900).
    "test_scores": {
        "sat_reading_25_75": [720, 760],
        "sat_math_25_75": [760, 800],
        "act_25_75": [34, 35],
    },
    "campus_basics": {"location": "New York, New York (Greenwich Village, Manhattan)"},
    # Scale: NYU CDS 2024-25 reports an 8:1 student-faculty ratio. NYU does not publish a single
    # clean university-wide instructional-faculty headcount across all schools, so faculty_count
    # is omitted (recorded in _OMITTED_INSTITUTION). Endowment ~$6.65B (FY2024, IPEDS via Data USA).
    "scale": {
        "student_faculty_ratio": "8:1",
        "endowment_usd": 6650000000,
    },
    # Washington Square (main campus), Greenwich Village, Manhattan.
    "location": {"lat": 40.7295, "lng": -73.9965},
    # Research: NYU's FY2024 R&D expenditures were $1.501B (NSF HERD survey, top-20 nationally),
    # organized across university-wide institutes and centers, each with its official link.
    "research": {
        "labs": [
            "Courant Institute of Mathematical Sciences",
            "Center for Data Science (CDS)",
            "Institute for the Study of the Ancient World (ISAW)",
            "Marron Institute of Urban Management",
            "Furman Center for Real Estate and Urban Policy",
            "Center for Neural Science",
        ],
        "areas": [
            "Mathematics, computing, and data science",
            "Neuroscience and cognition",
            "Urban science, policy, and real estate",
            "Ancient world, humanities, and the arts",
            "Public health and the life sciences",
            "Business, finance, and economics",
        ],
        "lab_links": {
            "Courant Institute of Mathematical Sciences": "https://cims.nyu.edu/",
            "Center for Data Science (CDS)": "https://cds.nyu.edu/",
            "Institute for the Study of the Ancient World (ISAW)": "https://isaw.nyu.edu/",
            "Marron Institute of Urban Management": "https://marroninstitute.nyu.edu/",
            "Furman Center for Real Estate and Urban Policy": "https://furmancenter.org/",
            "Center for Neural Science": "https://www.cns.nyu.edu/",
        },
    },
    "campus_life": {
        "athletics_division": "NCAA Division III (University Athletic Association)",
        "resources": [
            {"name": "NYU Athletics (the Violets)", "url": "https://gonyuathletics.com/"},
            {
                "name": "Wasserman Center for Career Development",
                "url": "https://www.nyu.edu/students/student-information-and-resources/career-development-and-jobs.html",
            },
            {
                "name": "NYU Libraries (Elmer Holmes Bobst Library)",
                "url": "https://library.nyu.edu/",
            },
            {"name": "NYU Student Affairs", "url": "https://www.nyu.edu/students.html"},
        ],
    },
    "media_credit": "Wikimedia Commons / Ajay Suresh (CC BY 2.0)",
    "campus_photos": [
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Bobst_Library_%2848072704803%29.jpg/1920px-Bobst_Library_%2848072704803%29.jpg",
            "credit": "Wikimedia Commons / Ajay Suresh (CC BY 2.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/NYC%2C_NYU_Stern_School_of_Business.jpg/1920px-NYC%2C_NYU_Stern_School_of_Business.jpg",
            "credit": "Wikimedia Commons / Jess Hawsor (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/NYU_%282011%29_03.JPG/1920px-NYU_%282011%29_03.JPG",
            "credit": "Wikimedia Commons / Nandaro (CC BY-SA 3.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/NYU_%2830415154541%29.jpg/1920px-NYU_%2830415154541%29.jpg",
            "credit": "Wikimedia Commons / Billie Grace Ward (CC BY 2.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/New_York_%286035597104%29.jpg/1920px-New_York_%286035597104%29.jpg",
            "credit": "Wikimedia Commons / popejon2 (CC BY 2.0)",
        },
    ],
    "flagship": {
        # Total degree-seeking enrollment, Fall 2024 (IPEDS via Data USA).
        "enrollment_total": 56832,
        # NYU Common Data Set 2024-25 (C1), first-time first-year, Fall 2024.
        "applicants": 110807,
        "admits": 10232,
        "admissions_cycle": "First-year, Fall 2024 (NYU Common Data Set 2024-25)",
        # Founded in 1831 by Albert Gallatin and a group of New Yorkers.
        "founded_year": 1831,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (New York University, UNITID 193900)",
            "url": "https://collegescorecard.ed.gov/school/?193900-New-York-University",
        },
        {
            "label": "NCES College Navigator — New York University (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=193900",
        },
        {
            "label": "NYU — Common Data Set 2024-25 (Office of Institutional Research)",
            "url": "https://www.nyu.edu/content/dam/nyu/institutionalResearch/documents/cds-on-website/CDS_2024-2025_Final%20for%20Release_wo%20PART%20H%20(check%20back%20for%20for%20PART%20H).pdf",
        },
        {
            "label": "NYU — 2025 All-University Commencement program (school founding years + deans)",
            "url": "https://www.nyu.edu/content/dam/nyu/univEvents/documents/CM25-accessible-program.pdf",
        },
        {
            "label": "NYU — Deans and Directors",
            "url": "https://www.nyu.edu/about/leadership-university-administration/deans-and-directors.html",
        },
        {
            "label": "NSF HERD Survey FY2024 — top-30 R&D expenditures (NYU $1.501B)",
            "url": "https://ncses.nsf.gov/pubs/nsf26305",
        },
        {
            "label": "Carnegie Classifications — New York University (R1)",
            "url": "https://carnegieclassifications.acenet.edu/institution/new-york-university/",
        },
        {
            "label": "QS World University Rankings 2026 — New York University (#55)",
            "url": "https://www.topuniversities.com/universities/new-york-university-nyu",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — NYU (=#31)",
            "url": "https://www.timeshighereducation.com/world-university-rankings/new-york-university",
        },
        {
            "label": "U.S. News Best Colleges 2026 — New York University (#32 National)",
            "url": "https://www.collegekickstart.com/blog/item/u-s-news-world-report-posts-2026-college-rankings",
        },
        {
            "label": "NYU Bulletin — Program Finder (full degree catalog)",
            "url": "https://bulletins.nyu.edu/programs/",
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it "Undergraduates"); the total
# degree-seeking enrollment (56,832) lives in flagship.enrollment_total.
UNDERGRAD_COUNT = 28663

DESCRIPTION = (
    "New York University is a private research university in New York, NY. Founded in 1831 by "
    "Albert Gallatin and a group of civic-minded New Yorkers, NYU is the largest private "
    "research university in the United States, anchored at Washington Square in Greenwich "
    "Village and woven throughout Manhattan, with degree-granting portal campuses in Abu Dhabi "
    "and Shanghai and a dozen global academic centers on six continents. It enrolls roughly "
    "29,000 undergraduates and more than 56,000 degree-seeking students in all, with an 8:1 "
    "student-faculty ratio, and admitted about 9% of first-year applicants for Fall 2024.\n\n"
    "NYU is organized into more than a dozen schools and colleges at its New York campus, "
    "including the College of Arts and Science, the Graduate School of Arts and Science (home "
    "to the Courant Institute of Mathematical Sciences), the Leonard N. Stern School of "
    "Business, the Tandon School of Engineering, the Steinhardt School of Culture, Education, "
    "and Human Development, the Tisch School of the Arts, the Robert F. Wagner Graduate School "
    "of Public Service, the School of Law, the Grossman School of Medicine, the College of "
    "Dentistry, the Rory Meyers College of Nursing, the School of Global Public Health, the "
    "Silver School of Social Work, the School of Professional Studies, the Gallatin School of "
    "Individualized Study, and Liberal Studies. Together they award some 500 degree programs "
    "across the bachelor's, master's, professional, and doctoral levels.\n\n"
    "A Carnegie R1 university accredited by the Middle States Commission on Higher Education, "
    "NYU ranks #32 among national universities by U.S. News, =#31 in the world by Times Higher "
    "Education, and #55 by QS for 2026, with world-leading departments in law, the arts and "
    "humanities, business, mathematics, and the social sciences. Its research enterprise drew "
    "$1.5 billion in R&D expenditures in fiscal year 2024, among the top 20 nationally.\n\n"
    "NYU enrolls more international students than any other U.S. university and sends more "
    "students to study abroad than any other. Its average net price is about $37,000 a year "
    "against a published cost of attendance near $84,000, and the median federal debt of "
    "completers is about $20,500; since 2021 NYU has met 100% of demonstrated need for "
    "incoming first-year undergraduates, and the NYU Promise makes tuition free for families "
    "earning under $100,000. NYU graduates earn a median of roughly $82,500 ten years after "
    "entry. The Violets compete in NCAA Division III (the University Athletic Association)."
)

# ── The schools (display order = founding year) ────────────────────────────
_CAS = "College of Arts and Science"
_LAW = "School of Law"
_MED = "Grossman School of Medicine"
_TANDON = "Tandon School of Engineering"
_DENTISTRY = "College of Dentistry"
_GSAS = "Graduate School of Arts and Science"
_STEINHARDT = "Steinhardt School of Culture, Education, and Human Development"
_STERN = "Leonard N. Stern School of Business"
_NURSING = "Rory Meyers College of Nursing"
_SPS = "School of Professional Studies"
_WAGNER = "Robert F. Wagner Graduate School of Public Service"
_SILVER = "Silver School of Social Work"
_TISCH = "Tisch School of the Arts"
_GALLATIN = "Gallatin School of Individualized Study"
_LS = "Liberal Studies"
_GPH = "School of Global Public Health"
_MEDLI = "Grossman Long Island School of Medicine"

SCHOOLS: list[dict] = [
    {
        "name": _CAS,
        "sort_order": 1,
        "description": (
            "The College of Arts and Science, founded in 1832, is NYU's primary undergraduate "
            "liberal-arts college at Washington Square. Its departments span the humanities, "
            "the natural and mathematical sciences, and the social sciences, and it awards the "
            "Bachelor of Arts and Bachelor of Science across dozens of majors, including "
            "joint-degree paths with the Tandon School of Engineering."
        ),
    },
    {
        "name": _LAW,
        "sort_order": 2,
        "description": (
            "NYU School of Law, founded in 1835, is one of the nation's leading law schools, "
            "consistently ranked in the top tier and No. 1 worldwide for tax and international "
            "law. It awards the Juris Doctor, a large slate of LL.M. master's degrees, the "
            "J.S.D., and specialized M.S. degrees, and is known for its Root-Tilden-Kern public "
            "interest scholarship and clinical programs."
        ),
    },
    {
        "name": _MED,
        "sort_order": 3,
        "description": (
            "NYU Grossman School of Medicine, founded in 1841 and part of NYU Langone Health, "
            "awards the M.D. and research master's degrees. In 2018 it became the first top-ranked "
            "U.S. medical school to offer full-tuition scholarships to all M.D. students, and it "
            "is a national leader in biomedical research and clinical care."
        ),
    },
    {
        "name": _TANDON,
        "sort_order": 4,
        "description": (
            "The NYU Tandon School of Engineering traces its roots to 1854 (the Brooklyn "
            "Polytechnic Institute), making it the nation's second-oldest private engineering "
            "school. Based in Downtown Brooklyn at MetroTech, Tandon awards bachelor's, master's, "
            "and doctoral degrees across engineering, computer science, applied sciences, and "
            "technology management, with strengths in cybersecurity, AI, and urban systems."
        ),
    },
    {
        "name": _DENTISTRY,
        "sort_order": 5,
        "description": (
            "The NYU College of Dentistry, founded in 1865, is the largest dental school in the "
            "United States and educates roughly one in ten U.S. dentists. It awards the Doctor of "
            "Dental Surgery (D.D.S.), advanced specialty programs, and research master's degrees "
            "in biomaterials science and clinical research."
        ),
    },
    {
        "name": _GSAS,
        "sort_order": 6,
        "description": (
            "The Graduate School of Arts and Science, founded in 1886, is NYU's principal graduate "
            "school in the arts, humanities, sciences, and social sciences, and is home to the "
            "Courant Institute of Mathematical Sciences and the Center for Data Science. It awards "
            "master's and doctoral degrees across more than fifty departments and programs."
        ),
    },
    {
        "name": _STEINHARDT,
        "sort_order": 7,
        "description": (
            "The Steinhardt School of Culture, Education, and Human Development, founded in 1890, "
            "spans education, applied psychology, communicative sciences and disorders, media and "
            "communication, the performing and visual arts, nutrition and public health, and the "
            "health professions. It awards bachelor's, master's, and doctoral degrees and prepares "
            "teachers, clinicians, artists, and researchers."
        ),
    },
    {
        "name": _STERN,
        "sort_order": 8,
        "description": (
            "The Leonard N. Stern School of Business, founded in 1900, is one of the nation's "
            "premier management schools. At Washington Square it offers the undergraduate BS in "
            "Business, a portfolio of full-time, part-time, executive, and specialized MBAs, a "
            "broad set of specialized MS degrees in finance, data, and analytics, and Ph.D. "
            "programs, enriched by its location in the financial capital of the world."
        ),
    },
    {
        "name": _NURSING,
        "sort_order": 9,
        "description": (
            "The Rory Meyers College of Nursing, founded in 1932, is a top-ranked nursing school "
            "that awards the Bachelor of Science in Nursing (traditional and accelerated), a range "
            "of master's and Doctor of Nursing Practice (D.N.P.) nurse-practitioner specialties, "
            "and a Ph.D. in nursing research and theory development."
        ),
    },
    {
        "name": _SPS,
        "sort_order": 10,
        "description": (
            "The School of Professional Studies, founded in 1934, delivers career-focused "
            "bachelor's and master's degrees in fields such as real estate, hospitality and "
            "tourism, sports management, marketing, public relations, global affairs, project "
            "management, human capital, and publishing, with a strong emphasis on industry "
            "practitioners and working professionals."
        ),
    },
    {
        "name": _WAGNER,
        "sort_order": 11,
        "description": (
            "The Robert F. Wagner Graduate School of Public Service, founded in 1938, is a "
            "top-ranked school of public policy and administration. It awards the Master of Public "
            "Administration (public and nonprofit management; health policy and management), the "
            "Master of Urban Planning, an MS in public policy, an Executive MPA, an online Master "
            "of Health Administration, and a Ph.D. in public administration."
        ),
    },
    {
        "name": _SILVER,
        "sort_order": 12,
        "description": (
            "The Silver School of Social Work, founded in 1960, is one of the oldest and largest "
            "schools of social work in the United States. It awards the BS, the Master of Social "
            "Work (M.S.W.), the Doctor of Social Work (D.S.W.) in clinical practice, and a Ph.D., "
            "with field placements across New York City and partner campuses."
        ),
    },
    {
        "name": _TISCH,
        "sort_order": 13,
        "description": (
            "The Tisch School of the Arts, founded in 1965, is among the world's foremost schools "
            "of the performing, cinematic, and emerging media arts. It awards BFA, BA, MFA, MA, "
            "and MPS degrees across film and television, drama, dance, dramatic writing, "
            "photography and imaging, game design, recorded music, interactive media, and the "
            "Interactive Telecommunications Program (ITP)."
        ),
    },
    {
        "name": _GALLATIN,
        "sort_order": 14,
        "description": (
            "The Gallatin School of Individualized Study, founded in 1972, lets students design "
            "their own interdisciplinary course of study across NYU's schools, anchored by a great-"
            "books curriculum and intensive advising. It awards an individualized BA and MA."
        ),
    },
    {
        "name": _LS,
        "sort_order": 15,
        "description": (
            "Liberal Studies, founded in 1972, is NYU's global, interdisciplinary liberal-arts "
            "core: students begin with a two-year sequence in the arts and sciences (often at a "
            "global site) and can complete the Bachelor of Arts in Global Liberal Studies, "
            "including a public-health track."
        ),
    },
    {
        "name": _GPH,
        "sort_order": 16,
        "description": (
            "The School of Global Public Health, founded in 2015, is a university-wide school that "
            "advances public health education and research worldwide. It awards the Master of "
            "Public Health, MS degrees in biostatistics and epidemiology, an MA in bioethics, and "
            "Ph.D. and Doctor of Public Health degrees."
        ),
    },
    {
        "name": _MEDLI,
        "sort_order": 17,
        "description": (
            "The NYU Grossman Long Island School of Medicine, founded in 2019 in Mineola, New "
            "York, is a three-year, tuition-free, primary-care-focused medical school that awards "
            "the Doctor of Medicine (M.D.) in partnership with NYU Langone Hospital—Long Island."
        ),
    },
]

_SCHOOL_WEBSITE: dict[str, str] = {
    _CAS: "https://cas.nyu.edu/",
    _LAW: "https://www.law.nyu.edu/",
    _MED: "https://med.nyu.edu/",
    _TANDON: "https://engineering.nyu.edu/",
    _DENTISTRY: "https://dental.nyu.edu/",
    _GSAS: "https://gsas.nyu.edu/",
    _STEINHARDT: "https://steinhardt.nyu.edu/",
    _STERN: "https://www.stern.nyu.edu/",
    _NURSING: "https://nursing.nyu.edu/",
    _SPS: "https://www.sps.nyu.edu/",
    _WAGNER: "https://wagner.nyu.edu/",
    _SILVER: "https://socialwork.nyu.edu/",
    _TISCH: "https://tisch.nyu.edu/",
    _GALLATIN: "https://gallatin.nyu.edu/",
    _LS: "https://liberalstudies.nyu.edu/",
    _GPH: "https://publichealth.nyu.edu/",
    _MEDLI: "https://med.nyu.edu/our-community/why-nyu-langone/grossman-long-island-school-medicine",
}

# Per-school about_detail (founded, leadership/dean, research_centers/departments, named_for,
# source). Founding years + current deans verified from the NYU 2025 Commencement program and
# the official Deans & Directors page. Notable named faculty are not enumerated at the school
# level (omitted in _ABOUT_OMITTED), never guessed.
_ABOUT_DETAIL: dict[str, dict] = {
    _CAS: {
        "founded": 1832,
        "leadership": "Wendy A. Suzuki — Kriser Dean of the College of Arts and Science",
        "research_centers": [
            "Humanities departments (English, History, Philosophy, Languages)",
            "Natural and mathematical sciences (Biology, Chemistry, Physics, Mathematics)",
            "Social sciences (Economics, Politics, Sociology, Anthropology)",
            "Center for Neural Science",
        ],
        "source": {
            "label": "NYU Arts & Science — Leadership",
            "url": "https://as.nyu.edu/about/leadership-of-arts-and-science.html",
        },
    },
    _LAW: {
        "founded": 1835,
        "leadership": "Troy A. McKenzie — Dean and Cecelia Goetz Professor of Law",
        "research_centers": [
            "Center on the Administration of Criminal Law",
            "Institute for International Law and Justice",
            "Engelberg Center on Innovation Law & Policy",
            "Furman Center for Real Estate and Urban Policy",
        ],
        "source": {
            "label": "NYU School of Law — Law School Leadership",
            "url": "https://www.law.nyu.edu/about/law-school-leadership",
        },
    },
    _MED: {
        "founded": 1841,
        "leadership": "Alec C. Kimmelman — Dean and CEO, NYU Grossman School of Medicine / NYU Langone Health",
        "research_centers": [
            "Perlmutter Cancer Center",
            "Neuroscience Institute",
            "Cardiovascular Research Center",
            "Institute for Systems Genetics",
        ],
        "source": {
            "label": "NYU Grossman School of Medicine — Deans",
            "url": "https://med.nyu.edu/our-community/about-us/deans",
        },
    },
    _TANDON: {
        "founded": 1854,
        "leadership": "Juan J. de Pablo — Executive Dean, Tandon School of Engineering",
        "research_centers": [
            "Center for Cybersecurity",
            "Center for Urban Science and Progress (CUSP)",
            "NYU WIRELESS",
            "Center for Advanced Technology in Telecommunications",
        ],
        "named_for": "Named in 2015 for Chandrika and Ranjan Tandon following their endowment gift",
        "source": {
            "label": "NYU Tandon — Juan de Pablo, Executive Dean",
            "url": "https://engineering.nyu.edu/faculty/juan-de-pablo",
        },
    },
    _DENTISTRY: {
        "founded": 1865,
        "leadership": "Charles N. Bertolami — Herman Robert Fox Dean, College of Dentistry",
        "research_centers": [
            "Department of Molecular Pathobiology",
            "Bluestone Center for Clinical Research",
            "Hansjörg Wyss Department of Plastic Surgery collaborations",
        ],
        "source": {
            "label": "NYU College of Dentistry — Dean Charles N. Bertolami",
            "url": "https://dental.nyu.edu/aboutus/leadership.html",
        },
    },
    _GSAS: {
        "founded": 1886,
        "leadership": "Lynne Kiorpes — Dean, Graduate School of Arts and Science",
        "research_centers": [
            "Courant Institute of Mathematical Sciences",
            "Center for Data Science",
            "Institute for the Study of the Ancient World",
            "Center for Neural Science",
        ],
        "source": {
            "label": "NYU Arts & Science — Leadership",
            "url": "https://as.nyu.edu/about/leadership-of-arts-and-science.html",
        },
    },
    _STEINHARDT: {
        "founded": 1890,
        "leadership": "Jack H. Knott — Dean, Steinhardt School of Culture, Education, and Human Development",
        "research_centers": [
            "Department of Applied Psychology",
            "Department of Media, Culture, and Communication",
            "Department of Communicative Sciences and Disorders",
            "Department of Music and Performing Arts Professions",
            "Department of Teaching and Learning",
        ],
        "named_for": "Named in 2001 for Michael H. Steinhardt following his endowment gift",
        "source": {
            "label": "NYU — Deans and Directors",
            "url": "https://www.nyu.edu/about/leadership-university-administration/deans-and-directors.html",
        },
    },
    _STERN: {
        "founded": 1900,
        "leadership": "Bharat N. Anand — Richard R. West Dean, Leonard N. Stern School of Business",
        "research_centers": [
            "Salomon Center for the Study of Financial Institutions",
            "Center for Sustainable Business",
            "Fubon Center for Technology, Business and Innovation",
            "Berkley Center for Entrepreneurship",
        ],
        "named_for": "Named in 1988 for Leonard N. Stern, a 1957 alumnus, following his endowment gift",
        "source": {
            "label": "NYU Stern — Dean Bharat N. Anand",
            "url": "https://www.stern.nyu.edu/faculty/bio/bharat-anand",
        },
    },
    _NURSING: {
        "founded": 1932,
        "leadership": "Angela Frederick Amar — Dean, Rory Meyers College of Nursing",
        "research_centers": [
            "Hartford Institute for Geriatric Nursing",
            "NYU Meyers Center for Nursing Research",
            "Florence S. Downs PhD Program in Nursing Research and Theory Development",
        ],
        "named_for": "Named in 2015 for the Meyers family (Rory Meyers) following their endowment gift",
        "source": {
            "label": "NYU — Deans and Directors",
            "url": "https://www.nyu.edu/about/leadership-university-administration/deans-and-directors.html",
        },
    },
    _SPS: {
        "founded": 1934,
        "leadership": "Angie D. Kamath — Dean, School of Professional Studies",
        "research_centers": [
            "Jonathan M. Tisch Center of Hospitality",
            "Schack Institute of Real Estate",
            "Preston Robert Tisch Institute for Global Sport",
            "Center for Global Affairs",
        ],
        "source": {
            "label": "NYU — Deans and Directors",
            "url": "https://www.nyu.edu/about/leadership-university-administration/deans-and-directors.html",
        },
    },
    _WAGNER: {
        "founded": 1938,
        "leadership": "Polly Trottenberg — Dean and Global Distinguished Professor",
        "research_centers": [
            "Wagner Health Policy and Management area",
            "Public and Nonprofit Management and Policy area",
            "Urban Planning area",
            "Rudin Center for Transportation Policy and Management",
        ],
        "named_for": "Named for Robert F. Wagner Jr., the three-term Mayor of New York City",
        "source": {
            "label": "NYU Wagner — Dean Polly Trottenberg",
            "url": "https://wagner.nyu.edu/community/faculty/polly-trottenberg",
        },
    },
    _SILVER: {
        "founded": 1960,
        "leadership": "Michael A. Lindsey — Dean, Silver School of Social Work",
        "research_centers": [
            "McSilver Institute for Poverty Policy and Research",
            "Constance and Martin Silver Center on Data Science and Social Equity",
            "Zelda Foster Studies Program in Palliative and End-of-Life Care",
        ],
        "named_for": "Named for Constance and Martin Silver following their endowment gift",
        "source": {
            "label": "NYU — Deans and Directors",
            "url": "https://www.nyu.edu/about/leadership-university-administration/deans-and-directors.html",
        },
    },
    _TISCH: {
        "founded": 1965,
        "leadership": "Rubén Polendo — Dean, Tisch School of the Arts",
        "research_centers": [
            "Maurice Kanbar Institute of Film & Television",
            "Department of Drama",
            "Interactive Telecommunications Program (ITP)",
            "Department of Photography & Imaging",
        ],
        "named_for": "Named for Laurence and Preston Robert Tisch following their endowment gift",
        "source": {
            "label": "NYU Tisch — Dean Rubén Polendo",
            "url": "https://tisch.nyu.edu/about/directory/general/108670593.html",
        },
    },
    _GALLATIN: {
        "founded": 1972,
        "leadership": "Victoria Rosner — Dean, Gallatin School of Individualized Study",
        "research_centers": [
            "Individualized interdisciplinary study (concentrations designed by students)",
            "Gallatin Arts Festival",
            "Great-books / interdisciplinary seminar curriculum",
        ],
        "named_for": "Named for Albert Gallatin, NYU's founder and U.S. Secretary of the Treasury",
        "source": {
            "label": "NYU — Deans and Directors",
            "url": "https://www.nyu.edu/about/leadership-university-administration/deans-and-directors.html",
        },
    },
    _LS: {
        "founded": 1972,
        "leadership": "Bruce Grant — Interim Dean of Liberal Studies",
        "research_centers": [
            "Global liberal-arts core curriculum",
            "Global Liberal Studies BA",
            "First-year global sites (study-away network)",
        ],
        "source": {
            "label": "NYU Arts & Science — Leadership",
            "url": "https://as.nyu.edu/about/leadership-of-arts-and-science.html",
        },
    },
    _GPH: {
        "founded": 2015,
        "leadership": "Melody Goodman — Dean, School of Global Public Health",
        "research_centers": [
            "Department of Epidemiology",
            "Department of Biostatistics",
            "Center for Anti-racism, Social Justice & Public Health",
            "Global Center for Implementation Science",
        ],
        "source": {
            "label": "NYU — Deans and Directors",
            "url": "https://www.nyu.edu/about/leadership-university-administration/deans-and-directors.html",
        },
    },
    _MEDLI: {
        "founded": 2019,
        "leadership": "Gladys M. Ayala — Dean, NYU Grossman Long Island School of Medicine",
        "research_centers": [
            "Three-year accelerated primary-care M.D. curriculum",
            "NYU Langone Hospital—Long Island clinical training",
        ],
        "source": {
            "label": "NYU — 2025 All-University Commencement program",
            "url": "https://www.nyu.edu/content/dam/nyu/univEvents/documents/CM25-accessible-program.pdf",
        },
    },
}

# Per-school honestly-omitted about_detail fields (verified-unavailable), for _standard.
# Every school records its founded year + dean + research centers; named distinguished faculty
# are not enumerated at the school level (would be cherry-picked), so about_detail.faculty is
# omitted everywhere, and about_detail.named_for is omitted where the school is not eponymous.
_ABOUT_OMITTED: dict[str, list[str]] = {
    _CAS: ["about_detail.named_for", "about_detail.faculty"],
    _LAW: ["about_detail.named_for", "about_detail.faculty"],
    _MED: ["about_detail.named_for", "about_detail.faculty"],
    _TANDON: ["about_detail.faculty"],
    _DENTISTRY: ["about_detail.named_for", "about_detail.faculty"],
    _GSAS: ["about_detail.named_for", "about_detail.faculty"],
    _STEINHARDT: ["about_detail.faculty"],
    _STERN: ["about_detail.faculty"],
    _NURSING: ["about_detail.faculty"],
    _SPS: ["about_detail.named_for", "about_detail.faculty"],
    _WAGNER: ["about_detail.faculty"],
    _SILVER: ["about_detail.faculty"],
    _TISCH: ["about_detail.faculty"],
    _GALLATIN: ["about_detail.faculty"],
    _LS: ["about_detail.named_for", "about_detail.faculty"],
    _GPH: ["about_detail.named_for", "about_detail.faculty"],
    _MEDLI: ["about_detail.named_for", "about_detail.faculty"],
}

# ── Feeds (content_sources) ────────────────────────────────────────────────
# NYU's official news site (AEM) is captcha-gated with no verified public RSS. Washington Square
# News (nyunews.com/feed/) is NYU's independent student newspaper (est. 1973) — verified
# 2026-06-17 to return live RSS items with media enclosures for cover images.
_NYU_NEWS_URL = "https://www.nyu.edu/about/news-publications/news.html"
_NYU_NEWS_RSS = "https://nyunews.com/feed/"

# Official university social handles (verified 2026-06-13).
_SOCIAL_NYU = {
    "instagram": "https://www.instagram.com/nyuniversity/",
    "linkedin": "https://www.linkedin.com/school/new-york-university/",
    "x": "https://twitter.com/nyuniversity",
    "youtube": "https://www.youtube.com/user/nyu",
    "facebook": "https://www.facebook.com/NYU",
}

# Per-school keywords that identify the school's items in the shared NYU news channel (the
# MIT/MBAn pattern); the school's own website is its news_url.
_SCHOOL_FEED_SPEC: dict[str, list[str]] = {
    _CAS: ["College of Arts and Science", "Arts and Science", "Washington Square"],
    _LAW: ["School of Law", "NYU Law"],
    _MED: ["Grossman School of Medicine", "NYU Langone", "medicine"],
    _TANDON: ["Tandon School of Engineering", "Tandon", "engineering"],
    _DENTISTRY: ["College of Dentistry", "dental"],
    _GSAS: ["Graduate School of Arts and Science", "Courant", "Center for Data Science"],
    _STEINHARDT: ["Steinhardt", "education", "media culture communication"],
    _STERN: ["Stern School of Business", "Stern", "MBA"],
    _NURSING: ["Meyers College of Nursing", "nursing"],
    _SPS: ["School of Professional Studies", "Schack", "Tisch Center of Hospitality"],
    _WAGNER: ["Wagner", "public service", "public policy"],
    _SILVER: ["Silver School of Social Work", "social work"],
    _TISCH: ["Tisch School of the Arts", "Tisch", "film", "drama"],
    _GALLATIN: ["Gallatin", "individualized study"],
    _LS: ["Liberal Studies", "Global Liberal Studies"],
    _GPH: ["School of Global Public Health", "public health"],
    _MEDLI: ["Grossman Long Island School of Medicine", "Long Island"],
}


def _school_content(name: str) -> dict:
    """Build a school's content_sources from the school site + NYU news channel + keywords."""
    return {
        "news_url": _SCHOOL_WEBSITE.get(name, _NYU_NEWS_URL),
        "news_rss": _NYU_NEWS_RSS,
        "news_curated": False,
        "keywords": list(_SCHOOL_FEED_SPEC[name]),
        "social": _SOCIAL_NYU,
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    """Build a program's content_sources from its school channel, refined by program keywords."""
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


# Institution-wide channel: verified WSN RSS + official NYU news page + social handles.
_INSTITUTION_CONTENT: dict = {
    "news_url": _NYU_NEWS_URL,
    "news_rss": _NYU_NEWS_RSS,
    "news_curated": True,
    "social": _SOCIAL_NYU,
}


# Slug field → human field-name override (for fields whose title-cased slug would be wrong or
# awkward). Applied to the slug base after stripping the trailing degree code.
_FIELD_OVERRIDE: dict[str, str] = {
    "media-culture-communication": "Media, Culture, and Communication",
    "social-cultural-analysis": "Social and Cultural Analysis",
    "hebrew-judaic-studies": "Hebrew and Judaic Studies",
    "history-art-archaeology": "History of Art and Archaeology",
    "latin-american-caribbean-studies": "Latin American and Caribbean Studies",
    "russian-slavic-studies": "Russian and Slavic Studies",
    "electrical-computer-engineering": "Electrical and Computer Engineering",
    "chemical-biomolecular-engineering": "Chemical and Biomolecular Engineering",
    "communicative-sciences-disorders": "Communicative Sciences and Disorders",
    "nutrition-food-studies": "Nutrition and Food Studies",
    "nutrition-dietetics": "Nutrition and Dietetics",
    "applied-statistics-social-science-research": "Applied Statistics for Social Science Research",
    "mechatronics-robotics": "Mechatronics and Robotics",
    "biochemistry": "Biochemistry",
    "computer-science": "Computer Science",
    "computer-data-science": "Computer and Data Science",
    "data-science": "Data Science",
    "data-science-mathematics": "Data Science and Mathematics",
    "international-relations": "International Relations",
    "east-asian-studies": "East Asian Studies",
    "near-eastern-studies": "Near Eastern Studies",
    "middle-eastern-islamic-studies": "Middle Eastern and Islamic Studies",
    "gender-sexuality-studies": "Gender and Sexuality Studies",
    "environmental-studies": "Environmental Studies",
    "environmental-health-science": "Environmental Health Science",
    "spanish-portuguese": "Spanish and Portuguese",
    "english-american-literature": "English and American Literature",
    "comparative-literature": "Comparative Literature",
    "cinema-studies": "Cinema Studies",
    "performance-studies": "Performance Studies",
    "creative-writing": "Creative Writing",
    "literary-reportage": "Literary Reportage",
    "scientific-computing": "Scientific Computing",
    "quantitative-economics": "Quantitative Economics",
    "biomedical-informatics": "Biomedical Informatics",
    "information-systems": "Information Systems",
    "atmosphere-ocean-science": "Atmosphere-Ocean Science",
    "cognition-perception": "Cognition and Perception",
    "neural-science": "Neural Science",
    "human-skeletal-biology": "Human Skeletal Biology",
    "industrial-organizational-psychology": "Industrial and Organizational Psychology",
    "biomolecular-science": "Biomolecular Science",
    "integrated-design-media": "Integrated Design and Media",
    "applied-quantum-science-technology": "Applied Quantum Science and Technology",
    "urban-infrastructure-systems": "Urban Infrastructure Systems",
    "transportation-systems": "Transportation Systems",
    "construction-management": "Construction Management",
    "management-technology": "Management of Technology",
    "human-centered-technology-innovation-design": "Human-Centered Technology, Innovation, and Design",
    "financial-engineering": "Financial Engineering",
    "business-technology-management": "Business and Technology Management",
    "business-analytics-ai": "Business Analytics and AI",
    "data-analytics-business-computing": "Data Analytics and Business Computing",
    "quantitative-finance": "Quantitative Finance",
    "global-finance": "Global Finance",
    "marketing-retail-science": "Marketing and Retail Science",
    "organization-management-strategy": "Management of Organizations and Strategy",
    "management-organizational-behavior": "Management and Organizational Behavior",
    "operations-management": "Operations Management",
    "public-relations-corporate-communication": "Public Relations and Corporate Communication",
    "human-capital-analytics-technology": "Human Capital Analytics and Technology",
    "human-capital-management": "Human Capital Management",
    "integrated-marketing": "Integrated Marketing",
    "management-analytics": "Management and Systems",
    "professional-writing": "Professional Writing",
    "project-management": "Project Management",
    "translation-interpreting": "Translation and Interpreting",
    "travel-tourism-management": "Travel and Tourism Management",
    "global-hospitality-management": "Global Hospitality Management",
    "hospitality-travel-tourism-management": "Hospitality, Travel, and Tourism Management",
    "global-security-conflict-cyber-crime": "Global Security, Conflict, and Cybercrime",
    "executive-coaching-organizational-consulting": "Executive Coaching and Organizational Consulting",
    "entrepreneurship-management": "Entrepreneurship and Management",
    "financial-planning": "Financial Planning",
    "global-affairs": "Global Affairs",
    "real-estate-development": "Real Estate Development",
    "real-estate-urban-sustainability": "Real Estate and Urban Sustainability",
    "applied-data-analytics-visualization": "Applied Data Analytics and Visualization",
    "digital-communications-media": "Digital Communications and Media",
    "healthcare-management": "Healthcare Management",
    "information-systems-technology": "Information Systems and Technology",
    "leadership-management": "Leadership and Management",
    "marketing-analytics": "Marketing Analytics",
    "sport-management": "Sport Management",
    "sports-business": "Sports Business",
    "global-sport": "Global Sport",
    "applied-psychology": "Applied Psychology",
    "art-education-community-practice": "Art Education and Community Practice",
    "counseling-mental-health-wellness": "Counseling for Mental Health and Wellness",
    "learning-technology-experience-design": "Learning, Technology, and Experience Design",
    "higher-education-student-affairs": "Higher Education and Student Affairs",
    "human-development-research-policy": "Human Development, Research, and Policy",
    "international-education": "International Education",
    "performing-arts-administration": "Performing Arts Administration",
    "visual-arts-administration": "Visual Arts Administration",
    "music-technology": "Music Technology",
    "music-theory-composition": "Music Theory and Composition",
    "music-business": "Music Business",
    "vocal-performance": "Vocal Performance",
    "instrumental-performance": "Instrumental Performance",
    "piano-performance": "Piano Performance",
    "music-performance": "Music Performance",
    "studio-art": "Studio Art",
    "costume-studies": "Costume Studies",
    "art-therapy": "Art Therapy",
    "drama-therapy": "Drama Therapy",
    "food-studies": "Food Studies",
    "games-learning": "Games for Learning",
    "advanced-occupational-therapy": "Advanced Occupational Therapy",
    "occupational-therapy": "Occupational Therapy",
    "physical-therapy-entry-level": "Physical Therapy (Entry-Level)",
    "educational-leadership-policy-studies": "Educational Leadership and Policy Studies",
    "educational-leadership-politics-advocacy": "Educational Leadership, Politics, and Advocacy",
    "higher-education-administration": "Higher Education Administration",
    "leadership-innovation": "Leadership and Innovation",
    "teaching-learning": "Teaching and Learning",
    "developmental-psychology": "Developmental Psychology",
    "social-psychology": "Social Psychology",
    "clinical-counseling-psychology": "Clinical and Counseling Psychology",
    "clinical-research": "Clinical Research",
    "clinical-investigation": "Clinical Investigation",
    "genome-health-analysis": "Genome and Health Analysis",
    "biomaterials-science": "Biomaterials Science",
    "biomedical-sciences": "Biomedical Sciences",
    "biomedical-engineering": "Biomedical Engineering",
    "clinical-research-nursing": "Clinical Research Nursing",
    "nursing-education": "Nursing Education",
    "nursing-informatics": "Nursing Informatics",
    "nursing-research-theory-development": "Nursing Research and Theory Development",
    "family-nurse-practitioner": "Family Nurse Practitioner",
    "nurse-midwifery": "Nurse-Midwifery",
    "adult-gerontology-acute-care-nurse-practitioner": "Adult-Gerontology Acute Care Nurse Practitioner",
    "adult-gerontology-primary-care-nurse-practitioner": "Adult-Gerontology Primary Care Nurse Practitioner",
    "pediatric-nurse-practitioner": "Pediatric Nurse Practitioner",
    "psychiatric-mental-health-nurse-practitioner": "Psychiatric-Mental Health Nurse Practitioner",
    "public-policy": "Public Policy",
    "public-administration": "Public Administration",
    "urban-planning": "Urban Planning",
    "health-policy-management": "Health Policy and Management",
    "public-nonprofit-management-policy": "Public and Nonprofit Management and Policy",
    "moving-image-archiving-preservation": "Moving Image Archiving and Preservation",
    "interactive-media-arts": "Interactive Media Arts",
    "interactive-telecommunications": "Interactive Telecommunications (ITP)",
    "virtual-production": "Virtual Production",
    "media-producing": "Media Producing",
    "arts-politics": "Arts and Politics",
    "dramatic-writing": "Dramatic Writing",
    "musical-theatre-writing": "Musical Theatre Writing",
    "design-stage-film": "Design for Stage and Film",
    "dance-interdisciplinary-research": "Dance and Interdisciplinary Research",
    "film-television": "Film and Television",
    "game-design": "Game Design",
    "photography-imaging": "Photography and Imaging",
    "recorded-music": "Recorded Music",
    "collaborative-arts": "Collaborative Arts",
    "individualized-major": "Individualized Study",
    "individualized-study": "Individualized Study",
    "global-liberal-studies": "Global Liberal Studies",
    "global-liberal-studies-public-health": "Global Liberal Studies (Public Health)",
    "bioethics": "Bioethics",
    "epidemiology": "Epidemiology",
    "biostatistics": "Biostatistics",
}

# Slug → (program_name, degree_type, department) for degrees whose name does not follow the
# regular "<Degree> in <Field>" pattern: the professional doctorates, the Stern MBAs, the
# combined/dual degrees, and a few disambiguated names.
_SPECIAL: dict[str, tuple[str, str, str]] = {
    "law-jd": ("Juris Doctor (J.D.)", "professional", "Law"),
    "juridical-science-jsd": ("Doctor of Juridical Science (J.S.D.)", "phd", "Law"),
    "medicine-md": ("Doctor of Medicine (M.D.)", "professional", "Medicine"),
    "dentistry-dds": ("Doctor of Dental Surgery (D.D.S.)", "professional", "Dentistry"),
    "biology-dentistry-ba-dds": (
        "Combined-Degree B.A./D.D.S. in Biology and Dentistry (7-year)",
        "professional",
        "Dentistry",
    ),
    "social-work-msw": ("Master of Social Work (M.S.W.)", "masters", "Social Work"),
    "clinical-social-work-dsw": (
        "Doctor of Social Work (D.S.W.) in Clinical Social Work",
        "phd",
        "Social Work",
    ),
    # Stern MBAs
    "general-management-mba": ("MBA (Full-Time, Two-Year)", "masters", "Business Administration"),
    "general-management-executives-mba": (
        "MBA for Executives (Executive MBA)",
        "masters",
        "Business Administration",
    ),
    "global-executive-mba": ("Global Executive MBA", "masters", "Business Administration"),
    "luxury-retail-mba": ("Fashion & Luxury MBA", "masters", "Business Administration"),
    "stern-nyu-abu-dhabi-mba": (
        "Executive MBA — NYU Stern / NYU Abu Dhabi",
        "masters",
        "Business Administration",
    ),
    "technology-entrepreneurship-mba": (
        "Andre Koo Technology and Entrepreneurship MBA",
        "masters",
        "Business Administration",
    ),
    # Disambiguated / specially-named master's
    "accounting-bs-ms": ("Combined B.S./M.S. in Accounting", "masters", "Accounting"),
    "computer-science-courant-ms": (
        "Master of Science in Computer Science (Courant)",
        "masters",
        "Computer Science",
    ),
    "computer-science-tandon-ms": (
        "Master of Science in Computer Science (Tandon)",
        "masters",
        "Computer Science",
    ),
    "computer-science-management-technology-bs-ms": (
        "Combined B.S./M.S. in Computer Science and Management of Technology",
        "masters",
        "Computer Science",
    ),
    "studio-art-integrated-design-media-bfa-ms": (
        "Combined B.F.A./M.S. in Studio Art and Integrated Design & Media",
        "masters",
        "Studio Art",
    ),
    "human-capital-management-human-capital-analytics-technology-ms-ms": (
        "Dual M.S. in Human Capital Management and Human Capital Analytics & Technology",
        "masters",
        "Human Capital",
    ),
    "conservation-historic-artistic-works-history-art-archaeology-ms-ma": (
        "Dual M.S./M.A. in Conservation of Historic and Artistic Works and History of Art and Archaeology",
        "masters",
        "Conservation / History of Art and Archaeology",
    ),
    "online-health-administration-mha": (
        "Master of Health Administration (Online)",
        "masters",
        "Health Administration",
    ),
    "executive-master-public-administration-empa": (
        "Executive Master of Public Administration",
        "masters",
        "Public Administration",
    ),
    "taxation-executive-program-llm": (
        "Master of Laws (LL.M.) in Taxation (Executive Program)",
        "masters",
        "Taxation",
    ),
    "taxation-msl": ("Master of Studies in Law (M.S.L.) in Taxation", "masters", "Taxation"),
    # Combined CAS/Tandon dual-degree B.S. programs (named explicitly so the "-bs-bs" slug reads well)
    "biology-chemical-biomolecular-engineering-bs-bs": (
        "Combined B.S. in Biology and Chemical & Biomolecular Engineering",
        "bachelors",
        "Biology / Engineering",
    ),
    "chemistry-chemical-biomolecular-engineering-bs-bs": (
        "Combined B.S. in Chemistry and Chemical & Biomolecular Engineering",
        "bachelors",
        "Chemistry / Engineering",
    ),
    "computer-science-electrical-engineering-bs-bs": (
        "Combined B.S. in Computer Science and Electrical Engineering",
        "bachelors",
        "Computer Science / Engineering",
    ),
    "computer-science-engineering-bs-bs": (
        "Combined B.S. in Computer Science and Engineering",
        "bachelors",
        "Computer Science / Engineering",
    ),
    "mathematics-civil-engineering-bs-bs": (
        "Combined B.S. in Mathematics and Civil Engineering",
        "bachelors",
        "Mathematics / Engineering",
    ),
    "mathematics-computer-engineering-bs-bs": (
        "Combined B.S. in Mathematics and Computer Engineering",
        "bachelors",
        "Mathematics / Engineering",
    ),
    "mathematics-electrical-engineering-bs-bs": (
        "Combined B.S. in Mathematics and Electrical Engineering",
        "bachelors",
        "Mathematics / Engineering",
    ),
    "mathematics-mechanical-engineering-bs-bs": (
        "Combined B.S. in Mathematics and Mechanical Engineering",
        "bachelors",
        "Mathematics / Engineering",
    ),
    "physics-civil-engineering-bs-bs": (
        "Combined B.S. in Physics and Civil Engineering",
        "bachelors",
        "Physics / Engineering",
    ),
    "physics-computer-engineering-bs-bs": (
        "Combined B.S. in Physics and Computer Engineering",
        "bachelors",
        "Physics / Engineering",
    ),
    "physics-electrical-engineering-bs-bs": (
        "Combined B.S. in Physics and Electrical Engineering",
        "bachelors",
        "Physics / Engineering",
    ),
    "physics-mechanical-engineering-bs-bs": (
        "Combined B.S. in Physics and Mechanical Engineering",
        "bachelors",
        "Physics / Engineering",
    ),
}

# Degree code → (name prefix, degree_type) for the regular "<Degree> in <Field>" derivation.
_CODE_PREFIX: dict[str, tuple[str, str]] = {
    "ba": ("Bachelor of Arts in", "bachelors"),
    "bs": ("Bachelor of Science in", "bachelors"),
    "bfa": ("Bachelor of Fine Arts in", "bachelors"),
    "bm": ("Bachelor of Music in", "bachelors"),
    "ms": ("Master of Science in", "masters"),
    "ma": ("Master of Arts in", "masters"),
    "mfa": ("Master of Fine Arts in", "masters"),
    "mm": ("Master of Music in", "masters"),
    "mat": ("Master of Arts in Teaching", "masters"),
    "mps": ("Master of Professional Studies in", "masters"),
    "mpa": ("Master of Public Administration in", "masters"),
    "mph": ("Master of Public Health in", "masters"),
    "mup": ("Master of Urban Planning in", "masters"),
    "msw": ("Master of Social Work in", "masters"),
    "mha": ("Master of Health Administration in", "masters"),
    "empa": ("Executive Master of Public Administration in", "masters"),
    "msl": ("Master of Studies in Law in", "masters"),
    "llm": ("Master of Laws (LL.M.) in", "masters"),
    "phd": ("Doctor of Philosophy in", "phd"),
    "dnp": ("Doctor of Nursing Practice —", "phd"),
    "edd": ("Doctor of Education in", "phd"),
    "otd": ("Doctor of Occupational Therapy —", "phd"),
    "dpt": ("Doctor of Physical Therapy —", "phd"),
    "dma": ("Doctor of Musical Arts in", "phd"),
    "dph": ("Doctor of Public Health in", "phd"),
    "jsd": ("Doctor of Juridical Science in", "phd"),
    "dsw": ("Doctor of Social Work in", "phd"),
    "dds": ("Doctor of Dental Surgery", "professional"),
    "md": ("Doctor of Medicine", "professional"),
    "jd": ("Juris Doctor", "professional"),
}

_DURATION_BY_CODE: dict[str, int] = {
    "ba": 48,
    "bs": 48,
    "bfa": 48,
    "bm": 48,
    "ms": 24,
    "ma": 24,
    "mfa": 24,
    "mm": 24,
    "mat": 18,
    "mps": 24,
    "mpa": 24,
    "mph": 24,
    "mup": 24,
    "msw": 24,
    "mha": 24,
    "empa": 24,
    "msl": 12,
    "llm": 12,
    "mba": 24,
    "phd": 60,
    "dnp": 36,
    "edd": 48,
    "otd": 36,
    "dpt": 36,
    "dma": 48,
    "dph": 48,
    "jsd": 60,
    "dsw": 36,
    "dds": 48,
    "md": 48,
    "jd": 36,
}

_DEGREE_ROLE = {
    "phd": "a research doctorate",
    "masters": "a master's program",
    "professional": "a professional degree program",
    "bachelors": "an undergraduate major",
}

# Disambiguate bulletin slugs that recur across two schools (unique program_name required).
_DISAMBIG_NAMES: dict[str, str] = {
    "nyu-cinema-studies-ba-tisch": "Bachelor of Arts in Cinema Studies — Tisch School of the Arts",
    "nyu-economics-phd-stern": "Doctor of Philosophy in Economics — Stern School of Business",
    "nyu-medicine-md-long-island": "Doctor of Medicine (M.D.) — Long Island School of Medicine",
}

_LEVEL_SUFFIX: dict[str, str] = {
    "bachelors": (
        " Undergraduates complete major requirements, electives, and often "
        "undergraduate research or internships in New York City."
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


_FIELD_KEY_BY_NAME: dict[str, str] = {
    "Juris Doctor (J.D.)": "Law (J.D.)",
    "Doctor of Medicine (M.D.)": "Medicine (M.D.)",
    "Doctor of Dental Surgery (D.D.S.)": "Dentistry (D.D.S.)",
    "Doctor of Medicine (M.D.) — Long Island School of Medicine": "Medicine (Long Island M.D.)",
    "MBA (Full-Time, Two-Year)": "Business Administration (MBA)",
}


def _field_key(program_name: str) -> str:
    if program_name in _FIELD_KEY_BY_NAME:
        return _FIELD_KEY_BY_NAME[program_name]
    for prefix in (
        "Bachelor of Arts in ",
        "Bachelor of Science in ",
        "Bachelor of Fine Arts in ",
        "Bachelor of Music in ",
        "Master of Science in ",
        "Master of Arts in ",
        "Master of Fine Arts in ",
        "Master of Music in ",
        "Master of Public Administration in ",
        "Master of Public Health in ",
        "Master of Urban Planning in ",
        "Master of Social Work in ",
        "Master of Professional Studies in ",
        "Master of Laws (LL.M.) in ",
        "Doctor of Philosophy in ",
        "Doctor of Education in ",
        "Doctor of Musical Arts in ",
        "Doctor of Social Work in ",
    ):
        if program_name.startswith(prefix):
            return program_name[len(prefix) :].strip()
    if program_name.endswith(" — Tisch School of the Arts"):
        return program_name.replace(" — Tisch School of the Arts", "").replace(
            "Bachelor of Arts in ", ""
        )
    if program_name.endswith(" — Stern School of Business"):
        return "Economics (Stern Ph.D.)"
    if program_name.endswith(" — Long Island School of Medicine"):
        return "Medicine (Long Island M.D.)"
    return program_name


def _lookup_field_clause(key: str) -> str:
    from unipaith.data.nyu_field_descriptions import FIELD_DESCRIPTIONS

    if key in FIELD_DESCRIPTIONS:
        return FIELD_DESCRIPTIONS[key]
    base = re.sub(r"\s*\(Online\)\s*", "", key).strip()
    if base in FIELD_DESCRIPTIONS:
        return FIELD_DESCRIPTIONS[base]
    raise ValueError(f"Missing FIELD_DESCRIPTIONS entry for {key!r}")


def _credential_suffix(code: str, degree_type: str) -> str:
    if code == "ba":
        return (
            " The Bachelor of Arts path emphasizes humanities-oriented seminars, "
            "writing-intensive coursework, and undergraduate research or internships."
        )
    if code == "bs":
        return (
            " The Bachelor of Science path emphasizes quantitative and laboratory "
            "coursework, methods training, and undergraduate research or internships."
        )
    if code == "bfa":
        return (
            " The B.F.A. path emphasizes studio production, critique, and portfolio "
            "development with industry mentorship."
        )
    if code == "bm":
        return (
            " The Bachelor of Music path emphasizes applied lessons, ensemble "
            "performance, and recital preparation."
        )
    if code == "ma":
        return (
            " The Master of Arts path emphasizes humanities-oriented graduate "
            "seminars, research papers, and a thesis or capstone project."
        )
    if code == "ms":
        return (
            " The Master of Science path emphasizes quantitative methods, "
            "laboratory or computational work, and a thesis or capstone project."
        )
    if code == "mfa":
        return (
            " The M.F.A. path emphasizes advanced studio work, critique, and a "
            "graduate portfolio or thesis exhibition."
        )
    if code == "phd":
        return (
            " The Ph.D. path prepares researchers for dissertation scholarship "
            "and academic or policy research careers."
        )
    return _LEVEL_SUFFIX.get(degree_type, "")


def _nyu_description(spec: dict) -> str:
    pname = spec["program_name"]
    key = _field_key(pname)
    clause = _lookup_field_clause(key)
    suffix = _credential_suffix(spec["code"], spec["degree_type"])
    delivery = ""
    if spec.get("delivery_format") == "online":
        delivery = " Delivered fully online through NYU School of Professional Studies."
    elif spec.get("delivery_format") == "hybrid":
        delivery = " Delivered in a hybrid or executive format."
    return f"{clause}{suffix}{delivery}"


# ── The program catalog ────────────────────────────────────────────────────
def _slug_field(base: str) -> str:
    if base in _FIELD_OVERRIDE:
        return _FIELD_OVERRIDE[base]
    return " ".join(w.capitalize() for w in base.split("-"))


def _derive(slug: str, code: str) -> tuple[str, str, str]:
    """Return (program_name, degree_type, department) for a catalog slug + degree code."""
    if slug in _SPECIAL:
        return _SPECIAL[slug]
    base = slug[: -(len(code) + 1)]
    field = _slug_field(base)
    prefix, dtype = _CODE_PREFIX[code]
    if code == "mat":
        return f"Master of Arts in Teaching — {field}", dtype, field
    if code in ("dnp", "otd", "dpt"):
        return f"{prefix} {field}", dtype, field
    return f"{prefix} {field}", dtype, field


# (bulletin_slug, school, degree_code, delivery_format, bulletin_path, db_suffix). Every entry is
# a published degree on the official NYU Bulletin Program Finder (bulletins.nyu.edu); the
# bulletin_path is the program's authoritative page. Abu Dhabi and Shanghai (separate IPEDS ids),
# minors, and stand-alone certificates are excluded. db_suffix disambiguates the three bulletin
# slugs that recur across two schools (economics-phd, medicine-md, cinema-studies-ba).

_CATALOG: list[tuple[str, str, str, str, str, str]] = [
    # ── CAS ──
    (
        "africana-studies-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/africana-studies-ba/",
        "",
    ),
    (
        "american-studies-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/american-studies-ba/",
        "",
    ),
    (
        "anthropology-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/anthropology-ba/",
        "",
    ),
    (
        "anthropology-classical-civilization-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/anthropology-classical-civilization-ba/",
        "",
    ),
    (
        "anthropology-linguistics-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/anthropology-linguistics-ba/",
        "",
    ),
    (
        "art-history-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/art-history-ba/",
        "",
    ),
    (
        "asian-pacific-american-studies-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/asian-pacific-american-studies-ba/",
        "",
    ),
    (
        "biochemistry-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/biochemistry-ba/",
        "",
    ),
    ("biology-ba", _CAS, "ba", "on_campus", "/undergraduate/arts-science/programs/biology-ba/", ""),
    (
        "chemistry-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/chemistry-ba/",
        "",
    ),
    (
        "cinema-studies-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/cinema-studies-ba/",
        "",
    ),
    (
        "classical-civilization-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/classical-civilization-ba/",
        "",
    ),
    (
        "classical-civilization-hellenic-studies-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/classical-civilization-hellenic-studies-ba/",
        "",
    ),
    (
        "classics-art-history-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/classics-art-history-ba/",
        "",
    ),
    (
        "classics-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/classics-ba/",
        "",
    ),
    (
        "comparative-literature-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/comparative-literature-ba/",
        "",
    ),
    (
        "computer-data-science-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/computer-data-science-ba/",
        "",
    ),
    (
        "computer-science-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/computer-science-ba/",
        "",
    ),
    (
        "data-science-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/data-science-ba/",
        "",
    ),
    (
        "data-science-mathematics-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/data-science-mathematics-ba/",
        "",
    ),
    (
        "dramatic-literature-theatre-history-cinema-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/dramatic-literature-theatre-history-cinema-ba/",
        "",
    ),
    (
        "east-asian-studies-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/east-asian-studies-ba/",
        "",
    ),
    (
        "economics-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/economics-ba/",
        "",
    ),
    (
        "economics-computer-science-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/economics-computer-science-ba/",
        "",
    ),
    (
        "economics-mathematics-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/economics-mathematics-ba/",
        "",
    ),
    (
        "english-american-literature-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/english-american-literature-ba/",
        "",
    ),
    (
        "environmental-studies-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/environmental-studies-ba/",
        "",
    ),
    (
        "european-mediterranean-studies-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/european-mediterranean-studies-ba/",
        "",
    ),
    ("french-ba", _CAS, "ba", "on_campus", "/undergraduate/arts-science/programs/french-ba/", ""),
    (
        "french-linguistics-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/french-linguistics-ba/",
        "",
    ),
    (
        "gender-sexuality-studies-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/gender-sexuality-studies-ba/",
        "",
    ),
    ("german-ba", _CAS, "ba", "on_campus", "/undergraduate/arts-science/programs/german-ba/", ""),
    (
        "german-linguistics-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/german-linguistics-ba/",
        "",
    ),
    (
        "global-public-health-anthropology-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/global-public-health-anthropology-ba/",
        "",
    ),
    (
        "global-public-health-history-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/global-public-health-history-ba/",
        "",
    ),
    (
        "global-public-health-sociology-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/global-public-health-sociology-ba/",
        "",
    ),
    (
        "hebrew-judaic-studies-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/hebrew-judaic-studies-ba/",
        "",
    ),
    (
        "hellenic-studies-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/hellenic-studies-ba/",
        "",
    ),
    ("history-ba", _CAS, "ba", "on_campus", "/undergraduate/arts-science/programs/history-ba/", ""),
    (
        "international-relations-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/international-relations-ba/",
        "",
    ),
    ("italian-ba", _CAS, "ba", "on_campus", "/undergraduate/arts-science/programs/italian-ba/", ""),
    (
        "italian-linguistics-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/italian-linguistics-ba/",
        "",
    ),
    (
        "journalism-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/journalism-ba/",
        "",
    ),
    (
        "language-mind-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/language-mind-ba/",
        "",
    ),
    (
        "latin-american-caribbean-studies-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/latin-american-caribbean-studies-ba/",
        "",
    ),
    (
        "latino-studies-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/latino-studies-ba/",
        "",
    ),
    (
        "linguistics-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/linguistics-ba/",
        "",
    ),
    (
        "mathematics-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/mathematics-ba/",
        "",
    ),
    (
        "mathematics-computer-science-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/mathematics-computer-science-ba/",
        "",
    ),
    (
        "medieval-renaissance-studies-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/medieval-renaissance-studies-ba/",
        "",
    ),
    (
        "middle-eastern-studies-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/middle-eastern-studies-ba/",
        "",
    ),
    ("music-ba", _CAS, "ba", "on_campus", "/undergraduate/arts-science/programs/music-ba/", ""),
    (
        "philosophy-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/philosophy-ba/",
        "",
    ),
    ("physics-ba", _CAS, "ba", "on_campus", "/undergraduate/arts-science/programs/physics-ba/", ""),
    (
        "politics-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/politics-ba/",
        "",
    ),
    (
        "psychology-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/psychology-ba/",
        "",
    ),
    (
        "public-policy-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/public-policy-ba/",
        "",
    ),
    (
        "religious-studies-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/religious-studies-ba/",
        "",
    ),
    (
        "romance-languages-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/romance-languages-ba/",
        "",
    ),
    (
        "russian-slavic-studies-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/russian-slavic-studies-ba/",
        "",
    ),
    (
        "social-cultural-analysis-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/social-cultural-analysis-ba/",
        "",
    ),
    (
        "sociology-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/sociology-ba/",
        "",
    ),
    (
        "spanish-linguistics-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/spanish-linguistics-ba/",
        "",
    ),
    (
        "spanish-portuguese-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/spanish-portuguese-ba/",
        "",
    ),
    (
        "urban-design-architecture-studies-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/urban-design-architecture-studies-ba/",
        "",
    ),
    (
        "urban-studies-anthropology-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/urban-studies-anthropology-ba/",
        "",
    ),
    (
        "urban-studies-history-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/urban-studies-history-ba/",
        "",
    ),
    (
        "urban-studies-social-cultural-analysis-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/urban-studies-social-cultural-analysis-ba/",
        "",
    ),
    (
        "urban-studies-sociology-ba",
        _CAS,
        "ba",
        "on_campus",
        "/undergraduate/arts-science/programs/urban-studies-sociology-ba/",
        "",
    ),
    (
        "biology-chemical-biomolecular-engineering-bs-bs",
        _CAS,
        "bs",
        "on_campus",
        "/undergraduate/arts-science/programs/biology-chemical-biomolecular-engineering-bs-bs/",
        "",
    ),
    (
        "chemistry-bs",
        _CAS,
        "bs",
        "on_campus",
        "/undergraduate/arts-science/programs/chemistry-bs/",
        "",
    ),
    (
        "chemistry-chemical-biomolecular-engineering-bs-bs",
        _CAS,
        "bs",
        "on_campus",
        "/undergraduate/arts-science/programs/chemistry-chemical-biomolecular-engineering-bs-bs/",
        "",
    ),
    (
        "computer-science-electrical-engineering-bs-bs",
        _CAS,
        "bs",
        "on_campus",
        "/undergraduate/arts-science/programs/computer-science-electrical-engineering-bs-bs/",
        "",
    ),
    (
        "computer-science-engineering-bs-bs",
        _CAS,
        "bs",
        "on_campus",
        "/undergraduate/arts-science/programs/computer-science-engineering-bs-bs/",
        "",
    ),
    (
        "global-public-health-science-bs",
        _CAS,
        "bs",
        "on_campus",
        "/undergraduate/arts-science/programs/global-public-health-science-bs/",
        "",
    ),
    (
        "mathematics-civil-engineering-bs-bs",
        _CAS,
        "bs",
        "on_campus",
        "/undergraduate/arts-science/programs/mathematics-civil-engineering-bs-bs/",
        "",
    ),
    (
        "mathematics-computer-engineering-bs-bs",
        _CAS,
        "bs",
        "on_campus",
        "/undergraduate/arts-science/programs/mathematics-computer-engineering-bs-bs/",
        "",
    ),
    (
        "mathematics-electrical-engineering-bs-bs",
        _CAS,
        "bs",
        "on_campus",
        "/undergraduate/arts-science/programs/mathematics-electrical-engineering-bs-bs/",
        "",
    ),
    (
        "mathematics-mechanical-engineering-bs-bs",
        _CAS,
        "bs",
        "on_campus",
        "/undergraduate/arts-science/programs/mathematics-mechanical-engineering-bs-bs/",
        "",
    ),
    (
        "neural-science-bs",
        _CAS,
        "bs",
        "on_campus",
        "/undergraduate/arts-science/programs/neural-science-bs/",
        "",
    ),
    ("physics-bs", _CAS, "bs", "on_campus", "/undergraduate/arts-science/programs/physics-bs/", ""),
    (
        "physics-civil-engineering-bs-bs",
        _CAS,
        "bs",
        "on_campus",
        "/undergraduate/arts-science/programs/physics-civil-engineering-bs-bs/",
        "",
    ),
    (
        "physics-computer-engineering-bs-bs",
        _CAS,
        "bs",
        "on_campus",
        "/undergraduate/arts-science/programs/physics-computer-engineering-bs-bs/",
        "",
    ),
    (
        "physics-electrical-engineering-bs-bs",
        _CAS,
        "bs",
        "on_campus",
        "/undergraduate/arts-science/programs/physics-electrical-engineering-bs-bs/",
        "",
    ),
    (
        "physics-mechanical-engineering-bs-bs",
        _CAS,
        "bs",
        "on_campus",
        "/undergraduate/arts-science/programs/physics-mechanical-engineering-bs-bs/",
        "",
    ),
    (
        "biology-dentistry-ba-dds",
        _CAS,
        "dds",
        "on_campus",
        "/undergraduate/arts-science/programs/biology-dentistry-ba-dds/",
        "",
    ),
    # ── DENTISTRY ──
    (
        "dentistry-dds",
        _DENTISTRY,
        "dds",
        "on_campus",
        "/graduate/dentistry/programs/dentistry-dds/",
        "",
    ),
    (
        "biomaterials-science-ms",
        _DENTISTRY,
        "ms",
        "on_campus",
        "/graduate/dentistry/programs/biomaterials-science-ms/",
        "",
    ),
    (
        "clinical-research-ms",
        _DENTISTRY,
        "ms",
        "on_campus",
        "/graduate/dentistry/programs/clinical-research-ms/",
        "",
    ),
    # ── GALLATIN ──
    (
        "individualized-major-ba",
        _GALLATIN,
        "ba",
        "on_campus",
        "/undergraduate/individualized-study/programs/individualized-major-ba/",
        "",
    ),
    (
        "individualized-study-ma",
        _GALLATIN,
        "ma",
        "on_campus",
        "/graduate/individualized-study/programs/individualized-study-ma/",
        "",
    ),
    # ── GPH ──
    (
        "public-health-dph",
        _GPH,
        "dph",
        "on_campus",
        "/graduate/global-public-health/programs/public-health-dph/",
        "",
    ),
    (
        "bioethics-ma",
        _GPH,
        "ma",
        "on_campus",
        "/graduate/global-public-health/programs/bioethics-ma/",
        "",
    ),
    (
        "public-health-mph",
        _GPH,
        "mph",
        "on_campus",
        "/graduate/global-public-health/programs/public-health-mph/",
        "",
    ),
    (
        "biostatistics-ms",
        _GPH,
        "ms",
        "on_campus",
        "/graduate/global-public-health/programs/biostatistics-ms/",
        "",
    ),
    (
        "epidemiology-ms",
        _GPH,
        "ms",
        "on_campus",
        "/graduate/global-public-health/programs/epidemiology-ms/",
        "",
    ),
    (
        "public-health-phd",
        _GPH,
        "phd",
        "on_campus",
        "/graduate/global-public-health/programs/public-health-phd/",
        "",
    ),
    # ── GSAS ──
    (
        "africana-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/africana-studies-ma/",
        "",
    ),
    (
        "american-journalism-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/american-journalism-ma/",
        "",
    ),
    (
        "animal-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/animal-studies-ma/",
        "",
    ),
    (
        "archives-public-history-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/archives-public-history-ma/",
        "",
    ),
    (
        "cinema-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/cinema-studies-ma/",
        "",
    ),
    ("classics-ma", _GSAS, "ma", "on_campus", "/graduate/arts-science/programs/classics-ma/", ""),
    (
        "comparative-literature-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/comparative-literature-ma/",
        "",
    ),
    (
        "conservation-historic-artistic-works-history-art-archaeology-ms-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/conservation-historic-artistic-works-history-art-archaeology-ms-ma/",
        "",
    ),
    (
        "east-asian-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/east-asian-studies-ma/",
        "",
    ),
    ("economics-ma", _GSAS, "ma", "on_campus", "/graduate/arts-science/programs/economics-ma/", ""),
    ("english-ma", _GSAS, "ma", "on_campus", "/graduate/arts-science/programs/english-ma/", ""),
    (
        "european-mediterranean-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/european-mediterranean-studies-ma/",
        "",
    ),
    (
        "french-literature-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/french-literature-ma/",
        "",
    ),
    (
        "french-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/french-studies-ma/",
        "",
    ),
    (
        "german-thought-literature-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/german-thought-literature-ma/",
        "",
    ),
    (
        "hebrew-judaic-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/hebrew-judaic-studies-ma/",
        "",
    ),
    (
        "historical-sustainable-architecture-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/historical-sustainable-architecture-ma/",
        "",
    ),
    (
        "history-art-archaeology-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/history-art-archaeology-ma/",
        "",
    ),
    ("history-ma", _GSAS, "ma", "on_campus", "/graduate/arts-science/programs/history-ma/", ""),
    (
        "industrial-organizational-psychology-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/industrial-organizational-psychology-ma/",
        "",
    ),
    (
        "interdisciplinary-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/interdisciplinary-studies-ma/",
        "",
    ),
    (
        "international-relations-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/international-relations-ma/",
        "",
    ),
    (
        "irish-american-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/irish-american-studies-ma/",
        "",
    ),
    (
        "italian-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/italian-studies-ma/",
        "",
    ),
    (
        "journalism-africana-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/journalism-africana-studies-ma/",
        "",
    ),
    (
        "journalism-east-asian-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/journalism-east-asian-studies-ma/",
        "",
    ),
    (
        "journalism-european-mediterranean-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/journalism-european-mediterranean-studies-ma/",
        "",
    ),
    (
        "journalism-french-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/journalism-french-studies-ma/",
        "",
    ),
    (
        "journalism-international-relations-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/journalism-international-relations-ma/",
        "",
    ),
    (
        "journalism-latin-american-caribbean-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/journalism-latin-american-caribbean-studies-ma/",
        "",
    ),
    (
        "journalism-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/journalism-ma/",
        "",
    ),
    (
        "journalism-near-eastern-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/journalism-near-eastern-studies-ma/",
        "",
    ),
    (
        "journalism-russian-slavic-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/journalism-russian-slavic-studies-ma/",
        "",
    ),
    (
        "latin-american-caribbean-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/latin-american-caribbean-studies-ma/",
        "",
    ),
    (
        "museum-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/museum-studies-ma/",
        "",
    ),
    (
        "near-eastern-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/near-eastern-studies-ma/",
        "",
    ),
    (
        "performance-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/performance-studies-ma/",
        "",
    ),
    ("politics-ma", _GSAS, "ma", "on_campus", "/graduate/arts-science/programs/politics-ma/", ""),
    (
        "psychology-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/psychology-ma/",
        "",
    ),
    (
        "religious-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/religious-studies-ma/",
        "",
    ),
    (
        "russian-slavic-studies-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/russian-slavic-studies-ma/",
        "",
    ),
    (
        "social-cultural-analysis-ma",
        _GSAS,
        "ma",
        "on_campus",
        "/graduate/arts-science/programs/social-cultural-analysis-ma/",
        "",
    ),
    (
        "creative-writing-mfa",
        _GSAS,
        "mfa",
        "on_campus",
        "/graduate/arts-science/programs/creative-writing-mfa/",
        "",
    ),
    (
        "creative-writing-spanish-mfa",
        _GSAS,
        "mfa",
        "on_campus",
        "/graduate/arts-science/programs/creative-writing-spanish-mfa/",
        "",
    ),
    (
        "literary-reportage-mfa",
        _GSAS,
        "mfa",
        "on_campus",
        "/graduate/arts-science/programs/literary-reportage-mfa/",
        "",
    ),
    ("biology-ms", _GSAS, "ms", "on_campus", "/graduate/arts-science/programs/biology-ms/", ""),
    (
        "biomedical-informatics-ms",
        _GSAS,
        "ms",
        "on_campus",
        "/graduate/arts-science/programs/biomedical-informatics-ms/",
        "",
    ),
    ("chemistry-ms", _GSAS, "ms", "on_campus", "/graduate/arts-science/programs/chemistry-ms/", ""),
    (
        "computer-science-courant-ms",
        _GSAS,
        "ms",
        "on_campus",
        "/graduate/arts-science/programs/computer-science-courant-ms/",
        "",
    ),
    (
        "computing-entrepreneurship-innovation-ms",
        _GSAS,
        "ms",
        "on_campus",
        "/graduate/arts-science/programs/computing-entrepreneurship-innovation-ms/",
        "",
    ),
    (
        "data-science-ms",
        _GSAS,
        "ms",
        "on_campus",
        "/graduate/arts-science/programs/data-science-ms/",
        "",
    ),
    (
        "environmental-health-science-ms",
        _GSAS,
        "ms",
        "on_campus",
        "/graduate/arts-science/programs/environmental-health-science-ms/",
        "",
    ),
    (
        "human-skeletal-biology-ms",
        _GSAS,
        "ms",
        "on_campus",
        "/graduate/arts-science/programs/human-skeletal-biology-ms/",
        "",
    ),
    (
        "information-systems-ms",
        _GSAS,
        "ms",
        "on_campus",
        "/graduate/arts-science/programs/information-systems-ms/",
        "",
    ),
    (
        "mathematics-finance-ms",
        _GSAS,
        "ms",
        "on_campus",
        "/graduate/arts-science/programs/mathematics-finance-ms/",
        "",
    ),
    (
        "mathematics-ms",
        _GSAS,
        "ms",
        "on_campus",
        "/graduate/arts-science/programs/mathematics-ms/",
        "",
    ),
    ("physics-ms", _GSAS, "ms", "on_campus", "/graduate/arts-science/programs/physics-ms/", ""),
    (
        "quantitative-economics-ms",
        _GSAS,
        "ms",
        "on_campus",
        "/graduate/arts-science/programs/quantitative-economics-ms/",
        "",
    ),
    (
        "scientific-computing-ms",
        _GSAS,
        "ms",
        "on_campus",
        "/graduate/arts-science/programs/scientific-computing-ms/",
        "",
    ),
    (
        "american-studies-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/american-studies-phd/",
        "",
    ),
    (
        "ancient-world-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/ancient-world-phd/",
        "",
    ),
    (
        "anthropology-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/anthropology-phd/",
        "",
    ),
    (
        "atmosphere-ocean-science-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/atmosphere-ocean-science-phd/",
        "",
    ),
    ("biology-phd", _GSAS, "phd", "on_campus", "/graduate/arts-science/programs/biology-phd/", ""),
    (
        "biomedical-sciences-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/biomedical-sciences-phd/",
        "",
    ),
    (
        "chemistry-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/chemistry-phd/",
        "",
    ),
    (
        "cinema-studies-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/cinema-studies-phd/",
        "",
    ),
    (
        "classics-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/classics-phd/",
        "",
    ),
    (
        "cognition-perception-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/cognition-perception-phd/",
        "",
    ),
    (
        "comparative-literature-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/comparative-literature-phd/",
        "",
    ),
    (
        "computer-science-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/computer-science-phd/",
        "",
    ),
    (
        "data-science-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/data-science-phd/",
        "",
    ),
    (
        "east-asian-studies-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/east-asian-studies-phd/",
        "",
    ),
    (
        "economics-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/economics-phd/",
        "",
    ),
    ("english-phd", _GSAS, "phd", "on_campus", "/graduate/arts-science/programs/english-phd/", ""),
    (
        "environmental-health-science-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/environmental-health-science-phd/",
        "",
    ),
    (
        "environmental-studies-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/environmental-studies-phd/",
        "",
    ),
    ("french-phd", _GSAS, "phd", "on_campus", "/graduate/arts-science/programs/french-phd/", ""),
    (
        "french-studies-anthropology-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/french-studies-anthropology-phd/",
        "",
    ),
    (
        "french-studies-french-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/french-studies-french-phd/",
        "",
    ),
    (
        "french-studies-history-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/french-studies-history-phd/",
        "",
    ),
    ("german-phd", _GSAS, "phd", "on_campus", "/graduate/arts-science/programs/german-phd/", ""),
    (
        "hebrew-judaic-studies-history-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/hebrew-judaic-studies-history-phd/",
        "",
    ),
    (
        "hebrew-judaic-studies-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/hebrew-judaic-studies-phd/",
        "",
    ),
    (
        "history-art-archaeology-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/history-art-archaeology-phd/",
        "",
    ),
    (
        "history-middle-eastern-studies-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/history-middle-eastern-studies-phd/",
        "",
    ),
    ("history-phd", _GSAS, "phd", "on_campus", "/graduate/arts-science/programs/history-phd/", ""),
    (
        "italian-studies-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/italian-studies-phd/",
        "",
    ),
    (
        "linguistics-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/linguistics-phd/",
        "",
    ),
    (
        "mathematics-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/mathematics-phd/",
        "",
    ),
    (
        "middle-eastern-islamic-studies-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/middle-eastern-islamic-studies-phd/",
        "",
    ),
    ("music-phd", _GSAS, "phd", "on_campus", "/graduate/arts-science/programs/music-phd/", ""),
    (
        "neural-science-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/neural-science-phd/",
        "",
    ),
    (
        "performance-studies-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/performance-studies-phd/",
        "",
    ),
    (
        "philosophy-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/philosophy-phd/",
        "",
    ),
    ("physics-phd", _GSAS, "phd", "on_campus", "/graduate/arts-science/programs/physics-phd/", ""),
    (
        "politics-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/politics-phd/",
        "",
    ),
    (
        "social-psychology-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/social-psychology-phd/",
        "",
    ),
    (
        "sociology-phd",
        _GSAS,
        "phd",
        "on_campus",
        "/graduate/arts-science/programs/sociology-phd/",
        "",
    ),
    ("spanish-phd", _GSAS, "phd", "on_campus", "/graduate/arts-science/programs/spanish-phd/", ""),
    # ── LAW ──
    ("law-jd", _LAW, "jd", "on_campus", "/graduate/law/programs/law-jd/", ""),
    (
        "juridical-science-jsd",
        _LAW,
        "jsd",
        "on_campus",
        "/graduate/law/programs/juridical-science-jsd/",
        "",
    ),
    (
        "competition-innovation-information-law-llm",
        _LAW,
        "llm",
        "on_campus",
        "/graduate/law/programs/competition-innovation-information-law-llm/",
        "",
    ),
    (
        "corporate-law-llm",
        _LAW,
        "llm",
        "on_campus",
        "/graduate/law/programs/corporate-law-llm/",
        "",
    ),
    (
        "environmental-energy-law-llm",
        _LAW,
        "llm",
        "on_campus",
        "/graduate/law/programs/environmental-energy-law-llm/",
        "",
    ),
    (
        "international-business-regulation-litigation-arbitration-llm",
        _LAW,
        "llm",
        "on_campus",
        "/graduate/law/programs/international-business-regulation-litigation-arbitration-llm/",
        "",
    ),
    (
        "international-legal-studies-llm",
        _LAW,
        "llm",
        "on_campus",
        "/graduate/law/programs/international-legal-studies-llm/",
        "",
    ),
    (
        "international-taxation-llm",
        _LAW,
        "llm",
        "on_campus",
        "/graduate/law/programs/international-taxation-llm/",
        "",
    ),
    ("law-llm", _LAW, "llm", "on_campus", "/graduate/law/programs/law-llm/", ""),
    ("legal-theory-llm", _LAW, "llm", "on_campus", "/graduate/law/programs/legal-theory-llm/", ""),
    (
        "taxation-executive-program-llm",
        _LAW,
        "llm",
        "on_campus",
        "/graduate/law/programs/taxation-executive-program-llm/",
        "",
    ),
    ("taxation-llm", _LAW, "llm", "on_campus", "/graduate/law/programs/taxation-llm/", ""),
    (
        "cybersecurity-risk-strategy-ms",
        _LAW,
        "ms",
        "on_campus",
        "/graduate/law/programs/cybersecurity-risk-strategy-ms/",
        "",
    ),
    (
        "health-law-strategy-ms",
        _LAW,
        "ms",
        "on_campus",
        "/graduate/law/programs/health-law-strategy-ms/",
        "",
    ),
    ("taxation-msl", _LAW, "msl", "on_campus", "/graduate/law/programs/taxation-msl/", ""),
    # ── LS ──
    (
        "global-liberal-studies-ba",
        _LS,
        "ba",
        "on_campus",
        "/undergraduate/liberal-studies/programs/global-liberal-studies-ba/",
        "",
    ),
    (
        "global-liberal-studies-public-health-ba",
        _LS,
        "ba",
        "on_campus",
        "/undergraduate/liberal-studies/programs/global-liberal-studies-public-health-ba/",
        "",
    ),
    # ── MED ──
    (
        "medicine-md",
        _MED,
        "md",
        "on_campus",
        "/graduate/medicine-grossman/programs/medicine-md/",
        "",
    ),
    (
        "clinical-investigation-ms",
        _MED,
        "ms",
        "on_campus",
        "/graduate/medicine-grossman/programs/clinical-investigation-ms/",
        "",
    ),
    (
        "genome-health-analysis-ms",
        _MED,
        "ms",
        "on_campus",
        "/graduate/medicine-grossman/programs/genome-health-analysis-ms/",
        "",
    ),
    # ── MEDLI ──
    (
        "medicine-md",
        _MEDLI,
        "md",
        "on_campus",
        "/graduate/medicine-long-island/programs/medicine-md/",
        "-long-island",
    ),
    # ── NURSING ──
    (
        "global-public-health-nursing-bs",
        _NURSING,
        "bs",
        "on_campus",
        "/undergraduate/nursing/programs/global-public-health-nursing-bs/",
        "",
    ),
    (
        "nursing-accelerated-15-month-bs",
        _NURSING,
        "bs",
        "on_campus",
        "/undergraduate/nursing/programs/nursing-accelerated-15-month-bs/",
        "",
    ),
    (
        "nursing-traditional-4-year-bs",
        _NURSING,
        "bs",
        "on_campus",
        "/undergraduate/nursing/programs/nursing-traditional-4-year-bs/",
        "",
    ),
    (
        "adult-gerontology-acute-care-nurse-practitioner-dnp",
        _NURSING,
        "dnp",
        "on_campus",
        "/graduate/nursing/programs/adult-gerontology-acute-care-nurse-practitioner-dnp/",
        "",
    ),
    (
        "adult-gerontology-primary-care-nurse-practitioner-dnp",
        _NURSING,
        "dnp",
        "on_campus",
        "/graduate/nursing/programs/adult-gerontology-primary-care-nurse-practitioner-dnp/",
        "",
    ),
    (
        "family-nurse-practitioner-dnp",
        _NURSING,
        "dnp",
        "on_campus",
        "/graduate/nursing/programs/family-nurse-practitioner-dnp/",
        "",
    ),
    (
        "nurse-midwifery-dnp",
        _NURSING,
        "dnp",
        "on_campus",
        "/graduate/nursing/programs/nurse-midwifery-dnp/",
        "",
    ),
    (
        "pediatric-nurse-practitioner-dnp",
        _NURSING,
        "dnp",
        "on_campus",
        "/graduate/nursing/programs/pediatric-nurse-practitioner-dnp/",
        "",
    ),
    (
        "psychiatric-mental-health-nurse-practitioner-dnp",
        _NURSING,
        "dnp",
        "on_campus",
        "/graduate/nursing/programs/psychiatric-mental-health-nurse-practitioner-dnp/",
        "",
    ),
    (
        "adult-gerontology-acute-care-nurse-practitioner-ms",
        _NURSING,
        "ms",
        "on_campus",
        "/graduate/nursing/programs/adult-gerontology-acute-care-nurse-practitioner-ms/",
        "",
    ),
    (
        "adult-gerontology-primary-care-nurse-practitioner-ms",
        _NURSING,
        "ms",
        "on_campus",
        "/graduate/nursing/programs/adult-gerontology-primary-care-nurse-practitioner-ms/",
        "",
    ),
    (
        "clinical-research-nursing-ms",
        _NURSING,
        "ms",
        "on_campus",
        "/graduate/nursing/programs/clinical-research-nursing-ms/",
        "",
    ),
    (
        "family-nurse-practitioner-ms",
        _NURSING,
        "ms",
        "on_campus",
        "/graduate/nursing/programs/family-nurse-practitioner-ms/",
        "",
    ),
    (
        "nurse-midwifery-ms",
        _NURSING,
        "ms",
        "on_campus",
        "/graduate/nursing/programs/nurse-midwifery-ms/",
        "",
    ),
    (
        "nursing-education-ms",
        _NURSING,
        "ms",
        "on_campus",
        "/graduate/nursing/programs/nursing-education-ms/",
        "",
    ),
    (
        "nursing-informatics-ms",
        _NURSING,
        "ms",
        "on_campus",
        "/graduate/nursing/programs/nursing-informatics-ms/",
        "",
    ),
    (
        "pediatrics-nurse-practitioner-primary-care-acute-ms",
        _NURSING,
        "ms",
        "on_campus",
        "/graduate/nursing/programs/pediatrics-nurse-practitioner-primary-care-acute-ms/",
        "",
    ),
    (
        "pediatrics-primary-care-nurse-practitioner-ms",
        _NURSING,
        "ms",
        "on_campus",
        "/graduate/nursing/programs/pediatrics-primary-care-nurse-practitioner-ms/",
        "",
    ),
    (
        "psychiatric-mental-health-nurse-practitioner-ms",
        _NURSING,
        "ms",
        "on_campus",
        "/graduate/nursing/programs/psychiatric-mental-health-nurse-practitioner-ms/",
        "",
    ),
    (
        "nursing-research-theory-development-phd",
        _NURSING,
        "phd",
        "on_campus",
        "/graduate/nursing/programs/nursing-research-theory-development-phd/",
        "",
    ),
    # ── SILVER ──
    (
        "global-public-health-social-work-bs",
        _SILVER,
        "bs",
        "on_campus",
        "/undergraduate/social-work/programs/global-public-health-social-work-bs/",
        "",
    ),
    (
        "clinical-social-work-dsw",
        _SILVER,
        "dsw",
        "on_campus",
        "/graduate/social-work/programs/clinical-social-work-dsw/",
        "",
    ),
    (
        "social-work-msw",
        _SILVER,
        "msw",
        "on_campus",
        "/graduate/social-work/programs/social-work-msw/",
        "",
    ),
    (
        "social-work-phd",
        _SILVER,
        "phd",
        "on_campus",
        "/graduate/social-work/programs/social-work-phd/",
        "",
    ),
    # ── SPS ──
    (
        "applied-general-studies-ba",
        _SPS,
        "ba",
        "on_campus",
        "/undergraduate/professional-studies/programs/applied-general-studies-ba/",
        "",
    ),
    (
        "humanities-ba",
        _SPS,
        "ba",
        "on_campus",
        "/undergraduate/professional-studies/programs/humanities-ba/",
        "",
    ),
    (
        "social-sciences-ba",
        _SPS,
        "ba",
        "on_campus",
        "/undergraduate/professional-studies/programs/social-sciences-ba/",
        "",
    ),
    (
        "applied-data-analytics-visualization-bs",
        _SPS,
        "bs",
        "on_campus",
        "/undergraduate/professional-studies/programs/applied-data-analytics-visualization-bs/",
        "",
    ),
    (
        "digital-communications-media-bs",
        _SPS,
        "bs",
        "on_campus",
        "/undergraduate/professional-studies/programs/digital-communications-media-bs/",
        "",
    ),
    (
        "healthcare-management-bs",
        _SPS,
        "bs",
        "on_campus",
        "/undergraduate/professional-studies/programs/healthcare-management-bs/",
        "",
    ),
    (
        "hospitality-travel-tourism-management-bs",
        _SPS,
        "bs",
        "on_campus",
        "/undergraduate/professional-studies/programs/hospitality-travel-tourism-management-bs/",
        "",
    ),
    (
        "information-systems-technology-bs",
        _SPS,
        "bs",
        "on_campus",
        "/undergraduate/professional-studies/programs/information-systems-technology-bs/",
        "",
    ),
    (
        "leadership-management-bs",
        _SPS,
        "bs",
        "on_campus",
        "/undergraduate/professional-studies/programs/leadership-management-bs/",
        "",
    ),
    (
        "marketing-analytics-bs",
        _SPS,
        "bs",
        "on_campus",
        "/undergraduate/professional-studies/programs/marketing-analytics-bs/",
        "",
    ),
    (
        "real-estate-bs",
        _SPS,
        "bs",
        "on_campus",
        "/undergraduate/professional-studies/programs/real-estate-bs/",
        "",
    ),
    (
        "real-estate-urban-sustainability-bs",
        _SPS,
        "bs",
        "on_campus",
        "/undergraduate/professional-studies/programs/real-estate-urban-sustainability-bs/",
        "",
    ),
    (
        "sport-management-bs",
        _SPS,
        "bs",
        "on_campus",
        "/undergraduate/professional-studies/programs/sport-management-bs/",
        "",
    ),
    (
        "entrepreneurship-management-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/entrepreneurship-management-ms/",
        "",
    ),
    (
        "event-management-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/event-management-ms/",
        "",
    ),
    (
        "executive-coaching-organizational-consulting-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/executive-coaching-organizational-consulting-ms/",
        "",
    ),
    (
        "financial-planning-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/financial-planning-ms/",
        "",
    ),
    (
        "global-affairs-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/global-affairs-ms/",
        "",
    ),
    (
        "global-hospitality-management-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/global-hospitality-management-ms/",
        "",
    ),
    (
        "global-security-conflict-cyber-crime-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/global-security-conflict-cyber-crime-ms/",
        "",
    ),
    (
        "global-sport-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/global-sport-ms/",
        "",
    ),
    (
        "human-capital-analytics-technology-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/human-capital-analytics-technology-ms/",
        "",
    ),
    (
        "human-capital-management-human-capital-analytics-technology-ms-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/human-capital-management-human-capital-analytics-technology-ms-ms/",
        "",
    ),
    (
        "human-capital-management-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/human-capital-management-ms/",
        "",
    ),
    (
        "integrated-marketing-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/integrated-marketing-ms/",
        "",
    ),
    (
        "management-analytics-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/management-analytics-ms/",
        "",
    ),
    (
        "professional-writing-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/professional-writing-ms/",
        "",
    ),
    (
        "project-management-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/project-management-ms/",
        "",
    ),
    (
        "public-relations-corporate-communication-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/public-relations-corporate-communication-ms/",
        "",
    ),
    (
        "publishing-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/publishing-ms/",
        "",
    ),
    (
        "real-estate-development-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/real-estate-development-ms/",
        "",
    ),
    (
        "real-estate-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/real-estate-ms/",
        "",
    ),
    (
        "sports-business-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/sports-business-ms/",
        "",
    ),
    (
        "translation-interpreting-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/translation-interpreting-ms/",
        "",
    ),
    (
        "travel-tourism-management-ms",
        _SPS,
        "ms",
        "on_campus",
        "/graduate/professional-studies/programs/travel-tourism-management-ms/",
        "",
    ),
    # ── STEINHARDT ──
    (
        "education-studies-ba",
        _STEINHARDT,
        "ba",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/education-studies-ba/",
        "",
    ),
    (
        "studio-art-bfa",
        _STEINHARDT,
        "bfa",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/studio-art-bfa/",
        "",
    ),
    (
        "instrumental-performance-bm",
        _STEINHARDT,
        "bm",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/instrumental-performance-bm/",
        "",
    ),
    (
        "music-business-bm",
        _STEINHARDT,
        "bm",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/music-business-bm/",
        "",
    ),
    (
        "music-technology-bm",
        _STEINHARDT,
        "bm",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/music-technology-bm/",
        "",
    ),
    (
        "music-theory-composition-bm",
        _STEINHARDT,
        "bm",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/music-theory-composition-bm/",
        "",
    ),
    (
        "piano-performance-bm",
        _STEINHARDT,
        "bm",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/piano-performance-bm/",
        "",
    ),
    (
        "vocal-performance-bm",
        _STEINHARDT,
        "bm",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/vocal-performance-bm/",
        "",
    ),
    (
        "applied-psychology-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/applied-psychology-bs/",
        "",
    ),
    (
        "childhood-education-childhood-special-education-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/childhood-education-childhood-special-education-bs/",
        "",
    ),
    (
        "communicative-sciences-disorders-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/communicative-sciences-disorders-bs/",
        "",
    ),
    (
        "early-childhood-education-special-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/early-childhood-education-special-bs/",
        "",
    ),
    (
        "educational-theatre-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/educational-theatre-bs/",
        "",
    ),
    (
        "global-public-health-applied-psychology-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/global-public-health-applied-psychology-bs/",
        "",
    ),
    (
        "global-public-health-communicative-sciences-disorders-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/global-public-health-communicative-sciences-disorders-bs/",
        "",
    ),
    (
        "global-public-health-food-studies-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/global-public-health-food-studies-bs/",
        "",
    ),
    (
        "global-public-health-media-culture-communication-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/global-public-health-media-culture-communication-bs/",
        "",
    ),
    (
        "global-public-health-nutrition-dietetics-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/global-public-health-nutrition-dietetics-bs/",
        "",
    ),
    (
        "health-wellbeing-studies-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/health-wellbeing-studies-bs/",
        "",
    ),
    (
        "media-culture-communication-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/media-culture-communication-bs/",
        "",
    ),
    (
        "music-business-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/music-business-bs/",
        "",
    ),
    (
        "nutrition-food-studies-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/nutrition-food-studies-bs/",
        "",
    ),
    (
        "professional-studies-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/professional-studies-bs/",
        "",
    ),
    (
        "teaching-biology-7-12-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/teaching-biology-7-12-bs/",
        "",
    ),
    (
        "teaching-chemistry-7-12-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/teaching-chemistry-7-12-bs/",
        "",
    ),
    (
        "teaching-earth-science-7-12-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/teaching-earth-science-7-12-bs/",
        "",
    ),
    (
        "teaching-english-712-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/teaching-english-712-bs/",
        "",
    ),
    (
        "teaching-mathematics-712-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/teaching-mathematics-712-bs/",
        "",
    ),
    (
        "teaching-physics-7-12-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/teaching-physics-7-12-bs/",
        "",
    ),
    (
        "teaching-social-studies-712-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/teaching-social-studies-712-bs/",
        "",
    ),
    (
        "teaching-world-language-7-12-chinese-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/teaching-world-language-7-12-chinese-bs/",
        "",
    ),
    (
        "teaching-world-language-7-12-french-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/teaching-world-language-7-12-french-bs/",
        "",
    ),
    (
        "teaching-world-language-7-12-italian-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/teaching-world-language-7-12-italian-bs/",
        "",
    ),
    (
        "teaching-world-language-7-12-japanese-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/teaching-world-language-7-12-japanese-bs/",
        "",
    ),
    (
        "teaching-world-language-7-12-spanish-bs",
        _STEINHARDT,
        "bs",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/teaching-world-language-7-12-spanish-bs/",
        "",
    ),
    (
        "music-performance-dma",
        _STEINHARDT,
        "dma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/music-performance-dma/",
        "",
    ),
    (
        "physical-therapy-entry-level-dpt",
        _STEINHARDT,
        "dpt",
        "on_campus",
        "/graduate/culture-education-human-development/programs/physical-therapy-entry-level-dpt/",
        "",
    ),
    (
        "physical-therapy-practicing-physical-therapists-dpt",
        _STEINHARDT,
        "dpt",
        "on_campus",
        "/graduate/culture-education-human-development/programs/physical-therapy-practicing-physical-therapists-dpt/",
        "",
    ),
    (
        "educational-leadership-policy-studies-edd",
        _STEINHARDT,
        "edd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/educational-leadership-policy-studies-edd/",
        "",
    ),
    (
        "educational-theatre-colleges-communities-edd",
        _STEINHARDT,
        "edd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/educational-theatre-colleges-communities-edd/",
        "",
    ),
    (
        "higher-education-administration-edd",
        _STEINHARDT,
        "edd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/higher-education-administration-edd/",
        "",
    ),
    (
        "leadership-innovation-edd",
        _STEINHARDT,
        "edd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/leadership-innovation-edd/",
        "",
    ),
    (
        "advanced-occupational-therapy-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/advanced-occupational-therapy-ma/",
        "",
    ),
    (
        "art-education-community-practice-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/art-education-community-practice-ma/",
        "",
    ),
    (
        "art-therapy-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/art-therapy-ma/",
        "",
    ),
    (
        "bilingual-education-teachers-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/bilingual-education-teachers-ma/",
        "",
    ),
    (
        "childhood-education-special-education-childhood-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/childhood-education-special-education-childhood-ma/",
        "",
    ),
    (
        "childhood-special-education-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/childhood-special-education-ma/",
        "",
    ),
    (
        "costume-studies-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/costume-studies-ma/",
        "",
    ),
    (
        "counseling-mental-health-wellness-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/counseling-mental-health-wellness-ma/",
        "",
    ),
    (
        "drama-therapy-alternate-licensure-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/drama-therapy-alternate-licensure-ma/",
        "",
    ),
    (
        "drama-therapy-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/drama-therapy-ma/",
        "",
    ),
    (
        "early-childhood-education-special-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/early-childhood-education-special-ma/",
        "",
    ),
    (
        "educational-leadership-politics-advocacy-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/educational-leadership-politics-advocacy-ma/",
        "",
    ),
    (
        "educational-theatre-all-grades-english-712-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/educational-theatre-all-grades-english-712-ma/",
        "",
    ),
    (
        "educational-theatre-all-grades-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/educational-theatre-all-grades-ma/",
        "",
    ),
    (
        "educational-theatre-all-grades-social-studies-712-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/educational-theatre-all-grades-social-studies-712-ma/",
        "",
    ),
    (
        "environmental-conservation-education-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/environmental-conservation-education-ma/",
        "",
    ),
    (
        "food-studies-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/food-studies-ma/",
        "",
    ),
    (
        "higher-education-student-affairs-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/higher-education-student-affairs-ma/",
        "",
    ),
    (
        "human-development-research-policy-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/human-development-research-policy-ma/",
        "",
    ),
    (
        "international-education-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/international-education-ma/",
        "",
    ),
    (
        "learning-technology-experience-design-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/learning-technology-experience-design-ma/",
        "",
    ),
    (
        "media-culture-communication-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/media-culture-communication-ma/",
        "",
    ),
    (
        "music-business-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/music-business-ma/",
        "",
    ),
    (
        "music-therapists-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/music-therapists-ma/",
        "",
    ),
    (
        "performing-arts-administration-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/performing-arts-administration-ma/",
        "",
    ),
    (
        "physical-therapists-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/physical-therapists-ma/",
        "",
    ),
    (
        "special-education-early-childhood-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/special-education-early-childhood-ma/",
        "",
    ),
    (
        "specialized-studies-education-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/specialized-studies-education-ma/",
        "",
    ),
    (
        "teacher-dance-all-grades-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/teacher-dance-all-grades-ma/",
        "",
    ),
    (
        "teachers-english-7-12-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/teachers-english-7-12-ma/",
        "",
    ),
    (
        "teachers-mathematics-7-12-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/teachers-mathematics-7-12-ma/",
        "",
    ),
    (
        "teaching-art-all-grades-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/teaching-art-all-grades-ma/",
        "",
    ),
    (
        "teaching-dance-all-grades-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/teaching-dance-all-grades-ma/",
        "",
    ),
    (
        "teaching-dance-professions-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/teaching-dance-professions-ma/",
        "",
    ),
    (
        "teaching-english-7-12-5-6-extension-students-disabilities-7-12-generalist-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/teaching-english-7-12-5-6-extension-students-disabilities-7-12-generalist-ma/",
        "",
    ),
    (
        "teaching-english-language-literature-college-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/teaching-english-language-literature-college-ma/",
        "",
    ),
    (
        "teaching-english-speakers-other-languages-all-grades-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/teaching-english-speakers-other-languages-all-grades-ma/",
        "",
    ),
    (
        "teaching-english-speakers-other-languages-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/teaching-english-speakers-other-languages-ma/",
        "",
    ),
    (
        "teaching-social-studies-7-12-5-6-extension-students-disabilities-7-12-generalist-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/teaching-social-studies-7-12-5-6-extension-students-disabilities-7-12-generalist-ma/",
        "",
    ),
    (
        "teaching-world-languages-7-12-tesol-all-grades-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/teaching-world-languages-7-12-tesol-all-grades-ma/",
        "",
    ),
    (
        "theatre-social-civic-engagement-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/theatre-social-civic-engagement-ma/",
        "",
    ),
    (
        "visual-arts-administration-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/visual-arts-administration-ma/",
        "",
    ),
    (
        "world-language-education-ma",
        _STEINHARDT,
        "ma",
        "on_campus",
        "/graduate/culture-education-human-development/programs/world-language-education-ma/",
        "",
    ),
    (
        "inclusive-childhood-teacher-residency-mat",
        _STEINHARDT,
        "mat",
        "on_campus",
        "/graduate/culture-education-human-development/programs/inclusive-childhood-teacher-residency-mat/",
        "",
    ),
    (
        "teacher-residency-mat",
        _STEINHARDT,
        "mat",
        "on_campus",
        "/graduate/culture-education-human-development/programs/teacher-residency-mat/",
        "",
    ),
    (
        "transformational-teaching-middle-high-schools-mat",
        _STEINHARDT,
        "mat",
        "on_campus",
        "/graduate/culture-education-human-development/programs/transformational-teaching-middle-high-schools-mat/",
        "",
    ),
    (
        "transformational-teaching-students-disabilities-computer-science-mat",
        _STEINHARDT,
        "mat",
        "on_campus",
        "/graduate/culture-education-human-development/programs/transformational-teaching-students-disabilities-computer-science-mat/",
        "",
    ),
    (
        "studio-art-mfa",
        _STEINHARDT,
        "mfa",
        "on_campus",
        "/graduate/culture-education-human-development/programs/studio-art-mfa/",
        "",
    ),
    (
        "instrumental-performance-mm",
        _STEINHARDT,
        "mm",
        "on_campus",
        "/graduate/culture-education-human-development/programs/instrumental-performance-mm/",
        "",
    ),
    (
        "music-performance-piano-mm",
        _STEINHARDT,
        "mm",
        "on_campus",
        "/graduate/culture-education-human-development/programs/music-performance-piano-mm/",
        "",
    ),
    (
        "music-technology-mm",
        _STEINHARDT,
        "mm",
        "on_campus",
        "/graduate/culture-education-human-development/programs/music-technology-mm/",
        "",
    ),
    (
        "music-theory-composition-mm",
        _STEINHARDT,
        "mm",
        "on_campus",
        "/graduate/culture-education-human-development/programs/music-theory-composition-mm/",
        "",
    ),
    (
        "vocal-performance-mm",
        _STEINHARDT,
        "mm",
        "on_campus",
        "/graduate/culture-education-human-development/programs/vocal-performance-mm/",
        "",
    ),
    (
        "applied-statistics-social-science-research-ms",
        _STEINHARDT,
        "ms",
        "on_campus",
        "/graduate/culture-education-human-development/programs/applied-statistics-social-science-research-ms/",
        "",
    ),
    (
        "communicative-sciences-disorders-ms",
        _STEINHARDT,
        "ms",
        "on_campus",
        "/graduate/culture-education-human-development/programs/communicative-sciences-disorders-ms/",
        "",
    ),
    (
        "games-learning-ms",
        _STEINHARDT,
        "ms",
        "on_campus",
        "/graduate/culture-education-human-development/programs/games-learning-ms/",
        "",
    ),
    (
        "nutrition-dietetics-ms",
        _STEINHARDT,
        "ms",
        "on_campus",
        "/graduate/culture-education-human-development/programs/nutrition-dietetics-ms/",
        "",
    ),
    (
        "studio-art-integrated-design-media-bfa-ms",
        _STEINHARDT,
        "ms",
        "on_campus",
        "/undergraduate/culture-education-human-development/programs/studio-art-integrated-design-media-bfa-ms/",
        "",
    ),
    (
        "occupational-therapy-otd",
        _STEINHARDT,
        "otd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/occupational-therapy-otd/",
        "",
    ),
    (
        "occupational-therapy-practicing-occupational-therapists-otd",
        _STEINHARDT,
        "otd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/occupational-therapy-practicing-occupational-therapists-otd/",
        "",
    ),
    (
        "applied-linguistics-multilingual-education-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/applied-linguistics-multilingual-education-phd/",
        "",
    ),
    (
        "bilingual-education-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/bilingual-education-phd/",
        "",
    ),
    (
        "clinical-counseling-psychology-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/clinical-counseling-psychology-phd/",
        "",
    ),
    (
        "communicative-sciences-disorders-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/communicative-sciences-disorders-phd/",
        "",
    ),
    (
        "developmental-psychology-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/developmental-psychology-phd/",
        "",
    ),
    (
        "educational-communications-technology-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/educational-communications-technology-phd/",
        "",
    ),
    (
        "educational-leadership-policy-studies-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/educational-leadership-policy-studies-phd/",
        "",
    ),
    (
        "educational-theatre-colleges-communities-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/educational-theatre-colleges-communities-phd/",
        "",
    ),
    (
        "english-education-secondary-college-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/english-education-secondary-college-phd/",
        "",
    ),
    (
        "food-studies-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/food-studies-phd/",
        "",
    ),
    (
        "higher-education-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/higher-education-phd/",
        "",
    ),
    (
        "international-education-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/international-education-phd/",
        "",
    ),
    (
        "media-culture-communication-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/media-culture-communication-phd/",
        "",
    ),
    (
        "music-education-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/music-education-phd/",
        "",
    ),
    (
        "music-performance-composition-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/music-performance-composition-phd/",
        "",
    ),
    (
        "music-technology-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/music-technology-phd/",
        "",
    ),
    (
        "nutrition-dietetics-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/nutrition-dietetics-phd/",
        "",
    ),
    (
        "psychology-social-intervention-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/psychology-social-intervention-phd/",
        "",
    ),
    (
        "research-occupational-therapy-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/research-occupational-therapy-phd/",
        "",
    ),
    (
        "research-physical-therapy-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/research-physical-therapy-phd/",
        "",
    ),
    (
        "sociology-education-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/sociology-education-phd/",
        "",
    ),
    (
        "statistics-computational-social-science-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/statistics-computational-social-science-phd/",
        "",
    ),
    (
        "teaching-learning-phd",
        _STEINHARDT,
        "phd",
        "on_campus",
        "/graduate/culture-education-human-development/programs/teaching-learning-phd/",
        "",
    ),
    # ── STERN ──
    ("business-bs", _STERN, "bs", "on_campus", "/undergraduate/business/programs/business-bs/", ""),
    (
        "business-political-economy-bs",
        _STERN,
        "bs",
        "on_campus",
        "/undergraduate/business/programs/business-political-economy-bs/",
        "",
    ),
    (
        "business-technology-entrepreneurship-bs",
        _STERN,
        "bs",
        "on_campus",
        "/undergraduate/business/programs/business-technology-entrepreneurship-bs/",
        "",
    ),
    (
        "general-management-executives-mba",
        _STERN,
        "mba",
        "hybrid",
        "/graduate/business/programs/general-management-executives-mba/",
        "",
    ),
    (
        "general-management-mba",
        _STERN,
        "mba",
        "on_campus",
        "/graduate/business/programs/general-management-mba/",
        "",
    ),
    (
        "global-executive-mba",
        _STERN,
        "mba",
        "hybrid",
        "/graduate/business/programs/global-executive-mba/",
        "",
    ),
    (
        "luxury-retail-mba",
        _STERN,
        "mba",
        "on_campus",
        "/graduate/business/programs/luxury-retail-mba/",
        "",
    ),
    (
        "stern-nyu-abu-dhabi-mba",
        _STERN,
        "mba",
        "hybrid",
        "/graduate/business/programs/stern-nyu-abu-dhabi-mba/",
        "",
    ),
    (
        "technology-entrepreneurship-mba",
        _STERN,
        "mba",
        "on_campus",
        "/graduate/business/programs/technology-entrepreneurship-mba/",
        "",
    ),
    (
        "accounting-bs-ms",
        _STERN,
        "ms",
        "on_campus",
        "/undergraduate/business/programs/accounting-bs-ms/",
        "",
    ),
    ("accounting-ms", _STERN, "ms", "on_campus", "/graduate/business/programs/accounting-ms/", ""),
    (
        "business-analytics-ai-ms",
        _STERN,
        "ms",
        "on_campus",
        "/graduate/business/programs/business-analytics-ai-ms/",
        "",
    ),
    (
        "data-analytics-business-computing-ms",
        _STERN,
        "ms",
        "on_campus",
        "/graduate/business/programs/data-analytics-business-computing-ms/",
        "",
    ),
    ("fintech-ms", _STERN, "ms", "on_campus", "/graduate/business/programs/fintech-ms/", ""),
    (
        "global-finance-ms",
        _STERN,
        "ms",
        "on_campus",
        "/graduate/business/programs/global-finance-ms/",
        "",
    ),
    ("management-ms", _STERN, "ms", "on_campus", "/graduate/business/programs/management-ms/", ""),
    (
        "marketing-retail-science-ms",
        _STERN,
        "ms",
        "on_campus",
        "/graduate/business/programs/marketing-retail-science-ms/",
        "",
    ),
    (
        "organization-management-strategy-ms",
        _STERN,
        "ms",
        "on_campus",
        "/graduate/business/programs/organization-management-strategy-ms/",
        "",
    ),
    (
        "quantitative-finance-ms",
        _STERN,
        "ms",
        "on_campus",
        "/graduate/business/programs/quantitative-finance-ms/",
        "",
    ),
    (
        "accounting-phd",
        _STERN,
        "phd",
        "on_campus",
        "/graduate/business/programs/accounting-phd/",
        "",
    ),
    (
        "economics-phd",
        _STERN,
        "phd",
        "on_campus",
        "/graduate/business/programs/economics-phd/",
        "-stern",
    ),
    ("finance-phd", _STERN, "phd", "on_campus", "/graduate/business/programs/finance-phd/", ""),
    (
        "information-systems-phd",
        _STERN,
        "phd",
        "on_campus",
        "/graduate/business/programs/information-systems-phd/",
        "",
    ),
    (
        "management-organizational-behavior-phd",
        _STERN,
        "phd",
        "on_campus",
        "/graduate/business/programs/management-organizational-behavior-phd/",
        "",
    ),
    ("marketing-phd", _STERN, "phd", "on_campus", "/graduate/business/programs/marketing-phd/", ""),
    (
        "operations-management-phd",
        _STERN,
        "phd",
        "on_campus",
        "/graduate/business/programs/operations-management-phd/",
        "",
    ),
    (
        "statistics-phd",
        _STERN,
        "phd",
        "on_campus",
        "/graduate/business/programs/statistics-phd/",
        "",
    ),
    # ── TANDON ──
    (
        "applied-physics-bs",
        _TANDON,
        "bs",
        "on_campus",
        "/undergraduate/engineering/programs/applied-physics-bs/",
        "",
    ),
    (
        "biomolecular-science-bs",
        _TANDON,
        "bs",
        "on_campus",
        "/undergraduate/engineering/programs/biomolecular-science-bs/",
        "",
    ),
    (
        "business-technology-management-bs",
        _TANDON,
        "bs",
        "on_campus",
        "/undergraduate/engineering/programs/business-technology-management-bs/",
        "",
    ),
    (
        "chemical-biomolecular-engineering-bs",
        _TANDON,
        "bs",
        "on_campus",
        "/undergraduate/engineering/programs/chemical-biomolecular-engineering-bs/",
        "",
    ),
    (
        "civil-engineering-bs",
        _TANDON,
        "bs",
        "on_campus",
        "/undergraduate/engineering/programs/civil-engineering-bs/",
        "",
    ),
    (
        "computer-engineering-bs",
        _TANDON,
        "bs",
        "on_campus",
        "/undergraduate/engineering/programs/computer-engineering-bs/",
        "",
    ),
    (
        "computer-science-bs",
        _TANDON,
        "bs",
        "on_campus",
        "/undergraduate/engineering/programs/computer-science-bs/",
        "",
    ),
    (
        "electrical-computer-engineering-bs",
        _TANDON,
        "bs",
        "on_campus",
        "/undergraduate/engineering/programs/electrical-computer-engineering-bs/",
        "",
    ),
    (
        "electrical-engineering-bs",
        _TANDON,
        "bs",
        "on_campus",
        "/undergraduate/engineering/programs/electrical-engineering-bs/",
        "",
    ),
    (
        "environmental-engineering-bs",
        _TANDON,
        "bs",
        "on_campus",
        "/undergraduate/engineering/programs/environmental-engineering-bs/",
        "",
    ),
    (
        "integrated-design-media-bs",
        _TANDON,
        "bs",
        "on_campus",
        "/undergraduate/engineering/programs/integrated-design-media-bs/",
        "",
    ),
    (
        "mathematics-bs",
        _TANDON,
        "bs",
        "on_campus",
        "/undergraduate/engineering/programs/mathematics-bs/",
        "",
    ),
    (
        "mathematics-physics-bs",
        _TANDON,
        "bs",
        "on_campus",
        "/undergraduate/engineering/programs/mathematics-physics-bs/",
        "",
    ),
    (
        "mechanical-engineering-bs",
        _TANDON,
        "bs",
        "on_campus",
        "/undergraduate/engineering/programs/mechanical-engineering-bs/",
        "",
    ),
    (
        "applied-quantum-science-technology-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/applied-quantum-science-technology-ms/",
        "",
    ),
    (
        "bioinformatics-online-ms",
        _TANDON,
        "ms",
        "online",
        "/graduate/engineering/programs/bioinformatics-online-ms/",
        "",
    ),
    (
        "biomedical-engineering-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/biomedical-engineering-ms/",
        "",
    ),
    (
        "biotechnology-entrepreneurship-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/biotechnology-entrepreneurship-ms/",
        "",
    ),
    (
        "biotechnology-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/biotechnology-ms/",
        "",
    ),
    (
        "chemical-engineering-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/chemical-engineering-ms/",
        "",
    ),
    (
        "civil-engineering-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/civil-engineering-ms/",
        "",
    ),
    (
        "computer-engineering-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/computer-engineering-ms/",
        "",
    ),
    (
        "computer-science-management-technology-bs-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/undergraduate/engineering/programs/computer-science-management-technology-bs-ms/",
        "",
    ),
    (
        "computer-science-tandon-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/computer-science-tandon-ms/",
        "",
    ),
    (
        "construction-management-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/construction-management-ms/",
        "",
    ),
    (
        "cybersecurity-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/cybersecurity-ms/",
        "",
    ),
    (
        "electrical-engineering-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/electrical-engineering-ms/",
        "",
    ),
    (
        "emerging-technologies-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/emerging-technologies-ms/",
        "",
    ),
    (
        "environmental-engineering-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/environmental-engineering-ms/",
        "",
    ),
    (
        "environmental-science-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/environmental-science-ms/",
        "",
    ),
    (
        "financial-engineering-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/financial-engineering-ms/",
        "",
    ),
    (
        "industrial-engineering-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/industrial-engineering-ms/",
        "",
    ),
    (
        "integrated-design-media-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/integrated-design-media-ms/",
        "",
    ),
    (
        "management-technology-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/management-technology-ms/",
        "",
    ),
    (
        "mathematical-sciences-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/mathematical-sciences-ms/",
        "",
    ),
    (
        "mechanical-engineering-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/mechanical-engineering-ms/",
        "",
    ),
    (
        "mechatronics-robotics-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/mechatronics-robotics-ms/",
        "",
    ),
    (
        "transportation-systems-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/transportation-systems-ms/",
        "",
    ),
    (
        "urban-infrastructure-systems-ms",
        _TANDON,
        "ms",
        "on_campus",
        "/graduate/engineering/programs/urban-infrastructure-systems-ms/",
        "",
    ),
    (
        "biomedical-engineering-phd",
        _TANDON,
        "phd",
        "on_campus",
        "/graduate/engineering/programs/biomedical-engineering-phd/",
        "",
    ),
    (
        "chemical-engineering-phd",
        _TANDON,
        "phd",
        "on_campus",
        "/graduate/engineering/programs/chemical-engineering-phd/",
        "",
    ),
    (
        "civil-engineering-phd",
        _TANDON,
        "phd",
        "on_campus",
        "/graduate/engineering/programs/civil-engineering-phd/",
        "",
    ),
    (
        "electrical-computer-engineering-phd",
        _TANDON,
        "phd",
        "on_campus",
        "/graduate/engineering/programs/electrical-computer-engineering-phd/",
        "",
    ),
    (
        "human-centered-technology-innovation-design-phd",
        _TANDON,
        "phd",
        "on_campus",
        "/graduate/engineering/programs/human-centered-technology-innovation-design-phd/",
        "",
    ),
    (
        "mechanical-engineering-phd",
        _TANDON,
        "phd",
        "on_campus",
        "/graduate/engineering/programs/mechanical-engineering-phd/",
        "",
    ),
    (
        "transportation-systems-phd",
        _TANDON,
        "phd",
        "on_campus",
        "/graduate/engineering/programs/transportation-systems-phd/",
        "",
    ),
    (
        "urban-systems-phd",
        _TANDON,
        "phd",
        "on_campus",
        "/graduate/engineering/programs/urban-systems-phd/",
        "",
    ),
    # ── TISCH ──
    (
        "cinema-studies-ba",
        _TISCH,
        "ba",
        "on_campus",
        "/undergraduate/arts/programs/cinema-studies-ba/",
        "-tisch",
    ),
    (
        "performance-studies-ba",
        _TISCH,
        "ba",
        "on_campus",
        "/undergraduate/arts/programs/performance-studies-ba/",
        "",
    ),
    (
        "collaborative-arts-bfa",
        _TISCH,
        "bfa",
        "on_campus",
        "/undergraduate/arts/programs/collaborative-arts-bfa/",
        "",
    ),
    ("dance-bfa", _TISCH, "bfa", "on_campus", "/undergraduate/arts/programs/dance-bfa/", ""),
    (
        "dramatic-writing-bfa",
        _TISCH,
        "bfa",
        "on_campus",
        "/undergraduate/arts/programs/dramatic-writing-bfa/",
        "",
    ),
    (
        "film-television-bfa",
        _TISCH,
        "bfa",
        "on_campus",
        "/undergraduate/arts/programs/film-television-bfa/",
        "",
    ),
    (
        "game-design-bfa",
        _TISCH,
        "bfa",
        "on_campus",
        "/undergraduate/arts/programs/game-design-bfa/",
        "",
    ),
    (
        "interactive-media-arts-bfa",
        _TISCH,
        "bfa",
        "on_campus",
        "/undergraduate/arts/programs/interactive-media-arts-bfa/",
        "",
    ),
    (
        "photography-imaging-bfa",
        _TISCH,
        "bfa",
        "on_campus",
        "/undergraduate/arts/programs/photography-imaging-bfa/",
        "",
    ),
    (
        "recorded-music-bfa",
        _TISCH,
        "bfa",
        "on_campus",
        "/undergraduate/arts/programs/recorded-music-bfa/",
        "",
    ),
    ("theatre-bfa", _TISCH, "bfa", "on_campus", "/undergraduate/arts/programs/theatre-bfa/", ""),
    (
        "arts-politics-ma",
        _TISCH,
        "ma",
        "on_campus",
        "/graduate/arts/programs/arts-politics-ma/",
        "",
    ),
    (
        "interactive-media-arts-ma",
        _TISCH,
        "ma",
        "on_campus",
        "/graduate/arts/programs/interactive-media-arts-ma/",
        "",
    ),
    (
        "media-producing-ma",
        _TISCH,
        "ma",
        "on_campus",
        "/graduate/arts/programs/media-producing-ma/",
        "",
    ),
    (
        "moving-image-archiving-preservation-ma",
        _TISCH,
        "ma",
        "on_campus",
        "/graduate/arts/programs/moving-image-archiving-preservation-ma/",
        "",
    ),
    ("acting-mfa", _TISCH, "mfa", "on_campus", "/graduate/arts/programs/acting-mfa/", ""),
    (
        "dance-interdisciplinary-research-mfa",
        _TISCH,
        "mfa",
        "on_campus",
        "/graduate/arts/programs/dance-interdisciplinary-research-mfa/",
        "",
    ),
    (
        "design-stage-film-mfa",
        _TISCH,
        "mfa",
        "on_campus",
        "/graduate/arts/programs/design-stage-film-mfa/",
        "",
    ),
    (
        "dramatic-writing-mfa",
        _TISCH,
        "mfa",
        "on_campus",
        "/graduate/arts/programs/dramatic-writing-mfa/",
        "",
    ),
    (
        "film-television-mfa",
        _TISCH,
        "mfa",
        "on_campus",
        "/graduate/arts/programs/film-television-mfa/",
        "",
    ),
    ("game-design-mfa", _TISCH, "mfa", "on_campus", "/graduate/arts/programs/game-design-mfa/", ""),
    (
        "musical-theatre-writing-mfa",
        _TISCH,
        "mfa",
        "on_campus",
        "/graduate/arts/programs/musical-theatre-writing-mfa/",
        "",
    ),
    (
        "interactive-telecommunications-mps",
        _TISCH,
        "mps",
        "on_campus",
        "/graduate/arts/programs/interactive-telecommunications-mps/",
        "",
    ),
    (
        "virtual-production-mps",
        _TISCH,
        "mps",
        "on_campus",
        "/graduate/arts/programs/virtual-production-mps/",
        "",
    ),
    # ── WAGNER ──
    (
        "executive-master-public-administration-empa",
        _WAGNER,
        "empa",
        "on_campus",
        "/graduate/public-service/programs/executive-master-public-administration-empa/",
        "",
    ),
    (
        "online-health-administration-mha",
        _WAGNER,
        "mha",
        "online",
        "/graduate/public-service/programs/online-health-administration-mha/",
        "",
    ),
    (
        "health-policy-management-mpa",
        _WAGNER,
        "mpa",
        "on_campus",
        "/graduate/public-service/programs/health-policy-management-mpa/",
        "",
    ),
    (
        "public-nonprofit-management-policy-mpa",
        _WAGNER,
        "mpa",
        "on_campus",
        "/graduate/public-service/programs/public-nonprofit-management-policy-mpa/",
        "",
    ),
    (
        "public-policy-ms",
        _WAGNER,
        "ms",
        "on_campus",
        "/graduate/public-service/programs/public-policy-ms/",
        "",
    ),
    (
        "urban-planning-mup",
        _WAGNER,
        "mup",
        "on_campus",
        "/graduate/public-service/programs/urban-planning-mup/",
        "",
    ),
    (
        "public-administration-phd",
        _WAGNER,
        "phd",
        "on_campus",
        "/graduate/public-service/programs/public-administration-phd/",
        "",
    ),
]


_FLAGSHIP = "nyu-general-management-mba"


def _build_catalog() -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for slug, school, code, fmt, path, suffix in _CATALOG:
        db_slug = f"nyu-{slug}{suffix}"
        if db_slug in seen:
            continue
        seen.add(db_slug)
        name, dtype, dept = _derive(slug, code)
        if db_slug in _DISAMBIG_NAMES:
            name = _DISAMBIG_NAMES[db_slug]
        spec = {
            "slug": db_slug,
            "bulletin_slug": slug,
            "school": school,
            "code": code,
            "program_name": name,
            "degree_type": dtype,
            "department": dept,
            "duration_months": _DURATION_BY_CODE.get(code, 24),
            "delivery_format": fmt,
            "website": f"https://bulletins.nyu.edu{path}",
        }
        spec["description"] = _nyu_description(spec)
        out.append(spec)
    return out


PROGRAMS: list[dict] = _build_catalog()
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

_catalog_errors = validate_catalog(PROGRAMS)
if _catalog_errors:
    raise ValueError(f"NYU catalog validation failed: {_catalog_errors}")

_CLASSIFICATION_STUB_RE = re.compile(
    r"^.* is (an undergraduate|a graduate|a doctoral|a professional) (program|major) "
    r"offered through NYU",
    re.I,
)

_name_prefix_desc = sum(
    1 for p in PROGRAMS if (p.get("description") or "").startswith(p.get("program_name", ""))
)
if _name_prefix_desc:
    raise ValueError(f"NYU catalog has {_name_prefix_desc} name-prefixed descriptions")
_desc_counts = Counter(p.get("description") for p in PROGRAMS)
_shared_desc = sum(c - 1 for c in _desc_counts.values() if c > 1)
if _shared_desc:
    raise ValueError(f"NYU catalog has {_shared_desc} identical descriptions shared across rows")
_stub_desc = sum(
    1 for p in PROGRAMS if _CLASSIFICATION_STUB_RE.match(p.get("description") or "")
)
if _stub_desc:
    raise ValueError(f"NYU catalog has {_stub_desc} classification stub descriptions")

# Per-program keywords (program/department-naming terms) so the shared school channel is filtered
# to program-relevant items. Programs without an entry inherit their school's keywords.
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "nyu-general-management-mba": ["Stern MBA", "Full-Time MBA", "MBA"],
    "nyu-law-jd": ["NYU Law", "J.D.", "School of Law"],
    "nyu-film-television-bfa": ["Tisch", "film", "Kanbar Institute", "television"],
    "nyu-computer-science-courant-ms": ["Courant", "computer science", "Center for Data Science"],
    "nyu-data-science-ms": ["Center for Data Science", "data science"],
    "nyu-computer-science-tandon-ms": ["Tandon", "computer science"],
    "nyu-public-nonprofit-management-policy-mpa": ["Wagner", "MPA", "public service"],
    "nyu-public-health-mph": ["public health", "MPH", "School of Global Public Health"],
}


# ── Costs ──────────────────────────────────────────────────────────────────
# NYU bills tuition per school and (for most graduate programs) per credit hour or per term, and
# publishes no single uniform annual program-tuition figure, so cost_data.tuition_usd is omitted
# on every program (recorded in _standard) and the verified College Scorecard institution figures
# (cost of attendance $84,374; average net price $37,050) anchor the cost picture. Undergraduate
# programs carry those institution figures; graduate/professional programs carry a sourced
# "see the program/bursar tuition page" record.
_UNDERGRAD_COA = 84374
_AVG_NET_PRICE = 37050
_COST_SRC = "U.S. Dept. of Education — College Scorecard (NYU, UNITID 193900) + NYU Bursar"
_COST_SRC_URL = "https://collegescorecard.ed.gov/school/?193900-New-York-University"


def _undergrad_cost() -> dict:
    return {
        "total_cost_of_attendance": _UNDERGRAD_COA,
        "avg_net_price": _AVG_NET_PRICE,
        "funded": False,
        "note": (
            "NYU's published academic-year cost of attendance is about $84,374 and the average "
            "net price (after grant aid) is about $37,050 (College Scorecard, UNITID 193900). "
            "Since 2021 NYU has met 100% of demonstrated financial need for incoming first-year "
            "undergraduates, and the NYU Promise makes tuition free for families earning under "
            "$100,000. A single tuition-only figure is set per school and per term by the NYU "
            "Bursar — see the program's bulletin page."
        ),
        "source": _COST_SRC,
        "source_url": _COST_SRC_URL,
        "year": "2024-25",
    }


def _grad_cost_fallback(spec: dict) -> dict:
    return {
        "note": (
            "Tuition for this graduate/professional program is set by the NYU Bursar — most NYU "
            "graduate programs bill per credit hour or per term and vary by school and "
            "enrollment, so a single verified annual figure is not published here. Research "
            "doctoral students are typically funded through assistantships and fellowships; the "
            "Grossman School of Medicine M.D. and the Grossman Long Island M.D. are tuition-free."
        ),
        "source": "NYU Bursar / program bulletin page",
        "source_url": spec["website"],
    }


# ── Outcomes (flagship programs with verified program-specific employment data) ──
# NYU does not publish a uniform program-level employment-outcomes table, so program outcomes are
# attached only where a verified program-specific report exists; all other programs omit the
# outcomes fields with reason (the institution-wide median earnings of $82,509 ten years after
# entry is recorded at the institution level).
_OUTCOMES_BY_SLUG: dict[str, dict] = {
    "nyu-general-management-mba": {
        "employment_rate": 0.846,
        "median_salary": 175000,
        "mean_salary": 166148,
        "top_industries": [
            "Consulting",
            "Financial Services",
            "Technology",
            "Consumer Products / Retail",
            "Healthcare",
        ],
        "scope": "program",
        "conditions": (
            "NYU Stern Full-Time (two-year) MBA, Class of 2024: of 324 graduates (273 seeking "
            "employment), 86.1% received and 84.6% accepted a full-time offer within three months "
            "of graduation; median base salary $175,000 (a Stern record, matched in 2023 and "
            "2025) and average base salary $166,148. Average total compensation including bonuses "
            "was about $210,000. Self-reported per the Stern MBA employment report."
        ),
        "source": "NYU Stern — MBA Class of 2024 Employment Report (via Clear Admit)",
        "source_url": "https://www.clearadmit.com/2024/12/nyu-stern-employment-report-mba-class-of-2024/",
    },
    "nyu-law-jd": {
        "employment_rate": 0.9706,
        "median_salary": 215000,
        "salary_25th": 75086,
        "mean_salary": 163698,
        "top_industries": [
            "Private practice (law firms)",
            "Public interest",
            "Government",
            "Judicial clerkships",
            "Business / J.D.-advantage",
        ],
        "scope": "program",
        "conditions": (
            "NYU School of Law J.D., Class of 2023 (ABA Standard 509 / NYU Law Career Services): "
            "97.06% of 442 graduates were employed ten months after graduation (Class of 2024: "
            "98.28%; Class of 2025: 99.28%); median full-time salary $215,000, 25th percentile "
            "$75,086, mean $163,698. First-time bar passage (2022) was 94.9%."
        ),
        "source": "NYU School of Law — Employment Data for Recent Graduates (ABA 509)",
        "source_url": "https://www.law.nyu.edu/careerservices/employmentstatistics",
    },
}

# ── Class profile (only where a verified figure is published) ──
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    "nyu-general-management-mba": {
        "cohort_size": 324,
        "note": "NYU Stern Full-Time MBA Class of 2024 graduating cohort (employment report).",
        "source": "NYU Stern — MBA Class of 2024 Employment Report",
        "source_url": "https://www.stern.nyu.edu/business-partnerships/employment-reports",
    },
    "nyu-law-jd": {
        "cohort_size": 442,
        "note": "NYU School of Law J.D. Class of 2023 graduating cohort (ABA 509 employment report).",
        "source": "NYU School of Law — Employment Statistics",
        "source_url": "https://www.law.nyu.edu/careerservices/employmentstatistics",
    },
}

# ── Faculty contacts (program leadership / directory) ──
_FACULTY_BY_SLUG: dict[str, dict] = {
    "nyu-general-management-mba": {
        "lead": "Bharat N. Anand — Richard R. West Dean of NYU Stern; the Jones-style MBA program is supported by the Stern Office of Career Development.",
        "directory_url": "https://www.stern.nyu.edu/faculty",
    },
    "nyu-law-jd": {
        "lead": "Troy A. McKenzie — Dean and Cecelia Goetz Professor of Law; the J.D. is taught by NYU Law's full-time faculty.",
        "directory_url": "https://www.law.nyu.edu/faculty",
    },
    "nyu-film-television-bfa": {
        "lead": "Faculty of the Maurice Kanbar Institute of Film & Television, Tisch School of the Arts.",
        "directory_url": "https://tisch.nyu.edu/film-tv",
    },
}

# ── External reviews (MBAn shape) for the flagship coverable programs ──
_REVIEWS_DISCLAIMER = (
    "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, "
    "the trade press, official employment reports, and reputable student-review communities). "
    "Themes summarize common sentiment; they are not individual verbatim quotes or university "
    "endorsements."
)

_REVIEWS_BY_SLUG: dict[str, dict] = {
    "nyu-general-management-mba": {
        "summary": (
            "The NYU Stern Full-Time MBA is a top-tier program (consistently ranked in the U.S. "
            "top 15) prized for its New York City location, its strength in finance and an "
            "increasingly broad set of specializations, and its record-high pay. Reviewers point "
            "to a median base salary of $175,000 and total compensation near $210,000, deep Wall "
            "Street and consulting recruiting, and a collaborative, internationally diverse "
            "cohort — while noting that the program is expensive, that the 2024 market softened "
            "placement to the mid-80s percent at three months, and that NYC living costs are high."
        ),
        "themes": [
            {
                "label": "Finance and NYC recruiting power",
                "sentiment": "positive",
                "detail": "Stern's Greenwich Village location and Wall Street ties make it a top feeder to investment banking, consulting, and increasingly tech; top employers span consulting, financial services, technology, and consumer/retail.",
            },
            {
                "label": "Record-high compensation",
                "sentiment": "positive",
                "detail": "Class of 2024 median base salary $175,000 (a school record matched again in 2025), with average total compensation around $210,000 including bonuses.",
            },
            {
                "label": "Specialized, flexible curriculum",
                "sentiment": "positive",
                "detail": "Beyond finance, students pursue Andre Koo Tech, Fashion & Luxury, and a wide menu of specializations; the part-time (Langone), executive, and one-year focused MBAs broaden access.",
            },
            {
                "label": "High cost of attendance",
                "sentiment": "caution",
                "detail": "Tuition plus New York City living costs make Stern one of the most expensive MBAs; reviewers stress the ROI math and the value of scholarships.",
            },
            {
                "label": "Market-sensitive placement",
                "sentiment": "mixed",
                "detail": "Three-month placement eased to about 84.6% accepted for the Class of 2024 after a 94% peak in 2023, reflecting a tougher national MBA hiring market rather than a Stern-specific decline.",
            },
        ],
        "sources": [
            {
                "label": "Clear Admit — NYU Stern Employment Report: MBA Class of 2024",
                "url": "https://www.clearadmit.com/2024/12/nyu-stern-employment-report-mba-class-of-2024/",
            },
            {
                "label": "Poets&Quants — NYU Stern MBAs Join The $200K Compensation Club",
                "url": "https://poetsandquants.com/2023/10/20/nyu-stern-mbas-join-the-200k-compensation-club/",
            },
            {
                "label": "NYU Stern — Full-Time MBA Employment Reports",
                "url": "https://www.stern.nyu.edu/business-partnerships/employment-reports",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "nyu-law-jd": {
        "summary": (
            "NYU School of Law is a perennial T6 law school — ranked No. 9 by U.S. News (2024-25) "
            "and No. 2 in the world for law by Times Higher Education — and is regarded as the "
            "nation's leader in tax and international law. Reviewers consistently praise its "
            "near-total employment outcomes (97-99% employed at ten months, median salary "
            "$215,000+), its exceptional public-interest infrastructure (Root-Tilden-Kern), and "
            "its NYC setting, while noting the high cost and the intensity of a top law-school "
            "environment."
        ),
        "themes": [
            {
                "label": "Elite, near-total employment outcomes",
                "sentiment": "positive",
                "detail": "Class of 2023: 97.06% employed at ten months with a $215,000 median salary; the Classes of 2024 and 2025 reported 98.28% and 99.28%. First-time bar passage was 94.9% in 2022.",
            },
            {
                "label": "No. 1 for tax and international law",
                "sentiment": "positive",
                "detail": "NYU Law's graduate tax (LL.M.) program and international law are widely ranked first in the country, and it offers an unusually deep slate of LL.M. specializations.",
            },
            {
                "label": "Public-interest leadership",
                "sentiment": "positive",
                "detail": "The Root-Tilden-Kern Scholarship and extensive clinics make NYU a top destination for public-interest and government careers, not only Big Law.",
            },
            {
                "label": "High cost",
                "sentiment": "caution",
                "detail": "Like its T6 peers, NYU Law's tuition plus NYC living costs are very high; reviewers weigh this against its strong Big-Law and clerkship placement.",
            },
            {
                "label": "Rankings volatility",
                "sentiment": "mixed",
                "detail": "NYU slipped from the top 5 to a tie at No. 9 in the 2024-25 U.S. News methodology change; observers note the ranking is more sensitive to methodology than to any change in the school's strength.",
            },
        ],
        "sources": [
            {
                "label": "NYU School of Law — Employment Data for Recent Graduates (ABA 509)",
                "url": "https://www.law.nyu.edu/careerservices/employmentstatistics",
            },
            {
                "label": "ABA Journal — 2024-25 U.S. News law school rankings (NYU No. 9)",
                "url": "https://www.abajournal.com/web/article/t14-ties-and-shifts-found-in-2024-25-us-news-law-school-list",
            },
            {
                "label": "Times Higher Education — Law subject ranking 2026 (NYU No. 2 worldwide)",
                "url": "https://www.timeshighereducation.com/world-university-rankings/new-york-university",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "nyu-film-television-bfa": {
        "summary": (
            "The Tisch BFA in Film & Television, housed in the Maurice Kanbar Institute of Film & "
            "Television, is widely regarded as one of the world's premier film schools, with NYU "
            "ranked No. 16 globally for arts and humanities by Times Higher Education for 2026 and "
            "a celebrated alumni roster (Martin Scorsese, Spike Lee, Ang Lee, and many others). "
            "Reviewers praise the hands-on conservatory training, the NYC industry access, and the "
            "alumni network, while cautioning that the program is highly competitive, demanding, "
            "and among the most expensive arts educations in the country."
        ),
        "themes": [
            {
                "label": "World-class reputation and alumni",
                "sentiment": "positive",
                "detail": "Tisch is routinely ranked among the very best film schools; its alumni include leading directors, writers, and producers across film and television.",
            },
            {
                "label": "Hands-on conservatory training",
                "sentiment": "positive",
                "detail": "Students make films from their first year within a structured production curriculum, combining studio craft with NYU's liberal-arts breadth.",
            },
            {
                "label": "New York City industry access",
                "sentiment": "positive",
                "detail": "The Greenwich Village setting offers extensive internship, festival, and professional connections in a global media capital.",
            },
            {
                "label": "High cost",
                "sentiment": "caution",
                "detail": "Tisch tuition plus NYC living costs make it one of the most expensive undergraduate arts programs; reviewers urge careful financial planning.",
            },
            {
                "label": "Intense and competitive",
                "sentiment": "mixed",
                "detail": "The workload and competition are significant, and outcomes in the arts depend heavily on individual initiative and the program's network rather than guaranteed placement.",
            },
        ],
        "sources": [
            {
                "label": "NYU Tisch — Maurice Kanbar Institute of Film & Television",
                "url": "https://tisch.nyu.edu/film-tv",
            },
            {
                "label": "Times Higher Education — Arts & Humanities subject ranking 2026 (NYU No. 16)",
                "url": "https://www.timeshighereducation.com/world-university-rankings/new-york-university",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
}
from unipaith.data.nyu_reviews_generated import REVIEWS as _GENERATED_REVIEWS  # noqa: E402

_REVIEWS_BY_SLUG.update(_GENERATED_REVIEWS)

# ── Admissions requirement sets ────────────────────────────────────────────
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission to an on-campus program.",
}
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application (with NYU questions)", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "School counselor recommendation + school report", "required": True},
        {"name": "One teacher recommendation", "required": False},
        {"name": "$80 application fee (fee waivers available)", "required": True},
        {
            "name": "Standardized testing (flexible)",
            "required": False,
            "note": "NYU's flexible testing policy accepts the SAT, ACT, three AP exams, the IB diploma, or certain international exams in lieu of the SAT/ACT.",
        },
    ],
    "deadlines": [
        {"round": "Early Decision I", "date": "November 1"},
        {"round": "Early Decision II", "date": "January 1"},
        {"round": "Regular Decision", "date": "January 5"},
    ],
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "Duolingo English Test", "PTE Academic"],
            "required": False,
            "note": "English-proficiency proof is required for applicants whose first language is not English (waivers apply).",
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "NYU Undergraduate Admissions",
                "url": "https://www.nyu.edu/admissions/undergraduate-admissions.html",
            }
        ],
    },
    "source": "NYU Undergraduate Admissions",
    "source_url": "https://www.nyu.edu/admissions/undergraduate-admissions.html",
}

_REQ_MBA = {
    "materials": [
        {"name": "NYU Stern MBA online application", "required": True},
        {"name": "Required essays", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "One letter of recommendation", "required": True},
        {"name": "Resume", "required": True},
        {
            "name": "GMAT, GRE, or Executive Assessment scores",
            "required": False,
            "note": "Test waivers are available for qualified applicants; the EA is accepted for some programs.",
        },
        {"name": "Interview (by invitation)", "required": False},
    ],
    "deadlines": [
        {"round": "Round 1", "date": "Mid-September"},
        {"round": "Round 2", "date": "November"},
        {"round": "Round 3", "date": "January"},
        {"round": "Round 4", "date": "March"},
    ],
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "PTE"],
            "required": True,
            "note": "Required for applicants whose first language is not English (waivers apply).",
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "NYU Stern — Full-Time MBA Admissions",
                "url": "https://www.stern.nyu.edu/programs-admissions/full-time-mba/admissions",
            }
        ],
    },
    "source": "NYU Stern — Full-Time MBA Admissions",
    "source_url": "https://www.stern.nyu.edu/programs-admissions/full-time-mba/admissions",
}

_REQ_LAW = {
    "materials": [
        {"name": "LSAC application (via the Credential Assembly Service)", "required": True},
        {"name": "Personal statement", "required": True},
        {"name": "Transcripts (CAS report)", "required": True},
        {"name": "Two letters of recommendation", "required": True},
        {"name": "Resume", "required": True},
        {
            "name": "LSAT or GRE scores",
            "required": True,
            "note": "NYU Law accepts either the LSAT or the GRE for J.D. admission.",
        },
    ],
    "deadlines": [
        {"round": "Early Decision", "date": "November 15"},
        {"round": "Regular Decision", "date": "February 15 (rolling; apply early)"},
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
                "label": "NYU School of Law — J.D. Admissions",
                "url": "https://www.law.nyu.edu/jdadmissions",
            }
        ],
    },
    "source": "NYU School of Law — J.D. Admissions",
    "source_url": "https://www.law.nyu.edu/jdadmissions",
}

_REQ_ONLINE = {
    "materials": [
        {"name": "Online program application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Letters of recommendation", "required": True},
        {"name": "Resume / CV", "required": True},
    ],
    "deadlines": [
        {"round": "Fall entry", "date": "Rolling / spring application window"},
    ],
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": True,
            "note": "Required for applicants whose first language is not English.",
        },
        "visa": {"note": "Fully online programs do not sponsor an F-1/J-1 student visa."},
        "sources": [
            {
                "label": "NYU Graduate Admissions",
                "url": "https://www.nyu.edu/admissions/graduate-admissions.html",
            }
        ],
    },
    "source": "NYU — Online program admissions",
    "source_url": "https://www.nyu.edu/admissions/graduate-admissions.html",
}

_REQ_GRAD_GENERIC = {
    "materials": [
        {"name": "Program online application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose / personal statement", "required": True},
        {"name": "Résumé / CV", "required": True},
        {
            "name": "Letters of recommendation",
            "required": True,
            "note": "Most NYU graduate programs require two to three letters; check the program's bulletin page.",
        },
        {
            "name": "GRE scores",
            "required": False,
            "note": "GRE requirements vary by program; many NYU graduate programs are test-optional.",
        },
    ],
    "deadlines": [
        {
            "round": "Fall admission",
            "date": "Deadlines vary by program (typically December–January)",
        },
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
                "label": "NYU Graduate Admissions",
                "url": "https://www.nyu.edu/admissions/graduate-admissions.html",
            }
        ],
    },
    "source": "NYU Graduate Admissions",
    "source_url": "https://www.nyu.edu/admissions/graduate-admissions.html",
}


def _requirements_for(spec: dict) -> dict:
    slug = spec["slug"]
    if spec["degree_type"] == "bachelors":
        return _REQ_UNDERGRAD
    if spec["code"] == "mba":
        return _REQ_MBA
    if slug == "nyu-law-jd":
        return _REQ_LAW
    if spec.get("delivery_format") == "online":
        return _REQ_ONLINE
    return _REQ_GRAD_GENERIC


def _program_standard(slug: str, spec: dict) -> dict:
    """Per-program omitted-field list (verified-unavailable), for _standard."""
    omitted: list[str] = ["tracks", "cost_data.tuition_usd"]
    if slug not in _OUTCOMES_BY_SLUG:
        omitted += [
            "outcomes_data.employment_rate",
            "outcomes_data.median_salary",
            "outcomes_data.top_industries",
            "outcomes_data.conditions",
            "outcomes_data.source",
        ]
    if slug not in _CLASS_PROFILE_BY_SLUG:
        omitted.append("class_profile.cohort_size")
    if slug not in _FACULTY_BY_SLUG:
        omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    # content_sources is set on every program (school channel + program keywords), never omitted.
    return _standard(omitted)


def apply(session: Session) -> bool:
    """Enrich New York University to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when NYU is absent — safe on fresh/CI databases.
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
    inst.founded_year = 1831
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.nyu.edu"
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
    """True if any FK in the schema references this programs row (delete unsafe)."""
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
        p.department = spec.get("department")
        p.duration_months = spec.get("duration_months")
        p.description_text = spec["description"]
        p.website_url = spec["website"]
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "on_campus")
        _kw = _PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(_SCHOOL_FEED_SPEC[spec["school"]])
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
    # Reconcile legacy NYU programs (slug not in the canonical set): delete when unreferenced,
    # otherwise unpublish so the catalog stays clean without breaking any application/match rows.
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
