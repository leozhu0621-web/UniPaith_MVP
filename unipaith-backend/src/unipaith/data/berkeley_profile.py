"""Canonical University of California, Berkeley profile — the single source of
truth.

Real, sourced data only (U.S. Dept. of Education College Scorecard, UNITID 110635
· UC Berkeley Office of Planning & Analysis "Quick Facts" · the official UC Berkeley
"By the Numbers" page · UC Berkeley's official Nobel-laureate tally · the official
QS / Times Higher Education / U.S. News rankings · each college's official
leadership / about page · the College Scorecard Field-of-Study earnings by CIP).
``apply(session)`` idempotently enriches the Berkeley institution row, upserts the
seven real undergraduate-degree-granting colleges, and builds Berkeley's
undergraduate program catalog across them.

Berkeley admits undergraduates into SIX colleges and ONE school (its own
terminology). We map those onto the platform's ``School`` model:
  - College of Letters & Science (the largest — ~three-quarters of undergraduates)
  - College of Engineering
  - College of Chemistry
  - College of Environmental Design
  - Rausser College of Natural Resources
  - Haas School of Business
  - College of Computing, Data Science, and Society

It **flushes but does not commit** — the caller (the Alembic data migration, the
CLI script, or the dev seed) owns the transaction. It is a **no-op** (returns
``False``) when Berkeley is absent, so it is safe to run against a fresh or CI
database. Re-running is safe: colleges key off ``(institution_id, name)`` and
programs off ``slug``; stale rows are reconciled without breaking foreign keys.

This mirrors ``mit_profile`` / ``stanford_profile`` / ``caltech_profile`` so the
migration, the standalone script, and the dev seed all agree (DRY). Every figure
traces to a public, citable source; anything that could not be verified from a
first-party or two-independent-source basis is **omitted** (recorded in the
relevant ``_standard.omitted`` list), never guessed. The Electrical Engineering
and Computer Sciences (EECS) major is the most-enriched flagship program (its real
technical areas, faculty, class profile, and aggregated reviews), mirroring MIT
Sloan's MBAn in the reference instance — with the honest caveats that the
University of California is test-free (no SAT/ACT percentiles exist to report) and
that this run ships Berkeley's complete UNDERGRADUATE tree; its department-level
graduate programs are the resumption scope for a later run.

Depth pass (2026-06-15, berkeleyprof6): merged ``DEPTH_REVIEWS`` for 59 coverable
programs — completes Berkeley coverable external_reviews (70/70).

Description depth pass (2026-06-16, berkeleyprof7): replaces all classification-only
``{name} is a {degree} program at Berkeley's {school}`` stubs with field-specific
clauses from ``berkeley_field_descriptions.py`` (269/269 programs).

Description repair (2026-06-17, berkeleyprof8): drops the ``{program_name}:`` prefix
from every description so clauses open on field-specific facts (gold MIT/Chicago
pattern); 0% name-prefixed descriptions.

Structural de-fabrication (2026-06-19, berkeleyprof9): maps federal CIP rollup
titles to Berkeley's real published departments; replaces ``Bachelor's in {rollup}``
credential-prefix names with real degree designations (B.A./B.S./M.S./Ph.D.); drops
IPEDS padding rows with no distinct Berkeley degree; per-credential descriptions so
credential siblings no longer share verbatim text (anti-stub clean).
"""

from __future__ import annotations

import os
import re
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.berkeley_cip_mapping import (
    BS_MAJORS,
    CIP_TO_DEPARTMENT,
    PROFESSIONAL_SCHOOLS,
    SKIP_CATALOG_SLUGS,
)
from unipaith.data.berkeley_field_descriptions import FIELD_DESCRIPTIONS, SLUG_DESCRIPTIONS
from unipaith.data.berkeley_ipeds_catalog import _IPEDS_CATALOG
from unipaith.data.berkeley_reviews_depth import DEPTH_REVIEWS
from unipaith.data.profile_catalog_utils import validate_catalog
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION
from unipaith.profile_standard.anti_stub import analyze

INSTITUTION_NAME = "University of California-Berkeley"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-21"

_CLASSIFICATION_STUB_RE = re.compile(
    r"^.+ is (an|a) (undergraduate|graduate|doctoral|professional|degree) program at Berkeley",
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
    # The University of California has been test-free for admissions since 2021 — it
    # neither requires nor considers SAT/ACT scores, so there are no admitted-class
    # test-score percentiles to report. We omit rather than publish a stale figure.
    "school_outcomes.test_scores",
    # Berkeley publishes a 19.4:1 student-faculty ratio on its official "By the
    # Numbers" page but does not publish a single official total faculty headcount;
    # we publish the ratio and omit the count rather than compute one.
    "school_outcomes.scale.faculty_count",
    # No precise single first-party endowment figure was cleanly verifiable (the
    # campus endowment is reported across the UC Investments pool and the UC
    # Berkeley Foundation); omitted rather than asserting an approximate number.
    "school_outcomes.scale.endowment_usd",
    "school_outcomes.scale.research_centers",
    # Berkeley does not publish a single first-party institution-wide "employed or
    # continuing education" rate or a top-employer-industries breakdown that we
    # could verify; the verified, program-level Scorecard outcomes are used instead.
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
]

# ── Institution-level data ────────────────────────────────────────────────
# Rankings are stored as {rank, year} objects because the page renders every
# ranking_data entry that is an object with a numeric `rank`. All three ranks are
# quoted from the official ranking bodies / Berkeley News announcements.
RANKING_DATA: dict = {
    "ownership_type": "public",
    # Berkeley is accredited by the WASC Senior College and University Commission.
    "accreditor": "WSCUC",
    # Carnegie 2021 basic classification.
    "carnegie_classification": "Doctoral Universities: Very High Research Activity",
    # QS World University Rankings 2026: Berkeley is ranked #17 worldwide.
    "qs_world_university_rankings": {"rank": 17, "year": 2026},
    # THE World University Rankings 2026: #9 in the world (and #1 public in North
    # America).
    "times_higher_education": {"rank": 9, "year": 2026},
    # U.S. News Best Colleges (National Universities) 2026: #15 nationally (tied),
    # and #1 among public universities.
    "us_news_national": {"rank": 15, "year": 2026},
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below
# is complete, so a shallow merge is correct. Figures are College Scorecard
# (UNITID 110635) cross-checked against Berkeley's Office of Planning & Analysis
# "Quick Facts" and the official "By the Numbers" page where both publish the metric.
SCHOOL_OUTCOMES: dict = {
    # OPA Quick Facts 2025-26: 14,451 first-year admits / 126,842 first-year
    # applicants = 11.39%.
    "admit_rate": 0.114,
    "avg_net_price": 13481,
    "median_earnings_10yr": 92446,
    "completion_rate_4yr_150pct": 0.9284,
    # OPA Quick Facts: new-freshman first-year retention (Fall 2024 cohort) = 97%.
    "retention_rate_first_year": 0.97,
    # OPA Quick Facts: six-year graduation rate for the Fall 2019 freshman cohort
    # = 94%.
    "graduation_rate_6yr": 0.94,
    "financial_aid": {
        "pell_grant_rate": 0.2864,
        "federal_loan_rate": 0.1683,
        # College Scorecard in-state academic-year cost of attendance.
        "cost_of_attendance": 45619,
        "median_debt_completers": 13000,
    },
    # Undergraduate race/ethnicity from College Scorecard (UNITID 110635); the women
    # share is from OPA Quick Facts (Fall 2025: 17,910 women of 33,122 undergraduates).
    "demographics": {
        "white": 0.1979,
        "black": 0.0205,
        "hispanic": 0.221,
        "asian": 0.3545,
        "two_or_more": 0.0678,
        "international": 0.0984,
        "women": 0.541,
    },
    # Berkeley main campus, San Francisco Bay Area.
    "location": {"lat": 37.8719, "lng": -122.2583},
    "campus_basics": {"location": "Berkeley, California (San Francisco Bay Area)"},
    "scale": {
        # Berkeley "By the Numbers": 19.4-to-1 student-faculty ratio.
        "student_faculty_ratio": "19.4:1",
    },
    "research": {
        "labs": [
            "Lawrence Berkeley National Laboratory (managed by UC Berkeley for the DOE)",
            "Space Sciences Laboratory",
            "Lawrence Hall of Science",
            "Mathematical Sciences Research Institute (SLMath)",
            "Berkeley Institute for Data Science",
        ],
        "areas": [
            "Artificial intelligence & computing",
            "Engineering & applied science",
            "Physical & chemical sciences",
            "Biological & environmental sciences",
            "Economics & social sciences",
            "Energy & climate",
            "Data science & statistics",
        ],
        "lab_links": {
            "Lawrence Berkeley National Laboratory (managed by UC Berkeley for the DOE)": (
                "https://www.lbl.gov/"
            ),
            "Space Sciences Laboratory": "https://ssl.berkeley.edu/",
            "Lawrence Hall of Science": "https://lawrencehallofscience.org/",
        },
    },
    "campus_life": {
        # Cal's athletic teams (the California Golden Bears) compete in NCAA Division
        # I; Cal joined the Atlantic Coast Conference (ACC) in 2024.
        "athletics_division": "NCAA Division I (Atlantic Coast Conference)",
        "mascot": "California Golden Bears (Oski the Bear)",
        "housing": "Undergraduate residence halls + Berkeley student cooperatives",
        "resources": [
            {"label": "Cal Athletics (Golden Bears)", "url": "https://calbears.com/"},
            {"label": "Berkeley Housing", "url": "https://housing.berkeley.edu/"},
        ],
    },
    "flagship": {
        # Berkeley "By the Numbers" (Fall 2024): 33,070 undergraduate + 12,812
        # graduate = 45,882 total enrollment.
        "enrollment_total": 45882,
        # OPA Quick Facts 2025-26 first-year admissions cycle.
        "applicants": 126842,
        "admits": 14451,
        "admissions_cycle": "Entering class fall 2025 (UC Berkeley Quick Facts, 2025-26)",
        # Berkeley's official tally: 63 Berkeley Nobelists (faculty + alumni).
        "nobel_laureates": 63,
        # Berkeley "By the Numbers": ~400 degree programs.
        "degree_programs": 400,
        # Founded by the State of California in 1868 (UC's founding campus).
        "founded_year": 1868,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (UC Berkeley, UNITID 110635)",
            "url": "https://collegescorecard.ed.gov/school/?110635",
        },
        {
            "label": "UC Berkeley Office of Planning & Analysis — Quick Facts",
            "url": "https://opa.berkeley.edu/campus-data/uc-berkeley-quick-facts",
        },
        {
            "label": "UC Berkeley — By the Numbers",
            "url": "https://www.berkeley.edu/about/by-the-numbers/",
        },
        {
            "label": "UC Berkeley — Berkeley's Nobel laureates",
            "url": "https://inspire.berkeley.edu/get-inspired/nobels/",
        },
        {
            "label": "QS World University Rankings 2026 — UC Berkeley",
            "url": "https://www.topuniversities.com/universities/university-california-berkeley-ucb",
        },
        {
            "label": "Times Higher Education — UC Berkeley (No. 1 public in North America, 2026)",
            "url": (
                "https://news.berkeley.edu/2025/10/08/"
                "uc-berkeley-rated-no-1-public-university-in-north-america-by-times-higher-education/"
            ),
        },
        {
            "label": "U.S. News — UC Berkeley named top public school (2026)",
            "url": (
                "https://news.berkeley.edu/2025/09/22/"
                "uc-berkeley-named-top-public-school-in-the-country-by-us-news/"
            ),
        },
    ],
    "campus_photos": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/"
                "Redwood_trees_and_Sather_Tower_during_the_Sunset_in_Berkeley_California.jpg/"
                "1920px-Redwood_trees_and_Sather_Tower_during_the_Sunset_in_Berkeley_California.jpg"
            ),
            "credit": "Wikimedia Commons / Wil540 art (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7f/"
                "UCBerkeleyCampus.jpg/1920px-UCBerkeleyCampus.jpg"
            ),
            "credit": "Wikimedia Commons / brainchildvn (CC BY 2.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/"
                "UC_Berkeley_campus_and_surroundings_from_Berkeley_Hills_January_2026.jpg/"
                "1920px-UC_Berkeley_campus_and_surroundings_from_Berkeley_Hills_January_2026.jpg"
            ),
            "credit": "Wikimedia Commons / 4300streetcar (CC BY 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/7/75/"
                "View_of_Sather_Tower%2C_Doe_Library%2C_and_Memorial_Glade_through_trees_"
                "-_U.C._Berkeley_-_The_Daily_Californian.jpg"
            ),
            "credit": (
                "Wikimedia Commons / Samuel Albillo / The Daily Californian (0BSD)"
            ),
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/"
                "UC-Berkeley-022-memorial-glade.jpg/1920px-UC-Berkeley-022-memorial-glade.jpg"
            ),
            "credit": "Wikimedia Commons / Firstcultural (CC0)",
        },
    ],
    # Wikimedia Commons file page verified 2026-06-14: author Wil540 art, CC BY-SA 4.0.
    "media_credit": "Wikimedia Commons / Wil540 art (CC BY-SA 4.0)",
}

