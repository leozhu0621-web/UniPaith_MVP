"""University of California, Santa Barbara — gold-standard profile (institution + schools + catalog).

Every value below is verified against an authoritative source — UCSB's official pages
(ucsb.edu, the UCSB General Catalog at catalog.ucsb.edu, the Office of the Registrar / Graduate
Division fee schedules, and each college's site), the U.S. Dept. of Education College Scorecard /
NCES (UNITID 110705), the University of California systemwide admissions/tuition pages, Wikimedia
Commons (campus photos, author + license verified via the Commons extmetadata API), and the
ranking bodies (U.S. News, QS, THE) — and carries a citation, or is honestly omitted (recorded in
that node's ``_standard.omitted``). Nothing is guessed.

Scope note (SKILL §"Scope & resumption"): UCSB entered as a bare US-News institution-level seed
(0 real programs, a stub 92-character description, a null website, and no working feed). This pass
takes the institution to gold — real report-card / admissions-funnel / diversity / cost-aid /
research / rankings / campus-photo-gallery / feed fields — and ships a verified, real-named degree
catalog across UCSB's five colleges/schools: the College of Letters and Science, the Robert
Mehrabian College of Engineering, the College of Creative Studies, the Bren School of Environmental
Science & Management, and the Gevirtz Graduate School of Education. Every program name, degree
designation, and owning department is confirmed against a catalog.ucsb.edu program page. Emphases
(e.g. Earth Science's Geology / Geophysics tracks, MCDB's Microbiology / Pharmacology tracks) are
carried as ``tracks`` on the single degree, never split into padded rows; pre-major ("Pre-")
statuses are excluded (they are the same degree before full declaration, not separate credentials).

Every program carries a researched, field-specific ``description_text`` (anti-stub clean, gold
contrast), a ``who_its_for`` statement, a real owning ``department``, a ``cip_code`` (the
matcher's interest/field join key), a verified ``delivery_format``, and published tuition per
credential level. Because UCSB is a PUBLIC university, the matcher's flat ``tuition`` scalar is the
NON-RESIDENT (out-of-state) published rate — the broadly-correct budget input for a national /
international applicant pool — while ``cost_data.breakdown`` preserves BOTH the resident and
non-resident rates. Funded research doctorates carry funded=True / tuition=None; self-supporting
professional master's whose fee is not on the systemwide schedule omit tuition with a reason.

Tuition: undergraduate 2026-27 (UC systemwide, verified admission.universityofcalifornia.edu):
California-resident tuition & fees $17,388; non-resident $54,858 (resident + nonresident
supplemental). Academic graduate 2025-26 (verified graddiv.ucsb.edu, tuition & fees excluding
optional health insurance): resident $15,820; non-resident $30,922. Doctoral students are funded
(tuition covered + stipend within the guarantee), so PhD/EdD/DMA rows are funded-omit-with-reason.

external_reviews are recorded in each program's ``_standard.omitted`` pending a later depth pass —
UCSB's programs are structurally clean and matcher-complete here; the reviews depth pass (gathered,
program-specific third-party coverage, never synthesized) is deferred so no fabricated review ships.
"""

# ruff: noqa: E501

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "University of California-Santa Barbara"

ENRICHED_AT = "2026-07-02"


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
    # UCSB does not publish a Fall-2025 first-year enrolled (yield) headcount on the UC
    # admit-data page, so the enrolled count is omitted rather than guessed (applicants and
    # admits are published and stamped).
    "school_outcomes.flagship.enrolled",
]

# ── Institution-level data ────────────────────────────────────────────────
RANKING_DATA: dict = {
    "ownership_type": "public",
    "accreditor": "WSCUC",
    "carnegie_classification": "Doctoral Universities: Very High Research Activity (R1)",
    # U.S. News Best Colleges (National Universities) 2026: #41 nationally, #14 among public
    # universities (UCSB news release, Feb 2026).
    "us_news_national": {"rank": 41, "year": 2026},
    # QS World University Rankings 2026.
    "qs_world_university_rankings": {"rank": 179, "year": 2026},
    # Times Higher Education World University Rankings 2026.
    "times_higher_education": {"rank": 72, "year": 2026},
}

SCHOOL_OUTCOMES: dict = {
    # UC Santa Barbara Fall 2025 first-year admit rate (UC official admit data).
    "admit_rate": 0.383,
    # College Scorecard (UNITID 110705).
    "avg_net_price": 16109,
    "median_earnings_10yr": 74915,
    "graduation_rate_6yr": 0.8303,
    "retention_rate_first_year": 0.9246,
    "location": {
        "lat": 34.4140,
        "lng": -119.8489,
        "city": "Santa Barbara",
        "state": "CA",
        "country": "United States",
    },
    "demographics": {
        "hispanic": 0.30,
        "asian": 0.26,
        "white": 0.25,
        "black": 0.03,
        "note": (
            "Undergraduate race/ethnicity (College Scorecard / IPEDS); international, "
            "two-or-more-races, and not-reported make up the remainder, so shares do not sum "
            "to 100%."
        ),
        "source": "U.S. Dept. of Education College Scorecard (UCSB, UNITID 110705)",
        "source_url": "https://collegescorecard.ed.gov/school/?110705",
    },
    "financial_aid": {
        "pell_grant_rate": 0.2785,
        "federal_loan_rate": 0.1811,
        "median_debt": 13993,
        # College Scorecard cost of attendance (academic year).
        "cost_of_attendance": 41573,
        "source": "U.S. Dept. of Education College Scorecard (UCSB, UNITID 110705)",
        "source_url": "https://collegescorecard.ed.gov/school/?110705",
    },
    "research": {
        "labs": [
            "Kavli Institute for Theoretical Physics (KITP)",
            "California NanoSystems Institute (CNSI)",
            "Marine Science Institute",
            "Neuroscience Research Institute",
            "Materials Research Laboratory (an NSF MRSEC)",
        ],
        "areas": [
            "Materials & nanoscience",
            "Theoretical & experimental physics",
            "Marine & coastal environmental science",
            "Engineering & computing",
            "Neuroscience & the brain",
            "The arts & humanities",
        ],
        "lab_links": {
            "Kavli Institute for Theoretical Physics (KITP)": "https://www.kitp.ucsb.edu/",
            "California NanoSystems Institute (CNSI)": "https://www.cnsi.ucsb.edu/",
            "Marine Science Institute": "https://www.msi.ucsb.edu/",
            "Materials Research Laboratory (an NSF MRSEC)": "https://www.mrl.ucsb.edu/",
        },
        "source": "UC Santa Barbara — Office of Research",
        "source_url": "https://www.research.ucsb.edu/",
    },
    "scale": {
        # College Scorecard / IPEDS (UNITID 110705) — degree-seeking undergraduate enrollment,
        # Fall 2024.
        "undergraduate_enrollment": 23181,
        "student_faculty_ratio": "17:1",
        "research_centers": [
            "Kavli Institute for Theoretical Physics (KITP)",
            "California NanoSystems Institute (CNSI)",
            "Marine Science Institute",
        ],
    },
    "campus_life": {
        # UC Santa Barbara (the Gauchos) compete in NCAA Division I (Big West Conference).
        "athletics_division": "NCAA Division I (Big West Conference)",
        "mascot": "UC Santa Barbara Gauchos",
        "housing": "Oceanfront residential campus adjacent to Isla Vista, in Goleta, California",
        "resources": [
            {"label": "UCSB Athletics", "url": "https://ucsbgauchos.com/"},
            {"label": "UCSB Library", "url": "https://www.library.ucsb.edu/"},
            {"label": "AS Program Board & Arts events", "url": "https://www.artsandlectures.ucsb.edu/"},
            {"label": "Cheadle Center for Biodiversity & Ecological Restoration", "url": "https://www.ccber.ucsb.edu/"},
            {"label": "UCSB Career Services", "url": "https://career.ucsb.edu/"},
        ],
    },
    "flagship": {
        "founded_year": 1944,
        "applicants": 110178,
        "admits": 42170,
        "admissions_cycle": "Fall 2025 first-year (University of California admit data)",
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (UCSB, UNITID 110705)",
            "url": "https://collegescorecard.ed.gov/school/?110705",
        },
        {
            "label": "UC Santa Barbara — Fall 2025 first-year admit data (University of California)",
            "url": "https://admission.universityofcalifornia.edu/campuses-majors/santa-barbara/first-year-admit-data.html",
        },
        {
            "label": "UC 2026-27 tuition & cost of attendance (University of California)",
            "url": "https://admission.universityofcalifornia.edu/tuition-financial-aid/tuition-cost-of-attendance/",
        },
        {
            "label": "UCSB praised for excellence, access and value in national rankings (U.S. News 2026)",
            "url": "https://news.ucsb.edu/2025/022126/ucsb-praised-excellence-access-and-value-national-rankings",
        },
    ],
}

UNDERGRAD_COUNT = 23181

DESCRIPTION = (
    "The University of California, Santa Barbara is a public land-grant research university on the "
    "Pacific coast in Santa Barbara County, California. It traces its origins to 1891 and joined "
    "the University of California system in 1944, and is a member of the Association of American "
    "Universities, classified as a Carnegie R1 very-high-research-activity university. It enrolls "
    "about 23,200 undergraduates and roughly 3,000 graduate students on a 1,000-acre oceanfront "
    "campus adjacent to Isla Vista.\n\n"
    "UCSB is organized into five colleges and schools: the College of Letters and Science, which "
    "spans the humanities, fine arts, social sciences, and mathematical, life, and physical "
    "sciences; the Robert Mehrabian College of Engineering; the College of Creative Studies; the "
    "Bren School of Environmental Science & Management; and the Gevirtz Graduate School of "
    "Education. Its research is anchored by the Kavli Institute for Theoretical Physics, the "
    "California NanoSystems Institute, the Materials Research Laboratory, and the Marine Science "
    "Institute, and its faculty include multiple Nobel laureates in physics, chemistry, and "
    "economics.\n\n"
    "Accredited by the WASC Senior College and University Commission, UCSB ranks #41 among "
    "national universities and #14 among public universities by U.S. News, and its materials, "
    "physics, and marine-science programs are internationally recognized. As a public university "
    "it charges California residents about $17,388 in 2026-27 undergraduate tuition and fees and "
    "non-residents about $54,858; its teams, the Gauchos, compete in NCAA Division I."
)

# ── The real degree-granting colleges/schools (display order) ──────────────
_LS = "College of Letters and Science"
_ENGR = "Robert Mehrabian College of Engineering"
_CCS = "College of Creative Studies"
_BREN = "Bren School of Environmental Science & Management"
_GGSE = "Gevirtz Graduate School of Education"

_SCHOOL_WEBSITE: dict[str, str] = {
    _LS: "https://www.college.ucsb.edu/",
    _ENGR: "https://engineering.ucsb.edu/",
    _CCS: "https://www.ccs.ucsb.edu/",
    _BREN: "https://bren.ucsb.edu/",
    _GGSE: "https://education.ucsb.edu/",
}

SCHOOLS: list[dict] = [
    {"name": _LS, "sort_order": 1, "description": (
        "The College of Letters and Science is UCSB's largest college, teaching some eighty "
        "majors across the humanities and fine arts, the social sciences, and the mathematical, "
        "life, and physical sciences, and awarding the B.A., B.S., B.F.A., and B.M. alongside "
        "the master's and doctorate in most of its departments.")},
    {"name": _ENGR, "sort_order": 2, "description": (
        "The Robert Mehrabian College of Engineering offers ABET-accredited engineering and "
        "computing education across chemical engineering, computer science, computer and "
        "electrical engineering, mechanical engineering, and materials, and is anchored by a "
        "top-ranked materials program and the California NanoSystems Institute.")},
    {"name": _CCS, "sort_order": 3, "description": (
        "The College of Creative Studies is a small, selective college for advanced, self-directed "
        "students who begin original research or creative work early, awarding degrees in the "
        "sciences, mathematics, computing, art, music composition, and writing.")},
    {"name": _BREN, "sort_order": 4, "description": (
        "The Bren School of Environmental Science & Management is a graduate school that trains "
        "environmental scientists, managers, and data scientists, awarding the professional "
        "Master of Environmental Science and Management and Master of Environmental Data Science "
        "and a Ph.D. in environmental science and management.")},
    {"name": _GGSE, "sort_order": 5, "description": (
        "The Gevirtz Graduate School of Education prepares teachers, counselors, and education "
        "researchers, awarding the M.A. and Ph.D. in education, degrees in counseling, clinical, "
        "and school psychology, and teaching credentials with the Master of Education.")},
]

