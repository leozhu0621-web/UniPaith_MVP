"""University of California, Irvine — gold-standard profile (institution + schools + catalog).

Every value below is verified against an authoritative source — UC Irvine's official pages
(uci.edu, the UCI General Catalogue at catalogue.uci.edu, the University Registrar's fee
schedules, and each school's site), the U.S. Dept. of Education College Scorecard / NCES
(UNITID 110653), Wikimedia Commons (campus photos, author + license verified via the Commons
extmetadata API), and the ranking bodies (U.S. News) — and carries a citation, or is honestly
omitted (recorded in that node's ``_standard.omitted``). Nothing is guessed.

Scope note: UC Irvine entered as a 5-stub institution seed (the 2026-06 US-News bulk seed)
whose five programs ALL shipped with an EMPTY ``description_text`` — a blank student page and
zero matcher embedding (REPAIR_BACKLOG run 87 entry #2, a worst-tier open defect; the sibling
UC-Davis empty-desc seed was cleared by #1178 this wave). This pass (2026-06-26) takes the
institution to gold and REPLACES the five empty stubs with a verified, real-named catalog
across UC Irvine's fifteen degree-granting schools — the School of Humanities, the School of
Social Sciences, the School of Biological Sciences, the School of Physical Sciences, the Donald
Bren School of Information and Computer Sciences, the Henry Samueli School of Engineering, the
Claire Trevor School of the Arts, the School of Social Ecology, the Paul Merage School of
Business, the School of Education, the Joe C. Wen School of Population and Public Health, the
Sue & Bill Gross School of Nursing, the School of Law, the School of Medicine, and the School
of Pharmacy and Pharmaceutical Sciences.

Every program carries a researched, field-specific ``description_text`` (anti-stub clean, gold
contrast), a ``who_its_for`` statement, a real owning ``department``, a ``cip_code`` (the
canonical federal CIP code for the field — the matcher's interest/field join key), a verified
``delivery_format``, and published tuition per credential level. Because UC Irvine is a public
university, the matcher's flat ``tuition`` scalar is the NON-RESIDENT (out-of-state) published
rate (the broadly-correct budget input for a national / international applicant pool), while
``cost_data.breakdown`` preserves BOTH the resident and non-resident rates. Funded research
doctorates carry funded=True / tuition=None; programs whose annual figure is not separately
published on an accessible official page omit tuition with a reason. Nothing is padded.

Tuition (verified 2025-26, UCI Registrar / Catalogue, tuition and fees excluding optional
health insurance): non-resident undergraduate $49,679 (resident $17,105); non-resident
academic graduate $34,317 (resident $19,215). Professional-school rates are stamped where
verified; funded research doctorates carry funded=True + tuition=None.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "University of California-Irvine"

ENRICHED_AT = "2026-06-26"


def _standard(omitted: list[str] | None = None) -> dict:
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }


_OMITTED_INSTITUTION: list[str] = [
    "school_outcomes.scale.faculty_count",
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
    # The University of California is test-free — SAT/ACT scores are not considered in
    # admission — so a test-score band is not applicable rather than missing.
    "school_outcomes.test_scores",
    # UCI's admit rate is provided; a single citable applicants/admits headcount for the most
    # recent cycle could not be verified to the two-source bar this session, so the funnel
    # counts are omitted rather than guessed.
    "school_outcomes.flagship.applicants",
    "school_outcomes.flagship.admits",
]

# ── Institution-level data ────────────────────────────────────────────────
RANKING_DATA: dict = {
    "ownership_type": "public",
    # WASC Senior College and University Commission (UC Irvine's regional accreditor).
    "accreditor": "WSCUC",
    "carnegie_classification": "Doctoral Universities: Very High Research Activity (R1)",
    # U.S. News Best Colleges (National Universities) 2025-26: #32 nationally (UCI's highest
    # ever), and #9 among public universities (top 10 public for 11 consecutive years).
    "us_news_national": {"rank": 32, "year": 2025},
    # QS World University Rankings 2026.
    "qs_world_university_rankings": {"rank": 293, "year": 2026},
    # Times Higher Education World University Rankings 2026.
    "times_higher_education": {"rank": 97, "year": 2026},
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.286,
    "avg_net_price": 14251,
    "median_earnings_10yr": 80735,
    # College Scorecard / NCES — six-year graduation rate.
    "graduation_rate_6yr": 0.869,
    # UCI first-year retention rate.
    "retention_rate_first_year": 0.938,
    # UCI campus coordinates (Irvine, Orange County, California).
    "location": {
        "lat": 33.6405,
        "lng": -117.8443,
        "city": "Irvine",
        "state": "CA",
        "country": "United States",
    },
    "demographics": {
        "asian": 0.375,
        "hispanic": 0.268,
        "white": 0.128,
        "black": 0.020,
        "note": (
            "Undergraduate race/ethnicity (College Scorecard / IPEDS); international, "
            "two-or-more-races, and not-reported make up the remainder, so shares do not sum "
            "to 100%."
        ),
        "source": "U.S. Dept. of Education College Scorecard (UC Irvine, UNITID 110653)",
        "source_url": "https://collegescorecard.ed.gov/school/?110653",
    },
    "financial_aid": {
        "pell_grant_rate": 0.361,
        # UCI 2025-26 estimated non-resident total cost of attendance (tuition, fees, housing,
        # food, books, and personal expenses).
        "cost_of_attendance": 70129,
        "source": "UC Irvine — 2025-26 cost of attendance; College Scorecard Pell rate",
        "source_url": "https://www.ofas.uci.edu/cost/undergraduate-costs/new-students.php",
    },
    "research": {
        "labs": [
            "UCI Chao Family Comprehensive Cancer Center",
            "Beckman Laser Institute and Medical Clinic",
            "Calit2 (California Institute for Telecommunications and Information Technology)",
            "Beall Applied Innovation",
            "Susan Samueli Integrative Health Institute",
        ],
        "areas": [
            "Biomedical & health sciences",
            "Information & computer sciences",
            "Engineering & materials",
            "Climate, earth & environmental science",
            "Neuroscience & the brain",
            "The arts & humanities",
        ],
        "lab_links": {
            "UCI Chao Family Comprehensive Cancer Center": "https://www.cancer.uci.edu/",
            "Beckman Laser Institute and Medical Clinic": "https://www.bli.uci.edu/",
            "Calit2": "https://www.calit2.uci.edu/",
            "Beall Applied Innovation": "https://innovation.uci.edu/",
        },
        "source": "University of California, Irvine — Office of Research",
        "source_url": "https://research.uci.edu/",
    },
    "scale": {
        # College Scorecard (UNITID 110653) — degree-seeking undergraduate enrollment.
        "undergraduate_enrollment": 30197,
        "student_faculty_ratio": "19:1",
        "research_centers": [
            "UCI Chao Family Comprehensive Cancer Center",
            "Calit2",
            "Beckman Laser Institute and Medical Clinic",
        ],
    },
    "campus_life": {
        # UC Irvine (the Anteaters) compete in NCAA Division I (Big West Conference).
        "athletics_division": "NCAA Division I (Big West Conference)",
        "mascot": "UC Irvine Anteaters",
        "housing": "Residential campus in Irvine, California, in Orange County",
        "resources": [
            {"label": "UC Irvine Athletics", "url": "https://ucirvinesports.com/"},
            {"label": "UCI Libraries", "url": "https://www.lib.uci.edu/"},
            {"label": "Aldrich Park and the UCI Arboretum", "url": "https://arboretum.bio.uci.edu/"},
            {"label": "Claire Trevor School of the Arts events", "url": "https://www.arts.uci.edu/calendar"},
            {"label": "Division of Career Pathways", "url": "https://career.uci.edu/"},
        ],
    },
    "flagship": {
        "founded_year": 1965,
        "admissions_cycle": "Most recent reported cycle (College Scorecard, UC Irvine)",
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (UC Irvine, UNITID 110653)",
            "url": "https://collegescorecard.ed.gov/school/?110653",
        },
        {
            "label": "NCES College Navigator — University of California-Irvine (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=110653",
        },
        {
            "label": "UC Irvine — 2025-26 tuition and fees (University Registrar / Catalogue)",
            "url": (
                "https://catalogue.uci.edu/informationforprospectivestudents/expensestuitionandfees/"
            ),
        },
        {
            "label": "UC Irvine ranked #32 nationally, #9 public (U.S. News 2025-26)",
            "url": (
                "https://news.uci.edu/2025/09/23/uc-irvine-is-ranked-32nd-its-highest-ever-among-nations-universities-by-u-s-news/"
            ),
        },
    ],
}

UNDERGRAD_COUNT = 30197

DESCRIPTION = (
    "The University of California, Irvine is a public land-grant research university in Irvine, "
    "California, in Orange County, founded in 1965 and one of the youngest members of the "
    "Association of American Universities. It enrolls about 30,200 undergraduates and several "
    "thousand graduate and professional students and is classified as a Carnegie R1 "
    "very-high-research-activity university.\n\n"
    "UC Irvine is organized into fifteen schools, including the schools of Humanities, Social "
    "Sciences, Biological Sciences, and Physical Sciences; the Donald Bren School of "
    "Information and Computer Sciences — the only standalone computing school in the UC system; "
    "the Henry Samueli School of Engineering; the Claire Trevor School of the Arts; the School "
    "of Social Ecology; the Paul Merage School of Business; the School of Education; the Joe C. "
    "Wen School of Population and Public Health; the Sue & Bill Gross School of Nursing; and the "
    "Schools of Law, Medicine, and Pharmacy and Pharmaceutical Sciences. Its research is "
    "anchored by the Chao Family Comprehensive Cancer Center, the Beckman Laser Institute, and "
    "Calit2.\n\n"
    "Accredited by the WASC Senior College and University Commission, UC Irvine ranks among the "
    "top 10 public universities in the United States and #32 among national universities by "
    "U.S. News, and is repeatedly recognized for social mobility. The campus is built in "
    "concentric rings around Aldrich Park.\n\n"
    "As a public university, UC Irvine charges California residents about $17,105 in 2025-26 "
    "undergraduate tuition and fees and non-residents about $49,679; its teams, the Anteaters, "
    "compete in NCAA Division I."
)

# ── The real degree-granting schools (display order) ───────────────────────
_HUM = "School of Humanities"
_SOCSCI = "School of Social Sciences"
_BIO = "School of Biological Sciences"
_PHYS = "School of Physical Sciences"
_ICS = "Donald Bren School of Information and Computer Sciences"
_ENGR = "Henry Samueli School of Engineering"
_ARTS = "Claire Trevor School of the Arts"
_SOCECO = "School of Social Ecology"
_MERAGE = "Paul Merage School of Business"
_EDU = "School of Education"
_PUBHEALTH = "Joe C. Wen School of Population and Public Health"
_NURSING = "Sue & Bill Gross School of Nursing"
_LAW = "School of Law"
_MED = "School of Medicine"
_PHARM = "School of Pharmacy and Pharmaceutical Sciences"

_SCHOOL_WEBSITE: dict[str, str] = {
    _HUM: "https://www.humanities.uci.edu/",
    _SOCSCI: "https://www.socsci.uci.edu/",
    _BIO: "https://www.bio.uci.edu/",
    _PHYS: "https://www.physsci.uci.edu/",
    _ICS: "https://www.ics.uci.edu/",
    _ENGR: "https://engineering.uci.edu/",
    _ARTS: "https://www.arts.uci.edu/",
    _SOCECO: "https://socialecology.uci.edu/",
    _MERAGE: "https://merage.uci.edu/",
    _EDU: "https://education.uci.edu/",
    _PUBHEALTH: "https://publichealth.uci.edu/",
    _NURSING: "https://nursing.uci.edu/",
    _LAW: "https://www.law.uci.edu/",
    _MED: "https://som.uci.edu/",
    _PHARM: "https://pharmsci.uci.edu/",
}

SCHOOLS: list[dict] = [
    {"name": _HUM, "sort_order": 1, "description": (
        "The School of Humanities teaches literature, history, philosophy, languages, and the "
        "arts of interpretation, awarding the B.A. across the humanities and home to the "
        "nationally known programs in literary journalism and the writing disciplines.")},
    {"name": _SOCSCI, "sort_order": 2, "description": (
        "The School of Social Sciences is one of UC Irvine's largest schools, spanning "
        "economics, political science, sociology, anthropology, cognitive sciences, and "
        "international studies with strength in quantitative and behavioral research.")},
    {"name": _BIO, "sort_order": 3, "description": (
        "The School of Biological Sciences teaches biology from molecules to ecosystems across "
        "departments from molecular biology and biochemistry to neurobiology, ecology, and "
        "developmental and cell biology, with extensive undergraduate research.")},
    {"name": _PHYS, "sort_order": 4, "description": (
        "The School of Physical Sciences spans chemistry, mathematics, physics and astronomy, "
        "and Earth system science, with a Nobel-laureate legacy in chemistry and atmospheric "
        "science and strengths in climate research.")},
    {"name": _ICS, "sort_order": 5, "description": (
        "The Donald Bren School of Information and Computer Sciences is the only standalone "
        "computing school in the University of California, spanning computer science, "
        "informatics, and statistics across research from systems and AI to human-centered "
        "computing.")},
    {"name": _ENGR, "sort_order": 6, "description": (
        "The Henry Samueli School of Engineering offers ABET-accredited engineering education "
        "across aerospace, biomedical, chemical, civil and environmental, electrical and "
        "computer, materials, and mechanical engineering.")},
    {"name": _ARTS, "sort_order": 7, "description": (
        "The Claire Trevor School of the Arts educates artists in art, dance, drama, and music, "
        "awarding the B.A., B.F.A., and M.F.A. through conservatory-style training within a "
        "research university.")},
    {"name": _SOCECO, "sort_order": 8, "description": (
        "The School of Social Ecology studies how people interact with their social and physical "
        "environments across criminology, law and society, psychological science, urban "
        "planning, and public policy, with a problem-driven, field-engaged approach.")},
    {"name": _MERAGE, "sort_order": 9, "description": (
        "The Paul Merage School of Business educates business leaders through the undergraduate "
        "business administration major and graduate degrees from the MBA to specialized "
        "master's, with a focus on innovation and analytics in Southern California's economy.")},
    {"name": _EDU, "sort_order": 10, "description": (
        "The School of Education prepares teachers and education researchers and confers the "
        "undergraduate education sciences major alongside teaching credentials, the M.A.T., the "
        "Ed.D., and the Ph.D.")},
    {"name": _PUBHEALTH, "sort_order": 11, "description": (
        "The Joe C. Wen School of Population and Public Health teaches public health science and "
        "policy and conducts research on the determinants of population health, awarding "
        "undergraduate degrees, the M.P.H., and the Ph.D.")},
    {"name": _NURSING, "sort_order": 12, "description": (
        "The Sue & Bill Gross School of Nursing educates nurses and nurse scientists, awarding "
        "the Bachelor of Science in Nursing, the master's, the Doctor of Nursing Practice, and "
        "the Ph.D.")},
    {"name": _LAW, "sort_order": 13, "description": (
        "UC Irvine School of Law, founded in 2009, is a nationally ranked public law school "
        "known for clinical training and strong employment outcomes, awarding the J.D. and the "
        "LL.M.")},
    {"name": _MED, "sort_order": 14, "description": (
        "The UC Irvine School of Medicine awards the M.D. and conducts biomedical and clinical "
        "research through UCI Health, Orange County's only academic medical center.")},
    {"name": _PHARM, "sort_order": 15, "description": (
        "The School of Pharmacy and Pharmaceutical Sciences awards the Doctor of Pharmacy and "
        "graduate degrees in pharmaceutical sciences, training pharmacists and researchers in "
        "drug discovery and care.")},
]

# Each school carries an about_detail node whose founding year, leadership, faculty count, and
# research centers were not verified per-school to the two-source bar this session, so those
# fields are honestly omitted (the school's description_text and feeds are populated). A later
# depth pass can fill them from each school's official "About" page.
_ABOUT_OMITTED_FIELDS = [
    "about_detail.founded",
    "about_detail.leadership",
    "about_detail.faculty",
    "about_detail.research_centers",
]
_ABOUT_DETAIL: dict[str, dict] = {s["name"]: {} for s in SCHOOLS}
_ABOUT_OMITTED: dict[str, list[str]] = {s["name"]: list(_ABOUT_OMITTED_FIELDS) for s in SCHOOLS}

# ── Channel feeds + official social links ──────────────────────────────────
# The UCI News RSS was fetched live this session (verified 2026-06-26: returns valid RSS 2.0
# with recent items). Schools share the institution feed filtered by `keywords`.
_SOURCE_RSS = "https://news.uci.edu/feed/"
_NEWS_URL = "https://news.uci.edu/"

_SOCIAL_UCI = {
    "instagram": "https://www.instagram.com/ucirvine/",
    "linkedin": "https://www.linkedin.com/school/university-of-california-irvine/",
    "x": "https://x.com/ucirvine",
    "youtube": "https://www.youtube.com/user/ucirvine",
    "facebook": "https://www.facebook.com/UCIrvine",
}

_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _HUM: ["Humanities", "literature", "history"],
    _SOCSCI: ["Social Sciences", "economics", "research"],
    _BIO: ["Biological Sciences", "biology", "research"],
    _PHYS: ["Physical Sciences", "chemistry", "physics"],
    _ICS: ["Information and Computer Sciences", "computer science", "ICS"],
    _ENGR: ["Samueli", "engineering", "engineers"],
    _ARTS: ["Claire Trevor", "arts", "performance"],
    _SOCECO: ["Social Ecology", "criminology", "psychology"],
    _MERAGE: ["Merage", "business", "MBA"],
    _EDU: ["School of Education", "education", "teaching"],
    _PUBHEALTH: ["public health", "population health", "Wen School"],
    _NURSING: ["nursing", "Gross School", "health"],
    _LAW: ["School of Law", "legal", "law"],
    _MED: ["School of Medicine", "medicine", "UCI Health"],
    _PHARM: ["pharmacy", "pharmaceutical sciences", "PharmD"],
}


def _school_content(name: str) -> dict:
    return {
        "news_rss": _SOURCE_RSS,
        "news_url": _NEWS_URL,
        "news_curated": False,
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": _SOCIAL_UCI,
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


_INSTITUTION_CONTENT: dict = {
    "news_rss": _SOURCE_RSS,
    "news_url": _NEWS_URL,
    "news_curated": True,
    "social": _SOCIAL_UCI,
}

# ── Tuition constants (verified 2025-26, UCI Registrar / Catalogue) ─────────
_UG_TUITION_NONRES = 49679  # non-resident undergraduate tuition & fees (matcher scalar)
_UG_TUITION_RES = 17105  # California-resident undergraduate tuition & fees
_GRAD_TUITION_NONRES = 34317  # non-resident academic graduate tuition & fees
_GRAD_TUITION_RES = 19215  # California-resident academic graduate tuition & fees
_UG_COST_SRC = (
    "UC Irvine — 2025-26 undergraduate tuition & fees (Catalogue / University Registrar)",
    "https://catalogue.uci.edu/informationforprospectivestudents/expensestuitionandfees/",
)
_GRAD_COST_SRC = (
    "UC Irvine — 2025-26 graduate-academic tuition & fees (Catalogue / University Registrar)",
    "https://catalogue.uci.edu/informationforprospectivestudents/expensestuitionandfees/",
)

_FUNDED_NOTE = (
    "Admitted research doctoral students in this program are funded — tuition is covered "
    "alongside a stipend and health insurance for funded students — so the published sticker "
    "is not the price students pay."
)


def _grad_cost_note() -> str:
    return (
        "Standard University of California non-resident academic graduate tuition and fees "
        f"(2025-26); California residents pay about ${_GRAD_TUITION_RES:,}. UC sets graduate "
        "tuition systemwide."
    )


# ── The catalog (built from real, distinctly-named degree programs) ────────
_UG: list[dict] = []  # undergraduate majors — filled below
_GRAD: list[dict] = []  # academic graduate programs — filled below
_PROF: list[dict] = []  # professional & management degrees — filled below


# ============================ UNDERGRADUATE MAJORS ============================
_UG = [
    # ── Charlie Dunlop School of Biological Sciences ──
    dict(
        slug="uci-biochemistry-molecular-biology-bs", school=_BIO, degree_type="bachelors",
        program_name="Bachelor of Science in Biochemistry and Molecular Biology",
        department="Department of Molecular Biology and Biochemistry",
        cip="26.0202", duration_months=48,
        keywords=["biochemistry", "molecular biology"],
        description=(
            "Biochemistry and molecular biology gives comprehensive training in understanding "
            "biology at the chemical and molecular level — gene expression, immunology, "
            "pathogenesis, and virology — integrating laboratory experience with basic theory."
        ),
        who_its_for=(
            "Students bound for graduate or medical study who want molecular-level training, "
            "with paths into biotechnology, law, and public affairs."
        ),
    ),
    dict(
        slug="uci-biological-sciences-bs", school=_BIO, degree_type="bachelors",
        program_name="Bachelor of Science in Biological Sciences",
        department="Charlie Dunlop School of Biological Sciences",
        cip="26.0101", duration_months=48,
        keywords=["biological sciences", "biology"],
        description=(
            "Biological sciences offers a unified, in-depth study of modern biology through a "
            "core spanning ecology and evolution, genetics, biochemistry, and molecular biology, "
            "with upper-division laboratory technique and methodology."
        ),
        who_its_for=(
            "Students seeking a broad biology foundation who may continue into specialized "
            "tracks, the health professions, or research."
        ),
    ),
    dict(
        slug="uci-biology-education-bs", school=_BIO, degree_type="bachelors",
        program_name="Bachelor of Science in Biology/Education",
        department="Charlie Dunlop School of Biological Sciences",
        cip="13.1322", duration_months=48,
        keywords=["biology education", "teaching credential"],
        description=(
            "Biology/Education earns the bachelor's degree concurrently with a California "
            "Preliminary Single Subject Teaching Credential authorizing graduates to teach "
            "biology and general science in middle and high schools."
        ),
        who_its_for="Students who want to teach biology and science in secondary schools.",
    ),
    dict(
        slug="uci-developmental-cell-biology-bs", school=_BIO, degree_type="bachelors",
        program_name="Bachelor of Science in Developmental and Cell Biology",
        department="Department of Developmental and Cell Biology",
        cip="26.0407", duration_months=48,
        keywords=["cell biology", "developmental biology"],
        description=(
            "Developmental and cell biology gives intensive training in the structure and "
            "function of cells and how they interact to build a complex organism, emphasizing "
            "the molecular basis of development and genomic technology."
        ),
        who_its_for=(
            "Students preparing for graduate study in cell, developmental, or "
            "biomedical science."
        ),
    ),
    dict(
        slug="uci-ecology-evolutionary-biology-bs", school=_BIO, degree_type="bachelors",
        program_name="Bachelor of Science in Ecology and Evolutionary Biology",
        department="Department of Ecology and Evolutionary Biology",
        cip="26.1303", duration_months=48,
        keywords=["ecology", "evolutionary biology"],
        description=(
            "Ecology and evolutionary biology spans evolution, ecology, and physiology — from "
            "molecular evolution and conservation biology to behavioral and microbial ecology — "
            "and requires independent research."
        ),
        who_its_for=(
            "Students headed for graduate study or careers in environmental organizations, "
            "industry, and the professions."
        ),
    ),
    dict(
        slug="uci-genetics-bs", school=_BIO, degree_type="bachelors",
        program_name="Bachelor of Science in Genetics",
        department="Department of Developmental and Cell Biology",
        cip="26.0801", duration_months=48,
        keywords=["genetics"],
        description=(
            "Genetics focuses on developmental, evolutionary, and molecular genetics and how "
            "genetic knowledge illuminates human development and disease."
        ),
        who_its_for=(
            "Students focused on genetics who want biomedical research or medical and "
            "graduate study."
        ),
    ),
    dict(
        slug="uci-human-biology-bs", school=_BIO, degree_type="bachelors",
        program_name="Bachelor of Science in Human Biology",
        department="Charlie Dunlop School of Biological Sciences",
        cip="26.0102", duration_months=48,
        keywords=["human biology"],
        description=(
            "Human biology integrates human physiology, behavior, and culture with genetics, "
            "biochemistry, cell biology, and neurobiology to understand normal and disordered "
            "human function."
        ),
        who_its_for="Pre-health students who want a human-focused biology degree.",
    ),
    dict(
        slug="uci-microbiology-immunology-bs", school=_BIO, degree_type="bachelors",
        program_name="Bachelor of Science in Microbiology and Immunology",
        department="Department of Molecular Biology and Biochemistry",
        cip="26.0502", duration_months=48,
        keywords=["microbiology", "immunology"],
        description=(
            "Microbiology and immunology studies bacteria, viruses, and unicellular eukaryotes "
            "and the immune system, including microbiome research and emerging diseases and "
            "global pandemics."
        ),
        who_its_for="Students pursuing careers and graduate study in microbiology and immunology.",
    ),
    dict(
        slug="uci-neurobiology-bs", school=_BIO, degree_type="bachelors",
        program_name="Bachelor of Science in Neurobiology",
        department="Department of Neurobiology and Behavior", cip="26.1501", duration_months=48,
        keywords=["neurobiology"],
        description=(
            "Neurobiology teaches how cellular, molecular, systems, and behavioral analyses "
            "reveal how the nervous system works, with optional faculty-mentored research."
        ),
        who_its_for=(
            "Students bound for the health professions, biomedical research, or "
            "biotechnology."
        ),
    ),
    dict(
        slug="uci-physiology-exercise-science-bs", school=_BIO, degree_type="bachelors",
        program_name="Bachelor of Science in Physiology and Exercise Science",
        department="Charlie Dunlop School of Biological Sciences",
        cip="26.0908", duration_months=48,
        keywords=["physiology", "exercise science"],
        description=(
            "Physiology and exercise science studies how movement and physical activity stress "
            "the body's systems and shape health and disease, integrating biology, chemistry, "
            "and physics."
        ),
        who_its_for="Students focused on human health and the movement sciences.",
    ),
    # ── Henry Samueli School of Engineering ──
    dict(
        slug="uci-aerospace-engineering-bs", school=_ENGR, degree_type="bachelors",
        program_name="Bachelor of Science in Aerospace Engineering",
        department="Department of Mechanical and Aerospace Engineering",
        cip="14.0201", duration_months=48,
        keywords=["aerospace engineering"],
        description=(
            "Aerospace engineering studies the flight characteristics, performance, and design "
            "of aircraft and spacecraft across aerodynamics, propulsion, structures, and "
            "control, integrated in a capstone design project."
        ),
        who_its_for="Students who want to design aerospace vehicles and systems.",
    ),
    dict(
        slug="uci-biomedical-engineering-bs", school=_ENGR, degree_type="bachelors",
        program_name="Bachelor of Science in Biomedical Engineering",
        department="Department of Biomedical Engineering", cip="14.0501", duration_months=48,
        keywords=["biomedical engineering"],
        tracks=["Biophotonics", "BioMEMS", "Premedical"],
        description=(
            "Biomedical engineering applies engineering to medical problems and the quality of "
            "health care, spanning biomedical imaging, microscale diagnostics, drug delivery, "
            "and tissue engineering, with specializations in biophotonics or BioMEMS."
        ),
        who_its_for="Students engineering medical technology, including a premedical track.",
    ),
    dict(
        slug="uci-chemical-engineering-bs", school=_ENGR, degree_type="bachelors",
        program_name="Bachelor of Science in Chemical Engineering",
        department="Department of Chemical and Biomolecular Engineering",
        cip="14.0701", duration_months=48,
        keywords=["chemical engineering"],
        description=(
            "Chemical engineering applies chemistry, mathematics, physics, and biology to "
            "societal problems in energy, health, the environment, food, and semiconductors."
        ),
        who_its_for="Students pursuing process- and product-engineering careers.",
    ),
    dict(
        slug="uci-civil-engineering-bs", school=_ENGR, degree_type="bachelors",
        program_name="Bachelor of Science in Civil Engineering",
        department="Department of Civil and Environmental Engineering",
        cip="14.0801", duration_months=48,
        keywords=["civil engineering"],
        tracks=[
            "General Civil",
            "Environmental Hydrology and Water Resources",
            "Structural",
            "Transportation Systems",
        ],
        description=(
            "Civil engineering addresses large-scale projects vital to society — water "
            "distribution, transportation, and building design — across structural, "
            "environmental, geotechnical, and transportation specializations."
        ),
        who_its_for="Students who want to build and steward infrastructure.",
    ),
    dict(
        slug="uci-computer-engineering-bs", school=_ENGR, degree_type="bachelors",
        program_name="Bachelor of Science in Computer Engineering",
        department="Department of Electrical Engineering and Computer Science",
        cip="14.0901", duration_months=48,
        keywords=["computer engineering"],
        description=(
            "Computer engineering addresses the design and analysis of digital computers in "
            "both hardware and software, covering computer architecture, VLSI circuits, software "
            "engineering, and design automation."
        ),
        who_its_for="Students who want to design computing hardware and embedded systems.",
    ),
    dict(
        slug="uci-electrical-engineering-bs", school=_ENGR, degree_type="bachelors",
        program_name="Bachelor of Science in Electrical Engineering",
        department="Department of Electrical Engineering and Computer Science",
        cip="14.1001", duration_months=48,
        keywords=["electrical engineering"],
        tracks=[
            "Electronic Circuit Design",
            "Semiconductors and Optoelectronics",
            "RF and Microwaves",
            "Digital Signal Processing",
            "Communications",
        ],
        description=(
            "Electrical engineering spans electronic circuit design, semiconductors and "
            "optoelectronics, radio-frequency and microwave systems, digital signal processing, "
            "and communications."
        ),
        who_its_for="Students designing electrical and electronic systems.",
    ),
    dict(
        slug="uci-environmental-engineering-bs", school=_ENGR, degree_type="bachelors",
        program_name="Bachelor of Science in Environmental Engineering",
        department="Department of Civil and Environmental Engineering",
        cip="14.1401", duration_months=48,
        keywords=["environmental engineering"],
        description=(
            "Environmental engineering develops strategies to control pollutant emissions, treat "
            "waste, and remediate polluted systems, emphasizing air quality, water quality, and "
            "water resources."
        ),
        who_its_for="Students engineering solutions for clean air, water, and ecosystems.",
    ),
    dict(
        slug="uci-materials-science-engineering-bs", school=_ENGR, degree_type="bachelors",
        program_name="Bachelor of Science in Materials Science and Engineering",
        department="Department of Materials Science and Engineering",
        cip="14.1801", duration_months=48,
        keywords=["materials science"],
        description=(
            "Materials science and engineering relates the composition, structure, and synthesis "
            "of materials to their properties and applications, emphasizing advanced functional "
            "materials and characterization."
        ),
        who_its_for="Students who want to design and engineer advanced materials.",
    ),
    dict(
        slug="uci-mechanical-engineering-bs", school=_ENGR, degree_type="bachelors",
        program_name="Bachelor of Science in Mechanical Engineering",
        department="Department of Mechanical and Aerospace Engineering",
        cip="14.1901", duration_months=48,
        keywords=["mechanical engineering"],
        tracks=["Aerospace", "Energy Systems", "Flow Physics", "Design of Mechanical Systems"],
        description=(
            "Mechanical engineering considers the design, control, and motive power of fluid, "
            "thermal, and mechanical systems from microelectronics to spacecraft, across "
            "aerospace, energy, flow physics, and mechanical design."
        ),
        who_its_for="Students pursuing broad engineering careers across industry and research.",
    ),
    # ── Donald Bren School of Information and Computer Sciences ──
    dict(
        slug="uci-computer-science-bs", school=_ICS, degree_type="bachelors",
        program_name="Bachelor of Science in Computer Science",
        department="Department of Computer Science", cip="11.0701", duration_months=48,
        keywords=["computer science"],
        tracks=[
            "Algorithms",
            "Architecture and Embedded Systems",
            "Bioinformatics",
            "Intelligent Systems",
            "Networked Systems",
            "Systems and Software",
            "Visual Computing",
        ],
        description=(
            "Computer science emphasizes the principles of computing that underlie the modern "
            "world, with specializations from algorithms and intelligent systems to networked "
            "systems and visual computing."
        ),
        who_its_for=(
            "Students preparing for the broad spectrum of computing careers and "
            "graduate study."
        ),
    ),
    dict(
        slug="uci-data-science-bs", school=_ICS, degree_type="bachelors",
        program_name="Bachelor of Science in Data Science",
        department="Department of Statistics", cip="30.7001", duration_months=48,
        keywords=["data science"],
        description=(
            "Data science combines foundational statistics with computer-science principles — "
            "algorithmic design, machine learning, information visualization, and Bayesian "
            "statistics — and culminates in a capstone."
        ),
        who_its_for="Students pursuing data-analyst, data-scientist, and statistician careers.",
    ),
    dict(
        slug="uci-game-design-interactive-media-bs", school=_ICS, degree_type="bachelors",
        program_name="Bachelor of Science in Game Design and Interactive Media",
        department="Department of Informatics", cip="50.0411", duration_months=48,
        keywords=["game design", "interactive media"],
        description=(
            "Game design and interactive media offers hands-on courses in worldbuilding, game "
            "design and development, game programming, and game studies across augmented and "
            "virtual reality, tabletop, and mobile platforms."
        ),
        who_its_for=(
            "Students pursuing game development, interactive entertainment, and "
            "creative technologies."
        ),
    ),
    dict(
        slug="uci-informatics-bs", school=_ICS, degree_type="bachelors",
        program_name="Bachelor of Science in Informatics",
        department="Department of Informatics", cip="11.0104", duration_months=48,
        keywords=["informatics", "human-computer interaction"],
        description=(
            "Informatics focuses on people and design — how technologies shape behavior and "
            "society and how to design systems that fit human and organizational practices — "
            "combining human-computer interaction, software development, and social analysis of "
            "computing."
        ),
        who_its_for=(
            "Students who want adaptable technology careers at the human-computing "
            "boundary."
        ),
    ),
    dict(
        slug="uci-information-computer-science-bs", school=_ICS, degree_type="bachelors",
        program_name="Bachelor of Science in Information and Computer Science",
        department="Donald Bren School of Information and Computer Sciences",
        cip="11.0101", duration_months=48,
        keywords=["information and computer science"],
        description=(
            "This individualized major lets motivated continuing students design a course of "
            "study across the information and computer sciences not served by an existing ICS "
            "major."
        ),
        who_its_for="Continuing UCI students designing an individualized computing plan.",
    ),
    dict(
        slug="uci-software-engineering-bs", school=_ICS, degree_type="bachelors",
        program_name="Bachelor of Science in Software Engineering",
        department="Department of Informatics", cip="14.0903", duration_months=48,
        keywords=["software engineering"],
        description=(
            "Software engineering builds a foundation across the software lifecycle — from "
            "envisioning ideas as designs to implementing them in modern technology stacks and "
            "ensuring quality — culminating in a capstone for a real client."
        ),
        who_its_for=(
            "Students joining software-engineering teams from startups to large tech "
            "firms."
        ),
    ),
    # ── School of Physical Sciences ──
    dict(
        slug="uci-applied-computational-mathematics-bs", school=_PHYS, degree_type="bachelors",
        program_name="Bachelor of Science in Applied and Computational Mathematics",
        department="Department of Mathematics", cip="27.0301", duration_months=48,
        keywords=["applied mathematics", "computational mathematics"],
        tracks=["Standard", "Mathematical Biology", "Mathematical Finance", "Data Science"],
        description=(
            "Applied and computational mathematics applies mathematical modeling and computation "
            "across tracks in mathematical biology, mathematical finance, and data science."
        ),
        who_its_for="Students applying mathematics to science, finance, and data.",
    ),
    dict(
        slug="uci-applied-physics-bs", school=_PHYS, degree_type="bachelors",
        program_name="Bachelor of Science in Applied Physics",
        department="Department of Physics and Astronomy", cip="40.0801", duration_months=48,
        keywords=["applied physics"],
        description=(
            "Applied physics combines physics with overlapping disciplines such as materials "
            "science, electrical engineering, geosciences, and biomedical imaging to develop "
            "expert problem solvers."
        ),
        who_its_for="Students applying physics to industry, research, and the applied sciences.",
    ),
    dict(
        slug="uci-chemistry-bs", school=_PHYS, degree_type="bachelors",
        program_name="Bachelor of Science in Chemistry",
        department="Department of Chemistry", cip="40.0501", duration_months=48,
        keywords=["chemistry"],
        tracks=["Biochemistry", "Environmental Chemistry", "Medicinal Chemistry"],
        description=(
            "Chemistry prepares students for careers in the chemical sciences and allied fields, "
            "with concentration options in biochemistry, environmental chemistry, and medicinal "
            "chemistry."
        ),
        who_its_for="Students bound for the chemical sciences, medicine, or research.",
    ),
    dict(
        slug="uci-earth-system-science-bs", school=_PHYS, degree_type="bachelors",
        program_name="Bachelor of Science in Earth System Science",
        department="Department of Earth System Science", cip="40.0699", duration_months=48,
        keywords=["earth system science", "climate"],
        description=(
            "Earth system science is interdisciplinary across oceanography, atmospheric science, "
            "geology, and hydrology, applying physics, chemistry, and biology to climate, "
            "biogeochemical cycles, and global environmental change."
        ),
        who_its_for=(
            "Students pursuing climate science, environmental policy, and resource "
            "management."
        ),
    ),
    dict(
        slug="uci-mathematics-bs", school=_PHYS, degree_type="bachelors",
        program_name="Bachelor of Science in Mathematics",
        department="Department of Mathematics", cip="27.0101", duration_months=48,
        keywords=["mathematics"],
        description=(
            "Mathematics offers preparation for advanced work in mathematics, the exact "
            "sciences, and engineering, along with pathways for the social and biological "
            "sciences and for teaching."
        ),
        who_its_for="Students pursuing mathematics, the sciences, teaching, or graduate study.",
    ),
    dict(
        slug="uci-physics-bs", school=_PHYS, degree_type="bachelors",
        program_name="Bachelor of Science in Physics",
        department="Department of Physics and Astronomy", cip="40.0801", duration_months=48,
        keywords=["physics", "astrophysics"],
        tracks=[
            "Astrophysics",
            "Computational Physics",
            "Philosophy of Physics",
            "Physics Education",
        ],
        description=(
            "Physics develops expert problem solvers with a broad understanding of physical "
            "principles, with specializations in astrophysics and concentrations in computational "
            "physics, philosophy of physics, and physics education."
        ),
        who_its_for="Students pursuing physics research, technical careers, or graduate study.",
    ),
    # ── School of Humanities ──
    dict(
        slug="uci-african-american-studies-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in African American Studies",
        department="Department of African American Studies", cip="05.0201", duration_months=48,
        keywords=["African American studies"],
        description=(
            "African American studies is an interdisciplinary program studying the societies and "
            "cultures of the African diaspora, exploring colonization, migration, racialized "
            "social orders, and the aesthetics of Blackness."
        ),
        who_its_for="Students applying the field across the health professions, law, and business.",
    ),
    dict(
        slug="uci-art-history-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in Art History",
        department="Department of Art History", cip="50.0703", duration_months=48,
        keywords=["art history"],
        description=(
            "Art history explores visual art from all regions and periods — sculpture, painting, "
            "photography, architecture, and new media — engaging race, gender, environment, and "
            "political expression."
        ),
        who_its_for="Students pursuing museums, curatorial work, conservation, or graduate study.",
    ),
    dict(
        slug="uci-asian-american-studies-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in Asian American Studies",
        department="Department of Asian American Studies", cip="05.0200", duration_months=48,
        keywords=["Asian American studies"],
        description=(
            "Asian American studies examines the historical and contemporary experiences of "
            "Asians in the United States and globally and the cultural, political, and economic "
            "organization of Asian American communities."
        ),
        who_its_for=(
            "Students pursuing law, education, community work, government, or graduate "
            "study."
        ),
    ),
    dict(
        slug="uci-chinese-studies-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in Chinese Studies",
        department="Department of East Asian Studies", cip="16.0301", duration_months=48,
        keywords=["Chinese studies"],
        description=(
            "Chinese studies offers emphases in Chinese language and literature and in Chinese "
            "culture and society, combining humanistic and social-science study of modern China."
        ),
        who_its_for="Students seeking Chinese expertise for global careers and graduate study.",
    ),
    dict(
        slug="uci-classics-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in Classics",
        department="Department of Classics", cip="16.1200", duration_months=48,
        keywords=["classics"],
        description=(
            "Classics provides a working knowledge of Graeco-Roman civilization through Greek "
            "and Latin language and literature and courses in ancient history, mythology, and "
            "religion."
        ),
        who_its_for=(
            "Students who want a rigorous humanities foundation for teaching, "
            "archaeology, or the professions."
        ),
    ),
    dict(
        slug="uci-comparative-literature-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in Comparative Literature",
        department="Department of Comparative Literature", cip="16.0104", duration_months=48,
        keywords=["comparative literature"],
        description=(
            "Comparative literature studies the world through its literatures and cultures, using "
            "critical theory and translation to move across languages, media, and geographic "
            "borders."
        ),
        who_its_for="Multilingual readers drawn to literature and culture across traditions.",
    ),
    dict(
        slug="uci-east-asian-cultures-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in East Asian Cultures",
        department="Department of East Asian Studies", cip="05.0104", duration_months=48,
        keywords=["East Asian cultures"],
        description=(
            "East Asian cultures focuses on the regional dynamics of cultural and social "
            "transformation in East Asia through a multidisciplinary study of intra-regional "
            "relationships."
        ),
        who_its_for="Students seeking regional expertise for global and cross-cultural careers.",
    ),
    dict(
        slug="uci-english-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in English",
        department="Department of English", cip="23.0101", duration_months=48,
        keywords=["English", "literature"],
        description=(
            "English introduces the full range of literatures written in English — British, "
            "American, African, Asian, and Australasian — developing clarity of expression and "
            "independent investigation."
        ),
        who_its_for="Students pursuing education, law, writing, journalism, and communications.",
    ),
    dict(
        slug="uci-european-studies-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in European Studies",
        department="Department of European Languages and Studies",
        cip="05.0106", duration_months=48,
        keywords=["European studies"],
        description=(
            "European studies examines Europe in its linguistic, historical, literary, artistic, "
            "and cultural diversity and its contemporary interconnections."
        ),
        who_its_for="Students seeking interdisciplinary European expertise for global careers.",
    ),
    dict(
        slug="uci-film-media-studies-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in Film and Media Studies",
        department="Department of Film and Media Studies", cip="50.0601", duration_months=48,
        keywords=["film studies", "media studies"],
        description=(
            "Film and media studies examines the histories, theories, aesthetics, and cultural "
            "meanings of film, television, video games, and digital platforms, with screenwriting "
            "and media-production coursework."
        ),
        who_its_for="Students pursuing entertainment, creative, and scholarly media careers.",
    ),
    dict(
        slug="uci-french-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in French",
        department="Department of European Languages and Studies",
        cip="16.0901", duration_months=48,
        keywords=["French"],
        description=(
            "French develops deep communicative and interpretive proficiency alongside the study "
            "of French and Francophone literature, culture, and thought across historical "
            "periods."
        ),
        who_its_for="Students seeking French fluency for global, professional, and graduate paths.",
    ),
    dict(
        slug="uci-gender-sexuality-studies-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in Gender and Sexuality Studies",
        department="Department of Gender and Sexuality Studies", cip="05.0207", duration_months=48,
        keywords=["gender studies", "sexuality studies"],
        description=(
            "Gender and sexuality studies analyzes gender and sexuality in their complex "
            "articulation with race, ethnicity, class, religion, and nationality from a rigorous "
            "interdisciplinary perspective."
        ),
        who_its_for="Students pursuing law, medicine, social work, education, and advocacy.",
    ),
    dict(
        slug="uci-german-studies-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in German Studies",
        department="Department of European Languages and Studies",
        cip="16.0501", duration_months=48,
        keywords=["German studies"],
        description=(
            "German studies builds German proficiency alongside the examination of "
            "twentieth- and twenty-first-century German literature, culture, and film through "
            "cultural-studies approaches."
        ),
        who_its_for="Students seeking German expertise for global and professional careers.",
    ),
    dict(
        slug="uci-global-cultures-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in Global Cultures",
        department="Program in Global Cultures", cip="30.2001", duration_months=48,
        keywords=["global cultures"],
        description=(
            "Global cultures explores the problems and processes of globalization from a "
            "humanistic perspective, drawing on art history, film and media, history, "
            "philosophy, and the social sciences."
        ),
        who_its_for=(
            "Students who want a global, analytic humanities education for diverse "
            "careers."
        ),
    ),
    dict(
        slug="uci-history-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in History",
        department="Department of History", cip="54.0101", duration_months=48,
        keywords=["history"],
        description=(
            "History develops critical intelligence through the study of the past, emphasizing "
            "weighing evidence, constructing logical arguments, and the role of theory in "
            "historical analysis."
        ),
        who_its_for="Students pursuing teaching, law, public service, and graduate study.",
    ),
    dict(
        slug="uci-japanese-language-literature-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in Japanese Language and Literature",
        department="Department of East Asian Studies", cip="16.0302", duration_months=48,
        keywords=["Japanese"],
        description=(
            "Japanese language and literature builds understanding of Japan's literary, "
            "historical, social, and aesthetic achievements through its language, literature, "
            "film, and culture."
        ),
        who_its_for="Students seeking Japanese expertise for global and cultural careers.",
    ),
    dict(
        slug="uci-korean-literature-culture-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in Korean Literature and Culture",
        department="Department of East Asian Studies", cip="16.0399", duration_months=48,
        keywords=["Korean studies"],
        description=(
            "Korean literature and culture builds understanding of Korea's literary, historical, "
            "social, and aesthetic achievements through its language, literature, film, and "
            "culture."
        ),
        who_its_for="Students seeking Korean expertise for global and cultural careers.",
    ),
    dict(
        slug="uci-literary-journalism-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in Literary Journalism",
        department="Department of English", cip="09.0401", duration_months=48,
        keywords=["literary journalism", "nonfiction"],
        description=(
            "Literary journalism studies and writes narrative nonfiction — profiles, memoirs, "
            "histories, and essays — that transcends daily journalism across science, politics, "
            "justice, and culture."
        ),
        who_its_for="Students pursuing writing, journalism, communications, and graduate study.",
    ),
    dict(
        slug="uci-philosophy-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in Philosophy",
        department="Department of Philosophy", cip="38.0101", duration_months=48,
        keywords=["philosophy"],
        description=(
            "Philosophy relies on give-and-take dialogue in which students actively examine "
            "issues across ethics, art, and science, building rigorous reasoning and argument."
        ),
        who_its_for="Students pursuing law, medicine, business, computing, or graduate philosophy.",
    ),
    dict(
        slug="uci-religious-studies-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in Religious Studies",
        department="Program in Religious Studies", cip="38.0201", duration_months=48,
        keywords=["religious studies"],
        description=(
            "Religious studies offers a critical multidisciplinary lens into world religions, "
            "history, global philosophies, and culture across traditions including Buddhism, "
            "Christianity, Islam, Judaism, and Hinduism."
        ),
        who_its_for=(
            "Students pursuing nonprofit, education, counseling, and graduate or "
            "professional study."
        ),
    ),
    dict(
        slug="uci-spanish-ba", school=_HUM, degree_type="bachelors",
        program_name="Bachelor of Arts in Spanish",
        department="Department of Spanish and Portuguese", cip="16.0905", duration_months=48,
        keywords=["Spanish"],
        description=(
            "Spanish builds a strong foundation in the literature, linguistics, and visual "
            "culture of Spanish-speaking communities across Europe, Latin America, and the "
            "United States, with intercultural competencies."
        ),
        who_its_for=(
            "Students seeking Spanish fluency for teaching, the professions, and global "
            "work."
        ),
    ),
    # ── School of Social Sciences ──
    dict(
        slug="uci-anthropology-ba", school=_SOCSCI, degree_type="bachelors",
        program_name="Bachelor of Arts in Anthropology",
        department="Department of Anthropology", cip="45.0201", duration_months=48,
        keywords=["anthropology"],
        description=(
            "Anthropology develops cultural-diversity understanding and ethnographic research "
            "and analytical techniques for a wide range of careers in a culturally diverse "
            "world."
        ),
        who_its_for="Students drawn to human cultures who want research and intercultural careers.",
    ),
    dict(
        slug="uci-business-economics-ba", school=_SOCSCI, degree_type="bachelors",
        program_name="Bachelor of Arts in Business Economics",
        department="Department of Economics", cip="52.0601", duration_months=48,
        keywords=["business economics"],
        description=(
            "Business economics offers a focused, business-oriented study of economics guided by "
            "the rigorous logic and integrative perspective of the discipline rather than a "
            "traditional business curriculum."
        ),
        who_its_for="Students who want an economics-grounded path into business and finance.",
    ),
    dict(
        slug="uci-chicano-latino-studies-ba", school=_SOCSCI, degree_type="bachelors",
        program_name="Bachelor of Arts in Chicano/Latino Studies",
        department="Department of Chicano/Latino Studies", cip="05.0203", duration_months=48,
        keywords=["Chicano studies", "Latino studies"],
        description=(
            "Chicano/Latino studies is an interdisciplinary study of Americans of Latino "
            "heritage across language, history, culture, sociology, politics, health, and the "
            "creative fields."
        ),
        who_its_for=(
            "Students applying the field across education, law, health, and community "
            "work."
        ),
    ),
    dict(
        slug="uci-cognitive-sciences-bs", school=_SOCSCI, degree_type="bachelors",
        program_name="Bachelor of Science in Cognitive Sciences",
        department="Department of Cognitive Sciences", cip="30.2501", duration_months=48,
        keywords=["cognitive science"],
        description=(
            "Cognitive sciences exposes students to the theoretical foundations and experimental "
            "and computational methods of cognitive science and neuroscience, weaving "
            "psychology, mathematics, statistics, and computer science."
        ),
        who_its_for=(
            "Students studying mind and brain through quantitative and experimental "
            "methods."
        ),
    ),
    dict(
        slug="uci-economics-ba", school=_SOCSCI, degree_type="bachelors",
        program_name="Bachelor of Arts in Economics",
        department="Department of Economics", cip="45.0601", duration_months=48,
        keywords=["economics"],
        description=(
            "Economics offers a broad education applicable to business, law, and government and "
            "a foundation for graduate study in the social sciences."
        ),
        who_its_for="Students pursuing business, law, government, or graduate economics.",
    ),
    dict(
        slug="uci-international-studies-ba", school=_SOCSCI, degree_type="bachelors",
        program_name="Bachelor of Arts in International Studies",
        department="Department of Global and International Studies",
        cip="30.2001", duration_months=48,
        keywords=["international studies"],
        description=(
            "International studies offers an interdisciplinary perspective on global politics, "
            "economics, cultures, and history, with required language competency and "
            "international experience."
        ),
        who_its_for="Students pursuing international policy, business, organizations, and NGOs.",
    ),
    dict(
        slug="uci-language-science-ba", school=_SOCSCI, degree_type="bachelors",
        program_name="Bachelor of Arts in Language Science",
        department="Department of Language Science", cip="16.0102", duration_months=48,
        keywords=["language science", "linguistics"],
        description=(
            "Language science combines theoretical linguistics and language development and use "
            "with neuroscience, psychology, logic, and computer science, building the analytical "
            "tools of formal language study."
        ),
        who_its_for=(
            "Students pursuing language technology, teaching, speech sciences, and "
            "research."
        ),
    ),
    dict(
        slug="uci-political-science-ba", school=_SOCSCI, degree_type="bachelors",
        program_name="Bachelor of Arts in Political Science",
        department="Department of Political Science", cip="45.1001", duration_months=48,
        keywords=["political science"],
        description=(
            "Political science explores how politics works at the individual, group, national, "
            "and international levels across American politics, comparative politics, "
            "international relations, public law, and political theory."
        ),
        who_its_for="Students pursuing law, government, policy, and many professional fields.",
    ),
    dict(
        slug="uci-psychology-bs", school=_SOCSCI, degree_type="bachelors",
        program_name="Bachelor of Science in Psychology",
        department="Department of Cognitive Sciences", cip="42.0101", duration_months=48,
        keywords=["psychology", "brain sciences"],
        description=(
            "This psychology degree emphasizes the study of the mind and brain grounded in the "
            "physical and biological sciences, across cognitive, developmental, clinical, and "
            "cognitive-neuroscience coursework."
        ),
        who_its_for=(
            "Students drawn to the science of mind who want research or "
            "health-profession paths."
        ),
    ),
    dict(
        slug="uci-quantitative-economics-ba", school=_SOCSCI, degree_type="bachelors",
        program_name="Bachelor of Arts in Quantitative Economics",
        department="Department of Economics", cip="45.0603", duration_months=48,
        keywords=["quantitative economics", "econometrics"],
        description=(
            "Quantitative economics emphasizes rigorous economic analysis and quantitative "
            "methods, the strongest preparation for finance, graduate study, and "
            "M.B.A. programs."
        ),
        who_its_for="Students pursuing finance, law, and graduate study in the social sciences.",
    ),
    dict(
        slug="uci-social-policy-public-service-ba", school=_SOCSCI, degree_type="bachelors",
        program_name="Bachelor of Arts in Social Policy and Public Service",
        department="School of Social Sciences", cip="44.0501", duration_months=48,
        keywords=["social policy", "public service"],
        tracks=["Education", "Governance", "Health"],
        description=(
            "Social policy and public service uses the social sciences to analyze inequality, "
            "policy, and social institutions, with required fieldwork and a focus area in "
            "education, governance, or health."
        ),
        who_its_for=(
            "Students pursuing government, nonprofits, public administration, and "
            "public health."
        ),
    ),
    dict(
        slug="uci-sociology-ba", school=_SOCSCI, degree_type="bachelors",
        program_name="Bachelor of Arts in Sociology",
        department="Department of Sociology", cip="45.1101", duration_months=48,
        keywords=["sociology"],
        description=(
            "Sociology studies patterns of relationships among people and how cooperation and "
            "conflict among groups shape social structure and social change, with empirical "
            "research across organizations, work, gender, and networks."
        ),
        who_its_for="Students pursuing business, education, law, social work, and research.",
    ),
    # ── School of Social Ecology ──
    dict(
        slug="uci-criminology-law-society-ba", school=_SOCECO, degree_type="bachelors",
        program_name="Bachelor of Arts in Criminology, Law and Society",
        department="Department of Criminology, Law and Society", cip="45.0401", duration_months=48,
        keywords=["criminology", "law and society"],
        description=(
            "Criminology, law and society surveys the American legal system and the regulation "
            "of behavior, crime, and responses to crime through anthropological, economic, "
            "historical, political, and sociological approaches."
        ),
        who_its_for="Students pursuing criminal justice, public policy, legal services, and law.",
    ),
    dict(
        slug="uci-psychology-ba", school=_SOCECO, degree_type="bachelors",
        program_name="Bachelor of Arts in Psychology",
        department="Department of Psychological Science", cip="42.0101", duration_months=48,
        keywords=["psychology", "health"],
        description=(
            "This psychology degree studies the determinants of human health, well-being, and "
            "functioning across developmental, social, cultural, and environmental contexts, "
            "with field study."
        ),
        who_its_for=(
            "Students pursuing public health, health services, counseling, and graduate "
            "psychology."
        ),
    ),
    dict(
        slug="uci-social-ecology-ba", school=_SOCECO, degree_type="bachelors",
        program_name="Bachelor of Arts in Social Ecology",
        department="School of Social Ecology", cip="45.0101", duration_months=48,
        keywords=["social ecology"],
        description=(
            "Social ecology takes an interdisciplinary approach across criminology, "
            "psychological science, and urban planning and public policy to understand social, "
            "psychological, environmental, and legal problems."
        ),
        who_its_for=(
            "Students who want an interdisciplinary, problem-focused social-science "
            "degree."
        ),
    ),
    dict(
        slug="uci-urban-studies-ba", school=_SOCECO, degree_type="bachelors",
        program_name="Bachelor of Arts in Urban Studies",
        department="Department of Urban Planning and Public Policy",
        cip="45.1201", duration_months=48,
        keywords=["urban studies"],
        description=(
            "Urban studies introduces the global challenges of urbanization and the analytical "
            "skills to address them across planning, development, transportation, and housing."
        ),
        who_its_for="Students pursuing urban planning, community development, and housing careers.",
    ),
    # ── Claire Trevor School of the Arts ──
    dict(
        slug="uci-art-ba", school=_ARTS, degree_type="bachelors",
        program_name="Bachelor of Arts in Art",
        department="Department of Art", cip="50.0701", duration_months=48,
        keywords=["studio art"],
        description=(
            "Art takes a wide-ranging, interdisciplinary view of contemporary practice with an "
            "emphasis on experimentation across drawing, painting, sculpture, photography, "
            "digital imaging, video, and performance art."
        ),
        who_its_for="Students pursuing studio practice, the art world, or graduate study in art.",
    ),
    dict(
        slug="uci-dance-ba", school=_ARTS, degree_type="bachelors",
        program_name="Bachelor of Arts in Dance",
        department="Department of Dance", cip="50.0301", duration_months=48,
        keywords=["dance"],
        description=(
            "The dance B.A. provides a broad undergraduate background in performance and "
            "choreography with intellectual depth, preparing students for careers or graduate "
            "work and related fields."
        ),
        who_its_for=(
            "Students seeking a broad dance education across performance and related "
            "fields."
        ),
    ),
    dict(
        slug="uci-dance-bfa", school=_ARTS, degree_type="bachelors",
        program_name="Bachelor of Fine Arts in Dance",
        department="Department of Dance", cip="50.0301", duration_months=48,
        keywords=["dance", "performance"],
        description=(
            "The dance B.F.A. is an intensive, conservatory-style program with specializations in "
            "performance and choreography for students preparing for professional dance careers."
        ),
        who_its_for="Students preparing intensively for professional performance and choreography.",
    ),
    dict(
        slug="uci-drama-ba", school=_ARTS, degree_type="bachelors",
        program_name="Bachelor of Arts in Drama",
        department="Department of Drama", cip="50.0501", duration_months=48,
        keywords=["drama", "theatre"],
        description=(
            "Drama is a comprehensive study of acting, directing, design, music theatre, "
            "playwriting, stage management, and dramatic theory, criticism, literature, and "
            "history."
        ),
        who_its_for="Students pursuing theatre and film or applying performance skills broadly.",
    ),
    dict(
        slug="uci-music-ba", school=_ARTS, degree_type="bachelors",
        program_name="Bachelor of Arts in Music",
        department="Department of Music", cip="50.0901", duration_months=48,
        keywords=["music"],
        description=(
            "The music B.A. provides a broad, flexible foundation in music studies with an "
            "emphasis in history and theory of music or in integrated composition, "
            "improvisation, and technology."
        ),
        who_its_for="Students seeking a flexible music degree alongside other interests.",
    ),
    dict(
        slug="uci-music-bmus", school=_ARTS, degree_type="bachelors",
        program_name="Bachelor of Music",
        department="Department of Music", cip="50.0903", duration_months=48,
        keywords=["music performance"],
        tracks=["Piano", "Vocal Arts", "Strings"],
        description=(
            "The Bachelor of Music is pre-professional training in Western classical performance "
            "with specializations in piano, vocal arts, and strings, culminating in a senior "
            "solo recital."
        ),
        who_its_for="Students aspiring to careers as professional classical performers.",
    ),
    dict(
        slug="uci-music-theatre-bfa", school=_ARTS, degree_type="bachelors",
        program_name="Bachelor of Fine Arts in Music Theatre",
        department="Department of Drama", cip="50.0509", duration_months=48,
        keywords=["music theatre", "musical theatre"],
        description=(
            "The music theatre B.F.A. offers high-level training in song repertoire, audition "
            "and dance technique, singing for the stage, and the history of the American "
            "musical."
        ),
        who_its_for="Students pursuing professional musical-theatre performance careers.",
    ),
    # ── The Paul Merage School of Business (undergraduate) ──
    dict(
        slug="uci-business-administration-ba", school=_MERAGE, degree_type="bachelors",
        program_name="Bachelor of Arts in Business Administration",
        department="Paul Merage School of Business", cip="52.0201", duration_months=48,
        keywords=["business administration"],
        description=(
            "Business administration prepares students with management theory and practice — "
            "leadership, strategy, finance, technology, and marketing — emphasizing teamwork, "
            "analytical problem-solving, and digital transformation from an international "
            "perspective."
        ),
        who_its_for="Students pursuing varied business and management careers.",
    ),
    # ── School of Education (undergraduate) ──
    dict(
        slug="uci-education-sciences-ba", school=_EDU, degree_type="bachelors",
        program_name="Bachelor of Arts in Education Sciences",
        department="School of Education", cip="13.0101", duration_months=48,
        keywords=["education sciences"],
        description=(
            "Education sciences studies human development, learning, social structures, and "
            "education policy and organizations, drawing on cognitive science, developmental "
            "psychology, economics, and sociology."
        ),
        who_its_for=(
            "Students pursuing education, policy, research, and advanced degrees in "
            "teaching."
        ),
    ),
    # ── Sue & Bill Gross School of Nursing (undergraduate) ──
    dict(
        slug="uci-nursing-science-bs", school=_NURSING, degree_type="bachelors",
        program_name="Bachelor of Science in Nursing Science",
        department="Sue & Bill Gross School of Nursing", cip="51.3801", duration_months=48,
        keywords=["nursing"],
        description=(
            "Nursing science prepares generalist professional nurses through theory and "
            "research-based clinical experiences, with graduates eligible for the NCLEX "
            "licensing examination."
        ),
        who_its_for="Students preparing for professional registered-nursing practice.",
    ),
    # ── Joe C. Wen School of Population and Public Health (undergraduate) ──
    dict(
        slug="uci-public-health-policy-ba", school=_PUBHEALTH, degree_type="bachelors",
        program_name="Bachelor of Arts in Public Health Policy",
        department="Joe C. Wen School of Population and Public Health",
        cip="51.2201", duration_months=48,
        keywords=["public health policy"],
        description=(
            "Public health policy trains students in multidisciplinary public-health practice "
            "and research with an emphasis on administration, planning, advocacy, and "
            "policy-oriented roles."
        ),
        who_its_for="Students pursuing health administration, planning, advocacy, and policy.",
    ),
    dict(
        slug="uci-public-health-sciences-bs", school=_PUBHEALTH, degree_type="bachelors",
        program_name="Bachelor of Science in Public Health Sciences",
        department="Joe C. Wen School of Population and Public Health",
        cip="51.2207", duration_months=48,
        keywords=["public health sciences"],
        description=(
            "Public health sciences trains students in the quantitative and qualitative "
            "dimensions of public health practice and research across levels of analysis."
        ),
        who_its_for="Students pursuing public-health agencies, laboratories, and graduate study.",
    ),
    # ── School of Pharmacy and Pharmaceutical Sciences (undergraduate) ──
    dict(
        slug="uci-pharmaceutical-sciences-bs", school=_PHARM, degree_type="bachelors",
        program_name="Bachelor of Science in Pharmaceutical Sciences",
        department="Department of Pharmaceutical Sciences", cip="51.2010", duration_months=48,
        keywords=["pharmaceutical sciences"],
        tracks=["Medicinal Pharmacology"],
        description=(
            "Pharmaceutical sciences trains students across chemical synthesis, molecular "
            "assays, biopharmaceutical techniques, diagnostics, computational chemistry, and "
            "gene therapies, with a specialization in medicinal pharmacology."
        ),
        who_its_for="Students bound for pharmaceutical careers or graduate and professional study.",
    ),
    # ── Interdisciplinary programs ──
    dict(
        slug="uci-computer-science-engineering-bs", school=_ENGR, degree_type="bachelors",
        program_name="Bachelor of Science in Computer Science and Engineering",
        department="Interdisciplinary Program in Computer Science and Engineering",
        cip="14.0901", duration_months=48,
        keywords=["computer science and engineering"],
        description=(
            "Computer science and engineering joins computer-science fundamentals in hardware "
            "and software with engineering methods for computer systems and software design, "
            "from circuits to network architecture and digital signal processing."
        ),
        who_its_for="Students building computing infrastructure across hardware and software.",
    ),
    dict(
        slug="uci-business-information-management-bs", school=_ICS, degree_type="bachelors",
        program_name="Bachelor of Science in Business Information Management",
        department="Interdisciplinary Program in Business Information Management",
        cip="52.1201", duration_months=48,
        keywords=["business information management", "analytics"],
        description=(
            "Business information management integrates computing fundamentals, business "
            "foundations, and analytical methods so graduates can use technology and analytics "
            "to meet business goals."
        ),
        who_its_for=(
            "Students bridging technology and business in for-profit and nonprofit "
            "sectors."
        ),
    ),
    dict(
        slug="uci-environmental-science-policy-ba", school=_BIO, degree_type="bachelors",
        program_name="Bachelor of Arts in Environmental Science and Policy",
        department="Interdisciplinary Program in Environmental Science and Policy",
        cip="03.0103", duration_months=48,
        keywords=["environmental science", "environmental policy"],
        description=(
            "Environmental science and policy links the natural sciences with socioeconomic "
            "factors and public policy, merging environmental science, chemistry, and biology "
            "with law, policy, and economics for environmental problem-solving."
        ),
        who_its_for=(
            "Students pursuing environmental policy, resource management, and "
            "environmental law."
        ),
    ),
]


# ============================ ACADEMIC GRADUATE PROGRAMS ============================
# One row per graduate field at its primary/terminal degree. Research doctorates are funded;
# state-supported academic master's (M.A./M.S./M.F.A.) carry the standard UC non-resident
# graduate rate. Self-supporting professional master's appear in the professional section.
_GRAD = [
    # ── School of Humanities ──
    dict(
        slug="uci-english-phd", school=_HUM, degree_type="phd",
        program_name="Doctor of Philosophy in English",
        department="Department of English", cip="23.0101", duration_months=60, funded=True,
        keywords=["English", "literature"],
        description=(
            "English doctoral research studies literature in English across periods, genres, and "
            "critical theory, with strengths in literary history, poetics, and the relationship "
            "of literature to culture and media."
        ),
        who_its_for="Scholars pursuing literary research and university teaching.",
    ),
    dict(
        slug="uci-comparative-literature-phd", school=_HUM, degree_type="phd",
        program_name="Doctor of Philosophy in Comparative Literature",
        department="Department of Comparative Literature",
        cip="16.0104", duration_months=60, funded=True,
        keywords=["comparative literature"],
        description=(
            "Comparative literature doctoral research studies texts across languages and "
            "national traditions alongside critical theory, translation, and the relationship of "
            "literature to other media."
        ),
        who_its_for="Multilingual scholars pursuing literary research across traditions.",
    ),
    dict(
        slug="uci-classics-phd", school=_HUM, degree_type="phd",
        program_name="Doctor of Philosophy in Classics",
        department="Department of Classics", cip="16.1200", duration_months=60, funded=True,
        keywords=["classics"],
        description=(
            "Classics doctoral research studies the languages, literature, history, and material "
            "culture of the ancient Greek and Roman worlds."
        ),
        who_its_for="Scholars of Greek and Roman antiquity pursuing research and teaching.",
    ),
    dict(
        slug="uci-history-phd", school=_HUM, degree_type="phd",
        program_name="Doctor of Philosophy in History",
        department="Department of History", cip="54.0101", duration_months=60, funded=True,
        keywords=["history"],
        description=(
            "History doctoral research develops original scholarship and the methods of "
            "historical research and teaching across geographic and thematic fields."
        ),
        who_its_for="Scholars pursuing professional research and teaching in history.",
    ),
    dict(
        slug="uci-east-asian-studies-phd", school=_HUM, degree_type="phd",
        program_name="Doctor of Philosophy in East Asian Studies",
        department="Department of East Asian Studies",
        cip="05.0104", duration_months=60, funded=True,
        keywords=["East Asian studies"],
        description=(
            "East Asian studies doctoral research investigates the languages, literatures, and "
            "cultures of East Asia through interdisciplinary humanistic study."
        ),
        who_its_for="Scholars of East Asian languages and cultures.",
    ),
    dict(
        slug="uci-german-phd", school=_HUM, degree_type="phd",
        program_name="Doctor of Philosophy in German",
        department="Department of European Languages and Studies",
        cip="16.0501", duration_months=60, funded=True,
        keywords=["German studies"],
        description=(
            "German doctoral research studies German-language literature, thought, and culture "
            "within broader European intellectual traditions."
        ),
        who_its_for="Scholars of German literature and culture.",
    ),
    dict(
        slug="uci-spanish-phd", school=_HUM, degree_type="phd",
        program_name="Doctor of Philosophy in Spanish",
        department="Department of Spanish and Portuguese",
        cip="16.0905", duration_months=60, funded=True,
        keywords=["Spanish"],
        description=(
            "Spanish doctoral research investigates the literatures and cultures of Spain and "
            "Latin America and the broader Hispanic and Lusophone world."
        ),
        who_its_for="Scholars of Hispanic literature and culture.",
    ),
    dict(
        slug="uci-philosophy-phd", school=_HUM, degree_type="phd",
        program_name="Doctor of Philosophy in Philosophy",
        department="Department of Philosophy", cip="38.0101", duration_months=60, funded=True,
        keywords=["philosophy"],
        description=(
            "Philosophy doctoral research develops original work across the central areas of the "
            "discipline, with notable strength in the philosophy of science and logic."
        ),
        who_its_for="Scholars pursuing research and teaching in philosophy.",
    ),
    dict(
        slug="uci-culture-and-theory-phd", school=_HUM, degree_type="phd",
        program_name="Doctor of Philosophy in Culture and Theory",
        department="Department of Comparative Literature",
        cip="05.0299", duration_months=60, funded=True,
        keywords=["culture and theory"],
        description=(
            "Culture and theory doctoral research takes an interdisciplinary, theory-driven "
            "approach to culture, power, and difference across the humanities."
        ),
        who_its_for="Scholars pursuing interdisciplinary critical and cultural theory.",
    ),
    dict(
        slug="uci-visual-studies-phd", school=_HUM, degree_type="phd",
        program_name="Doctor of Philosophy in Visual Studies",
        department="Department of Art History", cip="50.0703", duration_months=60, funded=True,
        keywords=["visual studies"],
        description=(
            "Visual studies doctoral research analyzes images and visual culture across art "
            "history, media, and the histories of seeing and representation."
        ),
        who_its_for="Scholars of art history and visual culture.",
    ),
    dict(
        slug="uci-film-media-studies-phd", school=_HUM, degree_type="phd",
        program_name="Doctor of Philosophy in Film and Media Studies",
        department="Department of Film and Media Studies",
        cip="50.0601", duration_months=60, funded=True,
        keywords=["film studies", "media studies"],
        description=(
            "Film and media studies doctoral research examines cinema and media as art forms, "
            "industries, and cultural and technological systems."
        ),
        who_its_for="Scholars studying film and media history, theory, and culture.",
    ),
    dict(
        slug="uci-art-history-ma", school=_HUM, degree_type="masters",
        program_name="Master of Arts in Art History",
        department="Department of Art History", cip="50.0703", duration_months=24,
        tuition=_GRAD_TUITION_NONRES, cost_note=None,
        keywords=["art history"],
        description=(
            "This master's studies the history of art and visual culture across periods and "
            "regions, preparing students for doctoral study or arts professions."
        ),
        who_its_for="Students preparing for doctoral study or museum and arts careers.",
    ),
    dict(
        slug="uci-asian-american-studies-ma", school=_HUM, degree_type="masters",
        program_name="Master of Arts in Asian American Studies",
        department="Department of Asian American Studies", cip="05.0200", duration_months=24,
        tuition=_GRAD_TUITION_NONRES, cost_note=None,
        keywords=["Asian American studies"],
        description=(
            "This master's studies the histories, cultures, and contemporary experiences of "
            "Asian American communities through interdisciplinary, community-engaged scholarship."
        ),
        who_its_for="Students pursuing research, advocacy, or doctoral study in ethnic studies.",
    ),
    # ── School of Social Sciences ──
    dict(
        slug="uci-anthropology-phd", school=_SOCSCI, degree_type="phd",
        program_name="Doctor of Philosophy in Anthropology",
        department="Department of Anthropology", cip="45.0201", duration_months=60, funded=True,
        keywords=["anthropology"],
        description=(
            "Anthropology doctoral research studies human social and cultural life through "
            "ethnographic fieldwork and theory, with strengths in cultural, linguistic, and "
            "medical anthropology and science and technology studies."
        ),
        who_its_for="Researchers pursuing sociocultural and linguistic anthropology.",
    ),
    dict(
        slug="uci-cognitive-sciences-phd", school=_SOCSCI, degree_type="phd",
        program_name="Doctor of Philosophy in Cognitive Sciences",
        department="Department of Cognitive Sciences",
        cip="42.2701", duration_months=60, funded=True,
        keywords=["cognitive science"],
        description=(
            "Cognitive sciences doctoral research studies the mind and brain through "
            "experimental, computational, and mathematical approaches to perception, language, "
            "memory, and decision-making."
        ),
        who_its_for="Researchers studying cognition through quantitative and experimental methods.",
    ),
    dict(
        slug="uci-economics-phd", school=_SOCSCI, degree_type="phd",
        program_name="Doctor of Philosophy in Economics",
        department="Department of Economics", cip="45.0601", duration_months=60, funded=True,
        keywords=["economics"],
        description=(
            "Economics doctoral research builds fields of emphasis from microeconomic and "
            "macroeconomic theory and econometrics to applied microeconomics and "
            "experimental economics."
        ),
        who_its_for="Researchers pursuing academic, government, and private-sector economics.",
    ),
    dict(
        slug="uci-language-science-phd", school=_SOCSCI, degree_type="phd",
        program_name="Doctor of Philosophy in Language Science",
        department="Department of Language Science", cip="16.0102", duration_months=60, funded=True,
        keywords=["language science", "linguistics"],
        description=(
            "Language science doctoral research studies the structure, acquisition, processing, "
            "and computational modeling of human language across the cognitive and brain "
            "sciences."
        ),
        who_its_for="Researchers studying language as a cognitive and computational system.",
    ),
    dict(
        slug="uci-political-science-phd", school=_SOCSCI, degree_type="phd",
        program_name="Doctor of Philosophy in Political Science",
        department="Department of Political Science",
        cip="45.1001", duration_months=60, funded=True,
        keywords=["political science"],
        description=(
            "Political science doctoral research analyzes political institutions and behavior "
            "across American politics, comparative politics, international relations, and "
            "political theory."
        ),
        who_its_for="Researchers pursuing political science scholarship and university careers.",
    ),
    dict(
        slug="uci-sociology-phd", school=_SOCSCI, degree_type="phd",
        program_name="Doctor of Philosophy in Sociology",
        department="Department of Sociology", cip="45.1101", duration_months=60, funded=True,
        keywords=["sociology"],
        description=(
            "Sociology doctoral research studies social structure, inequality, and change, with "
            "strengths in immigration, social networks, and political and economic sociology."
        ),
        who_its_for="Researchers pursuing sociological scholarship and university teaching.",
    ),
    dict(
        slug="uci-global-studies-phd", school=_SOCSCI, degree_type="phd",
        program_name="Doctor of Philosophy in Global Studies",
        department="Department of Global and International Studies",
        cip="30.2001", duration_months=60, funded=True,
        keywords=["global studies"],
        description=(
            "Global studies doctoral research examines globalization, transnational politics, "
            "and the movement of people, capital, and ideas across an interdisciplinary social "
            "science."
        ),
        who_its_for="Researchers studying transnational and global processes.",
    ),
    dict(
        slug="uci-mathematical-behavioral-sciences-phd", school=_SOCSCI, degree_type="phd",
        program_name="Doctor of Philosophy in Mathematical Behavioral Sciences",
        department="Department of Cognitive Sciences",
        cip="45.0102", duration_months=60, funded=True,
        keywords=["mathematical behavioral sciences"],
        description=(
            "Mathematical behavioral sciences doctoral research applies formal and statistical "
            "models to choice, measurement, and social and cognitive behavior."
        ),
        who_its_for="Researchers building mathematical models of behavior and decision-making.",
    ),
    # ── Charlie Dunlop School of Biological Sciences ──
    dict(
        slug="uci-biological-sciences-phd", school=_BIO, degree_type="phd",
        program_name="Doctor of Philosophy in Biological Sciences",
        department="Charlie Dunlop School of Biological Sciences",
        cip="26.0101", duration_months=60, funded=True,
        keywords=["biological sciences"],
        description=(
            "Biological sciences doctoral research spans molecular biology and biochemistry, "
            "developmental and cell biology, neurobiology, and ecology and evolutionary biology."
        ),
        who_its_for="Researchers pursuing the life sciences across molecules to ecosystems.",
    ),
    dict(
        slug="uci-biomedical-sciences-phd", school=_BIO, degree_type="phd",
        program_name="Doctor of Philosophy in Biomedical Sciences",
        department="School of Medicine", cip="26.0102", duration_months=60, funded=True,
        keywords=["biomedical sciences"],
        description=(
            "Biomedical sciences doctoral research investigates the molecular and cellular basis "
            "of human health and disease in partnership with the School of Medicine."
        ),
        who_its_for="Researchers pursuing biomedical and translational science.",
    ),
    dict(
        slug="uci-mcsb-phd", school=_BIO, degree_type="phd",
        program_name="Doctor of Philosophy in Mathematical, Computational, and Systems Biology",
        department="Charlie Dunlop School of Biological Sciences",
        cip="26.1102", duration_months=60, funded=True,
        keywords=["systems biology", "computational biology"],
        description=(
            "This interdisciplinary doctorate applies mathematics, computation, and modeling to "
            "biological systems from molecules to populations across biology, physical sciences, "
            "and engineering."
        ),
        who_its_for="Quantitatively minded researchers modeling biological systems.",
    ),
    dict(
        slug="uci-conservation-restoration-science-mcrs", school=_BIO, degree_type="masters",
        program_name="Master of Conservation and Restoration Science",
        department="Charlie Dunlop School of Biological Sciences",
        cip="03.0101", duration_months=12,
        omit_tuition_reason=(
            "The Master of Conservation and Restoration Science is a self-supporting "
            "professional program whose fee is published on the program page rather than the "
            "systemwide academic schedule; a current verified annual figure is omitted."
        ),
        keywords=["conservation", "restoration ecology"],
        description=(
            "This professional master's trains students in the science and practice of "
            "conserving and restoring ecosystems, pairing ecology and data skills with applied "
            "fieldwork."
        ),
        who_its_for="Students pursuing applied careers in conservation and ecological restoration.",
    ),
    # ── School of Physical Sciences ──
    dict(
        slug="uci-chemistry-phd", school=_PHYS, degree_type="phd",
        program_name="Doctor of Philosophy in Chemistry",
        department="Department of Chemistry", cip="40.0501", duration_months=60, funded=True,
        keywords=["chemistry"],
        description=(
            "Chemistry doctoral research demonstrates breadth and depth across modern chemistry "
            "and independent research, with strengths in atmospheric and physical chemistry and "
            "an interdisciplinary chemical and materials physics concentration."
        ),
        who_its_for="Researchers pursuing chemistry careers in academia, industry, and government.",
    ),
    dict(
        slug="uci-mathematics-phd", school=_PHYS, degree_type="phd",
        program_name="Doctor of Philosophy in Mathematics",
        department="Department of Mathematics", cip="27.0101", duration_months=60, funded=True,
        keywords=["mathematics"],
        description=(
            "Mathematics doctoral research spans pure and applied mathematics, from algebra, "
            "analysis, and geometry to dynamical systems and mathematical modeling."
        ),
        who_its_for="Researchers pursuing mathematics in academia, industry, and research.",
    ),
    dict(
        slug="uci-physics-phd", school=_PHYS, degree_type="phd",
        program_name="Doctor of Philosophy in Physics",
        department="Department of Physics and Astronomy",
        cip="40.0801", duration_months=60, funded=True,
        keywords=["physics", "astronomy"],
        description=(
            "Physics and astronomy doctoral research ranges across particle physics, "
            "condensed-matter physics, astrophysics and cosmology, and biophysics, pairing "
            "theory and experiment."
        ),
        who_its_for="Researchers pursuing physics and astrophysics in academia and industry.",
    ),
    dict(
        slug="uci-earth-system-science-phd", school=_PHYS, degree_type="phd",
        program_name="Doctor of Philosophy in Earth System Science",
        department="Department of Earth System Science",
        cip="40.0699", duration_months=60, funded=True,
        keywords=["earth system science", "climate"],
        description=(
            "Earth system science doctoral research studies the coupled physics, chemistry, and "
            "biology of the atmosphere, oceans, land, and ice, with strength in climate change "
            "and the carbon and water cycles."
        ),
        who_its_for="Researchers studying climate and the Earth system.",
    ),
    dict(
        slug="uci-computational-science-phd", school=_PHYS, degree_type="phd",
        program_name="Doctor of Philosophy in Computational Science",
        department="School of Physical Sciences", cip="30.0801", duration_months=60, funded=True,
        keywords=["computational science"],
        description=(
            "This interdisciplinary doctorate develops the numerical methods, high-performance "
            "computing, and modeling that drive discovery across the physical and natural "
            "sciences."
        ),
        who_its_for="Researchers applying computation across the sciences.",
    ),
    # ── Donald Bren School of Information and Computer Sciences ──
    dict(
        slug="uci-computer-science-phd", school=_ICS, degree_type="phd",
        program_name="Doctor of Philosophy in Computer Science",
        department="Department of Computer Science", cip="11.0701", duration_months=60, funded=True,
        keywords=["computer science"],
        description=(
            "Computer science doctoral research spans artificial intelligence and machine "
            "learning, systems and networks, databases, graphics and vision, programming "
            "languages, security, and algorithms."
        ),
        who_its_for="Researchers pursuing computing research in academia and industry.",
    ),
    dict(
        slug="uci-informatics-phd", school=_ICS, degree_type="phd",
        program_name="Doctor of Philosophy in Informatics",
        department="Department of Informatics", cip="11.0104", duration_months=60, funded=True,
        keywords=["informatics", "human-centered computing"],
        description=(
            "Informatics doctoral research studies the design and use of computing in human "
            "contexts, spanning human-computer interaction, software engineering, and the "
            "social and organizational dimensions of technology."
        ),
        who_its_for="Researchers studying people, design, and software in computing.",
    ),
    dict(
        slug="uci-software-engineering-phd", school=_ICS, degree_type="phd",
        program_name="Doctor of Philosophy in Software Engineering",
        department="Department of Informatics", cip="14.0903", duration_months=60, funded=True,
        keywords=["software engineering"],
        description=(
            "Software engineering doctoral research advances the methods, tools, and theory for "
            "building large, reliable software systems across their design and evolution."
        ),
        who_its_for="Researchers advancing the engineering of software systems.",
    ),
    dict(
        slug="uci-statistics-phd", school=_ICS, degree_type="phd",
        program_name="Doctor of Philosophy in Statistics",
        department="Department of Statistics", cip="27.0501", duration_months=60, funded=True,
        keywords=["statistics"],
        description=(
            "Statistics doctoral research develops methodology and theory for data analysis and "
            "applies it across the sciences, with strengths in machine learning and Bayesian "
            "methods."
        ),
        who_its_for="Researchers developing and applying statistical methods.",
    ),
    # ── Henry Samueli School of Engineering ──
    dict(
        slug="uci-biomedical-engineering-phd", school=_ENGR, degree_type="phd",
        program_name="Doctor of Philosophy in Biomedical Engineering",
        department="Department of Biomedical Engineering",
        cip="14.0501", duration_months=60, funded=True,
        keywords=["biomedical engineering"],
        description=(
            "Biomedical engineering doctoral research integrates engineering with the biological "
            "and medical sciences across biophotonics, biomechanics, neural engineering, and "
            "medical imaging."
        ),
        who_its_for="Researchers developing technologies for human health.",
    ),
    dict(
        slug="uci-chemical-biomolecular-engineering-phd", school=_ENGR, degree_type="phd",
        program_name="Doctor of Philosophy in Chemical and Biomolecular Engineering",
        department="Department of Chemical and Biomolecular Engineering",
        cip="14.0701", duration_months=60, funded=True,
        keywords=["chemical engineering"],
        description=(
            "Chemical and biomolecular engineering doctoral research advances reaction "
            "engineering, transport, and materials and biomolecular processes for energy, "
            "health, and the environment."
        ),
        who_its_for="Researchers in chemical and biomolecular engineering.",
    ),
    dict(
        slug="uci-civil-environmental-engineering-phd", school=_ENGR, degree_type="phd",
        program_name="Doctor of Philosophy in Civil and Environmental Engineering",
        department="Department of Civil and Environmental Engineering",
        cip="14.0801", duration_months=60, funded=True,
        keywords=["civil engineering", "environmental engineering"],
        description=(
            "Civil and environmental engineering doctoral research spans structures, "
            "geotechnical and earthquake engineering, water resources, and environmental "
            "engineering for resilient infrastructure."
        ),
        who_its_for="Researchers advancing sustainable, resilient infrastructure.",
    ),
    dict(
        slug="uci-electrical-computer-engineering-phd", school=_ENGR, degree_type="phd",
        program_name="Doctor of Philosophy in Electrical and Computer Engineering",
        department="Department of Electrical Engineering and Computer Science",
        cip="14.1001", duration_months=60, funded=True,
        keywords=["electrical engineering", "computer engineering"],
        description=(
            "Electrical and computer engineering doctoral research spans circuits and devices, "
            "communications and signal processing, control, and computer engineering and "
            "embedded systems."
        ),
        who_its_for="Researchers solving problems in electrical and computer engineering.",
    ),
    dict(
        slug="uci-materials-science-engineering-phd", school=_ENGR, degree_type="phd",
        program_name="Doctor of Philosophy in Materials Science and Engineering",
        department="Department of Materials Science and Engineering",
        cip="14.1801", duration_months=60, funded=True,
        keywords=["materials science"],
        description=(
            "Materials science and engineering doctoral research studies the structure, "
            "properties, and processing of materials, with strengths in nanomaterials and "
            "electron microscopy."
        ),
        who_its_for="Researchers developing advanced materials.",
    ),
    dict(
        slug="uci-mechanical-aerospace-engineering-phd", school=_ENGR, degree_type="phd",
        program_name="Doctor of Philosophy in Mechanical and Aerospace Engineering",
        department="Department of Mechanical and Aerospace Engineering",
        cip="14.1901", duration_months=60, funded=True,
        keywords=["mechanical engineering", "aerospace engineering"],
        description=(
            "Mechanical and aerospace engineering doctoral research spans fluid and solid "
            "mechanics, combustion and energy, dynamics and control, and flight systems."
        ),
        who_its_for="Researchers in mechanical and aerospace engineering.",
    ),
    dict(
        slug="uci-transportation-science-phd", school=_SOCECO, degree_type="phd",
        program_name="Doctor of Philosophy in Transportation Science",
        department="Department of Civil and Environmental Engineering",
        cip="14.0804", duration_months=60, funded=True,
        keywords=["transportation science"],
        description=(
            "Transportation science doctoral research combines engineering, planning, behavior, "
            "and data science to model and improve transportation systems."
        ),
        who_its_for="Researchers studying transportation systems and travel behavior.",
    ),
    # ── School of Social Ecology ──
    dict(
        slug="uci-criminology-law-society-phd", school=_SOCECO, degree_type="phd",
        program_name="Doctor of Philosophy in Criminology, Law and Society",
        department="Department of Criminology, Law and Society",
        cip="45.0401", duration_months=60, funded=True,
        keywords=["criminology", "law and society"],
        description=(
            "Criminology, law and society doctoral research studies crime, law, and justice "
            "institutions through social-science theory and empirical methods."
        ),
        who_its_for="Researchers studying crime, law, and the justice system.",
    ),
    dict(
        slug="uci-psychological-science-phd", school=_SOCECO, degree_type="phd",
        program_name="Doctor of Philosophy in Psychological Science",
        department="Department of Psychological Science",
        cip="42.0101", duration_months=60, funded=True,
        keywords=["psychological science"],
        description=(
            "Psychological science doctoral research studies mind and behavior across "
            "developmental, social, health, and cognitive psychology with strong quantitative "
            "training."
        ),
        who_its_for="Researchers pursuing psychological science in academia and applied settings.",
    ),
    dict(
        slug="uci-social-ecology-phd", school=_SOCECO, degree_type="phd",
        program_name="Doctor of Philosophy in Social Ecology",
        department="School of Social Ecology", cip="30.2501", duration_months=60, funded=True,
        keywords=["social ecology"],
        description=(
            "Social ecology doctoral research takes an interdisciplinary, problem-focused "
            "approach to the relationships between people and their social and physical "
            "environments."
        ),
        who_its_for="Researchers studying people in their social and environmental contexts.",
    ),
    dict(
        slug="uci-urban-environmental-planning-policy-phd", school=_SOCECO, degree_type="phd",
        program_name="Doctor of Philosophy in Urban and Environmental Planning and Policy",
        department="Department of Urban Planning and Public Policy",
        cip="04.0301", duration_months=60, funded=True,
        keywords=["urban planning", "environmental policy"],
        description=(
            "This doctorate studies how cities and regions develop and how planning and policy "
            "shape housing, transportation, the environment, and equity."
        ),
        who_its_for="Researchers studying urban development, planning, and policy.",
    ),
    # ── Claire Trevor School of the Arts ──
    dict(
        slug="uci-art-mfa", school=_ARTS, degree_type="masters",
        program_name="Master of Fine Arts in Art",
        department="Department of Art", cip="50.0702", duration_months=24,
        tuition=_GRAD_TUITION_NONRES, cost_note=None,
        keywords=["studio art", "fine arts"],
        description=(
            "This studio M.F.A. supports interdisciplinary contemporary art practice across "
            "media, culminating in a thesis exhibition."
        ),
        who_its_for="Artists pursuing professional studio practice and exhibition.",
    ),
    dict(
        slug="uci-dance-mfa", school=_ARTS, degree_type="masters",
        program_name="Master of Fine Arts in Dance",
        department="Department of Dance", cip="50.0301", duration_months=24,
        tuition=_GRAD_TUITION_NONRES, cost_note=None,
        keywords=["dance"],
        description=(
            "This dance M.F.A. develops choreographers and performers through creative practice, "
            "dance science, and scholarship."
        ),
        who_its_for="Dance artists pursuing choreography, performance, and teaching.",
    ),
    dict(
        slug="uci-drama-mfa", school=_ARTS, degree_type="masters",
        program_name="Master of Fine Arts in Drama",
        department="Department of Drama", cip="50.0501", duration_months=36,
        tuition=_GRAD_TUITION_NONRES, cost_note=None,
        keywords=["drama", "theatre"],
        description=(
            "This drama M.F.A. offers conservatory-style training in acting, directing, and "
            "stage design within a research university."
        ),
        who_its_for="Theatre artists pursuing professional acting, directing, or design careers.",
    ),
    dict(
        slug="uci-music-mfa", school=_ARTS, degree_type="masters",
        program_name="Master of Fine Arts in Music",
        department="Department of Music", cip="50.0901", duration_months=24,
        tuition=_GRAD_TUITION_NONRES, cost_note=None,
        keywords=["music"],
        description=(
            "This music M.F.A. develops performers and composers through advanced study, "
            "performance, and creative work."
        ),
        who_its_for="Musicians pursuing performance and composition careers.",
    ),
    dict(
        slug="uci-drama-theatre-phd", school=_ARTS, degree_type="phd",
        program_name="Doctor of Philosophy in Drama and Theatre",
        department="Department of Drama", cip="50.0501", duration_months=60, funded=True,
        keywords=["drama", "theatre history"],
        description=(
            "Offered jointly with UC San Diego, this doctorate trains scholars in theatre and "
            "performance history, theory, and dramaturgy."
        ),
        who_its_for="Scholars pursuing research and teaching in theatre and performance.",
    ),
    dict(
        slug="uci-icit-phd", school=_ARTS, degree_type="phd",
        program_name=(
            "Doctor of Philosophy in Integrated Composition, Improvisation, and "
            "Technology"
        ),
        department="Department of Music", cip="50.0901", duration_months=60, funded=True,
        keywords=["composition", "music technology"],
        description=(
            "This doctorate joins composition, improvisation, and music technology in creative "
            "research at the intersection of the arts and computing."
        ),
        who_its_for="Composer-researchers working across music and technology.",
    ),
    # ── School of Education ──
    dict(
        slug="uci-education-phd", school=_EDU, degree_type="phd",
        program_name="Doctor of Philosophy in Education",
        department="School of Education", cip="13.0101", duration_months=60, funded=True,
        keywords=["education research"],
        description=(
            "Education doctoral research studies learning, teaching, and educational policy "
            "across the learning sciences, language and literacy, and educational policy and "
            "social context."
        ),
        who_its_for="Researchers and future faculty in education.",
    ),
    # ── Joe C. Wen School of Population and Public Health ──
    dict(
        slug="uci-public-health-phd", school=_PUBHEALTH, degree_type="phd",
        program_name="Doctor of Philosophy in Public Health",
        department="Joe C. Wen School of Population and Public Health",
        cip="51.2201", duration_months=60, funded=True,
        keywords=["public health"],
        description=(
            "Public health doctoral research investigates the social, environmental, and "
            "biological determinants of population health and the interventions that advance "
            "health equity."
        ),
        who_its_for="Researchers pursuing population and public health science.",
    ),
    dict(
        slug="uci-epidemiology-phd", school=_PUBHEALTH, degree_type="phd",
        program_name="Doctor of Philosophy in Epidemiology",
        department="Department of Epidemiology and Biostatistics",
        cip="26.1309", duration_months=60, funded=True,
        keywords=["epidemiology"],
        description=(
            "Epidemiology doctoral research studies the distribution and determinants of disease "
            "in populations, from chronic and infectious disease to environmental and cancer "
            "epidemiology."
        ),
        who_its_for="Researchers studying the causes and patterns of disease.",
    ),
    dict(
        slug="uci-environmental-health-sciences-phd", school=_PUBHEALTH, degree_type="phd",
        program_name="Doctor of Philosophy in Environmental Health Sciences",
        department="Department of Environmental and Occupational Health",
        cip="51.2202", duration_months=60, funded=True,
        keywords=["environmental health"],
        description=(
            "Environmental health sciences doctoral research studies how environmental and "
            "occupational exposures affect human health, from air pollution to the exposome."
        ),
        who_its_for="Researchers studying environmental determinants of health.",
    ),
    # ── Sue & Bill Gross School of Nursing ──
    dict(
        slug="uci-nursing-science-phd", school=_NURSING, degree_type="phd",
        program_name="Doctor of Philosophy in Nursing Science",
        department="Sue & Bill Gross School of Nursing",
        cip="51.3808", duration_months=60, funded=True,
        keywords=["nursing science"],
        description=(
            "Nursing science doctoral research prepares nurse scholars to advance the discipline "
            "through theory and empirical research on health and care."
        ),
        who_its_for="Nurses pursuing research and academic careers.",
    ),
    # ── School of Pharmacy and Pharmaceutical Sciences ──
    dict(
        slug="uci-pharmaceutical-sciences-phd", school=_PHARM, degree_type="phd",
        program_name="Doctor of Philosophy in Pharmacological Sciences",
        department="School of Pharmacy and Pharmaceutical Sciences",
        cip="51.2010", duration_months=60, funded=True,
        keywords=["pharmacological sciences"],
        description=(
            "Pharmacological sciences doctoral research studies how drugs act on biological "
            "systems and the discovery and development of new therapeutics."
        ),
        who_its_for="Researchers in pharmacology and drug discovery.",
    ),
    # ── The Paul Merage School of Business ──
    dict(
        slug="uci-management-phd", school=_MERAGE, degree_type="phd",
        program_name="Doctor of Philosophy in Management",
        department="Paul Merage School of Business", cip="52.0201", duration_months=60, funded=True,
        keywords=["management research"],
        description=(
            "Management doctoral research prepares scholars for academic careers across "
            "accounting, finance, marketing, operations, organization and management, and "
            "information systems."
        ),
        who_its_for="Researchers pursuing business-school faculty careers.",
    ),
]


# ============================ PROFESSIONAL & MANAGEMENT DEGREES ============================
_MBA_SRC = (
    "UC Irvine — 2025-26 MBA tuition & fees (University Registrar)",
    "https://www.reg.uci.edu/fees/2025-2026/business.html",
)
_LAW_SRC = (
    "UC Irvine — 2025-26 Law tuition & fees (University Registrar)",
    "https://www.reg.uci.edu/fees/2025-2026/law.html",
)
_LLM_SRC = (
    "UC Irvine School of Law — 2025-26 LL.M. tuition",
    "https://www.law.uci.edu/llm/tuition/",
)
_MED_SRC = (
    "UC Irvine — 2025-26 Medicine tuition & fees (University Registrar)",
    "https://www.reg.uci.edu/fees/2025-2026/medical.html",
)
_PHARMD_SRC = (
    "UC Irvine — 2025-26 PharmD tuition & fees (University Registrar)",
    "https://www.reg.uci.edu/fees/2025-2026/pharmd.html",
)
_NURSING_SRC = (
    "UC Irvine — 2025-26 Nursing (M.S.N.) tuition & fees (University Registrar)",
    "https://www.reg.uci.edu/fees/2025-2026/nursing.html",
)
_MPH_SRC = (
    "UC Irvine — 2025-26 Public Health tuition & fees (University Registrar)",
    "https://www.reg.uci.edu/fees/2025-2026/publichealth.html",
)
_SELF_SUPP_NOTE = (
    "This is a self-supporting graduate program whose fee is published on the program's own "
    "page rather than the systemwide academic schedule; a current verified annual figure is "
    "omitted rather than estimated."
)
_PROF = [
    dict(
        slug="uci-mba-full-time", school=_MERAGE, degree_type="masters",
        program_name="Master of Business Administration (Full-Time)",
        department="Paul Merage School of Business", cip="52.0201", duration_months=21,
        delivery_format="on_campus", tuition=67585, cost_source=_MBA_SRC,
        cost_note=(
            "2025-26 non-resident tuition and fees ($67,585); California residents pay about "
            "$55,340. A general-management MBA on the Irvine campus."
        ),
        keywords=["MBA", "business administration"],
        description=(
            "The Full-Time MBA is a general-management program that prepares graduates for "
            "leadership in digitally driven industries, with a cohort experience and strong ties "
            "to Southern California's technology, healthcare, and innovation economy."
        ),
        who_its_for=(
            "Early-career professionals and career changers seeking management and leadership "
            "roles, especially on the West Coast."
        ),
    ),
    dict(
        slug="uci-business-analytics-ms", school=_MERAGE, degree_type="masters",
        program_name="Master of Science in Business Analytics",
        department="Paul Merage School of Business", cip="52.1301", duration_months=12,
        delivery_format="on_campus", omit_tuition_reason=_SELF_SUPP_NOTE,
        keywords=["business analytics", "data science"],
        description=(
            "This master's builds expertise in data, marketing, and operations analytics for "
            "data-driven decision-making, pairing technical training with business strategy."
        ),
        who_its_for="Students pursuing business-analytics and data-science careers.",
    ),
    dict(
        slug="uci-finance-mfin", school=_MERAGE, degree_type="masters",
        program_name="Master of Finance",
        department="Paul Merage School of Business", cip="52.0801", duration_months=12,
        delivery_format="on_campus", omit_tuition_reason=_SELF_SUPP_NOTE,
        keywords=["finance"],
        description=(
            "This master's provides specialized training in financial management, investment, "
            "and quantitative finance for careers in financial services and corporate finance."
        ),
        who_its_for="Students pursuing careers in finance and investment.",
    ),
    dict(
        slug="uci-professional-accountancy-mpac", school=_MERAGE, degree_type="masters",
        program_name="Master of Professional Accountancy",
        department="Paul Merage School of Business", cip="52.0301", duration_months=12,
        delivery_format="on_campus", omit_tuition_reason=_SELF_SUPP_NOTE,
        keywords=["accounting", "accountancy"],
        description=(
            "This master's develops expertise in financial reporting, taxation, auditing, and "
            "assurance for careers in public and corporate accounting."
        ),
        who_its_for="Aspiring CPAs and accounting professionals.",
    ),
    dict(
        slug="uci-innovation-entrepreneurship-mie", school=_MERAGE, degree_type="masters",
        program_name="Master of Innovation and Entrepreneurship",
        department="Paul Merage School of Business", cip="52.0701", duration_months=12,
        delivery_format="on_campus", omit_tuition_reason=_SELF_SUPP_NOTE,
        keywords=["innovation", "entrepreneurship"],
        description=(
            "This master's focuses on new-venture creation and growth strategy, turning applied "
            "innovation into businesses and products."
        ),
        who_its_for="Aspiring entrepreneurs and innovation-focused leaders.",
    ),
    dict(
        slug="uci-jd", school=_LAW, degree_type="professional",
        program_name="Juris Doctor",
        department="School of Law", cip="22.0101", duration_months=36,
        delivery_format="on_campus", tuition=80300, cost_source=_LAW_SRC,
        cost_note=(
            "2025-26 non-resident tuition and fees ($80,300); California residents pay about "
            "$68,055."
        ),
        keywords=["law", "Juris Doctor"],
        description=(
            "Founded in 2009 as a model for innovation in legal education, the Juris Doctor "
            "offers a comprehensive curriculum, extensive clinical training, and a strong "
            "commitment to public service and access to justice."
        ),
        who_its_for="Aspiring attorneys, including those drawn to public-interest law.",
    ),
    dict(
        slug="uci-llm", school=_LAW, degree_type="masters",
        program_name="Master of Laws",
        department="School of Law", cip="22.0202", duration_months=10,
        delivery_format="on_campus", tuition=60000, cost_source=_LLM_SRC,
        cost_note="2025-26 full-time program fee ($60,000); a part-time track is also offered.",
        keywords=["LL.M.", "Master of Laws"],
        description=(
            "The Master of Laws gives internationally trained lawyers advanced and specialized "
            "study of the U.S. legal system in full-time and part-time tracks."
        ),
        who_its_for="Internationally trained lawyers seeking U.S. legal credentials.",
    ),
    dict(
        slug="uci-md", school=_MED, degree_type="professional",
        program_name="Doctor of Medicine",
        department="School of Medicine", cip="51.1201", duration_months=48,
        delivery_format="on_campus", tuition=62021, cost_source=_MED_SRC,
        cost_note=(
            "2025-26 non-resident tuition and fees ($62,021); California residents pay about "
            "$49,776."
        ),
        keywords=["medicine", "MD"],
        description=(
            "The Doctor of Medicine educates physicians whose backgrounds reflect California's "
            "diversity, joining high-impact medical research with evidence-based, "
            "patient-centered care through UCI Health, Orange County's only academic medical "
            "center."
        ),
        who_its_for=(
            "Future physicians, including those committed to community and "
            "diverse-population health."
        ),
    ),
    dict(
        slug="uci-pharmd", school=_PHARM, degree_type="professional",
        program_name="Doctor of Pharmacy",
        department="School of Pharmacy and Pharmaceutical Sciences",
        cip="51.2001", duration_months=48,
        delivery_format="on_campus", tuition=72022, cost_source=_PHARMD_SRC,
        cost_note=(
            "2025-26 non-resident tuition and fees ($72,022); California residents pay about "
            "$59,777."
        ),
        keywords=["pharmacy", "PharmD"],
        description=(
            "The Doctor of Pharmacy is a four-year professional degree integrating "
            "pharmaceutical, biomedical, and clinical sciences for careers across hospital, "
            "community, ambulatory, managed-care, industry, and research pharmacy."
        ),
        who_its_for="Future pharmacists across clinical, industry, and research settings.",
    ),
    dict(
        slug="uci-msn-mepn", school=_NURSING, degree_type="masters",
        program_name="Master of Science in Nursing (Master's Entry Program)",
        department="Sue & Bill Gross School of Nursing", cip="51.3801", duration_months=18,
        delivery_format="on_campus", tuition=49174, cost_source=_NURSING_SRC,
        cost_note=(
            "2025-26 non-resident tuition and fees ($49,174); California residents pay about "
            "$36,929."
        ),
        keywords=["nursing", "master's entry"],
        description=(
            "The Master's Entry Program in Nursing prepares college graduates to become "
            "registered nurses, with a concentration in community and population health nursing "
            "and training in evidence-based practice."
        ),
        who_its_for="Career changers entering nursing at the master's level.",
    ),
    dict(
        slug="uci-dnp", school=_NURSING, degree_type="professional",
        program_name="Doctor of Nursing Practice",
        department="Sue & Bill Gross School of Nursing", cip="51.3818", duration_months=36,
        delivery_format="hybrid", omit_tuition_reason=_SELF_SUPP_NOTE,
        keywords=["nursing practice", "DNP"],
        description=(
            "The Doctor of Nursing Practice develops the competencies for advanced clinical "
            "leadership in nursing and healthcare through a practice-focused doctoral program."
        ),
        who_its_for="Working nurses pursuing advanced clinical and leadership roles.",
    ),
    dict(
        slug="uci-mph", school=_PUBHEALTH, degree_type="masters",
        program_name="Master of Public Health",
        department="Joe C. Wen School of Population and Public Health",
        cip="51.2201", duration_months=24,
        delivery_format="on_campus", tuition=43957, cost_source=_MPH_SRC,
        cost_note=(
            "2025-26 non-resident tuition and fees ($43,957); California residents pay about "
            "$31,712."
        ),
        keywords=["public health", "MPH"],
        description=(
            "The Master of Public Health is the school's flagship professional degree, offered "
            "in several concentrations and aimed at achieving health equity through research, "
            "practice, and community partnership."
        ),
        who_its_for="Students entering public-health practice and leadership.",
    ),
    dict(
        slug="uci-urban-regional-planning-murp", school=_SOCECO, degree_type="masters",
        program_name="Master of Urban and Regional Planning",
        department="Department of Urban Planning and Public Policy",
        cip="04.0301", duration_months=24,
        delivery_format="on_campus", omit_tuition_reason=_SELF_SUPP_NOTE,
        keywords=["urban planning"],
        description=(
            "This professional planning master's trains students to shape housing, "
            "transportation, the environment, and community development across cities and "
            "regions."
        ),
        who_its_for="Students pursuing professional careers in urban and regional planning.",
    ),
    dict(
        slug="uci-public-policy-mpp", school=_SOCECO, degree_type="masters",
        program_name="Master of Public Policy",
        department="Department of Urban Planning and Public Policy",
        cip="44.0501", duration_months=24,
        delivery_format="on_campus", omit_tuition_reason=_SELF_SUPP_NOTE,
        keywords=["public policy"],
        description=(
            "This professional master's builds the analytic and quantitative skills to design "
            "and evaluate public policy across social, environmental, and economic problems."
        ),
        who_its_for="Students pursuing careers in policy analysis and public service.",
    ),
    dict(
        slug="uci-data-science-mds", school=_ICS, degree_type="masters",
        program_name="Master of Data Science",
        department="Donald Bren School of Information and Computer Sciences",
        cip="30.7001", duration_months=12,
        delivery_format="on_campus", omit_tuition_reason=_SELF_SUPP_NOTE,
        keywords=["data science"],
        description=(
            "This professional master's builds end-to-end data-science skills — statistics, "
            "machine learning, and large-scale computing — for analytics careers."
        ),
        who_its_for="Students pursuing data-science and machine-learning careers.",
    ),
    dict(
        slug="uci-computer-science-mcs", school=_ICS, degree_type="masters",
        program_name="Master of Computer Science",
        department="Department of Computer Science", cip="11.0701", duration_months=18,
        delivery_format="on_campus", omit_tuition_reason=_SELF_SUPP_NOTE,
        keywords=["computer science"],
        description=(
            "This professional master's deepens applied expertise across computer systems, "
            "software, and artificial intelligence for advanced computing careers."
        ),
        who_its_for="Computing professionals seeking advanced applied training.",
    ),
    dict(
        slug="uci-hcid-mhcid", school=_ICS, degree_type="masters",
        program_name="Master of Human-Computer Interaction and Design",
        department="Department of Informatics", cip="11.0104", duration_months=12,
        delivery_format="on_campus", omit_tuition_reason=_SELF_SUPP_NOTE,
        keywords=["human-computer interaction", "UX design"],
        description=(
            "This professional master's trains designers and researchers in user experience and "
            "human-centered design of interactive technology."
        ),
        who_its_for="Students pursuing UX research and interaction-design careers.",
    ),
    dict(
        slug="uci-genetic-counseling-ms", school=_MED, degree_type="masters",
        program_name="Master of Science in Genetic Counseling",
        department="School of Medicine", cip="51.1509", duration_months=24,
        delivery_format="on_campus", omit_tuition_reason=_SELF_SUPP_NOTE,
        keywords=["genetic counseling"],
        description=(
            "This professional master's trains genetic counselors to interpret genetic risk and "
            "support patients and families across clinical and research settings."
        ),
        who_its_for="Students pursuing certification and careers as genetic counselors.",
    ),
]

_REVIEWS_BY_SLUG = {
    "uci-jd": {
        "summary": (
            "Founded in 2009, UC Irvine School of Law rose quickly into the national top tier: "
            "U.S. News ranks it around #34 among U.S. law schools, and the school reports strong "
            "outcomes — first-time California bar passage near 87% for the Class of 2024 and "
            "roughly 93% full-time employment within ten months, with a national top-ranking for "
            "long-term bar-passage-required jobs. Coverage praises clinical training and "
            "public-interest focus, while noting that, as a young school, its alumni network is "
            "still maturing relative to older peers."
        ),
        "themes": [
            {"label": "Fast-rising program", "sentiment": "positive",
             "detail": "Ranked around #34 by U.S. News despite being founded only in 2009."},
            {"label": "Strong outcomes", "sentiment": "positive",
             "detail": (
                 "Class of 2024 first-time CA bar passage near 87% and about 93% full-time "
                 "employment within ten months.")},
            {"label": "Clinical and public-interest focus", "sentiment": "positive",
             "detail": "Extensive clinics and a public-service mission."},
            {"label": "Young alumni network", "sentiment": "caution",
             "detail": (
                 "As a young school, its alumni network is still maturing versus older "
                 "top-20 peers.")},
        ],
        "sources": [
            {"label": "U.S. News — UC Irvine law school profile",
             "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/university-of-california-irvine-03201"},
            {"label": "UC Irvine Law — 2026 rankings, employment, and outcomes",
             "url": "https://news.law.uci.edu/2026/05/04/uc-irvine-law-school-2026-rankings-employment-practical-training/"},
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources (U.S. News) and the "
            "school's reported outcomes — not individual verbatim reviews."
        ),
    },
    "uci-mba-full-time": {
        "summary": (
            "The Paul Merage Full-Time MBA is a small, STEM-oriented program known for "
            "innovation and analytics, ranked among the top U.S. public MBA programs (around "
            "#27 in the Financial Times U.S. ranking). The school reports about 90% of graduates "
            "employed within roughly six months, with strongest pull in Southern California "
            "technology and healthcare. Reviewers note a smaller national footprint than top-25 "
            "brands and a regional, West-Coast orientation."
        ),
        "themes": [
            {"label": "Innovation and analytics focus", "sentiment": "positive",
             "detail": (
                 "A STEM-oriented general-management MBA strong in technology and "
                 "analytics.")},
            {"label": "Employment outcomes", "sentiment": "mixed",
             "detail": (
                 "About 90% of graduates employed within roughly six months, concentrated "
                 "in the U.S. West.")},
            {"label": "Regional footprint", "sentiment": "caution",
             "detail": (
                 "A smaller national profile than top-25 brands, with strength in Southern "
                 "California.")},
        ],
        "sources": [
            {"label": "Paul Merage School — rankings",
             "url": "https://merage.uci.edu/why-merage/rankings.html"},
            {"label": "U.S. News — UC Irvine business school profile",
             "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/university-of-california-irvine-01030"},
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources (Financial Times, U.S. "
            "News) and the school's reported outcomes — not individual verbatim reviews."
        ),
    },
    "uci-md": {
        "summary": (
            "The UC Irvine School of Medicine is recognized for biomedical research and "
            "community-focused care through UCI Health, Orange County's only academic medical "
            "center; under U.S. News's tier system it places in the research tier-2 band. "
            "Coverage notes the coarseness of the med-school tiers and a mission oriented toward "
            "serving California's diverse populations."
        ),
        "themes": [
            {"label": "Academic medical center", "sentiment": "positive",
             "detail": "Anchored by UCI Health, Orange County's only academic medical center."},
            {"label": "Research strength", "sentiment": "positive",
             "detail": "Placed in U.S. News's research tier-2 band for medical schools."},
            {"label": "Coarse ranking signal", "sentiment": "caution",
             "detail": (
                 "U.S. News now reports med schools in tiers rather than exact ranks, so "
                 "comparisons are imprecise.")},
        ],
        "sources": [
            {"label": "U.S. News — UC Irvine medical school profile",
             "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-california-irvine-04009"},
            {"label": "UC Irvine — graduate programs recognized in U.S. News 2025",
             "url": "https://news.uci.edu/2025/04/08/uc-irvine-graduate-programs-recognized-among-nations-best-in-u-s-news-world-report-rankings/"},
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources (U.S. News, UC Irvine) "
            "— not individual verbatim reviews."
        ),
    },
}


_CATALOG: list[dict] = _UG + _GRAD + _PROF

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
    _seen2: set = set()
    _dn = [k for k in _name_keys if k in _seen2 or _seen2.add(k)]
    raise RuntimeError(f"duplicate (program_name, degree_type) in UC Irvine catalog: {_dn}")

# ── Outcomes (institution-wide; UCI publishes no per-program split) ──
_OUTCOMES_CONDITIONS = (
    "Institution-wide median earnings of federally aided students measured 10 years after "
    "entry (U.S. Dept. of Education College Scorecard); not a program-specific figure."
)
_OUTCOMES_INSTITUTION = {
    "median_salary": 80735,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry (institution-wide)",
    "conditions": _OUTCOMES_CONDITIONS,
    "source": "U.S. Dept. of Education College Scorecard (UC Irvine, UNITID 110653)",
    "source_url": "https://collegescorecard.ed.gov/school/?110653",
}

# ── Admissions requirement sets ────────────────────────────────────────────
_REQ_UNDERGRAD = {
    "materials": [
        "UC Application",
        "Personal insight questions",
        "Secondary-school record (self-reported, then official transcript)",
        "Test-free admissions (UC does not consider SAT/ACT scores)",
    ],
    "deadlines": {
        "application_window": "October 1 – December 2",
        "regular_decision": "December 2",
    },
    "source": "https://www.admissions.uci.edu/",
}
_REQ_GRAD_GENERIC = {
    "materials": [
        "Online graduate application",
        "Transcripts from all prior institutions",
        "Letters of recommendation",
        "Statement of purpose and personal history statement",
        "Standardized / English-proficiency scores where required by the program",
    ],
    "deadlines": {
        "note": "Deadlines vary by program; see the program's official admissions page.",
    },
    "source": "https://grad.uci.edu/admissions/",
}
_REQ_MBA = {
    "materials": [
        "Merage application + essays",
        "GMAT, GRE, or EA score (waivers considered)",
        "Undergraduate transcripts",
        "Two recommendations",
        "Resume + interview",
    ],
    "deadlines": {"round_1": "Fall", "round_2": "January", "round_3": "Spring"},
    "source": "https://merage.uci.edu/programs/",
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
    "source": "https://www.law.uci.edu/admission/",
}
_REQ_MED = {
    "materials": [
        "AMCAS application + UC Irvine secondary",
        "MCAT score",
        "Undergraduate transcripts",
        "Letters of recommendation",
        "Interviews as required",
    ],
    "deadlines": {"primary": "AMCAS deadline (see admissions site)"},
    "source": "https://som.uci.edu/",
}


def _requirements_for(spec: dict) -> dict:
    school = spec["school"]
    if school == _LAW:
        return dict(_REQ_LAW)
    if school == _MED and spec["degree_type"] == "professional":
        return dict(_REQ_MED)
    if school == _MERAGE and "mba" in spec["slug"]:
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


# A verified 5th campus photo (the seed shipped 4; gold gallery is 4-5). Author + license read
# directly from the Wikimedia Commons extmetadata API this session; the thumbnail URL resolves.
_EXTRA_CAMPUS_PHOTOS = [
    {
        "url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/"
            "Plaza_Verde_I.jpg/1920px-Plaza_Verde_I.jpg"
        ),
        "credit": "Wikimedia Commons / Alexliwiththe3 (CC BY-SA 4.0)",
    },
]


def apply(session: Session) -> bool:
    """Enrich UC Irvine to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when UC Irvine is absent — safe on fresh/CI databases.
    """
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    photos = list(school_outcomes.get("campus_photos") or [])
    have = {p.get("url") for p in photos if isinstance(p, dict)}
    for extra in _EXTRA_CAMPUS_PHOTOS:
        if extra["url"] not in have:
            photos.append(dict(extra))
            have.add(extra["url"])
    school_outcomes["campus_photos"] = photos
    school_outcomes["_standard"] = _standard(_OMITTED_INSTITUTION)
    inst.school_outcomes = school_outcomes
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    inst.founded_year = 1965
    inst.campus_setting = "suburban"
    if not inst.website_url:
        inst.website_url = "https://www.uci.edu"
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
        "tuition_usd": _UG_TUITION_NONRES,
        "breakdown": {
            "tuition_in_state": _UG_TUITION_RES,
            "tuition_out_of_state": _UG_TUITION_NONRES,
        },
        "funded": False,
        "note": (
            "Published 2025-26 UC Irvine undergraduate tuition and fees. As a public university "
            "UC Irvine charges California residents about $17,105 and non-residents about "
            "$49,679; the non-resident rate is the matcher's budget input for a national and "
            "international applicant pool."
        ),
        "source": _UG_COST_SRC[0],
        "source_url": _UG_COST_SRC[1],
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
            p.tuition = _UG_TUITION_NONRES
            p.cost_data = _undergrad_cost()
        elif spec.get("tuition") is not None:
            p.tuition = spec["tuition"]
            p.cost_data = {
                "tuition_usd": spec["tuition"],
                "funded": False,
                "note": spec.get("cost_note", ""),
                "source": (spec.get("cost_source") or _GRAD_COST_SRC)[0],
                "source_url": (spec.get("cost_source") or _GRAD_COST_SRC)[1],
                "year": "2025-26",
            }
        elif spec.get("funded"):
            p.tuition = None
            p.cost_data = {
                "funded": True,
                "note": spec.get("cost_note", _FUNDED_NOTE),
                "source": "UC Irvine Graduate Division — financial support",
                "source_url": "https://grad.uci.edu/funding/",
            }
        else:
            p.tuition = None
            p.cost_data = {
                "funded": False,
                "note": spec.get("omit_tuition_reason", (
                    "A verified per-program annual tuition figure is omitted here rather than "
                    "estimated; see the program's official cost page."
                )),
                "source": f"{spec['school']} — official program page",
                "source_url": _SCHOOL_WEBSITE.get(spec["school"], "https://www.uci.edu"),
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
        p.application_deadline = date(2026, 12, 2) if spec["degree_type"] == "bachelors" else None
    session.flush()
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
