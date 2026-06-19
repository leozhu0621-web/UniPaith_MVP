"""Canonical University of Chicago profile — the single source of truth.

Real, sourced data only (U.S. Dept. of Education College Scorecard, UNITID 144050 ·
NCES College Navigator / IPEDS · the University of Chicago Office of Institutional
Analysis Common Data Set 2024-25 · UChicago News (FY24 endowment) · the official QS /
Times Higher Education / U.S. News rankings · UChicago Career Advancement post-college
outcomes · each school's official leadership / about page · the Chicago Booth Full-Time
MBA employment report and class profile · the College Scorecard Field-of-Study earnings
by CIP). ``apply(session)`` idempotently enriches the University of Chicago institution
row, upserts its real degree-granting schools, and builds UChicago's program catalog
across them.

UChicago's academic structure: the College (the undergraduate division, which confers
every bachelor's degree), the graduate Divisions (Physical Sciences, Social Sciences,
Humanities, Biological Sciences) and a set of dean-led professional schools. We model
the units that own the degree programs in the canonical College Scorecard Field-of-Study
list for UNITID 144050 onto the platform's ``School`` model:
  - The College (undergraduate A.B./B.S. majors)
  - The University of Chicago Booth School of Business (the MBA — the flagship)
  - Harris School of Public Policy (the MPP)
  - The University of Chicago Law School (the J.D.)
  - Pritzker School of Medicine (the M.D.)
  - Crown Family School of Social Work, Policy, and Practice (the A.M.)
  - University of Chicago Divinity School (the M.Div.)
  - Pritzker School of Molecular Engineering (the molecular-engineering degree)
  - Division of the Physical Sciences (the M.P.C.S. and M.S. in Statistics)
  - Division of the Social Sciences (CIR and MAPSS)
  - Division of the Humanities (MAPH)

It **flushes but does not commit** — the caller (the Alembic data migration, the CLI
script, or the dev seed) owns the transaction. It is a **no-op** (returns ``False``)
when UChicago is absent, so it is safe to run against a fresh or CI database. Re-running
is safe: schools key off ``(institution_id, name)`` and programs off ``slug``; stale
rows are reconciled without breaking foreign keys.

This mirrors ``mit_profile`` / ``yale_profile`` so the migration, the standalone script,
and the dev seed all agree (DRY). Every figure traces to a public, citable source;
anything that could not be verified from a first-party or two-independent-source basis
is **omitted** (recorded in the relevant ``_standard.omitted`` list), never guessed.
The Booth Full-Time MBA is the most-enriched flagship (its real concentrations,
employment-report outcomes, class profile, and aggregated reviews), mirroring MIT
Sloan's MBAn in the reference instance — with the honest caveats that UChicago is
permanently test-optional, that several professional/graduate tuitions are published
only on the JavaScript-rendered University Bursar pages (omitted rather than guessed),
that the undergraduate housing system wording could not be confirmed first-party
(omitted), and that the federal one-year Field-of-Study earnings for the M.D. reflect
residency stipends rather than attending-physician pay (captured in that program's
conditions).

Structural repair (2026-06-17, chicagoprof7): real UChicago degree names (Bachelor of
Arts/Science, Master of Arts/Science — never CIP-rollup credential prefixes), field-
specific descriptions that open on the field fact (never restating program_name), and
deduplicated IPEDS rows that mapped to the same published degree (103 programs; 0%
name-prefix descriptions; 0% CIP-prefix names).
"""

from __future__ import annotations

import re
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.chicago_field_descriptions import (
    FIELD_ALIASES,
    FIELD_DESCRIPTIONS,
    GRAD_FIELD_DESCRIPTIONS,
    SLUG_DESCRIPTIONS,
)
from unipaith.data.chicago_ipeds_catalog import _IPEDS_CATALOG
from unipaith.data.profile_catalog_utils import validate_catalog
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "University of Chicago"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-17"

_TEMPLATE_STUB_RE = re.compile(
    r" — a .+ (undergraduate|graduate|doctoral|certificate|professional|"
    r"master's|bachelor's|PhD|MBA|JD|MD|bachelors|masters|phd) program offered through ",
    re.I,
)
_CLASSIFICATION_STUB_RE = re.compile(
    r"^.+ is (an undergraduate|a graduate|a doctoral|a graduate certificate|"
    r"a professional|a degree) program at ",
)
_PREFIX_NAME_RE = re.compile(
    r"^(Bachelor's in|Master's in|Professional program in) "
)

_SLUG_TO_FIELD: dict[str, str] = {
    slug: field_name for slug, _, field_name, _, _, _, _, _ in _IPEDS_CATALOG
}


def _standard(omitted: list[str] | None = None) -> dict:
    """The per-node provenance stamp the routine writes onto every enriched node."""
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }


# Institution-level fields that could NOT be verified from a citable source and are
# therefore honestly omitted rather than guessed.
_OMITTED_INSTITUTION = [
    # UChicago is associated with many Nobel laureates, but it does not publish a single
    # canonical headline count on an official page and third-party aggregate counts vary
    # by counting method, so the figure is omitted rather than asserting a number.
    "school_outcomes.flagship.nobel_laureates",
    # The undergraduate residence-hall / House system specifics could not be confirmed
    # verbatim from a first-party housing page at author time, so housing is omitted.
    "school_outcomes.campus_life.housing",
]

# ── Institution-level data ────────────────────────────────────────────────
# Rankings are stored as {rank, year} objects (the page renders any ranking_data entry
# that is an object with a numeric `rank`). All three ranks are quoted from the official
# ranking bodies for the 2026 editions.
RANKING_DATA: dict = {
    "ownership_type": "private",
    # UChicago is accredited by the Higher Learning Commission (HLC).
    "accreditor": "HLC",
    # Carnegie basic classification (R1).
    "carnegie_classification": "Doctoral Universities: Very High Research Activity",
    # QS World University Rankings 2026: UChicago is ranked #13 worldwide.
    "qs_world_university_rankings": {"rank": 13, "year": 2026},
    # THE World University Rankings 2026: #15 in the world.
    "times_higher_education": {"rank": 15, "year": 2026},
    # U.S. News Best Colleges (National Universities) 2026: #6 nationally.
    "us_news_national": {"rank": 6, "year": 2026},
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below is
# complete, so a shallow merge is correct. Figures are College Scorecard (UNITID 144050)
# cross-checked against UChicago's Common Data Set 2024-25 and NCES College Navigator
# (IPEDS) where each publishes a metric.
SCHOOL_OUTCOMES: dict = {
    # CDS 2024-25 (item C1): 1,955 admits / 43,612 first-year applicants = 4.48%
    # (College Scorecard 0.0448).
    "admit_rate": 0.0448,
    # College Scorecard average annual net price.
    "avg_net_price": 14860,
    # College Scorecard institution-wide median earnings 10 years after entry.
    "median_earnings_10yr": 91885,
    # College Scorecard four-year completion rate (150% of normal time).
    "completion_rate_4yr_150pct": 0.9585,
    # CDS 2024-25 (item B22): first-year retention (Fall 2023 cohort) = 99.0%.
    "retention_rate_first_year": 0.99,
    # NCES College Navigator (IPEDS) six-year graduation rate (Fall 2018 cohort) = 96%;
    # the CDS reports 95.9% overall for the same cohort (they agree within rounding).
    "graduation_rate_6yr": 0.96,
    "financial_aid": {
        # College Scorecard: 15.26% of undergraduates received a Pell grant; 4.7% took
        # federal student loans. UChicago meets full need with no-loan (grant) aid.
        "pell_grant_rate": 0.1526,
        "federal_loan_rate": 0.047,
        # College Scorecard average annual cost of attendance.
        "cost_of_attendance": 90360,
        # College Scorecard median debt of completers.
        "median_debt_completers": 15000,
    },
    # Undergraduate race/ethnicity (College Scorecard, cross-checked vs UChicago CDS
    # 2024-25 item B2 / NCES College Navigator; the sources agree within rounding).
    "demographics": {
        "white": 0.295,
        "black": 0.0687,
        "hispanic": 0.1694,
        "asian": 0.1932,
        "two_or_more": 0.0696,
        "international": 0.1764,
    },
    # SAT/ACT 25th-75th percentiles of enrolled first-years (UChicago CDS 2024-25, item
    # C9; cross-checked against College Scorecard).
    "test_scores": {
        "sat_reading_25_75": [740, 780],
        "sat_math_25_75": [770, 800],
        "act_25_75": [34, 35],
    },
    # UChicago main campus, Hyde Park, Chicago, Illinois (College Scorecard location).
    "location": {"lat": 41.787994, "lng": -87.599539},
    "campus_basics": {"location": "Chicago, Illinois"},
    # Wikimedia Commons file page verified: Michael Barera, CC BY-SA 4.0 (Main Quadrangles).
    "media_credit": "Wikimedia Commons / Michael Barera (CC BY-SA 4.0)",
    "campus_photos": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/"
                "University_of_Chicago_July_2013_19_%28Main_Quadrangles%29.jpg/"
                "1920px-University_of_Chicago_July_2013_19_%28Main_Quadrangles%29.jpg"
            ),
            "credit": "Wikimedia Commons / Michael Barera (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/f/f3/"
                "A_Quad_at_the_University_of_Chicago.jpg"
            ),
            "credit": "Wikimedia Commons / Crimson3981 (Public domain)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/"
                "58_032179_University_of_Chicago_quad.jpg/"
                "1920px-58_032179_University_of_Chicago_quad.jpg"
            ),
            "credit": "Wikimedia Commons / Downtowngal (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/"
                "Cobb_Gate%2C_University_of_Chicago%2C_57th_Street%2C_Hyde_Park%2C_Chicago%2C_IL%3B_"
                "Nov._2023_%2854514978242%29.jpg/"
                "1920px-Cobb_Gate%2C_University_of_Chicago%2C_57th_Street%2C_Hyde_Park%2C_Chicago%2C_IL%3B_"
                "Nov._2023_%2854514978242%29.jpg"
            ),
            "credit": (
                "Wikimedia Commons / Warren LeMay from Chicago, IL, United States (CC BY-SA 2.0)"
            ),
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/"
                "University_of_Chicago_July_2013_32_%28Gordon_Center_for_Integrative_Science%29.jpg/"
                "1920px-University_of_Chicago_July_2013_32_%28Gordon_Center_for_Integrative_Science%29.jpg"
            ),
            "credit": "Wikimedia Commons / Michael Barera (CC BY-SA 4.0)",
        },
    ],
    "scale": {
        # CDS 2024-25 (item I-1): 2,007 total instructional faculty (1,759 full-time +
        # 248 part-time).
        "faculty_count": 2007,
        # CDS 2024-25 (item I-2): 5:1 student-faculty ratio.
        "student_faculty_ratio": "5:1",
        # UChicago News: combined endowment $10.4 billion at fiscal year-end June 30,
        # 2024 (FY2024, 8.4% return).
        "endowment_usd": 10400000000,
    },
    # UChicago Career Advancement post-college outcomes, Class of 2025: 98% of graduates
    # received a post-college offer (employment, graduate school, or other); among offer
    # recipients, 71% employment and 29% graduate/professional school.
    "employed_or_continuing_ed": 0.98,
    # UChicago Career Advancement, Class of 2025 — top employment industries among
    # employed graduates, in rank order; the five largest categories.
    "top_employer_industries": [
        "Financial services",
        "Science & technology",
        "Education",
        "Consulting",
        "Government, nonprofit & social services",
    ],
    "research": {
        "labs": [
            "Argonne National Laboratory (U.S. DOE national lab managed by UChicago)",
            "Fermi National Accelerator Laboratory (Fermilab)",
            "Marine Biological Laboratory (Woods Hole, Massachusetts)",
            "Giant Magellan Telescope (founding partner)",
            "South Pole Telescope (UChicago-led collaboration)",
        ],
        "areas": [
            "Physics, astronomy & cosmology",
            "Economics & the social sciences",
            "Molecular engineering & advanced materials",
            "Biological & biomedical sciences",
            "Mathematics, statistics & computer science",
            "Law, public policy & global affairs",
            "Humanities & the arts",
        ],
        "lab_links": {
            "Argonne National Laboratory (U.S. DOE national lab managed by UChicago)": (
                "https://www.anl.gov/"
            ),
            "Fermi National Accelerator Laboratory (Fermilab)": "https://www.fnal.gov/",
            "Marine Biological Laboratory (Woods Hole, Massachusetts)": "https://www.mbl.edu/",
        },
    },
    "campus_life": {
        # UChicago's teams (the Maroons) compete in NCAA Division III as a charter member
        # of the University Athletic Association (UAA).
        "athletics_division": "NCAA Division III (University Athletic Association)",
        "mascot": "Chicago Maroons (the Phoenix)",
        "resources": [
            {"label": "UChicago Athletics (the Maroons)", "url": "https://athletics.uchicago.edu/"},
        ],
    },
    "flagship": {
        # CDS 2024-25 (item B1): grand total 16,221 students.
        "enrollment_total": 16221,
        # CDS 2024-25 first-year admissions cycle (item C1).
        "applicants": 43612,
        "admits": 1955,
        "admissions_cycle": (
            "Entering class fall 2024 (University of Chicago Common Data Set 2024-25)"
        ),
        # Incorporated in 1890; classes began October 1, 1892.
        "founded_year": 1890,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (UChicago, UNITID 144050)",
            "url": "https://collegescorecard.ed.gov/school/?144050",
        },
        {
            "label": "NCES College Navigator — University of Chicago (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=144050",
        },
        {
            "label": (
                "University of Chicago — Common Data Set 2024-25 (Office of Institutional Analysis)"
            ),
            "url": "https://data.uchicago.edu/common-data-set/",
        },
        {
            "label": "University of Chicago endowment ended FY24 at $10.4 billion (UChicago News)",
            "url": "https://news.uchicago.edu/story/university-chicago-endowment-ended-fy24-104-billion",
        },
        {
            "label": "QS World University Rankings 2026 — University of Chicago",
            "url": "https://www.topuniversities.com/universities/university-chicago",
        },
        {
            "label": (
                "Times Higher Education World University Rankings 2026 — University of Chicago"
            ),
            "url": "https://www.timeshighereducation.com/world-university-rankings/university-chicago",
        },
        {
            "label": (
                "U.S. News Best Colleges 2026 — University of Chicago (#6 National Universities)"
            ),
            "url": "https://www.usnews.com/best-colleges/university-of-chicago-1774",
        },
        {
            "label": "University of Chicago — No Barriers financial aid (need-blind, no-loan)",
            "url": "https://collegeadmissions.uchicago.edu/affording/no-barriers",
        },
        {
            "label": "University of Chicago Career Advancement — post-college outcomes",
            "url": "https://careeradvancement.uchicago.edu/about-us/post-college-outcomes/",
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it "Undergraduates");
# the total (16,221) lives in flagship.enrollment_total and renders as "Total enrollment".
# 7,519 = UChicago CDS 2024-25 (item B1) total undergraduate enrollment.
UNDERGRAD_COUNT = 7519