_ABOUT_OMITTED_FIELDS = [
    "about_detail.founded",
    "about_detail.leadership",
    "about_detail.faculty",
    "about_detail.research_centers",
]
_ABOUT_DETAIL: dict[str, dict] = {s["name"]: {} for s in SCHOOLS}
_ABOUT_OMITTED: dict[str, list[str]] = {s["name"]: list(_ABOUT_OMITTED_FIELDS) for s in SCHOOLS}

# ── Channel feeds + official social links ──────────────────────────────────
# The UCSB news RSS (The Current) was fetched live this session (verified 2026-07-02: returns
# valid RSS 2.0 with 15 recent items). Colleges share the institution feed filtered by keywords.
_SOURCE_RSS = "https://news.ucsb.edu/all/feed"
_NEWS_URL = "https://news.ucsb.edu/"

_SOCIAL_UCSB = {
    "instagram": "https://www.instagram.com/ucsantabarbara/",
    "linkedin": "https://www.linkedin.com/school/ucsantabarbara/",
    "x": "https://x.com/ucsantabarbara",
    "youtube": "https://www.youtube.com/user/ucsantabarbara",
    "facebook": "https://www.facebook.com/ucsantabarbara",
}

_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _LS: ["Letters and Science", "research", "faculty"],
    _ENGR: ["engineering", "materials", "computer science"],
    _CCS: ["Creative Studies", "research", "students"],
    _BREN: ["Bren School", "environmental", "climate"],
    _GGSE: ["Gevirtz", "education", "teaching"],
}