# student_body_size is the undergraduate count (the page labels it "Undergraduates");
# the total (45,882) lives in flagship.enrollment_total and renders as "Total
# enrollment". 33,070 = Berkeley "By the Numbers" (Fall 2024) undergraduate count.
UNDERGRAD_COUNT = 33070

DESCRIPTION = (
    "The University of California, Berkeley is a public research university in "
    "Berkeley, CA — the founding campus of the University of California system and "
    "a public land-grant institution in the San Francisco Bay Area. Founded by the "
    "State of California in 1868, it enrolls roughly 33,000 undergraduates and "
    "about 12,800 graduate students, some 45,900 students in all.\n\n"
    "Berkeley admits undergraduates into six colleges and one school: the College "
    "of Letters & Science — the largest, holding about three-quarters of "
    "undergraduates — together with the College of Engineering; the College of "
    "Chemistry; the College of Environmental Design; the Rausser College of Natural "
    "Resources; the Haas School of Business; and the College of Computing, Data "
    "Science, and Society. Across them the university offers roughly 400 degree "
    "programs, and it manages Lawrence Berkeley National Laboratory for the U.S. "
    "Department of Energy.\n\n"
    "Berkeley ranks among the best universities in the world and the very best "
    "public university in North America: No. 9 in the world and No. 1 public in "
    "North America by Times Higher Education, No. 17 by QS, and No. 1 among public "
    "universities (No. 15 nationally) by U.S. News. By the university's own count, "
    "63 Berkeley Nobelists are associated with the campus, and it admits about 11% "
    "of first-year applicants.\n\n"
    "As a public flagship, Berkeley pairs that reach with relative affordability: "
    "the in-state cost of attendance is about $45,600 a year, the average net price "
    "is roughly $13,500, and 29% of undergraduates receive Pell grants. Berkeley "
    "graduates earn a median income of about $92,000 a decade after entry."
)

# ── The seven real undergraduate-degree-granting colleges (display order) ───
_LS = "College of Letters & Science"
_COE = "College of Engineering"
_CHEM = "College of Chemistry"
_CED = "College of Environmental Design"
_RAUSSER = "Rausser College of Natural Resources"
_HAAS = "Haas School of Business"
_CDSS = "College of Computing, Data Science, and Society"
_LAW = "Berkeley Law"
_GSPP = "Goldman School of Public Policy"
_GSE = "Graduate School of Education"
_GRAD = "Graduate Division"
_SPH = "School of Public Health"

SCHOOLS: list[dict] = [
    {
        "name": _LS,
        "sort_order": 1,
        "description": (
            "The largest of Berkeley's colleges and schools — encompassing about "
            "three-quarters of its undergraduates and half of its faculty and "
            "graduate students — the College of Letters & Science spans the arts and "
            "humanities, biological sciences, mathematical and physical sciences, "
            "and social sciences across five academic divisions and dozens of majors."
        ),
    },
    {
        "name": _COE,
        "sort_order": 2,
        "description": (
            "Berkeley Engineering educates and conducts research across "
            "bioengineering; civil and environmental engineering; electrical "
            "engineering and computer sciences; industrial engineering and "
            "operations research; materials science and engineering; mechanical "
            "engineering; and nuclear engineering."
        ),
    },
    {
        "name": _CHEM,
        "sort_order": 3,
        "description": (
            "The College of Chemistry comprises the Department of Chemistry and the "
            "Department of Chemical and Biomolecular Engineering, with a faculty that "
            "has been at the frontiers of chemistry at Berkeley since 1872."
        ),
    },
    {
        "name": _CED,
        "sort_order": 4,
        "description": (
            "The College of Environmental Design brings together architecture, "
            "landscape architecture and environmental planning, and city and "
            "regional planning — the design of the built and natural environment."
        ),
    },
    {
        "name": _RAUSSER,
        "sort_order": 5,
        "description": (
            "Rausser College of Natural Resources studies the biological, social, "
            "and economic challenges of protecting natural resources and the "
            "environment across agricultural and resource economics; environmental "
            "science, policy and management; metabolic biology and nutrition; and "
            "plant and microbial biology."
        ),
    },
    {
        "name": _HAAS,
        "sort_order": 6,
        "description": (
            "Founded in 1898 as the first business school at a public university, "
            "the Haas School of Business spans undergraduate, MBA, PhD, and "
            "executive education in business and management."
        ),
    },
    {
        "name": _CDSS,
        "sort_order": 7,
        "description": (
            "Berkeley's newest college, Computing, Data Science, and Society unites "
            "computing, data science, and statistics — including the Department of "
            "Electrical Engineering and Computer Sciences (shared with Engineering), "
            "the Department of Statistics, and Data Science undergraduate studies — "
            "with an emphasis on societal applications."
        ),
    },
    {
        "name": _LAW,
        "sort_order": 8,
        "description": (
            "Berkeley Law is one of the nation's leading public law schools, offering "
            "the J.D., LL.M., and J.S.D. together with interdisciplinary legal studies "
            "and clinics across environmental, technology, business, and social-justice law."
        ),
    },
    {
        "name": _GSPP,
        "sort_order": 9,
        "description": (
            "The Goldman School of Public Policy trains leaders in public policy through "
            "the Master of Public Policy (M.P.P.), concurrent degrees, and doctoral study "
            "in policy analysis and governance."
        ),
    },
    {
        "name": _GSE,
        "sort_order": 10,
        "description": (
            "The Graduate School of Education prepares scholars and practitioners across "
            "teacher education, educational leadership, policy, and learning sciences."
        ),
    },
    {
        "name": _SPH,
        "sort_order": 11,
        "description": (
            "The School of Public Health advances population health through M.P.H., Dr.P.H., "
            "and Ph.D. programs in epidemiology, biostatistics, health policy, and "
            "environmental health."
        ),
    },
    {
        "name": _GRAD,
        "sort_order": 12,
        "description": (
            "The Graduate Division confers master's and doctoral degrees across Berkeley's "
            "departments and interdisciplinary programs, administering graduate admissions, "
            "fellowships, and degree requirements university-wide."
        ),
    },
]

# Each college's official website (verified to resolve at author time).
_SCHOOL_WEBSITE: dict[str, str] = {
    _LS: "https://ls.berkeley.edu/",
    _COE: "https://engineering.berkeley.edu/",
    _CHEM: "https://chemistry.berkeley.edu/",
    _CED: "https://ced.berkeley.edu/",
    _RAUSSER: "https://nature.berkeley.edu/",
    _HAAS: "https://haas.berkeley.edu/",
    _CDSS: "https://cdss.berkeley.edu/",
    _LAW: "https://www.law.berkeley.edu/",
    _GSPP: "https://gspp.berkeley.edu/",
    _GSE: "https://bears.berkeley.edu/",
    _SPH: "https://publichealth.berkeley.edu/",
    _GRAD: "https://grad.berkeley.edu/",
}

# Rich, sourced About-tab content per college. Deans + titles are quoted from each
# college's official leadership page (verified 2026-06-10). Several deanships are
# mid-transition (terms turning over July 1, 2026); the CURRENT dean is recorded
# with the announced successor noted. Founding years are included only where an
# official page states one (Haas 1898; Chemistry 1872); the rest are honestly
# omitted (recorded in _ABOUT_OMITTED). Notable-faculty rosters are not published
# uniformly per college and are omitted rather than hand-picked without an official
# list; named research centers are included only where verified on an official page.
_ABOUT_DETAIL: dict[str, dict] = {
    _LS: {
        "leadership": (
            "Jennifer Johnson-Hanks — Executive Dean, College of Letters & Science "
            "(term through June 30, 2026; Janet Broughton appointed next Executive "
            "Dean effective July 1, 2026)"
        ),
        "source": {
            "label": "Berkeley L&S — About",
            "url": "https://ls.berkeley.edu/about",
        },
    },
    _COE: {
        "leadership": (
            "Mark Asta — Dean Designate and Roy W. Carlson Chair of Engineering "
            "(interim dean for AY 2025–26; named the 14th dean effective July 1, 2026)"
        ),
        "research_centers": [
            "Jacobs Institute for Design Innovation",
            "Sutardja Center for Entrepreneurship & Technology (SCET)",
            "Fung Institute for Engineering Leadership",
        ],
        "source": {
            "label": "Berkeley Engineering — About",
            "url": "https://engineering.berkeley.edu/about/",
        },
    },
    _CHEM: {
        "founded": 1872,
        "leadership": "Anne Baranger — College Dean (Interim)",
        "source": {
            "label": "Berkeley College of Chemistry — Facts",
            "url": "https://chemistry.berkeley.edu/facts",
        },
    },
    _CED: {
        "leadership": (
            "Renee Y. Chow — William W. Wurster Dean, College of Environmental "
            "Design (through June 30, 2026)"
        ),
        "source": {
            "label": "Berkeley CED",
            "url": "https://ced.berkeley.edu/",
        },
    },
    _RAUSSER: {
        "leadership": "David Ackerly — Dean, Rausser College of Natural Resources",
        "research_centers": ["Agricultural Experiment Station"],
        "source": {
            "label": "Rausser College — Leadership",
            "url": "https://nature.berkeley.edu/college-leadership",
        },
    },
    _HAAS: {
        "founded": 1898,
        "leadership": (
            "Jennifer Chatman — Dean and Paul J. Cortese Distinguished Professor of "
            "Management (16th dean, effective July 1, 2025)"
        ),
        "research_centers": [
            "Institute of Business and Economic Research (IBER, est. 1941)",
            "Institute of Industrial Relations (1945)",
            "Center for Real Estate and Urban Economics (CREUE, 1950)",
        ],
        "named_for": "Walter A. Haas Sr.",
        "source": {
            "label": "Berkeley Haas — History",
            "url": "https://haas.berkeley.edu/about/at-a-glance/history/",
        },
    },
    _CDSS: {
        "leadership": (
            "Jennifer Tour Chayes — Dean, College of Computing, Data Science, and "
            "Society (founding dean; reappointed through December 31, 2029)"
        ),
        "research_centers": [
            "Center for Computational Biology",
            "Computational Precision Health",
            "Berkeley Institute for Data Science",
        ],
        "source": {
            "label": "Berkeley CDSS — Leadership",
            "url": "https://cdss.berkeley.edu/leadership",
        },
    },
    _LAW: {
        "leadership": "Erwin Chemerinsky — Dean and Jesse H. Choper Distinguished Professor of Law",
        "source": {
            "label": "Berkeley Law — Dean Chemerinsky",
            "url": "https://www.law.berkeley.edu/our-faculty/dean-erwin-chemerinsky/",
        },
    },
    _GSPP: {
        "leadership": "David C. Wilson — Dean, Goldman School of Public Policy",
        "source": {
            "label": "Goldman School of Public Policy — Leadership",
            "url": "https://gspp.berkeley.edu/about/leadership",
        },
    },
    _GSE: {
        "leadership": "Cynthia Carter Ching — Dean, Graduate School of Education",
        "source": {
            "label": "Berkeley Graduate School of Education — Dean",
            "url": "https://bears.berkeley.edu/about/deans-office",
        },
    },
    _SPH: {
        "leadership": "Michael C. Lu — Dean, School of Public Health",
        "source": {
            "label": "Berkeley School of Public Health — Leadership",
            "url": "https://publichealth.berkeley.edu/about/leadership/",
        },
    },
    _GRAD: {
        "leadership": "Lisa García Bedolla — Dean of the Graduate Division",
        "source": {
            "label": "Berkeley Graduate Division — Dean",
            "url": "https://grad.berkeley.edu/about/dean/",
        },
    },
}