DESCRIPTION = (
    "University of Chicago is a private research university in Chicago, IL, incorporated "
    "in 1890 with a gift from John D. Rockefeller and opening to students in 1892 in the "
    "Hyde Park neighborhood on the South Side. It enrolls about 7,500 undergraduates and "
    "roughly 8,700 graduate and professional students — some 16,200 in all — and is known "
    "for an intense intellectual culture, its undergraduate Core curriculum, and a 5:1 "
    "student-faculty ratio across a faculty of about 2,000.\n\n"
    "The College awards the bachelor's degree across the arts and sciences, and the "
    "university is organized into graduate Divisions — the Physical Sciences, Biological "
    "Sciences, Social Sciences and Humanities — and a set of renowned professional "
    "schools, among them the Booth School of Business, the Law School, the Pritzker "
    "School of Medicine, the Harris School of Public Policy, the Divinity School, the "
    "Crown Family School of Social Work, Policy, and Practice, and the Pritzker School of "
    "Molecular Engineering. UChicago's research reaches beyond Hyde Park: it manages "
    "Argonne National Laboratory and Fermilab for the U.S. Department of Energy and "
    "oversees the Marine Biological Laboratory at Woods Hole.\n\n"
    "The University of Chicago ranks among the very best universities in the world: No. 6 "
    "among national universities by U.S. News, No. 13 in the world by QS and No. 15 by "
    "Times Higher Education. It admits under 5% of first-year applicants and is permanently "
    "test-optional, reviewing the SAT or ACT only when a score helps an application.\n\n"
    "UChicago is need-blind for domestic applicants and meets 100% of demonstrated "
    "financial need with grants rather than loans through its No Barriers program: the "
    "average net price is about $14,900 a year, families earning under $125,000 pay no "
    "tuition, and only about 5% of undergraduates take federal student loans. Among the "
    "Class of 2025, 98% had secured a post-college outcome — most often employment or "
    "graduate study — within months of graduation."
)

# ── The real degree-granting schools (display order) ───────────────────────
_COLLEGE = "The College"
_BOOTH = "The University of Chicago Booth School of Business"
_HARRIS = "Harris School of Public Policy"
_LAW = "The University of Chicago Law School"
_PRITZKER_MED = "Pritzker School of Medicine"
_CROWN = "Crown Family School of Social Work, Policy, and Practice"
_DIVINITY = "University of Chicago Divinity School"
_PME = "Pritzker School of Molecular Engineering"
_PHYS_SCI = "Division of the Physical Sciences"
_SOC_SCI = "Division of the Social Sciences"
_HUMANITIES = "Division of the Humanities"

SCHOOLS: list[dict] = [
    {
        "name": _COLLEGE,
        "sort_order": 1,
        "description": (
            "The College, whose classes began in 1892, is the University of Chicago's "
            "undergraduate division and confers every bachelor's degree at the university. "
            "It is built around the Core — a broad common curriculum in the humanities, "
            "social sciences and physical sciences — and awards the A.B. and B.S. across "
            "roughly fifty majors taught by the faculty of the graduate Divisions."
        ),
    },
    {
        "name": _BOOTH,
        "sort_order": 2,
        "description": (
            "Founded in 1898, the University of Chicago Booth School of Business is one of "
            "the oldest and most highly ranked business schools in the world. It is known "
            "for a rigorous, discipline-based, evidence-driven approach and for the most "
            "flexible MBA curriculum among the top schools; its faculty include multiple "
            "Nobel laureates in economics."
        ),
    },
    {
        "name": _HARRIS,
        "sort_order": 3,
        "description": (
            "The Harris School of Public Policy, established in 1988, trains students to "
            "use rigorous data and economics to address public problems. It awards the "
            "Master of Public Policy and related degrees and is home to research centers "
            "including the Energy Policy Institute at the University of Chicago (EPIC) and "
            "the Pearson Institute."
        ),
    },
    {
        "name": _LAW,
        "sort_order": 4,
        "description": (
            "The University of Chicago Law School, which opened in 1902, is renowned for "
            "the influential 'law and economics' tradition and for an interdisciplinary, "
            "intellectually intense approach to legal education. It awards the J.D., the "
            "LL.M. and doctoral degrees in law."
        ),
    },
    {
        "name": _PRITZKER_MED,
        "sort_order": 5,
        "description": (
            "The Pritzker School of Medicine, which matriculated its first medical "
            "students in 1927 and was named for the Pritzker family in 1968, is the M.D.-"
            "granting school of the Biological Sciences Division. It is known for a small "
            "class size, an emphasis on research, and the affiliated University of Chicago "
            "Medicine academic health system."
        ),
    },
    {
        "name": _CROWN,
        "sort_order": 6,
        "description": (
            "The Crown Family School of Social Work, Policy, and Practice traces to the "
            "1908 Chicago School of Civics and Philanthropy and joined the university in "
            "1920 as the School of Social Service Administration, taking its current name "
            "in 2021. The oldest school of its kind, it awards the A.M. in social work, "
            "the Ph.D. and related degrees."
        ),
    },
    {
        "name": _DIVINITY,
        "sort_order": 7,
        "description": (
            "The University of Chicago Divinity School, with roots in an 1865 seminary "
            "charter, is a nonsectarian graduate school for the academic study of religion. "
            "It awards the Master of Divinity, the Master of Arts and the Ph.D. across the "
            "history, philosophy and practice of religious traditions."
        ),
    },
    {
        "name": _PME,
        "sort_order": 8,
        "description": (
            "The Pritzker School of Molecular Engineering, founded in 2011 as the Institute "
            "for Molecular Engineering and elevated to a school in 2019, is the University "
            "of Chicago's engineering school. It launched the nation's first undergraduate "
            "major in molecular engineering and anchors UChicago's work in quantum "
            "engineering, advanced materials and immunoengineering."
        ),
    },
    {
        "name": _PHYS_SCI,
        "sort_order": 9,
        "description": (
            "The Division of the Physical Sciences spans mathematics, statistics, computer "
            "science, physics, chemistry, astronomy and the geophysical sciences. Alongside "
            "its doctoral programs it offers professional master's degrees including the "
            "Master's Program in Computer Science and the M.S. in Statistics, and is home "
            "to the Enrico Fermi and James Franck Institutes."
        ),
    },
    {
        "name": _SOC_SCI,
        "sort_order": 10,
        "description": (
            "The Division of the Social Sciences is the home of the influential 'Chicago "
            "school' traditions in economics, sociology, political science and anthropology. "
            "It offers doctoral programs and professional master's degrees including the "
            "Committee on International Relations (CIR) and the Master of Arts Program in "
            "the Social Sciences (MAPSS)."
        ),
    },
    {
        "name": _HUMANITIES,
        "sort_order": 11,
        "description": (
            "The Division of the Humanities (now the Division of the Arts & Humanities) "
            "spans languages and literatures, philosophy, art history, music, cinema and "
            "the visual and performing arts. It offers doctoral programs and the Master of "
            "Arts Program in the Humanities (MAPH), and is home to the Franke Institute for "
            "the Humanities and the Neubauer Collegium."
        ),
    },
]

# Each school's official website (verified to resolve at author time).
_SCHOOL_WEBSITE: dict[str, str] = {
    _COLLEGE: "https://college.uchicago.edu/",
    _BOOTH: "https://www.chicagobooth.edu/",
    _HARRIS: "https://harris.uchicago.edu/",
    _LAW: "https://www.law.uchicago.edu/",
    _PRITZKER_MED: "https://pritzker.uchicago.edu/",
    _CROWN: "https://crownschool.uchicago.edu/",
    _DIVINITY: "https://divinity.uchicago.edu/",
    _PME: "https://pme.uchicago.edu/",
    _PHYS_SCI: "https://physicalsciences.uchicago.edu/",
    _SOC_SCI: "https://socialsciences.uchicago.edu/",
    _HUMANITIES: "https://humanities.uchicago.edu/",
}

# Rich, sourced About-tab content per school. Deans + titles are quoted from each
# school's official leadership page (verified 2026-06-10). Founding years come from each
# school's official history/about page. Notable-faculty rosters are not published
# uniformly per school and are omitted rather than hand-picked (recorded in
# _ABOUT_OMITTED). Founding years for the Physical Sciences, Social Sciences and
# Humanities divisions could not be confirmed from a first-party page and are omitted.
_ABOUT_DETAIL: dict[str, dict] = {
    _COLLEGE: {
        "founded": 1892,
        "leadership": (
            "Melina Hale — Dean of the College and William Rainey Harper Professor in "
            "Organismal Biology and Anatomy"
        ),
        "source": {
            "label": "The College — Message from the Dean",
            "url": "https://college.uchicago.edu/about/message-dean-college",
        },
    },
    _BOOTH: {
        "founded": 1898,
        "leadership": (
            "Madhav Rajan — Dean and George Shultz Professor of Accounting; Chief Global "
            "Strategist, University of Chicago"
        ),
        "research_centers": [
            "Becker Friedman Institute for Economics",
            "George J. Stigler Center for the Study of the Economy and the State",
            "Polsky Center for Entrepreneurship and Innovation",
        ],
        "source": {
            "label": "Chicago Booth — Deans and Administrators",
            "url": "https://www.chicagobooth.edu/about/deans-and-administrators",
        },
    },
    _HARRIS: {
        "founded": 1988,
        "leadership": ("Ethan Bueno de Mesquita — Dean and Sydney Stein Professor"),
        "research_centers": [
            "Energy Policy Institute at the University of Chicago (EPIC)",
            "The Pearson Institute for the Study and Resolution of Global Conflicts",
            "Center for the Economics of Human Development",
        ],
        "source": {
            "label": "Harris School of Public Policy — Meet Our Dean",
            "url": "https://harris.uchicago.edu/about/leadership/meet-our-dean",
        },
    },
    _LAW: {
        "founded": 1902,
        "leadership": (
            "Adam Chilton — Dean, Howard G. Krane Professor of Law and Walter Mander "
            "Research Scholar"
        ),
        "source": {
            "label": "The University of Chicago Law School — Meet the Dean",
            "url": "https://www.law.uchicago.edu/meet-dean",
        },
    },
    _PRITZKER_MED: {
        "founded": 1927,
        "leadership": (
            "Mark Anderson — Dean of the Biological Sciences Division and the Pritzker "
            "School of Medicine and Executive Vice President for Medical Affairs"
        ),
        "source": {
            "label": "Pritzker School of Medicine — About",
            "url": "https://pritzker.uchicago.edu/about",
        },
    },
    _CROWN: {
        "founded": 1908,
        "leadership": ("Deborah Gorman-Smith — Dean and Emily Klein Gidwitz Professor"),
        "source": {
            "label": "Crown Family School — Welcome from the Dean",
            "url": "https://crownschool.uchicago.edu/about/welcome-dean",
        },
    },
    _DIVINITY: {
        "founded": 1865,
        "leadership": (
            "James T. Robinson — Dean of the Divinity School and Nathan Cummings "
            "Professor of Jewish Studies"
        ),
        "source": {
            "label": "University of Chicago Divinity School — Message from the Dean",
            "url": "https://divinity.uchicago.edu/about/message-dean",
        },
    },
    _PME: {
        "founded": 2011,
        "leadership": ("Nadya Mason — Dean of the Pritzker School of Molecular Engineering"),
        "research_centers": [
            "Chicago Quantum Exchange",
        ],
        "source": {
            "label": "Pritzker School of Molecular Engineering — History",
            "url": "https://pme.uchicago.edu/about/history",
        },
    },
    _PHYS_SCI: {
        "leadership": (
            "Ka Yee C. Lee — Dean of the Division of the Physical Sciences and David Lee "
            "Shillinglaw Distinguished Service Professor in the Department of Chemistry"
        ),
        "research_centers": [
            "James Franck Institute",
            "Enrico Fermi Institute",
            "Kavli Institute for Cosmological Physics",
        ],
        "source": {
            "label": "Division of the Physical Sciences — Institutes & Centers",
            "url": "https://physicalsciences.uchicago.edu/research/institutes-centers/",
        },
    },
    _SOC_SCI: {
        "leadership": (
            "Amanda Woodward — Dean of the Division of the Social Sciences and William S. "
            "Gray Distinguished Service Professor of Psychology"
        ),
        "research_centers": [
            "Center for the Economics of Human Development",
            "Center for International Social Science Research (CISSR)",
            "Chicago Center for Computational Social Science",
        ],
        "source": {
            "label": "Division of the Social Sciences — Leadership",
            "url": "https://socialsciences.uchicago.edu/about/leadership",
        },
    },
    _HUMANITIES: {
        "leadership": (
            "Deborah L. Nelson — Dean of the Division and Helen B. and Frank L. Sulzberger "
            "Professor of English"
        ),
        "research_centers": [
            "Franke Institute for the Humanities",
            "Gray Center for Arts and Inquiry",
            "Neubauer Collegium for Culture and Society",
        ],
        "source": {
            "label": "Division of the Humanities — Divisional Leadership",
            "url": "https://humanities.uchicago.edu/about/divisional-leadership",
        },
    },
}

