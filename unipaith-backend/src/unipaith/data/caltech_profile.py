"""Canonical California Institute of Technology (Caltech) profile — the single
source of truth.

Real, sourced data only (U.S. Dept. of Education College Scorecard, UNITID 110404 ·
Caltech Common Data Set 2024-2025, Institutional Research Office · Caltech "At a
Glance" facts · Caltech FY2024 Endowment Report · Caltech's official University &
College Rankings page · the Caltech Class of 2023 Undergraduate Outcomes report ·
QS · Times Higher Education · U.S. News · each division's official chair/leadership
page). ``apply(session)`` idempotently enriches the Caltech institution row,
upserts the six real academic divisions, and builds Caltech's program catalog
across them.

Caltech is organized into SIX academic DIVISIONS (its own word — it has no
"schools" or "colleges"); we map them onto the platform's ``School`` model. It
**flushes but does not commit** — the caller (the Alembic data migration, the CLI
script, or the dev seed) owns the transaction. It is a **no-op** (returns
``False``) when Caltech is absent, so it is safe to run against a fresh or CI
database. Re-running is safe: divisions key off ``(institution_id, name)`` and
programs off ``slug``; stale rows are reconciled without breaking foreign keys.

This mirrors ``mit_profile`` / ``stanford_profile`` / ``harvard_profile`` so the
migration, the standalone script, and the dev seed all agree (DRY). Every figure
traces to a public, citable source; anything that could not be verified from a
first-party or two-independent-source basis is **omitted** (recorded in the
relevant ``_standard.omitted`` list), never guessed. The Computer Science
undergraduate option is the most-enriched flagship program (its real curriculum
tracks, faculty, class profile, and aggregated reviews), mirroring MIT Sloan's
MBAn and Stanford GSB's MBA in the reference instances — with the honest caveat
that Caltech does not publish per-program employment reports, so program-level
employment / industry / methodology fields are omitted rather than invented.

Description depth pass (2026-06-17, caltechprof7): replaces all classification-only
program descriptions with verified field-specific clauses from Caltech's official
catalog and division pages (90/90 programs; 0% classification stubs; 0% name-prefix
descriptions). Drops one duplicate IPEDS row (Business/Managerial Economics) that
mirrored the explicit BEM option.
"""

from __future__ import annotations

import re
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.caltech_field_descriptions import (
    FIELD_ALIASES,
    FIELD_DESCRIPTIONS,
    SLUG_DESCRIPTIONS,
)
from unipaith.data.caltech_ipeds_catalog import _IPEDS_CATALOG
from unipaith.data.caltech_reviews_depth import DEPTH_REVIEWS
from unipaith.data.profile_catalog_utils import validate_catalog
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "California Institute of Technology"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-17"

_CLASSIFICATION_STUB_RE = re.compile(
    r"^.+ is (an undergraduate|a graduate|a doctoral|a graduate certificate|"
    r"a professional|a degree) (major|program) at Caltech",
)
_TEMPLATE_STUB_RE = re.compile(
    r" — a .+ (undergraduate|graduate|doctoral|certificate|professional|"
    r"master's|bachelor's|phd|bachelors|masters) program offered through ",
    re.I,
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
    # Caltech's Class of 2023 Undergraduate Outcomes report explicitly withheld
    # employer names and industries ("aren't being released at this time"), and no
    # other first-party industry breakdown was verifiable. We publish the verified
    # placement rate but omit the top-industries list rather than guess it.
    "school_outcomes.top_employer_industries",
]

