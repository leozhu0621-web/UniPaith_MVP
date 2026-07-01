"""Georgia Institute of Technology — gold-standard profile data (institution + colleges + program catalog).

Mirrors the MIT / Sloan / MBAn reference instance (see ``mit_profile.py`` /
``rice_profile.py``): every value is researched from an authoritative source and carries a
citation, or is honestly omitted (recorded in that node's ``_standard.omitted``) — never
guessed. Built 2026-06-13 from:

  • U.S. Dept. of Education **College Scorecard** API + **NCES College Navigator** (IPEDS,
    UNITID 139755) — net price, earnings, completion/retention, Pell/loan, median debt,
    undergraduate race/ethnicity, admit rate.
  • Georgia Tech **Common Data Set 2024-25** (Office of Institutional Research & Planning) —
    admissions funnel, test scores, faculty count, student-faculty ratio, tuition & fees.
  • Georgia Tech **Fact Book** + Institute news releases — enrollment, graduation/retention
    milestones (Fall 2024 cohort reporting).
  • Georgia Tech **Career Center / Office of Academic Effectiveness** Career & Salary Survey
    (Career Outcomes Report 2023-24) — median salaries and job-acceptance rates by degree
    level, top employers, employment by industry.
  • Georgia Tech **research enterprise** report (research.gatech.edu) — FY2024 research awards,
    GTRI, the eleven Interdisciplinary Research Institutes (each with its official link).
  • The official **Georgia Tech Catalog** (catalog.gatech.edu, 2025-26 edition) for the seven
    colleges, their deans, and the full published degree catalog (≈143 degree programs); each
    program's catalog page for the degree name and delivery.
  • Rankings: **QS 2026**, **THE 2026**, **U.S. News 2026** (each cited), Carnegie (R1),
    SACSCOC accreditation.
  • Verified third-party reviews for the flagship coverable programs (OMSCS, Online MS
    Analytics, the Scheller Full-Time MBA, and undergraduate Computer Science).

Honest caveats stamped into ``_standard.omitted``: Georgia Tech reports career outcomes by
degree LEVEL (institute-wide median salary + job-acceptance rate for bachelor's / master's /
doctoral graduates), not per individual program, so each program carries the institute-wide
figure for its degree level with the methodology stated verbatim and omits program-specific
industry splits where none is published. Most graduate/professional programs bill tuition per
credit hour and publish no single annual figure, so those carry a sourced "see the program's
tuition page" record rather than a guessed number (OMSCS and Online MS Analytics, which DO
publish a total program cost, carry it). The institute does not publish a single combined
"employed or continuing education" rate, so that institution field is omitted with reason.
De-fabrication (2026-06-18, gatechprof3): the program catalog is re-grounded on first-party
sources. (a) Every program description is now a field-specific overview read off that
program's own page at catalog.gatech.edu/programs/<slug>/ (``georgia_tech_catalog_descriptions``)
— replacing the generated ``"{name} is a … program offered through Georgia Tech's {College}"``
classification stub that was 100% prefix-doubled and 73% classification. (b) ``department`` is
now the real owning GT school/unit (e.g. the Daniel Guggenheim School of Aerospace Engineering,
the H. Milton Stewart School of Industrial and Systems Engineering) rather than the field
echoed from the program name. (c) The ``DEPTH_REVIEWS`` batch (58 machine-synthesized
external_reviews minted one-per-row from program metadata + institution rankings — identical
institution-level themes repeated across the MS/PhD rows under a false "aggregated from public
sources" disclaimer) is REMOVED; a review fabricated-by-synthesis lends a row false third-party
credibility and is worse than an honest blank (SKILL.md miss #8), so those programs now record
``external_reviews`` in ``_standard.omitted``. The structure is clean fleet-wide, so the
structure-before-depth gate now unblocks the reviews DEPTH pass (gatechreviews1): the four
original flagship reviews (OMSCS, Online MS Analytics, the Scheller Full-Time MBA, and
undergraduate Computer Science) are joined by 13 more hand-gathered, program-specific reviews
across the coverable flagship set — BS/MS Industrial Engineering, BS/MS Aerospace Engineering,
BS Biomedical Engineering, MS Mechanical Engineering, MS Electrical & Computer Engineering, MS
Quantitative & Computational Finance, the residential MS in Analytics, the Executive MBA in
Management of Technology, MS Human-Computer Interaction, the Online MS in Cybersecurity, and MS
Supply Chain Engineering. Each summarizes real third-party coverage (U.S. News specialty ranks,
official employment reports, QuantNet, Financial Times, Poets&Quants, OMSCentral course reviews,
College Factual, College Confidential), pairs praise with the common cautions, and cites
resolvable program-specific sources. Programs with no verifiable program-specific third-party
coverage (the residential MSCS and MS-Cybersecurity, MCRP, MS Public Policy, and the research
MS/PhD tail) stay honestly recorded in ``_standard.omitted``, never synthesized. An enforced
anti-stub gate (``test_anti_stub_gate``,
``georgia_tech`` certified) and an anti-synthesis test (``test_georgia_tech_profile``) block any
future stub-swap or one-sweep review mint. Georgia Tech's events calendar
(events.gatech.edu) exposes no verified public iCalendar/RSS feed, so the verified Institute
news RSS (news.gatech.edu, current and image-carrying) feeds the Updates surface and no
events feed is asserted.
"""

# ruff: noqa: E501

from __future__ import annotations

import re
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.georgia_tech_catalog_descriptions import (
    CATALOGUE_DESCRIPTIONS,
    DEPARTMENTS,
)
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Georgia Institute of Technology-Main Campus"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-30"


def _standard(omitted: list[str] | None = None) -> dict:
    """The per-node provenance stamp the routine writes onto every enriched node."""
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }


# Every required institution-level field except the combined placement rate was verified from
# a citable source; GT reports outcomes by degree level, not a single institute-wide
# "employed or continuing education" figure, so that one field is omitted with reason.
_OMITTED_INSTITUTION: list[str] = ["school_outcomes.employed_or_continuing_ed"]

# ── Institution-level data ────────────────────────────────────────────────
RANKING_DATA: dict = {
    "ownership_type": "public",
    "accreditor": "SACSCOC (Southern Association of Colleges and Schools Commission on Colleges)",
    # Carnegie 2025 basic classification (R1).
    "carnegie_classification": (
        "Doctoral Universities: Very High Research Spending and Doctorate Production (R1)"
    ),
    # QS World University Rankings 2026: Georgia Tech is #=123 worldwide.
    "qs_world_university_rankings": {
        "rank": 123,
        "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/georgia-institute-technology",
    },
    # THE World University Rankings 2026: #=41 in the world.
    "times_higher_education": {
        "rank": 41,
        "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/georgia-institute-technology",
    },
    # U.S. News Best Colleges (National Universities) 2026: #32 nationally (#9 public).
    "us_news_national": {
        "rank": 32,
        "year": 2026,
        "source_url": "https://news.gatech.edu/news/2025/09/23/georgia-tech-secures-multiple-no-1-rankings",
    },
}