# About-detail fields omitted per school (verified-unavailable), recorded in each
# school's _standard.omitted. Notable-faculty rosters are omitted for every school. The
# College, Law, Pritzker Medicine, Crown and Divinity additionally omit a verified
# school-owned research-center list; the three Divisions omit a first-party founding year.
_FACULTY_OMIT = ["about_detail.faculty"]
_CENTERS_OMIT = "about_detail.research_centers"
_FOUNDED_OMIT = "about_detail.founded"
_ABOUT_OMITTED: dict[str, list[str]] = {
    _COLLEGE: [*_FACULTY_OMIT, _CENTERS_OMIT],
    _BOOTH: list(_FACULTY_OMIT),
    _HARRIS: list(_FACULTY_OMIT),
    _LAW: [*_FACULTY_OMIT, _CENTERS_OMIT],
    _PRITZKER_MED: [*_FACULTY_OMIT, _CENTERS_OMIT],
    _CROWN: [*_FACULTY_OMIT, _CENTERS_OMIT],
    _DIVINITY: [*_FACULTY_OMIT, _CENTERS_OMIT],
    _PME: list(_FACULTY_OMIT),
    _PHYS_SCI: [*_FACULTY_OMIT, _FOUNDED_OMIT],
    _SOC_SCI: [*_FACULTY_OMIT, _FOUNDED_OMIT],
    _HUMANITIES: [*_FACULTY_OMIT, _FOUNDED_OMIT],
}

# ── Channel feeds + official social links ──────────────────────────────────
# The daily content-ingest reads ``news_rss`` (RSS), ``events_feed`` (iCalendar), and
# ``keywords`` (filter gate). Without a real ``news_rss`` a node's Events & Updates tab
# is empty — so every school and program below carries a feed.
_UCHICAGO_NEWS_RSS = "http://feeds.feedburner.com/UChicago"
_UCHICAGO_EVENTS_ICS = {"url": "https://events.uchicago.edu/live/ical/events", "type": "ical"}
_SOCIAL_UCHICAGO = {
    "instagram": "https://www.instagram.com/uchicago/",
    "linkedin": "https://www.linkedin.com/school/university-of-chicago/",
    "x": "https://x.com/UChicago",
    "youtube": "https://www.youtube.com/user/uchicago",
    "facebook": "https://www.facebook.com/uchicago",
}

_INSTITUTION_CONTENT: dict = {
    "news_rss": _UCHICAGO_NEWS_RSS,
    "news_url": "https://news.uchicago.edu/",
    "news_curated": False,
    "events_feed": dict(_UCHICAGO_EVENTS_ICS),
    "social": dict(_SOCIAL_UCHICAGO),
}

_SCHOOL_FEED_SPEC: dict[str, dict] = {
    _COLLEGE: {"keywords": ["College", "undergraduate", "Core curriculum", "bachelor"]},
    _BOOTH: {"keywords": ["Booth", "business school", "MBA", "finance", "economics"]},
    _HARRIS: {"keywords": ["Harris", "public policy", "MPP", "policy"]},
    _LAW: {"keywords": ["Law School", "law", "legal", "JD"]},
    _PRITZKER_MED: {"keywords": ["Pritzker", "medicine", "medical school", "MD"]},
    _CROWN: {"keywords": ["Crown", "social work", "Crown Family School"]},
    _DIVINITY: {"keywords": ["Divinity", "religion", "ministry", "theology"]},
    _PME: {"keywords": ["molecular engineering", "PME", "quantum", "materials"]},
    _PHYS_SCI: {
        "keywords": [
            "Physical Sciences",
            "mathematics",
            "statistics",
            "computer science",
            "physics",
            "chemistry",
        ]
    },
    _SOC_SCI: {
        "keywords": ["Social Sciences", "economics", "sociology", "political science", "MAPSS"]
    },
    _HUMANITIES: {"keywords": ["Humanities", "literature", "philosophy", "MAPH", "arts"]},
}

_KW_STOP = {"and", "of", "the", "in", "for", "with", "science", "sciences", "engineering"}


def _school_content(name: str) -> dict:
    """A school's content_sources: UChicago News RSS + campus events filtered by keywords."""
    spec = _SCHOOL_FEED_SPEC[name]
    return {
        "news_rss": _UCHICAGO_NEWS_RSS,
        "news_url": _SCHOOL_WEBSITE.get(name, "https://www.uchicago.edu"),
        "news_curated": False,
        "events_feed": dict(_UCHICAGO_EVENTS_ICS),
        "keywords": list(spec["keywords"]),
        "social": dict(_SOCIAL_UCHICAGO),
    }


def _program_keywords(spec: dict) -> list[str]:
    school_kw = list(_SCHOOL_FEED_SPEC[spec["school"]]["keywords"])
    name = spec["program_name"].replace("&", " ").replace("/", " ")
    terms = [w for w in name.split() if len(w) > 3 and w.lower() not in _KW_STOP]
    program_term = " ".join(terms[:3]).strip()
    return ([program_term] if program_term else []) + school_kw


def _program_content(spec: dict) -> dict:
    base = _school_content(spec["school"])
    base["keywords"] = _program_keywords(spec)
    return base


# Booth MBA keyword-relevant feed (the flagship) — Booth news RSS + shared campus calendar.
_BOOTH_CONTENT: dict = {
    "news_rss": "http://feeds.chicagobooth.edu/boothnews",
    "news_url": "https://www.chicagobooth.edu/review",
    "events_feed": dict(_UCHICAGO_EVENTS_ICS),
    "keywords": ["chicago booth", "mba", "business school", "finance", "economics"],
    "social": {
        "instagram": "https://www.instagram.com/chicagobooth/",
        "linkedin": "https://www.linkedin.com/school/chicago-booth/",
        "x": "https://x.com/ChicagoBooth",
        "youtube": "https://www.youtube.com/user/ChicagoBooth",
        "facebook": "https://www.facebook.com/ChicagoBooth",
    },
}

# ── The program catalog (real majors/degrees, organized by school) ─────────
# slug = idempotency key. Every program is mapped to its owning school from UChicago's
# official structure. Each maps to a College Scorecard Field-of-Study CIP for UNITID
# 144050 (the deterministic federal view) where earnings are published. Graduate degrees
# use the generic ``masters``/``professional`` type with the real degree name carried in
# the program name.
PROGRAMS: list[dict] = [
    # ── The College (undergraduate A.B./B.S. majors) ──
    {
        "slug": "uchicago-economics-bs",
        "school": _COLLEGE,
        "program_name": "Economics",
        "degree_type": "bachelors",
        "cip": "45.06",
        "duration_months": 48,
        "description": (
            "Economics — micro, macro and econometrics in the tradition of the Chicago "
            "school; one of the College's largest and most prominent majors."
        ),
    },
    {
        "slug": "uchicago-computer-science-bs",
        "school": _COLLEGE,
        "program_name": "Computer Science",
        "degree_type": "bachelors",
        "cip": "11.07",
        "duration_months": 48,
        "description": (
            "Computer science — theory, systems, machine learning and applications, "
            "offered as the B.S. and B.A. and one of the fastest-growing College majors."
        ),
    },
    {
        "slug": "uchicago-mathematics-bs",
        "school": _COLLEGE,
        "program_name": "Mathematics",
        "degree_type": "bachelors",
        "cip": "27.01",
        "duration_months": 48,
        "description": "Mathematics — analysis, algebra, geometry and number theory.",
    },
    {
        "slug": "uchicago-statistics-bs",
        "school": _COLLEGE,
        "program_name": "Statistics",
        "degree_type": "bachelors",
        "cip": "27.05",
        "duration_months": 48,
        "description": (
            "Statistics — probability, statistical inference and data-driven computation."
        ),
    },
    {
        "slug": "uchicago-political-science-bs",
        "school": _COLLEGE,
        "program_name": "Political Science",
        "degree_type": "bachelors",
        "cip": "45.10",
        "duration_months": 48,
        "description": (
            "Political science — American, comparative and international politics and "
            "political theory."
        ),
    },
    {
        "slug": "uchicago-biology-bs",
        "school": _COLLEGE,
        "program_name": "Biological Sciences",
        "degree_type": "bachelors",
        "cip": "26.01",
        "duration_months": 48,
        "description": (
            "Biological sciences — genetics, cell and molecular biology, ecology and "
            "evolution, taught through the Biological Sciences Division."
        ),
    },
    {
        "slug": "uchicago-neuroscience-bs",
        "school": _COLLEGE,
        "program_name": "Neuroscience",
        "degree_type": "bachelors",
        "cip": "26.15",
        "duration_months": 48,
        "description": (
            "Neuroscience — the molecular, cellular, systems and cognitive study of the "
            "nervous system."
        ),
    },
    {
        "slug": "uchicago-english-bs",
        "school": _COLLEGE,
        "program_name": "English Language and Literature",
        "degree_type": "bachelors",
        "cip": "23.01",
        "duration_months": 48,
        "description": "English — literature in English, criticism and creative writing.",
    },
    {
        "slug": "uchicago-history-bs",
        "school": _COLLEGE,
        "program_name": "History",
        "degree_type": "bachelors",
        "cip": "54.01",
        "duration_months": 48,
        "description": "History — the study of the human past across periods and regions.",
    },
    {
        "slug": "uchicago-public-policy-bs",
        "school": _COLLEGE,
        "program_name": "Public Policy Studies",
        "degree_type": "bachelors",
        "cip": "44.05",
        "duration_months": 48,
        "description": (
            "Public policy studies — an interdisciplinary major analyzing public problems "
            "with economics, statistics and the social sciences."
        ),
    },
    {
        "slug": "uchicago-psychology-bs",
        "school": _COLLEGE,
        "program_name": "Psychology",
        "degree_type": "bachelors",
        "cip": "42.27",
        "duration_months": 48,
        "description": "Psychology — cognitive, developmental, social and clinical science.",
    },
    # ── Booth School of Business (the flagship) ──
    {
        "slug": "uchicago-mba",
        "school": _BOOTH,
        "program_name": "Master of Business Administration (Full-Time MBA)",
        "degree_type": "masters",
        "cip": "52.02",
        "duration_months": 21,
        "description": (
            "Chicago Booth's Full-Time MBA — a rigorous, discipline-based program built on "
            "the most flexible curriculum among the top business schools, requiring only a "
            "short foundation plus the experiential LEAD program before students design "
            "their own path across thirteen-plus concentrations."
        ),
    },
    # ── Harris School of Public Policy ──
    {
        "slug": "uchicago-mpp",
        "school": _HARRIS,
        "program_name": "Master of Public Policy (MPP)",
        "degree_type": "masters",
        "cip": "44.05",
        "duration_months": 21,
        "description": (
            "The Master of Public Policy — Harris's flagship degree, training students to "
            "use economics, statistics and data analysis to solve public problems."
        ),
    },
    # ── The University of Chicago Law School ──
    {
        "slug": "uchicago-jd",
        "school": _LAW,
        "program_name": "Juris Doctor (JD)",
        "degree_type": "professional",
        "cip": "22.01",
        "duration_months": 36,
        "description": (
            "The Juris Doctor — the Law School's three-year professional degree, shaped by "
            "the school's influential law-and-economics tradition."
        ),
    },
    # ── Pritzker School of Medicine ──
    {
        "slug": "uchicago-md",
        "school": _PRITZKER_MED,
        "program_name": "Doctor of Medicine (MD)",
        "degree_type": "professional",
        "cip": "51.12",
        "duration_months": 48,
        "description": (
            "The Doctor of Medicine — Pritzker's four-year M.D. program, distinguished by a "
            "small class size and a strong emphasis on research."
        ),
    },
    # ── Crown Family School of Social Work, Policy, and Practice ──
    {
        "slug": "uchicago-social-work-am",
        "school": _CROWN,
        "program_name": "Master of Arts in Social Work (AM)",
        "degree_type": "masters",
        "cip": "44.07",
        "duration_months": 24,
        "description": (
            "The A.M. in social work — Crown Family School's professional degree preparing "
            "clinical and administrative social-work practitioners."
        ),
    },
    # ── University of Chicago Divinity School ──
    {
        "slug": "uchicago-divinity-mdiv",
        "school": _DIVINITY,
        "program_name": "Master of Divinity (MDiv)",
        "degree_type": "masters",
        "cip": "39.06",
        "duration_months": 36,
        "description": (
            "The Master of Divinity — the Divinity School's professional degree in the "
            "academic study and practice of religion and ministry."
        ),
    },
    # ── Pritzker School of Molecular Engineering ──
    {
        "slug": "uchicago-molecular-engineering-bs",
        "school": _PME,
        "program_name": "Molecular Engineering",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": (
            "Molecular engineering — the nation's first undergraduate major in the field, "
            "applying engineering at the molecular scale across quantum, materials, water "
            "and immunoengineering."
        ),
    },
    # ── Division of the Physical Sciences ──
    {
        "slug": "uchicago-mpcs",
        "school": _PHYS_SCI,
        "program_name": "Master's Program in Computer Science (MPCS)",
        "degree_type": "masters",
        "cip": "11.07",
        "duration_months": 18,
        "description": (
            "The Master's Program in Computer Science — a professional master's spanning "
            "software, systems, machine learning and applications, with immersive and "
            "part-time options."
        ),
    },
    {
        "slug": "uchicago-statistics-ms",
        "school": _PHYS_SCI,
        "program_name": "Master of Science in Statistics",
        "degree_type": "masters",
        "cip": "27.05",
        "duration_months": 21,
        "description": (
            "The M.S. in Statistics — graduate training in statistical theory, methodology "
            "and computation in the Department of Statistics."
        ),
    },
    # ── Division of the Social Sciences ──
    {
        "slug": "uchicago-cir-ma",
        "school": _SOC_SCI,
        "program_name": "Master of Arts in International Relations (CIR)",
        "degree_type": "masters",
        "cip": "45.09",
        "duration_months": 21,
        "description": (
            "The Committee on International Relations (CIR) — the oldest graduate program "
            "of its kind in the United States, awarding the M.A. in international relations."
        ),
    },
    {
        "slug": "uchicago-mapss-ma",
        "school": _SOC_SCI,
        "program_name": "Master of Arts Program in the Social Sciences (MAPSS)",
        "degree_type": "masters",
        "cip": "45.01",
        "duration_months": 12,
        "description": (
            "MAPSS — a one-year interdisciplinary M.A. across the social sciences, "
            "preparing students for doctoral study and applied research."
        ),
    },
    # ── Division of the Humanities ──
    {
        "slug": "uchicago-maph-ma",
        "school": _HUMANITIES,
        "program_name": "Master of Arts Program in the Humanities (MAPH)",
        "degree_type": "masters",
        "cip": "24.01",
        "duration_months": 12,
        "description": (
            "MAPH — a one-year interdisciplinary M.A. across the humanities and the arts, "
            "with creative-writing and digital-studies options."
        ),
    },
]