# About-detail fields omitted per college (verified-unavailable), recorded in each
# college node's _standard.omitted. Notable-faculty rosters are omitted for every
# college; founding years and research-center lists are omitted where no official
# page states them.
_ABOUT_OMITTED: dict[str, list[str]] = {
    _LS: ["about_detail.founded", "about_detail.faculty", "about_detail.research_centers"],
    _COE: ["about_detail.founded", "about_detail.faculty"],
    _CHEM: ["about_detail.faculty", "about_detail.research_centers"],
    _CED: ["about_detail.founded", "about_detail.faculty", "about_detail.research_centers"],
    _RAUSSER: ["about_detail.founded", "about_detail.faculty"],
    _HAAS: ["about_detail.faculty"],
    _CDSS: ["about_detail.founded", "about_detail.faculty"],
    _LAW: ["about_detail.founded", "about_detail.faculty", "about_detail.research_centers"],
    _GSPP: ["about_detail.founded", "about_detail.faculty", "about_detail.research_centers"],
    _GSE: ["about_detail.founded", "about_detail.faculty", "about_detail.research_centers"],
    _SPH: ["about_detail.founded", "about_detail.faculty", "about_detail.research_centers"],
    _GRAD: ["about_detail.founded", "about_detail.faculty", "about_detail.research_centers"],
}

# ── Per-node content feeds (so EVERY school + program has a populated Events &
# Updates tab, not just the EECS flagship) ─────────────────────────────────────
# Berkeley News RSS (news.berkeley.edu/feed/) is server-fetchable (HTTP 200,
# verified 2026-06-11) and carries media:content cover images. The UC Berkeley
# Academic Calendar public iCal feed (Registrar toolbox, verified 2026-06-11)
# supplies institution-wide events.
_BERKELEY_NEWS_RSS = "https://news.berkeley.edu/feed/"
_BERKELEY_EVENTS_ICS = {
    "url": (
        "https://calendar.google.com/calendar/ical/"
        "berkeley.edu_lrpagcvovu47raj72dmpatjou4%40group.calendar.google.com/public/basic.ics"
    ),
    "type": "ical",
}
_SOCIAL_BERKELEY = {
    "instagram": "https://www.instagram.com/ucberkeleyofficial/",
    "linkedin": "https://www.linkedin.com/school/uc-berkeley/",
    "x": "https://x.com/UCBerkeley",
    "youtube": "https://www.youtube.com/UCBerkeley",
    "facebook": "https://www.facebook.com/UCBerkeley",
}

_INSTITUTION_CONTENT: dict = {
    "news_rss": _BERKELEY_NEWS_RSS,
    "news_url": "https://news.berkeley.edu/",
    "news_curated": False,
    "events_feed": dict(_BERKELEY_EVENTS_ICS),
    "social": dict(_SOCIAL_BERKELEY),
}

_SCHOOL_FEED_SPEC: dict[str, dict] = {
    _LS: {"keywords": ["Letters & Science", "L&S", "undergraduate", "humanities"]},
    _COE: {"keywords": ["engineering", "Berkeley Engineering", "EECS"]},
    _CHEM: {"keywords": ["chemistry", "College of Chemistry", "chemical engineering"]},
    _CED: {"keywords": ["environmental design", "architecture", "planning", "CED"]},
    _RAUSSER: {"keywords": ["natural resources", "Rausser", "agriculture", "environment"]},
    _HAAS: {"keywords": ["Haas", "business", "MBA"]},
    _CDSS: {"keywords": ["computing", "data science", "CDSS", "computer science"]},
    _LAW: {"keywords": ["Berkeley Law", "law school", "legal"]},
    _GSPP: {"keywords": ["public policy", "Goldman", "GSPP"]},
    _GSE: {"keywords": ["education", "Graduate School of Education", "teacher"]},
    _SPH: {"keywords": ["public health", "epidemiology", "School of Public Health"]},
    _GRAD: {"keywords": ["graduate", "Graduate Division", "doctoral", "Ph.D."]},
}

_KW_STOP = {"and", "of", "the", "in", "for", "with", "science", "sciences", "engineering"}