# school_outcomes is shallow-merged into the existing JSONB. The College Scorecard seed already
# wrote some fields; the sub-objects below fill the verified gaps the conformance check flags
# (funnel, diversity, test scores, retention/grad rate, scale, research, campus life, outcomes,
# cost & aid, location, campus photos, feeds, citations) from authoritative sources.
SCHOOL_OUTCOMES: dict = {
    # College Scorecard (UNITID 139755): first-year retention 98.08%; GT CDS 2024-25 reports
    # 98% for the Fall 2023 cohort.
    "retention_rate_first_year": 0.98,
    # GT news (Nov 2024): six-year graduation rate 94% (Fall 2018 cohort). College Scorecard
    # completion rate at 150% of normal time = 94.02%.
    "graduation_rate_6yr": 0.94,
    "completion_rate_4yr_150pct": 0.9402,
    # College Scorecard / GT CDS C1 (Fall 2024 first-year): 8,413 admits / 59,789 applicants.
    "admit_rate": 0.1407,
    # College Scorecard average annual net price + institution-wide median earnings 10 years
    # after entry (both cited to College Scorecard for UNITID 139755).
    "avg_net_price": 12116,
    "median_earnings_10yr": 102772,
    "financial_aid": {
        # College Scorecard (IPEDS): 13.9% of undergraduates received a Pell grant; 16.97%
        # took federal student loans.
        "pell_grant_rate": 0.139,
        "federal_loan_rate": 0.1697,
        # GT CDS 2024-25 (G1): in-state tuition $10,512 + required fees $1,546 + on-campus food
        # & housing $13,608 ≈ $25,666; College Scorecard academic-year cost of attendance
        # (in-state) = $28,167.
        "cost_of_attendance": 28167,
        # College Scorecard median federal debt of completers.
        "median_debt_completers": 21672,
        "avg_net_price": 12116,
    },
    # Undergraduate race/ethnicity shares (College Scorecard / IPEDS, UNITID 139755).
    "demographics": {
        "white": 0.347,
        "asian": 0.346,
        "hispanic": 0.086,
        "black": 0.083,
        "two_or_more": 0.048,
        "international": 0.080,
        "american_indian": 0.0004,
        "native_hawaiian": 0.0004,
        "unknown": 0.010,
    },
    # SAT/ACT 25th-75th percentiles of enrolled first-years (GT CDS 2024-25, C9). Georgia Tech
    # uses SAT/ACT scores in first-year admission.
    "test_scores": {
        "sat_reading_25_75": [680, 750],
        "sat_math_25_75": [690, 790],
        "act_25_75": [30, 34],
    },
    # GT Career Center / Office of Academic Effectiveness Career & Salary Survey, AY 2023-24:
    # employer industries spanning Georgia Tech graduates' first destinations.
    "top_employer_industries": [
        "Computer & Information Technology",
        "Engineering & Manufacturing",
        "Aerospace",
        "Defense",
        "Consulting",
        "Financial Services & Real Estate",
        "Energy & Utilities",
        "Consumer Products & Retail",
        "Healthcare & Biotechnology",
    ],
    "campus_basics": {"location": "Atlanta, Georgia"},
    # Scale: GT CDS 2024-25 (I-1) total instructional faculty = 1,443 (1,254 FT + 189 PT);
    # (I-2) Fall 2024 student-faculty ratio = 21:1. Research centers = the eleven
    # Interdisciplinary Research Institutes (research.gatech.edu).
    "scale": {
        "faculty_count": 1443,
        "student_faculty_ratio": "21:1",
        "research_centers": 11,
    },
    "location": {"lat": 33.7756, "lng": -84.3963},
    # Research: GT's FY2024 research and sponsored awards were $1.37B (GTRI alone $869M);
    # research is organized under the eleven Interdisciplinary Research Institutes plus GTRI,
    # each with its official link.
    "research": {
        "labs": [
            "Georgia Tech Research Institute (GTRI)",
            "Parker H. Petit Institute for Bioengineering and Bioscience (IBB)",
            "Institute for Data Engineering and Science (IDEaS)",
            "Strategic Energy Institute (SEI)",
            "Georgia Tech Manufacturing Institute (GTMI)",
            "Institute for Matter and Systems (IMS)",
            "Institute for Neuroscience, Neurotechnology, and Society (INNS)",
            "Institute for People and Technology (IPaT)",
            "Renewable Bioproducts Institute (RBI)",
            "Institute for Robotics and Intelligent Machines (IRIM)",
            "Space Research Institute (SRI)",
            "Brook Byers Institute for Sustainable Systems (BBISS)",
        ],
        "areas": [
            "Computing, artificial intelligence, and cybersecurity",
            "Aerospace, defense, and national security (GTRI)",
            "Robotics and intelligent machines",
            "Bioengineering, bioscience, and neurotechnology",
            "Materials, electronics, and nanotechnology",
            "Energy, sustainability, and manufacturing",
        ],
        "lab_links": {
            "Georgia Tech Research Institute (GTRI)": "https://gtri.gatech.edu/",
            "Parker H. Petit Institute for Bioengineering and Bioscience (IBB)": "https://petitinstitute.gatech.edu/",
            "Institute for Data Engineering and Science (IDEaS)": "https://ideas.gatech.edu/",
            "Strategic Energy Institute (SEI)": "https://energy.gatech.edu/",
            "Georgia Tech Manufacturing Institute (GTMI)": "https://manufacturing.gatech.edu/",
            "Institute for Matter and Systems (IMS)": "https://www.materials.gatech.edu/",
            "Institute for Neuroscience, Neurotechnology, and Society (INNS)": "https://neuro.gatech.edu/",
            "Institute for People and Technology (IPaT)": "https://ipat.gatech.edu/",
            "Renewable Bioproducts Institute (RBI)": "https://rbi.gatech.edu/",
            "Institute for Robotics and Intelligent Machines (IRIM)": "https://robotics.gatech.edu/",
            "Space Research Institute (SRI)": "https://space.gatech.edu/",
            "Brook Byers Institute for Sustainable Systems (BBISS)": "https://sustainable.gatech.edu/",
        },
    },
    "campus_life": {
        "athletics_division": "NCAA Division I (Atlantic Coast Conference)",
        "resources": [
            {"name": "Ramblin' Wreck — Georgia Tech Athletics", "url": "https://ramblinwreck.com/"},
            {"name": "Housing and Residence Life", "url": "https://housing.gatech.edu/"},
            {"name": "Campus Recreation Center", "url": "https://crc.gatech.edu/"},
            {"name": "Student Engagement & Well-Being", "url": "https://studentlife.gatech.edu/"},
        ],
    },
    "media_credit": "Wikimedia Commons / Mistercontributer (CC0)",
    "campus_photos": [
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/Tech_Tower_-_June_2024.jpg/1920px-Tech_Tower_-_June_2024.jpg",
            "credit": "Wikimedia Commons / Mistercontributer (CC0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Tech_Green_-_Georgia_Institute_of_Technology.jpg/1920px-Tech_Green_-_Georgia_Institute_of_Technology.jpg",
            "credit": "Wikimedia Commons / Maxicar (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Atlantic_Drive%2C_Georgia_Tech.jpg/1920px-Atlantic_Drive%2C_Georgia_Tech.jpg",
            "credit": "Wikimedia Commons / JJonahJackalope (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/Harrison_Square%2C_Georgia_Tech.jpg/1920px-Harrison_Square%2C_Georgia_Tech.jpg",
            "credit": "Wikimedia Commons / JJonahJackalope (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/4/47/Tech_Tower_and_One_Coca-Cola_Plaza.jpg",
            "credit": "Wikimedia Commons / JJonahJackalope (CC BY-SA 4.0)",
        },
    ],
    "flagship": {
        # GT news (Nov 2024): Fall 2024 total degree-seeking enrollment 51,433 (18,785
        # undergraduates).
        "enrollment_total": 51433,
        # GT Common Data Set 2024-25 (C1), first-time first-year, Fall 2024.
        "applicants": 59789,
        "admits": 8413,
        "admissions_cycle": "First-year, Fall 2024 (Georgia Tech Common Data Set 2024-25)",
        # Founded as the Georgia School of Technology by act of the Georgia legislature,
        # October 13, 1885; opened to students in 1888.
        "founded_year": 1885,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Georgia Tech, UNITID 139755)",
            "url": "https://collegescorecard.ed.gov/school/?139755-Georgia-Institute-of-Technology-Main-Campus",
        },
        {
            "label": "NCES College Navigator — Georgia Institute of Technology (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=139755",
        },
        {
            "label": "Georgia Tech — Common Data Set 2024-25 (Institutional Research & Planning)",
            "url": "https://irp.gatech.edu/files/CDS/CDS_2024-2025_FINAL_20FEB2025.pdf",
        },
        {
            "label": "Georgia Tech — Enrollment, Graduation, and Retention milestones (News Center)",
            "url": "https://news.gatech.edu/news/2024/11/12/georgia-tech-reaches-new-milestones-enrollment-graduation-and-retention-rates",
        },
        {
            "label": "Georgia Tech Career Center — Career & Salary Outcomes Report 2023-24",
            "url": "https://academiceffectiveness.gatech.edu/surveys/reports/georgia-tech-career-survey-report-ay-2024-2025",
        },
        {
            "label": "Georgia Tech — Research enterprise / Interdisciplinary Research Institutes",
            "url": "https://research.gatech.edu/interdisciplinary-research-institutes",
        },
        {
            "label": "Carnegie Classifications — Georgia Institute of Technology (R1)",
            "url": "https://carnegieclassifications.acenet.edu/institution/georgia-institute-of-technology/",
        },
        {
            "label": "QS World University Rankings 2026 — Georgia Institute of Technology (#=123)",
            "url": "https://www.topuniversities.com/universities/georgia-institute-technology",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — Georgia Tech (#=41)",
            "url": "https://www.timeshighereducation.com/world-university-rankings/georgia-institute-technology",
        },
        {
            "label": "U.S. News Best Colleges 2026 — Georgia Tech (#32 National, #9 public)",
            "url": "https://news.gatech.edu/news/2025/09/23/georgia-tech-secures-multiple-no-1-rankings",
        },
        {
            "label": "Georgia Tech Catalog 2025-26 — Colleges and Schools",
            "url": "https://catalog.gatech.edu/colleges/",
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it "Undergraduates"); the
# total degree-seeking enrollment (51,433) lives in flagship.enrollment_total.
UNDERGRAD_COUNT = 18785

DESCRIPTION = (
    "Georgia Institute of Technology is a public research university in Atlanta, Georgia. "
    "Founded by an act of the Georgia legislature in 1885 as the Georgia School of Technology "
    "and opened to students in 1888, Georgia Tech is a unit of the University System of "
    "Georgia and one of the nation's leading technological universities. Its 400-acre campus "
    "sits in Midtown Atlanta, anchored by the landmark Tech Tower, and enrolls roughly 18,800 "
    "undergraduates and more than 32,000 graduate and professional students — about 51,000 "
    "degree-seeking students in all — with a 21:1 student-faculty ratio.\n\n"
    "Georgia Tech is organized into seven colleges: the College of Computing, the College of "
    "Engineering, the College of Sciences, the College of Design, the Ivan Allen College of "
    "Liberal Arts, the Scheller College of Business, and the College of Lifetime Learning. "
    "Together they award some 143 degree programs across the bachelor's, master's, and "
    "doctoral levels, including a celebrated portfolio of low-cost, at-scale online master's "
    "degrees — the Online MS in Computer Science (OMSCS), the Online MS in Analytics, and an "
    "online MS in Cybersecurity — delivered through Georgia Tech Professional Education.\n\n"
    "A Carnegie R1 university accredited by SACSCOC, Georgia Tech ranks among the strongest "
    "research universities in the country: No. 32 among national universities (and No. 9 "
    "among public universities) by U.S. News, No. 41 in the world by Times Higher Education, "
    "and No. 123 by QS. Its engineering and computing programs are perennially ranked in the "
    "national top ten. The Institute admitted about 14% of first-year applicants for Fall "
    "2024.\n\n"
    "Georgia Tech's research enterprise drew $1.37 billion in research and sponsored awards in "
    "fiscal year 2024 — the Georgia Tech Research Institute (GTRI) alone accounting for $869 "
    "million — and is organized under eleven Interdisciplinary Research Institutes. The "
    "Institute's average net price is about $12,000 a year against an in-state cost of "
    "attendance near $28,000, and the median federal debt of completers is about $21,700. "
    "Georgia Tech graduates earn a median of roughly $103,000 ten years after entry, among the "
    "highest of any U.S. university. The Yellow Jackets compete in NCAA Division I (the "
    "Atlantic Coast Conference)."
)

# ── The seven colleges (display order) ─────────────────────────────────────
_COC = "College of Computing"
_COE = "College of Engineering"
_COS = "College of Sciences"
_COD = "College of Design"
_IAC = "Ivan Allen College of Liberal Arts"
_SCB = "Scheller College of Business"
_COLL = "College of Lifetime Learning"

SCHOOLS: list[dict] = [
    {
        "name": _COC,
        "sort_order": 1,
        "description": (
            "The College of Computing is a national leader in computer science research and "
            "education, organized into the School of Computer Science, the School of "
            "Interactive Computing, the School of Computational Science and Engineering, and "
            "the School of Cybersecurity and Privacy. It awards undergraduate degrees in "
            "computer science and computational media, research master's and Ph.D. degrees, "
            "and Georgia Tech's at-scale Online MS in Computer Science (OMSCS)."
        ),
    },
    {
        "name": _COE,
        "sort_order": 2,
        "description": (
            "The College of Engineering is the largest college at Georgia Tech and one of the "
            "largest and top-ranked engineering programs in the United States. Across eight "
            "schools — from aerospace, biomedical, civil and environmental, and mechanical "
            "engineering to the H. Milton Stewart School of Industrial and Systems Engineering "
            "— it awards bachelor's, master's, and doctoral degrees and a slate of "
            "professional and online master's programs."
        ),
    },
    {
        "name": _COS,
        "sort_order": 3,
        "description": (
            "The College of Sciences advances discovery across the natural and mathematical "
            "sciences through six schools: Biological Sciences; Chemistry and Biochemistry; "
            "Earth and Atmospheric Sciences; Mathematics; Physics; and Psychology. It awards "
            "undergraduate majors and research master's and Ph.D. degrees, and anchors "
            "interdisciplinary doctoral programs in bioinformatics, quantitative biosciences, "
            "and ocean science and engineering."
        ),
    },
    {
        "name": _COD,
        "sort_order": 4,
        "description": (
            "The College of Design (formerly the College of Architecture) explores the "
            "intersection of design and technology across its schools of Architecture; "
            "Building Construction; City and Regional Planning; Industrial Design; and Music. "
            "It awards the Bachelor of Science, Master of Architecture, Master of Industrial "
            "Design, professional master's degrees, and Ph.D. degrees."
        ),
    },
    {
        "name": _IAC,
        "sort_order": 5,
        "description": (
            "The Ivan Allen College of Liberal Arts brings the humanities and social sciences "
            "to a technological university through schools spanning economics; history and "
            "sociology; literature, media, and communication; modern languages; public "
            "policy; and the Sam Nunn School of International Affairs. It awards undergraduate "
            "majors and master's and Ph.D. degrees, often at the interface of policy, "
            "technology, and society."
        ),
    },
    {
        "name": _SCB,
        "sort_order": 6,
        "description": (
            "The Scheller College of Business educates leaders at the intersection of "
            "business and technology. Located in Atlanta's Tech Square, it offers the "
            "Bachelor of Science in Business Administration, Full-Time, Evening, and Executive "
            "MBA programs, the interdisciplinary MS in Analytics and MS in Quantitative and "
            "Computational Finance, an MS in Management, and a Ph.D. in Management."
        ),
    },
    {
        "name": _COLL,
        "sort_order": 7,
        "description": (
            "The College of Lifetime Learning, established in 2024, is Georgia Tech's newest "
            "college and amplifies learning as a lifelong pursuit. It comprises Georgia Tech "
            "Professional Education (GTPE), the Center for 21st Century Universities (C21U), "
            "and the Center for Education Integrating Science, Mathematics and Computing "
            "(CEISMC), and includes Georgia Tech-Savannah; GTPE delivers the Institute's "
            "at-scale online master's degrees and professional and executive education."
        ),
    },
]

_SCHOOL_WEBSITE: dict[str, str] = {
    _COC: "https://www.cc.gatech.edu/",
    _COE: "https://coe.gatech.edu/",
    _COS: "https://cos.gatech.edu/",
    _COD: "https://design.gatech.edu/",
    _IAC: "https://iac.gatech.edu/",
    _SCB: "https://www.scheller.gatech.edu/",
    _COLL: "https://lifetimelearning.gatech.edu/",
}

# Per-college about_detail (founded, leadership/dean, research centers, named_for, source).
# Deans verified from the Georgia Tech Catalog Deans page (2025-26). Notable named faculty are
# listed only where a current named distinction was verified from an official page; otherwise
# about_detail.faculty is omitted (recorded in _ABOUT_OMITTED), never guessed.
_ABOUT_DETAIL: dict[str, dict] = {
    _COC: {
        "founded": 1990,
        "leadership": "Vivek Sarkar — John P. Imlay, Jr. Dean's Chair, College of Computing",
        "research_centers": [
            "School of Computer Science",
            "School of Interactive Computing",
            "School of Computational Science and Engineering",
            "School of Cybersecurity and Privacy",
            "Institute for Data Engineering and Science (IDEaS)",
            "Institute for Robotics and Intelligent Machines (IRIM)",
        ],
        "source": {
            "label": "Georgia Tech Catalog — College of Computing",
            "url": "https://catalog.gatech.edu/colleges/computing/",
        },
    },
    _COE: {
        "founded": 1896,
        "leadership": "Doug Williams — Interim Dean, College of Engineering",
        "research_centers": [
            "Daniel Guggenheim School of Aerospace Engineering",
            "Wallace H. Coulter Department of Biomedical Engineering (joint with Emory)",
            "School of Chemical and Biomolecular Engineering",
            "School of Civil and Environmental Engineering",
            "School of Electrical and Computer Engineering",
            "H. Milton Stewart School of Industrial and Systems Engineering",
            "George W. Woodruff School of Mechanical Engineering",
            "School of Materials Science and Engineering",
        ],
        "source": {
            "label": "Georgia Tech Catalog — College of Engineering",
            "url": "https://catalog.gatech.edu/colleges/coe/",
        },
    },
    _COS: {
        "leadership": (
            "Susan Lozier — Betsy Middleton and John Clark Sutherland Dean's Chair, College of "
            "Sciences"
        ),
        "research_centers": [
            "School of Biological Sciences",
            "School of Chemistry and Biochemistry",
            "School of Earth and Atmospheric Sciences",
            "School of Mathematics",
            "School of Physics",
            "School of Psychology",
        ],
        "source": {
            "label": "Georgia Tech Catalog — College of Sciences",
            "url": "https://catalog.gatech.edu/colleges/cos/",
        },
    },
    _COD: {
        "leadership": "Ellen M. Bassett — John Portman Dean's Chair, College of Design",
        "research_centers": [
            "School of Architecture",
            "School of Building Construction",
            "School of City and Regional Planning",
            "School of Industrial Design",
            "School of Music",
        ],
        "named_for": (
            "Renamed the College of Design in 2017 (formerly the College of Architecture) to "
            "reflect its expanded scope across design disciplines"
        ),
        "source": {
            "label": "Georgia Tech College of Design — About",
            "url": "https://design.gatech.edu/",
        },
    },
    _IAC: {
        "founded": 1990,
        "leadership": "Amanda Murdie — Ivan Allen, Jr. Dean's Chair, Ivan Allen College of Liberal Arts",
        "research_centers": [
            "School of Economics",
            "School of History and Sociology",
            "School of Literature, Media, and Communication",
            "School of Modern Languages",
            "School of Public Policy",
            "Sam Nunn School of International Affairs",
        ],
        "named_for": (
            "Named for Ivan Allen Jr., the Atlanta mayor (1962-70) and civic leader, whose "
            "family foundation endowed the college"
        ),
        "source": {
            "label": "Georgia Tech Catalog — Ivan Allen College of Liberal Arts",
            "url": "https://catalog.gatech.edu/colleges/cola/",
        },
    },
    _SCB: {
        "leadership": "Anuj Mehrotra — Stephen P. Zelnak, Jr. Dean's Chair, Scheller College of Business",
        "research_centers": [
            "Jones MBA Career Center",
            "Institute for Leadership and Social Impact",
            "Ernest Scheller Jr. Institute for ENGAGE Entrepreneurship",
            "Business Analytics Center",
        ],
        "named_for": (
            "Named in 2009 for Ernest Scheller Jr., a 1952 Georgia Tech graduate, following his "
            "endowment gift"
        ),
        "source": {
            "label": "Georgia Tech Catalog — Scheller College of Business",
            "url": "https://catalog.gatech.edu/colleges/business/",
        },
    },
    _COLL: {
        "founded": 2024,
        "leadership": "William Gaudelli — Inaugural Dean, College of Lifetime Learning",
        "research_centers": [
            "Georgia Tech Professional Education (GTPE)",
            "Center for 21st Century Universities (C21U)",
            "Center for Education Integrating Science, Mathematics and Computing (CEISMC)",
            "Georgia Tech-Savannah",
        ],
        "source": {
            "label": "Georgia Tech College of Lifetime Learning — Dean William Gaudelli",
            "url": "https://lifetimelearning.gatech.edu/william-gaudelli",
        },
    },
}

# Per-college honestly-omitted about_detail fields (verified-unavailable), for _standard.
_ABOUT_OMITTED: dict[str, list[str]] = {
    _COC: ["about_detail.named_for", "about_detail.faculty"],
    _COE: ["about_detail.named_for", "about_detail.faculty"],
    # The College of Sciences' official pages give no single founding year and no honorific
    # name, and list faculty by school without naming current prize chairs at the college level.
    _COS: ["about_detail.founded", "about_detail.named_for", "about_detail.faculty"],
    _COD: ["about_detail.founded", "about_detail.faculty"],
    _IAC: ["about_detail.faculty"],
    _SCB: ["about_detail.founded", "about_detail.faculty"],
    _COLL: ["about_detail.named_for", "about_detail.faculty"],
}

# ── Feeds (content_sources) ────────────────────────────────────────────────
# The daily content-ingest reads news_rss (RSS), keywords (a word-boundary relevance filter)
# and news_curated (keep every item). Georgia Tech's Institute news site exposes a verified
# editorial RSS feed (news.gatech.edu/rss/all — current, image-carrying, HTTP 200 verified
# 2026-06-13) that feeds the Updates surface. The events calendar (events.gatech.edu) is a
# JavaScript application with no verified public iCalendar/RSS endpoint, so no events feed is
# asserted (events would be fabricated otherwise).
_GT_NEWS_RSS = "https://news.gatech.edu/rss/all"
_GT_NEWS_URL = "https://news.gatech.edu"

# Official university social handles (gatech.edu site footer, verified 2026-06-13).
_SOCIAL_GT = {
    "instagram": "https://www.instagram.com/georgiatech/",
    "linkedin": "https://www.linkedin.com/school/georgia-institute-of-technology/",
    "x": "https://x.com/georgiatech",
    "youtube": "https://www.youtube.com/channel/UCFkaWOGpyFBVRf5jEeD_wrA",
    "facebook": "https://www.facebook.com/georgiatech",
}

# Per-college feed config: the shared GT news RSS + keywords that identify the college's items
# in the shared feed (the MIT/MBAn pattern). GT publishes no per-college editorial RSS, so the
# shared Institute feed is keyword-filtered per college.
_SCHOOL_FEED_SPEC: dict[str, dict] = {
    _COC: {"keywords": ["College of Computing", "computer science", "OMSCS", "cybersecurity"]},
    _COE: {"keywords": ["College of Engineering", "engineering", "GTRI"]},
    _COS: {"keywords": ["College of Sciences", "physics", "chemistry", "biology", "mathematics"]},
    _COD: {"keywords": ["College of Design", "architecture", "city planning", "industrial design"]},
    _IAC: {
        "keywords": ["Ivan Allen College", "liberal arts", "public policy", "international affairs"]
    },
    _SCB: {"keywords": ["Scheller", "MBA", "business analytics", "Tech Square"]},
    _COLL: {"keywords": ["Lifetime Learning", "Professional Education", "GTPE", "online learning"]},
}


def _school_content(name: str) -> dict:
    """Build a college's content_sources from the shared GT news RSS + keywords + socials."""
    spec = _SCHOOL_FEED_SPEC[name]
    return {
        "news_rss": _GT_NEWS_RSS,
        "news_url": _SCHOOL_WEBSITE.get(name, _GT_NEWS_URL),
        "news_curated": False,
        "keywords": list(spec["keywords"]),
        "social": _SOCIAL_GT,
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    """Build a program's content_sources from its college feed, refined by program keywords."""
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


# Institution-wide feed: the verified GT news RSS (curated — every item is official Institute
# content) with the official university social handles.
_INSTITUTION_CONTENT: dict = {
    "news_rss": _GT_NEWS_RSS,
    "news_url": _GT_NEWS_URL,
    "news_curated": True,
    "social": _SOCIAL_GT,
}

# ── The program catalog (real degrees, organized by college) ───────────────
# Every program below is a published degree on the official Georgia Tech Catalog
# (catalog.gatech.edu, 2025-26 edition). Minors and embedded/stand-alone certificates are not
# included (they are not degree programs). The three at-scale online master's degrees (OMSCS,
# Online MS Analytics, Online MS Cybersecurity) are added as distinct online-delivery programs
# alongside their residential counterparts.

_FLAGSHIP = "gatech-online-ms-computer-science-omscs"

# Catalog specs: (slug, college, delivery_format). program_name / degree_type / department are
# derived from the slug (with the explicit overrides below).
_CATALOG: list[tuple[str, str, str]] = [
    # ── College of Computing ──
    ("computer-science-bs", _COC, "in_person"),
    ("computational-media-bs", _COC, "in_person"),
    ("computer-science-ms", _COC, "in_person"),
    ("cybersecurity-ms", _COC, "in_person"),
    ("human-computer-interaction-ms", _COC, "in_person"),
    ("bioinformatics-ms", _COC, "in_person"),
    ("computational-science-engineering-ms", _COC, "in_person"),
    ("robotics-ms", _COC, "in_person"),
    ("computer-science-phd", _COC, "in_person"),
    ("human-centered-computing-phd", _COC, "in_person"),
    ("machine-learning-phd", _COC, "in_person"),
    ("computational-science-engineering-phd", _COC, "in_person"),
    ("bioinformatics-phd", _COC, "in_person"),
    ("robotics-phd", _COC, "in_person"),
    ("algorithms-combinatorics-optimization-phd", _COC, "in_person"),
    # ── College of Engineering ──
    ("aerospace-engineering-bs", _COE, "in_person"),
    ("biomedical-engineering-bs", _COE, "in_person"),
    ("chemical-biomolecular-bs", _COE, "in_person"),
    ("civil-engineering-bs", _COE, "in_person"),
    ("computer-engineering-bs", _COE, "in_person"),
    ("electrical-engineering-bs", _COE, "in_person"),
    ("environmental-engineering-bs", _COE, "in_person"),
    ("industrial-engineering-bs", _COE, "in_person"),
    ("materials-science-bs", _COE, "in_person"),
    ("mechanical-engineering-bs", _COE, "in_person"),
    ("nuclear-radiological-bs", _COE, "in_person"),
    ("aerospace-engineering-ms", _COE, "in_person"),
    ("bioengineering-ms", _COE, "in_person"),
    ("biomedical-engineering-ms", _COE, "in_person"),
    ("chemical-engineering-ms", _COE, "in_person"),
    ("civil-engineering-ms", _COE, "in_person"),
    ("electrical-computer-engineering-ms", _COE, "in_person"),
    ("engineering-science-mechanics-ms", _COE, "in_person"),
    ("environmental-engineering-ms", _COE, "in_person"),
    ("health-systems-ms", _COE, "in_person"),
    ("industrial-engineering-ms", _COE, "in_person"),
    ("materials-science-engineering-ms", _COE, "in_person"),
    ("mechanical-engineering-ms", _COE, "in_person"),
    ("mechanical-engineering-undesignated-ms", _COE, "in_person"),
    ("medical-physics-ms", _COE, "in_person"),
    ("nuclear-engineering-ms", _COE, "in_person"),
    ("operations-research-ms", _COE, "in_person"),
    ("statistics-ms", _COE, "in_person"),
    ("supply-chain-engineering-ms", _COE, "in_person"),
    ("applied-systems-engineering-pmase", _COE, "hybrid"),
    ("manufacturing-leadership-pmml", _COE, "hybrid"),
    ("aerospace-engineering-phd", _COE, "in_person"),
    ("bioengineering-phd", _COE, "in_person"),
    ("biomedical-engineering-phd", _COE, "in_person"),
    ("chemical-engineering-phd", _COE, "in_person"),
    ("civil-engineering-phd", _COE, "in_person"),
    ("electrical-computer-engineering-phd", _COE, "in_person"),
    ("engineering-science-mechanics-phd", _COE, "in_person"),
    ("environmental-engineering-phd", _COE, "in_person"),
    ("industrial-engineering-phd", _COE, "in_person"),
    ("materials-science-phd", _COE, "in_person"),
    ("mechanical-engineering-phd", _COE, "in_person"),
    ("nuclear-engineering-phd", _COE, "in_person"),
    ("operations-research-phd", _COE, "in_person"),
    # ── College of Sciences ──
    ("applied-physics-bs", _COS, "in_person"),
    ("astrophysics-bs", _COS, "in_person"),
    ("atmospheric-oceanic-sciences-bs", _COS, "in_person"),
    ("biochemistry-bs", _COS, "in_person"),
    ("biology-bs", _COS, "in_person"),
    ("chemistry-bs", _COS, "in_person"),
    ("environmental-science-bs", _COS, "in_person"),
    ("mathematics-bs", _COS, "in_person"),
    ("mathematics-computing-bs", _COS, "in_person"),
    ("neuroscience-bs", _COS, "in_person"),
    ("physics-bs", _COS, "in_person"),
    ("psychology-bs", _COS, "in_person"),
    ("solid-earth-planetary-sciences-bs", _COS, "in_person"),
    ("biology-ms", _COS, "in_person"),
    ("chemistry-ms", _COS, "in_person"),
    ("earth-atmospheric-sciences-ms", _COS, "in_person"),
    ("mathematics-ms", _COS, "in_person"),
    ("physics-ms", _COS, "in_person"),
    ("psychology-ms", _COS, "in_person"),
    ("statistics-ms", _COS, "in_person"),
    ("applied-physiology-phd", _COS, "in_person"),
    ("biology-phd", _COS, "in_person"),
    ("chemistry-phd", _COS, "in_person"),
    ("earth-atmospheric-sciences-phd", _COS, "in_person"),
    ("mathematics-phd", _COS, "in_person"),
    ("ocean-science-engineering-phd", _COS, "in_person"),
    ("physics-phd", _COS, "in_person"),
    ("psychology-phd", _COS, "in_person"),
    ("quantitative-biosciences-phd", _COS, "in_person"),
    # ── College of Design ──
    ("arts-entertainment-creative-technologies-bs", _COD, "in_person"),
    ("construction-science-and-management-bs", _COD, "in_person"),
    ("industrial-design-bs", _COD, "in_person"),
    ("music-technology-bs", _COD, "in_person"),
    ("urban-planning-and-spatial-analytics-bs", _COD, "in_person"),
    ("architecture-ms", _COD, "in_person"),
    ("march", _COD, "in_person"),
    ("masters-industrial-design", _COD, "in_person"),
    ("building-construction-facility-management-ms", _COD, "in_person"),
    ("gist-ms", _COD, "in_person"),
    ("mcrp", _COD, "in_person"),
    ("urban-analytics-ms", _COD, "in_person"),
    ("urban-design-msud", _COD, "in_person"),
    ("music-technology-ms", _COD, "in_person"),
    ("master-real-estate-development", _COD, "in_person"),
    ("occupational-safety-health-pmosh", _COD, "hybrid"),
    ("architecture-phd", _COD, "in_person"),
    ("building-construction-phd", _COD, "in_person"),
    ("city-regional-planning-phd", _COD, "in_person"),
    ("music-technology-phd", _COD, "in_person"),
    # ── Ivan Allen College of Liberal Arts ──
    ("applied-language-intercultural-studies-bs", _IAC, "in_person"),
    ("economics-bs", _IAC, "in_person"),
    ("economics-international-affairs-bs", _IAC, "in_person"),
    ("global-economics-modern-languages-bs", _IAC, "in_person"),
    ("history-technology-society-bs", _IAC, "in_person"),
    ("international-affairs-bs", _IAC, "in_person"),
    ("international-affairs-modern-language-bs", _IAC, "in_person"),
    ("literature-media-communication-bs", _IAC, "in_person"),
    ("public-policy-bs", _IAC, "in_person"),
    ("applied-languages-intercultural-studies-ms", _IAC, "in_person"),
    ("digital-media-ms", _IAC, "in_person"),
    ("economics-ms", _IAC, "in_person"),
    ("global-development-ms", _IAC, "in_person"),
    ("global-media-cultures-ms", _IAC, "in_person"),
    ("history-sociology-technology-science-ms", _IAC, "in_person"),
    ("international-affairs-ms", _IAC, "in_person"),
    ("international-affairs-science-technology-ms", _IAC, "in_person"),
    ("international-security-ms", _IAC, "in_person"),
    ("master-sustainable-energy-environmental-management", _IAC, "in_person"),
    ("public-policy-ms", _IAC, "in_person"),
    ("digital-media-phd", _IAC, "in_person"),
    ("economics-phd", _IAC, "in_person"),
    ("history-sociology-technology-science-phd", _IAC, "in_person"),
    ("international-affairs-science-technology-phd", _IAC, "in_person"),
    ("public-policy-phd", _IAC, "in_person"),
    # ── Scheller College of Business ──
    ("business-administration-bs", _SCB, "in_person"),
    ("mba", _SCB, "in_person"),
    ("mba-global-business-executive", _SCB, "hybrid"),
    ("mba-management-technology-executive", _SCB, "hybrid"),
    ("analytics-ms", _SCB, "in_person"),
    ("management-ms", _SCB, "in_person"),
    ("quantitative-computational-finance-ms", _SCB, "in_person"),
    ("management-phd", _SCB, "in_person"),
    # ── At-scale online master's degrees (delivered via GTPE) ──
    ("online-ms-computer-science-omscs", _COC, "online"),
    ("online-ms-analytics", _SCB, "online"),
    ("online-ms-cybersecurity", _COC, "online"),
]

# Slug → field-name override (for fields whose title-cased slug would be wrong/awkward).
_FIELD_OVERRIDE: dict[str, str] = {
    "electrical-computer-engineering": "Electrical and Computer Engineering",
    "algorithms-combinatorics-optimization": "Algorithms, Combinatorics, and Optimization",
    "computational-science-engineering": "Computational Science and Engineering",
    "human-computer-interaction": "Human-Computer Interaction",
    "human-centered-computing": "Human-Centered Computing",
    "earth-atmospheric-sciences": "Earth and Atmospheric Sciences",
    "atmospheric-oceanic-sciences": "Atmospheric and Oceanic Sciences",
    "solid-earth-planetary-sciences": "Solid Earth and Planetary Sciences",
    "quantitative-computational-finance": "Quantitative and Computational Finance",
    "engineering-science-mechanics": "Engineering Science and Mechanics",
    "materials-science": "Materials Science and Engineering",
    "materials-science-engineering": "Materials Science and Engineering",
    "supply-chain-engineering": "Supply Chain Engineering",
    "nuclear-radiological": "Nuclear and Radiological Engineering",
    "chemical-biomolecular": "Chemical and Biomolecular Engineering",
    "literature-media-communication": "Literature, Media, and Communication",
    "history-technology-society": "History, Technology, and Society",
    "history-sociology-technology-science": "History and Sociology of Technology and Science",
    "international-affairs-modern-language": "International Affairs and Modern Language",
    "international-affairs-science-technology": "International Affairs, Science, and Technology",
    "applied-language-intercultural-studies": "Applied Languages and Intercultural Studies",
    "applied-languages-intercultural-studies": "Applied Languages and Intercultural Studies",
    "global-economics-modern-languages": "Global Economics and Modern Languages",
    "economics-international-affairs": "Economics and International Affairs",
    "arts-entertainment-creative-technologies": "Arts, Entertainment, and Creative Technologies",
    "construction-science-and-management": "Construction Science and Management",
    "building-construction-facility-management": "Building Construction and Facility Management",
    "building-construction": "Building Construction",
    "urban-planning-and-spatial-analytics": "Urban Planning and Spatial Analytics",
    "neuroscience-neurotechnology": "Neuroscience and Neurotechnology",
    "ocean-science-engineering": "Ocean Science and Engineering",
    "city-regional-planning": "City and Regional Planning",
    "mathematics-computing": "Mathematics and Computing",
    "global-media-cultures": "Global Media and Cultures",
}

# Slug → (program_name, degree_type, department) for degrees whose name does not follow the
# regular "<Degree> in <Field>" pattern.
_SPECIAL: dict[str, tuple[str, str, str]] = {
    "march": ("Master of Architecture", "masters", "Architecture"),
    "mcrp": ("Master of City and Regional Planning", "masters", "City and Regional Planning"),
    "masters-industrial-design": ("Master of Industrial Design", "masters", "Industrial Design"),
    "urban-design-msud": ("Master of Science in Urban Design", "masters", "Urban Design"),
    "gist-ms": (
        "Master of Science in Geographic Information Science and Technology",
        "masters",
        "Geographic Information Science and Technology",
    ),
    "master-real-estate-development": (
        "Master of Real Estate Development",
        "professional",
        "Real Estate Development",
    ),
    "master-sustainable-energy-environmental-management": (
        "Master of Sustainable Energy and Environmental Management",
        "professional",
        "Sustainable Energy and Environmental Management",
    ),
    "applied-systems-engineering-pmase": (
        "Professional Master's in Applied Systems Engineering",
        "professional",
        "Applied Systems Engineering",
    ),
    "manufacturing-leadership-pmml": (
        "Professional Master's in Manufacturing Leadership",
        "professional",
        "Manufacturing Leadership",
    ),
    "occupational-safety-health-pmosh": (
        "Professional Master's in Occupational Safety and Health",
        "professional",
        "Occupational Safety and Health",
    ),
    "mba": (
        "Master of Business Administration (Full-Time)",
        "professional",
        "Business Administration",
    ),
    "mba-global-business-executive": (
        "Executive MBA in Global Business",
        "professional",
        "Business Administration",
    ),
    "mba-management-technology-executive": (
        "Executive MBA in Management of Technology",
        "professional",
        "Business Administration",
    ),
    "management-ms": ("Master of Science in Management", "masters", "Management"),
    "mechanical-engineering-undesignated-ms": (
        "Master of Science in Mechanical Engineering (Undesignated)",
        "masters",
        "Mechanical Engineering",
    ),
    "online-ms-computer-science-omscs": (
        "Online Master of Science in Computer Science (OMSCS)",
        "masters",
        "Computer Science",
    ),
    "online-ms-analytics": (
        "Online Master of Science in Analytics (OMS Analytics)",
        "masters",
        "Analytics",
    ),
    "online-ms-cybersecurity": (
        "Online Master of Science in Cybersecurity",
        "masters",
        "Cybersecurity",
    ),
}

_DEGREE_WORD = {"bs": "bachelors", "ms": "masters", "phd": "phd"}
_DEGREE_PREFIX = {
    "bachelors": "Bachelor of Science in",
    "masters": "Master of Science in",
    "phd": "Doctor of Philosophy in",
}


def _slugify(name: str) -> str:
    s = name.lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _field_name(base: str) -> str:
    if base in _FIELD_OVERRIDE:
        return _FIELD_OVERRIDE[base]
    return " ".join(w.capitalize() for w in base.split("-"))


def _derive(slug: str) -> tuple[str, str, str]:
    """Return (program_name, degree_type, department) for a catalog slug."""
    if slug in _SPECIAL:
        return _SPECIAL[slug]
    for suffix, dtype in _DEGREE_WORD.items():
        if slug.endswith(f"-{suffix}"):
            base = slug[: -(len(suffix) + 1)]
            field = _field_name(base)
            return f"{_DEGREE_PREFIX[dtype]} {field}", dtype, field
    # Should not happen — every catalog slug is special or suffixed.
    field = _field_name(slug)
    return field, "masters", field


# Matcher-core CIP-2020 code per program (REPAIR_BACKLOG #1 — cip_code starvation).
# `cip_code` is the CIP join key the CPEF matcher uses to resolve a program's field to
# `ref_majors` + the field-66 interest vocabulary, so a null catalog is scored field-blind.
# Every code below is a verified NCES CIP-2020 six-digit code (NN.NNNN) that (a) is the
# canonical code for that field, (b) exists in data/reference/ref_majors.jsonl (the matcher
# join target), and (c) sits within a CIP-4 family Georgia Tech actually reports to IPEDS,
# cross-checked against the U.S. Dept. of Education College Scorecard field-of-study list
# for UNITID 139755 (api.data.gov collegescorecard latest.programs.cip_4_digit). Never a
# guess; a genuinely uncodeable program would be recorded in _standard.omitted. Keyed on the
# catalog slug (the raw _CATALOG slug, without the "gatech-" prefix).
_CIP_BY_SLUG: dict[str, str] = {
    # ── College of Computing ──
    "computer-science-bs": "11.0701",
    "computer-science-ms": "11.0701",
    "computer-science-phd": "11.0701",
    "computational-media-bs": "11.0801",
    "cybersecurity-ms": "11.1003",
    "human-computer-interaction-ms": "11.0105",
    "bioinformatics-ms": "26.1103",
    "bioinformatics-phd": "26.1103",
    "computational-science-engineering-ms": "11.0101",
    "computational-science-engineering-phd": "11.0101",
    "robotics-ms": "14.4201",
    "robotics-phd": "14.4201",
    "human-centered-computing-phd": "11.0105",
    "machine-learning-phd": "11.0102",
    "algorithms-combinatorics-optimization-phd": "27.0301",
    # ── College of Engineering ──
    "aerospace-engineering-bs": "14.0201",
    "aerospace-engineering-ms": "14.0201",
    "aerospace-engineering-phd": "14.0201",
    "biomedical-engineering-bs": "14.0501",
    "biomedical-engineering-ms": "14.0501",
    "biomedical-engineering-phd": "14.0501",
    "bioengineering-ms": "14.0501",
    "bioengineering-phd": "14.0501",
    "chemical-biomolecular-bs": "14.0702",
    "chemical-engineering-ms": "14.0701",
    "chemical-engineering-phd": "14.0701",
    "civil-engineering-bs": "14.0801",
    "civil-engineering-ms": "14.0801",
    "civil-engineering-phd": "14.0801",
    "computer-engineering-bs": "14.0901",
    "electrical-engineering-bs": "14.1001",
    "electrical-computer-engineering-ms": "14.1001",
    "electrical-computer-engineering-phd": "14.1001",
    "environmental-engineering-bs": "14.1401",
    "environmental-engineering-ms": "14.1401",
    "environmental-engineering-phd": "14.1401",
    "industrial-engineering-bs": "14.3501",
    "industrial-engineering-ms": "14.3501",
    "industrial-engineering-phd": "14.3501",
    "materials-science-bs": "14.1801",
    "materials-science-engineering-ms": "14.1801",
    "materials-science-phd": "14.1801",
    "mechanical-engineering-bs": "14.1901",
    "mechanical-engineering-ms": "14.1901",
    "mechanical-engineering-phd": "14.1901",
    "mechanical-engineering-undesignated-ms": "14.1901",
    "nuclear-radiological-bs": "14.2301",
    "nuclear-engineering-ms": "14.2301",
    "nuclear-engineering-phd": "14.2301",
    "engineering-science-mechanics-ms": "14.1101",
    "engineering-science-mechanics-phd": "14.1101",
    "health-systems-ms": "14.3501",
    "medical-physics-ms": "51.2205",
    "operations-research-ms": "14.3701",
    "operations-research-phd": "14.3701",
    "statistics-ms": "27.0501",
    "supply-chain-engineering-ms": "14.3501",
    "applied-systems-engineering-pmase": "14.2701",
    "manufacturing-leadership-pmml": "14.3601",
    # ── College of Sciences ──
    "applied-physics-bs": "40.0801",
    "physics-bs": "40.0801",
    "physics-ms": "40.0801",
    "physics-phd": "40.0801",
    "astrophysics-bs": "40.0801",
    "atmospheric-oceanic-sciences-bs": "40.0601",
    "earth-atmospheric-sciences-ms": "40.0601",
    "earth-atmospheric-sciences-phd": "40.0601",
    "solid-earth-planetary-sciences-bs": "40.0601",
    "biochemistry-bs": "26.0202",
    "biology-bs": "26.0101",
    "biology-ms": "26.0101",
    "biology-phd": "26.0101",
    "chemistry-bs": "40.0501",
    "chemistry-ms": "40.0501",
    "chemistry-phd": "40.0501",
    "environmental-science-bs": "03.0104",
    "mathematics-bs": "27.0101",
    "mathematics-ms": "27.0101",
    "mathematics-phd": "27.0101",
    "mathematics-computing-bs": "27.0303",
    "neuroscience-bs": "26.1501",
    "psychology-bs": "42.2701",
    "psychology-ms": "42.2701",
    "psychology-phd": "42.2701",
    "applied-physiology-phd": "26.0908",
    "ocean-science-engineering-phd": "30.3201",
    "quantitative-biosciences-phd": "26.1104",
    # ── College of Design ──
    "architecture-ms": "04.0201",
    "architecture-phd": "04.0201",
    "march": "04.0201",
    "industrial-design-bs": "50.0404",
    "masters-industrial-design": "50.0404",
    "building-construction-facility-management-ms": "04.0902",
    "building-construction-phd": "04.0902",
    "construction-science-and-management-bs": "04.0902",
    "gist-ms": "45.0702",
    "mcrp": "04.0301",
    "city-regional-planning-phd": "04.0301",
    "urban-analytics-ms": "04.0301",
    "urban-planning-and-spatial-analytics-bs": "04.0301",
    "urban-design-msud": "04.0401",
    "music-technology-bs": "50.0913",
    "music-technology-ms": "50.0913",
    "music-technology-phd": "50.0913",
    "master-real-estate-development": "04.1001",
    "occupational-safety-health-pmosh": "15.0701",
    "arts-entertainment-creative-technologies-bs": "50.0411",
    # ── Ivan Allen College of Liberal Arts ──
    "applied-language-intercultural-studies-bs": "16.0101",
    "applied-languages-intercultural-studies-ms": "16.0101",
    "economics-bs": "45.0601",
    "economics-ms": "45.0601",
    "economics-phd": "45.0601",
    "economics-international-affairs-bs": "45.0601",
    "global-economics-modern-languages-bs": "45.0601",
    "history-technology-society-bs": "30.1501",
    "history-sociology-technology-science-ms": "30.1501",
    "history-sociology-technology-science-phd": "30.1501",
    "international-affairs-bs": "45.0901",
    "international-affairs-ms": "45.0901",
    "international-affairs-modern-language-bs": "45.0901",
    "international-affairs-science-technology-ms": "45.0901",
    "international-affairs-science-technology-phd": "45.0901",
    "international-security-ms": "45.0902",
    "literature-media-communication-bs": "09.0702",
    "digital-media-ms": "09.0702",
    "digital-media-phd": "09.0702",
    "global-media-cultures-ms": "09.0702",
    "public-policy-bs": "44.0501",
    "public-policy-ms": "44.0501",
    "public-policy-phd": "44.0501",
    "global-development-ms": "30.2001",
    "master-sustainable-energy-environmental-management": "30.3301",
    # ── Scheller College of Business ──
    "business-administration-bs": "52.0201",
    "mba": "52.0201",
    "mba-global-business-executive": "52.0201",
    "mba-management-technology-executive": "52.0201",
    "management-ms": "52.0201",
    "management-phd": "52.0201",
    "analytics-ms": "30.7101",
    "online-ms-analytics": "30.7101",
    "quantitative-computational-finance-ms": "27.0305",
    # ── At-scale online master's ──
    "online-ms-computer-science-omscs": "11.0701",
    "online-ms-cybersecurity": "11.1003",
}


def _build_catalog() -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for slug, college, fmt in _CATALOG:
        if slug in seen:
            continue
        seen.add(slug)
        name, dtype, _field = _derive(slug)
        description = CATALOGUE_DESCRIPTIONS.get(slug)
        department = DEPARTMENTS.get(slug)
        if not description:
            raise ValueError(f"GT catalog missing verified description for {slug!r}")
        if not department:
            raise ValueError(f"GT catalog missing real owning department for {slug!r}")
        out.append(
            {
                "slug": f"gatech-{slug}",
                "catalog_slug": slug,
                "school": college,
                "program_name": name,
                "degree_type": dtype,
                "department": department,
                "duration_months": _duration(dtype, fmt),
                "delivery_format": fmt,
                "cip": _CIP_BY_SLUG.get(slug),
                "description": description,
            }
        )
    return out


def _duration(dtype: str, fmt: str) -> int:
    if dtype == "bachelors":
        return 48
    if dtype == "phd":
        return 60
    if fmt == "online":
        return 36  # self-paced at-scale online master's
    return 24


PROGRAMS: list[dict] = _build_catalog()
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

# Matcher-core: every program must carry a verified CIP-2020 code (REPAIR_BACKLOG #1).
# Coverage must be complete (no silent catalog-wide null); a genuinely uncodeable field
# would be recorded in _standard.omitted. Today the catalog is 100% covered.
_cip_missing = [p["catalog_slug"] for p in PROGRAMS if not p.get("cip")]
if _cip_missing:
    raise ValueError(f"GT catalog missing cip_code on {len(_cip_missing)} rows: {_cip_missing[:5]}")
_cip_bad = sorted({p["cip"] for p in PROGRAMS if not re.fullmatch(r"\d{2}\.\d{4}", p["cip"])})
if _cip_bad:
    raise ValueError(f"GT catalog has malformed cip_code values: {_cip_bad}")


def _assert_anti_stub_clean(programs: list[dict]) -> None:
    """Every GT description must score the gold-MIT zero on the anti-stub metrics."""
    from unipaith.profile_standard.anti_stub import analyze

    report = analyze(programs)
    if not report.is_clean:
        raise ValueError(f"GT catalog anti-stub gate failed: {report.summary()}")


_assert_anti_stub_clean(PROGRAMS)

# ── "Who it's for" — a UNIVERSAL depth field (enrich-profile miss #2 who_its_for rule) ────────
# Every program carries a PROGRAM-DISTINCT 1–2 sentence statement of the applicant it fits
# (subject, who it suits, typical next step), derived from that program's own published
# field/level/audience material — NOT a degree-type template (a CS PhD and a Public-Policy PhD
# must not read identically). Keyed on the full program slug; coverage must be 100% and the
# strings near-fully distinct (the bar the field-specific gold catalogs meet, distinct/total ≈ 1.0).
_WHO_BY_SLUG: dict[str, str] = {
    # ── College of Computing ──
    "gatech-computer-science-bs": "Undergraduates who want to build software and systems from first principles — algorithms, machine learning, systems, and theory — and who like Georgia Tech's Threads model of pairing computing with a second area of application. Most graduates head into software engineering or further CS study.",
    "gatech-computational-media-bs": "Students who live at the intersection of computing and the arts — game design, interactive narrative, animation, and digital media — and want the technical depth to build experiences, not just critique them. A path into games, UX, and creative-technology roles.",
    "gatech-computer-science-ms": "Working engineers and recent CS graduates who want graduate depth in a specialization (machine learning, systems, security, or interactive computing) before moving into senior technical roles; best for those who already have a computing foundation.",
    "gatech-cybersecurity-ms": "Technically grounded students aiming for security-engineering, policy, or research careers who want to combine deep systems and network security with cyber-policy and information-security management across computing, ECE, and public policy.",
    "gatech-human-computer-interaction-ms": "Designers, psychologists, and computer scientists who want rigorous, research-driven training in how people use technology — interaction design, user research, and evaluation — heading into UX research and product-design roles.",
    "gatech-bioinformatics-ms": "Life-scientists and computationally minded students who want to apply data science, genomics, and algorithms to biological problems, preparing for industry roles in biotech, pharma, and computational genomics.",
    "gatech-computational-science-engineering-ms": "Engineers and scientists who want to master high-performance computing, modeling, and large-scale data analysis to solve computationally intensive problems across the sciences and engineering.",
    "gatech-robotics-ms": "Students from CS, ECE, ME, or aerospace backgrounds who want interdisciplinary training in perception, control, autonomy, and machine learning to build robots and autonomous systems for industry or further research.",
    "gatech-computer-science-phd": "Researchers pursuing original contributions to computer science — from theory and systems to AI — who intend to lead academic, national-lab, or industrial research.",
    "gatech-human-centered-computing-phd": "Scholars who want to do original research on how computing systems are designed, used, and embedded in social contexts, bridging HCI, the learning sciences, and social computing.",
    "gatech-machine-learning-phd": "Researchers focused on the foundations and applications of machine learning — drawn from CS, ECE, ISyE, and mathematics — who want an interdisciplinary doctorate aimed at academic or research-lab careers.",
    "gatech-computational-science-engineering-phd": "Doctoral researchers developing the algorithms, models, and high-performance-computing methods that drive computational discovery across science and engineering.",
    "gatech-bioinformatics-phd": "Researchers integrating computation, statistics, and biology to study genomes and biological systems, aiming for faculty or research-scientist roles in computational biology.",
    "gatech-robotics-phd": "Doctoral students advancing the science of autonomous machines — perception, planning, manipulation, and human-robot interaction — across an interdisciplinary robotics faculty.",
    "gatech-algorithms-combinatorics-optimization-phd": "Mathematically inclined researchers who want a rigorous doctorate spanning discrete mathematics, theoretical CS, and operations research, run jointly by mathematics, computing, and ISyE.",
    "gatech-online-ms-computer-science-omscs": "Working software professionals worldwide who want a fully accredited Georgia Tech CS master's they can complete part-time and remotely for a few thousand dollars — provided they are ready for genuinely rigorous, self-directed coursework.",
    "gatech-online-ms-cybersecurity": "Employed IT and security practitioners who want an affordable, fully online Georgia Tech security master's that combines technical and policy coursework while they keep working.",
    # ── College of Engineering ── bachelors
    "gatech-aerospace-engineering-bs": "Undergraduates drawn to flight and space — aerodynamics, propulsion, structures, and controls — who want one of the country's largest aerospace programs as a path into the aerospace and defense industries.",
    "gatech-biomedical-engineering-bs": "Students who want to apply engineering to medicine and human health in a top-ranked joint program with Emory, heading toward medical devices, healthcare, or medical school.",
    "gatech-chemical-biomolecular-bs": "Undergraduates fascinated by how molecules and processes scale up — energy, materials, and biotechnology — preparing for the chemical, pharmaceutical, and energy industries or graduate study.",
    "gatech-civil-engineering-bs": "Students who want to design and build the infrastructure people depend on — structures, transportation, and water systems — and pursue licensure as professional engineers.",
    "gatech-computer-engineering-bs": "Undergraduates who want to work at the hardware-software boundary — embedded systems, processors, and computing devices — bridging electrical engineering and computing.",
    "gatech-electrical-engineering-bs": "Students drawn to electronics, power, signals, and communications who want a broad ECE foundation for industry or graduate study.",
    "gatech-environmental-engineering-bs": "Undergraduates committed to clean water, air, and sustainable systems who want to engineer solutions to environmental problems.",
    "gatech-industrial-engineering-bs": "Students who want to optimize complex systems — supply chains, logistics, manufacturing, and operations — in the nation's top-ranked IE program, heading into consulting, analytics, and operations roles.",
    "gatech-materials-science-bs": "Undergraduates curious about why materials behave as they do — metals, polymers, ceramics, and nanomaterials — preparing for the materials industries or research.",
    "gatech-mechanical-engineering-bs": "Students drawn to how things move and work — mechanics, thermodynamics, design, and manufacturing — in one of the largest ME programs in the U.S.",
    "gatech-nuclear-radiological-bs": "Undergraduates interested in nuclear power, radiation, and medical physics who want a path into the nuclear-energy, medical, and national-security sectors.",
    # ── College of Engineering ── master's
    "gatech-aerospace-engineering-ms": "Engineers seeking advanced specialization in aerodynamics, propulsion, structures, or autonomy for senior roles in the aerospace and defense industry.",
    "gatech-bioengineering-ms": "Graduate students applying engineering across biology and medicine through an interdisciplinary bioengineering program spanning several colleges.",
    "gatech-biomedical-engineering-ms": "Engineers and scientists pursuing advanced training in medical devices, imaging, and biomechanics in the joint Georgia Tech–Emory program.",
    "gatech-chemical-engineering-ms": "Graduates deepening expertise in reaction engineering, separations, energy, and biomolecular processes for industry or doctoral study.",
    "gatech-civil-engineering-ms": "Practicing and aspiring civil engineers specializing in structures, geotechnics, transportation, or water and environmental systems and moving toward professional licensure.",
    "gatech-electrical-computer-engineering-ms": "ECE graduates specializing in areas from microelectronics and power to communications, signal processing, and machine learning for advanced industry roles.",
    "gatech-engineering-science-mechanics-ms": "Students seeking the mechanics and applied-physics foundations — solid mechanics, dynamics, and the behavior of materials — that underpin advanced engineering.",
    "gatech-environmental-engineering-ms": "Engineers focusing on water quality, air, and sustainable environmental systems for consulting, utility, or agency careers.",
    "gatech-health-systems-ms": "Industrial engineers and analysts who want to apply operations-research and systems methods to healthcare delivery, improving the quality and efficiency of health systems.",
    "gatech-industrial-engineering-ms": "Engineers specializing in operations research, supply chain, analytics, or human factors in a top-ranked program with strong industry placement.",
    "gatech-materials-science-engineering-ms": "Graduates specializing in the design and characterization of advanced materials for energy, electronics, and manufacturing.",
    "gatech-mechanical-engineering-ms": "Engineers deepening expertise in design, controls, thermal and fluid sciences, or manufacturing for advanced industry roles.",
    "gatech-mechanical-engineering-undesignated-ms": "Mechanical-engineering students who want a flexible, self-directed master's spanning the breadth of ME rather than a single named specialization.",
    "gatech-medical-physics-ms": "Physics and engineering graduates preparing for careers in clinical and radiation medical physics — therapy and imaging — in healthcare settings.",
    "gatech-nuclear-engineering-ms": "Engineers specializing in reactor physics, radiation, and nuclear systems for the energy, medical, and national-security sectors.",
    "gatech-operations-research-ms": "Quantitatively strong graduates who want rigorous training in optimization, stochastics, and statistics to solve decision problems across industries.",
    "gatech-statistics-ms": "Graduates seeking applied and theoretical statistics — modeling, inference, and data analysis — for analytics and data-science careers.",
    "gatech-supply-chain-engineering-ms": "Engineers and analysts specializing in logistics, supply-chain design, and operations in the nation's leading supply-chain program.",
    # ── College of Engineering ── professional
    "gatech-applied-systems-engineering-pmase": "Mid-career engineers, often in defense and aerospace, who want an INCOSE-recognized professional master's in systems engineering delivered for working professionals (PMASE).",
    "gatech-manufacturing-leadership-pmml": "Experienced engineers moving into manufacturing leadership who want a professional master's combining advanced manufacturing with management.",
    # ── College of Engineering ── PhD
    "gatech-aerospace-engineering-phd": "Researchers pursuing original work in aerospace — fluid dynamics, structures, propulsion, and autonomy — for academic, national-lab, or industry-research careers.",
    "gatech-bioengineering-phd": "Doctoral researchers working across engineering and the life sciences in an interdisciplinary bioengineering program.",
    "gatech-biomedical-engineering-phd": "Researchers advancing medical devices, regenerative medicine, and imaging in the joint Georgia Tech–Emory BME doctorate.",
    "gatech-chemical-engineering-phd": "Doctoral researchers in catalysis, energy, soft matter, and biomolecular engineering aiming for faculty or industrial-research roles.",
    "gatech-civil-engineering-phd": "Researchers advancing structures, geosystems, transportation, or environmental engineering through original doctoral work.",
    "gatech-electrical-computer-engineering-phd": "Doctoral researchers across ECE — from nanoelectronics to communications and machine learning — pursuing academic or research-lab careers.",
    "gatech-engineering-science-mechanics-phd": "Researchers in solid mechanics, dynamics, and the mechanics of materials that underpin advanced engineering.",
    "gatech-environmental-engineering-phd": "Doctoral researchers in water, air, and sustainability engineering aiming for academic or research careers.",
    "gatech-industrial-engineering-phd": "Researchers in operations research, optimization, statistics, and systems pursuing faculty or research roles in a top-ranked program.",
    "gatech-materials-science-phd": "Doctoral researchers designing and studying advanced materials for energy, electronics, and structural applications.",
    "gatech-mechanical-engineering-phd": "Researchers advancing the mechanical sciences — robotics, energy, manufacturing, and biomechanics — toward academic or research careers.",
    "gatech-nuclear-engineering-phd": "Doctoral researchers in reactor physics, radiation transport, and nuclear systems for energy and security applications.",
    "gatech-operations-research-phd": "Researchers developing the mathematics of optimization and stochastic systems, jointly across ISyE, mathematics, and computing.",
    # ── College of Sciences ── bachelors
    "gatech-applied-physics-bs": "Undergraduates who want physics aimed at real devices and technologies — optics, materials, and electronics — bridging fundamental science and engineering.",
    "gatech-astrophysics-bs": "Students captivated by stars, galaxies, and cosmology who want a physics-grounded path into astronomy research or graduate study.",
    "gatech-atmospheric-oceanic-sciences-bs": "Undergraduates drawn to weather, climate, and the oceans who want quantitative training for environmental science or graduate research.",
    "gatech-biochemistry-bs": "Students fascinated by the chemistry of living systems — proteins, metabolism, and molecular mechanisms — preparing for the health professions or research.",
    "gatech-biology-bs": "Undergraduates exploring life from molecules to ecosystems who want a research-oriented foundation for graduate study, the health professions, or biotech.",
    "gatech-chemistry-bs": "Students drawn to how matter transforms — synthesis, analysis, and physical chemistry — heading into the chemical industry, research, or professional school.",
    "gatech-environmental-science-bs": "Undergraduates focused on earth systems and sustainability who want interdisciplinary science to address environmental challenges.",
    "gatech-mathematics-bs": "Students who love rigorous reasoning and abstraction across pure and applied mathematics, preparing for graduate study, analytics, or quantitative careers.",
    "gatech-mathematics-computing-bs": "Undergraduates who want to combine mathematical rigor with computation — algorithms, modeling, and data — for quantitative and computing careers.",
    "gatech-neuroscience-bs": "Students fascinated by the brain and behavior who want an interdisciplinary, research-driven path toward neuroscience, medicine, or graduate study.",
    "gatech-physics-bs": "Undergraduates drawn to the fundamental laws of nature who want a strong foundation for graduate study or technical careers in science and industry.",
    "gatech-psychology-bs": "Students interested in mind, behavior, and human factors who want a quantitative, research-oriented psychology degree.",
    "gatech-solid-earth-planetary-sciences-bs": "Undergraduates fascinated by the Earth and planets — geology, geophysics, and planetary science — preparing for earth-science research or industry.",
    # ── College of Sciences ── master's
    "gatech-biology-ms": "Graduates seeking advanced training in molecular, cellular, or organismal biology for research, biotech, or further doctoral study.",
    "gatech-chemistry-ms": "Graduates deepening expertise in a chemistry subfield for industry or as a step toward doctoral research.",
    "gatech-earth-atmospheric-sciences-ms": "Students advancing their study of the atmosphere, oceans, and solid earth with quantitative and computational methods.",
    "gatech-mathematics-ms": "Graduates strengthening their mathematical depth — pure or applied — for quantitative careers or doctoral preparation.",
    "gatech-physics-ms": "Graduates deepening their physics training for technical industry roles or as a step toward a doctorate.",
    "gatech-psychology-ms": "Graduates advancing in areas such as cognition, engineering psychology, or quantitative methods toward research or applied roles.",
    # ── College of Sciences ── PhD
    "gatech-applied-physiology-phd": "Researchers studying how the human body responds to exercise, stress, and the environment, aiming for academic or health-research careers.",
    "gatech-biology-phd": "Doctoral researchers pursuing original work from genomics to ecology and evolution for faculty or research-scientist roles.",
    "gatech-chemistry-phd": "Researchers advancing organic, inorganic, physical, or analytical chemistry toward academic or industrial-research careers.",
    "gatech-earth-atmospheric-sciences-phd": "Doctoral researchers in climate, atmospheric, ocean, and earth sciences pursuing original quantitative work.",
    "gatech-mathematics-phd": "Researchers pursuing original work in pure or applied mathematics who intend to enter academia or quantitative research.",
    "gatech-ocean-science-engineering-phd": "Interdisciplinary researchers studying ocean systems where science meets engineering, from biogeochemistry to marine technology.",
    "gatech-physics-phd": "Doctoral researchers across condensed matter, biophysics, astrophysics, and quantum science pursuing academic or research-lab careers.",
    "gatech-psychology-phd": "Researchers in cognition, engineering psychology, neuroscience, or quantitative methods aiming for faculty or applied-research roles.",
    "gatech-quantitative-biosciences-phd": "Researchers integrating biology with mathematics, physics, and computation to study living systems quantitatively.",
    # ── College of Design ── bachelors
    "gatech-arts-entertainment-creative-technologies-bs": "Students working at the intersection of art and technology — interactive media, performance, and creative computing — who want to build the tools and experiences of entertainment.",
    "gatech-construction-science-and-management-bs": "Undergraduates aiming for careers managing how buildings get built — construction methods, project management, and the built environment.",
    "gatech-industrial-design-bs": "Students who want to design the products and experiences people use, blending creativity, human-centered research, and engineering.",
    "gatech-music-technology-bs": "Undergraduates who combine music with engineering and computing — audio, instruments, and interactive sound — for careers in music technology.",
    "gatech-urban-planning-and-spatial-analytics-bs": "Students interested in shaping cities through planning and data — land use, transportation, and spatial analysis.",
    # ── College of Design ── master's
    "gatech-architecture-ms": "Designers and researchers pursuing advanced, often computational or technology-focused study of architecture beyond the professional degree.",
    "gatech-march": "Students pursuing the accredited professional degree required to become a licensed architect, combining design studios with building technology and history.",
    "gatech-masters-industrial-design": "Designers advancing their practice in product and experience design through research-driven, human-centered methods.",
    "gatech-building-construction-facility-management-ms": "Professionals advancing in construction management, facility operations, and building technology for leadership in the architecture-engineering-construction industry.",
    "gatech-gist-ms": "Students who want to master geographic information science — spatial data, GIS, and remote sensing — for analytics and planning careers.",
    "gatech-mcrp": "Aspiring urban and regional planners who want a professional planning degree spanning land use, transportation, housing, and community development.",
    "gatech-urban-analytics-ms": "Planners and analysts who want to apply data science and spatial methods to urban problems and decision-making.",
    "gatech-urban-design-msud": "Architects and planners focused on the design of public space and the form of cities at the neighborhood and district scale.",
    "gatech-music-technology-ms": "Graduates combining music, engineering, and computing to research and build new musical instruments, audio systems, and interactive sound.",
    # ── College of Design ── professional
    "gatech-master-real-estate-development": "Professionals entering real-estate development who want an interdisciplinary degree spanning design, finance, and construction.",
    "gatech-occupational-safety-health-pmosh": "Working safety and health professionals who want a professional master's to advance into occupational-safety leadership roles.",
    # ── College of Design ── PhD
    "gatech-architecture-phd": "Researchers pursuing original scholarship in architecture — design computing, building technology, or history and theory.",
    "gatech-building-construction-phd": "Doctoral researchers advancing the science of construction, building technology, and facility management.",
    "gatech-city-regional-planning-phd": "Researchers studying cities and regions — land use, transportation, environment, and policy — for academic or research careers.",
    "gatech-music-technology-phd": "Researchers at the frontier of music, computing, and engineering, building and studying new musical technologies.",
    # ── Ivan Allen College of Liberal Arts ── bachelors
    "gatech-applied-language-intercultural-studies-bs": "Students who want to combine fluency in a second language and culture with technical and professional skills for global careers.",
    "gatech-economics-bs": "Undergraduates who want a quantitative, policy-relevant economics degree with strong analytical and data skills.",
    "gatech-economics-international-affairs-bs": "Students combining economic analysis with international relations for careers in policy, trade, and global business.",
    "gatech-global-economics-modern-languages-bs": "Undergraduates pairing economics with advanced language and cultural study for international careers.",
    "gatech-history-technology-society-bs": "Students interested in how technology shapes — and is shaped by — society, history, and policy.",
    "gatech-international-affairs-bs": "Undergraduates focused on global politics, security, and development who want a technology-aware international-affairs degree.",
    "gatech-international-affairs-modern-language-bs": "Students combining international affairs with deep language and regional expertise for global careers.",
    "gatech-literature-media-communication-bs": "Students who want to analyze and produce across literature, media, and digital communication, bridging the humanities and technology.",
    "gatech-public-policy-bs": "Undergraduates who want to analyze and shape public decisions on technology, science, and society using evidence and policy tools.",
    # ── Ivan Allen College of Liberal Arts ── master's
    "gatech-applied-languages-intercultural-studies-ms": "Graduates advancing professional language and intercultural competence for translation, localization, and global communication careers.",
    "gatech-digital-media-ms": "Designers and researchers who want to study and build interactive and digital media, games, and emerging communication forms.",
    "gatech-economics-ms": "Graduates seeking rigorous applied economics — econometrics and policy analysis — for analyst and research roles.",
    "gatech-global-development-ms": "Students focused on the policy, economics, and technology of international development and global problem-solving.",
    "gatech-global-media-cultures-ms": "Graduates studying media, culture, and communication across borders, often with a comparative or global focus.",
    "gatech-history-sociology-technology-science-ms": "Graduates studying the historical and social dimensions of science and technology for research, policy, or further doctoral study.",
    "gatech-international-affairs-ms": "Graduates pursuing careers in diplomacy, security, and global policy with a science-and-technology orientation.",
    "gatech-international-affairs-science-technology-ms": "Students focused on where international affairs meets science and technology policy — security, energy, and innovation.",
    "gatech-international-security-ms": "Graduates specializing in security studies — defense, intelligence, and conflict — for policy and analytic careers.",
    "gatech-public-policy-ms": "Graduates who want rigorous policy analysis — economics, statistics, and program evaluation — for government, nonprofit, and private-sector roles.",
    # ── Ivan Allen College of Liberal Arts ── professional
    "gatech-master-sustainable-energy-environmental-management": "Working professionals who want to lead in energy and environmental management, combining policy, economics, and technology.",
    # ── Ivan Allen College of Liberal Arts ── PhD
    "gatech-digital-media-phd": "Researchers studying and building interactive and digital media, games, and computational creativity.",
    "gatech-economics-phd": "Researchers pursuing original work in economics with strong quantitative methods for academic or policy-research careers.",
    "gatech-history-sociology-technology-science-phd": "Doctoral researchers in the history and sociology of science and technology aiming for faculty or research careers.",
    "gatech-international-affairs-science-technology-phd": "Researchers studying the intersection of global affairs, security, and science-and-technology policy.",
    "gatech-public-policy-phd": "Researchers developing original policy scholarship — especially on science, technology, and innovation — for academic or think-tank careers.",
    # ── Scheller College of Business ──
    "gatech-business-administration-bs": "Undergraduates who want a technology-focused, analytics-driven business degree from a top public business school, heading into consulting, finance, and technology management.",
    "gatech-mba": "Early-career professionals who want a smaller, technology-focused full-time MBA in Atlanta's Tech Square, with strong career services and top specializations in analytics, IT, and operations.",
    "gatech-mba-global-business-executive": "Experienced managers who want an executive MBA emphasizing global business while continuing to work.",
    "gatech-mba-management-technology-executive": "Experienced technical professionals and managers who want an executive MBA focused on leading technology and innovation.",
    "gatech-analytics-ms": "Quantitatively strong graduates who want an interdisciplinary analytics master's spanning computing, statistics, and business for data-science and analytics careers.",
    "gatech-management-ms": "Recent graduates, often from technical backgrounds, who want a one-year business foundation before entering management and consulting roles.",
    "gatech-quantitative-computational-finance-ms": "Mathematically and computationally strong graduates aiming for quantitative finance — trading, risk, and financial engineering — in a top-ranked QCF program.",
    "gatech-management-phd": "Researchers pursuing original scholarship in management — strategy, operations, IT, finance, or marketing — for business-school faculty careers.",
    "gatech-online-ms-analytics": "Working professionals who want Georgia Tech's top-ranked analytics master's fully online and affordably, while continuing to work and provided they are ready for rigorous, self-directed study.",
}


def _assert_who_its_for_complete(programs: list[dict]) -> None:
    """who_its_for is a UNIVERSAL depth field: 100% coverage, program-DISTINCT (no type-gaming)."""
    missing = [p["slug"] for p in programs if not _WHO_BY_SLUG.get(p["slug"])]
    if missing:
        raise ValueError(f"GT who_its_for missing on {len(missing)} programs: {missing[:5]}")
    values = [_WHO_BY_SLUG[p["slug"]] for p in programs]
    distinct = len(set(values))
    # Field-specific gold catalogs run distinct/total ≈ 1.0; type-gaming collapses well under 0.5.
    if distinct < len(values):
        dupes = sorted({v for v in values if values.count(v) > 1})
        raise ValueError(f"GT who_its_for is not program-distinct ({distinct}/{len(values)}): {dupes[:3]}")


_assert_who_its_for_complete(PROGRAMS)

# Per-program catalog website (catalog.gatech.edu/programs/<catalog_slug>/) or a verified
# program homepage for the online degrees.
_PROGRAM_WEBSITE: dict[str, str] = {
    "gatech-online-ms-computer-science-omscs": "https://omscs.gatech.edu/",
    "gatech-online-ms-analytics": "https://pe.gatech.edu/degrees/analytics",
    "gatech-online-ms-cybersecurity": "https://pe.gatech.edu/degrees/cybersecurity",
}


def _website_for(spec: dict) -> str:
    slug = spec["slug"]
    if slug in _PROGRAM_WEBSITE:
        return _PROGRAM_WEBSITE[slug]
    return f"https://catalog.gatech.edu/programs/{spec['catalog_slug']}/"


# Per-program keywords (program/department-naming terms) so the shared college feed is filtered
# to program-relevant items. Programs without an entry inherit their college's keywords.
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "gatech-online-ms-computer-science-omscs": [
        "OMSCS",
        "online computer science",
        "computer science",
    ],
    "gatech-online-ms-analytics": ["OMS Analytics", "online analytics", "data science"],
    "gatech-online-ms-cybersecurity": ["online cybersecurity", "cybersecurity"],
    "gatech-computer-science-bs": ["computer science", "College of Computing"],
    "gatech-analytics-ms": ["analytics", "data science", "Scheller"],
    "gatech-mba": ["MBA", "Scheller"],
    "gatech-aerospace-engineering-bs": ["aerospace engineering", "Daniel Guggenheim"],
    "gatech-mechanical-engineering-bs": ["mechanical engineering", "Woodruff School"],
    "gatech-industrial-engineering-bs": ["industrial engineering", "Stewart School", "ISyE"],
}

# ── Costs ──────────────────────────────────────────────────────────────────
# Published 2024-25 / 2025-26 Georgia Tech undergraduate figures (GT CDS + College Scorecard).
_TUITION_UG_IN_STATE = 10512
_TUITION_UG_OUT_STATE = 32938
_UNDERGRAD_COA = 28167  # College Scorecard academic-year cost of attendance (in-state).
_AVG_NET_PRICE = 12116
_COST_SRC = (
    "Georgia Tech Common Data Set 2024-25 (Bursar tuition & fees) + College Scorecard (UNITID 139755)",
    "https://irp.gatech.edu/files/CDS/CDS_2024-2025_FINAL_20FEB2025.pdf",
)

# Per-program verified graduate tuition (only where Georgia Tech publishes a single total/annual
# figure). All other graduate/professional programs bill per credit hour and carry a sourced
# "see the program page" record (tuition_usd recorded in _standard.omitted, never guessed).
_COST_BY_SLUG: dict[str, dict] = {
    "gatech-online-ms-computer-science-omscs": {
        "tuition_usd": 7000,
        "tuition_basis": "total program (approximate)",
        "funded": False,
        "note": (
            "OMSCS is billed at a low per-credit-hour rate ($180/credit as of the 2024-25 "
            "schedule); the 30-credit degree totals roughly $7,000 — a small fraction of the "
            "on-campus or comparable online CS master's cost. Figure approximate and subject to "
            "Board of Regents tuition changes."
        ),
        "source": "Georgia Tech OMSCS — Program Costs",
        "source_url": "https://omscs.gatech.edu/program-info/cost-payment-schedule",
        "year": "2024-25",
    },
    "gatech-online-ms-analytics": {
        "tuition_usd": 12348,
        "tuition_basis": "total program",
        "funded": False,
        "note": (
            "Total tuition for the 36-credit Online MS in Analytics is $11,880 (Georgia "
            "resident) / $12,348 (U.S.) / $12,960 (international), at $327 per credit hour plus "
            "a per-term online learning fee — among the lowest-cost top-ranked analytics "
            "master's degrees. Figure shown is the U.S. total."
        ),
        "source": "Georgia Tech Professional Education — OMS Analytics tuition",
        "source_url": "https://pe.gatech.edu/degrees/analytics",
        "year": "2024-25",
    },
    "gatech-online-ms-cybersecurity": {
        "tuition_usd": 11936,
        "tuition_basis": "total program",
        "funded": False,
        "note": (
            "The 32-credit Online MS in Cybersecurity (OMS Cyber) is billed per credit hour "
            "($373/credit on the Fall 2026 Bursar schedule), totaling roughly $11,936 in "
            "tuition — the program is advertised at under $12,000 total, a fraction of a "
            "comparable on-campus or peer online cybersecurity master's. Part-time program "
            "spread over two to three years; figure is the full-program total."
        ),
        "source": "Georgia Tech Office of the Bursar (Fall 2026) + GTPE OMS Cybersecurity",
        "source_url": "https://pe.gatech.edu/degrees/cybersecurity",
        "year": "2026-27",
    },
    # ── Professional-tier tuition (REPAIR_BACKLOG — prof 3/8 → 8/8) ──
    "gatech-mba-global-business-executive": {
        "tuition_usd": 87100,
        "tuition_basis": "total program",
        "funded": False,
        "note": (
            "Scheller Executive MBA (Global Business track) inclusive program fee for the "
            "2025-26 class: $87,100 total (paid across four semesters plus a $1,500 "
            "non-refundable enrollment deposit applied to the first term). Covers tuition, "
            "fees, textbooks, parking, meals during class sessions, select international "
            "residency costs, and executive career coaching."
        ),
        "source": "Georgia Tech Scheller College of Business — Executive MBA Tuition and Financing",
        "source_url": (
            "https://www.scheller.gatech.edu/explore-programs/mba-programs/"
            "executive-mba/tuition-and-financing/index.html"
        ),
        "year": "2025-26",
    },
    "gatech-mba-management-technology-executive": {
        "tuition_usd": 87100,
        "tuition_basis": "total program",
        "funded": False,
        "note": (
            "Scheller Executive MBA (Management of Technology track) inclusive program fee "
            "for the 2025-26 class: $87,100 total — the same turnkey Executive MBA program "
            "fee structure as the Global Business track (four-semester payment schedule)."
        ),
        "source": "Georgia Tech Scheller College of Business — Executive MBA Tuition and Financing",
        "source_url": (
            "https://www.scheller.gatech.edu/explore-programs/mba-programs/"
            "executive-mba/tuition-and-financing/index.html"
        ),
        "year": "2025-26",
    },
    "gatech-applied-systems-engineering-pmase": {
        "tuition_usd": 34150,
        "tuition_basis": "total program",
        "funded": False,
        "note": (
            "GTPE Professional Master's in Applied Systems Engineering: 10 three-credit "
            "courses (30 credit hours) at $3,415 tuition per course = $34,150 total program "
            "tuition (mandatory student fees billed separately each enrolled term)."
        ),
        "source": "Georgia Tech Professional Education — PMASE tuition and fees",
        "source_url": "https://pe.gatech.edu/degrees/pmase",
        "year": "2025-26",
    },
    "gatech-manufacturing-leadership-pmml": {
        "tuition_usd": 34150,
        "tuition_basis": "total program",
        "funded": False,
        "note": (
            "GTPE Professional Master's in Manufacturing Leadership: 10 three-credit courses "
            "(30 credit hours) at $3,415 tuition per course = $34,150 total program tuition "
            "(mandatory student fees billed separately each enrolled term)."
        ),
        "source": "Georgia Tech Professional Education — PMML tuition and fees",
        "source_url": "https://pe.gatech.edu/degrees/pmml",
        "year": "2025-26",
    },
    "gatech-occupational-safety-health-pmosh": {
        "tuition_usd": 34150,
        "tuition_basis": "total program",
        "funded": False,
        "note": (
            "GTPE Professional Master's in Occupational Safety and Health: 10 three-credit "
            "courses (30 credit hours) at $3,415 tuition per course = $34,150 total program "
            "tuition (mandatory student fees billed separately each enrolled term)."
        ),
        "source": "Georgia Tech Professional Education — PMOSH tuition and fees",
        "source_url": "https://pe.gatech.edu/degrees/pmosh",
        "year": "2025-26",
    },
}

# ── Published graduate tuition (REPAIR_BACKLOG #2 — master's/professional starvation) ──
# Georgia Tech is a public university; the University System of Georgia Board of Regents
# publishes a standard full-time graduate tuition that applies to every graduate program
# EXCEPT those on the Bursar's differential-tuition list. The figures below are the CURRENT
# Fall 2026 Bursar full-time (12+ credit) per-semester rates DOUBLED to an academic-year
# total (the same in-state basis the undergraduate row uses; Program.tuition is read as
# ANNUAL tuition by the matcher), verified against the official Bursar "Fall 2026 Tuition
# and Fee Rates per Semester" schedule. Funding (assistantships) is a SEPARATE signal —
# these are the published sticker tuition the matcher scores on.
_TUITION_GRAD_IN_STATE = 14560  # $7,280/sem standard graduate rate × 2 semesters
_TUITION_GRAD_OUT_STATE = 32146  # $16,073/sem standard graduate rate × 2 semesters

# slug → (annual in-state, annual out-of-state) for Bursar DIFFERENTIAL-tuition programs
# (each its own published rate, distinct from the standard graduate rate and from each
# other — never one uniform number flattened across the tier). Fall 2026 per-sem × 2.
_GRAD_TUITION_BY_SLUG: dict[str, tuple[int, int]] = {
    "gatech-mba": (30548, 44956),  # Scheller Full-Time MBA — $15,274/$22,478 per sem
    "gatech-quantitative-computational-finance-ms": (18206, 42632),  # MSQCF
    "gatech-analytics-ms": (30236, 44700),  # on-campus MS Analytics (MSANLT) — premium
    "gatech-electrical-computer-engineering-ms": (17056, 37660),  # MSECE
    "gatech-human-computer-interaction-ms": (16630, 39060),  # MSHCI
    "gatech-robotics-ms": (16622, 39052),  # MSROBO
    "gatech-bioinformatics-ms": (17100, 40472),  # MSBINF
    "gatech-supply-chain-engineering-ms": (17150, 41804),  # MSSCE
    "gatech-march": (18692, 36546),  # Master of Architecture (MARCH)
    "gatech-mcrp": (17506, 35286),  # Master of City & Regional Planning (MCRP)
    "gatech-gist-ms": (17506, 35286),  # MS Geographic Information Science & Tech (MSGIST)
    "gatech-masters-industrial-design": (18692, 38840),  # Master of Industrial Design (MID)
    "gatech-music-technology-ms": (18136, 35958),  # MS Music Technology (MSMT)
    "gatech-urban-design-msud": (18692, 36546),  # MS Urban Design (MSUD)
    "gatech-building-construction-facility-management-ms": (20204, 43772),  # MSBCFM
}

# Slugs whose tuition is intentionally omitted (funded doctorates only — professional /
# executive / GTPE programs now carry verified totals in ``_COST_BY_SLUG``).
_GRAD_TUITION_OMIT: frozenset[str] = frozenset()


def _grad_cost_fallback(spec: dict) -> dict:
    return {
        "funded": spec.get("degree_type") == "phd",
        "note": (
            "Tuition for this graduate/professional program is billed by the Georgia Tech "
            "Bursar (per-credit-hour or per residence term) and varies by residency and "
            "enrollment; a verified single per-program annual figure is not published. "
            "Research master's and doctoral students are typically funded through "
            "assistantships that cover tuition."
        ),
        "source": "Georgia Tech Bursar / program tuition page",
        "source_url": _website_for(spec),
    }


def _grad_cost(spec: dict) -> dict:
    """Published GT graduate cost for a non-bachelor's program.

    A verified per-program override (``_COST_BY_SLUG``) wins at apply-time; funded
    doctorates omit tuition_usd with a sourced reason; then Bursar differential programs
    carry their own published rate; every other graduate program carries the standard
    published full-time graduate tuition (never leave a knowable tier null).
    """
    slug = spec["slug"]
    if spec.get("degree_type") == "phd" or slug in _GRAD_TUITION_OMIT:
        return _grad_cost_fallback(spec)
    diff = _GRAD_TUITION_BY_SLUG.get(slug)
    if diff is not None:
        tin, tout = diff
        basis = "Bursar differential-tuition program"
    else:
        tin, tout = _TUITION_GRAD_IN_STATE, _TUITION_GRAD_OUT_STATE
        basis = "standard graduate rate (University System of Georgia)"
    return {
        "tuition_usd": tin,
        "tuition_basis": f"annual, in-state — {basis}",
        "funded": False,
        "breakdown": {
            "tuition_in_state": tin,
            "tuition_out_of_state": tout,
        },
        "note": (
            f"Published Georgia Tech graduate tuition (Fall 2026 Bursar full-time rate × "
            f"two semesters): ${tin:,} in-state / ${tout:,} out-of-state, plus required "
            f"fees. Set by the University System of Georgia Board of Regents; many research "
            f"students receive assistantships that cover tuition separately."
        ),
        "source": "Georgia Tech Office of the Bursar — Fall 2026 Tuition and Fee Rates",
        "source_url": "https://bursar.gatech.edu/tuition-fees",
        "year": "2026-27",
    }


# ── Outcomes ───────────────────────────────────────────────────────────────
# Georgia Tech publishes career outcomes by degree LEVEL (Career & Salary Survey, AY 2023-24):
# institute-wide median full-time salary and job-acceptance rate for bachelor's / master's /
# doctoral graduates. Each program carries the figure for its degree level with the methodology
# stated verbatim; program-specific industry splits are not published (omitted per program).
_OUTCOMES_CONDITIONS = (
    "Institute-wide median full-time starting salary and full-time job-acceptance rate for "
    "Georgia Tech graduates at this degree level (Career Center / Office of Academic "
    "Effectiveness Career & Salary Survey, AY 2023-24, self-reported at graduation); not a "
    "program-specific figure."
)
_OUTCOMES_SRC = "Georgia Tech Career Center — Career & Salary Outcomes Report 2023-24"
_OUTCOMES_SRC_URL = "https://academiceffectiveness.gatech.edu/surveys/reports/georgia-tech-career-survey-report-ay-2024-2025"


def _outcomes_for(dtype: str) -> dict:
    by_level = {
        "bachelors": {"median_salary": 84000, "employment_rate": 0.73, "mean_salary": 88587},
        "masters": {"median_salary": 118000, "employment_rate": 0.81, "mean_salary": 121869},
        "phd": {"median_salary": 114000, "mean_salary": 116880},
        "professional": {"median_salary": 118000, "employment_rate": 0.81, "mean_salary": 121869},
    }
    rec = dict(by_level.get(dtype, by_level["masters"]))
    rec.update(
        {
            "scope": "institution_by_degree_level",
            "conditions": _OUTCOMES_CONDITIONS,
            "source": _OUTCOMES_SRC,
            "source_url": _OUTCOMES_SRC_URL,
        }
    )
    return rec


# Scheller Full-Time MBA carries its own verified employment report (program-specific).
_MBA_OUTCOMES = {
    "employment_rate": 0.884,
    "median_salary": 146260,
    "median_signing_bonus": 30000,
    "scope": "program",
    "top_industries": ["Consulting", "Technology", "Financial Services", "Healthcare", "Energy"],
    "top_employers": ["Amazon", "Bain & Company", "Honeywell", "PwC", "UPS", "McKinsey & Company"],
    "conditions": (
        "Scheller Full-Time MBA Class of 2024: 88.4% of graduates accepted full-time roles "
        "within three months of graduation; average base salary $146,260; median signing bonus "
        "$30,000 (69 job-seekers across 36 employers in 12 industries)."
    ),
    "source": "Georgia Tech Scheller College of Business — MBA Class of 2024 employment report",
    "source_url": "https://www.scheller.gatech.edu/news/2025/georgia-tech-full-time-mba-no-21-evening-mba-no-10.html",
}

# ── Admissions requirement sets ────────────────────────────────────────────
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission.",
}
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application or Georgia Tech application", "required": True},
        {"name": "Georgia Tech short-answer essays", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "School counselor / teacher recommendation", "required": False},
        {
            "name": "$75 application fee (in-state) / $85 (out-of-state); fee waivers available",
            "required": True,
        },
        {
            "name": "SAT or ACT scores",
            "required": True,
            "note": "Georgia Tech uses SAT/ACT scores in first-year admission decisions.",
        },
    ],
    "deadlines": [
        {"round": "Early Action I (Georgia students)", "date": "October 15"},
        {"round": "Early Action II (non-Georgia students)", "date": "November 1"},
        {"round": "Regular Decision", "date": "January 4"},
    ],
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "Duolingo English Test"],
            "required": False,
            "note": "English-proficiency proof may be required for non-native speakers.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Georgia Tech Undergraduate Admission — First-Year",
                "url": "https://admission.gatech.edu/first-year/",
            }
        ],
    },
    "source": "Georgia Tech Undergraduate Admission",
    "source_url": "https://admission.gatech.edu/first-year/",
}