_EXPLICIT_DEPARTMENTS: dict[str, str] = {
    "uchicago-economics-bs": "Economics",
    "uchicago-computer-science-bs": "Computer Science",
    "uchicago-mathematics-bs": "Mathematics",
    "uchicago-statistics-bs": "Statistics",
    "uchicago-political-science-bs": "Political Science",
    "uchicago-biology-bs": "Biological Sciences",
    "uchicago-neuroscience-bs": "Neuroscience",
    "uchicago-english-bs": "English Language and Literature",
    "uchicago-history-bs": "History",
    "uchicago-public-policy-bs": "Public Policy Studies",
    "uchicago-psychology-bs": "Psychology",
    "uchicago-mba": _BOOTH,
    "uchicago-mpp": _HARRIS,
    "uchicago-jd": _LAW,
    "uchicago-md": _PRITZKER_MED,
    "uchicago-social-work-am": _CROWN,
    "uchicago-divinity-mdiv": _DIVINITY,
    "uchicago-molecular-engineering-bs": _PME,
    "uchicago-mpcs": "Computer Science",
    "uchicago-statistics-ms": "Statistics",
    "uchicago-cir-ma": "Committee on International Relations",
    "uchicago-mapss-ma": "Master of Arts Program in the Social Sciences",
    "uchicago-maph-ma": "Master of Arts Program in the Humanities",
}
_EXPLICIT_FULL_NAMES: dict[str, str] = {
    "uchicago-economics-bs": "Bachelor of Arts in Economics",
    "uchicago-computer-science-bs": "Bachelor of Science in Computer Science",
    "uchicago-mathematics-bs": "Bachelor of Science in Mathematics",
    "uchicago-statistics-bs": "Bachelor of Science in Statistics",
    "uchicago-political-science-bs": "Bachelor of Arts in Political Science",
    "uchicago-biology-bs": "Bachelor of Science in Biological Sciences",
    "uchicago-neuroscience-bs": "Bachelor of Science in Neuroscience",
    "uchicago-english-bs": "Bachelor of Arts in English Language and Literature",
    "uchicago-history-bs": "Bachelor of Arts in History",
    "uchicago-public-policy-bs": "Bachelor of Arts in Public Policy Studies",
    "uchicago-psychology-bs": "Bachelor of Arts in Psychology",
    "uchicago-molecular-engineering-bs": "Bachelor of Science in Molecular Engineering",
}
for _p in PROGRAMS:
    if _p["slug"] in _EXPLICIT_DEPARTMENTS:
        _p["department"] = _EXPLICIT_DEPARTMENTS[_p["slug"]]
    if _p["slug"] in _EXPLICIT_FULL_NAMES:
        _p["program_name"] = _EXPLICIT_FULL_NAMES[_p["slug"]]

_EXISTING_SLUGS = {p["slug"] for p in PROGRAMS}
_EXISTING_CIP_KEYS = {(p.get("cip"), p["degree_type"]) for p in PROGRAMS if p.get("cip")}

# Professional schools where the degree is owned by the school itself.
_PROFESSIONAL_SCHOOLS = frozenset({
    _BOOTH,
    _HARRIS,
    _LAW,
    _PRITZKER_MED,
    _CROWN,
    _DIVINITY,
    _PME,
})

# Federal CIP field titles → UChicago's published department / program names.
_CIP_TO_DEPARTMENT: dict[str, str] = {
    "Political Science and Government": "Political Science",
    "Research and Experimental Psychology": "Psychology",
    "Clinical, Counseling and Applied Psychology": "Psychology",
    "Biology, General": "Biological Sciences",
    "English Language and Literature, General": "English Language and Literature",
    "Neurobiology and Neurosciences": "Neuroscience",
    "Public Policy Analysis": "Public Policy Studies",
    "Geological and Earth Sciences/Geosciences": "Geophysical Sciences",
    "Linguistic, Comparative, and Related Language Studies and Services": "Linguistics",
    "Social Sciences, General": "Social Sciences",
    "Fine and Studio Arts": "Visual Arts",
    "Film/Video and Photographic Arts": "Cinema and Media Studies",
    "Design and Applied Arts": "Media Arts, Data and Design",
    "Drama/Theatre Arts and Stagecraft": "Theater and Performance Studies",
    "International Relations and National Security Studies": "International Relations",
    "Business Administration, Management and Operations": "Business Administration",
    "Business/Commerce, General": "Business",
    "Management Sciences and Quantitative Methods": "Business Economics",
    "Finance and Financial Management Services": "Finance",
    "Marketing": "Marketing",
    "Social Work": "Social Work",
    "Law": "Law",
    "Health Professions (CIP 51.12)": "Medicine",
    "Medieval and Renaissance Studies": "Medieval Studies",
    "Science, Technology and Society": "Science, Technology, and Society",
    "Nutrition Sciences": "Nutritional Science",
    "Sustainability Studies": "Environment, Geography, and Urbanization",
    "Area Studies": "Area Studies",
    "Ethnic, Cultural Minority, Gender, and Group Studies": "Gender and Sexuality Studies",
    "Natural Resources Conservation and Research": "Environmental and Urban Studies",
    "Environmental/Natural Resources Management and Policy": "Environmental and Urban Studies",
    "Legal Research and Advanced Professional Studies": "Legal Studies",
    "Public Health": "Public Health Sciences",
    "Liberal Arts and Sciences, General Studies and Humanities": "Humanities",
    "Rhetoric and Composition/Writing Studies": "Writing",
    "Visual and Performing Arts, Other": "Visual Arts",
    "Social Sciences, Other": "Social Sciences",
    "Radio, Television, and Digital Communication": "Media Arts and Design",
    "Computer and Information Sciences, General": "Computer Science",
    "Information Science/Studies": "Information Science",
    "Teacher Education and Professional Development, Specific Levels and Methods": (
        "Education"
    ),
    "Chemical Engineering": "Molecular Engineering",
    "Engineering Physics": "Molecular Engineering",
    "East Asian Languages, Literatures, and Linguistics": "East Asian Languages and Civilizations",
    "Slavic, Baltic and Albanian Languages, Literatures, and Linguistics": (
        "Slavic Languages and Literatures"
    ),
    "Germanic Languages, Literatures, and Linguistics": "Germanic Studies",
    "Romance Languages, Literatures, and Linguistics": "Romance Languages and Literatures",
    "Middle/Near Eastern and Semitic Languages, Literatures, and Linguistics": (
        "Near Eastern Languages and Civilizations"
    ),
    "Classics and Classical Languages, Literatures, and Linguistics": "Classics",
    "Biochemistry, Biophysics and Molecular Biology": "Biochemistry and Molecular Biology",
    "Cell/Cellular Biology and Anatomical Sciences": "Cell Biology",
    "Microbiological Sciences and Immunology": "Microbiology",
    "Genetics": "Genetics",
    "Physiology, Pathology and Related Sciences": "Organismal Biology and Anatomy",
    "Biomathematics, Bioinformatics, and Computational Biology": "Computational Biology",
    "Ecology, Evolution, Systematics, and Population Biology": "Ecology and Evolution",
    "Applied Mathematics": "Applied Mathematics",
    "Physical Sciences, General": "Physical Sciences",
    "Astronomy and Astrophysics": "Astronomy and Astrophysics",
    "Geography and Cartography": "Geography",
    "Anthropology": "Anthropology",
    "Economics": "Economics",
    "History": "History",
    "Mathematics": "Mathematics",
    "Statistics": "Statistics",
    "Computer Science": "Computer Science",
    "Chemistry": "Chemistry",
    "Physics": "Physics",
    "Philosophy": "Philosophy",
    "Music": "Music",
    "Sociology": "Sociology",
}


def _department_for(field_name: str, school: str) -> str:
    """Owning department — map federal CIP titles to UChicago's published names."""
    mapped = _CIP_TO_DEPARTMENT.get(field_name, field_name)
    if school in _PROFESSIONAL_SCHOOLS:
        if mapped != field_name:
            return mapped
        return school
    if mapped.lower() in school.lower() or school.lower() in mapped.lower():
        return school
    return mapped


# IPEDS rows that do not map to distinct UChicago degrees — tracks within Molecular
# Engineering, Booth graduate-only business degrees mis-tagged as College bachelors, or
# credentials the institution does not publish (e.g. no B.S. in Social Work at Crown).
_SKIP_CATALOG_SLUGS = frozenset({
    "uchicago-business-commerce-general-bs",
    "uchicago-business-administration-management-and-operations-bs",
    "uchicago-management-sciences-and-quantitative-methods-bs",
    "uchicago-social-work-bs",
    "uchicago-chemical-engineering-bs",
    "uchicago-chemical-engineering-ms",
    "uchicago-engineering-physics-bs",
    # Redundant CIP rows that map to the same published degree as an explicit catalog entry.
    "uchicago-computer-and-information-sciences-general-bs",
    "uchicago-research-and-experimental-psychology-bs",
    "uchicago-research-and-experimental-psychology-ms",
    "uchicago-clinical-counseling-and-applied-psychology-bs",
    "uchicago-clinical-counseling-and-applied-psychology-ms",
    "uchicago-design-and-applied-arts-bs",
    "uchicago-visual-and-performing-arts-other-ms",
    # Professional degrees already modeled as explicit flagship programs.
    "uchicago-law-prof",
    "uchicago-health-professions-cip-51-12-prof",
})


# College majors that award the B.S. (STEM and quantitative fields); others default to B.A.
_BS_MAJORS = frozenset({
    "Computer Science",
    "Mathematics",
    "Statistics",
    "Applied Mathematics",
    "Physics",
    "Chemistry",
    "Astronomy and Astrophysics",
    "Molecular Engineering",
    "Biological Sciences",
    "Neuroscience",
    "Geophysical Sciences",
    "Computational Biology",
    "Information Science",
    "Biochemistry and Molecular Biology",
    "Cell Biology",
    "Microbiology",
    "Genetics",
    "Organismal Biology and Anatomy",
    "Ecology and Evolution",
    "Nutritional Science",
    "Physical Sciences",
    "Environmental and Urban Studies",
})

_MS_SCHOOLS = frozenset({
    _PHYS_SCI,
    _PME,
})


def _chicago_program_name(
    field_name: str, degree_type: str, school: str, slug: str
) -> str:
    """Real UChicago degree designation — never a CIP-rollup credential prefix."""
    dept = _department_for(field_name, school)
    if degree_type == "bachelors":
        if school == _PME or dept in _BS_MAJORS:
            return f"Bachelor of Science in {dept}"
        return f"Bachelor of Arts in {dept}"
    if degree_type == "masters":
        if school in _MS_SCHOOLS or dept in _BS_MAJORS:
            return f"Master of Science in {dept}"
        return f"Master of Arts in {dept}"
    if degree_type == "certificate":
        return f"Graduate Certificate in {dept}"
    if degree_type == "phd":
        return f"Doctor of Philosophy in {dept}"
    return dept


def _field_from_program_name(program_name: str) -> str | None:
    """Extract field title from a disambiguated program name."""
    for prefix in (
        "Bachelor of Arts in ",
        "Bachelor of Science in ",
        "Bachelor's in ",
        "Master of Science in ",
        "Master of Arts in ",
        "Master's in ",
        "Doctor of Philosophy in ",
        "Graduate Certificate in ",
        "Professional program in ",
    ):
        if program_name.startswith(prefix):
            return program_name[len(prefix):]
    return None


def _needs_normalize(desc: str, program_name: str = "") -> bool:
    """True when a description is a classification or template stub."""
    if not desc:
        return True
    if program_name and desc.startswith(program_name):
        return True
    if _CLASSIFICATION_STUB_RE.match(desc):
        return True
    if _TEMPLATE_STUB_RE.search(desc):
        return True
    if "offered through the " in desc:
        return True
    # Short "Field — topic" stubs from the first breadth pass.
    if " — " in desc and len(desc) < 160 and not desc.startswith("The "):
        return True
    return False