# ── Institution-level data ────────────────────────────────────────────────
# Rankings are stored as {rank, year} objects because the page renders every
# ranking_data entry that is an object with a numeric `rank` (labelled via the
# frontend `rankingLabel` map, which already knows these keys). All three ranks are
# quoted from Caltech's own official "University and College Rankings" page.
RANKING_DATA: dict = {
    "ownership_type": "private_nonprofit",
    # Caltech is accredited by the WASC Senior College and University Commission.
    "accreditor": "WSCUC",
    # Carnegie 2021 basic classification.
    "carnegie_classification": "Doctoral Universities: Very High Research Activity",
    # QS World University Rankings 2026 (Caltech official rankings page): rank 10.
    "qs_world_university_rankings": {"rank": 10, "year": 2026},
    # THE World University Rankings 2026 (Caltech official rankings page): rank 7.
    "times_higher_education": {"rank": 7, "year": 2026},
    # U.S. News Best Colleges (National Universities) 2026 (Caltech official
    # rankings page): rank 11.
    "us_news_national": {"rank": 11, "year": 2026},
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below
# is complete, so a shallow merge is correct. Figures are College Scorecard
# (UNITID 110404) cross-checked against Caltech's Common Data Set 2024-2025 where
# both publish the metric.
SCHOOL_OUTCOMES: dict = {
    # CDS 2024-25 C1: 356 admitted / 13,856 first-year applicants = 2.57%.
    "admit_rate": 0.0257,
    "avg_net_price": 16075,
    "median_earnings_10yr": 128566,
    "completion_rate_4yr_150pct": 0.9437,
    "retention_rate_first_year": 0.974,
    # CDS 2024-25 B22: six-year graduation rate for the full cohort = 94.40%.
    "graduation_rate_6yr": 0.944,
    # Class of 2023 Undergraduate Outcomes: 44% accepted a full-time job + 43%
    # entered graduate/professional school = 87% employed or continuing education.
    "employed_or_continuing_ed": 0.87,
    # SAT/ACT 25th-75th from IPEDS (Fall 2020) — the last cohort for which Caltech
    # reported scores before its test-blind/optional period; SAT or ACT is required
    # again beginning with the Class of 2029. The CDS 2024-25 reports no percentiles
    # (test-optional cycle), so these IPEDS figures are the most recent verifiable.
    "test_scores": {
        "sat_reading_25_75": [740, 780],
        "sat_math_25_75": [790, 800],
        "act_25_75": [35, 36],
        "year": 2020,
        "note": (
            "Fall 2020 — the most recent cohort for which Caltech reported SAT/ACT "
            "percentiles to IPEDS, before its test-blind/optional period. SAT or "
            "ACT is required again beginning with the Class of 2029."
        ),
    },
    "financial_aid": {
        "pell_grant_rate": 0.1799,
        "federal_loan_rate": 0.043,
        "cost_of_attendance": 86886,
        # CDS 2024-25 H2: Caltech meets 100% of every admitted student's
        # demonstrated financial need; the average need-based aid package among
        # first-year aid recipients was $74,780.
        "need_fully_met": True,
        "avg_need_based_package_first_year": 74780,
    },
    # CDS 2024-25 B2 — undergraduate enrollment by race/ethnicity (of 987
    # degree-seeking undergraduates); women share = 446/987 of degree-seeking
    # undergraduates (CDS B1).
    "demographics": {
        "white": 0.1874,
        "black": 0.0466,
        "hispanic": 0.1743,
        "asian": 0.3587,
        "women": 0.4519,
    },
    # Caltech main campus, Pasadena.
    "location": {"lat": 34.1377, "lng": -118.1253},
    "campus_basics": {"location": "Pasadena, California (greater Los Angeles)"},
    "scale": {
        # Caltech "At a Glance": 323 professorial faculty; 3:1 student-faculty ratio.
        "faculty_count": 323,
        "student_faculty_ratio": "3:1",
        # College Scorecard end-of-year endowment value (UNITID 110404).
        "endowment_usd": 4228841000,
        # Caltech "At a Glance": 124-acre Pasadena campus.
        "campus_acres": 124,
    },
    "research": {
        "labs": [
            "Jet Propulsion Laboratory (JPL)",
            "LIGO (Laser Interferometer Gravitational-Wave Observatory)",
            "Palomar Observatory",
            "W. M. Keck Observatory",
            "Beckman Institute",
            "Kavli Nanoscience Institute",
            "Institute for Quantum Information and Matter (IQIM)",
            "Seismological Laboratory",
        ],
        "areas": [
            "Astronomy & astrophysics",
            "Quantum science & matter",
            "Bioengineering & neuroscience",
            "Chemistry & catalysis",
            "Planetary & environmental science",
            "Computing & data science",
            "Aerospace & applied physics",
        ],
        "lab_links": {
            "Jet Propulsion Laboratory (JPL)": "https://www.jpl.nasa.gov/",
            "LIGO (Laser Interferometer Gravitational-Wave Observatory)": (
                "https://www.ligo.caltech.edu/"
            ),
            "Palomar Observatory": "https://sites.astro.caltech.edu/palomar/",
            "W. M. Keck Observatory": "https://keckobservatory.org/",
            "Beckman Institute": "https://beckmaninstitute.caltech.edu/",
            "Kavli Nanoscience Institute": "https://www.kni.caltech.edu/",
            "Institute for Quantum Information and Matter (IQIM)": "https://iqim.caltech.edu/",
            "Seismological Laboratory": "https://www.seismolab.caltech.edu/",
        },
    },
    "campus_life": {
        # Caltech competes in NCAA Division III in the Southern California
        # Intercollegiate Athletic Conference (SCIAC) as the Beavers.
        "athletics_division": "NCAA Division III (SCIAC)",
        "mascot": "Beavers",
        "housing": "Undergraduate residential house system (eight houses)",
        "resources": [
            {"label": "Caltech Athletics (Beavers)", "url": "https://gocaltech.com/"},
            {"label": "Housing — Undergraduate Houses", "url": "https://housing.caltech.edu/"},
        ],
    },
    "campus_photos": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ee/"
                "Arms_Courtyard_Caltech_2017.jpg/1920px-Arms_Courtyard_Caltech_2017.jpg"
            ),
            "credit": "Wikimedia Commons / Antony-22 (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/"
                "Athenaeum_Caltech_2020c.jpg/1920px-Athenaeum_Caltech_2020c.jpg"
            ),
            "credit": "Wikimedia Commons / Antony-22 (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/"
                "Caltech_Hall_2022b.jpg/1920px-Caltech_Hall_2022b.jpg"
            ),
            "credit": "Wikimedia Commons / Antony-22 (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/e/ef/Millikan_Library%2C_Caltech.jpg",
            "credit": "Wikimedia Commons / Geographer (CC BY 1.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/"
                "Robert_A._Millikan_Memorial_Library_at_Caltech.jpg/"
                "1920px-Robert_A._Millikan_Memorial_Library_at_Caltech.jpg"
            ),
            "credit": "Wikimedia Commons / Canon.vs.nikon (CC BY-SA 3.0)",
        },
    ],
    "media_credit": "Wikimedia Commons / Antony-22 (CC BY-SA 4.0)",
    "flagship": {
        # CDS 2024-25 B1 grand total enrollment: 987 undergraduate + 1,443 graduate.
        "enrollment_total": 2430,
        "applicants": 13856,
        "admits": 356,
        "admissions_cycle": "Entering class fall 2024 (Common Data Set 2024-2025)",
        # Caltech "At a Glance": 49 Nobel laureates associated with Caltech.
        "nobel_laureates": 49,
        # Caltech "At a Glance": 68 National Medal of Science recipients.
        "national_medal_science": 68,
        # Caltech "At a Glance": 15 National Medal of Technology and Innovation.
        "national_medal_technology": 15,
        # Founded as Throop University in 1891; renamed Caltech in 1920.
        "founded_year": 1891,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Caltech, UNITID 110404)",
            "url": "https://collegescorecard.ed.gov/school/?110404",
        },
        {
            "label": "Caltech Common Data Set 2024-2025 (Institutional Research Office)",
            "url": "https://iro.caltech.edu/documents/31491/Caltech_CDS_2024-2025_May_2025.pdf",
        },
        {"label": "Caltech — At a Glance", "url": "https://www.caltech.edu/about/at-a-glance"},
        {
            "label": "Caltech FY2024 Endowment Report",
            "url": (
                "https://investments.caltech.edu/documents/31209/"
                "Caltech_Endowment_Brochure_FY24_Final_Pages_compressed2.pdf"
            ),
        },
        {
            "label": "Caltech — University and College Rankings",
            "url": "https://www.caltech.edu/about/university-and-college-rankings",
        },
        {
            "label": "Caltech Class of 2023 Undergraduate Outcomes",
            "url": (
                "https://www.finaid.caltech.edu/documents/27967/"
                "Caltech_Class_of_2023_Undergraduate_Outcomes.pdf"
            ),
        },
        {
            "label": "QS World University Rankings 2026",
            "url": "https://www.topuniversities.com/universities/california-institute-technology-caltech",
        },
        {
            "label": "Times Higher Education — Caltech",
            "url": (
                "https://www.timeshighereducation.com/world-university-rankings/"
                "california-institute-technology"
            ),
        },
        {
            "label": "U.S. News — California Institute of Technology",
            "url": "https://www.usnews.com/best-colleges/california-institute-of-technology-1131",
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it
# "Undergraduates"); the total (2,430) lives in flagship.enrollment_total and
# renders as "Total enrollment". 987 = CDS 2024-25 / College Scorecard
# degree-seeking undergraduates (UNITID 110404).
UNDERGRAD_COUNT = 987

DESCRIPTION = (
    "California Institute of Technology (Caltech) is a private research university "
    "in Pasadena, CA, on a 124-acre campus in greater Los Angeles. Founded as "
    "Throop University in 1891 and renamed the California Institute of Technology "
    "in 1920, it is one of the "
    "smallest top-tier research universities in the world — roughly 990 "
    "undergraduates and about 1,440 graduate students — by deliberate design.\n\n"
    "Caltech is organized into six academic divisions: Biology and Biological "
    "Engineering; Chemistry and Chemical Engineering; Engineering and Applied "
    "Science; Geological and Planetary Sciences; the Humanities and Social "
    "Sciences; and Physics, Mathematics and Astronomy. Its 323 professorial "
    "faculty teach at a 3:1 student-faculty ratio, and the Institute manages NASA's "
    "Jet Propulsion Laboratory and operates landmark research facilities including "
    "LIGO, the Palomar Observatory, and the W. M. Keck Observatory.\n\n"
    "For its size, Caltech's record is singular: it is associated with 49 Nobel "
    "laureates, 68 National Medal of Science recipients, and 15 National Medal of "
    "Technology and Innovation recipients. It ranks among the very best "
    "universities in the world — No. 7 by Times Higher Education and No. 10 by QS "
    "— and admits about 2.6% of first-year applicants.\n\n"
    "A famously rigorous, science-and-engineering-centered education is paired with "
    "need-based aid that meets 100% of demonstrated need and holds the average net "
    "price near $16,000 a year. Caltech graduates leave with a median income of "
    "roughly $129,000 a decade after entry, and most go directly into industry or "
    "on to graduate and professional school."
)

# ── The six real academic divisions (in display order) ──────────────────────
_BBE = "Division of Biology and Biological Engineering"
_CCE = "Division of Chemistry and Chemical Engineering"
_EAS = "Division of Engineering and Applied Science"
_GPS = "Division of Geological and Planetary Sciences"
_HSS = "Division of the Humanities and Social Sciences"
_PMA = "Division of Physics, Mathematics and Astronomy"

SCHOOLS: list[dict] = [
    {
        "name": _BBE,
        "sort_order": 1,
        "description": (
            "Established in 1928 by Nobel laureate Thomas Hunt Morgan, Caltech's "
            "biology division spans biological engineering, cellular and "
            "developmental biology, evolutionary and organismal biology, "
            "microbiology, molecular biology and biophysics, and neuroscience — "
            "a lineage that has produced an extraordinary number of Nobel Prizes."
        ),
    },
    {
        "name": _CCE,
        "sort_order": 2,
        "description": (
            "Caltech's chemistry and chemical engineering division conducts research "
            "across organic, inorganic, physical, and theoretical chemistry, "
            "biochemistry, and chemical engineering — tackling challenges in energy, "
            "medicine, climate science, and catalysis."
        ),
    },
    {
        "name": _EAS,
        "sort_order": 3,
        "description": (
            "Engineering and Applied Science spans aerospace, applied physics, "
            "computing and mathematical sciences, electrical engineering, materials "
            "science, medical engineering, environmental science and engineering, "
            "and mechanical and civil engineering — and is home to Caltech's "
            "Computing and Mathematical Sciences (CMS) department."
        ),
    },
    {
        "name": _GPS,
        "sort_order": 4,
        "description": (
            "Geological and Planetary Sciences studies the Earth and the solar "
            "system across environmental science and engineering, geobiology, "
            "geochemistry, geology, geophysics, and planetary science, supported by "
            "the Seismological Laboratory and major observational facilities."
        ),
    },
    {
        "name": _HSS,
        "sort_order": 5,
        "description": (
            "The Humanities and Social Sciences division offers options in "
            "economics, business, history, philosophy, and political science "
            "alongside doctoral programs in the social sciences — with particular "
            "strength in experimental and behavioral economics."
        ),
    },
    {
        "name": _PMA,
        "sort_order": 6,
        "description": (
            "Physics, Mathematics and Astronomy encompasses physics, mathematics, "
            "and astronomy and operates landmark facilities including LIGO, the "
            "Palomar Observatory, and the W. M. Keck Observatory — a center of "
            "theoretical physics, quantum information, and astrophysics."
        ),
    },
]

# Each division's official website (verified to resolve at author time).
_SCHOOL_WEBSITE: dict[str, str] = {
    _BBE: "https://www.bbe.caltech.edu/",
    _CCE: "https://www.cce.caltech.edu/",
    _EAS: "https://www.eas.caltech.edu/",
    _GPS: "https://www.gps.caltech.edu/",
    _HSS: "https://www.hss.caltech.edu/",
    _PMA: "https://pma.caltech.edu/",
}

# Rich, sourced About-tab content per division. Chairs + endowed-chair titles are
# quoted from each division's official catalog / chair-appointment page (verified
# 2026-06-10). Only the Division of Biology publishes an explicit founding year
# (1928); the other five divisions' founding years could not be verified from a
# first-party source and are honestly omitted (recorded in _ABOUT_OMITTED).
_ABOUT_DETAIL: dict[str, dict] = {
    _BBE: {
        "founded": 1928,
        "leadership": (
            "Paul W. Sternberg — Bren Professor of Biology; William K. Bowes Jr. "
            "Leadership Chair (chair since 2024)"
        ),
        "faculty": [
            {
                "name": "Frances H. Arnold",
                "title": (
                    "Linus Pauling Professor of Chemical Engineering, "
                    "Bioengineering & Biochemistry"
                ),
                "focus": "Directed evolution of enzymes (2018 Nobel Prize in Chemistry)",
            },
            {
                "name": "David J. Anderson",
                "title": "Seymour Benzer Professor of Biology; HHMI Investigator",
                "focus": "Neural circuits of emotion and behavior",
            },
            {
                "name": "Elliot M. Meyerowitz",
                "title": "George W. Beadle Professor of Biology; HHMI Investigator",
                "focus": "Plant developmental biology",
            },
        ],
        "research_centers": [
            "Beckman Institute",
            "Tianqiao and Chrissy Chen Institute for Neuroscience",
            "Merkin Institute for Translational Research",
            "Center for Environmental Microbial Interactions (CEMI)",
        ],
        "named_for": None,
        "source": {
            "label": "Caltech BBE — History",
            "url": "https://www.bbe.caltech.edu/about-menu/history",
        },
    },
    _CCE: {
        "leadership": (
            "Sarah E. Reisman — Norman Davidson Leadership Chair, Division of "
            "Chemistry and Chemical Engineering"
        ),
        "faculty": [
            {
                "name": "Frances H. Arnold",
                "title": (
                    "Linus Pauling Professor of Chemical Engineering, "
                    "Bioengineering & Biochemistry"
                ),
                "focus": "Directed evolution (2018 Nobel Prize in Chemistry)",
            },
            {
                "name": "Rudolph A. Marcus",
                "title": "John G. Kirkwood and Arthur A. Noyes Professor of Chemistry",
                "focus": "Theory of electron-transfer reactions (1992 Nobel Prize in Chemistry)",
            },
        ],
        "research_centers": [
            "Rudolph A. Marcus Center for Theoretical Chemistry",
            "Center for Catalysis and Chemical Synthesis (3CS)",
            "Donna and Benjamin M. Rosen Bioengineering Center",
        ],
        "named_for": None,
        "source": {
            "label": "Caltech CCE — Division",
            "url": "https://www.cce.caltech.edu/",
        },
    },
    _EAS: {
        "leadership": (
            "Harry A. Atwater, Jr. — Otis Booth Leadership Chair; Howard Hughes "
            "Professor of Applied Physics and Materials Science (chair since 2021)"
        ),
        "faculty": [
            {
                "name": "Kerry J. Vahala",
                "title": (
                    "Ted and Ginger Jenkins Professor of Information Science & "
                    "Technology and Applied Physics"
                ),
                "focus": "Photonics and optical microresonators",
            },
            {
                "name": "Tim Colonius",
                "title": (
                    "Cecil and Sally Drinkward Leadership Chair; Executive "
                    "Officer for Mechanical & Civil Engineering"
                ),
                "focus": "Computational fluid dynamics",
            },
        ],
        "research_centers": [
            "Kavli Nanoscience Institute (KNI)",
            "Keck Institute for Space Studies (KISS)",
            "Center for Autonomous Systems and Technologies (CAST)",
        ],
        "named_for": None,
        "source": {
            "label": "Caltech EAS — Division",
            "url": "https://www.eas.caltech.edu/",
        },
    },
    _GPS: {
        "leadership": (
            "John M. Eiler — Robert P. Sharp Professor of Geology and Geochemistry; "
            "Ted and Ginger Jenkins Leadership Chair (chair since 2024)"
        ),
        "faculty": [
            {
                "name": "Michael E. Brown",
                "title": "Richard and Barbara Rosenberg Professor of Planetary Astronomy",
                "focus": "Outer solar system; discovery of dwarf planets",
            },
            {
                "name": "Shrinivas R. Kulkarni",
                "title": "George Ellery Hale Professor of Astronomy and Planetary Science",
                "focus": "Time-domain astronomy and transients",
            },
        ],
        "research_centers": [
            "Seismological Laboratory",
            "Linde Center for Global Environmental Science",
            "Caltech Center for Comparative Planetary Evolution (3CPE)",
        ],
        "named_for": None,
        "source": {
            "label": "Caltech GPS — Division",
            "url": "https://www.gps.caltech.edu/",
        },
    },
    _HSS: {
        "leadership": (
            "Tracy K. Dennison — Edie and Lew Wasserman Professor of Social Science "
            "History; Ronald and Maxine Linde Leadership Chair (chair since 2022)"
        ),
        "faculty": [
            {
                "name": "Colin F. Camerer",
                "title": "Robert Kirby Professor of Behavioral Economics",
                "focus": "Behavioral and neuroeconomics",
            },
            {
                "name": "Jed Z. Buchwald",
                "title": "Doris and Henry Dreyfuss Professor of History",
                "focus": "History of science",
            },
        ],
        "research_centers": [
            "T&C Chen Center for Social and Decision Neuroscience",
        ],
        "named_for": None,
        "source": {
            "label": "Caltech HSS — Division",
            "url": "https://www.hss.caltech.edu/",
        },
    },
    _PMA: {
        "leadership": (
            "Hirosi Ooguri — Fred Kavli Professor of Theoretical Physics and "
            "Mathematics; Kent and Joyce Kresa Leadership Chair (chair since 2025)"
        ),
        "faculty": [
            {
                "name": "John P. Preskill",
                "title": "Richard P. Feynman Professor of Theoretical Physics",
                "focus": "Quantum information and quantum computing",
            },
            {
                "name": "H. David Politzer",
                "title": "Richard Chace Tolman Professor of Theoretical Physics",
                "focus": "Quantum chromodynamics (2004 Nobel Prize in Physics)",
            },
        ],
        "research_centers": [
            "Walter Burke Institute for Theoretical Physics",
            "Institute for Quantum Information and Matter (IQIM)",
            "Keck Institute for Space Studies (KISS)",
        ],
        "named_for": None,
        "source": {
            "label": "Caltech PMA — Division",
            "url": "https://pma.caltech.edu/",
        },
    },
}

# About-detail fields omitted per division (verified-unavailable), recorded in each
# division node's _standard.omitted. Only the Division of Biology publishes a
# first-party founding year; the rest are honestly omitted.
_ABOUT_OMITTED: dict[str, list[str]] = {
    _CCE: ["about_detail.founded"],
    _EAS: ["about_detail.founded"],
    _GPS: ["about_detail.founded"],
    _HSS: ["about_detail.founded"],
    _PMA: ["about_detail.founded"],
}

# ── Per-node content feeds (so EVERY division + program has a populated Events &
# Updates tab, not just the CS flagship) ───────────────────────────────────────
# Caltech News Atom feed (www.caltech.edu/about/news/rss/) is server-fetchable
# (HTTP 200, verified 2026-06-11) and carries enclosure cover images. Campus-
# events items are filtered from the same feed via the official ``campus events``
# tag RSS URL (verified 2026-06-11).
_CALTECH_NEWS_RSS = "https://www.caltech.edu/about/news/rss/"
_CALTECH_EVENTS_FEED = {
    "url": "https://www.caltech.edu/about/news/rss?tag=campus%20events",
    "type": "rss",
}
_SOCIAL_CALTECH = {
    "instagram": "https://www.instagram.com/caltech/",
    "linkedin": "https://www.linkedin.com/school/california-institute-of-technology/",
    "x": "https://x.com/Caltech",
    "youtube": "https://www.youtube.com/caltech",
    "facebook": "https://www.facebook.com/californiainstituteoftechnology",
}

_INSTITUTION_CONTENT: dict = {
    "news_rss": _CALTECH_NEWS_RSS,
    "news_url": "https://www.caltech.edu/about/news",
    "news_curated": False,
    "events_feed": dict(_CALTECH_EVENTS_FEED),
    "social": dict(_SOCIAL_CALTECH),
}

# Keywords filter the shared Caltech feed to division-relevant items (the MIT/MBAn
# pattern). They are filter terms drawn from each division's official name + fields.
_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _BBE: ["biology", "biological engineering", "neuroscience", "BBE", "genetics"],
    _CCE: ["chemistry", "chemical engineering", "CCE", "catalysis"],
    _EAS: [
        "engineering",
        "applied science",
        "electrical engineering",
        "mechanical engineering",
        "aerospace",
        "CMS",
        "computing",
    ],
    _GPS: [
        "geological",
        "planetary",
        "geophysics",
        "GPS",
        "seismology",
        "environmental science",
    ],
    _HSS: ["humanities", "social sciences", "economics", "political science", "HSS"],
    _PMA: ["physics", "mathematics", "astronomy", "PMA", "LIGO", "astrophysics"],
}