_REQ_MBA = {
    "materials": [
        {"name": "Scheller MBA online application", "required": True},
        {"name": "Required essays", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Two letters of recommendation", "required": True},
        {"name": "Resume", "required": True},
        {
            "name": "GMAT or GRE scores",
            "required": False,
            "note": "A test waiver is available for qualified applicants.",
        },
        {"name": "Interview (by invitation)", "required": False},
    ],
    "deadlines": [
        {"round": "Round 1", "date": "October"},
        {"round": "Round 2", "date": "January"},
        {"round": "Round 3", "date": "March"},
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
                "label": "Scheller College of Business — Full-Time MBA Admissions",
                "url": "https://www.scheller.gatech.edu/degree-programs/full-time-mba/",
            }
        ],
    },
    "source": "Scheller College of Business — Full-Time MBA",
    "source_url": "https://www.scheller.gatech.edu/degree-programs/full-time-mba/",
}

_REQ_ONLINE = {
    "materials": [
        {"name": "Online program application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Letters of recommendation", "required": True},
        {"name": "Resume / CV", "required": True},
        {
            "name": "GRE scores",
            "required": False,
            "note": "The at-scale online master's degrees (OMSCS, OMS Analytics, OMS Cybersecurity) do not require the GRE/GMAT.",
        },
    ],
    "deadlines": [
        {"round": "Fall entry", "date": "Spring application window"},
        {"round": "Spring entry", "date": "Summer application window"},
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
                "label": "Georgia Tech Professional Education — Online Degrees",
                "url": "https://pe.gatech.edu/degrees",
            }
        ],
    },
    "source": "Georgia Tech Professional Education — Online Master's Degrees",
    "source_url": "https://pe.gatech.edu/degrees",
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
            "note": "Most Georgia Tech graduate programs require three letters; check the program page.",
        },
        {
            "name": "GRE scores",
            "required": False,
            "note": "GRE requirements vary by program; many Georgia Tech programs are test-optional.",
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
                "label": "Georgia Tech Graduate Education — Admissions",
                "url": "https://grad.gatech.edu/admissions",
            }
        ],
    },
    "source": "Georgia Tech Graduate Education",
    "source_url": "https://grad.gatech.edu/admissions",
}