def _chicago_description(spec: dict, field: str | None = None) -> str:
    """Field-specific description — never the degree-type classification stub."""
    slug = spec["slug"]
    fmt = spec.get("delivery_format", "in_person")
    delivery = ""
    if fmt == "online":
        delivery = " Delivered online."
    elif fmt == "hybrid":
        delivery = " Delivered in hybrid format."
    if slug in SLUG_DESCRIPTIONS:
        return f"{SLUG_DESCRIPTIONS[slug]}{delivery}"
    field_key = (
        field
        or spec.get("_field_name")
        or _SLUG_TO_FIELD.get(slug)
        or _field_from_program_name(spec.get("program_name", ""))
        or spec.get("department")
        or spec.get("program_name", "")
    )
    if field_key in FIELD_ALIASES:
        field_key = FIELD_ALIASES[field_key]
    # Per-credential body: a field's master's row uses the graduate clause so it never
    # shares text with the bachelor's row of the same field (anti-stub verbatim gate).
    # Key the graduate lookup off the clean published program_name field (e.g. "Master of
    # Science in Economics" -> "Economics"), which matches the GRAD dict keys even when the
    # raw IPEDS field aliases to a different FIELD_DESCRIPTIONS key.
    clause = None
    if spec["degree_type"] == "masters":
        pname_field = _field_from_program_name(spec.get("program_name", "")) or field_key
        clause = GRAD_FIELD_DESCRIPTIONS.get(pname_field) or GRAD_FIELD_DESCRIPTIONS.get(field_key)
    if not clause:
        clause = FIELD_DESCRIPTIONS.get(field_key)
    if not clause:
        raise ValueError(
            f"Missing FIELD_DESCRIPTIONS entry for {field_key!r} ({slug})"
        )
    return f"{clause}{delivery}"


def _normalize_program(spec: dict, field_name: str | None = None) -> None:
    """Stamp a field-specific description on stub program nodes."""
    if not _needs_normalize(spec.get("description") or "", spec.get("program_name", "")):
        return
    spec["description"] = _chicago_description(spec, field=field_name)


def _build_catalog() -> list[dict]:
    """Append breadth-first program nodes from the IPEDS Field-of-Study catalog."""
    out: list[dict] = []
    seen = set(_EXISTING_SLUGS)
    for slug, school, name, dtype, cip, dur, fmt, _desc in _IPEDS_CATALOG:
        if slug in seen:
            continue
        if slug in _SKIP_CATALOG_SLUGS:
            continue
        if (cip, dtype) in _EXISTING_CIP_KEYS:
            continue
        # Drop federal-certificate padding (one minted per CIP×award-level): UChicago does
        # not publish a standalone graduate certificate in each of these fields, and the
        # row only duplicated the field's degree description (enrich-profile miss #2).
        if dtype == "certificate":
            continue
        if name.startswith("Program (CIP") or name.startswith("Health Professions (CIP"):
            continue
        seen.add(slug)
        dept = _department_for(name, school)
        pname = _chicago_program_name(name, dtype, school, slug)
        delivery = fmt if fmt in {"online", "hybrid"} else "in_person"
        spec = {
            "slug": slug,
            "school": school,
            "program_name": pname,
            "degree_type": dtype,
            "department": dept,
            "cip": cip,
            "duration_months": dur,
            "delivery_format": delivery,
            "_field_name": name,
        }
        _normalize_program(spec, name)
        spec.pop("_field_name", None)
        out.append(spec)
    return out


PROGRAMS += _build_catalog()
for _p in PROGRAMS:
    if _p["slug"] in _EXPLICIT_FULL_NAMES:
        _p["program_name"] = _EXPLICIT_FULL_NAMES[_p["slug"]]
    _normalize_program(_p, _field_from_program_name(_p.get("program_name", "")))

_catalog_errors = validate_catalog(PROGRAMS)
_stub_desc = sum(1 for p in PROGRAMS if "offered through the " in (p.get("description") or ""))
_new_templ = sum(1 for p in PROGRAMS if _TEMPLATE_STUB_RE.search(p.get("description") or ""))
if _stub_desc:
    _catalog_errors.append(f"template stub descriptions on {_stub_desc} programs")
if _new_templ:
    _catalog_errors.append(f"program_description template on {_new_templ} programs")
_classification_stubs = sum(
    1 for p in PROGRAMS if _CLASSIFICATION_STUB_RE.match(p.get("description") or "")
)
if _classification_stubs:
    _catalog_errors.append(
        f"classification-only descriptions on {_classification_stubs} programs"
    )
_name_prefix_desc = sum(
    1
    for p in PROGRAMS
    if (p.get("description") or "").startswith(p.get("program_name", ""))
)
if _name_prefix_desc:
    _catalog_errors.append(
        f"name-prefixed descriptions on {_name_prefix_desc} programs"
    )
_prefix_names = sum(1 for p in PROGRAMS if _PREFIX_NAME_RE.match(p.get("program_name", "")))
if _prefix_names:
    _catalog_errors.append(f"CIP-prefix program_name on {_prefix_names} programs")
if _catalog_errors:
    raise RuntimeError(f"UChicago catalog quality gate failed: {_catalog_errors}")

for _p in PROGRAMS:
    _p.setdefault("delivery_format", "in_person")

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

# Full official program names (program-page title); equal to the program name here.
_FULL_NAME_BY_SLUG: dict[str, str] = {p["slug"]: p["program_name"] for p in PROGRAMS}

# Official program/department/school home pages.
_WEBSITE_BY_SLUG: dict[str, str] = {
    "uchicago-economics-bs": "https://economics.uchicago.edu/",
    "uchicago-computer-science-bs": "https://college.uchicago.edu/academics/computer-science",
    "uchicago-mathematics-bs": "https://mathematics.uchicago.edu/",
    "uchicago-statistics-bs": "https://stat.uchicago.edu/",
    "uchicago-political-science-bs": "https://political-science.uchicago.edu/",
    "uchicago-biology-bs": "https://biologicalsciences.uchicago.edu/",
    "uchicago-neuroscience-bs": "https://college.uchicago.edu/academics/neuroscience",
    "uchicago-english-bs": "https://english.uchicago.edu/",
    "uchicago-history-bs": "https://history.uchicago.edu/",
    "uchicago-public-policy-bs": "https://college.uchicago.edu/academics/public-policy-studies",
    "uchicago-psychology-bs": "https://psychology.uchicago.edu/",
    "uchicago-mba": "https://www.chicagobooth.edu/mba/full-time",
    "uchicago-mpp": "https://harris.uchicago.edu/academics/degrees/master-public-policy-mpp",
    "uchicago-jd": "https://www.law.uchicago.edu/jd",
    "uchicago-md": "https://pritzker.uchicago.edu/",
    "uchicago-social-work-am": "https://crownschool.uchicago.edu/academics/am-program",
    "uchicago-divinity-mdiv": "https://divinity.uchicago.edu/master-divinity-mdiv",
    "uchicago-molecular-engineering-bs": "https://pme.uchicago.edu/academics/undergraduate-program",
    "uchicago-mpcs": "https://masters.cs.uchicago.edu/",
    "uchicago-statistics-ms": "https://stat.uchicago.edu/academics/ms-in-statistics/",
    "uchicago-cir-ma": "https://cir.uchicago.edu/",
    "uchicago-mapss-ma": "https://mapss.uchicago.edu/",
    "uchicago-maph-ma": "https://maph.uchicago.edu/",
}

# ── Who-it's-for + highlights (catalog baselines) ──────────────────────────
_WHO_BASELINE = (
    "Academically driven students seeking a rigorous, intellectually intense education at "
    "a top research university with a famous Core curriculum, no-loan financial aid, and "
    "the depth of one of the world's leading faculties."
)
_HL_BASELINE = ["The Core curriculum", "5:1 student-faculty ratio", "Need-met, no-loan aid"]
_WHO_GRAD_BASELINE = (
    "Graduate and professional students seeking a top-ranked University of Chicago degree "
    "with the resources of a major research university and an internationally recognized "
    "faculty."
)
_HL_GRAD_BASELINE = ["Top-ranked UChicago degree", "World-class faculty", "Rigorous & data-driven"]

_WHO_BY_SLUG = {
    "uchicago-mba": (
        "Ambitious professionals seeking the most flexible MBA among the top schools — a "
        "rigorous, analytical, discipline-based program with strong outcomes in finance, "
        "consulting and technology."
    ),
    "uchicago-economics-bs": (
        "Students who want a quantitatively rigorous economics education in the tradition "
        "of the Chicago school, inside a research university."
    ),
}
_HL_BY_SLUG = {
    "uchicago-mba": [
        "Most flexible top-tier MBA",
        "13+ concentrations",
        "$175k median base salary",
    ],
    "uchicago-economics-bs": [
        "Chicago school of economics",
        "Among the College's largest majors",
        "Strong placement",
    ],
}

# ── Curriculum / concentrations, where published (the flagship) ────────────
# Booth publishes its MBA concentrations; quoted from the official MBA Curriculum page.
_TRACKS_BY_SLUG: dict[str, dict] = {
    "uchicago-mba": {
        "label": "Booth MBA concentrations",
        "note": (
            "Booth's flexible curriculum requires only foundation courses (in financial "
            "accounting, microeconomics and statistics) plus the experiential LEAD program; "
            "students then build their own path and may earn from among the school's "
            "functional concentrations."
        ),
        "items": [
            {"name": "Accounting"},
            {"name": "Analytic Finance"},
            {"name": "Behavioral Science"},
            {"name": "Business Analytics"},
            {"name": "Econometrics and Statistics"},
            {"name": "Economics"},
            {"name": "Entrepreneurship"},
            {"name": "Finance"},
            {"name": "General Management"},
            {"name": "International Business"},
            {"name": "Marketing Management"},
            {"name": "Operations Management"},
            {"name": "Strategic Management"},
        ],
        "source": "Chicago Booth — MBA Curriculum",
        "source_url": "https://www.chicagobooth.edu/mba/academics/curriculum",
    },
    "uchicago-molecular-engineering-bs": {
        "label": "Molecular Engineering tracks",
        "note": (
            "Undergraduates choose among bioengineering, chemical engineering, or quantum "
            "engineering tracks within the single Molecular Engineering major (PME)."
        ),
        "items": [
            {"name": "Bioengineering"},
            {"name": "Chemical engineering"},
            {"name": "Quantum engineering"},
        ],
        "source": "PME — Undergraduate major FAQs",
        "source_url": "https://pme.uchicago.edu/undergraduate-program/undergraduate-major-and-minor-faqs",
    },
}

# ── Program-specific cost ──────────────────────────────────────────────────
# The College undergraduate cost: tuition is the official 2025-26 figure (UChicago CDS
# 2024-25, Section G); cost of attendance and average net price are College Scorecard
# (UNITID 144050).
_TUITION_UG = 71325
_UNDERGRAD_COA = 90360
_AVG_NET_PRICE = 14860

# Per-program graduate / professional tuition (each school's official cost page, academic
# year as noted). Programs whose only tuition source is the JavaScript-rendered University
# Bursar page are omitted (cost_data.tuition_usd recorded in _standard.omitted) rather
# than guessed: Harris MPP, Divinity MDiv, M.S. Statistics, CIR, MAPSS, MAPH.
_COST_BY_SLUG: dict[str, dict] = {
    "uchicago-mba": {
        "tuition_usd": 89976,
        "total_cost_of_attendance": 132449,
        "funded": False,
        "note": (
            "Full-program Full-Time MBA tuition charged over six quarterly installments; "
            "estimated 2026-27 nine-month single-student cost of attendance shown."
        ),
        "source": "Chicago Booth — Full-Time MBA Cost",
        "source_url": "https://www.chicagobooth.edu/mba/full-time/admissions/cost",
        "year": "2026-27",
    },
    "uchicago-jd": {
        "tuition_usd": 83316,
        "funded": False,
        "note": "J.D. tuition (each of the three years).",
        "source": "The University of Chicago Law School — Cost of Attendance 2025-26",
        "source_url": "https://www.law.uchicago.edu/25-26-COA",
        "year": "2025-26",
    },
    "uchicago-md": {
        "tuition_usd": 64844,
        "funded": False,
        "note": (
            "First-year (M1) tuition; later years differ (M3/M4 are charged over four quarters)."
        ),
        "source": "Pritzker School of Medicine — Student Budget",
        "source_url": "https://pritzker.uchicago.edu/admissions/student-budget",
        "year": "2025-26",
    },
    "uchicago-social-work-am": {
        "tuition_usd": 54873,
        "funded": False,
        "note": "Full-time A.M. tuition ($18,291 per quarter across three quarters).",
        "source": "Crown Family School — Tuition, Fees & Financial Aid",
        "source_url": "https://crownschool.uchicago.edu/admissions/tuition-fees-financial-aid",
        "year": "2026-27",
    },
    "uchicago-mpcs": {
        "tuition_usd": 66762,
        "funded": False,
        "note": (
            "Nine-course M.S. total tuition ($7,415 per course); the twelve-course M.S. "
            "totals $89,016."
        ),
        "source": "Master's Program in Computer Science — Tuition & Fees",
        "source_url": "https://masters.cs.uchicago.edu/mpcs-admissions/tuition-fees/",
        "year": "2026-27",
    },
}

# Programs whose tuition is omitted (bursar-only / not first-party machine-verifiable).
_COST_OMITTED_SLUGS = {
    "uchicago-mpp",
    "uchicago-divinity-mdiv",
    "uchicago-statistics-ms",
    "uchicago-cir-ma",
    "uchicago-mapss-ma",
    "uchicago-maph-ma",
}

# Minimal cost record for tuition-omitted graduate programs — carries the canonical
# source (the University Bursar) without asserting a figure we could not verify.
_COST_OMITTED_RECORD = {
    "funded": False,
    "note": (
        "Tuition for this program is published on the University of Chicago Bursar's "
        "tuition-and-fees pages; the exact figure could not be machine-verified from a "
        "first-party page at author time and is omitted rather than guessed."
    ),
    "source": "University of Chicago — Office of the Bursar (tuition & fees)",
    "source_url": "https://bursar.uchicago.edu/tuition-fees/",
}