_KW_STOP = {"and", "of", "the", "in", "for", "with", "science", "sciences", "engineering"}


def _school_content(name: str) -> dict:
    """A division's content_sources: Caltech News RSS + campus-events feed filtered by keywords."""
    return {
        "news_rss": _CALTECH_NEWS_RSS,
        "news_url": _SCHOOL_WEBSITE.get(name, "https://www.caltech.edu"),
        "news_curated": False,
        "events_feed": dict(_CALTECH_EVENTS_FEED),
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": dict(_SOCIAL_CALTECH),
    }


def _program_keywords(spec: dict) -> list[str]:
    school_kw = list(_SCHOOL_KEYWORDS[spec["school"]])
    name = spec["program_name"].replace("&", " ").replace("/", " ")
    terms = [w for w in name.split() if len(w) > 3 and w.lower() not in _KW_STOP]
    program_term = " ".join(terms[:3]).strip()
    return ([program_term] if program_term else []) + school_kw


def _program_content(spec: dict) -> dict:
    """A program's content_sources: its division's shared feed refined by program keywords."""
    base = _school_content(spec["school"])
    base["keywords"] = _program_keywords(spec)
    return base


# Computer Science keyword-relevant feed (the flagship program) — CMS department
# page + shared Caltech News RSS with CS-specific keywords.
_CS_CONTENT: dict = {
    "news_rss": _CALTECH_NEWS_RSS,
    "news_url": "https://www.cms.caltech.edu/",
    "news_curated": False,
    "events_feed": dict(_CALTECH_EVENTS_FEED),
    "keywords": [
        "computer science",
        "computing and mathematical sciences",
        "CMS",
        "electrical engineering",
        "information and data sciences",
    ],
    "social": dict(_SOCIAL_CALTECH),
}

# ── The program catalog (real degree programs, organized by division) ───────
# slug = idempotency key. degree_type ∈ {bachelors, phd}. Caltech is overwhelmingly
# PhD-focused for graduate study and awards few terminal master's (most M.S. degrees
# are milestones en route to the Ph.D.), so graduate programs are modeled as fully
# funded PhDs. Options are grounded in the official Caltech catalog
# (catalog.caltech.edu) and the Graduate Office option list; none are invented.
PROGRAMS: list[dict] = [
    # ── Engineering and Applied Science ──
    {
        "slug": "caltech-cs-bs",
        "school": _EAS,
        "program_name": "Computer Science",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Caltech's most-awarded undergraduate option — CS theory, systems, and AI.",
    },
    {
        "slug": "caltech-cs-phd",
        "school": _EAS,
        "program_name": "Computer Science",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "A fully funded research doctorate in computer science (CMS department).",
    },
    {
        "slug": "caltech-ee-bs",
        "school": _EAS,
        "program_name": "Electrical Engineering",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "BS in Electrical Engineering — devices, signals, and systems.",
    },
    {
        "slug": "caltech-ee-phd",
        "school": _EAS,
        "program_name": "Electrical Engineering",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "A fully funded research doctorate in electrical engineering.",
    },
    {
        "slug": "caltech-me-bs",
        "school": _EAS,
        "program_name": "Mechanical Engineering",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "BS in Mechanical Engineering — mechanics, design, and thermal sciences.",
    },
    {
        "slug": "caltech-me-phd",
        "school": _EAS,
        "program_name": "Mechanical Engineering",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "A fully funded research doctorate in mechanical engineering.",
    },
    {
        "slug": "caltech-aph-bs",
        "school": _EAS,
        "program_name": "Applied Physics",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "BS in Applied Physics — physics applied to engineering problems.",
    },
    {
        "slug": "caltech-acm-bs",
        "school": _EAS,
        "program_name": "Applied and Computational Mathematics",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "BS in Applied and Computational Mathematics — modeling and computation.",
    },
    {
        "slug": "caltech-ids-bs",
        "school": _EAS,
        "program_name": "Information and Data Sciences",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "BS in Information and Data Sciences — data, learning, and information.",
    },
    {
        "slug": "caltech-mse-bs",
        "school": _EAS,
        "program_name": "Materials Science",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "BS in Materials Science — structure, properties, and processing.",
    },
    {
        "slug": "caltech-aero-phd",
        "school": _EAS,
        "program_name": "Aeronautics",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "A fully funded research doctorate in aeronautics (GALCIT).",
    },
    {
        "slug": "caltech-cms-phd",
        "school": _EAS,
        "program_name": "Computing and Mathematical Sciences",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "A fully funded research doctorate in computing and mathematical sciences.",
    },
    # ── Biology and Biological Engineering ──
    {
        "slug": "caltech-biology-bs",
        "school": _BBE,
        "program_name": "Biology",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "BS in Biology — molecular, cellular, organismal, and neuro-biology.",
    },
    {
        "slug": "caltech-biology-phd",
        "school": _BBE,
        "program_name": "Biology",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "A fully funded research doctorate in biology.",
    },
    {
        "slug": "caltech-bioengineering-bs",
        "school": _BBE,
        "program_name": "Bioengineering",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "BS in Bioengineering — engineering at the interface with biology.",
    },
    {
        "slug": "caltech-bioengineering-phd",
        "school": _BBE,
        "program_name": "Bioengineering",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "A fully funded research doctorate in bioengineering.",
    },
    {
        "slug": "caltech-cns-phd",
        "school": _BBE,
        "program_name": "Computation and Neural Systems",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "A fully funded research doctorate bridging neuroscience and computation.",
    },
    # ── Chemistry and Chemical Engineering ──
    {
        "slug": "caltech-chemistry-bs",
        "school": _CCE,
        "program_name": "Chemistry",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "BS in Chemistry — organic, inorganic, physical, and theoretical chemistry.",
    },
    {
        "slug": "caltech-chemistry-phd",
        "school": _CCE,
        "program_name": "Chemistry",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "A fully funded research doctorate in chemistry.",
    },
    {
        "slug": "caltech-cheme-bs",
        "school": _CCE,
        "program_name": "Chemical Engineering",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "BS in Chemical Engineering — reaction engineering and process design.",
    },
    {
        "slug": "caltech-cheme-phd",
        "school": _CCE,
        "program_name": "Chemical Engineering",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "A fully funded research doctorate in chemical engineering.",
    },
    # ── Geological and Planetary Sciences ──
    {
        "slug": "caltech-gps-bs",
        "school": _GPS,
        "program_name": "Geological and Planetary Sciences",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "BS in Geological and Planetary Sciences — Earth and planetary science.",
    },
    {
        "slug": "caltech-planetary-phd",
        "school": _GPS,
        "program_name": "Planetary Science",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "A fully funded research doctorate in planetary science.",
    },
    {
        "slug": "caltech-geophysics-phd",
        "school": _GPS,
        "program_name": "Geophysics",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "A fully funded research doctorate in geophysics.",
    },
    {
        "slug": "caltech-ese-phd",
        "school": _GPS,
        "program_name": "Environmental Science and Engineering",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "A fully funded doctorate in environmental science and engineering.",
    },
    # ── Humanities and Social Sciences ──
    {
        "slug": "caltech-bem-bs",
        "school": _HSS,
        "program_name": "Business, Economics, and Management",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "BS in Business, Economics, and Management — quantitative economics.",
    },
    {
        "slug": "caltech-economics-bs",
        "school": _HSS,
        "program_name": "Economics",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "BS in Economics — micro, macro, and econometrics with a quantitative core.",
    },
    {
        "slug": "caltech-polisci-bs",
        "school": _HSS,
        "program_name": "Political Science",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "BS in Political Science — formal and quantitative political analysis.",
    },
    {
        "slug": "caltech-social-science-phd",
        "school": _HSS,
        "program_name": "Social Science",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "A fully funded research doctorate in the social sciences.",
    },
    # ── Physics, Mathematics and Astronomy ──
    {
        "slug": "caltech-physics-bs",
        "school": _PMA,
        "program_name": "Physics",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "BS in Physics — Caltech's signature rigorous physics curriculum.",
    },
    {
        "slug": "caltech-physics-phd",
        "school": _PMA,
        "program_name": "Physics",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "A fully funded research doctorate in physics.",
    },
    {
        "slug": "caltech-math-bs",
        "school": _PMA,
        "program_name": "Mathematics",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "BS in Mathematics — pure and applied, with deep research access.",
    },
    {
        "slug": "caltech-math-phd",
        "school": _PMA,
        "program_name": "Mathematics",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "A fully funded research doctorate in mathematics.",
    },
    {
        "slug": "caltech-astrophysics-bs",
        "school": _PMA,
        "program_name": "Astrophysics",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "BS in Astrophysics — observational and theoretical astrophysics.",
    },
]

