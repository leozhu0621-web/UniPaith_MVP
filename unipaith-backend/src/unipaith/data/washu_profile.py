"""Washington University in St. Louis — gold-standard profile (institution + schools + catalog).

Every value below is verified against an authoritative source (WashU's official pages —
washu.edu, The Source [source.washu.edu], the undergraduate bulletin at bulletin.wustl.edu,
each school's site, the Office of Student Financial Aid / Registrar — the U.S. Dept. of
Education College Scorecard / NCES for UNITID 179867, and the ranking bodies) and carries a
citation, or is honestly omitted (recorded in that node's ``_standard.omitted``) — never
guessed.

Scope note: WashU entered as a 5-stub institution seed (the 2026-06 US-News bulk seed)
whose five programs ALL shipped with an EMPTY ``description_text`` — a blank student page
and zero matcher embedding (REPAIR_BACKLOG run 85 entry #2, a worst-tier open defect; the
sibling Georgetown seed was cleared by #1169 this cycle). This pass (2026-06-26) takes the
institution to gold (filling the seed's missing report-card / admissions-funnel / diversity
/ cost-aid / campus-resources fields and adding a verified 4th campus photo) and REPLACES
the five empty stubs with a verified, real-named catalog across WashU's degree-granting
schools — the College of Arts & Sciences, the McKelvey School of Engineering, Olin Business
School, the Sam Fox School of Design & Visual Arts, the Brown School, the School of Law, the
School of Medicine, and the Graduate School of Arts & Sciences.

Every program carries a researched, field-specific ``description_text`` (anti-stub clean,
gold contrast), a ``who_its_for`` statement, a real owning ``department``, a ``cip_code``,
a verified ``delivery_format``, published tuition per credential level (never the
undergraduate sticker copied onto a graduate row — funded PhDs carry funded=True /
tuition=None; programs whose annual figure is not separately published omit-with-reason),
working WashU news feeds, and sourced ``external_reviews`` on the coverable flagships
(Olin MBA, the Olin MS in Finance and MS in Business Analytics, the Brown School MSW, the
J.D., and the M.D.). Nothing is padded.

Tuition (verified WashU "The Source" + each school): undergraduate sticker $68,240; Arts &
Sciences / McKelvey Engineering graduate $66,850; Olin Full-Time MBA $70,250; School of
Medicine M.D. $67,968 (fixed across four years); School of Law J.D. $72,792; Brown School
M.S.W. $49,210. The 2026-06-30 pass closes the last matcher-core tuition gap — Olin's two
specialized master's, billed per program rather than in the university release, now carry
their published per-program rate (MS in Finance $81,500, Corporate Finance one-year track;
MS in Business Analytics $67,866 academic-year, of a $101,799 three-semester program;
Olin Cost-Aid-Scholarships pages) instead of an omit-with-reason. Graduate-School-of-Arts-&-
Sciences doctorates are funded (tuition waived for funded PhD students), so they carry
funded=True + tuition=None.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Washington University in St Louis"

ENRICHED_AT = "2026-06-30"


def _standard(omitted: list[str] | None = None) -> dict:
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }


_OMITTED_INSTITUTION: list[str] = [
    # The student-faculty ratio is published; a single current instructional-faculty
    # headcount could not be verified this session, so the count is omitted, not guessed.
    "school_outcomes.scale.faculty_count",
    # WashU's Center for Career Engagement publishes a First Destination Survey with a 90%
    # knowledge rate, but the headline employed-or-continuing-education percentage is shown
    # only in an interactive dashboard, not as a single citable static figure, so both
    # outcomes fields are omitted rather than approximated; median earnings are provided.
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
]

# ── Institution-level data ────────────────────────────────────────────────
RANKING_DATA: dict = {
    "ownership_type": "private",
    # Higher Learning Commission (WashU's regional accreditor).
    "accreditor": "HLC",
    "carnegie_classification": "Doctoral Universities: Very High Research Activity (R1)",
    # QS World University Rankings 2026.
    "qs_world_university_rankings": {"rank": 167, "year": 2026},
    # THE World University Rankings 2026.
    "times_higher_education": {"rank": 67, "year": 2026},
    # U.S. News Best Colleges (National Universities) 2026: #20 nationally.
    "us_news_national": {"rank": 20, "year": 2026},
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.1206,
    "avg_net_price": 21786,
    "median_earnings_10yr": 86182,
    # NCES / WashU CDS — six-year graduation rate.
    "graduation_rate_6yr": 0.945,
    # WashU CDS 2024-25 — first-year retention.
    "retention_rate_first_year": 0.959,
    # WashU CDS 2024-25 — SAT/ACT middle ranges of enrolled first-years who submitted scores.
    "test_scores": {
        "sat_total_25_75": [1500, 1570],
        "act_25_75": [33, 35],
        "source": "Washington University Common Data Set 2024-25",
        "source_url": "https://washu.edu/app/uploads/2025/06/2024-2025-WashU-CDS.pdf",
    },
    # Undergraduate race/ethnicity (IPEDS-based aggregation). Categories do not sum to 100%
    # (two-or-more-races and not-reported make up the remainder).
    "demographics": {
        "white": 0.415,
        "asian": 0.202,
        "hispanic": 0.125,
        "black": 0.095,
        "international": 0.085,
        "note": (
            "Undergraduate race/ethnicity (IPEDS-based); two-or-more-races and "
            "not-reported make up the remainder, so shares do not sum to 100%."
        ),
        "source": "College Factual / IPEDS — WashU undergraduate diversity",
        "source_url": (
            "https://www.collegefactual.com/colleges/"
            "washington-university-in-st-louis/student-life/diversity/"
        ),
    },
    "financial_aid": {
        # WashU Registrar — Fall 2025 share of undergraduates receiving Pell grants.
        "pell_grant_rate": 0.22,
        # WashU Office of Student Financial Aid — 2025-26 total cost of attendance
        # (first-year, on-campus): tuition + fees + housing + meals + personal expenses.
        "cost_of_attendance": 94760,
        "source": "WashU Office of Student Financial Aid — 2025-26 cost of attendance",
        "source_url": "https://financialaid.washu.edu/costs/",
    },
    "research": {
        "labs": [
            "Siteman Cancer Center",
            "McDonnell Genome Institute",
            "Edison Family Center for Genome Sciences & Systems Biology",
            "Institute for Public Health",
            "Mildred Lane Kemper Art Museum",
        ],
        "areas": [
            "Genomics & genome sciences",
            "Cancer biology & oncology",
            "Public & global health",
            "Neuroscience & brain sciences",
            "Energy, environment & sustainability",
            "Design & the visual arts",
        ],
        "lab_links": {
            "Siteman Cancer Center": "https://siteman.wustl.edu/",
            "McDonnell Genome Institute": "https://www.genome.wustl.edu/",
            "Institute for Public Health": "https://publichealth.wustl.edu/",
            "Mildred Lane Kemper Art Museum": "https://www.kemperartmuseum.wustl.edu/",
        },
        "source": "Washington University in St. Louis — research",
        "source_url": "https://research.washu.edu/",
    },
    "scale": {
        # NCES / WashU (Fall 2024) total + undergraduate enrollment.
        "total_enrollment": 16399,
        "undergraduate_enrollment": 8220,
        # WashU CDS 2024-25 — undergraduate student-faculty ratio.
        "student_faculty_ratio": "7:1",
        "research_centers": [
            "Siteman Cancer Center",
            "McDonnell Genome Institute",
            "Institute for Public Health",
        ],
    },
    "campus_life": {
        # WashU's teams (the Bears) compete in NCAA Division III (University Athletic Assn).
        "athletics_division": "NCAA Division III (University Athletic Association)",
        "mascot": "WashU Bears",
        "housing": "Residential Danforth Campus in St. Louis, Missouri",
        "resources": [
            {"label": "WashU Bears Athletics", "url": "https://washubears.com/"},
            {"label": "University Libraries", "url": "https://library.washu.edu/"},
            {"label": "Mildred Lane Kemper Art Museum", "url": "https://www.kemperartmuseum.wustl.edu/"},
            {"label": "Center for Career Engagement", "url": "https://careers.washu.edu/"},
        ],
    },
    "flagship": {
        "enrollment_total": 16399,
        # Undergraduate Class of 2028 admissions funnel (WashU).
        "applicants": 32754,
        "admits": 3951,
        "admissions_cycle": "Class of 2028 (entering fall 2024; WashU)",
        "founded_year": 1853,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (WashU, UNITID 179867)",
            "url": "https://collegescorecard.ed.gov/school/?179867",
        },
        {
            "label": "NCES College Navigator — Washington University in St. Louis (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=179867",
        },
        {
            "label": "WashU — 2025-26 tuition, housing, meal plans, fees (The Source)",
            "url": "https://source.washu.edu/2025/03/2025-26-tuition-housing-meal-plans-fees-announced/",
        },
        {
            "label": "Washington University Common Data Set 2024-25",
            "url": "https://washu.edu/app/uploads/2025/06/2024-2025-WashU-CDS.pdf",
        },
        {
            "label": "QS World University Rankings 2026 — Washington University in St. Louis",
            "url": "https://www.topuniversities.com/universities/washington-university-st-louis",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — WashU",
            "url": (
                "https://www.timeshighereducation.com/world-university-rankings/"
                "washington-university-st-louis"
            ),
        },
        {
            "label": "U.S. News Best Colleges 2026 — WashU (#20 National Universities)",
            "url": "https://www.usnews.com/best-colleges/washington-university-in-st-louis-2520",
        },
    ],
}

UNDERGRAD_COUNT = 8220

DESCRIPTION = (
    "Washington University in St. Louis is a private research university in St. Louis, "
    "Missouri, founded in 1853. A member of the Association of American Universities, it "
    "enrolls about 8,200 undergraduates and some 8,000 graduate and professional students "
    "— roughly 16,400 in all — with a 7:1 student-faculty ratio, and is classified as a "
    "Carnegie R1 very-high-research-activity university.\n\n"
    "WashU is organized into schools spanning the arts and sciences, engineering, "
    "business, design and the visual arts, social work and public health, law, and "
    "medicine: the undergraduate-anchored College of Arts & Sciences, the McKelvey School "
    "of Engineering, Olin Business School, the Sam Fox School of Design & Visual Arts, the "
    "Brown School, the School of Law, the nationally prominent School of Medicine, and the "
    "Graduate School of Arts & Sciences. Its research is anchored by the Siteman Cancer "
    "Center, the McDonnell Genome Institute, and a deep strength in genomics and the "
    "biomedical sciences.\n\n"
    "Accredited by the Higher Learning Commission, WashU ranks No. 20 among national "
    "universities by U.S. News, No. 67 in the world by Times Higher Education, and No. 167 "
    "by QS. It admitted about 12% of applicants to the undergraduate Class of 2028, "
    "graduates about 95% of its undergraduates, and is among the nation's best-endowed "
    "universities.\n\n"
    "WashU's published 2025-26 undergraduate tuition is $68,240, with an average net price "
    "of about $22,000 after aid; about 22% of undergraduates receive Pell grants. Its "
    "teams, the Bears, compete in NCAA Division III in the University Athletic Association."
)

# ── The real degree-granting schools (display order) ───────────────────────
_ARTSCI = "College of Arts & Sciences"
_MCKELVEY = "McKelvey School of Engineering"
_OLIN = "Olin Business School"
_SAMFOX = "Sam Fox School of Design & Visual Arts"
_BROWN = "Brown School"
_LAW = "School of Law"
_MEDICINE = "School of Medicine"
_GRAD = "Graduate School of Arts & Sciences"

_SCHOOL_WEBSITE: dict[str, str] = {
    _ARTSCI: "https://artsci.washu.edu/",
    _MCKELVEY: "https://engineering.washu.edu/",
    _OLIN: "https://olin.washu.edu/",
    _SAMFOX: "https://samfoxschool.washu.edu/",
    _BROWN: "https://brownschool.washu.edu/",
    _LAW: "https://law.washu.edu/",
    _MEDICINE: "https://medicine.washu.edu/",
    _GRAD: "https://gradstudies.artsci.washu.edu/",
}

SCHOOLS: list[dict] = [
    {
        "name": _ARTSCI,
        "sort_order": 1,
        "description": (
            "The College of Arts & Sciences is WashU's founding undergraduate school, "
            "teaching the liberal arts across the humanities, the natural and physical "
            "sciences, and the social sciences. It awards the A.B. and B.S. across dozens "
            "of majors and houses the departments behind most of WashU's doctoral programs."
        ),
    },
    {
        "name": _MCKELVEY,
        "sort_order": 2,
        "description": (
            "The McKelvey School of Engineering offers a broad, research-intensive "
            "engineering education spanning biomedical, computer, electrical, mechanical, "
            "and systems engineering and computer and data science, awarding the B.S. "
            "through graduate degrees with strength in biomedical and data-driven fields."
        ),
    },
    {
        "name": _OLIN,
        "sort_order": 3,
        "description": (
            "Olin Business School educates undergraduates and graduate students in "
            "management, awarding the Bachelor of Science in Business Administration "
            "alongside the MBA and specialized master's degrees in finance and analytics, "
            "with an experiential, globally connected curriculum."
        ),
    },
    {
        "name": _SAMFOX,
        "sort_order": 4,
        "description": (
            "The Sam Fox School of Design & Visual Arts unites architecture, art, and "
            "design with the Mildred Lane Kemper Art Museum, awarding undergraduate and "
            "graduate degrees in architecture, studio art, and communication and "
            "industrial design in a single creative community."
        ),
    },
    {
        "name": _BROWN,
        "sort_order": 5,
        "description": (
            "The Brown School is WashU's school of social work, public health, and social "
            "policy, awarding the Master of Social Work — among the top-ranked in the "
            "country — alongside public-health and policy degrees grounded in research and "
            "field practice."
        ),
    },
    {
        "name": _LAW,
        "sort_order": 6,
        "description": (
            "The School of Law awards the Juris Doctor and graduate legal degrees, pairing "
            "a strong doctrinal and clinical curriculum with offerings in intellectual "
            "property, dispute resolution, and public-interest law."
        ),
    },
    {
        "name": _MEDICINE,
        "sort_order": 7,
        "description": (
            "The School of Medicine is one of the nation's leading academic medical "
            "centers, awarding the Doctor of Medicine and biomedical doctorates and "
            "training physicians and scientists with the BJC HealthCare hospitals and a "
            "deep research base in genomics."
        ),
    },
    {
        "name": _GRAD,
        "sort_order": 8,
        "description": (
            "The Graduate School of Arts & Sciences administers WashU's PhD and academic "
            "master's programs across the humanities, the natural and physical sciences, "
            "and the social sciences, with full funding for its doctoral students."
        ),
    },
]

_ABOUT_DETAIL: dict[str, dict] = {
    _ARTSCI: {
        "founded": "1853 (WashU's founding college)",
        "research_centers": [
            "Institute for Public Health",
            "McDonnell Center for the Space Sciences",
        ],
    },
    _MCKELVEY: {
        "founded": "1854",
        "research_centers": [
            "Institute of Materials Science & Engineering",
            "Center for Biological Systems Engineering",
        ],
    },
    _OLIN: {"founded": "1917"},
    _SAMFOX: {
        "founded": "2005 (uniting WashU's architecture and art schools)",
        "research_centers": ["Mildred Lane Kemper Art Museum"],
    },
    _BROWN: {
        "founded": "1925",
        "research_centers": ["Center for Social Development", "Institute for Public Health"],
    },
    _LAW: {"founded": "1867"},
    _MEDICINE: {
        "founded": "1891",
        "research_centers": ["Siteman Cancer Center", "McDonnell Genome Institute"],
    },
    _GRAD: {"founded": "1853"},
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
# Each feed below was fetched live this session (verified 2026-06-26). The university-wide
# "The Source" newsroom feed is the institution feed and the shared feed for schools without
# their own working feed; the Brown School and School of Medicine carry their own working
# WordPress feeds.
_SOURCE_RSS = "https://source.washu.edu/feed/"
_SCHOOL_RSS: dict[str, str] = {
    _ARTSCI: _SOURCE_RSS,
    _MCKELVEY: _SOURCE_RSS,
    _OLIN: _SOURCE_RSS,
    _SAMFOX: _SOURCE_RSS,
    _BROWN: "https://brownschool.washu.edu/feed/",
    _LAW: _SOURCE_RSS,
    _MEDICINE: "https://medicine.washu.edu/feed/",
    _GRAD: _SOURCE_RSS,
}

_SOCIAL_WASHU = {
    "instagram": "https://www.instagram.com/washu/",
    "linkedin": "https://www.linkedin.com/school/washuniversity/",
    "x": "https://twitter.com/WashU",
    "youtube": "https://www.youtube.com/user/WUSTLnews",
    "facebook": "https://www.facebook.com/WashingtonUniversity",
}

_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _ARTSCI: ["Arts & Sciences", "undergraduate", "faculty"],
    _MCKELVEY: ["McKelvey", "engineering", "engineers"],
    _OLIN: ["Olin", "business", "MBA"],
    _SAMFOX: ["Sam Fox", "architecture", "art"],
    _BROWN: ["Brown School", "social work", "public health"],
    _LAW: ["law", "legal", "School of Law"],
    _MEDICINE: ["medicine", "medical", "Siteman"],
    _GRAD: ["graduate", "PhD", "research"],
}


def _school_content(name: str) -> dict:
    return {
        "news_rss": _SCHOOL_RSS[name],
        "news_url": "https://source.washu.edu/",
        "news_curated": False,
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": _SOCIAL_WASHU,
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


_INSTITUTION_CONTENT: dict = {
    "news_rss": _SOURCE_RSS,
    "news_url": "https://source.washu.edu/",
    "news_curated": True,
    "social": _SOCIAL_WASHU,
}

# ── Tuition constants (all verified 2025-26, WashU "The Source" + schools) ──
_UG_TUITION = 68240
_UG_NET_PRICE = 21786
_COST_SRC = (
    "WashU — 2025-26 tuition (The Source); College Scorecard net price",
    "https://source.washu.edu/2025/03/2025-26-tuition-housing-meal-plans-fees-announced/",
)
_AS_ENG_GRAD = 66850  # Arts & Sciences / McKelvey Engineering graduate tuition
_MBA_FT = 70250  # Olin Full-Time MBA
_MD = 67968  # School of Medicine M.D. (fixed across four years)
_JD = 72792  # School of Law J.D.
_MSW = 49210  # Brown School Master of Social Work
_MARCH = 60975  # Sam Fox Master of Architecture (2025-26 published annual rate)
_MFA = 50680  # Sam Fox Master of Fine Arts (2025-26 published annual rate)
_MPH = 43710  # Brown School Master of Public Health (2025-26 published annual rate)
_LLM = 72792  # School of Law LL.M. (2025-26, grouped with J.D./J.S.D./M.L.S.)
_GRAD_SRC = (
    "WashU — 2025-26 graduate/professional tuition (The Source)",
    "https://source.washu.edu/2025/03/2025-26-tuition-housing-meal-plans-fees-announced/",
)
_OLIN_SRC = (
    "WashU Olin Business School — 2025-26 Full-Time MBA cost",
    "https://olin.washu.edu/programs/mbas/full-time-mba/cost-aid-scholarships.php",
)
# Olin specialized-master's tuition, published per program on each program's Cost, Aid &
# Scholarships page (billed at a flat per-semester rate). The matcher reads the flat annual
# scalar, so each carries a standard two-semester academic-year figure; the per-semester
# rate and full multi-semester program total are stated in the cost note.
_MSF = 81500  # MS in Finance — Corporate Finance track (2 semesters = 1 academic year total)
_OLIN_MSF_SRC = (
    "WashU Olin Business School — MS in Finance Cost, Aid & Scholarships (2026-27)",
    "https://olin.washu.edu/programs/specialized-masters/ms-in-finance/cost-aid-scholarships.php",
)
_MSBA = 67866  # MS in Business Analytics — 2 semesters (of the 3-semester program) at $33,933
_OLIN_MSBA_SRC = (
    "WashU Olin Business School — MS in Business Analytics Cost, Aid & Scholarships",
    "https://olin.washu.edu/programs/specialized-masters/ms-in-business-analytics/"
    "cost-aid-scholarships.php",
)
_OLIN_RANK_SRC = (
    "WashU Olin Business School — Accreditation & Rankings",
    "https://olin.washu.edu/about/why-olin/accreditation-rankings.php",
)
_MED_SRC = (
    "WashU School of Medicine — 2025-26 M.D. tuition",
    "https://medicine.washu.edu/",
)
_LAW_SRC = (
    "WashU School of Law — 2025-26 J.D. tuition",
    "https://law.washu.edu/",
)
_BROWN_SRC = (
    "WashU Brown School — 2025-26 M.S.W. tuition",
    "https://brownschool.washu.edu/admissions-aid/tuition-and-fees/",
)

# ── The catalog ────────────────────────────────────────────────────────────
_A = _ARTSCI

_CATALOG: list[dict] = [
    # ───────────── College of Arts & Sciences ─────────────
    dict(
        slug="washu-anthropology-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Anthropology",
        department="Department of Anthropology", cip="45.02", duration_months=48,
        keywords=["anthropology"],
        description=(
            "Anthropology at WashU studies human societies across cultural, biological, and "
            "archaeological subfields, pairing ethnographic and laboratory research with a "
            "global-health specialization option."
        ),
        who_its_for=(
            "Students curious about human cultures, evolution, and health who want research "
            "experience and a flexible path into medicine, law, or the social sciences."
        ),
    ),
    dict(
        slug="washu-art-history-archaeology-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Art History and Archaeology",
        department="Department of Art History and Archaeology", cip="50.07", duration_months=48,
        keywords=["art history", "archaeology"],
        description=(
            "Art history and archaeology examines visual culture and material remains from "
            "antiquity to the present, drawing on the Kemper Art Museum and Saint Louis "
            "Art Museum for object-based study."
        ),
        who_its_for=(
            "Students drawn to art and the material past who want museum-based study toward "
            "curation, conservation, or graduate work."
        ),
    ),
    dict(
        slug="washu-biology-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Biology",
        department="Department of Biology", cip="26.01", duration_months=48,
        keywords=["biology"],
        description=(
            "Biology spans molecular, cellular, organismal, and ecological scales, with "
            "specializations from neuroscience to computational biology and extensive "
            "undergraduate research alongside WashU's medical and genome scientists."
        ),
        who_its_for=(
            "Aspiring biologists and pre-health students who want a research-rich foundation "
            "from molecules to ecosystems."
        ),
    ),
    dict(
        slug="washu-chemistry-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Chemistry",
        department="Department of Chemistry", cip="40.05", duration_months=48,
        keywords=["chemistry", "biochemistry"],
        description=(
            "Chemistry covers organic, inorganic, physical, and analytical chemistry with a "
            "biochemistry option, anchoring core coursework in undergraduate research in "
            "faculty laboratories."
        ),
        who_its_for=(
            "Students bound for chemistry, medicine, or materials and energy research who "
            "want rigorous training and early lab access."
        ),
    ),
    dict(
        slug="washu-classics-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Classics",
        department="Department of Classics", cip="16.12", duration_months=48,
        keywords=["classics", "Greek", "Latin"],
        description=(
            "Classics combines Greek and Latin with the literature, history, and "
            "archaeology of the ancient Mediterranean, reading foundational texts in the "
            "original."
        ),
        who_its_for=(
            "Students fascinated by antiquity who want to read the classical languages and "
            "build analytic skills prized in law and the humanities."
        ),
    ),
    dict(
        slug="washu-comparative-literature-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Comparative Literature",
        department="Comparative Literature Program", cip="16.01", duration_months=48,
        keywords=["comparative literature"],
        description=(
            "Comparative literature studies texts across languages and national traditions "
            "alongside literary theory, translation, and the relationship between "
            "literature and other arts."
        ),
        who_its_for=(
            "Multilingual readers drawn to literature across cultures who want training in "
            "theory and interpretation."
        ),
    ),
    dict(
        slug="washu-earth-planetary-sciences-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Earth and Planetary Sciences",
        department="Department of Earth and Planetary Sciences", cip="40.06", duration_months=48,
        keywords=["earth science", "planetary science"],
        description=(
            "Earth and planetary sciences studies the Earth, the solar system, and the "
            "processes that shape planets, linking fieldwork and laboratory analysis to "
            "WashU's role in NASA planetary missions."
        ),
        who_its_for=(
            "Students drawn to the Earth and planets who want field and lab research toward "
            "geoscience, planetary science, or environmental careers."
        ),
    ),
    dict(
        slug="washu-economics-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Economics",
        department="Department of Economics", cip="45.06", duration_months=48,
        keywords=["economics"],
        description=(
            "Economics grounds students in micro and macroeconomic theory and "
            "econometrics, with applied fields from labor and public economics to finance "
            "and development."
        ),
        who_its_for=(
            "Quantitatively minded students aiming for finance, consulting, or graduate "
            "study who want theory plus empirical method."
        ),
    ),
    dict(
        slug="washu-english-literature-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in English Literature",
        department="Department of English", cip="23.01", duration_months=48,
        keywords=["English", "literature", "creative writing"],
        description=(
            "English literature studies writing in English across periods and genres, with "
            "creative-writing and publishing options that pair critical study with "
            "workshops in fiction, poetry, and nonfiction."
        ),
        who_its_for=(
            "Strong readers and writers headed toward law, publishing, media, or graduate "
            "study who want sustained training in interpretation and craft."
        ),
    ),
    dict(
        slug="washu-film-media-studies-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Film and Media Studies",
        department="Department of Film and Media Studies", cip="50.06", duration_months=48,
        keywords=["film", "media studies"],
        description=(
            "Film and media studies pairs the critical study of cinema and moving-image "
            "culture with production, examining how film and media shape culture and "
            "society."
        ),
        who_its_for=(
            "Students drawn to cinema and media who want both analysis and hands-on "
            "production toward the film and media industries or scholarship."
        ),
    ),
    dict(
        slug="washu-history-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in History",
        department="Department of History", cip="54.01", duration_months=48,
        keywords=["history"],
        description=(
            "History spans the Americas, Europe, Africa, and Asia, training students in "
            "archival research and historical argument across premodern and modern "
            "periods."
        ),
        who_its_for=(
            "Students who want to investigate the past rigorously toward law, journalism, "
            "public history, or graduate study."
        ),
    ),
    dict(
        slug="washu-mathematics-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Mathematics",
        department="Department of Mathematics and Statistics", cip="27.01", duration_months=48,
        keywords=["mathematics"],
        description=(
            "Mathematics covers analysis, algebra, and applied mathematics, with combined "
            "tracks toward economics, computer science, and the physical sciences."
        ),
        who_its_for=(
            "Students with a love of mathematical reasoning aiming for quantitative careers, "
            "data science, or graduate study."
        ),
    ),
    dict(
        slug="washu-philosophy-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Philosophy",
        department="Department of Philosophy", cip="38.01", duration_months=48,
        keywords=["philosophy"],
        description=(
            "Philosophy examines logic, ethics, metaphysics, and epistemology, with a "
            "strong philosophy-neuroscience-psychology program linking the discipline to "
            "the science of mind."
        ),
        who_its_for=(
            "Students who want rigorous training in reasoning and argument as a foundation "
            "for law, ethics, or any analytic field."
        ),
    ),
    dict(
        slug="washu-physics-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Physics",
        department="Department of Physics", cip="40.08", duration_months=48,
        keywords=["physics", "biophysics"],
        description=(
            "Physics spans classical and quantum mechanics, electromagnetism, and "
            "astrophysics, with a biophysics option and undergraduate research from "
            "condensed matter to space science."
        ),
        who_its_for=(
            "Students fascinated by how the physical world works who want research training "
            "for science, engineering, or graduate study."
        ),
    ),
    dict(
        slug="washu-political-science-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Political Science",
        department="Department of Political Science", cip="45.10", duration_months=48,
        keywords=["political science", "government"],
        description=(
            "Political science studies American and comparative politics, international "
            "relations, and political theory, with specializations in political economy "
            "and methods."
        ),
        who_its_for=(
            "Future lawyers, public servants, and analysts who want analytic depth in "
            "politics and policy."
        ),
    ),
    dict(
        slug="washu-psychological-brain-sciences-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Psychological and Brain Sciences",
        department="Department of Psychological and Brain Sciences", cip="42.27",
        duration_months=48, keywords=["psychology", "brain sciences"],
        description=(
            "Psychological and brain sciences studies cognition, perception, social "
            "behavior, and the brain through coursework and laboratory research, with "
            "specializations across clinical, cognitive, and behavioral neuroscience."
        ),
        who_its_for=(
            "Students interested in mind, behavior, and the brain who want research "
            "experience for health, research, or graduate study."
        ),
    ),
    dict(
        slug="washu-religious-studies-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Religious Studies",
        department="Department of Religious Studies", cip="38.02", duration_months=48,
        keywords=["religious studies"],
        description=(
            "Religious studies analyzes the texts, histories, and practices of the world's "
            "religious traditions and their place in culture, politics, and ethics."
        ),
        who_its_for=(
            "Students who want to engage religion across traditions as preparation for law, "
            "public service, or graduate study."
        ),
    ),
    dict(
        slug="washu-sociology-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Sociology",
        department="Department of Sociology", cip="45.11", duration_months=48,
        keywords=["sociology"],
        description=(
            "Sociology analyzes how social structures, inequality, and institutions shape "
            "society, combining social theory with quantitative and qualitative methods."
        ),
        who_its_for=(
            "Students who want to understand inequality and social change toward policy, "
            "social services, or research."
        ),
    ),
    dict(
        slug="washu-statistics-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Statistics",
        department="Department of Mathematics and Statistics", cip="27.05", duration_months=48,
        keywords=["statistics"],
        description=(
            "Statistics trains students in probability, statistical modeling, and data "
            "analysis, with applications across the natural and social sciences and "
            "machine learning."
        ),
        who_its_for=(
            "Data-minded students aiming for analytics, data science, or graduate study who "
            "want a rigorous statistical foundation."
        ),
    ),
    dict(
        slug="washu-african-american-studies-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in African and African American Studies",
        department="Department of African and African American Studies", cip="05.02",
        duration_months=48, keywords=["African American studies"],
        description=(
            "African and African American studies analyzes the history, politics, and "
            "cultural production of Black communities in the United States, Africa, and the "
            "diaspora."
        ),
        who_its_for=(
            "Students committed to understanding race and the African diaspora as a "
            "foundation for law, policy, education, or scholarship."
        ),
    ),
    dict(
        slug="washu-global-studies-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Global Studies",
        department="Global Studies Program", cip="30.20", duration_months=48,
        keywords=["global studies", "international"],
        description=(
            "Global studies examines globalization, development, human rights, and "
            "transnational issues across multiple concentrations, combining the social "
            "sciences with regional and language study."
        ),
        who_its_for=(
            "Students drawn to global problems who want interdisciplinary grounding for "
            "international affairs, development, or law."
        ),
    ),
    dict(
        slug="washu-womens-gender-sexuality-studies-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Women, Gender, and Sexuality Studies",
        department="Women, Gender, and Sexuality Studies Program", cip="05.02",
        duration_months=48, keywords=["women gender sexuality studies"],
        description=(
            "Women, gender, and sexuality studies analyzes how gender and sexuality shape "
            "culture, politics, and the body, drawing on feminist theory and the social "
            "sciences."
        ),
        who_its_for=(
            "Students committed to analyzing gender and inequality toward advocacy, policy, "
            "health, or scholarship."
        ),
    ),
    dict(
        slug="washu-data-science-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Data Science",
        department="Division of Computational and Data Sciences", cip="30.70",
        duration_months=48, keywords=["data science"],
        description=(
            "Data science joins statistics, computing, and machine learning with a domain "
            "focus, training students to gather, model, and interpret data and to reason "
            "about its ethical use."
        ),
        who_its_for=(
            "Students who want to turn data into insight across science, business, or "
            "policy with a liberal-arts grounding."
        ),
    ),
    dict(
        slug="washu-astrophysics-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Astrophysics",
        department="Department of Physics", cip="40.02", duration_months=48,
        keywords=["astrophysics", "astronomy"],
        description=(
            "Astrophysics studies stars, galaxies, and cosmology through physics and "
            "observation, connecting students to WashU's space-sciences research."
        ),
        who_its_for=(
            "Students captivated by the cosmos who want a physics-grounded path into "
            "astronomy and space science."
        ),
    ),
    dict(
        slug="washu-linguistics-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Linguistics",
        department="Linguistics Program", cip="16.01", duration_months=48,
        keywords=["linguistics"],
        description=(
            "Linguistics investigates the structure of language — sound, grammar, and "
            "meaning — alongside language acquisition, sociolinguistics, and computational "
            "approaches."
        ),
        who_its_for=(
            "Students fascinated by how language works who want paths into language "
            "technology, cognitive science, or research."
        ),
    ),
    dict(
        slug="washu-environmental-analysis-ab", school=_A, degree_type="bachelors",
        program_name="Bachelor of Arts in Environmental Analysis",
        department="Environmental Studies Program", cip="03.01", duration_months=48,
        keywords=["environmental analysis", "environment"],
        description=(
            "Environmental analysis links the natural and social sciences, policy, and the "
            "humanities to study sustainability, climate, and environmental change."
        ),
        who_its_for=(
            "Students committed to environmental and climate solutions who want an "
            "interdisciplinary foundation for science, policy, or advocacy."
        ),
    ),
    # ───────────── McKelvey School of Engineering ─────────────
    dict(
        slug="washu-biomedical-engineering-bs", school=_MCKELVEY, degree_type="bachelors",
        program_name="Bachelor of Science in Biomedical Engineering",
        department="Department of Biomedical Engineering", cip="14.05", duration_months=48,
        keywords=["biomedical engineering"],
        description=(
            "Biomedical engineering applies engineering to medicine and biology — imaging, "
            "biomaterials, neural engineering, and computational modeling — with close ties "
            "to WashU's medical school."
        ),
        who_its_for=(
            "Students who want to engineer solutions for medicine and human health, often "
            "toward medical or biomedical-research careers."
        ),
    ),
    dict(
        slug="washu-chemical-engineering-bs", school=_MCKELVEY, degree_type="bachelors",
        program_name="Bachelor of Science in Chemical Engineering",
        department="Department of Energy, Environmental and Chemical Engineering",
        cip="14.07", duration_months=48, keywords=["chemical engineering"],
        description=(
            "Chemical engineering designs processes that transform matter and energy, with "
            "strength in energy, the environment, and sustainable manufacturing."
        ),
        who_its_for=(
            "Students drawn to chemistry and large-scale processes who want to work in "
            "energy, materials, or environmental industries."
        ),
    ),
    dict(
        slug="washu-computer-engineering-bs", school=_MCKELVEY, degree_type="bachelors",
        program_name="Bachelor of Science in Computer Engineering",
        department="Department of Computer Science and Engineering", cip="14.09",
        duration_months=48, keywords=["computer engineering"],
        description=(
            "Computer engineering bridges hardware and software — digital systems, "
            "embedded computing, and computer architecture — joining electrical "
            "engineering with computer science."
        ),
        who_its_for=(
            "Students who want to build computing systems from the circuit to the program "
            "for careers in hardware, embedded systems, or systems software."
        ),
    ),
    dict(
        slug="washu-computer-science-bs", school=_MCKELVEY, degree_type="bachelors",
        program_name="Bachelor of Science in Computer Science",
        department="Department of Computer Science and Engineering", cip="11.07",
        duration_months=48, keywords=["computer science"],
        description=(
            "Computer science covers algorithms, systems, theory, and artificial "
            "intelligence, with electives in security, graphics, and machine learning and "
            "extensive project work."
        ),
        who_its_for=(
            "Students building careers in software, AI, or research who want a strong "
            "computing foundation in a research university."
        ),
    ),
    dict(
        slug="washu-data-science-engineering-bs", school=_MCKELVEY, degree_type="bachelors",
        program_name="Bachelor of Science in Data Science",
        department="Department of Computer Science and Engineering", cip="11.07",
        duration_months=48, keywords=["data science engineering"],
        description=(
            "This engineering data-science degree combines computing, statistics, and "
            "machine learning with systems for large-scale data, emphasizing the "
            "engineering of data-driven applications."
        ),
        who_its_for=(
            "Students who want to engineer machine-learning and data systems for technical "
            "data-science and ML-engineering roles."
        ),
    ),
    dict(
        slug="washu-electrical-engineering-bs", school=_MCKELVEY, degree_type="bachelors",
        program_name="Bachelor of Science in Electrical Engineering",
        department="Department of Electrical and Systems Engineering", cip="14.10",
        duration_months=48, keywords=["electrical engineering"],
        description=(
            "Electrical engineering covers circuits, signals, electronics, and "
            "communications, with work in sensing, power, and the systems that connect "
            "the physical and digital worlds."
        ),
        who_its_for=(
            "Students drawn to electronics, signals, and devices who want a foundation for "
            "hardware, communications, or power-systems careers."
        ),
    ),
    dict(
        slug="washu-mechanical-engineering-bs", school=_MCKELVEY, degree_type="bachelors",
        program_name="Bachelor of Science in Mechanical Engineering",
        department="Department of Mechanical Engineering and Materials Science", cip="14.19",
        duration_months=48, keywords=["mechanical engineering"],
        description=(
            "Mechanical engineering covers mechanics, thermodynamics, design, and "
            "materials, with hands-on work in robotics, energy systems, and "
            "manufacturing."
        ),
        who_its_for=(
            "Students who like to design and build physical systems for careers in "
            "robotics, energy, aerospace, or manufacturing."
        ),
    ),
    dict(
        slug="washu-systems-science-engineering-bs", school=_MCKELVEY, degree_type="bachelors",
        program_name="Bachelor of Science in Systems Science and Engineering",
        department="Department of Electrical and Systems Engineering", cip="14.27",
        duration_months=48, keywords=["systems science engineering"],
        description=(
            "Systems science and engineering studies how to model, optimize, and control "
            "complex systems — networks, decision-making, and operations — across "
            "engineering and the social sciences."
        ),
        who_its_for=(
            "Students drawn to optimization and complex systems who want analytic tools "
            "for engineering, operations, and data-driven decision-making."
        ),
    ),
    # ───────────── Olin Business School ─────────────
    dict(
        slug="washu-business-administration-bsba", school=_OLIN, degree_type="bachelors",
        program_name="Bachelor of Science in Business Administration",
        department="Olin Business School", cip="52.02", duration_months=48,
        keywords=["business administration", "BSBA"],
        description=(
            "The Bachelor of Science in Business Administration combines a management core "
            "with experiential learning, letting students concentrate in fields such as "
            "accounting, finance, marketing, entrepreneurship, and supply chain and "
            "operations."
        ),
        who_its_for=(
            "Undergraduates aiming for careers in business and management who want an "
            "experiential, analytically grounded business education."
        ),
        tracks=[
            "Accounting", "Economics and Strategy", "Entrepreneurship", "Finance",
            "Health Care Management", "Marketing", "Supply Chain, Operations, and Technology",
        ],
    ),
    dict(
        slug="washu-mba", school=_OLIN, degree_type="masters",
        program_name="Master of Business Administration",
        department="Olin Business School", cip="52.02", duration_months=24,
        keywords=["MBA", "management"],
        description=(
            "The full-time MBA builds general-management capability through an analytics-"
            "driven core, global experiential courses, and electives across finance, "
            "consulting, and entrepreneurship."
        ),
        who_its_for=(
            "Early-career professionals seeking a general-management MBA with strength in "
            "analytics, finance, and consulting."
        ),
        tuition=_MBA_FT, cost_note=(
            f"Olin Full-Time MBA tuition (${_MBA_FT:,}; 2025-26 published rate)."
        ),
        cost_source=_OLIN_SRC,
    ),
    dict(
        slug="washu-finance-ms", school=_OLIN, degree_type="masters",
        program_name="Master of Science in Finance",
        department="Olin Business School", cip="52.08", duration_months=12,
        keywords=["finance", "MS Finance"],
        description=(
            "The MS in Finance gives pre-experience and early-career students advanced "
            "training in corporate finance, investments, and quantitative methods, with "
            "tracks in corporate finance and asset management."
        ),
        who_its_for=(
            "Analytically strong graduates targeting careers in investment, corporate "
            "finance, or financial analysis."
        ),
        tuition=_MSF,
        cost_source=_OLIN_MSF_SRC,
        cost_note=(
            "MS in Finance tuition is billed at a flat per-semester rate. The Corporate "
            "Finance track runs two semesters and totals $81,500; the STEM-designated "
            "Quantitative and Wealth & Asset Management tracks run three semesters and "
            "total $102,900 (Olin, 2026-27). The scalar shows the one-academic-year "
            "Corporate Finance total; a $1,350 per-semester program/fees charge is additional."
        ),
        cost_year="2026-27",
    ),
    dict(
        slug="washu-business-analytics-ms", school=_OLIN, degree_type="masters",
        program_name="Master of Science in Business Analytics",
        department="Olin Business School", cip="52.13", duration_months=16,
        keywords=["business analytics"],
        description=(
            "The MS in Business Analytics trains students in data management, statistical "
            "modeling, and machine learning applied to business decisions, with a "
            "capstone project."
        ),
        who_its_for=(
            "Graduates who want to turn data into business decisions through analytics and "
            "machine learning."
        ),
        tuition=_MSBA,
        cost_source=_OLIN_MSBA_SRC,
        cost_note=(
            "The STEM-designated MS in Business Analytics is billed at a flat $33,933 per "
            "semester; the three-semester program totals $101,799 (Olin, Spring 2026 "
            "cohort). The scalar shows the standard two-semester academic-year tuition; a "
            "$1,350 per-semester program/fees charge is additional."
        ),
        cost_year="2025-26",
    ),
    # ───────────── Sam Fox School of Design & Visual Arts ─────────────
    dict(
        slug="washu-architecture-bs", school=_SAMFOX, degree_type="bachelors",
        program_name="Bachelor of Science in Architecture",
        department="College of Architecture", cip="04.02", duration_months=48,
        keywords=["architecture"],
        description=(
            "The undergraduate architecture degree builds design ability through studios, "
            "history and theory, and building technology, preparing students for the "
            "professional Master of Architecture."
        ),
        who_its_for=(
            "Students drawn to design and the built environment who want a studio-based "
            "path toward the architecture profession."
        ),
    ),
    dict(
        slug="washu-art-bfa", school=_SAMFOX, degree_type="bachelors",
        program_name="Bachelor of Fine Arts in Art",
        department="College of Art", cip="50.07", duration_months=48,
        keywords=["art", "studio art", "BFA"],
        description=(
            "The BFA in art develops studio practice across concentrations such as "
            "painting, photography, printmaking, sculpture, and time-based media, with "
            "critique grounded in the Kemper Art Museum."
        ),
        who_its_for=(
            "Committed studio artists who want an immersive, critique-driven path toward an "
            "art practice or graduate study."
        ),
    ),
    dict(
        slug="washu-communication-design-bfa", school=_SAMFOX, degree_type="bachelors",
        program_name="Bachelor of Fine Arts in Communication Design",
        department="College of Art", cip="50.04", duration_months=48,
        keywords=["communication design", "graphic design"],
        description=(
            "Communication design teaches typography, visual systems, and interaction "
            "design, training students to shape how information and brands are seen and "
            "experienced."
        ),
        who_its_for=(
            "Visually minded students who want a design career in branding, digital "
            "products, or visual communication."
        ),
    ),
    # ───────────── Brown School ─────────────
    dict(
        slug="washu-public-health-bs", school=_BROWN, degree_type="bachelors",
        program_name="Bachelor of Science in Public Health",
        department="Brown School", cip="51.22", duration_months=48,
        keywords=["public health"],
        description=(
            "The undergraduate public-health degree studies the determinants of health "
            "across populations and the systems that respond to them, joining "
            "epidemiology, policy, and the social sciences."
        ),
        who_its_for=(
            "Students aiming for careers in public health, health policy, or medicine who "
            "want to understand health at the population scale."
        ),
    ),
    dict(
        slug="washu-social-work-msw", school=_BROWN, degree_type="masters",
        program_name="Master of Social Work",
        department="Brown School", cip="44.07", duration_months=24,
        keywords=["social work", "MSW"],
        description=(
            "The Master of Social Work — among the top-ranked in the country — prepares "
            "clinical and macro practitioners through coursework and extensive field "
            "practica in mental health, children and families, and social and economic "
            "development."
        ),
        who_its_for=(
            "Students committed to clinical or community social-work practice and social "
            "change who want a top-ranked, field-intensive MSW."
        ),
        tuition=_MSW, cost_note=(
            f"Brown School Master of Social Work tuition (${_MSW:,}; 2025-26 published rate)."
        ),
        cost_source=_BROWN_SRC,
    ),
    dict(
        slug="washu-public-health-mph", school=_BROWN, degree_type="masters",
        program_name="Master of Public Health",
        department="Brown School", cip="51.22", duration_months=24,
        keywords=["public health", "MPH"],
        description=(
            "The Master of Public Health trains practitioners in epidemiology, "
            "biostatistics, and health policy, with applied practice addressing health "
            "equity and population health."
        ),
        who_its_for=(
            "Students and clinicians pursuing careers in public health, epidemiology, or "
            "health policy."
        ),
        tuition=_MPH, cost_note=(
            f"Brown School Master of Public Health tuition (${_MPH:,}; 2025-26 published "
            "annual rate stated in WashU's 'The Source' tuition release)."
        ),
        cost_source=_GRAD_SRC,
    ),
    # ───────────── School of Law ─────────────
    dict(
        slug="washu-juris-doctor-jd", school=_LAW, degree_type="professional",
        program_name="Juris Doctor",
        department="School of Law", cip="22.01", duration_months=36,
        keywords=["Juris Doctor", "JD", "law"],
        description=(
            "The Juris Doctor is WashU Law's three-year professional degree, pairing a "
            "doctrinal core with clinics and concentrations in intellectual property, "
            "dispute resolution, and public-interest law."
        ),
        who_its_for=(
            "Future lawyers who want a rigorous J.D. with strong clinical training and "
            "specialization options."
        ),
        tuition=_JD, cost_note=(
            f"WashU School of Law full-time J.D. tuition (${_JD:,}; 2025-26 published rate)."
        ),
        cost_source=_LAW_SRC,
    ),
    dict(
        slug="washu-master-of-laws-llm", school=_LAW, degree_type="masters",
        program_name="Master of Laws",
        department="School of Law", cip="22.02", duration_months=12,
        keywords=["LLM", "Master of Laws"],
        description=(
            "The Master of Laws offers lawyers advanced study in fields such as "
            "intellectual property, taxation, and U.S. law for international attorneys."
        ),
        who_its_for=(
            "Practicing and international lawyers seeking advanced specialization in a "
            "focused area of law."
        ),
        tuition=_LLM, cost_note=(
            f"WashU School of Law full-time LL.M. tuition (${_LLM:,}; 2025-26 published "
            "annual rate — the School of Law J.D., J.S.D., LL.M., and M.L.S. share one "
            "flat full-time rate in WashU's 'The Source' tuition release)."
        ),
        cost_source=_LAW_SRC,
    ),
    # ───────────── School of Medicine ─────────────
    dict(
        slug="washu-medicine-md", school=_MEDICINE, degree_type="professional",
        program_name="Doctor of Medicine",
        department="School of Medicine", cip="51.12", duration_months=48,
        keywords=["Doctor of Medicine", "MD", "medical"],
        description=(
            "The Doctor of Medicine educates physicians at one of the nation's leading "
            "academic medical centers, integrating basic and clinical science with early "
            "patient care and training in the BJC HealthCare hospitals."
        ),
        who_its_for=(
            "Aspiring physicians who want an elite, research-rich medical education with "
            "broad clinical training."
        ),
        tuition=_MD, cost_note=(
            f"School of Medicine M.D. tuition (${_MD:,} per year, fixed across the four-year "
            "program; 2025-26 published rate)."
        ),
        cost_source=_MED_SRC,
    ),
    # ───────────── Graduate School of Arts & Sciences (funded PhDs) ─────────────
    dict(
        slug="washu-biology-phd", school=_GRAD, degree_type="phd",
        program_name="Doctor of Philosophy in Biology",
        department="Division of Biology and Biomedical Sciences", cip="26.01",
        duration_months=60, keywords=["biology PhD"],
        description=(
            "Doctoral research in biology pursues independent investigation across "
            "molecular, cellular, evolutionary, and computational biology, with strong "
            "ties to WashU's genome and medical sciences."
        ),
        who_its_for=(
            "Research scientists pursuing a doctorate for academic, industry, or biomedical "
            "research careers."
        ),
        funded=True,
    ),
    dict(
        slug="washu-chemistry-phd", school=_GRAD, degree_type="phd",
        program_name="Doctor of Philosophy in Chemistry",
        department="Department of Chemistry", cip="40.05", duration_months=60,
        keywords=["chemistry PhD"],
        description=(
            "Doctoral research in chemistry pursues laboratory investigation across the "
            "chemical sciences, from synthesis and physical chemistry to biological and "
            "materials chemistry."
        ),
        who_its_for=(
            "Research scientists pursuing a doctorate for careers in academia, industry, or "
            "national laboratories."
        ),
        funded=True,
    ),
    dict(
        slug="washu-physics-phd", school=_GRAD, degree_type="phd",
        program_name="Doctor of Philosophy in Physics",
        department="Department of Physics", cip="40.08", duration_months=60,
        keywords=["physics PhD"],
        description=(
            "Doctoral research in physics advances original work in areas including "
            "condensed-matter physics, biophysics, and astrophysics through theory, "
            "computation, and experiment."
        ),
        who_its_for=(
            "Future physicists pursuing research careers in academia, industry, or "
            "government laboratories."
        ),
        funded=True,
    ),
    dict(
        slug="washu-economics-phd", school=_GRAD, degree_type="phd",
        program_name="Doctor of Philosophy in Economics",
        department="Department of Economics", cip="45.06", duration_months=60,
        keywords=["economics PhD"],
        description=(
            "Doctoral research in economics builds advanced theory and econometrics toward "
            "original research in fields such as microeconomics, macroeconomics, and "
            "applied microeconomics."
        ),
        who_its_for=(
            "Quantitatively rigorous students pursuing research careers in academia or "
            "policy institutions."
        ),
        funded=True,
    ),
    dict(
        slug="washu-psychological-brain-sciences-phd", school=_GRAD, degree_type="phd",
        program_name="Doctor of Philosophy in Psychological and Brain Sciences",
        department="Department of Psychological and Brain Sciences", cip="42.27",
        duration_months=60, keywords=["psychology PhD", "brain sciences"],
        description=(
            "Doctoral research in psychological and brain sciences investigates cognition, "
            "behavior, and the brain across clinical, cognitive, and behavioral-"
            "neuroscience areas."
        ),
        who_its_for=(
            "Researchers pursuing the science of mind and behavior toward academic or "
            "applied research careers."
        ),
        funded=True,
    ),
    dict(
        slug="washu-history-phd", school=_GRAD, degree_type="phd",
        program_name="Doctor of Philosophy in History",
        department="Department of History", cip="54.01", duration_months=72,
        keywords=["history PhD"],
        description=(
            "Doctoral research in history develops archival expertise and original "
            "scholarship across world regions and the early-modern and modern periods."
        ),
        who_its_for=(
            "Historians-in-training pursuing original research toward academic or public-"
            "history careers."
        ),
        funded=True,
    ),
    dict(
        slug="washu-social-work-phd", school=_BROWN, degree_type="phd",
        program_name="Doctor of Philosophy in Social Work",
        department="Brown School", cip="44.07", duration_months=60,
        keywords=["social work PhD"],
        description=(
            "The PhD in social work trains researchers in social-work science — mental "
            "health, social and economic development, and health — to produce evidence "
            "that shapes practice and policy."
        ),
        who_its_for=(
            "Future social-work scholars pursuing research and faculty careers grounded in "
            "social-welfare science."
        ),
        funded=True,
    ),
    # ───────────── Sam Fox — graduate ─────────────
    dict(
        slug="washu-architecture-march", school=_SAMFOX, degree_type="masters",
        program_name="Master of Architecture",
        department="College of Architecture", cip="04.02", duration_months=36,
        keywords=["Master of Architecture", "MArch"],
        description=(
            "The professional Master of Architecture develops design, technology, and "
            "urban thinking through advanced studios, preparing graduates for licensure "
            "and practice."
        ),
        who_its_for=(
            "Students pursuing the professional architecture credential and a career in "
            "architectural practice or research."
        ),
        tuition=_MARCH, cost_note=(
            f"Sam Fox School Master of Architecture tuition (${_MARCH:,}; 2025-26 published "
            "annual rate stated in WashU's 'The Source' tuition release)."
        ),
        cost_source=_GRAD_SRC,
    ),
    dict(
        slug="washu-visual-art-mfa", school=_SAMFOX, degree_type="masters",
        program_name="Master of Fine Arts in Visual Art",
        department="College of Art", cip="50.07", duration_months=24,
        keywords=["MFA", "visual art"],
        description=(
            "The MFA in visual art is a studio-based terminal degree developing an "
            "independent art practice through critique, interdisciplinary work, and "
            "engagement with the Kemper Art Museum."
        ),
        who_its_for=(
            "Practicing artists pursuing a terminal studio degree toward exhibiting "
            "careers or teaching."
        ),
        tuition=_MFA, cost_note=(
            f"Sam Fox School Master of Fine Arts in Visual Art tuition (${_MFA:,}; 2025-26 "
            "published annual rate stated in WashU's 'The Source' tuition release)."
        ),
        cost_source=_GRAD_SRC,
    ),
    # ───────────── McKelvey — graduate ─────────────
    dict(
        slug="washu-computer-science-ms", school=_MCKELVEY, degree_type="masters",
        program_name="Master of Science in Computer Science",
        department="Department of Computer Science and Engineering", cip="11.07",
        duration_months=18, keywords=["computer science MS"],
        description=(
            "The MS in computer science deepens expertise in algorithms, systems, and "
            "artificial intelligence through advanced coursework and a research or project "
            "specialization."
        ),
        who_its_for=(
            "Computing graduates and professionals deepening technical expertise for "
            "advanced software, AI, or research roles."
        ),
        tuition=_AS_ENG_GRAD, cost_note=(
            f"McKelvey Engineering graduate tuition (${_AS_ENG_GRAD:,}; 2025-26 published "
            "rate for Arts & Sciences and McKelvey graduate programs)."
        ),
        cost_source=_GRAD_SRC,
    ),
    dict(
        slug="washu-data-science-ms", school=_MCKELVEY, degree_type="masters",
        program_name="Master of Science in Data Science",
        department="Department of Computer Science and Engineering", cip="30.70",
        duration_months=18, keywords=["data science MS"],
        description=(
            "The MS in data science combines machine learning, statistics, and data "
            "engineering with applied projects, preparing graduates to build and deploy "
            "data-driven systems."
        ),
        who_its_for=(
            "Graduates and professionals targeting data-science and machine-learning "
            "engineering roles."
        ),
        tuition=_AS_ENG_GRAD, cost_note=(
            f"McKelvey Engineering graduate tuition (${_AS_ENG_GRAD:,}; 2025-26 published "
            "rate for Arts & Sciences and McKelvey graduate programs)."
        ),
        cost_source=_GRAD_SRC,
    ),
]


# ── Reviews (gathered → summarized → cited; coverable flagships only) ───────
_USNEWS_UG = "https://www.usnews.com/best-colleges/washington-university-in-st-louis-2520"
_USNEWS_GRAD = "https://www.usnews.com/best-graduate-schools/washington-university-179867"
_GRADREPORTS = "https://gradreports.com/colleges/washington-university-in-st-louis"
_SDN_MED = (
    "https://www.studentdoctor.net/schools-database/medical-school/detail/"
    "WASHU/washington-university-in-st-louis-school-of-medicine"
)

_REVIEWS_BY_SLUG: dict[str, dict] = {
    "washu-finance-ms": {
        "summary": (
            "Olin's MS in Finance draws strong third-party recognition — TFE Times ranked "
            "WashU's Master of Finance #3 globally in 2025 — and coverage emphasizes its "
            "quantitative rigor, STEM-designated tracks (Quantitative and Wealth & Asset "
            "Management), and AACSB-accredited faculty; common cautions are the program's "
            "modest cohort and St. Louis location relative to the largest coastal finance "
            "markets, and a multi-track structure applicants must navigate."
        ),
        "themes": [
            {
                "label": "Top-ranked finance master's",
                "sentiment": "positive",
                "detail": (
                    "TFE Times placed WashU's Master of Finance #3 worldwide in its 2025 "
                    "ranking, reflecting strong curricular and outcomes reputation."
                ),
            },
            {
                "label": "STEM-designated quantitative tracks",
                "sentiment": "positive",
                "detail": (
                    "The Quantitative and Wealth & Asset Management tracks are STEM-"
                    "designated, extending OPT eligibility for international students and "
                    "signalling technical depth."
                ),
            },
            {
                "label": "Scale & location",
                "sentiment": "mixed",
                "detail": (
                    "A smaller cohort supports faculty access, but the St. Louis market is "
                    "less proximate to coastal finance hubs than the largest programs."
                ),
            },
        ],
        "sources": [
            {"label": "WashU Olin — Accreditation & Rankings", "url": _OLIN_RANK_SRC[1]},
            {"label": "U.S. News — WashU Best Graduate Schools", "url": _USNEWS_GRAD},
            {"label": "GradReports — Washington University in St. Louis", "url": _GRADREPORTS},
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources (TFE Times via "
            "Olin's published rankings, U.S. News, GradReports) — not individual verbatim "
            "reviews."
        ),
    },
    "washu-business-analytics-ms": {
        "summary": (
            "Coverage of Olin's MS in Business Analytics highlights a STEM-designated "
            "curriculum spanning data management, statistical modeling, and machine "
            "learning with a capstone, taught by AACSB-accredited faculty and placing "
            "graduates in analytics and consulting roles; common cautions are the smaller "
            "program scale and the St. Louis market relative to the largest coastal tech "
            "and analytics hubs."
        ),
        "themes": [
            {
                "label": "Applied analytics & machine learning",
                "sentiment": "positive",
                "detail": (
                    "The curriculum pairs data management, statistical modeling, and "
                    "machine learning with a capstone project on real business problems."
                ),
            },
            {
                "label": "STEM designation",
                "sentiment": "positive",
                "detail": (
                    "The program's STEM designation extends OPT work eligibility for "
                    "international graduates and signals technical depth to employers."
                ),
            },
            {
                "label": "Scale & location",
                "sentiment": "mixed",
                "detail": (
                    "A smaller cohort affords close faculty contact, but St. Louis is less "
                    "proximate to the largest coastal tech employer markets."
                ),
            },
        ],
        "sources": [
            {"label": "WashU Olin — MS in Business Analytics", "url": _OLIN_MSBA_SRC[1]},
            {"label": "U.S. News — WashU Best Graduate Schools", "url": _USNEWS_GRAD},
            {"label": "GradReports — Washington University in St. Louis", "url": _GRADREPORTS},
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources (Olin program "
            "materials, U.S. News, GradReports) — not individual verbatim reviews."
        ),
    },
    "washu-mba": {
        "summary": (
            "Coverage of the Olin MBA highlights its analytics-driven curriculum, small "
            "and collaborative cohort, and strong placement in consulting and finance; "
            "common cautions are a smaller class and recruiting footprint than the largest "
            "programs and the St. Louis location relative to coastal hubs."
        ),
        "themes": [
            {
                "label": "Analytics & general management",
                "sentiment": "positive",
                "detail": (
                    "A data-driven core and experiential courses build broad management "
                    "capability with a quantitative edge."
                ),
            },
            {
                "label": "Small, collaborative cohort",
                "sentiment": "positive",
                "detail": (
                    "A small class supports close faculty access and a collaborative rather "
                    "than cut-throat culture."
                ),
            },
            {
                "label": "Location & scale",
                "sentiment": "mixed",
                "detail": (
                    "St. Louis offers affordability and community but less proximity to "
                    "coastal employer markets than the largest urban MBAs."
                ),
            },
        ],
        "sources": [
            {"label": "GradReports — Washington University in St. Louis", "url": _GRADREPORTS},
            {"label": "U.S. News — WashU Best Graduate Schools", "url": _USNEWS_GRAD},
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources (GradReports, "
            "U.S. News) — not individual verbatim reviews."
        ),
    },
    "washu-social-work-msw": {
        "summary": (
            "The Brown School's MSW is consistently ranked among the very best social-work "
            "programs in the country, praised for its research depth, generous funding, and "
            "extensive field practica; common cautions are the program's intensity and the "
            "modest salaries typical of the social-work field."
        ),
        "themes": [
            {
                "label": "Top-ranked social work",
                "sentiment": "positive",
                "detail": (
                    "U.S. News repeatedly places the Brown School among the top social-work "
                    "schools nationally."
                ),
            },
            {
                "label": "Field practica & funding",
                "sentiment": "positive",
                "detail": (
                    "Extensive supervised field placements and substantial scholarship "
                    "support are recurring strengths in coverage."
                ),
            },
            {
                "label": "Field salaries",
                "sentiment": "mixed",
                "detail": (
                    "As across social work, post-graduate salaries are modest relative to "
                    "tuition, which prospective students weigh."
                ),
            },
        ],
        "sources": [
            {"label": "U.S. News — WashU Best Graduate Schools", "url": _USNEWS_GRAD},
            {"label": "GradReports — Washington University in St. Louis", "url": _GRADREPORTS},
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources (U.S. News, "
            "GradReports) — not individual verbatim reviews."
        ),
    },
    "washu-juris-doctor-jd": {
        "summary": (
            "WashU Law draws praise for its collegial culture, strong clinics, and "
            "scholarship support, and is consistently ranked among the country's top law "
            "schools; common cautions are a St. Louis legal market smaller than the coastal "
            "hubs and the high cost typical of private law schools."
        ),
        "themes": [
            {
                "label": "Clinics & specialization",
                "sentiment": "positive",
                "detail": (
                    "A strong clinical program and concentrations in IP and dispute "
                    "resolution support hands-on, specialized training."
                ),
            },
            {
                "label": "Collegial culture & aid",
                "sentiment": "positive",
                "detail": (
                    "Reviewers note a collaborative student culture and generous merit "
                    "scholarship support."
                ),
            },
            {
                "label": "Regional market & cost",
                "sentiment": "mixed",
                "detail": (
                    "The St. Louis legal market is smaller than coastal hubs and tuition is "
                    "high, which some applicants weigh."
                ),
            },
        ],
        "sources": [
            {"label": "U.S. News — WashU Best Graduate Schools", "url": _USNEWS_GRAD},
            {"label": "GradReports — Washington University in St. Louis", "url": _GRADREPORTS},
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources (U.S. News, "
            "GradReports) — not individual verbatim reviews."
        ),
    },
    "washu-medicine-md": {
        "summary": (
            "The WashU School of Medicine is consistently ranked among the nation's top "
            "research-intensive medical schools, praised for its research depth (especially "
            "in genomics), clinical training through BJC HealthCare, and supportive culture; "
            "common cautions are the high cost and the intensity of a research-heavy "
            "environment."
        ),
        "themes": [
            {
                "label": "Elite research base",
                "sentiment": "positive",
                "detail": (
                    "Deep strengths in genomics and the biomedical sciences (the McDonnell "
                    "Genome Institute, Siteman Cancer Center) anchor research training."
                ),
            },
            {
                "label": "Clinical training",
                "sentiment": "positive",
                "detail": (
                    "Training across the BJC HealthCare hospitals provides broad, "
                    "high-volume clinical exposure."
                ),
            },
            {
                "label": "Cost & intensity",
                "sentiment": "mixed",
                "detail": (
                    "Cost of attendance is high and the research-intensive environment is "
                    "demanding."
                ),
            },
        ],
        "sources": [
            {"label": "Student Doctor Network — WashU School of Medicine", "url": _SDN_MED},
            {"label": "U.S. News — WashU Best Graduate Schools", "url": _USNEWS_GRAD},
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources (Student Doctor "
            "Network, U.S. News) — not individual verbatim reviews."
        ),
    },
}

# ── Tracks (concentrations of a single degree, NOT separate program rows) ──
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
        "slug": r["slug"],
        "school": r["school"],
        "program_name": r["program_name"],
        "degree_type": r["degree_type"],
        "department": r["department"],
        "duration_months": r["duration_months"],
        "delivery_format": r.get("delivery_format", "on_campus"),
        "keywords": list(r["keywords"]),
        "description": r["description"],
        "cip": r["cip"],
        "who_its_for": r["who_its_for"],
        "tuition": r.get("tuition"),
        "funded": r.get("funded", False),
        "cost_note": r.get("cost_note"),
        "cost_source": r.get("cost_source"),
        "cost_year": r.get("cost_year"),
        "omit_tuition_reason": r.get("omit_tuition_reason"),
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
    raise RuntimeError("duplicate (program_name, degree_type) in WashU catalog")

# ── Outcomes (institution-wide; WashU publishes no per-program split) ──
_OUTCOMES_CONDITIONS = (
    "Institution-wide median earnings of federally aided students measured 10 years after "
    "entry (U.S. Dept. of Education College Scorecard); not a program-specific figure."
)
_OUTCOMES_INSTITUTION = {
    "median_salary": 86182,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry (institution-wide)",
    "conditions": _OUTCOMES_CONDITIONS,
    "source": "U.S. Dept. of Education College Scorecard (WashU, UNITID 179867)",
    "source_url": "https://collegescorecard.ed.gov/school/?179867",
}

# ── Admissions requirement sets ────────────────────────────────────────────
_REQ_UNDERGRAD = {
    "materials": [
        "Common Application or Coalition Application",
        "WashU writing supplement",
        "Secondary-school transcript + school report",
        "Counselor and teacher recommendations",
        "Standardized test scores (test-optional policy; SAT or ACT if submitted)",
    ],
    "deadlines": {
        "early_decision_1": "November 1",
        "early_decision_2": "January 2",
        "regular_decision": "January 2",
    },
    "source": "https://admissions.washu.edu/apply/",
}
_REQ_GRAD_GENERIC = {
    "materials": [
        "Online application",
        "Transcripts from all prior institutions",
        "Letters of recommendation",
        "Statement of purpose",
        "Standardized / English-proficiency scores where required by the program",
    ],
    "deadlines": {
        "note": "Deadlines vary by program; see the program's official admissions page.",
    },
    "source": "https://gradstudies.artsci.washu.edu/admissions",
}
_REQ_MBA = {
    "materials": [
        "Olin application + essays",
        "GMAT, GRE, or EA score (waivers considered)",
        "Undergraduate transcripts",
        "Two recommendations",
        "Resume + interview",
    ],
    "deadlines": {"round_1": "Fall", "round_2": "January", "round_3": "Spring"},
    "source": "https://olin.washu.edu/programs/mbas/full-time-mba/",
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
    "source": "https://law.washu.edu/admissions/",
}
_REQ_MED = {
    "materials": [
        "AMCAS application + WashU secondary",
        "MCAT score",
        "Undergraduate transcripts",
        "Letters of recommendation",
        "Interviews as required",
    ],
    "deadlines": {"primary": "AMCAS deadline (see admissions site)"},
    "source": "https://medicine.washu.edu/education/md-program/",
}


def _requirements_for(spec: dict) -> dict:
    school = spec["school"]
    if school == _LAW:
        return dict(_REQ_LAW)
    if school == _MEDICINE:
        return dict(_REQ_MED)
    if spec["slug"] == "washu-mba":
        return dict(_REQ_MBA)
    if spec["degree_type"] == "bachelors":
        return dict(_REQ_UNDERGRAD)
    return dict(_REQ_GRAD_GENERIC)


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def _program_standard(spec: dict) -> dict:
    omitted: list[str] = ["outcomes_data.employment_rate", "outcomes_data.top_industries"]
    if spec["degree_type"] != "bachelors" and spec.get("tuition") is None:
        omitted.append("cost_data.tuition_usd")
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


# A verified 4th campus photo (the seed shipped only 3 — below the >=4 gallery gate).
# Brookings Hall, WashU's landmark building; CC BY-SA 4.0 on Wikimedia Commons.
_EXTRA_CAMPUS_PHOTO = {
    "url": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/"
        "Brookings_Hall.jpg/1920px-Brookings_Hall.jpg"
    ),
    "credit": "Wikimedia Commons / Doc2129 (CC BY-SA 4.0)",
}


def apply(session: Session) -> bool:
    """Enrich WashU to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when WashU is absent — safe on fresh/CI databases.
    """
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    # Append the verified 4th campus photo if not already present (seed shipped 3).
    photos = list(school_outcomes.get("campus_photos") or [])
    if all(p.get("url") != _EXTRA_CAMPUS_PHOTO["url"] for p in photos if isinstance(p, dict)):
        photos.append(dict(_EXTRA_CAMPUS_PHOTO))
    school_outcomes["campus_photos"] = photos
    school_outcomes["_standard"] = _standard(_OMITTED_INSTITUTION)
    inst.school_outcomes = school_outcomes
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    inst.founded_year = 1853
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://washu.edu"
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


def _undergrad_cost() -> dict:
    return {
        "tuition_usd": _UG_TUITION,
        "avg_net_price": _UG_NET_PRICE,
        "breakdown": {"tuition": _UG_TUITION},
        "funded": False,
        "note": (
            "Published 2025-26 WashU undergraduate tuition with the College Scorecard "
            "average net price after aid. WashU meets full demonstrated financial need for "
            "admitted undergraduates, so many families pay well below the sticker."
        ),
        "source": _COST_SRC[0],
        "source_url": _COST_SRC[1],
        "year": "2025-26",
    }


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
        if spec["degree_type"] == "bachelors":
            p.tuition = _UG_TUITION
            p.cost_data = _undergrad_cost()
        elif spec.get("tuition") is not None:
            p.tuition = spec["tuition"]
            p.cost_data = {
                "tuition_usd": spec["tuition"],
                "funded": False,
                "note": spec.get("cost_note", ""),
                "source": (spec.get("cost_source") or _GRAD_SRC)[0],
                "source_url": (spec.get("cost_source") or _GRAD_SRC)[1],
                "year": spec.get("cost_year") or "2025-26",
            }
        elif spec.get("funded"):
            p.tuition = None
            p.cost_data = {
                "funded": True,
                "note": (
                    "Doctoral students in the Graduate School of Arts & Sciences are fully "
                    "funded — tuition waiver plus a stipend and health insurance — so the "
                    "sticker is not the price admitted students pay."
                ),
                "source": "Graduate School of Arts & Sciences — funding",
                "source_url": "https://gradstudies.artsci.washu.edu/funding/",
            }
        else:
            p.tuition = None
            p.cost_data = {
                "funded": False,
                "note": spec.get("omit_tuition_reason", (
                    "A verified per-program annual tuition figure is omitted here rather "
                    "than estimated; see the program's official cost page."
                )),
                "source": f"{spec['school']} — official program page",
                "source_url": _SCHOOL_WEBSITE.get(spec["school"], "https://washu.edu"),
            }
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
        p.application_deadline = date(2027, 1, 2) if spec["degree_type"] == "bachelors" else None
    session.flush()
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