# ── Program-specific outcomes (College Scorecard Field of Study, by CIP) ────
# Where the federal College Scorecard publishes a Field-of-Study median earnings (one
# year after completion) for an awarded CIP at UNITID 144050, we use it (program scope).
# Programs whose CIP earnings are suppressed fall back to the institution 10-year median.
# Tuples are (median_earnings_1yr, cip).
_FOS_OUTCOMES: dict[str, tuple[int, str]] = {
    "uchicago-economics-bs": (92075, "45.06"),
    "uchicago-computer-science-bs": (117578, "11.07"),
    "uchicago-mathematics-bs": (100421, "27.01"),
    "uchicago-statistics-bs": (82681, "27.05"),
    "uchicago-political-science-bs": (56022, "45.10"),
    "uchicago-biology-bs": (35275, "26.01"),
    "uchicago-neuroscience-bs": (37246, "26.15"),
    "uchicago-english-bs": (44397, "23.01"),
    "uchicago-history-bs": (46616, "54.01"),
    "uchicago-public-policy-bs": (60057, "44.05"),
    "uchicago-psychology-bs": (31986, "42.27"),
    "uchicago-mpp": (79721, "44.05"),
    "uchicago-jd": (199603, "22.01"),
    "uchicago-md": (70564, "51.12"),
    "uchicago-social-work-am": (52551, "44.07"),
    "uchicago-divinity-mdiv": (34557, "39.06"),
    "uchicago-mpcs": (135918, "11.07"),
    "uchicago-statistics-ms": (115925, "27.05"),
    "uchicago-cir-ma": (66182, "45.09"),
    "uchicago-mapss-ma": (53788, "45.01"),
    "uchicago-maph-ma": (26094, "24.01"),
}

# Verbatim methodology for the program-scope Scorecard FOS earnings figure.
_FOS_CONDITIONS = (
    "Median earnings of graduates who received federal financial aid, measured "
    "approximately one year after program completion; reported by the U.S. Department of "
    "Education College Scorecard Field of Study by 4-digit CIP code. Programs with too "
    "few completers are suppressed."
)

# Per-slug conditions override where the generic FOS note needs an extra caveat.
_FOS_CONDITIONS_BY_SLUG: dict[str, str] = {
    "uchicago-md": (
        "Median earnings of M.D. graduates who received federal financial aid, measured "
        "approximately one year after completion (U.S. Dept. of Education College "
        "Scorecard Field of Study, CIP 51.12). One year after the M.D., most graduates "
        "are resident physicians, so this figure reflects residency stipends rather than "
        "attending-physician salaries."
    ),
}

# Institution-wide outcomes fallback (College Scorecard, UNITID 144050), used for degree
# programs whose program-level one-year earnings are suppressed (Molecular Engineering).
_OUTCOMES_INSTITUTION = {
    "median_salary": 91885,
    "scope": "institution",
    "conditions": (
        "University of Chicago institution-wide median earnings ten years after entry "
        "(College Scorecard, UNITID 144050); a program-level one-year earnings figure is "
        "not published (suppressed) for this field of study."
    ),
    "source": "U.S. Dept. of Education College Scorecard (UNITID 144050)",
    "source_url": "https://collegescorecard.ed.gov/school/?144050",
}

# ── Booth MBA employment-report outcomes (the flagship) ─────────────────────
# From the Chicago Booth Full-Time MBA Employment Report, Class of 2024.
_MBA_OUTCOMES = {
    "median_salary": 175000,
    "median_signing_bonus": 31000,
    "scope": "program",
    "earnings_timeframe": "median base salary at graduation",
    "top_industries": [
        "Consulting",
        "Technology",
        "Diversified financial services",
        "Investment banking & brokerage",
        "Private equity",
    ],
    "conditions": (
        "Median base salary and median signing bonus for the Chicago Booth Full-Time MBA "
        "Class of 2024. The report states that roughly eighty percent of the class sought "
        "employment upon completing the MBA, and that nearly nine in ten of those students "
        "secured their roles before or within three months of graduation."
    ),
    "source": "Chicago Booth — Full-Time MBA Employment Report, Class of 2024",
    "source_url": "https://www.chicagobooth.edu/employmentreport",
}

# ── Class profile, where published (the flagship) ──────────────────────────
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    "uchicago-mba": {
        "cohort_size": "635 students in the entering Full-Time MBA class (Class of 2027)",
        "international_pct": 0.37,
        "note": (
            "Entering Full-Time MBA Class of 2027: 635 students, 41% women, 37% "
            "international; average GMAT 729 (median 730)."
        ),
        "source": "Chicago Booth — Full-Time MBA Class Profile",
        "source_url": "https://www.chicagobooth.edu/mba/full-time/admissions/class-profile",
    },
}

# ── Faculty (lead + directory link), where confidently sourced ─────────────
# No per-program faculty roster was verified first-party this pass; omitted for every
# program (recorded in each program's _standard.omitted) rather than hand-picked.
_FACULTY_BY_SLUG: dict[str, dict] = {}