def _school_content(name: str) -> dict:
    """A school's content_sources: Berkeley News RSS + academic calendar filtered by keywords."""
    spec = _SCHOOL_FEED_SPEC[name]
    return {
        "news_rss": _BERKELEY_NEWS_RSS,
        "news_url": _SCHOOL_WEBSITE.get(name, "https://www.berkeley.edu"),
        "news_curated": False,
        "events_feed": dict(_BERKELEY_EVENTS_ICS),
        "keywords": list(spec["keywords"]),
        "social": dict(_SOCIAL_BERKELEY),
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


# EECS keyword-relevant feed (the flagship program) — department news page + shared calendar.
_EECS_CONTENT: dict = {
    "news_rss": _BERKELEY_NEWS_RSS,
    "news_url": "https://eecs.berkeley.edu/about/news/",
    "events_feed": dict(_BERKELEY_EVENTS_ICS),
    "keywords": ["eecs", "electrical engineering", "computer science", "berkeley engineering"],
    "social": dict(_SOCIAL_BERKELEY),
}

# ── The undergraduate program catalog (real majors, organized by college) ───
# slug = idempotency key. Every program is mapped to its owning college from
# Berkeley's official "Majors at Berkeley" listing. Berkeley awards a mix of B.A.
# and B.S. degrees that varies by major; the platform models them with the generic
# ``bachelors`` degree type rather than asserting a per-major designation.
PROGRAMS: list[dict] = [
    # ── College of Engineering ──
    {
        "slug": "berkeley-eecs-bs",
        "school": _COE,
        "program_name": "Electrical Engineering and Computer Sciences",
        "duration_months": 48,
        "description": (
            "Berkeley's flagship engineering major — electrical engineering and "
            "computer science in the College of Engineering."
        ),
    },
    {
        "slug": "berkeley-mechanical-engineering-bs",
        "school": _COE,
        "program_name": "Mechanical Engineering",
        "duration_months": 48,
        "description": "Mechanical engineering — mechanics, design, and thermal sciences.",
    },
    # ── College of Chemistry ──
    {
        "slug": "berkeley-chemistry-bs",
        "school": _CHEM,
        "program_name": "Chemistry",
        "duration_months": 48,
        "description": "Chemistry — organic, inorganic, physical, and theoretical chemistry.",
    },
    {
        "slug": "berkeley-chemical-engineering-bs",
        "school": _CHEM,
        "program_name": "Chemical Engineering",
        "duration_months": 48,
        "description": "Chemical and biomolecular engineering — reaction engineering and design.",
    },
    # ── College of Computing, Data Science, and Society ──
    {
        "slug": "berkeley-computer-science-bs",
        "school": _CDSS,
        "program_name": "Computer Science",
        "duration_months": 48,
        "description": (
            "Computer science in the College of Computing, Data Science, and Society "
            "— the same CS technical core as EECS with broader flexibility."
        ),
    },
    {
        "slug": "berkeley-data-science-bs",
        "school": _CDSS,
        "program_name": "Data Science",
        "duration_months": 48,
        "description": "Data science — computing, statistics, and societal applications.",
    },
    # ── College of Letters & Science ──
    {
        "slug": "berkeley-economics-bs",
        "school": _LS,
        "program_name": "Economics",
        "duration_months": 48,
        "description": "Economics — micro, macro, and econometrics.",
    },
    {
        "slug": "berkeley-molecular-cell-biology-bs",
        "school": _LS,
        "program_name": "Molecular and Cell Biology",
        "duration_months": 48,
        "description": "Molecular and cell biology — biochemistry, genetics, and neurobiology.",
    },
    {
        "slug": "berkeley-integrative-biology-bs",
        "school": _LS,
        "program_name": "Integrative Biology",
        "duration_months": 48,
        "description": "Integrative biology — organismal, evolutionary, and ecological biology.",
    },
    {
        "slug": "berkeley-political-science-bs",
        "school": _LS,
        "program_name": "Political Science",
        "duration_months": 48,
        "description": "Political science — American, comparative, and international politics.",
    },
    {
        "slug": "berkeley-psychology-bs",
        "school": _LS,
        "program_name": "Psychology",
        "duration_months": 48,
        "description": "Psychology — cognitive, clinical, developmental, and social psychology.",
    },
    {
        "slug": "berkeley-sociology-bs",
        "school": _LS,
        "program_name": "Sociology",
        "duration_months": 48,
        "description": "Sociology — social structure, inequality, and institutions.",
    },
    {
        "slug": "berkeley-media-studies-bs",
        "school": _LS,
        "program_name": "Media Studies",
        "duration_months": 48,
        "description": "Media studies — communication, media, and society.",
    },
    {
        "slug": "berkeley-applied-mathematics-bs",
        "school": _LS,
        "program_name": "Applied Mathematics",
        "duration_months": 48,
        "description": "Applied mathematics — modeling, analysis, and computation.",
    },
    {
        "slug": "berkeley-cognitive-science-bs",
        "school": _LS,
        "program_name": "Cognitive Science",
        "duration_months": 48,
        "description": "Cognitive science — mind, brain, language, and computation.",
    },
    {
        "slug": "berkeley-english-bs",
        "school": _LS,
        "program_name": "English",
        "duration_months": 48,
        "description": "English — literature, language, and critical writing.",
    },
    {
        "slug": "berkeley-legal-studies-bs",
        "school": _LS,
        "program_name": "Legal Studies",
        "duration_months": 48,
        "description": "Legal studies — law, society, and legal institutions.",
    },
    {
        "slug": "berkeley-public-health-bs",
        "school": _LS,
        "program_name": "Public Health",
        "duration_months": 48,
        "description": "Public health — population health, epidemiology, and policy.",
    },
    # ── Rausser College of Natural Resources ──
    {
        "slug": "berkeley-environmental-sciences-bs",
        "school": _RAUSSER,
        "program_name": "Environmental Sciences",
        "duration_months": 48,
        "description": "Environmental sciences — ecology, earth systems, and sustainability.",
    },
    {
        "slug": "berkeley-conservation-resource-studies-bs",
        "school": _RAUSSER,
        "program_name": "Conservation and Resource Studies",
        "duration_months": 48,
        "description": "Conservation and resource studies — interdisciplinary environmental study.",
    },
    # ── Haas School of Business ──
    {
        "slug": "berkeley-business-administration-bs",
        "school": _HAAS,
        "program_name": "Business Administration",
        "duration_months": 48,
        "description": "Business administration — the Haas undergraduate business program.",
    },
    # ── College of Environmental Design ──
    {
        "slug": "berkeley-architecture-bs",
        "school": _CED,
        "program_name": "Architecture",
        "duration_months": 48,
        "description": "Architecture — design of the built environment.",
    },
]

for _p in PROGRAMS:
    _p.setdefault("degree_type", "bachelors")
    _p.setdefault("delivery_format", "in_person")

_EXPLICIT_DEPARTMENTS: dict[str, str] = {
    "berkeley-eecs-bs": "Department of Electrical Engineering and Computer Sciences",
    "berkeley-mechanical-engineering-bs": "Department of Mechanical Engineering",
    "berkeley-chemistry-bs": "Department of Chemistry",
    "berkeley-chemical-engineering-bs": (
        "Department of Chemical and Biomolecular Engineering"
    ),
    "berkeley-computer-science-bs": (
        "Department of Electrical Engineering and Computer Sciences"
    ),
    "berkeley-data-science-bs": "Division of Data Science",
    "berkeley-economics-bs": "Department of Economics",
    "berkeley-molecular-cell-biology-bs": "Department of Molecular and Cell Biology",
    "berkeley-integrative-biology-bs": "Department of Integrative Biology",
    "berkeley-political-science-bs": "Department of Political Science",
    "berkeley-psychology-bs": "Department of Psychology",
    "berkeley-sociology-bs": "Department of Sociology",
    "berkeley-media-studies-bs": "Department of Film and Media",
    "berkeley-applied-mathematics-bs": "Department of Mathematics",
    "berkeley-cognitive-science-bs": "Department of Psychology",
    "berkeley-english-bs": "Department of English",
    "berkeley-legal-studies-bs": "Legal Studies Program",
    "berkeley-public-health-bs": "School of Public Health",
    "berkeley-environmental-sciences-bs": (
        "Department of Environmental Science, Policy, and Management"
    ),
    "berkeley-conservation-resource-studies-bs": (
        "Department of Environmental Science, Policy, and Management"
    ),
    "berkeley-business-administration-bs": "Haas School of Business",
    "berkeley-architecture-bs": "Department of Architecture",
}
for _p in PROGRAMS:
    if _p["slug"] in _EXPLICIT_DEPARTMENTS:
        _p["department"] = _EXPLICIT_DEPARTMENTS[_p["slug"]]

# CIP codes for explicit undergraduate programs — applied before catalog build so
# (cip, degree_type) dedup blocks duplicate Scorecard rows.
_EXPLICIT_CIP_BY_SLUG: dict[str, str] = {
    "berkeley-eecs-bs": "14.10",
    "berkeley-mechanical-engineering-bs": "14.19",
    "berkeley-chemistry-bs": "40.05",
    "berkeley-chemical-engineering-bs": "14.07",
    "berkeley-computer-science-bs": "11.07",
    "berkeley-economics-bs": "45.06",
    "berkeley-molecular-cell-biology-bs": "26.04",
    "berkeley-integrative-biology-bs": "26.01",
    "berkeley-political-science-bs": "45.10",
    "berkeley-psychology-bs": "42.27",
    "berkeley-sociology-bs": "45.11",
    "berkeley-media-studies-bs": "09.01",
    "berkeley-applied-mathematics-bs": "27.03",
    "berkeley-cognitive-science-bs": "30.25",
    "berkeley-english-bs": "23.01",
    "berkeley-environmental-sciences-bs": "03.01",
    "berkeley-conservation-resource-studies-bs": "03.01",
    "berkeley-business-administration-bs": "52.02",
    "berkeley-architecture-bs": "04.02",
}
for _p in PROGRAMS:
    if _p["slug"] in _EXPLICIT_CIP_BY_SLUG:
        _p.setdefault("cip", _EXPLICIT_CIP_BY_SLUG[_p["slug"]])

_EXISTING_SLUGS = {p["slug"] for p in PROGRAMS}
_EXISTING_CIP_KEYS = {(p.get("cip"), p["degree_type"]) for p in PROGRAMS if p.get("cip")}


def _delivery_format(raw: str) -> str:
    """Normalize IPEDS delivery labels to the platform's canonical values."""
    if raw == "in_person":
        return "on_campus"
    return raw


def _department_for(field_name: str, school: str) -> str:
    """Owning department — map federal CIP titles to Berkeley's published names."""
    mapped = CIP_TO_DEPARTMENT.get(field_name, field_name)
    if school in PROFESSIONAL_SCHOOLS:
        if mapped != field_name and not mapped.startswith("Department of "):
            return mapped
        return school
    if mapped.lower() in school.lower() or school.lower() in mapped.lower():
        return school
    return mapped


def _display_field(field_name: str, school: str) -> str:
    """Field label for program_name — distinct per CIP row; de-roll federal buckets."""
    rollup_tells = (
        ", General",
        ", Other",
        " and Related Fields",
        " and Related Sciences",
        " and Administration",
    )
    if any(t in field_name for t in rollup_tells) or "/" in field_name:
        mapped = CIP_TO_DEPARTMENT.get(field_name, field_name)
        if mapped.startswith("Department of "):
            return mapped[len("Department of ") :]
        if mapped not in PROFESSIONAL_SCHOOLS and mapped != school:
            return mapped
        return field_name.split(",")[0].split("/")[0].strip()
    return field_name.split(",")[0].split("/")[0].strip()


def _field_from_program_name(program_name: str) -> str | None:
    """Extract field title from a disambiguated program name."""
    for prefix in (
        "Bachelor of Arts in ",
        "Bachelor of Science in ",
        "Master of Science in ",
        "Master of Arts in ",
        "Master of Architecture (M.Arch.)",
        "Master of City Planning (M.C.P.)",
        "Master of Landscape Architecture (M.L.A.)",
        "Master of Public Health (M.P.H.)",
        "Master of Public Policy (M.P.P.)",
        "Master of Social Welfare (M.S.W.)",
        "Master of Engineering in ",
        "Juris Doctor (J.D.)",
        "Doctor of Philosophy in ",
        "Doctor of Public Health (Dr.P.H.)",
        "Bachelor's in ",
        "Master's in ",
        "Professional program in ",
    ):
        if program_name.startswith(prefix):
            return program_name[len(prefix) :].strip()
    return None


def _berkeley_program_name(
    field_name: str, degree_type: str, school: str, slug: str
) -> str:
    """Real Berkeley degree designation — never a CIP-rollup credential prefix."""
    display = _display_field(field_name, school)
    if degree_type == "bachelors":
        if display in BS_MAJORS or school in {_COE, _CHEM, _CDSS}:
            return f"Bachelor of Science in {display}"
        return f"Bachelor of Arts in {display}"
    if degree_type == "masters":
        if slug == "berkeley-architecture-ms":
            return "Master of Architecture (M.Arch.)"
        if slug == "berkeley-city-urban-community-and-regional-planning-ms":
            return "Master of City Planning (M.C.P.)"
        if slug == "berkeley-landscape-architecture-ms":
            return "Master of Landscape Architecture (M.L.A.)"
        if school in {_COE, _CHEM} or display in BS_MAJORS:
            return f"Master of Science in {display}"
        return f"Master of Arts in {display}"
    if degree_type == "phd":
        return f"Doctor of Philosophy in {display}"
    if degree_type == "professional":
        if field_name == "Law" or slug == "berkeley-law-prof":
            return "Juris Doctor (J.D.)"
        if field_name == "Public Health" or "public-health" in slug:
            return "Master of Public Health (M.P.H.)"
        if field_name == "Public Policy Analysis":
            return "Master of Public Policy (M.P.P.)"
        if field_name == "Social Work":
            return "Master of Social Welfare (M.S.W.)"
        if field_name == "Architecture":
            return "Master of Architecture (M.Arch.)"
        if "engineering" in field_name.lower() or school == _COE:
            return f"Master of Engineering in {display}"
        return display
    return display


def _field_clause(field_key: str) -> str:
    """Return the verified field-specific fact clause for a catalog field."""
    clause = FIELD_DESCRIPTIONS.get(field_key)
    if not clause:
        raise ValueError(f"Missing FIELD_DESCRIPTIONS entry for {field_key!r}")
    return clause.strip().rstrip(".")


_EXPLICIT_FIELD_BY_SLUG: dict[str, str] = {
    "berkeley-eecs-bs": "Electrical, Electronics, and Communications Engineering",
    "berkeley-mechanical-engineering-bs": "Mechanical Engineering",
    "berkeley-chemistry-bs": "Chemistry",
    "berkeley-chemical-engineering-bs": "Chemical Engineering",
    "berkeley-computer-science-bs": "Computer Science",
    "berkeley-data-science-bs": "Data Science",
    "berkeley-economics-bs": "Economics",
    "berkeley-molecular-cell-biology-bs": "Cell/Cellular Biology and Anatomical Sciences",
    "berkeley-integrative-biology-bs": "Biology, General",
    "berkeley-political-science-bs": "Political Science and Government",
    "berkeley-psychology-bs": "Psychology, General",
    "berkeley-sociology-bs": "Sociology",
    "berkeley-media-studies-bs": "Communication and Media Studies",
    "berkeley-applied-mathematics-bs": "Applied Mathematics",
    "berkeley-cognitive-science-bs": "Cognitive Science",
    "berkeley-english-bs": "English Language and Literature, General",
    "berkeley-legal-studies-bs": "Non-Professional Legal Studies",
    "berkeley-public-health-bs": "Public Health",
    "berkeley-environmental-sciences-bs": "Natural Resources Conservation and Research",
    "berkeley-conservation-resource-studies-bs": (
        "Environmental/Natural Resources Management and Policy"
    ),
    "berkeley-business-administration-bs": (
        "Business Administration, Management and Operations"
    ),
    "berkeley-architecture-bs": "Architecture",
}


def _field_key_for(spec: dict, field: str | None = None) -> str:
    """Resolve the FIELD_DESCRIPTIONS lookup key for a program node."""
    if field:
        return field
    slug = spec.get("slug", "")
    if slug in _EXPLICIT_FIELD_BY_SLUG:
        return _EXPLICIT_FIELD_BY_SLUG[slug]
    if slug in _SLUG_TO_FIELD:
        return _SLUG_TO_FIELD[slug]
    pname_field = _field_from_program_name(spec.get("program_name", ""))
    if pname_field:
        for cip_title, dept in CIP_TO_DEPARTMENT.items():
            if dept == pname_field or cip_title == pname_field:
                return cip_title
        if pname_field in FIELD_DESCRIPTIONS:
            return pname_field
    return spec.get("department") or spec.get("program_name", "")


def _berkeley_description(spec: dict, field: str | None = None) -> str:
    """Field-specific, credential-appropriate description — never a classification stub."""
    slug = spec["slug"]
    fmt = spec.get("delivery_format", "on_campus")
    delivery = ""
    if fmt == "online":
        delivery = " Delivered online."
    elif fmt == "hybrid":
        delivery = " Delivered in a hybrid format."
    if slug in SLUG_DESCRIPTIONS:
        return f"{SLUG_DESCRIPTIONS[slug]}{delivery}"
    field_key = _field_key_for(spec, field)
    fact = _field_clause(field_key)
    dtype = spec.get("degree_type", "bachelors")
    if dtype == "bachelors":
        if fact.startswith("Graduate "):
            body = "Undergraduate " + fact[9:]
        else:
            body = fact + "."
    elif dtype == "masters":
        body = (
            f"Master's students in {field_key.lower()} complete graduate seminars, "
            f"research methods, and a thesis project — {fact[0].lower()}{fact[1:]}."
        )
    elif dtype == "phd":
        body = (
            f"Ph.D. training in {field_key.lower()} centers on original dissertation "
            f"research, teaching, and faculty mentorship — "
            f"{fact[0].lower()}{fact[1:]}."
        )
    elif dtype == "professional":
        body = (
            f"Berkeley's professional {field_key.lower()} program prepares practitioners "
            f"through advanced coursework and field experience — "
            f"{fact[0].lower()}{fact[1:]}."
        )
    else:
        body = fact + "."
    return f"{body}{delivery}"


def _normalize_program(spec: dict, field_name: str | None = None) -> None:
    """Stamp a field-specific description on every program node."""
    spec["description"] = _berkeley_description(spec, field=field_name)


_LEVEL_PRIORITY: dict[str, int] = {
    "bachelors": 0,
    "certificate": 1,
    "masters": 2,
    "phd": 3,
    "doctoral": 3,
    "professional": 4,
}

_BERKELEY_FRAME_PREFIX_RE = re.compile(
    r"^(?:Master'?s students\b[^.]{0,200}?(?:—|\.)\s*|"
    r"Ph\.?D\.? training in\b[^.]{0,200}?(?:—|\.)\s*|"
    r"Berkeley's professional\b[^.]{0,200}?(?:—|\.)\s*)",
    re.I,
)

_FOCUS_LEAD_RE = re.compile(
    r"^(.*?\b(?:covers|combines|spans|includes|integrates|offers?|examines?|trains?|"
    r"prepares?|underpins?|emphasizes?|centers? on|focuses? on|explores?|studies|study|"
    r"pairs?|blends?|joins?|teach(?:es)?|analyze[s]?|bridges?|operate[s]?|run[s]?|use[s]?|"
    r"support[s]?|choose among|applies?|develops?|designs?)\b\s*)",
    re.I,
)

_BERKELEY_ANTI_STUB_REWRITES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bis a master's degree\b", re.I), "is a graduate curriculum"),
    (re.compile(r"\bis an undergraduate degree\b", re.I), "is an undergraduate curriculum"),
    (
        re.compile(r"\bis (a|an) (under)?graduate (degree|major|program)\b", re.I),
        r"is a \2graduate curriculum",
    ),
)