def _requirements_for(spec: dict) -> dict:
    slug = spec["slug"]
    if spec["degree_type"] == "bachelors":
        return _REQ_UNDERGRAD
    if slug in (
        "gatech-mba",
        "gatech-mba-global-business-executive",
        "gatech-mba-management-technology-executive",
    ):
        return _REQ_MBA
    if spec.get("delivery_format") == "online":
        return _REQ_ONLINE
    return _REQ_GRAD_GENERIC


# ── Curriculum tracks (only for programs with a verified published track structure) ──
_TRACKS_BY_SLUG: dict[str, dict] = {
    "gatech-online-ms-analytics": {
        "structure": "36 credit hours across three specialization tracks (interdisciplinary).",
        "tracks": [
            "Analytical Tools",
            "Business Analytics",
            "Computational Data Analytics",
        ],
        "source": "Georgia Tech Professional Education — OMS Analytics",
        "source_url": "https://pe.gatech.edu/degrees/analytics",
    },
    "gatech-computer-science-bs": {
        "structure": "The BS in Computer Science uses Georgia Tech's 'Threads' model: students combine two of eight threads to shape their degree.",
        "tracks": [
            "Intelligence",
            "Information Internetworks",
            "Systems and Architecture",
            "People",
            "Media",
            "Modeling and Simulation",
            "Theory",
            "Devices",
        ],
        "source": "Georgia Tech College of Computing — BS in Computer Science Threads",
        "source_url": "https://www.cc.gatech.edu/threads-better-way-learn-computing",
    },
}