def _school_content(name: str) -> dict:
    return {
        "news_rss": _SOURCE_RSS,
        "news_url": _NEWS_URL,
        "news_curated": False,
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": _SOCIAL_UCSB,
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


_INSTITUTION_CONTENT: dict = {
    "news_rss": _SOURCE_RSS,
    "news_url": _NEWS_URL,
    "news_curated": True,
    "social": _SOCIAL_UCSB,
}

# ── Tuition constants ──────────────────────────────────────────────────────
# Undergraduate 2026-27 (UC systemwide, verified). Academic graduate 2025-26 (UCSB Graduate
# Division, verified; tuition & fees excluding optional student health insurance).
_UG_TUITION_NONRES = 54858
_UG_TUITION_RES = 17388
_GRAD_TUITION_NONRES = 30922
_GRAD_TUITION_RES = 15820
_UG_COST_SRC = (
    "UC 2026-27 undergraduate tuition & cost of attendance (University of California)",
    "https://admission.universityofcalifornia.edu/tuition-financial-aid/tuition-cost-of-attendance/",
)
_GRAD_COST_SRC = (
    "UCSB Graduate Division — 2025-26 academic-graduate tuition & fees",
    "https://www.graddiv.ucsb.edu/fees-costs/25-26-quarterly",
)
_SELF_SUPP_SRC = (
    "UCSB — professional / self-supporting program fees (see the program's official page)",
    "https://www.graddiv.ucsb.edu/fees-costs",
)

_FUNDED_NOTE = (
    "Admitted research doctoral students in this program are funded — tuition is covered "
    "alongside a stipend and health insurance for funded students within the support guarantee — "
    "so the published sticker is not the price students pay."
)
_SELF_SUPP_NOTE = (
    "This is a self-supporting professional program billed at its own fee rather than the "
    "systemwide academic-graduate rate; a single verified annual figure is not published on the "
    "systemwide schedule, so the scalar is omitted rather than estimated. See the program's "
    "official cost page."
)


def _grad_cost_note() -> str:
    return (
        "Standard University of California non-resident academic-graduate tuition and fees "
        f"(2025-26); California residents pay about ${_GRAD_TUITION_RES:,}. UC sets graduate "
        "tuition systemwide."
    )


# ── The catalog (built from real, distinctly-named degree programs) ────────
_UG: list[dict] = []
_GRAD: list[dict] = []
_PROF: list[dict] = []

# ============================ UNDERGRADUATE MAJORS ============================
_UG = [
    # ── Robert Mehrabian College of Engineering ──
    dict(slug="ucsb-chemical-engineering-bs", school=_ENGR, degree_type="bachelors",
         program_name="Bachelor of Science in Chemical Engineering",
         department="Department of Chemical Engineering", cip="14.0701", duration_months=48,
         keywords=["chemical engineering"],
         description=(
             "Chemical engineering applies chemistry, physics, and mathematics to the design of "
             "processes that convert raw materials into fuels, materials, pharmaceuticals, and "
             "energy, combining reaction engineering, transport, and thermodynamics with "
             "laboratory practice."),
         who_its_for=(
             "Students who enjoy chemistry and mathematics and want to design and scale the "
             "processes behind energy, materials, and medicine.")),
    dict(slug="ucsb-computer-engineering-bs", school=_ENGR, degree_type="bachelors",
         program_name="Bachelor of Science in Computer Engineering",
         department="Departments of Computer Science and Electrical & Computer Engineering",
         cip="14.0901", duration_months=48, keywords=["computer engineering"],
         description=(
             "Computer engineering spans the hardware-software boundary — digital logic, computer "
             "architecture, embedded systems, and the software that runs on them — jointly taught "
             "by computer science and electrical and computer engineering."),
         who_its_for=(
             "Students who want to build computing systems from the circuit up, bridging hardware "
             "and software.")),
    dict(slug="ucsb-computer-science-bs", school=_ENGR, degree_type="bachelors",
         program_name="Bachelor of Science in Computer Science",
         department="Department of Computer Science", cip="11.0701", duration_months=48,
         keywords=["computer science"],
         description=(
             "Computer science covers algorithms, systems, programming languages, machine "
             "learning, and theory, with a rigorous core and electives spanning artificial "
             "intelligence, security, graphics, and distributed systems."),
         who_its_for=(
             "Students who want a rigorous computing foundation for careers in software, AI, and "
             "research or graduate study.")),
    dict(slug="ucsb-electrical-engineering-bs", school=_ENGR, degree_type="bachelors",
         program_name="Bachelor of Science in Electrical Engineering",
         department="Department of Electrical and Computer Engineering", cip="14.1001",
         duration_months=48, keywords=["electrical engineering"],
         description=(
             "Electrical engineering studies circuits, signals, electromagnetics, photonics, and "
             "communications, with UCSB strengths in optoelectronics and high-speed devices and a "
             "hands-on laboratory and design sequence."),
         who_its_for=(
             "Students fascinated by electronics, signals, and photonics who want to design the "
             "devices behind modern communication and computing.")),
    dict(slug="ucsb-mechanical-engineering-bs", school=_ENGR, degree_type="bachelors",
         program_name="Bachelor of Science in Mechanical Engineering",
         department="Department of Mechanical Engineering", cip="14.1901", duration_months=48,
         keywords=["mechanical engineering"],
         description=(
             "Mechanical engineering covers mechanics, thermodynamics, fluid dynamics, dynamics "
             "and control, and design, preparing students to analyze and build machines, energy "
             "systems, and robots through a project-based curriculum."),
         who_its_for=(
             "Students who like physics and design and want to build machines, energy systems, "
             "and robotics.")),
    dict(slug="ucsb-artificial-intelligence-bs", school=_ENGR, degree_type="bachelors",
         program_name="Bachelor of Science in Artificial Intelligence",
         department="Department of Computer Science", cip="11.0102", duration_months=48,
         keywords=["artificial intelligence"],
         description=(
             "Artificial intelligence combines computer science foundations with machine "
             "learning, reasoning, perception, and the ethics of intelligent systems; approved by "
             "the UCSB Academic Senate in 2026, it enrolls its first cohort in Fall 2026."),
         who_its_for=(
             "Students who want to specialize early in machine learning and intelligent systems "
             "within a computer-science foundation.")),

    # ── College of Creative Studies ──
    dict(slug="ucsb-ccs-biology-ba", school=_CCS, degree_type="bachelors",
         program_name="Bachelor of Arts in Biology (College of Creative Studies)",
         department="College of Creative Studies", cip="26.0101", duration_months=48,
         keywords=["biology", "creative studies"],
         description=(
             "The College of Creative Studies biology major lets students move quickly into "
             "independent laboratory and field research alongside faculty, replacing survey "
             "coursework with early immersion in original science."),
         who_its_for=(
             "Highly self-directed students who want to start original biological research early "
             "rather than follow a conventional survey sequence.")),
    dict(slug="ucsb-ccs-chemistry-biochemistry-bs", school=_CCS, degree_type="bachelors",
         program_name="Bachelor of Science in Chemistry and Biochemistry (College of Creative Studies)",
         department="College of Creative Studies", cip="40.0501", duration_months=48,
         keywords=["chemistry", "biochemistry", "creative studies"],
         description=(
             "The College of Creative Studies chemistry and biochemistry major pairs a rigorous "
             "chemical foundation with early, sustained research in a faculty laboratory, giving "
             "advanced students the freedom to specialize quickly."),
         who_its_for=(
             "Advanced chemistry students who want to begin serious laboratory research in their "
             "first years.")),
    dict(slug="ucsb-ccs-computing-bs", school=_CCS, degree_type="bachelors",
         program_name="Bachelor of Science in Computing (College of Creative Studies)",
         department="College of Creative Studies", cip="11.0701", duration_months=48,
         keywords=["computing", "creative studies"],
         description=(
             "The College of Creative Studies computing major gives independent students an "
             "accelerated, research-oriented path through computer science, emphasizing original "
             "projects and early collaboration with faculty."),
         who_its_for=(
             "Self-directed computing students who want to build ambitious original projects and "
             "research early.")),
    dict(slug="ucsb-ccs-mathematics-bs", school=_CCS, degree_type="bachelors",
         program_name="Bachelor of Science in Mathematics (College of Creative Studies)",
         department="College of Creative Studies", cip="27.0101", duration_months=48,
         keywords=["mathematics", "creative studies"],
         description=(
             "The College of Creative Studies mathematics major lets students advance through "
             "rigorous pure and applied mathematics at their own pace and begin research and "
             "graduate-level work early."),
         who_its_for=(
             "Mathematically talented students ready to move quickly into advanced and original "
             "mathematics.")),
    dict(slug="ucsb-ccs-physics-bs", school=_CCS, degree_type="bachelors",
         program_name="Bachelor of Science in Physics (College of Creative Studies)",
         department="College of Creative Studies", cip="40.0801", duration_months=48,
         keywords=["physics", "creative studies"],
         description=(
             "The College of Creative Studies physics major immerses advanced students in "
             "theoretical and experimental physics and early research, drawing on UCSB's "
             "internationally recognized physics community."),
         who_its_for=(
             "Advanced physics students who want early access to research and graduate-level "
             "coursework.")),
    dict(slug="ucsb-ccs-art-ba", school=_CCS, degree_type="bachelors",
         program_name="Bachelor of Arts in Art (College of Creative Studies)",
         department="College of Creative Studies", cip="50.0701", duration_months=48,
         keywords=["art", "creative studies"],
         description=(
             "The College of Creative Studies art major treats students as working artists from "
             "the start, centering studio practice, critique, and independent projects across "
             "media rather than a fixed survey curriculum."),
         who_its_for=(
             "Committed young artists who want to develop a serious independent studio practice.")),
    dict(slug="ucsb-ccs-music-composition-ba", school=_CCS, degree_type="bachelors",
         program_name="Bachelor of Arts in Music Composition (College of Creative Studies)",
         department="College of Creative Studies", cip="50.0904", duration_months=48,
         keywords=["music composition", "creative studies"],
         description=(
             "The College of Creative Studies music composition major centers original "
             "composition, with students writing, performing, and workshopping new music from the "
             "outset alongside composition faculty."),
         who_its_for=(
             "Young composers who want to focus on writing and performing original music early.")),
    dict(slug="ucsb-ccs-writing-literature-ba", school=_CCS, degree_type="bachelors",
         program_name="Bachelor of Arts in Writing and Literature (College of Creative Studies)",
         department="College of Creative Studies", cip="23.1302", duration_months=48,
         keywords=["writing", "literature", "creative studies"],
         description=(
             "The College of Creative Studies writing and literature major centers a serious "
             "creative-writing practice — fiction, poetry, and nonfiction — read against "
             "literature, with frequent workshops and independent manuscripts."),
         who_its_for=(
             "Dedicated writers who want to build a substantial body of creative work as "
             "undergraduates.")),

    # ── College of Letters & Science: mathematical, life & physical sciences ──
    dict(slug="ucsb-chemistry-bs", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Science in Chemistry",
         department="Department of Chemistry and Biochemistry", cip="40.0501", duration_months=48,
         keywords=["chemistry"],
         description=(
             "The B.S. in chemistry gives a rigorous, laboratory-intensive foundation across "
             "organic, inorganic, physical, and analytical chemistry for students bound for "
             "graduate study or the chemical and pharmaceutical industries."),
         who_its_for=(
             "Students who want a research-track chemistry degree for graduate study or industry.")),
    dict(slug="ucsb-chemistry-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Chemistry",
         department="Department of Chemistry and Biochemistry", cip="40.0501", duration_months=48,
         keywords=["chemistry"],
         description=(
             "The B.A. in chemistry pairs the core of chemical science with greater flexibility "
             "for double majors and pre-professional paths, suiting students who want chemistry "
             "within a broader liberal-arts program."),
         who_its_for=(
             "Students who want a strong chemistry foundation with room for a broader course of "
             "study or pre-health preparation.")),
    dict(slug="ucsb-biochemistry-bs", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Science in Biochemistry",
         department="Department of Chemistry and Biochemistry", cip="26.0202", duration_months=48,
         keywords=["biochemistry"],
         description=(
             "Biochemistry studies the chemistry of living systems — proteins, nucleic acids, "
             "metabolism, and molecular structure — combining organic and physical chemistry with "
             "molecular biology and extensive laboratory work."),
         who_its_for=(
             "Students bound for graduate or medical study who want molecular-level training at "
             "the chemistry–biology interface.")),
    dict(slug="ucsb-biological-sciences-bs", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Science in Biological Sciences",
         department="Departments of EEMB and MCDB (joint)", cip="26.0101", duration_months=48,
         keywords=["biological sciences", "biology"],
         description=(
             "The B.S. in biological sciences gives a comprehensive, laboratory-based foundation "
             "spanning molecular and cell biology, genetics, physiology, and ecology and "
             "evolution, jointly administered by UCSB's two biology departments."),
         who_its_for=(
             "Students seeking a broad, research-ready biology foundation for graduate study, "
             "health professions, or biotechnology.")),
    dict(slug="ucsb-biological-sciences-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Biological Sciences",
         department="Departments of EEMB and MCDB (joint)", cip="26.0101", duration_months=48,
         keywords=["biological sciences", "biology"],
         description=(
             "The B.A. in biological sciences covers the same biological core with added "
             "flexibility, suiting students combining biology with teaching, policy, or another "
             "field rather than a laboratory-research track."),
         who_its_for=(
             "Students who want a biology foundation within a broader program, including future "
             "teachers and pre-health students.")),
    dict(slug="ucsb-molecular-cellular-developmental-biology-bs", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Science in Molecular, Cellular, and Developmental Biology",
         department="Department of Molecular, Cellular, and Developmental Biology", cip="26.0406",
         duration_months=48, keywords=["molecular biology", "cell biology", "developmental biology"],
         tracks=["Microbiology", "Pharmacology"],
         description=(
             "Molecular, cellular, and developmental biology examines how cells and molecules "
             "govern life — gene expression, signaling, immunity, development, and disease — with "
             "laboratory training and emphases available in microbiology and pharmacology."),
         who_its_for=(
             "Students preparing for graduate research or the health professions who want "
             "molecular-, cellular-, and developmental-level training.")),
    dict(slug="ucsb-aquatic-biology-bs", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Science in Aquatic Biology",
         department="Department of Ecology, Evolution, and Marine Biology", cip="26.1302",
         duration_months=48, keywords=["aquatic biology", "marine biology"],
         description=(
             "Aquatic biology studies the organisms and ecosystems of oceans, lakes, and streams, "
             "drawing on UCSB's coastal setting and marine field sites for hands-on study of "
             "marine and freshwater life."),
         who_its_for=(
             "Students drawn to marine and freshwater life who want field- and lab-based training "
             "on the coast.")),
    dict(slug="ucsb-physiology-bs", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Science in Physiology",
         department="Department of Ecology, Evolution, and Marine Biology", cip="26.0901",
         duration_months=48, keywords=["physiology"],
         description=(
             "Physiology studies how animal bodies function — from cells and organs to whole "
             "organisms — integrating anatomy, cell biology, and systems physiology with "
             "laboratory work, a common path toward the health professions."),
         who_its_for=(
             "Students interested in how bodies work, especially those preparing for medicine and "
             "the health professions.")),
    dict(slug="ucsb-earth-science-bs", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Science in Earth Science",
         department="Department of Earth Science", cip="40.0601", duration_months=48,
         keywords=["earth science", "geology"],
         tracks=["Geology", "Geophysics", "Climate and Environment", "Geobiology and Paleobiology"],
         description=(
             "The B.S. in earth science studies the solid earth, oceans, and climate through "
             "field, laboratory, and quantitative methods, with emphases spanning geology, "
             "geophysics, climate and environment, and geobiology and paleobiology."),
         who_its_for=(
             "Students who want a quantitative, field-based science of the earth and climate.")),
    dict(slug="ucsb-earth-science-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Earth Science",
         department="Department of Earth Science", cip="40.0601", duration_months=48,
         keywords=["earth science"],
         description=(
             "The B.A. in earth science surveys the processes shaping the planet — from plate "
             "tectonics to surface and climate systems — with more flexibility than the B.S. for "
             "students combining earth science with policy, education, or another field."),
         who_its_for=(
             "Students who want a broad earth-science foundation within a flexible liberal-arts "
             "program.")),
    dict(slug="ucsb-geography-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Geography",
         department="Department of Geography", cip="45.0701", duration_months=48,
         keywords=["geography"],
         tracks=["Geographic Information Science (GIScience)"],
         description=(
             "Geography studies the human and physical processes that shape places and "
             "environments, from cities and migration to landscapes and climate, with a "
             "geographic-information-science track for spatial analysis and mapping."),
         who_its_for=(
             "Students interested in places, environments, and spatial data across the human and "
             "physical sciences.")),
    dict(slug="ucsb-physical-geography-bs", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Science in Physical Geography",
         department="Department of Geography", cip="45.0702", duration_months=48,
         keywords=["physical geography"],
         tracks=["Ocean Science"],
         description=(
             "Physical geography studies the earth's surface systems — climate, water, "
             "landforms, and ecosystems — with quantitative and remote-sensing methods and an "
             "ocean-science emphasis for coastal and marine environments."),
         who_its_for=(
             "Students who want a quantitative science of climate, water, and the earth's "
             "surface.")),
    dict(slug="ucsb-mathematics-bs", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Science in Mathematics",
         department="Department of Mathematics", cip="27.0101", duration_months=48,
         keywords=["mathematics"],
         description=(
             "The B.S. in mathematics gives a rigorous, proof-based course through analysis, "
             "algebra, and geometry with depth toward graduate study, emphasizing the structure "
             "and logic of modern mathematics."),
         who_its_for=(
             "Students who love rigorous, proof-based mathematics and may pursue graduate study.")),
    dict(slug="ucsb-mathematics-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Mathematics",
         department="Department of Mathematics", cip="27.0101", duration_months=48,
         keywords=["mathematics"],
         description=(
             "The B.A. in mathematics covers the mathematical core with more flexibility for "
             "double majors, teaching, and applied paths, suiting students who want mathematics "
             "within a broader program."),
         who_its_for=(
             "Students who want a strong mathematics foundation alongside another field or "
             "teaching.")),
    dict(slug="ucsb-applied-mathematics-bs", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Science in Applied Mathematics",
         department="Department of Mathematics", cip="27.0301", duration_months=48,
         keywords=["applied mathematics"],
         description=(
             "Applied mathematics uses analysis, differential equations, and computation to model "
             "problems in science and engineering, pairing mathematical rigor with modeling and "
             "numerical methods."),
         who_its_for=(
             "Students who want to use advanced mathematics to model real problems in science, "
             "engineering, and industry.")),
    dict(slug="ucsb-actuarial-science-bs", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Science in Actuarial Science",
         department="Department of Mathematics", cip="27.0601", duration_months=48,
         keywords=["actuarial science"],
         description=(
             "Actuarial science applies probability, statistics, and financial mathematics to "
             "measure and price risk, preparing students for the actuarial examinations and "
             "careers in insurance, pensions, and finance."),
         who_its_for=(
             "Quantitatively strong students who want to price and manage risk in insurance and "
             "finance.")),
    dict(slug="ucsb-financial-mathematics-statistics-bs", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Science in Financial Mathematics and Statistics",
         department="Departments of Mathematics and Statistics & Applied Probability (joint)",
         cip="27.0305", duration_months=48, keywords=["financial mathematics", "statistics"],
         description=(
             "Financial mathematics and statistics combines probability, statistics, and "
             "mathematical finance with economics to model markets, derivatives, and risk, jointly "
             "offered by mathematics and statistics."),
         who_its_for=(
             "Students aiming for quantitative finance, data, and risk careers who want a "
             "math-and-statistics foundation.")),
    dict(slug="ucsb-statistics-data-science-bs", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Science in Statistics and Data Science",
         department="Department of Statistics and Applied Probability", cip="27.0501",
         duration_months=48, keywords=["statistics", "data science"],
         description=(
             "Statistics and data science teaches statistical theory, probability, and "
             "computation for drawing inferences from data, spanning modeling, machine learning, "
             "and data analysis with substantial programming."),
         who_its_for=(
             "Students who want to turn data into insight across science, industry, and research.")),
    dict(slug="ucsb-statistics-data-science-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Statistics and Data Science",
         department="Department of Statistics and Applied Probability", cip="27.0501",
         duration_months=48, keywords=["statistics", "data science"],
         description=(
             "The B.A. in statistics and data science covers statistical reasoning, probability, "
             "and data analysis with more room to combine data skills with a second field such as "
             "economics, biology, or the social sciences."),
         who_its_for=(
             "Students who want data-analysis skills paired with a substantive application "
             "field.")),
    dict(slug="ucsb-physics-bs", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Science in Physics",
         department="Department of Physics", cip="40.0801", duration_months=48,
         keywords=["physics"],
         description=(
             "The B.S. in physics gives a rigorous foundation in classical and quantum physics "
             "with laboratory and computational training, drawing on a department internationally "
             "known for theoretical and experimental physics."),
         who_its_for=(
             "Students who want a deep, research-oriented physics education for graduate study.")),
    dict(slug="ucsb-physics-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Physics",
         department="Department of Physics", cip="40.0801", duration_months=48,
         keywords=["physics"],
         description=(
             "The B.A. in physics covers the physical core with added flexibility for double "
             "majors, teaching, and interdisciplinary paths, suiting students who want physics "
             "within a broader course of study."),
         who_its_for=(
             "Students who want strong physics training alongside another field or teaching.")),
    dict(slug="ucsb-psychological-brain-sciences-bs", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Science in Psychological and Brain Sciences",
         department="Department of Psychological and Brain Sciences", cip="42.2701",
         duration_months=48, keywords=["psychology", "brain sciences"],
         description=(
             "Psychological and brain sciences studies mind and behavior through cognitive, "
             "developmental, social, and neuroscience approaches, with a research-oriented, "
             "quantitatively grounded curriculum."),
         who_its_for=(
             "Students who want a rigorous, science-based study of mind, brain, and behavior.")),
    dict(slug="ucsb-biopsychology-bs", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Science in Biopsychology",
         department="Department of Psychological and Brain Sciences", cip="42.2706",
         duration_months=48, keywords=["biopsychology", "neuroscience"],
         description=(
             "Biopsychology studies the biological bases of behavior — the brain, hormones, and "
             "nervous system — bridging neuroscience and psychology with laboratory training."),
         who_its_for=(
             "Students fascinated by the brain and behavior who want a neuroscience-leaning "
             "psychology degree.")),
    dict(slug="ucsb-hydrologic-sciences-policy-bs", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Science in Hydrologic Sciences and Policy",
         department="Department of Earth Science", cip="03.0205", duration_months=48,
         keywords=["hydrology", "water", "policy"],
         description=(
             "Hydrologic sciences and policy studies the movement, quality, and management of "
             "water, combining hydrology, earth science, and environmental chemistry with the "
             "policy that governs water resources."),
         who_its_for=(
             "Students who want to understand and manage water resources at the interface of "
             "science and policy.")),

    # ── College of Letters & Science: interdisciplinary & environment ──
    dict(slug="ucsb-environmental-studies-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Environmental Studies",
         department="Environmental Studies Program", cip="03.0103", duration_months=48,
         keywords=["environmental studies"],
         description=(
             "Environmental studies is an interdisciplinary major spanning ecology, policy, "
             "economics, and the humanities to understand environmental problems and their "
             "solutions; the B.A. emphasizes the social, political, and humanistic dimensions."),
         who_its_for=(
             "Students who want to address environmental challenges through policy, economics, and "
             "the social sciences.")),
    dict(slug="ucsb-environmental-studies-bs", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Science in Environmental Studies",
         department="Environmental Studies Program", cip="03.0104", duration_months=48,
         keywords=["environmental studies", "environmental science"],
         description=(
             "The B.S. in environmental studies grounds the interdisciplinary field in the natural "
             "sciences — ecology, chemistry, and earth systems — for students who want a "
             "science-intensive path to environmental problem-solving."),
         who_its_for=(
             "Students who want a science-heavy environmental degree spanning ecology, chemistry, "
             "and earth systems.")),
    dict(slug="ucsb-global-studies-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Global Studies",
         department="Global Studies Program", cip="30.2001", duration_months=48,
         keywords=["global studies"],
         description=(
             "Global studies examines globalization across economics, politics, culture, and the "
             "environment, combining the social sciences and humanities with regional expertise "
             "and language study."),
         who_its_for=(
             "Students interested in global affairs, development, and cross-cultural work across "
             "disciplines.")),

    # ── College of Letters & Science: social sciences ──
    dict(slug="ucsb-anthropology-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Anthropology",
         department="Department of Anthropology", cip="45.0201", duration_months=48,
         keywords=["anthropology"], tracks=["Cultural", "Biological", "Archaeology"],
         description=(
             "Anthropology studies humanity across time and cultures through its cultural, "
             "biological, and archaeological subfields, examining how people live, evolve, and "
             "make meaning."),
         who_its_for=(
             "Students curious about human cultures, evolution, and the material past across "
             "societies.")),
    dict(slug="ucsb-sociology-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Sociology",
         department="Department of Sociology", cip="45.1101", duration_months=48,
         keywords=["sociology"],
         description=(
             "Sociology studies how societies, institutions, and group life shape human behavior, "
             "examining inequality, culture, and social change with theory and empirical methods."),
         who_its_for=(
             "Students who want to understand social structures, inequality, and change.")),
    dict(slug="ucsb-political-science-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Political Science",
         department="Department of Political Science", cip="45.1001", duration_months=48,
         keywords=["political science"],
         description=(
             "Political science studies government, power, and political behavior across American "
             "politics, comparative politics, international relations, and political theory, with "
             "quantitative and analytical methods."),
         who_its_for=(
             "Students interested in politics, government, and international affairs, including "
             "future law and public-service careers.")),
    dict(slug="ucsb-economics-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Economics",
         department="Department of Economics", cip="45.0601", duration_months=48,
         keywords=["economics"],
         description=(
             "Economics analyzes how people, firms, and governments allocate scarce resources, "
             "combining micro- and macroeconomic theory with statistics and empirical analysis of "
             "markets and policy."),
         who_its_for=(
             "Students who want analytical training for careers in business, policy, data, or "
             "graduate study.")),
    dict(slug="ucsb-economics-accounting-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Economics and Accounting",
         department="Department of Economics", cip="52.0301", duration_months=48,
         keywords=["economics", "accounting"],
         description=(
             "Economics and accounting pairs economic analysis with financial and managerial "
             "accounting, preparing students for the CPA path, corporate finance, and "
             "professional accounting careers."),
         who_its_for=(
             "Students aiming for accounting, finance, and business careers who want economics "
             "plus accounting training.")),
    dict(slug="ucsb-communication-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Communication",
         department="Department of Communication", cip="09.0101", duration_months=48,
         keywords=["communication"],
         description=(
             "Communication studies how people create, exchange, and interpret messages across "
             "interpersonal, media, and digital contexts, grounded in social-science theory and "
             "empirical research."),
         who_its_for=(
             "Students interested in media, human interaction, and the science of communication.")),
    dict(slug="ucsb-linguistics-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Linguistics",
         department="Department of Linguistics", cip="16.0101", duration_months=48,
         keywords=["linguistics"],
         tracks=["English", "Chinese", "Japanese", "French", "German", "Slavic", "Spanish",
                 "Speech-Language Sciences and Disorders", "Language and Speech Technologies"],
         description=(
             "Linguistics studies the structure, sound, meaning, and use of human language, from "
             "phonetics and syntax to language and cognition, with emphases spanning specific "
             "languages, speech sciences, and language technology."),
         who_its_for=(
             "Students fascinated by how language works, including paths into speech science and "
             "language technology.")),
    dict(slug="ucsb-language-culture-society-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Language, Culture, and Society",
         department="Department of Linguistics", cip="16.0102", duration_months=48,
         keywords=["language", "culture", "society"],
         description=(
             "Language, culture, and society examines how language shapes social life, identity, "
             "and power, combining linguistics with anthropology and sociology to study language "
             "in its cultural context."),
         who_its_for=(
             "Students interested in language as a social and cultural phenomenon rather than a "
             "formal system alone.")),
    dict(slug="ucsb-feminist-studies-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Feminist Studies",
         department="Department of Feminist Studies", cip="05.0207", duration_months=48,
         keywords=["feminist studies", "gender studies"],
         description=(
             "Feminist studies analyzes gender and sexuality as they intersect with race, class, "
             "and power across cultures and history, drawing on the humanities and social "
             "sciences."),
         who_its_for=(
             "Students who want to study gender, sexuality, and social justice across "
             "disciplines.")),
    dict(slug="ucsb-black-studies-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Black Studies",
         department="Department of Black Studies", cip="05.0201", duration_months=48,
         keywords=["black studies", "african american studies"],
         description=(
             "Black studies examines the histories, cultures, politics, and expressive traditions "
             "of Black people in Africa and the diaspora, combining the humanities and social "
             "sciences."),
         who_its_for=(
             "Students who want to study the Black experience, culture, and politics across the "
             "diaspora.")),
    dict(slug="ucsb-asian-american-studies-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Asian American Studies",
         department="Department of Asian American Studies", cip="05.0202", duration_months=48,
         keywords=["asian american studies"],
         description=(
             "Asian American studies examines the histories, communities, and cultural production "
             "of Asian Americans and Pacific Islanders, with attention to migration, race, and "
             "identity in the United States."),
         who_its_for=(
             "Students interested in Asian American history, communities, and cultural "
             "politics.")),
    dict(slug="ucsb-chicana-chicano-studies-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Chicana and Chicano Studies",
         department="Department of Chicana and Chicano Studies", cip="05.0203", duration_months=48,
         keywords=["chicana and chicano studies", "latino studies"],
         description=(
             "Chicana and Chicano studies examines the history, culture, politics, and social "
             "experience of Chicanas/os and Latinas/os, combining the humanities and social "
             "sciences with community engagement."),
         who_its_for=(
             "Students who want to study Chicana/o and Latina/o history, culture, and social "
             "justice.")),
    dict(slug="ucsb-religious-studies-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Religious Studies",
         department="Department of Religious Studies", cip="38.0201", duration_months=48,
         keywords=["religious studies"],
         description=(
             "Religious studies examines the world's religious traditions, texts, and practices "
             "across history and cultures, using humanistic and social-scientific methods rather "
             "than advocating any faith."),
         who_its_for=(
             "Students curious about religion's role in history, culture, and society across "
             "traditions.")),
    dict(slug="ucsb-middle-east-studies-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Middle East Studies",
         department="Department of Religious Studies", cip="05.0114", duration_months=48,
         keywords=["middle east studies"],
         description=(
             "Middle East studies is an interdisciplinary major spanning the languages, "
             "histories, religions, and politics of the Middle East, combining area expertise "
             "with language study."),
         who_its_for=(
             "Students interested in the languages, cultures, and politics of the Middle East.")),
    dict(slug="ucsb-latin-american-iberian-studies-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Latin American and Iberian Studies",
         department="Latin American and Iberian Studies Program", cip="05.0107", duration_months=48,
         keywords=["latin american studies", "iberian studies"],
         description=(
             "Latin American and Iberian studies is an interdisciplinary major on the histories, "
             "cultures, politics, and languages of Latin America, Spain, and Portugal, integrating "
             "the humanities and social sciences with language study."),
         who_its_for=(
             "Students interested in Latin America and the Iberian world across disciplines and "
             "languages.")),

    # ── College of Letters & Science: languages & literatures ──
    dict(slug="ucsb-classics-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Classics",
         department="Department of Classics", cip="16.1200", duration_months=48,
         keywords=["classics", "greek", "latin"],
         tracks=["Classical Language and Literature", "Greek and Roman Culture"],
         description=(
             "Classics studies the languages, literature, history, and archaeology of ancient "
             "Greece and Rome, with tracks in classical languages and literature and in Greek and "
             "Roman culture."),
         who_its_for=(
             "Students drawn to the ancient Mediterranean world, its languages, texts, and "
             "material culture.")),
    dict(slug="ucsb-comparative-literature-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Comparative Literature",
         department="Comparative Literature Program", cip="16.0104", duration_months=48,
         keywords=["comparative literature"],
         description=(
             "Comparative literature studies literature across languages, cultures, and media, "
             "reading works in translation and the original alongside literary theory and "
             "interdisciplinary approaches."),
         who_its_for=(
             "Students who love literature across languages and want to read it comparatively and "
             "theoretically.")),
    dict(slug="ucsb-chinese-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Chinese",
         department="Department of East Asian Languages and Cultural Studies", cip="16.0301",
         duration_months=48, keywords=["chinese"],
         description=(
             "Chinese develops advanced proficiency in Mandarin while studying classical and "
             "modern Chinese literature, film, and history."),
         who_its_for=(
             "Students who want fluency in Chinese and deep engagement with Chinese literature "
             "and history.")),
    dict(slug="ucsb-japanese-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Japanese",
         department="Department of East Asian Languages and Cultural Studies", cip="16.0302",
         duration_months=48, keywords=["japanese"],
         description=(
             "Japanese builds advanced language proficiency alongside the study of Japanese "
             "literature, visual and popular culture, and history from the premodern era to the "
             "present."),
         who_its_for=(
             "Students who want fluency in Japanese and deep engagement with Japanese literature "
             "and culture.")),
    dict(slug="ucsb-asian-studies-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Asian Studies",
         department="Department of East Asian Languages and Cultural Studies", cip="05.0103",
         duration_months=48, keywords=["asian studies"],
         description=(
             "Asian studies is an interdisciplinary major on the languages, histories, religions, "
             "and cultures of East and broader Asia, combining area expertise with language "
             "study."),
         who_its_for=(
             "Students interested in Asia across disciplines who want language plus cultural and "
             "historical depth.")),
    dict(slug="ucsb-french-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in French",
         department="Department of French and Italian", cip="16.0901", duration_months=48,
         keywords=["french"],
         description=(
             "The French major builds advanced proficiency in French alongside the study of "
             "French and Francophone literature, film, and culture."),
         who_its_for=(
             "Students who want fluency in French and engagement with the Francophone world.")),
    dict(slug="ucsb-italian-studies-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Italian Studies",
         department="Department of French and Italian", cip="16.0902", duration_months=48,
         keywords=["italian studies"],
         description=(
             "Italian studies develops proficiency in Italian alongside the study of Italian "
             "literature, cinema, art, and culture from the medieval period to the present."),
         who_its_for=(
             "Students drawn to Italian language, literature, and culture.")),
    dict(slug="ucsb-german-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in German",
         department="Department of Germanic and Slavic Studies", cip="16.0501", duration_months=48,
         keywords=["german"],
         description=(
             "The German major builds advanced proficiency in German alongside the study of "
             "German literature, philosophy, film, and culture."),
         who_its_for=(
             "Students who want fluency in German and engagement with German-language culture and "
             "thought.")),
    dict(slug="ucsb-russian-east-european-studies-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Russian and East European Studies",
         department="Department of Germanic and Slavic Studies", cip="05.0110", duration_months=48,
         keywords=["russian", "east european studies"],
         description=(
             "Russian and East European studies combines Russian and Slavic language study with "
             "the literature, history, and politics of Russia and Eastern Europe."),
         who_its_for=(
             "Students interested in Russia and Eastern Europe, their languages, cultures, and "
             "politics.")),
    dict(slug="ucsb-spanish-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Spanish",
         department="Department of Spanish and Portuguese", cip="16.0905", duration_months=48,
         keywords=["spanish"],
         description=(
             "The Spanish major develops advanced proficiency in Spanish alongside the study of "
             "Spanish, Latin American, and U.S. Latina/o literature and culture."),
         who_its_for=(
             "Students who want fluency in Spanish and engagement with the Hispanic world.")),
    dict(slug="ucsb-portuguese-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Portuguese",
         department="Department of Spanish and Portuguese", cip="16.0904", duration_months=48,
         keywords=["portuguese"],
         description=(
             "The Portuguese major builds proficiency in Portuguese alongside the study of "
             "Brazilian and Lusophone literature and culture."),
         who_its_for=(
             "Students interested in Portuguese and the Lusophone world, especially Brazil.")),

    # ── College of Letters & Science: humanities & fine arts ──
    dict(slug="ucsb-english-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in English",
         department="Department of English", cip="23.0101", duration_months=48,
         keywords=["english", "literature"],
         description=(
             "English studies literature in English across periods and genres — poetry, fiction, "
             "drama, and film — with training in close reading, critical theory, and writing."),
         who_its_for=(
             "Students who love literature and want strong reading, writing, and analytical "
             "skills.")),
    dict(slug="ucsb-history-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in History",
         department="Department of History", cip="54.0101", duration_months=48,
         keywords=["history"],
         description=(
             "History studies the human past across regions and eras, teaching students to "
             "interpret primary sources, construct evidence-based arguments, and understand "
             "change over time."),
         who_its_for=(
             "Students who want to understand the past and build research and argumentation "
             "skills.")),
    dict(slug="ucsb-history-policy-law-governance-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in History of Policy, Law, and Governance",
         department="Department of History", cip="54.0102", duration_months=48,
         keywords=["history", "policy", "law", "governance"],
         description=(
             "History of policy, law, and governance studies how institutions, law, and public "
             "policy have developed over time, giving a historical foundation for careers in law, "
             "government, and public affairs."),
         who_its_for=(
             "Students interested in law, policy, and government who want a historical "
             "grounding.")),
    dict(slug="ucsb-philosophy-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Philosophy",
         department="Department of Philosophy", cip="38.0101", duration_months=48,
         keywords=["philosophy"],
         description=(
             "Philosophy examines fundamental questions of knowledge, reality, ethics, and logic, "
             "training students in rigorous argument and clear reasoning across the analytic "
             "tradition."),
         who_its_for=(
             "Students who enjoy rigorous argument about knowledge, ethics, and reality.")),
    dict(slug="ucsb-history-art-architecture-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in History of Art and Architecture",
         department="Department of History of Art and Architecture", cip="50.0703",
         duration_months=48, keywords=["art history", "architecture"],
         description=(
             "History of art and architecture studies visual art, buildings, and material culture "
             "across periods and world traditions, teaching visual analysis and the history of "
             "objects and the built environment."),
         who_its_for=(
             "Students drawn to art, architecture, and visual culture and their histories.")),
    dict(slug="ucsb-art-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Art",
         department="Department of Art", cip="50.0701", duration_months=48,
         keywords=["art", "studio art"],
         description=(
             "The art major develops studio practice across media — painting, sculpture, "
             "photography, and new media — alongside critique and the history and theory of "
             "contemporary art."),
         who_its_for=(
             "Students who want to develop a contemporary studio-art practice within a research "
             "university.")),
    dict(slug="ucsb-film-media-studies-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Film and Media Studies",
         department="Department of Film and Media Studies", cip="50.0601", duration_months=48,
         keywords=["film", "media studies"],
         description=(
             "Film and media studies analyzes cinema, television, and digital media — their "
             "history, theory, and industry — with some production, treating moving-image media "
             "as art and social force."),
         who_its_for=(
             "Students who want to study and critically analyze film and media, with some "
             "production.")),
    dict(slug="ucsb-theater-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Theater",
         department="Department of Theater and Dance", cip="50.0501", duration_months=48,
         keywords=["theater"],
         description=(
             "The theater major combines performance, directing, design, and dramatic literature "
             "with hands-on production, training students as theater artists and scholars."),
         who_its_for=(
             "Students who want to make and study theater across performance and production.")),
    dict(slug="ucsb-dance-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Dance",
         department="Department of Theater and Dance", cip="50.0301", duration_months=48,
         keywords=["dance"],
         description=(
             "The dance major integrates technique, choreography, performance, and dance studies, "
             "developing dancers and dance-makers within a liberal-arts context."),
         who_its_for=(
             "Students who want to train as dancers and choreographers while studying dance.")),
    dict(slug="ucsb-music-studies-ba", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Arts in Music Studies",
         department="Department of Music", cip="50.0901", duration_months=48,
         keywords=["music", "music studies"],
         description=(
             "Music studies offers a liberal-arts path through music history, theory, and "
             "musicianship for students who want to study music broadly rather than pursue "
             "conservatory-style performance."),
         who_its_for=(
             "Students who want to study music within a broad liberal-arts program.")),
    dict(slug="ucsb-music-bm", school=_LS, degree_type="bachelors",
         program_name="Bachelor of Music",
         department="Department of Music", cip="50.0903", duration_months=48,
         keywords=["music", "performance"],
         description=(
             "The Bachelor of Music is a performance-intensive degree in instrumental or vocal "
             "performance, combining private study, ensembles, and recitals with music theory and "
             "history."),
         who_its_for=(
             "Students pursuing serious training as performing musicians.")),
]


def _grad(slug, school, name, dept, cip, keywords, description, who, degree_type="masters",
          tuition="academic", tracks=None):
    """Build a graduate program row. tuition: 'academic' → non-resident academic-graduate
    scalar; 'funded' → funded research doctorate (tuition=None); 'selfsupp' → omit-with-reason."""
    row = dict(slug=slug, school=school, degree_type=degree_type, program_name=name,
               department=dept, cip=cip, duration_months=(60 if degree_type == "phd" else 24),
               keywords=list(keywords), description=description, who_its_for=who)
    if tracks:
        row["tracks"] = list(tracks)
    if tuition == "funded":
        row["funded"] = True
    elif tuition == "selfsupp":
        row["omit_tuition_reason"] = _SELF_SUPP_NOTE
    else:  # academic
        row["tuition"] = _GRAD_TUITION_NONRES
    return row


# ============================ ACADEMIC GRADUATE (MA / MS / PhD) ============================
_GRAD = [
    # ── Sciences (College of Letters & Science) ──
    _grad("ucsb-chemistry-ms", _LS, "Master of Science in Chemistry",
          "Department of Chemistry and Biochemistry", "40.0501", ["chemistry"],
          "The M.S. in chemistry deepens laboratory research and advanced coursework in a "
          "chemical specialization, typically as a step toward doctoral work or industry research.",
          "Students seeking advanced chemical training and research experience beyond the "
          "bachelor's."),
    _grad("ucsb-chemistry-phd", _LS, "Doctor of Philosophy in Chemistry",
          "Department of Chemistry and Biochemistry", "40.0501", ["chemistry"],
          "The Ph.D. in chemistry centers on original research across organic, inorganic, "
          "physical, and biological chemistry, culminating in a dissertation.",
          "Aspiring research chemists pursuing academic or industry research careers.",
          degree_type="phd", tuition="funded"),
    _grad("ucsb-physics-ma", _LS, "Master of Arts in Physics", "Department of Physics",
          "40.0801", ["physics"],
          "The M.A. in physics provides advanced coursework in classical, quantum, and "
          "statistical physics, often en route to doctoral research.",
          "Students strengthening their physics foundation before doctoral study.",
          tracks=["Astrophysics"]),
    _grad("ucsb-physics-phd", _LS, "Doctor of Philosophy in Physics", "Department of Physics",
          "40.0801", ["physics"],
          "The Ph.D. in physics centers on original theoretical or experimental research, drawing "
          "on a department internationally known for its work and the Kavli Institute for "
          "Theoretical Physics.",
          "Aspiring physicists pursuing research in academia or national laboratories.",
          degree_type="phd", tuition="funded", tracks=["Astrophysics"]),
    _grad("ucsb-mathematics-ma", _LS, "Master of Arts in Mathematics",
          "Department of Mathematics", "27.0101", ["mathematics"],
          "The M.A. in mathematics offers advanced graduate coursework in pure and applied "
          "mathematics, often as preparation for doctoral study or teaching.",
          "Students deepening their mathematics before a Ph.D. or a teaching career."),
    _grad("ucsb-applied-mathematics-ma", _LS, "Master of Arts in Applied Mathematics",
          "Department of Mathematics", "27.0301", ["applied mathematics"],
          "The M.A. in applied mathematics develops advanced modeling, analysis, and "
          "computational methods for problems in science and engineering.",
          "Students who want advanced applied-mathematics training for research or industry."),
    _grad("ucsb-mathematics-phd", _LS, "Doctor of Philosophy in Mathematics",
          "Department of Mathematics", "27.0101", ["mathematics"],
          "The Ph.D. in mathematics centers on original research in pure or applied mathematics, "
          "culminating in a dissertation.",
          "Aspiring research mathematicians pursuing academic careers.",
          degree_type="phd", tuition="funded"),
    _grad("ucsb-statistics-ma", _LS, "Master of Arts in Statistics",
          "Department of Statistics and Applied Probability", "27.0501", ["statistics"],
          "The M.A. in statistics develops advanced statistical theory and data-analysis methods, "
          "with a data-science emphasis available.",
          "Students seeking advanced statistical training for data-science and analytics "
          "careers."),
    _grad("ucsb-statistics-applied-probability-phd", _LS,
          "Doctor of Philosophy in Statistics and Applied Probability",
          "Department of Statistics and Applied Probability", "27.0501", ["statistics",
          "probability"],
          "The Ph.D. in statistics and applied probability centers on original research in "
          "statistical theory, probability, and their applications, including a financial "
          "mathematics and statistics emphasis.",
          "Aspiring research statisticians and probabilists pursuing academic or industry "
          "research.", degree_type="phd", tuition="funded"),
    _grad("ucsb-actuarial-science-ms", _LS, "Master of Science in Actuarial Science",
          "Department of Statistics and Applied Probability", "27.0601", ["actuarial science"],
          "The M.S. in actuarial science provides advanced training in probability, statistics, "
          "and financial mathematics for the actuarial profession.",
          "Students preparing for advanced actuarial careers and examinations."),
    _grad("ucsb-eemb-ma", _LS, "Master of Arts in Ecology, Evolution, and Marine Biology",
          "Department of Ecology, Evolution, and Marine Biology", "26.1301", ["ecology",
          "evolution", "marine biology"],
          "The M.A. in ecology, evolution, and marine biology supports advanced study and "
          "research in organismal, population, and ecosystem biology.",
          "Students advancing toward research or doctoral study in ecology and evolution."),
    _grad("ucsb-eemb-ms", _LS, "Master of Science in Ecology, Evolution, and Marine Biology",
          "Department of Ecology, Evolution, and Marine Biology", "26.1301", ["ecology",
          "evolution", "marine biology"],
          "The M.S. in ecology, evolution, and marine biology centers on field- and lab-based "
          "research in ecological and evolutionary science, drawing on UCSB's coastal setting.",
          "Students pursuing research training in ecology, evolution, and marine biology."),
    _grad("ucsb-eemb-phd", _LS, "Doctor of Philosophy in Ecology, Evolution, and Marine Biology",
          "Department of Ecology, Evolution, and Marine Biology", "26.1301", ["ecology",
          "evolution", "marine biology"],
          "The Ph.D. in ecology, evolution, and marine biology centers on original research from "
          "molecules to ecosystems, with strengths in marine and coastal science.",
          "Aspiring research ecologists and evolutionary and marine biologists.",
          degree_type="phd", tuition="funded"),
    _grad("ucsb-mcdb-ms", _LS,
          "Master of Science in Molecular, Cellular, and Developmental Biology",
          "Department of Molecular, Cellular, and Developmental Biology", "26.0406",
          ["molecular biology", "cell biology"],
          "The M.S. in molecular, cellular, and developmental biology supports advanced "
          "laboratory research on the molecular mechanisms of cells and development.",
          "Students building research experience in molecular and cellular biology."),
    _grad("ucsb-mcdb-phd", _LS,
          "Doctor of Philosophy in Molecular, Cellular, and Developmental Biology",
          "Department of Molecular, Cellular, and Developmental Biology", "26.0406",
          ["molecular biology", "cell biology"],
          "The Ph.D. in molecular, cellular, and developmental biology centers on original "
          "research into gene regulation, cell function, and development.",
          "Aspiring research biologists in molecular, cellular, and developmental biology.",
          degree_type="phd", tuition="funded"),
    _grad("ucsb-biochemistry-molecular-biology-ms", _LS,
          "Master of Science in Biochemistry and Molecular Biology",
          "Interdisciplinary Program in Quantitative Biosciences", "26.0202", ["biochemistry",
          "molecular biology"],
          "The M.S. in biochemistry and molecular biology supports interdisciplinary research at "
          "the interface of chemistry and biology through the Quantitative Biosciences program.",
          "Students pursuing research at the chemistry–biology interface."),
    _grad("ucsb-biochemistry-molecular-biology-phd", _LS,
          "Doctor of Philosophy in Biochemistry and Molecular Biology",
          "Interdisciplinary Program in Quantitative Biosciences", "26.0202", ["biochemistry",
          "molecular biology"],
          "The Ph.D. in biochemistry and molecular biology centers on interdisciplinary research "
          "on biological molecules and mechanisms through the Quantitative Biosciences program.",
          "Aspiring researchers in biochemistry and quantitative biosciences.",
          degree_type="phd", tuition="funded"),
    _grad("ucsb-earth-science-ms", _LS, "Master of Science in Earth Science",
          "Department of Earth Science", "40.0601", ["earth science", "geology"],
          "The M.S. in earth science supports graduate research in a chosen specialization, "
          "pairing advanced coursework with a thesis project supervised by faculty.",
          "Students pursuing research training in the earth and climate sciences."),
    _grad("ucsb-earth-science-phd", _LS, "Doctor of Philosophy in Earth Science",
          "Department of Earth Science", "40.0601", ["earth science", "geology"],
          "The Ph.D. in earth science centers on original research across geology, geophysics, "
          "climate, and geobiology.",
          "Aspiring research earth and climate scientists.", degree_type="phd", tuition="funded"),
    _grad("ucsb-geography-ma", _LS, "Master of Arts in Geography", "Department of Geography",
          "45.0701", ["geography"],
          "The M.A. in geography supports advanced study of human and physical geography and "
          "geographic information science.",
          "Students advancing in geographic research and spatial analysis."),
    _grad("ucsb-geography-phd", _LS, "Doctor of Philosophy in Geography",
          "Department of Geography", "45.0701", ["geography"],
          "The Ph.D. in geography centers on original research in human geography, physical "
          "geography, or geographic information science.",
          "Aspiring geographers and spatial scientists pursuing research careers.",
          degree_type="phd", tuition="funded"),
    _grad("ucsb-marine-science-ms", _LS, "Master of Science in Marine Science",
          "Interdepartmental Graduate Program in Marine Science", "26.1302", ["marine science"],
          "The M.S. in marine science is an interdepartmental program supporting research on "
          "ocean and coastal systems, drawing on UCSB's Marine Science Institute.",
          "Students pursuing interdisciplinary research in ocean and coastal science."),
    _grad("ucsb-marine-science-phd", _LS, "Doctor of Philosophy in Marine Science",
          "Interdepartmental Graduate Program in Marine Science", "26.1302", ["marine science"],
          "The Ph.D. in marine science centers on interdisciplinary original research on marine "
          "and coastal systems across UCSB's ocean-science departments.",
          "Aspiring marine scientists pursuing research careers.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-dynamical-neuroscience-ma", _LS, "Master of Arts in Dynamical Neuroscience",
          "Dynamical Neuroscience Program", "26.1501", ["neuroscience"],
          "The M.A. in dynamical neuroscience supports interdisciplinary study of the brain using "
          "quantitative and computational approaches.",
          "Students building quantitative neuroscience research skills."),
    _grad("ucsb-dynamical-neuroscience-phd", _LS,
          "Doctor of Philosophy in Dynamical Neuroscience", "Dynamical Neuroscience Program",
          "26.1501", ["neuroscience"],
          "The Ph.D. in dynamical neuroscience centers on original research on brain systems using "
          "quantitative, computational, and experimental methods.",
          "Aspiring neuroscientists pursuing computational and systems research.",
          degree_type="phd", tuition="funded"),
    _grad("ucsb-psychological-brain-sciences-ma", _LS,
          "Master of Arts in Psychological and Brain Sciences",
          "Department of Psychological and Brain Sciences", "42.2701", ["psychology"],
          "The M.A. in psychological and brain sciences supports advanced coursework and research "
          "in cognitive, developmental, social, or neuroscience areas, typically en route to the "
          "doctorate.",
          "Students advancing toward doctoral research in psychology and neuroscience."),
    _grad("ucsb-psychological-brain-sciences-phd", _LS,
          "Doctor of Philosophy in Psychological and Brain Sciences",
          "Department of Psychological and Brain Sciences", "42.2701", ["psychology",
          "neuroscience"],
          "The Ph.D. in psychological and brain sciences centers on original research across "
          "cognition, development, social psychology, and neuroscience.",
          "Aspiring research psychologists and cognitive neuroscientists.", degree_type="phd",
          tuition="funded"),

    # ── Social sciences & humanities (College of Letters & Science) ──
    _grad("ucsb-anthropology-phd", _LS, "Doctor of Philosophy in Anthropology",
          "Department of Anthropology", "45.0201", ["anthropology"],
          "The Ph.D. in anthropology centers on original research across the archaeological, "
          "biological, and sociocultural subfields.",
          "Aspiring research anthropologists pursuing academic careers.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-sociology-phd", _LS, "Doctor of Philosophy in Sociology",
          "Department of Sociology", "45.1101", ["sociology"],
          "The Ph.D. in sociology centers on original research on social structures, inequality, "
          "and change, with theoretical and empirical training.",
          "Aspiring research sociologists pursuing academic careers.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-political-science-ma", _LS, "Master of Arts in Political Science",
          "Department of Political Science", "45.1001", ["political science"],
          "The M.A. in political science offers advanced study across the subfields of political "
          "science, often en route to the doctorate.",
          "Students advancing toward doctoral study or applied political analysis."),
    _grad("ucsb-political-science-phd", _LS, "Doctor of Philosophy in Political Science",
          "Department of Political Science", "45.1001", ["political science"],
          "The Ph.D. in political science centers on original research across American, "
          "comparative, international-relations, and theory subfields.",
          "Aspiring political scientists pursuing academic or policy-research careers.",
          degree_type="phd", tuition="funded"),
    _grad("ucsb-economics-phd", _LS, "Doctor of Philosophy in Economics",
          "Department of Economics", "45.0601", ["economics"],
          "The Ph.D. in economics centers on original research in economic theory and applied "
          "econometrics, training research economists.",
          "Aspiring research economists pursuing academic, policy, or industry research.",
          degree_type="phd", tuition="funded"),
    _grad("ucsb-communication-phd", _LS, "Doctor of Philosophy in Communication",
          "Department of Communication", "09.0101", ["communication"],
          "The Ph.D. in communication centers on original social-scientific research on human and "
          "mediated communication.",
          "Aspiring communication researchers pursuing academic careers.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-linguistics-ma", _LS, "Master of Arts in Linguistics",
          "Department of Linguistics", "16.0101", ["linguistics"],
          "The M.A. in linguistics offers advanced study of language structure, sound, and "
          "meaning, often en route to the doctorate.",
          "Students advancing toward doctoral research in linguistics."),
    _grad("ucsb-linguistics-phd", _LS, "Doctor of Philosophy in Linguistics",
          "Department of Linguistics", "16.0101", ["linguistics"],
          "The Ph.D. in linguistics centers on original research in the structure and use of "
          "language, with strengths in usage-based and interactional linguistics.",
          "Aspiring linguists pursuing academic and research careers.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-global-studies-ma", _LS, "Master of Arts in Global Studies",
          "Global Studies Program", "30.2001", ["global studies"],
          "The M.A. in global studies offers advanced interdisciplinary study of globalization "
          "across politics, economics, and culture.",
          "Students advancing toward global-affairs research or doctoral study."),
    _grad("ucsb-global-studies-phd", _LS, "Doctor of Philosophy in Global Studies",
          "Global Studies Program", "30.2001", ["global studies"],
          "The Ph.D. in global studies centers on original interdisciplinary research on "
          "transnational processes, governance, and culture.",
          "Aspiring researchers of globalization and transnational studies.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-feminist-studies-ma", _LS, "Master of Arts in Feminist Studies",
          "Department of Feminist Studies", "05.0207", ["feminist studies"],
          "The M.A. in feminist studies offers advanced interdisciplinary study of gender and "
          "sexuality, often en route to the doctorate.",
          "Students advancing toward doctoral research in gender and sexuality studies."),
    _grad("ucsb-feminist-studies-phd", _LS, "Doctor of Philosophy in Feminist Studies",
          "Department of Feminist Studies", "05.0207", ["feminist studies"],
          "The Ph.D. in feminist studies centers on original interdisciplinary research on "
          "gender, sexuality, and power across cultures and history.",
          "Aspiring researchers of gender, sexuality, and feminist theory.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-chicana-chicano-studies-phd", _LS,
          "Doctor of Philosophy in Chicana and Chicano Studies",
          "Department of Chicana and Chicano Studies", "05.0203", ["chicana and chicano studies"],
          "The Ph.D. in Chicana and Chicano studies centers on original interdisciplinary "
          "research on Chicana/o and Latina/o history, culture, and social experience.",
          "Aspiring researchers of Chicana/o and Latina/o studies.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-religious-studies-ma", _LS, "Master of Arts in Religious Studies",
          "Department of Religious Studies", "38.0201", ["religious studies"],
          "The M.A. in religious studies offers advanced study of religious traditions, texts, "
          "and theory across cultures.",
          "Students advancing toward doctoral study of religion."),
    _grad("ucsb-religious-studies-phd", _LS, "Doctor of Philosophy in Religious Studies",
          "Department of Religious Studies", "38.0201", ["religious studies"],
          "The Ph.D. in religious studies centers on original research on religious traditions, "
          "texts, and theory across cultures and history.",
          "Aspiring scholars of religion pursuing academic careers.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-classics-phd", _LS, "Doctor of Philosophy in Classics",
          "Department of Classics", "16.1200", ["classics"],
          "The Ph.D. in classics centers on original research in ancient Greek and Latin "
          "language, literature, and history.",
          "Aspiring classicists pursuing academic careers.", degree_type="phd", tuition="funded"),
    _grad("ucsb-comparative-literature-phd", _LS,
          "Doctor of Philosophy in Comparative Literature", "Comparative Literature Program",
          "16.0104", ["comparative literature"],
          "The Ph.D. in comparative literature centers on original research on literature across "
          "languages, cultures, and media, and hosts graduate study in French, Italian, and "
          "Slavic literatures.",
          "Aspiring literary scholars working across languages and traditions.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-east-asian-languages-cultural-studies-ma", _LS,
          "Master of Arts in East Asian Languages and Cultural Studies",
          "Department of East Asian Languages and Cultural Studies", "16.0300", ["east asian",
          "chinese", "japanese"],
          "The M.A. in East Asian languages and cultural studies offers advanced study of "
          "Chinese and Japanese language, literature, and culture.",
          "Students advancing in East Asian language and cultural studies."),
    _grad("ucsb-east-asian-languages-cultural-studies-phd", _LS,
          "Doctor of Philosophy in East Asian Languages and Cultural Studies",
          "Department of East Asian Languages and Cultural Studies", "16.0300", ["east asian"],
          "The Ph.D. in East Asian languages and cultural studies centers on original research on "
          "the literatures and cultures of China and Japan.",
          "Aspiring scholars of East Asian literatures and cultures.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-german-ma", _LS, "Master of Arts in German",
          "Department of Germanic and Slavic Studies", "16.0501", ["german"],
          "The M.A. in German offers advanced study of German literature, thought, and culture, "
          "often en route to the doctorate.",
          "Students advancing toward doctoral study in German literary studies."),
    _grad("ucsb-german-phd", _LS, "Doctor of Philosophy in German",
          "Department of Germanic and Slavic Studies", "16.0501", ["german"],
          "The Ph.D. in German centers on original research in German literary and cultural "
          "studies, in cooperation with comparative literature.",
          "Aspiring scholars of German literature and thought.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-french-ma", _LS, "Master of Arts in French",
          "Department of French and Italian", "16.0901", ["french"],
          "The M.A. in French offers advanced study of French and Francophone literature and "
          "culture.",
          "Students advancing in French literary and cultural study."),
    _grad("ucsb-spanish-ma", _LS, "Master of Arts in Spanish",
          "Department of Spanish and Portuguese", "16.0905", ["spanish"],
          "The M.A. in Spanish offers advanced study of Hispanic literatures and linguistics, "
          "often within the doctoral track.",
          "Students advancing in Hispanic literary and linguistic study."),
    _grad("ucsb-hispanic-languages-literatures-phd", _LS,
          "Doctor of Philosophy in Hispanic Languages and Literatures",
          "Department of Spanish and Portuguese", "16.0905", ["spanish", "portuguese"],
          "The Ph.D. in Hispanic languages and literatures centers on original research in "
          "Spanish, Latin American, and Luso-Brazilian literatures and Iberian linguistics.",
          "Aspiring scholars of Hispanic and Luso-Brazilian literatures and linguistics.",
          degree_type="phd", tuition="funded"),
    _grad("ucsb-classics-ma", _LS, "Master of Arts in Classics", "Department of Classics",
          "16.1200", ["classics"],
          "The M.A. in classics offers advanced study of ancient Greek and Latin language, "
          "literature, and culture.",
          "Students deepening their classical training toward doctoral or teaching careers."),
    _grad("ucsb-comparative-literature-ma", _LS, "Master of Arts in Comparative Literature",
          "Comparative Literature Program", "16.0104", ["comparative literature"],
          "The M.A. in comparative literature offers advanced cross-cultural literary study and "
          "theory.",
          "Students advancing in comparative literary study."),
    _grad("ucsb-latin-american-iberian-studies-ma", _LS,
          "Master of Arts in Latin American and Iberian Studies",
          "Latin American and Iberian Studies Program", "05.0107", ["latin american studies"],
          "The M.A. in Latin American and Iberian studies is an interdisciplinary program on the "
          "histories, cultures, and politics of Latin America and the Iberian Peninsula.",
          "Students seeking interdisciplinary regional expertise in Latin America and Iberia."),
    _grad("ucsb-english-ma", _LS, "Master of Arts in English", "Department of English",
          "23.0101", ["english", "literature"],
          "The M.A. in English offers advanced literary study and criticism, typically within the "
          "doctoral track.",
          "Students advancing toward doctoral study in literature."),
    _grad("ucsb-english-phd", _LS, "Doctor of Philosophy in English", "Department of English",
          "23.0101", ["english", "literature"],
          "The Ph.D. in English centers on original research in literature and criticism across "
          "periods and fields.",
          "Aspiring literary scholars pursuing academic careers.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-history-ma", _LS, "Master of Arts in History", "Department of History",
          "54.0101", ["history"],
          "The M.A. in history offers advanced training in historical research and "
          "interpretation, typically within the doctoral track.",
          "Students advancing toward doctoral historical research."),
    _grad("ucsb-history-phd", _LS, "Doctor of Philosophy in History", "Department of History",
          "54.0101", ["history"],
          "The Ph.D. in history centers on original archival research and the writing of a "
          "dissertation across fields and regions.",
          "Aspiring historians pursuing academic and research careers.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-philosophy-ma", _LS, "Master of Arts in Philosophy",
          "Department of Philosophy", "38.0101", ["philosophy"],
          "The M.A. in philosophy offers advanced study across the analytic tradition, often en "
          "route to the doctorate.",
          "Students advancing toward doctoral study in philosophy."),
    _grad("ucsb-philosophy-phd", _LS, "Doctor of Philosophy in Philosophy",
          "Department of Philosophy", "38.0101", ["philosophy"],
          "The Ph.D. in philosophy centers on original research across metaphysics, epistemology, "
          "ethics, and logic in the analytic tradition.",
          "Aspiring philosophers pursuing academic careers.", degree_type="phd", tuition="funded"),
    _grad("ucsb-film-media-studies-ma", _LS, "Master of Arts in Film and Media Studies",
          "Department of Film and Media Studies", "50.0601", ["film", "media studies"],
          "The M.A. in film and media studies offers advanced study of the history and theory of "
          "cinema and media, typically within the doctoral track.",
          "Students advancing toward doctoral study of film and media."),
    _grad("ucsb-film-media-studies-phd", _LS, "Doctor of Philosophy in Film and Media Studies",
          "Department of Film and Media Studies", "50.0601", ["film", "media studies"],
          "The Ph.D. in film and media studies centers on original research on the history, "
          "theory, and culture of moving-image and digital media.",
          "Aspiring film and media scholars pursuing academic careers.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-history-art-architecture-ma", _LS,
          "Master of Arts in History of Art and Architecture",
          "Department of History of Art and Architecture", "50.0703", ["art history"],
          "The M.A. in history of art and architecture offers advanced study of art, "
          "architecture, and visual culture across world traditions, within the doctoral track.",
          "Students advancing toward doctoral study in art and architectural history."),
    _grad("ucsb-history-art-architecture-phd", _LS,
          "Doctor of Philosophy in History of Art and Architecture",
          "Department of History of Art and Architecture", "50.0703", ["art history"],
          "The Ph.D. in history of art and architecture centers on original research on visual "
          "art, architecture, and material culture across periods and traditions.",
          "Aspiring art and architectural historians pursuing academic and curatorial careers.",
          degree_type="phd", tuition="funded"),
    _grad("ucsb-music-ma", _LS, "Master of Arts in Music", "Department of Music", "50.0901",
          ["music", "musicology"],
          "The M.A. in music offers advanced study in musicology, theory, or composition within "
          "the department's graduate program.",
          "Students advancing in musical scholarship and composition."),
    _grad("ucsb-music-phd", _LS, "Doctor of Philosophy in Music", "Department of Music",
          "50.0901", ["music", "musicology"],
          "The Ph.D. in music centers on original research in musicology, music theory, or "
          "composition.",
          "Aspiring music scholars and composer-researchers pursuing academic careers.",
          degree_type="phd", tuition="funded"),

    # ── Engineering (academic MS / PhD) ──
    _grad("ucsb-chemical-engineering-ms", _ENGR, "Master of Science in Chemical Engineering",
          "Department of Chemical Engineering", "14.0701", ["chemical engineering"],
          "The M.S. in chemical engineering deepens advanced coursework and research in reaction "
          "engineering, transport, and materials.",
          "Engineers seeking advanced technical depth or a step toward doctoral research."),
    _grad("ucsb-chemical-engineering-phd", _ENGR,
          "Doctor of Philosophy in Chemical Engineering", "Department of Chemical Engineering",
          "14.0701", ["chemical engineering"],
          "The Ph.D. in chemical engineering centers on original research in areas from soft "
          "materials and catalysis to biomolecular engineering.",
          "Aspiring research chemical engineers pursuing academic or industry research.",
          degree_type="phd", tuition="funded"),
    _grad("ucsb-computer-science-ms", _ENGR, "Master of Science in Computer Science",
          "Department of Computer Science", "11.0701", ["computer science"],
          "The M.S. in computer science offers advanced coursework and research across systems, "
          "theory, and artificial intelligence.",
          "Computing professionals and researchers seeking advanced CS depth."),
    _grad("ucsb-computer-science-phd", _ENGR, "Doctor of Philosophy in Computer Science",
          "Department of Computer Science", "11.0701", ["computer science"],
          "The Ph.D. in computer science centers on original research across AI, systems, "
          "security, theory, and human-centered computing.",
          "Aspiring computer scientists pursuing research careers.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-electrical-computer-engineering-ms", _ENGR,
          "Master of Science in Electrical and Computer Engineering",
          "Department of Electrical and Computer Engineering", "14.1001", ["electrical engineering",
          "computer engineering"],
          "The M.S. in electrical and computer engineering deepens research in areas from "
          "photonics and communications to computer engineering.",
          "Engineers seeking advanced depth in electrical and computer engineering."),
    _grad("ucsb-electrical-computer-engineering-phd", _ENGR,
          "Doctor of Philosophy in Electrical and Computer Engineering",
          "Department of Electrical and Computer Engineering", "14.1001", ["electrical engineering"],
          "The Ph.D. in electrical and computer engineering centers on original research, with "
          "internationally recognized strength in optoelectronics and high-speed devices.",
          "Aspiring research electrical and computer engineers.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-mechanical-engineering-ms", _ENGR, "Master of Science in Mechanical Engineering",
          "Department of Mechanical Engineering", "14.1901", ["mechanical engineering"],
          "The M.S. in mechanical engineering deepens research in dynamics and control, fluids, "
          "solid mechanics, and thermal sciences.",
          "Engineers seeking advanced mechanical-engineering depth."),
    _grad("ucsb-mechanical-engineering-phd", _ENGR,
          "Doctor of Philosophy in Mechanical Engineering",
          "Department of Mechanical Engineering", "14.1901", ["mechanical engineering"],
          "The Ph.D. in mechanical engineering centers on original research across dynamics, "
          "controls, fluids, robotics, and micro-systems.",
          "Aspiring research mechanical engineers.", degree_type="phd", tuition="funded"),
    _grad("ucsb-materials-ms", _ENGR, "Master of Science in Materials",
          "Department of Materials", "14.1801", ["materials", "materials science"],
          "The M.S. in materials offers advanced coursework and research in the structure, "
          "properties, and processing of materials within a top-ranked program.",
          "Engineers and scientists seeking advanced materials training."),
    _grad("ucsb-materials-phd", _ENGR, "Doctor of Philosophy in Materials",
          "Department of Materials", "14.1801", ["materials", "materials science"],
          "The Ph.D. in materials centers on original research in electronic, structural, and "
          "soft materials, in a program consistently ranked among the best in the nation.",
          "Aspiring materials researchers pursuing academic or industry research.",
          degree_type="phd", tuition="funded"),
    _grad("ucsb-biological-engineering-phd", _ENGR,
          "Doctor of Philosophy in Biological Engineering", "Department of Bioengineering",
          "14.0501", ["bioengineering", "biological engineering"],
          "The Ph.D. in biological engineering centers on original research at the interface of "
          "engineering and biology, from synthetic biology to biomaterials.",
          "Aspiring researchers engineering biological systems.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-media-arts-technology-ms", _ENGR, "Master of Science in Media Arts and Technology",
          "Media Arts and Technology Program", "50.0102", ["media arts", "technology"],
          "The M.S. in media arts and technology is an interdisciplinary program bridging "
          "engineering, computing, and the arts in areas such as sound, visual media, and "
          "interactive systems.",
          "Artists and technologists building research skills at the art–engineering interface."),
    _grad("ucsb-media-arts-technology-phd", _ENGR,
          "Doctor of Philosophy in Media Arts and Technology",
          "Media Arts and Technology Program", "50.0102", ["media arts", "technology"],
          "The Ph.D. in media arts and technology centers on original interdisciplinary research "
          "across engineering, computing, and the media arts.",
          "Aspiring researchers at the intersection of technology and the arts.", degree_type="phd",
          tuition="funded"),

    # ── Education (Gevirtz Graduate School of Education) ──
    _grad("ucsb-education-ma", _GGSE, "Master of Arts in Education", "Department of Education",
          "13.0101", ["education"],
          "The M.A. in education supports advanced study of learning, teaching, and educational "
          "policy across emphases in the Department of Education.",
          "Educators and researchers advancing their study of education."),
    _grad("ucsb-education-phd", _GGSE, "Doctor of Philosophy in Education",
          "Department of Education", "13.0101", ["education"],
          "The Ph.D. in education centers on original research on learning, teaching, and policy "
          "across the department's emphases.",
          "Aspiring education researchers pursuing academic and policy careers.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-counseling-clinical-school-psychology-phd", _GGSE,
          "Doctor of Philosophy in Counseling, Clinical, and School Psychology",
          "Department of Counseling, Clinical, and School Psychology", "42.2803", ["psychology",
          "counseling"],
          "The Ph.D. in counseling, clinical, and school psychology centers on original research "
          "and clinical training in psychological science and practice.",
          "Aspiring psychologists pursuing research and applied practice.", degree_type="phd",
          tuition="funded"),
]

# ============================ PROFESSIONAL / SELF-SUPPORTING ============================
_PROF = [
    _grad("ucsb-environmental-science-management-mesm", _BREN,
          "Master of Environmental Science and Management",
          "Bren School of Environmental Science & Management", "03.0201", ["environmental science",
          "environmental management"],
          "The professional Master of Environmental Science and Management (MESM) trains "
          "environmental problem-solvers through interdisciplinary coursework, specializations, "
          "and a client-based group project.",
          "Early-career professionals preparing to lead environmental science and management "
          "work.", tuition="selfsupp"),
    _grad("ucsb-environmental-data-science-meds", _BREN,
          "Master of Environmental Data Science",
          "Bren School of Environmental Science & Management", "30.7001", ["environmental data "
          "science", "data science"],
          "The professional Master of Environmental Data Science (MEDS) is an accelerated program "
          "combining data science, programming, and environmental science for data-driven "
          "environmental work.",
          "Professionals building data-science skills for environmental careers.",
          tuition="selfsupp"),
    _grad("ucsb-environmental-science-management-phd", _BREN,
          "Doctor of Philosophy in Environmental Science and Management",
          "Bren School of Environmental Science & Management", "03.0101", ["environmental science"],
          "The Ph.D. in environmental science and management centers on original "
          "interdisciplinary research on environmental problems and their solutions.",
          "Aspiring researchers of environmental science, policy, and management.",
          degree_type="phd", tuition="funded"),
    _grad("ucsb-technology-management-mtm", _ENGR, "Master of Technology Management",
          "Technology Management Program", "52.0201", ["technology management"],
          "Technology management pairs engineering and science backgrounds with coursework in "
          "management, entrepreneurship, finance, and innovation to prepare technical "
          "professionals to lead and launch technology ventures.",
          "Technical professionals moving into management and entrepreneurship.",
          tuition="selfsupp"),
    _grad("ucsb-art-mfa", _LS, "Master of Fine Arts in Art", "Department of Art", "50.0701",
          ["art", "studio art"],
          "The M.F.A. in art is a studio-intensive terminal degree developing a mature "
          "independent art practice through critique, exhibition, and the history and theory of "
          "contemporary art.",
          "Practicing artists pursuing the terminal studio degree.", tuition="academic"),
    _grad("ucsb-music-mm", _LS, "Master of Music", "Department of Music", "50.0903",
          ["music", "performance"],
          "The Master of Music is a performance-focused graduate degree combining advanced "
          "private study, ensembles, and recitals with graduate musicianship.",
          "Musicians pursuing advanced performance training.", tuition="academic"),
    _grad("ucsb-music-dma", _LS, "Doctor of Musical Arts", "Department of Music", "50.0903",
          ["music", "performance"],
          "The Doctor of Musical Arts is a performance-centered doctorate combining advanced "
          "performance and scholarship for professional musicians.",
          "Advanced performers pursuing the highest performance degree.", degree_type="phd",
          tuition="funded"),
    _grad("ucsb-school-psychology-med", _GGSE, "Master of Education in School Psychology",
          "Department of Counseling, Clinical, and School Psychology", "42.2805", ["school "
          "psychology", "education"],
          "The M.Ed. in school psychology trains practitioners to support students' learning, "
          "behavior, and mental health in schools, toward the pupil-personnel-services "
          "credential.",
          "Students preparing to become credentialed school psychologists.", tuition="academic"),
    _grad("ucsb-teaching-med", _GGSE, "Master of Education in Teaching",
          "Teacher Education Program", "13.1206", ["teaching", "teacher education"],
          "The Teacher Education Program combines a California teaching credential with the M.Ed., "
          "preparing candidates to teach in elementary and secondary schools.",
          "Aspiring teachers earning a California credential with a master's.", tuition="academic"),
]



# ── Verified Wikimedia Commons campus gallery (author + license from the Commons extmetadata
# API; every URL resolves — recognizable outdoor campus scenes, no logos/maps/interiors). ──
_CAMPUS_PHOTOS: list[dict] = [
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/9/96/UCSB_Lagoon_%284547142266%29.jpg",
        "credit": "Wikimedia Commons / Dhilung Kirat (CC BY 2.0)",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/UCSB_Cliffs.jpg/1920px-UCSB_Cliffs.jpg",
        "credit": "Wikimedia Commons / Doopokko (CC BY-SA 2.0)",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/View_of_UCSB_courtyard.jpg/1920px-View_of_UCSB_courtyard.jpg",
        "credit": "Wikimedia Commons / Carsten Keßler (CC BY 2.0)",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/d/da/Empty_Campus_%284758256749%29.jpg",
        "credit": "Wikimedia Commons / Damian Gadal (CC BY 2.0)",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/UCSB-ocean1.JPG/1920px-UCSB-ocean1.JPG",
        "credit": "Wikimedia Commons / Joyradost (CC BY-SA 4.0)",
    },
]