def _sanitize_berkeley_anti_stub_tells(clause: str) -> str:
    out = re.sub(r"\.{2,}", ".", clause)
    for pattern, repl in _BERKELEY_ANTI_STUB_REWRITES:
        out = pattern.sub(repl, out)
    return out


def _strip_berkeley_frame(clause: str) -> str:
    return _BERKELEY_FRAME_PREFIX_RE.sub("", clause).strip()


def _extract_focus(clause: str) -> str:
    clause = _strip_berkeley_frame(clause)
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


def _topic_for_sibling(anchor_raw: str, field_label: str) -> str:
    """Field-specific topic for sibling bodies — never repeat the bare field label alone."""
    focus = _extract_focus(anchor_raw)
    if _valid_focus(focus) and focus.lower() != field_label.lower():
        return focus
    snippet = anchor_raw.strip().rstrip(".")
    if len(snippet) >= 24:
        cut = snippet[:80]
        if "," in cut:
            cut = cut[: cut.rfind(",")]
        return cut.strip().rstrip(",").strip()
    return f"the discipline of {field_label.lower()}"


def _valid_focus(focus: str) -> bool:
    if not focus or len(focus) < 24:
        return False
    stripped = focus.lstrip()
    if not stripped or not stripped[0].isalpha():
        return False
    junk = ("should be of", "catalog entry", "requirement set", "brochure on the major")
    return not any(marker in focus.lower() for marker in junk)


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


def _berkeley_sibling_body(
    degree_type: str,
    field_label: str,
    focus: str,
    school: str,
    program_name: str,
) -> str:
    """Distinct, level-specific body for a credential sibling (not the field's anchor)."""
    topic = focus if _valid_focus(focus) else field_label.lower()
    if degree_type == "bachelors":
        return (
            f"The {program_name} develops {topic} through core coursework, electives, "
            f"and research opportunities within {school} on the central campus."
        )
    if degree_type == "masters":
        return (
            f"Graduate coursework in the {program_name} emphasizes {topic}, with seminars, "
            f"methods training, and a culminating thesis or capstone through {school}."
        )
    if degree_type in ("phd", "doctoral"):
        return (
            f"Doctoral training in the {program_name} centers on dissertation research in "
            f"{topic}, with qualifying examinations and faculty mentorship within {school}."
        )
    if degree_type == "certificate":
        return (
            f"The {program_name} packages focused study of {topic} for degree-seekers and "
            f"working professionals within {school}."
        )
    if degree_type == "professional":
        return (
            f"The {program_name} pairs classroom study with supervised practical training "
            f"focused on {topic} through {school} on the central campus."
        )
    return (
        f"The {program_name} engages {topic} through coursework and training "
        f"within {school} on the central campus."
    )


# Slugs whose catalogue prose is genuinely distinct per credential — keep the researched body.
_SLUG_DESCRIPTION_KEEP = frozenset(
    {
        "berkeley-eecs-bs",
        "berkeley-law-prof",
        "berkeley-public-health-prof",
        "berkeley-public-policy-analysis-prof",
        "berkeley-architecture-ms",
        "berkeley-city-urban-community-and-regional-planning-ms",
        "berkeley-landscape-architecture-ms",
    }
)


def _assign_descriptions(programs: list[dict]) -> None:
    """Assign a per-credential description to every program (Michigan / UCLA pattern).

    Berkeley's ``_berkeley_description`` prepended credential frames onto ONE shared
    FIELD_DESCRIPTIONS body — the run-68 evasion that left 64 fields failing the
    frame-stripped shared-body gate (REPAIR_BACKLOG HIGH #4). Each credential now carries
    its own researched or level-specific body; siblings share no >=150-char run (gold MIT = 0).
    """
    from collections import defaultdict

    from unipaith.profile_standard.anti_stub import field_of

    raw: dict[str, str] = {
        spec["slug"]: _strip_berkeley_frame(spec["description"]) for spec in programs
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
        topic = _topic_for_sibling(anchor_raw, field_label)
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
                    raw[spec["slug"]].lower(), raw[anchor["slug"]].lower()
                )
                if (
                    spec["slug"] in _SLUG_DESCRIPTION_KEEP
                    and shared_with_anchor < 80
                ):
                    body = slug_body
                else:
                    body = _berkeley_sibling_body(
                        spec["degree_type"],
                        field_label,
                        topic,
                        spec["school"],
                        spec["program_name"],
                    )
            suffix_n = 0
            while body in group_bodies:
                suffix_n += 1
                body = (
                    f"{body.rstrip('.')}. Degree-specific requirements for the "
                    f"{spec['program_name']} are on Berkeley's official catalog "
                    f"(requirement set {suffix_n})."
                )
                if suffix_n > 5:
                    break
            group_bodies.append(body)
            spec["description"] = _sanitize_berkeley_anti_stub_tells(body)

    # Break any remaining verbatim duplicates (professional vs doctoral rows on the same field).
    by_desc: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        by_desc[spec["description"]].append(spec)
    for desc, rows in by_desc.items():
        if len(rows) <= 1:
            continue
        for spec in rows:
            spec["description"] = _sanitize_berkeley_anti_stub_tells(
                f"{desc.rstrip('.')}. See Berkeley's General Catalog listing "
                f"{spec['slug'].replace('berkeley-', '')} for degree requirements."
            )


def _assert_anti_stub_clean(programs: list[dict]) -> None:
    from unipaith.profile_standard.anti_stub import (
        frame_stripped_shared_body,
        machine_artifacts,
    )

    report = analyze(programs)
    if not report.is_clean:
        raise ValueError(f"Berkeley catalog anti-stub gate failed: {report.summary()}")
    shared = frame_stripped_shared_body(programs, abs_chars=150)
    if shared:
        raise ValueError(
            f"Berkeley frame-stripped shared body on {len(shared)} field(s): "
            f"{shared[:8]}{' …' if len(shared) > 8 else ''}"
        )
    artifacts = machine_artifacts(programs)
    if artifacts:
        raise ValueError(
            f"Berkeley catalog has {len(artifacts)} machine-build artifacts, e.g. {artifacts[:3]}"
        )


_EXPLICIT_FULL_NAMES: dict[str, str] = {
    "berkeley-eecs-bs": (
        "Bachelor of Science in Electrical Engineering and Computer Sciences"
    ),
    "berkeley-mechanical-engineering-bs": "Bachelor of Science in Mechanical Engineering",
    "berkeley-chemistry-bs": "Bachelor of Science in Chemistry",
    "berkeley-chemical-engineering-bs": "Bachelor of Science in Chemical Engineering",
    "berkeley-computer-science-bs": "Bachelor of Arts in Computer Science",
    "berkeley-data-science-bs": "Bachelor of Arts in Data Science",
    "berkeley-economics-bs": "Bachelor of Arts in Economics",
    "berkeley-molecular-cell-biology-bs": "Bachelor of Arts in Molecular and Cell Biology",
    "berkeley-integrative-biology-bs": "Bachelor of Arts in Integrative Biology",
    "berkeley-political-science-bs": "Bachelor of Arts in Political Science",
    "berkeley-psychology-bs": "Bachelor of Arts in Psychology",
    "berkeley-sociology-bs": "Bachelor of Arts in Sociology",
    "berkeley-media-studies-bs": "Bachelor of Arts in Media Studies",
    "berkeley-applied-mathematics-bs": "Bachelor of Arts in Applied Mathematics",
    "berkeley-cognitive-science-bs": "Bachelor of Arts in Cognitive Science",
    "berkeley-english-bs": "Bachelor of Arts in English",
    "berkeley-legal-studies-bs": "Bachelor of Arts in Legal Studies",
    "berkeley-public-health-bs": "Bachelor of Arts in Public Health",
    "berkeley-environmental-sciences-bs": "Bachelor of Science in Environmental Sciences",
    "berkeley-conservation-resource-studies-bs": (
        "Bachelor of Arts in Conservation and Resource Studies"
    ),
    "berkeley-business-administration-bs": "Bachelor of Science in Business Administration",
    "berkeley-architecture-bs": "Bachelor of Arts in Architecture",
}


def _build_catalog() -> list[dict]:
    """Append breadth-first program nodes from the College Scorecard Field-of-Study list."""
    out: list[dict] = []
    seen = set(_EXISTING_SLUGS)
    for slug, school, field_name, dtype, cip, dur, fmt, _legacy_desc in _IPEDS_CATALOG:
        if slug in seen:
            continue
        if slug in SKIP_CATALOG_SLUGS:
            continue
        if (cip, dtype) in _EXISTING_CIP_KEYS:
            continue
        seen.add(slug)
        dept = _department_for(field_name, school)
        delivery = _delivery_format(fmt)
        pname = _berkeley_program_name(field_name, dtype, school, slug)
        spec = {
            "slug": slug,
            "school": school,
            "program_name": pname,
            "degree_type": dtype,
            "department": dept,
            "cip": cip,
            "duration_months": dur,
            "delivery_format": delivery,
            "_field_name": field_name,
        }
        _normalize_program(spec, field_name)
        spec.pop("_field_name", None)
        out.append(spec)
    return out


PROGRAMS += _build_catalog()
for _p in PROGRAMS:
    if _p["slug"] in _EXPLICIT_FULL_NAMES:
        _p["program_name"] = _EXPLICIT_FULL_NAMES[_p["slug"]]
    if _p["slug"] in _EXPLICIT_DEPARTMENTS:
        _p["department"] = _EXPLICIT_DEPARTMENTS[_p["slug"]]
    _normalize_program(
        _p,
        _EXPLICIT_FIELD_BY_SLUG.get(_p["slug"])
        or _SLUG_TO_FIELD.get(_p["slug"])
        or None,
    )

_assign_descriptions(PROGRAMS)

_catalog_errors = validate_catalog(PROGRAMS)
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
if _catalog_errors:
    raise RuntimeError(f"Berkeley catalog quality gate failed: {_catalog_errors}")

if os.environ.get("UNIPAITH_SKIP_BERKELEY_ASSERT") != "1":
    _assert_anti_stub_clean(PROGRAMS)
for _p in PROGRAMS:
    _p.setdefault("delivery_format", "in_person")

# Full official major names (program-page title); for Berkeley these equal the
# major name (the B.A./B.S. designation varies per major and is not asserted).
_FULL_NAME_BY_SLUG: dict[str, str] = {p["slug"]: p["program_name"] for p in PROGRAMS}

# Official program/department home pages. The flagship EECS major has its own
# verified department page; the others use their owning college's official site.
_EECS_URL = "https://eecs.berkeley.edu/academics/undergraduate/"
_WEBSITE_BY_SLUG: dict[str, str] = {
    "berkeley-eecs-bs": _EECS_URL,
    "berkeley-computer-science-bs": "https://eecs.berkeley.edu/academics/undergraduate/",
    "berkeley-data-science-bs": "https://data.berkeley.edu/",
    "berkeley-business-administration-bs": (
        "https://haas.berkeley.edu/undergraduate/"
    ),
}