# ── Aggregated, cited student-review themes (≥2 third-party sources, the flagship) ──
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "uchicago-mba": {
        "summary": (
            "Students and third-party guides consistently praise Booth for its analytical "
            "rigor and its signature flexible curriculum — beyond a short foundation and "
            "the experiential LEAD program, students design their own course of study — and "
            "for strong outcomes in finance, consulting and analytics. Common cautions are "
            "a less tightly-knit fixed cohort than some peer programs and that, outside its "
            "core recruiting industries, some students run a more self-directed job search."
        ),
        "themes": [
            {
                "label": "Analytical rigor",
                "sentiment": "positive",
                "detail": (
                    "A quantitatively rigorous, data-driven program respected in finance, "
                    "economics and analytics."
                ),
            },
            {
                "label": "Flexible curriculum",
                "sentiment": "positive",
                "detail": (
                    "Only foundation courses and LEAD are required; students tailor the rest "
                    "of the MBA."
                ),
            },
            {
                "label": "Career outcomes",
                "sentiment": "positive",
                "detail": (
                    "Strong placement in consulting, finance and technology with a $175,000 "
                    "median base salary (Class of 2024)."
                ),
            },
            {
                "label": "Cohort cohesion",
                "sentiment": "caution",
                "detail": (
                    "The flexible, non-lockstep structure means a less tight fixed cohort; "
                    "students invest effort to build community."
                ),
            },
            {
                "label": "Self-directed recruiting",
                "sentiment": "caution",
                "detail": (
                    "Outside core recruiting industries, some students run a more independent "
                    "search."
                ),
            },
        ],
        "sources": [
            {
                "label": "GMAT Club — Chicago Booth MBA reviews",
                "url": "https://gmatclub.com/reviews/business_school/booth-chicago-5",
            },
            {
                "label": "U.S. News — University of Chicago (Booth) Best Business Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/university-of-chicago-01073",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "uchicago-computer-science-bs": {
        "summary": (
            "Students and third-party guides describe UChicago's computer-science major as "
            "a fast-rising, theory-strong program — Niche ranks it #20 nationally for "
            "undergraduate CS (2026) and the department notes a U.S. News graduate ranking "
            "of #27 (2025), up from the mid-30s a decade ago — with growing enrollments "
            "and interdisciplinary ties to economics, data science, and public policy. "
            "Common cautions are that CS is still smaller than peer flagships like CMU or "
            "MIT, introductory courses can feel large, and the Core curriculum adds breadth "
            "beyond a purely technical track."
        ),
        "themes": [
            {
                "label": "Rising national standing",
                "sentiment": "positive",
                "detail": (
                    "Niche #20 Best Colleges for Computer Science (2026); U.S. News "
                    "graduate CS #27 (2025)."
                ),
            },
            {
                "label": "Theory & research depth",
                "sentiment": "positive",
                "detail": (
                    "Top-20 subfield rankings in theory and systems; strong faculty hiring "
                    "and research momentum."
                ),
            },
            {
                "label": "Interdisciplinary campus",
                "sentiment": "positive",
                "detail": (
                    "CS is the College's second-largest major, paired with a renowned "
                    "data-science program and policy/economics pathways."
                ),
            },
            {
                "label": "Smaller than CS flagships",
                "sentiment": "caution",
                "detail": (
                    "Department scale and industry-recruiting volume trail the very largest "
                    "CS schools."
                ),
            },
            {
                "label": "Core + quantitative load",
                "sentiment": "mixed",
                "detail": (
                    "UChicago's broad Core adds intellectual breadth but can compete with "
                    "technical electives for some CS students."
                ),
            },
        ],
        "sources": [
            {
                "label": "Niche — Best Colleges for Computer Science (2026)",
                "url": "https://www.niche.com/colleges/search/best-colleges-for-computer-science/",
            },
            {
                "label": "UChicago CS — A Bet Worth Placing: Computing and Data Science",
                "url": (
                    "https://cs.uchicago.edu/news/"
                    "a-bet-worth-placing-computing-and-data-science-at-uchicago/"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "uchicago-jd": {
        "summary": (
            "Students and third-party guides describe Chicago Law as one of the nation's "
            "most rigorous top-tier programs — U.S. News ranked it #2 nationally (tie with "
            "Yale) in 2026 — praised for its quarter system, accessible faculty, and strong "
            "Big Law and clerkship placement. Common cautions are extremely competitive "
            "admission, high tuition, and an intellectually demanding culture that can feel "
            "intense for students seeking a more relaxed law-school experience."
        ),
        "themes": [
            {
                "label": "Elite national rank",
                "sentiment": "positive",
                "detail": "U.S. News Best Law Schools 2026: #2 (tie with Yale).",
            },
            {
                "label": "Rigorous quarter system",
                "sentiment": "positive",
                "detail": (
                    "A fast-paced, analytically demanding curriculum with small sections "
                    "and strong faculty engagement."
                ),
            },
            {
                "label": "Career outcomes",
                "sentiment": "positive",
                "detail": (
                    "Consistently strong placement in federal clerkships, Big Law, and "
                    "academia (Princeton Review student surveys)."
                ),
            },
            {
                "label": "Selectivity & cost",
                "sentiment": "caution",
                "detail": (
                    "Among the most selective J.D. programs with tuition exceeding $83,000 "
                    "per year."
                ),
            },
            {
                "label": "Intense culture",
                "sentiment": "mixed",
                "detail": (
                    "Reviewers note the intellectual intensity can feel less collegial than "
                    "some peer schools."
                ),
            },
        ],
        "sources": [
            {
                "label": "ABA Journal — 2026 U.S. News law school rankings",
                "url": (
                    "https://www.abajournal.com/news/article/"
                    "stanford-tops-us-news-law-school-rankings-while-yale-slips-to-second-place"
                ),
            },
            {
                "label": "The Princeton Review — University of Chicago Law School",
                "url": "https://www.princetonreview.com/law/university-chicago--law-school-1035807",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "uchicago-md": {
        "summary": (
            "Applicants and guides describe Pritzker as a top-tier research medical school "
            "with an innovative, patient-centered curriculum and strong clinical training at "
            "UChicago Medicine — it ranked #20 among U.S. research medical schools in U.S. "
            "News's 2023 survey before withdrawing from future rankings over methodology "
            "concerns. Common cautions are extremely competitive admission, high cost of "
            "attendance in Chicago, and the intensity of the four-year professional "
            "curriculum."
        ),
        "themes": [
            {
                "label": "Research medical school",
                "sentiment": "positive",
                "detail": (
                    "Historically a top-20 U.S. research medical school with close ties to "
                    "UChicago Medicine and the Biological Sciences Division."
                ),
            },
            {
                "label": "Innovative curriculum",
                "sentiment": "positive",
                "detail": (
                    "Team-based, patient-first training with early clinical exposure through "
                    "UChicago Medicine."
                ),
            },
            {
                "label": "Clinical & research integration",
                "sentiment": "positive",
                "detail": (
                    "Access to a major academic medical center and interdisciplinary "
                    "research across the BSD."
                ),
            },
            {
                "label": "Ranking transparency",
                "sentiment": "mixed",
                "detail": (
                    "Pritzker withdrew from U.S. News medical-school rankings in 2023, "
                    "citing methodology concerns, but continues publishing admissions data."
                ),
            },
            {
                "label": "Selectivity & cost",
                "sentiment": "caution",
                "detail": (
                    "Highly selective admission with first-year tuition near $65,000 plus "
                    "Chicago living expenses."
                ),
            },
        ],
        "sources": [
            {
                "label": "Pritzker School of Medicine — U.S. News rankings withdrawal",
                "url": "https://pritzker.uchicago.edu/news/us-news-rankings",
            },
            {
                "label": "The Chicago Maroon — Pritzker withdraws from U.S. News (2023 rank #20)",
                "url": (
                    "https://chicagomaroon.com/37932/news/"
                    "pritzker-withdraws-from-u-s-news-rankings-citing-methodological-concerns/"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "uchicago-mpp": {
        "summary": (
            "Students and policy guides describe Harris's two-year MPP as a quantitative, "
            "economics-grounded program that trains data-minded policy leaders — Harris was "
            "ranked #3 in U.S. News public-policy analysis in 2022 and remains widely cited "
            "among top MPP programs alongside Harvard Kennedy, Berkeley Goldman, and "
            "Princeton SPIA. Common cautions are the program's analytical rigor (heavy "
            "econometrics and microeconomics in the core), a large cohort that can feel "
            "impersonal, and tuition in Chicago without the D.C. proximity of Georgetown."
        ),
        "themes": [
            {
                "label": "Quantitative policy training",
                "sentiment": "positive",
                "detail": (
                    "Core courses in microeconomics, econometrics, and policy analysis "
                    "ground every specialization."
                ),
            },
            {
                "label": "Top-tier reputation",
                "sentiment": "positive",
                "detail": (
                    "Harris ranked #3 in U.S. News public-policy analysis (2022) and is "
                    "consistently listed among elite MPP programs."
                ),
            },
            {
                "label": "Interdisciplinary UChicago ecosystem",
                "sentiment": "positive",
                "detail": (
                    "Joint degrees and cross-registration with Booth, Law, SSA, and the "
                    "College's public-policy major."
                ),
            },
            {
                "label": "Analytical rigor",
                "sentiment": "caution",
                "detail": (
                    "The core expects strong math and statistics; students without "
                    "quantitative preparation may struggle."
                ),
            },
            {
                "label": "Cohort scale & location",
                "sentiment": "mixed",
                "detail": (
                    "A large MPP class (~300+ students in recent cycles) and a Hyde Park "
                    "campus distant from Washington policy hubs."
                ),
            },
        ],
        "sources": [
            {
                "label": "Harris School — Master of Public Policy (MPP)",
                "url": "https://harris.uchicago.edu/academics/degrees/master-public-policy-mpp",
            },
            {
                "label": "Admit Lab — Best MPP Programs (Harris acceptance & placement data)",
                "url": "https://admit-lab.com/blog/best-mpp-programs/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "uchicago-economics-bs": {
        "summary": (
            "Students and third-party guides describe UChicago's economics major as one of "
            "the nation's most rigorous undergraduate programs — Niche ranks it #4 for "
            "Best Colleges for Economics (2026) and College Factual ranks the bachelor's "
            "#1 nationally — grounded in the Chicago School's quantitative micro, macro, "
            "and econometrics tradition with tracks in business economics, data science, and "
            "politics and policy. Common cautions are heavy calculus and theory prerequisites, "
            "large intermediate courses, and an intellectually intense Core that adds breadth "
            "beyond a purely economics track."
        ),
        "themes": [
            {
                "label": "Elite national standing",
                "sentiment": "positive",
                "detail": (
                    "Niche #4 Best Colleges for Economics (2026); College Factual #1 "
                    "bachelor's in economics nationally."
                ),
            },
            {
                "label": "Chicago School rigor",
                "sentiment": "positive",
                "detail": (
                    "Theory-forward curriculum with honors sequences and research pathways "
                    "through the Griffin Department of Economics."
                ),
            },
            {
                "label": "Career & Ph.D. placement",
                "sentiment": "positive",
                "detail": (
                    "Graduates enter finance, consulting, policy, and top economics Ph.D. "
                    "programs; the department publishes research-opportunity guidance."
                ),
            },
            {
                "label": "Quantitative prerequisites",
                "sentiment": "caution",
                "detail": (
                    "Multivariable calculus and a demanding theory core can overwhelm "
                    "students without strong math preparation."
                ),
            },
            {
                "label": "Core + course scale",
                "sentiment": "mixed",
                "detail": (
                    "UChicago's broad Core adds intellectual breadth but can compete with "
                    "economics electives; some intermediate lectures feel large."
                ),
            },
        ],
        "sources": [
            {
                "label": "Niche — Best Colleges for Economics (2026)",
                "url": "https://www.niche.com/colleges/search/best-colleges-for-economics/",
            },
            {
                "label": "Kenneth C. Griffin Department of Economics — Undergraduate",
                "url": "https://economics.uchicago.edu/undergraduate-study",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "uchicago-mpcs": {
        "summary": (
            "Students and guides describe the Master's Program in Computer Science (MPCS) as "
            "a professionally oriented, career-launching degree — Niche graduate reviewers "
            "praise its mix of academic rigor and industry-relevant projects, and the program "
            "publishes annual career-outcomes reports with strong tech placement. Common "
            "cautions are an intense workload with stacked deadlines, per-course tuition near "
            "$7,000, limited in-campus housing, and less centralized career-services support "
            "than some larger CS master's programs."
        ),
        "themes": [
            {
                "label": "Industry-oriented curriculum",
                "sentiment": "positive",
                "detail": (
                    "Courses blend theory with hands-on projects taught by faculty and "
                    "practitioners; cohorts are collaborative."
                ),
            },
            {
                "label": "Career outcomes",
                "sentiment": "positive",
                "detail": (
                    "MPCS publishes alumni career-outcomes reports; graduates enter software, "
                    "data, and product roles."
                ),
            },
            {
                "label": "Accessible to career changers",
                "sentiment": "positive",
                "detail": (
                    "The program accommodates students new to CS with immersive and "
                    "part-time formats."
                ),
            },
            {
                "label": "Workload intensity",
                "sentiment": "caution",
                "detail": (
                    "Fast-paced quarters and project deadlines can feel overwhelming, "
                    "especially for working students."
                ),
            },
            {
                "label": "Cost & career services",
                "sentiment": "mixed",
                "detail": (
                    "High per-course tuition and lighter centralized recruiting than some "
                    "peer CS master's programs."
                ),
            },
        ],
        "sources": [
            {
                "label": "MPCS — Career Outcomes Reports",
                "url": "https://masters.cs.uchicago.edu/career-services/career-outcomes-reports/",
            },
            {
                "label": "Niche — University of Chicago Graduate Reviews",
                "url": "https://www.niche.com/graduate-schools/university-of-chicago/reviews/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "uchicago-social-work-am": {
        "summary": (
            "Students and policy guides describe Crown Family School's A.M. in Social Work, "
            "Social Policy, and Social Administration as a top-tier, interdisciplinary "
            "professional degree — U.S. News ranked the school #3 nationally for social work "
            "(2024) — combining clinical practice with policy, research, and social-science "
            "theory beyond a traditional MSW. Common cautions are demanding coursework across "
            "the quarter system, the cost of a private-university graduate degree in Chicago, "
            "and an administrative pace that some students find intense."
        ),
        "themes": [
            {
                "label": "Top national rank",
                "sentiment": "positive",
                "detail": (
                    "U.S. News Best Schools for Social Work #3 (2024); CSWE-accredited since "
                    "1919."
                ),
            },
            {
                "label": "Interdisciplinary breadth",
                "sentiment": "positive",
                "detail": (
                    "The A.M. integrates direct practice with policy analysis and social-science "
                    "theory across five specialization pathways."
                ),
            },
            {
                "label": "Career flexibility",
                "sentiment": "positive",
                "detail": (
                    "Graduates pursue clinical social work, nonprofit leadership, policy, "
                    "research, and community organizing."
                ),
            },
            {
                "label": "Program intensity",
                "sentiment": "caution",
                "detail": (
                    "Rigorous coursework on UChicago's quarter calendar can feel fast-paced."
                ),
            },
            {
                "label": "Cost & administration",
                "sentiment": "mixed",
                "detail": (
                    "Private-university tuition in Chicago; some students note administrative "
                    "complexity."
                ),
            },
        ],
        "sources": [
            {
                "label": "Crown Family School — Master's in Social Work",
                "url": "https://crownschool.uchicago.edu/academic-programs/masters-social-work",
            },
            {
                "label": "U.S. News — Best Schools for Social Work",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "uchicago-molecular-engineering-bs": {
        "summary": (
            "Students and parents on College Confidential describe UChicago's Molecular "
            "Engineering major — the nation's first undergraduate program in the field — as "
            "research-rich and flexible across bioengineering, chemical engineering, and "
            "quantum tracks, with plentiful lab and internship opportunities through PME. "
            "Common cautions are that the program is not ABET-accredited (by design), is "
            "still younger than peer engineering schools, and suits students comfortable "
            "building a bespoke path within UChicago's liberal-arts Core."
        ),
        "themes": [
            {
                "label": "Research & lab access",
                "sentiment": "positive",
                "detail": (
                    "Students report early research-lab placement and industry internships; "
                    "PME emphasizes capstone projects with industry partners."
                ),
            },
            {
                "label": "Distinctive tracks",
                "sentiment": "positive",
                "detail": (
                    "Bioengineering, chemical engineering, and quantum engineering tracks "
                    "within one molecular-engineering major."
                ),
            },
            {
                "label": "Interdisciplinary UChicago setting",
                "sentiment": "positive",
                "detail": (
                    "Engineering training sits inside a rigorous liberal-arts college with "
                    "cross-registration across the university."
                ),
            },
            {
                "label": "No ABET accreditation",
                "sentiment": "caution",
                "detail": (
                    "PME deliberately forgoes ABET; students and alumni report this has not "
                    "blocked industry or graduate-school paths."
                ),
            },
            {
                "label": "Younger program scale",
                "sentiment": "mixed",
                "detail": (
                    "Smaller than long-established engineering schools; students must be "
                    "self-directed in building community and recruiting."
                ),
            },
        ],
        "sources": [
            {
                "label": "PME — Undergraduate major FAQs",
                "url": "https://pme.uchicago.edu/undergraduate-program/undergraduate-major-and-minor-faqs",
            },
            {
                "label": "College Confidential — Molecular Engineering at UChicago",
                "url": (
                    "https://talk.collegeconfidential.com/t/"
                    "molecular-engineering-reviews-and-feedback-please/3664775"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "uchicago-economics-ms": {
        "summary": (
            "Students and the department describe the one-year Master of Arts in Economics "
            "(MAE) as the only M.A. from a top-five U.S. economics department — built on "
            "Chicago's micro, macro, and econometrics core with electives across economics, "
            "Harris, and Booth. Common cautions are the program's mathematical intensity, "
            "the one-year timeline for students aiming at Ph.D. coursework, and the need to "
            "self-direct recruiting for industry roles beyond the department's placement "
            "listings."
        ),
        "themes": [
            {
                "label": "Chicago Economics pedigree",
                "sentiment": "positive",
                "detail": (
                    "Only M.A. from a top U.S. economics department; Nobel-caliber faculty "
                    "and ECMA core sequences."
                ),
            },
            {
                "label": "Flexible outcomes",
                "sentiment": "positive",
                "detail": (
                    "Graduates enter industry, policy, predoctoral research, and Ph.D. "
                    "programs; the department publishes placement data."
                ),
            },
            {
                "label": "Research pathway",
                "sentiment": "positive",
                "detail": (
                    "Research Intensive Track (RIT) option for students pursuing doctoral "
                    "coursework."
                ),
            },
            {
                "label": "Quantitative rigor",
                "sentiment": "caution",
                "detail": (
                    "Math camp and graduate theory expect strong preparation in calculus and "
                    "statistics."
                ),
            },
            {
                "label": "One-year pace",
                "sentiment": "mixed",
                "detail": (
                    "The compressed timeline can limit depth for students pivoting from "
                    "non-quantitative backgrounds."
                ),
            },
        ],
        "sources": [
            {
                "label": "Kenneth C. Griffin Department of Economics — MAE",
                "url": "https://economics.uchicago.edu/masters-programs/master-arts-economics",
            },
            {
                "label": "Economics — Placement and Outcomes",
                "url": "https://economics.uchicago.edu/masters-programs/placement-and-outcomes",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "uchicago-film-video-and-photographic-arts-bs": {
        "summary": (
            "Students and film-school guides describe UChicago's Cinema and Media Studies "
            "major as intellectually rigorous and theory-forward — FilmSchool.org reviewers "
            "rate the department highly for coursework and professors — with optional "
            "production-thesis tracks and student-led filmmaking through Fire Escape Films. "
            "Common cautions are that the program emphasizes critical history and theory "
            "over hands-on production training, the overall UChicago workload is intense, "
            "and practical filmmaking often requires joining campus organizations."
        ),
        "themes": [
            {
                "label": "Theory & history depth",
                "sentiment": "positive",
                "detail": (
                    "Core cinema-history sequence and advanced seminars prepare students for "
                    "graduate study and critical analysis."
                ),
            },
            {
                "label": "Production pathways",
                "sentiment": "positive",
                "detail": (
                    "Intensive production-thesis track and student organizations (e.g., Fire "
                    "Escape Films) provide filmmaking experience."
                ),
            },
            {
                "label": "Interdisciplinary campus",
                "sentiment": "positive",
                "detail": (
                    "CMS sits within UChicago's humanities ecosystem with cross-registration "
                    "and joint-thesis options."
                ),
            },
            {
                "label": "Limited formal production",
                "sentiment": "caution",
                "detail": (
                    "Applicants seeking a primarily hands-on film school may find the "
                    "curriculum analysis-heavy compared with conservatory programs."
                ),
            },
            {
                "label": "Academic intensity",
                "sentiment": "mixed",
                "detail": (
                    "Reviewers note UChicago's demanding Core and quarter pace alongside CMS "
                    "coursework."
                ),
            },
        ],
        "sources": [
            {
                "label": "Cinema and Media Studies — Undergraduate major",
                "url": (
                    "https://cms.uchicago.edu/undergraduate/"
                    "why-study-cinema-and-media-studies/major-cinema-and-media-studies"
                ),
            },
            {
                "label": "FilmSchool.org — UChicago Cinema and Media Studies reviews",
                "url": (
                    "https://www.filmschool.org/reviews/"
                    "university-of-chicago-department-of-cinema-and-media-studies.211/reviews"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "uchicago-film-video-and-photographic-arts-ms": {
        "summary": (
            "Graduate students and departmental materials describe UChicago's cinema and "
            "media graduate work — centered in the Department of Cinema and Media Studies "
            "within the Division of the Humanities — as research-intensive and "
            "interdisciplinary, with strengths in film history, theory, and media "
            "archaeology rather than vocational production training. Common cautions are "
            "small cohorts, the academic job market for film studies, and the need to "
            "self-build production experience if pursuing industry roles."
        ),
        "themes": [
            {
                "label": "Research reputation",
                "sentiment": "positive",
                "detail": (
                    "Faculty and graduate students are known for rigorous scholarship in "
                    "film history, theory, and media studies."
                ),
            },
            {
                "label": "Humanities integration",
                "sentiment": "positive",
                "detail": (
                    "Graduate work connects to art history, literature, and interdisciplinary "
                    "centers across the Division of the Humanities."
                ),
            },
            {
                "label": "Academic placement",
                "sentiment": "positive",
                "detail": (
                    "The program prepares students for doctoral study and academic careers "
                    "in cinema and media fields."
                ),
            },
            {
                "label": "Industry orientation",
                "sentiment": "caution",
                "detail": (
                    "The curriculum is scholarly rather than a vocational film-production "
                    "master's."
                ),
            },
            {
                "label": "Cohort scale",
                "sentiment": "mixed",
                "detail": (
                    "Small graduate community offers close faculty access but fewer peer "
                    "resources than large film schools."
                ),
            },
        ],
        "sources": [
            {
                "label": "Cinema and Media Studies — Department home",
                "url": "https://cms.uchicago.edu/",
            },
            {
                "label": "FilmSchool.org — UChicago Cinema and Media Studies",
                "url": (
                    "https://www.filmschool.org/reviews/"
                    "university-of-chicago-department-of-cinema-and-media-studies.211/"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "uchicago-divinity-mdiv": {
        "summary": (
            "Students and accreditors describe the Divinity School's three-year Master of "
            "Divinity as a cohort-based program combining religious-studies coursework, "
            "field education, and leadership formation — the school is accredited by the "
            "Association of Theological Schools (ATS) and publishes MDiv placement outcomes. "
            "Common cautions are demanding writing and language requirements, limited Niche "
            "review volume, and some student notes of administrative disorganization "
            "alongside strong faculty mentorship."
        ),
        "themes": [
            {
                "label": "ATS accreditation",
                "sentiment": "positive",
                "detail": (
                    "The MDiv is accredited by the Commission on Accrediting of ATS; the "
                    "school publishes placement summaries."
                ),
            },
            {
                "label": "Field education",
                "sentiment": "positive",
                "detail": (
                    "Three-year curriculum integrates community engagement and supervised "
                    "ministry placements."
                ),
            },
            {
                "label": "Interdisciplinary study",
                "sentiment": "positive",
                "detail": (
                    "MDiv students cross-register across the university's divisions while "
                    "grounding work in religious leadership."
                ),
            },
            {
                "label": "Administrative pace",
                "sentiment": "caution",
                "detail": (
                    "Graduate reviewers occasionally note administrative complexity on the "
                    "quarter calendar."
                ),
            },
            {
                "label": "Niche visibility",
                "sentiment": "mixed",
                "detail": (
                    "Public third-party review volume is small compared with larger divinity "
                    "schools."
                ),
            },
        ],
        "sources": [
            {
                "label": "UChicago Divinity School — MDiv Program",
                "url": "https://divinity.uchicago.edu/MDivprogram",
            },
            {
                "label": "Niche — University of Chicago Divinity School",
                "url": "https://www.niche.com/graduate-schools/university-of-chicago-divinity-school/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
}

# ── Application requirements ─────────────────────────────────────────────────
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission.",
}
# Undergraduate (the College) admission via the Common Application, Coalition (Scoir) or
# QuestBridge. UChicago is permanently test-optional and applies a "no harm" policy to
# any submitted SAT/ACT scores.
_REQ_UNDERGRAD = {
    "materials": [
        {
            "name": "Common Application, Coalition Application (Scoir) or QuestBridge",
            "required": True,
        },
        {"name": "UChicago-specific supplement (the 'Uncommon' essays)", "required": True},
        {"name": "Secondary-school transcript", "required": True},
        {"name": "Counselor recommendation", "required": True},
        {"name": "Two teacher evaluations", "required": True},
        {
            "name": "Application fee (waived for applicants for need-based financial aid)",
            "required": True,
        },
        {
            "name": "Standardized test scores",
            "required": False,
            "note": (
                "UChicago is permanently test-optional; the SAT or ACT is not required, and "
                "a submitted score is reviewed only when it strengthens an application "
                "('no harm' policy)."
            ),
        },
    ],
    "deadlines": [
        {"round": "Early Action / Early Decision I", "date": "November 3"},
        {"round": "Early Decision II / Regular Decision", "date": "January 5"},
    ],
    "recommendations": {
        "required": 3,
        "note": "One counselor recommendation plus two teacher evaluations.",
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "Duolingo English Test"],
            "required": False,
            "note": "English-proficiency proof may be required for non-native speakers.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "UChicago College Admissions — Apply",
                "url": "https://collegeadmissions.uchicago.edu/apply",
            }
        ],
    },
    "source": "University of Chicago College Admissions",
    "source_url": "https://collegeadmissions.uchicago.edu/apply",
}

# Graduate (Booth Full-Time MBA) admission via the Booth application.
_REQ_MBA = {
    "materials": [
        {"name": "Chicago Booth online application", "required": True},
        {"name": "Essays (per the current Booth prompts)", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Two letters of recommendation", "required": True},
        {"name": "Resume", "required": True},
        {
            "name": "GMAT or GRE scores",
            "required": True,
            "note": (
                "Booth accepts the GMAT or GRE; a test score is required for the Full-Time MBA."
            ),
        },
        {"name": "Interview (by invitation only)", "required": False},
        {"name": "$250 application fee (fee waivers available)", "required": True},
    ],
    "deadlines": [
        {"round": "Round 1", "date": "September 16, 2025"},
        {"round": "Round 2", "date": "January 6, 2026"},
        {"round": "Round 3", "date": "April 2, 2026"},
    ],
    "recommendations": {
        "required": 2,
        "note": "Two letters of recommendation submitted through the Booth application.",
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "PTE"],
            "required": True,
            "note": (
                "An English-proficiency test is required for applicants whose first "
                "language is not English (waivers may apply)."
            ),
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Chicago Booth — Full-Time MBA Admissions",
                "url": "https://www.chicagobooth.edu/mba/full-time/admissions",
            }
        ],
    },
    "source": "Chicago Booth — Full-Time MBA Admissions",
    "source_url": "https://www.chicagobooth.edu/mba/full-time/admissions",
}

# Generic UChicago graduate / professional admission set. Each professional school and
# Division administers its own admissions; the materials below are common across UChicago
# graduate and professional programs, and deadlines vary by program — applicants are
# pointed to the program's own admissions page via the program website.
_REQ_GRAD_GENERIC = {
    "materials": [
        {"name": "Program online application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose / personal statement", "required": True},
        {"name": "Resume / CV", "required": True},
        {
            "name": "Letters of recommendation",
            "required": True,
            "note": (
                "Most UChicago graduate and professional programs require two to three letters."
            ),
        },
        {
            "name": "Standardized test scores",
            "required": False,
            "note": (
                "Test requirements vary by program — the J.D. requires the LSAT or GRE and "
                "the M.D. requires the MCAT, while many master's programs are test-optional."
            ),
        },
    ],
    "deadlines": [
        {"round": "Application deadline", "date": "Varies by program — see the program page"},
    ],
    "recommendations": {
        "required": 3,
        "note": (
            "Most UChicago graduate and professional programs require two to three letters "
            "of recommendation."
        ),
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": True,
            "note": (
                "Required for applicants whose native language is not English; an "
                "exemption applies to degrees earned where English is the language of "
                "instruction."
            ),
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "UChicagoGRAD — Guidelines and Deadlines",
                "url": "https://grad.uchicago.edu/admissions/apply/guidelines-and-deadlines/",
            }
        ],
    },
    "source": "University of Chicago graduate & professional admissions",
    "source_url": "https://grad.uchicago.edu/admissions/apply/guidelines-and-deadlines/",
}


def _requirements_for(spec: dict) -> dict:
    """Pick the admissions requirement set for a program by slug / degree type."""
    if spec["slug"] == "uchicago-mba":
        return dict(_REQ_MBA)
    if spec["degree_type"] in ("masters", "professional"):
        return dict(_REQ_GRAD_GENERIC)
    return dict(_REQ_UNDERGRAD)


# Real UChicago campus photo (the Main Quadrangles) — Wikimedia Commons, hotlinkable
# landscape JPG (verified HTTP 200). Leads the institution hero; see
# ``SCHOOL_OUTCOMES["campus_photos"]`` for gallery.
_CAMPUS_PHOTO = SCHOOL_OUTCOMES["campus_photos"][0]["url"]


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich UChicago to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when UChicago is absent — safe on fresh/CI databases.
    """
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    # Shallow-merge JSONB: every sub-object we provide is complete.
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    # Drop any stale value for a path we explicitly declare omitted, so the merge can't
    # keep serving a figure the enrichment run refused to assert.
    for _path in _OMITTED_INSTITUTION:
        if _path.startswith("school_outcomes."):
            rest = _path.split(".", 1)[1]
            if "." not in rest:
                school_outcomes.pop(rest, None)
            else:
                head, leaf = rest.split(".", 1)
                if isinstance(school_outcomes.get(head), dict):
                    school_outcomes[head].pop(leaf, None)
    school_outcomes["_standard"] = _standard(_OMITTED_INSTITUTION)
    inst.school_outcomes = school_outcomes
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    inst.founded_year = 1890
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.uchicago.edu"
    # Lead the gallery with a real campus photo (dedupe + prepend; idempotent).
    _gallery = [u for u in (inst.media_gallery or []) if u != _CAMPUS_PHOTO]
    inst.media_gallery = [_CAMPUS_PHOTO, *_gallery]
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
        spec = _SPEC_BY_SLUG[slug]
    omitted: list[str] = []
    # The Booth MBA carries its own employment-report outcomes; every other program uses
    # the federal Field-of-Study one-year earnings, which publishes neither a program
    # employment rate nor a top-industries breakdown — so those omit them.
    if slug != "uchicago-mba":
        omitted += [
            "outcomes_data.employment_rate",
            "outcomes_data.top_industries",
        ]
    else:
        # Booth reports placement qualitatively (no single first-party employment %), so
        # the numeric employment_rate is omitted even for the flagship.
        omitted.append("outcomes_data.employment_rate")
    if spec["degree_type"] != "bachelors" and slug not in _COST_BY_SLUG:
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
        p.program_name = _FULL_NAME_BY_SLUG.get(slug) or spec["program_name"]
        p.degree_type = spec["degree_type"]
        p.duration_months = spec.get("duration_months")
        p.description_text = spec["description"]
        # Website: verified program/department page where available, else the owning
        # school's site.
        p.website_url = _WEBSITE_BY_SLUG.get(slug) or _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.department = spec.get("department")
        p.is_published = True
        p.catalog_source = "curated"
        # Persist the curated CIP so the matching feature path (program_features
        # featurize_program → cip_code) gets the CIP-family signal; already in the
        # normalized 4-digit dotted form (e.g. "45.06").
        p.cip_code = spec.get("cip")
        p.delivery_format = spec.get("delivery_format", "in_person")
        p.content_sources = _BOOTH_CONTENT if slug == "uchicago-mba" else _program_content(spec)
        # Cost: verified per-program tuition where available; undergraduate uses the
        # published College rates; tuition-omitted graduate programs carry the bursar
        # source without a figure.
        cost_override = _COST_BY_SLUG.get(slug)
        if cost_override is not None:
            p.tuition = cost_override.get("tuition_usd")
            p.cost_data = dict(cost_override)
        elif spec["degree_type"] == "bachelors":
            p.tuition = _TUITION_UG
            p.cost_data = {
                "tuition_usd": _TUITION_UG,
                "total_cost_of_attendance": _UNDERGRAD_COA,
                "avg_net_price": _AVG_NET_PRICE,
                "breakdown": {
                    "tuition": _TUITION_UG,
                    "total_cost_of_attendance": _UNDERGRAD_COA,
                },
                "funded": False,
                "note": (
                    "Published 2025-26 College tuition with the College Scorecard cost of "
                    "attendance and average net price. UChicago is need-blind for domestic "
                    "applicants and meets 100% of demonstrated need with grants rather than "
                    "loans (No Barriers), so most families pay far less than the sticker "
                    "price (average net price ≈ $14,900); families earning under $125,000 "
                    "pay no tuition."
                ),
                "source": (
                    "University of Chicago CDS 2024-25 (tuition) + College Scorecard "
                    "(UNITID 144050)"
                ),
                "source_url": "https://collegescorecard.ed.gov/school/?144050",
                "year": "2025-26",
            }
        elif slug in _COST_OMITTED_SLUGS:
            p.tuition = None
            p.cost_data = dict(_COST_OMITTED_RECORD)
        else:
            p.tuition = None
            p.cost_data = {
                "funded": spec["degree_type"] == "phd",
                "note": (
                    "UChicago does not publish a single citable per-program tuition for this "
                    "degree on a public page; see the program website for current tuition."
                    + (
                        " Doctoral students are typically funded via fellowships or "
                        "assistantships when admitted."
                        if spec["degree_type"] == "phd"
                        else ""
                    )
                ),
                "source": "University of Chicago program website",
                "source_url": _WEBSITE_BY_SLUG.get(slug) or _SCHOOL_WEBSITE.get(spec["school"]),
            }
        # Admissions: undergraduate, MBA or generic graduate set by slug / degree type.
        p.application_requirements = _requirements_for(spec)
        # Outcomes precedence: Booth employment report (flagship) → Scorecard FOS
        # (program) → institution median.
        if slug == "uchicago-mba":
            outcomes = dict(_MBA_OUTCOMES)
        else:
            fos = _FOS_OUTCOMES.get(slug)
            if fos is not None:
                salary, cip = fos
                outcomes = {
                    "median_salary": salary,
                    "scope": "program",
                    "cip": cip,
                    "earnings_timeframe": "median earnings 1 year after completion",
                    "conditions": _FOS_CONDITIONS_BY_SLUG.get(slug, _FOS_CONDITIONS),
                    "source": "U.S. Dept. of Education College Scorecard — Field of Study",
                    "source_url": "https://collegescorecard.ed.gov/school/?144050",
                }
            else:
                outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        if spec["degree_type"] in ("masters", "professional"):
            p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_GRAD_BASELINE
            p.highlights = _HL_BY_SLUG.get(slug) or _HL_GRAD_BASELINE
        else:
            p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_BASELINE
            p.highlights = _HL_BY_SLUG.get(slug) or _HL_BASELINE
        # Always assign so a stale value on a pre-existing row is cleared (tracks is
        # recorded as omitted where unverified, and match_service reads program.tracks).
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        # Application deadline (upcoming): Booth Round 1, else undergraduate RD.
        p.application_deadline = date(2026, 9, 16) if slug == "uchicago-mba" else date(2027, 1, 5)
    session.flush()
    # Reconcile legacy UChicago programs (slug not in the canonical set): delete when
    # unreferenced, otherwise unpublish so the catalog stays clean without breaking any
    # application/match rows that point at them.
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