# ── Class profile (only where a verified figure is published) ──
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    "gatech-mba": {
        "cohort_size": 145,
        "source": "Poets&Quants — Scheller College of Business profile (Full-Time enrollment)",
        "source_url": "https://poetsandquants.com/school-profile/georgia-institute-of-technologys-scheller-college-of-business/",
    },
    "gatech-online-ms-computer-science-omscs": {
        "cohort_size": 10000,
        "note": "OMSCS graduated more than 10,000 alumni in its first decade; current enrollment is the largest of any computing master's program.",
        "source": "Georgia Tech OMSCS",
        "source_url": "https://omscs.gatech.edu/",
    },
}

# ── Faculty contacts (program leadership / directory) ──
_FACULTY_BY_SLUG: dict[str, dict] = {
    "gatech-online-ms-computer-science-omscs": {
        "lead": "Charles Isbell-era founding program; College of Computing faculty teach the same courses as on-campus.",
        "directory_url": "https://www.cc.gatech.edu/people",
    },
    "gatech-mba": {
        "lead": "Scheller College of Business faculty; Jones MBA Career Center supports placement.",
        "directory_url": "https://www.scheller.gatech.edu/directory/faculty/",
    },
}

# ── External reviews (MBAn shape) for the flagship coverable programs ──
# GATHER → SUMMARIZE → CITE: distilled from substantial public third-party coverage, including
# the common cautions. Aggregated/paraphrased from public sources — not individual verbatim
# quotes or fabricated ratings.
_REVIEWS_DISCLAIMER = (
    "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, "
    "the trade press, official employment reports, and reputable student-review communities). "
    "Themes summarize common sentiment; they are not individual verbatim quotes or institute "
    "endorsements."
)