# CIP codes for explicit catalog entries — used to dedupe against the IPEDS breadth list.
_CIP_BY_SLUG: dict[str, str] = {
    "caltech-cs-bs": "11.07",
    "caltech-cs-phd": "11.07",
    "caltech-ee-bs": "14.10",
    "caltech-ee-phd": "14.10",
    "caltech-me-bs": "14.19",
    "caltech-me-phd": "14.19",
    "caltech-aph-bs": "14.12",
    "caltech-acm-bs": "27.03",
    "caltech-ids-bs": "11.04",
    "caltech-mse-bs": "14.18",
    "caltech-aero-phd": "14.02",
    "caltech-cms-phd": "11.07",
    "caltech-biology-bs": "26.01",
    "caltech-biology-phd": "26.01",
    "caltech-bioengineering-bs": "14.05",
    "caltech-bioengineering-phd": "14.05",
    "caltech-cns-phd": "26.11",
    "caltech-chemistry-bs": "40.05",
    "caltech-chemistry-phd": "40.05",
    "caltech-cheme-bs": "14.07",
    "caltech-cheme-phd": "14.07",
    "caltech-gps-bs": "40.06",
    "caltech-planetary-phd": "40.06",
    "caltech-geophysics-phd": "40.06",
    "caltech-ese-phd": "14.14",
    "caltech-bem-bs": "52.02",
    "caltech-economics-bs": "45.06",
    "caltech-polisci-bs": "45.10",
    "caltech-social-science-phd": "45.99",
    "caltech-physics-bs": "40.08",
    "caltech-physics-phd": "40.08",
    "caltech-math-bs": "27.01",
    "caltech-math-phd": "27.01",
    "caltech-astrophysics-bs": "40.02",
}
for _p in PROGRAMS:
    if _p["slug"] in _CIP_BY_SLUG:
        _p.setdefault("cip", _CIP_BY_SLUG[_p["slug"]])
    _p.setdefault("delivery_format", "in_person")

_EXPLICIT_DEPARTMENTS: dict[str, str] = {
    "caltech-cs-bs": "Computing and Mathematical Sciences",
    "caltech-cs-phd": "Computing and Mathematical Sciences",
    "caltech-ee-bs": "Electrical Engineering",
    "caltech-ee-phd": "Electrical Engineering",
    "caltech-me-bs": "Mechanical Engineering",
    "caltech-me-phd": "Mechanical Engineering",
    "caltech-aph-bs": "Applied Physics",
    "caltech-acm-bs": "Applied and Computational Mathematics",
    "caltech-ids-bs": "Information and Data Sciences",
    "caltech-mse-bs": "Materials Science",
    "caltech-aero-phd": "Aeronautics",
    "caltech-cms-phd": "Computing and Mathematical Sciences",
    "caltech-biology-bs": "Biology and Biological Engineering",
    "caltech-biology-phd": "Biology and Biological Engineering",
    "caltech-bioengineering-bs": "Bioengineering",
    "caltech-bioengineering-phd": "Bioengineering",
    "caltech-cns-phd": "Computation and Neural Systems",
    "caltech-chemistry-bs": "Chemistry",
    "caltech-chemistry-phd": "Chemistry",
    "caltech-cheme-bs": "Chemical Engineering",
    "caltech-cheme-phd": "Chemical Engineering",
    "caltech-gps-bs": "Geological and Planetary Sciences",
    "caltech-planetary-phd": "Planetary Science",
    "caltech-geophysics-phd": "Geophysics",
    "caltech-ese-phd": "Environmental Science and Engineering",
    "caltech-bem-bs": "Business, Economics, and Management",
    "caltech-economics-bs": "Economics",
    "caltech-polisci-bs": "Political Science",
    "caltech-social-science-phd": "Social Science",
    "caltech-physics-bs": "Physics",
    "caltech-physics-phd": "Physics",
    "caltech-math-bs": "Mathematics",
    "caltech-math-phd": "Mathematics",
    "caltech-astrophysics-bs": "Astrophysics",
}
for _p in PROGRAMS:
    if _p["slug"] in _EXPLICIT_DEPARTMENTS:
        _p["department"] = _EXPLICIT_DEPARTMENTS[_p["slug"]]

# Full official degree names (program-page title in place of the short label).
_FULL_NAME_BY_SLUG: dict[str, str] = {
    "caltech-cs-bs": "Bachelor of Science in Computer Science",
    "caltech-cs-phd": "Doctor of Philosophy in Computer Science",
    "caltech-ee-bs": "Bachelor of Science in Electrical Engineering",
    "caltech-ee-phd": "Doctor of Philosophy in Electrical Engineering",
    "caltech-me-bs": "Bachelor of Science in Mechanical Engineering",
    "caltech-me-phd": "Doctor of Philosophy in Mechanical Engineering",
    "caltech-aph-bs": "Bachelor of Science in Applied Physics",
    "caltech-acm-bs": "Bachelor of Science in Applied and Computational Mathematics",
    "caltech-ids-bs": "Bachelor of Science in Information and Data Sciences",
    "caltech-mse-bs": "Bachelor of Science in Materials Science",
    "caltech-aero-phd": "Doctor of Philosophy in Aeronautics",
    "caltech-cms-phd": "Doctor of Philosophy in Computing and Mathematical Sciences",
    "caltech-biology-bs": "Bachelor of Science in Biology",
    "caltech-biology-phd": "Doctor of Philosophy in Biology",
    "caltech-bioengineering-bs": "Bachelor of Science in Bioengineering",
    "caltech-bioengineering-phd": "Doctor of Philosophy in Bioengineering",
    "caltech-cns-phd": "Doctor of Philosophy in Computation and Neural Systems",
    "caltech-chemistry-bs": "Bachelor of Science in Chemistry",
    "caltech-chemistry-phd": "Doctor of Philosophy in Chemistry",
    "caltech-cheme-bs": "Bachelor of Science in Chemical Engineering",
    "caltech-cheme-phd": "Doctor of Philosophy in Chemical Engineering",
    "caltech-gps-bs": "Bachelor of Science in Geological and Planetary Sciences",
    "caltech-planetary-phd": "Doctor of Philosophy in Planetary Science",
    "caltech-geophysics-phd": "Doctor of Philosophy in Geophysics",
    "caltech-ese-phd": "Doctor of Philosophy in Environmental Science and Engineering",
    "caltech-bem-bs": "Bachelor of Science in Business, Economics, and Management",
    "caltech-economics-bs": "Bachelor of Science in Economics",
    "caltech-polisci-bs": "Bachelor of Science in Political Science",
    "caltech-social-science-phd": "Doctor of Philosophy in Social Science",
    "caltech-physics-bs": "Bachelor of Science in Physics",
    "caltech-physics-phd": "Doctor of Philosophy in Physics",
    "caltech-math-bs": "Bachelor of Science in Mathematics",
    "caltech-math-phd": "Doctor of Philosophy in Mathematics",
    "caltech-astrophysics-bs": "Bachelor of Science in Astrophysics",
}
for _p in PROGRAMS:
    if _p["slug"] in _FULL_NAME_BY_SLUG:
        _p["program_name"] = _FULL_NAME_BY_SLUG[_p["slug"]]

# IPEDS rows that duplicate an explicit Caltech option already in PROGRAMS.
_IPEDS_SKIP_SLUGS = frozenset({
    "caltech-business-managerial-economics-bs",  # same as caltech-bem-bs
})

_EXISTING_SLUGS = {p["slug"] for p in PROGRAMS}
_EXISTING_CIP_KEYS = {(p.get("cip"), p["degree_type"]) for p in PROGRAMS if p.get("cip")}

# Federal CIP field titles → Caltech's published option / department names.
_CIP_TO_DEPARTMENT: dict[str, str] = {
    "Computer Science": "Computing and Mathematical Sciences",
    "Information Science/Studies": "Information and Data Sciences",
    "Engineering, General": "Engineering and Applied Science",
    "Aerospace, Aeronautical, and Astronautical/Space Engineering": "Aeronautics",
    "Biomedical/Medical Engineering": "Bioengineering",
    "Chemical Engineering": "Chemical Engineering",
    "Civil Engineering": "Civil Engineering",
    "Electrical, Electronics, and Communications Engineering": "Electrical Engineering",
    "Engineering Mechanics": "Engineering Mechanics",
    "Engineering Physics": "Applied Physics",
    "Environmental/Environmental Health Engineering": "Environmental Science and Engineering",
    "Materials Engineering": "Materials Science",
    "Mechanical Engineering": "Mechanical Engineering",
    "Systems Engineering": "Systems Engineering",
    "English Language and Literature, General": "English",
    "Biology, General": "Biology",
    "Biochemistry, Biophysics and Molecular Biology": "Biochemistry and Molecular Biophysics",
    "Cell/Cellular Biology and Anatomical Sciences": "Cell and Developmental Biology",
    "Microbiological Sciences and Immunology": "Microbiology",
    "Genetics": "Genetics",
    "Neurobiology and Neurosciences": "Neuroscience",
    "Mathematics": "Mathematics",
    "Applied Mathematics": "Applied and Computational Mathematics",
    "Mathematics and Computer Science": "Mathematics and Computer Science",
    "Multi/Interdisciplinary Studies, Other": "Individualized Studies",
    "Philosophy": "Philosophy",
    "Astronomy and Astrophysics": "Astrophysics",
    "Chemistry": "Chemistry",
    "Geological and Earth Sciences/Geosciences": "Geological and Planetary Sciences",
    "Physics": "Physics",
    "Economics": "Economics",
    "Political Science and Government": "Political Science",
    "Business/Managerial Economics": "Business, Economics, and Management",
    "History": "History",
}