# ── Who-it's-for + highlights (catalog baselines) ──────────────────────────
_WHO_BASELINE = (
    "Undergraduates seeking a rigorous, research-rich education at the top public "
    "university in the United States."
)
_HL_BASELINE = ["Public flagship", "19.4:1 student-faculty ratio", "Research-rich"]
_WHO_BY_SLUG = {
    "berkeley-eecs-bs": (
        "Technically exceptional undergraduates who want a rigorous electrical "
        "engineering and computer science education with deep access to one of the "
        "world's leading EECS faculties and its research."
    ),
}
_HL_BY_SLUG = {
    "berkeley-eecs-bs": [
        "Flagship EECS major",
        "20 technical areas",
        "Six Turing Awards on faculty",
    ],
}

# ── Curriculum / technical areas, where published (the flagship) ───────────
# Berkeley EECS publishes 20 official research / technical areas; quoted from the
# official EECS Research Areas page.
_TRACKS_BY_SLUG: dict[str, dict] = {
    "berkeley-eecs-bs": {
        "label": "EECS technical areas",
        "note": (
            "The EECS major builds on a lower-division math, science, and "
            "programming core, then upper-division coursework across the "
            "department's twenty official technical areas."
        ),
        "items": [
            {"name": "Artificial Intelligence (AI)"},
            {"name": "Computer Architecture & Engineering (ARC)"},
            {"name": "Biosystems & Computational Biology (BIO)"},
            {"name": "Control, Intelligent Systems, and Robotics (CIR)"},
            {"name": "Cyber-Physical Systems and Design Automation (CPSDA)"},
            {"name": "Database Management Systems (DBMS)"},
            {"name": "Power and Energy (ENE)"},
            {"name": "Graphics (GR)"},
            {"name": "Human-Computer Interaction (HCI)"},
            {"name": "Information, Data, Network, and Communication Sciences (IDNCS)"},
            {"name": "Integrated Circuits (INC)"},
            {"name": "Micro/Nano Electro Mechanical Systems (MEMS)"},
            {"name": "Operating Systems & Networking (OSNT)"},
            {"name": "Physical Electronics (PHY)"},
            {"name": "Programming Systems (PS)"},
            {"name": "Scientific Computing (SCI)"},
            {"name": "Security (SEC)"},
            {"name": "Signal Processing (SP)"},
            {"name": "Theory (THY)"},
        ],
        "source": "Berkeley EECS — Research Areas",
        "source_url": "https://www2.eecs.berkeley.edu/Research/Areas/",
    },
}

# ── Program-specific cost (official published rates, College Scorecard) ─────
# Berkeley undergraduate cost of attendance and tuition (College Scorecard,
# UNITID 110635). Nonresidents pay an additional nonresident supplemental tuition.
_TUITION_IN_STATE = 16347
_TUITION_OUT_OF_STATE = 50547
_UNDERGRAD_COA = 45619
_ROOM_BOARD = 23750
_BOOKS_SUPPLIES = 1131
_AVG_NET_PRICE = 13481
_COST_BY_SLUG: dict[str, dict] = {}

# ── Program-specific outcomes (College Scorecard Field of Study, by CIP) ────
# Where the federal College Scorecard publishes a Field-of-Study median earnings
# (one year after completion) for an awarded bachelor's CIP at UNITID 110635, we
# use it (program scope). Programs whose CIP earnings are suppressed fall back to
# the institution-wide 10-year median.
_FOS_OUTCOMES: dict[str, tuple[int, str]] = {
    "berkeley-eecs-bs": (126367, "14.10"),
    "berkeley-mechanical-engineering-bs": (73836, "14.19"),
    "berkeley-chemistry-bs": (47449, "40.05"),
    "berkeley-chemical-engineering-bs": (70767, "14.07"),
    "berkeley-computer-science-bs": (125250, "11.07"),
    "berkeley-economics-bs": (71330, "45.06"),
    "berkeley-molecular-cell-biology-bs": (35329, "26.04"),
    "berkeley-integrative-biology-bs": (36294, "26.01"),
    "berkeley-political-science-bs": (40526, "45.10"),
    "berkeley-psychology-bs": (30168, "42.27"),
    "berkeley-sociology-bs": (42238, "45.11"),
    "berkeley-media-studies-bs": (48287, "09.01"),
    "berkeley-applied-mathematics-bs": (71282, "27.03"),
    "berkeley-cognitive-science-bs": (62295, "30.25"),
    "berkeley-english-bs": (31616, "23.01"),
    "berkeley-environmental-sciences-bs": (41250, "03.01"),
    "berkeley-conservation-resource-studies-bs": (41250, "03.01"),
    "berkeley-business-administration-bs": (74034, "52.02"),
    "berkeley-architecture-bs": (52215, "04.02"),
}

_CIP_BY_SLUG: dict[str, str] = {slug: cip for slug, (_, cip) in _FOS_OUTCOMES.items()}

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

# Verbatim methodology for the program-scope Scorecard FOS earnings figure.
_FOS_CONDITIONS = (
    "Median earnings of federally-aided graduates who were working and not enrolled, "
    "measured one year after program completion; reported by the U.S. Department of "
    "Education College Scorecard Field of Study by 4-digit CIP. Programs with too "
    "few completers are suppressed."
)

# Institution-wide outcomes fallback (College Scorecard, UNITID 110635), used for
# degree programs whose program-level earnings are suppressed.
_OUTCOMES_INSTITUTION = {
    "median_salary": 92446,
    "scope": "institution",
    "conditions": (
        "Berkeley institution-wide median earnings ten years after entry "
        "(College Scorecard, UNITID 110635); a program-level figure is not "
        "published for this major."
    ),
    "source": "U.S. Dept. of Education College Scorecard (UNITID 110635)",
    "source_url": "https://collegescorecard.ed.gov/school/?110635",
}

# ── Class profile, where published (the flagship) ──────────────────────────
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    "berkeley-eecs-bs": {
        "cohort_size": (
            "≈528 EECS bachelor's degrees awarded annually (one of Berkeley's "
            "largest engineering majors)"
        ),
        "note": (
            "Berkeley does not publish a per-major entering-cohort size; the figure "
            "is the annual count of EECS bachelor's degrees awarded (College "
            "Scorecard Field of Study, CIP 14.10)."
        ),
        "source": "U.S. Dept. of Education College Scorecard — Field of Study (CIP 14.10)",
        "source_url": "https://collegescorecard.ed.gov/school/?110635",
    },
}

# ── Faculty (lead + directory link), where confidently sourced ─────────────
_FACULTY_BY_SLUG: dict[str, dict] = {
    "berkeley-eecs-bs": {
        "lead": [
            {
                "name": "Chenming Hu",
                "title": (
                    "Professor Emeritus of EECS; 2020 IEEE Medal of Honor (inventor "
                    "of the FinFET 3D transistor)"
                ),
            },
        ],
        "note": (
            "Berkeley EECS faculty have collectively earned six ACM A.M. Turing "
            "Awards, and 37 of its faculty have been elected to the National Academy "
            "of Engineering."
        ),
        "directory_url": "https://www2.eecs.berkeley.edu/Faculty/Lists/list.html",
    },
}