_REVIEWS_BY_SLUG: dict[str, dict] = {
    "gatech-online-ms-computer-science-omscs": {
        "summary": (
            "Georgia Tech's Online MS in Computer Science (OMSCS), launched in 2014 with Udacity "
            "and AT&T, is widely regarded as the program that proved a top-ranked, fully "
            "accredited CS master's could be delivered online at scale and at very low cost. "
            "Reviewers consistently praise its affordability (roughly $7,000 for the full "
            "degree versus $45,000+ on campus), the fact that the diploma is identical to the "
            "on-campus degree, and its flexibility for working professionals — while cautioning "
            "that the coursework is genuinely rigorous, time-intensive, and has a sub-50% "
            "completion rate."
        ),
        "themes": [
            {
                "label": "Exceptional affordability and ROI",
                "sentiment": "positive",
                "detail": "The complete degree costs about $7,000 — a fraction of comparable online CS master's at peer schools — with no 'online' label on the diploma.",
            },
            {
                "label": "Same credential, strong industry recognition",
                "sentiment": "positive",
                "detail": "Employers value the Georgia Tech CS name; alumni report roles at Google, Amazon, Microsoft, and Meta, and the program graduated 10,000+ alumni in its first decade.",
            },
            {
                "label": "Flexibility for working professionals",
                "sentiment": "positive",
                "detail": "Fully asynchronous; students take one to three courses per term and have up to six years to finish, making it compatible with full-time work.",
            },
            {
                "label": "Genuinely rigorous — high attrition",
                "sentiment": "caution",
                "detail": "Multiple reviewers note a graduation rate below 50% and 15–25 hours per week per course; it is not a credential mill and is not suited to everyone.",
            },
            {
                "label": "Variable course quality and support",
                "sentiment": "mixed",
                "detail": "Course quality and TA responsiveness vary; students rely on the OMSCentral review site and large peer/Slack communities to choose courses and stay on track.",
            },
        ],
        "sources": [
            {
                "label": "Forbes / OMSCS — program overview and cost",
                "url": "https://omscs.gatech.edu/",
            },
            {"label": "OMSCentral — student course reviews", "url": "https://www.omscentral.com/"},
            {
                "label": "The Wandering Engineer — comprehensive OMSCS review",
                "url": "https://thewanderingengineer.medium.com/georgia-tech-omscs-program-a-comprehensive-review-a588b570f4e4",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "gatech-online-ms-analytics": {
        "summary": (
            "Georgia Tech's Online MS in Analytics (OMS Analytics) is an interdisciplinary, fully "
            "online data-science degree drawing on the College of Computing, College of "
            "Engineering, and Scheller College of Business. Reviewers rate it among the best "
            "value graduate analytics programs in the country — a top-5-ranked degree for under "
            "about $12,000 total, with no GRE requirement and three specialization tracks — "
            "while noting that the curriculum is application-heavy, requires significant "
            "self-teaching, and has a high attrition rate."
        ),
        "themes": [
            {
                "label": "Top-ranked at a fraction of the cost",
                "sentiment": "positive",
                "detail": "A top-5 analytics program for roughly $10,000–$13,000 total tuition; reviewers repeatedly cite ROI far above bootcamps and $50k+ peer programs.",
            },
            {
                "label": "Breadth across computing, stats, and business",
                "sentiment": "positive",
                "detail": "Three tracks (Analytical Tools, Business Analytics, Computational Data Analytics) span machine learning, statistics, optimization, and business applications.",
            },
            {
                "label": "Flexible and career-changing",
                "sentiment": "positive",
                "detail": "Self-paced and online; reviewers describe meaningful career transitions into analytics and ML roles, often with employer tuition support.",
            },
            {
                "label": "Rigorous and self-directed",
                "sentiment": "caution",
                "detail": "Courses are demanding and require substantial independent learning; many courses need 14+ hours/week and the program has a high dropout rate.",
            },
            {
                "label": "Less computing depth than OMSCS",
                "sentiment": "mixed",
                "detail": "Some reviewers aiming for ML-engineering roles note OMSA carries less core computing/systems content than OMSCS and choose accordingly.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech Professional Education — OMS Analytics",
                "url": "https://pe.gatech.edu/degrees/analytics",
            },
            {
                "label": "The Data Generalist — OMSA review",
                "url": "https://thedatageneralist.com/omsa-review/",
            },
            {
                "label": "EnjoyMachineLearning — OMS Analytics review",
                "url": "https://enjoymachinelearning.com/blog/georgia-tech-oms-analytics-review/",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "gatech-mba": {
        "summary": (
            "The Scheller College of Business Full-Time MBA is a smaller, technology-focused "
            "program (about 145 students per class) in Atlanta's Tech Square, ranked No. 21 "
            "nationally (No. 6 among public schools) by U.S. News for 2025. It is best known for "
            "the strength and consistency of its Jones MBA Career Center — recognized by "
            "Poets&Quants as best-in-class — and for top-ranked specializations in business "
            "analytics, information systems, and operations. Reviewers note strong, resilient "
            "employment outcomes and ROI, while observing that the program is smaller and more "
            "regionally concentrated than the largest national brands and that 2024 reflected a "
            "tougher MBA job market."
        ),
        "themes": [
            {
                "label": "Best-in-class career services",
                "sentiment": "positive",
                "detail": "The Jones MBA Career Center pairs each student with a coach and deep employer ties; Poets&Quants named it a 2025 best-in-class career-services program.",
            },
            {
                "label": "Strong, resilient outcomes",
                "sentiment": "positive",
                "detail": "Class of 2024: 88.4% employed within three months at an average $146,260 and a $30,000 median signing bonus, after 96% / $154,679 for the Class of 2023.",
            },
            {
                "label": "Business-meets-technology positioning",
                "sentiment": "positive",
                "detail": "Tech Square location and top-ranked specializations (Business Analytics #3, Information Systems #5, Operations #5) suit tech, consulting, and analytics careers.",
            },
            {
                "label": "Smaller, more regional brand",
                "sentiment": "mixed",
                "detail": "At ~145 students the program is intimate but less nationally sprawling than top-10 brands, with placements concentrated in consulting, tech, and the Southeast.",
            },
            {
                "label": "Market sensitivity",
                "sentiment": "caution",
                "detail": "Coverage of the Class of 2024 framed Scheller's dip to 88.4% as a 'canary in the coal mine' for a tougher national MBA hiring market.",
            },
        ],
        "sources": [
            {
                "label": "Poets&Quants — Scheller College of Business profile",
                "url": "https://poetsandquants.com/school-profile/georgia-institute-of-technologys-scheller-college-of-business/",
            },
            {
                "label": "Poets&Quants — 2025 Best-in-Class Career Services: Scheller",
                "url": "https://poetsandquants.com/2025/11/18/2025-mba-best-in-class-award-for-career-services-georgia-tech-scheller/",
            },
            {
                "label": "Scheller — Full-Time MBA rises to No. 21 (U.S. News 2025)",
                "url": "https://www.scheller.gatech.edu/news/2025/georgia-tech-full-time-mba-no-21-evening-mba-no-10.html",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "gatech-computer-science-bs": {
        "summary": (
            "Georgia Tech's undergraduate BS in Computer Science is ranked among the very best in "
            "the country (No. 5 in U.S. News' undergraduate computer-science ranking) and is the "
            "Institute's largest and most sought-after major. Its distinctive 'Threads' "
            "curriculum lets students combine two of eight focus areas, and the program is "
            "consistently praised for academic strength, co-op/internship access, and employer "
            "demand — while students cite heavy workload, large class sizes, and intense "
            "competition as the trade-offs of its scale and rigor."
        ),
        "themes": [
            {
                "label": "Top-5 reputation and employer demand",
                "sentiment": "positive",
                "detail": "Ranked No. 5 for undergraduate CS by U.S. News; graduates are recruited heavily by major technology, finance, and aerospace employers.",
            },
            {
                "label": "Flexible 'Threads' curriculum",
                "sentiment": "positive",
                "detail": "Students combine two of eight threads (e.g., Intelligence, Systems & Architecture, People) to tailor the degree to their goals.",
            },
            {
                "label": "Strong experiential learning",
                "sentiment": "positive",
                "detail": "Georgia Tech's century-old co-op program and Atlanta tech ecosystem give CS students extensive internship and co-op access.",
            },
            {
                "label": "Heavy workload and rigor",
                "sentiment": "caution",
                "detail": "Students describe a demanding, fast-paced curriculum where strong time management is essential.",
            },
            {
                "label": "Scale and competition",
                "sentiment": "mixed",
                "detail": "As one of the largest CS programs in the country, popular courses are large and competitive, which some students find impersonal.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech — Rankings (U.S. News undergraduate CS No. 5)",
                "url": "https://www.gatech.edu/about/rankings",
            },
            {
                "label": "Georgia Tech College of Computing — BS in Computer Science",
                "url": "https://www.cc.gatech.edu/threads-better-way-learn-computing",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    # ── Depth-pass reviews (gatechreviews1) — each hand-gathered from program-specific
    # third-party coverage (U.S. News specialty ranks, official employment reports, QuantNet,
    # Financial Times, OMSCentral course reviews, College Factual, College Confidential),
    # summarizing praise AND common cautions, never synthesized from metadata. Programs with
    # no verifiable program-specific coverage (residential MSCS/MS-Cybersecurity, MCRP, MS
    # Public Policy, and the research MS/PhD tail) remain honestly recorded in _standard.omitted.
    "gatech-industrial-engineering-bs": {
        "summary": (
            "Georgia Tech's undergraduate industrial engineering program, in the H. Milton "
            "Stewart School of Industrial and Systems Engineering (ISyE), has been ranked No. 1 "
            "in the nation by U.S. News for 25 consecutive years (2026 edition) — the longest "
            "top-ranked run of any Georgia Tech program. Reviewers point to its broad, "
            "quantitative curriculum and unusually strong recruiting into consulting, analytics, "
            "supply-chain, and finance roles, while cautioning that the workload is demanding and "
            "the peer environment competitive."
        ),
        "themes": [
            {
                "label": "No. 1 undergraduate IE program for 25 straight years",
                "sentiment": "positive",
                "detail": "U.S. News has ranked ISyE's undergraduate program first in the nation for 25 consecutive years (2026), the field's longest continuous No. 1 streak.",
            },
            {
                "label": "Versatile, quantitative curriculum",
                "sentiment": "positive",
                "detail": "The degree's core in optimization, probability, statistics, and computing opens careers well beyond manufacturing — roughly 40% of graduates enter consulting, alongside analytics, supply-chain, and finance roles.",
            },
            {
                "label": "Strong recruiting and starting pay",
                "sentiment": "positive",
                "detail": "ISyE reports a median starting salary of $74,000 on its placement page and $82,000 with 88.5% of students holding an offer before graduation on its facts page; employers include McKinsey, Bain, Deloitte, Apple, Google, UPS, and Delta.",
            },
            {
                "label": "Demanding, fast-paced workload",
                "sentiment": "caution",
                "detail": "Advising write-ups describe a rigorous curriculum that requires disciplined time management to keep up with.",
            },
            {
                "label": "Prestige brings a competitive peer culture",
                "sentiment": "mixed",
                "detail": "The program's reputation draws high-achieving peers, so students describe a competitive atmosphere in which proactive networking matters.",
            },
        ],
        "sources": [
            {
                "label": "ISyE (CASE) — Undergraduate program ranked No. 1 for 2025",
                "url": "https://case.isye.gatech.edu/news/industrial-and-systems-engineering-undergraduate-program-ranked-no-1-nation-2025",
            },
            {
                "label": "Georgia Tech News — Multiple No. 1 rankings (ISyE undergrad, 25 straight years, 2026)",
                "url": "https://news.gatech.edu/news/2025/09/23/georgia-tech-secures-multiple-no-1-rankings",
            },
            {
                "label": "ISyE — Facts & Rankings (88.5% offer rate, $82,000 median)",
                "url": "https://www.isye.gatech.edu/about/school/facts-rankings",
            },
            {
                "label": "ISyE — BSIE Placement ($74,000 median; employer list)",
                "url": "https://isye.gatech.edu/academics/bachelors/industrial-engineering/placement",
            },
            {
                "label": "CollegeVine — Industrial Engineering at Georgia Tech (strengths and cautions)",
                "url": "https://www.collegevine.com/faq/39422/industrial-engineering-at-georgia-tech-any-pro-tips",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "gatech-industrial-engineering-ms": {
        "summary": (
            "Georgia Tech's graduate industrial engineering program (ISyE) has been ranked No. 1 "
            "in the nation by U.S. News for 35 consecutive years — the longest No. 1 streak in "
            "the discipline. Reviewers value its rigorous methodological core and broad employer "
            "pipeline, while noting selective admissions, a competitive peer culture, and that "
            "Georgia Tech publishes no program-specific salary data for the master's."
        ),
        "themes": [
            {
                "label": "No. 1 graduate IE program for 35 consecutive years",
                "sentiment": "positive",
                "detail": "U.S. News has ranked ISyE's graduate program first nationally for 35 straight years — the longest sustained No. 1 in the field.",
            },
            {
                "label": "Rigorous methodological core",
                "sentiment": "positive",
                "detail": "The curriculum is built on optimization, stochastic modeling, statistics, and computing, with specialization breadth across supply chain, analytics, and operations.",
            },
            {
                "label": "Broad employer pipeline",
                "sentiment": "positive",
                "detail": "The master's placement page lists employers spanning Apple, Boeing, Coca-Cola, Delta, Ford, Google, McKinsey, Nike, Tesla, and UPS.",
            },
            {
                "label": "Selective and competitive",
                "sentiment": "caution",
                "detail": "Georgia Tech notes applicants below a 3.0 GPA may find admission difficult, and the program's prestige fosters a competitive environment among peers.",
            },
            {
                "label": "No published master's-specific outcomes",
                "sentiment": "caution",
                "detail": "The school lists sample titles and employers but no master's-level salary or placement rate, so ROI must be weighed against the program's own cost pages.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech News — ISyE graduate No. 1, 35th consecutive year (2025)",
                "url": "https://www.gatech.edu/news/2025/04/08/h-milton-stewart-school-industrial-and-systems-engineering-graduate-program-ranked",
            },
            {
                "label": "Georgia Tech College of Engineering — Facts & Rankings (IE graduate No. 1, 2026)",
                "url": "https://coe.gatech.edu/about/facts-and-rankings",
            },
            {
                "label": "ISyE — MS in Industrial Engineering Placement (titles and employers)",
                "url": "https://www.isye.gatech.edu/academics/masters/ms-industrial-engineering/placement",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "gatech-aerospace-engineering-bs": {
        "summary": (
            "The Daniel Guggenheim School's undergraduate aerospace engineering program is ranked "
            "No. 2 in the nation and No. 1 among public universities for the 11th consecutive year "
            "(2026 U.S. News). Third-party outcome data reports a strong bachelor's median salary, "
            "though independent student-review coverage specific to the undergraduate program is "
            "limited."
        ),
        "themes": [
            {
                "label": "No. 2 undergraduate AE, No. 1 public",
                "sentiment": "positive",
                "detail": "U.S. News ranks the undergraduate aerospace program No. 2 nationally and No. 1 among public institutions for the 11th year running (2026).",
            },
            {
                "label": "Strong reported starting salary",
                "sentiment": "positive",
                "detail": "College Factual reports a bachelor's median salary near $101,367, placing the program #6 of 73 nationally and #1 in the Southeast by that source's methodology.",
            },
            {
                "label": "Math- and physics-heavy, demanding curriculum",
                "sentiment": "caution",
                "detail": "Aerospace engineering is a rigorous, technical major; prospective students should weigh the heavy coursework and the value of Georgia Tech's co-op pipeline.",
            },
            {
                "label": "Thin undergraduate-specific student reviews",
                "sentiment": "mixed",
                "detail": "Beyond rankings and outcome data, openly-published student-voice reviews specific to the BS are sparse, so campus visits and current-student conversations are worthwhile.",
            },
        ],
        "sources": [
            {
                "label": "Guggenheim School (AE) — Undergraduate program No. 2, No. 1 public (2026)",
                "url": "https://ae.gatech.edu/news/2025/09/aerospace-engineering-ranks-no-2-2026-undergraduate-rankings",
            },
            {
                "label": "College Factual — Georgia Tech Aerospace Engineering (bachelor's median $101,367)",
                "url": "https://www.collegefactual.com/colleges/georgia-institute-of-technology-main-campus/academic-life/academic-majors/engineering/aerospace-and-aeronautical-engineering/",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "gatech-aerospace-engineering-ms": {
        "summary": (
            "The Daniel Guggenheim School's graduate aerospace engineering program is ranked No. 2 "
            "in the nation (tied with Caltech, Purdue, and Stanford) and No. 1 among public "
            "universities (2025 U.S. News). It is a fast-growing, well-funded program, though the "
            "school is explicit that graduate funding, while common, is not guaranteed, and "
            "admission is selective."
        ),
        "themes": [
            {
                "label": "No. 2 graduate AE, No. 1 public",
                "sentiment": "positive",
                "detail": "U.S. News ranks the graduate aerospace program No. 2 nationally — tied with Caltech, Purdue, and Stanford — and No. 1 among public institutions (2025).",
            },
            {
                "label": "Rapidly growing, well-resourced program",
                "sentiment": "positive",
                "detail": "Graduate enrollment roughly doubled from about 490 to 900 students over five years, expanding research capacity across autonomy, space, and propulsion.",
            },
            {
                "label": "Funding is common but not guaranteed",
                "sentiment": "mixed",
                "detail": "Over 70% of AE graduate students held a GRA/GTA/fellowship as of Fall 2021, but the school states assistantships are limited and not guaranteed, especially in the first semester.",
            },
            {
                "label": "Selective admissions",
                "sentiment": "caution",
                "detail": "A recent cycle admitted roughly 304 of 652 applicants (~47%), and applicants report real rejections on GradCafe — the master's is not a safety admit.",
            },
        ],
        "sources": [
            {
                "label": "Guggenheim School (AE) — Remains No. 2 in 2025 graduate rankings",
                "url": "https://www.ae.gatech.edu/news/2025/04/ae-school-remains-no-2-2025-graduate-rankings",
            },
            {
                "label": "Guggenheim School (AE) — Graduate research & teaching funding (>70%, not guaranteed)",
                "url": "https://ae.gatech.edu/graduate-research-and-teaching-opportunities",
            },
            {
                "label": "Peterson's — Georgia Tech School of Aerospace Engineering (admissions funnel)",
                "url": "https://www.petersons.com/graduate-schools/georgia-institute-of-technology-college-of-engineering-school-of-aerospace-engineering-000_10029377.aspx",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "gatech-biomedical-engineering-bs": {
        "summary": (
            "The Wallace H. Coulter Department of Biomedical Engineering — a joint Georgia "
            "Tech/Emory program — is tied for No. 1 in the nation for undergraduate biomedical "
            "engineering (2026 U.S. News), and its graduate program also returned to No. 1 "
            "(tied with Johns Hopkins). Reviewers praise the engineering-plus-medicine partnership "
            "and outcomes, while raising the field-wide caution that BME bachelor's-only job "
            "prospects can be narrower than other engineering majors."
        ),
        "themes": [
            {
                "label": "Tied for No. 1 undergraduate BME",
                "sentiment": "positive",
                "detail": "U.S. News ties the Coulter Department for the No. 1 undergraduate biomedical engineering program nationally (2026); its graduate program is also No. 1, tied with Johns Hopkins.",
            },
            {
                "label": "Georgia Tech/Emory partnership",
                "sentiment": "positive",
                "detail": "The joint department pairs an engineering campus with a major medical school, and College Factual reports a bachelor's median salary near $89,405 with median debt around $22,750.",
            },
            {
                "label": "BME bachelor's job-market caution",
                "sentiment": "caution",
                "detail": "A widely-echoed field caution (seen on College Confidential) is that biomedical engineering bachelor's-only roles can be narrower than other engineering fields, so many graduates pursue graduate school or a second engineering skill.",
            },
            {
                "label": "Large cohort, pre-med-adjacent rigor",
                "sentiment": "mixed",
                "detail": "With roughly 1,100 undergraduates and a strong alumni network, the program is sizable but carries a demanding, science-heavy workload.",
            },
        ],
        "sources": [
            {
                "label": "GT Biomedical Engineering — Rankings & Academic Data (undergrad tied No. 1, 2026)",
                "url": "https://bme.gatech.edu/about-us/rankings-academic-data",
            },
            {
                "label": "College Factual — Georgia Tech Biomedical Engineering (bachelor's median $89,405)",
                "url": "https://www.collegefactual.com/colleges/georgia-institute-of-technology-main-campus/academic-life/academic-majors/engineering/biomedical-engineering/",
            },
            {
                "label": "College Confidential — Georgia Tech vs Duke for Biomedical Engineering",
                "url": "https://talk.collegeconfidential.com/t/georgia-tech-vs-duke-for-biomedical-engineering/2048015",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "gatech-mechanical-engineering-ms": {
        "summary": (
            "The George W. Woodruff School's graduate mechanical engineering program reached No. 3 "
            "nationally — its highest-ever ranking — and No. 1 among public universities in the "
            "2026 U.S. News graduate rankings. It is one of the largest ME programs in the country "
            "with broad research breadth, though Georgia Tech publishes no master's-specific "
            "outcome figures."
        ),
        "themes": [
            {
                "label": "Highest-ever No. 3 graduate ranking",
                "sentiment": "positive",
                "detail": "U.S. News ranked the Woodruff School's graduate mechanical engineering program No. 3 nationally in 2026 — its highest ever — and No. 1 among public universities.",
            },
            {
                "label": "Large program, wide research breadth",
                "sentiment": "positive",
                "detail": "With roughly 831 graduate students, the school spans robotics, energy, manufacturing, acoustics, and bioengineering research.",
            },
            {
                "label": "No published master's-specific outcomes",
                "sentiment": "caution",
                "detail": "Georgia Tech does not publish an MS-ME salary or placement rate, so prospective students should weigh cost and outcomes against the program's own pages.",
            },
            {
                "label": "Research-intensive, limited MS student reviews",
                "sentiment": "mixed",
                "detail": "The master's sits within a large, research-driven school; openly-published student-voice reviews specific to the MS are sparse.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech College of Engineering — Graduate programs, 2026 U.S. News (ME No. 3)",
                "url": "https://coe.gatech.edu/news/2026/04/engineering-grad-programs-remain-no-4-2026-rankings",
            },
            {
                "label": "Woodruff School of Mechanical Engineering — Program Facts (enrollment)",
                "url": "https://www.me.gatech.edu/program-facts",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "gatech-electrical-computer-engineering-ms": {
        "summary": (
            "Georgia Tech's School of Electrical and Computer Engineering is a top-tier ECE "
            "program — electrical engineering ranked No. 7 (No. 4 public) and computer engineering "
            "No. 5 (No. 2 public) in the 2026 U.S. News graduate rankings. It is one of the "
            "largest ECE schools in the U.S., but is explicit that master's funding is very "
            "limited and admission is capacity-constrained."
        ),
        "themes": [
            {
                "label": "Top-tier ECE rankings",
                "sentiment": "positive",
                "detail": "U.S. News ranks electrical engineering No. 7 (No. 4 public) and computer engineering No. 5 (No. 2 public) in its 2026 graduate rankings.",
            },
            {
                "label": "Large scale, deep research, GRE-optional",
                "sentiment": "positive",
                "detail": "One of the biggest ECE schools in the country — roughly 372 EE degrees awarded per year — with broad research breadth and no GRE requirement.",
            },
            {
                "label": "Master's funding is limited and not guaranteed",
                "sentiment": "caution",
                "detail": "The school states GTA/GRA funding is very limited and not guaranteed for MS students, who should have an alternative plan to fund the degree — most self-fund.",
            },
            {
                "label": "Capacity-limited admissions",
                "sentiment": "caution",
                "detail": "The school notes it denies admission to many excellent applicants because of program-capacity limits.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech School of ECE — Among top graduate programs, 2026 rankings",
                "url": "https://ece.gatech.edu/news/2026/04/ece-among-top-graduate-programs-2026-rankings",
            },
            {
                "label": "Georgia Tech School of ECE — Graduate Admissions (funding not guaranteed)",
                "url": "https://ece.gatech.edu/future-students/graduate-admissions",
            },
            {
                "label": "College Factual — Georgia Tech Electrical Engineering (372 master's/yr)",
                "url": "https://www.collegefactual.com/colleges/georgia-institute-of-technology-main-campus/academic-life/academic-majors/engineering/ee-electrical-engineering/",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "gatech-quantitative-computational-finance-ms": {
        "summary": (
            "Georgia Tech's MS in Quantitative and Computational Finance (QCF) — a joint program "
            "of Scheller, ISyE, and Mathematics — is ranked No. 8 nationally by QuantNet (2026) "
            "and No. 13 by TFE Times. It reports strong, transparent employment outcomes at public "
            "tuition, though the most recent cohort's placement softened and the curriculum is "
            "intensely quantitative."
        ),
        "themes": [
            {
                "label": "Top-10 financial engineering ranking",
                "sentiment": "positive",
                "detail": "QuantNet ranks QCF No. 8 nationally for 2026 (its second straight year at No. 8), and TFE Times ranks it No. 13.",
            },
            {
                "label": "Strong, transparently-reported outcomes",
                "sentiment": "positive",
                "detail": "Official statistics show 85–97% of graduates placed within three months across recent cohorts, with average first-year total compensation of roughly $134K–$148K at firms including Goldman Sachs, BlackRock, JPMorgan, and Millennium Management.",
            },
            {
                "label": "Exceptional ROI at public tuition",
                "sentiment": "positive",
                "detail": "The program pairs public-university tuition with six-figure quant-finance compensation, which Scheller highlights as an unusually strong return on investment.",
            },
            {
                "label": "Recent placement softened",
                "sentiment": "caution",
                "detail": "The most recent (Fall 2025) cohort's three-month placement dipped to 85%, down from 96–97% a couple of years earlier, reflecting a tighter quant-hiring market.",
            },
            {
                "label": "Intensely quantitative and coding-heavy",
                "sentiment": "caution",
                "detail": "The curriculum spans stochastic modeling, optimization, and programming, demanding strong mathematical and computational preparation.",
            },
        ],
        "sources": [
            {
                "label": "Scheller College of Business — QCF top-10 QuantNet ranking (No. 8, 2026)",
                "url": "https://www.scheller.gatech.edu/news/2025/georgia-tech-qcf-top-10-national-ranking.html",
            },
            {
                "label": "QCF — Employment Statistics by cohort (placement, salary, employers)",
                "url": "https://qcf.gatech.edu/careers/employment-stats",
            },
            {
                "label": "TFE Times — Best Financial Engineering Program Ranking (No. 13, 2026)",
                "url": "https://tfetimes.com/best-financial-engineering-program-ranking/",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "gatech-analytics-ms": {
        "summary": (
            "Georgia Tech's residential (on-campus) MS in Analytics is an interdisciplinary "
            "program across ISyE, Computing, and Scheller. Georgia Tech's business analytics is "
            "ranked No. 3 nationally by U.S. News (2025 specialty ranking), and the on-campus "
            "cohort reports strong official placement and salary outcomes — though it should not "
            "be confused with the much larger, low-cost Online MS Analytics."
        ),
        "themes": [
            {
                "label": "No. 3 business analytics ranking",
                "sentiment": "positive",
                "detail": "U.S. News ranks Georgia Tech's business analytics No. 3 nationally (2025), reflecting the strength of the interdisciplinary analytics faculty across ISyE, Computing, and Scheller.",
            },
            {
                "label": "Strong reported residential outcomes",
                "sentiment": "positive",
                "detail": "Official statistics show 84–100% of job-seeking residential graduates received full-time offers across 2021–2024, with average base salary near $113K in 2024 at employers including Amazon, Apple, Deloitte, Goldman Sachs, McKinsey, Microsoft, and Netflix.",
            },
            {
                "label": "Distinct from the online program",
                "sentiment": "mixed",
                "detail": "The small, full-time, in-person cohort is separate from the far larger and cheaper Online MS Analytics (OMS Analytics); the two differ sharply in scale, cost, and format.",
            },
            {
                "label": "Limited independent residential-specific reviews",
                "sentiment": "caution",
                "detail": "Most openly-published discussion concerns the online program, so third-party review coverage of the residential cohort specifically is thin.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech News — 2025 U.S. News graduate rankings (Business Analytics No. 3)",
                "url": "https://www.gatech.edu/news/2025/04/08/georgia-tech-shines-2025-us-news-graduate-program-rankings",
            },
            {
                "label": "MS in Analytics — Reports & Statistics (placement, salary, employers)",
                "url": "https://www.analytics.gatech.edu/inside-our-program/reports-statistics",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "gatech-mba-management-technology-executive": {
        "summary": (
            "The Scheller College of Business Executive MBA, with its Management of Technology "
            "specialization, ranked in the Financial Times' top 15 U.S. programs (2024). Alumni "
            "report strong salary gains, and student profiles praise the global capstone and "
            "weekend format, while noting the intensity of studying alongside a full-time job."
        ),
        "themes": [
            {
                "label": "Financial Times top-15 U.S. EMBA",
                "sentiment": "positive",
                "detail": "The Financial Times ranked Scheller's Executive MBA among the top 15 U.S. programs (2024), with a Management of Technology track covering emerging technology, change management, and technology forecasting.",
            },
            {
                "label": "Strong salary outcomes",
                "sentiment": "positive",
                "detail": "The Class of 2021 reported an average salary of $209,350 three years after graduation — a 47% average increase, per Financial Times data cited by Scheller.",
            },
            {
                "label": "Weekend format and hands-on capstone",
                "sentiment": "positive",
                "detail": "The 17-month Friday/Saturday format suits working professionals, and Poets&Quants student profiles describe the global capstone — solving real problems with real companies — as invaluable, hands-on experience.",
            },
            {
                "label": "Intensity of balancing work and study",
                "sentiment": "caution",
                "detail": "Students describe the constant reprioritization of a rigorous curriculum against a full-time job, and some wish for more depth in finance and strategy electives.",
            },
        ],
        "sources": [
            {
                "label": "Scheller College of Business — Financial Times ranks EMBA top 15 in the U.S.",
                "url": "https://www.scheller.gatech.edu/news/2024/the-financial-times-ranks-georgia-tech-executive-mba-top-15-in-the-us.html",
            },
            {
                "label": "Poets&Quants for Execs — Best & Brightest EMBA (Georgia Tech Scheller profile)",
                "url": "https://poetsandquantsforexecs.com/students/2025-best-brightest-executive-mba-isha-vasavada-georgia-tech-scheller/",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "gatech-human-computer-interaction-ms": {
        "summary": (
            "Georgia Tech's MS in Human-Computer Interaction (MS-HCI) is a distinctive "
            "interdisciplinary program spanning four schools, known for placing graduates into "
            "top UX and product roles. It is highly selective — the program states it admits fewer "
            "than 10% of applicants — and its placement report lists employers but no salary data."
        ),
        "themes": [
            {
                "label": "Interdisciplinary across four schools",
                "sentiment": "positive",
                "detail": "The degree spans Interactive Computing, Industrial Design, Literature/Media/Communication, and Psychology, producing versatile UX and product designers and researchers.",
            },
            {
                "label": "Strong UX and product placement",
                "sentiment": "positive",
                "detail": "The 2024 report lists 41 graduate placements at employers including Amazon, Microsoft, Duolingo, Palantir, SpaceX, Delta, and The Home Depot, and the program cites 200+ notable hiring organizations.",
            },
            {
                "label": "Highly selective admission",
                "sentiment": "caution",
                "detail": "The program states it admits fewer than 10% of applicants in recent cycles, turning away many qualified candidates.",
            },
            {
                "label": "No published compensation figures",
                "sentiment": "caution",
                "detail": "The placement report lists employers and titles but no salary figures or aggregate placement rate, so compensation must be researched separately.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech MS-HCI — 2024 Graduate Placement Report",
                "url": "https://mshci.gatech.edu/news/2024-graduate-placement-report",
            },
            {
                "label": "Georgia Tech MS-HCI — Career Outcomes (200+ employers)",
                "url": "https://mshci.gatech.edu/program/career-outcomes",
            },
            {
                "label": "Georgia Tech MS-HCI — Admissions FAQ (<10% acceptance)",
                "url": "https://medium.com/georgia-tech-mshci/georgia-techs-ms-hci-program-some-frequently-asked-questions-about-program-admissions-d25f3a03d5c",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "gatech-online-ms-cybersecurity": {
        "summary": (
            "Georgia Tech's Online MS in Cybersecurity (OMS Cybersecurity) delivers an accredited "
            "master's fully online for under $12,000 total — a fraction of comparable programs. "
            "OMSCentral course reviews praise its hands-on, project-based courses but recurringly "
            "criticize minimal instructor presence and variable teaching support, making it best "
            "suited to disciplined, self-directed learners."
        ),
        "themes": [
            {
                "label": "Exceptional affordability, fully online",
                "sentiment": "positive",
                "detail": "Total tuition is under $12,000 ($369 per credit-hour × 32 credits), delivered 100% online over two to three years (extendable to six).",
            },
            {
                "label": "Hands-on, project-based courses",
                "sentiment": "positive",
                "detail": "Core courses such as Introduction to Information Security (rated 3.44/5 on OMSCentral) use capture-the-flag-style assignments that students find engaging and practical.",
            },
            {
                "label": "Minimal instructor presence in some courses",
                "sentiment": "caution",
                "detail": "A recurring OMSCentral criticism is that some core courses have little instructor involvement — lectures that don't track the projects — pushing students onto peer forums and self-study.",
            },
            {
                "label": "Variable TA and course quality",
                "sentiment": "mixed",
                "detail": "Support and course quality vary widely across the catalog, so students lean on OMSCentral reviews to choose courses carefully.",
            },
            {
                "label": "Rewards self-directed learners",
                "sentiment": "caution",
                "detail": "The asynchronous, self-paced format suits disciplined, independent learners rather than those wanting structured guidance.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech Professional Education — Online MS Cybersecurity (cost, format)",
                "url": "https://pe.gatech.edu/degrees/cybersecurity",
            },
            {
                "label": "OMSCentral — Introduction to Information Security (CS-6035) reviews",
                "url": "https://www.omscentral.com/courses/introduction-to-information-security/reviews",
            },
            {
                "label": "School of Cybersecurity and Privacy — Graduate Programs (tracks)",
                "url": "https://scp.cc.gatech.edu/graduate-programs",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "gatech-supply-chain-engineering-ms": {
        "summary": (
            "Georgia Tech's MS in Supply Chain Engineering is a specialized one-year master's from "
            "the No. 1-ranked H. Milton Stewart School of ISyE, focused specifically on designing "
            "and optimizing global supply chains. It feeds a strong named employer pipeline in "
            "logistics and operations, though it is a small, niche program with limited independent "
            "review coverage."
        ),
        "themes": [
            {
                "label": "Specialized supply-chain master's from the No. 1 ISyE",
                "sentiment": "positive",
                "detail": "The one-year degree comes from the top-ranked ISyE and concentrates on supply-chain optimization and logistics, distinct from the broader MS in Industrial Engineering.",
            },
            {
                "label": "Strong named employer pipeline",
                "sentiment": "positive",
                "detail": "The program's placement page lists supply-chain and logistics employers including Amazon, FedEx, UPS, Maersk, DHL, Intel, Coca-Cola, and The Home Depot.",
            },
            {
                "label": "Intensive one-year, Atlanta-only format",
                "sentiment": "mixed",
                "detail": "The fast-paced Fall–Spring–Summer program runs only on the Atlanta campus and is aimed at business-savvy engineers ready for a demanding pace.",
            },
            {
                "label": "Niche program, limited public outcome data",
                "sentiment": "caution",
                "detail": "It is a small, specialized program; Georgia Tech publishes no SCE-specific salary or placement rate and independent third-party reviews are sparse, so outcomes should be verified case by case.",
            },
        ],
        "sources": [
            {
                "label": "ISyE — MS in Supply Chain Engineering (format, employers)",
                "url": "https://www.isye.gatech.edu/academics/masters/degrees/ms-supply-chain-engineering",
            },
            {
                "label": "Georgia Tech Supply Chain & Logistics Institute — MS Supply Chain Engineering",
                "url": "https://www.scl.gatech.edu/ms-supply-chain-engineering",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
}


def apply(session: Session) -> bool:
    """Enrich Georgia Tech to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Georgia Tech is absent — safe on fresh/CI databases.
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
    inst.founded_year = 1885
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.gatech.edu"
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
        # Every college gets a working feed (the verified GT news RSS filtered to college-
        # relevant items by keywords) so its Events & Updates tab populates.
        sc.content_sources = _school_content(spec["name"])
        by_name[spec["name"]] = sc
    # Drop legacy schools — programs.school_id is ON DELETE SET NULL, so this is FK-safe.
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


def _program_standard(slug: str, spec: dict | None = None) -> dict:
    """Per-program omitted-field list (verified-unavailable), for _standard."""
    if spec is None:
        spec = _SPEC_BY_SLUG.get(slug, {})
    omitted: list[str] = []
    # GT publishes no per-program top-industries split (career outcomes are reported by degree
    # level institution-wide), so every program except the Scheller MBA omits top_industries.
    if slug != "gatech-mba":
        omitted.append("outcomes_data.top_industries")
    # PhD job-acceptance rate is not reported at degree level, so doctoral programs omit it.
    if spec.get("degree_type") == "phd":
        omitted.append("outcomes_data.employment_rate")
    # Graduate/professional programs without a verified per-program tuition omit tuition_usd
    # (their cost_data carries a sourced "see the program page" record instead).
    if spec.get("degree_type") != "bachelors":
        cost = _COST_BY_SLUG.get(slug) or _grad_cost(spec)
        if cost.get("tuition_usd") is None:
            omitted.append("cost_data.tuition_usd")
    if slug not in _TRACKS_BY_SLUG:
        omitted.append("tracks")
    if slug not in _CLASS_PROFILE_BY_SLUG:
        omitted.append("class_profile.cohort_size")
    if slug not in _FACULTY_BY_SLUG:
        omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    if not spec.get("cip"):
        omitted.append("cip_code")
    # content_sources is set on every program (college feed + program keywords), never omitted.
    return _standard(omitted)


def _matcher_tuition(cost: dict) -> int | None:
    """The scalar ``program.tuition`` the CPEF matcher reads for its budget veto.

    Georgia Tech is a PUBLIC university, so it publishes two residency stickers. The matcher
    budget feature reads the flat ``program.tuition`` scalar (not the residency-aware net-price
    estimator), so for the out-of-state + international applicant pool — the majority at a
    flagship public — the conservative, broadly-correct budget input is the NON-RESIDENT rate
    (REPAIR_BACKLOG #2 / enrich-profile public non-resident-tuition rule). When a cost record
    carries a residency breakdown, expose the out-of-state figure; otherwise (residency-flat
    online/professional totals, funded doctorates) fall back to the published scalar. The
    honest in-state rate is always preserved in ``cost_data.breakdown``.
    """
    breakdown = cost.get("breakdown") or {}
    oos = breakdown.get("tuition_out_of_state")
    if oos is not None:
        return oos
    return cost.get("tuition_usd")


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
        p.delivery_format = spec.get("delivery_format", "in_person")
        _kw = _PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(
            _SCHOOL_FEED_SPEC[spec["school"]]["keywords"]
        )
        p.content_sources = _program_content(spec["school"], _kw)
        # Cost precedence: published GT undergraduate rates for bachelor's → a verified
        # per-program graduate tuition → a sourced "see the program page" record.
        if spec["degree_type"] == "bachelors":
            p.cost_data = {
                "tuition_usd": _TUITION_UG_IN_STATE,
                "total_cost_of_attendance": _UNDERGRAD_COA,
                "avg_net_price": _AVG_NET_PRICE,
                "breakdown": {
                    "tuition_in_state": _TUITION_UG_IN_STATE,
                    "tuition_out_of_state": _TUITION_UG_OUT_STATE,
                    "total_cost_of_attendance_in_state": _UNDERGRAD_COA,
                },
                "funded": False,
                "note": (
                    "Published 2024-25 Georgia Tech undergraduate tuition: $10,512 in-state / "
                    "$32,938 out-of-state (plus ~$1,546 required fees). College Scorecard "
                    "in-state cost of attendance ≈ $28,167; average net price ≈ $12,116."
                ),
                "source": _COST_SRC[0],
                "source_url": _COST_SRC[1],
                "year": "2024-25",
            }
        else:
            cost_override = _COST_BY_SLUG.get(slug)
            if cost_override is not None:
                p.cost_data = cost_override
            else:
                p.cost_data = _grad_cost(spec)
        # The matcher's budget scalar is the NON-RESIDENT sticker for this public university
        # (REPAIR_BACKLOG #2); the in-state rate stays in cost_data.breakdown.
        p.tuition = _matcher_tuition(p.cost_data)
        p.application_requirements = _requirements_for(spec)
        if slug == "gatech-mba":
            outcomes = dict(_MBA_OUTCOMES)
        else:
            outcomes = _outcomes_for(spec["degree_type"])
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        # who_its_for is a UNIVERSAL depth field — never hard-null it (that bakes the 0% starvation
        # into the build and reverts any value on every replace=True re-apply); fill the
        # program-distinct statement researched per program.
        p.who_its_for = _WHO_BY_SLUG[slug]
        p.highlights = None
        p.application_deadline = date(2027, 1, 4) if spec["degree_type"] == "bachelors" else None
    session.flush()
    # Reconcile legacy GT programs (slug not in the canonical set): delete when unreferenced,
    # otherwise unpublish so the catalog stays clean without breaking any application/match rows.
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