def _department_for(field_name: str, school: str) -> str:
    """Owning department — map federal CIP titles to Caltech option names."""
    mapped = _CIP_TO_DEPARTMENT.get(field_name, field_name)
    if mapped.lower() in school.lower() or school.lower() in mapped.lower():
        return school
    return mapped


def _caltech_program_name(field_name: str, degree_type: str, school: str) -> str:
    """Real Caltech degree designation — never a CIP-rollup credential prefix."""
    option = _CIP_TO_DEPARTMENT.get(field_name, field_name)
    if degree_type == "bachelors":
        return f"Bachelor of Science in {option}"
    if degree_type == "masters":
        return f"Master of Science in {option}"
    if degree_type == "certificate":
        return f"Graduate Certificate in {option}"
    if degree_type == "phd":
        return f"Doctor of Philosophy in {option}"
    return option


def _field_from_program_name(program_name: str) -> str | None:
    for prefix in (
        "Bachelor of Science in ",
        "Master of Science in ",
        "Doctor of Philosophy in ",
        "Graduate Certificate in ",
        "Bachelor's in ",
        "Master's in ",
    ):
        if program_name.startswith(prefix):
            return program_name[len(prefix):]
    return None


def _needs_normalize(desc: str, program_name: str = "") -> bool:
    if not desc:
        return True
    if program_name and desc.startswith(program_name):
        return True
    if _CLASSIFICATION_STUB_RE.match(desc):
        return True
    if _TEMPLATE_STUB_RE.search(desc):
        return True
    return "offered through the " in desc


def _caltech_description(spec: dict, field: str | None = None) -> str:
    """Field-specific description — never the degree-type classification stub."""
    slug = spec["slug"]
    fmt = spec.get("delivery_format", "in_person")
    delivery = ""
    if fmt == "online":
        delivery = " Delivered online."
    elif fmt == "hybrid":
        delivery = " Delivered in a hybrid format."
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
    spec["description"] = _caltech_description(spec, field=field_name)


def _build_catalog() -> list[dict]:
    """Append breadth-first program nodes from the College Scorecard Field-of-Study list."""
    out: list[dict] = []
    seen = set(_EXISTING_SLUGS)
    for slug, school, name, dtype, cip, dur, fmt, _desc in _IPEDS_CATALOG:
        if slug in seen or slug in _IPEDS_SKIP_SLUGS:
            continue
        if (cip, dtype) in _EXISTING_CIP_KEYS:
            continue
        pname_candidate = _caltech_program_name(name, dtype, school)
        if any(p["program_name"] == pname_candidate for p in PROGRAMS + out):
            continue
        seen.add(slug)
        dept = _department_for(name, school)
        delivery = fmt if fmt in {"online", "hybrid"} else "in_person"
        pname = _caltech_program_name(name, dtype, school)
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
    if _p["slug"] in _FULL_NAME_BY_SLUG:
        _p["program_name"] = _FULL_NAME_BY_SLUG[_p["slug"]]
    _normalize_program(_p)

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
_prefix_names = sum(1 for p in PROGRAMS if _PREFIX_NAME_RE.match(p.get("program_name", "")))
if _prefix_names:
    _catalog_errors.append(f"CIP-prefix program_name on {_prefix_names} programs")
if _catalog_errors:
    raise RuntimeError(f"Caltech catalog quality gate failed: {_catalog_errors}")

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

# Official program/option home pages. The Computer Science option has its own
# verified catalog page; the other options use their owning division's official
# site (the authoritative home for the option) and the Graduate Office for PhDs —
# all verified to resolve at author time.
_CS_OPTION_URL = (
    "https://catalog.caltech.edu/current/information-for-undergraduate-students/"
    "graduation-requirements-all-options/computer-science-option-and-minor-cs/"
)
_GRAD_OPTIONS_URL = "https://gradoffice.caltech.edu/academics/optionreps"
_WEBSITE_BY_SLUG: dict[str, str] = {
    "caltech-cs-bs": _CS_OPTION_URL,
    "caltech-cs-phd": "https://www.cms.caltech.edu/academics/grad/grad_cs",
}

# ── Who-it's-for + highlights, by degree type (catalog fallbacks) ──────────
_WHO_BY_TYPE = {
    "bachelors": "Undergraduates seeking a deeply rigorous grounding in science and engineering.",
    "phd": "Aspiring scholars pursuing an academic or research career (fully funded).",
}
_HL_BY_TYPE = {
    "bachelors": ["Core curriculum", "3:1 student-faculty ratio", "Undergraduate research (SURF)"],
    "phd": ["Full funding & stipend", "World-class advisors", "Research apprenticeship"],
}
_WHO_BY_SLUG = {
    "caltech-cs-bs": (
        "Technically exceptional undergraduates who want a deeply rigorous CS "
        "education — theory, systems, and AI — with early access to faculty research."
    ),
}
_HL_BY_SLUG = {
    "caltech-cs-bs": ["Most-awarded option", "Six project tracks", "CMS faculty & research"],
}

# ── Curriculum / tracks, where published (the flagship) ────────────────────
# Caltech's CS option page publishes its requirement structure and six "project
# sequences" (specialization tracks). Quoted from the official option page.
_TRACKS_BY_SLUG: dict[str, dict] = {
    "caltech-cs-bs": {
        "label": "Project-sequence tracks",
        "note": (
            "The Computer Science option builds on a CS fundamentals and "
            "intermediate core, then a required three-quarter project sequence "
            "chosen from six specialization areas, plus advanced CS, mathematical, "
            "and communication requirements."
        ),
        "items": [
            {"name": "Graphics"},
            {"name": "Learning & Vision"},
            {"name": "Networks & Communication"},
            {"name": "Quantum & Molecular Computing"},
            {"name": "Robotics"},
            {"name": "Programming Languages"},
        ],
        "source": "Caltech Catalog — Computer Science Option (CS)",
        "source_url": _CS_OPTION_URL,
    },
}

# ── Program-specific cost (official published rates) ───────────────────────
# Caltech full-time tuition (College Scorecard, UNITID 110404). PhDs are fully
# funded (tuition + stipend). Undergraduates pay the published tuition; total cost
# of attendance is the Scorecard academic-year COA.
_TUITION_UNDERGRAD = 65898
_UNDERGRAD_COA = 86886
_COST_BY_SLUG: dict[str, dict] = {}

# ── Program-specific outcomes ──────────────────────────────────────────────
# Caltech does NOT publish per-program employment reports, so no program carries
# employment_rate / top_industries / a methodology block (those are recorded as
# omitted per program). Where the federal College Scorecard publishes a Field-of-
# Study median earnings for an awarded CIP at UNITID 110404, we use it (program
# scope); otherwise programs fall back to the institution-wide 10-year median.
# Only Computer Science (CIP 11.07, bachelor's) has a non-suppressed FOS figure.
_FOS_OUTCOMES: dict[str, tuple[int, str]] = {
    "caltech-cs-bs": (129693, "11.07"),
}

# Institution-wide outcomes fallback (College Scorecard, UNITID 110404), used for
# degree programs without a published program-level report or FOS earnings.
_OUTCOMES_INSTITUTION = {
    "median_salary": 128566,
    "scope": "institution",
    "note": "Caltech institution-wide median earnings 10 years after entry.",
    "source": "U.S. Dept. of Education College Scorecard (UNITID 110404)",
    "source_url": "https://collegescorecard.ed.gov/school/?110404",
}

# ── Class profile, where published (the flagship) ──────────────────────────
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    "caltech-cs-bs": {
        "cohort_size": "≈67 bachelor's degrees awarded annually (Caltech's most-awarded option)",
        "note": (
            "Caltech does not publish per-option cohort sizes; the figure is the "
            "annual count of CS bachelor's degrees awarded (College Scorecard "
            "Field of Study, CIP 11.07), the largest of any Caltech option."
        ),
        "source": "U.S. Dept. of Education College Scorecard — Field of Study (CIP 11.07)",
        "source_url": "https://collegescorecard.ed.gov/school/?110404",
    },
}

# ── Faculty (lead + directory link), where confidently sourced ─────────────
_FACULTY_BY_SLUG: dict[str, dict] = {
    "caltech-cs-bs": {
        "lead": [
            {
                "name": "Christopher Umans",
                "title": (
                    "Professor of Computer Science; Coughran Leadership Chair, "
                    "CMS; Executive Officer for CMS"
                ),
            },
            {
                "name": "Leonard J. Schulman",
                "title": "Professor of Computer Science; Graduate Option Representative for CS",
            },
            {
                "name": "Erik Winfree",
                "title": (
                    "Professor of Computer Science, Computation and Neural "
                    "Systems, and Bioengineering"
                ),
            },
        ],
        "note": "Taught by Caltech Computing and Mathematical Sciences (CMS) faculty.",
        "directory_url": "https://www.cms.caltech.edu/people/faculty",
    },
}