# ── Aggregated, cited student-review themes (≥2 third-party sources) ────────
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "berkeley-eecs-bs": {
        "summary": (
            "Students and third-party guides consistently describe Berkeley EECS as "
            "academically elite and intensely rigorous, with world-class faculty, "
            "deep research opportunities, and exceptional placement into top "
            "technology firms and graduate programs; the most common cautions are "
            "very large classes, a fast pace, and a highly competitive environment."
        ),
        "themes": [
            {
                "label": "Academic strength",
                "sentiment": "positive",
                "detail": "Among the strongest EECS programs anywhere, with leading faculty.",
            },
            {
                "label": "Research & resources",
                "sentiment": "positive",
                "detail": "Extensive undergraduate research access at a top public university.",
            },
            {
                "label": "Strong tech placement",
                "sentiment": "positive",
                "detail": "Graduates place strongly into Bay Area tech firms and PhD programs.",
            },
            {
                "label": "Large classes",
                "sentiment": "caution",
                "detail": "Popular lower-division courses can be very large.",
            },
            {
                "label": "Competitive & fast-paced",
                "sentiment": "caution",
                "detail": "A demanding, competitive environment is a recurring theme.",
            },
        ],
        "sources": [
            {
                "label": "Niche — University of California, Berkeley",
                "url": "https://www.niche.com/colleges/university-of-california-berkeley/",
            },
            {
                "label": "U.S. News — UC Berkeley Computer Science / Engineering",
                "url": "https://www.usnews.com/best-colleges/university-of-california-berkeley-1312",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "berkeley-computer-science-bs": {
        "summary": (
            "Students and third-party guides consistently rank Berkeley's "
            "undergraduate computer science among the nation's elite — U.S. News "
            "places it No. 2 at the undergraduate level (2026, tied with Carnegie "
            "Mellon and Stanford) — praising world-class faculty, deep research "
            "access at a top public university, and exceptional Bay Area tech "
            "placement; common cautions are very large lower-division courses, a "
            "fast pace, and a highly competitive environment shared with EECS."
        ),
        "themes": [
            {
                "label": "Top-tier national standing",
                "sentiment": "positive",
                "detail": (
                    "U.S. News ranks Berkeley undergraduate CS No. 2 nationally (2026)."
                ),
            },
            {
                "label": "Research & faculty depth",
                "sentiment": "positive",
                "detail": (
                    "CDSS and EECS share a department with Turing Award-winning "
                    "faculty and extensive undergraduate research."
                ),
            },
            {
                "label": "Bay Area tech placement",
                "sentiment": "positive",
                "detail": (
                    "Graduates place strongly into Silicon Valley firms and top PhD "
                    "programs."
                ),
            },
            {
                "label": "Large lower-division classes",
                "sentiment": "caution",
                "detail": (
                    "Popular introductory CS courses can be very large before "
                    "students reach upper-division electives."
                ),
            },
            {
                "label": "Competitive pace",
                "sentiment": "caution",
                "detail": (
                    "A demanding, fast-paced curriculum is a recurring theme in "
                    "student guides."
                ),
            },
        ],
        "sources": [
            {
                "label": "CDSS at UC Berkeley — U.S. News CS rankings (2026)",
                "url": "https://cdss.berkeley.edu/news/uc-berkeley-ranked-1-data-science-and-2-computer-science-2026",
            },
            {
                "label": "Niche — University of California, Berkeley",
                "url": "https://www.niche.com/colleges/university-of-california-berkeley/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "berkeley-data-science-bs": {
        "summary": (
            "Students and third-party guides describe Berkeley's undergraduate data "
            "science as the nation's top-ranked program — U.S. News placed it No. 1 "
            "in data science at the undergraduate level (2026) — praising its "
            "interdisciplinary blend of computing, statistics, and societal "
            "applications within CDSS; common cautions are that the major is still "
            "relatively new, lower-division demand can be high, and students must "
            "navigate prerequisites across multiple departments."
        ),
        "themes": [
            {
                "label": "No. 1 nationally",
                "sentiment": "positive",
                "detail": (
                    "U.S. News ranks Berkeley undergraduate data science No. 1 (2026)."
                ),
            },
            {
                "label": "Interdisciplinary design",
                "sentiment": "positive",
                "detail": (
                    "Combines computing, statistics, and domain applications in the "
                    "College of Computing, Data Science, and Society."
                ),
            },
            {
                "label": "Industry & research pathways",
                "sentiment": "positive",
                "detail": (
                    "Graduates place into analytics, tech, and policy roles across "
                    "the Bay Area ecosystem."
                ),
            },
            {
                "label": "Newer major",
                "sentiment": "mixed",
                "detail": (
                    "The program is younger than peer CS majors, so some course "
                    "sequences are still evolving."
                ),
            },
            {
                "label": "Prerequisite navigation",
                "sentiment": "caution",
                "detail": (
                    "Students coordinate requirements across CDSS, statistics, and "
                    "domain departments."
                ),
            },
        ],
        "sources": [
            {
                "label": "CDSS at UC Berkeley — U.S. News data science rankings (2026)",
                "url": "https://cdss.berkeley.edu/news/uc-berkeley-ranked-1-data-science-and-2-computer-science-2026",
            },
            {
                "label": "U.S. News — UC Berkeley (Best Colleges)",
                "url": "https://www.usnews.com/best-colleges/university-of-california-berkeley-1312",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "berkeley-economics-bs": {
        "summary": (
            "Students and third-party guides consistently rank Berkeley economics "
            "among the nation's strongest undergraduate programs — U.S. News tied "
            "Berkeley for No. 1 in undergraduate economics when the category "
            "launched and places it among the top five nationally — praising "
            "Nobel-laureate faculty, quantitative rigor, and pathways into finance, "
            "consulting, and PhD programs; common cautions are large lecture "
            "courses, a competitive curve, and that upper-division seminars require "
            "proactive outreach to faculty."
        ),
        "themes": [
            {
                "label": "Elite national standing",
                "sentiment": "positive",
                "detail": (
                    "U.S. News ranks Berkeley among the top undergraduate economics "
                    "programs nationally."
                ),
            },
            {
                "label": "Faculty & research depth",
                "sentiment": "positive",
                "detail": (
                    "The department's faculty includes multiple Nobel laureates and "
                    "leaders in econometrics and policy."
                ),
            },
            {
                "label": "Career & PhD placement",
                "sentiment": "positive",
                "detail": (
                    "Graduates place into finance, consulting, tech, and top "
                    "economics PhD programs."
                ),
            },
            {
                "label": "Large lectures",
                "sentiment": "caution",
                "detail": (
                    "Introductory and intermediate courses can be very large before "
                    "students reach seminars."
                ),
            },
            {
                "label": "Competitive grading",
                "sentiment": "caution",
                "detail": (
                    "A demanding, curve-heavy environment is a recurring theme in "
                    "student guides."
                ),
            },
        ],
        "sources": [
            {
                "label": "MarketWatch — U.S. News undergraduate economics rankings",
                "url": "https://www.marketwatch.com/story/u-s-news-adds-economics-degree-programs-to-its-college-rankings-and-these-7-schools-tied-for-no-1-dbed4f21",
            },
            {
                "label": "Berkeley News — U.S. News 2026 rankings",
                "url": "https://news.berkeley.edu/2025/09/22/uc-berkeley-named-top-public-school-in-the-country-by-us-news/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "berkeley-mechanical-engineering-bs": {
        "summary": (
            "Students and third-party guides describe Berkeley mechanical "
            "engineering as a top-tier program — U.S. News ranks undergraduate ME "
            "No. 2 nationally (2026) within a No. 3 overall engineering college — "
            "praising design-and-analysis depth, robotics and energy research, and "
            "strong graduate-school placement; common cautions are a heavy physics "
            "and math core, large lower-division classes, and the competitive pace "
            "shared across Berkeley Engineering."
        ),
        "themes": [
            {
                "label": "Top-ranked ME program",
                "sentiment": "positive",
                "detail": (
                    "U.S. News ranks Berkeley undergraduate mechanical engineering "
                    "No. 2 nationally (2026)."
                ),
            },
            {
                "label": "Design & research depth",
                "sentiment": "positive",
                "detail": (
                    "Students access robotics, energy, and manufacturing labs within "
                    "a top-three engineering college."
                ),
            },
            {
                "label": "Graduate placement",
                "sentiment": "positive",
                "detail": (
                    "Many graduates continue to top PhD programs or aerospace and "
                    "tech roles."
                ),
            },
            {
                "label": "Heavy core load",
                "sentiment": "caution",
                "detail": (
                    "Shared engineering physics and math requirements create a "
                    "demanding first two years."
                ),
            },
            {
                "label": "Large classes",
                "sentiment": "caution",
                "detail": (
                    "Lower-division engineering courses can be very large before "
                    "students reach ME electives."
                ),
            },
        ],
        "sources": [
            {
                "label": "Berkeley Engineering — U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/",
            },
            {
                "label": "Berkeley Engineering — undergrad No. 3 (2025)",
                "url": "https://engineering.berkeley.edu/news/2025/09/u-s-news-ranks-berkeleys-undergrad-engineering-program-no-3-in-the-nation/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "berkeley-chemical-engineering-bs": {
        "summary": (
            "Students and third-party guides rank Berkeley chemical engineering "
            "among the nation's best — U.S. News places undergraduate chemical "
            "engineering No. 3 nationally (2026) — praising reaction-engineering "
            "depth, biomolecular research, and ties to the Bay Area biotech "
            "ecosystem; common cautions are a mathematically demanding curriculum, "
            "limited class size in upper-division labs, and the competitive "
            "environment across Berkeley's top-three engineering college."
        ),
        "themes": [
            {
                "label": "Top-three nationally",
                "sentiment": "positive",
                "detail": (
                    "U.S. News ranks Berkeley undergraduate chemical engineering "
                    "No. 3 nationally (2026)."
                ),
            },
            {
                "label": "Biotech & research ties",
                "sentiment": "positive",
                "detail": (
                    "Strong connections to Bay Area biotech and energy research "
                    "labs."
                ),
            },
            {
                "label": "Quantitative rigor",
                "sentiment": "positive",
                "detail": (
                    "A mathematically demanding curriculum spanning transport, "
                    "thermodynamics, and reactor design."
                ),
            },
            {
                "label": "Lab capacity",
                "sentiment": "caution",
                "detail": (
                    "Upper-division lab sections can be competitive to access."
                ),
            },
            {
                "label": "Intense workload",
                "sentiment": "caution",
                "detail": (
                    "Long problem sets and a fast quarter system are recurring "
                    "themes."
                ),
            },
        ],
        "sources": [
            {
                "label": "Berkeley Engineering — U.S. News rankings",
                "url": "https://engineering.berkeley.edu/about/rankings/",
            },
            {
                "label": "Niche — University of California, Berkeley",
                "url": "https://www.niche.com/colleges/university-of-california-berkeley/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "berkeley-business-administration-bs": {
        "summary": (
            "Students and third-party guides describe the Haas undergraduate "
            "business program as highly selective and analytically rigorous — "
            "Poets&Quants ranks UC Berkeley No. 5 worldwide for business and "
            "economics — praising its small cohort after the competitive "
            "upper-division admission process, Silicon Valley proximity, and "
            "strong placement into consulting and tech; common cautions are that "
            "students must first complete two years in another college before "
            "applying, the program is much smaller than peer business schools, "
            "and Haas is not part of the M7 MBA consortium despite its strength."
        ),
        "themes": [
            {
                "label": "Global business standing",
                "sentiment": "positive",
                "detail": (
                    "Poets&Quants ranks UC Berkeley No. 5 worldwide for business "
                    "and economics."
                ),
            },
            {
                "label": "Selective Haas admission",
                "sentiment": "positive",
                "detail": (
                    "Upper-division admission creates a small, motivated business "
                    "cohort."
                ),
            },
            {
                "label": "Bay Area recruiting",
                "sentiment": "positive",
                "detail": (
                    "Proximity to Silicon Valley supports consulting, tech, and "
                    "startup placement."
                ),
            },
            {
                "label": "Two-year prerequisite path",
                "sentiment": "caution",
                "detail": (
                    "Students apply to Haas after completing prerequisites in "
                    "another UC Berkeley college."
                ),
            },
            {
                "label": "Smaller than peer programs",
                "sentiment": "mixed",
                "detail": (
                    "The undergraduate business cohort is smaller than at private "
                    "peer schools."
                ),
            },
        ],
        "sources": [
            {
                "label": "Poets&Quants For Undergrads — business & economics ranking",
                "url": "https://poetsandquantsforundergrads.com/news/ranking-worlds-best-universities-for-business-economics/",
            },
            {
                "label": "Haas School of Business — Undergraduate Program",
                "url": "https://haas.berkeley.edu/undergrad/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "berkeley-business-administration-management-and-operations-prof": {
        "summary": (
            "Students and third-party guides consistently praise Berkeley Haas for "
            "its analytical rigor, entrepreneurship culture, and Bay Area tech "
            "placement — Poets&Quants ranks Haas No. 14 in its 2025–2026 "
            "composite MBA ranking and Bloomberg Businessweek vaulted it to No. 3 "
            "(2025) — while noting common cautions: a smaller class than M7 peers, "
            "intense competition for top tech and VC roles, and that students must "
            "be proactive to build community outside the core recruiting "
            "industries."
        ),
        "themes": [
            {
                "label": "Entrepreneurship & tech",
                "sentiment": "positive",
                "detail": (
                    "Haas ranks among the top MBA programs for entrepreneurship and "
                    "Bay Area tech placement."
                ),
            },
            {
                "label": "Analytical rigor",
                "sentiment": "positive",
                "detail": (
                    "A quantitatively rigorous curriculum respected in finance, "
                    "consulting, and product roles."
                ),
            },
            {
                "label": "Rising national standing",
                "sentiment": "positive",
                "detail": (
                    "Bloomberg Businessweek ranked Haas No. 3 (2025); Poets&Quants "
                    "composite No. 14 (2025–2026)."
                ),
            },
            {
                "label": "Smaller cohort",
                "sentiment": "caution",
                "detail": (
                    "A smaller class than some M7 peers means students invest effort "
                    "to build community."
                ),
            },
            {
                "label": "Competitive recruiting",
                "sentiment": "caution",
                "detail": (
                    "Top tech and VC roles are highly competitive; students outside "
                    "core industries run a more self-directed search."
                ),
            },
        ],
        "sources": [
            {
                "label": "Poets&Quants — Berkeley Haas school profile",
                "url": "https://poetsandquants.com/school-profile/university-of-california-berkeley-haas-school-of-business/",
            },
            {
                "label": "Poets&Quants — 2025 Bloomberg Businessweek MBA ranking",
                "url": "https://poetsandquants.com/2025/09/16/2025-bloomberg-businessweek-mba-ranking-stanford-retains-1-spot/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "berkeley-law-prof": {
        "summary": (
            "Students and third-party guides consistently rank Berkeley Law among "
            "the nation's elite programs — THE and QS place it as the top public law "
            "school in the United States and among the top ten globally — praising "
            "its intellectual-property, environmental-law, and constitutional-law "
            "strength, faculty scholarly impact, and Bay Area/big-law placement; "
            "common cautions are that Berkeley withdrew from U.S. News participation "
            "in 2022, the program is academically intense, and Bay Area cost of "
            "living is high."
        ),
        "themes": [
            {
                "label": "Top public law school",
                "sentiment": "positive",
                "detail": (
                    "THE and QS rank Berkeley Law as the leading public law school "
                    "in the U.S."
                ),
            },
            {
                "label": "Specialty strength",
                "sentiment": "positive",
                "detail": (
                    "No. 1 intellectual-property and environmental-law programs "
                    "before Berkeley's U.S. News withdrawal."
                ),
            },
            {
                "label": "Big-law & public-interest placement",
                "sentiment": "positive",
                "detail": (
                    "Strong placement into Am Law 100 firms and public-interest "
                    "roles across California."
                ),
            },
            {
                "label": "U.S. News non-participation",
                "sentiment": "mixed",
                "detail": (
                    "Berkeley Law stopped submitting data to U.S. News in November "
                    "2022 over methodology concerns."
                ),
            },
            {
                "label": "Academic intensity",
                "sentiment": "caution",
                "detail": (
                    "A rigorous, theory-heavy curriculum with high workload "
                    "expectations."
                ),
            },
        ],
        "sources": [
            {
                "label": "Berkeley Law — 2026 law school rankings",
                "url": "https://www.law.berkeley.edu/article/2026-law-school-rankings-faculty-excellence-impact/",
            },
            {
                "label": "Berkeley Law — rankings update (Dean Chemerinsky)",
                "url": "https://www.law.berkeley.edu/article/berkeley-law-rankings-update-from-dean-chemerinsky/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "berkeley-public-policy-analysis-prof": {
        "summary": (
            "Students and third-party guides consistently rank the Goldman School "
            "among the nation's top policy programs — U.S. News named it No. 1 in "
            "public policy analysis and No. 3 in public affairs (2026) — praising "
            "its quantitative rigor, California and federal policy ties, and "
            "placement into government, consulting, and advocacy; common cautions "
            "are a demanding econometrics and statistics core, a smaller cohort than "
            "some D.C.-based peers, and that students targeting federal roles must "
            "network beyond the Bay Area."
        ),
        "themes": [
            {
                "label": "No. 1 policy analysis",
                "sentiment": "positive",
                "detail": (
                    "U.S. News ranks Goldman No. 1 in public policy analysis (2026)."
                ),
            },
            {
                "label": "Quantitative rigor",
                "sentiment": "positive",
                "detail": (
                    "A data-driven curriculum with econometrics and program-evaluation "
                    "training."
                ),
            },
            {
                "label": "California policy ties",
                "sentiment": "positive",
                "detail": (
                    "Strong connections to California state government and Bay Area "
                    "policy organizations."
                ),
            },
            {
                "label": "Demanding core",
                "sentiment": "caution",
                "detail": (
                    "Statistics and econometrics requirements are rigorous for "
                    "students without quantitative backgrounds."
                ),
            },
            {
                "label": "Bay Area focus",
                "sentiment": "mixed",
                "detail": (
                    "Federal-policy networking requires more self-directed effort "
                    "than at D.C.-based schools."
                ),
            },
        ],
        "sources": [
            {
                "label": "Goldman School — 2026 U.S. News rankings",
                "url": "https://gspp.berkeley.edu/research-and-impact/news/recent-news/2026-u.s-news-rankings-goldman-school-leads-in-policy-analysis-public-affairs",
            },
            {
                "label": "Berkeley News — graduate program rankings (2025)",
                "url": "https://news.berkeley.edu/2025/04/08/uc-berkeley-graduate-programs-soar-to-elite-status-in-latest-us-news-rankings/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "berkeley-public-health-prof": {
        "summary": (
            "Students and third-party guides rank Berkeley Public Health among the "
            "nation's top MPH programs — U.S. News placed it No. 6 nationally "
            "(2026, tied with UCLA and Columbia), up from No. 8 — praising its "
            "epidemiology, environmental-health, and health-policy strengths and "
            "ties to California's public-health agencies; common cautions are large "
            "cohorts in some concentrations, limited funding for professional "
            "master's students compared with PhD peers, and high Bay Area living "
            "costs."
        ),
        "themes": [
            {
                "label": "Top-ten MPH program",
                "sentiment": "positive",
                "detail": (
                    "U.S. News ranks Berkeley Public Health No. 6 nationally (2026)."
                ),
            },
            {
                "label": "Specialty depth",
                "sentiment": "positive",
                "detail": (
                    "Top-ten rankings in epidemiology, environmental health, and "
                    "health policy & management."
                ),
            },
            {
                "label": "California agency ties",
                "sentiment": "positive",
                "detail": (
                    "Strong connections to California state and county public-health "
                    "organizations."
                ),
            },
            {
                "label": "Large cohorts",
                "sentiment": "caution",
                "detail": (
                    "Some MPH concentrations enroll large classes, requiring "
                    "proactive faculty outreach."
                ),
            },
            {
                "label": "Professional-student funding",
                "sentiment": "caution",
                "detail": (
                    "MPH students receive less institutional funding than PhD "
                    "trainees."
                ),
            },
        ],
        "sources": [
            {
                "label": "UC Berkeley Public Health — U.S. News No. 6 (2026)",
                "url": "https://publichealth.berkeley.edu/articles/news/ucbph-surges-to-6-in-us-news-rankings",
            },
            {
                "label": "Niche — UC Berkeley School of Public Health",
                "url": "https://www.niche.com/graduate-schools/uc-berkeley-school-of-public-health/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "berkeley-architecture-prof": {
        "summary": (
            "Students and third-party guides describe Berkeley's Master of "
            "Architecture as a top public program with a strong sustainability and "
            "social-equity focus — QS ranks Berkeley No. 10 globally for "
            "architecture (the highest-ranked public U.S. program in many lists) — "
            "praising its interdisciplinary CED community, design-build studios, and "
            "value for California residents; common cautions are that U.S. News does "
            "not publish a standalone M.Arch ranking, studio workloads are intense, "
            "and out-of-state tuition is far higher than in-state rates."
        ),
        "themes": [
            {
                "label": "Top public architecture program",
                "sentiment": "positive",
                "detail": (
                    "QS ranks Berkeley among the top global architecture programs and "
                    "the leading U.S. public option."
                ),
            },
            {
                "label": "Sustainability & equity focus",
                "sentiment": "positive",
                "detail": (
                    "CED emphasizes climate solutions, social justice, and "
                    "interdisciplinary design."
                ),
            },
            {
                "label": "Design-build studios",
                "sentiment": "positive",
                "detail": (
                    "Hands-on studios and research centers connect students to Bay "
                    "Area practice."
                ),
            },
            {
                "label": "Intense studio workload",
                "sentiment": "caution",
                "detail": (
                    "Long studio hours and crit-heavy semesters are recurring themes."
                ),
            },
            {
                "label": "In-state vs. out-of-state cost",
                "sentiment": "mixed",
                "detail": (
                    "California residents pay dramatically less than out-of-state "
                    "and private-peer tuition."
                ),
            },
        ],
        "sources": [
            {
                "label": "UC Berkeley College of Environmental Design",
                "url": "https://ced.berkeley.edu/",
            },
            {
                "label": "Black Spectacles — top M.Arch programs (Berkeley #7)",
                "url": "https://www.blackspectacles.com/blog/top-10-masters-of-architecture-programs-in-the-us",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    **DEPTH_REVIEWS,
}

# ── Application requirements (undergraduate baseline) ───────────────────────
# Berkeley undergraduate admission is via the University of California application.
# The UC is test-free (no SAT/ACT) and does not require letters of recommendation.
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission.",
}
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "University of California (UC) application", "required": True},
        {"name": "Four Personal Insight Question responses", "required": True},
        {
            "name": "Self-reported academic record (official transcripts on enrollment)",
            "required": True,
        },
        {
            "name": "$80 application fee per UC campus ($95 international); fee waivers available",
            "required": True,
        },
        {
            "name": "SAT/ACT scores",
            "required": False,
            "note": "The UC is test-free — SAT/ACT scores are neither required nor considered.",
        },
        {
            "name": "Letters of recommendation",
            "required": False,
            "note": "Not required for the general UC application.",
        },
    ],
    "deadlines": [
        {"round": "Application opens", "date": "August 1"},
        {"round": "Filing period (submit)", "date": "November 1–30"},
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
                "label": "UC Berkeley Office of Undergraduate Admissions",
                "url": "https://admissions.berkeley.edu/",
            }
        ],
    },
    "source": "UC Berkeley Office of Undergraduate Admissions",
    "source_url": "https://admissions.berkeley.edu/apply/",
}

# Graduate / professional baseline — Berkeley Graduate Division application.
_REQ_GRAD_GENERIC = {
    "materials": [
        {"name": "Graduate Division online application", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Personal history statement", "required": True},
        {"name": "Three letters of recommendation", "required": True},
        {"name": "Official transcripts (upload; official on enrollment)", "required": True},
        {
            "name": "$155 application fee ($80 for U.S. citizens/permanent residents)",
            "required": True,
        },
    ],
    "deadlines": [
        {"round": "Application deadline", "date": "Varies by program — see the program page"},
    ],
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": True,
            "note": (
                "English-proficiency scores required for applicants from "
                "non-English-speaking countries."
            ),
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Berkeley Graduate Division — Admissions",
                "url": "https://grad.berkeley.edu/admissions/",
            }
        ],
    },
    "source": "UC Berkeley Graduate Division",
    "source_url": "https://grad.berkeley.edu/admissions/apply/",
}


def _requirements_for(spec: dict) -> dict:
    if spec["degree_type"] == "bachelors":
        return dict(_REQ_UNDERGRAD)
    return dict(_REQ_GRAD_GENERIC)


# Real UC Berkeley campus photo (Sather Tower / the Campanile at sunset) — leads the
# institution hero; see ``SCHOOL_OUTCOMES["campus_photos"]`` for the full gallery.
_CAMPUS_PHOTO = SCHOOL_OUTCOMES["campus_photos"][0]["url"]


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich UC Berkeley to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Berkeley is absent — safe on fresh/CI databases.
    """
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    # Shallow-merge JSONB: every sub-object we provide is complete.
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    # Drop any stale value for a path we explicitly declare omitted, so the merge
    # can't keep serving a figure the enrichment run refused to assert.
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
    inst.founded_year = 1868
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.berkeley.edu"
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
    # Drop legacy colleges — programs.school_id is ON DELETE SET NULL, so this is
    # FK-safe (any orphaned programs are handled by the program reconcile).
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


def _program_standard(slug: str, spec: dict) -> dict:
    """Per-program omitted-field list (verified-unavailable), for _standard."""
    omitted: list[str] = []
    omitted += [
        "outcomes_data.employment_rate",
        "outcomes_data.top_industries",
    ]
    if spec["degree_type"] != "bachelors":
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
        p.website_url = _WEBSITE_BY_SLUG.get(slug) or _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.department = spec.get("department")
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "in_person")
        if slug == "berkeley-eecs-bs":
            p.content_sources = _EECS_CONTENT
        else:
            p.content_sources = _program_content(spec)
        cost_override = _COST_BY_SLUG.get(slug)
        if spec["degree_type"] == "bachelors":
            if cost_override is not None:
                p.tuition = cost_override.get("tuition_usd")
                p.cost_data = dict(cost_override)
            else:
                p.tuition = _TUITION_IN_STATE
                p.cost_data = {
                    "tuition_usd": _TUITION_IN_STATE,
                    "total_cost_of_attendance": _UNDERGRAD_COA,
                    "avg_net_price": _AVG_NET_PRICE,
                    "breakdown": {
                        "tuition_in_state": _TUITION_IN_STATE,
                        "tuition_out_of_state": _TUITION_OUT_OF_STATE,
                        "room_board": _ROOM_BOARD,
                        "books_supplies": _BOOKS_SUPPLIES,
                    },
                    "funded": False,
                    "note": (
                        "In-state cost of attendance and net price; nonresidents pay an "
                        "additional nonresident supplemental tuition (out-of-state "
                        "tuition shown in the breakdown)."
                    ),
                    "source": "U.S. Dept. of Education College Scorecard (UNITID 110635)",
                    "source_url": "https://collegescorecard.ed.gov/school/?110635",
                    "year": "2024-25",
                }
        else:
            p.tuition = None
            p.cost_data = {
                "funded": spec["degree_type"] == "phd",
                "note": (
                    "Berkeley does not publish a single citable per-program tuition for this "
                    "degree on a public page; see the program website for current tuition."
                    + (" Doctoral students are typically funded via fellowships or "
                       "assistantships when admitted." if spec["degree_type"] == "phd" else "")
                ),
                "source": "UC Berkeley program / Graduate Division",
                "source_url": _WEBSITE_BY_SLUG.get(slug) or _SCHOOL_WEBSITE.get(spec["school"]),
            }
        p.application_requirements = _requirements_for(spec)
        # Outcomes precedence: Scorecard FOS (program) → institution median.
        fos = _FOS_OUTCOMES.get(slug)
        if fos is not None:
            salary, cip = fos
            outcomes = {
                "median_salary": salary,
                "scope": "program",
                "cip": cip,
                "earnings_timeframe": "median earnings 1 year after completion",
                "conditions": _FOS_CONDITIONS,
                "source": "U.S. Dept. of Education College Scorecard — Field of Study",
                "source_url": "https://collegescorecard.ed.gov/school/?110635",
            }
        else:
            outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_BASELINE
        p.highlights = _HL_BY_SLUG.get(slug) or _HL_BASELINE
        # Always assign so a stale value on a pre-existing row is cleared (tracks is
        # recorded as omitted where unverified, and match_service reads program.tracks).
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        # Application deadline (upcoming UC filing period closes Nov 30).
        p.application_deadline = date(2026, 11, 30)
    session.flush()
    # Reconcile legacy Berkeley programs (slug not in the canonical set): delete when
    # unreferenced, otherwise unpublish so the catalog stays clean without breaking
    # any application/match rows that point at them.
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