# external_reviews are deferred to a later depth pass (gathered, program-specific third-party
# coverage — never synthesized), so every program records external_reviews.summary in
# _standard.omitted. No fabricated review ships.
_REVIEWS_BY_SLUG: dict[str, dict] = {}

# ── Assemble + guard the catalog ───────────────────────────────────────────
_CATALOG: list[dict] = _UG + _GRAD + _PROF

_TRACKS_BY_SLUG: dict[str, dict] = {}
for _row in _CATALOG:
    if _row.get("tracks"):
        _TRACKS_BY_SLUG[_row["slug"]] = {
            "tracks": list(_row["tracks"]),
            "source": f"{_row['department']} — UCSB General Catalog",
            "source_url": "https://catalog.ucsb.edu/",
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
    raise RuntimeError(f"duplicate (program_name, degree_type) in UCSB catalog: {_dn}")

# ── Outcomes (institution-wide; UCSB publishes no per-program split) ──
_OUTCOMES_CONDITIONS = (
    "Institution-wide median earnings of federally aided students measured 10 years after "
    "entry (U.S. Dept. of Education College Scorecard); not a program-specific figure."
)
_OUTCOMES_INSTITUTION = {
    "median_salary": 74915,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry (institution-wide)",
    "conditions": _OUTCOMES_CONDITIONS,
    "source": "U.S. Dept. of Education College Scorecard (UCSB, UNITID 110705)",
    "source_url": "https://collegescorecard.ed.gov/school/?110705",
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
    "source": "https://admissions.ucsb.edu/",
}
_REQ_GRAD_GENERIC = {
    "materials": [
        "UCSB Graduate Division application",
        "Transcripts from all prior institutions",
        "Letters of recommendation",
        "Statement of purpose and personal achievements/contributions statement",
        "Standardized / English-proficiency scores where required by the program",
    ],
    "deadlines": {
        "note": "Deadlines vary by program; see the program's official admissions page.",
    },
    "source": "https://www.graddiv.ucsb.edu/admissions",
}


def _requirements_for(spec: dict) -> dict:
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


def _undergrad_cost() -> dict:
    return {
        "tuition_usd": _UG_TUITION_NONRES,
        "breakdown": {
            "tuition_in_state": _UG_TUITION_RES,
            "tuition_out_of_state": _UG_TUITION_NONRES,
        },
        "funded": False,
        "note": (
            "Published 2026-27 UC undergraduate tuition and fees. As a public university UCSB "
            f"charges California residents about ${_UG_TUITION_RES:,} and non-residents about "
            f"${_UG_TUITION_NONRES:,}; the non-resident rate is the matcher's budget input for a "
            "national and international applicant pool."
        ),
        "source": _UG_COST_SRC[0],
        "source_url": _UG_COST_SRC[1],
        "year": "2026-27",
    }


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


def apply(session: Session) -> bool:
    """Enrich UCSB to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when UCSB is absent — safe on fresh/CI databases.
    """
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    school_outcomes["campus_photos"] = [dict(p) for p in _CAMPUS_PHOTOS]
    school_outcomes["media_credit"] = _CAMPUS_PHOTOS[0]["credit"]
    school_outcomes["_standard"] = _standard(_OMITTED_INSTITUTION)
    inst.school_outcomes = school_outcomes
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    inst.founded_year = 1944
    inst.campus_setting = "suburban"
    if not inst.website_url:
        inst.website_url = "https://www.ucsb.edu"
    lead_photo = _CAMPUS_PHOTOS[0]["url"]
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
                "breakdown": {
                    "tuition_in_state": _GRAD_TUITION_RES,
                    "tuition_out_of_state": _GRAD_TUITION_NONRES,
                },
                "funded": False,
                "note": _grad_cost_note(),
                "source": _GRAD_COST_SRC[0],
                "source_url": _GRAD_COST_SRC[1],
                "year": "2025-26",
            }
        elif spec.get("funded"):
            p.tuition = None
            p.cost_data = {
                "funded": True,
                "note": _FUNDED_NOTE,
                "source": "UCSB Graduate Division — financial support",
                "source_url": "https://www.graddiv.ucsb.edu/financial",
            }
        else:
            p.tuition = None
            p.cost_data = {
                "funded": False,
                "note": spec.get("omit_tuition_reason", _SELF_SUPP_NOTE),
                "source": _SELF_SUPP_SRC[0],
                "source_url": _SELF_SUPP_SRC[1],
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
        p.application_deadline = date(2025, 12, 2) if spec["degree_type"] == "bachelors" else None
    session.flush()
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