# ── Aggregated, cited student-review themes (≥2 third-party sources) ────────
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "caltech-cs-bs": {
        "summary": (
            "Students and third-party guides consistently describe Caltech CS as "
            "extraordinarily rigorous, with small classes, deep faculty access, and "
            "strong research and industry placement; the most common cautions are "
            "the intense, problem-set-heavy workload and the very small, "
            "high-pressure environment."
        ),
        "themes": [
            {
                "label": "Academic rigor",
                "sentiment": "positive",
                "detail": "A demanding core and CS curriculum among the most rigorous anywhere.",
            },
            {
                "label": "Faculty access & research",
                "sentiment": "positive",
                "detail": "A 3:1 student-faculty ratio and early research (SURF) access.",
            },
            {
                "label": "Strong tech placement",
                "sentiment": "positive",
                "detail": "Graduates place strongly into top technology firms and PhD programs.",
            },
            {
                "label": "Intense workload",
                "sentiment": "caution",
                "detail": "A heavy, problem-set-driven course load is a recurring theme.",
            },
            {
                "label": "Very small environment",
                "sentiment": "caution",
                "detail": "Fewer than 1,000 undergraduates: a small, high-pressure community.",
            },
        ],
        "sources": [
            {
                "label": "Niche — California Institute of Technology",
                "url": "https://www.niche.com/colleges/california-institute-of-technology/",
            },
            {
                "label": "U.S. News — Caltech Computer Science",
                "url": "https://www.usnews.com/best-colleges/california-institute-of-technology-1131",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "caltech-ee-bs": {
        "summary": (
            "Students and third-party guides describe Caltech electrical engineering as "
            "among the most rigorous undergraduate EE programs in the United States — "
            "U.S. News ranks Caltech No. 11 among National Universities (2026) with "
            "leading engineering research — praising small classes, early lab access, and "
            "ties to JPL and campus quantum institutes; common cautions are the "
            "problem-set-heavy core, limited course variety versus larger schools, and "
            "the intense pace shared across all Caltech majors."
        ),
        "themes": [
            {
                "label": "Rigorous EE core",
                "sentiment": "positive",
                "detail": (
                    "A mathematically demanding curriculum with hands-on labs from the "
                    "Division of Engineering and Applied Science."
                ),
            },
            {
                "label": "Research & JPL ties",
                "sentiment": "positive",
                "detail": (
                    "Undergraduates access SURF research and Caltech-managed JPL "
                    "facilities on aerospace and communications projects."
                ),
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "A 3:1 student-faculty ratio supports close mentoring in a tiny cohort.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": (
                    "Long problem sets and a fast quarter system are recurring themes in "
                    "student guides."
                ),
            },
            {
                "label": "Small-program trade-offs",
                "sentiment": "mixed",
                "detail": (
                    "Fewer elective breadth options than at large engineering colleges."
                ),
            },
        ],
        "sources": [
            {
                "label": "Niche — California Institute of Technology",
                "url": "https://www.niche.com/colleges/california-institute-of-technology/",
            },
            {
                "label": "Caltech — University and College Rankings",
                "url": "https://www.caltech.edu/about/university-and-college-rankings",
            },
            {
                "label": "Caltech — Electrical Engineering",
                "url": "https://www.ee.caltech.edu/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "caltech-me-bs": {
        "summary": (
            "Students and college guides consistently rank Caltech mechanical engineering "
            "among the nation's most selective and research-intensive undergraduate ME "
            "programs — Caltech reports mechanical engineering as one of its most popular "
            "majors — praising design-and-analysis depth, robotics and aerospace labs, and "
            "strong graduate-school placement; common cautions are the heavy physics and "
            "math core, limited class size, and an workload students describe as among "
            "the most demanding in the country."
        ),
        "themes": [
            {
                "label": "Design & analysis depth",
                "sentiment": "positive",
                "detail": (
                    "A quantitative ME curriculum spanning dynamics, thermodynamics, and "
                    "modern fabrication."
                ),
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": (
                    "Access to Caltech robotics, fluid mechanics, and materials labs from "
                    "undergraduate research programs."
                ),
            },
            {
                "label": "Graduate placement",
                "sentiment": "positive",
                "detail": (
                    "Many graduates continue to top PhD programs or aerospace and tech "
                    "roles."
                ),
            },
            {
                "label": "Core intensity",
                "sentiment": "caution",
                "detail": (
                    "Shared Caltech physics and math requirements create a heavy first two "
                    "years."
                ),
            },
            {
                "label": "Small cohort",
                "sentiment": "caution",
                "detail": (
                    "Fewer than 1,000 undergraduates campus-wide limits peer group size "
                    "within ME."
                ),
            },
        ],
        "sources": [
            {
                "label": "Niche — California Institute of Technology",
                "url": "https://www.niche.com/colleges/california-institute-of-technology/",
            },
            {
                "label": "Caltech — Mechanical and Civil Engineering",
                "url": "https://www.mce.caltech.edu/",
            },
            {
                "label": "Caltech — University and College Rankings",
                "url": "https://www.caltech.edu/about/university-and-college-rankings",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "caltech-physics-bs": {
        "summary": (
            "Students and guides universally describe Caltech physics as one of the world's "
            "premier undergraduate physics programs — home to LIGO, Nobel-laureate "
            "faculty, and a legacy of fundamental discovery — praising unmatched research "
            "access for undergraduates and theoretical depth; common cautions are extreme "
            "selectivity (~2.6% admit rate), a punishing problem-set culture, and that "
            "the program assumes exceptional mathematical preparation from day one."
        ),
        "themes": [
            {
                "label": "World-leading physics",
                "sentiment": "positive",
                "detail": (
                    "Caltech's Division of Physics, Mathematics and Astronomy anchors "
                    "facilities like LIGO and Palomar Observatory."
                ),
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": (
                    "SURF and faculty-led projects expose undergraduates to frontier "
                    "experiments early."
                ),
            },
            {
                "label": "Theoretical depth",
                "sentiment": "positive",
                "detail": (
                    "A mathematically rigorous curriculum spanning classical mechanics, "
                    "quantum theory, and modern physics."
                ),
            },
            {
                "label": "Selectivity & pace",
                "sentiment": "caution",
                "detail": (
                    "Admission is among the most competitive nationally; the quarter system "
                    "moves quickly."
                ),
            },
            {
                "label": "Math prerequisites",
                "sentiment": "caution",
                "detail": (
                    "Students report that strong multivariable calculus and linear algebra "
                    "are essential from the start."
                ),
            },
        ],
        "sources": [
            {
                "label": "Caltech — Division of Physics, Mathematics and Astronomy",
                "url": "https://www.pma.caltech.edu/",
            },
            {
                "label": "Caltech — University and College Rankings",
                "url": "https://www.caltech.edu/about/university-and-college-rankings",
            },
            {
                "label": "Niche — California Institute of Technology",
                "url": "https://www.niche.com/colleges/california-institute-of-technology/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "caltech-math-bs": {
        "summary": (
            "Students and academic guides describe Caltech mathematics as a deeply "
            "theoretical undergraduate major within a research powerhouse — Times Higher "
            "Education ranks Caltech seventh globally (2026) with leading physical-sciences "
            "strength — praising proof-based coursework, small seminars, and a pipeline to "
            "top PhD programs; common cautions are the abstract, fast-paced curriculum, "
            "limited applied-business pathways, and the shared Caltech workload that "
            "students call exceptionally demanding."
        ),
        "themes": [
            {
                "label": "Proof-based rigor",
                "sentiment": "positive",
                "detail": (
                    "A pure-mathematics core emphasizing analysis, algebra, and topology."
                ),
            },
            {
                "label": "Research culture",
                "sentiment": "positive",
                "detail": (
                    "Faculty in PMA and CMS collaborate on theory, computation, and "
                    "mathematical physics."
                ),
            },
            {
                "label": "PhD pipeline",
                "sentiment": "positive",
                "detail": (
                    "Graduates frequently continue to leading mathematics and quantitative "
                    "PhD programs."
                ),
            },
            {
                "label": "Abstract pace",
                "sentiment": "caution",
                "detail": (
                    "Courses move quickly through graduate-level material for undergraduates."
                ),
            },
            {
                "label": "Limited pre-professional focus",
                "sentiment": "mixed",
                "detail": (
                    "The major targets research careers more than corporate finance or "
                    "consulting tracks."
                ),
            },
        ],
        "sources": [
            {
                "label": "Caltech — Division of Physics, Mathematics and Astronomy",
                "url": "https://www.pma.caltech.edu/",
            },
            {
                "label": "Caltech — University and College Rankings",
                "url": "https://www.caltech.edu/about/university-and-college-rankings",
            },
            {
                "label": "Niche — California Institute of Technology",
                "url": "https://www.niche.com/colleges/california-institute-of-technology/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "caltech-chemistry-bs": {
        "summary": (
            "Students and third-party guides rank Caltech chemistry among the strongest "
            "undergraduate programs in the United States — the Division of Chemistry and "
            "Chemical Engineering hosts Nobel-caliber faculty and major research centers — "
            "praising early lab research, small classes, and depth in physical and synthetic "
            "chemistry; common cautions are long lab hours stacked on Caltech's heavy core, "
            "limited non-research career advising, and the pressure of a tiny, high-achieving "
            "peer group."
        ),
        "themes": [
            {
                "label": "Research-intensive labs",
                "sentiment": "positive",
                "detail": (
                    "Undergraduates join synthesis, catalysis, and chemical biology groups "
                    "through SURF and term-time research."
                ),
            },
            {
                "label": "Faculty depth",
                "sentiment": "positive",
                "detail": (
                    "A small division with direct access to leading experimental and "
                    "theoretical chemists."
                ),
            },
            {
                "label": "Graduate-school outcomes",
                "sentiment": "positive",
                "detail": (
                    "Most graduates pursue PhD programs or research careers in industry R&D."
                ),
            },
            {
                "label": "Lab workload",
                "sentiment": "caution",
                "detail": (
                    "Multi-hour lab sections on top of problem sets are a recurring theme."
                ),
            },
            {
                "label": "Narrow career services",
                "sentiment": "mixed",
                "detail": (
                    "Career paths skew toward academia and research labs versus large "
                    "corporate recruiting."
                ),
            },
        ],
        "sources": [
            {
                "label": "Caltech — Division of Chemistry and Chemical Engineering",
                "url": "https://www.cce.caltech.edu/",
            },
            {
                "label": "Niche — California Institute of Technology",
                "url": "https://www.niche.com/colleges/california-institute-of-technology/",
            },
            {
                "label": "Caltech — University and College Rankings",
                "url": "https://www.caltech.edu/about/university-and-college-rankings",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "caltech-cheme-bs": {
        "summary": (
            "Students and engineering guides describe Caltech chemical engineering as a "
            "small, elite program blending molecular science with quantitative transport "
            "and reaction engineering — U.S. News ranks Caltech among the top National "
            "Universities (No. 11, 2026) with leading engineering research output — "
            "praising faculty mentorship and interdisciplinary ties to chemistry and "
            "biology; common cautions are demanding thermodynamics and math prerequisites, "
            "a limited alumni network versus larger ChemE schools, and Caltech's "
            "notoriously heavy workload."
        ),
        "themes": [
            {
                "label": "Quantitative ChemE core",
                "sentiment": "positive",
                "detail": (
                    "Transport, thermodynamics, and reaction engineering taught with "
                    "rigorous mathematical modeling."
                ),
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": (
                    "Links to catalysis, bioengineering, and materials labs across CCE and "
                    "BBE."
                ),
            },
            {
                "label": "Small-class mentoring",
                "sentiment": "positive",
                "detail": (
                    "A tiny ChemE cohort enables close faculty advising and lab placement."
                ),
            },
            {
                "label": "Prerequisite intensity",
                "sentiment": "caution",
                "detail": (
                    "Shared Caltech physics and chemistry sequences are time-consuming."
                ),
            },
            {
                "label": "Career breadth",
                "sentiment": "mixed",
                "detail": (
                    "Placement skews toward PhD study and specialized R&D rather than "
                    "large-process engineering roles."
                ),
            },
        ],
        "sources": [
            {
                "label": "Caltech — Chemical Engineering",
                "url": "https://www.cce.caltech.edu/academics/chemical-engineering",
            },
            {
                "label": "Caltech — University and College Rankings",
                "url": "https://www.caltech.edu/about/university-and-college-rankings",
            },
            {
                "label": "Niche — California Institute of Technology",
                "url": "https://www.niche.com/colleges/california-institute-of-technology/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "caltech-biology-bs": {
        "summary": (
            "Students and guides describe Caltech biology as a research-first "
            "undergraduate major in a division built for bioengineering and "
            "neuroscience discovery — praising early bench research, access to the "
            "Beckman Institute and affiliated medical centers, and quantitative training "
            "unusual for a biology degree; common cautions are that courses assume strong "
            "chemistry and math, pre-med support is less centralized than at larger "
            "universities, and the overall Caltech workload leaves little slack."
        ),
        "themes": [
            {
                "label": "Research from year one",
                "sentiment": "positive",
                "detail": (
                    "SURF placements in molecular biology, neuroscience, and "
                    "bioengineering labs are common."
                ),
            },
            {
                "label": "Quantitative biology",
                "sentiment": "positive",
                "detail": (
                    "The curriculum integrates genetics, biochemistry, and computational "
                    "methods."
                ),
            },
            {
                "label": "Interdisciplinary ties",
                "sentiment": "positive",
                "detail": (
                    "BBE connects biology to chemical engineering and applied physics "
                    "across campus."
                ),
            },
            {
                "label": "Pre-med advising",
                "sentiment": "caution",
                "detail": (
                    "Students note fewer structured pre-med resources than at large "
                    "research universities."
                ),
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": (
                    "Lab time plus Caltech core requirements create a packed schedule."
                ),
            },
        ],
        "sources": [
            {
                "label": "Caltech — Division of Biology and Biological Engineering",
                "url": "https://www.bbe.caltech.edu/",
            },
            {
                "label": "Niche — California Institute of Technology",
                "url": "https://www.niche.com/colleges/california-institute-of-technology/",
            },
            {
                "label": "Caltech — University and College Rankings",
                "url": "https://www.caltech.edu/about/university-and-college-rankings",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "caltech-ids-bs": {
        "summary": (
            "Students and data-science guides describe Caltech's Information and Data "
            "Sciences option as a rigorous, math-forward major bridging CMS computing "
            "with statistics and machine learning — launched as Caltech expanded its "
            "computing footprint — praising small cohorts, faculty-led projects, and "
            "strong placement into tech and graduate analytics programs; common cautions "
            "are that the major is newer and smaller than peer CS programs, course "
            "offerings can feel narrow, and the standard Caltech workload remains intense."
        ),
        "themes": [
            {
                "label": "Math-forward data science",
                "sentiment": "positive",
                "detail": (
                    "Combines probability, inference, and computing in CMS with Caltech's "
                    "quantitative core."
                ),
            },
            {
                "label": "Research projects",
                "sentiment": "positive",
                "detail": (
                    "Undergraduates work on machine learning and information theory with "
                    "CMS faculty."
                ),
            },
            {
                "label": "Tech placement",
                "sentiment": "positive",
                "detail": (
                    "Graduates target data-science, quant, and software roles leveraging "
                    "the Caltech brand."
                ),
            },
            {
                "label": "Newer major",
                "sentiment": "mixed",
                "detail": (
                    "The option is still growing compared with long-established CS "
                    "programs elsewhere."
                ),
            },
            {
                "label": "Course breadth",
                "sentiment": "caution",
                "detail": (
                    "Fewer electives than at large CS departments can limit specialization "
                    "outside core strengths."
                ),
            },
        ],
        "sources": [
            {
                "label": "Caltech CMS — Information and Data Sciences",
                "url": "https://www.cms.caltech.edu/academics/undergrad",
            },
            {
                "label": "Niche — California Institute of Technology",
                "url": "https://www.niche.com/colleges/california-institute-of-technology/",
            },
            {
                "label": "Caltech — University and College Rankings",
                "url": "https://www.caltech.edu/about/university-and-college-rankings",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "caltech-bem-bs": {
        "summary": (
            "Students and guides describe Caltech's Business, Economics, and Management "
            "option as a quantitative social-science major inside a STEM institute — "
            "emphasizing microeconomics, econometrics, and decision science rather than a "
            "traditional undergraduate business school — praising analytical rigor and "
            "faculty research access; common cautions are that it is not a pre-MBA "
            "pipeline like peer business colleges, recruiting is self-directed, and the "
            "humanities division is tiny relative to engineering."
        ),
        "themes": [
            {
                "label": "Quantitative economics",
                "sentiment": "positive",
                "detail": (
                    "Coursework stresses micro theory, game theory, and econometrics with "
                    "Caltech-level math."
                ),
            },
            {
                "label": "Faculty research",
                "sentiment": "positive",
                "detail": (
                    "HSS economists work on industrial organization, finance, and "
                    "experimental economics."
                ),
            },
            {
                "label": "Analytical toolkit",
                "sentiment": "positive",
                "detail": (
                    "Graduates pursue PhD economics, quant finance, consulting, and policy "
                    "analysis."
                ),
            },
            {
                "label": "Not a B-school",
                "sentiment": "mixed",
                "detail": (
                    "There is no separate undergraduate business college or corporate "
                    "recruiting cycle."
                ),
            },
            {
                "label": "Small division",
                "sentiment": "caution",
                "detail": (
                    "Fewer humanities peers and electives than at liberal-arts colleges."
                ),
            },
        ],
        "sources": [
            {
                "label": "Caltech — Business, Economics, and Management",
                "url": "https://www.hss.caltech.edu/academics/bem",
            },
            {
                "label": "Niche — California Institute of Technology",
                "url": "https://www.niche.com/colleges/california-institute-of-technology/",
            },
            {
                "label": "Caltech — University and College Rankings",
                "url": "https://www.caltech.edu/about/university-and-college-rankings",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "caltech-computer-science-ms": {
        "summary": (
            "Students and graduate guides describe Caltech's MS in Computer Science as a "
            "selective, research-oriented degree within CMS — Caltech ranks among the "
            "world's top universities for engineering and technology in Times Higher "
            "Education (No. 7 globally, 2026) — praising thesis and project paths with "
            "leading faculty; common cautions are limited seats, fewer industry "
            "recruiting events than larger CS schools, and a curriculum that assumes "
            "strong theoretical and mathematical preparation."
        ),
        "themes": [
            {
                "label": "Research-oriented MS",
                "sentiment": "positive",
                "detail": (
                    "Thesis and project tracks connect students to algorithms, ML, and "
                    "systems groups in CMS."
                ),
            },
            {
                "label": "Faculty depth",
                "sentiment": "positive",
                "detail": (
                    "A small graduate cohort works directly with faculty on publishing "
                    "research."
                ),
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is highly competitive with a small entering class.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "caution",
                "detail": (
                    "Fewer on-campus corporate events than at large CS graduate programs "
                    "— students often network independently."
                ),
            },
            {
                "label": "Theoretical prerequisites",
                "sentiment": "caution",
                "detail": (
                    "Courses expect strong algorithms, linear algebra, and probability "
                    "backgrounds."
                ),
            },
        ],
        "sources": [
            {
                "label": "Caltech CMS — Graduate Programs",
                "url": "https://www.cms.caltech.edu/academics/grad",
            },
            {
                "label": "Caltech — University and College Rankings",
                "url": "https://www.caltech.edu/about/university-and-college-rankings",
            },
            {
                "label": "Niche — California Institute of Technology",
                "url": "https://www.niche.com/colleges/california-institute-of-technology/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "caltech-physics-ms": {
        "summary": (
            "Students and academic guides rank Caltech's physics MS among the most "
            "prestigious physics graduate credentials — the division operates LIGO and "
            "partners with Palomar and Keck observatories — praising frontier thesis "
            "research and faculty mentorship; common cautions are that many MS students "
            "continue toward the PhD, funding packages vary by group, and the program "
            "expects exceptional physics and math preparation."
        ),
        "themes": [
            {
                "label": "Frontier research",
                "sentiment": "positive",
                "detail": (
                    "Thesis work spans astrophysics, quantum matter, and gravitational-wave "
                    "science."
                ),
            },
            {
                "label": "Observatory access",
                "sentiment": "positive",
                "detail": (
                    "Caltech-managed observatories and LIGO provide unique experimental "
                    "platforms."
                ),
            },
            {
                "label": "PhD pipeline",
                "sentiment": "mixed",
                "detail": (
                    "Many MS students treat the degree as a step toward Caltech's PhD "
                    "program or other top doctorates."
                ),
            },
            {
                "label": "Funding variability",
                "sentiment": "caution",
                "detail": (
                    "Research-group support differs; students should confirm funding when "
                    "joining a lab."
                ),
            },
            {
                "label": "Preparation bar",
                "sentiment": "caution",
                "detail": (
                    "Graduate coursework assumes mastery of undergraduate quantum mechanics "
                    "and math methods."
                ),
            },
        ],
        "sources": [
            {
                "label": "Caltech PMA — Graduate Studies",
                "url": "https://www.pma.caltech.edu/academics/grad",
            },
            {
                "label": "Caltech — University and College Rankings",
                "url": "https://www.caltech.edu/about/university-and-college-rankings",
            },
            {
                "label": "Niche — California Institute of Technology",
                "url": "https://www.niche.com/colleges/california-institute-of-technology/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "caltech-electrical-electronics-and-communications-engineering-ms": {
        "summary": (
            "Students and engineering guides describe Caltech's electrical engineering MS "
            "as a research-intensive graduate option with strengths in communications, "
            "photonics, and quantum hardware — praising close faculty collaboration and "
            "ties to JPL and campus quantum institutes; common cautions are a small "
            "program with limited coursework breadth, competitive lab placement, and "
            "fewer corporate recruiting events than at large EE graduate schools."
        ),
        "themes": [
            {
                "label": "Research depth",
                "sentiment": "positive",
                "detail": (
                    "Thesis research spans photonics, circuits, communications, and "
                    "quantum engineering."
                ),
            },
            {
                "label": "JPL & lab ties",
                "sentiment": "positive",
                "detail": (
                    "Graduate students collaborate with JPL and on-campus quantum and "
                    "nanotechnology centers."
                ),
            },
            {
                "label": "Faculty mentoring",
                "sentiment": "positive",
                "detail": "Small cohorts enable direct advising from EE faculty.",
            },
            {
                "label": "Limited breadth",
                "sentiment": "caution",
                "detail": (
                    "Course offerings are narrower than at large EE departments with many "
                    "specializations."
                ),
            },
            {
                "label": "Recruiting",
                "sentiment": "caution",
                "detail": (
                    "Industry placement often relies on faculty networks rather than large "
                    "career fairs."
                ),
            },
        ],
        "sources": [
            {
                "label": "Caltech — Electrical Engineering graduate program",
                "url": "https://www.ee.caltech.edu/academics/grad",
            },
            {
                "label": "Caltech — University and College Rankings",
                "url": "https://www.caltech.edu/about/university-and-college-rankings",
            },
            {
                "label": "Niche — California Institute of Technology",
                "url": "https://www.niche.com/colleges/california-institute-of-technology/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "caltech-mechanical-engineering-ms": {
        "summary": (
            "Students and guides describe Caltech's mechanical engineering MS as a "
            "thesis-centered graduate program emphasizing fluid mechanics, robotics, and "
            "materials — praising hands-on experimental work and interdisciplinary ties "
            "to aerospace and bioengineering; common cautions are limited class offerings "
            "relative to large ME departments, funding tied to research groups, and the "
            "expectation that students arrive with strong continuum mechanics and math "
            "backgrounds."
        ),
        "themes": [
            {
                "label": "Experimental thesis work",
                "sentiment": "positive",
                "detail": (
                    "Graduate research in fluids, robotics, and materials with access to "
                    "Caltech's fabrication facilities."
                ),
            },
            {
                "label": "Interdisciplinary links",
                "sentiment": "positive",
                "detail": (
                    "Collaboration with GALCIT aerospace and BBE bioengineering is common."
                ),
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "Small program size supports close mentoring relationships.",
            },
            {
                "label": "Course breadth",
                "sentiment": "caution",
                "detail": (
                    "Fewer specialized ME electives than at large public engineering "
                    "colleges."
                ),
            },
            {
                "label": "Funding",
                "sentiment": "caution",
                "detail": (
                    "Research assistantships depend on faculty grants; not all groups fund "
                    "every admit."
                ),
            },
        ],
        "sources": [
            {
                "label": "Caltech — Mechanical and Civil Engineering graduate",
                "url": "https://www.mce.caltech.edu/academics/grad",
            },
            {
                "label": "Caltech — University and College Rankings",
                "url": "https://www.caltech.edu/about/university-and-college-rankings",
            },
            {
                "label": "Niche — California Institute of Technology",
                "url": "https://www.niche.com/colleges/california-institute-of-technology/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "caltech-aerospace-aeronautical-and-astronautical-space-engineering-ms": {
        "summary": (
            "Students and aerospace guides rank Caltech's GALCIT aerospace MS among the "
            "most prestigious aeronautics programs — Caltech operates and co-manages JPL "
            "for NASA — praising thesis research in propulsion, structures, and space "
            "systems with unmatched access to JPL mentors; common cautions are extremely "
            "selective admission, funding tied to research contracts, and a curriculum "
            "that assumes strong physics and engineering mathematics."
        ),
        "themes": [
            {
                "label": "JPL partnership",
                "sentiment": "positive",
                "detail": (
                    "Graduate students routinely collaborate with Jet Propulsion Laboratory "
                    "scientists and engineers."
                ),
            },
            {
                "label": "Thesis research",
                "sentiment": "positive",
                "detail": (
                    "Work spans hypersonics, space systems, and computational aerodynamics."
                ),
            },
            {
                "label": "Prestige",
                "sentiment": "positive",
                "detail": (
                    "GALCIT alumni feed NASA, aerospace primes, and leading PhD programs."
                ),
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is highly competitive with a very small cohort.",
            },
            {
                "label": "Funding dependence",
                "sentiment": "caution",
                "detail": (
                    "Research assistantships follow faculty and JPL project funding cycles."
                ),
            },
        ],
        "sources": [
            {
                "label": "Caltech — GALCIT Graduate Aerospace",
                "url": "https://www.galcit.caltech.edu/academics/grad",
            },
            {
                "label": "Caltech — Jet Propulsion Laboratory",
                "url": "https://www.jpl.nasa.gov/",
            },
            {
                "label": "Caltech — University and College Rankings",
                "url": "https://www.caltech.edu/about/university-and-college-rankings",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    **DEPTH_REVIEWS,
}

# Coverable programs that must carry external_reviews (the MBAn/CMU pattern).
_COVERABLE_REVIEWS = frozenset(_REVIEWS_BY_SLUG.keys())

# ── Application requirements (degree-type baselines) ────────────────────────
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission.",
}
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application or QuestBridge Application", "required": True},
        {"name": "Caltech short-answer questions", "required": True},
        {"name": "School report + counselor recommendation", "required": True},
        {"name": "Two STEM teacher recommendations", "required": True},
        {"name": "Official transcript", "required": True},
        {
            "name": "SAT or ACT scores",
            "required": True,
            "note": "Required again from the Class of 2029 — verify on the official page.",
        },
        {"name": "$75 application fee or fee waiver", "required": True},
    ],
    "deadlines": [
        {"round": "Restrictive Early Action", "date": "November 1"},
        {"round": "Regular Decision", "date": "January 3"},
    ],
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": False,
            "note": "English-proficiency proof recommended for non-native speakers.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {"label": "Caltech Undergraduate Admissions", "url": "https://www.admissions.caltech.edu/"}
        ],
    },
    "source": "Caltech Undergraduate Admissions",
    "source_url": "https://www.admissions.caltech.edu/apply/first-year-applicants",
}
_REQ_GRAD = {
    "materials": [
        {"name": "Online graduate application", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Three letters of recommendation", "required": True},
        {"name": "Transcripts from all institutions attended", "required": True},
        {
            "name": "GRE",
            "required": False,
            "note": "Most options are GRE-optional or do not require it — check the option page.",
        },
        {
            "name": "TOEFL or IELTS for international applicants",
            "required": False,
            "note": "Required if your first language is not English; waivers available.",
        },
    ],
    "recommendations": {
        "required_count": 3,
        "types": ["Three academic or research letters of recommendation"],
    },
    "deadlines": [
        {
            "round": "Option deadlines (typically December 15)",
            "date": "Varies by option — verify on the option page",
        }
    ],
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": True,
            "note": "Required if your first language is not English; waivers available.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {"label": "Caltech Graduate Studies Office", "url": "https://gradoffice.caltech.edu/"}
        ],
    },
    "source": "Caltech Graduate Studies Office",
    "source_url": "https://gradoffice.caltech.edu/admissions",
}


# Real Caltech campus photo (Arms Courtyard) — leads the institution hero; see
# ``SCHOOL_OUTCOMES["campus_photos"]`` for the full gallery.
_CAMPUS_PHOTO = SCHOOL_OUTCOMES["campus_photos"][0]["url"]


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich Caltech to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Caltech is absent — safe on fresh/CI databases.
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
            school_outcomes.pop(_path.split(".", 1)[1], None)
    school_outcomes["_standard"] = _standard(_OMITTED_INSTITUTION)
    inst.school_outcomes = school_outcomes
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    inst.founded_year = 1891
    inst.campus_setting = "suburban"
    if not inst.website_url:
        inst.website_url = "https://www.caltech.edu"
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
        # Every division carries keyword-filtered Caltech News + campus-events feeds.
        sc.content_sources = _school_content(spec["name"])
        by_name[spec["name"]] = sc
    # Drop legacy divisions — programs.school_id is ON DELETE SET NULL, so this is
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


def _program_standard(slug: str, spec: dict, *, has_program_outcomes: bool) -> dict:
    """Per-program omitted-field list (verified-unavailable), for _standard."""
    omitted: list[str] = []
    # Caltech publishes no per-program employment report, so every program omits
    # the program-level employment rate, top industries, and methodology block.
    omitted += [
        "outcomes_data.employment_rate",
        "outcomes_data.top_industries",
        "outcomes_data.conditions",
    ]
    if slug not in _TRACKS_BY_SLUG:
        omitted.append("tracks")
    if slug not in _CLASS_PROFILE_BY_SLUG:
        omitted.append("class_profile.cohort_size")
    if slug not in _FACULTY_BY_SLUG:
        omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    if spec["degree_type"] == "phd":
        # Funded PhDs carry tuition $0 (not a sticker price); cost breakdown N/A.
        pass
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
        # Website: verified option/grad page where available, else the owning
        # division's official site (the authoritative home for the option).
        p.website_url = _WEBSITE_BY_SLUG.get(slug) or (
            _GRAD_OPTIONS_URL
            if spec["degree_type"] == "phd"
            else _SCHOOL_WEBSITE.get(spec["school"])
        )
        p.school_id = school_by_name[spec["school"]].id
        p.department = spec.get("department")
        p.is_published = True
        p.catalog_source = "curated"
        p.cip_code = spec.get("cip")
        p.delivery_format = spec.get("delivery_format", "in_person")
        # Always assign so a stale value on a pre-existing row is cleared.
        p.content_sources = _CS_CONTENT if slug == "caltech-cs-bs" else _program_content(spec)
        # Cost: funded PhD → undergrad rate (published tuition + COA).
        cost_override = _COST_BY_SLUG.get(slug)
        if cost_override is not None:
            p.tuition = cost_override.get("tuition_usd")
            p.cost_data = dict(cost_override)
        elif spec["degree_type"] == "phd":
            p.tuition = 0
            p.cost_data = {
                "tuition_usd": 0,
                "funded": True,
                "note": "Caltech PhD students receive full tuition plus a stipend.",
                "source": "Caltech Graduate Studies Office",
                "source_url": "https://gradoffice.caltech.edu/admissions/financial-support",
                "year": "2025-26",
            }
        else:  # bachelors
            p.tuition = _TUITION_UNDERGRAD
            p.cost_data = {
                "tuition_usd": _TUITION_UNDERGRAD,
                "total_cost_of_attendance": _UNDERGRAD_COA,
                "funded": False,
                "source": "U.S. Dept. of Education College Scorecard (UNITID 110404)",
                "source_url": "https://collegescorecard.ed.gov/school/?110404",
                "year": "2024-25",
            }
        # Admissions: undergrad vs grad baseline.
        if spec["degree_type"] == "bachelors":
            p.application_requirements = dict(_REQ_UNDERGRAD)
        else:
            p.application_requirements = dict(_REQ_GRAD)
        # Outcomes precedence: Scorecard FOS (program) → institution median.
        fos = _FOS_OUTCOMES.get(slug)
        if fos is not None:
            salary, cip = fos
            outcomes = {
                "median_salary": salary,
                "scope": "program",
                "cip": cip,
                "earnings_timeframe": "median earnings 1 year after completion",
                "source": "U.S. Dept. of Education College Scorecard — Field of Study",
                "source_url": "https://collegescorecard.ed.gov/school/?110404",
            }
            has_program_outcomes = True
        else:
            outcomes = dict(_OUTCOMES_INSTITUTION)
            has_program_outcomes = False
        outcomes["_standard"] = _program_standard(
            slug, spec, has_program_outcomes=has_program_outcomes
        )
        p.outcomes_data = outcomes
        p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_BY_TYPE.get(spec["degree_type"])
        p.highlights = _HL_BY_SLUG.get(slug) or _HL_BY_TYPE.get(spec["degree_type"])
        # Always assign so a stale value on a pre-existing row is cleared (tracks is
        # recorded as omitted where unverified, and match_service reads program.tracks).
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        # Application deadline (upcoming cycle).
        if spec["degree_type"] == "bachelors":
            p.application_deadline = date(2027, 1, 3)
        else:
            p.application_deadline = date(2026, 12, 15)
    session.flush()
    # Reconcile legacy Caltech programs (slug not in the canonical set): delete when
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
